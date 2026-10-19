"""hifi_den_props: the den's free-standing Poly Haven (CC0) pieces fitted to their measured boxes (spec/dressing/den.json "props"),
like hifi_props.py: TV (television_02) in the bookcase's centre bay, the sofa under the end window and the armchair by the living
wall (both sofa_02, recoloured), the round pedestal coffee table (round_wooden_table_01). Each model is turned so its front faces
`front` (spec axis), then scaled per axis into its box (x, z, y), feet on the floor (or its shelf).

Recolours (texture pixels, before export): the sofa's leather to Marina's red (her sofa, Part 1 ~560 s: sRGB ~(110, 15, 20)), the
armchair's to the film's burgundy leather (2926-2941: Kevin's chair), keeping the leather's own shading and the frame's wood; the
TV's silver case to black (film 2877: a black JVC). Downloads (CC0) in sfm-work/polyhaven/<id> (gitignored); the exported .glb
carries them into the repo.

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P tools/house/hifi_den_props.py
  -> unity/HomeAlone/Assets/Models/Foyer/DenProps.glb (placed by SpecGreybox.Den)
"""
import json
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
PH = ROOT / "sfm-work/polyhaven"
OUT = ROOT / "unity/HomeAlone/Assets/Models/Foyer/DenProps.glb"
P = json.loads((ROOT / "spec/dressing/den.json").read_text())["props"]
# the direction each model's front faces as imported (Blender axes; Poly Haven models face -Y), checked on a preview render
NATIVE_FRONT = Vector((0, -1, 0))
SPEC2B = {"+x": Vector((-1, 0, 0)), "-x": Vector((1, 0, 0)), "+z": Vector((0, 1, 0)), "-z": Vector((0, -1, 0))}

bpy.ops.wm.read_factory_settings(use_empty=True)


def load(name, tag):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(next((PH / name).glob("*.gltf"))))
    objs = [o for o in bpy.data.objects if o not in before]
    for o in objs:
        o.name = f"{tag}_{o.name}"
    return objs


def bounds(objs):
    pts = [o.matrix_world @ Vector(c) for o in objs if o.type == "MESH" for c in o.bound_box]
    return Vector([min(p[i] for p in pts) for i in range(3)]), Vector([max(p[i] for p in pts) for i in range(3)])


def fit(objs, x, z, y, front):
    """turn the front to `front`, then scale per axis into the spec box x, z, y (spec -> Blender: (-x, z, y))"""
    root = bpy.data.objects.new("grp", None); bpy.context.scene.collection.objects.link(root)
    for o in objs:
        if o.parent is None:
            o.parent = root
    want = SPEC2B[front]
    root.rotation_euler = (0, 0, NATIVE_FRONT.to_2d().angle_signed(want.to_2d()) * -1)
    bpy.context.view_layer.update()
    for o in objs:   # bake the turn into the meshes so the per-axis scale acts on world axes
        o.select_set(o.type == "MESH")
    bpy.context.view_layer.objects.active = next(o for o in objs if o.type == "MESH")
    bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM")
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    lo, hi = bounds(objs); size = hi - lo
    bx0, bx1 = -x[1], -x[0]; by0, by1 = z[0], z[1]
    sx, sy, sz = (bx1 - bx0) / size.x, (by1 - by0) / size.y, (y[1] - y[0]) / size.z
    for o in objs:
        if o.type == "MESH":
            o.location = Vector(((o.location.x - lo.x) * sx + bx0, (o.location.y - lo.y) * sy + by0, (o.location.z - lo.z) * sz + y[0]))
            o.scale = (o.scale.x * sx, o.scale.y * sy, o.scale.z * sz)
    bpy.context.view_layer.update()
    for o in objs:
        o.select_set(o.type == "MESH")
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    lo, hi = bounds(objs)
    print(f"  fitted: spec x {-hi.x:.3f}..{-lo.x:.3f} z {lo.y:.3f}..{hi.y:.3f} y {lo.z:.3f}..{hi.z:.3f}")
    bpy.data.objects.remove(root)


def recolour(objs, new_name, srgb_target, keep=None, scale_mean=True):
    """copy the model's material + base-colour image, recolour pixels (not matching `keep`) to the target, keeping their shading"""
    for o in objs:
        for slot in getattr(o, "material_slots", []):
            m = slot.material
            if m is None:
                continue
            m2 = m.copy(); m2.name = new_name; slot.material = m2
            for n in m2.node_tree.nodes:
                if n.type == "TEX_IMAGE" and n.image and "diff" in n.image.name:
                    img = n.image.copy(); img.name = new_name + "_diff"
                    a = np.array(img.pixels[:]).reshape(img.size[1], img.size[0], 4)
                    rgb = a[..., :3]; lum = rgb.mean(2)
                    mask = np.ones(lum.shape, bool) if keep is None else ~keep(rgb)
                    ref = np.median(lum[mask]) if scale_mean else 1.0
                    t = np.array(srgb_target)
                    rgb[mask] = np.clip(t[None, :] * (lum[mask] / max(ref, 1e-3))[:, None], 0, 1)
                    a[..., :3] = rgb; img.pixels = a.ravel().tolist(); img.pack(); n.image = img


wood = lambda rgb: (rgb[..., 0] > 1.35 * rgb[..., 1]) & (rgb[..., 0] > 0.08)     # the sofa frame's reddish-brown wood

for key, spec in P.items():   # (the TV is generated now: hifi_den.py, the film's black CRT)
    objs = load(spec["model"], key)
    if key == "coffee_table":
        r = spec["d"] / 2
        fit(objs, [spec["cx"] - r, spec["cx"] + r], [spec["cz"] - r, spec["cz"] + r], [0.0, spec["h"]], "+x")
        continue
    if key == "sofa":
        recolour(objs, "DP_SofaRed", (0.30, 0.035, 0.045), keep=wood)
    if key == "armchair":
        recolour(objs, "DP_ChairBurgundy", (0.135, 0.021, 0.025))   # user Oct 18: darker oxblood (film 2900/2932), was (0.20, 0.035, 0.04); no wood mask: the seat's brown leather read as "wood" and kept its old red (the legs are hidden under the chair)
    if key == "tv":
        recolour(objs, "DP_TvBlack", (0.07, 0.07, 0.07))
    fit(objs, spec["x"], spec["z"], spec["y"], spec["front"])

# the ficus in its wicker basket (film 2868/2877; the basket is hifi_den.py's): Poly Haven pachira_aquatica_01's tallest tree, fitted
f = json.loads((ROOT / "spec/dressing/den.json").read_text())["decor"]["ficus"]
objs = load("pachira_aquatica_01", "ficus")
roots = [o for o in objs if o.parent is None]
groups = {r: [r] + list(r.children_recursive) for r in roots}
best = max(groups, key=lambda r: (lambda b: b[1].z - b[0].z)(bounds(groups[r])) if any(o.type == "MESH" for o in groups[r]) else -1)
for r, g in groups.items():
    if r is not best:
        for o in g:
            bpy.data.objects.remove(o, do_unlink=True)
cx, cz, hc = f["at"][0], f["at"][1], f["crown"] / 2
fit(groups[best], [cx - hc, cx + hc], [cz - hc, cz + hc], [f["basket_h"] - 0.05, f["height"]], "-x")

OUT.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(OUT), export_format="GLB", export_yup=True, export_apply=True)
print("wrote", OUT)
