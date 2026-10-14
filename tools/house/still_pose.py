"""Marina's review stills, posed in her own CG rooms and re-rendered from the same camera in both models.

Per still: a VGGT solve of the still's own frame plus ~56 context frames of the same room (job); PnP of the still
from its own point map; gravity from the floor plane; a Manhattan room frame from the wall density peaks (windows
per wall, read off the fit plot: `fit`); metres from Marina's measured room size (measurements/rooms, 80 in door)
or, where none exists, from the measured spec. The pose is then model-independent: distances from the four
named walls, eye height, forward in wall-normal components, vfov. `poses` pins it at the nearest corner in each
model (MODEL_WALLS, by wall function) and writes the RenderViews lists; `triples` lays Marina | September |
grey-box side by side after Unity has rendered.

  uv run --with numpy --with opencv-python-headless --with matplotlib --with pillow python -I tools/house/still_pose.py solve <job>
  ... still_pose.py fit <room>          -> sfm-work/stills/<job>/fit-<room>.png (walls, camera path, stills)
  ... still_pose.py poses               -> spec/captures/sheet-matched/poses.json, spec/captures/views/sheet-matched-{sept,latest}.json
  Unity -batchmode -projectPath unity/HomeAlone -executeMethod SpecGreybox.RenderViews -quit -logFile - -scene IntactHouseReference -views sheet-matched-sept.json -fill 3000 -ev 7.5
  Unity ... -scene Greybox_Upstairs -views sheet-matched-latest.json -fill 3000 -ev 7.5
  ... still_pose.py triples             -> spec/captures/sheet-matched/<still>-{sept,latest}.jpg, <still>-triple.jpg
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
W = ROOT / "sfm-work"
STILLS = W / "stills"
OUT = ROOT / "spec/captures/sheet-matched"
P1 = ROOT / "Tour the Home Alone House_ Part 1, Main Floor [CG Tour] copy.mp4"
P2 = ROOT / "Tour the Home Alone House_ Part 2  [CG Tour].mp4"
sys.path.insert(0, str(ROOT / "tools/sfm"))

# job: (video, still seconds, context frames [(frames dir, first, last, count)]). Frame dirs are 4 fps extractions
# (room.py prepare / extract.sh); ground-fly = Part 1 1060-1192 s, the final main-floor walkthrough.
JOBS = {
    "parents": (P2, [178, 217, 223, 247, 636], [(W / "rooms/parents/all/images", 338, 653, 56)]),
    "kevin": (P2, [355, 376], [(W / "rooms/kevin/all/images", 192, 352, 56)]),
    "hallbath": (P2, [451, 481], [(W / "rooms/hallbath/all/images", 26, 176, 56)]),
    "buzz": (P2, [540, 550, 556], [(W / "real-vggt-buzzall/images/shot_buzz", 1, 89, 45)]),
    "hall": (P2, [609, 615, 621], [(W / "rooms/hall/all/images", 262, 376, 58)]),
    "attic": (P2, [892, 910], [(W / "attic/images", 304, 640, 56)]),
    "stairs": (P1, [335, 345], [(W / "rooms/stairs/all/images", 116, 187, 56)]),
    "foyer1": (P1, [1067], [(W / "ground-fly/images", 1, 60, 56)]),       # one solve per foyer visit: the two visits
    "foyer2": (P1, [1187], [(W / "ground-fly/images", 470, 528, 56)]),    # 2 min apart did not register together
    "kitchen": (P1, [1079, 1088, 1100], [(W / "ground-fly/images", 53, 193, 56)]),
    "dining": (P1, [1121, 1127], [(W / "ground-fly/images", 193, 301, 56)]),
    "living": (P1, [1145, 1157, 1160, 1163, 1172], [(W / "ground-fly/images", 313, 473, 56)]),
}
CLIP_TIME = {"parents": 92, "kevin": 307, "hallbath": 445, "buzz": 540, "hall": 540, "attic": 775, "stairs": 305,
             "foyer1": 1060, "foyer2": 1060, "kitchen": 1060, "dining": 1060, "living": 1060}   # context frame k = start + (k-1)/4 s

# Room fits. walls = (axis0 lo, axis0 hi, axis1 lo, axis1 hi): (function name, search window in solve units) or None.
# size_m = Marina's metres across (axis0 pair, axis1 pair); None = no measurement on that axis.
ROOMS = {
    "parents_bedroom": dict(job="parents", frames="338-455,548-653", stills=[178, 247, 636],
                            walls=[("window wall", (-0.3, -0.15)), ("hall-door wall", (1.25, 1.45)),
                                   ("bath-door wall", (-0.5, -0.3)), ("front wall", (1.05, 1.2))],
                            size_m=(5.23, 5.23), size_src="measurements/rooms/parents.json polygon x 3.465 m/u (80 in hall door)"),
    "parents_bath": dict(job="parents", frames="458-544", stills=[217, 223],
                         walls=[("far end wall", (0.25, 0.4)), ("near end wall", (1.2, 1.3)),
                                ("tub wall", (0.45, 0.55)), ("bedroom-door wall", (1.2, 1.3))],
                         size_m=(3.26, 2.63), size_src="measurements/rooms/parents.json bath polygon x 3.465 m/u"),
    "kevin_jeff_room": dict(job="kevin", frames=None, stills=[355, 376],
                            walls=[("hall-door wall", (-0.25, -0.05)), ("front-window wall", (1.3, 1.5)),
                                   ("closet-door wall", (-0.1, 0.05)), ("windows'-corner wall", (1.15, 1.3))],
                            size_m=(4.575, 3.60), size_src="measurements/rooms/kevin.json polygon x 2.914 m/u (80 in doors)"),
    "hall_bath": dict(job="hallbath", frames=None, stills=[451, 481],
                      walls=[("hall-door wall", (-0.35, -0.2)), ("window wall", (1.15, 1.3)),
                             ("Kevin-side wall", (-0.45, -0.3)), ("Buzz-side wall", (0.95, 1.1))],
                      size_m=(3.16, 3.33), size_src="spec/house_spec.measured.json hall_bath (overhead trace; no door scale)"),
    "buzz_room": dict(job="buzz", frames=None, stills=[540, 550, 556],
                      walls=[("front-window wall", (-0.8, -0.65)), ("shelves wall", (0.9, 1.0)),
                             ("door wall", (-1.3, -1.15)), ("desk wall", (0.85, 0.95))],
                      size_m=(3.49, 4.35), size_src="measurements/rooms/buzz.json (80 in door)"),
    "hall_corridor": dict(job="hall", frames=None, stills=[609, 615, 621],
                          walls=[None, ("parents'-door end wall", (1.05, 1.2)),
                                 ("Kevin-side wall", (-0.12, -0.02)), ("stair-side wall", (0.15, 0.25))],
                          size_m=(None, 1.22), size_src="measurements/rooms/hall.json far-end passage 1.22 m (hall-s4, 80 in door)"),
    "attic": dict(job="attic", frames=None, stills=[892, 910],
                  walls=[("front eave wall", (-0.8, -0.65)), ("rear eave wall", (0.65, 0.8)),
                         ("east gable wall", (-1.15, -1.0)), ("stair-end gable wall", (1.3, 1.42))],
                  size_m=(5.14, 8.61), size_src="Marina's 476 ft2 attic label split by the clip's 1.464:2.453 aspect (no door in the attic); eave/gable assignment unverified"),
    "kitchen": dict(job="kitchen", frames=None, stills=[1079, 1088, 1100],
                    walls=[("dining-door wall", (-0.1, 0.12)), ("rear wall", (0.95, 1.05)),
                           ("foyer-side wall", (-0.1, 0.12)), ("far side wall", (1.02, 1.12))],
                    size_m=(9.31, 7.90), size_src="spec/house_spec.ground.json kitchen extents (overhead trace; the built kitchen is 590 ft2 vs Marina's 477)"),
    "dining_room": dict(job="dining", frames=None, stills=[1121, 1127],
                        walls=[("sunroom-arch wall", (-0.06, 0.06)), ("foyer-arch wall", (0.62, 0.72)),
                               ("kitchen-door wall", (0.75, 0.85)), ("French-door wall", (1.35, 1.45))],
                        size_m=(4.62, None), size_src="spec/house_spec.ground.json dining width 4.62 (overhead trace); depth not used: the clip reads ~4.1 m kitchen door to French doors vs 5.87 built"),
    "living_room": dict(job="living", frames="313-380,429-473", stills=[1145, 1172],
                        walls=[("front-window wall", (-0.2, -0.05)), ("rear wall", (0.7, 0.8)),
                               ("foyer-door wall", (0.5, 0.65)), ("den-arch wall", (0.93, 1.05))],
                        size_m=(8.37, 4.50), size_src="spec/house_spec.ground.json living room (overhead trace)"),
    "den": dict(job="living", frames="383-426", stills=[1157, 1160, 1163],
                walls=[("front-window wall", (-0.15, 0.05)), ("bookshelf wall", (0.7, 0.8)),
                       ("living-arch wall", (0.93, 1.05)), ("far end wall", (1.35, 1.45))],
                size_m=(6.91, 3.71), size_src="spec/house_spec.ground.json den (overhead trace; den clip registration)"),
}

# Each model's walls by function, Unity world coordinates of that scene (sept: native units, 0.774 m/unit;
# latest: metres, world z = -spec z). A pair's two names must be the room's opposite walls.
M_SEPT = 0.774
MODEL_WALLS = {
    "sept": {"scene": "IntactHouseReference", "unit": M_SEPT, "rooms": {
        "parents_bedroom": dict(floor=5.22, **{"window wall": ("x", 14.80), "hall-door wall": ("x", 8.91), "bath-door wall": ("z", 7.29), "front wall": ("z", -1.0)}),
        "parents_bath": dict(floor=5.22, **{"far end wall": ("x", 12.50), "near end wall": ("x", 9.30), "tub wall": ("z", 10.77), "bedroom-door wall": ("z", 7.46)}),
        "kevin_jeff_room": dict(floor=5.22, **{"hall-door wall": ("z", 2.01), "front-window wall": ("z", -2.30), "closet-door wall": ("x", 5.0), "windows'-corner wall": ("x", 9.86)}),
        "hall_bath": dict(floor=5.22, **{"hall-door wall": ("z", -0.04), "window wall": ("z", -2.30), "Kevin-side wall": ("x", 4.35), "Buzz-side wall": ("x", -1.0)}),
        "buzz_room": dict(floor=5.22, **{"front-window wall": ("z", -2.30), "shelves wall": ("z", 1.87), "door wall": ("x", -1.16), "desk wall": ("x", -6.09)}),
        "hall_corridor": dict(floor=5.22, **{"parents'-door end wall": ("x", 8.91), "attic-door end wall": ("x", -3.21), "Kevin-side wall": ("z", 2.10), "stair-side wall": ("z", 4.50)}),
        "attic": dict(floor=8.55, **{"front eave wall": ("z", -2.1), "rear eave wall": ("z", 9.8), "east gable wall": ("x", 5.3), "stair-end gable wall": ("x", -10.5)}),
        "kitchen": dict(floor=1.31, **{"dining-door wall": ("z", 7.46), "rear wall": ("z", 15.3), "foyer-side wall": ("x", 4.9), "far side wall": ("x", 15.6)}),
        "dining_room": dict(floor=1.31, **{"sunroom-arch wall": ("x", 9.86), "foyer-arch wall": ("x", 4.73), "kitchen-door wall": ("z", 7.29), "French-door wall": ("z", -2.4)}),
        "living_room": dict(floor=1.31, **{"front-window wall": ("z", -2.4), "rear wall": ("z", 10.77), "foyer-door wall": ("x", -1.16), "den-arch wall": ("x", -6.09)}),
        "den": dict(floor=1.31, **{"front-window wall": ("z", -1.0), "bookshelf wall": ("z", 7.98), "living-arch wall": ("x", -6.28), "far end wall": ("x", -11.03)}),
    }},
    "latest": {"scene": "Greybox_Upstairs", "unit": 1.0, "rooms": {
        "parents_bedroom": dict(floor=0.0, **{"window wall": ("z", 0.0), "hall-door wall": ("z", -5.331), "bath-door wall": ("x", 3.21), "front wall": ("x", 8.491)}),
        "parents_bath": dict(floor=0.0, **{"far end wall": ("z", -0.872), "near end wall": ("z", -4.436), "tub wall": ("x", 0.343), "bedroom-door wall": ("x", 3.07)}),
        "kevin_jeff_room": dict(floor=0.0, **{"hall-door wall": ("x", 7.06), "front-window wall": ("x", 11.66), "closet-door wall": ("z", -7.74), "windows'-corner wall": ("z", -3.86)}),
        "hall_bath": dict(floor=0.0, **{"hall-door wall": ("x", 8.41), "window wall": ("x", 11.66), "Kevin-side wall": ("z", -7.88), "Buzz-side wall": ("z", -11.40)}),
        "buzz_room": dict(floor=0.0, **{"front-window wall": ("x", 11.16), "shelves wall": ("x", 7.47), "door wall": ("z", -11.54), "desk wall": ("z", -16.0)}),
        "hall_corridor": dict(floor=0.0, **{"parents'-door end wall": ("z", -5.47), "attic-door end wall": ("z", -13.59), "Kevin-side wall": ("x", 7.233), "stair-side wall": ("x", 5.634)}),
        "kitchen": dict(floor=-2.535, **{"dining-door wall": ("x", 4.12), "rear wall": ("x", -5.192), "foyer-side wall": ("z", -7.622), "far side wall": ("z", 0.28)}),
        "dining_room": dict(floor=-2.535, **{"sunroom-arch wall": ("z", -3.004), "foyer-arch wall": ("z", -7.622), "kitchen-door wall": ("x", 4.26), "French-door wall": ("x", 10.13)}),
        "living_room": dict(floor=-2.535, **{"front-window wall": ("x", 9.954), "rear wall": ("x", 1.583), "foyer-door wall": ("z", -11.569), "den-arch wall": ("z", -16.07)}),
        "den": dict(floor=-2.535, **{"front-window wall": ("x", 9.266), "bookshelf wall": ("x", 2.355), "living-arch wall": ("z", -16.21), "far end wall": ("z", -19.917)}),
    }},
}
PAIRS = {}   # room -> [(lo name, hi name), (lo name, hi name)] from ROOMS


# ---------------------------------------------------------------- solve
def solve(job):
    video, stills, ctx = JOBS[job]
    d = STILLS / job / "images/shot00"; shutil.rmtree(STILLS / job, ignore_errors=True); d.mkdir(parents=True)
    for folder, a, b, k in ctx:
        have = sorted(p for p in folder.glob("f_*.jpg") if a <= int(p.stem[2:]) <= b)
        for p in [have[i] for i in np.linspace(0, len(have) - 1, min(k, len(have))).round().astype(int)]:
            shutil.copy(p, d / f"c_{int(p.stem[2:]):05d}.jpg")
    for t in stills:   # the still itself, straight from the video at that second
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", str(video), "-frames:v", "1", "-q:v", "2",
                        str(d / f"s_{t:04d}.jpg")], check=True)
    subprocess.run([W / ".venv/bin/python", ROOT / "tools/sfm/vggt_solve.py", STILLS / job, "64"], check=True)


# ---------------------------------------------------------------- geometry
def load(job):
    from synthetic_score_lib import quat_to_R
    j = STILLS / job
    d = np.load(j / "sparse/0/pixels.npz"); names = [str(n) for n in d["names"]]
    cams = {int(l.split()[0]): float(l.split()[4]) for l in (j / "sparse/0/txt/cameras.txt").read_text().splitlines() if l.strip()}
    poses = {}
    for l in (j / "sparse/0/txt/images.txt").read_text().splitlines():
        if not l.strip():
            continue
        f = l.split(); poses[Path(f[-1]).name] = (quat_to_R(*map(float, f[1:5])), np.array(list(map(float, f[5:8]))), cams[int(f[8])])
    return d, names, poses


def pnp(d, i, R0, t0, focal):
    """Re-solve the frame's pose from its own point map (VGGT's camera head and point head are separate predictions)."""
    import cv2
    Hh, Ww = d["world"].shape[1:3]
    ys, xs = np.mgrid[2:Hh - 2:2, 2:Ww - 2:2]
    conf = d["conf"][i][ys, xs]; keep = conf >= np.percentile(conf, 50)
    obj = d["world"][i][ys, xs][keep].astype(np.float64); img = np.c_[xs[keep], ys[keep]].astype(np.float64) + 0.5
    fk = focal * Ww / 1920; K = np.array([[fk, 0, Ww / 2], [0, fk, Hh / 2], [0, 0, 1]])
    rvec0, _ = cv2.Rodrigues(R0)
    ok, rvec, tvec, inl = cv2.solvePnPRansac(obj, img, K, None, rvec0, t0.reshape(3, 1), useExtrinsicGuess=True,
                                             reprojectionError=2.0, iterationsCount=300)
    R, t = cv2.Rodrigues(rvec)[0], tvec.ravel()
    proj, _ = cv2.projectPoints(obj[inl.ravel()], rvec, tvec, K, None)
    rms = float(np.sqrt(((proj.reshape(-1, 2) - img[inl.ravel()]) ** 2).sum(1).mean()))
    return R, -R.T @ t, dict(rms_px_518=round(rms, 2), rms_px_1920=round(rms * 1920 / Ww, 1), inliers=int(len(inl)), points=int(len(obj)),
                             shift_from_camera_head_u=round(float(np.linalg.norm(-R.T @ t + R0.T @ t0)), 4))


def planes(pts, up):
    """Floor and ceiling: lowest / highest dense horizontal band (>= 15% of the fullest bin)."""
    h = pts @ up; hist, edges = np.histogram(h, bins=300); hist = np.convolve(hist, np.ones(3) / 3, mode="same")
    ok = np.where(hist >= 0.15 * hist.max())[0]; ck = (edges[:-1] + edges[1:]) / 2
    return float(ck[ok[0]]), float(ck[ok[-1]]), h


def manhattan(points, up):
    """Horizontal Manhattan frame (right-handed with up): sharpest wall histograms (room_dims.py method)."""
    h = points @ up; lo, hi = np.percentile(h, [15, 85]); p = points[(h > lo) & (h < hi)]
    a = np.cross(up, [1, 0, 0]); a /= np.linalg.norm(a); b = np.cross(up, a)
    P = np.c_[p @ a, p @ b]
    best = None
    for th in np.radians(np.arange(0, 90, 0.25)):
        R = np.array([[np.cos(th), -np.sin(th)], [np.sin(th), np.cos(th)]]); Q = P @ R.T
        score = sum(((np.histogram(Q[:, k], bins=300)[0] / len(Q)) ** 2).sum() for k in (0, 1))
        if best is None or score > best[0]:
            best = (score, R)
    R = best[1]
    e0 = R[0, 0] * a + R[0, 1] * b; e1 = R[1, 0] * a + R[1, 1] * b
    if np.linalg.det(np.c_[e0, e1, up]) < 0:
        e1 = -e1
    return e0, e1, Q


def wall_peak(q, window):
    """Densest 1-cm-ish bin of the slab points inside the window (solve units)."""
    sel = q[(q > window[0]) & (q < window[1])]
    if len(sel) < 50:
        return None
    hist, edges = np.histogram(sel, bins=max(int((window[1] - window[0]) / 0.004), 10))
    hist = np.convolve(hist, np.ones(3) / 3, mode="same"); i = int(np.argmax(hist))
    return float((edges[i] + edges[i + 1]) / 2)


def frame_filter(spec):
    rr = [tuple(map(int, r.split("-"))) for r in spec.split(",")] if spec else None
    return lambda n: n.startswith("s_") or rr is None or any(a <= int(n[2:7]) <= b for a, b in rr)


def fit_room(room, plot=None):
    cfg = ROOMS[room]; d, names, poses = load(cfg["job"])
    want = {f"s_{t:04d}.jpg" for t in cfg["stills"]}
    sel = [i for i, n in enumerate(names) if (n in want) or (not n.startswith("s_") and frame_filter(cfg["frames"])(n))]
    ups = np.array([-poses[names[i]][0].T @ [0, 1, 0] for i in sel]); up0 = ups.mean(0); up0 /= np.linalg.norm(up0)
    wp = d["world"][sel].reshape(-1, 3); cf = d["conf"][sel].reshape(-1); wp = wp[cf > np.median(cf)]
    pts = wp[np.random.default_rng(0).choice(len(wp), min(300_000, len(wp)), replace=False)].astype(np.float64)
    floor0, _, h = planes(pts, up0); fl = pts[np.abs(h - floor0) < 0.02 * np.ptp(h)]
    _, v = np.linalg.eigh(np.cov((fl - fl.mean(0)).T)); up = v[:, 0]; up *= np.sign(up @ up0)   # floor-plane normal
    floor, ceil, _ = planes(pts, up)
    e0, e1, Q = manhattan(pts, up)
    centres = np.array([-poses[names[i]][0].T @ poses[names[i]][1] for i in sel])
    hh = pts @ up; lo, hi = np.percentile(hh, [15, 85]); slab = pts[(hh > lo) & (hh < hi)]
    Q = np.c_[slab @ e0, slab @ e1]; CQ = np.c_[centres @ e0, centres @ e1]
    walls = [None if w is None else wall_peak(Q[:, k // 2], w[1]) for k, w in enumerate(cfg["walls"])]
    scales = []
    for k in (0, 1):
        if cfg["size_m"][k] and walls[2 * k] is not None and walls[2 * k + 1] is not None:
            scales.append(cfg["size_m"][k] / (walls[2 * k + 1] - walls[2 * k]))
    scale = float(np.mean(scales))
    res = dict(room=room, job=cfg["job"], frames_in_fit=len(sel), gravity_tilt_deg=round(float(np.degrees(np.arccos(np.clip(up @ up0, -1, 1)))), 2),
               walls_u=[None if w is None else round(w, 4) for w in walls], m_per_unit=round(scale, 4),
               scale_axes=[round(s, 4) for s in scales], scale_spread_pct=round(100 * (max(scales) - min(scales)) / scale, 1) if len(scales) > 1 else None,
               size_src=cfg["size_src"], ceiling_m=round((ceil - floor) * scale, 2), stills={})
    idx = {n: i for i, n in enumerate(names)}
    for t in cfg["stills"]:
        n = f"s_{t:04d}.jpg"; R0, t0, focal = poses[n]
        R, C, q = pnp(d, idx[n], R0, t0, focal)
        fwd = R.T @ [0, 0, 1]; upc = -R.T @ [0, 1, 0]
        p = np.array([C @ e0, C @ e1]); f2 = [float(fwd @ e0), float(fwd @ e1), float(fwd @ up)]
        right = np.cross(up, fwd); right /= np.linalg.norm(right)
        dist = [None if walls[k] is None else round(float((p[k // 2] - walls[k]) * scale * (1 if k % 2 == 0 else -1)), 3) for k in range(4)]
        res["stills"][t] = dict(p_u=[round(float(x), 4) for x in p], dist_m={cfg["walls"][k][0]: dist[k] for k in range(4) if cfg["walls"][k]},
                                eye_m=round(float((C @ up - floor) * scale), 3), forward=f2,
                                pitch_deg=round(float(np.degrees(np.arcsin(np.clip(fwd @ up, -1, 1)))), 1),
                                roll_deg=round(float(np.degrees(np.arcsin(np.clip(upc @ right, -1, 1)))), 1),
                                vfov_deg=round(float(2 * np.degrees(np.arctan(540 / focal))), 2), pnp=q)
    if plot:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(9, 9))
        ax.hexbin(Q[:, 0], Q[:, 1], gridsize=200, bins="log", cmap="Greys", mincnt=1); ax.plot(CQ[:, 0], CQ[:, 1], "b.", ms=4)
        for k, w in enumerate(walls):
            if w is not None:
                (ax.axvline if k < 2 else ax.axhline)(w, color="r", lw=1); ax.text(*((w, Q[:, 1].max()) if k < 2 else (Q[:, 0].min(), w)), cfg["walls"][k][0], color="r", fontsize=8)
        for t, st in res["stills"].items():
            p, f = st["p_u"], st["forward"]; ax.plot(*p, "go", ms=7); ax.arrow(p[0], p[1], f[0] * 0.25, f[1] * 0.25, color="g", width=0.01); ax.text(p[0], p[1], str(t), color="g")
        ax.set_aspect("equal"); ax.grid(True, lw=0.3); ax.set_title(f"{room}: {res['m_per_unit']} m/u, ceiling {res['ceiling_m']} m")
        fig.savefig(plot, dpi=80, bbox_inches="tight")
    return res


# ---------------------------------------------------------------- models
def place(res, model):
    """Pose in one model: pinned at the nearest wall of each pair, forward from the wall-normal components."""
    cfg = ROOMS[res["room"]]; mw = MODEL_WALLS[model]["rooms"].get(res["room"]); unit = MODEL_WALLS[model]["unit"]
    if mw is None:
        return None
    out = {}
    for t, st in res["stills"].items():
        pos = {}; dirs = {}; pins = []
        for k in (0, 1):
            lo, hi = cfg["walls"][2 * k], cfg["walls"][2 * k + 1]
            cands = [(c, st["dist_m"][c[0]]) for c in (lo, hi) if c and st["dist_m"].get(c[0]) is not None]
            near = min(cands, key=lambda c: abs(c[1]))                      # nearest wall of the pair (may be behind the camera: negative)
            other = hi if near[0] is lo else lo
            ax, c = mw[near[0][0]]
            ax_o, c_o = mw[other[0]] if other and other[0] in mw else (ax, None)
            inward = np.sign(c_o - c) if c_o is not None else (1 if near[0] is lo else -1)
            pos[ax] = c + inward * near[1] / unit
            sign_pair = inward if near[0] is lo else -inward                 # model direction of the fit's +axis k
            dirs[k] = (ax, sign_pair); pins.append(near[0][0])
        ay = {"x": 0, "z": 2}
        p = np.zeros(3); p[1] = mw["floor"] + st["eye_m"] / unit
        for ax, v in pos.items():
            p[ay[ax]] = v
        f = np.zeros(3); f[1] = st["forward"][2]
        for k in (0, 1):
            ax, s = dirs[k]; f[ay[ax]] += s * st["forward"][k]
        out[t] = dict(pos=[round(float(x), 3) for x in p], look_at=[round(float(x), 3) for x in (p + f)], vfov=st["vfov_deg"], pin=" / ".join(pins))
    return out


# ---------------------------------------------------------------- stairs (flight frame: riser lines, flight direction)
STAIR_STILLS = [("stairs", 335), ("stairs", 345), ("foyer1", 1067), ("foyer2", 1187)]   # all look at the main stair


def stair_still(job, t, RISE=0.169, GOING=0.241):
    """One still in the flight frame, from its OWN point map only (a straight stair walk drifts in scale, so nothing
    global is used): up and flight direction from the carpet normals (tools/sfm/stair_measure.py method), the rise and
    going visible in the map give the vertical and along-flight metres (measurements/rooms/stairs.json), position =
    height above the foyer floor (lowest tread level), distance before the first riser line seen, across from the
    flight centreline (left positive)."""
    from stair_measure import normals, peaks
    d, names, poses = load(job); i = names.index(f"s_{t:04d}.jpg")
    world, conf, images = d["world"][i:i + 1], d["conf"][i], d["images"][i]
    rgb = images.astype(np.float32); r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    carpet = (r > g * 1.6) & (r > b * 1.4) & (r > 40) & (conf >= np.percentile(conf, 30))
    N = normals(world)[0]; m = carpet & (np.linalg.norm(N, axis=-1) > 0.5); P, Nc = world[0][m], N[m]
    R0, t0, focal = poses[names[i]]; R, C, q = pnp(d, i, R0, t0, focal)
    if m.sum() < 2000:
        return dict(unposed=f"only {int(m.sum())} carpet pixels in the still's point map", pnp=q, vfov_deg=round(float(2 * np.degrees(np.arctan(540 / focal))), 2))
    up = -R.T @ [0, 1, 0]
    for cone in (35, 25, 20, 20, 20):
        sdot = Nc @ up; sel = np.abs(sdot) > np.cos(np.radians(cone)); fam = Nc[sel] * np.sign(sdot[sel])[:, None]
        up = fam.mean(0); up /= np.linalg.norm(up)
    hn = Nc - np.outer(Nc @ up, up); horiz = np.abs(Nc @ up) < np.sin(np.radians(20))
    hv = hn[horiz]; hv /= np.linalg.norm(hv, axis=1, keepdims=True)
    _, evec = np.linalg.eigh(hv.T @ hv); f = evec[:, -1]; f -= (f @ up) * up; f /= np.linalg.norm(f)
    tread = np.abs(Nc @ up) > np.cos(np.radians(15))
    if np.corrcoef((P @ f)[tread], (P @ up)[tread])[0, 1] < 0:
        f = -f
    side = np.cross(up, f)          # left when facing up the flight (right-handed frame)
    riser = horiz & (np.abs(Nc @ f) > np.cos(np.radians(25)))
    h, sv_ = P @ up, P @ f

    def steps(v, bw, frac):
        pk = np.array(sorted(p[0] for p in peaks(v, bw, frac)))
        keep = [pk[0]]
        for x in pk[1:]:
            if x - keep[-1] > 0.5 * np.median(np.diff(pk)):
                keep.append(x)
        return np.array(keep)
    levels = steps(h[tread], np.ptp(h[tread]) / 300, 0.15); rises = np.diff(levels)
    rise = float(np.median(rises[rises < 2 * np.min(rises)]))
    nos = steps(sv_[riser], rise / 20, 0.10); goings = np.diff(nos); going = float(np.median(goings[goings < 2 * np.min(goings)]))
    sv, sa = RISE / rise, GOING / going
    centre = float(np.median(P[tread] @ side))
    fwd = R.T @ [0, 0, 1]; upc = -R.T @ [0, 1, 0]; right = np.cross(up, fwd); right /= np.linalg.norm(right)
    return dict(ref="foyer floor / first riser / flight centreline", forward=[float(fwd @ f), float(fwd @ side), float(fwd @ up)],
                levels_seen=int(len(levels)), risers_seen=int(len(nos)), m_per_unit_vertical=round(sv, 3), m_per_unit_along=round(sa, 3),
                height_m=round(float((C @ up - levels[0]) * sv), 3), along_m=round(float((C @ f - nos[0]) * sa), 3),
                across_left_m=round(float((C @ side - centre) * sv), 3),
                pitch_deg=round(float(np.degrees(np.arcsin(np.clip(fwd @ up, -1, 1)))), 1),
                roll_deg=round(float(np.degrees(np.arcsin(np.clip(upc @ right, -1, 1)))), 1),
                vfov_deg=round(float(2 * np.degrees(np.arctan(540 / focal))), 2), pnp=q)


def stairs():
    res = dict(room="main_stair", job="stairs", method="per-still local rise/going scale from the still's own point map", stills={})
    for job, t in STAIR_STILLS:
        if not (STILLS / job / "sparse/0/pixels.npz").exists():
            continue
        st = stair_still(job, t); st["job"] = job
        if "unposed" in st:
            res["stills"][t] = st; continue
        if t == 345:   # on the flight: VGGT's depth along the straight climb is not trusted; the frame shows 6 risers ahead
            # of the camera to the landing nosing, so she stands on tread 7 (13 risers to the landing). Height = 7 rises +
            # her eye height at 335; along = 7 goings + half a tread.
            st.update(height_m=round(7 * 0.169 + res["stills"][335]["height_m"], 3), along_m=round(7 * 0.241 + 0.12, 3),
                      note="along/height from the riser count in the frame (6 ahead) and the 335 eye height; local VGGT read was inconsistent")
        res["stills"][t] = st
    return res


# flight frame in each model: first riser foot on the flight centreline and the top nosing / landing level (13 risers);
# along = up the flight, left = across to the left when facing up. Grey-box: measurements/rooms/stairs.json as built;
# Sept: sheet_views.py (first riser z 4.15, centreline x 0.115, landing z 9.42 at y 4.45).
STAIR_MODEL = {"sept": dict(first=(0.115, 1.31, 4.15), top=(0.115, 4.45, 9.42), along=(0, 0, 1), left=(-1, 0, 0)),
               "latest": dict(first=(4.472, -2.535, -10.801), top=(4.472 - 13 * 0.241, -2.535 + 13 * 0.169, -10.801), along=(-1, 0, 0), left=(0, 0, -1))}


def place_stairs(res, model):
    m = STAIR_MODEL[model]; unit = MODEL_WALLS[model]["unit"]; al, lf = np.array(m["along"]), np.array(m["left"])
    out = {}
    for t, st in res["stills"].items():
        if "unposed" in st:
            continue
        o = np.array(m["first"], float)
        p = o + al * st["along_m"] / unit + lf * st["across_left_m"] / unit + np.array([0, st["height_m"] / unit, 0])
        f = al * st["forward"][0] + lf * st["forward"][1] + np.array([0, st["forward"][2], 0])
        out[t] = dict(pos=[round(float(x), 3) for x in p], look_at=[round(float(x), 3) for x in (p + f)], vfov=st["vfov_deg"], pin=st["ref"])
    return out


# Findings from looking at the triples (Oct 14). "outside" = Marina's camera falls outside that model's room.
NOTES = {
    "p2-178": "clean match (scale spread 0.6%, ceiling 2.49 m vs 2.42-2.50 measured)",
    "p2-247": "clean match; windows on the right in all three",
    "p2-636": "camera stands 0.30 m into the hall doorway: inside the Sept door wall (white render), in the grey-box it sees the room through the door",
    "p2-217": "bath shape disagrees with the old polygon by 9% (L-shaped bath, no door scale); Sept bath is L-shaped the other way: camera lands in its tub alcove",
    "p2-223": "as 217; grey-box bath is a bare box",
    "p2-355": "clean match (scale spread 0.5%, ceiling 2.31 m vs 2.30-2.33 measured); camera 5 cm off the closet wall = in the doorway corner",
    "p2-376": "clean match",
    "p2-451": "hall bath: clip vs spec shape differ 10% (hall_bath +10% from wall thinning); Sept bath is smaller, camera almost on its tiled wall; grey-box render is white: camera 0.1 m inside the notch/closet_1 wall",
    "p2-481": "as 451; grey-box fine",
    "p2-540": "regression vs views-buzz-old.json: door wall 2.55 vs 2.50 m, shelves wall 1.98 vs 1.92 m, eye 1.29 vs 1.30 m",
    "p2-550": "regression: 1.61/0.85 m vs 1.55/0.86 m",
    "p2-556": "regression: 3.29/0.75 m vs 3.25/0.69 m",
    "p2-609": "hall: scale from the far-end passage width (1.22 m); eye 1.14 m agrees with hall-s1 (1.03-1.19, attic-door scale), an independent check. Sept hall is 1.86 m wide vs Marina's 1.22-1.58, so the far walls differ",
    "p2-615": "as 609",
    "p2-621": "this is the hall end with girls' room A's door on the left and the parents' door on the right (the caption says Girl's Room); camera is in the hall, not in girls' room B. girls_room_a does not exist in Sept (back-stair hall there)",
    "p2-892": "attic (Sept only): scale from Marina's 476 ft2 label, eave/gable assignment unverified; eye 2.0 m (camera high); Sept attic layout differs (stair at the west end, not the middle)",
    "p2-910": "as 892",
    "p1-335": "stair frame from the still's own treads and risers (rise 0.169 / going 0.241 m); clean match in both models",
    "p1-345": "on the flight: along/height from the riser count (6 ahead) + the 335 eye height, not from VGGT depth (straight climb drifts); both renders are a touch close/low",
    "p1-1067": "UNRELIABLE: the foyer solve is poor (15% PnP inliers); puts the camera 4.7 m behind the first riser = inside the rear foyer wall in both models (white renders). Needs a solve of a proper foyer pan (stairs-a 312-320 s has one, but not this frame)",
    "p1-1187": "UNRELIABLE: 1.8 m before the first riser is plausible but 1.08 m left of the flight centreline puts the camera in the stair wall (35% inliers); grey render white, Sept shows the stair from inside the wall",
    "p1-1079": "kitchen near walls (dining door / foyer side) not resolved by the fit: scale spread 30%; position +-1 m. Sept camera lands in the back-stair bay beside the kitchen",
    "p1-1088": "pinned at the rear / far-side corner; grey-box render black on the left: camera 1 m inside the grey kitchen's rear-wing wall (grey kitchen is 590 ft2, a different L than Marina's); Sept plausible (island, window)",
    "p1-1100": "pinned at the rear / far-side corner; Sept window + cabinets line up with Marina's sink window; grey-box shows a bare wall",
    "p1-1121": "camera is in the butler's pantry 1.3 m before the dining room's kitchen-door wall (outside the dining room in both models, as in the still)",
    "p1-1127": "dining scale from the room width only; the clip reads ~4.1 m kitchen door to French doors vs 5.87 m built: Marina's dining room is shallower than the grey-box's",
    "p1-1145": "camera in the foyer 0.9 m before the living-room doorway (as in the still); both renders look through the doorway",
    "p1-1172": "living room (scale spread 0.7%); camera at the den arch looking back at the fireplace wall",
    "p1-1157": "DEN, not living room: 0.7 m inside the den arch looking at the den's front windows (the fit puts it 0.73 m past the living-arch wall)",
    "p1-1160": "den; eye 0.77 m is suspicious (PnP shift 0.10 u): pose +-0.3 m",
    "p1-1163": "den bookshelf wall ahead in all three; den scale spread 18% (Marina's den reads longer than the spec's 3.71 m)",
}


# ---------------------------------------------------------------- outputs
def still_name(t):
    return f"p{1 if t in sum((JOBS[j][1] for j in JOBS if JOBS[j][0] == P1), []) else 2}-{t}"


def poses():
    OUT.mkdir(parents=True, exist_ok=True)
    rows, views = [], {"sept": [], "latest": []}
    fits = [fit_room(r, STILLS / ROOMS[r]["job"] / f"fit-{r}.png") for r in ROOMS] + [stairs()]
    for res in fits:
        placed = {m: (place_stairs(res, m) if res["room"] == "main_stair" else place(res, m)) for m in ("sept", "latest")}
        for t, st in res["stills"].items():
            name = still_name(t)
            row = dict(still=name, room=("foyer" if t in (1067, 1187) else res["room"]), job=st.get("job", res["job"]), second=t, frame_in_job=f"s_{t:04d}.jpg", clip_start_s=CLIP_TIME[st.get("job", res["job"])],
                       room_frame={k: v for k, v in st.items() if k != "pnp"}, reprojection=st["pnp"],
                       fit={k: res[k] for k in res if k not in ("stills", "room", "job")}, models={}, note=NOTES.get(name, ""))
            for m, pl in placed.items():
                if pl and t in pl:
                    row["models"][m] = pl[t]
                    views[m].append(dict(name=f"../sheet-matched/{name}-{m}", pos=pl[t]["pos"], look_at=pl[t]["look_at"], vfov=pl[t]["vfov"],
                                         note=f"Marina {name} ({res['room']}); pinned at {pl[t]['pin']}"))
            rows.append(row)
    (OUT / "poses.json").write_text(json.dumps(rows, indent=1) + "\n")
    for m, v in views.items():
        (ROOT / "spec/captures/views" / f"sheet-matched-{m}.json").write_text(json.dumps(v, indent=1) + "\n")
    for r in rows:
        print(r["still"], r["room"], {k: v for k, v in r["room_frame"].items() if k in ("dist_m", "eye_m", "along_m", "across_m", "height_m")},
              "rms", r["reprojection"]["rms_px_1920"], "px;", {m: p["pos"] for m, p in r["models"].items()})


def triples():
    from PIL import Image, ImageDraw
    rows = json.loads((OUT / "poses.json").read_text())
    for r in rows:
        tiles = []
        job = r["job"]; still = STILLS / job / "images/shot00" / r["frame_in_job"]
        for label, path in ((f"Marina {r['still']} ({r['room']})", still), ("September", OUT / f"{r['still']}-sept.png"), ("grey-box", OUT / f"{r['still']}-latest.png")):
            if path.exists():   # a fresh Unity PNG: shrink to 1280 wide and keep only the JPEG
                im = Image.open(path).convert("RGB").resize((1280, 720)); im.save(path.with_suffix(".jpg"), quality=85); path.unlink()
            elif path.with_suffix(".jpg").exists():
                im = Image.open(path.with_suffix(".jpg")).convert("RGB")
            else:
                im = Image.new("RGB", (1280, 720), (30, 30, 30)); label += " (not rendered)"
            ImageDraw.Draw(im).rectangle((0, 0, 420, 22), fill="black"); ImageDraw.Draw(im).text((6, 5), label, fill="yellow"); tiles.append(im)
        sheet = Image.new("RGB", (3 * 1280, 720))
        for k, t in enumerate(tiles):
            sheet.paste(t, (k * 1280, 0))
        sheet.save(OUT / f"{r['still']}-triple.jpg", quality=85)
    print(len(rows), "triples")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "solve":
        solve(sys.argv[2])
    elif cmd == "fit":
        res = fit_room(sys.argv[2], STILLS / ROOMS[sys.argv[2]]["job"] / f"fit-{sys.argv[2]}.png")
        print(json.dumps(res, indent=1, default=float))
    elif cmd == "stairs":
        print(json.dumps(stairs(), indent=1, default=float))
    elif cmd == "poses":
        poses()
    elif cmd == "triples":
        triples()
