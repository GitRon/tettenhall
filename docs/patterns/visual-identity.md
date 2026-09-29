# Visual identity

**Eight colours, three typefaces, no radius and no shadow. Everything a screen needs is one of them,
and a screen that needs a ninth value is a conversation rather than an edit.**

The whole identity lives in the `@theme` block of `assets/css/tailwind.css`. Nothing else in the
project names an interface colour (the hair on a portrait is paint, see
[where this does not reach](#where-this-does-not-reach)): the block drops Tailwind's own palette with `--color-*: initial`, so a stray
`bg-sky-100` or `text-white` does not compile at all. That is the enforcement, and it is deliberate —
an element that inherits its colour still reads, where a hue nobody chose looks fine and is wrong.

## The colours

| Token | Value | What it is for | On `ground` |
|---|---|---|---|
| `ground` | `#0c0b0a` | The page, and the default state of every surface on it | — |
| `raised` | `#1a1714` | Hover, and any panel that has to separate from the ground | 1.10:1 |
| `rule` | `#23201c` | Every hairline inside a card. 1px, never thicker | 1.21:1 |
| `rule-strong` | `#3a342d` | A card's outer edge, so a box reads as a box on the ground and on `raised` | 1.60:1 |
| `ink` | `#e6dcc9` | Headings and primary text. Warm off-white, never pure white | 14.46:1 |
| `ink-muted` | `#8b8373` | Body copy and descriptions. The lowest colour text may be | 5.24:1 |
| `blood` | `#c8644d` | Something needs the player, or went wrong. Never decorative | 5.04:1 |
| `brass` | `#9c8650` | A gain, or something ready and worth having. Never decorative | 5.56:1 |

`ink-dim` `#6b6459` is 3.36:1 and therefore decorative only — a divider that wants to be quieter than a
rule, or the name on a greyed option when the reason beside it (in `ink-muted`) is what says why. Not a
disabled control's label: a refusal is meant to be read, so it wears `ink-muted` itself. **It never carries meaning**, because a player who cannot read it has not
been told.

Every value that carries text clears WCAG AA at any size, on `ground` and on `raised` alike: `ink-muted`
is 4.75:1 on `raised`, `blood` 4.58:1 and `brass` 5.05:1. That is the reason the accent is the value it
is: the thing that means "this wants you" must not be the hardest thing on the screen to read, on
whichever surface it lands. The one filled control pairs `ground` on `blood`, which is the same 5.04:1.

**`blood` is a reservation, not a colour in a palette.** It marks a wage bill that cannot be paid, a
man who is down, the control that advances the month. It is never a heading, never a link, never a
decoration, and never the way a screen says "this part is important". If two things on a screen are
red, at least one of them is wrong.

**`brass` is the second reservation, and it is kept the same way.** It says "good": a month that makes
silver, gear better than anything the men carry. It is never a heading, never a link, never a decoration,
and if two unrelated things on a screen wear it, one of them is wrong.

**A normal state is not good news.** A leader fit to march, a building that may be raised this month -
those are how things usually stand, and they read as fine by being plain `ink`. Brass on them would shout
every ordinary month, and the Month page, which carries all three, would have three brass things on it.
Brass is for a gain the player would otherwise have to work out. It is deliberately a muted brass rather than a green, which would
pull the game towards a dashboard, and deliberately only a little brighter than `blood` - `blood` is the
more saturated of the two and still reads first, so the thing that wants the player stays at least as
loud as the thing that pleases them. A brighter gold would out-shout it on every screen. The upgrade
tags the shop, stores and pub are to carry (#207) wear it too.

## The typefaces

| Token | Family | Its one job |
|---|---|---|
| `font-display` | Cinzel 500/700 | **Where the player is**: the page title (`h1`) and nothing else. Always uppercase, tracked |
| `font-body` | Spectral 300/400 | All prose, and the headings below the page title: a section (`h2`), a card (`h3`), a line of news (`h4`). Never below 17px, never uppercase |
| `font-mono` | IBM Plex Mono 400/500 | Every number and every label: silver, men, months, stat lines, status marks, column heads, button labels, the section nav. Labels uppercase, `text-label` with `tracking-label`; 500 for what the player presses or reads as a state |

**The display face means "this is where you are".** A page title, a section, a card and a button each
set in their own voice, so they stop looking alike - a card title is a label for what is in the card,
not a place, and a quest or a building name is Spectral like any other. The base layer does this for
bare `h1`-`h4`, `button` and `input[type=submit]`; a drawn control that is an `<a>` sets the mono label
at its own call site.

**Every number is mono, with its word beside it.** The resource bar reads `MEN 3 · SILVER 1000`, a
warrior's line reads `LEVEL 1 · 94 XP · WAGE 0 · HEALTH 16/16`, and a figure set in prose or behind
nothing but an icon has to be learned before it can be read. The word is the quiet label in
`ink-muted`, the figure the loud part in `ink`.

`--text-label` (12px) and `--tracking-label` (`0.1em`) are the mono label, tokenised because every
count, status tag and column head in the game is set in them. That is the smallest the mono reads
comfortably in uppercase on this ground; wider tracking at a smaller size breaks a word into letters.

**A control or a status is the label at 500.** Buttons, the row action, the row menu and the
outlined tag that names a state (*Unconscious*, *Ready*, *No upgrade*) wear the heavier cut, because
the 400 at this size thins to grey hairlines on the dark ground, and those are the words the player
acts on. Column heads, the quiet word beside a figure and the fact boxes that pair one with a figure
(`LEVEL 2`, `LOOT HIGH`) stay at 400.

`--text-figure` (13px) is a figure standing in a column on its own - a level, a wage, a health
reading - one step above the label, so the number is the loud part and the word naming it the quiet
one. Not uppercased: there is nothing in a figure to capitalise, and a die roll keeps its `d`.

The three are self-hosted out of `node_modules` via `@fontsource`, linked from `base.html`, and only at
the weights above. A face loaded at a weight nothing sets is bytes on every page load for nothing.

**`html` stays at 16px.** Tailwind's spacing scale is rem-based, so a 17px root would rescale every
padding, margin and width in the project by six percent to buy one step of body copy. The 17px floor is
set on `body`.

## Surface

- **Radius is 0.** The `--radius-*` scale is dropped, so `rounded-lg` is not a utility that exists.
- **No shadows, no gradients, no glows, no texture images.** `--shadow-*` is dropped too.
- **Separation comes from a 1px rule and space**, not from a box. A card is `bg-ground` with
  `border border-rule-strong`; the hairlines inside it are `rule`.
- **Status is a 1px outlined mono tag**, never a filled pill, and **only for the exception**: a man
  who can fight, a quest that is open, carries no tag, because a tag on five rows out of six is the
  loudest thing in the list while saying nothing. The word inside stays `ink` — the outline
  carries the meaning: `border-blood` when it wants the player, `border-brass` when it is a gain or
  better than what is there, `border-ink` when the thing it marks is whole and ready, `border-rule`
  when it is merely a fact. A figure that is good news takes `text-brass` rather than a tag.
- **Hover moves the background to `raised`.** Not the text colour, and never the position.
- **Except on the one filled control, which answers with its rule instead** — `hover:border-ink`, fill
  untouched. A filled button that drops to the dark ground on hover reads as the button leaving rather
  than as the pointer arriving, and it is the one thing on the screen that must not flicker.
- **A link is `ink` with a `rule` underline that goes `blood` on hover.** The word never changes
  colour; spending the reserved red on every link in a sentence is exactly the decorative use above.

### One filled element per screen

At most one control on a screen is filled — `bg-blood` with `text-ground` — and it is the thing the
screen exists for: **Fight!** on the fight screen, the control in the month band — *Finish month*, or
the fight holding it up while one is unresolved — on the month page. Everything
else is outlined.

### The row action

Every other control that acts on one thing - *Accept* on a quest, *Buy*, *Sell*, *Recruit*, *Build*, the
Month page's way into each section - is the **row action**, the `row-action` utility in
`assets/css/tailwind.css`: the mono label in `ink`, a `rule-strong` outline, the `raised` hover, one size.
It sits at the right of its row or of its card's footer, as a control. Never as bare text, and never
several joined by slashes in a sentence.

**It is never `blood`.** Five buildings each with a Build button are five row actions, and five red
outlines on one screen is four red things too many - the reserved colour would stop meaning anything on
exactly the screens where the player compares. The red stays with the one filled control and with what
has gone wrong.

**A disabled row action stays readable.** `row-action` on a `disabled` button (or one with
`aria-disabled="true"`) drops to `ink-muted` with a `rule` outline, and its label is the reason: *Build a
hall to feast*, *Already feasted this month*, *Your leader stays*. It is quieter than the controls that
would work, but it is text the player is meant to read, so it never goes to `ink-dim` - and never
`blood`, the colour of a control that wants you.

A class written into the stylesheet is the exception here, and this is why it is one: the row action is
on thirty templates, and the same utility list copied thirty times drifts into four controls that each
look a little different, which a player reads as four kinds of thing.

### The row menu

Where a table line has actions - *Dismiss* on the roster, *Recruit* and *Enslave* in the player's
cells - they sit behind three dots at the end of the line, in the `row-menu` popover, rather than as
row actions on every line. Six identical outlined controls down the right edge are the loudest column
in the table, and a table is read down its columns before anything on a line is pressed. Each line of the menu is `row-menu-item`: the mono label at 500, `raised` on hover, and a
refusal disabled in `ink-muted` with its reason underneath, the same as a disabled row action.

Anything that costs silver and cannot be taken back asks first, inside the menu: the item turns the
menu into the question and two row actions, and the safe answer takes the focus. Never `confirm()`,
which is the browser's look rather than the game's.

## The icons

The hand-drawn set in `static/svg/icons/` is painted as a **mask**, not fetched as an image:
`common/components/svg_icon.html` renders a span whose `background-color` is `currentColor` with the
drawing punched out of it, so every icon takes the colour of the text beside it. See
`static/css/icons.css`.

Two things follow, and both bite silently:

- **The mask reads alpha, so every opaque shape in the file is part of the glyph.** A full-bleed
  background rectangle masks in as a solid square with the drawing invisible inside it. A new icon
  arrives with that rectangle removed.
- **The fill colour in the file is ignored.** There is no point setting one.

Font Awesome covers the UI verbs and inherits `color` in the ordinary way. Which of the two sets owns
which concept is not settled — see #64.

## Where this does not reach

**Hair colours** (`apps/warband/fixtures/haircolour.json`) are the one colour named outside the `@theme`
block. They are pigment for a painting, not colours of the interface: they reach the page as an inline
custom property on a portrait layer and colour nothing else. A hair colour is never a text, rule or status
colour, and a UI colour is never added to that fixture - see [portraits](portraits.md).

`403.html`, `404.html` and `500.html` do not extend `base.html`, because they are what Django reaches
for when the shell itself may be what failed. They carry the values they use - `ground`, `rule`, `ink`,
`ink-muted` and `blood` - hand-written in an inline `<style>`. A change to one of those has to be made in
four places, and those three are the other three.

## Design skills

A design skill brings its own defaults: palettes, type scales, motion and radius. This document overrides
them. `impeccable` is in the repository to review screens against these rules, not to choose new ones -
see [AGENTS.md](../../AGENTS.md) for which of its commands apply.

## See also

- [Responsive layout](responsive-layout.md) — the phone is the default, `md:` adds the desk
- [Local setup](../contributing/setup.md) — `yarn build:css`, and why the stylesheet has to be rebuilt
  after a template gains a class it did not use before
