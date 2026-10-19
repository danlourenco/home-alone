"""Foyer pier mirror mouldings, same recorded box; film 1690/10673, authored relief (deviation105)."""
import json, math, sys
from pathlib import Path
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
import hifi_pipeline as hp
ROOT=Path(__file__).resolve().parents[2]
D=json.loads((ROOT/'spec/dressing/foyer_props.json').read_text())['mirror']
OUT=ROOT/'unity/HomeAlone/Assets/Models/Foyer/FoyerMirror.glb'
TEX=ROOT/'unity/HomeAlone/Assets/Textures/Generated/FoyerMirror'
bpy.ops.wm.read_factory_settings(use_empty=True)
c=bpy.context.scene.collection
mesh=hp.Mesh('MirrorFrame','FM_Gilt')
cx=D['cx'];x0=cx-D['w']/2;x1=cx+D['w']/2;y0,y1=D['y'];z=D['z_back']
place=lambda x,y,d:(x,y,z+d)
toward=lambda x,y,d:(x,y,d)
# True rounded reeds on a moulded bed, with smooth profile normals and mitred corners.
profile=[]
# Closed oval cross-section, giving the frame both a convex face and solid back.
for k in range(33):
 a=math.tau*k/32
 profile.append((.031*math.cos(a),.023+.019*math.sin(a)))
path=[(x0+.032,(y0+y1)/2),(x0+.032,y0+.032),(x1-.032,y0+.032),(x1-.032,y1-.032),(x0+.032,y1-.032),(x0+.032,(y0+y1)/2)]
path=hp.rounded([path[0]]+[('r',*p) for p in path[1:-1]]+[path[-1]],.060)
mesh.sweep(path,profile[::-1],place,toward,cuts=(1,2,3,4))
# Fine inner bead; separate profile entirely within the retained overall frame envelope.
bead=[(.005*math.cos(math.tau*k/16),.034+.005*math.sin(math.tau*k/16)) for k in range(17)]
path=[(x0+.060,(y0+y1)/2),(x0+.060,y0+.060),(x1-.060,y0+.060),(x1-.060,y1-.060),(x0+.060,y1-.060),(x0+.060,(y0+y1)/2)]
path=hp.rounded([path[0]]+[('r',*p) for p in path[1:-1]]+[path[-1]],.012)
mesh.sweep(path,bead[::-1],place,toward)
# Two curved scrolls in the crest and apron, matching the film's outline rather than a flat polygon.
for sign in (-1,1):
 for base,vertical in [(y1+.025,1),(y0-.018,-1)]:
  r=.046 if vertical>0 else .025
  path=[]
  for k in range(65):
   a=-math.pi/2+math.tau*1.05*k/64;rr=r*(1-.65*k/64)
   path.append((cx+sign*(.09+rr*math.cos(a)),base+vertical*rr*math.sin(a)))
  tube=[(.007*math.cos(math.tau*k/16),.03+.007*math.sin(math.tau*k/16)) for k in range(17)]
  mesh.sweep(path,tube[::-1],place,toward)
# Crown's connecting arch, including a round central bead beneath the recorded crest top.
path=[(cx-.15+.30*k/48,y1+.025+.085*math.sin(math.pi*k/48)) for k in range(49)]
mesh.sweep(path,bead[::-1],place,toward)
height=hp.pack([mesh],1024,width=4096)
low=hp.to_object(mesh,bpy.data.materials.new('low'),c)
high=low.copy();high.data=low.data.copy();c.objects.link(high)
sub=high.modifiers.new('Gilt relief','SUBSURF');sub.subdivision_type='SIMPLE';sub.levels=2;hp.apply_modifiers(high);hp.displace(high,.015,.00012)
maps=hp.bake(low,high,4096,height,cage=.001,ao_dist=.04,samples=16)
scan=hp.scan('white_plaster_02','1k');mp=hp.compose(maps,scan,(.60,.45,.21),1024,1,.1,(.36,.04),.1,.16)
extras={'role':'baked','albedo_srgb':[.60,.45,.21],'albedo_tol':.06,'ppm':1024,'detail_tiling':[3,3],'scan':'polyhaven:white_plaster_02 (CC0), subdued for gilding'}
det=hp.detail_map(hp.scan('white_plaster_02','2k'));det[...,0]=.5+(det[...,0]-.5)*.06
hp.write_unity_maps(TEX,'Gilt',mp,det,extras)
low.data.materials.clear();low.data.materials.append(hp.pbr_material('FM_Gilt',mp,extras))
bpy.data.objects.remove(high,do_unlink=True)
low['artist_pipeline']=1;low['lod_reason']='Single LOD, small fixed mirror frame; continuous mouldings at all views'
bpy.context.view_layer.update()
hp.export(OUT,[low],{'artist_pipeline':1,'lod_reason':'single LOD, small fixed mirror frame; preserving wall joints at all views'})
