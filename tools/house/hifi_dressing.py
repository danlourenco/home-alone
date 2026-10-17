"""hifi_dressing: the foyer's front-wall dressing as the film shows it (user note Oct 16 08:08: "those box fixtures look bad"),
placed from spec/dressing/foyer.json (Marina 203 s footprints and heights), spec metres, y above the ground floor.

Film 3225, 9358, 10248, 778:
- STANDS (flower_stand_left/right): dark wood pedestals, a round top with a green marble inset, three slender columns, a round
  base on brass bun feet; ~0.95 m (foyer.json)
- POINSETTIAS (flowers_left/right): white bracts over dark leaves in a crinkled gold-foil pot
- PRINTS (print_left/right): thin gilt frame, wide sea-green mat, the botanical plate cut from the film (film_prints.py:
  cherries left from 3225, currants right from 778); the paper carries UVs for its texture
Profiles and leaf shapes are authored; every face >= 1 cm off the one behind it (zfight-check).

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P tools/house/hifi_dressing.py
  -> unity/HomeAlone/Assets/Models/Foyer/FoyerDressing.glb
"""
import json
import math
import random
import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hifi_lib import Part, material   # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "unity/HomeAlone/Assets/Models/Foyer/FoyerDressing.glb"
P = {p["name"]: p for p in json.loads((ROOT / "spec/dressing/foyer.json").read_text())["pieces"] if "x" in p}
mid = lambda r: (r[0] + r[1]) / 2

wood, marble, brass, foil, bract, leaf, gilt, mat_ = (Part("Wood", "Dress_DarkWood"), Part("Marble", "Dress_Marble"), Part("Brass", "Door_Brass"),
                                                      Part("Foil", "Dress_Foil"), Part("Bracts", "Dress_Bract"), Part("Leaves", "Dress_Leaf"),
                                                      Part("Gilt", "Dress_Gilt"), Part("Mat", "Dress_Mat"))
cyathia = Part("Cyathia", "Door_Brass")
papers = {"print_left": Part("PaperL", "Print_Left"), "print_right": Part("PaperR", "Print_Right")}


def stand(name):
    p = P[name]; cx, cz, H = mid(p["x"]), mid(p["z"]), p["y"][1]; R = (p["x"][1] - p["x"][0]) / 2
    wood.lathe(cx, cz, H - 0.035, [(0, R - 0.01), (0.01, R), (0.025, R), (0.03, R - 0.012)], n=32)          # top with a moulded edge
    marble.lathe(cx, cz, H - 0.005, [(0, R - 0.03), (0.004, R - 0.03)], n=32)                              # green marble inset, proud
    brass.lathe(cx, cz, H - 0.05, [(0, R - 0.02), (0.012, R - 0.02)], n=32)                               # brass band under the top
    wood.lathe(cx, cz, 0.05, [(0, R - 0.005), (0.035, R - 0.005), (0.045, R - 0.02)], n=32)               # round base
    for k in range(3):
        a = 2 * math.pi * k / 3 + math.pi / 2; x, z = cx + 0.075 * math.cos(a), cz + 0.075 * math.sin(a)
        wood.lathe(x, z, 0.095, [(0, 0.016), (0.03, 0.013), (H - 0.20, 0.011), (H - 0.16, 0.014), (H - 0.145, 0.0)], n=12)   # columns
        bx, bz = cx + (R - 0.03) * math.cos(a), cz + (R - 0.03) * math.sin(a)
        brass.lathe(bx, bz, 0.0, [(0, 0.012), (0.02, 0.022), (0.04, 0.018), (0.05, 0.0)], n=12)              # bun feet


def poinsettia(name, stand_name, seed):
    p, s = P[name], P[stand_name]; cx, cz, y0 = mid(s["x"]), mid(s["z"]), s["y"][1]
    random.seed(seed)
    prof = [(0, 0.085), (0.02, 0.095), (0.19, 0.125), (0.21, 0.135), (0.22, 0.12)]   # film: a deep foil-wrapped pot
    foil.lathe(cx, cz, y0, [(h, r * random.uniform(0.97, 1.03)) for h, r in prof], n=18)               # crinkled foil pot
    top = y0 + 0.21; spread = (p["x"][1] - p["x"][0]) / 2 * 1.6    # the film's plants overhang their stands (3225, 10248): ~0.6 m across

    def blade(part, ox, oy, oz, ang, tilt, L, W):
        """One pointed leaf from (ox, oy, oz) outward along compass angle ang, tilted up by tilt; a fold down its middle."""
        dx, dz = math.cos(ang), math.sin(ang); up = math.sin(tilt); hz = math.cos(tilt)
        tip = (ox + dx * L * hz, oy + L * up, oz + dz * L * hz)
        midp = (ox + dx * L * 0.45 * hz, oy + L * 0.45 * up + 0.01, oz + dz * L * 0.45 * hz)
        sx, sz = -dz * W, dx * W
        for side in (1, -1):
            part.face([(ox, oy, oz), (midp[0] + side * sx, midp[1], midp[2] + side * sz), tip, midp], (0, 1, 0))
    for k in range(34):                                                                                     # dark leaves, drooping over the pot
        ang = 2 * math.pi * k / 16 + random.uniform(-0.2, 0.2)
        blade(leaf, cx, top + random.uniform(0.0, 0.08), cz, ang, random.uniform(-0.35, 0.25), spread * random.uniform(0.75, 1.05), 0.05)
    for c in range(26):                                                                                     # bract rosettes, in layers
        ca = 2 * math.pi * c * 0.618 + random.uniform(-0.3, 0.3); cr = 0 if c == 0 else spread * math.sqrt(c / 26) * 0.75
        ox, oz = cx + cr * math.cos(ca), cz + cr * math.sin(ca)
        oy = top + 0.04 + 0.22 * (1 - (cr / (spread * 0.75)) ** 2) + random.uniform(-0.02, 0.02)          # a dome from the pot rim up
        for k in range(8):
            blade(bract, ox, oy, oz, 2 * math.pi * k / 8 + random.uniform(-0.2, 0.2), random.uniform(0.15, 0.7), random.uniform(0.14, 0.22), 0.045)
        cyathia.lathe(ox, oz, oy - 0.005, [(0, 0.008), (0.012, 0.008)], n=6)                               # yellow cyathia at the centre (own part: hidden with the plant)


def framed_print(name):
    p, pp = P[name], P[name + "_paper"]; xw = p["x"][1]                                                      # the wall face behind
    z0, z1, y0, y1 = p["z"][0], p["z"][1], p["y"][0], p["y"][1]; f = 0.025                                  # gilt moulding width
    gilt.box(xw - 0.03, xw - 0.001, y0, y0 + f, z0, z1); gilt.box(xw - 0.03, xw - 0.001, y1 - f, y1, z0, z1)
    gilt.box(xw - 0.03, xw - 0.001, y0 + f, y1 - f, z0, z0 + f); gilt.box(xw - 0.03, xw - 0.001, y0 + f, y1 - f, z1 - f, z1)
    gilt.box(xw - 0.04, xw - 0.03, y0 + 0.006, y0 + 0.012, z0 + 0.006, z1 - 0.006)                          # a raised bead on the moulding
    mat_.box(xw - 0.012, xw - 0.002, y0 + f, y1 - f, z0 + f, z1 - f)                                        # the mat, set back in the frame
    pz0, pz1, py0, py1 = pp["z"][0], pp["z"][1], pp["y"][0], pp["y"][1]
    papers[name].face_uv([(xw - 0.024, py0, pz0), (xw - 0.024, py1, pz0), (xw - 0.024, py1, pz1), (xw - 0.024, py0, pz1)],
                         [(0, 0), (0, 1), (1, 1), (1, 0)], (-1, 0, 0))                                      # the plate, 1.2 cm proud of the mat


for side, seed in (("left", 3), ("right", 5)):
    stand(f"flower_stand_{side}"); poinsettia(f"flowers_{side}", f"flower_stand_{side}", seed); framed_print(f"print_{side}")

bpy.ops.wm.read_factory_settings(use_empty=True)
M = {"Dress_DarkWood": material("Dress_DarkWood", (0.10, 0.045, 0.03), 0.35), "Dress_Marble": material("Dress_Marble", (0.17, 0.27, 0.22), 0.15),
     "Door_Brass": material("Door_Brass", (0.75, 0.56, 0.25), 0.3), "Dress_Foil": material("Dress_Foil", (0.78, 0.6, 0.3), 0.25),
     "Dress_Bract": material("Dress_Bract", (0.93, 0.93, 0.88), 0.6), "Dress_Leaf": material("Dress_Leaf", (0.06, 0.13, 0.06), 0.55),
     "Dress_Gilt": material("Dress_Gilt", (0.72, 0.55, 0.25), 0.35), "Dress_Mat": material("Dress_Mat", (0.33, 0.52, 0.45), 0.8),
     "Print_Left": material("Print_Left", (1, 1, 1), 0.8), "Print_Right": material("Print_Right", (1, 1, 1), 0.8)}
coll = bpy.context.scene.collection
root = bpy.data.objects.new("FoyerDressing_HiFi", None); coll.objects.link(root)
parts = (wood, marble, brass, foil, bract, leaf, gilt, mat_, cyathia) + tuple(papers.values())
for part in parts:
    if part.f:
        part.build(coll, M).parent = root
OUT.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(OUT), export_format="GLB", export_yup=True, export_apply=True)
print("wrote", OUT, {p.name: len(p.f) for p in parts})
