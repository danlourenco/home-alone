"""RESULT (Oct 15): NOT USABLE. Both models fail their checks: all directions mixed folded the front wall onto the
picture wall (damask); the back-only model puts 2677 and 10671 at one camera position and its two rear-door rulers
disagree by 28%. Kept as a record and for a retry with masked wallpaper. The film's layout is taken from the
single-frame, scale-free readings in foyer_film.py instead.

Measure the film's foyer in its own 3D reconstruction (tools/house/film_foyer_sfm.py; COLMAP model of 92 film frames).

Surfaces are fitted as planes to the reconstruction's own points: a region drawn in ONE frame selects the 3D points that
frame observed there; RANSAC fits the plane. A feature on a known surface is then a pixel's ray meeting that plane (one
frame is enough). The floor plane gives 'up'; scale comes from an 80 in door, checked against a second door.
usage: uv run --with numpy python -I tools/house/film_foyer_measure.py
"""
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
# the back-facing shots only (film_foyer_sfm.py --back): with all directions mixed the damask folded front onto back
M = ROOT / "sfm-work/film-foyer-back/sparse/1-txt"


def load():
    cams = {}
    for l in (M / "cameras.txt").read_text().splitlines():
        if l and not l.startswith("#"):
            p = l.split(); cams[int(p[0])] = tuple(map(float, p[4:]))           # SIMPLE_RADIAL: f, cx, cy, k
    pts = {}
    for l in (M / "points3D.txt").read_text().splitlines():
        if l and not l.startswith("#"):
            p = l.split(); pts[int(p[0])] = np.array(list(map(float, p[1:4])))
    imgs = {}
    L = [l for l in (M / "images.txt").read_text().splitlines() if not l.startswith("#")]
    for a, b in zip(L[0::2], L[1::2]):
        p = a.split(); q = np.array(list(map(float, p[1:5]))); t = np.array(list(map(float, p[5:8])))
        w, x, y, z = q
        R = np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                      [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                      [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
        obs = np.array(list(map(float, b.split()))).reshape(-1, 3) if b.strip() else np.zeros((0, 3))
        imgs[p[9].split("/")[-1][:5].lstrip("0")] = {"R": R, "t": t, "cam": cams[int(p[8])], "obs": obs}
    return imgs, pts


def ray(img, u, v):
    """World ray (origin, unit direction) through pixel (u, v), undistorting SIMPLE_RADIAL."""
    f, cx, cy, k = img["cam"]
    xd, yd = (u - cx) / f, (v - cy) / f; x, y = xd, yd
    for _ in range(20):
        r2 = x * x + y * y; x, y = xd / (1 + k * r2), yd / (1 + k * r2)
    d = img["R"].T @ np.array([x, y, 1.0]); o = -img["R"].T @ img["t"]
    return o, d / np.linalg.norm(d)


def inside(poly, x, y):
    c = np.zeros(len(x), bool)
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        cr = (y1 > y) != (y2 > y)
        with np.errstate(divide="ignore", invalid="ignore"):
            c ^= cr & (x < x1 + (y - y1) * (x2 - x1) / (y2 - y1))
    return c


def plane(imgs, pts, frame, poly, tol=0.02, seed=0):
    """RANSAC plane (n, d with n.x = d) through the 3D points that `frame` observed inside pixel polygon `poly`."""
    o = imgs[frame]["obs"]; m = inside(poly, o[:, 0], o[:, 1]) & (o[:, 2] >= 0)
    P = np.array([pts[int(i)] for i in o[m, 2] if int(i) in pts])
    rng = np.random.default_rng(seed); best = (0, None)
    scale = np.median(np.linalg.norm(P - np.median(P, 0), axis=1)) if len(P) else 1
    for _ in range(2000):
        a, b, c = P[rng.choice(len(P), 3, replace=False)]
        n = np.cross(b - a, c - a)
        if np.linalg.norm(n) < 1e-12:
            continue
        n /= np.linalg.norm(n); inl = np.abs(P @ n - n @ a) < tol * scale
        if inl.sum() > best[0]:
            best = (inl.sum(), inl)
    Q = P[best[1]]; c0 = Q.mean(0); n = np.linalg.svd(Q - c0)[2][2]
    return n, n @ c0, len(P), int(best[0])


def hit(imgs, frame, u, v, pl):
    o, d = ray(imgs[frame], u, v); n, k = pl[:2]
    return o + d * (k - n @ o) / (n @ d)


if __name__ == "__main__":
    imgs, pts = load()
    print(f"model: {len(imgs)} frames, {len(pts)} points")


# ---- surfaces (frame, pixel polygon) and features (frame, u, v), read on gridded full-resolution crops (+-4 px) ----
SURF = {"picture": [("2677", [(1640, 120), (1900, 120), (1900, 520), (1640, 520)]), ("1612", [(1165, 280), (1365, 280), (1365, 590), (1165, 590)])],
        "stair_wall": [("2677", [(150, 50), (600, 50), (600, 580), (150, 580)]), ("3170", [(180, 330), (420, 330), (420, 730), (180, 730)])],
        "front_wall": [("10244", [(390, 340), (570, 340), (570, 930), (390, 930)])]}
FRONT_DOOR = {"tl": ("10244", 770, 100), "bl": ("10244", 770, 908), "tr": ("10244", 1130, 100), "br": ("10244", 1130, 908)}
BACK = {   # on the picture-wall plane, per frame: floor line, ceiling line, wainscot top, arch casing (outer, right), corner
    "1612": {"floor": (1300, 772), "ceiling": (1300, 272), "wainscot": (1300, 598), "arch": (1162, 450), "corner": (1372, 450)},
    "10671": {"floor": (1520, 640), "ceiling": (1520, 215), "wainscot": (1520, 500), "arch": (1432, 400), "corner": (1620, 400)},
    "3170": {"floor": (1520, 1037), "ceiling": (1520, 432), "wainscot": (1520, 820), "arch": (1400, 650), "corner": (1653, 650)},
    "2677": {"floor": (1600, 787), "ceiling": (1700, 104), "wainscot": (1750, 557)}}
ARCH_2677 = {"left": (1283, 500), "right": (1604, 500), "casing": (1629, 500), "crown": (1443, 117), "spring": (1604, 192)}
REAR_DOOR = {"2677": {"bottom": (1450, 738), "top": (1450, 215), "left": (1321, 500), "right": (1567, 500)},
             "10671": {"bottom": (1320, 613), "top": (1320, 280)}}


def survey():
    imgs, pts = load()
    P = {}
    for k in ("picture", "stair_wall"):
        regs = SURF[k]; fits = [plane(imgs, pts, fr, poly) for fr, poly in regs]
        P[k] = fits[0]
        print(f"  plane {k:10s}: {fits[0][3]} of {fits[0][2]} points; second frame agrees to "
              f"{np.degrees(np.arccos(min(1, abs(fits[0][0] @ fits[1][0])))):.1f} deg")
    n_pic, d_pic = P["picture"][:2]; n_st, d_st = P["stair_wall"][:2]
    print(f"  picture wall vs stair wall {np.degrees(np.arccos(abs(n_pic @ n_st))):.1f} deg (a house: 90)")
    up = np.cross(n_pic, n_st); up /= np.linalg.norm(up)
    t = hit(imgs, "2677", *REAR_DOOR["2677"]["top"], P["picture"]); b = hit(imgs, "2677", *REAR_DOOR["2677"]["bottom"], P["picture"])
    if (t - b) @ up < 0:
        up = -up
    h = lambda p: p @ up
    # floor: level (normal = up) through the picture wall's base line, read in 2677
    floorpl = (up, h(hit(imgs, "2677", *BACK["2677"]["floor"], P["picture"])))
    scales = {}
    for fr, d in REAR_DOOR.items():
        bot = hit(imgs, fr, *d["bottom"], floorpl); dpl = (n_pic, n_pic @ bot); top = hit(imgs, fr, *d["top"], dpl)
        scales[fr] = 2.032 / (h(top) - h(bot))
        print(f"  rear door ({fr}) behind the picture wall by {abs(n_pic @ bot - d_pic):.3f} units; 80 in -> {scales[fr]:.3f} m/unit")
    s = scales["2677"]
    d = REAR_DOOR["2677"]; bot = hit(imgs, "2677", *d["bottom"], floorpl); dpl = (n_pic, n_pic @ bot)
    print(f"\nScale from the 2677 rear door (80 in). Checks: the same door's width "
          f"{np.linalg.norm(hit(imgs, '2677', *d['right'], dpl) - hit(imgs, '2677', *d['left'], dpl)) * s:.2f} m (leaf + casing ~0.9-1.05); "
          f"10671's door gives a scale {scales['10671'] / s:.2f}x this one")
    print(f"Passage: the rear door stands {abs(n_pic @ bot - d_pic) * s:.2f} m behind the picture wall")
    rows = {}
    for fr, bb in BACK.items():
        q = {k: hit(imgs, fr, u, v, P["picture"]) for k, (u, v) in bb.items()}
        fl = h(q["floor"]); row = {k: (h(q[k]) - fl) * s for k in ("ceiling", "wainscot")}
        if "arch" in q:
            row["picture_wall"] = np.linalg.norm((q["corner"] - q["arch"]) - ((q["corner"] - q["arch"]) @ up) * up) * s
            row["corner_to_stair_wall"] = abs(q["corner"] @ n_st - d_st) * s
            row["arch_casing_to_stair_wall"] = abs(q["arch"] @ n_st - d_st) * s
        rows[fr] = row
        print(f"  {fr:>5}: " + ", ".join(f"{k} {v:.2f} m" for k, v in row.items()))
    a = {k: hit(imgs, "2677", u, v, P["picture"]) for k, (u, v) in ARCH_2677.items()}
    fl = h(hit(imgs, "2677", *BACK["2677"]["floor"], P["picture"]))
    print(f"Arch (2677): clear width {np.linalg.norm(a['right'] - a['left']) * s:.2f} m, crown {(h(a['crown']) - fl) * s:.2f} m, "
          f"springline {(h(a['spring']) - fl) * s:.2f} m; its left side {abs(a['left'] @ n_st - d_st) * s:.2f} m and right casing "
          f"{abs(a['casing'] @ n_st - d_st) * s:.2f} m from the stair wall")
    return rows


if __name__ == "__main__":
    survey()
