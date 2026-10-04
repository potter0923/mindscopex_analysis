# Copyright 2026 MindScopeX
"""Item 1 of the 2026-10-03 plan: is the J-lens better than the logit lens on 9B?

    Fit the lens on N cases, read the held-out rest at every scanned layer with
    both lenses, and correlate each readout against the answer the model actually
    ends up preferring.

The 2026-10-02 run did this on 2B and got 0.35 for the Jacobian lens against 0.10
for the logit lens, but the interval around the *difference* contained zero, so no
win could be claimed. The phenomenon under study is cleanest on 9B, so this job
repeats the comparison there, with a paired bootstrap over cases that makes the
difference testable rather than eyeballed.

What this job does **not** do: claim a mechanism. A lens readout that tracks the
final answer is a place to look next, not a cause. The paper separates the two and
so does this.

Run::

    # cheap rehearsal first: catches every bug on a free GPU
    python -m experiments.jobs.jlens_item1 --profile 2b --n-fit 20 --tag rehearsal

    # pipeline check on the real model
    python -m experiments.jobs.jlens_item1 --profile 9b --n-fit 20 --tag smoke

    # the plan as written
    python -m experiments.jobs.jlens_item1 --profile 9b --n-fit 105 --tag main

Fitting cost per prompt is one forward plus ``ceil(hidden_size / dim_batch)``
backwards, so 9B at ``dim_batch=16`` is 256 backwards per prompt. Budget roughly
half an hour for 20 prompts and a few hours for 105 on an A100. The lens is cached
at ``--lens-path`` and the fit checkpoints, so a killed session resumes instead of
starting over.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

from mindscopex_analysis import jlens
from mindscopex_analysis.lure_datasets import load_lure_dataset
from mindscopex_analysis.models import (
    QWEN35_ANALYSIS_PROFILES,
    get_qwen35_analysis_profile,
    load_qwen_text_generation_model,
)

DEFAULT_DATASET = "hagendorff_crt"
DEFAULT_N_FIT = 105
DEFAULT_SEED = 0
DEFAULT_DIM_BATCH = 16
DEFAULT_LAYER_STRIDE = 2


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--profile", default="9b", choices=sorted(QWEN35_ANALYSIS_PROFILES))
    parser.add_argument("--dataset", default=DEFAULT_DATASET)
    parser.add_argument("--n-fit", type=int, default=DEFAULT_N_FIT)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--dim-batch", type=int, default=DEFAULT_DIM_BATCH)
    parser.add_argument(
        "--layer-stride",
        type=int,
        default=DEFAULT_LAYER_STRIDE,
        help="Fit every Nth layer. Every layer is expensive and adjacent layers move together.",
    )
    parser.add_argument("--tag", default="main", help="Label for the output directory.")
    parser.add_argument("--out-root", default="results/runs")
    parser.add_argument("--lens-path", default=None, help="Defaults to the run directory.")
    parser.add_argument("--bootstrap-draws", type=int, default=2000)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the plan and the split, load no model.",
    )
    return parser.parse_args(argv)


def build_plan(args: argparse.Namespace) -> dict[str, Any]:
    """Resolve everything that does not need a GPU, so --dry-run can show it."""
    profile = get_qwen35_analysis_profile(args.profile)
    cases = load_lure_dataset(args.dataset)
    fit_cases, eval_cases = jlens.split_fit_eval(cases, n_fit=args.n_fit, seed=args.seed)
    layers = list(range(0, profile.num_layers - 1, args.layer_stride))
    backwards = -(-profile.hidden_size // args.dim_batch)
    return {
        "profile": profile,
        "model_id": profile.behavior_model_id,
        "dataset": args.dataset,
        "n_cases": len(cases),
        "fit_cases": fit_cases,
        "eval_cases": eval_cases,
        "layers": layers,
        "backwards_per_prompt": backwards,
        "total_backwards": backwards * len(fit_cases),
    }


def describe(plan: dict[str, Any]) -> str:
    profile = plan["profile"]
    return "\n".join(
        [
            f"model        {plan['model_id']}  ({profile.num_layers} layers, d={profile.hidden_size})",
            f"dataset      {plan['dataset']}  n={plan['n_cases']}",
            f"split        fit {len(plan['fit_cases'])} / eval {len(plan['eval_cases'])}",
            f"layers       {plan['layers']}",
            f"fit cost     {plan['backwards_per_prompt']} backwards/prompt"
            f"  ->  {plan['total_backwards']:,} total",
        ]
    )


def run(args: argparse.Namespace) -> dict[str, Any]:
    plan = build_plan(args)
    print(describe(plan), flush=True)
    if args.dry_run:
        return {"dry_run": True}

    run_dir = Path(args.out_root) / f"jlens_item1_{args.profile}_{args.tag}"
    run_dir.mkdir(parents=True, exist_ok=True)
    lens_path = Path(args.lens_path) if args.lens_path else run_dir / "lens.pt"

    started = time.time()
    hf_model, loaded = load_qwen_text_generation_model(plan["model_id"])
    tokenizer = jlens.as_tokenizer(loaded)  # Qwen3.5 arrives as an AutoProcessor
    model = jlens.wrap_model(hf_model, tokenizer)
    print(f"[{time.time() - started:6.0f}s] model loaded", flush=True)

    lens = jlens.load_or_fit_lens(
        model,
        path=str(lens_path),
        prompts=[case.prompt for case in plan["fit_cases"]],
        source_layers=plan["layers"],
        dim_batch=args.dim_batch,
        checkpoint_path=str(run_dir / "lens_checkpoint.pt"),
    )
    print(f"[{time.time() - started:6.0f}s] lens ready at {lens_path}", flush=True)

    readouts: dict[str, Any] = {}
    for name, use_jacobian in (("jacobian", True), ("logit", False)):
        margins, finals, skipped = jlens.margin_scan(
            lens,
            model,
            tokenizer,
            plan["eval_cases"],
            layers=plan["layers"],
            use_jacobian=use_jacobian,
        )
        readouts[name] = {"margins": margins, "finals": finals, "skipped": skipped}
        print(
            f"[{time.time() - started:6.0f}s] {name}: "
            f"{len(finals)} cases read, {len(skipped)} skipped (shared first token)",
            flush=True,
        )

    correlations = {
        name: jlens.layer_correlations(data["margins"], data["finals"])
        for name, data in readouts.items()
    }
    rows = jlens.comparison_rows(correlations["jacobian"], correlations["logit"])

    scored = [row for row in rows if row["delta"] is not None]
    best = max(scored, key=lambda row: row["jacobian"]) if scored else None
    interval = None
    if best is not None:
        point, low, high = jlens.bootstrap_delta_ci(
            readouts["jacobian"]["margins"][best["layer"]],
            readouts["logit"]["margins"][best["layer"]],
            readouts["jacobian"]["finals"],
            draws=args.bootstrap_draws,
            seed=args.seed,
        )
        interval = {"layer": best["layer"], "delta": point, "low": low, "high": high}

    result = {
        "config": {
            "profile": args.profile,
            "model_id": plan["model_id"],
            "dataset": args.dataset,
            "n_fit": len(plan["fit_cases"]),
            "n_eval": len(plan["eval_cases"]),
            "seed": args.seed,
            "layers": plan["layers"],
            "dim_batch": args.dim_batch,
            "target_layer": jlens.DEFAULT_TARGET_LAYER,
        },
        "eval_case_ids": [case.case_id for case in plan["eval_cases"]],
        "skipped_case_ids": readouts["jacobian"]["skipped"],
        "correlations": rows,
        "best_layer": best,
        "delta_ci": interval,
        "elapsed_seconds": round(time.time() - started, 1),
    }
    (run_dir / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")

    print("\nlayer   J-lens   logit    delta")
    for row in rows:
        print(
            f"{row['layer']:5d}"
            f"{_fmt(row['jacobian'])}{_fmt(row['logit'])}{_fmt(row['delta'])}"
        )
    if interval is not None:
        verdict = "J-lens ahead" if interval["low"] > 0 else "not separable from zero"
        print(
            f"\nbest layer {interval['layer']}: "
            f"delta {interval['delta']:+.3f} "
            f"[{interval['low']:+.3f}, {interval['high']:+.3f}]  -> {verdict}"
        )
    print(f"\nwritten to {run_dir / 'result.json'}")
    return result


def _fmt(value: float | None) -> str:
    return "      -" if value is None else f"{value:+8.3f}"


if __name__ == "__main__":
    run(parse_args(sys.argv[1:]))
