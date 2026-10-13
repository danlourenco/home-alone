"""Lay the lens/eye-height renders (SpecGreybox.RenderLens) beside Marina's own frame of the same hall view.
usage: uv run --with pillow python tools/house/lens_compare.py   -> spec/captures/lens/compare.png
"""
import json
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
D = ROOT / "spec/captures/lens"
p = json.loads((ROOT / "spec/captures/matched/hall-s1/poses.json").read_text())["poses"][0]
tiles = [(Image.open(p["frame"]), f"Marina's frame (eye {p['pos'][1]:.2f} m, vertical FOV {p['vfov']:.0f} deg)"),
         (Image.open(D / "marina-camera.png"), "grey-box, Marina's camera"),
         (Image.open(D / "player-adult.png"), "grey-box, adult player (eye 1.65 m, FOV 60)"),
         (Image.open(D / "player-kevin.png"), "grey-box, Kevin (eye 1.05 m, FOV 60)")]
sheet = Image.new("RGB", (1920, 1080))
for k, (im, label) in enumerate(tiles):
    im = im.convert("RGB").resize((960, 540)); ImageDraw.Draw(im).text((10, 10), label, fill="yellow")
    sheet.paste(im, ((k % 2) * 960, (k // 2) * 540))
sheet.save(D / "compare.png"); print(D / "compare.png")
