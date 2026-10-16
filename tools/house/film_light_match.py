"""film_light_match: how the day lighting compares with the film, from matched views (user, Oct 16: "cross check with some foyer scenes and
take a read of the lighting"; chose the film's set lighting). For each pair (film frame, live capture from the same solved camera) it
reports, per region: luminance relative to the frame's mean (scale-free: auto exposure cancels) and warmth (R/B). FilmFill's strength
and colour (SpecGreybox.FillNits, FillKelvin) are set so the walls' relative luminance and warmth match.

  uv run --with pillow --with numpy python -I tools/house/film_light_match.py <captures dir> <prefix>
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


if __name__ == "__main__":
    cap, prefix = Path(sys.argv[1]), sys.argv[2]
    for frame, regions in VIEWS.items():
        for name, (fbox, obox) in regions.items():
            fl, fw = read(FILM / f"film-{frame}.jpg", fbox)
            ol, ow = read(cap / f"{prefix}{frame}.png", obox)
            print(f"{frame:6s} {name:12s} rel. luminance film {fl:4.2f} ours {ol:4.2f} ({ol / fl:4.2f}x)   warmth R/B film {fw:4.2f} ours {ow:4.2f}")
