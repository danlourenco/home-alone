"""Shared loading/alignment for the synthetic scorer and plot."""
import json
import subprocess
from pathlib import Path

import numpy as np


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


def image_lines(txt):
    """Header line per image. images.txt alternates header / 2D-points lines, and the points line is
    empty for an image with no observations, so blank lines must be kept before pairing."""
    body = [l for l in (Path(txt) / "images.txt").read_text().split("\n") if not l.startswith("#")]
    return [h for h in body[::2] if h.strip()]


def load_model(ws, model, with_names=False):
    """Estimated centres, true centres (z flipped: Unity is left-handed), shot ids; contaminants skipped."""
    ws = Path(ws)
    gt = {f["i"]: f for f in json.loads((ws / "gt.json").read_text())["frames"]}
    timeline = json.loads((ws / "timeline.json").read_text())
    txt = Path(model) / "txt"
    txt.mkdir(exist_ok=True)
    if (Path(model) / "images.bin").exists():  # COLMAP solve; VGGT writes TXT directly
        subprocess.run(["colmap", "model_converter", "--input_path", model, "--output_path", txt, "--output_type", "TXT"],
                       check=True, capture_output=True)
    lines = image_lines(txt)
    est, true, shots, names = [], [], [], []
    for l in lines:
        f = l.split()
        src = timeline[int(Path(f[-1]).name[2:7])]
        if src is None:
            continue
        R = quat_to_R(*map(float, f[1:5]))
        est.append(-R.T @ np.array(list(map(float, f[5:8]))))
        p = gt[src]["pos"]
        true.append([p[0], p[1], -p[2]])
        shots.append(gt[src]["shot"])
        names.append(Path(f[-1]).name)
    if with_names:
        return np.array(est), np.array(true), shots, names
    return np.array(est), np.array(true), shots
