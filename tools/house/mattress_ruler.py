"""Buzz's room, headboard (door) wall length, using the twin mattress as the ruler. Shares no data, scale or upstream
with the Buzz SfM (vggt:real-vggt-buzzall, door-80in:buzz-clip) or the overhead trace.

Frame: Marina Part 2 at 563.0 s (`ffmpeg -ss 563.0 -i "Tour the Home Alone House_ Part 2  [CG Tour].mp4" -frames:v 1`),
the door wall almost face-on, from the shelves-wall corner to the front-window corner, the bed head against it.
The headboard posts stand at the wall; the gap between them holds the mattress: twin 39 in, plus up to 1 in of play.
Lengths along a horizontal line on a plane are measured projectively: with the line's vanishing point v (image x), the
true position is affine in 1/(v - x). Verticals in this frame are image-vertical (door casings), so each pick projects
straight up or down onto the reference line.
Picks were read on 3x gridded crops (scratch); each carries the spread used below.
usage: uv run --with numpy python -I tools/house/mattress_ruler.py
"""
import itertools

import numpy as np

# image x of the picks (px), each with a +- read spread
CORNER_L = (195, 5)       # shelves wall | door wall (crown turn and the vertical corner edge at the floor)
CORNER_R = (1452, 3)      # door wall | front-window wall (crown corner)
POST_L = (817, 3)         # left headboard post, inner face
POST_R = (1152, 3)        # right headboard post, inner face
# Two wall-plane lines (x, y) pairs: bottom of the crown and the floor junction (baseboard foot)
CROWN = [(210, 38), (395, 48), (1350, 110), (1440, 115)]
FLOOR = [(300, 940), (600, 922)]
GAP_M = (0.9906, 1.0160)  # 39 in mattress .. 40 in with play


def vp(a, b):
    """x where two fitted lines meet."""
    (m1, c1), (m2, c2) = (np.polyfit(*np.array(p).T, 1) for p in (a, b))
    return (c2 - c1) / (m1 - m2)


def length(xl, xr, p1, p2, v, gap):
    f = lambda x: 1.0 / (v - x)
    return gap * (f(xr) - f(xl)) / (f(p2) - f(p1))


def main():
    v = vp(CROWN, FLOOR)
    out = []
    for dl, dr, d1, d2 in itertools.product((-1, 1), repeat=4):
        for vv in (v * 0.7, v, v * 1.5, 1e9):            # the vanishing point is the weakest pick: 0.7x .. infinity
            for gap in GAP_M:
                out.append(length(CORNER_L[0] + dl * CORNER_L[1], CORNER_R[0] + dr * CORNER_R[1],
                                  POST_L[0] + d1 * POST_L[1], POST_R[0] + d2 * POST_R[1], vv, gap))
    best = length(CORNER_L[0], CORNER_R[0], POST_L[0], POST_R[0], v, 0.9906)
    lo, hi = min(out), max(out)
    print(f"vanishing point x = {v:.0f} px")
    print(f"door wall (shelves corner to front-window corner): {best:.2f} m at 39 in; spread {lo:.2f} .. {hi:.2f} m")
    for name, val in (("Marina overhead trace", 3.63), ("grey-box (built)", 3.68), ("Buzz SfM", 3.49),
                      ("September model", 3.24)):
        print(f"  {name:<22}{val:5.2f} m  {'inside' if lo <= val <= hi else 'OUTSIDE'} the spread")
    return lo, hi


def selftest():
    """Synthetic wall: a 3.60 m wall and a 0.99 m gap seen by a pinhole camera turned 15 deg; recover 3.60."""
    f, yaw = 1200.0, np.radians(15)
    X = np.array([0.0, 3.60, 1.30, 1.30 + 0.99])          # corners, posts along the wall
    P = np.stack([X * np.cos(yaw) - 1.8, X * np.sin(yaw) + 4.0])  # camera coords: lateral, depth
    x = f * P[0] / P[1]
    v = f * np.cos(yaw) / np.sin(yaw)                       # image of the wall direction at infinity
    got = length(x[0], x[1], x[2], x[3], v, 0.99)
    assert abs(got - 3.60) < 1e-6, got
    print("selftest ok: recovered 3.60 m on a synthetic wall turned 15 deg")


if __name__ == "__main__":
    selftest()
    main()
