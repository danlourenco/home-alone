"""buzz_prop_textures: the printed faces of Buzz's hero props, cut from the film (props lane, Oct 17 overnight).

  uv run --with numpy --with pillow python -I tools/house/buzz_prop_textures.py
  -> spec/dressing/buzz_props_{can,playboy,girlfriend,chips,jordan}.png (read by tools/house/hifi_buzz_props.py)

Inputs: the film screencaps in 0-homealone/full (untracked; the PNGs are committed) and the Jordan "Measure Up" poster photo
(unity/HomeAlone/Assets/Textures/Buzz/Jordan.jpg).
  can        film 2720 (the Bulls wastebasket by the chest): bands and colour read off the frame, the bull drawn (too blurred to cut); the
             lettering is set in Georgia Bold (Kevin's head hides the left half of the film's)
  playboy    film 2706, the cover rectified (8.5 x 11 in); its bottom edge is the frame's (the last cover line is just above it)
  girlfriend film 2752, the photo inside the frame mat rectified (5 x 7 in)
  chips      film 2724, the yellow Crunch Tators bag face
  jordan     the poster photo cropped to the sheet, the four tape squares painted over with the colour beside them
  cork_*     film 530, the corkboard over the desk: six pinned papers cut out (calendar, couple photo, comic, card, basketball card, note)
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
FILM = ROOT / "0-homealone/full/homealone-movie-screencaps.com-{}.jpg"
OUT = str(ROOT / "spec/dressing/buzz_props_{}.png")


def film(n):
    return Image.open(str(FILM).format(n)).convert("RGB")


def rectify(im, quad, size):
    """quad = TL, TR, BR, BL in source pixels -> an upright size[0] x size[1] image"""
    (a, b, c, d) = quad
    return im.transform(size, Image.QUAD, data=(*a, *d, *c, *b), resample=Image.BICUBIC)


def median(im, box):
    return tuple(int(v) for v in np.median(np.asarray(im.crop(box)).reshape(-1, 3), axis=0))


# ---- Bulls can: label around the whole circumference (u) by the can's height (v, top of image = rim)
f = film(2720)
# the frame is in shade (the bull's red reads sRGB ~(67, 0, 11)): keep its hue at a painted-red lightness (red channel 180).
# The bull itself is too blurred to cut cleanly (its outline reads pink): drawn as the logo's silhouette, red on the white panel
bb = np.asarray(f.crop((1530, 330, 1690, 488))).astype(int); isred = bb[..., 0] > bb[..., 1] + 60
hue = np.median(bb[isred], axis=0); red = tuple(int(v) for v in np.clip(hue * 180.0 / hue[0], 0, 255)); red_body = red
BULL = [(0.02, 0.02), (0.18, 0.20), (0.32, 0.25), (0.68, 0.25), (0.82, 0.20), (0.98, 0.02), (0.90, 0.30), (0.76, 0.40), (0.72, 0.62),
        (0.62, 0.92), (0.50, 1.0), (0.38, 0.92), (0.28, 0.62), (0.24, 0.40), (0.10, 0.30)]
W, H = 2048, 1024
lab = Image.new("RGB", (W, H), red_body); d = ImageDraw.Draw(lab)
bands = [(0.00, 0.10, red), (0.10, 0.125, (235, 232, 222)), (0.125, 0.16, (20, 18, 18)), (0.16, 0.185, (235, 232, 222)), (0.185, 0.205, red)]
for y0, y1, c in bands:
    d.rectangle([0, int(y0 * H), W, int(y1 * H)], fill=c)
font_s = ImageFont.truetype("/System/Library/Fonts/Supplemental/Georgia Bold.ttf", 120)
font_b = ImageFont.truetype("/System/Library/Fonts/Supplemental/Georgia Bold.ttf", 150)
for cx in (W * 0.25, W * 0.75):                  # the panel front and back
    pw = W * 0.40
    d.rounded_rectangle([cx - pw / 2, 0.215 * H, cx + pw / 2, 0.93 * H], radius=60, fill=(235, 232, 222))
    for txt, fnt, y in (("CHICAGO", font_s, 0.235), ("BULLS", font_b, 0.38)):
        tw = d.textlength(txt, font=fnt)
        d.text((cx - tw / 2, y * H), txt, fill=(22, 20, 20), font=fnt)
    bw, bh, by = pw * 0.7, 0.33 * H, 0.57 * H
    d.polygon([(cx + (u - 0.5) * bw, by + v * bh) for u, v in BULL], fill=red)
lab.save(OUT.format("can"))
print("can", red, red_body)

# ---- Playboy cover (film 2706)
rectify(film(2706), [(933, 30), (1620, 7), (1703, 1058), (913, 1058)], (850, 1100)).save(OUT.format("playboy"))

# ---- girlfriend photo (film 2752), inside the mat
rectify(film(2752), [(458, 205), (1000, 92), (1262, 870), (738, 995)], (500, 700)).save(OUT.format("girlfriend"))

# ---- chip bag face (film 2724)
Image.fromarray(np.clip(np.asarray(film(2724).crop((20, 200, 480, 1000))) * 1.3, 0, 255).astype(np.uint8)).save(OUT.format("chips"))

# ---- Jordan poster
j = Image.open(ROOT / "unity/HomeAlone/Assets/Textures/Buzz/Jordan.jpg").convert("RGB")
d = ImageDraw.Draw(j)
yellow = median(j, (110, 300, 140, 400))
for box, c in (((92, 52, 168, 132), yellow), ((536, 40, 612, 122), median(j, (500, 125, 530, 140))), ((92, 1468, 170, 1548), median(j, (110, 1400, 140, 1460))),
               ((546, 1464, 622, 1548), median(j, (510, 1440, 545, 1462)))):
    d.rectangle(box, fill=c)
j.crop((95, 58, 604, 1546)).save(OUT.format("jordan"))
print("jordan", yellow)

# ---- the corkboard's pinned papers (film 530, over the desk; lamp-lit, brightened as the chip bag): the calendar under the Bulls
# photo, the couple photo, the comic, the red-framed card, the basketball card, an "IDIOTS!" note. Boxes in film pixels.
CORK = {"calendar": (1570, 15, 1760, 312), "couple": (1405, 62, 1472, 156), "comic": (1357, 172, 1447, 332),
        "card": (1480, 8, 1568, 128), "bball": (1800, 20, 1860, 192), "idiots": (1764, 203, 1822, 290)}
f = film(530)
for k, box in CORK.items():
    im = Image.fromarray(np.clip(np.asarray(f.crop(box)) * 1.4, 0, 255).astype(np.uint8))
    im.resize((im.width * 2, im.height * 2), Image.BICUBIC).save(OUT.format("cork_" + k))
