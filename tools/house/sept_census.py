"""September-model census: every room of the downloaded house (IntactHouseReference) against Marina's, one tolerance.

The September scene is the source GLB with windows cut and dressing added; no wall is moved (checked Oct 14 in the
SurveyBuilder scripts), so rooms are measured on the GLB itself (tools/survey/glb_section.py, 0.774 m/unit from its
80 in door). Each floor is sectioned above the door heads, rasterised, and each room flood-filled from a seed. Cased
openings that rise above the section are closed by CLOSE segments (wall end to wall end, listed below).
Marina: the traced overhead without stretch or thinning (shape_drift.marina). Plan axes: Marina x (side to side) is
GLB -X, Marina y (front to back) is GLB -Y, so widths compare directly.
Both scales come from an 80 in door, so proportions are scale-free; sizes share that one assumption.
usage: uv run --with numpy --with scipy --with matplotlib python -I tools/house/sept_census.py [--tol 5] [--selftest]
"""
import sys
from pathlib import Path

import numpy as np
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/survey"))
sys.path.insert(0, str(ROOT / "tools/house"))
from glb_section import section  # noqa: E402
from shape_drift import marina, area  # noqa: E402

HALL = {"hall_corridor", "hall_corridor_south", "hall_end"}   # Marina's hall pieces: plan splits, not rooms
RES = 0.02                                # m per raster cell
FLOORS = {"ground": 4.05, "upstairs": 7.95}   # native z: floor (1.3 / 5.2) + 2.13 m, above door heads, below ceilings
# Seeds in GLB plan metres, one per Marina room; None = no matching room in the September model.
SEEDS = {
    "ground": {"den": (-7, 3), "living_room": (-3, 3), "foyer": (1.5, 3), "vestibule": (1.5, -1.5),
               "dining_room": (5.5, 2), "sunroom": (9.5, 2), "kitchen": (9, 10), "back_stair": None},
    "upstairs": {"buzz_room": (-2.7, -0.5), "girls_room_b": (-2.7, 6), "kevin_jeff_room": (5.5, 0),
                 "hall_bath": (1.5, -1), "hall_corridor": (1.5, 5), "hall_corridor_south": (-1.6, 2.5),
                 "hall_end": (5, 2.5), "parents_bedroom": (9.5, 2.5), "parents_bath": (7.8, 7),
                 "girls_room_a": None},   # its place holds the back-stair hall (x 3.8..6.5 m, y 3.6..11.9 m)
}
CLOSE = {"ground": [((-4.78, 0.1), (-4.78, 2.05)),   # den | living cased opening
                    ((-0.80, 0.1), (-0.80, 2.05)),   # living | foyer
                    ((3.70, 0.1), (3.70, 2.05)),     # foyer | dining
                    ((7.70, 0.1), (7.70, 2.05)),     # dining | sunroom
                    ((0.45, -0.25), (2.45, -0.25)),  # vestibule | foyer
                    ((0.45, -1.95), (2.50, -1.95)),  # front door frame
                    ((3.75, 5.65), (4.75, 5.65)),    # dining rear face missing its header (kitchen face is solid)
                    ((7.60, 5.68), (7.85, 5.68)),    # sunroom rear corner open into the hollow wall
                    ((-0.95, 8.35), (-0.70, 8.35)),  # living | foyer hollow wall open at the rear
                    ((3.15, 8.40), (3.85, 8.40))],   # foyer rear alcove | strip behind the closed rear box
         "upstairs": [((-4.80, 0.15), (-4.80, 1.25)),  # Buzz: former side-wing doorway, infilled by BuzzBedroom.cs
                      ((-0.80, 0.10), (-0.80, 1.30)),  # Buzz door
                      ((-0.80, 1.25), (-0.80, 3.60)),  # hall | Marina's short south leg (no wall: plan split)
                      ((3.65, 1.60), (3.65, 3.50)),    # hall | end bay toward the parents' door (no wall: plan split)
                      ((-2.55, 3.55), (-1.25, 3.55)),  # front girls' room door
                      ((6.80, 1.85), (6.80, 3.25)),    # parents' door
                      ((7.00, 5.70), (8.45, 5.70))]}   # parents' bedroom | en suite opening     # extra wall segments ((x0, y0), (x1, y1)) closing tall cased openings


def raster(floor, extra=()):
    S = section(FLOORS[floor])
    S = S[(np.abs(S[..., 0]) < 14).all(1) & (S[..., 1] > -4).all(1) & (S[..., 1] < 16).all(1)]
    S = np.concatenate([S, np.array(CLOSE[floor] + list(extra), float).reshape(-1, 2, 2)])
    lo = S.reshape(-1, 2).min(0) - 0.5
    shape = tuple(((S.reshape(-1, 2).max(0) + 0.5 - lo) / RES).astype(int) + 1)
    wall = np.zeros(shape, bool)
    for a, b in S:
        n = int(np.linalg.norm(b - a) / (RES / 2)) + 2
        p = ((a + np.linspace(0, 1, n)[:, None] * (b - a) - lo) / RES).astype(int)
        wall[p[:, 0], p[:, 1]] = True
    return ndimage.binary_dilation(wall), lo     # 1-cell dilation seals diagonal leaks; costs ~2 cm per face


def rooms(floor, extra=()):
    wall, lo = raster(floor, extra)
    lab, _ = ndimage.label(~wall)
    out = {}
    for name, seed in SEEDS[floor].items():
        if seed is None:
            out[name] = None; continue
        i = lab[tuple(((np.array(seed) - lo) / RES).astype(int))]
        cells = np.argwhere(lab == i) * RES + lo
        dims = np.ptp(cells, 0) + RES + 2 * RES            # add back the dilation on both faces
        out[name] = {"dims": dims, "area": len(cells) * RES * RES, "cells": cells, "leak": dims.max() > 16}
    return out, wall, lo


def report(tol):
    rows, fails = [], 0
    for floor in FLOORS:
        M = marina(floor); R, _, _ = rooms(floor)
        for name in SEEDS[floor]:
            m = M.get(name); r = R.get(name)
            if m is None:
                continue
            dm, am = np.ptp(m, 0), area(m)
            if r is None:
                rows.append((floor, name, dm, None, am, None, "MISSING")); fails += 1; continue
            d, a = r["dims"], r["area"]
            turned = np.abs(d[::-1] / dm - 1).max() < np.abs(d / dm - 1).max()   # same room rotated 90 deg fits better
            d = d[::-1] if turned else d
            ok = np.abs(d / dm - 1).max() * 100 <= tol and not r["leak"]
            if name in HALL:
                v = "(plan split; judge the hall by width)"
            else:
                v = "LEAK" if r["leak"] else ("ok" if ok else "FAIL") + (" (turned 90 deg)" if turned else "")
                fails += not ok
            rows.append((floor, name, dm, d, am, a, v))
    ft = lambda m: f"{round(m / 0.0254) // 12}'{round(m / 0.0254) % 12:02d}\""
    print(f"{'floor':<9}{'room':<20}{'Marina w x d':>18}{'September w x d':>20}{'w':>6}{'d':>6}{'area':>6}  verdict")
    for floor, name, dm, d, am, a, v in rows:
        if d is None:
            print(f"{floor:<9}{name:<20}{ft(dm[0]):>8} x {ft(dm[1]):<8}{'(no room)':>20}{'':>18}  {v}"); continue
        print(f"{floor:<9}{name:<20}{ft(dm[0]):>8} x {ft(dm[1]):<8}{ft(d[0]):>9} x {ft(d[1]):<9}"
              f"{d[0] / dm[0] - 1:+6.0%}{d[1] / dm[1] - 1:+6.0%}{a / am - 1:+6.0%}  {v}")
    print(f"\n{fails} room(s) outside +-{tol:.0f}% on a side, leaking or missing.")
    return rows


def plot():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(26, 12))
    for ax, floor in zip(axes, FLOORS):
        R, wall, lo = rooms(floor)
        ax.imshow(wall.T, origin="lower", extent=(lo[0], lo[0] + wall.shape[0] * RES, lo[1], lo[1] + wall.shape[1] * RES), cmap="gray_r")
        for (name, r), c in zip(R.items(), plt.cm.tab10.colors * 2):
            if r is None or r["leak"]:
                continue
            ax.scatter(*r["cells"][::40].T, s=1, color=c, alpha=0.3)
            ax.text(*r["cells"].mean(0), name, fontsize=10, ha="center")
        for a, b in CLOSE[floor]:
            ax.plot([a[0], b[0]], [a[1], b[1]], "r-", lw=2)
        ax.set_title(f"September model {floor}: measured rooms (red = closures)"); ax.grid(True, lw=0.3)
    out = ROOT / "spec/captures/sept-census.png"
    fig.savefig(out, dpi=60); print(f"map -> {out}")


def selftest():
    """The measurement must move by a known amount: a wall 30 cm inside the living room's west face shrinks its width."""
    R, _, _ = rooms("ground")
    w0 = R["living_room"]["dims"][0]
    x = R["living_room"]["cells"][:, 0].min() + 0.30
    R2, _, _ = rooms("ground", extra=[((x, -3.0), (x, 9.0))])
    dw = w0 - R2["living_room"]["dims"][0]
    assert abs(dw - 0.30) < 0.05, dw
    print(f"selftest ok: injected 30 cm wall moved the width by {dw * 100:.0f} cm")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest(); sys.exit()
    report(float(sys.argv[sys.argv.index("--tol") + 1]) if "--tol" in sys.argv else 5.0)
    plot()
