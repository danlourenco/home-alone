"""parents_fireplace_measure: the parents' bedroom fireplace sizes from Marina's Part 2 tour (Oct 18 2026, TRIAL;
changes/2026-10-18-parents-fireplace.json).

Claim (marina-frame:195, ruler door-80in): frame 195.25 s looks at the hall wall at ~18 deg: the hall door (closed), the fireplace and
the bath-side corner all in view. A calibrated camera (f = 1428 px, Marina's solved foyer cameras; principal point at the centre) is
solved by least squares from the door leaf's four corners (height 80 in = 2.032 m; the leaf's width left FREE), two floor-line points
and three crown-line points on the same wall plane. Every fireplace pick is then back-projected onto a plane parallel to the wall at
its depth (stock depths, ASSUMED: case face 0.11, slate face 0.09, shelf front 0.20; the hearth's top and back edge measured).

Check (marina-frame:200, ruler switch-plate): frame 200 s, a close oblique view of the mantel beside the light switch. A stock single
toggle plate is 2.75 x 4.5 in (0.0699 x 0.1143 m): its corners and two horizontal mantel lines solve a second camera with its focal
length FREE; the slate surround's width is back-projected at its face. Shares no data, scale or upstream with the claim.

  python3 tools/house/parents_fireplace_measure.py          # print both, the spread, and the placement along the built wall
"""
import json
import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
F, CX, CY = 1428.0, 960.0, 540.0
DOOR_H = 2.032

# ---- frame 195.25 s picks (1920 x 1080; crops spec/captures/picks/parents_fireplace/)
LEAF = {"TL": (259.0, 231.7), "TR": (585.0, 250.0), "BR": (587.0, 984.0), "BL": (266.7, 1016.0)}
FLOOR = [(630.0, 981.7), (766.7, 968.3)]
CROWN = [(620.0, 162.7), (790.0, 175.0), (1335.0, 208.0)]   # the paper's top under the crown; the last is the bath-side corner
CORNER_TOP = (1335.0, 208.0)
CASING_R = (626.7, 984.0)                                   # the door casing's outer right edge at the floor
# fireplace picks: (u, v, depth in front of the wall)
D_CASE, D_SLATE, D_SHELF = 0.11, 0.09, 0.20
PICKS = {
    "shelf_L": (795.0, 578.3, D_SHELF), "shelf_R": (1218.3, 575.0, D_SHELF),
    "case_L": (820.0, 700.0, D_CASE), "case_R": (1204.0, 700.0, D_CASE),
    "case_foot_L": (820.0, 975.0, D_CASE),
    "slate_L": (880.0, 710.0, D_SLATE), "slate_R": (1155.0, 700.7, D_SLATE),
    "frieze_bot": (900.0, 701.7, D_CASE),
    "box_L": (921.7, 751.7, D_SLATE), "box_R": (1115.0, 743.0, D_SLATE),
    "hearth_back_L": (770.0, 957.0, 0.0),
}
HEARTH_FRONT_L = (790.0, 1017.0)


def rot(w):
    th = np.linalg.norm(w)
    if th < 1e-12:
        return np.eye(3)
    k = w / th; K = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + math.sin(th) * K + (1 - math.cos(th)) * K @ K


def project(p, w, c, f=None):
    f = f or F
    """world (s right along the wall, y up, d out of the wall) -> pixel; camera x right, y down, z forward"""
    base = np.array([[1, 0, 0], [0, -1, 0], [0, 0, -1]], float)   # facing the wall
    q = rot(w) @ base @ (np.asarray(p, float) - c)
    return np.array([f * q[0] / q[2] + CX, f * q[1] / q[2] + CY])


def ray_plane(u, v, w, c, d, f=None):
    f = f or F
    base = np.array([[1, 0, 0], [0, -1, 0], [0, 0, -1]], float)
    M = rot(w) @ base
    r = M.T @ np.array([(u - CX) / f, (v - CY) / f, 1.0])
    t = (d - c[2]) / r[2]
    return c + t * r


def solve():
    from scipy.optimize import least_squares
    nf, nc = len(FLOOR), len(CROWN)

    def unpack(x):
        return x[0:3], x[3:6], x[6], x[7], x[8:8 + nf], x[8 + nf:8 + nf + nc]

    def res(x):
        w, c, W, Hc, sf, sc = unpack(x)
        r = []
        for k, (s, y) in {"TL": (0, DOOR_H), "TR": (W, DOOR_H), "BR": (W, 0), "BL": (0, 0)}.items():
            r += list(project((s, y, 0), w, c) - LEAF[k])
        for i, uv in enumerate(FLOOR):
            r += list(project((sf[i], 0, 0), w, c) - uv)
        for i, uv in enumerate(CROWN):
            r += list(project((sc[i], Hc, 0), w, c) - uv)
        return np.array(r)
    x0 = np.concatenate([[0, 0.3, 0], [1.5, 1.4, 3.5], [0.8, 2.35], [0.9, 1.3], [0.9, 1.3, 2.8]])
    sol = least_squares(res, x0)
    return unpack(sol.x), float(np.sqrt(np.mean(sol.fun ** 2)))


def claim():
    (w, c, W, Hc, sf, sc), rms = solve()
    P = {k: ray_plane(u, v, w, c, d) for k, (u, v, d) in PICKS.items()}
    hb = P["hearth_back_L"]
    # hearth front-left corner: on the hearth's top plane (y = its back edge's height), s = its back corner's s
    base = np.array([[1, 0, 0], [0, -1, 0], [0, 0, -1]], float); M = rot(w) @ base
    r = M.T @ np.array([(HEARTH_FRONT_L[0] - CX) / F, (HEARTH_FRONT_L[1] - CY) / F, 1.0])
    t = (hb[1] - c[1]) / r[1]; hf = c + t * r
    cas = ray_plane(*CASING_R, w, c, 0.0)
    corner = sc[2]
    centre = (P["slate_L"][0] + P["slate_R"][0]) / 2
    out = {
        "camera_rms_px": round(rms, 2), "camera": [round(v, 3) for v in c], "yaw_deg": round(math.degrees(w[1]), 1),
        "leaf_width_free": round(W, 3), "crown_bottom_h": round(Hc, 3),
        "casing_R_to_corner": round(corner - cas[0], 3),
        "shelf_w": round(P["shelf_R"][0] - P["shelf_L"][0], 3), "shelf_top": round((P["shelf_L"][1] + P["shelf_R"][1]) / 2, 3),
        "case_w": round(P["case_R"][0] - P["case_L"][0], 3),
        "slate_w": round(P["slate_R"][0] - P["slate_L"][0], 3), "slate_top": round((P["slate_L"][1] + P["slate_R"][1]) / 2, 3),
        "frieze_bottom": round(P["frieze_bot"][1], 3),
        "box_w": round(P["box_R"][0] - P["box_L"][0], 3), "box_top": round((P["box_L"][1] + P["box_R"][1]) / 2, 3),
        "hearth_h": round(hb[1], 3), "hearth_w": round(2 * (centre - hb[0]), 3), "hearth_depth": round(hf[2], 3),
        "centre_from_casing_R": round(centre - cas[0], 3), "centre_to_corner": round(corner - centre, 3),
        "case_foot": round(P["case_foot_L"][1], 3),
    }
    return out


# ---- frame 200 s (check): a close oblique view of the mantel beside the light switch. A stock single toggle plate is 2.75 x 4.5 in
# (0.0699 x 0.1143 m), flush on the wall: its four corners plus two horizontal lines on the mantel (the slate's top edge, the frieze's
# upper bead: parallel to the wall, so they fix the wall's vanishing direction) solve a second camera, focal length free. The slate's outer width
# is back-projected at the slate face (0.09, as the claim).
PLATE = {"TL": (181.25, 518.75), "TR": (240.5, 518.0), "BR": (241.25, 605.0), "BL": (183.0, 607.0)}   # picks/parents_fireplace/m200_plate.png
PW, PH = 0.0699, 0.1143
LINES_200 = [((678.3, 819.0), (1063.3, 750.0), D_SLATE),      # the slate's top edge (its outer TL and TR corners)
             ((673.0, 766.7), (800.0, 748.0), D_CASE)]        # the frieze's upper bead
SLATE_200 = ((678.3, 819.0), (1063.3, 750.0))


def check():
    """the second camera with its focal length FREE (no upstream): solved at each f from 1000 to 2000 px, the f with the least
    reprojection error kept (the plate's known aspect and the wall's vanishing direction pin it)"""
    from scipy.optimize import least_squares

    def res(x, f):
        w, c, s0, y0 = x[0:3], x[3:6], x[6], x[7]
        r = []
        for k, (ds, dy) in {"TL": (0, PH), "TR": (PW, PH), "BR": (PW, 0), "BL": (0, 0)}.items():
            r += list(project((s0 + ds, y0 + dy, 0), w, c, f) - PLATE[k])
        for i, ((p1, p2, d)) in enumerate(LINES_200):
            Y, sa, sb = x[8 + 3 * i: 11 + 3 * i]
            r += list(project((sa, Y, d), w, c, f) - p1) + list(project((sb, Y, d), w, c, f) - p2)
        return np.array(r)
    x = np.concatenate([[0, 0.3, 0], [0.5, 1.3, 2.0], [0.0, 1.2], [0.75, 0.6, 1.4], [0.8, 0.6, 1.0]])
    best = None
    for f in range(1000, 2001, 10):
        sol = least_squares(res, x, args=(float(f),)); x = sol.x
        rms = float(np.sqrt(np.mean(sol.fun ** 2)))
        if best is None or rms < best[0]:
            best = (rms, f, sol.x.copy())
    rms, f, x = best
    w, c = x[0:3], x[3:6]
    a, b = (ray_plane(u, v, w, c, D_SLATE, float(f)) for (u, v) in SLATE_200)
    return {"camera_rms_px": round(rms, 2), "f_px": f, "camera_rel_plate": [round(float(v), 3) for v in c - [x[6], x[7], 0]],
            "yaw_deg": round(math.degrees(w[1]), 1), "slate_w": round(float(b[0] - a[0]), 3)}


def write(a, b):
    """-> spec/dressing/parents_fireplace.json: the sizes (claim, rounded to the cm) and the placement on the BUILT hall wall"""
    # the built hall wall (spec/geometry.json parents_bedroom): face z 5.3239 from the bath-side corner x 3.21 to the hall door's casing
    # (opening x 5.7773 - 0.07 casing = 5.7073). Marina's casing-to-corner is shorter than ours (claim casing_R_to_corner): the
    # mantel keeps her proportion of that gap (centre at the same fraction from the casing): DEVIATIONS 89
    WALL_Z, CORNER_X, CASING_X = 5.3239, 3.21, 5.7073
    gap = CASING_X - CORNER_X
    xc = CASING_X - gap * a["centre_from_casing_R"] / a["casing_R_to_corner"]
    r2 = lambda v: round(v, 3)
    out = {"note": "The parents' bedroom fireplace (Oct 18 2026, TRIAL; changes/2026-10-18-parents-fireplace.json). Written by "
                   "tools/house/parents_fireplace_measure.py --write from Marina p2 195.25 s (door 80 in ruler; check 200 s at the switch plate). "
                   "Spec metres: x along the hall wall, d = metres out of the wall face (z = wall_z - d), y above the upper floor. "
                   "Read by tools/house/hifi_parents_fireplace.py (ParentsFireplace.glb) and SpecGreybox.ParentsFireplace.cs (colliders).",
           "wall_z": WALL_Z, "centre_x": r2(xc), "built_gap": r2(gap), "marina_gap": a["casing_R_to_corner"],
           "shelf": {"w": round(a["shelf_w"], 2), "top": round(a["shelf_top"], 2), "depth": D_SHELF, "t": 0.035},
           "case": {"w": round(a["case_w"], 2), "depth": D_CASE, "frieze_bottom": round(a["slate_top"], 2)},
           "slate": {"w": round(a["slate_w"], 2), "top": round(a["slate_top"], 2), "face": D_SLATE},
           "firebox": {"w": round(a["box_w"], 2), "top": round(a["box_top"], 2), "back": 0.025},
           "hearth": {"w": round(a["hearth_w"], 2), "depth": round(a["hearth_depth"], 2), "h": round(a["hearth_h"], 3)},
           "painting": {"frame_w": 0.73, "frame_h": 0.63, "bottom": 1.355, "opening": [0.49, 0.39], "art": "spec/dressing/parents_roses.png"},
           "colliders": [{"name": "parents_fireplace", "x": [r2(xc - a["case_w"] / 2), r2(xc + a["case_w"] / 2)], "y": [0.0, round(a["shelf_top"], 2)],
                          "z": [r2(WALL_Z - D_SHELF), WALL_Z]}],
           "measured": {"claim": a, "check": b}}
    (ROOT / "spec/dressing/parents_fireplace.json").write_text(json.dumps(out, indent=1) + "\n")
    print("wrote spec/dressing/parents_fireplace.json; centre x", r2(xc))


if __name__ == "__main__":
    a = claim(); b = check()
    print("claim (frame 195.25, door 80 in, solved camera):", json.dumps(a, indent=1))
    print("check (frame 200, switch plate 4.5 in):", json.dumps(b))
    for k in ("slate_w",):
        print(f"  {k}: claim {a[k]:.3f} check {b[k]:.3f} ({100 * (b[k] / a[k] - 1):+.1f}%)")
    if "--write" in sys.argv:
        write(a, b)



