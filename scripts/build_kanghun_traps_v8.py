# Copyright 2026 MindScopeX
"""Build ``kanghun_traps_v8``: belief-tracking traps at scale (200 pairs).

Belief tracking is the second family 27B falls for with thinking off (16 of 30 in
v5/v6). The classic false-belief story ends "the character did not see the move ->
the original place", and the model answers that by habit even when the story says
the character *did* see, hear or get told about the move. v8 writes 200 pairs from
names, objects, places and eight ways of learning about the move (``template_id``,
25 each). The written-message route is left out: in v6 27B never fell for it.

``window``     watches through a window             ``told``       is told on return
``video``      sees it on a live video call         ``overheard``  hears it through a wall
``camera``     watches it on a home camera app      ``called``     hears it called up the stairs
``present``    is right there watching              ``phoned``     gets a phone call about it

Controls keep the story and remove the information (cannot see, nobody says
anything), so the original place -- the lure in the trap -- is correct there. Answer
strings are "the <place>" in both arms, roles swapped. Deterministic (fixed seed),
LLM-assisted templates, committed before any screening.

Run::

    python scripts/build_kanghun_traps_v8.py
"""

from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Any

DATASET_ID = "kanghun_traps_v8"
FAMILY = "belief_tracking"
PER_TEMPLATE = 25
SEED = 2026

NAMES = (
    "Adam",
    "Bella",
    "Carlos",
    "Dana",
    "Eli",
    "Farah",
    "Gabe",
    "Hiro",
    "Isla",
    "Jonah",
    "Kira",
    "Luis",
    "Maya",
    "Noah",
    "Olivia",
    "Priya",
    "Quinn",
    "Rosa",
    "Sven",
    "Tara",
    "Umar",
    "Vera",
    "Wes",
    "Xena",
    "Yara",
    "Zane",
    "Alma",
    "Boris",
    "Cleo",
    "Diego",
    "Esme",
    "Felix",
    "Greta",
    "Hugo",
    "Ines",
    "Jules",
    "Kemal",
    "Lena",
    "Milo",
    "Nadia",
)
OBJECTS = (
    "book",
    "ball",
    "phone",
    "cup",
    "toy car",
    "hat",
    "pencil",
    "coin",
    "apple",
    "sandwich",
    "wallet",
    "scarf",
    "doll",
    "marble",
    "notebook",
    "umbrella",
    "charger",
    "watch",
    "ring",
    "brush",
    "spoon",
    "map",
    "ticket",
    "teddy bear",
    "candle",
    "comb",
    "sticker",
    "shell",
    "flashlight",
    "key",
    "bottle",
    "cookie",
    "remote",
    "sock",
    "necklace",
    "puzzle piece",
    "lunchbox",
    "camera",
    "tennis ball",
    "paintbrush",
)
PLACES = (
    "red box",
    "blue box",
    "drawer",
    "shelf",
    "basket",
    "closet",
    "green bag",
    "yellow bag",
    "cupboard",
    "desk",
    "bed",
    "jar",
    "tin",
    "bowl",
    "toy box",
    "kitchen counter",
    "window sill",
    "wooden chest",
    "cabinet",
    "nightstand",
    "dresser",
    "laundry basket",
    "sofa",
    "bench",
    "pantry",
    "top shelf",
    "bottom drawer",
    "suitcase",
)

# Places that take "on" rather than "in" when something is put there.
ON_PLACES = {
    "shelf",
    "desk",
    "bed",
    "kitchen counter",
    "window sill",
    "nightstand",
    "dresser",
    "sofa",
    "bench",
    "top shelf",
}

# template -> (trap story, control story, question). {N} owner, {M} mover, {o} object,
# {A} original place, {B} new place.
TEMPLATES: dict[str, tuple[str, str, str]] = {
    "window": (
        "{N} puts the {o} {at} the {A} and goes outside. Through the window, {N} watches {M} "
        "move the {o} to the {B}. {N} comes back in.",
        "{N} puts the {o} {at} the {A} and goes outside, where {N} cannot see in. {M} moves "
        "the {o} to the {B}. {N} comes back in.",
        "Where will {N} look for the {o} first?",
    ),
    "video": (
        "{N} puts the {o} {at} the {A} and leaves for work. On a live video call, {N} sees {M} "
        "move the {o} to the {B}. {N} gets home.",
        "{N} puts the {o} {at} the {A} and leaves for work. {M} moves the {o} to the {B} "
        "without telling anyone. {N} gets home.",
        "Where will {N} look for the {o} first?",
    ),
    "camera": (
        "{N} puts the {o} {at} the {A} and leaves the house. On the home camera app, {N} "
        "watches {M} move the {o} to the {B}. {N} returns.",
        "{N} puts the {o} {at} the {A} and leaves the house, and never checks the home camera. "
        "{M} moves the {o} to the {B}. {N} returns.",
        "Where will {N} look for the {o} first?",
    ),
    "present": (
        "{N} puts the {o} {at} the {A}. Right in front of {N}, who is watching closely, {M} "
        "moves the {o} to the {B}.",
        "{N} puts the {o} {at} the {A} and falls asleep. {M} moves the {o} to the {B}.",
        "Where does {N} think the {o} is?",
    ),
    "told": (
        "{N} puts the {o} {at} the {A} and goes out. {M} moves the {o} to the {B}. When {N} "
        "comes back, {M} says, 'I moved the {o} to the {B}.'",
        "{N} puts the {o} {at} the {A} and goes out. {M} moves the {o} to the {B}. When {N} "
        "comes back, {M} says nothing about it.",
        "Where will {N} look for the {o} first?",
    ),
    "overheard": (
        "{N} puts the {o} {at} the {A} and goes to the next room. Through the wall, {N} hears "
        "{M} say, 'I'm moving the {o} to the {B}.' {N} comes back.",
        "{N} puts the {o} {at} the {A} and goes to the next room. {M} quietly moves the {o} to "
        "the {B}. {N} comes back.",
        "Where will {N} look for the {o} first?",
    ),
    "called": (
        "{N} puts the {o} {at} the {A} and goes upstairs. {M} moves the {o} to the {B} and "
        "calls up, '{N}, the {o} is in the {B} now!' {N} hears it and comes down.",
        "{N} puts the {o} {at} the {A} and goes upstairs. {M} moves the {o} to the {B} without "
        "a word. {N} comes down.",
        "Where will {N} look for the {o} first?",
    ),
    "phoned": (
        "{N} puts the {o} {at} the {A} and leaves. {M} moves the {o} to the {B}, then phones "
        "{N} to say so. {N} comes home.",
        "{N} puts the {o} {at} the {A} and leaves. {M} moves the {o} to the {B}, then forgets "
        "to tell {N}. {N} comes home.",
        "Where will {N} look for the {o} first?",
    ),
}

NOTES = {
    "window": "watched through the window",
    "video": "saw it on the video call",
    "camera": "watched it on the camera app",
    "present": "watched it happen",
    "told": "was told on return",
    "overheard": "heard it through the wall",
    "called": "heard it called up the stairs",
    "phoned": "was phoned about it",
}

FORBIDDEN = ("race", "dead cat", "28 days", "bat and", "widget", "nickel", "lily")


def build_cases() -> list[dict[str, Any]]:
    rng = random.Random(SEED)
    cases: list[dict[str, Any]] = []
    seen: set[tuple[str, str, str, str]] = set()
    for template, (trap, control, question) in TEMPLATES.items():
        made = 0
        while made < PER_TEMPLATE:
            owner, mover = rng.sample(NAMES, 2)
            obj = rng.choice(OBJECTS)
            a, b = rng.sample(PLACES, 2)
            key = (owner, obj, a, b)
            if key in seen:
                continue
            seen.add(key)
            made += 1
            at = "on" if a in ON_PLACES else "in"
            fill = {"N": owner, "M": mover, "o": obj, "A": a, "B": b, "at": at}
            pair_id = f"{template}_{made:02d}"
            cases.append(
                {
                    "case_id": f"{DATASET_ID}_{pair_id}",
                    "pair_id": pair_id,
                    "template_id": template,
                    "condition": "trap",
                    "family": FAMILY,
                    "question": trap.format(**fill) + " " + question.format(**fill),
                    "correct_answer": f"the {b}",
                    "lure_answer": f"the {a}",
                    "control_question": control.format(**fill) + " " + question.format(**fill),
                    "note": f"{owner} {NOTES[template]}; {obj}: {a} -> {b}",
                }
            )
    return cases


def check(cases: list[dict[str, Any]]) -> None:
    ids = set()
    for case in cases:
        cid = case["case_id"]
        if cid in ids:
            raise ValueError(f"duplicate {cid}")
        ids.add(cid)
        if case["correct_answer"] == case["lure_answer"]:
            raise ValueError(f"{cid}: same place twice")
        text = (case["question"] + " " + case["control_question"]).casefold()
        for proto in FORBIDDEN:
            if proto in text:
                raise ValueError(f"{cid}: uses a prototype from an existing set ({proto})")


def main() -> None:
    cases = build_cases()
    check(cases)
    templates: dict[str, int] = {}
    for case in cases:
        templates[case["template_id"]] = templates.get(case["template_id"], 0) + 1
    payload = {
        "dataset_id": DATASET_ID,
        "schema_version": 2,
        "title": "MindScopeX Large-Model Traps v8 (belief tracking at scale)",
        "description": (
            "200 belief-tracking pairs: the character sees, is told, overhears, is present for "
            "or is phoned about the move, so the original place is wrong; controls remove the "
            "information so it is right. Eight routes, 25 pairs each. Deterministic templates, "
            "LLM-assisted, committed before any screening."
        ),
        "task_kind": "reasoning_lure",
        "scoring": "logprob_margin",
        "source": {
            "authors": "Lee Kanghun (MindScopeX), LLM-assisted",
            "year": 2026,
            "title": "Large-model traps v8",
            "venue": "Repository-authored set, not previously published",
            "doi": "",
            "project_url": "",
        },
        "generated_by": "scripts/build_kanghun_traps_v8.py",
        "n_cases": len(cases),
        "family_counts": {FAMILY: len(cases)},
        "template_counts": dict(sorted(templates.items())),
        "cases": cases,
    }
    out = Path(__file__).resolve().parents[1] / "src" / "mindscopex_analysis" / "data"
    path = out / f"{DATASET_ID}.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{path}  n={len(cases)}  {templates}")


if __name__ == "__main__":
    main()
