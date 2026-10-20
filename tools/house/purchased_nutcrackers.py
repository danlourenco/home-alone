"""Prepare the user's red/green nutcrackers; licensed inputs/outputs stay gitignored.

Put Nutcraker.fbx and the extracted texture/ directory in sfm-work/purchased/nutcrackers/.
Run with Blender -b --factory-startup -P tools/house/purchased_nutcrackers.py.
Unity materials/prefabs are prepared by import_nutcrackers.cs, then placed with props.py.
"""
import json
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "sfm-work/purchased/nutcrackers"
OUT = ROOT / "unity/HomeAlone/Assets/Purchased/Nutcrackers"
HEIGHT = 0.355   # preserve the generated figures' height, including their bases
OUT.mkdir(parents=True, exist_ok=True)


def texture(path, name, noncolor=False):
    image = bpy.data.images.load(str(path), check_existing=False)
    image.colorspace_settings.name = "Non-Color" if noncolor else "sRGB"
    scale = min(1, 2048 / max(image.size))
    if scale < 1:
        image.scale(max(1, round(image.size[0] * scale)), max(1, round(image.size[1] * scale)))
    image.filepath_raw = str(OUT / (name + ".png"))
    image.file_format = "PNG"
    image.save()
    return image


def solid(name, rgba, noncolor=False):
    image = bpy.data.images.new(name, 1, 1, alpha=True)
    image.colorspace_settings.name = "Non-Color" if noncolor else "sRGB"
    image.pixels[:] = rgba
    image.filepath_raw = str(OUT / (name + ".png"))
    image.file_format = "PNG"
    image.save()
    return image


def material(variant, kind, folder, stem=None, hair=None, color=(0.03, 0.03, 0.03), metal=0, rough=0.5):
    name = f"NC_{variant}_{kind}"
    base = texture(folder / (stem + "_BaseColor.png"), name + "_base") if stem else (
        texture(SRC / "texture" / hair, name + "_base") if hair else solid(name + "_base", (*color, 1)))
    normal = texture(folder / (stem + "_Normal.png"), name + "_normal", True) if stem else None
    if stem:
        maps = []
        for suffix in ("Metallic", "Roughness"):
            image = bpy.data.images.load(str(folder / (stem + "_" + suffix + ".png")), check_existing=False)
            image.colorspace_settings.name = "Non-Color"
            image.scale(*base.size)
            pixels = np.empty(image.size[0] * image.size[1] * 4, dtype=np.float32)
            image.pixels.foreach_get(pixels)
            maps.append(pixels.reshape(-1, 4)[:, 0])
        mask = bpy.data.images.new(name + "_mask", *base.size, alpha=True)
        mask.colorspace_settings.name = "Non-Color"
        pixels = np.ones((base.size[0] * base.size[1], 4), dtype=np.float32)
        pixels[:, 0], pixels[:, 3] = maps[0], 1 - maps[1]
        mask.pixels.foreach_set(pixels.ravel())
        mask.filepath_raw = str(OUT / (name + "_mask.png")); mask.file_format = "PNG"; mask.save()
    else:
        mask = solid(name + "_mask", (metal, 1, 1, 1 - rough), True)
    mat = bpy.data.materials.new(name); mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    shader = nodes.get("Principled BSDF")
    image = nodes.new("ShaderNodeTexImage"); image.image = base
    links.new(image.outputs["Color"], shader.inputs["Base Color"])
    shader.inputs["Metallic"].default_value = metal
    shader.inputs["Roughness"].default_value = rough
    if normal:
        image = nodes.new("ShaderNodeTexImage"); image.image = normal
        bump = nodes.new("ShaderNodeNormalMap")
        links.new(image.outputs["Color"], bump.inputs["Color"])
        links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    return mat, {"base": Path(base.filepath_raw).name, "mask": Path(mask.filepath_raw).name,
                 "normal": Path(normal.filepath_raw).name if normal else None, "cutout": bool(hair)}


report = {}
for variant, root_name, directory in (("Green", "Nutcracker", "Green"), ("Red", "nutcraker_2", "red")):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(SRC / "Nutcraker.fbx"))
    root = bpy.data.objects[root_name]
    meshes = [o for o in root.children_recursive if o.type == "MESH"]
    assert meshes
    for obj in meshes:
        obj.data.transform(obj.matrix_world)
        obj.parent = None; obj.matrix_world = Matrix.Identity(4)
        for attribute in list(obj.data.color_attributes):
            obj.data.color_attributes.remove(attribute)
    for obj in list(bpy.data.objects):
        if obj not in meshes:
            bpy.data.objects.remove(obj, do_unlink=True)
    vertices = np.array([tuple(v.co) for obj in meshes for v in obj.data.vertices])
    lo, hi = vertices.min(0), vertices.max(0)
    origin = np.array([(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, lo[2]])
    scale = HEIGHT / (hi[2] - lo[2])
    transform = Matrix.Scale(float(scale), 4) @ Matrix.Translation(tuple(-origin))
    folder = SRC / "texture" / directory
    materials = {
        "Body": material(variant, "Body", folder, "body_and_head"),
        "Extremities": material(variant, "Extremities", folder, "weapon_and_extremities"),
        "Hair": material(variant, "Hair", folder, hair="hair .png"),
        "Beard": material(variant, "Beard", folder, hair="hair06.png"),
        "Gold": material(variant, "Gold", folder, color=(0.65, 0.42, 0.10), metal=0.65, rough=0.32),
        "Belt": material(variant, "Belt", folder, color=(0.55, 0.02, 0.025)),
        "Base": material(variant, "Base", folder),
    }
    for obj in meshes:
        obj.data.transform(transform); obj.data.update()
        for slot in obj.material_slots:
            name = slot.material.name.lower()
            key = "Body" if name in ("g_body_and_weapon", "r_body_and_head") else (
                "Extremities" if name in ("g_weapon_and_extremities", "r_extremities") else
                {"hair": "Hair", "beard": "Beard", "gold": "Gold", "red": "Belt", "base": "Base"}[name])
            slot.material = materials[key][0]
    triangles = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in meshes)
    assert triangles < 150000, triangles
    vertices = np.array([tuple(v.co) for o in meshes for v in o.data.vertices])
    assert abs(vertices[:, 2].min()) < 1e-6 and abs(vertices[:, 2].max() - HEIGHT) < 1e-6
    base = next(o for o in meshes if o.name.startswith("base"))
    base_vertices = np.array([tuple(v.co) for v in base.data.vertices])
    base_centre = (base_vertices.min(0) + base_vertices.max(0)) / 2
    bpy.ops.export_scene.gltf(filepath=str(OUT / (variant + ".glb")), export_format="GLB", export_yup=True, export_apply=True)
    report[variant] = {"triangles": triangles, "size": (vertices.max(0) - vertices.min(0)).tolist(),
                       "base_offset": [-float(base_centre[0]), -float(base_centre[1])],
                       "materials": {mat.name: data for mat, data in materials.values()}}
(OUT / "import.json").write_text(json.dumps(report, indent=2) + "\n")
print("Nutcrackers:", json.dumps({k: {a: v[a] for a in ("triangles", "size")} for k, v in report.items()}))
