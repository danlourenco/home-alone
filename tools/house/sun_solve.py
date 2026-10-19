"""sun_solve: the film's sun (azimuth, elevation) from the portico's shadow on the brick in frame 4382 (Oct 19 2026; DEVIATIONS 34).

Camera: tools/house/exterior_film_fit.py's pinhole solve of 4382 (window centres). Portico: tools/house/exterior_shell.py portico()
(columns 1.28 m out from the brick, entablature to 1.50 m, its top-left edge at floor + 2.56 m, the left column at door z + 1.42).
Two shadow features are read off the film BY THE SCRIPT (luminance edges in fixed search windows):
  1. the left column's shadow on the shutter left of it: a vertical step (lit ~20 -> shadow ~12), rows 690-790;
     its offset from the column's own left edge (bright, x 815-840) is measured on the same rows (relative: camera bias cancels);
  2. the diagonal top edge of the shadow under the canopy's left end (the shadow of its top-left edge, wall -> front),
     x 776-810: its slope in the image.
The camera's absolute fit error (~10 px) cancels: both are compared as image OFFSETS / SLOPES, predicted by projecting the model's
portico and its shadow through the same camera. Spread: Monte Carlo over the edge reads (+-3 px), the portico depths (+-0.10 m),
the column radius and the camera (+-0.3 m position, +-0.5 deg yaw).

Independent checks (no shared picks):
  A. the main block's shadow on the set-back left section (1.06 m step) in the same frame: the predicted shadowed width on the
     left section's face next to the corner vs the film's darker right-hand window units (read here as a luminance ratio).
  B. solar ephemeris, Winnetka (42.106 N, 87.736 W): which dates (Dec 1989 - May 1990) and local times give this sun.

  uv run --with numpy --with scipy --with pillow python -I tools/house/sun_solve.py      # exit 1 if the spread is wider than 10 deg
"""
import math
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import exterior_film_fit as E  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
FRONT = 227.6                      # compass bearing the front (+spec x) faces (tools/house/house_bearing.py)
XW = E.FM + 0.1                    # brick face (front_main + veneer)
GF = -3.026
ZC, HALF = 9.716, 1.42


def to_sun(az, el):
    """compass az/el -> unit vector toward the sun in spec coords (+x = 227.6, -z = 137.6, y up)."""
    r, e = math.radians(az - FRONT), math.radians(el)
    return np.array([math.cos(r) * math.cos(e), math.sin(e), math.sin(r) * math.cos(e)])


def shadow(P, s, xw=XW):
    P = np.asarray(P, float); t = (P[0] - xw) / s[0]
    return P - t * s


def read_film():
    L = np.asarray(Image.open(ROOT / "0-homealone/full/homealone-movie-screencaps.com-4382.jpg").convert("L")).astype(float)
    rows = range(690, 790, 4)
    col_edge, sh_edge = [], []
    for y in rows:
        p = np.median(L[y:y + 4], 0)
        g = p[816:842]; col_edge.append(816 + int(np.argmax(np.diff(g))) + 0.5)          # dark -> bright: column's left edge
        best = None                                                                            # shutter step: lit (left) -> shadow (right)
        for x in range(762, 790):
            d = p[x - 8:x].mean() - p[x:x + 8].mean()
            if best is None or d > best[0]: best = (d, x)
        sh_edge.append(best[1])
    diag = []
    for x in range(776, 812, 2):                                                               # first dark row under the lit brick
        c = np.median(L[600:690, x - 1:x + 2], 1)
        for i in range(20, len(c) - 6):
            if c[i:i + 6].max() < 40 and c[i - 8:i].mean() > 45: diag.append((x, 600 + i)); break
    return np.median(col_edge), np.median(sh_edge), np.array(diag, float)


def predict(az, el, cam, col_out=1.28, ent_out=1.50, rad=0.125):
    s = to_sun(az, el)
    xc = XW + col_out; zl = ZC + HALF
    # column: its left silhouette as seen by the camera vs the shadow of its sun-silhouette line
    out = []
    for y in (-2.2, -1.8):
        seen = E.project(np.array([xc, y, zl + rad]), cam)[0]
        h = np.array([s[0], 0, s[2]]); h /= np.linalg.norm(h); perp = np.array([-h[2], 0, h[0]])
        if perp[2] < 0: perp = -perp
        sp = E.project(shadow(np.array([xc, y, zl]) + rad * perp + 0.05 * np.array([0, 0, 0]), s, XW + 0.05), cam)[0]   # shutters ~5 cm proud
        out.append(sp[0] - seen[0])
    dx = float(np.mean(out))
    ye1 = GF + 2.56; ze = ZC + HALF + 0.22
    A = E.project(np.array([XW, ye1, ze]), cam)[0]
    B = E.project(shadow(np.array([XW + ent_out, ye1, ze]), s), cam)[0]
    slope = (B[1] - A[1]) / (B[0] - A[0])
    return dx, slope


def solve(target_dx, target_slope, cam, **kw):
    from scipy.optimize import least_squares
    def res(p):
        dx, sl = predict(p[0], p[1], cam, **kw)
        return [(dx - target_dx) / 3, (math.atan(sl) - math.atan(target_slope)) / math.radians(4)]
    best = min((least_squares(res, x0, bounds=([130, 2], [227, 70])) for x0 in ([160, 15], [195, 25], [215, 40])), key=lambda r: r.cost)
    return float(best.x[0]), float(best.x[1])


def left_section_check(az, el, cam):
    """predicted shadow of the main block's left front corner on the set-back left section (face x 9.406+0.1), as image px
    from the corner, vs the film's darkness of the last window unit (x 375-405) against the others."""
    s = to_sun(az, el)
    corner = np.array([XW, 0.6, 16.21])
    sh = shadow(corner, s, 9.406 + 0.1)
    c_px = E.project(corner, cam)[0][0]; s_px = E.project(sh, cam)[0][0]
    return c_px - s_px


def solar(lat, lon, when_utc):
    """NOAA low-precision solar position: (azimuth deg from N clockwise, elevation deg)."""
    d = when_utc - datetime(2000, 1, 1, 12, tzinfo=timezone.utc); n = d.total_seconds() / 86400
    Lm = (280.460 + 0.9856474 * n) % 360; g = math.radians((357.528 + 0.9856003 * n) % 360)
    lam = math.radians(Lm + 1.915 * math.sin(g) + 0.020 * math.sin(2 * g)); eps = math.radians(23.439 - 4e-7 * n)
    ra = math.atan2(math.cos(eps) * math.sin(lam), math.cos(lam)); dec = math.asin(math.sin(eps) * math.sin(lam))
    gmst = (18.697374558 + 24.06570982441908 * n) % 24
    ha = math.radians((gmst * 15 + lon) - math.degrees(ra))
    la = math.radians(lat)
    el = math.asin(math.sin(la) * math.sin(dec) + math.cos(la) * math.cos(dec) * math.cos(ha))
    az = math.atan2(-math.sin(ha), math.tan(dec) * math.cos(la) - math.sin(la) * math.cos(ha))
    return math.degrees(az) % 360, math.degrees(el)


def ephemeris(az0, el0, daz, del_):
    out = []
    for month, days in ((12, (21,)), (1, (15,)), (2, (1, 15)), (3, (1, 15)), (4, (1, 15)), (5, (1, 15))):
        for day in days:
            yr = 1989 if month == 12 else 1990
            dst = month in (4, 5) and not (month == 4 and day < 2)   # CDT from Apr 1 1990
            off = 5 if dst else 6
            hits = []
            for mins in range(6 * 60, 18 * 60, 5):
                t = datetime(yr, month, day, tzinfo=timezone.utc) + timedelta(hours=off, minutes=mins)
                a, e = solar(42.106, -87.736, t)
                if abs(a - az0) <= daz and abs(e - el0) <= del_: hits.append(mins)
            noon_el = max(solar(42.106, -87.736, datetime(yr, month, day, tzinfo=timezone.utc) + timedelta(hours=off, minutes=m))[1] for m in range(600, 840, 5))
            span = f"{hits[0] // 60:02d}:{hits[0] % 60:02d}-{hits[-1] // 60:02d}:{hits[-1] % 60:02d} local" if hits else "no time fits"
            out.append(f"{yr}-{month:02d}-{day:02d}: {span} (max elevation that day {noon_el:.0f})")
    return out


def main():
    cam, _, err = E.fit("4382")
    col, she, diag = read_film()
    t_dx = she - col
    A = np.polyfit(diag[:, 0], diag[:, 1], 1); t_slope = A[0]
    print(f"film 4382 reads: column left edge x {col:.1f}, its shadow's edge on the shutter x {she:.1f} (offset {t_dx:+.1f} px); "
          f"canopy-end shadow diagonal slope {t_slope:.2f} over {len(diag)} columns (x {diag[0, 0]:.0f}-{diag[-1, 0]:.0f})")
    az, el = solve(t_dx, t_slope, cam)
    rng = np.random.default_rng(1990)
    samp = []
    for _ in range(150):
        c = list(cam); c[0] += rng.normal(0, 0.3); c[2] += rng.normal(0, 0.3); c[3] += math.radians(rng.normal(0, 0.5)); c = tuple(c)
        dx = t_dx + rng.normal(0, 3 * math.sqrt(2)); sl = math.tan(math.atan(t_slope) + math.radians(rng.normal(0, 4)))
        samp.append(solve(dx, sl, c, col_out=1.28 + rng.normal(0, 0.1), ent_out=1.50 + rng.normal(0, 0.1), rad=0.125 + rng.normal(0, 0.015)))
    S = np.array(samp)
    lo, hi = np.percentile(S, [5, 95], 0)
    print(f"SUN (film 4382): azimuth {az:.1f} deg (5-95%: {lo[0]:.1f}-{hi[0]:.1f}), elevation {el:.1f} deg (5-95%: {lo[1]:.1f}-{hi[1]:.1f}); "
          f"relative to the front's normal {az - FRONT:+.1f} deg (toward the SE side)")
    w = left_section_check(az, el, cam)
    L = np.asarray(Image.open(ROOT / "0-homealone/full/homealone-movie-screencaps.com-4382.jpg").convert("L")).astype(float)
    b = np.median(L[600:660], 0)                                    # brick between the left section's windows
    corner = next(x for x in range(385, 430) if np.median(b[x:x + 6]) > 32)   # dark (left section) -> lit (main block front)
    x = corner - 2
    while x > 330 and np.median(b[x - 4:x + 1]) < 22: x -= 1
    print(f"check A (same frame, other geometry: the main block's shadow on the left section, 0.96 m back): predicted {w:.0f} px "
          f"left of the corner; film: dark brick {corner - x} px (x {x}-{corner}; its edge sits near a window mullion and a branch shadow: weak)")
    # check C: held-out frame 1644 (another shot, near-frontal, closer): the left column's shadow on the brick left of it. Column
    # diameter (0.27 m at its shaft) as the ruler; the shadow runs from the column's left edge over dark brick to the shutter.
    F = np.asarray(Image.open(ROOT / "0-homealone/full/homealone-movie-screencaps.com-1644.jpg").convert("L")).astype(float)
    p = np.median(F[300:440], 0)
    cl = 830 + int(np.argmax(np.diff(p[830:870]))) + 1; cr = cl + 10 + int(np.argmin(np.diff(p[cl + 10:cl + 45])))
    run = cl - 4                                                     # lit brick here reads 60-90, shadowed 15-30, the shutter ~12
    while run > 700 and p[run] < 40 and np.median(p[run - 6:run]) >= 14: run -= 1
    m_per_px = 0.27 / (cr - cl)
    off_m = (cl - run) * m_per_px
    th = math.degrees(math.atan(off_m / 1.28))
    print(f"check C (held-out film 1644): column {cl}-{cr} px, shadowed brick to x {run} (then the shutter): offset >= {off_m:.2f} m "
          f"-> sun >= {th:.0f} deg SE of the front's normal (az <= {FRONT - th:.0f}); 4382's solve {FRONT - az:.0f} deg "
          f"({'consistent' if FRONT - az >= th - 3 else 'INCONSISTENT'}); same side (SE) as 4382")
    print("check B (ephemeris, Winnetka 42.106 N; dates the sun is within the 5-95% box):")
    for line in ephemeris(az, el, max(3, (hi[0] - lo[0]) / 2), max(3, (hi[1] - lo[1]) / 2)): print("  " + line)
    ok = (hi[0] - lo[0]) < 20 and (hi[1] - lo[1]) < 20
    print("ok" if ok else "FAIL (spread too wide)")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
