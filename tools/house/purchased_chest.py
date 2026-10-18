"""purchased_chest: Buzz's chest of drawers (film 2718: a tall dark-mahogany chest, one column of framed drawers, brass batwing
pulls) rebuilt from the owned Classic Wooden Furniture Pack BEDSIDE_CAB_01 (3 drawers, nightstand size), written ONLY to the
gitignored unity/HomeAlone/Assets/Purchased/BuzzChest/BuzzChest.glb (pack licence: use, no redistribution).

- Height: whole drawer fronts copied (the pack's 0.16 m drawer, 3 -> N_DRAWERS); each copy gets a 'cut-and-move' band through its
  flat panel's middle (INS) so N drawers reach the box's 1.257 m. The case (posts, sides, carcass: vertical grain) is stretched
  only along its grain to follow. Width: everything right of the drawer centre moves right (stretch along the drawers' horizontal
  grain only) to the box's 1.04 m. No face is stretched across its grain except each panel's middle (+INS).
- The round knobs are dropped; two brass batwing (Chippendale) pulls per drawer: a backplate cut to film 2718's outline + a bail.
- Albedo tinted to the film's dark mahogany (a copy under Purchased/, the pack's file untouched).
- A flat back board (the chest stands against the wall). store_props gives yaw 270 (Orient took the pulls for the back).
- Exported at the origin, front -y (Blender); StoreProps fits it into spec/dressing/store_props.json buzz_chest (~x1 each axis).

  /Applications/Blender.app/Contents/MacOS/Blender -b --disable-autoexec -P tools/house/purchased_chest.py
"""
import json
import math
from pathlib import Path

import bmesh
import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
PACK = ROOT / "unity/HomeAlone/Assets/Classic Wooden Furniture Pack"
OUT = ROOT / "unity/HomeAlone/Assets/Purchased/BuzzChest/BuzzChest.glb"
BOX = next(b for b in json.loads((ROOT / "spec/dressing/buzz.json").read_text())["boxes"] if b["name"] == "buzz_chest")
H, W = BOX["y"][1] - BOX["y"][0], BOX["z"][1] - BOX["z"][0]          # 1.257 tall, 1.039 along the wall

N_DRAWERS = 6
D0, D1, DMID = 0.258, 0.418, 0.338     # pack drawer 1 (Blender z, before the floor shift): bottom, top, its flat panel's middle
STACK0, STACK1 = 0.258, 0.738          # the pack's 3-drawer stack
XC = -0.11                             # drawer centre (knob axis)
FLOOR = 0.14

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(PACK / "Meshes/BEDSIDE_CAB_01.fbx"))
src = [o for o in bpy.data.objects if o.type == "MESH"][0]
bpy.context.view_layer.objects.active = src; src.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
bm = bmesh.new(); bm.from_mesh(src.data)
bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
uv = bm.loops.layers.uv.active

# face islands (faces linked through shared vertices)
isl, seen = [], set()
for f in bm.faces:
    if f.index in seen:
        continue
    st, comp = [f], []; seen.add(f.index)
    while st:
        a = st.pop(); comp.append(a)
        for v in a.verts:
            for g in v.link_faces:
                if g.index not in seen:
                    seen.add(g.index); st.append(g)
    isl.append(comp)


def bbox(fs):
    P = np.array([v.co[:] for f in fs for v in f.verts]); return P.min(0), P.max(0)


knobs, drawers, frame = [], [], []
for c in isl:
    lo, hi = bbox(c)
    if hi[0] - lo[0] < 0.05 and lo[1] < -0.05:
        knobs.append(c)
    elif hi[1] < 0 and hi[2] - lo[2] < 0.17 and hi[0] - lo[0] > 0.3:
        drawers.append((lo[2], c))
    else:
        frame.append(c)
assert len(knobs) == 3 and len(drawers) == 3, (len(knobs), len(drawers))
template = min(drawers, key=lambda d: abs(d[0] - D0))[1]

ADD_W = W - 0.53                                           # pack top 0.53 wide
P_ = (H - (0.635 - (STACK1 - STACK0))) / N_DRAWERS          # new drawer pitch
INS = P_ - (D1 - D0)
NEW1 = STACK0 + N_DRAWERS * P_
print(f"pitch {P_:.4f}, band {INS:.4f}, width add {ADD_W:.3f}")


def xmap(x):
    return x + (ADD_W if x > XC else 0.0)


# ---- new mesh: frame (stretched along its grain), N drawer copies, no knobs
out = bmesh.new(); ouv = out.loops.layers.uv.new("UVMap")


def copy(faces, zmap):
    vm = {}
    for f in faces:
        vs = []
        for v in f.verts:
            if v not in vm:
                vm[v] = out.verts.new((xmap(v.co.x), v.co.y, zmap(v.co.z) - FLOOR))
            vs.append(vm[v])
        try:
            nf = out.faces.new(vs)
        except ValueError:
            continue
        for l0, l1 in zip(f.loops, nf.loops):
            l1[ouv].uv = l0[uv].uv


def zframe(z):
    if z <= STACK0:
        return z
    if z >= STACK1:
        return z + NEW1 - STACK1
    return STACK0 + (z - STACK0) * (NEW1 - STACK0) / (STACK1 - STACK0)


for c in frame:
    copy(c, zframe)
for i in range(N_DRAWERS):
    copy(template, lambda z, i=i: STACK0 + i * P_ + (z - D0) + (INS if z > DMID else 0.0))

# flat back board, flush with the top's back edge (a grid so it reads as the flat back)
V = np.array([v.co[:] for v in out.verts])
yb = V[:, 1].max(); x0, x1 = V[:, 0].min(), V[:, 0].max(); z1 = V[:, 2].max()
n = 16
grid = [[out.verts.new((x0 + (x1 - x0) * i / n, yb, 0.02 + (z1 - 0.06) * j / n)) for j in range(n + 1)] for i in range(n + 1)]
for i in range(n):
    for j in range(n):
        f = out.faces.new((grid[i][j], grid[i][j + 1], grid[i + 1][j + 1], grid[i + 1][j]))
        for l in f.loops:
            l[ouv].uv = (0.62 + 0.15 * (l.vert.co.x - x0) / (x1 - x0), 0.45 + 0.12 * l.vert.co.z / z1)

wood_me = bpy.data.meshes.new("BuzzChestWood"); out.to_mesh(wood_me)
yfront = min(v.co.y for f in template for v in f.verts)    # drawer front face
dx0 = xmap(min(v.co.x for f in template for v in f.verts)); dx1 = xmap(max(v.co.x for f in template for v in f.verts))

# ---- brass batwing pulls (film 2718): backplate outline (right half, normalised: x 0..0.5, y -0.5..0.5) + bail on two posts
HALF = [(0, .50), (.06, .48), (.10, .38), (.16, .30), (.24, .34), (.32, .40), (.40, .36), (.46, .22), (.50, .05), (.47, -.08),
        (.40, -.12), (.32, -.10), (.24, -.18), (.16, -.30), (.10, -.42), (.04, -.50), (0, -.50)]
PW, PH, PT = 0.100, 0.062, 0.0025        # plate width, height, thickness
outline = [(x, y) for x, y in HALF] + [(-x, y) for x, y in reversed(HALF[1:-1])]
pb = bmesh.new()


def plate(cx, cz):
    y0 = yfront - 0.0008
    fr = [pb.verts.new((cx + x * PW, y0, cz + y * PH)) for x, y in outline]
    bk = [pb.verts.new((cx + x * PW, y0 - PT, cz + y * PH)) for x, y in outline]
    pb.faces.new(list(reversed(fr))); pb.faces.new(bk)
    k = len(fr)
    for i in range(k):
        pb.faces.new((fr[i], fr[(i + 1) % k], bk[(i + 1) % k], bk[i]))


def tube(path, r, seg=8):
    rings = []
    for i, p in enumerate(path):
        a = np.array(path[min(i + 1, len(path) - 1)]) - np.array(path[max(i - 1, 0)]); a /= np.linalg.norm(a)
        u = np.cross(a, (0, 1, 0)); u = u / np.linalg.norm(u) if np.linalg.norm(u) > 1e-6 else np.array((1.0, 0, 0))
        w = np.cross(a, u)
        rings.append([pb.verts.new(tuple(np.array(p) + r * (math.cos(t) * u + math.sin(t) * w)))
                      for t in np.linspace(0, 2 * math.pi, seg, endpoint=False)])
    for a, b in zip(rings, rings[1:]):
        for i in range(seg):
            pb.faces.new((a[i], a[(i + 1) % seg], b[(i + 1) % seg], b[i]))
    pb.faces.new(list(reversed(rings[0]))); pb.faces.new(rings[-1])


def pull(cx, cz):
    plate(cx, cz)
    face = yfront - 0.0008 - PT; proud = face - 0.009
    for s in (-1, 1):                                  # posts with a round boss
        tube([(cx + s * 0.031, face, cz + 0.006), (cx + s * 0.031, proud, cz + 0.006)], 0.0035)
    arc = [(cx + 0.031 * math.cos(t), proud - 0.002 * math.sin(t), cz + 0.006 - 0.028 * math.sin(t)) for t in np.linspace(0, math.pi, 17)]
    tube(arc, 0.0026)


dcx = (dx0 + dx1) / 2; off = 0.30 * (dx1 - dx0)
for i in range(N_DRAWERS):
    cz = STACK0 + i * P_ + P_ / 2 - FLOOR
    for s in (-1, 1):
        pull(dcx + s * off, cz)
brass_me = bpy.data.meshes.new("BuzzChestBrass"); pb.to_mesh(brass_me)

# ---- materials: mahogany-tinted albedo copy + the pack's normal map; brass (StoreProps swaps BC_Brass for the house brass)
T = PACK / "Textures/HDRP"
alb = bpy.data.images.load(str(T / "BEDSIDE_CAB_ALBEDO.png"))
px = np.array(alb.pixels[:]).reshape(-1, 4)
px[:, :3] *= (0.78, 0.42, 0.32)                       # sRGB-space tint: pack's mid brown -> film 2718 dark red-brown mahogany
alb.pixels[:] = px.ravel()
OUT.parent.mkdir(parents=True, exist_ok=True)
alb.filepath_raw = str(OUT.parent / "BuzzChest_Albedo.png"); alb.file_format = "PNG"; alb.save()
nrm = bpy.data.images.load(str(T / "BEDSIDE_CAB_NORMAL.png")); nrm.colorspace_settings.name = "Non-Color"

wood = bpy.data.materials.new("BC_Mahogany"); wood.use_nodes = True
nt = wood.node_tree; bsdf = nt.nodes["Principled BSDF"]
ti = nt.nodes.new("ShaderNodeTexImage"); ti.image = alb; nt.links.new(ti.outputs["Color"], bsdf.inputs["Base Color"])
tn = nt.nodes.new("ShaderNodeTexImage"); tn.image = nrm
nm = nt.nodes.new("ShaderNodeNormalMap"); nt.links.new(tn.outputs["Color"], nm.inputs["Color"]); nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
bsdf.inputs["Roughness"].default_value = 0.55   # 0.38 mirrored the room's blue sky on every edge (overnight2 capture)
brass = bpy.data.materials.new("BC_Brass"); brass.use_nodes = True
b2 = brass.node_tree.nodes["Principled BSDF"]
b2.inputs["Base Color"].default_value = (0.72, 0.52, 0.22, 1); b2.inputs["Metallic"].default_value = 1.0; b2.inputs["Roughness"].default_value = 0.35
wood_me.materials.append(wood); brass_me.materials.append(brass)

bpy.data.objects.remove(src)
root = bpy.data.objects.new("BuzzChest", None); bpy.context.scene.collection.objects.link(root)
for nme, me in (("ChestBody", wood_me), ("ChestPulls", brass_me)):
    o = bpy.data.objects.new(nme, me); bpy.context.scene.collection.objects.link(o); o.parent = root
    for p in me.polygons:
        p.use_smooth = nme == "ChestPulls"
allv = np.array([v.co[:] for me in (wood_me, brass_me) for v in me.vertices])
print("built size (x w, y d, z h):", np.ptp(allv, 0).round(3), "target", round(W, 3), "x", round(H, 3))
bpy.ops.export_scene.gltf(filepath=str(OUT), export_format="GLB", export_yup=True)
print("wrote", OUT)
