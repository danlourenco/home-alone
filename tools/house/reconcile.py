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
    {"default": 2.438, "foyer": 2.82, "back_hall": 2.25}  # back_hall Oct 15: just under the landing (underside 2.264 m; a coplanar ceiling flickered, seam check), unknown beyond. foyer Oct 14 (2.82 = the most under the 0.2 m upper-floor slab): front ceiling 2.92 m in the clip A solve, 1.40 x a door in the film
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
    """The service (back) stair in its traced enclosure: foot at the breakfast-area end (the enclosure's open east side),
    rising west at the main stair's measured rise, risers spread over the enclosure's length. Built only up to the
    enclosure's ceiling and closed there: Marina's upstairs has no arrival for it (Muto: it never reached the upstairs
    set); the user accepted closing it (Oct 15). Going and count are AUTHORED (DEVIATIONS 30)."""
    S = json.loads(STAIR.read_text()); r = S["measured"]["rise_m"]["value"]; n = S["authored"]["risers_total"]
    P = np.c_[final["back_stair"][:, 1] - o[1], final["back_stair"][:, 0] - o[0]]
    x0, x1, z0, z1 = P[:, 0].min(), P[:, 0].max(), P[:, 1].min(), P[:, 1].max()
    g = (x1 - x0) / (n - 1)
    ceil = CEILINGS.get("back_stair", CEILINGS["default"])
    B = []
    for k in range(1, n):
        if k * r > ceil - 0.05:
            break
        B.append({"name": f"service_step{k:02d}", "kind": "step", "x": [round(float(x1 - k * g), 3), round(float(x1 - (k - 1) * g), 3)],
                  "y": [0.0, round(k * r, 3)], "z": [round(float(z0), 3), round(float(z1), 3)]})
        xa, xb = x1 - k * g, x1 - (k - 1) * g                # open side (the breakfast area, z0): 2 spindles a tread, rail 0.9 m above
        B.append({"name": f"service_rail{k:02d}_cap", "kind": "rail", "x": [round(float(xa), 3), round(float(xb), 3)],
                  "y": [round(k * r + 0.84, 3), round(k * r + 0.9, 3)], "z": [round(float(z0), 3), round(float(z0) + 0.06, 3)]})
        for i in (0.25, 0.75):
            c = xa + i * g
            B.append({"name": f"service_rail{k:02d}_spindle{i}", "kind": "rail", "x": [round(float(c - 0.02), 3), round(float(c + 0.02), 3)],
                      "y": [round(k * r, 3), round(k * r + 0.84, 3)], "z": [round(float(z0) + 0.01, 3), round(float(z0) + 0.05, 3)]})
    return {"rise_m": r, "going_m": round(float(g), 3), "risers": len(B), "boxes": B, "walk_path": [],
            "authored": f"going {g:.3f} m = enclosure length / {n - 1} treads; {len(B)} risers built, closed at the {ceil} m ceiling"}


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
        P_ = np.array(fy["polygon_xz"]); xw, zn, zs = P_[:, 0].min(), P_[:, 1].min(), P_[:, 1].max()
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
    SLAB = 0.05   # landing / flight-2 construction depth. Oct 15 (user: the soffit began below the kitchen opening head): Marina 312 s shows the picture wall papered to 2.26-2.28 m, where flight 2's white soffit starts, and a thin landing edge over the passage (foyer_length.py); was 0.28 from a clip A "underside 1.94-2.07" read. Marina's walk 1068-1072 s passes UNDER the landing to
                  # the arched door and the kitchen opening, so these are raised slabs, not solid blocks (fixed Oct 13)
    box("landing", "landing", xw, xl, -F + n1 * r - SLAB, -F + n1 * r, zn, zs)          # full width along the rear wall
    for k in range(n1 + 1, n):                                            # flight 2: rises east from the landing's north end
        box(f"flight2_step{k - n1:02d}", "step", xl + (k - n1 - 1) * g2, xl + (k - n1) * g2, -F + k * r - r - SLAB, -F + k * r, zn, zg)
    x0 = xl + (n1 - 1) * g                                                # foot of flight 1
    box("foyer_floor_under_well", "floor", xw, xe + 1.0, -F - 0.2, -F, zn, zs)
    for k in range(1, n1):                                                # flight 1 open-side balustrade, stepped with the treads
        rail(f"flight1_rail{k:02d}", xl + (n1 - 1 - k) * g, xl + (n1 - k) * g, -F + k * r, -F + k * r + 0.9, z1 - 0.06, z1)
    rail("landing_rail", xl, xl + 0.06, -F + n1 * r, -F + n1 * r + 0.9, zg, z1)   # landing edge over the foyer
    for k in range(n1 + 1, n):
        rail(f"flight2_rail{k - n1:02d}", xl + (k - n1 - 1) * g2, xl + (k - n1) * g2, -F + k * r, -F + k * r + 0.9, zg, zg + 0.06)
    box("well_wall_south", "wall", xw - 0.07, xe, -F + fc, 0, zs, zs + 0.07)    # the photo wall, above the foyer's own wall
    box("well_wall_west", "wall", xw - 0.07, xw, (-F + n1 * r - SLAB) if fy else -F, 0 if fy else 2.4, zn - 0.07, zs + 0.07)   # rear wall, landing underside to the upper floor (the upstairs well's own wall goes on above; seam check)
    # north edge of the well: only the upper floor's edge (fascia). A full-height wall here stood inside the foyer, which is
    # wider than the well (fixed Oct 13)
    box("well_fascia_north", "wall", xw, xe, (-F + fc) if fy else -0.30, 0, zn - 0.07, zn)   # from the foyer's wall top (no overlap)
    box("well_ceiling", "ceiling", xw - 0.07, xe, 2.40, 2.55, zn - 0.07, zs + 0.07)   # Marina: chandelier hangs from it
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
        coord = P[:, ax].max() if w["side"].endswith("max") else P[:, ax].min()
        lo, hi = P[:, 1 - ax].min(), P[:, 1 - ax].max()
        c = lo + w["centre_frac"] * (hi - lo)
        out.append({"room": w["room"], "name": w["name"], "wall_axis": "x" if ax == 0 else "z", "wall_coord_spec": round(float(coord), 3),
                    "span_spec": [round(float(c - w["width_m"] / 2), 3), round(float(c + w["width_m"] / 2), 3)],
                    "sill_m": w["sill_m"], "head_m": w["head_m"]})
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
        on = [q for q in pairs if tuple(sorted((q["a"], q["b"]))) == key and door_on(q, topo["doors"]) is d]
        p = max(on, key=lambda q: q["hi"] - q["lo"]) if on else None
        if not p:
            flags.append(f"door {d['a']}/{d['b']}: no shared wall found within {FACE_MAX} m"); continue
        wall_c = (p["coord_a"] + p["coord_b"]) / 2
        if d["kind"] in ("rail", "open") or (d["kind"] == "arch" and not ({"span", "px", "width"} & set(d))):
            lo, hi, src = p["lo"], p["hi"], "full shared wall"
        elif "span" in d or "px" in d:
            if "px" in d:   # doorway ends read in the overhead, mapped through the trace's calibration
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
                      "width": round(w, 3), "height": DOOR_H if d["kind"] in ("door", "fake_door") else None, "opens": d["kind"] != "fake_door", "placed_from": src, "source": d["source"]})
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
        "stair": stair_spec(final, o) if FLOOR == "upstairs" else (service_stair_spec(final, o) if "back_stair" in final else None),
        "floor_y_m": 0.0 if FLOOR == "upstairs" else -round(json.loads((ROOT / f"spec/house_spec{'.' + VARIANT if VARIANT else ''}.json").read_text())["stair"]["floor_to_floor_m"], 3),
        "sources": {"plan": str(PLAN.relative_to(ROOT)), "doors": str(DOORS.relative_to(ROOT)), "anchors": ANCHORS},
    }
    spec["windows"] = windows_spec(spec["spaces"])
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
