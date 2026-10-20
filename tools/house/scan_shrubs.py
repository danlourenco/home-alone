"""scan_shrubs: the front beds' clipped evergreens from a downloaded boxwood (exterior shrubs TRIAL 3, Oct 20; decoration).

User Oct 20 on the generated shrubs (build 8): "smooth painted balls with blotchy snow up close, and too-perfect domes". Source:
arekusandoru.kurobe, "Low poly Bush (Buxus)" (Sketchfab, CC-BY-4.0, CREDITS.md; the user's download, kept in the gitignored
sfm-work/purchased/sketchfab-buxus/): a round boxwood of 1080 triangles, alpha-cut leaf cards over a leaf-textured core, 2K maps.
Film 4382 reads as clipped yews/boxwood: rounded, lumpy, dark. The yew scan the user also downloaded (Luis 3D, "Topiary bush - Bell
shape - Sceaux Park") was reshaped first (cast onto lumpy domes, relief from its luminance): beside this boxwood in a Blender render it
read as a dark rock at Kevin's eye and from 16 m (spec/captures/views/exterior-shrubs-scan/yew_vs_buxus_*.jpg), so it is not used.

Per variant (three), the boxwood is pushed radially by two noise octaves (lumps of +-10-14 %, no two the same dome) and its foot
flattened onto the bed; each plant is a LINKED copy (one mesh per variant: Unity instancing) with its own width, squash, tilt and turn.
One LOD (1080 triangles; an LOD1 would save nothing worth a switch): SpecGreybox.Shell gives each plant an LODGroup that culls it
when tiny. Maps (Unity): bux_albedo.png = the scan's leaves graded to film 4382's near-black olive (alpha kept for the cut-out), a
bux_albedo_snow.png the same with patches of leaves white, on a second material for the crown's up-facing cards; bux_normal.png (the scan's, OpenGL); bux_mask.png (R metal, G AO 0.35-0.75 from the leaf's brightness, B 0,
A smoothness from the scan's roughness). bulbs.json: mini-lights on the outward cards (0.4 cm proud, a quarter 1.5 cm inside,
dimmer) in the generated plant root's local Unity frame (SpecGreybox.Shell lays them).
The generated plants (hifi_ext_plants.py -> ExteriorPlants.glb) stay the fallback: SpecGreybox.Shell hides their foliage (_leaf /
_ball) where this file has a plant, and keeps their stems, urns and the corner firs.

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P tools/house/scan_shrubs.py
  -> unity/HomeAlone/Assets/Purchased/Sketchfab/ScanShrubs/ (gitignored; SS_OUT=<dir> writes elsewhere, e.g. a build overlay)
"""
import json
import math
import os
import random
from pathlib import Path

import bmesh
import bpy
import numpy as np
from mathutils import Vector, noise

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "sfm-work/purchased/sketchfab-buxus/low_poly_bush_buxus.glb"
OUT = Path(os.environ.get("SS_OUT", ROOT / "unity/HomeAlone/Assets/Purchased/Sketchfab/ScanShrubs"))
PL = json.loads((ROOT / "spec/dressing/exterior_plants.json").read_text())["plants"]
OUT.mkdir(parents=True, exist_ok=True)

# film 4382's shrubs: sRGB ~21-30/20-26/9-12 (mean), R:G:B ~1.05:1:0.29 in the film's warm grade, in part shade. The leaves keep the
# scan's light/dark pattern at this mean (linear), a little greener than the film's grade and a little brighter (the film's are shaded)
OLIVE = np.array([0.0072, 0.0080, 0.0009])   # matched to film 4382 in the built view (tools/house/shrub_colour.py), two passes:
# 0.036/0.041/0.014 rendered 2.4x the film's shrub/brick luminance and bluer; 0.0088/0.0097/0.0018 (+ leaf AO, smoothness 0.12) 1.38x,
# still bluer (the sky's fill in the shade and the snow cards; the film's grade is warm)
HUE_PULL = 0.8     # share of the film's hue in each texel (the rest the scan's own green)
SNOW = 0.35        # strongest snow blend on a leaf of the snow map
SNOW_UP, SNOW_SHARE = 0.72, 0.6   # cards whose normal z (either side) passes this on the crown take the snow map, this share of them
BULB_DENSITY = 28  # mini-lights per m2 of outward card area (both card layers count) (build 8: ~52 per m2 of the box ellipsoid)
VARIANTS = {"A": (0.10, 1), "B": (0.14, 2), "C": (0.12, 3)}   # (lump amplitude, seed)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(SRC))
src = [o for o in bpy.data.objects if o.type == "MESH"][0]
mw = src.matrix_world.copy(); src.parent = None; src.matrix_world = mw
bpy.context.view_layer.objects.active = src; src.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
ALB, MR, NRM = [n.image for n in src.data.materials[0].node_tree.nodes if n.type == "TEX_IMAGE"]   # base (+alpha), metal/rough, normal
MAT, MAT_SNOW = bpy.data.materials.new("EP_ScanBux"), bpy.data.materials.new("EP_ScanBuxSnow")


def variant(lump, seed):
    """The boxwood at unit width, foot at z 0, pushed radially by two noise octaves; returns (mesh, height / width)."""
    bm = bmesh.new(); bm.from_mesh(src.data)
    P = np.array([v.co[:] for v in bm.verts]); lo, hi = P.min(0), P.max(0)
    c = Vector(((lo + hi) / 2).tolist()); w = ((hi - lo)[0] + (hi - lo)[1]) / 2
    off = Vector((seed * 5.3, seed * 2.9, seed * 7.7))
    for v in bm.verts:
        d = (Vector(v.co) - c) / w
        n = d.normalized() if d.length > 1e-6 else Vector((0, 0, 1))
        v.co = d * (1 + lump * noise.noise(n * 1.3 + off) + 0.35 * lump * noise.noise(n * 3.1 + off))
    foot = np.percentile([v.co.z for v in bm.verts], 3)
    for v in bm.verts: v.co.z = max(v.co.z, foot) - foot   # the round underside flattened onto the bed
    P = np.array([v.co[:] for v in bm.verts]); lo, hi = P.min(0), P.max(0); w = ((hi - lo)[0] + (hi - lo)[1]) / 2
    for v in bm.verts: v.co = Vector(((v.co.x - (lo[0] + hi[0]) / 2) / w, (v.co.y - (lo[1] + hi[1]) / 2) / w, v.co.z / w))
    bm.normal_update(); rs = random.Random(seed); top = max(v.co.z for v in bm.verts)
    for f in bm.faces:   # the crown's up-facing cards carry the snow map (film 4382: a dusting on the tops)
        if abs(f.normal.z) > SNOW_UP and f.calc_center_median().z > 0.55 * top and rs.random() < SNOW_SHARE: f.material_index = 1
    me = bpy.data.meshes.new(f"SS_bux{seed}"); bm.to_mesh(me); bm.free(); me.materials.append(MAT); me.materials.append(MAT_SNOW)
    return me, (hi[2] - lo[2]) / w


MESH, ASPECT = {}, {}
for vn, (lump, seed) in VARIANTS.items():
    MESH[vn], ASPECT[vn] = variant(lump, seed)
    print(f"scan_shrubs: variant {vn}: {len(MESH[vn].polygons)} tris, aspect {ASPECT[vn]:.2f}")

# --- the maps
W, H = ALB.size
px = np.array(ALB.pixels[:], dtype=np.float32).reshape(H, W, 4)   # bottom row first; a byte image's pixels are sRGB-encoded
lin = lambda c: np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
enc = lambda c: np.where(c <= 0.0031308, c * 12.92, 1.055 * np.clip(c, 0, None) ** (1 / 2.4) - 0.055)
rgb, alpha = lin(px[..., :3]), px[..., 3]
leaf = alpha > 0.5
lum = rgb @ np.array([0.2126, 0.7152, 0.0722]); m = lum[leaf].mean()
albedo = rgb * (1 - HUE_PULL) + lum[..., None] * (OLIVE / OLIVE.mean()) * HUE_PULL
albedo *= OLIVE.mean() / albedo[leaf].mean()


# snow: a second map (the same leaves, patches of them white on their brighter side) on a second material, given per variant to the
# cards that face up on the crown. Not in the one map by UV: the atlas's leaves are shared by cards facing every way (a first try
# whitened leaves all round the sides)
speck = np.kron(np.random.default_rng(4382).random((H // 16, W // 16)), np.ones((16, 16)))[:H, :W]
snow = (speck > 0.45) * np.clip((lum / m - 0.5) / 0.6, 0, 1) * SNOW
snowy = albedo * (1 - snow[..., None]) + np.array([0.80, 0.82, 0.86]) * snow[..., None]
print(f"scan_shrubs: leaf mean albedo {albedo[leaf].mean(0).round(3)} (linear); snow map: {(snow[leaf] > 0.15).mean():.0%} of leaf texels white")


def dilate(img):   # the leaf colour bled into the cut-out, so the mips don't fringe round the leaves
    fill = img.copy(); have = leaf.copy()
    for _ in range(12):
        if have.all(): break
        acc = np.zeros_like(fill); cnt = np.zeros(have.shape, np.float32)
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            sh = np.roll(have, (dy, dx), (0, 1)); acc += np.roll(fill, (dy, dx), (0, 1)) * sh[..., None]; cnt += sh
        new = ~have & (cnt > 0); fill[new] = acc[new] / cnt[new][:, None]; have |= new
    fill[~have] = img[leaf].mean(0)
    return fill


def save(name, rgb_, a=None, srgb=True):
    im = bpy.data.images.new(name, W, H, alpha=True, float_buffer=False)
    im.colorspace_settings.name = "sRGB" if srgb else "Non-Color"   # before the pixels (artist-pipeline trap)
    a = np.ones((H, W), np.float32) if a is None else a
    im.pixels[:] = np.concatenate([np.clip(rgb_, 0, 1), a[..., None]], axis=2).ravel()
    im.filepath_raw = str(OUT / name); im.file_format = "PNG"; im.save()


mr = np.array(MR.pixels[:], dtype=np.float32).reshape(H, W, 4)   # glTF: G roughness, B metal
save("bux_albedo.png", enc(dilate(albedo)), alpha)   # written as sRGB bytes
save("bux_albedo_snow.png", enc(dilate(snowy)), alpha)
save("bux_normal.png", np.array(NRM.pixels[:], dtype=np.float32).reshape(H, W, 4)[..., :3], srgb=False)
ao = np.clip(0.35 + 0.35 * lum / m, 0.35, 0.75)   # a dense shrub's leaves see little sky: build 1's AO 1 let the sky's 4 % specular turn the dark leaves grey-blue
save("bux_mask.png", np.dstack([mr[..., 2], ao, np.zeros((H, W))]), a=1 - mr[..., 1], srgb=False)
for o in list(bpy.data.objects): bpy.data.objects.remove(o)   # the download's own empties too (Sketchfab_model: build 1 logged it as a stray root)

# --- the plants (generated plant root names P<i>_<kind>, hifi_ext_plants.py)
rnd = random.Random(4382)
roots, bulbs, used, ASPECT_OF = [], {}, {}, {}


def inst(root, name, vn, w, h, z0, tilt=5.0):
    """A linked copy of variant vn, w wide (+-jitter, a little out of round), h tall (+-6 %), foot at z0, turned and tilted."""
    ob = bpy.data.objects.new(name, MESH[vn]); bpy.context.scene.collection.objects.link(ob)
    ob.parent = root; ob.location = (0, 0, z0)
    ob.scale = (w * rnd.uniform(0.92, 1.08), w * rnd.uniform(0.88, 1.04), h * rnd.uniform(0.94, 1.06) / ASPECT[vn])
    ob.rotation_euler = (math.radians(rnd.uniform(-tilt, tilt)), math.radians(rnd.uniform(-tilt, tilt)), rnd.uniform(0, 2 * math.pi))
    used[vn] = used.get(vn, 0) + 1; ASPECT_OF[name] = ASPECT[vn]
    return ob


def surface_points(ob):
    """Mini-lights on the cards that face out (not down), area-weighted; [x, y, z, dim] root-local, Unity frame."""
    me = ob.data; M = ob.matrix_world; Rl = ob.parent.matrix_world.inverted()
    c = M @ Vector((0, 0, ASPECT_OF[ob.name] * 0.5)); out = []
    for p in me.polygons:
        vw = [M @ me.vertices[i].co for i in p.vertices]
        nw = (vw[1] - vw[0]).cross(vw[2] - vw[0]); a = nw.length / 2
        if a < 1e-9: continue
        nw.normalize(); ctr = (vw[0] + vw[1] + vw[2]) / 3; rad = (ctr - c).normalized()
        if nw.dot(rad) < 0: nw = -nw   # double-sided cards
        if nw.dot(rad) < 0.3 or nw.z < -0.3 or ctr.z - M.translation.z < 0.1 * ob.dimensions.z: continue
        cnt = a * BULB_DENSITY; cnt = int(cnt) + (rnd.random() < cnt - int(cnt))
        for _ in range(cnt):
            u, v = rnd.random(), rnd.random()
            if u + v > 1: u, v = 1 - u, 1 - v
            dim = rnd.random() < 0.25
            l = Rl @ (vw[0] + (vw[1] - vw[0]) * u + (vw[2] - vw[0]) * v + nw * (-0.015 if dim else 0.004))
            out.append([round(-l.x, 4), round(l.z, 4), round(-l.y, 4), 1 if dim else 0])   # Blender -> Unity (glTF): (-x, z, -y)
    return out


vs = list(VARIANTS)
for i, p in enumerate(PL):
    kind, name = p["kind"], f"P{i}_{p['kind']}"
    if kind == "fir": continue
    root = bpy.data.objects.new(name + "_SCAN", None); bpy.context.scene.collection.objects.link(root)
    root.location = (-p["x"], p["z"], 0.0)   # spec (x, y, z) -> Blender (-x, z, y), as hifi_ext_plants
    root["scan_of"] = name
    if kind == "round":
        inst(root, name + "_leaf_scan", vs[i % 3], p["w"], p["h"], -0.03)
    elif kind == "topiary":   # the generated stem stays; balls where hifi_ext_plants puts them (the lowest largest)
        y = 0.05
        for k, (fw, fh) in enumerate(((1.0, 0.24), (0.85, 0.21), (0.66, 0.17))):
            hh = p["h"] * fh
            inst(root, f"{name}_ball{k}_scan", vs[(i + k) % 3], p["w"] * fw, hh, y - 0.05 * hh, tilt=8); y += hh + p["h"] * 0.10
    elif kind == "urn":   # a small boxwood in the urn's mouth (the generated urn stays)
        inst(root, name + "_leaf_scan", vs[i % 3], p["w"] * 0.9, p["h"] * 0.6, p["h"] * 0.86, tilt=3)
    roots.append(root)
bpy.context.view_layer.update()
for root in roots:
    bulbs[root["scan_of"]] = [q for ob in root.children for q in surface_points(ob)]
(OUT / "bulbs.json").write_text(json.dumps({"what": "scan_shrubs.py: mini-lights per plant, [x, y, z, dim] in the generated plant root's local Unity frame", "plants": bulbs}))

bpy.ops.object.select_all(action="DESELECT")
for o in bpy.data.objects: o.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(OUT / "ScanShrubs.glb"), export_format="GLB", use_selection=True, export_apply=True,
                          export_extras=True, export_tangents=True, export_image_format="NONE")
drawn = sum(len(o.data.polygons) for o in bpy.data.objects if o.type == "MESH")
print(f"scan_shrubs: wrote {OUT / 'ScanShrubs.glb'}: {len(roots)} plants, variants {used}, unique tris {sum(len(m.polygons) for m in MESH.values())}, "
      f"drawn {drawn}, {sum(len(v) for v in bulbs.values())} bulbs")
