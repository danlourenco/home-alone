"""Horizontal section of the intact GLB (art/home_alone/references/glb-audit/triangles.npz) in metres.
Scale: ground-floor door leaf object2937 is 2.625 x 0.989 native units = an 80 x 30 in door -> 0.774 m/unit.
usage: uv run --with numpy --with matplotlib python tools/survey/glb_section.py <native_height> <out.png>
"""
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

M_PER_UNIT = 2.032 / 2.625
T = np.load(Path(__file__).resolve().parents[2] / "art/home_alone/references/glb-audit/triangles.npz")["triangles"]


def section(h):
    z = T[:, :, 2] - h
    segs = []
    for tri, s in zip(T, z):
        pts = []
        for i, j in ((0, 1), (1, 2), (2, 0)):
            if (s[i] > 0) != (s[j] > 0):
                t = s[i] / (s[i] - s[j]); pts.append(tri[i, :2] + t * (tri[j, :2] - tri[i, :2]))
        if len(pts) == 2:
            segs.append(pts)
    return np.array(segs) * M_PER_UNIT


if __name__ == "__main__":
    S = section(float(sys.argv[1]))
    S = S[(np.abs(S[..., 0]) < 14).all(1) & (S[..., 1] > -4).all(1) & (S[..., 1] < 16).all(1)]   # the house, not the site
    fig, ax = plt.subplots(figsize=(16, 16))
    for a, b in S:
        ax.plot([a[0], b[0]], [a[1], b[1]], "k-", lw=0.6)
    ax.set_aspect("equal"); ax.grid(True, lw=0.3); ax.set_xticks(np.arange(np.floor(S[..., 0].min()), S[..., 0].max() + 1, 1))
    ax.set_yticks(np.arange(np.floor(S[..., 1].min()), S[..., 1].max() + 1, 1))
    ax.set_title(f"intact GLB section at native z={sys.argv[1]} (metres at 0.774 m/unit)")
    plt.savefig(sys.argv[2], dpi=70)
