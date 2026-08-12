#!/usr/bin/env bash
# Reports how the sharded review round is doing: wall-clock against the deadline, and the state of every
# shard file. Cheap enough to call on every task notification; it reads files, it never waits.
#
# Usage: bash .claude/skills/implement-story/scripts/review-status.sh .claude/runs/<slug> [deadline_seconds]

set -uo pipefail

RUN_DIR="${1:?usage: review-status.sh <run-dir> [deadline_seconds]}"
DEADLINE="${2:-720}"
REPO_ROOT="$(git rev-parse --show-toplevel)"

case "$RUN_DIR" in
  /*) ;;
  *) RUN_DIR="$REPO_ROOT/$RUN_DIR" ;;
esac

REVIEW_DIR="$RUN_DIR/review"
if [ ! -d "$REVIEW_DIR" ]; then
  echo "no review round started (missing $REVIEW_DIR)"
  exit 1
fi

now=$(date +%s)
started=$(cat "$REVIEW_DIR/.started_at" 2>/dev/null || echo "$now")
elapsed=$(( now - started ))
remaining=$(( DEADLINE - elapsed ))

if [ $remaining -gt 0 ]; then
  echo "elapsed ${elapsed}s / deadline ${DEADLINE}s - ${remaining}s left"
else
  echo "elapsed ${elapsed}s / deadline ${DEADLINE}s - DEADLINE PASSED, stop stragglers and continue"
fi
echo "reviewing $(cat "$REVIEW_DIR/.head_sha" 2>/dev/null || echo 'unknown sha')"
echo

shopt -s nullglob
found=0
for f in "$REVIEW_DIR"/*.md; do
  found=1
  name=$(basename "$f")
  findings=$(grep -c '^```finding' "$f" 2>/dev/null || echo 0)
  # The sentinel is the only thing that distinguishes a finished lens from one that died mid-write.
  if tail -n 5 "$f" | grep -q -- '<!-- shard-complete -->'; then
    state="complete"
  else
    state="partial "
  fi
  printf '%-24s %s  %s finding(s)\n' "$name" "$state" "$findings"
done

if [ $found -eq 0 ]; then
  echo "(no shard files yet)"
fi

echo
echo "Any lens you launched with no file above is missing: retry it once, then record it as a gap."
