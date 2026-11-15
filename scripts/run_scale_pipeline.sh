#!/usr/bin/env bash
# Scale both lure families to ~100 passing items each, two-stage:
#   stage 1  thinking OFF, traps + controls  (fast)   -> keep trap=lure, control=correct
#   stage 2  thinking ON,  survivors' traps   (slow)   -> keep trap=correct
# Memo override (v7) and belief tracking (v8). Every step commits and pushes.
#
#   setsid nohup bash scripts/run_scale_pipeline.sh > /content/scale.log 2>&1 < /dev/null &
set -u
cd "$(dirname "$0")/.."
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
git config user.name "이강훈"
git config user.email "kanghun@sk.com"

push() {
  flock /tmp/mindscopex_git.lock bash -c '
    git add runs_shared src/mindscopex_analysis/data/kanghun_traps_v7s2.json \
      src/mindscopex_analysis/data/kanghun_traps_v8s2.json \
      src/mindscopex_analysis/data/kanghun_lure27b_memo.json \
      src/mindscopex_analysis/data/kanghun_lure27b_belief.json 2>/dev/null
    git commit -qm "$1" || true
    git pull --rebase --autostash -q || git rebase --abort
    git push -q && echo "  pushed: $1" || echo "  push failed: $1 (results kept on this VM)"
  ' _ "$1"
}
stamp() { date -u +%m/%d\ %H:%M; }
run() { python experiments/jobs/crt_text_responses.py --config "experiments/configs/$1.toml" \
          --output-root runs_shared || echo "=== $1 exited with an error (partial results kept)"; }

echo "=== $(stamp) stage 1: thinking off"
run 07_kanghun_traps_v7_27b_off
run 08_kanghun_traps_v8_27b_off
python scripts/two_stage_screen.py subset --source kanghun_traps_v7 \
  --stage1 runs_shared/07_kanghun_traps_v7_27b_off/responses.json
python scripts/two_stage_screen.py subset --source kanghun_traps_v8 \
  --stage1 runs_shared/08_kanghun_traps_v8_27b_off/responses.json
push "stage 1 (thinking off) for v7 memo + v8 belief"

echo "=== $(stamp) stage 2: memo override, thinking on"
run 07b_kanghun_traps_v7_27b_on
python scripts/two_stage_screen.py select --source kanghun_traps_v7 \
  --stage1 runs_shared/07_kanghun_traps_v7_27b_off/responses.json \
  --stage2 runs_shared/07b_kanghun_traps_v7_27b_on/responses.json \
  --dataset-id kanghun_lure27b_memo
push "kanghun_lure27b_memo (two-stage screened)"

echo "=== $(stamp) stage 2: belief tracking, thinking on"
run 08b_kanghun_traps_v8_27b_on
python scripts/two_stage_screen.py select --source kanghun_traps_v8 \
  --stage1 runs_shared/08_kanghun_traps_v8_27b_off/responses.json \
  --stage2 runs_shared/08b_kanghun_traps_v8_27b_on/responses.json \
  --dataset-id kanghun_lure27b_belief
push "kanghun_lure27b_belief (two-stage screened)"
echo "=== $(stamp) PIPELINE FINISHED"
