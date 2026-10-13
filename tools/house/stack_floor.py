"""Stack the ground-floor plan under the upstairs plan, pinned by the main stair (skill overhead-floor).

The two overheads face different ways: the main floor's front is image-down, the upstairs' front is image-right.
A quarter turn takes ground plan (x down its overhead, y across) into the upstairs plan frame. The stair fixes the
translation: the foyer's rear wall sits under the stairwell's rear (west) edge, where the landing is, and the foyer's
left (photo) wall under the stairwell's south edge, where flight 1 runs. Both are wall-top inner edges in their plans.
Writes measurements/overhead/ground.reg.H.txt (overhead px -> upstairs plan metres) and points the ground trace at it,
then prints the independent check: how the two floors' exterior walls line up.
usage: uv run --with numpy python tools/house/stack_floor.py
"""
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
TURN = np.array([[0, -1.0], [1, 0]])   # ground (x_g, y_g) -> upstairs (x_u, y_u) = (-y_g, x_g): proper rotation, no mirror


def apply(H, px):
    q = np.c_[np.asarray(px, float), np.ones(len(px))] @ H.T
    return q[:, :2] / q[:, 2:]


def main():
    G = json.loads((ROOT / "measurements/overhead/ground.json").read_text())
    T = json.loads((ROOT / "measurements/overhead/ground-trace.json").read_text())
    H = np.loadtxt(ROOT / "measurements/overhead/ground.H.txt")
    foyer = apply(H, next(s["px"] for s in T["spaces"] if s["name"] == "foyer"))
    spec = json.loads((ROOT / "spec/house_spec.json").read_text()); o = spec["origin_plan_m"]
    well = np.array(next(s["polygon_xz"] for s in spec["spaces"] if s["name"] == "main_stair_opening"))
    well_rear_y = well[:, 0].min() + o[1]          # upstairs plan y of the well's rear (west) edge
    well_south_x = well[:, 1].max() + o[0]         # upstairs plan x of the well's south edge
    f = foyer @ TURN.T
    t = np.array([well_south_x - f[:, 0].max(), well_rear_y - f[:, 1].min()])
    A = np.eye(3); A[:2, :2] = TURN; A[:2, 2] = t
    Hr = A @ H
    # User decision Oct 13: Marina's ground main block is ~15% shallower front-to-back than her upstairs; stretch the
    # ground floor front-to-back (plan y) about the rear wall so the main facades stack too.
    up = json.loads((ROOT / "measurements/overhead/upstairs-trace.json").read_text())
    uo = apply(np.loadtxt(ROOT / up["calibration"]), up["outline_px"])
    gf = apply(Hr, [G["facade_px"]])[0]                                  # ground main facade, upstairs frame
    xs = sorted(apply(Hr, [[G["facade_span_px"][0], G["facade_px"][1]], [G["facade_span_px"][1], G["facade_px"][1]]])[:, 0])
    front = np.median([q[1] for q in uo if xs[0] - 1 <= q[0] <= xs[1] + 1 and q[1] > np.median(uo[:, 1])])
    k = (front - well_rear_y) / (gf[1] - well_rear_y)
    np.savetxt(ROOT / "measurements/overhead/ground.reg.H.txt", Hr)
    T["calibration"] = "measurements/overhead/ground.reg.H.txt"
    # User decision Oct 13 (3): NO stretch. The real-house plan matches Marina's ground floor as measured, and the film's
    # upstairs was a separate set that never had to stack. Rooms keep Marina's shapes; the upstairs front wall overhangs
    # the ground floor's by (k-1) x depth. docs/DEVIATIONS.md #1. The stretch k is still computed and reported.
    T.pop("stretch", None)
    T["registration"] = {"turn": "ground (x,y) -> upstairs (-y, x)", "translation_m": t.round(3).tolist(),
                         "stretch_needed_to_stack_facades": round(float(k), 4),
                         "stretch_note": "NOT applied (user decision Oct 13): rooms keep Marina's shapes; upstairs overhangs the front",
                         "pinned_by": "foyer rear wall = stairwell rear edge (landing); foyer photo wall = stairwell south edge (flight 1)"}
    (ROOT / "measurements/overhead/ground-trace.json").write_text(json.dumps(T, indent=1) + "\n")

    # independent check: exterior walls of the two floors (wall-top outer edges, both traced from their overheads)
    import sys; sys.path.insert(0, str(ROOT / "tools/sfm")); from calib import mapper
    go = mapper(T)[0](G["scale"][0]["pixels"])
    print(f"translation {t.round(3)} m; a {k:.3f} front-to-back stretch would stack the facades (not applied)")
    print(f"{'exterior edge':<26}{'upstairs':>10}{'ground':>10}{'diff':>8}")
    for name, k, fn in (("front facade (plan y max)", 1, np.max), ("rear wall (plan y min)", 1, np.min),
                        ("north side (plan x min)", 0, np.min), ("south side (plan x max)", 0, np.max)):
        u, gr = fn(uo[:, k]), fn(go[:, k])
        print(f"{name:<26}{u:10.2f}{gr:10.2f}{gr - u:+8.2f}")


if __name__ == "__main__":
    assert np.allclose(TURN @ [1, 0], [0, 1]) and np.isclose(np.linalg.det(TURN), 1)   # front (+x_g) -> front (+y_u)
    main()
