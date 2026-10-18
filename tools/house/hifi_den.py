"""hifi_den: the den's windows (with their drapes and valances) and its built-in bookcase, generated to measurement (Oct 16 2026,
user: "start on the den, using the same approach you used to nail the kitchen").

Windows: each den window is FOUR mulled double-hung units, 6-over-6 (Marina's den, the real-house plan's 4-unit symbols and the
film's facade 4382 agree on the pattern). Openings from spec/house_spec.ground.json (den front_wide / side_twin, measured by
tools/house/den_walls.py; the same numbers cut the wall, and the grey-box lays the casing round the cut). This model is everything
inside the cut: frame, mull posts, sashes with muntins, glass, sash locks and lifts, the stool and apron; then the valance and two
tie-back drapes per window in Marina's floral (spec/dressing/den_fabric.png, cut by den_walls.py --fabric). Sheers are not built here
(the sheer pass, tools/house/hifi_sheers.py, owns them).
Bookcase: the rear wall's built-in (spec/dressing/den.json bookcase): carcass, three bays, shelves, the centre bay's TV shelf and
lower divider, a white plinth, the VCR, and rows of books (sizes and colours authored, film 2877 / Marina f69 spines).
Every visible face stands >= 1 cm off any face behind it that it overlaps; faces via Part.box/face only (zfight-check).

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P tools/house/hifi_den.py
  -> unity/HomeAlone/Assets/Models/Foyer/DenWindows.glb, DenBuiltins.glb (placed by SpecGreybox.Den: ground-floor root, spec metres)
"""
import json
import math
import random
import sys
from pathlib import Path

import bpy

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hifi_lib import Part, material   # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUTW = ROOT / "unity/HomeAlone/Assets/Models/Foyer/DenWindows.glb"
OUTB = ROOT / "unity/HomeAlone/Assets/Models/Foyer/DenBuiltins.glb"
SPEC = json.loads((ROOT / "spec/house_spec.ground.json").read_text())
D = json.loads((ROOT / "spec/dressing/den.json").read_text())
FAB = json.loads((ROOT / "spec/dressing/den_fabric.json").read_text())["repeat_m"]
WT = 0.14                                            # exterior wall thickness (spec/geometry.json)
WIN = [w for w in SPEC["windows"] if w["room"] == "den"]
assert len(WIN) == 2 and all(w.get("model") == "DenWindows" for w in WIN)

paint, glass, brass, fabric, tie = Part("Paint", "DW_Paint"), Part("Glass", "DW_Glass"), Part("Brass", "DW_Brass"), Part("Fabric", "DW_Fabric"), Part("Tie", "DW_Tie")


class Wall:
    """Local frame on a den wall: a along the wall from the window's low end, d into the wall (room face 0, outward +), y up.
    The den lies on the wall's -x (front wall) or -z (end wall) side."""
    def __init__(self, w):
        self.axis, self.face, (self.lo, self.hi) = w["wall_axis"], w["wall_coord_spec"], w["span_spec"]
        self.room = (-1, 0, 0) if self.axis == "x" else (0, 0, -1)

    def p(self, a, d, y):
        return (self.face + d, y, self.lo + a) if self.axis == "x" else (self.lo + a, y, self.face + d)

    def box(self, part, a0, a1, d0, d1, y0, y1):
        (x0, _, z0), (x1, _, z1) = self.p(a0, d0, 0), self.p(a1, d1, 0)
        part.box(min(x0, x1), max(x0, x1), y0, y1, min(z0, z1), max(z0, z1))

    def quad(self, part, pts, toward_room=True, uvs=None):
        n = self.room if toward_room else tuple(-c for c in self.room)
        part.face([self.p(*q) for q in pts], n, uvs)


U, ST, VAL, DR = D["windows"]["unit"], D["windows"]["stool"], D["windows"]["valance"], D["windows"]["drape"]


def window(w):
    L = Wall(w); W = L.hi - L.lo; S, H = w["sill_m"], w["head_m"]
    UW, JT, SS = U["w"], U["jamb"], U["stile"]; MW = (W - 4 * UW) / 3
    assert 0.03 < MW < 0.12, f"mull {MW:.3f} m: the opening does not fit four {UW} m units"
    STOOL = S + 0.012                                 # stool top 1.2 cm above the wall's cut (no face in the wall-top plane)
    # stool (into the opening under the sashes, 4.5 cm into the room, ears past the casing) and apron
    L.box(paint, -ST["ears"], W + ST["ears"], -ST["proud"], 0.0, STOOL - ST["t"], STOOL)          # nose and ears, in the room
    L.box(paint, 0.0, W, 0.0, 0.06, STOOL - ST["t"], STOOL)                                         # the part inside the cut only
    L.box(paint, -0.07, W + 0.07, -0.012, 0.0, STOOL - ST["t"] - ST["apron_h"], STOOL - ST["t"])
    L.box(paint, 0.0, W, 0.0, WT, H - JT, H)                                  # head jamb across the whole opening
    for i in range(4):
        a0 = i * (UW + MW); a1 = a0 + UW
        L.box(paint, a0, a0 + JT, 0.0, WT, STOOL, H - JT); L.box(paint, a1 - JT, a1, 0.0, WT, STOOL, H - JT)   # side jambs
        if i < 3:
            L.box(paint, a1, a1 + MW, 0.006, WT, STOOL, H - JT)                 # mull post (6 mm behind the jambs' room face)
            L.box(paint, a1 - 0.012, a1 + MW + 0.012, -0.012, 0.006, STOOL, H - JT)   # mull cover strip on the room face
        L.box(paint, a0 + JT, a1 - JT, 0.075, WT, STOOL, STOOL + 0.03)        # frame sill behind the lower sash (outside)
        YB, YT = STOOL + 0.0, H - JT; hs = (YT - YB + U["meeting"]) / 2
        z0, z1 = a0 + JT, a1 - JT
        for (y0, y1, d0, d1, top, bot) in ((YB, YB + hs, 0.025, 0.065, U["meeting"], U["bottom_rail"]),      # lower sash, room side
                                           (YT - hs, YT, 0.075, 0.115, U["top_rail"], U["meeting"])):         # upper sash, outside
            L.box(paint, z0, z0 + SS, d0, d1, y0, y1); L.box(paint, z1 - SS, z1, d0, d1, y0, y1)
            L.box(paint, z0 + SS, z1 - SS, d0, d1, y0, y0 + bot); L.box(paint, z0 + SS, z1 - SS, d0, d1, y1 - top, y1)
            ga0, ga1, gy0, gy1 = z0 + SS, z1 - SS, y0 + bot, y1 - top
            m = U["muntin"]
            for c in range(1, U["cols"]):
                ac = ga0 + (ga1 - ga0) * c / U["cols"]; L.box(paint, ac - m / 2, ac + m / 2, d0 + 0.006, d1 - 0.006, gy0, gy1)
            for r in range(1, U["rows"]):
                yc = gy0 + (gy1 - gy0) * r / U["rows"]; L.box(paint, ga0, ga1, d0 + 0.006, d1 - 0.006, yc - m / 2, yc + m / 2)
            dm = (d0 + d1) / 2
            L.quad(glass, [(ga0, dm, gy0), (ga1, dm, gy0), (ga1, dm, gy1), (ga0, dm, gy1)])
        ac = (z0 + z1) / 2; yl = YB + hs                                            # lock on the lower sash's meeting rail, two lifts
        L.box(brass, ac - 0.035, ac + 0.035, 0.03, 0.06, yl, yl + 0.012)
        for q in (z0 + 0.12, z1 - 0.12):
            L.box(brass, q - 0.025, q + 0.025, 0.012, 0.025, YB + 0.025, YB + 0.045)

    # ---- valance: box-pleated board 0.22 past the frame each side, its face 0.15 off the wall; fabric UVs at the cut's repeat
    va0, va1, vd = -VAL["past_frame"], W + VAL["past_frame"], -VAL["depth"]
    ru, rv = FAB
    y0, y1 = VAL["bottom"], VAL["top"]
    a0, a1, dd = va0, va1, vd
    if True:
        n = max(1, round((a1 - a0) / (ru / 2)))                       # box pleats: alternating panels 1.2 cm apart, a seam per half repeat
        for k in range(n):
            b0, b1 = a0 + (a1 - a0) * k / n, a0 + (a1 - a0) * (k + 1) / n; off = 0.0 if k % 2 == 0 else 0.012
            uv = [(b0 / ru, 0), (b1 / ru, 0), (b1 / ru, 1), (b0 / ru, 1)]
            L.quad(fabric, [(b0, dd - off, y0), (b1, dd - off, y0), (b1, dd - off, y1), (b0, dd - off, y1)], True, uv)
            L.quad(fabric, [(b0, dd - off + 0.006, y0), (b1, dd - off + 0.006, y0), (b1, dd - off + 0.006, y1), (b0, dd - off + 0.006, y1)], False, uv)
            if k > 0:   # the step between neighbouring panels (seam), facing along a
                ds = (dd - 0.012, dd + 0.006)
                fabric.face([L.p(b0, ds[0], y0), L.p(b0, ds[1], y0), L.p(b0, ds[1], y1), L.p(b0, ds[0], y1)], _along(L, -1 if k % 2 else 1))
        for ae, sgn in ((a0, -1), (a1, 1)):                           # returns to the wall (stop 1 cm short of it)
            fabric.face([L.p(ae, vd, y0), L.p(ae, -0.01, y0), L.p(ae, -0.01, y1), L.p(ae, vd, y1)], _along(L, sgn),
                        [(0, 0), (0.14 / ru, 0), (0.14 / ru, 1), (0, 1)])
            fabric.face([L.p(ae - sgn * 0.006, vd + 0.006, y0), L.p(ae - sgn * 0.006, -0.01, y0), L.p(ae - sgn * 0.006, -0.01, y1),
                         L.p(ae - sgn * 0.006, vd + 0.006, y1)], _along(L, -sgn), [(0, 0), (0.14 / ru, 0), (0.14 / ru, 1), (0, 1)])
        L.box(paint, a0, a1, vd, -0.01, y1, y1 + 0.019)                # dust board on top (painted)

    # ---- drapes: a pleated panel each side, hung under the valance to 1 cm off the floor, tied back
    for side in (0, 1):
        def edges(y):
            """outer and inner a of the panel at height y (window-local, the low-a side; mirrored for the other)."""
            outer = va0 + DR["outer_in"]
            if y >= DR["mid_h"]:
                t = (y - DR["mid_h"]) / (VAL["bottom"] - DR["mid_h"]); inner = DR["mid_inner"] + t * (DR["top_inner"] - DR["mid_inner"])
            elif y >= DR["tie_h"]:
                t = (y - DR["tie_h"]) / (DR["mid_h"] - DR["tie_h"]); inner = outer + DR["tie_w"] + t * (DR["mid_inner"] - outer - DR["tie_w"])
            else:
                t = y / DR["tie_h"]; inner = outer + DR["hem_w"] + t * (DR["tie_w"] - DR["hem_w"])
            return outer, inner
        ys = [0.01, 0.2, 0.4, 0.6, DR["tie_h"] - 0.03, DR["tie_h"], DR["tie_h"] + 0.03, 0.85, DR["mid_h"], 1.2, 1.4, 1.6, VAL["bottom"] + 0.03]
        nf = 8
        grid = []
        for y in ys:
            o, i_ = edges(y); row = []
            for k in range(nf * 2 + 1):
                t = k / (nf * 2); a = o + t * (i_ - o)
                fold = DR["front"] + (DR["back"] - DR["front"]) * (0.5 + 0.5 * math.cos(math.pi * k))   # alternate front/back crests
                a = a if side == 0 else W - a
                row.append((a, fold, y))
            grid.append(row)
        th = 0.006
        for r in range(len(ys) - 1):
            for k in range(nf * 2):
                A, B, C, E = grid[r][k], grid[r][k + 1], grid[r + 1][k + 1], grid[r + 1][k]
                vv = lambda q: (q[2] - 0.0) / rv
                uu = lambda kk: kk * DR["fold"] / ru / 2
                uv = [(uu(k), vv(A)), (uu(k + 1), vv(B)), (uu(k + 1), vv(C)), (uu(k), vv(E))]
                L.quad(fabric, [A, B, C, E], True, uv)
                L.quad(fabric, [(q[0], q[1] + th, q[2]) for q in (A, B, C, E)], False, uv)
        # tie-back: a dark green band round the pinch, 1.5 cm proud of the folds
        o, i_ = edges(DR["tie_h"]); a0_, a1_ = (o - 0.015, i_ + 0.015) if side == 0 else (W - i_ - 0.015, W - o + 0.015)
        L.box(tie, a0_, a1_, DR["front"] - 0.02, DR["back"] + 0.012, DR["tie_h"] - 0.02, DR["tie_h"] + 0.02)
        tq = (a0_ if side == 0 else a1_)                              # the tassel hangs on the outer side
        L.box(tie, tq - 0.025, tq + 0.025, DR["front"] - 0.05, DR["front"] - 0.02, DR["tie_h"] - 0.17, DR["tie_h"] - 0.02)


def _along(L, sgn):
    """the direction +a (sgn 1) or -a (sgn -1) on wall L, in spec axes"""
    return (0, 0, sgn) if L.axis == "x" else (sgn, 0, 0)


def bookcase(wood, white, black, book_parts):
    B = D["bookcase"]; x0, x1 = B["x"]; z0, z1 = B["z"]; T = 0.02; t = B["shelf_t"]
    white.box(x0, x1, 0.0, B["plinth"], z0, z1)                                                # plinth (white, as Marina's)
    wood.box(x0, x1, B["plinth"], B["top"], z0, z0 + T); wood.box(x0, x1, B["plinth"], B["top"], z1 - T, z1)   # end panels
    wood.box(x0, x0 + 0.015, B["bottom_top"], B["top_band"], z0 + T, z1 - T)                      # back
    wood.box(x0, x1, B["top_band"], B["top"], z0 + T, z1 - T)                                    # top band
    wood.box(x0 + 0.015, x1, B["plinth"], B["bottom_top"], z0 + T, z1 - T)                         # bottom shelf
    (dA0, dA1), (dB0, dB1) = B["dividers"]
    for a, b in ((dA0, dA1), (dB0, dB1)):
        wood.box(x0 + 0.015, x1, B["bottom_top"], B["top_band"], a, b)
    bays = [(z0 + T, dA0, B["shelves_side"]), (dA1, dB0, B["shelves_centre"]), (dB1, z1 - T, B["shelves_side"])]
    for a, b, tops in bays:
        for s in tops:
            wood.box(x0 + 0.015, x1, s - t, s, a, b)
    lz0, lz1, lt = B["lower_divider"]
    wood.box(x0 + 0.015, x1, B["bottom_top"], lt - t, lz0, lz1)
    v = B["vcr"]; black.box(v["x"][0], v["x"][1], v["y"][0] + 0.001, v["y"][1], v["z"][0], v["z"][1])
    # books: rows standing on shelves, 1.5 cm in from the front edge, spines facing the room (sizes/colours authored); the spans
    # leave room for the clutter (games, VHS, the lamp, the soldier, the bus)
    rng = random.Random(16)
    (eb0, eb1), (cb0, cb1), (lb0, lb1) = (dB1, z1 - T), (dA1, dB0), (z0 + T, dA0)   # end, centre, living-side bays
    rows = [(19.12, eb1 - 0.02, 0.80), (eb0 + 0.03, eb1 - 0.25, 1.208), (eb0 + 0.20, eb1 - 0.03, 1.617),
            (lb0 + 0.02, lb1 - 0.35, 0.17), (lb0 + 0.15, lb1 - 0.03, 0.452), (17.08, lb1 - 0.03, 0.80), (17.02, lb1 - 0.05, 1.208),
            (lb0 + 0.04, lb1 - 0.40, 1.617), (cb0 + 0.03, B["lower_divider"][0] - 0.02, 0.17)]
    # the books themselves are the Fadnn pack's SM_Book models on these rows: tools/house/den_books.py -> store_props den_book_*
    del rows, rng


def lbox(body, lab, x0, x1, y0, y1, z0, z1, uv):
    """a box whose room-facing (+x) face carries a label from the atlas (uv = [u0, v0, u1, v1]); its other faces plain"""
    body.face([(x0, y1, z0), (x0, y1, z1), (x1, y1, z1), (x1, y1, z0)], (0, 1, 0)); body.face([(x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)], (0, -1, 0))
    body.face([(x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)], (-1, 0, 0))
    body.face([(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)], (0, 0, -1)); body.face([(x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], (0, 0, 1))
    u0, v0, u1, v1 = uv   # seen from the room (looking -x) +z is on the left: text runs from z1 to z0
    lab.face([(x1, y0, z1), (x1, y0, z0), (x1, y1, z0), (x1, y1, z1)], (1, 0, 0), [(u0, v0), (u1, v0), (u1, v1), (u0, v1)])


def clutter(P):
    """film 2877 / 2868 on our shelves: game and puzzle stacks, VHS, the CRT on the VCR, the soldier, the bus, a Santa"""
    B = D["bookcase"]; x1 = B["x"][1]; L = json.loads((ROOT / "spec/dressing/den_labels.json").read_text()); rng = random.Random(1990)
    dA1, eb1 = B["dividers"][1][1], B["z"][1] - 0.02
    # games: lying flat, stacked 3-5 high on the end bay's two lower shelves, edges out
    gi = 0
    c2 = B["lower_divider"][1]                                                            # the centre bay's lower-right compartment too
    for shelf, zs in ((0.17, [(dA1 + 0.03, dA1 + 0.45), (dA1 + 0.50, dA1 + 0.92), (c2 + 0.03, c2 + 0.48)]),
                      (0.452, [(dA1 + 0.03, dA1 + 0.44), (dA1 + 0.62, dA1 + 1.06), (c2 + 0.04, c2 + 0.47)])):
        for za, zb in zs:
            y = shelf + 0.001
            for k in range(rng.randint(3, 5)):
                hh = rng.uniform(0.045, 0.075); dz = rng.uniform(-0.02, 0.02); dep = rng.uniform(0.26, 0.33)
                kind = "puzzle" if rng.random() < 0.3 else "game"; cell = L[kind][gi % len(L[kind])]; gi += 1
                body = P["box_" + str(gi % 4)]
                if y + hh > shelf + 0.23: break   # under the next shelf (gaps 0.24 / 0.31)
                lbox(body, P["labels"], x1 - 0.012 - dep, x1 - 0.012 - rng.uniform(0, 0.02), y, y + hh, za + dz, zb + dz, cell)
                y += hh + 0.001
    # VHS: a row standing in the centre bay's lower-left compartment (the 0.452 shelf), spines out
    c0, c1 = B["dividers"][0][1] + 0.02, B["lower_divider"][0] - 0.02; z = c0
    for k, cell in enumerate(L["vhs"] * 2):
        if z + 0.026 > c1: break
        lbox(P["vhs"], P["labels"], x1 - 0.015 - 0.105, x1 - 0.015, 0.453, 0.453 + 0.19, z, z + 0.025, cell); z += 0.027
    # the TV is the bought JVC set (store_props.json den_tv); its video screen is SpecGreybox.DenScreenPatch
    # the wooden soldier (lathe parts): black boots, white trousers, red coat, skin, black shako
    so = D["decor"]["soldier"]; sx, sy, sz = so["at"]; h = so["h"]
    P["soldier_black"].lathe(sx, sz, sy, [(0, 0.035), (0.02, 0.035), (0.02, 0.0)], 12)
    P["soldier_white"].lathe(sx, sz, sy + 0.02, [(0, 0.022), (0.10, 0.022), (0.10, 0.0)], 12)
    P["soldier_red"].lathe(sx, sz, sy + 0.12, [(0, 0.026), (0.09, 0.024), (0.09, 0.0)], 12)
    P["soldier_skin"].lathe(sx, sz, sy + 0.21, [(0, 0.02), (0.035, 0.022), (0.035, 0.0)], 12)
    P["soldier_black"].lathe(sx, sz, sy + 0.245, [(0, 0.024), (h - 0.245, 0.028), (h - 0.245, 0.0)], 12)
    # the double-decker bus: red body, cream band, dark windows (two rows), black wheels
    bu = D["decor"]["bus"]; bx, by, bz = bu["at"]; w, hh, L_ = bu["size"]
    P["bus_red"].box(bx - w / 2, bx + w / 2, by + 0.012, by + hh, bz - L_ / 2, bz + L_ / 2)
    for yy in (by + 0.03, by + 0.06):
        P["bus_dark"].box(bx + w / 2, bx + w / 2 + 0.002, yy, yy + 0.018, bz - L_ / 2 + 0.01, bz + L_ / 2 - 0.01)
    for zz in (bz - L_ / 2 + 0.03, bz + L_ / 2 - 0.03):
        P["bus_dark"].box(bx - w / 2 - 0.002, bx + w / 2 + 0.002, by, by + 0.022, zz - 0.012, zz + 0.012)
    sa = D["decor"]["santa"]; ax, ay, az = sa["at"]
    P["soldier_red"].lathe(ax, az, ay, [(0, 0.025), (0.05, 0.022), (0.07, 0.012), (sa["h"], 0.0)], 12)
    P["soldier_white"].lathe(ax, az, ay + 0.045, [(0, 0.024), (0.012, 0.024), (0.012, 0.0)], 12)


def lamps(P):
    """the den's lamps from their fixtures (den.json lamps): bases and stems, shades as HiFi_Shade* (emissive at night), bulbs"""
    Lm = D["lamps"]
    x, y, z = Lm["bookcase"]["at"]; rb, rt, s0, s1 = Lm["bookcase"]["shade"]       # urn lamp, orange cone shade
    P["urn"].lathe(x, z, y, [(0, 0.055), (0.02, 0.06), (0.06, 0.05), (0.12, 0.04), (0.15, 0.02), (0.16, 0.0)], 16)
    P["brass"].lathe(x, z, y + 0.16, [(0, 0.008), (s0 - 0.16 + 0.03, 0.008), (s0 - 0.16 + 0.03, 0.0)], 8)
    P["shade_orange"].lathe(x, z, y + s0, [(0, rb), (s1 - s0, rt), (s1 - s0, 0.0)], 20)
    x, y, z = Lm["floor"]["at"]; ax, az = Lm["floor"]["arm"]; rb, rt, s0, s1 = Lm["floor"]["shade"]
    P["brass"].lathe(x, z, y, [(0, 0.14), (0.025, 0.13), (0.03, 0.012), (s1 - 0.02, 0.012), (s1, 0.0)], 20)
    P["brass"].box(min(x, x + ax), max(x, x + ax), s1 - 0.035, s1 - 0.02, z - 0.008, z + 0.008)          # the swing arm
    P["shade_cream"].lathe(x + ax, z + az, s0, [(0, rb), (s1 - s0 - 0.06, rt), (s1 - s0 - 0.06, 0.0)], 24)
    x, y, z = Lm["side"]["at"]; rb, rt, s0, s1 = Lm["side"]["shade"]
    P["stemwood"].lathe(x, z, y, [(0, 0.07), (0.03, 0.07), (0.05, 0.03), (0.15, 0.04), (0.25, 0.02), (s0 + 0.05, 0.012), (s0 + 0.05, 0.0)], 16)
    P["shade_white"].lathe(x, z, y + s0, [(0, rb), (s1 - s0, rt), (s1 - s0, 0.0)], 24)
    x, y, z = Lm["desk"]["at"]                                                        # banker's lamp: brass base and stem, green shade
    if "store" not in Lm["desk"]:   # the bought lamp (store_props den_banker) replaces this stand-in
     P["brass"].lathe(x, z, y, [(0, 0.075), (0.02, 0.07), (0.025, 0.012), (0.30, 0.012), (0.30, 0.0)], 16)
     P["shade_green"].box(x - 0.06, x + 0.06, y + 0.30, y + 0.36, z - 0.13, z + 0.13)
    for name in ("bookcase", "floor", "side"):                                           # a bulb inside each shade (it glows through)
        x, y, z = Lm[name]["at"]; ax, az = Lm[name].get("arm", [0, 0]); rb, rt, s0, s1 = Lm[name]["shade"]
        yb = (y if name != "floor" else 0) + (s0 + s1) / 2 - (0.03 if name == "floor" else 0)
        P["bulb"].lathe(x + ax, z + az, yb - 0.03, [(0, 0.0001), (0.01, 0.025), (0.04, 0.03), (0.06, 0.012), (0.06, 0.0)], 10)


def decor(P):
    """floor pieces in front of the shelves (film 2868/2877): poinsettias red (gold foil pot) and white (wicker), the ficus's basket"""
    rng = random.Random(7)
    for key, col in (("poinsettia_red", "bract_red"), ("poinsettia_white", "bract_white")):
        q = D["decor"][key]; cx, cz = q["at"]; r, hgt = q["r"], q["h"]
        pot = "foil" if q["pot"] == "foil" else "wicker"
        P[pot].lathe(cx, cz, 0.0, [(0, 0.10), (0.02, 0.105), (0.17, 0.13), (0.19, 0.14), (0.19, 0.0)], 16)
        P["leaf"].lathe(cx, cz, 0.19, [(0, 0.12), (0.05, 0.10), (0.05, 0.0)], 12)              # soil and foliage mound
        for k in range(80):                                                                    # bracts: flat pointed leaves in a dome
            ang = rng.uniform(0, 2 * math.pi); rr = rng.uniform(0.03, r); yy = 0.24 + (hgt - 0.24) * (1 - (rr / r) ** 2) * rng.uniform(0.7, 1.0)
            L_ = rng.uniform(0.09, 0.15); W_ = L_ * 0.42; dx, dz = math.cos(ang), math.sin(ang)
            px, pz = cx + rr * dx * 0.6, cz + rr * dz * 0.6; tipx, tipz = px + dx * L_, pz + dz * L_
            sx, sz = -dz * W_ / 2, dx * W_ / 2; part = P[col] if k % 4 else P["leaf"]
            pts = [(px, yy, pz), (px + dx * L_ * 0.45 + sx, yy + 0.01, pz + dz * L_ * 0.45 + sz), (tipx, yy - 0.02 - 0.25 * L_ * rr / r, tipz), (px + dx * L_ * 0.45 - sx, yy + 0.01, pz + dz * L_ * 0.45 - sz)]
            part.face(pts, (0, 1, 0))
    f = D["decor"]["ficus"]; cx, cz = f["at"]
    P["wicker"].lathe(cx, cz, 0.0, [(0, f["basket_r"] - 0.04), (0.03, f["basket_r"] - 0.02), (f["basket_h"], f["basket_r"]), (f["basket_h"], 0.0)], 20)


def export(parts, mats, out, root_name):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    M = {k: material(k, *v) for k, v in mats.items()}
    coll = bpy.context.scene.collection
    root = bpy.data.objects.new(root_name, None); coll.objects.link(root)
    for p in parts:
        if p.f:
            p.build(coll, M).parent = root
    out.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=str(out), export_format="GLB", export_yup=True, export_apply=True)
    print("wrote", out, {p.name: len(p.f) for p in parts})


for w in WIN:
    window(w)
export((paint, glass, brass, fabric, tie), {"DW_Paint": ((0.88, 0.87, 0.83), 0.35), "DW_Glass": ((0.1, 0.12, 0.13), 0.05),
                                            "DW_Brass": ((0.75, 0.56, 0.25), 0.3), "DW_Fabric": ((0.85, 0.8, 0.7), 0.9), "DW_Tie": ((0.05, 0.16, 0.08), 0.6)},
       OUTW, "DenWindows_HiFi")

wood, white, black = Part("Wood", "DB_Wood"), Part("Plinth", "DB_Paint"), Part("VCR", "DB_Black")
books = [Part(f"Books{i}", f"DB_Book{i}") for i in range(5)]
bookcase(wood, white, black, books)
MATS = {"labels": ("DB_Labels", (1, 1, 1), 0.6), "box_0": ("DB_Box0", (0.75, 0.10, 0.10), 0.6), "box_1": ("DB_Box1", (0.10, 0.25, 0.60), 0.6),
        "box_2": ("DB_Box2", (0.90, 0.75, 0.15), 0.6), "box_3": ("DB_Box3", (0.92, 0.90, 0.84), 0.6), "vhs": ("DB_Vhs", (0.02, 0.02, 0.025), 0.5),
        "tvcase": ("DB_TvCase", (0.015, 0.015, 0.017), 0.45), "screen": ("DB_Screen", (0.02, 0.025, 0.025), 0.1), "chrome": ("DB_Chrome", (0.5, 0.5, 0.5), 0.3),
        "soldier_black": ("DB_SoldierBlack", (0.02, 0.02, 0.02), 0.5), "soldier_white": ("DB_SoldierWhite", (0.85, 0.83, 0.78), 0.5),
        "soldier_red": ("DB_SoldierRed", (0.55, 0.04, 0.04), 0.5), "soldier_skin": ("DB_Skin", (0.80, 0.60, 0.48), 0.6),
        "bus_red": ("DB_BusRed", (0.62, 0.04, 0.04), 0.4), "bus_dark": ("DB_BusDark", (0.03, 0.03, 0.03), 0.3),
        "urn": ("DB_Urn", (0.04, 0.06, 0.05), 0.2), "brass": ("DL_Brass", (0.75, 0.56, 0.25), 0.3), "stemwood": ("DL_Stem", (0.35, 0.22, 0.12), 0.4),
        "shade_orange": ("DL_ShadeOrange", (0.80, 0.30, 0.08), 0.8), "shade_cream": ("DL_ShadeCream", (0.92, 0.88, 0.78), 0.9),
        "shade_white": ("DL_ShadeWhite", (0.94, 0.93, 0.90), 0.9), "shade_green": ("DL_ShadeGreen", (0.05, 0.40, 0.12), 0.2),
        "bulb": ("DL_Bulb", (1, 0.95, 0.85), 0.2), "foil": ("DB_Foil", (0.85, 0.65, 0.25), 0.3), "wicker": ("DB_Wicker", (0.55, 0.38, 0.20), 0.85),
        "leaf": ("DB_Leaf", (0.06, 0.20, 0.06), 0.6), "bract_red": ("DB_BractRed", (0.62, 0.03, 0.05), 0.7), "bract_white": ("DB_BractWhite", (0.90, 0.90, 0.84), 0.7)}
P = {k: Part(k, m) for k, (m, _, _) in MATS.items()}
clutter(P); lamps(P); decor(P)
export([wood, white, black] + books + list(P.values()), {**{m: (c, r) for m, c, r in MATS.values()}, "DB_Wood": ((0.12, 0.05, 0.035), 0.5), "DB_Paint": ((0.88, 0.87, 0.83), 0.35), "DB_Black": ((0.02, 0.02, 0.02), 0.4),
                                      "DB_Book0": ((0.45, 0.06, 0.05), 0.7), "DB_Book1": ((0.08, 0.15, 0.30), 0.7), "DB_Book2": ((0.70, 0.62, 0.45), 0.7),
                                      "DB_Book3": ((0.10, 0.22, 0.12), 0.7), "DB_Book4": ((0.80, 0.78, 0.72), 0.7)},
       OUTB, "DenBuiltins_HiFi")
