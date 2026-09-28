"""
Cut the portrait contact sheet into separate layers for the alignment page.

The sheet is one 1536x1024 raster: a 4x4 grid of bare faces, a 4x3 grid of hairstyles and a 4x3 grid
of beards, all on a near-black ground. Faces are cut as opaque crops of one uniform size, so every face
shares one canvas. Hair and beards are keyed off the ground into transparent greyscale value maps and
lifted into the light range multiply needs: shadows at 100, highlights at 245.

Pillow and numpy are not project dependencies, so run it through uv:

    uv run --no-project --with pillow --with numpy python tools/portrait_alignment/cut_sheet.py <sheet.png>
"""

import json
import sys
from collections.abc import Iterator
from pathlib import Path

import numpy as np
from PIL import Image

OUT = Path(__file__).resolve().parents[2] / "static" / "img" / "warrior" / "portrait"
MANIFEST = Path(__file__).resolve().parent / "pieces.json"

FACE_X = [44, 247, 451, 654, 853]
FACE_Y = [72, 281, 494, 708, 909]
HAIR_X = [899, 1055, 1210, 1363, 1510]
HAIR_Y = [52, 191, 334, 476]
BEARD_X = [899, 1055, 1210, 1362, 1510]
BEARD_Y = [537, 657, 772, 898]

# Grid lines and the cell number in each top-left corner are not part of the drawing.
INSET = 2
LABEL_BOX = (34, 30)

FACE_SIZE = (198, 204)

# Luminance band over which a sprite fades from ground to fully opaque.
KEY_LOW, KEY_HIGH = 15.0, 32.0
VALUE_SHADOW, VALUE_HIGHLIGHT = 100.0, 245.0


def cells(*, xs: list[int], ys: list[int]) -> Iterator[tuple[int, int, int, int]]:
    for row in range(len(ys) - 1):
        for col in range(len(xs) - 1):
            yield xs[col] + INSET, ys[row] + INSET, xs[col + 1] - INSET, ys[row + 1] - INSET


def blank_label(*, cell: np.ndarray) -> np.ndarray:
    cell = cell.copy()
    ground = np.median(cell[-12:, -12:].reshape(-1, cell.shape[2]), axis=0)
    cell[: LABEL_BOX[1], : LABEL_BOX[0]] = ground
    return cell


def head_box(*, face: np.ndarray) -> tuple[int, int, int, int]:
    """Bounding box of the bare skull: skin-coloured pixels above the jaw."""
    r, g, b = (face[..., i].astype(float) for i in range(3))
    skin = (r > 90) & (g > 60) & (r - b > 25) & (g > 0.55 * r)
    rows = np.where(skin.sum(axis=1) > 3)[0]
    top = int(rows[0])
    upper = skin[top : top + 110]
    cols = np.where(upper.sum(axis=0) > 2)[0]
    return int(cols[0]), top, int(cols[-1] - cols[0] + 1), 165


def value_map(*, cell: np.ndarray) -> Image.Image:
    lum = cell[..., :3].astype(float).mean(axis=2)
    alpha = np.clip((lum - KEY_LOW) / (KEY_HIGH - KEY_LOW), 0.0, 1.0)
    solid = alpha > 0.5
    low, high = np.percentile(lum[solid], [2, 98])
    value = VALUE_SHADOW + (np.clip(lum, low, high) - low) / (high - low) * (VALUE_HIGHLIGHT - VALUE_SHADOW)
    ys, xs = np.where(alpha > 0.02)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    grey = value[y0:y1, x0:x1].round().astype(np.uint8)
    a = (alpha[y0:y1, x0:x1] * 255).round().astype(np.uint8)
    return Image.fromarray(np.dstack([grey, grey, grey, a]), "RGBA")


def main(*, sheet_path: str) -> None:
    sheet = np.asarray(Image.open(sheet_path).convert("RGB"))
    manifest = {"face_size": FACE_SIZE, "faces": [], "hair": [], "beards": []}

    (OUT / "face").mkdir(parents=True, exist_ok=True)
    for number, (x0, y0, _x1, _y1) in enumerate(cells(xs=FACE_X, ys=FACE_Y), start=1):
        face = blank_label(cell=sheet[y0 : y0 + FACE_SIZE[1], x0 : x0 + FACE_SIZE[0]])
        name = f"{number:02d}.png"
        Image.fromarray(face, "RGB").save(OUT / "face" / name, optimize=True)
        manifest["faces"].append({"id": number, "src": f"face/{name}", "head": head_box(face=face)})

    for kind, xs, ys in (("hair", HAIR_X, HAIR_Y), ("beards", BEARD_X, BEARD_Y)):
        folder = "hair" if kind == "hair" else "beard"
        (OUT / folder).mkdir(parents=True, exist_ok=True)
        for number, (x0, y0, x1, y1) in enumerate(cells(xs=xs, ys=ys), start=1):
            sprite = value_map(cell=blank_label(cell=sheet[y0:y1, x0:x1]))
            name = f"{number:02d}.png"
            sprite.save(OUT / folder / name, optimize=True)
            manifest[kind].append({"id": number, "src": f"{folder}/{name}", "size": sprite.size})

    MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"{len(manifest['faces'])} faces, {len(manifest['hair'])} hair, {len(manifest['beards'])} beards")


if __name__ == "__main__":
    main(sheet_path=sys.argv[1])
