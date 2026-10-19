"""exterior_shell: the house's outside skin, generated to the film on our measured ground floor (Oct 18 2026, TRIAL;
changes/2026-10-18-exterior-shell.json, DEVIATIONS 97).

User, Oct 18: "Keep ground floor as measured, but it must still look exactly like the iconic home from the exterior." The film's
facade is one flush brick face over both storeys (4382, 6399/6400); our ground front is measured and Marina's upstairs stands 1.1-1.5 m
proud of it (DEVIATIONS 1). Resolution (the Oct 15 split, now drawn): the skin is the film's house on OUR GROUND FOOTPRINT, its upper
storey carried straight up from the ground walls. Upstairs and attic pieces that reach outside the skin are drawn only while the
player is upstairs (HouseSplit), and the skin's upper parts are drawn only while he is not.

Massing (spec x front +, z; world y; ground floor -3.026, upper floor 0):
  main block   x 1.44-10.27  z 2.864-16.21   two storeys, hip roof (film: 5 bays, portico, 2 front dormers, rear dormer, chimney)
  den section  x 2.215-9.406 z 16.21-20.057  two storeys, set back 0.86 m (film 6400: one flush face over the den, 4-unit windows)
  right section x 2.316-9.547 z -1.055-2.864 two storeys, set back 0.72 m (film 4382/9512: 4-unit windows, mirror of the den end)
  kitchen wing, back stair, back hall: one storey, hip / lean-to roofs (film 4575, 6810)
  portico, terraced beds (SpecGreybox.Yard). No sun porch past the right end (user Oct 18: the sunroom is the right section's
  ground storey; changes/2026-10-18-sunroom-fix.json)
Every ground-floor exterior opening of spec/geometry.json is left open in the brick (veneer 0.10 m on the measured outer faces);
the upper storey's windows are the film's (aligned over the ground bays), not Marina's.

Writes sfm-work/exterior/shell.json (faces per part, read by hifi_exterior.py in Blender) and spec/exterior_shell.json (the
skin's solids and part sets, read by SpecGreybox.Shell). Checks (exit 1 on a FAIL):
  - no always-drawn (L) face inside any ground or upstairs room or the attic; no upper (U) face inside a ground room
  - every ground exterior opening has its hole in the veneer (same span and cuts)
  usage: uv run --with numpy --with shapely python -I tools/house/exterior_shell.py
"""
import json
import math
import sys
from pathlib import Path

from shapely.geometry import LineString, Point, Polygon, box as sbox

ROOT = Path(__file__).resolve().parents[2]
G = json.loads((ROOT / "spec/geometry.json").read_text())
HS = json.loads((ROOT / "spec/house_spec.json").read_text())
HG = json.loads((ROOT / "spec/house_spec.ground.json").read_text())
GF = G["ground"]["floor_y"]                 # -3.026
UF = G["upstairs"]["floor_y"]               # 0.0
V = 0.10                                    # brick veneer on the measured outer faces
SPLIT = -0.25                               # always-drawn ground storey (L) below, upper storey (U) above (upper slab -0.2..0)
# the film's upper storey sits LOWER on the ground storey than Marina's (our upper floor 3.026 over the ground): the cameras of 4382 and
# 6399, solved on the facade's window centres with the upper storey's height left free, put its windows 0.358 / 0.334 m lower than
# ours (fit 10.2 / 8.5 px), and with it the eave, ridge and dormers (4382: 0.28 m, 16-24 px). The skin's upper storey is drawn that
# much lower; Marina's rooms keep their height inside (the split).
UPPER_DY = -0.346
EAVE = 2.55 + UPPER_DY                      # main roof: underside of the roof plane at the fascia line; frieze 2.17-2.35 just over the 2.15 heads (film 4382: sashes up to the frieze)
EAVE_S = 2.45 + UPPER_DY                    # end sections: their cornice sits lower than the main block's (film 4382: 0.2-0.4 m)
PITCH = math.radians(40.0)                  # film 4382 (camera solved on 11 window centres): ridge at 264.5 px vs 265 read; 35 deg gave 302
TP = math.tan(PITCH)
OVER = 0.40                                 # eave overhang, main block; sections 0.35
RT = 0.05                                   # roof covering thickness
MAIN = dict(x=(1.44, 10.27), z=(2.864, 16.21))
DEN = dict(x=(2.215, 9.406), z=(16.21, 20.057))
RIGHT = dict(x=(2.316, 9.547), z=(-1.055, 2.864))
FRONT_MAIN = MAIN["x"][1] + V               # one brick plane over dining, vestibule and living (living's wall is 0.176 behind)
GRADE = dict(front=-4.32, rear=-3.39, side=-3.59)
WIN_UP = dict(sill=0.81, head=2.15)         # the upper storey's window band (Buzz, guest, hall bath: 0.81 / 2.15 over the upper floor)
UPW = 0.86                                  # film upper sash width (4382: 70 px window vs 37 px shutters at 12.6 mm/px)

parts = {}


def part(name, mat, layer):
    """layer 'L': always drawn (ground storey, low roofs); 'U': hidden while the player is upstairs (upper storey, main roofs)."""
    key = f"{layer}_{name}"
    if key not in parts:
        parts[key] = dict(mat=mat, layer=layer, faces=[])
    return parts[key]["faces"]


GROUPS = {}            # id(face list) -> group id per face: the faces of one box/prism/wall share a group (hifi_exterior welds and bevels
_GID, _CUR = [0], [None]   # within a group only, so touching boxes stay separate closed parts; realism pass Oct 18)


class group:
    def __enter__(self): _GID[0] += 1; _CUR[0] = _GID[0]
    def __exit__(self, *a): _CUR[0] = None


def face(F, pts, toward):
    if _CUR[0] is None: _GID[0] += 1
    GROUPS.setdefault(id(F), []).append(_CUR[0] if _CUR[0] is not None else _GID[0])
    n = [0.0, 0.0, 0.0]
    for (ax, ay, az), (bx, by, bz) in zip(pts, pts[1:] + pts[:1]):
        n[0] += (ay - by) * (az + bz); n[1] += (az - bz) * (ax + bx); n[2] += (ax - bx) * (ay + by)
    if sum(a * b for a, b in zip(n, toward)) < 0:
        pts = list(reversed(pts))
    F.append([[round(c, 5) for c in p] for p in pts])


def box(F, x0, x1, y0, y1, z0, z1, skip=()):
    with group(): _box(F, x0, x1, y0, y1, z0, z1, skip)


def _box(F, x0, x1, y0, y1, z0, z1, skip=()):
    x0, x1 = sorted((x0, x1)); y0, y1 = sorted((y0, y1)); z0, z1 = sorted((z0, z1))
    q = {"y1": ([(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)], (0, 1, 0)),
         "y0": ([(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)], (0, -1, 0)),
         "x0": ([(x0, y0, z0), (x0, y1, z0), (x0, y1, z1), (x0, y0, z1)], (-1, 0, 0)),
         "x1": ([(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)], (1, 0, 0)),
         "z0": ([(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)], (0, 0, -1)),
         "z1": ([(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], (0, 0, 1))}
    for k, (p, t) in q.items():
        if k not in skip:
            face(F, p, t)


def prism(F, pts, e):
    with group(): _prism(F, pts, e)


def _prism(F, pts, e):
    """Convex planar polygon pts extruded by vector e, faces outward."""
    top = [tuple(a + b for a, b in zip(p, e)) for p in pts]
    c = [sum(p[i] for p in pts + top) / (2 * len(pts)) for i in range(3)]
    def out(q): m = [sum(p[i] for p in q) / len(q) for i in range(3)]; return [m[i] - c[i] for i in range(3)]
    face(F, list(pts), out(pts)); face(F, top, out(top))
    for i in range(len(pts)):
        q = [pts[i], pts[(i + 1) % len(pts)], top[(i + 1) % len(pts)], top[i]]; face(F, q, out(q))


def mound(F, axis, d, s, a0, a1, y, t0, t1, hmax, seed=0, nt=6, step=0.05):
    """Exterior realism (Oct 18): snow sitting on a ledge: a soft rounded mound on the level top at y between t0..t1 out from the
    face d (outward s), along a0..a1; height hmax with noise, tapering to nothing at both ends (no flat caps). 2 mm over the ledge."""
    na = max(2, int((a1 - a0) / step))
    def pt(i, j):
        a = a0 + (a1 - a0) * i / na; u = j / nt
        e = max(0.0, min(1.0, min(a - a0, a1 - a) / 0.08)) ** 0.5
        h = hmax * e * (0.75 + 0.5 * _vnoise(a * 7.0, seed, seed)) * math.sin(math.pi * u) ** 0.6
        return P(axis, a, y + 0.002 + h, d + s * (t0 + (t1 - t0) * u))
    for i in range(na):
        for j in range(nt):
            face(F, [pt(i, j), pt(i + 1, j), pt(i + 1, j + 1), pt(i, j + 1)], (0, 1, 0))


def icicles(F, axis, d, s, a0, a1, y, t, seed=0, every=0.9):
    """A few thin icicles hanging from a gutter's lip (film 4382/10: subtle): clusters at hashed spots, 4-26 cm long."""
    a = a0 + 0.3
    while a < a1 - 0.3:
        r = _vnoise(a * 3.1, seed, seed + 5)
        if r > 0.55:
            for k in range(1 + int(r * 4)):
                ak = a + (k - 1.5) * 0.045; L = 0.04 + 0.22 * _vnoise(ak * 11.0, seed, 9) * r; w = 0.008 + 0.006 * r
                c = P(axis, ak, y, d + s * t); tip = (c[0], y - L, c[2])
                base = [(c[0] - w, y, c[2] - w), (c[0] + w, y, c[2] - w), (c[0] + w, y, c[2] + w), (c[0] - w, y, c[2] + w)]
                for q in range(4):
                    m = [(base[q][i] + base[(q + 1) % 4][i]) / 2 - c[i] for i in range(3)]
                    face(F, [base[q], base[(q + 1) % 4], tip], (m[0], 0, m[2]))
        a += every * (0.6 + 0.8 * _vnoise(a, seed, 2))


# ---------------------------------------------------------------- walls with holes
def P(axis, a, y, d):
    """axis 'x': a wall facing along x (runs along z), d = x; axis 'z': facing along z, d = z."""
    return (d, y, a) if axis == "x" else (a, y, d)


def wall(F, *a, **k):
    with group(): _wall(F, *a, **k)


def _wall(F, axis, c, s, a0, a1, y0, y1, t, holes=(), caps=(True, True), top=True, bottom=False):
    """A vertical slab on the plane d = c (our wall's outer face), t thick toward s (+1/-1). Holes: dicts a0 a1 y0 y1 [rise]
    (rise: elliptical head over y1). Emits the outer face, the reveals, caps and top (the inner face is never seen)."""
    n_out = (s, 0, 0) if axis == "x" else (0, 0, s)
    do = c + s * t
    hs = []
    for h in holes:
        a_0, a_1 = max(h["a0"], a0), min(h["a1"], a1)
        if a_1 - a_0 > 1e-4 and h["y1"] > y0 and h["y0"] < y1:
            hs.append(dict(h, a0=a_0, a1=a_1))
    br = {a0, a1}
    for h in hs:
        br |= {h["a0"], h["a1"]}
        if h.get("rise"):
            for k in range(1, 12):
                br.add(h["a0"] + (h["a1"] - h["a0"]) * k / 12)
    br = sorted(br)

    def htop(h, a):
        r = h.get("rise", 0.0)
        if not r: return h["y1"]
        u = 2 * (a - h["a0"]) / (h["a1"] - h["a0"]) - 1
        return h["y1"] + r * math.sqrt(max(0.0, 1 - u * u))
    for i in range(len(br) - 1):
        aa, ab = br[i], br[i + 1]; am = (aa + ab) / 2
        blk = sorted([h for h in hs if h["a0"] <= am <= h["a1"]], key=lambda h: h["y0"])
        lo_a = lo_b = y0
        for h in blk:
            if h["y0"] > lo_a + 1e-4:
                face(F, [P(axis, aa, lo_a, do), P(axis, ab, lo_b, do), P(axis, ab, max(h["y0"], y0), do), P(axis, aa, max(h["y0"], y0), do)], n_out)
            lo_a, lo_b = min(htop(h, aa), y1), min(htop(h, ab), y1)
        if lo_a < y1 - 1e-4 or lo_b < y1 - 1e-4:
            q = [P(axis, aa, lo_a, do), P(axis, ab, lo_b, do), P(axis, ab, y1, do), P(axis, aa, y1, do)]
            face(F, q, n_out)
    for h in hs:   # reveals through the brick
        ya, yb = max(h["y0"], y0), min(h["y1"], y1)
        for a, sg in ((h["a0"], 1), (h["a1"], -1)):
            face(F, [P(axis, a, ya, c), P(axis, a, ya, do), P(axis, a, min(htop(h, a), y1), do), P(axis, a, min(htop(h, a), y1), c)],
                 (0, 0, sg) if axis == "x" else (sg, 0, 0))
        if h["y0"] > y0 + 1e-4:
            face(F, [P(axis, h["a0"], ya, c), P(axis, h["a1"], ya, c), P(axis, h["a1"], ya, do), P(axis, h["a0"], ya, do)], (0, 1, 0))
        if h["y1"] < y1 - 1e-4:
            pts = sorted(b for b in br if h["a0"] <= b <= h["a1"])
            for aa, ab in zip(pts, pts[1:]):
                ta, tb = htop(h, aa), htop(h, ab)
                if max(ta, tb) >= y1: continue
                face(F, [P(axis, aa, ta, c), P(axis, ab, tb, c), P(axis, ab, tb, do), P(axis, aa, ta, do)], (0, -1, 0))
    al = (lambda a: (0, 0, a)) if axis == "x" else (lambda a: (a, 0, 0))
    if caps[0]: face(F, [P(axis, a0, y0, c), P(axis, a0, y0, do), P(axis, a0, y1, do), P(axis, a0, y1, c)], al(-1))
    if caps[1]: face(F, [P(axis, a1, y0, c), P(axis, a1, y0, do), P(axis, a1, y1, do), P(axis, a1, y1, c)], al(1))
    if top: face(F, [P(axis, a0, y1, c), P(axis, a1, y1, c), P(axis, a1, y1, do), P(axis, a0, y1, do)], (0, 1, 0))
    if bottom: face(F, [P(axis, a0, y0, c), P(axis, a1, y0, c), P(axis, a1, y0, do), P(axis, a0, y0, do)], (0, -1, 0))


# ---------------------------------------------------------------- openings
def ground_openings():
    out = []
    for o in G["ground"]["openings"]:
        if len(o["between"]) == 1 or "outside" in o["between"]:
            for cut in o["cuts"]:
                out.append(dict(axis=o["axis"], c=o["c"], a0=o["lo"], a1=o["hi"], y0=GF + cut[0], y1=GF + cut[1], room=o["between"][0]))
    lw = HG["wall_openings"][0]   # the landing window (arched), ground frame, rear wall of the stair hall
    out.append(dict(axis="x", c=(lw["x"][0] + lw["x"][1]) / 2, a0=lw["z"][0], a1=lw["z"][1], y0=GF + lw["y"][0], y1=GF + lw["y"][1],
                    rise=lw["fan_rise_m"], room="landing"))
    # the front door assembly (hifi_door.py: pilasters z 8.848-10.583, arch apex 2.118 over the 1.93 transom): the vestibule wall is
    # closed behind the door model, so the brick opening shows the exterior door face (below)
    out.append(dict(axis="x", c=10.2, a0=8.848, a1=10.583, y0=GF, y1=GF + 1.93, rise=0.188, room="front_door"))
    return out


OPEN = ground_openings()


def holes_on(axis, c, tol=0.12):
    return [dict(a0=o["a0"], a1=o["a1"], y0=o["y0"], y1=o["y1"], rise=o.get("rise", 0.0)) for o in OPEN if o["axis"] == axis and abs(o["c"] - c) < tol]


# ---------------------------------------------------------------- the upper storey's windows (film), sills and heads over the upper floor
def upper_windows():
    W = []
    ys, yh = UF + UPPER_DY + WIN_UP["sill"], UF + UPPER_DY + WIN_UP["head"]
    for zc in (4.742, 6.702, 9.716, 12.938, 14.643):            # over the ground bays (film 4382: upper sashes over the French windows)
        W.append(dict(face="front", axis="x", d=FRONT_MAIN, a0=zc - UPW / 2, a1=zc + UPW / 2, y0=ys, y1=yh, units=1, shutters=True))
    W.append(dict(face="den_front", axis="x", d=DEN["x"][1] + V, a0=16.994, a1=19.626, y0=ys, y1=yh, units=4))
    W.append(dict(face="den_end", axis="z", d=DEN["z"][1] + V, a0=5.405, a1=8.037, y0=ys, y1=yh, units=4))
    W.append(dict(face="den_rear", axis="x", d=DEN["x"][0] - V, a0=16.992, a1=19.624, y0=ys, y1=yh, units=4))
    W.append(dict(face="right_front", axis="x", d=RIGHT["x"][1] + V, a0=0.905 - 1.316, a1=0.905 + 1.316, y0=ys, y1=yh, units=4))
    W.append(dict(face="right_end", axis="z", d=RIGHT["z"][0] - V, a0=5.85 - 1.316, a1=5.85 + 1.316, y0=ys, y1=yh, units=4))
    for a0, a1, s in ((12.291, 13.011, 0.81), (15.006, 15.726, 0.81), (6.555, 7.276, 0.81), (3.056, 3.656, 0.54)):   # rear: girls_b x2, girls_a, parents bath
        W.append(dict(face="rear", axis="x", d=MAIN["x"][0] - V, a0=a0, a1=a1, y0=UF + UPPER_DY + s, y1=yh, units=1))
    return W


UPW_LIST = upper_windows()
# the right section's ground storey is the sealed sunroom (DEVIATIONS 33): its windows are drawn on the skin only, sheers in the panes
# (film 4382 day, 10 night lit), on the street face and under the upper end window (film 1890); the den's openings mirrored
BLIND = [dict(face="right_front_ground", axis="x", s=1, d=RIGHT["x"][1] + V, a0=0.905 - 1.316, a1=0.905 + 1.316, y0=GF + 0.41, y1=GF + 2.086, units=4),
         dict(face="right_end_ground", axis="z", s=-1, d=RIGHT["z"][0] - V, a0=5.85 - 1.316, a1=5.85 + 1.316, y0=GF + 0.41, y1=GF + 2.086, units=4)]


# ---------------------------------------------------------------- walls
def build_walls():
    B = part("Brick", "EX_Brick", "L")
    BU = part("Brick", "EX_Brick", "U")
    # ground-storey veneer on every exterior face of the ground footprint
    up_holes = lambda axis, d: [dict(a0=w["a0"], a1=w["a1"], y0=w["y0"], y1=w["y1"]) for w in UPW_LIST + BLIND if w["axis"] == axis and abs(w["d"] - d) < 0.01]
    xF, zR0 = MAIN["x"][1], RIGHT["z"][0]
    single_top = -0.30            # the one-storey parts' walls run up under their roofs' soffits
    lean_top = -0.70              # back hall (its ceiling top -0.721) under the lean-to
    two = SPLIT
    # (axis, wall outer face c, outward s, a0, a1, grade, top) -- spec/geometry.json footprint outline, outer faces
    runs = [
        ("z", 4.225, 1, -5.332, -1.645, GRADE["rear"], single_top),       # wing side
        ("x", -1.645, -1, 4.225, 7.778, GRADE["rear"], single_top),       # back stair rear
        ("z", 7.778, 1, -1.645, -0.132, GRADE["rear"], single_top),
        ("x", -0.132, -1, 7.778, 11.57, GRADE["rear"], lean_top),         # back hall rear
        ("z", 11.57, 1, -0.132, 1.44, GRADE["rear"], lean_top),
        ("x", 1.44, -1, 11.57, 16.21, GRADE["rear"], two),                # living rear
        ("z", 16.21, 1, 1.44, 2.215, GRADE["rear"], two),
        ("x", 2.215, -1, 16.21, 20.057, GRADE["rear"], two),              # den rear
        ("z", 20.057, 1, 2.215, 9.406, GRADE["front"], two),              # den end
        ("x", 9.406, 1, 16.21, 20.057, GRADE["front"], two),              # den front
        ("z", 16.21, 1, 9.406, xF, GRADE["front"], two),                  # main end, front return (living padded to the dining plane)
        ("x", xF, 1, 2.864, 16.21, GRADE["front"], two),                  # main front: one plane (living's wall 0.176 behind it, filled)
        ("z", 2.864, -1, 9.547, xF, GRADE["front"], two),                 # main end, front return
        ("x", 9.547, 1, -1.055, 2.864, GRADE["front"], two),              # right section front
        ("z", zR0, -1, 2.316, 9.547, GRADE["side"], two),                 # right section end
        ("z", zR0, -1, -5.332, 2.316, GRADE["side"], single_top),         # kitchen end
        ("x", -5.332, -1, -1.055, 4.225, GRADE["rear"], single_top),      # wing rear
    ]
    for axis, c, s, a0, a1, g0, top in runs:
        tol = 0.2
        hs = [h for h in [dict(a0=o["a0"], a1=o["a1"], y0=o["y0"], y1=o["y1"], rise=o.get("rise", 0.0)) for o in OPEN
                          if o["axis"] == axis and (abs(o["c"] - c) < tol or (axis == "x" and c == xF and o["c"] > 9.9))]]
        hs += up_holes(axis, c + s * V)
        # corners: the run along x owns the corner (its caps reach over the crossing run's veneer)
        ext0 = ext1 = 0.0
        if axis == "z":
            ext0, ext1 = V, V
        aa0, aa1 = (a0 - ext0, a1 + ext1) if s > 0 or axis == "z" else (a0, a1)
        if axis == "x" and c == xF:
            # the living's front wall is 0.176 behind the plane: the gap is filled to the wall (inner face at the living wall)
            wall(B, "x", 10.094, 1, 11.57, 16.21, g0, top, xF + V - 10.094, holes=hs, caps=(False, False), top=False)
            wall(B, "x", xF, 1, 2.864, 11.57, g0, top, V, holes=hs, caps=(False, False), top=False)
            continue
        wall(B, axis, c, s, aa0, aa1, g0, top, V, holes=hs, caps=(False, False), top=False)
    # the veneer's corners: the runs along z were extended by V; the x runs end flush at the outer faces
    # upper storey on the two-storey sections, from SPLIT up into the roof (U)
    yt = EAVE + 0.15
    ups = [
        ("x", FRONT_MAIN - V, 1, 2.864, 16.21, SPLIT),
        ("x", MAIN["x"][0], -1, 2.864, 16.21, SPLIT),
        ("z", 16.21, 1, 9.406, FRONT_MAIN - V, SPLIT), ("z", 16.21, 1, 1.44, 2.215, SPLIT),
        ("z", 2.864, -1, 9.547, FRONT_MAIN - V, SPLIT), ("z", 2.864, -1, 1.44, 2.316, -0.43),
        ("x", DEN["x"][1], 1, 16.21, 20.057, SPLIT), ("x", DEN["x"][0], -1, 16.21, 20.057, SPLIT), ("z", DEN["z"][1], 1, DEN["x"][0], DEN["x"][1], SPLIT),
        ("x", RIGHT["x"][1], 1, -1.055, 2.864, SPLIT), ("x", RIGHT["x"][0], -1, -1.055, 2.864, -0.43), ("z", RIGHT["z"][0], -1, RIGHT["x"][0], RIGHT["x"][1], SPLIT),
    ]
    for axis, c, s, a0, a1, y0 in ups:
        hs = up_holes(axis, c + s * V) + holes_on(axis, c + 0.07 * (-s), 0.2) if axis == "x" and c == MAIN["x"][0] else up_holes(axis, c + s * V)
        ext = V if axis == "z" else 0.0
        if axis == "x" and c == MAIN["x"][0]:   # main rear: down to the back hall's lean-to and the wing roof where they meet it
            wall(BU, "x", c, s, 2.864, 7.778, -0.43, yt, V, holes=hs, caps=(False, False))
            wall(BU, "x", c, s, 7.778, 11.57, -0.70, yt, V, holes=hs, caps=(False, False))
            wall(BU, "x", c, s, 11.57, 16.21, y0, yt, V, holes=hs, caps=(False, False))
            continue
        wall(BU, axis, c, s, a0 - ext, a1 + ext, y0, yt, V, holes=hs, caps=(False, False))


# ---------------------------------------------------------------- roofs
def hip_facets(x0, x1, z0, z1, ye, tp):
    """Hip roof over the rectangle (already including the overhang): its four facets (plan points lifted), ridge on the long axis."""
    def h(x, z): return ye + tp * min(x - x0, x1 - x, z - z0, z1 - z)
    if (x1 - x0) >= (z1 - z0):
        r = (z1 - z0) / 2; zr = z0 + r; xa, xb = x0 + r, x1 - r
        F = [[(x0, z0), (x1, z0), (xb, zr), (xa, zr)], [(x1, z1), (x0, z1), (xa, zr), (xb, zr)],
             [(x0, z1), (x0, z0), (xa, zr)], [(x1, z0), (x1, z1), (xb, zr)]]
    else:
        r = (x1 - x0) / 2; xr = x0 + r; za, zb = z0 + r, z1 - r
        F = [[(x0, z1), (x0, z0), (xr, za), (xr, zb)], [(x1, z0), (x1, z1), (xr, zb), (xr, za)],
             [(x0, z0), (x1, z0), (xr, za)], [(x1, z1), (x0, z1), (xr, zb)]]
    return [[(x, h(x, z), z) for x, z in f] for f in F], h


def roof_from(facets, h, F, keep=None, lift=0.0):
    for f in facets:
        poly = Polygon([(x, z) for x, _, z in f])
        if keep is not None:
            poly = poly.intersection(keep)
            if poly.is_empty: continue
        polys = [poly] if poly.geom_type == "Polygon" else [g for g in getattr(poly, "geoms", []) if g.geom_type == "Polygon"]
        for pg in polys:
            pts = list(pg.exterior.coords)[:-1]
            if len(pts) < 3: continue
            P3 = [(x, h(x, z) + lift + RT, z) for x, z in pts]
            face(F, P3, (0, 1, 0))


ROOFS = []   # for spec/exterior_shell.json: the skin's solids (SpecGreybox.Shell's inside-only test)


def hip_roof(name, rect, over, ye, tp, layer, keep=None, cornice=True, frieze=0.0, cornice_keep=None):
    x0, x1, z0, z1 = rect[0] - over, rect[1] + over, rect[2] - over, rect[3] + over
    facets, h = hip_facets(x0, x1, z0, z1, ye, tp)
    roof_from(facets, h, part("Roof", "EX_Roof", layer), keep)
    ROOFS.append(dict(name=name, kind="hip", x=[x0, x1], z=[z0, z1], eave=ye, tan=tp, keep=keep is not None, walls=list(rect)))
    if cornice:
        eave_box(rect, over, ye, layer, frieze, cornice_keep if cornice_keep is not None else keep)
    return h


def eave_box(rect, over, ye, layer, frieze, keep=None):
    """Fascia, soffit and (main block) frieze round a roof's eave line; skipped where 'keep' cuts the roof off."""
    T = part("Cornice", "EX_Trim", layer)
    G_ = part("Gutter", "EX_Gutter", layer)
    x0, x1, z0, z1 = rect
    fh = 0.20                                          # fascia depth below the roof plane's eave
    sides = [("x", x1, 1, z0 - over, z1 + over), ("x", x0, -1, z0 - over, z1 + over), ("z", z1, 1, x0 - over, x1 + over), ("z", z0, -1, x0 - over, x1 + over)]
    runs = []
    for axis, d, s, a0, a1 in sides:
        if keep is None:
            runs.append((axis, d, s, a0, a1)); continue
        dm = d + s * over * 0.5     # clip the run to the kept roof (a wing abutting a wall keeps only its free eaves)
        ln = LineString([P(axis, a0, 0, dm)[::2], P(axis, a1, 0, dm)[::2]]).intersection(keep)
        for g in ([ln] if ln.geom_type == "LineString" else list(getattr(ln, "geoms", []))):
            if g.is_empty or g.length < 0.05: continue
            cs = [q[1] if axis == "x" else q[0] for q in g.coords]
            runs.append((axis, d, s, min(cs), max(cs)))
    for axis, d, s, a0, a1 in runs:
        if axis == "x":
            box(T, d + s * (over - 0.04), d + s * over, ye - fh, ye + RT * 0.5, a0, a1)                        # fascia
            box(T, d, d + s * (over - 0.04), ye - fh, ye - fh + 0.03, a0 + (0.04 if s else 0), a1)             # soffit
            box(G_, d + s * over, d + s * (over + 0.11), ye - fh + 0.05, ye + RT * 0.3, a0, a1)               # gutter
            mound(part("GutterSnow", "EX_Snow", layer), "x", d, s, a0, a1, ye + RT * 0.3, over - 0.02, over + 0.11, 0.05, seed=int(d * 7))
            icicles(part("Icicles", "EX_Ice", layer), "x", d, s, a0, a1, ye - fh + 0.05, over + 0.10, seed=int(d * 7))
            if frieze: box(T, d, d + s * 0.025, ye - fh - frieze, ye - fh, a0 + over, a1 - over)
        else:
            box(T, a0, a1, ye - fh, ye + RT * 0.5, d + s * (over - 0.04), d + s * over)
            box(T, a0, a1, ye - fh, ye - fh + 0.03, d, d + s * (over - 0.04))
            box(G_, a0, a1, ye - fh + 0.05, ye + RT * 0.3, d + s * over, d + s * (over + 0.11))
            mound(part("GutterSnow", "EX_Snow", layer), "z", d, s, a0, a1, ye + RT * 0.3, over - 0.02, over + 0.11, 0.05, seed=int(d * 7))
            icicles(part("Icicles", "EX_Ice", layer), "z", d, s, a0, a1, ye - fh + 0.05, over + 0.10, seed=int(d * 7))
            if frieze: box(T, a0 + over, a1 - over, ye - fh - frieze, ye - fh, d, d + s * 0.025)


def build_roofs():
    fm = (MAIN["x"][0] - V, FRONT_MAIN, MAIN["z"][0], MAIN["z"][1])
    # the main block's end eaves run only where no section roof covers them (they poked through the section roofs as white strips)
    ck = sbox(fm[0] - OVER - 1, fm[2] - OVER - 1, fm[1] + OVER + 1, fm[3] + OVER + 1).difference(
        sbox(RIGHT["x"][0] - V - 0.35, RIGHT["z"][0] - 2, RIGHT["x"][1] + V + 0.35, RIGHT["z"][1] + 0.6)).difference(
        sbox(DEN["x"][0] - V - 0.35, DEN["z"][0] - 0.6, DEN["x"][1] + V + 0.35, DEN["z"][1] + 2))
    hm = hip_roof("main", fm, OVER, EAVE, TP, "U", frieze=0.18, cornice_keep=ck)
    hd = hip_roof("den", (DEN["x"][0] - V, DEN["x"][1] + V, DEN["z"][0], DEN["z"][1] + V), 0.35, EAVE_S, TP, "U", frieze=0.0)
    hr = hip_roof("right", (RIGHT["x"][0] - V, RIGHT["x"][1] + V, RIGHT["z"][0] - V, RIGHT["z"][1]), 0.35, EAVE_S, TP, "U", frieze=0.0)
    # kitchen wing: hipped on its three free sides (film 4575), abutting the right section and the main block's rear wall
    wing = (-5.332 - V, 2.316 - V, -1.055 - V, 4.225 + V)
    keep = Polygon([(-9, -4), (RIGHT["x"][0] - V, -4), (RIGHT["x"][0] - V, MAIN["z"][0]), (MAIN["x"][0] - V, MAIN["z"][0]),
                    (MAIN["x"][0] - V, 4.225 + V), (-1.645 - V, 4.225 + V), (-1.645 - V, 9), (-9, 9)])   # the back stair's lean-to takes over past z 4.33
    tw = math.tan(math.radians(25.0))
    hip_roof("wing", (wing[0], wing[1] + 3.0, wing[2], wing[3]), 0.30, -0.45, tw, "U", keep=keep)
    # back stair lean-to: falls to -x from the main rear wall (under the girls_a / parents bath windows' sills 0.54)
    # back stair lean-to: falls to -x from the main rear wall, over the service stair's ceiling opening (top -0.215, x -1.505..1.48) and
    # under the girls_a window's sill (0.46)
    lean("backstair", "x", MAIN["x"][0] - V, -1.645 - V, 4.225 + V, 7.778, 0.30, 0.15, -0.25, "U", ends=(False, False), rake=(0.0, 0.62))
    # back hall lean-to: from the landing window's sill (-0.336) down to the back hall's wall (top -0.721)
    lean("backhall", "x", MAIN["x"][0] - V, -0.132 - V, 7.778, 11.57 + V, 0.30, -0.41 - RT, -0.75, "L", ends=(False, True), rake=(0.0, 0.18))
    return hm, hd, hr


def lean(name, axis, hi_d, lo_d, a0, a1, over, y_hi, y_lo_eave, layer, ends=(True, True), rake=(0.18, 0.18)):
    """A lean-to from the wall line hi_d (top y_hi under the covering) down past lo_d by 'over' to y_lo_eave (fascia line); an end
    that abuts another roof (ends False) has no overhang."""
    d_eave = lo_d - over
    a0, a1 = a0 - (over if ends[0] else 0.0), a1 + (over if ends[1] else 0.0)
    tp = (y_hi - y_lo_eave) / (hi_d - d_eave)
    def h(x, z): return y_lo_eave + tp * (x - d_eave)
    F = part("Roof", "EX_Roof", layer)
    pts = [(d_eave, a0), (hi_d, a0), (hi_d, a1), (d_eave, a1)]
    face(F, [(x, h(x, z) + RT, z) for x, z in pts], (0, 1, 0))
    T = part("Cornice", "EX_Trim", layer); G_ = part("Gutter", "EX_Gutter", layer)
    box(T, d_eave, d_eave + 0.04, y_lo_eave - 0.18, y_lo_eave + RT * 0.5, a0, a1)
    box(T, d_eave + 0.04, lo_d, y_lo_eave - 0.18, y_lo_eave - 0.15, a0, a1)
    box(G_, d_eave - 0.11, d_eave, y_lo_eave - 0.13, y_lo_eave + RT * 0.3, a0, a1)
    for a, s, rk in ((a0, 1, rake[0]), (a1, -1, rake[1])):   # rake boards at the ends, inside the roof's plan
        if rk > 0:
            prism(T, [(d_eave, y_lo_eave - rk, a), (hi_d, y_hi - rk, a), (hi_d, y_hi + RT, a), (d_eave, y_lo_eave + RT, a)], (0, 0, s * 0.03))
    ROOFS.append(dict(name=name, kind="lean", x=[d_eave, hi_d], z=[a0, a1], eave=y_lo_eave, tan=tp, walls=[lo_d, hi_d, a0, a1]))


# ---------------------------------------------------------------- window units, trim, shutters
def sash_unit(face_axis, d, s, a0, a1, y0, y1, layer, recess=0.07, rows=(3, 3), cols=2, shade=True, sheer=False):
    """A double-hung unit set 'recess' behind the brick face d (outward s): white frame, two sashes with muntins, dark glass and a
    drawn shade behind (glows at night, SpecGreybox.Shell adds it to the night mode's glow list)."""
    T = part("Sash", "EX_Trim", layer); Gl = part("Glass", "EX_Glass", layer); Sh = part("Shade", "EX_Shade", layer)
    if sheer: Gl, shade = part("Sheer", "EX_Sheer", layer), False   # a sealed room behind: sheers behind glossy glass fill the panes (glow at night)
    df = d - s * recess
    fw = 0.055
    def bx(F, a_0, a_1, y_0, y_1, t0, t1):
        if face_axis == "x": box(F, df + s * t0, df + s * t1, y_0, y_1, a_0, a_1)
        else: box(F, a_0, a_1, y_0, y_1, df + s * t0, df + s * t1)
    bx(T, a0, a0 + fw, y0, y1, -0.06, 0.0); bx(T, a1 - fw, a1, y0, y1, -0.06, 0.0)
    bx(T, a0, a1, y1 - fw, y1, -0.06, 0.0); bx(T, a0, a1, y0, y0 + fw, -0.06, 0.0)
    ym = (y0 + y1) / 2
    bx(T, a0 + fw, a1 - fw, ym - 0.025, ym + 0.025, -0.04, -0.005)              # meeting rail (its back on the glass's front: 5 mm behind the glass's back face z-fought, realism build 3)
    ia0, ia1 = a0 + fw, a1 - fw
    for k in range(1, cols):
        a = ia0 + (ia1 - ia0) * k / cols
        bx(T, a - 0.011, a + 0.011, y0 + fw, y1 - fw, -0.04, -0.01)
    for (yb, yt_), nr in (((y0 + fw, ym - 0.025), rows[1]), ((ym + 0.025, y1 - fw), rows[0])):
        for k in range(1, nr):
            yy = yb + (yt_ - yb) * k / nr
            bx(T, ia0, ia1, yy - 0.011, yy + 0.011, -0.04, -0.01)
    # glass: one outward face 1 cm behind the muntins (a 5 mm box's back face sat 5 mm from the muntins' backs: z-fight, realism build 4)
    gp = [(ia0, y0 + fw), (ia1, y0 + fw), (ia1, y1 - fw), (ia0, y1 - fw)]
    face(Gl, [P(face_axis, a, y, df - s * 0.05) for a, y in gp], (s, 0, 0) if face_axis == "x" else (0, 0, s))
    if shade:   # a shade drawn two thirds down (film 4382: blinds/sheers in most upper sashes)
        bx(Sh, ia0, ia1, y1 - fw - (y1 - y0) * 0.62, y1 - fw, -0.09, -0.085)


def mulled(face_axis, d, s, a0, a1, y0, y1, n, layer, shade=True, recess=0.07, sheer=False):
    w = (a1 - a0 - 0.064 * (n - 1)) / n
    T = part("Sash", "EX_Trim", layer)
    for k in range(n):
        u0 = a0 + k * (w + 0.064)
        sash_unit(face_axis, d, s, u0, u0 + w, y0, y1, layer, recess=recess, shade=shade, sheer=sheer)
        if k:
            if face_axis == "x": box(T, d - s * recess, d - s * 0.01, y0, y1, u0 - 0.064, u0)
            else: box(T, u0 - 0.064, u0, y0, y1, d - s * recess, d - s * 0.01)


def surround(face_axis, d, s, a0, a1, y0, y1, layer, sill=True, key=False, head=True):
    """White brick mould round an opening on the brick face, a limestone sill and (film 4382, ground front) a stone label block."""
    T = part("Mould", "EX_Trim", layer); S = part("Stone", "EX_Stone", layer)
    m = 0.07
    def bx(F, a_0, a_1, y_0, y_1, t0, t1):
        if face_axis == "x": box(F, d + s * t0, d + s * t1, y_0, y_1, a_0, a_1)
        else: box(F, a_0, a_1, y_0, y_1, d + s * t0, d + s * t1)
    bx(T, a0 - m, a0, y0, y1 + (m if head else 0), 0.0, 0.025)
    bx(T, a1, a1 + m, y0, y1 + (m if head else 0), 0.0, 0.025)
    if head: bx(T, a0, a1, y1, y1 + m, 0.0, 0.025)
    if sill: bx(S, a0 - m - 0.05, a1 + m + 0.05, y0 - 0.07, y0 - 0.005, 0.0, 0.06)
    if sill: mound(part("SillSnow", "EX_Snow", layer), face_axis, d, s, a0 - m - 0.04, a1 + m + 0.04, y0 - 0.005, 0.0, 0.058, 0.028, seed=int(a0 * 10))
    if key:
        ac = (a0 + a1) / 2
        bx(S, ac - 0.11, ac + 0.11, y1 + m + 0.10, y1 + m + 0.24, 0.0, 0.03)


def shutters(face_axis, d, s, a0, a1, y0, y1, layer):
    """Black louvered shutters either side of the opening (film 4382: main block, both storeys)."""
    Sh = part("Shutter", "EX_Shutter", layer)
    w = min((a1 - a0) / 2, 0.48)
    for b0, b1 in ((a0 - 0.07 - w - 0.02, a0 - 0.07 - 0.02), (a1 + 0.07 + 0.02, a1 + 0.07 + 0.02 + w)):
        def bx(a_0, a_1, y_0, y_1, t0, t1):
            if face_axis == "x": box(Sh, d + s * t0, d + s * t1, y_0, y_1, a_0, a_1)
            else: box(Sh, a_0, a_1, y_0, y_1, d + s * t0, d + s * t1)
        bx(b0, b1, y0, y1, 0.02, 0.045)                                      # back panel
        st = 0.055
        bx(b0, b0 + st, y0, y1, 0.045, 0.06); bx(b1 - st, b1, y0, y1, 0.045, 0.06)
        ym = (y0 + y1) / 2
        for ya, yb in ((y0, y0 + st), (ym - st / 2, ym + st / 2), (y1 - st, y1)):
            bx(b0 + st, b1 - st, ya, yb, 0.045, 0.06)
        y = y0 + st + 0.03
        while y < y1 - st - 0.03:                                            # louvres
            if abs(y - ym) > st / 2 + 0.02:
                bx(b0 + st, b1 - st, y, y + 0.022, 0.045, 0.055)
            y += 0.055


def build_windows():
    # upper storey (film), U
    for w in UPW_LIST:
        s = 1 if w["face"] in ("front", "den_front", "den_end", "right_front") else -1
        if w["units"] == 1:
            sash_unit(w["axis"], w["d"], s, w["a0"], w["a1"], w["y0"], w["y1"], "U")
        else:
            mulled(w["axis"], w["d"], s, w["a0"], w["a1"], w["y0"], w["y1"], w["units"], "U")
        surround(w["axis"], w["d"], s, w["a0"], w["a1"], w["y0"], w["y1"], "U")
        if w.get("shutters"):
            shutters(w["axis"], w["d"], s, w["a0"], w["a1"], w["y0"], w["y1"], "U")
    # the sunroom's windows (no opening: the room is sealed), L; the sash 2.5 cm behind the brick so its sheers stand in front of the
    # grey-box wall's outer face (veneer 0.10: sheers 7 cm in, the wall face 10 cm)
    for w in BLIND:
        mulled(w["axis"], w["d"], w["s"], w["a0"], w["a1"], w["y0"], w["y1"], 4, "L", recess=0.025, sheer=True)
        surround(w["axis"], w["d"], w["s"], w["a0"], w["a1"], w["y0"], w["y1"], "L", key=True)
    # ground openings: brick mould, sills, label blocks (front), shutters on the main block's front French windows (film)
    for o in OPEN:
        if o["room"] in ("landing", "front_door"):
            continue
        axis = o["axis"]
        # which veneer plane, outward sign
        if axis == "x":
            if o["c"] > 9.0: d, s = (FRONT_MAIN if o["c"] > 9.9 else o["c"] + 0.07 + V), 1   # the brick face (was FRONT_MAIN + V: mould 10 cm proud, fixed Oct 18 polish)
            else: d, s = o["c"] - 0.07 - V, -1
        else:
            if o["c"] > 15: d, s = o["c"] + 0.07 + V, 1
            elif o["c"] < 0: d, s = o["c"] - 0.07 - V, -1
            else: d, s = o["c"] + 0.07 + V, 1
        door = o["y0"] - GF < 0.05
        front = axis == "x" and o["c"] > 9.9
        surround(axis, d, s, o["a0"], o["a1"], o["y0"], o["y1"], "L", sill=not door or front, key=front or (axis == "x" and 9.0 < o["c"] < 9.9))
        if front and o["room"] in ("dining_room", "living_room"):
            shutters(axis, d, s, o["a0"], o["a1"], o["y0"], o["y1"], "L")


# ---------------------------------------------------------------- dormers, chimney, portico, door face
def dormer(zc, xface, s, roof_h, layer, w=1.50, win=(0.62, 1.06), casement=False):
    """A gabled dormer whose face stands at xface (s: +1 on the front slope, -1 on the rear), sill just over the roof there."""
    T = part("Dormer", "EX_Trim", layer); R = part("Roof", "EX_Roof", layer)
    yr0 = roof_h(xface, zc)
    ys = yr0 + 0.02; yh = ys + win[1]; ye = yh + 0.16; pr = math.tan(math.radians(45.0))
    yp = ye + (w / 2 + 0.08) * pr
    # how far back the dormer runs: until the main roof reaches its ridge
    xb = xface
    while roof_h(xb, zc) < yp + 0.2 and abs(xb - xface) < 4.0:
        xb -= s * 0.05
    z0, z1 = zc - w / 2, zc + w / 2
    # face (white boards) with the window opening, cheeks down to the slope, pediment and cornice
    wall(T, "x", xface - s * 0.06, s, z0, z1, yr0 - 0.05, ye, 0.06, holes=[dict(a0=zc - win[0] / 2, a1=zc + win[0] / 2, y0=ys, y1=yh)], top=True)
    for zz, sg in ((z0, -1), (z1, 1)):
        n = 6   # the cheek follows the slope: one strip per step (its outline is not convex)
        for k in range(n):
            xa_, xb_ = xb + (xface - xb) * k / n, xb + (xface - xb) * (k + 1) / n
            ya_, yb_ = min(roof_h(xa_, zc) - 0.05, ye), min(roof_h(xb_, zc) - 0.05, ye)
            q = [(xa_, ya_, zz), (xb_, yb_, zz), (xb_, ye, zz), (xa_, ye, zz)]
            face(T, q, (0, 0, sg))
            face(T, [(x_, y_, zz + sg * 0.05) for x_, y_, _ in q], (0, 0, sg))
    # cornice + pediment
    xo = xface + s * 0.08
    box(T, xface - s * 0.06, xo, ye - 0.12, ye, z0 - 0.08, z1 + 0.08)
    prism(T, [(xo - s * 0.02, ye, z0 - 0.08), (xo - s * 0.02, ye, z1 + 0.08), (xo - s * 0.02, yp, zc)], (-s * 0.10, 0, 0))
    for sg in (-1, 1):   # raking cornice boards
        ze = zc + sg * (w / 2 + 0.16)
        prism(T, [(xo, ye - 0.05, ze), (xo, yp + 0.03, zc), (xo, yp + 0.13, zc), (xo, ye + 0.05, ze)], (-s * 0.12, 0, 0))
    # dormer roof: two slopes from the ridge (xo .. xb) down to its eaves
    for sg in (-1, 1):
        ze = zc + sg * (w / 2 + 0.16)
        face(R, [(xo, ye + 0.05, ze), (xo, yp + 0.13, zc), (xb, yp + 0.13, zc), (xb, ye + 0.05, ze)], (0, 1, 0))
        face(R, [(xo, ye + 0.05 - 0.04, ze), (xo, yp + 0.09, zc), (xb, yp + 0.09, zc), (xb, ye + 0.05 - 0.04, ze)], (0, -1, 0))
    if casement:   # the zipline dormer: a pair of 3-lite casements open outward (film 10950)
        Tr = part("Casement", "EX_Trim", layer); Gl = part("Glass", "EX_Glass", layer)
        lw = win[0] / 2
        for sg in (-1, 1):
            hz = zc + sg * win[0] / 2
            x0_ = xface + s * 0.0
            box(Tr, x0_, x0_ + s * lw, ys, ys + 0.04, hz - sg * 0.02, hz)
            box(Tr, x0_, x0_ + s * lw, yh - 0.04, yh, hz - sg * 0.02, hz)
            box(Tr, x0_ + s * (lw - 0.04), x0_ + s * lw, ys, yh, hz - sg * 0.02, hz)
            box(Tr, x0_, x0_ + s * 0.04, ys, yh, hz - sg * 0.02, hz)
            for k in (1, 2):
                yy = ys + (yh - ys) * k / 3
                box(Tr, x0_, x0_ + s * lw, yy - 0.012, yy + 0.012, hz - sg * 0.018, hz - sg * 0.002)
            box(Gl, x0_ + s * 0.04, x0_ + s * (lw - 0.04), ys + 0.04, yh - 0.04, hz - sg * 0.012, hz - sg * 0.008)
        # behind the open window: drawn curtains (film 9435: lit, curtained), so the opening never shows the hidden attic
        box(part("Shade", "EX_Shade", layer), xface - s * 0.30, xface - s * 0.28, ys - 0.02, yh + 0.02, zc - win[0] / 2 - 0.02, zc + win[0] / 2 + 0.02)
    else:
        sash_unit("x", xface, s, zc - win[0] / 2, zc + win[0] / 2, ys, yh, layer, recess=0.05, rows=(3, 3))
    return dict(z=zc, face=xface, sill=ys, head=yh, peak=yp + 0.13)


def chimney(x0, x1, z0, z1, y0, ytop, layer):
    B = part("Brick", "EX_Brick", layer); S = part("Stone", "EX_Stone", layer); C = part("Pots", "EX_Pot", layer)
    box(B, x0, x1, y0, ytop - 0.25, z0, z1, skip=("y0",))
    box(B, x0 - 0.05, x1 + 0.05, ytop - 0.25, ytop - 0.10, z0 - 0.05, z1 + 0.05)          # corbel
    box(S, x0 - 0.03, x1 + 0.03, ytop - 0.10, ytop, z0 - 0.03, z1 + 0.03)                  # cap
    for zc in (z0 + (z1 - z0) * 0.3, z0 + (z1 - z0) * 0.7):
        xc = (x0 + x1) / 2
        box(C, xc - 0.10, xc + 0.10, ytop, ytop + 0.32, zc - 0.10, zc + 0.10)


def portico(layer):
    """Film 4382/1830: two Tuscan columns and wall pilasters carrying an entablature and a segmental arched canopy over the door
    (columns 2.8 m apart, 1.3 m out, entablature top 2.56 m and crown 3.12 m over the floor at 0.0104 m/px)."""
    T = part("Portico", "EX_Trim", layer); R = part("Roof", "EX_Roof", layer)
    zc, xw = 9.716, FRONT_MAIN
    half, xc = 1.42, xw + 1.28
    ys = -3.09                                   # the stoop (SpecGreybox.Yard)
    ye0, ye1 = GF + 2.36, GF + 2.56
    crown = GF + 3.12
    for zz in (zc - half, zc + half):
        Cl = part("Column", "EX_Trim", layer)
        box(Cl, xc - 0.17, xc + 0.17, ys, ys + 0.12, zz - 0.17, zz + 0.17)                 # plinth
        prof = [(0.0, 0.135), (ye0 - ys - 0.30, 0.115), (ye0 - ys - 0.22, 0.13), (ye0 - ys - 0.12, 0.16)]
        n = 16
        rings = [[(xc + r * math.cos(2 * math.pi * k / n), ys + 0.12 + hh, zz + r * math.sin(2 * math.pi * k / n)) for k in range(n)] for hh, r in prof]
        for a, b in zip(rings, rings[1:]):
            for k in range(n):
                k2 = (k + 1) % n
                q = [a[k], a[k2], b[k2], b[k]]
                m = [sum(p[i] for p in q) / 4 for i in range(3)]
                face(Cl, q, (m[0] - xc, 0, m[2] - zz))
        box(Cl, xc - 0.19, xc + 0.19, ye0 - 0.12 + 0.0, ye0, zz - 0.19, zz + 0.19)       # capital abacus
        box(T, xw, xw + 0.06, ys, ye0, zz - 0.15, zz + 0.15)                               # pilaster on the wall
    box(T, xw, xc + 0.22, ye0, ye1, zc - half - 0.22, zc + half + 0.22)                    # entablature
    # the arched canopy: a segmental arch over the span, extruded from the wall to the front, thickness 0.22 (face band) and a
    # roof skin over it
    span = half + 0.22; rise = crown - ye1
    R_ = (span ** 2 + rise ** 2) / (2 * rise); zc0 = ye1 + rise - R_
    n = 16
    def arc(r, k):
        a = math.asin(span / R_)
        t = -a + 2 * a * k / n
        return (zc + R_ * math.sin(t) * (r / R_), zc0 + r * math.cos(t))
    for k in range(n):
        (za, ya), (zb, yb) = arc(R_, k), arc(R_, k + 1)
        (za2, ya2), (zb2, yb2) = arc(R_ - 0.25, k), arc(R_ - 0.25, k + 1)
        ya2, yb2 = max(ya2, ye1), max(yb2, ye1)
        # front band
        face(T, [(xc + 0.22, ya2, za2), (xc + 0.22, yb2, zb2), (xc + 0.22, yb, zb), (xc + 0.22, ya, za)], (1, 0, 0))
        # top (roof) from the wall to the front
        face(R, [(xw, ya + 0.02, za), (xw, yb + 0.02, zb), (xc + 0.24, yb + 0.02, zb), (xc + 0.24, ya + 0.02, za)], (0, 1, 0))
        # soffit of the band (inner arc)
        face(T, [(xw, ya2, za2), (xw, yb2, zb2), (xc + 0.22, yb2, zb2), (xc + 0.22, ya2, za2)], (0, -1, 0))
    face(T, [(xc + 0.22, ye1, zc - span), (xc + 0.22, ye1, zc + span), (xc + 0.22, ye1 - 0.01, zc + span), (xc + 0.22, ye1 - 0.01, zc - span)], (1, 0, 0))
    ROOFS.append(dict(name="portico", kind="box", x=[xw, xc + 0.24], z=[zc - span, zc + span], eave=crown + 0.05, tan=0.0, walls=[]))


def door_face(layer):
    """The front door's outside (film 4382, 1495, 1830): a black six-panel leaf with a brass knocker and the wreath, white sidelight
    frames and an elliptical fanlight under the brick arch; on the closed vestibule wall's outer face (x 10.27), in the brick opening."""
    T = part("DoorTrim", "EX_Trim", layer); D = part("DoorLeaf", "EX_DoorBlack", layer); Gl = part("Glass", "EX_Glass", layer)
    Br = part("Brass", "EX_Brass", layer); Wr = part("Wreath", "EX_Wreath", layer); Rb = part("Bow", "EX_Bow", layer)
    xw = 10.27
    z0, z1 = 9.31, 10.121
    y0, y1 = GF, GF + 1.898
    box(D, xw, xw + 0.03, y0, y1, z0, z1)
    for (a, b) in ((0.12, 0.62), (0.72, 1.38), (1.48, 1.80)):
        for (c, d) in ((z0 + 0.09, (z0 + z1) / 2 - 0.04), ((z0 + z1) / 2 + 0.04, z1 - 0.09)):
            box(D, xw + 0.03, xw + 0.045, y0 + a, y0 + b, c, d)
    box(Br, xw + 0.045, xw + 0.07, y0 + 0.95, y0 + 1.05, z1 - 0.12, z1 - 0.08)            # handle
    box(Br, xw + 0.045, xw + 0.06, y0 + 1.30, y0 + 1.42, (z0 + z1) / 2 - 0.05, (z0 + z1) / 2 + 0.05)   # knocker
    # pilasters and sidelight frames (the sidelight glass is the wall's own opening: hifi_door.py)
    for (a, b) in ((8.848, 8.978), (9.255, 9.31), (10.121, 10.176), (10.453, 10.583)):   # outer pilasters 1 cm into the brick reveal (coplanar at 8.968/10.463, realism build 4)
        box(T, xw, xw + 0.06, y0, GF + 1.93, a, b)
    for (a, b) in ((8.968, 9.255), (10.176, 10.463)):
        box(T, xw, xw + 0.04, GF + 1.834, GF + 1.93, a, b)   # 1 cm under the brick head reveal (coplanar at 1.844, realism build 3)
        box(T, xw, xw + 0.04, GF, GF + 0.422, a, b)   # 1 cm over the brick sill reveal (coplanar at 0.412)
        box(T, xw + 0.04, xw + 0.05, GF + 0.08, GF + 0.33, a + 0.04, b - 0.04)
    box(T, xw, xw + 0.06, GF + 1.898, GF + 1.93, 8.848, 10.583)                            # transom bar
    # fanlight: elliptical, radial muntins
    zc, span, rise = 9.7155, (10.583 - 8.848) / 2, 0.188
    n = 14
    for k in range(n):
        ua, ub = -1 + 2 * k / n, -1 + 2 * (k + 1) / n
        ya, yb = GF + 1.93 + rise * math.sqrt(max(0, 1 - ua * ua)), GF + 1.93 + rise * math.sqrt(max(0, 1 - ub * ub))
        face(Gl, [(xw + 0.01, GF + 1.93, zc + ua * span), (xw + 0.01, GF + 1.93, zc + ub * span), (xw + 0.01, yb, zc + ub * span), (xw + 0.01, ya, zc + ua * span)], (1, 0, 0))
        if k % 2 == 0:
            box(T, xw + 0.01, xw + 0.03, GF + 1.93, ya, zc + ua * span - 0.008, zc + ua * span + 0.008)
    # the wreath (film 1495): a ring of boxes and a red bow
    wc_y, wr = GF + 1.47, 0.22
    for k in range(16):
        t = 2 * math.pi * k / 16
        cz, cy = (z0 + z1) / 2 + wr * math.cos(t), wc_y + wr * math.sin(t)
        box(Wr, xw + 0.045, xw + 0.11, cy - 0.06, cy + 0.06, cz - 0.06, cz + 0.06)
    box(Rb, xw + 0.10, xw + 0.13, wc_y - wr - 0.10, wc_y - wr + 0.04, (z0 + z1) / 2 - 0.10, (z0 + z1) / 2 + 0.10)


def garage_oculus(layer):
    """Film 6399/2515: a round window with spokes in the detached garage's street gable, under its cupola (the old GLB's garage has the
    cupola and no oculus). On the registered GLB gable face (x -0.45, apex y 0.99, z 19.65-26.87): centre z 23.26, y 0.05."""
    T = part("Oculus", "EX_Trim", layer); Gl = part("OculusGlass", "EX_Glass", layer)
    x, zc, yc, ro, ri, n = -0.40, 23.26, 0.05, 0.36, 0.27, 20
    for k in range(n):
        a, b = 2 * math.pi * k / n, 2 * math.pi * (k + 1) / n
        q = [(x, yc + ri * math.sin(a), zc + ri * math.cos(a)), (x, yc + ri * math.sin(b), zc + ri * math.cos(b)),
             (x, yc + ro * math.sin(b), zc + ro * math.cos(b)), (x, yc + ro * math.sin(a), zc + ro * math.cos(a))]
        face(T, [(x + 0.05, p[1], p[2]) for p in q], (1, 0, 0))
        face(T, [(x + 0.05, q[3][1], q[3][2]), (x + 0.05, q[2][1], q[2][2]), (x, q[2][1], q[2][2]), (x, q[3][1], q[3][2])], (0, q[3][1] - yc, q[3][2] - zc))
    face(Gl, [(x + 0.01, yc + ri * math.sin(2 * math.pi * k / n), zc + ri * math.cos(2 * math.pi * k / n)) for k in range(n)], (1, 0, 0))
    # spokes: a cross
    box(T, x + 0.01, x + 0.04, yc - 0.012, yc + 0.012, zc - ri, zc + ri)
    box(T, x + 0.01, x + 0.04, yc - ri, yc + ri, zc - 0.012, zc + 0.012)


def downpipes(layer):
    D = part("Downpipe", "EX_Gutter", layer)
    yt = EAVE - 0.15
    for (x, z, g) in ((FRONT_MAIN + 0.05, 16.21 + 0.10, GRADE["front"]), (FRONT_MAIN + 0.05, 2.864 - 0.10, GRADE["front"]),
                      (MAIN["x"][0] - V - 0.06, 16.21 + 0.10, GRADE["rear"]), (MAIN["x"][0] - V - 0.06, 7.70, GRADE["rear"])):
        box(D, x - 0.04, x + 0.04, g, yt, z - 0.04, z + 0.04)


# ---------------------------------------------------------------- polish (Oct 18, exterior polish TRIAL)
def french_leaves(axis, d, s, a0, a1, y0, y1, layer):
    """Film 2508/1640/4382: the ground French windows from outside, a pair of white leaves of 2 x 5 lites over a raised panel (the
    living room's interior model's pattern, hifi_living.french), in the brick reveal 6 cm behind the face d. Only where the room has
    no leaves of its own (the dining room: grey-box glass and sheers)."""
    T = part("FrenchLeaf", "EX_Trim", layer)   # no glass of its own: the room's glazing and sheers show through (lit at night)
    df = d - s * 0.06
    def bx(F, a_0, a_1, y_0, y_1, t0, t1):
        box(F, df + s * t0, df + s * t1, y_0, y_1, a_0, a_1) if axis == "x" else box(F, a_0, a_1, y_0, y_1, df + s * t0, df + s * t1)
    JT, SS, TR, G0, G1, m = 0.04, 0.055, 0.10, y0 + 0.44, y0 + 1.90, 0.018
    bx(T, a0, a0 + JT, y0, y1, -0.05, 0.0); bx(T, a1 - JT, a1, y0, y1, -0.05, 0.0); bx(T, a0, a1, y1 - JT, y1, -0.05, 0.0)
    lw = (a1 - a0 - 2 * JT) / 2
    for k in range(2):
        b0 = a0 + JT + k * lw; b1 = b0 + lw
        bx(T, b0, b0 + SS, y0, y1 - JT, -0.045, -0.005); bx(T, b1 - SS, b1, y0, y1 - JT, -0.045, -0.005)
        bx(T, b0 + SS, b1 - SS, G1, y1 - JT, -0.045, -0.005); bx(T, b0 + SS, b1 - SS, y0, G0, -0.045, -0.005)
        bx(T, b0 + SS + 0.03, b1 - SS - 0.03, y0 + 0.08, G0 - 0.06, -0.005, 0.005)          # raised panel
        g0, g1 = b0 + SS, b1 - SS
        bx(T, (g0 + g1) / 2 - m / 2, (g0 + g1) / 2 + m / 2, G0, G1, -0.035, -0.012)
        for r in range(1, 5):
            yy = G0 + (G1 - G0) * r / 5; bx(T, g0, g1, yy - m / 2, yy + m / 2, -0.035, -0.012)


BULB, BULB_STEP = 0.024, 0.055   # realism pass: twice the density (Pietro/film 10 read as thick outlines), draped, varied
_BULBN = [0]


def bulb_loop(B, axis, d, s, a0, a1, y0, y1, closed=True):
    """Film 10/1470/3377: warm mini-lights strung round a window's outline (just outside its mould), 7.5 cm proud of the face d.
    Exterior realism (Oct 18): a real strand: clipped every ~0.30 m, sagging 1-2.5 cm between clips on the level runs (bowing out a
    little on the verticals), a dark wire along it, bulbs of varied size on short leads in three tints (bright/warm/dim parts)."""
    q = d + s * 0.075   # in front of the sills and shutters (0.06)
    lay = B["layer"]; parts_ = (B["faces"], part("XmasBulbsWarm", "EX_BulbWarm", lay), part("XmasBulbsDim", "EX_BulbDim", lay))
    W = part("XmasWire", "EX_Wire", lay)
    corners = [(a0, y0), (a0, y1), (a1, y1), (a1, y0)] + ([(a0, y0)] if closed else [])
    prev = None
    for (pa, py), (qa, qy) in zip(corners, corners[1:]):
        L = math.hypot(qa - pa, qy - py); n = max(1, round(L / BULB_STEP)); nclip = max(1, round(L / 0.30))
        level = abs(qy - py) < 1e-6
        for k in range(n + 1):
            u = k / n; a = pa + (qa - pa) * u; y = py + (qy - py) * u
            v = (u * nclip) % 1.0; sag = (0.010 + 0.015 * _vnoise(a * 3, y * 3, 4)) * 4 * v * (1 - v)
            if level: y -= sag
            off = 0.0 if level else sag * 0.6
            cur = (a, y, q + s * off)
            if prev is not None:   # the wire from the last point (4 mm square)
                (pa_, py_, pq_), (ca, cy, cq) = prev, cur; w = 0.002
                if axis == "x":
                    face(W, [(pq_, py_ - w, pa_), (cq, cy - w, ca), (cq, cy + w, ca), (pq_, py_ + w, pa_)], (s, 0, 0))
                else:
                    face(W, [(pa_, py_ - w, pq_), (ca, cy - w, cq), (ca, cy + w, cq), (pa_, py_ + w, pq_)], (0, 0, s))
            prev = cur
            if k == n: continue
            _BULBN[0] += 1; r = _vnoise(_BULBN[0] * 0.731, 3.3, 17)
            h = BULB / 2 * (0.7 + 0.6 * _vnoise(_BULBN[0] * 1.913, 1.1, 5))
            dy = -0.012 * _vnoise(_BULBN[0] * 0.37, 2.0, 8)   # hangs a little off the wire on its lead
            F = parts_[0 if r < 0.45 else 1 if r < 0.8 else 2]
            qq = q + s * (off + 0.006)
            box(F, qq - h, qq + h, y + dy - h, y + dy + h, a - h, a + h) if axis == "x" else box(F, a - h, a + h, y + dy - h, y + dy + h, qq - h, qq + h)


def xmas_lights(D):
    """The front's Christmas lights: every window of the street side outlined (film 10: both storeys, the den and right sections,
    both dormers), drawn as emissive bulbs (EX_Bulb: SpecGreybox.Shell lights them at night only, HouseNightMode's glow list)."""
    out, lo = 0.08, 0.09   # on the mould's outer edge, inside the shutters (they start 0.09 off the opening); under the sill
    part("XmasBulbs", "EX_Bulb", "U"); part("XmasBulbs", "EX_Bulb", "L"); BU, BL = parts["U_XmasBulbs"], parts["L_XmasBulbs"]
    for w in UPW_LIST:
        if w["face"] in ("front", "den_front", "right_front"):
            bulb_loop(BU, "x", w["d"], 1, w["a0"] - out, w["a1"] + out, w["y0"] - lo, w["y1"] + out)
    for w in BLIND[:1]:   # the street face only (film 10)
        bulb_loop(BL, "x", w["d"], 1, w["a0"] - out, w["a1"] + out, w["y0"] - lo, w["y1"] + out)
    for o in OPEN:
        if o["axis"] == "x" and o["c"] > 9.0 and o["room"] in ("den", "dining_room", "living_room"):
            d = FRONT_MAIN if o["c"] > 9.9 else o["c"] + 0.07 + V
            bulb_loop(BL, "x", d, 1, o["a0"] - out, o["a1"] + out, max(o["y0"] - lo, GF + 0.15), o["y1"] + out, closed=o["y0"] - GF > 0.05)
    for dd in D[:2]:
        bulb_loop(BU, "x", dd["face"] + 0.02, 1, dd["z"] - 0.31 - 0.10, dd["z"] + 0.31 + 0.10, dd["sill"] - 0.04, dd["head"] + 0.10)


def porch_lantern(layer):
    """Film 10/714 (night): a lit lantern hanging in the portico on the door's axis. Brass frame, glowing glass (EX_LampGlow)."""
    Br = part("Lantern", "EX_Brass", layer); Gw = part("LanternGlow", "EX_LampGlow", layer)
    xc, zc, top = FRONT_MAIN + 0.62, 9.716, GF + 2.36
    box(Br, xc - 0.008, xc + 0.008, top - 0.30, top, zc - 0.008, zc + 0.008)                # chain/rod
    y1 = top - 0.30; y0 = y1 - 0.36
    box(Br, xc - 0.13, xc + 0.13, y1 - 0.04, y1, zc - 0.13, zc + 0.13)                      # cap
    box(Br, xc - 0.11, xc + 0.11, y0, y0 + 0.03, zc - 0.11, zc + 0.11)                      # base
    for sx in (-1, 1):
        for sz in (-1, 1):
            box(Br, xc + sx * 0.10 - 0.01, xc + sx * 0.10 + 0.01, y0, y1, zc + sz * 0.10 - 0.01, zc + sz * 0.10 + 0.01)
    box(Gw, xc - 0.09, xc + 0.09, y0 + 0.03, y1 - 0.04, zc - 0.09, zc + 0.09)
    return dict(x=xc, y=(y0 + y1) / 2, z=zc)


def _vnoise(x, z, seed=0):
    """smooth value noise (bilinear on a hashed lattice, smoothstep), 0..1"""
    def hsh(i, j):
        h = (i * 374761393 + j * 668265263 + seed * 1442695041) & 0xffffffff
        h = ((h ^ (h >> 13)) * 1274126177) & 0xffffffff
        return (h ^ (h >> 16)) * 2.3283064365386963e-10
    i, j = math.floor(x), math.floor(z); fx, fz = x - i, z - j
    fx, fz = fx * fx * (3 - 2 * fx), fz * fz * (3 - 2 * fz)
    a, b, c, d = hsh(i, j), hsh(i + 1, j), hsh(i, j + 1), hsh(i + 1, j + 1)
    return a + (b - a) * fx + (c - a) * fz + (a - b - c + d) * fx * fz


def roof_snow(roofs, dormers):
    """Film 10 / 1470 (night) and 4382: a light, patchy snow on the main and end-section hips. Cells of 0.12 m on each facet, kept where
    two octaves of noise pass a threshold, 1.5 cm over the covering (never coplanar); none on a hip/ridge line, under a higher roof,
    round the dormers or the chimney."""
    Sn = part("RoofSnow", "EX_Snow", "U")
    C = 0.10
    def jit(x, z):   # every cell corner moved in plan by a hash of its lattice point (shared by the 4 cells): ragged, unstepped edges
        i, k = round(x / C), round(z / C)
        return x + (_vnoise(i * 1.37, k * 1.37, 11) - 0.5) * 0.8 * C, z + (_vnoise(i * 1.37, k * 1.37, 13) - 0.5) * 0.8 * C
    def facet(r, x, z):
        x0, x1 = r["x"]; z0, z1 = r["z"]; d = [x - x0, x1 - x, z - z0, z1 - z]; return d.index(min(d))
    def h(r, x, z): return r["eave"] + r["tan"] * min(x - r["x"][0], r["x"][1] - x, z - r["z"][0], r["z"][1] - z) + RT + 0.015
    def blocked(x, z):
        for dd in dormers:
            if abs(z - dd["z"]) < 1.05 and (dd["face"] - 3.6 < x < dd["face"] + 0.3 if dd["face"] > 5 else dd["face"] - 0.3 < x < dd["face"] + 3.6):
                return True
        return 0.35 < x < 1.65 and 13.0 < z < 14.65
    for r in roofs:
        others = [o for o in roofs if o is not r]
        x0, x1 = r["x"]; z0, z1 = r["z"]
        nx, nz = int((x1 - x0) / C), int((z1 - z0) / C)
        for i in range(nx):
            for k in range(nz):
                xa, za = x0 + i * C, z0 + k * C; xb, zb = xa + C, za + C
                cs = [(xa, za), (xb, za), (xb, zb), (xa, zb)]
                if len({facet(r, x, z) for x, z in cs}) > 1: continue
                xm, zm = xa + C / 2, za + C / 2
                n = 0.65 * _vnoise(xm / 0.9, zm / 0.9, 3) + 0.35 * _vnoise(xm / 0.3, zm / 0.3, 7)
                ed = min(xm - x0, x1 - xm, zm - z0, z1 - zm)   # realism pass: 4382 shows a light dusting, more along the eaves
                n += 0.12 * max(0.0, 1.0 - ed / 0.9)
                if n < 0.80 or blocked(xm, zm): continue
                if any(o["x"][0] - 0.1 < xm < o["x"][1] + 0.1 and o["z"][0] - 0.1 < zm < o["z"][1] + 0.1 and h(o, xm, zm) > h(r, xm, zm) - 0.05 for o in others):
                    continue
                cj = [jit(x, z) for x, z in cs]
                if len({facet(r, x, z) for x, z in cj}) > 1: continue
                face(Sn, [(x, h(r, x, z), z) for x, z in cj], (0, 1, 0))


# ---------------------------------------------------------------- checks
def rooms():
    out = []
    for st, fy in (("ground", GF), ("upstairs", UF)):
        for r in G[st]["rooms"]:
            out.append((st, r["name"], Polygon([(p[0], p[1]) for p in r["poly"]]), fy + 0.002, fy + r["ceil"] - 0.002))
    A = HS["attic_stair"]["attic"]
    out.append(("attic", "attic", sbox(A["x"][0], A["z"][0], A["x"][1], A["z"][1]), A["floor_y"] + 0.01, A["ridge_y"]))
    return out


def check():
    R = rooms(); bad = []
    for key, p in parts.items():
        lay = p["layer"]
        for f in p["faces"]:
            c = [sum(q[i] for q in f) / len(f) for i in range(3)]
            pts = [c] + [[0.8 * q[i] + 0.2 * c[i] for i in range(3)] for q in f]    # the centre and each corner pulled 20% in
            hit = None
            for q in pts:
                for st, nm, poly, y0, y1 in R:
                    if not (y0 < q[1] < y1): continue
                    if lay == "U" and st != "ground": continue      # the upper storey's skin may cross Marina's rooms (hidden upstairs)
                    if poly.buffer(-0.01).contains(Point(q[0], q[2])):
                        hit = f"{key} face point {[round(v, 2) for v in q]} inside {st}/{nm}"; break
                if hit: break
            if hit: bad.append(hit)
    return bad


def main():
    build_walls()
    hm, hd, hr = build_roofs()
    build_windows()
    # dormers: front pair over the 2nd and 4th upper bays (film 4382; old GLB z 6.46 / 13.04), the zipline dormer on the rear slope
    # over the landing window (film 9435, attic dormer z 9.6745)
    D = [dormer(6.702, FRONT_MAIN - 0.78, 1, hm, "U"), dormer(12.938, FRONT_MAIN - 0.78, 1, hm, "U"),
         dormer(9.6745, MAIN["x"][0] - V + 0.62, -1, hm, "U", casement=True)]
    # the living-room flue: outside the rear wall (old GLB chimney_rear x 0.58-1.46 z 13.22-14.46; film 6810/11050 tall stack)
    chimney(0.64, MAIN["x"][0] - V, 13.32, 14.32, GRADE["rear"], 6.75, "U")
    portico("U")
    door_face("L")
    garage_oculus("L")
    downpipes("U")
    for o in OPEN:   # the dining room's French windows have no leaves inside: the film's from the street
        if o["room"] == "dining_room" and o["axis"] == "x" and o["c"] > 9.9:
            french_leaves("x", FRONT_MAIN, 1, o["a0"], o["a1"], o["y0"], o["y1"], "L")
    xmas_lights(D)
    roof_snow([q for q in ROOFS if q["name"] in ("main", "den", "right")], D)
    lantern = porch_lantern("L")
    bad = check()
    out = ROOT / "sfm-work/exterior"; out.mkdir(parents=True, exist_ok=True)
    for v in parts.values(): v["groups"] = GROUPS.get(id(v["faces"]), [])
    (out / "shell.json").write_text(json.dumps(parts))
    nf = {k: len(v["faces"]) for k, v in parts.items()}
    summary = dict(
        what="the exterior skin (tools/house/exterior_shell.py -> Exterior.glb via hifi_exterior.py); read by SpecGreybox.Shell",
        ground_floor=GF, split_y=SPLIT, eave=EAVE, pitch_deg=math.degrees(PITCH), veneer=V,
        sections=dict(main=MAIN, den=DEN, right=RIGHT), front_main=FRONT_MAIN,
        roofs=ROOFS, dormers=D, porch_lantern=lantern, upper_windows=UPW_LIST, blind=BLIND,
        parts={k: dict(layer=v["layer"], mat=v["mat"], faces=len(v["faces"])) for k, v in parts.items()})
    (ROOT / "spec/exterior_shell.json").write_text(json.dumps(summary, indent=1))
    print(f"exterior_shell: {sum(nf.values())} faces in {len(nf)} parts; dormers " + ", ".join(f"z {d['z']:.2f} sill {d['sill']:.2f} peak {d['peak']:.2f}" for d in D))
    print(f"  main ridge y {EAVE + TP * ((FRONT_MAIN + OVER) - (MAIN['x'][0] - V - OVER)) / 2:.2f}")
    if bad:
        print(f"FAIL {len(bad)} faces inside rooms:"); [print("  " + b) for b in bad[:40]]
        sys.exit(1)
    print("ok   no always-drawn face inside a room; no upper face inside a ground room")


if __name__ == "__main__":
    main()
