"""Marina Coates reference interior. Blender --background --python this_file -- --render."""
import math
import json
import sys
from pathlib import Path
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'art/home_alone/marina'
OUT = ROOT / 'assets/home_alone/marina'
ART.mkdir(parents=True, exist_ok=True)
OUT.mkdir(parents=True, exist_ok=True)
H = 3.35
KITCHEN_AREA = 477 * 0.09290304
BACK = 10 + KITCHEN_AREA / 5.2
BREAKFAST_BACK = 14.2
FOYER_BREAKFAST_DOOR = 9.55
SERVICE_START = 10.4


def prepare_blender_workspace():
    """Keep the saved source portable and ready for editing or Walk Navigation."""
    bpy.ops.object.select_all(action='DESELECT')
    meshes = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    for o in meshes:o.select_set(True)
    bpy.context.view_layer.objects.active = meshes[0]
    bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')
    bpy.ops.object.select_all(action='DESELECT')
    bpy.context.view_layer.objects.active = None
    bpy.ops.file.pack_all()
    presentation = bpy.data.collections.get('Cameras and lights') or bpy.data.collections.new('Cameras and lights')
    if presentation.name not in bpy.context.scene.collection.children:
        bpy.context.scene.collection.children.link(presentation)
    for o in bpy.context.scene.objects:
        if o.type in {'CAMERA', 'LIGHT'}:
            for collection in list(o.users_collection):collection.objects.unlink(o)
            presentation.objects.link(o)
    if bpy.context.window:
        bpy.context.window.workspace = bpy.data.workspaces['Layout']
    eye = Vector((0, 1.9, 1.55))
    forward = Vector((0, 1, 0))
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type != 'VIEW_3D':continue
            space = area.spaces.active
            space.shading.type = 'MATERIAL'
            space.shading.use_scene_world = False
            space.overlay.show_extras = False
            space.clip_start = .05
            space.clip_end = 150
            space.region_3d.view_perspective = 'PERSP'
            space.region_3d.view_rotation = forward.to_track_quat('-Z', 'Y')
            space.region_3d.view_distance = 3
            space.region_3d.view_location = eye + forward * 3
    note = bpy.data.texts.get('START HERE') or bpy.data.texts.new('START HERE')
    note.clear()
    note.write('Marina interior: editable room collections, packed textures, meters.\n'
               'The viewport starts in the foyer at 1.55 m eye height.\n'
               'For first-person navigation: View > Navigation > Walk Navigation.\n'
               'Mouse looks; WASD moves; Enter accepts the view; Esc cancels.\n'
               'For gameplay collision, open scenes/Marina_House_Walkthrough.tscn in Godot and press F6.\n'
               'Save As a new .blend before manual edits: build_marina_interior.py regenerates this file.\n')


bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1
room = 'Shell'
collections = {}
materials = {}
serial = 0


def mat(name, color, rough=.65, metallic=0, image=None, repeat=1, normal=None):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    bs = m.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value = (*color, 1)
    bs.inputs['Roughness'].default_value = rough
    bs.inputs['Metallic'].default_value = metallic
    if image:
        tex = m.node_tree.nodes.new('ShaderNodeTexImage')
        tex.image = bpy.data.images.load(str(image), check_existing=True)
        m.node_tree.links.new(tex.outputs['Color'], bs.inputs['Base Color'])
    if normal:
        tex = m.node_tree.nodes.new('ShaderNodeTexImage')
        tex.image = bpy.data.images.load(str(normal), check_existing=True)
        tex.image.colorspace_settings.name = 'Non-Color'
        n = m.node_tree.nodes.new('ShaderNodeNormalMap')
        n.inputs['Strength'].default_value = .3
        m.node_tree.links.new(tex.outputs['Color'], n.inputs['Color'])
        m.node_tree.links.new(n.outputs['Normal'], bs.inputs['Normal'])
    m['repeat_m'] = repeat
    materials[name] = m
    return m


ivory = mat('Ivory painted wood', (.81,.79,.70), .4)
plaster = mat('Warm plaster', (.76,.73,.65), .92)
walnut = mat('Dark walnut joinery', (.115,.049,.024), .36)
oak = mat('Honey oak furniture', (.34,.21,.10), .44)
red = mat('Cranberry upholstery', (.25,.017,.032), .88)
green = mat('Den green paint', (.035,.12,.066), .76)
leather = mat('Dark leather', (.09,.04,.023), .42)
brass = mat('Aged brass', (.47,.30,.11), .27, .85)
black = mat('Appliance enamel', (.018,.024,.021), .27)
steel = mat('Stainless sink', (.48,.51,.53), .22, .9)
blue = mat('Blue glazed ceramic', (.037,.089,.145), .2)
grout = mat('Warm pale grout', (.42,.40,.32), .8)
terracotta = mat('Terracotta', (.26,.092,.045), .73)
linen = mat('Curtain linen', (.83,.81,.7), .94)
leaf = mat('Plant foliage', (.035,.12,.04), .8)
foyerpaper = mat('Foyer damask', (1,1,1), image=ROOT/'art/home_alone/textures/foyer_wallpaper.png', repeat=1.2)
floral = mat('Kitchen rose stripe', (1,1,1), image=ART/'textures/kitchen_floral.png', repeat=.95)
wood = mat('Photographed oak floor', (1,1,1), .52, image=ROOT/'art/home_alone/textures/wood_floor_diff.jpg', repeat=3,
           normal=ROOT/'art/home_alone/textures/wood_floor_normal.jpg')


def mesh(name, verts, faces, material, collision=False, bevel=0):
    global serial
    serial += 1
    data = bpy.data.meshes.new(name)
    data.from_pydata(verts, [], faces)
    data.update()
    o = bpy.data.objects.new(f'{room}_{name}_{serial}' + ('-col' if collision else ''), data)
    if room not in collections:
        collections[room] = bpy.data.collections.new(room)
        scene.collection.children.link(collections[room])
    collections[room].objects.link(o)
    data.materials.append(material)
    uv = data.uv_layers.new(name='UVMap')
    scale = material.get('repeat_m', 1)
    for p in data.polygons:
        axis = max(range(3), key=lambda i: abs(p.normal[i]))
        a,b = ((1,2),(0,2),(0,1))[axis]
        for idx in p.loop_indices:
            v = data.vertices[data.loops[idx].vertex_index].co
            uv.data[idx].uv = (v[a]/scale, v[b]/scale)
    if bevel:
        mod = o.modifiers.new('Small edge bevel', 'BEVEL')
        mod.width = bevel
        mod.segments = 3
    return o


def box(name, c, s, material, collision=False, bevel=0):
    assert min(s)>0, (name,s)
    vs=[(c[0]+x*s[0]/2,c[1]+y*s[1]/2,c[2]+z*s[2]/2) for x,y,z in
        [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
    return mesh(name,vs,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],material,collision,bevel)


def rod(name, a, b, radius, material):
    a,b=Vector(a),Vector(b)
    direction=b-a
    basis=direction.to_track_quat('Z','Y')
    vs=[tuple(p+basis@Vector((math.cos(i*math.tau/12)*radius,math.sin(i*math.tau/12)*radius,0))) for p in (a,b) for i in range(12)]
    return mesh(name,vs,[tuple(reversed(range(12))),tuple(range(12,24))]+[(i,(i+1)%12,(i+1)%12+12,i+12) for i in range(12)],material)


def lathe(name, c, profile, material, segments=16):
    vs=[(c[0]+r*math.cos(i*math.tau/segments),c[1]+r*math.sin(i*math.tau/segments),c[2]+z) for z,r in profile for i in range(segments)]
    faces=[tuple(reversed(range(segments))),tuple(range((len(profile)-1)*segments,len(profile)*segments))]
    faces += [(j*segments+i,j*segments+(i+1)%segments,(j+1)*segments+(i+1)%segments,(j+1)*segments+i) for j in range(len(profile)-1) for i in range(segments)]
    o=mesh(name,vs,faces,material)
    for p in o.data.polygons:p.use_smooth=True
    return o


def group_rotate(objects, center, angle):
    c=Vector(center)
    from mathutils import Matrix
    rot=Matrix.Rotation(angle,4,'Z')
    for o in objects:
        for v in o.data.vertices:v.co=c+rot.to_3x3()@(v.co-c)


def floor_rect(name,x0,x1,y0,y1,material):
    box(name,((x0+x1)/2,(y0+y1)/2,-.1),(x1-x0,y1-y0,.2),material,True)


def wall(name,axis,fixed,start,end,finish,other=plaster,openings=(),height=H):
    # One core, two independently textured faces. Openings are center,width,sill,height.
    def part(a,b,z0,z1):
        if b-a<.001 or z1-z0<.001:return
        def make(label,offset,thickness,material):
            c=[(a+b)/2,fixed+offset,(z0+z1)/2];s=[b-a,thickness,z1-z0]
            if axis=='Y':c[0],c[1]=c[1],c[0];s[0],s[1]=s[1],s[0]
            box(label,c,s,material,label==name)
        make(name,0,.18,plaster)
        make(name+'_finish',-.094,.008,finish)
        make(name+'_reverse',.094,.008,other)
        if z0==0:
            for offset in [-.112,.112]:
                c=[(a+b)/2,fixed+offset,.09];s=[b-a,.036,.18]
                if axis=='Y':c[0],c[1]=c[1],c[0];s[0],s[1]=s[1],s[0]
                box('Skirting',c,s,ivory,False,.005)
    cursor=start
    for center,w,sill,h in sorted(openings):
        a,b=center-w/2,center+w/2
        assert cursor<=a<b<=end and sill+h<=height,(name,openings)
        part(cursor,a,0,height);part(a,b,0,sill);part(a,b,sill+h,height);cursor=b
    part(cursor,end,0,height)
    for offset in [-.12,.12]:
        c=[(start+end)/2,fixed+offset,height-.1];s=[end-start,.09,.13]
        if axis=='Y':c[0],c[1]=c[1],c[0];s[0],s[1]=s[1],s[0]
        box('Cornice',c,s,ivory,False,.016)


def opening_trim(axis,fixed,center,width,sill,height):
    def piece(u,d,z,su,sd,sz):
        c=(u,fixed+d,z) if axis=='X' else (fixed+d,u,z)
        s=(su,sd,sz) if axis=='X' else (sd,su,sz)
        box('Opening casing',c,s,ivory,False,.006)
    for d in [-.12,.12]:
        for u in [center-width/2-.055,center+width/2+.055]:piece(u,d,sill+height/2,.11,.065,height+.17)
        piece(center,d,sill+height+.055,width+.22,.065,.11)
        if sill:piece(center,d,sill-.025,width+.22,.13,.09)


def window(axis,fixed,center,width,sill=.75,height=1.9,inward=1,curtains=True):
    opening_trim(axis,fixed,center,width,sill,height)
    def piece(u,d,z,su,sd,sz,material=ivory):
        c=(u,fixed+d,z) if axis=='X' else (fixed+d,u,z)
        s=(su,sd,sz) if axis=='X' else (sd,su,sz)
        box('Window',c,s,material)
    for i in range(4):piece(center-width/2+i*width/3,0,sill+height/2,.035,.065,height)
    for i in range(5):piece(center,0,sill+i*height/4,width,.065,.032)
    if not curtains:return
    def fabric(mid,w,top,length,material,layer=0):
        vs=[];nx,nz=28,12
        for j in range(nz+1):
            v=j/nz
            for i in range(nx+1):
                u=i/nx
                d=inward*(.22+layer+.035*math.cos(u*math.tau*7))
                along=mid+(u-.5)*w*(.7+.3*abs(2*v-1))
                z=top-v*length+.018*math.sin(u*math.tau*7)*v
                vs.append((along,fixed+d,z) if axis=='X' else (fixed+d,along,z))
        faces=[(j*(nx+1)+i,j*(nx+1)+i+1,(j+1)*(nx+1)+i+1,(j+1)*(nx+1)+i) for j in range(nz) for i in range(nx)]
        mesh('Pleated curtain',vs,faces,material)
    for s in [-1,1]:fabric(center+s*(width/2-.09),.43,sill+height+.1,height+.12,linen)
    fabric(center,width+.36,sill+height+.2,.29,red if room in ['Kitchen','Breakfast'] else green,.08)


# Main plan: front=-Y, Blender meters; Godot coordinates become (x,z,-y).
room='Foyer'
floor_rect('Floor',-2.2,2.2,0,10.6,wood)
wall('Front','X',0,-2.2,2.2,plaster,foyerpaper,[(0,1.5,0,2.55)])
wall('Living partition','Y',-2.2,0,9.3,floral,foyerpaper,[(2.7,2.2,0,2.5)],height=H*2)
wall('Dining partition','Y',2.2,0,6.8,foyerpaper,red,[(2.7,2.2,0,2.5)],height=H*2)
wall('Breakfast partition','Y',2.2,6.8,10.6,foyerpaper,floral,[(FOYER_BREAKFAST_DOOR,1.35,0,2.5)],height=H*2)
wall('Landing side','Y',-2.2,9.3,10.6,plaster,foyerpaper,height=H*2)
box('Upper foyer front',(0,3.4,H*1.5),(4.4,.18,H),foyerpaper,True)
wall('Rear','X',10.6,-2.2,2.2,foyerpaper,plaster,[(-.7,2.15,3.05,2.2)],height=H*2)
wall('Arch wall','X',8.65,0,2.2,foyerpaper,plaster,[(1.15,1.5,0,2.6)])
# Curved top of rear arch, extruded so collision follows the visible opening.
for side in [-1,1]:
    for i in range(12):
        a=i*math.pi/24;b=(i+1)*math.pi/24
        x0=1.15+side*.75*math.cos(a);x1=1.15+side*.75*math.cos(b)
        z0=1.85+.75*math.sin(a);z1=1.85+.75*math.sin(b)
        vs=[(x,y,z) for y in [8.55,8.75] for x,z in [(x0,z0),(x1,z1),(x1,2.61),(x0,2.61)]]
        mesh('Arch curve',vs,[(0,1,2,3),(7,6,5,4),(0,4,5,1),(3,2,6,7)],ivory,True)
wall('Vestibule','X',1.35,-2.2,2.2,foyerpaper,foyerpaper,[(0,2.5,0,2.65)])
for axis,f,c,w,s,h in [('X',0,0,1.5,0,2.55),('X',1.35,0,2.5,0,2.65),('Y',-2.2,2.7,2.2,0,2.5),('Y',2.2,2.7,2.2,0,2.5),('Y',2.2,FOYER_BREAKFAST_DOOR,1.35,0,2.5)]:opening_trim(axis,f,c,w,s,h)
window('X',10.6,-.7,2.15,3.05,2.2,-1,False)
room='Living'
floor_rect('Floor',-7.8,-2.2,0,9.3,wood)
wall('Front','X',0,-7.8,-2.2,plaster,floral,[(-6.5,1.25,.6,2.1),(-4.2,1.25,.6,2.1)])
wall('Den partition','Y',-7.8,0,9.3,green,floral,[(2.7,2.2,0,2.5)])
wall('Fireplace wall','X',9.3,-7.8,-2.2,floral,plaster,[(-6.9,1,.75,1.9),(-3.05,1,.75,1.9)])
for c in [-6.5,-4.2]:window('X',0,c,1.25,.6,2.1)
for c in [-6.9,-3.05]:window('X',9.3,c,1,.75,1.9,-1)
opening_trim('Y',-7.8,2.7,2.2,0,2.5)
room='Den'
floor_rect('Floor',-12.1,-7.8,.8,8.3,wood)
wall('Front','X',.8,-12.1,-7.8,plaster,green,[(-10,2.7,.6,2.1)])
wall('Side','Y',-12.1,.8,8.3,plaster,green,[(3.9,3.1,.6,2.1)])
wall('TV wall','X',8.3,-12.1,-7.8,green)
window('X',.8,-10,2.7,.6,2.1)
window('Y',-12.1,3.9,3.1,.6,2.1)
room='Dining'
floor_rect('Floor',2.2,7.6,0,6.8,wood)
wall('Front','X',0,2.2,7.6,plaster,red,[(5,2.6,.65,2)])
wall('Breakfast wall','X',6.8,2.2,7.6,red,floral,[(3.5,1.55,0,2.5)])
wall('Sunroom partition','Y',7.6,0,6.8,red,ivory,[(2.7,2.2,0,2.5)])
window('X',0,5,2.6,.65,2)
opening_trim('X',6.8,3.5,1.55,0,2.5)
opening_trim('Y',7.6,2.7,2.2,0,2.5)
# Wainscot rails and flat panels stop at the same openings as the walls.
for axis,f,a,b in [('X',.105,2.3,3.6),('X',.105,6.4,7.5),('X',6.695,4.35,7.5),('X',6.695,2.3,2.67),('Y',2.305,.1,1.55),('Y',2.305,3.85,6.7),('Y',7.495,.1,1.55),('Y',7.495,3.85,6.7)]:
    def panelbox(u,z,su,sz,depth=.035):
        box('Wainscot', (u,f,z) if axis=='X' else (f,u,z),(su,depth,sz) if axis=='X' else (depth,su,sz),ivory,False,.004)
    panelbox((a+b)/2,.48,b-a,.9)
    panelbox((a+b)/2,.97,b-a,.065,.06)
    for j in range(int((b-a)/.7)+1):panelbox(a+j*(b-a)/max(1,int((b-a)/.7)),.48,.045,.82,.055)
room='Sunroom'
floor_rect('Floor',7.6,12,.7,6.8,wood)
wall('Front','X',.7,7.6,12,plaster,ivory,[(9.8,3.2,.55,2.1)])
wall('Side','Y',12,.7,6.8,ivory,plaster,[(3.6,4.4,.55,2.1)])
wall('Rear','X',6.8,8.5,12,ivory)
window('X',.7,9.8,3.2,.55,2.1,1,False)
window('Y',12,3.6,4.4,.55,2.1,-1,False)
room='Breakfast'
floor_rect('Floor',2.2,8.5,6.8,10,terracotta)
floor_rect('Floor extension',2.2,6,10,BREAKFAST_BACK,terracotta)
wall('Stair wall','Y',2.2,10.6,BREAKFAST_BACK,plaster,floral,height=H+2.2)
wall('Stair rear','X',BREAKFAST_BACK,2.2,3.7,floral,height=H+2.2)
box('Stair upper return',(3.7,(SERVICE_START+BREAKFAST_BACK)/2,H+1.1),(.18,BREAKFAST_BACK-SERVICE_START,2.2),plaster,True)
box('Stair upper front',(2.95,SERVICE_START,H+1.1),(1.5,.18,2.2),floral,True)
wall('Rear','X',BREAKFAST_BACK,3.7,6,floral,plaster,[(4.8,1.25,.9,1.8)])
wall('Side return','Y',8.5,6.8,10,floral)
window('X',BREAKFAST_BACK,4.8,1.25,.9,1.8,-1)
room='Kitchen'
floor_rect('Floor',6,11.2,10,BACK,terracotta)
wall('Refrigerator wall','Y',6,BREAKFAST_BACK,BACK,plaster,floral)
wall('Sink wall','X',BACK,6,11.2,floral,plaster,[(7.05,1.05,0,2.5),(9.45,2.2,1.12,1.35)])
wall('Window seat wall','Y',11.2,10,BACK,floral,plaster,[(12.75,1.35,.67,1.9),(15.7,1.35,.67,1.9)])
wall('Return wall','X',10,8.5,11.2,plaster,floral)
window('X',BACK,9.45,2.2,1.12,1.35,-1)
for y in [12.75,15.7]:window('Y',11.2,y,1.35,.67,1.9,-1)
opening_trim('X',BACK,7.05,1.05,0,2.5)


def stair(name,x,y,width,run,height,count):
    rise=height/count;step=run/count
    for i in range(count):
        z=rise*(i+1)
        box(name+' step',(x,y+(i+.5)*step,z/2),(width,step,z),ivory,True)
        box(name+' nosing',(x,y+(i+.5)*step-.015,z+.016),(width+.03,step+.04,.033),walnut,False,.005)
        if name=='Main':
            box('Carpet tread',(x,y+(i+.5)*step,z+.038),(width*.64,step+.032,.014),red)
            box('Carpet riser',(x,y+i*step-.018,z-rise/2),(width*.64,.015,rise),red)
        bx=x+width/2-.045
        for dy in [.07,.22]:
            by=y+i*step+dy
            lathe('Turned baluster',(bx,by,z),[(0,.025),(.18,.025),(.25,.04),(.32,.017),(.60,.02),(.68,.032),(.76,.02),(.9,.02)],ivory,10)
    rod('Stair handrail',(x+width/2,y,.98),(x+width/2,y+run,height+.98),.052,walnut)
    lathe('Newel post',(x+width/2,y,0),[(0,.09),(.16,.09),(.2,.06),(.75,.06),(.83,.09),(.9,.07),(1.05,.02)],walnut)

room='Foyer'
stair('Main',-1.35,3.5,1.5,4.8,2.68,16)
box('Rear landing',(-.95,9.4,2.58),(2.5,2.2,.2),wood,True)
box('Landing carpet',(-.95,9.4,2.697),(2.3,2.08,.03),red)
# Four steps turning right from the rear landing to the upper hall.
for i in range(4):
    box('Landing turn step',(.45+(i+.5)*.31,9.4,2.68+(i+1)*.1675/2),(.31,1.5,(i+1)*.1675),ivory,True)
    box('Landing turn carpet',(.45+(i+.5)*.31,9.4,2.68+(i+1)*.1675+.018),(.33,1.05,.026),red)
box('Upper hall',(1.3,6.1,H-.1),(1.8,6.2,.2),wood,True)
for y in [3.8+i*.17 for i in range(30)]:
    lathe('Upper baluster',(.4,y,H),[(0,.025),(.2,.025),(.27,.045),(.34,.02),(.75,.025),(.9,.022)],ivory,10)
rod('Upper handrail',(.4,3.8,H+.91),(.4,8.65,H+.91),.055,walnut)
room='Breakfast'
stair('Service',2.92,SERVICE_START,1.18,3.55,H,18)
# The tour does not establish an upstairs exit; enclose the visible stair volume.
box('Service top landing',(2.92,14.05,H-.10),(1.18,.30,.20),wood,True)
# Ceilings are separate for overhead inspection; eye-level renders keep them intact.
room='Ceilings'
for x0,x1,y0,y1,z in [(-7.8,-2.2,0,9.3,H),(-12.1,-7.8,.8,8.3,H),(2.2,7.6,0,6.8,H),(7.6,12,.7,6.8,H),(2.2,8.5,6.8,10,H),(3.7,6,10,BREAKFAST_BACK,H),(2.2,3.7,10,SERVICE_START,H),(2.2,3.7,SERVICE_START,BREAKFAST_BACK,H+2.2),(6,11.2,10,BACK,H),(-2.2,2.2,0,3.4,H),(-2.2,2.2,3.4,10.6,H*2)]:
    box('Ceiling',((x0+x1)/2,(y0+y1)/2,z+.08),(x1-x0,y1-y0,.16),plaster,True)
room='Kitchen'
for y in [10.2,12.2,14.2,16.2,18.25]:box('Ceiling beam',(8.6,y,H-.12),(5.2,.19,.24),walnut)
room='Breakfast'
for y in [7.1,9.5]:box('Ceiling beam',(4.95,y,H-.12),(5.4,.19,.24),walnut)
box('Ceiling beam',(4.85,13.8,H-.12),(2.3,.19,.24),walnut)

# Large reference silhouettes. Keep the walk paths open and leave small dressing for later.
def table(name, c, length, width, top_z=0.78, material=oak, chairs=0):
    x,y=c
    box(name+' top',(x,y,top_z),(length,width,.12),material,True,.045)
    for dx in (-length*.34,length*.34):
        for dy in (-width*.32,width*.32):box(name+' leg',(x+dx,y+dy,top_z/2-.04),(.12,.12,top_z-.08),material,True,.02)
    for i in range(chairs):
        a=math.tau*i/chairs
        cx=x+math.cos(a)*(length*.58);cy=y+math.sin(a)*(width*.72)
        box(name+' chair seat',(cx,cy,.48),(.52,.52,.09),oak,True,.03)
        for dx in [-.19,.19]:
            for dy in [-.19,.19]:box(name+' chair leg',(cx+dx,cy+dy,.22),(.055,.055,.44),oak,False,.008)
        box(name+' chair back',(cx+math.cos(a)*.2,cy+math.sin(a)*.2,.92),(.09,.45,.8),oak,False,.02)

def cabinet_run(name, x0, x1, y, z=.48, depth=.58, material=walnut, upper=False, height=.92):
    count=max(1,round((x1-x0)/.62));step=(x1-x0)/count
    for i in range(count):
        x=x0+(i+.5)*step
        box(name+' cabinet',(x,y,z),(step-.035,depth,height if not upper else .72),material,True,.025)
        for side in (-1,1):box(name+' stile',(x+side*(step/2-.06),y-depth/2-.012,z),(.045,.025,.76 if not upper else .58),oak,False,.008)
        box(name+' pull',(x,y-depth/2-.035,z+.05),(.13,.035,.025),brass)

def sofa(name,c,length,depth,material=leather):
    x,y=c
    box(name+' seat',(x,y,.52),(length,depth,.34),material,True,.11)
    box(name+' back',(x,y+depth/2-.12,.98),(length,.22,.9),material,False,.1)
    for side in (-1,1):
        box(name+' arm',(x+side*(length/2-.13),y,.86),(.2,depth,.68),material,False,.08)
        for dy in [-depth*.30,depth*.30]:box(name+' foot',(x+side*(length/2-.18),y+dy,.175),(.09,.09,.35),walnut,False,.01)

room='Foyer'
box('Foyer console',(1.85,6.0,.62),(.38,1.25,.9),walnut,True,.025)
box('Console top',(1.85,6.0,1.1),(.48,1.42,.09),oak,False,.025)
for y in [5.65,6.35]:lathe('Foyer urn',(1.85,y,1.145),[(0,.12),(.12,.08),(.25,.1),(.36,.05)],brass,12)
room='Living'
box('Fireplace',(-5.2,9.08,1.25),(2.0,.28,2.25),walnut,True,.03)
box('Firebox',(-5.2,8.9,1.0),(1.08,.08,1.0),black,False,.02)
sofa('Living sofa',(-4.55,4.1),2.35,.9,leather)
box('Wingback chair',(-3.15,1.7,.7),(.9,.85,1.35),red,True,.1)
box('Piano',(-6.3,1.55,.72),(1.65,.62,.95),walnut,True,.04)
room='Den'
# M26/M27: sofa under the side window faces leather seating on the opposite wall.
before=set(collections[room].objects)
sofa('Den red sofa',(-11.35,4.7),2.25,.88,red)
group_rotate(set(collections[room].objects)-before,(-11.35,4.7,0),math.pi/2)
for y in [4.55,6.0]:
    before=set(collections[room].objects)
    sofa('Den leather chair',(-8.45,y),.95,.88,leather)
    group_rotate(set(collections[room].objects)-before,(-8.45,y,0),-math.pi/2)
table('Den coffee table',(-10.3,4.8),.60,1.3,.43,walnut)
# M08: television sits in the middle bay of a full-width bookcase.
box('Den bookcase back',(-9.95,8.16,1.43),(3.8,.06,2.7),walnut,True)
for x in [-11.85,-10.59,-9.31,-8.05]:
    box('Den bookcase upright',(x,7.98,1.43),(.075,.42,2.7),walnut,True,.008)
for z in [.12,.7,1.10,2.2,2.78]:
    box('Den bookcase shelf',(-9.95,7.98,z),(3.8,.42,.065),walnut,True,.008)
box('Den television',(-9.95,7.96,1.60),(.98,.32,.91),black,True,.03)
box('Den television screen',(-9.95,7.788,1.62),(.82,.025,.69),black,False,.035)
table('Den desk',(-10.2,1.55),1.35,.62,.75,walnut)
room='Dining'
before=set(collections[room].objects)
table('Dining table',(4.9,3.4),2.9,1.25,.82,oak,8)
group_rotate(set(collections[room].objects)-before,(4.9,3.4,0),math.pi/2)
cabinet_run('China cabinet',5.9,7.1,6.35,.9,.42,ivory,True)
box('China cabinet base',(6.5,6.35,.55),(1.55,.42,1.0),ivory,True,.025)
room='Breakfast'
before=set(collections[room].objects)
table('Breakfast table',(5.4,9.4),2.25,1.05,.8,oak,6)
group_rotate(set(collections[room].objects)-before,(5.4,9.4,0),math.pi/2)
# M18/M23: hutch runs along the west wall, south of the foyer doorway.
before=set(collections[room].objects)
cabinet_run('Breakfast hutch',6.95,8.65,-2.58,.48,.52,ivory,height=.84)
box('Breakfast hutch counter',(7.8,-2.58,.94),(1.78,.58,.08),ivory,True,.012)
box('Breakfast hutch back',(7.8,-2.34,1.84),(1.75,.06,1.64),ivory)
for u in [6.925,8.675]:box('Breakfast hutch side',(u,-2.50,1.86),(.065,.38,1.60),ivory,True)
for z in [1.32,1.86,2.39,2.67]:box('Breakfast hutch shelf',(7.8,-2.50,z),(1.78,.38,.055),ivory,True)
group_rotate(set(collections[room].objects)-before,(0,0,0),math.pi/2)
# Guard the actual mesh extents against overlap with either the doorway or stairs.
hutch=[o for o in collections[room].objects if 'Breakfast hutch' in o.name]
assert max(v.co.y for o in hutch for v in o.data.vertices) < FOYER_BREAKFAST_DOOR-1.35/2-.11
assert FOYER_BREAKFAST_DOOR+1.35/2+.11 < SERVICE_START
room='Kitchen'
# Worktops finish at 0.92 m; layout follows M10/M21/M22 in the tour frame index.
def kitchen_run(name, x0, x1, y):
    cabinet_run(name,x0,x1,y,.48,.62,height=.80)
    box(name+' counter',((x0+x1)/2,y,.90),(x1-x0+.03,.66,.04),blue,True,.008)

# Rear sink run leaves the back-door opening clear.
kitchen_run('Sink base',7.85,10.95,BACK-.43)
# ponytail: shallow sink inset; cut the countertop mesh in the close-up joinery pass.
box('Sink cavity',(9.45,BACK-.43,.924),(.82,.46,.012),black)
box('Sink bottom',(9.45,BACK-.43,.932),(.68,.33,.012),steel,False,.02)
for x in [9.04,9.86]:box('Sink rim',(x,BACK-.43,.94),(.035,.49,.035),steel,False,.008)
for y in [BACK-.675,BACK-.185]:box('Sink rim',(9.45,y,.94),(.85,.035,.035),steel,False,.008)
rod('Faucet',(9.45,BACK-.17,.94),(9.45,BACK-.17,1.25),.025,brass)
rod('Faucet spout',(9.45,BACK-.17,1.25),(9.45,BACK-.40,1.25),.025,brass)
for x0,x1 in [(7.85,8.25),(10.65,10.95)]:
    cabinet_run('Sink upper',x0,x1,BACK-.29,2.15,.35,walnut,True)
# Rotate complete cabinet groups onto the right wall, with fronts facing into the kitchen.
for y0,y1 in [(10.25,12.02),(13.48,14.97),(16.43,BACK-.82)]:
    before=set(collections[room].objects)
    kitchen_run('Side base',-y1,-y0,10.78)
    cabinet_run('Side upper',-y1,-y0,10.93,2.15,.35,walnut,True)
    group_rotate(set(collections[room].objects)-before,(0,0,0),-math.pi/2)
for y in [12.75,15.7]:
    box('Window seat',(10.82,y,.26),(.60,1.35,.52),walnut,True,.01)
    box('Window seat cushion',(10.78,y,.55),(.66,1.32,.08),red,False,.025)
box('Back door',(7.05,BACK,1.25),(1.05,.12,2.5),ivory,True)
# The long arm points toward the sink; the short return faces the breakfast room.
box('Island long',(8.55,14.60,.48),(.78,3.55,.84),walnut,True,.012)
box('Island return',(8.2,12.65,.48),(1.48,.78,.84),walnut,True,.012)
box('Island long counter',(8.55,14.60,.90),(1.02,3.65,.04),blue,True,.008)
box('Island return counter',(8.2,12.65,.90),(1.70,1.02,.04),blue,True,.008)
box('Island cooktop',(8.55,15.50,.94),(.63,.85,.035),black,False,.008)
for x in [8.38,8.72]:
    for y in [15.27,15.72]:lathe('Burner',(x,y,.96),[(0,.10),(.018,.10)],steel)
for y in [13.6,14.6,15.6]:
    lathe('Island stool',(9.3,y,0),[(0,.19),(.08,.16),(.58,.055),(.62,.21),(.68,.21)],oak)
    box('Stool collision',(9.3,y,.34),(.30,.30,.68),oak,True,.015)
for y in [14.45,15.85]:
    rod('Pot rack suspension',(8.15,y,2.45),(8.15,y,H),.02,brass)
rod('Pot rack rail',(8.15,14.45,2.45),(8.15,15.85,2.45),.025,brass)
for y in [14.6,15.05,15.5]:
    rod('Pan handle',(8.15,y,2.45),(8.15,y,2.18),.025,black)
    pan=lathe('Hanging pan',(0,0,0),[(0,.19),(.065,.19),(.09,.16)],red,16)
    from mathutils import Matrix
    for v in pan.data.vertices:v.co=Matrix.Rotation(math.pi/2,3,'Y')@v.co+Vector((8.15,y,2.02))
box('Refrigerator',(6.53,10.65,1.05),(.85,.78,2.1),black,True,.025)
for z in [.55,1.55]:box('Refrigerator handle',(7.0,10.55,z),(.045,.06,.45),steel,False,.01)
# Keep all kitchen furnishings inside its footprint and enforce human-scale worktops.
for o in collections[room].objects:
    if any(tag in o.name for tag in ['base','Island','Sink','Refrigerator','Window seat cushion']) and 'wall' not in o.name:
        assert all(5.99 <= v.co.x <= 11.3 and 9.99 <= v.co.y <= BACK+.11 for v in o.data.vertices),o.name
    if 'counter' in o.name:
        assert .90 <= max(v.co.z for v in o.data.vertices) <= .93,o.name
room='Dining'
for x in [2.65,6.95]:box('Dining drape',(x,0.14,2.1),(.28,.06,1.9),red)
room='Kitchen'
for x in [8.3,10.5]:box('Counter canister',(x,BACK-.43,1.05),(.18,.18,.26),ivory,False,.02)
room='Den'
for x in [-11.3,-8.7]:lathe('Den plant',(x,7.55,.15),[(0,.22),(.2,.2),(.65,.07)],leaf,12)

# Export the room-specific asset and a modest diagnostic render.
for o in bpy.context.scene.objects:o.select_set(o.type=='MESH')
bpy.ops.export_scene.gltf(filepath=str(OUT/'interior.glb'), export_format='GLB', use_selection=True, export_apply=True, export_animations=False)
world=bpy.data.worlds.new('Marina interior world');scene.world=world;world.use_nodes=True
world.node_tree.nodes['Background'].inputs[0].default_value=(.12,.14,.16,1);world.node_tree.nodes['Background'].inputs[1].default_value=.45
bpy.ops.object.light_add(type='AREA',location=(4,-2,8));bpy.context.object.data.energy=1500;bpy.context.object.data.size=8
bpy.ops.object.camera_add(location=(6.8,13.5,1.55))
camera=bpy.context.object
camera.rotation_euler=(Vector((9.5,17,1.3))-camera.location).to_track_quat('-Z','Y').to_euler()
camera.data.lens=22
scene.camera=camera
# Modest interior fill for the diagnostic view with the ceiling present.
bpy.ops.object.light_add(type='AREA',location=(8.5,14.5,3.1))
bpy.context.object.data.energy=180
bpy.context.object.data.size=4
for location,energy in [((0,6,5.7),250),((-10,4.5,3.1),120),((5,9.4,3.1),160)]:
    bpy.ops.object.light_add(type='AREA',location=location)
    bpy.context.object.data.energy=energy
    bpy.context.object.data.size=3
scene.render.engine='BLENDER_EEVEE_NEXT'
scene.render.resolution_x=1280
scene.render.resolution_y=720
scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'
if '--render' in sys.argv:
    scene.render.filepath=str(ART/'kitchen-breakfast.png')
    bpy.ops.render.render(write_still=True)
    for name,location,target in [('foyer',(1.15,2.7,1.55),(-.6,6,1.5)),('den',(-9.45,2.7,1.55),(-10.2,5.7,1.3)),('breakfast',(7.4,7.35,1.55),(2.6,9.4,1.5))]:
        camera.location=location
        camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler()
        scene.render.filepath=str(ART/('blender-'+name+'.png'))
        bpy.ops.render.render(write_still=True)
    camera.location=(6.8,13.5,1.55)
    camera.rotation_euler=(Vector((9.5,17,1.3))-camera.location).to_track_quat('-Z','Y').to_euler()
    hidden=[o for o in scene.objects if o.name.startswith('Ceilings_') or 'Ceiling beam' in o.name or 'Upper hall' in o.name]
    for o in hidden:o.hide_render=True
    bpy.ops.object.light_add(type='AREA',location=(0,9,18))
    plan_light=bpy.context.object
    plan_light.data.energy=3500
    plan_light.data.size=20
    bpy.ops.object.camera_add(location=(0,9.25,30))
    plan=bpy.context.object
    plan.name='Marina plan camera'
    plan.data.type='ORTHO'
    plan.data.ortho_scale=27
    scene.camera=plan
    scene.render.resolution_y=1024
    scene.render.filepath=str(ART/'plan.png')
    bpy.ops.render.render(write_still=True)
    for o in hidden:o.hide_render=False
    plan_light.hide_render=True
    scene.camera=camera
    scene.render.resolution_y=720
    scene.render.filepath=str(ART/'kitchen-breakfast.png')
prepare_blender_workspace()
bpy.ops.wm.save_as_mainfile(filepath=str(ART/'interior.blend'))
assert abs((BACK-10)*5.2-KITCHEN_AREA)<.01
print('MARINA INTERIOR OK',round(BACK-10,3),'m kitchen depth',len(scene.objects),'objects')
