# Copyright 2026 MindScopeX
"""Two-stage screening helpers: cheap thinking-off filter first, thinking-on second.

A full screen runs thinking off *and* on for every trap and control; with ~400 pairs
that is ~800 long thinking generations. Most items already fail on the cheap side
(the model does not take the lure with thinking off, or gets the control wrong), so:

``subset``  after stage 1 (thinking off, traps + controls): write ``<source>s2``, the
            pairs whose trap got the lure and whose control was answered correctly.
            Case ids are kept, so stage-2 rows line up with stage-1 rows.
``select``  after stage 2 (thinking on, traps only): keep the pairs that also come out
            correct with thinking on, write the final dataset, the thinking-on traces
            (for ``thinking_direction``) and a per-template table.

The thinking-on run of the *controls* is skipped on purpose: across v2-v6 a control
answered correctly with thinking off was essentially never wrong with thinking on.
The selection rule is otherwise the one used for kanghun_lure27b_v1-v3.

Run::

    python scripts/two_stage_screen.py subset --source kanghun_traps_v7 \\
        --stage1 runs_shared/07_kanghun_traps_v7_27b_off/responses.json
    python scripts/two_stage_screen.py select --source kanghun_traps_v7 \\
        --stage1 runs_shared/07_kanghun_traps_v7_27b_off/responses.json \\
        --stage2 runs_shared/07b_kanghun_traps_v7_27b_on/responses.json \\
        --dataset-id kanghun_lure27b_memo
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "src" / "mindscopex_analysis" / "data"


def _rows(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, list) else payload.get("responses", [])


def _truthy(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def labels(rows: list[dict[str, Any]], source_id: str) -> dict[tuple[str, str, bool], str]:
    """``(pair_id, kind, thinking) -> label``; first seed wins."""

    prefix = f"{source_id}_"
    out: dict[tuple[str, str, bool], str] = {}
    for row in sorted(rows, key=lambda r: str(r.get("seed", ""))):
        cid = str(row["case_id"])
        if not cid.startswith(prefix):
            continue
        kind = "control" if cid.endswith("__control") else "trap"
        pair = cid[len(prefix) :].removesuffix("__control")
        key = (pair, kind, str(row.get("mode", "")) == "thinking")
        out.setdefault(key, str(row.get("answer_label", "")))
    return out


def stage1_pass(lab: dict[tuple[str, str, bool], str], pair: str) -> bool:
    return (
        lab.get((pair, "trap", False)) == "lure" and lab.get((pair, "control", False)) == "correct"
    )


def final_pass(
    lab1: dict[tuple[str, str, bool], str], lab2: dict[tuple[str, str, bool], str], pair: str
) -> bool:
    return stage1_pass(lab1, pair) and lab2.get((pair, "trap", True)) == "correct"


def template_table(
    cases: list[dict[str, Any]],
    lab1: dict[tuple[str, str, bool], str],
    lab2: dict[tuple[str, str, bool], str] | None,
) -> list[dict[str, Any]]:
    groups: dict[str, list[str]] = defaultdict(list)
    for case in cases:
        groups[case.get("template_id") or case["family"]].append(case["pair_id"])
    table = []
    for template in sorted(groups):
        pairs = groups[template]
        off = [p for p in pairs if (p, "trap", False) in lab1]
        row = {
            "template": template,
            "pairs": len(pairs),
            "off_lure": sum(lab1.get((p, "trap", False)) == "lure" for p in off),
            "off_seen": len(off),
            "stage1_pass": sum(stage1_pass(lab1, p) for p in pairs),
        }
        if lab2 is not None:
            row["on_correct"] = sum(lab2.get((p, "trap", True)) == "correct" for p in pairs)
            row["final_pass"] = sum(final_pass(lab1, lab2, p) for p in pairs)
        table.append(row)
    return table


def _write_table(path: Path, table: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(table[0]))
        writer.writeheader()
        writer.writerows(table)
    for row in table:
        print("  " + "  ".join(f"{k}={v}" for k, v in row.items()))


def cmd_subset(args: argparse.Namespace) -> None:
    source = json.loads((DATA / f"{args.source}.json").read_text(encoding="utf-8"))
    lab1 = labels(_rows(args.stage1), args.source)
    kept = [c for c in source["cases"] if stage1_pass(lab1, c["pair_id"])]
    out_id = f"{args.source}s2"
    payload = {
        **{
            k: v
            for k, v in source.items()
            if k not in {"cases", "n_cases", "dataset_id", "family_counts", "template_counts"}
        },
        "dataset_id": out_id,
        "title": f"{source.get('title', args.source)} -- stage-2 subset",
        "description": (
            f"Pairs of {args.source} whose trap took the lure and whose control was correct "
            "with thinking off (stage 1). Case ids unchanged."
        ),
        "n_cases": len(kept),
        "family_counts": {
            f: sum(1 for c in kept if c["family"] == f) for f in sorted({c["family"] for c in kept})
        },
        "cases": kept,
    }
    (DATA / f"{out_id}.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"{out_id}: {len(kept)} of {len(source['cases'])} pairs pass stage 1")
    _write_table(
        args.stage1.parent / "stage1_templates.csv", template_table(source["cases"], lab1, None)
    )


def cmd_select(args: argparse.Namespace) -> None:
    source = json.loads((DATA / f"{args.source}.json").read_text(encoding="utf-8"))
    lab1 = labels(_rows(args.stage1), args.source)
    rows2 = _rows(args.stage2)
    lab2 = labels(rows2, args.source)
    selected = [c for c in source["cases"] if final_pass(lab1, lab2, c["pair_id"])]
    cases = []
    for row in selected:
        case = dict(row)
        case["case_id"] = f"{args.dataset_id}_{row['pair_id']}"
        case["note"] = f"[{args.source}:{row.get('template_id', '')}] {row['note']}"
        cases.append(case)
    counts: dict[str, int] = defaultdict(int)
    for case in cases:
        counts[case["family"]] += 1
    payload = {
        "dataset_id": args.dataset_id,
        "schema_version": 2,
        "title": f"27B lure set ({args.dataset_id}, two-stage screened)",
        "description": (
            f"Pairs of {args.source} that Qwen3.5-27B answered with the lure when thinking was "
            "off and correctly when it was on, with the matched control correct with thinking "
            "off. Copied verbatim."
        ),
        "task_kind": "reasoning_lure",
        "scoring": "logprob_margin",
        "source": source.get("source", {}),
        "generated_by": "scripts/two_stage_screen.py",
        "n_cases": len(cases),
        "family_counts": dict(sorted(counts.items())),
        "cases": cases,
    }
    (DATA / f"{args.dataset_id}.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"{args.dataset_id}: {len(cases)} of {len(source['cases'])} pairs")
    _write_table(args.stage2.parent / "templates.csv", template_table(source["cases"], lab1, lab2))

    wanted = {c["pair_id"] for c in selected}
    prefix = f"{args.source}_"
    traces: dict[str, dict[str, Any]] = {}
    for row in sorted(rows2, key=lambda r: str(r.get("seed", ""))):
        cid = str(row["case_id"])
        pair = cid[len(prefix) :] if cid.startswith(prefix) else ""
        new_id = f"{args.dataset_id}_{pair}"
        if pair not in wanted or str(row.get("mode")) != "thinking" or new_id in traces:
            continue
        traces[new_id] = {
            "case_id": new_id,
            "family": row.get("family", ""),
            "thinking": True,
            "raw_text": row.get("raw_text", ""),
            "answer_label": row.get("answer_label", ""),
            "thinking_completed": _truthy(row.get("thinking_completed", True)),
            "seed": row.get("seed", ""),
        }
    short = args.dataset_id.removeprefix("kanghun_")
    out = args.stage2.parent / f"{short}_traces.json"
    out.write_text(
        json.dumps(list(traces.values()), indent=2, ensure_ascii=False), encoding="utf-8"
    )
    done = sum(1 for t in traces.values() if t["thinking_completed"])
    print(f"traces: {len(traces)} ({done} finished thinking) -> {out}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    p1 = sub.add_parser("subset")
    p1.add_argument("--source", required=True)
    p1.add_argument("--stage1", type=Path, required=True)
    p1.set_defaults(func=cmd_subset)
    p2 = sub.add_parser("select")
    p2.add_argument("--source", required=True)
    p2.add_argument("--stage1", type=Path, required=True)
    p2.add_argument("--stage2", type=Path, required=True)
    p2.add_argument("--dataset-id", required=True)
    p2.set_defaults(func=cmd_select)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
