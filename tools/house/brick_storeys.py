#!/usr/bin/env python3
"""Upper vs lower storey brick at walk0645 (front, from the piers), from perf_probe.sh tour images.

The APV leak (Oct 21): with probes on, the skin's upper storey read darker than the ground floor in every tile of
apv-tuning-sheet.jpg; with the APV off the two match. Gate: in every column the upper brick is within 5% of the lower
(luminance), and its R/G within 5% too.

    uv run -q --with pillow python -I tools/house/brick_storeys.py RUN_DIR [SUNNY OVERCAST NIGHT]
RUN_DIR is a tour of -perfposes walk0645 (1920x1080). The three tiles default to walk0645-day-A1 (base, sunny),
walk0645-day-B1 (weather=overcast as the first variant) and walk0645-night-A1. Exit 1 on any FAIL.
    ... brick_storeys.py --rooms BEFORE_RUN AFTER_RUN parents-day buzz-night ...   the rooms a front fix must not change (5%)
"""
import sys
from pathlib import Path
from statistics import median

from PIL import Image

# (x0, y0, x1, y1) in the 1920x1080 walk0645 frame: plain brick, clear of windows, shutters, lanterns and the portico.
# Read off spec/captures/views/front-0645 tiles; median per patch so snowflakes and branch shadows don't move it. Left of the
# portico the ground-floor brick is in the portico's shadow in sun, so the centre is read right of it. Film 6399 (overcast), same
# patches by eye: upper/lower lum 0.94 (wing), 1.10 (left of the porch), 0.99 (centre); R/G 0.96-1.04.
COLUMNS = {
    "wing L": ((582, 352, 595, 395), (580, 470, 594, 520)),
    "centre R": ((1045, 352, 1090, 395), (1072, 465, 1090, 520)),
}
TOL = 0.05


def patch(im, box):
    px = list(im.crop(box).get_flattened_data())
    r, g, b = (median(p[i] for p in px) for i in range(3))
    return r, g, b, 0.2126 * r + 0.7152 * g + 0.0722 * b


def check(path, label):
    im = Image.open(path).convert("RGB")
    assert im.size == (1920, 1080), f"{path}: {im.size}, want the 1920x1080 walk0645 tile"
    fails = 0
    for col, (up, lo) in COLUMNS.items():
        u, l = patch(im, up), patch(im, lo)
        lum, rg = u[3] / l[3], (u[0] / u[1]) / (l[0] / l[1])
        ok = abs(lum - 1) <= TOL and abs(rg - 1) <= TOL
        fails += not ok
        print(f"{'ok  ' if ok else 'FAIL'} {label:9s} {col:9s} upper/lower lum {lum:.3f} R/G {rg:.3f}"
              f"  (upper {u[0]:.0f}/{u[1]:.0f}/{u[2]:.0f}, lower {l[0]:.0f}/{l[1]:.0f}/{l[2]:.0f})")
    return fails


def rooms(before, after, poses):
    """--rooms BEFORE AFTER POSE...: mean brightness of each pose tile (POSE.png or POSE-A1.png), after vs before; FAIL past 5%.
    The upstairs rooms share probes with the front wall, so a front fix must leave them alone."""
    def tile(run, pose):
        for n in (f"{pose}.png", f"{pose}-A1.png"):
            if (run / n).exists():
                px = list(Image.open(run / n).convert("L").get_flattened_data()); return sum(px) / len(px)
        return None
    fails = 0
    for pose in poses:
        b, a = tile(before, pose), tile(after, pose)
        if b is None or a is None: print(f"skip {pose}: missing in {'before' if b is None else 'after'}"); continue
        ok = abs(a / b - 1) <= TOL; fails += not ok
        print(f"{'ok  ' if ok else 'FAIL'} room {pose:16s} mean {b:.1f} -> {a:.1f} ({(a / b - 1) * 100:+.1f}%)")
    print(f"brick_storeys rooms: {fails} FAIL")
    return 1 if fails else 0


def main(argv):
    if argv[1:2] == ["--rooms"]:
        return rooms(Path(argv[2]), Path(argv[3]), argv[4:])
    run = Path(argv[1])
    names = argv[2:5] or ["walk0645-day-A1", "walk0645-day-B1", "walk0645-night-A1"]
    fails = sum(check(run / f"{n}.png", lab) for n, lab in zip(names, ["sunny", "overcast", "night"]) if (run / f"{n}.png").exists())
    print(f"brick_storeys: {fails} FAIL ({run.name})")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
