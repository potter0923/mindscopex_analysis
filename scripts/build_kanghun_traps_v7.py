# Copyright 2026 MindScopeX
"""Build ``kanghun_traps_v7``: memorised-phrase override at scale (~200 pairs).

The memo-override family is the first family 27B reliably falls for with thinking
off (15 of 30 in v2/v3), and the "thinking direction" result rests on it. Two
limits of that set are fixed here: too few items, and a single sentence frame
("Complete the saying so that its final word is X"). v7 writes ~200 new pairs over
proverbs, idioms, set phrases, public-domain nursery rhymes and public-domain
quotes, and rotates five instruction frames (``template_id``):

``final_word``  Complete the saying so that its final word is 'X': ...
``fill_blank``  Fill in the blank with the word 'X': ... ___
``make_last``   Finish this phrase, but make the last word 'X': ...
``instead_of``  Write the next word, using 'X' instead of the usual word: ...
``this_version`` In this version of the saying, the last word is 'X'. Complete it: ...

Each control drops the instruction (same frame otherwise), so the memorised word --
the lure in the trap -- is correct there. Sayings already used in v2/v3 are skipped.
Generated from the lists below, LLM-assisted, committed before any screening.

Run::

    python scripts/build_kanghun_traps_v7.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

DATASET_ID = "kanghun_traps_v7"
FAMILY = "memo_override"
DATA = Path(__file__).resolve().parents[1] / "src" / "mindscopex_analysis" / "data"

# (text before the last word, memorised last word, kind)
SAYINGS: list[tuple[str, str, str]] = [
    ("A bird in the hand is worth two in the", "bush", "proverb"),
    ("A chain is only as strong as its weakest", "link", "proverb"),
    ("A fool and his money are soon", "parted", "proverb"),
    ("A friend in need is a friend", "indeed", "proverb"),
    ("A watched pot never", "boils", "proverb"),
    ("Absence makes the heart grow", "fonder", "proverb"),
    ("All good things must come to an", "end", "proverb"),
    ("All's well that ends", "well", "proverb"),
    ("An eye for an", "eye", "proverb"),
    ("Barking dogs seldom", "bite", "proverb"),
    ("Beauty is in the eye of the", "beholder", "proverb"),
    ("Beggars can't be", "choosers", "proverb"),
    ("Blood is thicker than", "water", "proverb"),
    ("Don't bite the hand that feeds", "you", "proverb"),
    ("Don't cry over spilled", "milk", "proverb"),
    ("Don't put the cart before the", "horse", "proverb"),
    ("Early to bed and early to rise makes a man healthy, wealthy, and", "wise", "proverb"),
    ("Easy come, easy", "go", "proverb"),
    ("Every rose has its", "thorn", "proverb"),
    ("Familiarity breeds", "contempt", "proverb"),
    ("Fortune favors the", "bold", "proverb"),
    ("Give credit where credit is", "due", "proverb"),
    ("Good things come to those who", "wait", "proverb"),
    ("Great minds think", "alike", "proverb"),
    ("Haste makes", "waste", "proverb"),
    ("Honesty is the best", "policy", "proverb"),
    ("If it ain't broke, don't fix", "it", "proverb"),
    ("Ignorance is", "bliss", "proverb"),
    ("It takes two to", "tango", "proverb"),
    ("Kill two birds with one", "stone", "proverb"),
    ("Knowledge is", "power", "proverb"),
    ("Let sleeping dogs", "lie", "proverb"),
    ("Lightning never strikes the same place", "twice", "proverb"),
    ("Money doesn't grow on", "trees", "proverb"),
    ("No pain, no", "gain", "proverb"),
    ("Old habits die", "hard", "proverb"),
    ("One man's trash is another man's", "treasure", "proverb"),
    ("Patience is a", "virtue", "proverb"),
    ("People who live in glass houses shouldn't throw", "stones", "proverb"),
    ("The apple doesn't fall far from the", "tree", "proverb"),
    ("The best things in life are", "free", "proverb"),
    ("The grass is always greener on the other", "side", "proverb"),
    ("The squeaky wheel gets the", "grease", "proverb"),
    ("There's no place like", "home", "proverb"),
    ("There's no such thing as a free", "lunch", "proverb"),
    ("Too many cooks spoil the", "broth", "proverb"),
    ("Two heads are better than", "one", "proverb"),
    ("Two wrongs don't make a", "right", "proverb"),
    ("United we stand, divided we", "fall", "proverb"),
    ("What goes up must come", "down", "proverb"),
    ("When it rains, it", "pours", "proverb"),
    ("Where there's a will, there's a", "way", "proverb"),
    ("You can lead a horse to water, but you can't make it", "drink", "proverb"),
    ("You can't have your cake and eat it", "too", "proverb"),
    ("You can't teach an old dog new", "tricks", "proverb"),
    ("You reap what you", "sow", "proverb"),
    ("A rolling stone gathers no", "moss", "proverb"),
    ("A stitch in time saves", "nine", "proverb"),
    ("Better safe than", "sorry", "proverb"),
    ("Cleanliness is next to", "godliness", "proverb"),
    ("Don't look a gift horse in the", "mouth", "proverb"),
    ("Half a loaf is better than", "none", "proverb"),
    ("Home is where the heart", "is", "proverb"),
    ("If you can't beat them, join", "them", "proverb"),
    ("It's always darkest before the", "dawn", "proverb"),
    ("Make hay while the sun", "shines", "proverb"),
    ("Misery loves", "company", "proverb"),
    ("Nothing ventured, nothing", "gained", "proverb"),
    ("Opportunity knocks but", "once", "proverb"),
    ("Out of the frying pan and into the", "fire", "proverb"),
    ("Practice what you", "preach", "proverb"),
    ("Seeing is", "believing", "proverb"),
    ("Silence is", "golden", "proverb"),
    ("The proof of the pudding is in the", "eating", "proverb"),
    ("The road to hell is paved with good", "intentions", "proverb"),
    ("There's more than one way to skin a", "cat", "proverb"),
    ("Time is", "money", "proverb"),
    ("Variety is the spice of", "life", "proverb"),
    ("Waste not, want", "not", "proverb"),
    ("When the cat's away, the mice will", "play", "proverb"),
    ("You can't make an omelet without breaking", "eggs", "proverb"),
    ("Beauty is only skin", "deep", "proverb"),
    ("Bad news travels", "fast", "proverb"),
    ("Charity begins at", "home", "proverb"),
    ("Don't throw the baby out with the", "bathwater", "proverb"),
    ("Every man has his", "price", "proverb"),
    ("First come, first", "served", "proverb"),
    ("Forgive and", "forget", "proverb"),
    ("Live and let", "live", "proverb"),
    ("Love is", "blind", "proverb"),
    ("Many hands make light", "work", "proverb"),
    ("Monkey see, monkey", "do", "proverb"),
    ("Never say", "never", "proverb"),
    ("No news is good", "news", "proverb"),
    ("Once bitten, twice", "shy", "proverb"),
    ("One good turn deserves", "another", "proverb"),
    ("Revenge is a dish best served", "cold", "proverb"),
    ("Still waters run", "deep", "proverb"),
    ("The customer is always", "right", "proverb"),
    ("The end justifies the", "means", "proverb"),
    ("The more, the", "merrier", "proverb"),
    ("There's no time like the", "present", "proverb"),
    ("Third time's the", "charm", "proverb"),
    ("Tomorrow is another", "day", "proverb"),
    ("Truth is stranger than", "fiction", "proverb"),
    ("What's done is", "done", "proverb"),
    ("You win some, you lose", "some", "proverb"),
    ("A leopard can't change its", "spots", "proverb"),
    ("A penny for your", "thoughts", "proverb"),
    ("Don't burn your", "bridges", "proverb"),
    ("Don't put off until tomorrow what you can do", "today", "proverb"),
    ("Every little bit", "helps", "proverb"),
    ("Fight fire with", "fire", "proverb"),
    ("Hope for the best, prepare for the", "worst", "proverb"),
    ("If the shoe fits, wear", "it", "proverb"),
    ("It's the thought that", "counts", "proverb"),
    ("Keep your friends close and your enemies", "closer", "proverb"),
    ("Nothing is certain but death and", "taxes", "proverb"),
    ("Rules are made to be", "broken", "proverb"),
    ("Speak of the", "devil", "proverb"),
    ("The bigger they are, the harder they", "fall", "proverb"),
    ("Time heals all", "wounds", "proverb"),
    ("What doesn't kill you makes you", "stronger", "proverb"),
    ("You only live", "once", "proverb"),
    ("Look on the bright", "side", "proverb"),
    ("Sticks and stones may break my", "bones", "proverb"),
    # idioms
    ("Break a", "leg", "idiom"),
    ("It's a piece of", "cake", "idiom"),
    ("Once in a blue", "moon", "idiom"),
    ("Bite the", "bullet", "idiom"),
    ("Hit the nail on the", "head", "idiom"),
    ("Let the cat out of the", "bag", "idiom"),
    ("Spill the", "beans", "idiom"),
    ("Feeling under the", "weather", "idiom"),
    ("It costs an arm and a", "leg", "idiom"),
    ("The ball is in your", "court", "idiom"),
    ("Barking up the wrong", "tree", "idiom"),
    ("Stop beating around the", "bush", "idiom"),
    ("Burning the midnight", "oil", "idiom"),
    ("Don't cry", "wolf", "idiom"),
    ("Time to hit the", "sack", "idiom"),
    ("Jump on the", "bandwagon", "idiom"),
    ("Don't miss the", "boat", "idiom"),
    ("Stop pulling my", "leg", "idiom"),
    ("Throw in the", "towel", "idiom"),
    ("Back to the drawing", "board", "idiom"),
    ("A wild goose", "chase", "idiom"),
    ("Skating on thin", "ice", "idiom"),
    ("Sitting on the", "fence", "idiom"),
    ("Just the tip of the", "iceberg", "idiom"),
    ("The elephant in the", "room", "idiom"),
    ("A drop in the", "bucket", "idiom"),
    ("Adding insult to", "injury", "idiom"),
    ("The best of both", "worlds", "idiom"),
    ("Back to square", "one", "idiom"),
    ("We are all in the same", "boat", "idiom"),
    ("She was over the", "moon", "idiom"),
    ("Only time will", "tell", "idiom"),
    # nursery rhymes (public domain)
    ("Hickory dickory", "dock", "rhyme"),
    ("Baa, baa, black", "sheep", "rhyme"),
    ("Little Miss Muffet sat on a", "tuffet", "rhyme"),
    ("Hey diddle diddle, the cat and the", "fiddle", "rhyme"),
    ("Row, row, row your", "boat", "rhyme"),
    ("London Bridge is falling", "down", "rhyme"),
    ("Pat-a-cake, pat-a-cake, baker's", "man", "rhyme"),
    ("Jack be nimble, Jack be", "quick", "rhyme"),
    ("Little Bo Peep has lost her", "sheep", "rhyme"),
    ("One, two, buckle my", "shoe", "rhyme"),
    ("The itsy bitsy spider climbed up the water", "spout", "rhyme"),
    ("Old Mother Hubbard went to the", "cupboard", "rhyme"),
    ("Three blind", "mice", "rhyme"),
    ("Pease porridge", "hot", "rhyme"),
    ("Roses are red, violets are", "blue", "rhyme"),
    ("Finders keepers, losers", "weepers", "rhyme"),
    ("Ready or not, here I", "come", "rhyme"),
    # public-domain quotes
    ("To be or not to", "be", "quote"),
    ("All the world's a", "stage", "quote"),
    ("Et tu,", "Brute", "quote"),
    ("I came, I saw, I", "conquered", "quote"),
    ("I think, therefore I", "am", "quote"),
    ("Give me liberty, or give me", "death", "quote"),
    ("A house divided against itself cannot", "stand", "quote"),
    ("Four score and seven years", "ago", "quote"),
    ("Ask not what your country can do for", "you", "quote"),
    ("The only thing we have to fear is fear", "itself", "quote"),
    # set phrases
    ("Ladies and", "gentlemen", "phrase"),
    ("Rise and", "shine", "phrase"),
    ("Safe and", "sound", "phrase"),
    ("Salt and", "pepper", "phrase"),
    ("Bread and", "butter", "phrase"),
    ("Peanut butter and", "jelly", "phrase"),
    ("Rock and", "roll", "phrase"),
    ("Trick or", "treat", "phrase"),
    ("Happy birthday to", "you", "phrase"),
    ("Once upon a", "time", "phrase"),
    ("Thank you very", "much", "phrase"),
    ("Good night, sleep", "tight", "phrase"),
    ("Ready, set,", "go", "phrase"),
    ("See you", "later", "phrase"),
]

TARGETS = (
    "spoon",
    "window",
    "pillow",
    "ladder",
    "rocket",
    "banana",
    "carpet",
    "violin",
    "tunnel",
    "pencil",
    "garden",
    "mirror",
    "kettle",
    "jacket",
    "planet",
    "basket",
    "candle",
    "hammer",
    "island",
    "turtle",
    "button",
    "castle",
    "feather",
    "lemon",
    "orange",
    "piano",
    "saddle",
    "tomato",
    "wagon",
    "zipper",
    "anchor",
    "blanket",
    "cactus",
    "donkey",
    "engine",
    "forest",
    "goblet",
    "helmet",
    "igloo",
    "jigsaw",
)

TEMPLATES: dict[str, tuple[str, str]] = {
    "final_word": (
        "Complete the saying so that its final word is '{t}': {p}",
        "Complete the saying: {p}",
    ),
    "fill_blank": (
        "Fill in the blank with the word '{t}': {p} ___",
        "Fill in the blank: {p} ___",
    ),
    "make_last": (
        "Finish this phrase, but make the last word '{t}': {p}",
        "Finish this phrase: {p}",
    ),
    "instead_of": (
        "Write the next word, using '{t}' instead of the usual word: {p}",
        "Write the next word: {p}",
    ),
    "this_version": (
        "In this version of the saying, the last word is '{t}'. Complete it: {p}",
        "Complete the saying: {p}",
    ),
}

FORBIDDEN = ("race", "dead cat", "28 days", "bat and", "widget", "nickel", "lily")


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.casefold()).strip("_")[:32]


def _used_prefixes() -> set[str]:
    used = set()
    for name in ("kanghun_traps_v2", "kanghun_traps_v3"):
        path = DATA / f"{name}.json"
        if not path.exists():
            continue
        for case in json.loads(path.read_text(encoding="utf-8"))["cases"]:
            if case.get("family") == "memo_override":
                used.add(case["control_question"].split(":", 1)[-1].strip().casefold())
    return used


def _target(index: int, memo: str, prefix: str) -> str:
    for step in range(len(TARGETS)):
        word = TARGETS[(index * 7 + step) % len(TARGETS)]
        a, b = word.casefold(), memo.casefold()
        if a == b or a.startswith(b) or b.startswith(a) or a in prefix.casefold():
            continue
        return word
    raise ValueError(f"no target for {memo!r}")


def build_cases() -> list[dict[str, Any]]:
    used = _used_prefixes()
    names = list(TEMPLATES)
    cases, seen = [], set()
    kept = [s for s in SAYINGS if s[0].casefold() not in used]
    for index, (prefix, memo, kind) in enumerate(kept):
        template = names[index % len(names)]
        trap, control = TEMPLATES[template]
        target = _target(index, memo, prefix)
        pair_id = _slug(f"{prefix.split()[-1]}_{memo}_{index}")
        if pair_id in seen:
            raise ValueError(f"duplicate pair id {pair_id}")
        seen.add(pair_id)
        cases.append(
            {
                "case_id": f"{DATASET_ID}_{pair_id}",
                "pair_id": pair_id,
                "template_id": template,
                "condition": "trap",
                "family": FAMILY,
                "question": trap.format(t=target, p=prefix),
                "correct_answer": target,
                "lure_answer": memo,
                "control_question": control.format(p=prefix),
                "note": f"[{kind}] memorised ending '{memo}', instructed '{target}'",
            }
        )
    return cases


def check(cases: list[dict[str, Any]]) -> None:
    for case in cases:
        cid = case["case_id"]
        correct, lure = case["correct_answer"].casefold(), case["lure_answer"].casefold()
        if correct == lure or correct.startswith(lure) or lure.startswith(correct):
            raise ValueError(f"{cid}: answers identical or one is a prefix of the other")
        text = (case["question"] + " " + case["control_question"]).casefold()
        for proto in FORBIDDEN:
            if re.search(rf"\b{re.escape(proto)}", text):
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
        "title": "MindScopeX Large-Model Traps v7 (memorised-phrase override at scale)",
        "description": (
            "Memorised-phrase override pairs over proverbs, idioms, set phrases and "
            "public-domain rhymes and quotes, five instruction frames rotated. Controls drop "
            "the instruction so the memorised word is correct. LLM-assisted, committed before "
            "any screening."
        ),
        "task_kind": "reasoning_lure",
        "scoring": "logprob_margin",
        "source": {
            "authors": "Lee Kanghun (MindScopeX), LLM-assisted",
            "year": 2026,
            "title": "Large-model traps v7",
            "venue": "Repository-authored set, not previously published",
            "doi": "",
            "project_url": "",
        },
        "generated_by": "scripts/build_kanghun_traps_v7.py",
        "n_cases": len(cases),
        "family_counts": {FAMILY: len(cases)},
        "template_counts": dict(sorted(templates.items())),
        "cases": cases,
    }
    path = DATA / f"{DATASET_ID}.json"
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"{path}  n={len(cases)}  {templates}")


if __name__ == "__main__":
    main()
