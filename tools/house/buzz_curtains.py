"""buzz_curtains: Buzz's green drapes measured in Marina's solved Buzz clip (the 45 cameras of tools/house/buzz_layout.py).

Buzz TRIAL 2 (decoration, change-gate decoration rule). Marina 540-562 s: on every window a brass rod over the casing and two
pleated panels hanging straight (not tied back) to the stool (hers dark green); the film (528, 530) shows them neutral grey over a
white sheer (colour and sheer: hifi_buzz_curtains.py). This file measures the GEOMETRY only. Picks are on the FULL 1920 x 1080 frames (sfm-work/buzz1/full/<i>.jpg; gridded crops in
spec/captures/picks/buzz2/), the front wall's hall-side window (built z 12.48-13.20):
  * hem corners (outer and inner edge of each panel at the hem), frames 20 and 27: each ray cut with a plane parallel to the
    front wall at the panels' depth, per frame (the spread between the two frames is printed). Depth AUTHORED 0.09 m (a 3.5 in
    rod bracket): triangulating the corners gave -0.17..+0.01 m (rays nearly parallel in depth; the clip's wall points also sit
    0.1-0.2 m behind the wall plane, buzz_layout.py), so depth is not measurable here; heights and widths barely depend on it
  * the rod: frame 27 only (the clip never shows it twice), cut with the same plane
Everything is in the built room's frame (buzz_layout.Frame, origin the door|front corner) at the twin-mattress ruler; the window
is then expressed RELATIVE TO ITS CASING (overhang past the casing, rod above the head, hem below the stool), so it carries over
to the built windows, which stand where the plan puts them (DEVIATIONS 24: the front windows' width assumed the desk window's).

  uv run --with numpy --with scipy --with pillow python -I tools/house/buzz_curtains.py   -> spec/dressing/buzz_curtains.json
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import buzz_layout as bl   # noqa: E402

ROOT = bl.ROOT
F = bl.F
# full-frame picks (u, v) -> 518 grid
PICKS = {
    "hemL_out": {20: F(288, 688), 27: F(1022, 699)},    # left panel, outer (door-corner side) edge at the hem
    "hemL_in":  {20: F(470, 688), 27: F(1158, 700)},    # left panel, inner edge at the hem
    "hemR_in":  {20: F(733, 678), 27: F(1338, 737)},    # right panel, inner edge at the hem
    "hemR_out": {20: F(898, 676), 27: F(1500, 753)},    # right panel, outer (chest side) edge at the hem
}
DEPTH = 0.09                                            # AUTHORED (see above)
ROD = {27: [F(1025, 28), F(1150, 6)]}                   # rod centre line near its left finial and 0.12 m further right


def main():
    cams, world, conf = bl.load()
    pl = bl.planes(world, conf, cams)
    R = bl.rulers(cams, pl)
    fr = bl.Frame(pl, R["mattress"][0])
    out, sp = {}, {}
    d = DEPTH
    n, c = pl["front"]; c = c + n * d / fr.s
    each = {}
    for k, obs in PICKS.items():
        E = np.array([fr.spec(bl.cut(cams[i], u, v, n, c))[0] for i, (u, v) in obs.items()])
        sp[k] = E.mean(0); each[k] = E
        print(f"  {k:9s} spec {np.round(sp[k], 3)}  frames 20/27 spread y {np.ptp(E[:, 1]) * 100:.1f} z {np.ptp(E[:, 2]) * 100:.1f} cm")
    rod = [fr.spec(bl.cut(cams[i], u, v, n, c))[0] for i, uv in ROD.items() for u, v in uv]
    rod_y = float(np.mean([p[1] for p in rod]))
    print(f"  rod (frame 27, cut at the panels' depth {d:.3f} m): y {[round(p[1], 3) for p in rod]}")
    # the window in the same frame: the built casing is where the plan puts it; Marina's casing from the same solve: the hem's
    # panels hang symmetric about the window, so its centre is the mid point of the two outer edges
    zc = (sp["hemL_out"][2] + sp["hemR_out"][2]) / 2
    W = sp["hemR_out"][2] - sp["hemL_out"][2]
    wL = sp["hemL_in"][2] - sp["hemL_out"][2]; wR = sp["hemR_out"][2] - sp["hemR_in"][2]
    hem = float(np.mean([sp[k][1] for k in PICKS]))
    win = next(o for o in json.loads((ROOT / "spec/openings.json").read_text())["openings"] if o["id"] == "upstairs:window:buzz_room:12.480")
    lo, hi, head, sill = win["lo"], win["hi"], win["head"], win["sill"]
    print(f"  Marina: panels' outer edges {W:.3f} m apart, centred at z {zc:.3f} (built window centre {(lo + hi) / 2:.3f}, clear {hi - lo:.3f});"
          f" panel widths at the hem {wL:.3f} / {wR:.3f}; hem y {hem:.3f}; rod y {rod_y:.3f}; depth {d:.3f}")
    casing = 0.07
    out = {
        "note": "Buzz's drapes (decoration; tools/house/buzz_curtains.py). Measured in Marina's solved Buzz clip at the twin-mattress ruler, "
                "relative to the window's casing so it applies to all three built windows (Marina dresses all three alike). Built by "
                "tools/house/hifi_sheers.py (the Buzz section).",
        "overhang_m": round((W - (hi - lo) - 2 * casing) / 2, 3),          # past the casing's outer edge, each side
        "panel_w_hem_m": round((wL + wR) / 2, 3),
        "hem_below_stool_m": round(sill - hem, 3),
        "rod_above_head_m": round(rod_y - head, 3),
        "panel_depth_m": d, "panel_depth_source": "AUTHORED 0.09 (not measurable in this clip)",
        "measured": {k: [round(float(v), 3) for v in p] for k, p in sp.items()},
        "rod_y": round(rod_y, 3), "hem_y": round(hem, 3),
        "spread": {"panel_w_L_vs_R": round(abs(wL - wR), 3), "hem_y_corners": round(float(np.ptp([sp[k][1] for k in PICKS])), 3),
                   "frames_20_27_max_cm": round(float(max(np.ptp(E, 0).max() for E in each.values())) * 100, 1)},
        "colour_source": "FILM 528/530 (lamp-lit): neutral grey panels over a white sheer (panel / white paper chroma 0.98/1.03/1.00); Marina's are dark green without a sheer (lit folds / white stool linear ~0.07/0.11/0.06): film first where they differ (hifi_buzz_curtains.py)",
    }
    (ROOT / "spec/dressing/buzz_curtains.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k not in ("note", "measured")}, indent=1))


if __name__ == "__main__":
    main()
