"""den_textures: ORIGINAL labels for the den's bookcase clutter (board-game box edges, puzzle boxes, VHS spines), drawn here so no real
brand, logo or trademark is copied (the repo is public). The film's shelves (2856-2941) show stacked game and puzzle boxes in bright
primaries with big titles on their edges, a "1000"-piece puzzle box, and VHS tapes in black cases with white spine labels; these
are look-alikes in that spirit, every title and graphic invented.
Oct 18 (user; hobby project, film props drawn from the frames are fine): Kevin's snacks on the tray lamp (film 2900/2932): the
CRUNCH TATORS bag front (Frito Lay's badge, peanut-oil flash, white title on red, the green dino in a cowboy hat, NO PRESERVATIVES),
its plain back, a Pepsi can wrap (white, blue vertical PEPSI, the red-white-blue globe) and the TV remote's face; drawn by hand here.

  uv run --with pillow python -I tools/house/den_textures.py
  -> spec/dressing/den_labels.png (atlas) + den_labels.json (cell rectangles in UV, for tools/house/hifi_den.py)
"""
import json
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "spec/dressing/den_labels.png"
W, H = 1024, 1024
GAME = ["STAR QUEST", "TOWER TUMBLE", "MYSTERY MANOR", "RACE AROUND", "WORD WIZARD", "TREASURE ISLE", "SPACE FLEET", "PIRATE COVE",
        "FARM FRIENDS", "CASTLE KEEP", "ROCKET RALLY", "JUNGLE TREK"]
PUZZLE = ["1000  HARBOUR IN SNOW", "1000  COUNTRY MILL", "500  LIGHTHOUSE", "1000  WINTER BARN"]
VHS = ["XMAS 1989", "CARTOONS", "HOCKEY", "BIRTHDAY", "SKI TRIP", "RECITAL", "TAPE 4", "OLD MOVIES", "GAME SHOW", "FAMILY", "SHOWS", "SPORTS"]
PALETTE = [(200, 30, 35), (25, 70, 160), (235, 190, 30), (30, 130, 70), (240, 120, 20), (120, 40, 140), (240, 240, 230), (20, 20, 25)]


def bold(sz):
    for f in ("/System/Library/Fonts/Supplemental/Arial Black.ttf", "/System/Library/Fonts/Supplemental/Arial Bold.ttf"):
        try:
            return ImageFont.truetype(f, sz)
        except OSError:
            pass
    return font(sz)


def snacks(im, d, cells):
    """film 2900/2932: the bag (256 x 368 px = 0.20 x 0.29 m), its back, the can wrap (256 x 150 = 0.207 x 0.122) and the remote face"""
    RED, YEL, WHITE, GREEN = (190, 25, 30), (245, 200, 40), (250, 250, 245), (60, 150, 50)
    x0, y0 = 0, 200                                                       # bag front
    d.rectangle([x0, y0, x0 + 255, y0 + 367], fill=RED)
    d.polygon([(x0, y0), (x0 + 255, y0), (x0 + 255, y0 + 70), (x0, y0 + 130)], fill=YEL)              # yellow top, a slant down to the left
    d.ellipse([x0 + 120, y0 + 18, x0 + 220, y0 + 78], fill=RED, outline=YEL, width=3)               # the maker's badge
    d.text((x0 + 170, y0 + 34), "Frito", fill=YEL, font=bold(17), anchor="mm"); d.text((x0 + 170, y0 + 58), "Lay's", fill=YEL, font=bold(19), anchor="mm")
    for i, t in enumerate(("Made With", "100%", "Peanut Oil")):
        d.text((x0 + 14, y0 + 30 + 17 * i), t, fill=RED, font=bold(13))
    for t, yy, sz in (("CRUNCH", 112, 50), ("TATORS", 166, 50)):                                       # the title: white, red-shadowed
        d.text((x0 + 131, y0 + yy + 3), t, fill=(110, 10, 15), font=bold(sz), anchor="mm")
        d.text((x0 + 128, y0 + yy), t, fill=WHITE, font=bold(sz), anchor="mm", stroke_width=2, stroke_fill=(150, 15, 20))
    d.text((x0 + 128, y0 + 202), "CRUNCHY POTATO CHIPS", fill=WHITE, font=bold(13), anchor="mm")
    d.rounded_rectangle([x0 + 40, y0 + 214, x0 + 216, y0 + 240], 8, fill=YEL); d.text((x0 + 128, y0 + 227), "Hearty Mesquite", fill=RED, font=bold(16), anchor="mm")
    cx, cy = x0 + 90, y0 + 312                                           # the dino: green body, tail, snout, cowboy hat, eye
    d.polygon([(cx - 70, cy + 40), (cx - 20, cy + 10), (cx - 10, cy + 30)], fill=GREEN)                 # tail
    d.ellipse([cx - 30, cy - 20, cx + 30, cy + 50], fill=GREEN, outline=(20, 70, 20), width=2)
    d.ellipse([cx - 5, cy - 50, cx + 55, cy - 10], fill=GREEN, outline=(20, 70, 20), width=2)           # head
    d.polygon([(cx + 40, cy - 40), (cx + 85, cy - 30), (cx + 45, cy - 18)], fill=GREEN)                  # snout
    for k in range(4):
        d.polygon([(cx + 46 + 9 * k, cy - 22), (cx + 50 + 9 * k, cy - 14), (cx + 54 + 9 * k, cy - 22)], fill=WHITE)   # teeth
    d.ellipse([cx + 18, cy - 44, cx + 30, cy - 32], fill=WHITE); d.ellipse([cx + 22, cy - 41, cx + 28, cy - 35], fill=(0, 0, 0))
    d.ellipse([cx - 20, cy - 58, cx + 60, cy - 44], fill=(200, 160, 70)); d.rectangle([cx + 2, cy - 76, cx + 38, cy - 50], fill=(200, 160, 70))   # hat
    d.rectangle([cx + 2, cy - 58, cx + 38, cy - 53], fill=(120, 60, 20))
    d.ellipse([cx - 25, cy + 40, cx + 5, cy + 55], fill=YEL); d.ellipse([cx + 5, cy + 40, cx + 35, cy + 55], fill=YEL)   # boots
    for k in range(6):                                                    # chips flying
        bx, by = x0 + 175 + (k % 2) * 36, y0 + 268 + 20 * (k // 2)
        d.ellipse([bx, by, bx + 26, by + 14], fill=(235, 180, 60), outline=(150, 90, 20))
    d.text((x0 + 250, y0 + 356), "NO PRESERVATIVES", fill=WHITE, font=bold(11), anchor="rm")
    cells["bag_front"] = [x0 / W, 1 - (y0 + 368) / H, (x0 + 256) / W, 1 - y0 / H]
    x0 = 268                                                              # bag back: red with a yellow band and a white panel
    d.rectangle([x0, y0, x0 + 255, y0 + 367], fill=RED); d.rectangle([x0, y0, x0 + 255, y0 + 60], fill=YEL)
    d.rectangle([x0 + 40, y0 + 120, x0 + 215, y0 + 260], fill=WHITE)
    for k in range(8):
        d.line([x0 + 50, y0 + 135 + 15 * k, x0 + 205, y0 + 135 + 15 * k], fill=(120, 120, 120), width=2)
    d.text((x0 + 128, y0 + 300), "CRUNCH TATORS", fill=WHITE, font=bold(22), anchor="mm")
    cells["bag_back"] = [x0 / W, 1 - (y0 + 368) / H, (x0 + 256) / W, 1 - y0 / H]
    x0, y0 = 536, 200                                                     # can wrap: u 0..1 round the can, v up
    d.rectangle([x0, y0, x0 + 255, y0 + 149], fill=(238, 238, 236))
    d.rectangle([x0, y0, x0 + 255, y0 + 8], fill=(180, 180, 185)); d.rectangle([x0, y0 + 141, x0 + 255, y0 + 149], fill=(180, 180, 185))
    for k in range(2):                                                    # two faces (film 2932): blue PEPSI across, the globe below it
        gx = x0 + 64 + 128 * k
        d.text((gx, y0 + 48), "PEPSI", fill=(20, 50, 150), font=bold(24), anchor="mm")
        d.pieslice([gx - 24, y0 + 72, gx + 24, y0 + 120], 180, 360, fill=(200, 25, 35)); d.pieslice([gx - 24, y0 + 72, gx + 24, y0 + 120], 0, 180, fill=(20, 60, 160))
        d.chord([gx - 24, y0 + 89, gx + 24, y0 + 103], 0, 360, fill=WHITE)
    cells["can"] = [x0 / W, 1 - (y0 + 150) / H, (x0 + 256) / W, 1 - y0 / H]
    x0 = 804                                                              # remote face: black, rows of grey keys, red power/record
    d.rectangle([x0, y0, x0 + 79, y0 + 255], fill=(18, 18, 20))
    d.rectangle([x0 + 10, y0 + 12, x0 + 69, y0 + 34], fill=(40, 40, 46))
    for r in range(8):
        for c in range(3):
            col = (200, 30, 30) if (r, c) in ((0, 0), (5, 2)) else (120, 120, 125)
            d.rounded_rectangle([x0 + 10 + 22 * c, y0 + 48 + 24 * r, x0 + 26 + 22 * c, y0 + 60 + 24 * r], 3, fill=col)
    cells["remote"] = [x0 / W, 1 - (y0 + 256) / H, (x0 + 80) / W, 1 - y0 / H]


def font(sz):
    try:
        return ImageFont.load_default(size=sz)
    except TypeError:
        return ImageFont.load_default()


def main():
    rng = random.Random(1990)
    im = Image.new("RGB", (W, H), (30, 30, 30)); d = ImageDraw.Draw(im)
    cells = {"game": [], "puzzle": [], "vhs": []}
    # box edges: 4 columns x 16 rows of 256 x 40 px (an edge ~6:1)
    labels = [("game", t) for t in GAME] + [("puzzle", t) for t in PUZZLE]
    for i, (kind, title) in enumerate(labels):
        c, r = i % 4, i // 4; x0, y0 = c * 256, r * 40
        bg = rng.choice(PALETTE[:6]) if kind == "game" else (245, 240, 225)
        fg = (255, 255, 255) if sum(bg) < 450 else (20, 20, 30)
        d.rectangle([x0, y0, x0 + 255, y0 + 39], fill=bg)
        if kind == "game":   # a stripe and a starburst badge
            st = rng.choice([p for p in PALETTE if p != bg]); d.rectangle([x0, y0 + 30, x0 + 255, y0 + 36], fill=st)
            cx, cy = x0 + 225, y0 + 18
            d.regular_polygon((cx, cy, 13), 8, fill=st); d.ellipse([cx - 6, cy - 6, cx + 6, cy + 6], fill=fg)
            d.text((x0 + 8, y0 + 5), title, fill=fg, font=font(20))
        else:                # puzzle: cream with a big red count and a small picture block
            n, rest = title.split("  ")
            d.text((x0 + 6, y0 + 4), n, fill=(200, 25, 30), font=font(28))
            d.text((x0 + 80, y0 + 12), rest, fill=(30, 40, 90), font=font(14))
            d.rectangle([x0 + 200, y0 + 6, x0 + 248, y0 + 33], fill=rng.choice([(90, 140, 190), (120, 150, 90), (160, 120, 80)]))
        cells[kind].append([x0 / W, 1 - (y0 + 40) / H, (x0 + 256) / W, 1 - y0 / H])
    # VHS spines: 32 x 256 px (a spine 25 x 190 mm standing), from y 640
    for i, title in enumerate(VHS):
        x0, y0 = i * 34, 640
        d.rectangle([x0, y0, x0 + 31, y0 + 255], fill=(14, 14, 16))
        d.rectangle([x0 + 5, y0 + 30, x0 + 26, y0 + 225], fill=(236, 234, 226))
        t = Image.new("RGB", (190, 20), (236, 234, 226)); ImageDraw.Draw(t).text((4, 2), title, fill=(30, 30, 120), font=font(15))
        im.paste(t.rotate(90, expand=True), (x0 + 6, y0 + 33))
        cells["vhs"].append([x0 / W, 1 - (y0 + 256) / H, (x0 + 32) / W, 1 - y0 / H])
    snacks(im, d, cells)
    im.save(OUT)
    OUT.with_suffix(".json").write_text(json.dumps({"note": "UV rectangles [u0, v0, u1, v1] (v up) of each label; all titles and art invented", **cells}, indent=1) + "\n")
    print(OUT, {k: len(v) for k, v in cells.items()})


main()
