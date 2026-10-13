"""Check a joint p1/p2 model: shared points, which frames carry the link, and camera heights.
usage: uv run --with numpy python -I tools/sfm/link_check.py <model_txt_dir>"""
import sys
import numpy as np


def quat_to_R(w, x, y, z):
    return np.array([[1-2*(y*y+z*z), 2*(x*y-w*z), 2*(x*z+w*y)],
                     [2*(x*y+w*z), 1-2*(x*x+z*z), 2*(y*z-w*x)],
                     [2*(x*z-w*y), 2*(y*z+w*x), 1-2*(x*x+y*y)]])


d = sys.argv[1]
lines = [l for l in open(f"{d}/images.txt") if not l.startswith("#")]
cams, seen = {}, {}
for head, obs in zip(lines[::2], lines[1::2]):
    f = head.split(); name = f[-1]; src = name[:2]
    R = quat_to_R(*map(float, f[1:5])); t = np.array(list(map(float, f[5:8])))
    cams[name] = (-R.T @ t, -R.T @ [0, 1, 0])
    for pid in obs.split()[2::3]:
        if pid != "-1":
            seen.setdefault(pid, {"p1": set(), "p2": set()})[src].add(name)
shared = {p: s for p, s in seen.items() if s["p1"] and s["p2"]}
f1 = sorted({n for s in shared.values() for n in s["p1"]}); f2 = sorted({n for s in shared.values() for n in s["p2"]})
print(f"points: {len(seen)}, seen by BOTH videos: {len(shared)}")
print(f"link frames p1: {len(f1)} ({f1[0]}..{f1[-1]})" if f1 else "no p1 link frames")
print(f"link frames p2: {len(f2)} ({f2[0]}..{f2[-1]})" if f2 else "no p2 link frames")
# Heights along the mean camera-up direction; Part 1 starts at foyer level.
up = np.mean([u for _, u in cams.values()], axis=0); up /= np.linalg.norm(up)
h = {n: c @ up for n, (c, _) in cams.items()}
p1 = sorted((n for n in h if n.startswith("p1")))
foyer = np.median([h[n] for n in p1[:15]]); landing = np.median([h[n] for n in p1[-15:]])
upper = np.median([h[n] for n in h if n.startswith("p2")])
climb = landing - foyer
print(f"camera height (model units): foyer {0:.2f}, end of p1 climb {climb:.2f}, upper hall {upper - foyer:.2f}")
print(f"upper hall / p1 climb = {(upper - foyer) / climb:.2f}  (expect >1: upper floor above the landing)")
