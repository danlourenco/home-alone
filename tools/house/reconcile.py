"""Reconcile measured spaces into one clean, buildable floor spec (docs/RECONCILIATION.md, step 2).

Input: a traced, calibrated floor plan (measurements/overhead/<floor>-trace.plan.json), its doors/topology file, and
which spaces are SfM-measured anchors. Moves measurements as little as possible and logs every move:
  1. square: each wall becomes exactly axis-aligned (endpoints averaged)
  2. align: near-collinear walls of neighbouring spaces share one line (anchors weigh 5x, so measured rooms barely move)
  3. walls: thickness between facing spaces; too thin / too thick is flagged, not fixed
  4. doors: measured spans where available, else centred on the shared wall (flagged as topology-placed)
  5. rules: adult body passes every door and hall
Output: spec/house_spec.json (the only thing the Unity generator reads) and spec/<floor>-changes.md.
usage: uv run --with numpy python tools/house/reconcile.py
"""
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
PLAN = ROOT / "measurements/overhead/upstairs-trace.plan.json"
DOORS = ROOT / "measurements/overhead/upstairs-doors.json"
ANCHORS = {"parents_bedroom": "measurements/rooms/parents.json", "kevin_jeff_room": "measurements/rooms/kevin.json",
           "buzz_room": "measurements/rooms/buzz.json"}
ANCHOR_WEIGHT = 5.0
ALIGN_TOL = 0.12      # m: walls closer than this (and near each other along the line) become one line
ALIGN_REACH = 1.0     # m: ...if their extents are within this distance along the line
MAX_SPREAD = 0.20     # m: a cluster wider than this is a conflict, left unsnapped
WALL_MIN, WALL_MAX = 0.08, 0.50   # m: plausible wall thickness between facing spaces
FACE_MAX = 0.80       # m: facing edges farther apart than this are not one wall
DOOR_W, DOOR_H = 0.762, 2.032     # 30 x 80 in
ADULT = {"capsule_diameter": 0.55, "height": 1.85, "min_hall": 0.90}
CEILING_ASSUMED = 2.74  # 9 ft; not yet measured


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
            for ea in edges[a]:
                sa = outward_sign(polys[a], ea)
                for eb in edges[b]:
                    if ea[0] != eb[0]:
                        continue
                    sb = outward_sign(polys[b], eb)
                    if sa != -sb:
                        continue
                    gap = (eb[1] - ea[1]) * sa
                    lo, hi = max(ea[2], eb[2]), min(ea[3], eb[3])
                    if -0.05 < gap <= FACE_MAX and hi - lo > 0.3:
                        out.append({"a": a, "b": b, "axis": ea[0], "coord_a": ea[1], "coord_b": eb[1], "gap": gap, "lo": lo, "hi": hi})
    return out


def main():
    plan = json.loads(PLAN.read_text())
    topo = json.loads(DOORS.read_text())
    sp = {s["name"]: s for s in plan["spaces"]}
    raw = {n: np.array(s["polygon_m"]) for n, s in sp.items()}
    weights = {n: ANCHOR_WEIGHT if n in ANCHORS else 1.0 for n in sp}
    log = ["# Upstairs reconciliation log", "",
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
        if p["gap"] < WALL_MIN:
            note = "TOO THIN: rooms overlap or touch"; flags.append(f"wall {a}/{b} {p['gap'] * 100:.0f} cm: too thin")
        elif p["gap"] > WALL_MAX:
            note = "thick: chase, closet or measurement error"; flags.append(f"wall {a}/{b} {p['gap'] * 100:.0f} cm: thick")
        log.append(f"| {a} / {b} | {p['gap'] * 100:.0f} | {p['hi'] - p['lo']:.2f} | {note} |")

    # 4. doors
    doors, rules = [], []
    log += ["", "## 4. Doors and openings", "", "| between | kind | position along wall (m) | width (m) | placed from |", "|---|---|---|---|---|"]
    for d in topo["doors"]:
        key = tuple(sorted((d["a"], d["b"])))
        p = best.get(key)
        if not p:
            flags.append(f"door {d['a']}/{d['b']}: no shared wall found within {FACE_MAX} m"); continue
        wall_c = (p["coord_a"] + p["coord_b"]) / 2
        if d["kind"] in ("arch", "rail"):
            lo, hi, src = p["lo"], p["hi"], "full shared wall"
        elif "span" in d:
            lo, hi = sorted(d["span"]); src = "measured"
            if lo < p["lo"] or hi > p["hi"]:  # keep the measured width, slide it onto the wall
                shift = max(p["lo"] - lo, 0) - max(hi - p["hi"], 0)
                lo, hi = lo + shift, hi + shift
                src = f"measured, slid {shift * 100:+.0f} cm onto the shared wall"
                if abs(shift) > 0.15 or lo < p["lo"] - 1e-9 or hi > p["hi"] + 1e-9:
                    flags.append(f"door {d['a']}/{d['b']}: measured span needs {shift * 100:+.0f} cm to fit its wall")
        else:
            mid = (p["lo"] + p["hi"]) / 2; lo, hi = mid - DOOR_W / 2, mid + DOOR_W / 2; src = "topology (centred; position unverified)"
        w = hi - lo
        doors.append({"between": [d["a"], d["b"]], "kind": d["kind"], "wall_axis": "x" if p["axis"] == 0 else "y",
                      "wall_coord": round(wall_c, 3), "wall_thickness": round(p["gap"], 3), "span": [round(lo, 3), round(hi, 3)],
                      "width": round(w, 3), "height": DOOR_H if d["kind"] == "door" else None, "placed_from": src, "source": d["source"]})
        log.append(f"| {d['a']} / {d['b']} | {d['kind']} | {lo:.2f}-{hi:.2f} | {w:.2f} | {src} |")
        if d["kind"] == "door":
            rules.append((f"adult fits door {d['a']}/{d['b']}", w >= ADULT["capsule_diameter"] + 0.1 and DOOR_H >= ADULT["height"] + 0.1,
                          f"{w:.2f} m wide x {DOOR_H:.2f} m"))

    # 5. rules
    for n, s in sp.items():
        if s["kind"] == "hall":
            short = float(np.ptp(final[n], axis=0).min())
            rules.append((f"adult fits hall {n}", short >= ADULT["min_hall"], f"narrowest {short:.2f} m"))
    log += ["", "## 5. Body rules (adult, hard)", "", "| rule | result | value |", "|---|---|---|"]
    for r, ok, v in rules:
        log.append(f"| {r} | {'pass' if ok else 'FAIL'} | {v} |")
        if not ok:
            flags.append(f"rule failed: {r} ({v})")

    log += ["", "## Flags (need a decision or more evidence)", ""] + [f"- {f}" for f in flags] + \
           [f"- unresolved: {u}" for u in topo.get("unresolved", [])] + \
           [f"- ceiling height {CEILING_ASSUMED} m is ASSUMED (not measured)"]

    # spec: x = across (plan y), z = along (plan x), origin at the outline's min corner, y up
    allp = np.vstack(list(final.values()))
    o = allp.min(0)
    to_spec = lambda P: [[round(float(y - o[1]), 3), round(float(x - o[0]), 3)] for x, y in P]
    spec = {
        "version": 1, "level": "upstairs", "units": "metres",
        "frame": "x = across the overhead (right), z = down the overhead; origin = min corner of all spaces; y up. "
                 "Front facade is the +x side (parents' room / Kevin / hall bath / Buzz row).",
        "scale": {"door_height_m": DOOR_H, "door_range_in": [78, 80], "note": "80 in nominal; area check brackets 78-80 in"},
        "ceiling_height_m": {"value": CEILING_ASSUMED, "assumed": True},
        "bodies": {"kevin": {"eye_height": 1.1, "crawl_height": 0.4}, "bandit": {"eye_height": 1.7, "crouch_height": 1.1, **ADULT}},
        "spaces": [{"name": n, "kind": sp[n]["kind"], "anchor": n in ANCHORS, "polygon_xz": to_spec(final[n]),
                    "area_m2": round(area(final[n]), 2)} for n in sp],
        "doors": [{**d, "wall_coord_spec": round(d["wall_coord"] - o[0 if d["wall_axis"] == "x" else 1], 3),
                   "span_spec": [round(v - o[1 if d["wall_axis"] == "x" else 0], 3) for v in d["span"]],
                   "spec_axis": "z" if d["wall_axis"] == "x" else "x"} for d in doors],
        "flags": flags,
        "sources": {"plan": str(PLAN.relative_to(ROOT)), "doors": str(DOORS.relative_to(ROOT)), "anchors": ANCHORS},
    }
    (ROOT / "spec").mkdir(exist_ok=True)
    (ROOT / "spec/house_spec.json").write_text(json.dumps(spec, indent=1) + "\n")
    (ROOT / "spec/upstairs-changes.md").write_text("\n".join(log) + "\n")
    print("\n".join(log))


if __name__ == "__main__":
    sq = rebuild(edges_of(np.array([[0, 0], [0.02, 3], [2, 3.03], [1.98, 0.01]])))
    assert (np.diff(np.vstack([sq, sq[:1]]), axis=0) == 0).any(1).all(), "squared walls must be axis-aligned"
    assert np.allclose(np.ptp(sq, axis=0), [1.98, 3.01])
    main()
