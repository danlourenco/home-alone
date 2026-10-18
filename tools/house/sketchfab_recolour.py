"""sketchfab_recolour: base-colour maps for two Sketchfab (CC-BY, CREDITS.md) props, recoloured to the film (props lane, Oct 18).

  rifle  henry_lever-action_rifle 'rifle': the grey metal (receiver, barrel, lever, bands) darkened to blued steel, the walnut kept a
         touch warmer -> Buzz's Daisy-style BB gun (film 2766: warm brown stock and forearm, near-black barrel and receiver)
  glove  baseball_glove-2 'default': its tan + blue leather -> one brown leather (film 478/480: a brown glove), shading kept

  uv run --with numpy --with pillow python -I tools/house/sketchfab_recolour.py
  -> unity/HomeAlone/Assets/Purchased/Sketchfab/Recoloured/{rifle,glove}.png (gitignored with the models; SpecGreybox.Sketchfab.cs)
"""
import io
import json
import struct
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SF = ROOT / "unity/HomeAlone/Assets/Purchased/Sketchfab"
OUT = SF / "Recoloured"


def base_map(glb, mat):
    b = (SF / glb).read_bytes(); n = struct.unpack("<I", b[12:16])[0]; j = json.loads(b[20:20 + n]); bin0 = 20 + n + 8
    m = next(m for m in j["materials"] if m["name"] == mat)
    img = j["images"][j["textures"][m["pbrMetallicRoughness"]["baseColorTexture"]["index"]]["source"]]
    bv = j["bufferViews"][img["bufferView"]]; o = bin0 + bv.get("byteOffset", 0)
    return np.asarray(Image.open(io.BytesIO(b[o:o + bv["byteLength"]])).convert("RGB")).astype(np.float32) / 255


OUT.mkdir(parents=True, exist_ok=True)
a = base_map("henry_lever-action_rifle.glb", "rifle")
wood = (a[..., 0] > 1.15 * a[..., 2]) & (a[..., 0] > 0.12)   # the walnut (and the red-brown forearm band)
metal = ~wood
lum = a.mean(2, keepdims=True)
a = np.where(metal[..., None], lum * 0.22 * np.array([0.92, 0.97, 1.08]), a * np.array([1.08, 1.0, 0.94]))
Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).save(OUT / "rifle.png")

g = base_map("baseball_glove-2.glb", "default")
lum = g.mean(2)
leather = lum > 0.04                                          # the black atlas background stays
ref = np.median(lum[leather])
brown = np.array([0.30, 0.16, 0.075])
g[leather] = np.clip(brown[None, :] * (lum[leather] / ref)[:, None], 0, 1)
Image.fromarray((g * 255).astype(np.uint8)).save(OUT / "glove.png")
print("wrote", OUT / "rifle.png", OUT / "glove.png")
