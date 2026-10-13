"""Top-down: true camera path (grey) vs each model's Sim3-aligned estimate (colour = shot).
usage: uv run --with numpy --with matplotlib python -I tools/sfm/synthetic_plot.py <ws> <out.png>"""
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.argv, (ws, out) = sys.argv[:1], (Path(sys.argv[1]), sys.argv[2])
from synthetic_score_lib import load_model, umeyama  # noqa: E402

gt = json.loads((ws / "gt.json").read_text())["frames"]
models = sorted(p for p in (ws / "sparse").iterdir() if p.is_dir())
fig, axes = plt.subplots(1, len(models), figsize=(6 * len(models), 6), squeeze=False)
truth_xz = np.array([[f["pos"][0], -f["pos"][2]] for f in gt])
for ax, model in zip(axes[0], models):
    est, true, shots = load_model(ws, model)
    ax.plot(truth_xz[:, 0], truth_xz[:, 1], color="0.8", lw=4, label="true path")
    if len(est) >= 3:
        s, R, t = umeyama(est, true)
        a = (s * (R @ est.T)).T + t
        sc = ax.scatter(a[:, 0], a[:, 2], c=shots, cmap="tab10", vmin=0, vmax=9, s=14, label="estimate (colour=shot)")
        for e, tr in zip(a, true):
            ax.plot([e[0], tr[0]], [e[2], tr[2]], color="r", lw=0.4, alpha=0.5)
    ax.set_title(f"model {model.name}: {len(est)} frames, shots {sorted(set(shots))}")
    ax.set_aspect("equal"); ax.legend(loc="lower left", fontsize=8)
fig.savefig(out, dpi=90, bbox_inches="tight")
