# Copyright 2026 MindScopeX
"""Write control traces.json files for the thinking-suppresses-the-feature claim.

Run 43 found L55 #65825 at ~13 where the no-thinking answer is emitted and at 0 at
the end of every completed thinking trace. Two alternatives explain that without
the reasoning doing anything:

* **format** -- any text after ``<think>`` keeps the feature off;
* **copying** -- 27B writes "Final decision: <answer>" before ``</think>``, so the
  answer position just repeats a word it has already produced.

Each variant keeps run 43's no-thinking traces and replaces the thinking trace,
then ``reasoning_trajectory`` reads it with ``reuse_traces`` (no generation):

``filler``  ``<think>\\nOkay.\\n</think>`` -- the format with no content
``cut25``   the first 25% of the real reasoning, closed early -- before any
            decision is written down
``cut50``   the first 50%, same

Cuts land on a line break so no word is split. Thinking traces that never closed
in run 43 are cut the same way from what was generated.

Run::

    python scripts/make_variant_traces.py
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "runs_shared" / "43_lure27b_trajectory_long" / "traces.json"
VARIANTS = {
    "44_lure27b_traj_filler": ("filler", None),
    "45_lure27b_traj_cut25": ("cut", 0.25),
    "46_lure27b_traj_cut50": ("cut", 0.50),
}


def reasoning_body(raw_text: str) -> str:
    body = raw_text.split("<think>", 1)[-1]
    return body.split("</think>", 1)[0].strip("\n")


def cut_at_line(text: str, fraction: float) -> str:
    target = int(len(text) * fraction)
    head = text[:target]
    newline = head.rfind("\n")
    return head[:newline] if newline > 0 else head


def main() -> None:
    traces = json.loads(SOURCE.read_text(encoding="utf-8"))
    for run_name, (kind, fraction) in VARIANTS.items():
        out = []
        for trace in traces:
            if not trace["thinking"]:
                out.append(trace)
                continue
            if kind == "filler":
                body = "Okay."
            else:
                body = cut_at_line(reasoning_body(trace["raw_text"]), float(fraction))
            raw = f"<think>\n{body}\n</think>\n\n"
            out.append(
                {
                    **trace,
                    "raw_text": raw,
                    "answer": "",
                    "answer_label": "other",
                    "output_tokens": 0,
                    "has_thinking_block": True,
                    "variant": run_name,
                }
            )
        run_dir = ROOT / "runs_shared" / run_name
        run_dir.mkdir(parents=True, exist_ok=True)
        (run_dir / "traces.json").write_text(
            json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        lengths = [len(t["raw_text"]) for t in out if t["thinking"]]
        print(f"{run_name}: {len(out)} traces, thinking text {min(lengths)}-{max(lengths)} chars")


if __name__ == "__main__":
    main()
