"""hifi_foyer_props: the foyer's furniture and decor as the film shows them (Oct 16, foyer finish), from spec/dressing/foyer_props.json
(measurements: tools/house/foyer_props_measure.py). Spec metres, y above the ground floor.

- CONSOLE: Hepplewhite side table, square tapered legs, apron with one drawer and a brass knob (film 1616/1690/10673)
- CHAIRS (2): mahogany side chairs, red slip seat, vase splat, shaped crest rail, square legs with an H stretcher
- MIRROR: tall rectangular gilt pier mirror with a scrolled crest and a small apron
- BENCH: green velvet bench with scrolled (rolled) arms on cabriole legs (Marina M01; film 2677/3888 green)
- RUGS: the runner and the front rug, a slab with an invented pattern (foyer_textures.py) and cotton fringes at the ends; the front
  rug and the runner are the fallbacks when the user's bought rugs are absent (tools/house/purchased_rugs.py: the Nain, and a
  runner cut from the Heriz photo; SpecGreybox.PurchasedRug)
- PICTURES: the stair gallery (10), the picture under the landing, the landing print: gilt / dark / black / oval frames, mats, art
  from the public-domain atlas spec/dressing/foyer_art.png (foyer_textures.py)
- PLANTS: red poinsettia on the console, white under it, red + a green plant on the landing table, crinkled gold-foil pots
Every part is built with hifi_lib's Part.box/lathe/sweep/face (faces outward by construction); overlays >= 1 cm proud.
Materials FP_* are remapped in SpecGreybox.FoyerProps; the art and rug materials carry their images in the .glb.

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P tools/house/hifi_foyer_props.py
  -> unity/HomeAlone/Assets/Models/Foyer/FoyerProps.glb
"""
import json
import math
import random
import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hifi_lib import Part, material   # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "unity/HomeAlone/Assets/Models/Foyer/FoyerProps.glb"
D = json.loads((ROOT / "spec/dressing/foyer_props.json").read_text())
ATLAS = json.loads((ROOT / "spec/dressing/foyer_art.json").read_text())["pictures"]
FW, GMAT = 0.03, 0.02   # frame moulding, gallery mat (foyer_textures.py)

parts = {}


def part(name, mat):
    if name not in parts:
        parts[name] = Part(name, mat)
    return parts[name]


wood, red, green, gilt, black, glass, brass = (part("Wood", "FP_Wood"), part("Seat", "FP_Red"), part("Velvet", "FP_Green"), part("Gilt", "FP_Gilt"),
                                               part("BlackFrame", "FP_Black"), part("Glass", "FP_Glass"), part("Brass", "FP_Brass"))
art, mat_c, mat_b = part("Art", "FP_Art"), part("Mat", "FP_Mat"), part("MatBurgundy", "FP_MatBurgundy")
wicker = part("Wicker", "FP_Wicker")
poin_foil, poin_leaf = part("PoinFoil", "FP_Foil"), part("PoinLeaf", "FP_Leaf")   # the poinsettias' own parts: hidden when the bought model is placed
foil, leaf, bract_r, bract_w = part("Foil", "FP_Foil"), part("Leaf", "FP_Leaf"), part("BractRed", "FP_BractRed"), part("BractWhite", "FP_BractWhite")


# ---------------------------------------------------------------- solids
def prism(p, outline, axis, a0, a1):
    """a flat outline extruded: axis 'z' -> outline in (x, y), from z a0 to a1; axis 'x' -> outline in (z, y), from x a0 to a1"""
    P = (lambda q, w: (q[0], q[1], w)) if axis == "z" else (lambda q, w: (w, q[1], q[0]))
    n = (0, 0, 1) if axis == "z" else (1, 0, 0)
    p.face([P(q, a1) for q in outline], n); p.face([P(q, a0) for q in outline], tuple(-c for c in n))
    area = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(outline, outline[1:] + outline[:1]))   # > 0: counter-clockwise
    for q0, q1 in zip(outline, outline[1:] + outline[:1]):
        e = (q1[0] - q0[0], q1[1] - q0[1]); nrm = (e[1], -e[0]) if area > 0 else (-e[1], e[0])    # outward for any (concave) outline
        p.face([P(q0, a0), P(q1, a0), P(q1, a1), P(q0, a1)], P((nrm[0], nrm[1]), 0) if axis == "z" else (0, nrm[1], nrm[0]))


def frustum(p, x0, x1, z0, z1, bx0, bx1, bz0, bz1, y0, y1):
    """a box whose bottom (y0) is the rectangle bx/bz and top (y1) is x/z: a tapered leg"""
    B = [(bx0, y0, bz0), (bx1, y0, bz0), (bx1, y0, bz1), (bx0, y0, bz1)]; T = [(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)]
    p.face(T, (0, 1, 0)); p.face(B, (0, -1, 0))
    for i, n in enumerate([(0, 0, -1), (1, 0, 0), (0, 0, 1), (-1, 0, 0)]):
        j = (i + 1) % 4; p.face([B[i], B[j], T[j], T[i]], n)


def leg(p, cx, cz, y0, y1, wt, wb):
    frustum(p, cx - wt / 2, cx + wt / 2, cz - wt / 2, cz + wt / 2, cx - wb / 2, cx + wb / 2, cz - wb / 2, cz + wb / 2, y0, y1)


# ---------------------------------------------------------------- console (Hepplewhite)
def console():
    c = D["console"]; (x0, x1), (z0, z1), top = c["x"], c["z"], c["top"]
    wood.box(x0, x1, top - 0.025, top, z0, z1)                                               # top, 25 mm
    ax0, ax1, az0, az1, ay0 = x0 + 0.02, x1 - 0.02, z0 + 0.02, z1 - 0.02, top - 0.125
    wood.box(ax0, ax1, ay0, top - 0.025, az0, az1)                                           # apron
    wood.box((x0 + x1) / 2 - 0.26, (x0 + x1) / 2 + 0.26, ay0 + 0.015, top - 0.04, az1, az1 + 0.012)   # drawer front, 1.2 cm proud
    brass.box((x0 + x1) / 2 - 0.012, (x0 + x1) / 2 + 0.012, (ay0 + top - 0.025) / 2 - 0.012, (ay0 + top - 0.025) / 2 + 0.012, az1 + 0.012, az1 + 0.03)
    for lx in (ax0 + 0.0225, ax1 - 0.0225):
        for lz in (az0 + 0.0225, az1 - 0.0225):
            leg(wood, lx, lz, 0.0, ay0, 0.045, 0.024)                                         # square taper


# ---------------------------------------------------------------- side chairs
def chair(cx):
    c = D["chairs"]; zb, zf = c["z"]; seat, top, fw, bw = c["seat"], c["back_top"], c["front_w"], c["back_w"]
    rail0, rail1 = seat - 0.12, seat - 0.06                                                  # the seat frame under the slip seat
    # legs: back legs up to the frame, front legs square
    for s in (-1, 1):
        leg(wood, cx + s * (bw / 2 - 0.02), zb + 0.02, 0.0, rail0, 0.04, 0.034)
        leg(wood, cx + s * (fw / 2 - 0.0225), zf - 0.0225, 0.0, rail0, 0.045, 0.045)
    # seat frame: a trapezoid in plan, 6 cm deep
    outline = [(cx - bw / 2, zb), (cx + bw / 2, zb), (cx + fw / 2, zf), (cx - fw / 2, zf)]
    def slab(p, ol, y0, y1):
        P = lambda q, y: (q[0], y, q[1])
        p.face([P(q, y1) for q in ol], (0, 1, 0)); p.face([P(q, y0) for q in ol], (0, -1, 0))
        mx = sum(q[0] for q in ol) / 4; mz = sum(q[1] for q in ol) / 4
        for q0, q1 in zip(ol, ol[1:] + ol[:1]):
            p.face([P(q0, y0), P(q1, y0), P(q1, y1), P(q0, y1)], ((q0[0] + q1[0]) / 2 - mx, 0, (q0[1] + q1[1]) / 2 - mz))
    slab(wood, outline, rail0, rail1)
    ins = 0.012                                                                               # the red slip seat sits inside the frame's top edge, behind the posts
    cushion = [(cx - bw / 2 + ins + 0.02, zb + 0.045), (cx + bw / 2 - ins - 0.02, zb + 0.045), (cx + fw / 2 - ins, zf - ins), (cx - fw / 2 + ins, zf - ins)]
    slab(red, cushion, rail1, seat)
    # H stretcher
    for s in (-1, 1):
        a = (cx + s * (fw / 2 - 0.0225), 0.11, zf - 0.0225); b = (cx + s * (bw / 2 - 0.02), 0.11, zb + 0.02)
        wood.sweep([a, b], [(-0.011, -0.011), (0.011, -0.011), (0.011, 0.011), (-0.011, 0.011)])
    wood.box(cx - (fw + bw) / 4 + 0.03, cx + (fw + bw) / 4 - 0.03, 0.10, 0.12, (zb + zf) / 2 - 0.011, (zb + zf) / 2 + 0.011)
    # back: posts from the frame to the crest, shoe, vase splat, shaped crest rail
    cr0 = top - 0.06
    for s in (-1, 1):
        wood.box(cx + s * (bw / 2 - 0.02) - 0.019, cx + s * (bw / 2 - 0.02) + 0.019, rail1, cr0, zb + 0.002, zb + 0.038)
    wood.box(cx - bw / 2 + 0.045, cx + bw / 2 - 0.045, rail1, rail1 + 0.03, zb + 0.008, zb + 0.032)        # shoe
    hw = [(0.0, 0.035), (0.12, 0.075), (0.30, 0.095), (0.50, 0.06), (0.68, 0.035), (0.85, 0.055), (1.0, 0.075)]   # vase splat half-widths
    H = cr0 - (rail1 + 0.03)
    ol = [(cx + w, rail1 + 0.03 + f * H) for f, w in hw] + [(cx - w, rail1 + 0.03 + f * H) for f, w in reversed(hw)]
    prism(wood, ol, "z", zb + 0.012, zb + 0.028)
    crest = [(cx - bw / 2 - 0.012, cr0), (cx + bw / 2 + 0.012, cr0), (cx + bw / 2 + 0.02, top - 0.005), (cx + bw / 4, top - 0.012), (cx, top + 0.01),
             (cx - bw / 4, top - 0.012), (cx - bw / 2 - 0.02, top - 0.005)]
    prism(wood, crest, "z", zb + 0.004, zb + 0.036)


# ---------------------------------------------------------------- mirror
def mirror():
    m = D["mirror"]; cx, w, (y0, y1), zb, dep = m["cx"], m["w"], m["y"], m["z_back"], m["depth"]
    # The ornate frame is a separate artist-pipeline asset (FoyerMirror.glb).
    f=.065; x0,x1=cx-w/2,cx+w/2
    glass.box(x0+f,x1-f,y0+f,y1-f,zb+.004,zb+.016)


# ---------------------------------------------------------------- bench
def bench():
    b = D["bench"]; (x0, x1), (z0, z1), seat, arm = b["x"], b["z"], b["seat"], b["arm_top"]
    aw, r = 0.13, 0.065
    wood.box(x0 + 0.03, x1 - 0.03, 0.27, 0.33, z0 + 0.03, z1 - 0.03)                         # seat rail
    green.box(x0 + aw, x1 - aw, 0.33, seat, z0 + 0.01, z1 - 0.01)                               # upholstered seat
    for side in (-1, 1):                                                                      # rolled arms, curling outward
        xi = x0 + aw if side < 0 else x1 - aw; ccx = xi + side * r; ccy = arm - r; xo = ccx + side * r
        ol = [(xi, 0.33), (xi, ccy)] + [(ccx - side * r * math.cos(t), ccy + r * math.sin(t)) for t in [math.pi * k / 12 for k in range(1, 13)]]
        ol += [(xo - side * 0.02, ccy - 0.06), (xo - side * 0.02, 0.33)]
        prism(green, ol, "z", z0, z1)
    for lx in (x0 + 0.06, x1 - 0.06):                                                         # cabriole legs: knee out, ankle in, pad foot
        for lz in (z0 + 0.06, z1 - 0.06):
            ox, oz = (1 if lx > (x0 + x1) / 2 else -1) * 0.022, (1 if lz > (z0 + z1) / 2 else -1) * 0.022
            path = [(lx + ox * k, y, lz + oz * k) for y, k in ((0.27, 0.0), (0.22, 0.8), (0.15, 0.3), (0.08, -0.3), (0.035, 0.1))]
            wood.sweep(path, [(0.018 * math.cos(a), 0.018 * math.sin(a)) for a in [i * math.pi / 4 for i in range(8)]])
            fx, fz = path[-1][0] + ox * 0.4, path[-1][2] + oz * 0.4
            wood.lathe(fx, fz, 0.0, [(0, 0.022), (0.012, 0.026), (0.03, 0.016)], n=12)


# ---------------------------------------------------------------- rugs
def rug(r, along, tex):
    (x0, x1), (z0, z1), fr = r["x"], r["z"], r["fringe"]; y = 0.012
    p = part("Rug_" + tex, "FP_" + tex)
    # top face with UVs: u across, v along the length (rows of the image run along the rug)
    if along == "x":
        pts = [(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)]; uvs = [(0, 0), (0, 1), (1, 1), (1, 0)]
    else:
        pts = [(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)]; uvs = [(0, 0), (1, 0), (1, 1), (0, 1)]
    p.face(pts, (0, 1, 0), uvs)
    p.face([(x0, 0.002, z0), (x1, 0.002, z0), (x1, 0.002, z1), (x0, 0.002, z1)], (0, -1, 0))
    for (a, b, n) in (((x0, z0), (x1, z0), (0, 0, -1)), ((x1, z0), (x1, z1), (1, 0, 0)), ((x1, z1), (x0, z1), (0, 0, 1)), ((x0, z1), (x0, z0), (-1, 0, 0))):
        p.face([(a[0], 0.002, a[1]), (b[0], 0.002, b[1]), (b[0], y, b[1]), (a[0], y, a[1])], n)
    fringe = part("Fringe_" + tex, "FP_Fringe")   # per rug: SpecGreybox hides the front rug's (body + fringe) under the bought one
    random.seed(len(tex))
    ends = ((x0, -1), (x1, 1)) if along == "x" else ((z0, -1), (z1, 1))
    span = (z0, z1) if along == "x" else (x0, x1)
    for e, s in ends:                                                                         # cotton fringe: 4 mm threads every 8 mm, 1 cm proud of the floor
        t = span[0] + 0.01
        while t < span[1] - 0.01:
            L = fr * random.uniform(0.75, 1.1)
            if along == "x":
                q = [(e, 0.01, t), (e + s * L, 0.01, t), (e + s * L, 0.01, t + 0.004), (e, 0.01, t + 0.004)]
            else:
                q = [(t, 0.01, e), (t, 0.01, e + s * L), (t + 0.004, 0.01, e + s * L), (t + 0.004, 0.01, e)]
            fringe.face(q, (0, 1, 0)); t += 0.008


# ---------------------------------------------------------------- pictures
def pic(key, p, wall, gallery):
    """wall: 'stair' (face z 11.43, room -z, along x) | 'picture' (x 2.985, room +x, along z) | 'landing_window' (x 1.58, +x, along z)"""
    face = D["wall_faces"][wall]
    if wall == "stair":
        Pt = lambda a, y, d: (a, y, face - d); a0, a1 = p["x"]; inward = (0, 0, -1)
    else:
        Pt = lambda a, y, d: (face + d, y, a); a0, a1 = p["z"]; inward = (1, 0, 0)

    def lbox(pp, b0, b1, y0, y1, d0, d1):
        A, B = Pt(b0, y0, d0), Pt(b1, y1, d1)
        pp.box(min(A[0], B[0]), max(A[0], B[0]), y0, y1, min(A[2], B[2]), max(A[2], B[2]))
    y0, y1 = p["y"]; style = p.get("frame", "gilt"); fp = {"gilt": gilt, "dark": wood, "black": black}.get(style, gilt)
    uv = ATLAS[key]["uv"]
    if style == "oval":
        ca, cy, ra, ry = (a0 + a1) / 2, (y0 + y1) / 2, (a1 - a0) / 2, (y1 - y0) / 2; n = 40
        ell = lambda sa, sy, k: (ca + sa * math.cos(2 * math.pi * k / n), cy + sy * math.sin(2 * math.pi * k / n))
        for k in range(n):                                                                    # a moulded oval ring, 3 cm, 2.5 cm deep
            o0, o1, i0, i1 = ell(ra, ry, k), ell(ra, ry, k + 1), ell(ra - FW, ry - FW, k), ell(ra - FW, ry - FW, k + 1)
            gilt.face([Pt(*o0, 0.03), Pt(*o1, 0.03), Pt(*i1, 0.03), Pt(*i0, 0.03)], inward)
            gilt.face([Pt(*o0, 0.005), Pt(*o1, 0.005), Pt(*i1, 0.005), Pt(*i0, 0.005)], tuple(-c for c in inward))
            mo = ((o0[0] + o1[0]) / 2 - ca, (o0[1] + o1[1]) / 2 - cy)
            nvec = (mo[0], mo[1], 0) if wall == "stair" else (0, mo[1], mo[0])
            gilt.face([Pt(*o0, 0.005), Pt(*o1, 0.005), Pt(*o1, 0.03), Pt(*o0, 0.03)], nvec)
            gilt.face([Pt(*i0, 0.005), Pt(*i1, 0.005), Pt(*i1, 0.03), Pt(*i0, 0.03)], tuple(-c for c in nvec))
        ring = [ell(ra - FW + 0.003, ry - FW + 0.003, k) for k in range(n)]
        art.face([Pt(a, y, 0.018) for a, y in ring], inward,
                 [(uv[0] + (uv[2] - uv[0]) * ((1 - fu) if wall == "stair" else fu), uv[1] + (uv[3] - uv[1]) * fv)
                  for fu, fv in [((a - (ca - ra + FW)) / (2 * (ra - FW)), (y - (cy - ry + FW)) / (2 * (ry - FW))) for a, y in ring]])
        mat_c.face([Pt(*ell(ra - FW + 0.004, ry - FW + 0.004, k), 0.008) for k in range(n)], inward)   # backing behind the art
        return
    mw = GMAT if gallery else p["mat"]
    lbox(fp, a0, a1, y1 - FW, y1, 0.001, 0.03); lbox(fp, a0, a1, y0, y0 + FW, 0.001, 0.03)
    lbox(fp, a0, a0 + FW, y0 + FW, y1 - FW, 0.001, 0.03); lbox(fp, a1 - FW, a1, y0 + FW, y1 - FW, 0.001, 0.03)
    mp = mat_b if p.get("mat_colour") == "burgundy" else mat_c
    lbox(mp, a0 + FW, a1 - FW, y0 + FW, y1 - FW, 0.002, 0.012)                                 # the mat board, set back in the frame
    ia0, ia1, iy0, iy1 = a0 + FW + mw, a1 - FW - mw, y0 + FW + mw, y1 - FW - mw
    # the art, 1.2 cm proud of the mat; u runs along the wall in the room's view (left to right seen from the room)
    flip = wall == "stair"     # seen from the room (-z side) +x runs to the LEFT on the stair wall
    ua, ub = (uv[2], uv[0]) if flip else (uv[0], uv[2])
    art.face([Pt(ia0, iy0, 0.024), Pt(ia1, iy0, 0.024), Pt(ia1, iy1, 0.024), Pt(ia0, iy1, 0.024)], inward,
             [(ua, uv[1]), (ub, uv[1]), (ub, uv[3]), (ua, uv[3])])


# ---------------------------------------------------------------- plants (as hifi_dressing.py's, sized per piece)
def plant(q, seed):
    random.seed(seed)
    cx, cz = q["at"]; y0, spread, height = q["y0"], q["spread"] / 2, q["height"]
    ph = min(0.20, height * 0.45); pr = spread * 0.55
    prof = [(0, pr * 0.62), (0.02, pr * 0.7), (ph * 0.85, pr * 0.95), (ph * 0.93, pr * 1.04), (ph, pr * 0.9)]
    poin = q["bract"] != "none"
    pot = wicker if q.get("pot") == "wicker" else poin_foil if poin else foil
    lp = poin_leaf if poin else leaf
    pot.lathe(cx, cz, y0, [(h, r * random.uniform(0.95, 1.05)) for h, r in prof], n=18)   # crinkled foil (or a wicker basket)
    top = y0 + ph + 0.02; dome = height - ph   # leaves start above the rim: none passes through the foil

    def blade(pp, ox, oy, oz, ang, tilt, L, W):
        dx, dz = math.cos(ang), math.sin(ang); up = math.sin(tilt); hz = math.cos(tilt)
        if "wall_x" in q and dx < 0:   # against a wall (the landing's): leaves toward it stop 4 cm short of the frames hung there
            L = min(L, (ox - q["wall_x"] - 0.05) / max(-dx * hz, 1e-3))
        tip = (ox + dx * L * hz, oy + L * up, oz + dz * L * hz)
        midp = (ox + dx * L * 0.45 * hz, oy + L * 0.45 * up + 0.006, oz + dz * L * 0.45 * hz)
        sx, sz = -dz * W, dx * W
        for side in (1, -1):
            pp.face([(ox, oy, oz), (midp[0] + side * sx, midp[1], midp[2] + side * sz), tip, midp], (0, 1, 0))
    nl = 30 if q["bract"] != "none" else 46
    for k in range(nl):
        ang = 2 * math.pi * k / 15 + random.uniform(-0.2, 0.2)
        blade(lp, cx, top + random.uniform(0.0, dome * 0.4), cz, ang, random.uniform(-0.12, 0.6 if q["bract"] == "none" else 0.25),
              spread * random.uniform(0.7, 1.0), 0.035 if q["bract"] == "none" else 0.045)
    if q["bract"] == "none":
        return
    bp = bract_r if q["bract"] == "red" else bract_w
    nr = 18
    for c in range(nr):
        ca = 2 * math.pi * c * 0.618 + random.uniform(-0.3, 0.3); cr = 0 if c == 0 else spread * math.sqrt(c / nr) * 0.72
        ox, oz = cx + cr * math.cos(ca), cz + cr * math.sin(ca)
        oy = top + 0.03 + dome * 0.75 * (1 - (cr / (spread * 0.72)) ** 2) + random.uniform(-0.015, 0.015)
        for k in range(7):
            blade(bp, ox, oy, oz, 2 * math.pi * k / 7 + random.uniform(-0.2, 0.2), random.uniform(0.1, 0.6), spread * random.uniform(0.32, 0.5), 0.038)


console()
for cx in D["chairs"]["centres_x"]:
    chair(cx)
mirror(); bench()
rug(D["runner"], "x", "RugRunner"); rug(D["front_rug"], "z", "RugFront")
for k in ("under_landing", "landing"):
    pic(k, D["pictures"][k], D["pictures"][k]["wall"], False)
for i, g in enumerate(D["pictures"]["gallery"]):
    pic(f"gallery{i + 1}", g, "stair", True)
for i, (k, q) in enumerate(D["plants"].items()):
    plant(q, 11 + i)

# ---------------------------------------------------------------- export
bpy.ops.wm.read_factory_settings(use_empty=True)


def tex_material(name, img_path, rough):
    m = material(name, (1, 1, 1), rough)
    nt = m.node_tree; t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(str(img_path)); t.image.pack()
    nt.links.new(t.outputs["Color"], nt.nodes["Principled BSDF"].inputs["Base Color"]); return m


M = {"FP_Wood": material("FP_Wood", (0.10, 0.035, 0.022), 0.45), "FP_Red": material("FP_Red", (0.42, 0.03, 0.045), 0.85),
     "FP_Green": material("FP_Green", (0.045, 0.11, 0.06), 0.85), "FP_Gilt": material("FP_Gilt", (0.72, 0.55, 0.25), 0.35),
     "FP_Black": material("FP_Black", (0.02, 0.02, 0.02), 0.4), "FP_Glass": material("FP_Glass", (0.8, 0.8, 0.8), 0.05),
     "FP_Brass": material("FP_Brass", (0.75, 0.56, 0.25), 0.3), "FP_Mat": material("FP_Mat", (0.82, 0.78, 0.68), 0.9),
     "FP_MatBurgundy": material("FP_MatBurgundy", (0.25, 0.04, 0.05), 0.9), "FP_Fringe": material("FP_Fringe", (0.80, 0.76, 0.66), 0.95),
     "FP_Foil": material("FP_Foil", (0.78, 0.6, 0.3), 0.25), "FP_Wicker": material("FP_Wicker", (0.45, 0.30, 0.15), 0.9), "FP_Leaf": material("FP_Leaf", (0.06, 0.13, 0.06), 0.55),
     "FP_BractRed": material("FP_BractRed", (0.62, 0.03, 0.05), 0.6), "FP_BractWhite": material("FP_BractWhite", (0.90, 0.90, 0.84), 0.6),
     "FP_Art": tex_material("FP_Art", ROOT / "spec/dressing/foyer_art.png", 0.6),
     "FP_RugRunner": tex_material("FP_RugRunner", ROOT / "spec/dressing/rug_runner.png", 0.95),
     "FP_RugFront": tex_material("FP_RugFront", ROOT / "spec/dressing/rug_front.png", 0.95)}
coll = bpy.context.scene.collection
root = bpy.data.objects.new("FoyerProps_HiFi", None); coll.objects.link(root)
for p in parts.values():
    if p.f:
        p.build(coll, M).parent = root
OUT.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(OUT), export_format="GLB", export_yup=True, export_apply=True)
print("wrote", OUT, {p.name: len(p.f) for p in parts.values()})
