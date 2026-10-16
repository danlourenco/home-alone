"""wall_scale: positions along one straight wall from a single perspective frame, without solving the camera.

For points on a straight wall, the vertical scale V(u) (px per metre of a known height at image column u) is linear in u, and the
position along the wall is s = K / V(u) + c, with K = f / sin(theta) fixed by the focal length (sin(theta) = f / hypot(f, u_vp - cx),
u_vp = alpha / beta where V vanishes). The result is insensitive to f when the wall is near frontal (228 s). Positions are
relative; one known point (a corner) or the room's length closes them.

Dining room rear wall (user, Oct 16: "the wall looks a bit wider between the two doors in marinas than ours, maybe by a foot"):
  uv run python tools/house/wall_scale.py
Readings (Marina Part 1, 1920 x 1080): casing tops are 2.10 m (80 in door + head casing), the wainscot cap is unknown and is solved
(it must come out at the house's measured 0.705 m for the scale to be trusted).
"""
import math

CX = 960


def fit(points):
    """points: [(u, V)] -> alpha, beta of V = alpha - beta u (least squares)."""
    n = len(points); mu = sum(p[0] for p in points) / n; mv = sum(p[1] for p in points) / n
    b = -sum((u - mu) * (v - mv) for u, v in points) / sum((u - mu) ** 2 for u, _ in points)
    return mv + b * mu, b


def positions(points, cols, f):
    a, b = fit(points)
    s_theta = f / math.hypot(f, a / b - CX)
    K = f / s_theta                           # s = K / V
    return {name: K / (a - b * u) for name, u in cols.items()}


# frame 228: left casing (u 850): top 75, floor 865 -> 2.10 m; cap at 600 -> solved height; right door casing tops over the cap
H = 2.10
V850 = (865 - 75) / H
cap = (865 - 600) / V850
V1520 = (595 - 115) / (H - cap); V1810 = (585 - 125) / (H - cap)
pts228 = [(850, V850), (1520, V1520), (1810, V1810)]
cols228 = {"left_door_far": 595, "left_door_near": 830, "right_door_near": 1550, "right_door_far": 1762}
# frame 226: left casing (u 300): top 25, floor 895; right casing (u 1150): top 128, cap 535; the sunroom-side corner at u 1240
V300 = (895 - 25) / H; cap226 = (895 - 595) / V300; V1150 = (535 - 128) / (H - cap226)
pts226 = [(300, V300), (1150, V1150)]
cols226 = {"left_door_near": 250, "right_door_far": 960, "right_door_near": 1120, "corner": 1240}

if __name__ == "__main__":
    print(f"228: wainscot cap {cap:.3f} m (house: 0.705); V fit residual at 1520: {V1520 - (fit(pts228)[0] - fit(pts228)[1] * 1520):+.1f} px/m")
    for f in (1200, 1663, 2400):
        p = positions(pts228, cols228, f)
        print(f"228 f {f}: right door {p['right_door_far'] - p['right_door_near']:.2f} m, wall between {p['right_door_near'] - p['left_door_near']:.2f} m, "
              f"left door (left edge occluded) {p['left_door_near'] - p['left_door_far']:.2f} m")
    print(f"226: wainscot cap {cap226:.3f} m")
    for f in (1200, 1663, 2400):
        p = positions(pts226, cols226, f)
        print(f"226 f {f}: corner to right door {p['corner'] - p['right_door_near']:.2f} m, right door {p['right_door_near'] - p['right_door_far']:.2f} m, "
              f"wall between {p['right_door_far'] - p['left_door_near']:.2f} m")
