"""Plan map of the neighbourhood evidence in the spec frame.  uv run --with numpy --with pillow --with matplotlib python -I tools/house/nb_plan.py [out.png] [x0 x1 z0 z1]"""
import json, sys
from pathlib import Path
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
ROOT = Path(__file__).resolve().parents[2]; N = ROOT/"art/home_alone/references/neighborhood"
d = json.load(open(N/"data/spec_frame.json")); man = json.load(open(ROOT/"spec/neighborhood.json")) if (ROOT/"spec/neighborhood.json").exists() else None
out = sys.argv[1] if len(sys.argv) > 1 else str(N/"plan.png")
x0, x1, z0, z1 = (map(float, sys.argv[2:6]) if len(sys.argv) > 5 else (-60, 120, -170, 190))
col = {1: "#e8b04a", 2: "#e0894b", 3: "#9ab8d8", 0: "#eeeeee"}
fig, ax = plt.subplots(figsize=(16, 8.5), dpi=100)
tier = {}; lab = {}
if man:
    for e in man["parcels"]:
        tier[e["parcel_idx"]] = e["tier"]; lab[e["parcel_idx"]] = e["id"]
for i, p in enumerate(d["parcels"]):
    t = tier.get(i, 0)
    ax.add_patch(Polygon([(q[1], q[0]) for q in p["poly"]], fc=col[t], ec="#999", lw=.5, alpha=.7 if t else .25))
    if i in lab:
        cx = sum(q[1] for q in p["poly"])/len(p["poly"]); cz = sum(q[0] for q in p["poly"])/len(p["poly"])
        ax.text(cx, cz, lab[i], fontsize=7, ha="center", color="#222")
for r in d["roads"]:
    ax.plot([q[1] for q in r["pts"]], [q[0] for q in r["pts"]], color="#556" if r["hw"] in ("residential", "tertiary", "secondary") else "#bbb", lw=3 if r["name"] == "Lincoln Avenue" else 1)
for f in d["footprints"]:
    ax.add_patch(Polygon([(q[1], q[0]) for q in f["poly"]], fc="#7a5a48", ec="k", lw=.4))
tr = [t for t in d["trees"] if x0 < t["x"] < x1 and z0 < t["z"] < z1]
ax.scatter([t["z"] for t in tr], [t["x"] for t in tr], s=[t["h_m"]*1.2 for t in tr], c="#3a7d3a", alpha=.45, lw=0)
# our house + piers + drive
DL = [(21.4,30.6),(21.4,24.4),(18.2,21.8),(13.5,20.2),(9.8,20.5),(3.9,22.7),(1.1,25.6),(-0.5,27.3),(-1.2,28.7),(-2.0,30.6)]
ax.plot([a for a,b in DL],[b for a,b in DL],"-",color="#444",lw=2.5);
ax.plot([-2.1, 21.4], [28.3, 28.3], "r-", lw=1); ax.plot([9.716-.75]*2, [28.3]*2, "rs", ms=4); ax.plot([9.716+.75]*2, [28.3]*2, "rs", ms=4)
ax.set_xlim(z0 and z0, z1) if False else None
ax.set_xlim(z1, z0); ax.set_ylim(x0, x1); ax.set_aspect("equal")   # horizontal = spec z (reversed), vertical = spec x (front/street up)
ax.set_xlabel("spec z (m)"); ax.set_ylabel("spec x (m), +x = toward Lincoln Ave"); ax.set_title("Neighbourhood evidence plan: tier 2 orange, tier 3 blue, our lot yellow; red = piers")
plt.tight_layout(); plt.savefig(out, dpi=100)
