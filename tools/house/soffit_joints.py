"""soffit_joints: flight 2's plaster soffit meets its neighbours along every edge, by construction.

Why (user walk Oct 19 12:26 "does not connect", 14:49 "why is this soffit still not fixed?", shot 20261019-144917): the sloped soffit
under flight 2 stopped 11.5 cm under the foyer ceiling at the stair head (the dark tread undersides showed through the slot) and
its open-side edge stood 1 cm proud of a recessed infill, 7-9 cm under the stringer's bottom edge. Eye checks and the z-fight/clash
gates passed it twice; nothing tested that the edges touch anything.

The soffit is every sloped, downward-facing triangle of MainStair.glb's white part over flight 2's plan. Its boundary (edges used by
one soffit triangle) is sampled every 2 cm; each sample must lie within TOL of another drawn surface: the stair model's other
triangles (landing slab, stringer, head fascia) or a wall / ceiling / floor box of spec/geometry.json (the grey-box draws those).
Also: the soffit runs from flight 2's foot to its head, and clears the foyer->kitchen opening's head (DEVIATIONS 20).

Open sides (user note Oct 19 16:23 "the balusters appear to hang off the side ... would a builder do it this way?"): a cut-string stair
has ONE outer plane per open side, the rail band's outer edge (spec rail boxes): flight 1 z 10.17, the landing edge x 3.045, flight 2
and the gallery fascia z 9.23. The stringer's outer face, the landing's edge, the soffit's open edge and the gallery fascia must lie on
it (TOL), and every baluster's foot (all four corners of its block) must stand on a level drawn surface (a tread, the landing, the
gallery floor) within TOL: over air, it hangs off the side.

  uv run -q --with trimesh --with numpy python -I tools/house/soffit_joints.py [--glb PATH]     exit 1 on any gap
"""
import json
import sys
from pathlib import Path

import numpy as np
import trimesh

ROOT = Path(__file__).resolve().parents[2]
TOL = 0.003      # a gap the eye can't see under a white soffit at 2-4 m
STEP = 0.02


def soffit_and_neighbours(glb, S, geo):
    tris, part = load(glb)
    white = part == "RisersStringers"
    f2 = [b for b in S["boxes"] if b["name"].startswith("flight2_step")]
    x0, x1 = min(b["x"][0] for b in f2), max(b["x"][1] for b in f2)
    z0, z1 = min(b["z"][0] for b in f2), max(b["z"][1] for b in f2)
    n = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0]); area = np.linalg.norm(n, axis=1)
    ny = np.abs(n[:, 1]) / np.maximum(area, 1e-12); c = tris.mean(1)
    sof = white & (area > 1e-10) & (ny > 0.3) & (ny < 0.999) & (c[:, 0] > x0 - 0.01) & (c[:, 0] < x1 + 0.6) & (c[:, 2] > z0 - 0.01) & (c[:, 2] < z1 + 0.06)
    boxes = []
    for floor, keys in (("ground", ("walls", "ceilings")), ("upstairs", ("walls", "ceilings", "floor"))):
        G = geo[floor]
        boxes += [dict(b, y=[b["y"][0] + G["floor_y"], b["y"][1] + G["floor_y"]]) for k in keys for b in G[k]]
    for b in boxes:
        bx = trimesh.creation.box(bounds=[[b["x"][0], b["y"][0], b["z"][0]], [b["x"][1], b["y"][1], b["z"][1]]])
        tris = np.vstack([tris, bx.vertices[bx.faces]])
    keep = np.r_[~sof, np.ones(len(tris) - len(sof), bool)]
    return tris[:len(sof)][sof], tris[keep], (x0, x1, z0, z1)


def load(glb):
    """Every triangle of the model in spec metres, with its part (node) name."""
    sc = trimesh.load(glb, force="scene")
    tris, part = [], []
    for nd in sc.graph.nodes_geometry:
        T, g = sc.graph[nd]
        m = sc.geometry[g]
        v = m.vertices @ T[:3, :3].T + T[:3, 3]
        v = np.c_[-v[:, 0], v[:, 1], -v[:, 2]]            # glTF (+Y up, glTFast mirrors x) -> spec: (-gx, gy, -gz)
        tris.append(v[m.faces]); part += [nd.split(".")[0]] * len(m.faces)
    return np.vstack(tris), np.array(part)


def open_sides(glb, S, geo, st):
    """The outer planes of the open sides, and the balusters' feet."""
    tris, part = load(glb)
    B = {b["name"]: b for b in S["boxes"]}
    RB = [b for b in S["boxes"] if b["kind"] == "rail"]
    out1 = min(b["z"][0] for b in RB if b["name"].startswith("flight1_rail"))
    out2 = max(b["z"][1] for b in RB if b["name"].startswith("flight2_rail"))
    outl = B["landing_rail_cap"]["x"][1]
    L = B["landing"]; f1 = [b for b in S["boxes"] if b["name"].startswith("flight1_step")]; f2 = [b for b in S["boxes"] if b["name"].startswith("flight2_step")]
    white = tris[part == "RisersStringers"]
    w = white.reshape(-1, 3)
    centre = white.mean(1)
    normal = np.cross(white[:, 1] - white[:, 0], white[:, 2] - white[:, 0])
    area = np.linalg.norm(normal, axis=1)
    landing_face = white[(centre[:, 2] > out2 + 0.01) & (centre[:, 2] < out1 - 0.01) &
                         (centre[:, 1] > L["y"][0] - 0.01) & (centre[:, 1] < L["y"][1] + 0.01) &
                         (area > 1e-12) & (np.abs(normal[:, 0]) > 0.99 * area)]
    up = geo["upstairs"]
    def extreme(values, minimum=False):
        return (values.min() if minimum else values.max()) if len(values) else float("nan")
    planes = {   # name: (measured, wanted)
        "flight 2 stringer outer face (z)": (w[(w[:, 0] > min(b["x"][0] for b in f2) + 0.01) & (w[:, 0] < max(b["x"][1] for b in f2) - 0.01) & (w[:, 2] < 9.5)][:, 2].max(), out2),
        "flight 2 soffit open edge (z)": (st.reshape(-1, 3)[:, 2].max(), out2),
        "gallery fascia (z)": (max(b["z"][1] for b in up["walls"] if b["z"][1] - b["z"][0] < 0.1 and abs(b["z"][0] - min(b["z"][0] for b in RB if b["name"].startswith("flight2_rail"))) < 0.01), out2),
        "landing edge over the well (x)": (extreme(landing_face.reshape(-1, 3)[:, 0]), outl),
        "flight 1 stringer outer face (z)": (w[(w[:, 0] > max(b["x"][0] for b in f1 if b["name"] != "flight1_step12") - 0.3) & (w[:, 0] < B["flight1_step01"]["x"][0]) & (w[:, 2] < 10.5) & (w[:, 0] > B["flight1_step12"]["x"][0] + 0.01)][:, 2].min(), out1),
    }
    bad = [f"PLANE   {k}: {m:.3f}, the rail band's outer edge is {t:.3f} ({abs(m - t) * 1000:.0f} mm off; nan means missing surface)" for k, (m, t) in planes.items() if not np.isfinite(m) or abs(m - t) > TOL]
    if len(landing_face):
        # A single corner reaching the plane cannot certify the whole landing fascia.
        zs = np.linspace(out2, out1, int(np.ceil((out1 - out2) / STEP)) + 1)
        pts = np.array([(outl, y, z) for y in (L["y"][0], L["y"][1] - 0.025) for z in zs])
        q = trimesh.triangles.closest_point(np.repeat(landing_face[None], len(pts), 0).reshape(-1, 3, 3), np.repeat(pts, len(landing_face), 0))
        d = np.linalg.norm(q - np.repeat(pts, len(landing_face), 0), axis=1).reshape(len(pts), len(landing_face)).min(1)
        if d.max() > TOL:
            bad.append(f"PLANE   landing fascia coverage: {(d > TOL).sum()}/{len(d)} samples missing, worst {d.max() * 1000:.0f} mm")
    # baluster feet: the lowest horizontal square of each baluster (block 45 mm); support = a level non-baluster face under each corner
    bt = tris[part == "Balusters"]
    n = np.cross(bt[:, 1] - bt[:, 0], bt[:, 2] - bt[:, 0]); a = np.linalg.norm(n, axis=1)
    sq = bt[(a > 1e-12) & (np.abs(n[:, 1]) > 0.99 * a) & (np.abs(a / 2 - 0.045 ** 2 / 2) < 1e-6)]
    feet = {}
    for t in sq:
        k = tuple(np.round([t[:, 0].min(), t[:, 0].max(), t[:, 2].min(), t[:, 2].max()], 4))
        feet[k] = min(feet.get(k, 9e9), t[0, 1])
    if not feet:
        bad.append("HANGING no baluster feet found; support cannot be verified")
    sup = tris[part != "Balusters"]
    for g in ("ground", "upstairs"):
        G = geo[g]
        for b in G["floor"] + G["walls"]:
            y = b["y"][1] + G["floor_y"]; x0, x1, z0, z1 = b["x"][0], b["x"][1], b["z"][0], b["z"][1]
            sup = np.vstack([sup, [[[x0, y, z0], [x1, y, z0], [x1, y, z1]], [[x0, y, z0], [x1, y, z1], [x0, y, z1]]]])
    sn = np.cross(sup[:, 1] - sup[:, 0], sup[:, 2] - sup[:, 0]); sa = np.linalg.norm(sn, axis=1)
    lev = sup[(sa > 1e-12) & (np.abs(sn[:, 1]) > 0.999 * sa)]
    def held(x, y, z):
        c = lev[np.abs(lev[:, 0, 1] - y) <= TOL]
        if not len(c): return False
        p = np.array([x, z]); A, Bv, C = c[:, 0][:, [0, 2]], c[:, 1][:, [0, 2]], c[:, 2][:, [0, 2]]
        cr = lambda u, v, q: (v[:, 0] - u[:, 0]) * (q[1] - u[:, 1]) - (v[:, 1] - u[:, 1]) * (q[0] - u[:, 0])
        d1, d2, d3 = cr(A, Bv, p), cr(Bv, C, p), cr(C, A, p)
        return bool((((d1 >= -1e-9) & (d2 >= -1e-9) & (d3 >= -1e-9)) | ((d1 <= 1e-9) & (d2 <= 1e-9) & (d3 <= 1e-9))).any())
    off = []
    for (x0, x1, z0, z1), y in feet.items():
        e = 0.001   # a corner on a face's very edge counts
        loose = [(x, z) for x in (x0 + e, x1 - e) for z in (z0 + e, z1 - e) if not held(x, y, z)]
        if loose:
            off.append(f"({(x0 + x1) / 2:.3f}, {y:.3f}, {(z0 + z1) / 2:.3f}) {len(loose)}/4 corners over air")
    if off:
        bad.append(f"HANGING {len(off)} of {len(feet)} balusters not standing on a tread/landing/floor: " + "; ".join(off[:6]) + (" ..." if len(off) > 6 else ""))
    print(f"Open sides: {len(planes)} plane joints, {len(feet)} baluster feet checked")
    return bad


def boundary(st):
    """Edges used by exactly one soffit triangle (vertices welded at 0.1 mm)."""
    key = lambda p: tuple(np.round(p / 1e-4).astype(int))
    count, seg = {}, {}
    for t in st:
        for a, b in ((0, 1), (1, 2), (2, 0)):
            k = tuple(sorted((key(t[a]), key(t[b]))))
            count[k] = count.get(k, 0) + 1; seg[k] = (t[a], t[b])
    return [seg[k] for k, c in count.items() if c == 1]


def gaps(st, other):
    lo, hi = st.reshape(-1, 3).min(0) - 0.2, st.reshape(-1, 3).max(0) + 0.2
    near = other[((other.max(1) > lo) & (other.min(1) < hi)).all(1)]
    out = []
    for a, b in boundary(st):
        k = max(2, int(np.ceil(np.linalg.norm(b - a) / STEP)) + 1)
        pts = a + np.linspace(0, 1, k)[:, None] * (b - a)
        q = trimesh.triangles.closest_point(np.repeat(near[None], len(pts), 0).reshape(-1, 3, 3), np.repeat(pts, len(near), 0))
        d = np.linalg.norm(q - np.repeat(pts, len(near), 0), axis=1).reshape(len(pts), len(near)).min(1)
        if d.max() > TOL:
            i = int(d.argmax())
            out.append(f"GAP     soffit edge ({a[0]:.3f}, {a[1]:.3f}, {a[2]:.3f}) -> ({b[0]:.3f}, {b[1]:.3f}, {b[2]:.3f}): "
                       f"{int((d > TOL).sum())}/{len(d)} samples loose, worst {d[i] * 1000:.0f} mm at ({pts[i][0]:.3f}, {pts[i][1]:.3f}, {pts[i][2]:.3f})")
    return out


def main(glb):
    S = json.loads((ROOT / "spec/house_spec.json").read_text())["stair"]
    geo = json.loads((ROOT / "spec/geometry.json").read_text())
    st, other, (x0, x1, z0, z1) = soffit_and_neighbours(glb, S, geo)
    bad = []
    if not len(st):
        print("Soffit joints: no soffit under flight 2 in", glb); return 1
    v = st.reshape(-1, 3)
    if v[:, 0].min() > x0 + TOL or v[:, 0].max() < x1 - TOL:
        bad.append(f"SPAN    soffit runs x {v[:, 0].min():.3f}-{v[:, 0].max():.3f}, flight 2 is x {x0:.3f}-{x1:.3f}")
    bad += gaps(st, other)
    bad += open_sides(glb, S, geo, st)
    # head clearance over the foyer -> kitchen opening (DEVIATIONS 20: the soffit keeps its 2.20 m head)
    G = geo["ground"]
    for o in G["openings"]:
        if sorted(o["between"]) == ["foyer", "kitchen"]:
            head = G["floor_y"] + o["cuts"][0][1]
            over = (v[:, 0] > o["lo"]) & (v[:, 0] < o["hi"]) & (v[:, 2] < o["c"] + 0.2)
            # the plane's height at the opening's ends, on the soffit's own slope
            A = np.c_[v[:, 0], v[:, 2], np.ones(len(v))]; p = np.linalg.lstsq(A, v[:, 1], rcond=None)[0]
            low = min(p[0] * x + p[1] * o["c"] + p[2] for x in (o["lo"], o["hi"]))
            if low < head - 1e-3:
                bad.append(f"HEAD    soffit {low:.3f} over the kitchen opening, below its head {head:.3f}")
            print(f"Soffit over the kitchen opening: lowest {low - G['floor_y']:.3f} m above the floor, head {o['cuts'][0][1]:.3f} m ({int(over.sum())} vertices over it)")
    print(f"Soffit joints: {len(st)} soffit triangles, x {v[:, 0].min():.3f}-{v[:, 0].max():.3f}, y {v[:, 1].min():.3f}-{v[:, 1].max():.3f}; "
          f"{len(boundary(st))} edges checked against {len(other)} triangles; {len(bad)} problems (tolerance {TOL * 1000:.0f} mm)")
    for b in bad:
        print(b)
    return 1 if bad else 0


if __name__ == "__main__":
    a = sys.argv[1:]
    sys.exit(main(Path(a[a.index("--glb") + 1]) if "--glb" in a else ROOT / "unity/HomeAlone/Assets/Models/Foyer/MainStair.glb"))
