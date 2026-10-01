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

Four rules follow from the default:

- **No fixed width is ever unprefixed.** A `w-96` or a `min-w-*` without an `md:` in front of it is a
  horizontal scrollbar on a phone. Widths belong behind `md:`; the phone gets `w-full`.
- **A grid starts at one column.** `grid grid-cols-1 md:grid-cols-3`, never `grid-cols-3` alone.
- **A table has a portrait form**, and which one depends on its shape - see [tables](#tables).
- **Type has a phone size too.** A display size is a width like any other: one word of 36px Cinzel caps
  is wider than a phone. The page title is set small in the base layer of `assets/css/tailwind.css` and
  grows at `md:`, and it may break inside a word - a heading that can hold a player-visible name
  cannot promise the name fits.

## Tables

Every table in the project is one of three shapes, and each shape has one answer on a phone.

| Shape | Examples | On a phone |
|---|---|---|
| **A fact sheet**: label and value, or at most three short columns | a warrior's page, the attack form, current costs, the transactions ledger | The table as it is. It fits the screen, so there is nothing to change and no scroll box. |
| **A list**: one row per thing, five to seven columns | rivals, savegames, skirmishes, training progress | `table-stack` on the `<table>`: each row becomes a record, each cell a line led by its column name. |
| **A ledger**: a row per man, a dozen columns | the roster, the captives | `table-stack`, plus a grid on the row: the name across the top, short figures two to a line, gauges and gear one to a line. |

`table-stack` lives in `assets/css/tailwind.css`. Below `md:` it hides the column heads (they are
still read out) and prints each cell's `data-label` in front of it, so a cell is labelled by giving it
the same word as its column head: `<td data-label="Culture">`. A cell that needs no lead - the name
of the thing, its action - has no `data-label`. From `md:` up it does nothing.

Its own rules sit under `:where()`, so a row or a cell styles itself with ordinary `max-md:` utilities
on top of it - which is how the ledger lays its row out as a grid.

A ledger is wider than a narrow desk too, so it keeps a scroll box there, with its `min-w-*` behind
`md:`.

## When one column is not enough

Some screens do not have a portrait form. The three-panel fight screen is the one in this project:
stacked, it puts the battle report *between* the two warbands, so the panel read every round is the
one scrolled past twice.

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
