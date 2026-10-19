"""Remove painted faces hidden under the hardware; split fittings by side.
Preserves the baked UVs/maps: only covered faces are removed. No floating plates.
Called by hifi_front_leaf; standalone mode refines the previously baked asset.
"""
import sys
from pathlib import Path
import bpy, bmesh

def finish(objects):
    for obj in list(objects):
        if obj.name in ('Inside','Outside'):
            xf=-10.082 if obj.name=='Inside' else -10.132
            zc=(9.312+10.119)/2
            rects=[(zc-.129,zc+.129,.778,.791),(zc-.129,zc+.129,.820,.833),
                   (zc-.129,zc-.116,.792,.819),(zc+.116,zc+.129,.792,.819),
                   (10.054-.020,10.054+.020,.815,.975)]
            bm=bmesh.new();bm.from_mesh(obj.data)
            for axis,values in [(1,sorted(set(v for r in rects for v in r[:2]))),(2,sorted(set(v for r in rects for v in r[2:])) )]:
                for value in values:
                    co=[0.,0.,0.];co[axis]=value;n=[0.,0.,0.];n[axis]=1
                    bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),plane_co=co,plane_no=n,dist=1e-7)
            removed=[]
            for f in bm.faces:
                p=f.calc_center_median()
                if max(abs(v.co.x-xf) for v in f.verts)<.0005 and any(a<p.y<b and c<p.z<d for a,b,c,d in rects): removed.append(f)
            bmesh.ops.delete(bm,geom=removed,context='FACES');bm.to_mesh(obj.data);bm.free();obj.data.update()
            print('covered faces removed',obj.name,len(removed),flush=True)
        elif obj.name=='Hardware':
            # Opposite handles in one renderer fool a through-surface test; each side is a separate fitting.
            for name,side in [('HardwareInside',-1),('HardwareOutside',1)]:
                dup=obj.copy();dup.data=obj.data.copy();obj.users_collection[0].objects.link(dup);dup.name=name
                bm=bmesh.new();bm.from_mesh(dup.data)
                kill=[f for f in bm.faces if (-f.calc_center_median().x-10.107)*side<0]
                bmesh.ops.delete(bm,geom=kill,context='FACES');bm.to_mesh(dup.data);bm.free();dup.data.update();objects.append(dup)
            objects.remove(obj);bpy.data.objects.remove(obj,do_unlink=True)
    bpy.context.view_layer.update()
    return objects

if __name__=='__main__':
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    import hifi_pipeline as hp
    path=Path(__file__).resolve().parents[2]/'unity/HomeAlone/Assets/Models/Foyer/FrontLeaf.glb'
    bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(path))
    objects=[o for o in bpy.context.scene.objects if o.type=='MESH']
    finish(objects)
    for o in objects:
        o['artist_pipeline']=1;o['lod_reason']='Single LOD for compact entrance hero leaf'
    hp.export(path,objects,{'artist_pipeline':1,'lod_reason':'Single LOD for compact entrance hero leaf'})
