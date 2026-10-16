"""hifi_props: real models (Poly Haven, CC0) for the foyer's dressing pieces, placed and sized by spec/dressing/foyer.json.

Why (Oct 15, user: "replace that tree, too. it looks like something out of minecraft"): the dressing pieces are coloured boxes.
Each prop here keeps the measured footprint and height of its dressing piece (Marina 312 s) and swaps the box for a model.

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P tools/house/hifi_props.py
  -> unity/HomeAlone/Assets/Models/Foyer/Tree.glb   (SpecGreybox.HiFiStair places it and hides the tree_* boxes)
Sources (downloaded to sfm-work/polyhaven/, user OK Oct 15): pachira_aquatica_01 (largest of its 4 trees), brass_pot_01.
Coordinates as hifi_foyer.py: a spec point (x, y, z) is Blender (-x, z, y); y is above the ground floor here and the model is
placed under the ground-floor root, so Unity adds the floor height.
"""
import json
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
PH = ROOT / "sfm-work/polyhaven"
OUT = ROOT / "unity/HomeAlone/Assets/Models/Foyer/Tree.glb"
P = {p["name"]: p for p in json.loads((ROOT / "spec/dressing/foyer.json").read_text())["pieces"]}

bpy.ops.wm.read_factory_settings(use_empty=True)


def load(name):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(next((PH / name).glob("*.gltf"))))
    return [o for o in bpy.data.objects if o not in before]


def bounds(objs):
    pts = [o.matrix_world @ Vector(c) for o in objs if o.type == "MESH" for c in o.bound_box]
    return Vector([min(p[i] for p in pts) for i in range(3)]), Vector([max(p[i] for p in pts) for i in range(3)])


def keep_largest_tree(objs):
    """pachira_aquatica_01 holds 4 trees side by side: keep the tallest mesh group (by top-level parent)."""
    roots = [o for o in objs if o.parent is None]
    groups = {r: [r] + [c for c in r.children_recursive] for r in roots}
    best = max(groups, key=lambda r: (lambda b: b[1].z - b[0].z)(bounds(groups[r])) if any(o.type == "MESH" for o in groups[r]) else -1)
    for r, g in groups.items():
        if r is not best:
            for o in g:
                bpy.data.objects.remove(o, do_unlink=True)
    return groups[best]


def place(objs, cx, cz, y0, width=None, height=None):
    """Scale uniformly to the measured width (or height), then stand the group's base centre at spec (cx, y0, cz)."""
    root = bpy.data.objects.new("grp", None); bpy.context.scene.collection.objects.link(root)
    for o in objs:
        if o.parent is None:
            o.parent = root
    lo, hi = bounds(objs); size = hi - lo
    s = (width / max(size.x, size.y)) if width else (height / size.z)
    root.scale = (s, s, s); bpy.context.view_layer.update()
    lo, hi = bounds(objs)
    root.location += Vector((-cx - (lo.x + hi.x) / 2, cz - (lo.y + hi.y) / 2, y0 - lo.z))
    bpy.context.view_layer.update()
    return root, bounds(objs)


pot = P["tree_pot"]; crown = P["tree_crown"]
cx, cz = sum(pot["x"]) / 2, sum(pot["z"]) / 2
pot_objs = load("brass_pot_01")
pot_root, (plo, phi) = place(pot_objs, cx, cz, 0.0, width=pot["x"][1] - pot["x"][0])
pot_root.scale.z *= pot["y"][1] / (phi.z - plo.z)          # the measured pot is taller than the model's: stretch height only
bpy.context.view_layer.update(); plo, phi = bounds(pot_objs)
tree_objs = keep_largest_tree(load("pachira_aquatica_01"))
soil = phi.z - 0.04
tree_root, (tlo, thi) = place(tree_objs, cx, cz, soil, height=crown["y"][1] - soil)
print(f"pot {plo.z:.2f}-{phi.z:.2f} m, {phi.x - plo.x:.2f} wide; tree {tlo.z:.2f}-{thi.z:.2f} m, crown {thi.x - tlo.x:.2f} x {thi.y - tlo.y:.2f}")
OUT.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(OUT), export_format="GLB", export_yup=True, export_apply=True)
print("wrote", OUT)
