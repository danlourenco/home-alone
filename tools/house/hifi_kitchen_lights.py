"""hifi_kitchen_lights: the breakfast-area chandelier as a model (user, Oct 16: "add night-accurate lighting to the kitchen"; "add
necessary light sources fixtures"). The kitchen's other lights are the under-cabinet strips, built with the cabinets
(tools/house/hifi_kitchen.py, KT_UnderLight).

The chandelier is Poly Haven Chandelier_02 (CC0, Oct 20: the user's download; brass, six arms, as the film's 980/1025/1103/2106) with its
shades flipped to open UP like the film's frosted bowls, fitted to Marina's measures (big clip f197/f261, spec/dressing/kitchen.json
"chandelier": hub bottom, 0.36 m shade ring; the rod is cut to the ceiling). Before Oct 20 it was generated here (lathed hub and tulips).

Built at its own origin = the ceiling point it hangs from (spec axes, y up); SpecGreybox.KitchenFixtures places it.
Materials: Light_Brass, Light_Shade (glows at night; HouseNightMode darkens it by day).

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P tools/house/hifi_kitchen_lights.py
  -> unity/HomeAlone/Assets/Models/Foyer/KitchenChandelier.glb
"""
import json
import os
import math
import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hifi_lib import Part, material   # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(os.environ.get("HA_MODEL_DIR", ROOT / "unity/HomeAlone/Assets/Models/Foyer")) / "KitchenChandelier.glb"   # HA_MODEL_DIR: a draft dir (the open editor must not import it mid-Play)
C = json.loads((ROOT / "spec/dressing/kitchen.json").read_text())["chandelier"]
def export(parts, out, name):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    M = {"Light_Brass": material("Light_Brass", (0.75, 0.56, 0.25), 0.3), "Light_Shade": material("Light_Shade", (0.95, 0.93, 0.88), 0.5)}
    coll = bpy.context.scene.collection
    root = bpy.data.objects.new(name, None); coll.objects.link(root)
    for p in parts:
        if p.f:
            ob = p.build(coll, M); ob.parent = root
            ob.modifiers.new("WeightedNormal", "WEIGHTED_NORMAL").keep_sharp = True   # artist-pipeline: smooth curved parts, flat faces stay flat
            for poly in ob.data.polygons: poly.use_smooth = True
    bpy.ops.export_scene.gltf(filepath=str(out), export_format="GLB", export_yup=True, export_apply=True)
    print("wrote", out, {p.name: len(p.f) for p in parts})


# ---- wall sconces (spec/dressing/kitchen.json "sconces"): a round brass backplate on the wall, a curved arm out and up to a cup,
# a frosted tulip shade facing up (film 1133/1151/2106; Marina f153/f165). Built in place, in spec metres (ground floor y 0).
SC = json.loads((ROOT / "spec/dressing/kitchen.json").read_text())["sconces"]
sb, ss = Part("Brass", "Light_Brass"), Part("Shade", "Light_Shade")


def disc(p, c, axis, r, t, n=32):
    """A disc (cylinder) of radius r, thickness t, from centre c along the horizontal unit axis (x or z, signed)."""
    ax = [axis[0], 0.0, axis[1]]; perp = [axis[1], 0.0, -axis[0]]
    def ring(o): return [(c[0] + o * ax[0] + r * math.cos(2 * math.pi * k / n) * perp[0], c[1] + r * math.sin(2 * math.pi * k / n),
                          c[2] + o * ax[2] + r * math.cos(2 * math.pi * k / n) * perp[2]) for k in range(n)]
    a, b = ring(0), ring(t)
    for k in range(n):
        k2 = (k + 1) % n; q = [a[k], a[k2], b[k2], b[k]]; m = [sum(v[i] for v in q) / 4 for i in range(3)]
        p.face(q, (m[0] - c[0] - (t / 2) * ax[0], m[1] - c[1], m[2] - c[2] - (t / 2) * ax[2]))
    p.face(a, (-ax[0], 0, -ax[2])); p.face(b, (ax[0], 0, ax[2]))


for sc in SC["list"]:
    out = sc["out"]; axis = (out, 0.0) if sc["wall"] == "x" else (0.0, out)
    wx, wz = (sc["at"], sc["along"]) if sc["wall"] == "x" else (sc["along"], sc["at"])
    y = sc["h"]; R = SC["reach"]
    disc(sb, (wx + axis[0] * 0.003, y, wz + axis[1] * 0.003), axis, SC["plate_r"], SC["plate_t"])            # backplate, 3 mm off the paper
    disc(sb, (wx + axis[0] * (0.003 + SC["plate_t"]), y, wz + axis[1] * (0.003 + SC["plate_t"])), axis, 0.018, 0.02, n=20)   # boss
    path = []
    for k in range(13):                                  # arm: out from the boss, then curving up to the cup
        t = k / 12; out_d = 0.03 + (R - 0.03) * math.sin(t * math.pi / 2); up = 0.11 * (1 - math.cos(t * math.pi / 2)) - 0.02 * math.sin(t * math.pi)
        path.append((wx + axis[0] * out_d, y + up, wz + axis[1] * out_d))
    sb.sweep(path, [(-0.005, -0.005), (0.005, -0.005), (0.005, 0.005), (-0.005, 0.005)])
    cx, cz, cy = wx + axis[0] * R, wz + axis[1] * R, y + 0.11
    sb.lathe(cx, cz, cy - 0.005, [(0, 0.012), (0.012, 0.03), (0.022, 0.032)], n=24)                         # cup
    ss.lathe(cx, cz, cy + 0.017, [(0, 0.028), (0.03, 0.042), (0.07, 0.062), (SC["shade_h"], SC["shade_rim_r"])], n=32)   # tulip shade
export((sb, ss), OUT.with_name("KitchenSconces.glb"), "KitchenSconces")

# ---- the chandelier: Poly Haven Chandelier_02 (CC0; the user's download, unzipped into sfm-work/polyhaven/Chandelier_02): brass, six
# arms on a turned column, as the film's (980/1025/1103/2106). Its drum shades hang wide end down; the film's frosted bowls open UP, so
# each shade is flipped about its own middle (wide end up, still seated on its cup). Fitted to Marina's measures (spec "chandelier"):
# uniform scale to put the shade centres on ring_r, hub bottom at hub_bottom; the rod alone is cut to reach the ceiling canopy.
CH02 = ROOT / "sfm-work/polyhaven/Chandelier_02/Chandelier_02_4k.blend"
bpy.ops.wm.read_factory_settings(use_empty=True)
with bpy.data.libraries.load(str(CH02)) as (src, dst):
    dst.objects = ["Chandelier_02"]
ob = dst.objects[0]; bpy.context.scene.collection.objects.link(ob)
bpy.context.view_layer.objects.active = ob; ob.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="SELECT"); bpy.ops.mesh.separate(type="LOOSE"); bpy.ops.object.mode_set(mode="OBJECT")
parts = [o for o in bpy.context.scene.objects if o.type == "MESH"]
def bb(o):
    vs = [v.co for v in o.data.vertices]
    return [min(v[i] for v in vs) for i in range(3)], [max(v[i] for v in vs) for i in range(3)]
B = {o: bb(o) for o in parts}
z_lo = min(lo[2] for lo, hi in B.values()); z_hi = max(hi[2] for lo, hi in B.values())
bulbs = [o for o in parts if o.data.materials[o.data.polygons[0].material_index].name.endswith("_bulb")]
shades = [o for o in parts if o not in bulbs and B[o][1][0] - B[o][0][0] > 0.12 and B[o][0][2] > z_lo + 0.15 and B[o][1][2] < z_lo + 0.32]
assert len(shades) == len(bulbs) == C["arms"], (len(shades), len(bulbs))
rod = [o for o in parts if B[o][1][2] - B[o][0][2] > 0.3 and B[o][1][0] - B[o][0][0] < 0.02]; assert len(rod) == 1
canopy = [o for o in parts if B[o][0][2] > z_hi - 0.07]
hub = max(parts, key=lambda o: len(o.data.polygons))   # the turned brass dome under the arms: slimmed to the film's narrow column (980/1025; AUTHORED x0.6 across)
ring = sum(math.hypot((B[o][0][0] + B[o][1][0]) / 2, (B[o][0][1] + B[o][1][1]) / 2) for o in shades) / len(shades)
k = C["ring_r"] / ring; H0 = C["hub_bottom"] - C["ceiling"]
body_top = H0 + (B[rod[0]][0][2] - z_lo) * k; can_bot = -(z_hi - min(B[o][0][2] for o in canopy)) * k
brass_m = material("Light_Brass", (0.75, 0.56, 0.25), 0.3); shade_m = material("Light_Shade", (0.95, 0.93, 0.88), 0.5)
for o in parts:
    lo, hi = B[o]; flip = False
    for v in o.data.vertices:
        x, y, z = v.co
        if o in rod:
            z = body_top + (z - lo[2]) / (hi[2] - lo[2]) * (can_bot - body_top)
        elif o in canopy:
            z = (z - z_hi) * k
        else:
            z = H0 + (z - z_lo) * k
        if o is hub:
            x, y = x * 0.6, y * 0.6
        v.co = (x * k, y * k, z)
    if o in rod:   # Poly Haven's custom normals don't follow the stretch
        bpy.context.view_layer.objects.active = o; bpy.ops.mesh.customdata_custom_splitnormals_clear(); o.data.shade_smooth()
    o.data.materials.clear(); o.data.materials.append(brass_m)
# re-seat the shades: the model's drums (and the candle bulbs in them) out, a frosted ribbed bowl opening UP on each cup (film 980/1025:
# rounded, ~1.6x as wide as tall; rim radius and height AUTHORED by eye to the film's proportions against the arm ring)
BOWL_R, BOWL_H, NECK_R = 0.105, 0.13, 0.03
seats = [((B[o][0][0] + B[o][1][0]) / 2 * k, (B[o][0][1] + B[o][1][1]) / 2 * k, H0 + (B[o][0][2] - z_lo) * k) for o in shades]
for o in shades + bulbs:
    parts.remove(o); bpy.data.objects.remove(o, do_unlink=True)
import bmesh
for i, (bx, by, bz) in enumerate(seats):
    bm = bmesh.new(); NS, NR = 48, 12; rings = []
    for side, inset in ((0, 0.0), (1, 0.003)):   # outer and inner skins (seen from below and from the stair above)
        ring_list = []
        for j in range(NR + 1):
            t = j / NR; r = NECK_R + (BOWL_R - NECK_R) * math.sin(t * math.pi / 2) - inset
            ring_list.append([bm.verts.new((bx + r * (1 + 0.035 * math.cos(12 * 2 * math.pi * q / NS)) * math.cos(2 * math.pi * q / NS),
                                            by + r * (1 + 0.035 * math.cos(12 * 2 * math.pi * q / NS)) * math.sin(2 * math.pi * q / NS), bz + BOWL_H * t + inset))
                              for q in range(NS)])
        for j in range(NR):
            for q in range(NS):
                f = [ring_list[j][q], ring_list[j][(q + 1) % NS], ring_list[j + 1][(q + 1) % NS], ring_list[j + 1][q]]
                bm.faces.new(f if side == 0 else f[::-1])
        rings.append(ring_list)
    bm.faces.new(rings[0][0][::-1])   # the neck's floor
    for q in range(NS):   # the rim joining the two skins
        bm.faces.new([rings[0][NR][q], rings[0][NR][(q + 1) % NS], rings[1][NR][(q + 1) % NS], rings[1][NR][q]][::-1])
    bmesh.ops.recalc_face_normals(bm, faces=[f for f in bm.faces if f.verts[0] in rings[0][0]])
    me = bpy.data.meshes.new(f"Bowl{i}"); bm.to_mesh(me); me.shade_smooth(); me.materials.append(shade_m)
    ob2 = bpy.data.objects.new(f"Bowl{i}", me); bpy.context.scene.collection.objects.link(ob2); parts.append(ob2)
cups = [bz + BOWL_H for bx, by, bz in seats]
print(f"Chandelier_02: k {k:.3f} (shade ring {ring:.3f} -> {C['ring_r']}), {len(parts)} parts, shades re-seated as upward bowls, rod cut to {can_bot - body_top:.3f} m, "
      f"bowl rims {C['ceiling'] + max(cups):.3f} (spec cup_y {C['cup_y']}), span {2 * (C['ring_r'] + BOWL_R):.2f} m, "
      f"tris {sum(len(p.vertices) - 2 for o in parts for p in o.data.polygons)}")
bpy.context.view_layer.objects.active = parts[0]
for o in parts:
    o.select_set(True)
bpy.ops.object.join(); bpy.context.view_layer.objects.active.name = "KitchenChandelier"
OUT.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(OUT), export_format="GLB", export_yup=True, export_apply=True)
print("wrote", OUT)
