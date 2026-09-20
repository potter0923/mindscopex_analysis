# Copyright 2026 MindScopeX
"""Jacobian-lens (J-lens) adapter for the MindScopeX pipeline.

The Jacobian lens reads out what an internal activation is *disposed to make the
model say*. It transports a residual at layer ``l`` into the final-layer basis
with an averaged input-output Jacobian, then decodes with the model's own
unembedding::

    lens_l(h) = softmax( W_U · norm( J_l @ h ) )
    J_l       = E[ ∂h_target / ∂h_l ]

Reference: Gurnee, Sofroniew, ... Lindsey (Anthropic, 2026-07-06),
*Verbalizable Representations Form a Global Workspace in Language Models*
(https://transformer-circuits.pub/2026/workspace), code
https://github.com/anthropics/jacobian-lens.

**This module does not reimplement the lens.** ``jlens`` is the reference
implementation and already supports Qwen3.5: its ``hf._LAYOUTS`` contains
``Layout("model.language_model")``, which is exactly
:data:`~mindscopex_analysis.models.QWEN35_BLOCK_PATH_TEMPLATE`. What this module
adds is the glue this repo needs:

* profile-aware lens loading / fitting keyed on
  :class:`~mindscopex_analysis.models.Qwen35AnalysisProfile`;
* a per-condition **rank trajectory** readout over a
  :class:`~mindscopex_analysis.cases.LureCase` family, which is the T1 deliverable
  ("when does the model start aiming at the lure, and when does it stop");
* :func:`divergence_layer`, which turns those trajectories into the *layer band to
  search next* — the causal-localization step that precedes feature search;
* a bridge from ``lens.transport()`` to residuals captured by
  :func:`~mindscopex_analysis.activations.capture_residual_stream`, so a J-lens
  direction can be compared against an existing difference-in-means direction.

Two facts from the paper that the README does not state, and that the defaults
here follow:

* the paper's default **target is the penultimate layer**, not the final one
  (including the last block "can sometimes increase the number of noisy
  artifacts") — see :data:`DEFAULT_TARGET_LAYER`;
* lens quality saturates fast: "J-lens beats the logit lens and tuned lens
  baselines with **as few as 10 prompts**", so :data:`DEFAULT_FIT_PROMPTS` is
  small on purpose.

Caveats the paper states and that callers must respect:

* the readout only names concepts that are **a single token** in the vocabulary;
* in roughly the **first third** of the model the readouts are "noisy and largely
  uninterpretable";
* **reading is not causation** — "A lens that surfaces a concept in its readout
  has not necessarily found the direction the model actually computes with."
  Use :func:`divergence_layer` to *localize*, then run an intervention with a
  matched random-direction control before claiming a mechanism.
"""

from __future__ import annotations

import os
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from mindscopex_analysis.cases import LureCase

#: Paper default: transport to the penultimate layer, not the final one.
DEFAULT_TARGET_LAYER = -2

#: Small on purpose; the paper reports the lens beats baselines from ~10 prompts.
DEFAULT_FIT_PROMPTS = 20

#: Conditions compared by :func:`condition_trajectories`, in report order.
DEFAULT_CONDITIONS: tuple[str, ...] = ("hostile", "explicit", "neutral")


def _require_jlens() -> Any:
    """Import ``jlens`` with an actionable message when it is missing."""
    try:
        import jlens
    except ImportError as exc:  # pragma: no cover - import-guard
        raise ImportError(
            "The Jacobian lens reference implementation is required:\n"
            "    pip install git+https://github.com/anthropics/jacobian-lens.git"
        ) from exc
    return jlens


# --------------------------------------------------------------- pure helpers
# These carry the report logic and are unit-testable without torch or a model.


def token_rank(scores: Sequence[float], token_id: int) -> int:
    """1-based rank of ``token_id`` when ``scores`` is sorted descending.

    Rank 1 means the model is most strongly disposed to emit that token.

    Raises:
        IndexError: If ``token_id`` is out of range for ``scores``.
    """
    if not 0 <= token_id < len(scores):
        raise IndexError(f"token_id={token_id} out of range for {len(scores)} scores")
    target = scores[token_id]
    return 1 + sum(1 for value in scores if value > target)


@dataclass(frozen=True)
class LayerReadout:
    """Lure/correct ranks for one (condition, layer)."""

    condition: str
    layer: int
    lure_rank: int
    correct_rank: int

    @property
    def lure_advantage(self) -> float:
        """``correct_rank / lure_rank``; > 1 means the lure is ahead."""
        return self.correct_rank / max(self.lure_rank, 1)

    def as_row(self) -> dict[str, Any]:
        return {
            "condition": self.condition,
            "layer": self.layer,
            "lure_rank": self.lure_rank,
            "correct_rank": self.correct_rank,
            "lure_advantage": self.lure_advantage,
        }


def divergence_layer(
    trajectories: Mapping[str, Mapping[int, LayerReadout]],
    *,
    base: str = "hostile",
    control: str = "explicit",
) -> tuple[int, float]:
    """Layer where ``base`` most out-aims ``control`` on the lure token.

    The score at a layer is ``control.lure_rank / base.lure_rank``: large when the
    trap condition has the lure near the top while the control has pushed it down.
    That layer is where the two conditions have already parted, so it is the band
    to search first — the localization step the 2026-09-06 recap asks for before
    any feature search.

    Returns:
        ``(layer, ratio)`` for the largest ratio.

    Raises:
        KeyError: If either condition is absent.
        ValueError: If the two conditions share no layer.
    """
    for name in (base, control):
        if name not in trajectories:
            raise KeyError(f"condition {name!r} not in trajectories: {sorted(trajectories)}")
    shared = sorted(set(trajectories[base]) & set(trajectories[control]))
    if not shared:
        raise ValueError(f"{base!r} and {control!r} share no layers")
    ratios = {
        layer: trajectories[control][layer].lure_rank / max(trajectories[base][layer].lure_rank, 1)
        for layer in shared
    }
    best = max(ratios, key=lambda layer: ratios[layer])
    return best, ratios[best]


def trajectory_rows(
    trajectories: Mapping[str, Mapping[int, LayerReadout]],
) -> list[dict[str, Any]]:
    """Flatten trajectories into CSV-ready rows, ordered by condition then layer."""
    rows: list[dict[str, Any]] = []
    for condition in sorted(trajectories):
        for layer in sorted(trajectories[condition]):
            rows.append(trajectories[condition][layer].as_row())
    return rows


def first_token_id(tokenizer: Any, answer: str) -> int:
    """Token id of the first token of ``answer``.

    The lens names only single-token concepts, so a multi-token answer is read
    through its first token. Callers comparing two answers should check that the
    two first tokens differ, or the trajectory is meaningless.
    """
    ids = tokenizer.encode(answer, add_special_tokens=False)
    if not ids:
        raise ValueError(f"answer {answer!r} produced no tokens")
    return int(ids[0])


def answers_are_separable(tokenizer: Any, case: LureCase) -> bool:
    """Whether correct and lure answers differ in their first token."""
    return first_token_id(tokenizer, case.correct_answer) != first_token_id(
        tokenizer, case.lure_answer
    )


# ------------------------------------------------------------ model-dependent


def wrap_model(hf_model: Any, tokenizer: Any, **kwargs: Any) -> Any:
    """Wrap a loaded HF model for the lens (``jlens.from_hf``).

    Qwen3.5's layout is auto-detected; no explicit ``layout=`` is needed. Note
    that ``from_hf`` mutates the model in place (``requires_grad_(False)``,
    ``tokenizer.add_bos_token = True``), so do not share the object with other
    experiments.
    """
    return _require_jlens().from_hf(hf_model, tokenizer, **kwargs)


def load_or_fit_lens(
    model: Any,
    *,
    path: str,
    prompts: Sequence[str] | None = None,
    source_layers: Sequence[int] | None = None,
    target_layer: int = DEFAULT_TARGET_LAYER,
    dim_batch: int = 16,
    checkpoint_path: str | None = None,
) -> Any:
    """Load a fitted lens from ``path``, or fit one and save it there.

    Args:
        model: A wrapped model from :func:`wrap_model`.
        path: Where the lens is cached.
        prompts: Corpus for fitting. Required when ``path`` does not exist.
        source_layers: Layers to fit. ``None`` fits every layer below the target,
            which is expensive on a deep model; pass a stride for a first pass.
        target_layer: Defaults to the paper's penultimate-layer target.
        dim_batch: Output dims per backward pass. Cost per prompt is one forward
            plus ``ceil(d_model / dim_batch)`` backwards.
        checkpoint_path: Written during fitting so a killed session can resume.

    Raises:
        ValueError: If a fit is needed but ``prompts`` is empty.
    """
    jlens = _require_jlens()
    if os.path.exists(path):
        return jlens.JacobianLens.load(path)
    if not prompts:
        raise ValueError(f"no lens at {path!r} and no prompts given to fit one")
    lens = jlens.fit(
        model,
        prompts=list(prompts),
        source_layers=None if source_layers is None else list(source_layers),
        target_layer=target_layer,
        dim_batch=dim_batch,
        checkpoint_path=checkpoint_path,
    )
    lens.save(path)
    return lens


def case_trajectory(
    lens: Any,
    model: Any,
    tokenizer: Any,
    case: LureCase,
    *,
    condition: str | None = None,
    position: int = -1,
    layers: Sequence[int] | None = None,
    use_jacobian: bool = True,
) -> dict[int, LayerReadout]:
    """Per-layer lure/correct ranks for one case.

    ``use_jacobian=False`` reproduces the plain logit-lens baseline, which is the
    comparison the paper reports against.
    """
    lure_id = first_token_id(tokenizer, case.lure_answer)
    correct_id = first_token_id(tokenizer, case.correct_answer)
    lens_logits, _model_logits, _ids = lens.apply(
        model,
        case.prompt,
        layers=None if layers is None else list(layers),
        positions=[position],
        use_jacobian=use_jacobian,
    )
    name = condition or case.condition
    out: dict[int, LayerReadout] = {}
    for layer, logits in lens_logits.items():
        scores = logits[0].tolist()
        out[int(layer)] = LayerReadout(
            condition=name,
            layer=int(layer),
            lure_rank=token_rank(scores, lure_id),
            correct_rank=token_rank(scores, correct_id),
        )
    return out


def condition_trajectories(
    lens: Any,
    model: Any,
    tokenizer: Any,
    cases_by_condition: Mapping[str, LureCase],
    *,
    conditions: Iterable[str] = DEFAULT_CONDITIONS,
    position: int = -1,
    layers: Sequence[int] | None = None,
    use_jacobian: bool = True,
) -> dict[str, dict[int, LayerReadout]]:
    """Trajectories for one scenario across its conditions.

    ``cases_by_condition`` is the ``{condition: LureCase}`` map for a single
    ``pair_id`` — the trap, the cue-free control, and the explicit-precondition
    control all share surface form, so their trajectories are comparable.
    """
    out: dict[str, dict[int, LayerReadout]] = {}
    for condition in conditions:
        case = cases_by_condition.get(condition)
        if case is None:
            continue
        out[condition] = case_trajectory(
            lens,
            model,
            tokenizer,
            case,
            condition=condition,
            position=position,
            layers=layers,
            use_jacobian=use_jacobian,
        )
    if not out:
        raise ValueError(f"none of {list(conditions)} present in the given cases")
    return out


def lens_answer_direction(
    lens: Any,
    unembedding_weight: Any,
    *,
    layer: int,
    lure_token_id: int,
    correct_token_id: int,
) -> Any:
    """The "lure minus correct" direction expressed in ``layer``'s basis.

    ``W_U``'s rows are token directions in the final basis; pushing one back
    through ``J_l`` gives the direction at ``layer`` that the lens reads that
    token off. The difference of two such rows is the contrast to compare against
    an existing difference-in-means direction (roadmap T1-6).

    This is a *readout* direction. Whether moving along it changes behaviour is a
    separate question that needs an intervention and a matched random-direction
    control (roadmap T1-7).
    """
    jacobian = lens.jacobians[int(layer)]
    contrast = unembedding_weight[lure_token_id] - unembedding_weight[correct_token_id]
    return contrast.float().cpu() @ jacobian


__all__ = [
    "DEFAULT_CONDITIONS",
    "DEFAULT_FIT_PROMPTS",
    "DEFAULT_TARGET_LAYER",
    "LayerReadout",
    "answers_are_separable",
    "case_trajectory",
    "condition_trajectories",
    "divergence_layer",
    "first_token_id",
    "load_or_fit_lens",
    "lens_answer_direction",
    "token_rank",
    "trajectory_rows",
    "wrap_model",
]
