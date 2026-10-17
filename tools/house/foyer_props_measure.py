"""foyer_props_measure: every film reading behind spec/dressing/foyer_props.json, re-runnable (Oct 16, foyer finish).

Cameras (level, principal point at the frame centre, solved from flight 1's nosings so the stair wall is well pinned):
  film-1616fc  foyer_cameras.py's 1616 solve (spec/captures/views/views-foyer-film-after.json: pos 12.308 / 1.052 m / 9.403,
               vfov 26.64), written here as a refcam camera; check: flight-1 nosings 2 and 7 re-project to 2 cm
  film-3888fc  foyer_cameras.py's 3888 solve (measurements/cameras/film-3888fc.json), used only for the door check
  film-2677    refcam's solve (measurements/cameras/film-2677.json, rms 7.2 px)
Each reading is a pixel (full 1920 x 1058 frame, read on refcam grids, +-3 px) whose ray meets the plane the piece stands on.
Along the north wall the 1616 view is grazing (2 px = 3 cm along the wall, and the yaw is uncertain), so positions ALONG that
wall stay Marina's (312 s); only heights are read there, on the plane x = Marina's centre.

  uv run --with numpy python -I tools/house/foyer_props_measure.py
"""
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import refcam as rc   # noqa: E402

CAM = rc.CAMS / "film-1616fc.json"
if not CAM.exists():   # foyer_cameras.py 1616 solution as a refcam camera (Unity pos/look-at -> spec yaw)
    dx, dz = 11.309 - 12.308, -(-9.437 + 9.403)
    CAM.write_text(json.dumps({"cx": 960.0, "cy": 529.0, "yaw": math.atan2(-dz, -dx), "pos": [12.308, -1.974, 9.403],
                               "f": 529 / math.tan(math.radians(26.64 / 2)), "name": "film-1616fc",
                               "frame": "0-homealone/full/homealone-movie-screencaps.com-1616.jpg", "size": [1920, 1058],
                               "points": [], "note": "foyer_cameras.py 1616 (level, nosings), not re-solved"}, indent=1))

R = [  # (camera, u, v, plane, what)
    ("film-1616fc", 308, 778, "z=11.41", "CHECK flight-1 nosing 2 (spec x 6.23, h 0.356)"),
    ("film-1616fc", 447, 473, "z=11.41", "CHECK flight-1 nosing 7 (spec x 4.755, h 1.246)"),
    ("film-1616fc", 1500, 618, "x=5.67", "console top, front edge at the centre"),
    ("film-1616fc", 1520, 618, "z=8.138", "console top along the front edge (front end)"),
    ("film-1616fc", 1440, 618, "z=8.138", "console top along the front edge (rear end)"),
    ("film-1616fc", 1500, 752, "x=6.51", "front chair seat top"),
    ("film-1616fc", 1380, 700, "x=4.82", "rear chair seat top"),
    ("film-1616fc", 1630, 580, "x=6.51", "front chair back top"),
    ("film-1616fc", 1560, 505, "x=5.67", "mirror frame bottom"),
    ("film-1616fc", 1560, 130, "x=5.67", "mirror frame, highest clear read (crest above, dark)"),
    ("film-1616fc", 1206, 355, "x=3.01", "picture under the landing, outer top-left"),
    ("film-1616fc", 1330, 513, "x=3.01", "picture under the landing, outer bottom-right"),
    ("film-1616fc", 1228, 375, "x=3.01", "picture under the landing, image top-left"),
    ("film-1616fc", 1308, 495, "x=3.01", "picture under the landing, image bottom-right"),
    ("film-1616fc", 1065, 980, "h=0.005", "runner near fringe, left"),
    ("film-1616fc", 1400, 980, "h=0.005", "runner near fringe, right"),
    ("film-1616fc", 1225, 800, "h=0.005", "runner far end"),
    ("film-1616fc", 1060, 1012, "h=0.005", "front rug far fringe"),
    ("film-1616fc", 380, 1050, "h=0.005", "front rug, left end"),
    ("film-1616fc", 1440, 1050, "h=0.005", "front rug, right end"),
    ("film-2677", 400, 752, "z=11.41", "CHECK flight-1 nosing 2 on 2677 (x 6.23, h 0.356)"),
    ("film-2677", 1450, 215, "x=1.58", "CHECK rear door top (80 in = 2.032 above its bottom)"), ("film-2677", 1450, 738, "x=1.58", "CHECK rear door bottom"),
    ("film-3888fc", 1490, 275, "x=1.58", "CHECK rear door top on 3888"), ("film-3888fc", 1490, 821, "x=1.58", "CHECK rear door bottom on 3888"),
    ("film-2677", 370, 50, "z=11.43", "gallery 1 (dark) top-left"), ("film-2677", 440, 195, "z=11.43", "gallery 1 bottom-right"),
    ("film-2677", 463, 20, "z=11.43", "gallery 2 (gilt) top-left"), ("film-2677", 510, 150, "z=11.43", "gallery 2 bottom-right"),
    ("film-1616fc", 285, 225, "z=11.43", "gallery 1 on 1616, top-left"), ("film-1616fc", 340, 345, "z=11.43", "gallery 1 on 1616, bottom-right"),
    ("film-1616fc", 335, 185, "z=11.43", "gallery 2 on 1616, top-left"), ("film-1616fc", 360, 295, "z=11.43", "gallery 2 on 1616, bottom-right"),
    ("film-1616fc", 290, 150, "z=11.43", "gallery 3 top-left"), ("film-1616fc", 315, 230, "z=11.43", "gallery 3 bottom-right"),
    ("film-1616fc", 290, 40, "z=11.43", "gallery 4 top-left"), ("film-1616fc", 345, 140, "z=11.43", "gallery 4 bottom-right"),
    ("film-1616fc", 380, 80, "z=11.43", "gallery 5 top-left"), ("film-1616fc", 400, 230, "z=11.43", "gallery 5 bottom-right"),
    ("film-1616fc", 410, 70, "z=11.43", "gallery 6 top-left"), ("film-1616fc", 440, 170, "z=11.43", "gallery 6 bottom-right"),
    ("film-1616fc", 440, 50, "z=11.43", "gallery 7 top-left"), ("film-1616fc", 470, 130, "z=11.43", "gallery 7 bottom-right"),
    ("film-1616fc", 480, 40, "z=11.43", "gallery 8 top-left"), ("film-1616fc", 500, 100, "z=11.43", "gallery 8 bottom-right"),
]

cams = {}
for cam, u, v, plane, what in R:
    c = cams.setdefault(cam, rc.load_cam(cam))
    o, d = rc.ray(c, u, v); ax, val = plane.split("="); val = float(val)
    i = {"x": 0, "z": 2, "h": 1}[ax]; val = rc.G + val if ax == "h" else val
    P = o + (val - o[i]) / d[i] * d
    print(f"{cam:12s} ({u:4d},{v:4d}) {plane:8s} -> x {P[0]:6.3f} z {P[2]:6.3f} h {P[1] - rc.G:5.3f}   {what}")
