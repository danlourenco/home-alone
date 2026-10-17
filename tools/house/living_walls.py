"""living_walls: the living room measured from Marina's living clip (sfm-work/rooms/living, Part 1, 212 frames at 4 fps) for its
upgrade (Oct 16 2026: paper, windows, fireplace, furniture), the den method (tools/house/den_walls.py): cameras solved on the BUILT
room's corners, ceiling lines and floor lines, then pixels intersected with the built room's planes.

Marina's camera in this clip is NOT level (the den clip's was): the den-side wall's ceiling and floor lines meet at y ~499 in
frame 165, 41 px above the frame centre (a ~1.8 deg pitch), so refcam's level model leaves 13 px rms. Here the camera has yaw,
pitch and roll (and position) at the clip's COLMAP focal (1325 px, SIMPLE_PINHOLE). Saved in refcam's format plus "pitch"/"roll".

Rulers, two of different kinds, never averaged: the built room's width/length (overhead-trace:ground) through the corner points,
and the 8 ft ceiling (ceiling-8ft: living; measured at the door jambs, tools/house/ground_ceiling.py). Independent checks named per
number in the report.

  uv run --with numpy --with scipy --with pillow python -I tools/house/living_walls.py          # solve cameras, print every pick
"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import refcam as rc   # noqa: E402

G = rc.G
FOCAL = 1325.07
ROOM = {"x0": 1.58, "x1": 9.954, "z0": 11.57, "z1": 16.07}     # spec/house_spec.ground.json living_room (rear, front, foyer, den)
CEIL = 2.438


def frame(n):
    return ROOT / f"sfm-work/rooms/living/colmap/images/shot00/f_{n:05d}.jpg"


def Rot(c):
    """spec -> camera (right, down, forward): refcam's level yaw rotation, then pitch (about the camera's right axis, + = up) and roll"""
    p, r = c.get("pitch", 0.0), c.get("roll", 0.0)
    Rp = np.array([[1, 0, 0], [0, np.cos(p), np.sin(p)], [0, -np.sin(p), np.cos(p)]])
    Rr = np.array([[np.cos(r), -np.sin(r), 0], [np.sin(r), np.cos(r), 0], [0, 0, 1]])
    return Rr @ Rp @ rc.R(c["yaw"])


def proj(c, X):
    Xc = (np.atleast_2d(X) - np.array(c["pos"])) @ Rot(c).T
    return np.c_[c["cx"] + c["f"] * Xc[:, 0] / Xc[:, 2], c["cy"] + c["f"] * Xc[:, 1] / Xc[:, 2]], Xc[:, 2]


def ray(c, u, v):
    d = Rot(c).T @ np.array([(u - c["cx"]) / c["f"], (v - c["cy"]) / c["f"], 1.0])
    return np.array(c["pos"]), d


SEEDS = {"living-f165": (165, 0.0, (8.0, 13.8)), "living-f3": (3, 0.0, (5.5, 13.8)), "living-f89": (89, 180.0, (4.5, 13.5)),
         "living-f117": (117, 90.0, (6.0, 14.5))}


def solve(name, quiet=False):
    from scipy.optimize import least_squares
    fr, yaw0, (x0, z0) = SEEDS[name]
    P = json.loads((ROOT / f"measurements/cameras/points/{name}.json").read_text())
    pts = [p for p in P if "line" not in p]; lines = [p for p in P if "line" in p]
    X = np.array([rc.xyz_of(p) for p in pts]); U = np.array([p["uv"] for p in pts], float)
    cam = lambda q: dict(cx=960, cy=540, f=FOCAL, yaw=q[0], pitch=q[1], roll=q[2], pos=list(q[3:6]))
    def res(q):
        c = cam(q); r = list((proj(c, X)[0] - U).ravel()) if len(X) else []
        for p in lines:
            (pa, pb), _ = proj(c, np.array(p["line"], float)); t = pb - pa; n = np.array([-t[1], t[0]]) / np.linalg.norm(t)
            r.append(float((np.array(p["uv"]) - pa) @ n))
        return np.array(r)
    s = least_squares(res, [np.radians(yaw0), 0.0, 0.0, x0, G + 1.3, z0], x_scale=[0.1, 0.02, 0.02, 1, 1, 1]); r = res(s.x); c = cam(s.x)
    per = [float(np.hypot(r[2 * i], r[2 * i + 1])) for i in range(len(pts))] + [abs(float(v)) for v in r[2 * len(pts):]]
    c.update(name=name, frame=str(frame(fr).relative_to(ROOT)), size=[1920, 1080], rms_px=round(float(np.sqrt(np.mean(r ** 2))), 2),
             points=pts + lines, residuals_px=[round(e, 2) for e in per])
    (ROOT / f"measurements/cameras/{name}.json").write_text(json.dumps(c, indent=1))
    if not quiet:
        print(f"{name}: x {c['pos'][0]:.2f} z {c['pos'][2]:.2f} eye {c['pos'][1] - G:.2f} m yaw {np.degrees(c['yaw']):.1f} pitch {np.degrees(c['pitch']):.2f} "
              f"roll {np.degrees(c['roll']):.2f}; rms {c['rms_px']} px; worst {max(per):.1f} px ({(pts + lines)[int(np.argmax(per))].get('note')})")
    return c


def hit(name, u, v, plane):
    """pixel -> spec point (x, height above the ground floor, z) on 'x=..', 'z=..' or 'h=..'"""
    c = json.loads((ROOT / f"measurements/cameras/{name}.json").read_text()); o, d = ray(c, u, v)
    ax, val = plane.split("="); val = float(val); i = {"x": 0, "z": 2, "h": 1}[ax]; val = G + val if ax == "h" else val
    X = o + (val - o[i]) / d[i] * d
    return np.array([X[0], X[1] - G, X[2]])


PICKS = [   # (camera, label, u, v, plane): pixels read on 2.5-3x zooms of the clip frames (+-2 px)
    ("living-f165", "mantel shelf top, left end", 897, 470, "x=1.58"), ("living-f165", "mantel shelf top, right end", 1243, 468, "x=1.58"),
    ("living-f165", "surround left edge", 945, 600, "x=1.58"), ("living-f165", "surround right edge", 1200, 600, "x=1.58"),
    ("living-f165", "firebox left", 1008, 600, "x=1.58"), ("living-f165", "firebox right", 1142, 600, "x=1.58"), ("living-f165", "firebox top", 1075, 568, "x=1.58"),
    ("living-f165", "wreath centre", 1075, 380, "x=1.58"),
    ("living-f165", "den-side window: drape outer", 670, 420, "x=1.58"), ("living-f165", "den-side window: glass left", 730, 420, "x=1.58"),
    ("living-f165", "den-side window: glass right", 825, 420, "x=1.58"), ("living-f165", "den-side window: drape outer right", 885, 420, "x=1.58"),
    ("living-f165", "den-side window: drape top", 760, 308, "x=1.58"),
    ("living-f165", "foyer-side window: drape outer", 1292, 420, "x=1.58"), ("living-f165", "foyer-side window: glass left", 1360, 420, "x=1.58"),
    ("living-f165", "foyer-side window: glass right", 1465, 420, "x=1.58"), ("living-f165", "foyer-side window: drape outer right", 1540, 420, "x=1.58"),
    ("living-f165", "foyer-side window: drape top", 1400, 298, "x=1.58"),
]


def report():
    for n in SEEDS:
        if (ROOT / f"measurements/cameras/points/{n}.json").exists():
            solve(n)
    for cam, lab, u, v, pl in PICKS:
        if (ROOT / f"measurements/cameras/{cam}.json").exists():
            x, h, z = hit(cam, u, v, pl); print(f"  {cam:12s} {lab:44s} x {x:6.3f}  h {h:6.3f}  z {z:6.3f}   [{pl}]")


if __name__ == "__main__":
    report()
