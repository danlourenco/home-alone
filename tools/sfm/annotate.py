"""Annotated top-down of model 2 with frame thumbnails at camera poses.
usage: uv run --with numpy --with matplotlib python -I tools/sfm/annotate.py sfm-work/buzz-hall"""
import sys, numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
ws = sys.argv[1]; d = f"{ws}/txt/2"
def R_(w,x,y,z): return np.array([[1-2*(y*y+z*z),2*(x*y-w*z),2*(x*z+w*y)],[2*(x*y+w*z),1-2*(x*x+z*z),2*(y*z-w*x)],[2*(x*z-w*y),2*(y*z+w*x),1-2*(x*x+y*y)]])
cams = {}
ups = []
for l in [l for l in open(f"{d}/images.txt") if not l.startswith("#")][::2]:
    f = l.split(); R = R_(*map(float,f[1:5])); t = np.array(list(map(float,f[5:8])))
    cams[int(f[-1][2:7])] = (-R.T@t, R.T@[0,0,1]); ups.append(-R.T@[0,1,0])
up = np.mean(ups,0); up/=np.linalg.norm(up); a=np.cross(up,[1,0,0]); a/=np.linalg.norm(a); b=np.cross(up,a)
pr = lambda v: np.array([v@a, v@b])
pts = np.array([list(map(float,l.split()[1:4])) for l in open(f"{d}/points3D.txt") if not l.startswith("#")])
h = pts@up; P = np.c_[pts@a, pts@b][h<np.percentile(h,97)]
fig, ax = plt.subplots(figsize=(14,11))
ax.hexbin(P[:,0],P[:,1],gridsize=220,bins="log",cmap="Greys",mincnt=1)
ks = sorted(cams); C = np.array([pr(cams[k][0]) for k in ks])
gap = np.where(np.diff(ks)>5)[0]+1
for seg in np.split(C,gap): ax.plot(seg[:,0],seg[:,1],color="tab:blue",lw=2.5,alpha=.7)
ax.text(-3.6,-3.2,"BUZZ'S ROOM",fontsize=18,weight="bold",color="tab:red",ha="center")
ax.text(4.2,1.9,"UPPER HALL",fontsize=18,weight="bold",color="tab:red",ha="center")
ax.text(-15.5,11.5,"Grey dots = 3D points on walls & furniture, seen from above.\nBlue line = path the camera flew. Thumbnails = what it saw there\n(arrow = direction it was facing).",fontsize=11,va="top",bbox=dict(fc="w",ec="0.7"))
spots = [(5,(-12.5,-7.5)),(60,(-12.5,1.5)),(90,(-3,-11.5)),(150,(12.5,-4)),(215,(4,9.5))]
for k,pos in spots:
    k = min(ks,key=lambda x:abs(x-k)); c, fwd = cams[k]; c2 = pr(c); f2 = pr(fwd); f2/=np.linalg.norm(f2)
    ax.annotate("",xy=c2+f2*1.2,xytext=c2,arrowprops=dict(arrowstyle="-|>",color="tab:orange",lw=2.5))
    ax.plot(*c2,"o",color="tab:orange",ms=8)
    im = plt.imread(f"{ws}/images/f_{k:05d}.jpg")[::6,::6]
    ax.add_artist(AnnotationBbox(OffsetImage(im,zoom=0.42),pos,xybox=pos,boxcoords="data",arrowprops=dict(arrowstyle="-",color="tab:orange"),xycoords="data"))
    ax.annotate("",xy=c2,xytext=pos,arrowprops=dict(arrowstyle="-",color="tab:orange",ls="--"))
ax.set_aspect("equal"); ax.set_xlim(-16,16); ax.set_ylim(-14,12); ax.set_xticks([]); ax.set_yticks([])
ax.set_title("Buzz's room + upper hall, reconstructed from Marina's tour video (top-down, scale not set yet)",fontsize=13)
fig.savefig(f"{ws}/topdown-annotated.png",dpi=100,bbox_inches="tight")
