"""hall_purchased: the user's CGTrader plants (Oct 16) for the upstairs hall, written ONLY to the gitignored
unity/HomeAlone/Assets/Purchased/HallPlants.glb (CGTrader Royalty Free, no AI: use OK, no redistribution; the public repo never holds
the files or anything derived from them). Without the downloads (sfm-work/purchased/, gitignored) the urns and pot stay empty.

The same sources and treatment as tools/house/purchased_plants.py (the foyer's; not edited here): "Poinsettia Gift Plant" foliage only
(its red foil wrap dropped: our urns and pot hold it), seated 1 cm into the rim, uniform scale by the measured spread; "Indoor
Decorative Ficus Tree" with its own planter (retinted brass in Unity: PP_Pot), scaled to the hall's measured pot and top, crown
squeezed to hall.json's 0.44 m. Positions from spec/dressing/hall.json (urns on their walls, the floor pot, the ficus).

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P tools/house/hall_purchased.py
"""
import json
import math
from pathlib import Path

import bmesh
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "sfm-work/purchased"
OUT = ROOT / "unity/HomeAlone/Assets/Purchased/HallPlants.glb"
D = json.loads((ROOT / "spec/dressing/hall.json").read_text())
B = lambda x, y, z: Vector((-x, z, y))      # spec -> Blender (hifi_lib)

bpy.ops.wm.read_factory_settings(use_empty=True)


def bounds(objs):
    pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
    return Vector([min(p[i] for p in pts) for i in range(3)]), Vector([max(p[i] for p in pts) for i in range(3)])


def image(path, name, size=None):
    im = bpy.data.images.load(str(path)); im.name = name
    if size and im.size[0] > size:
        im.scale(size, size)
    im.pack(); return im


def mat(name, base, normal=None, alpha=False, rough=0.6):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; bs = nt.nodes["Principled BSDF"]
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = base; nt.links.new(t.outputs["Color"], bs.inputs["Base Color"])
    if alpha:
        nt.links.new(t.outputs["Alpha"], bs.inputs["Alpha"])
        try:
            m.blend_method = "CLIP"
        except (AttributeError, TypeError):
            pass
    if normal:
        n = nt.nodes.new("ShaderNodeTexImage"); n.image = normal; n.image.colorspace_settings.name = "Non-Color"
        nm = nt.nodes.new("ShaderNodeNormalMap"); nt.links.new(n.outputs["Color"], nm.inputs["Color"]); nt.links.new(nm.outputs["Normal"], bs.inputs["Normal"])
    bs.inputs["Roughness"].default_value = rough
    return m


def wall_point(wall, s, d):
    w = D["walls"][wall]
    return (w["face"] + w["room_side"] * d, s) if w["axis"] == "x" else (s, w["face"] + w["room_side"] * d)


# ------------------------------------------------------------------ poinsettias (foliage only, in our urns / pot)
P = SRC / "poinsettia"
M_RED = mat("PP_BractRed", image(P / "Texture_Poinsettia Gift Plant.png", "PP_PoinRed"), image(P / "Normals_Poinsettia Gift Plant.png", "PP_PoinNormal", 1024), alpha=True)
before = set(bpy.data.objects)
bpy.ops.import_scene.fbx(filepath=str(P / "FBX_Poinsettia Gift Plant.fbx"))
SRC_POIN = next(o for o in bpy.data.objects if o not in before and o.type == "MESH")
for o in [o for o in bpy.data.objects if o not in before and o is not SRC_POIN]:
    bpy.data.objects.remove(o)
basket = next(i for i, s in enumerate(SRC_POIN.material_slots) if "basket" in s.material.name)
bpy.context.view_layer.objects.active = SRC_POIN; SRC_POIN.select_set(True)
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
me = SRC_POIN.data
TOP = max(me.vertices[i].co.z for p in me.polygons if p.material_index == basket for i in p.vertices)


def poinsettia(name, cx, cz, y0, spread):
    o = SRC_POIN.copy(); o.data = SRC_POIN.data.copy(); o.name = name; bpy.context.scene.collection.objects.link(o)
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index == basket or max(v.co.z for v in f.verts) < TOP - 0.003], context="FACES")
    bm.to_mesh(o.data); bm.free()
    o.data.materials.clear(); o.data.materials.append(M_RED)
    for p in o.data.polygons:
        p.material_index = 0
    bpy.context.view_layer.update()
    lo, hi = bounds([o]); s = spread / max(hi.x - lo.x, hi.y - lo.y); o.scale = (s, s, s)
    bpy.context.view_layer.update(); lo, hi = bounds([o])
    o.location += B(cx, y0 - 0.01, cz) - Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    bpy.context.view_layer.update(); lo, hi = bounds([o])
    print(f"  {name}: x {-hi.x:.2f}..{-lo.x:.2f} z {lo.y:.2f}..{hi.y:.2f} y {lo.z:.2f}..{hi.z:.2f}")


U = D["urns"]
for i, q in enumerate(U["at"]):
    cx, cz = wall_point(q["wall"], q["s"], 0.03 + U["stand_dia"] / 2)
    poinsettia(f"Poin_hall_urn{i + 1}", cx, cz, U["height"] - 0.005, 0.38)   # spread: the film's plants overhang the 0.30 urn (2687: ~1.5x); 0.38 keeps the leaves 1 cm off the wall
fp = D["floor_pot"]; poinsettia("Poin_hall_floor", fp["at"][0], fp["at"][1], fp["height"], fp["spread"])
bpy.data.objects.remove(SRC_POIN)

# ------------------------------------------------------------------ ficus (plant + its planter)
F = SRC / "ficus"; T = F / "textures"
before = set(bpy.data.objects)
bpy.ops.import_scene.fbx(filepath=str(F / "Indoor Decorative Ficus Tree .fbx"))
new = [o for o in bpy.data.objects if o not in before]
meshes = [o for o in new if o.type == "MESH"]
plant = max(meshes, key=lambda o: len(o.data.polygons)); pot = next(o for o in meshes if o is not plant)
for o in new:
    if o.type != "MESH":
        for c in o.children:
            c.parent = None
for o in meshes:
    o.select_set(True)
bpy.context.view_layer.objects.active = plant
bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM"); bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)


def leaf_rgba():
    im = bpy.data.images.load(str(T / "leaf_002_diff.jpg")); im.scale(1024, 1024)
    op = bpy.data.images.load(str(T / "leaf_002_Opacity.jpg")); op.scale(1024, 1024)
    a = list(im.pixels[:]); o_ = op.pixels[:]
    a[3::4] = o_[0::4]; im.pixels.foreach_set(a); im.name = "PP_FicusLeafRGBA"; im.pack(); return im


M_LEAF = mat("PP_FicusLeaf", leaf_rgba(), image(T / "leaf_002_Normal.jpg", "PP_FicusLeafN", 1024), alpha=True, rough=0.55)
M_BARK = mat("PP_FicusBark", image(T / "Bark_01.png", "PP_Bark", 1024), image(T / "Bark_01_Normal.png", "PP_BarkN", 1024), rough=0.85)
M_SOIL = mat("PP_Soil", image(T / "3DC_Tierra_01_Albedo_2K.jpg", "PP_SoilA", 512), rough=0.95)
M_POT = mat("PP_Pot", image(T / "3DC_Maceta_Mod_14_Albedo_2K.jpg", "PP_PotA", 512), rough=0.4)
for o in (plant, pot):
    for s in o.material_slots:
        n = s.material.name.lower() if s.material else ""
        s.material = M_SOIL if "soil" in n else M_POT if ("pot" in n or "inpot" in n) else M_BARK if "002" in n else M_LEAF if "005" in n else M_POT
q = D["ficus"]; cx, cz = q["at"]
lo, hi = bounds([pot]); sxy, sz = q["pot_dia"] / max(hi.x - lo.x, hi.y - lo.y), q["pot_h"] / (hi.z - lo.z)
pot.scale = (sxy, sxy, sz); bpy.context.view_layer.update(); lo, hi = bounds([pot])
pot.location += B(cx, 0.0, cz) - Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z)); bpy.context.view_layer.update()
soil = q["pot_h"] - 0.04
lo, hi = bounds([plant]); s = (q["top"] - soil) / (hi.z - lo.z); w = max(hi.x - lo.x, hi.y - lo.y) * s; h = min(1.0, q["crown"] / w)
plant.scale = (s * h, s * h, s); bpy.context.view_layer.update(); lo, hi = bounds([plant])
plant.location += B(cx, soil, cz) - Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z)); bpy.context.view_layer.update()
pot.name, plant.name = "Ficus_Pot_hall", "Ficus_Tree_hall"
lo, hi = bounds([plant, pot])
print(f"  ficus: x {-hi.x:.2f}..{-lo.x:.2f} z {lo.y:.2f}..{hi.y:.2f}, top {hi.z:.2f} (squeeze {h:.2f})")
for o in list(bpy.data.objects):
    if o.type != "MESH":
        bpy.data.objects.remove(o)
for o in bpy.data.objects:   # FBX vertex colours crash glTFast's import (purchased_plants.py, Oct 16)
    while o.data.color_attributes:
        o.data.color_attributes.remove(o.data.color_attributes[0])
OUT.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(OUT), export_format="GLB", export_yup=True, export_apply=True)
print("wrote", OUT)
