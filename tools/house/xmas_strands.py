#!/usr/bin/env python3
"""xmas_strands: the house's window-loop C7 strands at the film's pitch -> spec/dressing/xmas.json (docs/XMAS-LIGHTS.md; read by
SpecGreybox.Xmas.cs for the bake-off build). Same loops as today's (exterior_shell.xmas_lights: every street-side window and both
front dormers, 7.5 cm proud of the face), but the bulbs are C7s every PITCH m (film 5545: 0.21 m, xmas_lights_check.py --film), each on
its socket, with the wire sagging between sockets.

Output frame: Unity world (spec x, y, -z; exterior_shell's y is world y). Per strand: storey (U/L: HouseSplit hides U upstairs),
outward normal, bulbs [[x, y, z], ...], wire polyline.

  uv run -q --with numpy --with shapely python -I tools/house/xmas_strands.py            # write the json
  uv run -q --with numpy --with shapely python -I tools/house/xmas_strands.py --selftest
"""
import json, math, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/house"))
OUT = ROOT / "spec/dressing/xmas.json"
PITCH = 0.21    # film 5545: 0.212 m mean over the two measured loops (xmas_lights_check.py --film)
SAG = 0.012     # C7 sockets clip to the trim; the wire droops ~1 cm between them on the level runs


def loops():
    """the loops exterior_shell.xmas_lights strings today: (storey, axis, d, s, a0, a1, y0, y1, closed), recorded instead of meshed"""
    import exterior_shell as e
    rec = []
    e.build_walls(); hm, _, _ = e.build_roofs(); e.build_windows()
    D = [e.dormer(6.702, e.FRONT_MAIN - 0.78, 1, hm, "U"), e.dormer(12.938, e.FRONT_MAIN - 0.78, 1, hm, "U")]   # main(): the front pair
    real = e.bulb_loop
    def record(B, axis, d, s, a0, a1, y0, y1, closed=True):
        rec.append((B["layer"], axis, d, s, a0, a1, y0, y1, closed))
    e.bulb_loop = record
    try: e.xmas_lights(D)
    finally: e.bulb_loop = real
    return rec


def strand(storey, axis, d, s, a0, a1, y0, y1, closed):
    q = d + s * 0.075   # exterior_shell.bulb_loop: in front of the sills and shutters
    W = lambda a, y: [q, y, -a] if axis == "x" else [a, y, -q]   # spec (q, y, a) / (a, y, q) -> Unity (x, y, -z)
    nrm = [s, 0, 0] if axis == "x" else [0, 0, -s]
    corners = [(a0, y0), (a0, y1), (a1, y1), (a1, y0)] + ([(a0, y0)] if closed else [])
    per = sum(math.hypot(qa - pa, qy - py) for (pa, py), (qa, qy) in zip(corners, corners[1:]))
    n = max(2, round(per / PITCH)); step = per / n
    def at(t):   # point at arc length t along the corners
        for (pa, py), (qa, qy) in zip(corners, corners[1:]):
            L = math.hypot(qa - pa, qy - py)
            if t <= L + 1e-9: u = t / L; return pa + (qa - pa) * u, py + (qy - py) * u, abs(qy - py) < 1e-6
            t -= L
        return corners[-1][0], corners[-1][1], True
    bulbs, wire = [], []
    for k in range(n + (0 if closed else 1)):
        a, y, _ = at(min(k * step + step / 2, per)); bulbs.append([round(v, 4) for v in W(a, y)])
    for k in range(4 * n + 1):   # the wire: 4 samples per pitch, sagging between sockets on level runs
        t = min(k * step / 4, per); a, y, level = at(t); v = ((t / step) + 0.5) % 1.0
        wire.append([round(c, 4) for c in W(a, y - (SAG * 4 * v * (1 - v) if level else 0.0))])
    return {"storey": storey, "normal": nrm, "perimeter": round(per, 3), "bulbs": bulbs, "wire": wire}


def build():
    S = [strand(*l) for l in loops()]
    return {"what": "xmas_strands.py: the house's C7 window loops (Unity world), docs/XMAS-LIGHTS.md", "pitch": PITCH,
            "colour_linear": [1.0, 0.53, 0.32], "colour_src": "film 5545 halo shoulder, 419 isolated bulbs (xmas_lights_check.py --film-extra)",
            "bulbs": sum(len(s["bulbs"]) for s in S), "strands": S}


def selftest():
    s = strand("U", "x", 10.0, 1, 0.0, 1.02, 0.0, 1.51, True)   # the measured upper loop
    assert len(s["bulbs"]) == round(2 * (1.02 + 1.51) / PITCH) == 24, len(s["bulbs"])
    d = [math.dist(a, b) for a, b in zip(s["bulbs"], s["bulbs"][1:])]
    assert all(abs(x - PITCH) < 0.03 or x < PITCH for x in d), d   # corners cut the chord
    assert all(abs(p[0] - 10.075) < 1e-6 for p in s["bulbs"]) and s["normal"] == [1, 0, 0]
    assert min(p[1] for p in s["wire"]) < -0.005   # the bottom run sags
    print("xmas_strands selftest ok")


if __name__ == "__main__":
    if "--selftest" in sys.argv: selftest(); sys.exit(0)
    J = build(); OUT.parent.mkdir(parents=True, exist_ok=True); OUT.write_text(json.dumps(J))
    print(f"xmas_strands: {len(J['strands'])} loops, {J['bulbs']} C7s at {PITCH} m -> {OUT.relative_to(ROOT)}")
