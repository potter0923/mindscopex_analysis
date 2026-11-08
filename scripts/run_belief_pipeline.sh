#!/usr/bin/env bash
# Belief tracking end to end: screen v6 on 27B, pool the passing belief items with
# v5's, then run 51 (leave-one-out belief direction, memorised-phrase direction,
# controls, transfer). Every step commits and pushes, pulling first.
#
#   setsid nohup bash scripts/run_belief_pipeline.sh > /content/belief.log 2>&1 < /dev/null &
set -u
cd "$(dirname "$0")/.."
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
git config user.name "이강훈"
git config user.email "kanghun@sk.com"

push() {
  flock /tmp/mindscopex_git.lock bash -c '
    git add runs_shared src/mindscopex_analysis/data/kanghun_lure27b_v3.json 2>/dev/null
    git commit -qm "$1" || true
    git pull --rebase --autostash -q || git rebase --abort
    git push -q && echo "  pushed: $1" || echo "  push failed: $1 (results kept on this VM)"
  ' _ "$1"
}

stamp() { date -u +%m/%d\ %H:%M; }

echo "=== $(stamp) 1/3 screen v6 (belief tracking)"
python experiments/jobs/crt_text_responses.py \
  --config experiments/configs/06_kanghun_traps_v6_27b.toml --output-root runs_shared \
  || echo "=== screen exited with an error (partial results kept)"
push "06_kanghun_traps_v6_27b screen"

echo "=== $(stamp) 2/3 select belief items (v5 + v6) -> kanghun_lure27b_v3"
python scripts/build_kanghun_lure27b_v2.py \
  --screen runs_shared/05_kanghun_traps_v5_27b/responses.json --source kanghun_traps_v5 \
  --screen runs_shared/06_kanghun_traps_v6_27b/responses.json --source kanghun_traps_v6 \
  --dataset-id kanghun_lure27b_v3 --families belief_tracking \
  --traces-out runs_shared/06_kanghun_traps_v6_27b/lure27b_v3_traces.json || exit 1
push "kanghun_lure27b_v3 (belief items from v5 + v6)"
N=$(python -c "import json;print(json.load(open('src/mindscopex_analysis/data/kanghun_lure27b_v3.json'))['n_cases'])")
if [ "$N" -lt 3 ]; then
  echo "=== only $N belief item(s) passed; skipping run 51"
  exit 0
fi

echo "=== $(stamp) 3/3 run 51 on $N belief items"
python experiments/jobs/thinking_direction.py \
  --config experiments/configs/51_lure27b_v3_belief_direction.toml --output-root runs_shared
push "51_lure27b_v3_belief_direction results"
echo "=== $(stamp) PIPELINE FINISHED"
