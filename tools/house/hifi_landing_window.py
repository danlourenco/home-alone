"""hifi_landing_window: the stair landing's window as the film shows it (user, Oct 16: "make sure that landing window looks exactly
like the movie, it's iconic"). Read from spec/house_spec.ground.json wall_openings.landing_window (measured: film 11966 and 12133,
Marina 312 s; measurements/windows/ground.json); the same numbers cut the wall (SpecGreybox.CutWallOpenings), so the two agree.

Film: two 6-over-6 double-hung sashes either side of a wide post, a transom bar, and one elliptical fanlight over both with radial
muntins round a half-oval hub; a 9 cm white casing up the legs and round the arch; a deep stool and an apron. The landing's back
wall's wainscot is the face trim's (tools/house/trim_faces.py, HOUSE-KERNEL step 2); before step 2 this model panelled it to the stool. Room side is +x (spec); the wall's room face is 'face'.

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P tools/house/hifi_landing_window.py
  -> unity/HomeAlone/Assets/Models/Foyer/LandingWindow.glb (placed like Tree.glb)
"""
import json
import math
import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hifi_lib import Part, material   # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "unity/HomeAlone/Assets/Models/Foyer/LandingWindow.glb"
SPEC = json.loads((ROOT / "spec/house_spec.ground.json").read_text())
W = next(o for o in SPEC["wall_openings"] if o["name"] == "landing_window")
# HOUSE-KERNEL step 2: the window's casing legs, stool and apron come from its opening record (tools/house/openings.py ->
# spec/openings.json), the same boxes the face trim is cut at; with own_trim the landing's wainscot is the face trim's (one height
# round the landing, STATUS 8t-3) and the stool rests on the wall under the rough opening (its top was flush with the cut: 8t-2 z-fight)
OPN = json.loads((ROOT / "spec/openings.json").read_text())
REC = next(r for r in OPN["openings"] if r["id"] == "ground:wall_opening:landing_window")
OWN = OPN["own_trim"]
PIECE = {pc["part"]: pc["box"] for pc in REC["pieces"]}   # spec x, spec z, world y
GY = json.loads((ROOT / "spec/geometry.json").read_text())["ground"]["floor_y"]

FACE, XB = W["face"], W["x"][0]                       # room face, back face of the wall
ZC, HW = W["z_centre"], W["width_m"] / 2
Z0, Z1 = ZC - HW, ZC + HW
SILL, SASH, TR, FAN = W["sill_m"], W["sash_m"], W["transom_m"], W["fan_rise_m"]
SPRING = SILL + SASH + TR                             # top of the transom bar = the fanlight's spring line
POST, CAS = W["post_m"], W["casing_m"]
COLS, ROWS = W["panes"]

paint, glass, brass, paper = Part("Paint", "LW_Paint"), Part("Glass", "LW_Glass"), Part("Brass", "LW_Brass"), Part("Paper", "LW_Paper")
st = 0.045                                            # sash stile / rail
mun = 0.018                                           # muntin width


def sash(z0, z1, y0, y1, x0, x1, top_rail, bottom_rail):
    """A sash: stiles, rails, a COLS x ROWS muntin grid and its glass (glass in the sash's middle plane)."""
    paint.box(x0, x1, y0, y1, z0, z0 + st); paint.box(x0, x1, y0, y1, z1 - st, z1)
    paint.box(x0, x1, y0, y0 + bottom_rail, z0 + st, z1 - st); paint.box(x0, x1, y1 - top_rail, y1, z0 + st, z1 - st)
    gz0, gz1, gy0, gy1 = z0 + st, z1 - st, y0 + bottom_rail, y1 - top_rail
    for c in range(1, COLS):
        zc = gz0 + (gz1 - gz0) * c / COLS
        paint.box(x0 + 0.006, x1 - 0.006, gy0, gy1, zc - mun / 2, zc + mun / 2)
    for r in range(1, ROWS):
        yc = gy0 + (gy1 - gy0) * r / ROWS
        paint.box(x0 + 0.006, x1 - 0.006, yc - mun / 2, yc + mun / 2, gz0, gz1)
    xm = (x0 + x1) / 2
    glass.face([(xm, gy0, gz0), (xm, gy1, gz0), (xm, gy1, gz1), (xm, gy0, gz1)], (1, 0, 0))


# ---- the two double-hung units: lower sash at the room side, upper sash 4 cm further out (they overlap at the meeting rail)
half = SASH / 2
for z0, z1 in ((Z0, ZC - POST / 2), (ZC + POST / 2, Z1)):
    sash(z0, z1, SILL, SILL + half + 0.02, FACE - 0.10, FACE - 0.06, 0.035, 0.06)              # lower (meeting rail 0.035)
    sash(z0, z1, SILL + half - 0.02, SILL + SASH, FACE - 0.14, FACE - 0.10, st, 0.035)         # upper
    brass.box(FACE - 0.06, FACE - 0.05, SILL + half + 0.005, SILL + half + 0.02, (z0 + z1) / 2 - 0.03, (z0 + z1) / 2 + 0.03)  # sash lock
paint.box(FACE - 0.14, FACE - 0.005, SILL, SILL + SASH, ZC - POST / 2, ZC + POST / 2)          # the centre post
for z0, z1 in ((Z0, Z0 + 0.02), (Z1 - 0.02, Z1)):                                              # jamb liners (the reveal)
    paint.box(XB + 0.01, FACE - 0.005, SILL, SPRING, z0, z1)
paint.box(FACE - 0.14, FACE - 0.005, SILL + SASH, SPRING, Z0 + 0.02, Z1 - 0.02)                # transom bar

# ---- fanlight: half-ellipse glass, a rim, the hub and radial muntins (film: ~11 spokes)
A, B = HW - 0.02, FAN


def ell(t, a, b):
    return ZC - a * math.cos(t), SPRING + b * math.sin(t)


xf = FACE - 0.10
fan = [ell(math.radians(d), A, B) for d in range(0, 181, 5)]
glass.face([(xf, y, z) for z, y in fan], (1, 0, 0))
mp = [(-0.009, -0.009), (0.009, -0.009), (0.009, 0.009), (-0.009, 0.009)]
paint.sweep([(xf + 0.012, y, z) for z, y in [ell(math.radians(d), 0.11, 0.045) for d in range(6, 175, 12)]], mp)   # hub
paint.sweep([(xf + 0.012, y, z) for z, y in [ell(math.radians(d), A - 0.009, B - 0.009) for d in range(2, 179, 4)]], mp)   # rim (film 11966)
for k in range(1, 12):
    t = math.pi * k / 12
    (za, ya), (zb, yb) = ell(t, 0.11, 0.045), ell(t, A, B)
    paint.sweep([(xf + 0.012, ya, za), (xf + 0.012, yb, zb)], mp)
# the infill between the rectangle cut and the arch, papered like the wall, flush with its face (vertical strips under the top edge)
TOP = W["y"][1]
for d in range(0, 180, 3):
    (za, ya), (zb, yb) = ell(math.radians(d), HW, FAN), ell(math.radians(d + 3), HW, FAN)
    if TOP - max(ya, yb) > 0.002:
        paper.face([(FACE, ya, za), (FACE, TOP, za), (FACE, TOP, zb), (FACE, yb, zb)], (1, 0, 0))

# ---- casing: legs from the stool to the spring line, an elliptical band round the arch; 2 cm proud of the wall
cx0, cx1 = FACE, FACE + 0.02


def piece(part):   # the opening record's box in this model's frame (ground-floor metres)
    b = PIECE[part]; paint.box(b[0], b[1], b[4] - GY, b[5] - GY, b[2], b[3])


piece("leg_lo"); piece("leg_hi")
band = [ell(math.radians(d), HW + CAS / 2, FAN + CAS / 2) for d in range(0, 181, 4)]
# a sweep's 'across' is horizontal and perpendicular to the path: for an arc in the wall's plane that is the depth (x); 'up' is the
# band's width in the plane. Both symmetric, so the profile cannot land on the wrong side of its path
paint.sweep([(cx0 + 0.01, y, z) for z, y in band], [(-0.01, -CAS / 2), (0.01, -CAS / 2), (0.01, CAS / 2), (-0.01, CAS / 2)])
# stool (deep sill) and apron
if OWN:   # the stool board fills the rough opening through the wall, resting on its top (no face flush with the cut)
    paint.box(XB, FACE, REC["rough"]["y"][0], SILL, Z0 + 0.02, Z1 - 0.02)
else:
    paint.box(XB + 0.01, FACE, SILL - 0.035, SILL, Z0 + 0.02, Z1 - 0.02)                    # in the opening, between the jamb liners
piece("stool")                                                                             # the stool's nose, with ears
piece("apron")

# ---- the landing's back wall below the stool: white panelling across the landing (film 11966, 12133), 1.2 cm proud
LY = W["landing_y"]                                   # the landing's finished floor (carpet top), ground-floor metres
WZ0, WZ1 = 7.778, 11.43   # with OWN the face trim panels this wall instead (skirt, panel, rail at the landing's one wainscot height)
if not OWN:   # step 1 (old path): the model panels the wall to its stool
    paint.box(FACE, FACE + 0.012, LY, SILL - 0.035, WZ0, Z0 - CAS - 0.03)
    paint.box(FACE, FACE + 0.012, LY, SILL - 0.13, Z0 - CAS - 0.03, Z1 + CAS + 0.03)
    paint.box(FACE, FACE + 0.012, LY, SILL - 0.035, Z1 + CAS + 0.03, WZ1)
    paint.box(FACE + 0.012, FACE + 0.03, SILL - 0.06, SILL - 0.035, WZ0, Z0 - CAS - 0.03)     # cap rail level with the stool
    paint.box(FACE + 0.012, FACE + 0.03, SILL - 0.06, SILL - 0.035, Z1 + CAS + 0.03, WZ1)

bpy.ops.wm.read_factory_settings(use_empty=True)
M = {"LW_Paint": material("LW_Paint", (0.88, 0.87, 0.83), 0.35), "LW_Glass": material("LW_Glass", (0.1, 0.12, 0.13), 0.05),
     "LW_Brass": material("LW_Brass", (0.75, 0.56, 0.25), 0.3), "LW_Paper": material("LW_Paper", (0.75, 0.63, 0.52), 0.8)}
coll = bpy.context.scene.collection
root = bpy.data.objects.new("LandingWindow_HiFi", None); coll.objects.link(root)
parts = (paint, glass, brass, paper)
for p in parts:
    if p.f:
        p.build(coll, M).parent = root
OUT.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(OUT), export_format="GLB", export_yup=True, export_apply=True)
print("wrote", OUT, {p.name: len(p.f) for p in parts})
