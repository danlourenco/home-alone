"""Wall-grid PREVIEW (tasks/wall-grid-plan.md, before phase 1): propose the shared wall lines for both floors and report
how far every wall would move. Changes nothing; writes spec/captures/wall-grid/preview.json and the review page preview.html.

A room edge is a wall face; the current builder puts the wall's centreline HalfWall (0.07 m) outside it. Centrelines on
one axis and floor are clustered (union-find) when they are within SNAP_TOL and connected: their extents overlap or nearly
meet along the line (REACH). Across floors nothing is snapped: lines within STACK_TOL whose extents overlap are listed as
stacking CANDIDATES for the user to accept or reject (the plan's designated stacks). A cluster's line is the weighted mean (anchored rooms
x5). Spread > MAX_SPREAD = a conflict, not snapped.
usage: uv run --with numpy python -I tools/house/wall_grid_preview.py
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HALF, SNAP_TOL, REACH, MAX_SPREAD, STACK_TOL = 0.07, 0.10, 1.0, 0.20, 0.30
ANCHORED = {"parents_bedroom", "kevin_jeff_room", "buzz_room"}   # SfM-measured (reconcile.py ANCHORS)


def inside(poly, x, z):
    c = False
    for (x1, z1), (x2, z2) in zip(poly, poly[1:] + poly[:1]):
        if (z1 > z) != (z2 > z) and x < x1 + (z - z1) * (x2 - x1) / (z2 - z1):
            c = not c
    return c


def edges(floor, spec):
    out = []
    for s in spec["spaces"]:
        P = s["polygon_xz"]
        for (x1, z1), (x2, z2) in zip(P, P[1:] + P[:1]):
            axis = "x" if abs(x1 - x2) < 1e-4 else "z"      # "x": the line x = const (runs along z)
            c, lo, hi = (x1, min(z1, z2), max(z1, z2)) if axis == "x" else (z1, min(x1, x2), max(x1, x2))
            if hi - lo < 0.02:
                continue
            m = (lo + hi) / 2
            probe = (c + 0.02, m) if axis == "x" else (m, c + 0.02)
            out_sgn = -1 if inside(P, *probe) else 1
            out.append({"floor": floor, "room": s["name"], "kind": s["kind"], "axis": axis, "face": round(c, 4),
                        "centre": round(c + out_sgn * HALF, 4), "out": out_sgn, "lo": lo, "hi": hi,
                        "w": 5.0 if s["name"] in ANCHORED else 1.0})
    return out


def cluster(E):
    parent = list(range(len(E)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]; i = parent[i]
        return i
    for i, a in enumerate(E):
        for j in range(i + 1, len(E)):
            b = E[j]
            if a["axis"] != b["axis"] or a["floor"] != b["floor"] or abs(a["centre"] - b["centre"]) > SNAP_TOL:
                continue
            if max(a["lo"], b["lo"]) - min(a["hi"], b["hi"]) <= REACH:
                parent[find(i)] = find(j)
    groups = {}
    for i in range(len(E)):
        groups.setdefault(find(i), []).append(i)
    lines = []
    for k, idx in enumerate(groups.values()):
        cs = [E[i]["centre"] for i in idx]
        spread = max(cs) - min(cs)
        line = sum(E[i]["centre"] * E[i]["w"] for i in idx) / sum(E[i]["w"] for i in idx)
        conflict = spread > MAX_SPREAD
        for i in idx:
            E[i]["line"] = k
            E[i]["snap"] = 0.0 if conflict else round(line - E[i]["centre"], 4)
        lines.append({"id": k, "axis": E[idx[0]]["axis"], "coord": round(line, 4), "spread": round(spread, 4), "conflict": conflict,
                      "floors": sorted({E[i]["floor"] for i in idx}), "members": len(idx),
                      "lo": min(E[i]["lo"] for i in idx), "hi": max(E[i]["hi"] for i in idx)})
    return lines


SHELL_C, SHELL_D, GLB_M = 11.06, 8.76, 2.032 / 2.625   # shell_fit.py (ground-floor fit): GLB X = c - spec z, Y = d - spec x; 0.774 m/unit
GLB_GROUND_Z = 1.3                                       # native height of the GLB's ground floor (sept_census FLOORS)


def shell(rooms, ground_y):
    """The downloaded model as triangles in spec coordinates, its interior dropped (a triangle whose centre lies inside a
    built room, between that room's floor and ceiling), so the exterior and roof remain. Base64 float32 [x, y, z] x 3."""
    import base64
    import numpy as np
    T = np.load(ROOT / "art/home_alone/references/glb-audit/triangles.npz")["triangles"].astype(float)
    X, Y = T[..., 0] * GLB_M, T[..., 1] * GLB_M
    spec = np.stack([SHELL_D - Y, (T[..., 2] - GLB_GROUND_Z) * GLB_M + ground_y, SHELL_C - X], -1)   # (x, y, z)
    c = spec.mean(1)
    keep = (np.abs(X).max(1) < 14 * 1.0) & (Y.min(1) > -4) & (Y.max(1) < 16)   # the house, not the site (glb_section)
    for r in rooms:
        if r["kind"] == "opening":
            continue
        P = r["poly"]; ins = np.zeros(len(c), bool)
        for (x1, z1), (x2, z2) in zip(P, P[1:] + P[:1]):
            cross = (z1 > c[:, 2]) != (z2 > c[:, 2])
            xi = x1 + (c[:, 2] - z1) * (x2 - x1) / ((z2 - z1) or 1e-9)
            ins ^= cross & (c[:, 0] < xi)
        band = (c[:, 1] > r["y"] + 0.02) & (c[:, 1] < r["y"] + r["ceil"] - 0.02)
        keep &= ~(ins & band)
    S = spec[keep].astype(np.float32)
    return base64.b64encode(S.tobytes()).decode(), int(keep.sum())


def odd_walls(E, t=2 * HALF):
    """Facing faces of two spaces on one floor (opposite sides of one wall) whose separation AFTER the grid is not the
    built thickness: a wall thicker or thinner than 14 cm, which the grid did not fix (e.g. a near-miss just past SNAP_TOL)."""
    out = []
    for i, a in enumerate(E):
        for b in E[i + 1:]:
            if a["floor"] != b["floor"] or a["axis"] != b["axis"] or a["room"] == b["room"] or a["out"] != -b["out"]:
                continue
            lo, hi = max(a["lo"], b["lo"]), min(a["hi"], b["hi"])
            fa, fb = a["face"] + a["snap"], b["face"] + b["snap"]
            sep = (fb - fa) * a["out"]                          # positive when b lies beyond a's outward side
            if hi - lo < 0.2 or not (0.03 < sep < 0.60) or abs(sep - t) < 0.01:
                continue
            out.append({"floor": a["floor"], "axis": a["axis"], "rooms": [a["room"], b["room"]], "a": fa, "b": fb,
                        "lo": lo, "hi": hi, "thickness": round(sep, 4), "excess": round(sep - t, 4)})
    return out


def main():
    up = json.loads((ROOT / "spec/house_spec.json").read_text()); gr = json.loads((ROOT / "spec/house_spec.ground.json").read_text())
    E = edges("upstairs", up) + edges("ground", gr)
    lines = cluster(E)
    odd = odd_walls(E)
    stacks = [{"up": u["id"], "ground": g["id"], "axis": u["axis"], "up_coord": u["coord"], "ground_coord": g["coord"],
               "offset": round(u["coord"] - g["coord"], 4), "lo": max(u["lo"], g["lo"]), "hi": min(u["hi"], g["hi"])}
              for u in lines if u["floors"] == ["upstairs"] for g in lines if g["floors"] == ["ground"]
              if u["axis"] == g["axis"] and abs(u["coord"] - g["coord"]) <= STACK_TOL and min(u["hi"], g["hi"]) - max(u["lo"], g["lo"]) > 0.3]
    doors = [{"floor": f, "between": d["between"], "kind": d["kind"], "axis": d["spec_axis"],   # spec_axis names the wall's constant coordinate (SpecGreybox: alongX = spec_axis == "z")
              "coord": d["wall_coord_spec"], "span": d["span_spec"]} for f, sp in (("upstairs", up), ("ground", gr)) for d in sp["doors"]]
    rooms = [{"floor": f, "name": s["name"], "kind": s["kind"], "poly": s["polygon_xz"], "ceil": s["ceiling_m"], "y": sp.get("floor_y_m", 0.0)}
             for f, sp in (("upstairs", up), ("ground", gr)) for s in sp["spaces"]]
    stair = [b for b in up["stair"]["boxes"] if b["kind"] in ("step", "landing")]
    shell_b64, shell_n = shell(rooms, gr["floor_y_m"])
    sys.path.insert(0, str(ROOT / "tools/house")); import wall_graph as wg   # the rebuild as it stands (tasks/wall-grid-plan.md phase 2): snapped rooms, wall boxes, openings
    geo, _, geo_report = wg.build(*wg.load())
    after = {f: {"rooms": g["rooms"], "walls": g["walls"], "openings": [{k: o[k] for k in ("kind", "axis", "c", "lo", "hi", "between")} for o in g["openings"]],
                 "floor_y": g["floor_y"]} for f, g in geo.items()}
    out = ROOT / "spec/captures/wall-grid"; out.mkdir(parents=True, exist_ok=True)
    (out / "preview.json").write_text(json.dumps({"params": {"half_wall": HALF, "snap_tol": SNAP_TOL, "reach": REACH, "max_spread": MAX_SPREAD},
                                                  "rooms": rooms, "edges": E, "lines": lines, "stacks": stacks, "odd": odd, "after": after, "after_report": geo_report, "shell": shell_b64, "shell_fit": "tools/house/shell_fit.py: ground-floor fit, IoU 0.77 ground / 0.65 upstairs", "doors": doors, "stair": stair}, indent=0))
    html = (ROOT / "tools/house/wall_grid_preview.template.html").read_text()
    (out / "preview.html").write_text(html.replace("__DATA__", (out / "preview.json").read_text().replace("</", "<\\/")))
    moved = sorted((e for e in E if abs(e["snap"]) > 0.0005), key=lambda e: -abs(e["snap"]))
    print(f"{len(E)} wall faces -> {len(lines)} lines ({sum(l['conflict'] for l in lines)} conflicts); "
          f"{len(moved)} faces move: {sum(abs(e['snap']) > 0.04 for e in moved)} over 1.5 in, {sum(abs(e['snap']) > 0.10 for e in moved)} over 4 in")
    print(f"{len(odd)} walls not 14 cm thick after the grid:")
    for o in sorted(odd, key=lambda o: -abs(o["excess"])):
        print(f"  {o['floor']:8s} {o['rooms'][0]} / {o['rooms'][1]}: {o['thickness'] / 0.0254:.1f} in thick ({o['excess'] / 0.0254:+.1f}) over {o['hi'] - o['lo']:.2f} m")
    print(f"shell: {shell_n} triangles kept (exterior and roof)")
    print(f"{len(stacks)} cross-floor stacking candidates (within {STACK_TOL} m, overlapping >0.3 m):")
    for k in sorted(stacks, key=lambda k: abs(k["offset"])):
        print(f"  {k['axis']}: upstairs {k['up_coord']:.3f} vs ground {k['ground_coord']:.3f} ({k['offset'] / 0.0254:+.1f} in) over {k['hi'] - k['lo']:.2f} m")
    for e in moved[:15]:
        print(f"  {e['floor']:8s} {e['room']:20s} {e['axis']}={e['face']:.3f} moves {e['snap'] / 0.0254:+.1f} in")
    print("->", (out / "preview.json").relative_to(ROOT))


if __name__ == "__main__":
    # self-check: two rooms 3 cm off one wall line share it; a room 30 cm off does not
    t = [{"axis": "x", "centre": c, "lo": 0, "hi": 2, "w": 1.0, "floor": "f"} for c in (1.0, 1.03, 1.30)]
    L = cluster(t)
    assert t[0]["line"] == t[1]["line"] != t[2]["line"] and abs(t[0]["snap"] - 0.015) < 1e-9, t
    main()
