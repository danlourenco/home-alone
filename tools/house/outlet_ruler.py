"""Main-stair riser height from an outlet cover plate on the stair's side wall: a ruler with no door in it.
Frame: Marina Part 1 at 198 s (`ffmpeg -ss 198 -i "Tour the Home Alone House_ Part 1, Main Floor [CG Tour] copy.mp4" -frames:v 1`).
The stair's side wall is nearly face-on; the plate sits on that wall below the treads near x 270. Reads in px at 1920x1080
on a 3x gridded crop. The wall's right side is nearer the camera, so the riser spacing grows left to right; the local value
at the plate's x is taken from the two treads that bracket it.
usage: uv run python -I tools/house/outlet_ruler.py
"""
PLATE_PX = (852.7, 900.7)                 # top, bottom of the plate
PLATE_W_PX = 30.0
PLATES_IN = {"standard 2.75 x 4.5": (2.75, 4.5), "midway 3.13 x 4.88": (3.13, 4.88)}
RISER_PX = (70, 76)                       # local riser spacing at the plate's x (treads at x 95-220 and 200-330: 71 and 76)
DOOR_SCALED_RISE_IN = 0.169 / 0.0254      # measurements/rooms/stairs.json, closet door at 80 in


def main():
    h = PLATE_PX[1] - PLATE_PX[0]
    print(f"plate {PLATE_W_PX:.0f} x {h:.0f} px, aspect {PLATE_W_PX / h:.3f}")
    out = {}
    for name, (w, ph) in PLATES_IN.items():
        lo, hi = RISER_PX[0] / h * ph, RISER_PX[1] / h * ph
        out[name] = (lo, hi)
        print(f"  if {name} in (aspect {w / ph:.3f}): riser {lo:.1f}-{hi:.1f} in")
    print(f"door-scaled riser (closet door = 80 in): {DOOR_SCALED_RISE_IN:.2f} in")
    lo, hi = out["standard 2.75 x 4.5"]
    print(f"closet door implied by a standard plate: {80 * lo / DOOR_SCALED_RISE_IN:.0f}-{80 * hi / DOOR_SCALED_RISE_IN:.0f} in")
    return out


if __name__ == "__main__":
    out = main()
    assert all(5.5 < lo < hi < 8.5 for lo, hi in out.values()), "a riser outside 5.5-8.5 in: re-read the plate or the treads"
