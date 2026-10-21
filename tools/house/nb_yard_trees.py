"""nb_yard_trees: the front yard's big trees, as built vs proposed (Oct 20 2026, step 3; a PROPOSAL, nothing moved). Plan plot only.
Built: SpecGreybox.Trees swaps the old WinterNeighborhood's stick trees one for one (their spec positions computed from
WinnetkaNeighborhood.cs: yard (19.67, 24.6), (18.67, -3.4); our side's street row (27.27, 24.2), (27.27, 3.8)).
Evidence: ISGS 2022 lidar crown peaks over our lot (17.3, 12.6) 21.0 m, (14.8, 15.9) 20.8 m, (25.1, 16.5) 20.9 m (crown peaks, not trunks);
film 12030/11908 (straight-on, Christmas morning): two big trunks RIGHT of the portico (frame 0.58 and 0.79 of the width), 5545 the same
two at night; 4382 a huge trunk at the right edge (near the camera); 6399 (from the left) two trunks at the frame's left edge; the user's
modern summer photo: one big tree left of centre (in front of the left French windows) and a big oak just right of the portico.
  uv run --with matplotlib python -I tools/house/nb_yard_trees.py OUT.png"""
import json, sys
from pathlib import Path
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle
ROOT = Path(__file__).resolve().parents[2]
built = [(19.67, 24.6, "yard"), (18.67, -3.4, "yard"), (27.27, 24.2, "street row"), (27.27, 3.8, "street row")]
lidar = [(17.3, 12.6, 21.0), (14.8, 15.9, 20.8), (25.1, 16.5, 20.9)]
# PROPOSED trunks (to be fixed with a solved 12030 camera before building): two right of the portico (film 12030/11908/5545), the lidar's
# left crown pair as one big tree left of centre (the user's photo), the parkway trunk beside the right pier (12030)
prop = [(16.5, 6.6, 1.1, "oak R of portico (12030 0.58, photo)"), (19.5, 0.5, 1.0, "trunk R (12030 0.79, 5545)"),
        (16.0, 14.2, 1.0, "big tree L of centre (lidar pair, photo)"), (27.4, 7.6, 0.9, "beside the right pier (12030)")]
fig, ax = plt.subplots(figsize=(10, 8), dpi=100)
lot = [(-30.16, 30.58), (28.87, 30.72), (28.87, -3.91), (-34.16, -4.06)]
ax.add_patch(Polygon([(z, x) for x, z in lot], fc="#f3ecd2", ec="#998", lw=1))
for nm, (x0, x1), (z0, z1) in (("main", (1.44, 10.27), (2.864, 16.21)), ("den", (2.215, 9.406), (16.21, 20.057)), ("right", (2.316, 9.547), (-1.055, 2.864))):
    ax.add_patch(Polygon([(z0, x0), (z1, x0), (z1, x1), (z0, x1)], fc="#a0503c", ec="k", lw=.8))
ax.add_patch(Polygon([(8.9, 10.37), (10.5, 10.37), (10.5, 11.6), (8.9, 11.6)], fc="w", ec="k"))   # portico
DL = [(21.4, 30.6), (21.4, 24.4), (18.2, 21.8), (13.5, 20.2), (9.8, 20.5), (3.9, 22.7), (1.1, 25.6), (-0.5, 27.3), (-1.2, 28.7), (-2.0, 30.6)]
ax.plot([a for a, b in DL], [b for a, b in DL], "-", color="#444", lw=8, alpha=.4, label="U-drive")
ax.plot([8.97, 10.47], [28.55, 28.55], "rs", ms=6, label="walk piers")
for x, z, k in built: ax.add_patch(Circle((z, x), 0.6, fc="#888", ec="k")); ax.text(z, x - 1.6, "built\n" + k, ha="center", fontsize=7)
for x, z, h in lidar: ax.add_patch(Circle((z, x), 3.0, fc="none", ec="#1f8a2a", ls="--", lw=1.5)); ax.text(z, x + 3.3, f"lidar crown {h} m", ha="center", fontsize=7, color="#1f8a2a")
for x, z, d, k in prop: ax.add_patch(Circle((z, x), d / 2 * 1.5, fc="#c47a12", ec="k")); ax.text(z + 0.8, x + 0.8, "PROPOSED " + k, fontsize=7, color="#a05a00")
ax.set_xlim(32, -8); ax.set_ylim(-2, 33); ax.set_aspect("equal"); ax.set_xlabel("spec z (m): street view left = +z"); ax.set_ylabel("spec x (m), +x = Lincoln")
ax.set_title("Front-yard big trees: built (grey, old stick layout) vs lidar crowns (green) vs PROPOSED trunks (orange, not built)\nfilm 12030/11908/5545: two trunks right of the portico; the user's photo: one left of centre, an oak right of the portico", fontsize=9)
ax.legend(loc="lower left", fontsize=7); plt.tight_layout(); plt.savefig(sys.argv[1] if len(sys.argv) > 1 else "yard_trees.png")
