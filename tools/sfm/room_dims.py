"""Fit a rectangular room's walls from a point cloud and report width/depth (scale-free ratio).
Walls = outermost strong density peak beyond the camera path (before a wide empty gap) along each Manhattan axis, so
points seen through windows (trees, neighbours) beyond the walls are ignored.
usage: PYTHONPATH=tools/sfm uv run --with numpy --with matplotlib python tools/sfm/room_dims.py <out.png> <label>=<model_dir>[:<folder_prefix>][@a-b,c-d] ...
  COLMAP model dirs use points3D observed by images under <folder_prefix>; VGGT dirs use points.npy, or
  per-frame maps from pixels.npz when frame ranges are given. @a-b,c-d keeps only frames taken inside the room
  (a camera walk through a suite visits several rooms).
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from synthetic_score_lib import image_lines, quat_to_R, load_centers


def cameras(model):
    centres, ups, ids = [], [], {}
    for l in image_lines(Path(model) / "txt"):
        f = l.split()
        R = quat_to_R(*map(float, f[1:5]))
        centres.append(-R.T @ np.array(list(map(float, f[5:8]))))
        ups.append(-R.T @ [0, 1, 0])
        ids[int(f[0])] = f[-1]
    return np.array(centres), np.array(ups), ids


def frame_no(name):
    return int(Path(name).stem.split("_")[-1])


def in_ranges(name, ranges):
    return ranges is None or any(a <= frame_no(name) <= b for a, b in ranges)


def colmap_points(model, prefix, ranges=None):
    load_centers(model)  # ensures TXT export exists
    _, _, ids = cameras(model)
    ids = {k: v for k, v in ids.items() if v.startswith(prefix) and in_ranges(v, ranges)}
    pts = []
    for l in (Path(model) / "txt" / "points3D.txt").read_text().splitlines():
        if l.startswith("#") or not l.strip():
            continue
        f = l.split()
        if sum(int(i) in ids for i in f[8::2]) >= 2:  # seen from >= 2 in-room frames
            pts.append(list(map(float, f[1:4])))
    return np.array(pts)


def fit(points, centres, ups):
    up = ups.mean(0); up /= np.linalg.norm(up)
    h = points @ up
    lo, hi = np.percentile(h, [15, 85])  # drop floor/ceiling-dominated slices
    p = points[(h > lo) & (h < hi)]
    a = np.cross(up, [1, 0, 0]); a /= np.linalg.norm(a); b = np.cross(up, a)
    P, C = np.c_[p @ a, p @ b], np.c_[centres @ a, centres @ b]
    span = np.ptp(P, axis=0).max()
    best = None
    for th in np.radians(np.arange(0, 90, 0.25)):  # Manhattan angle: sharpest wall histograms
        R = np.array([[np.cos(th), -np.sin(th)], [np.sin(th), np.cos(th)]])
        Q = P @ R.T
        score = sum(((np.histogram(Q[:, k], bins=300)[0] / len(Q)) ** 2).sum() for k in (0, 1))
        if best is None or score > best[0]:
            best = (score, R)
    R = best[1]
    Q, CQ = P @ R.T, C @ R.T
    walls = []
    for k in (0, 1):
        bins = np.linspace(Q[:, k].min(), Q[:, k].max(), 400)
        hist, edges = np.histogram(Q[:, k], bins=bins)
        hist = np.convolve(hist, np.ones(3) / 3, mode="same")
        centres_k = (edges[:-1] + edges[1:]) / 2
        found = []
        for side, inside in ((-1, CQ[:, k].min()), (1, CQ[:, k].max())):
            mask = centres_k < inside if side < 0 else centres_k > inside
            idx = np.where(mask)[0][::-1] if side < 0 else np.where(mask)[0]
            if not mask.any():  # camera path reaches past every point on this side (e.g. stood in the doorway)
                found.append(None)
                continue
            thresh = 0.25 * hist[mask].max()
            gap_bins = int(0.05 * len(hist))  # wall->outside (trees through windows) leaves an empty gap
            pos, empty = None, 0
            # outermost strong peak before the first wide empty gap, walking outward from the cameras;
            # furniture fronts are strong peaks too, but the wall lies beyond them
            for i in idx:
                empty = empty + 1 if hist[i] < 0.02 * thresh else 0
                if empty > gap_bins:
                    break
                if hist[i] >= thresh and hist[i] >= hist[max(i - 1, 0)] and hist[i] >= hist[min(i + 1, len(hist) - 1)]:
                    pos = centres_k[i]
            found.append(pos)
        walls.append(found)
    return Q, CQ, walls, span


def main():
    out = sys.argv[1]
    items = []
    for arg in sys.argv[2:]:
        label, spec = arg.split("=", 1)
        spec, _, rng = spec.partition("@")
        ranges = [tuple(map(int, r.split("-"))) for r in rng.split(",")] if rng else None
        model, _, prefix = spec.partition(":")
        c, u, ids = cameras(model)
        keep = [i for i, n in enumerate(ids.values()) if n.startswith(prefix) and in_ranges(n, ranges)]
        c, u = c[keep], u[keep]
        if prefix:  # COLMAP
            pts = colmap_points(model, prefix, ranges)
        elif ranges:  # VGGT per-frame maps, in-room frames only
            d = np.load(Path(model) / "pixels.npz")
            sel = [i for i, n in enumerate(d["names"]) if in_ranges(str(n), ranges)]
            wp, cf = d["world"][sel].reshape(-1, 3), d["conf"][sel].reshape(-1)
            wp = wp[cf > np.median(cf)]
            pts = wp[np.random.default_rng(0).choice(len(wp), min(200_000, len(wp)), replace=False)]
        else:
            pts = np.load(Path(model) / "points.npy")
        items.append((label, *fit(pts, c, u)))

    fig, axes = plt.subplots(1, len(items), figsize=(5 * len(items), 5), squeeze=False)
    print(f"{'source':<14} {'side A':>8} {'side B':>8} {'ratio':>6}  (model units; ratio = short/long)")
    for ax, (label, Q, CQ, walls, span) in zip(axes[0], items):
        ax.hexbin(Q[:, 0], Q[:, 1], gridsize=150, bins="log", cmap="Greys", mincnt=1)
        ax.plot(CQ[:, 0], CQ[:, 1], "b.", ms=3)
        for k, (w0, w1) in enumerate(walls):
            for w in (w0, w1):
                if w is not None:
                    (ax.axvline if k == 0 else ax.axhline)(w, color="r")
        if all(w is not None for pair in walls for w in pair):
            A, B = walls[0][1] - walls[0][0], walls[1][1] - walls[1][0]
            print(f"{label:<14} {A:8.3f} {B:8.3f} {min(A, B) / max(A, B):6.3f}")
            ax.set_title(f"{label}: ratio {min(A, B) / max(A, B):.3f}")
        else:
            print(f"{label:<14} wall not found on some side")
            ax.set_title(f"{label}: incomplete")
        ax.set_aspect("equal")
    fig.savefig(out, dpi=90, bbox_inches="tight")


if __name__ == "__main__":
    main()
