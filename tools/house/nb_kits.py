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
    # step 3 street life (by eye from the film; car paint is gloss: NB_car_* in Unity/nb_render)
    "policenavy": [0.07, 0.10, 0.20], "carblue": [0.20, 0.32, 0.55], "vanblue": [0.55, 0.64, 0.74], "chrome": [0.78, 0.78, 0.78],
    "palepink": [0.90, 0.72, 0.74],   # Marley's house in 1990 (film 1888, day, sunlit turret wall: R/G 1.23, G/B 1.03 = 6 % redder and a little bluer than our white portico in the same frame): pale rose
    "tyre": [0.03, 0.03, 0.03], "taillight": [0.55, 0.04, 0.03], "headlamp": [0.9, 0.9, 0.85], "hydrantred": [0.62, 0.07, 0.05],
}


def W(face, at, sill, h, w, typ, **k):
    d = {"face": face, "at": round(at, 3), "sill": sill, "h": h, "w": w, "type": typ}; d.update(k); return d


def murphys():
    """lot_B0, the Murphys (film 11551-11636 night; 3241 day, blurred). Foursquare, 2.5 storeys, hip roof + hip dormers.
    Step 3 (Oct 20): the house moved 0.55 m to +z (the film's bays and both eave corners read there: residuals eave_fl -22 px, eave_fr
    +22 px), the porch keeps the county's front and now starts at the house's left corner with the film's two left columns (11576), a
    taller front dormer, a 1-storey side bay at the +z front (11581 grazing), room cards behind the lit windows, the film's light layout."""
    zc = 12.2    # F: bays centred 0.55 m to +z of the county main block's centre (11.65); kit_log murphys_offset
    fl1 = 1.15   # F: 11556, a tall flight to the porch
    win = []
    # front (-x), 2nd floor: three bays; the left one unlit (blinds, 11581), the middle sheers (room 0), the right a half shade (room 2)
    for at, typ, lit, room in ((zc - 3.5, "dh11", False, 1), (zc, "dh_diamond", True, 0), (zc + 3.5, "dh11", True, 2)):
        win.append(W("-x", at, 5.45, 1.32, 1.00 if typ == "dh11" else 0.90, typ, xmas=at >= zc - 0.1, room=room, _lit=lit))
    # front, 1st floor under the porch (11581 + 11556): French doors L, leaded window, front door, lamp-lit window, French doors R (a tree)
    win += [W("-x", zc - 3.6, fl1, 2.60, 1.20, "french", xmas=True, room=1, _lit=True), W("-x", zc - 0.75, 2.85, 1.00, 1.20, "picture_diamond", room=0, _lit=True),
            W("-x", zc + 0.55, fl1, 2.40, 0.90, "door", xmas=True, room=1, _lit=True), W("-x", zc + 1.85, 2.30, 1.50, 1.30, "dh11", room=1, _lit=True),
            W("-x", zc + 3.6, fl1, 2.60, 1.25, "french", xmas=True, room=3, _lit=True)]
    # sides and rear: G (the +z side is in 11581 at a grazing angle: two upper windows; the lower front of that side is the bay, block 1)
    for face in ("+z", "-z"):
        for at in (66.6, 70.2, 74.6): win.append(W(face, at, 5.45, 1.32, 0.95, "dh11", _lit=face == "+z" and at < 67))
        for at in ((71.0, 75.2) if face == "+z" else (66.6, 71.0, 75.2)): win.append(W(face, at, 1.95, 1.70, 1.00, "dh11"))
    for at in (zc - 2.6, zc + 2.6):
        win.append(W("+x", at, 5.45, 1.32, 0.95, "dh11")); win.append(W("+x", at, 1.95, 1.70, 1.00, "dh11"))
    for at in (65.5, 67.3): win.append(W("+z", at, 1.25, 1.60, 0.90, "dh11", block=1, _lit=at < 66, room=1))
    lit = [i for i, w in enumerate(win) if w.pop("_lit", False)]
    dw = lambda h=0.64, sill=1.21: [{"off": -0.6, "w": 1.0, "h": h, "sill": sill, "type": "casement_diamond"}, {"off": 0.6, "w": 1.0, "h": h, "sill": sill, "type": "casement_diamond"}]
    shrub = lambda x, z, rx, rz, h, n: {"x": x, "z": z, "rx": rx, "rz": rz, "h": h, "bulbs": n}
    return {
        "style": "foursquare", "cladding": "clapboard", "roof_mat": "roof_asphalt", "foundation_mat": "concrete", "foundation_h": 0.75,
        "palette": {"wall": "greyblue", "trim": "white", "sash": "white", "roof": "frostgrey", "door": "darkblue", "porch_floor": "porchgrey",
                    "found": "stone", "shutter": "black", "brick": "red", "lattice": "white", "gutter": "white"},
        "blocks": [{"x": [63.6, 78.2], "z": [5.65, 18.75], "plate": 7.44, "roof": "hip", "pitch": 31.8, "overhang": 0.55,
                    "_src": "C footprint (main block x 63.6-78.2, z 5.1-18.2) moved +0.55 m in z to the film's bays and eave corners (DEVIATIONS); F camera "
                            "fit: eave edge 7.10 +-0.94, ridge 11.53 +-0.9 -> pitch 31.8 (C 11.1, L apex 10.9-11.1 agree within 1 sd). DISAGREES: L roof 6.0 at the "
                            "wall line (kept the film; 0.5 m lidar pixels smear the eave edge): kit_log",
                    "xmas_eave": [[-1, 0, 0]]},
                   {"x": [64.6, 68.2], "z": [18.75, 19.55], "plate": 3.5, "roof": "hip", "pitch": 25, "overhang": 0.3, "hidden_faces": ["-z"], "downspouts": False,
                    "_src": "F 11581 (grazing, one view, low): behind the porch's right end a lower plane with its own roof edge at ~3.6 m, x 64-68 on z 18.75 "
                            "(frame 1665-1765, y 435-530); depth 0.8 G. Not in the 2022 county footprint (post-1990 change or a bay under 1 m)"}],
        "windows": win, "lit": {"windows": lit},
        "dormers": [{"face": "-x", "at": zc, "w": 3.6, "h": 2.35, "setback": 1.2, "depth": 3.0, "roof": "hip", "windows": dw(0.80, 1.25),
                     "_src": "F 11581: two diamond-lattice lights; step 3: taller face (eave +0.35, lights 0.80 high) per the close-up sheet"},
                    {"face": "+x", "at": zc, "w": 3.6, "h": 2.0, "setback": 1.2, "depth": 3.0, "roof": "hip", "windows": [dict(x, type="dh11") for x in dw()], "_src": "L rear plateau 9.9 at z 10-13"},
                    {"face": "+z", "at": 70.9, "w": 3.6, "h": 2.0, "setback": 1.2, "depth": 3.0, "roof": "hip", "windows": [dict(x, type="dh11") for x in dw()], "_src": "L side plateau 10.7 across z at x 70.8"},
                    {"face": "-z", "at": 70.9, "w": 3.6, "h": 2.0, "setback": 1.2, "depth": 3.0, "roof": "hip", "windows": [dict(x, type="dh11") for x in dw()], "_src": "L (as +z)"}],
        "porch": {"x": [60.6, 63.6], "z": [5.65, 17.9], "floor": fl1, "edge": 4.17, "pitch": 14, "overhang": 0.30,
                  "columns": [5.95, 7.07, 10.55, 13.9, 17.33], "rail": 0.80, "piers": "paint",
                  "steps": {"at": zc, "w": 2.9, "risers": 6, "iron": True}, "lamp": [63.55, zc + 1.12], "xmas_eave": "wrap", "xmas_rail": "swag",
                  "_src": "C porch x 60.6-63.6, z 6.05-17.9; F 11581 columns at z 7.07/10.55/13.9/17.33, 11576 a second column at the left corner (5.95); the "
                          "porch roof's left end + downspout at z ~5.6 (frame 785-815): the porch starts at the house's left corner, the roof overhangs past it; "
                          "11556: six risers between square newels, a black iron handrail in the middle"},
        "chimneys": [{"x": 72.6, "z": 16.15, "w": 0.75, "d": 0.62, "top": 12.1, "from": 5.0, "_src": "F 11581: a dark stack behind the right roof slope (by eye); G size"}],
        "garages": [{"x": [83.9, 92.85], "z": [-1.9, 9.15], "plate": 2.7, "roof": "hip", "pitch": 28, "door_face": "-x", "door": [3.65, 5.0],
                     "_src": "C outbuilding (ridge 5.9), O drive at z 3.1-4.2 (2022). It is at the house's LEFT seen from Lincoln; the white garage at the right edge of 11581 is lot_B+1's"}],
        "xmas": {"_src": "F 11581/11576 (night): main eave front only (the +z side eave is dark), a line along the wall over the porch roof (frame 1100-1560, "
                         "y ~340), the middle and right upper windows outlined, the porch eave turning the right corner, dense swags on the rails, the "
                         "French doors and the front door outlined, lit foundation shrubs both sides of the steps and a big lit shrub at the left corner",
                 "strings": [{"pts": [[63.54, 5.38, 9.4], [63.54, 5.38, 16.0]], "step": 0.2, "sag": 0.03}],
                 "shrubs": [shrub(58.6, 5.2, 0.65, 0.75, 1.15, 70), shrub(60.0, 7.5, 0.5, 0.9, 1.2, 50), shrub(60.0, 9.6, 0.5, 0.8, 1.1, 45),
                            shrub(60.0, 14.8, 0.5, 0.9, 1.2, 50), shrub(60.0, 16.9, 0.5, 0.8, 1.1, 45)]},
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
    """lot_A+1 = Old Man Marley's house (user, Oct 20: the neighbour LEFT of ours seen from the street = +z = lot_A+1). Shingle Style:
    2.5 storeys of shakes over a red brick/stone base, an octagonal turret with a tall conical roof at the front, hip wings with deep
    flared eaves, eyebrow hoods over upper windows, a recessed entry with dark round columns up stone steps, a tall brick chimney on the
    left (+z) wing, a hip dormer on the right wing, dark green trim.
    Evidence: F 1888/1884/1891 (day, across Lincoln: the turret's conical roof and the wings' roofs RED in 1990, the turret's upper walls
    PALE ROSE; a chimney on the left), L (ISGS 2022 nDSM: a 12.5 m peak at x 10-11, z 37-38 over the footprint's octagonal corners = the
    turret; the main hip plateau 9.8 at x 3-5), C (2022 footprint: main x -2..10.8, z 36.75..47.6; the octagon's diagonals (10.79, 39.43)-
    (11.21, 40.26) and (10.78, 36.83)-(9.34, 35.52); the front projection x 10.8..12.64, z 40.25..43.04 = the entry), the user's modern photo
    description (today: brown shakes, grey roofs). 1990 colours from the film are used; today's are kept as palette_today (decision)."""
    win = []
    for at in (44.3, 46.4):   # left (+z) wing, street face
        win += [W("+x", at, 4.0, 1.30, 0.95, "dh91", hood="eyebrow"), W("+x", at, 1.35, 1.75, 1.0, "dh91")]
    win.append(W("+x", 41.65, 4.0, 1.20, 1.50, "casement", leaves=3, casing=True, hood="eyebrow"))   # over the entry
    win.append(W("+x", 41.65, 0.90, 2.15, 1.00, "door"))                                            # the door at the back of the entry
    win.append(W("+x", 41.65, 0.90, 2.25, 2.10, "opening", block=2, columns=2, reveal=1.84))      # the entry's mouth (block 2's street face)
    for face in ("+z", "-z"):
        for at in (1.5, 6.5): win += [W(face, at, 4.0, 1.3, 0.9, "dh91"), W(face, at, 1.35, 1.6, 0.95, "dh91")]
    tw = [{"k": 0, "sill": 4.0, "h": 1.25, "w": 0.85, "type": "dh11"}, {"k": 0, "sill": 1.35, "h": 1.7, "w": 0.85, "type": "dh11"},
          {"k": 1, "sill": 4.0, "h": 1.25, "w": 0.8, "type": "dh11"}, {"k": 7, "sill": 4.0, "h": 1.25, "w": 0.8, "type": "dh11"},
          {"k": 1, "sill": 1.35, "h": 1.7, "w": 0.8, "type": "dh11"}, {"k": 7, "sill": 1.35, "h": 1.7, "w": 0.8, "type": "dh11"}]
    tw += [{"k": k, "sill": 6.55, "h": 0.85, "w": 0.75, "type": "casement"} for k in (0, 1, 7, 2, 6)]   # the band above the wings' roofs (F 1888)
    return {"style": "Shingle Style (Marley's house)", "cladding": "shingle", "roof_mat": "roof_asphalt", "foundation_mat": "brick", "foundation_h": 0.9,
            "palette": {"wall": "palepink", "trim": "white", "sash": "white", "roof": "clayred", "door": "darkgreen", "found": "red", "brick": "red", "gutter": "white",
                        "_src": "film 1888 (1990): pale rose walls, white cornice and sashes, red roofs (sampled; nb_kits PALETTE palepink)"},
            "palette_today": {"wall": "brown", "trim": "darkgreen", "sash": "darkgreen", "roof": "slate", "gutter": "darkgreen", "_src": "the user's modern photo (late winter): warm brown cedar shakes, dark green trim, grey shingle roofs"},
            "blocks": [{"x": [-1.95, 10.8], "z": [36.75, 47.6], "plate": 5.9, "roof": "hip", "pitch": 37, "overhang": 0.55, "flare": 0.7,
                        "_src": "C main rectangle; L hip plateau 9.8 (built 9.6); flared eaves (Shingle Style, user photo)"},
                       {"x": [-9.6, -1.95], "z": [33.1, 47.7], "plate": 5.6, "roof": "hip", "pitch": 37, "overhang": 0.5, "flare": 0.6, "_src": "C rear wing; L tree-covered (G height)"},
                       {"x": [10.8, 12.64], "z": [40.25, 43.04], "plate": 3.1, "roof": "hip", "pitch": 30, "overhang": 0.35, "hidden_faces": ["-x"], "downspouts": False, "collider_top": 0.9,
                        "_src": "C front projection = the recessed entry (user photo: a recessed porch with dark round columns, stone steps)"}],
            "windows": win, "lit": {"windows": [0, 4]},
            "turrets": [{"x": 8.55, "z": 37.9, "r": 2.4, "plate": 7.8, "peak": 12.5, "overhang": 0.45, "flare": 0.5, "windows": tw,
                         "_src": "C octagonal corners (r 2.4 to the face middles, the front face 15 cm proud of the main wall); L peak 12.5 m at x 10-11, z 37-38; F 1888 the tall red cone over a pale windowed band that rises above the wings' red roofs (plate 7.8: G from the frame's proportions)"}],
            "dormers": [{"face": "+x", "block": 1, "at": 34.9, "w": 1.9, "h": 1.6, "setback": 0.6, "depth": 2.2, "roof": "hip",
                         "windows": [{"off": 0, "w": 1.0, "h": 0.8, "sill": 0.6, "type": "dh11"}], "_src": "the user's photo: a hip dormer on the right wing (G position)"}],
            "steps": [{"x": [12.64, 14.04], "z": [40.6, 42.7], "top": 0.9, "n": 5, "climb": -1, "_src": "the user's photo: stone steps up to the entry"}],
            "chimneys": [{"x": 4.0, "z": 47.25, "w": 0.7, "d": 0.6, "top": 11.6, "from": 1.0, "_src": "F 1888: a chimney on the left (+z) wing; the user's photo: tall red brick"}]}


STYLES3 = [("brick", "roof_asphalt", {"wall": "red", "trim": "white", "roof": "slate", "shutter": "black", "brick": "red"}),
           ("clapboard", "roof_asphalt", {"wall": "white", "trim": "white", "roof": "charcoal", "shutter": "black"}),
           ("stucco", "roof_asphalt", {"wall": "ivory", "trim": "brown", "roof": "slate", "shutter": "darkgreen"}),
           ("clapboard", "roof_asphalt", {"wall": "pale_yellow", "trim": "white", "roof": "slate", "shutter": "black"}),
           ("brick", "roof_asphalt", {"wall": "red", "trim": "ivory", "roof": "charcoal", "shutter": "darkgreen", "brick": "red"}),
           ("shingle", "roof_asphalt", {"wall": "brown", "trim": "white", "roof": "charcoal", "shutter": "black"}),
           ("clapboard", "roof_asphalt", {"wall": "sage", "trim": "white", "roof": "slate", "shutter": "black"}),
           ("stucco", "roof_clay", {"wall": "cream", "trim": "brown", "roof": "clayred", "shutter": "brown"})]


def _lincoln():
    d = json.loads((ROOT / "art/home_alone/references/neighborhood/data/spec_frame.json").read_text())
    return [r["pts"] for r in d["roads"] if r["name"] == "Lincoln Avenue"]


LINCOLN = None


def toward_lincoln(x, z):
    """Unit (dx, dz) from (x, z) to the nearest point of Lincoln's OSM centreline (handles the bend at z -110 and the fork at -67)."""
    global LINCOLN
    LINCOLN = LINCOLN or _lincoln(); best = None
    for r in LINCOLN:
        for (ax, az), (bx, bz) in zip(r, r[1:]):
            dx, dz = bx - ax, bz - az; t = max(0.0, min(1.0, ((x - ax) * dx + (z - az) * dz) / (dx * dx + dz * dz + 1e-9)))
            px, pz = ax + t * dx, az + t * dz; dd = math.hypot(px - x, pz - z)
            if best is None or dd < best[0]: best = (dd, (px - x) / max(dd, 1e-6), (pz - z) / max(dd, 1e-6))
    return best[1], best[2]


def rects(poly, cell=0.5, n=3, min_a=18.0):
    """Split a footprint (already in its rectangle's frame: u, v) into up to n axis-aligned rectangles, greedily the largest one inside
    the polygon each time (histogram method on a 0.5 m raster), until what is left is under 12 % of the area. The step-2 stand-ins were
    one bounding box per footprint (the L-shaped lots read as barns in the aerial: RESUME section 2 step 3)."""
    us = [p[0] for p in poly]; vs = [p[1] for p in poly]; u0, v0 = min(us), min(vs)
    W, H = int((max(us) - u0) / cell) + 1, int((max(vs) - v0) / cell) + 1
    def inside(x, y):
        c = False
        for (a, b), (e, g) in zip(poly, poly[1:] + poly[:1]):
            if (b > y) != (g > y) and x < (e - a) * (y - b) / (g - b) + a: c = not c
        return c
    M = [[inside(u0 + (i + 0.5) * cell, v0 + (j + 0.5) * cell) for i in range(W)] for j in range(H)]
    total = sum(map(sum, M)); out = []
    while len(out) < n:
        best = None; hgt = [0] * W
        for j in range(H):
            hgt = [hgt[i] + 1 if M[j][i] else 0 for i in range(W)]
            st = []
            for i in range(W + 1):
                h = hgt[i] if i < W else 0; start = i
                while st and st[-1][1] >= h:
                    s0, sh = st.pop(); A = sh * (i - s0)
                    if best is None or A > best[0]: best = (A, s0, i, j - sh + 1, j + 1)
                    start = s0
                st.append((start, h))
        if not best or best[0] * cell * cell < min_a: break
        A, i0, i1, j0, j1 = best
        for j in range(j0, j1):
            for i in range(i0, i1): M[j][i] = False
        out.append((u0 + i0 * cell, u0 + i1 * cell, v0 + j0 * cell, v0 + j1 * cell))
        if sum(map(sum, M)) < 0.12 * total: break
    return out


def auto_kit(e):
    """Tier 3 stand-in (LOD1 only, not reachable): the main county footprint split into 1-3 rectangles in its minimum-area rectangle's
    frame (main = the largest, 2 storeys if the county ridge > 8 m, wings at the main plate if big, else 1 storey: G), the other
    footprints over 25 m2 as 1-storey outbuildings, windows on the face toward Lincoln (nearest point of OSM's centreline) and the two
    sides, ~30 % lit at night (hashed), a hashed period style (STYLES3)."""
    import sys; sys.path.insert(0, str(ROOT / "tools/house")); from nb_house import obb
    b = next((b for b in e["buildings"] if b["main"]), None)
    if not b or b["area_m2"] < 60: return None
    _, _, _, _, yaw = obb([tuple(p) for p in b["footprint_spec"]])
    c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    loc = lambda P: [(x * c + z * s, -x * s + z * c) for x, z in P]     # spec -> the rectangle's frame (nb_house turns it back by yaw)
    R = rects(loc(b["footprint_spec"]))
    ridge = min(12.5, max(6.0, b["ridge_m"])); two = ridge > 8.0; o = 0.4; pitch = 32
    h = zlib.crc32(e["id"].encode()); clad, roof, pal = STYLES3[h % len(STYLES3)]
    cx = sum(p[0] for p in b["footprint_spec"]) / len(b["footprint_spec"]); cz = sum(p[1] for p in b["footprint_spec"]) / len(b["footprint_spec"])
    wx, wz = toward_lincoln(cx, cz); want = (wx * c + wz * s, -wx * s + wz * c)   # in the frame
    axes = {"-x": (-1, 0), "+x": (1, 0), "-z": (0, -1), "+z": (0, 1)}
    ff = max(axes, key=lambda k: axes[k][0] * want[0] + axes[k][1] * want[1])
    side = {"-x": ("-z", "+z"), "+x": ("-z", "+z"), "-z": ("-x", "+x"), "+z": ("-x", "+x")}[ff]
    blocks, win = [], []
    A0 = (R[0][1] - R[0][0]) * (R[0][3] - R[0][2])
    for bi, (u0, u1, v0, v1) in enumerate(R):
        W_, D_ = u1 - u0, v1 - v0; big = bi == 0 or W_ * D_ > 0.35 * A0
        plate = 6.0 if two and big else 3.0
        rise = (min(W_, D_) / 2 + o) * math.tan(math.radians(pitch))
        if bi == 0: plate = max(3.0, min(plate, ridge - rise + o * math.tan(math.radians(pitch))))
        blocks.append({"x": [round(u0, 2), round(u1, 2)], "z": [round(v0, 2), round(v1, 2)], "plate": round(plate, 2),
                       "roof": "hip" if max(W_, D_) / min(W_, D_) < 1.35 else ("gable_x" if W_ > D_ else "gable_z"), "pitch": pitch, "overhang": o,
                       "downspouts": False, "_src": "C footprint rectangle %d of %d (nb_kits.rects)" % (bi + 1, len(R))})
        for face in (ff,) + side:
            span = (v0, v1) if face in ("-x", "+x") else (u0, u1); L = span[1] - span[0]; n = int(L / 2.8)
            if n < 1: continue
            for i in range(n):
                at = span[0] + L * (i + 0.5) / n; door = face == ff and bi == 0 and i == n // 2
                if plate > 4: win.append(W(face, at, 4.0, 1.4, 0.95, "dh66", block=bi))
                win.append(W(face, at, 0.5, 2.1, 1.0, "door", block=bi) if door else W(face, at, 1.0, 1.6, 1.0, "dh66", block=bi))
    gar = []
    for ob in e["buildings"]:
        if ob is b or ob["area_m2"] < 25: continue
        P = loc(ob["footprint_spec"]); us = [p[0] for p in P]; vs = [p[1] for p in P]
        gar.append({"x": [round(min(us), 2), round(max(us), 2)], "z": [round(min(vs), 2), round(max(vs), 2)], "plate": 2.6, "roof": "hip", "pitch": 26,
                    "door_face": ff, "_src": "C outbuilding (bounding rectangle in the main frame)"})
    lit = [i for i in range(len(win)) if zlib.crc32(f"{e['id']}{i}".encode()) % 10 < 3]
    if h % 5 < 2:   # ~40 % of the backdrop houses string C7s along the eave toward Lincoln (film 11581/8221: most of the street is lit)
        blocks[0]["xmas_eave"] = [[axes[ff][0], 0, axes[ff][1]]]
    return {"style": f"Tier 3 stand-in ({clad})", "cladding": clad, "roof_mat": roof, "foundation_h": 0.5, "palette": dict(pal, found="stone"),
            "yaw_deg": round(yaw, 2), "blocks": blocks, "windows": win, "lit": {"windows": lit}, "garages": gar, "front_face": ff,
            "_src": "C footprint split into %d rectangles + C ridge; front toward Lincoln's OSM centreline; style hashed from STYLES3 (G, low)" % len(R)}


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
    kits = {"lot_B0": (murphys(), "medium", "massing C+L, eave/porch heights + camera F 11581 (rms 11 px), facade bays F (house +0.55 m z), porch columns F 11581+11576, lights F 11581; sides/rear G; day 3241 (blurred) confirms the grey-blue clapboard, hip dormer and full porch but shows a pediment over the steps that 11581 does not: not modelled (logged)"),
            "lot_B-1": (b_minus1(), "low-medium", "gable-front from L; white clapboard F (11581 left edge); windows G"),
            "lot_B+1": (b_plus1(), "low", "hip from L; colour/windows G (only its garage and an edge are in 11581)"),
            "lot_A-1": (a_minus1(), "medium", "white + green shutters F 6399 (day edge), 1471 (night: gabled dormer, lit lower wing), 3246 (day, the sled run: white painted walls, green shutters, a small arched hood over the door, a low dark roof; the green shingled lot_A-2 beyond it); massing L/C simplified to two blocks"),
            "lot_A+1": (a_plus1(), "medium", "Old Man Marley's house (user, Oct 20: the left neighbour from the street = +z). Shingle Style: turret + cone F 1888 (1990: red roofs, pale turret walls) + L peak 12.5 m on the C footprint's octagon; wings, entry, dormer, chimney from the user's modern photo description (G positions)")}
    STEP3 = {   # step 3 evidence pass (Oct 20): frames looked at per lot, what they show, the conclusion (art/home_alone/references/neighborhood/README.md)
        "lot_B0": [{"frame": 11581, "shows": "front + right side, night", "use": "camera solve; bays 0.55 m +z; porch columns; lights"},
                   {"frame": 11576, "shows": "porch left end, two columns, the white post mailbox", "use": "corner column 5.95; mailbox"},
                   {"frame": 3241, "shows": "day, blurred (sled POV): grey-blue clapboard, hip dormer, full porch, a pediment over the steps", "use": "colour/massing confirmed; the pediment conflicts with 11581 (straight lit porch eave): not modelled, logged"}],
        "lot_B-1": [{"frame": 11576, "shows": "white clapboard 2.5 storeys, a 1-storey porch roof across the front, dark shutters", "use": "kit kept (white gable-front + porch)"},
                    {"frame": 3241, "shows": "day, blurred: a white house left of the Murphys", "use": "colour"}],
        "lot_B+1": [{"frame": 11581, "shows": "right edge: a white panelled garage door, a cream/white 2-storey under a dark roof", "use": "kit kept"}],
        "lot_A-1": [{"frame": 3246, "shows": "day: white, green shutters, arched door hood, low dark roof; green shingled lot_A-2 beyond", "use": "confidence low-medium -> medium"},
                    {"frame": 1471, "shows": "night: a gabled dormer, a lit lower wing beside the lamp post", "use": "dormer kept"}],
        "lot_A+1": [{"frame": 1888, "shows": "day, across Lincoln, left of our garage: an octagonal turret with a tall red conical roof, pale upper walls, red hip roofs, a chimney on the left", "use": "Marley's house: Shingle Style kit (turret, flared hips); 1990 colours"},
                    {"frame": 546, "shows": "Buzz's window POV at night: Marley shovelling by the trash can; a dark house behind with a lit window", "use": "night: lit windows"}],
        "lot_A-2": [{"frame": 3246, "shows": "a dark green shingled house with a steep gable and a wreath on the door, beyond lot_A-1", "use": "Tier 3 style: shingle; colour TODO (palette has no dark green shingle)"}],
        "street": [{"frame": 3295, "shows": "a red fire hydrant on our side by the parkway, patchy snow banks, the acorn lamp", "use": "hydrant"},
                   {"frame": 1564, "shows": "a cherry picker at the overhead line in front of our house (day)", "use": "poles + wires on our side"},
                   {"frame": 1888, "shows": "overhead wires over Lincoln at our frontage; a blue sedan + a van parked at our kerb film-left", "use": "wires; the parked sedan"},
                   {"frame": 9540, "shows": "the bandits' van's RAM badge (Dodge Ram Van, B-series)", "use": "the van proxy"},
                   {"frame": 11581, "shows": "two box-body police cruisers, navy with a white door stripe, red beacon bars; a wire across the top left", "use": "the night scene cars"}],
    }
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
    # user, Oct 20 (via the coordinator): only OUR lot, Marley's (lot_A+1) and the Murphys' (lot_B0) are walkable heroes; every other house is
    # a distant backdrop (no colliders: SpecGreybox.Neighborhood, the walk boundary keeps the player off), with lit windows and some C7s
    XM = {"lot_A-1": ([1, 0, 0], False), "lot_B+1": ([-1, 0, 0], True), "lot_B-1": (None, True)}
    for e in man["parcels"]:
        e["walkable"] = e["id"] in ("lot_A0", "lot_A+1", "lot_B0")
        e["role"] = "hero" if e["walkable"] else "backdrop"
        if e["id"] in XM and e.get("kit"):
            n, porch = XM[e["id"]]
            if n: e["kit"]["blocks"][0]["xmas_eave"] = [n]
            if porch and e["kit"].get("porch"): e["kit"]["porch"]["xmas_eave"] = True
    for e in man["parcels"]:
        if e["id"] in STEP3: e["evidence_step3"] = STEP3[e["id"]]; e["evidence_frames"] = sorted(set(e.get("evidence_frames", [])) | {q["frame"] for q in STEP3[e["id"]]})
    man["street_evidence_step3"] = STEP3["street"]
    man["tiers"] = TIERS; man["budgets"] = BUDGETS
    P.write_text(json.dumps(man, indent=1)); print("kits", len(kits), "tier-3 auto", n3)


if __name__ == "__main__":
    main()
