"""wall_measure: measure things on (or standing proud of) a flat wall from ONE frame, with a known rectangle on that wall as the ruler.
Replaces the per-job camera solvers (film_foyer_measure.py, foyer_props_measure.py, parents_fireplace_measure.py ...): the slow
part of a fixture job was hand-picking corners one crop at a time and re-writing a solver (slow_jobs, Oct 18).

  frame  SRC                      fetch a frame: marina1:SEC | marina2:SEC | film:N | a path  -> sfm-work/frames/<name>.png
  crops  SRC name=u,v ...         ONE sheet of 6x gridded crops (10 px grid) for every rough pick, each snapped to the nearest
                                  corner (sub-pixel); prints the refined picks to paste into the job file
  solve  JOB.json                 sizes on the wall plane + an overlay with a 0.1 m grid drawn back on the frame
  demo                            self-check on a synthetic camera

JOB.json:
  {"frame": "marina2:195.25",
   "ruler": {"corners": [[u,v] TL, TR, BR, BL], "w": 0.813 | null, "h": 2.032},   # w null: solved, needs "f"
   "f": 1428,                                   # px (Marina's solved focal, 1080p); optional when w and h are both known
   "points": {"shelf_L": [u, v] | {"uv": [u, v], "depth": 0.20}},   # depth: metres in front of the wall (needs f or w+h)
   "lengths": {"shelf": ["shelf_L", "shelf_R"]},
   "check": {"lengths": {"shelf": 1.25}}}       # optional: a second ruler's numbers -> spread %
Wall coordinates: s along the wall from the ruler's left edge (m), y up from its bottom edge, d out of the wall toward the camera.
usage: uv run --with numpy --with pillow python -I tools/house/wall_measure.py ...
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
FR = ROOT / "sfm-work/frames"
VID = {"marina1": "Tour the Home Alone House_ Part 1, Main Floor [CG Tour] copy.mp4", "marina2": "Tour the Home Alone House_ Part 2  [CG Tour].mp4"}


def frame(src):
    if ":" not in src:
        return Path(src)
    kind, n = src.split(":", 1)
    if kind == "film":
        return ROOT / f"0-homealone/full/homealone-movie-screencaps.com-{int(n)}.jpg"
    out = FR / f"{kind}-{n}.png"
    if not out.exists():
        FR.mkdir(parents=True, exist_ok=True)
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", n, "-i", str(ROOT / VID[kind]), "-frames:v", "1", str(out)], check=True)
    return out


def homography(src, dst):
    A = []
    for (x, y), (u, v) in zip(src, dst):
        A += [[x, y, 1, 0, 0, 0, -u * x, -u * y, -u], [0, 0, 0, x, y, 1, -v * x, -v * y, -v]]
    H = np.linalg.svd(np.asarray(A, float))[2][-1].reshape(3, 3)
    return H / H[2, 2]


def apply(H, p):
    q = H @ np.array([p[0], p[1], 1.0])
    return q[:2] / q[2]


def wall_corners(w, h):
    return [(0, h), (w, h), (w, 0), (0, 0)]   # TL TR BR BL in wall metres (s, y)


def pose(H, f, c):
    """wall (s, y, 0) -> image homography H and intrinsics -> R (columns: s, y, d axes in camera), t; d toward the camera"""
    K = np.array([[f, 0, c[0]], [0, f, c[1]], [0, 0, 1.0]])
    M = np.linalg.inv(K) @ H
    lam = 2.0 / (np.linalg.norm(M[:, 0]) + np.linalg.norm(M[:, 1]))
    r1, r2, t = M[:, 0] * lam, M[:, 1] * lam, M[:, 2] * lam
    if t[2] < 0:
        r1, r2, t = -r1, -r2, -t
    r3 = np.cross(r1, r2)
    U, _, Vt = np.linalg.svd(np.column_stack([r1, r2, r3]))
    return K, U @ Vt, t


def ortho_error(corners_img, w, h, f, c):
    M = np.linalg.inv(np.array([[f, 0, c[0]], [0, f, c[1]], [0, 0, 1.0]])) @ homography(wall_corners(w, h), corners_img)
    a, b = M[:, 0], M[:, 1]
    return (np.linalg.norm(a) - np.linalg.norm(b)) ** 2 / np.linalg.norm(a) ** 2 + (a @ b) ** 2 / (np.linalg.norm(a) * np.linalg.norm(b)) ** 2


def solve_width(corners_img, h, f, c):
    """the ruler's unknown width: the one that makes the wall axes orthonormal through a camera of focal f (golden search)"""
    lo, hi = 0.05 * h, 20 * h
    g = (5 ** 0.5 - 1) / 2
    for _ in range(200):
        a, b = hi - g * (hi - lo), lo + g * (hi - lo)
        if ortho_error(corners_img, a, h, f, c) < ortho_error(corners_img, b, h, f, c):
            hi = b
        else:
            lo = a
    return (lo + hi) / 2


def to_wall(uv, depth, H, K, R, t):
    """pixel -> wall coords on the plane d = depth (metres out of the wall)"""
    if not depth:
        s, y = apply(np.linalg.inv(H), uv)
        return np.array([s, y, 0.0])
    ray = R.T @ (np.linalg.inv(K) @ np.array([uv[0], uv[1], 1.0]))   # in wall axes
    cam = -R.T @ t
    k = (depth - cam[2]) / ray[2]
    return cam + k * ray


def solve(job, draw=True):
    img = frame(job["frame"])
    from PIL import Image, ImageDraw
    im = Image.open(img).convert("RGB")
    c = (im.width / 2, im.height / 2)
    r = job["ruler"]; corners = [tuple(p) for p in r["corners"]]; f = job.get("f")
    w = r.get("w")
    if w is None:
        assert f, "ruler width unknown: give the focal f"
        w = solve_width(corners, r["h"], f, c)
    H = homography(wall_corners(w, r["h"]), corners)
    K = R = t = None
    if f:
        K, R, t = pose(H, f, c)
    pts = {}
    for name, p in job.get("points", {}).items():
        uv, d = (p, 0.0) if isinstance(p, list) else (p["uv"], p.get("depth", 0.0))
        assert not d or f, f"{name}: a depth needs the focal f"
        pts[name] = to_wall(uv, d, H, K, R, t)
    out = {"frame": str(img.relative_to(ROOT)) if img.is_relative_to(ROOT) else str(img), "ruler_w": round(w, 4), "ruler_h": r["h"],
           "points": {k: [round(float(x), 4) for x in v] for k, v in pts.items()},
           "lengths": {k: round(float(np.linalg.norm(pts[a][:2] - pts[b][:2])), 4) for k, (a, b) in job.get("lengths", {}).items()}}
    chk = job.get("check", {}).get("lengths", {})
    out["spread_pct"] = {k: round(100 * (out["lengths"][k] - v) / v, 1) for k, v in chk.items() if k in out["lengths"]}
    if draw:   # a 0.1 m grid on the wall plane over the ruler's span (+1 m round it), and the picks
        dr = ImageDraw.Draw(im)
        for i in range(-10, int(w * 10) + 11):
            dr.line([tuple(apply(H, (i / 10, -0.5))), tuple(apply(H, (i / 10, r["h"] + 0.5)))], fill=(255, 220, 0) if i % 10 == 0 else (0, 200, 255), width=1)
        for j in range(-5, int(r["h"] * 10) + 6):
            dr.line([tuple(apply(H, (-1.0, j / 10))), tuple(apply(H, (w + 1.0, j / 10)))], fill=(255, 220, 0) if j % 10 == 0 else (0, 200, 255), width=1)
        dr.polygon(corners, outline=(255, 0, 0), width=3)
        for name, p in job.get("points", {}).items():
            u, v = p if isinstance(p, list) else p["uv"]
            dr.ellipse([u - 4, v - 4, u + 4, v + 4], outline=(255, 0, 255), width=2); dr.text((u + 6, v - 6), name, fill=(255, 0, 255))
        ov = FR / f"overlay-{job['frame'].replace(':', '-').replace('/', '_')}.png"; FR.mkdir(parents=True, exist_ok=True); im.save(ov)
        out["overlay"] = str(ov.relative_to(ROOT))
    return out


def refine(gray, u, v, r=6):
    """snap to the strongest corner (Harris response, structure tensor) within r px; sub-pixel by a parabola fit"""
    x0, y0 = int(round(u)), int(round(v))
    g = gray[max(0, y0 - r - 3): y0 + r + 4, max(0, x0 - r - 3): x0 + r + 4].astype(float)
    if g.shape[0] < 7 or g.shape[1] < 7:
        return u, v
    gy, gx = np.gradient(g)
    def box(a):
        k = np.ones((3, 3)) / 9
        p = np.pad(a, 1, mode="edge")
        return sum(p[i:i + a.shape[0], j:j + a.shape[1]] * k[i, j] for i in range(3) for j in range(3))
    xx, yy, xy = box(gx * gx), box(gy * gy), box(gx * gy)
    resp = xx * yy - xy * xy - 0.05 * (xx + yy) ** 2
    resp[:2, :] = resp[-2:, :] = -np.inf; resp[:, :2] = resp[:, -2:] = -np.inf
    j, i = np.unravel_index(np.argmax(resp), resp.shape)
    def sub(a, b, cc):
        d = a - 2 * b + cc
        return 0.0 if d == 0 or not np.isfinite(d) else 0.5 * (a - cc) / d
    di = sub(resp[j, i - 1], resp[j, i], resp[j, i + 1]); dj = sub(resp[j - 1, i], resp[j, i], resp[j + 1, i])
    return max(0, x0 - r - 3) + i + di, max(0, y0 - r - 3) + j + dj


def crops(src, picks, z=6, half=20):
    from PIL import Image, ImageDraw
    im = Image.open(frame(src)).convert("RGB"); gray = np.asarray(im.convert("L"))
    cells, out = [], {}
    for name, (u, v) in picks.items():
        ru, rv = refine(gray, u, v)
        out[name] = [round(ru, 1), round(rv, 1)]
        c = im.crop((int(u) - half, int(v) - half, int(u) + half, int(v) + half)).resize((2 * half * z, 2 * half * z), Image.NEAREST)
        d = ImageDraw.Draw(c)
        for k in range(0, 2 * half + 1, 10):
            d.line([(k * z, 0), (k * z, 2 * half * z)], fill=(0, 200, 255)); d.line([(0, k * z), (2 * half * z, k * z)], fill=(0, 200, 255))
        for (a, b, col) in ((u, v, (255, 0, 255)), (ru, rv, (0, 255, 0))):
            x, y = (a - int(u) + half) * z, (b - int(v) + half) * z; d.ellipse([x - 5, y - 5, x + 5, y + 5], outline=col, width=2)
        d.text((4, 4), f"{name} {int(u) - half},{int(v) - half} +10px grid", fill=(255, 255, 0))
        cells.append(c)
    n = len(cells); cols = min(4, n); s = 2 * half * z
    sheet = Image.new("RGB", (cols * s, ((n + cols - 1) // cols) * s))
    for k, c in enumerate(cells):
        sheet.paste(c, ((k % cols) * s, (k // cols) * s))
    p = FR / f"crops-{src.replace(':', '-').replace('/', '_')}.png"; FR.mkdir(parents=True, exist_ok=True); sheet.save(p)
    return str(p.relative_to(ROOT)), out


def demo():
    """a camera 3 m from a wall, turned 25 deg: a 0.813 x 2.032 door and a shelf 0.2 m proud must come back exact"""
    f, c = 1428.0, (960.0, 540.0)
    th = np.radians(25); R = np.array([[np.cos(th), 0, np.sin(th)], [0, -1, 0], [np.sin(th), 0, -np.cos(th)]])   # columns: s, y, d in camera
    t = np.array([-0.4, 1.4, 3.2])
    K = np.array([[f, 0, c[0]], [0, f, c[1]], [0, 0, 1.0]])
    P = lambda p: (lambda q: q[:2] / q[2])(K @ (R @ np.asarray(p, float) + t))
    corners = [P((s, y, 0)) for s, y in wall_corners(0.813, 2.032)]
    H = homography(wall_corners(0.813, 2.032), corners)
    w = solve_width(corners, 2.032, f, c)
    assert abs(w - 0.813) < 1e-3, w
    K2, R2, t2 = pose(H, f, c)
    for p in ((1.5, 1.12, 0.2), (2.77, 0.0, 0.0), (1.2, 0.74, 0.09)):
        q = to_wall(P(p), p[2], H, K2, R2, t2)
        assert np.allclose(q, p, atol=1e-3), (p, q)
    print("demo ok: width", round(w, 4))


if __name__ == "__main__":
    a = sys.argv[1:]
    if not a or a[0] == "demo":
        demo()
    elif a[0] == "frame":
        print(frame(a[1]))
    elif a[0] == "crops":
        path, ref = crops(a[1], {k: tuple(map(float, v.split(","))) for k, v in (x.split("=") for x in a[2:])})
        print(path); print(json.dumps(ref))
    elif a[0] == "solve":
        print(json.dumps(solve(json.loads(Path(a[1]).read_text())), indent=1))
