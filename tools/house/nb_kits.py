"""nb_kits: the kit entries of the neighbourhood manifest (Oct 20 2026), written into spec/neighborhood.json (parcels[].kit, kit_auto,
kit_palette, kit_log). Every number below names its source; nb_house.py builds from the manifest only.

Sources (evidence ladder, RESUME section 2): F = film frame (camera solved: tools/house/nb_film_camera.py, film 11581, rms 11 px),
L = ISGS 2022 lidar nDSM (re-registered Oct 20: nb_evidence.py; profiles in kit_log), C = Cook County 2022 footprint, O = OSM,
G = period guess (style kit), confidence per lot. Spec metres, +x toward Lincoln Ave; heights over the lot's own grade.
  python3 tools/house/nb_kits.py
"""
import json
import math
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
P = ROOT / "spec/neighborhood.json"

# shared paint / material colours (sRGB 0-1); NB_<set>_<name> in both Blender and Unity
PALETTE = {
    "greyblue": [0.42, 0.50, 0.60],   # the Murphys' clapboard: film 11581/11556 under warm porch light read B/R 1.04-1.14 (a neutral grey reads ~0.6): a slate blue
    "white": [0.90, 0.89, 0.85], "cream": [0.88, 0.83, 0.70], "pale_yellow": [0.86, 0.80, 0.58], "sage": [0.58, 0.63, 0.53],
    "brown": [0.30, 0.22, 0.16], "slate": [0.30, 0.31, 0.33], "charcoal": [0.20, 0.21, 0.22], "red": [0.62, 0.36, 0.28],
    "clayred": [0.62, 0.32, 0.22], "stone": [0.66, 0.64, 0.60], "porchgrey": [0.45, 0.46, 0.46], "black": [0.04, 0.04, 0.045],
    "darkgreen": [0.10, 0.20, 0.14], "shuttergreen": [0.16, 0.34, 0.20], "darkblue": [0.12, 0.17, 0.26], "ivory": [0.86, 0.84, 0.77],
    "darkred": [0.35, 0.10, 0.09], "lampgreen": [0.05, 0.085, 0.07], "frostgrey": [0.52, 0.53, 0.56],   # the Murphys' roof reads pale grey in 11581 (frost / moonlight): a light grey shingle, by eye
      # the street lamps (film 3297/9511: very dark green cast iron)
}


def W(face, at, sill, h, w, typ, **k):
    d = {"face": face, "at": round(at, 3), "sill": sill, "h": h, "w": w, "type": typ}; d.update(k); return d


def murphys():
    """lot_B0, the Murphys (film 11551-11636 night; no day frame of it in film_index). Foursquare, 2.5 storeys, hip roof + hip dormers."""
    zc = 11.65   # C: main block z 5.1-18.2 (centre 11.65); the film's bays read 0.55 m to +z of it (camera/registration: kit_log)
    fl1, fl2 = 1.15, 4.45   # F: 1st-floor heads 3.84-3.97 and 2nd-floor sills 5.36 (refit camera); 11556: a tall flight to the porch
    win = []
    # front (-x), 2nd floor: three bays, film back-projection z 7.93-9.48 / 11.49-12.98 / 14.93-16.45 (incl. casings), centred on zc
    for at, typ, lit in ((zc - 3.5, "dh11", False), (zc, "dh_diamond", True), (zc + 3.5, "dh11", True)):
        win.append(W("-x", at, 5.45, 1.32, 1.00 if typ == "dh11" else 0.90, typ, xmas=at >= zc - 0.1, _lit=lit))
    # front, 1st floor under the porch (film 11581 + close-up 11556): French doors L, leaded window, front door, lamp-lit window, French doors R
    win += [W("-x", zc - 3.6, fl1, 2.60, 1.20, "french", _lit=True), W("-x", zc - 0.75, 2.85, 1.00, 1.20, "picture_diamond", _lit=True),
            W("-x", zc + 0.55, fl1, 2.40, 0.90, "door", _lit=True), W("-x", zc + 1.85, 2.30, 1.50, 1.30, "dh11", _lit=True),
            W("-x", zc + 3.6, fl1, 2.60, 1.25, "french", _lit=True)]
    # sides and rear: G (the +z side is in 11581 at a grazing angle: two upper windows, ground-floor bay not seen clearly)
    for face in ("+z", "-z"):
        for at in (66.6, 70.2, 74.6): win.append(W(face, at, 5.45, 1.32, 0.95, "dh11", _lit=face == "+z" and at < 67))
        for at in (66.6, 71.0, 75.2): win.append(W(face, at, 1.95, 1.70, 1.00, "dh11"))
    for at in (zc - 2.6, zc + 2.6):
        win.append(W("+x", at, 5.45, 1.32, 0.95, "dh11")); win.append(W("+x", at, 1.95, 1.70, 1.00, "dh11"))
    lit = [i for i, w in enumerate(win) if w.pop("_lit", False)]
    dw = lambda: [{"off": -0.6, "w": 1.0, "h": 0.64, "sill": 1.21, "type": "casement_diamond"}, {"off": 0.6, "w": 1.0, "h": 0.64, "sill": 1.21, "type": "casement_diamond"}]
    return {
        "style": "foursquare", "cladding": "clapboard", "roof_mat": "roof_asphalt", "foundation_mat": "concrete", "foundation_h": 0.75,
        "palette": {"wall": "greyblue", "trim": "white", "sash": "white", "roof": "frostgrey", "door": "darkblue", "porch_floor": "porchgrey",
                    "found": "stone", "shutter": "black", "brick": "red", "lattice": "white", "gutter": "white"},
        "blocks": [{"x": [63.6, 78.2], "z": [5.1, 18.2], "plate": 7.44, "roof": "hip", "pitch": 31.8, "overhang": 0.55,
                    "_src": "C footprint (main block; porch x 60.6-63.6 in front of it, O front walk ends at the door x 63.7); F camera fit (corners + far kerb): eave edge "
                            "7.10 +-0.94, ridge 11.53 +-0.9 -> pitch 31.8 (ridge 11.5; C 11.1, L apex 10.9-11.1 agree within 1 sd). DISAGREES: L roof 6.0 at the wall line "
                            "(kept the film; 0.5 m lidar pixels smear the eave edge with ground): kit_log",
                    "xmas_eave": [[-1, 0, 0], [0, 0, 1]]}],
        "windows": win, "lit": {"windows": lit},
        "dormers": [{"face": "-x", "at": zc, "w": 3.6, "h": 2.0, "setback": 1.2, "depth": 3.0, "roof": "hip", "windows": dw(),
                     "_src": "F 11581: two diamond-lattice lights, face z 10.9-13.4 back-projected at setback 1.2"},
                    {"face": "+x", "at": zc, "w": 3.6, "h": 2.0, "setback": 1.2, "depth": 3.0, "roof": "hip", "windows": [dict(x, type="dh11") for x in dw()], "_src": "L rear plateau 9.9 at z 10-13"},
                    {"face": "+z", "at": 70.9, "w": 3.6, "h": 2.0, "setback": 1.2, "depth": 3.0, "roof": "hip", "windows": [dict(x, type="dh11") for x in dw()], "_src": "L side plateau 10.7 across z at x 70.8"},
                    {"face": "-z", "at": 70.9, "w": 3.6, "h": 2.0, "setback": 1.2, "depth": 3.0, "roof": "hip", "windows": [dict(x, type="dh11") for x in dw()], "_src": "L (as +z)"}],
        "porch": {"x": [60.6, 63.6], "z": [6.2, 17.4], "floor": fl1, "edge": 4.17, "pitch": 14, "overhang": 0.30,
                  "columns": [6.5, 10.0, 13.35, 16.8], "rail": 0.80, "piers": "paint",
                  "steps": {"at": zc, "w": 2.9, "risers": 6, "iron": True}, "lamp": [63.55, zc + 1.12], "xmas_eave": True, "xmas_rail": True,
                  "_src": "C porch x 60.6-63.6, z 6.05-17.9; F 11581 four columns at z 7.07/10.55/13.9/17.33 (-0.55 to the house's axis), roof edge 3.56 (fit); "
                          "11556: five risers between square newels, a black iron handrail in the middle, white rail with square balusters"},
        "chimneys": [{"x": 72.6, "z": 15.6, "w": 0.75, "d": 0.62, "top": 12.1, "from": 5.0, "_src": "F 11581: a dark stack behind the right roof slope (by eye); G size"}],
        "garages": [{"x": [83.9, 92.85], "z": [-1.9, 9.15], "plate": 2.7, "roof": "hip", "pitch": 28, "door_face": "-x", "door": [3.65, 5.0],
                     "_src": "C outbuilding (ridge 5.9), O drive at z 3.1-4.2 (2022). It is at the house's LEFT seen from Lincoln; the white garage at the right edge of 11581 is lot_B+1's"}],
    }


def b_minus1():
    """lot_B-1 (film-left of the Murphys in 11576-11586: white clapboard 2-storey with a front gable): L ridge 9.6 along x, x 61.5-75.5."""
    z0, z1 = -21.8, -10.4; zc = (z0 + z1) / 2; win = []
    for at in (zc - 3.0, zc, zc + 3.0): win.append(W("-x", at, 4.30, 1.45, 0.90, "dh66", shutters=True))
    for at in (zc - 3.0, zc + 3.0): win.append(W("-x", at, 1.50, 1.60, 1.00, "dh66", shutters=True))
    win.append(W("-x", zc, 0.9, 2.1, 0.95, "door"))
    for face in ("+z", "-z"):
        for at in (65.0, 69.0, 73.0): win += [W(face, at, 4.3, 1.4, 0.9, "dh66"), W(face, at, 1.5, 1.6, 0.95, "dh66")]
    return {"style": "gable-front colonial", "cladding": "clapboard", "roof_mat": "roof_asphalt", "foundation_h": 0.6,
            "palette": {"wall": "white", "trim": "white", "roof": "charcoal", "shutter": "black", "door": "darkred", "porch_floor": "porchgrey", "found": "stone"},
            "blocks": [{"x": [62.8, 76.0], "z": [z0, z1], "plate": 6.1, "roof": "gable_x", "pitch": 31, "overhang": 0.40,
                        "_src": "C 60.6-78.3 x -21.8..-10.4; L ridge 9.6 from x 61.5 to 75.5 at z -16 (gable to the street), eaves 6.0-6.3"}],
            "windows": win, "lit": {"windows": [1, 3]},
            "porch": {"x": [60.6, 62.8], "z": [z0 + 0.3, z1 - 0.3], "floor": 0.6, "edge": 3.2, "pitch": 12, "columns": [z0 + 0.5, zc - 1.3, zc + 1.3, z1 - 0.5], "rail": 0.8,
                      "steps": {"at": zc, "w": 1.6, "risers": 3}, "_src": "C front strip x 60.6-62.8; G porch (11581 left edge: a low roof across the front)"},
            "chimneys": [{"x": 70.0, "z": z0 + 0.4, "w": 0.6, "d": 0.8, "top": 10.4, "from": 1.0}],
            "garages": [{"x": [75.8, 85.1], "z": [-30.5, -21.9], "plate": 2.7, "roof": "hip", "pitch": 26, "door_face": "-x", "door": [-26.2, 5.0], "_src": "C outbuilding"}]}


def b_plus1():
    """lot_B+1 (film-right of the Murphys: a hipped roof and a white garage, 11576-11586 right edge). L hip apex 10.2 at (69.5, 46.5)."""
    z0, z1 = 38.5, 54.6; zc = (z0 + z1) / 2; win = []
    for at in (zc - 6.0, zc - 3.0, zc, zc + 3.0, zc + 6.0): win.append(W("-x", at, 4.2, 1.45, 0.95, "dh66", shutters=True))
    for at in (zc - 6.0, zc - 3.6, zc + 3.6, zc + 6.0): win.append(W("-x", at, 1.4, 1.65, 1.0, "dh66", shutters=True))
    win.append(W("-x", zc, 0.75, 2.1, 1.0, "door"))
    for face in ("+z", "-z"):
        for at in (66.5, 71.5): win += [W(face, at, 4.2, 1.4, 0.9, "dh66"), W(face, at, 1.4, 1.6, 0.95, "dh66")]
    return {"style": "Colonial Revival, side-hipped", "cladding": "clapboard", "roof_mat": "roof_asphalt", "foundation_h": 0.55,
            "palette": {"wall": "cream", "trim": "white", "roof": "slate", "shutter": "black", "door": "black", "found": "stone", "porch_floor": "porchgrey"},
            "blocks": [{"x": [63.5, 75.0], "z": [z0, z1], "plate": 6.1, "roof": "hip", "pitch": 31, "overhang": 0.45,
                        "_src": "C 60.3-81.1 x 38.5-55.0; L hip apex 10.2 at x 69.5, eaves ~6"},
                       {"x": [75.0, 81.0], "z": [44.2, 50.85], "plate": 3.3, "roof": "hip", "pitch": 22, "overhang": 0.3, "_src": "C rear wing; L 4.5"}],
            "windows": win, "lit": {"windows": [9]},
            "porch": {"x": [60.3, 63.5], "z": [zc - 3.0, zc + 3.0], "floor": 0.75, "edge": 3.3, "pitch": 12, "columns": [zc - 2.8, zc - 1.0, zc + 1.0, zc + 2.8], "rail": 0.8,
                      "steps": {"at": zc, "w": 1.8, "risers": 4}, "_src": "L porch roof 4.3 at x 60.3-63.5 (z 40-49 seen, trees beyond); G centred entry porch"},
            "chimneys": [{"x": 69.5, "z": z0 + 0.3, "w": 0.8, "d": 0.6, "top": 10.8, "from": 1.0}],
            "garages": [{"x": [83.4, 91.7], "z": [31.3, 42.0], "plate": 2.8, "roof": "hip", "pitch": 26, "door_face": "-x", "door": [36.6, 5.2],
                         "_src": "C outbuilding; F 11581 right edge: white garage door with horizontal panels"}]}


def a_minus1():
    """lot_A-1 (film-right of our house: 1471, 3297, 6399, 9511): white clapboard, dark-green shutters, side-gabled 2.5 storeys with a dormer,
    close to the street; L ridge 10.4-10.8 (main), a lower 2-storey front section ~8 m at x 0-8."""
    z0, z1 = -38.0, -24.3; win = []
    # main block's street face shows only z -29.6..-24.3 beside the front wing: door + one bay; the wing carries three bays
    win += [W("+x", -27.0, 4.1, 1.45, 0.95, "dh66", shutters=True), W("+x", -25.4, 1.2, 1.65, 0.9, "dh66", shutters=True), W("+x", -27.6, 0.5, 2.1, 1.0, "door")]
    for at in (-36.0, -33.75, -31.5): win += [W("+x", at, 4.1, 1.45, 0.95, "dh66", block=1, shutters=True), W("+x", at, 1.2, 1.65, 1.0, "dh66", block=1, shutters=True)]
    for at in (-9.0, -5.5, -2.0): win += [W("+z", at, 4.1, 1.45, 0.9, "dh66", shutters=True), W("+z", at, 1.2, 1.6, 0.95, "dh66", shutters=True)]
    for at in (3.0, 6.0): win += [W("+z", at, 4.1, 1.4, 0.9, "dh66", block=1, shutters=True), W("+z", at, 1.2, 1.5, 0.95, "dh66", block=1, shutters=True)]
    return {"style": "Colonial Revival, side-gabled", "cladding": "clapboard", "roof_mat": "roof_asphalt", "foundation_h": 0.5,
            "palette": {"wall": "white", "trim": "white", "roof": "charcoal", "shutter": "shuttergreen", "door": "black", "found": "stone"},
            "blocks": [{"x": [-12.5, 0.5], "z": [z0, z1], "plate": 6.2, "roof": "gable_z", "pitch": 33, "overhang": 0.35,
                        "_src": "C 437 m2 (L-shaped, rear wings to x -19.7); L ridge 10.4-10.8 along z at x -5 (z -36..-29)"},
                       {"x": [0.5, 8.2], "z": [-37.9, -29.6], "plate": 6.0, "roof": "hip", "pitch": 18, "overhang": 0.35, "_src": "C front part to x 8.27; L ~8 m"}],
            "windows": win, "lit": {"windows": [1, 3]},
            "dormers": [{"face": "+x", "at": -27.0, "w": 1.6, "h": 1.5, "setback": 0.8, "depth": 2.0, "roof": "gable", "windows": [{"off": 0, "w": 0.75, "h": 0.95, "sill": 0.5, "type": "dh66"}],
                         "_src": "F 6399 right edge: a gabled dormer on the street slope"}],
            "chimneys": [{"x": -6.0, "z": z1 - 0.5, "w": 0.9, "d": 0.6, "top": 11.6, "from": 1.0}]}


def a_plus1():
    """lot_A+1 (film-left of our house beyond the garage: 1886/1891): cream stucco with a red clay-tile hip roof (a turret-like steep
    corner roof is visible there, possibly lot_A+2's), 2 storeys; L hip ridge 9.8 at x 1.5-4.5, z 40-44."""
    z0, z1 = 36.7, 47.7; win = []
    for at in (38.6, 41.0, 43.6, 46.0): win.append(W("+x", at, 4.0, 1.4, 0.9, "casement", leaves=2, casing=True))
    for at in (38.6, 46.0): win.append(W("+x", at, 1.0, 1.7, 1.2, "casement", leaves=2, casing=True))
    win.append(W("+x", 42.25, 0.45, 2.1, 1.0, "door", block=1))
    for face in ("-z", "+z"):
        for at in (1.0, 6.0): win += [W(face, at, 4.0, 1.35, 0.9, "casement", leaves=2, casing=True), W(face, at, 1.0, 1.6, 0.95, "casement", leaves=2, casing=True)]
    return {"style": "Mediterranean / Prairie stucco, hip roof", "cladding": "stucco", "roof_mat": "roof_clay", "foundation_h": 0.45,
            "palette": {"wall": "cream", "trim": "brown", "sash": "brown", "roof": "clayred", "door": "brown", "found": "stone"},
            "blocks": [{"x": [-2.0, 10.8], "z": [z0, z1], "plate": 6.0, "roof": "hip", "pitch": 30, "overhang": 0.55,
                        "_src": "C 260 m2 (rear wing to x -9.6, z 33.1); L hip ridge 9.8"},
                       {"x": [10.8, 12.6], "z": [40.3, 44.2], "plate": 3.0, "roof": "hip", "pitch": 25, "overhang": 0.3, "_src": "C front projection (vestibule)"},
                       {"x": [-9.6, -2.0], "z": [33.1, 41.0], "plate": 5.6, "roof": "hip", "pitch": 30, "overhang": 0.45, "_src": "C rear wing"}],
            "windows": win, "lit": {"windows": [2]},
            "chimneys": [{"x": 4.0, "z": z1 - 0.4, "w": 0.6, "d": 0.8, "top": 10.6, "from": 1.0}]}


STYLES3 = [("brick", "roof_asphalt", {"wall": "red", "trim": "white", "roof": "slate", "shutter": "black", "brick": "red"}),
           ("clapboard", "roof_asphalt", {"wall": "white", "trim": "white", "roof": "charcoal", "shutter": "black"}),
           ("stucco", "roof_asphalt", {"wall": "ivory", "trim": "brown", "roof": "slate", "shutter": "darkgreen"}),
           ("clapboard", "roof_asphalt", {"wall": "pale_yellow", "trim": "white", "roof": "slate", "shutter": "black"}),
           ("brick", "roof_asphalt", {"wall": "red", "trim": "ivory", "roof": "charcoal", "shutter": "darkgreen", "brick": "red"}),
           ("shingle", "roof_asphalt", {"wall": "brown", "trim": "white", "roof": "charcoal", "shutter": "black"}),
           ("clapboard", "roof_asphalt", {"wall": "sage", "trim": "white", "roof": "slate", "shutter": "black"}),
           ("stucco", "roof_clay", {"wall": "cream", "trim": "brown", "roof": "clayred", "shutter": "brown"})]


def auto_kit(e):
    """Tier 3: the main county footprint's minimum-area rectangle, the county ridge, a hashed period style; LOD1 (stand-in) only."""
    import sys; sys.path.insert(0, str(ROOT / "tools/house")); from nb_house import obb
    b = next((b for b in e["buildings"] if b["main"]), None)
    if not b or b["area_m2"] < 60: return None
    u0, u1, v0, v1, yaw = obb([tuple(p) for p in b["footprint_spec"]])
    c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    # build axis-aligned in the rectangle's own frame (u -> x, v -> z), then nb_house turns it by yaw about the origin
    ridge = min(12.5, max(6.0, b["ridge_m"])); two = ridge > 8.0
    W_, D_ = u1 - u0, v1 - v0; o = 0.4
    pitch = 32; plate = 6.0 if two else 3.0
    rise = (min(W_, D_) / 2 + o) * math.tan(math.radians(pitch)); plate = max(3.0, min(plate, ridge - rise + o * math.tan(math.radians(pitch))))
    h = zlib.crc32(e["id"].encode()); clad, roof, pal = STYLES3[h % len(STYLES3)]
    front = "-x" if e["side"] == "across_lincoln" else "+x"
    # which local face looks toward Lincoln: the rectangle's +-u or +-v axis closest to the street direction
    want = (-1, 0) if front == "-x" else (1, 0)
    axes = {"-x": (-c, -s), "+x": (c, s), "-z": (s, -c), "+z": (-s, c)}
    ff = max(axes, key=lambda k: axes[k][0] * want[0] + axes[k][1] * want[1])
    span = (v0, v1) if ff in ("-x", "+x") else (u0, u1); L = span[1] - span[0]; n = max(2, int(L / 2.8))
    win = []
    for i in range(n):
        at = span[0] + L * (i + 0.5) / n
        if two: win.append(W(ff, at, 4.0, 1.4, 0.95, "dh66"))
        win.append(W(ff, at, 1.0, 1.6, 1.0, "dh66" if i != n // 2 else "door") if i != n // 2 else W(ff, at, 0.5, 2.1, 1.0, "door"))
    return {"style": f"Tier 3 stand-in ({clad})", "cladding": clad, "roof_mat": roof, "foundation_h": 0.5, "palette": dict(pal, found="stone"),
            "yaw_deg": round(yaw, 2), "blocks": [{"x": [round(u0, 2), round(u1, 2)], "z": [round(v0, 2), round(v1, 2)], "plate": round(plate, 2),
                                                  "roof": "hip" if max(W_, D_) / min(W_, D_) < 1.35 else ("gable_x" if W_ > D_ else "gable_z"), "pitch": pitch, "overhang": o}],
            "windows": win, "_src": "C footprint rectangle (min-area) + C ridge; style hashed from STYLES3 (G, low)"}


TIERS = {
    "2": "walkable hero: lot_A-1, lot_A+1, lot_B-1, lot_B0 (Murphys), lot_B+1 (nb_house LOD0 + LOD1, box colliders), Lincoln Ave + kerbs, sidewalks, parkways, "
         "drives, walks, snow banks (Street.glb, mesh colliders), acorn lamps, lidar trees",
    "3": "stand-ins built now: the 10 other manifest lots (A-3..A+6, B-3..B+4, z ~ -150..+115) as kit LOD1 from the county footprint rectangle + ridge, "
         "hashed period style, not reachable. PLAN to finish: (a) extend nb_manifest's rows to every parcel fronting Lincoln within z -150..150 and the two "
         "junctions (Lincoln's fork at z -67, Pine St at z 112): about 14 more lots; complex footprints (lot_A-2/A-3, 420 m2 L-shapes) as 2-3 rectangles, "
         "not one box (they read as barns in the aerial); (b) facade cards: none needed at LOD1 (windows are framed quads); (c) the WinterNeighborhood "
         "(1410 renderers): SpecGreybox.Neighborhood switches its street, sidewalks, kerbs, houses, trees and snowy-lot ground off inside x -60..100, |z| < 150; "
         "keep its utility wires only where the film shows them (11581: overhead wires, top left); then delete the rest with Tier 4; (d) the photo dome "
         "(R 75 m, the windows' view) stands inside Tier 3: outside it must go (or grow to R ~220 m as a sky-only dome) and Tier 4 takes the horizon; "
         "(e) the inactive WinterBackdrop_NightHouse card (wrong house, film 5546) is deleted once the Murphys are in; (f) K (PropertyView) already hides "
         "everything off the lot, the Neighborhood root included",
    "4": "PLAN: a treeline ring at 160-220 m (alpha tree-silhouette cards from the lidar canopy height, 2 rows, varied), a flat overcast/clear sky (no hills: "
         "Winnetka is flat; DEVIATIONS 104), the dome's photo ground band hidden behind it",
}
BUDGETS = {
    "_note": "per view from the street (Tier 2 sidewalk, adult eye); triangles after LOD selection; measured from the generated files (build_stats.json); "
             "frame-time slot: plug the Mac standalone baseline (perf_probe.sh) in at 'baseline_ms'",
    "frame_ms_target": 16.7, "baseline_ms": None, "neighbourhood_gpu_ms_target": 3.0,
    "tier2": {"houses_lod0_tris": 144219, "houses_lod0_tris_cap": 200000, "per_house_lod0_cap": 60000, "lod1_ratio": "4-5 % (target <= 10 %)",
              "street_tris": 8344, "lamp_tris_lod0": 1384, "lamps": 10, "c7_bulbs": 326,
              "trees": 58, "tree_lod0_tris": 120000, "tree_rule": "LOD0 (120k) only above 0.55 screen height = within ~20 m: at most ~4 at once from the sidewalk; "
              "LOD1 25k, LOD2 5k; if the M3 baseline is tight: LOD0 cut to 0.75 screen (12 m)",
              "draw_calls": "~10 per house LOD0 (one mesh, a submesh per shared material) x 5 + street 5 x 3 + lamps 2 x 10 + trees 2 x 58 = ~200 (SRP batcher: shared materials)"},
    "tier3": {"stand_ins": 10, "tris_total": 3464, "per_house": "270-520", "draw_calls": "~6 each (shared materials) = 60", "shadows": "on (cheap), off past 80 m"},
    "materials": "23 shared NB_* (one per set x colour) + 2 glass + lamp globe",
    "texture_memory": "10 sets x (1024^2 albedo BC1 0.7 MB + normal BC5 1.3 MB + mask BC7 1.3 MB) = ~33 MB with mips; bark sets shared with the yard",
    "lights": "10 lamp posts (point, no shadows, night) + porch lamp glows as emissive; HDRP serves <= 24 lights per frame: lamps culled past 60 m",
}


def main():
    man = json.loads(P.read_text()); man["kit_palette"] = PALETTE
    kits = {"lot_B0": (murphys(), "medium", "massing C+L, eave/porch heights + camera F 11581 (rms 11 px), facade bays F; sides/rear G"),
            "lot_B-1": (b_minus1(), "low-medium", "gable-front from L; white clapboard F (11581 left edge); windows G"),
            "lot_B+1": (b_plus1(), "low", "hip from L; colour/windows G (only its garage and an edge are in 11581)"),
            "lot_A-1": (a_minus1(), "low-medium", "white clapboard + green shutters F 6399; massing L/C simplified to two blocks"),
            "lot_A+1": (a_plus1(), "low", "cream stucco + red tile roof F 1886/1891 (edge views; may be lot_A+2's); hip from L")}
    n3 = 0
    for e in man["parcels"]:
        if e["id"] in kits:
            k, conf, why = kits[e["id"]]; e["kit"] = k; e["kit_confidence"] = conf; e["kit_basis"] = why; e["status"] = "kit"
        elif e["tier"] == 3:
            a = auto_kit(e)
            if a: e["kit_auto"] = a; e["status"] = "kit_auto"; n3 += 1
    man["kit_log"] = {
        "camera": "art/home_alone/references/neighborhood/data/film11581_camera.json (tools/house/nb_film_camera.py)",
        "lidar_fix_oct20": "step-1 nDSM was placed with the requested bbox; ArcGIS returned a widened extent (square pixels): trees ~45 m off, roofs on bare "
                           "ground. Re-fetched with the server extent (nb_evidence.py --fetch): footprint p25 now 5.3 m median (was 0.1).",
        "murphys_profiles": "x at z 11.6: 10.4-11.5 plateau x 64.5-76 (front+rear dormers into the hip); x at z 8: 6.0 at the front wall rising 0.74/m to 10.8 at x 70.5; "
                            "z at x 70.8: plateau 10.7 z 6.5-17 (side dormers); porch roof 4.0-4.4 at x 60-63",
        "murphys_eave": "film refit (with the far kerb line) eave edge 7.10 +-0.94 vs lidar ~6.0 at the wall line: the film is kept (evidence ladder); the lidar disposition: 0.5 m pixels at the eave mix roof and ground. Revisit: a second film camera (11626) or a day photo",
        "murphys_offset": "the film's facade bays read 0.55 m to +z of the footprint's centre (apex residual 30 px): kept on the footprint, bays centred (DEVIATIONS)",
        "garage_side": "the Murphys' 2022 outbuilding and drive are on the house's LEFT (-z) seen from Lincoln; step-1 notes said right",
    }
    man["tiers"] = TIERS; man["budgets"] = BUDGETS
    P.write_text(json.dumps(man, indent=1)); print("kits", len(kits), "tier-3 auto", n3)


if __name__ == "__main__":
    main()
