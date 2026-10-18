"""hifi_basement: the basement's look, generated to measurement (Oct 18 2026, TRIAL; changes/2026-10-18-basement-shell.json, DEVIATIONS 91).

Every position comes from spec/house_spec.ground.json basement / basement_areaway (tools/house/reconcile.py basement_spec, from
measurements/rooms/basement.json): floor joists under the ground plate (cut round the stair and the chute, stopped at the chimney),
the open wooden stair (treads on two stringers, a raking handrail and balusters on the open side: film 2414/2490/10300), the
film's green furnace (2466/2482/6800: riveted hood, 14-bar grate with the fire behind it, gauges on top, two silver ducts rising in a
V, a flue to the chimney), the laundry corner (2430: deep sink, washer, dryer, shelves), bare bulbs on cords (the pull-cord light,
10114-10126), the laundry chute's foot in the ceiling (10127-10150), small high windows (2394/2466) and the half-glazed areaway door
with a red gingham curtain, standing open (9952-10104). The walls, floor, landing, posts, chimney and the areaway's stone are the
grey-box boxes, textured in SpecGreybox.Basement. y is above the GROUND floor; faces via Part.face (zfight-check).

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P tools/house/hifi_basement.py
  -> unity/HomeAlone/Assets/Models/Foyer/Basement.glb (SpecGreybox.Basement places it)
"""
import json
import math
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/house"))
from hifi_lib import Part, material   # noqa: E402

OUT = ROOT / "unity/HomeAlone/Assets/Models/Foyer/Basement.glb"
GS = json.loads((ROOT / "spec/house_spec.ground.json").read_text())
ST = GS["basement"]; B = ST["basement"]; AW = GS["basement_areaway"]
FY, PL, JD = B["floor_y"], B["plate_y"], B["joist_d"]
JB = PL - JD                                            # joist bottoms
(FX0, FX1), (FZ0, FZ1), G, R = B["flight"]["x"], B["flight"]["z"], B["flight"]["going"], B["flight"]["rise"]
YL = B["landing_y"]
HX0, HX1 = B["hole"]["x"]

joist, tread, rail = Part("Joists", "BS_Joist"), Part("Stair", "BS_Tread"), Part("Handrail", "BS_Rail")
green, iron, glow, duct, brass = Part("Furnace", "BS_Furnace"), Part("FurnaceIron", "BS_Iron"), Part("FurnaceFire", "BS_Glow"), Part("Ducts", "BS_Duct"), Part("Gauges", "BS_Brass")
enamel, chrome, shelf, sinkp = Part("Appliances", "BS_Enamel"), Part("Knobs", "BS_Chrome"), Part("Shelves", "BS_Shelf"), Part("Sink", "BS_Sink")
bulb, cord, metal, dark = Part("Bulbs", "BS_Bulb"), Part("Cords", "BS_Cord"), Part("Chute", "BS_Metal"), Part("ChuteDark", "BS_Dark")
door, glass, ging = Part("AreawayDoor", "BS_DoorPaint"), Part("AreawayGlass", "BS_Glass"), Part("Gingham", "BS_Gingham")
wframe, wglass = Part("WindowFrames", "BS_DoorPaint"), Part("WindowGlass", "BS_Daylight")


def box(part, x0, x1, y0, y1, z0, z1):
    part.box(min(x0, x1), max(x0, x1), min(y0, y1), max(y0, y1), min(z0, z1), max(z0, z1))


def add(a, b): return tuple(p + q for p, q in zip(a, b))
def sub(a, b): return tuple(p - q for p, q in zip(a, b))
def cen(ps): return tuple(sum(p[i] for p in ps) / len(ps) for i in range(3))


def prism(part, pts, e):
    """a convex planar polygon extruded by e, faces outward"""
    top = [add(p, e) for p in pts]; c = cen(pts + top)
    part.face(list(pts), sub(cen(pts), c)); part.face(top, sub(cen(top), c))
    for i in range(len(pts)):
        q = [pts[i], pts[(i + 1) % len(pts)], top[(i + 1) % len(pts)], top[i]]
        part.face(q, sub(cen(q), c))


def cyl_y(part, x, z, y0, y1, r, n=12):
    part.lathe(x, z, y0, [(0.0, r), (y1 - y0, r)], n)


# ---------------------------------------------------------------- joists (2x10 at 16 in, along x), headers and trimmers at the cuts
FP = B["footprint"]
def x_span(z):   # the footprint's x extent at z (the bands of reconcile's rectangles)
    for z0, z1, x0 in ((-0.915, 4.085, -5.192), (4.085, 7.778, -1.505), (7.778, 11.43, 0.008), (11.43, 16.07, 1.58)):
        if z0 <= z < z1:
            return x0, 10.13
    return None
CH, CU = B["chimney"], B["chute"]
z = -0.915 + 0.406
while z + 0.025 < 16.07:
    sp = x_span(z - 0.025) if x_span(z - 0.025) == x_span(z + 0.025) else None
    if sp:
        x0, x1 = sp
        cuts = []
        if FZ0 - 0.03 < z < FZ1 + 0.03: cuts.append((HX0, HX1 + 0.05))                    # the stair opening and its trimmer
        elif 6.357 - 0.03 < z < FZ0: cuts.append((HX0, -0.62))                             # the pocket behind the door
        if CH["z"][0] - 0.03 < z < CH["z"][1] + 0.03: cuts.append((x0, CH["x"][1]))         # the chimney base
        segs, a_ = [], x0
        for c0, c1 in sorted(cuts):
            if c0 > a_: segs.append((a_, c0))
            a_ = max(a_, c1)
        if a_ < x1: segs.append((a_, x1))
        for a_, b_ in segs:
            if b_ - a_ > 0.05: box(joist, a_, b_, JB, PL, z - 0.025, z + 0.025)
    z += 0.406
box(joist, HX0, -0.62, JB, PL, 6.307, 6.357)                                                  # header: the pocket's kitchen edge
box(joist, -0.62, HX1 + 0.05, JB, PL, FZ0 - 0.05, FZ0)                                        # header: the opening's kitchen edge
box(joist, HX1, HX1 + 0.05, JB, PL, FZ0, FZ1)                                                 # trimmer at the opening's end

# ---------------------------------------------------------------- the open stair: treads on two stringers, raking handrail, balusters
SW = 0.04                                                                                     # stringer thickness
n_tr = round((FX1 - FX0) / G)
def nose(x): return FY + R + (FX1 - x) / G * R                                                # the nosing line (rising toward -x)
XB_ = FX1 + 0.02
def st_top(x): return FY + R + 0.06 + (XB_ - x) / (XB_ - FX0) * (YL - FY - R)                 # the stringers' top edge
for k in range(1, n_tr + 1):
    xa = FX0 + (n_tr - k) * G; top = FY + k * R
    box(tread, xa, xa + G + 0.02, top - 0.035, top, FZ0 + SW, FZ1 - SW)                       # 2 cm nosing on the low side
for za, xb in ((FZ0, FX1 - 0.09), (FZ1 - SW, XB_)):                                           # the south one stops at the newel
    yb_ = FY + (XB_ - xb) / G * R if xb < XB_ else FY
    prism(tread, [(xb, yb_, za), (xb, st_top(xb), za), (FX0, YL + 0.06, za), (FX0, YL - 0.25, za)], (0, 0, SW))
RH, RZ = 0.86, FZ0 + 0.02                                                                     # rail height over the nosings; rail centre z
x_top = FX1 - (JB - 0.04 - RH - FY - R) / R * G                                               # the rail stops under the opening's header
rail.sweep([(FX1 - 0.07, nose(FX1 - 0.07) + RH, RZ), (x_top, nose(x_top) + RH, RZ)], [(-0.025, -0.03), (0.025, -0.03), (0.025, 0.03), (-0.025, 0.03)])
box(rail, FX1 - 0.09, FX1, FY, FY + R + 1.00, FZ0 - 0.03, FZ0 + 0.04)                         # bottom newel
x = FX1 - 0.18
while x > x_top + 0.05:
    box(rail, x - 0.015, x + 0.015, st_top(x) - 0.01, nose(x) + RH - 0.03, FZ0 + 0.005, FZ0 + 0.035)
    x -= 0.12

# ---------------------------------------------------------------- the furnace (film 2466: body w:h 1.29, grate 360 of 585 px, front -z)
F = B["furnace"]; (fx0, fx1), (fz0, fz1), fh = F["x"], F["z"], F["body_h"]
fxc, W = (fx0 + fx1) / 2, fx1 - fx0
box(iron, fx0 + 0.05, fx1 - 0.05, FY, FY + 0.12, fz0 + 0.05, fz1 - 0.05)                     # plinth
box(green, fx0, fx1, FY + 0.12, FY + fh - 0.12, fz0 + 0.06, fz1)                              # casing
hood = [(fx0, FY + fh - 0.12, fz0 + 0.06), (fx1, FY + fh - 0.12, fz0 + 0.06), (fx1 - 0.08, FY + fh, fz0 + 0.14), (fx0 + 0.08, FY + fh, fz0 + 0.14)]
prism(green, hood, (0, 0, fz1 - fz0 - 0.20))                                                  # the rounded hood (chamfered)
gw, gx0 = W * 360 / 585, fxc - W * 360 / 585 / 2
gy0, gy1 = FY + 0.24, FY + 0.24 + (fh - 0.12) * 0.48
box(green, gx0 - 0.07, gx0 + gw + 0.07, gy0 - 0.06, gy1 + 0.10, fz0, fz0 + 0.06)            # the grate's frame (proud of the casing)
box(glow, gx0, gx0 + gw, gy0, gy1, fz0 + 0.04, fz0 + 0.05)                                    # the fire behind the bars (emissive)
for i in range(14):
    bx = gx0 + (i + 0.5) * gw / 14
    box(iron, bx - 0.012, bx + 0.012, gy0, gy1, fz0 - 0.012, fz0 + 0.03)
box(iron, gx0 - 0.02, gx0 + gw + 0.02, gy1 + 0.02, gy1 + 0.06, fz0 - 0.02, fz0 + 0.01)       # riveted top rail of the grate
for i in range(16):                                                                          # rivets along the hood's front edge
    rx = fx0 + 0.08 + i * (W - 0.16) / 15
    box(iron, rx - 0.01, rx + 0.01, FY + fh - 0.16, FY + fh - 0.14, fz0 + 0.05, fz0 + 0.07)
for sx in (fx0 - 0.03, fx1):                                                                 # the side "arms": curved iron legs (2482)
    box(iron, sx, sx + 0.03, FY, FY + fh - 0.25, fz0 + 0.10, fz0 + 0.20)
for gxp in (fxc - 0.25, fxc + 0.18):                                                          # gauges on top
    cyl_y(brass, gxp, fz0 + 0.40, FY + fh, FY + fh + 0.18, 0.025, 8)
    box(brass, gxp - 0.07, gxp + 0.07, FY + fh + 0.18, FY + fh + 0.32, fz0 + 0.38, fz0 + 0.42)
cyl_y(iron, fxc, (fz0 + fz1) / 2 + 0.15, FY + fh, FY + fh + 0.30, 0.12, 12)                   # the bonnet's collar
for side in (-1, 1):                                                                         # two silver ducts in a V up to the joists
    a = (fxc + side * 0.25, FY + fh + 0.25, (fz0 + fz1) / 2)
    b = (fxc + side * 1.0, JB - 0.13, (fz0 + fz1) / 2 - 0.6)
    oct_ = [(0.12 * math.cos(2 * math.pi * k / 10), 0.12 * math.sin(2 * math.pi * k / 10)) for k in range(10)]
    duct.sweep([a, b, (b[0], JB - 0.13, b[2] - 1.0)], oct_)
duct.sweep([(fx0 + 0.15, FY + fh - 0.05, fz1 - 0.15), (CH["x"][1] - 0.08, FY + fh + 0.35, CH["z"][0] + 0.25)],
           [(0.09 * math.cos(2 * math.pi * k / 10), 0.09 * math.sin(2 * math.pi * k / 10)) for k in range(10)])   # flue into the chimney

# ---------------------------------------------------------------- laundry (film 2430): sink, washer, dryer, shelves; 27 in appliances
L = B["laundry"]; wz, dp = L["wall_z"], L["depth"]
zf = wz - dp                                                                                  # their fronts
for nm in ("washer", "dryer"):
    x0, x1 = L[nm + "_x"]
    box(enamel, x0, x1, FY, FY + L["deck_h"], zf, wz - 0.01)
    box(enamel, x0, x1, FY + L["deck_h"], FY + 1.10, wz - 0.16, wz - 0.01)                          # back console
    for i in range(3 if nm == "washer" else 2):
        box(chrome, x0 + 0.10 + i * 0.2, x0 + 0.15 + i * 0.2, FY + 1.00, FY + 1.05, wz - 0.175, wz - 0.16)
    if nm == "dryer":
        box(chrome, x0 + 0.10, x1 - 0.10, FY + 0.70, FY + 0.74, zf - 0.02, zf)                 # door handle
    else:
        box(chrome, x0 + 0.08, x1 - 0.08, FY + L["deck_h"] - 0.005, FY + L["deck_h"] + 0.005, zf + 0.06, wz - 0.20)        # lid seam
sx0, sx1 = L["sink_x"]; th = L["sink_h"]
for lx in (sx0 + 0.03, sx1 - 0.06):                                                          # the film's dark double tub on legs
    for lz in (zf + 0.15, wz - 0.12):
        box(sinkp, lx, lx + 0.03, FY, FY + th - 0.32, lz, lz + 0.03)
box(sinkp, sx0, sx1, FY + th - 0.32, FY + th - 0.28, zf + 0.05, wz - 0.03)
xm_ = (sx0 + sx1) / 2
for (a_, b_, c_, d_) in ((sx0, sx0 + 0.04, zf + 0.05, wz - 0.03), (sx1 - 0.04, sx1, zf + 0.05, wz - 0.03), (xm_ - 0.02, xm_ + 0.02, zf + 0.09, wz - 0.07),
                         (sx0, sx1, zf + 0.05, zf + 0.09), (sx0, sx1, wz - 0.07, wz - 0.03)):
    box(sinkp, a_, b_, FY + th - 0.28, FY + th, c_, d_)
box(chrome, xm_ - 0.02, xm_ + 0.02, FY + th, FY + th + 0.22, wz - 0.06, wz - 0.03)            # tap riser
sy = FY + L["shelf_h"]                                                                        # the shelf over the tub (film 2430: cleaners)
box(shelf, sx0 + 0.15, sx1 - 0.08, sy, sy + 0.025, wz - 0.28, wz - 0.01)
for bxx in (sx0 + 0.17, sx1 - 0.12):
    box(shelf, bxx, bxx + 0.02, sy - 0.18, sy, wz - 0.03, wz - 0.01)

# ---------------------------------------------------------------- bulbs on cords (the pull-cord light), the chute's foot
LT = B["light"]
for i, (bx_, bz_) in enumerate([(LT["x"], LT["z"])] + [tuple(q) for q in LT["more"]]):
    yb = LT["bulb_y"] if i == 0 else LT["bulb_y"] + 0.15
    box(cord, bx_ - 0.004, bx_ + 0.004, yb + 0.10, JB, bz_ - 0.004, bz_ + 0.004)
    cyl_y(cord, bx_, bz_, yb + 0.05, yb + 0.10, 0.02, 8)                                     # socket
    bulb.lathe(bx_, bz_, yb - 0.06, [(0.0, 0.012), (0.03, 0.03), (0.07, 0.03), (0.11, 0.015)], 10)
    if i == 0:
        box(cord, bx_ + 0.03, bx_ + 0.034, yb - 0.55, yb + 0.07, bz_ - 0.002, bz_ + 0.002)    # the pull string
        box(cord, bx_ + 0.022, bx_ + 0.042, yb - 0.60, yb - 0.55, bz_ - 0.01, bz_ + 0.01)
(cx0, cx1), (cz0, cz1) = CU["x"], CU["z"]
for (a, b, c, d) in ((cx0, cx1, cz0, cz0 + 0.01), (cx0, cx1, cz1 - 0.01, cz1), (cx0, cx0 + 0.01, cz0, cz1), (cx1 - 0.01, cx1, cz0, cz1)):
    box(metal, a, b, JB - 0.03, PL, c, d)                                                    # sheet-metal liner through the joist bay
box(dark, cx0 + 0.01, cx1 - 0.01, PL - 0.012, PL - 0.011, cz0 + 0.01, cz1 - 0.01)             # the shaft's dark throat
for (a, b, c, d) in ((cx0 - 0.04, cx1 + 0.04, cz0 - 0.04, cz0), (cx0 - 0.04, cx1 + 0.04, cz1, cz1 + 0.04), (cx0 - 0.04, cx0, cz0, cz1), (cx1, cx1 + 0.04, cz0, cz1)):
    box(metal, a, b, JB - 0.045, JB - 0.03, c, d)                                            # its flange under the joists

# ---------------------------------------------------------------- small high windows (look only), 0.80 x 0.40 under the joists
for w in B["windows"]:
    y0, y1 = (FY + w["sill_over_floor"] if "sill_over_floor" in w else JB - 0.48), JB - 0.06
    if w["wall"] == "z":                                                                     # a wall at z = at; the room on the other side of 0
        sd = 1 if w["at"] < 2 else -1                                                        # face toward the room
        zfc = w["at"] + sd * 0.0
        (a, b) = w["x"]
        for (p0, p1, q0, q1) in ((a - 0.05, b + 0.05, y0 - 0.05, y0), (a - 0.05, b + 0.05, y1, y1 + 0.05), (a - 0.05, a, y0, y1), (b, b + 0.05, y0, y1), ((a + b) / 2 - 0.015, (a + b) / 2 + 0.015, y0, y1)):
            box(wframe, p0, p1, q0, q1, zfc, zfc + sd * 0.04)
        box(wglass, a, b, y0, y1, zfc + sd * 0.012, zfc + sd * 0.018)
    else:
        sd = 1 if w["at"] < 5 else -1
        xfc = w["at"]
        (a, b) = w["z"]
        for (p0, p1, q0, q1) in ((a - 0.05, b + 0.05, y0 - 0.05, y0), (a - 0.05, b + 0.05, y1, y1 + 0.05), (a - 0.05, a, y0, y1), (b, b + 0.05, y0, y1), ((a + b) / 2 - 0.015, (a + b) / 2 + 0.015, y0, y1)):
            box(wframe, xfc, xfc + sd * 0.04, q0, q1, p0, p1)
        box(wglass, xfc + sd * 0.012, xfc + sd * 0.018, y0, y1, a, b)

# ---------------------------------------------------------------- the areaway door: frame, half-glazed leaf open 90 deg into the basement
D = B["door"]; (dz0, dz1), dh = D["z"], D["h"]
xw = -5.192                                                                                   # the wall's inside face
for (a, b, c, d) in ((dz0 - 0.07, dz0, FY, FY + dh + 0.07), (dz1, dz1 + 0.07, FY, FY + dh + 0.07), (dz0, dz1, FY + dh, FY + dh + 0.07)):
    box(door, xw, xw + 0.02, c, d, a, b)                                                       # casing on the inside face
lw = dz1 - dz0; lx0, lx1, lz0, lz1 = xw + 0.025, xw + 0.025 + lw, dz1 + 0.003, dz1 + 0.048       # the leaf lies along +x (open)
yb, yt = FY + 0.01, FY + dh - 0.01
st = 0.10
box(door, lx0, lx1, yb, yb + 0.95, lz0, lz1)                                                  # lower panel half
box(door, lx0, lx0 + st, yb + 0.95, yt, lz0, lz1); box(door, lx1 - st, lx1, yb + 0.95, yt, lz0, lz1)
box(door, lx0 + st, lx1 - st, yt - st, yt, lz0, lz1)
gx0_, gx1_, gy1_ = lx0 + st, lx1 - st, yt - st
gy0_ = gy1_ - 0.55
box(door, lx0 + st, lx1 - st, yb + 0.95, gy0_, lz0, lz1)                                     # the rail under the lites
for i in (1, 2):                                                                              # muntins: 3 x 2 lites (film 9930/9952)
    xm = gx0_ + i * (gx1_ - gx0_) / 3; box(door, xm - 0.012, xm + 0.012, gy0_, gy1_, lz0 + 0.008, lz1 - 0.008)
ym = (gy0_ + gy1_) / 2; box(door, gx0_, gx1_, ym - 0.012, ym + 0.012, lz0 + 0.008, lz1 - 0.008)
box(glass, gx0_, gx1_, gy0_, gy1_, (lz0 + lz1) / 2 - 0.003, (lz0 + lz1) / 2 + 0.003)
box(ging, gx0_ - 0.01, gx1_ + 0.01, gy0_ - 0.02, gy1_ + 0.02, lz1 + 0.012, lz1 + 0.020)             # the gingham curtain on the room side
box(chrome, lx1 - 0.09, lx1 - 0.06, FY + 0.92, FY + 0.96, lz1, lz1 + 0.05)                     # knob

# ---------------------------------------------------------------- the areaway's iron handrails (film 9900/9924/9930), one down each wall
Q = B["areaway"]; (qx0, qx1), (qz0, qz1), qg, qr = Q["x"], Q["z"], Q["going"], Q["rise"]
xl_ = Q["landing_x"]
def anose(x): return FY + qr + (xl_ - x) / qg * qr                                            # rising toward -x from the landing's edge
pipe = [(0.02 * math.cos(2 * math.pi * k / 8), 0.02 * math.sin(2 * math.pi * k / 8)) for k in range(8)]
for zr in (qz0 + 0.07, qz1 - 0.07):
    xa_, xb_ = qx0 + 0.15, xl_ - 0.05
    rail_iron = iron
    rail_iron.sweep([(xb_, anose(xb_) + 0.86, zr), (xa_, anose(xa_) + 0.86, zr)], pipe)
    x_ = xb_ - 0.10
    while x_ > xa_:
        k = math.ceil((xl_ - x_) / qg); top = FY + k * qr
        box(iron, x_ - 0.012, x_ + 0.012, top, anose(x_) + 0.86 - 0.015, zr - 0.012, zr + 0.012)
        x_ -= 1.2

# ---------------------------------------------------------------- the iron picket railing round the areaway at grade (film 9960-9976)
GYa = Q["grade_y"]; STt = Q["stone_t"]
for zc in (qz0 - STt / 2, qz1 + STt / 2):
    for yy in (GYa + 1.02,):
        box(iron, qx0, -5.492 - 0.01, yy, yy + 0.025, zc - 0.012, zc + 0.012)               # bottom and top rails
    x_ = qx0 + 0.02
    while x_ < -5.52:
        box(iron, x_ - 0.008, x_ + 0.008, GYa + 0.15, GYa + 1.02, zc - 0.008, zc + 0.008)   # pickets on the coping
        x_ += 0.12
    for xp in (qx0, -5.492 - 0.05):
        box(iron, xp, xp + 0.04, GYa + 0.15, GYa + 1.10, zc - 0.02, zc + 0.02)              # end posts

# ---------------------------------------------------------------- dressing round (Oct 18; spec/dressing/basement.json): hanging bikes, shelving with jars
# and cans, the lamp by the outside stairwell door
DB = json.loads((ROOT / "spec/dressing/basement.json").read_text())
bframe, btire, bsteel, bseat = Part("BikeFrame", "BS_BikeRed"), Part("BikeTires", "BS_Iron"), Part("BikeSteel", "BS_Chrome"), Part("BikeSeat", "BS_Sink")


def torus(part, c, u, v, R, r, n=32, m=8):
    w = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
    P_ = lambda a, b: tuple(c[k] + (R + r * math.cos(b)) * (math.cos(a) * u[k] + math.sin(a) * v[k]) + r * math.sin(b) * w[k] for k in range(3))
    for i in range(n):
        for j in range(m):
            a0, a1, b0, b1 = 2 * math.pi * i / n, 2 * math.pi * (i + 1) / n, 2 * math.pi * j / m, 2 * math.pi * (j + 1) / m
            q = [P_(a0, b0), P_(a1, b0), P_(a1, b1), P_(a0, b1)]
            am, bm = (a0 + a1) / 2, (b0 + b1) / 2
            nrm = tuple(math.cos(bm) * (math.cos(am) * u[k] + math.sin(am) * v[k]) + math.sin(bm) * w[k] for k in range(3))
            part.face(q, nrm)


rod = lambda r, k=8: [(r * math.cos(t), r * math.sin(t)) for t in [2 * math.pi * i / k for i in range(k)]]
for bk in DB["bikes"]:
    bx_, bz_ = bk["x"], bk["z"]; top = JB - 0.03
    Pt = lambda x, y, dz=0.0: (bx_ + x, top - y, bz_ + dz)            # bike-local (upright: x along, y up from the ground), hung upside down
    for ax in (0.0, 1.05):
        torus(btire, Pt(ax, 0.33), (1, 0, 0), (0, 1, 0), 0.31, 0.022)
        torus(bsteel, Pt(ax, 0.33), (1, 0, 0), (0, 1, 0), 0.285, 0.008, n=32, m=6)
        for k in range(12):                                              # spokes
            a = 2 * math.pi * k / 12
            bsteel.sweep([Pt(ax, 0.33, 0.02 * (1 if k % 2 else -1)), Pt(ax + 0.28 * math.cos(a), 0.33 + 0.28 * math.sin(a))], rod(0.0015, 4))
        iron.sweep([(bx_ + ax, JB, bz_), (bx_ + ax, top + 0.01, bz_)], rod(0.005))      # the hook from the joist to the rim
    BB, SC, HT, HB, RA, FA = Pt(0.42, 0.30), Pt(0.30, 0.82), Pt(0.93, 0.86), Pt(0.97, 0.70), Pt(0.0, 0.33), Pt(1.05, 0.33)
    for a_, b_ in ((BB, SC), (SC, HT), (BB, HB), (HB, HT)):
        bframe.sweep([a_, b_], rod(0.016))
    for dz_ in (-0.06, 0.06):                                            # stays and fork blades splay out before they reach the tyre's radius
        for a_, (mx_, my_), (bx2, by2) in ((Pt(0.42, 0.30), (0.34, 0.31), (0.0, 0.33)), (Pt(0.30, 0.82), (0.24, 0.62), (0.0, 0.33)),
                                          (Pt(0.97, 0.70), (0.99, 0.665), (1.05, 0.33))):
            bframe.sweep([(a_[0], a_[1], a_[2] + dz_ * 0.2), Pt(mx_, my_, dz_), Pt(bx2, by2, dz_)], rod(0.011))
    for ax in (0.0, 1.05):
        bframe.sweep([Pt(ax, 0.33, -0.065), Pt(ax, 0.33, 0.065)], rod(0.008))    # axles
    bframe.sweep([Pt(0.30, 0.82), Pt(0.27, 0.93)], rod(0.012))                         # seat post
    bseat.box(bx_ + 0.17, bx_ + 0.37, top - 0.99, top - 0.93, bz_ - 0.07, bz_ + 0.07)     # saddle
    bframe.sweep([Pt(0.93, 0.86), Pt(0.91, 1.0)], rod(0.012))                          # stem
    bsteel.sweep([Pt(0.91, 1.0, -0.28), Pt(0.91, 1.0, 0.28)], rod(0.011))               # handlebar
    for dz_ in (-0.28, 0.28):
        bseat.sweep([Pt(0.91, 1.0, dz_), Pt(0.91, 1.0, dz_ + (0.09 if dz_ > 0 else -0.09))], rod(0.016))   # grips
    bframe.sweep([Pt(0.42, 0.30, -0.06), Pt(0.42, 0.30, 0.06)], rod(0.03, 10))          # crank hub

SH = DB["shelving"]; (sx0_, sx1_), (sz0_, sz1_) = SH["x"], SH["z"]
wood = Part("Shelving", "BS_Shelf")
for zz in (sz0_, sz1_ - 0.03):
    for xx in (sx0_, sx1_ - 0.03):
        box(wood, xx, xx + 0.03, FY, FY + SH["boards"][-1] + 0.04, zz, zz + 0.03)
for by in SH["boards"]:
    box(wood, sx0_ + 0.005, sx1_ - 0.005, FY + by, FY + by + 0.02, sz0_ + 0.03, sz1_ - 0.03)
import random
rnd = random.Random(11)
jar = Part("Jars", "BS_JarGlass")
fills = {c: Part("JarFill" + c, "BS_Fill" + c) for c in ("Red", "Amber", "Green")}
lid = Part("JarLids", "BS_Brass")
can = Part("Cans", "BS_Metal"); label = {c: Part("CanLabel" + c, "BS_Label" + c) for c in ("White", "Blue", "Red")}
xc_ = (sx0_ + sx1_) / 2


def paint_can(x, z, y0, lab, r=0.085, h=0.19):
    """a gallon can: tin band, paper label, tin band and rim stacked (no overlapping faces)"""
    can.lathe(x, z, y0, [(0, r), (0.03, r)], 18)
    lab.lathe(x, z, y0 + 0.03, [(0, r), (0.13, r)], 18)
    can.lathe(x, z, y0 + 0.16, [(0, r), (h - 0.16, r), (h - 0.155, r * 0.9)], 18)


for bi, by in enumerate(SH["boards"][1:4]):
    z = sz0_ + 0.10
    y0 = FY + by + 0.02
    while z < sz1_ - 0.12:
        if bi < 2:                                                       # jars (home canning: tomatoes, peaches, pickles)
            r, h = rnd.choice([(0.04, 0.15), (0.045, 0.17), (0.035, 0.12)])
            list(fills.values())[rnd.randrange(3)].lathe(xc_, z, y0, [(0, r - 0.004), (0.004, r), (h * 0.72, r)], 14)   # the contents seen through the glass
            jar.lathe(xc_, z, y0 + h * 0.72, [(0, r), (h * 0.08, r), (h * 0.18, r * 0.8), (h * 0.20, r * 0.8)], 14)       # the empty glass shoulder
            lid.lathe(xc_, z, y0 + h * 0.92, [(0, r * 0.82), (0.02, r * 0.82), (0.022, 0.001)], 14)
            z += 2 * r + 0.03
        else:                                                            # paint cans
            r, h = 0.085, 0.19
            paint_can(xc_, z, y0, list(label.values())[rnd.randrange(3)])
            z += 2 * r + 0.04

for (cx, cz) in DB["floor_cans"]:                                      # film 2466/2490: paint cans on the floor along the wall
    paint_can(cx, cz, FY, list(label.values())[rnd.randrange(3)])

DL = DB["door_lamp"]; lx_, ly_, lz_ = DL["at"]                          # the bare-bulb lamp beside the outside stairwell door (film 9936)
box(wood, -5.192, -5.192 + 0.025, ly_ - 0.06, ly_ + 0.06, lz_ - 0.06, lz_ + 0.06)       # its wooden block on the wall
lampp = Part("DoorLampHolder", "BS_Enamel")
lampp.sweep([(-5.192 + 0.025, ly_, lz_), (lx_ + 0.07, ly_, lz_)], rod(0.03, 14))
bulb.sweep([(lx_ + 0.07, ly_, lz_), (lx_ + 0.15, ly_, lz_)], rod(0.03, 14))
DRESS = [bframe, btire, bsteel, bseat, wood, jar, lid, can, lampp] + list(fills.values()) + list(label.values())

# ---------------------------------------------------------------- export
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob)
coll = bpy.data.collections.new("Basement"); bpy.context.scene.collection.children.link(coll)
mats = {nm: material(nm, c, r, *e) for nm, c, r, *e in (
    ("BS_Joist", (0.42, 0.30, 0.18), 0.85), ("BS_Tread", (0.50, 0.36, 0.22), 0.7), ("BS_Rail", (0.30, 0.20, 0.12), 0.6),
    ("BS_Furnace", (0.12, 0.20, 0.15), 0.55), ("BS_Iron", (0.04, 0.04, 0.04), 0.6), ("BS_Duct", (0.62, 0.63, 0.64), 0.35),
    ("BS_Brass", (0.70, 0.55, 0.25), 0.4), ("BS_Enamel", (0.88, 0.88, 0.85), 0.35), ("BS_Chrome", (0.75, 0.75, 0.76), 0.25),
    ("BS_Shelf", (0.55, 0.42, 0.28), 0.8), ("BS_Sink", (0.09, 0.09, 0.09), 0.5), ("BS_Cord", (0.03, 0.03, 0.03), 0.7),
    ("BS_Metal", (0.55, 0.56, 0.57), 0.4), ("BS_Dark", (0.01, 0.01, 0.01), 0.9), ("BS_DoorPaint", (0.86, 0.85, 0.80), 0.5),
    ("BS_Glass", (0.8, 0.85, 0.9), 0.05), ("BS_Gingham", (0.70, 0.12, 0.10), 0.9),
    ("BS_Glow", (1.0, 0.45, 0.10), 0.9, (1.0, 0.45, 0.10), 6.0), ("BS_Bulb", (1.0, 0.9, 0.7), 0.3, (1.0, 0.85, 0.6), 20.0),
    ("BS_Daylight", (0.75, 0.80, 0.85), 0.2, (0.75, 0.80, 0.85), 1.5), ("BS_BikeRed", (0.55, 0.08, 0.06), 0.4),
    ("BS_JarGlass", (0.75, 0.80, 0.78), 0.1), ("BS_FillRed", (0.55, 0.10, 0.06), 0.4), ("BS_FillAmber", (0.80, 0.50, 0.12), 0.4),
    ("BS_FillGreen", (0.35, 0.45, 0.15), 0.4), ("BS_LabelWhite", (0.88, 0.87, 0.82), 0.6), ("BS_LabelBlue", (0.15, 0.25, 0.60), 0.6),
    ("BS_LabelRed", (0.65, 0.10, 0.08), 0.6))}
root = bpy.data.objects.new("Basement_HiFi", None); coll.objects.link(root)
for p in (joist, tread, rail, green, iron, glow, duct, brass, enamel, chrome, shelf, sinkp, bulb, cord, metal, dark, door, glass, ging, wframe, wglass, *DRESS):
    if p.f:
        p.build(coll, mats).parent = root
OUT.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(OUT), export_format="GLB", use_selection=False, export_apply=True)
print("hifi_basement: wrote", OUT)
