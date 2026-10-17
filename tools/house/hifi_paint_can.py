"""hifi_paint_can: the two US 1-gallon paint cans of the paint-can trap (docs/paint-can-trap.md), Blender headless.

  PaintCan.glb      Marv's can (film 10706/10708): silver can, white-painted lid, red paint over the top rim running down the side in
                    drips, a blue label panel beside one ear
  PaintCanSatin.glb Harry's can (film 10700/10716-10722): cream-painted can, a wide blue "SATIN" label (no lettering modelled),
                    cream drips running down over the label's front

Shared shape (user walk note Oct 16: "have a bottom"): turned body closed at both ends with rolled chime rims at the bottom and top, the
lid sunk inside the top rim with its groove, two ear lugs and the wire bail. 6.5 in x 7.5 in (0.165 x 0.19 m), the standard gallon
can; rims, lid, bail, label extents and drip layout are authored to the frames above (no frame measures them). Colours are set in
Unity from spec/dressing/traps.json (sampled from the film); materials here are placeholders named PC_Metal, PC_Lid, PC_Label,
PC_Paint, PC_Wire. Origin = the bail's apex (where the rope is tied).

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P tools/house/hifi_paint_can.py
  -> unity/HomeAlone/Assets/Models/Foyer/PaintCan.glb, PaintCanSatin.glb
"""
import math
import sys
from pathlib import Path

import bpy

ROOT = Path(__file__).resolve().parents[2]
OUTDIR = ROOT / "unity/HomeAlone/Assets/Models/Foyer"
sys.path.insert(0, str(Path(__file__).resolve().parent))
from hifi_lib import Part, material   # noqa: E402

H, R, RIM = 0.19, 0.0812, 0.0830     # height, wall radius, rolled rim (chime) radius
BAIL_RISE = 0.08                      # bail apex above the can's top (spec/dressing/traps.json bail_rise_m)
Y0 = -(H + BAIL_RISE)                 # the origin sits at the apex
N = 48


def shell(part, prof, a0, a1, n):
    """A closed profile [(r, y above Y0)] (counter-clockwise: up the outside) turned about the can's axis from angle a0 to a1 (deg);
    a part-turn gets flat end caps."""
    full = abs(a1 - a0) >= 360
    k_n = n if full else max(2, int(n * abs(a1 - a0) / 360))
    ang = [math.radians(a0 + (a1 - a0) * k / k_n) for k in range(k_n + (0 if full else 1))]
    P = lambda r, y, t: (r * math.cos(t), Y0 + y, r * math.sin(t))
    rings = [[P(r, y, t) for t in ang] for r, y in prof]
    m = len(ang)
    for i in range(len(prof)):
        a, b = rings[i], rings[(i + 1) % len(prof)]
        for k in range(m if full else m - 1):
            k2 = (k + 1) % m
            part.quad(a[k], b[k], b[k2], a[k2])
    if not full:
        for t, s in ((ang[0], -1), (ang[-1], 1)):
            part.face([P(r, y, t) for r, y in prof], (-s * math.sin(t), 0, s * math.cos(t)))


def can(out, label_span, label_y, drips, rim_paint):
    body, lid, label, paint, wire = (Part("CanBody", "PC_Metal"), Part("CanLid", "PC_Lid"), Part("CanLabel", "PC_Label"),
                                     Part("CanPaint", "PC_Paint"), Part("CanBail", "PC_Wire"))
    body.lathe(0, 0, Y0, [(0.0, 0.0800), (0.002, RIM), (0.008, RIM), (0.010, R), (0.178, R), (0.181, RIM), (0.189, RIM),
                          (0.190, 0.0800), (0.190, 0.0765), (0.184, 0.0760)], n=N)
    lid.lathe(0, 0, Y0 + 0.183, [(0.0, 0.0700), (0.0035, 0.0700)], n=N)
    # label: 0.6 mm paper on the wall
    lo, hi = label_y
    shell(label, [(R + 0.0006, lo), (R + 0.0006, hi), (R - 0.0004, hi), (R - 0.0004, lo)], *label_span, N)
    # paint: a skin over the top rim (out past the chime, over its top, into the groove), then drips down the side; each drip a strip
    # 1.4 mm proud of the wall (over the label) ending in a rounder bead
    if rim_paint:
        shell(paint, [(RIM + 0.0012, 0.176), (RIM + 0.0012, 0.1912), (0.0745, 0.1912), (0.0745, 0.1885), (RIM - 0.0012, 0.1885),
                      (R - 0.0004, 0.176)], 0, 360, N)
    for deg, length, width in drips:
        half = math.degrees(width / 2 / R); y1 = 0.177; y0 = y1 - length
        shell(paint, [(R + 0.0016, y0), (R + 0.0016, y1), (R - 0.0004, y1), (R - 0.0004, y0)], deg - half, deg + half, N)
        hb = half * 1.45
        shell(paint, [(R + 0.0022, y0 - 0.004), (R + 0.0022, y0 + 0.007), (R - 0.0004, y0 + 0.007), (R - 0.0004, y0 - 0.004)], deg - hb, deg + hb, N)
    # ear lugs at x = +/-R, 0.165 up; the bail's ends go through them
    ear_y = Y0 + 0.165
    for s in (-1, 1):
        x0, x1 = sorted((s * (R - 0.001), s * (R + 0.004)))
        wire.box(x0, x1, ear_y - 0.012, ear_y + 0.012, -0.008, 0.008)
    ax, ay = R + 0.006, -ear_y
    path = [(-ax * math.cos(math.pi * k / 24), ear_y + ay * math.sin(math.pi * k / 24), 0.0) for k in range(25)]
    prof = [(0.00125 * math.cos(2 * math.pi * k / 8), 0.00125 * math.sin(2 * math.pi * k / 8)) for k in range(8)]
    wire.sweep(path, prof)
    for s, p in ((-1, path[0]), (1, path[-1])):
        wire.sweep([(p[0], p[1] + 0.0001, p[2]), (s * (R - 0.0005), p[1], p[2])], prof)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    mats = {k: material(k, c, 0.5) for k, c in (("PC_Metal", (0.75, 0.75, 0.73)), ("PC_Lid", (0.85, 0.85, 0.85)),
            ("PC_Label", (0.3, 0.4, 0.7)), ("PC_Paint", (0.6, 0.1, 0.1)), ("PC_Wire", (0.45, 0.45, 0.45)))}
    coll = bpy.context.scene.collection
    root = bpy.data.objects.new(out.stem, None); coll.objects.link(root)
    for p in (body, lid, label, paint, wire):
        if p.f:
            p.build(coll, mats).parent = root
    bpy.ops.export_scene.gltf(filepath=str(out), export_format="GLB", export_yup=True, export_apply=True)
    print("wrote", out)


OUTDIR.mkdir(parents=True, exist_ok=True)
# Marv's (10708): red over the whole rim, drips all round of 3-15 cm (the longest past the middle), a blue panel ~110 deg wide by one ear
can(OUTDIR / "PaintCan.glb", (8, 118), (0.030, 0.160),
    [(150, 0.14, 0.012), (172, 0.09, 0.009), (200, 0.15, 0.014), (228, 0.06, 0.008), (255, 0.11, 0.011), (290, 0.04, 0.007),
     (318, 0.13, 0.012), (345, 0.08, 0.009), (40, 0.05, 0.008), (75, 0.10, 0.010)], rim_paint=True)
# Harry's (10700, 10722): the label covers ~3/4 of the can; four long cream runs down its front (10722), cream rim
can(OUTDIR / "PaintCanSatin.glb", (-40, 220), (0.025, 0.165),
    [(70, 0.15, 0.013), (88, 0.11, 0.010), (104, 0.16, 0.014), (125, 0.07, 0.009), (250, 0.05, 0.008)], rim_paint=True)
