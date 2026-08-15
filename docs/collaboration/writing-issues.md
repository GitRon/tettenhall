# Writing an issue

An issue here is not a reminder to yourself — it is the input to
[`/implement-story`](../../.claude/skills/implement-story/SKILL.md). Phase 0 of that skill copies the
title, body and comments into `spec.md` **once** and never fetches the issue again. Whatever is not in
the body does not exist for the implementation.

So an issue has to survive being read exactly once, by someone with no memory of the conversation that
produced it. Two things are therefore not optional: the labels, and the review pass in step 3.

## 1. Label it

Every issue carries labels on two axes. Both are required.

### Scope — exactly one of `mvp`, `v1`, `v2`

This is the only thing that answers "what do we do next", so an issue without a scope label is invisible
when planning.

- **`mvp`** — the game is incoherent or unplayable without it: a rule that contradicts itself, a state the
  player cannot get out of, a loop that has no ending.
- **`v1`** — wanted for the first version anyone else plays. Depth, polish and readability; the game works
  without it, it is just thinner.
- **`v2`** — worth keeping, not worth planning around yet.

When in doubt between `mvp` and `v1`, ask whether a player would call the current behaviour *broken* or
merely *plain*. Broken is `mvp`.

### Type — at least one of `bug`, `enhancement`, `documentation`, `question`

- **`bug`** — the code does something the game does not mean, and the issue can name where.
- **`enhancement`** — new behaviour, or behaviour the game means but does not have.
- **`documentation`** — a doc [indexed in the README](../../README.md) is wrong, missing or has drifted
  from the code.
- **`question`** — a decision has to be made before the work can be specified. Issue #62 is the pattern:
  the code is doing something nobody chose, and the issue exists to get it chosen. A `question` issue is
  finished when the decision is written down, not when code changes — #62 closed with a comment in a
  handler (14db034) and no behaviour change at all.

`bug` + `question` together is legitimate and common: the behaviour is wrong *and* the right behaviour is
open.

The remaining labels are not classifications. `duplicate`, `invalid` and `wontfix` are reasons for
closing; `good first issue` and `help wanted` are invitations.

## 2. Write the body

Ground every claim in the code. A claim without a `path/to/file.py:line` behind it is an opinion, and the
next reader has no way to check it.

```markdown
<!-- Feature: open with the story. Bug: open with the wrong behaviour. -->
**As a** player
**I want** …
**so that** …

<!-- What the code does today, with references. This is the part that makes the issue actionable. -->
`handle_x` sets `CONDITION_FLEEING` (`apps/skirmish/handlers/commands/warrior.py:123`). Nothing ever
sets it back, because …

### Why it matters
<!-- What it costs the player or the game. Numbers and consequences, not adjectives. -->

### Direction
<!-- Where the fix should go, and the open question. Options with their trade-offs — one bullet each,
     naming what it touches and what it risks. Add "Suggested: …" when you have an opinion. -->

### Out of scope
<!-- What this issue does not own, and which issue does. -->

### Depends on
<!-- Issues that must land first, with the reason the order matters. -->
```

Rules that matter more than the skeleton:

- **The title is a sentence about the game, not the code.** *"A warrior who routs without a scratch never
  fights again"*, not *"Fix condition reset in replenish_current_morale"*. No `Feat:`/`Bug:` prefix — the
  type label already says that.
- **Direction, not design.** Say where the fix belongs and what the open question is. Deciding the
  implementation in the issue puts the decision where nobody will look at it again.
- **Name the open question explicitly.** If the issue has one and does not say so, it will be answered by
  accident during implementation.
- **For a bug, list the branches that need covering.** The suite runs behind a
  [100% branch gate](../patterns/coverage.md), so the cases are part of the story.
- Drop a section rather than filling it with nothing. An empty *Out of scope* is noise.

Ideas live in the [backlog](backlog.md) until they are worth an issue. Promoting a backlog line means
doing everything on this page — the line itself is one sentence of intent, not a spec.

## 3. Review the draft against the code and the other issues

**This is the step that must not be skipped.** Hand the draft to Claude before it is created, and have it
checked against two things in this order. Expect it to come back with the issue changed — if a draft
survives this untouched, the pass was too shallow.

### Against the codebase

Read [AGENTS.md](../../AGENTS.md) and the docs it points at for the area first — this project deviates
from Django defaults on purpose, so a direction inferred from nearby code is often wrong.

- Does the described behaviour actually happen? Find the code that produces it and cite `file.py:line`.
  If it cannot be found, the premise is wrong and the issue should not be created.
- Is it already there, or half there? Partly-implemented is the common answer, and it changes the issue
  from "build this" to "finish this".
- Does the proposed direction fit the patterns — [message bus](../patterns/message-bus.md),
  [savegame scoping](../patterns/savegame-scoping.md),
  [town buildings](../patterns/town-buildings.md) for balance numbers,
  [testing strategy](../patterns/testing-strategy.md)?
- What does it touch? Handlers, managers, templates — and which existing tests will move.
- What breaks if it lands? Rules elsewhere that assume today's behaviour.

### Against the other issues

`gh issue list --state all --limit 100`, then read the bodies of everything adjacent — closed ones
included, because a closed issue is where a decision was made.

- **Duplicate** — comment on the existing issue instead of opening a second one.
- **Overlap** — two issues touching the same code. Split the ownership in writing: *"Out of scope:
  whether a fled warrior rallies — #43 owns that."*
- **Dependency** — say so and say why: *"#3 sets what a slow recovery costs a rival, so the rate cannot be
  tuned before it lands."*
- **Contradiction** — the draft undoes a decision another issue made. That conflict is the issue.

Cross-references are worth the effort here: they are what stops #43, #44 and #46 from being three
implementations of the same wrong assumption.

### The prompt

```
Review this draft issue for tettenhall before I create it.

1. Read AGENTS.md and the docs it points at for the area this touches.
2. Verify every factual claim against the code. Give me file:line for each one, and say
   plainly which claims you could not confirm.
3. Tell me whether this is already implemented, partly implemented, or rests on a wrong
   premise.
4. Check it against all open and closed issues (gh issue list --state all --limit 100).
   Report duplicates, overlaps, dependencies and contradictions by number.
5. Check the proposed direction against the project's patterns and say where it conflicts.
6. Propose the scope label (mvp/v1/v2) and the type labels, with a reason.
7. Rewrite the issue with the corrections, adding Out of scope and Depends on sections.

<paste the draft here>
```

## 4. Create it

Bodies are long and multi-line, so write the reviewed text to a file and pass it — quoting a body inline
in PowerShell will mangle it. `.claude/runs/` is gitignored, so a draft can live there.

```bash
gh issue create --title "A warrior who routs without a scratch never fights again" \
  --body-file .claude/runs/draft-issue.md --label bug --label mvp
```

Then read it back with `gh issue view --web <n>` — long tables and hard-wrapped bullets do not always
render the way they looked in the editor.

## Checklist

- [ ] Exactly one scope label: `mvp`, `v1` or `v2`
- [ ] At least one type label
- [ ] Title reads as a sentence about the game
- [ ] Every factual claim carries a `file.py:line`
- [ ] Reviewed against the codebase — premise confirmed, existing implementation checked
- [ ] Reviewed against all open and closed issues — duplicates, overlaps, dependencies named by number
- [ ] The open question is stated, or there is none
- [ ] *Out of scope* says which issue owns what was left out
- [ ] For a bug: the branches that need covering are listed

## See also

- [Backlog](backlog.md) — where ideas live before they are issues
- [Implement a story](../../.claude/skills/implement-story/SKILL.md) — what happens to an issue afterwards
- [Commit messages](../contributing/commit-messages.md) — a different, much shorter, set of rules
