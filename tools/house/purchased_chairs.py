"""The user's CGTrader "CHIPPENDALE CHAIR" (bought Oct 20 2026, $25, royalty-free: files gitignored) as two GLBs in
Assets/Purchased/Chairs: Chippendale_Dining.glb (the dining room's eight, tapestry slip seat, film 246/252) and Chippendale_Foyer.glb
(the two console side chairs, red seat, film 1616/1690/10673). Same mesh, two seats.

The download (~/Downloads/chippendale-chair: chippendale.blend, a .skp and dae.zip) is a SketchUp export: 116k triangles, one untextured
material, carved ball-and-claw legs and a pierced splat. Step 1 (plain Python): copy the sources into sfm-work/purchased/chairs and write
the 2K maps: the wood is Poly Haven cherry_veneer (CC0, already cached) recoloured to the film's mahogany, the dining seat a tapestry
generated in the film's gold-tan, the foyer seat the house's foyer red (SpecGreybox.FoyerProps HiFi_FoyerSeat, film 1690). Step 2
(Blender, this file again): bake the SketchUp groups into a Wood and a Seat mesh, weld, decimate, scale x0.88 uniform (native seat top
0.52 / back 1.13 m -> 0.457 / 0.995: a real Chippendale side chair is ~0.46 / ~0.97-1.0), smart-UV, export with the front at +Z (glTF),
origin at the floor centre.
usage: uv run --with numpy --with pillow python -I tools/house/purchased_chairs.py [SOURCE_DIR]
"""
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "sfm-work/purchased/chairs"
OUT = ROOT / "unity/HomeAlone/Assets/Purchased/Chairs"
BLENDER = "/Applications/Blender.app/Contents/MacOS/Blender"
SIZE = 2048
SCALE = 0.88                       # native seat top 0.52 m, back top 1.131 m
SEAT_OBJECTS = ("group_1", "D_6_0_mm")   # the slip seat (the rest is wood)
DECIMATE = 0.25
WOOD_SRGB = (88, 34, 16)           # film 246 crest rail #351308 (hue), at the house mahogany's brightness (hifi_living_props.py 0.10 linear)
FOYER_SEAT_LINEAR = (0.42, 0.03, 0.045)   # HiFi_FoyerSeat (film 1690 seat #4d0010 hue)
TAPESTRY = ((126, 84, 38), (74, 50, 24), (150, 112, 60))   # film 246 seat highlights #3f2611 under the cloth, x2: gold-tan ground, olive-brown, light motif


def maps():
    import numpy as np
    from PIL import Image
    SRC.mkdir(parents=True, exist_ok=True)
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home() / "Downloads/chippendale-chair"
    for f in ("chippendale.blend", "dae.zip"):
        if not (SRC / f).exists():
            shutil.copy(src / f, SRC / f)
    ph = ROOT / "sfm-work/polyhaven/cherry_veneer"
    a = np.asarray(Image.open(ph / "albedo.jpg").convert("RGB").resize((SIZE, SIZE), Image.LANCZOS)).astype(float) / 255
    lum = a.mean(2); t = np.array(WOOD_SRGB) / 255
    Image.fromarray((np.clip(t[None, None] * (lum / np.median(lum))[..., None], 0, 1) * 255).astype(np.uint8)).save(SRC / "Wood_Base.png")
    Image.open(ph / "normal.jpg").convert("RGB").resize((SIZE, SIZE), Image.LANCZOS).save(SRC / "Wood_Normal.png")
    N = 1024; v, u = np.mgrid[0:N, 0:N] / N                       # a small two-tone damask repeat (tileable), 8 motifs a side
    cu, cv = (u * 8) % 1 - 0.5, (v * 8) % 1 - 0.5; r, ang = np.hypot(cu, cv), np.arctan2(cv, cu)
    motif = r < 0.32 * (0.6 + 0.4 * np.abs(np.cos(2 * ang)))
    vine = np.abs(np.sin((u + 0.3 * np.sin(v * 16 * np.pi)) * 16 * np.pi)) < 0.12
    g, o, li = (np.array(c) for c in TAPESTRY)
    img = np.where(motif[..., None], li, np.where(vine[..., None], o, g)) * (0.92 + 0.08 * np.random.default_rng(1).random((N, N, 1)))
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(SRC / "Seat_Tapestry.png")
    red = np.array([(c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055) * 255 for c in FOYER_SEAT_LINEAR])   # linear -> sRGB
    Image.fromarray(np.clip(red * (0.94 + 0.06 * np.random.default_rng(2).random((256, 256, 1))), 0, 255).astype(np.uint8)).save(SRC / "Seat_Red.png")   # a map, not a flat colour (the build's Props check wants one)


def blender():
    import bpy
    import bmesh
    bpy.ops.wm.open_mainfile(filepath=str(SRC / "chippendale.blend"))
    dg = bpy.context.evaluated_depsgraph_get()
    parts = {"Wood": bmesh.new(), "Seat": bmesh.new()}
    for o in bpy.data.objects:
        if o.type != "MESH" or not o.material_slots or o.material_slots[0].material is None or o.material_slots[0].material.name != "material":
            continue                                                    # SketchUp edge lines (edge_color000255) carry no faces
        m = o.evaluated_get(dg).to_mesh(); m.transform(o.matrix_world)
        b = parts["Seat" if o.name in SEAT_OBJECTS else "Wood"]
        vs = [b.verts.new(v.co) for v in m.vertices]
        for p in m.polygons:
            try:
                b.faces.new([vs[i] for i in p.vertices])
            except ValueError:
                pass                                                    # a duplicate face in the SketchUp data
        o.evaluated_get(dg).to_mesh_clear()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    lo = [min(v.co[i] for b in parts.values() for v in b.verts) for i in range(3)]
    hi = [max(v.co[i] for b in parts.values() for v in b.verts) for i in range(3)]
    cx, cy = (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2
    objs = {}
    for name, b in parts.items():
        for v in b.verts:
            v.co.x, v.co.y, v.co.z = (v.co.x - cx) * SCALE, (v.co.y - cy) * SCALE, (v.co.z - lo[2]) * SCALE
        bmesh.ops.remove_doubles(b, verts=b.verts, dist=0.0002)
        bmesh.ops.recalc_face_normals(b, faces=b.faces)
        me = bpy.data.meshes.new(name); b.to_mesh(me); ob = bpy.data.objects.new(name, me); bpy.context.scene.collection.objects.link(ob)
        objs[name] = ob
    for name, ob in objs.items():
        bpy.context.view_layer.objects.active = ob
        for q in objs.values():
            q.select_set(q is ob)
        if name == "Wood":
            ob.modifiers.new("dec", "DECIMATE").ratio = DECIMATE
            bpy.ops.object.modifier_apply(modifier="dec")
        bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.select_all(action="SELECT")
        bpy.ops.uv.smart_project(angle_limit=1.15, island_margin=0.003, scale_to_bounds=False)
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.shade_auto_smooth(angle=0.7)

    def mat(name, base=None, normal=None, colour=(1, 1, 1), rough=0.5):
        m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; sh = nt.nodes["Principled BSDF"]
        sh.inputs["Base Color"].default_value = (*colour, 1); sh.inputs["Roughness"].default_value = rough; sh.inputs["Metallic"].default_value = 0
        if base:
            t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(str(base)); nt.links.new(t.outputs["Color"], sh.inputs["Base Color"])
        if normal:
            t = nt.nodes.new("ShaderNodeTexImage"); t.image = bpy.data.images.load(str(normal)); t.image.colorspace_settings.name = "Non-Color"
            nm = nt.nodes.new("ShaderNodeNormalMap"); nt.links.new(t.outputs["Color"], nm.inputs["Color"]); nt.links.new(nm.outputs["Normal"], sh.inputs["Normal"])
        return m
    wood = mat("Chip_Wood", SRC / "Wood_Base.png", SRC / "Wood_Normal.png", rough=0.4)
    seats = {"Dining": mat("Chip_SeatTapestry", SRC / "Seat_Tapestry.png", rough=0.85), "Foyer": mat("Chip_SeatRed", SRC / "Seat_Red.png", rough=0.8)}
    objs["Wood"].data.materials.append(wood)
    OUT.mkdir(parents=True, exist_ok=True)
    tris = {n: sum(len(p.vertices) - 2 for p in o.data.polygons) for n, o in objs.items()}
    for variant, sm in seats.items():
        objs["Seat"].data.materials.clear(); objs["Seat"].data.materials.append(sm)
        for q in objs.values():
            q.select_set(True)
        out = OUT / f"Chippendale_{variant}.glb"
        bpy.ops.export_scene.gltf(filepath=str(out), export_format="GLB", use_selection=True, export_image_format="AUTO")
        print(f"-> {out}")
    b = [min(v.co[i] for o in objs.values() for v in o.data.vertices) for i in range(3)], [max(v.co[i] for o in objs.values() for v in o.data.vertices) for i in range(3)]
    seat_top = max(v.co.z for v in objs["Seat"].data.vertices)
    print(f"tris {tris} total {sum(tris.values())}; size w {b[1][0]-b[0][0]:.3f} d {b[1][1]-b[0][1]:.3f} h {b[1][2]:.3f}; seat top {seat_top:.3f}")
    assert abs(b[1][2] - 1.131 * SCALE) < 0.01 and 0.44 < seat_top < 0.48, "scale check: back ~0.995, seat ~0.46"


if __name__ == "__main__":
    if "bpy" in sys.modules or Path(sys.executable).name.lower().startswith("blender"):
        blender()
    else:
        maps()
        subprocess.run([BLENDER, "-b", "--factory-startup", "-P", __file__], check=True)
