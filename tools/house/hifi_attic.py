"""hifi_attic: the attic shell, generated to measurement (Oct 18 2026, TRIAL; changes/2026-10-18-attic-shell.json, DEVIATIONS 90).

Every number comes from spec/house_spec.json attic_stair.attic (tools/house/reconcile.py, from measurements/rooms/attic.json):
Marina's room (p2 775-935 s) fitted over our upper floor: floor, vertical-board knee walls and end walls, exposed rafters with collar
ties and a ridge board, roof boards (shingle outside), the house's chimney (the living-room flue) with a wood stove, a log-style
balustrade round the stair well (open at its top, where the flight meets the end wall), the zipline dormer in the rear slope (film
9435, 10950, 11090: pedimented gable, a pair of 3-lite casements opening outward, cream curtains) and a placeholder sofa bed
(the film's fold-out, 1403-1447) where the user's poster puts the bed (IMG_4295: bed 26 at the far end beside the chimney). The casement leaves are their own objects (CasementL_*, CasementR_*): SpecGreybox.Attic hangs them on
hinges and opens them. Faces via Part.face (zfight-check); y is above the upper floor.

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P tools/house/hifi_attic.py
  -> unity/HomeAlone/Assets/Models/Foyer/Attic.glb (SpecGreybox.Attic places it)
"""
import json
import math
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/house"))
from hifi_lib import Part, material   # noqa: E402

OUT = ROOT / "unity/HomeAlone/Assets/Models/Foyer/Attic.glb"
ST = json.loads((ROOT / "spec/house_spec.json").read_text())["attic_stair"]
A = ST["attic"]
(ax0, ax1), (az0, az1) = A["x"], A["z"]
yf, ridge, kh, xc = A["floor_y"], A["ridge_y"], A["knee_h"], A["ridge_x"]
th = math.radians(A["pitch_deg"]); tp, sn, cs = math.tan(th), math.sin(th), math.cos(th)
(wx0, wx1), (wz0, wz1) = A["well"]["x"], A["well"]["z"]
D = A["dormer"]; dz, dface, di, (dw, dh), ys, yh, yc = D["z"], D["face_x"], D["inner_half"], D["opening"], D["sill_y"], D["head_y"], D["ceiling_y"]
T = A["wall_t"]
FB = 0.012            # floor boards over the grey-box floor (1.2 cm proud of the well's framing tops)
F = yf + FB           # finished floor
RB = 0.03             # roof boards
PB = 0.015            # wall boards
OVER = 0.15           # roof overhang at the ends (outside)
XE0, XE1 = ax0 - kh / tp, ax1 + kh / tp     # where the roof's underside meets the attic floor level (the eaves, outside)

def hr(x):  # rear slope underside
    return yf + kh + (x - ax0) * tp

def hf(x):  # front slope underside
    return yf + kh + (ax1 - x) * tp

NR, NF = (-sn, cs, 0.0), (sn, cs, 0.0)     # outward normals of the rear / front slopes

boards, roofout, rafter, floor = Part("Boards", "AT_Boards"), Part("Shingle", "AT_Shingle"), Part("Rafters", "AT_Rafter"), Part("Floor", "AT_Floor")
brick, iron, rail, paint = Part("Chimney", "AT_Brick"), Part("Stove", "AT_Iron"), Part("Balustrade", "AT_Rail"), Part("DormerTrim", "AT_Paint")
curtain, sofa, mattress = Part("Curtains", "AT_Curtain"), Part("SofaBed", "AT_Sofa"), Part("Mattress", "AT_Mattress")
crib, ltable, lglass, shade, bulb, porcelain = (Part("Crib", "AT_Wood"), Part("LampTable", "AT_Wood"), Part("LampBase", "AT_LampGlass"),
                                                Part("LampShade", "AT_Shade"), Part("Bulbs", "AT_Bulb"), Part("BulbFixtures", "AT_Porcelain"))
cribmat = Part("CribMattress", "AT_Mattress")
leaves = {s: (Part(f"Casement{s}_Frame", "AT_Paint"), Part(f"Casement{s}_Glass", "AT_Glass")) for s in "LR"}


def add(a, b): return tuple(p + q for p, q in zip(a, b))
def mul(a, k): return tuple(p * k for p in a)
def cen(ps): return tuple(sum(p[i] for p in ps) / len(ps) for i in range(3))
def sub(a, b): return tuple(p - q for p, q in zip(a, b))


def prism(part, pts, e, out=None):
    """A convex planar polygon extruded by vector e: every face oriented away from the solid's centre. 'out' takes the far cap."""
    top = [add(p, e) for p in pts]
    c = cen(pts + top)
    part.face(list(pts), sub(cen(pts), c))
    (out or part).face(top, sub(cen(top), c))
    n = len(pts)
    for i in range(n):
        q = [pts[i], pts[(i + 1) % n], top[(i + 1) % n], top[i]]
        part.face(q, sub(cen(q), c))


def box(part, x0, x1, y0, y1, z0, z1):
    part.box(min(x0, x1), max(x0, x1), min(y0, y1), max(y0, y1), min(z0, z1), max(z0, z1))


def slope(xa, xb, za, zb, rear=True, out=True):
    """roof boards between xa and xb (plan), za..zb: underside on the slope line, RB thick outward; shingle face outside"""
    h, n = (hr, NR) if rear else (hf, NF)
    pts = [(xa, h(xa), za), (xb, h(xb), za), (xb, h(xb), zb), (xa, h(xa), zb)]
    prism(boards, pts, mul(n, RB), roofout if out else None)


def lathe_y(part, x, z, y0, y1, r, n=10):
    part.lathe(x, z, y0, [(0.0, r), (y1 - y0, r)], n)


# ---------------------------------------------------------------- floor (around the well; the dormer alcove)
for x0_, x1_, z0_, z1_ in ((ax0, wx0, az0, az1), (wx1, ax1, az0, az1), (wx0, wx1, az0, wz0), (wx0, wx1, wz1, az1), (dface, ax0, dz - di, dz + di)):
    box(floor, x0_, x1_, yf, F, z0_, z1_)

# ---------------------------------------------------------------- knee walls (vertical boards), end walls (gables to the eaves)
box(boards, ax1 - PB, ax1, F, yf + kh, az0 + PB, az1 - PB)
box(boards, ax0, ax0 + PB, F, yf + kh, az0 + PB, dz - di - T)
box(boards, ax0, ax0 + PB, F, yf + kh, dz + di + T, az1 - PB)
box(boards, ax0, ax1, F, yf + kh, az1 - PB, az1)                 # the hip end's knee wall (poster: hipped)
prism(boards, [(XE0 + FB / tp, F, az0), (XE1 - FB / tp, F, az0), (xc, ridge, az0)], (0, 0, PB))   # the partition at the bed end

# ---------------------------------------------------------------- roof boards: rear slope round the chimney and the dormer, hip end
zh = az1 - (xc - ax0)                                   # where the hip lines meet the ridge
NE = (0.0, cs, sn)
def he(z):  # hip-end slope underside
    return yf + kh + (az1 - z) * tp
cz0, cz1 = A["chimney"]["z"]; cx1 = A["chimney"]["x"][1]
lz0, lz1 = A["chimney_living"]["z"]; lx0, lx1 = A["chimney_living"]["x"]   # the living-room flue's breast (Oct 18)
xd = ax0 + (yc - yf - kh) / tp                          # where the dormer's ceiling meets the rear slope
dza, dzb = dz - di - T, dz + di + T
za_ = az0 - OVER
for xa, za, zb in ((ax0, za_, cz0), (cx1, cz0, cz1), (ax0, cz1, dza), (xd, dza, dzb), (ax0, dzb, zh)):
    slope(xa, xc, za, zb, rear=True)
slope(xc, ax1, za_, zh, rear=False)
prism(boards, [(ax0, hr(ax0), zh), (xc, hr(xc), zh), (ax0, hr(ax0), az1)], mul(NR, RB), roofout)
prism(boards, [(xc, hf(xc), zh), (ax1, hf(ax1), zh), (ax1, hf(ax1), az1)], mul(NF, RB), roofout)
prism(boards, [(ax0, he(az1), az1), (ax1, he(az1), az1), (xc, he(zh), zh)], mul(NE, RB), roofout)
# outside the knee walls the roof runs on down to the eaves (the "short roof" under the dormer, film 10950/11162)
for xa, xb, za, zb in ((XE0, ax0, za_, dza), (XE0, ax0, dzb, az1), (XE0, dface - T, dza, dzb)):
    slope(xa, xb, za, zb, rear=True)
slope(ax1, XE1, za_, az1, rear=False)
box(rafter, xc - 0.02, xc + 0.02, ridge - 0.22, ridge - 0.02, az0 + PB, zh)   # ridge board

# ---------------------------------------------------------------- rafters (0.05 x 0.14 at 0.61 m), hip and jack rafters, collar ties
RW, RD = 0.05, 0.14
cy = A["collar_y"]
zs, z = [], az0 + PB + 0.03
while z + RW < az1 - PB - 0.06:
    zs.append(z); z += 0.61
def rafter_piece(xa, xb, z0_, rear):
    h, n = (hr, NR) if rear else (hf, NF)
    pts = [(xa, h(xa), z0_), (xb, h(xb), z0_), (xb, h(xb), z0_ + RW), (xa, h(xa), z0_ + RW)]
    prism(rafter, pts, mul(n, -RD))
for z0_ in zs:
    zm = z0_ + RW / 2
    xa = ax0 + PB + 0.002
    if dza - 0.02 < zm < dzb + 0.02:
        xa = xd + 0.01                                   # cut at the dormer (a header carries it)
    if cz0 - 0.03 < zm < cz1 + 0.03:
        xa = cx1 + 0.01
    if lz0 - 0.03 < zm < lz1 + 0.03:
        xa = lx1 + 0.01
    if z0_ + RW < zh - 0.03:                             # common rafters to the ridge
        rafter_piece(xa, xc - 0.02, z0_, True); rafter_piece(xc + 0.02, ax1 - PB - 0.002, z0_, False)
    elif z0_ > zh + 0.06:                                # jack rafters up to the hip lines
        reach = az1 - (z0_ + RW) - 0.04
        rafter_piece(xa, ax0 + reach, z0_, True); rafter_piece(ax1 - reach, ax1 - PB - 0.002, z0_, False)
headers = [(dza - 0.02, dzb + 0.02, xd), (cz0 - 0.03, cz1 + 0.03, cx1), (lz0 - 0.03, lz1 + 0.03, lx1)]
for z0_, z1_, x in headers:   # a doubled header across each cut, under the boards
    pts = [(x + 0.01, hr(x + 0.01), z0_), (x + 0.11, hr(x + 0.11), z0_), (x + 0.11, hr(x + 0.11), z1_), (x + 0.01, hr(x + 0.01), z1_)]
    prism(rafter, pts, mul(NR, -RD))
for xh in (ax0, ax1):                                    # the two hip rafters, under the hip lines
    rafter.sweep([(xh + (0.25 if xh == ax0 else -0.25), yf + kh + 0.25 * tp - 0.02, az1 - 0.25), (xc, ridge - 0.02, zh)],
                 [(-0.025, -0.14), (0.025, -0.14), (0.025, 0.0), (-0.025, 0.0)])
x = ax0 + 0.40
while x + RW < ax1 - 0.40:                               # jack rafters on the hip end
    if abs(x + RW / 2 - xc) > 0.06:
        reach = min(x - ax0, ax1 - x - RW) - 0.04
        pts = [(x, he(az1 - PB - 0.002), az1 - PB - 0.002), (x + RW, he(az1 - PB - 0.002), az1 - PB - 0.002), (x + RW, he(az1 - reach), az1 - reach), (x, he(az1 - reach), az1 - reach)]
        prism(rafter, pts, mul(NE, -RD))
    x += 0.61
# collar ties beside every other common rafter, and beside the one over the stair head (film 10922-10926: the zipline's rope loops over it)
common = [i for i, z0_ in enumerate(zs) if z0_ + RW < zh - 0.03]
head = min(common, key=lambda i: abs(zs[i] - (wz1 - 0.35)))
ties = sorted(set(common[::2]) | {head})
xt0, xt1 = ax0 + (cy + 0.07 - yf - kh) / tp, ax1 - (cy + 0.07 - yf - kh) / tp
for i in ties:
    zt = zs[i] + RW
    box(rafter, xt0 + 0.01, xt1 - 0.01, cy - 0.07, cy + 0.07, zt, zt + 0.05)

# ---------------------------------------------------------------- chimneys (the parents' flue through the rear slope; the living room's outside) and the stove
cx0 = ax0 + PB + 0.002
prism(brick, [(cx0, F, cz0), (cx1, F, cz0), (cx1, ridge + 0.9, cz0), (cx0, ridge + 0.9, cz0)], (0, 0, cz1 - cz0))
# the living-room flue's breast against the rear knee wall, up to 1 cm under the roof boards (it continues out of sight to the stack
# outside, ext_chimney): the stove's pipe goes into it (film 1410/1418)
prism(brick, [(lx0 + PB + 0.002, F, lz0), (lx1, F, lz0), (lx1, hr(lx1) - 0.01, lz0), (lx0 + PB + 0.002, hr(lx0 + PB + 0.002) - 0.01, lz0)], (0, 0, lz1 - lz0))
EC = A["ext_chimney"]
prism(brick, [(EC["x"][0], yf, EC["z"][0]), (EC["x"][1], yf, EC["z"][0]), (EC["x"][1], ridge + 0.9, EC["z"][0]), (EC["x"][0], ridge + 0.9, EC["z"][0])], (0, 0, EC["z"][1] - EC["z"][0]))
S_ = A["stove"]; (sx0, sx1), (sz0, sz1), sh = S_["x"], S_["z"], S_["h"]
box(iron, sx0, sx1, F + 0.12, F + sh, sz0, sz1)
for lx in (sx0 + 0.04, sx1 - 0.08):
    for lz in (sz0 + 0.04, sz1 - 0.08):
        box(iron, lx, lx + 0.04, F, F + 0.12, lz, lz + 0.04)
px, pz, py = (sx0 + sx1) / 2, (sz0 + sz1) / 2, F + 1.45
lathe_y(iron, px, pz, F + sh, py + 0.075, 0.075)
oct_ = [(0.075 * math.cos(2 * math.pi * k / 10), 0.075 * math.sin(2 * math.pi * k / 10)) for k in range(10)]
iron.sweep([(px, py, pz), (lx1, py, pz)], oct_)

# ---------------------------------------------------------------- balustrade round the well (log style)
R = A["rail"]; ro, rh = R["off"], R["h"]
xr, xf, zfoot, zend = wx0 - ro, wx1 + ro, wz0 - ro, wz1 - 0.05
zmid = (zfoot + zend) / 2
posts = [(xr, zfoot), (xf, zfoot), (xr, zend), (xf, zend), (xr, zmid), (xf, zmid)]
for x, z in posts:
    rail.lathe(x, z, F, [(0.0, 0.05), (rh + 0.06, 0.05), (rh + 0.06, 0.055), (rh + 0.10, 0.055), (rh + 0.12, 0.03)], 12)
runs = [((xr, zfoot), (xr, zmid)), ((xr, zmid), (xr, zend)), ((xr, zfoot), (xf, zfoot)), ((xf, zfoot), (xf, zmid)), ((xf, zmid), (xf, zend))]
for (xa, za), (xb, zb) in runs:
    L = math.hypot(xb - xa, zb - za); ux, uz = (xb - xa) / L, (zb - za) / L
    a, b = (xa + ux * 0.04, za + uz * 0.04), (xb - ux * 0.04, zb - uz * 0.04)   # ends inside the posts
    for y0, y1, w in ((F + rh - 0.07, F + rh, 0.035), (F + 0.08, F + 0.13, 0.025)):
        box(rail, min(a[0], b[0]) - (w if ux == 0 else 0), max(a[0], b[0]) + (w if ux == 0 else 0), y0, y1,
            min(a[1], b[1]) - (w if uz == 0 else 0), max(a[1], b[1]) + (w if uz == 0 else 0))
    n = max(1, int((L - 0.14) / 0.11))
    for k in range(1, n + 1):
        s = 0.07 + (L - 0.14) * k / (n + 1)
        rail.lathe(xa + ux * s, za + uz * s, F + 0.13, [(0.0, 0.018), (rh - 0.20, 0.018)], 8)

# ---------------------------------------------------------------- the dormer: alcove, window wall, casements, curtains, outside
yt = yc + 0.10                                           # the dormer's eaves (outside)
cw = D["cornice_w"]; dp = math.tan(math.radians(D["pitch_deg"]))
yr = yt + cw / 2 * dp
for zf, sgn in ((dz - di, -1), (dz + di, 1)):            # cheeks: full height in the alcove, down to the slope inside the knee line
    pts = [(dface - T, F, zf), (ax0, F, zf), (ax0, yf + kh, zf), (xd, yc, zf), (xd, yt, zf), (dface - T, yt, zf)]
    zb = zf + sgn * T
    # split into convex pieces: the alcove part and the triangle over the slope
    prism(boards, [(dface - T, F, zf), (ax0, F, zf), (ax0, yt, zf), (dface - T, yt, zf)], (0, 0, zb - zf))
    prism(boards, [(ax0, yf + kh, zf), (xd, yc, zf), (xd, yt, zf), (ax0, yt, zf)], (0, 0, zb - zf))
box(boards, dface, xd, yc, yc + 0.02, dz - di, dz + di)  # dormer ceiling
# window wall: apron, jambs, head (the opening between)
box(boards, dface - T, dface, F, ys, dz - di, dz + di)
box(boards, dface - T, dface, ys, yh, dz - di, dz - dw / 2)
box(boards, dface - T, dface, ys, yh, dz + dw / 2, dz + di)
box(boards, dface - T, dface, yh, yt, dz - di, dz + di)
box(paint, dface, dface + 0.05, ys, ys + 0.025, dz - dw / 2, dz + dw / 2)            # stool
# outside: casing, cornice, pediment, the dormer's roof meeting the main slope along its valleys
xo = dface - T
for z0_, z1_, y0, y1 in ((dz - dw / 2 - 0.08, dz - dw / 2, ys - 0.06, yh + 0.08), (dz + dw / 2, dz + dw / 2 + 0.08, ys - 0.06, yh + 0.08),
                         (dz - dw / 2, dz + dw / 2, yh, yh + 0.08), (dz - dw / 2, dz + dw / 2, ys - 0.06, ys)):
    box(paint, xo - 0.02, xo, y0, y1, z0_, z1_)
box(paint, xo - 0.10, xo, yt - 0.10, yt, dz - cw / 2, dz + cw / 2)                   # cornice
prism(paint, [(xo - 0.08, yt, dz - cw / 2), (xo - 0.08, yt, dz + cw / 2), (xo - 0.08, yr, dz)], (0.08, 0, 0))   # pediment
xv = lambda y: ax0 + (y - yf - kh - RB / cs) / tp       # the main roof's outer surface at height y
for sgn in (-1, 1):
    ze = dz + sgn * cw / 2
    pts = [(xo - 0.10, yt, ze), (xo - 0.10, yr, dz), (xv(yr), yr, dz), (xv(yt), yt, ze)]
    nrm = (0.0, math.cos(math.radians(D["pitch_deg"])), sgn * math.sin(math.radians(D["pitch_deg"])))
    prism(roofout, pts, mul(nrm, 0.03))
# the casement pair: each leaf 3 lites, hung at its outer jamb, opening outward (SpecGreybox.Attic turns them)
lw, lh, lt, st = (dw - 0.04) / 2, dh - 0.04, 0.04, 0.05
for s, za in (("L", dz - dw / 2 + 0.02), ("R", dz + 0.0)):
    fr, gl = leaves[s]
    zb = za + lw; yb, yt2 = ys + 0.02, ys + 0.02 + lh
    box(fr, xo, xo + lt, yb, yt2, za, za + st); box(fr, xo, xo + lt, yb, yt2, zb - st, zb)
    box(fr, xo, xo + lt, yb, yb + st, za + st, zb - st); box(fr, xo, xo + lt, yt2 - st, yt2, za + st, zb - st)
    lite = (lh - 2 * st - 2 * 0.025) / 3
    for k in (1, 2):
        y0 = yb + st + k * lite + (k - 1) * 0.025
        box(fr, xo + 0.005, xo + lt - 0.005, y0, y0 + 0.025, za + st, zb - st)
    box(gl, xo + 0.017, xo + 0.023, yb + st, yt2 - st, za + st, zb - st)
# curtains: a rod and two cream panels drawn to the sides, folded (film 10932-10938)
oct2 = [(0.012 * math.cos(2 * math.pi * k / 8), 0.012 * math.sin(2 * math.pi * k / 8)) for k in range(8)]
curtain.sweep([(dface + 0.08, yh + 0.07, dz - di + 0.01), (dface + 0.08, yh + 0.07, dz + di - 0.01)], oct2)
for sgn in (-1, 1):
    z_out, z_in = dz + sgn * (di - 0.015), dz + sgn * (dw / 2 - 0.09)
    zs_ = [z_out + (z_in - z_out) * k / 4 for k in range(5)]
    for k in range(4):
        x = dface + 0.065 + (0.02 if k % 2 else 0.0)
        box(curtain, x, x + 0.012, yf + 0.25, yh + 0.06, min(zs_[k], zs_[k + 1]), max(zs_[k], zs_[k + 1]))

# ---------------------------------------------------------------- the sofa bed (placeholder in the film's place)
Bd = A["bed"]; (bx0, bx1), (bz0, bz1) = Bd["x"], Bd["z"]; bd = Bd["back_d"]
box(sofa, bx0, bx1, F, F + Bd["top"] - 0.12, bz0, bz1)
box(sofa, bx0, bx0 + bd, F + Bd["top"], F + Bd["back"], bz0, bz1)                 # its back to the rear knee wall (poster bed 26)
box(mattress, bx0 + bd + 0.01, bx1 - 0.02, F + Bd["top"] - 0.12, F + Bd["top"], bz0 + 0.03, bz1 - 0.03)
for za, zb in ((bz0 + 0.12, bz0 + 0.92), (bz1 - 0.92, bz1 - 0.12)):                 # two pillows against the back
    box(mattress, bx0 + bd + 0.03, bx0 + bd + 0.45, F + Bd["top"], F + Bd["top"] + 0.12, za, zb)

# ---------------------------------------------------------------- the crib beyond the bed, the lamp table and the film's lamp (1410/1418)
Cb = A["crib"]; (kx0, kx1), (kz0, kz1), kh_ = Cb["x"], Cb["z"], Cb["h"]
for x in (kx0, kx1 - 0.05):
    for z in (kz0, kz1 - 0.05):
        box(crib, x, x + 0.05, F, F + kh_, z, z + 0.05)                            # corner posts
for z in (kz0, kz1 - 0.05):                                                       # long sides: rails and slats
    box(crib, kx0 + 0.05, kx1 - 0.05, F + kh_ - 0.06, F + kh_ - 0.02, z + 0.01, z + 0.04)
    box(crib, kx0 + 0.05, kx1 - 0.05, F + 0.25, F + 0.29, z + 0.01, z + 0.04)
    n = int((kx1 - kx0 - 0.10) / 0.075)
    for k in range(1, n):
        x = kx0 + 0.05 + k * (kx1 - kx0 - 0.10) / n
        box(crib, x - 0.0125, x + 0.0125, F + 0.29, F + kh_ - 0.06, z + 0.015, z + 0.035)
for x in (kx0, kx1 - 0.05):                                                       # end panels
    box(crib, x + 0.01, x + 0.04, F + 0.25, F + kh_ - 0.02, kz0 + 0.05, kz1 - 0.05)
box(cribmat, kx0 + 0.05, kx1 - 0.05, F + 0.29, F + 0.41, kz0 + 0.04, kz1 - 0.04)
Lt = A["lamp_table"]; (tx0, tx1), (tz0, tz1), th_ = Lt["x"], Lt["z"], Lt["h"]
box(ltable, tx0, tx1, F + th_ - 0.03, F + th_, tz0, tz1)
for x in (tx0 + 0.03, tx1 - 0.07):
    for z in (tz0 + 0.03, tz1 - 0.07):
        box(ltable, x, x + 0.04, F, F + th_ - 0.03, z, z + 0.04)
Lp = A["lamp"]; (lpx, lpy, lpz), (rt_, rb_, s0, s1) = Lp["at"], Lp["shade"]
yb = F + lpy
lglass.lathe(lpx, lpz, yb, [(0.0, 0.07), (0.03, 0.07), (0.05, 0.03), (0.12, 0.085), (0.24, 0.07), (0.30, 0.025), (s0 + 0.04, 0.012)], 16)
shade.lathe(lpx, lpz, yb + s0, [(0.0, rb_), (s1 - s0, rt_)], 24)
# bare-bulb pull-chain fixtures under the collar ties (porcelain lamp holder, a clear bulb, a chain)
for b in A["bulbs"]:
    bx, bz = b["at"]; yt_ = b["tie_y"]                                            # reconcile.py snapped it to a collar tie
    porcelain.lathe(bx, bz, yt_ - 0.07, [(0.0, 0.035), (0.04, 0.04), (0.06, 0.055), (0.07, 0.055)], 16)
    bulb.lathe(bx, bz, yt_ - 0.20, [(0.0, 0.01), (0.03, 0.03), (0.07, 0.032), (0.11, 0.015), (0.13, 0.013)], 16)
    box(porcelain, bx + 0.03, bx + 0.034, yt_ - 0.35, yt_ - 0.06, bz - 0.002, bz + 0.002)   # pull chain

# ---------------------------------------------------------------- export
for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob)
coll = bpy.data.collections.new("Attic"); bpy.context.scene.collection.children.link(coll)
mats = {n: material(n, c, r) for n, c, r in (
    ("AT_Boards", (0.55, 0.36, 0.20), 0.7), ("AT_Shingle", (0.10, 0.11, 0.12), 0.9), ("AT_Rafter", (0.45, 0.28, 0.15), 0.7),
    ("AT_Floor", (0.35, 0.30, 0.26), 0.8), ("AT_Brick", (0.16, 0.05, 0.03), 0.9), ("AT_Iron", (0.06, 0.06, 0.06), 0.6),
    ("AT_Rail", (0.70, 0.50, 0.28), 0.6), ("AT_Paint", (0.88, 0.87, 0.82), 0.5), ("AT_Glass", (0.8, 0.85, 0.9), 0.05),
    ("AT_Curtain", (0.86, 0.80, 0.66), 0.9), ("AT_Sofa", (0.20, 0.12, 0.06), 0.9), ("AT_Mattress", (0.60, 0.60, 0.58), 0.9),
    ("AT_Wood", (0.22, 0.12, 0.06), 0.6), ("AT_LampGlass", (0.75, 0.22, 0.06), 0.15), ("AT_Shade", (0.90, 0.86, 0.74), 0.9),
    ("AT_Bulb", (1.0, 0.95, 0.85), 0.1), ("AT_Porcelain", (0.92, 0.91, 0.88), 0.3))}
root = bpy.data.objects.new("Attic_HiFi", None); coll.objects.link(root)
for p in [boards, roofout, rafter, floor, brick, iron, rail, paint, curtain, sofa, mattress, crib, cribmat, ltable, lglass, shade, bulb, porcelain] + [q for pair in leaves.values() for q in pair]:
    if p.f:
        p.build(coll, mats).parent = root
OUT.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(OUT), export_format="GLB", use_selection=False, export_apply=True)
print("hifi_attic: wrote", OUT)
