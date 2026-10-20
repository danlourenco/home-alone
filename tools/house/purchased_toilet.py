"""The user's Asset Store toilet (Tobiesen "VR-ready PBR toilet", Oct 20 2026) as a GLB in the GITIGNORED Assets/Purchased/Toilet.

The package is a Unity 2017 export: Unity 6 rejects its prefab and metas (old serialization: new GUIDs, the prefab loses its mesh and
material), so it is rebuilt here instead. Step 1 (plain Python): unpack the FBX and the 8K maps from the .unitypackage (a tar.gz of GUID
folders) into sfm-work/purchased/toilet, maps at 2K, plus an HDRP mask map (R metallic, G AO, B 0, A smoothness). Step 2 (Blender, this
file again): import the FBX, drop the LOD1 meshes, one PBR material (base colour + normal), export Toilet.glb; Toilet_Mask.png beside it is
picked up by StoreProps.HdrpOrConvert as the HDRP mask map. Skipped: the DemoScene, Floor.mat, the LOD-only FBX, the height map.
usage: uv run --with numpy --with pillow python -I tools/house/purchased_toilet.py [PACKAGE]
"""
import shutil
import subprocess
import sys
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "sfm-work/purchased/toilet"
OUT = ROOT / "unity/HomeAlone/Assets/Purchased/Toilet"
BLENDER = "/Applications/Blender.app/Contents/MacOS/Blender"
SIZE = 2048


def unpack(pkg):
    import numpy as np
    from PIL import Image
    Image.MAX_IMAGE_PIXELS = None
    SRC.mkdir(parents=True, exist_ok=True)
    with tarfile.open(pkg, "r:gz") as tf:
        entries = {}
        for m in tf.getmembers():
            if m.isfile() and m.name.count("/") == 1:
                g, leaf = m.name.split("/"); entries.setdefault(g, {})[leaf] = m
        files = {}
        for e in entries.values():
            if "pathname" in e and "asset" in e:
                files[tf.extractfile(e["pathname"]).read().decode().splitlines()[0].split("/")[-1]] = e["asset"]
        (SRC / "ferguson.fbx").write_bytes(tf.extractfile(files["ferguson.FBX"]).read())
        maps = {n: Image.open(tf.extractfile(files[n + ".tga"])).convert("RGBA").resize((SIZE, SIZE), Image.LANCZOS)
                for n in ("Diffuse", "Normal", "AO", "Metallic", "Metallic_smoothness")}
    maps["Diffuse"].convert("RGB").save(SRC / "Toilet_Base.png")
    maps["Normal"].convert("RGB").save(SRC / "Toilet_Normal.png")
    a = lambda n, c: np.asarray(maps[n])[..., c]
    mask = np.dstack([a("Metallic", 0), a("AO", 0), np.zeros((SIZE, SIZE), np.uint8), a("Metallic_smoothness", 3)])
    Image.fromarray(mask, "RGBA").save(SRC / "Toilet_Mask.png")


def blender():
    import bpy
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(SRC / "ferguson.fbx"))
    for o in list(bpy.data.objects):
        if o.type == "MESH" and o.name.endswith("LOD1"):
            bpy.data.objects.remove(o, do_unlink=True)
    mat = bpy.data.materials.new("Toilet"); mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    sh = nodes.get("Principled BSDF")
    base = nodes.new("ShaderNodeTexImage"); base.image = bpy.data.images.load(str(SRC / "Toilet_Base.png"))
    links.new(base.outputs["Color"], sh.inputs["Base Color"])
    nimg = nodes.new("ShaderNodeTexImage"); nimg.image = bpy.data.images.load(str(SRC / "Toilet_Normal.png")); nimg.image.colorspace_settings.name = "Non-Color"
    nm = nodes.new("ShaderNodeNormalMap"); links.new(nimg.outputs["Color"], nm.inputs["Color"]); links.new(nm.outputs["Normal"], sh.inputs["Normal"])
    sh.inputs["Roughness"].default_value = 0.15; sh.inputs["Metallic"].default_value = 0.0   # the mask map carries the real values in HDRP
    n = 0
    for o in bpy.data.objects:
        if o.type == "MESH":
            o.data.materials.clear(); o.data.materials.append(mat); n += 1
    OUT.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=str(OUT / "Toilet.glb"), export_format="GLB", export_image_format="AUTO")
    shutil.copy(SRC / "Toilet_Mask.png", OUT / "Toilet_Mask.png")
    print(f"-> {OUT / 'Toilet.glb'}: {n} meshes (LOD0)")


if __name__ == "__main__":
    if "bpy" in sys.modules or Path(sys.executable).name.lower().startswith("blender"):
        blender()
    else:
        pkg = Path(sys.argv[1] if len(sys.argv) > 1 else Path.home() / "Library/Unity/Asset Store-5.x/Tobiesen/3D ModelsCharacters/VR-ready PBR toilet.unitypackage")
        unpack(pkg)
        subprocess.run([BLENDER, "-b", "--factory-startup", "-P", __file__], check=True)
