"""foyer_textures: the foyer's pictures and rugs as images (Oct 16, foyer finish), from spec/dressing/foyer_props.json.

PICTURES: public-domain art only (the repo is public; no film captures, no copyrighted images). Each work is fetched from
Wikimedia Commons (cached in sfm-work/foyer-art/, gitignored), centre-cropped to its frame's opening and packed into one atlas,
spec/dressing/foyer_art.png; spec/dressing/foyer_art.json lists each work's file, artist, licence and its atlas rectangle.
The film's own pictures are matched by kind, not copied: the botanical prints by the door (film 3225/778: cherries, red currants)
become a USDA pomological watercolour and an 1820 currant plate (spec/dressing/prints/print_left|right.png, which replace the
film cuts film_prints.py made), the landing's red camellia an 1788 Botanical Magazine plate, the dark floral under the landing a
Ruysch still life, and the stair gallery's family photographs portraits and cabinet photographs of unknown sitters.

RUGS: invented Persian-style patterns, generated (no design copied): the runner a red field with navy guls and a navy border
(film 1616/1690/10673), the front rug an ivory field with a red-and-navy medallion and a red border (film 1690, 30).

  uv run --with numpy --with pillow python -I tools/house/foyer_textures.py      (needs the network the first time)
"""
import json
import math
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "sfm-work/foyer-art"
OUT = ROOT / "spec/dressing"
P = json.loads((OUT / "foyer_props.json").read_text())
UA = {"User-Agent": "home-alone-house/1.0 (research; public-domain art for a fan recreation)"}

ART = {   # id -> (Commons file, crop: None or (x0, y0, x1, y1) fractions before the aspect crop, vertical bias of the aspect crop)
    "ruysch": ("Rachel Ruysch - Flowers in a vase on a stone slab - 1704 -1995.67.jpg", None, 0.4),
    "camellia": ("The Botanical Magazine, Plate 42 (Volume 2, 1788).png", None, 0.5),
    "cherries": ("Pomological Watercolor POM00004432.jpg", (0.04, 0.03, 0.96, 0.80), 0.4),
    "currants": ("Vincent ribes-rubrum-1820.jpg", (0.06, 0.05, 0.94, 0.95), 0.5),
    "boy": ("'Portrait of a Boy', oil on canvas painting by John Singer Sargent, 1890.jpg", None, 0.3),
    "lady_eden": ("Sargent - Portrait of Lady Eden, 1906, W1920-2-1.jpg", None, 0.2),
    "photo_woman": ("Portrait of an African American Woman, ca 1890.jpg", (0.02, 0.03, 0.48, 0.97), 0.3),
    "nurse": ("Anne and Her Nurse by Mary Cassatt, c. 1897, oil on canvas, Portland Museum of Art.jpg", None, 0.3),
    "red_hat": ("Child with Red Hat, Mary Cassatt.jpg", None, 0.3),
    "photo_mother": ("Unidentified woman with young child, Tacoma, Washington, ca 1896 (PORTRAITS 634).jpg", None, 0.3),
    "yates": ("Gilbert Stuart - Catherine Brass Yates.jpg", None, 0.25),
    "barefoot": ("The Barefoot Child by Mary Cassatt, 1897, pastel.jpg", None, 0.3),
    "photo_fan": ("Woman seated with fan in lap (6902668466).jpg", (0.02, 0.02, 0.49, 0.98), 0.3),
    "boy_sargent2": ("Sargent - Head of an Italian Boy, c. 1878, nr. 718.jpg", None, 0.3),
}
FRAME_W, GALLERY_MAT = 0.03, 0.02    # moulding width; the gallery's mats (hifi_foyer_props.py uses the same numbers)


def get(url):
    """GET with backoff: Commons answers 429 to bursts"""
    for attempt in range(8):
        try:
            time.sleep(1.0)
            return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=120).read()
        except urllib.error.HTTPError as e:
            if e.code != 429 or attempt == 7:
                raise
            time.sleep(10 * (attempt + 1))


def fetch(title):
    """The file (800 px wide) and its licence metadata from Commons, cached."""
    CACHE.mkdir(parents=True, exist_ok=True)
    stem = "".join(c if c.isalnum() else "_" for c in title)[:80]
    img, meta = CACHE / (stem + ".img"), CACHE / (stem + ".json")
    if not img.exists():
        q = urllib.parse.urlencode({"action": "query", "titles": "File:" + title, "prop": "imageinfo", "iiprop": "url|extmetadata",
                                    "iiurlwidth": 960, "format": "json"})
        d = json.loads(get("https://commons.wikimedia.org/w/api.php?" + q))
        ii = next(iter(d["query"]["pages"].values()))["imageinfo"][0]; m = ii["extmetadata"]
        strip = lambda k: " ".join(__import__("re").sub("<[^>]+>", " ", m.get(k, {}).get("value", "")).split())[:200]
        meta.write_text(json.dumps({"file": "File:" + title, "page": ii["descriptionurl"], "licence": strip("LicenseShortName"),
                                    "artist": strip("Artist"), "credit": strip("Credit"), "date": strip("DateTimeOriginal")}, indent=1))
        img.write_bytes(get(ii["thumburl"]))
    return Image.open(img).convert("RGB"), json.loads(meta.read_text())


def aspect_crop(im, aspect, bias):
    """centre crop to width/height = aspect; bias 0 keeps the top, 0.5 the middle (portraits keep the head)"""
    w, h = im.size
    if w / h > aspect:
        nw = int(h * aspect); x0 = (w - nw) // 2; return im.crop((x0, 0, x0 + nw, h))
    nh = int(w / aspect); y0 = int((h - nh) * bias); return im.crop((0, y0, w, y0 + nh))


def opening(p, gallery):
    """the art's opening (width, height) in metres for a picture entry"""
    w = (p["x"][1] - p["x"][0]) if "x" in p else (p["z"][1] - p["z"][0]); h = p["y"][1] - p["y"][0]
    m = GALLERY_MAT if gallery else p["mat"]
    if p.get("frame") == "oval":
        return w - 2 * FRAME_W, h - 2 * FRAME_W
    return w - 2 * (FRAME_W + m), h - 2 * (FRAME_W + m)


def pictures():
    pics = [(k, v, False) for k, v in P["pictures"].items() if k != "gallery"] + [(f"gallery{i + 1}", g, True) for i, g in enumerate(P["pictures"]["gallery"])]
    cell, cols = 512, 4
    atlas = Image.new("RGB", (cell * cols, cell * cols), (128, 128, 128)); index = {}
    for n, (key, p, gal) in enumerate(pics):
        title, crop, bias = ART[p["art"]]
        im, meta = fetch(title)
        if crop:
            W, H = im.size; im = im.crop((int(crop[0] * W), int(crop[1] * H), int(crop[2] * W), int(crop[3] * H)))
        w, h = opening(p, gal); im = aspect_crop(im, w / h, bias)
        s = (cell - 8) / max(im.size); im = im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))), Image.LANCZOS)
        cx, cy = (n % cols) * cell + (cell - im.width) // 2, (n // cols) * cell + (cell - im.height) // 2
        atlas.paste(im, (cx, cy))
        # glTF/Blender UV: v up from the bottom of the image
        index[key] = dict(meta, art=p["art"], uv=[cx / atlas.width, 1 - (cy + im.height) / atlas.height, (cx + im.width) / atlas.width, 1 - cy / atlas.height])
    atlas.save(OUT / "foyer_art.png", optimize=True)
    for side, art in (("print_left", "cherries"), ("print_right", "currants")):   # the door prints' paper: 0.34 x 0.42 (foyer.json)
        title, crop, bias = ART[art]; im, meta = fetch(title)
        if crop:
            W, H = im.size; im = im.crop((int(crop[0] * W), int(crop[1] * H), int(crop[2] * W), int(crop[3] * H)))
        aspect_crop(im, 0.34 / 0.42, bias).resize((680, 840), Image.LANCZOS).save(OUT / f"prints/{side}.png", optimize=True)
        index[side] = dict(meta, art=art, file_out=f"spec/dressing/prints/{side}.png")
    (OUT / "foyer_art.json").write_text(json.dumps({"note": "public-domain works (Wikimedia Commons metadata as fetched); uv = atlas rectangle [u0, v0, u1, v1], v up", "pictures": index}, indent=1))
    (OUT / "prints/prints.json").write_text(json.dumps({"note": "Oct 16: the film cuts (frames 3225 / 778) were replaced by public-domain plates of the same fruit (tools/house/foyer_textures.py); sources in spec/dressing/foyer_art.json",
                                                        "print_left": index["print_left"]["file"], "print_right": index["print_right"]["file"]}, indent=1))
    print("pictures:", {k: v["licence"] for k, v in index.items()})


# ------------------------------------------------------------------ rugs (invented patterns)
def srgb(c):
    return np.array(c, float) / 255.0


def rug(w_m, l_m, ppm, scheme, seed):
    """a Persian-style rug, w across x l along; returns an RGB array (rows along the length)"""
    rng = np.random.default_rng(seed)
    W, L = int(w_m * ppm), int(l_m * ppm)
    u, v = np.meshgrid((np.arange(W) + 0.5) / ppm, (np.arange(L) + 0.5) / ppm)     # metres across / along
    d = np.minimum.reduce([u, w_m - u, v, l_m - v])                                   # distance to the nearest edge
    S = scheme; img = np.zeros((L, W, 3)) + srgb(S["field"])
    b0, b1 = 0.015, 0.015 + S["border"]                                               # outer guard, main border
    img[d < b0] = srgb(S["guard"])
    band = (d >= b0) & (d < b1)
    img[band] = srgb(S["border_bg"])
    # border motif: a running chain of diamonds along the band's centre line, with a small star between
    s = np.where(np.minimum(u, w_m - u) < np.minimum(v, l_m - v), v, u)               # coordinate along the nearer edge
    t = d - (b0 + b1) / 2; per = S["border"] * 1.1
    k = (s % per) - per / 2
    dia = (np.abs(k) + np.abs(t) * 1.4) < S["border"] * 0.42
    img[band & dia] = srgb(S["border_motif"])
    img[band & dia & ((np.abs(k) + np.abs(t) * 1.4) < S["border"] * 0.22)] = srgb(S["accent"])
    star = band & ~dia & (np.hypot(np.abs(k) - per / 2, t) < S["border"] * 0.12)
    img[star] = srgb(S["accent"])
    g = (d >= b1) & (d < b1 + 0.012); img[g] = srgb(S["guard_in"])                     # inner guard stripe
    field = d >= b1 + 0.012
    fx, fy = u - w_m / 2, v - l_m / 2
    if S["kind"] == "guls":   # runner: a column of octagonal guls with small hooks
        p = S["gul_pitch"]; gy = (fy % p) - p / 2; gx = fx
        r = (w_m / 2 - b1 - 0.012) * 0.72
        octo = np.maximum.reduce([np.abs(gx), np.abs(gy), (np.abs(gx) + np.abs(gy)) / 1.3])
        img[field & (octo < r)] = srgb(S["gul"])
        img[field & (octo < r * 0.78)] = srgb(S["gul_in"])
        img[field & (octo < r * 0.40)] = srgb(S["accent"])
        q = field & (octo < r * 0.78) & (np.abs(np.abs(gx) - np.abs(gy)) < r * 0.08) & (octo > r * 0.45)
        img[q] = srgb(S["gul"])
        mid = field & (np.hypot(gx * 1.6, ((fy + p / 2) % p) - p / 2) > 0) & (np.abs(((fy % p) - p / 2)) > p * 0.40)
        dots = mid & (np.hypot((np.abs(gx) - r * 0.6), np.abs(((fy) % p)) - 0.0) < 0.02)
        img[dots] = srgb(S["accent"])
    else:                      # front rug: a central medallion, corner spandrels, a sprinkle of small flowers
        hw, hl = w_m / 2 - b1 - 0.012, l_m / 2 - b1 - 0.012
        med = (np.abs(fx) / (hw * 0.55)) + (np.abs(fy) / (hl * 0.42))
        img[field & (med < 1.0)] = srgb(S["gul"])
        img[field & (med < 0.78)] = srgb(S["gul_in"])
        img[field & (med < 0.45)] = srgb(S["accent"])
        img[field & (med < 0.22)] = srgb(S["gul"])
        cs = ((hw - np.abs(fx)) / (hw * 0.5)) + ((hl - np.abs(fy)) / (hl * 0.32))
        img[field & (cs < 1.0)] = srgb(S["gul"])
        img[field & (cs < 0.7)] = srgb(S["gul_in"])
        sp = 0.16; mx, my = (fx % sp) - sp / 2, (fy % sp) - sp / 2
        flw = field & (med > 1.12) & (cs > 1.15) & (np.hypot(mx, my) < 0.022)
        img[flw] = srgb(S["sprig"])
        img[flw & (np.hypot(mx, my) < 0.009)] = srgb(S["accent"])
    # Persian density: a fine diagonal vine lattice with rosettes over the field (the film's rugs read busy, not graphic)
    lp = S.get("lattice", 0.11); a1, a2 = (fx + fy) / lp, (fx - fy) / lp
    vine = (np.minimum(np.abs(a1 - np.round(a1)), np.abs(a2 - np.round(a2))) < 0.06)
    ros = np.hypot(((fx / lp) % 1 - 0.5), ((fy / lp) % 1 - 0.5)) < 0.17
    petal = np.hypot(((fx / lp + 0.5) % 1 - 0.5), ((fy / lp + 0.5) % 1 - 0.5)) < 0.10
    plain = field & (img == srgb(S["field"])).all(-1)
    img[plain & vine] = img[plain & vine] * 0.55 + srgb(S["sprig"]) * 0.45
    img[plain & ros] = srgb(S["sprig"]); img[plain & petal] = srgb(S["accent"]) * 0.8 + srgb(S["field"]) * 0.2
    inb = band & ~dia & ~star & (np.abs(((s / 0.03) % 1) - 0.5) < 0.12) & (np.abs(t) < S["border"] * 0.45)
    img[inb] = img[inb] * 0.6 + srgb(S["accent"]) * 0.4
    # wool: per-knot jitter and a soft abrash (row-wise colour drift), then slight wear toward the middle
    knot = rng.normal(0, 0.035, (L, W, 1))
    abrash = (rng.normal(0, 0.025, (L, 1, 1)) * np.ones((1, W, 1)))
    img = img * (1 + knot + abrash)
    wear = 1 + 0.05 * np.exp(-((fx / (w_m * 0.3)) ** 2 + (fy / (l_m * 0.35)) ** 2))
    img = np.clip(img * wear[..., None], 0, 1)
    from PIL import ImageFilter
    return Image.fromarray((img * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2))   # wool, not print


def rugs():
    run = P["runner"]; fr = P["front_rug"]
    runner = dict(kind="guls", field=(122, 22, 26), guard=(20, 24, 48), border=0.075, border_bg=(24, 30, 62), border_motif=(150, 32, 34),
                  accent=(214, 196, 150), guard_in=(205, 186, 140), gul=(26, 32, 66), gul_in=(150, 40, 36), gul_pitch=0.40, sprig=(30, 40, 78), lattice=0.09)
    front = dict(kind="medallion", field=(214, 200, 168), guard=(70, 30, 30), border=0.13, border_bg=(128, 34, 34), border_motif=(30, 38, 70),
                 accent=(232, 216, 176), guard_in=(30, 38, 70), gul=(130, 38, 36), gul_in=(36, 46, 82), sprig=(150, 70, 62), lattice=0.12)
    rug(run["z"][1] - run["z"][0], run["x"][1] - run["x"][0], 540, runner, 1).save(OUT / "rug_runner.png", optimize=True)
    rug(fr["x"][1] - fr["x"][0], fr["z"][1] - fr["z"][0], 540, front, 2).save(OUT / "rug_front.png", optimize=True)
    print("rugs written")


if __name__ == "__main__":
    import sys
    if "--rugs" not in sys.argv:
        pictures()
    rugs()
