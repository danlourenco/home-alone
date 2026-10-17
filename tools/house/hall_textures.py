"""hall_textures: the upstairs hall's pictures, tapestry, table photographs and the clock / barometer dials as one atlas
(spec/dressing/hall_art.png + hall_art.json with each work's file, artist, licence and atlas rectangle), from spec/dressing/hall.json.

Public-domain works only (the repo is public; never film captures): fetched from Wikimedia Commons through foyer_textures.fetch (cache
sfm-work/foyer-art/, gitignored); a work whose Commons licence is not public domain / CC0 / no known restrictions stops the script.
The film's own pictures are matched by kind: its big rose botanical (film 2296 / 410) -> a Redoute rose plate; its small fruit and
flower prints -> USDA pomological watercolours; its matted landscape prints (1276, 2687) -> Currier & Ives / Durrie winter farm
lithographs; its verdure tapestry (352 / 1276) -> a 17th-18th c. Flemish verdure; the table photographs -> 1890s cabinet cards of
unknown sitters. The clock and barometer dials are drawn here (invented, no maker's name).

  uv run --with numpy --with pillow python -I tools/house/hall_textures.py      (needs the network the first time)
"""
import json
import math
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from foyer_textures import aspect_crop, fetch   # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
D = json.loads((ROOT / "spec/dressing/hall.json").read_text())
OUT = ROOT / "spec/dressing"
FRAME = {"mahogany": 0.035, "gilt": 0.03, "tapestry": 0.0}
OK_LICENCES = ("public domain", "cc0", "pd-", "no restrictions", "no known")

ART = {   # art id -> (Commons file, crop fractions or None, vertical bias of the aspect crop)
    "redoute_rose": ("Redoute - Rosa centifolia foliacea.jpg", (0.04, 0.03, 0.96, 0.93), 0.45),
    "pom_pear": ("Pomological Watercolor POM00007055.jpg", (0.04, 0.03, 0.96, 0.82), 0.4),
    "pom_apple": ("Pomological Watercolor POM00004848.jpg", (0.04, 0.03, 0.96, 0.82), 0.4),
    "pom_plum": ("Pomological Watercolor POM00005005.jpg", (0.04, 0.03, 0.96, 0.82), 0.4),
    "pom_peach": ("Pomological Watercolor POM00005183.jpg", (0.04, 0.03, 0.96, 0.82), 0.4),
    "pom_cherry": ("Pomological Watercolor POM00005378.jpg", (0.04, 0.03, 0.96, 0.82), 0.4),
    "landscape_oak": ("James Merritt Ives (American, 1824-1895), Nathaniel Currier (American, 1813-1888) - American Homestead, Winter - 1946.448.4 - Cleveland Museum of Art.jpg", None, 0.5),
    "landscape_a": ("Winter Morning in the Country MET DT9292.jpg", None, 0.5),
    "landscape_b": ("John Schutler after George Henry Durrie, Home to Thanksgiving, 1867, NGA 66577.jpg", None, 0.5),
    "verdure": ("Stadhuis Maastricht, verdure wandtapijt (1).jpg", None, 0.5),
    "photo_girl": ("African American girl, portrait, cabinet card - DPLA - 3575c3990819eab7477b8046ff6e8933.jpg", None, 0.3),
    "photo_pair": ("B.E. Canavan and Winifred Canavan Skinner (cabinet card is by LaRush, Artist) (8738376217).jpg", None, 0.3),
}


def font(px):
    for f in ("/System/Library/Fonts/Supplemental/Times New Roman.ttf", "/System/Library/Fonts/Times.ttc"):
        try:
            return ImageFont.truetype(f, px)
        except OSError:
            pass
    return ImageFont.load_default()


def dial(kind, n=512):
    """an invented dial: a ship's clock (roman hours) or an aneroid barometer (inches 28-31, weather words), cream enamel"""
    im = Image.new("RGB", (n, n), (236, 230, 214)); d = ImageDraw.Draw(im); c = n / 2
    d.ellipse([6, 6, n - 6, n - 6], outline=(40, 34, 28), width=5)
    if kind == "clock":
        rom = ["XII", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X", "XI"]
        for k in range(60):
            a = 2 * math.pi * k / 60; r0 = c - 22 if k % 5 else c - 40
            d.line([(c + r0 * math.sin(a), c - r0 * math.cos(a)), (c + (c - 14) * math.sin(a), c - (c - 14) * math.cos(a))], fill=(30, 26, 22), width=3 if k % 5 == 0 else 1)
        f = font(38)
        for k, t in enumerate(rom):
            a = 2 * math.pi * k / 12; r = c - 78; w = d.textlength(t, font=f)
            d.text((c + r * math.sin(a) - w / 2, c - r * math.cos(a) - 20), t, fill=(30, 26, 22), font=f)
        for a, L, w in ((math.radians(305), c * 0.48, 9), (math.radians(60), c * 0.70, 6)):   # 10:10
            d.line([(c, c), (c + L * math.sin(a), c - L * math.cos(a))], fill=(25, 22, 20), width=w)
    else:
        f = font(30); f2 = font(26)
        for k in range(31):   # 28.0 .. 31.0 in. over 270 degrees
            a = math.radians(-135 + 9 * k); r0 = c - 40 if k % 5 == 0 else c - 26
            d.line([(c + r0 * math.sin(a), c - r0 * math.cos(a)), (c + (c - 14) * math.sin(a), c - (c - 14) * math.cos(a))], fill=(30, 26, 22), width=3 if k % 5 == 0 else 1)
            if k % 10 == 0:
                t = str(28 + k // 10); w = d.textlength(t, font=f); r = c - 70
                d.text((c + r * math.sin(a) - w / 2, c - r * math.cos(a) - 16), t, fill=(30, 26, 22), font=f)
        for t, deg in (("STORMY", -110), ("RAIN", -55), ("CHANGE", 0), ("FAIR", 55), ("VERY DRY", 110)):
            a = math.radians(deg); r = c - 120; w = d.textlength(t, font=f2)
            d.text((c + r * math.sin(a) - w / 2, c - r * math.cos(a) - 14), t, fill=(60, 50, 40), font=f2)
        a = math.radians(30); d.line([(c, c), (c + (c - 50) * math.sin(a), c - (c - 50) * math.cos(a))], fill=(20, 18, 16), width=5)
        d.line([(c, c), (c + (c - 60) * math.sin(math.radians(5)), c - (c - 60) * math.cos(math.radians(5)))], fill=(150, 110, 40), width=4)
    d.ellipse([c - 12, c - 12, c + 12, c + 12], fill=(150, 110, 40))
    return im


def opening(p):
    """the art's opening (w, h) in metres"""
    w, h = p["s"][1] - p["s"][0], p["y"][1] - p["y"][0]
    fw = FRAME[p["frame"]] if w > 0.2 else 0.018
    m = p.get("mat", 0.0)
    return w - 2 * (fw + m), h - 2 * (fw + m)


def main():
    items = []   # (key, image)
    index = {}
    for p in D["pictures"]:
        title, crop, bias = ART[p["art"]]
        im, meta = fetch(title)
        if not any(k in meta["licence"].lower() for k in OK_LICENCES):
            sys.exit(f"{title}: licence '{meta['licence']}' is not public domain: pick another work")
        if crop:
            W, H = im.size; im = im.crop((int(crop[0] * W), int(crop[1] * H), int(crop[2] * W), int(crop[3] * H)))
        w, h = opening(p); im = aspect_crop(im, w / h, bias)
        items.append((p["key"], im)); index[p["key"]] = dict(meta, art=p["art"])
    td = D["table_dressing"]
    for i, (q, art) in enumerate(zip(td["photos"], ("photo_girl", "photo_pair"))):
        title, crop, bias = ART[art]; im, meta = fetch(title)
        if not any(k in meta["licence"].lower() for k in OK_LICENCES):
            sys.exit(f"{title}: licence '{meta['licence']}' is not public domain")
        im = aspect_crop(im, (q["w"] - 0.03) / (q["h"] - 0.03), bias)
        items.append((f"photo{i + 1}", im)); index[f"photo{i + 1}"] = dict(meta, art=art)
    for k in ("clock", "barometer"):
        items.append((k, dial(k))); index[k] = {"licence": "invented (drawn by tools/house/hall_textures.py)"}
    cell, cols = 512, 4
    atlas = Image.new("RGB", (cell * cols, cell * cols), (128, 128, 128))
    for n, (key, im) in enumerate(items):
        s = (cell - 8) / max(im.size); im = im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))), Image.LANCZOS)
        cx, cy = (n % cols) * cell + (cell - im.width) // 2, (n // cols) * cell + (cell - im.height) // 2
        atlas.paste(im, (cx, cy))
        index[key]["uv"] = [cx / atlas.width, 1 - (cy + im.height) / atlas.height, (cx + im.width) / atlas.width, 1 - cy / atlas.height]   # v up
    atlas.save(OUT / "hall_art.png", optimize=True)
    (OUT / "hall_art.json").write_text(json.dumps({"note": "public-domain works (Wikimedia Commons metadata as fetched) and invented dials; uv = atlas rectangle [u0, v0, u1, v1], v up", "pictures": index}, indent=1) + "\n")
    print({k: v["licence"] for k, v in index.items()})


if __name__ == "__main__":
    main()
