"""Reconcile measured spaces into one clean, buildable floor spec (docs/RECONCILIATION.md, step 2).

Input: a traced, calibrated floor plan (measurements/overhead/<floor>-trace.plan.json), its doors/topology file, and
which spaces are SfM-measured anchors. Moves measurements as little as possible and logs every move:
  1. square: each wall becomes exactly axis-aligned (endpoints averaged)
  2. align: near-collinear walls of neighbouring spaces share one line (anchors weigh 5x, so measured rooms barely move)
  3. walls: thickness between facing spaces; too thin / too thick is flagged, not fixed
  4. doors: measured spans where available, else centred on the shared wall (flagged as topology-placed)
  5. rules: adult body passes every door and hall
Output: spec/house_spec.json (the only thing the Unity generator reads) and spec/<floor>-changes.md.
--measured: skip wall thinning and write spec/house_spec.measured.json instead, the house exactly as measured, so the
render comparison can separate measurement error from the deliberate gameplay change (thinner walls, bigger rooms).
usage: uv run --with numpy python tools/house/reconcile.py [--measured]
"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
FLOOR = sys.argv[sys.argv.index("--floor") + 1] if "--floor" in sys.argv else "upstairs"
TRACE = ROOT / f"measurements/overhead/{FLOOR}-trace.json"
PLAN = ROOT / f"measurements/overhead/{FLOOR}-trace.plan.json"
DOORS = ROOT / f"measurements/overhead/{FLOOR}-doors.json"
ANCHORS = {"parents_bedroom": "measurements/rooms/parents.json", "kevin_jeff_room": "measurements/rooms/kevin.json",
           "buzz_room": "measurements/rooms/buzz.json"} if FLOOR == "upstairs" else {}
ANCHOR_WEIGHT = 5.0
ORIGIN = (-0.704, -4.578)   # upstairs plan metres of the spec origin (was the min corner of all spaces)
ALIGN_TOL = 0.12      # m: walls closer than this (and near each other along the line) become one line
ALIGN_REACH = 1.0     # m: ...if their extents are within this distance along the line
MAX_SPREAD = 0.20     # m: a cluster wider than this is a conflict, left unsnapped
WALL_MIN, WALL_MAX = 0.08, 0.50   # m: plausible wall thickness between facing spaces
FACE_MAX = 0.80       # m: facing edges farther apart than this are not one wall
DOOR_W, DOOR_H = 0.762, 2.032     # 30 x 80 in
ADULT = {"capsule_diameter": 0.55, "height": 1.85, "min_hall": 0.90}
# Ceiling heights, measured Oct 13 on door walls (wall height / door height x 80 in, door_scale.py):
# parents 2.42 m and Kevin 2.30-2.33 m to the crown's lower edge (+~0.08 m crown), hall attic leg 2.29 m to the ceiling.
CEILINGS = {"default": 2.40, "parents_bedroom": 2.50, "parents_bath": 2.50, "hall_corridor_south": 2.29} if FLOOR == "upstairs" else \
    {"default": 2.438, "foyer": 2.82, "back_hall": 2.155, "rear_passage": 2.155, "under_landing": 2.155}  # under the landing: 1.5 cm below its underside (2.17, film; coplanar flickered). Was back_hall 2.25 under Marina's 2.264
                         # back_hall Oct 15: just under the landing (underside 2.264 m; a coplanar ceiling flickered, seam check), unknown beyond. foyer Oct 14 (2.82 = the most under the 0.2 m upper-floor slab): front ceiling 2.92 m in the clip A solve, 1.40 x a door in the film
                        # (then-foyer.png), 1.51 x the vestibule opening in Marina 205 s (film_ratios.py). Ground: 8 ft standard, inside the measured living 2.44 / dining 2.42 m (tools/house/ground_ceiling.py, Oct 14). Was 2.32, the
                        # landing balustrade's base in the stair clip, misread as the foyer ceiling. Kitchen (beams) unmeasured
# Which way each stairwell opening leads (sources): the main stair goes DOWN to the foyer (measured, stairs.json); the
# attic stair goes UP from this floor (Part 2 attic segment: the CG walk climbs it from the hall-end door). A "down"
# opening has no floor and cuts the ceiling below; an "up" opening has a floor and no ceiling (attic not built).
OPENS = {"main_stair_opening": "down", "attic_stair": "up"}
RAIL_T = 0.06         # m: a balustrade between a hall and a stairwell, not a wall (hall-s1 wall check: hall reaches the rail)
WALL_T = 0.14         # m: interior wall thickness built (5.5 in). User decision Oct 13: thin Marina's thick walls,
                      # keep each wall's centreline, rooms take the freed space. Exterior walls are untouched.


def edges_of(poly):
    """Rectilinear edges: (const_axis, coord, lo, hi). const_axis 0 = constant plan-x (runs along y)."""
    out = []
    for p, q in zip(poly, np.roll(poly, -1, 0)):
        d = q - p
        ax = 0 if abs(d[0]) < abs(d[1]) else 1
        out.append([ax, (p[ax] + q[ax]) / 2, min(p[1 - ax], q[1 - ax]), max(p[1 - ax], q[1 - ax])])
    for a, b in zip(out, out[1:] + out[:1]):
        assert a[0] != b[0], "trace polygons must alternate wall directions"
    return out


def rebuild(edges):
    """Vertex i = corner where edge i-1 meets edge i."""
    pts = []
    for prev, cur in zip(edges[-1:] + edges[:-1], edges):
        v = np.zeros(2)
        v[prev[0]], v[cur[0]] = prev[1], cur[1]
        pts.append(v)
    return np.array(pts)


def area(p):
    x, y = p.T
    return 0.5 * abs(x @ np.roll(y, -1) - y @ np.roll(x, -1))


def outward_sign(poly, e):
    """+1 if the space lies on the low-coordinate side of edge e (outward normal points to +coord), else -1."""
    ax, c, lo, hi = e
    mid = np.zeros(2); mid[ax] = c; mid[1 - ax] = (lo + hi) / 2
    probe = mid.copy(); probe[ax] -= 0.05
    return 1 if inside(poly, probe) else -1


def inside(poly, pt):
    x, y = pt; n = len(poly); c = False
    for i in range(n):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


def align(spaces, weights):
    """Cluster near-collinear edges across spaces; return per-edge new coordinate and the cluster log."""
    flat = [(s, i, e) for s, es in spaces.items() for i, e in enumerate(es)]
    parent = list(range(len(flat)))
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i
    for i, (si, _, a) in enumerate(flat):
        for j in range(i + 1, len(flat)):
            sj, _, b = flat[j]
            if a[0] == b[0] and abs(a[1] - b[1]) <= ALIGN_TOL and si != sj:
                gap = max(a[2], b[2]) - min(a[3], b[3])
                if gap <= ALIGN_REACH:
                    parent[find(i)] = find(j)
    groups = {}
    for i in range(len(flat)):
        groups.setdefault(find(i), []).append(i)
    new, log = {}, []
    for g in groups.values():
        cs = np.array([flat[i][2][1] for i in g])
        if len(g) == 1:
            new[g[0]] = cs[0]; continue
        w = np.array([(flat[i][2][3] - flat[i][2][2]) * weights[flat[i][0]] for i in g])
        if np.ptp(cs) > MAX_SPREAD:
            for i in g:
                new[i] = flat[i][2][1]
            log.append(("conflict", g, cs, None)); continue
        c = float(w @ cs / w.sum())
        for i in g:
            new[i] = c
        log.append(("aligned", g, cs, c))
    return flat, new, log


def facing_pairs(polys, edges):
    """Walls between spaces: facing edges (opposite outward normals) with overlap, gap = wall thickness."""
    out = []
    names = list(edges)
    for ia, a in enumerate(names):
        for b in names[ia + 1:]:
            for ia_, ea in enumerate(edges[a]):
                sa = outward_sign(polys[a], ea)
                for ib_, eb in enumerate(edges[b]):
                    if ea[0] != eb[0]:
                        continue
                    sb = outward_sign(polys[b], eb)
                    if sa != -sb:
                        continue
                    gap = (eb[1] - ea[1]) * sa
                    lo, hi = max(ea[2], eb[2]), min(ea[3], eb[3])
                    if -0.05 < gap <= FACE_MAX and hi - lo > 0.3:
                        out.append({"a": a, "b": b, "ia": ia_, "ib": ib_, "sa": sa, "axis": ea[0], "coord_a": ea[1], "coord_b": eb[1], "gap": gap, "lo": lo, "hi": hi})
    return out


MEASURED = "--measured" in sys.argv
STAIR = ROOT / "measurements/rooms/stairs.json"
# --variant <name> --risers <landing>+<total>: a comparison build (spec/house_spec[.ground].<name>.json) with the stair's riser
# counts changed and the rise refitted to --floor-to-floor; measurements untouched (tools/house/stair_variants.py)
VARIANT = sys.argv[sys.argv.index("--variant") + 1] if "--variant" in sys.argv else None


def wall_of(p):
    return (p["coord_a"] + p["coord_b"]) / 2


def door_on(p, doors):
    """The topology door on facing pair p. Two spaces can share several walls (the stairwell and the hall share two
    rails and the stair head), so a door may name its wall by "wall_axis" (x/y = the plan axis held constant) and
    "near" (that coordinate); the nearest such door wins. A door without them sits on the pair's longest wall."""
    key = tuple(sorted((p["a"], p["b"])))
    cands = [d for d in doors if tuple(sorted((d["a"], d["b"]))) == key]
    axis = "x" if p["axis"] == 0 else "y"
    named = [d for d in cands if d.get("wall_axis") == axis]
    if named:
        return min(named, key=lambda d: abs(d["near"] - wall_of(p)))
    return next((d for d in cands if "wall_axis" not in d), None)


def service_stair_spec(final, o):
    """The service (back) stair, measured (Oct 15 night; changes/2026-10-15-back-stair-measured.json, -winders.json; joint_fit.py track on
    Marina 914-945 s, COLMAP cameras scaled by her fixed camera height; labels/backstair-marina.json). From the breakfast area: 2 straight
    steps rising toward the wall, 3 winders turning 90 deg around the tall post (x 1.48, on the open side), then the flight up along the
    wall toward the rear (going 0.30, rise 0.183: the tracked nosings sit at risers 6-8) to the ceiling. The short newel stands on the
    winders' doorway-side edge (x 2.64) with a raking balustrade from it to a post at the wall (Marina 1073.5/1074.5 s); the winders
    are the wedges by the tall post in 933 s and the two diagonals in the 812 s overhead. One raking handrail from the tall post up the
    flight, 2 balusters a tread. Under the flight the papered spandrel runs down to the floor; above the treads the balustrade runs to
    the ceiling. Kevin's basement door (x -1.284..-0.445, 0.84 m, 2.032 m) sits in a short wall 0.30 m proud of the open side.
    AUTHORED (DEVIATIONS 30): the straight steps' square fronts (film 912: rounded, flared) and their count (812 s + film; behind the
    table in every eye-level frame); winder count from the overhead's two diagonals."""
    P = np.c_[final["back_stair"][:, 1] - o[1], final["back_stair"][:, 0] - o[0]]
    x0, z0, z1 = P[:, 0].min(), P[:, 1].min(), P[:, 1].max()
    r, g, NS, NW = 0.183, 0.30, 2, 3
    NOSE = 0.02                                             # a tread overhangs its step by 2 cm on every side (finish; a flush tread
                                                            # shares faces with its step and flickers: z-fight gate, Oct 16)
    def grow(poly, d):                                      # convex outline offset outward by d (mitred corners)
        P = [np.asarray(q, float) for q in poly]; A2 = sum(P[i][0] * P[i - 1][1] - P[i - 1][0] * P[i][1] for i in range(len(P)))
        L = []
        for a, b in zip(P, P[1:] + P[:1]):
            t = (b - a) / np.linalg.norm(b - a); nrm = np.array([t[1], -t[0]]) * (1 if A2 < 0 else -1)
            L.append((a + nrm * d, t))
        out = []
        for (p1, t1), (p2, t2) in zip(L[-1:] + L[:-1], L):
            s_ = np.linalg.solve(np.array([t1, -t2]).T, p2 - p1); out.append(p1 + t1 * s_[0])
        return out
    XL, XN = 1.48, 2.64                                     # the tall post (pivot, inner corner) and the short newel's x (measured)
    ceil = CEILINGS.get("back_stair", CEILINGS["default"])
    B = []
    rd = lambda v: round(float(v), 3)
    box = lambda name, kind, xa, xb, ya, yb, za, zb, **kw: B.append({"name": name, "kind": kind, "x": [rd(min(xa, xb)), rd(max(xa, xb))],
                                                                   "y": [rd(ya), rd(yb)], "z": [rd(min(za, zb)), rd(max(za, zb))], **kw})
    def prism(name, kind, poly, ya, yb):
        xs, zs = [q[0] for q in poly], [q[1] for q in poly]
        B.append({"name": name, "kind": kind, "x": [rd(min(xs)), rd(max(xs))], "y": [rd(ya), rd(yb)], "z": [rd(min(zs)), rd(max(zs))],
                  "poly": [[rd(q[0]), rd(q[1])] for q in poly]})
    for k in range(1, NS + 1):                              # straight steps in the breakfast area, rising +z toward the winders
        za, zb, h = z0 - (NS - k + 1) * g, z0 - (NS - k) * g, k * r
        box(f"service_foot{k:02d}", "step", XL, XN, 0.0, h, za, zb)
        box(f"service_foot{k:02d}_tread", "tread", XL - NOSE, XN + NOSE, h - 0.025, h + 0.005, za - NOSE, zb + NOSE)
        box(f"service_foot{k:02d}_riser", "riser", XL, XN, h - r, h - 0.025, za - 0.01, za)
    piv = np.array([XL, z0]); corner = np.degrees(np.arctan2(z1 - z0, XN - XL))
    def edge(th):                                           # pivot ray at th (0 = +x along the open side, 90 = +z) to the square's far side
        d = np.array([np.cos(np.radians(th)), np.sin(np.radians(th))])
        t = min((XN - XL) / d[0] if d[0] > 1e-9 else 1e9, (z1 - z0) / d[1] if d[1] > 1e-9 else 1e9)
        return piv + t * d
    ang = np.linspace(0, 90, NW + 1)
    for i in range(NW):                                     # winders: wedges around the tall post
        h = (NS + 1 + i) * r
        poly = [piv, edge(ang[i])] + ([np.array([XN, z1])] if ang[i] < corner < ang[i + 1] else []) + [edge(ang[i + 1])]
        prism(f"service_winder{i + 1}", "step", poly, 0.0, h)
        e = edge(ang[i]); n = np.array([np.sin(np.radians(ang[i])), -np.cos(np.radians(ang[i]))]) * 0.01   # riser on its front edge
        prism(f"service_winder{i + 1}_tread", "tread", grow(poly, NOSE), h - 0.025, h + 0.005)
        prism(f"service_winder{i + 1}_riser", "riser", [piv, e, e + n, piv + n], h - r, h - 0.025)
    hf = lambda x: (NS + NW + 1) * r + (XL - x) / g * r     # flight nosing line
    k = 0
    FTF = json.loads((ROOT / "spec/house_spec.json").read_text())["stair"]["floor_to_floor_m"]
    TOP = round(FTF - 0.20 - 0.015, 3)                      # the recess over the flight: 1.5 cm under the upstairs floor plate
    while (NS + NW + 1 + k) * r <= TOP - 0.15 and XL - (k + 1) * g >= x0 - 1e-6:   # the flight: rising -x along the wall, into the recess
        k += 1; xa, xb = XL - k * g, XL - (k - 1) * g; hk = (NS + NW + k) * r
        box(f"service_step{k:02d}", "step", xa, xb, 0.0, hk, z0, z1)
        box(f"service_step{k:02d}_tread", "tread", xa - NOSE, xb + NOSE, hk - 0.025, hk + 0.005, z0 - NOSE, z1 + NOSE)
        box(f"service_step{k:02d}_riser", "riser", xb, xb + 0.01, hk - r, hk - 0.025, z0, z1)
        for f in (0.25, 0.75):                              # 2 white balusters a tread, up to the raking rail
            c = xa + f * g
            if hk < TOP - 0.10:                             # ending in the recess's top where the rail would rise past it
                box(f"service_step{k:02d}_spindle{f}", "spindle", c - 0.02, c + 0.02, hk, min(hf(c) + 0.84, TOP - 0.005), z0 + 0.01, z0 + 0.05)
    xt = XL - k * g
    rail_lo = hf(XL) + 0.84                                 # one raking handrail from the tall post up into the recess's top
    xr = max(xt, XL - (TOP - 0.005 - 0.90 - hf(XL)) / r * g)
    box("service_handrail", "newel", xr, XL, (hf(XL) + hf(xr)) / 2 + 0.84, (hf(XL) + hf(xr)) / 2 + 0.90, z0, z0 + 0.06, rise_x=rd(hf(xr) - hf(XL)))
    # Kevin's basement door in a short wall 0.30 m proud of the open side (measured), from the corner to past its casing
    DX0, DX1, DZ = -1.284, -0.445, z0 - 0.30
    for b in B:
        if b["kind"] == "step" and b["name"].startswith("service_step") and b["x"][0] < DX1 + 0.2:
            b["y"][0] = rd(b["y"][1] - 0.22)                # over the door: the flight is a slab (headroom under it)
    for b in [b for b in B if b["kind"] == "step" and b["name"].startswith("service_step") and b["y"][0] > 0]:
        box(b["name"] + "_spandrel", "spandrel", b["x"][0], b["x"][1], 0.0, b["y"][0], z0, z0 + 0.03)   # papered, floor to the slab only
    WX1 = XL - round((XL - (DX1 + 0.15)) / g) * g           # the door's wall ends on a step edge past its casing, then returns
    box("basement_wall_front_l", "spandrel", x0, DX0 - 0.07, 0.0, ceil, DZ - 0.03, DZ)
    box("basement_wall_front_r", "spandrel", DX1 + 0.07, WX1, 0.0, ceil, DZ - 0.03, DZ)
    box("basement_wall_head", "spandrel", DX0 - 0.07, DX1 + 0.07, 2.10, ceil, DZ - 0.03, DZ)
    box("basement_wall_return", "spandrel", WX1 - g, WX1, 0.0, ceil, DZ, z0)   # one going deep: its faces on the step edges (no ledge)
    box("basement_PropDoor", "door_prop", DX0, DX1, 0.0, 2.032, DZ - 0.035, DZ)
    for nm, xa, xb in (("basement_Casing_l", DX0 - 0.07, DX0), ("basement_Casing_r", DX1, DX1 + 0.07)):
        box(nm, "casing", xa, xb, 0.0, 2.10, DZ - 0.05, DZ - 0.03)
    box("basement_Casing_head", "casing", DX0 - 0.07, DX1 + 0.07, 2.032, 2.10, DZ - 0.05, DZ - 0.03)
    box("basement_PropDoor_knob", "newel", DX1 - 0.09, DX1 - 0.05, 0.92, 0.96, DZ - 0.075, DZ - 0.035)
    for j in range(1, k + 1):                               # white cut stringer along the open side, not inside the return wall
        xa, xb = XL - j * g, XL - (j - 1) * g; hj = (NS + NW + j) * r
        if xa >= WX1 - g - 1e-6 and xb <= WX1 + 1e-6:
            continue
        box(f"service_stringer{j:02d}", "stringer", xa, xb, hj - r - 0.12, hj - 0.025, z0 - 0.02, z0)
    # posts (measured x): short newel on the winders' doorway-side edge, tall post at the pivot, a post at the wall; raking rail between
    ZN = 6.88; hn, hw = (NS + 1) * r, (NS + 2) * r
    box("service_newel", "newel", XN - 0.05, XN + 0.05, 0.0, hn + 0.95, ZN - 0.05, ZN + 0.05)
    box("service_newel_post", "newel", XL - 0.05, XL + 0.05, 0.0, hf(XL) + 1.05, z0 - NOSE - 0.01, z0 + 0.09 - NOSE)   # 1 cm proud of the stringer face
    box("service_wall_post", "newel", 2.45, 2.55, 0.0, hw + 1.0, z1 - 0.1, z1)
    box("service_winder_rail", "newel", XN - 0.06, XN, (hn + hw) / 2 + 0.84, (hn + hw) / 2 + 0.90, ZN, z1 - 0.1, rise_z=rd(hw - hn))
    for i in range(1, 5):
        c = ZN + i * (z1 - 0.1 - ZN) / 5; hc = hn + (hw - hn) * (c - ZN) / (z1 - 0.1 - ZN)
        box(f"service_winder_spindle{i}", "spindle", XN - 0.05, XN - 0.01, hn, hc + 0.83, c - 0.02, c + 0.02)   # ends under the rail (clash gate)
    # the flight rises through an opening in the ceiling (Marina 918/930 s) into a recess lined in the kitchen paper, its top just
    # under the upstairs floor: it reads as going up and touches no upstairs room (user, Oct 16: "close it off neatly"; DEVIATIONS 40)
    OZ0 = z0 - 0.05                                         # the opening clears the balustrade on the open side
    OPEN = {"x": [rd(x0), rd(XL)], "z": [rd(OZ0), rd(z1)], "top": TOP}
    box("service_well_open_side", "spandrel", x0, XL, ceil, TOP, OZ0, OZ0 + 0.02)   # linings stand inside the opening
    box("service_well_wall_side", "spandrel", x0, XL, ceil, TOP, z1 - 0.02, z1)
    box("service_well_low_end", "spandrel", XL - 0.02, XL, ceil, TOP, OZ0 + 0.02, z1 - 0.02)
    box("service_well_high_end", "spandrel", x0, x0 + 0.02, ceil, TOP, OZ0 + 0.02, z1 - 0.02)
    box("service_well_top", "spandrel", x0 + 0.02, XL - 0.02, TOP - 0.01, TOP, OZ0 + 0.02, z1 - 0.02)
    box("service_well_Casing_side", "casing", x0, XL + 0.05, ceil - 0.02, ceil, OZ0 - 0.05, OZ0 + 0.02)   # casing on the ceiling
    box("service_well_Casing_end", "casing", XL - 0.02, XL + 0.05, ceil - 0.02, ceil, OZ0 + 0.02, z1)
    ks = next(j for j in range(1, k + 1) if (NS + NW + j) * r + 1.20 > TOP)   # the first step Kevin (1.20 m) can't stand on
    xs_ = XL - (ks - 1) * g                                 # its front edge: an invisible stop across the flight
    box("service_stop", "stop", xs_ - 0.02, xs_, (NS + NW + ks - 1) * r, TOP, OZ0, z1)
    w1 = np.mean([piv, edge(ang[0]), edge(ang[1])], axis=0)   # walk test: up the straight steps onto the first winder (above it an
    # the start stands past the breakfast table's end (spec/dressing/kitchen.json, Oct 16): the table's far edge is 0.54 m from the
    # first riser, less than the adult capsule, so the walk now comes in from the newel side (it started under the table at x 2.06)
    # then to a floor point just clear of the first riser (adult capsule 0.275 m), from which the climb runs as before
    path = [[XN - 0.08, 0.0, z0 - NS * g - 0.66], [XN - 0.08, 0.0, z0 - NS * g - 0.277], [w1[0], (NS + 1) * r, w1[1]]]   # adult meets the 2.44 m ceiling from winder 2 on)
    return {"rise_m": r, "going_m": g, "risers": NS + NW + k, "boxes": B, "walk_path": [[rd(v) for v in q] for q in path], "ceiling_openings": [OPEN],
            "authored": f"measured: {NS} straight steps + {NW} winders around the tall post (x {XL}), {k} flight steps (going {g}, rise {r}) to x {xt:.2f}; straight steps' fronts square (film: rounded)"}


ATTIC = ROOT / "measurements/rooms/attic.json"


def attic_stair_spec(final, o, ceil):
    """The attic stair and the attic over it (Oct 18 2026, TRIAL; changes/2026-10-18-attic-shell.json, DEVIATIONS 21 and 90).
    Stair: a straight flight rising away from the hall-end door (film, f_00015-24 of sfm-work/attic) across the overhead's well, at the
    attic floor (measurements/rooms/attic.json: floor 2.670 = 15 main-stair rises, over the upper ceilings) in 14 risers of 0.1907
    with the old 0.42 m run-in (a 1.85 m body clears the door head's casing before step 1) and a 0.178 going (47 deg).
    Attic: Marina's room (5.20 x 8.50, 1.25 m knee walls) centred on the well across the house (the well sits on the house's centre
    line, under the ridge) and running back from the house's end wall over the upper rooms; the flight arrives at that end wall and you
    step off sideways (front side), the house's chimney (the living room's flue, rear wall z 13.82) stands at the rear knee wall, the
    zipline dormer is in the rear slope centred on the landing window (film 9435). Boxes here are the walk/envelope layer (renderers
    hidden by SpecGreybox.Attic, which places the look: tools/house/hifi_attic.py)."""
    A = {k: v["value"] for k, v in json.loads(ATTIC.read_text())["measured"].items()}
    n, yf = A["risers"], A["floor_y"]; r = yf / n           # 14 x 0.1907 (attic.json risers)
    P = np.c_[final["attic_stair"][:, 1] - o[1], final["attic_stair"][:, 0] - o[0]]
    x0, x1, z0, z1 = P[:, 0].min(), P[:, 0].max(), P[:, 1].min(), P[:, 1].max()
    s0 = 0.42                                  # run-in inside the door: a 1.85 m body clears the door head's casing before step 1
    g = (z1 - z0 - s0) / (n - 1)
    t = 0.14
    B = []
    rd = lambda v: round(float(v), 3)
    box = lambda name, kind, xa, xb, ya, yb, za, zb, **kw: B.append({"name": name, "kind": kind, "x": [rd(xa), rd(xb)], "y": [rd(ya), rd(yb)], "z": [rd(za), rd(zb)], **kw})
    for k in range(1, n):
        box(f"attic_step{k:02d}", "step", x0, x1, 0.0, k * r, z0 + s0 + (k - 1) * g, z0 + s0 + k * g)
    for name, xa, xb, za, zb in (("attic_wall_w", x0 - t, x0, z0 - t, z1 + t), ("attic_wall_e", x1, x1 + t, z0 - t, z1 + t),
                                 ("attic_wall_door", x0, x1, z0 - t, z0), ("attic_wall_end", x0, x1, z1, z1 + t)):
        box(name, "wall", xa, xb, ceil, yf, za, zb)       # the well's framing up to the attic floor (the builder stops them at its ceiling)
    # ---- the attic: room, floor, knee walls, end walls, lid (a box envelope round the sloped look)
    xc, W, L, kh, tp = (x0 + x1) / 2, A["room_w"], A["room_l"], A["knee_h"], np.tan(np.radians(A["pitch_deg"]))
    ax0, ax1, az1 = xc - W / 2, xc + W / 2, z1
    az0, ridge = az1 - L, yf + kh + W / 2 * tp
    top = ridge + 0.15                                   # over the ridge board and the roof boards
    dz, dsill, (dw, dh) = A["dormer_z"], A["dormer_sill_h"], A["dormer_opening"]
    di = A["dormer_body_w"] / 2 - t                      # cheeks' inner faces
    dface = ax0 - (kh - (dsill - 0.12)) / tp            # the window wall's inner face: where the roof's underside is 0.12 under the sill
    room = [[ax0, az0], [ax1, az0], [ax1, az1], [ax0, az1], [ax0, dz + di], [dface, dz + di], [dface, dz - di], [ax0, dz - di]]
    box("attic_room", "room", ax0, ax1, yf, ridge, az0, az1, poly=[[rd(a), rd(b)] for a, b in room])
    box("attic_floor_rear", "floor", ax0 - t, x0 - t, yf - 0.12, yf, az0 - t, az1 + t)
    box("attic_floor_front", "floor", x1 + t, ax1 + t, yf - 0.12, yf, az0 - t, az1 + t)
    box("attic_floor_mid", "floor", x0 - t, x1 + t, yf - 0.12, yf, az0 - t, z0 - t)
    box("attic_floor_dormer", "floor", dface - t, ax0 - t, yf - 0.12, yf, dz - di - t, dz + di + t)
    box("attic_knee_front", "wall", ax1, ax1 + t, yf, top, az0 - t, az1 + t)
    box("attic_knee_rear_a", "wall", ax0 - t, ax0, yf, top, az0 - t, dz - di - t)
    box("attic_knee_rear_b", "wall", ax0 - t, ax0, yf, top, dz + di + t, az1 + t)
    box("attic_gable_end", "wall", ax0, ax1, yf, top, az1, az1 + t)
    box("attic_gable_back", "wall", ax0, ax1, yf, top, az0 - t, az0)
    box("attic_dormer_cheek_a", "wall", dface - t, ax0, yf, top, dz - di - t, dz - di)
    box("attic_dormer_cheek_b", "wall", dface - t, ax0, yf, top, dz + di, dz + di + t)
    ys, yh = yf + dsill, yf + dsill + dh
    box("attic_dormer_apron", "wall", dface - t, dface, yf, ys, dz - di, dz + di)
    box("attic_dormer_head", "wall", dface - t, dface, yh, top, dz - di, dz + di)
    box("attic_dormer_jamb_a", "wall", dface - t, dface, ys, yh, dz - di, dz - dw / 2)
    box("attic_dormer_jamb_b", "wall", dface - t, dface, ys, yh, dz + dw / 2, dz + di)
    box("attic_dormer_opening", "opening", dface - t, dface, ys, yh, dz - dw / 2, dz + dw / 2)   # cut out of the envelope; no collider (the zipline)
    box("attic_lid", "ceiling", ax0 - t if dface > ax0 else dface - t, ax1 + t, top, top + 0.1, az0 - t, az1 + t)
    # balustrade round the well (colliders; the look is the model's): rear side, the end over the flight's foot, the front side open
    # for its last 0.95 m (the step-off: the flight meets the end wall)
    rh, rt, ro = 0.90, 0.06, 0.05
    gap = z1 - 0.95
    box("attic_rail_rear", "rail", x0 - ro - rt / 2, x0 - ro + rt / 2, yf, yf + rh, z0 - ro - rt / 2, z1)
    box("attic_rail_foot", "rail", x0 - ro - rt / 2, x1 + ro + rt / 2, yf, yf + rh, z0 - ro - rt / 2, z0 - ro + rt / 2)
    box("attic_rail_front", "rail", x1 + ro - rt / 2, x1 + ro + rt / 2, yf, yf + rh, z0 - ro - rt / 2, gap)
    # the sofa bed (film 1403-1447: against the balustrade's end, its head at the chimney; placeholder walk box)
    bed = {"x": [rd(xc - 2.0065), rd(xc - 0.0065)], "z": [rd(z0 - ro - rt / 2 - 0.03 - 2.10), rd(z0 - ro - rt / 2 - 0.03)], "top": 0.45, "back": 0.85, "back_d": 0.30}
    box("attic_bed", "furniture", bed["x"][0], bed["x"][1], yf, yf + bed["top"], bed["z"][0], bed["z"][1])
    box("attic_bed_back", "furniture", bed["x"][0], bed["x"][1], yf + bed["top"], yf + bed["back"], bed["z"][0], bed["z"][0] + bed["back_d"])
    chim = {"x": [rd(ax0 + 0.01), rd(ax0 + 0.66)], "z": [13.32, 14.32]}   # the living-room flue (spec/dressing/living.json fireplace z 13.82)
    box("attic_chimney", "furniture", chim["x"][0], chim["x"][1], yf, yf + kh, chim["z"][0], chim["z"][1])
    stove = {"x": [rd(chim["x"][1] + 0.04), rd(chim["x"][1] + 0.59)], "z": [13.58, 14.08], "h": 0.75}
    box("attic_stove", "furniture", stove["x"][0], stove["x"][1], yf, yf + stove["h"], stove["z"][0], stove["z"][1])
    xm = (x0 + x1) / 2
    path = [[xm, 0.0, z0 - 0.6], [xm, (n - 1) * r, z1 - 0.20], [x1 - 0.08, yf, z1 - 0.20], [x1 + 0.62, yf, z1 - 0.30], [x1 + 0.62, yf, az0 + 3.1], [ax0 + 1.45, yf, dz + 0.75]]
    attic = {"x": [rd(ax0), rd(ax1)], "z": [rd(az0), rd(az1)], "floor_y": rd(yf), "ridge_y": rd(ridge), "knee_h": kh, "pitch_deg": A["pitch_deg"],
             "ridge_x": rd(xc), "wall_t": t, "top_y": rd(top), "well": {"x": [rd(x0), rd(x1)], "z": [rd(z0), rd(z1)]},
             "rail": {"h": rh, "t": rt, "off": ro, "gap_z": rd(gap)},
             "dormer": {"z": dz, "face_x": rd(dface), "inner_half": rd(di), "opening": [dw, dh], "sill_y": rd(ys), "head_y": rd(yh),
                        "ceiling_y": rd(yf + 1.76), "cornice_w": A["dormer_cornice_w"], "pitch_deg": A["dormer_pitch_deg"], "open_deg": 95},
             "bed": bed, "chimney": chim, "stove": stove, "collar_y": rd(yf + 2.30)}
    return {"rise_m": round(r, 4), "going_m": round(float(g), 3), "risers": n, "boxes": B, "attic": attic, "walk_path": [[rd(v) for v in q] for q in path],
            "authored": f"{n} risers of {r:.4f} to the attic floor {yf:.3f}, going {g:.3f}, first riser {s0:.3f} m inside the door; full well width; attic {W} x {L} m, ridge {ridge:.2f}"}


def stair_spec(final, o):
    """The main stair in spec coordinates (x east, z south, y up; upper floor at y = 0), from the measured flight
    (measurements/rooms/stairs.json) and the well/walkway the trace now holds. Steps are solid boxes down to the foyer
    floor (a grey-box stair); rails are boxes; walk_path is the route the Unity walk test climbs and descends."""
    S = json.loads(STAIR.read_text()); m, a = S["measured"], S["authored"]
    r, g, n1, n = m["rise_m"]["value"], m["going_m"]["value"], m["risers_floor_to_landing"]["value"], a["risers_total"]
    if VARIANT:
        n1, n = map(int, sys.argv[sys.argv.index("--risers") + 1].split("+")); n += n1
        r = float(sys.argv[sys.argv.index("--floor-to-floor") + 1]) / n
    F = n * r
    sx = lambda P: np.c_[P[:, 1] - o[1], P[:, 0] - o[0]]
    well, hall = sx(final["main_stair_opening"]), sx(final["hall_corridor"])
    xw, xe, zn, zs = well[:, 0].min(), well[:, 0].max(), well[:, 1].min(), well[:, 1].max()
    xh = well[np.isclose(well[:, 1], zn), 0].max()                      # stair head: the gallery's west edge
    zg = hall[np.isclose(hall[:, 0], xh) & (hall[:, 1] > zn + 0.3), 1].min()   # gallery's south edge
    # Oct 15 (user: walls don't line up, z-fighting): the well's rear, north and south walls ARE the ground foyer's, traced
    # 2-5 cm apart on the two floors. The stair and its well walls take the foyer's planes; the well walls start where the
    # foyer's own walls stop (ceiling on the stair side, landing underside at the rear), so no two faces overlap.
    G = ROOT / "spec/house_spec.ground.json"
    fy = None
    if G.exists():
        gs = json.loads(G.read_text()); fy = next((s for s in gs["spaces"] if s["name"] == "foyer"), None)
    if fy:
        P_ = np.array(fy["polygon_xz"]); zn, zs = P_[:, 1].min(), P_[:, 1].max()
        # the rear wall: the foyer's notch under the landing became rear_passage + under_landing (film arch, Oct 15)
        xw = min(min(p[0] for p in s["polygon_xz"]) for s in gs["spaces"] if s["name"] in ("foyer", "rear_passage", "under_landing"))
    fc = fy["ceiling_m"] if fy else 0.0                                   # the foyer's walls end here
    W1, DL = a["flight_1_width_m"], a["landing_depth_m"]
    z1 = zs - W1                                                          # flight 1's north (open) side
    xl = xw + DL                                                          # landing's east edge = top nosing of flight 1
    g2 = (xh - xl) / (n - n1 - 1)                                         # flight 2 going (fills landing edge to stair head)
    B = []
    box = lambda name, kind, x0, x1, y0, y1, z0, z1_: B.append({"name": name, "kind": kind, "x": [round(float(x0), 3), round(float(x1), 3)],
                                                             "y": [round(float(y0), 3), round(float(y1), 3)], "z": [round(float(z0), 3), round(float(z1_), 3)]})

    def rail(name, x0, x1, y0, y1, z0, z1_):
        """An open balustrade in the box (x0..x1, z0..z1_), floor y0, handrail top y1: a 6 cm handrail and 4 cm spindles
        at most 0.12 m apart along its long side (Marina's stair has turned spindles, not a solid panel)."""
        along_x = (x1 - x0) >= (z1_ - z0)
        a0, a1 = (x0, x1) if along_x else (z0, z1_)
        box(name + "_cap", "rail", x0, x1, y1 - 0.06, y1, z0, z1_)
        k = max(1, int(np.ceil((a1 - a0) / 0.12)))
        for i in range(k):
            c = a0 + (i + 0.5) * (a1 - a0) / k
            if along_x: box(f"{name}_spindle{i}", "rail", c - 0.02, c + 0.02, y0, y1 - 0.06, z0, z1_)
            else: box(f"{name}_spindle{i}", "rail", x0, x1, y0, y1 - 0.06, c - 0.02, c + 0.02)
    for k in range(1, n1):                                                # flight 1 treads (the n1-th riser lands on the landing)
        box(f"flight1_step{k:02d}", "step", xl + (n1 - 1 - k) * g, xl + (n1 - k) * g, -F, -F + k * r, z1, zs)
    SLAB = 0.144  # landing / flight-2 construction depth. Oct 15 (film 2677/3888, tools/house/foyer_cameras.py): the wallpaper over the arch ends at 2.171/2.178 m, the arch crown just under it at 2.165/2.168; landing top 2.314 - 2.17. Was 0.05: Oct 15 (user: the soffit began below the kitchen opening head): Marina 312 s shows the picture wall papered to 2.26-2.28 m, where flight 2's white soffit starts, and a thin landing edge over the passage (foyer_length.py); was 0.28 from a clip A "underside 1.94-2.07" read. Marina's walk 1068-1072 s passes UNDER the landing to
                  # the arched door and the kitchen opening, so these are raised slabs, not solid blocks (fixed Oct 13)
    SLAB2 = 0.05  # flight 2 keeps the thin soffit (2.26 m at its foot): it runs over the kitchen opening (head 2.20), which the user had it clear (changes/2026-10-15-landing-soffit.json); only the landing takes the film's 0.144
    UNDER = 0.015   # the rooms under the landing have their ceilings this far below its underside (ground CEILINGS): the rear wall above starts there (seam check: 1.5 cm gap)
    box("landing", "landing", xw, xl, -F + n1 * r - SLAB, -F + n1 * r, zn, zs)          # full width along the rear wall
    for k in range(n1 + 1, n):                                            # flight 2: rises east from the landing's north end
        box(f"flight2_step{k - n1:02d}", "step", xl + (k - n1 - 1) * g2, xl + (k - n1) * g2, -F + k * r - r - SLAB2, -F + k * r, zn, zg)
    x0 = xl + (n1 - 1) * g                                                # foot of flight 1
    box("foyer_floor_under_well", "floor", xw, xe + 1.0, -F - 0.2, -F, zn, zs)
    for k in range(1, n1):                                                # flight 1 open-side balustrade, stepped with the treads
        rail(f"flight1_rail{k:02d}", xl + (n1 - 1 - k) * g, xl + (n1 - k) * g, -F + k * r, -F + k * r + 0.9, z1 - 0.06, z1)
    rail("landing_rail", xl, xl + 0.06, -F + n1 * r, -F + n1 * r + 0.9, zg, z1)   # landing edge over the foyer
    for k in range(n1 + 1, n):
        rail(f"flight2_rail{k - n1:02d}", xl + (k - n1 - 1) * g2, xl + (k - n1) * g2, -F + k * r, -F + k * r + 0.9, zg, zg + 0.06)
    box("well_wall_south", "wall", xw - 0.07, xe, -F + fc, 0, zs, zs + 0.07)    # the photo wall, above the foyer's own wall
    box("well_wall_west", "wall", xw - 0.07, xw, (-F + n1 * r - SLAB - UNDER) if fy else -F, 0 if fy else 2.4, zn - 0.07, zs + 0.07)   # rear wall, landing underside to the upper floor (the upstairs well's own wall goes on above; seam check)
    if fy:   # the landing's two ends: wall from under the landing up to where the foyer's walls end (walk note Oct 15: a slot above
             # the landing at its north end showed the back stair's and kitchen's ceilings; nothing stood between 2.16 and 2.82 m)
        for nm, z0_, z1_ in (("well_wall_landing_north", zn - 0.07, zn), ("well_wall_landing_south", zs, zs + 0.07)):
            box(nm, "wall", xw, xl - 0.07, -F + n1 * r - SLAB - UNDER, -F + fc, z0_, z1_)
    # north edge of the well: only the upper floor's edge (fascia). A full-height wall here stood inside the foyer, which is
    # wider than the well (fixed Oct 13)
    box("well_fascia_north", "wall", xw, xe, (-F + fc) if fy else -0.30, 0, zn - 0.07, zn)   # from the foyer's wall top (no overlap)
    box("well_ceiling", "ceiling", xw - 0.07, xe + RAIL_T, 2.40, 2.55, zn - 0.07, zs + 0.07)   # Marina: chandelier hangs from it
    zm, zf = (zn + zg) / 2, (z1 + zs) / 2
    path = [[x0 + 0.9, -F, zf], [x0 + 0.45, -F, zf], [xl - 0.4, -F + n1 * r, zf], [xl - 0.4, -F + n1 * r, zm],
            [xh + 0.5, 0.0, zm], [xe + 0.4, 0.0, zm]]
    return {"source": str(STAIR.relative_to(ROOT)), "floor_to_floor_m": round(F, 3), "risers": n, "rise_m": r, "going_m": g,
            "measured": "flight 1: 13 risers, rise, going (pitch), tread width; landing height",
            "authored": a["decided"] + "; landing depth, gallery and flight widths",
            "boxes": B, "walk_path": [[round(float(v), 3) for v in q] for q in path]}


def windows_spec(spaces):
    """measurements/windows/<floor>.json (fractions of a room wall) -> spec windows: the wall line and the span along it,
    resolved on the built room, so windows follow the room when it is rebuilt."""
    p = ROOT / f"measurements/windows/{FLOOR}.json"
    if not p.exists():
        return []
    polys = {s["name"]: np.array(s["polygon_xz"]) for s in spaces}
    out = []
    for w in json.loads(p.read_text())["windows"]:
        P = polys[w["room"]]
        ax = 0 if w["side"][0] == "x" else 1                  # x_max: the wall is x = max, the window spans z
        if "edge" in w:   # a wall that is not on the room's bounding box (L-shaped rooms): polygon edge i -> i+1
            p, q = P[w["edge"]], P[(w["edge"] + 1) % len(P)]
            assert abs(p[ax] - q[ax]) < 1e-6, f"{w['room']}/{w['name']}: edge {w['edge']} is not an {w['side'][0]} = const wall"
            coord, lo, hi = p[ax], min(p[1 - ax], q[1 - ax]), max(p[1 - ax], q[1 - ax])
        else:
            coord = P[:, ax].max() if w["side"].endswith("max") else P[:, ax].min()
            lo, hi = P[:, 1 - ax].min(), P[:, 1 - ax].max()
        c = lo + w["centre_frac"] * (hi - lo)
        assert lo <= c - w["width_m"] / 2 and c + w["width_m"] / 2 <= hi, f"{w['room']}/{w['name']}: window runs past its wall"
        out.append({"room": w["room"], "name": w["name"], "wall_axis": "x" if ax == 0 else "z", "wall_coord_spec": round(float(coord), 3),
                    "span_spec": [round(float(c - w["width_m"] / 2), 3), round(float(c + w["width_m"] / 2), 3)],
                    "sill_m": w["sill_m"], "head_m": w["head_m"], **({"bare": True} if w.get("bare") else {}),
                    **({"model": w["model"]} if w.get("model") else {})})   # model: the frame, leaf and glass are a generated model
    return out


def main():
    plan = json.loads(PLAN.read_text())
    topo = json.loads(DOORS.read_text())
    sp = {s["name"]: s for s in plan["spaces"]}
    raw = {n: np.array(s["polygon_m"]) for n, s in sp.items()}
    weights = {n: ANCHOR_WEIGHT if n in ANCHORS else 1.0 for n in sp}
    log = [f"# {FLOOR.capitalize()} reconciliation log", "",
           f"Generated by `tools/house/reconcile.py` from `{PLAN.relative_to(ROOT)}` and `{DOORS.relative_to(ROOT)}`.",
           f"Anchors (SfM-measured, weight {ANCHOR_WEIGHT:g}): {', '.join(ANCHORS)}. Tolerances: align {ALIGN_TOL} m, "
           f"wall {WALL_MIN}-{WALL_MAX} m.", ""]

    # 1. square
    edges = {n: edges_of(p) for n, p in raw.items()}
    squared = {n: rebuild(e) for n, e in edges.items()}
    log += ["## 1. Squared (walls made exactly straight)", "", "| space | max corner move (cm) |", "|---|---|"]
    for n in sp:
        log.append(f"| {n} | {np.abs(squared[n] - raw[n]).max() * 100:.1f} |")

    # 2. align
    flat, new, clusters = align(edges, weights)
    for k, (n, i, e) in enumerate(flat):
        edges[n][i][1] = new[k]
    final = {n: rebuild(e) for n, e in edges.items()}
    log += ["", "## 2. Aligned (near-collinear walls share one line)", "",
            "| line | walls (space) | before (m) | after (m) | largest move (cm) |", "|---|---|---|---|---|"]
    for kind, g, cs, c in clusters:
        who = ", ".join(flat[i][0] for i in g)
        axis = "x" if flat[g[0]][2][0] == 0 else "y"
        if kind == "aligned":
            log.append(f"| {axis} = {c:.2f} | {who} | {', '.join(f'{v:.2f}' for v in cs)} | {c:.2f} | {np.abs(cs - c).max() * 100:.1f} |")
        else:
            log.append(f"| CONFLICT {axis} | {who} | {', '.join(f'{v:.2f}' for v in cs)} | unchanged | spread {np.ptp(cs) * 100:.0f} cm > {MAX_SPREAD * 100:.0f} |")

    # anchors: did they keep their measured size?
    log += ["", "### Anchor rooms vs their own SfM measurement", "", "| room | reconciled (m) | SfM (m) | change |", "|---|---|---|---|"]
    sfm_dims = {"parents_bedroom": None, "kevin_jeff_room": (3.60, 4.57), "buzz_room": (4.35, 3.49)}
    for n in ANCHORS:
        bb = np.ptp(final[n], axis=0)
        ref = sfm_dims[n]
        if ref:
            log.append(f"| {n} | {bb[0]:.2f} x {bb[1]:.2f} | {ref[0]:.2f} x {ref[1]:.2f} | {(bb[0] / ref[0] - 1):+.1%} / {(bb[1] / ref[1] - 1):+.1%} |")
        else:
            log.append(f"| {n} | {bb[0]:.2f} x {bb[1]:.2f} | (frame of the calibration) | area {area(final[n]):.1f} vs {area(raw[n]):.1f} m² |")

    # 3. walls
    pairs = facing_pairs(final, edges)
    flags = []
    log += ["", "## 3. Walls between spaces", "", "| between | thickness (cm) | length (m) | note |", "|---|---|---|---|"]
    best = {}
    for p in pairs:
        key = tuple(sorted((p["a"], p["b"])))
        if key not in best or p["hi"] - p["lo"] > best[key]["hi"] - best[key]["lo"]:
            best[key] = p
    for (a, b), p in sorted(best.items()):
        note = ""
        d = door_on(p, topo["doors"])
        if d and d["kind"] == "open":
            note = "open (no wall: stair head)"
        elif p["gap"] < WALL_MIN:
            note = "TOO THIN: rooms overlap or touch"; flags.append(f"wall {a}/{b} {p['gap'] * 100:.0f} cm: too thin")
        elif p["gap"] > WALL_MAX:
            note = "thick: chase, closet or measurement error"; flags.append(f"wall {a}/{b} {p['gap'] * 100:.0f} cm: thick")
        log.append(f"| {a} / {b} | {p['gap'] * 100:.0f} | {p['hi'] - p['lo']:.2f} | {note} |")

    # 3b. thin interior walls to WALL_T around their centrelines; each side grows outward by half the excess
    before = {n: final[n].copy() for n in final}
    move = {}
    for p in pairs:
        dk = (door_on(p, topo["doors"]) or {}).get("kind")
        is_rail = dk == "rail"
        # open (no wall): the two rooms meet on their shared centreline. Was: left as traced, which kept a strip with no
        # floor and no wall between them (Oct 15: a 6 cm gap beside the service stair let the leak check's rays outside)
        t = 0.0 if dk == "open" else RAIL_T if is_rail else WALL_T
        if p["gap"] <= t or (MEASURED and not is_rail and dk != "open"):   # rails and openings are measurement facts, applied in both builds
            continue
        d = (p["gap"] - t) / 2
        for n, k, sgn in ((p["a"], p["ia"], p["sa"]), (p["b"], p["ib"], -p["sa"])):
            dn = d
            if is_rail:   # the balustrade stands on the stairwell's edge: the walkable side takes the whole gap
                dn = 0.0 if sp[n]["kind"] == "opening" else p["gap"] - t
            if (n, k) not in move or dn < abs(move[(n, k)]):  # an edge facing several neighbours takes the smallest move
                move[(n, k)] = sgn * dn
    for (n, k), m in move.items():
        edges[n][k][1] += m
    final = {n: rebuild(e) for n, e in edges.items()}
    edges = {n: edges_of(final[n]) for n in final}   # wall extents follow the moved neighbours (door spans read them)
    log += ["", f"## 3b. Interior walls thinned to {WALL_T * 100:.0f} cm (centrelines kept; rooms take the space)", "",
            "| space | before (m) | after (m) | area before → after (m²) | change |", "|---|---|---|---|---|"]
    for n in sp:
        b0, b1 = np.ptp(before[n], axis=0), np.ptp(final[n], axis=0)
        a0, a1 = area(before[n]), area(final[n])
        log.append(f"| {n} | {b0[0]:.2f} x {b0[1]:.2f} | {b1[0]:.2f} x {b1[1]:.2f} | {a0:.1f} → {a1:.1f} | {(a1 / a0 - 1):+.1%} |")
    pairs = facing_pairs(final, edges)
    best = {}
    for p in pairs:
        key = tuple(sorted((p["a"], p["b"])))
        if key not in best or p["hi"] - p["lo"] > best[key]["hi"] - best[key]["lo"]:
            best[key] = p

    # 4. doors
    doors, rules = [], []
    log += ["", "## 4. Doors and openings", "", "| between | kind | position along wall (m) | width (m) | placed from |", "|---|---|---|---|---|"]
    for d in topo["doors"]:
        if d["kind"] == "wall":   # names a plain wall between two spaces that also share an opening elsewhere
            continue
        key = tuple(sorted((d["a"], d["b"])))
        hit = lambda e: e is d or (e is not None and "wall_axis" not in d and "wall_axis" not in e)   # several doors on one wall (dining/kitchen)
        on = [q for q in pairs if tuple(sorted((q["a"], q["b"]))) == key and hit(door_on(q, topo["doors"]))]
        p = max(on, key=lambda q: q["hi"] - q["lo"]) if on else None
        if not p:
            flags.append(f"door {d['a']}/{d['b']}: no shared wall found within {FACE_MAX} m"); continue
        wall_c = (p["coord_a"] + p["coord_b"]) / 2
        if "span_spec" in d:   # measured directly in spec metres (e.g. from tracked Marina cameras): convert to plan metres
            O = np.array(json.loads((ROOT / "spec/house_spec.json").read_text())["origin_plan_m"]) if FLOOR != "upstairs" else np.array(ORIGIN)
            d = {**d, "span": [v + (O[1] if d["span_spec_axis"] == "x" else O[0]) for v in d["span_spec"]]}
        if d["kind"] in ("rail", "open") or (d["kind"] == "arch" and not ({"span", "px", "width"} & set(d))):
            lo, hi, src = p["lo"], p["hi"], "full shared wall"
        elif "span" in d or "px" in d:
            if "px" in d and "span_spec" not in d:   # doorway ends read in the overhead, mapped through the trace's calibration
                sys.path.insert(0, str(ROOT / "tools/sfm")); from calib import mapper
                P = mapper(json.loads(TRACE.read_text()))[0](d["px"])
                lo, hi = sorted(P[:, 1 - p["axis"]]); src = "read in the overhead"
            else:
                lo, hi = sorted(d["span"]); src = "measured"
            if lo < p["lo"] or hi > p["hi"]:  # keep the measured width, slide it onto the wall
                shift = max(p["lo"] - lo, 0) - max(hi - p["hi"], 0)
                lo, hi = lo + shift, hi + shift
                src = f"measured, slid {shift * 100:+.0f} cm onto the shared wall"
                if abs(shift) > 0.15 or lo < p["lo"] - 0.005 or hi > p["hi"] + 0.005:
                    flags.append(f"door {d['a']}/{d['b']}: measured span needs {shift * 100:+.0f} cm to fit its wall")
        else:
            wd = d.get("width", DOOR_W)
            mid = (p["lo"] + p["hi"]) / 2; lo, hi = mid - wd / 2, mid + wd / 2; src = "topology (centred; position unverified)"
        w = hi - lo
        if d["kind"] in ("door", "fake_door") and w > (p["hi"] - p["lo"]) + 0.005:
            flags.append(f"door {d['a']}/{d['b']}: {w:.2f} m door on only {p['hi'] - p['lo']:.2f} m of shared wall")
        doors.append({"between": [d["a"], d["b"]], "kind": d["kind"], "wall_axis": "x" if p["axis"] == 0 else "y",
                      "wall_coord": round(wall_c, 3), "wall_thickness": round(p["gap"], 3), "span": [round(lo, 3), round(hi, 3)],
                      "width": round(w, 3), "height": DOOR_H if d["kind"] in ("door", "fake_door") else d.get("crown"), **({"spring": d["spring"]} if "spring" in d else {}), **({"cased": True} if d.get("cased") else {}), **({"clear": d["clear"]} if "clear" in d else {}), "opens": d["kind"] != "fake_door", "placed_from": src, "source": d["source"]})
        log.append(f"| {d['a']} / {d['b']} | {d['kind']} | {lo:.2f}-{hi:.2f} | {w:.2f} | {src} |")
        if d["kind"] == "door":  # fake_door: a prop slab on the wall, no opening, no body rule
            rules.append((f"adult fits door {d['a']}/{d['b']}", w >= ADULT["capsule_diameter"] + 0.1 and DOOR_H >= ADULT["height"] + 0.1,
                          f"{w:.2f} m wide x {DOOR_H:.2f} m"))

    # 5. rules
    for n, s in sp.items():
        if s["kind"] == "hall":
            short = float(np.ptp(final[n], axis=0).min())
            # corridors keep the 0.90 m hall minimum; a stair (name *_stair) only has to pass the adult body like a door
            need = ADULT["capsule_diameter"] + 0.1 if n.endswith("_stair") else ADULT["min_hall"]
            rules.append((f"adult fits {'stair' if n.endswith('_stair') else 'hall'} {n}", short >= need, f"narrowest {short:.2f} m (min {need:.2f})"))
    log += ["", "## 5. Body rules (adult, hard)", "", "| rule | result | value |", "|---|---|---|"]
    for r, ok, v in rules:
        log.append(f"| {r} | {'pass' if ok else 'FAIL'} | {v} |")
        if not ok:
            flags.append(f"rule failed: {r} ({v})")

    log += ["", "## Flags (need a decision or more evidence)", ""] + [f"- {f}" for f in flags] + \
           [f"- unresolved: {u}" for u in topo.get("unresolved", [])] + \
           [f"- ceiling {CEILINGS['default']} m in rooms not measured directly (Kevin 2.40 / parents 2.50 / attic leg 2.29 measured)"]

    # spec: x = across (plan y), z = along (plan x), origin at the outline's min corner, y up
    allp = np.vstack(list(final.values()))
    o = np.array(ORIGIN)      # frozen (Oct 15): the well's rear edge set it until it moved; every spec coordinate depends on it
    if FLOOR == "upstairs":
        assert (allp.min(0) >= o - 1e-6).all(), "an upstairs space lies outside the spec frame's origin corner"
    else:   # every floor shares the upstairs spec frame (stack_floor.py registered the plan into it)
        o = np.array(json.loads((ROOT / "spec/house_spec.json").read_text())["origin_plan_m"])
    to_spec = lambda P: [[round(float(y - o[1]), 3), round(float(x - o[0]), 3)] for x, y in P]
    spec = {
        "version": 1, "level": FLOOR, "units": "metres",
        "frame": "x = across the overhead (right), z = down the overhead; origin = min corner of all spaces; y up. "
                 "Front facade is the +x side (parents' room / Kevin / hall bath / Buzz row).",
        "origin_plan_m": [round(float(o[0]), 4), round(float(o[1]), 4)],
        "scale": {"door_height_m": DOOR_H, "door_range_in": [78, 80], "note": "80 in nominal; area check brackets 78-80 in"},
        "ceiling_height_m": {"default": CEILINGS["default"], "source": "measured on door walls in 3 spaces (Oct 13); per-space values on each space" if FLOOR == "upstairs"
                             else "8 ft standard, agreeing with door-jamb measurements in the living and dining rooms (tools/house/ground_ceiling.py, Oct 14)"},
        "bodies": {"kevin": {"eye_height": 1.1, "crawl_height": 0.4}, "bandit": {"eye_height": 1.7, "crouch_height": 1.1, **ADULT}},
        "walls": {"interior_thickness_m": WALL_T, "exterior": "unchanged from the calibrated overhead",
                  "note": "user decision Oct 13: thin walls, rooms take the freed space (a few % larger than measured)"},
        "spaces": [{"name": n, "kind": sp[n]["kind"], "anchor": n in ANCHORS, **({"opens": OPENS[n]} if n in OPENS else {}), "polygon_xz": to_spec(final[n]),
                    "area_m2": round(area(final[n]), 2), "ceiling_m": CEILINGS.get(n, CEILINGS["default"])} for n in sp],
        "doors": [{**d, "wall_coord_spec": round(d["wall_coord"] - o[0 if d["wall_axis"] == "x" else 1], 3),
                   "span_spec": [round(v - o[1 if d["wall_axis"] == "x" else 0], 3) for v in d["span"]],
                   "spec_axis": "z" if d["wall_axis"] == "x" else "x"} for d in doors],
        "flags": flags,
        "attic_stair": attic_stair_spec(final, o, CEILINGS.get("attic_stair", CEILINGS["default"])) if FLOOR == "upstairs" and "attic_stair" in final else None,
        "stair": stair_spec(final, o) if FLOOR == "upstairs" else (service_stair_spec(final, o) if "back_stair" in final else None),
        "floor_y_m": 0.0 if FLOOR == "upstairs" else -round(json.loads((ROOT / f"spec/house_spec{'.' + VARIANT if VARIANT else ''}.json").read_text())["stair"]["floor_to_floor_m"], 3),
        "sources": {"plan": str(PLAN.relative_to(ROOT)), "doors": str(DOORS.relative_to(ROOT)), "anchors": ANCHORS},
    }
    spec["windows"] = windows_spec(spec["spaces"])
    wf = ROOT / f"measurements/windows/{FLOOR}.json"   # openings cut through walls of both storeys (the landing window), placed in spec metres
    spec["wall_openings"] = json.loads(wf.read_text()).get("wall_openings", []) if wf.exists() else []
    (ROOT / "spec").mkdir(exist_ok=True)
    tag =(".measured" if MEASURED else "") if FLOOR == "upstairs" else ("." + FLOOR + (".measured" if MEASURED else ""))
    if VARIANT:
        tag += "." + VARIANT
    if MEASURED:
        spec["walls"] = {"interior_thickness_m": None, "note": "as measured: walls NOT thinned (comparison build only)"}
    (ROOT / f"spec/house_spec{tag}.json").write_text(json.dumps(spec, indent=1) + "\n")
    if not VARIANT:
        (ROOT / f"spec/{FLOOR}-changes{'.measured' if MEASURED else ''}.md").write_text("\n".join(log) + "\n")
    print("\n".join(log))


if __name__ == "__main__":
    sq = rebuild(edges_of(np.array([[0, 0], [0.02, 3], [2, 3.03], [1.98, 0.01]])))
    assert (np.diff(np.vstack([sq, sq[:1]]), axis=0) == 0).any(1).all(), "squared walls must be axis-aligned"
    assert np.allclose(np.ptp(sq, axis=0), [1.98, 3.01])
    main()
