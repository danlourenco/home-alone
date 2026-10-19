"""polyhaven_fetch: download Poly Haven (CC0) models' 2k glTF into sfm-work/polyhaven/<id>/ (gitignored). Plain UA, no personal data.
  python3 tools/house/polyhaven_fetch.py shrub_01 fir_sapling_medium ...
  uv run --with numpy --with pillow python -I tools/house/polyhaven_fetch.py --neutral coated_pine   # grain-only albedo for tinting
  python3 tools/house/polyhaven_fetch.py --tex grey_roof_01   # 2k diffuse + GL normal -> Assets/Textures/PolyHaven/<id>/albedo|normal.jpg (TexMat)
"""
import json, sys, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UA = {"User-Agent": "home-alone-house/1.0"}


def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read()


if sys.argv[1] == "--neutral":   # albedo_neutral.jpg: the grain as luminance (mean 0.8), colour from the material tint (room-upgrade trap:
    # a strongly tinted scan - coated_pine's blue is ~0 - cannot be tinted to a measured colour)
    import numpy as np
    from PIL import Image
    for aid in sys.argv[2:]:
        d = ROOT / "unity/HomeAlone/Assets/Textures/PolyHaven" / aid
        a = np.asarray(Image.open(d / "albedo.jpg").convert("RGB")).astype(float) / 255
        L = a @ [0.2126, 0.7152, 0.0722]; L = np.clip(L / L.mean() * 0.8, 0, 1)
        Image.fromarray((np.stack([L] * 3, -1) * 255 + 0.5).astype(np.uint8)).save(d / "albedo_neutral.jpg", quality=92)
        print("neutral", aid, L.mean())
    sys.exit()
if sys.argv[1] == "--tex":
    for aid in sys.argv[2:]:
        files = json.loads(get(f"https://api.polyhaven.com/files/{aid}"))
        d = ROOT / "unity/HomeAlone/Assets/Textures/PolyHaven" / aid; d.mkdir(parents=True, exist_ok=True)
        (d / "albedo.jpg").write_bytes(get(files["Diffuse"]["2k"]["jpg"]["url"]))
        (d / "normal.jpg").write_bytes(get(files["nor_gl"]["2k"]["jpg"]["url"]))
        print("got texture", aid)
    sys.exit()
for aid in sys.argv[1:]:
    d = ROOT / "sfm-work/polyhaven" / aid
    if any(d.glob("*.gltf")):
        print("have", aid); continue
    files = json.loads(get(f"https://api.polyhaven.com/files/{aid}"))
    g = files["gltf"]["2k"]["gltf"]
    d.mkdir(parents=True, exist_ok=True); (d / "files.json").write_text(json.dumps(files))
    (d / Path(g["url"]).name).write_bytes(get(g["url"]))
    for rel, inc in g["include"].items():
        p = d / rel; p.parent.mkdir(parents=True, exist_ok=True); p.write_bytes(get(inc["url"]))
    print("got", aid, len(g["include"]), "files")
