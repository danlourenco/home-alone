"""Render-and-compare, step 4 of docs/RECONCILIATION.md: put the Unity camera where Marina's camera was and measure
how far the grey-box's structural edges land from the real frame's edges.

  poses    <clip> <frame-idx,...>   clip camera poses -> Unity world (via the clip's registration in
                                    measurements/checkpoints/upstairs.json) -> spec/captures/matched/<clip>/poses.json
  compare  <clip>                   after Unity renders (SpecGreybox.RenderMatched): edge overlay per frame, and the
                                    chamfer distance from every grey-box edge pixel to the nearest edge in Marina's frame

Run: uv run --with numpy --with scipy --with pillow python tools/house/match_cameras.py poses hall-s1 0,11,21,36,48,59
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
    reg = json.loads((ROOT / "measurements/checkpoints/upstairs.json").read_text())["registrations"][clip]
    return w, p, reg


def poses(clip, idxs):
    w, p, reg = clip_frame(clip)
    a, b = map(np.array, p["plane_axes"]); Rp = np.array(p["rotation"]); up = np.array(p["up"])
    S, sim = reg["m_per_unit"], reg["similarity"]          # clip plan metres -> floor plan (register_clip.py)
    th, k, tr = np.radians(sim["rotation_deg"]), sim["scale"], np.array(sim["translation"])
    M = np.array([[np.cos(th), np.sin(th)], [-np.sin(th), np.cos(th)]])
    spec = json.loads((ROOT / "spec/house_spec.json").read_text())
    o = np.array(spec["origin_plan_m"])
    d = np.load(w / "vggt/sparse/0/pixels.npz")
    floor = np.median([d["world"][i, y, x] @ up for i, x, y in reg["floor_pixels"]])
    focal = float((w / "vggt/sparse/0/txt/cameras.txt").read_text().split("\n")[0].split()[4])
    lines = image_lines(w / "vggt/sparse/0/txt")

    def to_unity(v, h):  # plan-frame horizontal (2,) and height -> Unity (x, y, z); world z = -spec z
        px, py = v
        return [float(py - o[1]), float(h), float(-(px - o[0]))]

    out = []
    for i in idxs:
        f = lines[i].split()
        R, t = quat_to_R(*map(float, f[1:5])), np.array(list(map(float, f[5:8])))
        C = -R.T @ t
        fwd, upv = R.T @ [0, 0, 1], -R.T @ [0, 1, 0]
        pos = to_unity(k * (np.array([C @ a, C @ b]) @ Rp * S) @ M + tr, k * (C @ up - floor) * S)
        dirs = []
        for D in (fwd, upv):
            v = (np.array([D @ a, D @ b]) @ Rp) @ M
            dirs.append([float(v[1]), float(D @ up), float(-v[0])])
        hfov = 2 * np.degrees(np.arctan(960 / focal))
        vfov = 2 * np.degrees(np.arctan(np.tan(np.radians(hfov / 2)) * 1080 / 1920))
        name = Path(f[-1]).stem
        out.append({"name": name, "frame": str(ROOT / "sfm-work/rooms" / clip / "all/images" / Path(f[-1]).name),
                    "pos": pos, "forward": dirs[0], "up": dirs[1], "vfov": float(vfov)})
        print(f"{name}: Unity pos {np.round(pos, 2)}, eye {pos[1]:.2f} m, vfov {vfov:.1f} deg")
    (OUT / clip).mkdir(parents=True, exist_ok=True)
    (OUT / clip / "poses.json").write_text(json.dumps({"clip": clip, "poses": out}, indent=1) + "\n")


def edges(img, frac=None, absolute=None):
    """Gradient edges: the strongest `frac` % (real frames), or above a fixed strength (grey-box renders, whose
    smooth light falloff would otherwise pass a percentile cut)."""
    g = np.asarray(img.convert("L").filter(ImageFilter.GaussianBlur(1.5)), float)
    gx, gy = np.gradient(g)
    m = np.hypot(gx, gy)
    return m > (absolute if absolute is not None else np.percentile(m, 100 - frac))


def compare(clip):
    from scipy.ndimage import distance_transform_edt
    D = OUT / clip
    P = json.loads((D / "poses.json").read_text())
    rows, tiles = [], []
    for p in P["poses"]:
        frame = Image.open(p["frame"]).convert("RGB").resize((960, 540))
        render = Image.open(D / f"{p['name']}.png").convert("RGB").resize((960, 540))
        fe, re_ = edges(frame, frac=12), edges(render, absolute=3.0)
        dist = distance_transform_edt(~fe)          # px to nearest edge in Marina's frame
        dd = dist[re_]
        med, p90 = float(np.median(dd)), float(np.percentile(dd, 90))
        rows.append((p["name"], med, p90))
        ov = Image.blend(frame, Image.new("RGB", frame.size), 0.45)
        arr = np.asarray(ov).copy(); arr[re_] = [255, 40, 200]
        tile = Image.fromarray(arr); ImageDraw.Draw(tile).text((8, 8), f"{p['name']}  grey-box edges -> nearest frame edge: median {med:.1f} px, 90% {p90:.1f} px", fill="yellow")
        tiles.append(tile)
    sheet = Image.new("RGB", (1920, 540 * -(-len(tiles) // 2)))
    for k, t in enumerate(tiles):
        sheet.paste(t, ((k % 2) * 960, (k // 2) * 540))
    sheet.save(D / "compare.png")
    print(f"{'frame':<14} {'median px':>9} {'90% px':>7}   (960x540; grey-box edge -> nearest edge in Marina's frame)")
    for n, m, q in rows:
        print(f"{n:<14} {m:9.1f} {q:7.1f}")
    print(f"-> {D / 'compare.png'}")
    (D / "scores.json").write_text(json.dumps([{"frame": n, "median_px": round(m, 1), "p90_px": round(q, 1)} for n, m, q in rows], indent=1) + "\n")


if __name__ == "__main__":
    cmd, clip = sys.argv[1], sys.argv[2]
    if cmd == "poses":
        poses(clip, [int(v) for v in sys.argv[3].split(",")])
    else:
        compare(clip)
