"""hifi_buzz_props: Buzz's hero props (props lane: placed by eye from the film, Marina where the film doesn't show it; real-world sizes;
no change record). One GLB in spec coordinates above the UPPER floor (SpecGreybox.BuzzProps places it at 0).

  the Jordan "Measure Up" poster   film 478/480/524/526: on Buzz's (fake) closet door by the shelves corner (store_props.json
                                   buzz_closet_door, a pack Door_3 leaf, 30 x 80 in, leaf x 7.803-8.565, its room face at z 15.9704),
                                   ruler edge 5 mm in from the latch edge. Sheet 0.735 wide from its own ruler (1 ft = 211 px), bottom
                                   1.2 cm up (the chart's 0 near the floor: the knob reads ~2.9 ft, film 480); the sheet's top 0.14 m is
                                   cut off at the leaf's head (a 2.15 m sheet on a 2.03 m leaf; above Jordan's head)
  the closet door's brass knob     36 in up, 6 cm in from the latch edge, through the poster's yellow ruler strip (film 480/526)
  the corkboard papers             film 530 cut-outs (buzz_props_cork_*.png) pinned (1 cm cards) on the framed corkboard over the desk (the board is
                                   the Sketchfab model, SpecGreybox.Sketchfab.cs: x 8.95-9.85, y 1.15-1.743, front z 15.9813)
  the Bulls wastebasket            film 2720/530, Marina 541/545: on the floor at the chest's desk-side end. 0.40 tall, 0.23-0.25 dia
                                   (film 2720, one ruler: the chest's drawer pitch ~0.24 m; the can spans >= 1.6 drawers, further back)
  the terrarium                    buzz_tank box (buzz.json): black base and rim, four glass panes, soil; the tarantula is the owned
                                   pack's (SpecGreybox.BuzzProps)
  desk                             Poly Haven portable_cassette_player (CC0) lying flat; standing_picture_frame_02 (CC0) with the
                                   girlfriend photo (film 2752) by the poster. (The typewriter is the Fadnn pack's: store_props.json)
  shelf                            Poly Haven baseball_01 (CC0) on board 1 (film 478: a ball in the glove)
  footlocker contents              film 2700/2706/2724/2752, lid closed: Playboy (front right, cover top to +x), four cassette cases
                                   (10.9 x 7 x 1.7 cm, back right), the Crunch Tators bag (centre back), three Pixy Stix, a toilet roll,
                                   a baseball, the girlfriend photo in a silver frame lying flat (back left). Separate objects so the lid
                                   can open later; inside the liner (x 9.207-10.037, z 13.823-14.246, floor 0.016, BuzzTrunk.glb)

Printed faces: spec/dressing/buzz_props_*.png (tools/house/buzz_prop_textures.py). Poly Haven downloads in sfm-work/polyhaven/<id>.

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P tools/house/hifi_buzz_props.py
  -> unity/HomeAlone/Assets/Models/Foyer/BuzzProps.glb
"""
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Euler, Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hifi_lib import Part, material   # noqa: E402
import hifi_pipeline as hp            # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "unity/HomeAlone/Assets/Models/Foyer/BuzzProps.glb"
PH = ROOT / "sfm-work/polyhaven"
TEX = ROOT / "spec/dressing"
BOX = {b["name"]: b for b in json.loads((ROOT / "spec/dressing/buzz.json").read_text())["boxes"]}

bpy.ops.wm.read_factory_settings(use_empty=True)
coll = bpy.context.scene.collection


def tex_material(name, png, rough):
    m = material(name, (1, 1, 1), rough)
    nt = m.node_tree; t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(str(TEX / png)); t.image.pack()
    nt.links.new(t.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"]); return m


M = {"BZP_Black": material("BZP_Black", (0.012, 0.012, 0.012), 0.35), "BZP_Glass": material("BZP_Glass", (0.8, 0.8, 0.8), 0.05),
     "BZP_Soil": material("BZP_Soil", (0.22, 0.13, 0.07), 0.95), "BZP_Paper": material("BZP_Paper", (0.85, 0.85, 0.82), 0.9),
     "BZP_Silver": material("BZP_Silver", (0.75, 0.74, 0.70), 0.3), "BZP_Cassette": material("BZP_Cassette", (0.02, 0.02, 0.022), 0.25),
     "BZP_StixPurple": material("BZP_StixPurple", (0.25, 0.06, 0.40), 0.7), "BZP_StixOrange": material("BZP_StixOrange", (0.85, 0.30, 0.04), 0.7),
     "BZP_StixGreen": material("BZP_StixGreen", (0.10, 0.45, 0.08), 0.7),
     "BZP_Can": tex_material("BZP_Can", "buzz_props_can.png", 0.35), "BZP_Jordan": tex_material("BZP_Jordan", "buzz_props_jordan.png", 0.6),
     "BZP_Playboy": tex_material("BZP_Playboy", "buzz_props_playboy.png", 0.4), "BZP_Photo": tex_material("BZP_Photo", "buzz_props_girlfriend.png", 0.3),
     "BZP_Chips": tex_material("BZP_Chips", "buzz_props_chips.png", 0.55),
     "BZP_Brass": material("BZP_Brass", (0.80, 0.60, 0.28), 0.4)}
M["BZP_Silver"].node_tree.nodes["Principled BSDF"].inputs["Metallic"].default_value = 0.8


def build(part, smooth=False):
    return hp.to_object(part, M[part.mat], coll, hard_deg=30) if smooth else part.build(coll, M)


def box(name, mat, x0, x1, y0, y1, z0, z1):
    p = Part(name, mat); p.box(x0, x1, y0, y1, z0, z1); return build(p)


def printed_box(name, mat, x0, x1, y0, y1, z0, z1, up_uv):
    """a thin box whose top face shows the whole image (up_uv: the image's (u, v) at corners (x0,z0), (x1,z0), (x1,z1), (x0,z1));
    the other faces sample the image's edge"""
    p = Part(name, mat); e = [(0.5, 0.01)] * 4
    p.face([(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)], (0, 1, 0), up_uv)
    p.face([(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)], (0, -1, 0), e)
    p.face([(x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)], (-1, 0, 0), e)
    p.face([(x1, y0, z0), (x1, y0, z1), (x1, y1, z1), (x1, y1, z0)], (1, 0, 0), e)
    p.face([(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)], (0, 0, -1), e)
    p.face([(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], (0, 0, 1), e)
    return build(p)


def tube(p, cx, cz, y0, y1, r0, r1, n, inward=False, uv=None):
    """a vertical wall of n quads, radius r0 at y0 to r1 at y1, facing out (or in); uv(k, n, which) -> per-corner uvs"""
    for k in range(n):
        a0, a1 = 2 * math.pi * k / n, 2 * math.pi * (k + 1) / n
        pts = [(cx + r0 * math.cos(a0), y0, cz + r0 * math.sin(a0)), (cx + r0 * math.cos(a1), y0, cz + r0 * math.sin(a1)),
               (cx + r1 * math.cos(a1), y1, cz + r1 * math.sin(a1)), (cx + r1 * math.cos(a0), y1, cz + r1 * math.sin(a0))]
        am = (a0 + a1) / 2; s = -1 if inward else 1
        p.face(pts, (s * math.cos(am), 0, s * math.sin(am)), uv(k, n) if uv else None)


def annulus(p, cx, cz, y, r_in, r_out, n, up, uv=None):
    for k in range(n):
        a0, a1 = 2 * math.pi * k / n, 2 * math.pi * (k + 1) / n
        pts = [(cx + r_in * math.cos(a0), y, cz + r_in * math.sin(a0)), (cx + r_out * math.cos(a0), y, cz + r_out * math.sin(a0)),
               (cx + r_out * math.cos(a1), y, cz + r_out * math.sin(a1)), (cx + r_in * math.cos(a1), y, cz + r_in * math.sin(a1))]
        p.face(pts, (0, 1 if up else -1, 0), [uv] * 4 if uv else None)


def disc(p, cx, cz, y, r, n, up, uv=None):
    pts = [(cx + r * math.cos(2 * math.pi * k / n), y, cz + r * math.sin(2 * math.pi * k / n)) for k in range(n)]
    p.face(pts, (0, 1 if up else -1, 0), [uv] * n if uv else None)


# ---------------------------------------------------------------- the Jordan poster on the closet door leaf (room face z 15.9704)
LEAF_Z, PH_W, PH_H, P_Y0, P_Y1, P_X1 = 15.9704, 0.735, 2.15, 0.012, 2.022, 8.56   # P_X1: the ruler edge, 5 mm in from the latch edge 8.565
p = Part("BZP_JordanPoster", "BZP_Jordan"); x0, x1, y0, y1, z0, z1 = P_X1 - PH_W, P_X1, P_Y0, P_Y1, LEAF_Z - 0.0044, LEAF_Z + 0.0001
vt = (y1 - y0) / PH_H   # the sheet's top cut at the leaf's head
e = [(0.02, 0.5)] * 4   # the ruler's yellow edge on the sheet's thin sides
# seen from the room (looking +z, spec -x on the right): the image's left (u 0, the ruler) at x1, its right at x0
p.face([(x1, y0, z0), (x0, y0, z0), (x0, y1, z0), (x1, y1, z0)], (0, 0, -1), [(0, 0), (1, 0), (1, vt), (0, vt)])
for pts, n in (([(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)], (0, 1, 0)), ([(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)], (0, -1, 0)),
               ([(x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)], (-1, 0, 0)), ([(x1, y0, z0), (x1, y0, z1), (x1, y1, z1), (x1, y1, z0)], (1, 0, 0)),
               ([(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], (0, 0, 1))):
    p.face(pts, n, e)
build(p)
# the knob through the ruler strip: rose (54 mm, 8 mm), neck, ball knob (56 mm), turned about a horizontal axis toward the room (-z)
KX, KY, KZ = 8.505, 0.914, z0 + 0.0005
p = Part("BZP_ClosetKnob", "BZP_Brass")
prof = [(0.0, 0.027), (0.006, 0.027), (0.008, 0.022), (0.010, 0.009), (0.030, 0.009), (0.034, 0.020), (0.042, 0.027), (0.056, 0.026), (0.066, 0.016), (0.070, 0.0)]
N = 24
ring = lambda d, r: [(KX + r * math.cos(2 * math.pi * k / N), KY + r * math.sin(2 * math.pi * k / N), KZ - d) for k in range(N)]
rings = [ring(d, r) for d, r in prof]
for a, b in zip(rings, rings[1:]):   # every band's true normal leans outward from the axis, so the radial direction orients it
    for k in range(N):
        k2 = (k + 1) % N; am = 2 * math.pi * (k + 0.5) / N
        p.face([a[k], a[k2], b[k]] if b[k] == b[k2] else [a[k], a[k2], b[k2], b[k]], (math.cos(am), math.sin(am), 0))
p.face(rings[0], (0, 0, 1))
build(p, smooth=True)

# ---------------------------------------------------------------- the corkboard's pinned papers (film 530), on the cork face
CK_X0, CK_X1, CK_Y0, CK_Y1, CK_Z = 8.9934, 9.8066, 1.1934, 1.6992, 15.9813
FPX = 740.0   # film px per metre (the film's cork 60..660 px wide across our 0.813 m)
CORK = {"calendar": (1570, 15, 1760, 312), "couple": (1405, 62, 1472, 156), "comic": (1357, 172, 1447, 332),
        "card": (1480, 8, 1568, 128), "bball": (1800, 20, 1860, 192), "idiots": (1764, 203, 1822, 290)}   # buzz_prop_textures.py
for i, (k, (a, b, c, d)) in enumerate(CORK.items()):
    M["BZP_Cork_" + k] = tex_material("BZP_Cork_" + k, f"buzz_props_cork_{k}.png", 0.8)
    xa, xb = CK_X1 - (c - 1260) / FPX, CK_X1 - (a - 1260) / FPX   # film left = spec +x (looking +z)
    ya, yb = CK_Y1 - (d - 8) / FPX, CK_Y1 - (b - 8) / FPX
    ua, ub = (max(xa, CK_X0) - xa) / (xb - xa), (min(xb, CK_X1) - xa) / (xb - xa)   # clipped to the cork, the image cut to match
    va, vb = (max(ya, CK_Y0) - ya) / (yb - ya), (min(yb, CK_Y1) - ya) / (yb - ya)
    xa, xb, ya, yb = max(xa, CK_X0), min(xb, CK_X1), max(ya, CK_Y0), min(yb, CK_Y1)
    # a 1 cm card on the cork (zfight-check rule 2: an overlay stands >= 1 cm proud), its back 0.5 mm into the board; no two overlap
    zf, zb = CK_Z - 0.010, CK_Z + 0.0005
    p = Part("BZP_CorkPaper_" + k, "BZP_Cork_" + k); ed = [((1 - ub + 1 - ua) / 2, (va + vb) / 2)] * 4
    # u runs with film x (spec -x): image left at xb
    p.face([(xb, ya, zf), (xa, ya, zf), (xa, yb, zf), (xb, yb, zf)], (0, 0, -1), [(1 - ub, va), (1 - ua, va), (1 - ua, vb), (1 - ub, vb)])
    for pts, n in (([(xa, yb, zf), (xb, yb, zf), (xb, yb, zb), (xa, yb, zb)], (0, 1, 0)), ([(xa, ya, zf), (xb, ya, zf), (xb, ya, zb), (xa, ya, zb)], (0, -1, 0)),
                   ([(xa, ya, zf), (xa, yb, zf), (xa, yb, zb), (xa, ya, zb)], (-1, 0, 0)), ([(xb, ya, zf), (xb, yb, zf), (xb, yb, zb), (xb, ya, zb)], (1, 0, 0))):
        p.face(pts, n, ed)
    build(p)

# ---------------------------------------------------------------- the Bulls wastebasket
CX, CZ, H, RB, RT, N = 10.97, 14.73, 0.40, 0.115, 0.125, 48
p = Part("BZP_BullsCan", "BZP_Can"); red = (0.5, 0.96)
U0 = -0.25   # turns a panel (u 0.25) to face -x (the room, between the door and the desk views; build 2 had the panels to the walls)
tube(p, CX, CZ, 0.0, H, RB, RT, N, uv=lambda k, n: [(1 - k / n + U0, 0), (1 - (k + 1) / n + U0, 0), (1 - (k + 1) / n + U0, 1), (1 - k / n + U0, 1)])
tube(p, CX, CZ, 0.006, H, RB - 0.004, RT - 0.004, N, inward=True, uv=lambda k, n: [red] * 4)
annulus(p, CX, CZ, H, RT - 0.004, RT, N, True, red)
disc(p, CX, CZ, 0.006, RB - 0.004, N, True, red)
disc(p, CX, CZ, 0.0, RB, N, False, red)
build(p, smooth=True)

# ---------------------------------------------------------------- the terrarium in the buzz_tank box
t = BOX["buzz_tank"]; (tx0, tx1), (ty0, ty1), (tz0, tz1) = t["x"], t["y"], t["z"]
G, BASE, RIM, SOIL = 0.004, 0.02, 0.015, 0.04
box("BZP_TankBase", "BZP_Black", tx0, tx1, ty0, ty0 + BASE, tz0, tz1)
box("BZP_TankSoil", "BZP_Soil", tx0 + 0.01, tx1 - 0.01, ty0 + BASE, ty0 + BASE + SOIL, tz0 + 0.01, tz1 - 0.01)
gy0, gy1 = ty0 + BASE, ty1 - 0.02
box("BZP_TankGlassBack", "BZP_Glass", tx0, tx0 + G, gy0, gy1, tz0, tz1)
box("BZP_TankGlassFront", "BZP_Glass", tx1 - G, tx1, gy0, gy1, tz0, tz1)
box("BZP_TankGlassEndA", "BZP_Glass", tx0 + G, tx1 - G, gy0, gy1, tz0, tz0 + G)
box("BZP_TankGlassEndB", "BZP_Glass", tx0 + G, tx1 - G, gy0, gy1, tz1 - G, tz1)
box("BZP_TankRimBack", "BZP_Black", tx0, tx0 + RIM, gy1, ty1, tz0, tz1)
box("BZP_TankRimFront", "BZP_Black", tx1 - RIM, tx1, gy1, ty1, tz0, tz1)
box("BZP_TankRimEndA", "BZP_Black", tx0 + RIM, tx1 - RIM, gy1, ty1, tz0, tz0 + RIM)
box("BZP_TankRimEndB", "BZP_Black", tx0 + RIM, tx1 - RIM, gy1, ty1, tz1 - RIM, tz1)


# ---------------------------------------------------------------- Poly Haven pieces
def load(name, tag):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(next((PH / name).glob("*_1k.gltf"))))
    objs = [o for o in bpy.data.objects if o not in before]
    for o in objs:
        o.name = f"{tag}_{o.name}"
    return objs


def place(objs, rot, x, z, y, yaw=0.0):
    """turn (Blender euler, radians) then yaw about up; bounds centred on spec (x, z), bottom at spec y"""
    root = bpy.data.objects.new("grp", None); coll.objects.link(root)
    for o in objs:
        if o.parent is None:
            o.parent = root
    root.rotation_euler = (Euler((0, 0, math.radians(yaw))).to_matrix() @ Euler(rot).to_matrix()).to_euler(); bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(c) for o in objs if o.type == "MESH" for c in o.bound_box]
    lo = Vector([min(p[i] for p in pts) for i in range(3)]); hi = Vector([max(p[i] for p in pts) for i in range(3)])
    root.location = Vector((-x, z, y)) - Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z)); bpy.context.view_layer.update()
    for o in objs:
        o.select_set(o.type == "MESH")
    bpy.context.view_layer.objects.active = next(o for o in objs if o.type == "MESH")
    bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    for o in objs:
        if o.type != "MESH":
            bpy.data.objects.remove(o)
    bpy.data.objects.remove(root)
    print(f"  placed {objs[0].name if objs else '?'} at spec ({x:.3f}, {y:.3f}, {z:.3f})")


DESK_TOP = BOX["buzz_desk"]["y"][1]
# desk: the girlfriend photo in the standing frame (its artwork image swapped), facing the room (-z spec = Blender -Y; native front +X)
fr = load("standing_picture_frame_02", "BZP_DeskFrame")
import bmesh   # noqa: E402
for o in fr:   # its glass pane (faces of the glass slot): draws as an opaque sheet over the photo, and lies coplanar with it
    if o.type == "MESH":
        gl = [i for i, s in enumerate(o.material_slots) if s.material and "glass" in s.material.name]
        bm = bmesh.new(); bm.from_mesh(o.data)
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index in gl], context="FACES"); bm.to_mesh(o.data); bm.free()
for o in fr:
    for s in getattr(o, "material_slots", []):
        if s.material and "artwork" in s.material.name:
            for n in s.material.node_tree.nodes:
                if n.type == "TEX_IMAGE" and "diff" in n.image.name:
                    n.image = bpy.data.images.load(str(TEX / "buzz_props_girlfriend.png")); n.image.pack()
place(fr, (0, 0, 0), 8.93, 15.86, DESK_TOP, yaw=-90)
# desk: the cassette player lying flat (its face, glTF +z = Blender -Y, turned up)
wm = load("portable_cassette_player", "BZP_Walkman")
for o in wm:   # four closed parts (4 mm screws under it) are wound inward as downloaded (glb_orientation.py): islands with a negative
    if o.type == "MESH":   # signed volume are flipped, and islands under 6 mm across (the screws, never seen) dropped
        bm = bmesh.new(); bm.from_mesh(o.data); bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
        seen, drop = set(), []
        for f0 in bm.faces:
            if f0.index in seen:
                continue
            isl, stack = [], [f0]; seen.add(f0.index)
            while stack:
                f = stack.pop(); isl.append(f)
                for e in f.edges:
                    for g in e.link_faces:
                        if g.index not in seen:
                            seen.add(g.index); stack.append(g)
            vol = sum(l[0].vert.co.dot(l[i].vert.co.cross(l[i + 1].vert.co)) for f in isl for l in [f.loops] for i in range(1, len(l) - 1))
            vs = {v for f in isl for v in f.verts}
            if max(max(v.co[i] for v in vs) - min(v.co[i] for v in vs) for i in range(3)) < 0.006:
                drop += isl
            elif vol < 0 and all(e.is_manifold for f in isl for e in f.edges):
                bmesh.ops.reverse_faces(bm, faces=isl)
        bmesh.ops.delete(bm, geom=drop, context="FACES")
        bm.to_mesh(o.data); bm.free()
        o.data.shade_smooth(); o.data.set_sharp_from_angle(angle=math.radians(30))
place(wm, (math.radians(-90), 0, 0), 9.72, 15.74, DESK_TOP, yaw=15)
# shelf: a baseball on board 1
place(load("baseball_01", "BZP_ShelfBall"), (0.3, 0.8, 0.2), 7.63, 13.65, BOX["buzz_shelves_board1"]["y"][1])

# ---------------------------------------------------------------- the footlocker contents (liner x 9.207-10.037, z 13.823-14.246)
# authored for the trunk at x 9.192-10.054; the trunk moved with the bed (buzz_trunk.json x, Oct 18 bed nudge) and the contents
# stayed behind (the Playboy poked through its end wall): they ride with it now (DX, applied to every footlocker object below)
DX = json.loads((ROOT / "spec/dressing/buzz_trunk.json").read_text())["x"][0] - 9.192
_before_trunk = set(bpy.data.objects)
F = 0.016
place(load("baseball_01", "BZP_TrunkBall"), (1.1, 0.2, 2.0), 9.40, 14.18, F)
# Playboy, front right: 8.5 x 11 in, cover top toward +x (film 2700)
printed_box("BZP_Playboy", "BZP_Playboy", 9.755, 10.031, F, F + 0.006, 13.995, 14.205, [(0, 0), (0, 1), (1, 1), (1, 0)])
# four cassette cases, back right
for i, x in enumerate((9.69, 9.77, 9.85, 9.93)):
    box(f"BZP_Cassette{i}", "BZP_Cassette", x, x + 0.07, F, F + 0.017, 13.845, 13.954)
# the Crunch Tators bag, centre back: a pillow (the top face's centre raised), the film's face on top
p = Part("BZP_ChipBag", "BZP_Chips"); x0, x1, z0, z1, yb, yt, ym = 9.47, 9.67, 13.84, 14.12, F, F + 0.025, F + 0.06
c = ((x0 + x1) / 2, ym, (z0 + z1) / 2); side = [(0.9, 0.5)] * 4
corners = [(x0, yt, z0), (x1, yt, z0), (x1, yt, z1), (x0, yt, z1)]; cuv = [(0, 1), (0, 0), (1, 0), (1, 1)]
for k in range(4):
    a, b = corners[k], corners[(k + 1) % 4]
    p.face([a, b, c], (0, 1, 0), [cuv[k], cuv[(k + 1) % 4], (0.5, 0.5)])
p.face([(x0, yb, z0), (x1, yb, z0), (x1, yb, z1), (x0, yb, z1)], (0, -1, 0), side)
for pts, n in (([(x0, yb, z0), (x0, yb, z1), (x0, yt, z1), (x0, yt, z0)], (-1, 0, 0)), ([(x1, yb, z0), (x1, yb, z1), (x1, yt, z1), (x1, yt, z0)], (1, 0, 0)),
               ([(x0, yb, z0), (x1, yb, z0), (x1, yt, z0), (x0, yt, z0)], (0, 0, -1)), ([(x0, yb, z1), (x1, yb, z1), (x1, yt, z1), (x0, yt, z1)], (0, 0, 1))):
    p.face(pts, n, side)
build(p)
# three Pixy Stix (paper straws, 8 mm square, 0.18 long), front centre
for i, (z, m) in enumerate(((14.16, "BZP_StixPurple"), (14.18, "BZP_StixOrange"), (14.20, "BZP_StixGreen"))):
    box(f"BZP_Stix{i}", m, 9.48, 9.66, F, F + 0.008, z, z + 0.008)
# a toilet roll standing, front left (0.11 dia, 0.10 tall, 4.2 cm core)
p = Part("BZP_ToiletRoll", "BZP_Paper"); RX, RZ = 9.30, 14.15
tube(p, RX, RZ, F, F + 0.10, 0.055, 0.055, 32); tube(p, RX, RZ, F, F + 0.10, 0.021, 0.021, 32, inward=True)
annulus(p, RX, RZ, F + 0.10, 0.021, 0.055, 32, True); annulus(p, RX, RZ, F, 0.021, 0.055, 32, False)
build(p, smooth=True)
# the girlfriend photo in a silver frame lying flat, back left (5 x 7 in print, 2 cm frame), photo top toward the hinge (-z)
fx0, fx1, fz0, fz1, fy = 9.225, 9.39, 13.835, 14.05, F
B, T = 0.019, 0.013
for n, (a0, a1, b0, b1) in {"L": (fx0, fx0 + B, fz0, fz1), "R": (fx1 - B, fx1, fz0, fz1), "Back": (fx0 + B, fx1 - B, fz0, fz0 + B), "Front": (fx0 + B, fx1 - B, fz1 - B, fz1)}.items():
    box(f"BZP_TrunkFrame{n}", "BZP_Silver", a0, a1, fy, fy + T, b0, b1)
# the print (no backing board: it lay 2 mm under the print and z-fought, build 1), its edges under the frame bars (a joint)
p = Part("BZP_TrunkPhoto", "BZP_Photo"); y = fy + 0.006
p.face([(fx0 + B - 0.003, y, fz0 + B - 0.003), (fx1 - B + 0.003, y, fz0 + B - 0.003), (fx1 - B + 0.003, y, fz1 - B + 0.003), (fx0 + B - 0.003, y, fz1 - B + 0.003)],
       (0, 1, 0), [(0, 1), (1, 1), (1, 0), (0, 0)])
build(p)

for o in set(bpy.data.objects) - _before_trunk:   # spec +x is Blender -x
    o.location.x -= DX
print(f"  footlocker contents moved {DX:+.3f} m in x with the trunk")

OUT.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(OUT), export_format="GLB", export_yup=True, export_apply=True)
print("wrote", OUT)
