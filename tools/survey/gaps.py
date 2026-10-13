import cv2, numpy as np, sys, json
mask=cv2.imread(sys.argv[1],0)>0
walls=json.load(open(sys.argv[2]))
for name,(kind,b0,b1,lo,hi) in walls.items():
    if kind=='v': prof=mask[lo:hi,b0:b1].mean(1)   # along y
    else: prof=mask[b0:b1,lo:hi].mean(0)           # along x
    off=prof<0.35; runs=[];i=0
    while i<len(off):
        if off[i]:
            j=i
            while j<len(off) and off[j]: j+=1
            if j-i>=12: runs.append((lo+i,lo+j-1,j-i))
            i=j
        else: i+=1
    print(f"{name:22s} {kind} band[{b0}-{b1}] span {lo}-{hi} openings:",runs)
