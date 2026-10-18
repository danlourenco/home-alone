#!/usr/bin/env python3
"""register_glb: register the OLD reference model (ThirdParty/HomeAloneExterior/HomeAloneExterior.glb, unlicensed, prototype
only) to our measured house, so its basement, attic, treehouse and yard can be placed where they belong (user, Oct 18:
"reconcile the best of these separate models into one, cohesive model").

Start frame ("pre"): the GLB as SpecGreybox.Exterior places it today (front-door aligned, no scale):
    glTF (gx, gy, gz) -> IntactHouseReference scene (gx, gy, -gz)            (glTFast x flip + the IntactGLB root's 180 deg)
    pre x = 7.67 - scene z,  pre z = 11.616 - scene x,  pre y (world) = scene y - 4.306
Features are matched pairs, our spec value (read from spec/geometry.json, spec/house_spec.json) <-> the GLB value (measured
from its triangles by the small detectors below inside stated seed boxes, pre frame):
    window/door centres on the front and rear facades  (jamb faces: the outermost frame faces in the seed range, midpoint)
    facade planes (the area-dominant wall plane in a tight slab), main-block end walls (as line constraints)
    the main stair's flight-1 bottom and top nosings (tread clusters)
    floor / ceiling / window sill and head heights per storey (horizontal faces)
Plan fit: 2D similarity spec = s R(yaw) pre + t, linear least squares (point->point and point->line rows), then outliers are
dropped one at a time, worst first, while a residual exceeds DROP_M. Held-out check: fit on the FRONT group (+ stair) only and
report the error on the REAR and END groups; plus leave-one-out over all kept features. Per-storey plan fits are reported too
(our upper floor sits 1.2-1.5 m forward of the ground floor; DEVIATIONS / floor stacking). Vertical: per storey, y = a*y_pre + b
by least squares over floor/ceiling/window heights; the attic floor is held out of the upper fit as its check.

  uv run --with numpy --with matplotlib python -I tools/house/register_glb.py          # fit, write json + plots, report
  uv run --with numpy python -I tools/house/register_glb.py --demo                     # fitter self-check only

Writes spec/glb_registration.json and spec/captures/glb_registration/{ground,upper,basement,attic,site}.png.
"""
import json, math, struct, sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
GLB = ROOT / "unity/HomeAlone/Assets/ThirdParty/HomeAloneExterior/HomeAloneExterior.glb"
DROP_M = 0.60     # plan residual above which a feature is dropped as a mismatch (about a window's half width)
WALL_HALF = 0.07  # our window openings sit on the wall centreline (c); the facade's outer face is c +- 0.07 (0.14 m walls)


# ---------------------------------------------------------------- GLB triangles, pre frame
def load_glb(path=GLB):
    f = open(path, "rb"); f.read(12)
    n, _ = struct.unpack("<II", f.read(8)); g = json.loads(f.read(n))
    bl, _ = struct.unpack("<II", f.read(8)); B = f.read(bl)

    def acc(i):
        a = g["accessors"][i]; bv = g["bufferViews"][a["bufferView"]]; off = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
        if a["type"] == "VEC3":
            st = bv.get("byteStride", 12) // 4
            return np.frombuffer(B, "<f4", count=(a["count"] - 1) * st + 3, offset=off).reshape(-1)[
                np.add.outer(np.arange(a["count"]) * st, np.arange(3))].astype(float)
        return np.frombuffer(B, {5121: "<u1", 5123: "<u2", 5125: "<u4"}[a["componentType"]], count=a["count"], offset=off)

    def q2m(q):
        x, y, z, w = q
        return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                         [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                         [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])

    def local(nd):
        if "matrix" in nd: return np.array(nd["matrix"]).reshape(4, 4).T
        M = np.eye(4); M[:3, :3] = q2m(nd.get("rotation", [0, 0, 0, 1])) @ np.diag(nd.get("scale", [1, 1, 1]))
        M[:3, 3] = nd.get("translation", [0, 0, 0]); return M

    T, L = [], []
    def walk(i, P):
        nd = g["nodes"][i]; M = P @ local(nd)
        if "mesh" in nd:
            for pr in g["meshes"][nd["mesh"]]["primitives"]:
                v = acc(pr["attributes"]["POSITION"]); w = (np.c_[v, np.ones(len(v))] @ M.T)[:, :3]
                ix = acc(pr["indices"]).reshape(-1, 3) if "indices" in pr else np.arange(len(v)).reshape(-1, 3)
                T.append(w[ix]); L.extend([nd.get("name", "")] * len(ix))
        for c in nd.get("children", []): walk(c, M)
    for r in g["scenes"][g.get("scene", 0)]["nodes"]: walk(r, np.eye(4))
    T = np.concatenate(T); L = np.array(L)
    sx, sy, sz = T[..., 0], T[..., 1], -T[..., 2]                       # glTF -> IntactHouseReference scene
    return np.stack([7.67 - sz, sy - 4.306, 11.616 - sx], -1), L        # scene -> pre (spec-like x, world y, spec z)


class Tris:
    def __init__(self, S, L):
        self.S, self.L = S, L; self.c = S.mean(1)
        n = np.cross(S[:, 1] - S[:, 0], S[:, 2] - S[:, 0]); self.a = np.linalg.norm(n, axis=1) / 2
        self.n = n / (2 * self.a[:, None] + 1e-12)

    def box(self, x=(-1e9, 1e9), y=(-1e9, 1e9), z=(-1e9, 1e9)):
        c = self.c
        return (c[:, 0] > x[0]) & (c[:, 0] < x[1]) & (c[:, 1] > y[0]) & (c[:, 1] < y[1]) & (c[:, 2] > z[0]) & (c[:, 2] < z[1])

    def plane(self, axis, slab, y, along):
        """Area-dominant wall plane facing `axis` ('x' or 'z') inside the slab (rounded to 1 cm)."""
        i, j = (0, 2) if axis == "x" else (2, 0)
        m = self.box(**{"xyz"[i]: slab, "y": y, "xyz"[j]: along}) & (np.abs(self.n[:, i]) > 0.95)
        k = np.round(self.c[m, i], 2); u, inv = np.unique(k, return_inverse=True)
        return float(u[np.argmax(np.bincount(inv, self.a[m]))])

    def jambs(self, axis, slab, y, along, amin=0.12):
        """Opening centre along the facade: midpoint of the outermost jamb faces (area >= amin m2 per 1 cm bin)."""
        i, j = (0, 2) if axis == "x" else (2, 0)
        m = self.box(**{"xyz"[i]: slab, "y": y, "xyz"[j]: along}) & (np.abs(self.n[:, j]) > 0.9)
        k = np.round(self.c[m, j], 2); u, inv = np.unique(k, return_inverse=True); w = np.bincount(inv, self.a[m])
        u = u[w >= amin]
        return float((u.min() + u.max()) / 2), float(u.max() - u.min())

    def level(self, x, y, z, up=True):
        """Height of the area-dominant horizontal face (floor if up, ceiling if not) in the box."""
        m = self.box(x, y, z) & ((self.n[:, 1] > 0.98) if up else (self.n[:, 1] < -0.98))
        k = np.round(self.c[m, 1], 2); u, inv = np.unique(k, return_inverse=True)
        return float(u[np.argmax(np.bincount(inv, self.a[m]))])

    def treads(self, x, y, z):
        """Up-facing small treads in the box: list of (y, xmin, xmax, zmin, zmax), one per 1 cm height bin."""
        m = self.box(x, y, z) & (self.n[:, 1] > 0.98)
        out = []
        for yy in np.unique(np.round(self.c[m, 1], 2)):
            P = self.S[m][np.round(self.c[m, 1], 2) == yy].reshape(-1, 3)
            out.append((float(yy), P[:, 0].min(), P[:, 0].max(), P[:, 2].min(), P[:, 2].max()))
        return out

    def bbox(self, m):
        P = self.S[m].reshape(-1, 3); return P.min(0), P.max(0)


# ---------------------------------------------------------------- the fitter
def fit_similarity(rows):
    """rows: dicts with 'p' (pre x,z) and either 'q' (spec x,z: point) or ('n','d': spec line n.q = d), weight 'w'.
    spec = [[a,-b],[b,a]] p + t, linear in (a,b,tx,tz). Returns params and per-row residuals (m)."""
    A, y = [], []
    for r in rows:
        (px, pz), w = r["p"], r.get("w", 1.0)
        rx, rz = [px, -pz, 1, 0], [pz, px, 0, 1]
        if "q" in r:
            A += [np.multiply(rx, w), np.multiply(rz, w)]; y += [w * r["q"][0], w * r["q"][1]]
        else:
            nx, nz = r["n"]; A.append(w * (nx * np.array(rx) + nz * np.array(rz))); y.append(w * r["d"])
    sol = np.linalg.lstsq(np.array(A, float), np.array(y, float), rcond=None)[0]
    return sol, [residual(sol, r) for r in rows]


def apply(sol, p):
    a, b, tx, tz = sol; return np.array([a * p[0] - b * p[1] + tx, b * p[0] + a * p[1] + tz])


def residual(sol, r):
    q = apply(sol, r["p"])
    return float(np.linalg.norm(q - r["q"])) if "q" in r else float(abs(np.dot(r["n"], q) - r["d"]))


def robust(rows, thr=DROP_M):
    keep = list(range(len(rows))); dropped = []
    while True:
        sol, res = fit_similarity([rows[i] for i in keep])
        k = int(np.argmax(res))
        if res[k] <= thr or len(keep) <= 4: return sol, keep, dropped
        dropped.append(keep.pop(k))


def params(sol):
    a, b, tx, tz = sol
    return dict(scale=float(math.hypot(a, b)), yaw_deg=float(math.degrees(math.atan2(b, a))), tx=float(tx), tz=float(tz))


def demo():
    rng = np.random.default_rng(1)
    s, th, t = 0.84, math.radians(1.5), np.array([2.0, -1.0])
    R = s * np.array([[math.cos(th), -math.sin(th)], [math.sin(th), math.cos(th)]])
    P = rng.uniform(-10, 10, (12, 2))
    rows = [dict(p=p, q=R @ p + t + rng.normal(0, 0.02, 2)) for p in P]
    rows.append(dict(p=np.array([3.0, 4.0]), n=(1.0, 0.0), d=float((R @ [3, 4] + t)[0])))   # line constraint
    rows.append(dict(p=np.array([5.0, 5.0]), q=R @ [5, 5] + t + [2.0, 0]))                    # a 2 m outlier
    sol, keep, dropped = robust(rows)
    pp = params(sol)
    assert abs(pp["scale"] - s) < 0.005 and abs(pp["yaw_deg"] - 1.5) < 0.2 and np.allclose([pp["tx"], pp["tz"]], t, atol=0.05), pp
    assert dropped == [len(rows) - 1], dropped
    v, _ = np.polyfit([0, 3], [1, 7], 1); assert abs(v - 2) < 1e-9
    print("demo ok:", {k: round(v, 4) for k, v in pp.items()}, "dropped", dropped)


# ---------------------------------------------------------------- our spec features
def spec_features():
    geo = json.loads((ROOT / "spec/geometry.json").read_text()); hs = json.loads((ROOT / "spec/house_spec.json").read_text())
    W = {}
    for lv in ("ground", "upstairs"):
        for o in geo[lv]["openings"]:
            if o["kind"] == "window": W.setdefault((lv, o["between"][0]), []).append(o)
    def win(lv, room, axis, k, side):
        """k-th window (along the wall) of the room's outer wall on `side` (+1: the max-c wall, -1: the min-c wall)."""
        ws = [o for o in W[(lv, room)] if o["axis"] == axis]; c = (max if side > 0 else min)(o["c"] for o in ws)
        o = sorted([o for o in ws if abs(o["c"] - c) < 0.01], key=lambda o: o["lo"])[k]
        return o["c"] + side * WALL_HALF, (o["lo"] + o["hi"]) / 2, o
    steps = sorted([b for b in hs["stair"]["boxes"] if b["name"].startswith("flight1_step")], key=lambda b: b["name"])
    return geo, hs, win, steps


def build_features(T):
    geo, hs, win, steps = spec_features()
    F = []   # name, group, storey, spec point/line, pre point
    FX = T.plane("x", (10.2, 10.5), (-2, 3), (2, 17))            # GLB front main-block face (outer)
    RU = T.plane("x", (-3.6, -3.3), (2.2, 3.0), (12, 18))         # GLB rear face, upper storey
    RG = T.plane("x", (-3.4, -3.2), (-2.0, -1.0), (12.8, 18))     # GLB rear face, ground storey
    UP, GB = (2.2, 3.0), (-2.0, -1.0)                              # window mid-height bands (pre y)
    def jam(axis, slab, band, rng): return T.jambs(axis, slab, band, rng)[0]
    # front, ground: the door between the vestibule sidelights, dining x2, living x2
    sl = [win("ground", "vestibule", "x", k, +1) for k in (0, 1)]
    F.append(("front_door", "front", "ground", (sl[0][0], (sl[0][1] + sl[1][1]) / 2), (FX, jam("x", (9.8, 10.8), GB, (9.0, 10.45)))))
    for k, rng in ((0, (2.45, 3.75)), (1, (4.75, 5.99))):
        x, z, _ = win("ground", "dining_room", "x", k, +1); F.append((f"front_dining_win{k+1}", "front", "ground", (x, z), (FX, jam("x", (9.8, 10.8), GB, rng))))
    for k, rng in ((0, (13.45, 14.75)), (1, (15.85, 17.0))):
        x, z, _ = win("ground", "living_room", "x", k, +1); F.append((f"front_living_win{k+1}", "front", "ground", (x, z), (FX, jam("x", (9.8, 10.8), GB, rng))))
    # front, upper: Kevin x2, hall bath, Buzz x2 <-> the GLB's five upper bays
    up = [("kevin_jeff_room", 0, (2.5, 3.7)), ("kevin_jeff_room", 1, (4.8, 5.95)), ("hall_bath", 0, (9.2, 10.3)),
          ("buzz_room", 0, (13.55, 14.7)), ("buzz_room", 1, (15.85, 16.95))]
    for room, k, rng in up:
        x, z, _ = win("upstairs", room, "x", k, +1); F.append((f"front_{room}_win{k+1}", "front", "upper", (x, z), (FX, jam("x", (9.8, 10.8), UP, rng))))
    # rear: living x2 (ground), girls B x2 (upper), parents' bath (upper) <-> the GLB's rear bays at the same end
    for k, rng in ((0, (13.0, 14.3)), (1, (16.4, 17.6))):
        x, z, _ = win("ground", "living_room", "x", k, -1); F.append((f"rear_living_win{k+1}", "rear", "ground", (x, z), (RG, jam("x", (-4.5, -3.0), GB, rng))))
    for k, rng in ((0, (13.0, 14.52)), (1, (16.1, 17.6))):
        x, z, _ = win("upstairs", "girls_room_b", "x", k, -1); F.append((f"rear_girls_b_win{k+1}", "rear", "upper", (x, z), (RU, jam("x", (-4.0, -2.5), UP, rng))))
    x, z, _ = win("upstairs", "parents_bath", "x", 0, -1); F.append(("rear_parents_bath_win", "rear", "upper", (x, z), (RU, jam("x", (-4.0, -2.5), UP, (0.8, 2.3)))))
    # ends of the main block (line constraints along z): Buzz's end wall / parents' end wall <-> the GLB main block's corners
    zb = win("upstairs", "buzz_room", "z", 0, +1)[2]["c"] + WALL_HALF
    zp = win("upstairs", "parents_bedroom", "z", 0, -1)[2]["c"] - WALL_HALF
    F.append(("end_buzz_wall", "end", "upper", ("line_z", zb), (FX, T.plane("z", (17.9, 18.3), UP, (9.8, 10.8)))))
    F.append(("end_parents_wall", "end", "upper", ("line_z", zp), (FX, T.plane("z", (1.2, 1.6), UP, (9.8, 10.8)))))
    # main stair, flight 1 (ground): bottom and top nosings at the flight's centreline
    tr = [t for t in T.treads((-0.5, 3.6), (-2.9, 0.0), (10.4, 12.6)) if t[4] - t[3] > 1.5 and t[2] - t[1] < 0.6]
    g_bot, g_top = max(t[2] for t in tr), min(t[1] for t in tr if t[0] < 0.1)
    gz = float(np.median([(t[3] + t[4]) / 2 for t in tr]))
    oz = (steps[0]["z"][0] + steps[0]["z"][1]) / 2
    F.append(("stair_bottom_nosing", "stair", "ground", (steps[0]["x"][1], oz), (g_bot, gz)))
    F.append(("stair_top_nosing", "stair", "ground", (steps[-1]["x"][0], oz), (g_top, gz)))
    # a window's position ALONG its facade and the facade's plane are separate measurements: each window becomes a line row on
    # its along-facade coordinate, and each of our facade walls one line row on its plane (paired with the GLB face plane at
    # that window), so a facade standing forward or back shows as ONE residual instead of spoiling every window on it
    G = []
    faces = {}
    for name, grp, sto, sp, pre in F:
        if grp in ("front", "rear"):
            G.append((name, grp, sto, ("line_z", sp[1]), pre))
            room = name.split("_win")[0].replace("front_", "").replace("rear_", "")
            room = "vestibule" if room == "door" else room
            faces.setdefault((grp, sto, room, round(sp[0], 3)), []).append(pre)
        else: G.append((name, grp, sto, sp, pre))
    for (grp, sto, room, x), pres in faces.items():
        G.append((f"{grp}_face_{sto}_{room}", "face", sto, ("line_x", x), tuple(np.mean(pres, 0))))
    return G, dict(front_face=FX, rear_face_upper=RU, rear_face_ground=RG, stair_treads=len(tr))


def rows_of(F):
    rows = []
    for name, grp, sto, sp, pre in F:
        if sp[0] in ("line_z", "line_x"): rows.append(dict(name=name, p=np.array(pre, float), n=(0.0, 1.0) if sp[0] == "line_z" else (1.0, 0.0), d=float(sp[1])))
        else: rows.append(dict(name=name, p=np.array(pre, float), q=np.array(sp, float)))
    return rows


def vertical(T):
    """Per storey y_spec = a*y_pre + b. Pairs: (name, pre y, spec y)."""
    gf = -3.026
    G = [("floor", T.level((2, 9), (-3.2, -2.8), (2, 17)), gf),
         ("ceiling", T.level((2, 9), (-0.5, 0.5), (2, 17), up=False), gf + 2.438),
         ("front_window_head", T.level((9.85, 10.45), (-1, 0.1), (2.6, 3.6), up=False), gf + 2.03)]
    U = [("floor", T.level((-3, 9.9), (0.6, 1.2), (1, 18)), 0.0),
         ("ceiling", T.level((-3, 9.9), (3.8, 4.15), (1, 18), up=False), 2.4),
         ("front_window_sill", T.level((9.85, 10.45), (1.3, 1.8), (2.7, 3.5)), 0.82),
         ("front_window_head", T.level((9.85, 10.45), (2.9, 3.3), (2.7, 3.5), up=False), 2.2)]
    attic = ("attic_floor", T.level((-3, 10.5), (4.15, 4.4), (1, 18)), 2.62)     # held out: measurements/rooms/attic.json
    out = {}
    for k, P in (("ground", G), ("upper", U)):
        a, b = np.polyfit([p[1] for p in P], [p[2] for p in P], 1)
        out[k] = dict(a=float(a), b=float(b), pairs=[dict(name=n, pre_y=py, spec_y=sy, residual=float(a * py + b - sy)) for n, py, sy in P])
    a, b = out["upper"]["a"], out["upper"]["b"]
    out["upper"]["holdout"] = dict(name=attic[0], pre_y=attic[1], spec_y=attic[2], error=float(a * attic[1] + b - attic[2]))
    out["basement"] = dict(note="no measured basement: mapped with the ground storey's (a, b)", a=out["ground"]["a"], b=out["ground"]["b"])
    out["attic"] = dict(note="mapped with the upper storey's (a, b)", a=a, b=b)
    return out


# ---------------------------------------------------------------- GLB parts to land
def parts(T, V):
    def yb(sto, y): return V[sto]["a"] * y + V[sto]["b"]
    P = {}
    # basement: floor faces at the basement level; inside stair; the outside stairwell (bulkhead) north-west of the kitchen wing
    bf = T.level((-20, 12), (-6.7, -6.3), (-8, 25))
    m = T.box((-20, 12), (bf - 0.05, bf + 0.05), (-8, 25)) & (T.n[:, 1] > 0.98) & (T.a > 0.05)
    P["basement_floor"] = (m, "basement")
    P["basement_stair"] = (T.box((-5.0, -2.5), (-6.5, -3.05), (4.8, 7.2)) & (T.n[:, 1] > 0.98), "basement")
    P["outside_basement_stairwell"] = (T.box((-17.5, -11.0), (-6.6, -3.0), (-3.2, -0.8)) & (T.n[:, 1] > 0.98), "basement")
    af = T.level((-4, 11), (4.15, 4.4), (-5, 24))
    P["attic_floor"] = (T.box((-4, 11.5), (af - 0.05, af + 0.05), (-5, 24)) & (T.n[:, 1] > 0.98), "attic")
    P["attic_stair"] = (T.box((2.5, 6.0), (0.95, 4.2), (14.5, 21.0)) & (T.n[:, 1] > 0.98), "upper")
    # chimneys / dormers: seed boxes read off the GLB roof plan (pre frame, everything above the eaves coloured by height)
    roof = dict(dormer_front_south=((6.3, 10.6), (4.4, 12), (4.3, 6.6)), dormer_front_north=((6.3, 10.6), (4.4, 12), (13.2, 15.6)),
                dormer_rear=((-3.8, -0.3), (4.4, 12), (8.5, 11.0)), chimney_rear=((-4.3, -2.7), (6.5, 12), (14.7, 16.5)),
                ridge_stack_south=((3.3, 4.8), (8.0, 12), (1.5, 2.6)), ridge_stack_north=((3.3, 4.8), (8.0, 12), (15.6, 16.9)))
    for k, (x, y, z) in roof.items(): P[k] = (T.box(x, y, z) & (np.abs(T.n[:, 1]) < 0.3), "attic")   # walls/cheeks only, not roof planes
    P["treehouse"] = (T.L == "object183", "upper")
    out = {}
    for name, (m, sto) in P.items():
        if not m.any(): continue
        lo, hi = T.bbox(m)
        out[name] = dict(pre=dict(x=[float(lo[0]), float(hi[0])], z=[float(lo[2]), float(hi[2])], y=[float(lo[1]), float(hi[1])]),
                         storey_map=sto, mask=m)
    return out


def land(sol, V, info):
    a, b, tx, tz = sol
    lo, hi = info["pre"], None
    C = np.array([[x, z] for x in lo["x"] for z in lo["z"]]); Q = np.array([apply(sol, c) for c in C])
    v = V[info["storey_map"]]; ys = [v["a"] * y + v["b"] for y in lo["y"]]
    return dict(x=[round(float(Q[:, 0].min()), 2), round(float(Q[:, 0].max()), 2)], z=[round(float(Q[:, 1].min()), 2), round(float(Q[:, 1].max()), 2)],
                y=[round(min(ys), 2), round(max(ys), 2)], centre=[round(float(Q[:, 0].mean()), 2), round(float(Q[:, 1].mean()), 2)])


# ---------------------------------------------------------------- plots
def plots(T, sol, V, P, geo, outdir):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    outdir.mkdir(parents=True, exist_ok=True)
    a, b, tx, tz = sol
    XZ = lambda S: np.stack([a * S[..., 0] - b * S[..., 2] + tx, b * S[..., 0] + a * S[..., 2] + tz], -1)

    def slice_(y, box):
        m = T.box(*box) & (T.S[:, :, 1].min(1) < y) & (T.S[:, :, 1].max(1) > y); segs = []
        for t in T.S[m]:
            p = []
            for i in range(3):
                u, v = t[i], t[(i + 1) % 3]
                if (u[1] - y) * (v[1] - y) < 0: p.append(u + (y - u[1]) / (v[1] - u[1]) * (v - u))
            if len(p) == 2: segs.append(p)
        return np.array(segs).reshape(-1, 2, 3)

    def rooms(ax, lv, col="r"):
        for r in geo[lv]["rooms"]:
            p = np.array(r["poly"] + [r["poly"][0]]); ax.plot(p[:, 0], p[:, 1], col + "-", lw=1.1)
            c = p[:-1].mean(0); ax.text(c[0], c[1], r["name"], color=col, fontsize=6, ha="center")

    def marks(ax, names):
        for n in names:
            if n in P:
                L = P[n]["spec"]; ax.add_patch(plt.Rectangle((L["x"][0], L["z"][0]), L["x"][1] - L["x"][0], L["z"][1] - L["z"][0], fill=False, ec="b", lw=1.8))
                ax.text(L["x"][0], L["z"][0] - 0.2, n, color="b", fontsize=7)

    ours = dict(basement_door=((-1.28, -0.45), (6.25, 6.39)), attic_stair=((5.78, 7.33), (13.66, 16.4)), parents_flue=((4.29, 4.59), (5.17, 5.47)))
    def our_marks(ax, keys):
        for k in keys:
            (x0, x1), (z0, z1) = ours[k]; ax.add_patch(plt.Rectangle((x0, z0), x1 - x0, z1 - z0, color="m", alpha=.5)); ax.text(x1 + 0.1, z0, "OURS " + k, color="m", fontsize=7)

    def fig(name, y, lv, title, mark=(), om=(), box=((-25, 15), (-8, 14), (-10, 30)), lim=((-14, 14), (-8, 26))):
        f, ax = plt.subplots(figsize=(11, 12))
        s = slice_(y, box)
        if len(s):
            Q = XZ(s)
            for q in Q: ax.plot(q[:, 0], q[:, 1], "k-", lw=0.4)
        if lv: rooms(ax, lv)
        marks(ax, mark); our_marks(ax, om)
        ax.set_xlim(*lim[0]); ax.set_ylim(lim[1][1], lim[1][0]); ax.set_aspect("equal"); ax.grid(alpha=.3)
        ax.set_xlabel("spec x (front +x)"); ax.set_ylabel("spec z"); ax.set_title(title, fontsize=9)
        f.savefig(outdir / name, dpi=80, bbox_inches="tight"); plt.close(f); return str((outdir / name).relative_to(ROOT))

    yy = lambda sto, spec_y: (spec_y - V[sto]["b"]) / V[sto]["a"]     # spec height -> pre height to slice at
    paths = [fig("ground.png", yy("ground", -1.8), "ground", "Registered GLB, ground storey section (black) on our ground rooms (red); blue = GLB parts",
                 ["basement_stair"], ["basement_door"]),
             fig("upper.png", yy("upper", 1.2), "upstairs", "Registered GLB, upper storey section (black) on our upper rooms (red); blue = GLB attic stair",
                 ["attic_stair"] + [k for k in P if k.startswith(("chimney", "ridge"))], ["attic_stair", "parents_flue"]),
             fig("basement.png", P and V["basement"] and (P["basement_floor"]["pre"]["y"][0] + 1.0), "ground", "Registered GLB basement section (floor +1 m) on our ground rooms",
                 ["basement_stair", "outside_basement_stairwell", "basement_floor"], ["basement_door"], lim=((-22, 14), (-8, 26))),
             fig("attic.png", P["attic_floor"]["pre"]["y"][0] + 1.0, "upstairs", "Registered GLB attic section (floor +1 m) on our upper rooms; chimneys, dormers, attic stair",
                 ["attic_floor", "attic_stair"] + [k for k in P if k.startswith(("chimney", "dormer", "ridge"))], ["attic_stair", "parents_flue"]),
             fig("site.png", yy("ground", -1.8), "ground", "Registered GLB site: house section + treehouse + outside stairwell",
                 ["treehouse", "outside_basement_stairwell"], [], box=((-40, 15), (-8, 14), (-30, 40)), lim=((-30, 14), (-10, 30)))]
    return paths


# ---------------------------------------------------------------- main
def main():
    if "--demo" in sys.argv: demo(); return
    demo()
    T = Tris(*load_glb())
    F, det = build_features(T)
    rows = rows_of(F)
    grp = {r[0]: (r[1], r[2]) for r in F}
    sol, keep, dropped = robust(rows)
    res_all = [residual(sol, r) for r in rows]
    # held out: fit on front + stair, test rear + end
    front = lambda n: grp[n][0] in ("front", "stair") or n.startswith("front_face")
    tr = [r for r in rows if front(r["name"])]; te = [r for r in rows if not front(r["name"])]
    sh, kh, dh = robust(tr)
    hold = {r["name"]: round(residual(sh, r), 3) for r in te}
    # leave-one-out over kept features
    loo = {}
    for i in keep:
        others = [rows[j] for j in keep if j != i]; s1, _ = fit_similarity(others); loo[rows[i]["name"]] = round(residual(s1, rows[i]), 3)
    # per-storey diagnostics
    per = {}
    for sto in ("ground", "upper"):
        rr = [r for r in rows if grp[r["name"]][1] == sto]
        s2, k2, d2 = robust(rr); per[sto] = dict(**params(s2), dropped=[rr[i]["name"] for i in d2],
                                              rms=float(np.sqrt(np.mean([residual(s2, rr[i]) ** 2 for i in k2]))))
    V = vertical(T)
    P = parts(T, V)
    for k, info in P.items(): info["spec"] = land(sol, V, info)
    geo = json.loads((ROOT / "spec/geometry.json").read_text()); hs = json.loads((ROOT / "spec/house_spec.json").read_text())
    # independent checks (no feature in the fit): the GLB's attic stair treads and basement stair top vs ours
    def flight(x, y, z, axis):
        tr = [t for t in T.treads(x, y, z) if (t[2] - t[1] if axis == "z" else t[4] - t[3]) > 1.0]
        lo = min(tr, key=lambda t: t[0]); hi = max(tr, key=lambda t: t[0])
        Q = lambda t: [apply(sol, (t[1], t[3])).round(2).tolist(), apply(sol, (t[2], t[4])).round(2).tolist()]
        return dict(bottom_tread=Q(lo), top_tread=Q(hi), risers=len(tr))
    ab = [b for b in hs["attic_stair"]["boxes"] if b["kind"] == "step"]
    checks = dict(
        attic_stair=dict(glb=flight((2.5, 6.0), (0.95, 4.0), (15.0, 20.2), "z"),
                         ours=dict(x=ab[0]["x"], bottom_z=ab[0]["z"][0], top_z=ab[-1]["z"][1], risers=len(ab))),
        basement_stair=dict(glb=flight((-5.1, -2.8), (-6.5, -4.5), (5.2, 6.9), "x"),
                            ours_basement_door=dict(x=[-1.28, -0.45], z=6.32)))
    th = math.atan2(sol[1], sol[0]); S_ = math.hypot(sol[0], sol[1]); bu = -3.026 + 3.0 * S_
    T0 = np.array([7.67, -11.616]); Rw = np.array([[math.cos(th), math.sin(th)], [-math.sin(th), math.cos(th)]])   # Unity yaw +th on (x, z)
    Pxz = S_ * Rw @ T0 + np.array([sol[2], -sol[3]])
    unity = dict(note="SpecGreybox.Exterior: put the GLB-derived renderers (Site, and later basement/attic/treehouse) under one container with this WORLD "
                      "transform instead of the current (7.67, gy-1.31, -11.616), yaw -90, scale 1. Leave WinterNeighborhood (not from the GLB) where it is. "
                      "Uniform scale is justified: the per-storey vertical fits give a = %.3f / %.3f vs plan s = %.3f. y offset puts the GLB ground floor "
                      "(pre -3.00) on ours (-3.026); valid for gy = -2.996 (the pre frame)." % (V["ground"]["a"], V["upper"]["a"], S_),
                 position=[round(float(Pxz[0]), 4), round(S_ * (-2.996 - 1.31) + bu, 4), round(float(Pxz[1]), 4)],
                 euler_y_deg=round(-90 + math.degrees(th), 4), scale=round(S_, 4),
                 lands=dict(glb_ground_floor=-3.026, glb_upper_floor=round(S_ * 0.91 + bu, 3), glb_attic_floor=round(S_ * 4.25 + bu, 3), glb_basement_floor=round(S_ * -6.54 + bu, 3)))
    for L in ((3.0, 2.0, 5.0), (-20.0, 1.0, 14.0)):   # the Unity transform reproduces the plan fit on scene points
        ph = math.radians(unity["euler_y_deg"]); P_ = unity["position"]
        w = np.array([P_[0] + S_ * (L[0] * math.cos(ph) + L[2] * math.sin(ph)), -(P_[2] + S_ * (-L[0] * math.sin(ph) + L[2] * math.cos(ph)))])
        assert np.allclose(w, apply(sol, (7.67 - L[2], 11.616 - L[0])), atol=0.01), (w, L)
    pngs = plots(T, sol, V, P, geo, ROOT / "spec/captures/glb_registration")
    pp = params(sol)
    out = dict(
        what="similarity registration of the OLD reference model (HomeAloneExterior.glb) to our spec frame; tools/house/register_glb.py",
        pre_frame="pre x = 7.67 - scene z, pre z = 11.616 - scene x, pre y = scene y - 4.306 (scene = glTF (gx, gy, -gz)): SpecGreybox.Exterior's placement as of Oct 18",
        plan=dict(**pp, formula="spec_x = s*(cos*px - sin*pz) + tx ; spec_z = s*(sin*px + cos*pz) + tz  (p = pre x,z)", drop_threshold_m=DROP_M,
                  kept=[rows[i]["name"] for i in keep], dropped=[rows[i]["name"] for i in dropped],
                  rms_kept=float(np.sqrt(np.mean([res_all[i] ** 2 for i in keep])))),
        residuals={r["name"]: dict(group=grp[r["name"]][0], storey=grp[r["name"]][1], residual_m=round(res_all[i], 3),
                                   kept=i in keep, spec=(r["q"].round(3).tolist() if "q" in r else f"z={r['d']:.3f} (line)"),
                                   glb_pre=r["p"].round(3).tolist()) for i, r in enumerate(rows)},
        holdout=dict(train="front windows + front faces + stair; test = rear windows, rear faces, end walls", train_fit=params(sh), train_dropped=[tr[i]["name"] for i in dh], test_errors_m=hold,
                     test_rms_m=float(np.sqrt(np.mean([v ** 2 for v in hold.values()]))), leave_one_out_m=loo),
        per_storey_plan=per,
        vertical=V, detectors=det,
        landed={k: dict(glb_pre=v["pre"], spec=v["spec"], storey_map=v["storey_map"]) for k, v in P.items()},
        checks=checks, unity_exterior_transform=unity, plots=pngs)
    (ROOT / "spec/glb_registration.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: out[k] for k in ("plan", "holdout", "per_storey_plan")}, indent=1))
    print("residuals:"); [print(f"  {k:28s} {v['group']:6s} {v['storey']:6s} {v['residual_m']:6.3f} {'' if v['kept'] else 'DROPPED'}") for k, v in out["residuals"].items()]
    print("vertical:", json.dumps({k: {kk: vv for kk, vv in v.items() if kk != 'pairs'} for k, v in V.items()}, indent=None))
    for k, v in V.items():
        for p in v.get("pairs", []): print(f"  {k} {p['name']:18s} pre {p['pre_y']:6.2f} -> {p['spec_y']:6.2f}  res {p['residual']:+.3f}")
    print("landed (spec):"); [print(f"  {k:28s} {v['spec']}") for k, v in out["landed"].items()]
    print("checks:", json.dumps(checks)); print("unity:", json.dumps(unity)); print("plots:", pngs)


if __name__ == "__main__":
    main()
