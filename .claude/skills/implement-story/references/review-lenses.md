# Review lenses and the shard prompt

Four lenses, ranked. A small diff uses the first N; a deadline cuts from the bottom. The ranking is by how
expensive the class of bug is to find later, not by how often it fires.

| # | File | Lens | Normative docs the shard must read first |
|---|---|---|---|
| 01 | `01-correctness.md` | Correctness and message-bus wiring | [message-bus](../../../../docs/patterns/message-bus.md), [handlers](../../../../docs/patterns/handlers.md), [strict-mode](../../../../docs/patterns/strict-mode.md), [registry-tests](../../../../docs/patterns/registry-tests.md) |
| 02 | `02-data-layer.md` | Data layer, savegame scoping and migrations | [savegame-scoping](../../../../docs/patterns/savegame-scoping.md), [app-layout](../../../../docs/patterns/app-layout.md), [town-buildings](../../../../docs/patterns/town-buildings.md) |
| 03 | `03-tests.md` | Test honesty and coverage substance | [testing-strategy](../../../../docs/patterns/testing-strategy.md), [testing-conventions](../../../../docs/patterns/testing-conventions.md), [testing-data](../../../../docs/patterns/testing-data.md), [mocking](../../../../docs/patterns/mocking.md), [coverage](../../../../docs/patterns/coverage.md) |
| 04 | `04-conformance.md` | Spec conformance and simplification | `spec.md`, [app-layout](../../../../docs/patterns/app-layout.md) |

### What each lens is looking for

**01 Correctness and message-bus wiring.** Logic that is wrong for inputs the story will actually produce.
Commands emitted with no handler. Handlers that mutate and return nothing where an event was owed. The
golden rule violated in either direction. Querysets left unevaluated on a message. `context` not
keyword-only. Off-by-one and inverted conditions in the game rules the story changed.

**02 Data layer, savegame scoping and migrations.** A model object resolved in a view without the scoping
mixins - a savegame leak is silent and this is the lens that catches it. Queries in loops. Missing
`select_related`/`prefetch_related` on a path the story made hot. A migration that will not apply on an
existing database, or model changes with no migration at all. Game-balance numbers written somewhere other
than where the docs put them.

**03 Test honesty and coverage substance.** Coverage that is reached without asserting anything. First-party
code mocked - the docs call that a review finding outright. Branches covered by patching the thing under
test rather than exercising it. A branch behind unpatched randomness, which makes the gate pass by chance.
Tests that would still pass if the story's change were reverted.

**04 Spec conformance and simplification.** Requirements in `spec.md` that the diff does not actually
satisfy, and behaviour in the diff that nothing in `spec.md` asked for. Code duplicated from somewhere it
could have been reused. Abstraction introduced for one caller. Dead branches left behind by the change.

## Shard prompt template

Fill the placeholders and pass this as the `Agent` prompt. Keep the wording - the incremental-write rule
and the verify stage are what make a dying shard cheap and a surviving shard trustworthy.

---

You are reviewing one lens of a code change in the Tettenhall repository at `<REPO_ROOT>`.

**Your deliverable is the file `<RUN_DIR>/review/<SHARD_FILE>`, not your reply.** Nothing you return in
chat is read. Write findings into that file as you confirm them, one at a time, appending - never buffer
them to the end. If you are killed halfway through, everything already written still counts, and that is
the point.

The change under review is `git diff main...HEAD`<SCOPE_NOTE>. Review only that diff. Problems on lines
this change did not touch are out of scope.

**Your lens: <LENS_NAME>.** <LENS_DESCRIPTION>

Read these before you review - they are normative for this project, which deviates from Django defaults on
purpose: <LENS_DOCS>. Also read `<RUN_DIR>/spec.md` for what the change was supposed to do.

Work in two stages, per finding:

1. **Find.** Scan the diff through your lens and note candidates.
2. **Verify.** For each candidate, go back to the actual code and try to *refute* it. Read the
   surrounding function, the callers, the tests. Then score your confidence 0-100 that it is a real defect
   a reviewer should raise: 100 you confirmed it end to end, 80 you verified it and it will bite in
   practice, 50 real but a nitpick, 25 you could not verify it, 0 refuted. **Write it to the file only if
   it scores 80 or higher.** Default to refuting when you are unsure - a false positive costs the
   maintainer more time than a missed nitpick.

Do not report: anything `ruff`, `boa-restrictor` or the 100% branch coverage gate already catches (they
run before you and are green); formatting and import order; pre-existing problems; style a senior
engineer would not raise in review; changes that are obviously intentional parts of the story.

Append each surviving finding in exactly this format:

```finding
file: apps/skirmish/handlers/commands/skirmish.py
line: 42
severity: high | medium | low
category: <short-kebab-slug>
claim: One sentence stating the defect.
scenario: Concrete inputs or state, then the wrong output or crash that follows.
confidence: 85
```

When you have finished the whole lens, append this line and nothing after it:

`<!-- shard-complete -->`

If you find nothing, still append the sentinel - a complete file with no findings is a real result and
stops the orchestrator from retrying you.

---

## Retry variant

On the single permitted retry, keep the prompt identical but replace `<SCOPE_NOTE>` with:

> , narrowed for this retry to these files only: `<FILE_LIST>` (the largest by changed lines; the rest of
> the diff is out of scope for you).

and note in the merged `findings.md` that the lens ran at reduced scope.
