"""nb_textures: the neighbourhood style kit's PBR sets (Oct 20 2026), shared by every kit house (tools/house/nb_house.py) and the street.

Poly Haven (CC0, fetched by exterior_textures.fetch: plain User-Agent, no personal data) at their real-world size, plus two procedural
sets drawn to period sizes: CLAPBOARD (4 3/8 in = 0.111 m exposure, 9 courses per 1 m tile: lap shadow, drip edge, painted grain from
Poly Haven white_planks_clean) and SHINGLE siding (cedar shakes, 0.178 m = 7 in exposure, random 0.10-0.30 m widths, keyways).
Albedo is NEUTRAL (linear mean ~0.8 for paintable sets): Unity/Blender tint it with the kit palette colour (spec/neighborhood.json
kit.palette), so one texture set serves every house colour (Unity 6 practice: shared materials, few textures).

Out: unity/HomeAlone/Assets/Textures/Neighborhood/<set>/albedo.jpg, normal.jpg (OpenGL), mask.png (HDRP: R metal 0, G AO, B detail 1,
A smoothness) and kit_textures.json {set: {tile_m, smooth, source, licence}}.
  uv run --with pillow --with numpy python -I tools/house/nb_textures.py
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/house"))
from exterior_textures import fetch  # noqa: E402  (Poly Haven download into sfm-work/polyhaven/<id>/)

import os
OUT = Path(os.environ["NB_TEX"]) if os.environ.get("NB_TEX") else ROOT / "unity/HomeAlone/Assets/Textures/Neighborhood"   # NB_TEX: a staging dir (one builder: never write Assets mid-build)
PX = 1024
# set: (Poly Haven id or None, tile_m = the scan's real width (Poly Haven 'dimensions'), neutral linear albedo mean or None (keep colour), smoothness)
SETS = {
    "roof_asphalt": ("grey_roof_01", 8.0, None, 0.18),         # 1920s-80s asphalt / slate-look shingles, ~0.2 m courses
    "roof_clay": ("clay_roof_tiles_02", 2.5, None, 0.30),      # red clay tile (lot_A+1, film 1886)
    "brick": ("red_brick_03", 1.9, None, 0.20),                # same scale as the McCallister facade (68 mm courses, SpecGreybox.Shell)
    "stucco": ("plastered_wall_02", 2.23, 0.72, 0.15),
    "paint": ("white_plaster_02", 1.0, 0.80, 0.35),            # painted trim, columns, sashes (subtle roughness only)
    "concrete": ("concrete_floor_01", 2.0, 0.55, 0.30),        # sidewalks, kerbs, walks, foundations
    "asphalt": ("asphalt_02", 3.0, None, 0.86),                # the street (wet, as HiFi_ExtWetRoad)
    "snow": ("snow_02", 2.0, 0.85, 0.35),
}


def save(o, alb, nrm, ao, rough):
    o.mkdir(parents=True, exist_ok=True)
    Image.fromarray((np.clip(alb, 0, 1) ** (1 / 2.2) * 255).astype(np.uint8)).save(o / "albedo.jpg", quality=92)
    Image.fromarray(((np.clip(nrm, -1, 1) * 0.5 + 0.5) * 255).astype(np.uint8)).save(o / "normal.jpg", quality=95)
    m = np.stack([np.zeros_like(ao), ao, np.ones_like(ao), 1 - rough], -1)
    Image.fromarray((np.clip(m, 0, 1) * 255).astype(np.uint8), "RGBA").save(o / "mask.png")


def height_to_normal(h, metres_per_px, strength=1.0):
    gy, gx = np.gradient(h, metres_per_px)
    n = np.dstack([-gx * strength, gy * strength, np.ones_like(h)])   # OpenGL: +y up (image rows run down)
    return n / np.linalg.norm(n, axis=-1, keepdims=True)


def grain():
    d = ROOT / "sfm-work/polyhaven/white_planks_clean"
    a = np.asarray(Image.open(d / "white_planks_clean_diff_1k.jpg").convert("L").resize((PX, PX)), np.float32) / 255
    return (a - a.mean()) / (a.std() + 1e-6)


def noise(rng, scales):
    acc = np.zeros((PX, PX))
    for sc, amp in scales:
        g = rng.random((PX // sc + 1, PX // sc + 1)); g = np.tile(g, (2, 2))
        im = np.asarray(Image.fromarray((g * 255).astype(np.uint8)).resize((2 * PX + 2 * sc, 2 * PX + 2 * sc), Image.BICUBIC), float)[:PX, :PX] / 255
        acc += amp * im
    return acc / sum(a for _, a in scales)


def clapboard():
    """1 m tile: 9 courses of 0.111 m. Each course: the board's face slopes out toward its butt (bottom) edge (tapered bevel siding,
    ~13 mm butt), a hard shadowed drip edge where it laps over the course below."""
    mpp = 1.0 / PX; v = (np.arange(PX)[:, None] + 0.5) * mpp; u = np.arange(PX)[None, :]
    e = 1.0 / 9; t = (v % e) / e                         # 0 at a course's top (row index grows downward), 1 at its butt
    h = 0.013 * t + 0.0 * u                              # metres proud of the sheathing
    g = grain(); h = h + 0.00025 * g
    nrm = height_to_normal(h, mpp, 1.0)
    butt = np.clip((t - 0.93) / 0.07, 0, 1); under = np.clip(1 - t / 0.08, 0, 1)   # bright butt edge, the shadow just under the lap
    ao = 1 - 0.55 * under ** 1.5
    rng = np.random.default_rng(11); n = noise(rng, [(64, .6), (8, .4)])
    lum = 0.80 * (1 + 0.04 * g + 0.05 * (n - 0.5)) * (1 - 0.25 * under) * (1 + 0.04 * butt)
    alb = np.repeat(lum[..., None] + 0 * u[..., None], 3, -1)
    rough = 0.62 + 0.08 * (n - 0.5) + 0.0 * u
    return alb, nrm, ao + 0 * u, rough


def shingle():
    """1 m tile of cedar shakes: 0.178 m courses (5.6 per metre: tiled as 6 x 0.1667 m to tile exactly), random widths 0.10-0.30 m,
    6 mm keyways, butts 10 mm proud, light/dark weathering per shake."""
    rng = np.random.default_rng(5); mpp = 1.0 / PX; rows = 6; e = PX // rows
    h = np.zeros((PX, PX)); tone = np.ones((PX, PX)); gap = np.zeros((PX, PX))
    for r in range(rows):
        x = 0
        while x < PX:
            w = int(rng.uniform(0.10, 0.30) / mpp); x1 = min(PX, x + w)
            if PX - x1 < 0.08 / mpp: x1 = PX
            sl = (slice(r * e, (r + 1) * e), slice(x, x1))
            t = np.linspace(0, 1, e)[:, None]
            h[sl] = 0.010 * t + 0.0015 * rng.random()
            tone[sl] = rng.uniform(0.82, 1.12)
            gap[r * e:(r + 1) * e, x:min(PX, x + 6)] = 1
            x = x1
    g = grain(); h = h - 0.006 * gap + 0.0004 * g
    nrm = height_to_normal(h, mpp, 1.0)
    t = (np.arange(PX)[:, None] % e) / e; under = np.clip(1 - t / 0.1, 0, 1) + 0 * h
    ao = (1 - 0.5 * under ** 1.5) * (1 - 0.5 * gap)
    lum = 0.78 * tone * (1 + 0.05 * g) * (1 - 0.2 * under)
    return np.repeat(lum[..., None], 3, -1), nrm, ao, 0.75 + 0 * h


# ---------------------------------------------------------------- step 3 (Oct 20): cards and the patchy ground
def _blur(a, r):
    from PIL import ImageFilter
    return np.asarray(Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r)), np.float32) / 255


def room_cards():
    """Lit-window interiors, a 2x2 atlas (512 px each, sRGB, used as albedo AND emissive map of NB_GlassLit): what the film's lit windows
    show at night (11581/11556): warm lamp-lit rooms behind (0) ivory sheers + side drapes, (1) open drapes, a table lamp, a picture,
    (2) a roller shade half down (the upper right window), (3) a Christmas tree behind half-open blinds. Values are radiance-like (the
    material's emissive intensity sets the absolute level); a window shows one quadrant across all its panes (nb_house UVs)."""
    from PIL import ImageDraw
    N = 512; rng = np.random.default_rng(3); out = np.zeros((2 * N, 2 * N, 3), np.float32)
    yy, xx = np.mgrid[0:N, 0:N] / N
    for k in range(4):
        wall = np.array([[1.0, 0.78, 0.52], [0.95, 0.70, 0.45], [1.0, 0.74, 0.50], [0.92, 0.66, 0.42]][k])
        lx, ly = [(0.30, 0.45), (0.72, 0.55), (0.5, 0.40), (0.25, 0.5)][k]
        lamp = np.exp(-((xx - lx) ** 2 + (yy - ly) ** 2) / 0.06)
        img = wall[None, None] * (0.38 + 0.62 * lamp[..., None])
        img[yy > 0.84] *= 0.35                                            # floor / furniture band
        img[yy < 0.06] *= 1.15                                            # ceiling wash
        im = Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)); d = ImageDraw.Draw(im)
        if k == 1:
            d.rectangle([60, 330, 300, 440], fill=(70, 38, 24)); d.rectangle([330, 150, 430, 230], fill=(90, 60, 30)); d.rectangle([340, 160, 420, 220], fill=(150, 120, 80))
            d.polygon([(340, 230), (400, 230), (420, 280), (320, 280)], fill=(255, 225, 160)); d.rectangle([365, 280, 375, 330], fill=(60, 40, 20))
        if k == 3:   # tree with C7-ish dots
            d.polygon([(256, 70), (120, 470), (392, 470)], fill=(25, 60, 30))
            for _ in range(70):
                x, y = rng.integers(140, 372), rng.integers(110, 460)
                if abs(x - 256) < (y - 70) * 0.34: d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=tuple(int(c) for c in rng.choice([[255, 40, 20], [40, 230, 60], [255, 150, 30], [60, 90, 255], [255, 240, 200]])))
        a = np.asarray(im, np.float32) / 255
        a[:, :8] = 0; a[:, -8:] = 0; a[:8] = 0
        if k in (0, 1):   # side drapes (deep red / ivory), gathered: vertical folds, backlit a little at the edges
            col = np.array([0.55, 0.12, 0.08]) if k == 1 else np.array([0.85, 0.80, 0.68])
            fold = 0.75 + 0.25 * np.sin(xx * 90) ** 2
            for x0, x1 in ((0.0, 0.17), (0.83, 1.0)):
                m = (xx >= x0) & (xx <= x1); a[m] = (col[None] * fold[m][:, None]) * (0.55 if k == 0 else 0.35)
        if k == 0:        # sheer: a bright, soft veil over the middle (the lamp glows through it)
            veil = 0.55 + 0.1 * np.sin(xx * 140) ** 2
            m = (xx > 0.17) & (xx < 0.83); a[m] = a[m] * (1 - veil[m][:, None] * 0.6) + np.array([1.0, 0.86, 0.66]) * veil[m][:, None] * 0.6 * (0.5 + 0.5 * lamp[m][:, None])
        if k == 2:        # roller shade, 42 % down: lit from behind (warm, flat), a pull ring
            m = yy < 0.42; a[m] = np.array([0.95, 0.78, 0.52]) * (0.55 + 0.25 * lamp[m][:, None]); a[(yy > 0.40) & (yy < 0.43)] *= 0.5
        if k == 3:        # blinds over the top half
            m = (yy < 0.5) & ((yy * 40) % 1 < 0.45); a[m] *= 0.45
        out[(k // 2) * N:(k // 2 + 1) * N, (k % 2) * N:(k % 2 + 1) * N] = a
    OUT.mkdir(parents=True, exist_ok=True)
    Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8)).save(OUT / "room_cards.png")


def tree_cards():
    """Tier 4 treeline: 4 bare winter tree silhouettes side by side (RGBA 2048 x 1024; each 512 wide), a crown of recursive branches
    over a trunk, alpha = branch coverage (blurred twigs give the film's grey haze of a bare crown at 160-220 m). Dark bark grey,
    a little snow on the upper sides of limbs. Card aspect 1:2 (w:h)."""
    from PIL import ImageDraw
    W, H = 512, 1024; atlas = Image.new("RGBA", (4 * W, H), (0, 0, 0, 0)); rng = np.random.default_rng(17)
    for k in range(4):
        im = Image.new("L", (W, H), 0); d = ImageDraw.Draw(im)
        def br(x, y, ang, L, w, depth):
            x2, y2 = x + L * np.cos(ang), y - L * np.sin(ang)
            d.line([(x, y), (x2, y2)], fill=255, width=max(1, int(w)))
            if depth == 0 or w < 0.8: return
            for _ in range(2 if depth > 5 else rng.integers(2, 4)):
                br(x2, y2, ang + rng.normal(0, 0.42), L * rng.uniform(0.68, 0.8), w * 0.66, depth - 1)
        trunk_h = [0.26, 0.22, 0.32, 0.24][k] * H
        d.line([(W / 2, H), (W / 2, H - trunk_h)], fill=255, width=[22, 18, 16, 20][k])
        for a0 in ([0.95, 1.35, 1.8, 2.2] if k != 2 else [1.2, 1.6, 1.95]):
            br(W / 2, H - trunk_h, a0 + rng.normal(0, 0.1), [150, 165, 140, 155][k], [15, 13, 12, 14][k], 9)
        a = np.asarray(im, np.float32) / 255
        a = np.maximum(a, np.minimum(_blur(a, 7) * 1.5, 0.55))           # the twig haze, see-through
        a = np.clip(a, 0, 1)
        snow = np.clip(np.roll(a, -2, 0) - a, 0, 1) * 0.0 + np.clip(a - np.roll(a, 3, 0), 0, 1)
        rgb = np.dstack([0.16 + 0.5 * snow, 0.15 + 0.5 * snow, 0.15 + 0.52 * snow])
        tile = Image.fromarray((np.dstack([np.clip(rgb, 0, 1), a]) * 255).astype(np.uint8), "RGBA")
        atlas.paste(tile, (k * W, 0))
    OUT.mkdir(parents=True, exist_ok=True); atlas.save(OUT / "tree_cards.png")


def snow_patchy():
    """The film's patchy front-yard snow (11581/11626: grass and wet leaf litter through thin snow, snow kept in the shade and on the
    parkway banks): Poly Haven snow_02 over brown_mud_leaves_01 by a 2-scale noise mask, 6 m tile. Used for lawns (not walks)."""
    a = fetch("snow_02", "1k"); b = fetch("brown_mud_leaves_01", "1k"); P2 = 2048
    def I(d, n, cs="RGB"): return np.asarray(Image.open(d / f"{n}.jpg").convert(cs).resize((P2 // 3 + 1, P2 // 3 + 1), Image.LANCZOS), np.float32) / 255
    def T(x): return np.tile(x, (3, 3) + ((1,) if x.ndim == 3 else ()))[:P2, :P2]
    rng = np.random.default_rng(23); g = rng.random((24, 24)); g = np.tile(g, (2, 2))
    big = np.asarray(Image.fromarray((g * 255).astype(np.uint8)).resize((2 * P2, 2 * P2), Image.BICUBIC), np.float32)[:P2, :P2] / 255
    sm = rng.random((128, 128)); sm = np.asarray(Image.fromarray((np.tile(sm, (2, 2)) * 255).astype(np.uint8)).resize((2 * P2, 2 * P2), Image.BICUBIC), np.float32)[:P2, :P2] / 255
    m = _blur(np.clip((0.6 * big + 0.4 * sm - 0.30) * 5, 0, 1), 3)          # 1 = snow (about 80 %)
    m = m[..., None]
    alb = T(I(a, "albedo")) ** 2.2 * m + (lambda c: c.mean(-1, keepdims=True) * 0.6 + c * 0.4)(T(I(b, "albedo")) ** 2.2) * np.array([0.9, 0.75, 0.6]) * (1 - m)
    nrm = (T(I(a, "normal")) * m + T(I(b, "normal")) * (1 - m)) * 2 - 1
    ao = T(I(a, "ao", "L")) * m[..., 0] + T(I(b, "ao", "L")) * (1 - m[..., 0]); rough = T(I(a, "rough", "L")) * m[..., 0] + 0.45 * (1 - m[..., 0])

    save(OUT / "snow_patchy", alb, nrm, ao, rough)


def step3():
    room_cards(); tree_cards(); snow_patchy()
    kp = OUT / "kit_textures.json"; meta = json.loads(kp.read_text()) if kp.exists() else json.loads((ROOT / "unity/HomeAlone/Assets/Textures/Neighborhood/kit_textures.json").read_text())
    meta["snow_patchy"] = {"tile_m": 6.0, "smooth": 0.3, "source": "Poly Haven snow_02 + brown_mud_leaves_01, noise mask (tools/house/nb_textures.py)", "licence": "CC0"}
    kp.write_text(json.dumps(meta, indent=1)); print("step3: room_cards.png, tree_cards.png, snow_patchy")


def main():
    if "--step3" in sys.argv: return step3()
    meta = {}
    for name, (aid, tile, neutral, smooth) in SETS.items():
        d = fetch(aid, "1k")
        I = lambda n: Image.open(d / f"{n}.jpg").resize((PX, PX), Image.LANCZOS)
        alb = (np.asarray(I("albedo").convert("RGB"), np.float32) / 255) ** 2.2
        if neutral:
            alb = np.clip(alb / alb.reshape(-1, 3).mean(0) * neutral, 0, 1)
        nrm = np.asarray(I("normal").convert("RGB"), np.float32) / 255 * 2 - 1
        L = lambda n: np.asarray(I(n).convert("L"), np.float32) / 255
        save(OUT / name, alb, nrm, L("ao"), L("rough"))
        meta[name] = {"tile_m": tile, "smooth": smooth, "source": f"Poly Haven {aid}", "licence": "CC0"}
        print(name, aid, tile)
    for name, fn, smooth in (("clapboard", clapboard, 0.38), ("shingle", shingle, 0.22)):
        save(OUT / name, *fn())
        meta[name] = {"tile_m": 1.0, "smooth": smooth, "source": "procedural (tools/house/nb_textures.py; grain: Poly Haven white_planks_clean)", "licence": "CC0"}
        print(name, "procedural")
    (OUT / "kit_textures.json").write_text(json.dumps(meta, indent=1))


if __name__ == "__main__":
    main()
