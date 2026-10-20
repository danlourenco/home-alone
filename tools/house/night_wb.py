"""night_wb: how orange our night interiors read against the film, and the HDRP White Balance temperature that would match it
(Oct 20: the hall bath night A/B read R/B 4.15 against film 336's 1.25; the film was shot on tungsten-balanced stock).

For each room: boxes on the SAME surface (white tile, a white jersey, the stringer, the room's paper ground, a white tablecloth) in a
film night frame and in our night render; R/B = mean red / mean blue of the box (sRGB). The film-match temperature is solved with
HDRP's own White Balance maths (ColorUtils.ColorBalanceToLMSCoeffs + the LMS matrices of ColorGrading), applied to our box's linear
colour: an approximation (HDRP applies it before tonemapping), checked by rendering the variant and measuring again.

  uv run --with numpy --with pillow python -I tools/house/night_wb.py [RUN_DIR [TAG]]    # TAG e.g. -A1 (the base column of a -perfab run)
  uv run --with numpy --with pillow python -I tools/house/night_wb.py --overlay OUT.jpg [RUN_DIR [TAG]]   # boxes drawn, for checking
  ... --selftest
Boxes are fractions of the image (x0, y0, x1, y1). Our renders: the tour's <pose>-night<TAG>.png; FALLBACK when a run lacks a pose.
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
FILM = str(ROOT / "0-homealone/full/homealone-movie-screencaps.com-{}.jpg")
PERF = Path.home() / ".cache/home-alone-perf/runs"
FALLBACK = {"hallbath": PERF / "hallbath-B1/hallbath-night.png", "buzz": PERF / "hallbath-B1/buzz-night.png",
            "foyer": PERF / "rel-oct20/foyer-night.png", "living": PERF / "rel-oct20/living-night.png",
            "parents": PERF / "rel-oct20/parents-night.png", "dining": ROOT / "spec/captures/views/purchased/chippendale/built-night-dining246.png"}
W, H = 960.0, 528.0   # box coordinates below: the 960-wide film frame (528 high) / our render (540 high)
R = lambda x0, y0, x1, y1, h=H: (x0 / W, y0 / h, x1 / W, y1 / h)
O = lambda x0, y0, x1, y1: R(x0, y0, x1, y1, 540.0)
ROOMS = {   # room: ([(film frame, box)], [our box], surface)
    "hallbath": ([(336, R(590, 345, 665, 420))], [O(586, 397, 634, 414)], "white wall tile right of the sink"),
    "buzz": ([(479, R(185, 50, 245, 170))], [O(748, 142, 800, 200)], "Jordan poster's white jersey"),
    "foyer": ([(851, R(20, 300, 60, 360))], [O(120, 282, 192, 354)], "white stair stringer / panel below it"),
    "living": ([(5650, R(110, 60, 200, 150))], [O(535, 130, 620, 230)], "the room's cream floral paper (same paper)"),
    "parents": ([(151, R(480, 200, 560, 380))], [O(100, 250, 200, 350)], "the room's floral stripe paper (same paper)"),
    "dining": ([(251, R(180, 370, 420, 450))], [O(290, 265, 600, 340)], "white lace tablecloth"),
    "kitchen": ([(1051, R(10, 30, 100, 90)), (1151, R(10, 30, 100, 90))], [O(0, 0, 0, 0)], "the room's cream paper (set in POSE_BOX)"),
}
POSE_BOX = {}   # our box per pose when the tour render differs from FALLBACK's framing (filled once the kitchen/dining poses exist)


def box_rgb(path, b):
    a = np.asarray(Image.open(path).convert("RGB"), dtype=float) / 255
    h, w = a.shape[:2]
    x0, y0, x1, y1 = int(b[0] * w), int(b[1] * h), int(b[2] * w), int(b[3] * h)
    return a[y0:y1, x0:x1].reshape(-1, 3).mean(0)


def lin(c):
    c = np.asarray(c, float); return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def srgb(c):
    c = np.clip(c, 0, None); return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


# HDRP White Balance (Unity's ColorUtils.ColorBalanceToLMSCoeffs; ColorGrading LIN_2_LMS / LMS_2_LIN)
L2M = np.array([[3.90405e-1, 5.49941e-1, 8.92632e-3], [7.08416e-2, 9.63172e-1, 1.35775e-3], [2.31082e-2, 1.28021e-1, 9.36245e-1]])
M2L = np.array([[2.85847e+0, -1.62879e+0, -2.48910e-2], [-2.10182e-1, 1.15820e+0, 3.24281e-4], [-4.18120e-2, -1.18169e-1, 1.06867e+0]])


def wb_coeffs(temperature, tint=0.0):
    t1, t2 = temperature / 65.0, tint / 65.0
    x = 0.31271 - t1 * (0.1 if t1 < 0 else 0.05)
    y = 2.87 * x - 3 * x * x - 0.27509507 + t2 * 0.05
    X, Y, Z = x / y, 1.0, (1 - x - y) / y
    lms = np.array([0.7328 * X + 0.4296 * Y - 0.1624 * Z, -0.7036 * X + 1.6975 * Y + 0.0061 * Z, 0.0030 * X + 0.0136 * Y + 0.9834 * Z])
    return np.array([0.949237, 1.03542, 1.08728]) / lms


def apply_wb(rgb_srgb, temperature):
    return srgb(M2L @ (wb_coeffs(temperature) * (L2M @ lin(rgb_srgb))))


def rb(c):
    return float(c[0] / max(c[2], 1e-4))


def solve(rgb_srgb, target_rb):
    """temperature (HDRP slider, -100..100) that brings rgb's R/B to target (bisection; R/B falls as temperature falls)"""
    lo, hi = -100.0, 100.0
    if rb(apply_wb(rgb_srgb, lo)) > target_rb:
        return lo
    for _ in range(60):
        m = (lo + hi) / 2
        lo, hi = (m, hi) if rb(apply_wb(rgb_srgb, m)) < target_rb else (lo, m)
    return (lo + hi) / 2


def measure(run=None, tag=""):
    rows = []
    for room, (films, ours, surface) in ROOMS.items():
        f = [rb(box_rgb(FILM.format(n), b)) for n, b in films]
        p = Path(run) / f"{room}-night{tag}.png" if run else None
        if not (p and p.exists()):
            p = FALLBACK.get(room)
        ob = POSE_BOX.get(room, ours[0])
        if p is None or not p.exists() or ob[2] <= ob[0]:
            rows.append((room, surface, f, None, None, None, None)); continue
        c = box_rgb(p, ob)
        rows.append((room, surface, f, rb(c), solve(c, float(np.mean(f))), c, p))
    return rows


def overlay(out, run=None, tag=""):
    tiles = []
    for room, (films, ours, _) in ROOMS.items():
        p = Path(run) / f"{room}-night{tag}.png" if run else None
        p = p if p and p.exists() else FALLBACK.get(room)
        for path, b in [(FILM.format(n), bx) for n, bx in films] + ([(p, POSE_BOX.get(room, ours[0]))] if p and p.exists() else []):
            im = Image.open(path).convert("RGB").resize((640, 352)); d = ImageDraw.Draw(im)
            d.rectangle([b[0] * 640, b[1] * 352, b[2] * 640, b[3] * 352], outline=(0, 255, 0), width=2); d.text((4, 4), f"{room} {Path(str(path)).name}", fill=(255, 255, 0))
            tiles.append(im)
    sh = Image.new("RGB", (640 * 3, 352 * ((len(tiles) + 2) // 3)))
    for i, t in enumerate(tiles):
        sh.paste(t, ((i % 3) * 640, (i // 3) * 352))
    sh.save(out, quality=85); print(out)


def selftest():
    assert np.allclose(wb_coeffs(0), 1, atol=2e-3), wb_coeffs(0)   # 0 = identity
    o = np.array([0.8, 0.5, 0.2])
    assert rb(apply_wb(o, -50)) < rb(o) < rb(apply_wb(o, 50))     # negative = cooler, positive = warmer (Unity docs)
    t = solve(o, 2.5); assert abs(rb(apply_wb(o, t)) - 2.5) < 1e-3, t
    print("selftest ok")


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["--selftest"]:
        selftest(); sys.exit()
    if a[:1] == ["--overlay"]:
        overlay(a[1], *a[2:4]); sys.exit()
    rows = measure(*a[:2])
    print("| room | surface | film R/B | ours R/B | film-match temperature |\n|---|---|---|---|---|")
    for room, surface, f, o, t, _, p in rows:
        print(f"| {room} | {surface} | {' / '.join(f'{x:.2f}' for x in f)} | {'-' if o is None else f'{o:.2f}'} | {'-' if t is None else f'{t:.0f}'} |")
    ts = [r[4] for r in rows if r[4] is not None and r[0] != "buzz"]
    if ts:
        print(f"median film-match temperature (Buzz excluded: his room stays as it is): {np.median(ts):.0f}")
