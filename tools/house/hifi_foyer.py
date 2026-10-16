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

# ---------------------------------------------------------------- mesh building in spec coordinates
class Part:
    def __init__(self, name, mat):
        self.name, self.mat, self.v, self.f = name, mat, [], []

    def quad(self, a, b, c, d):            # counter-clockwise seen from outside (spec space)
        i = len(self.v); self.v += [a, b, c, d]; self.f.append((i, i + 1, i + 2, i + 3))

    def poly(self, pts):
        i = len(self.v); self.v += list(pts); self.f.append(tuple(range(i, i + len(pts))))

    def box(self, x0, x1, y0, y1, z0, z1):
        P = lambda x, y, z: (x, y, z)
        self.quad(P(x0, y1, z0), P(x0, y1, z1), P(x1, y1, z1), P(x1, y1, z0))   # top
        self.quad(P(x0, y0, z0), P(x1, y0, z0), P(x1, y0, z1), P(x0, y0, z1))   # bottom
        self.quad(P(x0, y0, z0), P(x0, y0, z1), P(x0, y1, z1), P(x0, y1, z0))   # -x
        self.quad(P(x1, y0, z0), P(x1, y1, z0), P(x1, y1, z1), P(x1, y0, z1))   # +x
        self.quad(P(x0, y0, z0), P(x0, y1, z0), P(x1, y1, z0), P(x1, y0, z0))   # -z
        self.quad(P(x0, y0, z1), P(x1, y0, z1), P(x1, y1, z1), P(x0, y1, z1))   # +z

    def lathe(self, cx, cz, y0, prof, n=20):
        """Turned part: prof = [(height above y0, radius)], bottom to top, about a vertical axis at (cx, cz)."""
        rings = []
        for h, r in prof:
            rings.append([(cx + r * math.cos(2 * math.pi * k / n), y0 + h, cz + r * math.sin(2 * math.pi * k / n)) for k in range(n)])
        for a, b in zip(rings, rings[1:]):
            for k in range(n):
                k2 = (k + 1) % n
                self.quad(a[k], b[k], b[k2], a[k2])
        self.poly(list(reversed(rings[0]))); self.poly(rings[-1])

    def sweep(self, path, prof):
        """A profile [(across, up)] swept along a 3D polyline (handrail); 'across' is horizontal, perpendicular to the path."""
        rings = []
        for i, p in enumerate(path):
            a, b = path[max(i - 1, 0)], path[min(i + 1, len(path) - 1)]
            t = [b[0] - a[0], b[1] - a[1], b[2] - a[2]]; L = math.sqrt(sum(c * c for c in t)); t = [c / L for c in t]
            side = [-t[2], 0.0, t[0]]; Ls = math.hypot(side[0], side[2]); side = [side[0] / Ls, 0, side[2] / Ls]
            up = [t[1] * side[2] - t[2] * side[1], t[2] * side[0] - t[0] * side[2], t[0] * side[1] - t[1] * side[0]]
            rings.append([tuple(p[j] + u * side[j] + w * up[j] for j in range(3)) for u, w in prof])
        n = len(prof)
        for a, b in zip(rings, rings[1:]):
            for k in range(n):
                k2 = (k + 1) % n
                self.quad(a[k], a[k2], b[k2], b[k])
        self.poly(list(reversed(rings[0]))); self.poly(rings[-1])

    def build(self, coll):
        to_b = lambda p: (-p[0], p[2], p[1])                    # spec -> Blender (see module doc)
        me = bpy.data.meshes.new(self.name)
        me.from_pydata([to_b(p) for p in self.v], [], [tuple(reversed(f)) for f in self.f])
        me.update(); me.validate()
        ob = bpy.data.objects.new(self.name, me); coll.objects.link(ob)
        ob.data.materials.append(MATS[self.mat])
        for poly in me.polygons:
            poly.use_smooth = False
        return ob


def material(name, rgb, rough):
    m = bpy.data.materials.new(name); m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]; bsdf.inputs["Base Color"].default_value = (*rgb, 1.0); bsdf.inputs["Roughness"].default_value = rough
    return m


# colours sampled from Marina's frames (spec/dressing/foyer.json) where they exist
DRESS = json.loads((ROOT / "spec/dressing/foyer.json").read_text())["colours"]
MATS = {"Stair_TreadWood": material("Stair_TreadWood", DRESS["rail"], 0.35), "Stair_White": material("Stair_White", (0.86, 0.86, 0.84), 0.5),
        "Stair_Runner": material("Stair_Runner", DRESS["runner"], 0.9), "Stair_RailWood": material("Stair_RailWood", DRESS["rail"], 0.3)}

# ---------------------------------------------------------------- the stair
TREAD_T, NOSE = 0.025, 0.025                 # tread thickness, nosing overhang (authored: standard 1 in tread, 1 in nosing)
tread, white, runner, rail = Part("Treads", "Stair_TreadWood"), Part("RisersStringers", "Stair_White"), Part("Runner", "Stair_Runner"), Part("Rail", "Stair_RailWood")
bal = Part("Balusters", "Stair_White"); newel = Part("Newels", "Stair_RailWood")


def nosing(part, x_front, y_top, z0, z1, dirx):
    """Half-round nosing along z at the tread's front edge; dirx = +1 if the front faces +x."""
    r = TREAD_T / 2; yc = y_top - r; n = 8
    pts = [(x_front + dirx * r * math.sin(math.pi * k / n), yc + r * math.cos(math.pi * k / n)) for k in range(n + 1)]
    for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
        if dirx > 0:
            part.quad((xa, ya, z0), (xa, ya, z1), (xb, yb, z1), (xb, yb, z0))
        else:
            part.quad((xa, ya, z0), (xb, yb, z0), (xb, yb, z1), (xa, ya, z1))


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
        runner.box(xa + 0.01, xb - 0.01, y1, y1 + 0.006, ra, rb)
        runner.box(front + (0 if dirx > 0 else -0.006), front + (0.006 if dirx > 0 else 0), y1 - RISE, y1, ra, rb)
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
    white.poly([(x, y, z_face) for x, y in poly] if dirx * outward > 0 else [(x, y, z_face) for x, y in reversed(poly)])
    white.poly([(x, y, zb) for x, y in reversed(poly)] if dirx * outward > 0 else [(x, y, zb) for x, y in poly])
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
runner.box(lx0 + 0.15, lx1 - 0.15, ly1, ly1 + 0.006, lz0 + 0.15, lz1 - 0.15)

# wall-side skirt board along flight 1 (Marina 193.5 s, film 2677: a white board following the pitch on the wall): through the
# nosings, 0.30 m tall, 2 cm proud of the wall (z 11.43)
WALL_FACE = 11.43   # the stair wall's visible face (probe: a wall layer z 11.43-11.50 runs up beside the flight)
nos = [(b["x"][1] + NOSE, b["y"][1], WALL_FACE - 0.011) for b in f1]
nos = [(nos[0][0] + (nos[0][0] - nos[1][0]), nos[0][1] - (nos[1][1] - nos[0][1]), nos[0][2])] + nos
white.sweep(nos, [(-0.011, -0.10), (0.011, -0.10), (0.011, 0.20), (-0.011, 0.20)])

# the wall under flight 1's open side (Marina 193.5 s): wallpaper between the stringer's bottom edge and a white wainscot
# (0.705 m, foyer.json) with a cap; one plane 1 cm proud of the open side, over the flight only (the landing has its wall)
spand, wains = Part("Spandrel", "Stair_Spandrel"), Part("Wainscot", "Stair_White")
WAIN = json.loads((ROOT / "spec/dressing/foyer.json").read_text())["walls"]["wainscot_m"]
zf, y_floor = 10.21 - 0.012, B["flight1_step01"]["y"][0]
xa1, xb1 = B["flight1_step12"]["x"][0], B["flight1_step01"]["x"][1]
wains.quad((xa1, y_floor, zf), (xa1, y_floor + WAIN, zf), (xb1, y_floor + WAIN, zf), (xb1, y_floor, zf))
xs_ = [xa1 + (xb1 - xa1) * k / 40 for k in range(41)]
ptop = [(x, bot1(x)) for x in xs_ if bot1(x) > y_floor + WAIN + 0.005]
if ptop:
    poly = [(ptop[0][0], y_floor + WAIN)] + ptop + [(ptop[-1][0], y_floor + WAIN)]
    spand.poly([(x, y, zf) for x, y in poly])
wains.box(xa1, xb1, y_floor + WAIN - 0.01, y_floor + WAIN + 0.03, zf - 0.02, zf)   # wainscot cap
# the stair wall (z 11.43): a raking white wainscot from the skirt board up to a chair rail 0.705 m above the nosing line
# (film 2677, Marina 1070.5 s)
noseL = sorted([(b["x"][1] + NOSE, b["y"][1]) for b in f1])
zw = WALL_FACE - 0.004
for (xa, ya), (xb, yb) in zip(noseL, noseL[1:]):
    wains.quad((xa, ya + 0.20, zw), (xa, ya + WAIN, zw), (xb, yb + WAIN, zw), (xb, yb + 0.20, zw))
    wains.quad((xa, ya + 0.20, zw), (xb, yb + 0.20, zw), (xb, yb + WAIN, zw), (xa, ya + WAIN, zw))   # both faces (winding-proof)
rk = [(x, y + WAIN + 0.015, WALL_FACE - 0.015) for x, y in noseL]
white.sweep(rk, [(-0.015, -0.02), (0.015, -0.02), (0.015, 0.02), (-0.015, 0.02)])


# handrail: through the cap tops' midpoints, one continuous run per flight, plus the landing's run
def cap_line(prefix):
    caps = sorted((b for n, b in B.items() if n.startswith(prefix) and n.endswith("_cap")), key=lambda b: b["name"])
    return [((b["x"][0] + b["x"][1]) / 2, (b["y"][0] + b["y"][1]) / 2, (b["z"][0] + b["z"][1]) / 2) for b in caps]

p1 = cap_line("flight1_rail"); p2 = cap_line("flight2_rail")
step_x = abs(p1[1][0] - p1[0][0]); dy = p1[1][1] - p1[0][1]
p1 = p1 + [(p1[-1][0] - step_x / 2, p1[-1][1] + dy / 2, p1[-1][2])]   # from the bullnose newel (over the first cap) into the landing newel
rail.sweep(p1, RAIL_PROF)
lc = B["landing_rail_cap"]; ly = (lc["y"][0] + lc["y"][1]) / 2; lx = (lc["x"][0] + lc["x"][1]) / 2
rail.sweep([(lx, ly, lc["z"][1]), (lx, ly, lc["z"][0])], RAIL_PROF)
dy2 = p2[1][1] - p2[0][1]; sx2 = abs(p2[1][0] - p2[0][0])
p2 = [(p2[0][0] - sx2, p2[0][1] - dy2, p2[0][2])] + p2
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
for n, b in B.items():
    if b["kind"] == "rail" and "spindle" in n:
        cx, cz = (b["x"][0] + b["x"][1]) / 2, (b["z"][0] + b["z"][1]) / 2
        if n.startswith("flight1"):
            top = rail_y(p1, cx) - RAIL_BOTTOM
        elif n.startswith("flight2"):
            top = rail_y(p2, cx) - RAIL_BOTTOM
        else:
            top = ly - RAIL_BOTTOM
        baluster(cx, cz, b["y"][0], top - b["y"][0])

# the bottom step's bullnose (film 2677, Marina 193.5 s: the first step rounds out past the open side under the newel), replacing
# the dressing's square box (user note 23:26: "the first riser extends awkwardly")
b1 = B["flight1_step01"]; (bx0, bx1), (by0, by1), (bz0, bz1) = b1["x"], b1["y"], b1["z"]
BN_C, BN_R = ((bx0 + bx1) / 2, bz0), (bx1 - bx0) / 2
arc = [(BN_C[0] + BN_R * math.cos(math.pi * k / 16), BN_C[1] - BN_R * math.sin(math.pi * k / 16)) for k in range(17)]   # front -> back via -z
for (xa, za), (xb, zb) in zip(arc, arc[1:]):
    white.quad((xa, by0, za), (xa, by1 - TREAD_T, za), (xb, by1 - TREAD_T, zb), (xb, by0, zb))
cap = [(x, z) for x, z in arc]
tread.poly([(x, by1, z) for x, z in reversed(cap)])                       # top, facing up
tread.poly([(x, by1 - TREAD_T, z) for x, z in cap])                       # underside
for (xa, za), (xb, zb) in zip(cap, cap[1:]):                              # tread edge round the arc
    tread.quad((xa, by1 - TREAD_T, za), (xa, by1, za), (xb, by1, zb), (xb, by1 - TREAD_T, zb))
NEWEL1 = (BN_C[0], bz0 - BN_R * 0.45)

# newels: the foot of flight 1, the landing corner, the foot of flight 2 (grey-box rail ends)
y_floor = B["flight1_step01"]["y"][0]
newel_post(NEWEL1[0], NEWEL1[1], by1, p1[0][1] - by1 + 0.20)
newel_post(lx, 10.20, ly1, ly - ly1 + 0.20)
newel_post(lx, 9.20, ly1 - 0.0, p2[0][1] - ly1 + 0.20)

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
    p.build(coll).parent = root
OUT.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(OUT), export_format="GLB", export_yup=True, export_apply=True)
print("wrote", OUT, {p.name: len(p.f) for p in (tread, white, runner, rail, bal, newel, spand, wains)})
