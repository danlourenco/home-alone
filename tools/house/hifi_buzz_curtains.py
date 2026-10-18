"""hifi_buzz_curtains: Buzz's drapes (Buzz TRIAL 2, decoration). Marina 540-562 s: on each of the room's three windows a brass rod
just over the head casing and two pleated panels hanging straight (not tied back) to the stool, the same on all three; hers are
dark green with no sheer. The FILM (528, 530: the boys at Buzz's window, lamp-lit) shows the panels NEUTRAL GREY (panel / white paper
chroma 0.98/1.03/1.00) over a white sheer drawn across the glass: the film's colourway and sheer are built (film first where they
differ, as the kitchen's sheers), on Marina's measured geometry. Sizes from tools/house/buzz_curtains.py (spec/dressing/
buzz_curtains.json, measured in her solved clip, relative to the casing).
The cloth is hifi_sheers.py's (its functions run from its own source, as hifi_living.py does): one implementation of cloth.

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P tools/house/hifi_buzz_curtains.py
  -> unity/HomeAlone/Assets/Models/Foyer/BuzzCurtains.glb (spec coordinates above the UPPER floor; SpecGreybox.Curtains places it at 0)
"""
import json
import math
import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hifi_lib import Part, material   # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "unity/HomeAlone/Assets/Models/Foyer/BuzzCurtains.glb"
_src = (ROOT / "tools/house/hifi_sheers.py").read_text()
_ns = {"__file__": str(ROOT / "tools/house/hifi_sheers.py"), "__name__": "hifi_sheers_lib"}
exec(compile(_src[:_src.index("\nbpy.ops.wm.read_factory_settings(use_empty=True)")], "hifi_sheers.py", "exec"), _ns)
sheer_panel, SMOOTH, inside = _ns["sheer_panel"], _ns["SMOOTH"], _ns["inside"]

C = json.loads((ROOT / "spec/dressing/buzz_curtains.json").read_text())
GEO = json.loads((ROOT / "spec/geometry.json").read_text())["upstairs"]
POLY = next(r for r in GEO["rooms"] if r["name"] == "buzz_room")["poly"]
WINS = [o for o in json.loads((ROOT / "spec/openings.json").read_text())["openings"] if o["kind"] == "window" and o["between"] == ["buzz_room"]]
BOXES = json.loads((ROOT / "spec/dressing/buzz.json").read_text())["boxes"]
CASING, WT, ROD_R, CLEAR = 0.07, 0.14, 0.0125, 0.01
assert len(WINS) == 3, WINS

green, rod = Part("Drape", "BZ_Drape"), Part("Rod", "BZ_Brass")
voile, vhem = Part("Voile", "SH_Voile"), Part("VoileHem", "SH_Hem")
SHEER_D = 0.045                                          # the sheer's plane: clear of the casing (0.02) and the drape's folds (>= 0.071)


def frame(o):
    """P(u, y, d): u along the wall, y above the upper floor, d into the room from the wall's room face."""
    c, m = o["c"], (o["lo"] + o["hi"]) / 2
    if o["axis"] == "x":      # a wall at x = c, running along z
        r = 1 if inside(POLY, c + 0.2, m) else -1; face = c + r * WT / 2
        return (lambda u, y, d: (face + r * d, y, u)), "z"
    r = 1 if inside(POLY, m, c + 0.2) else -1; face = c + r * WT / 2
    return (lambda u, y, d: (u, y, face + r * d)), "x"


def clear_of_furniture(o, a, b, s, d0, d1, y0):
    """Pull a panel's outer edge back so it stands >= CLEAR from any furniture box in front of the wall (the chest beside the desk-side
    front window: Marina's chest stands right against that window's casing). s: the direction from the outer edge toward the window."""
    P, along = frame(o)
    for bx in BOXES:
        xs, zs, ys = bx["x"], bx["z"], bx["y"]
        lo, hi = (zs if along == "z" else xs)
        q = P(0, 0, (d0 + d1) / 2); off_axis = 0 if along == "z" else 2
        across = (xs if along == "z" else zs)
        if not (across[0] - 0.05 < q[off_axis] < across[1] + 0.05) or ys[1] < y0:
            continue
        if s > 0 and lo - CLEAR < a < hi + CLEAR:      # outer edge at a (low side), box reaching it
            a = hi + CLEAR
        if s < 0 and lo - CLEAR < b < hi + CLEAR:
            b = lo - CLEAR
    return a, b


rod_y, hem_y, dpt, over, pw = C["rod_y"], C["hem_y"], C["panel_depth_m"], C["overhang_m"], C["panel_w_hem_m"]
log = []
for k, o in enumerate(WINS):
    P, along = frame(o)
    lo, hi = o["lo"], o["hi"]
    a0, b1 = lo - CASING - over, hi + CASING + over                       # the panels' outer edges
    top = rod_y - ROD_R - 0.008                                           # the heading hangs from rings just under the rod
    for s, (a, b) in ((1, (a0, a0 + pw)), (-1, (b1 - pw, b1))):
        a2, b2 = clear_of_furniture(o, a, b, s, dpt - 0.035, dpt + 0.035, hem_y)
        if (a2, b2) != (a, b):
            log.append(f"{o['id']}: panel {'low' if s > 0 else 'high'} edge pulled {abs((a2 - a) + (b2 - b)) * 100:.1f} cm clear of furniture")
        sheer_panel(green, green, P, a2, b2, hem_y, top, dpt, 1.3 * k + (0.7 if s > 0 else 2.9), P0=0.10, A0=0.016)
    # the film's sheer: one panel across the glass, casing edge to casing edge, under the drapes, hem at the stool's top + 1.2 cm
    sheer_panel(voile, vhem, P, lo - CASING + 0.01, hi + CASING - 0.01, o["sill"] + 0.012, top - 0.01, SHEER_D, 4.1 + k, A0=0.008)
    # the rod: 4 cm past each panel's outer edge, ball finials, a bracket from the wall at each outer edge
    ra, rb = a0 - 0.04, b1 + 0.04
    circ = [(ROD_R * math.cos(t), ROD_R * math.sin(t)) for t in [2 * math.pi * i / 12 for i in range(12)]]
    rod.sweep([P(ra, rod_y, dpt), P(rb, rod_y, dpt)], circ)
    knob = [(0.02 * math.cos(t), 0.02 * math.sin(t)) for t in [2 * math.pi * i / 12 for i in range(12)]]
    for u in (ra - 0.022, rb + 0.022):   # finials: a 4 cm knob on each end, on the rod's axis
        rod.sweep([P(u - 0.022, rod_y, dpt), P(u + 0.022, rod_y, dpt)], knob)
    for u in (a0 + 0.01, b1 - 0.01):
        p0, p1 = P(u - 0.008, rod_y - 0.03, 0.003), P(u + 0.008, rod_y - ROD_R, dpt)
        rod.box(min(p0[0], p1[0]), max(p0[0], p1[0]), min(p0[1], p1[1]), max(p0[1], p1[1]), min(p0[2], p1[2]), max(p0[2], p1[2]))

bpy.ops.wm.read_factory_settings(use_empty=True)
# film 530: panel / white paper (same lamp) 0.06-0.2 by level, chroma neutral: a mid-dark grey cloth, linear ~0.10 (sRGB ~0.35);
# Unity remaps BZ_Drape to its own cloth material (SpecGreybox.Curtains). Marina's is dark green (linear ~0.07/0.11/0.06).
M = {"BZ_Drape": material("BZ_Drape", (0.095, 0.10, 0.095), 0.85), "BZ_Brass": material("BZ_Brass", (0.75, 0.56, 0.25), 0.3),
     "SH_Voile": material("SH_Voile", (0.95, 0.94, 0.91), 0.8), "SH_Hem": material("SH_Hem", (0.95, 0.94, 0.91), 0.8)}
coll = bpy.context.scene.collection
root = bpy.data.objects.new("BuzzCurtains_HiFi", None); coll.objects.link(root)
for p in (green, rod, voile, vhem):
    ob = p.build(coll, M); ob.parent = root
    if p in SMOOTH:
        for poly in ob.data.polygons:
            poly.use_smooth = True
OUT.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(OUT), export_format="GLB", export_yup=True, export_apply=True)
print("wrote", OUT, {p.name: len(p.f) for p in (green, rod, voile, vhem)}, log)
