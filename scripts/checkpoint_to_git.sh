#!/usr/bin/env bash
# Push a run directory to the current branch every few minutes, so a long Colab run
# survives a dropped session or a recycled VM.
#
#   bash scripts/checkpoint_to_git.sh runs_shared/03_kanghun_traps_v3_27b 600
#
# Pair it with crt_text_responses.py --output-root runs_shared: the job writes
# responses.json after every response, this loop commits and pushes it, and a fresh
# clone resumes from the pushed file automatically.
set -u
DEST="${1:?run directory inside the repo}"
INTERVAL="${2:-600}"
cd "$(dirname "$0")/.."
while true; do
  sleep "$INTERVAL"
  [ -d "$DEST" ] || continue
  # flock serializes with run_queue.sh so the two never fight over .git/index.lock
  flock /tmp/mindscopex_git.lock bash -c '
    git add "$1"
    if git -c user.name="이강훈" -c user.email="kanghun@sk.com" \
        commit -qm "Checkpoint $(basename "$1") ($(date -u +%H:%M))"; then
      git push -q && echo "$(date -u +%H:%M) pushed" || echo "$(date -u +%H:%M) push failed"
    fi
  ' _ "$DEST"
done
