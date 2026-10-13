import bpy
from mathutils import Vector

SRC = "/Users/dlo/Dev/home-alone/assets/home_alone/online_home_alone/HOME_ALONE_FINAL.glb"
OUT = "/Users/dlo/Dev/home-alone/art/home_alone/online_preview.png"
bpy.ops.import_scene.gltf(filepath=SRC)
meshes = [o for o in bpy.context.scene.objects if o.type == "MESH"]
points = [o.matrix_world @ Vector(corner) for o in meshes for corner in o.bound_box]
lo = Vector((min(p.x for p in points), min(p.y for p in points), min(p.z for p in points)))
hi = Vector((max(p.x for p in points), max(p.y for p in points), max(p.z for p in points)))
center = (lo + hi) * 0.5
size = max(hi - lo)
bpy.ops.object.camera_add(location=center + Vector((size * 1.2, -size * 1.2, size * 0.9)))
camera = bpy.context.object
camera.rotation_euler = (center - camera.location).to_track_quat("-Z", "Y").to_euler()
camera.data.type = "ORTHO"
camera.data.ortho_scale = size * 1.15
bpy.context.scene.camera = camera
bpy.ops.object.light_add(type="AREA", location=center + Vector((0, -size * 0.5, size)))
bpy.context.object.data.energy = 1800
bpy.context.object.data.shape = "DISK"
bpy.context.object.data.size = size * 0.7
bpy.context.object.rotation_euler = (center - bpy.context.object.location).to_track_quat("-Z", "Y").to_euler()
bpy.context.scene.world.color = (0.08, 0.1, 0.13)
bpy.context.scene.render.engine = "BLENDER_EEVEE_NEXT"
bpy.context.scene.render.resolution_x = 1280
bpy.context.scene.render.resolution_y = 900
bpy.context.scene.render.resolution_percentage = 100
bpy.context.scene.render.image_settings.file_format = "PNG"
bpy.context.scene.render.filepath = OUT
bpy.ops.render.render(write_still=True)
print("ONLINE PREVIEW", tuple(round(v, 2) for v in (hi - lo)), "objects", len(meshes))
