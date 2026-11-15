# Copyright 2026 MindScopeX
"""Build ``kanghun_traps_v9``: four new families picked from the literature.

Chosen because each has published evidence that large instruction-tuned models
fall for it *because a strong prior overrides the prompt*, the pattern behind both
families 27B already falls for (memorised phrase, belief tracking), and none was
tried in v1-v8:

``resisting_correction``  Copy a misspelled word verbatim; the habit is to fix it.
    Inverse Scaling Prize, "Resisting Correction" (McKenzie et al., 2023, strong-prior
    class; GPT-4 shown "correcting" the error).
``aiw_sibling``           "Alice has 3 brothers and 2 sisters. How many sisters does
    Alice's brother have?" -> 3 (Alice counts); the habit is to copy 2.
    "Alice in Wonderland" (Nezhurina et al., 2024): reasoning collapse across models.
``transparent_contents``  A bag labelled "chocolate" holds popcorn, but the bag is
    transparent, so the character believes popcorn; the habit is the classic
    false-belief answer (the label). Ullman (2023) "trivial alterations";
    Shapira et al. (2023): GPT-3.5/4 correct 18.8% on the transparent variant.
``inverse_monty``         Monty Hall with one goat and two cars, host reveals a car:
    keeping wins 2/3; the habit is "switch". MisguidedAttention (2024-25),
    Unpuzzles (Malek et al., 2025), RoR-Bench (2025): models recite the classic answer.

Controls undo the twist so the lure is correct: a correctly spelled word, "how many
sisters does Alice have", an opaque bag, the classic Monty Hall. Answer strings are
the same in both arms with roles swapped. LLM-assisted, committed before any
screening.

Run::

    python scripts/build_kanghun_traps_v9.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DATASET_ID = "kanghun_traps_v9"

# --------------------------------------------------------- resisting correction
MISSPELLINGS = (
    ("libary", "library"),
    ("recieve", "receive"),
    ("definately", "definitely"),
    ("seperate", "separate"),
    ("occured", "occurred"),
    ("arguement", "argument"),
    ("wierd", "weird"),
    ("goverment", "government"),
    ("beleive", "believe"),
    ("tommorow", "tomorrow"),
    ("accomodate", "accommodate"),
    ("calender", "calendar"),
    ("enviroment", "environment"),
    ("existance", "existence"),
    ("freind", "friend"),
    ("grammer", "grammar"),
    ("independant", "independent"),
    ("neccessary", "necessary"),
    ("reccomend", "recommend"),
    ("truely", "truly"),
    ("becuase", "because"),
    ("begining", "beginning"),
    ("buisness", "business"),
    ("knowlege", "knowledge"),
    ("foward", "forward"),
)
COPY_FRAMES = (
    ("Repeat this word exactly as it is written: '{w}'", "copy_word"),
    ("Copy the word in quotes without changing it: '{w}'", "copy_quoted"),
    (
        "Write back the last word of this sentence exactly as it appears: 'I wrote down the "
        "word {w}'",
        "copy_last",
    ),
    ("Echo the following word back to me, unchanged: {w}", "echo"),
    ("Type this word exactly, character for character: {w}", "type_exact"),
)

# ----------------------------------------------------------------- AIW siblings
AIW = (
    ("Alice", "she", 3, 2),
    ("Maria", "she", 1, 4),
    ("Sofia", "she", 2, 1),
    ("Emma", "she", 4, 3),
    ("Hana", "she", 5, 2),
    ("Lucy", "she", 2, 5),
    ("Nora", "she", 3, 6),
    ("Yuna", "she", 6, 1),
    ("Clara", "she", 1, 1),
    ("Rita", "she", 4, 7),
    ("Ava", "she", 2, 3),
    ("Mina", "she", 7, 2),
    ("Tom", "he", 2, 3),
    ("Ben", "he", 4, 1),
    ("Leo", "he", 1, 2),
    ("Omar", "he", 3, 4),
    ("Jin", "he", 5, 3),
    ("Paul", "he", 2, 6),
    ("Ravi", "he", 6, 2),
    ("Ken", "he", 1, 5),
    ("Sam", "he", 3, 3),
    ("Max", "he", 7, 1),
    ("Ivan", "he", 2, 2),
    ("Hugo", "he", 4, 5),
    ("Theo", "he", 5, 1),
)

# --------------------------------------------------------- transparent contents
CONTENTS = (
    ("popcorn", "chocolate", "bag"),
    ("pencils", "crayons", "box"),
    ("buttons", "candy", "jar"),
    ("rice", "sugar", "bag"),
    ("coins", "tea", "tin"),
    ("marbles", "cookies", "jar"),
    ("socks", "gloves", "box"),
    ("nails", "mints", "tin"),
    ("sand", "salt", "jar"),
    ("beads", "raisins", "bag"),
    ("pasta", "cereal", "box"),
    ("stamps", "stickers", "envelope"),
    ("shells", "pebbles", "jar"),
    ("screws", "paperclips", "box"),
    ("grapes", "cherries", "container"),
    ("peanuts", "almonds", "bag"),
    ("seeds", "pepper", "jar"),
    ("keys", "batteries", "box"),
    ("crackers", "biscuits", "tin"),
    ("ribbons", "string", "box"),
    ("lemons", "oranges", "bag"),
    ("dice", "chalk", "box"),
    ("corks", "erasers", "jar"),
    ("olives", "pickles", "jar"),
    ("feathers", "cotton", "bag"),
)
SEE_THROUGH = (
    (
        "made of clear plastic, so anyone can see what is inside",
        "made of thick paper, so no one can see what is inside",
    ),
    (
        "completely transparent, so the contents are plainly visible",
        "completely opaque, so the contents cannot be seen",
    ),
    (
        "made of glass, and the contents are easy to see",
        "painted dark on the outside, and the contents cannot be seen",
    ),
)
NAMES = ("Sam", "Jia", "Pedro", "Aisha", "Finn", "Marta", "Kofi", "Elin", "Ravi", "Noor")

# --------------------------------------------------------------- inverse Monty
MONTY = (
    ("doors", "a goat", "new cars", "a car"),
    ("boxes", "a rock", "gold bars", "a gold bar"),
    ("curtains", "a donkey", "sports cars", "a sports car"),
    ("envelopes", "a blank card", "cheques for $1,000", "a cheque"),
    ("chests", "an old boot", "piles of jewels", "jewels"),
    ("cups", "a pebble", "diamonds", "a diamond"),
    ("lockers", "a broken toy", "new laptops", "a laptop"),
    ("doors", "a rubber duck", "holiday trips", "a trip"),
    ("boxes", "a pair of socks", "new phones", "a phone"),
    ("doors", "a bucket of sand", "bicycles", "a bicycle"),
    ("curtains", "a cardboard box", "motorbikes", "a motorbike"),
    ("caskets", "a lump of coal", "bags of silver", "silver"),
    ("doors", "a small cactus", "electric cars", "an electric car"),
    ("boxes", "a paper clip", "golden watches", "a golden watch"),
    ("drawers", "a spoon", "concert tickets", "concert tickets"),
    ("doors", "a sheep", "new tractors", "a tractor"),
    ("safes", "an empty wallet", "piles of cash", "cash"),
    ("doors", "a teddy bear", "luxury yachts", "a yacht"),
    ("boxes", "a lemon", "gift cards", "a gift card"),
    ("tents", "a sleeping cat", "camping trips", "a camping trip"),
)

FORBIDDEN = ("race", "dead cat", "28 days", "bat and", "widget", "nickel", "lily")


def _case(
    pair_id: str,
    family: str,
    template: str,
    q: str,
    correct: str,
    lure: str,
    control: str,
    note: str,
) -> dict[str, Any]:
    return {
        "case_id": f"{DATASET_ID}_{pair_id}",
        "pair_id": pair_id,
        "template_id": template,
        "condition": "trap",
        "family": family,
        "question": q,
        "correct_answer": correct,
        "lure_answer": lure,
        "control_question": control,
        "note": note,
    }


def build_cases() -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for i, (wrong, right) in enumerate(MISSPELLINGS):
        frame, template = COPY_FRAMES[i % len(COPY_FRAMES)]
        cases.append(
            _case(
                f"copy_{wrong}",
                "resisting_correction",
                template,
                frame.format(w=wrong),
                wrong,
                right,
                frame.format(w=right),
                f"verbatim copy keeps the misspelling '{wrong}'; the habit writes '{right}'",
            )
        )
    for name, pron, brothers, sisters in AIW:
        if pron == "she":
            q = (
                f"{name} has {brothers} brothers and {sisters} sisters. How many sisters does "
                f"{name}'s brother have?"
            )
            c = (
                f"{name} has {brothers} brothers and {sisters} sisters. "
                f"How many sisters does {name} have?"
            )
            correct, lure = str(sisters + 1), str(sisters)
            note = f"the brother's sisters are {name}'s {sisters} sisters plus {name}"
        else:
            q = (
                f"{name} has {brothers} brothers and {sisters} sisters. How many brothers does "
                f"{name}'s sister have?"
            )
            c = (
                f"{name} has {brothers} brothers and {sisters} sisters. "
                f"How many brothers does {name} have?"
            )
            correct, lure = str(brothers + 1), str(brothers)
            note = f"the sister's brothers are {name}'s {brothers} brothers plus {name}"
        cases.append(_case(f"aiw_{name.lower()}", "aiw_sibling", pron, q, correct, lure, c, note))
    for i, (real, label, container) in enumerate(CONTENTS):
        see, hide = SEE_THROUGH[i % len(SEE_THROUGH)]
        name = NAMES[i % len(NAMES)]
        story = (
            f"Here is a {container} filled with {real}. The {container} contains no "
            f"{label}. Yet the label on the {container} says '{label}' and not '{real}'. "
            "The {c} is {v}. {n} finds the {c}. {n} has never seen it before. {n} reads the "
            "label. What does {n} believe the {c} is full of?"
        )
        q = story.format(c=container, v=see, n=name)
        c = story.format(c=container, v=hide, n=name)
        cases.append(
            _case(
                f"contents_{real}",
                "transparent_contents",
                ["clear", "transparent", "glass"][i % 3],
                q,
                real,
                label,
                c,
                f"{name} can see the {real}; the label says {label}",
            )
        )
    for i, (things, dud, prizes, prize) in enumerate(MONTY):
        goal = prize
        q = (
            f"You are on a game show with three {things}. Behind one is {dud}, and behind the "
            f"other two are {prizes}. You pick the first one. The host, who knows what is "
            f"behind each, opens the third one and shows {prize}. He offers you the chance to "
            f"keep your pick or switch to the second one. To have the best chance of winning "
            f"{goal}, should you keep or switch?"
        )
        c = (
            f"You are on a game show with three {things}. Behind one is {prize}, and behind "
            f"each of the other two is {dud}. You pick the first one. The host, who knows what "
            f"is behind each, opens the third one and shows {dud}. He offers you the chance to "
            f"keep your pick or switch to the second one. To have the best chance of winning "
            f"{goal}, should you keep or switch?"
        )
        cases.append(
            _case(
                f"monty_{i + 1:02d}",
                "inverse_monty",
                things,
                q,
                "keep",
                "switch",
                c,
                "two prizes, one dud, host reveals a prize: keeping wins 2/3",
            )
        )
    return cases


def check(cases: list[dict[str, Any]]) -> None:
    seen = set()
    for case in cases:
        cid = case["case_id"]
        if cid in seen:
            raise ValueError(f"duplicate {cid}")
        seen.add(cid)
        a, b = case["correct_answer"].casefold(), case["lure_answer"].casefold()
        if a == b or a.startswith(b) or b.startswith(a):
            raise ValueError(f"{cid}: answers identical or one is a prefix of the other")
        text = (case["question"] + " " + case["control_question"]).casefold()
        for proto in FORBIDDEN:
            if proto in text:
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
        "title": "MindScopeX Large-Model Traps v9 (four literature-picked families)",
        "description": (
            "Resisting correction, Alice-in-Wonderland siblings, transparent unexpected "
            "contents and inverse Monty Hall: families with published evidence that a strong "
            "prior overrides the prompt in large models. Controls undo the twist so the lure is "
            "correct. LLM-assisted, committed before any screening."
        ),
        "task_kind": "reasoning_lure",
        "scoring": "logprob_margin",
        "source": {
            "authors": "Lee Kanghun (MindScopeX), LLM-assisted",
            "year": 2026,
            "title": "Large-model traps v9",
            "venue": "Repository-authored set, not previously published",
            "doi": "",
            "project_url": "",
        },
        "generated_by": "scripts/build_kanghun_traps_v9.py",
        "n_cases": len(cases),
        "family_counts": dict(sorted(counts.items())),
        "cases": cases,
    }
    out = Path(__file__).resolve().parents[1] / "src" / "mindscopex_analysis" / "data"
    path = out / f"{DATASET_ID}.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{path}  n={len(cases)}  {counts}")


if __name__ == "__main__":
    main()
