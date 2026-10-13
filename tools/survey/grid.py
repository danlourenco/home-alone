import cv2,sys
src,out=sys.argv[1],sys.argv[2]; step=int(sys.argv[3]); crop=sys.argv[4] if len(sys.argv)>4 else None; zoom=float(sys.argv[5]) if len(sys.argv)>5 else 1
im=cv2.imread(src)
ox=oy=0
if crop:
    x,y,w,h=map(int,crop.split(',')); im=im[y:y+h,x:x+w]; ox,oy=x,y
if zoom!=1: im=cv2.resize(im,None,fx=zoom,fy=zoom,interpolation=cv2.INTER_CUBIC)
H,W=im.shape[:2]
for gx in range((ox//step)*step, ox+int(W/zoom)+1, step):
    px=int((gx-ox)*zoom)
    if 0<=px<W:
        big=gx%(step*5)==0; cv2.line(im,(px,0),(px,H),(255,255,0) if big else (0,200,200),2 if big else 1); cv2.putText(im,str(gx),(px+2,14),cv2.FONT_HERSHEY_SIMPLEX,0.45,(0,255,255),1)
for gy in range((oy//step)*step, oy+int(H/zoom)+1, step):
    py=int((gy-oy)*zoom)
    if 0<=py<H:
        big=gy%(step*5)==0; cv2.line(im,(0,py),(W,py),(255,255,0) if big else (0,200,200),2 if big else 1); cv2.putText(im,str(gy),(2,py+14),cv2.FONT_HERSHEY_SIMPLEX,0.45,(0,255,255),1)
cv2.imwrite(out,im)
