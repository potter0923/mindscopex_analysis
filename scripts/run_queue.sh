#!/usr/bin/env bash
# Run a queue of crt_text_responses configs back to back, unattended.
#
#   setsid nohup bash scripts/run_queue.sh experiments/queues/overnight_2026_10_24.txt \
#       > /content/queue.log 2>&1 < /dev/null &
#
# * every run writes to runs_shared/<run name>/ and resumes from what is there, so
#   restarting the queue after a dropped session skips finished work;
# * a failed config is logged and skipped, it does not stop the night;
# * after each config the results are committed and pushed, on top of the
#   ten-minute checkpoints from scripts/checkpoint_to_git.sh.
set -u
QUEUE="${1:?queue file}"
cd "$(dirname "$0")/.."

commit_push() {
  # flock serializes with checkpoint_to_git.sh so the two never fight over .git/index.lock
  flock /tmp/mindscopex_git.lock bash -c '
    git add runs_shared
    git -c user.name="이강훈" -c user.email="kanghun@sk.com" commit -qm "$1" \
      && { git push -q && echo "  pushed" || echo "  push failed (results kept on this VM)"; }
  ' _ "$1"
}

grep -v '^\s*#' "$QUEUE" | grep -v '^\s*$' | while read -r CONFIG; do
  echo "=== $(date -u +%m/%d\ %H:%M) START $CONFIG"
  if python experiments/jobs/crt_text_responses.py --config "$CONFIG" --output-root runs_shared; then
    echo "=== $(date -u +%m/%d\ %H:%M) DONE  $CONFIG"
  else
    echo "=== $(date -u +%m/%d\ %H:%M) FAIL  $CONFIG (skipping)"
  fi
  commit_push "Queue: $(basename "$CONFIG" .toml)"
done
echo "=== $(date -u +%m/%d\ %H:%M) QUEUE FINISHED"
