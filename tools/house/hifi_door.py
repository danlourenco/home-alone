"""hifi_door: the front door assembly as the film shows it from inside (user, Oct 16: "i want the door to look EXACTLY like it does
in the movie"), on the vestibule's front wall (inside face x 10.13, spec metres, y above the ground floor).

Measured on film 10248 with the camera solved by tools/house/film_solve_10248.py (fit 9.7 px), scaled by our door leaf (0.811 x
1.898 m, foyer.json front_door, Marina 203 s); film 9358 and 778 for the lower door and hardware:
- leaf z 9.31-10.121: six raised panels (short top pair, tall middle pair, lower pair), lock rail between middle and lower pairs
  with a brass mail slot; brass deadbolt (1.24 m) and tall handle plate (0.77-1.03 m) on the right; three brass hinges on the
  left; a Christmas wreath centred at 1.47 m
- sidelights either side: openings in the front wall (glass 0.412-1.844 m, z 8.968-9.255 / 10.176-10.463); white sheers gathered
  on brass rods (0.41 and 1.84 m) in the film (NOT built: DEVIATIONS 41), a raised panel below
- plain pilasters 9 cm wide, outer edges z 8.848 and 10.583; transom bar 1.898-1.93; an elliptical arch over door and
  sidelights, apex 2.118 m, with a radial-muntin fanlight
Every face stands >= 1 cm off the one behind it (zfight-check).

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P tools/house/hifi_door.py
  -> unity/HomeAlone/Assets/Models/Foyer/FrontDoor.glb (placed like Tree.glb: ground-floor root, spec coordinates)
"""
import math
import random
import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hifi_lib import Part, material   # noqa: E402

OUT = Path(__file__).resolve().parents[2] / "unity/HomeAlone/Assets/Models/Foyer/FrontDoor.glb"
WF = 10.13                                  # the front wall's inside face
DZ0, DZ1, DH = 9.31, 10.121, 1.898          # door leaf
PZ0, PZ1, PW = 8.848, 10.583, 0.09          # pilaster outer edges, width
ZC = (PZ0 + PZ1) / 2                        # 9.7155: the assembly's centre (the door's centre agrees within 1 mm)
TB, APEX = 1.93, 2.118                      # transom bar top, arch apex

paint, brass, glass, leaf, berry = (Part("Paint", "Door_Paint"), Part("Brass", "Door_Brass"), Part("Glass", "Door_Glass"),
                                    Part("Leaves", "Door_Wreath"), Part("Berries", "Door_Berry"))


def raised_panel(z0, z1, y0, y1, x_field):
    """A panel opening: its field 1.5 cm behind the stiles, a raised centre 1.2 cm proud of the field, 2.5 cm in from the edges."""
    paint.box(x_field, WF - 0.005, y0, y1, z0, z1)
    paint.box(x_field - 0.012, x_field, y0 + 0.025, y1 - 0.025, z0 + 0.025, z1 - 0.025)


def framed(z0, z1, y0, y1, stile, rails, panels_z, x_front):
    """Stiles and rails (x_front .. field) around panel openings: rails = [(y0, y1)] bands, panels_z = [(z0, z1)] columns."""
    xf = x_front + 0.025
    paint.box(x_front, xf, y0, y1, z0, z0 + stile); paint.box(x_front, xf, y0, y1, z1 - stile, z1)
    for ry0, ry1 in rails:
        paint.box(x_front, xf, ry0, ry1, z0 + stile, z1 - stile)
    if len(panels_z) > 1:   # the centre muntin between panel columns
        paint.box(x_front, xf, y0, y1, panels_z[0][1], panels_z[1][0])
    for (py0, py1) in [(rails[i][1], rails[i + 1][0]) for i in range(len(rails) - 1)]:
        for pz0, pz1 in panels_z:
            raised_panel(pz0, pz1, py0, py1, xf)


# ---- the leaf: stiles 0.115, rails top 0.098 / mid 0.10 / lock 0.15 / bottom 0.20, centre muntin 0.10
st = 0.115; mz = (DZ0 + DZ1) / 2
cols = [(DZ0 + st, mz - 0.05), (mz + 0.05, DZ1 - st)]
rails = [(0.0, 0.20), (0.72, 0.87), (1.53, 1.63), (1.80, DH)]
framed(DZ0, DZ1, 0.0, DH, st, rails, cols, WF - 0.048)
xd = WF - 0.048                                           # the leaf's front (room side)
paint.box(WF - 0.011, WF - 0.005, 0.0, DH, DZ0, DZ1)      # backing: the joints between stiles, rails and panels show paint, not lit
                                                          # wall (user note 09:33: "tiny gaps"); >= 1 cm from the wall and the panels
brass.box(xd - 0.008, xd, 0.78, 0.81, mz - 0.13, mz + 0.13)            # mail slot plate on the lock rail
brass.box(xd - 0.02, xd - 0.008, 0.80, 0.81, mz - 0.11, mz + 0.11)     # its lip, 1.2 cm proud
brass.box(xd - 0.008, xd, 0.77, 1.03, DZ1 - 0.085, DZ1 - 0.045)       # tall handle plate
for y in (0.98, 1.24):                                                  # thumb latch boss and deadbolt rosette + turn
    brass.box(xd - 0.03, xd, y - 0.02, y + 0.02, DZ1 - 0.085, DZ1 - 0.045)
brass.box(xd - 0.07, xd - 0.03, 0.86, 0.90, DZ1 - 0.09, DZ1 - 0.04)    # the grip's lever
for y in (0.25, 0.95, 1.65):                                            # hinges on the left edge
    brass.box(xd - 0.006, xd, y, y + 0.10, DZ0, DZ0 + 0.015)

# ---- mullions between the leaf and the sidelights (film 10248: ~5.6 cm; user note 09:33 "tiny gaps" was the open strip here)
for z0, z1 in ((DZ0 - 0.025, DZ0), (DZ1, DZ1 + 0.025)):
    paint.box(WF - 0.05, WF, 0.0, DH, z0, z1)

# ---- sidelights: stiles 0.03 / 0.025, a raised panel 0.025-0.377, glass 0.412-1.844 (the film's sheers and their rods: not built)
for z0, z1 in ((PZ0 + PW, DZ0 - 0.025), (DZ1 + 0.025, PZ1 - PW)):
    xs = WF - 0.04
    paint.box(xs, xs + 0.025, 0.0, DH, z0, z0 + 0.03); paint.box(xs, xs + 0.025, 0.0, DH, z1 - 0.03, z1)
    paint.box(xs, xs + 0.025, 0.0, 0.025, z0 + 0.03, z1 - 0.03)          # bottom rail
    paint.box(xs, xs + 0.025, 0.377, 0.412, z0 + 0.03, z1 - 0.03)        # rail under the glass
    paint.box(xs, xs + 0.025, 1.844, DH, z0 + 0.03, z1 - 0.03)           # top rail
    raised_panel(z0 + 0.03, z1 - 0.03, 0.025, 0.377, xs + 0.025)
    # no pane here: the sidelights are real openings in the front wall with clear glass (measurements/windows/ground.json)
    # sheers and rods: NOT built (user, Oct 16: "figure out how to do it properly and realistically or don't do it at all"); DEVIATIONS 41

# ---- pilasters with plinth and cap blocks; transom bar
for z0 in (PZ0, PZ1 - PW):
    paint.box(WF - 0.05, WF, 0.0, TB, z0, z0 + PW)
    paint.box(WF - 0.065, WF - 0.05, 0.0, 0.22, z0 - 0.01, z0 + PW + 0.01)       # plinth
    paint.box(WF - 0.065, WF - 0.05, TB - 0.06, TB, z0 - 0.01, z0 + PW + 0.01)   # cap
paint.box(WF - 0.05, WF, DH, TB, PZ0 + PW, PZ1 - PW)

# ---- the arch: an elliptical molding over the whole assembly, the fanlight glass and its radial muntins
A, B = (PZ1 - PZ0) / 2, APEX - TB                         # semi-axes
def ell(t, a=A, b=B):
    return ZC - a * math.cos(t), TB + b * math.sin(t)
paint.sweep([(WF - 0.015, y, z) for z, y in [ell(math.radians(d), A + 0.015, B + 0.015) for d in range(4, 177, 4)]],
            [(-0.015, -0.015), (0.015, -0.015), (0.015, 0.015), (-0.015, 0.015)])   # outer molding, 3 x 3 cm over the arc (symmetric profile)
ai, bi = A - PW, B - 0.035                                 # the fanlight opening inside the molding
fan = [ell(math.radians(d), ai, bi) for d in range(0, 181, 6)]
glass.face([(WF - 0.008, y, z) for z, y in fan], (-1, 0, 0))
mun = [(-0.008, -0.008), (0.008, -0.008), (0.008, 0.008), (-0.008, 0.008)]
hub = [ell(math.radians(d), 0.12, 0.05) for d in range(8, 177, 12)]                  # the small half-oval at the bottom centre
paint.sweep([(WF - 0.02, y, z) for z, y in hub], mun)
for k in range(1, 8):                                     # spokes from the hub to the rim
    t = math.pi * k / 8
    (z0, y0), (z1, y1) = ell(t, 0.12, 0.05), ell(t, ai, bi)
    paint.sweep([(WF - 0.02, y0, z0), (WF - 0.02, y1, z1)], mun)
mid = [ell(math.radians(d), ai * 0.62, bi * 0.62) for d in range(6, 177, 6)]          # the ring between hub and rim
paint.sweep([(WF - 0.02, y, z) for z, y in mid], mun)

# ---- the wreath: leaves round a ring 0.17 m across the middle, centred on the door at 1.47 m, berries
random.seed(7)
WC = (xd - 0.03, 1.47, mz)
for k in range(420):                                     # dense boxwood (film: a full, dark wreath)
    t = 2 * math.pi * k / 420 + random.uniform(-0.03, 0.03); r = random.uniform(0.10, 0.22)
    cy, cz = WC[1] + r * math.sin(t), WC[2] + r * math.cos(t)
    a = t + math.pi / 2 + random.uniform(-1.2, 1.2); L, W2 = random.uniform(0.035, 0.06), random.uniform(0.01, 0.016)
    ex, ez = math.sin(a) * L, math.cos(a) * L
    x = WC[0] - random.uniform(0, 0.05)
    leaf.face([(x, cy, cz), (x - 0.006, cy + ex / 2 + W2 * math.cos(a), cz + ez / 2 - W2 * math.sin(a)),
               (x, cy + ex, cz + ez), (x - 0.006, cy + ex / 2 - W2 * math.cos(a), cz + ez / 2 + W2 * math.sin(a))], (-1, 0, 0))
for k in range(18):
    t = random.uniform(0, 2 * math.pi); r = random.uniform(0.12, 0.2)
    cy, cz = WC[1] + r * math.sin(t), WC[2] + r * math.cos(t)
    berry.box(WC[0] - 0.045, WC[0] - 0.03, cy - 0.008, cy + 0.008, cz - 0.008, cz + 0.008)

bpy.ops.wm.read_factory_settings(use_empty=True)
M = {"Door_Paint": material("Door_Paint", (0.88, 0.87, 0.83), 0.35), "Door_Brass": material("Door_Brass", (0.75, 0.56, 0.25), 0.3),
     "Door_Glass": material("Door_Glass", (0.1, 0.12, 0.13), 0.05), 
     "Door_Wreath": material("Door_Wreath", (0.05, 0.09, 0.05), 0.6), "Door_Berry": material("Door_Berry", (0.55, 0.05, 0.05), 0.4)}
coll = bpy.context.scene.collection
root = bpy.data.objects.new("FrontDoor_HiFi", None); coll.objects.link(root)
parts = (paint, brass, glass, leaf, berry)
for p in parts:
    if p.f:
        p.build(coll, M).parent = root
OUT.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(OUT), export_format="GLB", export_yup=True, export_apply=True)
print("wrote", OUT, {p.name: len(p.f) for p in parts})
