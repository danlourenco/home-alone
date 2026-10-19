"""soffit_joints: flight 2's plaster soffit meets its neighbours along every edge, by construction.

Why (user walk Oct 19 12:26 "does not connect", 14:49 "why is this soffit still not fixed?", shot 20261019-144917): the sloped soffit
under flight 2 stopped 11.5 cm under the foyer ceiling at the stair head (the dark tread undersides showed through the slot) and
its open-side edge stood 1 cm proud of a recessed infill, 7-9 cm under the stringer's bottom edge. Eye checks and the z-fight/clash
gates passed it twice; nothing tested that the edges touch anything.

The soffit is every sloped, downward-facing triangle of MainStair.glb's white part over flight 2's plan. Its boundary (edges used by
one soffit triangle) is sampled every 2 cm; each sample must lie within TOL of another drawn surface: the stair model's other
triangles (landing slab, stringer, head fascia) or a wall / ceiling / floor box of spec/geometry.json (the grey-box draws those).
Also: the soffit runs from flight 2's foot to its head, and clears the foyer->kitchen opening's head (DEVIATIONS 20).

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
    sc = trimesh.load(glb, force="scene")
    tris, white = [], []
    for nd in sc.graph.nodes_geometry:
        T, g = sc.graph[nd]
        m = sc.geometry[g]
        v = m.vertices @ T[:3, :3].T + T[:3, 3]
        v = np.c_[-v[:, 0], v[:, 1], -v[:, 2]]            # glTF (+Y up, glTFast mirrors x) -> spec: (-gx, gy, -gz)
        t = v[m.faces]; tris.append(t); white.append(np.full(len(t), nd.startswith("RisersStringers")))
    tris, white = np.vstack(tris), np.concatenate(white)
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
