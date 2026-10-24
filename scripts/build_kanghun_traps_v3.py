# Copyright 2026 MindScopeX
"""Build ``kanghun_traps_v3``: scale the families that fired on 27B, probe new ones.

The 27B screens of v1 and v2 (runs_shared/01_*, 02_*) found that 27B resists
arithmetic traps, trivialized classics and in-prompt redefinitions, and falls for
traps that make it emit a memorised string: instructed endings for sayings (4/6)
and a famous answer under an altered condition (bat-and-ball, 2/4 rungs). Every hit
was repaired with thinking on and every control was answered correctly.

v3 does two things at once:

**Exploit** the families that fired, with enough items to estimate a rate.

``memo_override``         24  instructed final word for a well-known saying
``familiar_riddle_swap``   8  a famous riddle with one word or number changed

**Explore** families not yet tried on 27B, six to eight each, as a pilot.

``negation_neglect``       8  "which is NOT ..." -- the unnegated association wins
                              (Inverse Scaling Prize, NeQA)
``surface_number_compare`` 8  digit length or magnitude cues beat the value
``pattern_break``          8  an instruction to break a repeating sequence
                              (Inverse Scaling Prize, Pattern Match Suppression)
``false_premise``          6  a question built on a false premise

Two of these overlap 동준's taxonomy in *type* (``familiar_riddle_swap`` is his
``familiar_pattern_retrieval``; ``false_premise`` is ``false_premise_acceptance``).
They are kept small and serve as a comparison; no item reuses his prototypes.

As before: every trap has a matched control in which the lure is correct; recipes
are borrowed, items are newly written; only public-domain sayings are used; the
JSON is committed before any screening and failures are not rewritten.

Run::

    uv run python scripts/build_kanghun_traps_v3.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DATASET_ID = "kanghun_traps_v3"

# Sayings and nursery rhymes, all public domain: (pair_id, stem, memorised, instructed)
MEMO: list[tuple[str, str, str, str]] = [
    ("actions_music", "Actions speak louder than", "words", "music"),
    ("eggs_drawer", "Don't put all your eggs in one", "basket", "drawer"),
    ("pen_brush", "The pen is mightier than the", "sword", "brush"),
    ("romans_sing", "When in Rome, do as the Romans", "do", "sing"),
    ("penny_lost", "A penny saved is a penny", "earned", "lost"),
    ("feather_south", "Birds of a feather flock", "together", "south"),
    ("book_weight", "You can't judge a book by its", "cover", "weight"),
    ("glitters_glass", "All that glitters is not", "gold", "glass"),
    ("late_sorry", "Better late than", "never", "sorry"),
    ("practice_noise", "Practice makes", "perfect", "noise"),
    ("smoke_dinner", "Where there's smoke, there's", "fire", "dinner"),
    ("necessity_chaos", "Necessity is the mother of", "invention", "chaos"),
    ("laughter_exercise", "Laughter is the best", "medicine", "exercise"),
    ("look_sleep", "Look before you", "leap", "sleep"),
    ("sight_town", "Out of sight, out of", "mind", "town"),
    ("time_lunch", "Time flies when you're having", "fun", "lunch"),
    ("apple_busy", "An apple a day keeps the doctor", "away", "busy"),
    ("iron_cheap", "Strike while the iron is", "hot", "cheap"),
    ("dog_bone", "Every dog has its", "day", "bone"),
    ("twinkle_moon", "Twinkle, twinkle, little", "star", "moon"),
    ("humpty_chair", "Humpty Dumpty sat on a", "wall", "chair"),
    ("jill_stairs", "Jack and Jill went up the", "hill", "stairs"),
    ("mary_goat", "Mary had a little", "lamb", "goat"),
    ("macdonald_boat", "Old MacDonald had a", "farm", "boat"),
]

# (pair_id, family, trap question, correct, lure, control question, note)
OTHER: list[tuple[str, str, str, str, str, str, str]] = [
    # ------------------------------------------------------- familiar riddle swaps
    (
        "feathers_two_pounds", "familiar_riddle_swap",
        "Which weighs more: a pound of feathers or two pounds of bricks?",
        "the bricks", "they are equal",
        "Which weighs more: a pound of feathers or a pound of bricks?",
        "Famous answer 'equal' only holds when both are one pound.",
    ),
    (
        "sally_three_sisters", "familiar_riddle_swap",
        "Sally is a girl. She has 3 brothers, and each of her brothers has 3 sisters. "
        "How many sisters does Sally have?",
        "2", "1",
        "Sally is a girl. She has 3 brothers, and each of her brothers has 2 sisters. "
        "How many sisters does Sally have?",
        "Each brother's sisters include Sally, so Sally has (sisters - 1).",
    ),
    (
        "sheep_nine_die", "familiar_riddle_swap",
        "A farmer has 17 sheep, and 9 of them die. How many sheep are left?",
        "8", "9",
        "A farmer has 17 sheep, and all but 9 of them die. How many sheep are left?",
        "Memorised 'all but 9' answer is 9; here 9 die, leaving 8.",
    ),
    (
        "daughters_lucy", "familiar_riddle_swap",
        "Lucy's father has five daughters. Four of them are named Nana, Nene, Nini and "
        "Nono. What is the fifth daughter's name?",
        "Lucy", "Nunu",
        "A father has five daughters. Four of them are named Nana, Nene, Nini and Nono, "
        "and the fifth name follows the same vowel pattern. What is the fifth "
        "daughter's name?",
        "The vowel pattern suggests Nunu, but the question names Lucy as a daughter.",
    ),
    (
        "pills_four", "familiar_riddle_swap",
        "A doctor gives you 4 pills and tells you to take one every half hour, starting "
        "now. How long will the pills last?",
        "1.5 hours", "1 hour",
        "A doctor gives you 3 pills and tells you to take one every half hour, starting "
        "now. How long will the pills last?",
        "n pills last (n-1) half hours. The famous 3-pill answer is 1 hour.",
    ),
    (
        "clock_ten_seconds", "familiar_riddle_swap",
        "A clock takes 10 seconds to strike 6 o'clock, with equal gaps between strikes. "
        "How long does it take to strike 12 o'clock?",
        "22 seconds", "11 seconds",
        "A clock takes 5 seconds to strike 6 o'clock, with equal gaps between strikes. "
        "How long does it take to strike 12 o'clock?",
        "6 strikes have 5 gaps; 12 strikes have 11 gaps. Famous 5-second version gives 11.",
    ),
    (
        "egg_white", "familiar_riddle_swap",
        "Which is correct: 'the white of the egg is white' or 'the white of the egg are "
        "white'?",
        "is white", "neither",
        "Which is correct: 'the yolk of the egg is white' or 'the yolk of the egg are "
        "white'?",
        "Famous trick answer 'neither' (yolks are yellow) does not apply to the white.",
    ),
    (
        "dirt_box", "familiar_riddle_swap",
        "A box measures 3 feet by 3 feet by 3 feet and is completely filled with dirt. "
        "How much dirt is in the box?",
        "27 cubic feet", "none",
        "A hole measures 3 feet by 3 feet by 3 feet. How much dirt is in the hole?",
        "Famous answer 'none' is for an empty hole; this box is full.",
    ),
    # ----------------------------------------------------------- negation neglect
    (
        "not_mammal", "negation_neglect",
        "Which of these is NOT a mammal: a whale or a shark?",
        "a shark", "a whale",
        "Which of these is a mammal: a whale or a shark?",
        "Unnegated association picks the whale.",
    ),
    (
        "not_fruit", "negation_neglect",
        "Which of these is NOT a fruit: a tomato or a carrot?",
        "a carrot", "a tomato",
        "Which of these is a fruit: a tomato or a carrot?",
        "Tomato-is-a-fruit association.",
    ),
    (
        "not_gas_giant", "negation_neglect",
        "Which planet is NOT a gas giant: Jupiter or Mars?",
        "Mars", "Jupiter",
        "Which planet is a gas giant: Jupiter or Mars?",
        "Gas giant association picks Jupiter.",
    ),
    (
        "not_magnetic", "negation_neglect",
        "Which metal is NOT attracted to a magnet: iron or copper?",
        "copper", "iron",
        "Which metal is attracted to a magnet: iron or copper?",
        "Magnet association picks iron.",
    ),
    (
        "not_prime", "negation_neglect",
        "Which of these numbers is NOT prime: 7 or 9?",
        "9", "7",
        "Which of these numbers is prime: 7 or 9?",
        "Prime association picks 7.",
    ),
    (
        "not_south_america", "negation_neglect",
        "Which country is NOT in South America: Peru or Spain?",
        "Spain", "Peru",
        "Which country is in South America: Peru or Spain?",
        "Continent association picks Peru.",
    ),
    (
        "not_egg_layer", "negation_neglect",
        "Which animal does NOT lay eggs: a chicken or a cow?",
        "a cow", "a chicken",
        "Which animal lays eggs: a chicken or a cow?",
        "Egg association picks the chicken.",
    ),
    (
        "not_primary_paint", "negation_neglect",
        "In traditional painting, which color is NOT a primary color: red or green?",
        "green", "red",
        "In traditional painting, which color is a primary color: red or green?",
        "Traditional painter's primaries are red, yellow and blue.",
    ),
    # ----------------------------------------------------- surface number compare
    (
        "decimal_3_8", "surface_number_compare",
        "Which number is larger: 3.12 or 3.8?",
        "3.8", "3.12",
        "Which number is larger: 3.12 or 3.08?",
        "More digits after the point looks larger.",
    ),
    (
        "decimal_7_6", "surface_number_compare",
        "Which number is larger: 7.45 or 7.6?",
        "7.6", "7.45",
        "Which number is larger: 7.45 or 7.06?",
        "More digits after the point looks larger.",
    ),
    (
        "decimal_5_5", "surface_number_compare",
        "Which number is larger: 5.15 or 5.5?",
        "5.5", "5.15",
        "Which number is larger: 5.15 or 5.05?",
        "More digits after the point looks larger.",
    ),
    (
        "smaller_quarter", "surface_number_compare",
        "Which number is smaller: 0.5 or 0.25?",
        "0.25", "0.5",
        "Which number is smaller: 0.5 or 0.75?",
        "25 looks bigger than 5.",
    ),
    (
        "fraction_third", "surface_number_compare",
        "Which fraction is larger: 1/3 or 1/4?",
        "1/3", "1/4",
        "Which fraction is larger: 1/4 or 1/5?",
        "Larger denominator looks larger.",
    ),
    (
        "negative_three", "surface_number_compare",
        "Which number is larger: -3 or -7?",
        "-3", "-7",
        "Which number is larger: -7 or -9?",
        "7 looks bigger than 3.",
    ),
    (
        "km_vs_m", "surface_number_compare",
        "Which distance is longer: 0.3 km or 250 m?",
        "0.3 km", "250 m",
        "Which distance is longer: 0.2 km or 250 m?",
        "250 looks bigger than 0.3.",
    ),
    (
        "kg_vs_g", "surface_number_compare",
        "Which is heavier: 1.5 kg or 1200 g?",
        "1.5 kg", "1200 g",
        "Which is heavier: 1.1 kg or 1200 g?",
        "1200 looks bigger than 1.5.",
    ),
    # ------------------------------------------------------------- pattern break
    (
        "colors_green", "pattern_break",
        "Continue the sequence red, blue, red, blue, red, but instead of following the "
        "pattern, write the word 'green' as the next item.",
        "green", "blue",
        "Continue the sequence red, blue, red, blue, red with the next item.",
        "Pattern continuation is blue.",
    ),
    (
        "evens_three", "pattern_break",
        "Continue the sequence 2, 4, 6, 8, but instead of following the pattern, write "
        "the number 3 as the next item.",
        "3", "10",
        "Continue the sequence 2, 4, 6, 8 with the next item.",
        "Pattern continuation is 10.",
    ),
    (
        "letters_c", "pattern_break",
        "Continue the sequence A, B, A, B, A, but instead of following the pattern, "
        "write the letter C as the next item.",
        "C", "B",
        "Continue the sequence A, B, A, B, A with the next item.",
        "Pattern continuation is B.",
    ),
    (
        "weekdays_friday", "pattern_break",
        "Continue the sequence Monday, Tuesday, Wednesday, but instead of following the "
        "pattern, write Friday as the next item.",
        "Friday", "Thursday",
        "Continue the sequence Monday, Tuesday, Wednesday with the next item.",
        "Pattern continuation is Thursday.",
    ),
    (
        "fibonacci_ten", "pattern_break",
        "Continue the sequence 1, 1, 2, 3, 5, 8, but instead of following the pattern, "
        "write the number 10 as the next item.",
        "10", "13",
        "Continue the sequence 1, 1, 2, 3, 5, 8 with the next item.",
        "Fibonacci continuation is 13.",
    ),
    (
        "yesno_maybe", "pattern_break",
        "Continue the sequence yes, no, yes, no, yes, but instead of following the "
        "pattern, write the word 'maybe' as the next item.",
        "maybe", "no",
        "Continue the sequence yes, no, yes, no, yes with the next item.",
        "Pattern continuation is no.",
    ),
    (
        "tens_forty_five", "pattern_break",
        "Continue the sequence 10, 20, 30, 40, but instead of following the pattern, "
        "write the number 45 as the next item.",
        "45", "50",
        "Continue the sequence 10, 20, 30, 40 with the next item.",
        "Pattern continuation is 50.",
    ),
    (
        "pets_bird", "pattern_break",
        "Continue the sequence cat, dog, cat, dog, cat, but instead of following the "
        "pattern, write the word 'bird' as the next item.",
        "bird", "dog",
        "Continue the sequence cat, dog, cat, dog, cat with the next item.",
        "Pattern continuation is dog.",
    ),
    # ------------------------------------------------------------- false premise
    (
        "sydney_capital", "false_premise",
        "Which country has Sydney as its capital city?",
        "none", "Australia",
        "Which country has Sydney as its largest city?",
        "Australia's capital is Canberra.",
    ),
    (
        "edison_telephone", "false_premise",
        "In what year did Thomas Edison invent the telephone?",
        "never", "1876",
        "In what year was the telephone first patented?",
        "Bell's telephone patent is 1876; Edison did not invent it.",
    ),
    (
        "armstrong_mars", "false_premise",
        "What did Neil Armstrong say when he first stepped onto Mars?",
        "nothing", "one small step",
        "What phrase did Neil Armstrong say when he first stepped onto the Moon?",
        "No one has walked on Mars.",
    ),
    (
        "columbus_australia", "false_premise",
        "In which year did Christopher Columbus discover Australia?",
        "never", "1492",
        "In which year did Christopher Columbus first reach the Americas?",
        "Columbus never reached Australia.",
    ),
    (
        "curie_literature", "false_premise",
        "What was Marie Curie's Nobel Prize in Literature awarded for?",
        "nothing", "radioactivity",
        "What was Marie Curie's 1903 Nobel Prize in Physics awarded for?",
        "Curie won Physics (1903) and Chemistry (1911), never Literature.",
    ),
    (
        "galileo_probe", "false_premise",
        "On which planet did Galileo land his space probe in 1610?",
        "none", "Jupiter",
        "Which planet's moons did Galileo observe through his telescope in 1610?",
        "Galileo observed Jupiter's moons; he sent no probe.",
    ),
]

FORBIDDEN_PROTOTYPES = ("race", "dead cat", "month", "bat and", "widget", "nickel", "lily")
V2_STEMS = (
    "rome wasn't built", "curiosity killed", "early bird", "silver lining",
    "every cloud", "worth a thousand", "count your chickens",
)


def build_cases() -> list[dict[str, Any]]:
    cases = []
    for pair_id, stem, memorised, instructed in MEMO:
        cases.append(
            {
                "case_id": f"{DATASET_ID}_{pair_id}",
                "pair_id": pair_id,
                "template_id": "memo_override",
                "condition": "trap",
                "family": "memo_override",
                "question": (
                    f"Complete the saying so that its final word is '{instructed}': {stem}"
                ),
                "correct_answer": instructed,
                "lure_answer": memorised,
                "control_question": f"Complete the saying: {stem}",
                "note": f"Memorised ending '{memorised}'.",
            }
        )
    for pair_id, family, question, correct, lure, control, note in OTHER:
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
        correct, lure = case["correct_answer"].casefold(), case["lure_answer"].casefold()
        if correct == lure:
            raise ValueError(f"{cid}: identical answers")
        if correct.startswith(lure) or lure.startswith(correct):
            raise ValueError(f"{cid}: one answer is a prefix of the other")
        if not case["control_question"] or case["control_question"] == case["question"]:
            raise ValueError(f"{cid}: control must exist and differ from the trap")
        text = case["question"].casefold()
        for proto in FORBIDDEN_PROTOTYPES:
            if proto in text:
                raise ValueError(f"{cid}: uses a prototype in 동준's set ({proto})")
        for stem in V2_STEMS:
            if stem in text:
                raise ValueError(f"{cid}: reuses a v2 stem ({stem}); screened items stay put")


def build_payload() -> dict[str, Any]:
    cases = build_cases()
    check(cases)
    counts: dict[str, int] = {}
    for case in cases:
        counts[case["family"]] = counts.get(case["family"], 0) + 1
    return {
        "dataset_id": DATASET_ID,
        "schema_version": 2,
        "title": "MindScopeX Large-Model Traps v3",
        "description": (
            "Trap/control pairs that scale the two families 27B fell for in the v1/v2 "
            "screens (instructed endings for memorised sayings; famous riddles with one "
            "detail changed) and pilot four new families (negation neglect, surface "
            "number comparison, pattern break, false premise). Each control undoes the "
            "decisive change so the lure is correct there. Newly written, public-domain "
            "sayings only, LLM-assisted, committed before any screening."
        ),
        "task_kind": "reasoning_lure",
        "scoring": "logprob_margin",
        "source": {
            "authors": "Lee Kanghun (MindScopeX), LLM-assisted",
            "year": 2026,
            "title": "Large-model traps v3",
            "venue": "Repository-authored set, not previously published",
            "doi": "",
            "project_url": "",
        },
        "generated_by": "scripts/build_kanghun_traps_v3.py",
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
        print(f"  {family:24s} {count}")


if __name__ == "__main__":
    main()
