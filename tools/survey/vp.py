import cv2, numpy as np, sys
src=sys.argv[1]; out=sys.argv[2]
im=cv2.imread(src); hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV)
# wall tops: bright, low saturation
mask=((hsv[...,2]>200)&(hsv[...,1]<40)).astype(np.uint8)*255
mask=cv2.morphologyEx(mask,cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
edges=cv2.Canny(mask,50,150)
lines=cv2.HoughLinesP(edges,1,np.pi/720,threshold=60,minLineLength=120,maxLineGap=8)
vert=[];horiz=[]
for l in lines[:,0]:
    x1,y1,x2,y2=l; ang=np.degrees(np.arctan2(y2-y1,x2-x1))%180
    if 70<ang<110: vert.append(l)
    elif ang<8 or ang>172: horiz.append(l)
print('lines',len(lines),'vert',len(vert),'horiz',len(horiz))
# least squares vanishing point for vertical family: minimize distance to lines
A=[];b=[]
for x1,y1,x2,y2 in vert:
    dx,dy=x2-x1,y2-y1; n=np.array([dy,-dx],float); n/=np.linalg.norm(n)
    A.append(n); b.append(n@np.array([x1,y1],float))
A=np.array(A);b=np.array(b)
vp,res,_,_=np.linalg.lstsq(A,b,rcond=None)
# robust refit: drop worst 30%
d=np.abs(A@vp-b); keep=d<np.percentile(d,70)
vp2,_,_,_=np.linalg.lstsq(A[keep],b[keep],rcond=None)
print('vp initial',vp,'refit',vp2,'resid px median',np.median(np.abs(A[keep]@vp2-b[keep])))
# horizontal family mean angle
angs=[np.degrees(np.arctan2(y2-y1,x2-x1)) for x1,y1,x2,y2 in horiz]
angs=[(a+90)%180-90 for a in angs]
print('horiz angle mean',np.mean(angs),'std',np.std(angs))
vis=im.copy()
for x1,y1,x2,y2 in vert: cv2.line(vis,(x1,y1),(x2,y2),(0,0,255),2)
for x1,y1,x2,y2 in horiz: cv2.line(vis,(x1,y1),(x2,y2),(0,255,0),2)
cv2.imwrite(out,vis)
np.save(out+'.vp.npy',vp2)
