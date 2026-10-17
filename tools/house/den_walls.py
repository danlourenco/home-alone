"""den_walls: the den (family room) measured on wall planes in Marina's own SfM, for its upgrade (Oct 16: paint, windows, furniture).

Method (copied from kitchen_walls.py): COLMAP of Part 1 den clip (sfm-work/rooms/den, 157/157 frames, gate 5/6 against VGGT;
frame n of the clip is Part 1 ~555 + (n - 1) / 4 s). Each wall, the floor and the ceiling is a RANSAC plane through the 3D points
seen inside hand-picked regions (plain green paint, floor boards, ceiling). Lengths are plane-to-plane, so no corner is picked.
Picked pixels (window glass edges, the mullion, valance, the bookcase, furniture feet) are intersected with their plane, from two
frames where possible (the spread is printed).

Rulers (model units -> metres), two of different kinds, never averaged:
  * 'width':   the built room's width across the house, 3.707 m (overhead-trace:ground, registered on the den clip's own walls)
  * 'ceiling': floor plane to ceiling plane = 8 ft (2.438 m; standard, measured 2.42-2.44 in the living and dining rooms by door
               jambs, tools/house/ground_ceiling.py)
Each ruler is printed measuring the other's quantity. The real-house plan (dimensioned-first-floor.png, own 16.61 px/ft ruler,
FAMILY 12 ft arrow) is the independent check of the room width.

  uv run --with numpy --with scipy --with pillow python -I tools/house/den_walls.py           # cameras, window/bookcase/furniture picks, paint
  ... den_walls.py --paint | --fabric (-> spec/dressing/den_fabric.png) | --drift (why the clip's own 3-D is not used globally)
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from kitchen_walls import load, ransac_plane   # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
M = ROOT / "sfm-work/rooms/den/colmap/sparse/0/txt"
BUILT = {"x0": 2.355, "x1": 9.266, "z0": 16.21, "z1": 19.917}   # spec/house_spec.ground.json den polygon (rear, front, living, end)
CEIL = 2.438

# plain regions (frame, x0, y0, x1, y1). Walls named by the house: front (x max, the desk window), end (z max, the big window),
# living (z min, the arch), rear (x min, the bookcase)
# The painted walls carry no SfM points (flat CG paint), so walls are located by their CORNER LINES, each triangulated from picks in
# several frames (a vertical line: every ray projected on the floor plane must pass through it); the floor is a RANSAC plane through
# the rug and boards. Picks were read on 3x zooms (+-2 px).
FLOOR = [(13, 1300, 900, 1920, 1080), (161, 800, 1000, 1200, 1080)]
CORNERS = {   # name -> [(frame, u, v)], v at the ceiling kink or the baseboard top
    "front_living": [(161, 533, 226), (161, 543, 777), (153, 335, 207), (153, 338, 845), (129, 695, 69), (129, 702, 898)],
    "rear_living":  [(57, 1668, 124), (57, 1682, 806), (69, 1545, 38), (45, 1812, 119), (45, 1814, 160)],
    "rear_end":     [(57, 638, 150), (45, 855, 187)],
}
TOPS = {"front_living": [(161, 533, 226), (153, 335, 207), (129, 695, 69)], "rear_living": [(57, 1668, 124), (69, 1545, 38), (45, 1812, 119)],
        "rear_end": [(57, 638, 150), (45, 855, 187)]}


def frame(n):
    return ROOT / f"sfm-work/rooms/den/colmap/images/shot00/f_{n:05d}.jpg"


def ray(cams, f, cx, cy, fr, u, v):
    cam = cams[fr]; d = cam["R"].T @ np.array([(u - cx) / f, (v - cy) / f, 1.0]); return cam["C"], d / np.linalg.norm(d)


def frame3d(quiet=False):
    """Room frame from Marina's SfM: up from the floor plane, corner lines triangulated, axes along the living wall."""
    pr = (lambda *a, **k: None) if quiet else print
    f, cx, cy, cams, pts = load(M)
    Q = []
    for fr, x0, y0, x1, y1 in FLOOR:
        o = cams[fr]["obs"]; m = (o[:, 0] >= x0) & (o[:, 0] <= x1) & (o[:, 1] >= y0) & (o[:, 1] <= y1)
        Q += [pts[int(i)] for i in o[m, 2] if int(i) in pts]
    up, c0, k, N = ransac_plane(np.array(Q)); pr(f"floor: {k}/{N} points on the plane")
    if up @ (cams[69]["R"].T @ [0, -1, 0]) < 0: up = -up
    e1 = np.cross(up, [1, 0, 0]); e1 /= np.linalg.norm(e1); e2 = np.cross(up, e1)
    to2 = lambda X: np.array([X @ e1, X @ e2])
    corners = {}
    for name, picks in CORNERS.items():
        A, b = [], []
        for fr, u, v in picks:
            o, d = ray(cams, f, cx, cy, fr, u, v); o2, d2 = to2(o), to2(d); n2 = np.array([-d2[1], d2[0]]) / np.linalg.norm(d2)
            A.append(n2); b.append(n2 @ o2)
        A, b = np.array(A), np.array(b); p = np.linalg.lstsq(A, b, rcond=None)[0]
        corners[name] = (p, np.abs(A @ p - b).max())
    def height(name, fr, u, v):   # height above the floor of the ray's closest approach to the corner line
        o, d = ray(cams, f, cx, cy, fr, u, v); p = corners[name][0]
        dh = d - (d @ up) * up; t = ((p[0] * e1 + p[1] * e2) - o) @ dh / (dh @ dh); X = o + t * d
        return (X - c0) @ up
    return dict(f=f, cx=cx, cy=cy, cams=cams, pts=pts, up=up, c0=c0, e1=e1, e2=e2, to2=to2, corners=corners, height=height)


def drift_report():
    F = frame3d()
    C = {k: v[0] for k, v in F["corners"].items()}
    for k, (p, r) in F["corners"].items(): print(f"corner {k:13s} residual (max ray miss) {r:.4f} units")
    L_living = np.linalg.norm(C["front_living"] - C["rear_living"])
    t = (C["front_living"] - C["rear_living"]) / L_living; nrm = np.array([-t[1], t[0]])
    W_rear = abs((C["rear_end"] - C["rear_living"]) @ nrm)
    ang = np.degrees(np.arccos(abs((C["rear_end"] - C["rear_living"]) @ t) / np.linalg.norm(C["rear_end"] - C["rear_living"])))
    print(f"living wall {L_living:.4f} units; width (rear-end corner to the living wall) {W_rear:.4f}; rear wall vs living wall {ang:.1f} deg")
    hs = {k: [F["height"](k, *q) for q in v] for k, v in TOPS.items()}
    H = np.mean(sum(hs.values(), []))
    print("ceiling heights (units):", {k: np.round(v, 4).tolist() for k, v in hs.items()}, f"mean {H:.4f} spread {np.ptp(sum(hs.values(), [])):.4f}")
    print(f"aspect width/length {W_rear / L_living:.3f}  (built {3.707 / 6.911:.3f}; overhead den aspect 0.53)")
    for rn, k in {"width 3.707": 3.707 / W_rear, "ceiling 8 ft": CEIL / H}.items():
        print(f"ruler {rn:12s}: length {L_living * k:.3f} m  width {W_rear * k:.3f} m  ceiling {H * k:.3f} m")


# ---- per-wall, local (the clip drifts round the room: its rear corners sit 62 deg off square, so only LOCAL geometry is used)
VALANCE = {"front": [(141, 450, 160, 1560, 300), (153, 470, 260, 1320, 360)], "end": [(13, 820, 160, 1810, 270), (9, 840, 200, 1720, 290)]}
PICTURES_END = [(13, 630, 325, 735, 625), (9, 670, 340, 765, 610)]   # the three small prints on the end wall, left of the window


def fit(F, regs):
    o_pts = []
    for fr, x0, y0, x1, y1 in regs:
        o = F["cams"][fr]["obs"]; m = (o[:, 0] >= x0) & (o[:, 0] <= x1) & (o[:, 1] >= y0) & (o[:, 1] <= y1)
        o_pts += [F["pts"][int(i)] for i in o[m, 2] if int(i) in F["pts"]]
    return np.array(o_pts)


def walls_local(quiet=False):
    pr = (lambda *a, **k: None) if quiet else print
    F = frame3d(quiet=True); up = F["up"]
    def vplane(P):   # a vertical plane (normal _|_ up) through points
        n, c, k, N = ransac_plane(P); n = n - (n @ up) * up; return n / np.linalg.norm(n), c, k, N
    out = {}
    for w, regs in VALANCE.items():
        n, c, k, N = vplane(fit(F, regs)); out[w + "_valance"] = (n, c); pr(f"{w} valance: {k}/{N} points")
    Pp = fit(F, PICTURES_END); n, c, k, N = vplane(Pp); out["end_prints"] = (n, c)
    pr(f"end-wall prints: {k}/{N} points; angle to the end valance {np.degrees(np.arccos(abs(n @ out['end_valance'][0]))):.1f} deg")
    pr(f"front valance vs end valance: {np.degrees(np.arccos(abs(out['front_valance'][0] @ out['end_valance'][0]))):.1f} deg (90 expected)")
    return F, out


# ---- cameras: refcam's level-camera model, solved from the built room's corners/lines, but SEEDED inside the den (refcam's global
# search lands on the mirror camera behind the wall when the points are mostly lines). Saved in refcam's format, so
# `refcam.py measure/overlay/view` work on them. Focal fixed at the clip's COLMAP focal (1526 px, SIMPLE_PINHOLE, all 157 frames).
FOCAL = 1526.0
SEEDS = {"den-f9": (9, -90.0, (7.0, 16.6)), "den-f13": (13, -90.0, (7.0, 16.6)), "den-f153": (153, 180.0, (4.0, 18.9)), "den-f161": (161, 180.0, (3.1, 19.0)), "den-f57": (57, 0.0, (7.5, 17.6))}


def solve_cam(name, quiet=False):
    import refcam as rc
    from scipy.optimize import least_squares
    fr, yaw0, (x0, z0) = SEEDS[name]
    P = json.loads((ROOT / f"measurements/cameras/points/{name}.json").read_text())
    pts = [p for p in P if "line" not in p]; lines = [p for p in P if "line" in p]
    X = np.array([rc.xyz_of(p) for p in pts]); U = np.array([p["uv"] for p in pts], float)
    cam = lambda q: dict(cx=960, cy=540, f=FOCAL, yaw=q[0], pos=list(q[1:4]))
    def res(q):
        c = cam(q); r = list((rc.proj(c, X)[0] - U).ravel())
        for p in lines:
            (pa, pb), _ = rc.proj(c, np.array(p["line"], float)); t = pb - pa; n = np.array([-t[1], t[0]]) / np.linalg.norm(t)
            r.append(float((np.array(p["uv"]) - pa) @ n))
        return np.array(r)
    s = least_squares(res, [np.radians(yaw0), x0, rc.G + 1.2, z0]); r = res(s.x); c = cam(s.x)
    per = [float(np.hypot(r[2 * i], r[2 * i + 1])) for i in range(len(pts))] + [abs(float(v)) for v in r[2 * len(pts):]]
    c.update(name=name, frame=str(frame(fr).relative_to(ROOT)), size=[1920, 1080], rms_px=round(float(np.sqrt(np.mean(r ** 2))), 2),
             points=pts + lines, residuals_px=[round(e, 2) for e in per])
    (ROOT / f"measurements/cameras/{name}.json").write_text(json.dumps(c, indent=1))
    if not quiet:
        print(f"{name}: x {c['pos'][0]:.2f} z {c['pos'][2]:.2f} eye {c['pos'][1] - rc.G:.2f} m yaw {np.degrees(c['yaw']):.1f}; rms {c['rms_px']} px; "
              f"worst {max(per):.1f} px ({(pts + lines)[int(np.argmax(per))].get('note')})")
    return c


def on_wall(name, u, v, wall):
    """A pixel on a wall plane of the BUILT den -> (along the wall from its front/living-side end, height)."""
    import refcam as rc
    c = rc.load_cam(name); o, d = rc.ray(c, u, v)
    i, val = {"front": (0, BUILT["x1"]), "end": (2, BUILT["z1"]), "rear": (0, BUILT["x0"]), "living": (2, BUILT["z0"])}[wall]
    X = o + (val - o[i]) / d[i] * d
    along = {"front": X[2] - BUILT["z0"], "end": BUILT["x1"] - X[0], "rear": X[2] - BUILT["z0"], "living": BUILT["x1"] - X[0]}[wall]
    return along, X[1] - rc.G


def hit(name, u, v, plane):
    """Pixel -> spec point on a plane 'x=..', 'z=..' or 'h=..' (height above the ground floor)."""
    import refcam as rc
    c = rc.load_cam(name); o, d = rc.ray(c, u, v); ax, val = plane.split("="); val = float(val)
    i = {"x": 0, "z": 2, "h": 1}[ax]; val = rc.G + val if ax == "h" else val
    X = o + (val - o[i]) / d[i] * d
    return np.array([X[0], X[1] - rc.G, X[2]])   # spec x, height, spec z


# ---- paint: the den is PAINTED, not papered (film 2877, 2868-2886: a flat teal-green with no repeat; Marina's is a flat dark green).
# Colour = albedo ratio of the wall to the white baseboard in the same light, per column just above/below the board's top edge
# (the board's paint assumed albedo 0.85, as the dining room's wainscot). The film shows the den (Kevin's movie night), so the
# film's colour is used (the house rule: the film decides the look where it shows it); Marina's is printed for comparison.
FILM = str(ROOT / "0-homealone/full/homealone-movie-screencaps.com-{}.jpg")
PAINT_SRC = {"film": [(2877, 1700, 1910, 940, 1045)], "marina": [(69, 1640, 1900, 900, 1075)]}   # frame, columns, rows searched for the board top


def _lin(c):
    c = c / 255.0; return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def _srgb(l):
    l = np.clip(l, 0, 1); return np.where(l <= 0.0031308, 12.92 * l, 1.055 * l ** (1 / 2.4) - 0.055)


def paint(quiet=False):
    from PIL import Image
    pr = (lambda *a, **k: None) if quiet else print
    out = {}
    for src, items in PAINT_SRC.items():
        R = []
        for n, u0, u1, v0, v1 in items:
            a = np.asarray(Image.open(FILM.format(n) if src == "film" else frame(n)).convert("RGB"), float); L = _lin(a)
            for u in range(u0, u1, 6):
                col = a[v0:v1, u - 2:u + 3].mean(1).sum(1); dv = col[3:] - col[:-3]; j = int(np.argmax(dv)); v = v0 + j + 3
                if dv[j] < 45 or v + 30 >= a.shape[0]: continue
                w = L[v - 45:v - 15, u - 2:u + 3].reshape(-1, 3).mean(0); b = L[v + 8:v + 30, u - 2:u + 3].reshape(-1, 3).mean(0)
                if b.sum() > 0.05: R.append(w / b)
                if not quiet and u % 30 < 6: print(f"   {src} {n} u {u} board top v {v}: wall {np.round(_srgb(w) * 255)} board {np.round(_srgb(b) * 255)}")
        R = np.array(R); r = np.median(R, 0); alb = 0.85 * r
        out[src] = dict(n=len(R), ratio=r, iqr=np.percentile(R, 75, 0) - np.percentile(R, 25, 0), albedo=alb, srgb=_srgb(alb))
        pr(f"{src:6s} {len(R)} columns: wall/board ratio {r.round(3)} (IQR {out[src]['iqr'].round(3)}) -> linear albedo {alb.round(3)}"
           f" -> sRGB {np.round(_srgb(alb), 3)} ({np.round(_srgb(alb) * 255).astype(int)})")
    return out


# ---- the drapery fabric (valance and drapes): Marina's floral (cream ground, red roses, green leaves). The film never shows the den's
# windows from inside, so Marina is the only source. One repeat cut from the end-wall valance in clip frame 13 (near frontal):
# the pattern repeats once per box pleat; the pleat pitch is read by autocorrelation along the valance; the valance's own height
# (1.855-2.249 m on the front wall, den-f153) is the ruler for the cut's height.
def fabric():
    from PIL import Image
    from scipy.ndimage import gaussian_filter
    a = np.asarray(Image.open(frame(13)).convert("RGB"), float)
    band = a[175:265, 840:1800, 0] - a[175:265, 840:1800, 1]               # red minus green: the roses
    p = band.mean(0); p -= p.mean(); ac = np.correlate(p, p, "full")[len(p) - 1:]; ac /= ac[0]
    per = 80 + int(np.argmax(ac[80:200]))
    print(f"valance pattern period {per} px (autocorrelation {ac[per]:.2f})")
    V0, V1 = 162, 278                                                      # valance top/bottom rows at the cut (frame 13)
    x0 = 1058; tile = a[V0:V1, x0:x0 + per].copy()                       # starts just past a pleat line (1055): the fold falls on the wrap
    lum = tile.mean(2); bg = gaussian_filter(lum, 25, mode="wrap")
    tile = tile / np.maximum(bg, 1)[..., None] * np.median(lum)
    for ax in (0, 1):   # blend the edges 5 px so the cut wraps (one pleat across, the valance's height down)
        e = 5; t = np.moveaxis(tile, ax, 0); w = np.linspace(0, 1, e)[:, None, None]
        t[:e] = t[:e] * w + t[-e:] * (1 - w); tile = np.moveaxis(t, 0, ax)
    out = ROOT / "spec/dressing/den_fabric.png"
    Image.fromarray(np.clip(tile, 0, 255).astype(np.uint8)).resize((256, round(256 * (V1 - V0) / per)), Image.LANCZOS).save(out)
    h_m = 0.394 * (V1 - V0) / 116.0                                          # the valance (0.394 m) spans rows 162-278 here
    rep = [round(h_m * per / (V1 - V0), 3), round(h_m, 3)]
    out.with_suffix(".json").write_text(json.dumps({"source": f"Marina, den clip frame 13 (Part 1 ~558 s), end-wall valance x {x0}-{x0 + per}, rows {V0}-{V1}",
                                                    "repeat_m": rep}) + "\n")
    print(out, rep)


# ---- the measurements behind spec/dressing/den.json and measurements/windows/ground.json (den), re-runnable: pixel picks read on 3x
# zooms of the clip frames, intersected with planes of the built den through the solved cameras
WALL_PICKS = [   # camera, label, u, v, wall
    ("den-f9", "end: unit 1 glass left", 909, 500, "end"), ("den-f9", "end: unit 1 glass right", 1053, 500, "end"),
    ("den-f9", "end: unit 2 glass left", 1105, 500, "end"), ("den-f9", "end: unit 2 glass right", 1250, 500, "end"),
    ("den-f9", "end: unit 3 glass left", 1300, 500, "end"), ("den-f9", "end: unit 3 glass right", 1445, 500, "end"),
    ("den-f9", "end: unit 4 glass left", 1500, 500, "end"), ("den-f9", "end: unit 4 glass right", 1645, 500, "end"),
    ("den-f9", "end: glass top under the valance", 1170, 305, "end"), ("den-f9", "end: upper muntin", 1170, 365, "end"),
    ("den-f9", "end: meeting rail", 1170, 470, "end"), ("den-f9", "end: lower muntin", 1170, 575, "end"), ("den-f9", "end: glass bottom", 1170, 685, "end"),
    ("den-f153", "front: unit 1 glass left", 562, 600, "front"), ("den-f153", "front: unit 1 glass right", 695, 600, "front"),
    ("den-f153", "front: unit 2 glass left", 747, 600, "front"), ("den-f153", "front: unit 2 glass right", 885, 600, "front"),
    ("den-f153", "front: unit 3 glass left", 937, 600, "front"), ("den-f153", "front: unit 3 glass right", 1075, 600, "front"),
    ("den-f153", "front: unit 4 glass left", 1127, 600, "front"), ("den-f153", "front: unit 4 glass right", 1267, 600, "front"),
    ("den-f153", "front: upper muntin", 1000, 425, "front"), ("den-f153", "front: meeting rail", 1000, 530, "front"),
    ("den-f153", "front: lower muntin", 1000, 632, "front"), ("den-f153", "front: glass bottom", 1000, 732, "front"),
]
PLANE_PICKS = [   # camera, label, u, v, plane
    ("den-f9", "end valance top-left", 830, 195, "z=19.767"), ("den-f9", "end valance top-right", 1737, 185, "z=19.767"),
    ("den-f9", "end valance bottom", 900, 304, "z=19.767"), ("den-f9", "end drape hem", 848, 837, "z=19.767"), ("den-f9", "end tie-back", 1700, 615, "z=19.767"),
    ("den-f153", "front valance top-left", 463, 260, "x=9.116"), ("den-f153", "front valance top-right", 1332, 253, "x=9.116"),
    ("den-f153", "front valance bottom", 480, 368, "x=9.116"), ("den-f153", "front drape inner @1m", 557, 600, "x=9.116"),
    ("den-f153", "front drape hem", 510, 885, "x=9.116"), ("den-f153", "front tie-back", 487, 690, "x=9.116"),
    ("den-f57", "bookcase top", 950, 207, "x=2.77"), ("den-f57", "bookcase top band bottom", 950, 238, "x=2.77"),
    ("den-f57", "divider A (end side) z", 940, 500, "x=2.77"), ("den-f57", "divider B (living side) z", 1304, 500, "x=2.77"),
    ("den-f57", "lower divider", 1120, 700, "x=2.77"), ("den-f57", "shelf top 1", 800, 355, "x=2.77"), ("den-f57", "shelf top 2", 800, 475, "x=2.77"),
    ("den-f57", "shelf top 3", 800, 595, "x=2.77"), ("den-f57", "shelf top 4", 800, 697, "x=2.77"), ("den-f57", "bottom shelf top", 800, 780, "x=2.77"),
    ("den-f57", "TV left", 1092, 420, "x=2.77"), ("den-f57", "TV right", 1290, 420, "x=2.77"), ("den-f57", "TV bottom", 1180, 592, "x=2.77"),
    ("den-f57", "bookcase front at floor (depth read)", 950, 815, "h=0"), ("den-f57", "bookcase front at floor (depth read)", 1300, 825, "h=0"),
    ("den-f57", "sofa rear end (front of its arm)", 650, 900, "z=19.3"),
    ("den-f9", "sofa front-left end", 1392, 850, "h=0.08"), ("den-f9", "sofa front", 1500, 850, "h=0.08"), ("den-f9", "floor lamp foot", 1200, 861, "h=0"),
    ("den-f9", "coffee table foot", 1778, 1022, "h=0"), ("den-f153", "desk leg near L", 895, 986, "h=0"), ("den-f153", "desk leg near R", 1105, 991, "h=0"),
    ("den-f153", "desk leg far L", 927, 918, "h=0"), ("den-f153", "desk leg far R", 1100, 941, "h=0"), ("den-f153", "wall chair legs", 418, 891, "h=0"),
]


def report():
    for n in SEEDS:
        if (ROOT / f"measurements/cameras/points/{n}.json").exists():
            solve_cam(n)
    print("\nwall picks (along: front wall from the living corner, end wall from the front corner; height above the floor)")
    for cam, lab, u, v, wall in WALL_PICKS:
        a, h = on_wall(cam, u, v, wall); print(f"  {cam:9s} {lab:34s} along {a:6.3f}  h {h:6.3f}")
    print("\nplane picks (spec x, height, z)")
    for cam, lab, u, v, pl in PLANE_PICKS:
        x, h, z = hit(cam, u, v, pl); print(f"  {cam:9s} {lab:38s} x {x:6.3f}  h {h:6.3f}  z {z:6.3f}   [{pl}]")
    paint()

if __name__ == "__main__":
    {"--fabric": fabric, "--paint": paint, "--drift": drift_report}.get(next((a for a in sys.argv[1:] if a.startswith("--")), "--report"), lambda: report())()
