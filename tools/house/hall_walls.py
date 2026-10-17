"""hall_walls: the upstairs hall's finish measured from the film (Oct 16 2026: hall upgrade, film first; DEVIATIONS 1: the upstairs is
Marina's plan drawn only from inside, so its paint, trim and dressing come from the film's hall set).

  uv run --with numpy --with pillow python -I tools/house/hall_walls.py --paint      teal paint: wall / white wainscot in the same light
  uv run --with numpy --with pillow python -I tools/house/hall_walls.py --heights    wainscot cap and baseboard heights on door rulers
  uv run --with numpy --with pillow python -I tools/house/hall_walls.py --overlay    the picks drawn on their frames (scratch, for checking)

PAINT (the den's method, tools/house/den_walls.py paint(), with the lesson from its first pass: it sampled the darkest columns and came out
too red/grey): per column, the cap rail's top edge is found as the strongest dark->bright step going down; the wall just above it and the
white wainscot just below are in the same light, so their ratio cancels the light's colour and level; albedo = 0.85 (white paint) x ratio.
Only the brighter half of the columns (by wainscot luminance: lit, not in shadow or grazing) is kept for the hue; the median and IQR
are printed per frame and over all frames, so a frame that disagrees shows.

HEIGHTS: on a level film camera (verticals vertical in these frames: the casings' edges are within 0.3 deg of vertical) a vertical line at
one depth maps heights to rows linearly, so along a door casing the cap height is head x (v_floor - v_cap) / (v_floor - v_head). The
ruler is the 80 in door (2.032 m, the house's door height: spec scale). The independent check uses a different ruler kind: the hall's
2.40 m ceiling (spec ceiling_height_m, measured on door walls in Marina's model) on the end wall in film 410, where floor, cap and
ceiling line are on one wall plane.
"""
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
FILM = str(ROOT / "0-homealone/full/homealone-movie-screencaps.com-{}.jpg")
OUT = ROOT / "sfm-work/hall"

# frame -> [(u0, u1, v0, v1, what)]: columns searched for the cap rail's top edge (green above, white cap below), plain wall only
PAINT_SRC = {
    2687: [(1545, 1640, 450, 560, "right side wall right of the poinsettia"), (650, 735, 330, 400, "left wall beyond the stair-well paper")],
    10741: [(1040, 1118, 420, 480, "left wall past the paper")],   # the right wall: the globe and console break the edge
    410: [(1520, 1840, 700, 840, "right foreground wall"), (530, 630, 600, 660, "end wall left of the far door")],
    1276: [(1160, 1320, 830, 900, "right wall below the prints"), (1550, 1640, 900, 960, "right wall right of the prints")],
    2296: [(1330, 1600, 590, 720, "right wall below the rose print")],
}


def _lin(c):
    c = c / 255.0; return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def _srgb(l):
    l = np.clip(l, 0, 1); return np.where(l <= 0.0031308, 12.92 * l, 1.055 * l ** (1 / 2.4) - 0.055)


def cap_edges(a, u0, u1, v0, v1, step=4):
    """(u, v) of the cap's top edge per column: the strongest dark->bright step going down"""
    out = []
    for u in range(u0, u1, step):
        col = a[v0:v1, u - 2:u + 3].mean(1).sum(1); dv = col[3:] - col[:-3]; j = int(np.argmax(dv))
        if dv[j] >= 60:
            out.append((u, v0 + j + 2))
    return out


def paint(quiet=False):
    from PIL import Image
    pr = (lambda *a, **k: None) if quiet else print
    allR = []
    for n, regions in PAINT_SRC.items():
        a = np.asarray(Image.open(FILM.format(n)).convert("RGB"), float); L = _lin(a)
        rows = []
        for u0, u1, v0, v1, what in regions:
            for u, v in cap_edges(a, u0, u1, v0, v1):
                w = L[v - 26:v - 6, u - 2:u + 3].reshape(-1, 3).mean(0)        # wall: 6-26 px above the cap's top
                b = L[v + 4:v + 12, u - 2:u + 3].reshape(-1, 3).mean(0)        # the cap's white face just below its top
                if b.sum() > 0.03 and w.sum() > 0.003:
                    rows.append((b.sum(), w / b))
        if not rows:
            pr(f"film {n}: no edges"); continue
        rows.sort(key=lambda r: -r[0]); keep = np.array([r[1] for r in rows[:max(3, len(rows) // 2)]])   # the brighter half (lit wainscot)
        r = np.median(keep, 0); alb = 0.85 * r; allR.append(keep)
        pr(f"film {n:5d}: {len(keep):3d}/{len(rows):3d} columns, wall/wainscot {r.round(3)} (IQR {(np.percentile(keep, 75, 0) - np.percentile(keep, 25, 0)).round(3)})"
           f" -> linear {alb.round(3)} sRGB {np.round(_srgb(alb) * 255).astype(int)}")
    R = np.concatenate(allR); r = np.median(R, 0); alb = 0.85 * r
    per = np.array([np.median(k, 0) for k in allR]) * 0.85
    pr(f"ALL {len(R)} columns: linear albedo {alb.round(3)} (IQR {(0.85 * (np.percentile(R, 75, 0) - np.percentile(R, 25, 0))).round(3)}; "
       f"per-frame spread {(per.max(0) - per.min(0)).round(3)}) -> sRGB {np.round(_srgb(alb), 3)} ({np.round(_srgb(alb) * 255).astype(int)})")
    return alb, per


# HEIGHTS: (frame, label, u, v_floor, v_cap_top, v_head, v_base_top): rows read on 3x zooms (refcam grid) along one casing's outer edge
# (one depth); v_base_top = the baseboard's top beside the casing (None where hidden)
CASINGS = [
    (410, "attic door (end wall), left casing", 778, 790, 626, 300, 760),
    (410, "attic door (end wall), right casing", 1012, 790, 626, 300, 760),
    (10819, "parents' doorway, left casing", 800, None, None, None, None),
]


def heights():
    for n, what, u, vf, vc, vh, vb in CASINGS:
        if None in (vf, vc, vh):
            continue
        cap = 2.032 * (vf - vc) / (vf - vh); base = 2.032 * (vf - vb) / (vf - vh) if vb else None
        print(f"film {n:5d} {what:40s}: cap top {cap:.3f} m" + (f", baseboard top {base:.3f} m" if base else ""))


# ARCHES (Oct 17; changes/2026-10-17-upstairs-arches.json). Columns read on luminance profiles (the arch's lower edge = where its
# dark face meets the lit soffit / ceiling beyond, +-3 px):
#  B (hall_corridor | hall_corridor_south, z 11.5): film 410 sees it frontal; Buzz's doorway is in the same wall plane (z 11.43), so the
#    doorway's head and threshold rows are a ruler ON that plane: heights = (v_floor - v) / (px per m). Shape: circle vs half-ellipse
#    through the springs and crown, residuals at the other edge points.
#  A (the gallery arch, plane x ~5.6): film 2085, camera solved by refcam on the linen door and the bath doorway (two depths, 80 in
#    ruler; measurements/cameras/film-2085.json, rms 1.7 px); its edge points measured on the plane x 5.607.
ARCH_B_410 = {"door_head_v": 208, "door_floor_v": 872, "jambs_u": (702, 1095),
              "edge": [(720, 254), (760, 236), (800, 224), (850, 214), (900, 213), (950, 218), (1000, 227), (1050, 246)]}
ARCH_A_2085 = [(390, 250), (420, 207), (700, 142), (1000, 118), (1300, 130), (1600, 178), (1745, 235)]   # (u, v) on the stair-well face


def arches():
    q = ARCH_B_410; ppm = (q["door_floor_v"] - q["door_head_v"]) / 2.032
    pts = [((u - (q["jambs_u"][0] + q["jambs_u"][1]) / 2) / ppm, (q["door_floor_v"] - v) / ppm) for u, v in q["edge"]]
    half = (q["jambs_u"][1] - q["jambs_u"][0]) / 2 / ppm; crown = max(y for _, y in pts)
    spring = np.mean([y for x, y in pts if abs(x) > 0.75 * half]) - 0.0   # nearest the jambs
    ends = [y for x, y in sorted(pts, key=lambda p: -abs(p[0]))[:2]]
    # fit spring as the curve's value at the jambs: circle through (+-half, s) and (0, crown); pick s by least squares
    best = None
    for s in np.arange(1.80, 1.98, 0.002):
        rise = crown - s; R = (half ** 2 + rise ** 2) / (2 * rise); yc = crown - R
        rc = [y - (yc + math.sqrt(max(R * R - x * x, 0))) for x, y in pts]
        re = [y - (s + rise * math.sqrt(max(1 - (x / half) ** 2, 0))) for x, y in pts]
        e = (np.sqrt(np.mean(np.square(rc))), np.sqrt(np.mean(np.square(re))))
        if best is None or e[0] < best[1][0]:
            best = (s, e, rc, re)
    s, (ec, ee), rc, re = best
    print(f"arch B (film 410, ruler: Buzz's doorway in the arch's plane, {ppm:.1f} px/m): clear span {2 * half:.3f} m, crown {crown:.3f} m,"
          f" springline {s:.3f} m (circle fit), rise/span {(crown - s) / (2 * half):.3f}")
    print(f"   residuals circle rms {ec * 100:.1f} cm (max {max(map(abs, rc)) * 100:.1f}), half-ellipse rms {ee * 100:.1f} cm (max {max(map(abs, re)) * 100:.1f})")
    import subprocess
    out = []
    for u, v in ARCH_A_2085:
        r = subprocess.run(["uv", "run", "-q", "--with", "numpy", "--with", "scipy", "python", "-I", str(ROOT / "tools/house/refcam.py"), "measure", "film-2085",
                            str(u), str(v), "--plane", "x=5.607"], capture_output=True, text=True).stdout.split()
        out.append((float(r[r.index("z") + 1]), float(r[r.index("(y") + 1].rstrip(")"))))
    zs = [z for z, _ in out]; z0, z1 = out[0][0], out[-1][0]; zm, a = (z0 + z1) / 2, (z1 - z0) / 2
    sp = (out[0][1] + out[-1][1]) / 2; cr = max(y for _, y in out)
    re = [y - (sp + (cr - sp) * math.sqrt(max(1 - ((z - zm) / a) ** 2, 0))) for z, y in out[1:-1]]
    R = (a * a + (cr - sp) ** 2) / (2 * (cr - sp)); rc = [y - (cr - R + math.sqrt(max(R * R - (z - zm) ** 2, 0))) for z, y in out[1:-1]]
    print(f"arch A (film 2085, refcam film-2085 on the plane x 5.607): jambs z {z0:.3f} / {z1:.3f} (plan 7.778 / 11.43), springs {out[0][1]:.3f} / {out[-1][1]:.3f},"
          f" crown {cr:.3f}; half-ellipse residuals rms {np.sqrt(np.mean(np.square(re))) * 100:.1f} cm, circle {np.sqrt(np.mean(np.square(rc))) * 100:.1f} cm")


if __name__ == "__main__":
    if "--arches" in sys.argv:
        arches()
    if "--paint" in sys.argv:
        paint()
    if "--heights" in sys.argv:
        heights()
    if "--overlay" in sys.argv:
        from PIL import Image, ImageDraw
        OUT.mkdir(parents=True, exist_ok=True)
        for n, regions in PAINT_SRC.items():
            im = Image.open(FILM.format(n)).convert("RGB"); a = np.asarray(im, float); d = ImageDraw.Draw(im)
            for u0, u1, v0, v1, what in regions:
                d.rectangle([u0, v0, u1, v1], outline=(255, 255, 0))
                for u, v in cap_edges(a, u0, u1, v0, v1):
                    d.line([(u, v - 26), (u, v - 6)], fill=(0, 255, 255)); d.line([(u, v + 4), (u, v + 12)], fill=(255, 0, 255))
            im.save(OUT / f"paint-{n}.jpg"); print(OUT / f"paint-{n}.jpg")
