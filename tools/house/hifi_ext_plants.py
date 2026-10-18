"""hifi_ext_plants: the front beds' plants (exterior polish, Oct 18 2026, TRIAL; decoration) from spec/dressing/exterior_plants.json.

Film 4382: clipped round evergreens, ball topiaries before the shutters, white urns at the foot of the steps, low shrubs in the lower
bed. Poly Haven has no clipped shrub, so those are generated: a noise-lumped ellipsoid (EP_Leaf) with snow on the up-facing lumps
(EP_Snow); leaf cards EP_Leaf/EP_LeafB over a dark core EP_Core. The corner evergreens are Poly Haven fir_sapling (CC0; sfm-work/polyhaven, tools/house/polyhaven_fetch.py), decimated.
Each plant is one root object named P<i>_<kind> at its spec (x, 0, z); SpecGreybox.Shell drops it onto the bed with a ray.

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P tools/house/hifi_ext_plants.py
  -> unity/HomeAlone/Assets/Models/Foyer/ExteriorPlants.glb
"""
import json
import math
import random
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector, noise

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "unity/HomeAlone/Assets/Models/Foyer/ExteriorPlants.glb"
PH = ROOT / "sfm-work/polyhaven"
PL = json.loads((ROOT / "spec/dressing/exterior_plants.json").read_text())["plants"]

bpy.ops.wm.read_factory_settings(use_empty=True)


def mat(name, rgb, rough):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]; b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Roughness"].default_value = rough
    return m


CORE, LEAF, LEAF2 = mat("EP_Core", (0.012, 0.025, 0.010), 0.9), mat("EP_Leaf", (0.030, 0.070, 0.025), 0.6), mat("EP_LeafB", (0.050, 0.095, 0.030), 0.6)
SNOW, STEM, STONE = mat("EP_Snow", (0.85, 0.87, 0.90), 0.7), mat("EP_Stem", (0.12, 0.08, 0.05), 0.9), mat("EP_Stone", (0.80, 0.78, 0.74), 0.7)


def blob(name, w, h, y0, seed, snow=True):
    """A clipped shrub: a dark core (icosphere scaled to w x h, lumped by two noise octaves, base flattened) covered in small leaf
    cards (two greens, tilted off the surface: the clipped-boxwood texture at Kevin's eye); the up-facing leaves of the upper lumps
    carry snow (film 4382: a light dusting)."""
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=3, radius=1.0)
    off = Vector((seed * 7.1, seed * 3.3, seed * 1.7))
    for v in bm.verts:
        n = v.co.normalized()
        d = 1 + 0.10 * noise.noise(n * 2.2 + off) + 0.05 * noise.noise(n * 7.0 + off)
        v.co = Vector((n.x * w / 2 * d, n.y * w / 2 * d, max(n.z * h / 2 * d, -h / 2 * 0.85)))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    rnd = random.Random(seed)
    core = [(f.calc_center_median(), f.normal.copy(), f.calc_area(), [v.co.copy() for v in f.verts]) for f in bm.faces]
    for f in bm.faces: f.smooth = True; f.material_index = 0
    leaves = []   # (verts, material index)
    for c, n, a, vs in core:
        k = int(a * 900 + rnd.random())   # ~900 leaves a square metre
        for _ in range(k):
            u, v = rnd.random(), rnd.random()
            if u + v > 1: u, v = 1 - u, 1 - v
            p = vs[0] + (vs[1] - vs[0]) * u + (vs[2] - vs[0]) * v
            nn = (n + Vector((rnd.uniform(-0.8, 0.8), rnd.uniform(-0.8, 0.8), rnd.uniform(-0.8, 0.8)))).normalized()
            t = nn.cross(Vector((0.3, 0.5, 0.8))).normalized(); b = nn.cross(t)
            L, W = rnd.uniform(0.035, 0.06), rnd.uniform(0.018, 0.03)
            q = p + n * rnd.uniform(0.0, 0.03)
            quad = [q - t * L / 2, q + b * W / 2, q + t * L / 2, q - b * W / 2]
            up = nn.z > 0.55 and n.z > 0.45 and noise.noise(p * 5 + off) + rnd.uniform(-0.3, 0.3) > 0.1
            leaves.append((quad, 3 if (snow and up) else (1 if rnd.random() < 0.55 else 2)))
    for quad, mi in leaves:
        f = bm.faces.new([bm.verts.new(x) for x in quad]); f.material_index = mi
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for m in (CORE, LEAF, LEAF2, SNOW): me.materials.append(m)
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
    ob.location.z = y0 + h / 2 * 0.85
    return ob


def stem(name, r, z0, z1):
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=r, depth=z1 - z0, location=(0, 0, (z0 + z1) / 2))
    ob = bpy.context.active_object; ob.name = name; ob.data.materials.append(STEM); return ob


def urn(name, w, h):
    """A white stone urn (film 4382: classical, on a square foot) by revolving a profile."""
    prof = [(0.0, 0), (0.45, 0), (0.45, 0.10), (0.22, 0.14), (0.18, 0.30), (0.40, 0.45), (0.50, 0.85), (0.56, 0.92), (0.56, 1.0), (0.0, 1.0)]
    bm = bmesh.new(); n = 20; rings = []
    for r, z in prof:
        rings.append([bm.verts.new((r * w / 2 * math.cos(2 * math.pi * k / n), r * w / 2 * math.sin(2 * math.pi * k / n), z * h)) for k in range(n)])
    for a, b in zip(rings, rings[1:]):
        for k in range(n):
            bm.faces.new((a[k], a[(k + 1) % n], b[(k + 1) % n], b[k]))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5); bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free(); me.materials.append(STONE)
    ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob); return ob


def fir(name, h, seed):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(next((PH / "fir_sapling").glob("*.gltf"))))
    new = [o for o in bpy.data.objects if o not in before]
    keep = [o for o in new if o.type == "MESH" and o.name.startswith("fir_sapling_a")]
    for o in new:
        if o not in keep and o.type == "MESH": bpy.data.objects.remove(o)
    ob = keep[0]; ob.parent = None; ob.location = (0, 0, 0)
    d = ob.modifiers.new("dec", "DECIMATE"); d.ratio = 0.2
    bpy.context.view_layer.objects.active = ob; bpy.ops.object.modifier_apply(modifier="dec")
    s = h / ob.dimensions.z; ob.scale = (s, s, s); ob.rotation_euler.z = seed
    bpy.ops.object.select_all(action="DESELECT"); ob.select_set(True); bpy.ops.object.transform_apply(scale=True, rotation=True)
    ob.name = name; return ob


for i, p in enumerate(PL):
    name = f"P{i}_{p['kind']}"
    root = bpy.data.objects.new(name, None); bpy.context.scene.collection.objects.link(root)
    parts = []
    if p["kind"] == "round":
        parts.append(blob(name + "_leaf", p["w"], p["h"], 0.0, i))
    elif p["kind"] == "topiary":   # three balls on a stem, the lowest largest (film 4382/2508)
        h, w = p["h"], p["w"]
        parts.append(stem(name + "_stem", 0.025, 0.0, h * 0.85))
        y = 0.05
        for k, (fw, fh) in enumerate(((1.0, 0.24), (0.85, 0.21), (0.66, 0.17))):
            parts.append(blob(f"{name}_ball{k}", w * fw, h * fh, y, i * 10 + k)); y += h * fh + h * 0.10
    elif p["kind"] == "urn":
        parts.append(urn(name + "_urn", p["w"], p["h"]))
        parts.append(blob(name + "_leaf", p["w"] * 0.9, p["h"] * 0.6, p["h"] * 0.9, i))
    elif p["kind"] == "fir":
        parts.append(fir(name + "_fir", p["h"], i * 1.3))
    for o in parts:
        o.parent = root
    root.location = (-p["x"], p["z"], 0.0)   # spec (x, y, z) -> Blender (-x, z, y), as hifi_props

bpy.ops.export_scene.gltf(filepath=str(OUT), export_format="GLB", use_selection=False, export_apply=True)
print("hifi_ext_plants: wrote", OUT, len(PL), "plants")
