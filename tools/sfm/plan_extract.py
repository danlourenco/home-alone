"""Top-down wall plan from a VGGT reconstruction: Manhattan-aligned wall segments (model units).
A floor-plan cell is wall when it is dense with mid-height points (30-70% of floor-to-ceiling): floors and
ceilings put nothing there, low furniture little. Runs of wall cells along each axis become segments.
usage: PYTHONPATH=tools/sfm uv run --with numpy --with matplotlib python tools/sfm/plan_extract.py <vggt_model_dir> <out_prefix> [a-b,c-d]
Writes <out_prefix>.png (density + wall mask + segments) and <out_prefix>.json (segments, up, rotation).
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from room_dims import cameras, in_ranges

model, out = Path(sys.argv[1]), sys.argv[2]
WALL_FRAC = float(__import__("os").environ.get("WALL_FRAC", "0.05"))  # fraction of the densest cells
ranges = [tuple(map(int, r.split("-"))) for r in sys.argv[3].split(",")] if len(sys.argv) > 3 else None

d = np.load(model / "pixels.npz")
sel = [i for i, n in enumerate(d["names"]) if in_ranges(str(n), ranges)]
wp, cf = d["world"][sel].reshape(-1, 3), d["conf"][sel].reshape(-1)
pts = wp[cf > np.percentile(cf, 40)]
c, u, ids = cameras(model)
keep = [i for i, n in enumerate(ids.values()) if in_ranges(n, ranges)]
c, u = c[keep], u[keep]

up = u.mean(0); up /= np.linalg.norm(up)
a = np.cross(up, [1, 0, 0]); a /= np.linalg.norm(a); b = np.cross(up, a)
h = pts @ up
floor, ceil = np.percentile(h, [2, 98])
P, C = np.c_[pts @ a, pts @ b], np.c_[c @ a, c @ b]

# Manhattan rotation: sharpest axis histograms of mid-height points.
mid = (h > floor + 0.3 * (ceil - floor)) & (h < floor + 0.7 * (ceil - floor))
best = max(np.radians(np.arange(0, 90, 0.25)), key=lambda th: sum(
    ((np.histogram((P[mid] @ np.array([[np.cos(th), np.sin(th)], [-np.sin(th), np.cos(th)]]))[:, k], bins=300)[0]
      / mid.sum()) ** 2).sum() for k in (0, 1)))
R = np.array([[np.cos(best), np.sin(best)], [-np.sin(best), np.cos(best)]])
Q, CQ = P @ R, C @ R

lo, hi = np.percentile(Q, [0.5, 99.5], axis=0)
inside = np.all((Q >= lo) & (Q <= hi), axis=1)
Q, hh = Q[inside], h[inside]
cell = (hi - lo).max() / 300
nx, ny = (np.ceil((hi - lo) / cell).astype(int) + 1)
ix, iy = ((Q - lo) / cell).astype(int).T
band = (hh > floor + 0.3 * (ceil - floor)) & (hh < floor + 0.7 * (ceil - floor))
density = np.zeros((nx, ny))
np.add.at(density, (ix[band], iy[band]), 1)
wall = density > WALL_FRAC * np.percentile(density[density > 0], 99)
# ponytail: fixed density threshold; tall wardrobes/bookcases also pass — review the overlay, tag them by hand


def runs(mask_line, min_len):
    out, start = [], None
    for i, v in enumerate(np.r_[mask_line, False]):
        if v and start is None:
            start = i
        if not v and start is not None:
            if i - start >= min_len:
                out.append((start, i - 1))
            start = None
    return out


segments = []
min_len = int(0.04 * max(nx, ny))
gap_fill = 3  # bridge tiny holes (noise), not doorways
for axis in (0, 1):
    m = wall if axis == 0 else wall.T  # axis 0: walls running along y (constant x)
    for k in range(m.shape[0]):
        line = m[max(k - 1, 0):k + 2].any(0)
        filled = line.copy()
        for s, e in runs(~line, 1):
            if e - s + 1 <= gap_fill and s > 0 and e < len(line) - 1:
                filled[s:e + 1] = True
        for s, e in runs(filled, min_len):
            segments.append((axis, k, s, e))

# Merge parallel duplicates from wall thickness: same axis, within 3 cells, overlapping extent.
merged = []
for ax, k, st, en in sorted(segments):
    for i, (mx, mk, ms, me) in enumerate(merged):
        if mx == ax and abs(k - mk) <= 3 and st <= me and en >= ms:
            merged[i] = (ax, (mk + k) / 2, min(ms, st), max(me, en))
            break
    else:
        merged.append((ax, k, st, en))

walls_out = []
for ax, k, s, e in merged:
    if ax == 0:
        p0, p1 = lo + cell * np.array([k, s]), lo + cell * np.array([k, e])
    else:
        p0, p1 = lo + cell * np.array([s, k]), lo + cell * np.array([e, k])
    walls_out.append({"from": p0.round(4).tolist(), "to": p1.round(4).tolist(), "length": float(np.linalg.norm(p1 - p0))})

Path(out + ".json").write_text(json.dumps({"up": up.tolist(), "rotation": R.tolist(), "plane_axes": [a.tolist(), b.tolist()],
                                           "floor": float(floor), "ceiling": float(ceil), "cell": float(cell),
                                           "walls": walls_out}, indent=1))
fig, axs = plt.subplots(1, 2, figsize=(14, 7))
axs[0].hexbin(Q[:, 0], Q[:, 1], gridsize=250, bins="log", cmap="Greys", mincnt=1); axs[0].set_title("all points (top-down)")
axs[1].imshow(wall.T, origin="lower", extent=(lo[0], lo[0] + nx * cell, lo[1], lo[1] + ny * cell), cmap="Greys", alpha=0.4)
for w in walls_out:
    axs[1].plot([w["from"][0], w["to"][0]], [w["from"][1], w["to"][1]], "r-", lw=2)
for ax in axs:
    ax.plot(CQ[:, 0], CQ[:, 1], "b.", ms=3); ax.set_aspect("equal")
axs[1].set_title(f"wall cells + {len(walls_out)} segments (red), cameras (blue)")
fig.savefig(out + ".png", dpi=90, bbox_inches="tight")
print(f"{len(walls_out)} wall segments; floor-to-ceiling {ceil - floor:.4f} units; -> {out}.png / .json")
