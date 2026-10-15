# Parents x_max twin window from two frames (Part 2 182 s, 240 s): joint 1-D projective fit.
# world u along the wall from the screen (z_min) corner, unit = one sash glass width
import numpy as np
from scipy.optimize import least_squares
f182 = {"A0": 260, "A1": 500, "B0": 510, "B1": 800, "L": 1105}
f240 = {"O": 872, "A0": 1150, "A1": 1320, "B0": 1395, "B1": 1650}
def world(a, m, L):
    return {"O": 0, "A0": a, "A1": a + 1, "B0": a + 1 + m, "B1": a + 2 + m, "L": L}
def proj(p, u):  # x = (p0 u + p1) / (p2 u + 1)
    return (p[0] * u + p[1]) / (p[2] * u + 1)
def res(v):
    a, m, L = v[:3]; W = world(a, m, L)
    r = [proj(v[3:6], W[k]) - x for k, x in f182.items()] + [proj(v[6:9], W[k]) - x for k, x in f240.items()]
    return r
v0 = [1.0, 0.1, 6.0, 300, -40, 0.05, 280, 872, 0.0]
s = least_squares(res, v0)
a, m, L = s.x[:3]
print("residual px", np.round(s.fun, 1))
print(f"a={a:.2f} m={m:.2f} L={L:.2f} (sash units); window centre frac from screen corner {(a + 1 + m / 2) / L:.3f}; glass span frac {(2 + m) / L:.3f}")
