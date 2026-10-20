"""nb_compare: film frame | render | 50% blend, one sheet (Oct 20 2026).  uv run --with pillow python -I tools/house/nb_compare.py FRAME RENDER OUT [title]"""
import sys
from PIL import Image, ImageDraw
fr, rp, out = int(sys.argv[1]), sys.argv[2], sys.argv[3]; title = sys.argv[4] if len(sys.argv) > 4 else ""
F = Image.open(f"/Users/dlo/Dev/home-alone/0-homealone/full/homealone-movie-screencaps.com-{fr}.jpg").convert("RGB")
R = Image.open(rp).convert("RGB").resize(F.size, Image.LANCZOS); W, H = F.size; s = 0.5
F2, R2 = F.resize((int(W * s), int(H * s))), R.resize((int(W * s), int(H * s)))
o = Image.new("RGB", (F2.width * 3 + 20, F2.height + 40), (20, 20, 20)); o.paste(F2, (0, 40)); o.paste(R2, (F2.width + 10, 40)); o.paste(Image.blend(F2, R2, 0.5), (2 * F2.width + 20, 40))
d = ImageDraw.Draw(o)
for i, t in enumerate((f"film {fr}", "kit render (Blender Cycles, solved camera)", "50/50 overlay")): d.text((i * (F2.width + 10) + 8, 12), t, fill=(240, 240, 240))
d.text((o.width - 900, 12), title, fill=(255, 210, 120)); o.save(out, quality=90)
