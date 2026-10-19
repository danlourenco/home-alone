"""exterior_textures: Poly Haven (CC0) PBR sets for the exterior realism pass (Oct 18 2026; changes/2026-10-18-exterior-realism.json).

Downloads each set (plain User-Agent, no personal data) into sfm-work/polyhaven/<id>/ and writes the Unity maps to
unity/HomeAlone/Assets/Textures/PolyHaven/<id>_x/: albedo.jpg, normal.jpg (OpenGL), height.png (16-bit grey, POM) and mask.png
(HDRP mask map: R metallic 0, G ambient occlusion, B detail mask 1, A smoothness = 1 - roughness).

  uv run --with pillow --with numpy python -I tools/house/exterior_textures.py
"""
import io
import json
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "sfm-work/polyhaven"
OUT = ROOT / "unity/HomeAlone/Assets/Textures/PolyHaven"
UA = {"User-Agent": "home-alone-house/1.0"}
SETS = {   # id: (resolution, neutral albedo mean or None). A neutral set is rescaled to that linear mean per channel (grey, variation
    # kept) so SpecGreybox tints it to a measured colour without a tint over 1
    "red_brick_03": ("2k", None),      # facade brick (68 mm courses: tiled per metre in SpecGreybox.Shell)
    "roof_slates_02": ("2k", None),    # roof shingles (tinted to film 4382's dark brown-grey)
    "white_plaster_02": ("1k", 0.80),  # painted trim: subtle roughness variation
    "concrete_floor_01": ("1k", 0.60), # stone sills, caps, step treads (speckled)
    "snow_02": ("2k", 0.85),           # ground snow, drifts, roof snow
    "asphalt_02": ("2k", None),        # the street (wet)
}
KEYS = (("Diffuse", "albedo"), ("nor_gl", "normal"), ("Rough", "rough"), ("Displacement", "height"), ("AO", "ao"))


def fetch(aid, res):
    d = RAW / aid; d.mkdir(parents=True, exist_ok=True)
    if all((d / f"{n}.jpg").exists() for _, n in KEYS):
        return d
    j = json.load(urllib.request.urlopen(urllib.request.Request(f"https://api.polyhaven.com/files/{aid}", headers=UA)))
    for k, n in KEYS:
        url = j[k][res]["jpg"]["url"]
        (d / f"{n}.jpg").write_bytes(urllib.request.urlopen(urllib.request.Request(url, headers=UA)).read())
    return d


def main():
    for aid, (res, neutral) in SETS.items():
        d = fetch(aid, res); o = OUT / f"{aid}_x"; o.mkdir(parents=True, exist_ok=True)
        px = {"1k": 1024, "2k": 2048}[res]
        I = lambda n: Image.open(d / f"{n}.jpg").resize((px, px), Image.LANCZOS)
        I("normal").convert("RGB").save(o / "normal.jpg", quality=92)
        alb = I("albedo").convert("RGB")
        if neutral:
            a = (np.asarray(alb, np.float32) / 255.0) ** 2.2; a = np.clip(a / a.reshape(-1, 3).mean(0) * neutral, 0, 1)
            alb = Image.fromarray((a ** (1 / 2.2) * 255).astype(np.uint8))
        alb.save(o / "albedo.jpg", quality=92)
        L = lambda n: np.asarray(I(n).convert("L"), np.float32) / 255.0
        h = L("height"); h = (h - h.min()) / max(1e-6, h.max() - h.min())
        Image.fromarray((h * 255).astype(np.uint8)).save(o / "height.png")
        r, ao = L("rough"), L("ao")
        m = np.stack([np.zeros_like(r), ao, np.ones_like(r), 1.0 - r], -1)
        Image.fromarray((m * 255).astype(np.uint8), "RGBA").save(o / "mask.png")
        print(aid, res, "->", o.relative_to(ROOT), "rough mean %.2f" % r.mean())


def generated():
    """Snowflake sprites and the weathering decals' masks (procedural, no download): Assets/Textures/Exterior/."""
    o = ROOT / "unity/HomeAlone/Assets/Textures/Exterior"; o.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(7)
    def disc(n, soft):
        y, x = np.mgrid[0:n, 0:n] / (n - 1) * 2 - 1; r = np.sqrt(x * x + y * y)
        a = np.clip((1 - r) / soft, 0, 1) ** 1.5
        return Image.fromarray(np.dstack([np.full((n, n), 255, np.uint8)] * 3 + [(a * 255).astype(np.uint8)]), "RGBA")
    disc(64, 0.6).save(o / "flake.png"); disc(128, 1.0).save(o / "bokeh.png")
    def noise(h, w, scales):
        acc = np.zeros((h, w))
        for sc, amp in scales:
            g = rng.random((h // sc + 2, w // sc + 2))
            acc += amp * np.asarray(Image.fromarray((g * 255).astype(np.uint8)).resize((w + 2 * sc, h + 2 * sc), Image.BICUBIC), float)[sc:sc + h, sc:sc + w] / 255
        return acc / sum(a for _, a in scales)
    # base grime: dark brown, strongest at the bottom (splash-back off the snow/soil), ragged top edge, fading over the height
    h, w = 256, 1024; v = np.linspace(0, 1, h)[:, None]   # PNG row 0 is the top: dark at the bottom
    n = noise(h, w, [(64, 0.5), (16, 0.3), (4, 0.2)])
    a = np.clip((v ** 1.6) * 1.4 * (0.55 + 0.9 * n) - 0.15, 0, 1) * 0.75
    rgb = np.dstack([np.full((h, w), c, np.uint8) for c in (52, 40, 30)])
    Image.fromarray(np.dstack([rgb, (a * 255).astype(np.uint8)]), "RGBA").save(o / "grime_base.png")
    # streaks under a sill or gutter outlet: thin vertical runs from the top, fading down, a few stronger
    h, w = 512, 256; cols = noise(1, w, [(8, 0.6), (2, 0.4)])[0] ** 3
    v = np.linspace(1, 0, h)[:, None] ** 1.2; n = noise(h, w, [(32, 0.6), (8, 0.4)])
    a = np.clip(cols[None, :] * 2.2 * v * (0.6 + 0.8 * n), 0, 1) * 0.55
    a *= np.clip(np.minimum(np.arange(w), w - 1 - np.arange(w)) / 30, 0, 1)[None, :]
    rgb = np.dstack([np.full((h, w), c, np.uint8) for c in (45, 38, 32)])
    Image.fromarray(np.dstack([rgb, (a * 255).astype(np.uint8)]), "RGBA").save(o / "grime_streak.png")
    print("generated ->", o.relative_to(ROOT))


if __name__ == "__main__":
    main()
    generated()
