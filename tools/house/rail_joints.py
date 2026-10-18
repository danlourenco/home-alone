"""rail_joints: every handrail end of the main stair's balustrade (flights, landing, upstairs gallery) meets something by construction.

Why (walk note 2026-10-17T22:46:06 at the gallery corner, "bannisters don't connect"): the gallery's two grey-box rails stopped 4 cm short
of each other on both axes and flight 2's handrail stopped in mid air 15 cm short of the gallery rail; nothing checked rail ends.

A rail end passes when, within TOL (5 mm), it is
  - another rail's end, or
  - inside a newel (its plan square and height), or
  - in a wall (a wall box of spec/geometry.json upstairs or the stair's own wall boxes).
Rails come from what is drawn: the stair model's runs (tools/house/hifi_foyer.py writes them to spec/captures/main_stair_rails.json,
and each listed end is checked against MainStair.glb's Rail mesh: the end's cap ring must be there), plus every grey-box gallery rail
(spec/geometry.json rail openings of the main stair well; SpecGreybox.Rail draws them) the model does not list as covered.

  uv run -q --with trimesh --with numpy python -I tools/house/rail_joints.py [--selftest]     exit 1 on any loose end
"""
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOL = 0.005
RAIL_H = 0.95          # SpecGreybox.RailHeight: the grey-box rail's top; its 6 cm box is centred 3 cm under it


def gallery_rails(geo):
    """Grey-box rails of the main stair well as SpecGreybox.Rail draws them: a box from lo to hi on the plane c."""
    out = []
    for o in geo["openings"]:
        if o["kind"] == "rail" and "main_stair_opening" in o["between"]:
            y = RAIL_H - 0.03
            p = (lambda s: (o["c"], y, s)) if o["axis"] == "x" else (lambda s: (s, y, o["c"]))
            out.append({"name": f"greybox rail:{o['axis']}:{o['c']}", "id": f"rail:{o['axis']}:{round(o['c'], 3)}", "pts": [p(o["lo"]), p(o["hi"])]})
    return out


def loose_ends(runs, newels, walls):
    bad = []
    ends = [(r, i) for r in runs for i in (0, -1)]
    for r, i in ends:
        p = r["pts"][i]
        if any(math.dist(p, o["pts"][j]) <= TOL for o, j in ends if o is not r):
            continue
        if any(abs(p[0] - n["x"]) <= n["hx"] + TOL and abs(p[2] - n["z"]) <= n["hz"] + TOL and n["y0"] - TOL <= p[1] <= n["y1"] + TOL for n in newels):
            continue
        if any(w["x"][0] - TOL <= p[0] <= w["x"][1] + TOL and w["z"][0] - TOL <= p[2] <= w["z"][1] + TOL and w["y"][0] - TOL <= p[1] <= w["y"][1] + TOL for w in walls):
            continue
        near = min((math.dist(p, o["pts"][j]) for o, j in ends if o is not r), default=float("inf"))
        bad.append(f"LOOSE   {r['name']} {'start' if i == 0 else 'end'} at spec ({p[0]:.3f}, {p[1]:.3f}, {p[2]:.3f}): no newel or wall, nearest rail end {near * 100:.1f} cm")
    return bad


def model_problems(man, glb):
    """Each listed run end has its cap ring in the Rail mesh; each listed newel has Newels geometry at its square."""
    import numpy as np
    import trimesh
    sc = trimesh.load(glb, force="scene")
    def verts(name):
        vs = [sc.geometry[g].vertices @ T[:3, :3].T + T[:3, 3] for nd in sc.graph.nodes_geometry
              for T, g in [sc.graph[nd]] if nd.startswith(name)]
        v = np.vstack(vs); return np.c_[-v[:, 0], v[:, 1], -v[:, 2]]   # glTF (+Y up, glTFast mirrors x) -> spec: (-gx, gy, -gz)
    rail, newel = verts("Rail"), verts("Newels")
    bad = []
    for r in man["runs"]:
        for i, j in ((0, 1), (-1, -2)):
            p, q = np.array(r["pts"][i]), np.array(r["pts"][j]); t = (p - q) / np.linalg.norm(p - q)
            d = rail - p
            ring = (np.abs(d @ t) < 0.0015) & (np.linalg.norm(d, axis=1) < 0.06)
            if ring.sum() < 8:
                bad.append(f"MODEL   {r['name']} {'start' if i == 0 else 'end'}: no rail end in MainStair.glb at {np.round(p, 3).tolist()} ({int(ring.sum())} ring vertices)")
    for n in man["newels"]:
        m = (np.abs(newel[:, 0] - n["x"]) <= n["hx"] + 1e-3) & (np.abs(newel[:, 2] - n["z"]) <= n["hz"] + 1e-3) & (newel[:, 1] >= n["y0"] - 1e-3) & (newel[:, 1] <= n["y1"] + 1e-3)
        if m.sum() < 8:
            bad.append(f"MODEL   newel {n['name']} not in MainStair.glb at ({n['x']:.3f}, {n['z']:.3f})")
    return bad


def selftest():
    w = [{"x": [0, 1], "z": [2, 2.1], "y": [0, 2.5]}]
    n = [{"name": "n", "x": 0.0, "z": 0.0, "hx": 0.045, "hz": 0.045, "y0": 0, "y1": 1.0}]
    a = {"name": "a", "pts": [(0.0, 0.9, 0.0), (0.0, 0.9, 2.0)]}            # newel to wall: closed
    b = {"name": "b", "pts": [(0.07, 0.9, 0.0), (1.0, 0.9, 0.0)]}           # 7 cm off the newel (the gallery corner of Oct 17)
    c = {"name": "c", "pts": [(1.0, 0.9, 0.0), (1.0, 0.9, 1.0)]}            # meets b's end, then free
    assert loose_ends([a], n, w) == []
    bad = loose_ends([a, b, c], n, w)
    assert len(bad) == 2 and "b start" in bad[0] and "c end" in bad[1], bad
    print("selftest ok")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest(); sys.exit(0)
    geo = json.loads((ROOT / "spec/geometry.json").read_text())["upstairs"]
    S = json.loads((ROOT / "spec/house_spec.json").read_text())["stair"]
    mp = ROOT / "spec/captures/main_stair_rails.json"
    man = json.loads(mp.read_text()) if mp.exists() else {"runs": [], "newels": [], "covers": []}
    walls = geo["walls"] + [b for b in S["boxes"] if b["kind"] == "wall"]
    runs = [dict(r, pts=[tuple(p) for p in r["pts"]]) for r in man["runs"]] + [g for g in gallery_rails(geo) if g["id"] not in man.get("covers", [])]
    bad = loose_ends(runs, man["newels"], walls) + (model_problems(man, ROOT / "unity/HomeAlone/Assets/Models/Foyer/MainStair.glb") if man["runs"] else [])
    print(f"Rail joints: {len(runs)} rails ({len(man['runs'])} in the stair model, {len(runs) - len(man['runs'])} grey-box), {len(man['newels'])} newels, "
          f"{len(bad)} loose ends (tolerance {TOL * 1000:.0f} mm)")
    for b in bad:
        print(b)
    sys.exit(1 if bad else 0)
