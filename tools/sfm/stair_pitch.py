"""Stair pitch from one frame by vanishing points: no depth, so immune to SfM depth/focal distortion along the flight.

Line families (LSD segments): verticals (casings, balusters), wall horizontals (picture-frame tops/bottoms inside a
box on the stair wall), and pitch lines (skirting/wallpaper line, handrail: all parallel to the nosing line).
Each family -> vanishing point -> 3D direction d = K^-1 vp. Pitch = 90 deg - angle(pitch direction, vertical): only
the two strong families. Checks: vertical vs wall-horizontal must be 90 deg (validates the focal); pitch via the
picture frames (they hang slightly crooked, so a few degrees of disagreement is expected; check only).
usage: uv run --with numpy --with opencv-python-headless python tools/sfm/stair_pitch.py <frame.jpg> <focal_px> <x0,y0,x1,y1 wall box> [out.jpg]
"""
import sys

import cv2
import numpy as np


def segments(gray, min_len):
    L = cv2.createLineSegmentDetector(0).detect(gray)[0].reshape(-1, 4)
    ln = np.hypot(L[:, 2] - L[:, 0], L[:, 3] - L[:, 1])
    L = L[ln > min_len]
    ang = np.degrees(np.arctan2(-(L[:, 3] - L[:, 1]), L[:, 2] - L[:, 0])) % 180
    return L, ang


def vanishing_point(L, iters=2000, tol_deg=0.6, seed=0):
    """RANSAC on segment pairs; inlier = segment points at the VP within tol_deg. Refit: least squares on inliers."""
    p1 = np.c_[L[:, :2], np.ones(len(L))]; p2 = np.c_[L[:, 2:], np.ones(len(L))]
    lines = np.cross(p1, p2); lines /= np.linalg.norm(lines[:, :2], axis=1, keepdims=True)
    mid = (L[:, :2] + L[:, 2:]) / 2; dirs = L[:, 2:] - L[:, :2]; dirs /= np.linalg.norm(dirs, axis=1, keepdims=True)
    lens = np.hypot(*(L[:, 2:] - L[:, :2]).T)

    def err(vp):   # angle between each segment and the line from its midpoint to the VP (VP may be at infinity)
        to = vp[:2] - mid * vp[2]
        to /= np.linalg.norm(to, axis=1, keepdims=True) + 1e-12
        return np.degrees(np.arccos(np.clip(np.abs((to * dirs).sum(1)), 0, 1)))

    rng = np.random.default_rng(seed); best = None
    for _ in range(iters):
        i, j = rng.choice(len(L), 2, replace=False)
        vp = np.cross(lines[i], lines[j])
        if not np.isfinite(vp).all() or np.linalg.norm(vp) == 0:
            continue
        inl = err(vp) < tol_deg
        score = lens[inl].sum()
        if best is None or score > best[0]:
            best = (score, inl)
    inl = best[1]
    A = lines[inl] * lens[inl, None]
    vp = np.linalg.svd(A)[2][-1]
    return vp, inl, float(np.median(err(vp)[inl]))


def direction(vp, f, c):
    d = np.array([vp[0] - c[0] * vp[2], vp[1] - c[1] * vp[2], f * vp[2]])
    return d / np.linalg.norm(d)


def measure(path, f, box, out=None, verbose=True):
    im = cv2.imread(path); g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    h, w = g.shape; c = (w / 2, h / 2)
    L, ang = segments(g, 30)
    mid = (L[:, :2] + L[:, 2:]) / 2
    x0, y0, x1, y1 = box
    inbox = (mid[:, 0] > x0) & (mid[:, 0] < x1) & (mid[:, 1] > y0) & (mid[:, 1] < y1)
    fam = {"vertical": np.abs(ang - 90) < 8,
           "wall_h": ((ang < 15) | (ang > 165)) & inbox,
           "pitch": (ang > 20) & (ang < 60) & (np.hypot(*(L[:, 2:] - L[:, :2]).T) > 80)}
    vps, dirs, used = {}, {}, {}
    for k, sel in fam.items():
        if sel.sum() < 2:
            return {"frame": path, "ok": False, "why": f"no {k} lines"}
        vp, inl, e = vanishing_point(L[sel])
        vps[k], used[k] = vp, (L[sel][inl], e)
        dirs[k] = direction(vp, f, c)
    dv, dh, ds = dirs["vertical"], dirs["wall_h"], dirs["pitch"]
    ortho = np.degrees(np.arccos(abs(dv @ dh)))
    n_wall = np.cross(dv, dh); n_wall /= np.linalg.norm(n_wall)
    coplanar = np.degrees(np.arcsin(abs(ds @ n_wall)))
    ds_in = ds - (ds @ n_wall) * n_wall; ds_in /= np.linalg.norm(ds_in)
    pitch = np.degrees(np.arcsin(abs(ds @ dv)))          # needs only the vertical and pitch families
    pitch_wall = np.degrees(np.arctan2(abs(ds_in @ dv), abs(ds_in @ dh)))   # via picture frames (hung crooked: check only)
    res = {"frame": path, "focal": f, "pitch_deg": round(float(pitch), 2), "rise_over_going": round(float(np.tan(np.radians(pitch))), 4),
           "pitch_via_picture_frames_deg": round(float(pitch_wall), 2),
           "vertical_vs_wallh_deg": round(float(ortho), 2), "pitch_off_wall_plane_deg": round(float(coplanar), 2),
           "segments": {k: int(len(v[0])) for k, v in used.items()},
           "pitch_len_px": round(float(np.hypot(*(used["pitch"][0][:, 2:] - used["pitch"][0][:, :2]).T).sum())),
           "fit_err_deg": {k: round(v[1], 3) for k, v in used.items()}}
    # gate: the pitch VP needs two separate physical lines (skirting + handrail); one line can't fix a VP
    pts = used["pitch"][0]
    spread = np.ptp(((pts[:, :2] + pts[:, 2:]) / 2) @ np.array([-np.sin(np.radians(35)), np.cos(np.radians(35))]))
    res["pitch_line_separation_px"] = round(float(spread))
    res["ok"] = bool(len(pts) >= 4 and res["pitch_len_px"] >= 1000 and spread > 150 and abs(ortho - 90) < 1.5
                     and abs(pitch - pitch_wall) < 2.0 and coplanar < 8.0)
    if verbose:
        print(res)
    if out:
        col = {"vertical": (0, 0, 255), "wall_h": (0, 255, 0), "pitch": (255, 0, 0)}
        for k, (segs, _) in used.items():
            for x1_, y1_, x2_, y2_ in segs:
                cv2.line(im, (int(x1_), int(y1_)), (int(x2_), int(y2_)), col[k], 3)
        cv2.rectangle(im, (int(x0), int(y0)), (int(x1), int(y1)), (0, 255, 255), 2)
        cv2.imwrite(out, cv2.resize(im, (1280, int(1280 * h / w))))
    return res


def selftest():
    """Render line drawings of a stair wall at known pitch (30/35/40 deg) with a known camera, measure them back.
    Also: measure with a 10% wrong focal (sensitivity), and with only one pitch line (must fail the gate)."""
    import tempfile
    W_, H_, F = 1920, 1080, 1510.0
    def render(pitch, two_lines=True, yaw=25):
        R = cv2.Rodrigues(np.array([0.0, np.radians(yaw), 0.0]))[0] @ cv2.Rodrigues(np.array([np.radians(-8), 0, 0]))[0]
        t = np.array([0.0, 0.0, 4.0])
        def proj(P):
            X = (R @ np.asarray(P, float).T).T + t
            return np.c_[F * X[:, 0] / X[:, 2] + W_ / 2, F * X[:, 1] / X[:, 2] + H_ / 2]
        img = np.full((H_, W_, 3), 230, np.uint8)
        def seg(a, b, w=4):
            p = proj([a, b]).astype(int); cv2.line(img, tuple(p[0]), tuple(p[1]), (40, 40, 40), w)
        tp = np.tan(np.radians(pitch))   # wall plane z=0, x along wall, y down
        for off in ([0, 0.0], [0, 0.9]) if two_lines else ([0, 0.0],):
            seg([-1.5, 1.0 + off[1], 0], [1.5, 1.0 + off[1] - 3 * tp, 0], 6)
        for x in np.linspace(-1.8, 1.8, 10):          # verticals (casings, balusters)
            seg([x, -1.2, 0.05], [x, 1.4, 0.05])
        for x, y in [(-1.2, -1.0), (-0.6, -0.8), (0.0, -1.1), (0.5, -0.7), (-0.9, -0.3)]:   # picture frames
            for dy in (0, 0.25):
                seg([x, y + dy, 0], [x + 0.3, y + dy, 0])
        f = tempfile.NamedTemporaryFile(suffix=".jpg", delete=False).name
        cv2.imwrite(f, img)
        return f
    ok = True
    for pitch in (30, 35, 40):
        r = measure(render(pitch), F, (0, 0, W_, H_), verbose=False)
        r10 = measure(render(pitch), F * 1.1, (0, 0, W_, H_), verbose=False)
        good = r["ok"] and abs(r["pitch_deg"] - pitch) < 0.5
        ok &= good
        print(f"true {pitch}: measured {r['pitch_deg']} (gate {r['ok']}), focal +10%: {r10['pitch_deg']}  {'PASS' if good else 'FAIL'}")
    r1 = measure(render(35, two_lines=False), F, (0, 0, W_, H_), verbose=False)
    print(f"one pitch line only: gate {r1['ok']}  {'PASS' if not r1['ok'] else 'FAIL'}")
    ok &= not r1["ok"]
    return ok


if __name__ == "__main__" and sys.argv[1:] == ["--selftest"]:
    sys.exit(0 if selftest() else 1)
elif __name__ == "__main__":
    path, f, box = sys.argv[1], float(sys.argv[2]), tuple(map(float, sys.argv[3].split(",")))
    measure(path, f, box, sys.argv[4] if len(sys.argv) > 4 else None)
