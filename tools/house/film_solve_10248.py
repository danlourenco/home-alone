"""film_solve_10248: the film camera for still 10248 (inner foyer facing the front door), solved from the door leaf, the sidelight
edges and the vestibule opening's far jamb edges; draws our walls, door assembly, stands, prints and sconces over the still and
back-projects the film's sconces onto the front wall (they sit at z 8.56 / 10.99, ~1.57 m).
  uv run --with numpy --with scipy --with pillow python -I tools/house/film_solve_10248.py <repo> <out.jpg>
"""
import json, sys
import numpy as np
from scipy.optimize import least_squares
from PIL import Image, ImageDraw
R = sys.argv[1]; OUT = sys.argv[2]
W, H = 1920, 1058
# correspondences on the vestibule's front wall (spec x, y up, z) <-> film 10248 pixels
P3 = np.array([[10.10, 1.898, 9.31], [10.10, 1.898, 10.121], [10.10, 0.0, 9.31], [10.10, 0.0, 10.121],   # door leaf corners
               [10.10, 1.898, 8.917], [10.10, 0.0, 8.917], [10.10, 1.898, 10.564], [10.10, 0.0, 10.564]])   # sidelight outer edges
P2 = np.array([[770, 97], [1130, 97], [770, 905], [1130, 905], [610, 97], [610, 905], [1290, 97], [1290, 905]], float)
JAMB = [(np.array([9.088, 1.0, 8.794]), 385), (np.array([9.088, 1.0, 10.443]), 1500)]   # opening's far jamb edges (vertical lines)

def proj(p, X):
    f, yaw, pitch, cx, cy, cz = p
    c = np.array([cx, cy, cz])
    fwd = np.array([np.cos(pitch) * np.cos(yaw), np.sin(pitch), np.cos(pitch) * np.sin(yaw)])   # spec space, yaw 0 = +x
    right = np.cross(fwd, [0, 1, 0]); right /= np.linalg.norm(right)   # image right = +z when looking +x
    up = np.cross(right, fwd)
    d = X - c; zc = d @ fwd
    return np.c_[W / 2 + f * (d @ right) / zc, H / 2 - f * (d @ up) / zc]

def res(p):
    r = (proj(p, P3) - P2).ravel().tolist()
    for X, u in JAMB: r.append(proj(p, X[None])[0, 0] - u)
    return r

best = min((least_squares(res, [f0, 0.0, 0.0, 7.0, 1.0, 9.7], bounds=([600, -0.6, -0.5, 4.0, 0.2, 8.0], [9000, 0.6, 0.5, 9.0, 2.2, 11.5])) for f0 in (1500, 2500, 3500, 5000)), key=lambda s: s.cost)
p = best.x; rms = np.sqrt(np.mean(np.square(res(p))))
print("camera f %.0f px, pos spec (%.2f, %.2f, %.2f), yaw %.1f, pitch %.1f deg, rms %.1f px" % (p[0], p[3], p[4], p[5], np.degrees(p[1]), np.degrees(p[2]), rms))

im = Image.open(f"{R}/0-homealone/full/homealone-movie-screencaps.com-10248.jpg").convert("RGB"); d = ImageDraw.Draw(im)
def box(x0, x1, y0, y1, z0, z1, col, w=3):
    V = np.array([[x, y, z] for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]); Q = proj(p, V)
    for i in range(8):
        for j in range(i + 1, 8):
            if bin(i ^ j).count("1") == 1: d.line([tuple(Q[i]), tuple(Q[j])], fill=col, width=w)
G = json.load(open(f"{R}/spec/geometry.json"))["ground"]
for wl in G["walls"]:   # grey-box walls near the front of the foyer (cyan)
    if wl["x"][1] >= 8.9 and wl["x"][0] <= 10.3 and wl["z"][1] >= 7.7 and wl["z"][0] <= 11.6 and wl["y"][1] - wl["y"][0] > 0.5:
        box(*wl["x"], *wl["y"], *wl["z"], (0, 255, 255), 2)
D = {q["name"]: q for q in json.load(open(f"{R}/spec/dressing/foyer.json"))["pieces"] if "x" in q}
for n in ("flower_stand_left", "flowers_left", "print_left", "flower_stand_right", "flowers_right", "print_right", "front_door", "sidelight_left", "sidelight_right"):
    q = D[n]; box(*q["x"], *q["y"], *q["z"], (255, 220, 0), 3)
for z in (8.73, 10.70):   # our sconces (backplate centre 1.62 m, on the vestibule's front wall)
    box(10.05, 10.13, 1.52, 1.82, z - 0.18, z + 0.18, (255, 0, 255), 4)
for u, v in ((440, 240), (1465, 240)):   # the film's sconces (backplate centres read on the still)
    d.ellipse([u - 18, v - 18, u + 18, v + 18], outline=(0, 255, 0), width=5)
im.save(OUT)
# where the film's sconces sit on our front wall plane (x = 10.10): back-project their pixels
def back(u, v, xw=10.10):
    f, yaw, pitch, cx, cy, cz = p; c = np.array([cx, cy, cz])
    fwd = np.array([np.cos(pitch) * np.cos(yaw), np.sin(pitch), np.cos(pitch) * np.sin(yaw)])
    right = np.cross(fwd, [0, 1, 0]); right /= np.linalg.norm(right); up = np.cross(right, fwd)
    ray = fwd + right * (u - W / 2) / f + up * (H / 2 - v) / f
    t = (xw - c[0]) / ray[0]; return c + t * ray
for u in (440, 1465):
    q = back(u, 240); print("film sconce at px %d -> spec z %.2f, y %.2f" % (u, q[2], q[1]))
