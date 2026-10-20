"""shrub_colour: the front-bed shrubs' colour in a built render against film 4382 (exterior shrubs TRIAL 3, Oct 20), not by eye.

Both images are sampled in the same boxes (the film-4382 camera view, spec/captures/views/exterior-shrubs-scan-after.json): three shrubs
(the stoop pair and one upper-bed shrub), a brick patch and the snow. Exposure is normalised on the brick (shrub / brick luminance),
white balance on the snow (per-channel). Prints the render's ratio to the film and the per-channel factor that would match it
(multiply scan_shrubs.py OLIVE by it). Exit 1 when the luminance is more than 35 % off or the hue (R/G, B/G) more than 25 % off.

  uv run --with pillow --with numpy python -I tools/house/shrub_colour.py [RENDER.jpg]
"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
RENDER = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "spec/captures/views/exterior-shrubs-scan/after/film4382.jpg"
FILM = ROOT / "art/home_alone/references/film-exterior/4382.jpg"
# boxes (x0, y0, x1, y1) in each image's own pixels: render 1920x1080, film 1920x1038 (the film camera solve differs a little)
R = {"shrubs": [(690, 800, 770, 885), (1125, 800, 1200, 880), (240, 845, 320, 895)], "brick": (395, 700, 445, 760), "snow": (300, 960, 360, 975)}
F = {"shrubs": [(770, 820, 850, 900), (1070, 810, 1150, 880), (400, 830, 480, 880)], "brick": (395, 700, 440, 760), "snow": (1450, 960, 1550, 990)}
LUM = np.array([0.2126, 0.7152, 0.0722])


def lin(c): return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def mean(a, b): x0, y0, x1, y1 = b; return lin(a[y0:y1, x0:x1].reshape(-1, 3)).mean(0)


def stats(path, B):
    a = np.asarray(Image.open(path).convert("RGB")) / 255.0
    sh = np.mean([mean(a, b) for b in B["shrubs"]], 0); br, sn = mean(a, B["brick"]), mean(a, B["snow"])
    wb = sn / sn[1]   # the snow's cast
    return sh @ LUM / (br @ LUM), (sh / wb) / (sh / wb)[1]


rl, rh = stats(RENDER, R); fl, fh = stats(FILM, F)
k_lum = fl / rl; k = k_lum * fh / rh
print(f"shrub/brick luminance: render {rl:.3f}, film {fl:.3f} (render x{rl / fl:.2f}); hue R:G:B render {rh.round(2)}, film {fh.round(2)}")
print(f"factor to match (OLIVE x): {k.round(2)}")
ok = abs(rl / fl - 1) <= 0.35 and abs(rh[0] / fh[0] - 1) <= 0.25 and abs(rh[2] / fh[2] - 1) <= 0.25
print("Shrub colour:", "ok" if ok else "FAIL", f"({RENDER.name} vs film 4382)")
sys.exit(0 if ok else 1)
