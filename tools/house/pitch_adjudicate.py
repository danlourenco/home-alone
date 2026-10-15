"""Stair pitch adjudication (Oct 15 review, item 4): the 35.0 deg vanishing-point read (stair_pitch.py, climb frames
116-120 = Part 1 334-335 s) vs the 31-33 deg step-spacing fits (foyer_length.py). In ONE frame (334 s) both lines are read
with the same camera across a focal sweep: the skirting/handrail line (its VP from LSD segments) and the nosing line
(7 wall-side tread-nosing corners, equally spaced at the 0.178 m rise). If they differ at every focal, the two lines are
not parallel in Marina's model, and the walking surface follows the nosings.
usage: uv run --with numpy --with scipy python -I tools/house/pitch_adjudicate.py
"""
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import foyer_length as F  # noqa: E402

ALONG, VERT = (2803.02, 453.89), (951.13, 26179.7)        # 334 s: wall-horizontal and vertical VPs (LSD + RANSAC)
SKIRT = np.array([3358.55, -1607.18])                     # 334 s: skirting + handrail VP (6 segments, 2050 px)
NOSINGS = [(912.5, 947.5), (1020, 835), (1125, 731.5), (1219, 636), (1302.5, 551), (1379, 475), (1448.5, 405)]
COLMAP_F = 1432.5                                         # sfm-work/rooms/stairs colmap camera (one camera, this clip)


def read(f):
    cam = F.camera(v0=(0, 0), v1=ALONG, vv=VERT, f=f)
    s = F.fit_line(cam, NOSINGS, range(len(NOSINGS)), 1)
    d = np.array([SKIRT[0] - 960, SKIRT[1] - 540, f]); d /= np.linalg.norm(d)
    return np.degrees(np.arctan(F.R / s["going"])), s["going"], s["rms"], np.degrees(np.arcsin(abs(d @ cam[3])))


def main():
    out = {}
    for f in (1300, COLMAP_F, 1500, 1600, 1700):
        n, g, rms, sk = read(f); out[f] = (n, g, sk)
        print(f"f {f:.0f}: nosing line {n:.1f} deg (going {g:.3f} m, rms {rms:.1f} px)   skirting/handrail {sk:.1f} deg   difference {sk - n:.1f}")
    a = F.frame_203()[1]["free"]
    print(f"203 s (focal from two VPs, 1308): nosing-line going {a['going']:.3f} m, pitch {np.degrees(np.arctan(F.R / a['going'])):.1f} deg")
    return out, a


if __name__ == "__main__":
    out, a = main()
    assert all(2.0 < sk - n < 4.0 for n, g, sk in out.values()), "skirting no longer steeper than the nosings at every focal"
    assert abs(out[COLMAP_F][1] - a["going"]) < 0.01, "the two frames' nosing-line goings disagree"
