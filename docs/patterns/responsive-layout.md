# Responsive layout

**The phone is the default. Every unprefixed utility describes the 390px screen, and `md:` and up add
the desk.**

This is the whole convention, and it is normative for every template in the project. A screen written
the other way round — desktop unprefixed, a narrower variant bolted on — renders at desk proportions on
a phone whenever a prefix is forgotten, which is a silent failure: the page looks right in the browser
the author is using.

## The breakpoints

Tailwind's defaults, unchanged. Only three of them are used here:

| Prefix | From | What it is for |
|---|---|---|
| *(none)* | 0px | **The phone.** One column, full width, nothing beside anything else. |
| `md:` | 768px | **The desk.** Columns, tables at full width, the navbar as one row. |
| `lg:` | 1024px | Only where `md:` genuinely runs out of room — a third column, a wider gutter. |

`sm:` (640px), `xl:` and `2xl:` are available and deliberately unused. A layout that needs a fourth
breakpoint to work is usually a layout that needs a different shape, which is the question the
paragraph below answers.

**`md:` is the one that matters.** It is the single line between "a phone" and "a desk" in this project,
so a template that picks `sm:` or `lg:` for that split is picking a different line from its neighbours
and will disagree with them on a tablet.

## Writing a screen

Start in one column and add to it:

```html
<div class="flex flex-col gap-4 md:flex-row md:gap-6">
```

Not the reverse:

```html
<!-- Wrong: the desk is unprefixed, so the phone gets it too. -->
<div class="flex flex-row gap-6 max-md:flex-col">
```

Both render the same thing today. The first one is still correct when someone adds a third child and
forgets the prefix; the second one is broken on a phone the moment anyone touches it.

Three rules follow from the default:

- **No fixed width is ever unprefixed.** A `w-96` or a `min-w-*` without an `md:` in front of it is a
  horizontal scrollbar on a phone. Widths belong behind `md:`; the phone gets `w-full`.
- **A grid starts at one column.** `grid grid-cols-1 md:grid-cols-3`, never `grid-cols-3` alone.
- **A table gets a scroll container, not a narrower table.** `overflow-x-auto` on a wrapper is the
  honest answer for a table with more than three columns — the table keeps its shape and the page body
  stops scrolling sideways.

## When one column is not enough

Some screens do not have a portrait form. A six-column ledger and the three-panel fight screen are the
two in this project: stacked, the fight screen puts the battle report *between* the two warbands, so the
panel read every round is the one scrolled past twice.

**That is a design decision, and a media query cannot make it.** The obligation in a migration or a new
feature is "fits the viewport and works" — a scroll container, or a stack that is ugly but usable.
Making it *read* well means changing what the screen is, not how wide it is, and that belongs in an
issue against **#64**, which owns the information hierarchy of exactly these screens.

What is never the answer: a `min-width` that pushes the body wider than the screen, a horizontally
scrolling page, or a `hidden` that drops information on a phone that a desk user gets.

## Testing it

Nothing in the suite asserts on markup — see [testing strategy](testing-strategy.md), which rules
template assertions out because they break on every change and catch nothing. So the only gate on this
convention is looking at the page at **390px** and at desk width. Step 7 of the baseline journey in
[content review](../../.claude/skills/implement-story/references/content-review.md) is where
`/implement-story` does that, on every page a story touched.

A screen that was only ever seen at desk width has not been checked, whatever the suite says.

## See also

- [Local setup](../contributing/setup.md) — installing the frontend dependencies and compiling the
  stylesheet
- [Where code goes](app-layout.md) — why every template sits at the app root under
  `apps/warband/templates/`
