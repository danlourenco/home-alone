"""Real-house storey height from brick courses: an absolute ruler that shares nothing with doors, Marina or our model.
Photo: Famartin 2015-05-11, art/home_alone/references/neighborhood/house.jpg (3264x2448), front wall left of the porch.
The course period is measured by FFT on a plain brick strip; edges were read on a 3x gridded crop of the window column
(the left French door pair and the upstairs window above it).
usage: uv run --with numpy --with pillow python -I tools/house/brick_courses.py
"""
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
COURSE_IN = (2.5, 2.75)          # 1920s brick plus joint per course; modular is 2.667 (3 courses = 8 in)
EDGES = {"up_head": 985, "up_sill": 1107, "door_head": 1212, "door_foot": 1382}   # px, read +-4
UP_HEAD_IN = (80, 90)            # upstairs window head above its floor: at a door head (80) up to just under a ceiling


def course_px():
    im = np.asarray(Image.open(ROOT / "art/home_alone/references/neighborhood/house.jpg").convert("L"), float)
    out = []
    for ya, yb in ((997, 1160), (1160, 1322)):                    # upper and lower half of the strip (keystone check)
        pr = im[ya:yb, 1264:1326].mean(1)
        pr -= np.convolve(pr, np.ones(15) / 15, "same")
        F = np.abs(np.fft.rfft(pr * np.hanning(len(pr)), 8192)); fr = np.fft.rfftfreq(8192)
        m = (fr > 1 / 12) & (fr < 1 / 3)
        out.append(1 / fr[m][F[m].argmax()])
    return out


def main():
    per = course_px()
    p = sum(per) / 2
    door = (EDGES["door_foot"] - EDGES["door_head"]) / p
    span = (EDGES["door_foot"] - EDGES["up_head"]) / p             # ground floor to upstairs window head, in courses
    print(f"course period {per[0]:.2f} / {per[1]:.2f} px (upper / lower half)")
    print(f"French door: {door:.1f} courses = {door * COURSE_IN[0]:.0f}-{door * COURSE_IN[1]:.0f} in")
    f2f = [span * c - h for c in COURSE_IN for h in UP_HEAD_IN]
    print(f"ground floor to upstairs window head: {span:.1f} courses = {span * COURSE_IN[0]:.0f}-{span * COURSE_IN[1]:.0f} in")
    print(f"floor-to-floor: {min(f2f):.0f}-{max(f2f):.0f} in ({min(f2f) * 0.0254:.2f}-{max(f2f) * 0.0254:.2f} m)")
    return door, f2f


if __name__ == "__main__":
    door, f2f = main()
    assert 76 <= door * 2.667 <= 84, "the French doors no longer read as standard doors; recheck the course period"
    assert max(f2f) < 120, "floor-to-floor reads over 10 ft; 10 ft ceilings would need about 132 in"
