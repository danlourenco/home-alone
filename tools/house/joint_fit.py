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

import numpy as np
from scipy.optimize import least_squares

RIG_H, RIG_SD = 0.639 * 80 * 0.0254, 0.03     # Marina camera height prior (2.5% spread)
W, H = 1920, 1080

# ---------------------------------------------------------------- the model
# Free parameters, initialised from the build (spec metres; reconcile.service_stair_spec + the enclosure trace).
FREE = {"newel_x": 2.37,        # x1: the foot's newel side (the enclosure's doorway end)
        "open_z": 6.66,         # z0: the stair's open side toward the room
        "going": 0.262, "rise": 0.188,
        "door_x0": -1.43, "door_x1": -0.72, "door_head": 2.032,   # basement door in the open-side plane
        "ceiling": 2.438}
WALL_Z, END_X, NB = 7.638, -1.505, 4    # anchored: the foyer-side wall face, the kitchen's back-right corner, 4 foot steps

# Anchors: established geometry that fixes frame and scale (foyer doorway from the film-solved foyer; corner and window from the trace)
ANCHORS = {"doorway L foot": (3.043, 0, WALL_Z), "doorway L head": (3.043, 2.20, WALL_Z),
           "doorway R foot": (4.025, 0, WALL_Z), "doorway R head": (4.025, 2.20, WALL_Z),
           "corner foot": (END_X, 0, WALL_Z), "window sill near": (END_X, 0.82, 4.99), "window sill far": (END_X, 0.82, 5.79),
           "window head near": (END_X, 2.15, 4.99), "window head far": (END_X, 2.15, 5.79), "hutch corner foot": (4.12, 0, 6.0)}


def features(p):
    """Every labelled point as a function of the parameters (dict name -> xyz with y = height above the floor)."""
    x1, z0, g, r = p["newel_x"], p["open_z"], p["going"], p["rise"]
    w = WALL_Z - z0; xl = x1 - w; F = dict(ANCHORS)
    F["newel foot"] = (x1 - 0.05, 0, z0 - NB * g + 0.05); F["newel top"] = (x1 - 0.05, r + 1.0, z0 - NB * g + 0.05)
    F["post foot"] = (xl + 0.05, 0, z0 - 0.05); F["post top"] = (xl + 0.05, (NB + 1) * r + 1.05, z0 - 0.05)
    for k in range(1, NB + 1):                     # the foot's nosings, both ends
        F[f"foot{k} nosing room end"] = (xl, k * r, z0 - (NB - k + 1) * g)
        F[f"foot{k} nosing newel end"] = (x1, k * r, z0 - (NB - k + 1) * g)
    for k in range(1, 13):                         # flight nosings on the open side (a fixed set, so the fit stays smooth;
        F[f"flight{k} nosing"] = (xl - (k - 1) * g, (NB + 1 + k) * r, z0)   # synth() keeps only those under the ceiling)
    F["flight meets ceiling"] = (xl - (p["ceiling"] / r - NB - 2) * g, p["ceiling"], z0)   # the nosing line at ceiling height
    F["ceiling corner"] = (END_X, p["ceiling"], WALL_Z)
    F["door L foot"] = (p["door_x0"], 0, z0); F["door R foot"] = (p["door_x1"], 0, z0)
    F["door L head"] = (p["door_x0"], p["door_head"], z0); F["door R head"] = (p["door_x1"], p["door_head"], z0)
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
    truth = {k: v + (rng.normal(0, 0.25) if k not in ("going", "rise", "door_head", "ceiling") else rng.normal(0, 0.015)) for k, v in FREE.items()}
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


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); sp = ap.add_subparsers(dest="cmd", required=True)
    s = sp.add_parser("rehearse"); s.add_argument("--seed", type=int, default=0); s.set_defaults(fn=cmd_rehearse)
    a = ap.parse_args(); a.fn(a)
