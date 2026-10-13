import cv2, numpy as np, sys, json
mask=cv2.imread(sys.argv[1],0)>0
probes=json.load(open(sys.argv[2]))
res={}
for name,(kind,a0,a1,approx) in probes.items():
    if kind=='h':   # horizontal wall: average mask over columns a0..a1, scan rows
        prof=mask[:,a0:a1].mean(1)
    else:           # vertical wall: average over rows a0..a1, scan columns
        prof=mask[a0:a1,:].mean(0)
    on=prof>0.5
    # find runs
    runs=[];i=0
    while i<len(on):
        if on[i]:
            j=i
            while j<len(on) and on[j]: j+=1
            runs.append((i,j-1)); i=j
        else: i+=1
    if not runs: res[name]=None; print(name,'NONE'); continue
    best=min(runs,key=lambda r: min(abs(r[0]-approx),abs(r[1]-approx),abs((r[0]+r[1])/2-approx)))
    res[name]={'kind':kind,'edge0':int(best[0]),'edge1':int(best[1]),'thick':int(best[1]-best[0]+1),'center':(best[0]+best[1])/2}
    print(f"{name:28s} {kind} band {best[0]}-{best[1]} thick {best[1]-best[0]+1} (approx {approx})")
json.dump(res,open(sys.argv[3],'w'),indent=1)
