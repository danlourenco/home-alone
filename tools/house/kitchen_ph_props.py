"""kitchen_ph_props: film-coloured variants of Poly Haven CC0 models for the kitchen's store props (Oct 19, props lane; user: the
generated counter props "read as simple shapes, not film quality"). Each variant is the scanned/modelled mesh with its own normal map,
recoloured to the film (film 2116/1146, user photo IMG_4305) and, for the pans, turned to hang handle-up from the pot rack's hooks.

  kettle_film         GENERATED to the film's shape: Poly Haven's only kettle (vintage_electric_kettle, recoloured, build 1) read as a
                      tall bell on an electric base, not the film's squat whistling kettle
  stool_pine          wooden_stool_01: round seat, turned splayed legs, stretchers (the film's stool); weathered grey -> honey pine
  skillet_red_hang    brass_pan_01 (handle shortened to a skillet's): red enamel outside, black non-stick inside, iron handle
  skillet_black_hang  brass_pan_01: black cast iron / non-stick
  casserole_red_hang  pot_enamel_01 (no lid): red enamel outside, dark enamel inside, hung from one loop handle
  apple               food_apple_01: as scanned, roughness fixed

StoreProps' material conversion reads only constant factors (roughnessFactor -> smoothness; metallicFactor when the material has no
metallic-roughness map), so each variant's roughness/metallic maps are replaced by constants chosen per finish.
Sources: sfm-work/polyhaven/<id>/ (props.py get polyhaven ID 2k). Hang points (the handle hole / loop, local metres from the drawn
bounds' centre, Blender axes) -> sfm-work/props/kitchen_ph.json for the store_props entries.

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P tools/house/kitchen_ph_props.py [-- --preview DIR]
  -> unity/HomeAlone/Assets/Models/PolyHaven/Kitchen/<variant>.glb
"""
import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "sfm-work/polyhaven"
OUT = ROOT / "unity/HomeAlone/Assets/Models/PolyHaven/Kitchen"
META = ROOT / "sfm-work/props/kitchen_ph.json"
ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
PREVIEW = Path(ARGS[ARGS.index("--preview") + 1]) if "--preview" in ARGS else None

RED = (0.62, 0.05, 0.04)          # sRGB-encoded base colours (film 2116 kettle/pans in shade, a little under the lit highlights)
BLACK = (0.045, 0.043, 0.045)
DARK_ENAMEL = (0.07, 0.05, 0.05)
PINE = (0.66, 0.47, 0.30)         # film 2116 stool seats (lit ~0.82, 0.66, 0.45 under the lamps), honey pine; the cupboard face reads 0.72, 0.49, 0.33


def load(pid):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=str(next((SRC / pid).glob("*.gltf"))))
    return [o for o in bpy.data.objects if o.type == "MESH"]


def bsdf(m):
    return m.node_tree.nodes["Principled BSDF"]


def tex(m, socket):
    """The image feeding a BSDF input (through a separate-colour node for packed metal/rough maps)."""
    def up(s):
        for l in s.links:
            n = l.from_node
            if n.type == "TEX_IMAGE":
                return n
            for i in n.inputs:
                r = up(i)
                if r:
                    return r
        return None
    return up(bsdf(m).inputs[socket])


def constants(m, rough, metal=0.0):
    """Replace the roughness/metallic maps with constants (StoreProps reads only factors)."""
    b = bsdf(m)
    for socket, value in (("Roughness", rough), ("Metallic", metal)):
        for l in list(b.inputs[socket].links):
            m.node_tree.links.remove(l)
        b.inputs[socket].default_value = value
    return m


def recolour(m, rgb, strength, name):
    """Base colour = rgb modulated by the map's own luminance detail (strength 0: flat). A NEW image (room-upgrade trap: pack() packs
    the file on disk), colourspace set before the pixels (artist-pipeline trap)."""
    t = tex(m, "Base Color"); src = t.image
    px = np.array(src.pixels[:], dtype=np.float32).reshape(-1, src.channels)
    lum = px[:, :3] @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
    k = 1.0 + strength * (lum / max(1e-4, float(lum.mean())) - 1.0)
    out = np.ones((px.shape[0], 4), dtype=np.float32)
    out[:, :3] = np.clip(np.outer(k, rgb), 0, 1)
    img = bpy.data.images.new(name, src.size[0], src.size[1], alpha=False)
    img.colorspace_settings.name = "sRGB"
    img.pixels.foreach_set(out.ravel()); img.file_format = "JPEG"; img.pack()
    t.image = img
    return m


def flat(m, rgb):
    b = bsdf(m)
    for l in list(b.inputs["Base Color"].links):
        m.node_tree.links.remove(l)
    b.inputs["Base Color"].default_value = (*[c ** 2.2 for c in rgb], 1.0)   # linear
    for n in [n for n in m.node_tree.nodes if n.type == "TEX_IMAGE" and not n.outputs[0].is_linked and not n.outputs[1].is_linked]:
        m.node_tree.nodes.remove(n)   # an unlinked map would still show in previews
    return m


def copy(m, name):
    n = m.copy(); n.name = name
    return n


def assign(o, mats, which):
    """which(face centre (world), face normal (world)) -> index into mats."""
    me = o.data; me.materials.clear()
    for m in mats:
        me.materials.append(m)
    mw = o.matrix_world; nm = mw.to_3x3().inverted().transposed()
    for p in me.polygons:
        p.material_index = which(mw @ p.center, (nm @ p.normal).normalized())


def delete_faces(o, pred):
    import bmesh
    bm = bmesh.new(); bm.from_mesh(o.data); mw = o.matrix_world
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if pred(f)], context="FACES")
    bm.to_mesh(o.data); bm.free()


def join(objs):
    bpy.ops.object.select_all(action="DESELECT")
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    if len(objs) > 1:
        bpy.ops.object.join()
    o = bpy.context.view_layer.objects.active
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    return o


def basis(h, o):
    """A rotation taking direction h to +Z (up) and o to -Y."""
    h, o = Vector(h).normalized(), Vector(o).normalized()
    src = Matrix((h, o, h.cross(o))).transposed()
    dst = Matrix((Vector((0, 0, 1)), Vector((0, -1, 0)), Vector((0, 0, 1)).cross(Vector((0, -1, 0))))).transposed()
    return (dst @ src.inverted()).to_4x4()


def export(o, name, meta, hang=None):
    o.name = o.data.name = name
    bs = [Vector(v.co) for v in o.data.vertices]
    lo = Vector([min(v[i] for v in bs) for i in range(3)]); hi = Vector([max(v[i] for v in bs) for i in range(3)])
    c = (lo + hi) / 2
    meta[name] = {"size_blender": [round(v, 4) for v in hi - lo]}
    if hang is not None:
        meta[name]["hang_from_centre_blender"] = [round(v, 4) for v in hang - c]
    OUT.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=str(OUT / f"{name}.glb"), export_format="GLB", export_yup=True)
    tris = sum(len(p.vertices) - 2 for p in o.data.polygons)
    assert tris < 150000, (name, tris)
    print("wrote", name, [round(v, 3) for v in hi - lo], tris, "tris")
    if PREVIEW:
        preview(o, name)


def preview(o, name):
    PREVIEW.mkdir(parents=True, exist_ok=True)
    sc = bpy.context.scene; sc.render.engine = "BLENDER_WORKBENCH"; sc.display.shading.color_type = "TEXTURE"
    sc.display.shading.light = "STUDIO"; sc.render.resolution_x = sc.render.resolution_y = 480
    sc.world = sc.world or bpy.data.worlds.new("w")
    r = max(o.dimensions) * 1.9
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
    ctr = sum((o.matrix_world @ Vector(b) for b in o.bound_box), Vector()) / 8
    for i, d in enumerate(((0, -1, 0.35), (1, 0, 0.35), (0.7, 0.7, -0.6))):
        cam.location = ctr + Vector(d).normalized() * r
        cam.rotation_euler = (ctr - cam.location).to_track_quat("-Z", "Y").to_euler()
        sc.render.filepath = str(PREVIEW / f"{name}-{i}.png"); bpy.ops.render.render(write_still=True)


meta = {}

# ---- the film's kettle, generated (film 2116 / IMG_4305: a squat round red-enamel whistling kettle, chrome domed lid and knob, a
# spout with a chrome whistle cap, a tall chrome handle arching from the spout side over to the back). Poly Haven's vintage_electric_kettle
# (tried in build 1) reads as a tall bell on an electric base. Proportions by eye against the film's tiles (0.158 m): body 0.22 m across, 0.15 m to the lid rim,
# handle top 0.30 m.
def kettle_film():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    import bmesh
    def lathe_obj(name, prof, n=64):
        bm = bmesh.new(); rings = []
        for r, z in prof:
            rings.append([bm.verts.new((r * math.cos(2 * math.pi * k / n), r * math.sin(2 * math.pi * k / n), z)) for k in range(n)] if r > 1e-6 else [bm.verts.new((0, 0, z))])
        for a, b in zip(rings, rings[1:]):
            for k in range(n):
                k2 = (k + 1) % n
                if len(a) == 1: bm.faces.new((a[0], b[k], b[k2]))
                elif len(b) == 1: bm.faces.new((a[k], b[0], a[k2]))
                else: bm.faces.new((a[k], a[k2], b[k2], b[k]))
        me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
        o = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(o)
        bmesh_fix(o); return o
    def bmesh_fix(o):
        import bmesh as B
        bm = B.new(); bm.from_mesh(o.data); B.ops.recalc_face_normals(bm, faces=bm.faces); bm.to_mesh(o.data); bm.free()
        for p in o.data.polygons: p.use_smooth = True
    def tube(name, pts, r, taper=None):
        cu = bpy.data.curves.new(name, "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = r; cu.bevel_resolution = 6; cu.use_fill_caps = True
        sp = cu.splines.new("NURBS"); sp.points.add(len(pts) - 1)
        for p, c in zip(sp.points, pts): p.co = (*c, 1.0)
        sp.use_endpoint_u = True; sp.order_u = min(4, len(pts)); sp.resolution_u = 24
        if taper:
            for p, w in zip(sp.points, taper): p.radius = w
        o = bpy.data.objects.new(name, cu); bpy.context.scene.collection.objects.link(o)
        bpy.context.view_layer.objects.active = o; o.select_set(True); bpy.ops.object.convert(target="MESH"); o.select_set(False)
        for p in o.data.polygons: p.use_smooth = True
        return o
    def mat(name, rgb, rough, metal):
        m = bpy.data.materials.new(name); m.use_nodes = True; b = m.node_tree.nodes["Principled BSDF"]
        b.inputs["Base Color"].default_value = (*[c ** 2.2 for c in rgb], 1); b.inputs["Roughness"].default_value = rough; b.inputs["Metallic"].default_value = metal
        return m
    red, chrome, black = mat("kettle_film_enamel", RED, 0.12, 0.0), mat("kettle_film_chrome", (0.82, 0.82, 0.82), 0.1, 1.0), mat("kettle_film_black", (0.04, 0.04, 0.04), 0.4, 0.0)
    body = lathe_obj("body", [(0, 0.004), (0.085, 0.004), (0.1, 0.008), (0.109, 0.022), (0.112, 0.05), (0.108, 0.08), (0.097, 0.105), (0.08, 0.126),
                              (0.062, 0.14), (0.05, 0.147), (0.048, 0.149), (0, 0.149)])
    ring = lathe_obj("ring", [(0, 0.0), (0.084, 0.0), (0.088, 0.004), (0, 0.004)])           # the chrome-edged base ring
    lid = lathe_obj("lid", [(0, 0.148), (0.052, 0.148), (0.053, 0.152), (0.045, 0.163), (0.025, 0.172), (0.012, 0.175), (0, 0.175)])
    knob = lathe_obj("knob", [(0, 0.174), (0.006, 0.174), (0.006, 0.182), (0.014, 0.186), (0.013, 0.194), (0.006, 0.198), (0, 0.199)])
    spout = tube("spout", [(0.095, 0, 0.055), (0.125, 0, 0.08), (0.15, 0, 0.115), (0.165, 0, 0.145)], 0.018, [1.0, 0.75, 0.55, 0.45])
    whistle = tube("whistle", [(0.163, 0, 0.142), (0.172, 0, 0.155), (0.178, 0, 0.165)], 0.011, [1.0, 1.0, 0.8])
    handle = tube("handle", [(0.075, 0, 0.128), (0.09, 0, 0.2), (0.06, 0, 0.29), (-0.02, 0, 0.305), (-0.08, 0, 0.25), (-0.085, 0, 0.18), (-0.07, 0, 0.13)], 0.0065)
    for k, o in enumerate((body,)): o.data.materials.append(red)
    spout.data.materials.append(red)
    for o in (ring, lid, knob, whistle, handle): o.data.materials.append(chrome)
    objs = [body, ring, lid, knob, spout, whistle, handle]
    o = join(objs)
    wn = o.modifiers.new("wn", "WEIGHTED_NORMAL"); bpy.ops.object.modifier_apply(modifier="wn")
    export(o, "kettle_film", meta)

kettle_film()

# ---- counter stool (IMG_4305 / film 2116: four pine stools, round seat, turned splayed legs, two rings of stretchers) ----
o = join(load("wooden_stool_01")); m = o.data.materials[0]
recolour(constants(m, 0.55, 0.0), PINE, 0.25, "stool_pine_diff")   # the scan's weathering blotches read as dirt at 0.4 (build 1)
export(o, "stool_pine", meta)

# ---- pans: brass_pan_01, a 19 cm pan with a 26 cm handle; scaled per pan in store_props, handle shortened to a skillet's ----
def pan_variant(name, outside, inside, handle):
    o = join(load("brass_pan_01")); src = o.data.materials[0]
    vs = [Vector(v.co) for v in o.data.vertices]
    H = max(v.z for v in vs); bottom = [v for v in vs if v.z < 0.004]
    cx, cy = sum(v.x for v in bottom) / len(bottom), sum(v.y for v in bottom) / len(bottom)
    R = max(math.hypot(v.x - cx, v.y - cy) for v in vs if v.z > H - 0.006 and math.hypot(v.x - cx, v.y - cy) < 0.12)
    far = max(vs, key=lambda v: math.hypot(v.x - cx, v.y - cy)); hd = Vector((far.x - cx, far.y - cy, 0)).normalized()
    # shorten the handle's middle (the end loop keeps its shape): 0.26 m -> ~0.17 m (a skillet handle ~0.9 x the pan's diameter)
    end = max(Vector((v.x - cx, v.y - cy, 0)).dot(hd) for v in vs); a, b = R + 0.03, end - 0.045; k = 0.45
    for v in o.data.vertices:
        t = Vector((v.co.x - cx, v.co.y - cy, 0)).dot(hd)
        if t > a:
            v.co -= hd * ((min(t, b) - a) * (1 - k) + 0)
    outside_m = recolour(constants(copy(src, name + "_out"), *outside[1:]), outside[0], 0.08, name + "_out_diff")
    inside_m = recolour(constants(copy(src, name + "_in"), *inside[1:]), inside[0], 0.25, name + "_in_diff")
    handle_m = recolour(constants(copy(src, name + "_handle"), *handle[1:]), handle[0], 0.3, name + "_handle_diff")
    def which(c, n):
        r = math.hypot(c.x - cx, c.y - cy)
        if r > R + 0.006:
            return 2
        radial = Vector((c.x - cx, c.y - cy, 0)).normalized() if r > 1e-4 else Vector((0, 0, 0))
        return 1 if (n.z > 0.5 and c.z > 0.002) or (n.dot(radial) < -0.3) else 0
    assign(o, [outside_m, inside_m, handle_m], which)
    vs = [Vector(v.co) for v in o.data.vertices]; end = max(Vector((v.x - cx, v.y - cy, 0)).dot(hd) for v in vs)
    ring = [v for v in vs if Vector((v.x - cx, v.y - cy, 0)).dot(hd) > end - 0.03]
    hang = sum(ring, Vector()) / len(ring)            # the hanging hole's centre (the end loop's centroid)
    M = basis(hd, (0, 0, 1)); o.data.transform(M); hang = M @ hang
    export(o, name, meta, hang)

pan_variant("skillet_red_hang", (RED, 0.14, 0.0), (BLACK, 0.35, 0.0), ((0.05, 0.05, 0.05), 0.45, 0.6))
pan_variant("skillet_black_hang", ((0.05, 0.05, 0.055), 0.42, 0.25), (BLACK, 0.35, 0.0), ((0.05, 0.05, 0.05), 0.4, 0.0))

# ---- red casserole (film 2116 upper left: a red enamel casserole hanging by a loop handle, dark inside) ----
objs = load("pot_enamel_01")
for x in [o for o in objs if o.name.endswith("_lid")]:
    bpy.data.objects.remove(x)
o = join([x for x in bpy.data.objects if x.type == "MESH"]); src = o.data.materials[0]
outm = flat(constants(copy(src, "casserole_out"), 0.12, 0.0), RED); inm = flat(constants(copy(src, "casserole_in"), 0.25, 0.0), DARK_ENAMEL)
vs = [Vector(v.co) for v in o.data.vertices]; cx = sum(v.x for v in vs) / len(vs); cy = sum(v.y for v in vs) / len(vs); H = max(v.z for v in vs)
def which(c, n):
    radial = Vector((c.x - cx, c.y - cy, 0)); radial = radial.normalized() if radial.length > 1e-4 else Vector((0, 0, 0))
    return 1 if (n.z > 0.5 and c.z > 0.01) or (n.dot(radial) < -0.4 and math.hypot(c.x - cx, c.y - cy) < 0.085) else 0
assign(o, [outm, inm], which)
xmax = max(v.x for v in vs); loop = [v for v in vs if v.x > xmax - 0.012]; hang = sum(loop, Vector()) / len(loop)
M = basis((1, 0, 0), (0, 0, 1)); o.data.transform(M); hang = M @ hang
export(o, "casserole_red_hang", meta, hang)

# ---- fruit (film 6044/2116: a red bowl of fruit on a green plate) ----
for pid, name, rough in (("food_apple_01", "apple", 0.38),):
    o = join(load(pid)); constants(o.data.materials[0], rough, 0.0); export(o, name, meta)

META.parent.mkdir(parents=True, exist_ok=True); META.write_text(json.dumps(meta, indent=1))
print("meta", META)
