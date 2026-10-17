"""hifi_foyer_arch: the foyer's cased segmental arch (to the rear passage) through the artist pipeline (.claude/skills/artist-pipeline).

User, Oct 16: "the arch for example is jagged". The grey-box built the arch's top from 12 stepped slices (SpecGreybox.ArchTop);
they stay for collision only. This model draws, on the cut and from the cut's own numbers (spec/geometry.json ground opening
foyer/rear_passage: c, lo, hi, spring, height):
  - the soffit: a true segmental arc through the wall's thickness (chord error <= 0.5 mm), painted plaster, a 4 mm round on
    the passage edge (the foyer edge is under the casing);
  - the spandrels' two papered faces (materials FA_PaperPos/Neg: SpecGreybox gives them the room's own wallpaper, triplanar in
    world space, so the paper runs on from the wall boxes around them);
  - the casing on the foyer face (film 2677/3888): a flat band with a 3 mm rounded inner edge and an ovolo outer edge, 44 mm
    wide (film: 38-48 mm from the right leg, 2677 and 3888 cameras), 20 mm proud (the house's CasingProud; the film shows a
    shadow line beside it). A leg runs to the floor where a free wall face is beside the jamb (the picture-wall side); on the
    stair side the arc's casing dies into the stair's flank (Marina 195 s: the arch springs off the stair's end, no pier). The
    passage face has no free face beside either jamb (its side walls continue the reveal), so no casing there.
Faces flush against walls (casing backs, spandrel tops and ends) are not built: never seen.

Maps: high-poly (same profiles, 4 mm sampling, plaster 0.8 mm / paint 0.2 mm unevenness) baked in Cycles to normal, AO (with the
walls, landing, stair and floor round it as occluders) and a convex-edge mask; composed with Poly Haven white_plaster_02 (CC0)
tinted to the house's measured paints: soffit = ceiling paint, casing = door/casing paint (SpecGreybox mCeil / mProp).

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
OUT = Path("/private/tmp/claude-501/-Users-dlo-Dev-home-alone/fd5a08ea-1f93-4780-9824-223b49afa65a/scratchpad/out/FoyerArch.glb")
TEX = Path("/private/tmp/claude-501/-Users-dlo-Dev-home-alone/fd5a08ea-1f93-4780-9824-223b49afa65a/scratchpad/out/tex")
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
CW, CP, BEV = 0.044, 0.020, 0.004          # casing width, proud; plaster round on the bare (passage) edge
A0, A1 = math.atan2(SP - YC, LO - ZM), math.atan2(SP - YC, HI - ZM)   # springing angles in the (z, y) plane
PPM = 1024                                   # px per metre (hero piece, seen up close)
STAIR = [dict(b, y=[b["y"][0] - GY, b["y"][1] - GY]) for b in SPEC["stair"]["boxes"]]


def solid_at(x0, x1, z0, z1, y0, y1):
    """Does a wall or stair box occupy any of this region (spec, ground-relative y)?"""
    boxes = GEO["walls"] + [b for b in STAIR if b["kind"] in ("step", "landing")]
    return any(b["x"][0] < x1 - 1e-4 and b["x"][1] > x0 + 1e-4 and b["z"][0] < z1 - 1e-4 and b["z"][1] > z0 + 1e-4
               and b["y"][0] < y1 - 1e-4 and b["y"][1] > y0 + 1e-4 for b in boxes)


def free(face_x, s, z0, z1):
    """A free wall face beside a jamb: the wall stands behind it and nothing stands in front of it up to the springline."""
    return solid_at(face_x - s * 0.02, face_x, z0, z1, 0.0, SP) and not solid_at(face_x, face_x + s * 0.03, z0, z1, 0.05, SP)


def arch_path(r_off=0.0, fine=False):
    """The arc (z, y) from the lo springing to the hi springing at radius R + r_off, crown point included."""
    up = hp.arc(ZM, YC, R + r_off, A0, math.pi / 2, fine); down = hp.arc(ZM, YC, R + r_off, math.pi / 2, A1, fine)
    n = max(len(up), len(down)) - 1      # same count both halves (symmetric facets)
    up = [(ZM + (R + r_off) * math.cos(A0 + (math.pi / 2 - A0) * k / n), YC + (R + r_off) * math.sin(A0 + (math.pi / 2 - A0) * k / n)) for k in range(n + 1)]
    down = [(ZM + (R + r_off) * math.cos(math.pi / 2 + (A1 - math.pi / 2) * k / n), YC + (R + r_off) * math.sin(math.pi / 2 + (A1 - math.pi / 2) * k / n)) for k in range(n + 1)]
    return up + down[1:]


def build(fine):
    """Soffit + casing meshes (one detail level) and, at low detail, the papered spandrel faces."""
    step = 0.004 if fine else None
    sof, cas = hp.Mesh("Soffit_FoyerArch", "FA_Soffit"), hp.Mesh("Casing_FoyerArch", "FA_Casing")
    path = arch_path(fine=fine)
    if fine: path = hp.resample(path, step)
    # soffit: across the thickness from the passage face (round BEV) to the foyer face; placed on the foyer face plane, h toward +x
    place = lambda u, y, h: (X1 + h, y, u); toward = lambda du, dy, dh: (dh, dy, du)
    prof = hp.rounded([(BEV, -T), ("r", 0.0, -T), (0.0, 0.0)], BEV, fine)
    if fine: prof = hp.resample(prof, step)
    sof.sweep(path, prof, place, toward)
    # casing on the foyer face: lo leg (when free), the arc, and on a blocked jamb a short tail that the bisect below removes
    lo_free, hi_free = free(X1, 1, LO - CW, LO), free(X1, 1, HI, HI + CW)
    assert lo_free and not hi_free, (lo_free, hi_free)   # what the plan holds today (picture wall | stair flank); revisit if it changes
    cpath = ([(LO, 0.0)] if lo_free else [(LO, SP - 0.05)]) + path + ([(HI, 0.0)] if hi_free else [(HI, SP - 0.05)])
    if fine: cpath = hp.resample(cpath, step)
    ovolo = hp.arc(CW - 0.016, CP - 0.016, 0.016, math.pi / 2, 0.0, fine)            # ovolo: quarter round r 16 mm to the outer edge
    cprof = hp.rounded([(0.0, 0.0), ("r", 0.0, CP), (CW - 0.016, CP)], 0.003, fine)[:-1] + ovolo + [(CW, 0.0)]
    if fine: cprof = hp.resample(cprof, step)
    kinks = [i for i, p in enumerate(cpath) if min(math.dist(p, (LO, SP)), math.dist(p, (HI, SP))) < 1e-6]
    cas.sweep(cpath, cprof, place, toward, cuts=kinks)
    paper = []
    if not fine:   # papered spandrel faces: fans from the top corners to the arc; foyer face from R (under the casing), passage from R + BEV
        for s, x, r_off, mat in ((1, X1, 0.0, "FA_PaperPos"), (-1, X0, BEV, "FA_PaperNeg")):
            p = Part(f"Paper_FoyerArch_{'Pos' if s > 0 else 'Neg'}", mat)
            pts = [(min(max(z, LO), HI), min(y, CR)) for z, y in arch_path(r_off)]
            k = len(pts) // 2
            for corner, seg in (((LO, CR), pts[:k + 1]), ((HI, CR), pts[k:])):
                for (za, ya), (zb, yb) in zip(seg, seg[1:]):
                    area = abs((za - corner[0]) * (yb - corner[1]) - (zb - corner[0]) * (ya - corner[1])) / 2
                    if area > 1e-7:
                        p.face([(x, corner[1], corner[0]), (x, ya, za), (x, yb, zb)], (s, 0, 0))
            paper.append(p)
    return sof, cas, paper, (lo_free, hi_free)


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
mats = {k: bpy.data.materials.new(k) for k in ("FA_Soffit", "FA_Casing", "FA_PaperPos", "FA_PaperNeg")}
sof, cas, paper, sides = build(False)
sof_h, cas_h, _, _ = build(True)
hs = {"FA_Soffit": hp.pack([sof], PPM), "FA_Casing": hp.pack([cas], PPM)}
# the soffit's round stays inside the cut (jambs at LO/HI, crown CR: Arch fit checks it); the casing dies into the stair's flank
# 0.2 mm short of it
sof_cuts = [((C, 0.0, LO), (0, 0, -1)), ((C, 0.0, HI), (0, 0, 1)), ((C, CR, LO), (0, 1, 0))]
cas_cuts = [((C, 0.0, HI - 0.0002), (0, 0, 1))]
lows = [hp.to_object(sof, mats["FA_Soffit"], coll, cuts=sof_cuts), hp.to_object(cas, mats["FA_Casing"], coll, cuts=cas_cuts)]
highs = [hp.to_object(sof_h, bpy.data.materials.new("hs"), coll, hard_deg=60, cuts=sof_cuts), hp.to_object(cas_h, bpy.data.materials.new("hc"), coll, hard_deg=60, cuts=cas_cuts)]
hp.displace(highs[0], 0.03, 0.0008); hp.displace(highs[1], 0.012, 0.0002)
papers = [p.build(coll, mats) for p in paper]
occ = proxies(coll)
for o in lows:
    o.visible_diffuse = o.visible_glossy = o.visible_shadow = o.visible_transmission = False
sc_lo, sc_hi = hp.scan("white_plaster_02", "1k"), hp.scan("white_plaster_02", "2k")
spec = {   # measured paints (sRGB, the house's own: SpecGreybox mCeil / mProp), roughness, wear, grime, scan detail
    "FA_Soffit": dict(albedo=(0.92, 0.92, 0.90), rough=(0.80, 0.05), wear=0.12, grime=0.30, variation=0.5),
    "FA_Casing": dict(albedo=(0.95, 0.93, 0.86), rough=(0.40, 0.04), wear=0.35, grime=0.30, variation=0.15)}
final = []
for low, high in zip(lows, highs):
    name = low.active_material.name; s = spec[name]
    maps = hp.bake(low, high, 2048, hs[name], cage=0.003, occluders=[occ] + papers)
    mp = hp.compose(maps, sc_lo, s["albedo"], PPM, 1.0, s["variation"], s["rough"], s["wear"], s["grime"])
    extras = {"role": "baked", "albedo_srgb": list(s["albedo"]), "albedo_tol": 0.06, "ppm": PPM,
              "detail_tiling": [2048 / PPM / 0.5, hs[name] / PPM / 0.5], "scan": "polyhaven:white_plaster_02 (CC0)"}
    hp.write_unity_maps(TEX, name.split("_")[1], mp, hp.detail_map(sc_hi), extras)
    low.active_material.name = name + "_bake"   # the exported material keeps the plain name (SpecGreybox remaps by it)
    m = hp.pbr_material(name, mp, extras); low.data.materials.clear(); low.data.materials.append(m); final.append(low)
    print(name, {k: (float(v[..., 0].mean()), float(v[..., 0].std())) for k, v in maps.items()})
for p in papers:
    p.active_material["role"] = "system"; p.active_material["system"] = "wallpaper (SpecGreybox: the room's paper, triplanar)"
for o in [occ] + highs:
    bpy.data.objects.remove(o)
hp.export(OUT, final + papers, {"artist_pipeline": 1, "source": "tools/house/hifi_foyer_arch.py",
                                "lod_reason": "single LOD: ~%d triangles of architecture fixed to the walls; LOD swaps would open cracks at the wall joints"
                                % sum(len(o.data.polygons) * 2 for o in final + papers)})
print("wrote", OUT, "R", round(R, 4), "springs", A0, A1, "casing sides lo/hi free", sides, "atlas heights", hs)
