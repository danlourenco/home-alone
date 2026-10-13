"""Wall-by-wall check of the spec against a gated SfM clip's dense 3D points (verify-plan skill).

For every wall edge of every space in the spec, take the clip's wall-height points (30-70% of floor-to-ceiling,
confidence above median) that fall within +-0.40 m of the edge and alongside it, and find the density peak of their
signed distance to the edge: that peak is where the real wall is. Reports the offset in cm per wall, so a misplaced
wall shows up as its actual error instead of as an image score. Image edge scores could not detect a 20 cm camera
shift (Oct 13 sensitivity test), so this is the numeric gate; render overlays remain the visual check.
usage: uv run --with numpy python tools/house/check_walls.py <clip> [measured]
"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
INSIDE, OUTSIDE, MIN_PTS, TOL_CM = 0.40, 0.20, 400, 8.0   # search 40 cm into the room, 20 cm beyond the wall
# (not further out: Marina's walls are 25-45 cm thick, so the neighbouring room's face would win the density peak)


def inside(poly, pt):
    x, y = pt; c = False
    for (x1, y1), (x2, y2) in zip(poly, np.roll(poly, -1, 0)):
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


def clip_points(clip):
    """Wall-height points in plan metres, each tagged with the plan position of the camera that saw it."""
    w = ROOT / "sfm-work/rooms" / clip
    p = json.loads((w / "plan-0.05.json").read_text())
    reg = json.loads((ROOT / "measurements/checkpoints/upstairs.json").read_text())["registrations"][clip]
    a, b = map(np.array, p["plane_axes"]); R = np.array(p["rotation"]); up = np.array(p["up"])
    sim = reg["similarity"]; th = np.radians(sim["rotation_deg"])
    M = np.array([[np.cos(th), np.sin(th)], [-np.sin(th), np.cos(th)]])
    d = np.load(w / "vggt/sparse/0/pixels.npz")
    to_plan = lambda X: sim["scale"] * (np.c_[X @ a, X @ b] @ R * reg["m_per_unit"]) @ M + sim["translation"]
    sys.path.insert(0, str(ROOT / "tools/sfm"))
    from synthetic_score_lib import image_lines, quat_to_R
    cams = {}
    for l in image_lines(w / "vggt/sparse/0/txt"):
        f = l.split(); Rc = quat_to_R(*map(float, f[1:5])); t = np.array(list(map(float, f[5:8])))
        cams[Path(f[-1]).name] = -Rc.T @ t
    thr = np.median(d["conf"]); fl, ce = p["floor"], p["ceiling"]
    pts, cpos = [], []
    for i, n in enumerate(d["names"]):
        W = d["world"][i].reshape(-1, 3)[d["conf"][i].reshape(-1) > thr]
        h = W @ up; W = W[(h > fl + 0.3 * (ce - fl)) & (h < fl + 0.7 * (ce - fl))]
        if len(W):
            pts.append(to_plan(W)); cpos.append(np.repeat(to_plan(cams[str(n)][None]), len(W), 0))
    return np.vstack(pts), np.vstack(cpos)  # plan metres (x down the overhead, y across)


def main(clip, variant=""):
    spec = json.loads((ROOT / f"spec/house_spec{'.' + variant if variant else ''}.json").read_text())
    o = np.array(spec["origin_plan_m"])
    pts, cam = clip_points(clip)
    P = np.c_[pts[:, 1] - o[1], pts[:, 0] - o[0]]   # -> spec (x, z)
    Cs = np.c_[cam[:, 1] - o[1], cam[:, 0] - o[0]]
    rows = []
    for s in spec["spaces"]:
        poly = np.array(s["polygon_xz"])
        # only points seen by a camera standing in this space: they can only be this room's inner wall faces
        ucam, inv = np.unique(np.round(Cs, 3), axis=0, return_inverse=True)
        incam = np.array([inside(poly, c) for c in ucam])[inv.ravel()]
        if not incam.any():
            continue
        for v0, v1 in zip(poly, np.roll(poly, -1, 0)):
            along_x = abs(v0[1] - v1[1]) < 1e-6
            k = 1 if along_x else 0                   # coordinate that is constant along the wall
            lo, hi = sorted((v0[1 - k], v1[1 - k]))
            if hi - lo < 0.5:
                continue
            c = v0[k]
            mid = (v0 + v1) / 2
            probe = mid.copy(); probe[k] += 0.05
            inward = 1.0 if inside(poly, probe) else -1.0       # side of the wall the room is on
            off_all = (P[:, k] - c) * -inward                  # + = beyond the spec wall (room really bigger)
            sel = incam & (P[:, 1 - k] > lo + 0.1) & (P[:, 1 - k] < hi - 0.1) & (off_all > -INSIDE) & (off_all < OUTSIDE)
            if sel.sum() < MIN_PTS:
                continue
            off = off_all[sel]
            hist, e = np.histogram(off, bins=np.arange(-INSIDE, OUTSIDE + 0.001, 0.02))
            peak = (e[np.argmax(hist)] + e[np.argmax(hist) + 1]) / 2
            share = hist.max() / sel.sum()
            rows.append((s["name"], "z" if along_x else "x", round(float(c), 2), round(hi - lo, 2), int(sel.sum()), peak * 100, share))
    print(f"{clip}{' (' + variant + ')' if variant else ''}: wall offset = where the clip's wall points peak relative to the spec wall "
          f"(+ = real wall further out, room bigger). |offset| > {TOL_CM:.0f} cm flagged")
    print(f"{'space':<22} {'wall':<10} {'len m':>5} {'pts':>7} {'offset cm':>9} {'peak share':>10}")
    bad = 0
    for n, ax, c, L, cnt, off, sh in sorted(rows, key=lambda r: -abs(r[5])):
        flag = abs(off) > TOL_CM and sh > 0.15
        bad += flag
        print(f"{n:<22} {ax}={c:<8} {L:5.2f} {cnt:7d} {off:+9.0f} {sh:10.2f}{'  <-- check' if flag else ''}")
    print(f"{len(rows)} walls seen from inside, {bad} flagged (an inward offset can be furniture against the wall: look before moving it)")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "")
