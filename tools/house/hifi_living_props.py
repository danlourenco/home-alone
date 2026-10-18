"""hifi_living_props: the living room's free-standing Poly Haven (CC0) pieces fitted to their boxes (spec/dressing/living.json), the den's
method and functions (tools/house/hifi_den_props.py: load, fit, recolour; run from its own source up to its build loop):
  sofa_03 -> the film's green velvet sofa (10636), its fabric and leather recoloured green, its wood kept
  ClassicConsole_01 -> the console under the painting (10636), recoloured mahogany
  CoffeeTable_01 -> the coffee table carrying the nutcrackers (10636/5650), its painted turquoise recoloured mahogany
  fancy_picture_frame_01 -> the gilt-framed landscape over the console (10636; a public-domain style landscape, Poly Haven's own)
  mantel_clock_01 -> on the mantel shelf (film 10600 does not show the shelf; Marina f165 has a framed photo there: a generic garniture)
  side_table_tall_01 -> the tall plant stand by the foyer opening (5650); its poinsettia is hifi_living.py's
Downloads in sfm-work/polyhaven/<id> (gitignored); the .glb carries them into the repo (CC0).

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P tools/house/hifi_living_props.py
  -> unity/HomeAlone/Assets/Models/Foyer/LivingProps.glb (placed by SpecGreybox.Living)
"""
import json
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[2]
_src = (ROOT / "tools/house/hifi_den_props.py").read_text()
_ns = {"__file__": str(ROOT / "tools/house/hifi_den_props.py"), "__name__": "hifi_den_props_lib"}
exec(compile(_src[:_src.index("\nfor key, spec in P.items():")], "hifi_den_props.py", "exec"), _ns)   # resets the scene, defines load/fit/recolour
load, fit, recolour = _ns["load"], _ns["fit"], _ns["recolour"]
D = json.loads((ROOT / "spec/dressing/living.json").read_text())
OUT = ROOT / "unity/HomeAlone/Assets/Models/Foyer/LivingProps.glb"
MAHOGANY = (0.10, 0.035, 0.022)                       # linear; the film's dark mahogany (the den's built-in and kitchen used the same family)
# (sofa_03's show-wood is recoloured too: the film's sofa reads green all over)
wood = lambda rgb: (rgb[..., 0] > 1.35 * rgb[..., 1]) & (rgb[..., 0] > 0.08) & (rgb[..., 1] < 0.25)   # sofa_03's carved show-wood

s = D["sofa"]; o = load("sofa_03", "sofa")
recolour(o, "LP_SofaGreen", (0.09, 0.26, 0.13))                          # film 10635/10636: green velvet all over (its show-wood and leather too); was (0.022, 0.10, 0.04): read near-black (user Oct 17)
fit(o, s["x"], s["z"], [0.0, s["h"]], s["front"])
c = D["console"]; o = load("ClassicConsole_01", "console"); recolour(o, "LP_ConsoleMahogany", MAHOGANY)
fit(o, c["x"], c["z"], [0.0, c["h"]], c.get("front", "-z"))
c = D["sofa_console"]; o = load("ClassicConsole_01", "sofaconsole"); recolour(o, "LP_SofaConsoleMahogany", MAHOGANY)   # Marina 458: behind the sofa
fit(o, c["x"], c["z"], [0.0, c["h"]], c["front"])
t = D["coffee_table"]; o = load("CoffeeTable_01", "coffee"); recolour(o, "LP_CoffeeMahogany", MAHOGANY)
fit(o, t["x"], t["z"], [0.0, t["h"]], t.get("front", "+z"))
p = D["painting"]; o = load("fancy_picture_frame_01", "painting")
fit(o, p["x"], [p["z"] - 0.025, p["z"] - 0.005], p["h"], "-z")               # 1.5-2 cm off the den-side wall face (16.07)
for q in o:   # the canvas sat 1.7 mm behind the frame's lip over its edge (Z-fight check): 3% smaller, so the lip no longer covers it
    if q.name.endswith("_canvas"):
        bpy.context.view_layer.update(); c = sum((q.matrix_world @ __import__("mathutils").Vector(v) for v in q.bound_box), __import__("mathutils").Vector()) / 8
        for v in q.data.vertices:
            w = q.matrix_world @ v.co; w.x = c.x + (w.x - c.x) * 0.97; w.z = c.z + (w.z - c.z) * 0.97; v.co = q.matrix_world.inverted() @ w
F = D["fireplace"]; zc = F["centre_z"]; top = F["shelf"]["top"]
o = load("mantel_clock_01", "clock")
for g in [q for q in o if "glass" in q.name.lower()]:   # its glass sat inside the case; squashed 2 cm it passed through it (Clash check)
    bpy.data.objects.remove(g, do_unlink=True); o.remove(g)
fit(o, [1.59, 1.82], [zc - 0.2415, zc + 0.2415], [top + 0.001, top + 0.162], "+x")   # native 0.48 x 0.25 x 0.16, 2 cm shallower to stay on the shelf
st = D["stand"]; (sx, sz), h = st["at"], st["h"]
o = load("side_table_tall_01", "stand"); fit(o, [sx - 0.18, sx + 0.18], [sz - 0.18, sz + 0.18], [0.0, h], "+x")

# Oct 17 (user: "the rest of the living room furniture"): the film's red armchair (10635/10645 = Marina 436-442's red wingback),
# Marina's floral armchair + ottoman right of the fireplace (418/466) and her glass-front china cabinet (458/466)
import numpy as np
CHINTZ = ROOT / "sfm-work/living_fabric/chintz.png"   # tools/house/living_chintz.py: Marina 418's chintz drawn (olive ground, cream blossoms, red buds)
frame = lambda rgb: rgb.mean(2) < 0.16                # ArmChair_01's dark carved frame (kept)


def chintz(objs, new_name, keep=None, repeats=6):
    """re-skin: the diff texture's fabric pixels become the chintz tile (repeats per UV unit), keeping the model's shading"""
    tile = bpy.data.images.load(str(CHINTZ)); tw, th = tile.size
    t = np.array(tile.pixels[:]).reshape(th, tw, 4)[..., :3]
    for o in objs:
        for slot in getattr(o, "material_slots", []):
            m = slot.material
            if m is None:
                continue
            m2 = m.copy(); m2.name = new_name; slot.material = m2
            for n in m2.node_tree.nodes:
                if n.type == "TEX_IMAGE" and n.image and "diff" in n.image.name:
                    img = n.image.copy(); img.name = new_name + "_diff"; W, H = img.size
                    a = np.array(img.pixels[:]).reshape(H, W, 4); rgb = a[..., :3]; lum = rgb.mean(2)
                    mask = np.ones(lum.shape, bool) if keep is None else ~keep(rgb)
                    yy, xx = np.mgrid[0:H, 0:W]
                    pat = t[(yy * repeats * th // H) % th, (xx * repeats * tw // W) % tw]
                    shade = np.clip(lum / max(np.median(lum[mask]), 1e-3), 0, 1.6)[..., None]
                    rgb[mask] = np.clip(pat * shade, 0, 1)[mask]
                    a[..., :3] = rgb; img.pixels = a.ravel().tolist(); img.pack(); n.image = img


q = D["red_chair"]; o = load("ArmChair_01", "redchair"); recolour(o, "LP_ChairRed", (0.42, 0.05, 0.06), keep=frame)
fit(o, q["x"], q["z"], [0.0, q["h"]], q["front"])
def turn(o, deg):
    """turn a fitted piece about its own centre (spec "turn_deg", + = counter-clockwise seen from above in spec x/z): kitty-corner pieces"""
    import mathutils
    if not deg:
        return
    objs = o if isinstance(o, (list, tuple)) else [o]   # load() returns the model's objects: turn them together about their joint centre
    bpy.context.view_layer.update()
    pts = [ob.matrix_world @ mathutils.Vector(v) for ob in objs if hasattr(ob, "bound_box") for v in ob.bound_box]
    c = sum(pts, mathutils.Vector()) / len(pts)
    R = mathutils.Matrix.Translation(c) @ mathutils.Matrix.Rotation(np.radians(-deg), 4, "Z") @ mathutils.Matrix.Translation(-c)
    for ob in objs:
        if ob.parent not in objs:   # children follow their parent
            ob.matrix_world = R @ ob.matrix_world
q = D["floral_chair"]; o = load("ArmChair_01", "floralchair"); chintz(o, "LP_ChairChintz", keep=frame)
fit(o, q["x"], q["z"], [0.0, q["h"]], q["front"]); turn(o, q.get("turn_deg", 0))
q = D["ottoman"]; o = load("Ottoman_01", "ottoman"); chintz(o, "LP_OttomanChintz", repeats=5)
fit(o, q["x"], q["z"], [0.0, q["h"]], q["front"]); turn(o, q.get("turn_deg", 0))
q = D["curio"]; o = load("vintage_cabinet_01", "curio")   # its grey-brown stain read slate in the build: Marina 458's warm brown, brass kept
recolour(o, "LP_CurioBrown", (0.20, 0.11, 0.065), keep=lambda rgb: (rgb[..., 0] > 0.3) & (rgb[..., 1] > 0.2) & (rgb[..., 2] < 0.7 * rgb[..., 1]))   # Oct 18: was (0.26, 0.12, 0.06), read red-mahogany; Marina 458 a darker, browner wood
for ob in o:   # Oct 18 (user: "reads slate-blue"): its near-mirror lacquer reflected the windows' sky; satin like Marina 458 (roughness 0.45 + 0.55 r)
    for slot in getattr(ob, "material_slots", []):
        for n in (slot.material.node_tree.nodes if slot.material else []):
            if n.type == "TEX_IMAGE" and n.image and ("arm" in n.image.name or "rough" in n.image.name) and not n.image.name.startswith("LP_"):
                img = n.image.copy(); img.name = "LP_Curio_" + n.image.name; W, H = img.size
                a = np.array(img.pixels[:]).reshape(H, W, 4); a[..., 1] = 0.45 + 0.55 * a[..., 1]
                if "rough" in n.image.name: a[..., 0] = a[..., 2] = a[..., 1]
                img.pixels = a.ravel().tolist(); img.pack(); n.image = img
fit(o, q["x"], q["z"], [0.0, q["h"]], q["front"])

OUT.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(OUT), export_format="GLB", export_yup=True, export_apply=True)
print("wrote", OUT)
