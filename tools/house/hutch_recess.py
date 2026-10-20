"""hutch_recess: does the breakfast hutch stand proud of its wall, or in a recess? (walk note Oct 19 22:20, 'supposed to be recessed').

Film 2104 (= the user's IMG_4305) is shot from the hutch's LEFT, so a freestanding case shows its left end. Projects the hutch's
left/right end corners (wall corner and front corner, lower case 0.45 deep at y 0.70/1.00, upper 0.32 at 1.60) through film 2104's
solved camera (film2104_measure.fit: the island's 6 in tiles) and prints each end face's width in pixels: what a proud case would show.
Compare with the frame (spec/captures/picks/hutch-2104-ends.png: cyan = wall corners, magenta = proud front corners): the film shows
no end face, wallpaper runs straight to both cases' left edges, and those edges line up.

  uv run --with numpy --with scipy python -I tools/house/hutch_recess.py
"""
import runpy
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
ns = runpy.run_path(str(ROOT / "tools/house/film2104_measure.py"), run_name="lib")
f, R, Cw, rms = ns["fit"]()
C0 = np.array([960.0, 529.0])
K = np.array([[f, 0, C0[0]], [0, f, C0[1]], [0, 0, 1]]); Ki = np.linalg.inv(K)
def ray(p): return R.T @ (Ki @ np.array([p[0], p[1], 1.0]))
def at_y(p, y): r = ray(p); return Cw + (y - Cw[1]) / r[1] * r
off = np.array([0.354, 0.914, 0.834]) - at_y((683, 378), 0.0)        # film2104_measure's registration
def proj(X):
    q = R @ (np.asarray(X, float) - off - Cw); return f * q[:2] / q[2] + C0
print(f"camera fit rms {rms:.2f} px, camera spec {np.round(Cw + off, 3).tolist()}")
XF, Z0, Z1 = 4.12, 4.565, 6.395                                         # kitchen.json hutch: wall face, ends
for nm, d, y in (("lower case", 0.45, 0.70), ("lower case", 0.45, 1.00), ("upper case", 0.32, 1.60)):
    wl, fl = proj((XF, y, Z0)), proj((XF - d, y, Z0))
    print(f"{nm} at y {y:.2f}: a proud left end would span u {wl[0]:.0f} -> {fl[0]:.0f} = {fl[0] - wl[0]:.0f} px wide")
assert abs(proj((XF, 0.7, Z0))[0] - proj((XF - 0.45, 0.7, Z0))[0]) > 20, "the end face should be visible from this camera"
