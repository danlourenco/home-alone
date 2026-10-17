"""hifi_foyer_arch: the foyer's segmental arch (to the rear passage) through the artist pipeline (.claude/skills/artist-pipeline).

User, Oct 16: "the arch for example is jagged". The grey-box built the arch's top from 12 stepped slices (SpecGreybox.ArchTop);
they stay for collision only. This model draws, on the cut and from the cut's own numbers (spec/geometry.json ground opening
foyer/rear_passage: c, lo, hi, spring, height):
  - the soffit: a true segmental arc through the wall's thickness (chord error <= 0.5 mm), painted plaster, a 4 mm round on
    both edges;
  - the spandrels' two papered faces (materials FA_PaperPos/Neg: SpecGreybox gives them the room's own wallpaper, triplanar in
    world space, so the paper runs on from the wall boxes around them);
  - NO casing (Oct 17, user walk: 'why do i see a cased vertical thing coming down from the arch?'): the film's arch is plain,
    the paper runs to the arris. Through the solved cameras the 44 mm zone beside the picture-wall jamb is dark paper (2677
    luminance 14-38 vs 97-113 on the white strip; 1616 45-74), and 3175 shows paper to the jamb's arris; the white strip read
    on Oct 16 as the casing's leg lies inside the jamb, where the closet door stands (its knob is on it in 2677).
Faces flush against walls (spandrel tops and ends) are not built: never seen.

Maps: high-poly (same profiles, 4 mm sampling, plaster 0.8 mm / paint 0.2 mm unevenness) baked in Cycles to normal, AO (with the
walls, landing, stair and floor round it as occluders) and a convex-edge mask; composed with Poly Haven white_plaster_02 (CC0)
tinted to the house's measured ceiling paint (SpecGreybox mCeil).

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P tools/house/hifi_foyer_arch.py
  -> unity/HomeAlone/Assets/Models/Foyer/FoyerArch.glb + Assets/Textures/Generated/FoyerArch/*.png (SpecGreybox.ArchModel)
"""
import json
import math
import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
import hifi_pipeline as hp   # noqa: E402
from hifi_lib import Part   # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "unity/HomeAlone/Assets/Models/Foyer/FoyerArch.glb"
TEX = ROOT / "unity/HomeAlone/Assets/Textures/Generated/FoyerArch"
GEO = json.loads((ROOT / "spec/geometry.json").read_text())["ground"]
SPEC = json.loads((ROOT / "spec/house_spec.json").read_text())
GY = json.loads((ROOT / "spec/house_spec.ground.json").read_text())["floor_y_m"]
O = next(o for o in GEO["openings"] if o["kind"] == "arch" and sorted(o["between"]) == ["foyer", "rear_passage"])
assert O["axis"] == "x" and O["spring"], O
C, LO, HI, SP, CR = O["c"], O["lo"], O["hi"], O["spring"], O["height"]
WALL = next(w for w in GEO["walls"] if abs(w["z"][1] - LO) < 1e-4 and w["x"][0] < C < w["x"][1])   # the wall the arch is cut in
X0, X1 = WALL["x"]; T = X1 - X0
HALF, RISE = (HI - LO) / 2, CR - SP
R = (HALF ** 2 + RISE ** 2) / (2 * RISE); ZM, YC = (LO + HI) / 2, CR - R
BEV = 0.004                                 # plaster round on both arrises
A0, A1 = math.atan2(SP - YC, LO - ZM), math.atan2(SP - YC, HI - ZM)   # springing angles in the (z, y) plane
PPM = 1024                                   # px per metre (hero piece, seen up close)
DETAIL_ALBEDO = 0.25                         # share of the plaster scan's albedo variation kept on paint (the gate allows +-2 x albedo_tol)
STAIR = [dict(b, y=[b["y"][0] - GY, b["y"][1] - GY]) for b in SPEC["stair"]["boxes"]]


def arch_path(r_off=0.0, fine=False):
    """The arc (z, y) from the lo springing to the hi springing at radius R + r_off, crown point included."""
    up = hp.arc(ZM, YC, R + r_off, A0, math.pi / 2, fine); down = hp.arc(ZM, YC, R + r_off, math.pi / 2, A1, fine)
    n = max(len(up), len(down)) - 1      # same count both halves (symmetric facets)
    up = [(ZM + (R + r_off) * math.cos(A0 + (math.pi / 2 - A0) * k / n), YC + (R + r_off) * math.sin(A0 + (math.pi / 2 - A0) * k / n)) for k in range(n + 1)]
    down = [(ZM + (R + r_off) * math.cos(math.pi / 2 + (A1 - math.pi / 2) * k / n), YC + (R + r_off) * math.sin(math.pi / 2 + (A1 - math.pi / 2) * k / n)) for k in range(n + 1)]
    return up + down[1:]


def build(fine):
    """Soffit mesh (one detail level) and, at low detail, the papered spandrel faces."""
    step = 0.004 if fine else None
    sof = hp.Mesh("Soffit_FoyerArch", "FA_Soffit")
    path = arch_path(fine=fine)
    if fine: path = hp.resample(path, step)
    # soffit: across the thickness from the passage face (round BEV) to the foyer face; placed on the foyer face plane, h toward +x
    place = lambda u, y, h: (X1 + h, y, u); toward = lambda du, dy, dh: (dh, dy, du)
    prof = hp.rounded([(BEV, -T), ("r", 0.0, -T), ("r", 0.0, 0.0), (BEV, 0.0)], BEV, fine)
    if fine: prof = hp.resample(prof, step)
    sof.sweep(path, prof, place, toward)
    paper = []
    if not fine:   # papered spandrel faces: fans from the top corners to the arc, from R + BEV (where the soffit's round ends)
        for s, x, r_off, mat in ((1, X1, BEV, "FA_PaperPos"), (-1, X0, BEV, "FA_PaperNeg")):
            p = Part(f"Paper_FoyerArch_{'Pos' if s > 0 else 'Neg'}", mat)
            pts = [(min(max(z, LO), HI), min(y, CR)) for z, y in arch_path(r_off)]
            k = len(pts) // 2
            for corner, seg in (((LO, CR), pts[:k + 1]), ((HI, CR), pts[k:])):
                for (za, ya), (zb, yb) in zip(seg, seg[1:]):
                    area = abs((za - corner[0]) * (yb - corner[1]) - (zb - corner[0]) * (ya - corner[1])) / 2
                    if area > 1e-7:
                        p.face([(x, corner[1], corner[0]), (x, ya, za), (x, yb, zb)], (s, 0, 0))
            paper.append(p)
    return sof, paper


def proxies(coll):
    """Occluders for the AO bake: walls, ceilings, floor, landing and stair boxes within 1.5 m of the arch (not exported)."""
    p = Part("Occluders", "occ")
    near = lambda b: b["x"][0] < C + 1.5 and b["x"][1] > C - 1.5 and b["z"][0] < HI + 1.5 and b["z"][1] > LO - 1.5
    for b in GEO["walls"] + GEO["ceilings"] + GEO["floor"] + [b for b in STAIR if b["kind"] in ("step", "landing")]:
        if near(b) and b["y"][1] > -0.5:
            p.box(b["x"][0], b["x"][1], b["y"][0], b["y"][1], b["z"][0], b["z"][1])
    return p.build(coll, {"occ": bpy.data.materials.new("occ")})


bpy.ops.wm.read_factory_settings(use_empty=True)
coll = bpy.context.scene.collection
mats = {k: bpy.data.materials.new(k) for k in ("FA_Soffit", "FA_PaperPos", "FA_PaperNeg")}
sof, paper = build(False)
sof_h, _ = build(True)
hs = {"FA_Soffit": hp.pack([sof], PPM)}
# the soffit's rounds stay inside the cut (jambs at LO/HI, crown CR: Arch fit checks it)
sof_cuts = [((C, 0.0, LO), (0, 0, -1)), ((C, 0.0, HI), (0, 0, 1)), ((C, CR, LO), (0, 1, 0))]
lows = [hp.to_object(sof, mats["FA_Soffit"], coll, cuts=sof_cuts)]
highs = [hp.to_object(sof_h, bpy.data.materials.new("hs"), coll, hard_deg=60, cuts=sof_cuts)]
hp.displace(highs[0], 0.03, 0.0008)
papers = [p.build(coll, mats) for p in paper]
occ = proxies(coll)
for o in lows:
    o.visible_diffuse = o.visible_glossy = o.visible_shadow = o.visible_transmission = False
sc_lo, sc_hi = hp.scan("white_plaster_02", "1k"), hp.scan("white_plaster_02", "2k")
spec = {   # measured paints (sRGB, the house's own: SpecGreybox mCeil / mProp), roughness, wear, grime, scan detail
    "FA_Soffit": dict(albedo=(0.92, 0.92, 0.90), rough=(0.80, 0.05), wear=0.12, grime=0.30, variation=0.5)}
final = []
for low, high in zip(lows, highs):
    name = low.active_material.name; s = spec[name]
    maps = hp.bake(low, high, 2048, hs[name], cage=0.003, occluders=[occ] + papers)
    mp = hp.compose(maps, sc_lo, s["albedo"], PPM, 1.0, s["variation"], s["rough"], s["wear"], s["grime"])
    extras = {"role": "baked", "albedo_srgb": list(s["albedo"]), "albedo_tol": 0.06, "ppm": PPM,
              "detail_tiling": [2048 / PPM / 0.5, hs[name] / PPM / 0.5], "scan": "polyhaven:white_plaster_02 (CC0)"}
    # the scan is raw plaster: its pits (detail albedo 0.18-0.84) read as dirt on paint (Oct 17 renders; model_quality albedo).
    # Painted plaster keeps a quarter of that variation (about +-3 % of the paint); the detail normal carries the texture
    det = hp.detail_map(sc_hi); det[..., 0] = 0.5 + (det[..., 0] - 0.5) * DETAIL_ALBEDO
    hp.write_unity_maps(TEX, name.split("_")[1], mp, det, extras)
    low.active_material.name = name + "_bake"   # the exported material keeps the plain name (SpecGreybox remaps by it)
    m = hp.pbr_material(name, mp, extras); low.data.materials.clear(); low.data.materials.append(m); final.append(low)
    print(name, {k: (float(v[..., 0].mean()), float(v[..., 0].std())) for k, v in maps.items()})
for p in papers:
    p.active_material["role"] = "system"; p.active_material["system"] = "wallpaper (SpecGreybox: the room's paper, triplanar)"
for o in [occ] + highs:
    bpy.data.objects.remove(o)
bpy.context.view_layer.update()   # drop the removed objects from the view layer (export iterates it)
hp.export(OUT, final + papers, {"artist_pipeline": 1, "source": "tools/house/hifi_foyer_arch.py",
                                "lod_reason": "single LOD: ~%d triangles of architecture fixed to the walls; LOD swaps would open cracks at the wall joints"
                                % sum(len(o.data.polygons) * 2 for o in final + papers)})
print("wrote", OUT, "R", round(R, 4), "springs", A0, A1, "atlas heights", hs)
