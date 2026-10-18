"""hifi_living: the living room's windows (with their drapes, sheers and valances), fireplace, piano and small dressing, generated
to measurement (Oct 16 2026, TRIAL; changes/2026-10-16-living-room.json). The den's method (tools/house/hifi_den.py) and the
sheer pass's cloth (tools/house/hifi_sheers.py: its functions are reused, not copied: see SHEERS below).

  LivingWindows.glb  everything inside the four cuts (spec/house_spec.ground.json living windows, model "LivingWindows"):
                     rear: stock 2'8" double-hung, 6-over-6 (film 10600, Marina f3), stool and apron;
                     front: French windows, a pair of leaves each, 2 x 5 lites over a raised bottom panel (film 4382 facade,
                     Marina f89: glass 0.44-1.87 m, knobs 0.945 m), brass knobs;
                     cloth: the film's deep green damask drapes tied back (5650, 10600), white sheers across the glass (5650, 10600),
                     Marina's box-pleated valances over the French windows (f89: 1.82-2.23 m; the film never shows their tops)
  LivingBuiltins.glb the fireplace (Marina f165 sizes, film 10600's Adam style: fluted pilasters, swag frieze, overmantel panel),
                     hearth, firebox with grate and logs, the brass fire screen and tools (10600), stockings (Marina); the console
                     upright piano with bench and brass bar lamp (film 5628-5650), the lamps (living.json lamps: shades HiFi_Shade*,
                     bulbs HiFi_Bulb*: dark by day, lit at night), wall brackets with porcelain dogs (5650), nutcrackers and a tin
                     (10636), the toy train on its oval (5650), the rug, the white poinsettia, and the C7 bulbs and gifts on the
                     user's Asset Store Christmas tree (placed by StoreProps)
Every visible face >= 1 cm off any face behind it; faces via Part.box/face/lathe/sweep (zfight-check). Textures it writes:
unity/HomeAlone/Assets/Textures/Living/{damask,rug}.png (generated here, CC0 by construction).

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P tools/house/hifi_living.py
"""
import json
import math
import random
import sys
from pathlib import Path

import bpy
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hifi_lib import Part, material   # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
MOD = ROOT / "unity/HomeAlone/Assets/Models/Foyer"
TEXD = ROOT / "unity/HomeAlone/Assets/Textures/Living"
D = json.loads((ROOT / "spec/dressing/living.json").read_text())
SPEC = json.loads((ROOT / "spec/house_spec.ground.json").read_text())
WIN = {w["name"]: w for w in SPEC["windows"] if w["room"] == "living_room"}
assert len(WIN) == 4 and all(w.get("model") == "LivingWindows" for w in WIN.values())
WT, CASING, X0, X1, Z0, Z1 = 0.14, 0.07, 1.58, 9.954, 11.57, 16.07

# SHEERS: hifi_sheers.py's cloth functions (frame, sheet, lin, wobble, sheer_panel, drape, valance, SMOOTH) run from its own source up to
# its first build line, so the living room's cloth is the same cloth as the dining room's and the kitchen's (one implementation)
_src = (ROOT / "tools/house/hifi_sheers.py").read_text()
_ns = {"__file__": str(ROOT / "tools/house/hifi_sheers.py"), "__name__": "hifi_sheers_lib"}
exec(compile(_src[:_src.index("\nbpy.ops.wm.read_factory_settings(use_empty=True)")], "hifi_sheers.py", "exec"), _ns)
frame, sheer_panel, drape, valance, SMOOTH = _ns["frame"], _ns["sheer_panel"], _ns["drape"], _ns["valance"], _ns["SMOOTH"]


def P(n, m):
    return Part(n, m)


_box = Part.box
Part.box = lambda self, x0, x1, y0, y1, z0, z1: _box(self, min(x0, x1), max(x0, x1), min(y0, y1), max(y0, y1), min(z0, z1), max(z0, z1))   # any corner order: always outward


# ------------------------------------------------------------------------------------------------ textures (numpy, tileable)
def save_png(name, px):
    TEXD.mkdir(parents=True, exist_ok=True)
    h, w = px.shape[:2]
    img = bpy.data.images.new(name, w, h, alpha=px.shape[2] == 4)
    if px.shape[2] == 3:
        px = np.dstack([px, np.ones((h, w))])                                    # Blender images are RGBA
    img.pixels.foreach_set(np.ascontiguousarray(px[::-1]).astype(np.float32).ravel())
    img.filepath_raw = str(TEXD / f"{name}.png"); img.file_format = "PNG"; img.save()


def damask_texture():
    """Tone-on-tone damask: one ogee repeat (mirrored left/right), the motif in satin (lighter) on a matte ground, 512 x 768 for a
    0.40 x 0.60 m repeat. Linear colour of the film's drapes (5650/5640 against the white baseboard: lin 0.020/0.031/0.021, a deep
    bottle green); the motif x1.7."""
    H, W = 768, 512
    v, u = np.mgrid[0:H, 0:W] / np.array([H, W])[:, None, None]
    x = np.abs(u - 0.5) * 2                                                       # mirrored across the repeat's centre line
    ogee = np.abs(x - 0.5 * (1 + np.cos(2 * np.pi * v)) * 0.9) < 0.035              # the ogee lattice lines
    def blob(cx, cy, rx, ry): return ((x - cx) / rx) ** 2 + ((v - cy) / ry) ** 2 < 1
    flower = blob(0.0, 0.5, 0.28, 0.16) | blob(0.0, 0.32, 0.12, 0.10) | blob(0.0, 0.68, 0.1, 0.12) | blob(0.22, 0.42, 0.16, 0.06) | blob(0.22, 0.58, 0.16, 0.06)
    leaf = blob(0.75, 0.0, 0.12, 0.09) | blob(0.75, 1.0, 0.12, 0.09) | blob(0.95, 0.5, 0.06, 0.14)
    hole = blob(0.0, 0.5, 0.12, 0.06)
    m = ((flower & ~hole) | leaf | ogee).astype(float)
    from_ = np.array([0.020, 0.031, 0.021]); g = np.clip(from_ * (1 + 0.7 * m)[..., None] * (1 + 0.04 * np.sin(v[..., None] * 2 * np.pi * 120)), 0, 1)
    srgb = np.where(g <= 0.0031308, 12.92 * g, 1.055 * g ** (1 / 2.4) - 0.055)
    save_png("damask", srgb)


def rug_texture():
    """A Persian-style rug (the film's and Marina's red oriental rug; generic, not a copied design): a deep red field covered in a dense
    arabesque (interlaced sine vines with small rosettes), a navy medallion, navy/ivory guard borders. 1024 x 768 over 3.66 x 2.74 m."""
    H, W = 768, 1024
    v, u = np.mgrid[0:H, 0:W] / np.array([H, W])[:, None, None]
    red, navy, ivory, gold, dk = map(np.array, ([0.30, 0.025, 0.03], [0.02, 0.03, 0.08], [0.55, 0.47, 0.33], [0.45, 0.30, 0.08], [0.08, 0.01, 0.015]))
    X, Y = u * 3.66, v * 2.74
    b = np.minimum(np.minimum(X, 3.66 - X), np.minimum(Y, 2.74 - Y))           # metres from the edge
    img = np.empty((H, W, 3)); img[:] = red
    vine = (np.abs(np.sin(X * 9 + 2 * np.sin(Y * 7)) * np.sin(Y * 9 + 2 * np.sin(X * 7))) > 0.80) | \
           (np.abs(np.sin(X * 5.5 - 1.5 * np.cos(Y * 11)) * np.cos(Y * 6 + 1.5 * np.sin(X * 9))) > 0.88)   # two interlaced vine layers
    ros = (np.sin(X * 18) * np.sin(Y * 18)) > 0.82                             # small rosettes on a lattice
    img[vine] = dk; img[ros] = navy; img[ros & ((np.sin(X * 36) * np.sin(Y * 36)) > 0.5)] = gold
    du, dv = X - 1.83, Y - 1.37
    med = np.abs(du) / 0.85 + np.abs(dv) / 0.62 < 1
    img[med] = navy; img[med & vine] = red; img[np.abs(du) / 0.45 + np.abs(dv) / 0.33 < 1] = red
    img[(du / 0.22) ** 2 + (dv / 0.16) ** 2 < 1] = gold
    band = b < 0.34
    img[band] = navy
    img[band & ((np.sin((X + Y) * 30) > 0.6) | (np.sin((X - Y) * 30) > 0.6))] = red          # the border's running motif
    img[(b > 0.05) & (b < 0.075)] = ivory; img[(b > 0.27) & (b < 0.295)] = ivory; img[(b > 0.32) & (b < 0.34)] = gold
    rng = np.random.default_rng(3)
    lin = np.clip(img * (1 + 0.10 * rng.standard_normal((H, W))[..., None]), 0, 1)   # pile irregularity
    save_png("rug", np.where(lin <= 0.0031308, 12.92 * lin, 1.055 * lin ** (1 / 2.4) - 0.055))


# ------------------------------------------------------------------------------------------------ windows
class Wall:
    """Local frame on a window's wall: a along the wall from the span's low end, d from the room face (0) outward (+), y up."""
    def __init__(self, w):
        self.face, (self.lo, self.hi) = w["wall_coord_spec"], w["span_spec"]
        self.out = 1 if self.face > 5 else -1                                  # front wall: outward +x; rear wall: outward -x

    def p(self, a, d, y):
        return (self.face + self.out * d, y, self.lo + a)

    def box(self, part, a0, a1, d0, d1, y0, y1):
        (x0, _, z0), (x1, _, z1) = self.p(a0, d0, 0), self.p(a1, d1, 0)
        part.box(min(x0, x1), max(x0, x1), y0, y1, min(z0, z1), max(z0, z1))


paint, glass, brass = P("Paint", "LV_Paint"), P("Glass", "LV_Glass"), P("Brass", "LV_Brass")


def lites(L, a0, a1, y0, y1, d0, d1, cols, rows, m=0.018):
    """glass and muntins inside a sash/leaf opening"""
    for c in range(1, cols):
        ac = a0 + (a1 - a0) * c / cols; L.box(paint, ac - m / 2, ac + m / 2, d0 + 0.004, d1 - 0.004, y0, y1)
    for r in range(1, rows):
        yc = y0 + (y1 - y0) * r / rows; L.box(paint, a0, a1, d0 + 0.004, d1 - 0.004, yc - m / 2, yc + m / 2)
    dm = (d0 + d1) / 2
    glass.face([L.p(a0, dm, y0), L.p(a1, dm, y0), L.p(a1, dm, y1), L.p(a0, dm, y1)], (-L.out, 0, 0))


def double_hung(w):
    """stock 2'8" double-hung, 6-over-6 (3 x 2 lites a sash), like hifi_den.py's units"""
    L = Wall(w); W = L.hi - L.lo; S, H = w["sill_m"], w["head_m"]; JT, SS = 0.02, 0.05
    ST = S + 0.012
    L.box(paint, -0.09, W + 0.09, -0.045, 0.0, ST - 0.025, ST)                    # stool nose and ears, in the room
    L.box(paint, 0.0, W, 0.0, 0.06, ST - 0.025, ST)
    L.box(paint, -0.07, W + 0.07, -0.012, 0.0, ST - 0.025 - 0.08, ST - 0.025)     # apron
    L.box(paint, 0.0, W, 0.0, WT, H - JT, H)
    L.box(paint, 0.0, JT, 0.0, WT, ST, H - JT); L.box(paint, W - JT, W, 0.0, WT, ST, H - JT)
    L.box(paint, JT, W - JT, 0.075, WT, ST, ST + 0.03)
    YB, YT = ST, H - JT; hs = (YT - YB + 0.035) / 2; z0, z1 = JT, W - JT
    for (y0, y1, d0, d1, top, bot) in ((YB, YB + hs, 0.025, 0.065, 0.035, 0.08), (YT - hs, YT, 0.075, 0.115, 0.05, 0.035)):
        L.box(paint, z0, z0 + SS, d0, d1, y0, y1); L.box(paint, z1 - SS, z1, d0, d1, y0, y1)
        L.box(paint, z0 + SS, z1 - SS, d0, d1, y0, y0 + bot); L.box(paint, z0 + SS, z1 - SS, d0, d1, y1 - top, y1)
        lites(L, z0 + SS, z1 - SS, y0 + bot, y1 - top, d0, d1, 3, 2)
    ac = (z0 + z1) / 2; yl = YB + hs
    L.box(brass, ac - 0.035, ac + 0.035, 0.03, 0.06, yl, yl + 0.012)
    for q in (z0 + 0.12, z1 - 0.12):
        L.box(brass, q - 0.025, q + 0.025, 0.012, 0.025, YB + 0.025, YB + 0.045)


def french(w):
    """a pair of leaves in a 0.75 m cut: frame, leaves (stiles 0.055, top rail 0.10, glass 0.44-1.90 in 2 x 5 lites, a raised bottom
    panel), meeting stiles, knobs at 0.945 (Marina f89), a threshold"""
    L = Wall(w); W = L.hi - L.lo; H = w["head_m"]; JT = 0.02
    L.box(paint, 0.0, W, 0.0, WT, H - JT, H)
    L.box(paint, 0.0, JT, 0.0, WT, 0.012, H - JT); L.box(paint, W - JT, W, 0.0, WT, 0.012, H - JT)
    L.box(paint, -0.02, W + 0.02, -0.01, WT, 0.0, 0.012)                          # threshold (oak, painted here)
    lw = (W - 2 * JT) / 2; d0, d1 = 0.03, 0.075
    for k in range(2):
        a0 = JT + k * lw; a1 = a0 + lw; SS, TR, G0, G1 = 0.055, 0.10, 0.44, 1.90
        L.box(paint, a0, a0 + SS, d0, d1, 0.012, H - JT); L.box(paint, a1 - SS, a1, d0, d1, 0.012, H - JT)
        L.box(paint, a0 + SS, a1 - SS, d0, d1, G1, H - JT)                       # top rail
        L.box(paint, a0 + SS, a1 - SS, d0, d1, 0.012, G0)                         # bottom rail and panel, one board
        L.box(paint, a0 + SS + 0.03, a1 - SS - 0.03, d0 - 0.012, d0, 0.08, G0 - 0.06)   # the raised panel, 1.2 cm proud
        lites(L, a0 + SS, a1 - SS, G0, G1, d0, d1, 2, 5)
        knob_a = a1 - 0.035 if k == 0 else a0 + 0.035
        # knob: a short boss and a ball on the room face of the leaf
        L.box(brass, knob_a - 0.012, knob_a + 0.012, d0 - 0.035, d0, 0.933, 0.957)
        L.box(brass, knob_a - 0.022, knob_a + 0.022, d0 - 0.06, d0 - 0.035, 0.925, 0.965)


# ------------------------------------------------------------------------------------------------ cloth (hifi_sheers' functions)
voile, hem, damask, tie = P("Voile", "SH_Voile"), P("VoileHem", "SH_Hem"), P("Damask", "LV_Damask"), P("DamaskTie", "LV_Tie")


def dress_french(w, seed):
    Pf = frame(w); lo, hi = w["span_spec"]; mid = (lo + hi) / 2
    VB0, VB1, RET = 1.84, 2.24, 0.28                                             # Marina f89: valance 1.82-2.23, runs 0.28 past the casing
    va, vb = lo - CASING - RET, hi + CASING + RET
    valance(damask, Pf, va, vb, VB0, VB1, 0.20)
    top = VB0 + 0.02
    sheer_panel(voile, hem, Pf, lo - CASING - 0.04, mid - 0.005, 0.015, top, 0.060, seed)
    sheer_panel(voile, hem, Pf, mid + 0.005, hi + CASING + 0.04, 0.015, top, 0.060, seed + 3.1)
    for uo, s in ((va + 0.03, 1), (vb - 0.03, -1)):
        drape(damask, tie, Pf, uo, s, 0.012, top, 1.05, 0.34, 0.15, 0.27, 0.125, N=6, seed=seed + s)


def dress_rear(w, seed, run):
    """film 10600: green damask panels tied back with rope, a white sheer across to the stool; no valance (Marina: none; the film's top
    unseen): the panels hang from a hidden rod at 2.22 (Marina f165 drape tops 2.19-2.22)"""
    Pf = frame(w); lo, hi = w["span_spec"]; S = w["sill_m"]
    va, vb = run
    top = 2.22
    sheer_panel(voile, hem, Pf, lo - CASING - 0.03, hi + CASING + 0.03, S + 0.025, top, 0.065, seed)
    for uo, s in ((va + 0.03, 1), (vb - 0.03, -1)):
        drape(damask, tie, Pf, uo, s, 0.012, top, 1.22, 0.30, 0.13, 0.24, 0.13, N=6, seed=seed + s)


# ------------------------------------------------------------------------------------------------ fireplace
F = D["fireplace"]; FC = F["centre_z"]
white, black, brick, slate, wood_log = P("Mantel", "LV_Paint"), P("Firebox", "LV_Iron"), P("Firebrick", "LV_Firebrick"), P("Hearth", "LV_Slate"), P("Logs", "LV_Log")
screen_mesh = P("ScreenMesh", "LV_ScreenMesh")


def fireplace():
    fb, sr, sh, hr = F["firebox"], F["surround"], F["shelf"], F["hearth"]
    x0, pr = X0, sr["proud"]; zl, zr = FC - fb["w"] / 2, FC + fb["w"] / 2; ZL, ZR = FC - sr["w"] / 2, FC + sr["w"] / 2
    slate.box(x0, x0 + hr["depth"], 0.0, hr["h"], FC - hr["w"] / 2, FC + hr["w"] / 2)          # hearth slab, 2.5 cm
    # pilasters and frieze: the surround, its face pr off the wall; the opening's reveal (inner faces) black
    white.box(x0, x0 + pr, hr["h"], fb["h"], ZL, zl); white.box(x0, x0 + pr, hr["h"], fb["h"], zr, ZR)
    white.box(x0, x0 + pr, fb["h"], sr["frieze_top"], ZL, ZR)
    for zc in np.linspace(ZL + 0.04, zl - 0.04, 5).tolist() + np.linspace(zr + 0.04, ZR - 0.04, 5).tolist():   # flutes: reeds 1 cm proud
        white.box(x0 + pr, x0 + pr + 0.01, hr["h"] + 0.12, fb["h"] - 0.08, zc - 0.009, zc + 0.009)
    for zc in (ZL + (zl - ZL) / 2, zr + (ZR - zr) / 2):                         # pilaster capitals (blocks in the frieze line)
        white.box(x0 + pr, x0 + pr + 0.025, fb["h"], sr["frieze_top"] - 0.02, zc - 0.13, zc + 0.13)
    white.box(x0 + pr, x0 + pr + 0.02, fb["h"] + 0.08, sr["frieze_top"] - 0.08, FC - 0.17, FC + 0.17)   # central tablet
    for s in (-1, 1):                                                            # swags on the frieze either side of the tablet (film 10600)
        za, zb = FC + s * 0.21, FC + s * (ZR - FC - 0.19)
        pts = [(x0 + pr + 0.012, sr["frieze_top"] - 0.09 - 0.09 * math.sin(math.pi * t), za + (zb - za) * t) for t in np.linspace(0, 1, 13)]
        white.sweep(pts, [(0.012 * math.cos(q), 0.012 * math.sin(q)) for q in np.linspace(0, 2 * math.pi, 9)[:-1]])
    # shelf: a board with a moulded edge (two steps)
    white.box(x0, x0 + sh["depth"], sh["top"] - sh["t"], sh["top"], FC - sh["w"] / 2, FC + sh["w"] / 2)
    white.box(x0, x0 + sh["depth"] - 0.03, sr["frieze_top"], sh["top"] - sh["t"], FC - sh["w"] / 2 + 0.06, FC + sh["w"] / 2 - 0.06)
    # firebox: back (firebrick) 1 cm off the wall, sides and floor black, 'depth' deep behind the surround's face
    brick.box(x0 + 0.002, x0 + 0.012, hr["h"], fb["h"] - 0.002, zl, zr)
    black.box(x0 + 0.012, x0 + pr, hr["h"], fb["h"] - 0.002, zl, zl + 0.012); black.box(x0 + 0.012, x0 + pr, hr["h"], fb["h"] - 0.002, zr - 0.012, zr)
    black.box(x0 + 0.012, x0 + pr, fb["h"] - 0.02, fb["h"] - 0.002, zl + 0.012, zr - 0.012)
    # grate and two logs
    for zc in (zl + 0.12, zr - 0.12):
        black.box(x0 + 0.03, x0 + 0.14, hr["h"], hr["h"] + 0.09, zc - 0.012, zc + 0.012)
    black.box(x0 + 0.03, x0 + 0.14, hr["h"] + 0.07, hr["h"] + 0.09, zl + 0.08, zr - 0.08)
    for k, xx in enumerate((x0 + 0.06, x0 + 0.11)):
        yy = hr["h"] + 0.09 + 0.045 + k * 0.03
        wood_log.sweep([(xx, yy, zl + 0.07), (xx, yy, zr - 0.07)], [(0.045 * math.cos(q), 0.045 * math.sin(q)) for q in np.linspace(0, 2 * math.pi, 11)[:-1]])
    # overmantel panel (film 10600): a raised moulding frame on the wall, its field painted
    (oz0, oz1), (oy0, oy1) = F["overmantel"]["z"], F["overmantel"]["h"]
    white.box(x0, x0 + 0.012, oy0, oy1, oz0, oz1)                               # the field, 1.2 cm proud of the paper
    for (a0, a1, b0, b1) in ((oz0, oz1, oy0, oy0 + 0.05), (oz0, oz1, oy1 - 0.05, oy1), (oz0, oz0 + 0.05, oy0, oy1), (oz1 - 0.05, oz1, oy0, oy1)):
        white.box(x0 + 0.012, x0 + 0.035, b0, b1, a0, a1)
    white.sweep([(x0 + 0.02, 1.85 + 0.2 * math.sin(q), FC + 0.3 * math.cos(q)) for q in np.linspace(0, 2 * math.pi, 33)],   # oval wreath moulding
                [(0.009 * math.cos(q), 0.009 * math.sin(q)) for q in np.linspace(0, 2 * math.pi, 7)[:-1]])


def fire_screen():
    """film 10600: a brass folding screen, three arched panels, fine mesh; the centre panel parallel to the wall, the wings angled back"""
    fb = F["firebox"]; xc = X0 + F["surround"]["proud"] + 0.22; zw = 0.36
    tube = [(0.008 * math.cos(q), 0.008 * math.sin(q)) for q in np.linspace(0, 2 * math.pi, 7)[:-1]]
    panels = [((xc, FC - zw), (xc, FC + zw), 0.80), ((xc, FC - zw), (xc - 0.17, FC - zw - 0.28), 0.66), ((xc, FC + zw), (xc - 0.17, FC + zw + 0.28), 0.66)]
    for (xa, za), (xb, zb), hgt in panels:
        arch = [(xa + (xb - xa) * t, hgt - 0.10 + 0.10 * math.sin(math.pi * t), za + (zb - za) * t) for t in np.linspace(0, 1, 13)]
        brass.sweep([(xa, 0.03, za)] + arch + [(xb, 0.03, zb)], tube)
        brass.sweep([(xa, 0.06, za), (xb, 0.06, zb)], tube)
        n = (-(zb - za), 0, xb - xa)
        pts = [(xa, 0.065, za)] + [(x, y - 0.012, z) for x, y, z in arch] + [(xb, 0.065, zb)]
        screen_mesh.face(pts, n); screen_mesh.face(list(reversed(pts)), tuple(-c for c in n))
        for (x, z) in ((xa, za), (xb, zb)):
            brass.lathe(x, z, 0.0, [(0, 0.016), (0.03, 0.012), (0.03, 0.0)], 10)
    # tools on a stand beside the hearth (rear, den side)
    tx, tz = X0 + 0.26, FC + F["hearth"]["w"] / 2 + 0.12
    brass.lathe(tx, tz, 0.0, [(0, 0.11), (0.02, 0.10), (0.03, 0.012), (0.70, 0.010), (0.72, 0.03), (0.75, 0.0)], 14)
    for k, a in enumerate(np.linspace(0, 2 * math.pi, 5)[:-1]):
        px, pz = tx + 0.05 * math.cos(a), tz + 0.05 * math.sin(a)
        brass.lathe(px, pz, 0.06, [(0, 0.006), (0.58, 0.006), (0.60, 0.014), (0.66, 0.014), (0.67, 0.0)], 8)


def stockings():
    """Marina f3/f165: stockings hung from the shelf's front edge (red and cream, white cuffs); flat padded shapes, 2 cm thick"""
    sh = D["fireplace"]["shelf"]; xf = X0 + sh["depth"] + 0.015
    zs = np.linspace(FC - 0.7, FC + 0.7, 5); cols = ["red", "cream", "cream", "cream", "red"]
    for zc, c in zip(zs, cols):
        top = sh["top"] - sh["t"] - 0.005
        prof = [(0.0, 0.0), (0.0, -0.30), (0.04, -0.36), (0.14, -0.37), (0.17, -0.33), (0.13, -0.28), (0.09, -0.26), (0.09, 0.0)]
        pts = [(zc - 0.045 + a, top + b) for a, b in prof]
        part = STK[c]
        front = [(xf + 0.02, y, z) for z, y in pts]; back = [(xf, y, z) for z, y in pts]
        part.face(front, (1, 0, 0)); part.face(back, (-1, 0, 0))
        for (p0, p1), (q0, q1) in zip(zip(front, front[1:] + front[:1]), zip(back, back[1:] + back[:1])):
            n = (0, -(p1[2] - p0[2]), p1[1] - p0[1])
            part.face([p0, p1, q1, q0], n)
        STK["cuff"].box(xf - 0.012, xf + 0.032, top - 0.07, top + 0.01, zc - 0.05, zc + 0.05)   # its top 1 cm above the stocking's


# ------------------------------------------------------------------------------------------------ piano (film 5628-5650)
mahog, keysw, keysb, felt = P("PianoCase", "LV_Mahogany"), P("Keys", "LV_KeysWhite"), P("BlackKeys", "LV_KeysBlack"), P("Felt", "LV_Felt")


def cabriole(part, x, z, y_top, s, out):
    """a cabriole leg: a square profile swept down an S curve (knee out, ankle in, pad foot out); out = (dx, dz) unit toward the knee"""
    pts = []
    for t in np.linspace(0, 1, 14):
        y = y_top * (1 - t)
        k = 0.035 * math.sin(math.pi * min(t / 0.45, 1)) - 0.02 * math.sin(math.pi * max(0, (t - 0.45) / 0.45)) + (0.03 * (t - 0.9) / 0.1 if t > 0.9 else 0)
        pts.append((x + out[0] * k, y, z + out[1] * k))
    r = s / 2
    part.sweep(pts, [(-r, -r), (r, -r), (r, r), (-r, r)])
    part.lathe(pts[-1][0], pts[-1][2], 0.0, [(0, s * 0.9), (0.02, s * 0.85), (0.02, 0.0)], 10)


def piano():
    p = D["piano"]; (ax0, ax1), (zf, zb), Ht = p["x"], p["z"], p["h"]
    dz = lambda d: zb - d                                                        # depth from the back (keyboard toward -z)
    C, KB0, KB1, KT = 0.035, ax0 + 0.075, ax1 - 0.075, 0.71
    mahog.box(ax0, ax0 + C, 0.12, Ht - 0.02, dz(0.30), dz(0.0)); mahog.box(ax1 - C, ax1, 0.12, Ht - 0.02, dz(0.30), dz(0.0))   # upper cheeks
    mahog.box(ax0, ax0 + C, 0.62, KT + 0.04, dz(0.60), dz(0.30)); mahog.box(ax1 - C, ax1, 0.62, KT + 0.04, dz(0.60), dz(0.30))   # key cheeks
    mahog.box(ax0 + C, ax1 - C, 0.12, Ht - 0.04, dz(0.0), dz(0.02))             # back
    mahog.box(ax0 - 0.01, ax1 + 0.01, Ht - 0.025, Ht, dz(0.0), dz(0.32))        # top lid, 1 cm past the cheeks
    mahog.box(ax0 + C, ax1 - C, 0.82, Ht - 0.025, dz(0.26), dz(0.30))           # upper front panel (behind the music desk)
    mahog.box(ax0 + C, ax1 - C, 0.12, 0.60, dz(0.24), dz(0.27))                  # lower front panel
    mahog.box(ax0 + C + 0.04, ax1 - C - 0.04, 0.20, 0.52, dz(0.27), dz(0.282))  # its raised panel, 1.2 cm proud
    mahog.box(ax0, ax1, 0.08, 0.12, dz(0.0), dz(0.28))                           # plinth
    mahog.box(ax0 + C, ax1 - C, 0.60, 0.69, dz(0.27), dz(0.61))                  # keybed and key slip
    keysw.box(KB0, KB1, 0.69, KT, dz(0.40), dz(0.605))                           # white keys as one slab; lines are black-key gaps
    for i in range(1, 52):
        a = KB0 + (KB1 - KB0) * i / 52; felt.box(a - 0.0006, a + 0.0006, KT, KT + 0.0012, dz(0.455), dz(0.6055))
    wk = (KB1 - KB0) / 52; pat = [1, 1, 0, 1, 1, 1, 0]                          # A0 starts: black after A, (B none), C# D#, F# G# A#
    names = "ABCDEFG"; idx = 0
    for i in range(51):
        n = names[(i) % 7]
        if n in "ACDFG":
            a = KB0 + wk * (i + 1); keysb.box(a - 0.0065, a + 0.0065, KT, KT + 0.012, dz(0.40), dz(0.50))
    mahog.box(ax0 + C, ax1 - C, KT, 0.82, dz(0.33), dz(0.36))                   # fallboard, raised (vertical)
    mahog.box(ax0 + 0.25, ax1 - 0.25, 0.83, 0.98, dz(0.31), dz(0.325))          # music desk
    mahog.box(ax0 + 0.25, ax1 - 0.25, 0.83, 0.85, dz(0.325), dz(0.36))          # its lip
    for a in (ax0 + 0.075, ax1 - 0.075):                                         # front cabriole legs under the key cheeks
        cabriole(mahog, a, dz(0.55), 0.60, 0.05, (0, -1))
    for k, a in enumerate(((ax0 + ax1) / 2 - 0.07, (ax0 + ax1) / 2, (ax0 + ax1) / 2 + 0.07)):   # pedals
        brass.box(a - 0.018, a + 0.018, 0.05, 0.065, dz(0.28), dz(0.38))
    b = p["bench"]; (bx0, bx1), (bz0, bz1), bh = b["x"], b["z"], b["h"]
    mahog.box(bx0, bx1, bh - 0.035, bh, bz0, bz1); mahog.box(bx0 + 0.04, bx1 - 0.04, bh - 0.11, bh - 0.035, bz0 + 0.04, bz1 - 0.04)
    for (x, z, o) in ((bx0 + 0.06, bz0 + 0.06, (-0.7, -0.7)), (bx1 - 0.06, bz0 + 0.06, (0.7, -0.7)), (bx0 + 0.06, bz1 - 0.06, (-0.7, 0.7)), (bx1 - 0.06, bz1 - 0.06, (0.7, 0.7))):
        cabriole(mahog, x, z, bh - 0.11, 0.04, o)


# ------------------------------------------------------------------------------------------------ lamps (living.json lamps)
G = {k: P(k, m) for k, m in (("shade_burgundy", "LV_ShadeBurgundy"), ("shade_black", "LV_ShadeBlack"), ("shade_brass", "LV_ShadeBrass"),
                              ("bulb", "LV_Bulb"))}


def lamps():
    Lm = D["lamps"]
    for key, q in Lm.items():
        x, y, z = q["at"]
        if q["kind"] in ("candlestick", "urn"):
            rb, rt, s0, s1 = q["shade"]
            if q["kind"] == "candlestick":
                brass.lathe(x, z, y, [(0, 0.07), (0.015, 0.07), (0.03, 0.03), (0.08, 0.022), (0.10, 0.03), (0.12, 0.02), (0.30, 0.016), (0.33, 0.026), (0.36, 0.014), (s1 - 0.02, 0.008), (s1 - 0.02, 0.0)], 16)
            else:
                brass.lathe(x, z, y, [(0, 0.06), (0.02, 0.06), (0.05, 0.04), (0.14, 0.09), (0.24, 0.05), (0.28, 0.025), (0.32, 0.02), (s1 - 0.02, 0.008), (s1 - 0.02, 0.0)], 16)
            part = G["shade_burgundy"] if q["kind"] == "candlestick" else G["shade_black"]
            part.lathe(x, z, y + s0, [(0, rb), (s1 - s0, rt), (s1 - s0, 0.0)], 24)
            G["bulb"].lathe(x, z, y + (s0 + s1) / 2 - 0.05, [(0, 0.0001), (0.01, 0.022), (0.05, 0.03), (0.07, 0.012), (0.07, 0.0)], 10)
        elif q["kind"] == "banker":
            brass.lathe(x, z, y, [(0, 0.075), (0.02, 0.07), (0.025, 0.012), (0.30, 0.012), (0.30, 0.0)], 16)
            G["shade_brass"].lathe(x, z, y + 0.27, [(0, 0.12), (0.03, 0.09), (0.08, 0.05), (0.13, 0.025), (0.15, 0.0)], 20)
            G["bulb"].lathe(x, z, y + 0.27, [(0, 0.0001), (0.01, 0.02), (0.04, 0.025), (0.06, 0.0)], 10)
        else:   # piano: a brass bar shade on a curved arm from a round base on the top, shining down on the music desk
            brass.lathe(x, z, y, [(0, 0.06), (0.015, 0.055), (0.02, 0.01), (0.02, 0.0)], 14)
            brass.sweep([(x, y + 0.015, z), (x, y + 0.18, z), (x, y + 0.24, z - 0.04), (x, y + 0.24, z - 0.13)], [(0.006 * math.cos(q), 0.006 * math.sin(q)) for q in np.linspace(0, 2 * math.pi, 7)[:-1]])
            G["shade_brass"].sweep([(x - 0.18, y + 0.235, z - 0.15), (x + 0.18, y + 0.235, z - 0.15)], [(0.045 * math.cos(q), 0.045 * math.sin(q) + 0.0) for q in np.linspace(0, math.pi, 9)])
            G["bulb"].sweep([(x - 0.15, y + 0.215, z - 0.15), (x + 0.15, y + 0.215, z - 0.15)], [(0.012 * math.cos(q), 0.012 * math.sin(q)) for q in np.linspace(0, 2 * math.pi, 7)[:-1]])


# ------------------------------------------------------------------------------------------------ small dressing
porcelain, gilt = P("Porcelain", "LV_Porcelain"), P("Gilt", "LV_Gilt")
NC = {k: P("Nut_" + k, "LV_" + k) for k in ("Red", "Green", "White", "Black", "Skin", "Gold", "Brown", "Tin")}
STK = {"red": P("StockRed", "LV_Red"), "cream": P("StockCream", "LV_White"), "cuff": P("StockCuff", "LV_Porcelain")}


def brackets():
    """film 5650: gilt wall brackets on the foyer-side wall's front pier, each with a white porcelain (Staffordshire-style) dog"""
    for b in D["brackets"]:
        x, h = b["x"], b["h"]; z = Z0
        gilt.box(x - 0.11, x + 0.11, h - 0.02, h, z, z + 0.13)                   # shelf
        gilt.box(x - 0.03, x + 0.03, h - 0.20, h - 0.02, z, z + 0.02)            # back plate
        gilt.sweep([(x, h - 0.19, z + 0.02), (x, h - 0.12, z + 0.05), (x, h - 0.05, z + 0.10), (x, h - 0.02, z + 0.11)], [(-0.012, -0.01), (0.012, -0.01), (0.012, 0.01), (-0.012, 0.01)])
        porcelain.lathe(x, z + 0.07, h, [(0, 0.045), (0.02, 0.05), (0.09, 0.035), (0.11, 0.0)], 14)          # seated body
        porcelain.lathe(x, z + 0.075, h + 0.10, [(0, 0.03), (0.04, 0.035), (0.07, 0.02), (0.08, 0.0)], 12)   # head
        NC["Black"].box(x - 0.047, x - 0.037, h + 0.115, h + 0.15, z + 0.065, z + 0.085); NC["Black"].box(x + 0.037, x + 0.047, h + 0.115, h + 0.15, z + 0.065, z + 0.085)   # ears, just clear of the head
        NC["Gold"].box(x - 0.03, x + 0.03, h + 0.088, h + 0.098, z + 0.098, z + 0.112)                          # gilt collar


def nutcracker(x, z, y, coat, hat, beard=True):
    """film 10636: wooden nutcrackers, ~0.36 m: base, legs, coat, face, beard, hat (lathe parts)"""
    NC["Black"].box(x - 0.05, x + 0.05, y, y + 0.025, z - 0.04, z + 0.04)
    NC["Black"].lathe(x, z, y + 0.025, [(0, 0.032), (0.035, 0.032), (0.035, 0.0)], 12)            # boots
    NC["White"].lathe(x, z, y + 0.06, [(0, 0.029), (0.055, 0.028), (0.055, 0.0)], 12)             # trousers, standing on the boots
    NC[coat].lathe(x, z, y + 0.115, [(0, 0.04), (0.035, 0.037), (0.035, 0.0)], 14)                # coat below the belt
    NC["Gold"].lathe(x, z, y + 0.15, [(0, 0.042), (0.012, 0.042), (0.012, 0.0)], 14)              # belt
    NC[coat].lathe(x, z, y + 0.162, [(0, 0.036), (0.063, 0.034), (0.063, 0.0)], 14)               # coat above it
    NC["Skin"].lathe(x, z, y + 0.225, [(0, 0.028), (0.05, 0.03), (0.05, 0.0)], 12)
    if beard:
        NC["White"].box(x - 0.02, x + 0.02, y + 0.215, y + 0.25, z - 0.034, z - 0.026)
    NC[hat].lathe(x, z, y + 0.275, [(0, 0.032), (0.07, 0.03), (0.08, 0.0)], 12)


def small():
    ct = D["coffee_table"]; y = ct["h"]
    nutcracker(4.85, 14.05, y, "Red", "Red"); nutcracker(5.05, 14.25, y, "Green", "Brown"); nutcracker(5.28, 14.02, y, "Red", "Black")
    NC["Tin"].lathe(4.75, 14.3, y, [(0, 0.06), (0.11, 0.06), (0.12, 0.062), (0.13, 0.0)], 18)
    # the toy train: oval track (two rails, ties) on the floor, a black loco and two cars on the near straight
    t = D["train"]; (cx, cz), rx, rz = t["at"], t["rx"], t["rz"]
    Y = t.get("y", 0.0)   # 0.012 = on the rug (its top)
    oval = lambda q, k: (cx + (rx + k) * math.cos(q), 0.0, cz + (rz + k) * math.sin(q))
    qs = np.linspace(0, 2 * math.pi, 73)
    for k in (-0.017, 0.017):
        NC["Black"].sweep([(x, Y + 0.012, z) for x, _, z in (oval(q, k) for q in qs)], [(-0.002, -0.004), (0.002, -0.004), (0.002, 0.004), (-0.002, 0.004)])
    for q in qs[:-1:2]:
        x, _, z = oval(q, 0); tx, tz = -math.sin(q) * rx, math.cos(q) * rz; L = math.hypot(tx, tz); tx, tz = tx / L, tz / L
        NC["Brown"].face([(x - tz * 0.03 - tx * 0.006, Y + 0.010, z + tx * 0.03 - tz * 0.006), (x + tz * 0.03 - tx * 0.006, Y + 0.010, z - tx * 0.03 - tz * 0.006),
                          (x + tz * 0.03 + tx * 0.006, Y + 0.010, z - tx * 0.03 + tz * 0.006), (x - tz * 0.03 + tx * 0.006, Y + 0.010, z + tx * 0.03 + tz * 0.006)], (0, 1, 0))   # ties 1 cm up
    zt = cz - rz
    circ = lambda r, n=10: [(r * math.cos(q), r * math.sin(q)) for q in np.linspace(0, 2 * math.pi, n + 1)[:-1]]
    NC["Black"].sweep([(cx - 0.12, Y + 0.082, zt), (cx + 0.08, Y + 0.082, zt)], circ(0.03))                    # boiler
    NC["Black"].box(cx + 0.08, cx + 0.15, Y + 0.05, Y + 0.14, zt - 0.033, zt + 0.033)                      # cab
    NC["Black"].lathe(cx - 0.09, zt, Y + 0.105, [(0, 0.012), (0.04, 0.016), (0.04, 0.0)], 8)            # chimney
    for xw in (cx - 0.09, cx - 0.03, cx + 0.03, cx + 0.11, cx + 0.20, cx + 0.29, cx + 0.37, cx + 0.46):   # loco and both cars
        for zz in ((zt - 0.024, zt - 0.012), (zt + 0.012, zt + 0.024)):                              # wheels on the rail heads (rail top 0.016)
            NC["Red"].sweep([(xw, Y + 0.033, zz[0]), (xw, Y + 0.033, zz[1])], circ(0.016))
    for k in range(2):
        a = cx + 0.17 + k * 0.17
        NC["Black"].box(a, a + 0.15, Y + 0.05, Y + 0.12, zt - 0.03, zt + 0.03); NC["Brown"].box(a + 0.01, a + 0.14, Y + 0.12, Y + 0.13, zt - 0.03, zt + 0.03)
    # the white poinsettia on the tall stand (film 5650): gold foil pot, bract dome (the den's generator, smaller)
    sx, sz = D["stand"]["at"]; y0 = D["stand"]["h"]; rng = random.Random(5)
    NC["Gold"].lathe(sx, sz, y0, [(0, 0.08), (0.14, 0.11), (0.15, 0.115), (0.15, 0.0)], 16)
    LEAF = P("PoinLeaf", "LV_Leaf"); BR = P("PoinBract", "LV_Porcelain")
    LEAF.lathe(sx, sz, y0 + 0.15, [(0, 0.1), (0.04, 0.08), (0.04, 0.0)], 10)
    for k in range(70):
        ang = rng.uniform(0, 2 * math.pi); rr = rng.uniform(0.03, 0.24); yy = y0 + 0.2 + 0.18 * (1 - (rr / 0.24) ** 2) * rng.uniform(0.7, 1.0)
        L_ = rng.uniform(0.08, 0.13); W_ = L_ * 0.42; dx, dz_ = math.cos(ang), math.sin(ang)
        px, pz = sx + rr * dx * 0.6, sz + rr * dz_ * 0.6; tx, tz = px + dx * L_, pz + dz_ * L_; qx, qz = -dz_ * W_ / 2, dx * W_ / 2
        (BR if k % 4 else LEAF).face([(px, yy, pz), (px + dx * L_ * 0.45 + qx, yy + 0.01, pz + dz_ * L_ * 0.45 + qz), (tx, yy - 0.02, tz), (px + dx * L_ * 0.45 - qx, yy + 0.01, pz + dz_ * L_ * 0.45 - qz)], (0, 1, 0))
    RUG = P("Rug", "LV_Rug"); (rx0, rx1), (rz0, rz1) = D["rug"]["x"], D["rug"]["z"]
    RUG.face([(rx0, 0.012, rz0), (rx1, 0.012, rz0), (rx1, 0.012, rz1), (rx0, 0.012, rz1)], (0, 1, 0), [(0, 0), (1, 0), (1, 1), (0, 1)])
    for (a, b), n in ((((rx0, rz0), (rx1, rz0)), (0, 0, -1)), (((rx1, rz0), (rx1, rz1)), (1, 0, 0)), (((rx1, rz1), (rx0, rz1)), (0, 0, 1)), (((rx0, rz1), (rx0, rz0)), (-1, 0, 0))):
        NC["Red"].face([(a[0], 0.0, a[1]), (b[0], 0.0, b[1]), (b[0], 0.012, b[1]), (a[0], 0.012, a[1])], n)
    return [LEAF, BR, RUG]


# ------------------------------------------------------------------------------------------------ the Christmas tree's C7 bulbs and gifts
# The tree itself is the user's Asset Store tree (AlterEgos ChristmasTree.prefab, placed by StoreProps: store_props.json living_tree,
# uniform scale to D["tree"]["h"]); its warm-white mini lights are left out (hide_parts): the film's tree (10600) carries multicolour
# C7 bulbs, generated here on the tree's own foliage envelope. Envelope: the 85th-percentile radius of the model's Tips + DouglasFir
# vertices per 10 cm of height (native units, 2.55 m tall to the star tip; scratchpad read of its FBX, Oct 16), scaled with the tree.
TREE_R85 = [0.654, 0.551, 0.533, 0.534, 0.563, 0.615, 0.600, 0.655, 0.624, 0.592, 0.595, 0.584, 0.583, 0.528, 0.521, 0.505, 0.407, 0.400,
            0.356, 0.311, 0.265, 0.183, 0.107]
TREE_NATIVE_H = 2.55
C7 = {c: P("C7_" + c, "LV_C7" + c) for c in ("Red", "Green", "Blue", "Orange", "Pink", "White")}
GIFT = {c: P("Gift_" + c, "LV_Gift" + c) for c in ("Red", "Green", "Gold", "Blue", "Ribbon")}


def tree():
    t = D["tree"]; cx, cz = t["at"]; k = t["h"] / TREE_NATIVE_H; rng = random.Random(1990); cols = list(C7)
    for i in range(150):   # C7 bulbs standing out of the outer foliage, every colour in turn (film 10600)
        hb = rng.uniform(0.25, 2.15)
        r = float(np.interp(hb, np.arange(len(TREE_R85)) * 0.1 + 0.05, TREE_R85)) * 1.05 * k
        a = rng.uniform(0, 2 * math.pi); x, z, y = cx + r * math.cos(a), cz + r * math.sin(a), hb * k
        C7[cols[i % 6]].lathe(x, z, y, [(0, 0.008), (0.012, 0.011), (0.03, 0.014), (0.05, 0.008), (0.06, 0.0)], 8)
    # gifts round the foot on the room side, outside the lowest branches (0.84 native = 0.79 m)
    rx, rz = D["rug"]["x"], D["rug"]["z"]
    for (a, d, w, dd, h, c) in ((-20, 1.02, 0.36, 0.28, 0.22, "Red"), (15, 1.0, 0.30, 0.30, 0.25, "Green"), (-55, 1.0, 0.24, 0.24, 0.16, "Gold"),
                                (45, 1.02, 0.40, 0.26, 0.14, "Blue"), (-85, 0.98, 0.28, 0.22, 0.20, "Green")):
        gx, gz = cx + d * math.cos(math.radians(a)), cz + d * math.sin(math.radians(a))
        y0 = 0.013 if rx[0] - 0.25 < gx < rx[1] + 0.25 and rz[0] - 0.25 < gz < rz[1] + 0.25 else 0.0   # on (or at the edge of) the rug: its top
        if y0 and not (rx[0] < gx - w / 2 and gx + w / 2 < rx[1] and rz[0] < gz - dd / 2 and gz + dd / 2 < rz[1]):
            gx = max(gx, rx[0] + w / 2 + 0.01); gz = min(gz, rz[1] - dd / 2 - 0.01)           # wholly on it, not straddling its edge
        GIFT[c].box(gx - w / 2, gx + w / 2, y0, y0 + h, gz - dd / 2, gz + dd / 2); h += y0
        GIFT["Ribbon"].box(gx - 0.02, gx + 0.02, h, h + 0.004, gz - dd / 2 - 0.004, gz + dd / 2 + 0.004)
        GIFT["Ribbon"].box(gx - w / 2 - 0.004, gx + w / 2 + 0.004, h, h + 0.004, gz - 0.02, gz + 0.02)


def export(parts, mats, out, root_name):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    M = {k: material(k, *v) for k, v in mats.items()}
    coll = bpy.context.scene.collection
    root = bpy.data.objects.new(root_name, None); coll.objects.link(root)
    for p in parts:
        if p.f:
            ob = p.build(coll, M); ob.parent = root
            if p in SMOOTH:
                for poly in ob.data.polygons:
                    poly.use_smooth = True
    out.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.gltf(filepath=str(out), export_format="GLB", export_yup=True, export_apply=True)
    print("wrote", out, {p.name: len(p.f) for p in parts if p.f})


damask_texture(); rug_texture()
for name in ("rear_den_side", "rear_foyer_side"):
    double_hung(WIN[name])
for name in ("front_french_foyer_side", "front_french_den_side"):
    french(WIN[name])
dress_french(WIN["front_french_foyer_side"], 0.6); dress_french(WIN["front_french_den_side"], 2.2)
dress_rear(WIN["rear_den_side"], 4.1, (14.80, 15.96)); dress_rear(WIN["rear_foyer_side"], 5.3, (11.66, 12.78))   # Marina f165 drape runs (foyer side kept 9 cm off the side wall)
export([paint, glass, brass, voile, hem, damask, tie], {"LV_Paint": ((0.88, 0.87, 0.83), 0.35), "LV_Glass": ((0.1, 0.12, 0.13), 0.05), "LV_Brass": ((0.75, 0.56, 0.25), 0.3),
                                                        "SH_Voile": ((0.95, 0.94, 0.91), 0.8), "SH_Hem": ((0.95, 0.94, 0.91), 0.8), "LV_Damask": ((0.15, 0.2, 0.15), 0.6),
                                                        "LV_Tie": ((0.04, 0.12, 0.05), 0.6)}, MOD / "LivingWindows.glb", "LivingWindows_HiFi")

paint, glass, brass = P("Paint", "LV_Paint"), P("Glass", "LV_Glass"), P("Brass", "LV_Brass")
SMOOTH.clear()
fireplace(); fire_screen(); stockings(); (piano() if "replaced_by" not in D["piano"] else None); lamps(); brackets(); extra = small(); tree()
parts = [white, black, brick, slate, wood_log, screen_mesh, brass, mahog, keysw, keysb, felt, porcelain, gilt] + list(G.values()) + list(NC.values()) + \
        [STK["red"], STK["cream"], STK["cuff"]] + extra + list(C7.values()) + list(GIFT.values())
MATS = {"LV_Paint": ((0.88, 0.87, 0.83), 0.35), "LV_Iron": ((0.02, 0.02, 0.02), 0.6), "LV_Firebrick": ((0.16, 0.06, 0.04), 0.9), "LV_Slate": ((0.04, 0.04, 0.045), 0.4),
        "LV_Log": ((0.12, 0.07, 0.04), 0.9), "LV_ScreenMesh": ((0.03, 0.03, 0.03), 0.5), "LV_Brass": ((0.75, 0.56, 0.25), 0.3), "LV_Mahogany": ((0.12, 0.04, 0.025), 0.3),
        "LV_KeysWhite": ((0.9, 0.88, 0.82), 0.25), "LV_KeysBlack": ((0.01, 0.01, 0.01), 0.3), "LV_Felt": ((0.02, 0.02, 0.02), 0.9), "LV_Porcelain": ((0.92, 0.91, 0.88), 0.2),
        "LV_Gilt": ((0.7, 0.52, 0.22), 0.35), "LV_ShadeBurgundy": ((0.35, 0.04, 0.06), 0.8), "LV_ShadeBlack": ((0.02, 0.02, 0.02), 0.6), "LV_ShadeBrass": ((0.75, 0.56, 0.25), 0.3),
        "LV_Bulb": ((1, 0.95, 0.85), 0.2), "LV_Red": ((0.55, 0.04, 0.04), 0.5), "LV_Green": ((0.05, 0.25, 0.08), 0.5), "LV_White": ((0.85, 0.83, 0.78), 0.5),
        "LV_Black": ((0.02, 0.02, 0.02), 0.4), "LV_Skin": ((0.80, 0.60, 0.48), 0.6), "LV_Gold": ((0.75, 0.56, 0.2), 0.3), "LV_Brown": ((0.25, 0.14, 0.07), 0.7),
        "LV_Tin": ((0.06, 0.30, 0.12), 0.4), "LV_Leaf": ((0.06, 0.20, 0.06), 0.6), "LV_Rug": ((0.45, 0.05, 0.06), 0.9),
        }
MATS.update({"LV_C7" + c: (rgb, 0.3) for c, rgb in (("Red", (0.9, 0.05, 0.05)), ("Green", (0.05, 0.8, 0.1)), ("Blue", (0.1, 0.2, 0.95)),
                                                     ("Orange", (1.0, 0.45, 0.05)), ("Pink", (0.95, 0.2, 0.6)), ("White", (1.0, 0.92, 0.8)))})
MATS.update({"LV_Gift" + c: (rgb, 0.6) for c, rgb in (("Red", (0.55, 0.03, 0.04)), ("Green", (0.04, 0.3, 0.08)), ("Gold", (0.7, 0.5, 0.15)), ("Blue", (0.08, 0.12, 0.45)), ("Ribbon", (0.85, 0.8, 0.7)))})
export(parts, MATS, MOD / "LivingBuiltins.glb", "LivingBuiltins_HiFi")
