"""stair_arrival: every stair must arrive onto open floor. Beyond its top step, in the direction of travel, a zone as wide as the
flight (less 5 cm a side) and 0.90 m deep, standing on floor at the arrival height, (a 36 in top landing, IRC R311.7.6) must be clear from the arrival floor to 2.00 m above
it (an adult): no wall, ceiling, rail or furniture box of the stair's own spec, and no wall of either storey in spec/geometry.json.
Why (Oct 18): the attic shell trial put the attic's end wall at the attic stair's top step ("the steps lead directly into a wall");
no check looked at what is in front of you when you step off a stair.

  python3 tools/house/stair_arrival.py         # PASS/FAIL per stair in spec/house_spec.json (stair, attic_stair, ...); exit 1 on FAIL
  python3 tools/house/stair_arrival.py demo    # self-check
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DEPTH, HEAD, SIDE = 0.90, 2.00, 0.05
BLOCK = {"wall", "ceiling", "rail", "furniture"}


def centre(b, k):
    return (b[k][0] + b[k][1]) / 2


def arrival(stair):
    """the clear zone beyond the top step: (x0, x1, y0, y1, z0, z1) in the spec frame (y above the upper floor)"""
    steps = sorted((b for b in stair["boxes"] if b["kind"] == "step"), key=lambda b: b["y"][1])
    top, prev = steps[-1], steps[-2]
    dx, dz = centre(top, "x") - centre(prev, "x"), centre(top, "z") - centre(prev, "z")
    y0 = top["y"][1] + stair["rise_m"] + 0.02
    zone = {"y": [y0, y0 + HEAD - 0.02]}
    if abs(dx) > abs(dz):   # runs along x
        e = top["x"][1] if dx > 0 else top["x"][0]
        zone["x"] = sorted([e + 0.01 * (1 if dx > 0 else -1), e + DEPTH * (1 if dx > 0 else -1)])
        zone["z"] = [top["z"][0] + SIDE, top["z"][1] - SIDE]
    else:
        e = top["z"][1] if dz > 0 else top["z"][0]
        zone["z"] = sorted([e + 0.01 * (1 if dz > 0 else -1), e + DEPTH * (1 if dz > 0 else -1)])
        zone["x"] = [top["x"][0] + SIDE, top["x"][1] - SIDE]
    return top["name"], zone


def hits(zone, boxes):
    return [b.get("name", "wall") for b in boxes
            if all(b[k][0] < zone[k][1] and b[k][1] > zone[k][0] for k in ("x", "y", "z"))]


def inside(poly, x, z):
    c = False
    for (x1, z1), (x2, z2) in zip(poly, poly[1:] + poly[:1]):
        if (z1 > z) != (z2 > z) and x < x1 + (z - z1) * (x2 - x1) / (z2 - z1):
            c = not c
    return c


def floored(zone, st, geo):
    """the zone's corners and centre all stand on floor at the arrival height: a floor/landing box of the stair's spec, or a room of
    the storey whose floor is there (geometry.json)"""
    fy = zone["y"][0] - 0.02
    pads = [b for b in st["boxes"] if b["kind"] in ("floor", "landing") and abs(b["y"][1] - fy) < 0.1]
    rooms = [r["poly"] for s in geo.values() if abs(s["floor_y"] - fy) < 0.1 for r in s["rooms"]]
    (x0, x1), (z0, z1) = zone["x"], zone["z"]
    pts = [(x0, z0), (x0, z1), (x1, z0), (x1, z1), ((x0 + x1) / 2, (z0 + z1) / 2)]
    return [p for p in pts if not (any(b["x"][0] <= p[0] <= b["x"][1] and b["z"][0] <= p[1] <= b["z"][1] for b in pads)
                                   or any(inside(r, *p) for r in rooms))]


def check(spec, geo):
    walls = [dict(w, y=[w["y"][0] + s["floor_y"], w["y"][1] + s["floor_y"]], name=f"{name} wall") for name, s in geo.items() for w in s["walls"]]
    out, ok = [], True
    for key, st in spec.items():
        if not (isinstance(st, dict) and "boxes" in st and "rise_m" in st and sum(b["kind"] == "step" for b in st["boxes"]) >= 2):
            continue
        name, zone = arrival(st)
        bad = hits(zone, [b for b in st["boxes"] if b["kind"] in BLOCK] + walls)
        off = floored(zone, st, geo)
        ok &= not bad and not off
        out.append(f"{'FAIL' if bad or off else 'ok  '} {key}: top step {name}, zone x {zone['x'][0]:.2f}..{zone['x'][1]:.2f} z {zone['z'][0]:.2f}..{zone['z'][1]:.2f}"
                   + (f" blocked by {sorted(set(bad))}" if bad else "") + (f"; no floor under {[(round(a, 2), round(b, 2)) for a, b in off]}" if off else ""))
    return ok, out


def demo():
    steps = [{"name": f"s{i}", "kind": "step", "x": [0, 1], "y": [0, 0.2 * (i + 1)], "z": [0.25 * i, 0.25 * (i + 1)]} for i in range(10)]
    pad = {"name": "top", "kind": "floor", "x": [0, 1], "y": [2.1, 2.2], "z": [2.5, 4.0]}
    st = {"rise_m": 0.2, "boxes": steps + [pad]}
    assert check({"s": st}, {})[0]
    assert not check({"s": {"rise_m": 0.2, "boxes": steps}}, {})[0]                                       # no floor: off the edge
    st["boxes"] = steps + [pad, {"name": "end", "kind": "wall", "x": [0, 1], "y": [0, 5], "z": [2.9, 3.0]}]   # 0.4 m past the top: blocked
    assert not check({"s": st}, {})[0]
    geo = {"up": {"floor_y": 2.2, "rooms": [{"poly": [[0, 2.5], [1, 2.5], [1, 4], [0, 4]]}], "walls": [{"x": [0, 1], "y": [0, 2.5], "z": [3.6, 3.7]}]}}   # floor from the storey; wall 1.1 m past: clear
    assert check({"s": dict(st, boxes=steps)}, geo)[0]
    print("demo ok")


if __name__ == "__main__":
    if sys.argv[1:] == ["demo"]:
        demo(); sys.exit(0)
    ok, lines = check(json.loads((ROOT / "spec/house_spec.json").read_text()), json.loads((ROOT / "spec/geometry.json").read_text()))
    print("\n".join(lines))
    sys.exit(0 if ok else 1)
