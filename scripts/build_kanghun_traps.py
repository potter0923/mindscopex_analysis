# Copyright 2026 MindScopeX
"""Build ``kanghun_traps_v1``: independent trap types on an emphasis ladder.

Item 2 of the 2026-10-03 plan asks for

    sealed sentences written by a *different* author, and a ladder of sentences
    that vary only the decisive condition's position and prominence, covering
    5-8 independent types, each screened by the model's actual answer rather
    than by a selection score alone.

Three design rules follow from that, and from what the repo already has.

**Independent types, not paraphrases.** Each scenario takes a different trap
structure from ``docs`` axis B (``salient_cue_overrides_requirement``,
``relation_omission_or_reversal``, and so on). Five rewordings of one trap are one
type, not five, and the 36-pair synthetic attempt that yielded two usable pairs is
what happens when that is not enforced.

**The ladder moves the condition, nothing else.** Across ``buried`` →
``backgrounded`` → ``focused`` → ``explicit`` the arithmetic, the correct answer
and the lure are identical; only where the decisive clause sits and how plainly it
is stated changes. ``explicit`` may not introduce a fact the other rungs lack --
the classification guide is explicit that an added sentence must not hand over a
new answer-determining fact. So the ladder isolates *salience* as the variable.

**Both answers must be separable by token.** The lens reads one token at one
position, so a pair whose answers never diverge carries no signal. Every answer
here is short and starts to differ within a few tokens.

Each scenario also carries a ``control_question`` that removes the decisive
condition, which makes the lure the correct answer. That is the matched control:
if an intervention moves the hostile item it must leave this one alone.

Run::

    uv run python scripts/build_kanghun_traps.py

Writing a benchmark against a model you are about to test is how items get tuned
until they "work", so nothing here is screened against Qwen before being written.
``experiments/jobs/screen_traps.py`` does the screening afterwards, on generated
text, and whatever fails stays in the file marked as failing rather than being
quietly rewritten.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DATASET_ID = "kanghun_traps_v1"
CONDITIONS = ("buried", "backgrounded", "focused", "explicit")

# Every scenario: the decisive condition rendered four ways, and the shared
# numbers that both answers come from. ``setup`` runs before the condition in the
# buried rung and after it in the others, so the lure's inputs are always present.
SCENARIOS: list[dict[str, Any]] = [
    {
        "pair_id": "oven_preheat",
        "family": "prerequisite_or_order_omission",
        "domain": "rate_and_work",
        "correct": "90 minutes",
        "lure": "60 minutes",
        "buried": (
            "A baker, using an oven that cools completely between trays and needs ten "
            "minutes of preheating before each one, bakes three trays of rolls, and "
            "each tray bakes for twenty minutes."
        ),
        "backgrounded": (
            "A baker bakes three trays of rolls, and each tray bakes for twenty "
            "minutes, though the oven, which cools completely between trays, needs "
            "ten minutes of preheating before each one."
        ),
        "focused": (
            "A baker bakes three trays of rolls, and each tray bakes for twenty "
            "minutes. The oven cools completely between trays and needs ten minutes "
            "of preheating before each tray."
        ),
        "explicit": (
            "A baker bakes three trays of rolls, and each tray bakes for twenty "
            "minutes. The oven cools completely between trays and needs ten minutes "
            "of preheating before each tray. This preheating happens before every "
            "tray, not only the first."
        ),
        "question": "How many minutes does the whole job take?",
        "control": (
            "A baker bakes three trays of rolls, and each tray bakes for twenty "
            "minutes. The oven stays hot the whole time and needs no preheating. "
            "How many minutes does the whole job take?"
        ),
        "note": "Lure skips the per-tray preheat and reports 3 x 20.",
    },
    {
        "pair_id": "elevator_cart",
        "family": "capacity_or_compatibility_violation",
        "domain": "counting_and_probability",
        "correct": "7 trips",
        "lure": "6 trips",
        "buried": (
            "A porter, whose cart rides along and occupies one crate's worth of space "
            "on every trip, moves forty-six crates with a freight elevator that holds "
            "eight crates."
        ),
        "backgrounded": (
            "A porter moves forty-six crates with a freight elevator that holds eight "
            "crates, while his cart rides along and occupies one crate's worth of "
            "space on every trip."
        ),
        "focused": (
            "A porter moves forty-six crates with a freight elevator that holds eight "
            "crates. His cart rides along and occupies one crate's worth of space on "
            "every trip."
        ),
        "explicit": (
            "A porter moves forty-six crates with a freight elevator that holds eight "
            "crates. His cart rides along and occupies one crate's worth of space on "
            "every trip. The cart is in the elevator on every trip, so no trip carries "
            "eight crates."
        ),
        "question": "How many trips does he make?",
        "control": (
            "A porter moves forty-six crates with a freight elevator that holds eight "
            "crates. He leaves his cart downstairs, so every trip is crates only. "
            "How many trips does he make?"
        ),
        "note": "Lure divides 46 by the posted capacity 8; the cart reduces it to 7.",
    },
    {
        "pair_id": "cardstock_printer",
        "family": "entity_or_role_binding",
        "domain": "rate_and_work",
        "correct": "20 minutes",
        "lure": "12 minutes",
        "buried": (
            "An office, where only the blue printer takes cardstock, has a blue printer "
            "that prints twelve pages a minute and a grey printer that prints twenty, "
            "and a job of two hundred forty pages of cardstock comes in."
        ),
        "backgrounded": (
            "An office has a blue printer that prints twelve pages a minute and a grey "
            "printer that prints twenty, and a job of two hundred forty pages of "
            "cardstock comes in, on a stock that only the blue printer takes."
        ),
        "focused": (
            "An office has a blue printer that prints twelve pages a minute and a grey "
            "printer that prints twenty. A job of two hundred forty pages of cardstock "
            "comes in. Only the blue printer takes cardstock."
        ),
        "explicit": (
            "An office has a blue printer that prints twelve pages a minute and a grey "
            "printer that prints twenty. A job of two hundred forty pages of cardstock "
            "comes in. Only the blue printer takes cardstock, so the grey printer "
            "cannot run this job at all."
        ),
        "question": "How many minutes does the job take?",
        "control": (
            "An office has a blue printer that prints twelve pages a minute and a grey "
            "printer that prints twenty. A job of two hundred forty pages comes in, and "
            "either printer can run it, so the faster one is used. "
            "How many minutes does the job take?"
        ),
        "note": "Lure uses the larger, more salient rate 20 rather than the bound one.",
    },
    {
        "pair_id": "bus_stops",
        "family": "heuristic_or_salience_substitution",
        "domain": "counting_and_probability",
        "correct": "2",
        "lure": "30",
        "buried": (
            "Thirty passengers ride a bus out of the depot; eight get off and five get "
            "on at its first stop, and four get off and seven get on at its second."
        ),
        "backgrounded": (
            "A bus leaves the depot with thirty passengers. At the first stop eight get "
            "off and five get on, and at the second stop, after which it reaches the "
            "end of its route, four get off and seven get on."
        ),
        "focused": (
            "A bus leaves the depot with thirty passengers. At the first stop eight get "
            "off and five get on. At the second stop four get off and seven get on."
        ),
        "explicit": (
            "A bus leaves the depot with thirty passengers. At the first stop eight get "
            "off and five get on. At the second stop four get off and seven get on. "
            "Count stops, not passengers."
        ),
        "question": "How many stops did the bus make?",
        "control": (
            "A bus leaves the depot with thirty passengers. At the first stop eight get "
            "off and five get on. At the second stop four get off and seven get on. "
            "How many passengers are on the bus at the end?"
        ),
        "note": (
            "Lure reports the opening passenger count 30. The control asks for that "
            "count, which the arithmetic returns to 30, so the lure becomes correct."
        ),
    },
    {
        "pair_id": "clogged_valve",
        "family": "relation_omission_or_reversal",
        "domain": "rate_and_work",
        "correct": "20 minutes",
        "lure": "15 minutes",
        "buried": (
            "A tank, whose second valve has since clogged and now runs at half its "
            "usual rate, was measured while both valves were healthy: thirty minutes "
            "to drain through one valve alone and fifteen minutes with both open."
        ),
        "backgrounded": (
            "A tank drains in thirty minutes through one valve alone and in fifteen "
            "minutes with both valves open, although the second valve is clogged and "
            "now runs at half its usual rate."
        ),
        "focused": (
            "A tank drains in thirty minutes through one valve alone and in fifteen "
            "minutes with both valves open. The second valve is clogged and now runs at "
            "half its usual rate."
        ),
        "explicit": (
            "A tank drains in thirty minutes through one valve alone and in fifteen "
            "minutes with both valves open. The second valve is clogged and now runs at "
            "half its usual rate. The fifteen-minute figure is for two healthy valves, "
            "not for the tank's present state."
        ),
        "question": "How many minutes does the tank take to drain now?",
        "control": (
            "A tank drains in thirty minutes through one valve alone and in fifteen "
            "minutes with both valves open. Both valves are clear. "
            "How many minutes does the tank take to drain?"
        ),
        "note": "Lure quotes the stated two-valve time and ignores the halved rate.",
    },
    {
        "pair_id": "batball_plain",
        "family": "familiar_pattern_retrieval",
        "domain": "quantity_difference",
        "correct": "$0.10",
        "lure": "$0.05",
        "buried": (
            "A bat, priced at one dollar, is bought together with a ball, and the two "
            "come to one dollar ten."
        ),
        "backgrounded": (
            "A bat and a ball come to one dollar ten together, the bat having been "
            "priced at one dollar."
        ),
        "focused": (
            "A bat and a ball come to one dollar ten together. The bat costs one "
            "dollar."
        ),
        "explicit": (
            "A bat and a ball come to one dollar ten together. The bat costs one "
            "dollar. That is the bat's price, not the amount by which it exceeds the "
            "ball's."
        ),
        "question": "How much does the ball cost?",
        "control": (
            "A bat and a ball come to one dollar ten together. The bat costs one dollar "
            "more than the ball. How much does the ball cost?"
        ),
        "note": (
            "The famous item says 'one dollar more than'; this one does not. The lure "
            "is the memorised $0.05. The control restores the original wording, which "
            "makes $0.05 correct."
        ),
    },
]


def _prompt(text: str) -> str:
    return text.strip() + "\nAnswer:"


def build_cases() -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for scenario in SCENARIOS:
        for condition in CONDITIONS:
            body = f"{scenario[condition]} {scenario['question']}"
            cases.append(
                {
                    "case_id": f"{DATASET_ID}_{scenario['pair_id']}_{condition}",
                    "pair_id": scenario["pair_id"],
                    "template_id": condition,
                    "condition": condition,
                    "family": scenario["family"],
                    "domain": scenario["domain"],
                    "question": body,
                    "correct_answer": scenario["correct"],
                    "lure_answer": scenario["lure"],
                    "control_question": scenario["control"],
                    "note": scenario["note"],
                }
            )
    return cases


def check(cases: list[dict[str, Any]]) -> None:
    """Invariants that make the ladder a ladder. Build fails rather than ships."""
    seen = set()
    for case in cases:
        if case["case_id"] in seen:
            raise ValueError(f"duplicate case_id {case['case_id']}")
        seen.add(case["case_id"])
        if case["correct_answer"] == case["lure_answer"]:
            raise ValueError(f"{case['case_id']}: answers are identical")

    by_pair: dict[str, list[dict[str, Any]]] = {}
    for case in cases:
        by_pair.setdefault(case["pair_id"], []).append(case)
    for pair_id, rungs in by_pair.items():
        if {c["condition"] for c in rungs} != set(CONDITIONS):
            raise ValueError(f"{pair_id}: ladder is missing a rung")
        # Only salience may vary: the answers must be the same on every rung.
        if len({(c["correct_answer"], c["lure_answer"]) for c in rungs}) != 1:
            raise ValueError(f"{pair_id}: a rung changes the answer, so it is not a ladder")
        if len({c["question"] for c in rungs}) != len(rungs):
            raise ValueError(f"{pair_id}: two rungs have identical text")

    families = {c["family"] for c in cases}
    if not 5 <= len(families) <= 8:
        raise ValueError(f"item 2 asks for 5-8 independent types; got {len(families)}")


def build_payload() -> dict[str, Any]:
    cases = build_cases()
    check(cases)
    family_counts: dict[str, int] = {}
    for case in cases:
        family_counts[case["family"]] = family_counts.get(case["family"], 0) + 1
    return {
        "dataset_id": DATASET_ID,
        "schema_version": 2,
        "title": "MindScopeX Independent Traps v1 (emphasis ladder)",
        "description": (
            "Six independent trap structures, each written as a four-rung ladder "
            "(buried, backgrounded, focused, explicit) that moves only the position "
            "and prominence of the decisive condition. Arithmetic, correct answer and "
            "lure are identical across the rungs of a scenario, so salience is the "
            "only variable. Every scenario carries a matched control in which the "
            "decisive condition is removed and the lure becomes correct. Items were "
            "written before any model saw them and are screened separately on "
            "generated answers; failures are recorded, not rewritten."
        ),
        "task_kind": "reasoning_lure",
        "scoring": "logprob_margin",
        "source": {
            "authors": "Lee Kanghun (MindScopeX)",
            "year": 2026,
            "title": "Independent traps on an emphasis ladder",
            "venue": "Repository-authored set, not previously published",
            "doi": "",
            "project_url": "",
        },
        "generated_by": "scripts/build_kanghun_traps.py",
        "n_cases": len(cases),
        "family_counts": dict(sorted(family_counts.items())),
        "cases": cases,
    }


def main() -> None:
    payload = build_payload()
    out = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "mindscopex_analysis"
        / "data"
        / f"{DATASET_ID}.json"
    )
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{out}  n={payload['n_cases']}  types={len(payload['family_counts'])}")
    for family, count in payload["family_counts"].items():
        print(f"  {family:40s} {count}")


if __name__ == "__main__":
    main()
