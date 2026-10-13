import cv2, numpy as np, sys, json
src,vpfile,out=sys.argv[1],sys.argv[2],sys.argv[3]
ky=float(sys.argv[4]) if len(sys.argv)>4 else 1.0   # extra Y stretch (aspect calibration)
im=cv2.imread(src); H,W=im.shape[:2]; xv,yv=np.load(vpfile)
y0=H*0.6; s0=y0-yv
# forward map: x'=(x-xv)*s0/s+xv ; y'=(y0+s0-s0^2/s - y0)*ky + y0  where s=y-yv
def fwd(x,y):
    s=y-yv; return (x-xv)*s0/s+xv, ((y0+s0-s0*s0/s)-y0)*ky+y0
# output bounds
cs=np.array([fwd(x,y) for x in (0,W) for y in (0,H)]); x0,y0o=cs.min(0); x1,y1=cs.max(0)
OW,OH=int(x1-x0)+1,int(y1-y0o)+1
# inverse map for remap: given x',y' -> s from y': y'=((y0+s0-s0^2/s)-y0)*ky+y0 -> s0^2/s = s0 - (y'-y0)/ky -> s = s0^2/(s0-(y'-y0)/ky)
xs=np.arange(OW)+x0; ys=np.arange(OH)+y0o
XX,YY=np.meshgrid(xs,ys)
den=s0-(YY-y0)/ky; den[den<=1]=1
s=s0*s0/den; y=s+yv; x=(XX-xv)*s/s0+xv
rect=cv2.remap(im,x.astype(np.float32),y.astype(np.float32),cv2.INTER_LINEAR,borderValue=(0,0,0))
cv2.imwrite(out,rect)
json.dump({'x0':float(x0),'y0':float(y0o),'xv':float(xv),'yv':float(yv),'s0':float(s0),'yref':float(y0),'ky':ky,'W':OW,'H':OH},open(out+'.json','w'))
print(out,OW,OH)
