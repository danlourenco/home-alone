"""Reproducible exploratory camera fits; no scene or source-image mutation.

Manual pixels are approximate (+/- 5px, upper film +/- 3px).
Treads correspond by counting down from the rear landing, not from the floor.
Absolute scale is inherited from Unity, not recovered from the images.
Run: python3 art/home_alone/references/foyer-calibration/fit/fit.py
"""
import json
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation

HERE = Path(__file__).parent

def treads(pairs):
    return [[side, 4.452 - i*.1964, 8.070-i*.2613]
            for i in range(len(pairs)) for side in [-.943, 1.170]]

entry = [[[932,160],[1240,152]],[[914,202],[1240,196]],
         [[893,250],[1239,244]],[[871,302],[1239,298]],
         [[845,361],[1237,355]],[[816,428],[1236,423]],
         [[783,504],[1233,499]],[[744,592],[1230,583]],
         [[699,699],[1227,689]],[[645,820],[1222,810]],
         [[580,971],[1217,963]]]
landing = [[[698,490],[1260,483]],[[665,612],[1297,603]],
           [[625,752],[1334,749]],[[576,935],[1383,931]]]
film = [[[216,119],[292,119]],[[208,128],[292,128]],
        [[201,136],[292,136]],[[193,145],[291,145]],
        [[185,155],[290,155]],[[176,168],[288,168]],
        [[166,181],[287,181]],[[155,196],[286,196]],
        [[143,213],[284,213]],[[129,233],[282,233]],
        [[114,255],[280,255]],[[95,281],[277,281]]]
views = {
    'film-entry': dict(size=[600,352], source='../../foyer-film/entry-staircase-reference.jpg',
                       world=treads(film), pixels=np.array(film).reshape(-1,2).tolist(),
                       initial=[0,3,0,0,-5,0]),
    'entry': dict(size=[1920,1080], source='../foyer338.jpg',
                  world=treads(entry), pixels=np.array(entry).reshape(-1,2).tolist(),
                  initial=[0,3,2,0,-5,0]),
    'landing': dict(size=[1920,1080], source='../landing346.jpg',
                    world=treads(landing), pixels=np.array(landing).reshape(-1,2).tolist(),
                    initial=[0,4.8,6,0,0,0],
                    held_out_world=[[-.967,4.452,10.665]],
                    held_out_pixels=[[797,438]]),
    # Visible upper door casing and inner door top, then knob. These are
    # authored reference-based fixtures: fit anchors, not independent dimensions.
    'upper': dict(size=[910,488], source='../../foyer-film/upstairs-film-quality-target.png',
                  world=[[2.8,7.92,1.8],[1.4,7.92,1.8],
                         [2.65,7.755,1.796],[1.55,7.755,1.796],
                         [2.65,7.17,1.796],[1.55,7.17,1.796],
                         [1.635,6.26,1.857]],
                  pixels=[[382,128],[510,128],[398,145],[496,145],
                          [398,200],[496,200],[486,294]],
                  initial=[1,6.9,7,180,0,0])
}

def project(world, camera, fov, size):
    p=np.asarray(world)-np.asarray(camera[:3])
    p=p @ Rotation.from_euler('YXZ', camera[3:], degrees=True).as_matrix()
    focal=size[1]/(2*np.tan(np.deg2rad(fov)/2))
    return np.column_stack((size[0]/2+focal*p[:,0]/p[:,2],
                            size[1]/2-focal*p[:,1]/p[:,2]))

def fit(view, fov, width=1):
    world=np.array(view['world'],float)
    if view is not views['upper']:
        world[:,0]=-.943+(world[:,0]+.943)*width
    initial=view['initial']
    bounds=([-10,-2,-15,initial[3]-65,-60,-15],
            [12,12,10,initial[3]+65,60,15])
    solve=least_squares(lambda c:(project(world,c,fov,view['size'])-
                                  view['pixels']).ravel(), initial,
                        bounds=bounds, max_nfev=3000)
    out=dict(camera=solve.x.tolist(), fov=fov, stair_width_factor=width,
             rms_pixel_distance=float(np.sqrt(np.mean(np.sum(solve.fun.reshape(-1,2)**2,axis=1)))),
             projected=project(world,solve.x,fov,view['size']).tolist())
    if 'held_out_world' in view:
        pred=project(view['held_out_world'],solve.x,fov,view['size'])
        out['held_out_projected']=pred.tolist()
        out['held_out_error_px']=float(np.linalg.norm(pred-view['held_out_pixels']))
    return out

if __name__=='__main__':
    assert np.allclose(project([[0,0,2],[1,0,2]],[0,0,0,0,0,0],90,[200,100]),
                       [[100,50],[125,50]])
    synthetic=dict(size=[1920,1080],world=views['entry']['world'],
                   initial=[0,3,2,0,-5,0])
    synthetic['pixels']=project(synthetic['world'],[.3,3.2,1.5,2,-8,1],60,synthetic['size'])
    assert fit(synthetic,60)['rms_pixel_distance']<.001
    results={name:[fit(view,fov,width) for width in ([.45,.55,.65,.75,.85,1,1.15] if name!='upper' else [1])
                   for fov in [40,60,80]] for name,view in views.items()}
    (HERE/'landmarks.json').write_text(json.dumps(views,indent=2)+'\n')
    (HERE/'results.json').write_text(json.dumps(results,indent=2)+'\n')
    for name,rows in results.items():
        for row in rows:
            print(name, 'width',row['stair_width_factor'],'fov',row['fov'],
                  'rms',round(row['rms_pixel_distance'],2),
                  'heldout',round(row.get('held_out_error_px',0),2),
                  'camera',np.round(row['camera'],3).tolist())
