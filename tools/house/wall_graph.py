"""Wall graph (tasks/wall-grid-plan.md, phases 1-2): build each storey like a house, in Python, before Unity sees it.

1. grid: every room edge snaps onto a shared wall line per floor (wall_grid_preview.cluster: weighted mean, anchors x5),
   then the user's decisions in measurements/grid-snaps.json close the remaining thick walls ("close") and declare real
   spaces between rooms ("shaft").
2. rooms: each room polygon is rebuilt from its snapped edges (a vertex takes the snaps of its two edges).
3. cells: the storey is cut into cells on every room coordinate and every coordinate +-WALL. A cell is ROOM (inside a
   space), WALL (outside every space but within WALL of one: the union of all wall footprints, so corners and T-junctions
   close by construction) or OUT. Rectilinear, exact to 0.1 mm.
4. boxes: cells merge into non-overlapping rectangles: walls (per top height), the floor plate, ceilings per room.
   Openings (doors, arches, windows) are cut from the walls as y-intervals.
5. checks (V2): no void inside the building (OUT cells not reachable from outside) unless declared; no wall sliver under
   2 cm; no two boxes overlapping; every room within its baseline size.
usage: uv run --with numpy python -I tools/house/wall_graph.py [--json]   (writes spec/geometry.json with --json)
"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/house"))
import wall_grid_preview as wgp  # noqa: E402

WALL = 0.14          # m: interior wall thickness (user decision Oct 13); exterior walls use it too for now
Q = 1e-4             # coordinate quantum: everything is rounded to 0.1 mm so equal lines are bit-equal
SLIVER = 0.02        # m: a wall piece thinner than this is a modelling error
CASING = 0.07        # m: door/window trim width; an opening keeps this clear of a perpendicular wall (film 10819: casing meets wall)
ARCH_HEAD = 2.20     # m: arches without a measured crown (SpecGreybox.ArchHead); a spec door's height is its crown
CEIL_T = 0.15        # m: ceiling slab
RAIL_T = 0.06        # m: balustrade band between a hall and a stairwell (reconcile.RAIL_T)
MAX_SLIDE = 0.12     # m: a door slides at most a casing plus a snap to clear its trim; beyond that it is a conflict
FLOOR_T = 0.20       # m: floor plate


def q(v):
    return float(np.round(np.asarray(v) / Q) * Q)


def load():
    up = json.loads((ROOT / "spec/house_spec.json").read_text()); gr = json.loads((ROOT / "spec/house_spec.ground.json").read_text())
    dec = json.loads((ROOT / "measurements/grid-snaps.json").read_text())["decisions"]
    return {"upstairs": up, "ground": gr}, dec


# ---------- 1. grid ----------
def snap(spec, dec):
    E = wgp.edges("upstairs", spec["upstairs"]) + wgp.edges("ground", spec["ground"])
    # a rail is not a wall: its two rooms stand RAIL_T apart (the balustrade), so their faces cluster on the
    # rail's centre and keep that spacing (as a 14 cm wall the gallery's edge moved 4 cm off flight 2's side)
    for floor, fs in spec.items():
        for d in fs["doors"]:
            if d["kind"] != "rail":      # an "open" side shares one edge (no band): leave it
                continue
            for e in E:
                if e["floor"] == floor and e["room"] in d["between"] and e["axis"] == d["spec_axis"] and abs(e["face"] - d["wall_coord_spec"]) < 0.1 \
                        and min(e["hi"], d["span_spec"][1]) - max(e["lo"], d["span_spec"][0]) > 0.05:
                    e["centre"] = round(e["face"] + e["out"] * RAIL_T / 2, 4); e["rail"] = True
    wgp.cluster(E)
    # pins: a measured face keeps its place, or ("stack") goes to a given coordinate: the stair hall's upstairs walls stand on
    # the ground floor's (one two-storey wall, phase 5). Its whole shared line (the other side of the wall too) moves with it
    for d in dec:
        for p in (d.get("pin"), *d.get("stack", [])):
            if not p:
                continue
            hit = [e for e in E if e["floor"] == p["floor"] and e["room"] == p["room"] and e["axis"] == p["axis"] and abs(e["face"] - p["face"]) < 1e-3]
            assert hit, f"pin not found: {p}"
            e0 = hit[0]; line = [e for e in E if e["floor"] == e0["floor"] and e["axis"] == e0["axis"] and e.get("line") == e0["line"]]
            delta = p.get("to", p["face"]) - p["face"] - e0["snap"]
            for e in line:
                e["snap"] = round(e["snap"] + delta, 4); e["pinned_by"] = p["room"]
    for d in dec:   # close the thick walls the user decided: the moving room's face goes onto the other side's wall
        c = d.get("close")
        if not c:
            continue
        for a in E:
            if a["floor"] != c["floor"] or a["room"] != c["move"]:
                continue
            for b in E:
                if b["floor"] != c["floor"] or b["room"] != c["against"] or b["axis"] != a["axis"] or b["out"] != -a["out"]:
                    continue
                if min(a["hi"], b["hi"]) - max(a["lo"], b["lo"]) < 0.2:
                    continue
                fa, fb = a["face"] + a["snap"], b["face"] + b["snap"]
                sep = (fb - fa) * a["out"]
                if WALL + 0.01 < sep < 0.60:
                    a["snap"] = round(a["snap"] + a["out"] * (sep - WALL), 4); a["closed_by"] = c["against"]
    return E


# ---------- 2. rooms ----------
def snapped_rooms(spec, E):
    by = {}
    for e in E:
        by.setdefault((e["floor"], e["room"]), []).append(e)
    out = {}
    for floor, s in spec.items():
        rooms = []
        for r in s["spaces"]:
            P = r["polygon_xz"]; es = by.get((floor, r["name"]), [])
            def shift(axis, c, lo, hi):
                m = [e for e in es if e["axis"] == axis and abs(e["face"] - c) < 1e-4 and e["lo"] - 1e-4 <= lo and hi <= e["hi"] + 1e-4]
                return m[0]["snap"] if m else 0.0
            new = []
            n = len(P)
            for i, (x, z) in enumerate(P):
                px, pz = P[i - 1], P[(i + 1) % n]
                # the vertex's x comes from its x-edge (x = const), its z from its z-edge; one of its two edges is each
                ex = (px if abs(px[0] - x) < 1e-4 else pz); ez = (px if abs(px[1] - z) < 1e-4 else pz)
                dx = shift("x", x, min(z, ex[1]), max(z, ex[1])); dz = shift("z", z, min(x, ez[0]), max(x, ez[0]))
                new.append([q(x + dx), q(z + dz)])
            rooms.append({"name": r["name"], "kind": r["kind"], "opens": r.get("opens"), "poly": new, "ceil": r["ceiling_m"]})
        out[floor] = rooms
    return out


# ---------- 2b. openings ----------
def face_of(room, axis, c, lo, hi, reach=0.35):
    """The snapped edge of room on axis nearest coordinate c whose extent overlaps [lo, hi]: (face, out, edge_lo, edge_hi)."""
    P = room["poly"]; best = None
    for (x1, z1), (x2, z2) in zip(P, P[1:] + P[:1]):
        if axis == "x" and abs(x1 - x2) < Q:
            f, a, b = x1, min(z1, z2), max(z1, z2); probe = (x1 + 0.02, (a + b) / 2)
        elif axis == "z" and abs(z1 - z2) < Q:
            f, a, b = z1, min(x1, x2), max(x1, x2); probe = ((a + b) / 2, z1 + 0.02)
        else:
            continue
        if min(b, hi) - max(a, lo) <= 0 or abs(f - c) > reach:
            continue
        out = -1 if inside(P, np.array(probe[0]), np.array(probe[1])) else 1
        if best is None or abs(f - c) < abs(best[0] - c):
            best = (f, out, a, b)
    return best


def openings(floor_spec, rooms):
    """Doors, arches, rails, open sides and windows on the snapped walls. Each: axis (the constant coordinate), c (wall
    centreline), lo/hi along the wall, cuts (y intervals removed from the wall), and what Unity adds (trim, prop, rail, glass)."""
    by = {r["name"]: r for r in rooms}; out, notes = [], []
    for d in floor_spec["doors"]:
        a, b = d["between"]; axis = d["spec_axis"]; c0 = d["wall_coord_spec"]; lo, hi = d["span_spec"]
        fa = face_of(by[a], axis, c0, lo, hi) if a in by else None
        fb = face_of(by[b], axis, c0, lo, hi) if b in by else None
        f = fa or fb
        if f is None:
            notes.append(f"door {a}/{b}: no snapped wall near {axis}={c0:.3f}"); continue
        c = q(f[0] + f[1] * WALL / 2)
        kind = d["kind"]
        # an opening lives inside the wall its two rooms share, which the grid may have moved: a full-width opening (open side,
        # rail, arch) follows that wall's snapped ends, and nothing reaches past them (the stair head cut a notch into the
        # gallery's north wall in the pilot, Oct 15)
        slo = max(x[2] for x in (fa, fb) if x); shi = min(x[3] for x in (fa, fb) if x)
        if kind in ("open", "rail", "arch"):
            if abs(lo - slo) < 0.06: lo = slo
            if abs(hi - shi) < 0.06: hi = shi
        if kind != "door" and (lo < slo - Q or hi > shi + Q):     # doors keep their width and slide (below)
            notes.append(f"{kind} {a}/{b}: span {lo:.3f}-{hi:.3f} clipped to its wall {slo:.3f}-{shi:.3f}")
            lo, hi = max(lo, slo), min(hi, shi)
        conflict = None
        if kind == "door":      # trim clearance: slide (keeping the width) until a casing fits beside each end
            elo = max(x[2] for x in (fa, fb) if x) + CASING; ehi = min(x[3] for x in (fa, fb) if x) - CASING
            shift = max(0.0, elo - lo) - max(0.0, hi - ehi)
            if abs(shift) > MAX_SLIDE:     # more than a casing plus a snap: the door's place and a wall disagree
                conflict = f"door {a}/{b}: needs {shift / 0.0254:+.1f} in to clear its trim; NOT slid (its position is measured): a decision"
                notes.append("CONFLICT " + conflict)
            elif abs(shift) > Q:
                notes.append(f"door {a}/{b}: slid {shift / 0.0254:+.1f} in so its trim clears the side wall"); lo, hi = lo + shift, hi + shift
        # an open side or a rail is open only up to the ceiling: above it the ceiling runs on (a slit there showed the sky)
        top = min([by[n]["ceil"] for n in (a, b) if n in by] or [99.0])
        cuts = {"door": [(0.0, d["height"])], "arch": [(0.0, d.get("height") or ARCH_HEAD)], "open": [(0.0, top)], "rail": [(0.0, top)], "fake_door": []}[kind]
        out.append({"kind": kind, "between": [a, b], "axis": axis, "c": c, "lo": q(lo), "hi": q(hi), "cuts": cuts,
                    "height": d.get("height"), "spring": d.get("spring"), "cased": d.get("cased", False), "faces": [x[1] for x in (fa, fb) if x], "conflict": conflict})
    for w in floor_spec.get("windows") or []:
        axis = "z" if w["wall_axis"] == "z" else "x"; lo, hi = w["span_spec"]
        f = face_of(by[w["room"]], axis, w["wall_coord_spec"], lo, hi) if w["room"] in by else None
        if f is None:
            notes.append(f"window {w['room']}/{w.get('name')}: no snapped wall"); continue
        out.append({"kind": "window", "between": [w["room"]], "axis": axis, "c": q(f[0] + f[1] * WALL / 2), "lo": q(lo), "hi": q(hi),
                    "cuts": [(w["sill_m"], w["head_m"])], "sill": w["sill_m"], "head": w["head_m"], "faces": [f[1]], "name": w.get("name")})
    return out, notes


# ---------- 3. cells ----------
def inside(poly, x, z):
    c = np.zeros(np.broadcast(x, z).shape, bool)
    for (x1, z1), (x2, z2) in zip(poly, poly[1:] + poly[:1]):
        cr = (z1 > z) != (z2 > z)
        with np.errstate(divide="ignore", invalid="ignore"):
            xi = x1 + (z - z1) * (x2 - x1) / (z2 - z1)
        c ^= cr & (x < xi)
    return c


def cheb(poly, x, z):
    """Chebyshev distance from points to a rectilinear polygon's boundary."""
    d = np.full(np.broadcast(x, z).shape, np.inf)
    for (x1, z1), (x2, z2) in zip(poly, poly[1:] + poly[:1]):
        if abs(x1 - x2) < Q:     # x = const, z from lo to hi
            lo, hi = min(z1, z2), max(z1, z2); dd = np.maximum(np.abs(x - x1), np.maximum(np.maximum(lo - z, 0), z - hi))
        else:
            lo, hi = min(x1, x2), max(x1, x2); dd = np.maximum(np.abs(z - z1), np.maximum(np.maximum(lo - x, 0), x - hi))
        d = np.minimum(d, dd)
    return d


def cells(rooms, shafts=(), ops=(), extra=((), ())):
    """Cell grid for one storey. Returns xs, zs (cell edges), kind[i, j] (0 out, 1 room, 2 wall, 3 shaft), owner[i, j]
    (room index for room cells), top[i, j] (wall top = highest ceiling among the rooms it bounds)."""
    xs = {q(v) for r in rooms for p in r["poly"] for v in (p[0], p[0] - WALL, p[0] + WALL)}
    zs = {q(v) for r in rooms for p in r["poly"] for v in (p[1], p[1] - WALL, p[1] + WALL)}
    for s in shafts:
        xs |= {q(v) for v in s["x"]}; zs |= {q(v) for v in s["z"]}
    xs |= {q(v) for v in extra[0]}; zs |= {q(v) for v in extra[1]}   # lines from the other storey (the stairwell's edges, the landing)
    for o in ops:
        across, along = (xs, zs) if o["axis"] == "x" else (zs, xs)
        across |= {q(o["c"] - WALL / 2), q(o["c"] + WALL / 2)}; along |= {o["lo"], o["hi"]}
    xs, zs = np.array(sorted(xs)), np.array(sorted(zs))
    cx, cz = np.meshgrid((xs[:-1] + xs[1:]) / 2, (zs[:-1] + zs[1:]) / 2, indexing="ij")
    kind = np.zeros(cx.shape, int); owner = np.full(cx.shape, -1); top = np.zeros(cx.shape)
    for k, r in enumerate(rooms):
        m = inside(r["poly"], cx, cz) & (kind == 0)
        kind[m] = 1; owner[m] = k
    for k, r in enumerate(rooms):
        near = (kind != 1) & ~inside(r["poly"], cx, cz) & (cheb(r["poly"], cx, cz) <= WALL + Q)
        kind[near] = 2; top[near] = np.maximum(top[near], r["ceil"])
    for s in shafts:
        m = (cx > s["x"][0]) & (cx < s["x"][1]) & (cz > s["z"][0]) & (cz < s["z"][1])
        kind[m & (kind != 1)] = 3
    return xs, zs, kind, owner, top


def merge(mask, xs, zs, key=None):
    """Greedy merge of mask cells into maximal rectangles (runs along z, then stacked along x); cells of different key
    never merge. Returns [(x0, x1, z0, z1, key)]."""
    key = np.zeros(mask.shape) if key is None else key
    runs = []   # per x row: list of (j0, j1, key)
    for i in range(mask.shape[0]):
        row, j = [], 0
        while j < mask.shape[1]:
            if mask[i, j]:
                j0 = j
                while j + 1 < mask.shape[1] and mask[i, j + 1] and key[i, j + 1] == key[i, j0]:
                    j += 1
                row.append((j0, j, key[i, j0]))
            j += 1
        runs.append(row)
    out, open_ = [], {}
    for i, row in enumerate(runs + [[]]):
        now = {(j0, j1, k) for j0, j1, k in row}
        for r in list(open_):
            if r not in now:
                i0 = open_.pop(r); out.append((xs[i0], xs[i], zs[r[0]], zs[r[1] + 1], r[2]))
        for r in now:
            open_.setdefault(r, i)
    return out


# ---------- 5. checks ----------
def voids(kind):
    """OUT cells not connected to the outside of the bounding grid: holes inside the building."""
    out = kind == 0
    seen = np.zeros_like(out); stack = [(i, j) for i in range(out.shape[0]) for j in (0, out.shape[1] - 1) if out[i, j]]
    stack += [(i, j) for j in range(out.shape[1]) for i in (0, out.shape[0] - 1) if out[i, j]]
    while stack:
        i, j = stack.pop()
        if seen[i, j] or not out[i, j]:
            continue
        seen[i, j] = True
        stack += [(a, b) for a, b in ((i + 1, j), (i - 1, j), (i, j + 1), (i, j - 1)) if 0 <= a < out.shape[0] and 0 <= b < out.shape[1]]
    return out & ~seen


SLOT = 0.30          # m: outside space narrower than this between two parts of the building is a slot (a gap)


def slots(kind, xs, zs):
    """OUT cells in a run of OUT narrower than SLOT bounded by building at both ends, along x or along z: a notch or slit
    open to the outside (a void check misses those, because they connect to the outside)."""
    out = kind == 0; hit = np.zeros_like(out)
    for axis, edges in ((0, xs), (1, zs)):
        w = np.diff(edges)
        o = out if axis == 0 else out.T
        h = hit if axis == 0 else hit.T
        for j in range(o.shape[1]):
            i = 0
            while i < o.shape[0]:
                if not o[i, j]:
                    i += 1; continue
                i0 = i
                while i < o.shape[0] and o[i, j]:
                    i += 1
                if i0 > 0 and i < o.shape[0] and w[i0:i].sum() < SLOT - wg_Q:
                    h[i0:i, j] = True
    return hit


wg_Q = Q


def touches(region, seed):
    """Cells of region connected (4-neighbour, through region) to a cell adjacent to seed."""
    grow = np.zeros_like(region)
    for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        grow |= np.roll(seed, (a, b), (0, 1))
    hit = region & grow
    while True:
        nxt = hit.copy()
        for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nxt |= np.roll(hit, (a, b), (0, 1)) & region
        if (nxt == hit).all():
            return hit
        hit = nxt


def build(spec, dec):
    E = snap(spec, dec)
    rooms = snapped_rooms(spec, E)
    geo, report = {}, []
    for floor, rs in rooms.items():
        shafts = [d["shaft"] for d in dec if d.get("shaft", {}).get("floor") == floor]
        ops, onotes = openings(spec[floor], rs)
        extra = ((), ())
        if floor == "ground":   # cut the ground grid on the stairwell's edges and the landing, so ceilings and walls stop exactly there
            wells = [r for r in rooms["upstairs"] if r.get("opens") == "down"]
            L = next(b for b in spec["upstairs"]["stair"]["boxes"] if b["kind"] == "landing")
            extra = ([p[0] for r in wells for p in r["poly"]] + L["x"], [p[1] for r in wells for p in r["poly"]] + L["z"])
        xs, zs, kind, owner, top = cells(rs, shafts, ops, extra)
        v = voids(kind)
        chase = v & touches(v, kind == 3)   # the pocket around a declared shaft is solid wall (a chase), not a gap
        kind[chase] = 2; top[chase] = max(r["ceil"] for r in rs if r["kind"] != "opening")
        # heights: a ceiling slab sits on each room (stopping under the floor above); a wall rises to the highest slab top
        # of the rooms it bounds, then the openings through it are cut out as y-intervals
        cap = (spec["upstairs"]["stair"]["floor_to_floor_m"] - FLOOR_T) if floor == "ground" else 99.0
        ctop = lambda r: min(r["ceil"] + CEIL_T, cap)
        cx, cz = (xs[:-1] + xs[1:]) / 2, (zs[:-1] + zs[1:]) / 2
        wtop = np.zeros(kind.shape)
        for r in rs:
            near = (kind == 2) & (cheb(r["poly"], cx[:, None], cz[None, :]) <= WALL + Q)
            wtop[near] = np.maximum(wtop[near], ctop(r))
        wtop[(kind == 2) & (wtop == 0)] = max(ctop(r) for r in rs if r["kind"] != "opening")   # chase cells
        # the stair hall (phase 5): the landing is a slab inside it. Walls under the landing stop at its underside; walls along
        # its ends and back bound the stair hall above it, so they rise to the floor above (two storeys: the stairwell's walls
        # stand on them). Ceilings of the rooms under it stop at its underside; no ground ceiling under the open stairwell.
        under = np.zeros(kind.shape, bool); hall = np.zeros(kind.shape, bool); l_under = 99.0; ring_rooms = np.zeros(kind.shape, bool)
        if floor == "ground":
            F = spec["upstairs"]["stair"]["floor_to_floor_m"]
            L = next(b for b in spec["upstairs"]["stair"]["boxes"] if b["kind"] == "landing")
            lx, lz, l_under = L["x"], L["z"], q(L["y"][0] + F)
            X, Z = cx[:, None], cz[None, :]
            under = (X > lx[0]) & (X < lx[1]) & (Z > lz[0]) & (Z < lz[1])
            ring = (kind == 2) & ~under & (X > lx[0] - WALL - Q) & (X < lx[1]) & (Z > lz[0] - WALL - Q) & (Z < lz[1] + WALL + Q)
            wtop[(kind == 2) & under] = np.minimum(wtop[(kind == 2) & under], l_under)
            wtop[ring] = cap
            ring_rooms = (kind == 1) & ~under & (X > lx[0] - WALL - Q) & (X < lx[1]) & (Z > lz[0] - WALL - Q) & (Z < lz[1] + WALL + Q) \
                & ((X < lx[0]) | (Z < lz[0]) | (Z > lz[1]))
            for r in rooms["upstairs"]:
                if r.get("opens") == "down":
                    hall |= inside(r["poly"], X, Z)
        # upstairs walls around the stairwell stand down through the floor plate onto the stair hall's walls below (elsewhere the
        # plate runs under them: a wall there is never seen with the one below it)
        through = np.zeros(kind.shape, bool)
        if floor == "upstairs":
            for r in rs:
                if r.get("opens") == "down":
                    through |= (kind == 2) & (cheb(r["poly"], cx[:, None], cz[None, :]) <= WALL + Q)
        keys = np.empty(kind.shape, object)
        for i in range(kind.shape[0]):
            for j in range(kind.shape[1]):
                if kind[i, j] != 2:
                    continue
                # upstairs walls stand down through the floor plate onto the walls below (a 20 cm band of plate showed across the
                # two-storey stair-hall walls); the plate is the rooms' cells only
                iv = [(-FLOOR_T if through[i, j] else 0.0, wtop[i, j])]
                corner = [o for o in ops if o["kind"] == "rail" and abs((cx[i] if o["axis"] == "x" else cz[j]) - o["c"]) < WALL / 2
                          and o["lo"] - WALL < (cz[j] if o["axis"] == "x" else cx[i]) < o["hi"] + WALL]
                if len({o["axis"] for o in corner}) == 2:   # where two rails meet at a corner: open like the rails (a post stood there)
                    iv = [p for a, b in iv for p in ((a, min(b, 0.0)), (max(a, corner[0]["cuts"][0][1]), b)) if p[1] - p[0] > Q]
                for o in ops:
                    x, z = cx[i], cz[j]
                    along, across = (z, x) if o["axis"] == "x" else (x, z)
                    if o["lo"] < along < o["hi"] and abs(across - o["c"]) < WALL / 2:
                        for c0, c1 in o["cuts"]:
                            iv = [p for a, b in iv for p in ((a, min(b, c0)), (max(a, c1), b)) if p[1] - p[0] > Q]
                keys[i, j] = tuple((round(a, 4), round(b, 4)) for a, b in iv)
        walls = [w for w in merge(kind == 2, xs, zs, key=keys) if w[4]]
        # a wall strip left above a rail's cut lies in the ceiling's thickness: it is ceiling, not wall (it showed as a wallpaper
        # slit across the upstairs hall ceiling, user notes Oct 15 16:54 and 23:01)
        rail_tops = {round(o["cuts"][0][1], 4): o for o in ops if o["kind"] == "rail" and o["cuts"]}
        band_ceils = []
        walls = [list(w) for w in walls]
        for w in walls:
            keep = []
            for a, b in w[4]:
                o = rail_tops.get(round(a, 4))
                if o is not None and b - a <= CEIL_T + Q:
                    band_ceils.append({"room": o["between"][0], "x": [w[0], w[1]], "z": [w[2], w[3]], "y": [a, b], "band": True})
                else:
                    keep.append((a, b))
            w[4] = tuple(keep)
        walls = [w for w in walls if w[4]]
        if floor == "ground":   # the stair hall's wall above a room that reaches in beside the landing (above its ceiling slab)
            rkey = np.empty(kind.shape, object)
            for i, j in zip(*np.nonzero(ring_rooms)):
                rkey[i, j] = ((round(ctop(rs[owner[i, j]]), 4), round(cap, 4)),)
            walls += [w for w in merge(ring_rooms, xs, zs, key=rkey) if w[4]]
        # the floor plate, split by room so each piece carries its room's finish (a separate finish layer z-fought the plate and,
        # cut from the ceilings, laid a lid over the stairwell); wall cells are their own pieces (key -1); no floor in a well
        fmask = ((kind == 1) & ~np.isin(owner, [k for k, r in enumerate(rs) if r.get("opens") == "down"])) | ((kind == 2) & ~through)
        floor_rects = merge(fmask, xs, zs, key=np.where(kind == 1, owner, -1))
        # every space has a ceiling except an attic stair (it rises through it); a stairwell's is the storey's ceiling over the well
        has_ceil = (kind == 1) & np.isin(owner, [k for k, r in enumerate(rs) if r.get("opens") != "up"]) & ~(hall & ~under)
        ceil_rects = merge(has_ceil, xs, zs, key=owner * 2 + under)
        v = voids(kind)
        vrects = merge(v, xs, zs)
        slivers = [w for w in walls if min(w[1] - w[0], w[3] - w[2]) < SLIVER - Q]
        report += [f"   {n}" for n in onotes]
        srects = merge(slots(kind, xs, zs), xs, zs)
        geo[floor] = {"rooms": rs, "floor_y": spec[floor].get("floor_y_m", 0.0), "openings": ops,
                      "walls": [{"x": [w[0], w[1]], "z": [w[2], w[3]], "y": list(iv)} for w in walls for iv in w[4]],
                      "floor": [{"x": [r[0], r[1]], "z": [r[2], r[3]], "y": [-FLOOR_T, 0.0], "room": rs[int(r[4])]["name"] if r[4] >= 0 else None,
                                 "finish": (rs[int(r[4])]["kind"] if r[4] >= 0 else "wall")} for r in floor_rects],
                      "ceilings": [{"room": rs[int(r[4]) // 2]["name"], "x": [r[0], r[1]], "z": [r[2], r[3]],
                                    "y": [rs[int(r[4]) // 2]["ceil"], min(ctop(rs[int(r[4]) // 2]), l_under) if int(r[4]) % 2 else ctop(rs[int(r[4]) // 2])]}
                                   for r in ceil_rects] + band_ceils,
                      "voids": [{"x": [r[0], r[1]], "z": [r[2], r[3]]} for r in vrects], "shafts": shafts,
                      "slots": [{"x": [r[0], r[1]], "z": [r[2], r[3]]} for r in srects]}
        area = lambda R: sum((r[1] - r[0]) * (r[3] - r[2]) for r in R)
        report.append(f"{floor}: {len(rs)} spaces, {len(walls)} wall boxes, voids {len(vrects)} ({area(vrects):.2f} m2), "
                      f"slivers {len(slivers)}, slots {len(srects)}, shafts {len(shafts)}")
        for r in sorted(vrects, key=lambda r: -(r[1] - r[0]) * (r[3] - r[2]))[:8]:
            report.append(f"   VOID x {r[0]:.3f}-{r[1]:.3f}  z {r[2]:.3f}-{r[3]:.3f}  ({(r[1] - r[0]) / 0.0254:.1f} x {(r[3] - r[2]) / 0.0254:.1f} in)")
        for r in srects[:8]:
            report.append(f"   SLOT x {r[0]:.3f}-{r[1]:.3f}  z {r[2]:.3f}-{r[3]:.3f}  ({(r[1] - r[0]) / 0.0254:.1f} x {(r[3] - r[2]) / 0.0254:.1f} in)")
        for w in slivers[:8]:
            report.append(f"   SLIVER x {w[0]:.3f}-{w[1]:.3f}  z {w[2]:.3f}-{w[3]:.3f}")
    return geo, E, report


if __name__ == "__main__":
    spec, dec = load()
    geo, E, report = build(spec, dec)
    print("\n".join(report))
    if "--json" in sys.argv:
        (ROOT / "spec/geometry.json").write_text(json.dumps(geo))
        print("-> spec/geometry.json")
