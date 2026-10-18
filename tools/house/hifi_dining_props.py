"""hifi_dining_props: the dining room's generated and Poly Haven (CC0) pieces (spec/dressing/dining.json), with the den's load/fit/recolour
(tools/house/hifi_den_props.py, run from its own source up to its build loop, as hifi_living_props.py):
  the lace tablecloth (generated: ivory all-over floral lace on top and skirt, a scalloped open-work border; film 246/252/254)
  Chandelier_03 -> the brass candle-arm chandelier with crystal (film 246/10560); its flame bulbs split off as DN_Bulb (lit at night)
  vintage_cabinet_01 -> the mahogany china cabinet (film 10550/10658), as the living room's curio
  fancy_picture_frame_01 -> the gilt still life over the sideboard (film 246)
  brass_pot_01 -> brass on the sideboard (film 246/10548)
Downloads in sfm-work/polyhaven/<id> (gitignored; https://api.polyhaven.com/files/<id>, gltf 2k); the .glb carries them (CC0).

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P tools/house/hifi_dining_props.py
  -> unity/HomeAlone/Assets/Models/Foyer/DiningProps.glb (placed by SpecGreybox.Dining)
"""
import json
import math
from pathlib import Path

import bpy
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
_src = (ROOT / "tools/house/hifi_den_props.py").read_text()
_ns = {"__file__": str(ROOT / "tools/house/hifi_den_props.py"), "__name__": "hifi_den_props_lib"}
exec(compile(_src[:_src.index("\nfor key, spec in P.items():")], "hifi_den_props.py", "exec"), _ns)   # resets the scene, defines load/fit/recolour
load, fit, recolour = _ns["load"], _ns["fit"], _ns["recolour"]
D = json.loads((ROOT / "spec/dressing/dining.json").read_text())
OUT = ROOT / "unity/HomeAlone/Assets/Models/Foyer/DiningProps.glb"
TEX = ROOT / "sfm-work/dining"; TEX.mkdir(parents=True, exist_ok=True)
MAHOGANY = (0.10, 0.035, 0.022)   # hifi_living_props.py's


# ------------------------------------------------------------------------------------------------ lace textures (numpy, tileable)
def lace_png(path, border):
    """ivory lace: a grid of six-petal rosettes joined by a net; border=True adds the open-work band (darker holes = shadow behind)"""
    N = 512; v, u = np.mgrid[0:N, 0:N] / N
    ivory = np.array([0.93, 0.91, 0.85])
    img = np.ones((N, N, 3)) * ivory
    cu, cv = (u * 4) % 1 - 0.5, (v * 4) % 1 - 0.5                          # 4 x 4 rosettes per tile
    r, a = np.hypot(cu, cv), np.arctan2(cv, cu)
    petal = r < 0.30 * (0.55 + 0.45 * np.abs(np.cos(3 * a)))
    ring = np.abs(r - 0.36) < 0.025
    net = (np.abs(((u + v) * 16) % 1 - 0.5) < 0.06) | (np.abs(((u - v) * 16) % 1 - 0.5) < 0.06)
    shade = np.where(petal, 0.97, np.where(ring, 0.80, np.where(net, 0.86, 0.92)))
    if border:   # open-work: round holes between the motifs read dark (the shadow under the hem)
        hu, hv = (u * 8) % 1 - 0.5, (v * 8) % 1 - 0.5
        holes = (np.hypot(hu, hv) < 0.22) & ~petal
        shade = np.where(holes, 0.35, shade)
    img *= shade[..., None]
    bi = bpy.data.images.new(path.stem, N, N); px = np.concatenate([img[::-1], np.ones((N, N, 1))], 2)
    bi.pixels = px.ravel().tolist(); bi.filepath_raw = str(path); bi.file_format = "PNG"; bi.save(); bi.pack()
    return bi


def tex_mat(name, img, rough=0.85):
    m = bpy.data.materials.new(name); m.use_nodes = True; m.use_backface_culling = False
    bsdf = m.node_tree.nodes["Principled BSDF"]; t = m.node_tree.nodes.new("ShaderNodeTexImage"); t.image = img
    m.node_tree.links.new(t.outputs["Color"], bsdf.inputs["Base Color"]); bsdf.inputs["Roughness"].default_value = rough
    return m


# ------------------------------------------------------------------------------------------------ the tablecloth
def cloth():
    """top 5 mm over the table, a rounded-corner skirt `overhang` outside its edge hanging `drop`, the last `lace` of it the border
    with a scalloped hem (spec -> Blender: (-x, z, y))"""
    t, c = D["table"], D["cloth"]
    x0, x1 = t["x"][0] - c["overhang"], t["x"][1] + c["overhang"]; z0, z1 = t["z"][0] - c["overhang"], t["z"][1] + c["overhang"]
    top = t["h"] + 0.012; hem = top - c["drop"]; band = hem + c["lace"]; R = 0.04; TILE = 0.30
    # perimeter: rounded rectangle, points every ~2 cm (s = arc length)
    corners = [(x1 - R, z1 - R, 0), (x0 + R, z1 - R, 90), (x0 + R, z0 + R, 180), (x1 - R, z0 + R, 270)]
    per = []
    for i, (cx, cz, a0) in enumerate(corners):
        for k in range(7):
            q = math.radians(a0 + 90 * k / 6); per.append((cx + R * math.cos(q), cz + R * math.sin(q)))
        nx, nz, _ = corners[(i + 1) % 4]; ex, ez = per[-1]
        fx, fz = nx + R * math.cos(math.radians(a0 + 90)), nz + R * math.sin(math.radians(a0 + 90))
        L = math.hypot(fx - ex, fz - ez); n = max(1, int(L / 0.02))
        per += [(ex + (fx - ex) * j / n, ez + (fz - ez) * j / n) for j in range(1, n)]
    s = [0.0]
    for (ax, az), (bx, bz) in zip(per, per[1:] + per[:1]):
        s.append(s[-1] + math.hypot(bx - ax, bz - az))
    P = per + [per[0]]   # closed: the seam point twice (its own u)
    B = lambda x, y, z: (-x, z, y)
    # top: a fan from the centre over the perimeter
    me = bpy.data.meshes.new("DiningCloth"); verts, faces, uvs, mats = [], [], [], []
    cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
    verts.append(B(cx, top, cz)); ctr = 0
    for (px, pz) in per:
        verts.append(B(px, top, pz))
    for i in range(len(per)):
        a, b = 1 + i, 1 + (i + 1) % len(per)
        faces.append((ctr, b, a)); mats.append(0)
        uvs.append([((x - x0) / TILE, (z - z0) / TILE) for x, z in ((cx, cz), per[b - 1], per[a - 1])])
    # skirt: rows top -> band -> hem (scalloped: 8 cm scallops, 2 cm deep at their meeting points)
    scal = lambda si: hem + 0.02 * (1 - abs(math.sin(math.pi * si / 0.08)))
    rows = [top, top - 0.002, band]
    base = len(verts)
    for i, (px, pz) in enumerate(P):
        verts += [B(px, y, pz) for y in rows] + [B(px, scal(s[i]), pz)]   # the hem's scallops follow arc length
    stride = len(rows) + 1
    for i in range(len(P) - 1):
        for r in range(stride - 1):
            a, b = base + i * stride + r, base + (i + 1) * stride + r
            faces.append((a, b, b + 1, a + 1)); mats.append(1 if r == stride - 2 else 0)
            ya, yb = (verts[a][1], verts[a + 1][1]), (verts[b][1], verts[b + 1][1])
            uvs.append([(s[i] / TILE, (top - ya[0]) / TILE), (s[i + 1] / TILE, (top - yb[0]) / TILE), (s[i + 1] / TILE, (top - yb[1]) / TILE), (s[i] / TILE, (top - ya[1]) / TILE)])
    me.from_pydata(verts, [], faces); me.update()
    uvl = me.uv_layers.new(name="UVMap")
    for poly, uv in zip(me.polygons, uvs):
        for li, (uu, vv) in zip(poly.loop_indices, uv):
            uvl.data[li].uv = (uu, vv)
    ob = bpy.data.objects.new("DiningCloth", me); bpy.context.scene.collection.objects.link(ob)
    ob.data.materials.append(tex_mat("DN_Cloth", lace_png(TEX / "lace.png", False)))
    ob.data.materials.append(tex_mat("DN_Lace", lace_png(TEX / "lace_border.png", True)))
    for poly, m in zip(me.polygons, mats):
        poly.material_index = m
    print(f"  cloth: x {x0:.3f}..{x1:.3f} z {z0:.3f}..{z1:.3f} top {top:.3f} hem {hem:.3f}")


cloth()

# ------------------------------------------------------------------------------------------------ the chandelier: flame bulbs split off
ch = D["chandelier"]; (cx, cz), (y0, y1) = ch["at"], ch["y"]
o = load("Chandelier_03", "chandelier")
k = (y1 - y0) / 1.0406   # uniform: the model's height 1.0406 native
fit(o, [cx - 0.39 * k, cx + 0.39 * k], [cz - 0.3925 * k, cz + 0.3925 * k], [y0, y1], "-z")
for ob in [q for q in o if q.type == "MESH"]:   # bulbs: faces whose diff texel is near white (the brass, crystal and chain are not)
    m0 = next((sl.material for sl in ob.material_slots if sl.material and sl.material.name == "Chandelier_03"), None)
    if m0 is None:
        continue
    img = next(n.image for n in m0.node_tree.nodes if n.type == "TEX_IMAGE" and "diff" in n.image.name)
    W, H = img.size; px = np.array(img.pixels[:]).reshape(H, W, 4)
    bulb = bpy.data.materials.new("DN_Bulb"); bulb.use_nodes = True
    bulb.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (1, 0.95, 0.85, 1)
    ob.data.materials.append(bulb); bi = len(ob.data.materials) - 1
    uvl = ob.data.uv_layers.active.data; n = 0
    for poly in ob.data.polygons:
        if ob.material_slots[poly.material_index].material is not m0:
            continue
        u = sum(uvl[li].uv[0] for li in poly.loop_indices) / poly.loop_total; v = sum(uvl[li].uv[1] for li in poly.loop_indices) / poly.loop_total
        t = px[int((v % 1) * (H - 1)), int((u % 1) * (W - 1)), :3]
        if t.min() > 0.6 and t.max() - t.min() < 0.12:
            poly.material_index = bi; n += 1
    print(f"  chandelier: {n} bulb faces")
    bpy.context.view_layer.objects.active = ob
    for q in bpy.context.view_layer.objects:
        q.select_set(q is ob)
    bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.separate(type="MATERIAL"); bpy.ops.object.mode_set(mode="OBJECT")

q = D["china_cabinet"]; o = load("vintage_cabinet_01", "chinacab")
recolour(o, "DN_CabinetMahogany", (0.20, 0.11, 0.065), keep=lambda rgb: (rgb[..., 0] > 0.3) & (rgb[..., 1] > 0.2) & (rgb[..., 2] < 0.7 * rgb[..., 1]))   # the living curio's brown, brass kept
fit(o, q["x"], q["z"], [0.0, q["h"]], q["front"])
p = D["painting"]; o = load("fancy_picture_frame_01", "dnpainting")
fit(o, p["x"], [p["z"] + 0.012, p["z"] + 0.032], p["h"], "+z")               # 1.2-3.2 cm off the sunroom wall face (3.004): at 0.5 its canvas fought the wall (z-fight, 9.7 mm)
for q in o:   # as hifi_living_props: the canvas 3% smaller so the frame's lip no longer covers it (Z-fight check)
    if q.name.endswith("_canvas"):
        bpy.context.view_layer.update(); c = sum((q.matrix_world @ __import__("mathutils").Vector(v) for v in q.bound_box), __import__("mathutils").Vector()) / 8
        for v in q.data.vertices:
            w = q.matrix_world @ v.co; w.x = c.x + (w.x - c.x) * 0.97; w.z = c.z + (w.z - c.z) * 0.97; v.co = q.matrix_world.inverted() @ w
t = D["pot"]; (px_, pz_), r = t["at"], t["d"] / 2
o = load("brass_pot_01", "dnpot"); fit(o, [px_ - r, px_ + r], [pz_ - r, pz_ + r], [t["y"], t["y"] + t["d"] * 0.29 / 0.30], "+x")

OUT.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(OUT), export_format="GLB", export_yup=True, export_apply=True)
print("wrote", OUT)
