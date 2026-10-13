"""Run with Blender --background --python tools/build_house.py (optional -- --render)."""
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "art/home_alone"
ASSET = ROOT / "assets/home_alone"
H = 3.4  # Estimated floor spacing in meters; tune against better references.
WALL = 0.22
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
scene.unit_settings.system = "METRIC"
scene.unit_settings.scale_length = 1
groups = {}
name_counts = {}
for name in ("Ground", "Upper", "Attic", "Roof", "Details", "Site", "Collision", "Presentation"):
    groups[name] = bpy.data.collections.new(name)
    scene.collection.children.link(groups[name])


def material(name, color):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = (*color, 1)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = 0.85
    return mat


def image_material(name, color_path, normal_path=None, rough_path=None, scale=(3.0, 3.0, 3.0), roughness=0.55):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    for node in list(nodes):
        nodes.remove(node)
    out = nodes.new("ShaderNodeOutputMaterial")
    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value = roughness
    texcoord = nodes.new("ShaderNodeTexCoord")
    mapping = nodes.new("ShaderNodeMapping")
    mapping.inputs["Scale"].default_value = scale
    color = nodes.new("ShaderNodeTexImage")
    color.image = bpy.data.images.load(str(color_path), check_existing=True)
    links.new(texcoord.outputs["Generated"], mapping.inputs["Vector"])
    links.new(mapping.outputs["Vector"], color.inputs["Vector"])
    links.new(color.outputs["Color"], bsdf.inputs["Base Color"])
    if normal_path:
        normal = nodes.new("ShaderNodeTexImage")
        normal.image = bpy.data.images.load(str(normal_path), check_existing=True)
        normal.image.colorspace_settings.name = "Non-Color"
        bump = nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = 0.28
        links.new(mapping.outputs["Vector"], normal.inputs["Vector"])
        links.new(normal.outputs["Color"], bump.inputs["Height"])
        links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat


brick = material("Brick | muted oxblood", (0.31, 0.085, 0.055))
cream = material("Trim | ivory", (0.82, 0.76, 0.60))
slate = material("Roof | charcoal", (0.065, 0.08, 0.075))
green = material("Shutters | forest green", (0.035, 0.085, 0.063))
plaster = material("Walls | warm plaster", (0.64, 0.54, 0.37))
wood = material("Floors | oak", (0.29, 0.15, 0.065))
red = material("Carpet | cranberry", (0.30, 0.025, 0.038))
glass = material("Windows | blue gray placeholder", (0.22, 0.34, 0.38))
snow = material("Site | snow", (0.78, 0.84, 0.85))
stone = material("Paths | limestone", (0.33, 0.35, 0.33))
wallpaper = image_material("Foyer wallpaper | floral damask", ART / "textures/foyer_wallpaper.png", scale=(2.2, 2.2, 2.2), roughness=0.78)
oak_floor = image_material("Interior oak | photographed", ART / "textures/wood_floor_diff.jpg", ART / "textures/wood_floor_normal.jpg", ART / "textures/wood_floor_rough.jpg", scale=(2.4, 2.4, 2.4), roughness=0.42)
dark_wood = material("Kitchen cabinetry | dark cherry", (0.105, 0.028, 0.018))
tile_green = material("Kitchen tile | deep green ceramic", (0.025, 0.095, 0.075))
tile_grout = material("Kitchen grout | warm ivory", (0.72, 0.65, 0.48))
metal = material("Kitchen metal | brushed nickel", (0.34, 0.37, 0.36))
for mat in (dark_wood, tile_green, metal):
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Roughness"].default_value = 0.34 if mat is metal else 0.48
    noise = mat.node_tree.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 8.0 if mat is dark_wood else 18.0
    noise.inputs["Detail"].default_value = 3.0
    bump = mat.node_tree.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.08 if mat is dark_wood else 0.035
    mat.node_tree.links.new(noise.outputs["Fac"], bump.inputs["Height"])
    mat.node_tree.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])


def assign(obj, name, mat, group, collision=False):
    name_counts[name] = name_counts.get(name, 0) + 1
    unique = name if name_counts[name] == 1 else name + "_%03d" % name_counts[name]
    obj.name = unique + ("-col" if collision else "")
    if obj.type == "MESH":
        obj.data.name = obj.name
        obj.data.materials.append(mat)
    for collection in list(obj.users_collection):
        collection.objects.unlink(obj)
    groups[group].objects.link(obj)
    return obj


def box(name, center, size, mat=plaster, group="Ground", collision=True):
    assert min(size) > 0, (name, size)
    bpy.ops.mesh.primitive_cube_add(size=1, location=center)
    obj = bpy.context.object
    obj.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return assign(obj, name, mat, group, collision)


def mesh(name, vertices, faces, mat, group, collision=True):
    data = bpy.data.meshes.new(name)
    data.from_pydata(vertices, [], faces)
    data.update()
    obj = bpy.data.objects.new(name, data)
    groups[group].objects.link(obj)
    return assign(obj, name, mat, group, collision)


def wall(name, axis, fixed, start, end, z=0, height=H, openings=(), mat=plaster, group="Ground"):
    """Openings are (center, width, sill, height), cut as actual gaps in wall segments."""
    def segment(a, b, bottom, top):
        if b - a < 0.001 or top - bottom < 0.001:
            return
        center = [(a + b) / 2, fixed, z + (bottom + top) / 2]
        size = [b - a, WALL, top - bottom]
        if axis == "Y":
            center[0], center[1] = center[1], center[0]
            size[0], size[1] = size[1], size[0]
        box(name, center, size, mat, group)
    cursor = start
    for center, width, sill, opening_height in sorted(openings):
        a, b = center - width / 2, center + width / 2
        assert start <= a < b <= end and a >= cursor and sill + opening_height <= height
        segment(cursor, a, 0, height)
        segment(a, b, 0, sill)
        segment(a, b, sill + opening_height, height)
        cursor = b
    segment(cursor, end, 0, height)


def floor(name, x0, x1, y0, y1, z, group):
    return box(name, ((x0+x1)/2, (y0+y1)/2, z-0.12), (x1-x0, y1-y0, 0.24), wood, group)


def stairs(name, x, y, z, direction, group):
    width, run, count = 1.8, 5.6, 20
    for i in range(count):
        rise = H * (i + 1) / count
        box(name + "_Tread", (x, y + direction*(i+0.5)*run/count, z+rise/2),
            (width, run/count, rise), wood, group, False)
        if name == "MainStair":
            box(name + "_Runner", (x, y + direction*(i+0.5)*run/count, z+rise+0.025),
                (0.95, run/count*0.72, 0.035), red, group, False)
    # Smooth collision avoids requiring a stair-stepping player controller.
    vertices = [(x+dx, y+direction*dy, z+dz) for dx in (-width/2, width/2)
                for dy, dz in ((0, 0), (run, 0), (run, H))]
    ramp = mesh(name + "-colonly", vertices,
                [(0, 2, 1), (3, 4, 5), (0, 1, 4, 3), (1, 2, 5, 4), (2, 0, 3, 5)],
                wood, "Collision", False)
    # Mirror reverses winding; recalculate to keep collision normals outward.
    bpy.context.view_layer.objects.active = ramp
    bpy.ops.object.select_all(action="DESELECT")
    ramp.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.normals_make_consistent(inside=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    ramp.hide_render = True
    ramp.display_type = "WIRE"
    for side in (-1, 1):
        rail = box(name + "_Rail", (x+side*0.95, y+direction*run/2, z+H/2+0.9),
                   (0.07, math.hypot(run, H), 0.09), cream, group, False)
        rail.rotation_euler.x = direction * math.atan2(H, run)
        for i in range(11):
            box(name + "_Baluster", (x+side*0.95, y+direction*i*run/10, z+i*H/10+0.45),
                (0.055, 0.055, 0.9), cream, group, False)


# Main volume: front is Blender -Y (Godot +Z). All room dimensions are estimates.
floor("MainFloor", -8, 8, 0, 10, 0, "Ground")
for name, x0, x1, y0, y1 in (("FamilyWing", -12, -8, 1, 9),
                             ("Sunroom", 8, 12, 1, 9), ("Kitchen", 2.2, 12, 10, 18)):
    floor(name, x0, x1, y0, y1, 0, "Ground")
    front_start = 8 if name == "Kitchen" else x0
    wall(name+"_Front", "X", y0, front_start, x1, openings=[((front_start+x1)/2, 1.8, 0.8, 1.8)], mat=brick)
    wall(name+"_Rear", "X", y1, x0, x1, openings=[((x0+x1)/2, 1.8, 0 if name == "Kitchen" else 0.8, 2.4 if name == "Kitchen" else 1.8)], mat=brick)
    outer_x = x0 if name == "FamilyWing" else x1
    wall(name+"_Side", "Y", outer_x, y0, y1, openings=[((y0+y1)/2, 1.8, 0.8, 1.8)], mat=brick)
    if name == "Kitchen":
        wall("Kitchen_Left", "Y", x0, y0, y1, mat=brick)
    ceiling = floor(name+"_Ceiling", x0, x1, y0, y1, H, "Roof")
    ceiling.data.materials[0] = slate

for z, group in ((0, "Ground"), (H, "Upper")):
    front = [(x, 1.5, 0.8, 1.9) for x in (-6, -3.6, 3.6, 6)]
    front += [(0, 1.8 if z == 0 else 1.5, 0 if z == 0 else 0.8, 2.5 if z == 0 else 1.9)]
    wall("Facade", "X", 0, -8, 8, z, openings=front, mat=brick, group=group)
    wall("Rear", "X", 10, -8, 8, z, openings=[(-5, 1.5, 0.8, 1.9), (5, 1.8, 0, 2.5)] if z == 0 else [(-5,1.5,0.8,1.9),(5,1.5,0.8,1.9)], mat=brick, group=group)
    for x in (-8, 8):
        wall("Side", "Y", x, 0, 10, z, openings=[(5, 1.8, 0 if z == 0 else 0.8, 2.5 if z == 0 else 1.9)], mat=brick, group=group)
    for x in (-2.2, 2.2):
        wall("HallPartition", "Y", x, 0, 10, z, openings=[(1.7,1.8,0,2.5),(9,1.6,0,2.5)], group=group)
    if z == H:
        for a, b in ((-8, -2.2), (2.2, 8)):
            wall("BedroomPartition", "X", 5, a, b, z, openings=[((a+b)/2,1.6,0,2.5)], group=group)

# Upper slabs leave the entire main flight open. Upper hall also has a side passage.
for group, z, hole_x0, hole_x1 in (("Upper", H, -2.1, 0), ("Attic", 2*H, 0, 2.1)):
    floor("Floor_Left", -8, hole_x0, 0, 10, z, group)
    floor("Floor_Right", hole_x1, 8, 0, 10, z, group)
    floor("Floor_FrontLanding", hole_x0, hole_x1, 0, 2.8, z, group)
    floor("Floor_RearLanding", hole_x0, hole_x1, 8.4, 10, z, group)
stairs("MainStair", -1.05, 2.8, 0, 1, "Ground")
stairs("AtticStair", 1.05, 8.4, H, -1, "Upper")

# Blocking guards prevent walking sideways into each stairwell.
box("MainStairwellGuard", (-0.05, 5.6, H+0.5), (0.10,5.6,1), cream, "Upper")
box("AtticStairwellGuard", (0.05, 5.6, 2*H+0.5), (0.10,5.6,1), cream, "Attic")

# Low attic walls and a hollow hip roof leave usable headroom beneath the ridge.
for fixed in (0, 10):
    wall("AtticKneeWall", "X", fixed, -8, 8, 2*H, 0.9, mat=brick, group="Attic")
for fixed in (-8, 8):
    wall("AtticKneeWall", "Y", fixed, 0, 10, 2*H, 0.9, mat=brick, group="Attic")
roof = mesh("HipRoof", [(-8.5,-0.5,7.7),(8.5,-0.5,7.7),(8.5,10.5,7.7),(-8.5,10.5,7.7),
                        (-4,5,10.8),(4,5,10.8)],
            [(0,1,5,4),(1,2,5),(2,3,4,5),(3,0,4)], slate, "Roof")
solid = roof.modifiers.new("Roof thickness", "SOLIDIFY")
solid.thickness = 0.15
for y in (-0.12, 10.12):
    box("Cornice", (0,y,7.6), (16.7,0.35,0.24), cream, "Roof", False)
for x in (-8.12, 8.12):
    box("Cornice", (x,5,7.6), (0.35,10.3,0.24), cream, "Roof", False)
for x in (-6.7, 6.7):
    box("Chimney", (x,6.7,9.2), (0.9,1.2,3.1), brick, "Roof")
    box("ChimneyCap", (x,6.7,10.8), (1.05,1.35,0.16), stone, "Roof", False)
for x in (-3.8, 3.8):
    box("Dormer", (x,1.65,8.9), (1.7,1.3,1.8), cream, "Roof", False)
    box("DormerWindow", (x,0.98,8.85), (1.1,0.06,1.35), glass, "Roof", False)
    mesh("DormerPediment", [(x-1,0.85,9.75),(x+1,0.85,9.75),(x,0.85,10.45),
                            (x-1,2.5,9.75),(x+1,2.5,9.75),(x,2.5,10.45)],
         [(0,2,1),(3,4,5),(0,3,5,2),(1,2,5,4),(0,1,4,3)], slate, "Roof", False)
    box("DormerMullion", (x,0.92,8.85), (0.06,0.07,1.4), cream, "Roof", False)


def front_window(x, y, bottom, width=1.5, height=1.9, group="Details"):
    box("WindowPane", (x,y,bottom+height/2), (width,0.045,height), glass, group, False)
    for dx in (-width/2, 0, width/2):
        box("WindowFrame", (x+dx,y-0.06,bottom+height/2), (0.07,0.12,height+0.12), cream, group, False)
    for dz in (0, height/3, 2*height/3, height):
        box("WindowFrame", (x,y-0.06,bottom+dz), (width+0.14,0.12,0.065), cream, group, False)
    for side in (-1, 1):
        box("Shutter", (x+side*(width/2+0.29),y-0.09,bottom+height/2), (0.46,0.09,height), green, group, False)
    box("WindowSill", (x,y-0.10,bottom-0.04), (width+0.28,0.32,0.12), cream, group, False)


for z in (0, H):
    for x in (-6,-3.6,3.6,6):
        front_window(x,-0.13,z+0.8)
front_window(0,-0.13,H+0.8)
for x in (-10,10):
    front_window(x,0.87,0.8,1.8,1.8)

# Open front entrance: columns and arched canopy, with no blocking door leaf.
for x in (-1.15,1.15):
    box("EntryPilaster", (x,-0.35,1.35), (0.24,0.35,2.7), cream, "Details", False)
    box("EntryCapital", (x,-0.35,2.7), (0.42,0.5,0.18), cream, "Details", False)
for i in range(20):
    a0, a1 = math.pi*i/20, math.pi*(i+1)/20
    verts = [(r*math.cos(a),y,2.65+0.38*r*math.sin(a))
             for y in (-0.7,0.12) for r,a in ((1.5,a0),(1.5,a1),(1.28,a1),(1.28,a0))]
    mesh("EntryArch", verts, [(0,1,2,3),(4,7,6,5),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)], cream, "Details", False)

# Sparse furniture establishes room identity and leaves circulation routes clear.
box("FoyerRunner", (1.0,4.4,0.015), (1.5,6.8,0.025), red, "Ground", False)
box("DiningTable", (5.1,5,0.8), (2.0,3.2,0.16), wood)
for x in (4.4,5.8):
    for y in (3.7,6.3):
        box("TableLeg", (x,y,0.38), (0.12,0.12,0.76), wood)
box("Sofa", (-4.7,5,0.45), (2.7,1.0,0.9), green)
box("SofaBack", (-4.7,5.45,0.9), (2.7,0.22,0.85), green)
box("CoffeeTable", (-4.7,3.2,0.32), (1.6,0.8,0.64), wood)
box("FamilyRoomHearth", (-11.65,6,0.7), (0.5,2,1.4), brick)
box("KitchenIsland", (7.1,14,0.48), (1.4,3.8,0.96), green)
box("KitchenCounter", (10.9,14.5,0.48), (0.85,5.5,0.96), cream)
box("KitchenWorktop", (7.1,14,1.0), (1.55,3.95,0.09), cream)
box("KitchenTileFloor", (7.1,14,0.015), (9.8,8.0,0.035), tile_green, "Ground", False)
box("KitchenTileInset", (7.1,14,0.038), (7.2,5.2,0.012), tile_grout, "Ground", False)
for x in (3.1, 5.0, 9.2, 11.0):
    box("KitchenLowerCabinet", (x,17.65,0.9), (1.65,0.78,1.8), dark_wood, "Ground", False)
    box("KitchenCabinetFace", (x,17.22,0.9), (1.42,0.035,1.48), dark_wood, "Ground", False)
    box("KitchenHandle", (x,17.18,1.0), (0.36,0.05,0.05), metal, "Details", False)
for x in (3.3, 5.1, 9.0, 10.8):
    box("KitchenUpperCabinet", (x,17.65,2.55), (1.55,0.72,1.3), dark_wood, "Ground", False)
    box("KitchenUpperHandle", (x,17.25,2.5), (0.3,0.05,0.05), metal, "Details", False)
box("KitchenUpperCrown", (7.1,17.24,3.22), (8.1,0.16,0.14), dark_wood, "Details", False)
box("KitchenBacksplash", (7.1,17.18,1.65), (7.8,0.045,1.15), tile_green, "Ground", False)
for x in (3.4, 5.0, 9.1, 10.7):
    box("BacksplashGrout", (x,17.145,1.65), (0.025,0.02,1.1), tile_grout, "Details", False)
box("KitchenRange", (7.1,17.55,0.82), (1.8,0.78,1.65), metal, "Ground", False)
box("RangeBlackFace", (7.1,17.12,0.9), (1.45,0.04,1.45), dark_wood, "Details", False)
for x in (6.7, 7.5):
    box("RangeKnob", (x,17.08,1.55), (0.11,0.04,0.11), metal, "Details", False)
box("KitchenSink", (10.1,14.0,1.06), (1.0,1.25,0.06), metal, "Details", False)
box("KitchenFaucet", (10.1,13.4,1.35), (0.08,0.08,0.6), metal, "Details", False)

# Finish details for the foyer and the period kitchen set.
for x in (-2.08, 2.08):
    box("FoyerBaseboard", (x,5,0.13), (0.12,10,0.26), cream, "Details", False)
    box("FoyerCrownMoulding", (x,5,3.23), (0.16,10,0.24), cream, "Details", False)
for y in (0.18, 9.82):
    box("FoyerBaseboard", (0,y,0.13), (16,0.12,0.26), cream, "Details", False)
    box("FoyerCrownMoulding", (0,y,3.23), (16,0.16,0.24), cream, "Details", False)
for i, y in enumerate((3.1, 4.0, 4.9, 5.8, 6.7)):
    box("FoyerPictureFrame", (-2.02,y,1.95), (0.06,0.58,0.78), dark_wood, "Details", False)
    box("FoyerPictureMat", (-1.975,y,1.95), (0.025,0.46,0.64), cream, "Details", False)
    box("FoyerPictureArt", (-1.95,y,1.95), (0.018,0.36,0.54), red if i % 2 else green, "Details", False)
for y in (3.1, 4.0, 4.9, 5.8, 6.7):
    box("FoyerPictureFrame", (2.02,y,1.95), (0.06,0.58,0.78), dark_wood, "Details", False)
    box("FoyerPictureMat", (1.975,y,1.95), (0.025,0.46,0.64), cream, "Details", False)
    box("FoyerPictureArt", (1.95,y,1.95), (0.018,0.36,0.54), green, "Details", False)
box("FoyerPendantStem", (0,5,2.75), (0.055,0.055,0.8), metal, "Details", False)
bpy.ops.mesh.primitive_uv_sphere_add(segments=24, ring_count=12, radius=0.18, location=(0,5,2.3))
assign(bpy.context.object, "FoyerPendantShade", cream, "Details", False)
bpy.ops.object.light_add(type="POINT", location=(0,5,2.25))
pendant_light = assign(bpy.context.object, "FoyerPendantLight", None, "Presentation")
pendant_light.data.energy = 55
pendant_light.data.color = (1.0, 0.65, 0.35)
pendant_light.data.shadow_soft_size = 0.45
box("FoyerPlantPot", (2.8,8.8,0.38), (0.75,0.75,0.7), dark_wood, "Details", False)
for i in range(9):
    angle = 2*math.pi*i/9
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=2, radius=0.42,
        location=(2.8+0.55*math.cos(angle), 8.8+0.55*math.sin(angle), 1.7+0.12*(i%3)))
    assign(bpy.context.object, "FoyerPlantLeaf", green, "Details", False)

# Kitchen window treatment, period appliances, and small counter props.
box("KitchenWindowCurtainL", (3.2,17.05,2.0), (0.55,0.08,2.1), red, "Details", False)
box("KitchenWindowCurtainR", (11.0,17.05,2.0), (0.55,0.08,2.1), red, "Details", False)
box("KitchenFridge", (3.0,12.3,1.25), (1.45,1.3,2.5), metal, "Ground", False)
box("KitchenFridgeDoor", (2.7,11.62,1.25), (0.9,0.04,2.2), cream, "Details", False)
box("KitchenMicrowave", (4.2,17.05,2.05), (0.95,0.2,0.62), metal, "Details", False)
for x, y, z in ((5.9,13.4,1.08),(6.5,13.2,1.1),(8.0,14.7,1.08)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=0.13, location=(x,y,z))
    assign(bpy.context.object, "KitchenCounterProp", red, "Details", False)

# Period kitchen joinery details: toe-kicks, continuous worktops, inset sink,
# range hood, and island end panels make the room read as built cabinetry.
for x in (3.1, 5.0, 9.2, 11.0):
    box("KitchenToeKick", (x,17.18,0.18), (1.5,0.12,0.28), dark_wood, "Details", False)
    box("KitchenCountertop", (x,17.60,1.87), (1.76,0.92,0.12), cream, "Details", False)
box("KitchenSinkBasin", (10.1,14.0,1.10), (0.78,0.92,0.12), dark_wood, "Details", False)
box("KitchenSinkLip", (10.1,14.0,1.17), (1.10,1.25,0.06), metal, "Details", False)
box("RangeHood", (7.1,16.95,2.75), (2.0,0.55,0.35), metal, "Details", False)
box("RangeHoodTrim", (7.1,17.20,2.55), (1.7,0.08,0.10), dark_wood, "Details", False)
box("KitchenIslandEndPanel", (6.45,14.0,0.52), (0.08,3.45,0.92), dark_wood, "Details", False)
box("KitchenIslandEndPanel", (7.75,14.0,0.52), (0.08,3.45,0.92), dark_wood, "Details", False)
for y in (12.45,15.55):
    box("KitchenIslandToeKick", (7.1,y,0.18), (1.25,0.12,0.28), dark_wood, "Details", False)

for obj in list(groups["Ground"].objects) + list(groups["Details"].objects):
    if obj.type == "MESH" and "Kitchen" in obj.name:
        bevel = obj.modifiers.new("Soft manufactured edges", "BEVEL")
        bevel.width = 0.045
        bevel.segments = 3

# Give the foyer walls the film-set damask; the runner remains cranberry.
for obj in list(groups["Ground"].objects):
    if obj.type == "MESH" and "HallPartition" in obj.name:
        obj.data.materials.clear()
        obj.data.materials.append(wallpaper)
for obj in list(groups["Ground"].objects):
    if obj.type == "MESH" and obj.name.startswith("MainFloor"):
        obj.data.materials.clear()
        obj.data.materials.append(oak_floor)
for x in (-5,5):
    for y in (3,7):
        box("BedroomBed", (x,y,H+0.3), (2,2.2,0.6), red, "Upper")
        box("BedPillow", (x,y+0.65,H+0.67), (1.6,0.55,0.18), cream, "Upper", False)

box("SnowGround", (0,6,-0.38), (44,44,0.3), snow, "Site")
box("FrontWalk", (0,-7,-0.12), (2.5,14,0.24), stone, "Site")
box("Driveway", (15,4,-0.18), (5,35,0.12), stone, "Site")
box("RearLanding", (7.1,19, -0.12), (3,2,0.24), stone, "Site")
for x in (-9,-6,-3,3,6,9):
    box("Hedge", (x,-1.4,0.3), (1.8,0.8,0.9), green, "Site")

# Export only model geometry. Collision-only ramps remain in the GLB for Godot.
bpy.ops.object.select_all(action="DESELECT")
for obj in scene.objects:
    obj.select_set(obj.type == "MESH")
bpy.ops.export_scene.gltf(filepath=str(ASSET / "home_alone_blockout.glb"), export_format="GLB",
                          use_selection=True, export_apply=True, export_animations=False,
                          export_extras=True)

world = bpy.data.worlds.new("Winter daylight")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.5,0.65,0.8,1)
world.node_tree.nodes["Background"].inputs[1].default_value = 0.4
bpy.ops.object.light_add(type="SUN", location=(0,-10,20))
sun = assign(bpy.context.object, "Sun", None, "Presentation")
sun.rotation_euler = (math.radians(28),math.radians(-25),math.radians(-30))
sun.data.energy = 2.4
sun.data.angle = math.radians(15)
bpy.ops.object.camera_add(location=(28,-38,25))
camera = assign(bpy.context.object, "ExteriorCamera", None, "Presentation")
camera.rotation_euler = (Vector((0,5,3))-camera.location).to_track_quat("-Z","Y").to_euler()
camera.data.type = "ORTHO"
camera.data.ortho_scale = 39
scene.camera = camera
scene.render.engine = "CYCLES"
scene.cycles.samples = 24
scene.render.resolution_x = 1400
scene.render.resolution_y = 1000
scene.render.resolution_percentage = 100
scene.render.image_settings.file_format = "PNG"
scene.view_settings.view_transform = "AgX"
scene.render.filepath = str(ART / "exterior.png")
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type == "VIEW_3D":
            area.spaces.active.region_3d.view_distance = 38
            area.spaces.active.region_3d.view_location = (0,5,3)
            area.spaces.active.region_3d.view_rotation = camera.rotation_euler.to_quaternion()
            area.spaces.active.clip_end = 300
            area.spaces.active.shading.type = "MATERIAL"
bpy.ops.object.select_all(action="DESELECT")
scene["Reference"] = "Movie-inspired blockout; estimated dimensions, simplified upper floor. See README."
scene["Scale"] = "Meters; floor elevations 0 / 3.4 / 6.8. Front faces -Y."
bpy.context.preferences.filepaths.save_version = 0
bpy.ops.wm.save_as_mainfile(filepath=str(ART / "home_alone_blockout.blend"))
if "--render" in sys.argv:
    bpy.ops.render.render(write_still=True)
    for group in ("Upper", "Attic", "Roof"):
        groups[group].hide_render = True
    # Hide window details along with upper floors to expose the ground plan.
    groups["Details"].hide_render = True
    camera.location = (24,-30,40)
    camera.rotation_euler = (Vector((0,7,0))-camera.location).to_track_quat("-Z","Y").to_euler()
    scene.render.filepath = str(ART / "ground_floor.png")
    bpy.ops.render.render(write_still=True)
    # Close-up of the foyer materials and entry details.
    camera.data.type = "PERSP"
    camera.data.lens = 32
    camera.location = (4.0,-0.8,1.8)
    camera.rotation_euler = (Vector((-0.8,5.2,1.65))-camera.location).to_track_quat("-Z","Y").to_euler()
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    scene.cycles.samples = 48
    groups["Details"].hide_render = False
    scene.render.filepath = str(ART / "foyer_detail.png")
    bpy.ops.render.render(write_still=True)
    # Kitchen close-up for material and prop review.
    camera.data.lens = 30
    camera.location = (10.8,12.1,2.25)
    camera.rotation_euler = (Vector((7.2,16.8,1.45))-camera.location).to_track_quat("-Z","Y").to_euler()
    scene.render.filepath = str(ART / "kitchen_detail.png")
    bpy.ops.render.render(write_still=True)

ART.mkdir(parents=True, exist_ok=True)
ASSET.mkdir(parents=True, exist_ok=True)
assert len(groups["Collision"].objects) == 2
assert len([o for o in scene.objects if o.name.endswith("-col")]) > 60
print("BLOCKOUT STRUCTURE OK", len(scene.objects), "objects")
