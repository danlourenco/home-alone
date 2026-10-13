import bpy,json,numpy as np
from pathlib import Path
from mathutils import Vector
root=Path(__file__).resolve().parents[2]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(root/'assets/home_alone/online_home_alone/HOME_ALONE_FINAL.glb'))
rows=[]; alltris=[]
for o in bpy.context.scene.objects:
 if o.type!='MESH':continue
 v=np.array([tuple(o.matrix_world@x.co) for x in o.data.vertices])
 o.data.calc_loop_triangles(); tv=v[np.array([t.vertices for t in o.data.loop_triangles])];alltris.append(tv)
 rows.append(dict(name=o.name,lo=v.min(0).tolist(),hi=v.max(0).tolist(),triangles=len(tv)))
t=np.concatenate(alltris);cross=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]); area=np.linalg.norm(cross,axis=1)/2
flat=(np.ptp(t[:,:,2],axis=1)<.005)&(area>.001)
z=np.round(t[flat,:,2].mean(1),2); a=area[flat];levels={float(k):float(a[z==k].sum()) for k in np.unique(z)}
out=root/'art/home_alone/references/glb-audit'
(out/'inventory.json').write_text(json.dumps(dict(objects=rows,horizontal_area_by_height=levels),indent=2))
np.savez_compressed(out/'triangles.npz',triangles=t)
print('LEVELS',sorted(levels.items(),key=lambda v:-v[1])[:25]);print('BOUNDS',t.min((0,1)),t.max((0,1)))
