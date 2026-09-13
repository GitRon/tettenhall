# Visual identity

**Six colours, three typefaces, no radius and no shadow. Everything a screen needs is one of them, and
a screen that needs a seventh value is a conversation rather than an edit.**

The whole identity lives in the `@theme` block of `assets/css/tailwind.css`. Nothing else in the
project names a colour: the block drops Tailwind's own palette with `--color-*: initial`, so a stray
`bg-sky-100` or `text-white` does not compile at all. That is the enforcement, and it is deliberate —
an element that inherits its colour still reads, where a hue nobody chose looks fine and is wrong.

## The colours

| Token | Value | What it is for | On `ground` |
|---|---|---|---|
| `ground` | `#0c0b0a` | The page, and the default state of every surface on it | — |
| `raised` | `#131110` | Hover, and any panel that has to separate from the ground | — |
| `rule` | `#23201c` | Every hairline. 1px, never thicker | 1.21:1 |
| `ink` | `#e6dcc9` | Headings and primary text. Warm off-white, never pure white | 14.46:1 |
| `ink-muted` | `#8b8373` | Body copy and descriptions. The lowest colour text may be | 5.24:1 |
| `blood` | `#c05d46` | Something needs the player, or went wrong. Never decorative | 4.58:1 |

`ink-dim` `#6b6459` is 3.36:1 and therefore decorative only — a disabled control, a divider that wants
to be quieter than a rule. **It never carries meaning**, because a player who cannot read it has not
been told.

Every value that carries text clears WCAG AA at any size, `blood` included. That is the reason the
accent is the value it is: the thing that means "this wants you" must not be the hardest thing on the
screen to read. The one filled control pairs `ground` on `blood`, which is the same 4.58:1.

**`blood` is a reservation, not a colour in a palette.** It marks a wage bill that cannot be paid, a
man who is down, the control that advances the month. It is never a heading, never a link, never a
decoration, and never the way a screen says "this part is important". If two things on a screen are
red, at least one of them is wrong.

## The typefaces

| Token | Family | Its one job |
|---|---|---|
| `font-display` | Cinzel 500/700 | Headings, place names, buttons. **Always uppercase**, `tracking` `0.06em` and up. Never body copy |
| `font-body` | Spectral 300/400 | All prose: descriptions, events, reports. Never below 17px, never uppercase |
| `font-mono` | IBM Plex Mono 400 | Every number and label: silver, men, months, status marks. Uppercase, `text-label` with `tracking-label` |

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
  `border border-rule`.
- **Status is a 1px outlined mono tag**, never a filled pill: `border-blood` when it wants the player,
  `border-rule` otherwise. The word inside stays `ink` or `ink-muted` — the outline carries the alarm.
- **Hover moves the background to `raised`.** Not the text colour, and never the position.
- **A link is `ink` with a `rule` underline that goes `blood` on hover.** The word never changes
  colour; spending the reserved red on every link in a sentence is exactly the decorative use above.

### One filled element per screen

At most one control on a screen is filled — `bg-blood` with `text-ground` — and it is the thing the
screen exists for: **Fight!** on the fight screen, the quest's skirmish on the month page. Everything
else is outlined.

That makes a list a specific case: four buildings each with a Build button are four row actions, not
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
for when the shell itself may be what failed. They carry the same six values hand-written in an inline
`<style>`. A change to the palette has to be made in four places, and those three are the other three.

## See also

- [Responsive layout](responsive-layout.md) — the phone is the default, `md:` adds the desk
- [Local setup](../contributing/setup.md) — `yarn build:css`, and why the stylesheet has to be rebuilt
  after a template gains a class it did not use before
