"""One two-sided front-door leaf, film 9358/778/714, in the existing opening.
50 mm thickness is authored (DEVIATIONS 105). Both faces receive bevelled joinery,
rounded hardware and baked normal/AO/curvature + fine paint detail. Frame stays in FrontDoor.glb.
"""
import math
import sys
from pathlib import Path
import bpy
import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parent))
from hifi_lib import Part, material
import hifi_pipeline as hp
ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'unity/HomeAlone/Assets/Models/Foyer/FrontLeaf.glb'
TEX = ROOT/'unity/HomeAlone/Assets/Textures/Generated/FrontLeaf'
X0, X1 = 10.082, 10.132
Z0, Z1, H = 9.312, 10.119, 1.896
ZM = (Z0+Z1)/2
bpy.ops.wm.read_factory_settings(use_empty=True)
coll = bpy.context.scene.collection
parts=[]
class SolidPart(Part):
    # Bevel each closed piece before joining: welding contacting joinery first creates
    # non-manifold edges which Blender cannot bevel.
    def __init__(self,name,mat): super().__init__(name,mat); self.solids=[]
    def finish(self):
        if self.f:
            q=Part(self.name,self.mat);q.v,q.f,q.uv=self.v,self.f,self.uv
            self.solids.append(q);self.v=[];self.f=[];self.uv={}
    def box(self,*args,**kw):
        self.finish();super().box(*args,**kw);self.finish()
    def lathe(self,*args,**kw):
        self.finish();super().lathe(*args,**kw);self.finish()
    def sweep(self,*args,**kw):
        self.finish();super().sweep(*args,**kw);self.finish()


def box(p,x0,x1,y0,y1,z0,z1):
    p.box(min(x0,x1),max(x0,x1),y0,y1,z0,z1)

def face_part(name, side):
    p=SolidPart(name,'FD_'+name); xf=X0 if side<0 else X1; back=(X0+X1)/2
    # Frame members span half the leaf, so the two finishes meet at its edge.
    st=.113; rails=[(0,.20),(.72,.87),(1.53,1.63),(1.80,H)]
    box(p,xf,back,0,H,Z0,Z0+st);box(p,xf,back,0,H,Z1-st,Z1)
    for a,b in rails: box(p,xf,back,a,b,Z0+st,Z1-st)
    for (_,a),(b,_) in zip(rails,rails[1:]):
        box(p,xf,back,a,b,ZM-.05,ZM+.05)
        for c,d in [(Z0+st,ZM-.05),(ZM+.05,Z1-st)]:
            p.finish()
            # Raised field, with a continuous ogee-like stepped moulding profile, all bevelled below.
            cy,cz=(a+b)/2,(c+d)/2
            rings=[]
            for inset,depth in [(0,0),(.006,.003),(.014,.009),(.026,.012),(.037,.006),(.043,.005)]:
                rings.append([(xf-side*depth,a+inset,c+inset),(xf-side*depth,a+inset,d-inset),(xf-side*depth,b-inset,d-inset),(xf-side*depth,b-inset,c+inset)])
            for r,t in zip(rings,rings[1:]):
                for k in range(4):
                    q=[r[k],r[(k+1)%4],t[(k+1)%4],t[k]]
                    mid=np.mean(q,axis=0); p.face(q,(side,mid[1]-cy,mid[2]-cz))
            p.face(rings[-1],(side,0,0))
            # reverse at the core: closes every panel, avoids open-edge normal ambiguity
            rb=[(back,y,z) for _,y,z in rings[0]]
            p.face(rb,(-side,0,0))
            for k in range(4):
                q=[rings[0][k],rb[k],rb[(k+1)%4],rings[0][(k+1)%4]]
                mid=np.mean(q,axis=0);p.face(q,(0,mid[1]-cy,mid[2]-cz))
    p.finish()
    parts.append((p, (0.88,.87,.83) if side<0 else (.018,.026,.022), .32 if side<0 else .27, .002))
face_part('Inside',-1);face_part('Outside',1)
brass=SolidPart('Hardware','FD_Hardware')

def turned(x,y,z,side,prof):
    brass.finish()
    rings=[[(x+side*d,y+r*math.sin(k*math.tau/64),z+r*math.cos(k*math.tau/64)) for k in range(64)] for d,r in prof]
    for a,b in zip(rings,rings[1:]):
        for k in range(64):
            q=[a[k],a[(k+1)%64],b[(k+1)%64],b[k]];m=np.mean(q,axis=0)
            brass.face(q,(side*.00001,m[1]-y,m[2]-z))
    brass.face(rings[0],(-side,0,0));brass.face(rings[-1],(side,0,0));brass.finish()
for side,xf in [(-1,X0),(1,X1)]:
    # Tall escutcheon with rounded ends, actual curved grip, round deadbolt and thumb turn.
    z=Z1-.065
    for y in (.98,1.24): turned(xf,y,z,side,[(0,.024),(.003,.027),(.007,.025),(.009,.019)])
    brass.finish()
    ring=[]
    for cy,start in [(.995,0),(.795,math.pi)]:
        ring += [(cy+.023*math.sin(start+k*math.pi/32),z+.023*math.cos(start+k*math.pi/32)) for k in range(33)]
    for k in range(len(ring)):
        a,b=ring[k],ring[(k+1)%len(ring)]
        brass.face([(xf+side*.002,*a),(xf+side*.002,*b),(xf+side*.006,*b),(xf+side*.006,*a)],(0,(a[0]+b[0])/2-.895,(a[1]+b[1])/2-z))
    brass.face([(xf+side*.006,*a) for a in ring],(side,0,0));brass.face([(xf+side*.002,*a) for a in ring],(-side,0,0))
    brass.finish()
    path=[(xf+side*(.012+.035*math.sin(math.pi*k/24)),.80+.17*k/24,z) for k in range(25)]
    brass.sweep(path,[(.007*math.cos(k*math.tau/16),.007*math.sin(k*math.tau/16)) for k in range(16)])
    # Thumb turn and slot: slim, rounded by the hardware bevel, with dark inset behind the slot.
    box(brass,xf+side*.010,xf+side*.024,1.233,1.247,z-.018,z+.018)
    box(brass,xf+side*.002,xf+side*.007,.777,.792,ZM-.130,ZM+.130)
    box(brass,xf+side*.002,xf+side*.007,.819,.834,ZM-.130,ZM+.130)
    for zz in [ZM-.130,ZM+.115]: box(brass,xf+side*.002,xf+side*.007,.792,.819,zz,zz+.015)
    # Screw heads (real round geometry, subtle slots baked/visible at arm's reach).
    for y in (.803,.989): turned(xf+side*.006,y,z,side,[(0,.0035),(.001,.0035),(.0018,.002)])
# Knuckled hinge barrels on the room-side left edge.
for y in (.25,.95,1.65):
    for k in range(5):
        brass.lathe(X0-.006,Z0,y+k*.019,[(0,.008),(.001,.009),(.017,.009),(.018,.008)],n=32)
parts.append((brass,(.75,.56,.25),.26,.001))
final=[]
scan=hp.scan('white_plaster_02','1k');det=hp.detail_map(hp.scan('white_plaster_02','2k'));det[...,0]=.5+(det[...,0]-.5)*.06
for part,albedo,rough,bevel in parts:
    mat=material(part.mat,albedo,rough)
    part.finish();pieces=[]
    for solid in part.solids:
        ob=hp.to_object(solid,mat,coll,hard_deg=60)
        mod=ob.modifiers.new('Rounded joinery','BEVEL');mod.width=bevel;mod.segments=8;mod.limit_method='ANGLE';mod.angle_limit=math.radians(25);mod.use_clamp_overlap=False
        hp.apply_modifiers(ob);pieces.append(ob)
    bpy.ops.object.select_all(action='DESELECT')
    for ob in pieces: ob.select_set(True)
    bpy.context.view_layer.objects.active=pieces[0];bpy.ops.object.join();low=pieces[0];low.name=part.name
    # UV unwrap AFTER beveling; independent 2K atlas per face, 2K hardware atlas.
    bpy.ops.object.select_all(action='DESELECT');low.select_set(True);bpy.context.view_layer.objects.active=low
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(20),island_margin=.002);bpy.ops.object.mode_set(mode='OBJECT')
    if '--mesh-check' in sys.argv:
        final.append(low);continue
    high=low.copy();high.data=low.data.copy();coll.objects.link(high);high.name=low.name+'_High'
    sub=high.modifiers.new('Paint relief subdivision','SUBSURF');sub.subdivision_type='SIMPLE';sub.levels=3
    hp.apply_modifiers(high);hp.displace(high,.018,.00015 if part.name!='Hardware' else .00004)
    maps=hp.bake(low,high,4096,4096,cage=.001,ao_dist=.035,samples=16)
    mp=hp.compose(maps,scan,albedo,2048,1.0,.06,(rough,.025),.05,.12)
    extras={'role':'baked','albedo_srgb':list(albedo),'albedo_tol':.06,'ppm':2048,'detail_tiling':[4,4],'scan':'polyhaven:white_plaster_02 (CC0), subdued to painted finish'}
    hp.write_unity_maps(TEX,part.name,mp,det,extras)
    low.active_material.name = part.mat+'_bake'
    low.data.materials.clear();low.data.materials.append(hp.pbr_material(part.mat,mp,extras))
    if part.name=='Hardware':
        # Metallic HDRP material uses the same baked roughness/AO/normal maps; colour is brass.
        low.active_material['metallic_finish']=.8
    bpy.data.objects.remove(high,do_unlink=True)
    final.append(low)
    print('BAKED',part.name,flush=True)
from front_leaf_finish import finish
final=finish(final)
bpy.context.view_layer.update()
hp.export(Path('/tmp/FrontLeafMesh.glb') if '--mesh-check' in sys.argv else OUT,final,{'artist_pipeline':1,'lod_reason':'single LOD for the entrance hero leaf; compact mesh under 150k triangles, never more than one visible leaf','source':'tools/house/hifi_front_leaf.py'})
print('wrote',OUT)
