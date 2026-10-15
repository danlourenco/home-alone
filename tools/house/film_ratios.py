"""Scale-free height ratios from film frames: a ceiling as a multiple of a door (or wainscot) read in ONE wall plane, so no
camera model and no ruler size are needed. Turning a ratio into feet still needs a ruler (a door height, an actor); the
rulers are listed separately, each with its own assumption, so the gate can tell them apart.

Reads are px on gridded full-resolution crops, +-8 px each. Ceilings are read to the PLANE (top of the crown), with the
crown's lower edge alongside.
usage: uv run python -I tools/house/film_ratios.py
"""
PICK = 8
# frame: [(what, floor y, line y, ref y, ref name, plane)]: ratio = (floor - line) / (floor - ref) in that plane
READS = {
    "IMG_4261 upstairs hall (Kevin, user still)": [
        ("ceiling plane / end-wall wainscot", 2520, 311, 1836, "wainscot", "arch wall (left pier, x~1750)"),
        ("door leaf top / end-wall wainscot", 2304, 870, 1800, "wainscot", "end wall (door beyond the arch)"),
    ],
    "then-foyer.png foyer (film, user still)": [
        ("crown on the right wall / right-wall door head", 630, 125, 270, "door", "right wall at x~1120"),
        ("landing underside (NOT the ceiling) / rear door head", 615, 270, 322, "door", "rear wall"),
    ],
    "entry205.jpg foyer (Marina, Part 1 3:25)": [
        ("ceiling plane / vestibule opening head", 752, 33, 275, "opening", "front wall"),
    ],
}
RULERS = {   # each a separate assumption; none is evidence alone
    "door-80in": 80, "door-84in": 84, "door-96in": 96,
}


def ratio(f, line, ref, s1=0, s2=0):
    return (f - line + s1) / (f - ref + s2)


def main():
    out = {}
    for frame, reads in READS.items():
        print(frame)
        for what, f, line, ref, rname, plane in reads:
            r = ratio(f, line, ref)
            lo = min(ratio(f, line, ref, a, b) for a in (-2 * PICK, 2 * PICK) for b in (-PICK, PICK))
            hi = max(ratio(f, line, ref, a, b) for a in (-2 * PICK, 2 * PICK) for b in (-PICK, PICK))
            out[(frame, what)] = r
            feet = "  ".join(f"{k}: {r * v / 12:.1f} ft" for k, v in RULERS.items()) if rname == "door" else ""
            print(f"  {what:<55} {r:.3f} ({lo:.3f}-{hi:.3f})  [{plane}]  {feet}")
    hall = out[("IMG_4261 upstairs hall (Kevin, user still)", "ceiling plane / end-wall wainscot")] / \
        out[("IMG_4261 upstairs hall (Kevin, user still)", "door leaf top / end-wall wainscot")]
    print(f"upstairs hall: ceiling plane = {hall:.2f} x the end door (if the two wainscot caps match); "
          + "  ".join(f"{k}: {hall * v / 12:.1f} ft" for k, v in RULERS.items()))
    return out, hall


if __name__ == "__main__":
    out, hall = main()
    assert 1.0 < hall < 1.6, "hall ceiling/door ratio outside any plausible house: re-read"
