"""Test whether the bed-wall views provide a usable stereo baseline.
Assumed intrinsics and door aspect; outputs diagnostics, never changes the scene.
"""
import json
from pathlib import Path
import cv2
import numpy as np
from fit import project
P=Path(__file__).parent

def check(r,fov):
    f=540/np.tan(np.deg2rad(fov)/2)
    k=np.array([[f,0,960],[0,f,540],[0,0,1.]])
    a=r['door_aspect']; world=np.array([[0,1,0],[a,1,0],[a,0,0],[0,0,0]],float)
    poses={}
    for frame in [558,560]:
        im=project(np.linalg.inv(r[f'h{frame}']),world[:,:2])
        ok,rv,t=cv2.solvePnP(world,im,k,None,flags=cv2.SOLVEPNP_ITERATIVE)
        assert ok
        rot=cv2.Rodrigues(rv)[0]
        poses[frame]=(rot,t,-rot.T@t,k@np.c_[rot,t])
    p=np.array([[1182,410],[1593,410]],float)
    q=np.array([[1390,357],[1808,358]],float)
    ra,ta,ca,pa=poses[558];rb,tb,cb,pb=poses[560]
    x=cv2.triangulatePoints(pa,pb,p.T,q.T);x=(x[:3]/x[3]).T
    va=x-ca.ravel();vb=x-cb.ravel()
    angle=np.rad2deg(np.arccos(np.clip(np.sum(va*vb,axis=1)/np.linalg.norm(va,axis=1)/np.linalg.norm(vb,axis=1),-1,1)))
    def reproj(mat):
        pts=np.c_[x,np.ones(2)]@mat.T
        return pts[:,:2]/pts[:,2:]
    return dict(fov=fov,door_aspect=a,baseline=float(np.linalg.norm(ca-cb)),headpost_world=x.tolist(),
        headpost_width=float(np.linalg.norm(x[1]-x[0])),ray_angles_degrees=angle.tolist(),
        reprojection_rms_pixels=float(np.sqrt(np.mean(np.r_[reproj(pa)-p,reproj(pb)-q]**2))))

if __name__=='__main__':
    # A known stereo pair must recover a point at z=4.
    pa=np.c_[np.eye(3),np.zeros(3)];pb=np.c_[np.eye(3),[-1,0,0]]
    t=cv2.triangulatePoints(pa,pb,np.array([[.125],[.05]]),np.array([[-.125],[.05]]));t=t[:3]/t[3]
    assert np.max(np.abs(t.ravel()-[.5,.2,4]))<1e-6
    rs=json.loads((P/'fit-results.json').read_text())['results']
    out=[check(r,f) for r in rs for f in [50,60,70]]
    (P/'parallax-results.json').write_text(json.dumps(out,indent=2)+'\n')
    for r in out: print({k:r[k] for k in ['fov','door_aspect','baseline','headpost_width','ray_angles_degrees','reprojection_rms_pixels']})
