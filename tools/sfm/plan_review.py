"""Overlay a reviewed room plan (measurements/rooms/<suite>.json) on the VGGT top-down wall density, labelled in metres.
The reviewed polygons are hand-checked against plan_extract.py candidates and the video frames; this is the image the
user approves. Prints each room's sides and area at 78/80/84 in doors.
usage: PYTHONPATH=tools/sfm uv run --with numpy --with matplotlib python tools/sfm/plan_review.py <suite> [out.png]
"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]


def area(poly):
    x, y = np.array(poly).T
    return 0.5 * abs(x @ np.roll(y, -1) - y @ np.roll(x, -1))


def main():
    suite = sys.argv[1]
    spec = json.loads((ROOT / f"measurements/rooms/{suite}.json").read_text())
    w = ROOT / "sfm-work/rooms" / suite
    p = json.loads((w / "plan-0.05.json").read_text())
    out = sys.argv[2] if len(sys.argv) > 2 else str(w / "plan-reviewed.png")
    m = spec["m_per_unit"]["80in"]

    pts = np.load(w / "vggt/sparse/0/points.npy")
    up, R = np.array(p["up"]), np.array(p["rotation"])
    a, b = map(np.array, p["plane_axes"])
    h = pts @ up
    Q = np.c_[pts @ a, pts @ b] @ R * m
    band = (h > p["floor"] + .15 * (p["ceiling"] - p["floor"])) & (h < p["floor"] + .85 * (p["ceiling"] - p["floor"]))

    fig, ax = plt.subplots(figsize=(10, 12))
    ax.hexbin(Q[band, 0], Q[band, 1], gridsize=400, bins="log", cmap="Greys", mincnt=1)
    print(f"{'room':<18} {'area m2 @78/80/84 in':>24} {'ft2 @80':>8}")
    for room in spec["rooms"]:
        poly = np.array(room["polygon"]) * m
        ax.fill(*poly.T, alpha=.15)
        ax.plot(*np.vstack([poly, poly[:1]]).T, "b-", lw=2)
        for p0, p1 in zip(poly, np.roll(poly, -1, 0)):
            ax.text(*(p0 + p1) / 2, f"{np.linalg.norm(p1 - p0):.2f}", color="b", fontsize=8, ha="center",
                    bbox=dict(fc="white", ec="none", pad=0.5))
        ar = {k: area(np.array(room["polygon"]) * v) for k, v in spec["m_per_unit"].items()}
        ax.text(*poly.mean(0), f"{room['name']}\n{ar['80in']:.1f} m²", ha="center", fontsize=11, weight="bold")
        print(f"{room['name']:<18} {ar['78in']:7.1f} {ar['80in']:7.1f} {ar['84in']:7.1f}   {ar['80in'] * 10.7639:8.0f}")
    for kind, colour in (("doors", "lime"), ("features", "orange")):
        for d in spec.get(kind, []):
            s = np.array(d["span"]) * m
            ax.plot(*s.T, color=colour, lw=6, solid_capstyle="butt")
            ax.text(*s.mean(0), " " + d["name"], color="green" if kind == "doors" else "darkorange", fontsize=8)
            if kind == "doors":
                print(f"door {d['name']}: {np.linalg.norm(s[1] - s[0]):.2f} m wide (casing to casing where noted)")
    ax.set_aspect("equal"); ax.grid(lw=.3); ax.set_xlabel("metres (80 in doors)")
    ax.set_title(f"{suite}: reviewed plan (blue) over wall-height point density; dimensions in metres")
    fig.savefig(out, dpi=80, bbox_inches="tight")
    print("->", out)


if __name__ == "__main__":
    assert abs(area([[0, 0], [2, 0], [2, 1], [0, 1]]) - 2) < 1e-9
    main()
