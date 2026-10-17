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
recolour(o, "LP_SofaGreen", (0.022, 0.10, 0.04))                          # film 10636: green velvet all over (its show-wood and leather too)
fit(o, s["x"], s["z"], [0.0, s["h"]], s["front"])
c = D["console"]; o = load("ClassicConsole_01", "console"); recolour(o, "LP_ConsoleMahogany", MAHOGANY)
fit(o, c["x"], c["z"], [0.0, c["h"]], "-z")
t = D["coffee_table"]; o = load("CoffeeTable_01", "coffee"); recolour(o, "LP_CoffeeMahogany", MAHOGANY)
fit(o, t["x"], t["z"], [0.0, t["h"]], "+z")
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

OUT.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(OUT), export_format="GLB", export_yup=True, export_apply=True)
print("wrote", OUT)
