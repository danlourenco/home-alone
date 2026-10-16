"""hifi_swing_door: the dining room's double-acting kitchen door (user, Oct 16: "i'd love to figure out how to put one of those push
doors on the left in"). Marina 228 s: a white six-panel leaf (two short top panels, two tall middle, two lower), a brass push plate
on the latch side at mid-height, no knob; it swings both ways (SwingDoor.cs).

Built in the leaf's own frame so it can turn about its hinge: origin = the hinge at the floor, the leaf runs along spec -z (Unity
+z) to its latch edge, its faces look along +-x. Both faces are panelled (it is seen from the dining room and the kitchen).
Width follows the opening (spec/geometry.json, the dining_room-kitchen door nearest the foyer) less 1 cm of clearance.

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P tools/house/hifi_swing_door.py
  -> unity/HomeAlone/Assets/Models/Foyer/SwingDoor.glb
"""
import json
import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hifi_lib import Part, material   # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "unity/HomeAlone/Assets/Models/Foyer/SwingDoor.glb"
G = json.loads((ROOT / "spec/geometry.json").read_text())["ground"]
O = max((o for o in G["openings"] if o["between"] == ["dining_room", "kitchen"]), key=lambda o: o["hi"])   # the one by the foyer
W, H, T = O["hi"] - O["lo"] - 0.01, 2.025, 0.035          # leaf width, height (80 in less floor clearance), thickness

paint, brass = Part("Paint", "SD_Paint"), Part("Brass", "SD_Brass")
st, mu = 0.11, 0.09                                       # stiles, centre muntin
rails = [(0.0, 0.22), (0.80, 0.93), (1.58, 1.68), (H - 0.11, H)]
z0, z1 = -W, 0.0                                          # latch edge to hinge edge (spec z)
paint.box(-T / 2, T / 2, 0.0, H, z0, z1)                  # the core slab
zc = (z0 + z1) / 2
cols = [(z0 + st, zc - mu / 2), (zc + mu / 2, z1 - st)]
for side in (-1, 1):                                      # each face: raised panels proud of the slab, 1.2 cm
    xf = side * T / 2
    for (ra, rb), (rc, _) in zip(rails, rails[1:]):
        for pa, pb in cols:
            paint.box(min(xf, xf + side * 0.012), max(xf, xf + side * 0.012), rb + 0.025, rc - 0.025, pa + 0.025, pb - 0.025)
    xp = xf + side * 0.004                                # push plate on the latch side, mid-height (Marina 228 s)
    brass.box(min(xf, xp), max(xf, xp), 0.98, 1.27, z0 + 0.035, z0 + 0.105)

bpy.ops.wm.read_factory_settings(use_empty=True)
M = {"SD_Paint": material("SD_Paint", (0.88, 0.87, 0.83), 0.35), "SD_Brass": material("SD_Brass", (0.75, 0.56, 0.25), 0.3)}
coll = bpy.context.scene.collection
root = bpy.data.objects.new("SwingDoor_Leaf", None); coll.objects.link(root)
for p in (paint, brass):
    p.build(coll, M).parent = root
OUT.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(OUT), export_format="GLB", export_yup=True, export_apply=True)
print("wrote", OUT, "leaf", round(W, 3), "x", H)
