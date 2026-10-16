"""brick_ruler: absolute sizes of facade features from brick courses in film stills (no doors, no Marina, no SfM).

Why (Oct 15): the exterior is the real house and is accepted; brick courses are a ruler that shares nothing with the
door-height scale. A feature's size = its extent in pixels / the local brick period in pixels * the brick module.

Period: autocorrelation of the detrended intensity profile of a brick patch beside the feature (vertical: course
height; horizontal: stretcher repeat, from the 2-D autocorrelation, since running bond offsets alternate courses),
refined on the highest clean multiple. Spread: the same estimate on 4 sub-strips of the patch. Edges: snapped to the
strongest gradient within +-SNAP px of a pixel read from a refcam grid. Unresolved (< MIN_P px or weak peak) is flagged.

  brick_ruler.py            -> sfm-work/brick/results.json + overlays sfm-work/brick/<frame>.png
  brick_ruler.py --selftest -> synthetic brick (known period, JPEG, perspective) must be recovered; too-fine must flag
"""
import io
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "sfm-work/brick"
FRAME = str(ROOT / "0-homealone/full/homealone-movie-screencaps.com-{}.jpg")
MIN_P, SNAP = 4.0, 8
IN = 0.0254
# Course height and stretcher repeat (brick + joint), inches. 1920s houses predate modular brick (c. 1946).
STANDARDS = {"modular": (8 / 3, 8.0), "standard 3/8 joint": (2.625, 8.375), "standard 1/2 joint": (2.75, 8.5)}

# Brick patches per frame: clean brick on the same wall plane as the features, spread across x so the period can be
# fitted as a plane (1/Z is affine in image x, y for a plane: course height cv(x, y) = a + b x + c y). x0 y0 x1 y1.
WALLS = {
    # 4575: kitchen wing rear wall, day; the wall recedes to the right (course 18.7 px at left, 14.6 px at right).
    4575: [[10, 60, 190, 300], [200, 60, 265, 190], [560, 105, 680, 385], [880, 100, 1060, 390], [960, 240, 1060, 470]],
    # 7068: same wall from further back, near frontal (13.3 -> 12.3 px left to right). Railing/hedge excluded.
    7068: [[140, 620, 330, 700], [565, 400, 715, 480], [565, 440, 630, 700], [905, 400, 1080, 650], [990, 400, 1080, 560]],
}
# Features read from refcam grids (sfm-work/refcam/grids). edges: approximate pixel pair along `axis` (v: rows, h: columns),
# snapped to the strongest gradient; span: the perpendicular pixel range used for snapping (and its midpoint for the period).
FEATURES = [
    {"f": 4575, "name": "sink window: outer trim height", "axis": "v", "edges": [130, 357], "span": [290, 480]},
    {"f": 4575, "name": "sink window: outer trim width", "axis": "h", "edges": [271, 498], "span": [180, 320]},
    {"f": 4575, "name": "back door: outer trim width", "axis": "h", "edges": [692, 870], "span": [200, 300]},
    {"f": 4575, "name": "gap: window trim to door trim", "axis": "h", "edges": [498, 692], "span": [160, 340]},
    {"f": 7068, "name": "sink window: outer trim height", "axis": "v", "edges": [444, 612], "span": [380, 550]},
    {"f": 7068, "name": "sink window: outer trim width", "axis": "h", "edges": [372, 558], "span": [450, 600]},
    {"f": 7068, "name": "back door: outer trim width", "axis": "h", "edges": [723, 898], "span": [450, 640]},
    {"f": 7068, "name": "gap: window trim to door trim", "axis": "h", "edges": [558, 723], "span": [450, 600]},
    {"f": 7068, "name": "back door: trim top to threshold", "axis": "v", "edges": [443, 806], "span": [884, 896]},
]


def gray(path):
    import matplotlib.image as mpimg
    im = mpimg.imread(path).astype(float)
    return im[..., :3].mean(axis=2) if im.ndim == 3 else im


def detrend(p):
    k = max(3, int(len(p) / 6) | 1)          # remove shading slower than a few courses
    pad = np.pad(p, k, mode="reflect")
    smooth = np.convolve(pad, np.ones(k) / k, mode="same")[k:-k]
    q = (p - smooth) * np.hanning(len(p))
    return q - q.mean()


def acorr(q):
    n = len(q)
    F = np.fft.rfft(q, 2 * n)
    a = np.fft.irfft(F * np.conj(F))[:n]
    return a / a[0] / (1 - np.arange(n) / n)  # unbiased: correct for the shrinking overlap


def peak(a, lag, w):
    lo, hi = max(1, int(lag - w)), min(len(a) - 2, int(lag + w) + 1)
    i = lo + int(np.argmax(a[lo:hi + 1]))
    d = 0.5 * (a[i - 1] - a[i + 1]) / (a[i - 1] - 2 * a[i] + a[i + 1] + 1e-12)
    return i + float(np.clip(d, -0.5, 0.5)), float(a[i])


def period_of(a):
    """Period in px from an autocorrelation, or (None, strength) if unresolved."""
    n = len(a)
    for i in range(int(MIN_P) - 1, int(0.75 * n)):  # first local max that is strong (unbiased acorr is noisy past 3/4)
        if a[i] > a[i - 1] and a[i] >= a[i + 1] and a[i] > 0.25:
            break
    else:
        return None, 0.0
    p0, s = peak(a, i, 1)
    if p0 < MIN_P:
        return None, s
    best = p0
    for k in range(2, int((n / 2) // p0) + 1):  # refine on clean multiples
        pk, sk = peak(a, k * best, max(2, 0.15 * best))
        if sk < 0.25:
            break
        best = pk / k
    return best, s


def lines_acorr(P, axis):
    """Mean autocorrelation of every line through the patch: columns for course height ('v'), rows for the
    stretcher repeat ('h'). Averaging autocorrelations (not profiles) keeps running bond's half-brick shift between
    courses from halving the horizontal period."""
    L = P.T if axis == "v" else P
    return np.mean([acorr(detrend(l)) for l in L], axis=0)


def measure_period(img, patch, axis, n=4):
    x0, y0, x1, y1 = patch
    P = img[y0:y1, x0:x1]
    p, s = period_of(lines_acorr(P, axis))
    if p is None:
        return None
    parts = np.array_split(P, n, axis=1 if axis == "v" else 0)
    ps = [q for q in (period_of(lines_acorr(x, axis))[0] for x in parts) if q]
    sd = float(np.std(ps) / np.sqrt(len(ps))) if len(ps) >= 2 else float("nan")
    rng = [min(ps), max(ps)] if ps else [p, p]
    return {"px": round(p, 3), "strength": round(s, 3), "strip_range": [round(rng[0], 2), round(rng[1], 2)], "sd": round(sd, 3)}


def snap(img, axis, e, span):
    """Strongest gradient within +-SNAP px of e, across the perpendicular span."""
    if axis == "v":
        prof = img[:, span[0]:span[1]].mean(axis=1)
    else:
        prof = img[span[0]:span[1], :].mean(axis=0)
    g = np.abs(np.gradient(prof))
    lo, hi = e - SNAP, e + SNAP + 1
    i = lo + int(np.argmax(g[lo:hi]))
    d = 0.5 * (g[i - 1] - g[i + 1]) / (g[i - 1] - 2 * g[i] + g[i + 1] + 1e-12)
    return i + float(np.clip(d, -0.5, 0.5))


def fit_wall(img, patches, cx):
    """Course height cv(x, y) = a + b x + c y over the wall's patches, and the stretcher/course ratio
    r(x) = r0 + r1 (x - cx) (linear in x for a plane seen by a level camera: r = R (uX - (x - cx) uZ / f))."""
    rows = []
    for pt in patches:
        v, h = measure_period(img, pt, "v"), measure_period(img, pt, "h")
        if v:
            rows.append({"patch": pt, "x": (pt[0] + pt[2]) / 2, "y": (pt[1] + pt[3]) / 2, "cv": v["px"], "cv_sd": v["sd"],
                         "L": h["px"] if h else None})
    A = np.array([[1, r["x"], r["y"]] for r in rows]); cv = np.array([r["cv"] for r in rows])
    coef = np.linalg.lstsq(A, cv, rcond=None)[0] if len(rows) >= 3 else np.array([cv.mean(), 0, 0])
    rel = (cv - A @ coef) / cv
    rh = [r for r in rows if r["L"]]
    ratio = None
    if len(rh) >= 2:
        X = np.array([[1, r["x"] - cx] for r in rh]); y = np.array([r["L"] / (A[rows.index(r)] @ coef) for r in rh])
        rc = np.linalg.lstsq(X, y, rcond=None)[0]
        ratio = {"r0": round(float(rc[0]), 4), "r1": float(rc[1]), "resid": [round(float(e), 4) for e in y - X @ rc],
                 "points": [[r["x"], round(float(v), 4)] for r, v in zip(rh, y)]}
    return {"patches": rows, "cv_coef": [float(c) for c in coef], "cv_rel_resid": [round(float(e), 4) for e in rel],
            "cv_rms": float(np.sqrt(np.mean(rel ** 2))), "ratio": ratio}


def run():
    OUT.mkdir(parents=True, exist_ok=True)
    res, cache, walls = [], {}, {}
    for f, patches in WALLS.items():
        cache[f] = gray(FRAME.format(f))
        walls[f] = fit_wall(cache[f], patches, cache[f].shape[1] / 2)
        w = walls[f]
        print(f"wall {f}: cv = {w['cv_coef'][0]:.2f} + {w['cv_coef'][1]:.5f} x + {w['cv_coef'][2]:.5f} y px, "
              f"fit rms {100 * w['cv_rms']:.1f}%, ratio {w['ratio'] and (w['ratio']['r0'], w['ratio']['r1'])}")
    for ft in FEATURES:
        img, w = cache[ft["f"]], walls[ft["f"]]
        a0, b0, c0 = w["cv_coef"]
        a, b = (snap(img, ft["axis"], e, ft["span"]) for e in ft["edges"])
        m = (ft["span"][0] + ft["span"][1]) / 2
        t = np.linspace(a, b, 200)
        if ft["axis"] == "v":   # courses between the rows, at this column
            n = float(np.trapezoid(1 / (a0 + b0 * m + c0 * t), t))
            unit, rel = 0, w["cv_rms"]
        else:                   # stretchers between the columns: L(x) = cv(x) r(x)
            if not w["ratio"]:
                continue
            r = w["ratio"]; cx = img.shape[1] / 2
            n = float(np.trapezoid(1 / ((a0 + b0 * t + c0 * m) * (r["r0"] + r["r1"] * (t - cx))), t))
            unit = 1
            rel = float(np.hypot(w["cv_rms"], np.sqrt(np.mean(np.square(r["resid"]))) / r["r0"]))
        rel = float(np.hypot(rel, 1.0 / (b - a)))  # +-0.5 px per snapped edge
        r = {**ft, "snapped": [round(a, 1), round(b, 1)], "extent_px": round(b - a, 1),
             "modules": round(n, 2), "unit": "courses" if unit == 0 else "stretchers", "rel_sd": round(rel, 4),
             "size_m": {k: round(n * v[unit] * IN, 3) for k, v in STANDARDS.items()}}
        res.append(r)
        print(f'{ft["f"]:>5} {ft["name"]:<36} {r["modules"]:6.2f} {r["unit"]:<10} '
              + "  ".join(f"{k} {v:.3f}" for k, v in r["size_m"].items()) + f"  (+-{100 * rel:.1f}%)")
    (OUT / "results.json").write_text(json.dumps({"walls": walls, "features": res}, indent=1, default=float))
    overlay(res, cache, walls)
    return res, walls


def overlay(res, cache, walls):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    for f in sorted({r["f"] for r in res}):
        fig = plt.figure(figsize=(19.2, 10.58), dpi=100)
        ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off")
        import matplotlib.image as mpimg
        ax.imshow(mpimg.imread(FRAME.format(f)))
        for p in walls[f]["patches"]:
            x0, y0, x1, y1 = p["patch"]
            ax.add_patch(plt.Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, ec="yellow", lw=1.5, ls="--"))
            ax.text(x0 + 3, y0 + 18, f'{p["cv"]:.2f}' + (f' / {p["L"]:.1f}' if p["L"] else ""), color="yellow", fontsize=12)
        for k, r in enumerate([r for r in res if r["f"] == f]):
            c = "C%d" % k
            a, b = r["snapped"]; s0, s1 = r["span"]
            if r["axis"] == "v":
                for y in (a, b): ax.plot([s0, s1], [y, y], c=c, lw=2)
                ax.plot([(s0 + s1) / 2] * 2, [a, b], c=c, lw=1)
            else:
                for x in (a, b): ax.plot([x, x], [s0, s1], c=c, lw=2)
                ax.plot([a, b], [(s0 + s1) / 2] * 2, c=c, lw=1)
            ax.text(10, 30 + 34 * k, f'{r["name"]}: {r["modules"]} {r["unit"]} = {r["size_m"]["modular"]} m (modular)',
                    color=c, fontsize=16, weight="bold", bbox=dict(fc="black", alpha=.6))
        fig.savefig(OUT / f"{f}.png"); plt.close(fig)


def synth(period, L, h=400, w=600, tilt=0.0, q=60):
    """Running-bond brick, mortar bright; perspective: course height grows linearly by `tilt` across the image."""
    yy, xx = np.mgrid[0:h, 0:w].astype(float)
    scale = 1 + tilt * (yy / h - 0.5)
    v = yy / (period * scale)
    course = np.floor(v)
    u = (xx / (period * scale) * period / L + 0.5 * (course % 2))
    mortar = (v % 1 < 0.18) | (u % 1 < 0.06)
    rng = np.random.default_rng(1)
    im = np.where(mortar, 0.75, 0.3) + rng.normal(0, 0.05, (h, w))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    buf = io.BytesIO()
    plt.imsave(buf, np.clip(im, 0, 1), cmap="gray", format="jpg", pil_kwargs={"quality": q})
    buf.seek(0)
    import matplotlib.image as mpimg
    g = mpimg.imread(buf, format="jpg").astype(float)
    return g[..., :3].mean(axis=2)


def selftest():
    for P, L, tilt in [(11.0, 33.0, 0.0), (11.3, 33.9, 0.06), (21.0, 63.0, 0.03), (6.0, 18.0, 0.0)]:
        im = synth(P, L, tilt=tilt)
        pv = measure_period(im, [0, 0, 600, 400], "v")
        ph = measure_period(im, [0, 0, 600, 400], "h")
        true_v = P * (1 + tilt / 2)  # mean course height over the patch: h / courses(h), scale runs 1-t/2 .. 1+t/2
        assert pv and abs(pv["px"] / true_v - 1) < 0.01, (true_v, pv)
        assert ph and abs(ph["px"] / L - 1) < 0.02, (L, ph)
        print(f"ok  course {true_v:.3f} -> {pv['px']:.3f}   brick {L} -> {ph['px']:.3f}   (tilt {tilt})")
    bad = measure_period(synth(3.0, 9.0), [0, 0, 600, 400], "v")
    assert bad is None, ("3 px courses must be flagged unresolved", bad)
    print("ok  3 px courses flagged unresolved")
    # edge snap: a bright box in noise
    im = np.zeros((200, 200)) + np.random.default_rng(2).normal(0, .02, (200, 200)); im[60:141, 50:150] = 1
    assert abs(snap(im, "v", 64, [60, 140]) - 59.5) <= 1 and abs(snap(im, "v", 137, [60, 140]) - 140.5) <= 1
    print("ok  edge snap")


if __name__ == "__main__":
    selftest() if "--selftest" in sys.argv else run()
