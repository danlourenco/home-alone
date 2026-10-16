"""hifi_lights: the foyer's light fixtures as models (Blender), each built at its own origin and placed by SpecGreybox.HiFiLights.

Why (user, Oct 15: "place accurate lighting in the foyer according to stills ... the chandelier in the foyer by the vestibule ...
same with sconces"). From the film: a tall brass cage LANTERN with glass and candle bulbs hangs on a chain in the vestibule
(sled POV 3220-3229, landing 25); brass two-arm candle SCONCES with an oval backplate and ball body flank the vestibule
opening on the front wall (776-784). Marina 1070.5 s adds a pair beside the oval mirror. Sizes are standard (authored):
lantern body 0.28 m across x 0.50 m, sconce 0.36 m across the arms. Brass from the film crops.

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P tools/house/hifi_lights.py
  -> unity/HomeAlone/Assets/Models/Foyer/Lantern.glb (origin = ceiling point it hangs from), Sconce.glb (origin = wall point
     behind its backplate centre; it projects along +x and is turned in Unity to face the room)
"""
import math
import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hifi_lib import Part, material   # noqa: E402

OUT = Path(__file__).resolve().parents[2] / "unity/HomeAlone/Assets/Models/Foyer"


def export(parts, mats, name):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    M = {k: material(k, *v) for k, v in mats.items()}
    coll = bpy.context.scene.collection
    root = bpy.data.objects.new(name, None); coll.objects.link(root)
    for p in parts:
        if p.f:
            p.build(coll, M).parent = root
    bpy.ops.export_scene.gltf(filepath=str(OUT / f"{name}.glb"), export_format="GLB", export_yup=True, export_apply=True)
    print("wrote", name, {p.name: len(p.f) for p in parts})


BRASS = ((0.62, 0.45, 0.2), 0.3)
MATS = {"Light_Brass": BRASS, "Light_Glass": ((0.9, 0.92, 0.9), 0.05), "Light_Candle": ((0.95, 0.94, 0.9), 0.6),
        "Light_Bulb": ((1.0, 0.9, 0.7), 0.2, (1.0, 0.75, 0.45), 8.0)}

# ---------------------------------------------------------------- lantern: hangs from (0, 0, 0) down -y
brass, glass, candle, bulb = Part("Brass", "Light_Brass"), Part("Glass", "Light_Glass"), Part("Candles", "Light_Candle"), Part("Bulbs", "Light_Bulb")
R, TOP, BOT = 0.14, -0.19, -0.69                      # body radius, body top and bottom below the ceiling
brass.lathe(0, 0, -0.03, [(0, 0.07), (0.02, 0.07), (0.03, 0.02)], n=20)                     # ceiling canopy
for k in range(6):                                                                        # chain links, alternating
    y = -0.03 - 0.025 * (k + 1)
    if k % 2:
        brass.box(-0.008, 0.008, y - 0.022, y, -0.003, 0.003)
    else:
        brass.box(-0.003, 0.003, y - 0.022, y, -0.008, 0.008)
brass.lathe(0, 0, TOP - 0.06, [(0, 0.02), (0.03, 0.05), (0.06, 0.09), (0.07, R + 0.01), (0.08, R + 0.01)], n=24)   # crown
brass.lathe(0, 0, BOT - 0.06, [(0, 0.0), (0.02, 0.04), (0.05, R - 0.02), (0.06, R + 0.01), (0.07, R + 0.01)], n=24)  # base cap
for k in range(8):                                                                        # cage rods
    a = 2 * math.pi * k / 8; cx, cz = R * math.cos(a), R * math.sin(a)
    brass.box(cx - 0.006, cx + 0.006, BOT, TOP, cz - 0.006, cz + 0.006)
ring = [(0.0, R - 0.004), (TOP - BOT, R - 0.004)]
glass.lathe(0, 0, BOT, [(h, r) for h, r in ring], n=24)
for k in range(4):                                                                        # 4 candle bulbs
    a = 2 * math.pi * k / 4 + math.pi / 4; cx, cz = 0.06 * math.cos(a), 0.06 * math.sin(a)
    candle.lathe(cx, cz, BOT + 0.01, [(0, 0.012), (0.16, 0.012)], n=10)
    bulb.lathe(cx, cz, BOT + 0.17, [(0, 0.008), (0.015, 0.014), (0.035, 0.008), (0.05, 0.0)], n=10)
export([brass, glass, candle, bulb], MATS, "Lantern")

# ---------------------------------------------------------------- sconce: backplate on the wall plane x = 0, projecting +x
brass, candle, bulb = Part("Brass", "Light_Brass"), Part("Candles", "Light_Candle"), Part("Bulbs", "Light_Bulb")
# oval backplate 0.10 x 0.20, 1.5 cm thick
plate = [(0.05 * math.cos(2 * math.pi * k / 20), 0.10 * math.sin(2 * math.pi * k / 20)) for k in range(20)]
brass.poly([(0.015, y, z) for z, y in plate])                                             # front face (+x)
brass.poly([(0.0, y, z) for z, y in reversed(plate)])                                    # back face
for (za, ya), (zb, yb) in zip(plate, plate[1:] + plate[:1]):
    brass.quad((0.0, ya, za), (0.0, yb, zb), (0.015, yb, zb), (0.015, ya, za))
# ball body on a short stem
brass.box(0.015, 0.06, -0.012, 0.012, -0.012, 0.012)
n = 14
for i in range(n):                                                                        # sphere r 0.045 at x 0.09
    t0, t1 = math.pi * i / n, math.pi * (i + 1) / n
    for j in range(n):
        f0, f1 = 2 * math.pi * j / n, 2 * math.pi * (j + 1) / n
        P = lambda t, f: (0.09 + 0.045 * math.sin(t) * math.cos(f), -0.045 * math.cos(t), 0.045 * math.sin(t) * math.sin(f))
        brass.quad(P(t0, f0), P(t1, f0), P(t1, f1), P(t0, f1))
# two arms: from the ball sideways, curving up to a cup (bobeche) at +-0.10, 0.08 up (fits the 0.23 m gaps beside the opening)
for side in (-1, 1):
    pts = [(0.09, -0.01, 0.0)] + [(0.09 + 0.02 * math.sin(u * math.pi), -0.01 + 0.09 * (1 - math.cos(u * math.pi / 2)), side * 0.10 * u) for u in (0.25, 0.5, 0.75, 1.0)]
    brass.sweep(pts, [(-0.006, -0.006), (0.006, -0.006), (0.006, 0.006), (-0.006, 0.006)])
    cx, cz = pts[-1][0], pts[-1][2]
    brass.lathe(cx, cz, 0.08, [(0, 0.01), (0.015, 0.035), (0.02, 0.035)], n=16)           # bobeche cup
    candle.lathe(cx, cz, 0.10, [(0, 0.011), (0.12, 0.011)], n=10)                         # white candle sleeve
    bulb.lathe(cx, cz, 0.22, [(0, 0.008), (0.015, 0.014), (0.035, 0.008), (0.05, 0.0)], n=10)
export([brass, candle, bulb], MATS, "Sconce")
