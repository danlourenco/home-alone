"""hifi_kevin: Kevin and Jeff's room (TRIAL 1, Oct 18; changes/2026-10-18-kevin-room.json): the bunk beds, curtains, mirror, cork
board, dartboard, globe, the film's red desk lamp and the footlocker, in spec coordinates above the UPPER floor.

Evidence (report: spec/captures/views/kevin/README in the change record):
- FILM 294-306 (the packing night, Jeff and Kevin; the room's only film shots): honey-pine bunk beds, square posts, a wide upper side
  board covered in stickers (Bulls, dinosaurs, cars), rungs at the foot end; the lower bunk's red/white sawtooth + green quilt; a low
  pine dresser with a pine-framed mirror over it, a red swing-arm lamp and toys on top; green gingham curtains at the front window.
- Poster (user's cutaway, room 22): one bunk, head toward the hall wall, long axis front-to-back, closet doors on the side wall.
- Marina Part 2 354-386 s: the bunk's head against the hall wall beside the hall door (380 s), a nightstand with a globe, the dresser on
  the opposite side wall, a reading chair by the front window, a low bookcase + cork board between the windows, the desk with a green
  banker's lamp at the other window, a footlocker under a dartboard on the closet wall.
Bunk at Marina 380 s on the 80 in door (tools/house/wall_measure.py; spec/captures/picks/kevin/): head-post centres 0.874 m apart (a
33 in bunk mattress), the closet-side post 1.684 m from the closet wall's corner. Length 2.02 / post 1.62 / deck heights ASSUMED (a
33 x 75 in bunk mattress; Marina 375 ratio for the post height): DEVIATIONS 95.

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P tools/house/hifi_kevin.py
  -> unity/HomeAlone/Assets/Models/Foyer/KevinRoom.glb (SpecGreybox.Kevin places it at the upper floor, remaps KV_* materials)
"""
import json
import math
import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hifi_lib import Part, material   # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "unity/HomeAlone/Assets/Models/Foyer/KevinRoom.glb"
_src = (ROOT / "tools/house/hifi_sheers.py").read_text()
_ns = {"__file__": str(ROOT / "tools/house/hifi_sheers.py"), "__name__": "hifi_sheers_lib"}
exec(compile(_src[:_src.index("\nbpy.ops.wm.read_factory_settings(use_empty=True)")], "hifi_sheers.py", "exec"), _ns)
sheer_panel, SMOOTH = _ns["sheer_panel"], _ns["SMOOTH"]

K = json.loads((ROOT / "spec/dressing/kevin.json").read_text())
GEO = json.loads((ROOT / "spec/geometry.json").read_text())["upstairs"]
POLY = next(r for r in GEO["rooms"] if r["name"] == "kevin_jeff_room")["poly"]
X0, X1 = min(p[0] for p in POLY), max(p[0] for p in POLY)        # back (hall) wall face, front wall face
Z0, Z1 = min(p[1] for p in POLY), max(p[1] for p in POLY)        # dresser-side wall face, closet wall face
WINS = [o for o in json.loads((ROOT / "spec/openings.json").read_text())["openings"] if o["kind"] == "window" and o["between"] == ["kevin_jeff_room"]]
assert len(WINS) == 2, WINS

parts = {}


def P(name, mat=None):
    if name not in parts:
        parts[name] = Part(name, mat or name)
    return parts[name]


# ---------------------------------------------------------------- the bunk beds
B = K["bunk"]
bx0, bx1 = B["x"]; bz0, bz1 = B["z"]; s = B["post"]; H = B["post_h"]
pine = P("KV_Pine")
for x in (bx0, bx1 - s):
    for z in (bz0, bz1 - s):
        pine.box(x, x + s, 0, H, z, z + s)
INSET = 0.012                                                    # boards stand back from the posts' faces (no coplanar faces)
for y0, y1 in (B["low_rail"], B["up_rail"]):                     # side rails (both long sides) and end rails at each deck
    for z in (bz0 + INSET, bz1 - INSET - 0.03):
        pine.box(bx0 + s, bx1 - s, y0, y1, z, z + 0.03)
    for x in (bx0 + INSET, bx1 - INSET - 0.03):
        pine.box(x, x + 0.03, y0, y1, bz0 + s, bz1 - s)
for z in (bz0 + INSET, bz1 - INSET - 0.03):                      # film 303: the wide upper guard board (stickers) on both long sides
    pine.box(bx0 + s, bx1 - s, B["guard"][0], B["guard"][1], z, z + 0.03)
# head end (hall wall): two solid panels; film/Marina: a crest rail at the top
hx = bx0 + INSET
pine.box(hx, hx + 0.025, B["low_rail"][1] + 0.01, B["low_rail"][1] + 0.40, bz0 + s, bz1 - s)
pine.box(hx, hx + 0.025, B["up_rail"][1] + 0.12, H - 0.03, bz0 + s, bz1 - s)
# foot end: rungs (film 296/301: a ladder between the foot posts), round dowels
fx = bx1 - s / 2
circ = [(0.017 * math.cos(t), 0.017 * math.sin(t)) for t in [2 * math.pi * i / 10 for i in range(10)]]
for y in B["rungs"]:
    pine.sweep([(fx, y, bz0 + s), (fx, y, bz1 - s)], circ)
pine.box(bx1 - s + 0.005, bx1 - 0.005, H - 0.10, H - 0.02, bz0 + s, bz1 - s)          # foot top rail
# slats under each mattress (a board deck, hidden but closes the view from below)
for y in (B["low_rail"][0] + 0.06, B["up_rail"][0] + 0.06):
    pine.box(bx0 + s, bx1 - s, y, y + 0.02, bz0 + 0.045, bz1 - 0.045)
# mattresses, quilts, pillows
mat_w = B["mattress"]
for deck, rail, quilt in (("low", B["low_rail"], "KV_QuiltLow"), ("up", B["up_rail"], "KV_QuiltUp")):
    y0 = rail[0] + 0.09; y1 = y0 + 0.15
    zc = (bz0 + bz1) / 2
    P("KV_Mattress").box(bx0 + s + 0.01, bx1 - s - 0.01, y0, y1, zc - mat_w / 2, zc + mat_w / 2)
    q = P(quilt)
    qx0, qx1 = bx0 + s + 0.32, bx1 - s + 0.005                   # turned back under the pillow
    q.box(qx0, qx1, y1 - 0.10, y1 + 0.025, zc - mat_w / 2 - 0.012, zc + mat_w / 2 + 0.012)
    P("KV_Pillow").box(bx0 + s + 0.04, bx0 + s + 0.40, y1 - 0.01, y1 + 0.12, zc - 0.28, zc + 0.28)

# ---------------------------------------------------------------- curtains (film 296 green gingham; Marina 355-365 checked panels)
C = K["curtains"]
for k, o in enumerate(WINS):
    face = o["c"] - 0.07                                         # front wall's room face (wall 0.14 thick)
    Pw = lambda u, y, d: (face - d, y, u)
    a0, b1 = o["lo"] - 0.07 - C["overhang"], o["hi"] + 0.07 + C["overhang"]
    top = C["rod_y"] - 0.0125 - 0.008
    for sgn, (a, b) in ((1, (a0, a0 + C["panel_w"])), (-1, (b1 - C["panel_w"], b1))):
        sheer_panel(P("KV_Gingham"), P("KV_Gingham"), Pw, a, b, C["hem_y"], top, C["depth"], 1.7 * k + (0.4 if sgn > 0 else 2.2), P0=0.10, A0=0.016)
    rod = P("KV_Brass")
    rc = [(0.0125 * math.cos(t), 0.0125 * math.sin(t)) for t in [2 * math.pi * i / 12 for i in range(12)]]
    rod.sweep([Pw(a0 - 0.04, C["rod_y"], C["depth"]), Pw(b1 + 0.04, C["rod_y"], C["depth"])], rc)
    for u in (a0 + 0.01, b1 - 0.01):
        p0, p1 = Pw(u - 0.008, C["rod_y"] - 0.03, 0.003), Pw(u + 0.008, C["rod_y"] - 0.0125, C["depth"])
        rod.box(min(p0[0], p1[0]), max(p0[0], p1[0]), min(p0[1], p1[1]), max(p0[1], p1[1]), min(p0[2], p1[2]), max(p0[2], p1[2]))

# ---------------------------------------------------------------- wall pieces
M = K["mirror"]                                                  # film 296: pine frame over the dresser (dresser-side wall, z = Z0)
mx0, mx1 = M["x"]; my0, my1 = M["y"]; fw = 0.06
for (x0, x1, y0, y1) in ((mx0, mx1, my0, my0 + fw), (mx0, mx1, my1 - fw, my1), (mx0, mx0 + fw, my0 + fw, my1 - fw), (mx1 - fw, mx1, my0 + fw, my1 - fw)):
    pine.box(x0, x1, y0, y1, Z0 + 0.010, Z0 + 0.040)
P("KV_Mirror").box(mx0 + fw, mx1 - fw, my0 + fw, my1 - fw, Z0 + 0.012, Z0 + 0.026)

CB = K["corkboard"]                                              # Marina 355: cork board over the bookcase between the windows
cz0, cz1 = CB["z"]; cy0, cy1 = CB["y"]; cf = X1 - 0.010
pine.box(cf - 0.025, cf, cy0, cy1, cz0, cz1)
P("KV_Cork").box(cf - 0.032, cf - 0.025, cy0 + 0.03, cy1 - 0.03, cz0 + 0.03, cz1 - 0.03)
for i, (dz, dy, w, h) in enumerate(((0.08, 0.10, 0.20, 0.14), (0.33, 0.06, 0.14, 0.20), (0.50, 0.22, 0.16, 0.11), (0.16, 0.30, 0.12, 0.10))):
    P("KV_Paper").box(cf - 0.036, cf - 0.033, cy0 + 0.03 + dy, cy0 + 0.03 + dy + h, cz0 + 0.03 + dz, cz0 + 0.03 + dz + w)

D = K["dartboard"]                                               # Marina 382-386: dartboard over the footlocker, closet wall (z = Z1); bull 1.73 m
dxc, dyc = D["x"], D["y"]; wz = Z1 - 0.010
rings = [(0.0, 0.0064, "KV_DartRed"), (0.0064, 0.016, "KV_DartGreen"), (0.016, 0.099, None), (0.099, 0.107, "ring"),
         (0.107, 0.162, None), (0.162, 0.170, "ring"), (0.170, 0.225, "KV_DartBlack")]
nseg = 20
for r0, r1, kind in rings:
    for k in range(nseg):
        t0, t1 = 2 * math.pi * (k - 0.5) / nseg, 2 * math.pi * (k + 0.5) / nseg
        mat = kind if kind and kind.startswith("KV_") else (("KV_DartRed" if k % 2 else "KV_DartGreen") if kind == "ring" else ("KV_DartBlack" if k % 2 else "KV_DartCream"))
        sub = 3
        for j in range(sub):
            a, b = t0 + (t1 - t0) * j / sub, t0 + (t1 - t0) * (j + 1) / sub
            pts = [(dxc + r0 * math.cos(a), dyc + r0 * math.sin(a), wz - 0.04), (dxc + r1 * math.cos(a), dyc + r1 * math.sin(a), wz - 0.04),
                   (dxc + r1 * math.cos(b), dyc + r1 * math.sin(b), wz - 0.04), (dxc + r0 * math.cos(b), dyc + r0 * math.sin(b), wz - 0.04)]
            P(mat).face(pts if r0 > 0 else pts[1:], (0, 0, -1))
# the board's body: a 4 cm drum behind the face (sides only + back), black
body = P("KV_DartBlack"); n = 40
for k in range(n):
    a, b = 2 * math.pi * k / n, 2 * math.pi * (k + 1) / n
    p = lambda t, z: (dxc + 0.226 * math.cos(t), dyc + 0.226 * math.sin(t), z)
    body.face([p(a, wz), p(b, wz), p(b, wz - 0.041), p(a, wz - 0.041)], (math.cos((a + b) / 2), math.sin((a + b) / 2), 0))

# ---------------------------------------------------------------- tabletop props
G = K["globe"]                                                   # Marina 375: blue globe on the nightstand
gx, gy, gz = G["at"]
P("KV_Brass").lathe(gx, gz, gy, [(0, 0.06), (0.012, 0.06), (0.012, 0.012), (0.10, 0.008)], n=16)
prof = [(0.10 + 0.13 + 0.13 * math.sin(-math.pi / 2 + math.pi * i / 12), 0.13 * math.cos(-math.pi / 2 + math.pi * i / 12) + 1e-4) for i in range(13)]
P("KV_Globe").lathe(gx, gz, gy, prof, n=24)

L = K["lamp_red"]                                                # film 296/301: red swing-arm lamp on the dresser
lx, ly, lz = L["at"]
red = P("KV_LampRed")
red.lathe(lx, lz, ly, [(0, 0.075), (0.025, 0.075), (0.03, 0.02)], n=20)
elbow = (lx + 0.05, ly + 0.30, lz + 0.03)
tube = [(0.009 * math.cos(t), 0.009 * math.sin(t)) for t in [2 * math.pi * i / 8 for i in range(8)]]
red.sweep([(lx, ly + 0.03, lz), elbow], tube)
head = (lx + 0.22, ly + 0.36, lz + 0.10)
red.sweep([elbow, head], tube)
hx_, hy_, hz_ = head
red.lathe(hx_, hz_, hy_ - 0.14, [(0.0, 0.085), (0.06, 0.07), (0.12, 0.035), (0.15, 0.02)], n=20)   # the hood, open below
P("KV_Bulb").lathe(hx_, hz_, hy_ - 0.12, [(0, 0.001), (0.03, 0.03), (0.06, 0.001)], n=12)

T = K["trunk"]                                                   # Marina 382: khaki footlocker with a chessboard on it
tx0, tx1 = T["x"]; tz0, tz1 = T["z"]; th = T["h"]
P("KV_Trunk").box(tx0, tx1, 0, th, tz0, tz1)
for x in (tx0 + 0.12, tx1 - 0.14):                               # wooden bands, proud of the faces
    P("KV_TrunkBand").box(x, x + 0.02, -0.0 + 0.005, th + 0.008, tz0 - 0.008, tz1 + 0.008)
P("KV_Chess").box((tx0 + tx1) / 2 - 0.18, (tx0 + tx1) / 2 + 0.18, th - 0.005, th + 0.03, (tz0 + tz1) / 2 - 0.18, (tz0 + tz1) / 2 + 0.18)

# ---------------------------------------------------------------- write
bpy.ops.wm.read_factory_settings(use_empty=True)
COL = {"KV_Pine": ((0.62, 0.42, 0.22), 0.5), "KV_Mattress": ((0.85, 0.84, 0.80), 0.9), "KV_QuiltLow": ((0.8, 0.75, 0.7), 0.85),
       "KV_QuiltUp": ((0.12, 0.30, 0.18), 0.85), "KV_Pillow": ((0.90, 0.89, 0.86), 0.9), "KV_Gingham": ((0.5, 0.65, 0.5), 0.85),
       "KV_Brass": ((0.75, 0.56, 0.25), 0.3), "KV_Mirror": ((0.8, 0.82, 0.84), 0.05), "KV_Cork": ((0.52, 0.36, 0.20), 0.9),
       "KV_Paper": ((0.88, 0.87, 0.82), 0.9), "KV_DartBlack": ((0.03, 0.03, 0.03), 0.8), "KV_DartCream": ((0.80, 0.72, 0.55), 0.8),
       "KV_DartRed": ((0.55, 0.05, 0.05), 0.7), "KV_DartGreen": ((0.05, 0.35, 0.12), 0.7), "KV_Globe": ((0.10, 0.35, 0.70), 0.4),
       "KV_LampRed": ((0.70, 0.04, 0.04), 0.35), "KV_Bulb": ((1.0, 0.9, 0.7), 0.3), "KV_Trunk": ((0.60, 0.52, 0.30), 0.7),
       "KV_TrunkBand": ((0.40, 0.28, 0.14), 0.6), "KV_Chess": ((0.55, 0.40, 0.22), 0.5)}
MATS = {k: material(k, *v) for k, v in COL.items()}
coll = bpy.context.scene.collection
root = bpy.data.objects.new("KevinRoom_HiFi", None); coll.objects.link(root)
for p in parts.values():
    ob = p.build(coll, MATS); ob.parent = root
    if p.name in ("KV_Gingham", "KV_Globe", "KV_LampRed"):
        for poly in ob.data.polygons:
            poly.use_smooth = True
OUT.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(OUT), export_format="GLB", export_yup=True, export_apply=True)
print("wrote", OUT, {p.name: len(p.f) for p in parts.values()})

# Marina 365's pale reading chair with wooden arms: Poly Haven ArmChair_01 (CC0), cached by the earlier furniture jobs, re-exported as
# one GLB for StoreProps (store_props.json kevin_armchair fits it to its box). Skipped when the cache is missing (sfm-work is gitignored).
AC = ROOT / "sfm-work/polyhaven/ArmChair_01/ArmChair_01_2k.gltf"
if AC.exists():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(AC))
    bpy.ops.export_scene.gltf(filepath=str(OUT.with_name("KevinArmchair.glb")), export_format="GLB", export_yup=True)
    print("wrote", OUT.with_name("KevinArmchair.glb"))
