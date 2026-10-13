"""Turn the Unity synthetic renders into a Marina-like tour video with known contaminants.
Shot 0 | title card | shot 1 -crossfade- shot 2 (+caption overlay) | cut | shot 3 (mid-shot zoom).
Writes <ws>/tour.mp4 (H.264 ~6 Mb/s, YouTube-like) and <ws>/timeline.json: video frame -> render index or null.
usage: uv run --with numpy --with pillow python -I tools/sfm/synthetic_compose.py sfm-work/synthetic
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ws = Path(sys.argv[1])
gt = json.loads((ws / "gt.json").read_text())["frames"]
shots = {}
for fr in gt:
    shots.setdefault(fr["shot"], []).append(fr["i"])
font_path = "/System/Library/Fonts/Supplemental/Georgia.ttf"


def render(i):
    return Image.open(ws / "render" / f"r_{i:05d}.png").convert("RGB")


def title(text):
    im = Image.new("RGB", (1920, 1080), (8, 10, 22))
    ImageDraw.Draw(im).text((960, 480), text, font=ImageFont.truetype(font_path, 110), fill="white", anchor="mm")
    return im


def caption(im, text):
    ImageDraw.Draw(im).text((1500, 620), text, font=ImageFont.truetype(font_path, 44), fill="white", anchor="mm")
    return im


out = ws / "composed"
out.mkdir(exist_ok=True)
timeline = []


def emit(im, src):
    im.save(out / f"c_{len(timeline):05d}.jpg", quality=95)
    timeline.append(src)


for i in shots[0]:
    emit(render(i), i)
card = title("Dining Room")
for _ in range(38):  # 1.5 s title card, as in Marina's room intros
    emit(card, None)
# Shot 1 runs into a 12-frame cross-dissolve with shot 2; blended frames have no single true pose.
s1, s2 = shots[1], shots[2]
for i in s1[:-12]:
    emit(render(i), i)
for k in range(12):
    a, b = np.asarray(render(s1[-12 + k]), np.float32), np.asarray(render(s2[k]), np.float32)
    w = (k + 1) / 13
    emit(Image.fromarray(((1 - w) * a + w * b).astype(np.uint8)), None)
for i in s2[12:]:
    # Caption overlay (like "Linen Closet"): frame keeps its true pose; text is the contaminant.
    emit(caption(render(i), "Kitchen"), i)
for i in shots[3]:
    emit(render(i), i)

(ws / "timeline.json").write_text(json.dumps(timeline))
subprocess.run(["ffmpeg", "-v", "error", "-y", "-framerate", "25", "-i", str(out / "c_%05d.jpg"),
                "-c:v", "libx264", "-b:v", "6M", "-maxrate", "8M", "-bufsize", "12M", "-pix_fmt", "yuv420p",
                str(ws / "tour.mp4")], check=True)
print(f"{len(timeline)} video frames ({sum(t is None for t in timeline)} with no true pose) -> {ws / 'tour.mp4'}")
