"""hero_assets: data for the blog post's scroll hero, film slider and time strip -> ~/.cache/home-alone-board/hero/hero.json
(data: URIs and base64 buffers; read by build_post.py). Film and Marina frames stay in the cache, never in the repo.

Sources, all in spec metres (x front +, y up with the ground floor at -3.026 and the upper floor at 0, z; right-handed, so they
go into three.js unchanged):
  points  Marina's kitchen clip, COLMAP sfm-work/rooms/kitchen/colmap/sparse/1, registered exactly as kitchen_walls.fixtures()
          does: wall/floor RANSAC planes, 36 in counter ruler, then per axis into the built wing (x = -5.192 + u ku, z = -0.915 + v kv)
  plan    spec/house_spec.ground.json + spec/house_spec.json room polygons
  walls   wall_graph.build(): the generator's wall boxes (openings already cut)
  skin    sfm-work/exterior/shell.json (exterior_shell.py: the film's house on our ground floor), lights/snow/icicles dropped
  camera  exterior_film_fit.fit("6399"): the solved film camera
  slider  perf renders (fr-NB9) cut to the film camera's view with sheet_tiles.film_crop, beside the film frames
  strip   the post's IMG 1-25 (docs/blog/show-and-tell.md Images table)
usage: uv run --with numpy --with scipy --with pillow python -I tools/blog/hero_assets.py
"""
import base64
import io
import json
import math
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/house"))
import exterior_film_fit as eff  # noqa: E402
import kitchen_walls as kw  # noqa: E402
import sheet_tiles  # noqa: E402
import wall_graph as wg  # noqa: E402

OUT = Path.home() / ".cache/home-alone-board/hero"
FILM = ROOT / "0-homealone/full/homealone-movie-screencaps.com-{}.jpg"
PERF = Path.home() / ".cache/home-alone-perf/runs/fr-NB9"
SKIP = ("Xmas", "Snow", "Icicles", "Shade", "Sheer", "Oculus")   # the oculus belongs to the garage, which the skin leaves out   # tiny or numerous parts: the lights alone are ~100k faces
PALETTE = {"EX_Brick": "#7b3a2c", "EX_Roof": "#35302e", "EX_Trim": "#efebe3", "EX_Gutter": "#e6e4df", "EX_Glass": "#2a3540",
           "EX_Stone": "#cfc7b8", "EX_Shutter": "#1d2420", "EX_Pot": "#3a3633"}   # tints by eye (film 6399), not sampled
ROOMS = {"foyer": "#8c2a2a", "den": "#4f6b47", "living_room": "#cfc2a2", "dining_room": "#b9a37c", "kitchen": "#d8cfa6",
         "hall_end": "#3f7d7a", "hall_corridor": "#3f7d7a", "hall_corridor_south": "#3f7d7a", "buzz_room": "#6d7f95",
         "kevin_jeff_room": "#8aa0b3", "parents_bedroom": "#c9a7a0"}   # the house's palette, approximate
GREY = "#c9cdd2"


def b64(a):
    return base64.b64encode(np.ascontiguousarray(a).tobytes()).decode()


def jpg(im, w, q=78):
    im = im.convert("RGB")
    if im.width > w:
        im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
    b = io.BytesIO(); im.save(b, "JPEG", quality=q, optimize=True, progressive=True)
    return "data:image/jpeg;base64," + base64.b64encode(b.getvalue()).decode()


def inside(poly, x, z):
    c = np.zeros(np.shape(x), bool)
    for (x1, z1), (x2, z2) in zip(poly, poly[1:] + poly[:1]):
        cr = (z1 > z) != (z2 > z)
        c ^= cr & (x < x1 + (z - z1) * (x2 - x1) / ((z2 - z1) or 1e-9))
    return c


def points(ground):
    # registration: the same steps as kitchen_walls.fixtures() (kept in step by hand; the numbers are its)
    f, cx, cy, cams, P, pl = kw._wing_frame()
    (ne, ce), (ns, cs), (nf, cf) = pl["end"], pl["seat"], pl["floor"]
    K = 0.914 / kw._counter_units(f, cx, cy, cams, pl)
    ku = 7.508 / (abs((pl["pantry"][1] - ce) @ ne) * K); kv = 8.553 / (abs((pl["stair"][1] - cs) @ ns) * K)
    U, V, H = (P - ce) @ ne * K, (P - cs) @ ns * K, (P - cf) @ nf * K
    X, Z = -5.192 + U * ku, -0.915 + V * kv
    rgb = np.array([l.split()[4:7] for l in open(kw.W_M / "points3D.txt") if not l.startswith("#")], np.uint8)
    assert len(rgb) == len(P)
    kit = next(s["polygon_xz"] for s in ground["spaces"] if s["name"] == "kitchen")
    ins = inside(kit, X, Z) & (H > -0.1) & (H < 2.6)
    print(f"points: {len(P)} in the clip, {ins.mean():.0%} inside the built kitchen and between floor and ceiling (kept)")
    assert ins.mean() > 0.5, "registration check: most of the clip's points must land in the kitchen"
    keep = np.flatnonzero(ins)
    np.random.default_rng(0).shuffle(keep)    # shuffled, so a phone can draw the first half
    xyz = np.stack([X, H + ground["floor_y_m"], Z], 1)[keep]
    q = np.round(xyz * 1000).astype(np.int16)
    return {"n": len(keep), "pos": b64(q), "rgb": b64(rgb[keep])}


def room_of(rooms, x, z):
    for r in rooms:
        if r["kind"] != "opening" and inside(r["poly"], np.array(x), np.array(z)):
            return r["name"]
    return None


def walls():
    geo, _, _ = wg.build(*wg.load())
    out = []
    for floor, g in geo.items():
        for w in g["walls"]:
            (x0, x1), (z0, z1), (y0, y1) = w["x"], w["z"], w["y"]
            mx, mz = (x0 + x1) / 2, (z0 + z1) / 2
            thin_x = (x1 - x0) < (z1 - z0)
            names = [room_of(g["rooms"], mx + s * 0.15, mz) if thin_x else room_of(g["rooms"], mx, mz + s * 0.15) for s in (-1, 1)]
            name = next((n for n in names if n in ROOMS), next((n for n in names if n), None))
            out.append({"f": floor[0], "b": [round(v, 3) for v in (x0, y0 + g["floor_y"], z0, x1, y1 + g["floor_y"], z1)],
                        "c": ROOMS.get(name, "#e3ddd0"), "r": name})
    print(f"walls: {len(out)} boxes")
    return out


def skin():
    S = json.loads((ROOT / "sfm-work/exterior/shell.json").read_text())
    parts = {}
    for name, p in S.items():
        if any(k in name for k in SKIP) or p["mat"] not in PALETTE:
            continue
        tris = [(f[0], f[i], f[i + 1]) for f in p["faces"] for i in range(1, len(f) - 1)]   # fan: the skin's faces are convex
        if tris:
            parts.setdefault(p["mat"], []).extend(tris)
    out = []
    for mat, tris in parts.items():
        q = np.round(np.array(tris, float).reshape(-1, 3) * 1000).astype(np.int16)
        out.append({"mat": mat, "c": PALETTE[mat], "pos": b64(q)})
    print("skin:", {m: len(t) for m, t in parts.items()}, "triangles")
    return out


def plan(ground, up):
    return [{"f": f, "name": s["name"], "y": sp["floor_y_m"], "h": s["ceiling_m"], "poly": s["polygon_xz"], "c": ROOMS.get(s["name"], GREY)}
            for f, sp in (("g", ground), ("u", up)) for s in sp["spaces"] if s["kind"] != "opening"]


def camera():
    cam, dy, err = eff.fit("6399")
    x, y, z, yaw, pitch, roll, f = cam
    F, R, U = eff.look(yaw, pitch, roll)
    vfov = math.degrees(2 * math.atan(eff.H_ / 2 / f))
    print(f"film 6399 camera: ({x:.2f}, {y:.2f}, {z:.2f}), vfov {vfov:.2f} deg, fit {err:.1f} px")
    return {"pos": [x, y, z], "fwd": F.tolist(), "up": U.tolist(), "vfov": vfov, "aspect": eff.W_ / eff.H_, "fit_px": round(err, 1)}, vfov


# camera-matched renders (Oct 21): a tour of the newest build at the solved film cameras (exterior_film_fit.py prints the poses; PerfProbe
# takes roll and vfov, so each shot is the film's framing once its centre 1058 rows are kept). Until they exist, the older crops stand in.
MATCHED = {"day": Path.home() / ".cache/home-alone-perf/runs/hero-6399-day/front6399-day.png",
           "night": Path.home() / ".cache/home-alone-perf/runs/hero-5545-night/front5545-night.png"}


def matched(key):
    p = MATCHED[key]
    if not p.exists():
        return None
    im = Image.open(p).convert("RGB"); assert im.size == (1920, 1080), (p, im.size)
    return im.crop((0, 11, 1920, 1069))   # the film's 1058 rows (same focal in px)


def slider(vfov):
    film_aspect = 1920 / 1058
    W, H = 1400, round(1400 / film_aspect)
    day, night = matched("day"), matched("night")
    print("slider: day", "camera-matched render" if day else "PLACEHOLDER (fr-NB9 crop)", "| night", "camera-matched render" if night else "PLACEHOLDER (11908 view)")
    day_note = "Our render from film 6399's solved camera (position, lens and tilt), the newest build, overcast like the film."
    night_note = "Our render from film 5545's solved camera, the newest build at night."
    if day is None:
        day = sheet_tiles.film_crop(Image.open(PERF / "front6399-day-A1.png"), vfov, film_aspect)
        day_note = "Our render from film 6399's solved camera, cut to the film lens's field of view."
    if night is None:
        night = sheet_tiles.film_crop(Image.open(ROOT / "spec/captures/views/front-drive/batch-after/night_f11908.png"), 60.0, film_aspect)
        night_note = "Night: our render from film 11908's straight-on view beside film 5545, the night reference. Close, not the same camera."
    film = lambda n: jpg(Image.open(str(FILM).format(n)).resize((W, H)), W)
    return [{"key": "day", "label": "Day: film 6399", "ours": jpg(day.resize((W, H)), W), "film": film(6399), "note": day_note},
            {"key": "night", "label": "Night: film 5545", "ours": jpg(night.resize((W, H)), W), "film": film(5545), "note": night_note}]


def hero_ours(vfov):
    """the hero's middle stage: our render at film 6399's camera (the newest build), between the model and the film still"""
    im = matched("day")
    print("hero render:", "camera-matched" if im else "PLACEHOLDER (fr-NB9 crop, sunny)")
    return jpg(im if im else sheet_tiles.film_crop(Image.open(PERF / "front6399-day-A1.png"), vfov, 1920 / 1058), 1600, 80)


def strip():
    md = (ROOT / "docs/blog/show-and-tell.md").read_text().partition("\n## Images")[2]
    rows = []
    for m in re.finditer(r"^\| IMG (\d+) \| (\S+) \| [^|]+ \| ([^|]+) \|", md, re.M):
        n = int(m.group(1))
        if n > 25:
            continue
        p, cap = m.group(2), m.group(3).strip()
        d = re.match(r"(\d{4})-(\d\d)-(\d\d)", Path(p).name)
        when = "By Sep 11" if n <= 4 else "September" if n == 5 else f"Oct {int(d.group(3))}"
        rows.append((0 if n <= 4 else 1 if n == 5 else int(d.group(3)) + 10, n, when, cap, p))
    rows.sort()
    out = []
    for _, n, when, cap, p in rows:
        im = Image.open(p)
        im = im.crop((0, 0, im.width, min(im.height, round(im.width * 0.75))))   # tall sheets: their top
        out.append({"n": n, "when": when, "cap": re.sub(r"\s*\((by )?(Sep|Oct|September)[^)]*\)$", "", cap), "src": jpg(im, 560, 72)})
    print(f"strip: {len(out)} images")
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    ground = json.loads((ROOT / "spec/house_spec.ground.json").read_text())
    up = json.loads((ROOT / "spec/house_spec.json").read_text())
    cam, vfov = camera()
    data = {"points": points(ground), "plan": plan(ground, up), "walls": walls(), "skin": skin(), "camera": cam,
            "film": jpg(Image.open(str(FILM).format(6399)), 1600, 80), "ours": hero_ours(vfov), "slider": slider(vfov), "strip": strip()}
    p = OUT / "hero.json"; p.write_text(json.dumps(data, separators=(",", ":")))
    print(f"-> {p} ({p.stat().st_size / 1e6:.2f} MB)")


if __name__ == "__main__":
    assert inside([[0, 0], [1, 0], [1, 1], [0, 1]], np.array([0.5, 1.5]), np.array([0.5, 0.5])).tolist() == [True, False]
    main()
