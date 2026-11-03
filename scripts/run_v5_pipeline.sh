#!/usr/bin/env bash
# One unattended pass: screen the v5 families on 27B, pick the items 27B falls for,
# then test the thinking direction on them (run 50). Every step commits and pushes,
# pulling first so a push from another machine never blocks the upload.
#
#   setsid nohup bash scripts/run_v5_pipeline.sh > /content/v5.log 2>&1 < /dev/null &
set -u
cd "$(dirname "$0")/.."
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
git config user.name "이강훈"
git config user.email "kanghun@sk.com"

push() {
  flock /tmp/mindscopex_git.lock bash -c '
    git add runs_shared src/mindscopex_analysis/data/kanghun_lure27b_v2.json 2>/dev/null
    git commit -qm "$1" || true
    git pull --rebase --autostash -q || git rebase --abort
    git push -q && echo "  pushed: $1" || echo "  push failed: $1 (results kept on this VM)"
  ' _ "$1"
}

stamp() { date -u +%m/%d\ %H:%M; }

echo "=== $(stamp) 1/3 screen v5"
python experiments/jobs/crt_text_responses.py \
  --config experiments/configs/05_kanghun_traps_v5_27b.toml --output-root runs_shared \
  || echo "=== screen exited with an error (partial results kept)"
push "05_kanghun_traps_v5_27b screen"

echo "=== $(stamp) 2/3 select lure27b_v2"
python scripts/build_kanghun_lure27b_v2.py \
  --screen runs_shared/05_kanghun_traps_v5_27b/responses.json || exit 1
push "kanghun_lure27b_v2 from the v5 screen"
N=$(python -c "import json;print(json.load(open('src/mindscopex_analysis/data/kanghun_lure27b_v2.json'))['n_cases'])")
if [ "$N" -lt 2 ]; then
  echo "=== only $N item(s) passed; skipping run 50"
  exit 0
fi

echo "=== $(stamp) 3/3 run 50 on $N items"
python experiments/jobs/thinking_direction.py \
  --config experiments/configs/50_lure27b_v2_direction.toml --output-root runs_shared
push "50_lure27b_v2_direction results"
echo "=== $(stamp) PIPELINE FINISHED"
