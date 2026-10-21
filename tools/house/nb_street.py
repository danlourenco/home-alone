"""nb_street: Lincoln Avenue and the Tier 2 ground (Oct 20 2026; RESUME section 2 step 2). Pure Python layout (+ Blender export).

Layout (spec metres, +x toward and across Lincoln; heights relative to the ground-floor datum gy, matching what is built now):
  carriageway  our kerb face x 30.62 (SpecGreybox.FrontDrive / WinnetkaNeighborhood: the U-drive and piers meet it), centreline OSM
               (36.3 at the lot), far kerb face x 41.30 (B-side parkway trees cluster at x 41-46 in the re-registered lidar, B sidewalk
               OSM x 45.4): 10.7 m kerb to kerb; straight for z -45..65 (Tier 2, so it meets the existing kerb exactly), then it follows
               OSM's centreline (the bend at z -67 and on to Pine St at z 112); a 6 cm crown
  kerb+gutter  concrete: 0.45 m gutter pan at road level, 0.15 m kerb, 14 cm reveal; cut and ramped at every drive mouth
  our side     sidewalk x 28.87-30.37 (the built one), a 10 cm snow strip, the kerb x 30.47-30.62
  B side       kerb x 41.30-41.45, parkway (snow) to 44.65, sidewalk 44.65-46.15 (OSM 45.4), lawns from 46.15
  drives/walks OSM where mapped (the Murphys' walk z 11.5-11.8 and drive z 3.1-4.2; lot_B+1's drive z 36.8-38.1 and walk z 45), the
               others from each kit's door / garage (G); 3.0 m drives in wet asphalt, 1.5 m walks in concrete
  snow banks   plowed banks on the gutter both sides (0.25 m, 0.6 m wide, noise), open at drives and walks
  lamp posts   the film's (1471/3297/9511): dark green cast iron, bell base with rings, fluted tapered shaft, a ribbed clear acorn globe
               with a finial, 4.25 m; walk note 2026-10-19T12:33 "style of light is wrong". Ours: the two existing posts moved from
               x 25.2 (old GLB street) to the sidewalk's lawn edge x 28.55 (film 3297: the post stands at the sidewalk); more at ~45 m (G)
  trees        lidar crowns (re-registered ISGS 2022) in the street strip and the Tier 2 lots, not on our lot (Tier 1 has its own), 5 m
               apart; crowns over the carriageway move to the nearest parkway/lawn; species mix elm/oak/maple/ash x 2 variants
               (BareTrees.glb, hifi_bare_trees.py: NOT the rejected Sereib oaks), hashed yaw, scale from the lidar height x 0.92
               (1990 trees ~32 years younger; film 1886/4382 shows mature ones: a guess, DEVIATIONS)
  python3 tools/house/nb_street.py                     # layout -> spec/neighborhood.json "street" + street_layout.json for Unity
  Blender -b --factory-startup -P tools/house/nb_street.py -- --glb   # + Street.glb and LampPost.glb in Assets/Models/Neighborhood
"""
import json
import math
import random
import sys
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/house"))
from nb_house import Geo, UP, add, mul, sub, norm, to_blender  # noqa: E402

MAN_P = ROOT / "spec/neighborhood.json"
OUT = ROOT / "unity/HomeAlone/Assets/Models/Neighborhood"
FR = json.loads((ROOT / "art/home_alone/references/neighborhood/data/spec_frame.json").read_text())

ROAD_Y, WALK_Y = -1.304, -1.184          # rel gy: the WinterNeighborhood street top / public sidewalk top (what the U-drive meets)
KERB_Y = WALK_Y + 0.02
LAWN_A, LAWN_B = -1.334, -1.20           # our registered front yard; the B lots ~2 cm under their sidewalk (G)
KA, KB = 30.62, 41.30                     # kerb faces at the lot (centre 36.3)
Z0, Z1 = -118.0, 150.0   # step 3: the street stops at Lincoln's bend west (OSM z -110.7 -> (-14.1, -118.6)); past it the stand-ins stand where a straight street ran
CL = [(31.6, -110.7), (36.2, -92.4), (35.4, -66.7), (36.3, 0.5), (36.6, 26.0), (36.8, 38.1), (37.7, 112.2), (37.7, 160.0)]


def centre(z):
    """Lincoln's centreline x at z: exactly 36.3 over Tier 2 (z -45..65), easing into OSM's line over 20 m beyond."""
    def osm(z):
        if z <= CL[0][1]: return CL[0][0]
        for (xa, za), (xb, zb) in zip(CL, CL[1:]):
            if za <= z <= zb: return xa + (xb - xa) * (z - za) / (zb - za)
        return CL[-1][0]
    w = 0.0 if -45 <= z <= 65 else min(1.0, (min(abs(z + 45), abs(z - 65))) / 20.0)
    return 36.3 + w * (osm(z) - 36.3)


def zs(step=2.0):
    n = int((Z1 - Z0) / step); return [Z0 + i * step for i in range(n + 1)]


def strip(g, mat, off0, off1, y0, y1=None, step=2.0, zr=(Z0, Z1), toward=UP, skip=()):
    """A flat (or cross-sloped) ribbon at offsets off0..off1 from the centreline (x), between zr, skipping z ranges `skip`."""
    y1 = y0 if y1 is None else y1
    zz = [z for z in zs(step) if zr[0] <= z <= zr[1]]
    for za, zb in zip(zz, zz[1:]):
        zm = (za + zb) / 2
        if any(a < zm < b for a, b in skip): continue
        ca, cb = centre(za), centre(zb)
        g.quad(mat, (ca + off0, y0, za), (ca + off1, y1, za), (cb + off1, y1, zb), (cb + off0, y0, zb), toward)


def wall(g, mat, off, ya, yb, n, step=2.0, zr=(Z0, Z1), skip=()):
    """A vertical kerb face along offset `off`, facing n = -1 (toward -x) or +1."""
    zz = [z for z in zs(step) if zr[0] <= z <= zr[1]]
    for za, zb in zip(zz, zz[1:]):
        if any(a < (za + zb) / 2 < b for a, b in skip): continue
        ca, cb = centre(za), centre(zb)
        g.quad(mat, (ca + off, ya, za), (cb + off, ya, zb), (cb + off, yb, zb), (ca + off, yb, za), (n, 0, 0))


def kits():
    m = json.loads(MAN_P.read_text()); return m, {e["id"]: e for e in m["parcels"]}


def layout():
    man, P = kits()
    rnd = random.Random(20)
    # drives (asphalt) and walks (concrete): [side, z centre, x street end, x far end, width, source]
    drives = [("B", 3.65, KB, 83.9, 3.0, "OSM service z 3.1-4.2 (2022) to the outbuilding"),
              ("B", 37.45, KB, 83.4, 3.0, "OSM service z 36.8-38.1 to the outbuilding"),
              ("B", -26.2, KB, 75.8, 3.0, "G: to lot_B-1's outbuilding (C)"),
              ("A", 31.95, KA, -30.0, 2.4, "G: Marley's (lot_A+1) drive to the garage behind (C outbuilding x -38..-30), between our parcel line (30.72) and his house (33.1)")]
    walks = [("B", 12.2, 46.15, 60.6 - 6 * 0.29, 1.5, "OSM footway z 11.5-11.8, moved to the porch steps (step 3: z 12.2, the film-registered house)"),
             ("B", -16.1, 46.15, 60.6 - 3 * 0.29, 1.4, "G: to lot_B-1's porch steps"),
             ("B", 46.55, 46.15, 60.3 - 4 * 0.29, 1.4, "OSM footway z 44.9-45.4 (moved to the kit's steps)"),
             ("A", -27.6, 28.87, 0.5, 1.3, "G: lot_A-1's door (kit, main block beside the front wing)"),
             ("A", 41.65, 28.87, 14.04, 1.5, "G: to the foot of Marley's stone steps (kit, the recessed entry at z 41.65)")]
    lamps = [{"x": 28.55, "z": 24.2, "src": "existing post (SpecGreybox.Shell z 24.2), moved from x 25.2 to the sidewalk's lawn edge (film 3297)"},
             {"x": 28.55, "z": -6.0, "src": "existing post (z -6.0, film 1471/9511 right of our lot), moved from x 25.2"}]
    for z in (-51.0, 69.0, 114.0, -96.0): lamps.append({"x": 28.55, "z": z, "src": "G: ~45 m spacing on our side"})
    for z in (-40.0, 60.0, 105.0, -85.0): lamps.append({"x": 44.25, "z": z, "src": "G: B side, none in 11581's frontage (z -15..35)"})
    # trees: lidar crowns (re-registered) in the street strip and Tier 2 lots
    lot = P["lot_A0"]["parcel_poly_spec"]
    def pip(p, pg):
        c = False
        for (a, b), (e, g) in zip(pg, pg[1:] + pg[:1]):
            if (b > p[1]) != (g > p[1]) and p[0] < (e - a) * (p[1] - b) / (g - b) + a: c = not c
        return c
    t2 = [P[k]["parcel_poly_spec"] for k in ("lot_A-1", "lot_A+1", "lot_B-1", "lot_B0", "lot_B+1")]
    fps = [b["footprint_spec"] for e in man["parcels"] for b in e["buildings"]]
    cand = []
    for t in FR["trees"]:
        x, z = t["x"], t["z"]
        street = 24 < x < 47.5 and Z0 < z < Z1
        if not (street or any(pip((x, z), pg) for pg in t2)): continue
        if pip((x, z), lot) or x < -60: continue
        if 41.0 < x < 62.0 and 2.0 < z < 25.0: continue   # film 11581/11626 show the Murphys' parkway and front yard with no trunk: post-1990 trees
        if any(pip((x, z), f) for f in fps): continue
        cand.append(dict(t))
    cand.sort(key=lambda t: -t["h_m"]); keep = []
    for t in cand:
        if all(math.hypot(t["x"] - k["x"], t["z"] - k["z"]) > 5.0 for k in keep): keep.append(t)
    species = ["elmA", "elmB", "oakA", "oakB", "mapleA", "mapleB", "ashA", "elmA", "oakB", "mapleA"]
    trees = []
    for t in keep:
        x, z = t["x"], t["z"]; c = centre(z); moved = None
        if c - 5.68 - 0.3 < x < c + 5.0 + 0.4:            # over the carriageway: to the nearer side's trunk line
            moved = [x, z]; x = 27.9 + (c - 36.3) if x < c else c + 6.85
        elif 28.87 <= x <= 30.62 + (c - 36.3): moved = [x, z]; x = 27.9
        elif 44.65 <= x <= 46.15: moved = [x, z]; x = 43.6
        if any(abs(z - d[1]) < d[4] / 2 + 1.0 and min(d[2], d[3]) - 0.5 < x < max(d[2], d[3]) + 0.5 for d in drives + walks):
            moved = moved or [x, z]; z += 2.6
        if moved and (pip((x, z), lot) or -4.5 < z < 31.2 and x < 31.0): continue   # never onto our lot or its frontage (Tier 1 owns it)
        if moved and any(math.hypot(x - q["x"], z - q["z"]) < 6.0 for q in trees): continue
        h = zlib.crc32(f"{t['x']:.1f},{t['z']:.1f}".encode())
        trees.append({"x": round(x, 2), "z": round(z, 2), "h_m": round(t["h_m"] * 0.92, 1), "lidar_h_m": t["h_m"], "variant": random.Random(h).choice(species),
                      "yaw": h % 360, **({"moved_from": moved} if moved else {})})
    return {"levels_rel_gy": {"road": ROAD_Y, "walk": WALK_Y, "kerb": KERB_Y, "lawn_A": LAWN_A, "lawn_B": LAWN_B,
                              "lot_grade": {"lot_B-1": LAWN_B + 0.02, "lot_B0": LAWN_B + 0.02, "lot_B+1": LAWN_B + 0.02, "lot_A-1": LAWN_A, "lot_A+1": LAWN_A, "tier3_A": LAWN_A, "tier3_B": LAWN_B + 0.02}},
            "kerb_faces_x": [KA, KB], "centreline": "nb_street.centre(z): 36.3 for z -45..65, OSM beyond", "extent_z": [Z0, Z1],
            "drives": [dict(zip(("side", "z", "x0", "x1", "w", "src"), d)) for d in drives],
            "walks": [dict(zip(("side", "z", "x0", "x1", "w", "src"), w)) for w in walks], "lamps": lamps, "trees": trees}


def lamp_post(lod):
    """The film's acorn lamp (1471/3297/9511), base at the origin. LOD0 ~ fluted lathe; LOD1 a few-sided version."""
    g = Geo(); glow = Geo(); M, Gl = "NB_paint_lampgreen", "NB_LampGlobe"
    n = 24 if lod == 0 else 8
    prof = [(0.0, 0.20), (0.05, 0.20), (0.07, 0.185), (0.16, 0.175), (0.18, 0.155), (0.40, 0.11), (0.44, 0.115), (0.48, 0.095), (0.55, 0.085),
            (0.60, 0.075), (0.64, 0.068), (3.30, 0.050), (3.34, 0.062), (3.38, 0.062), (3.42, 0.055), (3.52, 0.075), (3.56, 0.085)]
    def lathe(geo, mat, pr, flute=0.0, nf=0, ys=(0.0, 99.0)):
        rings = []
        for y, r in pr:
            ring = []
            for k in range(n):
                a = 2 * math.pi * k / n; rr = r * (1 - (flute if (nf and ys[0] < y < ys[1] and k % 2) else 0.0))
                ring.append((rr * math.cos(a), y, rr * math.sin(a)))
            rings.append(ring)
        for a, b in zip(rings, rings[1:]):
            for k in range(n):
                k2 = (k + 1) % n; mid = mul(add(a[k], b[k2]), 0.5)
                geo.quad(mat, a[k], a[k2], b[k2], b[k], (mid[0], 0, mid[2]))
        geo.face(mat, rings[-1], UP); geo.face(mat, rings[0], (0, -1, 0))
    lathe(g, M, prof, flute=0.12 if lod == 0 else 0.0, nf=n, ys=(0.62, 3.32))
    # ribbed acorn globe 3.56 .. 4.12, finial to 4.25
    gp = [(3.56, 0.085), (3.62, 0.15), (3.72, 0.185), (3.84, 0.19), (3.96, 0.17), (4.05, 0.12), (4.10, 0.07), (4.12, 0.035)]
    rings = []
    for y, r in gp:
        rings.append([((r * (1 + (0.05 * math.cos(16 * 2 * math.pi * k / n)) if lod == 0 else r)) * math.cos(2 * math.pi * k / n), y,
                       (r * (1 + (0.05 * math.cos(16 * 2 * math.pi * k / n)) if lod == 0 else r)) * math.sin(2 * math.pi * k / n)) for k in range(n)])
    for a, b in zip(rings, rings[1:]):
        for k in range(n):
            k2 = (k + 1) % n; glow.quad(Gl, a[k], a[k2], b[k2], b[k], (a[k][0], 0, a[k][2]))
    lathe(g, M, [(4.11, 0.04), (4.15, 0.045), (4.18, 0.02), (4.25, 0.012), (4.26, 0.0)])
    return g, glow


def build_glb(L):
    import bpy
    bpy.ops.wm.read_factory_settings(use_empty=True); coll = bpy.context.scene.collection
    road, conc, snow, lawn = Geo(), Geo(), Geo(), Geo()
    R, C, S = "NB_asphalt_wet", "NB_concrete_walk", "NB_snow_ground"
    drv = [(d["z"] - d["w"] / 2, d["z"] + d["w"] / 2) for d in L["drives"]]
    wk = [(w["z"] - w["w"] / 2, w["z"] + w["w"] / 2) for w in L["walks"]]
    oA, oB = KA - 36.3, KB - 36.3
    # carriageway with a crown (4 strips), gutter pans
    for a, b, ya, yb in ((oA + 0.45, oA / 2, ROAD_Y, ROAD_Y + 0.04), (oA / 2, 0, ROAD_Y + 0.04, ROAD_Y + 0.06), (0, oB / 2, ROAD_Y + 0.06, ROAD_Y + 0.04), (oB / 2, oB - 0.45, ROAD_Y + 0.04, ROAD_Y)):
        strip(road, R, a, b, ya, yb)
    for a, b in ((oA, oA + 0.45), (oB - 0.45, oB)): strip(road, C, a, b, ROAD_Y - 0.005)
    # kerbs: our side face at oA (facing +x), top to oA - 0.15; B side face at oB (facing -x), top to oB + 0.15; open at drive mouths
    sideA = [s for s, d in zip(drv, L["drives"]) if d["side"] == "A"] + [(-2.1 - 1.8, -2.1 + 1.8), (21.4 - 1.8, 21.4 + 1.8)]   # + our U-drive's mouths
    sideB = [s for s, d in zip(drv, L["drives"]) if d["side"] == "B"]
    wall(conc, C, oA, ROAD_Y - 0.005, KERB_Y, 1, skip=sideA); strip(conc, C, oA - 0.15, oA, KERB_Y, skip=sideA)
    wall(conc, C, oB, ROAD_Y - 0.005, KERB_Y, -1, skip=sideB); strip(conc, C, oB, oB + 0.15, KERB_Y, skip=sideB)
    for (a, b) in sideA:   # kerb-cut aprons: walk level down to the gutter over the kerb's width + 0.6 m
        za, zb = max(a, Z0), min(b, Z1); c = centre((za + zb) / 2)
        conc.quad(C, (c + oA - 0.75, WALK_Y - 0.01, za), (c + oA, ROAD_Y, za), (c + oA, ROAD_Y, zb), (c + oA - 0.75, WALK_Y - 0.01, zb), UP)
    for (a, b) in sideB:
        c = centre((a + b) / 2)
        conc.quad(C, (c + oB, ROAD_Y, a), (c + oB + 0.75, WALK_Y - 0.01, a), (c + oB + 0.75, WALK_Y - 0.01, b), (c + oB, ROAD_Y, b), UP)
    # our side: sidewalk + strip; B side: parkway, sidewalk; lawns
    strip(conc, C, 28.87 - 36.3, 30.37 - 36.3, WALK_Y)
    strip(snow, S, 30.37 - 36.3, oA - 0.15, WALK_Y - 0.01, skip=sideA)
    strip(snow, S, oB + 0.15, 44.65 - 36.3, WALK_Y - 0.01, skip=sideB + [w for w, d in zip(wk, L["walks"]) if d["side"] == "B"] + [(z - 0.75, z + 0.75) for z in ()])
    strip(conc, C, 44.65 - 36.3, 46.15 - 36.3, WALK_Y)
    strip(snow, S, 46.15 - 36.3, 46.25 - 36.3, WALK_Y - 0.01, LAWN_B)      # the sidewalk's lawn edge eases down
    for a, b in (sideB):   # drive mouths through the parkway at walk level
        c = centre((a + b) / 2)
        road.quad(R, (c + oB + 0.75, WALK_Y - 0.008, a), (44.65, WALK_Y - 0.008, a), (44.65, WALK_Y - 0.008, b), (c + oB + 0.75, WALK_Y - 0.008, b), UP)
    for a, b in sideA:
        if b < -2.1 - 1.0 or a > 21.4 + 1.0 or True:
            c = centre((a + b) / 2)
            if a > 30 or b < -5: road.quad(R, (30.37, WALK_Y - 0.008, a), (c + oA - 0.75, WALK_Y - 0.008, a), (c + oA - 0.75, WALK_Y - 0.008, b), (30.37, WALK_Y - 0.008, b), UP)
    # B lawns (x 46.25 .. 100) and the A neighbours' front yards (x -60 .. 28.87 outside our lot's z), Tier 2+3 extent
    def rect(geo, mat, x0, x1, za, zb, y, step=4.0):
        z = za
        while z < zb - 1e-6:
            z2 = min(zb, z + step); geo.quad(mat, (x0, y, z), (x1, y, z), (x1, y, z2), (x0, y, z2), UP); z = z2
    for za, zb in ((-150.0, -45), (-45, 65), (65, Z1)):
        rect(lawn, "NB_snow_patchy", 46.25 + (0 if -45 <= za else 0), 100.0, za, zb, LAWN_B)
    rect(lawn, "NB_snow_patchy", -60.0, 28.87, -150.0, -4.06, LAWN_A); rect(lawn, "NB_snow_patchy", -60.0, 28.87, 30.72, Z1, LAWN_A)
    rect(lawn, "NB_snow_patchy", 28.87, 46.25, -150.0, Z0, LAWN_A)   # past the bend: lawn where the straight street ran
    # drives / walks surfaces on the lots
    for d in L["drives"]:
        y = (LAWN_B if d["side"] == "B" else LAWN_A) + 0.02; x0 = 46.15 if d["side"] == "B" else d["x1"]; x1 = d["x1"] if d["side"] == "B" else 28.87
        road.quad(R, (x0, y, d["z"] - d["w"] / 2), (x1, y, d["z"] - d["w"] / 2), (x1, y, d["z"] + d["w"] / 2), (x0, y, d["z"] + d["w"] / 2), UP)
    for w in L["walks"]:
        y = (LAWN_B if w["side"] == "B" else LAWN_A) + 0.03; x0, x1 = sorted((w["x0"], w["x1"]))
        conc.box(C, x0, x1, y - 0.12, y, w["z"] - w["w"] / 2, w["z"] + w["w"] / 2, 0.01)
    # snow banks on the gutters, open at drives, walks and our U-drive mouths; noise along z
    banks = Geo(); rng = random.Random(7)
    def bank(off, sgn, skip):
        zz = [z for z in zs(1.0)]
        prev = None
        for z in zz:
            if any(a - 0.8 < z < b + 0.8 for a, b in skip): prev = None; continue
            c = centre(z); h = 0.18 + 0.10 * (0.5 + 0.5 * math.sin(z * 0.37) * math.sin(z * 0.11 + 1.0)) + 0.03 * rng.random()
            ring = [(c + off, KERB_Y - 0.02, z), (c + off + sgn * 0.20, ROAD_Y + h * 0.95, z), (c + off + sgn * 0.42, ROAD_Y + h * 0.55, z), (c + off + sgn * 0.62, ROAD_Y - 0.01, z)]
            if prev:
                for k in range(3): banks.quad(S, prev[k], prev[k + 1], ring[k + 1], ring[k], (sgn, 1, 0))
            prev = ring
    bank(oA, 1, sideA + [(9.716 - 0.9, 9.716 + 0.9)]); bank(oB, -1, sideB)
    objs = [to_blender(road, "Street_Road", coll), to_blender(conc, "Street_Concrete", coll), to_blender(snow, "Street_Parkway", coll),
            to_blender(lawn, "Street_Lawns", coll, smooth=False), to_blender(banks, "Street_SnowBanks", coll)]
    root = bpy.data.objects.new("Street_Root", None); coll.objects.link(root)
    for o in objs: o.parent = root
    bpy.context.view_layer.update()
    for o in bpy.context.scene.collection.objects: o.select_set(True)
    OUT.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=str(OUT / "Street.glb"), export_format="GLB", export_yup=True, use_selection=True, export_materials="EXPORT")
    stats = {o.name: sum(len(p.vertices) - 2 for p in o.data.polygons) for o in objs}
    # the lamp post (one model, instanced by Unity at L["lamps"])
    bpy.ops.wm.read_factory_settings(use_empty=True); coll = bpy.context.scene.collection; lo = []
    for lod in (0, 1):
        g, gl = lamp_post(lod); lo += [to_blender(g, f"LampPost_LOD{lod}", coll), to_blender(gl, f"LampPost_Globe_LOD{lod}", coll)]
        stats[f"LampPost_LOD{lod}"] = g.tris() + gl.tris()
    root = bpy.data.objects.new("LampPost_Root", None); coll.objects.link(root)
    for o in lo: o.parent = root
    bpy.context.view_layer.update()
    for o in bpy.context.scene.collection.objects: o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(OUT / "LampPost.glb"), export_format="GLB", export_yup=True, use_selection=True, export_materials="EXPORT")
    return stats


def main():
    L = layout()
    man = json.loads(MAN_P.read_text()); man["street"] = {k: v for k, v in L.items() if k != "trees"}; man["street"]["n_trees"] = len(L["trees"])
    MAN_P.write_text(json.dumps(man, indent=1))
    OUT.mkdir(parents=True, exist_ok=True); (OUT / "street_layout.json").write_text(json.dumps(L, indent=1))
    print("street:", len(L["drives"]), "drives,", len(L["walks"]), "walks,", len(L["lamps"]), "lamps,", len(L["trees"]), "trees",
          sum(1 for t in L["trees"] if "moved_from" in t), "moved")
    if "--glb" in sys.argv:
        st = build_glb(L); print("street tris", st)
        sp = ROOT / "art/home_alone/references/neighborhood/build_stats.json"; s = json.loads(sp.read_text()) if sp.exists() else {}
        s["street"] = st; sp.write_text(json.dumps(s, indent=1))


if __name__ == "__main__":
    main()
