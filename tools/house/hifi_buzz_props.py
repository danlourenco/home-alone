"""hifi_buzz_props: Buzz's hero props (props lane: placed by eye from the film, Marina where the film doesn't show it; real-world sizes;
no change record). One GLB in spec coordinates above the UPPER floor (SpecGreybox.BuzzProps places it at 0).

  the Jordan "Measure Up" poster   film 478/480/524: on a closet door right of the desk lamp, by the shelves corner. No closet door is
                                   built yet: flat on the desk wall there (Marina's spot, 529-537 s), 1.2 cm proud, bottom over the
                                   0.14 m baseboard. Sheet 0.735 x 2.15 m from its own ruler (1 ft = 211 px)
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
     "BZP_Chips": tex_material("BZP_Chips", "buzz_props_chips.png", 0.55)}
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


# ---------------------------------------------------------------- the Jordan poster (desk wall, face z 15.998)
WALL_Z, PH_W, PH_H, P_Y0, P_CX = 15.998, 0.735, 2.15, 0.16, 8.20
p = Part("BZP_JordanPoster", "BZP_Jordan"); x0, x1, y0, y1, z0, z1 = P_CX - PH_W / 2, P_CX + PH_W / 2, P_Y0, P_Y0 + PH_H, WALL_Z - 0.012, WALL_Z
e = [(0.02, 0.5)] * 4   # the ruler's yellow edge on the sheet's thin sides
# seen from the room (looking +z, spec -x on the right): the image's left (u 0, the ruler) at x1, its right at x0
p.face([(x1, y0, z0), (x0, y0, z0), (x0, y1, z0), (x1, y1, z0)], (0, 0, -1), [(0, 0), (1, 0), (1, 1), (0, 1)])
for pts, n in (([(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)], (0, 1, 0)), ([(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)], (0, -1, 0)),
               ([(x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)], (-1, 0, 0)), ([(x1, y0, z0), (x1, y0, z1), (x1, y1, z1), (x1, y1, z0)], (1, 0, 0)),
               ([(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], (0, 0, 1))):
    p.face(pts, n, e)
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

OUT.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(OUT), export_format="GLB", export_yup=True, export_apply=True)
print("wrote", OUT)
