# Visual identity

**Eight colours, three typefaces, no radius and no shadow. Everything a screen needs is one of them,
and a screen that needs a ninth value is a conversation rather than an edit.**

The whole identity lives in the `@theme` block of `assets/css/tailwind.css`. Nothing else in the
project names a colour: the block drops Tailwind's own palette with `--color-*: initial`, so a stray
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

`ink-dim` `#6b6459` is 3.36:1 and therefore decorative only — a disabled control, a divider that wants
to be quieter than a rule. **It never carries meaning**, because a player who cannot read it has not
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
silver, a leader fit to march, a building that may be raised this month, gear better than anything the
men carry. It is never a heading, never a link, never a decoration, and if two unrelated things on a
screen wear it, one of them is wrong. It is deliberately a muted brass rather than a green, which would
pull the game towards a dashboard, and deliberately only a little brighter than `blood` - `blood` is the
more saturated of the two and still reads first, so the thing that wants the player stays at least as
loud as the thing that pleases them. A brighter gold would out-shout it on every screen. The upgrade
tags the shop, stores and pub are to carry (#207) wear it too.

## The typefaces

| Token | Family | Its one job |
|---|---|---|
| `font-display` | Cinzel 500/700 | **Where the player is**: the page title (`h1`) and nothing else. Always uppercase, tracked |
| `font-body` | Spectral 300/400 | All prose, and the headings below the page title: a section (`h2`), a card (`h3`), a line of news (`h4`). Never below 17px, never uppercase |
| `font-mono` | IBM Plex Mono 400 | Every number and every label: silver, men, months, stat lines, status marks, column heads, button labels, the section nav. Uppercase, `text-label` with `tracking-label` |

**The display face means "this is where you are".** A page title, a section, a card and a button each
set in their own voice, so they stop looking alike - a card title is a label for what is in the card,
not a place, and a quest or a building name is Spectral like any other. The base layer does this for
bare `h1`-`h4`, `button` and `input[type=submit]`; a drawn control that is an `<a>` sets the mono label
at its own call site.

**Every number is mono, with its word beside it.** The resource bar reads `MEN 3 · SILVER 1000`, a
warrior's line reads `LEVEL 1 · 94 XP · WAGE 0 · HEALTH 16/16`, and a figure set in prose or behind
nothing but an icon has to be learned before it can be read. The word is the quiet label in
`ink-muted`, the figure the loud part in `ink`.

`--text-label` (11px) and `--tracking-label` (`0.16em`) are the mono label, tokenised because every
count, status tag and column head in the game is set in them.

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
- **Status is a 1px outlined mono tag**, never a filled pill. The word inside stays `ink` — the outline
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

That makes a list a specific case: five buildings each with a Build button are five row actions, not
four primary ones, so they are outlined (`border-blood bg-transparent text-ink`). **A disabled control
is never `blood` in any form** — it wears `border-rule` and `ink-dim`, because a control that refuses
must not wear the colour reserved for one that wants you.

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

`403.html`, `404.html` and `500.html` do not extend `base.html`, because they are what Django reaches
for when the shell itself may be what failed. They carry the values they use - `ground`, `rule`, `ink`,
`ink-muted` and `blood` - hand-written in an inline `<style>`. A change to one of those has to be made in
four places, and those three are the other three.

## See also

- [Responsive layout](responsive-layout.md) — the phone is the default, `md:` adds the desk
- [Local setup](../contributing/setup.md) — `yarn build:css`, and why the stylesheet has to be rebuilt
  after a template gains a class it did not use before
