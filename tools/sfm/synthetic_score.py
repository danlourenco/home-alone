"""Score a COLMAP/VGGT solve of the synthetic tour against Unity ground truth (metres).
Images named v_<videoframe>.jpg (optionally under shot folders); timeline.json maps video frame -> render index.
Reports per model: registration, Sim3 position error, proportional stretch, FOV.
usage: PYTHONPATH=tools/sfm uv run --with numpy python tools/sfm/synthetic_score.py <ws> <sparse_dir>
"""
import sys
from pathlib import Path

import numpy as np

from synthetic_score_lib import image_lines, load_model, umeyama

ws, sparse = Path(sys.argv[1]), Path(sys.argv[2])
n_images = len(list((ws / "images").rglob("*.jpg")))

for model in sorted(p for p in sparse.iterdir() if p.is_dir()):
    est, true, shots = load_model(ws, model)
    txt = model / "txt"
    n_reg = len(image_lines(txt))
    print(f"== {model.name}: {n_reg}/{n_images} images registered, {n_reg - len(est)} contaminant frames registered, shots {sorted(set(shots))}")
    if len(est) < 10:
        continue
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
    cams = [l.split() for l in (txt / "cameras.txt").read_text().splitlines() if l and not l.startswith("#")]
    vfov = np.degrees(2 * np.arctan(540 / np.array([float(c[4]) for c in cams])))
    print(f"   {len(cams)} camera(s): solved vfov min/median/max {vfov.min():.1f}/{np.median(vfov):.1f}/{vfov.max():.1f} deg "
          f"(truth per shot: 55, 42, 62, 50->36 zoom)")
