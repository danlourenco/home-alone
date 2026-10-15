"""Scale-free height ratios from film frames: a ceiling as a multiple of a door (or wainscot) read on ONE vertical line.
Oct 15 (review item 3): being in one wall plane does NOT preserve length ratios under perspective. Each read is now the
cross-ratio (floor, ref, line, vertical vanishing point) on that vertical line, with the VP detected in the image itself
(LSD + RANSAC, tools/sfm/stair_pitch.py); the plain pixel ratio is printed beside it. Stills photographed off a screen
(IMG_*) add a second projection and lens distortion: approximate only. Turning a ratio into feet still needs a ruler (a door height, an actor); the
rulers are listed separately, each with its own assumption, so the gate can tell them apart.

Reads are px on gridded full-resolution crops, +-8 px each. Ceilings are read to the PLANE (top of the crown), with the
crown's lower edge alongside.
usage: uv run python -I tools/house/film_ratios.py
"""
PICK = 8
# frame: [(what, floor y, line y, ref y, ref name, plane)]: ratio = (floor - line) / (floor - ref) in that plane
IMAGES = {"IMG_4261 upstairs hall (Kevin, user still)": "art/home_alone/references/foyer-film/IMG_4261.JPG",
          "then-foyer.png foyer (film, user still)": "art/home_alone/references/foyer-film/then-foyer.png",
          "entry205.jpg foyer (Marina, Part 1 3:25)": "art/home_alone/references/foyer-calibration/entry205.jpg"}
SCREEN_PHOTO = {"IMG_4261 upstairs hall (Kevin, user still)"}
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


def ratio(f, line, ref, s1=0, s2=0, v=None):
    """Height of `line` over height of `ref` above the floor row f, all on one vertical image line. With the vertical VP's row v
    the cross-ratio (f, ref, line, v) gives the true ratio; without it (v=None) the plain pixel ratio (camera level only)."""
    f_, l_, r_ = f, line - s1, ref - s2
    if v is None:
        return (f_ - l_) / (f_ - r_)
    return ((f_ - l_) / (v - l_)) / ((f_ - r_) / (v - r_))


def vertical_vp_row(path, scale_x):
    """Row of the vertical vanishing point at the read's column, in the read's pixel frame (picks may be on a resized copy)."""
    import sys as _s
    import cv2
    import numpy as np
    from pathlib import Path as _P
    _s.path.insert(0, str(_P(__file__).resolve().parents[2] / "tools/sfm"))
    from stair_pitch import segments, vanishing_point
    g = cv2.cvtColor(cv2.imread(str(_P(__file__).resolve().parents[2] / path)), cv2.COLOR_BGR2GRAY)
    L, ang = segments(g, 40)
    vp, inl, e = vanishing_point(L[np.abs(ang - 90) < 8], tol_deg=0.5)
    return (vp[1] / vp[2] if abs(vp[2]) > 1e-12 else np.inf) / scale_x, int(inl.sum())


def main():
    out = {}
    for frame, reads in READS.items():
        v, n = vertical_vp_row(IMAGES[frame], 1.0)
        print(f"{frame}: vertical VP row {v:.0f} ({n} segments){'  APPROXIMATE: photographed off a screen' if frame in SCREEN_PHOTO else ''}")
        for what, f, line, ref, rname, plane in reads:
            r = ratio(f, line, ref, v=v); plain = ratio(f, line, ref)
            lo = min(ratio(f, line, ref, a, b, v) for a in (-2 * PICK, 2 * PICK) for b in (-PICK, PICK))
            hi = max(ratio(f, line, ref, a, b, v) for a in (-2 * PICK, 2 * PICK) for b in (-PICK, PICK))
            out[(frame, what)] = r
            feet = "  ".join(f"{k}: {r * v_ / 12:.1f} ft" for k, v_ in RULERS.items()) if rname == "door" else ""
            print(f"  {what:<55} {r:.3f} ({lo:.3f}-{hi:.3f}; plain pixel ratio {plain:.3f})  [{plane}]  {feet}")
    hall = out[("IMG_4261 upstairs hall (Kevin, user still)", "ceiling plane / end-wall wainscot")] / \
        out[("IMG_4261 upstairs hall (Kevin, user still)", "door leaf top / end-wall wainscot")]
    print(f"upstairs hall: ceiling plane = {hall:.2f} x the end door (if the two wainscot caps match); "
          + "  ".join(f"{k}: {hall * v / 12:.1f} ft" for k, v in RULERS.items()))
    return out, hall


if __name__ == "__main__":
    out, hall = main()
    assert 1.0 < hall < 1.6, "hall ceiling/door ratio outside any plausible house: re-read"
