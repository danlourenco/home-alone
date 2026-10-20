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
# step 2 (Oct 20): what the kit builds, by tier: kit blocks (Tier 2 hero = orange, Tier 3 stand-in = blue), the street (nb_street),
# lamp posts (stars), trees placed from the re-registered lidar (green), the film 11581 camera and its view
import math
NBD = ROOT/"unity/HomeAlone/Assets/Models/Neighborhood"
if man and (NBD/"street_layout.json").exists():
    L = json.load(open(NBD/"street_layout.json"))
    import importlib.util; sp = importlib.util.spec_from_file_location("nbs", ROOT/"tools/house/nb_street.py")
    zz = [z0 + i*2 for i in range(int((z1-z0)/2)+1)]
    def cl(z):   # nb_street.centre without Blender imports
        CL = [(31.6, -110.7), (36.2, -92.4), (35.4, -66.7), (36.3, 0.5), (36.6, 26.0), (36.8, 38.1), (37.7, 112.2), (37.7, 260.0)]
        o = CL[0][0]
        for (xa, za), (xb, zb) in zip(CL, CL[1:]):
            if za <= z <= zb: o = xa + (xb-xa)*(z-za)/(zb-za)
        w = 0.0 if -45 <= z <= 65 else min(1.0, min(abs(z+45), abs(z-65))/20)
        return 36.3 + w*(o-36.3)
    zr = [z for z in zz if L["extent_z"][0] <= z <= L["extent_z"][1]]
    for a0, a1, c in ((-5.68, 5.0, "#3a3a44"), (-7.43, -5.93, "#c8c8c0"), (8.35, 9.85, "#c8c8c0")):
        ax.add_patch(Polygon([(z, cl(z)+a0) for z in zr] + [(z, cl(z)+a1) for z in reversed(zr)], fc=c, ec="none", alpha=.85, zorder=3))
    for d in L["drives"] + L["walks"]:
        ax.add_patch(Polygon([(d["z"]-d["w"]/2, d["x0"]), (d["z"]+d["w"]/2, d["x0"]), (d["z"]+d["w"]/2, d["x1"]), (d["z"]-d["w"]/2, d["x1"])], fc="#555" if d in L["drives"] else "#ddd", ec="none", zorder=3))
    for e in man["parcels"]:
        k = e.get("kit") or e.get("kit_auto")
        if not k: continue
        yaw = math.radians(k.get("yaw_deg", 0)); c_, s_ = math.cos(yaw), math.sin(yaw)
        for b in k["blocks"] + k.get("garages", []):
            pts = [(b["x"][0], b["z"][0]), (b["x"][1], b["z"][0]), (b["x"][1], b["z"][1]), (b["x"][0], b["z"][1])]
            pts = [(u*c_ - v*s_, u*s_ + v*c_) for u, v in pts]
            ax.add_patch(Polygon([(q[1], q[0]) for q in pts], fc="#d9661f" if e["tier"] == 2 else "#4a78b0", ec="k", lw=.8, zorder=4))
        if k.get("porch"):
            pc = k["porch"]; ax.add_patch(Polygon([(pc["z"][0], pc["x"][0]), (pc["z"][1], pc["x"][0]), (pc["z"][1], pc["x"][1]), (pc["z"][0], pc["x"][1])], fc="#f0b080", ec="k", lw=.5, zorder=4))
    ax.scatter([t["z"] for t in L["trees"]], [t["x"] for t in L["trees"]], s=[t["h_m"]*6 for t in L["trees"]], facecolors="none", edgecolors="#1f6b2a", lw=1.2, zorder=5)
    ax.scatter([q["z"] for q in L["lamps"]], [q["x"] for q in L["lamps"]], marker="*", s=90, c="#ffcc00", edgecolors="k", lw=.5, zorder=6)
    cj = ROOT/"art/home_alone/references/neighborhood/data/film11581_camera.json"
    if cj.exists():
        c = json.load(open(cj)); C = c["camera_spec_xyz"]; f = c["forward_spec"]; hf = math.atan(960/c["f_px"]); a = math.atan2(f[2], f[0])
        for t in (-hf, hf): ax.plot([C[2], C[2]+70*math.sin(a+t)], [C[0], C[0]+70*math.cos(a+t)], "m--", lw=1, zorder=6)
        ax.plot([C[2]], [C[0]], "mo", zorder=7); ax.text(C[2]-2, C[0]-4, "film 11581 camera", color="m", fontsize=8, zorder=7)
ax.set_xlim(z0 and z0, z1) if False else None
ax.set_xlim(z1, z0); ax.set_ylim(x0, x1); ax.set_aspect("equal")   # horizontal = spec z (reversed), vertical = spec x (front/street up)
ax.set_xlabel("spec z (m)"); ax.set_ylabel("spec x (m), +x = toward Lincoln Ave"); ax.set_title("Neighbourhood plan, step 2 (Oct 20). Parcels: tier 2 orange, tier 3 blue, our lot yellow. Kit houses: dark orange = Tier 2 hero (walkable), blue = Tier 3 stand-in.\nStreet (nb_street), drives dark, walks light; trees green rings (lidar, re-registered); lamps = stars; magenta = film 11581 camera + view; brown = 2022 footprints", fontsize=9)
plt.tight_layout(); plt.savefig(out, dpi=100)
