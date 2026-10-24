# Copyright 2026 MindScopeX
"""Build ``kanghun_traps_v2``: traps aimed at what *large* models get wrong.

The v1 drafts were mostly arithmetic traps, and large models rarely fall for
those (27B was near 0% on CRT in August). Two lines of published work point to the
families that go the other way, getting *worse* or staying bad with scale, and
that a short reasoning pass repairs -- which is exactly the "lure with thinking
off, correct with thinking on" contrast this project studies.

``trivialized_classic``
    A famous puzzle altered so its answer becomes trivial. Models reproduce the
    memorised solution of the original ("phantom recall"; PHANTOM RECALL, 2025,
    arXiv:2510.11812; cf. the MisguidedAttention collection).

``redefinition``
    A familiar word or symbol is redefined inside the prompt; the model answers
    with the conventional meaning. The Inverse Scaling Prize's "Redefine" family
    (2022-23), where larger models did worse without chain of thought and close to
    perfectly with it.

``memo_override``
    A well-known saying must end in an instructed word; the model completes the
    memorised phrase instead. The Inverse Scaling Prize's "Memo Trap".

Rules kept from v1, and one dropped:

* every trap has a matched control that undoes the decisive change, so the lure
  is the correct answer there;
* only the recipes are borrowed -- every item is newly written, because published
  items may already be in Qwen3.5's training data;
* the puzzles 동준 already uses (race, dead cat, months, bat-and-ball, widgets,
  nickel) are avoided so the two sets stay disjoint;
* the four-rung salience ladder is dropped: both drafts showed its rungs are not
  reliably ordered, and here the question is only whether 27B falls at all.

Run::

    uv run python scripts/build_kanghun_traps_v2.py

Commit the JSON before screening it. Items that fail on the model stay in the file
and are reported as failing, never rewritten until they pass.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DATASET_ID = "kanghun_traps_v2"

# (pair_id, family, trap question, correct, lure, control question, note)
ITEMS: list[tuple[str, str, str, str, str, str, str]] = [
    # ---------------------------------------------------------- trivialized classics
    (
        "river_big_boat",
        "trivialized_classic",
        "A farmer must take a wolf, a goat and a cabbage across a river. Left alone, "
        "the wolf would eat the goat and the goat would eat the cabbage. The farmer's "
        "boat is large enough to carry him together with all three at once. What is "
        "the smallest number of one-way crossings needed to get everything across?",
        "1",
        "7",
        "A farmer must take a wolf, a goat and a cabbage across a river. Left alone, "
        "the wolf would eat the goat and the goat would eat the cabbage. The farmer's "
        "boat can carry him and at most one of the three. What is the smallest number "
        "of one-way crossings needed to get everything across?",
        "Classic answer 7 assumes one passenger per trip; here everything fits at once.",
    ),
    (
        "jug_already_full",
        "trivialized_classic",
        "You need exactly 4 liters of water in a single jug. You have a 4-liter jug "
        "that is already completely full, an empty 3-liter jug and an empty 5-liter "
        "jug. What is the minimum number of operations (filling, emptying, or pouring "
        "between jugs) needed?",
        "0",
        "6",
        "You need exactly 4 liters of water in a single jug. You have an empty "
        "3-liter jug, an empty 5-liter jug and an unlimited tap. What is the minimum "
        "number of operations (filling, emptying, or pouring between jugs) needed?",
        "Classic 3/5 solution: fill5, 5->3, empty3, 5->3, fill5, 5->3 = 6. Here 4 L exists.",
    ),
    (
        "glass_doors",
        "trivialized_classic",
        "On a game show there are three doors made of clear glass, so you can see "
        "the car behind door 1 and goats behind doors 2 and 3. You pick door 1. The "
        "host opens door 3 to show a goat and offers to let you switch to door 2. To "
        "win the car, should you stay or switch?",
        "stay",
        "switch",
        "On a game show there are three closed opaque doors: one hides a car and two "
        "hide goats. You pick door 1. The host, who knows where the car is, opens door "
        "3 to show a goat and offers to let you switch to door 2. To maximize your "
        "chance of winning the car, should you stay or switch?",
        "Memorised Monty Hall answer is switch; with glass doors you already see the car.",
    ),
    (
        "birthday_guarantee",
        "trivialized_classic",
        "Ignoring leap years, how many people must be in a room to guarantee that at "
        "least two of them share a birthday?",
        "366",
        "23",
        "Ignoring leap years, how many people must be in a room for the probability "
        "that at least two of them share a birthday to first exceed 50%?",
        "Pigeonhole gives 366; 23 is the famous 50% figure.",
    ),
    (
        "socks_two_black",
        "trivialized_classic",
        "A drawer holds 10 black socks and 10 white socks, mixed together, and the "
        "room is dark. How many socks must you take out to be certain you have at "
        "least two black socks?",
        "12",
        "3",
        "A drawer holds 10 black socks and 10 white socks, mixed together, and the "
        "room is dark. How many socks must you take out to be certain you have two "
        "socks of the same color?",
        "Worst case is all 10 white first, then 2 black. 3 is the famous any-pair answer.",
    ),
    (
        "two_headed_coin",
        "trivialized_classic",
        "A coin that has heads on both sides has just landed heads five times in a "
        "row. What is the probability that the next flip lands heads?",
        "100%",
        "50%",
        "A fair coin has just landed heads five times in a row. What is the "
        "probability that the next flip lands heads?",
        "Independence answer 50% only holds for a fair coin.",
    ),
    # ----------------------------------------------------------------- redefinition
    (
        "five_day_week",
        "redefinition",
        "In this puzzle, a week has exactly 5 days. How many days are in 3 weeks?",
        "15",
        "21",
        "How many days are in 3 weeks?",
        "Redefined week. Conventional answer 21.",
    ),
    (
        "dozen_is_ten",
        "redefinition",
        "In this shop, the word 'dozen' means exactly 10 items. How many items are in "
        "3 dozen?",
        "30",
        "36",
        "How many items are in 3 dozen?",
        "Redefined dozen. Conventional answer 36.",
    ),
    (
        "plus_means_minus",
        "redefinition",
        "In this question, the symbol + means subtraction. What is 9 + 4?",
        "5",
        "13",
        "What is 9 + 4?",
        "Redefined operator. Conventional answer 13.",
    ),
    (
        "pi_is_five",
        "redefinition",
        "In this problem, let the symbol pi stand for the number 5. What is 2 times "
        "pi, rounded to the nearest whole number?",
        "10",
        "6",
        "Let pi be the usual mathematical constant. What is 2 times pi, rounded to the "
        "nearest whole number?",
        "Redefined constant. Conventional 2*3.14159 = 6.28 -> 6.",
    ),
    (
        "pair_of_three",
        "redefinition",
        "In this club, a 'pair' always means a group of three people. How many people "
        "are in 4 pairs?",
        "12",
        "8",
        "How many people are in 4 pairs?",
        "Redefined pair. Conventional answer 8.",
    ),
    (
        "thirty_hour_day",
        "redefinition",
        "On this planet, one day lasts exactly 30 hours. How many hours are in 2 days "
        "on this planet?",
        "60",
        "48",
        "On Earth, how many hours are in 2 days?",
        "Redefined day length. Conventional answer 48.",
    ),
    # --------------------------------------------------------------- memo overrides
    (
        "rome_tomorrow",
        "memo_override",
        "Complete the saying so that its final word is 'tomorrow': Rome wasn't built "
        "in a",
        "tomorrow",
        "day",
        "Complete the saying: Rome wasn't built in a",
        "Memorised ending 'day'.",
    ),
    (
        "curiosity_dog",
        "memo_override",
        "Complete the saying so that its final word is 'dog': Curiosity killed the",
        "dog",
        "cat",
        "Complete the saying: Curiosity killed the",
        "Memorised ending 'cat'.",
    ),
    (
        "early_bird_spoon",
        "memo_override",
        "Complete the saying so that its final word is 'spoon': The early bird "
        "catches the",
        "spoon",
        "worm",
        "Complete the saying: The early bird catches the",
        "Memorised ending 'worm'.",
    ),
    (
        "silver_rain",
        "memo_override",
        "Complete the saying so that its final word is 'rain': Every cloud has a "
        "silver",
        "rain",
        "lining",
        "Complete the saying: Every cloud has a silver",
        "Memorised ending 'lining'.",
    ),
    (
        "thousand_stones",
        "memo_override",
        "Complete the saying so that its final word is 'stones': A picture is worth a "
        "thousand",
        "stones",
        "words",
        "Complete the saying: A picture is worth a thousand",
        "Memorised ending 'words'.",
    ),
    (
        "chickens_fly",
        "memo_override",
        "Complete the saying so that its final word is 'fly': Don't count your "
        "chickens before they",
        "fly",
        "hatch",
        "Complete the saying: Don't count your chickens before they",
        "Memorised ending 'hatch'.",
    ),
]

FORBIDDEN_PROTOTYPES = ("race", "dead cat", "month", "bat and", "widget", "nickel")


def build_cases() -> list[dict[str, Any]]:
    cases = []
    for pair_id, family, question, correct, lure, control, note in ITEMS:
        cases.append(
            {
                "case_id": f"{DATASET_ID}_{pair_id}",
                "pair_id": pair_id,
                "template_id": family,
                "condition": "trap",
                "family": family,
                "question": question,
                "correct_answer": correct,
                "lure_answer": lure,
                "control_question": control,
                "note": note,
            }
        )
    return cases


def check(cases: list[dict[str, Any]]) -> None:
    """Fail the build rather than ship an item that cannot be scored."""
    seen = set()
    for case in cases:
        cid = case["case_id"]
        if cid in seen:
            raise ValueError(f"duplicate case_id {cid}")
        seen.add(cid)
        correct, lure = case["correct_answer"], case["lure_answer"]
        if correct.casefold() == lure.casefold():
            raise ValueError(f"{cid}: identical answers")
        if correct.casefold().startswith(lure.casefold()) or lure.casefold().startswith(
            correct.casefold()
        ):
            raise ValueError(f"{cid}: one answer is a prefix of the other")
        if not case["control_question"] or case["control_question"] == case["question"]:
            raise ValueError(f"{cid}: control must exist and differ from the trap")
        text = case["question"].casefold()
        for proto in FORBIDDEN_PROTOTYPES:
            if proto in text:
                raise ValueError(f"{cid}: uses a prototype already in 동준's set ({proto})")


def build_payload() -> dict[str, Any]:
    cases = build_cases()
    check(cases)
    counts: dict[str, int] = {}
    for case in cases:
        counts[case["family"]] = counts.get(case["family"], 0) + 1
    return {
        "dataset_id": DATASET_ID,
        "schema_version": 2,
        "title": "MindScopeX Large-Model Traps v2",
        "description": (
            "Trap/control pairs in three families chosen because large models are "
            "known to fall for them while a reasoning pass repairs them: famous "
            "puzzles made trivial, in-prompt redefinitions, and instructed endings "
            "for memorised sayings. Recipes follow PHANTOM RECALL (2025) and the "
            "Inverse Scaling Prize (Redefine, Memo Trap); every item is newly "
            "written. Each control undoes the decisive change so the lure is correct "
            "there. Written with LLM assistance and committed before any screening."
        ),
        "task_kind": "reasoning_lure",
        "scoring": "logprob_margin",
        "source": {
            "authors": "Lee Kanghun (MindScopeX), LLM-assisted",
            "year": 2026,
            "title": "Large-model traps v2",
            "venue": "Repository-authored set, not previously published",
            "doi": "",
            "project_url": "",
        },
        "generated_by": "scripts/build_kanghun_traps_v2.py",
        "n_cases": len(cases),
        "family_counts": dict(sorted(counts.items())),
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
    print(f"{out}  n={payload['n_cases']}")
    for family, count in payload["family_counts"].items():
        print(f"  {family:22s} {count}")


if __name__ == "__main__":
    main()
