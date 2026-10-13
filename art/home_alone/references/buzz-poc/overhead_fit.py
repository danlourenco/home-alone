"""Normalized overhead footprint study. Does not recover metric aspect ratio.
Run from repository root: python3 art/home_alone/references/buzz-poc/overhead_fit.py
Manual landmarks are approximate; furniture heights introduce parallax.
"""
import json
from pathlib import Path
import cv2
import numpy as np
P=Path(__file__).parent
# Inner wall-top rectangle, clockwise from headwall/shelf corner, overhead50.jpg.
CORNERS=np.array([[1060,711],[1306,711],[1321,1014],[1065,1014]],float)

def normalized(points, corners=CORNERS):
    h,_=cv2.findHomography(corners,np.array([[0,0],[1,0],[1,1],[0,1]],float),0)
    p=np.c_[np.array(points),np.ones(len(points))]@h.T
    return p[:,:2]/p[:,2:]

if __name__=='__main__':
    assert np.max(np.abs(normalized(CORNERS)-[[0,0],[1,0],[1,1],[0,1]]))<1e-6
    landmarks={'bed_head_left':[1137,725],'bed_head_right':[1209,725],
               'bed_foot_left':[1134,848],'bed_foot_right':[1219,848],
               'dresser':[1268,875],'desk':[1166,989],
               'window_near_head':[1284,799],'window_near_desk':[1292,947],
               'third_window':[1271,1006]}
    vals=normalized(list(landmarks.values()))
    result=dict(source='Marina Part 2 00:50 overhead50.jpg',method='Wall-top quadrilateral mapped to unit square; aspect ratio remains unknown',
                wall_top_corners=CORNERS.tolist(),landmarks={k:dict(pixel=landmarks[k],normalized=v.tolist()) for k,v in zip(landmarks,vals)},
                limitation='Furniture and floor are below wall tops. These are apparent positions, not coplanar recovered coordinates.')
    # Sensitivity only: move each corner independently by up to 3px.
    rng=np.random.default_rng(0)
    samples=np.array([normalized(list(landmarks.values()),CORNERS+rng.uniform(-3,3,(4,2))) for _ in range(500)])
    result['corner_perturbation_max_normalized_change']=float(np.max(np.abs(samples-vals)))
    result['apparent_bed_depth_fraction']=float(vals[2:4,1].mean()-vals[:2,1].mean())
    (P/'overhead-results.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['apparent_bed_depth_fraction','corner_perturbation_max_normalized_change']},indent=2))
