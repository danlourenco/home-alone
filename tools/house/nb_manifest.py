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
