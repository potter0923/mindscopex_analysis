# Copyright 2026 MindScopeX
"""Screen trap items on what the model *says*, not on a selection score.

Item 2 of the 2026-10-03 plan ends with a requirement that is easy to skip:

    each item must pass on the actual answer, not on the selection score alone.

A logprob margin only says the lure outranks the correct answer among two strings
the scorer picked. The model can hold that preference and still emit neither. The
earlier synthetic attempt kept 2 of 36 pairs once real answers were read, so the
gap between the two tests is where most items die.

This job therefore asks for an answer, reads the generated text, and reports four
things per item:

``lure``        the model produced the lure            -- the item works
``correct``     the model produced the correct answer  -- no trap here
``other``       neither string appeared                -- usually a malformed item
``margin``      logprob(lure) - logprob(correct)       -- for comparison only

An item is kept when the hostile rungs draw the lure **and** the matched control
draws the correct answer. A control that also fails is the pattern that sank the
goal-affordance set: the intervention looked specific, but the control had simply
broken too.

Run::

    python -m experiments.jobs.screen_traps --profile 9b --dataset kanghun_traps_v1

Nothing here rewrites an item. Failures are reported and stay in the file, because
editing items until a model falls for them is how a benchmark stops measuring the
model and starts measuring the editing.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

from mindscopex_analysis.lure_datasets import load_lure_dataset
from mindscopex_analysis.models import (
    QWEN35_ANALYSIS_PROFILES,
    get_qwen35_analysis_profile,
    load_qwen_text_generation_model,
)

DEFAULT_MAX_NEW_TOKENS = 24


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--profile", default="9b", choices=sorted(QWEN35_ANALYSIS_PROFILES))
    parser.add_argument("--dataset", default="kanghun_traps_v1")
    parser.add_argument("--max-new-tokens", type=int, default=DEFAULT_MAX_NEW_TOKENS)
    parser.add_argument("--out-root", default="results/runs")
    parser.add_argument("--tag", default="screen")
    parser.add_argument(
        "--skip-controls",
        action="store_true",
        help="Screen only the trap rungs. Faster, but then a dead control goes unseen.",
    )
    return parser.parse_args(argv)


def normalise(text: str) -> str:
    """Lowercase, strip currency/punctuation noise, collapse spaces.

    ``"$0.10"``, ``"0.10 dollars"`` and ``"  $0.10."`` all have to count as the
    same answer, or the screen rejects items the model actually got right.
    """
    text = text.lower().replace(",", "")
    text = re.sub(r"[^a-z0-9.$ ]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def contains_answer(generated: str, answer: str) -> bool:
    """Whether ``answer`` appears in ``generated``, numerals compared as numbers."""
    haystack = normalise(generated)
    needle = normalise(answer)
    if needle and needle in haystack:
        return True
    numbers = re.findall(r"\d+(?:\.\d+)?", needle)
    if not numbers:
        return False
    found = re.findall(r"\d+(?:\.\d+)?", haystack)
    return all(any(float(n) == float(f) for f in found) for n in numbers)


def classify(generated: str, correct: str, lure: str) -> str:
    # One answer can sit inside the other ("Eligible" / "Not eligible"). Plain
    # substring checks would then see both in every correct reply and call it
    # "other", so test the longer phrase first and only fall back to the shorter.
    norm_correct, norm_lure = normalise(correct), normalise(lure)
    if norm_correct and norm_lure and (norm_correct in norm_lure or norm_lure in norm_correct):
        haystack = normalise(generated)
        if len(norm_correct) >= len(norm_lure):
            longer, shorter, longer_label, shorter_label = norm_correct, norm_lure, "correct", "lure"
        else:
            longer, shorter, longer_label, shorter_label = norm_lure, norm_correct, "lure", "correct"
        if longer in haystack:
            return longer_label
        if shorter in haystack:
            return shorter_label
        return "other"
    has_lure = contains_answer(generated, lure)
    has_correct = contains_answer(generated, correct)
    if has_lure and not has_correct:
        return "lure"
    if has_correct and not has_lure:
        return "correct"
    return "other"


def generate(model: Any, tokenizer: Any, prompt: str, max_new_tokens: int) -> str:
    import torch

    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
    with torch.no_grad():
        out = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,  # greedy: the screen must be reproducible
            pad_token_id=getattr(tokenizer, "pad_token_id", None)
            or getattr(tokenizer, "eos_token_id", None),
        )
    return tokenizer.decode(out[0][inputs["input_ids"].shape[1] :], skip_special_tokens=True)


def answer_margin(model: Any, tokenizer: Any, prompt: str, correct: str, lure: str) -> float:
    """``logprob(lure) - logprob(correct)`` for the two full answer strings."""
    import torch

    def score(answer: str) -> float:
        full = tokenizer(prompt + answer, return_tensors="pt").to(model.device)
        prefix_len = tokenizer(prompt, return_tensors="pt")["input_ids"].shape[1]
        with torch.no_grad():
            logits = model(**full).logits
        logprobs = torch.log_softmax(logits[0, :-1].float(), dim=-1)
        targets = full["input_ids"][0, 1:]
        picked = logprobs[range(len(targets)), targets]
        return float(picked[prefix_len - 1 :].sum())

    return score(lure) - score(correct)


def run(args: argparse.Namespace) -> dict[str, Any]:
    profile = get_qwen35_analysis_profile(args.profile)
    cases = load_lure_dataset(args.dataset)
    print(f"{profile.behavior_model_id}  ·  {args.dataset}  n={len(cases)}", flush=True)

    started = time.time()
    model, loaded = load_qwen_text_generation_model(profile.behavior_model_id)
    tokenizer = getattr(loaded, "tokenizer", loaded)
    print(f"[{time.time() - started:6.0f}s] model loaded", flush=True)

    rows: list[dict[str, Any]] = []
    for index, case in enumerate(cases, start=1):
        generated = generate(model, tokenizer, case.prompt, args.max_new_tokens)
        row = {
            "case_id": case.case_id,
            "pair_id": case.pair_id,
            "condition": case.condition,
            "family": case.family,
            "verdict": classify(generated, case.correct_answer, case.lure_answer),
            "generated": generated.strip()[:160],
            "margin": answer_margin(
                model, tokenizer, case.prompt, case.correct_answer, case.lure_answer
            ),
        }
        if case.control_prompt and not args.skip_controls:
            control = generate(model, tokenizer, case.control_prompt, args.max_new_tokens)
            # The control removes the decisive condition, so the lure is correct there.
            row["control_verdict"] = classify(
                control, case.lure_answer, case.correct_answer
            )
            row["control_generated"] = control.strip()[:160]
        rows.append(row)
        print(
            f"[{index:3d}/{len(cases)}] {case.case_id:52s} {row['verdict']:8s}"
            f" control={row.get('control_verdict', '-'):8s} margin={row['margin']:+7.2f}",
            flush=True,
        )

    kept, dropped = [], []
    for pair_id in sorted({row["pair_id"] for row in rows}):
        rungs = [row for row in rows if row["pair_id"] == pair_id]
        traps_fire = sum(row["verdict"] == "lure" for row in rungs)
        controls = {row.get("control_verdict") for row in rungs} - {None}
        control_ok = controls == {"correct"} if controls else None
        entry = {
            "pair_id": pair_id,
            "rungs": len(rungs),
            "lure_rungs": traps_fire,
            "control_ok": control_ok,
            "by_condition": {row["condition"]: row["verdict"] for row in rungs},
        }
        (kept if traps_fire and control_ok is not False else dropped).append(entry)

    result = {
        "config": {
            "profile": args.profile,
            "model_id": profile.behavior_model_id,
            "dataset": args.dataset,
            "max_new_tokens": args.max_new_tokens,
            "decoding": "greedy",
        },
        "rows": rows,
        "kept": kept,
        "dropped": dropped,
        "elapsed_seconds": round(time.time() - started, 1),
    }
    run_dir = Path(args.out_root) / f"screen_{args.dataset}_{args.profile}_{args.tag}"
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(f"\nkept {len(kept)} / {len(kept) + len(dropped)} scenarios")
    for entry in kept + dropped:
        ladder = " ".join(
            f"{condition[:4]}={verdict[:4]}"
            for condition, verdict in entry["by_condition"].items()
        )
        mark = "keep" if entry in kept else "drop"
        print(f"  [{mark}] {entry['pair_id']:22s} control={entry['control_ok']}  {ladder}")
    print(f"\nwritten to {run_dir / 'result.json'}")
    return result


if __name__ == "__main__":
    run(parse_args(sys.argv[1:]))
