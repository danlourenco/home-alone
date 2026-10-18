"""film_wallpaper: the foyer's wallpaper as the FILM shows it (red damask on cream, green accents), one repeat cut from a near
frontal still, lighting flattened, side edges blended to wrap. User, Oct 15: "sample the real wallpaper from the movie stills from
the foyer and apply it appropriately" (Marina's paper, spec/dressing/wallpaper.png, is a brown variant).

Source: film 1170 (daylight, near frontal): the panel right of the living-room opening's casing, x 1510-1890. Its repeat by 2-D
autocorrelation of the red channel (tools in this file's history): 442 px down (peak 0.29 at (442, -5)) and a half-drop at
(224, -187) / (220, 182), so a straight repeat 442 px tall and ~370 px wide (2 x 185). Film 780 (lamplight) agrees on the motif.
The tile is cut from rows 60-502, above the brass switch plate. Scale is AUTHORED: 442 px = 0.533 m, a
standard 21 in damask repeat (no ruler of known size in the panel); the width follows the pixels.

  uv run --with numpy --with scipy --with pillow python -I tools/house/film_wallpaper.py
  -> spec/dressing/wallpaper_film.png and wallpaper_film.json ({"repeat_m": [w, h]}); foyer_dressing.py uses it when present.
  uv run --with numpy --with scipy --with pillow python -I tools/house/film_wallpaper.py --kitchen
  -> spec/dressing/kitchen_wallpaper.png / .json: the kitchen's paper (see kitchen() below)
  ... film_wallpaper.py --buzz -> spec/dressing/buzz_wallpaper.png / .json: Buzz's paper (see buzz() below)
"""
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import gaussian_filter

import sys

ROOT = Path(__file__).resolve().parents[2]


def kitchen():
    """The kitchen and breakfast paper (user, Oct 16: "match it as closely to the movie as possible"): cream ground, columns of red
    and blue bouquets alternating with small red medallions, green sprig vines between the columns. Film 6910 (daylight, frontal):
    the panel right of the back door's casing, x 1300-1600, rows 235-1050 (below the switch plate, left of the counter).
    Lattice by autocorrelation: 362 px down (peak 0.31; 6910's rows drift 7 px left per repeat: perspective, sheared out) and the
    next bouquet column 184 px across, dropped half a repeat (181 px; peak at (180-186, -200..-196) on the bouquet column; vines
    alone give a false 82 px match). So a straight tile is two columns: 368 x 362 px, the right half the same strip half a repeat
    down; built from ONE strip (x 1356-1542, rows 480-1023: its edges fall on plain ground between a vine and a bouquet, below the switch plate's glare) of the photo, no patching; column pitch 186 (vines 185-190 apart, bouquets 180-186).
    Metric size, film 6902 (the same wall beside the back door, near frontal), multi-peak autocorrelation: motifs every 42.5 px down
    (bouquet and medallion alternate in a column: half a repeat; peaks 42/85/128/170) and columns every 45.5 px across (45/91/136/182),
    so one tile is 91.0 x 85.1 px; ruler: the 36 x 80 in back-door leaf in the same frame (323 x 705 px): 2.830 mm/px across,
    2.882 down -> 0.258 m across x 0.245 m down (the two axes' own scales; 1 px of JPEG = 1.2%). Built [0.258, 0.245].
    Lead, not evidence: the 2-gang switch plate in 6910 (160 px; 4.56 in standard) gives 0.269 x 0.262 (+4-7%).
    Colour: the ground is scaled to the casing's white in the same frame (casing albedo 0.8 assumed): ground/casing linear
    0.865/0.785/0.686."""
    from scipy.ndimage import map_coordinates, gaussian_filter1d
    src = ROOT / "0-homealone/full/homealone-movie-screencaps.com-6910.jpg"
    out = ROOT / "spec/dressing/kitchen_wallpaper.png"
    XS, Y0, V, P, DROP, SHEAR = 1356, 480, 362, 186, 181, -7.0
    im = np.asarray(Image.open(src).convert("RGB"), float)
    def strip(y_top):   # rows y_top .. y_top + V of the strip, sheared so a repeat lands back on itself
        r, c = np.mgrid[0:V, 0:P].astype(float)
        yy = y_top + r; xx = XS + c + SHEAR * (yy - Y0) / V
        return np.dstack([map_coordinates(im[..., k], [yy, xx], order=1) for k in range(3)])
    tile = np.concatenate([strip(Y0), strip(Y0 + DROP)], axis=1)
    # even out the light (falloff and the glare left of the switch plate) from the GROUND only, so the motifs keep their contrast:
    # the background is the blurred luminance of ground pixels over the blurred ground mask (wrapped: the tile repeats)
    lum = tile.mean(2); ground_m = (lum > np.percentile(lum, 45)).astype(float)
    bg = gaussian_filter(lum * ground_m, 14, mode="nearest") / np.maximum(gaussian_filter(ground_m, 14, mode="nearest"), 1e-3)   # not wrapped: the strip's top and bottom are lit differently in the photo
    tile = tile / np.maximum(bg, 1)[..., None] * np.median(lum[ground_m > 0])
    for c0 in (0, P):   # then each column's ground tone row by row (70th percentile of a row: ground), so top and bottom meet
        L = tile[:, c0:c0 + P].mean(2); prof = gaussian_filter1d(np.percentile(L, 70, axis=1), 12, mode="nearest")
        tile[:, c0:c0 + P] *= (np.median(prof) / prof)[:, None, None]
    lin = np.where(tile / 255 <= 0.04045, tile / 255 / 12.92, ((tile / 255 + 0.055) / 1.055) ** 2.4)
    L = lin.mean(2); ground = np.median(lin[L > np.percentile(L, 60)], 0)
    target = 0.8 * np.array([0.865, 0.785, 0.686])                           # ground albedo vs the casing's white
    lin = np.clip(lin * (target / ground), 0, 1)
    srgb = np.where(lin <= 0.0031308, lin * 12.92, 1.055 * lin ** (1 / 2.4) - 0.055)
    pad = 24; big = np.pad(srgb, ((pad, pad), (pad, pad), (0, 0)), mode="wrap")    # resample with wrapped edges: no seam ringing
    sx, sy = 512 / srgb.shape[1], 512 / srgb.shape[0]
    big = Image.fromarray((big * 255 + 0.5).astype(np.uint8)).resize((round(big.shape[1] * sx), round(big.shape[0] * sy)), Image.LANCZOS)
    big.crop((round(pad * sx), round(pad * sy), round(pad * sx) + 512, round(pad * sy) + 512)).save(out)
    rep = [0.258, 0.245]
    out.with_suffix(".json").write_text(json.dumps({"source": f"film 6910 strip x {XS}-{XS + P}, rows {Y0}-{Y0 + DROP + V}, half-drop", "repeat_m": rep,
                                                     "ground_srgb": [round(float(v), 3) for v in np.median(srgb[L > np.percentile(L, 60)], 0)]}) + "\n")
    big = np.tile(np.asarray(Image.open(out)), (3, 3, 1)); Image.fromarray(big).save(ROOT / "sfm-work/kitchen_wallpaper_3x3.png")
    print(out, rep, "3x3 check: sfm-work/kitchen_wallpaper_3x3.png")


def living():
    """The living room's paper (Oct 16): cream ground, rose bouquets hung from ribbon swags and garlands in a half-drop lattice.
    Film 10636 (near frontal on the den-side wall; lamplight, the only frontal wall shot of the room; 5640/5650 look down steeply).
    Lattice by 2-D autocorrelation of the blurred strip x 545-800, rows 0-640 (sigma 4 px kills the 16-px JPEG grid that dominates
    the raw peaks): (420, +5) down and (210, -141) / (206, +142): a half-drop, columns 141.5 px apart, so a straight tile is two columns
    283 x 421 px. Built from ONE strip (x 560-702, rows 4-425, between the glazed leaf's edge at 547 and the lamp) and the same strip
    half a repeat lower (rows 214-635) beside it, sheared 5 px per repeat (the lattice's own lean), no patching.
    Metric size, rulers in the same frame and wall plane, never averaged:
      * knob ruler: the glazed leaf's top edge (row 40) to its knob centre (row 638) = 598 px = 80 - 36 in (standard leaf and knob
        height) -> 1.869 mm/px -> tile 0.529 x 0.787 m
      * width ruler: the leaf 181-547 px = half the den-living opening (1.508 m, overhead trace) less 2 cm jambs = 0.734 m -> 2.005 mm/px
        -> tile 0.567 x 0.844 m
      spread 7%. Built at the standard 21 in (0.533 m) American roll width, inside the bracket (sensible-defaults): one straight repeat
      per roll width; height 0.533 * 421 / 283 = 0.793 m.
    Disagreeing read (logged, DEVIATIONS): film 5640's front-wall French door, knob (row 367) to floor (645) = 278 px for 36 in, against
    the paper's 355 px vertical repeat there, gives 1.17 m (+48%); a 1.17 m repeat would be 0.79 m wide, wider than any roll.
    Colour: the ground set to the house's off-white trim (ASSUMED; the stile ratio's own chroma, slightly magenta, read lilac by day)."""
    from scipy.ndimage import map_coordinates, gaussian_filter1d
    src = ROOT / "0-homealone/full/homealone-movie-screencaps.com-10636.jpg"
    out = ROOT / "spec/dressing/living_wallpaper.png"
    XS, Y0, V, P, DROP, SHEAR = 560, 4, 421, 142, 210, 5.0   # row 0-3: the frame edge; x 556-559 the leaf reveal's shadow
    im = np.asarray(Image.open(src).convert("RGB"), float)
    def strip(y_top):
        r, c = np.mgrid[0:V, 0:P].astype(float)
        yy = y_top + r; xx = XS + c + SHEAR * (yy - Y0) / V
        return np.dstack([map_coordinates(im[..., k], [yy, xx], order=1) for k in range(3)])
    tile = np.concatenate([strip(Y0), strip(Y0 + DROP)], axis=1)
    # per CHANNEL from the ground only: the lamp below-right warms the lower right column (its glow is colour, not just level)
    lum = tile.mean(2); ground_m = (lum > np.percentile(lum, 45)).astype(float)
    for k in range(3):
        ch = tile[..., k]
        bg = gaussian_filter(ch * ground_m, 14, mode="nearest") / np.maximum(gaussian_filter(ground_m, 14, mode="nearest"), 1e-3)
        tile[..., k] = ch / np.maximum(bg, 1) * np.median(ch[ground_m > 0])
    for c0 in (0, P):   # each column's ground tone row by row, then column by column (the leaf's reveal shades the strip's left edge)
        for ax in (1, 0):
            L = tile[:, c0:c0 + P].mean(2); prof = gaussian_filter1d(np.percentile(L, 70, axis=ax), 12 if ax == 1 else 8, mode="nearest")
            tile[:, c0:c0 + P] *= ((np.median(prof) / prof)[:, None, None] if ax == 1 else (np.median(prof) / prof)[None, :, None])
    # the brass desk lamp's arm enters the right column's lower right corner (image x >= 676, rows >= 606 = tile rows 392+): those
    # pixels are the SAME lattice point one full repeat up (image rows 185+, the left column's tile rows 181+, 5 px lean), after the
    # light is flattened: the paper's own period, not a patch from elsewhere
    tile[392:V, P + 120:2 * P] = tile[181:181 + V - 392, 120 - 5:P - 5]
    lin = np.where(tile / 255 <= 0.04045, tile / 255 / 12.92, ((tile / 255 + 0.055) / 1.055) ** 2.4)
    L = lin.mean(2); ground = np.median(lin[L > np.percentile(L, 60)], 0)
    # the leaf stands back in the opening's reveal and reads DARKER than the paper (ground/stile 1.18-1.23 beside its knob edge,
    # rows 100-400, x 515-543 vs 552-600): no usable white in the paper's light. The stile gives the CHROMA only (lamp colour
    # cancelled); the ground's albedo is ASSUMED 0.72 (max channel; a white-cream paper), DEVIATIONS.
    def L_(c): c = c / 255; return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    leaf = L_(im[100:400, 515:543].reshape(-1, 3)); paper = L_(im[100:400, 552:600].reshape(-1, 3))
    pl = paper.mean(1); ratio = np.median(paper[pl > np.percentile(pl, 60)], 0) / np.median(leaf, 0)
    target = np.array([0.71, 0.67, 0.57])   # the house's off-white trim colour (sRGB 0.86/0.84/0.78): the stile ratio's chroma (1.245/1.18/1.228, slightly
                                            # magenta) read lilac under the day sky in the first render; the film's ground reads cream (5650, 10600)
    print("ground/stile linear ratio", ratio.round(3), "-> ground albedo", target.round(3))
    lin = np.clip(lin * (target / ground), 0, 1)
    srgb = np.where(lin <= 0.0031308, lin * 12.92, 1.055 * lin ** (1 / 2.4) - 0.055)
    pad = 24; big = np.pad(srgb, ((pad, pad), (pad, pad), (0, 0)), mode="wrap")
    W2, H2 = 512, round(512 * V / (2 * P))
    sx, sy = W2 / srgb.shape[1], H2 / srgb.shape[0]
    big = Image.fromarray((big * 255 + 0.5).astype(np.uint8)).resize((round(big.shape[1] * sx), round(big.shape[0] * sy)), Image.LANCZOS)
    big.crop((round(pad * sx), round(pad * sy), round(pad * sx) + W2, round(pad * sy) + H2)).save(out)
    k = 1.8690e-3, (0.734 / 366)
    print("knob ruler tile", [round(2 * P * k[0], 3), round(V * k[0], 3)], "width ruler tile", [round(2 * P * k[1], 3), round(V * k[1], 3)])
    rep = [0.533, round(0.533 * V / (2 * P), 3)]
    out.with_suffix(".json").write_text(json.dumps({"source": f"film 10636 strip x {XS}-{XS + P}, rows {Y0}-{Y0 + DROP + V}, half-drop", "repeat_m": rep,
                                                     "rulers": {"knob_80_36in": [0.531, 0.787], "leaf_half_opening": [0.569, 0.844]},
                                                     "ground_srgb": [round(float(v), 3) for v in np.median(srgb[L > np.percentile(L, 60)], 0)]}) + "\n")
    big = np.tile(np.asarray(Image.open(out)), (3, 3, 1)); Image.fromarray(big).save(ROOT / "sfm-work/living_wallpaper_3x3.png")
    print(out, rep, "3x3 check: sfm-work/living_wallpaper_3x3.png")


def buzz():
    """Buzz's room paper (Oct 18, changes/2026-10-18-buzz-bed.json; was film 530 on Marina's spacing, Buzz TRIAL 2). Film 2766 (daylight,
    frontal and sharp: the BB gun on the wall) shows the paper close: a white ground, lines every quarter period in the order RED,
    grey, TAN, grey (530's 'grey minors' at a distance), each line broken by a short gap every ~1.5 periods, the gaps staggered.
    Metric size, two rulers of different kinds, never averaged:
      * gun (built): the gun hanging level across the frame, butt plate (x 62) to muzzle (x 1845), Daisy lever BB gun ~0.90 m
        (Red Ryder 35.4 in; the family runs 35-37 in): the red lines fitted per line over three clean row bands and counted along
        the gun's rows, fractional periods at both ends -> spacing = L / periods.
      * chart (check): film 480, the growth chart on the closet door (same wall as the desk/lamp): its 5/4/2/1 ft ticks give the
        local px/m (least squares); the paper beside the door (left of the chart, x 0-190) gives the line pitch in px. The wall is
        assumed frontal (foreshortening can only make the paper read NARROWER: a lower bound). The door knob is printed against
        the chart (36 in standard, a lead).
    Tile: ONE period across (the median of every clean period below the sling, rows 700-1050, x 1150-1900, each resampled to W px
    between its red lines; the median over rows removes the gaps), divided by its own ground, ground albedo ASSUMED the house's
    off-white (0.71/0.67/0.57 linear); TILE_H periods tall with one gap per line at staggered heights (film 2766: gaps every
    ~275-410 px of ~226 px periods)."""
    from scipy.ndimage import map_coordinates, gaussian_filter1d, percentile_filter
    from scipy.signal import find_peaks
    F = lambda n: ROOT / f"0-homealone/full/homealone-movie-screencaps.com-{n}.jpg"
    im = np.asarray(Image.open(F(2766)).convert("RGB"), float)
    red = im[..., 0] - (im[..., 1] + im[..., 2]) / 2

    # ---- ruler 1: the gun
    GUN_L, GUN_RANGE = 0.90, (0.89, 0.94)
    BUTT, MUZZLE = (62, 528), (1845, 338)                 # butt plate's middle, muzzle face's middle (picks: spec/captures/picks/buzz3/)
    bands = {150: (130, 170, 600), 620: (600, 640, 0), 1000: (980, 1020, 0)}   # row: (r0, r1, first clean x: the poster above)
    pk = {r: [x for x in find_peaks(red[r0:r1].mean(0), height=25, distance=150)[0] if x >= x0] for r, (r0, r1, x0) in bands.items()}
    lines = []
    for x620 in pk[620]:
        pts = [(r, min(pk[r], key=lambda x: abs(x - x620))) for r in pk]
        pts = [(r, x) for r, x in pts if abs(x - x620) < 40]
        lines.append(np.polyfit([r for r, _ in pts], [x for _, x in pts], 1) if len(pts) > 1 else (0.0, x620))
    def frac(x, row):   # x in red-line periods along that row (linear extrapolation past the end lines)
        xs = np.array(sorted(np.polyval(l, row) for l in lines)); k = np.arange(len(xs))
        if x < xs[0]: return (x - xs[0]) / (xs[1] - xs[0])
        if x > xs[-1]: return k[-1] + (x - xs[-1]) / (xs[-1] - xs[-2])
        return float(np.interp(x, xs, k))
    periods = frac(MUZZLE[0], MUZZLE[1]) - frac(BUTT[0], BUTT[1])
    rep = GUN_L / periods
    print(f"film 2766 gun: {periods:.2f} red periods butt to muzzle -> spacing {rep:.4f} m at L {GUN_L} m (L {GUN_RANGE[0]}-{GUN_RANGE[1]}: "
          f"{GUN_RANGE[0] / periods:.4f}-{GUN_RANGE[1] / periods:.4f}); line pitch in px {np.ptp([np.polyval(l, 430) for l in lines]) / (len(lines) - 1):.1f}")

    # ---- ruler 2 (check): film 480's growth chart
    im2 = np.asarray(Image.open(F(480)).convert("RGB"), float)
    TICKS = {5: 76, 4: 240, 2: 558, 1: 712}               # chart tick rows (picks: spec/captures/picks/buzz3/chart-480.png)
    ft = np.array(list(TICKS)); rows = np.array(list(TICKS.values()), float)
    slope, icpt = np.polyfit(ft * 0.3048, rows, 1); ppm = -slope
    resid = rows - (slope * ft * 0.3048 + icpt)
    knob_h = (418 - icpt) / slope
    def ac_peak(x, lo, hi):
        x = x - x.mean(); a = np.correlate(x, x, "full")[len(x) - 1:]; a /= a[0]
        k = lo + int(np.argmax(a[lo:hi])); return k + 0.5 * (a[k - 1] - a[k + 1]) / (a[k - 1] - 2 * a[k] + a[k + 1])
    lum2 = im2.mean(2); red2 = im2[..., 0] - im2[..., 1]
    minor = np.median([ac_peak(lum2[r:r + 100, 0:190].mean(0) - gaussian_filter1d(lum2[r:r + 100, 0:190].mean(0), 6), 12, 22) for r in (0, 100, 200)])
    major = np.median([ac_peak(red2[r:r + 100, 0:190].mean(0) - gaussian_filter1d(red2[r:r + 100, 0:190].mean(0), 25), 50, 90) for r in (0, 100, 200)])
    chart = {"px_per_m": round(float(ppm), 1), "tick_resid_px": [round(float(v), 1) for v in resid], "knob_h_m": round(float(knob_h), 3),
             "minor_px": round(float(minor), 2), "major_px": round(float(major), 2),
             "spacing_from_minors_m": round(float(4 * minor / ppm), 4), "spacing_from_reds_m": round(float(major / ppm), 4)}
    print("film 480 chart check:", chart)

    # ---- the tile from 2766
    W, TILE_H, GAP = 128, 1.5, 0.035                      # px per period; tile height in periods; gap length in periods
    prof = []
    for r in range(700, 1050, 10):
        p = find_peaks(red[r:r + 10].mean(0), height=25, distance=150)[0]
        p = p[(p >= 1150) & (p <= 1900)]
        for a_, b_ in zip(p, p[1:]):
            xx = a_ + (np.arange(W) + 0.5) * (b_ - a_) / W - 0.5 * (b_ - a_) / W   # the red line at column 0
            prof.append(np.stack([map_coordinates(im[r:r + 10, :, k].mean(0)[None].repeat(3, 0), [np.ones(W), xx], order=1) for k in range(3)], 1))
    prof = np.median(np.array(prof), 0)
    lin = np.where(prof / 255 <= 0.04045, prof / 255 / 12.92, ((prof / 255 + 0.055) / 1.055) ** 2.4)
    # the ground per column (a sliding 80th percentile a quarter period wide, wrapped: lines are dark and narrow), smoothed: the
    # light's slope across the wall left the plain paper shaded within each period (bands in the first cut)
    g = np.stack([gaussian_filter1d(percentile_filter(lin[:, k], 80, size=W // 4, mode="wrap"), W / 16, mode="wrap") for k in range(3)], 1)
    ratio = lin / g
    lin = np.clip(ratio * np.array([0.71, 0.67, 0.57]), 0, 1)
    H = int(round(W * TILE_H)); tile = np.repeat(lin[None], H, 0)
    ground = np.array([0.71, 0.67, 0.57]); dark = ratio.mean(1) < 0.93
    for i, (c, at) in enumerate(((0.0, 0.10), (0.25, 0.60), (0.5, 0.35), (0.75, 0.85))):   # red, grey, tan, grey: one staggered gap each
        cols = [j for j in range(W) if dark[j] and min(abs(j / W - c), 1 - abs(j / W - c)) < 0.06]
        y0 = int(at * H); tile[y0:y0 + max(2, int(GAP * W)), cols] = ground
    srgb = np.where(tile <= 0.0031308, tile * 12.92, 1.055 * tile ** (1 / 2.4) - 0.055)
    out = ROOT / "spec/dressing/buzz_wallpaper.png"
    Image.fromarray((srgb * 255 + 0.5).astype(np.uint8)).resize((512, int(512 * TILE_H)), Image.LANCZOS).save(out)
    w_m = round(rep, 4)
    out.with_suffix(".json").write_text(json.dumps({
        "source": "film 2766 rows 700-1050, x 1150-1900: median of every clean period (red, grey, tan, grey lines), gaps staggered one per line per tile",
        "repeat_m": [w_m, round(w_m * TILE_H, 4)], "ruler": f"gun (film 2766, Daisy lever BB gun {GUN_L} m): {periods:.2f} periods butt to muzzle",
        "gun_range_m": [round(GUN_RANGE[0] / periods, 4), round(GUN_RANGE[1] / periods, 4)], "check_chart_480": chart,
        "line_to_ground_linear": {n: [round(float(v), 3) for v in ratio[int(c * W) + (1 if c == 0 else 0)]] for n, c in (("red", 0.0), ("grey", 0.25), ("tan", 0.5))},
        "previous": "0.0853 (Marina's desk wall at her growth chart; her paper, not the film's)"}, indent=1) + "\n")
    big = np.tile(np.asarray(Image.open(out)), (2, 8, 1)); Image.fromarray(big).save(ROOT / "sfm-work/buzz_wallpaper_tiled.png")
    print(out, [w_m, round(w_m * TILE_H, 4)], "check: sfm-work/buzz_wallpaper_tiled.png")


if "--buzz" in sys.argv:
    buzz(); sys.exit()
if "--kitchen" in sys.argv:
    kitchen(); sys.exit()
if "--living" in sys.argv:
    living(); sys.exit()
SRC = ROOT / "0-homealone/full/homealone-movie-screencaps.com-1170.jpg"
OUT = ROOT / "spec/dressing/wallpaper_film.png"
X0, Y0, V, HW = 1515, 60, 442, 370          # tile left column and top row, vertical repeat, horizontal repeat (px)
REPEAT_H_M = 0.533

im = np.asarray(Image.open(SRC).convert("RGB"), float)
tile = im[Y0:Y0 + V, X0:X0 + HW].copy()
# rows 60-502 lie above the brass switch plate (rows 505-605): no patching needed
lum = tile.mean(2, keepdims=True); flat = gaussian_filter(lum, (60, 60, 0))         # even out the film's light falloff
tile = tile / np.maximum(flat, 1) * lum.mean()
# the cut is one exact repeat both ways, so it wraps; soften the seams 6 px against JPEG and perspective residue
for ax in (0, 1):
    e = 6; t = np.moveaxis(tile, ax, 0); a = np.linspace(0, 1, e)[:, None, None] if ax == 0 else np.linspace(0, 1, e)[:, None, None]
    t[:e] = t[:e] * a + t[-e:][::-1][::-1] * (1 - a); tile = np.moveaxis(t, 0, ax)
m = tile.mean((0, 1)); g = tile.mean(2, keepdims=True)                              # film JPEG is muddy: lift contrast and colour
tile = (g + (tile - g) * 1.25 - m.mean()) * 1.2 + m.mean() * 1.08
Image.fromarray(np.clip(tile, 0, 255).astype(np.uint8)).resize((512, round(512 * V / tile.shape[1])), Image.LANCZOS).save(OUT)
rep = [round(REPEAT_H_M * tile.shape[1] / V, 3), REPEAT_H_M]
(OUT.with_suffix(".json")).write_text(json.dumps({"source": f"film 1170 x {X0}-{X0 + HW}, rows {Y0}-{Y0 + V}", "repeat_m": rep}) + "\n")
print(OUT, rep)
