"""Overhead pixels <-> plan metres for a traced floor: the trace's homography ("calibration") plus an optional
piecewise front-to-back stretch ("stretch": {"pivot_y", "k"}): plan y in front of pivot_y (y > pivot) is stretched by k
about the pivot, y behind it is left as measured. Used by overhead_plan, reconcile, verify_plan, stack_floor.
"""
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]


def mapper(trace):
    H = np.loadtxt(ROOT / trace["calibration"]); Hi = np.linalg.inv(H)
    st = trace.get("stretch")

    def fwd(px):
        q = np.c_[np.asarray(px, float), np.ones(len(px))] @ H.T; P = q[:, :2] / q[:, 2:]
        if st:
            y = P[:, 1]; P[:, 1] = np.where(y > st["pivot_y"], st["pivot_y"] + st["k"] * (y - st["pivot_y"]), y)
        return P

    def inv(pl):
        P = np.array(pl, float).copy()
        if st:
            y = P[:, 1]; P[:, 1] = np.where(y > st["pivot_y"], st["pivot_y"] + (y - st["pivot_y"]) / st["k"], y)
        q = np.c_[P, np.ones(len(P))] @ Hi.T
        return q[:, :2] / q[:, 2:]
    return fwd, inv


if __name__ == "__main__":
    import json, tempfile
    f = tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False); np.savetxt(f.name, np.diag([0.01, 0.02, 1])); f.close()
    fwd, inv = mapper({"calibration": f.name, "stretch": {"pivot_y": 1.0, "k": 1.2}})
    px = np.array([[10, 0], [10, 100], [300, 300]])
    assert np.allclose(inv(fwd(px)), px) and np.isclose(fwd([[0, 100]])[0, 1], 1 + 1.2 * 1.0)
    print("calib self-check ok")
