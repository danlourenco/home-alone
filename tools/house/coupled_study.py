"""Coupled foyer / stair / landing / upper-floor study (Oct 15 review, item 4): every constraint on the connection, with its
source and spread, and the options a choice would make, drawn side by side. Nothing here moves geometry.
Writes spec/captures/coupled-study/study.png and prints the constraint table.
usage: uv run --with numpy --with scipy --with matplotlib python -I tools/house/coupled_study.py
"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/house"))
OUT = ROOT / "spec/captures/coupled-study"

# Foyer chain along spec x (front wall at the foyer/vestibule partition), each (low, high) in metres, with its source
FRONT = 8.948                                   # partition, overhead trace near the camera's nadir (low parallax)
CHAIN = {
    "stair foot -> front wall": [((2.20, 2.35), "Marina 203 s, rise ruler"), ((2.41, 2.41), "Marina 203 s, front door as 36 in"),
                                 ((2.25, 2.25), "real-house plan (Eric), 15 ft living as ruler")],
    "tread going": [((0.273, 0.275), "Marina nosing line, 334 s + 203 s (independent focals)"), ((0.295, 0.295), "BUILT"),
                    ((0.30, 0.30), "real-house plan, schematic treads")],
    "landing (rear wall behind top riser) / flight": [((0.34, 0.40), "Marina 312 s, at every focal")],
    "rear wall x": [((1.35, 1.50), "Marina overhead, floor line 0.08-0.23 m behind the living room's (tall-wall parallax)"),
                    ((1.581, 1.581), "BUILT: flush with the living room's rear wall"),
                    ((1.53, 1.53), "real-house plan: flush with the living room's rear wall")],
}
# Upper floor vs ground main block, front-to-back (spec x), metres
DEPTH = {"ground main block (living rear -> vestibule front)": (1.581, 10.13), "upstairs (girls B rear -> Kevin front)": (0.343, 11.66),
         "real house, both floors (plan, 8.7-8.8 m)": (0.0, 8.75)}
HELD_OUT = {"girls B / Buzz depth": (1.50, 1.42), "girls B rear -> Buzz front / Buzz": (3.16, 2.92)}   # Part 2 75 s vs our plan


def foyer_rows():
    rows = []
    for g, lab in ((0.274, "Marina nosings 0.274"), (0.295, "built 0.295")):
        flight = 12 * g
        for front in (2.20, 2.41):
            for ratio in (0.34, 0.40):
                rows.append((lab, front, flight, ratio * flight, FRONT - front - flight - ratio * flight))
    return rows


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
    up = json.loads((ROOT / "spec/house_spec.json").read_text()); gr = json.loads((ROOT / "spec/house_spec.ground.json").read_text())
    print("Foyer chain: rear wall x implied by Marina's frames (front wall fixed at 8.948)")
    rws = foyer_rows()
    for lab, front, flight, land, rear in rws:
        print(f"  {lab}: foot->front {front:.2f}, flight {flight:.2f}, landing {land:.2f} -> rear wall x {rear:.2f}")
    for k, v in CHAIN.items():
        print(f"{k}: " + "; ".join(f"{lo:g}-{hi:g} ({src})" if lo != hi else f"{lo:g} ({src})" for (lo, hi), src in v))
    for k, (a, b) in DEPTH.items():
        print(f"depth {k}: {b - a:.2f} m")
    for k, (img, ours) in HELD_OUT.items():
        print(f"held-out (Part 2 75 s, one image row, no ruler): {k} = {img:.2f}, our plan {ours:.2f} ({ours / img - 1:+.0%})")

    OUT.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(1, 4, figsize=(26, 8), gridspec_kw={"width_ratios": [1.3, 1, 1, 1]})
    a = ax[0]
    a.set_title("Foyer chain: where Marina's frames put the rear wall\n(front wall fixed; bars = spread of each reading)")
    for i, (lab, front, flight, land, rear) in enumerate(rws):
        y = i
        a.barh(y, front, left=FRONT - front, color="#c9a227"); a.barh(y, flight, left=FRONT - front - flight, color="#8b2323")
        a.barh(y, land, left=rear, color="#777"); a.text(rear - 0.05, y, f"{rear:.2f}", ha="right", va="center", fontsize=8)
        a.text(9.0, y, f"{lab}, front {front}, landing x{land / flight:.2f}", va="center", fontsize=8)
    for x, c, t in ((1.581, "c", "built / living-room rear wall"), (1.35, "b", "overhead floor line"), (1.50, "b", "")):
        a.axvline(x, color=c, ls="--"); a.text(x, len(rws) - 0.3, t, color=c, fontsize=8, rotation=90, va="top")
    a.set_xlim(0.8, 13.5); a.invert_xaxis(); a.set_xlabel("spec x (m): front wall at left, rear wall at right"); a.set_yticks([])

    def floors(a, shift, title, note):
        for s in gr["spaces"]:
            P = np.array(s["polygon_xz"] + [s["polygon_xz"][0]]); a.fill(P[:, 0], P[:, 1], color="#d8c3a5", alpha=0.6, lw=0.5, ec="#8a7")
        for s in up["spaces"]:
            P = np.array(s["polygon_xz"] + [s["polygon_xz"][0]]); a.plot(P[:, 0] + shift, P[:, 1], color="#1f4e79", lw=1)
        st = [b for b in up["stair"]["boxes"] if b["kind"] in ("step", "landing")]
        for b in st:
            a.add_patch(Rectangle((b["x"][0], b["z"][0]), b["x"][1] - b["x"][0], b["z"][1] - b["z"][0], fc="#8b2323", alpha=0.5))
        a.axvline(10.13, color="#a52", lw=0.8); a.axvline(11.66 + shift, color="#1f4e79", lw=0.8, ls="--")
        a.set_title(title + "\n" + note, fontsize=10); a.set_aspect("equal"); a.set_xlim(-6, 13.5); a.set_ylim(21, -1.5)
    floors(ax[1], 0.0, "A (built): pinned at the stair", "upstairs overhangs the front 1.5 m and the rear 1.2 m;\nstair, landing and well connect")
    floors(ax[2], 10.13 - 11.66, "B: front facades flush (upstairs -1.53 m)", "landing/well miss each other by 1.5 m (stair breaks);\nupstairs rear 2.7 m behind the living room")
    a = ax[3]
    sc = (10.13 - 1.581) / (11.66 - 0.343)
    for s in gr["spaces"]:
        P = np.array(s["polygon_xz"] + [s["polygon_xz"][0]]); a.fill(P[:, 0], P[:, 1], color="#d8c3a5", alpha=0.6, lw=0.5, ec="#8a7")
    for s in up["spaces"]:
        P = np.array(s["polygon_xz"] + [s["polygon_xz"][0]]); a.plot(1.581 + (P[:, 0] - 0.343) * sc, P[:, 1], color="#1f4e79", lw=1)
    a.set_title(f"C: upstairs squeezed front-to-back x{sc:.2f}\nfacades flush; every upstairs room {1 - sc:.0%} shallower (not Marina's rooms)", fontsize=10)
    a.set_aspect("equal"); a.set_xlim(-6, 13.5); a.set_ylim(21, -1.5)
    fig.savefig(OUT / "study.png", dpi=70, bbox_inches="tight")
    print("->", (OUT / "study.png").relative_to(ROOT))
    return rws


if __name__ == "__main__":
    rws = main()
    assert all(r[4] > 1.0 for r in rws)
