"""Build spec/neighborhood.json (draft, status 'evidence') + boards from data/spec_frame.json and film_index.json.
   uv run --with numpy --with pillow --with matplotlib python -I tools/house/nb_manifest.py"""
import json, math, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]; N = ROOT/"art/home_alone/references/neighborhood"
d = json.load(open(N/"data/spec_frame.json"))
def cen(p): return (sum(q[0] for q in p)/len(p), sum(q[1] for q in p)/len(p))
def pip(p, pg):
    c = False
    for (a, b), (e, g) in zip(pg, pg[1:]+pg[:1]):
        if (b > p[1]) != (g > p[1]) and p[0] < (e-a)*(p[1]-b)/(g-b)+a: c = not c
    return c
r1 = lambda p: [[round(a, 2), round(b, 2)] for a, b in p]
# rows along Lincoln (indices found by the front-edge x of each parcel; see RESUME plan)
rows = {"A": {}, "B": {}}
for i, p in enumerate(d["parcels"]):
    xs = [q[0] for q in p["poly"]]; c = cen(p["poly"])
    if not -200 < c[1] < 200: continue
    if 24 < max(xs) < 31 and max(xs)-min(xs) > 20: rows["A"][i] = c[1]
    elif 42 < min(xs) < 56 and max(xs)-min(xs) > 20: rows["B"][i] = c[1]
ORDER = {k: sorted(v, key=v.get) for k, v in rows.items()}
OURS, MUR = 10, 32                        # parcel indices containing the house / straight across
assert pip((5, 9.7), d["parcels"][OURS]["poly"])
FILM = json.load(open(N/"film_index.json"))["parcels"]
manifest = []
for row, anchor in (("A", OURS), ("B", MUR)):
    k0 = ORDER[row].index(anchor)
    for k, i in enumerate(ORDER[row]):
        off = k-k0
        c = rows[row][i]
        if abs(off) > 6 or abs(c-9.7) > 160: continue
        lid = f"lot_{row}{off:+d}" if off else f"lot_{row}0"
        tier = 1 if (row == "A" and off == 0) else 2 if abs(off) <= 1 else 3
        P = d["parcels"][i]["poly"]
        bl = [f for f in d["footprints"] if pip(cen(f["poly"]), P)]
        main = max(bl, key=lambda f: f["area_m2"]) if bl else None
        ent = {"id": lid, "tier": tier, "parcel_idx": i, "side": "mccallister_side" if row == "A" else "across_lincoln",
               "film_role": {"lot_A0": "McCallister lot", "lot_B0": "Murphys"}.get(lid),
               "parcel_poly_spec": r1(P), "parcel_source": "Cook County Clerk cadastre (clerkCadastre layer 1), reprojected to spec by tools/house/nb_frame.py",
               "buildings": []}
        for f in sorted(bl, key=lambda f: -f["area_m2"]):
            xs = [q[0] for q in f["poly"]]; zs = [q[1] for q in f["poly"]]
            short = min(max(xs)-min(xs), max(zs)-min(zs)); ridge = f["ridge_m"]   # county lidar max-ground; the nDSM p95 is raised by overhanging trees
            ent["buildings"].append({"footprint_spec": r1(f["poly"]), "area_m2": f["area_m2"], "footprint_source": "Cook County building footprints 2022 (buildingFootprint_2022)",
                 "height_source": "Cook County 2022 footprint Height (max point - ground, lidar); ISGS Cook DSM-DTM 2022 sampled as a cross-check",
                 "ridge_m": ridge, "ndsm_p95_m_tree_contaminated": f["lidar_p95_m"],
                 "eave_m_estimate": round(max(2.5, ridge-0.33*short), 1), "eave_note": "ESTIMATE: ridge minus 8:12 pitch rise over the short span; hip/gable and storeys unconfirmed",
                 "main": f is main})
        ent["trees_over_6m"] = [t for t in d["trees"] if pip((t["x"], t["z"]), P)]
        ev = FILM.get(lid, {})
        ent.update({"style_kit_guess": ev.get("style", "unknown: 1900s-30s North Shore frame/brick house, from massing only"), "evidence_frames": ev.get("frames", []),
                    "confidence": ev.get("confidence", "low"), "status": "evidence"})
        if ev.get("note"): ent["note"] = ev["note"]
        manifest.append(ent)
# step 3 (Oct 20): Tier 3 reaches every parcel fronting Lincoln within z -160..160, including past the fork (z -67), the bend west
# (z -110) and north of Pine (z 112): parcels whose edge lies within 16 m of Lincoln's OSM centreline, not already in a row. Neutral ids
# lot_P<parcel index>; side by which side of the street's direction they lie on (A = ours).
def _segd(p, a, b):
    dx, dz = b[0]-a[0], b[1]-a[1]; t = max(0, min(1, ((p[0]-a[0])*dx + (p[1]-a[1])*dz) / (dx*dx + dz*dz + 1e-9)))
    return math.hypot(p[0]-a[0]-t*dx, p[1]-a[1]-t*dz), (a[0]+t*dx, a[1]+t*dz), (dx, dz)
LIN = [r["pts"] for r in d["roads"] if r["name"] == "Lincoln Avenue"]
have = {e["parcel_idx"] for e in manifest}
for i, p in enumerate(d["parcels"]):
    c = cen(p["poly"])
    if i in have or not -160 < c[1] < 160: continue
    best = min((_segd(q, a, b) for q in p["poly"] for r in LIN for a, b in zip(r, r[1:])), key=lambda t: t[0])
    if best[0] > 16: continue
    bl = [f for f in d["footprints"] if pip(cen(f["poly"]), p["poly"])]
    if not bl: continue
    main = max(bl, key=lambda f: f["area_m2"])
    dd, q, (dx, dz) = best; sd = dx * (c[1] - q[1]) - dz * (c[0] - q[0])   # sign: which side of the centreline's direction
    ent = {"id": f"lot_P{i}", "tier": 3, "parcel_idx": i, "side": "across_lincoln" if (sd < 0) == (c[0] > 36) else "mccallister_side", "film_role": None,
           "parcel_poly_spec": r1(p["poly"]), "parcel_source": "Cook County Clerk cadastre (clerkCadastre layer 1), reprojected to spec by tools/house/nb_frame.py",
           "buildings": [{"footprint_spec": r1(f["poly"]), "area_m2": f["area_m2"], "footprint_source": "Cook County building footprints 2022 (buildingFootprint_2022)",
                          "height_source": "Cook County 2022 footprint Height (max point - ground, lidar)", "ridge_m": f["ridge_m"],
                          "ndsm_p95_m_tree_contaminated": f["lidar_p95_m"], "main": f is main} for f in sorted(bl, key=lambda f: -f["area_m2"])],
           "trees_over_6m": [t for t in d["trees"] if pip((t["x"], t["z"]), p["poly"])],
           "style_kit_guess": "unknown: 1900s-30s North Shore frame/brick house, from massing only", "evidence_frames": [], "confidence": "low",
           "status": "evidence", "note": "step 3 extension: fronts Lincoln past the Tier 2/3 rows (fork, bend or north of Pine)"}
    ent["side"] = "across_lincoln" if c[0] > 36.3 and -110 < c[1] < 112 else ent["side"]
    manifest.append(ent)
# keep what later steps added (kits, budgets, street, tiers: tools/house/nb_kits.py) so a re-run only refreshes the evidence
_old = json.loads((ROOT/"spec/neighborhood.json").read_text()) if (ROOT/"spec/neighborhood.json").exists() else {}
_prev = {e["id"]: e for e in _old.get("parcels", [])}
for ent in manifest:
    for k, v in _prev.get(ent["id"], {}).items():
        if k not in ent: ent[k] = v
out = {"_comment": "DRAFT evidence manifest (Oct 19 2026). Spec metres, +x toward Lincoln Ave (front). Lot ids are neutral: A = Lincoln's McCallister side, B = across the street; +n is toward +z (film-left from the street). Heights are 2022 lidar, post-1990: trees and additions differ from 1990.",
       "frame": "tools/house/nb_frame.py", "parcels": manifest}
for k, v in _old.items():
    if k not in out: out[k] = v
(ROOT/"spec/neighborhood.json").write_text(json.dumps(out, indent=1))
print(len(manifest), [(e["id"], e["tier"], len(e["buildings"])) for e in manifest])
