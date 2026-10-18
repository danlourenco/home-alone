"""buzz_layout: Buzz's room furniture measured in Marina's own multi-view solve, placed against the built room's faces.

HOUSE-KERNEL step 5 / STATUS 8z, TRIAL 1 (layout only; changes/2026-10-17-buzz-layout.json).

Why this way: every failed Buzz attempt (changes/*buzz*) took its numbers from ONE kind of source per step (the Buzz SfM at
its own door scale for the room; the oblique 0:50 overhead's fractions or a single frame's pixel ratios for furniture).
Here the furniture comes from the 45 solved cameras of Marina's Buzz clip (VGGT, sfm-work/real-vggt-buzzall: Part 2
540-562 s, frame i = 540.125 + i/2 s, found by image difference), as in the den (den_walls.py): wall and floor planes are fitted to the solve's dense
points in plain-wallpaper regions; every furniture edge is a picked pixel whose RAY is cut with a plane (the wall it
stands against, or a plane parallel to it), never the depth at a silhouette; each piece is picked in 2+ frames and the
spread is printed.

Scale: the SfM's units are arbitrary. Two rulers of different kinds, never averaged:
  * 'mattress': the twin mattress between the headboard posts' inner faces = 39 in (0.991 m; up to 40 in with play)
  * 'chart':    the growth chart beside the desk (Marina 540 s), its 3 ft and 5 ft marks 0.610 m apart (vertical)
Each ruler is printed measuring the room; the built room (spec/geometry.json buzz_room) is compared with both.

Placement (stage 8): each piece is stored in spec/dressing/buzz.json as {wall, from (corner), along, width, depth,
height}, measured from the nearest corner in Marina's order; positions resolve against the built faces in --write.

  uv run --with numpy --with scipy python -I tools/house/buzz_layout.py            # planes, rulers, room check, piece table
  ... buzz_layout.py --write                                                       # -> spec/dressing/buzz.json (+ store_props)
  ... buzz_layout.py --cams                                                        # the 45 cameras in spec coords -> measurements/cameras/buzz-v*.json
"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
M = ROOT / "sfm-work/real-vggt-buzzall/sparse/0"
S = 1920 / 518   # pick coordinates are on the solve's 518 x 294 images; poses are for the 1920 x 1080 frames

# built room faces (spec/geometry.json upstairs buzz_room; walls: shelves x0, front x1, door z0, desk z1)
ROOM = json.loads((ROOT / "spec/geometry.json").read_text())["upstairs"]
_P = next(r for r in ROOM["rooms"] if r["name"] == "buzz_room")["poly"]
X0, X1 = min(p[0] for p in _P), max(p[0] for p in _P)
Z0, Z1 = min(p[1] for p in _P), max(p[1] for p in _P)

# plain regions (frame index, x0, y0, x1, y1) on the 518 x 294 images, read on gridded crops (sfm-work/buzz1/vg*.png)
REG = {
    "floor": [(40, 262, 236, 372, 294), (38, 262, 236, 372, 294), (42, 262, 236, 372, 294), (36, 250, 236, 360, 294)],
    "door":  [(40, 372, 6, 500, 38), (40, 330, 150, 360, 205), (38, 372, 6, 500, 38), (42, 372, 6, 500, 38), (34, 372, 6, 500, 38)],
    "front": [(20, 245, 2, 292, 100), (20, 60, 100, 76, 280), (20, 250, 120, 258, 270), (22, 245, 2, 292, 100), (18, 245, 2, 292, 100)],
    "shelves": [(40, 45, 80, 120, 128), (40, 50, 170, 85, 205), (36, 68, 115, 108, 165)],
    "desk":  [(0, 100, 2, 150, 200), (0, 160, 145, 340, 200), (0, 372, 2, 400, 100), (2, 100, 2, 150, 200), (4, 160, 145, 340, 200)],
}


def q2R(w, x, y, z):
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)],
                     [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
                     [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)]])


def load():
    f = {int(l.split()[0]): float(l.split()[4]) for l in open(M / "txt/cameras.txt") if l.strip() and not l.startswith("#")}
    cams = []
    for l in open(M / "txt/images.txt"):
        p = l.split()
        if len(p) >= 10 and not l.startswith("#") and p[-1].endswith(".jpg"):
            R = q2R(*map(float, p[1:5])); t = np.array(list(map(float, p[5:8])))
            cams.append(dict(R=R, t=t, C=-R.T @ t, f=f[int(p[8])], name=p[9]))
    d = np.load(M / "pixels.npz")
    return cams, d["world"], d["conf"]


def ray(cam, u, v):
    """pick (u, v) on the 518 image -> ray in solve coordinates"""
    U, V = (u + 0.5) * S - 0.5, (v + 0.5) * (1080 / 294) - 0.5
    d = cam["R"].T @ np.array([(U - 960) / cam["f"], (V - 540) / cam["f"], 1.0])
    return cam["C"], d / np.linalg.norm(d)


def cut(cam, u, v, n, c):
    o, d = ray(cam, u, v); t = ((c - o) @ n) / (d @ n); return o + t * d


def plane(P, it=2000, seed=0):
    rng = np.random.default_rng(seed); tol = 0.004 * np.ptp(P, 0).max(); best = None
    for _ in range(it):
        a, b, c = P[rng.choice(len(P), 3, replace=False)]; n = np.cross(b - a, c - a)
        if np.linalg.norm(n) < 1e-12:
            continue
        n /= np.linalg.norm(n); inl = abs((P - a) @ n) < tol
        if best is None or inl.sum() > best.sum():
            best = inl
    Q = P[best]; c = Q.mean(0); n = np.linalg.svd(Q - c)[2][2]
    return n, c, best.mean()


def planes(world, conf, cams):
    out = {}
    for k, regs in REG.items():
        P = []
        for i, x0, y0, x1, y1 in regs:
            w = world[i, y0:y1, x0:x1].reshape(-1, 3); m = conf[i, y0:y1, x0:x1].reshape(-1) > 1.5
            P.append(w[m])
        P = np.concatenate(P); n, c, frac = plane(P)
        # normals point into the room: toward the cameras
        C = np.mean([cm["C"] for cm in cams], 0)
        if (C - c) @ n < 0:
            n = -n
        out[k] = (n, c); print(f"  {k:6s} plane: {frac * 100:.0f}% of {len(P)} points within tolerance")
    return out


class Frame:
    """solve coords -> spec coords: up from the floor, x across (shelves -> front), z from the door wall to the desk wall.
    Origin: the door|front corner (built x1, z0). scale = metres per solve unit."""
    def __init__(self, pl, scale):
        up = pl["floor"][0]
        nd = pl["door"][0] - (pl["door"][0] @ up) * up; nd /= np.linalg.norm(nd)          # into the room = +z spec
        nf = pl["front"][0] - (pl["front"][0] @ up) * up; nf /= np.linalg.norm(nf)        # into the room = -x spec
        self.ang = np.degrees(np.arccos(abs(nd @ nf)))
        ex = -nf; ex = ex - (ex @ nd) * nd; ex /= np.linalg.norm(ex)                      # make it square, keep the door wall's direction
        self.up, self.ez, self.ex = up, nd, ex
        # corner: on the floor, door and front planes
        A = np.array([pl["floor"][0], pl["door"][0], pl["front"][0]]); b = np.array([pl[k][0] @ pl[k][1] for k in ("floor", "door", "front")])
        self.o = np.linalg.solve(A, b); self.s = scale

    def spec(self, P):
        d = (np.atleast_2d(P) - self.o) * self.s
        return np.c_[X1 + d @ self.ex, d @ self.up, Z0 + d @ self.ez]


def dist(pl, k, P):
    n, c = pl[k]; return (np.atleast_2d(P) - c) @ n


# ---- picks (frame index: (u, v) on the 518 x 294 images), read on 3-12x gridded crops (sfm-work/buzz1/*.png) ----
def F(U, V):
    """a pick read on a FULL 1920 x 1080 frame (sfm-work/buzz1/full/<i>.jpg) -> the 518 x 294 grid"""
    return ((U + 0.5) / S - 0.5, (V + 0.5) / (1080 / 294) - 0.5)


PICKS = {   # name: (how, {frame: (u, v)}); how = "tri" (rays from 2+ frames), ("wall", plane, metres off it), ("h", other pick)
    # bed: the ball tops (finials) of the four posts. Head posts stand at the wall: cut 0.05 m off it (the triangulated depth
    # of points on the wall runs 0.1-0.2 m behind the wall plane here: the clip looks straight at that wall)
    "head_L": (("wall", "door", 0.05), {30: (105, 130), 32: (193, 128), 36: (325, 109), 40: (371, 98), 42: (317, 113), 43: (283, 112), 44: (249, 120)}),
    "head_R": (("wall", "door", 0.05), {30: (235, 128), 32: (310, 127), 36: (436, 109), 40: (482, 97), 42: (422, 113), 43: (385, 111), 44: (347, 118)}),
    "foot_L": ("tri", {36: (404, 207), 40: (442, 182), 42: (382, 184), 43: (344, 190), 44: (306, 204)}),
    "foot_R": ("tri", {16: (184, 222), 20: (311, 214), 22: (342, 225), 44: (476, 193)}),
    # nightstand top: back corners on the door wall (+1 cm), the front-right corner on the top's height
    "ns_back_L": (("wall", "door", 0.01), {44: (361, 182)}),   # 30/32: the mattress hides its corner (picks there read 14 cm apart)
    "ns_back_R": (("wall", "door", 0.01), {44: (404, 181), 30: (306, 202), 32: (381, 200)}),
    "ns_front_R": (("h", "ns_back_R"), {44: (421, 190), 30: (322, 210), 32: (398, 209)}),
    # chest of drawers (front wall, between the windows): top's front corners
    "chest_TL": ("tri", {16: (119, 108), 20: (258, 109), 22: (308, 120), 26: (375, 141), 28: (432, 147)}),
    "chest_TR": ("tri", {16: (291, 111), 20: (428, 110), 22: (485, 124)}),
    # desk (desk wall): top's back corners on the wall (+1 cm), front-left corner on the top's height
    # desk (desk wall), read on the full frame 0 (540.1 s): the top's left end runs from its back corner (at the wall, beside the
    # curtain's hem) down-left to its front corner; its right end from the back corner down-right to the front corner (behind the
    # chair's back). Back corners on the wall (+1 cm); front corners on the plane of the top's front edge, 0.50 m off the wall
    # (the drawer fronts' dense depth reads 0.484 m: FACES desk_front; the top overhangs them)
    "desk_back_L": (("wall", "desk", 0.01), {0: F(393, 797)}),
    "desk_back_R": (("wall", "desk", 0.01), {0: F(1400, 762)}),
    "desk_front_L": (("wall", "desk", 0.50), {0: F(335, 945)}),
    "desk_front_R": (("wall", "desk", 0.50), {0: F(1600, 866)}),
    # Marina's door (door wall), read on the full frame 44 (562.1 s) and converted to the 518 grid: leaf corners and the casing's outer edge
    "door_leaf_TL": (("wall", "door", 0.0), {44: (102.6, 39.1)}),
    "door_leaf_TR": (("wall", "door", 0.0), {44: (185.7, 40.9)}),
    "door_leaf_BR": (("wall", "door", 0.0), {44: (185.7, 242.8)}),
    "door_casing_R": (("wall", "door", 0.0), {44: (195.6, 242.8)}),
    # wall shelves (shelves wall): the glove shelf's near-end top-front corner
    "shelf_end": ("tri", {36: (174, 170), 40: (241, 148), 42: (177, 159), 44: (100, 173)}),
    "shelf_top": ("tri", {44: F(357, 185), 40: F(853, 122)}),
    "shelf_2": ("tri", {44: F(360, 362), 40: F(853, 283)}),
    "shelf_bottom": (("z_of", "shelf_end"), {44: F(355, 885)})   # boards end in one vertical plane,
}
# rulers
POSTS_INNER = {40: (377, 476), 42: (322, 416), 36: (330, 428)}   # head posts' inner faces at the block (v 140)
CHART = {0: ((418, 48.5), (418, 177))}                              # growth chart 5 ft and 3 ft ticks (desk wall)


def tri(cams, obs):
    """least-squares point closest to all rays; returns point and the rms miss distance (solve units)"""
    A = np.zeros((3, 3)); b = np.zeros(3); R = []
    for i, (u, v) in obs.items():
        o, d = ray(cams[i], u, v); P = np.eye(3) - np.outer(d, d); A += P; b += P @ o; R.append((o, d))
    X = np.linalg.solve(A, b)
    miss = [np.linalg.norm((np.eye(3) - np.outer(d, d)) @ (X - o)) for o, d in R]
    return X, float(np.sqrt(np.mean(np.square(miss))))


def rulers(cams, pl):
    nd = pl["door"][0]; up = pl["floor"][0]
    ex = np.cross(up, nd); ex /= np.linalg.norm(ex)
    out = {}
    m = []
    for i, (ul, ur) in POSTS_INNER.items():
        a = cut(cams[i], ul, 140, nd, pl["door"][1]); b = cut(cams[i], ur, 140, nd, pl["door"][1]); m.append(abs((b - a) @ ex))
    out["mattress"] = (0.9906 / np.mean(m), [0.9906 / q for q in m], [1.016 / q for q in m])
    c = []
    for i, (p5, p3) in CHART.items():
        a = cut(cams[i], *p5, pl["desk"][0], pl["desk"][1]); b = cut(cams[i], *p3, pl["desk"][0], pl["desk"][1]); c.append(abs((a - b) @ up))
    out["chart"] = (0.6096 / np.mean(c), [0.6096 / q for q in c], [])
    return out


def main():
    cams, world, conf = load()
    print(f"{len(cams)} cameras, f {min(c['f'] for c in cams):.0f}-{max(c['f'] for c in cams):.0f} px")
    pl = planes(world, conf, cams)
    up = pl["floor"][0]
    for a, b in (("door", "front"), ("front", "desk"), ("door", "desk"), ("door", "shelves"), ("front", "shelves")):
        print(f"  angle {a}/{b}: {np.degrees(np.arccos(abs(pl[a][0] @ pl[b][0]))):.1f} deg; {a}.up {pl[a][0] @ up:+.3f}")
    # room depth in solve units: door plane to desk plane (along the door normal)
    nd = pl["door"][0]; depth = (pl["desk"][1] - pl["door"][1]) @ nd
    print(f"  door wall -> desk wall {depth:.3f} units")
    nf = pl["front"][0]; width = (pl["shelves"][1] - pl["front"][1]) @ nf
    print(f"  front wall -> shelves wall {width:.3f} units")
    R = rulers(cams, pl)
    for k, (sc, each, wide) in R.items():
        print(f"  ruler {k}: {sc:.4f} m/unit (frames {', '.join(f'{q:.4f}' for q in each)}{'; 40 in: ' + ', '.join(f'{q:.4f}' for q in wide) if wide else ''})")
    fr = Frame(pl, R["mattress"][0]); print(f"  door/front walls {fr.ang:.1f} deg apart")
    # room size in metres at each ruler (door wall length is the corner-to-corner distance: needs the shelves wall, not in this
    # clip's planes; the desk wall depth is measured here)
    for k, (sc, *_r) in R.items():
        print(f"  door wall -> desk wall at {k}: {depth * sc:.3f} m (built {Z1 - Z0:.3f}); front -> shelves {width * sc:.3f} m (built {X1 - X0:.3f})")
    pts, spread = {}, {}
    for k, (how, obs) in PICKS.items():   # dict order: an "h" pick names an earlier one
        if how == "tri":
            X, miss = tri(cams, obs); each = []
        else:
            if how[0] == "wall":
                n, c = pl[how[1]]; c = c + n * how[2] / fr.s
            elif how[0] == "z_of":
                n, c = fr.ez, pts[how[1]]
            else:
                n, c = up, pts[how[1]]
            each = [cut(cams[i], u, v, n, c) for i, (u, v) in obs.items()]; X = np.mean(each, 0); miss = 0.0
        pts[k] = X; E = fr.spec(np.array(each)) if each else None
        spread[k] = np.ptp(E, 0) if E is not None and len(E) > 1 else np.zeros(3)
        print(f"  {k:12s} spec {np.round(fr.spec(X)[0], 3)}  ({len(obs)} frames; " + (f"rays miss {miss * fr.s * 100:.1f} cm rms" if how == "tri"
              else f"spread x {spread[k][0] * 100:.1f} y {spread[k][1] * 100:.1f} z {spread[k][2] * 100:.1f} cm") + ")")
    return cams, world, conf, pl, fr, pts


VIDEO = ROOT / "Tour the Home Alone House_ Part 2  [CG Tour].mp4"
WORK = ROOT / "sfm-work/buzz1"


def full_frame(i):
    import subprocess
    out = WORK / "full" / f"{i}.jpg"
    if not out.exists():
        out.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", f"{540.125 + i / 2:.3f}", "-i", str(VIDEO), "-frames:v", "1", "-q:v", "2", str(out)], check=True)
    return out


def to_solve(fr, Q):
    Q = np.atleast_2d(Q); return fr.o + ((Q[:, :1] - X1) * fr.ex + Q[:, 1:2] * fr.up + (Q[:, 2:3] - Z0) * fr.ez) / fr.s


def project(cam, fr, Q):
    Xc = to_solve(fr, Q) @ cam["R"].T + cam["t"]
    return np.c_[960 + cam["f"] * Xc[:, 0] / Xc[:, 2], 540 + cam["f"] * Xc[:, 1] / Xc[:, 2]], Xc[:, 2]


def box_edges(x, y, z):
    C = np.array([[x[i], y[j], z[k]] for i in (0, 1) for j in (0, 1) for k in (0, 1)])
    return [(C[a], C[b]) for a, b in [(0, 1), (0, 2), (0, 4), (1, 3), (1, 5), (2, 3), (2, 6), (3, 7), (4, 5), (4, 6), (5, 7), (6, 7)]]


def overlay(cams, fr, i, boxes, points, out):
    """built room (red), openings (cyan), planned boxes (green) and measured points (magenta) drawn on Marina frame i"""
    from PIL import Image, ImageDraw
    im = Image.open(full_frame(i)).convert("RGB"); d = ImageDraw.Draw(im); cam = cams[i]
    segs = box_edges([X0, X1], [0, 2.4], [Z0, Z1])
    segs = [(e, (255, 60, 60), 2) for e in segs]
    for o in ROOM["openings"]:
        if "buzz_room" in o["between"]:
            for c0, c1 in o["cuts"]:
                xs = [o["c"], o["c"]] if o["axis"] == "x" else [o["lo"], o["hi"]]; zs = [o["lo"], o["hi"]] if o["axis"] == "x" else [o["c"], o["c"]]
                segs += [(e, (60, 220, 255), 2) for e in box_edges(xs, [c0, c1], zs)]
    for name, (x, y, z) in boxes.items():
        segs += [(e, (60, 255, 60), 3) for e in box_edges(x, y, z)]
    for (A, B), col, w in segs:
        P, dep = project(cam, fr, np.linspace(A, B, 40)); pts = [tuple(q) for q, k in zip(P, dep > 0.05) if k]
        if len(pts) > 1:
            d.line(pts, fill=col, width=w)
    for name, Q in points.items():
        (u, v), = project(cam, fr, Q)[0]
        d.ellipse([u - 7, v - 7, u + 7, v + 7], outline=(255, 0, 255), width=3); d.text((u + 9, v - 9), name, fill=(255, 0, 255))
    out.parent.mkdir(parents=True, exist_ok=True); im.save(out, quality=88); return out


# ---- dense depth on flat faces (the solve's per-pixel points, median over a region; IQR printed) ----
FACES = {   # name: [(frame, x0, y0, x1, y1)] on the 518 grid, all on one flat face of the piece
    "chest_front": [(20, 290, 150, 400, 250), (16, 130, 150, 260, 250), (22, 320, 160, 460, 260), (26, 400, 170, 500, 250)],
    "desk_front": [(0, 120, 262, 250, 290), (6, 320, 215, 420, 260), (9, 380, 210, 480, 250)],
    "ns_front": [(44, 385, 192, 415, 205), (30, 280, 215, 315, 228)],
    "footboard": [(43, 330, 245, 450, 262), (44, 330, 240, 440, 265)],
    "mattress_top": [(40, 390, 175, 470, 192), (42, 330, 170, 400, 185), (43, 330, 205, 420, 225)],
}
SHELF_END_PIX = {44: (95, 175), 40: (226, 150), 42: (172, 161), 36: (168, 172)}   # the glove board's front face, 1-3 px inside its near end
# The shelves' desk-side end is outside this clip (Marina 530-537 s). Read on the full frame Part 2 533 s (shelves wall near
# face-on: the boards' front edges level across the frame): the glove board's top-front edge 617 px and the top board's 181 px at
# x 1260 are 0.737 m apart in height (shelf_top - shelf_end above) = 592 px/m on the boards' front plane; their left end 675 px,
# the desk|shelves corner line 274 px (on the wall, 0.29 m further: 533 px/m at f 1600). Left end = 1.287 - 0.481 = 0.81 m from
# the desk wall's corner.
SHELF_FAR_FROM_DESK = 0.806


# Independent scale check (no solve, no mattress): Marina Part 2 560 s, door wall near face-on, read on 4x gridded crops
# (sfm-work/buzz1/p*.png; crops spec/captures/picks/buzz1/m560_*.png). The door leaf's right edge is the 80 in ruler.
M560 = {"leaf_L": 877, "leaf_R": 1164, "leaf_top": 74, "leaf_floor": 803, "casing_R": 1204, "post_L_outer": 1366, "read_px": 4}   # corrected by the blind pick check (c51-c55)


def check_560(sp_bed_edge, casing_from_front, leaf_w):
    m = M560; ppm = (m["leaf_floor"] - m["leaf_top"]) / 2.032
    lw = (m["leaf_R"] - m["leaf_L"]) / ppm; gap = (m["post_L_outer"] - m["casing_R"]) / ppm; e = 2 * m["read_px"] / ppm
    print(f"  560 s at the 80 in door: leaf width {lw:.3f} (+-{e:.3f}) vs solve {leaf_w:.3f}; casing -> bed post {gap:.3f} (+-{e:.3f}) vs solve {casing_from_front - sp_bed_edge:.3f}")
    return lw, gap


def faces(world, conf, fr):
    out = {}
    for k, regs in FACES.items():
        S_ = np.concatenate([fr.spec(world[i, y0:y1, x0:x1].reshape(-1, 3)[conf[i, y0:y1, x0:x1].reshape(-1) > 1.2]) for i, x0, y0, x1, y1 in regs])
        out[k] = np.median(S_, 0)
        print(f"  face {k:12s} median {np.round(out[k], 3)}  IQR {np.round(np.percentile(S_, 75, 0) - np.percentile(S_, 25, 0), 3)}  ({len(S_)} points)")
    e = fr.spec(np.array([world[i, v, u] for i, (u, v) in SHELF_END_PIX.items()]))
    out["shelf_end"] = e.mean(0); print(f"  shelf near end (dense) {np.round(e.mean(0), 3)} spread z {np.ptp(e[:, 2]) * 100:.0f} cm")
    return out


def layout(pl, fr, pts, fc, cams_g):
    """Marina's arrangement as distances from her corners along each face (her metres, mattress ruler). Built = the same numbers
    from the same corner of the built face. wall: door (z0, from the front corner), front (x1, from the door corner), desk (z1,
    from the front corner), shelves (x0, from the door corner)."""
    sp = {k: fr.spec(v)[0] for k, v in pts.items()}
    W = (pl["shelves"][1] - pl["front"][1]) @ pl["front"][0] * fr.s; D = (pl["desk"][1] - pl["door"][1]) @ pl["door"][0] * fr.s
    r3 = lambda v: round(float(v), 3)
    sR, sL = X1 - sp["head_R"][0], X1 - sp["head_L"][0]; post = 0.104   # the pack bed's post (tools/house/purchased_bed.py; was 0.09 authored)
    sR, sL = sR + BED_SHIFT, sL + BED_SHIFT
    P = []
    P.append(dict(name="buzz_bed", wall="door", corner="front", along=[r3(sR - post / 2), r3(sL + post / 2)], store="Assets/Purchased/BuzzBed/BuzzBed.glb", yaw=180, off=[0.015, r3(fc["footboard"][2] - Z0)],
                  h=[0.0, r3((sp["head_L"][1] + sp["head_R"][1]) / 2 + 0.05)], foot_h=r3((sp["foot_L"][1] + sp["foot_R"][1]) / 2 + 0.05),
                  mattress_top=r3(fc["mattress_top"][1]), post=post,
                  source=f"head posts' finials (7 frames each, cut 0.05 m off the door wall) centres {r3(sR - BED_SHIFT)} / {r3(sL - BED_SHIFT)} m from the front corner, built {BED_SHIFT} m further toward the door (adult passage to the chest, changes/2026-10-18-buzz-bed.json); "
                         f"footboard face {r3(fc['footboard'][2] - Z0)} m off the wall (dense depth, 2 frames); finial tops head {r3((sp['head_L'][1] + sp['head_R'][1]) / 2 + 0.05)}, "
                         f"foot {r3((sp['foot_L'][1] + sp['foot_R'][1]) / 2 + 0.05)}; mattress top {r3(fc['mattress_top'][1])} (dense). Post 0.104 square: the pack bed's (purchased_bed.py)"))
    # nightstand: its top's front-right corner (frames 44/30/32, confirmed by the pick check) cut on the front face's plane (dense
    # depth 0.50 m off the wall, frames 44/30). The wall cuts of its back corners (ns_back_*) read 0.16-0.74 but the pick check put
    # them on the wall above the top (not the corner): not used. Its left end is hidden by the pillow in every solved frame; width
    # 0.55 m from Marina 563 s (front face 220 px vs the head posts' 402 px = 1.18 m, x 0.89 for the face standing 0.45 m nearer),
    # leaving 3 cm to the bed's post as her 563 s shows a narrow gap (DEVIATIONS)
    nd_, c_ = pl["door"]; dfront = fc["ns_front"][2] - Z0; cplane = c_ + nd_ * dfront / fr.s
    sR_ns = float(np.mean([X1 - fr.spec(cut(cams_g[i], u, v, nd_, cplane))[0][0] for i, (u, v) in PICKS["ns_front_R"][1].items()]))
    P.append(dict(name="buzz_nightstand", wall="door", corner="front", along=[r3(sR_ns), r3(sR_ns + 0.55)], off=[0.015, r3(dfront)],
                  h=[0.0, r3(sp["ns_front_R"][1])], store="Assets/Classic Wooden Furniture Pack/Prefabs/BEDSIDE_CAB_01.prefab", back="-z",
                  source="top's front-right corner (frames 44/30/32) on the front face's plane (dense depth, frames 44/30); width 0.55 from Marina 563 s (left end hidden by the pillow in the solved frames)"))
    P.append(dict(name="buzz_chest", wall="front", corner="door", along=[r3(sp["chest_TL"][2] - Z0), r3(sp["chest_TR"][2] - Z0)], off=[0.015, r3(X1 - fc["chest_front"][0])],
                  h=[0.0, r3((sp["chest_TL"][1] + sp["chest_TR"][1]) / 2)], store="Assets/Purchased/BuzzChest/BuzzChest.glb", yaw=270,   # film 2718's chest (tools/house/purchased_chest.py); yaw 270: drawers to the room (Orient took the pulls for the flat back: yaw 90, build overnight2 #2)
                  source="top's front corners triangulated (left: frames 16/20/22/26/28, right: 16/20/22), front face dense depth (frames 16/20/22/26, IQR 0.5-0.8 cm)"))
    P.append(dict(name="buzz_desk", wall="desk", corner="front", along=[r3(X1 - sp["desk_back_L"][0]), r3(X1 - sp["desk_back_R"][0])], off=[0.015, 0.50],
                  h=[0.0, r3((sp["desk_back_L"][1] + sp["desk_back_R"][1] + sp["desk_front_L"][1] + sp["desk_front_R"][1]) / 4)],
                  store="Assets/Fadnn - Vintage Interior Furniture Pack/Props/Prefabs/HDRP/SM_Desk_01.prefab", back="+z", yaw=0,   # yaw 0: user Oct 17 "rotate the desk 180" (Orient gave 180: drawers to the wall)
                 
                  source=f"top's four corners in frame 0 (back on the wall, front on the top's front plane; the four heights agree to 2.8 cm); drawer fronts {r3(D - (fc['desk_front'][2] - Z0))} m off the wall (dense, 3 frames), top 0.50"))
    ch0 = P[-1]["along"][0] + 0.84 * (P[-1]["along"][1] - P[-1]["along"][0])
    P.append(dict(name="buzz_desk_chair", wall="desk", corner="front", along=[1.517, 1.967], off=[0.297, 0.767], h=[0.0, 0.92],   # placed by the user in the editor, Oct 17
                  store="Assets/Fadnn - Vintage Interior Furniture Pack/Props/Prefabs/HDRP/SM_Chair_01.prefab", yaw=180,
                  source="PLACED BY THE USER in the editor (Oct 17): tucked under the desk's right part, seat facing the desk (was AUTHORED from Marina 540 s)"))
    near = fc["shelf_end"][2] - Z0; far = (Z1 - Z0) - SHELF_FAR_FROM_DESK; depth = fc["shelf_end"][0] - (X1 - W)   # far end from the BUILT desk corner, as measured depth = fc["shelf_end"][0] - (X1 - W)
    boards = sorted(r3(sp[k][1]) for k in ("shelf_bottom", "shelf_end", "shelf_2", "shelf_top"))
    P.append(dict(name="buzz_shelves", wall="shelves", corner="door", along=[r3(near), r3(far)], off=[0.015, r3(depth)], h=[0.45, boards[-1]], boards=boards,
                  standards=3, spacing=0.757,
                  source=f"near end: the glove board's front face, dense depth (4 frames) {r3(near)} m from the door wall, front {r3(depth)} m off the wall; far end Marina 533 s "
                         f"{SHELF_FAR_FROM_DESK} m from the desk-wall corner (SHELF_FAR_FROM_DESK); board top heights {boards} (triangulated, frames 40/44); 3 standards 0.757 m apart (533 s)"))
    P.append(dict(name="buzz_tank", wall="shelves", corner="door", along=[r3(far - 0.43), r3(far - 0.02)], off=[0.04, r3(depth - 0.02)], h=[boards[1], r3(boards[1] + 0.23)],
                  source="the tarantula tank on the glove board at its desk-side end, Marina 533 s: 0.02-0.43 m from the end, 0.23 high (592 px/m); depth authored"))
    return P, r3(W), r3(D)


BED_SHIFT = 0.14   # along the door wall toward the door (spec -x): adult passage bed-chest >= 0.59 (changes/2026-10-18-buzz-bed.json)
UNDER_Z = 0.48     # bed rails' underside (purchased_bed.py)


def place(p):
    """face-relative -> built box (spec x, y, z)"""
    a0, a1 = p["along"]; o0, o1 = p["off"]; h = p["h"]
    if p["wall"] == "door":
        return [X1 - a1, X1 - a0], h, [Z0 + o0, Z0 + o1]
    if p["wall"] == "front":
        return [X1 - o1, X1 - o0], h, [Z0 + a0, Z0 + a1]
    if p["wall"] == "desk":
        return [X1 - a1, X1 - a0], h, [Z1 - o1, Z1 - o0]
    if p["wall"] == "shelves":
        return [X0 + o0, X0 + o1], h, [Z0 + a0, Z0 + a1]


def parts(p):
    """a piece -> the boxes drawn (name, x, y, z, material)"""
    x, y, z = place(p); n = p["name"]
    if n == "buzz_bed":
        q = p["post"]; mt = p["mattress_top"]; out = []
        xa, xb, za, zb = x[0], x[1], z[0], z[1]
        for tag, (px, pz, top) in {"head_L": (xa, za, y[1]), "head_R": (xb - q, za, y[1]), "foot_L": (xa, zb - q, p["foot_h"]), "foot_R": (xb - q, zb - q, p["foot_h"])}.items():
            out.append((f"{n}_post_{tag}", [px, px + q], [0.0, top], [pz, pz + q], "wood"))
        t = 0.03; zc0 = za + q / 2; zc1 = zb - q / 2
        # walk layer = the model's (purchased_bed.py): boards to the floor, rails and mattress from UNDER_Z up so kid Kevin
        # (crouch 0.45 + skin 0.02) fits under (DEVIATIONS 72)
        out.append((f"{n}_headboard", [xa + q / 2, xb - q / 2], [0.16, y[1] - 0.15], [zc0 - t / 2, zc0 + t / 2], "wood"))
        out.append((f"{n}_footboard", [xa + q / 2, xb - q / 2], [0.16, p["foot_h"] - 0.07], [zc1 - t / 2, zc1 + t / 2], "wood"))
        for tag, (r0, r1) in {"L": (xa + q / 2 - 0.015, xa + q / 2 + 0.015), "R": (xb - q / 2 - 0.015, xb - q / 2 + 0.015)}.items():
            out.append((f"{n}_rail_{tag}", [r0, r1], [UNDER_Z, UNDER_Z + 0.08], [za + q, zb - q], "wood"))
        out.append((f"{n}_mattress", [xa + q, xb - q], [UNDER_Z + 0.08, mt - 0.03], [zc0 + t / 2, zc1 - t / 2], "mattress"))
        out.append((f"{n}_blanket", [xa + q - 0.015, xb - q + 0.015], [mt - 0.03, mt], [za + 0.55, zc1 - t / 2], "blanket"))
        return out
    if n == "buzz_shelves":
        out = []; t = 0.025
        for i, b in enumerate(p["boards"]):
            out.append((f"{n}_board{i}", x, [b - t, b], z, "wood"))
        a0 = z[0] + ((z[1] - z[0]) - p["spacing"] * (p["standards"] - 1)) / 2
        lev = [p["h"][0]] + [b - t for b in p["boards"]]
        for k in range(p["standards"]):
            zc = a0 + k * p["spacing"]
            for j in range(len(p["boards"])):   # segments between boards: a standard never passes through a board (clash check)
                y0 = p["h"][0] if j == 0 else p["boards"][j - 1]
                out.append((f"{n}_standard{k}_{j}", [x[0], x[0] + 0.025], [y0, p["boards"][j] - t], [zc - 0.0125, zc + 0.0125], "wood"))
        return out
    return [(n, x, y, z, {"buzz_tank": "glass"}.get(n, "wood"))]


def check(P):
    """HOUSE-KERNEL stage 8 rules on the built boxes: inside the room, on the floor (or on a board), clear of the door's swing and
    of the windows' casings and stools, no two pieces in one place. Returns problems (empty = pass)."""
    bad = []; B = {p["name"]: place(p) for p in P}
    door = next(o for o in ROOM["openings"] if "buzz_room" in o["between"] and o["kind"] == "door")
    hinge = np.array([door["lo"], Z0]); leaf = door["hi"] - door["lo"]   # Marina 563: knob on the bed side, hinges at the shelves end
    for n, (x, y, z) in B.items():
        if x[0] < X0 - 1e-6 or x[1] > X1 + 1e-6 or z[0] < Z0 - 1e-6 or z[1] > Z1 + 1e-6:
            bad.append(f"{n}: outside the room")
        if y[0] < -1e-6:
            bad.append(f"{n}: below the floor")
        cx, cz = np.clip(hinge[0], *x), np.clip(hinge[1], *z)
        if np.hypot(cx - hinge[0], cz - hinge[1]) < leaf and y[0] < 2.0:
            bad.append(f"{n}: inside the door's swing ({np.hypot(cx - hinge[0], cz - hinge[1]):.2f} m from the hinge < {leaf:.2f})")
    for o in json.loads((ROOT / "spec/openings.json").read_text())["openings"]:
        if "buzz_room" not in o["between"] or o["kind"] != "window":
            continue
        for pc in o["pieces"]:
            bx = pc["box"]
            for n, (x, y, z) in B.items():
                if x[0] < bx[1] and x[1] > bx[0] and z[0] < bx[3] and z[1] > bx[2] and y[0] < bx[5] and y[1] > bx[4]:
                    bad.append(f"{n}: meets the {o['id']} {pc['part']}")
    names = list(B)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            (ax, ay, az), (bx_, by, bz) = B[a], B[b]
            if a.startswith("buzz_tank") or b.startswith("buzz_tank"):
                continue   # the tank stands on the shelves' board
            if ax[0] < bx_[1] and ax[1] > bx_[0] and az[0] < bz[1] and az[1] > bz[0] and ay[0] < by[1] and ay[1] > by[0]:
                bad.append(f"{a} and {b} overlap")
    return bad


def write(P, W, D):
    boxes = [dict(name=n, x=[round(v, 4) for v in x], y=[round(v, 4) for v in y], z=[round(v, 4) for v in z], mat=m) for p in P for n, x, y, z, m in parts(p)]
    out = {"note": "Buzz's room furniture (Oct 17 2026, TRIAL 1: layout only; changes/2026-10-17-buzz-layout.json, DEVIATIONS 68-72). Written by "
                   "tools/house/buzz_layout.py --write: do not edit 'boxes' by hand. 'pieces' are HOUSE-KERNEL stage 8 placements: each piece sits "
                   "against a built face, 'along' metres from the named corner (Marina's order from that corner), 'off' metres off the face, 'h' "
                   "above the upper floor; measured in Marina's Buzz clip (45 solved cameras, VGGT real-vggt-buzzall) at the twin-mattress ruler. "
                   "'boxes' are the built boxes (spec x, y above the upper floor, z), read by SpecGreybox.Buzz; store models in "
                   "store_props.json (buzz_*) hide the box of the same name.",
           "marina_room": {"front_to_shelves": W, "door_to_desk": D, "built": [round(X1 - X0, 3), round(Z1 - Z0, 3)]},
           "pieces": P, "boxes": boxes}
    (ROOT / "spec/dressing/buzz.json").write_text(json.dumps(out, indent=1) + "\n")
    sp_path = ROOT / "spec/dressing/store_props.json"; SP = json.loads(sp_path.read_text())
    user = {q["name"]: q for q in SP["pieces"] if q.get("placed_by") == "user"}   # Home Alone > Save Prop Placement: the user's hand placement wins
    SP["pieces"] = [q for q in SP["pieces"] if q["name"] not in {p["name"] for p in P}]   # its own pieces only (buzz_door is the door's, changes/2026-10-17-buzz-door.json)
    for p in P:
        if "store" not in p:
            continue
        x, y, z = place(p)
        q = {"name": p["name"], "floor": "upper", "prefab": p["store"], "x": [round(v, 4) for v in x], "z": [round(v, 4) for v in z], "y0": 0.0,
             "height": p["h"][1], "hides": [b[0] for b in parts(p)], "collide": False,
             "source": "Buzz TRIAL 1 (changes/2026-10-17-buzz-layout.json): box from spec/dressing/buzz.json (tools/house/buzz_layout.py); " + p["source"]}
        if "yaw" in p:
            q["yaw"] = p["yaw"]; q["back"] = ""
        else:
            q["back"] = p["back"]
        if p["name"] in user:
            q.update({k: user[p["name"]][k] for k in ("x", "z", "yaw", "back", "placed_by") if k in user[p["name"]]})
        SP["pieces"].append(q)
    sp_path.write_text(json.dumps(SP, indent=1) + "\n")
    return boxes


if __name__ == "__main__":
    cams, world, conf, pl, fr, pts = main()
    fc = faces(world, conf, fr)
    P, W, D = layout(pl, fr, pts, fc, cams)
    for p in P:
        print(f"  {p['name']:16s} {p['wall']:7s} from {p['corner']:5s} along {p['along']} off {p['off']} h {p['h']}")
    sp_ = {k: fr.spec(v)[0] for k, v in pts.items()}
    check_560(P[0]["along"][1], X1 - sp_["door_casing_R"][0], sp_["door_leaf_TR"][0] - sp_["door_leaf_TL"][0])
    bad = check(P)
    print("Stage 8 check: " + ("PASS" if not bad else f"{len(bad)} problems\n    " + "\n    ".join(bad)))
    if "--write" in sys.argv:
        b = write(P, W, D); print(f"wrote spec/dressing/buzz.json ({len(b)} boxes) and the buzz_* entries of store_props.json")
    if "--views" in sys.argv:   # Unity RenderViews entries: Marina's solved cameras + Kevin-eye views (spec/captures/views/<FILE>)
        tag = sys.argv[sys.argv.index("--views") + 1]; V = []
        for i in (0, 6, 12, 16, 20, 26, 30, 36, 40, 44):
            c = cams[i]; C = fr.spec(c["C"])[0]; f_ = c["R"][2]; Fw = np.array([f_ @ fr.ex, f_ @ fr.up, f_ @ fr.ez])
            V.append({"name": f"buzz1/{tag}/marina-{i:02d}", "pos": [round(C[0], 3), round(C[1], 3), round(-C[2], 3)],
                      "look_at": [round(C[0] + Fw[0], 3), round(C[1] + Fw[1], 3), round(-(C[2] + Fw[2]), 3)], "vfov": round(float(np.degrees(2 * np.arctan(540 / c["f"]))), 2)})
        B_ = {b["name"]: b for b in json.loads((ROOT / "spec/dressing/buzz.json").read_text())["boxes"]}
        def kv(name, at, look, fov=60):
            V.append({"name": f"buzz1/{tag}/{name}", "pos": [at[0], at[1], -at[2]], "look_at": [look[0], look[1], -look[2]], "vfov": fov})
        kv("kevin-door", [7.92, 1.10, 11.75], [10.6, 0.7, 15.6])                  # just inside the door, toward the desk/front corner
        kv("kevin-bed", [8.75, 1.10, 13.0], [10.6, 0.6, 11.7])                   # beside the bed's foot, toward the headboard and nightstand
        kv("kevin-shelves", [9.6, 1.10, 13.4], [7.47, 1.0, 14.3])                # toward the shelves wall
        kv("kevin-front", [8.4, 1.10, 12.6], [11.15, 0.9, 14.2])                  # toward the chest between the front windows
        for n, at, look in (("close-bedfoot", [8.70, 1.10, 13.25], [9.15, 0.05, 13.70]),
                            ("close-nightstand", [10.30, 1.10, 12.45], [10.75, 0.3, 11.62]),
                            ("close-chest", [10.15, 1.10, 13.35], [10.95, 0.1, 13.80]),
                            ("close-desk", [9.35, 1.10, 14.95], [9.95, 0.3, 15.95]),
                            ("close-shelves", [8.40, 1.10, 13.30], [7.50, 0.8, 13.05]),
                            ("close-headpost", [9.55, 1.10, 12.35], [10.25, 0.1, 11.62])):
            kv(n, at, look, 55)
        out = ROOT / "spec/captures/views" / f"buzz1-{tag}.json"; out.write_text(json.dumps(V, indent=1)); print(out, len(V))
    if "--overlay" in sys.argv:   # the planned boxes (buzz.json) through every solved camera, before any Unity build
        from PIL import Image
        arg = sys.argv[sys.argv.index("--overlay") + 1]
        idx = range(len(cams)) if arg == "all" else map(int, arg.split(","))
        boxes = {b["name"]: (b["x"], b["y"], b["z"]) for b in json.loads((ROOT / "spec/dressing/buzz.json").read_text())["boxes"]}
        outs = [overlay(cams, fr, i, boxes, {}, ROOT / "spec/captures/buzz1/overlay" / f"plan-{i:02d}.jpg") for i in idx]
        W_, H_ = 480, 270; cols = 5; sheet = Image.new("RGB", (W_ * cols, H_ * ((len(outs) + cols - 1) // cols)))
        for k, o in enumerate(outs):
            sheet.paste(Image.open(o).resize((W_, H_)), ((k % cols) * W_, (k // cols) * H_))
        sheet.save(ROOT / "spec/captures/buzz1/overlay/sheet.jpg", quality=85); print(ROOT / "spec/captures/buzz1/overlay/sheet.jpg")
