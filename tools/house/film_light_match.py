"""film_light_match: how the day lighting compares with the film, from matched views (user, Oct 16: "cross check with some foyer scenes and
take a read of the lighting"; chose the film's set lighting). For each pair (film frame, live capture from the same solved camera) it
reports, per region: luminance relative to the frame's mean (scale-free: auto exposure cancels) and warmth (R/B). FilmFill's strength
and colour (SpecGreybox.FillNits, FillKelvin) are set so the walls' relative luminance and warmth match.

  uv run --with pillow --with numpy python -I tools/house/film_light_match.py <captures dir> <prefix>
  uv run --with pillow --with numpy python -I tools/house/film_light_match.py --night spec/captures/views/kitchen   (kitchen night)
  uv run --with pillow --with numpy python -I tools/house/film_light_match.py --den-night spec/captures/views/den   (den night, film 2877)
  uv run --with pillow --with numpy python -I tools/house/film_light_match.py --living-night spec/captures/views/living   (living night, film 5650)
  uv run --with pillow --with numpy python -I tools/house/film_light_match.py --hall-night spec/captures/views   (upstairs hall night, film 10819)
Regions are in 640x360 frame coordinates, one box per image on the same surface (drawn and checked: scratch regions.jpg).
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
FILM = ROOT / "art/home_alone/references/foyer-film"
VIEWS = {   # frame: {surface: (box in the film frame, box on the same surface in our capture)}; 11966 has no solved camera yet
    "2677": {"wallpaper": ((70, 20, 115, 70), (70, 20, 115, 70)), "white stringer": ((60, 220, 90, 300), (60, 220, 90, 300))},
    "10248": {"wallpaper": ((60, 150, 120, 260), (60, 120, 120, 200)), "door": ((345, 200, 362, 260), (340, 200, 360, 260))},
}


def lum(c):
    return 0.2126 * c[..., 0] + 0.7152 * c[..., 1] + 0.0722 * c[..., 2]


def read(path, box):
    a = np.asarray(Image.open(path).convert("RGB").resize((640, 360))).astype(float) / 255
    x0, y0, x1, y1 = box
    r = a[y0:y1, x0:x1].reshape(-1, 3).mean(0)
    return lum(r) / lum(a.reshape(-1, 3)).mean(), r[0] / max(r[2], 1e-3)


# NIGHT (Oct 16, the kitchen): film night frames against batch -night renders from approximately the same pose
# (spec/captures/views/kitchen-night-after.json; film 6042's camera does not solve well against our model: rms ~40 px,
# measurements/cameras/film-6042.json). So no pixel-matched boxes: each box sits on the same SURFACE in both images, in each
# image's own pixels, and only ratios between surfaces in one image are compared (scale- and exposure-free). The under-cabinet
# strips drive "backsplash"; "upper" is the upper cabinet's front just above it; "door" the back door's lower white paint; "floor" tile.
NIGHT = {   # film frame: (our render, {surface: (film box, our box)})
    "9812": ("after-night-film9812", {"backsplash": ((1260, 145, 1500, 220), (1150, 430, 1380, 500)), "upper": ((1140, 20, 1460, 110), (1130, 60, 1400, 380)),
                                     "door": ((610, 640, 650, 720), (760, 800, 830, 850)), "floor": ((700, 880, 1000, 1000), (600, 900, 1100, 1000))}),
    "10452": ("after-night-film10452", {"backsplash": ((1480, 270, 1820, 360), (800, 560, 1150, 640)), "upper": ((1360, 20, 1840, 220), (760, 50, 1180, 500)),
                                       "door": ((500, 700, 600, 900), (150, 900, 260, 1000))}),
    "6042": ("after-night-film6042", {"backsplash": ((600, 215, 800, 250), (660, 465, 800, 515)), "upper": ((600, 40, 880, 190), (660, 250, 820, 420))}),
}


# DEN NIGHT (Oct 16): film 2877 (Kevin's movie night: the urn lamp lit on the shelf right of the TV, the room otherwise dim) against our
# batch -night render from roughly its pose (spec/captures/views/views-den-night.json, den/night-film2877). Boxes on the same SURFACES:
# the books in the lamp's pool, the lit wall right of the shelves, the game boxes on the shelves left of the TV (no lamp near them).
DEN_NIGHT = {"2877": ("night-film2877", {"pool": ((1095, 250, 1125, 330), (1225, 330, 1265, 400)),        # shelf back beside the lamp
                                         "wall": ((1600, 500, 1700, 880), (1700, 300, 1880, 700)),         # side wall right of the shelves
                                         "games": ((100, 640, 420, 790), (1000, 380, 1150, 540))})}       # game boxes left of the TV


def den_night(caps):
    for frame, (ours, regions) in DEN_NIGHT.items():
        F = {k: box_lum(ROOT / f"0-homealone/full/homealone-movie-screencaps.com-{frame}.jpg", fb) for k, (fb, ob) in regions.items()}
        O = {k: box_lum(caps / f"{ours}.png", ob) for k, (fb, ob) in regions.items()}
        for a, b in (("pool", "wall"), ("pool", "games"), ("wall", "games")):
            rf, ro = F[a][0] / F[b][0], O[a][0] / O[b][0]
            print(f"{frame:6s} {a:5s} / {b:5s} film {rf:6.2f} ours {ro:6.2f}  (ours/film {ro / rf:5.2f}; log2 {np.log2(ro / rf):+5.2f} stops)")
        print(f"{frame:6s} pool warmth R/B film {F['pool'][1]:4.2f} ours {O['pool'][1]:4.2f}; wall R/B film {F['wall'][1]:4.2f} ours {O['wall'][1]:4.2f}")


# LIVING NIGHT (Oct 16): film 5650 (Kevin's mannequin party, the front wall at night: the black-shaded lamp lit on the corner chest, the
# piano lamp lit) against our batch -night render from roughly its pose (spec/captures/views/views-living-night.json, living/night-film5650).
# Boxes on the same SURFACES: the paper beside the chest lamp, the paper between the French window's drape and the den-side window, the sheer.
LIVING_NIGHT = {"5650": ("night-film5650", {"lamp wall": ((600, 130, 690, 300), (520, 260, 620, 420)),
                                            "mid wall": ((1340, 120, 1480, 400), (1010, 220, 1080, 520)),
                                            "sheer": ((1100, 120, 1180, 420), (1250, 380, 1350, 650))})}


def living_night(caps):
    for frame, (ours, regions) in LIVING_NIGHT.items():
        F = {k: box_lum(ROOT / f"0-homealone/full/homealone-movie-screencaps.com-{frame}.jpg", fb) for k, (fb, ob) in regions.items()}
        O = {k: box_lum(caps / f"{ours}.png", ob) for k, (fb, ob) in regions.items()}
        for a_, b_ in (("lamp wall", "mid wall"), ("sheer", "mid wall")):
            rf, ro = F[a_][0] / F[b_][0], O[a_][0] / O[b_][0]
            print(f"{frame:6s} {a_:9s} / {b_:8s} film {rf:6.2f} ours {ro:6.2f}  (ours/film {ro / rf:5.2f}; log2 {np.log2(ro / rf):+5.2f} stops)")
        print(f"{frame:6s} warmth R/B: lamp wall film {F['lamp wall'][1]:4.2f} ours {O['lamp wall'][1]:4.2f}; mid wall film {F['mid wall'][1]:4.2f} ours {O['mid wall'][1]:4.2f}")


# HALL NIGHT (Oct 17, the upstairs hall's sconces): film 10819 (low in the hall at night, the vestibule's two sconces lit over the parents'
# table) against our batch -night render from its placed camera (spec/captures/views/hall/views-after-night.json, hall/after-film10819-night).
# Boxes on the same SURFACES: the green side wall just below the near sconce, the green wall opposite it (the vestibule's left wall, above
# the cap), and the runner. Scale-free ratios between surfaces in one image.
HALL_NIGHT = {"10819": ("hall/after-film10819-night", {"sconce wall": ((1305, 150, 1330, 300), (1270, 300, 1320, 520)),
                                                       "far wall": ((560, 330, 640, 460), (745, 360, 800, 520)),
                                                       "runner": ((700, 950, 1100, 1040), (820, 900, 1150, 1050))})}


def hall_night(caps):
    for frame, (ours, regions) in HALL_NIGHT.items():
        F = {k: box_lum(ROOT / f"0-homealone/full/homealone-movie-screencaps.com-{frame}.jpg", fb) for k, (fb, ob) in regions.items()}
        O = {k: box_lum(caps / f"{ours}.png", ob) for k, (fb, ob) in regions.items()}
        for a_, b_ in (("sconce wall", "far wall"), ("runner", "far wall")):
            rf, ro = F[a_][0] / F[b_][0], O[a_][0] / O[b_][0]
            print(f"{frame:6s} {a_:11s} / {b_:8s} film {rf:6.2f} ours {ro:6.2f}  (ours/film {ro / rf:5.2f}; log2 {np.log2(ro / rf):+5.2f} stops)")
        print(f"{frame:6s} warmth R/B: sconce wall film {F['sconce wall'][1]:4.2f} ours {O['sconce wall'][1]:4.2f}; runner film {F['runner'][1]:4.2f} ours {O['runner'][1]:4.2f}")


def box_lum(path, box):
    a = np.asarray(Image.open(path).convert("RGB")).astype(float) / 255
    a = np.where(a <= 0.04045, a / 12.92, ((a + 0.055) / 1.055) ** 2.4)        # linear light
    x0, y0, x1, y1 = box; r = a[y0:y1, x0:x1].reshape(-1, 3).mean(0)
    return lum(r), r[0] / max(r[2], 1e-4)


def night(caps):
    out = []
    for frame, (ours, regions) in NIGHT.items():
        F = {k: box_lum(ROOT / f"0-homealone/full/homealone-movie-screencaps.com-{frame}.jpg", fb) for k, (fb, ob) in regions.items()}
        O = {k: box_lum(caps / f"{ours}.png", ob) for k, (fb, ob) in regions.items()}
        for k in regions:
            if k == "backsplash": continue
            rf, ro = F["backsplash"][0] / F[k][0], O["backsplash"][0] / O[k][0]
            out.append((frame, k, rf, ro)); print(f"{frame:6s} backsplash / {k:6s} film {rf:6.2f} ours {ro:6.2f}  (ours/film {ro / rf:5.2f}; log2 {np.log2(ro / rf):+5.2f} stops)")
        print(f"{frame:6s} backsplash warmth R/B  film {F['backsplash'][1]:4.2f} ours {O['backsplash'][1]:4.2f}")
    return out


if __name__ == "__main__":
    if "--hall-night" in sys.argv:
        hall_night(Path(sys.argv[sys.argv.index("--hall-night") + 1])); sys.exit()
    if "--living-night" in sys.argv:
        living_night(Path(sys.argv[sys.argv.index("--living-night") + 1])); sys.exit()
    if "--den-night" in sys.argv:
        den_night(Path(sys.argv[sys.argv.index("--den-night") + 1])); sys.exit()
    if "--night" in sys.argv:
        night(Path(sys.argv[sys.argv.index("--night") + 1])); sys.exit()
    cap, prefix = Path(sys.argv[1]), sys.argv[2]
    for frame, regions in VIEWS.items():
        for name, (fbox, obox) in regions.items():
            fl, fw = read(FILM / f"film-{frame}.jpg", fbox)
            ol, ow = read(cap / f"{prefix}{frame}.png", obox)
            print(f"{frame:6s} {name:12s} rel. luminance film {fl:4.2f} ours {ol:4.2f} ({ol / fl:4.2f}x)   warmth R/B film {fw:4.2f} ours {ow:4.2f}")
