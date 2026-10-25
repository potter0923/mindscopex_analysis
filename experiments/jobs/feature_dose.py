"""Dose-response and behaviour check for one pinned SAE feature.

The first mechanism pass (40_lure27b_study_margin) found L55 feature 65825 on 27B:
removing its activation lowered the lure margin on held-out memo traps by ~0.27
nats, but flipped no answer, and also moved the matched controls by ~0.11. Three
questions follow, and this job answers all of them in one run:

1. **Dose.** Removing k times the feature's own activation (k = 1, 2, 4, 8): does
   the lure margin keep falling, and does it cross zero (an actual flip)?
2. **Is it the feature or just the push?** At every dose the same per-case
   perturbation norm is spent on random directions. A feature-specific effect
   has to beat that null, case by case.
3. **Behaviour under the screen's own protocol.** The margins above use plain text.
   The lure was established in chat format with thinking off and a forced choice
   between the two answers, so the feature is also removed during that exact
   protocol and the chosen answer is recorded -- traps and controls, feature and
   random directions.

Controls are where a lure-specific feature should do nothing: the memorised word
is the correct answer there, so a flip on a control is damage, not success.

Run::

    python experiments/jobs/feature_dose.py --config experiments/configs/41_lure27b_feature_dose.toml \
        --output-root runs_shared
"""
# ruff: noqa: E402

from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
import time
from dataclasses import replace
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
for path in (ROOT, ROOT / "src"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import torch

from experiments.jobs.research_experiments import _load_sae, _load_splits, _resolve_env
from experiments.runners.config import load_toml, run_name, table
from mindscopex_analysis.generation import generate_constrained_choice_response
from mindscopex_analysis.lure_datasets import lure_dataset_cases
from mindscopex_analysis.models import load_qwen_language_model
from mindscopex_analysis.prompts import CRT_FINAL_ANSWER_SYSTEM_PROMPT
from mindscopex_analysis.qwen_scope import qwen_scope_sparse_feature_values, sae_decoder_direction
from mindscopex_analysis.research import (
    aggregate_feature_effect,
    find_decoder_block,
    random_direction_null_for_feature,
)


def _log(message: str) -> None:
    print(f"[dose] {message}", flush=True)


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def _as_control(case: Any, *, swap_answers: bool) -> Any:
    """The matched control as a case of its own.

    For margins the answer labels stay as they are, so ``margin > 0`` still means
    "the memorised word is preferred" and the trap and control margins are on one
    scale. For behaviour they are swapped, so ``correct`` means the right answer.
    """
    if swap_answers:
        return replace(
            case,
            case_id=f"{case.case_id}__control",
            prompt=case.control_prompt,
            correct_answer=case.lure_answer,
            lure_answer=case.correct_answer,
            control_prompt="",
        )
    return replace(case, case_id=f"{case.case_id}__control", prompt=case.control_prompt)


# ----------------------------------------------------------------- margin dose


def margin_dose(
    lm: Any,
    splits: dict[str, Any],
    *,
    layer: int,
    sae: Any,
    feature_id: int,
    coefficients: list[float],
    null_samples: int,
    null_seed: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for split_name, cases in (("held_out", splits["test"]), ("in_sample", splits["train"])):
        for kind in ("trap", "control"):
            batch = [c if kind == "trap" else _as_control(c, swap_answers=False) for c in cases]
            for coefficient in coefficients:
                _log(f"margin: {split_name} {kind} k={coefficient:g} on {len(batch)} items")
                effect = aggregate_feature_effect(
                    lm,
                    batch,
                    layer=layer,
                    sae=sae,
                    feature_id=feature_id,
                    coefficient=coefficient,
                    intervention_mode="remove_activation",
                )
                for case, row in zip(batch, effect["per_case"], strict=True):
                    value = float(row["feature_value"])
                    null: list[float] = []
                    if value > 0 and null_samples > 0:
                        null = random_direction_null_for_feature(
                            lm,
                            case,
                            layer=layer,
                            sae=sae,
                            feature_id=feature_id,
                            feature_value=value,
                            coefficient=coefficient,
                            n_samples=null_samples,
                            seed=null_seed,
                            baseline_margin=float(row["baseline_margin"]),
                        )
                    delta = float(row["margin_delta"])
                    rows.append(
                        {
                            "split": split_name,
                            "kind": kind,
                            "case_id": case.case_id,
                            "family": case.family,
                            "coefficient": coefficient,
                            "feature_value": value,
                            "baseline_margin": float(row["baseline_margin"]),
                            "edited_margin": float(row["edited_margin"]),
                            "margin_delta": delta,
                            # trap: lure -> correct is the goal. control: same sign
                            # change means the memorised (correct) answer was lost.
                            "crossed_zero": int(
                                row["baseline_margin"] > 0 and row["edited_margin"] < 0
                            ),
                            "null_mean": sum(null) / len(null) if null else None,
                            "null_percentile": (
                                sum(1 for x in null if x < delta) / len(null) if null else None
                            ),
                        }
                    )
    return rows


# ------------------------------------------------------------------ behaviour


def _removal_hook(sae: Any, feature_id: int, direction: torch.Tensor, coefficient: float):
    """Forward hook: subtract ``coefficient * a_t * direction`` at every position.

    ``a_t`` is the feature's actual TopK activation at that position, so k = 1 is
    an exact ablation and larger k pushes past zero. Passing a random direction of
    the decoder's norm instead gives the matched-norm control.
    """

    def hook(_module: Any, _inputs: Any, output: Any) -> Any:
        hidden = output[0] if isinstance(output, tuple) else output
        flat = hidden.reshape(-1, hidden.shape[-1])
        values = qwen_scope_sparse_feature_values(
            flat.to(device=sae.W_enc.device, dtype=sae.W_enc.dtype), sae, [feature_id]
        )[:, 0]
        values = values.to(device=hidden.device, dtype=hidden.dtype).reshape(*hidden.shape[:-1], 1)
        vec = direction.to(device=hidden.device, dtype=hidden.dtype)
        edited = hidden - float(coefficient) * values * vec
        if isinstance(output, tuple):
            return (edited, *output[1:])
        return edited

    return hook


def behaviour(
    lm: Any,
    config: dict[str, Any],
    splits: dict[str, Any],
    env: dict[str, Any],
    *,
    layer: int,
    sae: Any,
    feature_id: int,
    coefficients: list[float],
    random_coefficients: list[float],
    random_seeds: list[int],
) -> list[dict[str, Any]]:
    hf_model = getattr(lm, "_model", lm)
    tokenizer = lm.tokenizer
    block = find_decoder_block(
        hf_model, layer, block_path_template=env["profile"].block_path_template
    )
    direction = sae_decoder_direction(sae, [feature_id]).float()
    norm = float(torch.linalg.norm(direction))

    # The screen's own prompts: raw dataset cases (no instruction prefix), chat
    # template, thinking off, forced choice between the two answer strings.
    raw = {c.case_id: c for c in lure_dataset_cases(str(table(config, "data")["dataset"]))}
    membership = {c.case_id: "held_out" for c in splits["test"]}
    membership.update({c.case_id: "in_sample" for c in splits["train"]})

    arms: list[tuple[str, float, torch.Tensor | None]] = [("none", 0.0, None)]
    arms += [("feature", k, direction) for k in coefficients]
    for seed in random_seeds:
        generator = torch.Generator().manual_seed(int(seed))
        rand = torch.randn(direction.shape, generator=generator)
        rand = rand / torch.linalg.norm(rand) * norm
        arms += [(f"random{seed}", k, rand) for k in random_coefficients]

    rows: list[dict[str, Any]] = []
    for case_id, split_name in sorted(membership.items()):
        base = raw[case_id]
        for kind, case in (("trap", base), ("control", _as_control(base, swap_answers=True))):
            for arm, coefficient, vec in arms:
                handle = None
                if vec is not None:
                    handle = block.register_forward_hook(
                        _removal_hook(sae, feature_id, vec, coefficient)
                    )
                try:
                    response = generate_constrained_choice_response(
                        hf_model,
                        tokenizer,
                        case,
                        model_id=env["model_id"],
                        enable_thinking=False,
                        use_chat_template=True,
                        system_prompt=CRT_FINAL_ANSWER_SYSTEM_PROMPT,
                        seed=42,
                    )
                finally:
                    if handle is not None:
                        handle.remove()
                rows.append(
                    {
                        "split": split_name,
                        "kind": kind,
                        "case_id": case_id,
                        "family": base.family,
                        "arm": arm,
                        "coefficient": coefficient,
                        "label": response.evaluation_label,
                    }
                )
            _log(f"behaviour: {case_id} {kind} done")
    return rows


def _summaries(margin_rows: list[dict[str, Any]], behaviour_rows: list[dict[str, Any]]):
    margin_summary: list[dict[str, Any]] = []
    keys = sorted({(r["split"], r["kind"], r["coefficient"]) for r in margin_rows})
    for split_name, kind, coefficient in keys:
        group = [
            r for r in margin_rows
            if (r["split"], r["kind"], r["coefficient"]) == (split_name, kind, coefficient)
        ]
        active = [r for r in group if r["null_percentile"] is not None]
        margin_summary.append(
            {
                "split": split_name,
                "kind": kind,
                "coefficient": coefficient,
                "n": len(group),
                "mean_delta": sum(r["margin_delta"] for r in group) / len(group),
                "crossed_zero": sum(r["crossed_zero"] for r in group),
                "mean_null_delta": (
                    sum(r["null_mean"] for r in active) / len(active) if active else None
                ),
                "mean_null_percentile": (
                    sum(r["null_percentile"] for r in active) / len(active) if active else None
                ),
            }
        )
    behaviour_summary: list[dict[str, Any]] = []
    keys = sorted({(r["split"], r["kind"], r["arm"], r["coefficient"]) for r in behaviour_rows})
    for split_name, kind, arm, coefficient in keys:
        group = [
            r for r in behaviour_rows
            if (r["split"], r["kind"], r["arm"], r["coefficient"])
            == (split_name, kind, arm, coefficient)
        ]
        behaviour_summary.append(
            {
                "split": split_name,
                "kind": kind,
                "arm": arm,
                "coefficient": coefficient,
                "n": len(group),
                "correct": sum(r["label"] == "correct" for r in group),
                "lure": sum(r["label"] == "lure" for r in group),
            }
        )
    return margin_summary, behaviour_summary


def run(config_path: Path, output_root: Path) -> Path:
    config = load_toml(config_path)
    run_dir = output_root / run_name(config)
    run_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(config_path, run_dir / "config.toml")

    fcfg, dcfg, bcfg = table(config, "feature"), table(config, "dose"), table(config, "behaviour")
    layer, feature_id = int(fcfg["layer"]), int(fcfg["feature_id"])
    coefficients = [float(x) for x in dcfg.get("coefficients", [1, 2, 4, 8])]

    env = _resolve_env(config)
    splits = _load_splits(config)
    started = time.time()
    _log(f"loading {env['model_id']}")
    load_kwargs: dict[str, Any] = {}
    if env.get("max_memory"):
        load_kwargs["max_memory"] = env["max_memory"]
    lm = load_qwen_language_model(
        env["model_id"], device_map=env["device_map"], dtype=env["dtype"], **load_kwargs
    )
    sae = _load_sae(env, layer)
    _log(f"[{time.time() - started:5.0f}s] model and L{layer} SAE ready; feature {feature_id}")

    margin_rows = margin_dose(
        lm,
        splits,
        layer=layer,
        sae=sae,
        feature_id=feature_id,
        coefficients=coefficients,
        null_samples=int(dcfg.get("null_samples", 16)),
        null_seed=int(dcfg.get("null_seed", 0)),
    )
    _write_csv(run_dir / "margin_dose.csv", margin_rows)
    _log(f"[{time.time() - started:5.0f}s] margin dose written")

    behaviour_rows: list[dict[str, Any]] = []
    if bool(bcfg.get("enabled", True)):
        behaviour_rows = behaviour(
            lm,
            config,
            splits,
            env,
            layer=layer,
            sae=sae,
            feature_id=feature_id,
            coefficients=[float(x) for x in bcfg.get("coefficients", coefficients)],
            random_coefficients=[float(x) for x in bcfg.get("random_coefficients", [4, 8])],
            random_seeds=[int(x) for x in bcfg.get("random_seeds", [101, 102, 103])],
        )
        _write_csv(run_dir / "behaviour.csv", behaviour_rows)

    margin_summary, behaviour_summary = _summaries(margin_rows, behaviour_rows)
    _write_csv(run_dir / "margin_summary.csv", margin_summary)
    _write_csv(run_dir / "behaviour_summary.csv", behaviour_summary)
    (run_dir / "manifest.json").write_text(
        json.dumps(
            {
                "job": "feature_dose",
                "model_id": env["model_id"],
                "layer": layer,
                "feature_id": feature_id,
                "coefficients": coefficients,
                "n_train": len(splits["train"]),
                "n_test": len(splits["test"]),
                "elapsed_seconds": round(time.time() - started, 1),
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    print("\n== margin (held-out traps vs controls)")
    for row in margin_summary:
        if row["split"] == "held_out":
            pct = row["mean_null_percentile"]
            print(
                f"  {row['kind']:7s} k={row['coefficient']:<3g} mean_delta={row['mean_delta']:+.3f} "
                f"crossed_zero={row['crossed_zero']}/{row['n']} "
                f"null_pct={'-' if pct is None else f'{pct:.2f}'}"
            )
    print("\n== behaviour (held-out, chat format, thinking off)")
    for row in behaviour_summary:
        if row["split"] == "held_out":
            print(
                f"  {row['kind']:7s} {row['arm']:10s} k={row['coefficient']:<3g} "
                f"correct={row['correct']}/{row['n']} lure={row['lure']}/{row['n']}"
            )
    print(f"ARTIFACT_DIR={run_dir}", flush=True)
    return run_dir


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output-root", default=Path("outputs/experiments"), type=Path)
    args = parser.parse_args()
    run(args.config, args.output_root)


if __name__ == "__main__":
    main()
