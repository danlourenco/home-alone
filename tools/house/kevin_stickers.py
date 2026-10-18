"""kevin_stickers: the stickers on the bunk's wide upper guard board (film 303: a Bulls bumper sticker, dinosaurs, cars, a smiley) drawn
onto the board's pine (the oak veneer albedo SpecGreybox.Kevin uses for KV_Pine, at its tint) -> spec/dressing/kevin_stickers.png.
hifi_kevin.py UV-maps the board's room face to it (one surface: no decal faces to z-fight).
  uv run --with pillow python -I tools/house/kevin_stickers.py"""
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
K = json.loads((ROOT / "spec/dressing/kevin.json").read_text())["bunk"]
L = K["x"][1] - K["x"][0] - 2 * K["post"]; H = K["guard"][1] - K["guard"][0]     # the board's face, metres
PPM = 1100
W, Hp = round(L * PPM), round(H * PPM)
oak = Image.open(ROOT / "unity/HomeAlone/Assets/Textures/PolyHaven/oak_veneer_01/albedo.jpg").convert("RGB")
tile = round(0.8 * PPM)                                          # TexMat tile 0.8 m (SpecGreybox.Kevin KV_Pine)
oak = oak.resize((tile, tile))
img = Image.new("RGB", (W, Hp))
for x in range(0, W, tile):
    img.paste(oak, (x, 0))
img = Image.eval(img, lambda v: v)                               # (per-channel tint below)
r, g, b = img.split()
img = Image.merge("RGB", (r.point(lambda v: min(255, int(v * 1.1))), g.point(lambda v: int(v * 0.95)), b.point(lambda v: int(v * 0.78))))
d = ImageDraw.Draw(img)
m = lambda v: round(v * PPM)
X = lambda f: m(L * f)
Y = lambda y: Hp - m(y)                                          # y up from the board's bottom edge
font = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial Black.ttf", m(0.055))
# the Bulls sticker: red field, black border, white BULLS
x0 = X(0.05); d.rectangle([x0, Y(0.135), x0 + m(0.27), Y(0.02)], fill=(20, 18, 18)); d.rectangle([x0 + m(0.008), Y(0.127), x0 + m(0.262), Y(0.028)], fill=(196, 22, 28))
d.text((x0 + m(0.135), Y(0.075)), "BULLS", font=font, fill=(245, 245, 240), anchor="mm")
DINO = [(0, 0.02), (0.03, 0.03), (0.05, 0.045), (0.07, 0.045), (0.085, 0.07), (0.09, 0.085), (0.105, 0.088), (0.107, 0.08), (0.095, 0.077),
        (0.087, 0.05), (0.08, 0.03), (0.08, 0.0), (0.071, 0.0), (0.07, 0.02), (0.05, 0.02), (0.048, 0.0), (0.039, 0.0), (0.038, 0.022), (0.03, 0.024)]   # long-necked dinosaur
for f, col, k in ((0.29, (40, 150, 60), 1.35), (0.51, (125, 75, 175), 1.15), (0.85, (40, 150, 60), 1.3)):
    d.polygon([(X(f) + m(k * px), Y(0.02 + k * py)) for px, py in DINO], fill=col, outline=(240, 240, 235))
CAR = [(0, 0), (0.10, 0), (0.10, 0.03), (0.075, 0.03), (0.07, 0.052), (0.03, 0.052), (0.025, 0.03), (0, 0.03)]
for f, col in ((0.40, (30, 85, 200)), (0.70, (245, 205, 30))):
    d.polygon([(X(f) + m(1.5 * cx), Y(0.04 + 1.5 * cy)) for cx, cy in CAR], fill=col, outline=(240, 240, 235))
    for wx in (0.033, 0.117):
        c = (X(f) + m(wx), Y(0.04)); d.ellipse([c[0] - m(0.018), c[1] - m(0.018), c[0] + m(0.018), c[1] + m(0.018)], fill=(15, 15, 15))
c = (X(0.62), Y(0.09)); rr = m(0.035)                            # a smiley
d.ellipse([c[0] - rr, c[1] - rr, c[0] + rr, c[1] + rr], fill=(250, 210, 30), outline=(30, 30, 30), width=3)
for ex in (-0.012, 0.012):
    d.ellipse([c[0] + m(ex) - 4, c[1] - m(0.01) - 6, c[0] + m(ex) + 4, c[1] - m(0.01) + 6], fill=(20, 20, 20))
d.arc([c[0] - m(0.02), c[1] - m(0.015), c[0] + m(0.02), c[1] + m(0.022)], 20, 160, fill=(20, 20, 20), width=4)
out = ROOT / "spec/dressing/kevin_stickers.png"
img.save(out)
print("wrote", out, img.size)
