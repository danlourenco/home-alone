"""Calibrate an oblique overhead render of a floor (Marina's plan views) into metres.
Wall-top inner edges all lie in one horizontal plane (the ceiling height), so one homography maps them to the plan.
Control rooms come from measurements/rooms/*.json: a room with a known plan position fixes the frame; other rooms
contribute their measured shape with an unknown offset. Reports per-point residuals, leave-one-out error (the honest
accuracy), and any check distances given in the spec.
usage: uv run --with numpy --with scipy python tools/sfm/overhead_fit.py measurements/overhead/<floor>.json
"""
import json
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares


def to_plan(H, px):
    q = np.c_[np.asarray(px, float), np.ones(len(px))] @ H.T
    return q[:, :2] / q[:, 2:]


def solve(rooms, init):
    """rooms: list of (pixel corners, plan corners in metres, free_offset). Returns H (px -> plan m) and offsets."""
    free = [i for i, r in enumerate(rooms) if r[2]]

    def unpack(p):
        H = np.r_[p[:8], 1].reshape(3, 3)
        off = {i: p[8 + 2 * k:10 + 2 * k] for k, i in enumerate(free)}
        return H, off

    def resid(p):
        H, off = unpack(p)
        return np.concatenate([(to_plan(H, px) - (pl + off.get(i, 0))).ravel() for i, (px, pl, _) in enumerate(rooms)])

    p0 = np.r_[init.ravel()[:8] / init[2, 2], np.zeros(2 * len(free))]
    for k, i in enumerate(free):  # start each free room where the initial map puts its pixels
        p0[8 + 2 * k:10 + 2 * k] = (to_plan(init, rooms[i][0]) - rooms[i][1]).mean(0)
    sol = least_squares(resid, p0, x_scale="jac")
    return unpack(sol.x)


def affine_init(px, pl):
    A = np.c_[np.asarray(px, float), np.ones(len(px))]
    X, *_ = np.linalg.lstsq(A, np.asarray(pl), rcond=None)
    return np.r_[X.T, [[0, 0, 1]]]


def main():
    spec = json.loads(Path(sys.argv[1]).read_text())
    rooms, labels = [], []
    for r in spec["control"]:
        m = json.loads(Path(r["measurement"]).read_text())
        poly = np.array(next(x for x in m["rooms"] if x["name"] == r["room"])["polygon"]) * m["m_per_unit"]["80in"]
        pl = poly[r["polygon_index"]]
        if r.get("swap_axes"):
            pl = pl[:, ::-1]
        rooms.append((np.array(r["pixels"], float), pl - (pl.min(0) if r["free_offset"] else 0), r["free_offset"]))
        labels += [f"{r['room']}#{i}" for i in r["polygon_index"]]

    fixed = [k for k, r in enumerate(rooms) if not r[2]][0]
    H, off = solve(rooms, affine_init(rooms[fixed][0], rooms[fixed][1]))
    res = np.concatenate([np.linalg.norm(to_plan(H, px) - (pl + off.get(i, 0)), axis=1) for i, (px, pl, _) in enumerate(rooms)])

    loo = []  # drop one corner, refit, predict it
    for i, (px, pl, fr) in enumerate(rooms):
        for j in range(len(px)):
            sub = [(np.delete(p, j, 0) if k == i else p, np.delete(q, j, 0) if k == i else q, f) for k, (p, q, f) in enumerate(rooms)]
            H2, off2 = solve(sub, H)
            loo.append(np.linalg.norm(to_plan(H2, px[j:j + 1])[0] - (pl[j] + off2.get(i, 0))))
    print(f"{'corner':<22} {'fit cm':>7} {'held-out cm':>12}")
    for lab, r, l in zip(labels, res, loo):
        print(f"{lab:<22} {r * 100:7.1f} {l * 100:12.1f}")
    print(f"median: fit {np.median(res) * 100:.1f} cm, held-out {np.median(loo) * 100:.1f} cm (max {max(loo) * 100:.1f})")

    for c in spec.get("checks", []):
        a, b = to_plan(H, c["pixels"])
        d = np.linalg.norm(b - a)
        print(f"check {c['name']}: {d:.2f} m vs stated {c['metres']:.2f} m ({(d / c['metres'] - 1):+.1%})")
    np.savetxt(Path(sys.argv[1]).with_suffix(".H.txt"), H)
    return H


if __name__ == "__main__":
    H0 = np.array([[2.0, 0.1, 5], [0.2, 1.5, -3], [1e-4, 2e-4, 1]])
    pts = np.array([[0, 0], [100, 0], [100, 80], [0, 80], [50, 30]], float)
    assert np.allclose(to_plan(np.linalg.inv(np.linalg.inv(H0)), pts), to_plan(H0, pts))
    main()
