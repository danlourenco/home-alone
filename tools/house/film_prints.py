"""film_prints: the foyer's two botanical prints (front wall, either side of the vestibule opening) as the film shows them,
cut from stills and rectified to their paper's rectangle. Only the paper is cut; the mat (sea green) and the gilt frame are
modelled (hifi_dressing.py), so a poinsettia covering the mat's foot in the still does not matter.

  right print (red currants): film 778, near frontal, paper corners measured on the still
  left print (cherries):      film 3225, from the landing (small: ~95 px wide, so soft)
Paper 0.34 x 0.42 m is foyer.json's print_*_paper (from Marina 203 s); the stills' paper ratio agrees within 4%.

  uv run --with pillow python -I tools/house/film_prints.py   ->  spec/dressing/prints/print_left.png, print_right.png
"""
import json
from pathlib import Path

from PIL import Image, ImageEnhance

ROOT = Path(__file__).resolve().parents[2]
F = ROOT / "0-homealone/full/homealone-movie-screencaps.com-{}.jpg"
OUT = ROOT / "spec/dressing/prints"
# paper corners on the still: top-left, bottom-left, bottom-right, top-right (PIL QUAD order)
PRINTS = {
    "print_right": (778, [(1598, 165), (1593, 533), (1806, 530), (1815, 170)]),
    "print_left": (3225, [(360, 332), (360, 458), (455, 460), (455, 334)]),
}
W, H = 340, 420   # 1 px per mm

OUT.mkdir(parents=True, exist_ok=True)
src = {}
for name, (frame, quad) in PRINTS.items():
    im = Image.open(str(F).format(frame)).convert("RGB")
    flat = im.transform((W, H), Image.QUAD, [c for p in quad for c in p], Image.BICUBIC)
    flat = ImageEnhance.Brightness(flat).enhance(1.08)   # the film's warm grade: lift to paper white without changing the hues
    flat.save(OUT / f"{name}.png")
    src[name] = {"frame": frame, "quad": quad}
(OUT / "prints.json").write_text(json.dumps(src, indent=1) + "\n")
print("wrote", sorted(src))
