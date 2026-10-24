# Copyright 2026 MindScopeX
"""Build ``kanghun_traps_v4``: four more trap families, explored before scaling.

Breadth before depth: the typology needs to know *which* families make 27B take the
lure with thinking off, so v4 pilots four families not tried in v1-v3, six pairs
each, and runs right after v3 on the same protocol.

``relative_reference``   a time or position is given relative to a shifted anchor
                         ("three days before *tomorrow*"); the lure reads it from the
                         obvious anchor ("today")
``percent_symmetry``     percentages that look like they cancel or add (+50% then
                         -50%, two 10% discounts, average of two speeds)
``instruction_inversion`` an instruction flips or shifts the natural answer ("reply
                         'odd' if even", "second-largest", "spell it backwards")
``wordplay_referent``    the question asks about a different quantity than the one
                         the arithmetic invites ("how many apples do *you* have")

Every pair keeps the same two answer strings in trap and control, with their roles
swapped: the control removes the twist so the lure is correct there. Newly written,
LLM-assisted, committed before any screening; failures are recorded, not rewritten.

Run::

    uv run python scripts/build_kanghun_traps_v4.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DATASET_ID = "kanghun_traps_v4"

# (pair_id, family, trap question, correct, lure, control question, note)
ITEMS: list[tuple[str, str, str, str, str, str, str]] = [
    # ------------------------------------------------------- relative reference
    (
        "before_tomorrow", "relative_reference",
        "Today is Monday. What day was it three days before tomorrow?",
        "Saturday", "Friday",
        "Today is Monday. What day was it three days before today?",
        "Tomorrow is Tuesday; three days before Tuesday is Saturday.",
    ),
    (
        "after_tomorrow", "relative_reference",
        "If yesterday was Thursday, what day will it be the day after tomorrow?",
        "Sunday", "Saturday",
        "If yesterday was Thursday, what day will it be tomorrow?",
        "Today is Friday, so the day after tomorrow is Sunday.",
    ),
    (
        "before_yesterday_date", "relative_reference",
        "Today is the 10th. What date was it two days before yesterday?",
        "the 7th", "the 8th",
        "Today is the 10th. What date was it two days before today?",
        "Yesterday is the 9th; two days before that is the 7th.",
    ),
    (
        "hour_from_now", "relative_reference",
        "It is 3 PM now. What time was it two hours before the time one hour from now?",
        "2 PM", "1 PM",
        "It is 3 PM now. What time was it two hours before now?",
        "One hour from now is 4 PM; two hours before that is 2 PM.",
    ),
    (
        "month_from_now", "relative_reference",
        "One month from now it will be May. What month was it two months ago?",
        "February", "March",
        "It is May now. What month was it two months ago?",
        "It is April now; two months ago was February.",
    ),
    (
        "queue_behind", "relative_reference",
        "In a line, Lee is 4th from the front. Kim stands directly behind the person "
        "who is directly behind Lee. What is Kim's position from the front?",
        "6th", "5th",
        "In a line, Lee is 4th from the front. Kim stands directly behind Lee. What is "
        "Kim's position from the front?",
        "Behind Lee is 5th; behind that is 6th.",
    ),
    # ---------------------------------------------------------- percent symmetry
    (
        "price_up_down", "percent_symmetry",
        "A shirt's price rises by 50% and then falls by 50%. Compared with the original "
        "price, is it now lower or the same?",
        "lower", "the same",
        "A shirt's price rises by $50 and then falls by $50. Compared with the original "
        "price, is it now lower or the same?",
        "1.5 x 0.5 = 0.75 of the original.",
    ),
    (
        "salary_cut_raise", "percent_symmetry",
        "A salary is cut by 25% and later raised by 25%. Compared with the original "
        "salary, is it now lower or the same?",
        "lower", "the same",
        "A salary is cut by $250 and later raised by $250. Compared with the original "
        "salary, is it now lower or the same?",
        "0.75 x 1.25 = 0.9375 of the original.",
    ),
    (
        "population_grow_shrink", "percent_symmetry",
        "A town's population grows by 10% one year and shrinks by 10% the next. "
        "Compared with the start, is the population now lower or the same?",
        "lower", "the same",
        "A town's population grows by 100 people one year and shrinks by 100 people the "
        "next. Compared with the start, is the population now lower or the same?",
        "1.1 x 0.9 = 0.99 of the start.",
    ),
    (
        "double_discount", "percent_symmetry",
        "A shop takes 10% off an item, then takes another 10% off the reduced price. "
        "What is the total discount from the original price?",
        "19%", "20%",
        "A shop takes 10% of the original price off an item, then another 10% of the "
        "original price off. What is the total discount from the original price?",
        "0.9 x 0.9 = 0.81, so 19% off.",
    ),
    (
        "stock_recover", "percent_symmetry",
        "A stock falls by 50%. By what percentage must it now rise to get back to its "
        "original price?",
        "100%", "50%",
        "A stock falls by 50%. What percentage of its original price must it regain to "
        "get back to that price?",
        "Half must double to recover.",
    ),
    (
        "average_speed", "percent_symmetry",
        "A car drives 60 km at 30 km/h and then another 60 km at 90 km/h. What is its "
        "average speed for the whole trip?",
        "45 km/h", "60 km/h",
        "A car drives for one hour at 30 km/h and then for one hour at 90 km/h. What is "
        "its average speed for the whole trip?",
        "120 km over 2 h + 2/3 h = 45 km/h; equal times give the plain mean 60.",
    ),
    # ----------------------------------------------------- instruction inversion
    (
        "reply_odd_if_even", "instruction_inversion",
        "If the number is even, reply 'odd'; if it is odd, reply 'even'. The number is 4.",
        "odd", "even",
        "Is the number 4 even or odd?",
        "The instruction inverts the label.",
    ),
    (
        "opposite_of_true", "instruction_inversion",
        "Give the opposite of the true answer. Is ice hot or cold?",
        "hot", "cold",
        "Is ice hot or cold?",
        "The instruction inverts the answer.",
    ),
    (
        "no_if_true", "instruction_inversion",
        "Reply 'no' if the statement is true and 'yes' if it is false: Paris is in France.",
        "no", "yes",
        "Reply 'yes' if the statement is true and 'no' if it is false: Paris is in France.",
        "The instruction inverts yes and no.",
    ),
    (
        "second_largest", "instruction_inversion",
        "Name the second-largest of these numbers: 9, 3, 7.",
        "7", "9",
        "Name the largest of these numbers: 9, 3, 7.",
        "The ordinal shifts the answer off the maximum.",
    ),
    (
        "day_before_wednesday", "instruction_inversion",
        "Which day of the week comes just before Wednesday?",
        "Tuesday", "Thursday",
        "Which day of the week comes just after Wednesday?",
        "Forward sequence prior pulls to Thursday.",
    ),
    (
        "spell_backwards", "instruction_inversion",
        "Spell your answer backwards. What is the opposite of 'up'?",
        "nwod", "down",
        "What is the opposite of 'up'?",
        "The answer must be reversed.",
    ),
    # --------------------------------------------------------- wordplay referent
    (
        "apples_you_have", "wordplay_referent",
        "There are 3 apples on a table and you take away 2. How many apples do you have?",
        "2", "1",
        "There are 3 apples on a table and you take away 2. How many apples are left on "
        "the table?",
        "You hold the 2 you took.",
    ),
    (
        "divide_by_half", "wordplay_referent",
        "Divide 30 by one half and add 10. What is the result?",
        "70", "25",
        "Divide 30 in half and add 10. What is the result?",
        "30 / 0.5 = 60, plus 10.",
    ),
    (
        "subtract_ten", "wordplay_referent",
        "How many times can you subtract 10 from 50?",
        "once", "5 times",
        "How many times can you subtract 10 from 50 before reaching zero?",
        "After the first subtraction you are subtracting from 40.",
    ),
    (
        "shepherd_feet", "wordplay_referent",
        "A shepherd has 15 sheep and 5 dogs. How many feet does the shepherd have?",
        "2", "80",
        "A shepherd has 15 sheep and 5 dogs. How many feet do the animals have in total?",
        "The question asks about the shepherd.",
    ),
    (
        "eggs_all_but", "wordplay_referent",
        "A carton holds 12 eggs. All but 4 of them break. How many eggs are unbroken?",
        "4", "8",
        "A carton holds 12 eggs. 4 of them break. How many eggs are unbroken?",
        "'All but 4' means 4 survive.",
    ),
    (
        "candies_given", "wordplay_referent",
        "You have 5 candies and give 3 to a friend. How many candies did you give away?",
        "3", "2",
        "You have 5 candies and give 3 to a friend. How many candies do you have left?",
        "The question asks what was given, not what remains.",
    ),
]

FORBIDDEN = ("race", "dead cat", "28 days", "bat and", "widget", "nickel", "lily")


def build_cases() -> list[dict[str, Any]]:
    return [
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
        for pair_id, family, question, correct, lure, control, note in ITEMS
    ]


def check(cases: list[dict[str, Any]]) -> None:
    seen = set()
    for case in cases:
        cid = case["case_id"]
        if cid in seen:
            raise ValueError(f"duplicate case_id {cid}")
        seen.add(cid)
        correct, lure = case["correct_answer"].casefold(), case["lure_answer"].casefold()
        if correct == lure or correct.startswith(lure) or lure.startswith(correct):
            raise ValueError(f"{cid}: answers identical or one is a prefix of the other")
        if not case["control_question"] or case["control_question"] == case["question"]:
            raise ValueError(f"{cid}: control must exist and differ from the trap")
        for proto in FORBIDDEN:
            if proto in case["question"].casefold():
                raise ValueError(f"{cid}: uses a prototype in 동준's set ({proto})")


def main() -> None:
    cases = build_cases()
    check(cases)
    counts: dict[str, int] = {}
    for case in cases:
        counts[case["family"]] = counts.get(case["family"], 0) + 1
    payload = {
        "dataset_id": DATASET_ID,
        "schema_version": 2,
        "title": "MindScopeX Large-Model Traps v4 (family exploration)",
        "description": (
            "Pilot of four trap families not tried in v1-v3: relative reference, "
            "percent symmetry, instruction inversion and wordplay referent, six "
            "trap/control pairs each. Controls undo the twist so the lure is correct. "
            "Newly written, LLM-assisted, committed before any screening."
        ),
        "task_kind": "reasoning_lure",
        "scoring": "logprob_margin",
        "source": {
            "authors": "Lee Kanghun (MindScopeX), LLM-assisted",
            "year": 2026,
            "title": "Large-model traps v4",
            "venue": "Repository-authored set, not previously published",
            "doi": "",
            "project_url": "",
        },
        "generated_by": "scripts/build_kanghun_traps_v4.py",
        "n_cases": len(cases),
        "family_counts": dict(sorted(counts.items())),
        "cases": cases,
    }
    out = Path(__file__).resolve().parents[1] / "src" / "mindscopex_analysis" / "data"
    path = out / f"{DATASET_ID}.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{path}  n={len(cases)}")
    for family, count in sorted(counts.items()):
        print(f"  {family:22s} {count}")


if __name__ == "__main__":
    main()
