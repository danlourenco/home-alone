"""Buzz pilot: door-normalized wall rectification, not metric photogrammetry.
Run python3 art/home_alone/references/buzz-poc/fit.py.
Coordinates manually read from original 1920x1080 Marina frames; no image mutation.
Door aspect is a sensitivity parameter, not a measured standard.
"""
import json
from pathlib import Path
import cv2
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation

HERE = Path(__file__).parent
DOOR = np.array([[625,109],[945,111],[945,888],[625,891]], float)
POSTER_558 = np.array([[999,197],[1154,199],[1151,434],[999,434]], float)
POSTER_556 = np.array([[450,217],[645,228],[650,508],[455,510]], float)
POSTER_560 = np.array([[1216,158],[1368,157],[1365,379],[1216,381]], float)

def project(h, points):
    p=np.c_[np.asarray(points),np.ones(len(points))]@h.T
    return p[:,:2]/p[:,2:]

def wall_transfer(second, left):
    """Match upper wall only: avoid bed/shelves, whose different depth biases a planar fit."""
    a=cv2.imread(str(HERE/'tour558.jpg'),0)
    b=cv2.imread(str(HERE.parent/'buzz-bedroom'/second),0)
    sift=cv2.SIFT_create(nfeatures=8000)
    ma=np.zeros(a.shape,np.uint8);ma[:340,620:]=255
    mb=np.zeros(b.shape,np.uint8);mb[:340,left:1550 if left==0 else 1920]=255
    ka,da=sift.detectAndCompute(a,ma);kb,db=sift.detectAndCompute(b,mb)
    good=[x for x,y in cv2.BFMatcher().knnMatch(da,db,k=2) if x.distance<.7*y.distance]
    pa=np.float32([ka[x.queryIdx].pt for x in good]);pb=np.float32([kb[x.trainIdx].pt for x in good])
    h,mask=cv2.findHomography(pb,pa,cv2.RANSAC,2)
    keep=mask.ravel().astype(bool)
    if keep.sum()<20: raise RuntimeError('Insufficient common-wall matches')
    return h,dict(inliers=int(keep.sum()),matches=len(good),rms_pixels=float(np.sqrt(np.mean(np.sum((project(h,pb[keep])-pa[keep])**2,axis=1)))),source_pixels=pb[keep].tolist(),anchor_pixels=pa[keep].tolist())

def solve(aspect=.42):
    target=np.array([[0,1],[aspect,1],[aspect,0],[0,0]],float)
    h558,_=cv2.findHomography(DOOR,target,0)
    poster=project(h558,POSTER_558)
    t556,stats556=wall_transfer('tour556.jpg',0)
    t560,stats560=wall_transfer('tour560.jpg',880)
    h556=h558@t556
    h560=h558@t560
    # Door corners in560 are independent manually identified held-out landmarks.
    held=project(h560,[[877,76],[1165,76],[1165,794],[877,794]])
    left=project(h558,[[568,800]])[0,0]
    right=project(h556,[[1442,700]])[0,0]
    head=project(h558,[[1182,410],[1593,410]])[:,0]
    head560=project(h560,[[1390,357],[1808,358]])[:,0]
    return dict(door_aspect=aspect,wall_left=left,wall_right=right,
        wall_width=right-left,door_left=-left,door_width=aspect,
        head_left_apparent=head[0]-left,head_width_apparent=head[1]-head[0],
        door_to_head_apparent=head[0]-aspect,
        head_width_560_apparent=head560[1]-head560[0],
        transfer556=stats556,transfer560=stats560,
        held_out_door_560=held.tolist(),held_out_corner_rms_units=float(np.sqrt(np.mean(np.sum((held-target)**2,axis=1)))),
        h558=h558.tolist(),h556=h556.tolist(),h560=h560.tolist())

if __name__=='__main__':
    # Coordinate transform regression: a known synthetic rectangle recovers exactly.
    known=np.array([[0,0],[2,0],[2,3],[0,3]],float)
    h=np.array([[1.2,.2,10],[.1,1.1,15],[.002,.004,1.]])
    recovered,_=cv2.findHomography(project(h,known),known,0)
    assert np.max(np.abs(project(recovered,project(h,known))-known))<1e-5
    results=[solve(a) for a in [.38,.42,.46]]
    (HERE/'fit-results.json').write_text(json.dumps(dict(method='planar rectification; door height=1',results=results),indent=2)+'\n')
    r=results[1]
    study=dict(door_height=1.,door_width=.42,room_width=r['wall_width'],room_depth=2.1,room_height=1.18,
        door_left=r['door_left'],bed_left=r['head_left_apparent'],bed_width=r['head_width_apparent'],bed_length=.98,
        note='Width inferred by wall rectification. Bed apparent width includes unresolved parallax. Depth, height and bed length are provisional PoC assumptions, not recovered dimensions.')
    world=np.c_[np.array([[study['door_left'],1],[study['door_left']+.42,1],[study['door_left']+.42,0],[study['door_left'],0]]),np.zeros(4)]
    def camera_residual(c):
        p=(world-c[:3])@Rotation.from_euler('YXZ',c[3:],degrees=True).as_matrix()
        f=1080/(2*np.tan(np.deg2rad(60)/2))
        return (np.c_[960+f*p[:,0]/p[:,2],540-f*p[:,1]/p[:,2]]-DOOR).ravel()
    camera=least_squares(camera_residual,[.5,.65,-1.2,0,0,0],bounds=([-2,0,-5,-35,-35,-5],[3,2,-.3,35,35,5]))
    study['camera']=camera.x.tolist();study['vertical_fov']=60
    study['door_camera_rms_pixels']=float(np.sqrt(np.mean(camera.fun**2)))
    (HERE/'study.json').write_text(json.dumps(study,indent=2)+'\n')
    for r in results:
        print({k:round(r[k],4) for k in ['door_aspect','wall_width','door_to_head_apparent','head_width_apparent','head_width_560_apparent','held_out_corner_rms_units']})
