"""Can thinking-off reach thinking-on with an edit at the answer slot? (27B, lure27b)

동준's target: a feature that, steered with thinking OFF, gives the thinking-ON answer.
Run 41 got there partly (L55 #65825 removed x8: 4/6 held-out traps flipped, random
0/6). That feature was picked for *pushing the lure*. This job instead measures what
thinking actually changes at the answer slot and tries to put that change into OFF.

Three stages, one model load, all on the same chat-format protocol run 43 used
(instructed prompt, no system prompt, greedy). Margins are ``lure - correct`` summed
over the answer tokens, so positive = the memorised lure is preferred.

a. **Upper bound (patching).** For each item, the residual at the answer slot of the
   thinking-ON context (prompt + run 43's own trace + ``</think>``) is written into
   the thinking-OFF context at the same layer. If no single layer closes the gap,
   nothing at that layer can, and stage c's ceiling is known before it runs.
   ``last``: only the answer-slot token. ``tail``: the aligned ``</think>\\n\\n`` tokens
   that both contexts end with.

b. **Decomposition.** ON minus OFF at the answer slot, encoded with the layer's SAE.
   Features are ranked on the *train* split only; held-out items never pick a
   feature. The SAE's own reconstruction of the difference is reported, because a
   ranking over features that explain little of the difference says little.

c. **Steering, thinking off.** Held-out traps and their matched controls, at the
   answer slot only:

   - ``diffmean`` alpha x the train-mean (ON - OFF) residual -- SAE-free, so it is the
     version that can be repeated on models without an SAE;
   - ``sae_topN`` the N train-ranked features set to their train-mean ON value;
   - ``remove_pinned`` run 41's feature removed k x (the reference point);
   - ``random`` matched-norm random directions at the strongest diffmean dose.

   Gap closure per item is (OFF - edited) / (OFF - ON) on its own ON margin, which
   the item never contributed to choosing the edit.

Traces with no ``</think>`` (3 of 18 hit the 6000-token cap in run 43) are closed by
force and flagged ``on_completed = false``; summaries report completed-only.

Run::

    python experiments/jobs/thinking_patch.py \\
        --config experiments/configs/48_lure27b_thinking_patch.toml --output-root runs_shared
"""
# ruff: noqa: E402

from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import replace
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
for _path in (ROOT, ROOT / "src"):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

_THINK_OPEN = "<think>\n"
_THINK_CLOSE = "</think>"


def _log(message: str) -> None:
    print(f"[patch] {message}", flush=True)


# ===================================================================== pure logic
# Everything in this block is torch-free so it can be unit tested without a GPU.


def gap_closure(off: float, edited: float, on: float, *, min_gap: float = 0.5) -> float | None:
    """Fraction of the OFF->ON margin gap an edit recovers; None if there is no gap.

    1.0 means the edited OFF margin equals the ON margin, 0.0 means no change, and
    values above 1 overshoot. ``min_gap`` (nats) keeps items where thinking barely
    moved the margin from producing huge ratios out of noise.
    """

    gap = float(off) - float(on)
    if gap < min_gap:
        return None
    return (float(off) - float(edited)) / gap


def body_until_close(trace_text: str) -> tuple[str, bool]:
    """The reasoning text after ``<think>\\n`` up to and including ``</think>``.

    Run 43's ``raw_text`` starts with the ``<think>\\n`` that the ON chat template
    already puts in the prompt, so it is stripped. A trace that never closed is
    returned whole with the close tag appended and ``completed = False``.
    """

    text = trace_text[len(_THINK_OPEN) :] if trace_text.startswith(_THINK_OPEN) else trace_text
    index = text.find(_THINK_CLOSE)
    if index < 0:
        text = text.replace("<|im_end|>", "").rstrip()
        return text + "\n" + _THINK_CLOSE, False
    return text[: index + len(_THINK_CLOSE)], True


def tail_after_close(off_ids: Sequence[int], close_ids: Sequence[int]) -> list[int] | None:
    """Tokens the thinking-OFF prompt carries after its (empty) ``</think>``.

    The OFF template ends ``<think>\\n\\n</think>\\n\\n``; the same tail is appended to
    the ON context so the answer slot is the same token in both. None if the OFF
    prompt has no ``</think>`` (a template without the empty block).
    """

    off, close = list(off_ids), list(close_ids)
    if not close:
        return None
    for start in range(len(off) - len(close), -1, -1):
        if off[start : start + len(close)] == close:
            return off[start + len(close) :]
    return None


def rank_difference_features(
    off_codes: Sequence[Mapping[int, float]],
    on_codes: Sequence[Mapping[int, float]],
    *,
    top_n: int,
) -> list[dict[str, Any]]:
    """Features ranked by |mean(ON - OFF)| over paired items (absent = 0).

    ``sign_agreement`` is the fraction of items whose own difference has the sign of
    the mean, so a feature carried by one item with a huge value is visible as such.
    """

    if len(off_codes) != len(on_codes):
        raise ValueError("off_codes and on_codes must be paired")
    n = len(off_codes)
    if n == 0:
        return []
    ids = set()
    for codes in (*off_codes, *on_codes):
        ids.update(int(k) for k in codes)
    rows = []
    for fid in ids:
        offs = [float(c.get(fid, 0.0)) for c in off_codes]
        ons = [float(c.get(fid, 0.0)) for c in on_codes]
        diffs = [b - a for a, b in zip(offs, ons, strict=True)]
        mean = sum(diffs) / n
        if mean == 0.0:
            continue
        agree = sum(1 for d in diffs if d != 0.0 and (d > 0) == (mean > 0)) / n
        rows.append(
            {
                "feature_id": fid,
                "mean_diff": mean,
                "mean_off": sum(offs) / n,
                "mean_on": sum(ons) / n,
                "sign_agreement": agree,
                "n_items": n,
                "direction": "up_in_on" if mean > 0 else "down_in_on",
            }
        )
    rows.sort(key=lambda r: (-abs(r["mean_diff"]), r["feature_id"]))
    for rank, row in enumerate(rows[: int(top_n)], start=1):
        row["rank"] = rank
    return rows[: int(top_n)]


def summarise(
    rows: Sequence[Mapping[str, Any]], keys: Sequence[str], *, completed_only: bool = True
) -> list[dict[str, Any]]:
    """Group rows by ``keys``: n, correct count, mean margin, mean gap closure.

    ``completed_only`` drops items whose ON trace never closed, for the gap columns
    only -- correct counts use every row, because the OFF-side answer does not
    depend on the ON trace.
    """

    groups: dict[tuple[Any, ...], list[Mapping[str, Any]]] = {}
    for row in rows:
        groups.setdefault(tuple(row[k] for k in keys), []).append(row)
    out = []
    for key in sorted(groups, key=lambda k: tuple(str(x) for x in k)):
        group = groups[key]
        gaps = [
            float(r["gap_closure"])
            for r in group
            if r.get("gap_closure") not in (None, "")
            and (not completed_only or bool(r.get("on_completed", True)))
        ]
        margins = [float(r["margin"]) for r in group if r.get("margin") not in (None, "")]
        out.append(
            {
                **dict(zip(keys, key, strict=True)),
                "n": len(group),
                "correct": sum(1 for r in group if r.get("label") == "correct"),
                "mean_margin": sum(margins) / len(margins) if margins else None,
                "n_gap": len(gaps),
                "mean_gap_closure": sum(gaps) / len(gaps) if gaps else None,
                "median_gap_closure": sorted(gaps)[len(gaps) // 2] if gaps else None,
            }
        )
    return out


def _write_csv(path: Path, rows: Sequence[Mapping[str, Any]]) -> None:
    if not rows:
        return
    columns: list[str] = []
    for row in rows:
        for key in row:
            if key not in columns:
                columns.append(key)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({c: row.get(c, "") for c in columns})


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str), "utf-8")


# ===================================================================== model side


def _torch():
    import torch

    return torch


class _EditHook:
    """Forward hook editing the residual at fixed absolute positions.

    Applied only on a forward that covers those positions -- the full-context pass.
    Incremental decoding steps (length 1, positions beyond the context) are left
    alone; their cache already holds the edited upstream states.
    """

    def __init__(self, positions: Sequence[int], edit: Callable[[Any, int], Any]) -> None:
        self.positions = [int(p) for p in positions]
        self.edit = edit

    def __call__(self, _module: Any, _inputs: Any, output: Any) -> Any:
        hidden = output[0] if isinstance(output, tuple) else output
        if hidden.shape[1] <= max(self.positions):
            return output
        hidden = hidden.clone()
        for slot, position in enumerate(self.positions):
            hidden[0, position] = self.edit(hidden[0, position], slot).to(hidden.dtype)
        if isinstance(output, tuple):
            return (hidden, *output[1:])
        return hidden


class _Capture:
    def __init__(self, n_last: int) -> None:
        self.n_last = int(n_last)
        self.value: Any = None

    def __call__(self, _module: Any, _inputs: Any, output: Any) -> None:
        hidden = output[0] if isinstance(output, tuple) else output
        self.value = hidden[0, -self.n_last :].detach().float().cpu()


class Runner:
    """Model, tokenizer and hook plumbing shared by the three stages."""

    def __init__(self, hf_model: Any, tokenizer: Any, block_path_template: str) -> None:
        from mindscopex_analysis.generation import _input_device
        from mindscopex_analysis.research import find_decoder_block

        self.model = hf_model
        self.tokenizer = tokenizer
        self.text_tok = getattr(tokenizer, "tokenizer", tokenizer)
        self.device = _input_device(hf_model)
        self._blocks: dict[int, Any] = {}
        self._find = lambda layer: find_decoder_block(
            hf_model, layer, block_path_template=block_path_template
        )
        self.close_ids = list(self.text_tok.encode(_THINK_CLOSE, add_special_tokens=False))

    def block(self, layer: int) -> Any:
        if layer not in self._blocks:
            self._blocks[layer] = self._find(int(layer))
        return self._blocks[layer]

    # ---- contexts
    def prompt_ids(self, prompt: str, *, thinking: bool) -> list[int]:
        from mindscopex_analysis.generation import _prepare_inputs

        inputs = _prepare_inputs(
            self.tokenizer,
            prompt,
            system_prompt="",
            enable_thinking=thinking,
            use_chat_template=True,
        )
        return [int(t) for t in inputs["input_ids"][0].tolist()]

    def on_context(
        self, prompt: str, trace_text: str, tail: Sequence[int]
    ) -> tuple[list[int], bool]:
        ids = self.prompt_ids(prompt, thinking=True)
        # Run 43 prepended "<think>\n" only when the template had already put it in the
        # prompt. If this template does not end with it, the tag was generated and
        # must stay in the body.
        prompt_end = self.text_tok.decode(ids[-4:], skip_special_tokens=False)
        text = trace_text
        if not prompt_end.endswith(_THINK_OPEN) and not text.startswith(_THINK_OPEN):
            text = _THINK_OPEN + text
        body, completed = body_until_close(text)
        if not prompt_end.endswith(_THINK_OPEN):
            body = _THINK_OPEN + body
        ids += list(self.text_tok.encode(body, add_special_tokens=False)) + list(tail)
        return ids, completed

    def answer_ids(self, answer: str) -> list[int]:
        return list(self.text_tok.encode(answer.strip(), add_special_tokens=False))

    # ---- forwards
    def _forward(self, ids: Sequence[int], keep: int) -> Any:
        torch = _torch()
        tensor = torch.tensor([list(ids)], device=self.device)
        with torch.inference_mode():
            try:
                out = self.model(input_ids=tensor, use_cache=False, logits_to_keep=int(keep))
            except TypeError:
                out = self.model(input_ids=tensor, use_cache=False)
        return out.logits[0, -int(keep) :].float()

    def capture(self, ids: Sequence[int], layers: Sequence[int], n_last: int) -> dict[int, Any]:
        caps = {layer: _Capture(n_last) for layer in layers}
        handles = [self.block(layer).register_forward_hook(caps[layer]) for layer in layers]
        try:
            self._forward(ids, keep=1)
        finally:
            for handle in handles:
                handle.remove()
        return {layer: cap.value for layer, cap in caps.items()}

    def margin(
        self, ctx: Sequence[int], correct: Sequence[int], lure: Sequence[int], hooks=()
    ) -> float:
        """``logp(lure) - logp(correct)``, each summed over its answer tokens."""

        torch = _torch()
        handles = [self.block(layer).register_forward_hook(hook) for layer, hook in hooks]
        try:
            scores = []
            for answer in (correct, lure):
                logits = self._forward(list(ctx) + list(answer), keep=len(answer) + 1)[:-1]
                logp = torch.log_softmax(logits, dim=-1)
                target = torch.tensor(list(answer), device=logp.device)
                scores.append(float(logp.gather(1, target[:, None]).sum()))
        finally:
            for handle in handles:
                handle.remove()
        return scores[1] - scores[0]

    def choose(
        self, ctx: Sequence[int], correct: Sequence[int], lure: Sequence[int], hooks=()
    ) -> str:
        """The screen's forced choice (greedy, prefix-constrained) on ``ctx``."""

        from mindscopex_analysis.generation import _constrained_answer_ids

        torch = _torch()
        handles = [self.block(layer).register_forward_hook(hook) for layer, hook in hooks]
        try:
            chosen = _constrained_answer_ids(
                self.model,
                self.text_tok,
                torch.tensor([list(ctx)], device=self.device),
                [list(correct), list(lure)],
                max_answer_tokens=24,
            )
        finally:
            for handle in handles:
                handle.remove()
        if chosen == list(correct):
            return "correct"
        if chosen == list(lure):
            return "lure"
        return "other"


# --------------------------------------------------------------------- edits


def _patch_edit(targets: Any) -> Callable[[Any, int], Any]:
    return lambda _h, slot: targets[slot].to(_h.device)


def _add_edit(vector: Any) -> Callable[[Any, int], Any]:
    return lambda h, _slot: h + vector.to(device=h.device, dtype=h.dtype)


def _sae_set_edit(sae: Any, feature_ids: Sequence[int], targets: Sequence[float]):
    """Move the listed features to target activations: h += sum (t - a) d."""

    from mindscopex_analysis.qwen_scope import (
        qwen_scope_sparse_feature_values,
        sae_decoder_direction,
    )

    torch = _torch()
    dirs = torch.stack([sae_decoder_direction(sae, [int(f)]) for f in feature_ids]).float().cpu()
    target = torch.tensor([float(t) for t in targets])

    def edit(h: Any, _slot: int) -> Any:
        x = h.detach().to(device=sae.W_enc.device, dtype=sae.W_enc.dtype)[None]
        current = qwen_scope_sparse_feature_values(x, sae, list(feature_ids))[0].float().cpu()
        delta = ((target - current)[:, None] * dirs).sum(0)
        return h + delta.to(device=h.device, dtype=h.dtype)

    return edit


def _remove_edit(sae: Any, feature_id: int, k: float):
    from mindscopex_analysis.qwen_scope import (
        qwen_scope_sparse_feature_values,
        sae_decoder_direction,
    )

    direction = sae_decoder_direction(sae, [int(feature_id)]).float()

    def edit(h: Any, _slot: int) -> Any:
        x = h.detach().to(device=sae.W_enc.device, dtype=sae.W_enc.dtype)[None]
        value = float(qwen_scope_sparse_feature_values(x, sae, [int(feature_id)])[0, 0])
        return h - (float(k) * value * direction).to(device=h.device, dtype=h.dtype)

    return edit


def _sae_codes(sae: Any, vector: Any) -> dict[int, float]:
    from mindscopex_analysis.qwen_scope import encode_qwen_scope_topk

    values, indices = encode_qwen_scope_topk(vector[None], sae)
    return {int(i): float(v) for v, i in zip(values[0].tolist(), indices[0].tolist(), strict=True)}


def _sae_decode(sae: Any, codes: Mapping[int, float]) -> Any:
    from mindscopex_analysis.qwen_scope import sae_decoder_direction

    ids = list(codes)
    return sae_decoder_direction(sae, ids, [codes[i] for i in ids]).float().cpu()


# ===================================================================== the run


def _as_control(case: Any) -> Any:
    """Matched control with answers swapped: ``correct`` = the memorised word."""

    return replace(
        case,
        case_id=f"{case.case_id}__control",
        prompt=case.control_prompt,
        correct_answer=case.lure_answer,
        lure_answer=case.correct_answer,
        control_prompt="",
    )


def run(config_path: Path, output_root: Path) -> Path:
    torch = _torch()
    from experiments.jobs.research_experiments import _load_sae, _load_splits, _resolve_env
    from experiments.runners.config import load_toml, run_name, table
    from mindscopex_analysis.models import load_qwen_language_model

    config = load_toml(config_path)
    run_dir = output_root / run_name(config)
    run_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(config_path, run_dir / "config.toml")

    pcfg, dcfg, scfg = table(config, "patch"), table(config, "decompose"), table(config, "steer")
    tcfg = table(config, "thinking")
    patch_layers = [int(x) for x in pcfg.get("layers", [15, 31, 47, 55, 63])]
    sae_layers = [int(x) for x in dcfg.get("layers", [55])]
    top_n_rank = int(dcfg.get("top_n", 64))
    steer_layers = [int(x) for x in scfg.get("layers", [55])]
    alphas = [float(x) for x in scfg.get("diffmean_alphas", [0.5, 1.0, 2.0])]
    sae_ns = [int(x) for x in scfg.get("sae_top_n", [1, 4, 16, 64])]
    pinned = table(config, "pinned")
    pinned_layer, pinned_fid = int(pinned.get("layer", 55)), int(pinned.get("feature_id", 65825))
    pinned_ks = [float(x) for x in pinned.get("coefficients", [1, 8])]
    random_seeds = [int(x) for x in scfg.get("random_seeds", [101, 102, 103])]
    min_gap = float(scfg.get("min_gap", 0.5))

    env = _resolve_env(config)
    splits = _load_splits(config)
    membership = {c.case_id: "held_out" for c in splits["test"]}
    membership.update({c.case_id: "train" for c in splits["train"]})
    cases = sorted(splits["all"], key=lambda c: c.case_id)

    traces_path = ROOT / str(
        tcfg.get("traces", "runs_shared/43_lure27b_trajectory_long/traces.json")
    )
    traces = {
        t["case_id"]: t
        for t in json.loads(traces_path.read_text(encoding="utf-8"))
        if bool(t["thinking"])
    }

    started = time.time()
    _log(f"loading {env['model_id']}")
    load_kwargs: dict[str, Any] = {}
    if env.get("max_memory"):
        load_kwargs["max_memory"] = env["max_memory"]
    lm = load_qwen_language_model(
        env["model_id"], device_map=env["device_map"], dtype=env["dtype"], **load_kwargs
    )
    runner = Runner(getattr(lm, "_model", lm), lm.tokenizer, env["profile"].block_path_template)
    saes = {layer: _load_sae(env, layer) for layer in sorted(set(sae_layers + [pinned_layer]))}
    _log(f"[{time.time() - started:5.0f}s] model + SAE layers {sorted(saes)} ready")

    # ------------------------------------------------------- contexts + captures
    all_layers = sorted(set(patch_layers + sae_layers + steer_layers))
    items: list[dict[str, Any]] = []
    for case in cases:
        trace = traces.get(case.case_id)
        off_ids = runner.prompt_ids(case.prompt, thinking=False)
        tail = tail_after_close(off_ids, runner.close_ids)
        if tail is None:
            raise RuntimeError("thinking-off prompt has no </think>; cannot align answer slots")
        n_tail = len(runner.close_ids) + len(tail)
        correct, lure = runner.answer_ids(case.correct_answer), runner.answer_ids(case.lure_answer)
        item: dict[str, Any] = {
            "case": case,
            "split": membership[case.case_id],
            "off_ids": off_ids,
            "n_tail": n_tail,
            "correct": correct,
            "lure": lure,
            "off_cap": runner.capture(off_ids, all_layers, n_tail),
            "off_margin": runner.margin(off_ids, correct, lure),
            "off_label": runner.choose(off_ids, correct, lure),
        }
        if trace is not None:
            on_ids, completed = runner.on_context(case.prompt, trace["raw_text"], tail)
            if on_ids[-n_tail:] != off_ids[-n_tail:]:
                # Patching "tail" assumes both contexts end in the same tokens.
                raise RuntimeError(
                    f"{case.case_id}: ON/OFF answer slots differ "
                    f"({on_ids[-n_tail:]} vs {off_ids[-n_tail:]})"
                )
            item.update(
                on_ids=on_ids,
                on_completed=completed,
                on_cap=runner.capture(on_ids, all_layers, n_tail),
                on_margin=runner.margin(on_ids, correct, lure),
                on_label=runner.choose(on_ids, correct, lure),
                on_tokens=len(on_ids),
            )
        ctl = _as_control(case)
        ctl_ids = runner.prompt_ids(ctl.prompt, thinking=False)
        item.update(
            ctl_ids=ctl_ids,
            ctl_correct=runner.answer_ids(ctl.correct_answer),
            ctl_lure=runner.answer_ids(ctl.lure_answer),
        )
        item["ctl_margin"] = runner.margin(ctl_ids, item["ctl_correct"], item["ctl_lure"])
        item["ctl_label"] = runner.choose(ctl_ids, item["ctl_correct"], item["ctl_lure"])
        items.append(item)
        _log(
            f"{case.case_id[-24:]:24s} {item['split']:8s} off={item['off_margin']:+.2f} "
            f"({item['off_label']}) on={item.get('on_margin', float('nan')):+.2f} "
            f"({item.get('on_label', '-')}) completed={item.get('on_completed', '-')}"
        )
    baseline_rows = [
        {
            "case_id": it["case"].case_id,
            "split": it["split"],
            "off_margin": it["off_margin"],
            "off_label": it["off_label"],
            "on_margin": it.get("on_margin", ""),
            "on_label": it.get("on_label", ""),
            "on_completed": it.get("on_completed", ""),
            "on_tokens": it.get("on_tokens", ""),
            "control_margin": it["ctl_margin"],
            "control_label": it["ctl_label"],
        }
        for it in items
    ]
    _write_csv(run_dir / "baseline.csv", baseline_rows)
    with_on = [it for it in items if "on_ids" in it]

    def row(it: dict[str, Any], margin: float, label: str, **extra: Any) -> dict[str, Any]:
        return {
            "case_id": it["case"].case_id,
            "split": it["split"],
            "on_completed": it.get("on_completed", False),
            "margin": margin,
            "label": label,
            "gap_closure": (
                gap_closure(it["off_margin"], margin, it["on_margin"], min_gap=min_gap)
                if "on_margin" in it
                else None
            ),
            **extra,
        }

    # ------------------------------------------------------------- a. patching
    patch_rows: list[dict[str, Any]] = []
    if bool(pcfg.get("enabled", True)):
        for layer in patch_layers:
            for mode in ("last", "tail"):
                for it in with_on:
                    n = 1 if mode == "last" else it["n_tail"]
                    targets = it["on_cap"][layer][-n:]
                    end = len(it["off_ids"])
                    hook = _EditHook(range(end - n, end), _patch_edit(targets))
                    hooks = [(layer, hook)]
                    m = runner.margin(it["off_ids"], it["correct"], it["lure"], hooks)
                    lab = runner.choose(it["off_ids"], it["correct"], it["lure"], hooks)
                    patch_rows.append(row(it, m, lab, layer=layer, mode=mode))
            _log(f"[{time.time() - started:5.0f}s] patched layer {layer}")
        _write_csv(run_dir / "patch.csv", patch_rows)
        _write_csv(run_dir / "patch_summary.csv", summarise(patch_rows, ["layer", "mode"]))

    # ------------------------------------------------------- b. decomposition
    rankings: dict[int, list[dict[str, Any]]] = {}
    decomp_rows: list[dict[str, Any]] = []
    for layer in sae_layers:
        sae = saes[layer]
        train_off, train_on = [], []
        for it in with_on:
            x_off, x_on = it["off_cap"][layer][-1], it["on_cap"][layer][-1]
            c_off, c_on = _sae_codes(sae, x_off), _sae_codes(sae, x_on)
            raw = x_on - x_off
            rec = _sae_decode(sae, c_on) - _sae_decode(sae, c_off)
            decomp_rows.append(
                {
                    "layer": layer,
                    "case_id": it["case"].case_id,
                    "split": it["split"],
                    "on_completed": it["on_completed"],
                    "diff_norm": float(raw.norm()),
                    "sae_diff_cosine": float(
                        torch.nn.functional.cosine_similarity(raw, rec, dim=0)
                    ),
                    "sae_diff_norm_ratio": float(rec.norm() / raw.norm().clamp_min(1e-6)),
                    "pinned_off": c_off.get(pinned_fid, 0.0) if layer == pinned_layer else "",
                    "pinned_on": c_on.get(pinned_fid, 0.0) if layer == pinned_layer else "",
                }
            )
            if it["split"] == "train" and it["on_completed"]:
                train_off.append(c_off)
                train_on.append(c_on)
        rankings[layer] = rank_difference_features(train_off, train_on, top_n=top_n_rank)
        for r in rankings[layer]:
            r["layer"] = layer
        _log(f"L{layer}: ranked {len(rankings[layer])} features on {len(train_on)} train items")
    _write_csv(run_dir / "decompose_items.csv", decomp_rows)
    _write_csv(
        run_dir / "feature_ranking.csv", [r for layer in sae_layers for r in rankings[layer]]
    )

    # ------------------------------------------------------------- c. steering
    steer_rows: list[dict[str, Any]] = []
    train_done = [it for it in with_on if it["split"] == "train" and it["on_completed"]]
    for layer in steer_layers:
        if not train_done:
            break
        diffmean = torch.stack(
            [it["on_cap"][layer][-1] - it["off_cap"][layer][-1] for it in train_done]
        ).mean(0)
        arms: list[tuple[str, float, Callable[[Any, int], Any]]] = [("none", 0.0, lambda h, _s: h)]
        arms += [("diffmean", a, _add_edit(a * diffmean)) for a in alphas]
        top_alpha = max(alphas) if alphas else 1.0
        for seed in random_seeds:
            gen = torch.Generator().manual_seed(seed)
            rand = torch.randn(diffmean.shape, generator=gen)
            rand = rand / rand.norm() * diffmean.norm() * top_alpha
            arms.append((f"random{seed}", top_alpha, _add_edit(rand)))
        if layer in saes and layer in rankings:
            ranked = rankings[layer]
            for n in sae_ns:
                chosen = ranked[: int(n)]
                if chosen:
                    arms.append(
                        (
                            f"sae_top{n}",
                            float(n),
                            _sae_set_edit(
                                saes[layer],
                                [r["feature_id"] for r in chosen],
                                [r["mean_on"] for r in chosen],
                            ),
                        )
                    )
        if layer == pinned_layer:
            arms += [
                ("remove_pinned", k, _remove_edit(saes[pinned_layer], pinned_fid, k))
                for k in pinned_ks
            ]

        for it in items:
            for kind in ("trap", "control"):
                if kind == "trap":
                    ctx, cor, lur = it["off_ids"], it["correct"], it["lure"]
                else:
                    ctx, cor, lur = it["ctl_ids"], it["ctl_correct"], it["ctl_lure"]
                end = len(ctx)
                for arm, strength, edit in arms:
                    hooks = [] if arm == "none" else [(layer, _EditHook([end - 1], edit))]
                    m = runner.margin(ctx, cor, lur, hooks)
                    lab = runner.choose(ctx, cor, lur, hooks)
                    r = row(it, m, lab, layer=layer, kind=kind, arm=arm, strength=strength)
                    if kind == "control":
                        r["gap_closure"] = None  # no ON reference for controls here
                    steer_rows.append(r)
        _log(f"[{time.time() - started:5.0f}s] steered at layer {layer} ({len(arms)} arms)")
        _write_csv(run_dir / "steer.csv", steer_rows)
    steer_summary = summarise(steer_rows, ["layer", "split", "kind", "arm", "strength"])
    _write_csv(run_dir / "steer_summary.csv", steer_summary)

    manifest = {
        "job": "thinking_patch",
        "model_id": env["model_id"],
        "traces": str(traces_path.relative_to(ROOT)),
        "n_items": len(items),
        "n_with_on": len(with_on),
        "n_on_completed": sum(1 for it in with_on if it["on_completed"]),
        "n_train_completed": len(train_done),
        "split": {k: sum(1 for v in membership.values() if v == k) for k in ("train", "held_out")},
        "patch_layers": patch_layers,
        "sae_layers": sae_layers,
        "steer_layers": steer_layers,
        "min_gap": min_gap,
        "elapsed_seconds": round(time.time() - started, 1),
    }
    _write_json(run_dir / "manifest.json", manifest)

    print("\n== baseline (thinking off / on, chat protocol)")
    print(f"  off correct {sum(it['off_label'] == 'correct' for it in items)}/{len(items)}")
    print(f"  on  correct {sum(it.get('on_label') == 'correct' for it in with_on)}/{len(with_on)}")
    print("\n== a. patch: mean gap closure (completed ON traces)")
    for r in summarise(patch_rows, ["layer", "mode"]):
        print(
            f"  L{r['layer']:<3} {r['mode']:4s} correct={r['correct']}/{r['n']} "
            f"gap={r['mean_gap_closure']}"
        )
    print("\n== c. steer: held-out")
    for r in steer_summary:
        if r["split"] == "held_out":
            print(
                f"  L{r['layer']:<3} {r['kind']:7s} {r['arm']:14s} {r['strength']:<5g} "
                f"correct={r['correct']}/{r['n']} gap={r['mean_gap_closure']}"
            )
    print(f"ARTIFACT_DIR={run_dir}", flush=True)
    return run_dir


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--output-root", default=Path("outputs/experiments"), type=Path)
    args = parser.parse_args()
    run(args.config, args.output_root)


if __name__ == "__main__":
    main()
