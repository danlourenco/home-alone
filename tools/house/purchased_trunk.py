"""purchased_trunk: Buzz's footlocker from the bought scan ("Worn Black Trunk", Sketchfab, CC Attribution: CREDITS.md), rebuilt so
the lid opens and the box is hollow, written ONLY to the gitignored unity/HomeAlone/Assets/Purchased/Trunk/BuzzTrunk.glb.

- The scan is one closed shell (body and lid fused). Cut at the lid's lower edge (z 0.445 in the scan, where its back overhang
  starts): TrunkBody = the shell below, TrunkLid = the shell above, its origin ON THE HINGE LINE (back top edge) so a later
  interaction turns that one transform.
- Hollow: an inner liner box in each part (walls 1 cm inside the shell's innermost face, floor 1.5 cm up), faces pointing in,
  lined with the film's wood-chip paper (spec/dressing/buzz_trunk_lining.png, cut from film 2704 by tools/house/buzz_trunk.py).
- Brass: a thin channel ring on the body's rim and one on the lid's edge (film 2704/2718), covering the cut and the liner's top.
- Uniform scale to the film's outer length (0.86 m at the rim, spec/dressing/buzz_trunk.json): no texture stretch; depth and
  height follow the scan.
- Placed at spec/dressing/buzz_trunk.json x/z (spec -> Blender as hifi_lib: B(x, y, z) = (-x, z, y)), latches toward the room.

  /Applications/Blender.app/Contents/MacOS/Blender -b --disable-autoexec -P tools/house/purchased_trunk.py
  (writes the scan's built footprint back into buzz_trunk.json "scan"; re-run buzz_trunk.py then this if it changed)
"""
import json
from pathlib import Path

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "unity/HomeAlone/Assets/Purchased/Trunk/source"
OUT = ROOT / "unity/HomeAlone/Assets/Purchased/Trunk/BuzzTrunk.glb"
SPEC = ROOT / "spec/dressing/buzz_trunk.json"
J = json.loads(SPEC.read_text())
SEAM = 0.445          # scan metres: the lid's lower edge
WALL, FLOOR, GAP = 0.010, 0.015, 0.004   # liner inset, liner floor, shell cut back from the seam (each side) under the brass rings
RING_W, RING_H, RING_OUT = 0.004, 0.015, 0.003   # brass ring: inward width past the liner, height, proud of the shell

bpy.ops.wm.open_mainfile(filepath=str(SRC / "Geo/Chest.blend"), load_ui=False)
src = bpy.data.objects["ChestLow_obj"]
for o in list(bpy.data.objects):
    if o is not src:
        bpy.data.objects.remove(o)
me = src.data.copy(); me.transform(src.matrix_world)
# front (latches, scan -x) toward the room = spec -x = Blender +x: turn 180 about z
me.transform(Matrix.Rotation(np.pi, 4, "Z"))
V = np.array([v.co[:] for v in me.vertices])
body_len = np.ptp(V[V[:, 2] < SEAM - 0.02, 1])
S = J["outer_length_m"] / body_len
me.transform(Matrix.Scale(S, 4)); V *= S; seam = SEAM * S


def ext(lo, hi, central=0.6):
    """innermost faces of the shell between heights lo..hi: per side, the smallest |extent| over 2 cm slices (central part only)"""
    xs, ys = [], []
    for z in np.arange(lo, hi, 0.02 * S):
        s = V[(V[:, 2] >= z) & (V[:, 2] < z + 0.02 * S)]
        cx = s[np.abs(s[:, 1]) < central * np.abs(V[:, 1]).max()]; cy = s[np.abs(s[:, 0] - np.median(V[:, 0])) < 0.15]
        xs.append((cx[:, 0].min(), cx[:, 0].max())); ys.append((cy[:, 1].min(), cy[:, 1].max()))
    xs, ys = np.array(xs), np.array(ys)
    return (xs[:, 0].max(), xs[:, 1].min(), ys[:, 0].max(), ys[:, 1].min()), (xs[:, 0].min(), xs[:, 1].max(), ys[:, 0].min(), ys[:, 1].max())


# the body's front face below the latch hasps (they hang over the rim, scan z 0.22-0.42): inner extents from the plain shell
b_in, b_out = ext(0.03 * S, 0.20 * S)
b_out_rim = b_out   # the plain shell: near the rim the latch hasps would push the ring out
l_in, l_out = ext(seam + GAP + 0.01, V[:, 2].max() - 0.03)
top = V[:, 2].max(); bottom = V[:, 2].min()


def part(name, keep_below):
    m = me.copy(); bm = bmesh.new(); bm.from_mesh(m)
    z = seam - GAP if keep_below else seam + GAP
    geom = bm.verts[:] + bm.edges[:] + bm.faces[:]
    bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, 0, z), plane_no=(0, 0, 1), clear_outer=keep_below, clear_inner=not keep_below)
    bm.to_mesh(m); bm.free(); m.name = name; return m


def add_box(bm, x0, x1, y0, y1, z0, z1, mat, inward, skip=()):
    """axis box faces (outward normals unless inward), UVs in metres / the lining repeat; skip: face keys to leave open"""
    rep = J["lining"]["repeat_m"]; uv = bm.loops.layers.uv.verify()
    P = {"-x": [(x0, y1, z0), (x0, y0, z0), (x0, y0, z1), (x0, y1, z1)], "+x": [(x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)],
         "-y": [(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)], "+y": [(x1, y1, z0), (x0, y1, z0), (x0, y1, z1), (x1, y1, z1)],
         "-z": [(x0, y1, z0), (x1, y1, z0), (x1, y0, z0), (x0, y0, z0)], "+z": [(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]}
    for k, pts in P.items():
        if k in skip:
            continue
        pts = pts if not inward else pts[::-1]
        f = bm.faces.new([bm.verts.new(p) for p in pts]); f.material_index = mat
        ax = "xyz".index(k[1])
        for l in f.loops:
            c = l.vert.co; a, b = [c[i] for i in range(3) if i != ax]
            l[uv].uv = (a / rep[0], b / rep[1]) if ax != 2 else (c.x / rep[0], c.y / rep[1])


def ring(bm, outer, inner, z0, z1, mat):
    """a rectangular brass ring (closed solid, outward normals): outer/inner = (x0, x1, y0, y1)"""
    ox0, ox1, oy0, oy1 = outer; ix0, ix1, iy0, iy1 = inner
    O = [(ox0, oy0), (ox1, oy0), (ox1, oy1), (ox0, oy1)]; I = [(ix0, iy0), (ix1, iy0), (ix1, iy1), (ix0, iy1)]
    ob = [bm.verts.new((x, y, z0)) for x, y in O]; ot = [bm.verts.new((x, y, z1)) for x, y in O]
    ib = [bm.verts.new((x, y, z0)) for x, y in I]; it = [bm.verts.new((x, y, z1)) for x, y in I]
    for i in range(4):
        j = (i + 1) % 4
        for q in ([ob[i], ob[j], ot[j], ot[i]], [ib[j], ib[i], it[i], it[j]], [ot[i], ot[j], it[j], it[i]], [ob[j], ob[i], ib[i], ib[j]]):
            bm.faces.new(q).material_index = mat


def finish(m, liner, rings, lid):
    bm = bmesh.new(); bm.from_mesh(m)
    for f in bm.faces:
        f.material_index = 0
    x0, x1, y0, y1 = liner
    if lid:
        add_box(bm, x0, x1, y0, y1, seam + GAP / 2, top - FLOOR, 1, True, skip=("-z",))
    else:
        add_box(bm, x0, x1, y0, y1, bottom + FLOOR, seam - GAP / 2, 1, True, skip=("+z",))
    for o, z0, z1 in rings:
        ring(bm, o, (x0 + RING_W, x1 - RING_W, y0 + RING_W, y1 - RING_W), z0, z1, 2)
    bm.to_mesh(m); bm.free()


# ---- materials
def image(path, name, size, fn=None, colorspace="sRGB"):
    srcim = bpy.data.images.load(str(path)); srcim.scale(size, size)
    a = np.array(srcim.pixels[:], dtype=np.float32).reshape(size, size, 4)
    if fn:
        a = fn(a)
    im = bpy.data.images.new(name, size, size, alpha=False); im.colorspace_settings.name = colorspace
    im.pixels.foreach_set(a.ravel()); im.file_format = "PNG"; im.pack(); bpy.data.images.remove(srcim); return im


def bump_to_normal(a, k=6.0):
    h = a[..., 0]; gy, gx = np.gradient(h); n = np.dstack([-gx * k, -gy * k, np.ones_like(h)]); n /= np.linalg.norm(n, axis=2, keepdims=True)
    out = a.copy(); out[..., :3] = n * 0.5 + 0.5; out[..., 3] = 1; return out


def mat(name, base=None, normal=None, color=(1, 1, 1, 1), rough=0.6, metal=0.0, rough_img=None):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; bs = nt.nodes["Principled BSDF"]
    bs.inputs["Base Color"].default_value = color; bs.inputs["Roughness"].default_value = rough; bs.inputs["Metallic"].default_value = metal
    if base:
        t = nt.nodes.new("ShaderNodeTexImage"); t.image = base; nt.links.new(t.outputs["Color"], bs.inputs["Base Color"])
    if normal:
        n = nt.nodes.new("ShaderNodeTexImage"); n.image = normal; nm = nt.nodes.new("ShaderNodeNormalMap")
        nt.links.new(n.outputs["Color"], nm.inputs["Color"]); nt.links.new(nm.outputs["Normal"], bs.inputs["Normal"])
    return m


T = SRC / "Textures"
M_SHELL = mat("TR_Shell", image(T / "Chest_Diff_4k.1001.tiff", "TR_ShellDiff", 2048),
              image(T / "Chest_Bump_4k.1001.tif", "TR_ShellNrm", 2048, bump_to_normal, "Non-Color"), rough=0.55)
lt = bpy.data.images.load(str(ROOT / J["lining"]["png"])); lt.pack()
M_LINING = mat("TR_Lining", lt, rough=0.85)
M_BRASS = mat("TR_Brass", color=(0.78, 0.60, 0.28, 1), rough=0.3, metal=0.8)   # SpecGreybox.Trunk swaps in BrassMat
inner = lambda e: (e[0] + WALL, e[1] - WALL, e[2] + WALL, e[3] - WALL)
grow = lambda e: (e[0] - RING_OUT, e[1] + RING_OUT, e[2] - RING_OUT, e[3] + RING_OUT)
# the liner's walls stand inside the narrower of the two parts so body and lid liners line up when closed
lin = tuple(f(a, b) for f, a, b in zip((max, min, max, min), inner(b_in), inner(l_in)))
body = part("TrunkBody", True); lid = part("TrunkLid", False)
for m in (body, lid):
    m.materials.clear()
    for x in (M_SHELL, M_LINING, M_BRASS):
        m.materials.append(x)
    while m.color_attributes:
        m.color_attributes.remove(m.color_attributes[0])

finish(body, lin, [(grow(b_out_rim), seam - GAP - RING_H + GAP, seam - 0.001)], False)
_, l_out_edge = ext(seam + GAP, seam + 0.05 * S)
finish(lid, lin, [(grow(l_out_edge), seam + 0.001, seam + RING_H)], True)

# ---- objects: root at the box's floor centre (spec), lid origin on the hinge line (back top edge, spec +x = Blender -x)
bpy.data.objects.remove(src)
B = lambda x, y, z: Vector((-x, z, y))
cx, cz = sum(J["x"]) / 2, sum(J["z"]) / 2
Vb = np.array([v.co[:] for v in body.vertices]); Vl = np.array([v.co[:] for v in lid.vertices])
allv = np.vstack([Vb, Vl])
mid = Vector(((allv[:, 0].min() + allv[:, 0].max()) / 2, (allv[:, 1].min() + allv[:, 1].max()) / 2, allv[:, 2].min()))
root = bpy.data.objects.new("BuzzTrunk", None); bpy.context.scene.collection.objects.link(root)
root.location = B(cx, 0.001, cz)
root.rotation_euler = (0.0, 0.0, np.radians(J.get("yaw_deg", 0)))   # 90: latches from spec -x to +z (foot of the bed)
ob = bpy.data.objects.new("TrunkBody", body); bpy.context.scene.collection.objects.link(ob); ob.parent = root
body.transform(Matrix.Translation(-mid))
hinge = Vector((allv[:, 0].min(), 0.0, seam)) - mid                 # back edge (Blender -x), at the seam
lid.transform(Matrix.Translation(-mid - hinge))
ol = bpy.data.objects.new("TrunkLid", lid); bpy.context.scene.collection.objects.link(ol); ol.parent = root; ol.location = hinge

fx = np.ptp(allv[:, 0]); fy = np.ptp(allv[:, 1]); fz = np.ptp(allv[:, 2])
J["scan"] = {"scale": round(S, 4), "footprint_depth_m": round(float(fx), 3), "body_depth_m": round(float(fx), 3),
             "length_m": round(float(fy), 3), "height_m": round(float(fz), 3), "body_height_m": round(float(seam - bottom), 3),
             "lid_height_m": round(float(top - seam), 3), "liner_inside_m": [round(lin[1] - lin[0], 3), round(lin[3] - lin[2], 3)],
             "hinge_above_floor_m": round(float(seam - bottom), 3)}
SPEC.write_text(json.dumps(J, indent=1) + "\n")
print("scan built:", J["scan"])
OUT.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(OUT), export_format="GLB", export_yup=True, export_apply=True)
print("wrote", OUT)
