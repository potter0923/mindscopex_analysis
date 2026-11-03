# Copyright 2026 MindScopeX
"""Build ``kanghun_traps_v5``: eight trap families not tried in v1-v4.

Run 49 showed that the "thinking direction" (mean ON - OFF residual at the answer
slot) fixes memorised-phrase traps but not goal-affordance traps, so the next
question is which *other* families 27B falls for with thinking off and recovers
from with thinking on -- each one is a candidate for its own direction. v5 pilots
eight families, six trap/control pairs each:

``letter_count``        count a letter in a word whose repeats hide inside tokens
``repeated_word``       a duplicated word in a familiar phrase ("in the the spring")
``sequence_skip``       a familiar sequence with a stated skip, reversal or new rule
``last_letter_concat``  join the *last* letters, where the habit is first letters
``nested_relative``     a time/date anchored two hops away from "now"
``belief_tracking``     false-belief stories where a detail makes the belief true
``distinct_count``      "how many different", where the habit is counting all
``fact_tweak``          a memorised fact with a small arithmetic change appended

Every pair keeps the same two answer strings in trap and control with their roles
swapped: the control removes the twist so the lure is correct there. Newly written,
LLM-assisted, committed before any screening; failures are recorded, not rewritten.

Run::

    python scripts/build_kanghun_traps_v5.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DATASET_ID = "kanghun_traps_v5"

# (pair_id, family, trap question, correct, lure, control question, note)
ITEMS: list[tuple[str, str, str, str, str, str, str]] = [
    # ------------------------------------------------------------ letter count
    (
        "strawberry_r", "letter_count",
        "How many times does the letter 'r' appear in the word 'strawberry'?",
        "3", "2",
        "How many times does the letter 'r' appear in the word 'berry'?",
        "s-t-r-a-w-b-e-r-r-y has three r's; 'berry' has two.",
    ),
    (
        "bookkeeper_e", "letter_count",
        "How many times does the letter 'e' appear in the word 'bookkeeper'?",
        "3", "2",
        "How many times does the letter 'e' appear in the word 'keep'?",
        "b-o-o-k-k-e-e-p-e-r has three e's; 'keep' has two.",
    ),
    (
        "mississippi_s", "letter_count",
        "How many times does the letter 's' appear in the word 'mississippi'?",
        "4", "3",
        "How many times does the letter 's' appear in the word 'stress'?",
        "m-i-s-s-i-s-s-i-p-p-i has four s's; 'stress' has three.",
    ),
    (
        "parallel_l", "letter_count",
        "How many times does the letter 'l' appear in the word 'parallel'?",
        "3", "2",
        "How many times does the letter 'l' appear in the word 'allow'?",
        "p-a-r-a-l-l-e-l has three l's; 'allow' has two.",
    ),
    (
        "occurrence_c", "letter_count",
        "How many times does the letter 'c' appear in the word 'occurrence'?",
        "3", "2",
        "How many times does the letter 'c' appear in the word 'occur'?",
        "o-c-c-u-r-r-e-n-c-e has three c's; 'occur' has two.",
    ),
    (
        "assassin_s", "letter_count",
        "How many times does the letter 's' appear in the word 'assassin'?",
        "4", "3",
        "How many times does the letter 's' appear in the word 'assist'?",
        "a-s-s-a-s-s-i-n has four s's; 'assist' has three.",
    ),
    # ----------------------------------------------------------- repeated word
    (
        "paris_the", "repeated_word",
        "In the phrase 'Paris in the the spring', how many times does the word 'the' appear?",
        "2", "1",
        "In the phrase 'Paris in the spring', how many times does the word 'the' appear?",
        "The trap phrase repeats 'the'.",
    ),
    (
        "blue_moon_a", "repeated_word",
        "In the phrase 'Once in a a blue moon', how many times does the word 'a' appear?",
        "2", "1",
        "In the phrase 'Once in a blue moon', how many times does the word 'a' appear?",
        "The trap phrase repeats 'a'.",
    ),
    (
        "bird_hand_the", "repeated_word",
        "In the sentence 'A bird in the the hand is worth two in the bush', how many times "
        "does the word 'the' appear?",
        "3", "2",
        "In the sentence 'A bird in the hand is worth two in the bush', how many times "
        "does the word 'the' appear?",
        "'the the hand' plus 'the bush' is three; the normal saying has two.",
    ),
    (
        "late_than", "repeated_word",
        "In the phrase 'Better late than than never', how many times does the word 'than' appear?",
        "2", "1",
        "In the phrase 'Better late than never', how many times does the word 'than' appear?",
        "The trap phrase repeats 'than'.",
    ),
    (
        "glitters_is", "repeated_word",
        "In the phrase 'All that glitters is is not gold', how many times does the word "
        "'is' appear?",
        "2", "1",
        "In the phrase 'All that glitters is not gold', how many times does the word 'is' appear?",
        "The trap phrase repeats 'is'.",
    ),
    (
        "cloud_a", "repeated_word",
        "In the phrase 'Every cloud has a a silver lining', how many times does the word "
        "'a' appear?",
        "2", "1",
        "In the phrase 'Every cloud has a silver lining', how many times does the word 'a' appear?",
        "The trap phrase repeats 'a'.",
    ),
    # ----------------------------------------------------------- sequence skip
    (
        "weekdays_skip", "sequence_skip",
        "List the days of the week in order, but leave out Saturday and Sunday. "
        "Which day comes right after Friday in your list?",
        "Monday", "Saturday",
        "List the days of the week in order. Which day comes right after Friday?",
        "With the weekend removed, Friday is followed by Monday.",
    ),
    (
        "months_reverse", "sequence_skip",
        "Say the months of the year backwards, starting from December. "
        "Which month comes right after April in that list?",
        "March", "May",
        "Say the months of the year in normal order, starting from January. "
        "Which month comes right after April in that list?",
        "Backwards, April is followed by March.",
    ),
    (
        "planets_skip_earth", "sequence_skip",
        "List the planets in order from the Sun, but skip Earth. "
        "Which planet comes right after Venus in your list?",
        "Mars", "Earth",
        "List the planets in order from the Sun. Which planet comes right after Venus?",
        "Without Earth, Venus is followed by Mars.",
    ),
    (
        "rainbow_skip_orange", "sequence_skip",
        "List the colors of the rainbow in order starting with red, but skip orange. "
        "Which color comes right after red in your list?",
        "yellow", "orange",
        "List the colors of the rainbow in order starting with red. "
        "Which color comes right after red?",
        "Without orange, red is followed by yellow.",
    ),
    (
        "sum_of_three", "sequence_skip",
        "In this sequence each number is the sum of the previous three numbers: "
        "1, 1, 2, 4, 7, ... What is the next number?",
        "13", "11",
        "In this sequence each number is the sum of the previous two numbers: "
        "2, 1, 3, 4, 7, ... What is the next number?",
        "2 + 4 + 7 = 13; the two-term habit gives 4 + 7 = 11.",
    ),
    (
        "count_skip_three", "sequence_skip",
        "Count up from 10, but skip every number that contains the digit 3. "
        "Which number comes right after 12?",
        "14", "13",
        "Count up from 10. Which number comes right after 12?",
        "13 contains a 3, so 12 is followed by 14.",
    ),
    # ------------------------------------------------------ last letter concat
    (
        "last_big_cat", "last_letter_concat",
        "Take the last letter of each word and join them: 'big cat'. "
        "Answer with the letters only.",
        "gt", "bc",
        "Take the first letter of each word and join them: 'big cat'. "
        "Answer with the letters only.",
        "Last letters g, t; first letters b, c.",
    ),
    (
        "last_red_apple", "last_letter_concat",
        "Take the last letter of each word and join them: 'red apple'. "
        "Answer with the letters only.",
        "de", "ra",
        "Take the first letter of each word and join them: 'red apple'. "
        "Answer with the letters only.",
        "Last letters d, e; first letters r, a.",
    ),
    (
        "last_blue_sky", "last_letter_concat",
        "Take the last letter of each word and join them: 'blue sky'. "
        "Answer with the letters only.",
        "ey", "bs",
        "Take the first letter of each word and join them: 'blue sky'. "
        "Answer with the letters only.",
        "Last letters e, y; first letters b, s.",
    ),
    (
        "last_hot_dog_run", "last_letter_concat",
        "Take the last letter of each word and join them: 'hot dog run'. "
        "Answer with the letters only.",
        "tgn", "hdr",
        "Take the first letter of each word and join them: 'hot dog run'. "
        "Answer with the letters only.",
        "Last letters t, g, n; first letters h, d, r.",
    ),
    (
        "last_green_tree", "last_letter_concat",
        "Take the last letter of each word and join them: 'green tree'. "
        "Answer with the letters only.",
        "ne", "gt",
        "Take the first letter of each word and join them: 'green tree'. "
        "Answer with the letters only.",
        "Last letters n, e; first letters g, t.",
    ),
    (
        "last_fast_moving_car", "last_letter_concat",
        "Take the last letter of each word and join them: 'fast moving car'. "
        "Answer with the letters only.",
        "tgr", "fmc",
        "Take the first letter of each word and join them: 'fast moving car'. "
        "Answer with the letters only.",
        "Last letters t, g, r; first letters f, m, c.",
    ),
    # --------------------------------------------------------- nested relative
    (
        "two_before_after_tomorrow", "nested_relative",
        "Today is Monday. What day is two days before the day after tomorrow?",
        "Monday", "Saturday",
        "Today is Monday. What day was it two days before today?",
        "The day after tomorrow is Wednesday; two days before that is Monday.",
    ),
    (
        "three_after_before_yesterday", "nested_relative",
        "Today is Wednesday. What day is three days after the day before yesterday?",
        "Thursday", "Saturday",
        "Today is Wednesday. What day will it be three days after today?",
        "The day before yesterday is Monday; three days after that is Thursday.",
    ),
    (
        "hours_after_ago", "nested_relative",
        "It is now 3 PM. What time is two hours after the time it was five hours ago?",
        "12 PM", "5 PM",
        "It is now 3 PM. What time will it be two hours from now?",
        "Five hours ago was 10 AM; two hours after that is 12 PM.",
    ),
    (
        "date_before_after_tomorrow", "nested_relative",
        "Today is the 15th. What date is four days before the day after tomorrow?",
        "the 13th", "the 11th",
        "Today is the 15th. What date was it four days before today?",
        "The day after tomorrow is the 17th; four days before that is the 13th.",
    ),
    (
        "year_before_after_next", "nested_relative",
        "This year is 2026. Which year is ten years before the year after next?",
        "2018", "2016",
        "This year is 2026. Which year was ten years before this year?",
        "The year after next is 2028; ten years before that is 2018.",
    ),
    (
        "day_before_before_yesterday", "nested_relative",
        "Today is Friday. What day was one day before the day before yesterday?",
        "Tuesday", "Wednesday",
        "Today is Friday. What day was the day before yesterday?",
        "The day before yesterday is Wednesday; one day before that is Tuesday.",
    ),
    # --------------------------------------------------------- belief tracking
    (
        "ball_watched", "belief_tracking",
        "Sam puts his ball in the red box and goes outside. While Sam watches through the "
        "window, Ana moves the ball to the blue box. Sam comes back in. Where will Sam look "
        "for the ball first?",
        "the blue box", "the red box",
        "Sam puts his ball in the red box and goes outside. While Sam is away and cannot see, "
        "Ana moves the ball to the blue box. Sam comes back in. Where will Sam look for the "
        "ball first?",
        "Sam saw the move, so he knows the ball is in the blue box.",
    ),
    (
        "keys_texted", "belief_tracking",
        "Nora leaves her keys on the desk and goes out. Tom moves the keys to the drawer and "
        "texts Nora: 'I put your keys in the drawer.' Nora reads the message and comes back. "
        "Where will Nora look for her keys first?",
        "the drawer", "the desk",
        "Nora leaves her keys on the desk and goes out. Tom moves the keys to the drawer "
        "without telling Nora. Nora comes back. Where will Nora look for her keys first?",
        "Nora was told about the move.",
    ),
    (
        "coin_present", "belief_tracking",
        "Max hides a coin under the cup. His sister moves the coin under the plate while Max "
        "sits right next to her and watches. Where does Max think the coin is?",
        "the plate", "the cup",
        "Max hides a coin under the cup. His sister moves the coin under the plate while Max "
        "is asleep. Where does Max think the coin is?",
        "Max watched the move.",
    ),
    (
        "milk_phone", "belief_tracking",
        "Emma puts the milk in the fridge and leaves for school. Her dad moves it to the "
        "shelf, then calls Emma and tells her the milk is on the shelf now. When Emma gets "
        "home, where does she expect the milk to be?",
        "the shelf", "the fridge",
        "Emma puts the milk in the fridge and leaves for school. Her dad moves it to the "
        "shelf and does not tell anyone. When Emma gets home, where does she expect the "
        "milk to be?",
        "Emma was told about the move.",
    ),
    (
        "book_moved_back", "belief_tracking",
        "Jun leaves his book on the bed and goes out. His brother moves it to the desk, then "
        "moves it back to the bed before Jun returns. Where is the book when Jun returns?",
        "the bed", "the desk",
        "Jun leaves his book on the bed and goes out. His brother moves it to the desk and "
        "leaves it there. Where is the book when Jun returns?",
        "The book was moved back to the bed.",
    ),
    (
        "toy_told", "belief_tracking",
        "Mia puts her toy in the basket and leaves the room. Leo moves the toy to the box. "
        "When Mia comes back, Leo tells her, 'I moved your toy to the box.' Where will Mia "
        "look for her toy first?",
        "the box", "the basket",
        "Mia puts her toy in the basket and leaves the room. Leo moves the toy to the box. "
        "Mia comes back and nobody tells her anything. Where will Mia look for her toy first?",
        "Leo told Mia about the move.",
    ),
    # ---------------------------------------------------------- distinct count
    (
        "distinct_animals", "distinct_count",
        "How many different animals are in this list: cat, dog, cat, bird, dog?",
        "3", "5",
        "How many animal names are in this list in total: cat, dog, cat, bird, dog?",
        "cat, dog, bird are three different animals; five names in total.",
    ),
    (
        "distinct_colors", "distinct_count",
        "How many different colors are in this list: red, blue, red, red, green, blue?",
        "3", "6",
        "How many color names are in this list in total: red, blue, red, red, green, blue?",
        "red, blue, green are three different colors; six names in total.",
    ),
    (
        "distinct_letters_banana", "distinct_count",
        "How many different letters are in the word 'banana'?",
        "3", "6",
        "How many letters are in the word 'banana'?",
        "b, a, n are three different letters; six letters in total.",
    ),
    (
        "distinct_numbers", "distinct_count",
        "How many different numbers are in this list: 4, 7, 4, 4, 9, 7, 2?",
        "4", "7",
        "How many numbers are in this list in total: 4, 7, 4, 4, 9, 7, 2?",
        "4, 7, 9, 2 are four different numbers; seven in total.",
    ),
    (
        "distinct_fruits", "distinct_count",
        "How many different fruits are in this list: apple, pear, apple, apple?",
        "2", "4",
        "How many fruit names are in this list in total: apple, pear, apple, apple?",
        "apple and pear are two different fruits; four names in total.",
    ),
    (
        "distinct_letters_balloon", "distinct_count",
        "How many different letters are in the word 'balloon'?",
        "5", "7",
        "How many letters are in the word 'balloon'?",
        "b, a, l, o, n are five different letters; seven letters in total.",
    ),
    # -------------------------------------------------------------- fact tweak
    (
        "twelve_squared_minus", "fact_tweak",
        "What is 12 times 12, minus 1?",
        "143", "144",
        "What is 12 times 12?",
        "144 - 1 = 143.",
    ),
    (
        "spider_legs_minus", "fact_tweak",
        "Take the number of legs a spider has and subtract two. What is the result?",
        "6", "8",
        "How many legs does a spider have?",
        "A spider has 8 legs; 8 - 2 = 6.",
    ),
    (
        "ww2_plus_ten", "fact_tweak",
        "Take the year World War II ended and add ten. What year is that?",
        "1955", "1945",
        "In what year did World War II end?",
        "1945 + 10 = 1955.",
    ),
    (
        "hexagon_plus_one", "fact_tweak",
        "Take the number of sides of a hexagon and add one. What is the result?",
        "7", "6",
        "How many sides does a hexagon have?",
        "A hexagon has 6 sides; 6 + 1 = 7.",
    ),
    (
        "freezing_f_minus", "fact_tweak",
        "Take the temperature at which water freezes in degrees Fahrenheit and subtract two. "
        "What is the result?",
        "30", "32",
        "At what temperature in degrees Fahrenheit does water freeze?",
        "32 - 2 = 30.",
    ),
    (
        "hour_minutes_half", "fact_tweak",
        "Take the number of minutes in an hour and divide it by two. What is the result?",
        "30", "60",
        "How many minutes are in an hour?",
        "60 / 2 = 30.",
    ),
]

# Prototypes of an existing set in the repo, kept out so the sets stay independent.
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
            if proto in case["question"].casefold() or proto in case["control_question"].casefold():
                raise ValueError(f"{cid}: uses a prototype from an existing set ({proto})")


def main() -> None:
    cases = build_cases()
    check(cases)
    counts: dict[str, int] = {}
    for case in cases:
        counts[case["family"]] = counts.get(case["family"], 0) + 1
    payload = {
        "dataset_id": DATASET_ID,
        "schema_version": 2,
        "title": "MindScopeX Large-Model Traps v5 (eight new families)",
        "description": (
            "Pilot of eight trap families not tried in v1-v4: letter count, repeated word, "
            "sequence skip, last-letter concatenation, nested relative reference, belief "
            "tracking, distinct count and fact tweak, six trap/control pairs each. Controls "
            "undo the twist so the lure is correct. Newly written, LLM-assisted, committed "
            "before any screening."
        ),
        "task_kind": "reasoning_lure",
        "scoring": "logprob_margin",
        "source": {
            "authors": "Lee Kanghun (MindScopeX), LLM-assisted",
            "year": 2026,
            "title": "Large-model traps v5",
            "venue": "Repository-authored set, not previously published",
            "doi": "",
            "project_url": "",
        },
        "generated_by": "scripts/build_kanghun_traps_v5.py",
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
