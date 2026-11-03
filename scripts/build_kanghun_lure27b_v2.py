# Copyright 2026 MindScopeX
"""Build ``kanghun_lure27b_v2`` from the v5 screen: the new-family items 27B falls for.

Same selection rule as ``kanghun_lure27b_v1``, applied to every seed present in the
screen's ``responses.json``:

* thinking off  -> the lure;
* thinking on   -> the correct answer;
* matched control (twist undone, lure correct) -> correct, thinking off and on.

The original ``family`` is kept (no coarsening): the follow-up asks whether each
family has its own thinking direction, so leave-one-out runs within family.

It also writes the thinking-on traces of the selected items in the format
``thinking_direction`` reads (``case_id``, ``thinking``, ``raw_text``), so the
direction can be built without a second generation pass. Those traces were sampled
under the screen's protocol (system prompt, 2048-token budget); a trace that hit
the budget is kept but flagged ``thinking_completed = false`` and is not used to
build a direction.

Also prints and saves a per-family table of the screen (lure rate off/on, passes),
which is the typology result on its own.

Run::

    python scripts/build_kanghun_lure27b_v2.py \\
        --screen runs_shared/05_kanghun_traps_v5_27b/responses.json
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
SOURCE_ID = "kanghun_traps_v5"
DATASET_ID = "kanghun_lure27b_v2"


def _truthy(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def _rows(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, list) else payload.get("responses", [])


def labels_by_pair(rows: list[dict[str, Any]], source_id: str) -> dict[str, dict[tuple, str]]:
    """``pair_id -> {(kind, thinking, seed): label}`` from screen rows."""

    prefix = f"{source_id}_"
    out: dict[str, dict[tuple, str]] = defaultdict(dict)
    for row in rows:
        cid = str(row["case_id"])
        if not cid.startswith(prefix):
            continue
        kind = "control" if cid.endswith("__control") else "trap"
        pair = cid[len(prefix) :].removesuffix("__control")
        thinking = str(row.get("mode", "")) == "thinking"
        out[pair][(kind, thinking, str(row.get("seed", "")))] = str(row.get("answer_label", ""))
    return out


def passes(labels: dict[tuple, str]) -> bool:
    """Lure with thinking off, correct with it on, control correct both ways, every seed."""

    seeds = {seed for (_k, _t, seed) in labels}
    if not seeds:
        return False
    for seed in seeds:
        need = {
            ("trap", False, seed): "lure",
            ("trap", True, seed): "correct",
            ("control", False, seed): "correct",
            ("control", True, seed): "correct",
        }
        for key, want in need.items():
            if labels.get(key) != want:
                return False
    return True


def family_table(
    cases: list[dict[str, Any]], labels: dict[str, dict[tuple, str]]
) -> list[dict[str, Any]]:
    by_family: dict[str, list[str]] = defaultdict(list)
    for case in cases:
        by_family[case["family"]].append(case["pair_id"])
    table = []
    for family in sorted(by_family):
        pairs = by_family[family]
        off = on = n = 0
        for pair in pairs:
            for (kind, thinking, _seed), label in labels.get(pair, {}).items():
                if kind != "trap":
                    continue
                if thinking:
                    on += label == "lure"
                else:
                    off += label == "lure"
                    n += 1
        table.append(
            {
                "family": family,
                "pairs": len(pairs),
                "trap_lure_rate_off": round(off / n, 3) if n else "",
                "trap_lure_rate_on": round(on / n, 3) if n else "",
                "pass": sum(1 for pair in pairs if passes(labels.get(pair, {}))),
            }
        )
    return table


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--screen", type=Path, default=ROOT / "runs_shared/05_kanghun_traps_v5_27b/responses.json"
    )
    parser.add_argument("--source", default=SOURCE_ID, help="screened dataset id")
    parser.add_argument("--out-dir", type=Path, default=DATA, help="where the dataset goes")
    args = parser.parse_args()
    source_id = args.source

    source = json.loads((DATA / f"{source_id}.json").read_text(encoding="utf-8"))
    rows = _rows(args.screen)
    labels = labels_by_pair(rows, source_id)

    table = family_table(source["cases"], labels)
    table_path = args.screen.parent / "family_screen.csv"
    with table_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(table[0]))
        writer.writeheader()
        writer.writerows(table)
    print(f"{'family':22s} pairs  lure_off  lure_on  pass")
    for row in table:
        print(
            f"{row['family']:22s} {row['pairs']:>5}  {row['trap_lure_rate_off']!s:>8}  "
            f"{row['trap_lure_rate_on']!s:>7}  {row['pass']:>4}"
        )

    selected = [c for c in source["cases"] if passes(labels.get(c["pair_id"], {}))]
    cases = []
    for row in selected:
        case = dict(row)
        case["case_id"] = f"{DATASET_ID}_{row['pair_id']}"
        case["note"] = f"[{source_id}:{row['family']}] {row['note']}"
        cases.append(case)
    counts: dict[str, int] = defaultdict(int)
    for case in cases:
        counts[case["family"]] += 1
    payload = {
        "dataset_id": DATASET_ID,
        "schema_version": 2,
        "title": "27B lure set v2 (new families, screened)",
        "description": (
            "kanghun_traps_v5 pairs that Qwen3.5-27B answered with the lure when thinking was "
            "off and correctly when it was on, with the matched control correct both ways, on "
            "every screened seed. Copied verbatim; family kept."
        ),
        "task_kind": "reasoning_lure",
        "scoring": "logprob_margin",
        "source": {
            "authors": "Lee Kanghun (MindScopeX), LLM-assisted",
            "year": 2026,
            "title": "27B lure set v2",
            "venue": "Repository-authored set, screened on Qwen3.5-27B",
            "doi": "",
            "project_url": "",
        },
        "generated_by": "scripts/build_kanghun_lure27b_v2.py",
        "n_cases": len(cases),
        "family_counts": dict(sorted(counts.items())),
        "cases": cases,
    }
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / f"{DATASET_ID}.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"\n{DATASET_ID}: {len(cases)} items {dict(counts)}")

    # Thinking-on traces for the selected items, first seed that has one.
    wanted = {c["pair_id"] for c in selected}
    prefix = f"{source_id}_"
    traces: dict[str, dict[str, Any]] = {}
    for row in sorted(rows, key=lambda r: str(r.get("seed", ""))):
        cid = str(row["case_id"])
        if not cid.startswith(prefix) or cid.endswith("__control"):
            continue
        pair = cid[len(prefix) :]
        if pair not in wanted or str(row.get("mode")) != "thinking" or pair in traces:
            continue
        traces[pair] = {
            "case_id": f"{DATASET_ID}_{pair}",
            "family": row.get("family", ""),
            "thinking": True,
            "raw_text": row.get("raw_text", ""),
            "answer_label": row.get("answer_label", ""),
            "thinking_completed": _truthy(row.get("thinking_completed", True)),
            "seed": row.get("seed", ""),
        }
    traces_path = args.screen.parent / "lure27b_v2_traces.json"
    traces_path.write_text(
        json.dumps(list(traces.values()), indent=2, ensure_ascii=False), encoding="utf-8"
    )
    done = sum(1 for t in traces.values() if t["thinking_completed"])
    print(f"traces: {len(traces)} ({done} finished thinking) -> {traces_path}")


if __name__ == "__main__":
    main()
