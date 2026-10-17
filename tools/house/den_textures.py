"""den_textures: ORIGINAL labels for the den's bookcase clutter (board-game box edges, puzzle boxes, VHS spines), drawn here so no real
brand, logo or trademark is copied (the repo is public). The film's shelves (2856-2941) show stacked game and puzzle boxes in bright
primaries with big titles on their edges, a "1000"-piece puzzle box, and VHS tapes in black cases with white spine labels; these
are look-alikes in that spirit, every title and graphic invented.

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
    im.save(OUT)
    OUT.with_suffix(".json").write_text(json.dumps({"note": "UV rectangles [u0, v0, u1, v1] (v up) of each label; all titles and art invented", **cells}, indent=1) + "\n")
    print(OUT, {k: len(v) for k, v in cells.items()})


main()
