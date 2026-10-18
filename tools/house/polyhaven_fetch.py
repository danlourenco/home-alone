"""polyhaven_fetch: download Poly Haven (CC0) models' 2k glTF into sfm-work/polyhaven/<id>/ (gitignored). Plain UA, no personal data.
  python3 tools/house/polyhaven_fetch.py shrub_01 fir_sapling_medium ...
  python3 tools/house/polyhaven_fetch.py --tex grey_roof_01   # 2k diffuse + GL normal -> Assets/Textures/PolyHaven/<id>/albedo|normal.jpg (TexMat)
"""
import json, sys, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
UA = {"User-Agent": "home-alone-house/1.0"}


def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read()


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
