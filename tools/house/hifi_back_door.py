"""hifi_back_door: the kitchen's back door as the film shows it from inside (walk note 15:06, user decision Oct 16): a 36 x 80 in
leaf, nine-lite upper sash (3 x 3), lock rail, a raised lower panel with a framed flap dog door, red tie-back curtains and a sheer
cafe panel on the inside, brass knob and deadbolt on the latch side, three brass hinges on the left seen from inside (the
sink-wall side, spec +z). It swings in, so the leaf sits near the room face and the stop is on the outside.

Position: the opening `back_door` in spec/house_spec.ground.json (end wall, inside face x = wall_coord_spec, 0.14 m wall),
built from changes/2026-10-16-kitchen-wing.json. Proportions from film 6902 (leaf 323 x 705 px = 0.914 x 2.032 m): top rail to
1.935 m, glazing 0.92-1.935, lock rail 0.734-0.92, bottom rail to 0.265; raised lower panel 2.5 cm in from its frame; dog-door
opening 0.354-0.613 m from the hinge edge, 0.30-0.66 m up; hinges centred 0.32 / 1.05 / 1.79 m; knob 0.89 m, deadbolt 1.05 m.
Every visible face stands >= 1 cm off the one behind it where they overlap (zfight-check); faces via Part.face/box only.

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P tools/house/hifi_back_door.py
  -> unity/HomeAlone/Assets/Models/Foyer/BackDoor.glb (placed by SpecGreybox.HiFiStair like FrontDoor.glb: ground-floor root, spec metres)
"""
import json
import math
import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hifi_lib import Part, material   # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "unity/HomeAlone/Assets/Models/Foyer/BackDoor.glb"
W = next(w for w in json.loads((ROOT / "spec/house_spec.ground.json").read_text())["windows"] if w["name"] == "back_door")
assert W["wall_axis"] == "x", "the back door is on an x = const wall"
XI, (Z0, Z1), HEAD = W["wall_coord_spec"], W["span_spec"], W["head_m"]   # inside face, opening span, opening head
WT = 0.14                                                                  # exterior wall thickness (spec/geometry.json)
X = lambda d: XI - d                                                       # depth d into the wall from the room face
JT, GAP, THR = 0.019, 0.003, 0.010                                         # jamb, leaf clearance, threshold height
ZL0, ZL1 = Z0 + JT + GAP, Z1 - JT - GAP                                    # leaf: latch edge (low z), hinge edge (high z)
YL0, YL1 = THR + 0.001, HEAD - JT - GAP                                    # leaf bottom and top
DL0, DL1 = 0.02, 0.064                                                     # leaf faces (in from the room face; 44 mm leaf)
assert abs((ZL1 - ZL0) - 0.914) < 0.01 and abs((YL1 - YL0) - 2.032) < 0.01, (ZL1 - ZL0, YL1 - YL0)

paint, glass, brass, flap, red, sheer, oak = (Part("Paint", "BD_Paint"), Part("Glass", "BD_Glass"), Part("Brass", "BD_Brass"),
                                              Part("Flap", "BD_Flap"), Part("Curtain", "BD_Curtain"), Part("Sheer", "BD_Sheer"),
                                              Part("Threshold", "BD_Oak"))


def bx(p, d0, d1, y0, y1, z0, z1):
    """A box by depth range (room face = 0, outward +), height and z."""
    p.box(min(X(d0), X(d1)), max(X(d0), X(d1)), y0, y1, z0, z1)


def bx_hole(p, d0, d1, y0, y1, z0, z1, h):
    """The box minus a rectangular hole h = (y0, y1, z0, z1) running through it."""
    hy0, hy1, hz0, hz1 = h
    bx(p, d0, d1, y0, hy0, z0, z1); bx(p, d0, d1, hy1, y1, z0, z1)
    bx(p, d0, d1, hy0, hy1, z0, hz0); bx(p, d0, d1, hy0, hy1, hz1, z1)


def round_x(p, cy, cz, prof, n=16):
    """A turned part on a horizontal axis along x at (cy, cz): prof = [(depth, radius)] from d0 toward the room (depth decreasing)."""
    rings = [[(X(d), cy + r * math.sin(2 * math.pi * k / n), cz + r * math.cos(2 * math.pi * k / n)) for k in range(n)] for d, r in prof]
    for a, b in zip(rings, rings[1:]):
        for k in range(n):
            k2 = (k + 1) % n
            c = [(a[k][j] + b[k2][j]) / 2 for j in range(3)]
            p.face([a[k], a[k2], b[k2], b[k]], (0, c[1] - cy, c[2] - cz))
    out = 1.0 if X(prof[-1][0]) > X(prof[0][0]) else -1.0                   # the direction the part grows (x)
    p.face(rings[0], (-out, 0, 0)); p.face(rings[-1], (out, 0, 0))


# ---- frame: side and head jambs lining the opening, the stop on the outside of the leaf, threshold, brick mould outside
bx(paint, 0.005, WT, 0.0, HEAD, Z0, Z0 + JT); bx(paint, 0.005, WT, 0.0, HEAD, Z1 - JT, Z1)
bx(paint, 0.005, WT, HEAD - JT, HEAD, Z0 + JT, Z1 - JT)
for zs in ((Z0 + JT, Z0 + JT + 0.012), (Z1 - JT - 0.012, Z1 - JT)):                     # stops (outside the leaf)
    bx(paint, DL1, DL1 + 0.035, THR, HEAD - JT, *zs)
bx(paint, DL1, DL1 + 0.035, HEAD - JT - 0.012, HEAD - JT, Z0 + JT + 0.012, Z1 - JT - 0.012)
oak.box(X(WT + 0.03), X(0.005), 0.0, THR, Z0 + JT, Z1 - JT)                            # threshold, 3 cm past the outside face
for z0, z1 in ((Z0 - 0.05, Z0), (Z1, Z1 + 0.05)):                                       # brick mould (outside face of the wall)
    bx(paint, WT, WT + 0.03, 0.0, HEAD + 0.05, z0, z1)
bx(paint, WT, WT + 0.03, HEAD, HEAD + 0.05, Z0, Z1)

# ---- the leaf: stiles 0.115, top rail 1.935-top, lock rail 0.734-0.92, bottom rail to 0.265
ST, GL0, GL1, LR0, BR1 = 0.115, 0.92, 1.935, 0.734, 0.265
bx(paint, DL0, DL1, YL0, YL1, ZL0, ZL0 + ST); bx(paint, DL0, DL1, YL0, YL1, ZL1 - ST, ZL1)
zi0, zi1 = ZL0 + ST, ZL1 - ST
for y0, y1 in ((GL1, YL1), (LR0, GL0), (YL0, BR1)):
    bx(paint, DL0, DL1, y0, y1, zi0, zi1)
# nine-lite sash: glass in the middle of the leaf, 2 cm muntins 5 mm back from both faces
glass.box(X(0.044), X(0.040), GL0, GL1, zi0, zi1)
for k in (1, 2):
    zm, ym = zi0 + k * (zi1 - zi0) / 3, GL0 + k * (GL1 - GL0) / 3
    bx(paint, DL0 + 0.005, 0.040, GL0, GL1, zm - 0.01, zm + 0.01); bx(paint, 0.044, DL1 - 0.005, GL0, GL1, zm - 0.01, zm + 0.01)
    for seg in range(3):                                   # horizontal muntins between the vertical ones (no overlap)
        za = zi0 + seg * (zi1 - zi0) / 3 + (0.01 if seg else 0); zb = zi0 + (seg + 1) * (zi1 - zi0) / 3 - (0.01 if seg < 2 else 0)
        bx(paint, DL0 + 0.005, 0.040, ym - 0.01, ym + 0.01, za, zb); bx(paint, 0.044, DL1 - 0.005, ym - 0.01, ym + 0.01, za, zb)
# lower panel: field 1.5 cm in from both faces, a raised panel 1.2 cm proud of it on each side, the dog door through both
DOG = (0.30, 0.66, ZL1 - 0.613, ZL1 - 0.354)                       # opening: y0, y1, z0, z1 (film 6902)
bx_hole(paint, DL0 + 0.015, DL1 - 0.015, BR1, LR0, zi0, zi1, DOG)
RP = (BR1 + 0.025, LR0 - 0.025, zi0 + 0.025, zi1 - 0.025)
bx_hole(paint, DL0 + 0.003, DL0 + 0.015, RP[0], RP[1], RP[2], RP[3], DOG)
bx_hole(paint, DL1 - 0.015, DL1 - 0.003, RP[0], RP[1], RP[2], RP[3], DOG)
F = 0.03                                                            # the flap's frame, both faces, 1.3 cm proud of the raised panel
fo = (DOG[0] - F, DOG[1] + F, DOG[2] - F, DOG[3] + F)
bx_hole(flap, DL0 - 0.010, DL0 + 0.003, *fo, DOG); bx_hole(flap, DL1 - 0.003, DL1 + 0.010, *fo, DOG)
bx(flap, 0.040, 0.046, DOG[0] + 0.005, DOG[1] - 0.005, DOG[2] + 0.005, DOG[3] - 0.005)      # the flap, hanging in the middle
# hardware: three hinges on the room face at the hinge edge, knob and deadbolt on the latch side (both faces)
for yc in (0.32, 1.05, 1.79):
    bx(brass, DL0 - 0.006, DL0, yc - 0.045, yc + 0.045, ZL1 - 0.03, ZL1 + GAP)
for face, sgn in ((DL0, 1), (DL1, -1)):
    d = lambda t: face - sgn * t                                   # t = distance out from the leaf face
    round_x(brass, 0.89, ZL0 + 0.06, [(d(0), 0.03), (d(0.008), 0.03), (d(0.01), 0.011), (d(0.04), 0.011), (d(0.045), 0.028), (d(0.07), 0.027), (d(0.075), 0.012)])
    round_x(brass, 1.05, ZL0 + 0.06, [(d(0), 0.032), (d(0.012), 0.03), (d(0.014), 0.012)])
    bx(brass, min(d(0.014), d(0.026)), max(d(0.014), d(0.026)), 1.03, 1.07, ZL0 + 0.054, ZL0 + 0.066)   # thumb turn / key boss

# ---- the curtain rod over the glazing (the curtains themselves: hifi_sheers.py)
RY = GL1 + 0.025
bx(brass, -0.004, 0.006, RY, RY + 0.012, zi0 - 0.03, zi1 + 0.03)
# the red panels and the sheer are cloth, generated by tools/house/hifi_sheers.py (shirred on the rod line, film 6902/6910)

bpy.ops.wm.read_factory_settings(use_empty=True)
M = {"BD_Paint": material("BD_Paint", (0.88, 0.87, 0.83), 0.35), "BD_Glass": material("BD_Glass", (0.1, 0.12, 0.13), 0.05),
     "BD_Brass": material("BD_Brass", (0.75, 0.56, 0.25), 0.3), "BD_Flap": material("BD_Flap", (0.06, 0.055, 0.05), 0.5),
     "BD_Curtain": material("BD_Curtain", (0.62, 0.04, 0.06), 0.8), "BD_Sheer": material("BD_Sheer", (0.93, 0.92, 0.88), 0.9),
     "BD_Oak": material("BD_Oak", (0.45, 0.32, 0.2), 0.5)}
coll = bpy.context.scene.collection
root = bpy.data.objects.new("BackDoor_HiFi", None); coll.objects.link(root)
parts = (paint, glass, brass, flap, red, sheer, oak)
for p in parts:
    if p.f:
        p.build(coll, M).parent = root
OUT.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(OUT), export_format="GLB", export_yup=True, export_apply=True)
print("wrote", OUT, {p.name: len(p.f) for p in parts}, "opening z", Z0, Z1, "head", HEAD)
