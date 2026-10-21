"""nb_film1888_camera: solve film 1888's camera (day, from the airport van across Lincoln) on OUR house's facade (Oct 20 2026, step 3),
so Marley's house (lot_A+1, beyond our garage at film-left) can be rendered from the film's own viewpoint.

Known 3D (spec x, WORLD y, spec z; spec/exterior_shell.json, which the film 4382/6399 solves fixed): the four front upper windows'
centres (x 10.37, y 1.134), the main hip's front eave corners (10.77, 2.204, 2.464 / 16.61), the two front dormers' gable peaks
(9.65, 5.394, 6.702 / 12.938). Picks by eye on 1.5-1.6x gridded crops (+-3 px). Principal point at the frame centre.
  uv run --with numpy --with scipy python -I tools/house/nb_film1888_camera.py  -> art/home_alone/references/neighborhood/data/film1888_camera.json
"""
import json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation as Rot

ROOT = Path(__file__).resolve().parents[2]
C0 = np.array([960.0, 529.0])
PTS = [((10.37, 1.134, 14.643), (763, 623)), ((10.37, 1.134, 12.938), (846, 620)), ((10.37, 1.134, 9.716), (970, 601)),
       ((10.37, 1.134, 4.742), (1211, 573)), ((10.77, 2.204, 16.61), (682, 584)), ((10.77, 2.204, 2.464), (1312, 507)),
       ((9.65, 5.394, 12.938), (868, 428))]   # the right dormer: its peak is behind the trunk and branches (dropped)


def proj(p, X):
    f, R, C = p[0], Rot.from_rotvec(p[1:4]).as_matrix(), p[4:7]; q = R @ (np.asarray(X, float) - C); return f * q[:2] / q[2] + C0


def res(p):
    """+ priors: the van's window ~1.6 m over Lincoln (world y -2.7 +- 0.4), x across the street (38-46), no roll (the brick piers stand vertical)."""
    R = Rot.from_rotvec(p[1:4]).as_matrix()
    return np.concatenate([np.concatenate([proj(p, X) - np.array(uv) for X, uv in PTS]), [(p[5] + 2.75) / 0.15 * 10, R[0, 1] * 300, (max(0, 38 - p[4]) + max(0, p[4] - 46)) * 3]])


def main():
    best = None
    for cx in (40, 50, 60):
        for cz in (0, 10, 20, 30):
            fwd = np.array([10 - cx, 1.0 - (-1.5), 10 - cz], float); fwd /= np.linalg.norm(fwd)
            right = np.cross(fwd, [0, 1.0, 0]); right /= np.linalg.norm(right); down = np.cross(fwd, right)
            Rm = np.vstack([right, down, fwd])
            if np.linalg.det(Rm) < 0: Rm[0] = -Rm[0]
            p0 = np.r_[1500, Rot.from_matrix(Rm).as_rotvec(), cx, -1.5, cz]
            s = least_squares(res, p0)
            if best is None or s.cost < best.cost: best = s
    p = best.x; R = Rot.from_rotvec(p[1:4]).as_matrix(); r = res(p)[:2 * len(PTS)]
    out = {"frame": 1888, "f_px": round(float(p[0]), 1), "camera_spec_world_y": np.round(p[4:7], 2).tolist(), "forward_spec": np.round(R[2], 4).tolist(),
           "up_spec": np.round(-R[1], 4).tolist(), "rms_px": round(float(np.sqrt((r ** 2).mean())), 2),
           "residuals_px": [np.round(r[2 * i:2 * i + 2], 1).tolist() for i in range(len(PTS))],
           "convention": "y is WORLD (ground floor -3.026; a lot at grade g rel gy sits at gy + g, gy -2.996); image x right, y down, pp (960, 529)"}
    P = ROOT / "art/home_alone/references/neighborhood/data/film1888_camera.json"; P.write_text(json.dumps(out, indent=1)); print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
