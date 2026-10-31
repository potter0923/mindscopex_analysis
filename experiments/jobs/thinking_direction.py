"""How far does the thinking direction go? (27B, follow-up to run 48)

Run 48 found that adding 2x the train-mean (thinking ON - thinking OFF) residual at
the answer slot of layer 47 flips every held-out lure27b trap to the instructed
answer with thinking off, leaves the matched controls intact, and that matched-norm
random directions do not. Six held-out items is too few, so this job asks the three
questions that decide whether it is a result:

1. **Leave-one-out, all 18 items.** Each item is steered with the direction built
   from the *other* items only, at several layers and strengths, with random
   directions of the same norm. Traps and matched controls.
2. **Sanity set.** Plain questions whose obvious answer is right (facts, arithmetic,
   sayings with no instruction to change them). The direction should not move
   them; a free-generation sample per item shows whether the text stays fluent.
3. **Transfer.** The direction built from all completed lure27b items, applied to
   other datasets as they are: CRT (hagendorff, crt_fresh_v2), 동준's goal-affordance
   traps, and the other kanghun / external sets, traps and controls. Thinking off,
   forced choice, the same protocol as run 48.

All edits are at the answer slot only (last prompt token), thinking off, chat
template, instructed prompt, no system prompt -- run 48's protocol. Rows are
appended as they are produced and a rerun skips rows already on disk, so a recycled
VM resumes from the last checkpoint push.

Run::

    python experiments/jobs/thinking_direction.py \\
        --config experiments/configs/49_lure27b_thinking_direction.toml --output-root runs_shared
"""
# ruff: noqa: E402

from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
import time
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
for _path in (ROOT, ROOT / "src"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from experiments.jobs.thinking_patch import (
    _add_edit,
    _as_control,
    _EditHook,
    gap_closure,
    tail_after_close,
)


def _log(message: str) -> None:
    print(f"[direction] {message}", flush=True)


# Questions whose obvious answer is the right one. Nothing here asks the model to
# override what it knows, so a direction that only "follows the instruction over the
# memorised answer" should leave all of them alone.
SANITY_ITEMS: tuple[tuple[str, str, str, str], ...] = (
    ("fact_capital_france", "What is the capital of France?", "Paris", "Lyon"),
    ("fact_capital_japan", "What is the capital of Japan?", "Tokyo", "Osaka"),
    ("fact_capital_italy", "What is the capital of Italy?", "Rome", "Milan"),
    ("fact_spider_legs", "How many legs does a spider have?", "8", "6"),
    ("fact_week_days", "How many days are in a week?", "7", "5"),
    ("fact_sky", "What color is the sky on a clear day?", "blue", "green"),
    ("fact_water_freeze", "At what temperature in Celsius does water freeze?", "0", "10"),
    ("fact_planet_red", "Which planet is known as the Red Planet?", "Mars", "Venus"),
    ("fact_largest_ocean", "What is the largest ocean on Earth?", "Pacific", "Atlantic"),
    ("fact_author_hamlet", "Who wrote Hamlet?", "Shakespeare", "Dickens"),
    ("fact_ice", "What is frozen water called?", "ice", "steam"),
    ("fact_opposite_hot", "What is the opposite of 'hot'?", "cold", "warm"),
    ("fact_opposite_up", "What is the opposite of 'up'?", "down", "left"),
    ("fact_baby_cat", "What is a baby cat called?", "kitten", "puppy"),
    ("fact_bees", "Which insect makes honey?", "bee", "ant"),
    ("math_add", "What is 7 + 5?", "12", "13"),
    ("math_mul", "What is 6 x 4?", "24", "26"),
    ("math_sub", "What is 15 - 9?", "6", "7"),
    ("math_div", "What is 20 divided by 4?", "5", "4"),
    ("math_sq", "What is 9 squared?", "81", "18"),
    ("seq_letters", "What letter comes after C in the alphabet?", "D", "E"),
    ("seq_count", "What number comes after 99?", "100", "101"),
    ("say_late", "Complete the saying: Better late than", "never", "sorry"),
    ("say_eggs", "Complete the saying: Don't put all your eggs in one", "basket", "drawer"),
    ("say_bird", "Complete the saying: The early bird catches the", "worm", "spoon"),
    ("say_rome", "Complete the saying: Rome wasn't built in a", "day", "tomorrow"),
    ("say_apple", "Complete the saying: An apple a day keeps the", "doctor", "busy"),
    ("say_cat", "Complete the saying: Curiosity killed the", "cat", "dog"),
    ("instr_word", "Answer with one word. What animal says 'moo'?", "cow", "dog"),
    ("instr_number", "Answer with a number only. How many wheels does a bicycle have?", "2", "3"),
)


# ===================================================================== pure logic


def leave_one_out_means(diffs: Mapping[str, Any], *, include: Iterable[str]) -> dict[str, Any]:
    """For each key, the mean of the *other* included items' difference vectors.

    ``diffs`` maps item -> vector (anything supporting ``+`` and ``/``); only items in
    ``include`` (e.g. traces that finished) contribute, but every key gets a mean, so
    an item whose own trace never closed is still evaluated with the others' mean.
    """

    pool = [k for k in include if k in diffs]
    if not pool:
        return {}
    total = None
    for key in pool:
        total = diffs[key] if total is None else total + diffs[key]
    out = {}
    for key in diffs:
        others = len(pool) - (1 if key in pool else 0)
        if others == 0:
            continue
        out[key] = (total - diffs[key]) / others if key in pool else total / others
    return out


def row_key(row: Mapping[str, Any], keys: Sequence[str]) -> tuple[str, ...]:
    return tuple(str(row.get(k, "")) for k in keys)


class RowLog:
    """CSV that is appended to as rows arrive and skips rows already on disk."""

    def __init__(self, path: Path, keys: Sequence[str]) -> None:
        self.path = path
        self.keys = list(keys)
        self.done: set[tuple[str, ...]] = set()
        self.rows: list[dict[str, Any]] = []
        if path.exists():
            with path.open(encoding="utf-8", newline="") as handle:
                for row in csv.DictReader(handle):
                    self.rows.append(dict(row))
                    self.done.add(row_key(row, self.keys))

    def has(self, **key: Any) -> bool:
        return row_key(key, self.keys) in self.done

    def add(self, row: dict[str, Any]) -> None:
        self.rows.append(row)
        self.done.add(row_key(row, self.keys))

    def flush(self) -> None:
        if not self.rows:
            return
        columns: list[str] = []
        for row in self.rows:
            for key in row:
                if key not in columns:
                    columns.append(key)
        tmp = self.path.with_suffix(".tmp")
        with tmp.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=columns)
            writer.writeheader()
            for row in self.rows:
                writer.writerow({c: row.get(c, "") for c in columns})
        tmp.replace(self.path)


def count_table(
    rows: Sequence[Mapping[str, Any]], keys: Sequence[str], baseline_arm: str = "none"
) -> list[dict[str, Any]]:
    """Per group: n, correct, and how many answers flipped vs the unedited arm.

    ``lure_to_correct`` is the goal on traps; ``correct_to_lure`` is damage. Both are
    computed against the same item's ``baseline_arm`` row, so an item that was
    already right does not count as a fix.
    """

    base = {
        (str(r.get("dataset", "")), str(r["item"]), str(r["kind"])): r["label"]
        for r in rows
        if r.get("arm") == baseline_arm
    }
    groups: dict[tuple[str, ...], list[Mapping[str, Any]]] = {}
    for r in rows:
        groups.setdefault(row_key(r, keys), []).append(r)
    out = []
    for key in sorted(groups):
        group = groups[key]
        fixes = damage = 0
        for r in group:
            before = base.get((str(r.get("dataset", "")), str(r["item"]), str(r["kind"])))
            if before == "lure" and r["label"] == "correct":
                fixes += 1
            if before == "correct" and r["label"] == "lure":
                damage += 1
        gaps = [float(r["gap_closure"]) for r in group if r.get("gap_closure") not in (None, "")]
        out.append(
            {
                **dict(zip(keys, key, strict=True)),
                "n": len(group),
                "correct": sum(1 for r in group if r["label"] == "correct"),
                "lure_to_correct": fixes,
                "correct_to_lure": damage,
                "mean_gap_closure": sum(gaps) / len(gaps) if gaps else "",
            }
        )
    return out


def _write_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    if not rows:
        return
    columns: list[str] = []
    for row in rows:
        for key in row:
            if key not in columns:
                columns.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({c: row.get(c, "") for c in columns})


# ===================================================================== the run


def _random_like(vector: Any, seed: int, norm: float) -> Any:
    import torch

    gen = torch.Generator().manual_seed(int(seed))
    rand = torch.randn(vector.shape, generator=gen)
    return rand / rand.norm() * float(norm)


def run(config_path: Path, output_root: Path) -> Path:
    import torch

    from experiments.jobs.research_experiments import _load_splits, _resolve_env
    from experiments.jobs.thinking_patch import Runner
    from experiments.runners.config import load_toml, run_name, table
    from mindscopex_analysis.cases import LureCase
    from mindscopex_analysis.lure_datasets import lure_dataset_cases
    from mindscopex_analysis.models import load_qwen_language_model
    from mindscopex_analysis.prompts import instruct_lure_cases

    config = load_toml(config_path)
    run_dir = output_root / run_name(config)
    run_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(config_path, run_dir / "config.toml")

    lcfg, scfg, xcfg = table(config, "loo"), table(config, "sanity"), table(config, "transfer")
    tcfg = table(config, "thinking")
    layers = [int(x) for x in lcfg.get("layers", [39, 47, 51, 55])]
    alphas = [float(x) for x in lcfg.get("alphas", [1.0, 1.5, 2.0, 3.0])]
    random_seeds = [int(x) for x in lcfg.get("random_seeds", [101, 102, 103])]
    random_alpha = float(lcfg.get("random_alpha", 2.0))
    min_gap = float(lcfg.get("min_gap", 0.5))
    edit_arms = [(int(a[0]), float(a[1])) for a in xcfg.get("arms", [[47, 2.0], [47, 1.0]])]
    xrandom = [int(x) for x in xcfg.get("random_seeds", [101])]
    datasets = [str(x) for x in xcfg.get("datasets", [])]
    gen_tokens = int(scfg.get("generate_tokens", 40))

    env = _resolve_env(config)
    splits = _load_splits(config)
    cases = sorted(splits["all"], key=lambda c: c.case_id)
    traces_path = ROOT / str(
        tcfg.get("traces", "runs_shared/43_lure27b_trajectory_long/traces.json")
    )
    traces = {
        t["case_id"]: t
        for t in json.loads(traces_path.read_text(encoding="utf-8"))
        if bool(t["thinking"])
    }

    started = time.time()
    _log(f"loading {env['model_id']}")
    load_kwargs: dict[str, Any] = {}
    if env.get("max_memory"):
        load_kwargs["max_memory"] = env["max_memory"]
    lm = load_qwen_language_model(
        env["model_id"], device_map=env["device_map"], dtype=env["dtype"], **load_kwargs
    )
    runner = Runner(getattr(lm, "_model", lm), lm.tokenizer, env["profile"].block_path_template)
    all_layers = sorted(set(layers) | {layer for layer, _ in edit_arms})
    _log(f"[{time.time() - started:5.0f}s] model ready")

    def evaluate(log: RowLog, ctx, cor, lur, hooks, **key: Any) -> dict[str, Any] | None:
        if log.has(**key):
            return None
        row = dict(key)
        row["margin"] = runner.margin(ctx, cor, lur, hooks)
        row["label"] = runner.choose(ctx, cor, lur, hooks)
        log.add(row)
        return row

    def answer_slot_hooks(layer: int, vector: Any, ctx: Sequence[int]):
        return [(layer, _EditHook([len(ctx) - 1], _add_edit(vector)))]

    # ---------------------------------------------- capture ON / OFF (18 items)
    items: dict[str, dict[str, Any]] = {}
    for case in cases:
        off_ids = runner.prompt_ids(case.prompt, thinking=False)
        tail = tail_after_close(off_ids, runner.close_ids)
        trace = traces.get(case.case_id)
        item: dict[str, Any] = {
            "case": case,
            "off_ids": off_ids,
            "cor": runner.answer_ids(case.correct_answer),
            "lur": runner.answer_ids(case.lure_answer),
        }
        item["off_cap"] = runner.capture(off_ids, all_layers, 1)
        item["off_margin"] = runner.margin(off_ids, item["cor"], item["lur"])
        if trace is not None and tail is not None:
            on_ids, completed = runner.on_context(case.prompt, trace["raw_text"], tail)
            item["on_cap"] = runner.capture(on_ids, all_layers, 1)
            item["on_margin"] = runner.margin(on_ids, item["cor"], item["lur"])
            item["on_completed"] = completed
        ctl = _as_control(case)
        item["ctl"] = (
            runner.prompt_ids(ctl.prompt, thinking=False),
            runner.answer_ids(ctl.correct_answer),
            runner.answer_ids(ctl.lure_answer),
        )
        items[case.case_id] = item
    completed_ids = [k for k, it in items.items() if it.get("on_completed")]
    _log(f"[{time.time() - started:5.0f}s] captured {len(items)} items, {len(completed_ids)} done")

    directions: dict[int, dict[str, Any]] = {}
    global_dir: dict[int, Any] = {}
    for layer in all_layers:
        diffs = {
            k: it["on_cap"][layer][-1] - it["off_cap"][layer][-1]
            for k, it in items.items()
            if "on_cap" in it
        }
        directions[layer] = leave_one_out_means(diffs, include=completed_ids)
        global_dir[layer] = torch.stack([diffs[k] for k in completed_ids]).mean(0)
    torch.save(
        {layer: vec.clone() for layer, vec in global_dir.items()}, run_dir / "global_directions.pt"
    )
    _write_csv(
        run_dir / "direction_norms.csv",
        [{"layer": layer, "global_norm": float(global_dir[layer].norm())} for layer in all_layers],
    )

    # ------------------------------------------------------- 1. leave-one-out
    loo = RowLog(run_dir / "loo.csv", ["layer", "item", "kind", "arm", "alpha"])
    for layer in layers:
        for key, it in items.items():
            vec = directions[layer].get(key)
            if vec is None:
                continue
            for kind in ("trap", "control"):
                ctx, cor, lur = (
                    (it["off_ids"], it["cor"], it["lur"]) if kind == "trap" else it["ctl"]
                )
                arms = [("none", 0.0, None)]
                arms += [("loo_dir", a, a * vec) for a in alphas]
                arms += [
                    (f"random{s}", random_alpha, _random_like(vec, s, vec.norm() * random_alpha))
                    for s in random_seeds
                ]
                for arm, alpha, edit in arms:
                    hooks = [] if edit is None else answer_slot_hooks(layer, edit, ctx)
                    row = evaluate(
                        loo,
                        ctx,
                        cor,
                        lur,
                        hooks,
                        layer=layer,
                        item=key,
                        kind=kind,
                        arm=arm,
                        alpha=alpha,
                    )
                    if row is not None and kind == "trap" and "on_margin" in it:
                        row["on_completed"] = it["on_completed"]
                        row["gap_closure"] = gap_closure(
                            it["off_margin"], row["margin"], it["on_margin"], min_gap=min_gap
                        )
            loo.flush()
        _log(f"[{time.time() - started:5.0f}s] loo layer {layer} done")
    _write_csv(
        run_dir / "loo_summary.csv", count_table(loo.rows, ["layer", "kind", "arm", "alpha"])
    )

    # ------------------------------------------------------------ 2. sanity
    sanity = RowLog(run_dir / "sanity.csv", ["item", "kind", "arm", "layer", "alpha"])
    gens: list[dict[str, Any]] = []
    sanity_arms = [("none", 0, 0.0, None)]
    sanity_arms += [("global_dir", layer, a, a * global_dir[layer]) for layer, a in edit_arms]
    for seed in xrandom:
        layer, a = edit_arms[0]
        vec = global_dir[layer]
        sanity_arms.append((f"random{seed}", layer, a, _random_like(vec, seed, vec.norm() * a)))
    for item_id, question, correct, lure in SANITY_ITEMS:
        case = instruct_lure_cases(
            [
                LureCase(
                    case_id=item_id,
                    family="sanity",
                    prompt=question.strip() + "\nAnswer:",
                    correct_answer=correct,
                    lure_answer=lure,
                )
            ]
        )[0]
        ctx = runner.prompt_ids(case.prompt, thinking=False)
        cor, lur = runner.answer_ids(correct), runner.answer_ids(lure)
        for arm, layer, alpha, edit in sanity_arms:
            hooks = [] if edit is None else answer_slot_hooks(layer, edit, ctx)
            evaluate(
                sanity,
                ctx,
                cor,
                lur,
                hooks,
                item=item_id,
                kind="sanity",
                arm=arm,
                layer=layer,
                alpha=alpha,
            )
            if gen_tokens > 0:
                text = _generate(runner, ctx, hooks, gen_tokens)
                gens.append(
                    {"item": item_id, "arm": arm, "layer": layer, "alpha": alpha, "text": text}
                )
    sanity.flush()
    _write_csv(run_dir / "sanity_generations.csv", gens)
    _write_csv(
        run_dir / "sanity_summary.csv", count_table(sanity.rows, ["kind", "arm", "layer", "alpha"])
    )
    _log(f"[{time.time() - started:5.0f}s] sanity done")

    # ----------------------------------------------------------- 3. transfer
    transfer = RowLog(
        run_dir / "transfer.csv", ["dataset", "item", "kind", "arm", "layer", "alpha"]
    )
    t_arms = [("none", 0, 0.0, None)]
    t_arms += [("global_dir", layer, a, a * global_dir[layer]) for layer, a in edit_arms]
    for seed in xrandom:
        layer, a = edit_arms[0]
        vec = global_dir[layer]
        t_arms.append((f"random{seed}", layer, a, _random_like(vec, seed, vec.norm() * a)))
    for dataset in datasets:
        try:
            dcases = instruct_lure_cases(lure_dataset_cases(dataset))
        except Exception as exc:  # noqa: BLE001 -- one bad dataset must not stop the queue
            _log(f"skip {dataset}: {exc}")
            continue
        for case in dcases:
            if not case.correct_answer.strip() or not case.lure_answer.strip():
                continue
            pairs = [("trap", case)]
            if case.control_prompt:
                pairs.append(("control", _as_control(case)))
            for kind, c in pairs:
                try:
                    ctx = runner.prompt_ids(c.prompt, thinking=False)
                    cor, lur = runner.answer_ids(c.correct_answer), runner.answer_ids(c.lure_answer)
                    if not cor or not lur or cor == lur:
                        continue
                    for arm, layer, alpha, edit in t_arms:
                        hooks = [] if edit is None else answer_slot_hooks(layer, edit, ctx)
                        row = evaluate(
                            transfer,
                            ctx,
                            cor,
                            lur,
                            hooks,
                            dataset=dataset,
                            item=c.case_id,
                            kind=kind,
                            arm=arm,
                            layer=layer,
                            alpha=alpha,
                        )
                        if row is not None:
                            row["family"] = c.family
                            row["condition"] = getattr(c, "condition", "")
                except Exception as exc:  # noqa: BLE001
                    _log(f"skip {dataset}/{c.case_id}: {exc}")
        transfer.flush()
        _write_csv(
            run_dir / "transfer_summary.csv",
            count_table(transfer.rows, ["dataset", "kind", "arm", "layer", "alpha"]),
        )
        _log(f"[{time.time() - started:5.0f}s] transfer {dataset} done ({len(dcases)} cases)")

    (run_dir / "manifest.json").write_text(
        json.dumps(
            {
                "job": "thinking_direction",
                "model_id": env["model_id"],
                "n_items": len(items),
                "n_completed": len(completed_ids),
                "loo_layers": layers,
                "alphas": alphas,
                "edit_arms": edit_arms,
                "datasets": datasets,
                "elapsed_seconds": round(time.time() - started, 1),
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    print("\n== loo (all 18, direction from the other items)")
    for r in count_table(loo.rows, ["layer", "kind", "arm", "alpha"]):
        print(
            f"  L{r['layer']:<3} {r['kind']:7s} {r['arm']:10s} a={r['alpha']:<4} "
            f"correct={r['correct']}/{r['n']} fix={r['lure_to_correct']} "
            f"damage={r['correct_to_lure']} gap={r['mean_gap_closure']}"
        )
    print("\n== sanity")
    for r in count_table(sanity.rows, ["kind", "arm", "layer", "alpha"]):
        print(
            f"  {r['arm']:10s} L{r['layer']} a={r['alpha']} correct={r['correct']}/{r['n']} "
            f"damage={r['correct_to_lure']}"
        )
    print("\n== transfer")
    for r in count_table(transfer.rows, ["dataset", "kind", "arm", "layer", "alpha"]):
        print(
            f"  {r['dataset'][:26]:26s} {r['kind']:7s} {r['arm']:10s} L{r['layer']} "
            f"a={r['alpha']} correct={r['correct']}/{r['n']} fix={r['lure_to_correct']} "
            f"damage={r['correct_to_lure']}"
        )
    print(f"ARTIFACT_DIR={run_dir}", flush=True)
    return run_dir


def _generate(runner: Any, ctx: Sequence[int], hooks, max_new_tokens: int) -> str:
    import torch

    handles = [runner.block(layer).register_forward_hook(hook) for layer, hook in hooks]
    try:
        tensor = torch.tensor([list(ctx)], device=runner.device)
        pad = runner.text_tok.pad_token_id
        if pad is None:
            eos = runner.text_tok.eos_token_id
            pad = eos[0] if isinstance(eos, (list, tuple)) else eos
        with torch.inference_mode():
            out = runner.model.generate(
                input_ids=tensor,
                attention_mask=torch.ones_like(tensor),
                max_new_tokens=int(max_new_tokens),
                do_sample=False,
                pad_token_id=int(pad),
            )
    finally:
        for handle in handles:
            handle.remove()
    return runner.text_tok.decode(out[0, len(ctx) :], skip_special_tokens=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output-root", default=Path("outputs/experiments"), type=Path)
    args = parser.parse_args()
    run(args.config, args.output_root)


if __name__ == "__main__":
    main()
