"""purchased_plants: the user's CGTrader plants (Oct 16) fitted to the measured boxes, written ONLY to the gitignored
unity/HomeAlone/Assets/Purchased/PurchasedPlants.glb (CGTrader Royalty Free, no AI: use OK, no redistribution - the public repo
never holds the files or anything derived from them). Without the downloads the build keeps the generated plants.

Sources (unpacked by hand into sfm-work/purchased/, gitignored): "Indoor Decorative Ficus Tree" (ficus/: FBX + textures.rar via
`bsdtar -xf`) and "Poinsettia Gift Plant" (poinsettia/: FBX + pngs).

- FICUS (foyer, film 2677/1690/3888): plant scaled to the measured top (1.894) and crown (0.60; spec/dressing/foyer.json tree_*),
  its planter scaled to the measured pot (0.335 x 0.42) and retinted brass (SpecGreybox.FoyerProps remaps PP_Pot to BrassMat)
- POINSETTIAS: the model's red foil wrap and bow retinted to the film's gold (film 3225/10248), a white-bract copy of its texture
  for the white ones. Full plant (gold foil) where our pot is hidden: the foyer's console / under-console / landing plants
  (foyer_props.json), the front-door pedestals (foyer.json flowers_left/right: white), the den's red (den.json). Foliage only (the
  wrap's faces dropped, seated on the rim) where a generated pot shares its part with other pieces and stays: the den's white in
  its wicker pot, the living room's white on the tall stand (living.json stand; gold pot by hifi_living.py).
Uniform scale by the plant's measured spread (its height follows the model's proportions).

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P tools/house/purchased_plants.py
"""
import json
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "sfm-work/purchased"
OUT = ROOT / "unity/HomeAlone/Assets/Purchased/PurchasedPlants.glb"
FP = json.loads((ROOT / "spec/dressing/foyer_props.json").read_text())
FD = {p["name"]: p for p in json.loads((ROOT / "spec/dressing/foyer.json").read_text())["pieces"] if "x" in p}
DEN = json.loads((ROOT / "spec/dressing/den.json").read_text())["decor"]
LIV = json.loads((ROOT / "spec/dressing/living.json").read_text())["stand"]
mid = lambda r: (r[0] + r[1]) / 2
B = lambda x, y, z: Vector((-x, z, y))      # spec -> Blender (hifi_lib)

bpy.ops.wm.read_factory_settings(use_empty=True)


def bounds(objs):
    pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
    return Vector([min(p[i] for p in pts) for i in range(3)]), Vector([max(p[i] for p in pts) for i in range(3)])


def image(path, name, fn=None, size=None):
    """load an image, optionally transform its pixels (RGBA float array) and resize; written as a NEW image so the .glb carries the
    edited pixels (packing a loaded file packs the file on disk, not the edits: the gold foil exported red, Oct 16)"""
    src = bpy.data.images.load(str(path))
    if size and src.size[0] > size:
        src.scale(size, size)
    w, h = src.size
    a = np.array(src.pixels[:], dtype=np.float32).reshape(h, w, 4)
    if fn:
        a = fn(a)
    im = bpy.data.images.new(name, w, h, alpha=True); im.colorspace_settings.name = src.colorspace_settings.name
    im.pixels.foreach_set(a.ravel()); im.file_format = "PNG"; im.pack()
    bpy.data.images.remove(src); return im


def mat(name, base, normal=None, alpha=False, rough=0.6, metal=0.0):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; bs = nt.nodes["Principled BSDF"]
    t = nt.nodes.new("ShaderNodeTexImage"); t.image = base; nt.links.new(t.outputs["Color"], bs.inputs["Base Color"])
    if alpha:
        nt.links.new(t.outputs["Alpha"], bs.inputs["Alpha"])
        try:
            m.blend_method = "CLIP"            # glTF alphaMode MASK
        except (AttributeError, TypeError):
            pass
    if normal:
        n = nt.nodes.new("ShaderNodeTexImage"); n.image = normal; n.image.colorspace_settings.name = "Non-Color"
        nm = nt.nodes.new("ShaderNodeNormalMap"); nt.links.new(n.outputs["Color"], nm.inputs["Color"]); nt.links.new(nm.outputs["Normal"], bs.inputs["Normal"])
    bs.inputs["Roughness"].default_value = rough; bs.inputs["Metallic"].default_value = metal
    return m


def hue_mask(a):
    """reddish pixels (the bracts, the wrap, the bow): R well above G and B"""
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    return (r > 0.08) & (r > 1.6 * g) & (r > 1.4 * b)


def to_gold(a):
    m = hue_mask(a); lum = a[..., 0][m] / max(np.percentile(a[..., 0][m], 90), 1e-3)
    a[..., :3][m] = np.clip(np.array([0.93, 0.74, 0.36])[None, :] * lum[:, None], 0, 1); return a


def brighter_red(a):   # the model's bracts (sRGB ~113/19/15) are darker than the film's (3225, 11966): x1.6 on the red pixels
    m = hue_mask(a); a[..., :3][m] = np.clip(a[..., :3][m] * np.array([1.6, 1.25, 1.25])[None, :], 0, 1); return a


def to_white(a):
    m = hue_mask(a); lum = a[..., 0][m] / max(np.percentile(a[..., 0][m], 90), 1e-3)
    a[..., :3][m] = np.clip(np.array([0.93, 0.92, 0.86])[None, :] * (0.55 + 0.45 * lum)[:, None], 0, 1); return a


# ------------------------------------------------------------------ poinsettia source
P = SRC / "poinsettia"
tex, nrm = P / "Texture_Poinsettia Gift Plant.png", P / "Normals_Poinsettia Gift Plant.png"
NRM = None   # its normal map lit the bracts as if facing away (black): shading from the mesh normals
M_RED = mat("PP_BractRed", image(tex, "PP_PoinRed", brighter_red), NRM)          # opaque: its alpha is 255 throughout, and an alpha link exported BLEND (black bracts)
M_WHITE = mat("PP_BractWhite", image(tex, "PP_PoinWhite", to_white), NRM)
M_FOIL = mat("PP_Foil", image(tex, "PP_PoinFoil", to_gold, size=1024), NRM, rough=0.3, metal=0.7)

before = set(bpy.data.objects)
bpy.ops.import_scene.fbx(filepath=str(P / "FBX_Poinsettia Gift Plant.fbx"))
SRC_POIN = next(o for o in bpy.data.objects if o not in before and o.type == "MESH")
for o in [o for o in bpy.data.objects if o not in before and o is not SRC_POIN]:
    bpy.data.objects.remove(o)
bpy.context.view_layer.update()
basket_slot = next(i for i, s in enumerate(SRC_POIN.material_slots) if "basket" in s.material.name)
bpy.context.view_layer.objects.active = SRC_POIN; SRC_POIN.select_set(True)
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
me = SRC_POIN.data
vz = [v.co.z for p in me.polygons if p.material_index == basket_slot for v in [me.vertices[i] for i in p.vertices]]
BASKET_TOP = max(vz)
SRC_POIN.hide_render = True; SRC_POIN.hide_viewport = True


def poinsettia(name, cx, cz, y0, spread, white, foliage_only=False):
    o = SRC_POIN.copy(); o.data = SRC_POIN.data.copy(); o.name = name; bpy.context.scene.collection.objects.link(o)
    o.hide_render = False; o.hide_viewport = False
    flower = M_WHITE if white else M_RED
    o.data.materials.clear()
    o.data.materials.append(flower); o.data.materials.append(M_FOIL)
    uv = o.data.uv_layers.active.data
    for p in o.data.polygons:   # the wrap (atlas bottom-left) and the bow (top-right) take the gold foil; the model splits the wrap across both its materials
        u = sum(uv[l].uv.x for l in p.loop_indices) / p.loop_total; v = sum(uv[l].uv.y for l in p.loop_indices) / p.loop_total
        p.material_index = 1 if (p.material_index == basket_slot or (u < 0.45 and v < 0.55) or (u >= 0.5 and v > 0.6)) else 0
    if foliage_only:   # drop the wrap and whatever sits below its rim (it would show through our own pot)
        import bmesh
        bm = bmesh.new(); bm.from_mesh(o.data)
        bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index == 1 or max(v.co.z for v in f.verts) < BASKET_TOP - 0.003], context="FACES")
        bm.to_mesh(o.data); bm.free()
        o.data.materials.pop(index=1)
    bpy.context.view_layer.update()
    lo, hi = bounds([o]); s = spread / max(hi.x - lo.x, hi.y - lo.y)
    o.scale = (s, s, s); bpy.context.view_layer.update(); lo, hi = bounds([o])
    base = 0.01 if foliage_only else 0.0     # the trimmed foliage starts at the wrap's rim: set it 1 cm into our pot's rim (y0)
    o.location += B(cx, y0 - base, cz) - Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z))
    bpy.context.view_layer.update(); lo, hi = bounds([o])
    print(f"  {name}: spec x {-hi.x:.2f}..{-lo.x:.2f} z {lo.y:.2f}..{hi.y:.2f} y {lo.z:.2f}..{hi.z:.2f}")
    return o



for key, q in FP["plants"].items():
    if q["bract"] in ("red", "white"):
        cx, cz = q["at"]
        if "wall_x" in q:   # keep clear of the frame on that wall: the model can't be trimmed like the generated leaves
            cx = max(cx, q["wall_x"] + 0.02 + q["spread"] / 2)
        poinsettia("Poin_" + key, cx, cz, q["y0"], q["spread"], q["bract"] == "white")
for side in ("left", "right"):   # the front-door pedestals: white (film 10248/9358); 0.42 across, 1 cm off the front wall (x 8.948)
    st = FD[f"flower_stand_{side}"]; sp = 0.42
    poinsettia(f"Poin_pedestal_{side}", min(mid(st["x"]), 8.948 - 0.01 - sp / 2), mid(st["z"]), st["y"][1], sp, True)
r, w = DEN["poinsettia_red"], DEN["poinsettia_white"]   # side by side at their measured spots: both scaled so they don't overlap (a clash, Oct 17)
k = min(1.0, 0.97 * ((r["at"][0] - w["at"][0]) ** 2 + (r["at"][1] - w["at"][1]) ** 2) ** 0.5 / (r["r"] + w["r"]))
poinsettia("Poin_den_red", r["at"][0], r["at"][1], 0.0, 2 * r["r"] * k, False)
poinsettia("Poin_den_white", w["at"][0], w["at"][1], 0.19, 2 * w["r"] * k, True, foliage_only=True)
poinsettia("Poin_living_white", LIV["at"][0], LIV["at"][1], LIV["h"] + 0.15, 0.48, True, foliage_only=True)

# ------------------------------------------------------------------ ficus
F = SRC / "ficus"; T = F / "textures"
before = set(bpy.data.objects)
bpy.ops.import_scene.fbx(filepath=str(F / "Indoor Decorative Ficus Tree .fbx"))
new = [o for o in bpy.data.objects if o not in before]
meshes = [o for o in new if o.type == "MESH"]
plant = max(meshes, key=lambda o: len(o.data.polygons)); pot = next(o for o in meshes if o is not plant)
for o in meshes:
    o.select_set(True)
bpy.context.view_layer.objects.active = plant
for o in new:
    if o.type != "MESH":
        for c in o.children:
            c.parent = None
bpy.ops.object.parent_clear(type="CLEAR_KEEP_TRANSFORM"); bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)


def leaf_rgba(a):   # the diffuse with the opacity map as alpha
    op = bpy.data.images.load(str(T / "leaf_002_Opacity.jpg")); op.scale(a.shape[1], a.shape[0])
    o = np.array(op.pixels[:], dtype=np.float32).reshape(a.shape)[..., 0]; a[..., 3] = o; return a


M_LEAF = mat("PP_FicusLeaf", image(T / "leaf_002_diff.jpg", "PP_FicusLeafRGBA", leaf_rgba, size=1024), image(T / "leaf_002_Normal.jpg", "PP_FicusLeafN", size=1024), alpha=True, rough=0.55)
M_BARK = mat("PP_FicusBark", image(T / "Bark_01.png", "PP_Bark", size=1024), image(T / "Bark_01_Normal.png", "PP_BarkN", size=1024), rough=0.85)
M_SOIL = mat("PP_Soil", image(T / "3DC_Tierra_01_Albedo_2K.jpg", "PP_SoilA", size=512), rough=0.95)
M_POT = mat("PP_Pot", image(T / "3DC_Maceta_Mod_14_Albedo_2K.jpg", "PP_PotA", size=512), rough=0.4)
for o in (plant, pot):
    for s in o.material_slots:
        n = s.material.name.lower() if s.material else ""
        s.material = M_SOIL if "soil" in n else M_POT if ("pot" in n or "inpot" in n) else M_BARK if "002" in n else M_LEAF if "005" in n else M_POT
tp, tc = FD["tree_pot"], FD["tree_crown"]; cx, cz = mid(tp["x"]), mid(tp["z"])
lo, hi = bounds([pot]); sxy, sz = (tp["x"][1] - tp["x"][0]) / max(hi.x - lo.x, hi.y - lo.y), tp["y"][1] / (hi.z - lo.z)
pot.scale = (sxy, sxy, sz); bpy.context.view_layer.update(); lo, hi = bounds([pot])
pot.location += B(cx, 0.0, cz) - Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z)); bpy.context.view_layer.update()
soil = tp["y"][1] - 0.04
lo, hi = bounds([plant]); s = (tc["y"][1] - soil) / (hi.z - lo.z); crown = tc["x"][1] - tc["x"][0]
w = max(hi.x - lo.x, hi.y - lo.y) * s; h = min(1.0, crown / w)          # height by the measured top, crown squeezed to the measured 0.60
plant.scale = (s * h, s * h, s); bpy.context.view_layer.update(); lo, hi = bounds([plant])
plant.location += B(cx, soil, cz) - Vector(((lo.x + hi.x) / 2, (lo.y + hi.y) / 2, lo.z)); bpy.context.view_layer.update()
pot.name, plant.name = "Ficus_Pot", "Ficus_Tree"
lo, hi = bounds([plant, pot])
print(f"  ficus: crown {hi.x - lo.x:.2f} x {hi.y - lo.y:.2f}, top {hi.z:.2f} (squeeze {h:.2f}); faces {len(plant.data.polygons) + len(pot.data.polygons)}")

bpy.data.objects.remove(SRC_POIN)
for o in list(bpy.data.objects):
    if o.type != "MESH":
        bpy.data.objects.remove(o)
for o in bpy.data.objects:   # the FBX vertex colours crash glTFast's import (a job-dependency error, Oct 16); the textures carry the colour
    while o.data.color_attributes:
        o.data.color_attributes.remove(o.data.color_attributes[0])
OUT.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(OUT), export_format="GLB", export_yup=True, export_apply=True)
print("wrote", OUT)
