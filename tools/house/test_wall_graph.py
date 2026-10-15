"""V1 tests for wall_graph.py (tasks/wall-grid-plan.md). Each check is shown passing on a good case AND failing on an
injected error, so a green run means something.
usage: uv run --with numpy python -I tools/house/test_wall_graph.py
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import wall_graph as wg  # noqa: E402
import wall_grid_preview as wgp  # noqa: E402


def box(name, x0, x1, z0, z1, ceil=2.4, kind="room"):
    return {"name": name, "kind": kind, "poly": [[x0, z0], [x1, z0], [x1, z1], [x0, z1]], "ceil": ceil}


def storey(rooms, shafts=()):
    xs, zs, kind, owner, top = wg.cells(rooms, shafts)
    return xs, zs, kind, wg.voids(kind), wg.merge(kind == 2, xs, zs, key=top)


def area(R):
    return sum((r[1] - r[0]) * (r[3] - r[2]) for r in R)


def overlap(R):
    for i, a in enumerate(R):
        for b in R[i + 1:]:
            if min(a[1], b[1]) - max(a[0], b[0]) > 1e-6 and min(a[3], b[3]) - max(a[2], b[2]) > 1e-6:
                return True
    return False


def test_grid():
    E = [{"axis": "x", "centre": c, "lo": 0, "hi": 3, "w": 1.0, "floor": "f"} for c in (1.00, 1.03)]
    wgp.cluster(E); assert E[0]["line"] == E[1]["line"], "3 cm apart must share a line"
    E = [{"axis": "x", "centre": c, "lo": 0, "hi": 3, "w": 1.0, "floor": "f"} for c in (1.00, 1.30)]
    wgp.cluster(E); assert E[0]["line"] != E[1]["line"], "30 cm apart must not"
    E = [{"axis": "x", "centre": 1.00, "lo": 0, "hi": 3, "w": 5.0, "floor": "f"}, {"axis": "x", "centre": 1.05, "lo": 0, "hi": 3, "w": 1.0, "floor": "f"}]
    wgp.cluster(E); assert abs(E[0]["snap"]) < abs(E[1]["snap"]), "the anchored room moves less"


def test_two_rooms_one_wall():
    # two rooms one 14 cm wall apart: no void, walls tile exactly, no overlaps, no slivers
    R = [box("a", 0, 3, 0, 4), box("b", 3.14, 6, 0, 4)]
    xs, zs, kind, v, W = storey(R)
    assert not v.any() and not overlap(W)
    assert abs(area(W) - (np.sum((kind == 2) * np.outer(np.diff(xs), np.diff(zs))))) < 1e-9
    # outer ring: (6+0.28) x (4+0.28) minus the two rooms
    assert abs(area(W) - (6.28 * 4.28 - 12 - 2.86 * 4)) < 1e-6, area(W)
    assert all(min(w[1] - w[0], w[3] - w[2]) >= wg.SLIVER for w in W)


def test_gap_is_a_void():
    # INJECTED: rooms 40 cm apart, closed in on both ends: a 12 cm void inside the building
    R = [box("a", 0, 3, 0, 4), box("b", 3.40, 6, 0, 4), box("c", 0, 6, 4.14, 6), box("d", 0, 6, -2, -0.14)]
    _, _, _, v, _ = storey(R)
    assert v.any(), "an enclosed gap between rooms must be reported"


def test_open_gap_is_a_slot():
    # INJECTED: the same gap open to the outside at one end: not a void, but a slot
    R = [box("a", 0, 3, 0, 4), box("b", 3.40, 6, 0, 4), box("c", 0, 6, 4.14, 6)]
    xs, zs, kind, v, _ = storey(R)
    assert not v.any() and wg.slots(kind, xs, zs).any(), "an open 12 cm slit must be reported"
    R = [box("a", 0, 3, 0, 4), box("b", 4.0, 6, 0, 4), box("c", 0, 6, 4.14, 6)]   # 72 cm apart: a real exterior recess
    xs, zs, kind, v, _ = storey(R)
    assert not wg.slots(kind, xs, zs).any(), "a 44 cm recess is not a slot"


def test_jog_is_a_sliver():
    # INJECTED: one room's wall 1 cm off its neighbour's line leaves a 1 cm wall strip
    R = [box("a", 0, 3, 0, 2), box("b", 0, 3.01, 2.14, 4), box("c", 3.15, 6, 0, 4)]
    _, _, _, _, W = storey(R)
    assert any(min(w[1] - w[0], w[3] - w[2]) < wg.SLIVER for w in W), "a 1 cm jog must produce a sliver"


def test_shaft_chase():
    # a declared shaft in a pocket: the rest of the pocket becomes wall (chase), no void left
    R = [box("a", 0, 3, 0, 4), box("b", 3.9, 6, 0, 4), box("c", 0, 6, 4.14, 6), box("d", 0, 6, -2, -0.14)]
    shaft = {"x": [3.14, 3.5], "z": [0.5, 1.0]}
    xs, zs, kind, owner, top = wg.cells(R, [shaft])
    v = wg.voids(kind); chase = v & wg.touches(v, kind == 3)
    assert v.any() and chase.any(), "the pocket is a void until the shaft claims it"
    kind[chase] = 2
    assert not wg.voids(kind).any()
    xs, zs, kind, owner, top = wg.cells(R)   # INJECTED: no shaft declared -> the pocket stays a void
    assert wg.voids(kind).any()


def test_close_decision():
    # the real house: the user's 'close' decision leaves no parents/Kevin wall thicker than 14 cm
    spec, dec = wg.load()
    E = wg.snap(spec, dec)
    assert not wgp.odd_walls(E), wgp.odd_walls(E)
    E = wg.snap(spec, [d for d in dec if "close" not in d])   # INJECTED: without the decisions the thick walls remain
    assert wgp.odd_walls(E)


def test_real_house():
    spec, dec = wg.load()
    geo, E, report = wg.build(spec, dec)
    for f, g in geo.items():
        W = [(w["x"][0], w["x"][1], w["z"][0], w["z"][1], w["y"][0], w["y"][1]) for w in g["walls"]]
        assert not g["voids"], (f, g["voids"])
        assert not g["slots"], (f, g["slots"])
        assert not overlap3(W), f
        assert not overlap3(W + [(c["x"][0], c["x"][1], c["z"][0], c["z"][1], c["y"][0], c["y"][1]) for c in g["ceilings"]]), f


def overlap3(B):
    for i, a in enumerate(B):
        for b in B[i + 1:]:
            if all(min(a[k + 1], b[k + 1]) - max(a[k], b[k]) > 1e-6 for k in (0, 2, 4)):
                return True
    return False


def test_overlap3_catches():
    assert overlap3([(0, 1, 0, 1, 0, 2), (0.5, 2, 0, 1, 1, 3)]) and not overlap3([(0, 1, 0, 1, 0, 1), (0, 1, 0, 1, 1, 2)])


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t(); print("ok  ", t.__name__)
    print(f"{len(tests)} passed")
