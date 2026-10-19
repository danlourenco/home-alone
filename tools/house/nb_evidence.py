"""Neighbourhood evidence: Cook County parcels + footprints (+heights) and OSM -> spec frame, LiDAR trees.  Raw data: art/home_alone/references/neighborhood/data.
   uv run --with numpy --with pillow --with matplotlib python -I tools/house/nb_evidence.py  -> data/spec_frame.json (and plan.png via nb_plan)"""
import json, math, sys
from pathlib import Path
import numpy as np
from PIL import Image
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/house"))
import nb_frame as F
P = ROOT / "art/home_alone/references/neighborhood/data"
FT = 0.3048

def ring(r): return [F.spec(y, x) for x, y in r]
def area(p): return abs(sum(a[0]*b[1]-b[0]*a[1] for a, b in zip(p, p[1:]+p[:1])))/2
def cen(p): return (sum(q[0] for q in p)/len(p), sum(q[1] for q in p)/len(p))
def pip(p, pg):
    c = False
    for (a, b), (e, g) in zip(pg, pg[1:]+pg[:1]):
        if (b > p[1]) != (g > p[1]) and p[0] < (e-a)*(p[1]-b)/(g-b)+a: c = not c
    return c

parcels = [{"id": f"P{i:03d}", "poly": ring(f["geometry"]["rings"][0])} for i, f in enumerate(json.load(open(P/"cook-parcels.json"))["features"])]
fps = []
for i, f in enumerate(json.load(open(P/"cook-footprints.json"))["features"]):
    a = f["attributes"]
    fps.append({"id": f"B{i:03d}", "poly": ring(f["geometry"]["rings"][0]), "ridge_m": round(a["Height"]*FT, 1),
                "ground_m": round(a["Ground_Z"]*FT, 1), "max_m": round(a["Max_Point"]*FT, 1), "area_m2": round(area(ring(f["geometry"]["rings"][0])), 1)})
osm = json.load(open(P/"osm-200m.json"))
roads = [{"hw": e["tags"]["highway"], "name": e["tags"].get("name"), "pts": [F.spec(p["lat"], p["lon"]) for p in e["geometry"]]} for e in osm["elements"] if e["type"] == "way" and "highway" in e["tags"]]

# nDSM (ISGS Cook 2022 DSM - DTM, ft->m, 600x600 over B) -> trees: local maxima > 6 m outside buildings
from matplotlib.path import Path as MP
B = (-87.7376, 42.1070, -87.7296, 42.1125)
n = np.load(P/"ndsm_m.npz")["n"].astype(np.float32)
H, W = n.shape
ii, jj = np.mgrid[0:H, 0:W]
lon = B[0] + (jj+.5)/W*(B[2]-B[0]); lat = B[3] - (ii+.5)/H*(B[3]-B[1])
sx = np.vectorize(lambda a, b: F.spec(a, b)[0])(lat[::1, ::1], lon); sz = np.vectorize(lambda a, b: F.spec(a, b)[1])(lat, lon)
pts = np.c_[sx.ravel(), sz.ravel()]
inb = np.zeros(len(pts), bool)
for f in fps: inb |= MP(f["poly"]).contains_points(pts, radius=-1.5)
inb = inb.reshape(H, W)
k = 3; pad = np.pad(n, k, constant_values=0); mx = np.max([pad[a:a+H, b:b+W] for a in range(2*k+1) for b in range(2*k+1)], axis=0)
tm = (n > 6) & (n >= mx) & ~inb
trees = [{"x": round(float(sx[a, b]), 1), "z": round(float(sz[a, b]), 1), "h_m": round(float(n[a, b]), 1)} for a, b in zip(*np.nonzero(tm))]
# per footprint: nDSM ridge (p95 inside) vs the county's Max_Point height
for f in fps:
    m = MP(f["poly"]).contains_points(pts, radius=0.5).reshape(H, W)
    f["lidar_p95_m"] = round(float(np.percentile(n[m], 95)), 1) if m.sum() > 3 else None
    f["lidar_p25_m"] = round(float(np.percentile(n[m], 25)), 1) if m.sum() > 3 else None   # ~eave/low roof
out = {"parcels": parcels, "footprints": fps, "roads": roads, "trees": trees}
(P/"spec_frame.json").write_text(json.dumps(out))
print(len(parcels), len(fps), len(roads), len(trees))
