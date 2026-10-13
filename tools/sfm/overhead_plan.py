"""Map traced overhead spaces (pixels) to a metric plan with the calibrated homography from overhead_fit.py.
Writes <trace>.plan.json (polygons in metres, areas) and two overlays: the trace on the overhead image, and the plan.
usage: uv run --with numpy --with matplotlib --with pillow python tools/sfm/overhead_plan.py measurements/overhead/<floor>-trace.json
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

FT2 = 10.7639


def to_plan(H, px):
    q = np.c_[np.asarray(px, float), np.ones(len(px))] @ H.T
    return q[:, :2] / q[:, 2:]


def area(p):
    x, y = np.asarray(p).T
    return 0.5 * abs(x @ np.roll(y, -1) - y @ np.roll(x, -1))


def main():
    tf = Path(sys.argv[1]); t = json.loads(tf.read_text())
    H = np.loadtxt(t["calibration"])
    out = {"source": str(tf), "units": "metres; plan axes = parents' SfM plan frame (x: overhead down, y: overhead right)", "spaces": []}
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(20, 10))
    a1.imshow(Image.open(t["image"]))
    colours = {"room": "tab:blue", "hall": "tab:green", "closet": "tab:purple", "opening": "tab:red"}
    totals = {}
    print(f"{'space':<22} {'kind':<8} {'m2':>6} {'ft2':>6}  bbox m")
    for s in t["spaces"]:
        if "m" in s:  # measured directly (e.g. a gated SfM clip) in plan metres; overrides the overhead reading
            pl = np.array(s["m"], float); Hi = np.linalg.inv(H)
            q = np.c_[pl, np.ones(len(pl))] @ Hi.T; px = q[:, :2] / q[:, 2:]
        else:
            px = np.array(s["px"], float); pl = to_plan(H, px)
        A = area(pl); totals[s["kind"]] = totals.get(s["kind"], 0) + A
        bb = np.ptp(pl, axis=0)
        print(f"{s['name']:<22} {s['kind']:<8} {A:6.1f} {A * FT2:6.0f}  {bb[0]:.2f} x {bb[1]:.2f}")
        out["spaces"].append({"name": s["name"], "kind": s["kind"], "polygon_m": pl.round(3).tolist(), "area_m2": round(A, 2)})
        c = colours[s["kind"]]
        a1.fill(*px.T, alpha=.25, color=c); a1.plot(*np.vstack([px, px[:1]]).T, color=c, lw=1.5)
        a1.text(*px.mean(0), s["name"], fontsize=7, ha="center", color="white", bbox=dict(fc=c, ec="none", pad=1))
        P = pl[:, ::-1] * [1, -1]  # draw like the overhead: plan y right, plan x down
        a2.fill(*P.T, alpha=.3, color=c); a2.plot(*np.vstack([P, P[:1]]).T, color=c)
        a2.text(*P.mean(0), f"{s['name']}\n{A:.1f} m²", fontsize=7, ha="center")
    a1.set_xlim(560, 1360); a1.set_ylim(1050, 30); a1.set_title("trace on Marina's overhead")
    a2.set_aspect("equal"); a2.grid(lw=.3); a2.set_title("metric plan (m), calibrated overhead")
    fig.savefig(tf.with_suffix(".plan.png"), dpi=70, bbox_inches="tight")
    net = sum(v for k, v in totals.items() if k != "opening")
    out["totals_m2"] = {k: round(v, 2) for k, v in totals.items()} | {"net_floor_excl_openings": round(net, 2)}
    tf.with_suffix(".plan.json").write_text(json.dumps(out, indent=1) + "\n")
    print("totals:", {k: f"{v:.1f} m2 / {v * FT2:.0f} ft2" for k, v in totals.items()})
    print(f"net floor (rooms+halls+closets): {net:.1f} m2 = {net * FT2:.0f} ft2  (walls not included)")
    if "outline_px" in t:
        g = area(to_plan(H, t["outline_px"]))
        out["totals_m2"]["gross_outline"] = round(g, 2)
        print(f"gross outline: {g:.1f} m2 = {g * FT2:.0f} ft2 at 80 in doors; 78 in {g * FT2 * (78 / 80) ** 2:.0f}, 84 in {g * FT2 * (84 / 80) ** 2:.0f}"
              f"  (Marina: 1,900 ft2 upstairs)")
    tf.with_suffix(".plan.json").write_text(json.dumps(out, indent=1) + "\n")


if __name__ == "__main__":
    assert abs(area([[0, 0], [3, 0], [3, 2], [0, 2]]) - 6) < 1e-9
    main()
