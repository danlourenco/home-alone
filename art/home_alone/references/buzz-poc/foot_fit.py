"""Bed footprint from shared footpost; conditional on existing camera calibration."""
import json
from pathlib import Path
import cv2
import numpy as np
from scipy.optimize import least_squares
P=Path(__file__).parent
v=json.loads((P/'rigid-results.json').read_text())[0]['parameters']
f,a,hx,hw,hy,hz=v[:6];k=np.array([[f,0,960],[0,f,540],[0,0,1.]])
# Same left footpost finial centre, manually picked in original 1920x1080 frames.
observed={556:[1169,1011],560:[1652,672]}

def predict(point,frame):
    idx={556:6,558:12,560:18}[frame];cam=np.array(v[idx:idx+6])
    return cv2.projectPoints(np.array([point],float),cam[:3],cam[3:],k,None)[0].reshape(2)

def fit(obs):
    result=least_squares(lambda p:np.concatenate([predict(p,n)-q for n,q in obs.items()]),[hx,.42,1.],bounds=([0,0,.1],[2,1,1.8]))
    return result.x,result.fun
if __name__=='__main__':
    known=np.array([hx,.4,1.1]);recovered,_=fit({n:predict(known,n) for n in observed});assert np.max(np.abs(recovered-known))<1e-6
    pt,residual=fit(observed)
    # Truly withheld 559 pose obtained using door only, as in apply_joint.py.
    door=np.array([[835,83],[1123,81],[1123,821],[835,818]],float)
    world=np.array([[0,1,0],[a,1,0],[a,0,0],[0,0,0]],float)
    _,rv,t=cv2.solvePnP(world,door,k,None)
    predicted=cv2.projectPoints(np.array([pt]),rv,t,k,None)[0].reshape(2)
    withheld=np.array([1623,694])
    out=dict(observed=observed,footpost_world=pt.tolist(),post_to_post_length=float(pt[2]-hz),
             lateral_misalignment=float(pt[0]-hx),fit_rms_pixels=float(np.sqrt(np.mean(residual**2))),
             withheld559_observed=withheld.tolist(),withheld559_predicted=predicted.tolist(),
             withheld559_error_pixels=float(np.linalg.norm(predicted-withheld)),
             note='Free 3D point triangulation; bed alignment NOT forced. All values conditional on fitted cameras. Finial centres approximate.')
    (P/'foot-results.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
