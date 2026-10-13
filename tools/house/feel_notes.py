"""Read the walk-and-annotate notes (Unity FeelNotes, key M) and place each one.

  Greybox_Upstairs scene: notes map to the room they stand in (spec polygons; floor chosen by height).
  IntactHouseReference (the old downloaded model): notes are placed on that model's floor plan (glb_section.py) and
  drawn on a top-down map with their number; the screenshot shows the spot. No room name is inferred there.
Writes spec/feedback/feel-notes.md (table, newest last) and spec/feedback/feel-notes-old-model.png.
usage: uv run --with numpy --with matplotlib python tools/house/feel_notes.py
"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
FB = ROOT / "spec/feedback"


def inside(poly, pt):
    x, y = pt; c = False
    for (x1, y1), (x2, y2) in zip(poly, np.roll(poly, -1, 0)):
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


def room_in_greybox(pos):
    x, y, z = pos
    specs = [("upstairs", ROOT / "spec/house_spec.json")]
    g = ROOT / "spec/house_spec.ground.json"
    if g.exists():
        specs.append(("ground", g))
    floor = "ground" if g.exists() and y < -1.0 else "upstairs"
    spec = json.loads(dict(specs)[floor].read_text())
    for s in spec["spaces"]:
        if inside(np.array(s["polygon_xz"]), (x, -z)):           # Unity world z = -spec z
            return f"{floor}: {s['name']}"
    return f"{floor}: (between spaces)"


def old_model_xy(pos):
    """IntactHouseReference instantiates the GLB rotated 180 deg about y at native scale. The glTF import flips x and the
    180 deg turn flips it back, so Blender (X, Y) = (x, z). Checked Oct 13: a note facing the living-room fireplace lands
    in the model's living room (the mirrored mapping put it in the foyer)."""
    sys.path.insert(0, str(ROOT / "tools/survey"))
    from glb_section import M_PER_UNIT
    return np.array([pos[0], pos[2]]) * M_PER_UNIT


def main():
    FB.mkdir(parents=True, exist_ok=True); f = FB / "feel-notes.jsonl"
    notes = [json.loads(l) for l in f.read_text().splitlines() if l.strip()] if f.exists() else []
    rows = ["| # | scene | where | shape/size | lighting | note | screenshot |", "|---|---|---|---|---|---|---|"]
    old = []
    for i, n in enumerate(notes, 1):
        if n["scene"].startswith("Greybox"):
            where = room_in_greybox(n["pos"])
        else:
            xy = old_model_xy(n["pos"]); up = n["pos"][1] > 3.5    # old model: ground ~1.3, upper floor ~5.2 (native)
            old.append((i, xy, n["rating"], up))
            where = f"old model {'upper' if up else 'ground'} floor plan ({xy[0]:.1f}, {xy[1]:.1f}) m, see map"
        light = n.get("lighting", "(not asked)")
        rows.append(f"| {i} | {n['scene']} | {where} | {n['rating']} | {light} | {n['note']} | [{n['shot']}]({n['shot']}) |")
    (FB / "feel-notes.md").write_text("# Feel notes (walk-and-annotate, key M in Unity)\n\n" + "\n".join(rows) + "\n")
    print("\n".join(rows))
    if old:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        sys.path.insert(0, str(ROOT / "tools/survey"))
        from glb_section import section
        fig, axes = plt.subplots(1, 2, figsize=(24, 10))
        col = {"feels right": "tab:green", "feels off": "tab:red", "right": "tab:green", "off": "tab:red", "not sure": "tab:orange"}
        for ax, (title, h, upper) in zip(axes, (("ground floor", 1.75, False), ("upper floor", 5.7, True))):
            S = section(h)
            S = S[(np.abs(S[..., 0]) < 14).all(1) & (S[..., 1] > -4).all(1) & (S[..., 1] < 16).all(1)]
            for a, b in S:
                ax.plot([a[0], b[0]], [a[1], b[1]], "k-", lw=0.5)
            for i, xy, r, up in old:
                if up == upper:
                    ax.plot(*xy, "o", color=col.get(r, "k"), ms=12); ax.text(xy[0] + 0.25, xy[1] + 0.25, str(i), fontsize=11)
            ax.set_aspect("equal"); ax.set_title(f"Old model {title}: SHAPE ratings (green right, red off, orange unsure)")
        fig.savefig(FB / "feel-notes-old-model.png", dpi=70)
    print(f"\n{len(notes)} notes -> {FB / 'feel-notes.md'}")


if __name__ == "__main__":
    main()
