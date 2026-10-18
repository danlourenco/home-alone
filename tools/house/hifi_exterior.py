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
       "EX_Roof": ((0.11, 0.095, 0.09), 0.9), "EX_Glass": ((0.10, 0.12, 0.14), 0.05), "EX_Shade": ((0.86, 0.82, 0.70), 0.9),
       "EX_Stone": ((0.78, 0.74, 0.66), 0.8), "EX_Gutter": ((0.88, 0.88, 0.86), 0.4), "EX_Pot": ((0.55, 0.28, 0.18), 0.8),
       "EX_DoorBlack": ((0.025, 0.03, 0.03), 0.35), "EX_Brass": ((0.75, 0.56, 0.25), 0.3), "EX_Wreath": ((0.08, 0.20, 0.08), 0.9),
       "EX_Bow": ((0.55, 0.04, 0.04), 0.6), "EX_PorchGlass": ((0.55, 0.62, 0.65), 0.05)}

for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob)
coll = bpy.data.collections.new("Exterior"); bpy.context.scene.collection.children.link(coll)
mats = {n: material(n, c, r) for n, (c, r) in COL.items()}
root = bpy.data.objects.new("Exterior_HiFi", None); coll.objects.link(root)
for key, p in parts.items():
    pt = Part(key, p["mat"])
    for f in p["faces"]:
        pt.poly([tuple(v) for v in f])
    if pt.f:
        pt.build(coll, mats).parent = root

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
    bpy.ops.export_scene.gltf(filepath=str(OUT), export_format="GLB", use_selection=False, export_apply=True)
    print("hifi_exterior: wrote", OUT, sum(len(p["faces"]) for p in parts.values()), "faces")
