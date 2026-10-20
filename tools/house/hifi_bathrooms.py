"""hifi_bathrooms: the parents' ensuite and the upstairs hall bathroom (TRIAL 1, Oct 19; changes/2026-10-19-bathrooms.json), generated to
spec/dressing/bathrooms.json in spec coordinates above the UPPER floor (hifi_lib: Blender (-x, z, y) -> Unity (x, y, -z)).

Parents' ensuite (film 4386-4438 / 6402-6474, the set photo at Marina 160-169 s, Marina 205-228 s): the dark-green marble vanity with an
undermount oval sink and brass taps, ivory drawer bank, knee space, gilt mirror, bracket shelves with towels and toiletries, a curved-front
tub with its dark marble upstand, the black-framed quadrant shower, the 4-globe brass light bar, three gilt prints over two brass towel bars
with layered green towels, the toilet, lace window dressing, a wastebasket and the counter clutter of the aftershave scene (the
aftershave, Shower to Shower, Aquafresh, the toothbrush cup, cotton balls, the green bud vase).
Hall bath (film 332-344, Marina 445-490 s): the white subway-tile wainscot with its black liner and cap, the alcove tub with a tiled end
wall and a green shower curtain, the toilet, the pedestal sink, the medicine cabinet and the frosted globe, the towel bar, the wicker
shelf, the hamper, the window's cream panels. Plants are pack models (SpecGreybox.Bathrooms.cs).

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P tools/house/hifi_bathrooms.py
  -> unity/HomeAlone/Assets/Models/Foyer/Bathrooms.glb (fixtures, static) + BathroomProps.glb (loose props, movable)
"""
import json
import math
import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hifi_lib import Part, material   # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "unity/HomeAlone/Assets/Models/Foyer/Bathrooms.glb"
OUTP = OUT.with_name("BathroomProps.glb")
_src = (ROOT / "tools/house/hifi_sheers.py").read_text()
_ns = {"__file__": str(ROOT / "tools/house/hifi_sheers.py"), "__name__": "hifi_sheers_lib"}
exec(compile(_src[:_src.index("\nbpy.ops.wm.read_factory_settings(use_empty=True)")], "hifi_sheers.py", "exec"), _ns)
sheer_panel, valance, SMOOTH = _ns["sheer_panel"], _ns["valance"], _ns["SMOOTH"]

D = json.loads((ROOT / "spec/dressing/bathrooms.json").read_text())
GEO = json.loads((ROOT / "spec/geometry.json").read_text())["upstairs"]
POLY = {r["name"]: r["poly"] for r in GEO["rooms"]}
OPEN = [o for o in json.loads((ROOT / "spec/openings.json").read_text())["openings"] if o["storey"] == "upstairs"]
GAP = 0.015                                                     # fixtures stand this far off a wall face (the baseboard is 1.2 cm proud)

parts, props = {}, {}


def P(name, mat=None):
    if name not in parts:
        parts[name] = Part(name, mat or name)
    return parts[name]


def Q(name, mat=None):                                          # a loose prop (BathroomProps.glb)
    if name not in props:
        props[name] = Part(name, mat or name)
    return props[name]


def ellipse(cx, cz, rx, rz, n=48, a0=0.0):
    return [(cx + rx * math.cos(a0 + 2 * math.pi * k / n), cz + rz * math.sin(a0 + 2 * math.pi * k / n)) for k in range(n)]


def prism(part, pts, y0, y1, bottom=True):
    """A vertical prism over a closed plan outline [(x, z)]: sides facing out, a top, optionally a bottom."""
    n = len(pts); cx = sum(p[0] for p in pts) / n; cz = sum(p[1] for p in pts) / n
    for i in range(n):
        (ax, az), (bx, bz) = pts[i], pts[(i + 1) % n]
        mx, mz = (ax + bx) / 2, (az + bz) / 2
        out = (bz - az, 0, -(bx - ax))                          # either normal; pick the one away from the centroid
        if out[0] * (mx - cx) + out[2] * (mz - cz) < 0:
            out = (-out[0], 0, -out[2])
        part.face([(ax, y0, az), (bx, y0, bz), (bx, y1, bz), (ax, y1, az)], out)
    part.face([(x, y1, z) for x, z in pts], (0, 1, 0))
    if bottom:
        part.face([(x, y0, z) for x, z in pts], (0, -1, 0))


def ering(part, outer, inner, y, up=True):
    """The flat ring between two closed outlines with the same point count (a counter round a sink, a tub's rim)."""
    n = len(outer)
    for i in range(n):
        j = (i + 1) % n
        part.face([(outer[i][0], y, outer[i][1]), (outer[j][0], y, outer[j][1]), (inner[j][0], y, inner[j][1]), (inner[i][0], y, inner[i][1])], (0, 1 if up else -1, 0))


def wall_band(part, outline_a, outline_b, ya, yb, toward_centre, centre):
    """Quads joining two outlines at heights ya (outline_a) and yb (outline_b), facing toward (or away from) a centre point."""
    n = len(outline_a)
    for i in range(n):
        j = (i + 1) % n
        pts = [(outline_a[i][0], ya, outline_a[i][1]), (outline_a[j][0], ya, outline_a[j][1]), (outline_b[j][0], yb, outline_b[j][1]), (outline_b[i][0], yb, outline_b[i][1])]
        mx = sum(p[0] for p in pts) / 4; mz = sum(p[2] for p in pts) / 4
        v = (centre[0] - mx, 0, centre[1] - mz)
        part.face(pts, v if toward_centre else (-v[0], 0, -v[2]))


def rect_ray(cx, cz, x0, x1, z0, z1, n):
    """Points on a rectangle's edge, one per direction from (cx, cz) (pairs with ellipse(): a counter with a hole)."""
    out = []
    for k in range(n):
        a = 2 * math.pi * k / n; dx, dz = math.cos(a), math.sin(a)
        t = min([(x1 - cx) / dx if dx > 1e-9 else 1e9, (x0 - cx) / dx if dx < -1e-9 else 1e9,
                 (z1 - cz) / dz if dz > 1e-9 else 1e9, (z0 - cz) / dz if dz < -1e-9 else 1e9])
        out.append((cx + t * dx, cz + t * dz))
    return out


def cyl(part, x, z, y0, y1, r, n=16):
    part.lathe(x, z, y0, [(0, r), (y1 - y0, r)], n)


def rod(part, a, b, r, n=10):
    """A round rod between two points (spec), as a swept circle."""
    part.sweep([a, b], [(r * math.cos(2 * math.pi * k / n), r * math.sin(2 * math.pi * k / n)) for k in range(n)])


def hang_towel(part, axis, rc, inward, ry, a, b, drop, g):
    """A towel folded over a rod (rod centre rc off the wall line along `axis`, height ry, radius 1 cm): a 13 mm leaf each side of the
    rod at g..g+0.013 from its centre, ending inside a fold laid over the top, so nothing passes through the rod. a..b along the wall.
    Layering: the first towel g = 0.012, one hung over it g = 0.028 (its fold sits on the first one's)."""
    def bx(d0, d1, y0, y1):
        u0, u1 = sorted((rc + inward * d0, rc + inward * d1))
        if axis == "x":
            part.box(u0, u1, y0, y1, a, b)
        else:
            part.box(a, b, y0, y1, u0, u1)
    f0 = ry + 0.011 + (g - 0.012)                                  # the fold's underside
    bx(-g - 0.013, -g, ry - drop * 0.92, f0 + 0.006)               # back leaf (wall side)
    bx(g, g + 0.013, ry - drop, f0 + 0.006)                        # front leaf
    bx(-g - 0.015, g + 0.015, f0, f0 + 0.012)                      # the fold over the rod


# ================================================================ parents' ensuite
PB = D["parents_bath"]
V = PB["vanity"]; vx0, vx1 = V["x"]; vz0, vz1 = V["z"]; TOP = V["top"]; SL = V["slab"]; OH = V["overhang"]
WALL_A = max(z for _, z in POLY["parents_bath"])                # the vanity wall's face (geometry.json parents_bath; 5.17 since Oct 20)
assert abs(vz1 + GAP - WALL_A) < 0.002, (vz1, WALL_A)            # bathrooms.json's vanity must follow the wall
ivory, marble, brass, gilt = P("BA_Ivory"), P("BA_Marble"), P("BA_Brass"), P("BA_Gilt")
porc = P("BA_Porcelain")
toe, toe_in = V["toe"]
# carcass: drawer bank, knee space (open), sink cabinet; the front face set back by the doors' 2 cm
fz = vz0 + 0.02
BANKS = [V["drawers_x"], V["drawers_door_x"]]                  # the window-end bank (film 4398) and the door-end bank (Marina 196/225/228 s)
for a, b in BANKS + [V["sink_x"]]:
    ivory.box(a, b, toe, TOP - SL, fz, vz1)                      # case
    P("BA_Shadow").box(a + 0.01, b - 0.01, 0.0, toe, fz + toe_in, vz1)   # recessed toe kick
ivory.box(V["knee_x"][0], V["knee_x"][1], TOP - SL - 0.10, TOP - SL, fz, vz1)   # the knee space's apron (a pencil drawer front)
# drawer fronts (4) with brass pulls, the knee space's pencil drawer, the sink section's two dark doors with brass towel rings
hs = (TOP - SL - toe) / 4
for dx0, dx1 in BANKS:
    for k in range(4):
        y0, y1 = toe + k * hs + 0.004, toe + (k + 1) * hs - 0.004
        ivory.box(dx0 + 0.006, dx1 - 0.006, y0, y1, vz0, fz)
        brass.box((dx0 + dx1) / 2 - 0.05, (dx0 + dx1) / 2 + 0.05, (y0 + y1) / 2 - 0.006, (y0 + y1) / 2 + 0.006, vz0 - 0.022, vz0)
kx0, kx1 = V["knee_x"]
ivory.box(kx0 + 0.006, kx1 - 0.006, TOP - SL - 0.096, TOP - SL - 0.004, vz0, fz)
brass.box((kx0 + kx1) / 2 - 0.04, (kx0 + kx1) / 2 + 0.04, TOP - SL - 0.056, TOP - SL - 0.044, vz0 - 0.02, vz0)
sx0, sx1 = V["sink_x"]
dark = P("BA_MarbleDark", "BA_Marble")
for a, b in ((sx0 + 0.006, (sx0 + sx1) / 2 - 0.003), ((sx0 + sx1) / 2 + 0.003, sx1 - 0.006)):
    dark.box(a, b, toe + 0.004, TOP - SL - 0.004, vz0, fz)
    cx = (a + b) / 2
    brass.box(cx - 0.012, cx + 0.012, TOP - SL - 0.10, TOP - SL - 0.07, vz0 - 0.015, vz0)          # the ring's mount
    brass.sweep([(cx + 0.075 * math.cos(t), TOP - SL - 0.17 + 0.075 * math.sin(t), vz0 - 0.03) for t in [math.pi / 2 - 2 * math.pi * k / 24 for k in range(25)]],
                [(0.006 * math.cos(2 * math.pi * k / 8), 0.006 * math.sin(2 * math.pi * k / 8)) for k in range(8)])
# the counter: a slab round the oval sink opening, nosing 2 cm, back to the wall face
S = V["sink"]; N = 64
hole = ellipse(S["x"], S["z"], S["rx"], S["rz"], N)
cz0, cz1, cx0, cx1 = vz0 - OH, WALL_A, 0.343, vx1 + OH
outer = rect_ray(S["x"], S["z"], cx0, cx1, cz0, cz1, N)
ering(marble, outer, hole, TOP, True)
ering(marble, outer, hole, TOP - SL, False)
wall_band(marble, outer, outer, TOP - SL, TOP, False, (S["x"], S["z"]))
wall_band(marble, hole, hole, TOP - SL, TOP, True, (S["x"], S["z"]))
marble.box(cx0, cx1, TOP, TOP + V["backsplash"], WALL_A - 0.02, WALL_A)          # backsplash on the wall
# the undermount basin: an open bowl (faces toward its axis), its rim tucked under the slab
bowl = P("BA_Basin", "BA_Porcelain")
rings = [(TOP - SL, 1.06), (TOP - SL - 0.05, 0.98), (TOP - SL - 0.10, 0.82), (TOP - SL - S["depth"] + 0.02, 0.55), (TOP - SL - S["depth"], 0.0)]
prev = None
for y, f in rings:
    ring = ellipse(S["x"], S["z"], S["rx"] * max(f, 0.02), S["rz"] * max(f, 0.02), N)
    if prev:
        wall_band(bowl, prev[1], ring, prev[0], y, True, (S["x"], S["z"]))
    prev = (y, ring)
# taps: widespread, brass, behind the sink (film 4398: lever handles either side of a high spout)
tz = S["z"] + S["rz"] + 0.06
brass.lathe(S["x"], tz, TOP, [(0, 0.028), (0.03, 0.022), (0.05, 0.016), (0.16, 0.014), (0.18, 0.012)], 16)
brass.sweep([(S["x"], TOP + 0.17, tz), (S["x"], TOP + 0.20, tz - 0.04), (S["x"], TOP + 0.19, tz - 0.10), (S["x"], TOP + 0.15, tz - 0.13)],
            [(0.011 * math.cos(2 * math.pi * k / 10), 0.011 * math.sin(2 * math.pi * k / 10)) for k in range(10)])
for dxh in (-0.17, 0.17):
    brass.lathe(S["x"] + dxh, tz, TOP, [(0, 0.026), (0.025, 0.018), (0.07, 0.013), (0.085, 0.016)], 14)
    brass.sweep([(S["x"] + dxh, TOP + 0.08, tz), (S["x"] + dxh * 1.5, TOP + 0.10, tz - 0.02)],
                [(0.006 * math.cos(2 * math.pi * k / 8), 0.006 * math.sin(2 * math.pi * k / 8)) for k in range(8)])
# the gilt mirror: four mitred bars with a raised bead, the glass 1.5 cm behind the frame's face
M = PB["mirror"]; mx0, mx1 = M["x"]; my0, my1 = M["y"]; fw = M["frame"]; fz0 = WALL_A - 0.002
for (a, b, c, d) in ((mx0, mx1, my0, my0 + fw), (mx0, mx1, my1 - fw, my1), (mx0, mx0 + fw, my0 + fw, my1 - fw), (mx1 - fw, mx1, my0 + fw, my1 - fw)):
    gilt.box(a, b, c, d, fz0 - 0.045, fz0)
for (a, b, c, d) in ((mx0 + 0.02, mx1 - 0.02, my0 + 0.03, my0 + 0.05), (mx0 + 0.02, mx1 - 0.02, my1 - 0.05, my1 - 0.03),
                     (mx0 + 0.03, mx0 + 0.05, my0 + 0.05, my1 - 0.05), (mx1 - 0.05, mx1 - 0.03, my0 + 0.05, my1 - 0.05)):
    gilt.box(a, b, c, d, fz0 - 0.060, fz0 - 0.045)               # the bead stands 1.5 cm proud of the frame
P("BA_MirrorGlass").box(mx0 + fw - 0.01, mx1 - fw + 0.01, my0 + fw - 0.01, my1 - fw + 0.01, fz0 - 0.030, fz0 - 0.004)
# bracket shelves (brass brackets, ivory boards) at both ends of the counter
for key in ("shelves_door_end", "shelves_window_end"):
    sh = PB[key]; a, b = sh["x"]
    for y in sh["ys"]:
        ivory.box(a, b, y, y + 0.022, WALL_A - sh["depth"], WALL_A - 0.002)
        for xb in (a + 0.03, b - 0.03):
            brass.box(xb - 0.006, xb + 0.006, y - 0.16, y, WALL_A - 0.02, WALL_A - 0.002)
            brass.sweep([(xb, y - 0.15, WALL_A - 0.02), (xb, y - 0.06, WALL_A - 0.11), (xb, y - 0.004, WALL_A - 0.20)],
                        [(0.005 * math.cos(2 * math.pi * k / 6), 0.005 * math.sin(2 * math.pi * k / 6)) for k in range(6)])
# the tub: a rounded front apron, rim, basin; the dark marble band on the two walls above its deck
T = PB["tub"]; tx0, tx1 = T["x"]; tz0, tz1 = T["z"]; RIM = T["rim"]; BU = T["bulge"]
def tub_outline(x0, x1, z0, z1, bulge, n=24):
    pts = [(x0, z0), (x1, z0)]
    for k in range(n + 1):                                      # the front: a shallow arc bulging toward +z
        t = k / n; x = x1 - t * (x1 - x0); pts.append((x, z1 - bulge + bulge * math.sin(math.pi * t)))
    return pts[:-1] + [(x0, z1 - bulge)]
outer = tub_outline(tx0, tx1, tz0, tz1, BU)
inner = tub_outline(tx0 + 0.09, tx1 - 0.09, tz0 + 0.09, tz1 - 0.09, BU * 0.7)
# resample both to the same count along their perimeters so the rim is one ring
def resample(pts, n):
    L = [0.0]
    for (ax, az), (bx, bz) in zip(pts, pts[1:] + pts[:1]):
        L.append(L[-1] + math.hypot(bx - ax, bz - az))
    out, j = [], 0
    for k in range(n):
        s = L[-1] * k / n
        while L[j + 1] < s:
            j += 1
        (ax, az), (bx, bz) = pts[j], pts[(j + 1) % len(pts)]; t = (s - L[j]) / max(L[j + 1] - L[j], 1e-9)
        out.append((ax + t * (bx - ax), az + t * (bz - az)))
    return out
outer, inner = resample(outer, 96), resample(inner, 96)
cen = ((tx0 + tx1) / 2, (tz0 + tz1) / 2)
tub = P("BA_Tub", "BA_Porcelain")
wall_band(tub, outer, outer, 0.0, RIM, False, cen)
ering(tub, outer, inner, RIM, True)
floor_ring = [(cen[0] + 0.85 * (x - cen[0]), cen[1] + 0.8 * (z - cen[1])) for x, z in inner]
wall_band(tub, inner, floor_ring, RIM, 0.14, True, cen)
tub.face([(x, 0.14, z) for x, z in floor_ring], (0, 1, 0))
blk = P("BA_BlackMarble")
blk.box(0.343 + 0.0, tx1 + 0.02, RIM, RIM + 0.16, 0.872, 0.872 + 0.02)            # upstand on the tub's back wall
blk.box(0.343, 0.343 + 0.02, RIM, RIM + 0.16, 0.892, tz1 - BU + 0.02)              # and on the window wall's end
brass.lathe((tx0 + tx1) / 2, tz0 + 0.05, RIM, [(0, 0.03), (0.03, 0.022), (0.15, 0.016), (0.17, 0.014)], 16)
brass.sweep([((tx0 + tx1) / 2, RIM + 0.16, tz0 + 0.05), ((tx0 + tx1) / 2, RIM + 0.18, tz0 + 0.12), ((tx0 + tx1) / 2, RIM + 0.15, tz0 + 0.18)],
            [(0.012 * math.cos(2 * math.pi * k / 10), 0.012 * math.sin(2 * math.pi * k / 10)) for k in range(10)])
for dxh in (-0.12, 0.12):
    brass.lathe((tx0 + tx1) / 2 + dxh, tz0 + 0.05, RIM, [(0, 0.024), (0.06, 0.016), (0.08, 0.02)], 12)
# the quadrant shower: a white tray, black-framed curved glass (a gap for the door), brass head and mixer on the notch wall
SH = PB["shower"]; (qx, qz), R = SH["corner"], SH["r"]
cxs, czs, rs = qx - GAP, qz + GAP, R - GAP                       # the quadrant's centre: the notch corner, off both walls
arc = [(cxs - rs * math.cos(t), czs + rs * math.sin(t)) for t in [math.pi / 2 * k / 24 for k in range(25)]]
prism(P("BA_Tray", "BA_Porcelain"), [(cxs, czs)] + arc, 0.0, SH["tray"])
glass, frame = P("BA_ShowerGlass"), P("BA_BlackFrame")
d0, d1 = SH["door"]                                             # the open door, as a fraction of the arc
gy0, gy1 = SH["tray"], SH["tray"] + SH["glass_h"]
for (f0, f1) in ((0.0, d0), (d1, 1.0)):
    seg = arc[int(round(f0 * 24)):int(round(f1 * 24)) + 1]
    for (ax, az), (bx, bz) in zip(seg, seg[1:]):
        glass.face([(ax, gy0, az), (bx, gy0, bz), (bx, gy1, bz), (ax, gy1, az)], ((ax + bx) / 2 - qx, 0, (az + bz) / 2 - qz))
for f in (0.0, d0, d1, 1.0):
    px, pz = arc[int(round(f * 24))]
    frame.box(px - 0.015, px + 0.015, gy0, gy1 + 0.02, pz - 0.015, pz + 0.015)
frame.sweep([(x, gy1 + 0.01, z) for x, z in arc], [(0.015, 0.012), (-0.015, 0.012), (-0.015, -0.012), (0.015, -0.012)])
brass.sweep([(qx - 0.002, 1.95, qz + R * 0.55), (qx - 0.18, 1.95, qz + R * 0.55)], [(0.011 * math.cos(2 * math.pi * k / 10), 0.011 * math.sin(2 * math.pi * k / 10)) for k in range(10)])
brass.lathe(qx - 0.20, qz + R * 0.55, 1.90, [(0, 0.0), (0.0, 0.065), (0.035, 0.03), (0.05, 0.012)], 20)
brass.lathe(qx - 0.045, qz + R * 0.55, 1.08, [(0, 0.04), (0.03, 0.04)], 16)              # mixer plate (a disc on the wall... as a short drum)
# the light bar: a brass backplate with four globes (the globes glow: BA_Globe is emissive in Unity)
LB = PB["light_bar"]; lx0, lx1 = LB["x"]; ly = LB["y"]; lz = LB["wall_z"]
brass.box(lx0, lx1, ly - 0.05, ly + 0.05, lz + 0.002, lz + 0.035)
for k in range(LB["globes"]):
    gx = lx0 + (lx1 - lx0) * (k + 0.5) / LB["globes"]
    brass.lathe(gx, lz + 0.075, ly - 0.012, [(0, 0.014), (0.025, 0.014)], 10)
    P("BA_Globe").lathe(gx, lz + 0.09, ly - 0.06, [(0, 0.0), (0.012, 0.035), (0.05, 0.05), (0.09, 0.035), (0.10, 0.0)], 16)
# prints: gilt frames, cream mats, a plate on its own UVs (BA_PrintL/R/M, the foyer's public-domain fruit plates)
PR = PB["prints"]; wx = PR["wall_x"]; py0, py1 = PR["y"]
for k, (a, b) in enumerate(PR["z"]):
    gilt.box(wx + 0.002, wx + 0.03, py0, py1, a, b)
    P("BA_Mat").box(wx + 0.03, wx + 0.035, py0 + 0.035, py1 - 0.035, a + 0.035, b - 0.035)
    pl = P(["BA_PrintL", "BA_PrintM", "BA_PrintR"][k])
    pl.face_uv([(wx + 0.045, py0 + 0.09, b - 0.08), (wx + 0.045, py0 + 0.09, a + 0.08), (wx + 0.045, py1 - 0.09, a + 0.08), (wx + 0.045, py1 - 0.09, b - 0.08)],
               [(0, 0), (1, 0), (1, 1), (0, 1)], (1, 0, 0))
# towel bars with layered towels (a sage bath towel, a dark-green one over it, folded in thirds)
TB = PB["towel_bars"]; tbx = TB["wall_x"]; ty = TB["y"]
for a, b in TB["z"]:
    for zz in (a + 0.03, b - 0.03):
        brass.box(tbx + 0.002, tbx + 0.065, ty - 0.02, ty + 0.02, zz - 0.02, zz + 0.02)
    rod(brass, (tbx + 0.065, ty, a + 0.01), (tbx + 0.065, ty, b - 0.01), 0.010)
    hang_towel(P("BA_TowelSage"), "x", tbx + 0.065, +1, ty, a + 0.05, b - 0.05, 0.58, 0.012)
    hang_towel(P("BA_TowelDark"), "x", tbx + 0.065, +1, ty, (a + b) / 2 - 0.10, (a + b) / 2 + 0.10, 0.50, 0.028)
# the toilet: the bought model (store_props.json parents_toilet; user Oct 20), walk colliders in SpecGreybox.Bathrooms
# the window: lace panels either side and a shirred lace valance (production photo 165 s; Marina's is a grey swag)
W = next(o for o in OPEN if o["kind"] == "window" and o["between"] == ["parents_bath"])
def Pw(u, y, d):                                                # u along the window wall (spec z), d into the room
    return (0.343 + d, y, u)
lace = P("BA_Lace")
sheer_panel(lace, lace, Pw, W["lo"] - 0.12, W["lo"] + 0.10, W["sill"] + 0.01, W["head"] + 0.13, 0.07, 1.3, P0=0.06, A0=0.014)
sheer_panel(lace, lace, Pw, W["hi"] - 0.10, W["hi"] + 0.06, W["sill"] + 0.01, W["head"] + 0.13, 0.07, 2.7, P0=0.06, A0=0.014)
valance(lace, Pw, W["lo"] - 0.32, W["hi"] + 0.08, W["head"] - 0.12, W["head"] + 0.24, 0.10)
P("BA_Bin").lathe(PB["wastebasket"]["x"], PB["wastebasket"]["z"], 0.0, [(0, 0.11), (0.33, 0.13), (0.34, 0.135)], 4)   # square-ish dark basket
# recessed downlight trim (production photo 165 s)
cl = PB["ceiling_lamp"]["at"]
P("BA_White", "BA_Ivory").lathe(cl[0], cl[2], 2.495, [(0, 0.09), (0.004, 0.09)], 24)

# ---------------------------------------------------------------- parents' counter clutter (props: BathroomProps.glb, movable)
_before = set(props)   # the clutter below is written against the Oct 19 wall (z 4.436) and door-end shelf (x 1.97); moved with them after
def bottle(name, mat, x, z, h, r, cap_mat="BA_PropBlack", cap_h=0.03, square=False):
    q = Q(name + "_body", mat)
    n = 4 if square else 14
    q.lathe(x, z, TOP + V["backsplash"] * 0 + 0.0, [(0, r), (h * 0.8, r), (h * 0.9, r * 0.6), (h, r * 0.45)], n)
    Q(name + "_cap", cap_mat).lathe(x, z, TOP + h, [(0, r * 0.45), (cap_h, r * 0.45)], 12)
bottle("aftershave", "BA_PropAftershave", 1.50, 3.92, 0.15, 0.028, cap_h=0.05)           # film 4408: the dark bottle by the sink
bottle("shower_to_shower", "BA_PropMint", 1.52, 4.00, 0.16, 0.035, cap_mat="BA_PropWhite")  # film 4398/4408: the mint Shower to Shower
bottle("shave_can", "BA_PropSteel", 1.60, 3.94, 0.17, 0.028, cap_mat="BA_PropRed")
bottle("pump_soap", "BA_PropWhite", 2.12, 3.95, 0.15, 0.032, cap_mat="BA_PropWhite")
bottle("deodorant", "BA_PropWhite", 0.55, 4.25, 0.16, 0.03, cap_mat="BA_PropMint")
for k, (x, h) in enumerate(((0.42, 0.13), (0.50, 0.17), (0.60, 0.11), (0.68, 0.15))):     # the window-end shelf's toiletries (film: amber bottles)
    bottle(f"shelf_bottle_{k}", "BA_PropAmber", x, 4.33, h, 0.025, cap_mat="BA_PropGold")
    for q in (props[f"shelf_bottle_{k}_body"], props[f"shelf_bottle_{k}_cap"]):
        q.v = [(vx, vy - TOP + PB["shelves_window_end"]["ys"][k % 2] + 0.022, vz) for vx, vy, vz in q.v]
Q("aquafresh", "BA_PropAqua").box(1.40, 1.56, TOP, TOP + 0.04, 4.34, 4.39)               # the toothpaste on the counter behind the taps
Q("toothbrush_cup", "BA_PropCrystal").lathe(1.70, 4.33, TOP, [(0, 0.03), (0.10, 0.036), (0.105, 0.036)], 16); props["toothbrush_cup"].f.pop()   # open top: the brush stands in it
Q("toothbrush", "BA_PropRed").sweep([(1.70, TOP + 0.04, 4.33), (1.71, TOP + 0.19, 4.34)], [(0.005 * math.cos(2 * math.pi * k / 6), 0.005 * math.sin(2 * math.pi * k / 6)) for k in range(6)])
Q("cotton_balls", "BA_PropCotton").box(1.02, 1.30, TOP, TOP + 0.08, 3.92, 4.10)           # film 4398: the bag of cotton balls (pink/green print)
Q("bud_vase", "BA_PropJade").lathe(1.30, 4.32, TOP, [(0, 0.035), (0.01, 0.02), (0.18, 0.018), (0.24, 0.026)], 14); props["bud_vase"].f.pop()   # open mouth   # film 4398: tall jade vase
for k in range(5):                                              # its dried wheat and red flowers, fanned 5 cm apart
    a = -1.0 + 0.5 * k
    tip = (1.30 + 0.09 * math.sin(a), TOP + 0.44 + 0.03 * (k % 2), 4.32 - 0.05 * math.cos(a))
    Q("bud_stems", "BA_PropWheat").sweep([(1.30 + 0.004 * math.sin(a), TOP + 0.22, 4.32 - 0.004 * math.cos(a)), (tip[0], tip[1] - 0.010, tip[2])],   # stops under its flower (ran through it: clash)
                                         [(0.003, 0), (0, 0.003), (-0.003, 0), (0, -0.003)])
    Q("bud_flowers", "BA_PropRed").lathe(tip[0], tip[2], tip[1] - 0.008, [(0, 0.0), (0.012, 0.016), (0.03, 0.0)], 8)
for k, (y, tone) in enumerate(((0.0, "BA_TowelSage"), (0.05, "BA_TowelDark"), (0.10, "BA_TowelWhite"))):   # towel stack on the counter's door end
    Q(f"towel_stack_{k}", tone).box(1.99, 2.23, TOP + y, TOP + y + 0.048, 4.12, 4.40)
for k, y in enumerate(PB["shelves_door_end"]["ys"]):              # green towels on the door-end shelves
    for j in range(3):
        Q(f"shelf_towel_{k}_{j}", "BA_TowelSage" if j % 2 == 0 else "BA_TowelDark").box(1.99, 2.23, y + 0.022 + j * 0.05, y + 0.022 + (j + 1) * 0.05 - 0.003, 4.20, 4.42)

DZ, DXS = WALL_A - 4.436, PB["shelves_door_end"]["x"][0] - 1.97   # Oct 20: the vanity wall moved 0.73 m, the door-end shelves to the new door end
for name in set(props) - _before:
    dx = DXS if name.startswith(("towel_stack", "shelf_towel")) else 0.0
    props[name].v = [(vx + dx, vy, vz + DZ) for vx, vy, vz in props[name].v]

# ================================================================ hall bath
HB = D["hall_bath"]
HP = POLY["hall_bath"]
tile, black = P("BA_Subway"), P("BA_TileBlack")
WN = HB["wainscot"]; TP = WN["proud"]; CP = WN["cap_proud"]
obst = [p["box"] for o in OPEN if "hall_bath" in o["between"] for p in o["pieces"] if not p.get("by")]
# + each opening's own void (walk note Oct 20 06:49: the tile ran straight across the door between its casing legs, and across the
# window above its stool): along the wall lo..hi, sill (or the floor) to head, through the wall's thickness (its header box)
obst += [o["header"]["box"][:4] + [o["sill"] or 0.0, o["head"]] for o in OPEN if "hall_bath" in o["between"] and o.get("header")]


def free_runs(axis, c, lo, hi, y0, y1):
    """Stretches of the wall line (axis 'x': the wall x = c, along z) clear of the openings' casings/stools within y0..y1."""
    cuts = []
    for b in obst:
        x0, x1, z0, z1, by0, by1 = b
        if by1 <= y0 or by0 >= y1:
            continue
        if axis == "x" and x0 - 0.03 <= c <= x1 + 0.03:
            cuts.append((z0, z1))
        if axis == "z" and z0 - 0.03 <= c <= z1 + 0.03:
            cuts.append((x0, x1))
    runs, s = [], lo
    for a, b in sorted(cuts):
        if b <= s or a >= hi:
            continue
        if a > s:
            runs.append((s, a))
        s = max(s, b)
    if s < hi:
        runs.append((s, hi))
    return [r for r in runs if r[1] - r[0] > 0.01]


def band(part, axis, c, inward, lo, hi, y0, y1, d):
    """A tile band on a wall face: axis 'x' = the wall x = c (runs along z), 'z' = the wall z = c; inward = +1/-1 into the room."""
    cuts = sorted({y0, y1} | {v for b in obst for v in (b[4], b[5]) if y0 < v < y1})
    for ya, yb in zip(cuts, cuts[1:]):
        for a, b in free_runs(axis, c, lo, hi, ya, yb):
            if axis == "x":
                xa, xb = sorted((c, c + inward * d)); part.box(xa, xb, ya, yb, a, b)
            else:
                za, zb = sorted((c, c + inward * d)); part.box(a, b, ya, yb, za, zb)


TB_ = HB["tub"]; ex0, ex1 = HB["tub_end_wall"]["x"]
# (wall axis, coordinate, inward, run lo, run hi, tile top) for each face of the room; the alcove's faces tile to tub_tile_top
WALLS = [("z", 7.778, 1, 9.1135, ex0, WN["tub_tile_top"]), ("z", 7.778, 1, ex1, 11.664, WN["cap"][0]),
         ("x", 11.664, -1, 7.778, 11.43, WN["cap"][0]), ("z", 11.43, -1, 8.511, 11.664, WN["cap"][0]),
         ("x", 8.511, 1, 8.781, 11.43, WN["cap"][0]), ("z", 8.781, 1, 8.511, 9.1135, WN["cap"][0]),
         ("x", 9.1135, 1, 7.778, TB_["z"][1], WN["tub_tile_top"]), ("x", 9.1135, 1, TB_["z"][1], 8.781, WN["cap"][0])]
for ax, c, inw, lo, hi, top in WALLS:
    # runs meet at inside corners: shorten each run by the tile depth where it meets a face running across it (no overlap)
    lo2 = lo + (TP if any(w[0] != ax and abs(w[1] - lo) < 1e-3 for w in WALLS) else 0)
    hi2 = hi - (TP if any(w[0] != ax and abs(w[1] - hi) < 1e-3 for w in WALLS) else 0)
    if top > 1.5:
        band(tile, ax, c, inw, lo2, hi2, WN["tile_from"], top, TP)
        band(black, ax, c, inw, lo2, hi2, top, top + 0.055, CP)
        continue
    band(tile, ax, c, inw, lo2, hi2, WN["tile_from"], WN["liner"][0], TP)
    band(black, ax, c, inw, lo2, hi2, WN["liner"][0], WN["liner"][1], TP + 0.003)
    band(tile, ax, c, inw, lo2, hi2, WN["liner"][1], WN["cap"][0], TP)
    band(black, ax, c, inw, lo2, hi2, WN["cap"][0], WN["cap"][1], CP)
# the alcove's tiled end wall (its back 1.5 cm off the back wall: the baseboard runs behind it) and a black cap on top
tile.box(ex0, ex1, 0.0, HB["tub_end_wall"]["y"][1], 7.778 + TP, TB_["z"][1])
black.box(ex0 - 0.005, ex1 + 0.005, HB["tub_end_wall"]["y"][1], HB["tub_end_wall"]["y"][1] + 0.04, 7.778 + TP, TB_["z"][1] + 0.005)
# the tub: a white enamel alcove tub with a straight apron
hx0, hx1 = TB_["x"]; hz0, hz1 = TB_["z"]; HR = TB_["rim"]
o2 = resample([(hx0, hz0 + TP), (ex0 - 0.002, hz0 + TP), (ex0 - 0.002, hz1), (hx0, hz1)], 64)
i2 = resample([(hx0 + 0.06, hz0 + TP + 0.06), (ex0 - 0.06, hz0 + TP + 0.06), (ex0 - 0.06, hz1 - 0.07), (hx0 + 0.06, hz1 - 0.07)], 64)
ht = P("BA_HallTub", "BA_Porcelain")
c2 = ((hx0 + ex0) / 2, (hz0 + hz1) / 2)
wall_band(ht, o2, o2, 0.0, HR, False, c2); ering(ht, o2, i2, HR, True)
f2 = [(c2[0] + 0.92 * (x - c2[0]), c2[1] + 0.8 * (z - c2[1])) for x, z in i2]
wall_band(ht, i2, f2, HR, 0.08, True, c2); ht.face([(x, 0.08, z) for x, z in f2], (0, 1, 0))
SHH = HB["shower_head"]
brass.sweep([(SHH["wall_x"] + TP, SHH["y"], SHH["z"]), (SHH["wall_x"] + 0.20, SHH["y"] + 0.02, SHH["z"])], [(0.011 * math.cos(2 * math.pi * k / 10), 0.011 * math.sin(2 * math.pi * k / 10)) for k in range(10)])
brass.lathe(SHH["wall_x"] + 0.22, SHH["z"], SHH["y"] - 0.05, [(0, 0.0), (0.0, 0.055), (0.03, 0.025), (0.05, 0.012)], 18)
for dz in (-0.12, 0.12):
    brass.lathe(SHH["wall_x"] + TP + 0.02, SHH["z"] + dz, 0.95, [(0, 0.025), (0.05, 0.02)], 12)
brass.sweep([(SHH["wall_x"] + TP, HR + 0.10, SHH["z"]), (SHH["wall_x"] + 0.14, HR + 0.10, SHH["z"])], [(0.012 * math.cos(2 * math.pi * k / 10), 0.012 * math.sin(2 * math.pi * k / 10)) for k in range(10)])
# the shower curtain: the film's green, hung from a brass rod across the alcove's mouth, drawn toward the end wall
CU = HB["curtain"]
rod(brass, (hx0 + TP + 0.005, CU["rod_y"], CU["z"]), (ex0 - 0.002, CU["rod_y"], CU["z"]), 0.011)
def Pc(u, y, d):
    return (u, y, CU["z"] - d)
sheer_panel(P("BA_ShowerCurtain"), P("BA_ShowerCurtain"), Pc, CU["x"][0], CU["x"][1], CU["y"][0], CU["y"][1], 0.0, 0.6, P0=0.11, A0=0.025)
# the toilet: the bought model (store_props.json hall_toilet; user Oct 20)
# the pedestal sink against the tile on the wall z = 11.43
SK = HB["sink"]; skx = SK["x"]; sw = 11.43 - TP
porc.box(skx - 0.30, skx + 0.30, SK["rim"] - 0.17, SK["rim"], sw - 0.48, sw - 0.002)        # the basin's body (film 336: a square-shouldered basin)
P("BA_Basin2", "BA_Porcelain")
inner_b = ellipse(skx, sw - 0.25, 0.21, 0.15, 40); outer_b = rect_ray(skx, sw - 0.25, skx - 0.30, skx + 0.30, sw - 0.48, sw - 0.002, 40)
del parts["BA_Porcelain"].f[-6 + 0:-5 + 0]                       # the body's top face is replaced by the ring + bowl below
ering(parts["BA_Basin2"], outer_b, inner_b, SK["rim"], True)
prev = (SK["rim"], inner_b)
for y, f in ((SK["rim"] - 0.06, 0.85), (SK["rim"] - 0.12, 0.5), (SK["rim"] - 0.14, 0.02)):
    ring = ellipse(skx, sw - 0.25, 0.21 * f, 0.15 * f, 40); wall_band(parts["BA_Basin2"], prev[1], ring, prev[0], y, True, (skx, sw - 0.25)); prev = (y, ring)
porc.lathe(skx, sw - 0.20, 0.0, [(0, 0.15), (0.05, 0.11), (0.25, 0.085), (SK["rim"] - 0.26, 0.10), (SK["rim"] - 0.17, 0.13)], 20)
for dxh in (-0.17, 0.17):
    brass.lathe(skx + dxh, sw - 0.05, SK["rim"], [(0, 0.022), (0.06, 0.012), (0.08, 0.02)], 12)
brass.sweep([(skx, SK["rim"] + 0.05, sw - 0.05), (skx, SK["rim"] + 0.06, sw - 0.14)], [(0.01 * math.cos(2 * math.pi * k / 10), 0.01 * math.sin(2 * math.pi * k / 10)) for k in range(10)])
# the medicine cabinet: a white case with a moulded top and a mirror door, on the paper just above the cap
MC = HB["cabinet"]; mca, mcb = MC["x"]; mcy0, mcy1 = MC["y"]; wz = 11.43 - 0.002
whitep = P("BA_WhitePaint")
whitep.box(mca, mcb, mcy0, mcy1, wz - MC["depth"], wz)
whitep.box(mca - 0.02, mcb + 0.02, mcy1, mcy1 + 0.04, wz - MC["depth"] - 0.02, wz)        # cornice
whitep.box(mca - 0.01, mcb + 0.01, mcy0 - 0.03, mcy0, wz - MC["depth"] - 0.015, wz)       # sill shelf
P("BA_MirrorGlass").box(mca + 0.04, mcb - 0.04, mcy0 + 0.05, mcy1 - 0.05, wz - MC["depth"] - 0.012, wz - MC["depth"])   # 1.2 cm proud (a 6 mm plate z-fought the case)
# the double sconce above it (film 336: two ruffled frosted shades side by side over the cabinet): a brass backplate, two arms,
# a tulip shade on each with a scalloped rim (the globe was one; walk note 06:58)
SC = HB["sconce"]; sy, sd = SC["y"], SC["out"]
brass.box(SC["x"] - 0.04, SC["x"] + 0.04, sy + 0.02, sy + 0.14, wz - 0.015, wz)
for ax in SC["arms"]:
    brass.sweep([(SC["x"], sy + 0.08, wz - 0.015), (ax, sy + 0.17, wz - sd * 0.6), (ax, sy + 0.17, wz - sd), (ax, sy + 0.135, wz - sd)],   # over the shade, down into its cup (a level arm crossed the glass: clash)
                [(0.007 * math.cos(2 * math.pi * k / 8), 0.007 * math.sin(2 * math.pi * k / 8)) for k in range(8)])
    brass.lathe(ax, wz - sd, sy + 0.115, [(0, 0.022), (0.02, 0.02)], 12)                         # the cup (top sy + 0.135)
    # tulip shade, opening down, its rim ruffled by 8 scallops; glass 4 mm thick (an outer and an inner skin)
    shade = P("BA_Globe")
    rings = [(sy + 0.12, 0.035), (sy + 0.09, 0.055), (sy + 0.04, 0.075), (sy - 0.01, 0.085)]
    def outline(r, ruffle, k=1.0):
        return [(ax + k * r * (1 + ruffle * math.cos(8 * t)) * math.cos(t), wz - sd + k * r * (1 + ruffle * math.cos(8 * t)) * math.sin(t))
                for t in [2 * math.pi * i / 32 for i in range(32)]]
    for k, inward in ((1.0, False), (0.95, True)):
        ols = [outline(r, 0.12 if j == len(rings) - 1 else 0.0, k) for j, (_, r) in enumerate(rings)]
        for (y0, _), (y1, _), oa, ob in zip(rings, rings[1:], ols, ols[1:]):
            wall_band(shade, oa, ob, y0, y1, inward, (ax, wz - sd))
    ering(shade, outline(rings[-1][1], 0.12), outline(rings[-1][1], 0.12, 0.95), rings[-1][0], False)   # the rim's edge, facing down
    ering(shade, outline(rings[0][1], 0.0), outline(rings[0][1], 0.0, 0.95), rings[0][0], True)       # the crown's edge under the cup
# towel bar with white / dark green / white towels (film 336)
HTB = HB["towel_bar"]; bx = HTB["wall_x"] - 0.002; za, zb = HTB["z"]; by = HTB["y"]
for zz in (za + 0.03, zb - 0.03):
    brass.box(bx - 0.065, bx, by - 0.02, by + 0.02, zz - 0.02, zz + 0.02)
rod(brass, (bx - 0.065, by, za + 0.01), (bx - 0.065, by, zb - 0.01), 0.010)
for k, (mat, z0) in enumerate((("BA_TowelWhite", za + 0.08), ("BA_TowelDark", za + 0.24), ("BA_TowelWhite", za + 0.40))):
    hang_towel(P(mat), "x", bx - 0.065, -1, by, z0, z0 + 0.14, 0.45, 0.012)   # clear of the end brackets
# the wicker shelf (three tiers) with toilet paper, the hamper by the door
WS = HB["wicker_shelf"]; wsx0, wsx1 = WS["x"]; wsz0, wsz1 = WS["z"]
wick = P("BA_Wicker")
for xa, za_ in ((wsx0, wsz0), (wsx1 - 0.03, wsz0), (wsx0, wsz1 - 0.03), (wsx1 - 0.03, wsz1 - 0.03)):
    wick.box(xa, xa + 0.03, 0.0, WS["h"], za_, za_ + 0.03)
for y in (0.08, 0.40, WS["h"] - 0.02):
    wick.box(wsx0 + 0.03, wsx1 - 0.03, y, y + 0.02, wsz0 + 0.03, wsz1 - 0.03)
HM = HB["hamper"]
wick.box(HM["x"][0], HM["x"][1], 0.0, HM["h"], HM["z"][0], HM["z"][1])
wick.box(HM["x"][0] - 0.01, HM["x"][1] + 0.01, HM["h"], HM["h"] + 0.03, HM["z"][0] - 0.01, HM["z"][1] + 0.01)
Q("hb_tp_1", "BA_TowelWhite").lathe((wsx0 + wsx1) / 2, wsz0 + 0.12, WS["h"], [(0, 0.055), (0.11, 0.055)], 16)
Q("hb_tp_2", "BA_TowelWhite").lathe((wsx0 + wsx1) / 2, wsz0 + 0.26, 0.42, [(0, 0.055), (0.11, 0.055)], 16)
Q("hb_towels", "BA_TowelWhite").box(wsx0 + 0.05, wsx1 - 0.05, 0.10, 0.22, wsz0 + 0.05, wsz1 - 0.05)
Q("hb_toothbrush_cup", "BA_PropCrystal").lathe(skx + 0.24, sw - 0.06, SK["rim"], [(0, 0.03), (0.10, 0.034)], 14); props["hb_toothbrush_cup"].f.pop()
Q("hb_toothbrush", "BA_PropAqua").sweep([(skx + 0.24, SK["rim"] + 0.04, sw - 0.06), (skx + 0.25, SK["rim"] + 0.19, sw - 0.05)], [(0.005, 0), (0, 0.005), (-0.005, 0), (0, -0.005)])
Q("hb_soap", "BA_PropWhite").box(skx - 0.28, skx - 0.20, SK["rim"], SK["rim"] + 0.025, sw - 0.10, sw - 0.04)
# the film's tall grass in a pot in the corner (film 336; decoration): tapered blades, both faces drawn
PL = HB["plant"]["at"]
P("BA_Pot").lathe(PL[0], PL[1], 0.0, [(0, 0.09), (0.24, 0.12), (0.26, 0.125)], 20)
grass = P("BA_Grass")
for k in range(40):
    a = 2.39996 * k; r0 = 0.01 + 0.05 * ((k * 37) % 11) / 11; h = 0.75 + 0.45 * ((k * 53) % 13) / 13; lean = 0.06 + 0.12 * ((k * 29) % 7) / 7
    bx0, bz0 = PL[0] + r0 * math.cos(a), PL[1] + r0 * math.sin(a)
    al = math.pi * (1.25 + 0.25 * ((k * 17) % 9) / 8)             # lean into the room (-x, -z), clear of the walls and the cabinet
    tx, tz = bx0 + lean * math.cos(al), bz0 + lean * math.sin(al)
    sx, sz = -math.sin(a) * 0.008, math.cos(a) * 0.008
    pts = [(bx0 - sx, 0.25, bz0 - sz), (bx0 + sx, 0.25, bz0 + sz), (tx, 0.25 + h, tz)]
    nrm = (math.cos(a), 0.2, math.sin(a))
    grass.face(pts, nrm); grass.face(list(reversed(pts)), (-nrm[0], -nrm[1], -nrm[2]))
# the window: cream panels either side (Marina 451-486 s: tied back; built straight here)
WH = next(o for o in OPEN if o["kind"] == "window" and o["between"] == ["hall_bath"])
def Ph(u, y, d):
    return (11.664 - d, y, u)
cream = P("BA_CurtainCream")
sheer_panel(cream, cream, Ph, WH["lo"] - 0.30, WH["lo"] + 0.02, WH["sill"] - 0.25, WH["head"] + 0.15, 0.08, 3.1, P0=0.08, A0=0.02)
sheer_panel(cream, cream, Ph, WH["hi"] - 0.02, WH["hi"] + 0.26, WH["sill"] - 0.25, WH["head"] + 0.15, 0.08, 4.4, P0=0.08, A0=0.02)
rod(brass, Ph(WH["lo"] - 0.34, WH["head"] + 0.17, 0.08), Ph(WH["hi"] + 0.30, WH["head"] + 0.17, 0.08), 0.010)

# ---------------------------------------------------------------- export
COL = {"BA_Ivory": ((0.80, 0.77, 0.66), 0.45), "BA_Marble": ((0.03, 0.07, 0.05), 0.15), "BA_Brass": ((0.80, 0.60, 0.28), 0.35),
       "BA_Gilt": ((0.78, 0.58, 0.25), 0.35), "BA_Porcelain": ((0.93, 0.93, 0.90), 0.08), "BA_MirrorGlass": ((0.85, 0.87, 0.88), 0.02),
       "BA_BlackMarble": ((0.02, 0.03, 0.03), 0.15), "BA_ShowerGlass": ((0.85, 0.9, 0.9), 0.05), "BA_BlackFrame": ((0.02, 0.02, 0.02), 0.4),
       "BA_Globe": ((1.0, 0.95, 0.85), 0.3), "BA_Mat": ((0.90, 0.88, 0.82), 0.9), "BA_PrintL": ((0.9, 0.88, 0.8), 0.9),
       "BA_PrintM": ((0.9, 0.88, 0.8), 0.9), "BA_PrintR": ((0.9, 0.88, 0.8), 0.9), "BA_TowelSage": ((0.20, 0.42, 0.30), 0.95),
       "BA_TowelDark": ((0.02, 0.10, 0.05), 0.95), "BA_TowelWhite": ((0.90, 0.90, 0.87), 0.95), "BA_Lace": ((0.90, 0.88, 0.80), 0.9),
       "BA_Bin": ((0.03, 0.03, 0.03), 0.6), "BA_Pot": ((0.35, 0.33, 0.30), 0.5), "BA_Grass": ((0.18, 0.40, 0.14), 0.7), "BA_Shadow": ((0.04, 0.04, 0.04), 0.9), "BA_Subway": ((0.92, 0.92, 0.90), 0.1),
       "BA_TileBlack": ((0.02, 0.02, 0.02), 0.15), "BA_ShowerCurtain": ((0.05, 0.40, 0.18), 0.8), "BA_CurtainCream": ((0.82, 0.78, 0.70), 0.85),
       "BA_WhitePaint": ((0.88, 0.88, 0.86), 0.4), "BA_Wicker": ((0.62, 0.48, 0.28), 0.8),
       "BA_PropAftershave": ((0.05, 0.08, 0.06), 0.2), "BA_PropMint": ((0.62, 0.85, 0.72), 0.3), "BA_PropSteel": ((0.6, 0.6, 0.62), 0.3),
       "BA_PropWhite": ((0.9, 0.9, 0.88), 0.4), "BA_PropRed": ((0.75, 0.06, 0.08), 0.5), "BA_PropBlack": ((0.03, 0.03, 0.03), 0.4),
       "BA_PropAmber": ((0.55, 0.32, 0.08), 0.15), "BA_PropGold": ((0.80, 0.62, 0.28), 0.3), "BA_PropAqua": ((0.20, 0.55, 0.40), 0.4),
       "BA_PropCrystal": ((0.85, 0.88, 0.90), 0.05), "BA_PropCotton": ((0.95, 0.80, 0.88), 0.9), "BA_PropJade": ((0.45, 0.68, 0.52), 0.2),
       "BA_PropWheat": ((0.80, 0.66, 0.35), 0.8)}
MATS = {k: material(k, *v) for k, v in COL.items()}
SOFT = {"BA_Lace", "BA_ShowerCurtain", "BA_CurtainCream"}


def export(group, name, out):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    mats = {k: material(k, *v) for k, v in COL.items()}
    coll = bpy.context.scene.collection
    root = bpy.data.objects.new(name, None); coll.objects.link(root)
    for p in group.values():
        if not p.f:
            continue
        ob = p.build(coll, mats); ob.parent = root
        if p.name in ("BA_Ivory", "BA_Marble", "BA_MarbleDark", "BA_Gilt", "BA_Subway", "BA_TileBlack", "BA_WhitePaint", "BA_Wicker", "BA_BlackMarble"):
            bv = ob.modifiers.new("bevel", "BEVEL"); bv.width = 0.002; bv.segments = 2; bv.limit_method = "ANGLE"; bv.angle_limit = math.radians(30)
        if p in SMOOTH or p.name in SOFT or p.name in ("BA_Tub", "BA_HallTub", "BA_Basin", "BA_Basin2", "BA_Globe", "BA_Seat") or p.name.startswith("BA_Towel"):
            for poly in ob.data.polygons:
                poly.use_smooth = True
    out.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=str(out), export_format="GLB", export_yup=True, export_apply=True)
    print("wrote", out, {p.name: len(p.f) for p in group.values()})


export(parts, "Bathrooms_HiFi", OUT)
export(props, "BathroomProps_HiFi", OUTP)
