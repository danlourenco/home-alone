"""hifi_parents_dressing: the parents' bedroom window dressing and bedside lamps (Oct 18, overnight8, TRIAL 1; changes/2026-10-18-parents-room.json).

Film 2648/2663 (daylight, Kevin on the bed) shows the side window dressed in three layers: a white lace SHEER drawn across the
glass, two straight SIDE PANELS of a slate grey-blue damask to the floor at the outer edges, and a gathered damask SWAG VALANCE across
the top (Marina 188/238 dress hers alike in white swags with grey side drapes: film first for the colour). Built on both windows
(side bank z = 0, front twin x = 8.491). Geometry AUTHORED relative to each casing (no solve of these windows): rod 0.10 m over the
head, panels 0.40 wide hanging 0.12 past the casing to 1 cm off the floor, valance 0.38 deep in front of the panels; the sheer as
Buzz's (hifi_buzz_curtains.py), stool to rod. The cloth is hifi_sheers.py's.

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P tools/house/hifi_parents_dressing.py
  -> unity/HomeAlone/Assets/Models/Foyer/ParentsDressing.glb (spec coordinates above the UPPER floor; SpecGreybox.Curtains places it at 0)
"""
import json
import math
import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hifi_lib import Part, material   # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "unity/HomeAlone/Assets/Models/Foyer/ParentsDressing.glb"
_src = (ROOT / "tools/house/hifi_sheers.py").read_text()
_ns = {"__file__": str(ROOT / "tools/house/hifi_sheers.py"), "__name__": "hifi_sheers_lib"}
exec(compile(_src[:_src.index("\nbpy.ops.wm.read_factory_settings(use_empty=True)")], "hifi_sheers.py", "exec"), _ns)
sheer_panel, SMOOTH, inside = _ns["sheer_panel"], _ns["SMOOTH"], _ns["inside"]

GEO = json.loads((ROOT / "spec/geometry.json").read_text())["upstairs"]
POLY = next(r for r in GEO["rooms"] if r["name"] == "parents_bedroom")["poly"]
WINS = [o for o in json.loads((ROOT / "spec/openings.json").read_text())["openings"] if o["kind"] == "window" and o["between"] == ["parents_bedroom"]]
CASING, WT, ROD_R = 0.07, 0.14, 0.0125
ROD_UP, PANEL_W, OVER, PANEL_D, VAL_H, VAL_D, SHEER_D = 0.10, 0.40, 0.12, 0.09, 0.38, 0.19, 0.045
assert len(WINS) == 2, WINS
BOXES = json.loads((ROOT / "spec/dressing/parents.json").read_text())["boxes"]


def clear(o, a, b):
    """pull the panels' outer edges 1 cm clear of furniture standing in front of the wall (the etagere by the side window)"""
    for bx in BOXES:
        along, across = (bx["z"], bx["x"]) if o["axis"] == "x" else (bx["x"], bx["z"])
        wall = o["c"]
        if min(abs(across[0] - wall), abs(across[1] - wall)) > 0.35 or bx["y"][1] < 0.5:
            continue
        if along[0] - 0.01 < a < along[1] + 0.01:
            a = along[1] + 0.01
        if along[0] - 0.01 < b < along[1] + 0.01:
            b = along[0] - 0.01
    return a, b

drape, rod = Part("Drape", "PB_Damask"), Part("Rod", "PB_Brass")
valance = Part("Valance", "PB_Damask")
voile, vhem = Part("Voile", "SH_Voile"), Part("VoileHem", "SH_Hem")


def frame(o):
    c, m = o["c"], (o["lo"] + o["hi"]) / 2
    if o["axis"] == "x":
        r = 1 if inside(POLY, c + 0.2, m) else -1; face = c + r * WT / 2
        return lambda u, y, d: (face + r * d, y, u)
    r = 1 if inside(POLY, m, c + 0.2) else -1; face = c + r * WT / 2
    return lambda u, y, d: (u, y, face + r * d)


for k, o in enumerate(WINS):
    P = frame(o); lo, hi = o["lo"], o["hi"]
    rod_y = o["head"] + CASING + ROD_UP - 0.07          # the rod 0.10 over the head casing's top
    a0, b1 = clear(o, lo - CASING - OVER, hi + CASING + OVER)
    top = rod_y - ROD_R - 0.008
    for s, (a, b) in ((1, (a0, a0 + PANEL_W)), (-1, (b1 - PANEL_W, b1))):
        sheer_panel(drape, drape, P, a, b, 0.01, top, PANEL_D, 1.7 * k + (0.4 if s > 0 else 2.2), P0=0.11, A0=0.016)
    # the swag valance: a short gathered band across the whole width, in front of the panels' headings
    sheer_panel(valance, valance, P, a0 - 0.02, b1 + 0.02, top - VAL_H, top + 0.02, VAL_D, 3.3 + k, P0=0.16, A0=0.022)
    sheer_panel(voile, vhem, P, lo - CASING + 0.01, hi + CASING - 0.01, o["sill"] + 0.012, top - 0.01, SHEER_D, 4.1 + k, A0=0.008)
    ra, rb = a0 - 0.04, b1 + 0.04
    circ = [(ROD_R * math.cos(t), ROD_R * math.sin(t)) for t in [2 * math.pi * i / 12 for i in range(12)]]
    rod.sweep([P(ra, rod_y, PANEL_D), P(rb, rod_y, PANEL_D)], circ)

# the bedside lamps (film 1610/2648: a brass candlestick base with an urn, a black drum shade; Marina 250 dark shades): turned, on each
# nightstand box's top (spec/dressing/parents.json), centred; overall 0.60 m (shade 0.36-0.58)
brass, shade = Part("LampBrass", "PB_Brass"), Part("LampShade", "PB_Shade")
for bx in BOXES:
    if bx["name"].startswith("parents_nightstand"):
        cx, cz, y0 = (bx["x"][0] + bx["x"][1]) / 2, (bx["z"][0] + bx["z"][1]) / 2, bx["y"][1]
        brass.lathe(cx, cz, y0, [(0, 0.075), (0.012, 0.075), (0.02, 0.05), (0.035, 0.022), (0.06, 0.014), (0.16, 0.016), (0.20, 0.04), (0.24, 0.046),
                                 (0.28, 0.03), (0.30, 0.013), (0.42, 0.011), (0.44, 0.02), (0.46, 0.006), (0.585, 0.004)], n=24)
        shade.lathe(cx, cz, y0, [(0.36, 0.175), (0.58, 0.125)], n=32)
bpy.ops.wm.read_factory_settings(use_empty=True)
M = {"PB_Damask": material("PB_Damask", (0.26, 0.29, 0.36), 0.85), "PB_Brass": material("PB_Brass", (0.75, 0.56, 0.25), 0.3), "PB_Shade": material("PB_Shade", (0.02, 0.02, 0.02), 0.6),
     "SH_Voile": material("SH_Voile", (0.95, 0.94, 0.91), 0.8), "SH_Hem": material("SH_Hem", (0.95, 0.94, 0.91), 0.8)}
coll = bpy.context.scene.collection
root = bpy.data.objects.new("ParentsDressing_HiFi", None); coll.objects.link(root)
for p in (drape, valance, rod, voile, vhem, brass, shade):
    ob = p.build(coll, M); ob.parent = root
    if p in SMOOTH:
        for poly in ob.data.polygons:
            poly.use_smooth = True
OUT.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(OUT), export_format="GLB", export_yup=True, export_apply=True)
print("wrote", OUT, {p.name: len(p.f) for p in (drape, valance, rod, voile, vhem)})
