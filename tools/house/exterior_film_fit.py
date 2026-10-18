"""exterior_film_fit: the exterior skin's heights against the film (Oct 18 2026; changes/2026-10-18-exterior-shell.json).

Film 4382 (straight-on, sharp) and 6399 (oblique left): a pinhole camera (height fixed at the street, 1.7 m over the front yard; yaw,
pitch, roll, focal and plan position free) is solved on the facade's window centres (picks: spec/captures/picks/exterior/f4382_*.png,
f6399_*.png, read on 20 px grids), with the upper storey's height offset left free (dy). Then the skin's eave, frieze, ridge and
dormers (spec/exterior_shell.json) are projected and compared with the film. Ratio check on a third frame (4443, same set-up as 4382):
(upper sill - ground head) / upper window height, both in the facade plane.

  uv run --with numpy --with scipy python -I tools/house/exterior_film_fit.py      # exit 1 if 4382's fit or the ratio check fails
"""
import json
import math
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares

ROOT = Path(__file__).resolve().parents[2]
S = json.loads((ROOT / "spec/exterior_shell.json").read_text())
W_, H_ = 1920, 1058
CY = -2.6                         # camera height: 1.7 m over the front yard (-4.32)


def look(yaw, pitch, roll):
    f = np.array([-math.cos(pitch) * math.cos(yaw), math.sin(pitch), math.cos(pitch) * math.sin(yaw)])
    r = np.cross(f, [0, 1, 0]); r /= np.linalg.norm(r); u = np.cross(r, f)
    c, s = math.cos(roll), math.sin(roll)
    return f, c * r + s * u, -s * r + c * u


def project(P, cam):
    cx, cy, cz, yaw, pitch, roll, f = cam
    F, R, U = look(yaw, pitch, roll); d = np.atleast_2d(P) - np.array([cx, cy, cz]); zc = d @ F
    return np.stack([W_ / 2 + f * (d @ R) / zc, H_ / 2 - f * (d @ U) / zc], -1)


FM = S["front_main"] + S["veneer"]                 # the main block's brick face
up_c = (S["upper_windows"][0]["y0"] + S["upper_windows"][0]["y1"]) / 2   # the skin's upper window centre (world)
gh = -3.026 + 2.03                                  # ground French windows' head (spec/geometry.json)
FRAMES = {   # film pixel -> spec point; True marks an upper-storey point (its height gets dy)
    "4382": [((527, 507), (FM, up_c, 14.643), 1), ((702, 507), (FM, up_c, 12.938), 1), ((947, 505), (FM, up_c, 9.716), 1),
             ((1183, 502), (FM, up_c, 6.702), 1), ((1355, 502), (FM, up_c, 4.742), 1),
             ((521, 765), (FM, (-3.026 + gh) / 2, 14.643), 0), ((699, 765), (FM, (-3.026 + gh) / 2, 12.938), 0),
             ((1194, 759), (FM, (-3.026 + gh) / 2, 6.702), 0), ((1370, 759), (FM, (-3.026 + gh) / 2, 4.742), 0),
             ((291, 538), (9.506, up_c, 18.31), 1), ((262, 763), (9.506, (-2.616 - 0.94) / 2, 18.31), 0)],
    "6399": [((824, 458), (FM, up_c, 14.643), 1), ((968, 466), (FM, up_c, 12.938), 1), ((1152, 477), (FM, up_c, 9.716), 1),
             ((1321, 486), (FM, up_c, 6.702), 1), ((1434, 490), (FM, up_c, 4.742), 1), ((1557, 508), (9.647, up_c, 0.905), 1),
             ((825, 613), (FM, gh, 14.643), 0), ((970, 615), (FM, gh, 12.938), 0), ((1327, 624), (FM, gh, 6.702), 0),
             ((1440, 626), (FM, gh, 4.742), 0), ((1561, 632), (9.647, -0.94, 0.905), 0), ((646, 614), (9.506, -0.94, 16.994), 0),
             ((646, 401), (9.506, S["upper_windows"][0]["y1"], 16.994), 1)]}
X0 = {"4382": [26, 10, 0.0, 0.2, 0.0, 1300], "6399": [24, 17, -0.32, 0.2, 0.0, 1040]}
FILM = {"4382": {"ridge": 265, "gutter": 401, "frieze": 446, "dormer_peak": 213, "dormer_sill": 372},
        "6399": {"ridge": 193, "gutter": 370, "dormer_peak": 177, "dormer_sill": 330}}


def fit(name):
    P2 = np.array([p for p, _, _ in FRAMES[name]], float); P3 = np.array([q for _, q, _ in FRAMES[name]], float)
    up = np.array([u for _, _, u in FRAMES[name]], bool)
    def res(p):
        Q = P3.copy(); Q[up, 1] += p[6]
        return (project(Q, (p[0], CY, p[1], p[2], p[3], p[4], p[5])) - P2).ravel()
    r = least_squares(res, X0[name] + [0.0])
    cam = (r.x[0], CY, r.x[1], r.x[2], r.x[3], r.x[4], r.x[5])
    return cam, r.x[6], float(np.sqrt((r.fun.reshape(-1, 2) ** 2).sum(1)).mean())


def features(cam):
    m = [q for q in S["roofs"] if q["name"] == "main"][0]
    ridge = m["eave"] + m["tan"] * (m["x"][1] - m["x"][0]) / 2 + 0.05
    D = S["dormers"][1]
    pr = lambda p, z=9.7: float(project(np.array(p), cam)[0][1])
    return {"ridge": pr((5.855, ridge, 9.7)), "gutter": pr((FM + 0.5, S["eave"] + 0.03, 9.7)), "frieze": pr((FM, S["eave"] - 0.38, 9.7)),
            "dormer_peak": pr((D["face"] + 0.08, D["peak"], D["z"])), "dormer_sill": pr((D["face"], D["sill"], D["z"]))}


def main():
    ok = True
    for name in FRAMES:
        cam, dy, e = fit(name)
        f = features(cam)
        diffs = {k: round(f[k] - v, 1) for k, v in FILM[name].items()}
        print(f"film {name}: fit {e:.1f} px, upper-storey residual dy {dy:+.3f} m, focal {cam[6]:.0f}; model - film px: {diffs}")
        if name == "4382":
            ok &= abs(dy) < 0.08 and all(abs(v) < 15 for v in diffs.values())
    # ratio on 4443: upper sill (stone) bottom 567, upper mould top 448, ground mould top 669 (spec/captures/picks/exterior/f4443_ratio.png)
    film_r = (669 - 567) / (567 - 448)
    w = S["upper_windows"][0]
    top, bot = w["y1"] + 0.07, w["y0"] - 0.07
    model_r = (bot - (gh + 0.07)) / (top - bot)
    print(f"film 4443 ratio (upper sill to ground head) / (upper window): film {film_r:.3f}, skin {model_r:.3f} ({100 * (model_r / film_r - 1):+.1f}%)")
    ok &= abs(model_r / film_r - 1) < 0.08
    print("ok" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
