"""kevin_wallpaper: Kevin and Jeff's room paper (TRIAL Oct 18, changes/2026-10-18-kevin-room.json).

Film 296/301 (the packing night, the only film shots of the room): a white ground with small scattered sprig/dot motifs in muted
green, rose-peach and gold on a regular half-drop. The production still of the same set (Marina Part 2 335 s) shows the same paper
sharp: rows of small multicolour dots (green, yellow, red, a little blue), spacing ~4.7 cm (16.5 px against the 0.74 m window casing,
259 px: ASSUMED casing 0.60 + 2 x 0.07). Marina's CG paper is red dots on white (her colourway). The film's is too soft to cut a
repeat from (film_wallpaper.py needs a frontal sharp wall), so the paper is DRAWN to those numbers: DEVIATIONS 95.

  uv run --with numpy --with pillow python -I tools/house/kevin_wallpaper.py
  -> spec/dressing/kevin_wallpaper.png + .json (repeat_m), read by SpecGreybox through finishes.json kevin_jeff_room "paper"
  -> spec/dressing/kevin_quilt.png (film 303/296: the lower bunk's quilt, red and green sawtooth rows on white) and
     spec/dressing/kevin_gingham.png (film 296 / Marina 355-365: green gingham curtains), each with its .json repeat_m; SpecGreybox.Kevin
"""
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "spec/dressing/kevin_wallpaper.png"
CELL_M, N = 0.047, 4                   # dot spacing (set still), cells per repeat
PX = 128                               # px per cell
GROUND = (232, 229, 220)               # off-white, the house's trim ground (as Buzz's paper)
# film 296 motif colours (sRGB, muted by the film stock) + the set still's blue, one per lattice site in a fixed shuffle
COLS = [(122, 150, 104), (214, 140, 120), (206, 172, 92), (122, 150, 104), (120, 146, 182), (214, 140, 120), (206, 172, 92), (176, 96, 92)]


def tile():
    S = PX * N * 2                     # draw at 2x, then downsample (soft edges as printed paper)
    im = Image.new("RGB", (S, S), GROUND); d = ImageDraw.Draw(im)
    k = 0
    for j in range(N):
        for i in range(N):
            for half in (0, 1):        # half-drop: a second site in each cell's centre
                cx = (i + 0.5 * half) * 2 * PX + PX * 0.5
                cy = (j + 0.5 * half) * 2 * PX + PX * 0.5
                c = COLS[(k * 3 + j) % len(COLS)]; k += 1
                r = 0.0028 / CELL_M * 2 * PX           # 5.6 mm motif
                for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0)):   # a four-petal sprig
                    d.ellipse([cx + dx * r * 0.7 - r * 0.6, cy + dy * r * 0.7 - r * 0.6, cx + dx * r * 0.7 + r * 0.6, cy + dy * r * 0.7 + r * 0.6], fill=c)
                d.ellipse([cx - r * 0.4, cy - r * 0.4, cx + r * 0.4, cy + r * 0.4], fill=tuple(int(v * 0.85) for v in c))
    im = im.filter(ImageFilter.GaussianBlur(1.2)).resize((PX * N, PX * N), Image.LANCZOS)
    a = np.asarray(im).astype(float)
    a += np.random.default_rng(7).normal(0, 1.5, a.shape)          # paper grain
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


def quilt(px=512):
    """film 303: bold red sawtooth (flying-geese) rows on white; film 296: green blocks between them. Two rows per repeat."""
    im = Image.new("RGB", (px, px), (236, 232, 222)); d = ImageDraw.Draw(im)
    n, h = 6, px // 4
    for row, (col, y0) in enumerate((((178, 30, 36), 0), ((40, 112, 64), px // 2))):
        for k in range(n):
            x0 = k * px / n
            d.polygon([(x0, y0 + h), (x0 + px / n / 2, y0), (x0 + px / n, y0 + h)], fill=col)
        d.rectangle([0, y0 + h + 6, px, y0 + h + 14], fill=col)
    return im.filter(ImageFilter.GaussianBlur(0.8))


def gingham(px=256):
    """green gingham: white, mid green where one band crosses, dark green where two cross; two checks per repeat"""
    a = np.zeros((px, px, 3)); band = (np.arange(px) // (px // 2)) == 0
    g, w, dk = np.array([150, 186, 140]), np.array([238, 238, 228]), np.array([82, 128, 84])
    for y in range(px):
        for_x = band
        a[y] = np.where(for_x[:, None] & band[y], dk, np.where(for_x[:, None] | band[y], g, w))
    return Image.fromarray(a.astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6))


def save(img, name, rep, src):
    out = ROOT / f"spec/dressing/{name}.png"; img.save(out)
    out.with_suffix(".json").write_text(json.dumps({"source": src, "repeat_m": [rep, rep]}, indent=1))
    print("wrote", out, rep)


if __name__ == "__main__":
    save(quilt(), "kevin_quilt", 0.30, "drawn to film 303 (red sawtooth rows on white) and 296 (green blocks): the lower bunk's quilt; tools/house/kevin_wallpaper.py")
    save(gingham(), "kevin_gingham", 0.05, "drawn to film 296 (green gingham panel behind the ladder) and Marina 355-365 (green check panels); 2.5 cm checks AUTHORED")
    t = tile()
    assert t.size == (PX * N, PX * N) and t.getpixel((1, 1))[0] > 200, "ground must stay white"
    t.save(OUT)
    rep = round(CELL_M * N, 4)
    OUT.with_suffix(".json").write_text(json.dumps({"source": "drawn to film 296/301 colours + the set still (Marina 335 s) lattice; tools/house/kevin_wallpaper.py",
                                                    "repeat_m": [rep, rep], "ruler": "set still window casing 0.74 m ASSUMED (0.60 + 2 x 0.07)"}, indent=1))
    print("wrote", OUT, rep)
