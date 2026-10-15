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


def q(v):
    return float(np.round(np.asarray(v) / Q) * Q)


def load():
    up = json.loads((ROOT / "spec/house_spec.json").read_text()); gr = json.loads((ROOT / "spec/house_spec.ground.json").read_text())
    dec = json.loads((ROOT / "measurements/grid-snaps.json").read_text())["decisions"]
    return {"upstairs": up, "ground": gr}, dec


# ---------- 1. grid ----------
def snap(spec, dec):
    E = wgp.edges("upstairs", spec["upstairs"]) + wgp.edges("ground", spec["ground"])
    wgp.cluster(E)
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


def cells(rooms, shafts=()):
    """Cell grid for one storey. Returns xs, zs (cell edges), kind[i, j] (0 out, 1 room, 2 wall, 3 shaft), owner[i, j]
    (room index for room cells), top[i, j] (wall top = highest ceiling among the rooms it bounds)."""
    xs = {q(v) for r in rooms for p in r["poly"] for v in (p[0], p[0] - WALL, p[0] + WALL)}
    zs = {q(v) for r in rooms for p in r["poly"] for v in (p[1], p[1] - WALL, p[1] + WALL)}
    for s in shafts:
        xs |= {q(v) for v in s["x"]}; zs |= {q(v) for v in s["z"]}
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
        xs, zs, kind, owner, top = cells(rs, shafts)
        walls = merge(kind == 2, xs, zs, key=top)
        v = voids(kind)
        chase = v & touches(v, kind == 3)   # the pocket around a declared shaft is solid wall (a chase), not a gap
        kind[chase] = 2; top[chase] = max(r["ceil"] for r in rs if r["kind"] != "opening")
        walls = merge(kind == 2, xs, zs, key=top)
        v = voids(kind)
        vrects = merge(v, xs, zs)
        slivers = [w for w in walls if min(w[1] - w[0], w[3] - w[2]) < SLIVER - Q]
        srects = merge(slots(kind, xs, zs), xs, zs)
        geo[floor] = {"rooms": rs, "walls": [{"x": [w[0], w[1]], "z": [w[2], w[3]], "top": w[4]} for w in walls],
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
