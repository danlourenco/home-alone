"""Fit upper door AND rail; profile the crosswalk edge without editing Unity."""
import json
import numpy as np
from scipy.optimize import least_squares
from fit import views, project, HERE

v=views['upper']
# Top of rail at the turn, and the wall end of the transverse rail.
# Imported object204 world vertices bracket the top centre at y6.271,z4.6265.
# Film endpoint near the arch is less certain: use 8px versus 3px at door/corner.
world=np.array(v['world']+[[2.689,6.271,4.6265],[-.967,6.271,4.6265]])
pixels=np.array(v['pixels']+[[429,310],[859,318]])
sigma=np.array([3]*8+[8])[:,None]

def return_error(delta):
    direction=np.array([-49.,56.]);direction/=np.linalg.norm(direction)
    return np.array([(delta[0]*direction[1]-delta[1]*direction[0])/5,
                     min(0,float(delta@direction))/5])

def solve(dz, corner_x=2.689):
    points=world.copy();points[-2:,2]+=dz;points[-2,0]=corner_x
    def residual(c):
        predicted=project(points,c[:6],c[6],v['size'])
        # The return rail must recede toward the image LEFT from the corner.
        # Its visible segment has no identifiable endpoint: constrain its line,
        # not an invented correspondence along its length.
        tip=project([[corner_x,6.270,7.482]],c[:6],c[6],v['size'])[0]
        delta=tip-predicted[-2]
        return np.r_[((predicted-pixels)/sigma).ravel(),return_error(delta)]
    best=None
    for fov in [40,60,80,100]:
        result=least_squares(residual,
             [0,6.9,8,170,0,0,fov],
             bounds=([-4,5.3,4.8,110,-30,-3,25],[5,9,16,220,30,3,115]),max_nfev=2000)
        if best is None or result.cost<best.cost:best=result
    predicted=project(points,best.x[:6],best.x[6],v['size'])
    return dict(rail_z=4.6265+dz, corner_x=corner_x, camera=best.x.tolist(), weighted_rms=float(np.sqrt(np.mean(best.fun**2))),
                door_rms_px=float(np.sqrt(np.mean(np.sum((predicted[:7]-pixels[:7])**2,axis=1)))),
                rail_errors_px=np.linalg.norm(predicted[-2:]-pixels[-2:],axis=1).tolist(),
                projected=predicted.tolist())

if __name__=='__main__':
    assert np.linalg.norm(return_error(np.array([-49.,56.])))<1e-10
    assert np.linalg.norm(return_error(np.array([49.,-56.])))>1
    results=[solve(float(dz),x) for x in [1.2,1.6,2.,2.4,2.689] for dz in [-.75,0,.75]]
    (HERE/'joint-results.json').write_text(json.dumps(dict(world=world.tolist(),pixels=pixels.tolist(),results=results),indent=2)+'\n')
    for r in results: print(r['corner_x'],round(r['rail_z'],3),round(r['weighted_rms'],2),np.round(r['camera'],3).tolist(),np.round(r['rail_errors_px'],1))
