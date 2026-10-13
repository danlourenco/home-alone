"""Does agreement between two reconstruction methods predict that both are correct?
Splits each shot into windows of consecutive frames; per window and method pair: Sim3-align one method to
the other (disagreement) and each to truth (error), both as median residual / window path length.
usage: PYTHONPATH=tools/sfm uv run --with numpy python tools/sfm/agreement.py <gate_pct> <name>=<ws> ...
"""
import itertools
import sys
from pathlib import Path

import numpy as np

from synthetic_score_lib import load_model, umeyama

gate = float(sys.argv[1]) / 100
methods = dict(a.split("=", 1) for a in sys.argv[2:])
WINDOW = 10

# frame name -> (method -> (model id, estimated centre)); truth and shot per frame.
est, truth, shot_of = {}, {}, {}
for m, ws in methods.items():
    for model in sorted(p for p in (Path(ws) / "sparse").iterdir() if p.is_dir()):
        e, t, shots, names = load_model(ws, model, with_names=True)
        for n, ec, tc, s in zip(names, e, t, shots):
            est.setdefault(n, {})[m] = (model.name, ec)
            truth[n], shot_of[n] = tc, s


def rel_residual(src, dst):
    s, R, t = umeyama(src, dst)
    r = np.linalg.norm((s * (R @ src.T)).T + t - dst, axis=1)
    return np.median(r) / max(np.linalg.norm(np.diff(dst, axis=0), axis=1).sum(), 1e-6)


rows = []
for shot in sorted(set(shot_of.values())):
    frames = sorted(n for n in truth if shot_of[n] == shot)
    for w in range(0, len(frames) - WINDOW + 1, WINDOW):
        win = frames[w:w + WINDOW]
        for a, b in itertools.combinations(methods, 2):
            # Use each method's dominant model in the window; frames must be in both.
            pick = {}
            for m in (a, b):
                ids = [est[n][m][0] for n in win if m in est[n]]
                pick[m] = max(set(ids), key=ids.count) if ids else None
            common = [n for n in win if all(m in est[n] and est[n][m][0] == pick[m] for m in (a, b))]
            if len(common) < 6:
                continue
            A = np.array([est[n][a][1] for n in common]); B = np.array([est[n][b][1] for n in common])
            T = np.array([truth[n] for n in common])
            rows.append((shot, w, a, b, rel_residual(B, A), rel_residual(A, T), rel_residual(B, T)))

print(f"{'shot':>4} {'win':>4} {'pair':<18} {'disagree':>8} {'errA':>7} {'errB':>7}")
for shot, w, a, b, d, ea, eb in rows:
    print(f"{shot:>4} {w:>4} {a + '/' + b:<18} {d:8.1%} {ea:7.1%} {eb:7.1%}{'  <- AGREE' if d < gate else ''}")
d = np.array([r[4] for r in rows]); worst = np.array([max(r[5], r[6]) for r in rows])
acc = d < gate
print(f"\nwindows compared: {len(rows)}; gate: disagreement < {gate:.0%}")
print(f"accepted {acc.sum()}: both methods truly within {gate:.0%} in {(worst[acc] < gate).sum()}, "
      f"worst true error among accepted {worst[acc].max() if acc.any() else float('nan'):.1%}")
print(f"rejected {(~acc).sum()}: of which actually fine (both within gate) {(worst[~acc] < gate).sum()}")
rank = lambda x: np.argsort(np.argsort(x))
print(f"Spearman(disagreement, worse true error) = {np.corrcoef(rank(d), rank(worst))[0, 1]:.2f}")
