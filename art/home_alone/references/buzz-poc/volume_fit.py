"""Joint multi-depth camera fit. Includes headboard and nearer footpost."""
import json
from pathlib import Path
import cv2
import numpy as np
from scipy.optimize import least_squares
from fit import project
P=Path(__file__).parent
r=json.loads((P/'fit-results.json').read_text())['results'][1]
frames=[556,558,560]
door2={n:project(np.linalg.inv(r[f'h{n}']),[[0,1],[.42,1],[.42,0],[0,0]]) for n in frames}
heads={556:np.array([[687,477],[1125,470.]]),558:np.array([[1182,410],[1593,410.]]),560:np.array([[1390,357],[1808,358.]])}

def solve(fov,aspect):
    f=540/np.tan(np.deg2rad(fov)/2);k=np.array([[f,0,960],[0,f,540],[0,0,1.]])
    world=np.array([[0,1,0],[aspect,1,0],[aspect,0,0],[0,0,0]],float)
    cams=[]
    for n in frames:
        _,rv,t=cv2.solvePnP(world,door2[n],k,None)
        cams.extend([*rv.ravel(),*t.ravel()])
    initial=[f,aspect,.70,.52,.62,.04,*cams,.70,.35,1.1]
    def residual(v):
        f,a,x,w,y,z=v[:6];k=np.array([[f,0,960],[0,f,540],[0,0,1.]])
        obj=np.array([[0,1,0],[a,1,0],[a,0,0],[0,0,0],[x,y,z],[x+w,y,z]],float)
        out=[]
        for i,n in enumerate(frames):
            cam=v[6+i*6:12+i*6]
            im=cv2.projectPoints(obj,cam[:3],cam[3:],k,None)[0].reshape(-1,2)
            out.extend((im-np.r_[door2[n],heads[n]]).ravel())
            if n in [556,560]:
                foot=cv2.projectPoints(np.array([v[24:27]]),cam[:3],cam[3:],k,None)[0].reshape(2)
                out.extend(foot-np.array({556:[1169,1011],560:[1652,672]}[n]))
        return np.array(out)
    fit=least_squares(residual,initial,bounds=([400,.32,.3,.25,.4,0]+[-np.inf]*18+[0,0,.1],[2000,.55,1.2,.9,.9,.30]+[np.inf]*18+[2,1,1.8]),max_nfev=1500)
    v=fit.x
    return dict(rms_pixels=float(np.sqrt(np.mean(fit.fun**2))),fov=float(np.rad2deg(2*np.arctan(540/v[0]))),door_aspect=float(v[1]),head_left=float(v[2]),head_width=float(v[3]),head_height=float(v[4]),head_depth=float(v[5]),success=bool(fit.success),parameters=v.tolist(),residuals=fit.fun.tolist())
if __name__=='__main__':
    out=[solve(f,a) for f,a in [(45,.38),(60,.42),(75,.46)]]
    assert all(v['success'] for v in out)
    assert np.ptp([v['head_width'] for v in out])<1e-4, 'Starting-point solutions diverged'
    (P/'volume-results.json').write_text(json.dumps(out,indent=2)+'\n')
    for v in out:print({k:v[k] for k in ['rms_pixels','fov','door_aspect','head_width','head_depth','success']})
