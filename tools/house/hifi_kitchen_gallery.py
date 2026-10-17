"""hifi_kitchen_gallery: the picture gallery and the slant-front desk on the kitchen's wall beside the corner pantry (the kitchen /
sunroom wall, spec x 2.316; lighting sweep Oct 16: film 1049/1133/1151/2106 show framed pictures round a pair of sconces over a
desk with greenery; Marina f153/f165 place them, spec/dressing/kitchen.json "gallery" and "desk").

The pictures are INVENTED: generated landscapes and a still life (numpy, here), never film captures or anyone's likeness (the
film's are family photos; ours are deliberately not). Frames: a 25 mm moulding with a rounded face, the picture 12 mm behind
its front and 13 mm off the paper (>= 1 cm everywhere, zfight-check). Desk: a slant-front desk on bracket feet, three drawers
with brass bails, the slant lid with a brass escutcheon.

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P tools/house/hifi_kitchen_gallery.py
  -> unity/HomeAlone/Assets/Models/Foyer/KitchenGallery.glb, Assets/Textures/Kitchen/gallery_p*.png
"""
import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hifi_lib import Part, material   # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "unity/HomeAlone/Assets/Models/Foyer/KitchenGallery.glb"
TEX = ROOT / "unity/HomeAlone/Assets/Textures/Kitchen"
K = json.loads((ROOT / "spec/dressing/kitchen.json").read_text())
G, DK = K["gallery"], K["desk"]
WX = G["wall_x"]                                   # the wall's face (kitchen side is -x)


# ---------------------------------------------------------------- invented pictures
def smooth_noise(h, w, cells, rng):
    g = rng.normal(0, 1, (cells + 1, cells + 1))
    ys, xs = np.linspace(0, cells, h, endpoint=False), np.linspace(0, cells, w, endpoint=False)
    yi, xi = ys.astype(int), xs.astype(int); fy, fx = ys - yi, xs - xi
    fy, fx = fy * fy * (3 - 2 * fy), fx * fx * (3 - 2 * fx)
    a = g[yi][:, xi] * (1 - fx) + g[yi][:, xi + 1] * fx; b = g[yi + 1][:, xi] * (1 - fx) + g[yi + 1][:, xi + 1] * fx
    return a * (1 - fy)[:, None] + b * fy[:, None]


def landscape(h, w, seed, sky0, sky1, hill, field, season):
    rng = np.random.default_rng(seed); y = np.linspace(0, 1, h)[:, None]; x = np.linspace(0, 1, w)[None, :]
    img = np.zeros((h, w, 3)); img[:] = np.array(sky0) * (1 - y[..., None]) + np.array(sky1) * y[..., None]
    img += 0.03 * smooth_noise(h, w, 6, rng)[..., None]
    ridge = 0.52 + 0.06 * np.sin(x * 7 + seed) + 0.04 * smooth_noise(1, w, 5, rng)
    img = np.where((y > ridge)[..., None], np.array(hill) * (0.9 + 0.1 * smooth_noise(h, w, 8, rng))[..., None], img)
    ground = 0.66 + 0.03 * np.sin(x * 3 + 2 * seed)
    img = np.where((y > ground)[..., None], np.array(field) * (0.85 + 0.15 * smooth_noise(h, w, 12, rng))[..., None], img)
    for k in range(int(rng.integers(3, 6))):                        # trees: dark blobs on trunks
        tx, ty, r = rng.uniform(0.08, 0.92), rng.uniform(0.6, 0.75), rng.uniform(0.04, 0.08)
        d = ((x - tx) / r) ** 2 + ((y - ty + r) / (1.3 * r)) ** 2
        img = np.where((d < 1)[..., None], np.array(season) * (0.7 + 0.3 * smooth_noise(h, w, 20, rng))[..., None], img)
        img = np.where(((abs(x - tx) < r * 0.12) & (y > ty - 0.2 * r) & (y < ty + 0.6 * r))[..., None], np.array([0.25, 0.17, 0.1]), img)
    return np.clip(img, 0, 1)


def still_life(h, w, seed):
    rng = np.random.default_rng(seed); y = np.linspace(0, 1, h)[:, None]; x = np.linspace(0, 1, w)[None, :]
    img = np.zeros((h, w, 3)); img[:] = np.array([0.18, 0.12, 0.08]) * (1.1 - 0.4 * y[..., None])
    img = np.where((y > 0.72)[..., None], np.array([0.45, 0.32, 0.2]), img)                              # table
    vase = (((x - 0.5) / 0.13) ** 2 + ((y - 0.62) / 0.16) ** 2) < 1
    img = np.where(vase[..., None], np.array([0.2, 0.3, 0.45]) * (0.8 + 0.3 * (1 - abs(x - 0.47) * 5)).clip(0.6, 1.1)[..., None], img)
    for k in range(14):                                                                                  # flowers
        fx, fy, r = rng.uniform(0.3, 0.7), rng.uniform(0.18, 0.46), rng.uniform(0.03, 0.06)
        col = [np.array([0.75, 0.15, 0.15]), np.array([0.9, 0.85, 0.75]), np.array([0.85, 0.6, 0.2])][k % 3]
        img = np.where((((x - fx) ** 2 + (y - fy) ** 2) < r * r)[..., None], col * (0.8 + 0.2 * smooth_noise(h, w, 30, rng))[..., None], img)
    return np.clip(img + 0.02 * smooth_noise(h, w, 40, rng)[..., None], 0, 1)


PICS = {"p1": lambda h, w: landscape(h, w, 3, [0.62, 0.72, 0.85], [0.9, 0.88, 0.8], [0.45, 0.52, 0.5], [0.55, 0.6, 0.35], [0.2, 0.35, 0.18]),
        "p2": lambda h, w: still_life(h, w, 7),
        "p3": lambda h, w: landscape(h, w, 11, [0.85, 0.75, 0.62], [0.95, 0.85, 0.7], [0.55, 0.45, 0.4], [0.85, 0.85, 0.88], [0.25, 0.2, 0.15]),
        "p4": lambda h, w: landscape(h, w, 19, [0.55, 0.65, 0.8], [0.85, 0.85, 0.82], [0.4, 0.45, 0.48], [0.88, 0.9, 0.92], [0.22, 0.28, 0.22])}


def save_png(name, arr):
    h, w, _ = arr.shape; im = bpy.data.images.new(name, w, h, alpha=False)
    rgba = np.concatenate([arr[::-1], np.ones((h, w, 1))], axis=2)                 # Blender pixels start at the bottom row
    im.pixels.foreach_set(rgba.astype(np.float32).ravel()); im.filepath_raw = str(TEX / f"{name}.png"); im.file_format = "PNG"; im.save()


# ---------------------------------------------------------------- geometry
frame, desk, brass = Part("Frame", "KG_Frame"), Part("Desk", "KG_Wood"), Part("Brass", "KG_Brass")
pics = {f["name"]: Part("Pic_" + f["name"], "KG_" + f["name"]) for f in G["frames"]}
MO, DEP = G["moulding"], G["depth"]

for f in G["frames"]:
    z0, z1 = f["z"]; y0, y1 = f["h"]; xb, xf = WX - 0.003, WX - 0.003 - DEP           # back on the wall (3 mm off), front 2 cm out
    for (a0, a1, b0, b1) in ((z0, z1, y1 - MO, y1), (z0, z1, y0, y0 + MO), (z0, z0 + MO, y0 + MO, y1 - MO), (z1 - MO, z1, y0 + MO, y1 - MO)):
        frame.box(xf, xb, b0, b1, a0, a1)
    xp = WX - 0.013                                                                    # the picture: 13 mm off the paper
    pts = [(xp - 0.0005, y0 + MO, z1 - MO), (xp - 0.0005, y0 + MO, z0 + MO), (xp - 0.0005, y1 - MO, z0 + MO), (xp - 0.0005, y1 - MO, z1 - MO)]
    pics[f["name"]].face(pts, (-1, 0, 0), [(0, 0), (1, 0), (1, 1), (0, 1)])            # seen from the kitchen: z decreases left to right

x0, x1 = DK["x"]; z0, z1 = DK["z"]; bh, th, bd = DK["base_h"], DK["top_h"], DK["back_depth"]
for zz in (z0, z1 - 0.07):                                                             # bracket feet
    for xx in (x0, x1 - 0.07):
        desk.box(xx, xx + 0.07, 0.0, 0.09, zz, zz + 0.07)
desk.box(x0 + 0.01, x1, 0.09, bh, z0 + 0.01, z1 - 0.01)                                 # carcass
desk.box(x0, x1, 0.09, 0.115, z0, z1)                                                   # base moulding
for k, (ya, yb) in enumerate(((0.13, 0.33), (0.35, 0.53), (0.55, 0.73))):               # drawer fronts, 1.2 cm proud
    desk.box(x0 - 0.002, x0 + 0.01, ya, yb, z0 + 0.03, z1 - 0.03)
    for zc in (z0 + 0.25, z1 - 0.25):
        brass.box(x0 - 0.008, x0 - 0.002, (ya + yb) / 2 - 0.012, (ya + yb) / 2 + 0.012, zc - 0.045, zc + 0.045)
# the slant lid: a prism over the carcass, front edge at the carcass front, back rising to the top
prof = [(x0 + 0.01, bh), (x1, bh), (x1, th), (x1 - bd, th)]
for (ax, ay), (bx, by) in zip(prof, prof[1:] + prof[:1]):
    dx, dy = bx - ax, by - ay; nrm = (dy, -dx)                                           # profile is CCW in (x, y)
    desk.face([(ax, ay, z0), (bx, by, z0), (bx, by, z1), (ax, ay, z1)], (nrm[0], nrm[1], 0))
desk.face([(x, y, z0) for x, y in prof], (0, 0, -1)); desk.face([(x, y, z1) for x, y in prof], (0, 0, 1))
mz = (z0 + z1) / 2
brass.box(x0 + 0.05, x0 + 0.062, bh + 0.035, bh + 0.065, mz - 0.02, mz + 0.02)          # escutcheon on the lid's front edge

bpy.ops.wm.read_factory_settings(use_empty=True)
TEX.mkdir(parents=True, exist_ok=True)
M = {"KG_Frame": material("KG_Frame", (0.25, 0.14, 0.07), 0.45), "KG_Wood": material("KG_Wood", (0.55, 0.37, 0.2), 0.45),
     "KG_Brass": material("KG_Brass", (0.75, 0.56, 0.25), 0.3)}
for f in G["frames"]:
    M["KG_" + f["name"]] = material("KG_" + f["name"], (0.8, 0.8, 0.8), 0.6)
for f in G["frames"]:                                                                  # the invented pictures
    z0_, z1_ = f["z"]; y0_, y1_ = f["h"]; w_px = 512; h_px = max(64, round(w_px * (y1_ - y0_ - 2 * MO) / (z1_ - z0_ - 2 * MO)))
    save_png("gallery_" + f["name"], PICS[f["name"]](h_px, w_px))
coll = bpy.context.scene.collection
root = bpy.data.objects.new("KitchenGallery", None); coll.objects.link(root)
for p in [frame, desk, brass] + list(pics.values()):
    if p.f:
        ob = p.build(coll, M); ob.parent = root
        if p in (frame, desk):
            b = ob.modifiers.new("Bevel", "BEVEL"); b.width = 0.002; b.segments = 2; b.limit_method = "ANGLE"; b.angle_limit = math.radians(40)
            ob.modifiers.new("WeightedNormal", "WEIGHTED_NORMAL").keep_sharp = True
OUT.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(OUT), export_format="GLB", export_yup=True, export_apply=True, export_texcoords=True)
print("wrote", OUT, {p.name: len(p.f) for p in [frame, desk, brass] + list(pics.values())})
