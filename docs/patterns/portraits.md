# Portraits

**A warrior's face is drawn once, when he is generated, and stored.** Five columns on `Warrior` hold it -
`portrait_face`, `portrait_hair`, `portrait_beard`, `hair_colour`, `beard_colour` - written by
`draw_portrait()` (`apps/warband/warrior/services/portrait.py`) inside `BaseWarriorGenerator.process()`.
Nothing derives a look from an id or rolls one at render time: a man with one face on the roster and
another in the pub is two men to the player, which is the same reason `nickname_variant` is a column.

Hair and beard are empty for a bald or clean-shaven man. The face is empty only for a man generated before
faces were drawn: he keeps the silhouette icon, because no migration can give him a face - the pieces are
fixtures, and fixtures are loaded after the migrations run.

## The pieces

`PortraitPiece` (`apps/warband/warrior/models/portrait_piece.py`) is reference data in
`apps/warband/fixtures/portraitpiece.json`, and `HairColour` sits beside it in `haircolour.json`. Faces are
shared by every culture.

| Kind | Image | Placement |
|---|---|---|
| Face | an opaque crop, 198×204, `static/img/warrior/portrait/face/NN.png` | always 0 / 0 / 1: the face *is* the canvas |
| Hair, beard | a transparent greyscale value map, `static/img/warrior/portrait/{hair,beard}/NN.png` | `left`, `top`, `width` as fractions of the face canvas |

The placement is stored per piece because the pieces were cut from one contact sheet at differing scales,
and no single rule seats them all: a chin beard and a braided one hold a different share of their own
sprite above the jaw. It holds across faces, because the bases register within a few pixels of each other.

## Colour

Hair and beards are coloured in the browser by **multiply** - value × colour - in `static/css/portrait.css`.
Two things follow:

- **A value map has to be drawn light**: highlights near white, midtones around 180, shadows not below 100.
  A dark map turns every colour it is given into near-black, and a grey beard becomes unreachable.
- **A map is judged on mid-grey, never on `ground`.** Against the near-black page a far too dark map looks
  exactly right.

Hair colours are the one place outside the `@theme` block that names a colour, see
[visual identity](visual-identity.md#where-this-does-not-reach).

## Crops

`warrior/components/warrior_portrait.html` takes `crop`:

- `card` - head and neck in the 40px slot of every list. One crop box for all faces. At that size colour
  carries almost the whole signal and the face almost none.
- `full` - the whole canvas, on the warrior's own page.

## Adding or moving a piece

1. Cut or export it into `static/img/warrior/portrait/<kind>/NN.png`, following the value range above.
2. Add its row to `portraitpiece.json`.
3. Place it with the alignment page - `python tools/portrait_alignment/serve.py`, then
   http://127.0.0.1:8765/ - which shows the piece over every face and at card size, and writes
   `left` / `top` / `width` straight into the fixture.
4. `loaddata portraitpiece`.

The tool and the per-piece placement go away once every layer is exported on one canvas, see #362.
