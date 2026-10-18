#!/usr/bin/env python3
"""guest_room_measure: the upstairs room over the den (Oct 18 2026; changes/2026-10-18-guest-room.json), two rulers of different kinds.

1. Real-house plan (art/home_alone/references/dimensional-baseline/dimensioned-second-floor.png, Eric's visitor plan, 'OFFICE/UNKNOWN';
   its own scale: Buzz's room drawn between its inner faces = its label 14'11"): the room's front and rear setbacks from the main
   block's faces, its depth and length, the door into the rear bedroom. Picks are image px on gridded crops (EXIF-free PNG).
2. The old reference GLB, registered to our house by register_glb.py (similarity s 0.757 from 23 facade/stair features; no plan input):
   the over-den section's front and rear wall planes vs the main block's front plane, inside the upper storey's window band.

  uv run --with numpy python -I tools/house/guest_room_measure.py          # prints both, the spread, writes the pick crops
"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/house"))
FT = 0.3048
PLAN_IMG = ROOT / "art/home_alone/references/dimensional-baseline/dimensioned-second-floor.png"
# plan picks (px): y grows toward the FRONT (bottom of the drawing), x along the house (the office at the left)
P = {"buzz_inner_lo_x": 496, "buzz_inner_hi_x": 902.5,          # Buzz's room between its side walls' inner faces = 14'11"
     "office_front_inner_y": 1045, "office_front_outer_y": 1058.5, "main_front_inner_y": 1114, "main_front_outer_y": 1129,
     "office_rear_inner_y": 426, "main_rear_inner_y": 354,
     "office_end_inner_x": 160, "office_side_inner_x": 480,        # the end wall's and the Buzz-side wall's inner faces
     "door_rear_bedroom_y": (488, 555)}                          # the door into the rear bedroom, along the office's side wall


def plan():
    s = (P["buzz_inner_hi_x"] - P["buzz_inner_lo_x"]) / (14 * FT + 11 * 0.0254)   # px per m
    m = lambda px: px / s
    return {"px_per_m": round(s, 2),
            "front_setback_inner": round(m(P["main_front_inner_y"] - P["office_front_inner_y"]), 3),
            "front_setback_outer": round(m(P["main_front_outer_y"] - P["office_front_outer_y"]), 3),
            "rear_setback_inner": round(m(P["office_rear_inner_y"] - P["main_rear_inner_y"]), 3),
            "depth_inner": round(m(P["office_front_inner_y"] - P["office_rear_inner_y"]), 3),
            "length_inner": round(m(P["office_side_inner_x"] - P["office_end_inner_x"]), 3),
            "label_9ft11_x_22ft6": [round(9 * FT + 11 * 0.0254, 3), round(22 * FT + 6 * 0.0254, 3)],
            "door_centre_from_rear_inner": round(m(sum(P["door_rear_bedroom_y"]) / 2 - P["office_rear_inner_y"]), 3),
            "door_width": round(m(P["door_rear_bedroom_y"][1] - P["door_rear_bedroom_y"][0]), 3)}


def glb():
    import register_glb as R
    S, L = R.load_glb(); T = R.Tris(S, L)
    reg = json.loads((ROOT / "spec/glb_registration.json").read_text())["plan"]; s = reg["scale"]
    UP = (2.2, 3.0)                                   # upper-storey window band (pre y)
    def face(rng, band_z, sign):
        """area-dominant x-facing plane with outward normal sign, pre frame"""
        m = T.box(x=rng, y=UP, z=band_z) & (np.abs(T.n[:, 0]) > 0.95) & (np.sign(T.n[:, 0]) == sign)
        k = np.round(T.c[m, 0], 2); u, iv = np.unique(k, return_inverse=True)
        return float(u[np.argmax(np.bincount(iv, T.a[m]))])
    over = (18.6, 22.6)                               # pre z of the over-den section (spec z ~16.3-19.4)
    main = (14.0, 17.5)                               # pre z of Buzz's room
    f_main_out, f_main_in = face((9.5, 10.6), main, 1), face((9.5, 10.6), main, -1)
    f_over_out, f_over_in = face((7.0, 9.5), over, 1), face((7.0, 9.5), over, -1)
    r_over_in, r_over_out = face((-1.0, 0.0), over, 1), face((-1.0, 0.0), over, -1)
    return {"scale": round(s, 4), "pre": {"main_front_outer": f_main_out, "main_front_inner": f_main_in, "over_front_outer": f_over_out,
                                          "over_front_inner": f_over_in, "over_rear_inner": r_over_in, "over_rear_outer": r_over_out},
            "front_setback_outer": round(s * (f_main_out - f_over_out), 3), "front_setback_inner": round(s * (f_main_in - f_over_in), 3),
            "depth_inner": round(s * (f_over_in - r_over_in), 3)}


def crops():
    from PIL import Image, ImageDraw
    im = Image.open(PLAN_IMG).convert("RGB"); out = ROOT / "spec/captures/picks/guest"; out.mkdir(parents=True, exist_ok=True)
    for name, box in (("plan_front", (120, 960, 960, 1140)), ("plan_rear", (120, 250, 960, 460)), ("plan_doors", (360, 480, 820, 1080))):
        c = im.crop(box).resize(((box[2] - box[0]) * 2, (box[3] - box[1]) * 2)); d = ImageDraw.Draw(c)
        for k, v in P.items():
            for q in (v if isinstance(v, tuple) else (v,)):
                if k.endswith("_y") or k.startswith("door"):
                    if box[1] <= q <= box[3]: d.line([(0, (q - box[1]) * 2), (c.width, (q - box[1]) * 2)], fill=(255, 0, 255))
                elif box[0] <= q <= box[2]: d.line([((q - box[0]) * 2, 0), ((q - box[0]) * 2, c.height)], fill=(0, 160, 255))
        c.save(out / f"{name}.png")


if __name__ == "__main__":
    a, b = plan(), glb()
    print("real-house plan:", json.dumps(a))
    print("registered GLB :", json.dumps(b))
    print(f"front setback (outer faces): plan {a['front_setback_outer']:.2f} m, GLB {b['front_setback_outer']:.2f} m, spread "
          f"{abs(a['front_setback_outer'] - b['front_setback_outer']):.2f} m; depth (inner): plan {a['depth_inner']:.2f}, GLB {b['depth_inner']:.2f}")
    if "--no-crops" not in sys.argv:
        crops()
