#!/usr/bin/env bash
# Reports migration numbers this branch shares with a branch it will meet.
#
# Django numbers migrations sequentially from whatever it can see, and a worktree can only see itself.
# Two stories branching off the same leaf both get the next number, both stay green on their own, and
# the second one to merge turns "migrate" - and with it every database test - red on main.
#
# Usage: bash .claude/skills/implement-story/scripts/migration-numbers.sh [base-ref]
# Exit code: 0 when no number is shared with the base, 1 otherwise. A number shared with a neighbouring
# worktree is a warning rather than a failure: that branch may never land, and renumbering costs nothing.

set -uo pipefail

BASE_REF="${1:-github/main}"
REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT" || exit 1

MIGRATION_PATH='^apps/.+/migrations/[0-9]{4}_.+\.py$'

# app <tab> number <tab> filename <tab> where-it-was-seen, one line per migration file.
emit() {
  awk -v where="$1" '{
    slash = match($0, /\/migrations\/[^/]+$/)
    app = substr($0, 1, slash - 1)
    file = substr($0, slash + length("/migrations/"))
    print app "\t" substr(file, 1, 4) "\t" file "\t" where
  }'
}

{
  # The working tree, tracked and untracked alike: the migration under test is usually not committed yet.
  git ls-files --cached --others --exclude-standard \
    | grep -E "$MIGRATION_PATH" | emit "this branch"

  git ls-tree -r --name-only "$BASE_REF" 2>/dev/null \
    | grep -E "$MIGRATION_PATH" | emit "$BASE_REF"

  # Every other checkout of this repository. Their branches are the stories running right now.
  here="$REPO_ROOT"
  git worktree list --porcelain | awk '
    /^worktree /  { path = substr($0, 10) }
    /^branch /    { print path "\t" substr($0, 8) }
  ' | while IFS=$'\t' read -r path ref; do
    [ "$path" = "$here" ] && continue
    git ls-tree -r --name-only "$ref" 2>/dev/null \
      | grep -E "$MIGRATION_PATH" | emit "${ref#refs/heads/}"
  done
} | sort -u | awk -F'\t' -v base="$BASE_REF" '
  {
    number = $1 "\t" $2
    entry  = number "\t" $3

    if ($4 == "this branch") { on_branch[entry] = 1; used_here[number] = $3 }
    else if ($4 == base)     { on_base[entry] = 1; elsewhere[entry] = $4 }
    else                     { elsewhere[entry] = $4 }

    if ($2 + 0 > highest[$1]) { highest[$1] = $2 + 0 }
  }
  END {
    for (entry in elsewhere) {
      if (entry in on_branch) continue

      split(entry, part, "\t")
      number = part[1] "\t" part[2]
      if (!(number in used_here)) continue

      printf "%s  %s/migrations/%s is two different migrations: %s (this branch) vs %s (%s)\n",
             (entry in on_base) ? "COLLISION" : "warning",
             part[1], part[2], used_here[number], part[3], elsewhere[entry]
      printf "%s  renumber yours to %04d and point its dependency at the one it now follows\n",
             (entry in on_base) ? "         " : "       ", highest[part[1]] + 1

      if (entry in on_base) { failed = 1 }
    }
    exit failed ? 1 : 0
  }
'
