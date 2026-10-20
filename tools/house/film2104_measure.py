"""film2104_measure: the corner cupboard and the breakfast hutch measured in film 2104 (the user's IMG_4305 is the same shot: 2104-2146
and 2194-2206 are one static camera), Oct 19 (user: "make sure the hutch and the wooden thing in the corner are sized correctly").

Camera: f, rotation and position fitted jointly (least squares) to the island's grout lines (6 in tiles, 0.158 m pitch: the
ruler, film-native) and the frame's long vertical edges (measurements/kitchen/film2104_lines.json). Picks are pixel points in the
frame. Registration into spec: the island's far stool-side corner (683,378) = spec (0.354, 0.914, 0.834); objects at the gallery
wall are then placed by their offset from that wall (the film's wall line reads 0.28 m nearer the island than Marina's spec: DEVIATIONS).

  uv run --with numpy --with scipy python -I tools/house/film2104_measure.py          # prints the fit, the checks and the sizes
"""
import json
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation as Rot

ROOT = Path(__file__).resolve().parents[2]
D = json.loads((ROOT / "measurements/kitchen/film2104_lines.json").read_text())
P, C0, CH = 0.158, np.array([960.0, 529.0]), 0.914
# pixel picks (film 2104; crops: spec/captures/picks/cupboard-2116.jpg, hutch-2104.jpg)
PICK = {
    "cup_right_floor": (392, 563), "cup_right_top": (368, 82), "cup_left_floor": (277, 597), "cup_left_top": (232, 80),
    "cup_corner_floor": (335, 583), "cup_corner_top": (296, 82),                  # side | door-face edge (door left stiles lean with it)
    "cup_sec1": (382, 445), "cup_sec2": (378, 330), "cup_sec3": (374, 200),     # lips between sections on the right edge
    "wall_floor_1": (410, 549), "wall_floor_2": (470, 548), "wall_floor_3": (520, 546),   # gallery wall / floor junction
    "counter_front_far": (228, 345), "counter_front_mid": (222, 362),          # seat counter's front top edge, its far end
    "sconce_L": (592, 122), "sconce_R": (660, 122),                            # gallery sconce backplates (Marina: h 1.66)
    "hutch_L": (1128, 240), "hutch_R": (1395, 240), "hutch_bay1": (1220, 240), "hutch_bay2": (1308, 240),
    "hutch_glazed_bottom": (1260, 172), "hutch_case_bottom": (1260, 195), "hutch_shelf": (1260, 222), "hutch_cubby_bottom": (1260, 262),
}


def fit():
    def hl(c, d): l = np.cross([*c, 1], [c[0] + d[0], c[1] + d[1], 1]); return l
    rv0 = np.zeros(3)
    def unpack(p): return p[0], Rot.from_rotvec(p[1:4]).as_matrix(), p[4:7]
    def proj(p, X):
        f, R, Cw = unpack(p); q = R @ (np.asarray(X) - Cw); return f * q[:2] / q[2] + C0
    def lres(p, pts, X0, X1):
        a, b = proj(p, X0), proj(p, X1); d = (b - a) / np.linalg.norm(b - a); n = np.array([-d[1], d[0]]); return [(np.array(q) - a) @ n for q in pts]
    def res(p):
        r = []
        for i, cx, cy, dx, dy in D["z_lines"].values():
            r += lres(p, [(cx - 60 * dx, cy - 60 * dy), (cx + 60 * dx, cy + 60 * dy)], (-i * P, 0, -0.5), (-i * P, 0, 1.0))
        for j, cx, cy, dx, dy in D["x_lines"].values():
            r += lres(p, [(cx - 150 * dx, cy - 150 * dy), (cx + 150 * dx, cy + 150 * dy)], (-3.0, 0, j * P), (3.0, 0, j * P))
        f, R, Cw = unpack(p); up = R @ np.array([0, 1.0, 0]); vy = f * up[:2] / up[2] + C0
        for x1, y1, x2, y2 in D["verticals"]:
            m = np.array([(x1 + x2) / 2, (y1 + y2) / 2]); dv = (vy - m) / np.linalg.norm(vy - m); s = np.array([x2 - x1, y2 - y1]); L = np.linalg.norm(s); s /= L
            r.append(0.5 * L * (s[0] * dv[1] - s[1] * dv[0]))
        return np.array(r)
    # start: looking down +x with a slight pitch, 1 m over the counter
    R0 = Rot.from_euler("xyz", [0, 0, 0]).as_matrix()
    best = None
    for yaw in (-60, -30, 0, 30, 60):
        for pitch in (10, 20, 30):
            R = np.array([[0, 0, 1.0], [0, -1.0, 0], [1.0, 0, 0]]).T   # placeholder, replaced below
            # camera axes: x right, y down, z forward; world x forward-ish
            fwd = np.array([np.cos(np.radians(yaw)) * np.cos(np.radians(pitch)), -np.sin(np.radians(pitch)), np.sin(np.radians(yaw)) * np.cos(np.radians(pitch))])
            right = np.cross(fwd, [0, 1.0, 0]); right /= np.linalg.norm(right); down = np.cross(fwd, right)
            Rm = np.vstack([right, down, fwd])
            if np.linalg.det(Rm) < 0: Rm[0] = -Rm[0]
            p0 = np.r_[1800, Rot.from_matrix(Rm).as_rotvec(), -4.0, 1.0, -1.0]
            try:
                s = least_squares(res, p0, bounds=([800, -4, -4, -4, -20, 0.2, -10], [4000, 4, 4, 4, 20, 5, 10]))
            except ValueError:
                continue
            if best is None or s.cost < best.cost: best = s
    f, R, Cw = unpack(best.x); rr = res(best.x)
    return f, R, Cw, float(np.sqrt((rr ** 2).mean()))


def main():
    f, R, Cw, rms = fit()
    K = np.array([[f, 0, C0[0]], [0, f, C0[1]], [0, 0, 1]]); Ki = np.linalg.inv(K)
    def ray(p): return R.T @ (Ki @ np.array([p[0], p[1], 1.0]))
    def at_y(p, y): r = ray(p); return Cw + (y - Cw[1]) / r[1] * r          # local: y up from the counter plane
    off = np.array([0.354, CH, 0.834]) - at_y((683, 378), 0.0)
    def floor(k): return at_y(PICK[k], -CH) + off
    def on(k, y): return at_y(PICK[k], y - CH) + off
    def height(base, top):
        B = at_y(PICK[base], -CH); r = ray(PICK[top]); up = np.array([0, 1.0, 0]); w = B - Cw
        b_, c_, d_, e_ = up @ r, r @ r, up @ w, r @ w; return float((b_ * e_ - c_ * d_) / (c_ - b_ * b_))
    def on_x(k, X): r = ray(PICK[k]); return Cw + ((X - off[0]) - Cw[0]) / r[0] * r + off
    cam = Cw + off
    out = {"f_px": round(f, 1), "vfov_deg": round(float(np.degrees(2 * np.arctan(529 / f))), 2), "fit_rms_px": round(rms, 2), "camera_spec": np.round(cam, 3).tolist()}
    wall = [floor(k)[0] for k in ("wall_floor_1", "wall_floor_2", "wall_floor_3")]
    out["gallery_wall_x_film"] = round(float(np.mean(wall)), 3)
    cnt = [floor_k for floor_k in (on("counter_front_far", CH), on("counter_front_mid", CH))]
    out["seat_counter_front_z_film"] = round(float(np.mean([c[2] for c in cnt])), 3); out["seat_counter_end_x_film"] = round(float(cnt[0][0]), 3)
    out["counter_end_from_wall"] = round(out["gallery_wall_x_film"] - out["seat_counter_end_x_film"], 3)
    out["check_sconce_h"] = [round(float(on_x(k, 2.316)[1]), 3) for k in ("sconce_L", "sconce_R")]   # Marina: 1.66
    # the cupboard: a stack of boxes turned 45 deg (door face toward the island, a plain side toward the seat counter)
    cf, cr, cl = floor("cup_corner_floor"), floor("cup_right_floor"), floor("cup_left_floor")
    cup = {"height_right": round(height("cup_right_floor", "cup_right_top"), 3), "height_corner": round(height("cup_corner_floor", "cup_corner_top"), 3),
           "door_face_w": round(float(np.hypot(*(cr - cf)[[0, 2]])), 3), "side_w": round(float(np.hypot(*(cl - cf)[[0, 2]])), 3),
           "door_face_angle_deg": round(float(np.degrees(np.arctan2((cr - cf)[2], (cr - cf)[0]))), 1),
           "section_tops": [round(height("cup_right_floor", k), 3) for k in ("cup_sec1", "cup_sec2", "cup_sec3")],
           "back_corner_film": np.round((cr + cl - cf)[[0, 2]], 3).tolist()}
    cup["back_corner_from_wall"] = round(out["gallery_wall_x_film"] - cup["back_corner_film"][0], 3)
    out["cupboard"] = cup
    hut = {}
    for X in (3.84, 4.12):    # the hutch wall: spec face 4.12; the film's walls read ~0.28 m nearer (gallery wall), so both planes
        z = {k: float(on_x(k, X)[2]) for k in ("hutch_L", "hutch_R", "hutch_bay1", "hutch_bay2")}
        hut[str(X)] = {"width": round(z["hutch_R"] - z["hutch_L"], 3), "bays": [round(z["hutch_bay1"] - z["hutch_L"], 3), round(z["hutch_bay2"] - z["hutch_bay1"], 3), round(z["hutch_R"] - z["hutch_bay2"], 3)],
                       **{k: round(float(on_x(k, X)[1]), 3) for k in ("hutch_glazed_bottom", "hutch_case_bottom", "hutch_shelf", "hutch_cubby_bottom")}}
    out["hutch"] = hut
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
