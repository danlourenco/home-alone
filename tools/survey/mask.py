import cv2, numpy as np, sys
src,out=sys.argv[1],sys.argv[2]
im=cv2.imread(src); hsv=cv2.cvtColor(im,cv2.COLOR_BGR2HSV)
mask=((hsv[...,2]>205)&(hsv[...,1]<35)).astype(np.uint8)*255
mask=cv2.morphologyEx(mask,cv2.MORPH_OPEN,np.ones((3,3),np.uint8))
cv2.imwrite(out,mask)
vis=im.copy(); vis[mask>0]=(0,0,255)
cv2.imwrite(out.replace('.png','_vis.png'),vis)
