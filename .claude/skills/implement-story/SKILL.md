---
name: implement-story
description: Implement a story end to end - resolve it from a GitHub issue link, issue number or plain text, check it out into its own worktree, plan it, write it, get the local CI gates green, run a resumable sharded code review that never blocks on a dying reviewer, fix what it finds, play the story in a real browser to confirm it works, then commit, push and open the PR. Use when asked to implement an issue or story, or to resume an interrupted run.
---

# Implement a story

One story, from issue to open PR, with a code review that survives its own reviewers dying and a browser
that confirms the thing actually works.

## Usage

```
/implement-story <github issue url | issue number | free text describing the story>
/implement-story --resume [slug]           # pick an interrupted run back up
/implement-story <story> --no-worktree      # work in this checkout instead of a fresh worktree
/implement-story <story> --native          # use the built-in /code-review instead of sharded review
/implement-story <story> --deadline=900    # review wall-clock budget in seconds (default 720)
/implement-story <story> --no-content-review # skip the browser phase
/implement-story <story> --content-port=9000 # port for the smoke server (default 8765)
/implement-story <story> --no-pr           # stop after pushing, do not open the PR
```

## The run directory

Everything durable lives in `.claude/runs/<slug>/` (gitignored) inside the story's own worktree. This
directory *is* the state - it is what makes a dead reviewer cost one lens instead of the whole run.

```
.claude/runs/
  .lock                this worktree's one-run-at-a-time lock: slug, branch, epoch seconds
.claude/runs/<slug>/
  spec.md              the story, resolved once, never re-fetched
  plan.md              the approved implementation plan
  state.json           phase, branch, shard status, attempt counts
  ci.md                latest gate results
  ci-logs/             full pre-commit and pytest output
  review/
    .started_at        epoch seconds, written when the round launches
    .head_sha          the commit the round is reviewing
    01-correctness.md  each shard writes its own file, incrementally
    02-data-layer.md
    03-tests.md
    04-conformance.md
  findings.md          merged, deduped, triaged
  content/
    journey.md         the steps to play, written before clicking, with the result of each
    findings.md        what a player sees that is wrong
    smoke.sqlite3      the throwaway database the browser plays on
    server.log         the smoke server's output, where the tracebacks are
    setup.log          migrate, loaddata and user seeding
    .port  .pid        the running smoke server
```

A shard file ending in the line `<!-- shard-complete -->` is finished. A shard file **without** it is a
partial and is still used - its findings count, its coverage is reported as incomplete. No file at all
means that lens was never reviewed, which is reported as a gap rather than blocking the run.

`state.json` is what a later session resumes from, so its shape is fixed rather than improvised:

```json
{
  "slug": "faction-defeat",
  "issue": 21,
  "branch": "feature/faction-defeat",
  "base": "github/main",
  "session": "faction-defeat [f69956]",
  "phase": "review",
  "deadline_seconds": 720,
  "ci_attempts": 2,
  "touches": ["apps/faction/models/faction.py", "apps/faction/tests/models/test_faction.py"],
  "review": {
    "head_sha": "c753616",
    "shards": {
      "01-correctness": { "status": "complete", "attempts": 1, "agent_id": "agent_x" },
      "02-data-layer":  { "status": "running",  "attempts": 2, "agent_id": "agent_y" },
      "03-tests":       { "status": "gap",      "attempts": 2, "reason": "deadline" }
    }
  },
  "content": {
    "status": "pending",
    "port": 8765,
    "rounds": 0
  }
}
```

`base` is the ref every diff is taken against: `github/main`, or a neighbour's branch when this story
stacks on one. Phase 7 strips a `github/` prefix off it for `gh pr create --base`, which wants a branch
name. `session` is what `ListAgents` calls this run - it tells each session its own name, and writing it
down here is what lets a neighbour address this one instead of guessing. `touches` is the file list this
run claims, which is how the neighbouring worktrees see it coming. `phase` is one of `spec`, `plan`,
`implement`, `ci`, `review`, `triage`, `content`, `ship`. A shard
`status` is one of `running`, `complete`, `partial`, `gap`. A `content.status` is one of `pending`,
`pass`, `findings`, `blocked`, `skipped`. Write the file after every phase transition and every shard
state change - it is cheap, and it is the only thing standing between an interrupted run and a restart.

## Before you start

Read [AGENTS.md](../../../AGENTS.md) and the docs it points at for the area you are about to touch. They
are normative, and this project deviates from Django defaults on purpose. Do not infer conventions from
nearby code.

## Parallel runs

One story, one worktree - Phase 0 creates it. Nearly everything a run touches is per-checkout that way:
the branch, the run directory, `db.sqlite3`, the smoke database inside `content/`, and the port, which
`content-server.sh` probes upward from the default rather than assuming it is free. Three things still
reach across.

**The browser is shared across the whole machine.** `@playwright/mcp` gives every server started without
`--isolated` the same daemon browser, so two content reviews land in one Chrome: one of them sees the
other's tabs and the other dies mid-navigation with `Target page, context or browser has been closed`.
Phase 6 asks the neighbours before the first click; [content review](references/content-review.md) carries
the handshake and the fix.

**The neighbours are working the same repository.** Two stories editing the same files find that out at
the merge otherwise, so Phase 1 reads what the other worktrees have claimed and puts the overlap in front
of you at the approval stop.

**One run at a time per worktree.** Phase 2 rewrites the working tree, so a second run in the same
directory pulls the ground out from under the first. `.claude/runs/.lock` is one line -
`<slug> <branch> <epoch seconds>` - written in Phase 0 and deleted in Phase 7. In practice it only catches
a second session opened on a `--resume`.

## Phase 0 - Resolve the story

**On `--resume`, find the run before anything else.** The run directory lives inside the story's own
worktree, so a resume started anywhere else sees no `spec.md` and would resolve the story a second time
and try to create a branch that already exists. Walk `git worktree list --porcelain`, take the one whose
`.claude/runs/<slug>/spec.md` exists, `EnterWorktree` with its `path`, and skip the rest of this phase
apart from the lock.

Derive `<slug>` as a short kebab-case name for the story (`faction-defeat`, `town-shop-restock`).

- **Issue URL or number** - `gh issue view <n> --json number,title,body,labels,comments`. Write the title,
  body and any comment that changes the requirements into `spec.md`. Record the issue number in
  `state.json`; it becomes `Closes #<n>` in the PR.
- **Free text** - write it into `spec.md` verbatim, then add your reading of it underneath as
  "Interpretation". No issue number.

Resolve once. Later phases read `spec.md`, they do not re-fetch.

### Into its own worktree

One story, one checkout. The branch, the run directory and the smoke database all belong to it and to
nothing else, which is what lets several stories run at once.

```bash
git fetch github
[ "$(git rev-parse --git-dir)" = "$(git rev-parse --git-common-dir)" ] || echo "already in a worktree"
```

Fetch first, whichever way this goes. The branch is cut from `github/main`, never from local `main`, which
only moves on a `pull` and is stale on any machine that has been reviewing more than merging.

**Already in a worktree**, or `--no-worktree`: adopt the branch that is checked out and create nothing. A
worktree sitting on `main` still needs its own branch - `git switch -c <branch> github/main`, taking the
name from the next step. This is the case where a dirty tree matters: if `git status --porcelain` is not
empty or a rebase/merge is in progress, stop and say so rather than building on someone else's
half-finished work.

**In the main checkout**: create one. A new worktree starts from a remote ref, so whatever is lying around
uncommitted here does not come with it and does not block the run.

```bash
git worktree add -b feature/<slug> .claude/worktrees/issue-<n>-<slug> github/main
```

`feature/` for new behaviour, `fix/` for a defect, `chore/` for maintenance. The directory drops the
`issue-<n>-` prefix when the story came in as free text. The remote is `github`, not `origin` - which is
also why the worktree is created here rather than by `EnterWorktree`'s own `name`, whose base ref is
`origin/<default>`.

Then call `EnterWorktree` with `path` pointing at the new directory: the session moves in, and the rest of
the run happens there.

A fresh worktree carries no untracked files, so it has no `.venv`, and Phase 3 is where that would
surface - long after the story is written:

```bash
[ -x .venv/bin/python ] || [ -x .venv/Scripts/python.exe ] || uv sync
```

`pre-commit` and `uv` are installed machine-wide and their caches are shared, so they need nothing per
checkout. `node_modules` is missing too, but `content-server.sh` installs it in Phase 6 rather than
failing.

The worktree stays behind when the run ends. Phase 7 opens a PR, it does not merge one, and review
comments need a checkout to be answered in.

### Then take the worktree's lock, and say who you are

Record `base` as `github/main` and `session` as the name `ListAgents` reports for this session - it opens
with "This session is `<name> [ref]`". A neighbour reads that name out of `state.json` to reach this run;
without it, the rows `ListAgents` returns are just names, some of them sessions on other projects
entirely.

```bash
mkdir -p .claude/runs
cat .claude/runs/.lock 2>/dev/null          # empty, or a slug that is not yours -> stop
echo "<slug> <branch> $(date +%s)" > .claude/runs/.lock
```

A lock naming a different slug means another run owns this working tree. Stop and say which one - do not
take it over. If that run was abandoned, its `state.json` says which phase it died in: resume it, or
delete the lock deliberately and say you did.

## Phase 1 - Plan, then stop

Write `plan.md`: the files you will touch, the messages/handlers you will add, the tests you will write,
and anything in the story you consider out of scope. Follow
[adding a new flow](../../../docs/patterns/adding-a-flow.md) if the story crosses the message bus. Record
the file list as `touches` in `state.json` - that is what the neighbouring worktrees read.

### Neighbours

The other worktrees are working stories of their own, and their run directories are sitting right there:

```bash
git worktree list --porcelain               # absolute paths - read them straight, do not cd
cat <other worktree>/.claude/runs/*/state.json
```

Skip your own worktree, and skip any run whose `phase` is `ship` - that story is on a PR, its files come
back through the merge, and every worktree left standing after its run would otherwise pile into this list
forever.

Intersect your `touches` with what is left. Anything shared goes into `plan.md` under **Neighbours**,
naming the neighbour's slug, branch and phase. Match each neighbour's `session` against `ListAgents` to
say whether it is still alive - a dead one is a merge conflict waiting in the future, a live one is a
moving target. Rows that no `state.json` claims are other people's work; leave them alone. Decide nothing
here: the stop below is where the call gets made.

If the call is to build on a neighbour's branch, record that branch as `base` in `state.json`. Later
phases diff and open the PR against `base`, so a stacked story reviews its own change instead of the
neighbour's too. Only stack on a branch the neighbour has already pushed - it does that in its Phase 7,
and `gh pr create --base` wants a branch that exists on the remote. A neighbour still writing its story
is a reason to wait or to scope around it, not to stack.

**Present the plan and stop for approval.** This is the only mandatory stop in the run.

## Phase 2 - Implement

Work the plan. Tests are part of the story, not a follow-up - see
[testing strategy](../../../docs/patterns/testing-strategy.md) before writing any of them.

Keep commits in logical chunks as you go, following
[commit messages](../../../docs/contributing/commit-messages.md): one capitalized subject line, no
trailing period, no issue tag.

When the work is done, refresh `touches` from `git diff <base>...HEAD --name-only`. A neighbour planning
its story next reads that list, and a plan's guess is worth less to it than the diff.

## Phase 3 - CI gates

```bash
bash .claude/skills/implement-story/scripts/ci.sh .claude/runs/<slug>
```

Runs the same two gates as `.github/workflows/tests.yml`: `pre-commit run --all-files` (twice, because the
formatting hooks fail the run they rewrote) and `uv run pytest --cov` behind the 100% branch gate. Results
land in `ci.md`, full output in `ci-logs/`.

Fix and re-run until both are green, counting rounds in `ci_attempts`. **The review does not start on a
red run** - reviewers must not spend wall-clock on findings a linter would have caught for free. If
coverage is short, read [coverage](../../../docs/patterns/coverage.md): the fix is a test, never
`# pragma: no cover` and never a lower `fail_under`.

The formatting hooks rewrite files, so stage whatever they changed before the next commit - see
[linting](../../../docs/contributing/linting.md).

**After three red rounds, stop and report.** Three failures on the same gate means the plan was wrong, not
that the fix needs another attempt, and grinding on it is exactly the wall-clock this skill exists to
protect. Say what is failing and what you tried.

## Phase 4 - Sharded code review

With `--native`, skip this phase and invoke `/code-review` instead. Then go to Phase 5, but skip its
delta check - there is no review `head_sha` to diff against, and the native review already covered the
change.

### Launch

1. **`git status --porcelain` must be empty.** Commit everything first. The shards review
   `git diff <base>...HEAD`, so uncommitted work is invisible to all of them and the round would come back
   clean having reviewed nothing - the one failure this design must not have. Do not launch on a dirty
   tree.
2. `git diff <base>...HEAD --stat` - count changed lines and decide the shard count:

   | Changed lines | Shards |
   |---|---|
   | up to 200 | 1 |
   | up to 600 | 2 |
   | up to 1200 | 3 |
   | more | 4 |

   Take them in the order listed in [review lenses](references/review-lenses.md) - the lenses are ranked,
   so a small diff drops the least valuable ones and a deadline drops them too.
3. Write `review/.started_at` (`date +%s`) and `review/.head_sha` (`git rev-parse HEAD`).
4. Launch every shard **in a single message** so they run concurrently, one `Agent` call each with
   `subagent_type: "general-purpose"` and `model: "sonnet"`. Build each prompt from the template in
   [review lenses](references/review-lenses.md). Record the returned agent ids in `state.json`.

### Wait

Shard completions arrive as task notifications. On each one:

```bash
bash .claude/skills/implement-story/scripts/review-status.sh .claude/runs/<slug> <deadline_seconds>
```

Pass the deadline explicitly - the script defaults to 720 and would otherwise measure a `--deadline=900`
run against the wrong budget, cutting shards short without saying so.

It prints elapsed seconds against the deadline and the per-shard state (`complete`, `partial`, `missing`).
Do not poll it on a timer - only look when a notification wakes you, or when you have nothing else to do.

**Never re-read a shard's returned text as the source of truth.** The file is the deliverable. An agent
that returns nothing but left a complete file succeeded.

### Retry, once

A shard is failed when its agent returns an error, or dies, or leaves no file. Retry it exactly once, with
the scope halved - hand the retry only the largest changed files by line count, and say so in the prompt.
Bump `attempts` in `state.json`. A second failure is a gap, not a third attempt.

### Deadline

When elapsed exceeds the deadline (default 720s, `--deadline=N` to change it):

1. `TaskStop` any shard still running.
2. Anything with a partial file keeps its findings, marked incomplete.
3. Anything with no file is recorded in `findings.md` as
   `Not reviewed: <lens> - <reason>` and the run continues.

Continuing with a gap is the correct outcome, not a failure. Say plainly which lens was skipped so the
cost of continuing is visible.

### Merge

Read every shard file that exists. Drop findings below confidence 80, drop exact duplicates and collapse
near-duplicates on the same file and line, keeping the clearest wording. Write the survivors to
`findings.md`, most severe first, with the not-reviewed gaps listed at the bottom.

Then call `ReportFindings` with the merged set so they render as a navigable list rather than a wall of
markdown.

## Phase 5 - Triage and fix

Fix everything that is a real defect in code this story touched. Do not fix pre-existing problems in
passing - note them in `findings.md` under "Out of scope, worth a follow-up" and mention them in the final
report. One feature turning up five other things is normal here; the discipline is naming them, not doing
them.

Re-run `ci.sh`. **Do not re-run the review.** Instead, if the fixes were non-trivial, launch a single
`Agent` to check only `git diff <head_sha_from_review>..HEAD` for regressions the fixes introduced. A full
second review round is the single most expensive thing this skill could do and it is almost never worth
it.

## Phase 6 - Content review

Everything so far checked the code against itself. Nothing has loaded a page. This phase plays the story
in a real browser and looks at what a player would see - which is the only way to catch a control wired
to nothing, an htmx request quietly 500ing behind a one-second toast, or a feature that works perfectly
and is reachable from nowhere. Skip it with `--no-content-review`.

Read [content review](references/content-review.md) first. It carries the journey, this app's htmx
habits, how to reach a game state honestly, and what counts as a finding.

1. Start the app on its own throwaway database:

   ```bash
   bash .claude/skills/implement-story/scripts/content-server.sh fresh .claude/runs/<slug>
   ```

   `fresh` for the first round, so the story gets reached the way a player reaches it. Pass
   `--content-port=N` through as the third argument. Record `content.port` in `state.json`.
2. Write `content/journey.md` - the baseline journey plus the steps the story adds, each with its expected
   outcome - **before** you touch the browser. A journey written afterwards only describes what happened.
3. Walk it with the Playwright tools, from this session, in one browser. **Do not fan this out to agents**:
   there is a single browser behind those tools and parallel drivers would fight over it. The neighbouring
   worktrees share it too, unless the Playwright server runs `--isolated`: ask them before the first click
   - [content review](references/content-review.md) carries the handshake.
4. Record the result of every step in `journey.md` and every defect in `content/findings.md`. Check the
   network requests after each mutating click - a failed htmx call leaves the page looking fine.
5. Fix what the story broke, `content-server.sh restart` (the server does not autoreload, so without this
   you are still testing the old code), and walk the failed steps again. **At most two fix rounds**,
   counted in `content.rounds`. A third means the story's design is wrong in a way more clicking will not
   settle - stop and report.
6. Re-run `ci.sh`. A content fix that reddens the suite is worse than the bug it fixed.
7. Stop the server and close the browser, pass or fail:

   ```bash
   bash .claude/skills/implement-story/scripts/content-server.sh stop .claude/runs/<slug>
   ```

   A server left running holds the port and serves pre-fix code to the next run.

If the Playwright tools are not connected, or the server cannot be brought up, set `content.status` to
`skipped` or `blocked` with the reason and carry on to Phase 7. A phase that cannot run is a gap like any
other - say so plainly, and never report a pass you did not see.

## Phase 7 - Ship

Commit the fixes, push with `git push -u github <branch>`, and open the PR:

```bash
gh pr create --base ${base#github/} --title "<story title>" --body-file <body>
```

`--base` wants a branch name, so the `github/` comes off: a run based on `github/main` opens against
`main`, a stacked one against the neighbour's branch as recorded.

The body carries: what the story asked for, what you built, `Closes #<n>` when there is an issue, the CI
result, a **Review coverage** line naming any lens that was skipped or partial, and a **Content review**
line saying which journey was walked in the browser and what it showed - or that the phase was skipped,
and why. Unless `--no-pr`.

A PR onto a neighbour's branch rather than `main` says so in the body, so a reviewer knows half the story
is elsewhere.

Release the worktree's lock once the PR is open - `rm -f .claude/runs/.lock`. A lock left behind blocks
the next story in this worktree for no reason. The worktree itself stays; it is where review comments get
answered.

End with a short report: what shipped, what CI said, what the review found and what you fixed, what the
browser confirmed or broke, what was skipped and why, the out-of-scope list, and the worktree path and
branch - so it is clear what can be removed once the PR is merged.

## Resuming

Phase 0 opens with finding the worktree that holds the run and moving into it, so a resume can be started
from anywhere. It creates no second worktree and resolves no story twice.

`state.json` carries `phase`. On `--resume`, read it and re-enter at that phase. Within Phase 4, relaunch
only the shards whose status is not `complete`, and only if `review/.head_sha` still matches `HEAD` - if
the code moved on, the round is stale, so start a fresh one.

Within Phase 6, `content-server.sh start` reuses a smoke server that is still answering and reruns the
setup against the existing database otherwise, so resuming costs a `start` and re-walking the steps whose
result is missing from `journey.md`. Use `fresh` instead if the recorded results no longer describe the
code, which is the case whenever the diff moved since the round began.

If a run is interrupted anywhere, the run directory is enough to continue. Never restart from Phase 0 when
`spec.md` already exists. A `--resume` of the slug the lock already names simply keeps it; rewrite it if
it is missing.

## Cost rules

The point of the sharding is to spend wall-clock once. Hold these:

- Review the diff against `base`, never the repository.
- The neighbour scan is a file read, not a broadcast. At most one message per neighbour per run, and only
  when an overlap or the browser actually needs an answer.
- Never re-run a shard that produced a complete file.
- Never re-review after fixes; check the fix delta instead.
- Never spend review wall-clock on anything `ruff`, `boa-restrictor` or the coverage gate already catches.
- One retry per shard, at half scope. Then it is a gap.
- One browser, driven from this session. The content review is never fanned out - and never run at the
  same time as a neighbour's, unless the MCP server is `--isolated`.
- Walk the journey you wrote, plus at most ten exploratory clicks. Then write down what you have.
- Two content fix rounds, then stop. And always stop the server - a stale one costs the next run a round.
