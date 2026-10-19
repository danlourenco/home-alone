"""hifi_entrance: the front door's OUTSIDE as the film shows it (walk note Oct 19 07:28: "the lamp and door steel read as minecraft.
we need higher quality artifacts"; changes/2026-10-19-front-entrance.json, TRIAL). Replaces exterior_shell.door_face's box leaf, box
knob/knocker and box wreath, and porch_lantern's box lantern.

- LEAF: the same leaf as hifi_door.py (z 9.31-10.121, 1.898 m, foyer.json front_door), its outside face: six raised panels on the
  inside's rails (short top pair, tall middle pair, lower pair; lock rail 0.72-0.87), real depth (field 1.5 cm behind the stiles,
  a sloped raise and a shoulder), every edge bevelled, near-black green gloss (film 714, 4382, 5955). The Free Wood Door Pack was
  checked: its 15 doors share one flat Wood_Door.FBX with the panels only in the normal maps, and none is six-panel (Door_2 is
  2+2+1), so the leaf is generated.
- HARDWARE (brass, film 714/5955): the mail slot plate with its flap on the lock rail (as inside, hifi_door.py), a tall handle plate
  on the latch edge with a turned knob and a deadbolt rosette and cylinder. No knocker: the lit wreath hides the upper door in every
  film frame (714, 5955), so none is drawn.
- WREATH BULBS: 30 warm mini bulbs over the wreath (the wreath itself is the owned ChristmasTreeAndGarland store model, placed and
  lit in SpecGreybox.Shell); glow only at night (ShellGlow).
- LANTERN (film 714/10): a small glass-paned brass lantern hanging on a rod from the portico ceiling on the door's axis: four clear
  panes in a bevelled frame, a stepped hip cap and finial, a candelabra bulb (night glow), body 0.18 m square, bottom ~1.9 m over
  the floor (714: just above the door head). Authored to the film by eye (DEVIATIONS 102).
World y (placed like Exterior.glb at y 0); spec x, z.

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P tools/house/hifi_entrance.py
  -> unity/HomeAlone/Assets/Models/Foyer/FrontEntrance.glb (placed by SpecGreybox.Shell)
"""
import json
import math
import random
import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hifi_lib import Part, material   # noqa: E402
import hifi_pipeline as hp            # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "unity/HomeAlone/Assets/Models/Foyer/FrontEntrance.glb"
GF = json.loads((ROOT / "spec/geometry.json").read_text())["ground"]["floor_y"]
XW = 10.27                                   # the closed vestibule wall's outer face (exterior_shell.door_face)
DZ0, DZ1, DH = 9.31 + 0.002, 10.121 - 0.002, 1.898 - 0.002   # leaf 2 mm clear of the brick reveals and the transom (no coplanar faces)
ZM = (9.31 + 10.121) / 2
XB, XF = XW + 0.028, XW + 0.046              # panel field (the backing's face), stile/rail face
WREATH = dict(x=XF + 0.085, y=GF + 1.31, z=ZM, r=0.25)   # film 714: centre 1.31 m, ~0.6 m across with the bulbs (store model at 1.1x)
LX, LZ, LTOP = 10.37 + 0.62, 9.716, GF + 2.36   # the lantern's axis (exterior_shell.porch_lantern) and the portico ceiling

paint, brass, glass, bulb, wbulb = (Part("EntryPaint", "EN_Paint"), Part("EntryBrass", "EN_Brass"), Part("LanternGlass", "EN_Glass"),
                                    Part("LanternBulb", "EN_LampGlow"), Part("WreathBulbs", "EN_Bulb"))
panels = Part("EntryPanels", "EN_Paint")
lbrass = Part("LanternBrass", "EN_Brass")


# ---------------------------------------------------------------- the leaf
def raised(z0, z1, y0, y1):
    """A raised panel in the opening z0..z1, y0..y1 (spec z, height over the floor): slope from the field to a 3 mm shoulder 4 cm in,
    then the flat raise 6 mm under the stile face."""
    b, xs, xt = 0.040, XF - 0.010, XF - 0.006
    y0, y1 = GF + y0, GF + y1
    o = [(y0, z0), (y0, z1), (y1, z1), (y1, z0)]
    i = [(y0 + b, z0 + b), (y0 + b, z1 - b), (y1 - b, z1 - b), (y1 - b, z0 + b)]
    for k in range(4):
        a, c = o[k], o[(k + 1) % 4]; ia, ic = i[k], i[(k + 1) % 4]
        mid = ((a[0] + c[0] + ia[0] + ic[0]) / 4, (a[1] + c[1] + ia[1] + ic[1]) / 4)
        out = (0.3, mid[0] - (y0 + y1) / 2, mid[1] - (z0 + z1) / 2)
        panels.face([(XB + 0.001, a[0], a[1]), (XB + 0.001, c[0], c[1]), (xs, ic[0], ic[1]), (xs, ia[0], ia[1])], out)
        panels.face([(xs, ia[0], ia[1]), (xs, ic[0], ic[1]), (xt, ic[0], ic[1]), (xt, ia[0], ia[1])], (0, out[1], out[2]))
    panels.face([(xt, p[0], p[1]) for p in i], (1, 0, 0))


st = 0.115                                               # stiles; rails as the inside (hifi_door.py, film 10248)
rails = [(0.0, 0.20), (0.72, 0.87), (1.53, 1.63), (1.80, DH)]
cols = [(DZ0 + st, ZM - 0.05), (ZM + 0.05, DZ1 - st)]
paint.box(XW, XB, GF, GF + DH, DZ0, DZ1)                 # backing (the panels' field)
paint.box(XB, XF, GF, GF + DH, DZ0, DZ0 + st); paint.box(XB, XF, GF, GF + DH, DZ1 - st, DZ1)
for r0, r1 in rails:
    paint.box(XB, XF, GF + r0, GF + r1, DZ0 + st, DZ1 - st)
for (a, b), (c, d) in zip(rails, rails[1:]):
    paint.box(XB, XF, GF + b, GF + c, ZM - 0.05, ZM + 0.05)   # centre muntin
    for z0, z1 in cols:
        raised(z0, z1, b, c)

# ---------------------------------------------------------------- hardware (brass)
def plate(x, y0, y1, z0, z1, t):
    """A plate with rounded ends (radius = half its width), t thick, on the face x."""
    r = (z1 - z0) / 2; zc = (z0 + z1) / 2
    ring = [(y1 - r + r * math.sin(a), zc + r * math.cos(a)) for a in [math.pi * k / 16 for k in range(17)]]
    ring += [(y0 + r - r * math.sin(a), zc - r * math.cos(a)) for a in [math.pi * k / 16 for k in range(17)]]
    brass.face([(x + t, y, z) for y, z in ring], (1, 0, 0))
    brass.face([(x, y, z) for y, z in ring], (-1, 0, 0))
    for (ya, za), (yb, zb) in zip(ring, ring[1:] + ring[:1]):
        brass.face([(x, ya, za), (x, yb, zb), (x + t, yb, zb), (x + t, ya, za)], (0, (ya + yb) / 2 - (y0 + y1) / 2, (za + zb) / 2 - zc))


def turned(x0, y, z, prof, n=48):
    """A turned part on a horizontal axis along +x from the door face: prof = [(distance out, radius)]."""
    rings = [[(x0 + d, y + r * math.sin(2 * math.pi * k / n), z + r * math.cos(2 * math.pi * k / n)) for k in range(n)] for d, r in prof]
    for a, b in zip(rings, rings[1:]):
        for k in range(n):
            k2 = (k + 1) % n
            m = [(a[k][j] + a[k2][j] + b[k][j] + b[k2][j]) / 4 for j in range(3)]
            brass.face([a[k], a[k2], b[k2], b[k]], (0.0001 * (b[0][0] - a[0][0]), m[1] - y, m[2] - z))
    brass.face(rings[-1], (1, 0, 0))


zk = DZ1 - 0.065                                        # latch edge (the knob side seen from outside, film 714 left)
plate(XF, GF + 0.80, GF + 1.32, zk - 0.032, zk + 0.032, 0.006)
turned(XF + 0.006, GF + 0.92, zk, [(0, 0.022), (0.012, 0.016), (0.03, 0.009), (0.045, 0.012), (0.055, 0.027), (0.068, 0.029),
                                       (0.078, 0.025), (0.083, 0.012)])          # knob (55 mm)
turned(XF + 0.006, GF + 1.22, zk, [(0, 0.026), (0.006, 0.026), (0.010, 0.022), (0.014, 0.017), (0.024, 0.016)])   # deadbolt rosette + cylinder
brass.box(XF + 0.0248, XF + 0.0255, GF + 1.212, GF + 1.228, zk - 0.0015, zk + 0.0015)   # its keyway (proud of the cylinder face)
# mail slot on the lock rail (the inside's at 0.78-0.81: hifi_door.py; film 714 0.84 under the wreath)
brass.box(XF, XF + 0.005, GF + 0.762, GF + 0.838, ZM - 0.15, ZM + 0.15)                 # plate
brass.box(XF + 0.005, XF + 0.014, GF + 0.778, GF + 0.822, ZM - 0.125, ZM + 0.125)        # flap
brass.box(XF + 0.014, XF + 0.026, GF + 0.812, GF + 0.822, ZM - 0.05, ZM + 0.05)          # its lift handle
for zz in (ZM - 0.135, ZM + 0.135):
    turned(XF + 0.005, GF + 0.80, zz, [(0, 0.005), (0.003, 0.004), (0.004, 0.0)], n=16)   # screw heads

# ---------------------------------------------------------------- wreath bulbs (the wreath itself: the store model, SpecGreybox.Shell)
random.seed(19)
for k in range(30):
    t = 2 * math.pi * (k + random.uniform(-0.3, 0.3)) / 30
    if math.sin(t) > 0.82:   # under the bow at the top
        continue
    r = WREATH["r"] * random.uniform(0.72, 1.0); y, z = WREATH["y"] + r * math.sin(t), WREATH["z"] + r * math.cos(t)
    x = WREATH["x"] + random.uniform(0.03, 0.06)
    rings = [(0, 0.001), (0.004, 0.0045), (0.009, 0.006), (0.014, 0.0045), (0.019, 0.001)]
    n = 10; a = random.uniform(0, 2 * math.pi)
    ax = (0.5, math.cos(a), math.sin(a)); L = math.sqrt(sum(c * c for c in ax)); ax = [c / L for c in ax]
    u = [0, -ax[2], ax[1]]; Lu = math.sqrt(sum(c * c for c in u)); u = [c / Lu for c in u]
    v = [ax[1] * u[2] - ax[2] * u[1], ax[2] * u[0] - ax[0] * u[2], ax[0] * u[1] - ax[1] * u[0]]
    pts = [[(x + ax[0] * h + rr * (math.cos(2 * math.pi * j / n) * u[0] + math.sin(2 * math.pi * j / n) * v[0]),
             y + ax[1] * h + rr * (math.cos(2 * math.pi * j / n) * u[1] + math.sin(2 * math.pi * j / n) * v[1]),
             z + ax[2] * h + rr * (math.cos(2 * math.pi * j / n) * u[2] + math.sin(2 * math.pi * j / n) * v[2])) for j in range(n)] for h, rr in rings]
    for p, q in zip(pts, pts[1:]):
        for j in range(n):
            j2 = (j + 1) % n
            m = [(p[j][i] + p[j2][i] + q[j][i] + q[j2][i]) / 4 for i in range(3)]
            c = [x + ax[0] * 0.0095, y + ax[1] * 0.0095, z + ax[2] * 0.0095]
            wbulb.face([p[j], p[j2], q[j2], q[j]], tuple(m[i] - c[i] for i in range(3)))


# ---------------------------------------------------------------- lantern
def sq(y, h):
    return [(LX - h, y, LZ - h), (LX + h, y, LZ - h), (LX + h, y, LZ + h), (LX - h, y, LZ + h)]


def frustum(P, y0, h0, y1, h1):
    """A square frustum (or prism) about the lantern's axis from half-width h0 at y0 to h1 at y1, capped."""
    a, b = sq(y0, h0), sq(y1, h1)
    for k in range(4):
        k2 = (k + 1) % 4
        m = [(a[k][i] + a[k2][i] + b[k][i] + b[k2][i]) / 4 for i in range(3)]
        P.face([a[k], a[k2], b[k2], b[k]], (m[0] - LX, 0, m[2] - LZ))
    if h0 > 0: P.face(a, (0, -1, 0) if y0 < y1 else (0, 1, 0))
    if h1 > 0: P.face(b, (0, 1, 0) if y0 < y1 else (0, -1, 0))


H = 0.09                                                  # body half-width (0.18 m, film 714)
yb, yg0, yg1, yc = GF + 1.90, GF + 1.94, GF + 2.17, GF + 2.20
lbrass.lathe(LX, LZ, LTOP - 0.025, [(0, 0.012), (0.005, 0.012), (0.013, 0.045), (0.025, 0.045)], n=48)   # ceiling canopy
lbrass.lathe(LX, LZ, yc + 0.075, [(0, 0.006), (LTOP - 0.025 - yc - 0.075, 0.006)], n=16)                           # rod
lbrass.lathe(LX, LZ, yc + 0.05, [(0, 0.012), (0.01, 0.018), (0.02, 0.012), (0.025, 0.006)], n=24)                 # rod collar / ball
frustum(lbrass, yb, 0.03, yb + 0.03, H + 0.008)           # bottom pan
lbrass.lathe(LX, LZ, yb - 0.035, [(0, 0.002), (0.01, 0.008), (0.025, 0.012), (0.035, 0.004)], n=24)  # bottom finial
frustum(lbrass, yb + 0.03, H + 0.008, yg0, H + 0.008)     # bottom band
frustum(lbrass, yg1, H + 0.008, yc + 0.003, H + 0.012)    # top band (into the drip edge: no coplanar caps)
frustum(lbrass, yc, H + 0.016, yc + 0.008, H + 0.016)     # cap's drip edge
frustum(lbrass, yc + 0.008, H + 0.012, yc + 0.05, 0.02)   # hip cap
for sx in (-1, 1):
    for sz in (-1, 1):
        cx, cz = LX + sx * H, LZ + sz * H
        lbrass.box(cx - 0.007, cx + 0.007, yg0, yg1, cz - 0.007, cz + 0.007)   # corner posts
for k in range(4):                                        # clear panes (4 mm), between the posts, 3 mm in from the posts' faces
    if k < 2:
        x0 = LX + (-1 if k == 0 else 1) * (H - 0.002); glass.box(x0 - 0.002, x0 + 0.002, yg0, yg1, LZ - H + 0.007, LZ + H - 0.007)
    else:
        z0 = LZ + (-1 if k == 2 else 1) * (H - 0.002); glass.box(LX - H + 0.007, LX + H - 0.007, yg0, yg1, z0 - 0.002, z0 + 0.002)
lbrass.lathe(LX, LZ, yg0, [(0, 0.016), (0.035, 0.014), (0.045, 0.011)], n=32)                                        # socket
bulb.lathe(LX, LZ, yg0 + 0.045, [(0, 0.008), (0.02, 0.016), (0.045, 0.014), (0.07, 0.006), (0.078, 0.002)], n=32)      # candelabra bulb

# ---------------------------------------------------------------- export
bpy.ops.wm.read_factory_settings(use_empty=True)
M = {"EN_Paint": material("EN_Paint", (0.018, 0.026, 0.022), 0.35), "EN_Brass": material("EN_Brass", (0.75, 0.56, 0.25), 0.3),
     "EN_Glass": material("EN_Glass", (0.85, 0.9, 0.9), 0.05), "EN_LampGlow": material("EN_LampGlow", (1.0, 0.85, 0.6), 0.2),
     "EN_Bulb": material("EN_Bulb", (1.0, 0.75, 0.45), 0.3)}
BEVEL = {"EntryPaint": 0.004, "EntryPanels": 0.002, "EntryBrass": 0.0012, "LanternBrass": 0.0012}
coll = bpy.context.scene.collection
root = bpy.data.objects.new("FrontEntrance_HiFi", None); coll.objects.link(root)
root["lod_reason"] = "single LOD: a door, its hardware and a lantern seen from the stoop and the walk (<= 15 m)"
stats = {}
for p in (paint, panels, brass, lbrass, glass, bulb, wbulb):
    if not p.f:
        continue
    ob = hp.to_object(p, M[p.mat], coll, hard_deg=30.0, weld=1e-5); ob.parent = root
    if p.name in BEVEL:
        bv = ob.modifiers.new("Bevel", "BEVEL"); bv.width = BEVEL[p.name]; bv.segments = 3; bv.limit_method = "ANGLE"
        bv.angle_limit = math.radians(30); bv.use_clamp_overlap = True
        wn = ob.modifiers.new("WeightedNormal", "WEIGHTED_NORMAL"); wn.keep_sharp = True; wn.mode = "FACE_AREA"
        hp.apply_modifiers(ob)
    stats[p.name] = len(ob.data.polygons)
OUT.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(OUT), export_format="GLB", export_yup=True, export_apply=True, export_extras=True)
print("wrote", OUT, stats)
