"""living_chintz: Marina 418's floral armchair/ottoman fabric, drawn as a tileable 512 px chintz (olive-green ground, cream
five-petal blossoms, red buds, dark leaves; colours by eye from the frame). Read by hifi_living_props.py.

  uv run --with pillow --with numpy python -I tools/house/living_chintz.py  -> sfm-work/living_fabric/chintz.png
"""
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

OUT = Path(__file__).resolve().parents[2] / "sfm-work/living_fabric/chintz.png"
N = 512
rng = np.random.default_rng(418)
im = Image.new("RGB", (N, N), (68, 78, 44)); d = ImageDraw.Draw(im)


def wrap(fn, x, y):   # draw at the 9 periodic copies so the tile wraps
    for dx in (-N, 0, N):
        for dy in (-N, 0, N):
            fn(x + dx, y + dy)


for _ in range(110):   # leaves
    x, y = rng.uniform(0, N, 2); a = rng.uniform(0, math.pi); L = rng.uniform(10, 22)
    wrap(lambda X, Y: d.line([(X - L * math.cos(a), Y - L * math.sin(a)), (X + L * math.cos(a), Y + L * math.sin(a))], fill=(50, 60, 30), width=5), x, y)
for _ in range(48):    # cream blossoms
    x, y = rng.uniform(0, N, 2); r = rng.uniform(10, 15); a0 = rng.uniform(0, 6.3)

    def blossom(X, Y):
        for k in range(5):
            a = a0 + k * 2 * math.pi / 5; px, py = X + r * 0.7 * math.cos(a), Y + r * 0.7 * math.sin(a)
            d.ellipse([px - r * 0.55, py - r * 0.55, px + r * 0.55, py + r * 0.55], fill=(214, 200, 160))
        d.ellipse([X - 3, Y - 3, X + 3, Y + 3], fill=(170, 140, 70))
    wrap(blossom, x, y)
for _ in range(50):    # red buds
    x, y = rng.uniform(0, N, 2); r = rng.uniform(6, 10)
    wrap(lambda X, Y: (d.ellipse([X - r, Y - r, X + r, Y + r], fill=(140, 30, 32)), d.ellipse([X - r * 0.4, Y - r * 0.4, X + r * 0.4, Y + r * 0.4], fill=(190, 70, 60))), x, y)
OUT.parent.mkdir(parents=True, exist_ok=True)
im.filter(ImageFilter.GaussianBlur(0.8)).save(OUT)
print("wrote", OUT)
