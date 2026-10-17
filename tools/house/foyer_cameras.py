"""The back of the foyer measured through solved FILM cameras (tasks/wall-grid-plan.md phase 4; Oct 15).

Each film frame's camera is solved from flight 1 alone (its position is measured: Marina's rise, going and foot), so the
contested back wall is a prediction, not an input:
  - level camera (the frames' verticals are vertical: pilaster and arch jamb edges, checked on 2677), principal point at
    the centre; unknowns: yaw, position, focal, and the carpet nosing's drop below the tread top;
  - points: each tread's wall-side nosing end (spec z 11.41, against the skirt); lines: the carpet nosing read at one u.
Then a pixel on the back wall is a ray meeting the plane x = 2.986 (the landing front), and a pixel on the rear door a ray
meeting the door's plane. Readings are full-resolution pixels (1920 x 1058), +-4 px, from gridded crops.

Held-out checks (not used by the solve): the open-side nosing ends land on the balusters (overlay); the rear door's
80 in height and Marina's overhead position for it; the camera height from the rear door alone (foyer_film.py, 10673-style).
usage: uv run --with numpy --with scipy --with pillow python -I tools/house/foyer_cameras.py [--overlay] [--views]
"""
import json
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import brentq, least_squares

ROOT = Path(__file__).resolve().parents[2]
CX, CY = 960, 529
G = -3.026          # ground floor in spec y (upper floor 0)
X_BACK = 2.986      # the back wall's foyer face = the landing's front edge
Z_WALL = 11.41      # flight 1's wall-side nosing ends (south wall 11.43, skirt ~2 cm)
FRAMES = {   # wall-side nosing ends {step: (u, v)}; carpet nosings {step: v at u}; step 13 = the landing nosing
    "2677": dict(left={2: (400, 752), 3: (462, 663), 4: (520, 580), 5: (570, 506), 6: (620, 438), 7: (660, 378), 8: (700, 320),
                       9: (735, 270), 10: (768, 222), 11: (797, 180), 12: (826, 137), 13: (851, 98)},
                 red={2: 767, 3: 666, 4: 572, 5: 496, 6: 424, 7: 360, 8: 300, 9: 251, 10: 206, 11: 164, 12: 124}, u=950),
    "3888": dict(left={2: (410, 838), 3: (475, 744), 4: (535, 660), 5: (588, 583), 6: (640, 512), 11: (835, 245), 12: (850, 205), 13: (878, 162)},
                 red={2: 850, 3: 748, 4: 653, 5: 572, 6: 501, 7: 432, 8: 375, 9: 322, 10: 270, 11: 230, 12: 190}, u=950),
    "1616": dict(left={2: (308, 778), 3: (338, 708), 4: (373, 642), 5: (400, 583), 6: (425, 526), 7: (447, 473)},
                 red={2: 777, 3: 700, 4: 632, 5: 571, 6: 513, 7: 461, 8: 412, 9: 372, 10: 331, 11: 291, 12: 255}, u=650),
}
# On the back wall (u, v): arch inner jambs (at mid height), crown, springline, outer casing, the wallpaper's top edge,
# the wainscot top; the rear door through the arch: left/right edges (leaf + casing), top and bottom.
BACK = {"2677": dict(left=(1283, 500), right=(1604, 500), casing=(1629, 500), crown=(1440, 152), spring=(1604, 192), soffit=(1600, 123),
                     wainscot=(1750, 557), door_l=(1321, 500), door_r=(1567, 500), door_t=(1450, 215), door_b=(1450, 738)),
        "3888": dict(left=(1322, 500), right=(1658, 500), crown=(1470, 214), spring=(1658, 250), soffit=(1600, 181),
                     wainscot=(1750, 625), door_l=(1362, 500), door_r=(1617, 500), door_t=(1490, 275), door_b=(1490, 821)),
        # 1616: the picture wall face-on (foyer_film.FRAMES): arch casing outer, the corner, its wallpaper top
        "1616": dict(casing=(1162, 450), corner=(1372, 450), soffit=(1300, 272), wainscot=(1300, 598))}
BUILD_DOOR = (8.967, 9.887)   # the rear door in the spec (Marina 312 s / overhead), spec z


def stair():
    S = json.loads((ROOT / "spec/house_spec.json").read_text())
    steps = sorted([b for b in S["stair"]["boxes"] if b["name"].startswith("flight1_step")], key=lambda b: b["name"])
    land = next(b for b in S["stair"]["boxes"] if b["name"] == "landing")
    return [(b["x"][1], b["y"][1]) for b in steps] + [(land["x"][1], land["y"][1])], S


def R(yaw):   # spec world (x, y up, z) -> camera (right, down, forward); yaw 0 looks along -x
    c, s = np.cos(yaw), np.sin(yaw)
    return np.array([[s, 0, -c], [0, -1, 0], [-c, 0, -s]])


def proj(p, X):
    Xc = (np.atleast_2d(X) - p[1:4]) @ R(p[0]).T
    return np.c_[CX + p[4] * Xc[:, 0] / Xc[:, 2], CY + p[4] * Xc[:, 1] / Xc[:, 2]]


def ray_hit(p, uv, axis, c):
    d = R(p[0]).T @ np.array([(uv[0] - CX) / p[4], (uv[1] - CY) / p[4], 1.0]); t = (c - p[1 + axis]) / d[axis]
    return p[1:4] + t * d


def solve(fr, nose):
    L, RED, U = FRAMES[fr]["left"], FRAMES[fr]["red"], FRAMES[fr]["u"]

    def res(p):
        r = list((proj(p, np.array([[*nose[k - 1], Z_WALL] for k in L])) - np.array(list(L.values()))).ravel())
        for k, v in RED.items():
            a, b = proj(p, np.array([[nose[k - 1][0], nose[k - 1][1] - p[5], z] for z in (10.3, 11.4)]))
            r.append(a[1] + (U - a[0]) / (b[0] - a[0]) * (b[1] - a[1]) - v)
        return np.array(r)
    best = min((least_squares(res, np.r_[y0, 9.5, -2.2, 9.8, f0, 0.02], x_scale=np.r_[0.05, 1, 1, 1, 300, 0.01])
                for f0 in (900, 1300, 1800, 2500, 3200) for y0 in (-0.3, -0.1, 0.1)), key=lambda s: s.cost)
    return best.x, float(np.sqrt(np.mean(best.fun ** 2)))


def measure(fr, p):
    b = BACK[fr]; q = {k: ray_hit(p, v, 0, X_BACK) for k, v in b.items() if not k.startswith("door")}
    out = {k: round(float(q[k][1] - G), 3) for k in ("crown", "spring", "soffit", "wainscot") if k in q}
    out.update({f"{k}_z": round(float(q[k][2]), 3) for k in ("left", "right", "casing", "corner") if k in q})
    if "left" in q:
        out["clear_width"] = round(float(q["left"][2] - q["right"][2]), 3)
    if "door_t" in b:   # the rear door's plane from its own 80 in height; then its span there and at the built rear wall
        h = lambda x: ray_hit(p, b["door_t"], 0, x)[1] - ray_hit(p, b["door_b"], 0, x)[1] - 2.032
        out["door_face_x_from_80in"] = round(float(brentq(h, -3, 2.9)), 3)
        l, r = ray_hit(p, b["door_l"], 0, 1.581), ray_hit(p, b["door_r"], 0, 1.581)
        out["door_z_at_rear_wall"] = [round(float(r[2]), 3), round(float(l[2]), 3)]
        out["door_height_at_rear_wall"] = round(float(ray_hit(p, b["door_t"], 0, 1.581)[1] - ray_hit(p, b["door_b"], 0, 1.581)[1]), 3)
    return out


def main():
    nose, S = stair()
    cams, rows = {}, {}
    for fr in FRAMES:
        p, rms = solve(fr, nose); cams[fr] = p
        print(f"{fr}: camera {p[1]:.2f}, height {p[2] - G:.2f} m, z {p[3]:.2f}; yaw {np.degrees(p[0]):.1f} deg; f {p[4]:.0f} px "
              f"(vfov {np.degrees(2 * np.arctan(CY / p[4])):.1f}); fit rms {rms:.1f} px")
        rows[fr] = measure(fr, p); print("   ", rows[fr])
    a, b = rows["2677"], rows["3888"]
    print(f"\nArch (two cameras): clear z {a['right_z']:.2f}/{b['right_z']:.2f} - {a['left_z']:.2f}/{b['left_z']:.2f}, width "
          f"{a['clear_width']:.2f}/{b['clear_width']:.2f} m; crown {a['crown']:.3f}/{b['crown']:.3f}, springline "
          f"{a['spring']:.3f}/{b['spring']:.3f}; wallpaper top {a['soffit']:.3f}/{b['soffit']:.3f}")
    for fr in ("2677", "3888"):
        r = rows[fr]
        print(f"Rear door ({fr}): at the built rear wall z {r['door_z_at_rear_wall']} (build {list(BUILD_DOOR)}), "
              f"{r['door_height_at_rear_wall']:.2f} m tall (80 in = 2.03); its own 80 in puts its face at x {r['door_face_x_from_80in']:.2f} (build 1.58)")
    c = rows["1616"]
    print(f"Picture wall (1616): arch casing z {c['casing_z']:.2f} to corner z {c['corner_z']:.2f} = {c['casing_z'] - c['corner_z']:.2f} m "
          f"(build: north wall 7.778, so {c['casing_z'] - 7.778:.2f} m); 1616's casing sits {(c['casing_z'] - a['casing_z']) * 100:+.0f} cm from 2677's")
    # the solves agree with each other and with the doors they never saw
    assert all(2100 < cams[f][4] < 2400 for f in cams), "one lens for all three shots"
    assert abs(a["crown"] - b["crown"]) < 0.03 and abs(a["clear_width"] - b["clear_width"]) < 0.08
    for r in (a, b):   # caught Oct 17: the crown was picked on the fascia, above the paper that runs over the arch in both frames
        assert 0.05 < r["soffit"] - r["crown"] < 0.15, ("crown must sit a papered band under the wallpaper's top", r)
    for fr in ("2677", "3888"):
        r = rows[fr]; assert abs(r["door_height_at_rear_wall"] - 2.032) < 0.10   # 2677 -1.4%, 3888 +4.5%: depth is weak at this focal length
        assert abs(np.mean(r["door_z_at_rear_wall"]) - np.mean(BUILD_DOOR)) < 0.08
    # V4 checkpoint: the built arch stays on the film's (tolerance = the two cameras' spread + 2 cm)
    g = json.loads((ROOT / "spec/house_spec.ground.json").read_text())
    arch = next(d for d in g["doors"] if sorted(d["between"]) == ["foyer", "rear_passage"])
    film = {"right": (a["right_z"], b["right_z"]), "left": (a["left_z"], b["left_z"]), "crown": (a["crown"], b["crown"]), "spring": (a["spring"], b["spring"])}
    built = {"right": arch["span_spec"][0], "left": arch["span_spec"][1], "crown": arch["height"], "spring": arch["spring"]}
    OVERRIDE = {"left": "Marina 195 s / 1070.5 s and the user: the arch springs off the stair's side, no pier; the film's left jamb is tree-hidden (DEVIATIONS 35)"}
    for k, (u, v) in film.items():
        if k in OVERRIDE:
            print(f"V4 checkpoint arch {k}: built {built[k]:.3f}, film {u:.3f}/{v:.3f}: OVERRIDDEN ({OVERRIDE[k]})"); continue
        tol = abs(u - v) / 2 + 0.02
        ok = abs(built[k] - (u + v) / 2) <= tol
        print(f"V4 checkpoint arch {k}: built {built[k]:.3f}, film {u:.3f}/{v:.3f} (tol {tol:.3f}) {'ok' if ok else 'FAIL'}")
        assert ok, k
    json.dump({f: {"yaw": float(p[0]), "pos": [float(v) for v in p[1:4]], "f": float(p[4])} for f, p in cams.items()},
              open(ROOT / "measurements/foyer-film-cameras.json", "w"), indent=1)
    if "--views" in sys.argv:
        views(cams)
    if "--overlay" in sys.argv:
        overlay(cams, S)
    return cams, rows


def views(cams):
    """Unity views at the film cameras (near clip just inside the foyer's front wall: they stood outside the front door)."""
    for tag in ("before", "after"):
        P = ROOT / f"spec/captures/views/views-foyer-film-{tag}.json"
        keep = [v for v in json.loads(P.read_text()) if "inside" in v["name"]] if P.exists() else []
        V = []
        for fr, p in cams.items():
            pos = [p[1], p[2], -p[3]]; fwd = [-np.cos(p[0]), 0, np.sin(p[0])]
            V.append({"name": f"../foyer-film-cams/{tag}-{fr}", "pos": [round(float(v), 3) for v in pos],
                      "look_at": [round(float(pos[i] + fwd[i]), 3) for i in range(3)],
                      "vfov": round(float(np.degrees(2 * np.arctan(CY / p[4]))), 2), "near": round(float(pos[0] - 8.85), 2),
                      "note": f"film {fr}: level camera solved from flight 1's nosings (tools/house/foyer_cameras.py)"})
        P.write_text(json.dumps(V + keep, indent=1))


def overlay(cams, S):
    """Film frames with the build's lines: flight 1 (yellow; its open side is held out), the back wall built (green)."""
    from PIL import Image, ImageDraw
    g = json.loads((ROOT / "spec/house_spec.ground.json").read_text())
    arch = next(d for d in g["doors"] if sorted(d["between"]) == ["foyer", "rear_passage"])
    zr, zl = arch["span_spec"]; spring, crown = arch["spring"] - 0.0, arch["height"]
    land = next(b for b in S["stair"]["boxes"] if b["name"] == "landing")
    segs = {(255, 230, 0): [], (40, 255, 90): []}
    for b in S["stair"]["boxes"]:
        if b["name"].startswith("flight1_step"):
            segs[(255, 230, 0)].append([(b["x"][1], b["y"][1], 10.23), (b["x"][1], b["y"][1], 11.43)])
    zc, half, rise = (zr + zl) / 2, (zl - zr) / 2, crown - spring
    Rr = (half ** 2 + rise ** 2) / (2 * rise); yc = crown - Rr
    arc = [(X_BACK, G + yc + np.sqrt(Rr ** 2 - (z - zc) ** 2), z) for z in np.linspace(zl, zr, 25)]
    under = land["y"][0] - G
    segs[(40, 255, 90)] += [[(X_BACK, G, zl), (X_BACK, G + spring, zl)] + arc + [(X_BACK, G + spring, zr), (X_BACK, G, zr)],
                            [(X_BACK, G + under, 7.778), (X_BACK, G + under, 10.23)], [(X_BACK, G, 7.778), (X_BACK, G + under, 7.778)],
                            [(1.581, G, BUILD_DOOR[0]), (1.581, G + 2.032, BUILD_DOOR[0]), (1.581, G + 2.032, BUILD_DOOR[1]), (1.581, G, BUILD_DOOR[1])]]
    out = ROOT / "spec/captures/foyer-film-cams"; out.mkdir(exist_ok=True)
    for fr, p in cams.items():
        im = Image.open(ROOT / f"0-homealone/full/homealone-movie-screencaps.com-{fr}.jpg").convert("RGB"); d = ImageDraw.Draw(im)
        for col, L in segs.items():
            for s in L:
                for a, b in zip(s[:-1], s[1:]):
                    d.line([tuple(q) for q in proj(p, np.linspace(a, b, 20))], fill=col, width=3)
        im.save(out / f"lines-{fr}.jpg", quality=88)


if __name__ == "__main__":
    main()
