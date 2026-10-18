"""purchased_bed: Buzz's twin bed (Marina 553-561: four posts with ball finials, shaped head- and footboard, white sheet, green
blanket over the foot half, one white pillow) rebuilt from the owned Classic Wooden Furniture Pack BED_01 (a double), written ONLY
to the gitignored unity/HomeAlone/Assets/Purchased/BuzzBed/BuzzBed.glb (pack licence: use, no redistribution).
changes/2026-10-18-buzz-bed.json.

- Width (double -> twin): the frame (posts, head/footboard, rails) is cut on two planes symmetric about its middle, the middle
  CUT metres dropped and the right half slid left; the boards are symmetric so the two cut profiles meet and are welded (no
  squashed post). Soft parts (mattress, slats, cover) are narrowed instead (no seam in the cloth): the mattress to the inner
  span of the posts (twin, 0.98 m), the cover's drape pulled in to hang just outside the side rails, inside the posts' faces.
- Length: the foot posts and footboard move DY toward the foot; the deck (rails, slats, mattress, cover) is stretched along its
  length (the rails along their grain) to Marina's 2.155 m footboard face off the wall.
- Heights: only the straight post shafts are lengthened (cut-and-move above a plain band) to Marina's finial tops, head 1.342,
  foot 0.884; the boards are raised by the same amounts in their flat panel middles (the pack's board/post proportions kept).
- Under-bed (DEVIATIONS 72): rails, slats and mattress raised so their undersides stand UNDER_Z above the floor (kid Kevin's
  crouch 0.45 + skin 0.02 fits under); cover top at Marina's 0.645 (mattress 0.625 + blanket); the cover's drape ends 0.46 up.
- One pillow (the pack's left one, centred); the cover's foot half on top green (Marina's blanket), the rest the pack's sheet.
- Exported at the origin, head +y (Blender); store_props buzz_bed (yaw 180) fits it into spec/dressing/buzz.json's bed box (~x1).

  /Applications/Blender.app/Contents/MacOS/Blender -b --disable-autoexec -P tools/house/purchased_bed.py
"""
import json
from pathlib import Path

import bmesh
import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
PACK = ROOT / "unity/HomeAlone/Assets/Classic Wooden Furniture Pack"
OUT = ROOT / "unity/HomeAlone/Assets/Purchased/BuzzBed/BuzzBed.glb"
PIECE = next(p for p in json.loads((ROOT / "spec/dressing/buzz.json").read_text())["pieces"] if p["name"] == "buzz_bed")
W_OUT = PIECE["along"][1] - PIECE["along"][0]        # outer width over the posts (finial centres + one post)
L_OUT = PIECE["off"][1] - PIECE["off"][0]            # head posts' back to the footboard's face
HEAD, FOOT, TOP = PIECE["h"][1], PIECE["foot_h"], PIECE["mattress_top"]

FLOOR = 0.144                 # pack: the posts' feet
XC = -0.106                   # pack: the frame's mirror plane
YH = 0.958                    # pack: the headboard's front face (deck stretch anchor)
UNDER_Z = 0.48                # rails' and slats' underside above the floor
MAT_TOP = TOP - 0.02          # mattress top under the blanket
DRAPE_Z = 0.46                # the cover's hem

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(PACK / "Meshes/BED_01.fbx"))
src = [o for o in bpy.data.objects if o.type == "MESH"][0]
me0 = src.data.copy(); me0.transform(src.matrix_world)
bm = bmesh.new(); bm.from_mesh(me0)
bm.verts.ensure_lookup_table(); bm.faces.ensure_lookup_table()
for v in bm.verts:
    v.co.z -= FLOOR
uv = bm.loops.layers.uv.active

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


G = {k: [] for k in ("post_h", "post_f", "fin_h", "fin_f", "headboard", "footboard", "rail", "cover", "slat", "mattress", "pillow", "pillow_drop")}
for c in isl:
    lo, hi = bbox(c); n = len(c)
    if n == 100:
        G["post_h" if lo[1] > 0.5 else "post_f"].append(c)
    elif n == 408:
        G["fin_h" if lo[1] > 0.5 else "fin_f"].append(c)
    elif n == 44:
        G["rail"].append(c)
    elif n in (6, 2):
        G["slat"].append(c)
    elif n == 170:
        G["mattress"].append(c)
    elif n > 2500:
        G["cover"].append(c)
    elif lo[1] > 0.9 and n > 500:
        G["headboard"].append(c)
    elif hi[1] < -0.6 and n > 500:
        G["footboard"].append(c)
    elif lo[1] > 0.5 and lo[2] > 0.4:
        G["pillow" if lo[0] < XC - 0.3 else "pillow_drop"].append(c)
    else:
        raise SystemExit(f"unclassified island {n} {lo} {hi}")
assert [len(G[k]) for k in ("post_h", "post_f", "fin_h", "fin_f", "rail", "headboard", "footboard", "pillow", "cover", "mattress")] == [2, 2, 2, 2, 2, 1, 1, 1, 1, 1], {k: len(v) for k, v in G.items()}

lo_p, hi_p = bbox(G["post_h"][0] + G["post_h"][1])
W0 = hi_p[0] - lo_p[0]; CUT = W0 - W_OUT; XC1 = XC - CUT / 2
L0 = bbox(G["post_h"][0])[1][1] - bbox(G["post_f"][0])[0][1]
DY = L_OUT - L0
yf_in = bbox(G["footboard"][0])[1][1]                        # footboard's inner face
KY = (YH - (yf_in - DY)) / (YH - yf_in)
head_top0 = bbox(G["fin_h"][0])[1][2]; foot_top0 = bbox(G["fin_f"][0])[1][2]
DH, DF = HEAD - head_top0, FOOT - foot_top0
mlo, mhi = bbox(G["mattress"][0]); slo, shi = bbox(sum(G["slat"], []))
rlo, rhi = bbox(G["rail"][0] + G["rail"][1])
clo, chi = bbox(G["cover"][0])
HALF_IN = (W_OUT - 2 * 0.104) / 2 - 0.002                     # mattress half width: inside the posts' inner faces
HALF_OUT = W_OUT / 2 - 0.003                                  # the drape: inside the posts' outer faces
A_M = mhi[0] - XC; A_C = chi[0] - XC
print(f"cut {CUT:.3f} (outer {W0:.3f} -> {W_OUT:.3f}), DY {DY:.3f} (stretch x{KY:.3f}), head +{DH:.3f}, foot +{DF:.3f}")


def soft_x(x):
    d = x - XC; a = abs(d); s = 1 if d >= 0 else -1
    a2 = a * HALF_IN / A_M if a <= A_M else HALF_IN + (a - A_M) * (HALF_OUT - HALF_IN) / (A_C - A_M)
    return XC1 + s * a2


def rigid_x(x):
    return x - CUT if x > XC else x


def deck_y(y):
    return YH + (y - YH) * KY


def lin(z, a0, a1, b0, b1):
    return b0 + (z - a0) * (b1 - b0) / (a1 - a0)


def cover_z(z):
    m0 = mhi[2]
    return z + (MAT_TOP - m0) if z >= m0 else lin(z, clo[2], m0, DRAPE_Z, MAT_TOP)


def post_z(dz, zcut):
    return lambda z: z + dz if z > zcut else z


MAPS = {  # group -> (x, y, z) per vertex
    "post_h": (rigid_x, lambda y: y, post_z(DH, 0.55)),
    "fin_h": (rigid_x, lambda y: y, lambda z: z + DH),
    "post_f": (rigid_x, lambda y: y - DY, post_z(DF, 0.40)),
    "fin_f": (rigid_x, lambda y: y - DY, lambda z: z + DF),
    "headboard": (rigid_x, lambda y: y, post_z(DH, 0.55)),
    "footboard": (rigid_x, lambda y: y - DY, post_z(DF, 0.45)),
    "rail": (rigid_x, deck_y, lambda z: lin(z, rlo[2], rhi[2], UNDER_Z, UNDER_Z + 0.08)),
    "slat": (soft_x, deck_y, lambda z: lin(z, slo[2], shi[2], UNDER_Z, UNDER_Z + 0.028)),
    "mattress": (soft_x, deck_y, lambda z: lin(z, mlo[2], mhi[2], UNDER_Z + 0.028, MAT_TOP)),
    "cover": (soft_x, deck_y, cover_z),
    "pillow": (lambda x, d=XC1 - (bbox(G["pillow"][0])[0][0] + bbox(G["pillow"][0])[1][0]) / 2: x + d, lambda y: y, lambda z: z + MAT_TOP - mhi[2]),
}
CUT_GROUPS = {"headboard", "footboard"}        # the boards span the middle: cut, slide, weld


Y_BLANKET = deck_y((clo[1] + chi[1]) / 2 - 0.05)   # the green blanket covers the cover's foot side of this line (Marina 561: ~ the foot half)


def build(groups):
    out = bmesh.new(); ouv = out.loops.layers.uv.new("UVMap"); mats = []
    for g in groups:
        for comp in G[g]:
            sub = bmesh.new(); suv = sub.loops.layers.uv.new("UVMap"); vm = {}
            for f in comp:
                vs = []
                for v in f.verts:
                    if v not in vm:
                        vm[v] = sub.verts.new(v.co)
                    vs.append(vm[v])
                try:
                    nf = sub.faces.new(vs)
                except ValueError:
                    continue
                for l0, l1 in zip(f.loops, nf.loops):
                    l1[suv].uv = l0[uv].uv
            if g in CUT_GROUPS:
                xa, xb = XC - CUT / 2, XC + CUT / 2
                for xp, keep_lo in ((xa, True), (xb, False)):
                    geom = sub.verts[:] + sub.edges[:] + sub.faces[:]
                    bmesh.ops.bisect_plane(sub, geom=geom, plane_co=(xp, 0, 0), plane_no=(1, 0, 0))
                sub.faces.ensure_lookup_table()
                bmesh.ops.delete(sub, geom=[f for f in sub.faces if xa + 1e-5 < f.calc_center_median().x < xb - 1e-5], context="FACES")
                bmesh.ops.delete(sub, geom=[v for v in sub.verts if not v.link_faces], context="VERTS")
                for v in sub.verts:
                    if v.co.x > XC:
                        v.co.x -= CUT
                seam = [v for v in sub.verts if abs(v.co.x - xa) < 1e-4]
                bmesh.ops.remove_doubles(sub, verts=seam, dist=1e-4)
                fx = lambda x: x
            else:
                fx = MAPS[g][0]
            _, fy, fz = MAPS[g]
            for v in sub.verts:
                v.co.x, v.co.y, v.co.z = fx(v.co.x), fy(v.co.y), fz(v.co.z)
            if g == "cover":   # a straight blanket edge: split the cloth's faces on the line (face-wise it came out sawtoothed)
                bmesh.ops.bisect_plane(sub, geom=sub.verts[:] + sub.edges[:] + sub.faces[:], plane_co=(0, Y_BLANKET, 0), plane_no=(0, 1, 0))
            vm2 = {v: out.verts.new(v.co) for v in sub.verts}
            for f in sub.faces:
                nf = out.faces.new([vm2[v] for v in f.verts])
                for l0, l1 in zip(f.loops, nf.loops):
                    l1[ouv].uv = l0[suv].uv
                c0 = f.calc_center_median()
                mats.append(1 if g == "cover" and c0.y < Y_BLANKET else 0)
            sub.free()
    return out, mats


wood_bm, _ = build(["post_h", "fin_h", "post_f", "fin_f", "headboard", "footboard", "rail", "slat"])
soft_bm, soft_mats = build(["mattress", "cover", "pillow"])

T = PACK / "Textures/HDRP"
OUT.parent.mkdir(parents=True, exist_ok=True)
alb = bpy.data.images.load(str(T / "BED_01_ALBEDO.png"))
nrm = bpy.data.images.load(str(T / "BED_01_NORMAL.png")); nrm.colorspace_settings.name = "Non-Color"
grn = alb.copy(); px = np.array(grn.pixels[:]).reshape(-1, 4)
px[:, :3] *= (0.30, 0.48, 0.36)          # pack's beige cover -> Marina 553/561's green blanket (sRGB-space multiply)
grn.pixels[:] = px.ravel(); grn.filepath_raw = str(OUT.parent / "BuzzBed_Green.png"); grn.file_format = "PNG"; grn.save()


def mat(name, img, rough):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    ti = nt.nodes.new("ShaderNodeTexImage"); ti.image = img; nt.links.new(ti.outputs["Color"], b.inputs["Base Color"])
    tn = nt.nodes.new("ShaderNodeTexImage"); tn.image = nrm
    nm = nt.nodes.new("ShaderNodeNormalMap"); nt.links.new(tn.outputs["Color"], nm.inputs["Color"]); nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    b.inputs["Roughness"].default_value = rough
    return m


root = bpy.data.objects.new("BuzzBed", None); bpy.context.scene.collection.objects.link(root)
wood_me = bpy.data.meshes.new("BuzzBedFrame"); wood_bm.to_mesh(wood_me); wood_me.materials.append(mat("BB_Wood", alb, 0.55))
soft_me = bpy.data.meshes.new("BuzzBedBedding"); soft_bm.to_mesh(soft_me)
soft_me.materials.append(mat("BB_Sheet", alb, 0.9)); soft_me.materials.append(mat("BB_Blanket", grn, 0.95))
for p, mi in zip(soft_me.polygons, soft_mats):
    p.material_index = mi
for nme, me in (("BedFrame", wood_me), ("Bedding", soft_me)):
    o = bpy.data.objects.new(nme, me); bpy.context.scene.collection.objects.link(o); o.parent = root
    for p in me.polygons:
        p.use_smooth = True
bpy.data.objects.remove(src)
allv = np.array([v.co[:] for me in (wood_me, soft_me) for v in me.vertices])
under = min(v.co.z for v in soft_me.vertices if abs(v.co.x - XC1) < HALF_IN - 0.05 and v.co.z > 0.2)
print("built size (x w, y l, z h):", np.ptp(allv, 0).round(3), "min", allv.min(0).round(3), "target", round(W_OUT, 3), round(L_OUT, 3), HEAD)
print(f"under-bed: rails/slats {UNDER_Z}, mattress underside {under:.3f}, drape hem {DRAPE_Z}")
bpy.ops.export_scene.gltf(filepath=str(OUT), export_format="GLB", export_yup=True)
print("wrote", OUT)
