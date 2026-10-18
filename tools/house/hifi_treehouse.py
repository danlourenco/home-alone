"""hifi_treehouse: Kevin's treehouse, the zipline's fixed rope and the handlebar trolley (Oct 18 2026, TRIAL;
changes/2026-10-18-treehouse-zipline.json). Every number from spec/dressing/treehouse.json (film 6810/11102 rulers, the registered old
GLB's object183 for place and proportions). Spec x, z; y is WORLD (upper floor 0), as hifi_attic.py.

Weathered horizontal boards on a deck round the trunk, the cabin walls flaring out to a shed roof (film 11064, GLB front view), a front
porch with a low rail, the trunk up through the cabin, diagonal braces and porch posts, slats nailed up the trunk, a leaning ladder,
the pirate flag, a bare bulb inside; the rope's fixed parts (loops on the attic collar tie, the run under the dormer's ceiling edge to
the window head, turns round the trunk). The zipline span itself is drawn at runtime (ZipLine.cs) so it can be cut. The trolley
(chrome handlebars with streamers under a pulley block, film 11052-11058) and a rider stand-in are built at the origin (rope contact),
running toward spec -x: ZipLine moves them.

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P tools/house/hifi_treehouse.py
  -> unity/HomeAlone/Assets/Models/Foyer/Treehouse.glb (SpecGreybox.Treehouse places it)
"""
import json
import math
import random
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/house"))
from hifi_lib import Part, material   # noqa: E402

OUT = ROOT / "unity/HomeAlone/Assets/Models/Foyer/Treehouse.glb"
T = json.loads((ROOT / "spec/dressing/treehouse.json").read_text())
random.seed(7)

(cxs, czs), G = T["site"]["center"], T["site"]["grade_y"]
D, C, K, L, R = T["deck"], T["cabin"], T["trunk"], T["ladder"], T["rope"]
DY = G + D["top_above_grade"]                       # deck top (world)
X0, X1 = cxs - D["depth"] / 2, cxs + D["depth"] / 2  # deck back / front (front = +x, toward the house)
Z0, Z1 = czs - D["width"] / 2, czs + D["width"] / 2
XB, XF = X0 + 0.05, X0 + 0.05 + C["depth"]          # cabin back / front wall planes
ZC = czs
HF, HB = C["front_h"], C["back_h"]
TX, TZ = K["at"]

boards = [Part("Boards1", "TH_Board"), Part("Boards2", "TH_Board2")]
timber, bark, roof, rope = Part("Timber", "TH_Timber"), Part("Trunk", "TH_Bark"), Part("Roof", "TH_Roof"), Part("Rope", "TH_Rope")
ladder, flag, pole, bulb, holder = Part("Ladder", "TH_Ladder"), Part("Flag", "TH_Flag"), Part("FlagPole", "TH_Timber"), Part("Bulb", "TH_Bulb"), Part("BulbHolder", "TH_Porcelain")
trolley = [Part("ZipTrolley_Bar", "TH_Chrome"), Part("ZipTrolley_Block", "TH_Steel"), Part("ZipTrolley_Grips", "TH_Grip")]
streamers = [Part(f"ZipTrolley_Streamer{i}", f"TH_Streamer{i}") for i in range(3)]
rider = [Part("ZipRider_Sweater", "TH_Sweater"), Part("ZipRider_Pants", "TH_Pants"), Part("ZipRider_Skin", "TH_Skin"), Part("ZipRider_Hair", "TH_Hair"), Part("ZipRider_Shoes", "TH_Shoes")]


def add(a, b): return tuple(p + q for p, q in zip(a, b))
def sub(a, b): return tuple(p - q for p, q in zip(a, b))
def mul(a, k): return tuple(p * k for p in a)
def cen(ps): return tuple(sum(p[i] for p in ps) / len(ps) for i in range(3))
def norm(a): n = math.sqrt(sum(c * c for c in a)); return tuple(c / n for c in a)


def prism(part, pts, e):
    """convex planar polygon extruded by e, every face oriented away from the solid's centre"""
    top = [add(p, e) for p in pts]; c = cen(pts + top)
    part.face(list(pts), sub(cen(pts), c)); part.face(top, sub(cen(top), c))
    for i in range(len(pts)):
        q = [pts[i], pts[(i + 1) % len(pts)], top[(i + 1) % len(pts)], top[i]]
        part.face(q, sub(cen(q), c))


def beam(part, a, b, w, h, up=(0.0, 1.0, 0.0)):
    """a rectangular member w x h from a to b (h along 'up' projected off the axis)"""
    t = norm(sub(b, a)); u = sub(up, mul(t, sum(x * y for x, y in zip(up, t)))); u = norm(u)
    s = (t[1] * u[2] - t[2] * u[1], t[2] * u[0] - t[0] * u[2], t[0] * u[1] - t[1] * u[0])
    pts = [add(a, add(mul(s, sx * w / 2), mul(u, sy * h / 2))) for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    prism(part, pts, sub(b, a))


def tube(part, path, r, n=8):
    part.sweep(path, [(r * math.cos(2 * math.pi * k / n), r * math.sin(2 * math.pi * k / n)) for k in range(n)])


def clip(poly, keep):
    """Sutherland-Hodgman against one half-plane keep(p) -> signed distance (>= 0 kept); poly in (u, h)"""
    out = []
    for i, p in enumerate(poly):
        q = poly[(i + 1) % len(poly)]; dp, dq = keep(p), keep(q)
        if dp >= 0: out.append(p)
        if (dp >= 0) != (dq >= 0):
            k = dp / (dp - dq); out.append((p[0] + (q[0] - p[0]) * k, p[1] + (q[1] - p[1]) * k))
    return out


def wall(m, n, outline, u_range, holes, top_h):
    """horizontal weathered boards: m(u, h) -> 3D point, n outward normal; outline = half-planes in (u, h); holes = [(u0, u1, h0, h1)]"""
    h = 0.0
    while h < top_h - 0.01:
        bh = random.uniform(0.13, 0.19); h1 = min(h + bh, top_h); gap = random.uniform(0.004, 0.018)
        cuts = [u_range]
        for (a, b, c0, c1) in holes:
            if h1 > c0 and h < c1:
                cuts = [s for (u0, u1) in cuts for s in ((u0, min(u1, a)), (max(u0, b), u1)) if s[1] - s[0] > 0.02]
        for (u0, u1) in cuts:
            poly = [(u0, h), (u1, h), (u1, h1 - gap), (u0, h1 - gap)]
            for f in outline:
                poly = clip(poly, f)
                if len(poly) < 3: break
            if len(poly) >= 3:
                tk = random.uniform(0.018, 0.028)
                prism(random.choice(boards), [m(u, v) for u, v in poly], mul(n, tk))
        h = h1


# ---------------------------------------------------------------- deck: joists, rim, boards
JD = 0.14
for z in [Z0 + 0.03 + k * (D["width"] - 0.06) / 5 for k in range(6)]:                 # joists front-back
    timber.box(X0, X1, DY - 0.03 - JD, DY - 0.03, z - 0.025, z + 0.025)
for x0_, x1_, z0_, z1_ in ((X0 - 0.03, X0, Z0 - 0.03, Z1 + 0.03), (X1, X1 + 0.03, Z0 - 0.03, Z1 + 0.03),
                           (X0, X1, Z0 - 0.03, Z0), (X0, X1, Z1, Z1 + 0.03)):
    timber.box(x0_, x1_, DY - 0.03 - JD, DY - 0.015, z0_, z1_)                           # rim joists, 1.5 cm under the boards' top
x = X0
while x < X1 - 0.01:                                                                      # boards across (along z), weathered gaps
    w = random.uniform(0.12, 0.15); xe = min(x + w - 0.008, X1)
    if not (TX - K["r"] - 0.02 < (x + xe) / 2 < TX + K["r"] + 0.02):
        random.choice(boards).box(x, xe, DY - 0.03, DY - random.uniform(0.0, 0.004), Z0, Z1)
    else:                                                                                 # boards notched round the trunk
        for za, zb in ((Z0, TZ - K["r"] - 0.02), (TZ + K["r"] + 0.02, Z1)):
            random.choice(boards).box(x, xe, DY - 0.03, DY, za, zb)
    x += w

# ---------------------------------------------------------------- porch rail (low, film 11102), open where the ladder lands
RH = D["rail_h"]; PX = XF + 0.03
lz0, lz1 = L["top"][0] - L["w"] / 2 - 0.08, L["top"][0] + L["w"] / 2 + 0.08            # the ladder's x span on the +z side
posts = [(X1 - 0.05, Z0 + 0.05), (X1 - 0.05, ZC), (X1 - 0.05, Z1 - 0.05), (PX + 0.05, Z0 + 0.05), (PX + 0.05, Z1 - 0.05), (lz1, Z1 - 0.05), (lz0, Z1 - 0.05)]
for px, pz in posts:
    timber.box(px - 0.04, px + 0.04, DY, DY + RH, pz - 0.04, pz + 0.04)
for yy, hh in ((DY + RH - 0.05, 0.05), (DY + RH * 0.45, 0.04)):
    timber.box(X1 - 0.07, X1 - 0.03, yy, yy + hh, Z0 + 0.01, Z1 - 0.01)                      # front
    timber.box(PX, X1 - 0.07, yy, yy + hh, Z0 + 0.03, Z0 + 0.07)                             # -z side
    timber.box(PX, lz0 - 0.04, yy, yy + hh, Z1 - 0.07, Z1 - 0.03)                            # +z side, ladder gap
    timber.box(lz1 + 0.04, X1 - 0.07, yy, yy + hh, Z1 - 0.07, Z1 - 0.03)

# ---------------------------------------------------------------- cabin: flared front/back, leaning sides, shed roof
bw, ew = C["base_w"], C["eave_w"]
hw = lambda hh: bw / 2 + (ew - bw) / 2 * hh / HF                                          # half width at height hh above the deck
roof_h = lambda x: HB + (HF - HB) * (x - XB) / (XF - XB)
OV = 0.0125                                                                                # corners overlap half a board (nothing coplanar)
door, wins = C["door"], C["windows"]
fh = [(door["z"][0] - ZC, door["z"][1] - ZC, 0.0, door["h"])] + [(w_["z"][0] - ZC, w_["z"][1] - ZC, w_["y"][0], w_["y"][1]) for w_ in wins if w_["wall"] == "front"]
# front (x = XF, outward +x): u = z - ZC
wall(lambda u, v: (XF, DY + v, ZC + u), (1, 0, 0),
     [lambda p: hw(p[1]) + OV - p[0], lambda p: p[0] + hw(p[1]) + OV], (-ew / 2 - 0.1, ew / 2 + 0.1), fh, HF)
# back (x = XB, outward -x)
wall(lambda u, v: (XB, DY + v, ZC + u), (-1, 0, 0),
     [lambda p: hw(p[1]) + OV - p[0], lambda p: p[0] + hw(p[1]) + OV], (-ew / 2 - 0.1, ew / 2 + 0.1), [], HB)
# sides (lean out with the flare): u = x
lean = (ew - bw) / 2 / HF
for sgn in (-1, 1):
    sh = [(w_["x"][0], w_["x"][1], w_["y"][0], w_["y"][1]) for w_ in wins if w_["wall"] == ("side_pz" if sgn > 0 else "side_mz")]
    wall(lambda u, v, s=sgn: (u, DY + v, ZC + s * hw(v)), norm((0.0, -lean, float(sgn))),
         [lambda p: roof_h(p[0]) - p[1]], (XB - OV, XF + OV), sh, HF)
# window and door trim (rough 1x4 casings, film 11102 shows plain board frames)
for (u0, u1, h0, h1) in fh:
    for a, b, c0, c1 in ((u0 - 0.07, u0, h0, h1), (u1, u1 + 0.07, h0, h1), (u0 - 0.07, u1 + 0.07, h1, h1 + 0.07)) + (((u0 - 0.07, u1 + 0.07, h0 - 0.06, h0),) if h0 > 0 else ()):
        timber.box(XF + 0.03, XF + 0.05, DY + c0, DY + c1, ZC + a, ZC + b)
# shed roof: one board deck sloping to the back, overhanging, trunk passing through
ov = C["roof_over"]
ra, rb = (XF + ov, DY + roof_h(XF + ov) + 0.02), (XB - ov, DY + roof_h(XB - ov) + 0.02)
zr0, zr1 = ZC - ew / 2 - ov, ZC + ew / 2 + ov
prism(roof, [(ra[0], ra[1], zr0), (rb[0], rb[1], zr0), (rb[0], rb[1], zr1), (ra[0], ra[1], zr1)], (0, 0.045, 0))
for zz in (zr0, zr1 - 0.025):                                                              # fascia boards
    timber.box(XB - ov, XF + ov, min(ra[1], rb[1]) - 0.12, max(ra[1], rb[1]) - 0.02, zz, zz + 0.025)

# ---------------------------------------------------------------- trunk, branch stubs, braces, posts, slats
th = K["top_above_grade"]
prof = [(0.0, K["r_base"]), (0.35, K["r_base"] * 0.85), (0.9, K["r"] * 1.12), (2.5, K["r"] * 1.03), (6.0, K["r"]), (9.0, K["r"] * 0.78), (th, 0.10)]
bark.lathe(TX, TZ, G - 0.15, [(h + (0.15 if i else 0.0), r) for i, (h, r) in enumerate(prof)], 24)
def limb(p0, d, ln, r, depth):
    """a tapering branch from p0 along d (unit), splitting into smaller ones (film 6810: a mature bare tree over the cabin)"""
    n = 3; pts = [p0]
    for k in range(1, n + 1):
        q = add(pts[-1], mul(d, ln / n)); q = (q[0] + random.uniform(-0.1, 0.1) * ln / n, q[1] + random.uniform(-0.05, 0.1) * ln / n, q[2] + random.uniform(-0.1, 0.1) * ln / n)
        tube(bark, [pts[-1], q], max(r * (1 - 0.25 * k), 0.015), 6); pts.append(q)
    if depth:
        for j in range(random.choice((2, 3))):
            a = random.uniform(0, 2 * math.pi); dd = norm(add(d, (0.7 * math.cos(a), random.uniform(0.1, 0.5), 0.7 * math.sin(a))))
            limb(pts[random.choice((1, 2))], dd, ln * random.uniform(0.45, 0.65), r * 0.5, depth - 1)


ga = math.radians(137.5)
for i in range(8):                                                                         # limbs above the roof, round the trunk
    y0 = DY + HF + 0.6 + i * 0.8; a = i * ga + 0.4
    rr = K["r"] * (0.55 - 0.03 * i); up_ = random.uniform(0.6, 1.1)
    d = norm((math.cos(a), up_, math.sin(a)))
    limb((TX + math.cos(a) * K["r"] * 0.5, y0, TZ + math.sin(a) * K["r"] * 0.5), d, random.uniform(3.0, 4.5) * (1 - 0.06 * i), rr, 2)
yb = DY - 2.2                                                                              # braces from the trunk to the deck's corners (6810, 11060)
for cx_, cz_ in ((X0 + 0.15, Z0 + 0.15), (X0 + 0.15, Z1 - 0.15), (X1 - 0.3, Z0 + 0.15), (X1 - 0.3, Z1 - 0.15)):
    d = norm((cx_ - TX, 0.0, cz_ - TZ))
    beam(timber, (TX + d[0] * (K["r"] + 0.03), yb, TZ + d[2] * (K["r"] + 0.03)), (cx_, DY - 0.03 - JD, cz_), 0.05, 0.14, up=(-d[2], 0.0, d[0]))
for pz in (Z0 + 0.12, Z1 - 0.12):                                                          # porch posts to the ground (11102)
    timber.box(X1 - 0.16, X1 - 0.07, G - 0.1, DY - 0.03 - JD, pz - 0.045, pz + 0.045)
for k in range(8):                                                                         # slats nailed up the trunk (6810), facing the ladder
    y = G + 1.2 + 0.3 * k
    if y > DY - JD - 0.4: break
    timber.box(TX - 0.2, TX + 0.2, y, y + 0.07, TZ + K["r"] * 1.1, TZ + K["r"] * 1.1 + 0.025)

# ---------------------------------------------------------------- ladder (leaning on the porch's +z rim)
(lx, lzf), (_, lzt) = L["foot"], L["top"]
ytop = DY + 0.7
for s in (-1, 1):
    beam(ladder, (lx + s * L["w"] / 2, G - 0.02, lzf), (lx + s * L["w"] / 2, ytop, lzt), 0.035, 0.075, up=(0.0, 0.0, 1.0))
LL = math.dist((G, lzf), (ytop, lzt)); nr = int(LL / 0.305)
for k in range(1, nr + 1):
    f = k * 0.305 / LL
    yy, zz = G + (ytop - G) * f, lzf + (lzt - lzf) * f
    tube(ladder, [(lx - L["w"] / 2, yy, zz), (lx + L["w"] / 2, yy, zz)], 0.016, 8)

# ---------------------------------------------------------------- flag, bulb
fx_, fz_ = T["flag"]["pole"]; fh_ = T["flag"]["h"]
pole.lathe(fx_, fz_, DY, [(0.0, 0.025), (fh_, 0.02)], 8)
for s in (1, -1):                                                                          # two faces (the cloth seen from both sides)
    pts = [(fx_, DY + fh_ - 0.05, fz_), (fx_, DY + fh_ - 0.65, fz_), (fx_ - 0.05, DY + fh_ - 0.70, fz_ - 0.88), (fx_ - 0.02, DY + fh_ - 0.08, fz_ - 0.9)]
    flag.face([add(p, (s * 0.002, 0, 0)) for p in pts], (s, 0, 0))
bx, bz = XF - 0.25, ZC + 0.1
holder.lathe(bx, bz, DY + roof_h(bx) - 0.12, [(0.0, 0.03), (0.08, 0.035), (0.10, 0.05), (0.12, 0.05)], 12)
bulb.lathe(bx, bz, DY + roof_h(bx) - 0.25, [(0.0, 0.01), (0.03, 0.03), (0.07, 0.032), (0.11, 0.015), (0.13, 0.013)], 12)

# ---------------------------------------------------------------- the rope's fixed parts
oct8 = 0.5 * R["d"]
tie, edge, win, tk = R["tie"], R["ceiling_edge"], R["window"], R["trunk"]
for k in range(3):                                                                         # loops round the collar tie (10922; the tie runs along x)
    x = tie[0] - 0.03 + 0.03 * k
    tube(rope, [(x + 0.002 * i, tie[1] - 0.08 + 0.09 * math.sin(a), tie[2] + 0.04 * math.cos(a)) for i, a in enumerate([i * math.pi / 6 for i in range(13)])], oct8, 6)
tube(rope, [(tie[0] + 0.03, tie[1] - 0.08, tie[2] - 0.045), tuple(edge), tuple(win)], oct8, 6)
for k in range(4):                                                                         # turns round the trunk (11220)
    yy = tk[1] - 0.06 + 0.035 * k; rr = K["r"] * 1.03 + 0.012
    tube(rope, [(TX + rr * math.cos(a), yy + 0.035 * a / (2 * math.pi), TZ + rr * math.sin(a)) for a in [i * math.pi / 8 for i in range(17)]], oct8, 6)

# ---------------------------------------------------------------- trolley at the origin (rope contact), running toward -x
bar, block, grips = trolley
block.box(-0.07, 0.07, -0.13, 0.015, -0.025, 0.025)                                       # pulley block cheeks round the rope
bar.sweep([(0.0, -0.13, 0.0), (0.0, -0.22, 0.0)], [(0.012 * math.cos(a), 0.012 * math.sin(a)) for a in [i * math.pi / 4 for i in range(8)]])   # stem
path = [(0.0, -0.20, -0.32), (0.0, -0.17, -0.22), (0.05, -0.22, -0.08), (0.05, -0.22, 0.08), (0.0, -0.17, 0.22), (0.0, -0.20, 0.32)]   # chrome BMX bar
tube(bar, path, 0.011, 10)
for s in (-1, 1):
    tube(grips, [(0.0, -0.20, s * 0.26), (0.0, -0.205, s * 0.36)], 0.016, 10)
    for i, part in enumerate(streamers):                                                   # streamers from the bar ends (11056)
        z = s * (0.365 + 0.006 * i)
        o = 0.012 * (i - 1)
        prism(part, [(o, -0.20, z), (o, -0.20, z + s * 0.012), (o + 0.03, -0.55 - 0.05 * i, z + s * 0.03), (o + 0.03, -0.55 - 0.05 * i, z + s * 0.018)], (0.003, 0, 0))
# a kid-sized rider stand-in (1.37 m) hanging from the grips: shown only in the demo / third-person views
sweater, pants, skin, hair, shoes = rider
hy = -0.20                                                                                 # hands on the grips
skin.lathe(0, 0.31, hy, [(0.0, 0.035), (0.10, 0.035)], 8); skin.lathe(0, -0.31, hy, [(0.0, 0.035), (0.10, 0.035)], 8)    # hands
for s in (-1, 1):
    tube(sweater, [(0.0, hy - 0.05, s * 0.30), (0.02, hy - 0.30, s * 0.24), (0.02, hy - 0.52, s * 0.17)], 0.045, 8)        # arms up
sweater.lathe(0.02, 0.0, hy - 0.98, [(0.0, 0.14), (0.20, 0.15), (0.40, 0.16), (0.46, 0.10)], 12)                          # torso
skin.lathe(0.02, 0.0, hy - 0.54, [(0.0, 0.05), (0.06, 0.06), (0.16, 0.095), (0.24, 0.085)], 12)                          # neck + face
hair.lathe(0.0, 0.0, hy - 0.33, [(0.0, 0.098), (0.06, 0.07), (0.09, 0.03)], 12)
for s in (-1, 1):
    tube(pants, [(0.02, hy - 0.98, s * 0.07), (0.10, hy - 1.30, s * 0.08), (0.16, hy - 1.58, s * 0.09)], 0.06, 8)       # legs, knees up a little
    shoes.box(0.10, 0.28, hy - 1.66, hy - 1.58, s * 0.09 - 0.05, s * 0.09 + 0.05)

# ---------------------------------------------------------------- export
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob)
coll = bpy.data.collections.new("Treehouse"); bpy.context.scene.collection.children.link(coll)
mats = {n: material(n, c, r) for n, c, r in (
    ("TH_Board", (0.42, 0.40, 0.36), 0.9), ("TH_Board2", (0.30, 0.28, 0.25), 0.9), ("TH_Timber", (0.36, 0.32, 0.27), 0.9),
    ("TH_Bark", (0.25, 0.22, 0.19), 0.95), ("TH_Roof", (0.12, 0.12, 0.12), 0.9), ("TH_Rope", (0.62, 0.50, 0.32), 0.95),
    ("TH_Ladder", (0.30, 0.25, 0.19), 0.9), ("TH_Flag", (0.03, 0.03, 0.04), 0.9), ("TH_Bulb", (1.0, 0.95, 0.85), 0.1),
    ("TH_Porcelain", (0.9, 0.89, 0.86), 0.3), ("TH_Chrome", (0.85, 0.86, 0.88), 0.1), ("TH_Steel", (0.35, 0.36, 0.38), 0.4),
    ("TH_Grip", (0.05, 0.05, 0.05), 0.8), ("TH_Streamer0", (0.85, 0.12, 0.15), 0.8), ("TH_Streamer1", (0.95, 0.85, 0.15), 0.8),
    ("TH_Streamer2", (0.15, 0.35, 0.85), 0.8), ("TH_Sweater", (0.50, 0.04, 0.06), 0.95), ("TH_Pants", (0.20, 0.22, 0.14), 0.95),
    ("TH_Skin", (0.85, 0.66, 0.55), 0.7), ("TH_Hair", (0.80, 0.65, 0.35), 0.8), ("TH_Shoes", (0.30, 0.20, 0.12), 0.8))}
root = bpy.data.objects.new("Treehouse_HiFi", None); coll.objects.link(root)
for p in boards + [timber, bark, roof, rope, ladder, flag, pole, bulb, holder] + trolley + streamers + rider:
    if p.f:
        p.build(coll, mats).parent = root
OUT.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(OUT), export_format="GLB", use_selection=False, export_apply=True)
print("hifi_treehouse: wrote", OUT, "deck top", round(DY, 3), "deck x", round(X0, 2), round(X1, 2), "z", round(Z0, 2), round(Z1, 2))
