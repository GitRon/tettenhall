---
name: clean-worktrees
description: Remove the worktrees and local branches that finished stories leave behind - every one whose PR is merged and that holds nothing the PR did not. Proves each one is safe against the merged PR's head commit, never forces, and reports what it kept and why. Use when asked to clean up, prune or tidy old worktrees or branches.
---

# Clean up worktrees

`/implement-story` leaves its worktree standing after the PR opens, because review comments need a
checkout to be answered in. Once the PR is merged the worktree and its branch are dead weight. This skill
removes them - and only them.

## Usage

```
/clean-worktrees              # worktrees and their branches
/clean-worktrees --dry-run    # print the plan, remove nothing
```

## Why the obvious checks do not work here

PRs are **squash-merged**. The commits on a feature branch never reach `main` - one new commit does - so
`git branch --merged`, `git merge-base --is-ancestor <tip> github/main` and `git branch -d` all call every
finished branch unmerged. A remote branch marked `[gone]` is no proof either: it says the branch was
deleted on GitHub, not that every local commit went with it.

The one test that holds: **the branch tip is the head commit of a merged PR for that branch, or an
ancestor of it.** Then everything on the branch went into the squash. An ancestor is the common case of
commits added on GitHub before the merge - "Update branch", an accepted review suggestion - that were
never pulled. A tip that is neither carries commits made after the merge, or never pushed, and stays.

## Phase 1 - gather

Run these as plain, separate commands. In a session isolated to a worktree, the guard refuses `git -C`
pointed at another checkout and any loop or pipeline around `git` it cannot verify - so do not build a
shell loop, and do not wrap the commands in a script to get past it. Do the comparison yourself from the
output.

```bash
git fetch github --prune
git worktree list --porcelain
git for-each-ref refs/heads --format='%(refname:short) %(objectname) %(upstream:track)'
gh pr list --state merged --limit 500 --json number,headRefName,headRefOid --jq '.[] | "\(.headRefName) \(.headRefOid) #\(.number)"'
gh pr list --state open --limit 500 --json headRefName --jq '.[].headRefName'
ls <main>/.claude/worktrees
```

`<main>` is the main checkout: the first `worktree` entry of `git worktree list --porcelain`. Every path
in this skill is absolute and built from that output. A relative `.claude/worktrees/...` resolves against
the current checkout, so a session running inside a worktree would look in its own folder - every
removal fails with "is not a working tree" and the leftover-directory check comes back empty.

Compare full SHAs, not abbreviations. A branch name can belong to several merged PRs (a reused
`fix/playthrough-papercuts`, say) - the tip passing against any of their heads is enough. Raise `--limit`
if either list comes back with exactly 500 entries.

A tip equal to a merged head needs no further command. For any other tip on a branch with a merged PR,
run one plain command per candidate head:

```bash
git merge-base --is-ancestor <tip> <headRefOid>
```

Exit 0 passes, exit 1 fails. Exit 128 means the head commit is not in the local repository - it was
added on GitHub and the remote branch is deleted. GitHub keeps the PR's ref, so fetch it and run the
check again; if the fetch fails too, the branch stays:

```bash
git fetch github pull/<number>/head
```

## Phase 2 - classify

Each worktree other than the main checkout falls into exactly one bucket:

| Bucket | Test | Action |
|---|---|---|
| remove | branch tip is a merged PR's head or an ancestor of it, and the branch has no open PR | `git worktree remove` |
| remove | detached `HEAD` on a commit already in `main` (`git merge-base --is-ancestor <sha> github/main` exits 0) | `git worktree remove` |
| keep: own session | the worktree this session runs in | report; it can only be removed from elsewhere |
| keep: newer work | tip is neither a merged head nor an ancestor of one, no merged PR, or an open PR | report with the reason |

Then the local branches, after the worktrees are gone - a branch checked out in a worktree cannot be
deleted:

| Bucket | Test | Action |
|---|---|---|
| delete | tip is a merged PR's head or an ancestor of it, no open PR, not checked out anywhere | `git branch -D` |
| keep | `main`, the branch this session has checked out, anything else | report |

`-D` and not `-d`, because of the squash: `-d` refuses every one of them. The tip test above is what
makes `-D` safe here.

Finally, directories under `<main>/.claude/worktrees/` that `git worktree list` does not know about. They are
leftovers git no longer tracks. List what is inside and **ask before deleting** - nothing has proved them
safe.

On `--dry-run`, print the three tables and stop.

## Phase 3 - remove

One plain command per worktree, never `--force`:

```bash
git worktree remove <path>     # absolute, from git worktree list --porcelain
```

Without `--force`, git refuses a worktree with modified or untracked files, so uncommitted work survives
even if the classification got something wrong. Ignored files (`.venv`, `node_modules`,
`.claude/runs/`) do not block removal and go with the directory. A refusal moves that worktree to the
keep list with git's message as the reason - do not retry it with `--force`.

These calls are independent, so send them in parallel batches rather than one at a time.

Then `git branch -D <branch>` for each branch in the delete bucket, and `git worktree prune` to drop
registrations whose directory is already gone.

## Phase 4 - report

Confirm with `git worktree list` and `ls <main>/.claude/worktrees`, then say:

- how many worktrees and branches went, in one line - not the list
- every worktree and branch kept, each with its reason
- for this session's own worktree, the command to remove it from the main checkout once the session ends
- any untracked directories, and what is inside them
