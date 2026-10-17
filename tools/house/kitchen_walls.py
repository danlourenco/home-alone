"""kitchen_walls: the back-door corner of Marina's kitchen, measured on wall planes in her own SfM (walk note 15:06, Oct 16).

Why: the back door was placed 0.40 m from the sink-wall corner, from wall TOPS in her overhead (tall-wall parallax, the foyer's
trap), and 0.82 m wide. Her close-ups (Part 1 1101-1107 s) and film 6902 show the sink counter running into that corner and
stopping at the door casing, so a 0.6 m counter must fit between them.

Method: COLMAP of Part 1 1088-1112 s (sfm-work/rooms/kitchen-sink, all 96 frames registered). The door wall and the sink wall
are fitted (RANSAC) to the 3D points that project inside hand-picked wallpaper regions; their intersection is the room corner
and gives the vertical. Picked pixels (casing, leaf, counter end, window stool) are intersected with their wall plane, each
from two frames (the spread is printed). Scale: the door leaf = 80 in (door-80in:marina-1101); the leaf's width/height ratio is
scale-free and is compared with film 6902's (0.44).

  uv run --with numpy python -I tools/house/kitchen_walls.py            # the back-door corner (kitchen-sink clip)
  uv run --with numpy python -I tools/house/kitchen_walls.py --wing     # the whole wing (big kitchen clip), see wing()
  uv run --with numpy python -I tools/house/kitchen_walls.py --plan     # the real-house plan: own ruler + registration on our main block
  uv run --with numpy python -I tools/house/kitchen_walls.py --fixtures # cabinets, appliances, seats, island (big clip) + the plan's
"""
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
M = ROOT / "sfm-work/rooms/kitchen-sink/colmap/sparse/1/txt"
LEAF_H = 2.032

# wallpaper regions (frame, x0, y0, x1, y1) on each wall
REGIONS = {"door": [(61, 700, 120, 785, 620), (61, 1205, 470, 1300, 660), (49, 290, 160, 320, 700), (49, 1210, 520, 1530, 690)],
           "seat": [(5, 1130, 560, 1460, 740), (5, 1500, 540, 1880, 600)],
           "sink": [(69, 0, 440, 470, 600), (69, 1270, 440, 1330, 600), (61, 250, 460, 620, 520)]}
# picks: name -> wall, [(frame, u, v), ...] (same physical point in each frame)
PICKS = {
    "casing_out_corner_side_mid": ("door", [(61, 797, 600), (69, 1432, 600)]),
    "leaf_hinge_top": ("door", [(61, 868, 170)]),
    "leaf_hinge_bot": ("door", [(61, 868, 1015)]),
    "leaf_latch_top": ("door", [(61, 1142, 192), (49, 222, 222)]),
    "leaf_latch_bot": ("door", [(61, 1142, 1000)]),
    "counter_end_top": ("door", [(61, 697, 648), (69, 1326, 640)]),
    "stool_top_left": ("sink", [(69, 497, 510)]),
    "stool_top_right": ("sink", [(69, 903, 510)]),
    "casing_out_corner_side_top": ("door", [(61, 800, 140)]),
    "floor_at_casing": ("door", [(61, 797, 1018)]),
    "casing_out_latch_side": ("door", [(49, 281, 450), (61, 1196, 600), (41, 410, 500)]),
    "endwin_stool_left": ("door", [(49, 685, 607), (41, 720, 582)]),
    "endwin_stool_right": ("door", [(49, 1192, 607), (41, 1114, 582)]),
}


def q2R(w, x, y, z):
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def load(M=M):
    f, cx, cy = map(float, [l for l in open(M / "cameras.txt") if not l.startswith("#")][0].split()[4:7])
    cams, lines = {}, [l for l in open(M / "images.txt") if not l.startswith("#")]
    for a, b in zip(lines[::2], lines[1::2]):
        p = a.split(); R = q2R(*map(float, p[1:5])); t = np.array(list(map(float, p[5:8])))
        n = int(p[-1].split("_")[-1][:5])
        obs = np.array(b.split(), float).reshape(-1, 3)
        cams[n] = dict(R=R, t=t, C=-R.T @ t, obs=obs[obs[:, 2] >= 0])
    pts = {}
    for l in open(M / "points3D.txt"):
        if not l.startswith("#"):
            p = l.split(); pts[int(p[0])] = np.array(list(map(float, p[1:4])))
    return f, cx, cy, cams, pts


def ransac_plane(P, it=3000, tol=None, seed=0):
    rng = np.random.default_rng(seed); tol = tol or 0.01 * np.ptp(P, 0).max(); best = None
    for _ in range(it):
        a, b, c = P[rng.choice(len(P), 3, replace=False)]; n = np.cross(b - a, c - a)
        if np.linalg.norm(n) < 1e-9: continue
        n /= np.linalg.norm(n); inl = abs((P - a) @ n) < tol
        if best is None or inl.sum() > best.sum(): best = inl
    Q = P[best]; c = Q.mean(0); n = np.linalg.svd(Q - c)[2][2]
    return n, c, best.sum(), len(P)


def main(quiet=False):
    f, cx, cy, cams, pts = load()
    pr = (lambda *a, **k: None) if quiet else print
    planes = {}
    for wall, regs in REGIONS.items():
        P = []
        for fr, x0, y0, x1, y1 in regs:
            o = cams[fr]["obs"]; m = (o[:, 0] >= x0) & (o[:, 0] <= x1) & (o[:, 1] >= y0) & (o[:, 1] <= y1)
            P += [pts[int(i)] for i in o[m, 2] if int(i) in pts]
        n, c, k, N = ransac_plane(np.array(P)); planes[wall] = (n, c)
        pr(f"{wall} wall: {k}/{N} points on the plane")
    nd, cd = planes["door"]; ns, cs = planes["sink"]
    pr(f"angle between walls: {np.degrees(np.arccos(abs(nd @ ns))):.1f} deg (90 expected)")
    up = np.cross(nd, ns); up /= np.linalg.norm(up)
    if up @ (cams[61]["R"].T @ [0, -1, 0]) < 0: up = -up    # image up
    # a point on the corner line
    A = np.array([nd, ns, up]); corner0 = np.linalg.solve(A, [nd @ cd, ns @ cs, up @ cd])

    def hit(wall, fr, u, v):
        n, c = planes[wall]; cam = cams[fr]
        d = cam["R"].T @ np.array([(u - cx) / f, (v - cy) / f, 1.0]); s = n @ (c - cam["C"]) / (n @ d)
        return cam["C"] + s * d

    X = {}
    for name, (wall, obs) in PICKS.items():
        hs = np.array([hit(wall, *o) for o in obs]); X[name] = hs.mean(0)
        X[name + "_spread"] = np.ptp(hs, 0) if len(hs) > 1 else None
        X[name + "_each"] = hs
    h = lambda p: (p - corner0) @ up                                   # height (model units, from the corner point)
    ad = lambda p: abs((p - corner0) @ np.cross(up, nd))              # distance along the door wall from the corner
    asw = lambda p: abs((p - corner0) @ np.cross(up, ns))             # distance along the sink wall from the corner
    leaf_h = h(X["leaf_hinge_top"]) - h(X["leaf_hinge_bot"])   # hinge side only: the latch foot is hidden (g6)
    k = LEAF_H / leaf_h; floor = h(X["floor_at_casing"])
    leaf_w = (ad(X["leaf_latch_top"]) - ad(X["leaf_hinge_top"]) + ad(X["leaf_latch_bot"]) - ad(X["leaf_hinge_bot"])) / 2
    for name in PICKS:
        sp = X[name + "_spread"]
        pr(f"{name:28s} wall {PICKS[name][0]:4s}  along door wall {ad(X[name]) * k:5.3f}  along sink wall {asw(X[name]) * k:5.3f}"
              f"  height {(h(X[name]) - floor) * k:5.3f}" + (f"  2-frame spread {np.linalg.norm(sp) * k:.3f} m" if sp is not None else ""))
    for name in PICKS:
        if len(PICKS[name][1]) > 1:
            pr(f"  {name}: per frame along door/sink wall", [f"f{o[0]} {ad(p) * k:.3f}/{asw(p) * k:.3f}" for o, p in zip(PICKS[name][1], X[name + "_each"])])
    nt, ct = planes["seat"]
    L = abs((ct - corner0) @ ns)
    pr(f"seat wall vs sink wall: {np.degrees(np.arccos(abs(nt @ ns))):.1f} deg apart; end wall inner length {L * k:.3f} m at the leaf scale")
    pr("end-wall features as a fraction of its length, and at our traced 4.203 m:")
    for name in ("counter_end_top", "casing_out_corner_side_mid", "leaf_hinge_top", "leaf_latch_top", "casing_out_latch_side", "endwin_stool_left", "endwin_stool_right"):
        pr(f"  {name:28s} {ad(X[name]) / L:.3f}  {ad(X[name]) / L * 4.203:.3f} m")
    pr(f"\nleaf {leaf_w * k:.3f} x {LEAF_H} m at 80 in (ratio {leaf_w / leaf_h:.3f}; film 6902: 0.44)")
    pr(f"corner -> casing outer (corner side) {ad(X['casing_out_corner_side_mid']) * k:.3f} m; corner -> leaf {ad(X['leaf_hinge_top']) * k:.3f} m")
    pr(f"counter end on the door wall: {ad(X['counter_end_top']) * k:.3f} m from the corner (counter depth), top {(h(X['counter_end_top']) - floor) * k:.3f} m")
    pr(f"door casing outer: {ad(X['casing_out_corner_side_mid']) * k:.3f}-{ad(X['casing_out_latch_side']) * k:.3f} m from the corner"
          f" (outer width {(ad(X['casing_out_latch_side']) - ad(X['casing_out_corner_side_mid'])) * k:.3f}); head casing top {(h(X['casing_out_corner_side_top']) - floor) * k:.3f} m")
    pr(f"end-wall window stool: {ad(X['endwin_stool_left']) * k:.3f}-{ad(X['endwin_stool_right']) * k:.3f} m from the corner, top {(h(X['endwin_stool_left']) - floor) * k:.3f} m")
    pr(f"sink window stool: {asw(X['stool_top_right']) * k:.3f}-{asw(X['stool_top_left']) * k:.3f} m from the corner, top {(h(X['stool_top_left']) - floor) * k:.3f} m")

    return dict(up=up, floor=X["floor_at_casing"], k=k, nd=nd)

# ---- the whole wing, from the big kitchen clip (Part 1 868-950 s, sfm-work/rooms/kitchen, 299/299 frames registered;
# frame n is at ~867.75 + n/4 s). Every wall is a RANSAC plane through the points seen in wallpaper regions; lengths are
# plane-to-plane distances, so no corner has to be picked. Rulers (all ON the end-wall plane, so the door recess cannot
# bias them, unlike the leaf picks above): the back door's opening between the casing's inner edges (36 in leaf + jambs)
# and its height to the head casing (80 in leaf + head clearance), and the counter top where it meets the wall (36 in).
W_M = ROOT / "sfm-work/rooms/kitchen/colmap/sparse/1/txt"
W_REGIONS = {
    "end":     [(41, 400, 230, 620, 900), (41, 940, 230, 1000, 600), (41, 1000, 220, 1690, 300), (301, 420, 230, 500, 650)],
    "seat":    [(85, 600, 650, 1000, 880), (85, 1100, 490, 1500, 560)],
    "pantry":  [(165, 130, 0, 540, 1000), (165, 1050, 0, 1270, 440), (141, 1010, 150, 1200, 870)],  # kitchen/sunroom wall
    "hutch":   [(229, 500, 0, 560, 1000), (229, 560, 0, 1160, 40), (229, 1365, 150, 1390, 850)],    # kitchen/dining wall
    "stair":   [(261, 300, 60, 690, 480), (229, 1740, 100, 1900, 850)],                              # back-stair/foyer wall
    "floor":   [(301, 420, 700, 880, 1080), (41, 500, 960, 1300, 1080)],
}
W_PICKS = {   # on the end wall, frame 41 (frontal, ~4 m away)
    "open_left_mid": [(41, 656, 600)], "open_right_mid": [(41, 922, 600)],
    "open_head_left": [(41, 657, 345)], "open_head_right": [(41, 917, 352)],
    "counter_back_top": [(41, 1012, 676)],
}
# The sink wall has no clean wallpaper region (cabinets, a soffit over them, the window): it is read as peaks in the histogram of
# ALL points within 2 m of the end wall, 0.95-2.6 m up, by distance from the seat wall (the soffit face and cabinet fronts stand
# proud of the wall; the window recess lies beyond it). The breakfast rear wall has no 3D points at all (frames 255-290 barely
# register), so the sink wall's length is not measured here.


def wing(quiet=False, rulers=None):
    """Plane-to-plane lengths of the wing in model units, then metres at each ruler. Returns the dict of metres per ruler."""
    pr = (lambda *a, **k: None) if quiet else print
    f, cx, cy, cams, pts = load(W_M)
    planes = {}
    for wall, regs in W_REGIONS.items():
        P = []
        for fr, x0, y0, x1, y1 in regs:
            o = cams[fr]["obs"]; m = (o[:, 0] >= x0) & (o[:, 0] <= x1) & (o[:, 1] >= y0) & (o[:, 1] <= y1)
            P += [pts[int(i)] for i in o[m, 2] if int(i) in pts]
        P = np.array(P); n, c, k, N = ransac_plane(P); planes[wall] = (n, c, P)
        pr(f"{wall:7s} {k}/{N} points on the plane")
    ang = lambda a, b: np.degrees(np.arccos(min(1, abs(planes[a][0] @ planes[b][0]))))
    pr("angles: end/seat %.1f  end/pantry %.1f  end/hutch %.1f  seat/stair %.1f  end/floor %.1f" % (
        ang("end", "seat"), ang("end", "pantry"), ang("end", "hutch"), ang("seat", "stair"), ang("end", "floor")))
    def dist(a, b):           # distance between two (near-)parallel planes, along a's normal, with the spread of b's inliers
        n, c, _ = planes[a]; _, cb, Pb = planes[b]
        d = (Pb - c) @ n; d = d[abs(d - np.median(d)) < 0.02 * np.ptp(d) + 0.05 * abs(np.median(d))]
        return abs(np.median(d)), np.percentile(d, 75) - np.percentile(d, 25)
    nf, cf, _ = planes["floor"]
    def hit(wall, fr, u, v):
        n, c, _ = planes[wall]; cam = cams[fr]
        d = cam["R"].T @ np.array([(u - cx) / f, (v - cy) / f, 1.0]); s = n @ (c - cam["C"]) / (n @ d)
        return cam["C"] + s * d
    X = {k: np.mean([hit("end", *o) for o in v], 0) for k, v in W_PICKS.items()}
    h = lambda p: abs((p - cf) @ nf)
    open_w = np.linalg.norm(X["open_right_mid"] - X["open_left_mid"])
    open_h = (h(X["open_head_left"]) + h(X["open_head_right"])) / 2
    cnt = h(X["counter_back_top"])
    # rulers: model units -> metres. 36 x 80 in door: opening = leaf + 2 x 3/4 in jamb + 2 x 3/16 in reveal (0.962 m);
    # head = 80 in + 1/8 in clearance + 5/8 in threshold + 3/16 in reveal (2.056 m). Counter: 36 in (0.914 m).
    rulers = rulers or {"opening-36in": 0.962 / open_w, "opening-80in": 2.056 / open_h, "counter-36in": 0.914 / cnt}
    L = {"end_to_pantry": dist("end", "pantry"),
         "end_to_hutch": dist("end", "hutch"), "seat_to_stair": dist("seat", "stair")}
    ne, ce, _ = planes["end"]; ns, cs, _ = planes["seat"]
    A = np.array(list(pts.values())); de, ds, hh = (A - ce) @ ne, (A - cs) @ ns, (A - cf) @ nf
    de, ds, hh = de * np.sign(np.median(de)), ds * np.sign(np.median(ds)), hh * np.sign(np.median(hh))
    kc = 0.914 / cnt; m = (de * kc < 2.0) & (hh * kc > 0.95) & (hh * kc < 2.6) & (ds * kc > 4.3) & (ds * kc < 5.6)
    H, b = np.histogram(ds[m], bins=np.arange(4.3, 5.6, 0.025) / kc)
    peaks = sorted(((b[i] + b[i + 1]) / 2 for i in np.argsort(H)[::-1][:5]))
    pr("sink-wall side, histogram peaks (model units, counts):", [(round(p_, 3), int(H[np.searchsorted(b, p_) - 1])) for p_ in peaks])
    for i, p_ in enumerate(peaks): L[f"seat_to_sinkpeak{i}"] = (p_, 0.0)
    out = {}
    for rn, k in rulers.items():
        out[rn] = {name: round(v[0] * k, 3) for name, v in L.items()}
        out[rn].update(open_w=round(open_w * k, 3), open_h=round(open_h * k, 3), counter=round(cnt * k, 3))
    pr("\nlengths (model units, median; IQR of the far plane's inliers):")
    for name, (v, iqr) in L.items(): pr(f"  {name:16s} {v:.3f}  iqr {iqr:.3f}")
    pr("\nmetres per ruler (each ruler also shown measuring the other two):")
    for rn, d in out.items(): pr(f"  {rn:13s}", "  ".join(f"{k} {v:.3f}" for k, v in d.items()))
    return out


# ---- the real-house plan (art/home_alone/references/dimensional-baseline/dimensioned-first-floor.png; Eric's visitor
# reconstruction of the film's location house): its own ruler and its registration on our main block (no Marina, no door).
# Wall faces = the room-side black outline of each wall band, read from pixel profiles (rows/columns named in the comments).
RP_ARROWS = [(1107.5, 1305.8, 12), (190, 390, 12), (396, 646, 15), (852, 1101, 15)]   # tip-to-tip px, feet: sunroom, family, living, dining
RP_FACES_U = [(1101, 3.004), (850.5, 7.638), (1307, -0.915), (1106.5, 2.864), (646, 11.57), (395.5, 16.07), (389.5, 16.21), (189, 19.917)]  # column px -> our spec z (dining, sunroom, living, den faces)
RP_FACES_V = [(908.5, 10.13), (908.5, 9.954), (484.5, 2.355), (485, 2.456), (579.5, 4.26)]   # row px -> spec x (front, den/sunroom/dining rear)
RP_WING = {"sink face u": 1039, "seat face u": 1307.5, "door u0": 1094.5, "door u1": 1146.5, "end window u0": 1205.5, "end window u1": 1249.5,
           "end wall v": 60.5, "sink window v0": 125, "sink window v1": 168, "breakfast rear v": 275.5, "sunroom wall (kitchen side) v": 480,
           "dining wall (kitchen side) v": 572.5}


def real_plan(quiet=False):
    pr = (lambda *a, **k: None) if quiet else print
    ft = [(b - a) / n for a, b, n in RP_ARROWS]; pxft = float(np.mean(ft))
    pr(f"real plan: arrows {np.round(ft, 2)} px/ft -> {pxft:.2f} px/ft (own ruler)")
    u, z = np.array(RP_FACES_U).T; bu, au = np.polyfit(u, z, 1)
    v, x = np.array(RP_FACES_V).T; bv, av = np.polyfit(v, x, 1)
    pr(f"registered on our main block: z = {au:.3f} {bu:+.5f} u (resid max {abs(z - au - bu * u).max():.3f}),"
       f" x = {av:.3f} {bv:+.5f} v (resid max {abs(x - av - bv * v).max():.3f})")
    W = RP_WING; zs, zt = au + bu * W["sink face u"], au + bu * W["seat face u"]
    out = {"width_own_ruler": (W["seat face u"] - W["sink face u"]) / pxft * 0.3048, "sink_z": zs, "seat_z": zt, "width_registered": zs - zt,
           "door_z": (au + bu * W["door u1"], au + bu * W["door u0"]), "end_window_z": (au + bu * W["end window u1"], au + bu * W["end window u0"]),
           "end_x": av + bv * W["end wall v"], "sink_window_x": (av + bv * W["sink window v0"], av + bv * W["sink window v1"]),
           "breakfast_rear_x": av + bv * W["breakfast rear v"], "sunroom_wall_x": av + bv * W["sunroom wall (kitchen side) v"],
           "dining_wall_x": av + bv * W["dining wall (kitchen side) v"]}
    for k_, v_ in out.items(): pr(f"  {k_:18s} {np.round(v_, 3)}")
    return out


# ---- the kitchen's fixtures (cabinets, appliances, seats, island), Marina's big clip again. Two ways in:
#  * picks: a pixel intersected with a plane parallel to a wall (its front at a given offset) or to the floor (at a height)
#  * layers: every 3D point by height band, histogrammed along one axis in a strip (base fronts, counter edges, seat backs)
# Results are in her model at the counter ruler (36 in top), then mapped into the BUILT wing per axis: along the seat wall by the
# end-to-pantry-wall length (her 8.0 m -> built 7.508), across by the seat-to-stair-wall length (8.74 -> 8.553). Depths and
# heights of standard parts stay standard (counter 0.641 deep, 36 in high; uppers 54-87 in). DEVIATIONS 47.
FIX_PICKS = [   # name, frame, x, y, plane ("end" | "seat" | "floor"), offset (m from that plane, at the counter ruler)
    ("end run end (counter top at the wall)", 41, 1011, 676, "end", 0.0),
    ("door casing outer, seat side", 41, 952, 600, "end", 0.0),
    ("compactor front, door side", 41, 1060, 710, "end", 0.6), ("compactor front, seat side", 41, 1197, 710, "end", 0.6),
    ("end window stool, door side", 41, 1176, 590, "end", 0.0), ("end window stool, seat side", 41, 1437, 590, "end", 0.0),
    ("end upper A, door side (front)", 41, 1012, 420, "end", 0.33), ("end upper A, window side", 41, 1196, 420, "end", 0.33),
    ("end upper B, window side", 41, 1465, 420, "end", 0.33), ("end upper B, seat side", 41, 1697, 420, "end", 0.33),
    ("end upper bottom", 41, 1100, 535, "end", 0.33), ("end upper top", 41, 1100, 310, "end", 0.33),
    ("seat upper bottom", 85, 1300, 512, "seat", 0.33), ("seat upper top", 85, 1300, 108, "seat", 0.33),
    ("seat window 1 stool, end side", 85, 545, 595, "seat", 0.0), ("seat window 1 stool, far side", 85, 1010, 595, "seat", 0.0),
    ("seat window 1 stool, far side (f101)", 101, 885, 645, "seat", 0.0),
    ("seat window 2 stool, end side", 85, 1525, 560, "seat", 0.0), ("seat window 2 stool, far side", 85, 1815, 560, "seat", 0.0),
    ("seat window 2 stool, end side (f101)", 101, 1280, 620, "seat", 0.0), ("seat window 2 stool, far side (f101)", 101, 1465, 620, "seat", 0.0),
    ("seat window 1 glass top", 85, 610, 232, "seat", 0.0),
    ("tower front: cabinet top", 69, 930, 100, "seat", 0.6), ("tower front: oven top", 69, 930, 300, "seat", 0.6),
    ("tower front: oven bottom", 69, 930, 710, "seat", 0.6),
]
FIX_LAYERS = [  # name, axis histogrammed, (u range), (v range), (h range): peaks or occupied spans in metres (counter ruler)
    ("seat-wall back at seat height (seats)", "u", (-0.1, 8.2), (-0.06, 0.08), (0.3, 0.85)),
    ("seat-run fronts (bases)", "u", (-0.1, 8.2), (0.5, 0.72), (0.1, 0.8)),
    ("tower front (tall)", "u", (-0.1, 8.2), (0.5, 0.72), (1.0, 2.2)),
    ("island long leg faces (bases)", "v", (2.5, 5.0), (1.5, 3.0), (0.1, 0.85)),
    ("island short leg faces (bases)", "u", (4.8, 6.4), (2.7, 3.3), (0.1, 0.85)),
    ("island short leg end (bases)", "v", (5.3, 5.85), (3.0, 3.8), (0.1, 0.85)),
    ("island near end (counter top)", "u", (1.6, 3.0), (1.9, 2.5), (0.86, 0.95)),
    ("island far edge (counter top)", "u", (5.0, 6.4), (2.6, 3.4), (0.86, 0.95)),
    ("island long leg top edges", "v", (2.2, 3.4), (1.4, 3.0), (0.86, 0.95)),
    ("end-run front (bases)", "u", (0.2, 1.2), (1.0, 2.6), (0.1, 0.8)),
    ("seat-wall seat surfaces (heights)", "h", (1.75, 2.65), (0.08, 0.7), (0.0, 1.0)),
]


def _wing_frame():
    f, cx, cy, cams, pts = load(W_M)
    P = np.array(list(pts.values())); pl = {}
    for wall in ("end", "seat", "floor", "pantry", "stair"):
        Q = []
        for fr, x0, y0, x1, y1 in W_REGIONS[wall]:
            o = cams[fr]["obs"]; m = (o[:, 0] >= x0) & (o[:, 0] <= x1) & (o[:, 1] >= y0) & (o[:, 1] <= y1)
            Q += [pts[int(i)] for i in o[m, 2] if int(i) in pts]
        n, c, _, _ = ransac_plane(np.array(Q)); n = n * np.sign(np.median((P - c) @ n)); pl[wall] = (n, c)   # normals point into the room
    return f, cx, cy, cams, P, pl


def fixtures(quiet=False):
    pr = (lambda *a, **k: None) if quiet else print
    f, cx, cy, cams, P, pl = _wing_frame()
    (ne, ce), (ns, cs), (nf, cf) = pl["end"], pl["seat"], pl["floor"]
    K = 0.914 / _counter_units(f, cx, cy, cams, pl)
    uvh = lambda X: ((X - ce) @ ne * K, (X - cs) @ ns * K, (X - cf) @ nf * K)
    L_pantry = abs((pl["pantry"][1] - ce) @ ne) * K; L_stair = abs((pl["stair"][1] - cs) @ ns) * K
    ku, kv = 7.508 / L_pantry, 8.553 / L_stair
    pr(f"counter ruler: end->pantry wall {L_pantry:.3f} m, seat->stair wall {L_stair:.3f} m; into the built wing: along x x{ku:.4f}, along z x{kv:.4f}")
    bx = lambda u: -5.192 + u * ku; bz = lambda v: -0.915 + v * kv
    out = {"ku": ku, "kv": kv, "picks": {}, "layers": {}}
    pr("\npicks (u: from the end wall, v: from the seat wall, h: above the floor; metres at the counter ruler) -> built spec x / z")
    for name, fr, x, y, wall, off in FIX_PICKS:
        n, c = pl[wall]; c = c + n * off / K; cam = cams[fr]
        d = cam["R"].T @ np.array([(x - cx) / f, (y - cy) / f, 1.0]); X = cam["C"] + (n @ (c - cam["C"]) / (n @ d)) * d
        u, v, h = uvh(X); out["picks"][name] = (u, v, h)
        pr(f"  {name:40s} u {u:6.3f} v {v:6.3f} h {h:6.3f}   x {bx(u):7.3f} z {bz(v):7.3f}")
    U, V, H = uvh(P)
    pr("\nlayers (occupied bins, 5 cm; counts >= 4)")
    for name, ax, ur, vr, hr in FIX_LAYERS:
        m = (U > ur[0]) & (U < ur[1]) & (V > vr[0]) & (V < vr[1]) & (H > hr[0]) & (H < hr[1])
        a = {"u": U, "v": V, "h": H}[ax][m]; lo, hi = {"u": ur, "v": vr, "h": hr}[ax]
        Hh, b = np.histogram(a, bins=np.arange(lo, hi + 1e-9, 0.05))
        occ = [round(float(b[i] + 0.025), 3) for i in range(len(Hh)) if Hh[i] >= 4]
        out["layers"][name] = occ
        pr(f"  {name:40s} [{ax}] " + " ".join(f"{q:.2f}" for q in occ))
    return out


def _counter_units(f, cx, cy, cams, pl):
    """The counter top where it meets the end wall (frame 41), in model units above the floor plane."""
    (ne, ce), (nf, cf) = pl["end"], pl["floor"]; cam = cams[41]
    d = cam["R"].T @ np.array([(1012 - cx) / f, (676 - cy) / f, 1.0]); X = cam["C"] + (ne @ (ce - cam["C"]) / (ne @ d)) * d
    return abs((X - cf) @ nf)


# The real-house plan's kitchen fixtures (pixels in dimensioned-first-floor.png, read off a 4x crop): the island (cooktop box and its
# legs) and the sink under the sink window, registered like RP_WING (real_plan()).
RP_FIX = {"island long leg u": (1176, 1209), "island long leg v": (171, 340), "island short leg u": (1140, 1209), "island short leg v": (300, 340),
          "sink on the sink wall v": (130, 165)}


def real_plan_fixtures():
    u, z = np.array(RP_FACES_U).T; bu, au = np.polyfit(u, z, 1)
    v, x = np.array(RP_FACES_V).T; bv, av = np.polyfit(v, x, 1)
    for k_, (a, b) in RP_FIX.items():
        if k_.endswith(" u"): print(f"  {k_:28s} spec z {au + bu * b:6.3f} .. {au + bu * a:6.3f}")
        else: print(f"  {k_:28s} spec x {av + bv * a:6.3f} .. {av + bv * b:6.3f}")


if __name__ == "__main__":
    import sys
    if "--fixtures" in sys.argv:
        fixtures(); print("\nreal-house plan fixtures:"); real_plan_fixtures(); sys.exit()
    real_plan() if "--plan" in sys.argv else wing() if "--wing" in sys.argv else main()


def tile_ruler(frames=((89, 0, 680, 840, 1080), (93, 0, 700, 900, 1080), (81, 0, 700, 800, 1080)), res=0.01, size=3.0):
    """Floor tiles as a second ruler: rectify the floor (plane from COLMAP points in the region) top-down and read the tile
    pitch from the 2-D spectrum. Returns the pitch in model units per frame (the pitch is rotation-free)."""
    from PIL import Image
    f, cx, cy, cams, pts = load(); W = main(quiet=True)
    out = []
    for fr, x0, y0, x1, y1 in frames:
        cam = cams[fr]; o = cam["obs"]; m = (o[:, 0] >= x0) & (o[:, 0] <= x1) & (o[:, 1] >= y0) & (o[:, 1] <= y1)
        n = W["up"]; d = cam["R"].T @ np.array([((x0 + x1) / 2 - cx) / f, ((y0 + y1) / 2 - cy) / f, 1.0])
        c = cam["C"] + (n @ (W["floor"] - cam["C"]) / (n @ d)) * d       # floor point under the region's centre
        e1 = np.cross(n, W["nd"]); e1 /= np.linalg.norm(e1); e2 = np.cross(n, e1)
        im = np.asarray(Image.open(ROOT / f"sfm-work/rooms/kitchen-sink/all/images/f_{fr:05d}.jpg").convert("L"), float)
        g = np.arange(-size / 2, size / 2, res) / W["k"]; U, V = np.meshgrid(g, g)
        X = c + U[..., None] * e1 + V[..., None] * e2
        Xc = (X - cam["C"]) @ cam["R"].T
        u = cx + f * Xc[..., 0] / Xc[..., 2]; v = cy + f * Xc[..., 1] / Xc[..., 2]
        ok = (Xc[..., 2] > 0) & (u >= x0) & (u < x1 - 1) & (v >= y0) & (v < y1 - 1)
        top = np.zeros_like(U); top[ok] = im[v[ok].astype(int), u[ok].astype(int)]
        top[ok] -= top[ok].mean(); top *= ok
        F = np.abs(np.fft.fftshift(np.fft.fft2(top))); fyy, fxx = np.meshgrid(np.arange(F.shape[0]) - F.shape[0] / 2, np.arange(F.shape[1]) - F.shape[1] / 2, indexing='ij')
        per = size / np.maximum(np.hypot(fxx, fyy), 1e-9)                         # period in metres
        F[(per < 0.12) | (per > 0.5)] = 0                                          # tile-sized only (5-20 in)
        per_axis = []
        for ax in (0, 1):                                    # grout lines: autocorrelation of the gradient profile per axis
            gr = np.abs(np.diff(top, axis=ax)) * ok[:-1, :] if ax == 0 else np.abs(np.diff(top, axis=ax)) * ok[:, :-1]
            prof = gr.sum(axis=1 - ax); w = int(0.8 / res) | 1; prof = prof - np.convolve(prof, np.ones(w) / w, "same")   # detrend slower than 0.8 m
            ac = np.correlate(prof, prof, "full")[len(prof) - 1:]; ac /= ac[0]
            lags = np.arange(len(ac)) * res                   # metres
            best = None
            for nmul in (5, 4, 3):                            # the n-th peak near n x the rough pitch, refined
                lo, hi = int(nmul * 0.2 / res), int(nmul * 0.4 / res)
                i = lo + int(np.argmax(ac[lo:hi]))
                rough = lags[i] / nmul
                j = [int(round(m * rough / res)) for m in range(1, nmul + 1)]
                j = [jj - 3 + int(np.argmax(ac[jj - 3:jj + 4])) for jj in j]
                fit = np.polyfit(range(1, nmul + 1), np.array(j) * res, 1)[0]
                best = best or fit
            per_axis.append(round(best, 4))
        fy, fx = np.unravel_index(np.argmax(F), F.shape)
        kx, ky = (fx - F.shape[1] / 2) / (len(g) * res), (fy - F.shape[0] / 2) / (len(g) * res)
        pitch = 1 / np.hypot(kx, ky) / W["k"]   # model units
        # refine: parabolic peak on the radial profile is coarse at 1/size; report the 2nd-harmonic estimate too
        out.append((fr, per_axis, round(ok.mean(), 2)))   # tile pitch along each wall axis, metres at the 80 in door scale
        Image.fromarray(np.clip(top + 128, 0, 255).astype(np.uint8)).save(ROOT / f"sfm-work/backdoor/floor-top-{fr}.png")
    return out
