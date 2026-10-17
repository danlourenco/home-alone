"""kitchen_tile_tex: the kitchen's countertop tile as generated maps (user, Oct 16: "generate a high quality texture ... like the blue
tiles for the island"), 8 x 8 tiles per texture so neighbouring tiles differ.

Measured (changes/2026-10-16-kitchen-cabinets.json): 6 in glazed tile at a 0.158 m pitch (film 6902: the end counter's edge tiles
repeat 58.5 px against the 323 px back-door leaf and the 140 px compactor), 6 mm grout. Colours from the film, flattened by the
grout as the white reference (film-island-detail.jpg: grout lin 0.456/0.445/0.491 -> albedo 0.6): field tile sRGB ~0.19/0.19/0.23,
the cobalt bullnose edge (a separate solid material in SpecGreybox) 0.16/0.38/0.59, grout 0.80/0.78/0.74.

Writes unity/HomeAlone/Assets/Textures/Kitchen/tile_{albedo,normal,mask}.png (HDRP mask: R metallic, G AO, B detail, A smoothness).
UVs come from tools/house/hifi_kitchen.py: one texture = 8 tiles, laid from each counter's front edge.

  uv run --with numpy --with pillow python -I tools/house/kitchen_tile_tex.py
"""
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "unity/HomeAlone/Assets/Textures/Kitchen"
N, PX = 8, 128                      # tiles per texture side, pixels per tile pitch
PITCH, GROUT = 0.158, 0.006         # metres
FIELD = np.array([0.19, 0.19, 0.23]); GROUT_C = np.array([0.80, 0.78, 0.74])   # sRGB albedo
rng = np.random.default_rng(1990)


def srgb2lin(c): return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
def lin2srgb(c): return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.clip(c, 0, None) ** (1 / 2.4) - 0.055)


def noise(size, cells, seed):
    """Smooth value noise (bilinear upsample of a random grid), mean 0, sd ~0.3."""
    r = np.random.default_rng(seed).normal(0, 1, (cells + 1, cells + 1))
    t = np.linspace(0, cells, size, endpoint=False); i = t.astype(int); f = t - i; f = f * f * (3 - 2 * f)
    a = r[i][:, i] * (1 - f)[None, :] + r[i][:, i + 1] * f[None, :]
    b = r[i + 1][:, i] * (1 - f)[None, :] + r[i + 1][:, i + 1] * f[None, :]
    return (a * (1 - f)[:, None] + b * f[:, None]) * 0.3


def main():
    S = N * PX; y, x = np.mgrid[0:S, 0:S] + 0.5
    g = GROUT / PITCH * PX / 2                                   # half the grout width, px
    lx, ly = x % PX, y % PX                                      # position inside the tile cell (grout centred on the cell edge)
    d = np.minimum.reduce([lx, PX - lx, ly, PX - ly]) - g        # px from the tile's edge (negative: grout)
    edge = 3.0                                                   # the glaze's cushion edge, px
    hgt = np.clip(d / edge, 0, 1); hgt = np.sin(hgt * np.pi / 2)  # height: 0 in the grout, rounding up to 1 on the tile
    tile = d > 0
    ti, tj = (x // PX).astype(int), (y // PX).astype(int)
    var = rng.normal(0, 1, (N, N, 3)) * np.array([0.035, 0.035, 0.045]) + rng.normal(0, 0.05, (N, N, 1))   # per tile: value + hue
    lin = srgb2lin(FIELD)[None, None, :] * (1 + var[tj, ti]) * (1 + 0.35 * noise(S, 24, 2)[..., None])       # glaze mottling
    lin_g = srgb2lin(GROUT_C)[None, None, :] * (1 + 0.5 * noise(S, 64, 3)[..., None])
    alb = np.where(tile[..., None], lin, lin_g)
    alb = np.where((~tile)[..., None], alb, alb * (0.92 + 0.08 * hgt[..., None]))                            # the cushion edge reads darker
    OUT.mkdir(parents=True, exist_ok=True)
    Image.fromarray((np.clip(lin2srgb(alb), 0, 1) * 255 + 0.5).astype(np.uint8)).save(OUT / "tile_albedo.png")
    # normal (OpenGL convention, +y up): the grout is 1.5 mm below the glaze; slopes only on the cushion edge
    depth_px = 0.0015 / PITCH * PX
    gy, gx = np.gradient(hgt * depth_px)
    n = np.dstack([-gx, gy, np.ones_like(gx)]); n /= np.linalg.norm(n, axis=2, keepdims=True)
    Image.fromarray(((n * 0.5 + 0.5) * 255 + 0.5).astype(np.uint8)).save(OUT / "tile_normal.png")
    sm = np.where(tile, 0.86 + 0.04 * noise(S, 16, 4), 0.22)                                               # glossy glaze, matte grout
    ao = np.where(tile, 1.0, 0.65) * (0.85 + 0.15 * hgt)
    mask = np.dstack([np.zeros_like(sm), ao, np.zeros_like(sm), sm])
    Image.fromarray((np.clip(mask, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA").save(OUT / "tile_mask.png")
    print("wrote", OUT, f"{S}px = {N} tiles of {PITCH} m; grout {2 * g:.1f} px")


if __name__ == "__main__":
    main()
