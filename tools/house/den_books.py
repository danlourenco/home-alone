"""den_books: the den bookcase's books as the Fadnn pack's ten SM_Book models (high res; user Oct 18: "add fidelity to the den's
book case ... use any high res models we have"), standing spine out on hifi_den.py's rows (film 2868/2874/2877: a row on the end
bay's 1.208 shelf, books along the top shelves, the living-side bay's shelves; games, VHS, lamp and soldier keep their spans).
Props lane: by eye, no record. Rewrites the den_book_* entries of spec/dressing/store_props.json (others untouched).
usage: python3 tools/house/den_books.py
"""
import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SP = ROOT / "spec/dressing/store_props.json"
B = json.loads((ROOT / "spec/dressing/den.json").read_text())["bookcase"]
PACK = "Assets/Fadnn - Vintage Interior Furniture Pack/Props/Prefabs/HDRP/SM_Book_{:02d}.prefab"
# model sizes (thickness, depth, height), measured from the FBX files
SIZE = {1: (0.052, 0.183, 0.225), 2: (0.052, 0.183, 0.225), 3: (0.052, 0.183, 0.225), 4: (0.039, 0.183, 0.225), 5: (0.052, 0.183, 0.225),
        6: (0.052, 0.183, 0.25), 7: (0.052, 0.183, 0.25), 8: (0.065, 0.183, 0.25), 9: (0.048, 0.183, 0.25), 10: (0.047, 0.183, 0.225)}


def books():
    x1, z0, z1, T = B["x"][1], B["z"][0], B["z"][1], 0.02
    (dA0, dA1), (dB0, dB1) = B["dividers"]
    (eb0, eb1), (cb0, cb1), (lb0, lb1) = (dB1, z1 - T), (dA1, dB0), (z0 + T, dA0)
    rows = [(19.12, eb1 - 0.02, 0.80), (eb0 + 0.03, eb1 - 0.25, 1.208), (eb0 + 0.20, eb1 - 0.03, 1.617),
            (lb0 + 0.02, lb1 - 0.35, 0.17), (lb0 + 0.15, lb1 - 0.03, 0.452), (17.08, lb1 - 0.03, 0.80), (17.02, lb1 - 0.05, 1.208),
            (lb0 + 0.04, lb1 - 0.40, 1.617), (cb0 + 0.03, B["lower_divider"][0] - 0.02, 0.17)]
    tops = sorted(set(B["shelves_side"] + [B["bottom_top"]]))
    rng, out = random.Random(16), []
    for za, zb, shelf in rows:
        clear = min([t - B["shelf_t"] for t in tops if t > shelf + 0.01] + [B["top_band"]]) - shelf - 0.01
        z = za
        while True:
            m = rng.randint(1, 10); t, d, h = SIZE[m]; s = rng.uniform(0.85, 1.12)
            s = min(s, clear / h)                       # under the shelf above
            if z + t * s > zb:
                break
            out.append({"name": f"den_book_{len(out) + 1:03d}", "prefab": PACK.format(m),
                        "x": [round(x1 - 0.015 - d * s, 4), round(x1 - 0.015, 4)], "z": [round(z, 4), round(z + t * s, 4)],
                        "y0": round(shelf + 0.001, 4), "height": round(h * s, 4), "back": "-x", "hides": [], "collide": False, "yaw": 90,
                        "source": "props lane (Oct 18): den_books.py, Fadnn SM_Book spine out on hifi_den.py's book rows (film 2868/2874/2877)"})
            z += t * s + (0.002 if rng.random() > 0.12 else 0.03)
    return out


if __name__ == "__main__":
    sp = json.loads(SP.read_text())
    key = next(k for k, v in sp.items() if isinstance(v, list))
    bs = books()
    assert bs and all(b["z"][1] - b["z"][0] > 0.03 for b in bs)
    sp[key] = [p for p in sp[key] if not p["name"].startswith("den_book_")] + bs
    SP.write_text(json.dumps(sp, indent=1, ensure_ascii=False) + "\n")
    print(len(bs), "books")
