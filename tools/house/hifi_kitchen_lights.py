"""hifi_kitchen_lights: the breakfast-area chandelier as a model (user, Oct 16: "add night-accurate lighting to the kitchen"; "add
necessary light sources fixtures"). The kitchen's other lights are the under-cabinet strips, built with the cabinets
(tools/house/hifi_kitchen.py, KT_UnderLight).

From Marina's big clip (f197, f261; spec/dressing/kitchen.json "chandelier"): brass, eight arms curving down and out from a
turned hub and up to cups at a 0.36 m ring, frosted tulip shades facing up, a rod from a ceiling canopy. The film shows a brass
chandelier with white shades over the breakfast table by day (film-island-detail.jpg). Sizes beyond the ring and the hub's
height are authored (standard 28-30 in chandelier).

Built at its own origin = the ceiling point it hangs from (spec axes, y up); SpecGreybox.KitchenFixtures places it.
Materials: Light_Brass, Light_Shade (glows at night; HouseNightMode darkens it by day).

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P tools/house/hifi_kitchen_lights.py
  -> unity/HomeAlone/Assets/Models/Foyer/KitchenChandelier.glb
"""
import json
import math
import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hifi_lib import Part, material   # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "unity/HomeAlone/Assets/Models/Foyer/KitchenChandelier.glb"
C = json.loads((ROOT / "spec/dressing/kitchen.json").read_text())["chandelier"]
H0 = C["hub_bottom"] - C["ceiling"]            # hub bottom, relative to the ceiling (negative)
CUP = C["cup_y"] - C["ceiling"]; R = C["ring_r"]; N = C["arms"]
brass, shade = Part("Brass", "Light_Brass"), Part("Shade", "Light_Shade")

brass.lathe(0, 0, -0.035, [(0, 0.012), (0.02, 0.06), (0.035, 0.065)], n=20)                     # canopy on the ceiling
hub_top = H0 + 0.30
brass.lathe(0, 0, hub_top, [(0, 0.009), (-hub_top - 0.035, 0.009)], n=10)                      # rod to the canopy
brass.lathe(0, 0, H0, [(0, 0.004), (0.03, 0.022), (0.08, 0.05), (0.13, 0.045), (0.17, 0.02), (0.24, 0.014), (0.30, 0.018)], n=20)   # turned hub
y_arm = H0 + 0.10
for k in range(N):
    a = 2 * math.pi * (k + 0.5) / N; ca, sa = math.cos(a), math.sin(a)
    rp = [(0.045, y_arm), (0.14, y_arm - 0.07), (0.25, y_arm - 0.06), (R - 0.02, y_arm + 0.01), (R, CUP - 0.02)]
    brass.sweep([(r * ca, y, r * sa) for r, y in rp], [(-0.006, -0.006), (0.006, -0.006), (0.006, 0.006), (-0.006, 0.006)])
    cx, cz = R * ca, R * sa
    brass.lathe(cx, cz, CUP - 0.02, [(0, 0.012), (0.01, 0.03), (0.02, 0.03)], n=12)             # cup (bobeche)
    shade.lathe(cx, cz, CUP, [(0, 0.028), (0.03, 0.04), (0.07, 0.062), (0.10, 0.072)], n=16)       # frosted tulip shade, open side up

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

bpy.ops.wm.read_factory_settings(use_empty=True)
M = {"Light_Brass": material("Light_Brass", (0.75, 0.56, 0.25), 0.3), "Light_Shade": material("Light_Shade", (0.95, 0.93, 0.88), 0.5)}
coll = bpy.context.scene.collection
root = bpy.data.objects.new("KitchenChandelier", None); coll.objects.link(root)
for p in (brass, shade):
    if p.f:
        p.build(coll, M).parent = root
OUT.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(OUT), export_format="GLB", export_yup=True, export_apply=True)
print("wrote", OUT, {p.name: len(p.f) for p in (brass, shade)})
