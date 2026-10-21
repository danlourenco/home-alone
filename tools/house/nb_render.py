"""nb_render: Blender (Cycles) views of the neighbourhood kit for review (Oct 20 2026): the film 11581 camera at night beside the frame,
and a day contact sheet of the Tier 2 houses. Loads the built GLBs (nb_house.py, nb_street.py, hifi_bare_trees.py), gives every NB_*
material the kit's texture set + palette colour (as SpecGreybox.Neighborhood does in Unity), lights the night as the film (porch and
window glow, C7 strings, the acorn street lamps; the police cars' red beacons only as a comparison aid).

  Blender -b --factory-startup -P tools/house/nb_render.py -- film11581 OUT.png [--half]
  Blender -b --factory-startup -P tools/house/nb_render.py -- house lot_B0 OUT.png [--night] [--lod1]
Not a lighting judgement (room-upgrade: batch renders lie about light); for massing, proportions, materials and layout.
"""
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[2]
NB = ROOT / "unity/HomeAlone/Assets/Models/Neighborhood"
TEX = ROOT / "unity/HomeAlone/Assets/Textures/Neighborhood"
MAN = json.loads((ROOT / "spec/neighborhood.json").read_text())
PAL = MAN["kit_palette"]; KT = json.loads((TEX / "kit_textures.json").read_text())
LAY = json.loads((NB / "street_layout.json").read_text())
LV = LAY["levels_rel_gy"]
B = lambda x, y, z: Vector((-x, z, y))          # spec -> Blender
BULB = [(1.0, 0.08, 0.04), (0.10, 0.9, 0.15), (1.0, 0.45, 0.05), (0.15, 0.30, 1.0), (1.0, 0.85, 0.65)]


def srgb2lin(c): return [((v + 0.055) / 1.055) ** 2.4 if v > 0.04045 else v / 12.92 for v in c]


def material(name, night):
    m = bpy.data.materials.get(name + "_R")
    if m: return m
    m = bpy.data.materials.new(name + "_R"); m.use_nodes = True; nt = m.node_tree; bsdf = nt.nodes["Principled BSDF"]
    k = name[3:]
    if name == "NB_Glass":
        bsdf.inputs["Base Color"].default_value = (0.01, 0.012, 0.015, 1); bsdf.inputs["Roughness"].default_value = 0.04; return m
    if name in ("NB_GlassLit", "NB_LampGlobe"):
        bsdf.inputs["Base Color"].default_value = (1, 0.8, 0.55, 1)
        bsdf.inputs["Emission Color"].default_value = (1.0, 0.72, 0.42, 1) if name == "NB_GlassLit" else (1.0, 0.88, 0.7, 1)
        bsdf.inputs["Emission Strength"].default_value = (2.2 if name == "NB_GlassLit" else 60.0) if night else 0.0
        rc = TEX / "room_cards.png"
        if name == "NB_GlassLit" and rc.exists():   # step 3: the room cards (nb_textures.room_cards) on the window's own UVs
            im = nt.nodes.new("ShaderNodeTexImage"); im.image = bpy.data.images.load(str(rc), check_existing=True)
            nt.links.new(im.outputs["Color"], bsdf.inputs["Emission Color"]); nt.links.new(im.outputs["Color"], bsdf.inputs["Base Color"])
            bsdf.inputs["Emission Strength"].default_value = 3.0 if night else 0.0
        if name == "NB_LampGlobe" and not night: bsdf.inputs["Roughness"].default_value = 0.1; bsdf.inputs["Transmission Weight"].default_value = 0.6
        return m
    if name.startswith("NB_car_"):   # step 3 street life: gloss paint / chrome / tyres (nb_life.py)
        col = name[7:]; bsdf.inputs["Base Color"].default_value = (*srgb2lin(PAL.get(col, [0.5, 0.5, 0.5])), 1)
        bsdf.inputs["Roughness"].default_value = 0.6 if col == "tyre" else 0.12 if col == "chrome" else 0.25
        bsdf.inputs["Metallic"].default_value = 1.0 if col == "chrome" else 0.0; return m
    if name == "NB_Beacon":
        bsdf.inputs["Base Color"].default_value = (1, 0.05, 0.03, 1); bsdf.inputs["Emission Color"].default_value = (1, 0.05, 0.03, 1)
        bsdf.inputs["Emission Strength"].default_value = 40.0 if night else 0.0; return m
    if name == "NB_TreeCard":
        im = nt.nodes.new("ShaderNodeTexImage"); im.image = bpy.data.images.load(str(TEX / "tree_cards.png"), check_existing=True)
        nt.links.new(im.outputs["Color"], bsdf.inputs["Base Color"]); nt.links.new(im.outputs["Alpha"], bsdf.inputs["Alpha"])
        bsdf.inputs["Roughness"].default_value = 0.9; return m
    st = next((s for s in sorted(KT, key=len, reverse=True) if k.startswith(s + "_") or k == s), None)
    if st is None:
        bsdf.inputs["Base Color"].default_value = (0.5, 0.5, 0.5, 1); return m
    col = k[len(st) + 1:]; rgb = srgb2lin(PAL[col]) if col in PAL else [1, 1, 1]
    if st == "brick" and col in ("red",): rgb = [1, 1, 1]          # the brick scan keeps its own colour
    if st in ("roof_clay", "asphalt"): rgb = [1, 1, 1] if col not in PAL else rgb
    if st == "roof_asphalt": rgb = [min(1, 2.2 * c) for c in rgb]   # the scan is dark grey already: the palette shifts its hue
    tile = KT[st]["tile_m"]; d = TEX / st
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (1 / tile, 1 / tile, 1)
    nt.links.new(tc.outputs["UV"], mp.inputs["Vector"])
    def img(fn, cs):
        n = nt.nodes.new("ShaderNodeTexImage"); n.image = bpy.data.images.load(str(d / fn), check_existing=True); n.image.colorspace_settings.name = cs
        nt.links.new(mp.outputs["Vector"], n.inputs["Vector"]); return n
    a = img("albedo.jpg", "sRGB"); mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.blend_type = "MULTIPLY"; mix.inputs["Factor"].default_value = 1
    nt.links.new(a.outputs["Color"], mix.inputs[6]); mix.inputs[7].default_value = (*rgb, 1)
    nt.links.new(mix.outputs[2], bsdf.inputs["Base Color"])
    nm = img("normal.jpg", "Non-Color"); nn = nt.nodes.new("ShaderNodeNormalMap"); nt.links.new(nm.outputs["Color"], nn.inputs["Color"]); nt.links.new(nn.outputs["Normal"], bsdf.inputs["Normal"])
    mk = img("mask.png", "Non-Color"); inv = nt.nodes.new("ShaderNodeMath"); inv.operation = "SUBTRACT"; inv.inputs[0].default_value = 1.0
    nt.links.new(mk.outputs["Alpha"], inv.inputs[1]); nt.links.new(inv.outputs[0], bsdf.inputs["Roughness"])
    if "wet" in k: bsdf.inputs["Roughness"].default_value = 0.08; nt.links.remove(inv.outputs[0].links[0])
    return m


def load(path, dz=0.0, keep=lambda n: True):
    before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=str(path)); new = [o for o in bpy.data.objects if o not in before]
    for o in new:
        if o.parent is None: o.location.z += dz
        if o.type == "MESH" and (not keep(o.name) or "Collider" in o.name): o.hide_render = True
    return new


def assign(night):
    for o in bpy.data.objects:
        if o.type != "MESH": continue
        for i, s in enumerate(o.material_slots):
            if s.material and s.material.name.startswith("NB_"): o.material_slots[i].material = material(s.material.name.split(".")[0], night)


def scene(night, lots_lod0, lod1_only=False, near=None):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene; sc.render.engine = "CYCLES"; sc.cycles.samples = 96; sc.cycles.use_denoising = True
    try:
        bpy.context.preferences.addons["cycles"].preferences.compute_device_type = "METAL"; bpy.context.preferences.addons["cycles"].preferences.get_devices()
        for d in bpy.context.preferences.addons["cycles"].preferences.devices: d.use = True
        sc.cycles.device = "GPU"
    except Exception:
        pass
    sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Base Contrast" if night else "None"
    load(NB / "Street.glb")
    grade = LV["lot_grade"]
    for e in MAN["parcels"]:
        f = NB / f"{e['id']}.glb"
        if not f.exists() or e["id"] == "lot_A0": continue
        g = grade.get(e["id"], grade["tier3_B"] if e["side"] == "across_lincoln" else grade["tier3_A"])
        lod0 = e["id"] in lots_lod0 and not lod1_only
        load(f, g, keep=lambda n, lod0=lod0: ("LOD0" in n if lod0 else "LOD1" in n) or ("NightGlow" in n and night))
        xp = NB / f"{e['id']}_xmas.json"
        if night and lod0 and xp.exists(): bulbs(json.loads(xp.read_text())["bulbs"], g)
    # trees (BareTrees.glb): LOD0 within 30 m of `near`, LOD1 beyond
    tr = load(ROOT / "unity/HomeAlone/Assets/Models/Foyer/BareTrees.glb")
    src = {o.name: o for o in tr if o.type == "MESH"}
    for o in tr: o.hide_render = True
    bark = bpy.data.materials.new("bark_R"); bark.use_nodes = True; bark.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.09, 0.075, 0.065, 1)
    for o in src.values():
        for sl in o.material_slots:
            if sl.material and "Snow" not in sl.material.name: sl.material = bark
    for t in LAY["trees"]:
        y = LV["lawn_B"] if t["x"] > 36.3 else LV["lawn_A"]
        lod = "LOD0" if near is not None and math.hypot(t["x"] - near[0], t["z"] - near[1]) < 30 else "LOD1"
        s = src.get(f"{t['variant']}_{lod}")
        if not s: continue
        ob = bpy.data.objects.new("tree", s.data); bpy.context.scene.collection.objects.link(ob)
        sc_ = t["h_m"] / max(1.0, s.dimensions.z)
        ob.matrix_world = Matrix.Translation(B(t["x"], y - 0.3 * sc_, t["z"])) @ Matrix.Rotation(math.radians(t["yaw"]), 4, "Z") @ Matrix.Scale(sc_, 4)
    # lamp posts
    lp = load(NB / "LampPost.glb"); lsrc = {o.name: o for o in lp if o.type == "MESH"}
    for o in lp: o.hide_render = True
    for L in LAY["lamps"]:
        for nm in ("LampPost_LOD0", "LampPost_Globe_LOD0"):
            ob = bpy.data.objects.new(nm, lsrc[nm].data); bpy.context.scene.collection.objects.link(ob); ob.location = B(L["x"], LV["walk"], L["z"])
        if night: point(B(L["x"], LV["walk"] + 3.85, L["z"]), (1.0, 0.8, 0.6), 220, 0.18)
    life(night)
    assign(night)
    w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True; bg = w.node_tree.nodes["Background"]
    if night:
        bg.inputs["Color"].default_value = (0.004, 0.005, 0.009, 1); bg.inputs["Strength"].default_value = 1.0
        sun = bpy.data.lights.new("moon", "SUN"); sun.energy = 0.02; sun.color = (0.6, 0.7, 1.0); so = bpy.data.objects.new("moon", sun); sc.collection.objects.link(so)
        so.rotation_euler = (0, math.radians(55), math.radians(-12))   # a cool fill from the street side (the film's night is lit for camera: the roof reads pale)
        sun.energy = 0.12
    else:
        sky = w.node_tree.nodes.new("ShaderNodeTexSky"); w.node_tree.links.new(sky.outputs[0], bg.inputs["Color"]); bg.inputs["Strength"].default_value = 0.35
        try: sky.sky_type = "MULTIPLE_SCATTERING"
        except Exception: pass
        sky.sun_elevation = math.radians(18); sky.sun_rotation = math.radians(150)
        sun = bpy.data.lights.new("sun", "SUN"); sun.energy = 2.0; sun.angle = math.radians(3); so = bpy.data.objects.new("sun", sun); sc.collection.objects.link(so)
        so.rotation_euler = (math.radians(70), 0, math.radians(150))
    return sc


def life(night):
    """Step 3: street life (StreetLife.glb at life_layout.json; the police cars only at night) and the Tier 4 treeline (TreeLine.glb)."""
    lp = NB / "life_layout.json"
    if not lp.exists(): return
    L = json.loads(lp.read_text()); objs = load(NB / "StreetLife.glb"); src = {o.name: o for o in objs if o.type == "MESH"}
    for o in objs: o.hide_render = True
    lvl = lambda it: LV["walk"] if it.get("y") == "walk" else LV["lot_grade"].get(it.get("y", ""), LV["road"] if 30.62 < it["x"] < 41.3 else LV["lawn_B"] if it["x"] >= 41.3 else LV["lawn_A"])
    def put(name, x, y, z, yaw):
        if name not in src: return
        ob = bpy.data.objects.new(name, src[name].data); bpy.context.scene.collection.objects.link(ob)
        ob.matrix_world = Matrix.Translation(B(x, y, z)) @ Matrix.Rotation(yaw, 4, "Z")
    for it in L["items"]:
        if it.get("scene") == "night" and not night: continue
        h = it.get("heading", [0, 1]); yaw = math.atan2(h[0], h[1])   # spec heading (x, z) from +z; Blender: spec z = +y, spec x = -x
        for nm in (it["kind"], it["kind"] + "_Beacons"): put(nm, it["x"], lvl(it), it["z"], yaw)
        if it.get("scene") == "night": point(B(it["x"], lvl(it) + 1.7, it["z"]), (1.0, 0.05, 0.03), 120, 0.2)
    for q in L["poles"]: put("Pole", q["x"], LV["walk"], q["z"], 0.0)
    put("Wires", 0, 0, 0, 0.0)
    tl = NB / "TreeLine.glb"
    if tl.exists(): load(tl)


def point(loc, col, W, r=0.1):
    l = bpy.data.lights.new("p", "POINT"); l.energy = W; l.color = col; l.shadow_soft_size = r
    o = bpy.data.objects.new("p", l); bpy.context.scene.collection.objects.link(o); o.location = loc; return o


def bulbs(bl, dz):
    mats = []
    for i, c in enumerate(BULB):
        m = bpy.data.materials.new(f"bulb{i}"); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = (*c, 1); b.inputs["Emission Color"].default_value = (*c, 1); b.inputs["Emission Strength"].default_value = 90.0; mats.append(m)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.028); proto = bpy.context.object; proto.hide_render = True
    for i in range(5):
        pts = [b for b in bl if b[3] == i]
        me = bpy.data.meshes.new(f"bulbs{i}"); vs, fs = [], []
        for x, y, z, _ in pts:
            o = len(vs); c = B(x, y + dz, z); vs += [tuple(c + v.co) for v in proto.data.vertices]; fs += [tuple(o + j for j in p.vertices) for p in proto.data.polygons]
        me.from_pydata(vs, [], fs); me.materials.append(mats[i]); ob = bpy.data.objects.new(f"bulbs{i}", me); bpy.context.scene.collection.objects.link(ob)


def camera(loc_spec, fwd_spec, up_spec, f_px, w=1920, h=1058):
    cam = bpy.data.cameras.new("cam"); cam.sensor_fit = "HORIZONTAL"; cam.sensor_width = 36; cam.lens = f_px * 36 / w
    o = bpy.data.objects.new("cam", cam); bpy.context.scene.collection.objects.link(o); bpy.context.scene.camera = o
    f = B(*fwd_spec).normalized(); u = B(*up_spec).normalized(); r = f.cross(u).normalized(); u = r.cross(f)
    M = Matrix(((r.x, u.x, -f.x), (r.y, u.y, -f.y), (r.z, u.z, -f.z))).to_4x4(); M.translation = B(*loc_spec); o.matrix_world = M
    s = bpy.context.scene.render; s.resolution_x, s.resolution_y = w, h; s.resolution_percentage = 100
    return o


def film11581(out, half):
    c = json.loads((ROOT / "art/home_alone/references/neighborhood/data/film11581_camera.json").read_text())
    g = LV["lot_grade"]["lot_B0"]
    sc = scene(True, {"lot_B0", "lot_B-1", "lot_B+1"}, near=(c["camera_spec_xyz"][0], c["camera_spec_xyz"][2]))
    x, y, z = c["camera_spec_xyz"]; camera((x, y + g, z), c["forward_spec"], c["up_spec"], c["f_px"])
    # the Murphys' porch light (the bright lamp inside the porch by the door, film 11581/11556) and room light behind the lit windows
    point(B(62.9, g + 3.1, 12.9), (1.0, 0.75, 0.45), 260, 0.15)
    for zz in (8.2, 11.6, 15.2): point(B(65.0, g + 5.5, zz), (1.0, 0.7, 0.42), 60, 0.4); point(B(65.0, g + 2.2, zz), (1.0, 0.7, 0.42), 70, 0.4)
    # (step 3: the police cars and their beacons are street life now: life())
    if half: sc.render.resolution_percentage = 50
    sc.render.filepath = out; bpy.ops.render.render(write_still=True)


def view(out, eye, tgt, night, fpx=1100, lod0=("lot_B0", "lot_A+1", "lot_A-1", "lot_B-1", "lot_B+1")):
    """A free camera (spec x, y over gy, z): eye -> target, e.g. the street from our walk piers."""
    sc = scene(night, set(lod0), near=(eye[0], eye[2]))
    f = [tgt[i] - eye[i] for i in range(3)]; L = math.sqrt(sum(v * v for v in f)); f = [v / L for v in f]
    camera(eye, f, (0, 1, 0), fpx, 1920, 1080); sc.cycles.samples = 64
    if night:
        g = LV["lot_grade"]["lot_B0"]; point(B(62.9, g + 3.1, 12.9), (1.0, 0.75, 0.45), 260, 0.15)
    sc.render.filepath = out; bpy.ops.render.render(write_still=True)


def film1888(out):
    """Film 1888's solved camera (nb_film1888_camera.py, on our facade; day): Marley's house (lot_A+1) beyond our garage. Our own house
    and garage are the Unity build, not in these GLBs: their place shows empty."""
    c = json.loads((ROOT / "art/home_alone/references/neighborhood/data/film1888_camera.json").read_text())
    sc = scene(False, {"lot_A+1", "lot_A-1", "lot_B0"}, near=(c["camera_spec_world_y"][0], c["camera_spec_world_y"][2]))
    x, y, z = c["camera_spec_world_y"]; camera((x, y + 2.996, z), c["forward_spec"], c["up_spec"], c["f_px"])
    sc.cycles.samples = 64; sc.render.filepath = out; bpy.ops.render.render(write_still=True)


def house(lot, out, night, lod1):
    e = next(p for p in MAN["parcels"] if p["id"] == lot); k = e["kit"]; b0 = k["blocks"][0]
    cx, cz = (b0["x"][0] + b0["x"][1]) / 2, (b0["z"][0] + b0["z"][1]) / 2; front = -1 if e["side"] == "across_lincoln" else 1
    g = LV["lot_grade"][lot]
    sc = scene(night, {lot}, lod1_only=lod1, near=None)
    eye = (cx + front * 26.0, g + 1.6, cz + 11.0); tgt = (cx, g + 4.2, cz)
    f = [tgt[i] - eye[i] for i in range(3)]; L = math.sqrt(sum(v * v for v in f)); f = [v / L for v in f]
    camera(eye, f, (0, 1, 0), 1100, 1280, 800); sc.cycles.samples = 64
    sc.render.filepath = out; bpy.ops.render.render(write_still=True)


def aerial(out):
    """Bird's-eye over our lot toward Lincoln, day: every kit house (Tier 2 LOD0, Tier 3 LOD1), the street, lamps, trees. Our own
    house is not in these GLBs (it is the Unity build): its lot shows empty."""
    sc = scene(False, {"lot_B0", "lot_B-1", "lot_B+1", "lot_A-1", "lot_A+1"})
    eye = (-25.0, 55.0, 95.0); tgt = (45.0, 0.0, 5.0)
    f = [tgt[i] - eye[i] for i in range(3)]; L = math.sqrt(sum(v * v for v in f)); f = [v / L for v in f]
    camera(eye, f, (0, 1, 0), 1500, 1920, 1080); sc.cycles.samples = 64
    sc.render.filepath = out; bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    a = sys.argv[sys.argv.index("--") + 1:]
    if a[0] == "film11581": film11581(a[1], "--half" in a)
    elif a[0] == "aerial": aerial(a[1])
    elif a[0] == "film1888": film1888(a[1])
    elif a[0] == "piers": view(a[1], (29.0, LV["walk"] + 1.6, 9.716), (45.0, LV["walk"] + 2.6, 32.0), "--night" in a, 900)
    elif a[0] == "street": view(a[1], (37.0, LV["road"] + 1.6, -4.0), (37.0, LV["road"] + 2.0, 60.0), "--night" in a, 1000)
    elif a[0] == "house": house(a[1], a[2], "--night" in a, "--lod1" in a)
