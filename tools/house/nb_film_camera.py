"""nb_film_camera: solve the film 11581 camera (the Murphys across Lincoln, night) from the house's own corners, Oct 20 2026.

Known 3D (spec x, height over the lot's grade, z): the 2022 county footprint (main block x 63.6-78.2, z 5.1-18.2; porch front x 60.6,
z 6.05-17.9) and the lidar hip apex (ridge front end x 70.15, z 11.65; height a prior 11.0 +- 0.3 from the re-registered ISGS nDSM).
Unknown and fitted with the camera: eave-edge height, porch-roof edge height, eave overhang. Picks: gridded 3x crops of the frame
(scratch crops, by eye, +-3 px). Verticals: the porch columns stand vertical in the frame (no keystone).
  uv run --with numpy --with scipy python -I tools/house/nb_film_camera.py   -> art/home_alone/references/neighborhood/data/film11581_camera.json
"""
import json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation as Rot

ROOT = Path(__file__).resolve().parents[2]
C0 = np.array([960.0, 529.0])
PICK = {"apex": (1310, 22), "eave_fl": (848, 247), "eave_fr": (1707, 185), "eave_rr": (1790, 302),
        "porch_fl": (782, 413), "porch_fr": (1652, 383)}
COLS = [(60.6, 6.05, 870), (60.6, 17.9, 1590)]   # porch columns: spec x, z and their image x (vertical in the frame)
KERB = [(750, 866), (1450, 878)]                # far kerb's top edge (3x crops, +-4 px; the snow bank's road edge on the left)
OP = 0.25                                        # porch-roof overhang beyond its columns (authored)


def pts(h):
    R, he, hp, o = h
    return {"apex": (70.15, R, 11.65), "eave_fl": (63.6 - o, he, 5.1 - o), "eave_fr": (63.6 - o, he, 18.2 + o),
            "eave_rr": (78.2 + o, he, 18.2 + o), "porch_fl": (60.6 - OP, hp, 6.05 - OP), "porch_fr": (60.6 - OP, hp, 17.9 + OP)}


def unpack(p):
    return p[0], Rot.from_rotvec(p[1:4]).as_matrix(), p[4:7], p[7:11]


def proj(p, X):
    f, R, C, _ = unpack(p); q = R @ (np.asarray(X, float) - C); return f * q[:2] / q[2] + C0


def res(p):
    f, R, C, h = unpack(p); P = pts(h); r = []
    for k, uv in PICK.items(): r += list(proj(p, P[k]) - uv)
    for x, z, u in COLS:
        a, b = proj(p, (x, 0.3, z)), proj(p, (x, 3.5, z)); r += [(a[0] - b[0]) * 0.5]
    for uv in KERB:   # the far (B) kerb's top edge: a line in the frame, x 41.30 (nb_street), ~0 over the B lots' grade
        a, b = proj(p, (41.3, 0.0, 0.0)), proj(p, (41.3, 0.0, 40.0)); d = (b - a) / np.linalg.norm(b - a)
        r.append(float((np.asarray(uv) - a) @ np.array([-d[1], d[0]])))
    r += [(h[0] - 11.0) / 0.3 * 3, (h[3] - 0.6) / 0.2 * 3]   # priors (px-weighted)
    return np.array(r)


def fit():
    best = None
    for cz in (14, 22, 30, 40):
        for cx in (28, 33, 38):
            fwd = np.array([70 - cx, 4 - 1.5, 11.6 - cz]); fwd /= np.linalg.norm(fwd)
            right = np.cross(fwd, [0, 1.0, 0]); right /= np.linalg.norm(right); down = np.cross(fwd, right)
            Rm = np.vstack([right, down, fwd])
            if np.linalg.det(Rm) < 0: Rm[0] = -Rm[0]
            p0 = np.r_[1800, Rot.from_matrix(Rm).as_rotvec(), cx, 1.5, cz, 11.0, 6.0, 4.0, 0.6]
            try:
                s = least_squares(res, p0, bounds=([600, -4, -4, -4, 0, -1, -40, 9, 3, 2, 0.2], [6000, 4, 4, 4, 58, 8, 80, 13, 9, 6, 1.2]))
            except ValueError:
                continue
            if best is None or s.cost < best.cost: best = s
    return best


def main():
    s = fit(); f, R, C, h = unpack(s.x); r = res(s.x)
    J = s.jac; cov = np.linalg.pinv(J.T @ J) * (r ** 2).sum() / max(1, len(r) - len(s.x)); sd = np.sqrt(np.diag(cov))
    fwd = R[2]; yaw = float(np.degrees(np.arctan2(fwd[2], fwd[0]))); pitch = float(np.degrees(np.arcsin(-fwd[1])))
    out = {"frame": 11581, "f_px": round(f, 1), "vfov_deg": round(float(np.degrees(2 * np.arctan(529 / f))), 2),
           "camera_spec_xyz": np.round(C, 2).tolist(), "camera_sd_m": np.round(sd[4:7], 2).tolist(),
           "forward_spec": np.round(fwd, 4).tolist(), "up_spec": np.round(-R[1], 4).tolist(), "yaw_deg_from_x": round(yaw, 2), "pitch_deg": round(pitch, 2),
           "fitted": {"ridge_m": round(h[0], 2), "eave_edge_m": round(h[1], 2), "porch_roof_edge_m": round(h[2], 2), "eave_overhang_m": round(h[3], 2)},
           "fitted_sd": {"ridge_m": round(sd[7], 2), "eave_edge_m": round(sd[8], 2), "porch_roof_edge_m": round(sd[9], 2), "eave_overhang_m": round(sd[10], 2)},
           "rms_px": round(float(np.sqrt((r[:12] ** 2).mean())), 2), "residuals_px": {k: np.round(r[2 * i:2 * i + 2], 1).tolist() for i, k in enumerate(PICK)},
           "uncertainty": "picks by eye on 3x crops (+-3 px); heights are over the lot's grade (street kerb unknown, ~0.3 m lower); camera_sd from the fit Jacobian",
           "convention": "spec right-handed, y up; camera looks along forward_spec; image x right, y down, principal point (960, 529)"}
    P = ROOT / "art/home_alone/references/neighborhood/data/film11581_camera.json"; P.parent.mkdir(parents=True, exist_ok=True)
    P.write_text(json.dumps(out, indent=1)); print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
