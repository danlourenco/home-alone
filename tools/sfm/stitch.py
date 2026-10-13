"""Chain overlapping VGGT models (short clips of one long walk) into the first model's frame.
Each model is aligned to the previous one by a similarity fit on the camera centres of the frames they share;
the fit residual (as % of the shared path length) is printed so a bad link is visible, not hidden.
Writes a merged model dir (txt/, points.npy, pixels.npz) that plan_extract.py / door_scale.py read as usual.
usage: PYTHONPATH=tools/sfm uv run --with numpy python tools/sfm/stitch.py <out_dir> <vggt_model_dir> <vggt_model_dir> ...
"""
import shutil
import sys
from pathlib import Path

import numpy as np

from synthetic_score_lib import image_lines, quat_to_R, umeyama


def R_to_quat(R):
    w = np.sqrt(max(0.0, 1 + np.trace(R))) / 2
    x = np.copysign(np.sqrt(max(0.0, 1 + R[0, 0] - R[1, 1] - R[2, 2])) / 2, R[2, 1] - R[1, 2])
    y = np.copysign(np.sqrt(max(0.0, 1 - R[0, 0] + R[1, 1] - R[2, 2])) / 2, R[0, 2] - R[2, 0])
    z = np.copysign(np.sqrt(max(0.0, 1 - R[0, 0] - R[1, 1] + R[2, 2])) / 2, R[1, 0] - R[0, 1])
    return np.array([w, x, y, z])


def poses(model):
    """frame name -> (world->camera rotation, translation)."""
    out = {}
    for l in image_lines(Path(model) / "txt"):
        f = l.split()
        out[Path(f[-1]).name] = (quat_to_R(*map(float, f[1:5])), np.array(list(map(float, f[5:8]))))
    return out


def centre(Rt):
    return -Rt[0].T @ Rt[1]


def main():
    out, models = Path(sys.argv[1]), [Path(m) for m in sys.argv[2:]]
    T = (1.0, np.eye(3), np.zeros(3))  # current model -> merged frame
    merged, pts, pix = {}, [], {"names": [], "images": [], "world": [], "conf": []}
    for k, m in enumerate(models):
        P = poses(m)
        if k:
            shared = sorted(set(P) & set(merged))
            if len(shared) < 3:
                sys.exit(f"{m}: only {len(shared)} frames shared with the previous clips; cannot link")
            src = np.array([centre(P[n]) for n in shared])
            dst = np.array([centre(merged[n]) for n in shared])
            T = umeyama(src, dst)
            res = np.linalg.norm(T[0] * src @ T[1].T + T[2] - dst, axis=1)
            path = np.linalg.norm(np.diff(dst, axis=0), axis=1).sum()
            print(f"{m}: {len(shared)} shared frames, residual median {np.median(res) / path:.1%} / max "
                  f"{res.max() / path:.1%} of shared path ({path:.3f} units), scale {T[0]:.3f}")
        s, R, t = T
        for n, (Rc, tc) in P.items():
            if n not in merged:  # first model to see a frame owns it
                merged[n] = (Rc @ R.T, s * tc - Rc @ R.T @ t)
        pts.append(s * np.load(m / "points.npy") @ R.T + t)
        d = np.load(m / "pixels.npz")
        pix["names"].append(d["names"]); pix["images"].append(d["images"]); pix["conf"].append(d["conf"])
        pix["world"].append((s * d["world"] @ R.T + t).astype(np.float32))

    shutil.rmtree(out, ignore_errors=True)
    (out / "txt").mkdir(parents=True)
    names = sorted(merged)
    (out / "txt/cameras.txt").write_text("".join(f"{i + 1} SIMPLE_PINHOLE 1920 1080 1000 960 540\n" for i in range(len(names))))
    (out / "txt/images.txt").write_text("".join(
        f"{i + 1} {' '.join(map(str, R_to_quat(merged[n][0])))} {' '.join(map(str, merged[n][1]))} {i + 1} merged/{n}\n\n"
        for i, n in enumerate(names)))
    (out / "txt/points3D.txt").write_text("")
    np.save(out / "points.npy", np.concatenate(pts))
    np.savez_compressed(out / "pixels.npz", **{k: np.concatenate(v) for k, v in pix.items()})
    print(f"merged {len(models)} models, {len(names)} frames -> {out}")


if __name__ == "__main__":
    Rz = quat_to_R(*R_to_quat(quat_to_R(0.5, 0.5, 0.5, 0.5)))
    assert np.allclose(Rz, quat_to_R(0.5, 0.5, 0.5, 0.5))
    main()
