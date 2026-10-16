"""rig_check: Marina's camera height as a multiple of a door's height, read from single frames with no scale and no SfM.

Why (Oct 15): the posed review stills give her eye height 1.27-1.40 m in rooms scaled from 80 in doors but 1.09-1.19 m in rooms
scaled another way (hall: passage width; hall bath, kitchen, living: overhead traces). If her CG camera height is fixed, that
split is a scale error in those rooms. This tool measures the ratio h/H (camera height / door height) straight from pixels:
single-view metrology (Criminisi 2000): the cross ratio of the door edge's foot b, top t, its meeting i with the horizon, and the
vertical vanishing point V equals that of heights 0, H, h, infinity, so h/H = k/(k-1) with k = CR(b, t; i, V).

Labels (pixels, 1920x1080 Marina frames; every point is snapped to the strongest edge within --snap px before use):
  [{"frame": "marina2-178", "room": "parents", "h_lines": [[[u,v],[u,v]], ...],   # >=2 lines that are level in the world and
                                                                                 # parallel (one family): their VP is on the horizon
    "h_lines2": [...],                     # optional second level family: horizon = line through both VPs (else level horizon)
    "v_lines": [[[u,v],[u,v]], ...],       # optional verticals (door jambs, corners): V by least squares, else from f and pitch
    "objects": [{"name": "hall door", "b": [u,v], "t": [u,v]}]}]                 # b = jamb foot on the floor, t = under the head

  rig_check.py selftest               synthetic frames: exact recovery, 1 px noise spread, and an injected wrong door is flagged
  rig_check.py measure LABELS.json [--f 1428] [--snap 4] [--overlay]   per object h/H and h for an 80 in door; per-room summary
"""
import argparse
import json
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
FRAMES = ROOT / "sfm-work/refcam/frames"
DOOR = 80 * 0.0254
F_DEFAULT = 1428.0   # Marina foyer solves 312 s / 1068 s (f 1419 / 1438 at 1920 wide); only used when no v_lines are given


def hom(p):
    return np.array([p[0], p[1], 1.0])


def vp(lines):
    """Least-squares intersection of 2+ image lines, each given by two points."""
    L = np.array([np.cross(hom(a), hom(b)) for a, b in lines])
    L /= np.linalg.norm(L[:, :2], axis=1, keepdims=True)
    return np.linalg.svd(L)[2][-1]


def cr(a, b, c, d):
    return ((c - a) * (d - b)) / ((c - b) * (d - a))


def ratio(b, t, horizon, V):
    """h/H for a vertical segment b (foot) .. t (top), horizon line (homogeneous), vertical VP V (homogeneous)."""
    b, t = np.asarray(b, float), np.asarray(t, float)
    line = np.cross(hom(b), hom(t))
    i = np.cross(line, horizon)
    d = (t - b) / np.linalg.norm(t - b)
    s = lambda P: (P[:2] / P[2] - b) @ d if abs(P[2]) > 1e-12 else np.inf * np.sign(P[:2] @ d)
    k = cr(0.0, s(hom(t)), s(i), s(V)) if np.isfinite(s(V)) else (s(i) - 0.0) / (s(i) - s(hom(t)))
    return k / (k - 1)


def horizon_of(fr, f, cx, cy):
    v1 = vp(fr["h_lines"])
    if fr.get("h_lines2"):
        return np.cross(v1, vp(fr["h_lines2"])), v1
    v1n = v1[:2] / v1[2]
    return np.array([0.0, 1.0, -v1n[1]]), v1          # level horizon through the VP (roll 0)


def auto_vertical_vp(path, min_len=40, max_tilt_deg=12, iters=400, tol_deg=0.6, seed=0):
    """Vertical VP from every near-vertical edge segment in the frame (Canny + probabilistic Hough, RANSAC on angle error)."""
    import cv2
    g = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    e = cv2.Canny(cv2.GaussianBlur(g, (3, 3), 0), 40, 120)
    segs = cv2.HoughLinesP(e, 1, np.pi / 720, 40, minLineLength=min_len, maxLineGap=3)
    segs = [] if segs is None else segs.reshape(-1, 4).astype(float)
    S = [s for s in segs if abs(np.degrees(np.arctan2(s[2] - s[0], s[3] - s[1]))) % 180 < max_tilt_deg
         or abs(np.degrees(np.arctan2(s[2] - s[0], s[3] - s[1]))) % 180 > 180 - max_tilt_deg]
    if len(S) < 8:
        return None, 0
    S = np.array(S); L = np.array([np.cross(hom(s[:2]), hom(s[2:])) for s in S]); L /= np.linalg.norm(L[:, :2], axis=1, keepdims=True)
    mid = (S[:, :2] + S[:, 2:]) / 2; ln = np.linalg.norm(S[:, 2:] - S[:, :2], axis=1)

    def err(V):   # angle between each segment and the direction from its midpoint to V
        d = V[:2] - mid * V[2]; d /= np.linalg.norm(d, axis=1, keepdims=True) + 1e-12
        u = (S[:, 2:] - S[:, :2]) / ln[:, None]
        return np.degrees(np.arccos(np.clip(np.abs((d * u).sum(1)), 0, 1)))
    rng = np.random.default_rng(seed); best = None
    for _ in range(iters):
        i, j = rng.choice(len(S), 2, replace=False); V = np.cross(L[i], L[j])
        if np.linalg.norm(V) < 1e-12:
            continue
        inl = err(V) < tol_deg; score = ln[inl].sum()
        if best is None or score > best[0]:
            best = (score, inl)
    inl = best[1]; W = L[inl] * ln[inl, None]
    V = np.linalg.svd(W)[2][-1]
    return V, int(inl.sum())


def segments(path, min_len=40):
    import cv2
    g = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
    e = cv2.Canny(cv2.GaussianBlur(g, (3, 3), 0), 40, 120)
    S = cv2.HoughLinesP(e, 1, np.pi / 720, 40, minLineLength=min_len, maxLineGap=3)
    return np.zeros((0, 4)) if S is None else S.reshape(-1, 4).astype(float)


def ransac_vp(S, iters=600, tol_deg=0.5, seed=0):
    L = np.array([np.cross(hom(s[:2]), hom(s[2:])) for s in S]); L /= np.linalg.norm(L[:, :2], axis=1, keepdims=True)
    mid = (S[:, :2] + S[:, 2:]) / 2; ln = np.linalg.norm(S[:, 2:] - S[:, :2], axis=1); u = (S[:, 2:] - S[:, :2]) / ln[:, None]

    def err(V):
        d = V[:2] - mid * V[2]; d /= np.linalg.norm(d, axis=1, keepdims=True) + 1e-12
        return np.degrees(np.arccos(np.clip(np.abs((d * u).sum(1)), 0, 1)))
    rng = np.random.default_rng(seed); best = None
    for _ in range(iters):
        i, j = rng.choice(len(S), 2, replace=False); V = np.cross(L[i], L[j])
        if np.linalg.norm(V) < 1e-12:
            continue
        inl = err(V) < tol_deg; sc = ln[inl].sum()
        if best is None or sc > best[0]:
            best = (sc, inl)
    inl = best[1]
    return np.linalg.svd(L[inl] * ln[inl, None])[2][-1], inl


def auto_level_vp(path, V, f, cx, cy, min_tilt=6.0):
    """VP of receding level edges: segments that are neither near-vertical (towards V) nor near-horizontal, RANSAC.
    Returns the VP, inlier count, and the focal length implied by its orthogonality to V (None if not real)."""
    S = segments(path)
    ang = np.degrees(np.arctan2(S[:, 3] - S[:, 1], S[:, 2] - S[:, 0])) % 180
    keep = (np.minimum(ang, 180 - ang) > min_tilt) & (np.abs(ang - 90) > 15)
    S = S[keep]
    if len(S) < 6:
        return None, 0, None
    H, inl = ransac_vp(S)
    a = H[:2] / H[2] - [cx, cy] if abs(H[2]) > 1e-9 else None
    b = V[:2] / V[2] - [cx, cy] if abs(V[2]) > 1e-9 else None
    f2 = -(a @ b) if a is not None and b is not None else None
    return H, int(inl.sum()), (np.sqrt(f2) if f2 and f2 > 0 else None)


def level_inliers(path, V, min_tilt=6.0):
    S = segments(path)
    ang = np.degrees(np.arctan2(S[:, 3] - S[:, 1], S[:, 2] - S[:, 0])) % 180
    S = S[(np.minimum(ang, 180 - ang) > min_tilt) & (np.abs(ang - 90) > 15)]
    if len(S) < 6:
        return []
    _, inl = ransac_vp(S)
    return S[inl].tolist()


def horizon_from_v(V, f, cx, cy):
    """Vanishing line of the planes orthogonal to direction V: l = K^-T K^-1 V."""
    Ki = np.array([[1 / f, 0, -cx / f], [0, 1 / f, -cy / f], [0, 0, 1]])
    return Ki.T @ Ki @ V


def vertical_vp(fr, horizon, f, cx, cy):
    if fr.get("V") is not None:
        return np.array(fr["V"], float)
    if fr.get("v_lines") and len(fr["v_lines"]) >= 2:
        return vp(fr["v_lines"])
    vh = -(horizon[0] * cx + horizon[2]) / horizon[1]   # horizon row at the centre column
    if abs(cy - vh) < 1e-6:
        return np.array([0.0, 1.0, 0.0])                # level camera: V at infinity straight down
    return np.array([cx, cy + f * f / (cy - vh), 1.0])


# ---------- snapping ----------
def gray(path):
    from PIL import Image, ImageFilter
    return np.asarray(Image.open(path).convert("L").filter(ImageFilter.GaussianBlur(1.0)), float)


def snap_along(G, p, n, r):
    """Move p along unit direction n (|step| <= r) to the strongest intensity edge; sub-pixel by parabola."""
    if r <= 0:
        return np.asarray(p, float)
    p, n = np.asarray(p, float), np.asarray(n, float)
    ts = np.arange(-r - 1, r + 2)
    val = []
    for t in ts:
        x, y = p + t * n
        xi, yi = int(round(x)), int(round(y))
        val.append(G[np.clip(yi, 0, G.shape[0] - 1), np.clip(xi, 0, G.shape[1] - 1)])
    g = np.abs(np.gradient(np.array(val)))[1:-1]; tt = ts[1:-1]
    k = int(np.argmax(g))
    off = 0.0
    if 0 < k < len(g) - 1:
        den = g[k - 1] - 2 * g[k] + g[k + 1]
        off = 0.5 * (g[k - 1] - g[k + 1]) / den if den != 0 else 0.0
    return p + (tt[k] + off) * n


def snap_frame(fr, G, r):
    out = json.loads(json.dumps(fr)); moves = []
    for key in ("h_lines", "h_lines2", "v_lines"):
        for ln in out.get(key, []) or []:
            a, b = np.array(ln[0], float), np.array(ln[1], float)
            d = (b - a) / np.linalg.norm(b - a); n = np.array([-d[1], d[0]])
            for j in range(2):
                q = snap_along(G, ln[j], n, r); moves.append(np.linalg.norm(q - ln[j])); ln[j] = q.tolist()
    for o in out["objects"]:
        d = np.array(o["t"], float) - np.array(o["b"], float); d /= np.linalg.norm(d)
        for key in ("b", "t"):
            q = snap_along(G, o[key], d, r); moves.append(np.linalg.norm(q - o[key])); o[key] = q.tolist()
    return out, moves


# ---------- commands ----------
def horizon_through(Hv, V, cx, cy):
    """Horizon through a level VP Hv, perpendicular to the image vertical through the principal point (sets the roll)."""
    h = Hv[:2] / Hv[2]
    n = V[:2] - np.array([cx, cy]) * V[2]; n /= np.linalg.norm(n)
    return np.array([n[0], n[1], -n @ h])


def measure_frame(fr, f, cx=960.0, cy=540.0):
    if fr.get("V") is not None and fr.get("H_level") is not None and not fr.get("h_lines"):
        V = np.array(fr["V"], float); horizon = horizon_through(np.array(fr["H_level"], float), V, cx, cy)
        return [(o["name"], ratio(o["b"], o["t"], horizon, V)) for o in fr["objects"]], horizon, V
    if fr.get("V") is not None and not fr.get("h_lines"):
        V = np.array(fr["V"], float); horizon = horizon_from_v(V, f, cx, cy)
        return [(o["name"], ratio(o["b"], o["t"], horizon, V)) for o in fr["objects"]], horizon, V
    horizon, v1 = horizon_of(fr, f, cx, cy)
    V = vertical_vp(fr, horizon, f, cx, cy)
    return [(o["name"], ratio(o["b"], o["t"], horizon, V)) for o in fr["objects"]], horizon, V


def cmd_measure(a):
    frames = json.loads(Path(a.labels).read_text()); rows = []
    for fr in frames:
        path = FRAMES / f"{fr['frame']}.jpg"
        moves = []
        if not fr.get("h_lines") and path.exists():
            V, n = auto_vertical_vp(path); fr["V"] = V.tolist(); fr["n_vertical_segments"] = n
            hz = horizon_from_v(V, a.f, 960.0, 540.0); vh = -(hz[0] * 960 + hz[2]) / hz[1]
            Hv, nh, f_est = auto_level_vp(path, V, a.f, 960.0, 540.0)
            hv_row = Hv[1] / Hv[2] if Hv is not None and abs(Hv[2]) > 1e-9 else float("nan")
            # the level VP's row, moved to the centre column along the horizon from V (same roll)
            hv_c = hv_row + (-(hz[0] / hz[1])) * (960 - Hv[0] / Hv[2]) if Hv is not None and abs(Hv[2]) > 1e-9 else float("nan")
            if Hv is not None and nh >= 6 and not a.horizon_from_v:
                fr["H_level"] = Hv.tolist(); fr["level_inliers"] = level_inliers(path, V)
            fr["horizon_check"] = {"from_V_and_f": round(vh, 1), "from_level_edges": round(hv_c, 1), "n_level": nh, "f_from_orthogonality": round(f_est, 0) if f_est else None}
            print(f"{fr['frame']}: V from {n} verticals -> horizon row {vh:.1f}; level VP from {nh} edges -> row {hv_c:.1f}; f from orthogonality {f_est if f_est is None else round(f_est)}")
        if a.snap and path.exists():
            fr, moves = snap_frame(fr, gray(path), a.snap)
        res, horizon, V = measure_frame(fr, a.f)
        # sensitivity: re-measure with every point jittered 1 px (labelling noise), 200 draws
        rng = np.random.default_rng(0); jit = []
        for _ in range(200):
            g = json.loads(json.dumps(fr))
            for key in ("h_lines", "h_lines2", "v_lines"):
                for ln in g.get(key, []) or []:
                    for j in range(2):
                        ln[j] = (np.array(ln[j]) + rng.normal(0, 1, 2)).tolist()
            for o in g["objects"]:
                for key in ("b", "t"):
                    o[key] = (np.array(o[key]) + rng.normal(0, 1, 2)).tolist()
            jit.append([r for _, r in measure_frame(g, a.f)[0]])
        sd = np.std(np.array(jit), axis=0)
        for (name, r), s in zip(res, sd):
            rows.append({"frame": fr["frame"], "room": fr["room"], "object": name, "h_over_H": round(r, 4), "sd": round(float(s), 4),
                         "h_m_at_80in": round(r * DOOR, 3), "max_snap_px": round(max(moves), 1) if moves else None})
        if a.overlay and path.exists():
            overlay(path, fr, horizon, V)
    for r in rows:
        print(f"{r['frame']:16s} {r['room']:10s} {r['object']:22s} h/H {r['h_over_H']:.3f} ±{r['sd']:.3f}  h(80in) {r['h_m_at_80in']:.3f} m  snap≤{r['max_snap_px']}")
    by = {}
    for r in rows:
        by.setdefault(r["room"], []).append(r["h_over_H"])
    print("\nper room (median h/H, n, h for 80 in doors):")
    allv = [v for vs in by.values() for v in vs]
    med = float(np.median(allv))
    for k, vs in by.items():
        m = float(np.median(vs)); flag = "  <-- off the house median by %+.0f%%" % (100 * (m / med - 1)) if abs(m / med - 1) > 0.05 else ""
        print(f"  {k:10s} {m:.3f}  n={len(vs)}  {m * DOOR:.3f} m{flag}")
    print(f"  all        {med:.3f}  n={len(allv)}  spread {100 * (max(allv) - min(allv)) / med:.1f}%")
    out = Path(a.labels).with_suffix(".result.json"); out.write_text(json.dumps(rows, indent=1)); print(out)


RIG = 0.639   # measured h/H (this tool's `measure`, 6 doors, 4 rooms, spread 2.5%)


def floor_point(p, horizon, h, f, cx=960.0, cy=540.0):
    """Floor point (camera-centred metres) under pixel p, for camera height h and the image horizon line."""
    K = np.array([[f, 0, cx], [0, f, cy], [0, 0, 1]])
    up = K.T @ horizon; up /= np.linalg.norm(up)
    if up @ np.linalg.solve(K, [cx, cy + 400, 1]) > 0:   # rays below the horizon must point down
        up = -up
    r = np.linalg.solve(K, hom(p))
    return r * h / -(up @ r)


def floor_dist(fr, horizon, h, f):
    """Perpendicular distance between two labelled floor lines (wall bases), or between two floor points."""
    L = {k: [floor_point(p, horizon, h, f) for p in v] for k, v in fr["floor"].items()}
    out = []
    for a, b in fr["pairs"]:
        A, B = L[a], L[b]
        if len(A) == 1:
            out.append((f"{a} - {b}", float(np.linalg.norm(A[0] - B[0])), 0.0)); continue
        da = (A[1] - A[0]) / np.linalg.norm(A[1] - A[0]); db = (B[1] - B[0]) / np.linalg.norm(B[1] - B[0])
        mid = (B[0] + B[1]) / 2 - A[0]
        out.append((f"{a} | {b}", float(np.linalg.norm(mid - (mid @ da) * da)), float(np.degrees(np.arccos(min(1, abs(da @ db)))))))
    return out


def cmd_floor(a):
    """Floor distances in Marina frames: horizon from the frame's edges (as `measure`), camera height RIG x 80 in.
    Labels: [{"frame", "room", "h_lines": optional hand-labelled level lines of one family (when the auto horizon is poor), "floor": {"left base": [[u,v],[u,v]], "corner": [[u,v]]}, "pairs": [["left base","right base"]],
              "plan": {"left base | right base": 3.69}}]  (plan = the build's value for that pair, metres)"""
    h = RIG * DOOR; rows = []
    for fr in json.loads(Path(a.labels).read_text()):
        path = FRAMES / f"{fr['frame']}.jpg"
        V, _ = auto_vertical_vp(path)
        Hv, nh = (vp(fr["h_lines"]), -len(fr["h_lines"])) if fr.get("h_lines") else auto_level_vp(path, V, a.f, 960.0, 540.0)[:2]   # n < 0 = hand-labelled
        hz = horizon_through(Hv, V, 960.0, 540.0)
        if a.snap:   # snap each labelled point across its line to the strongest edge
            G = gray(path)
            for k, pts in fr["floor"].items():
                if len(pts) == 2:
                    d = np.subtract(pts[1], pts[0], dtype=float); d /= np.linalg.norm(d); n = [-d[1], d[0]]
                    fr["floor"][k] = [snap_along(G, p, n, a.snap).tolist() for p in pts]
        base = floor_dist(fr, hz, h, a.f)
        vh = -(hz[0] * 960 + hz[2]) / hz[1]
        shift = lambda dv: hz - np.array([0, 0, -dv * hz[1]])       # horizon moved dv px down
        sens = {"f-10%": floor_dist(fr, hz, h, a.f * 0.9), "f+10%": floor_dist(fr, hz, h, a.f * 1.1),
                "hz-3px": floor_dist(fr, shift(-3), h, a.f), "hz+3px": floor_dist(fr, shift(3), h, a.f)}
        for i, (name, d, ang) in enumerate(base):
            var = [s[i][1] for s in sens.values()]; lo, hi = min(var + [d]), max(var + [d])
            plan = fr.get("plan", {}).get(name)
            rows.append({"frame": fr["frame"], "room": fr["room"], "pair": name, "m": round(d, 3), "lo": round(lo, 3), "hi": round(hi, 3),
                         "parallel_deg": round(ang, 1), "horizon_row": round(vh, 1), "n_level": nh, "plan": plan,
                         "diff_pct": round(100 * (d / plan - 1), 1) if plan else None})
        if a.overlay:
            overlay(path, {"frame": fr["frame"], "objects": [], "level_inliers": level_inliers(path, V)}, hz, V, extra=fr["floor"])
    for r in rows:
        pl = f"plan {r['plan']:.2f}  {r['diff_pct']:+.1f}%" if r["plan"] else ""
        print(f"{r['frame']:14s} {r['room']:12s} {r['pair']:34s} {r['m']:.2f} m [{r['lo']:.2f}-{r['hi']:.2f}]  par {r['parallel_deg']:.1f}°  "
              f"hz {r['horizon_row']:.0f} ({r['n_level']} edges)  {pl}")
    out = Path(a.labels).with_suffix(".result.json"); out.write_text(json.dumps(rows, indent=1)); print(out)


def overlay(path, fr, horizon, V, extra=None):
    from PIL import Image, ImageDraw
    im = Image.open(path).convert("RGB"); d = ImageDraw.Draw(im); W = im.width
    yl = lambda x: -(horizon[0] * x + horizon[2]) / horizon[1]
    d.line([(0, yl(0)), (W, yl(W))], fill=(255, 0, 255), width=2)
    for key, col in (("h_lines", (0, 255, 255)), ("h_lines2", (0, 200, 120)), ("v_lines", (255, 200, 0))):
        for ln in fr.get(key, []) or []:
            d.line([tuple(ln[0]), tuple(ln[1])], fill=col, width=2)
    for sgm in fr.get("level_inliers", []):
        d.line([(sgm[0], sgm[1]), (sgm[2], sgm[3])], fill=(0, 255, 0), width=3)
    for o in fr["objects"]:
        d.line([tuple(o["b"]), tuple(o["t"])], fill=(255, 60, 60), width=3)
        d.text((o["t"][0] + 6, o["t"][1]), o["name"], fill=(255, 60, 60))
    for k, pts in (extra or {}).items():
        if len(pts) == 2:
            d.line([tuple(pts[0]), tuple(pts[1])], fill=(255, 140, 0), width=3)
        for p in pts:
            d.ellipse([p[0] - 5, p[1] - 5, p[0] + 5, p[1] + 5], outline=(255, 140, 0), width=2)
        d.text((pts[0][0] + 8, pts[0][1] - 18), k, fill=(255, 140, 0))
    out = ROOT / "sfm-work/rig" / f"{fr['frame']}-overlay.jpg"; out.parent.mkdir(parents=True, exist_ok=True); im.save(out, quality=88)


def cmd_selftest(a):
    """Synthetic camera: known h, pitch, roll 0. Exact recovery; 1 px noise spread; a 10% taller door is flagged."""
    f, cx, cy = 1428.0, 960.0, 540.0

    def project(X, h, pitch, yaw):
        c, s = np.cos(yaw), np.sin(yaw)
        Xc = np.array([c * X[0] - s * X[2], X[1] - h, s * X[0] + c * X[2]])     # yaw about vertical
        cp, sp = np.cos(pitch), np.sin(pitch)
        y2, z2 = cp * Xc[1] - sp * Xc[2], sp * Xc[1] + cp * Xc[2]               # pitch (positive looks up)
        return [cx + f * Xc[0] / z2, cy - f * y2 / z2]

    def scene(h, pitch, yaw, Hdoor, rng=None, noise=0.0):
        P = lambda X: (np.array(project(np.array(X, float), h, pitch, yaw)) + (rng.normal(0, noise, 2) if rng is not None else 0)).tolist()
        wall = 4.0
        return {"frame": "synthetic", "room": "test",
                "h_lines": [[P([wall, 0, 2]), P([wall, 0, 7])], [P([wall, 2.44, 2]), P([wall, 2.44, 7])], [P([wall, Hdoor, 4.0]), P([wall, Hdoor, 4.9])]],
                "v_lines": [[P([wall, 0, 4.0]), P([wall, Hdoor, 4.0])], [P([wall, 0, 4.9]), P([wall, Hdoor, 4.9])], [P([wall, 0, 6.5]), P([wall, 2.44, 6.5])]],
                "objects": [{"name": "door", "b": P([wall, 0, 4.0]), "t": P([wall, Hdoor, 4.0])}]}

    ok = True
    for h, pitch, yaw in ((1.32, np.radians(-3.0), 0.3), (1.09, np.radians(-7.0), -0.2), (1.5, np.radians(2.0), 0.5)):
        for use_v in (True, False):
            fr = scene(h, pitch, yaw, DOOR)
            if not use_v:
                fr.pop("v_lines")
            r = measure_frame(fr, f)[0][0][1]
            good = abs(r - h / DOOR) < 1e-6 if use_v else abs(r - h / DOOR) < 1e-3
            ok &= good
            print(f"exact   h {h:.2f} pitch {np.degrees(pitch):+.0f}  V from {'jambs' if use_v else 'f+pitch'}: h/H {r:.4f} vs {h / DOOR:.4f}  {'ok' if good else 'FAIL'}")
    for h, pitch in ((1.32, np.radians(-3.0)), (1.09, np.radians(-7.0))):
        fr = scene(h, pitch, 0.3, DOOR); fr["V"] = vp(fr.pop("v_lines")).tolist(); fr.pop("h_lines")
        r = measure_frame(fr, f)[0][0][1]; good = abs(r - h / DOOR) < 1e-6; ok &= good
        print(f"horizon from V and f (auto mode) h {h:.2f}: h/H {r:.4f} vs {h / DOOR:.4f}  {'ok' if good else 'FAIL'}")
    for h, pitch in ((1.29, np.radians(-3.0)), (1.29, np.radians(2.5))):
        fr = scene(h, pitch, 0.3, DOOR); fr["V"] = vp(fr.pop("v_lines")).tolist(); fr["H_level"] = vp(fr.pop("h_lines")).tolist()
        r = measure_frame(fr, f)[0][0][1]; good = abs(r - h / DOOR) < 1e-6; ok &= good
        print(f"horizon through the level VP h {h:.2f} pitch {np.degrees(pitch):+.1f}: h/H {r:.4f} vs {h / DOOR:.4f}  {'ok' if good else 'FAIL'}")
    rng = np.random.default_rng(1)
    rs = [measure_frame(scene(1.32, np.radians(-3), 0.3, DOOR, rng, 1.0), f)[0][0][1] for _ in range(300)]
    spread = np.std(rs) / (1.32 / DOOR)
    print(f"1 px noise: h/H sd {100 * spread:.1f}% of value")
    ok &= spread < 0.03
    # injected error: one room's door 10% taller than 80 in reads as a 10% lower h/H and must be flagged
    rooms = [measure_frame(scene(1.32, np.radians(-3), 0.3, DOOR * k), f)[0][0][1] for k in (1, 1, 1, 1.10)]
    med = np.median(rooms); flagged = [abs(x / med - 1) > 0.05 for x in rooms]
    print(f"injected 10% door: flags {flagged}  {'ok' if flagged == [False, False, False, True] else 'FAIL'}")
    ok &= flagged == [False, False, False, True]
    # floor distances: a 3.40 m wide room (wall bases at x = -1.2 and +2.2) seen yawed and pitched; horizon from the level VP
    for h, pitch, yaw in ((1.30, np.radians(-4.0), 0.25), (1.30, np.radians(3.0), -0.4)):
        P = lambda X: project(np.array(X, float), h, pitch, yaw)
        lines = [[P([-1.2, 0, 3]), P([-1.2, 0, 8])], [P([2.2, 0, 4]), P([2.2, 0, 9])]]
        hz = horizon_through(vp(lines), vp([[P([0, 0, 5]), P([0, 2, 5])], [P([1, 0, 6]), P([1, 2, 6])]]), cx, cy)
        fr = {"floor": {"L": lines[0], "R": lines[1], "a": [P([0.3, 0, 5])], "b": [P([1.5, 0, 6.6])]}, "pairs": [["L", "R"], ["a", "b"]]}
        (_, w, _), (_, dab, _) = floor_dist(fr, hz, h, f)
        good = abs(w - 3.4) < 1e-6 and abs(dab - np.hypot(1.2, 1.6)) < 1e-6; ok &= good
        print(f"floor width 3.40 / points 2.00 (pitch {np.degrees(pitch):+.0f}, yaw {yaw:+.2f}): {w:.4f} / {dab:.4f}  {'ok' if good else 'FAIL'}")
    print("SELFTEST", "PASS" if ok else "FAIL")
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); sp = ap.add_subparsers(dest="cmd", required=True)
    s = sp.add_parser("selftest"); s.set_defaults(fn=cmd_selftest)
    s = sp.add_parser("measure"); s.add_argument("labels"); s.add_argument("--f", type=float, default=F_DEFAULT)
    s.add_argument("--snap", type=int, default=4); s.add_argument("--overlay", action="store_true")
    s.add_argument("--horizon-from-v", action="store_true", help="old mode: horizon from the vertical VP and --f only"); s.set_defaults(fn=cmd_measure)
    s = sp.add_parser("floor"); s.add_argument("labels"); s.add_argument("--f", type=float, default=F_DEFAULT)
    s.add_argument("--snap", type=int, default=3); s.add_argument("--overlay", action="store_true"); s.set_defaults(fn=cmd_floor)
    a = ap.parse_args(); a.fn(a)
