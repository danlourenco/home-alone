"""film_wallpaper: the foyer's wallpaper as the FILM shows it (red damask on cream, green accents), one repeat cut from a near
frontal still, lighting flattened, side edges blended to wrap. User, Oct 15: "sample the real wallpaper from the movie stills from
the foyer and apply it appropriately" (Marina's paper, spec/dressing/wallpaper.png, is a brown variant).

Source: film 1170 (daylight, near frontal): the panel right of the living-room opening's casing, x 1510-1890. Its repeat by 2-D
autocorrelation of the red channel (tools in this file's history): 442 px down (peak 0.29 at (442, -5)) and a half-drop at
(224, -187) / (220, 182), so a straight repeat 442 px tall and ~370 px wide (2 x 185). Film 780 (lamplight) agrees on the motif.
The tile is cut from rows 60-502, above the brass switch plate. Scale is AUTHORED: 442 px = 0.533 m, a
standard 21 in damask repeat (no ruler of known size in the panel); the width follows the pixels.

  uv run --with numpy --with scipy --with pillow python -I tools/house/film_wallpaper.py
  -> spec/dressing/wallpaper_film.png and wallpaper_film.json ({"repeat_m": [w, h]}); foyer_dressing.py uses it when present.
"""
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "0-homealone/full/homealone-movie-screencaps.com-1170.jpg"
OUT = ROOT / "spec/dressing/wallpaper_film.png"
X0, Y0, V, HW = 1515, 60, 442, 370          # tile left column and top row, vertical repeat, horizontal repeat (px)
REPEAT_H_M = 0.533

im = np.asarray(Image.open(SRC).convert("RGB"), float)
tile = im[Y0:Y0 + V, X0:X0 + HW].copy()
# rows 60-502 lie above the brass switch plate (rows 505-605): no patching needed
lum = tile.mean(2, keepdims=True); flat = gaussian_filter(lum, (60, 60, 0))         # even out the film's light falloff
tile = tile / np.maximum(flat, 1) * lum.mean()
# the cut is one exact repeat both ways, so it wraps; soften the seams 6 px against JPEG and perspective residue
for ax in (0, 1):
    e = 6; t = np.moveaxis(tile, ax, 0); a = np.linspace(0, 1, e)[:, None, None] if ax == 0 else np.linspace(0, 1, e)[:, None, None]
    t[:e] = t[:e] * a + t[-e:][::-1][::-1] * (1 - a); tile = np.moveaxis(t, 0, ax)
m = tile.mean((0, 1)); g = tile.mean(2, keepdims=True)                              # film JPEG is muddy: lift contrast and colour
tile = (g + (tile - g) * 1.25 - m.mean()) * 1.2 + m.mean() * 1.08
Image.fromarray(np.clip(tile, 0, 255).astype(np.uint8)).resize((512, round(512 * V / tile.shape[1])), Image.LANCZOS).save(OUT)
rep = [round(REPEAT_H_M * tile.shape[1] / V, 3), REPEAT_H_M]
(OUT.with_suffix(".json")).write_text(json.dumps({"source": f"film 1170 x {X0}-{X0 + HW}, rows {Y0}-{Y0 + V}", "repeat_m": rep}) + "\n")
print(OUT, rep)
