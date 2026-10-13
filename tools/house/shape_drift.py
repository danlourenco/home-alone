"""Shape drift: does every built room still have Marina's shape and size? (docs/DEVIATIONS.md, "must feel authentic")

For each floor, compares each room in the built spec (spec/house_spec[.<floor>].json, after squaring, wall thinning
and any stacking stretch) with Marina's own evidence: the traced overhead through its calibration WITHOUT the stretch.
Reports width, depth, proportion (w/d) and area per room, and flags any that moved more than the threshold.
Wall thinning legitimately adds ~10-30 cm per dimension (rooms take the freed space), so small rooms read higher %.
usage: uv run --with numpy python tools/house/shape_drift.py [--tol 5]
exit 1 if any room drifts past --tol (%) in proportion or area, so it can gate a build.
"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/sfm"))
from calib import mapper  # noqa: E402


def area(P):
    x, y = np.asarray(P).T
    return 0.5 * abs(x @ np.roll(y, -1) - y @ np.roll(x, -1))


def marina(floor):
    """Room polygons in plan metres from Marina's overhead alone (no stretch, no thinning, no squaring)."""
    t = json.loads((ROOT / f"measurements/overhead/{floor}-trace.json").read_text())
    t = {k: v for k, v in t.items() if k != "stretch"}
    fwd, _ = mapper(t)
    out = {}
    for s in t["spaces"]:
        if s["kind"] in ("opening", "closet"):
            continue
        out[s["name"]] = np.array(s["m"], float) if "m" in s else fwd(s["px"])
    return out


def built(floor):
    p = ROOT / ("spec/house_spec.json" if floor == "upstairs" else f"spec/house_spec.{floor}.json")
    o = json.loads(p.read_text())
    return {s["name"]: np.array(s["polygon_xz"])[:, ::-1] for s in o["spaces"]}   # spec (x, z) -> plan order (x=z, y=x)


def main():
    tol = float(sys.argv[sys.argv.index("--tol") + 1]) if "--tol" in sys.argv else 5.0
    bad = 0
    for floor in ("upstairs", "ground"):
        if not (ROOT / f"measurements/overhead/{floor}-trace.json").exists():
            continue
        M, B = marina(floor), built(floor)
        print(f"\n{floor.upper()}  (Marina's overhead as traced -> built; plan x = north-south, y = front-back)")
        print(f"{'room':<20}{'x (m)':>15}{'y (m)':>15}{'proportion':>16}{'area':>16}")
        for n, m in M.items():
            if n not in B:
                continue
            dm, db = np.ptp(m, 0), np.ptp(B[n], 0)
            am, ab = area(m), area(B[n])
            dx, dy = db / dm - 1
            dr = (db[0] / db[1]) / (dm[0] / dm[1]) - 1
            da = ab / am - 1
            flag = abs(dr) * 100 > tol or abs(da) * 100 > tol
            bad += flag
            print(f"{n:<20}{dm[0]:5.2f}>{db[0]:5.2f} {dx:+4.0%}{dm[1]:5.2f}>{db[1]:5.2f} {dy:+4.0%}"
                  f"{dm[0] / dm[1]:7.2f}>{db[0] / db[1]:5.2f} {dr:+4.0%}{am:6.1f}>{ab:5.1f} {da:+4.0%}  {'<-- DRIFT' if flag else ''}")
    print(f"\n{bad} room(s) drift more than {tol:.0f}% in proportion or area. Each must be listed in docs/DEVIATIONS.md or fixed.")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    sq = np.array([[0, 0], [2, 0], [2, 1], [0, 1]])
    assert abs(area(sq) - 2) < 1e-9
    main()
