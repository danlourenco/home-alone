"""Stair geometry from a gated VGGT solve (sfm-work/rooms/<clip>/vggt/sparse/0/pixels.npz).

Carpet pixels (the red runner) give the steps. Per-pixel normals from the point map split them into treads
(normal ~ up) and risers (normal ~ horizontal). Up = mean tread normal; flight direction = mean riser normal.
Tread heights cluster at one level per step: the spacing is the rise. Riser positions along the flight cluster
one per step: the spacing is the going. Everything is in model units; the scale comes from a door
(`--door idx:x:ytop:ybot`, same picks as door_scale.py) or is left as units (ratios still hold).
usage: uv run --with numpy --with matplotlib python tools/sfm/stair_measure.py <clip> [--door idx:x:yt:yb ...] [--door-in 80]
writes sfm-work/rooms/<clip>/stair.json and stair.png
"""
import json
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]


def normals(world, k=3):
    dx = world[:, k:-k, 2 * k:] - world[:, k:-k, :-2 * k]
    dy = world[:, 2 * k:, k:-k] - world[:, :-2 * k, k:-k]
    n = np.cross(dx, dy)
    n /= np.linalg.norm(n, axis=-1, keepdims=True) + 1e-12
    out = np.zeros_like(world); out[:, k:-k, k:-k] = n
    return out


def peaks(v, bin_w, min_frac=0.15):
    """Cluster centres of 1-D values: histogram peaks (local maxima above min_frac of the top), refined by mean."""
    lo, hi = v.min(), v.max()
    hist, edges = np.histogram(v, bins=max(int((hi - lo) / bin_w), 1), range=(lo, hi))
    hs = np.convolve(hist, [1, 2, 3, 2, 1], "same")
    top = hs.max()
    idx = [i for i in range(1, len(hs) - 1) if hs[i] >= hs[i - 1] and hs[i] > hs[i + 1] and hs[i] > min_frac * top]
    out = []
    for i in idx:
        c = (edges[i] + edges[i + 1]) / 2
        sel = np.abs(v - c) < 1.5 * bin_w
        out.append((float(v[sel].mean()), int(sel.sum())))
    return out


def camera_up(images_txt):
    def q2R(w, x, y, z):
        return np.array([[1-2*(y*y+z*z), 2*(x*y-w*z), 2*(x*z+w*y)], [2*(x*y+w*z), 1-2*(x*x+z*z), 2*(y*z-w*x)],
                         [2*(x*z-w*y), 2*(y*z+w*x), 1-2*(x*x+y*y)]])
    hs = [l for l in Path(images_txt).read_text().split("\n") if l.endswith(".jpg")]
    u = np.mean([-q2R(*map(float, l.split()[1:5])).T @ [0, 1, 0] for l in hs], 0)
    return u / np.linalg.norm(u)


def door_height(images, world, up, spec, inset=4):
    """Door height along up. Edge pixels sit on depth discontinuities (their 3D points can jump to the wall or floor
    behind), so read the slab's interior points along the column and extrapolate a quadratic fit to the snapped edges."""
    idx, x, yt, yb = spec
    gray = images[idx].astype(np.float32).mean(2)
    def snap(y):
        g = np.abs(np.diff(gray[:, x - 1:x + 2].mean(1)))
        lo, hi = max(y - 8, 0), min(y + 8, len(g) - 1)
        return lo + int(np.argmax(g[lo:hi]))
    t, b = snap(yt) + 1, snap(yb)
    hs = []
    for c in range(x - 2, x + 3):
        rows = np.arange(t + inset, b - inset + 1)
        pts = world[idx, rows, c]
        fit = [np.polyfit(rows, pts[:, k], 2) for k in range(3)]
        at = lambda r: np.array([np.polyval(f, r) for f in fit])
        hs.append(abs((at(b) - at(t)) @ up))
    return float(np.median(hs))


def main():
    args = sys.argv[1:]
    clip = args[0]
    doors = [tuple(map(int, args[i + 1].split(":"))) for i, a in enumerate(args) if a == "--door"]
    door_in = float(args[args.index("--door-in") + 1]) if "--door-in" in args else 80.0
    w = ROOT / "sfm-work/rooms" / clip
    d = np.load(w / "vggt/sparse/0/pixels.npz")
    world, conf, images = d["world"], d["conf"], d["images"]
    rgb = images.astype(np.float32)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    carpet = (r > g * 1.6) & (r > b * 1.4) & (r > 40) & (conf > np.percentile(conf, 30))
    N = normals(world)
    ok = carpet & (np.linalg.norm(N, axis=-1) > 0.5)
    P, Nc = world[ok], N[ok]

    # up: the normal family nearest the cameras' mean vertical (camera pitch biases that guess by up to ~30 deg,
    # still far closer to the tread normal than to the riser normal, which is ~90 deg away)
    up0 = camera_up(w / "vggt/sparse/0/txt/images.txt")
    up = up0.copy()
    for cone in (35, 25, 20, 20, 20):
        sdot = Nc @ up   # normals carry no consistent sign: flip each toward the current guess
        sel = np.abs(sdot) > np.cos(np.radians(cone))
        fam = Nc[sel] * np.sign(sdot[sel])[:, None]
        up = fam.mean(0); up /= np.linalg.norm(up)
    # orient up: cameras look from above the treads mostly; treads are lower than the camera path on average
    h = P @ up
    # risers: normals near horizontal; their dominant horizontal direction is the flight direction
    hn = Nc - np.outer(Nc @ up, up)
    horiz = np.abs(Nc @ up) < np.sin(np.radians(20))
    hv = hn[horiz]; hv /= np.linalg.norm(hv, axis=1, keepdims=True)
    M = hv.T @ hv
    ev, evec = np.linalg.eigh(M)
    f = evec[:, -1]; f -= (f @ up) * up; f /= np.linalg.norm(f)
    s = P @ f
    # orient so the stair climbs with +f, and up is up: tread height must rise with s
    tread = np.abs(Nc @ up) > np.cos(np.radians(15))
    if np.corrcoef(s[tread], h[tread])[0, 1] < 0:
        f, s = -f, -s
    # sign of up: if heights fall as we go "up" the flight the whole frame is flipped; we only fixed f relative to up,
    # so check with gravity from the camera frames (VGGT frame: camera y points down)
    side = P @ np.cross(up, f)

    # treads: heights of tread-normal carpet points
    th = h[tread]
    span = np.ptp(th)
    tpk = peaks(th, span / 400)
    levels = np.array(sorted(p[0] for p in tpk))
    rises = np.diff(levels)
    rise = float(np.median(rises)) if len(rises) else float("nan")
    # re-cluster with the rise known: keep levels at least 0.5 rise apart
    keep = [levels[0]] if len(levels) else []
    for L in levels[1:]:
        if L - keep[-1] > 0.5 * rise:
            keep.append(L)
    levels = np.array(keep); rises = np.diff(levels); rise = float(np.median(rises))
    # risers: along-flight positions of riser-normal points, per step band
    riser = horiz & (np.abs(Nc @ f) > np.cos(np.radians(25)))
    rs = s[riser]
    rpk = peaks(rs, rise / 20, 0.10)
    nos = np.array(sorted(p[0] for p in rpk))
    keep = [nos[0]] if len(nos) else []
    for v in nos[1:]:
        if v - keep[-1] > 0.4 * np.median(np.diff(nos)):
            keep.append(v)
    nos = np.array(keep); goings = np.diff(nos); going = float(np.median(goings))
    # width: side extent of tread points (robust 2-98%)
    ts = side[tread]
    width = float(np.percentile(ts, 98) - np.percentile(ts, 2))

    scale = None
    if doors:
        dh = [door_height(images, world, up, sp) for sp in doors]
        scale = door_in * 0.0254 / float(np.median(dh))
    m = scale or 1.0
    out = {"clip": clip, "units": "m" if scale else "model units",
           "door_scale": {"picks": [":".join(map(str, sp)) for sp in doors], "door_in": door_in,
                          "door_units": [round(x, 4) for x in dh] if doors else None,
                          "m_per_unit": round(scale, 4) if scale else None},
           "up": up.round(4).tolist(), "flight_dir": f.round(4).tolist(),
           "tread_levels": [round(float(L * m), 4) for L in levels - levels[0]],
           "rises": [round(float(x * m), 4) for x in rises], "rise_median": round(rise * m, 4),
           "riser_positions": [round(float(x * m), 4) for x in nos - nos[0]],
           "goings": [round(float(x * m), 4) for x in goings], "going_median": round(going * m, 4),
           "rise_over_going": round(rise / going, 4), "width_2_98": round(width * m, 4),
           "n_tread_points": int(tread.sum()), "n_riser_points": int(riser.sum())}
    (w / "stair.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps(out, indent=1))

    fig, ax = plt.subplots(1, 3, figsize=(24, 8))
    ax[0].hist2d(s * m, h * m, bins=(500, 400), cmap="gray_r", vmax=30)
    for L in levels: ax[0].axhline(L * m, color="r", lw=0.4)
    for v in nos: ax[0].axvline(v * m, color="b", lw=0.4)
    ax[0].set_aspect("equal"); ax[0].set_title("carpet: along flight vs height (red: tread levels, blue: risers)")
    ax[1].hist(th * m, bins=400); ax[1].set_title("tread heights")
    ax[2].scatter(s[tread] * m, side[tread] * m, s=0.05, alpha=0.2); ax[2].set_aspect("equal"); ax[2].set_title("treads, plan")
    plt.savefig(w / "stair.png", dpi=70)


if __name__ == "__main__":
    main()
