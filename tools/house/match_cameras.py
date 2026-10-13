"""Render-and-compare, step 4 of docs/RECONCILIATION.md: put the Unity camera where Marina's camera was and measure
how far the grey-box's structural edges land from the real frame's edges.

  poses    <clip> <frame-idx,...>   clip camera poses -> Unity world (via the clip's registration in
                                    measurements/checkpoints/upstairs.json) -> spec/captures/matched/<clip>/poses.json
  compare  <clip> [measured]        after Unity renders (SpecGreybox.RenderMatched): edge overlay per frame, and the
                                    chamfer distance from every grey-box edge pixel to the nearest edge in Marina's frame

Run: uv run --with numpy --with scipy --with pillow --with opencv-python-headless python tools/house/match_cameras.py poses hall-s1 0,11,21,36,48,59
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "spec/captures/matched"
sys.path.insert(0, str(ROOT / "tools/sfm"))
from synthetic_score_lib import image_lines, quat_to_R  # noqa: E402


def clip_frame(clip):
    """The clip's plan frame (plan_extract.py output) + its registration onto the floor plan."""
    w = ROOT / "sfm-work/rooms" / clip
    p = json.loads((w / "plan-0.05.json").read_text())
    for floor in ("upstairs", "ground"):
        regs = json.loads((ROOT / f"measurements/checkpoints/{floor}.json").read_text()).get("registrations", {})
        if clip in regs:
            return w, p, regs[clip] | {"floor": floor}
    raise KeyError(clip)


def poses(clip, idxs):
    w, p, reg = clip_frame(clip)
    a, b = map(np.array, p["plane_axes"]); Rp = np.array(p["rotation"]); up = np.array(p["up"])
    S, sim = reg["m_per_unit"], reg["similarity"]          # clip plan metres -> floor plan (register_clip.py)
    th, k, tr = np.radians(sim["rotation_deg"]), sim["scale"], np.array(sim["translation"])
    M = np.array([[np.cos(th), np.sin(th)], [-np.sin(th), np.cos(th)]])
    spec = json.loads((ROOT / "spec/house_spec.json").read_text())
    o = np.array(spec["origin_plan_m"])
    d = np.load(w / "vggt/sparse/0/pixels.npz")
    floor = (np.median([d["world"][i, y, x] @ up for i, x, y in reg["floor_pixels"]]) if reg["floor_pixels"]
             else p["floor"])   # no picked floor pixels: plan_extract's floor level
    y0 = 0.0 if reg["floor"] == "upstairs" else json.loads((ROOT / f"spec/house_spec.{reg['floor']}.json").read_text())["floor_y_m"]
    cams = {int(l.split()[0]): float(l.split()[4]) for l in (w / "vggt/sparse/0/txt/cameras.txt").read_text().splitlines()
            if l.strip() and not l.startswith("#")}
    lines = image_lines(w / "vggt/sparse/0/txt")
    import cv2

    def to_unity(v, h):  # plan-frame horizontal (2,) and height -> Unity (x, y, z); world z = -spec z
        px, py = v
        return [float(py - o[1]), float(h), float(-(px - o[0]))]

    out = []
    for i in idxs:
        f = lines[i].split()
        focal = cams[int(f[8])]                    # VGGT predicts intrinsics per frame
        R0, t0 = quat_to_R(*map(float, f[1:5])), np.array(list(map(float, f[5:8])))
        # VGGT's camera head and point head are separate predictions; the plan was measured from the points, so
        # re-solve this frame's pose from its own point map (PnP) and report how far the camera head was off.
        Hh, Ww = d["world"].shape[1:3]
        ys, xs = np.mgrid[2:Hh - 2:3, 2:Ww - 2:3]
        conf = d["conf"][i][ys, xs]; keep = conf > np.percentile(conf, 50)
        obj = d["world"][i][ys, xs][keep].astype(np.float64); img = np.c_[xs[keep], ys[keep]].astype(np.float64) + 0.5
        fk = focal * Ww / 1920
        K = np.array([[fk, 0, Ww / 2], [0, fk, Hh / 2], [0, 0, 1]])
        rvec0, _ = cv2.Rodrigues(R0)
        ok, rvec, tvec, inl = cv2.solvePnPRansac(obj, img, K, None, rvec0, t0.reshape(3, 1), useExtrinsicGuess=True,
                                                 reprojectionError=2.0, iterationsCount=200)
        R, t = (cv2.Rodrigues(rvec)[0], tvec.ravel()) if ok else (R0, t0)
        C = -R.T @ t
        dC = np.linalg.norm((C - (-R0.T @ t0)) @ np.c_[a, b, up]) * S
        dA = np.degrees(np.arccos(np.clip((np.trace(R @ R0.T) - 1) / 2, -1, 1)))
        fwd, upv = R.T @ [0, 0, 1], -R.T @ [0, 1, 0]
        pos = to_unity(k * (np.array([C @ a, C @ b]) @ Rp * S) @ M + tr, k * (C @ up - floor) * S + y0)
        dirs = []
        for D in (fwd, upv):
            v = (np.array([D @ a, D @ b]) @ Rp) @ M
            dirs.append([float(v[1]), float(D @ up), float(-v[0])])
        hfov = 2 * np.degrees(np.arctan(960 / focal))
        vfov = 2 * np.degrees(np.arctan(np.tan(np.radians(hfov / 2)) * 1080 / 1920))
        name = Path(f[-1]).stem
        out.append({"name": name, "frame": str(ROOT / "sfm-work/rooms" / clip / "all/images" / Path(f[-1]).name),
                    "pos": pos, "forward": dirs[0], "up": dirs[1], "vfov": float(vfov),
                    "pnp_vs_camera_head": {"cm": round(float(dC * 100), 1), "deg": round(float(dA), 2), "inliers": int(len(inl) if ok else 0)}})
        print(f"{name}: Unity pos {np.round(pos, 2)}, eye {pos[1]:.2f} m, vfov {vfov:.1f} deg; "
              f"point-map pose vs camera head: {dC * 100:.1f} cm, {dA:.2f} deg ({len(inl) if ok else 0} inliers)")
    (OUT / clip).mkdir(parents=True, exist_ok=True)
    (OUT / clip / "poses.json").write_text(json.dumps({"clip": clip, "poses": out}, indent=1) + "\n")


def edges(img, frac=None, absolute=None):
    """Gradient edges: the strongest `frac` % (real frames), or above a fixed strength (grey-box surface-ID renders,
    where any colour change is a geometric edge: max gradient over the R, G, B channels)."""
    a = np.asarray(img.filter(ImageFilter.GaussianBlur(1.0)), float)
    m = np.max([np.hypot(*np.gradient(a[..., c])) for c in range(3)], axis=0)
    if absolute is None:
        g = np.asarray(img.convert("L").filter(ImageFilter.GaussianBlur(1.5)), float)
        m = np.hypot(*np.gradient(g))
        return m > np.percentile(m, 100 - frac)
    return m > absolute


LOW_STRUCTURE = 0.006   # fraction of render pixels that are edges; below this a view isn't scored


def compare(clip, variant=""):
    from scipy.ndimage import distance_transform_edt
    D = OUT / clip
    P = json.loads((D / "poses.json").read_text())
    rows, tiles = [], []
    for p in P["poses"]:
        frame = Image.open(p["frame"]).convert("RGB").resize((960, 540))
        render = Image.open(D / variant / f"{p['name']}.png").convert("RGB").resize((960, 540))
        fe, re_ = edges(frame, frac=12), edges(render, absolute=8.0)
        dist = distance_transform_edt(~fe)          # px to nearest edge in Marina's frame
        dd = dist[re_]
        med, p90 = float(np.median(dd)), float(np.percentile(dd, 90))
        low = re_.mean() < LOW_STRUCTURE    # too few grey-box edges to score (e.g. looking straight at a blank corner)
        rows.append((p["name"] + (" (low structure)" if low else ""), med, p90))
        ov = Image.blend(frame, Image.new("RGB", frame.size), 0.45)
        arr = np.asarray(ov).copy(); arr[re_] = [255, 40, 200]
        tile = Image.fromarray(arr); ImageDraw.Draw(tile).text((8, 8), f"{p['name']}  grey-box edge -> nearest frame edge: median {med:.1f} px, 90% {p90:.1f} px", fill="yellow")
        tiles.append(tile)
    sheet = Image.new("RGB", (1920, 540 * -(-len(tiles) // 2)))
    for k, t in enumerate(tiles):
        sheet.paste(t, ((k % 2) * 960, (k // 2) * 540))
    sheet.save(D / variant / "compare.png")
    print(f"{'frame':<30} {'median px':>9} {'90% px':>7}   (960x540; grey-box edge -> nearest strong edge in Marina's frame)")
    for n, m, q in rows:
        print(f"{n:<30} {m:9.1f} {q:7.1f}")
    print(f"-> {D / variant / 'compare.png'}")
    (D / variant / "scores.json").write_text(json.dumps([{"frame": n, "median_px": round(m, 1), "p90_px": round(q, 1)} for n, m, q in rows], indent=1) + "\n")


if __name__ == "__main__":
    cmd, clip = sys.argv[1], sys.argv[2]
    if cmd == "poses":
        poses(clip, [int(v) for v in sys.argv[3].split(",")])
    else:
        compare(clip, sys.argv[3] if len(sys.argv) > 3 else "")
