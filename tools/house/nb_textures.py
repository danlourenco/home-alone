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

OUT = ROOT / "unity/HomeAlone/Assets/Textures/Neighborhood"
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


def main():
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
