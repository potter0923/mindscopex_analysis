# Copyright 2026 MindScopeX
"""Build ``kanghun_lure27b_v1``: the items 27B reliably falls for, for mechanism work.

Selection rule, applied to the 27B screens in ``runs_shared/`` (2026-10-24/25):

* thinking off  -> the lure, on every seed;
* thinking on   -> the correct answer, on every seed (seeds 42, 43, 44);
* matched control (decisive change undone, lure correct) -> correct, every seed.

Only sets screened on three seeds and authored for this project are eligible
(v2, v3, v4). Left out on purpose: bat-and-ball (a prototype in 동준's set),
the external ChatGPT set (one seed, different author) and hagendorff (one seed,
public). Items are copied verbatim from their source datasets, never edited.

``family`` is coarsened to ``memo_override`` vs ``non_memo`` so the research
pipeline's family-stratified, hash-based split puts some non-memo items in the
held-out half; the original family is kept in ``note``.

Caveat carried into every downstream claim: the thinking-off answer is a forced
choice and is identical across seeds, so the seed check only shows that the
*thinking-on* recovery is stable. Robustness of the lure itself needs rewordings.

Run::

    uv run python scripts/build_kanghun_lure27b.py
"""

from __future__ import annotations

import json
from pathlib import Path

DATASET_ID = "kanghun_lure27b_v1"
DATA = Path(__file__).resolve().parents[1] / "src" / "mindscopex_analysis" / "data"

SELECTED = {
    "kanghun_traps_v2": ["rome_tomorrow", "curiosity_dog", "early_bird_spoon"],
    "kanghun_traps_v3": [
        "eggs_drawer", "penny_lost", "feather_south", "book_weight", "glitters_glass",
        "smoke_dinner", "necessity_chaos", "time_lunch", "apple_busy", "twinkle_moon",
        "humpty_chair", "jill_stairs", "columbus_australia",
    ],
    "kanghun_traps_v4": ["before_tomorrow", "spell_backwards"],
}


def main() -> None:
    cases = []
    for source, pair_ids in SELECTED.items():
        rows = {
            row["pair_id"]: row
            for row in json.loads((DATA / f"{source}.json").read_text(encoding="utf-8"))["cases"]
        }
        for pair_id in pair_ids:
            row = dict(rows[pair_id])
            original = row["family"]
            row["family"] = "memo_override" if original == "memo_override" else "non_memo"
            row["case_id"] = f"{DATASET_ID}_{pair_id}"
            row["note"] = f"[{source}:{original}] {row['note']}"
            cases.append(row)
    counts: dict[str, int] = {}
    for case in cases:
        counts[case["family"]] = counts.get(case["family"], 0) + 1
    payload = {
        "dataset_id": DATASET_ID,
        "schema_version": 2,
        "title": "27B lure set v1 (screened, for mechanism work)",
        "description": (
            "Trap/control pairs that Qwen3.5-27B answered with the lure when thinking "
            "was off and correctly when it was on, on all three seeds, with the matched "
            "control answered correctly. Copied verbatim from kanghun_traps_v2/v3/v4."
        ),
        "task_kind": "reasoning_lure",
        "scoring": "logprob_margin",
        "source": {
            "authors": "Lee Kanghun (MindScopeX), LLM-assisted",
            "year": 2026,
            "title": "27B lure set v1",
            "venue": "Repository-authored set, screened on Qwen3.5-27B",
            "doi": "",
            "project_url": "",
        },
        "generated_by": "scripts/build_kanghun_lure27b.py",
        "n_cases": len(cases),
        "family_counts": dict(sorted(counts.items())),
        "cases": cases,
    }
    path = DATA / f"{DATASET_ID}.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{path}  n={len(cases)}  {counts}")


if __name__ == "__main__":
    main()
