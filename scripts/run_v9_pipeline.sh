#!/usr/bin/env bash
# Screen the four literature-picked families (v9) two-stage, after the scale
# pipeline has finished (waits for it, so both can be launched together).
#
#   setsid nohup bash scripts/run_v9_pipeline.sh > /content/v9.log 2>&1 < /dev/null &
set -u
cd "$(dirname "$0")/.."
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
while pgrep -f run_scale_pipeline.sh >/dev/null; do sleep 60; done
git config user.name "이강훈"
git config user.email "kanghun@sk.com"

push() {
  flock /tmp/mindscopex_git.lock bash -c '
    git add runs_shared src/mindscopex_analysis/data/kanghun_traps_v9s2.json \
      src/mindscopex_analysis/data/kanghun_lure27b_new.json 2>/dev/null
    git commit -qm "$1" || true
    git pull --rebase --autostash -q || git rebase --abort
    git push -q && echo "  pushed: $1" || echo "  push failed: $1 (results kept on this VM)"
  ' _ "$1"
}
stamp() { date -u +%m/%d\ %H:%M; }
run() { python experiments/jobs/crt_text_responses.py --config "experiments/configs/$1.toml" \
          --output-root runs_shared || echo "=== $1 exited with an error (partial results kept)"; }

echo "=== $(stamp) v9 stage 1: thinking off"
run 09_kanghun_traps_v9_27b_off
python scripts/two_stage_screen.py subset --source kanghun_traps_v9 \
  --stage1 runs_shared/09_kanghun_traps_v9_27b_off/responses.json
push "v9 stage 1 (thinking off)"

echo "=== $(stamp) v9 stage 2: thinking on"
run 09b_kanghun_traps_v9_27b_on
python scripts/two_stage_screen.py select --source kanghun_traps_v9 \
  --stage1 runs_shared/09_kanghun_traps_v9_27b_off/responses.json \
  --stage2 runs_shared/09b_kanghun_traps_v9_27b_on/responses.json \
  --dataset-id kanghun_lure27b_new
push "kanghun_lure27b_new (v9, two-stage screened)"
echo "=== $(stamp) V9 PIPELINE FINISHED"
