"""Metric scale from a door's height measured in VGGT's per-pixel 3D map.
For each (frame, column, top guess, bottom guess): snap each edge to the strongest vertical intensity
change within +-8 px, read the 3D points there, and take their separation along 'up' (median over 5
neighbouring columns). Reports door height in model units, the metres-per-unit for an assumed door
height, floor-to-ceiling height, and room sides from room_dims.py.
usage: sfm-work/.venv/bin/python tools/sfm/door_scale.py <vggt_model_dir> <side_a> <side_b> <out.png> idx:x:ytop:ybot ...
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

model, side_a, side_b, out = Path(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
specs = [tuple(map(int, s.split(":"))) for s in sys.argv[5:]]
d = np.load(model / "pixels.npz")
images, world, conf = d["images"], d["world"], d["conf"]


def quat_to_R(w, x, y, z):
    return np.array([[1-2*(y*y+z*z), 2*(x*y-w*z), 2*(x*z+w*y)],
                     [2*(x*y+w*z), 1-2*(x*x+z*z), 2*(y*z-w*x)],
                     [2*(x*z-w*y), 2*(y*z+w*x), 1-2*(x*x+y*y)]])


body = [l for l in (model / "txt" / "images.txt").read_text().split("\n") if not l.startswith("#")]
ups = [-quat_to_R(*map(float, h.split()[1:5])).T @ [0, 1, 0] for h in body[::2] if h.strip()]
up = np.mean(ups, axis=0); up /= np.linalg.norm(up)


def snap(gray, x, y):
    col = gray[:, x - 1:x + 2].mean(1)
    grad = np.abs(np.diff(col))
    lo, hi = max(y - 8, 0), min(y + 8, len(grad) - 1)
    return lo + int(np.argmax(grad[lo:hi]))


heights, tiles = [], []
for idx, x, yt, yb in specs:
    gray = images[idx].astype(np.float32).mean(2)
    t, b = snap(gray, x, yt), snap(gray, x, yb)
    per_col = [abs((world[idx, b, c] - world[idx, t + 1, c]) @ up) for c in range(x - 2, x + 3)]
    h = float(np.median(per_col))
    heights.append(h)
    print(f"frame {idx}: column {x}, top edge y={t} (guess {yt}), floor y={b} (guess {yb}), "
          f"door height {h:.4f} units (cols spread {np.ptp(per_col):.4f}), conf {conf[idx, t, x]:.1f}/{conf[idx, b, x]:.1f}")
    im = Image.fromarray(images[idx]).resize((1036, 588)); dr = ImageDraw.Draw(im)
    for y, c in ((t, "red"), (b, "lime")):
        dr.line([(2 * (x - 25), 2 * y), (2 * (x + 25), 2 * y)], fill=c, width=3)
    dr.line([(2 * x, 2 * t), (2 * x, 2 * b)], fill="yellow", width=2)
    tiles.append(im)
sheet = Image.new("RGB", (1036, 588 * len(tiles)))
for k, im in enumerate(tiles):
    sheet.paste(im, (0, 588 * k))
sheet.save(out)

door = float(np.median(heights))
pts = np.load(model / "points.npy") @ up
hist, edges = np.histogram(pts, bins=200)
mid = len(hist) // 2
floor_u = edges[np.argmax(hist[:mid])]; ceil_u = edges[mid + np.argmax(hist[mid:])]
print(f"\ndoor height: median {door:.4f} units over {len(heights)} frames, spread {np.ptp(heights) / door:.1%}")
print(f"floor-to-ceiling (point histogram peaks): {abs(ceil_u - floor_u):.4f} units")
print(f"{'assumed door':>14} {'m/unit':>7} {'side A m':>9} {'side B m':>9} {'ceiling m':>9}")
for inches in (78, 80, 84):
    m = inches * 0.0254 / door
    print(f"{inches:>11} in {m:7.3f} {side_a * m:9.2f} {side_b * m:9.2f} {abs(ceil_u - floor_u) * m:9.2f}")
