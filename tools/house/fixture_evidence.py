import sys
from PIL import Image, ImageDraw, ImageFont, ImageOps
R = sys.argv[1]
F = R + "/0-homealone/full/homealone-movie-screencaps.com-{}.jpg"
V = R + "/spec/captures/views/fixtures/{}.png"
I = R + "/art/home_alone/references/foyer-film/{}"
try:
    font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 22); big = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 30)
except Exception:
    font = big = ImageFont.load_default()

def tile(path, crop, marks, label, w=600, h=400):
    im = ImageOps.exif_transpose(Image.open(path)).convert("RGB")
    d = ImageDraw.Draw(im)
    for m in marks:
        if m[0] == "box": d.rectangle(m[1], outline=(255, 40, 40), width=max(6, im.width // 220))
        if m[0] == "line": d.line(m[1], fill=(40, 220, 255), width=max(5, im.width // 260))
    im = im.crop(crop) if crop else im
    im = ImageOps.contain(im, (w, h)); t = Image.new("RGB", (w, h + 34), (20, 20, 20)); t.paste(im, ((w - im.width) // 2, 0))
    ImageDraw.Draw(t).text((8, h + 5), label, fill="white", font=font)
    return t

def row(title, note, tiles):
    w = 600 * len(tiles); r = Image.new("RGB", (max(w, 1800), 434 + 90), (20, 20, 20)); d = ImageDraw.Draw(r)
    d.text((10, 8), title, fill=(255, 220, 90), font=big); d.text((10, 48), note, fill=(220, 220, 220), font=font)
    for i, t in enumerate(tiles): r.paste(t, (i * 600, 90))
    return r

g = Image.open(I.format("IMG_3843.JPG")); g = ImageOps.exif_transpose(g); s3843 = g.width / 900
rows = [
 row("1. LANTERN: in the foyer, just inside the vestibule opening (moved out of the vestibule)",
     "3225: the chain runs down past the opening's head (blue line) against the foyer wall, so it hangs on the foyer side. 1616: the same lantern from outside the door.",
     [tile(F.format(3225), (500, 0, 1500, 667), [("box", (870, 0, 1010, 335)), ("line", (500, 175, 1500, 175))], "film 3225 (from the landing)"),
      tile(F.format(1616), (560, 0, 1460, 600), [("box", (915, 0, 1050, 95))], "film 1616 (from outside the front door)"),
      tile(V.format("light-sled"), (300, 0, 1500, 800), [], "ours, from the landing")]),
 row("   ...and no second chandelier over the stair well",
     "Shots up the stair show the well and landing window with nothing hanging in front of them.",
     [tile(F.format(384), (300, 0, 1500, 800), [], "film 384 (stair foot, looking up)"),
      tile(F.format(3175), (300, 0, 1500, 800), [], "film 3175 (inside the door, low)"),
      tile(I.format("IMG_3843.JPG"), None, [], "your IMG_3843 (wide, from the front)")]),
 row("2. VESTIBULE SCONCES: two-arm candle sconces on the front wall, outside each sidelight (unchanged)",
     "Both sides in 10248; the right one in 778 (beside the sidelight, with the print beyond the opening).",
     [tile(F.format(10248), None, [("box", (350, 120, 520, 300)), ("box", (1390, 140, 1560, 320))], "film 10248"),
      tile(F.format(778), (500, 0, 1500, 667), [("box", (860, 140, 1100, 400))], "film 778"),
      tile(V.format("light-front"), None, [], "ours, facing the front door")]),
 row("3. MIRROR SCONCES: single candles in tall glass chimneys either side of the mirror (were two-arm)",
     "Right wall, past the dining doorway. Positions from Marina 1070.5 s; style from the film.",
     [tile(F.format(1616), (1150, 100, 1920, 620), [("box", (1390, 200, 1720, 430))], "film 1616"),
      tile(F.format(10673), (1350, 0, 1920, 600), [("box", (1600, 60, 1900, 380))], "film 10673"),
      tile(V.format("film-1616"), (900, 100, 1920, 780), [], "ours, matched to 1616")]),
 row("4. REAR DOME LIGHT: opal ceiling light just behind the rear arch (new)",
     "Glows just under the arch head in your IMG_3843 and in film 10673.",
     [tile(I.format("IMG_3843.JPG"), None, [("box", (int(790*s3843), int(345*s3843), int(890*s3843), int(405*s3843)))], "your IMG_3843"),
      tile(F.format(10673), (1000, 50, 1750, 600), [("box", (1250, 210, 1360, 310))], "film 10673"),
      tile(V.format("rear-arch"), (650, 450, 1450, 1000), [], "ours, toward the rear arch")]),
]
out = Image.new("RGB", (1800, sum(r.height for r in rows)), (20, 20, 20)); y = 0
for r in rows: out.paste(r, (0, y)); y += r.height
out.save(sys.argv[2], quality=88); print(out.size)
