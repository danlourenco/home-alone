"""hifi_hall_arches: the upstairs hall's three arches through the artist pipeline (tools/house/hifi_pipeline.py, the foyer arch's helpers;
changes/2026-10-17-upstairs-arches.json, DEVIATIONS 64).

- B (hall_corridor | hall_corridor_south) and C (hall_end | hall_corridor): plain plastered SEGMENTAL arches painted with the hall
  (film 410 / 2055 / 10828), drawn on the cut's own numbers (spec/geometry.json upstairs openings: c, lo, hi, spring, height): a true
  arc soffit through the 14 cm wall with a 5 mm round on both edges, and the painted spandrel faces on both sides (material AR_Paint:
  SpecGreybox.Hall gives them the hall's paint). The grey-box's stepped slices (SpecGreybox.ArchTop) stay as colliders only.
- A (the gallery arch, film 2080-2100 / 2085: a wide, shallow HALF-ELLIPSE between the stair well's gallery and the hall, papered with
  the stair well's damask on its well face and the soffit, painted on its hall face: Oct 18): a 10 cm header in the plane x 5.547-5.647 from the gallery's back wall
  (z 7.778) to the wall at z 11.43, springing at 2.04 (film 2085, refcam film-2085: 2.029 / 2.060) to a crown of 2.30 under our 2.40
  ceiling (film: 2.39 under a ~2.6 m set ceiling; DEVIATIONS 64). It is dressing above head height (no wall in the spec: the wall
  graph has no header over a rail, and the arch spans the gallery's open side and the balustrade): hall.json "arch_a".

Maps (B and C soffits): high-poly (same profiles, 4 mm sampling, plaster 0.8 mm unevenness) baked in Cycles to normal, AO (with the
walls round it as occluders) and a convex-edge mask, composed with Poly Haven white_plaster_02 (CC0) tinted to the hall's measured
paint (finishes.json, film). The papered and painted flat faces take the room's own triplanar materials in Unity (paper continuity).

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P tools/house/hifi_hall_arches.py
  -> unity/HomeAlone/Assets/Models/Foyer/HallArches.glb + Assets/Textures/Generated/HallArches/*.png (SpecGreybox.Hall)
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
OUT = ROOT / "unity/HomeAlone/Assets/Models/Foyer/HallArches.glb"
TEX = ROOT / "unity/HomeAlone/Assets/Textures/Generated/HallArches"
GEO = json.loads((ROOT / "spec/geometry.json").read_text())["upstairs"]
HALL = json.loads((ROOT / "spec/dressing/hall.json").read_text())
PAINT = json.loads((ROOT / "spec/dressing/finishes.json").read_text())["rooms"]["hall_corridor"]["upper"]
H, RND, PPM = 0.07, 0.005, 1024          # half wall thickness (B, C), edge round, texel density (hero: seen up close)
DETAIL_ALBEDO = 0.25                     # share of the raw plaster scan's albedo variation kept on paint (as hifi_foyer_arch.py; model_quality +-2 x albedo_tol)


def arch_spec(pair):
    o = next(o for o in GEO["openings"] if o["kind"] == "arch" and sorted(o["between"]) == sorted(pair))
    assert o["axis"] == "z" and o["spring"], o
    return o


def segment(lo, hi, sp, cr, off=0.0, fine=False):
    """the segmental arc (u along the span, y) from lo to hi springing, offset `off` outward (into the spandrel)"""
    half, rise = (hi - lo) / 2, cr - sp; R = (half ** 2 + rise ** 2) / (2 * rise); um, yc = (lo + hi) / 2, cr - R
    a0, a1 = math.atan2(sp - yc, lo - um), math.atan2(sp - yc, hi - um)
    n = hp.segments(R + off, a0 - a1, fine) * (4 if fine else 1)
    n += n % 2
    return [(um + (R + off) * math.cos(a0 + (a1 - a0) * k / n), yc + (R + off) * math.sin(a0 + (a1 - a0) * k / n)) for k in range(n + 1)]


def ellipse(lo, hi, sp, cr, off=0.0, fine=False):
    """the half-ellipse (vertical at the springs), offset `off` along its outward normal"""
    a, b, um = (hi - lo) / 2, cr - sp, (lo + hi) / 2
    # parameter steps fine enough for the chord error on the sharpest part (radius b^2 / a at the crown, a^2 / b... take the min)
    rmin = min(b * b / a, a * a / b); n = max(hp.segments(rmin, math.pi) * 2, 96) * (4 if fine else 1)
    pts = []
    for k in range(n + 1):
        t = math.pi - math.pi * k / n
        x, y = a * math.cos(t), b * math.sin(t); nx, ny = b * math.cos(t), a * math.sin(t); L = math.hypot(nx, ny)
        pts.append((um + x + off * nx / L, sp + y + off * ny / L))
    return pts


def build(name, curve, args, faces, face_mats, top, fine, soffit_mat):
    """soffit sweep between the two faces (u along the span: spec x for B/C, z for A) and the flat spandrel faces up to `top`"""
    path = curve(*args, fine=fine)
    if fine:
        path = hp.resample(path, 0.004)
    (f0, f1), ax = faces, name != "A"
    T = f1 - f0
    if ax:   # B, C: the wall runs along x at z f0..f1; u = x
        place = lambda u, y, h: (u, y, f1 - h); toward = lambda du, dy, dh: (du, dy, -dh)
    else:    # A: the header runs along z at x f0..f1; u = z
        place = lambda u, y, h: (f1 - h, y, u); toward = lambda du, dy, dh: (-dh, dy, du)
    prof = hp.rounded([(RND, 0.0), ("r", 0.0, 0.0), ("r", 0.0, T), (RND, T)], RND, fine)
    if fine:
        prof = hp.resample(prof, 0.004)
    sof = hp.Mesh(f"Soffit_{name}", soffit_mat)
    sof.sweep(path, prof, place, toward)
    papers = []
    if not fine:
        lo, hi = path[0][0], path[-1][0]
        for fc, h, mat in ((f1, 0.0, face_mats[1]), (f0, T, face_mats[0])):
            sgn = 1 if fc == f1 else -1
            p = Part(f"Face_{name}_{'Pos' if sgn > 0 else 'Neg'}", mat)
            pts = curve(*args, off=RND)
            pts = [(min(max(u, lo), hi), min(y, top)) for u, y in pts]
            k = len(pts) // 2
            P = (lambda u, y: (u, y, fc)) if ax else (lambda u, y: (fc, y, u))
            nrm = (0, 0, sgn) if ax else (sgn, 0, 0)
            for corner, seg in (((lo, top), pts[:k + 1]), ((hi, top), pts[k:])):
                for (ua, ya), (ub, yb) in zip(seg, seg[1:]):
                    if abs((ua - corner[0]) * (yb - corner[1]) - (ub - corner[0]) * (ya - corner[1])) > 2e-7:
                        p.face([P(*corner), P(ua, ya), P(ub, yb)], nrm)
            if top > max(y for _, y in pts) + 1e-4:   # the band over the crown (A: the header up to the ceiling)
                p.face([P(lo, top), P(*pts[k]), P(hi, top)], nrm)
            papers.append(p)
    return sof, papers


bpy.ops.wm.read_factory_settings(use_empty=True)
coll = bpy.context.scene.collection
M = {k: bpy.data.materials.new(k) for k in ("AR_Paint", "AR_Paper", "AR_SoffitB", "AR_SoffitC")}
lows, highs, flat, cuts = [], [], [], {}
for name, pair in (("B", ("hall_corridor", "hall_corridor_south")), ("C", ("hall_end", "hall_corridor"))):
    o = arch_spec(pair); args = (o["lo"], o["hi"], o["spring"], o["height"])
    faces = (o["c"] - H, o["c"] + H)
    lo_m, papers = build(name, segment, args, faces, ("AR_Paint", "AR_Paint"), o["height"], False, f"AR_Soffit{name}")
    hi_m, _ = build(name, segment, args, faces, None, o["height"], True, f"AR_Soffit{name}")
    cuts[name] = [((o["lo"], 0.0, o["c"]), (-1, 0, 0)), ((o["hi"], 0.0, o["c"]), (1, 0, 0)), ((o["lo"], o["height"], o["c"]), (0, 1, 0))]
    lows.append((name, lo_m)); highs.append(hi_m); flat += papers
a = HALL["arch_a"]
# A's faces: the stair well's damask on the well side (x 5.547; film 2084), the hall's paint on the hall side (x 5.647; film 10828, the
# header over the ficus reads teal; walk note 2026-10-17T08:28:20 "the wallpaper should actually be paint on this side of the arch")
sofA, papersA = build("A", ellipse, (a["z"][0], a["z"][1], a["spring"], a["crown"]), tuple(a["x"]), ("AR_Paper", "AR_Paint"), a["top"], False, "AR_Paper")
flat += papersA

hs = {n: hp.pack([m], PPM) for n, m in lows}
objs_low = [hp.to_object(m, M[f"AR_Soffit{n}"], coll, cuts=cuts[n]) for n, m in lows]
objs_high = [hp.to_object(m, bpy.data.materials.new(f"h{n}"), coll, hard_deg=60, cuts=cuts[n]) for (n, _), m in zip(lows, highs)]
for o in objs_high:
    hp.displace(o, 0.03, 0.0008)
flat_objs = [p.build(coll, M) for p in flat]
sofA_obj = hp.to_object(sofA, M["AR_Paper"], coll, cuts=[((5.6, 0.0, a["z"][0]), (0, 0, -1)), ((5.6, 0.0, a["z"][1]), (0, 0, 1))])


def proxies():
    p = Part("Occluders", "occ")
    for b in GEO["walls"] + GEO["ceilings"]:
        if b["x"][0] < 8.5 and b["x"][1] > 5.0 and b["z"][0] < 12.5 and b["z"][1] > 6.7:
            p.box(b["x"][0], b["x"][1], b["y"][0], b["y"][1], b["z"][0], b["z"][1])
    return p.build(coll, {"occ": bpy.data.materials.new("occ")})


occ = proxies()
for o in objs_low:
    o.visible_diffuse = o.visible_glossy = o.visible_shadow = o.visible_transmission = False
sc_lo, sc_hi = hp.scan("white_plaster_02", "1k"), hp.scan("white_plaster_02", "2k")
final = []
for (n, _), low, high in zip(lows, objs_low, objs_high):
    maps = hp.bake(low, high, 2048, hs[n], cage=0.003, occluders=[occ] + flat_objs)
    mp = hp.compose(maps, sc_lo, tuple(PAINT), PPM, 1.0, 0.35, (0.75, 0.05), 0.12, 0.30)
    extras = {"role": "baked", "albedo_srgb": list(PAINT), "albedo_tol": 0.06, "ppm": PPM, "detail_tiling": [2048 / PPM / 0.5, hs[n] / PPM / 0.5],
              "scan": "polyhaven:white_plaster_02 (CC0)"}
    det = hp.detail_map(sc_hi); det[..., 0] = 0.5 + (det[..., 0] - 0.5) * DETAIL_ALBEDO   # painted plaster: the scan's pits read as dirt
    hp.write_unity_maps(TEX, f"Soffit{n}", mp, det, extras)
    nm = low.active_material.name; low.active_material.name = nm + "_bake"
    m = hp.pbr_material(nm, mp, extras); low.data.materials.clear(); low.data.materials.append(m); final.append(low)
    print(n, {k: (round(float(v[..., 0].mean()), 3), round(float(v[..., 0].std()), 3)) for k, v in maps.items()})
for o in [occ] + objs_high:
    bpy.data.objects.remove(o)
for o in flat_objs + [sofA_obj]:
    o.active_material["role"] = "system"; o.active_material["system"] = "room finish (SpecGreybox.Hall: the hall's paint or the stair well's paper, triplanar)"
hp.export(OUT, final + flat_objs + [sofA_obj], {"artist_pipeline": 1, "source": "tools/house/hifi_hall_arches.py",
                                                "lod_reason": "single LOD: architecture fixed to the walls; LOD swaps would open cracks at the wall joints"})
print("wrote", OUT, "atlas heights", hs)
