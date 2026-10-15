"""refcam: match a reference frame (film still or Marina tour frame) to the build, measure from it, and overlay the build on it.

Why (Oct 15): placements read by eye from frames kept coming out wrong (the stair-hall pier, the basement door). Every claim
about where something is in a frame now goes through a solved camera, with per-point residuals, and an overlay of the
build's own geometry on the frame before anything is built.

Coordinates: spec metres (x across, z down the plan, y up with the upper floor at 0; the ground floor at -3.026). Points may
give "h" (height above the ground floor) instead of y. Cameras are level (verticals vertical: true for the film's dolly shots
and Marina's CG walk; check with the residuals), principal point at the frame centre; unknowns yaw, position, focal
(or a fixed focal with --f).

  refcam.py frame marina 916            -> sfm-work/refcam/frames/marina-916.jpg (ffmpeg, Part 1; 'marina2 441' for Part 2)
  refcam.py frame film 2677             -> the film still's path
  refcam.py grid FRAME x0 y0 x1 y1 [--step 20]       gridded crop (PNG) for reading pixels, coordinates labelled
  refcam.py solve NAME FRAME POINTS.json [--f F]     camera from correspondences -> measurements/cameras/NAME.json
       POINTS.json: [{"uv": [u, v], "xyz": [x, y, z]} | {"uv": [u, v], "x": .., "h": .., "z": ..} | {"uv": .., "line": [[x,y,z],[x,y,z]]}, ...]
       ('line': the pixel lies on the image of that 3D line, e.g. a wall's floor line; 'note' fields are kept)
  refcam.py measure NAME u v --plane x=2.985 | z=7.638 | h=0     the 3D point under a pixel, on a plane
  refcam.py overlay NAME [--out PNG] [--floor ground] [--what walls,openings,stairs,dressing]   build's edges drawn on the frame
  refcam.py view NAME [--views FILE]                 append the camera as a Unity RenderViews entry (near clip past walls it stands behind)
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
G = -3.026
CAMS = ROOT / "measurements/cameras"
WORK = ROOT / "sfm-work/refcam"
VIDEOS = {"marina": ROOT / "Tour the Home Alone House_ Part 1, Main Floor [CG Tour] copy.mp4",
          "marina2": ROOT / "Tour the Home Alone House_ Part 2  [CG Tour].mp4"}


def R(yaw):   # spec (x, y up, z) -> camera (right, down, forward); yaw 0 looks along -x, yaw +90 deg along -z
    c, s = np.cos(yaw), np.sin(yaw)
    return np.array([[s, 0, -c], [0, -1, 0], [-c, 0, -s]])


def proj(cam, X):
    Xc = (np.atleast_2d(X) - np.array(cam["pos"])) @ R(cam["yaw"]).T
    return np.c_[cam["cx"] + cam["f"] * Xc[:, 0] / Xc[:, 2], cam["cy"] + cam["f"] * Xc[:, 1] / Xc[:, 2]], Xc[:, 2]


def ray(cam, u, v):
    d = R(cam["yaw"]).T @ np.array([(u - cam["cx"]) / cam["f"], (v - cam["cy"]) / cam["f"], 1.0])
    return np.array(cam["pos"]), d


def xyz_of(p):
    if "xyz" in p:
        return np.array(p["xyz"], float)
    return np.array([p["x"], G + p["h"] if "h" in p else p["y"], p["z"]], float)


def load_cam(name):
    return json.loads((CAMS / f"{name}.json").read_text())


def cmd_frame(a):
    if a.source == "film":
        print(ROOT / f"0-homealone/full/homealone-movie-screencaps.com-{a.id}.jpg"); return
    out = WORK / "frames" / f"{a.source}-{a.id}.jpg"; out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", str(a.id), "-i", str(VIDEOS[a.source]), "-frames:v", "1", "-q:v", "2", str(out)], check=True)
    print(out)


def cmd_grid(a):
    from PIL import Image, ImageDraw
    im = Image.open(a.frame).convert("RGB").crop((a.x0, a.y0, a.x1, a.y1)); s = a.scale
    im = im.resize((im.width * s, im.height * s)); d = ImageDraw.Draw(im)
    for x in range((a.x0 // a.step + 1) * a.step, a.x1, a.step):
        d.line([((x - a.x0) * s, 0), ((x - a.x0) * s, im.height)], fill=(255, 255, 0) if x % (a.step * 5) == 0 else (0, 255, 255)); d.text(((x - a.x0) * s + 2, 2), str(x), fill=(255, 255, 0))
    for y in range((a.y0 // a.step + 1) * a.step, a.y1, a.step):
        d.line([(0, (y - a.y0) * s), (im.width, (y - a.y0) * s)], fill=(255, 255, 0) if y % (a.step * 5) == 0 else (0, 255, 255)); d.text((2, (y - a.y0) * s + 2), str(y), fill=(255, 255, 0))
    out = Path(a.out or WORK / "grids" / f"{Path(a.frame).stem}-{a.x0}-{a.y0}.png"); out.parent.mkdir(parents=True, exist_ok=True); im.save(out); print(out)


def cmd_solve(a):
    from PIL import Image
    from scipy.optimize import least_squares
    W, H = Image.open(a.frame).size
    P = json.loads(Path(a.points).read_text())
    pts = [p for p in P if "line" not in p]; lines = [p for p in P if "line" in p]
    X = np.array([xyz_of(p) for p in pts]) if pts else np.zeros((0, 3)); U = np.array([p["uv"] for p in pts], float) if pts else np.zeros((0, 2))
    base = {"cx": W / 2, "cy": H / 2}

    def cam_of(q):
        return dict(base, yaw=q[0], pos=list(q[1:4]), f=a.f if a.f else q[4])

    def res(q):
        c = cam_of(q); r = []
        if len(X):
            r += list((proj(c, X)[0] - U).ravel())
        for p in lines:   # distance from the pixel to the projected 3D line (pixels)
            (pa, pb), _ = proj(c, np.array(p["line"], float))
            t = pb - pa; n = np.array([-t[1], t[0]]) / (np.linalg.norm(t) + 1e-9)
            r.append(float((np.array(p["uv"]) - pa) @ n))
        return np.array(r)
    # start from every horizontal direction and a spread of positions around the points' centroid
    c0 = X.mean(0) if len(X) else np.array([0, G + 1.5, 0])
    best = None
    for yaw in np.radians(np.arange(-180, 180, 30)):
        fwd = np.array([-np.cos(yaw), 0.0, -np.sin(yaw)])          # the camera's viewing direction at this yaw
        for dist in (3.0, 6.0, 10.0):
            start = np.r_[yaw, c0 - fwd * dist, a.f or 1400]       # stand back from the points, looking at them
            start[2] = G + 1.4
            try:
                s = least_squares(res, start if not a.f else start[:4], x_scale=np.r_[0.1, 1, 1, 1, 300][: 4 if a.f else 5])
            except Exception:
                continue
            c = cam_of(s.x)
            if len(X) and (proj(c, X)[1] <= 0).any():
                continue
            if best is None or s.cost < best.cost:
                best = s
    c = cam_of(best.x); r = res(best.x)
    rms = float(np.sqrt(np.mean(r ** 2))); per = []
    k = 0
    for p in pts:
        e = float(np.hypot(r[k], r[k + 1])); k += 2; per.append(e)
    for p in lines:
        per.append(abs(float(r[k]))); k += 1
    c.update({"name": a.name, "frame": str(Path(a.frame).resolve().relative_to(ROOT)) if str(Path(a.frame).resolve()).startswith(str(ROOT)) else str(a.frame),
              "size": [W, H], "rms_px": round(rms, 2), "points": P, "residuals_px": [round(e, 2) for e in per]})
    CAMS.mkdir(parents=True, exist_ok=True); (CAMS / f"{a.name}.json").write_text(json.dumps(c, indent=1))
    print(f"{a.name}: camera x {c['pos'][0]:.2f} z {c['pos'][2]:.2f} height {c['pos'][1] - G:.2f} m, yaw {np.degrees(c['yaw']):.1f} deg, "
          f"f {c['f']:.0f} px (vfov {np.degrees(2 * np.arctan(H / 2 / c['f'])):.1f}); rms {rms:.1f} px over {len(per)} constraints")
    for p, e in zip(P, per):
        flag = "  <-- check" if e > max(3 * rms, 6) else ""
        print(f"   {e:6.1f} px  {p.get('note', '')}{flag}")


def cmd_measure(a):
    c = load_cam(a.name); o, d = ray(c, a.u, a.v)
    ax, val = a.plane.split("="); val = float(val)
    i = {"x": 0, "z": 2, "h": 1, "y": 1}[ax]; val = G + val if ax == "h" else val
    t = (val - o[i]) / d[i]; P = o + t * d
    print(f"x {P[0]:.3f}  z {P[2]:.3f}  height {P[1] - G:.3f} (y {P[1]:.3f})  at {t:.2f} m along the ray")


def box_edges(x, y, z):
    C = np.array([[x[i], y[j], z[k]] for i in (0, 1) for j in (0, 1) for k in (0, 1)])
    E = [(0, 1), (0, 2), (0, 4), (1, 3), (1, 5), (2, 3), (2, 6), (3, 7), (4, 5), (4, 6), (5, 7), (6, 7)]
    return [(C[i], C[j]) for i, j in E]


def cmd_overlay(a):
    from PIL import Image, ImageDraw
    c = load_cam(a.name); im = Image.open(ROOT / c["frame"] if not Path(c["frame"]).is_absolute() else c["frame"]).convert("RGB"); d = ImageDraw.Draw(im)
    geo = json.loads((ROOT / "spec/geometry.json").read_text())
    what = set(a.what.split(","))
    segs = []
    for floor, off in (("ground", G), ("upstairs", 0.0)):
        if a.floor and floor != a.floor:
            continue
        st = geo[floor]
        if "walls" in what:
            for w in st["walls"]:
                segs += [(e, (255, 60, 60)) for e in box_edges(w["x"], [w["y"][0] + off, w["y"][1] + off], w["z"])]
        if "openings" in what:
            for o in st["openings"]:
                for c0, c1 in o["cuts"]:
                    xs = [o["c"], o["c"]] if o["axis"] == "x" else [o["lo"], o["hi"]]; zs = [o["lo"], o["hi"]] if o["axis"] == "x" else [o["c"], o["c"]]
                    segs += [(e, (60, 220, 255)) for e in box_edges(xs, [c0 + off, c1 + off], zs)]
    spec = {"ground": json.loads((ROOT / "spec/house_spec.ground.json").read_text()), "upstairs": json.loads((ROOT / "spec/house_spec.json").read_text())}
    if "stairs" in what:
        for f, s in spec.items():
            if a.floor and f != a.floor and not (a.floor == "ground" and f == "upstairs"):
                continue
            for k in ("stair", "attic_stair"):
                st = s.get(k)
                if not st:
                    continue
                for b in st["boxes"]:
                    if b["kind"] in ("rail", "spindle"):
                        continue
                    y = [b["y"][0] + (G if f == "ground" else 0), b["y"][1] + (G if f == "ground" else 0)]
                    segs += [(e, (255, 230, 0)) for e in box_edges(b["x"], y, b["z"])]
    if "dressing" in what:
        dr = json.loads((ROOT / "spec/dressing/foyer.json").read_text())
        for p in dr["pieces"]:
            if "x" in p:
                segs += [(e, (90, 255, 90)) for e in box_edges(p["x"], [p["y"][0] + G, p["y"][1] + G], p["z"])]
    for (A, B), col in segs:
        P, depth = proj(c, np.linspace(A, B, 24))
        ok = depth > 0.05
        pts = [tuple(q) for q, k in zip(P, ok) if k]
        if len(pts) > 1:
            d.line(pts, fill=col, width=2)
    for p, e in zip(c.get("points", []), c.get("residuals_px", [])):
        u, v = p["uv"]; d.ellipse([u - 6, v - 6, u + 6, v + 6], outline=(255, 0, 255), width=2)
    out = Path(a.out or WORK / "overlays" / f"{a.name}.jpg"); out.parent.mkdir(parents=True, exist_ok=True); im.save(out, quality=88); print(out)


def cmd_view(a):
    c = load_cam(a.name)
    pos = [c["pos"][0], c["pos"][1], -c["pos"][2]]; fwd = [-np.cos(c["yaw"]), 0.0, np.sin(c["yaw"])]
    v = {"name": f"../refcam/{a.name}", "pos": [round(float(q), 3) for q in pos], "look_at": [round(float(pos[i] + fwd[i]), 3) for i in range(3)],
         "vfov": round(float(np.degrees(2 * np.arctan(c["size"][1] / 2 / c["f"]))), 2)}
    if a.near:
        v["near"] = a.near
    P = ROOT / "spec/captures/views" / a.views
    V = json.loads(P.read_text()) if P.exists() else []
    V = [w for w in V if w["name"] != v["name"]] + [v]; P.write_text(json.dumps(V, indent=1)); print(f"{P}: {v}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter); sp = ap.add_subparsers(dest="cmd", required=True)
    p = sp.add_parser("frame"); p.add_argument("source", choices=["film", "marina", "marina2"]); p.add_argument("id")
    p = sp.add_parser("grid"); p.add_argument("frame"); [p.add_argument(k, type=int) for k in ("x0", "y0", "x1", "y1")]
    p.add_argument("--step", type=int, default=20); p.add_argument("--scale", type=int, default=2); p.add_argument("--out")
    p = sp.add_parser("solve"); p.add_argument("name"); p.add_argument("frame"); p.add_argument("points"); p.add_argument("--f", type=float)
    p = sp.add_parser("measure"); p.add_argument("name"); p.add_argument("u", type=float); p.add_argument("v", type=float); p.add_argument("--plane", required=True)
    p = sp.add_parser("overlay"); p.add_argument("name"); p.add_argument("--out"); p.add_argument("--floor"); p.add_argument("--what", default="walls,openings,stairs")
    p = sp.add_parser("view"); p.add_argument("name"); p.add_argument("--views", default="views-refcam.json"); p.add_argument("--near", type=float)
    a = ap.parse_args()
    {"frame": cmd_frame, "grid": cmd_grid, "solve": cmd_solve, "measure": cmd_measure, "overlay": cmd_overlay, "view": cmd_view}[a.cmd](a)


if __name__ == "__main__":
    main()
