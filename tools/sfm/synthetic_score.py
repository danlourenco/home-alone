"""Score a COLMAP solve of the synthetic tour against Unity ground truth (metres).
Images must be named v_<videoframe>.jpg; timeline.json maps video frame -> render index (null = contaminant).
Reports per model: registration, contaminants registered, Sim3 position error, proportional stretch, FOV error.
usage: uv run --with numpy python -I tools/sfm/synthetic_score.py <ws> <sparse_dir>
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

ws, sparse = Path(sys.argv[1]), Path(sys.argv[2])
gt = {f["i"]: f for f in json.loads((ws / "gt.json").read_text())["frames"]}
timeline = json.loads((ws / "timeline.json").read_text())
n_images = len(list((ws / "images").rglob("*.jpg")))


def quat_to_R(w, x, y, z):
    return np.array([[1-2*(y*y+z*z), 2*(x*y-w*z), 2*(x*z+w*y)],
                     [2*(x*y+w*z), 1-2*(x*x+z*z), 2*(y*z-w*x)],
                     [2*(x*z-w*y), 2*(y*z+w*x), 1-2*(x*x+y*y)]])


def umeyama(src, dst):
    """Similarity (s, R, t) minimising |s R src + t - dst|, no reflection."""
    mu_s, mu_d = src.mean(0), dst.mean(0)
    a, b = src - mu_s, dst - mu_d
    U, S, Vt = np.linalg.svd(b.T @ a / len(src))
    D = np.diag([1, 1, np.sign(np.linalg.det(U @ Vt))])
    R = U @ D @ Vt
    s = np.trace(np.diag(S) @ D) / a.var(0).sum()
    return s, R, mu_d - s * R @ mu_s


for model in sorted(p for p in sparse.iterdir() if p.is_dir()):
    txt = model / "txt"
    txt.mkdir(exist_ok=True)
    subprocess.run(["colmap", "model_converter", "--input_path", model, "--output_path", txt, "--output_type", "TXT"],
                   check=True, capture_output=True)
    lines = [l for l in (txt / "images.txt").read_text().splitlines() if l and not l.startswith("#")][::2]
    est, true, contaminants, shots = [], [], 0, set()
    for l in lines:
        f = l.split()
        src = timeline[int(Path(f[-1]).name[2:7])]
        if src is None:
            contaminants += 1
            continue
        R = quat_to_R(*map(float, f[1:5]))
        est.append(-R.T @ np.array(list(map(float, f[5:8]))))
        p = gt[src]["pos"]
        true.append([p[0], p[1], -p[2]])  # Unity is left-handed; flip z for a proper rotation fit
        shots.add(gt[src]["shot"])
    print(f"== {model.name}: {len(lines)}/{n_images} images registered, {contaminants} contaminant frames registered, shots {sorted(shots)}")
    if len(est) < 10:
        continue
    est, true = np.array(est), np.array(true)
    s, R, t = umeyama(est, true)
    aligned = (s * (R @ est.T)).T + t
    err = np.linalg.norm(aligned - true, axis=1)
    extent = np.ptp(true, axis=0)
    print(f"   position error after Sim3: median {np.median(err)*100:.1f} cm, p95 {np.percentile(err, 95)*100:.1f} cm "
          f"(path extent {extent[0]:.1f} x {extent[2]:.1f} m)")
    # Proportional stretch: best affine map from aligned estimate to truth in the floor plane (x, z).
    A, *_ = np.linalg.lstsq(np.c_[aligned[:, [0, 2]], np.ones(len(aligned))], true[:, [0, 2]], rcond=None)
    sv = np.linalg.svd(A[:2].T, compute_uv=False)
    print(f"   floor-plane stretch: axis scales {sv[0]:.4f} / {sv[1]:.4f} -> proportion error {(sv[0]/sv[1]-1)*100:.2f}%")
    for cam in [l for l in (txt / "cameras.txt").read_text().splitlines() if l and not l.startswith("#")]:
        c = cam.split()
        vfov = np.degrees(2 * np.arctan(540 / float(c[4])))
        print(f"   camera {c[0]} {c[1]}: solved vfov {vfov:.1f} deg (truth per shot: 55, 42, 62, 50->36 zoom)")
