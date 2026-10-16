"""hifi_foyer: the foyer's main stair as a detailed model (Blender, headless), built from the same spec the grey-box uses.

Why (Oct 15, user: "let's do the foyer visual upgrade"): the grey-box stays as the invisible walking/collision layer (its gates are
unchanged); this script writes the look over it: dark wood treads with a rounded nosing, white risers, a white cut stringer on the
open side, white turned balusters on square blocks, a continuous dark handrail and turned dark newels (Marina 193.5 s, 1070.5 s).
Every position comes from spec/house_spec.json "stair" boxes (steps, landing, spindles, rail caps); only profiles are authored.

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P tools/house/hifi_foyer.py
  -> unity/HomeAlone/Assets/Models/Foyer/MainStair.glb   (SpecGreybox.HiFi places it and hides the grey-box stair's renderers)

Coordinates: spec (x, y up, z) -> Unity (x, y, -z). glTF export (+Y up) and glTFast (x mirrored) give Unity = (-bx, bz, -by), so a
spec point goes to Blender (-x, z, y). That map is a reflection, so every face is wound reversed on the way.
"""
import json
import math
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "unity/HomeAlone/Assets/Models/Foyer/MainStair.glb"
S = json.loads((ROOT / "spec/house_spec.json").read_text())["stair"]
B = {b["name"]: b for b in S["boxes"]}
RISE = S["rise_m"]

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from hifi_lib import Part, material   # noqa: E402

# colours sampled from Marina's frames (spec/dressing/foyer.json) where they exist
DRESS = json.loads((ROOT / "spec/dressing/foyer.json").read_text())["colours"]
MATS = {"Stair_TreadWood": material("Stair_TreadWood", DRESS["rail"], 0.35), "Stair_White": material("Stair_White", (0.86, 0.86, 0.84), 0.5),
        "Stair_Runner": material("Stair_Runner", DRESS["runner"], 0.9), "Stair_RailWood": material("Stair_RailWood", DRESS["rail"], 0.3)}

# ---------------------------------------------------------------- the stair
TREAD_T, NOSE = 0.025, 0.025                 # tread thickness, nosing overhang (authored: standard 1 in tread, 1 in nosing)
CARPET = 0.01                                 # runner thickness: 1 cm, the z-fight gate's minimum offset (carpet is ~1 cm)
tread, white, runner, rail = Part("Treads", "Stair_TreadWood"), Part("RisersStringers", "Stair_White"), Part("Runner", "Stair_Runner"), Part("Rail", "Stair_RailWood")
bal = Part("Balusters", "Stair_White"); newel = Part("Newels", "Stair_RailWood")


def nosing(part, x_front, y_top, z0, z1, dirx):
    """Half-round nosing along z at the tread's front edge; dirx = +1 if the front faces +x."""
    r = TREAD_T / 2; yc = y_top - r; n = 8
    pts = [(x_front + dirx * r * math.sin(math.pi * k / n), yc + r * math.cos(math.pi * k / n)) for k in range(n + 1)]
    for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
        part.face([(xa, ya, z0), (xa, ya, z1), (xb, yb, z1), (xb, yb, z0)], ((xa + xb) / 2 - x_front, (ya + yb) / 2 - yc, 0))


def flight(prefix, dirx, open_z, runner_inset=0.15):
    """Steps named prefix01..: each a tread slab (front edge proud by NOSE, rounded), a white riser under its front, a runner."""
    steps = sorted((b for n, b in B.items() if n.startswith(prefix) and b["kind"] == "step"), key=lambda b: b["name"])
    for b in steps:
        (x0, x1), (_, y1), (z0, z1) = b["x"], b["y"], b["z"]
        front = x1 if dirx > 0 else x0
        xa, xb = (x0, x1 + NOSE - TREAD_T / 2) if dirx > 0 else (x0 - NOSE + TREAD_T / 2, x1)
        tread.box(xa, xb, y1 - TREAD_T, y1, z0, z1)
        nosing(tread, xb if dirx > 0 else xa, y1, z0, z1, dirx)
        white.box(front - 0.02 if dirx > 0 else front, front if dirx > 0 else front + 0.02, y1 - RISE, y1 - TREAD_T, z0, z1)   # riser
        ra, rb = z0 + runner_inset, z1 - runner_inset                                    # carpet runner on tread and riser
        if open_z is not None:
            ra, rb = (z0 + runner_inset, z1 - runner_inset)
        runner.box(xa + 0.01, xb - 0.01, y1, y1 + CARPET, ra, rb)
        runner.box(front + (0 if dirx > 0 else -CARPET), front + (CARPET if dirx > 0 else 0), y1 - RISE, y1 + CARPET, ra, rb)
    return steps


def stringer(steps, dirx, z_face, outward, depth=0.25):
    """White cut stringer on the open side: one board, stepped top (risers and treads), a straight bottom edge parallel to the
    pitch 'depth' below the nosing line, clipped at the floor; a front face at z_face and a back face 2 cm in (user note 23:26:
    per-step boxes stepped its bottom edge)."""
    st = sorted(steps, key=lambda b: b["y"][1])                     # bottom step first
    top = []
    for b in st:
        (x0, x1), (_, y1) = b["x"], b["y"]
        front, back = (x1, x0) if dirx > 0 else (x0, x1)
        top += [(front, y1 - RISE), (front, y1 - TREAD_T), (back, y1 - TREAD_T)]
    yf = st[0]["y"][0]
    slope = RISE / abs(st[0]["x"][1] - st[0]["x"][0])
    xs = [q[0] for q in top]; x_lo, x_hi = (xs[0], xs[-1])
    bot = lambda x: max(yf, (st[0]["y"][1] - depth) + slope * (x - top[0][0]) * (-dirx))
    poly = top + [(x_hi, bot(x_hi))] + [(x_lo, max(bot(x_lo), yf))]
    poly = [(x, max(y, yf)) for x, y in poly]
    zb = z_face - outward * 0.02
    white.face([(x, y, z_face) for x, y in poly], (0, 0, outward))
    white.face([(x, y, zb) for x, y in poly], (0, 0, -outward))
    return bot


def baluster(cx, cz, y0, h):
    """Turned white baluster on a square block (Marina 193.5 s): block 0-0.20, vase, collar, square top 0.06 under the rail."""
    s = 0.0225
    bal.box(cx - s, cx + s, y0, y0 + 0.20, cz - s, cz + s)
    t = h - 0.26
    prof = [(0.20, 0.018), (0.22, 0.022), (0.26, 0.016), (0.20 + 0.30 * t, 0.012), (0.20 + 0.55 * t, 0.019),
            (0.20 + 0.78 * t, 0.013), (0.20 + 0.92 * t, 0.017), (0.20 + t, 0.014)]
    bal.lathe(cx, cz, y0, prof, n=14)
    bal.box(cx - s * 0.8, cx + s * 0.8, y0 + 0.20 + t, y0 + h, cz - s * 0.8, cz + s * 0.8)


def newel_post(cx, cz, y0, h):
    """Turned dark newel (Marina 193.5 s): square base, turned shaft with rings, square cap block, ball finial."""
    s = 0.045
    newel.box(cx - s, cx + s, y0, y0 + 0.45, cz - s, cz + s)
    prof = [(0.45, 0.034), (0.48, 0.042), (0.52, 0.03), (0.75, 0.026), (0.85, 0.036), (0.90, 0.026), (h - 0.30, 0.03), (h - 0.26, 0.04)]
    newel.lathe(cx, cz, y0, prof, n=20)
    newel.box(cx - s, cx + s, y0 + h - 0.26, y0 + h - 0.06, cz - s, cz + s)
    newel.lathe(cx, cz, y0 + h - 0.06, [(0, 0.03), (0.02, 0.04), (0.06, 0.045), (0.10, 0.035), (0.13, 0.0)], n=16)


RAIL_PROF = [(-0.03, -0.035), (0.03, -0.035), (0.035, -0.01), (0.03, 0.01), (0.015, 0.025), (-0.015, 0.025), (-0.03, 0.01), (-0.035, -0.01)]

# flight 1: rises toward -x, open side at z 10.23 (rail band 10.17-10.23), wall at 11.43
f1 = flight("flight1_step", +1, 10.23)
bot1 = stringer(f1, +1, 10.21, -1)
# flight 2: rises toward +x, open side at z 9.17 (rail band 9.17-9.23)
f2 = flight("flight2_step", -1, 9.17)
stringer(f2, -1, 9.16, -1)
for b in f2:   # flight 2 sits on the landing as slabs: their bodies under the treads are white (seen from the foyer below)
    (x0, x1), (y0, y1), (z0, z1) = b["x"], b["y"], b["z"]
    white.box(x0, x1, y0, y1 - TREAD_T, z0, z1)
L = B["landing"]; (lx0, lx1), (_, ly1), (lz0, lz1) = L["x"], L["y"], L["z"]
white.box(lx0, lx1, L["y"][0], ly1 - TREAD_T, lz0, lz1)   # the landing's slab under its tread (fascia and soffit, white)
tread.box(lx0, lx1 + NOSE - TREAD_T / 2, ly1 - TREAD_T, ly1, lz0, lz1); nosing(tread, lx1 + NOSE - TREAD_T / 2, ly1, 9.23, lz1, +1)
runner.box(lx0 + 0.15, lx1 - 0.15, ly1, ly1 + CARPET, lz0 + 0.15, lz1 - 0.15)

# wall-side skirt board along flight 1 (Marina 193.5 s, film 2677: a white board following the pitch on the wall): through the
# nosings, 0.30 m tall, 2 cm proud of the wall (z 11.43)
WALL_FACE = 11.43   # the stair wall's visible face (probe: a wall layer z 11.43-11.50 runs up beside the flight)
# one trim line on the stair wall (user note Oct 16 08:41: the raking wainscot stopped short at both ends): from floor level at
# the foot, up every nosing, then flat across the landing to its back wall; skirt board, raking panel and chair rail follow it,
# so they meet the foyer's flat wainscot at the bottom and continue as the landing's wainscot at the top
LN = B["landing"]
line = sorted(((b["x"][1] + NOSE, b["y"][1]) for b in f1), reverse=True)              # bottom step first
line = [(line[0][0] + (line[0][0] - line[1][0]), line[0][1] - (line[1][1] - line[0][1]))] + line   # floor level
line += [(LN["x"][1] + NOSE, LN["y"][1]), (LN["x"][0] + 0.02, LN["y"][1])]            # landing nosing, landing back wall
white.sweep([(x, y, WALL_FACE - 0.011) for x, y in line[:-1]], [(-0.011, -0.10), (0.011, -0.10), (0.011, 0.20), (-0.011, 0.20)])   # to the landing nosing
white.box(line[-1][0], line[-2][0], LN["y"][1], LN["y"][1] + 0.20, WALL_FACE - 0.022, WALL_FACE)   # on the landing: sits on it (a dip went through the ceiling below)

# the wall under flight 1's open side (Marina 193.5 s): wallpaper between the stringer's bottom edge and a white wainscot
# (0.705 m, foyer.json) with a cap; one plane 1 cm proud of the open side, over the flight only (the landing has its wall)
spand, wains = Part("Spandrel", "Stair_Spandrel"), Part("Wainscot", "Stair_White")
WAIN = json.loads((ROOT / "spec/dressing/foyer.json").read_text())["walls"]["wainscot_m"]
zf, y_floor = 10.21 - 0.012, B["flight1_step01"]["y"][0]
xa1, xb1 = B["flight1_step12"]["x"][0], B["flight1_step01"]["x"][0]   # stops behind the bullnose first step, which rounds out in front of it
xs_ = [xa1 + (xb1 - xa1) * k / 40 for k in range(41)]
# the panel stops at the stringer's underside where the stair is lower than the wainscot (user note 08:40: it rose above the
# bottom treads and the balusters passed through it)
wtop = [(x, min(y_floor + WAIN, bot1(x))) for x in xs_]
wains.face([(xa1, y_floor, zf)] + [(x, y, zf) for x, y in wtop] + [(xb1, y_floor, zf)], (0, 0, -1))   # seen from the foyer
ptop = [(x, bot1(x)) for x in xs_ if bot1(x) > y_floor + WAIN + 0.005]
if ptop:
    poly = [(ptop[0][0], y_floor + WAIN)] + ptop + [(ptop[-1][0], y_floor + WAIN)]
    spand.face([(x, y, zf) for x, y in poly], (0, 0, -1))
xcap = max((x for x in xs_ if bot1(x) >= y_floor + WAIN + 0.03), default=xa1)        # the cap runs only under the stringer's clear part
wains.box(xa1, xcap, y_floor + WAIN - 0.01, y_floor + WAIN + 0.03, zf - 0.02, zf)   # wainscot cap
# the stair wall (z 11.43): a raking white wainscot from the skirt board up to a chair rail 0.705 m above the nosing line
# (film 2677, Marina 1070.5 s)
zw = WALL_FACE - 0.015   # 1.5 cm proud: at 4 mm it z-fought the wallpaper face (user note Oct 16 07:11)
for (xa, ya), (xb, yb) in zip(line, line[1:]):
    wains.face([(xa, ya + 0.20, zw), (xa, ya + WAIN, zw), (xb, yb + WAIN, zw), (xb, yb + 0.20, zw)], (0, 0, -1))   # seen from the foyer
rk = [(x, y + WAIN + 0.015, WALL_FACE - 0.03) for x, y in line]
white.sweep(rk, [(-0.015, -0.02), (0.015, -0.02), (0.015, 0.02), (-0.015, 0.02)])


# the bottom step's bullnose (film 2677, Marina 193.5 s: the first step rounds out past the open side under the newel), replacing
# the dressing's square box (user note 23:26: "the first riser extends awkwardly")
b1 = B["flight1_step01"]; (bx0, bx1), (by0, by1), (bz0, bz1) = b1["x"], b1["y"], b1["z"]
BN_C, BN_R = ((bx0 + bx1) / 2, bz0), (bx1 - bx0) / 2
arc = [(BN_C[0] + BN_R * math.cos(math.pi * k / 16), BN_C[1] - BN_R * math.sin(math.pi * k / 16)) for k in range(17)]   # front -> back via -z
for (xa, za), (xb, zb) in zip(arc, arc[1:]):
    white.face([(xa, by0, za), (xa, by1 - TREAD_T, za), (xb, by1 - TREAD_T, zb), (xb, by0, zb)], ((xa + xb) / 2 - BN_C[0], 0, (za + zb) / 2 - BN_C[1]))
cap = [(x, z) for x, z in arc]
tread.face([(x, by1, z) for x, z in cap], (0, 1, 0))                      # top
tread.face([(x, by1 - TREAD_T, z) for x, z in cap], (0, -1, 0))           # underside
for (xa, za), (xb, zb) in zip(cap, cap[1:]):                              # tread edge round the arc
    tread.face([(xa, by1 - TREAD_T, za), (xa, by1, za), (xb, by1, zb), (xb, by1 - TREAD_T, zb)], ((xa + xb) / 2 - BN_C[0], 0, (za + zb) / 2 - BN_C[1]))
NEWEL1 = (BN_C[0], bz0 - BN_R * 0.45)


# handrail: through the cap tops' midpoints, one continuous run per flight, plus the landing's run
def cap_line(prefix):
    caps = sorted((b for n, b in B.items() if n.startswith(prefix) and n.endswith("_cap")), key=lambda b: b["name"])
    return [((b["x"][0] + b["x"][1]) / 2, (b["y"][0] + b["y"][1]) / 2, (b["z"][0] + b["z"][1]) / 2) for b in caps]

p1 = cap_line("flight1_rail"); p2 = cap_line("flight2_rail")
step_x = abs(p1[1][0] - p1[0][0]); dy = p1[1][1] - p1[0][1]
p1 = p1 + [(p1[-1][0] - step_x / 2, p1[-1][1] + dy / 2, p1[-1][2])]   # from the bullnose newel (over the first cap) into the landing newel
lc = B["landing_rail_cap"]; ly = (lc["y"][0] + lc["y"][1]) / 2; lx = (lc["x"][0] + lc["x"][1]) / 2
NEWELS = [NEWEL1, (lx, 10.20), (lx, 9.20)]   # the foot of flight 1, the landing corner, the foot of flight 2 (grey-box rail ends)
# every rail run ends at a newel's centre: inside the post, never through it and out the far side (clash gate, Oct 16)
p1[-1] = (lx, p1[-1][1], p1[-1][2])
rail.sweep(p1, RAIL_PROF)
rail.sweep([(lx, ly, 10.20), (lx, ly, 9.20)], RAIL_PROF)
dy2 = p2[1][1] - p2[0][1]; sx2 = abs(p2[1][0] - p2[0][0])
p2 = [(lx, p2[0][1] - dy2 * (p2[0][0] - lx) / sx2, p2[0][2])] + p2
rail.sweep(p2, RAIL_PROF)

# balusters: every grey-box spindle position, each ending at the handrail's underside where it stands (the rail slopes: the
# grey-box caps were flat per tread, and baluster tops stuck up through the rail; user note Oct 15 23:18)
def rail_y(line, x):
    pts = sorted(line, key=lambda q: q[0])
    for (xa, ya, _), (xb, yb, _) in zip(pts, pts[1:]):
        if xa <= x <= xb:
            return ya + (yb - ya) * (x - xa) / (xb - xa)
    return pts[0][1] if x < pts[0][0] else pts[-1][1]

RAIL_BOTTOM = 0.035
BAL_S, NEWEL_S = 0.0225, 0.045   # half-widths of the baluster block and the newel base
STEPS = {"flight1": (f1, +1), "flight2": (f2, -1)}
for n, b in B.items():
    if b["kind"] == "rail" and "spindle" in n:
        cx, cz = (b["x"][0] + b["x"][1]) / 2, (b["z"][0] + b["z"][1]) / 2
        if any(abs(cx - nx) < BAL_S + NEWEL_S + 0.01 and abs(cz - nz) < BAL_S + NEWEL_S + 0.01 for nx, nz in NEWELS):
            continue   # a newel stands here
        fl = STEPS.get(n[:7])
        st = next((q for q in fl[0] if q["x"][0] <= cx <= q["x"][1]), None) if fl else None
        y0 = b["y"][0]
        if st:   # clear of the next tread's nosing (it overhangs this tread at the riser behind), standing on the tread
            cx = max(cx, st["x"][0] + NOSE + BAL_S + 0.005) if fl[1] > 0 else min(cx, st["x"][1] - NOSE - BAL_S - 0.005)
            y0 = st["y"][1]
        if n.startswith("flight1"):
            top = rail_y(p1, cx) - RAIL_BOTTOM
        elif n.startswith("flight2"):
            top = rail_y(p2, cx) - RAIL_BOTTOM
        else:
            top = ly - RAIL_BOTTOM
        baluster(cx, cz, y0, top - y0)


# newels (NEWELS above)
newel_post(NEWEL1[0], NEWEL1[1], by1, p1[0][1] - by1 + 0.20)
newel_post(lx, 10.20, ly1, ly - ly1 + 0.20)
newel_post(lx, 9.20, ly1, p2[0][1] - ly1 + 0.20)

# ---------------------------------------------------------------- write
bpy.ops.wm.read_factory_settings(use_empty=True)
for k, m in list(MATS.items()):   # factory reset dropped the materials: rebuild them
    pass
MATS.update({"Stair_TreadWood": material("Stair_TreadWood", DRESS["rail"], 0.35), "Stair_White": material("Stair_White", (0.86, 0.86, 0.84), 0.5),
             "Stair_Runner": material("Stair_Runner", DRESS["runner"], 0.9), "Stair_RailWood": material("Stair_RailWood", DRESS["rail"], 0.3),
             "Stair_Spandrel": material("Stair_Spandrel", DRESS["wallpaper"], 0.8)})
coll = bpy.context.scene.collection
root = bpy.data.objects.new("MainStair_HiFi", None); coll.objects.link(root)
for p in (tread, white, runner, rail, bal, newel, spand, wains):
    p.build(coll, MATS).parent = root
OUT.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(OUT), export_format="GLB", export_yup=True, export_apply=True)
print("wrote", OUT, {p.name: len(p.f) for p in (tread, white, runner, rail, bal, newel, spand, wains)})
