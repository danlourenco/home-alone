"""Top-down density plot of a COLMAP TXT model; up = mean camera up vector.
usage: python3 tools/sfm/topdown.py <txt_model_dir> <out.png>"""
import sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def quat_to_R(w, x, y, z):
    return np.array([[1-2*(y*y+z*z), 2*(x*y-w*z), 2*(x*z+w*y)],
                     [2*(x*y+w*z), 1-2*(x*x+z*z), 2*(y*z-w*x)],
                     [2*(x*z-w*y), 2*(y*z+w*x), 1-2*(x*x+y*y)]])


d, out = sys.argv[1], sys.argv[2]
lines = [l for l in open(f"{d}/images.txt") if not l.startswith("#")][::2]
centers, ups, names = [], [], []
for l in lines:
    f = l.split()
    R = quat_to_R(*map(float, f[1:5])); t = np.array(list(map(float, f[5:8])))
    centers.append(-R.T @ t); ups.append(-R.T @ [0, 1, 0]); names.append(int(f[-1][2:7]))
centers, names = np.array(centers), np.array(names)
up = np.mean(ups, axis=0); up /= np.linalg.norm(up)
pts = np.array([list(map(float, l.split()[1:4])) for l in open(f"{d}/points3D.txt") if not l.startswith("#")])
a = np.cross(up, [1, 0, 0]); a /= np.linalg.norm(a); b = np.cross(up, a)
h = pts @ up
keep = h < np.percentile(h, 97)  # drop ceiling clutter so walls read in plan
P, C = np.c_[pts @ a, pts @ b][keep], np.c_[centers @ a, centers @ b]
plt.figure(figsize=(10, 10)); plt.hexbin(P[:, 0], P[:, 1], gridsize=220, bins="log", cmap="Greys", mincnt=1)
sc = plt.scatter(C[:, 0], C[:, 1], c=names, cmap="viridis", s=8); plt.colorbar(sc, label="frame #")
plt.gca().set_aspect("equal"); plt.title(f"{d}: {len(pts)} pts, {len(C)} cams (units arbitrary)")
plt.savefig(out, dpi=110, bbox_inches="tight")
