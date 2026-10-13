"""Reconstruct each images/<shot>/ folder with VGGT and write a COLMAP TXT model per shot,
so tools/sfm/synthetic_score.py grades it exactly like a COLMAP solve.
Weights: facebook/VGGT-1B (NON-COMMERCIAL licence; VGGT-1B-Commercial needs an application).
usage: sfm-work/.venv/bin/python tools/sfm/vggt_solve.py <ws> [max_frames_per_chunk=40]
"""
import sys
from pathlib import Path

import numpy as np
import torch
from vggt.models.vggt import VGGT
from vggt.utils.load_fn import load_and_preprocess_images
from vggt.utils.pose_enc import pose_encoding_to_extri_intri

ws = Path(sys.argv[1])
chunk = int(sys.argv[2]) if len(sys.argv) > 2 else 40
device = "mps" if torch.backends.mps.is_available() else "cpu"
model = VGGT.from_pretrained("facebook/VGGT-1B").to(device).eval()
out_root = ws / "sparse"
out_root.mkdir(exist_ok=True)


def rot_to_quat(R):
    w = np.sqrt(max(0.0, 1 + R[0, 0] + R[1, 1] + R[2, 2])) / 2
    x = np.copysign(np.sqrt(max(0.0, 1 + R[0, 0] - R[1, 1] - R[2, 2])) / 2, R[2, 1] - R[1, 2])
    y = np.copysign(np.sqrt(max(0.0, 1 - R[0, 0] + R[1, 1] - R[2, 2])) / 2, R[0, 2] - R[2, 0])
    z = np.copysign(np.sqrt(max(0.0, 1 - R[0, 0] - R[1, 1] + R[2, 2])) / 2, R[1, 0] - R[0, 1])
    return w, x, y, z


model_id = 0
for shot in sorted(p for p in (ws / "images").iterdir() if p.is_dir() and p.name.startswith("shot")):
    frames = sorted(shot.glob("*.jpg"))
    # ponytail: fixed-size chunks per shot, no cross-chunk alignment; add overlap+Sim3 chaining if shots exceed one chunk
    for start in range(0, len(frames), chunk):
        part = frames[start:start + chunk]
        if len(part) < 3:
            continue
        imgs = load_and_preprocess_images([str(p) for p in part]).to(device)
        with torch.no_grad():
            pred = model(imgs)
        extri, intri = pose_encoding_to_extri_intri(pred["pose_enc"], imgs.shape[-2:])
        extri, intri = extri[0].cpu().numpy(), intri[0].cpu().numpy()  # world->camera (OpenCV), per frame
        txt = out_root / str(model_id) / "txt"
        txt.mkdir(parents=True, exist_ok=True)
        # Intrinsics are in the preprocessed image's pixels; scale focal back to the 1920-wide source.
        scale = 1920 / imgs.shape[-1]
        cams, ims = [], []
        for k, (p, E, K) in enumerate(zip(part, extri, intri)):
            cams.append(f"{k + 1} SIMPLE_PINHOLE 1920 1080 {K[0, 0] * scale} 960 540")
            q = rot_to_quat(E[:3, :3])
            ims.append(f"{k + 1} {q[0]} {q[1]} {q[2]} {q[3]} {E[0, 3]} {E[1, 3]} {E[2, 3]} {k + 1} {shot.name}/{p.name}\n\n")  # second line: no 2D points
        (txt / "cameras.txt").write_text("\n".join(cams) + "\n")
        (txt / "images.txt").write_text("".join(ims))
        (txt / "points3D.txt").write_text("")
        print(f"model {model_id}: {shot.name} frames {start}-{start + len(part) - 1}")
        model_id += 1
