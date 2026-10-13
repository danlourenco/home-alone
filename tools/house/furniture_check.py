"""Furniture vs standard sizes, in TRUE metres (skill room-feel, step 2).

Reads spec/captures/furniture-<scene>.json (written by Unity: SpecGreybox.DumpFurniture, which records each named
furniture piece's size in scene units and the scene's metres-per-unit) and compares every piece whose name matches
spec/furniture_standards.json. A mattress matches if it fits ANY bed size; other pieces must fall inside their range.
usage: uv run python tools/house/furniture_check.py <scene>      (exit 1 if any piece is off-standard)
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main(scene):
    std = json.loads((ROOT / "spec/furniture_standards.json").read_text())["items"]
    dump = json.loads((ROOT / f"spec/captures/furniture-{scene}.json").read_text())
    mpu = dump["m_per_unit"]
    bad = 0
    print(f"{scene}: {mpu} m per scene unit")
    for p in dump["pieces"]:
        name = p["name"].lower()
        dims = sorted([p["size"][0] * mpu, p["size"][2] * mpu]); h = p["size"][1] * mpu
        w, l = dims
        kinds = {k: v for k, v in std.items() if any(m in name for m in v["match"])}
        if not kinds:
            continue
        def fits(v):
            ok = True
            if "w" in v and "l" in v:
                ok &= v["w"][0] * 0.97 <= w <= v["w"][1] * 1.03 and v["l"][0] * 0.97 <= l <= v["l"][1] * 1.03
            else:
                if "w" in v: ok &= v["w"][0] <= l <= v["w"][1]          # width = the longer horizontal side
                if "d" in v: ok &= v["d"][0] <= w <= v["d"][1]
            if "h" in v: ok &= v["h"][0] <= h <= v["h"][1]
            return ok
        hit = [k for k, v in kinds.items() if fits(v)]
        bad += not hit
        print(f"{'ok ' if hit else 'OFF'} {p['path']:<60} {l:.2f} x {w:.2f} m, {h:.2f} tall  "
              f"{'= ' + hit[0] if hit else 'vs ' + ', '.join(kinds)}")
    print(f"{bad} piece(s) off-standard")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main(sys.argv[1])
