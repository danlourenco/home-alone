"""hifi_kitchen: the kitchen's cabinets, tiled counters, appliances, window seats and L-shaped island (user, Oct 16: "add the
kitchen cabinets ... as seen in marina's layouts"; "get the cabinet sizing right and then generate a high quality texture").

Every position comes from spec/dressing/kitchen.json (measured: tools/house/kitchen_walls.py --fixtures). Profiles are authored to
the film (6902, 9812, film-island-detail.jpg): overlay doors with a raised centre panel, a drawer over two doors, brass bail pulls
on drawers and curved bar pulls on doors, a recessed toe kick, 6 in tile with a cobalt bullnose edge tile along every exposed edge
(one piece per tile, 6 mm grout gaps), one row of tile up the wall.

Faces: every visible face stands >= 1 cm off a same-facing face it overlaps (zfight-check); flat faces via Part.face (no hand
winding). Materials by name, remapped in SpecGreybox.KitchenModel: KT_Wood (Poly Haven cherry, triplanar), KT_Tile (generated maps,
these UVs: one texture = 8 tiles, laid from each counter's front edge), KT_Edge, KT_Grout, KT_Brass, KT_Black, KT_Steel, KT_Sink,
KT_Cushion. Collision is not in the model: SpecGreybox builds invisible boxes from kitchen.json "colliders".

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P tools/house/hifi_kitchen.py
  -> unity/HomeAlone/Assets/Models/Foyer/KitchenCabinets.glb
"""
import json
import math
import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hifi_lib import Part, material   # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "unity/HomeAlone/Assets/Models/Foyer/KitchenCabinets.glb"
K = json.loads((ROOT / "spec/dressing/kitchen.json").read_text()); S = K["std"]
CH, SB, TT, TOE, TR, DT, GAP = S["counter_h"], S["slab_bottom"], S["tile_top"], S["toe_h"], S["toe_recess"], S["door_t"], S["gap"]
UB, UT, P, GR, EW, ED, EP, BH = S["upper_bottom"], S["upper_top"], S["tile_pitch"], S["grout"], S["edge_w"], S["edge_drop"], S["edge_proud"], S["backsplash_h"]
TEX = 8 * P                                                           # metres per texture repeat (kitchen_tile_tex.py: 8 tiles)

wood, tile, edge, grout, brass, black, steel, sink, cushion, housing, glow = (Part(n, "KT_" + n) for n in
    ("Wood", "Tile", "Edge", "Grout", "Brass", "Black", "Steel", "Sink", "Cushion", "Housing", "UnderLight"))
# Oct 19 (kitchen fidelity, user photo IMG_4305 / film 2116): the corner cupboard is knotty pine in four stacked sections, not
# cherry; the fridge's left door has the ice/water dispenser (film 1050/1146); the wall oven reads black (film 6044)
pine, disp = Part("Pine", "KT_Pine"), Part("Dispenser", "KT_Dispenser")
UL = K.get("under_lights")
AX = {"+x": (1, 0), "-x": (-1, 0), "+z": (0, 1), "-z": (0, -1)}


# ---------------------------------------------------------------- oriented boxes and prisms
def obox(p, o, e, n, a0, a1, d0, d1, y0, y1):
    """A box: o = (x, z) on the reference line, e = unit along-direction, n = unit outward normal (both horizontal),
    a: along e, d: along n (outward), y: up."""
    def pt(a, d, y): return (o[0] + a * e[0] + d * n[0], y, o[1] + a * e[1] + d * n[1])
    for (y, s) in ((y1, 1), (y0, -1)):
        p.face([pt(a0, d0, y), pt(a1, d0, y), pt(a1, d1, y), pt(a0, d1, y)], (0, s, 0))
    p.face([pt(a0, d1, y0), pt(a1, d1, y0), pt(a1, d1, y1), pt(a0, d1, y1)], (n[0], 0, n[1]))
    p.face([pt(a0, d0, y0), pt(a1, d0, y0), pt(a1, d0, y1), pt(a0, d0, y1)], (-n[0], 0, -n[1]))
    p.face([pt(a1, d0, y0), pt(a1, d1, y0), pt(a1, d1, y1), pt(a1, d0, y1)], (e[0], 0, e[1]))
    p.face([pt(a0, d0, y0), pt(a0, d1, y0), pt(a0, d1, y1), pt(a0, d0, y1)], (-e[0], 0, -e[1]))


def front_frame(front, F):
    """A front on an axis-aligned plane: returns o (on the plane), e (along, increasing x or z), n (outward)."""
    nx, nz = AX[front]
    return ((F, 0.0) if nx else (0.0, F)), ((0.0, 1.0) if nx else (1.0, 0.0)), (float(nx), float(nz))


def prism(p, poly, y0, y1, sides=True):
    """A vertical prism over a CCW-or-CW polygon [(x, z)]; side faces point away from the centroid side (convex-safe via the
    polygon's own orientation)."""
    area = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(poly, poly[1:] + poly[:1]))
    p.face([(x, y1, z) for x, z in poly], (0, 1, 0)); p.face([(x, y0, z) for x, z in poly], (0, -1, 0))
    if not sides: return
    for a, b in zip(poly, poly[1:] + poly[:1]):
        dx, dz = b[0] - a[0], b[1] - a[1]; out = (dz, -dx) if area > 0 else (-dz, dx)   # area>0: CCW in (x, z) -> outward is (dz, -dx)
        p.face([(a[0], y0, a[1]), (b[0], y0, b[1]), (b[0], y1, b[1]), (a[0], y1, a[1])], (out[0], 0, out[1]))


# ---------------------------------------------------------------- fronts: doors, drawers, pulls
def raised(p, o, e, n, a0, a1, y0, y1, inset):
    """A front slab (DT thick, behind the front plane) with a raised centre panel 1.2 cm proud."""
    obox(p, o, e, n, a0, a1, -DT, 0.0, y0, y1)
    if a1 - a0 > 2 * inset + 0.02 and y1 - y0 > 2 * inset + 0.02:
        obox(p, o, e, n, a0 + inset, a1 - inset, 0.0, 0.012, y0 + inset, y1 - inset)


def bail(o, e, n, ac, yc, base, w=0.10):
    """A brass bail pull: two rosettes and a bar bowed 2.5 cm out from 'base' (the face it is fixed to), centred at ac, yc."""
    for s in (-1, 1):
        obox(brass, o, e, n, ac + s * w / 2 - 0.008, ac + s * w / 2 + 0.008, base, base + 0.006, yc - 0.008, yc + 0.008)
    path = []
    for k in range(9):
        t = k / 8; a = ac - w / 2 + w * t; d = base + 0.006 + 0.022 * math.sin(math.pi * t)
        path.append((o[0] + a * e[0] + d * n[0], yc - 0.012 * math.sin(math.pi * t), o[1] + a * e[1] + d * n[1]))
    brass.sweep(path, [(-0.004, -0.004), (0.004, -0.004), (0.004, 0.004), (-0.004, 0.004)])


def bar(o, e, n, ac, y0, y1, base):
    """A curved vertical bar pull for a door (film: brass, bowed)."""
    for y in (y0, y1):
        obox(brass, o, e, n, ac - 0.007, ac + 0.007, base, base + 0.006, y - 0.007, y + 0.007)
    path = [(o[0] + ac * e[0] + (base + 0.006 + 0.02 * math.sin(math.pi * k / 8)) * n[0], y0 + (y1 - y0) * k / 8,
             o[1] + ac * e[1] + (base + 0.006 + 0.02 * math.sin(math.pi * k / 8)) * n[1]) for k in range(9)]
    brass.sweep(path, [(-0.004, -0.004), (0.004, -0.004), (0.004, 0.004), (-0.004, 0.004)])


def module_fronts(o, e, n, a0, a1, typ, lo=TOE + GAP, hi=SB - GAP):
    """The fronts of one base module between a0 and a1 on the front plane (o, e, n)."""
    g = GAP / 2; a0, a1 = a0 + g, a1 - g
    if typ == "blind":
        raised(wood, o, e, n, a0, a1, lo, hi, 0.06); return
    if typ in ("dishwasher", "compactor"):
        obox(black, o, e, n, a0, a1, -DT, 0.0, lo, hi)
        obox(steel, o, e, n, a0 + 0.01, a1 - 0.01, 0.0, 0.012, hi - 0.07, hi - 0.01)            # control strip / handle bar
        return
    dr = 0.70                                                                                     # drawer from 0.70 to the counter
    if typ == "door":
        raised(wood, o, e, n, a0, a1, lo, hi, 0.06); bar(o, e, n, a1 - 0.04, hi - 0.2, hi - 0.08, 0.0); return
    if typ == "sink_base":                                                                        # a false front over two doors
        raised(wood, o, e, n, a0, a1, dr + g, hi, 0.035)
    else:
        raised(wood, o, e, n, a0, a1, dr + g, hi, 0.035)
        bail(o, e, n, (a0 + a1) / 2, (dr + hi) / 2 + 0.005, 0.012)
    nd = 2 if a1 - a0 > 0.5 else 1; w = (a1 - a0) / nd
    for k in range(nd):
        b0, b1 = a0 + k * w + (g if k else 0), a0 + (k + 1) * w - (g if k < nd - 1 else 0)
        raised(wood, o, e, n, b0, b1, lo, dr - g, 0.06)
        right = (k == 0) if nd == 2 else True
        bar(o, e, n, (b1 - 0.04) if right else (b0 + 0.04), dr - g - 0.20, dr - g - 0.08, 0.0)


def base_run(b):
    nx, nz = AX[b["front"]]; F = (b["x"][1] if nx > 0 else b["x"][0]) if nx else (b["z"][1] if nz > 0 else b["z"][0])
    o, e, n = front_frame(b["front"], F)
    # carcass and toe: the run's box pulled back from the front plane
    x0, x1, z0, z1 = *b["x"], *b["z"]
    def back(r):
        return (x0, x1 - r, z0, z1) if nx > 0 else (x0 + r, x1, z0, z1) if nx < 0 else (x0, x1, z0, z1 - r) if nz > 0 else (x0, x1, z0 + r, z1)
    cx0, cx1, cz0, cz1 = back(DT)
    # the carcass, lowered under the sink (its bowls hang 0.2 m into it): split along the run at each sink base
    lo_, hi_ = (cz0, cz1) if nx else (cx0, cx1); cuts = sorted([lo_, hi_] + [v for m in b["modules"] if m["type"] == "sink_base" for v in (m["z"] if nx else m["x"])])
    for s0, s1 in zip(cuts, cuts[1:]):
        if s1 - s0 < 1e-6: continue
        sink_here = any(m["type"] == "sink_base" and (m["z"] if nx else m["x"])[0] <= (s0 + s1) / 2 <= (m["z"] if nx else m["x"])[1] for m in b["modules"])
        top = CH - 0.22 if sink_here else SB
        if nx: wood.box(cx0, cx1, TOE, top, s0, s1)
        else: wood.box(s0, s1, TOE, top, cz0, cz1)
    tx0, tx1, tz0, tz1 = back(TR); wood.box(tx0, tx1, 0.0, TOE, tz0, tz1)
    for m in b["modules"]:
        a0, a1 = m["z"] if nx else m["x"]
        module_fronts(o, e, n, a0, a1, m["type"])


# ---------------------------------------------------------------- counters: slab, field tile (UV'd), bullnose edge tiles, backsplash
def cells(poly, holes, cuts_x, cuts_z, keep):
    xs = sorted(set([p[0] for p in poly] + cuts_x + [v for h in holes for v in h["x"]]))
    zs = sorted(set([p[1] for p in poly] + cuts_z + [v for h in holes for v in h["z"]]))
    def inside(x, z):
        c = False
        for (x1, z1), (x2, z2) in zip(poly, poly[1:] + poly[:1]):
            if (z1 > z) != (z2 > z) and x < x1 + (z - z1) * (x2 - x1) / (z2 - z1): c = not c
        return c
    out = {}
    for i in range(len(xs) - 1):
        for j in range(len(zs) - 1):
            mx, mz = (xs[i] + xs[i + 1]) / 2, (zs[j] + zs[j + 1]) / 2
            if inside(mx, mz) and not any(h["x"][0] < mx < h["x"][1] and h["z"][0] < mz < h["z"][1] for h in holes) and keep(mx, mz):
                out[(i, j)] = (xs[i], xs[i + 1], zs[j], zs[j + 1])
    return out, xs, zs


def cell_layer(p, cs, y0, y1, top_part, uv=None, bottom=True, skip_top=()):
    """Top faces per cell (UV'd if uv), side faces only where the neighbouring cell is missing. A layer resting on another gets
    no bottom faces, and the one below no top faces there (no coincident hidden pairs: they made non-manifold parts)."""
    for (i, j), (x0, x1, z0, z1) in cs.items():
        pts = [(x0, y1, z0), (x1, y1, z0), (x1, y1, z1), (x0, y1, z1)]
        if (i, j) not in skip_top:
            top_part.face(pts, (0, 1, 0), [uv(x, z) for x, _, z in pts] if uv else None)
        if bottom:
            p.face([(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)], (0, -1, 0))
        for (di, dj), f in (((1, 0), [(x1, z0), (x1, z1)]), ((-1, 0), [(x0, z0), (x0, z1)]), ((0, 1), [(x0, z1), (x1, z1)]), ((0, -1), [(x0, z0), (x1, z0)])):
            if (i + di, j + dj) in cs: continue
            (ax, az), (bx_, bz) = f
            p.face([(ax, y0, az), (bx_, y0, bz), (bx_, y1, bz), (ax, y1, az)], (di, 0, dj))


def edge_profile():
    r = EP; prof = [(-EW, CH), (0.0, CH)]
    for k in range(1, 6):
        t = math.pi / 2 * k / 6; prof.append((r * math.sin(t), CH - r + r * math.cos(t)))
    prof += [(EP, CH - r), (EP, CH - ED), (0.0, CH - ED), (0.0, TT), (-EW, TT)]
    return prof


def edge_piece(o, e, n, a0, a1):
    """One bullnose edge tile from a0 to a1 along the exposed edge line (o, e), outward n: the profile extruded along e."""
    prof = edge_profile()
    def pt(a, d, y): return (o[0] + a * e[0] + d * n[0], y, o[1] + a * e[1] + d * n[1])
    for (d0, y0), (d1, y1) in zip(prof, prof[1:] + prof[:1]):
        nd, ny = -(y1 - y0), (d1 - d0)                               # outward in the (d, y) plane for a clockwise profile
        L = math.hypot(nd, ny) or 1.0
        edge.face([pt(a0, d0, y0), pt(a1, d0, y0), pt(a1, d1, y1), pt(a0, d1, y1)], (n[0] * nd / L, ny / L, n[1] * nd / L))
    edge.face([pt(a0, d, y) for d, y in prof], (-e[0], 0, -e[1])); edge.face([pt(a1, d, y) for d, y in prof], (e[0], 0, e[1]))


def counter(c):
    poly = [tuple(v) for v in c["poly"]]; holes = c.get("holes", []); N = len(poly)
    area = sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(poly, poly[1:] + poly[:1]))
    def outward(i, j):
        (ax, az), (bx_, bz) = poly[i], poly[j]; L = math.hypot(bx_ - ax, bz - az); dx, dz = (bx_ - ax) / L, (bz - az) / L
        return ((dz, -dx) if area > 0 else (-dz, dx)), (dx, dz), L
    # the tile grid: rows laid from the first (front) edge, EW in; the other axis from grid_origin
    (fi, fj, *_), = c["edges"][:1]; nfront, _, _ = outward(fi, fj)
    gx, gz = c["grid_origin"]; gx -= nfront[0] * EW; gz -= nfront[1] * EW
    uv = lambda x, z: ((x - gx) / TEX, (z - gz) / TEX)
    exposed = []
    for ed in c["edges"]:
        i, j = ed[0], ed[1]; nrm, d, L = outward(i, j)
        s_start = abs(ed[2] - (poly[i][1] if d[1] else poly[i][0])) if len(ed) > 2 else 0.0
        exposed.append((i, j, nrm, d, L, s_start))
    def near_edge(x, z):                                               # within EW inside the exposed part of an edge
        for i, j, nrm, d, L, s_start in exposed:
            ax, az = poly[i]; rx, rz = x - ax, z - az; a = rx * d[0] + rz * d[1]; dd = -(rx * nrm[0] + rz * nrm[1])
            if 0 <= dd <= EW and s_start - 1e-6 <= a <= L + 1e-6: return True
        return False
    cut_x, cut_z = [], []
    for i, j, nrm, d, L, s_start in exposed:
        ax, az = poly[i]
        if nrm[0]: cut_x.append(ax - nrm[0] * EW)
        else: cut_z.append(az - nrm[1] * EW)
        if s_start:
            (cut_z if d[1] else cut_x).append((az if d[1] else ax) + (d[1] or d[0]) * s_start)
    slab_cells, _, _ = cells(poly, holes, cut_x, cut_z, lambda x, z: True)
    field, _, _ = cells(poly, holes, cut_x, cut_z, lambda x, z: not near_edge(x, z))
    cell_layer(grout, slab_cells, SB, TT, grout, skip_top=set(field))  # the slab (its top shows only in the edge tiles' grout gaps)
    cell_layer(grout, field, TT, CH, tile, uv, bottom=False)           # the field tile, 1 cm proud of the slab
    # bullnose edge tiles, one per grid tile, along every exposed edge; corners per the convex/concave rule
    for i, j, nrm, d, L, s_start in exposed:
        ax, az = poly[i]; s0, s1 = s_start, L
        prev = [q for q in exposed if q[1] == i]; nxt = [q for q in exposed if q[0] == j]
        def convex(da, db): return (da[0] * db[1] - da[1] * db[0]) * (1 if area > 0 else -1) > 0
        if prev: s0 += EW if convex(prev[0][3], d) else EP                 # leaving a corner: skip the other edge's strip
        if nxt and convex(d, nxt[0][3]): s1 += EP                          # arriving at a convex corner: cover its protrusion
        A = ax if d[0] else az; sg = d[0] + d[1]; base = gx if d[0] else gz  # world coordinate along the edge = A + sg * s
        w0, w1 = sorted((A + sg * s0, A + sg * s1))
        for t in range(math.floor((w0 - base) / P) - 1, math.ceil((w1 - base) / P) + 1):
            lo, hi = max(base + t * P + GR / 2, w0), min(base + (t + 1) * P - GR / 2, w1)
            if hi - lo > 0.005:
                a_lo, a_hi = sorted(((lo - A) * sg, (hi - A) * sg))
                edge_piece((ax, az), d, nrm, a_lo, a_hi)
    # one row of tile up the wall along the listed wall edges (1.2 cm thick, its face UV'd like the field)
    for i, j in c.get("backsplash", []):
        nrm, d, L = outward(i, j); inn = (-nrm[0], -nrm[1]); ax, az = poly[i]
        o = (ax, az); e = d; n = inn
        a0, a1 = 0.0, L
        def pt(a, dd, y): return (o[0] + a * e[0] + dd * n[0], y, o[1] + a * e[1] + dd * n[1])
        pts = [pt(a0, 0.012, CH), pt(a1, 0.012, CH), pt(a1, 0.012, CH + BH), pt(a0, 0.012, CH + BH)]
        tile.face(pts, (n[0], 0, n[1]), [(((x - gx) if e[0] else (z - gz)) / TEX, (y - CH) / TEX) for x, y, z in pts])
        grout.face([pt(a0, 0, CH + BH), pt(a1, 0, CH + BH), pt(a1, 0.012, CH + BH), pt(a0, 0.012, CH + BH)], (0, 1, 0))
        grout.face([pt(a0, 0, CH), pt(a0, 0.012, CH), pt(a0, 0.012, CH + BH), pt(a0, 0, CH + BH)], (-e[0], 0, -e[1]))
        grout.face([pt(a1, 0, CH), pt(a1, 0.012, CH), pt(a1, 0.012, CH + BH), pt(a1, 0, CH + BH)], (e[0], 0, e[1]))


# ---------------------------------------------------------------- the pieces
for b in K["bases"]:
    base_run(b)
for c in K["counters"]:
    counter(c)

for ib in K["island_bases"]:
    x0, x1, z0, z1 = *ib["x"], *ib["z"]; f = ib["faces"]
    has = lambda k: k in f
    wood.box(x0 + (DT if has("-x") else 0), x1 - (DT if has("+x") else 0), TOE, SB, z0 + (DT if has("-z") else 0), z1 - (DT if has("+z") else 0))
    for side, spec in f.items():
        nx, nz = AX[side]; F = (x1 if nx > 0 else x0) if nx else (z1 if nz > 0 else z0)
        o, e, n = front_frame(side, F)
        if spec == "panel":
            a0, a1 = (z0, z1) if nx else (x0, x1)
            raised(wood, o, e, n, a0 + GAP, a1 - GAP, TOE + GAP, SB - GAP, 0.07)
        else:
            w = (spec["to"] - spec["from"]) / spec["n"]
            for k in range(spec["n"]):
                module_fronts(o, e, n, spec["from"] + k * w, spec["from"] + (k + 1) * w, spec["type"])
# island toe kicks (the union of the two bases, pulled in by TR on every exposed side)
(l, s) = K["island_bases"]
wood.box(l["x"][0] + TR, l["x"][1] - TR, 0.0, TOE, l["z"][0] + TR, l["z"][1] - TR)
wood.box(s["x"][0] + TR, s["x"][1] - TR, 0.0, TOE, l["z"][1] - TR, s["z"][1] - TR)

# ---------------------------------------------------------------- the stacked knotty-pine cupboard (walk note Oct 19 14:47: "what is
# that thing in the corner? it looks weird": a plain slab with smeared triplanar grain). IMG_4305 / film 2116: four stacked pine
# sections, each a face frame round framed raised-panel doors with wooden knobs, a moulded lip between sections, a moulded top.
# Kept in the measured footprint (kitchen.json talls "pantry": 1.29 m angled front, two doors per section; the film's piece reads
# narrower, one door per section: DEVIATIONS). Grain on UVs (KT_UVPine, 1 UV = 1 m): up the stiles and panels, along rails and mouldings.
pineuv = Part("PineUV", "KT_UVPine")   # not "KT_Pine..." (PlaceHiFi remaps by name prefix)
_MEMBER = [0]


def pbox(o, e, n, a0, a1, d0, d1, y0, y1, grain):
    """obox for the pine with per-face UVs (metres) following the member's grain; each member gets its own grain offset."""
    _MEMBER[0] += 1; k = _MEMBER[0]; ou, ov = (k * 0.377) % 1.1, (k * 0.613) % 1.1
    def pt(a, d, y): return (o[0] + a * e[0] + d * n[0], y, o[1] + a * e[1] + d * n[1])
    def uv(corners, kind):          # corners as (a, d, y); kind: which axis the face is normal to
        out = []
        for a, d, y in corners:
            if kind == "y": u, v = a, d
            elif kind == "n": u, v = (y, a) if grain == "v" else (a, y)
            else: u, v = (y, d) if grain == "v" else (d, y)
            out.append((u + ou, v + ov))
        return out
    F = [((a0, d0, y1), (a1, d0, y1), (a1, d1, y1), (a0, d1, y1)), (0, 1, 0), "y"], \
        [((a0, d0, y0), (a1, d0, y0), (a1, d1, y0), (a0, d1, y0)), (0, -1, 0), "y"], \
        [((a0, d1, y0), (a1, d1, y0), (a1, d1, y1), (a0, d1, y1)), (n[0], 0, n[1]), "n"], \
        [((a0, d0, y0), (a1, d0, y0), (a1, d0, y1), (a0, d0, y1)), (-n[0], 0, -n[1]), "n"], \
        [((a1, d0, y0), (a1, d1, y0), (a1, d1, y1), (a1, d0, y1)), (e[0], 0, e[1]), "e"], \
        [((a0, d0, y0), (a0, d1, y0), (a0, d1, y1), (a0, d0, y1)), (-e[0], 0, -e[1]), "e"]
    # shared corners per member (each member a closed box, so the bevel modifier rounds its edges; members are not welded together)
    idx = {}
    def vi(c):
        if c not in idx:
            idx[c] = len(pineuv.v); pineuv.v.append(pt(*c))
        return idx[c]
    for corners, toward, kind in F:
        pts = [pt(*c) for c in corners]; nn = [0.0, 0.0, 0.0]
        for (ax_, ay, az_), (bx, by, bz) in zip(pts, pts[1:] + pts[:1]):
            nn[0] += (ay - by) * (az_ + bz); nn[1] += (az_ - bz) * (ax_ + bx); nn[2] += (ax_ - bx) * (ay + by)
        cs, us = list(corners), uv(corners, kind)
        if sum(a * b for a, b in zip(nn, toward)) < 0:
            cs, us = cs[::-1], us[::-1]
        pineuv.f.append(tuple(vi(c) for c in cs)); pineuv.uv[len(pineuv.f) - 1] = us


def raised_field(o, e, n, a0, a1, y0, y1, d_back, d_base, d_top, bevel):
    """A door's panel: a thin board (d_back..d_base) and a raised field (d_base -> d_top over 'bevel' of sloped margin), grain up."""
    pbox(o, e, n, a0, a1, d_back, d_base, y0, y1, "v")
    k = _MEMBER[0]; ou, ov = (k * 0.377) % 1.1, (k * 0.613) % 1.1
    def pt(a, d, y): return (o[0] + a * e[0] + d * n[0], y, o[1] + a * e[1] + d * n[1])
    A = [(a0, y0), (a1, y0), (a1, y1), (a0, y1)]; B = [(a0 + bevel, y0 + bevel), (a1 - bevel, y0 + bevel), (a1 - bevel, y1 - bevel), (a0 + bevel, y1 - bevel)]
    for i in range(4):                                             # the four sloped margins (from the board's face up to the field)
        j = (i + 1) % 4; q = [(A[i], d_base + 0.0005), (A[j], d_base + 0.0005), (B[j], d_top), (B[i], d_top)]
        mid = ((A[i][0] + A[j][0]) / 2 - (a0 + a1) / 2, (A[i][1] + A[j][1]) / 2 - (y0 + y1) / 2)
        L = math.hypot(*mid) or 1.0; toward = (n[0] + mid[0] / L * e[0], 0.0, n[1] + mid[0] / L * e[1]); toward = (toward[0], mid[1] / L, toward[2])
        pineuv.face([pt(a, d, y) for (a, y), d in q], toward, [(y + ou, a + ov) for (a, y), d in q])
    pineuv.face([pt(a, d_top, y) for a, y in B], (n[0], 0, n[1]), [(y + ou, a + ov) for a, y in B])


def knob(o, e, n, a, y, base):
    """A turned wooden knob on a door face (film 2116: small round pine knobs), axis along n."""
    def circ(r, m=16): return [(r * math.cos(2 * math.pi * i / m), r * math.sin(2 * math.pi * i / m)) for i in range(m)]
    def P(d): return (o[0] + a * e[0] + d * n[0], y, o[1] + a * e[1] + d * n[1])
    pine.sweep([P(base - 0.002), P(base + 0.014)], circ(0.008))
    pine.sweep([P(base + 0.014), P(base + 0.018), P(base + 0.030), P(base + 0.034)], circ(0.019))
    pine.sweep([P(base + 0.034), P(base + 0.037)], circ(0.013))


def stacked_cupboard(poly, pull_in, o, e, n, L, top):
    prism(pine, pull_in(DT), TOE, top); prism(pine, pull_in(TR), 0.0, TOE)   # carcass (sides against the walls) and toe kick
    FW, CW, DW, gap = 0.045, 0.04, 0.055, 0.003       # face-frame stile, centre stile, door frame member, door gap
    db, df = -DT + 0.002, 0.012                       # door frame back and front (12 mm proud of the face frame: 6 mm read flat, build 1)
    half = L / 2; CROWN = 0.09; tops = [TOE + k * (top - CROWN - TOE) / 4 for k in range(5)]
    for si, (y0, y1) in enumerate(zip(tops, tops[1:])):
        for a0, a1 in ((0.0, FW), (L - FW, L), (half - CW / 2, half + CW / 2)):             # face-frame stiles
            pbox(o, e, n, a0, a1, -DT + 0.002, 0.0, y0, y1, "v")
        for a0, a1 in ((FW, half - CW / 2), (half + CW / 2, L - FW)):
            pbox(o, e, n, a0, a1, -DT + 0.002, 0.0, y0, y0 + FW, "h"); pbox(o, e, n, a0, a1, -DT + 0.002, 0.0, y1 - FW, y1, "h")   # rails
            b0, b1, c0, c1 = a0 + gap, a1 - gap, y0 + FW + gap, y1 - FW - gap               # the door in its opening
            pbox(o, e, n, b0, b0 + DW, db, df, c0, c1, "v"); pbox(o, e, n, b1 - DW, b1, db, df, c0, c1, "v")
            pbox(o, e, n, b0 + DW, b1 - DW, db, df, c0, c0 + DW, "h"); pbox(o, e, n, b0 + DW, b1 - DW, db, df, c1 - DW, c1, "h")
            raised_field(o, e, n, b0 + DW, b1 - DW, c0 + DW, c1 - DW, db, -0.004, 0.006, 0.035)   # field 6 mm under the frame face
            knob(o, e, n, b1 - 0.03 if a0 < half else b0 + 0.03, (c0 + c1) / 2, df)
        if si < 3:                                                                          # the lip between sections
            pbox(o, e, n, 0.004, L - 0.004, -0.003, 0.024, y1 - 0.018, y1 + 0.018, "h"); pbox(o, e, n, 0.008, L - 0.008, 0.024, 0.036, y1 - 0.010, y1 + 0.010, "h")
    y = top - CROWN                                                                         # moulded top: three steps out
    for d1, h0, h1 in ((0.02, 0.0, 0.035), (0.04, 0.03, 0.06), (0.06, 0.055, 0.09)):
        pbox(o, e, n, 0.004, L - 0.004, -0.003, d1, y + h0, y + h1, "h")   # ends 4 mm in from the stiles' (no coplanar end faces)


for t in K["talls"]:
    if t["name"] == "tower":
        x0, x1, z0, z1 = *t["x"], *t["z"]; top = t["top"]; o, e, n = front_frame(t["front"], z1)
        wood.box(x0, x1, TOE, top, z0, z1 - DT); wood.box(x0, x1, 0.0, TOE, z0, z1 - TR)
        ov0, ov1 = t["oven"]; g = GAP / 2
        for y0, y1 in ((TOE + GAP, 0.45 - g), (0.45 + g, ov0 - g)):
            raised(wood, o, e, n, x0 + g, x1 - g, y0, y1, 0.035); bail(o, e, n, (x0 + x1) / 2, (y0 + y1) / 2, 0.012)
        obox(black, o, e, n, x0 + 0.03, x1 - 0.03, -DT, 0.0, ov0 + g, ov1 - g)                   # wall oven: black frame (film 6044)
        obox(disp, o, e, n, x0 + 0.10, x1 - 0.10, 0.0, 0.012, ov0 + 0.10, ov1 - 0.22)           # its smoked glass door window
        obox(black, o, e, n, x0 + 0.08, x1 - 0.08, 0.0, 0.012, ov1 - 0.16, ov1 - 0.06)          # control panel
        obox(wood, o, e, n, x0 + g, x0 + 0.03, -DT, 0.0, ov0 + g, ov1 - g); obox(wood, o, e, n, x1 - 0.03, x1 - g, -DT, 0.0, ov0 + g, ov1 - g)
        hp = [(o[0] + a * e[0] + 0.035 * n[0], ov1 - 0.19, o[1] + a * e[1] + 0.035 * n[1]) for a in (x0 + 0.12, x1 - 0.12)]
        steel.sweep(hp, [(-0.008, -0.008), (0.008, -0.008), (0.008, 0.008), (-0.008, 0.008)])  # handle bar
        for a in (x0 + 0.12, x1 - 0.12):
            obox(steel, o, e, n, a - 0.008, a + 0.008, 0.012, 0.03, ov1 - 0.198, ov1 - 0.182)
        raised(wood, o, e, n, x0 + g, x1 - g, ov1 + g, top - g, 0.06); bar(o, e, n, x1 - 0.05, ov1 + 0.04, ov1 + 0.16, 0.0)
    else:                                                                                         # the corner pantry
        poly = [tuple(v) for v in t["poly"]]; i, j = t["front_edge"]; (ax, az), (bx_, bz) = poly[i], poly[j]
        L = math.hypot(bx_ - ax, bz - az); e = ((bx_ - ax) / L, (bz - az) / L)
        cx_, cz_ = sum(p[0] for p in poly) / len(poly), sum(p[1] for p in poly) / len(poly)
        n = (-e[1], e[0]) if (-e[1]) * (ax - cx_) + e[0] * (az - cz_) > 0 else (e[1], -e[0])
        def pull_in(r): return [p if k not in (i, j) else (p[0] - n[0] * r, p[1] - n[1] * r) for k, p in enumerate(poly)]
        stacked_cupboard(poly, pull_in, (ax, az), e, n, L, t["top"])

for st in K["seats"]:
    x0, x1, z0, z1 = *st["x"], *st["z"]; top = st["seat_top"]; cu = st["cushion"]; o, e, n = front_frame("+z", z1)
    wood.box(x0, x1, TOE, top - cu, z0, z1 - DT); wood.box(x0, x1, 0.0, TOE, z0, z1 - TR)
    raised(wood, o, e, n, x0 + GAP / 2, x1 - GAP / 2, TOE + GAP, top - cu, 0.05)
    cushion.box(x0 + 0.01, x1 - 0.01, top - cu, top, z0, z1 - 0.012)

for u in K["uppers"]:
    x0, x1, z0, z1 = *u["x"], *u["z"]; nx, nz = AX[u["front"]]; F = (x1 if nx > 0 else x0) if nx else (z1 if nz > 0 else z0)
    o, e, n = front_frame(u["front"], F); y0 = u.get("bottom", UB)
    if nx > 0: wood.box(x0, x1 - DT, y0, UT, z0, z1)
    elif nx < 0: wood.box(x0 + DT, x1, y0, UT, z0, z1)
    elif nz > 0: wood.box(x0, x1, y0, UT, z0, z1 - DT)
    else: wood.box(x0, x1, y0, UT, z0 + DT, z1)
    a0, a1 = (z0, z1) if nx else (x0, x1); nd = max(1, round((a1 - a0) / 0.42)); w = (a1 - a0) / nd; g = GAP / 2
    for k in range(nd):
        b0, b1 = a0 + k * w + g, a0 + (k + 1) * w - g
        raised(wood, o, e, n, b0, b1, y0 + g, UT - g, 0.06)
        bar(o, e, n, (b1 - 0.04) if k % 2 == 0 else (b0 + 0.04), y0 + 0.05, y0 + 0.15, 0.0)
    if UL and "bottom" not in u:   # the under-cabinet fluorescent strip (film 9812/10452/6042/10448): housing on the cabinet's
        # underside behind its front, the diffuser (emissive, KT_UnderLight) below it; faces >= 1 cm off the cabinet bottom
        d1 = -DT - UL["inset_front"]; d0 = d1 - UL["depth"]; s0, s1 = a0 + UL["end_gap"], a1 - UL["end_gap"]
        obox(housing, o, e, n, s0, s1, d0, d1, y0 - UL["housing_h"], y0)
        obox(glow, o, e, n, s0 + 0.01, s1 - 0.01, d0 + 0.008, d1 - 0.008, y0 - UL["housing_h"] - UL["diffuser_h"], y0 - UL["housing_h"])

for a in K["appliances"]:
    x0, x1, z0, z1 = *a["x"], *a["z"]
    if a["type"] == "fridge":
        o, e, n = front_frame(a["front"], z0); top = a["top"]                                  # front -z at z0
        black.box(x0 + 0.005, x1 - 0.005, 0.03, top, z0 + 0.03, z1)                             # body behind 3 cm doors
        black.box(x0 + 0.04, x1 - 0.04, 0.0, 0.03, z0 + 0.06, z1)                               # grille / feet recess
        split = x1 - 0.42 * (x1 - x0)                                                            # narrow freezer door at high x (the room's left; film 1050)
        for b0, b1 in ((x0 + 0.005, split - 0.003), (split + 0.003, x1 - 0.005)):
            obox(black, o, e, n, b0, b1, -0.03, 0.0, 0.03, top - 0.003)
        dx0, dx1 = split + 0.09, x1 - 0.08                                                          # dispenser on the freezer door
        obox(disp, o, e, n, dx0, dx1, 0.0, 0.012, 0.98, 1.40)
        obox(black, o, e, n, dx0 + 0.025, dx1 - 0.025, 0.012, 0.022, 1.02, 1.30)                 # its dark recess face
        for ac in (split - 0.04, split + 0.04):
            path = [(ac, 0.75 + 0.6 * k / 8, z0 - 0.006 - 0.025 * math.sin(math.pi * k / 8)) for k in range(9)]
            steel.sweep(path, [(-0.007, -0.007), (0.007, -0.007), (0.007, 0.007), (-0.007, 0.007)])
            for y in (0.75, 1.35):
                steel.box(ac - 0.008, ac + 0.008, y - 0.008, y + 0.008, z0 - 0.006, z0)
    elif a["type"] == "cooktop":
        black.box(x0, x1, CH - 0.06, CH + 0.006, z0, z1)                                        # black glass, 6 mm over the tile
        steel.box(x0 - 0.012, x1 + 0.012, CH, CH + 0.016, z0 - 0.012, z0)                       # steel trim front/back, on the tile
        steel.box(x0 - 0.012, x1 + 0.012, CH, CH + 0.016, z1, z1 + 0.012)
        for kx in range(4):                                                                     # knobs along the stool side
            cx_ = x0 + 0.10 + kx * (x1 - x0 - 0.2) / 3
            steel.lathe(cx_, z0 + 0.04, CH + 0.006, [(0, 0.016), (0.014, 0.016), (0.022, 0.012)], n=12)
    elif a["type"] == "sink":                                                                   # white double bowl, drop-in
        r, q = 0.022, 0.008
        for bx0, bx1, bz0, bz1 in ((x0 - r, x1 + r, z0 - r, z0 + q), (x0 - r, x1 + r, z1 - q, z1 + r), (x0 - r, x0 + q, z0 + q, z1 - q), (x1 - q, x1 + r, z0 + q, z1 - q)):
            sink.box(bx0, bx1, CH, CH + 0.012, bz0, bz1)                                        # rim on the tile, over the bowls' lips
        mid = (x0 + x1) / 2; depth = 0.20; yb = CH - depth
        for bx0, bx1, outer in ((x0 + q, mid - 0.012, x0 + q), (mid + 0.012, x1 - q, x1 - q)):
            Z0, Z1 = z0 + q, z1 - q
            sink.face([(bx0, yb, Z0), (bx1, yb, Z0), (bx1, yb, Z1), (bx0, yb, Z1)], (0, 1, 0))   # bowl floor (seen from above)
            sink.face([(bx0, yb, Z0), (bx1, yb, Z0), (bx1, CH, Z0), (bx0, CH, Z0)], (0, 0, 1))
            sink.face([(bx0, yb, Z1), (bx1, yb, Z1), (bx1, CH, Z1), (bx0, CH, Z1)], (0, 0, -1))
            sink.face([(outer, yb, Z0), (outer, yb, Z1), (outer, CH, Z1), (outer, CH, Z0)], (1 if outer == x0 + q else -1, 0, 0))
        sink.box(mid - 0.012, mid + 0.012, yb, CH + 0.012, z0, z1)                              # divider (the bowls' inner walls)
        # brass gooseneck faucet behind the bowls (film 6902), clear of the backsplash
        fz = z1 + 0.045
        brass.lathe(mid, fz, CH, [(0, 0.022), (0.02, 0.022), (0.03, 0.012), (0.10, 0.012)], n=14)
        brass.sweep([(mid, CH + 0.10, fz), (mid, CH + 0.30, fz), (mid, CH + 0.36, fz - 0.08), (mid, CH + 0.30, fz - 0.17), (mid, CH + 0.24, fz - 0.19)],
                    [(-0.009, -0.009), (0.009, -0.009), (0.009, 0.009), (-0.009, 0.009)])
        for s in (-1, 1):
            brass.lathe(mid + s * 0.13, fz, CH, [(0, 0.02), (0.02, 0.02), (0.03, 0.01), (0.07, 0.01), (0.075, 0.02), (0.085, 0.02)], n=12)

bpy.ops.wm.read_factory_settings(use_empty=True)
M = {"KT_Wood": material("KT_Wood", (0.36, 0.11, 0.12), 0.45), "KT_Tile": material("KT_Tile", (0.19, 0.19, 0.23), 0.1),
     "KT_Edge": material("KT_Edge", (0.16, 0.38, 0.59), 0.1), "KT_Grout": material("KT_Grout", (0.8, 0.78, 0.74), 0.8),
     "KT_Brass": material("KT_Brass", (0.75, 0.56, 0.25), 0.3), "KT_Black": material("KT_Black", (0.02, 0.02, 0.02), 0.15),
     "KT_Steel": material("KT_Steel", (0.6, 0.6, 0.6), 0.3), "KT_Sink": material("KT_Sink", (0.92, 0.91, 0.88), 0.15),
     "KT_Cushion": material("KT_Cushion", (0.55, 0.06, 0.08), 0.9), "KT_Housing": material("KT_Housing", (0.85, 0.84, 0.8), 0.4),
     "KT_UnderLight": material("KT_UnderLight", (0.95, 0.95, 0.92), 0.5, (1.0, 0.93, 0.8), 5.0),
     "KT_Pine": material("KT_Pine", (0.72, 0.48, 0.25), 0.4), "KT_UVPine": material("KT_UVPine", (0.72, 0.48, 0.25), 0.4), "KT_Dispenser": material("KT_Dispenser", (0.12, 0.12, 0.13), 0.3)}
coll = bpy.context.scene.collection
root = bpy.data.objects.new("KitchenCabinets_HiFi", None); coll.objects.link(root)
parts = (wood, tile, edge, grout, brass, black, steel, sink, cushion, housing, glow, pine, disp, pineuv)
for p in parts:
    if p.f:
        ob = p.build(coll, M); ob.parent = root
        if p is pineuv:   # artist-pipeline: 2.5 mm bevels on every member's edges, weighted normals (flat faces stay flat)
            bv = ob.modifiers.new("bevel", "BEVEL"); bv.width = 0.0025; bv.segments = 2; bv.limit_method = "ANGLE"; bv.angle_limit = math.radians(30)
            bv.harden_normals = True
            ob.modifiers.new("wn", "WEIGHTED_NORMAL").keep_sharp = True
OUT.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(OUT), export_format="GLB", export_yup=True, export_apply=True, export_texcoords=True, export_tangents=True)
print("wrote", OUT, {p.name: len(p.f) for p in parts})
