"""Ground-floor ceiling height from Marina's Part 1 frames: at a door jamb in the wall plane, the ceiling line, the door
head and the floor are read in one image column, and the ceiling = door height x (floor - ceiling) / (floor - head).
Verticals are image-vertical in both frames (level camera), so the column is a straight vertical scale.
Two rooms, two frames; neither uses the stair clips that gave the old 2.32 m (that line was the landing balustrade's base).
usage: uv run --with numpy python -I tools/house/ground_ceiling.py
"""
IN = 0.0254
READS = {   # room: (frame, column x, floor y, head y, ceiling y), px at 1920x1080, read on 2-3x gridded crops
    "living room (French door to the foyer, hinge jamb)": ("1175 s", 1410, 815, 207, 85),
    "dining room (French doors to the foyer, near jamb)": ("1125 s", 457, 1000, 177, 18),
}
PICK = 4          # px read spread on each line
DOOR_IN = (78, 80)  # door height range used across the house (spec scale note)


def main():
    out = []
    for room, (frame, x, f, h, c) in READS.items():
        vals = [d * IN * (f - c + s1) / (f - h + s2) for d in DOOR_IN for s1 in (-2 * PICK, 2 * PICK) for s2 in (-PICK, PICK)]
        mid = 80 * IN * (f - c) / (f - h)
        out.append(mid)
        print(f"{room:<52} {frame}: {mid:.2f} m at 80 in (spread {min(vals):.2f}-{max(vals):.2f})")
    print(f"ground ceiling: {sum(out) / len(out):.2f} m (the two rooms agree within {abs(out[0] - out[1]) * 100:.0f} cm); "
          f"8 ft = {96 * IN:.3f} m is the value built")
    return out


if __name__ == "__main__":
    a, b = main()
    assert abs(a - b) < 0.05, "the two rooms disagree; do not use one number for the floor"
    assert all(abs(v - 96 * IN) < 0.05 for v in (a, b)), "8 ft no longer fits the measurements; revisit the ground ceiling"
