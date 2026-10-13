"""Calibrate an angled overhead render without SfM-measured rooms: the faster route (skill: overhead-floor).

All walls are square to each other, so the image's two wall-direction vanishing points fix the projective part:
lines through each VP become the plan's x and y axes. What is left is one aspect (x vs y stretch) and one scale.
  - aspect: from ONE room whose proportions were measured elsewhere (a gated SfM clip, scale-free)
  - scale:  every anchor in the spec gives its own m/px; they are reported side by side and must agree
Wall-top inner corners all lie in one plane; anchors on another plane (a floor-level stair) carry a plane bias,
so the spec marks each anchor's plane and only wall-top anchors set the scale.
Writes <spec>.H.txt (overhead px -> plan metres) for tools/sfm/overhead_plan.py, and prints every check.
usage: uv run --with numpy --with opencv-python-headless python tools/sfm/overhead_rectify.py measurements/overhead/<floor>.json
       ... --selftest   (synthetic overhead with a known plan: must recover it)
"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]


def wall_vps(img_path, seed=0):
    import cv2
    sys.path.insert(0, str(ROOT / "tools/sfm"))
    from stair_pitch import segments, vanishing_point
    g = cv2.cvtColor(cv2.imread(str(ROOT / img_path)), cv2.COLOR_BGR2GRAY)
    L, ang = segments(g, 40)
    out = []
    for sel in ((ang < 30) | (ang > 150), (ang > 60) & (ang < 120)):
        vp, inl, e = vanishing_point(L[sel], tol_deg=0.5, seed=seed)
        out.append((vp / np.linalg.norm(vp), int(inl.sum()), e))
    return out


def projective(vx, vy, origin):
    """H0 sending vx -> x direction, vy -> y direction, origin pixel -> (0,0)."""
    o = np.array([origin[0], origin[1], 1.0])
    return np.linalg.inv(np.c_[vx, vy, o])


def apply(H, px):
    q = np.c_[np.asarray(px, float), np.ones(len(px))] @ H.T
    return q[:, :2] / q[:, 2:]


def rect_dims(P):
    """Side lengths of a traced quad (TL, TR, BR, BL) in rectified units: mean of opposite sides."""
    w = (np.linalg.norm(P[1] - P[0]) + np.linalg.norm(P[2] - P[3])) / 2
    h = (np.linalg.norm(P[3] - P[0]) + np.linalg.norm(P[2] - P[1])) / 2
    return w, h


def area(P):
    x, y = P.T
    return 0.5 * abs(x @ np.roll(y, -1) - y @ np.roll(x, -1))


def calibrate(spec, vps):
    (vx, *_), (vy, *_) = vps
    H0 = projective(vx, vy, spec["origin_px"])
    # orient: image right -> +x, image down -> +y
    t = apply(H0, [spec["origin_px"], [spec["origin_px"][0] + 100, spec["origin_px"][1]], [spec["origin_px"][0], spec["origin_px"][1] + 100]])
    sx, sy = np.sign(t[1, 0] - t[0, 0]), np.sign(t[2, 1] - t[0, 1])
    a = spec["aspect"]
    w, h = rect_dims(apply(np.diag([sx, sy, 1]) @ H0, a["pixels"]))
    k = (w / h) / a["ratio_w_over_h"]          # stretch y by k so the room's w/h matches its measurement
    H1 = np.diag([sx, sy * k, 1]) @ H0
    scales = []
    for s in spec["scale"]:
        P = apply(H1, s["pixels"])
        if s["kind"] == "length":
            got = np.linalg.norm(P[1] - P[0]); mpu = s["metres"] / got
        else:                                    # "area": polygon of known floor area (m^2)
            got = area(P); mpu = np.sqrt(s["m2"] / got)
        scales.append((s, mpu))
    use = [m for s, m in scales if s.get("use", True)]
    mpu = float(np.median(use))
    H = np.diag([mpu, mpu, 1]) @ H1
    return H, scales, mpu


def main(path):
    spec = json.loads(Path(path).read_text())
    vps = wall_vps(spec["image"])
    print("wall-direction lines: " + ", ".join(f"{n} inliers, fit {e:.2f} deg" for _, n, e in vps))
    H, scales, mpu = calibrate(spec, vps)
    print("\nscale anchors (m per rectified unit); 'use' anchors set the scale, the rest are checks:")
    for s, m in scales:
        print(f"  {'USE  ' if s.get('use', True) else 'check'} {s['name']:<44} {m:.5f}  ({m / mpu - 1:+.1%})")
    print("\nchecks:")
    for c in spec.get("checks", []):
        P = apply(H, c["pixels"])
        if c["kind"] == "area_m2":
            got = area(P); print(f"  {c['name']:<46} {got:6.1f} m2 vs {c['m2']:.1f} ({got / c['m2'] - 1:+.1%})")
        elif c["kind"] == "ratio":
            w, h = rect_dims(P); print(f"  {c['name']:<46} w/h {w / h:.3f} vs {c['ratio_w_over_h']:.3f} ({(w / h) / c['ratio_w_over_h'] - 1:+.1%})")
        elif c["kind"] == "dims":
            w, h = rect_dims(P); print(f"  {c['name']:<46} {w:.2f} x {h:.2f} m vs {c['w']:.2f} x {c['h']:.2f} ({w / c['w'] - 1:+.1%}, {h / c['h'] - 1:+.1%})")
    out = Path(path).with_suffix(".H.txt")
    np.savetxt(out, H)
    print(f"\nwrote {out}")


def selftest():
    """Project a known plan with a known camera, rectify it back from VPs + one aspect + one area."""
    rng = np.random.default_rng(1)
    K = np.array([[1500, 0, 960], [0, 1500, 540], [0, 0, 1.0]])
    R = __import__("cv2").Rodrigues(np.array([np.radians(35), 0.0, np.radians(4)]))[0]
    t = np.array([-4.0, -2.0, 18.0])
    Ph = lambda X: (lambda q: q[:, :2] / q[:, 2:])((np.c_[X, np.zeros(len(X))] @ R.T + t) @ K.T)
    rooms = {"A": (0, 0, 4.0, 7.0), "B": (4.2, 0, 9.0, 5.0), "C": (9.2, -3, 13.0, 5.0)}
    quad = lambda r: np.array([[r[0], r[1]], [r[2], r[1]], [r[2], r[3]], [r[0], r[3]]])
    px = {k: Ph(quad(r)) + rng.normal(0, 0.8, (4, 2)) for k, r in rooms.items()}
    # VPs straight from the camera (the image path is tested on real data)
    vx = K @ R @ [1, 0, 0]; vy = K @ R @ [0, 1, 0]
    spec = {"origin_px": px["A"][0].tolist(), "aspect": {"pixels": px["A"].tolist(), "ratio_w_over_h": 4 / 7},
            "scale": [{"name": "B area", "kind": "area", "pixels": px["B"].tolist(), "m2": 4.8 * 5}]}
    H, _, _ = calibrate(spec, [(vx / np.linalg.norm(vx), 0, 0), (vy / np.linalg.norm(vy), 0, 0)])
    w, h = rect_dims(apply(H, px["C"]))
    ok = abs(w - 3.8) < 0.08 and abs(h - 8.0) < 0.12
    print(f"selftest: room C recovered {w:.2f} x {h:.2f} m (true 3.80 x 8.00) -> {'PASS' if ok else 'FAIL'}")
    spec["aspect"]["ratio_w_over_h"] = 4 / 7 * 1.10          # a 10% wrong aspect must show up in C
    H, _, _ = calibrate(spec, [(vx / np.linalg.norm(vx), 0, 0), (vy / np.linalg.norm(vy), 0, 0)])
    w2, h2 = rect_dims(apply(H, px["C"]))
    bad = abs((w2 / h2) / (w / h) - 1) > 0.08
    print(f"selftest: with a 10% wrong aspect, room C reads {w2:.2f} x {h2:.2f} -> {'detected' if bad else 'NOT detected'}")
    return ok and bad


if __name__ == "__main__":
    if sys.argv[1:] == ["--selftest"]:
        sys.exit(0 if selftest() else 1)
    main(sys.argv[1])
