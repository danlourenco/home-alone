"""Buzz's three windows from Marina's Part 2 tour: positions, sill, head and width -> measurements/windows/upstairs.json.

No input shares the Buzz SfM or its 80 in door scale:
- Heights: the Jordan growth chart's printed 3 ft and 5 ft marks on the desk wall (541.5 s) set the vertical scale. A
  standard 36 x 24 in bulletin board on the same wall agrees (762-782 px/m against the chart's 758), and the desk top
  reads 0.79 m (standard 0.74-0.76). Window head: frame 563.0 s, the front window's own height scaled from its stool,
  since the chart is not in that frame.
- Positions: fractions of each wall's length, from the 0:50 overhead (taken at window height, between the wall's
  floor and top edges). Check from a different view: the desk-wall window centre 0.61 m from the front corner in 543 s
  (bulletin-board scale) against the overhead's 0.60 m.
- Width: the desk-wall window's stool in 541.5 s (chart scale), less stool horns and casing. ASSUMED the same for the
  two front windows (no ruler in their wall plane); docs/DEVIATIONS.md.
Picks are image px (frame size 1920x1080 unless noted), read on gridded crops.
usage: uv run --with numpy python -I tools/house/buzz_windows.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FT = 0.3048

# 541.5 s: growth chart and the desk-wall window
CHART_5FT_Y, CHART_3FT_Y = 186, 648
STOOL_TOP_Y = 725            # stool front edge, top
STOOL_X = (50, 740)          # stool ends (horns included)
DESK_TOP_Y = 745             # sanity only
HORN, CASING = 0.025, 0.07   # stool horn past the casing, casing width (the grey-box's door casing)
# 563.0 s: front window nearest the door wall, at x ~1700
F563_FLOOR_Y = (990, 1020)   # floor line under the window (baseboard foot, by the bin): the weakest pick
F563_STOOL_Y, F563_HEAD_Y = 672, 125   # stool top, underside of the head casing
# 0:50 overhead (4x crop, crop px): front wall face, window centres and the wall ends at window height (0.6 of the face)
OV_FRONT_ENDS = (91, 1278)
OV_FRONT_CENTRES = ((295 + 580) / 2, (870 + 1185) / 2)   # curtain-pair centres
OV_DESK_ENDS = (125, 1030)   # shelves-wall end .. front-wall end
OV_DESK_CENTRE = (710 + 1055) / 2
EYE_543_DESK_CENTRE_M = 0.61  # held-out view: 543 s, corner to window centre at bulletin-board scale


def main():
    pxm = (CHART_3FT_Y - CHART_5FT_Y) / (2 * FT)
    sill = 3 * FT - (STOOL_TOP_Y - CHART_3FT_Y) / pxm
    desk = 3 * FT - (DESK_TOP_Y - CHART_3FT_Y) / pxm
    heads = [sill * (f - F563_HEAD_Y) / (f - F563_STOOL_Y) for f in F563_FLOOR_Y]
    head = (min(heads) + max(heads)) / 2
    width = (STOOL_X[1] - STOOL_X[0]) / pxm - 2 * (HORN + CASING)
    front = [(c - OV_FRONT_ENDS[0]) / (OV_FRONT_ENDS[1] - OV_FRONT_ENDS[0]) for c in OV_FRONT_CENTRES]
    desk_frac = (OV_DESK_CENTRE - OV_DESK_ENDS[0]) / (OV_DESK_ENDS[1] - OV_DESK_ENDS[0])
    print(f"chart scale {pxm:.0f} px/m; desk top {desk:.2f} m (standard 0.74-0.76)")
    print(f"sill {sill:.2f} m; head {head:.2f} m (spread {min(heads):.2f}-{max(heads):.2f}); opening width {width:.2f} m")
    print(f"front windows at {front[0]:.3f}, {front[1]:.3f} of the front wall from the hall wall; desk window at {desk_frac:.3f} of the desk wall from the shelves wall")
    common = {"width_m": round(width, 2), "sill_m": round(sill, 2), "head_m": round(head, 2)}
    src = "tools/house/buzz_windows.py (Marina Part 2: 0:50 overhead, 541.5 s chart, 563.0 s head)"
    out = {"note": "Window openings (clear, inside the casing). side = which edge of the room's bounding box in spec "
                   "coordinates; centre_frac = along that wall from its low-coordinate end; optional edge = polygon edge index (edge i runs from vertex i to i+1) for a wall off the bounding box. Written by " + src,
           "windows": [
               {"room": "buzz_room", "name": "front_hall_side", "side": "x_max", "centre_frac": round(front[0], 3), **common,
                "width_source": "assumed = desk-wall window"},
               {"room": "buzz_room", "name": "front_desk_side", "side": "x_max", "centre_frac": round(front[1], 3), **common,
                "width_source": "assumed = desk-wall window"},
               {"room": "buzz_room", "name": "desk_wall", "side": "z_max", "centre_frac": round(desk_frac, 3), **common,
                "width_source": "measured, 541.5 s stool at chart scale"},
           ]}
    p = ROOT / "measurements/windows/upstairs.json"
    p.parent.mkdir(parents=True, exist_ok=True)
    if p.exists():   # keep the other rooms' windows
        out["windows"] += [w for w in json.loads(p.read_text())["windows"] if w["room"] != "buzz_room"]
    p.write_text(json.dumps(out, indent=1) + "\n")
    print(f"-> {p.relative_to(ROOT)}")
    return sill, head, desk_frac


if __name__ == "__main__":
    sill, head, desk_frac = main()
    assert 0.70 < sill < 0.95 and 1.95 < head < 2.30, "heights outside any plausible double-hung window"
    built_desk_wall = 3.685   # spec buzz_room x span
    off = (1 - desk_frac) * built_desk_wall
    assert abs(off - EYE_543_DESK_CENTRE_M) < 0.10, f"overhead {off:.2f} m vs 543 s {EYE_543_DESK_CENTRE_M} m"
    print(f"check: desk window centre {off:.2f} m from the front corner (overhead) vs {EYE_543_DESK_CENTRE_M} m (543 s): ok")
