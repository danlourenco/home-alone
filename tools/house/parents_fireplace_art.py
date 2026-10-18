"""parents_fireplace_art: the painting over the parents' bedroom mantel (Oct 18 2026, decoration; changes/2026-10-18-parents-fireplace.json).
Marina 195-204 hangs two pink roses lying on a dark ground in a gilt frame with a green mat. Matched by kind with a public-domain work
(no film or Marina capture): Martin Johnson Heade, 'Roses Lying on Gold Velvet' (c. 1883-1900), from Wikimedia Commons via
foyer_textures.fetch (cached in sfm-work/foyer-art/), centre-cropped to the opening (0.49 x 0.39 m) -> spec/dressing/parents_roses.png;
licence metadata -> spec/dressing/parents_roses.json.

  uv run --with numpy --with pillow python -I tools/house/parents_fireplace_art.py     (needs the network the first time)
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/house"))
from foyer_textures import fetch, aspect_crop   # noqa: E402

TITLE = "Henri Fantin-Latour - Still Life of White Roses - Google Art Project.jpg"
im, meta = fetch(TITLE)
im = aspect_crop(im, 0.49 / 0.39, 0.5).resize((640, 510))
im.save(ROOT / "spec/dressing/parents_roses.png")
(ROOT / "spec/dressing/parents_roses.json").write_text(json.dumps(meta, indent=1) + "\n")
print(meta)
