"""joint_fit: the house as a parametric model, fitted together with every camera to labelled frames (model-based photogrammetry).

Why (Oct 15, method page https://claude.ai/artifact/XXuuXaREgFsR35eZ8QWYpR): one camera per frame solved from the build cannot
correct the build. Here the house parameters (wall lines, stair fields) and all cameras are unknowns of one robust least squares;
fixed anchors (already-established geometry) carry the plan frame and scale, and Marina's camera height (rig_check.py:
0.639 x 80 in) is a prior on her cameras. Marina and the film are fitted as SEPARATE parameter sets and compared, never averaged:
a disagreement beyond both error bars is a canon question for the user.

Pilot: the kitchen's back stair (reconcile.service_stair_spec). Coordinates as refcam.py: spec metres, h above the ground floor.
Cameras: yaw, pitch, position (x, h, z), focal; roll 0; principal point at the frame centre.

  joint_fit.py rehearse [--seed 0]     synthetic truth -> labels (noise, occlusion, one gross mislabel a frame) -> fit -> report:
                                       parameter recovery vs error bars, outlier caught, held-out frame, canon split, budget sweep
"""
import argparse
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares

sys.path.insert(0, str(Path(__file__).resolve().parent))
RIG_H, RIG_SD = 0.639 * 80 * 0.0254, 0.03     # Marina camera height prior (2.5% spread)
W, H = 1920, 1080

# ---------------------------------------------------------------- the model
# Free parameters, initialised from the build (spec metres; reconcile.service_stair_spec + the enclosure trace).
FREE = {"newel_x": 2.37,        # x1: the foot's newel side (the enclosure's doorway end)
        "open_z": 6.66,         # z0: the stair's open side toward the room
        "going": 0.262, "rise": 0.188,
        "door_x0": -1.43, "door_x1": -0.72, "door_head": 2.032,   # basement door leaf edges and head
        "door_z": 6.66,         # the basement door's wall plane (built in the open-side plane; Marina 916 shows it flush with the wall to the corner)
        "newel_h": 1.19, "post_h": 1.99,   # newel and tall-post top heights (authored in the build)
        "doorway_z": 7.638, "doorway_head": 2.20,   # the foyer doorway's plane and head: Marina 916 puts it ~9.5 m from the camera
        "ceiling": 2.438}                           # against ~5.8 m for the stair if it were 0.98 x 2.20 on the stair wall: fitted, not anchored
WALL_Z, END_X, NB = 7.638, -1.505, 4    # anchored: the foyer-side wall face, the kitchen's back-right corner, 4 foot steps

# Anchors: established geometry that fixes frame and scale (foyer doorway from the film-solved foyer; corner and window from the trace)
ANCHORS = {"window sill near": (END_X, 0.82, 4.99), "window sill far": (END_X, 0.82, 5.79),
           "window head near": (END_X, 2.15, 4.99), "window head far": (END_X, 2.15, 5.79)}


def features(p):
    """Every labelled point as a function of the parameters (dict name -> xyz with y = height above the floor)."""
    x1, z0, g, r = p["newel_x"], p["open_z"], p["going"], p["rise"]
    w = WALL_Z - z0; xl = x1 - w; F = dict(ANCHORS)
    F["newel foot"] = (x1 - 0.05, 0, z0 - NB * g + 0.05); F["newel top"] = (x1 - 0.05, p["newel_h"], z0 - NB * g + 0.05)
    F["post foot"] = (xl + 0.05, 0, z0 - 0.05); F["post top"] = (xl + 0.05, p["post_h"], z0 - 0.05)
    for k, x in (("L", 3.043), ("R", 4.025)):      # foyer doorway jambs (x from the film-solved foyer)
        F[f"doorway {k} foot"] = (x, 0, p["doorway_z"]); F[f"doorway {k} head"] = (x, p["doorway_head"], p["doorway_z"])
    for k in range(1, NB + 1):                     # the foot's nosings, both ends
        F[f"foot{k} nosing room end"] = (xl, k * r, z0 - (NB - k + 1) * g)
        F[f"foot{k} nosing newel end"] = (x1, k * r, z0 - (NB - k + 1) * g)
    for k in range(1, 13):                         # flight nosings on the open side (a fixed set, so the fit stays smooth;
        F[f"flight{k} nosing"] = (xl - (k - 1) * g, (NB + 1 + k) * r, z0)   # synth() keeps only those under the ceiling)
    F["flight meets ceiling"] = (xl - (p["ceiling"] / r - NB - 2) * g, p["ceiling"], z0)   # the nosing line at ceiling height
    F["ceiling corner"] = (END_X, p["ceiling"], WALL_Z)
    dz = p["door_z"]
    F["door L foot"] = (p["door_x0"], 0, dz); F["door R foot"] = (p["door_x1"], 0, dz)
    F["door L head"] = (p["door_x0"], p["door_head"], dz); F["door R head"] = (p["door_x1"], p["door_head"], dz)
    F["door-wall corner foot"] = (END_X, 0, dz); F["door-wall ceiling corner"] = (END_X, p["ceiling"], dz)
    return F


def rot(yaw, pitch):   # world (x, y up, z) -> camera (right, down, forward); yaw as refcam.R, pitch > 0 looks up
    c, s = np.cos(yaw), np.sin(yaw)
    Ry = np.array([[s, 0, -c], [0, -1, 0], [-c, 0, -s]])
    cp, sp = np.cos(pitch), np.sin(pitch)
    return np.array([[1, 0, 0], [0, cp, sp], [0, -sp, cp]]) @ Ry


def project(cam, X):
    yaw, pitch, x, h, z, f = cam
    Xc = (np.atleast_2d(X) - [x, h, z]) @ rot(yaw, pitch).T
    return np.c_[W / 2 + f * Xc[:, 0] / Xc[:, 2], H / 2 + f * Xc[:, 1] / Xc[:, 2]], Xc[:, 2]


# ---------------------------------------------------------------- the fit
def fit(labels, p0, cams0, rig_prior, fix_params=False):
    """labels: [{name: uv}] per frame. Robust (soft L1, 2 px) on pixels; Marina cameras get the height prior."""
    names = list(FREE); n = len(names)
    def unpack(q):
        p = dict(zip(names, q[:n])) if not fix_params else dict(p0)
        return p, q[(0 if fix_params else n):].reshape(-1, 6)

    def res(q):
        p, C = unpack(q); F = features(p); r = []
        for lab, c in zip(labels, C):
            keys = [k for k in lab if k in F]
            uv, _ = project(c, np.array([F[k] for k in keys])); r.append((uv - np.array([lab[k] for k in keys])).ravel())
            if rig_prior:
                r.append([(c[3] - RIG_H) / RIG_SD * 2.0])   # in 2 px units, so it weighs like one sigma-scaled label
        return np.concatenate(r)
    q0 = np.r_[[] if fix_params else [p0[k] for k in names], np.ravel(cams0)]
    s = least_squares(res, q0, loss="soft_l1", f_scale=2.0, x_scale="jac")
    p, C = unpack(s.x)
    # error bars from the robust Jacobian, scaled by the inlier residual spread
    J = s.jac; r = s.fun; inl = np.abs(r) < 6; sig = np.sqrt(np.mean(r[inl] ** 2)) if inl.any() else 1.0
    try:
        cov = np.linalg.pinv(J.T @ J) * sig ** 2
    except np.linalg.LinAlgError:
        cov = np.full((len(s.x), len(s.x)), np.nan)
    sd = {} if fix_params else dict(zip(names, np.sqrt(np.diag(cov)[:n])))
    # per-label residuals (px), to flag mislabels
    F = features(p); per = []
    for i, (lab, c) in enumerate(zip(labels, C)):
        for k, uv in lab.items():
            e = float(np.linalg.norm(project(c, np.array([F[k]]))[0][0] - uv)); per.append((i, k, e))
    return p, sd, C, per, sig


def jackknife_sd(labels, p, C, rig_prior):
    """Leave-one-frame-out spread of every parameter: catches a single frame (or a mislabel the robust loss kept) pulling the
    house, which the Jacobian error bar cannot see. Use max(Jacobian sd, this)."""
    n = len(labels); runs = []
    for i in range(n):
        keep = [j for j in range(n) if j != i]
        runs.append(fit([labels[j] for j in keep], p, C[keep], rig_prior)[0])
    return {k: float(np.sqrt((n - 1) / n * np.sum((np.array([r[k] for r in runs]) - np.mean([r[k] for r in runs])) ** 2))) for k in FREE}


# ---------------------------------------------------------------- rehearsal
def synth(p_true, cams, rng, noise, drop=0.3, outlier=30.0):
    F = {k: v for k, v in features(p_true).items() if not k.startswith("flight") or k == "flight meets ceiling" or v[1] <= p_true["ceiling"] - 0.05}
    labels = []; bad = []
    for i, c in enumerate(cams):
        keys = list(F); uv, z = project(c, np.array([F[k] for k in keys]))
        lab = {k: u + rng.normal(0, noise, 2) for k, u, d in zip(keys, uv, z)
               if d > 0.3 and 0 <= u[0] < W and 0 <= u[1] < H and rng.random() > drop}
        if lab:
            k = rng.choice(list(lab)); lab[k] = lab[k] + rng.choice([-1, 1], 2) * outlier; bad.append((i, k))
        labels.append(lab)
    return labels, bad


def views(rng, n, film):
    """Plausible cameras in the breakfast area looking at the back stair: Marina (f 1428, h 1.30, small pitch) or film (long lens, varied height)."""
    C = []
    for _ in range(n):
        x, z = rng.uniform(-0.5, 3.5), rng.uniform(0.5, 3.0)
        tx, tz = rng.uniform(-1.0, 2.5), 7.2
        yaw = np.arctan2(-(tz - z), -(tx - x))                 # refcam yaw convention: looks along (-cos, -sin)
        if film:
            C.append([yaw, np.radians(rng.uniform(-4, 6)), x, rng.uniform(0.8, 1.6), z, rng.uniform(1800, 2600)])
        else:
            C.append([yaw, np.radians(rng.uniform(-3, 4)), x, RIG_H + rng.normal(0, 0.01), z, 1428.0])
    return np.array(C)


def jitter(C, rng):
    C = C.copy(); C[:, 0] += np.radians(rng.normal(0, 6, len(C))); C[:, 1] += np.radians(rng.normal(0, 2, len(C)))
    C[:, [2, 4]] += rng.normal(0, 0.4, (len(C), 2)); C[:, 3] += rng.normal(0, 0.15, len(C)); C[:, 5] *= rng.uniform(0.9, 1.1, len(C))
    return C


def one(p_true, n, film, noise, rng, jack=False):
    C = views(rng, n + 1, film); labels, bad = synth(p_true, C, rng, noise)
    p, sd, Cf, per, sig = fit(labels[:n], dict(FREE), jitter(C[:n], rng), rig_prior=not film)
    if jack:
        js = jackknife_sd(labels[:n], p, Cf, not film); sd = {k: max(sd[k], js[k]) for k in FREE}
    err = {k: p[k] - p_true[k] for k in FREE}; z = {k: err[k] / sd[k] for k in FREE if sd[k] > 0}
    flagged = {(i, k) for i, k, e in per if e > 10}; caught = sum((i, k) in flagged for i, k in bad if i < n)
    # held-out frame: its camera alone, house fixed at the fit
    _, _, _, per_h, _ = fit([labels[n]], p, jitter(C[n:], rng), rig_prior=not film, fix_params=True)
    eh = np.array([e for _, _, e in per_h]); held = float(np.median(eh)) if len(eh) else np.nan
    return dict(err=err, sd=sd, z=z, caught=caught, bad=sum(i < n for i, _ in bad), false=len(flagged) - caught, held=held, p=p)


def cmd_rehearse(a):
    rng = np.random.default_rng(a.seed); ok = True
    truth = {k: v + (rng.normal(0, 0.25) if k not in ("going", "rise", "door_head", "ceiling", "doorway_head") else rng.normal(0, 0.015)) for k, v in FREE.items()}
    truth["door_x1"] = truth["door_x0"] + 0.711 + rng.normal(0, 0.05)
    print("1. Recovery, 6 Marina frames, 1.5 px labels, 30% occluded, one 30 px mislabel a frame (20 trials)")
    R = [one(truth, 6, False, 1.5, rng) for _ in range(20)]
    print(f"   {'param':10s} {'median |err| cm':>16s} {'median sd cm':>13s} {'|z| median':>10s}  (z = err/sd; calibrated if ~0.67)")
    zall = []
    for k in FREE:
        e = np.median([abs(r["err"][k]) for r in R]) * 100; s = np.median([r["sd"][k] for r in R]) * 100; zz = np.median([abs(r["z"][k]) for r in R])
        zall += [abs(r["z"][k]) for r in R]; print(f"   {k:10s} {e:16.1f} {s:13.1f} {zz:10.2f}")
    zm = float(np.median(zall)); cal = 0.4 < zm < 1.1; ok &= cal
    print(f"   error bars {'calibrated' if cal else 'NOT calibrated'}: median |z| {zm:.2f} (0.67 expected)")
    caught = sum(r["caught"] for r in R); bad = sum(r["bad"] for r in R); false = sum(r["false"] for r in R)
    good = caught >= 0.9 * bad and false <= len(R); ok &= good
    print(f"   mislabels flagged (>10 px): {caught}/{bad}; false flags {false}  {'ok' if good else 'FAIL'}")
    held = np.median([r["held"] for r in R]); good = held < 4; ok &= good
    print(f"   held-out frame, house fixed: median label residual {held:.1f} px  {'ok' if good else 'FAIL'}")

    print("2. Sensitivity: the held-out residual must rise when the house is wrong (newel 15 cm off)")
    C = views(rng, 1, False); labs, _ = synth(truth, C, rng, 1.5, outlier=0)
    base = fit(labs, truth, jitter(C, rng), True, fix_params=True)[3]; wrong = dict(truth, newel_x=truth["newel_x"] + 0.15)
    bad_ = fit(labs, wrong, jitter(C, rng), True, fix_params=True)[3]
    m0, m1 = np.median([e for *_, e in base]), np.max([e for *_, e in bad_]); good = m1 > 3 * max(m0, 1.5); ok &= good
    print(f"   true house: median {m0:.1f} px; newel +15 cm: worst label {m1:.1f} px  {'ok' if good else 'FAIL'}")

    print("3. Canon split: the film's newel 40 cm from Marina's, everything else equal; fitted separately, error bars = max(Jacobian,")
    print("   leave-one-frame-out); 5 trials, every one must flag the newel and nothing else")
    film_truth = dict(truth, newel_x=truth["newel_x"] + 0.40); wrong = 0
    for t in range(5):
        rm = one(truth, 6, False, 1.5, rng, jack=True); rf = one(film_truth, 6, True, 2.0, rng, jack=True); flags = []
        for k in FREE:
            d = rf["p"][k] - rm["p"][k]; s = np.hypot(rm["sd"][k], rf["sd"][k]); flags.append((k, d, s, abs(d) > 3 * s))
        got = [k for k, *_, f in flags if f]; wrong += got != ["newel_x"]
        print(f"   trial {t}: flagged {got}; newel film - Marina {100 * flags[0][1]:+.1f} cm (+-{100 * flags[0][2]:.1f}); "
              f"largest other |d|/s {max(abs(d) / s for k, d, s, _ in flags[1:]):.1f}")
    good = wrong == 0; ok &= good
    print(f"   only the newel flagged in every trial: {'ok' if good else 'FAIL'}")

    print("5. Model error: anchors (doorway, corner, window) each off by N(0, 5 cm) in the truth; the fit keeps the build's anchors")
    global ANCHORS
    keep = dict(ANCHORS); E = []
    for t in range(8):
        ANCHORS = {k: tuple(np.add(v, rng.normal(0, 0.05, 3) * [1, 0.4, 1])) for k, v in keep.items()}
        C = views(rng, 6, False); labels, _ = synth(truth, C, rng, 1.5)
        ANCHORS = keep
        p, sd, Cf, per, _ = fit(labels, dict(FREE), jitter(C, rng), True)
        E.append(max(abs(p[k] - truth[k]) for k in FREE)); worst = max(e for *_, e in per if e < 10)
    print(f"   worst parameter error median {100 * np.median(E):.1f} cm, max {100 * max(E):.1f} cm (5 cm anchor errors are damped: many anchors and frames share them out)")
    print("6. Off-by-one nosing: one frame labels flight nosing 3 where nosing 4 is (a 1-step slip, ~0.26 m along, one rise up)")
    C = views(rng, 6, False); labels, _ = synth(truth, C, rng, 1.5, outlier=0)
    i = next(j for j, l in enumerate(labels) if "flight3 nosing" in l and "flight4 nosing" in l)
    labels[i]["flight3 nosing"] = labels[i]["flight4 nosing"].copy()
    p, sd, Cf, per, _ = fit(labels, dict(FREE), jitter(C, rng), True)
    e = next(e for j, k, e in per if j == i and k == "flight3 nosing"); good = e > 10; ok &= good
    print(f"   slipped label residual {e:.1f} px, house error max {100 * max(abs(p[k] - truth[k]) for k in FREE):.1f} cm  {'flagged ok' if good else 'NOT flagged: FAIL'}")

    print("4. Budget: Marina frames x label noise -> worst parameter error (median of 8 trials, cm)")
    for noise in (1.0, 2.0, 3.0):
        row = []
        for n in (2, 3, 4, 6, 9):
            row.append(np.median([max(abs(v) for v in one(truth, n, False, noise, rng)["err"].values()) for _ in range(8)]) * 100)
        print(f"   {noise:.0f} px: " + "  ".join(f"{n} fr {e:5.1f}" for n, e in zip((2, 3, 4, 6, 9), row)))
    print("REHEARSAL", "PASS" if ok else "FAIL")
    raise SystemExit(0 if ok else 1)


# ---------------------------------------------------------------- labelling
def frame_path(name):
    from pathlib import Path
    root = Path(__file__).resolve().parents[2]
    if name.startswith("film-"):
        return root / f"0-homealone/full/homealone-movie-screencaps.com-{name[5:]}.jpg"
    return root / f"sfm-work/refcam/frames/{name}.jpg"


def frame_segments(name):
    """Detected line segments of a frame (Canny + probabilistic Hough, as rig_check.py), deterministic, numbered."""
    import rig_check
    S = rig_check.segments(frame_path(name), min_len=25)
    return S[np.argsort(-np.hypot(S[:, 2] - S[:, 0], S[:, 3] - S[:, 1]), kind="stable")]


def cmd_segs(a):
    """Numbered segments over a crop (2x), to pick features by segment id instead of reading pixels by eye."""
    from pathlib import Path
    from PIL import Image, ImageDraw
    x0, y0, x1, y1 = a.roi; S = frame_segments(a.frame); k = 2
    im = Image.open(frame_path(a.frame)).convert("RGB").crop((x0, y0, x1, y1)); im = im.resize((im.width * k, im.height * k)); d = ImageDraw.Draw(im)
    for i, s in enumerate(S):
        if not (x0 <= (s[0] + s[2]) / 2 <= x1 and y0 <= (s[1] + s[3]) / 2 <= y1):
            continue
        col = [(255, 40, 40), (40, 220, 40), (40, 120, 255), (255, 160, 0), (220, 40, 220)][i % 5]
        d.line([((s[0] - x0) * k, (s[1] - y0) * k), ((s[2] - x0) * k, (s[3] - y0) * k)], fill=col, width=2)
        d.text((((s[0] + s[2]) / 2 - x0) * k + 3, ((s[1] + s[3]) / 2 - y0) * k - 12), str(i), fill=col)
    out = Path(__file__).resolve().parents[2] / f"sfm-work/joint/{a.frame}-segs-{x0}-{y0}.png"; out.parent.mkdir(parents=True, exist_ok=True); im.save(out); print(out)


def label_uv(frame, spec, S):
    """A label: [u, v] (by eye), {"x": [i, j]} (intersection of segments i and j), or {"on": i, "near": [u, v]} (foot of the
    perpendicular from an eye point onto segment i: an endpoint read along a clean edge)."""
    import rig_check
    if isinstance(spec, list):
        return np.array(spec, float)
    if "x" in spec:
        i, j = spec["x"]; P = np.cross(np.cross(rig_check.hom(S[i][:2]), rig_check.hom(S[i][2:])), np.cross(rig_check.hom(S[j][:2]), rig_check.hom(S[j][2:])))
        return P[:2] / P[2]
    a, b = S[spec["on"]][:2], S[spec["on"]][2:]; d = (b - a) / np.linalg.norm(b - a); q = np.array(spec["near"], float)
    return a + ((q - a) @ d) * d


# ---------------------------------------------------------------- hybrid: free points + one parametric flight (the pilot)
# Marina's overhead (812 s) and 929 s show a foot/turn the 8-parameter model doesn't describe, so the pilot locates the irregular
# parts as free 3D points (triangulated by the cameras) and keeps only the long straight flight parametric: nosing k at
# (fx0 - k*g, fh0 + k*r, z0). Labels name nosings "nosing@k" with the frame's own count; each frame's count may be shifted by
# up to 2 steps, and the shift with the least misfit is kept and reported. Anchors (the side window, ANCHORS) are fixed;
# Marina's camera height is a prior. Points seen in one frame only get a weak 0.5 m prior to their start, and are flagged.
FLIGHT0 = {"fx0": 1.6, "fh0": 1.2, "g": 0.262, "r": 0.188, "z0": 6.66}


def points_fit(frames, X0, fl0, C0, shifts, rig=True, fix=False):
    """frames: [{name: uv}]; X0: {name: xyz} free points; fl0: flight dict; C0: cameras. Returns X, fl, C, per-label residuals, sd."""
    names = sorted(X0); fk = list(FLIGHT0); nP = 3 * len(names) + len(fk)
    seen = {n: sum(n in f for f in frames) for n in names}
    def unpack(q):
        if fix:
            return X0, fl0, q.reshape(-1, 6)
        X = {n: q[3 * i:3 * i + 3] for i, n in enumerate(names)}; fl = dict(zip(fk, q[3 * len(names):nP]))
        return X, fl, q[nP:].reshape(-1, 6)
    def where(name, X, fl, sh):
        if name.startswith("nosing@"):
            kk = int(name[7:]) + sh; return np.array([fl["fx0"] - kk * fl["g"], fl["fh0"] + kk * fl["r"], fl["z0"]])
        return np.asarray(ANCHORS[name] if name in ANCHORS else X[name], float)
    def res(q):
        X, fl, C = unpack(q); r = []
        for f, c, sh in zip(frames, C, shifts):
            keys = list(f); P = np.array([where(n, X, fl, sh) for n in keys])
            uv, z = project(c, P); r.append(((uv - np.array([f[n] for n in keys])) * (z[:, None] > 0.1) + (z[:, None] <= 0.1) * 500).ravel())
            if rig:   # Marina's fixed rig: one height (rig_check.py) and one field of view (f 1428 from the foyer solves, ~1%)
                r.append([(c[3] - RIG_H) / RIG_SD * 2.0, (c[5] - 1428.0) / 15.0 * 2.0])
        if not fix:
            for n in names:   # one-frame points: 0.5 m prior to their start; every point: a loose 3 m one (keeps the gauge)
                r.append((X[n] - X0[n]) / (0.5 if seen[n] < 2 else 3.0) * 2.0)
        return np.concatenate(r)
    q0 = np.r_[[] if fix else np.r_[np.concatenate([X0[n] for n in names]) if names else [], [fl0[k] for k in fk]], np.ravel(C0)]
    s = least_squares(res, q0, loss="soft_l1", f_scale=3.0, x_scale="jac", max_nfev=4000)
    X, fl, C = unpack(s.x)
    r = s.fun; inl = np.abs(r) < 9; sig = np.sqrt(np.mean(r[inl] ** 2)) if inl.any() else 1.0
    sd = np.sqrt(np.clip(np.diag(np.linalg.pinv(s.jac.T @ s.jac)), 0, None)) * sig
    per = []
    for i, (f, c, sh) in enumerate(zip(frames, C, shifts)):
        for n, uv in f.items():
            per.append((i, n, float(np.linalg.norm(project(c, where(n, X, fl, sh)[None])[0][0] - uv))))
    sdX = {} if fix else {n: sd[3 * i:3 * i + 3] for i, n in enumerate(names)}
    sdF = {} if fix else dict(zip(fk, sd[3 * len(names):nP]))
    return X, fl, C, per, sdX, sdF, s.cost, seen


def init_camera(f, X0, fl0, rig):
    """Multi-start: yaw every 30 deg, a few positions in the breakfast area; the house held at its start values."""
    best = None
    for yaw in np.radians(np.arange(-180, 180, 30)):
        for x, z in ((1.0, 1.5), (0.0, 3.0), (2.5, 2.5), (-0.5, 0.5)):
            c0 = np.array([[yaw, 0.0, x, RIG_H, z, 1428.0]])
            try:
                out = points_fit([f], X0, fl0, c0, [0], rig, fix=True)
            except Exception:
                continue
            if best is None or out[6] < best[6]:
                best = out
    return best[2][0]


def cmd_points(a):
    import json
    L = json.loads(Path(a.labels).read_text())
    fit_fr = [fr for fr in L if not fr.get("held_out")]; held = [fr for fr in L if fr.get("held_out")]
    F0 = features(FREE)
    names = sorted({n for fr in L for n in fr["pts"] if n not in ANCHORS and not n.startswith("nosing@")})
    X0 = {n: np.array(fr0) for n, fr0 in ((n, F0.get(n, (0.0, 1.0, 7.0))) for n in names)}
    for n, v in a_starts(L).items():
        X0[n] = np.array(v, float)
    fl0 = dict(FLIGHT0)
    frames = [{n: np.array(v, float) for n, v in fr["pts"].items()} for fr in fit_fr]
    C0 = np.array([init_camera(f, X0, fl0, True) for f in frames])
    best = None
    for shifts in __import__("itertools").product(*[range(-2, 3) if any(k.startswith("nosing@") for k in f) else [0] for f in frames]):
        out = points_fit(frames, X0, fl0, C0, list(shifts))
        if best is None or out[6] < best[0][6]:
            best = (out, shifts)
    (X, fl, C, per, sdX, sdF, cost, seen), shifts = best
    print(f"fit frames {[fr['frame'] for fr in fit_fr]}; nosing shifts {list(shifts)}")
    for i, fr in enumerate(fit_fr):
        c = C[i]; print(f"  {fr['frame']:12s} camera x {c[2]:+.2f} z {c[4]:+.2f} h {c[3]:.2f} yaw {np.degrees(c[0]):+.0f} pitch {np.degrees(c[1]):+.1f} f {c[5]:.0f}")
    print("flight: " + "  ".join(f"{k} {fl[k]:.3f}±{sdF[k]:.3f}" for k in fl))
    print("points (x, h, z) ± sd, frames seen:")
    for n in sorted(X):
        print(f"  {n:28s} {X[n][0]:+.3f} {X[n][1]:+.3f} {X[n][2]:+.3f}  ± {sdX[n][0]:.3f} {sdX[n][1]:.3f} {sdX[n][2]:.3f}  {seen[n]}{'  <-- one frame: weak' if seen[n] < 2 else ''}")
    bad = [(fit_fr[i]["frame"], n, e) for i, n, e in per if e > 8]
    print(f"label residuals: median {np.median([e for *_, e in per]):.1f} px, max {max(e for *_, e in per):.1f}; over 8 px: {bad}")
    for fr in held:
        f = {n: np.array(v, float) for n, v in fr["pts"].items() if n in ANCHORS or n.startswith("nosing@") or n in X}
        c0 = init_camera(f, X, fl, True)
        hb = min((points_fit([f], X, fl, np.array([c0]), [sh], True, fix=True) for sh in range(-2, 3)), key=lambda o: o[6])
        e = [x for *_, x in hb[3]]
        print(f"HELD-OUT {fr['frame']}: median {np.median(e):.1f} px, max {max(e):.1f} px over {len(e)} labels")
    out = {"frames": [fr["frame"] for fr in fit_fr], "shifts": list(shifts), "flight": fl, "flight_sd": sdF,
           "points": {n: X[n].tolist() for n in X}, "points_sd": {n: sdX[n].tolist() for n in X}, "seen": seen,
           "cameras": {fr["frame"]: C[i].tolist() for i, fr in enumerate(fit_fr)}, "residuals": [(fit_fr[i]["frame"], n, round(e, 2)) for i, n, e in per]}
    Path(a.labels).with_suffix(".result.json").write_text(json.dumps(out, indent=1, default=float))
    if a.overlay:
        from PIL import Image, ImageDraw
        for i, fr in enumerate(fit_fr):
            im = Image.open(frame_path(fr["frame"])).convert("RGB"); d = ImageDraw.Draw(im)
            for n, uv in fr["pts"].items():
                if n.startswith("nosing@"):
                    kk = int(n[7:]) + shifts[i]; P3 = [fl["fx0"] - kk * fl["g"], fl["fh0"] + kk * fl["r"], fl["z0"]]
                else:
                    P3 = ANCHORS.get(n, X.get(n))
                q = project(C[i], np.array([P3]))[0][0]
                d.ellipse([uv[0] - 5, uv[1] - 5, uv[0] + 5, uv[1] + 5], outline=(0, 220, 0), width=2)
                d.line([tuple(uv), tuple(q)], fill=(255, 0, 0), width=2); d.text((uv[0] + 7, uv[1] - 14), n, fill=(255, 255, 0))
            for kk in range(-6, 16):     # the fitted flight's nosing line
                q = project(C[i], np.array([[fl["fx0"] - kk * fl["g"], fl["fh0"] + kk * fl["r"], fl["z0"]]]))[0][0]
                d.ellipse([q[0] - 3, q[1] - 3, q[0] + 3, q[1] + 3], outline=(255, 0, 255))
            o = Path(__file__).resolve().parents[2] / f"sfm-work/joint/{fr['frame']}-fit.jpg"; o.parent.mkdir(parents=True, exist_ok=True); im.save(o, quality=88)
        print("overlays: sfm-work/joint/*-fit.jpg")


def a_starts(L):
    """Optional start values for free points, given in the labels file as {"start": {name: [x, h, z]}}."""
    out = {}
    for fr in L:
        out.update(fr.get("start", {}))
    return out


def cmd_points_selftest(a):
    """Synthetic: build features from a known truth, 4 Marina-like cameras, 1.5 px noise; free points must come back within 3 cm."""
    rng = np.random.default_rng(2); ok = True
    F = features(FREE); fl = dict(FLIGHT0, fx0=0.9, fh0=1.30)
    names = ["newel top", "newel foot", "post top", "door L head", "door R head", "door L foot", "door R foot", "doorway R head", "doorway L head"]
    truth = {n: np.array(F[n]) + rng.normal(0, 0.2, 3) for n in names}
    C = views(rng, 5, False); frames = []
    for c in C:
        f = {}
        for n in names + list(ANCHORS):
            P3 = truth[n] if n in truth else np.array(ANCHORS[n]); uv, z = project(c, P3[None])
            if z[0] > 0.3 and 0 <= uv[0][0] < W and 0 <= uv[0][1] < H:
                f[n] = uv[0] + rng.normal(0, 1.5, 2)
        for kk in range(0, 6):
            P3 = np.array([fl["fx0"] - kk * fl["g"], fl["fh0"] + kk * fl["r"], fl["z0"]]); uv, z = project(c, P3[None])
            if z[0] > 0.3 and 0 <= uv[0][0] < W and 0 <= uv[0][1] < H:
                f[f"nosing@{kk + 1}"] = uv[0] + rng.normal(0, 1.5, 2)    # labelled one step out: the shift search must find -1
        frames.append(f)
    X0 = {n: np.array(F[n], float) for n in names}
    C0 = np.array([init_camera(f, X0, FLIGHT0, True) for f in frames])
    best = min((points_fit(frames, X0, dict(FLIGHT0), C0, [sh] * len(frames)) + (sh,) for sh in range(-2, 3)), key=lambda o: o[6])
    X, flf, sdX, sh = best[0], best[1], best[4], best[-1]
    # a shift common to every frame is the same as moving the flight one step, so compare nosing POSITIONS, not the shift
    nose = lambda f, k: np.array([f["fx0"] - k * f["g"], f["fh0"] + k * f["r"], f["z0"]])
    nerr = max(np.linalg.norm(nose(flf, k + sh) - nose(fl, k - 1)) for k in range(1, 6))
    z = {n: np.linalg.norm(X[n] - truth[n]) / max(np.linalg.norm(sdX[n]), 1e-6) for n in names if best[7][n] >= 2}
    for n in names:
        if best[7][n] >= 2:
            print(f"   {n:16s} error {100 * np.linalg.norm(X[n] - truth[n]):5.1f} cm  sd {100 * np.linalg.norm(sdX[n]):5.1f} cm  seen {best[7][n]}")
    good = nerr < 0.02 and max(z.values()) < 4 and abs(flf["g"] - fl["g"]) < 0.01; ok &= good
    print(f"nosings within {100 * nerr:.1f} cm; every point inside 4 sd of the truth (worst {max(z.values()):.1f}); going {flf['g']:.3f}  {'ok' if good else 'FAIL'}")
    print("POINTS SELFTEST", "PASS" if ok else "FAIL")
    raise SystemExit(0 if ok else 1)


# ---------------------------------------------------------------- tracked cameras (COLMAP) + triangulated labels
# The hand-label-only fit was underdetermined (sfm-plan, Oct 15 night). Here the cameras come from COLMAP's sequential tracking of
# Marina's walk (hundreds of matches a frame), metric and level from her fixed rig: her camera centres lie on one horizontal plane
# (its normal is up), and their height above the floor (the densest low band of tracked points) is 0.639 x 80 in. Labels then only
# triangulate the named points. Output distances and heights do not depend on the plan's origin.
def read_colmap(model):
    """cameras.txt/images.txt of a TXT model -> {image name: (K, k1, R, t)} (x_cam = R X + t)."""
    cams = {}
    for l in (model / "cameras.txt").read_text().splitlines():
        if l and not l.startswith("#"):
            f = l.split(); cams[int(f[0])] = (f[1], list(map(float, f[4:])))
    out = {}; lines = [l for l in (model / "images.txt").read_text().splitlines() if l and not l.startswith("#")]
    for l in lines[::2]:
        f = l.split(); qw, qx, qy, qz = map(float, f[1:5]); t = np.array(list(map(float, f[5:8])))
        R = np.array([[1 - 2 * (qy * qy + qz * qz), 2 * (qx * qy - qz * qw), 2 * (qx * qz + qy * qw)],
                      [2 * (qx * qy + qz * qw), 1 - 2 * (qx * qx + qz * qz), 2 * (qy * qz - qx * qw)],
                      [2 * (qx * qz - qy * qw), 2 * (qy * qz + qx * qw), 1 - 2 * (qx * qx + qy * qy)]])
        model_, par = cams[int(f[8])]; fx, cx, cy, k1 = par[0], par[1], par[2], (par[3] if len(par) > 3 else 0.0)
        out[f[9]] = (np.array([[fx, 0, cx], [0, fx, cy], [0, 0, 1]]), k1, R, t)
    P3 = {int(l.split()[0]): np.array(list(map(float, l.split()[1:4]))) for l in (model / "points3D.txt").read_text().splitlines() if l and not l.startswith("#")}
    for head, kp in zip(lines[::2], lines[1::2]):   # each image's keypoints that belong to a track: [(u, v, point id)]
        v = np.array(kp.split(), float).reshape(-1, 3); out[head.split()[9]] += (v[v[:, 2] >= 0],)
    return out, np.array(list(P3.values())), P3


def undistort(uv, K, k1):
    x = np.linalg.solve(K, [uv[0], uv[1], 1.0])[:2]; y = x.copy()
    for _ in range(10):
        y = x / (1 + k1 * (y @ y))
    return y


def triangulate(obs):
    """obs: [(R, t, xn)] normalised image points -> X minimising the algebraic error (DLT), and per-view reprojection (normalised)."""
    A = []
    for R, t, xn in obs:
        Pm = np.c_[R, t]; A += [xn[0] * Pm[2] - Pm[0], xn[1] * Pm[2] - Pm[1]]
    X = np.linalg.svd(np.array(A))[2][-1]; X = X[:3] / X[3]
    err = [np.linalg.norm(((R @ X + t)[:2] / (R @ X + t)[2]) - xn) for R, t, xn in obs]
    return X, err


def metric_frame(C, pts, down=None, rights=None):
    """Up = normal of the camera-centre plane (her camera height is fixed), signed against the cameras' own image-down axis
    (a tracked-point majority is not safe: beams and wallpaper put most points above the eye); floor = lowest dense band of
    points; scale from 1.298 m."""
    c0 = C.mean(0); sv = np.linalg.svd(C - c0)[1]; up = np.linalg.svd(C - c0)[2][-1]
    if rights is not None:   # roll 0 (CG camera, level horizons): up is perpendicular to every camera's x axis. A near-straight
        up = np.linalg.svd(np.asarray(rights))[2][-1]   # walk leaves the centre-plane normal free to tilt about the path
    if down is not None and up @ down > 0:
        up = -up
    print(f"  path singular values {sv[0]:.2f} {sv[1]:.2f} {sv[2]:.3f} (a small middle one = near-straight walk); "
          f"up vs centre-plane normal {np.degrees(np.arccos(min(1, abs(up @ np.linalg.svd(C - c0)[2][-1])))):.1f} deg")
    h = (pts - c0) @ up
    # The floor is the LOWEST band that stands out (>= 2x both neighbours) and spreads at least as far as the camera travels.
    # Not the densest band: on Marina's breakfast walk the patterned chair seats (1,522 points over 5 x 5 units) outnumber the
    # dark floor tiles (140 points over 16 x 12) ten to one, and taking them made every height 55% too large (Oct 15 night).
    e1 = np.linalg.svd(C - c0)[2][0]; e2 = np.cross(up, e1); reach = max(np.ptp((C - c0) @ e1), 1e-9)
    lo = h[h < 0]; step = 0.03 * float(-np.percentile(lo, 0.2))
    edges = np.arange(lo.min() - step, 0, step); cnt = np.histogram(lo, edges)[0]; floor = None
    for i in range(1, len(cnt) - 1):
        m = (h >= edges[i]) & (h < edges[i + 1]); P = pts[m] - c0
        if cnt[i] < 30 or cnt[i] < 2 * max(cnt[i - 1], cnt[i + 1]):
            continue
        if np.percentile(P @ e1, 95) - np.percentile(P @ e1, 5) >= reach and np.percentile(P @ e2, 95) - np.percentile(P @ e2, 5) >= 0.5 * reach:
            floor = float(np.median(h[m])); break
    if floor is None:
        raise SystemExit("no floor band found: label floor contacts instead")
    cam_h = -floor                                  # camera plane height above the floor, model units
    return up, c0, RIG_H / cam_h, cam_h, float(np.std((C - c0) @ up) / cam_h)


def cmd_track(a):
    import json, subprocess
    ws = Path(a.workspace); model = max((ws / "sparse").glob("*/"), key=lambda m: (m / "images.bin").stat().st_size)   # most registered frames
    txt = ws / "txt"; txt.mkdir(exist_ok=True)
    subprocess.run(["colmap", "model_converter", "--input_path", str(model), "--output_path", str(txt), "--output_type", "TXT"], check=True, capture_output=True)
    V, pts, P3 = read_colmap(txt)
    C = np.array([-R.T @ t for K, k1, R, t, _ in V.values()])
    down = np.mean([R.T @ [0, 1, 0] for K, k1, R, t, _ in V.values()], axis=0)    # image +v is down in the world
    up, c0, s, cam_h, flat = metric_frame(C, pts, down, [R.T @ [1, 0, 0] for K, k1, R, t, _ in V.values()])
    print(f"{len(V)} cameras registered; camera-centre plane flat to {100 * flat:.1f}% of eye height; scale {s:.4f} m/unit; f {list(V.values())[0][0][0, 0]:.0f} px")
    L = json.loads(Path(a.labels).read_text())
    name_of = lambda fr: f"f_{int(round((float(fr['frame'].split('-')[1]) - a.start) * a.fps)) + 1:05d}.jpg"
    obs = {}; snaps = {}
    for fr in L:
        im = name_of(fr)
        if im not in V:
            print(f"  {fr['frame']} -> {im}: not registered"); continue
        K, k1, R, t, kp = V[im]
        for n, uv in fr["pts"].items():
            if isinstance(uv, dict) and "p3d" in uv:          # a tracked point picked by id (joint_fit.py kp)
                snaps.setdefault(n, []).append((fr["frame"], P3[int(uv["p3d"])], 0.0)); continue
            if isinstance(uv, dict) and "floor" in uv:        # a floor contact: the pixel's ray meets the floor plane
                Cc = -R.T @ t; dvec = R.T @ np.r_[undistort(uv["floor"], K, k1), 1.0]
                hc = (Cc - c0) @ up * s + RIG_H; lam = -hc / ((dvec @ up) * s)
                snaps.setdefault(n, []).append((fr["frame"], Cc + lam * dvec, 0.0)); continue
            obs.setdefault(n, []).append((R, t, undistort(uv, K, k1), fr["frame"], K[0, 0]))
            d = np.hypot(kp[:, 0] - uv[0], kp[:, 1] - uv[1]); j = int(np.argmin(d)) if len(d) else -1
            if j >= 0 and d[j] <= a.snap:     # a tracked feature under the label: its 3D point, from this frame alone
                snaps.setdefault(n, []).append((fr["frame"], P3[int(kp[j, 2])], float(d[j])))
    out = {}
    for n, o in sorted(obs.items()):
        if len(o) < 2:
            continue
        X, err = triangulate([(R, t, xn) for R, t, xn, *_ in o])
        px = [e * f for e, (*_, f) in zip(err, o)]
        hgt = ((X - c0) @ up) * s + RIG_H
        out[n] = {"X": X.tolist(), "h_m": round(float(hgt), 3), "px": [round(p, 1) for p in px], "frames": [fr for *_, fr, f in o]}
        print(f"  {n:28s} height {hgt:6.3f} m   reprojection {', '.join(f'{p:.1f}' for p in px)} px   ({len(o)} frames)")
    print(f"snapped to tracked features (within {a.snap} px), per frame: height m, and spread between frames (cm)")
    for n, sn in sorted(snaps.items()):
        Xs = np.array([X for _, X, _ in sn]); hs = ((Xs - c0) @ up) * s + RIG_H
        spread = 100 * np.max(np.linalg.norm(Xs - Xs.mean(0), axis=1)) * s if len(sn) > 1 else float("nan")
        print(f"  {n:28s} " + "  ".join(f"{fr[-3:]}: {h:.3f} ({d:.1f}px)" for (fr, _, d), h in zip(sn, hs)) + f"   spread {spread:.0f} cm")
        out.setdefault(n, {})["S"] = Xs.mean(0).tolist()
        out[n]["snapped"] = [{"frame": fr, "X": X.tolist(), "h_m": round(float(h), 3), "px": round(d, 1)} for (fr, X, d), h in zip(sn, hs)]
    names = sorted(out)
    print("horizontal distances (m):")
    for i, a_ in enumerate(names):
        for b_ in names[i + 1:]:
            pa, pb = (out[a_].get("S", out[a_].get("X")), out[b_].get("S", out[b_].get("X")))   # snapped/floor points first
            if pa is None or pb is None:
                continue
            d = (np.array(pa) - np.array(pb)) * s; d -= (d @ up) * up
            if a.pairs and f"{a_}|{b_}" not in a.pairs and f"{b_}|{a_}" not in a.pairs:
                continue
            print(f"  {a_:22s} - {b_:22s} {np.linalg.norm(d):6.3f}")
    Path(a.labels).with_suffix(".track.json").write_text(json.dumps({"workspace": str(ws), "scale_m_per_unit": s, "up": up.tolist(),
        "camera_plane_flatness": flat, "points": out}, indent=1))


def cmd_track_selftest(a):
    """Synthetic: cameras on a level plane at 1.298 m (arbitrary similarity transform applied), floor points; recover heights and a distance."""
    rng = np.random.default_rng(4); ok = True
    Rw = np.linalg.qr(rng.normal(size=(3, 3)))[0]; Rw *= np.sign(np.linalg.det(Rw)); sc, tw = 0.37, rng.normal(size=3)
    to_model = lambda X: (Rw @ (np.asarray(X) / 1.0)) * sc + tw          # world metres (y up) -> model units
    cams = []
    for i in range(8):
        cw = np.array([rng.uniform(0, 3), RIG_H, rng.uniform(0, 2)]); yaw = rng.uniform(-0.5, 0.5)
        Rc = rot(yaw - np.pi / 2, rng.uniform(-0.05, 0.05))                # world -> camera
        Rm = Rc @ Rw.T; cm = to_model(cw); cams.append((Rm, -Rm @ cm, Rc, cw))
    floor = [to_model([x, rng.normal(0, 0.003), z]) for x in np.linspace(-1, 4, 20) for z in np.linspace(2, 8, 20)]
    floor += [to_model([rng.uniform(-1, 4), rng.uniform(0.2, 2.4), rng.uniform(2, 8)]) for _ in range(150)]   # furniture, walls
    target = {"A": np.array([1.0, 2.0, 6.0]), "B": np.array([2.5, 0.9, 7.0])}
    C = np.array([-R.T @ t for R, t, *_ in cams]); up, c0, s, cam_h, flat = metric_frame(C, np.array(floor), np.mean([R.T @ [0, 1, 0] for R, t, *_ in cams], axis=0), [R.T @ [1, 0, 0] for R, t, *_ in cams])
    est = {}
    for n, Xw in target.items():
        obs = []
        for R, t, Rc, cw in cams:
            xc = R @ to_model(Xw) + t
            if xc[2] > 0.2:
                obs.append((R, t, xc[:2] / xc[2] + rng.normal(0, 1.5 / 1428, 2)))
        X, _ = triangulate(obs); est[n] = X
    hA = ((est["A"] - c0) @ up) * s + RIG_H; dAB = np.linalg.norm(est["A"] - est["B"]) * s
    good = abs(hA - 2.0) < 0.02 and abs(dAB - np.linalg.norm(target["A"] - target["B"])) < 0.02; ok &= good
    print(f"height A {hA:.3f} (2.000), |AB| {dAB:.3f} ({np.linalg.norm(target['A'] - target['B']):.3f})  {'ok' if good else 'FAIL'}")
    print("TRACK SELFTEST", "PASS" if ok else "FAIL")
    raise SystemExit(0 if ok else 1)


def cmd_kp(a):
    """Tracked features (with their COLMAP point ids) over a crop of one frame, 2x, for labelling by point id."""
    from PIL import Image, ImageDraw
    ws = Path(a.workspace); V, _, _ = read_colmap(ws / "txt")
    im_name = f"f_{int(round((a.t - a.start) * a.fps)) + 1:05d}.jpg"; kp = V[im_name][4]
    x0, y0, x1, y1 = a.roi; k = 2
    im = Image.open(ws / "images" / im_name).convert("RGB").crop((x0, y0, x1, y1)); im = im.resize((im.width * k, im.height * k)); d = ImageDraw.Draw(im)
    for u, v, pid in kp:
        if x0 <= u < x1 and y0 <= v < y1:
            q = ((u - x0) * k, (v - y0) * k); d.ellipse([q[0] - 3, q[1] - 3, q[0] + 3, q[1] + 3], outline=(255, 40, 40), width=2)
            d.text((q[0] + 4, q[1] - 11), str(int(pid)), fill=(255, 255, 0))
    out = ws / f"kp-{a.t:g}-{x0}-{y0}.png"; im.save(out); print(out, f"({im_name})")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); sp = ap.add_subparsers(dest="cmd", required=True)
    s = sp.add_parser("rehearse"); s.add_argument("--seed", type=int, default=0); s.set_defaults(fn=cmd_rehearse)
    s = sp.add_parser("points"); s.add_argument("labels"); s.add_argument("--overlay", action="store_true"); s.set_defaults(fn=cmd_points)
    s = sp.add_parser("track"); s.add_argument("workspace"); s.add_argument("labels"); s.add_argument("--start", type=float, default=914.0)
    s.add_argument("--fps", type=float, default=5.0); s.add_argument("--pairs", nargs="*"); s.add_argument("--snap", type=float, default=4.0); s.set_defaults(fn=cmd_track)
    s = sp.add_parser("kp"); s.add_argument("workspace"); s.add_argument("t", type=float); s.add_argument("roi", type=int, nargs=4)
    s.add_argument("--start", type=float, default=914.0); s.add_argument("--fps", type=float, default=5.0); s.set_defaults(fn=cmd_kp)
    s = sp.add_parser("track-selftest"); s.set_defaults(fn=cmd_track_selftest)
    s = sp.add_parser("points-selftest"); s.set_defaults(fn=cmd_points_selftest)
    s = sp.add_parser("segs"); s.add_argument("frame"); s.add_argument("roi", type=int, nargs=4); s.set_defaults(fn=cmd_segs)
    a = ap.parse_args(); a.fn(a)
