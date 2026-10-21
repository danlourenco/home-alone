"""sheet_tiles: comparison sheets that never stretch a picture (user, Oct 21: the French-window stills in brick-sheers-nb9-sheet.jpg
looked stretched: a narrow crop resized into a 16:9 tile). Every tile is fitted inside its cell and letterboxed; fit() asserts the
picture's aspect is kept within 1%. Also film_crop(): our 60 deg (vertical) player frame cropped to a film frame's field of view and
aspect, so a solved film camera's pose shows the same framing.

    from sheet_tiles import fit, film_crop, sheet
    sheet([[(img, "caption"), ...], ...], out, title, cell=(640, 360))
    uv run -q --with pillow python -I tools/house/sheet_tiles.py      # self-check
"""
import math

from PIL import Image, ImageDraw

BG = (18, 18, 18)


def fit(im, w, h, bg=BG):
    """im scaled to fit inside w x h (aspect kept), centred on bg."""
    s = min(w / im.width, h / im.height)
    nw, nh = max(1, round(im.width * s)), max(1, round(im.height * s))
    assert abs((nw / nh) / (im.width / im.height) - 1) <= 0.01 or min(nw, nh) < 50, f"tile aspect {nw}x{nh} vs source {im.width}x{im.height}"
    t = Image.new("RGB", (w, h), bg)
    t.paste(im.convert("RGB").resize((nw, nh), Image.LANCZOS), ((w - nw) // 2, (h - nh) // 2))
    return t


def film_crop(im, film_vfov_deg, film_aspect, our_vfov_deg=60.0):
    """the centre of our frame (vertical FOV our_vfov_deg) that a film camera of film_vfov_deg and film_aspect (w/h) would see"""
    k = math.tan(math.radians(film_vfov_deg) / 2) / math.tan(math.radians(our_vfov_deg) / 2)
    ch = im.height * min(1.0, k); cw = min(im.width, ch * film_aspect)
    x0, y0 = (im.width - cw) / 2, (im.height - ch) / 2
    return im.crop((round(x0), round(y0), round(x0 + cw), round(y0 + ch)))


def sheet(rows, out, title, cell=(640, 360), gap=10, cap=22):
    """rows of [(image or None, caption)]: one cell per entry, each picture fitted (never stretched)."""
    W, H = cell; ncol = max(len(r) for r in rows)
    o = Image.new("RGB", (ncol * (W + gap), 30 + len(rows) * (H + cap + 4)), BG); d = ImageDraw.Draw(o)
    d.text((6, 8), title, fill=(255, 220, 120))
    for r, row in enumerate(rows):
        for c, (im, t) in enumerate(row):
            x, y = c * (W + gap), 30 + r * (H + cap + 4)
            if im is not None:
                o.paste(fit(im, W, H), (x, y + cap))
            d.text((x + 4, y + 4), t, fill=(230, 230, 230))
    o.save(out, quality=86)
    return out


if __name__ == "__main__":
    a = Image.new("RGB", (520, 120), (200, 0, 0))
    t = fit(a, 640, 360); px = t.load()
    assert px[320, 180] == (200, 0, 0) and px[320, 20] == BG, "letterboxed, not stretched"
    c = film_crop(Image.new("RGB", (1920, 1080)), 45.63, 1920 / 1058)
    assert abs(c.width / c.height - 1920 / 1058) < 0.01 and c.height < 1080
    print("sheet_tiles ok")
