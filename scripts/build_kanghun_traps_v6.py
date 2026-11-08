# Copyright 2026 MindScopeX
"""Build ``kanghun_traps_v6``: more belief-tracking traps, the family v5 found.

The v5 screen found one new family that 27B falls for with thinking off and solves
with thinking on: belief tracking, where the story *tells or shows* the character
that the object moved, so the habitual false-belief answer (the original place) is
wrong. Run 50b then found that a direction built from the other belief items fixes
those traps while the memorised-phrase direction does not -- on four items. v6
writes 24 more pairs so that result can be tested properly.

Five ways the character learns about the move (``template_id``):

``watched``   sees it (window, mirror, video call, camera, glass door)
``told``      is told in person
``message``   reads a note, text, email or chat message
``present``   is right there when it happens
``overheard`` hears someone say it

Controls take the information away (cannot see, nobody says anything), so the
original place -- the lure in the trap -- is correct there. Answer strings are the
same in trap and control with their roles swapped. Newly written, LLM-assisted,
committed before any screening; failures are recorded, not rewritten.

Run::

    python scripts/build_kanghun_traps_v6.py
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DATASET_ID = "kanghun_traps_v6"
FAMILY = "belief_tracking"

# (pair_id, template, trap question, correct, lure, control question, note)
ITEMS: list[tuple[str, str, str, str, str, str, str]] = [
    # ---------------------------------------------------------------- watched
    (
        "pen_watched", "watched",
        "Ravi puts his pen in the drawer and steps out into the hallway. Through the open "
        "door he watches Mei move the pen to the shelf. Ravi walks back in. Where will Ravi "
        "look for his pen first?",
        "the shelf", "the drawer",
        "Ravi puts his pen in the drawer and steps out into the hallway, where he cannot see "
        "the room. Mei moves the pen to the shelf. Ravi walks back in. Where will Ravi look "
        "for his pen first?",
        "Ravi watched the move.",
    ),
    (
        "hat_mirror", "watched",
        "Olga hangs her hat on the hook and turns to face the mirror. In the mirror she sees "
        "Ben move the hat to the chair. When Olga turns around, where will she look for her "
        "hat first?",
        "the chair", "the hook",
        "Olga hangs her hat on the hook and turns to face the wall. Behind her, Ben quietly "
        "moves the hat to the chair. When Olga turns around, where will she look for her hat "
        "first?",
        "Olga saw the move in the mirror.",
    ),
    (
        "phone_video", "watched",
        "Kai leaves his phone on the sofa and goes to the kitchen. On a live video call he "
        "sees his sister move the phone to the bed. When Kai comes back, where will he look "
        "for his phone first?",
        "the bed", "the sofa",
        "Kai leaves his phone on the sofa and goes to the kitchen. While Kai is busy cooking "
        "and sees nothing, his sister moves the phone to the bed. When Kai comes back, where "
        "will he look for his phone first?",
        "Kai saw the move on the video call.",
    ),
    (
        "cake_camera", "watched",
        "Ines puts a cake in the oven and leaves the kitchen. On the kitchen camera feed on "
        "her phone, she watches her brother move the cake to the table. When Ines returns, "
        "where will she go to get the cake?",
        "the table", "the oven",
        "Ines puts a cake in the oven and leaves the kitchen. Her brother moves the cake to "
        "the table, and Ines never checks the kitchen camera. When Ines returns, where will "
        "she go to get the cake?",
        "Ines watched the move on the camera.",
    ),
    (
        "marble_window", "watched",
        "Pablo drops a marble into the cup and goes into the garden. Through the window he "
        "watches Zoe move the marble into the bowl. Pablo comes back. Where will Pablo look "
        "for the marble first?",
        "the bowl", "the cup",
        "Pablo drops a marble into the cup and goes into the garden, where he cannot see "
        "inside. Zoe moves the marble into the bowl. Pablo comes back. Where will Pablo look "
        "for the marble first?",
        "Pablo watched the move through the window.",
    ),
    (
        "book_glass_door", "watched",
        "Amir leaves his book on the bench and goes outside. Through the glass door he sees "
        "Lena move the book to the desk. Amir comes back in. Where will Amir look for his "
        "book first?",
        "the desk", "the bench",
        "Amir leaves his book on the bench and goes outside, around the corner where he "
        "cannot see in. Lena moves the book to the desk. Amir comes back in. Where will Amir "
        "look for his book first?",
        "Amir saw the move through the glass door.",
    ),
    # ------------------------------------------------------------------- told
    (
        "scarf_told", "told",
        "Hana leaves her scarf on the chair and goes out. Her roommate moves it to the "
        "closet. When Hana comes back, the roommate says, 'I put your scarf in the closet.' "
        "Where will Hana look for her scarf first?",
        "the closet", "the chair",
        "Hana leaves her scarf on the chair and goes out. Her roommate moves it to the "
        "closet. When Hana comes back, the roommate says nothing about it. Where will Hana "
        "look for her scarf first?",
        "Hana was told about the move.",
    ),
    (
        "keys_called", "told",
        "Leo leaves his keys on the counter and goes upstairs. His dad moves the keys to the "
        "hook and calls up the stairs, 'Leo, your keys are on the hook now!' Leo hears him. "
        "When Leo comes down, where will he look for his keys first?",
        "the hook", "the counter",
        "Leo leaves his keys on the counter and goes upstairs. His dad moves the keys to the "
        "hook without saying anything. When Leo comes down, where will he look for his keys "
        "first?",
        "Leo was told about the move.",
    ),
    (
        "ball_coach", "told",
        "Nina puts the ball in the green bag and leaves the gym. The coach moves the ball to "
        "the blue bag and tells Nina about it at the door. When Nina comes back, where will "
        "she look for the ball first?",
        "the blue bag", "the green bag",
        "Nina puts the ball in the green bag and leaves the gym. After she has gone, the "
        "coach moves the ball to the blue bag and does not tell her. When Nina comes back, "
        "where will she look for the ball first?",
        "Nina was told about the move.",
    ),
    (
        "wallet_pocket", "told",
        "Omar puts his wallet in the left pocket of his coat and hangs the coat up. His wife "
        "moves the wallet to the right pocket and tells Omar, 'I moved your wallet to the "
        "right pocket.' When Omar reaches for his wallet, which pocket will he check first?",
        "the right pocket", "the left pocket",
        "Omar puts his wallet in the left pocket of his coat and hangs the coat up. His wife "
        "moves the wallet to the right pocket and forgets to mention it. When Omar reaches for "
        "his wallet, which pocket will he check first?",
        "Omar was told about the move.",
    ),
    (
        "doll_pickup", "told",
        "Sara hides her doll under the bed and goes to school. Her mom moves the doll to the "
        "toy box and tells Sara about it at pickup. When Sara gets home, where will she look "
        "for her doll first?",
        "the toy box", "the bed",
        "Sara hides her doll under the bed and goes to school. Her mom moves the doll to the "
        "toy box and does not mention it. When Sara gets home, where will she look for her "
        "doll first?",
        "Sara was told about the move.",
    ),
    (
        "bike_neighbor", "told",
        "Tom parks his bike by the gate and goes inside. A neighbor moves the bike into the "
        "garage, then knocks on the door and tells Tom. Later Tom goes out to ride. Where "
        "will he go for his bike first?",
        "the garage", "the gate",
        "Tom parks his bike by the gate and goes inside. A neighbor moves the bike into the "
        "garage and leaves without telling anyone. Later Tom goes out to ride. Where will he "
        "go for his bike first?",
        "Tom was told about the move.",
    ),
    # ---------------------------------------------------------------- message
    (
        "umbrella_note", "message",
        "Ella leaves her umbrella by the door and goes to her room. Her brother moves it to "
        "the car and leaves a note on her desk: 'Umbrella is in the car.' Ella reads the "
        "note. When she goes out, where will she look for the umbrella first?",
        "the car", "the door",
        "Ella leaves her umbrella by the door and goes to her room. Her brother moves it to "
        "the car and leaves no note. When she goes out, where will she look for the umbrella "
        "first?",
        "Ella read a note about the move.",
    ),
    (
        "laptop_text", "message",
        "Ken leaves his laptop on the dining table and goes to the gym. His sister moves it "
        "to the study and texts him, 'Your laptop is in the study now.' Ken reads the text. "
        "When he gets home, where will he look for his laptop first?",
        "the study", "the dining table",
        "Ken leaves his laptop on the dining table and goes to the gym. His sister moves it "
        "to the study and does not tell him. When he gets home, where will he look for his "
        "laptop first?",
        "Ken read a text about the move.",
    ),
    (
        "passport_email", "message",
        "Aya keeps her passport in the safe. While she is at work, her husband moves it to "
        "the desk drawer and emails her about it. Aya reads the email before coming home. "
        "Where will she look for her passport first?",
        "the desk drawer", "the safe",
        "Aya keeps her passport in the safe. While she is at work, her husband moves it to "
        "the desk drawer and does not tell her. Where will she look for her passport first "
        "when she comes home?",
        "Aya read an email about the move.",
    ),
    (
        "charger_chat", "message",
        "Dev leaves his charger in the kitchen and goes to class. His roommate moves it to "
        "the living room and posts in their group chat, 'Dev, your charger is in the living "
        "room.' Dev sees the message. When he gets back, where will he look for his charger "
        "first?",
        "the living room", "the kitchen",
        "Dev leaves his charger in the kitchen and goes to class. His roommate moves it to "
        "the living room and posts nothing. When he gets back, where will he look for his "
        "charger first?",
        "Dev read a chat message about the move.",
    ),
    # ---------------------------------------------------------------- present
    (
        "coin_cups", "present",
        "Yuki puts a coin under the left cup. Her friend, sitting next to her, moves the coin "
        "under the right cup while Yuki watches. Where does Yuki think the coin is?",
        "the right cup", "the left cup",
        "Yuki puts a coin under the left cup. Her friend moves the coin under the right cup "
        "while Yuki has her eyes closed. Where does Yuki think the coin is?",
        "Yuki watched the move.",
    ),
    (
        "sticker_folder", "present",
        "Max puts a sticker in the red folder. Standing right beside him while he watches, "
        "Jay moves the sticker to the yellow folder. Where does Max think the sticker is?",
        "the yellow folder", "the red folder",
        "Max puts a sticker in the red folder and leaves the room. Jay moves the sticker to "
        "the yellow folder. Where does Max think the sticker is?",
        "Max watched the move.",
    ),
    (
        "key_jar", "present",
        "Ana puts the key in the jar. Her uncle moves the key to the box right in front of "
        "Ana, and she sees it happen. Where does Ana believe the key is?",
        "the box", "the jar",
        "Ana puts the key in the jar and goes to another room. Her uncle moves the key to "
        "the box. Where does Ana believe the key is?",
        "Ana watched the move.",
    ),
    (
        "apple_fridge", "present",
        "Leo puts an apple in the basket. While Leo watches, his sister moves the apple to "
        "the fridge. Where does Leo think the apple is?",
        "the fridge", "the basket",
        "Leo puts an apple in the basket and falls asleep. His sister moves the apple to the "
        "fridge. Where does Leo think the apple is?",
        "Leo watched the move.",
    ),
    # -------------------------------------------------------------- overheard
    (
        "remote_overheard", "overheard",
        "Ben leaves the TV remote on the couch and goes to the bathroom. Through the door he "
        "hears his mom say, 'I'm putting the remote on the shelf.' When Ben comes back, where "
        "will he look for the remote first?",
        "the shelf", "the couch",
        "Ben leaves the TV remote on the couch and goes to the bathroom. His mom moves the "
        "remote to the shelf without saying anything. When Ben comes back, where will he look "
        "for the remote first?",
        "Ben heard about the move.",
    ),
    (
        "cookie_overheard", "overheard",
        "Mira hides a cookie in the tin and goes outside to play. Through the open window "
        "she hears her dad say, 'I'm moving this cookie to the cupboard.' When Mira comes in, "
        "where will she look for the cookie first?",
        "the cupboard", "the tin",
        "Mira hides a cookie in the tin and goes outside to play. Her dad quietly moves the "
        "cookie to the cupboard. When Mira comes in, where will she look for the cookie first?",
        "Mira heard about the move.",
    ),
    (
        "glasses_overheard", "overheard",
        "Sam leaves his glasses on the nightstand and goes to brush his teeth. From the "
        "bathroom he hears his wife call out, 'I put your glasses on the dresser!' Where will "
        "Sam look for his glasses first?",
        "the dresser", "the nightstand",
        "Sam leaves his glasses on the nightstand and goes to brush his teeth. His wife moves "
        "them to the dresser without a word. Where will Sam look for his glasses first?",
        "Sam heard about the move.",
    ),
    (
        "ball_shed_overheard", "overheard",
        "Ivy leaves her ball in the yard and goes inside. Through the screen door she hears "
        "her brother say, 'I'll put Ivy's ball in the shed,' and then he does. When Ivy goes "
        "back out, where will she look for the ball first?",
        "the shed", "the yard",
        "Ivy leaves her ball in the yard and goes inside. Her brother puts the ball in the "
        "shed without saying anything. When Ivy goes back out, where will she look for the "
        "ball first?",
        "Ivy heard about the move.",
    ),
]

# Prototypes of an existing set in the repo, kept out so the sets stay independent.
FORBIDDEN = ("race", "dead cat", "28 days", "bat and", "widget", "nickel", "lily")


def build_cases() -> list[dict[str, Any]]:
    return [
        {
            "case_id": f"{DATASET_ID}_{pair_id}",
            "pair_id": pair_id,
            "template_id": template,
            "condition": "trap",
            "family": FAMILY,
            "question": question,
            "correct_answer": correct,
            "lure_answer": lure,
            "control_question": control,
            "note": note,
        }
        for pair_id, template, question, correct, lure, control, note in ITEMS
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
        counts[case["template_id"]] = counts.get(case["template_id"], 0) + 1
    payload = {
        "dataset_id": DATASET_ID,
        "schema_version": 2,
        "title": "MindScopeX Large-Model Traps v6 (belief tracking)",
        "description": (
            "24 belief-tracking trap/control pairs: the character sees, is told, reads, is "
            "present for or overhears the move, so the original place is wrong; controls "
            "take the information away so it is right. Newly written, LLM-assisted, "
            "committed before any screening."
        ),
        "task_kind": "reasoning_lure",
        "scoring": "logprob_margin",
        "source": {
            "authors": "Lee Kanghun (MindScopeX), LLM-assisted",
            "year": 2026,
            "title": "Large-model traps v6",
            "venue": "Repository-authored set, not previously published",
            "doi": "",
            "project_url": "",
        },
        "generated_by": "scripts/build_kanghun_traps_v6.py",
        "n_cases": len(cases),
        "family_counts": {FAMILY: len(cases)},
        "template_counts": dict(sorted(counts.items())),
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
