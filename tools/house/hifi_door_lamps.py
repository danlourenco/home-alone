"""hifi_door_lamps: the two back-door wall lanterns (walk note Oct 19 09:03 "missing exterior lights by the basement door and kitchen.
please refer to appropriate movie stills"; changes/2026-10-19-exterior-mess-lamps.json, TRIAL; DEVIATIONS 104).

- KITCHEN BACK DOOR (film 10372, Harry's head on fire; 10324, Harry at the door): a small black square lantern with milky glass on a
  tall backplate, on the brick to the RIGHT of the door seen from the yard (spec +z). Read off 10372 with the door as the ruler
  (sill to head 510 px = 80 in -> 250 px/m; the casing 247 px wide = leaf 0.81 + 2 x 0.09 agrees): glass centre 1.84 m over the
  sill (0.2 m under the head), axis 0.28 m beyond the casing's outer edge, body ~0.16 wide x 0.22 tall.
- BASEMENT DOOR (film 9936, 10012, 10372): the same kind of lantern, a dark backplate and a frosted body with a cross bar, on the
  areaway's LEFT side wall (seen facing the door; spec z -0.065, film 10012 from above), ~0.7 m back from the door's wall, its glass
  over the door's lights (9936): centre 1.95 m over the landing. By eye, not measured (one steep frame each).
The glass panes are their own part (DL_Glass): HouseNightMode lights them at night only (ShellGlow), each lantern a night light
(SpecGreybox.Shell DoorLamps). World y (placed like Exterior.glb at y 0); spec x, z.

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P tools/house/hifi_door_lamps.py
  -> unity/HomeAlone/Assets/Models/Foyer/DoorLamps.glb
"""
import json
import math
import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hifi_lib import Part, material   # noqa: E402
import hifi_pipeline as hp            # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "unity/HomeAlone/Assets/Models/Foyer/DoorLamps.glb"
GF = json.loads((ROOT / "spec/geometry.json").read_text())["ground"]["floor_y"]
AREA = json.loads((ROOT / "spec/house_spec.ground.json").read_text())["basement"]["basement"]
LANDING_Y = GF + AREA["floor_y"]                   # the areaway landing is the basement floor (-2.681)
# (name, wall point (spec x, world y of the glass centre, spec z), outward normal (spec x, z), the wall's along-direction)
# kitchen: the back wall's brick face x = c - 0.07 - veneer 0.10 (exterior_shell OPEN), the door's mould ends at z 3.004 + 0.07
LAMPS = [("Kitchen", (-5.432, GF + 1.84, 3.074 + 0.28), (-1.0, 0.0)),
         ("Basement", (-6.20, LANDING_Y + 1.95, AREA["areaway"]["z"][0]), (0.0, 1.0))]
LAMPS_JSON = {n: {"glass_centre": [round(p[0] + 0.105 * o[0], 3), round(p[1], 3), round(p[2] + 0.105 * o[1], 3)]} for n, p, o in LAMPS}

metal, glass = Part("LampMetal", "DL_Metal"), Part("LampGlass", "DL_Glass")


def lamp(p, out):
    """One lantern on the wall point p, looking along out. Local frame: u along the wall, v up, w out of the wall."""
    ox, oz = out
    ux, uz = -oz, ox                                   # along the wall (horizontal, perpendicular to out)
    def W(u, v, w):                                    # local -> spec
        return (p[0] + u * ux + w * ox, p[1] + v, p[2] + u * uz + w * oz)
    def box(P, u0, u1, v0, v1, w0, w1):
        c = [W(u, v, w) for (u, v, w) in ((u0, v0, w0), (u1, v0, w0), (u1, v0, w1), (u0, v0, w1),
                                          (u0, v1, w0), (u1, v1, w0), (u1, v1, w1), (u0, v1, w1))]
        mid = [sum(q[i] for q in c) / 8 for i in range(3)]
        for f in ((0, 1, 2, 3), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)):
            pts = [c[i] for i in f]; fm = [sum(q[i] for q in pts) / 4 for i in range(3)]
            P.face(pts, tuple(fm[i] - mid[i] for i in range(3)))
    def frustum(P, v0, h0, v1, h1, wc):
        """A square frustum about the body's axis (u 0, w wc) from half-width h0 at v0 to h1 at v1, capped."""
        sq = lambda v, h: [W(-h, v, wc - h), W(h, v, wc - h), W(h, v, wc + h), W(-h, v, wc + h)]
        a, b = sq(v0, h0), sq(v1, h1); ax = W(0, 0, wc)
        for k in range(4):
            k2 = (k + 1) % 4
            m = [(a[k][i] + a[k2][i] + b[k][i] + b[k2][i]) / 4 for i in range(3)]
            P.face([a[k], a[k2], b[k2], b[k]], (m[0] - ax[0], 0, m[2] - ax[2]))
        if h0 > 0: P.face(a, (0, -1, 0) if v0 < v1 else (0, 1, 0))
        if h1 > 0: P.face(b, (0, 1, 0) if v0 < v1 else (0, -1, 0))

    H, wc = 0.075, 0.105                               # body half-width at the glass (0.15 m), its axis 10.5 cm off the wall
    g0, g1 = -0.095, 0.095                             # glass band about the glass centre (0.19 m)
    # backplate on the wall (1 cm thick, rounded-off by the bevel), 0.11 x 0.32
    box(metal, -0.055, 0.055, -0.17, 0.15, 0.0005, 0.0125)
    # top arm and bottom bracket from the plate to the body
    box(metal, -0.012, 0.012, g1 + 0.035, g1 + 0.055, 0.012, wc)
    box(metal, -0.010, 0.010, g0 - 0.060, g0 - 0.045, 0.012, wc - 0.02)
    # bottom: finial, pan, band; top: band, drip edge, hip cap, finial
    frustum(metal, g0 - 0.050, 0.012, g0 - 0.025, H + 0.004, wc)
    frustum(metal, g0 - 0.025, H + 0.004, g0, H + 0.004, wc)
    frustum(metal, g1, H + 0.004, g1 + 0.022, H + 0.010, wc)
    frustum(metal, g1 + 0.022, H + 0.020, g1 + 0.030, H + 0.020, wc)
    frustum(metal, g1 + 0.030, H + 0.014, g1 + 0.085, 0.012, wc)
    frustum(metal, g1 + 0.085, 0.012, g1 + 0.105, 0.003, wc)
    # corner posts, the back panel (no glass against the wall) and the cross bar of film 10012 on the three glass faces
    for su in (-1, 1):
        for sw in (-1, 1):
            box(metal, su * H - 0.006, su * H + 0.006, g0, g1, wc + sw * H - 0.006, wc + sw * H + 0.006)
    box(metal, -H, H, g0, g1, wc - H - 0.003, wc - H + 0.003)
    box(metal, -H, H, -0.004, 0.004, wc + H - 0.004, wc + H + 0.004)              # bar across the front pane
    for su in (-1, 1):                                                               # and the side panes
        box(metal, su * H - 0.004, su * H + 0.004, -0.004, 0.004, wc - H, wc + H)
    # milky glass panes (front and two sides), 4 mm, 1 mm inside the posts' outer faces
    gi = H - 0.003
    box(glass, -gi, gi, g0 + 0.001, g1 - 0.001, wc + gi - 0.002, wc + gi + 0.002)
    for su in (-1, 1):
        box(glass, su * gi - 0.002, su * gi + 0.002, g0 + 0.001, g1 - 0.001, wc - gi, wc + gi)


for _, p, o in LAMPS:
    lamp(p, o)

bpy.ops.wm.read_factory_settings(use_empty=True)
M = {"DL_Metal": material("DL_Metal", (0.02, 0.02, 0.02), 0.45), "DL_Glass": material("DL_Glass", (0.92, 0.90, 0.84), 0.25)}
coll = bpy.context.scene.collection
root = bpy.data.objects.new("DoorLamps_HiFi", None); coll.objects.link(root)
root["lod_reason"] = "single LOD: two small wall lanterns seen from the back yard and the areaway (<= 15 m)"
root["lamps"] = json.dumps(LAMPS_JSON)
stats = {}
for part in (metal, glass):
    ob = hp.to_object(part, M[part.mat], coll, hard_deg=30.0, weld=1e-5); ob.parent = root
    if part is metal:
        bv = ob.modifiers.new("Bevel", "BEVEL"); bv.width = 0.0015; bv.segments = 2; bv.limit_method = "ANGLE"
        bv.angle_limit = math.radians(30); bv.use_clamp_overlap = True
        wn = ob.modifiers.new("WeightedNormal", "WEIGHTED_NORMAL"); wn.keep_sharp = True; wn.mode = "FACE_AREA"
        hp.apply_modifiers(ob)
    stats[part.name] = len(ob.data.polygons)
OUT.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(OUT), export_format="GLB", export_yup=True, export_apply=True, export_extras=True)
print("wrote", OUT, stats, LAMPS_JSON)
