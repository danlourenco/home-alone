import bpy, numpy as np
from pathlib import Path
bpy.ops.wm.read_factory_settings(use_empty=True)
root=Path(__file__).resolve().parents[2]
bpy.ops.import_scene.gltf(filepath=str(root/'assets/home_alone/online_home_alone/HOME_ALONE_FINAL.glb'))
points=[]; edges=[]; segments={str(z):[] for z in [1.5,4.5,6.3]}
for o in bpy.context.scene.objects:
 if o.type!='MESH': continue
 v=np.array([tuple(o.matrix_world @ x.co) for x in o.data.vertices])
 # Original Blender XY plan; same transform used by ExteriorShell.cs, vertical untouched except scale.
 v=v*.83+np.array([9.445,2.208,0.])
 points.append(v)
 edges.append(v[np.array([tuple(e.vertices) for e in o.data.edges])])
 o.data.calc_loop_triangles()
 tri=np.array([t.vertices for t in o.data.loop_triangles]); tv=v[tri]
 for z in [1.5,4.5,6.3]:
  cut=tv[(tv[:,:,2].min(1)<z)&(tv[:,:,2].max(1)>z)]
  for t in cut:
   hit=[]
   for a,b in [(t[0],t[1]),(t[1],t[2]),(t[2],t[0])]:
    if (a[2]<z)!=(b[2]<z): hit.append(a+(b-a)*(z-a[2])/(b[2]-a[2]))
   if len(hit)==2: segments[str(z)].append(np.array(hit)[:,:2])
p=np.concatenate(points)
np.savez_compressed(root/'art/home_alone/references/reconciliation/exterior-slices.npz',points=p,edges=np.concatenate(edges),**{k:np.array(v) for k,v in segments.items()})
print('EXTRACT',len(p),p.min(0),p.max(0))
