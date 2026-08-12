---
name: implement-story
description: Implement a story end to end - resolve it from a GitHub issue link, issue number or plain text, plan it, write it, get the local CI gates green, run a resumable sharded code review that never blocks on a dying reviewer, fix what it finds, then commit, push and open the PR. Use when asked to implement an issue or story, or to resume an interrupted run.
---

# Implement a story

One story, from issue to open PR, with a code review that survives its own reviewers dying.

## Usage

```
/implement-story <github issue url | issue number | free text describing the story>
/implement-story --resume [slug]        # pick an interrupted run back up
/implement-story <story> --native       # use the built-in /code-review instead of sharded review
/implement-story <story> --deadline=900 # review wall-clock budget in seconds (default 720)
/implement-story <story> --no-pr        # stop after pushing, do not open the PR
```

## The run directory

Everything durable lives in `.claude/runs/<slug>/` (gitignored). This directory *is* the state - it is
what makes a dead reviewer cost one lens instead of the whole run.

```
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
```

A shard file ending in the line `<!-- shard-complete -->` is finished. A shard file **without** it is a
partial and is still used - its findings count, its coverage is reported as incomplete. No file at all
means that lens was never reviewed, which is reported as a gap rather than blocking the run.

## Before you start

Read [AGENTS.md](../../../AGENTS.md) and the docs it points at for the area you are about to touch. They
are normative, and this project deviates from Django defaults on purpose. Do not infer conventions from
nearby code.

## Phase 0 - Resolve the story

Derive `<slug>` as a short kebab-case name for the story (`faction-defeat`, `town-shop-restock`).

- **Issue URL or number** - `gh issue view <n> --json number,title,body,labels,comments`. Write the title,
  body and any comment that changes the requirements into `spec.md`. Record the issue number in
  `state.json`; it becomes `Closes #<n>` in the PR.
- **Free text** - write it into `spec.md` verbatim, then add your reading of it underneath as
  "Interpretation". No issue number.

Resolve once. Later phases read `spec.md`, they do not re-fetch.

If the working tree is dirty or a rebase/merge is in progress, stop and say so. Do not start a story on
top of someone else's half-finished work.

## Phase 1 - Plan, then stop

Create the branch from an up-to-date `main`: `feature/<slug>` for new behaviour, `fix/<slug>` for a
defect, `chore/<slug>` for maintenance. The remote is `github`, not `origin`.

Write `plan.md`: the files you will touch, the messages/handlers you will add, the tests you will write,
and anything in the story you consider out of scope. Follow
[adding a new flow](../../../docs/patterns/adding-a-flow.md) if the story crosses the message bus.

**Present the plan and stop for approval.** This is the only mandatory stop in the run.

## Phase 2 - Implement

Work the plan. Tests are part of the story, not a follow-up - see
[testing strategy](../../../docs/patterns/testing-strategy.md) before writing any of them.

Keep commits in logical chunks as you go, following
[commit messages](../../../docs/contributing/commit-messages.md): one capitalized subject line, no
trailing period, no issue tag.

## Phase 3 - CI gates

```bash
bash .claude/skills/implement-story/scripts/ci.sh .claude/runs/<slug>
```

Runs the same two gates as `.github/workflows/tests.yml`: `pre-commit run --all-files` (twice, because the
formatting hooks fail the run they rewrote) and `uv run pytest --cov` behind the 100% branch gate. Results
land in `ci.md`, full output in `ci-logs/`.

Fix and re-run until both are green. **The review does not start on a red run** - reviewers must not spend
wall-clock on findings a linter would have caught for free. If coverage is short, read
[coverage](../../../docs/patterns/coverage.md): the fix is a test, never `# pragma: no cover` and never a
lower `fail_under`.

## Phase 4 - Sharded code review

With `--native`, skip this phase and invoke `/code-review` instead, then jump to Phase 5.

### Launch

1. `git diff main...HEAD --stat` - count changed lines and decide the shard count:

   | Changed lines | Shards |
   |---|---|
   | up to 200 | 1 |
   | up to 600 | 2 |
   | up to 1200 | 3 |
   | more | 4 |

   Take them in the order listed in [review lenses](references/review-lenses.md) - the lenses are ranked,
   so a small diff drops the least valuable ones and a deadline drops them too.
2. Write `review/.started_at` (`date +%s`) and `review/.head_sha` (`git rev-parse HEAD`).
3. Launch every shard **in a single message** so they run concurrently, one `Agent` call each with
   `subagent_type: "general-purpose"` and `model: "sonnet"`. Build each prompt from the template in
   [review lenses](references/review-lenses.md). Record the returned agent ids in `state.json`.

### Wait

Shard completions arrive as task notifications. On each one:

```bash
bash .claude/skills/implement-story/scripts/review-status.sh .claude/runs/<slug>
```

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

## Phase 6 - Ship

Commit the fixes, push with `git push -u github <branch>`, and open the PR:

```bash
gh pr create --base main --title "<story title>" --body-file <body>
```

The body carries: what the story asked for, what you built, `Closes #<n>` when there is an issue, the CI
result, and a **Review coverage** line naming any lens that was skipped or partial. Unless `--no-pr`.

End with a short report: what shipped, what CI said, what the review found and what you fixed, what was
skipped and why, and the out-of-scope list.

## Resuming

`state.json` carries `phase`. On `--resume`, read it and re-enter at that phase. Within Phase 4, relaunch
only the shards whose status is not `complete`, and only if `review/.head_sha` still matches `HEAD` - if
the code moved on, the round is stale, so start a fresh one.

If a run is interrupted anywhere, the run directory is enough to continue. Never restart from Phase 0 when
`spec.md` already exists.

## Cost rules

The point of the sharding is to spend wall-clock once. Hold these:

- Review the diff against `main`, never the repository.
- Never re-run a shard that produced a complete file.
- Never re-review after fixes; check the fix delta instead.
- Never spend review wall-clock on anything `ruff`, `boa-restrictor` or the coverage gate already catches.
- One retry per shard, at half scope. Then it is a gap.
