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
import random
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


def split_fit_eval(
    cases: Sequence[LureCase],
    *,
    n_fit: int,
    seed: int = 0,
) -> tuple[list[LureCase], list[LureCase]]:
    """Deterministic fit/eval split over a case list.

    The lens must not be fitted on the prompts it is then scored against, so the
    2026-10-03 plan splits ``hagendorff_crt`` 105/45. The shuffle is seeded and
    uses only the stdlib, so the same seed reproduces the same split anywhere.

    Raises:
        ValueError: If ``n_fit`` leaves no evaluation cases.
    """
    if not 0 < n_fit < len(cases):
        raise ValueError(f"n_fit={n_fit} must be between 1 and {len(cases) - 1}")
    order = list(cases)
    random.Random(seed).shuffle(order)
    return order[:n_fit], order[n_fit:]


def answer_margin(scores: Sequence[float], lure_token_id: int, correct_token_id: int) -> float:
    """``score[lure] - score[correct]``; positive means the lure is favoured.

    Ranks say *where* a token sits; the margin says *by how much*, which is what
    the lens-versus-lens correlation needs.
    """
    for token_id in (lure_token_id, correct_token_id):
        if not 0 <= token_id < len(scores):
            raise IndexError(f"token_id={token_id} out of range for {len(scores)} scores")
    return float(scores[lure_token_id]) - float(scores[correct_token_id])


def _average_ranks(values: Sequence[float]) -> list[float]:
    """Ranks of ``values``, ties sharing the mean of the ranks they span."""
    order = sorted(range(len(values)), key=lambda i: values[i])
    ranks = [0.0] * len(values)
    start = 0
    while start < len(order):
        stop = start
        while stop + 1 < len(order) and values[order[stop + 1]] == values[order[start]]:
            stop += 1
        shared = (start + stop) / 2 + 1
        for position in range(start, stop + 1):
            ranks[order[position]] = shared
        start = stop + 1
    return ranks


def spearman(xs: Sequence[float], ys: Sequence[float]) -> float:
    """Spearman rank correlation, stdlib only, ties averaged.

    Returns ``0.0`` when either side is constant, since no monotone relation is
    measurable there. Kept dependency-free so it is testable without torch.

    Raises:
        ValueError: If the inputs differ in length or have fewer than two points.
    """
    if len(xs) != len(ys):
        raise ValueError(f"length mismatch: {len(xs)} vs {len(ys)}")
    if len(xs) < 2:
        raise ValueError("need at least two points")
    rx, ry = _average_ranks(xs), _average_ranks(ys)
    mx, my = sum(rx) / len(rx), sum(ry) / len(ry)
    dx = [value - mx for value in rx]
    dy = [value - my for value in ry]
    denominator = (sum(v * v for v in dx) * sum(v * v for v in dy)) ** 0.5
    if denominator == 0:
        return 0.0
    return sum(a * b for a, b in zip(dx, dy, strict=True)) / denominator


def layer_correlations(
    lens_margins: Mapping[int, Mapping[str, float]],
    final_margins: Mapping[str, float],
) -> dict[int, float]:
    """Per-layer Spearman between the lens margin and the model's final margin.

    This is the number the 2026-10-02 note reports (0.35 for the J-lens against
    0.10 for the logit lens, on 2B). A layer scoring high means the lens readout
    there already tracks which answer the model ends up preferring.
    """
    out: dict[int, float] = {}
    for layer in sorted(lens_margins):
        shared = [case_id for case_id in lens_margins[layer] if case_id in final_margins]
        if len(shared) < 2:
            continue
        out[int(layer)] = spearman(
            [lens_margins[layer][case_id] for case_id in shared],
            [final_margins[case_id] for case_id in shared],
        )
    return out


def comparison_rows(
    jacobian: Mapping[int, float],
    logit: Mapping[int, float],
) -> list[dict[str, Any]]:
    """Side-by-side per-layer correlations, J-lens minus logit lens."""
    rows: list[dict[str, Any]] = []
    for layer in sorted(set(jacobian) | set(logit)):
        j_value, l_value = jacobian.get(layer), logit.get(layer)
        rows.append(
            {
                "layer": layer,
                "jacobian": j_value,
                "logit": l_value,
                "delta": None if j_value is None or l_value is None else j_value - l_value,
            }
        )
    return rows


def bootstrap_delta_ci(
    jacobian_margins: Mapping[str, float],
    logit_margins: Mapping[str, float],
    final_margins: Mapping[str, float],
    *,
    draws: int = 2000,
    seed: int = 0,
    alpha: float = 0.05,
) -> tuple[float, float, float]:
    """Case-resampled CI for ``spearman(J) - spearman(logit)`` at one layer.

    The 2026-10-02 result could not be called a win because the interval around
    the difference contained zero. Resampling *cases* (not layers) keeps the two
    lenses paired on the same draw, which is what makes the difference testable.

    Returns:
        ``(point_estimate, low, high)``.

    Raises:
        ValueError: If fewer than two cases are shared by all three maps.
    """
    shared = sorted(set(jacobian_margins) & set(logit_margins) & set(final_margins))
    if len(shared) < 2:
        raise ValueError("need at least two cases present in all three maps")

    def _delta(case_ids: Sequence[str]) -> float:
        finals = [final_margins[c] for c in case_ids]
        return spearman([jacobian_margins[c] for c in case_ids], finals) - spearman(
            [logit_margins[c] for c in case_ids], finals
        )

    point = _delta(shared)
    rng = random.Random(seed)
    samples = []
    for _ in range(draws):
        resampled = [rng.choice(shared) for _ in shared]
        if len({final_margins[c] for c in resampled}) < 2:
            continue
        samples.append(_delta(resampled))
    if not samples:
        return point, float("nan"), float("nan")
    samples.sort()
    low = samples[int(alpha / 2 * (len(samples) - 1))]
    high = samples[int((1 - alpha / 2) * (len(samples) - 1))]
    return point, low, high


def bootstrap_mean_delta_ci(
    jacobian_margins: Mapping[int, Mapping[str, float]],
    logit_margins: Mapping[int, Mapping[str, float]],
    final_margins: Mapping[str, float],
    *,
    draws: int = 2000,
    seed: int = 0,
    alpha: float = 0.05,
) -> tuple[float, float, float, list[int]]:
    """CI for the J-lens advantage *averaged over layers*, not picked at the best one.

    Testing at the layer that happened to score highest is the winner's curse the
    2026-08-23 post-mortem ran into: with sixteen layers on the table, the best of
    them looks good by chance alone. Averaging over a layer set fixed in advance
    gives one number with no selection in it, so it is the headline; per-layer
    intervals stay descriptive.

    Returns:
        ``(point_estimate, low, high, layers_used)``.

    Raises:
        ValueError: If no layer is shared, or fewer than two cases are.
    """
    layers = sorted(set(jacobian_margins) & set(logit_margins))
    if not layers:
        raise ValueError("the two lenses share no layer")
    shared = sorted(
        set.intersection(
            *(set(jacobian_margins[layer]) for layer in layers),
            *(set(logit_margins[layer]) for layer in layers),
            set(final_margins),
        )
    )
    if len(shared) < 2:
        raise ValueError("need at least two cases present at every layer")

    def _mean_delta(case_ids: Sequence[str]) -> float:
        finals = [final_margins[c] for c in case_ids]
        total = 0.0
        for layer in layers:
            total += spearman([jacobian_margins[layer][c] for c in case_ids], finals)
            total -= spearman([logit_margins[layer][c] for c in case_ids], finals)
        return total / len(layers)

    point = _mean_delta(shared)
    rng = random.Random(seed)
    samples = []
    for _ in range(draws):
        resampled = [rng.choice(shared) for _ in shared]
        if len({final_margins[c] for c in resampled}) < 2:
            continue
        samples.append(_mean_delta(resampled))
    if not samples:
        return point, float("nan"), float("nan"), layers
    samples.sort()
    low = samples[int(alpha / 2 * (len(samples) - 1))]
    high = samples[int((1 - alpha / 2) * (len(samples) - 1))]
    return point, low, high, layers


def first_token_id(tokenizer: Any, answer: str) -> int:
    """Token id of the first token of ``answer``.

    The lens names only single-token concepts, so a multi-token answer is read
    through its first token. Callers comparing two answers should check that the
    two first tokens differ, or the trajectory is meaningless.
    """
    ids = as_tokenizer(tokenizer).encode(answer, add_special_tokens=False)
    if not ids:
        raise ValueError(f"answer {answer!r} produced no tokens")
    return int(ids[0])


def as_tokenizer(tokenizer: Any) -> Any:
    """Unwrap a processor to the text tokenizer inside it.

    Qwen3.5 loads through ``AutoProcessor`` (it is a multimodal checkpoint), and
    the processor has no ``encode``/``decode`` of its own — the text tokenizer is
    one attribute in. Passing a plain tokenizer through is a no-op, so callers can
    apply this unconditionally.
    """
    return getattr(tokenizer, "tokenizer", tokenizer)


@dataclass(frozen=True)
class AnswerContrast:
    """Where two answers first part company, and what to read there.

    The lens scores one token at one position, so a pair like ``" $20.0"`` and
    ``" $40.0"`` cannot be told apart at the answer slot: both open with ``" $"``.
    They differ at the *next* token. Appending the shared opening to the prompt
    (teacher forcing) moves the read to the position where the two answers
    actually diverge, which is where the choice is visible.
    """

    prefix: str
    prefix_tokens: int
    lure_token_id: int
    correct_token_id: int

    @property
    def needs_prefix(self) -> bool:
        return self.prefix_tokens > 0


def answer_contrast(tokenizer: Any, case: LureCase) -> AnswerContrast:
    """First token position at which the two answers differ.

    Raises:
        ValueError: If one answer's tokens are a prefix of the other's, so no
            position distinguishes them and the case carries no lens signal.
    """
    tokenizer = as_tokenizer(tokenizer)
    correct = tokenizer.encode(case.correct_answer, add_special_tokens=False)
    lure = tokenizer.encode(case.lure_answer, add_special_tokens=False)
    if not correct or not lure:
        raise ValueError(f"case {case.case_id!r} has an answer that produced no tokens")
    for index in range(min(len(correct), len(lure))):
        if correct[index] != lure[index]:
            return AnswerContrast(
                prefix=tokenizer.decode(correct[:index]) if index else "",
                prefix_tokens=index,
                lure_token_id=int(lure[index]),
                correct_token_id=int(correct[index]),
            )
    raise ValueError(
        f"case {case.case_id!r}: one answer is a token-prefix of the other "
        f"({case.correct_answer!r} vs {case.lure_answer!r}); no position separates them"
    )


def answers_are_separable(tokenizer: Any, case: LureCase) -> bool:
    """Whether some token position tells the two answers apart."""
    try:
        answer_contrast(tokenizer, case)
    except ValueError:
        return False
    return True


# ------------------------------------------------------------ model-dependent


def wrap_model(hf_model: Any, tokenizer: Any, **kwargs: Any) -> Any:
    """Wrap a loaded HF model for the lens (``jlens.from_hf``).

    Qwen3.5's layout is auto-detected; no explicit ``layout=`` is needed. Note
    that ``from_hf`` mutates the model in place (``requires_grad_(False)``,
    ``tokenizer.add_bos_token = True``), so do not share the object with other
    experiments.
    """
    return _require_jlens().from_hf(hf_model, as_tokenizer(tokenizer), **kwargs)


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
    contrast = answer_contrast(tokenizer, case)
    lure_id, correct_id = contrast.lure_token_id, contrast.correct_token_id
    lens_logits, _model_logits, _ids = lens.apply(
        model,
        case.prompt + contrast.prefix,
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


def margin_scan(
    lens: Any,
    model: Any,
    tokenizer: Any,
    cases: Sequence[LureCase],
    *,
    layers: Sequence[int] | None = None,
    position: int = -1,
    use_jacobian: bool = True,
    skip_inseparable: bool = True,
) -> tuple[dict[int, dict[str, float]], dict[str, float], list[str]]:
    """Lens margins per layer plus the model's own final margin, over a case set.

    This is the measurement half of the 2026-10-03 plan's first item: read the
    held-out cases at every scanned layer, and separately record what the model
    actually ended up preferring, so the two can be correlated.

    Args:
        layers: Layers to read. ``None`` reads every layer the lens holds.
        position: Token position to read; ``-1`` is the answer slot.
        use_jacobian: ``False`` gives the plain logit-lens baseline.
        skip_inseparable: Drop cases whose two answers share a first token. The
            lens reads one token, so those cases carry no signal either way and
            would only add noise to the correlation.

    Returns:
        ``(lens_margins, final_margins, skipped_case_ids)`` where ``lens_margins``
        is ``{layer: {case_id: margin}}``.
    """
    lens_margins: dict[int, dict[str, float]] = {}
    final_margins: dict[str, float] = {}
    skipped: list[str] = []
    for case in cases:
        try:
            contrast = answer_contrast(tokenizer, case)
        except ValueError:
            if not skip_inseparable:
                raise
            skipped.append(case.case_id)
            continue
        lens_logits, model_logits, _ids = lens.apply(
            model,
            case.prompt + contrast.prefix,
            layers=None if layers is None else list(layers),
            positions=[position],
            use_jacobian=use_jacobian,
        )
        for layer, logits in lens_logits.items():
            lens_margins.setdefault(int(layer), {})[case.case_id] = answer_margin(
                logits[0].tolist(), contrast.lure_token_id, contrast.correct_token_id
            )
        final_margins[case.case_id] = answer_margin(
            model_logits[0].tolist(), contrast.lure_token_id, contrast.correct_token_id
        )
    return lens_margins, final_margins, skipped


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
    "AnswerContrast",
    "LayerReadout",
    "answer_contrast",
    "answer_margin",
    "answers_are_separable",
    "as_tokenizer",
    "bootstrap_delta_ci",
    "bootstrap_mean_delta_ci",
    "case_trajectory",
    "comparison_rows",
    "condition_trajectories",
    "divergence_layer",
    "first_token_id",
    "layer_correlations",
    "lens_answer_direction",
    "load_or_fit_lens",
    "margin_scan",
    "spearman",
    "split_fit_eval",
    "token_rank",
    "trajectory_rows",
    "wrap_model",
]
