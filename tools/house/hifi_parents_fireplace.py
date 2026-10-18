"""hifi_parents_fireplace: the parents' bedroom fireplace, generated to measurement (Oct 18 2026, TRIAL; changes/2026-10-18-parents-fireplace.json).

Marina p2 176-204 s: on the hall wall between the hall door and the bath-side corner, a white Federal mantel (plain legs with a
pilaster strip, capital blocks under the shelf, a frieze with a central tablet, two beads at its foot), a black slate surround and
hearth, a black firebox with a grate and logs behind a brass-framed three-panel arched screen, fire tools on a stand at the corner
side; above it a gilt-framed still life of pale roses on a green mat (a public-domain Fantin-Latour: parents_fireplace_art.py);
on the shelf family photographs (Poly Haven standing_picture_frame_02, CC0, props lane by eye) and a gingerbread house
(generated). The film never shows this wall (film 1578-1610, 2640-2670 checked): Marina only.
Sizes: spec/dressing/parents_fireplace.json (tools/house/parents_fireplace_measure.py). Profiles and depths authored (stock).
The firebox is 6.5 cm deep: the hall is behind the 14 cm wall (DEVIATIONS 89). Faces via Part.box/face/lathe/sweep (zfight-check).

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P tools/house/hifi_parents_fireplace.py
  -> unity/HomeAlone/Assets/Models/Foyer/ParentsFireplace.glb (spec coordinates above the UPPER floor; SpecGreybox.ParentsFireplace places it)
"""
import json
import math
import sys
from pathlib import Path

import bmesh
import bpy

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/house"))
_src = (ROOT / "tools/house/hifi_den_props.py").read_text()
_ns = {"__file__": str(ROOT / "tools/house/hifi_den_props.py"), "__name__": "hifi_den_props_lib"}
exec(compile(_src[:_src.index("\nfor key, spec in P.items():")], "hifi_den_props.py", "exec"), _ns)   # resets the scene; load/fit
load, fit = _ns["load"], _ns["fit"]
from hifi_lib import Part, material   # noqa: E402

OUT = ROOT / "unity/HomeAlone/Assets/Models/Foyer/ParentsFireplace.glb"
J = json.loads((ROOT / "spec/dressing/parents_fireplace.json").read_text())
W, XC = J["wall_z"], J["centre_x"]
SH, CS, SL, FB, HR, PT = J["shelf"], J["case"], J["slate"], J["firebox"], J["hearth"], J["painting"]

_box = Part.box
Part.box = lambda self, x0, x1, y0, y1, z0, z1: _box(self, min(x0, x1), max(x0, x1), min(y0, y1), max(y0, y1), min(z0, z1), max(z0, z1))


def Z(d):
    """metres out of the wall face -> spec z (the room is z < W)"""
    return W - d


paint, slate, iron, brick = Part("Mantel", "PF_Paint"), Part("Slate", "PF_Slate"), Part("Firebox", "PF_Iron"), Part("Firebrick", "PF_Brick")
logs, brass, mesh = Part("Logs", "PF_Log"), Part("Brass", "PF_Brass"), Part("ScreenMesh", "PF_Mesh")
gilt, mat_, art = Part("Frame", "PF_Gilt"), Part("Mat", "PF_Mat"), Part("Art", "PF_Art")
ginger, icing, candy = Part("Ginger", "PF_Ginger"), Part("Icing", "PF_Icing"), Part("Candy", "PF_Candy")

cw, sw, bw, h = CS["w"], SL["w"], FB["w"], HR["h"]
CL, CR = XC - cw / 2, XC + cw / 2          # the case's outer edges
IL, IR = XC - sw / 2, XC + sw / 2          # the legs' inner edges = the slate's outer edges
OL, OR = XC - bw / 2, XC + bw / 2          # the firebox opening
FT = SL["top"]                             # the frieze's foot = the slate's top
ST = SH["top"] - SH["t"]                   # under the shelf
D = CS["depth"]

# hearth: a slate slab against the wall, centred
slate.box(XC - HR["w"] / 2, XC + HR["w"] / 2, 0.0, h, Z(0.0), Z(HR["depth"]))
# legs and frieze (one case, its face D out of the wall); legs stand on the hearth
paint.box(CL, IL, h, FT, Z(0.0), Z(D)); paint.box(IR, CR, h, FT, Z(0.0), Z(D))
paint.box(CL, CR, FT, ST - 0.025, Z(0.0), Z(D))
for xl, xr in ((CL, IL), (IR, CR)):
    xm = (xl + xr) / 2
    paint.box(xl - 0.01, xr + 0.01, h, h + 0.13, Z(D), Z(D + 0.015))                     # plinth block
    paint.box(xm - 0.045, xm + 0.045, h + 0.13, FT, Z(D), Z(D + 0.015))                   # pilaster strip
    paint.box(xm - 0.085, xm + 0.085, ST - 0.025 - 0.17, ST - 0.025, Z(D), Z(D + 0.02))  # capital block in the frieze
for y0 in (FT + 0.005, FT + 0.04):                                                         # two beads across the frieze's foot
    paint.box(CL + 0.005, CR - 0.005, y0, y0 + 0.018, Z(D), Z(D + 0.012))
paint.box(XC - 0.10, XC + 0.10, FT + 0.07, ST - 0.025, Z(D), Z(D + 0.015))                # central tablet
paint.box(CL, CR, SH["top"] - SH["t"] - 0.025, SH["top"] - SH["t"], Z(0.0), Z(SH["depth"] - 0.04))   # bed moulding under the shelf
xs0, xs1 = XC - SH["w"] / 2, XC + SH["w"] / 2
paint.box(xs0, xs1, SH["top"] - SH["t"], SH["top"], Z(0.0), Z(SH["depth"]))               # the shelf
# slate surround between the legs, its face SL["face"] out; the opening through it
sf, sb = SL["face"], 0.02
slate.box(IL, OL, h, FT, Z(sb), Z(sf)); slate.box(OR, IR, h, FT, Z(sb), Z(sf)); slate.box(OL, OR, FB["top"], FT, Z(sb), Z(sf))
# firebox: firebrick back 2.5 cm off the wall (in front of the baseboard), black sides and top up to the slate's face
fbk = FB["back"]
brick.box(OL, OR, h, FB["top"], Z(fbk), Z(fbk + 0.01))
iron.box(OL, OL + 0.012, h, FB["top"], Z(fbk + 0.01), Z(sf)); iron.box(OR - 0.012, OR, h, FB["top"], Z(fbk + 0.01), Z(sf))
iron.box(OL + 0.012, OR - 0.012, FB["top"] - 0.015, FB["top"], Z(fbk + 0.01), Z(sf))
# grate (andirons and a bar) and two logs, standing on the hearth in the opening, poking a little past the slate's face
for xg in (OL + 0.09, OR - 0.09):
    iron.box(xg - 0.01, xg + 0.01, h, h + 0.10, Z(fbk + 0.02), Z(sf + 0.07))
iron.box(OL + 0.06, OR - 0.06, h + 0.075, h + 0.09, Z(fbk + 0.03), Z(fbk + 0.045))
ring = lambda r, n: [(r * math.cos(q), r * math.sin(q)) for q in [2 * math.pi * i / n for i in range(n)]]
for k, dd in enumerate((fbk + 0.06, fbk + 0.11)):
    yy = h + 0.09 + 0.04 + k * 0.035
    logs.sweep([(OL + 0.07, yy, Z(dd)), (OR - 0.07, yy, Z(dd))], ring(0.038, 10))
# the screen (Marina 195/198: brass frame, three arched panels, black mesh; the centre parallel to the wall, the wings angled back)
dc, zw = sf + 0.20, 0.25
tube = ring(0.006, 6)
panels = [((XC - zw, dc), (XC + zw, dc), 0.62), ((XC - zw, dc), (XC - zw - 0.16, sf + 0.06), 0.56), ((XC + zw, dc), (XC + zw + 0.16, sf + 0.06), 0.56)]
for (xa, da), (xb, db), hg in panels:
    arch = [(xa + (xb - xa) * t, h + hg - 0.09 + 0.09 * math.sin(math.pi * t), Z(da + (db - da) * t)) for t in [i / 12 for i in range(13)]]
    brass.sweep([(xa, h + 0.02, Z(da))] + arch + [(xb, h + 0.02, Z(db))], tube)
    brass.sweep([(xa, h + 0.05, Z(da)), (xb, h + 0.05, Z(db))], tube)
    nrm = (-(Z(db) - Z(da)), 0, xb - xa)
    # the mesh inset 1.2 cm inside its tubes (Clash check, build 3: its edges ran along the tubes' axes)
    tin = [0.02 + 0.96 * i / 12 for i in range(13)]
    edge = [(xa + (xb - xa) * t, h + hg - 0.09 + 0.09 * math.sin(math.pi * t) - 0.013, Z(da + (db - da) * t)) for t in tin]
    pts = [(edge[0][0], h + 0.063, edge[0][2])] + edge + [(edge[-1][0], h + 0.063, edge[-1][2])]
    mesh.face(pts, nrm); mesh.face(list(reversed(pts)), tuple(-c for c in nrm))
# tools on a stand at the hearth's corner-side end (Marina 195: right of the case, i.e. toward the bath corner = lower x)
tx, tz = CL - 0.07, Z(0.22)
brass.lathe(tx, tz, h, [(0, 0.08), (0.015, 0.075), (0.025, 0.01), (0.62, 0.009), (0.64, 0.025), (0.665, 0.0)], 14)
for a in (0.4, 2.0, 3.6, 5.2):
    px, pz = tx + 0.04 * math.cos(a), tz + 0.04 * math.sin(a)
    brass.lathe(px, pz, h + 0.05, [(0, 0.005), (0.50, 0.005), (0.52, 0.012), (0.57, 0.012), (0.58, 0.0)], 8)
# the painting: gilt frame ring, green mat ring, the canvas 1.2 cm off the paper (uv: image left = high x, as seen from the room)
fw, fh, fy0 = PT["frame_w"], PT["frame_h"], PT["bottom"]; ow, oh = PT["opening"]; MW = 0.06
fx0, fx1, fy1 = XC - fw / 2, XC + fw / 2, fy0 + fh
for (a0, a1, b0, b1) in ((fx0, fx1, fy0, fy0 + MW), (fx0, fx1, fy1 - MW, fy1), (fx0, fx0 + MW, fy0 + MW, fy1 - MW), (fx1 - MW, fx1, fy0 + MW, fy1 - MW)):
    gilt.box(a0, a1, b0, b1, Z(0.0), Z(0.04))
ax0, ax1, ay0 = XC - ow / 2, XC + ow / 2, fy0 + (fh - oh) / 2; ay1 = ay0 + oh
mx0, mx1, my0, my1 = fx0 + MW, fx1 - MW, fy0 + MW, fy1 - MW
for (a0, a1, b0, b1) in ((mx0, mx1, my0, ay0), (mx0, mx1, ay1, my1), (mx0, ax0, ay0, ay1), (ax1, mx1, ay0, ay1)):
    mat_.box(a0, a1, b0, b1, Z(0.005), Z(0.025))
zc = Z(0.012)
art.face_uv([(ax1, ay0, zc), (ax0, ay0, zc), (ax0, ay1, zc), (ax1, ay1, zc)], [(0, 0), (1, 0), (1, 1), (0, 1)], (0, 0, -1))
# the gingerbread house on the shelf (Marina 195: 0.74 of the shelf from its door-side end; ~0.17 wide, 0.26 to the ridge)
gx, gz, gy = xs1 - 0.74 * SH["w"], Z(0.09), SH["top"] + 0.001
gw, gd, gh, rh = 0.15, 0.11, 0.15, 0.10
ginger.box(gx - gw / 2, gx + gw / 2, gy, gy + gh, gz - gd / 2, gz + gd / 2)
for s in (-1, 1):   # gable ends (pentagon tops) and the two roof slabs, icing white with an overhang
    zz = gz + s * gd / 2
    ginger.face([(gx - gw / 2, gy + gh, zz), (gx + gw / 2, gy + gh, zz), (gx, gy + gh + rh * 0.8, zz)], (0, 0, s))
for s in (-1, 1):
    p0 = (gx + s * (gw / 2 + 0.015), gy + gh - 0.012); p1 = (gx, gy + gh + rh * 0.8 + 0.012)
    n = (s * (p1[1] - p0[1]), abs(p1[0] - p0[0]), 0)
    z0, z1 = gz - gd / 2 - 0.015, gz + gd / 2 + 0.015
    quad = [(p0[0], p0[1], z0), (p0[0], p0[1], z1), (p1[0], p1[1], z1), (p1[0], p1[1], z0)]
    icing.face(quad, n)
    icing.face([(x, y - 0.012, zq) for x, y, zq in reversed(quad)], tuple(-c for c in n))
candy.box(gx - 0.025, gx + 0.025, gy, gy + 0.075, gz - gd / 2 - 0.006, gz - gd / 2)          # the door (red), on the front face
for xx in (gx - 0.05, gx + 0.05):
    icing.box(xx - 0.017, xx + 0.017, gy + 0.08, gy + 0.115, gz - gd / 2 - 0.006, gz - gd / 2)   # windows (white icing)

M = {"PF_Paint": material("PF_Paint", (0.86, 0.85, 0.80), 0.4), "PF_Slate": material("PF_Slate", (0.035, 0.037, 0.035), 0.55),
     "PF_Iron": material("PF_Iron", (0.012, 0.012, 0.012), 0.6), "PF_Brick": material("PF_Brick", (0.06, 0.035, 0.03), 0.9),
     "PF_Log": material("PF_Log", (0.20, 0.12, 0.07), 0.9), "PF_Brass": material("PF_Brass", (0.75, 0.56, 0.25), 0.3),
     "PF_Mesh": material("PF_Mesh", (0.02, 0.02, 0.02), 0.6), "PF_Gilt": material("PF_Gilt", (0.55, 0.40, 0.18), 0.4),
     "PF_Mat": material("PF_Mat", (0.03, 0.17, 0.14), 0.8), "PF_Art": material("PF_Art", (0.5, 0.5, 0.5), 0.7),
     "PF_Ginger": material("PF_Ginger", (0.45, 0.22, 0.09), 0.8), "PF_Icing": material("PF_Icing", (0.92, 0.91, 0.88), 0.6),
     "PF_Candy": material("PF_Candy", (0.6, 0.04, 0.04), 0.5)}
coll = bpy.context.scene.collection
root = bpy.data.objects.new("ParentsFireplace_HiFi", None); coll.objects.link(root)
for p in (paint, slate, iron, brick, logs, brass, mesh, gilt, mat_, art, ginger, icing, candy):
    ob = p.build(coll, M); ob.parent = root
    if p in (logs, brass):
        for poly in ob.data.polygons:
            poly.use_smooth = True

# photographs on the shelf (props lane, by eye from Marina 195's sequence; u on the shelf 795..1218): sizes w x h
for k, (u0, u1, hh) in enumerate(((820, 865, 0.19), (873, 915, 0.17), (933, 970, 0.15), (990, 1030, 0.15), (1145, 1185, 0.15))):
    xa, xb = xs1 - (u1 - 795) / 423 * SH["w"], xs1 - (u0 - 795) / 423 * SH["w"]
    o = load("standing_picture_frame_02", f"photo{k}")
    for q in o:   # squashed to the shelf, its glass sat 0.8 mm off the photo (Z-fight check, build 3): the glass faces removed
        if q.type == "MESH":
            gi = {i for i, sl in enumerate(q.material_slots) if sl.material and "glass" in sl.material.name.lower()}
            if gi:
                bm = bmesh.new(); bm.from_mesh(q.data)
                bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.material_index in gi], context="FACES")
                bm.to_mesh(q.data); bm.free()
    fit(o, [xa, xb], [Z(0.12), Z(0.04)], [SH["top"] + 0.002, SH["top"] + 0.002 + hh], "+x")   # the pack frame's photo faces +-X as imported (builds 5-6 showed it edge-on): "+x" turns it to the room
OUT.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(OUT), export_format="GLB", export_yup=True, export_apply=True)
print("wrote", OUT)
