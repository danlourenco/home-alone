"""hifi_exterior: the exterior skin's GLB from tools/house/exterior_shell.py's faces (Oct 18 2026, TRIAL; changes/2026-10-18-exterior-shell.json).

Every object is named by its draw set: L_* always drawn, U_* hidden while the player is upstairs (SpecGreybox.Shell / HouseSplit).
World y (the GLB is placed at y 0). Materials are remapped by name in SpecGreybox.Shell (EX_*).

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P tools/house/hifi_exterior.py
      -> runs tools/house/exterior_shell.py, then writes unity/HomeAlone/Assets/Models/Foyer/Exterior.glb
  ... -P tools/house/hifi_exterior.py -- --render <cams.json> <outdir>   (preview renders, Workbench, no export)
"""
import json
import math
import subprocess
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/house"))
from hifi_lib import Part, material   # noqa: E402

OUT = ROOT / "unity/HomeAlone/Assets/Models/Foyer/Exterior.glb"
if "--render" not in sys.argv:   # the faces come from the generator (shapely, outside Blender): build_models.py runs only this script
    subprocess.run(["uv", "run", "-q", "--with", "numpy", "--with", "shapely", "python", "-I", str(ROOT / "tools/house/exterior_shell.py")], check=True)
parts = json.loads((ROOT / "sfm-work/exterior/shell.json").read_text())
COL = {"EX_Brick": ((0.36, 0.12, 0.08), 0.9), "EX_Trim": ((0.90, 0.89, 0.85), 0.5), "EX_Shutter": ((0.03, 0.035, 0.035), 0.6),
       "EX_Roof": ((0.11, 0.095, 0.09), 0.9), "EX_Glass": ((0.10, 0.12, 0.14), 0.05), "EX_Shade": ((0.86, 0.82, 0.70), 0.9), "EX_Sheer": ((0.70, 0.69, 0.66), 0.25),
       "EX_Stone": ((0.78, 0.74, 0.66), 0.8), "EX_Gutter": ((0.88, 0.88, 0.86), 0.4), "EX_Pot": ((0.55, 0.28, 0.18), 0.8),
       "EX_DoorBlack": ((0.025, 0.03, 0.03), 0.35), "EX_Brass": ((0.75, 0.56, 0.25), 0.3), "EX_Wreath": ((0.08, 0.20, 0.08), 0.9),
       "EX_Bow": ((0.55, 0.04, 0.04), 0.6), "EX_PorchGlass": ((0.55, 0.62, 0.65), 0.05),
       "EX_Bulb": ((1.0, 0.80, 0.55), 0.3), "EX_LampGlow": ((1.0, 0.85, 0.60), 0.2),
       "EX_Snow": ((0.86, 0.88, 0.92), 0.8),
       "EX_BulbWarm": ((1.0, 0.70, 0.42), 0.3), "EX_BulbDim": ((0.9, 0.62, 0.38), 0.3), "EX_Wire": ((0.02, 0.04, 0.02), 0.6),
       "EX_Ice": ((0.80, 0.88, 0.95), 0.05)}

for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob)
coll = bpy.data.collections.new("Exterior"); bpy.context.scene.collection.children.link(coll)
mats = {n: material(n, c, r) for n, (c, r) in COL.items()}
root = bpy.data.objects.new("Exterior_HiFi", None); coll.objects.link(root)
# Exterior realism (Oct 18, TRIAL; changes/2026-10-18-exterior-realism.json): every face gets metric UVs (1 unit = 1 m) so the
# Unity materials can map PBR sets with height (POM) on the mesh's own UVs: roofs along the slope (u along the eave, v up the
# slope, so shingle rows run level on all four hips), walls u along the wall / v up, flats in plan. Edges that catch the light
# (trim, sills, cornice, columns, shutters, brick corners and reveals) get a small chamfer (bevel, harden normals).
BEVEL = {"Mould": 0.006, "Stone": 0.008, "Cornice": 0.008, "Portico": 0.008, "Column": 0.006, "DoorTrim": 0.005,
         "Dormer": 0.006, "Shutter": 0.003, "Sash": 0.003, "Casement": 0.003, "FrenchLeaf": 0.003, "Oculus": 0.004, "Gutter": 0.004}


def metric_uvs(ob):
    me = ob.data; uv = me.uv_layers.new(name="UVMap") if not me.uv_layers else me.uv_layers[0]
    up = Vector((0, 0, 1))
    for poly in me.polygons:
        n = poly.normal
        if abs(n.z) > 0.97:
            t, b = Vector((1, 0, 0)), Vector((0, 1, 0))
        else:
            t = up.cross(n).normalized()
            b = up if abs(n.z) < 0.15 else n.cross(t).normalized()   # walls: v = height; slopes: v runs up the slope
            if b.z < 0: b = -b
        for li in poly.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            uv.data[li].uv = (co.dot(t), co.dot(b))


def bevel(ob, w, groups):
    import bmesh
    bm = bmesh.new(); bm.from_mesh(ob.data); bm.faces.ensure_lookup_table()
    seen, tmap = {}, {}   # weld coincident corners within one box/prism/wall only (exterior_shell groups)
    for f, g in zip(bm.faces, groups):
        for v in f.verts:
            k = (g, round(v.co.x, 4), round(v.co.y, 4), round(v.co.z, 4))
            if k in seen and seen[k] is not v: tmap[v] = seen[k]
            else: seen.setdefault(k, v)
    bmesh.ops.weld_verts(bm, targetmap=tmap); bm.to_mesh(ob.data); bm.free()
    for poly in ob.data.polygons:
        poly.use_smooth = True
    m = ob.modifiers.new("Bevel", "BEVEL"); m.width = w; m.segments = 2; m.limit_method = "ANGLE"
    m.angle_limit = math.radians(35); m.use_clamp_overlap = True; m.harden_normals = True


for key, p in parts.items():
    pt = Part(key, p["mat"])
    for f in p["faces"]:
        pt.poly([tuple(v) for v in f])
    if pt.f:
        ob = pt.build(coll, mats); ob.parent = root
        metric_uvs(ob)
        w = BEVEL.get(key.split("_", 1)[1])
        if w and "--render" not in sys.argv and len(p.get("groups", [])) == len(ob.data.polygons): bevel(ob, w, p["groups"])
        if "--render" not in sys.argv: ob.modifiers.new("Tri", "TRIANGULATE")   # tangents (HDRP normal maps, parallax) are not exported from ngons

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if args and args[0] == "--render":
    cams, outdir = json.loads(Path(args[1]).read_text()), Path(args[2]); outdir.mkdir(parents=True, exist_ok=True)
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_WORKBENCH"; sc.display.shading.light = "STUDIO"; sc.display.shading.color_type = "MATERIAL"
    sc.display.shading.show_shadows = True; sc.display.shading.show_cavity = True
    sc.render.resolution_x, sc.render.resolution_y = 1920, 1058
    w = bpy.data.worlds.new("w"); sc.world = w
    # ground at the front yard level
    bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, -4.33)); g = bpy.context.active_object
    gm = material("Snow", (0.85, 0.86, 0.88), 0.9); g.data.materials.append(gm)
    to_b = lambda p: Vector((-p[0], p[2], p[1]))
    for c in cams:
        cd = bpy.data.cameras.new(c["name"]); cam = bpy.data.objects.new(c["name"], cd); sc.collection.objects.link(cam)
        cd.sensor_fit = "VERTICAL"; cd.angle_y = math.radians(c["vfov"])
        if "shift" in c: cd.shift_x, cd.shift_y = c["shift"]
        cam.location = to_b(c["pos"])
        d = to_b(c["look_at"]) - cam.location
        cam.rotation_mode = "QUATERNION"; cam.rotation_quaternion = d.to_track_quat("-Z", "Y")
        if "roll" in c: cam.rotation_mode = "XYZ"; cam.rotation_euler.rotate_axis("Z", math.radians(c["roll"]))
        sc.camera = cam; sc.render.filepath = str(outdir / (c["name"] + ".png"))
        bpy.ops.render.render(write_still=True)
    print("hifi_exterior: rendered", len(cams))
else:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=str(OUT), export_format="GLB", use_selection=False, export_apply=True, export_tangents=True)   # tangents: HDRP normal maps + parallax on the UVs
    print("hifi_exterior: wrote", OUT, sum(len(p["faces"]) for p in parts.values()), "faces")
