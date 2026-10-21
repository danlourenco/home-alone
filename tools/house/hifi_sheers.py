"""hifi_sheers: window treatments as cloth, not boards (DEVIATIONS 41: "the sheer looks terrible; figure out how to do it properly").

Every piece is a smooth-shaded sheet with shared vertices (no boxes), folds with an irregular period so they do not read as a
corrugated board, UVs along the fabric's own length (arc length across, height down) for the woven voile texture, and a denser
hem and heading on the sheers. Materials (SpecGreybox.Curtains): HDRP Lit "Translucent" with a thin-object diffusion profile, so
a backlit panel transmits light; the sheers are also alpha-blended (the voile texture's alpha), double sided, no shadows.

Dining room front French windows (both), prototype (Oct 16):
  - interior from Marina Part 1 1118-1128 s: ivory pinch-pleated side panels to the floor, tied back at ~0.92 m with a fabric
    tie-back; a box-pleated valance whose bottom covers the casing head (2.10) and whose top is ~2.39, running ~0.20 m past the
    casing each side; panel width at the rod ~0.25 of the valance's run (frame 1128).
  - sheers from the film (frame 4382, the front from the street): white sheers drawn across the French windows, split at the
    meeting stiles. Marina's model shows clear glass; the film is the authority for what the windows show (memory: exterior = film).
  - depths off the wall's room face (all >= 1 cm clear of each other and of the casing (2 cm) and cap rail (3 cm)): sheer
    0.045-0.075, drape >= 0.093, valance face 0.20.

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P tools/house/hifi_sheers.py
  -> unity/HomeAlone/Assets/Models/Foyer/Sheers.glb (+ Assets/Textures/Sheers/voile.png, generated, tileable, 0.20 m repeat)
"""
import json
import math
import sys
from pathlib import Path

import bpy
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hifi_lib import Part, material   # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "unity/HomeAlone/Assets/Models/Foyer/Sheers.glb"
TEX = ROOT / "unity/HomeAlone/Assets/Textures/Sheers/voile.png"
SPEC = json.loads((ROOT / "spec/house_spec.ground.json").read_text())
WIN = {w["name"]: w for w in SPEC["windows"]}
ROOMS = {s["name"]: s["polygon_xz"] for s in SPEC["spaces"]}
TILE = 0.20                                   # voile texture repeat, metres of fabric
CASING = 0.07                                 # SpecGreybox.CasingW


def inside(poly, x, z):
    c = False
    for (x0, z0), (x1, z1) in zip(poly, poly[1:] + poly[:1]):
        if (z0 > z) != (z1 > z) and x < x0 + (z - z0) * (x1 - x0) / (z1 - z0):
            c = not c
    return c


def frame(w):
    """P(u, y, d): u along the wall (spec coordinate), y above the ground floor, d into the room from the wall's room face."""
    W0, (a, b), poly = w["wall_coord_spec"], w["span_spec"], ROOMS[w["room"]]
    m = (a + b) / 2
    if w["wall_axis"] == "x":
        r = 1 if inside(poly, W0 + 0.1, m) else -1
        return lambda u, y, d: (W0 + r * d, y, u)
    r = 1 if inside(poly, m, W0 + 0.1) else -1
    return lambda u, y, d: (u, y, W0 + r * d)


SMOOTH = []                                   # parts drawn smooth (cloth)


def sheet(part, P, ts, ys, pos):
    """A cloth sheet: pos(t, y) -> (u, d) or (u, d, y') over the grid ts x ys; shared vertices (smooth normals), UV = (arc length, height) / TILE,
    front faces toward the room."""
    i0 = len(part.v)
    rows = []
    for y in ys:
        ud = [(pos(t, y) + (y,))[:3] for t in ts]                    # pos may also return its own height (a shaped edge)
        s = [0.0]
        for (u0, d0, _), (u1, d1, _) in zip(ud, ud[1:]):
            s.append(s[-1] + math.hypot(u1 - u0, d1 - d0))
        rows.append([(P(u, yy, d), (sk / TILE, yy / TILE)) for (u, d, yy), sk in zip(ud, s)])
    for row in rows:
        part.v += [p for p, _ in row]
    nt = len(ts)
    # winding: the normal of the first quad must point into the room (+d)
    probe = [np.array(part.v[i0 + k]) for k in (0, 1, nt + 1)]
    n = np.cross(probe[1] - probe[0], probe[2] - probe[0])
    into = np.array(P(0, 0, 1)) - np.array(P(0, 0, 0))
    flip = float(np.dot(n, into)) < 0
    for j in range(len(ys) - 1):
        for k in range(nt - 1):
            q = [(j, k), (j, k + 1), (j + 1, k + 1), (j + 1, k)]
            if flip:
                q.reverse()
            part.f.append(tuple(i0 + jj * nt + kk for jj, kk in q))
            part.uv[len(part.f) - 1] = [rows[jj][kk][1] for jj, kk in q]
    if part not in SMOOTH:
        SMOOTH.append(part)


def lin(a, b, step):
    n = max(2, int(math.ceil(abs(b - a) / step)) + 1)
    return [a + (b - a) * i / (n - 1) for i in range(n)]


def wobble(x, seed):
    return 0.22 * math.sin(7.3 * x + seed) + 0.12 * math.sin(17.9 * x + 2.1 * seed)


def sheer_panel(body, hem, P, a, b, y0, y1, dc, seed, P0=0.075, A0=0.011):
    """A sheer hanging straight from a rod, u in [a, b]: folds of irregular period (~P0) and depth (~A0, a little deeper toward the
    floor), a 5 cm hem at the bottom and a 4 cm heading at the top (denser material)."""
    us = np.linspace(a, b, 2000)
    ph = np.concatenate([[0], np.cumsum(2 * math.pi / (P0 * (1 + np.array([wobble(u, seed) for u in us[1:]])))) * (us[1] - us[0])])
    def pos(t, y):
        u = a + t * (b - a)
        A = A0 * (1 + 0.3 * math.sin(5.1 * u + 1.3 * y + seed)) * (1 + 0.15 * (1 - (y - y0) / (y1 - y0)))
        return u, dc + A * math.sin(float(np.interp(u, us, ph)) + seed)
    ts = lin(0, 1, 0.006 / (b - a))
    sheet(hem, P, ts, lin(y0, y0 + 0.05, 0.025), pos)
    sheet(body, P, ts, lin(y0 + 0.05, y1 - 0.04, 0.10), pos)
    sheet(hem, P, ts, lin(y1 - 0.04, y1, 0.02), pos)


def drape(part, band, P, uo, s, y0, y1, yt, Wt, Wtie, Wb, dc, N=5, A0=0.018, Amax=0.032, seed=0.0):
    """A side panel hung from its outer edge uo (s = +1/-1: the direction toward the opening), width Wt at the top, gathered to Wtie
    over +-h at the tie height yt by a fabric tie-back, flaring to Wb at the hem; N folds, deeper where gathered, the gathered part
    standing a little toward the room."""
    h = 0.035
    def w(y):
        if y >= yt + h:
            return Wtie + (Wt - Wtie) * min(1.0, max(0.0, (y - yt - h) / (y1 - yt - h))) ** 0.55
        if y <= yt - h:
            return Wtie + (Wb - Wtie) * min(1.0, max(0.0, (yt - h - y) / (yt - h - y0))) ** 0.8
        return Wtie
    def amp(y):
        return min(Amax, A0 * (Wt / w(y)) ** 0.6)
    def pos(t, y):
        g = (Wt / w(y) - 1) / (Wt / Wtie - 1)
        ph = 2 * math.pi * N * t + 0.5 * math.sin(3.1 * t + 0.7 * y + seed)
        return uo + s * t * w(y), dc + amp(y) * math.sin(ph) + 0.012 * g
    ys = sorted(set(lin(y0, yt - h, 0.06) + lin(yt - h, yt + h, 0.035) + lin(yt + h, y1, 0.05)))
    sheet(part, P, lin(0, 1, 1 / (N * 14)), ys, pos)
    # the tie-back: a 5 cm band from a hook on the wall beside the panel's outer edge, round the gathered panel (front, inner edge,
    # and back between the panel and the sheer, d 0.084) and back to the hook; >= 6 mm clear of both
    dmax, dbk, r = dc + Amax + 0.012 + 0.010, 0.084, 0.030
    uo_, ui_ = uo - s * 0.012, uo + s * (Wtie + 0.012)                 # outer leg (hook side), inner edge
    def arc(cu, cd, a0, a1):                                           # corner arcs in the (along-s, d) plane
        return [(cu + s * r * math.cos(a), cd + r * math.sin(a)) for a in np.linspace(a0, a1, 7)[1:-1]]
    pts = [(uo_, -0.005), (uo_, dmax - r)] + arc(uo_ + s * r, dmax - r, math.pi, math.pi / 2) + [(uo_ + s * r, dmax), (ui_ - s * r, dmax)]
    pts += arc(ui_ - s * r, dmax - r, math.pi / 2, 0) + [(ui_, dmax - r), (ui_, dbk + r)] + arc(ui_ - s * r, dbk + r, 0, -math.pi / 2)
    pts += [(ui_ - s * r, dbk), (uo_ + s * 0.010, dbk)]
    lens = [(0.0035 * math.cos(a) * (1 - 0.6 * abs(math.sin(a)) ** 4), 0.025 * math.sin(a))    # a soft fabric band: a flat lens in section
            for a in np.linspace(-math.pi / 2, 3 * math.pi / 2, 17)[:-1]]
    band.sweep([P(u, yt, d) for u, d in pts], lens)


def valance(part, P, va, vb, y0, y1, dv, PV=0.05, depth=0.009):
    """A box-pleated valance: a pleated face at dv (squared-off folds, smooth normals), flat returns to the wall and a dust board."""
    def pos(t, y):
        u = va + t * (vb - va)
        return u, dv + depth * math.tanh(4 * math.sin(2 * math.pi * (u - va) / PV)) / math.tanh(4)
    sheet(part, P, lin(0, 1, 0.004 / (vb - va)), [y0, (y0 + y1) / 2, y1], pos)
    for u, tw in ((va, -1), (vb, 1)):
        n = np.array(P(u + tw, 0, 0)) - np.array(P(u, 0, 0))
        part.face([P(u, y0, 0), P(u, y0, dv), P(u, y1, dv), P(u, y1, 0)], tuple(n))
    part.face([P(va, y1, 0), P(vb, y1, 0), P(vb, y1, dv), P(va, y1, dv)], (0, -1, 0))


def voile_texture():
    """Tileable woven voile, 512 px over 0.20 m: alpha = cover factor (mean ~0.8), warp streaks (yarn thickness varying across),
    slubs (elongated along the warp), faint weft bars and a fine thread grid that mips away. Periodic noise by FFT filtering."""
    rng = np.random.default_rng(41)
    N = 512
    k = np.fft.fftfreq(N) * N
    def noise(sx, sy):
        F = np.fft.fft2(rng.standard_normal((N, N))) * np.exp(-(k[None, :] / sx) ** 2 - (k[:, None] / sy) ** 2)
        a = np.real(np.fft.ifft2(F)); return (a - a.mean()) / a.std()
    warp = noise(60, 0.5)            # varies across (x = U), constant along the warp (y = V)
    slub = noise(80, 6)
    weft = noise(0.5, 40)
    yy, xx = np.mgrid[0:N, 0:N]
    grid = np.cos(2 * math.pi * xx / 3) * np.cos(2 * math.pi * yy / 3)
    alpha = np.clip(0.80 + 0.06 * warp + 0.05 * slub + 0.025 * weft + 0.03 * grid, 0.55, 0.96)
    rgb = np.clip(0.97 + 0.02 * slub, 0, 1)
    px = np.stack([rgb, rgb * 0.995, rgb * 0.985, alpha], -1).astype(np.float32)
    img = bpy.data.images.new("voile", N, N, alpha=True)
    img.pixels.foreach_set(px.ravel())
    TEX.parent.mkdir(parents=True, exist_ok=True)
    img.filepath_raw = str(TEX); img.file_format = "PNG"; img.save()


bpy.ops.wm.read_factory_settings(use_empty=True)
voile, hem, ivory, tie = (Part("Voile", "SH_Voile"), Part("VoileHem", "SH_Hem"), Part("Drape", "SH_DrapeIvory"),
                          Part("TieBack", "SH_DrapeIvory"))

# ---- dining room, front French windows (both alike; Marina 1118-1128 s, film 4382)
for name, seed in (("front_french_sunroom_side", 0.0), ("front_french_foyer_side", 1.7)):
    w = WIN[name]; P = frame(w); lo, hi = w["span_spec"]; head = w["head_m"]
    VB0, VB1, RET = head + CASING, 2.39, 0.20                        # valance bottom on the casing head, top, run past the casing
    va, vb = lo - CASING - RET, hi + CASING + RET
    valance(ivory, P, va, vb, VB0, VB1, 0.20)
    top = VB0 + 0.02                                                 # rods hidden behind the valance
    mid = (lo + hi) / 2
    sheer_panel(voile, hem, P, lo - CASING - 0.06, mid - 0.005, 0.015, top, 0.060, seed)
    sheer_panel(voile, hem, P, mid + 0.005, hi + CASING + 0.06, 0.015, top, 0.060, seed + 3.1)
    Wt = 0.25 * (vb - va)
    for uo, s in ((va + 0.03, 1), (vb - 0.03, -1)):
        drape(ivory, tie, P, uo, s, 0.012, top, 0.92, Wt, 0.16, 0.24, 0.125, seed=seed + s)

# ---- den windows (film 4382 / 2508 / 6399 / 5545 from the street: white sheers across the bay like every front window; Marina: "her
# sheers hide" the den's stools too, den.json). Oct 21 (house-split rule 4, film first): across the glass between the casings' inner
# edges, from 1 cm over the stool to the head (behind the valance), 3 cm into the room: clear of the casings (2 cm proud), the stool,
# and the drapes' backs (6 cm) by >= 1.5 cm with the fold depth held to 0.8 cm (tools/house/hifi_den.py owns the drapes and valance)
DEN = json.loads((ROOT / "spec/dressing/den.json").read_text())["windows"]
for name, seed in (("front_wide", 0.9), ("side_twin", 2.4)):
    w = WIN[name]; P = frame(w); lo, hi = w["span_spec"]
    sheer_panel(voile, hem, P, lo + 0.005, hi - 0.005, w["sill_m"] + DEN["stool"]["t"] + 0.01, w["head_m"], 0.030, seed, A0=0.008)

# ---- kitchen windows (film 6902 / 10448: the sink-wall and end-wall windows): a red shirred valance with ballooned swags, red
# panels tied back each side, a white sheer across the glass to the stool. Marina (Part 1 889, 1101, 1104 s) dresses all four
# kitchen windows alike (red valance cabinet-to-cabinet, side panels tied back), so the film's dressing goes on all four; her panels
# are cream and she has no sheers: the film governs the kitchen's look. The breakfast window (Marina 931 s: red valance) gets the same.
KIT = json.loads((ROOT / "spec/dressing/kitchen.json").read_text())
CEIL = 2.438


def room_to_cabinet(w):
    """Free run beyond each casing along the wall before an upper or tall cabinet standing against it: (low side, high side)."""
    W0, (lo, hi) = w["wall_coord_spec"], w["span_spec"]
    free = [0.15, 0.15]
    for b in KIT["uppers"] + KIT["talls"]:
        xs, zs = (b["x"], b["z"]) if "x" in b else ([min(p[0] for p in b["poly"]), max(p[0] for p in b["poly"])],
                                                    [min(p[1] for p in b["poly"]), max(p[1] for p in b["poly"])])
        wa, ua = (xs, zs) if w["wall_axis"] == "x" else (zs, xs)
        if min(abs(wa[0] - W0), abs(wa[1] - W0)) > 0.02:
            continue
        if ua[1] <= lo:
            free[0] = min(free[0], lo - CASING - ua[1] - 0.008)
        elif ua[0] >= hi:
            free[1] = min(free[1], ua[0] - hi - CASING - 0.008)
    return free


def ruffle_valance(part, P, va, vb, y0, y1, dv, seed, rise=0.03, puff=0.018):
    """A shirred valance: fine irregular gathers (~4 cm), the bottom edge in swags (lowest mid-swag at y0, drawn up `rise` between
    them) that balloon toward the room; returns to the wall at both ends and a dust board on top."""
    n = max(2, round((vb - va) / 0.33))
    us = np.linspace(va, vb, 1500)
    ph = np.concatenate([[0], np.cumsum(2 * math.pi / (0.04 * (1 + np.array([wobble(u, seed) for u in us[1:]])))) * (us[1] - us[0])])
    def pos(t, s):
        u = va + t * (vb - va); sw = abs(math.sin(math.pi * n * t))
        yb = y0 + rise * (1 - sw)
        return u, dv + 0.009 * math.sin(float(np.interp(u, us, ph))) + puff * (1 - s) ** 2 * sw, yb + s * (y1 - yb)
    sheet(part, P, lin(0, 1, 0.004 / (vb - va)), lin(0, 1, 0.1), pos)
    for u, tw in ((va, -1), (vb, 1)):
        nrm = np.array(P(u + tw, 0, 0)) - np.array(P(u, 0, 0))
        part.face([P(u, y0 + rise, 0), P(u, y0 + rise, dv), P(u, y1, dv), P(u, y1, 0)], tuple(nrm))
    part.face([P(va, y1, 0), P(vb, y1, 0), P(vb, y1, dv), P(va, y1, dv)], (0, -1, 0))


red, redtie = Part("Red", "SH_Red"), Part("RedTieBack", "SH_Red")
for name, seed in (("sink", 0.4), ("side_upper", 1.1), ("seat_1", 2.3), ("seat_2", 2.9), ("breakfast_rear", 3.7)):
    w = WIN[name]; P = frame(w); lo, hi = w["span_spec"]; head, sill = w["head_m"], w["sill_m"]
    f0, f1 = room_to_cabinet(w)
    va, vb = lo - CASING - f0, hi + CASING + f1
    VB0 = head + CASING
    VB1 = min(VB0 + 0.25, CEIL - 0.015)
    ruffle_valance(red, P, va, vb, VB0, VB1, 0.20, seed)
    top = VB0 + 0.05                                                   # rods hidden in the valance (its swags rise 3 cm)
    # over the sink the faucet's gooseneck (KitchenCabinets.glb, brass to 1.283 m, 2.4 cm off the wall) stands where the hem
    # would be: that sheer stops 1.5 cm above it (film 10448 shows it to the stool behind the faucet; ours leans back further)
    hem_y = 1.298 if name == "side_upper" else sill + 0.012
    sheer_panel(voile, hem, P, max(va + 0.05, lo - CASING - 0.04), min(vb - 0.05, hi + CASING + 0.04), hem_y, top, 0.060, seed)
    yt = sill + 0.42 * (head - sill)                                   # film 10448: tied ~0.4 of the glass up
    for uo, s in ((va + 0.03, 1), (vb - 0.03, -1)):
        drape(red, redtie, P, uo, s, sill + 0.012, top, yt, 0.22, 0.11, 0.15, 0.125, N=4, A0=0.014, Amax=0.026, seed=seed + s)

# ---- the back door's sash curtains (film 6902, 6910: a white sheer shirred on rods above and below the glazing with a ruffle
# under the lower rod; narrow red panels hanging straight either side, also with a bottom ruffle). Replaces the board-like panels
# and flat sheer that hifi_back_door.py had. Leaf geometry from hifi_back_door.py: glazing 0.92-1.935 m, stiles 0.115, leaf room
# face 2 cm inside the wall's room face (d = -0.02); its brass rod over the glazing stays (hifi_back_door.py).
w = WIN["back_door"]; P = frame(w); Z0, Z1 = w["span_spec"]
GL0, GL1 = 0.92, 1.935
zi0, zi1 = Z0 + 0.022 + 0.115, Z1 - 0.022 - 0.115


def sash(body, frill, P, a, b, y0, y1, dc, A, P0, seed):
    """A shirred sash panel: fine gathers between a heading at y1 and a pocket at y0, a 3 cm ruffle below the pocket (flaring)."""
    us = np.linspace(a, b, 800)
    ph = np.concatenate([[0], np.cumsum(2 * math.pi / (P0 * (1 + np.array([wobble(u, seed) for u in us[1:]])))) * (us[1] - us[0])])
    def pos(t, y):
        u = a + t * (b - a)
        fl = 1 + 1.2 * max(0.0, (y0 - y) / 0.03)                      # the ruffle flares to 2.2x
        return u, dc + A * fl * math.sin(float(np.interp(u, us, ph)))
    ts = lin(0, 1, 0.003 / (b - a))
    sheet(frill, P, ts, lin(y0 - 0.03, y0 + 0.015, 0.0075), pos)
    sheet(body, P, ts, lin(y0 + 0.015, y1 - 0.015, 0.08), pos)
    sheet(frill, P, ts, lin(y1 - 0.015, y1, 0.0075), pos)


# separate objects (Leaf*): they hang on the back door's leaf and swing with it (SpecGreybox.BackDoorInteractions, Oct 19)
lvoile, lhem, lred = Part("LeafSheer", "SH_Voile"), Part("LeafSheerHem", "SH_Hem"), Part("LeafRed", "SH_Red")
sash(lvoile, lhem, P, zi0 - 0.01, zi1 + 0.01, GL0 - 0.005, GL1 + 0.015, -0.010, 0.003, 0.025, 5.0)
PW = 0.17
for zo, s in ((zi0 - 0.02, 1), (zi1 + 0.02, -1)):
    a, b = sorted((zo, zo + s * PW))
    sash(lred, lred, P, a, b, GL0 - 0.005, GL1 + 0.02, 0.008, 0.004, 0.03, 6.0 + s)

voile_texture()
M = {"SH_Voile": material("SH_Voile", (0.95, 0.94, 0.91), 0.8), "SH_Hem": material("SH_Hem", (0.95, 0.94, 0.91), 0.8),
     "SH_DrapeIvory": material("SH_DrapeIvory", (0.80, 0.77, 0.66), 0.9), "SH_Red": material("SH_Red", (0.55, 0.02, 0.04), 0.5)}
coll = bpy.context.scene.collection
root = bpy.data.objects.new("Sheers_HiFi", None); coll.objects.link(root)
parts = (voile, hem, ivory, tie, red, redtie, lvoile, lhem, lred)
for p in parts:
    if p.f:
        ob = p.build(coll, M); ob.parent = root
        if p in SMOOTH:
            for poly in ob.data.polygons:
                poly.use_smooth = True
OUT.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(OUT), export_format="GLB", export_yup=True, export_apply=True)
print("wrote", OUT, {p.name: len(p.f) for p in parts})
