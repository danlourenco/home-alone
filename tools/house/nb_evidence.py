"""Neighbourhood evidence: Cook County parcels + footprints (+heights) and OSM -> spec frame, LiDAR trees.  Raw data: art/home_alone/references/neighborhood/data.
   uv run --with numpy --with pillow --with matplotlib --with tifffile python -I tools/house/nb_evidence.py [--fetch]  -> data/spec_frame.json (and plan.png via nb_plan)"""
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

# nDSM = ISGS Cook DSM 2022 - DTM 2022 (ft -> m). Oct 20 fix: the step-1 raster was georeferenced with the REQUESTED bbox, but ArcGIS
# exportImage widens the extent to square pixels and returns the real one: every tree was ~45 m off and the footprints sat on bare
# ground (median p25 0.1 m; registered now: 5.3 m). The npz keeps the server's extent; --fetch re-downloads (plain User-Agent).
from matplotlib.path import Path as MP
if "--fetch" in sys.argv:
    import io, urllib.request
    UA = {"User-Agent": "home-alone-house/1.0"}; url = "https://data.isgs.illinois.edu/arcgis/rest/services/Elevation/IL_Cook_{}_2022/ImageServer/exportImage"
    q = "?bbox=-87.7376,42.1070,-87.7296,42.1125&bboxSR=4326&imageSR=4326&size=1300,1100&format=tiff&pixelType=F32&noData=-9999&interpolation=RSP_BilinearInterpolation&f=json"
    get = lambda u: urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=120).read()
    import tifffile
    js = {k: json.loads(get(url.format(k) + q)) for k in ("DSM", "DTM")}
    r = {k: tifffile.imread(io.BytesIO(get(j["href"]))).astype(np.float32) for k, j in js.items()}
    e = js["DSM"]["extent"]; nn = (r["DSM"] - r["DTM"]) * 0.3048006; nn[(r["DSM"] < -9000) | (r["DTM"] < -9000)] = np.nan
    np.savez_compressed(P/"ndsm_m.npz", n=nn.astype(np.float16), extent=np.array([e["xmin"], e["ymin"], e["xmax"], e["ymax"]]))
z = np.load(P/"ndsm_m.npz"); n = np.nan_to_num(z["n"].astype(np.float32)); B = tuple(z["extent"])   # lon0, lat0, lon1, lat1 (server's)
H, W = n.shape
ii, jj = np.mgrid[0:H, 0:W]
lon = B[0] + (jj+.5)/W*(B[2]-B[0]); lat = B[3] - (ii+.5)/H*(B[3]-B[1])
sx, sz = F.spec(lat, lon)
pts = np.c_[sx.ravel(), sz.ravel()]
inb = np.zeros(len(pts), bool)
for f in fps: inb |= MP(f["poly"]).contains_points(pts, radius=-1.5)
inb = inb.reshape(H, W)
px = abs(float(sx[0, 1] - sx[0, 0]) + 1j * float(sz[0, 1] - sz[0, 0]))          # metres per pixel (~0.51)
k = max(1, round(3.0 / px)); pad = np.pad(n, k, constant_values=0); mx = np.max([pad[a:a+H, b:b+W] for a in range(2*k+1) for b in range(2*k+1)], axis=0)
tm = (n > 6) & (n >= mx) & ~inb                                                  # crowns: local maxima over 3 m, > 6 m, off the roofs
trees = [{"x": round(float(sx[a, b]), 1), "z": round(float(sz[a, b]), 1), "h_m": round(float(n[a, b]), 1)} for a, b in zip(*np.nonzero(tm))]
# per footprint: nDSM ridge (p95 inside) vs the county's Max_Point height
for f in fps:
    m = MP(f["poly"]).contains_points(pts, radius=0.5).reshape(H, W)
    f["lidar_p95_m"] = round(float(np.percentile(n[m], 95)), 1) if m.sum() > 3 else None
    f["lidar_p25_m"] = round(float(np.percentile(n[m], 25)), 1) if m.sum() > 3 else None   # ~eave/low roof
out = {"parcels": parcels, "footprints": fps, "roads": roads, "trees": trees}
(P/"spec_frame.json").write_text(json.dumps(out))
print(len(parcels), len(fps), len(roads), len(trees))
