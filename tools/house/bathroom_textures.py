"""bathroom_textures: drawn tiles for the two upstairs bathrooms (Oct 19, changes/2026-10-19-bathrooms.json). Each PNG is ONE repeat with a
.json {"repeat_m": [w, h]} beside it (SpecGreybox.PaperMat tiles it world-space).

- hall_bath_wallpaper: the film's hall-bath paper (film 336-344, Fuller at the pedestal sink): a dark green ground with a fine gold
  trellis, white lidded tureens on a green foot alternating (half-drop) with pale-blue oval medallions holding a green sprig. Too soft
  and too oblique to cut a repeat (night, 15-20 deg off frontal), so DRAWN. Pitch: 91 px same motif to same motif across and down on
  the back wall in film 336, at 1.40 mm/px (the tile liner-to-cap 0.17 m of Marina 468 s = 122 px on the same wall) -> 0.128 m:
  DEVIATIONS 110. Marina's own paper is a red/white floral on green (her colourway; film first).
- bath_subway: white 6 x 3 in subway tile, running bond, 2 mm pale grout (film 336 / Marina 468: white tile wainscot). ASSUMED size.
- bath_hex: white 2 in hexagon floor mosaic (the film never shows the floor; Marina 457 shows a white tile floor). ASSUMED.
- bath_marble: the parents' dark green marble counter (film 4398: near-black green, pale green-grey veins).

  python3 tools/house/bathroom_textures.py   (Pillow + numpy)
"""
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

OUT = Path(__file__).resolve().parents[2] / "spec/dressing"


def save(name, im, rep):
    im.save(OUT / f"{name}.png")
    (OUT / f"{name}.json").write_text(json.dumps({"repeat_m": rep, "source": "tools/house/bathroom_textures.py"}) + "\n")


def wallpaper():
    S = 512                                    # one repeat = 0.128 m: two motifs across and down (half-drop checkerboard)
    k = 4                                      # supersample
    im = Image.new("RGB", (S * k, S * k), (38, 66, 40)); d = ImageDraw.Draw(im)
    g = S * k
    for i in range(-8, 9):                     # gold trellis, 1/8 repeat pitch, thin diagonal lines with tiny crosses
        o = i * g / 8
        d.line([(o, 0), (o + g, g)], fill=(150, 128, 64), width=k)
        d.line([(o + g, 0), (o, g)], fill=(150, 128, 64), width=k)

    def tureen(cx, cy):
        u = g / 2 / 100                        # motif units: 100 per half repeat
        d.ellipse([cx - 18 * u, cy + 8 * u, cx + 18 * u, cy + 30 * u], fill=(108, 160, 92))      # green foot/bowl
        d.rectangle([cx - 8 * u, cy + 26 * u, cx + 8 * u, cy + 34 * u], fill=(90, 140, 80))
        d.chord([cx - 30 * u, cy - 16 * u, cx + 30 * u, cy + 20 * u], 180, 360, fill=(236, 234, 228))  # white lid
        d.rectangle([cx - 30 * u, cy + 1 * u, cx + 30 * u, cy + 9 * u], fill=(226, 224, 218))
        d.ellipse([cx - 6 * u, cy - 26 * u, cx + 6 * u, cy - 14 * u], fill=(236, 234, 228))    # knob

    def medallion(cx, cy):
        u = g / 2 / 100
        d.ellipse([cx - 22 * u, cy - 30 * u, cx + 22 * u, cy + 30 * u], outline=(170, 196, 200), width=int(4 * u))
        d.ellipse([cx - 18 * u, cy - 26 * u, cx + 18 * u, cy + 26 * u], fill=(52, 92, 50))
        d.line([(cx, cy + 18 * u), (cx, cy - 16 * u)], fill=(150, 196, 120), width=int(3 * u))
        for s in (-1, 1):
            for t in (-8, 2, 12):
                d.ellipse([cx + s * 2 * u - 5 * u + s * 5 * u, cy - t * u - 3 * u, cx + s * 2 * u + 5 * u + s * 5 * u, cy - t * u + 3 * u], fill=(150, 196, 120))

    for oy in (-g, 0, g):
        for ox in (-g, 0, g):
            for (mx, my, f) in ((0.25, 0.25, tureen), (0.75, 0.75, tureen), (0.75, 0.25, medallion), (0.25, 0.75, medallion)):
                f(ox + mx * g, oy + my * g)
    im = im.filter(ImageFilter.GaussianBlur(k * 0.6)).resize((S, S), Image.LANCZOS)
    save("hall_bath_wallpaper", im, [0.128, 0.128])


def subway():
    W, H, gr = 1024, 512, 6                    # 0.305 x 0.152 m: two courses, running bond
    rng = np.random.default_rng(3)
    a = np.full((H, W, 3), 214.0)              # grout
    for row in range(2):
        for col in range(-1, 3):
            x0 = col * W // 2 + (W // 4 if row else 0); y0 = row * H // 2
            tone = 240 + rng.uniform(-4, 3)
            xs, xe = max(0, x0 + gr // 2), min(W, x0 + W // 2 - gr // 2)
            if xe > xs:
                a[y0 + gr // 2:y0 + H // 2 - gr // 2, xs:xe] = [tone, tone, tone - 3]
    im = Image.fromarray(a.clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.0))
    save("bath_subway", im, [0.305, 0.152])


def hexfloor():
    """Pointy-top hexagons, 2 in across flats; the rectangular repeat is two rows: sqrt(3) r wide, 3 r tall (r = circumradius)."""
    flats = 2.0 * 0.0254; r_m = flats / math.sqrt(3)
    W = 400; r = W / math.sqrt(3); H = int(round(3 * r))
    im = Image.new("RGB", (W, H), (150, 150, 146)); d = ImageDraw.Draw(im)
    for j in range(-1, 4):
        for i in range(-1, 3):
            cx = i * W + (W / 2 if j % 2 else 0); cy = j * 1.5 * r
            pts = [(cx + 0.93 * r * math.cos(math.pi / 2 + t * math.pi / 3), cy + 0.93 * r * math.sin(math.pi / 2 + t * math.pi / 3)) for t in range(6)]
            d.polygon(pts, fill=(238, 237, 233))
    im = im.filter(ImageFilter.GaussianBlur(0.8))
    save("bath_hex", im, [math.sqrt(3) * r_m, 3 * r_m])


def marble():
    S = 1024; rng = np.random.default_rng(7)
    y, x = np.mgrid[0:S, 0:S] / S
    n = np.zeros((S, S))
    for f in (2, 4, 8, 16, 32):                # tileable value noise from sums of periodic sines
        for _ in range(3):
            ax, ay, ph = rng.integers(-f, f + 1), rng.integers(-f, f + 1), rng.uniform(0, 6.28)
            n += np.sin(2 * math.pi * (ax * x + ay * y) + ph) / f
    v = np.abs(np.sin(2 * math.pi * (2 * x + y) + 3.0 * n))        # veins
    vein = (1 - v) ** 12
    base = np.array([18, 40, 30.0]); veinc = np.array([120, 150, 130.0])
    a = base * (1 + 0.15 * n[..., None]) + vein[..., None] * (veinc - base)
    save("bath_marble", Image.fromarray(a.clip(0, 255).astype(np.uint8)), [0.6, 0.6])


if __name__ == "__main__":
    wallpaper(); subway(); hexfloor(); marble()
    print("wrote hall_bath_wallpaper, bath_subway, bath_hex, bath_marble")
