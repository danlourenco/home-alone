#!/usr/bin/env python3
"""window_glow: do the front windows read as lit rooms at night, as in film 5545? (user, Oct 21: "shouldn't the lights upstairs
appear on from the outside at night?")

Per window: mean luminance (Rec.709 luma of the sRGB pixels) and R/B, over the window's pane less a 20% border (the bulb loops and
casings stay out). Film: boxes picked by eye on film 5545 (gridded, Oct 21). Ours: the windows' rectangles (spec/exterior_shell.json
upper_windows and dormers, spec/house_spec.ground.json front openings) projected with the front6399 pose (PerfProbe: Unity camera at
(26.078, -2.6, -19.421), yaw 292.7, pitch -9.39, vertical FOV 60 at 1920x1080).
The two frames have different cameras and exposures, so each window is judged against the film's own house: lum relative to the
brightest ground-floor window of the same frame (film: the left bay), and R/B. Gate: every window lit (lum ratio >= 0.5 x the film's
ratio for that window class) and warm (R/B >= 0.8 x the film's class median). Exit 1 on any FAIL.

    uv run -q --with numpy --with pillow python -I tools/house/window_glow.py RUN/front6399-night-A1.png
"""
import json, math, sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
FILM = ROOT / "0-homealone/full/homealone-movie-screencaps.com-5545.jpg"
# film 5545 (1920x1058) pane boxes, left to right (picked on a 0.9x gridded copy)
FILM_BOX = {
    "upper": [(240, 350, 430, 440), (565, 335, 620, 420), (737, 335, 792, 420), (980, 335, 1036, 420), (1225, 335, 1280, 420), (1405, 335, 1458, 420), (1622, 340, 1785, 430)],
    "dormer": [(748, 140, 792, 210), (1220, 140, 1270, 210)],
    "ground": [(235, 565, 435, 685), (555, 560, 625, 685), (728, 560, 800, 685), (1220, 560, 1290, 685), (1398, 560, 1468, 685), (1615, 560, 1785, 685)],
}
POSE = dict(pos=(26.078, -2.6, -19.421), yaw=292.7, pitch=-9.39, vfov=60.0, w=1920, h=1080)


def luma(a):
    return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]


def stats(img, box, shrink=0.2):
    x0, y0, x1, y1 = box; dx, dy = (x1 - x0) * shrink / 2, (y1 - y0) * shrink / 2
    p = img[int(y0 + dy):int(y1 - dy), int(x0 + dx):int(x1 - dx)].reshape(-1, 3)
    if len(p) == 0: return None
    m = np.median(p, axis=0); return float(luma(m)), float(m[0] / max(m[2], 1.0))


def project(X):
    px, py, pz = POSE["pos"]; yw, pt = math.radians(POSE["yaw"]), math.radians(POSE["pitch"])
    f = (POSE["h"] / 2) / math.tan(math.radians(POSE["vfov"]) / 2)
    fw = (math.sin(yw) * math.cos(pt), -math.sin(pt), math.cos(yw) * math.cos(pt))
    rt = (math.cos(yw), 0.0, -math.sin(yw))
    up = (math.sin(yw) * math.sin(pt), math.cos(pt), math.cos(yw) * math.sin(pt))
    v = (X[0] - px, X[1] - py, X[2] - pz); dot = lambda a, b: sum(i * j for i, j in zip(a, b))
    z = dot(v, fw); return POSE["w"] / 2 + f * dot(v, rt) / z, POSE["h"] / 2 - f * dot(v, up) / z


def rect(x, a0, a1, y0, y1):
    pts = [project((x, y, -a)) for a in (a0, a1) for y in (y0, y1)]
    return (min(p[0] for p in pts), min(p[1] for p in pts), max(p[0] for p in pts), max(p[1] for p in pts))


def our_boxes():
    s = json.loads((ROOT / "spec/exterior_shell.json").read_text()); g = json.loads((ROOT / "spec/house_spec.ground.json").read_text())
    gy = s["ground_floor"]
    up = [w for w in s["upper_windows"] if w["face"] in ("front", "den_front", "right_front")]
    upper = [rect(w["d"] + 0.02, w["a0"], w["a1"], w["y0"], w["y1"]) for w in up]
    dorm = [rect(d["face"], d["z"] - 0.31, d["z"] + 0.31, d["sill"], d["head"]) for d in s["dormers"] if d["face"] > 5]
    gr = [w for w in g["windows"] if w["wall_axis"] == "x" and w["wall_coord_spec"] > 9 and "sidelight" not in w["name"]]
    ground = [rect(max(w["wall_coord_spec"], s["front_main"] if w["wall_coord_spec"] > 9.9 else w["wall_coord_spec"]) + 0.02, w["span_spec"][0], w["span_spec"][1], gy + w["sill_m"], gy + w["head_m"]) for w in gr]
    ground += [rect(b["d"] + 0.02, b["a0"], b["a1"], b["y0"], b["y1"]) for b in s["blind"] if b["face"] == "right_front_ground"]
    key = lambda b: (b[0] + b[2]) / 2
    return {"upper": sorted(upper, key=key), "dormer": sorted(dorm, key=key), "ground": sorted(ground, key=key)}


def measure(img, boxes):
    out = {k: [stats(img, b) for b in v] for k, v in boxes.items()}
    ref = max(v[0] for v in out["ground"] if v)   # the brightest ground-floor window: the frame's own ruler
    return out, ref


def main(argv):
    film = np.asarray(Image.open(FILM).convert("RGB")).astype(float)
    ours = np.asarray(Image.open(argv[1]).convert("RGB")).astype(float)
    fm, fref = measure(film, FILM_BOX); om, oref = measure(ours, our_boxes())
    fails = 0
    for k in ("upper", "dormer", "ground"):
        fl = [v[0] / fref for v in fm[k] if v]; frb = sorted(v[1] for v in fm[k] if v)
        fl_med, frb_med = sorted(fl)[len(fl) // 2], frb[len(frb) // 2]
        print(f"film {k:6s}: lum/ref median {fl_med:.2f}, R/B median {frb_med:.2f}  ({len(fl)} windows)")
        for i, v in enumerate(om[k]):
            if v is None: print(f"  skip ours {k} {i}: off frame"); continue
            lr, rb = v[0] / oref, v[1]
            ok = lr >= 0.5 * fl_med and rb >= 0.8 * frb_med; fails += not ok
            print(f"  {'ok  ' if ok else 'FAIL'} ours {k} {i}: lum {v[0]:.0f} (/ref {lr:.2f}) R/B {rb:.2f}")
    print(f"window_glow: {fails} FAIL (ref: film {fref:.0f}, ours {oref:.0f})")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
