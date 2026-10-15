"""Marina's foyer frames matched to the build (phase 5 comparison): each frame's camera solved from flight 1's step corners
(measured stair: rise, going, position), as foyer_cameras.py does for the film. Level camera (her CG walk keeps verticals
vertical), principal point at the centre; unknowns yaw, position, focal.
Points: tread nosing tips and the riser bottoms below them, on the wall side (z 11.41) or the open side (z 10.23).
usage: uv run --with numpy --with scipy python -I tools/house/marina_cameras.py [--views]
"""
import json
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/house"))
from foyer_cameras import R  # noqa: E402

CX, CY = 960, 540
VIDEO = ROOT / "Tour the Home Alone House_ Part 1, Main Floor [CG Tour] copy.mp4"
# frame (s) -> {"z": side, "tip": {step: (u, v)}, "bottom": {step: (u, v)}}; step 13 = the landing nosing
FRAMES = {
    "312": {"z": 11.41,
            "tip": {2: (80, 845), 3: (142, 745), 4: (197, 660), 5: (242, 590), 6: (282, 530), 7: (315, 475), 8: (345, 427),
                    9: (372, 385), 10: (397, 347), 11: (417, 315), 12: (437, 282), 13: (455, 255)},
            "bottom": {2: (80, 922), 3: (142, 815), 4: (197, 725), 5: (242, 650), 6: (282, 582), 7: (315, 522), 8: (345, 475),
                       9: (372, 430), 10: (397, 390), 11: (417, 352), 12: (437, 317), 13: (455, 290)}},
    # 1068 s: flight 1's open side close by; each visible tread end: its front (nosing) and back corners, top. Which steps they
    # are is solved for (k0 = the lowest one's number)
    "1068": {"z": 10.23, "ends": [(0, "front", (55, 915)), (0, "back", (194, 876)), (1, "front", (165, 772)), (1, "back", (270, 741)),
                                  (2, "front", (247, 642)), (2, "back", (330, 634)), (3, "front", (314, 545))]},
}


def stair():
    S = json.loads((ROOT / "spec/house_spec.json").read_text())
    steps = sorted([b for b in S["stair"]["boxes"] if b["name"].startswith("flight1_step")], key=lambda b: b["name"])
    land = next(b for b in S["stair"]["boxes"] if b["name"] == "landing")
    nose = [(b["x"][1], b["y"][1]) for b in steps] + [(land["x"][1], land["y"][1])]
    return nose, S["stair"]["rise_m"]


def proj(p, X):
    Xc = (np.atleast_2d(X) - p[1:4]) @ R(p[0]).T
    return np.c_[CX + p[4] * Xc[:, 0] / Xc[:, 2], CY + p[4] * Xc[:, 1] / Xc[:, 2]]


def points(fr, k0=0):
    nose, r = stair(); F = FRAMES[fr]; z = F["z"]; g = 0.295
    X, U = [], []
    for k, uv in F.get("tip", {}).items():
        X.append([nose[k - 1][0], nose[k - 1][1], z]); U.append(uv)
    for k, uv in F.get("bottom", {}).items():
        X.append([nose[k - 1][0], nose[k - 1][1] - r, z]); U.append(uv)
    for i, which, uv in F.get("ends", []):
        x, y = nose[k0 + i - 1]
        X.append([x if which == "front" else x - g, y, z]); U.append(uv)
    return np.array(X), np.array(U, float)


def solve(fr):
    tries = range(1, 11) if "ends" in FRAMES[fr] else [0]
    out = []
    for k0 in tries:
        X, U = points(fr, k0)
        res = lambda p: (proj(p, X) - U).ravel()
        best = min((least_squares(res, np.r_[y0, x0, -2.0, z0, f0], x_scale=np.r_[0.05, 1, 1, 1, 300])
                    for f0 in (900, 1400, 1900) for y0 in (-0.6, -0.2, 0.2) for x0 in (6.0, 8.5, 10.5) for z0 in (8.8, 9.6)),
                   key=lambda s: s.cost)
        out.append((best.cost, k0, best))
    cost, k0, best = min(out, key=lambda t: t[0])
    if len(out) > 1:
        print(f"   {fr}: lowest visible tread = step {k0} (next best rms {sorted(np.sqrt(2 * c / len(best.fun)) for c, _, _ in out)[1]:.1f} px)")
    return best.x, float(np.sqrt(np.mean(best.fun ** 2)))


if __name__ == "__main__":
    G = -3.026; cams = {}
    for fr in FRAMES:
        p, rms = solve(fr); cams[fr] = p
        print(f"Marina {fr} s: camera x {p[1]:.2f} height {p[2] - G:.2f} m z {p[3]:.2f}; yaw {np.degrees(p[0]):.1f}; f {p[4]:.0f} "
              f"(vfov {np.degrees(2 * np.arctan(CY / p[4])):.1f}); rms {rms:.1f} px")
    json.dump({f: {"yaw": float(p[0]), "pos": [float(v) for v in p[1:4]], "f": float(p[4])} for f, p in cams.items()},
              open(ROOT / "measurements/marina-foyer-cameras.json", "w"), indent=1)
