"""wet_check: the ground's wetness by weather sits in each state's band (walk notes Oct 19 08:48, 09:50, 12:11; DEVIATIONS 124).

Reads the built materials (Assets/Materials/Greybox/<name>.mat) and the textures they reference: per material the effective linear
albedo (texture mean x tint) and the smoothness distribution (mask alpha remapped, or the flat _Smoothness). Per state (Sunny =
film 1640: pale weathered asphalt, mostly dry, damp patches; Overcast: damper; Night = film 10162/10170: dark, wet, glinting):
  - the asphalt (street, drives, walk) inside the state's TARGET albedo and mean-smoothness band;
  - the concrete (sidewalks, kerbs) and the apron within BAND of the asphalt's mean smoothness, no darker than the asphalt and no
    brighter than CONCRETE_MAX x it (a dry slab beside wet asphalt is the jarring contrast of the notes), and wet patches (p95 >= P95);
  - the steps (one set, always wet) within BAND of the night asphalt's smoothness.

  uv run --with numpy --with pillow python -I tools/house/wet_check.py
"""
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image

A = Path(__file__).resolve().parents[2] / "unity/HomeAlone/Assets"
TARGET = {"Sunny": ((0.10, 0.30), (0.30, 0.55)), "Overcast": ((0.06, 0.18), (0.60, 0.80)), "Night": ((0.03, 0.12), (0.78, 0.95))}
BAND, P95, CONCRETE_MAX = 0.10, 0.85, 2.0
GUIDS = {}


def tex(guid):
    if not GUIDS:
        for m in A.rglob("Textures/**/*.meta"):
            g = re.search(r"^guid: (\w+)", m.read_text(errors="ignore"), re.M)
            if g: GUIDS[g.group(1)] = m.with_suffix("")
    return GUIDS.get(guid)


def stats(name):
    t = (A / f"Materials/Greybox/{name}.mat").read_text()
    f = lambda k: float(re.search(rf"- {k}: ([\d.eE+-]+)", t).group(1))
    g = lambda k: (re.search(rf"- {k}:\n\s+m_Texture: {{fileID: \d+(?:, guid: (\w+))?", t) or [None, None])[1]
    c = re.search(r"- _BaseColor: {r: ([\d.]+), g: ([\d.]+), b: ([\d.]+)", t)
    tint = np.array([float(x) for x in c.groups()]) ** 2.2                       # gamma colour -> linear
    alb = np.asarray(Image.open(tex(g("_BaseColorMap"))).convert("RGB").reduce(4), np.float32) / 255.0
    albedo = float(((alb ** 2.2).reshape(-1, 3).mean(0) * tint) @ [0.2126, 0.7152, 0.0722])
    mk = g("_MaskMap")
    if mk:
        a = np.asarray(Image.open(tex(mk)).reduce(4), np.float32)[..., 3] / 255.0
        s = f("_SmoothnessRemapMin") + (f("_SmoothnessRemapMax") - f("_SmoothnessRemapMin")) * a
    else:
        s = np.full(1, f("_Smoothness"))
    return albedo, float(s.mean()), float(np.percentile(s, 5)), float(np.percentile(s, 95))


def main():
    fails = 0
    def report(n, st, why):
        nonlocal fails
        fails += bool(why); print(f"{n:26s} albedo {st[0]:.3f}  smoothness mean {st[1]:.2f} (5-95% {st[2]:.2f}-{st[3]:.2f})  {'FAIL: ' + '; '.join(why) if why else 'PASS'}")
    def get(n):
        return stats(n) if (A / f"Materials/Greybox/{n}.mat").exists() else None
    night = None
    for state, ((a0, a1), (s0, s1)) in TARGET.items():
        print(f"-- {state}")
        asph = get(f"HiFi_ExtAsphalt_{state}")
        if asph is None: print(f"HiFi_ExtAsphalt_{state} MISSING (not built yet)"); fails += 1; continue
        report(f"HiFi_ExtAsphalt_{state}", asph, [w for w, bad in ((f"albedo outside {a0}-{a1}", not a0 <= asph[0] <= a1),
                                                                   (f"smoothness outside {s0}-{s1}", not s0 <= asph[1] <= s1)) if bad])
        if state == "Night": night = asph
        for kind in ("Concrete", "Apron"):
            n = f"HiFi_Ext{kind}_{state}"; c = get(n)
            if c is None: print(f"{n} MISSING"); fails += 1; continue
            report(n, c, [w for w, bad in (("smoothness off the asphalt's", abs(c[1] - asph[1]) > BAND), (f"no wet patches (p95 < {P95})", c[3] < P95),
                                           ("darker than the asphalt", c[0] < asph[0]), (f"over {CONCRETE_MAX}x the asphalt's albedo", c[0] > CONCRETE_MAX * asph[0])) if bad])
    st = get("HiFi_ExtStepStone")
    if st and night:
        print("-- steps (always wet)"); report("HiFi_ExtStepStone", st, ["smoothness off the night asphalt's"] if abs(st[1] - night[1]) > BAND else [])
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
