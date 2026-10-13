"""Export the selected bed-wall candidate; does not edit the main house."""
import json
from pathlib import Path
import cv2
import numpy as np
P=Path(__file__).parent
r=json.loads((P/'rigid-results.json').read_text())[0];v=r['parameters'];f,a,x,w,y,z=v[:6]
s=json.loads((P/'study-planar.json').read_text());scale=a/s['door_width']
s.update(room_width=s['room_width']*scale,door_left=s['door_left']*scale,door_width=a,bed_width=w,head_height=y,head_z=-z,vertical_fov=r['fov'])
s['bed_left']=s['door_left']+x
rot=cv2.Rodrigues(np.array(v[12:15]))[0];pos=-rot.T@np.array(v[15:18]);pos[0]+=s['door_left']
# OpenCV Y-up world has camera on positive Z. Reflect world Z for Unity room convention.
reflect=np.array([1,1,-1]);s['camera_position']=(pos*reflect).tolist();s['camera_forward']=(rot[2]*reflect).tolist();s['camera_up']=(-rot[1]*reflect).tolist()
s.pop('door_camera_rms_pixels',None)
s['joint_fit_rms_pixels']=r['rms_pixels']
s['note']='Joint bed-wall candidate. Head depth hits zero bound and is NOT recovered. Depth/height/bed length remain provisional.'
(P/'study.json').write_text(json.dumps(s,indent=2)+'\n')
k=np.array([[f,0,960],[0,f,540],[0,0,1.]])
world=np.array([[0,1,0],[a,1,0],[a,0,0],[0,0,0]],float)
door=np.array([[835,83],[1123,81],[1123,821],[835,818]],float)
_,rv,t=cv2.solvePnP(world,door,k,None)
head=np.array([[x,y,z],[x+w,y,z]]);pred=cv2.projectPoints(head,rv,t,k,None)[0].reshape(-1,2);obs=np.array([[1355,367],[1770,368]])
result=dict(source='tour559.jpg; withheld from joint geometry fit',door_pixels=door.tolist(),head_observed=obs.tolist(),head_predicted=pred.tolist(),head_error_pixels=np.linalg.norm(pred-obs,axis=1).tolist(),note='Only camera pose fitted from door; headposts withheld. Approximate manual landmarks.')
assert max(result['head_error_pixels'])<10, 'Held-out headpost check regressed beyond 10px'
(P/'heldout559.json').write_text(json.dumps(result,indent=2)+'\n')
print(result['head_error_pixels'])
