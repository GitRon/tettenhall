#!/usr/bin/env bash
# Runs the two gates from .github/workflows/tests.yml locally and records the outcome.
#
# Usage: bash .claude/skills/implement-story/scripts/ci.sh .claude/runs/<slug>
# Exit code: 0 when both gates pass, 1 otherwise.

set -uo pipefail

RUN_DIR="${1:?usage: ci.sh <run-dir>}"
REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT" || exit 1

case "$RUN_DIR" in
  /*) ;;
  *) RUN_DIR="$REPO_ROOT/$RUN_DIR" ;;
esac

LOG_DIR="$RUN_DIR/ci-logs"
mkdir -p "$LOG_DIR"
OUT="$RUN_DIR/ci.md"

# The formatting hooks rewrite files and then fail the very run that rewrote them, so a single red pass
# proves nothing. The second pass on the rewritten tree is the honest signal - hence a retry, not a loop.
pre-commit run --all-files > "$LOG_DIR/pre-commit.log" 2>&1
lint_status=$?
lint_passes=1
if [ $lint_status -ne 0 ]; then
  pre-commit run --all-files > "$LOG_DIR/pre-commit.log" 2>&1
  lint_status=$?
  lint_passes=2
fi

# Coverage config lives in pyproject.toml and fails below 100% branch coverage, so this one command is
# both the test gate and the coverage gate.
uv run pytest --cov > "$LOG_DIR/pytest.log" 2>&1
test_status=$?

verdict() { [ "$1" -eq 0 ] && echo "PASS" || echo "FAIL"; }

{
  echo "# CI gates"
  echo
  echo "Commit: \`$(git rev-parse --short HEAD 2>/dev/null || echo unknown)\` on branch \`$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)\`"
  echo
  echo "| Gate | Command | Result |"
  echo "|---|---|---|"
  echo "| Lint | \`pre-commit run --all-files\` ($lint_passes pass(es)) | $(verdict $lint_status) |"
  echo "| Tests + coverage | \`uv run pytest --cov\` | $(verdict $test_status) |"
  echo
  if [ $lint_status -ne 0 ]; then
    echo "## pre-commit (last 60 lines)"
    echo
    echo '```'
    tail -n 60 "$LOG_DIR/pre-commit.log"
    echo '```'
    echo
  fi
  if [ $test_status -ne 0 ]; then
    echo "## pytest (last 80 lines)"
    echo
    echo '```'
    tail -n 80 "$LOG_DIR/pytest.log"
    echo '```'
    echo
  fi
  echo "Full output: \`${LOG_DIR#"$REPO_ROOT/"}/\`"
} > "$OUT"

cat "$OUT"

if [ $lint_status -eq 0 ] && [ $test_status -eq 0 ]; then
  exit 0
fi
exit 1
