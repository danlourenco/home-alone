"""hifi_breakfast_table: the breakfast-area table (user, Oct 16: "model the breakfast table as accurately and as well done as ...
the kitchen island and cabinets").

Data: spec/dressing/kitchen.json "breakfast_table" (measured in Marina's big clip, frames 189/197: top edges and ends on the plane
0.75 m up; changes/2026-10-16-breakfast-table.json). Look, film first: film 2528 / 2202 show an oval honey-oak top with a stepped
edge over a deep apron, a dark pedestal under it and eight chairs; Marina models it as an oval double-pedestal table with turned
columns and splayed legs (f189, f197). Built: a superellipse oval top (a racetrack-like oval: straight-ish sides, full ends),
a 1.2 cm step under its edge, an inset apron, two pedestals (turned column, hub, four swept legs on the diagonals).

Faces via hifi_lib (Part.face/lathe/sweep), every visible face >= 1 cm off a same-facing face it overlaps. Material BT_Wood
(SpecGreybox: Poly Haven oak_veneer_01 tinted to film 2528's top, triplanar).

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P tools/house/hifi_breakfast_table.py
  -> unity/HomeAlone/Assets/Models/Foyer/BreakfastTable.glb (spec metres, ground floor at y 0; placed like the cabinets)
"""
import json
import math
import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hifi_lib import Part, material   # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "unity/HomeAlone/Assets/Models/Foyer/BreakfastTable.glb"
T = json.loads((ROOT / "spec/dressing/kitchen.json").read_text())["breakfast_table"]
CX, CZ, A, B, H = T["cx"], T["cz"], T["length"] / 2, T["width"] / 2, T["height"]
NEXP, TT, STEP, AI, AH = T["shape_exponent"], T["top_t"], T["edge_step"], T["apron_inset"], T["apron_h"]
wood = Part("Wood", "BT_Wood")


def oval(a, b, n=72):
    """Superellipse |x/a|^e + |z/b|^e = 1, counter-clockwise in (x, z)."""
    pts = []
    for k in range(n):
        t = 2 * math.pi * k / n; c, s = math.cos(t), math.sin(t)
        pts.append((CX + a * math.copysign(abs(c) ** (2 / NEXP), c), CZ + b * math.copysign(abs(s) ** (2 / NEXP), s)))
    return pts


def prism(p, poly, y0, y1):
    p.face([(x, y1, z) for x, z in poly], (0, 1, 0)); p.face([(x, y0, z) for x, z in poly], (0, -1, 0))
    for (ax, az), (bx, bz) in zip(poly, poly[1:] + poly[:1]):
        dx, dz = bx - ax, bz - az; out = (dz, -dx)                       # CCW in (x, z): outward is (dz, -dx)
        p.face([(ax, y0, az), (bx, y0, bz), (bx, y1, bz), (ax, y1, az)], (out[0], 0, out[1]))


y_top0 = H - TT                                         # underside of the top board
prism(wood, oval(A, B), y_top0 + STEP, H)               # the top board
prism(wood, oval(A - STEP, B - STEP), y_top0, y_top0 + STEP)      # the step under its edge (moulding)
y_ap = y_top0 - AH
prism(wood, oval(A - AI, B - AI), y_ap, y_top0)         # apron

for px in T["pedestals_x"]:
    wood.lathe(px, CZ, 0.12, [(0, 0.075), (0.03, 0.08), (0.06, 0.07), (0.09, 0.05), (0.13, 0.042), (0.20, 0.058), (0.28, 0.066),
                              (0.34, 0.055), (0.40, 0.04), (0.45, 0.034), (y_ap - 0.12 - 0.04, 0.034), (y_ap - 0.12 - 0.02, 0.05), (y_ap - 0.12, 0.05)], n=24)
    R = T["leg_reach"]
    for k in range(T["legs"]):
        ang = math.pi / 4 + k * 2 * math.pi / T["legs"]; c, s = math.cos(ang), math.sin(ang)
        rp = [(0.04, 0.17), (0.12, 0.155), (0.21, 0.11), (0.29, 0.06), (R - 0.03, 0.033), (R, 0.026)]
        wood.sweep([(px + r * c, y, CZ + r * s) for r, y in rp], [(-0.018, -0.025), (0.018, -0.025), (0.018, 0.025), (-0.018, 0.025)])

bpy.ops.wm.read_factory_settings(use_empty=True)
M = {"BT_Wood": material("BT_Wood", (0.67, 0.53, 0.34), 0.35)}
coll = bpy.context.scene.collection
root = bpy.data.objects.new("BreakfastTable", None); coll.objects.link(root)
wood.build(coll, M).parent = root
OUT.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(OUT), export_format="GLB", export_yup=True, export_apply=True)
print("wrote", OUT, len(wood.f), "faces")
