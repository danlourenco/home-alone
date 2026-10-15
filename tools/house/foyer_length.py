"""Foyer length and the main stair's place in it, from single Marina frames (no SfM): each frame's camera comes from its
own vanishing points (verticals + the foyer's two wall directions give the focal and the rotation), and the stair's
13 risers (rise 0.178 m, measurements/rooms/stairs.json) set the metres. Picks are px at 1920x1080 on 2-5x gridded crops.

  Part 1 203 s, facing the front door: open-side tread ends of treads 3-6 -> camera height; floor rows -> stair foot to
      the front wall (the foyer/vestibule partition). Second ruler: the front door leaf as 36 in.
  Part 1 312 s, facing the rear: the wall-side riser ends of all 13 risers -> camera height, going, and the planes of
      the picture wall (landing front) and the arched door. Its focal is poorly fixed (one VP near infinity), so it is
      swept; ratios and across-widths hold at every focal.
  Main-floor overhead (994 s): the foyer's rear wall is two storeys tall, so its top edge sits higher than the
      one-storey walls the plan was traced on; its floor line is compared with the living room's rear wall, whose face
      shows top to floor (drapes, hearth).

usage: uv run --with numpy --with scipy python -I tools/house/foyer_length.py
"""
import subprocess
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares

ROOT = Path(__file__).resolve().parents[2]
R = 0.178                                   # rise, m
P0 = np.array([960, 540.])
FRAMES = {   # VPs from tools/sfm/stair_pitch.py segments + vanishing_point (LSD, RANSAC 0.5 deg): across, along, vertical
    203: dict(v0=(4911.83, 366.51), v1=(519.46, 366.72), vv=(956.67, 10350.45)),
    312: dict(v0=(15647.59, 568.59), v1=(816.14, 549.46), vv=(886.67, -171037.9)),
}
TREADS_203 = {3: (1306, 711.5), 4: (1398.5, 652.5), 5: (1516, 579), 6: (1670, 484)}   # bottom-front corner of the open-side tread end
FRONT_WALL_203 = (540, 688)                 # base of the partition at the cased opening's left jamb
DOOR_203 = ((638, 611), (810, 602.5))      # front door leaf, sill corners
RISERS_312 = [(10, 1050), (80, 922), (145, 818), (198, 720), (242, 643), (282, 575), (317, 520), (347, 468),
              (373, 425), (398, 388), (418, 352), (438, 322), (455, 290)]   # wall-side riser ends, base corner, risers 1-13
PICTURE_312, DOOR_312 = ((1015, 763), (1290, 765)), ((812, 730), (985, 733))
OVERHEAD = dict(foyer_rear_top=330, foyer_rear_landing=415, living_rear_top=417, living_rear_floor=470, trace_front=872,
                stair_foot=735, landing_nosing=497)   # overhead_994.jpg rows, px


def camera(v0, v1, vv, f=None):
    v0, v1, vv = map(np.array, (v0, v1, vv))
    if f is None:
        f = float(np.sqrt(-(v0 - P0) @ (v1 - P0)))
    d = lambda v: (lambda x: x / np.linalg.norm(x))(np.array([v[0] - P0[0], v[1] - P0[1], f]))
    U = d(vv) * (1 if vv[1] < 0 else -1)    # up
    B = d(v1); B -= (B @ U) * U; B /= np.linalg.norm(B)
    A = np.cross(B, U)
    return f, A, B, U


def floor_pt(cam, uv):
    f, A, B, U = cam
    r = np.array([uv[0] - P0[0], uv[1] - P0[1], f]); t = -1 / (r @ U)
    return np.array([t * r @ A, t * r @ B])  # (across, along) in camera heights


def proj(cam, X):
    return P0 + cam[0] * X[:, :2] / X[:, 2:]


def fit_line(cam, px, ks, sign, g=None):
    """Equally spaced stair points O + k*(going*dir + R*up); dir free in the floor plane unless the going is fixed."""
    f, A, B, U = cam
    px = np.asarray(px, float); ks = np.asarray(ks, float)[:, None]

    def pts(q):
        run = (q[3] * A + q[4] * B) if g is None else sign * g * B
        return q[:3] + ks * (run + R * U)
    best = None
    for dep in (1.5, 3, 5):
        r0 = np.array([px[0, 0] - P0[0], px[0, 1] - P0[1], f]); q0 = np.r_[r0 / np.linalg.norm(r0) * dep, 0, sign * 0.27]
        s = least_squares(lambda q: (proj(cam, pts(q)) - px).ravel(), q0)
        if best is None or s.cost < best.cost:
            best = s
    q = best.x
    going = np.hypot(q[3], q[4]) if g is None else g
    return dict(O=q[:3], going=going, rms=float(np.sqrt(np.mean(best.fun ** 2))), Hc=float(-(q[:3] @ U)))


def frame_203():
    cam = camera(**FRAMES[203])
    ks = sorted(TREADS_203)
    out = {}
    for label, g in (("free", None), ("0.29", 0.29), ("0.254", 0.254)):
        s = fit_line(cam, [TREADS_203[k] for k in ks], [k - 1 for k in ks], -1, g)
        Hc = s["Hc"] + (R - 0.025)          # the corners are the nosing undersides of treads k (height k*R - 1 in)
        foot = s["O"] @ cam[2] + 0.025      # riser 1 ~1 in behind its nosing
        out[label] = dict(going=s["going"], rms=s["rms"], Hc=Hc, foot_to_front=floor_pt(cam, FRONT_WALL_203)[1] * Hc - foot)
    door = np.linalg.norm(floor_pt(cam, DOOR_203[0]) - floor_pt(cam, DOOR_203[1]))
    Hd = 0.9144 / door
    free = fit_line(cam, [TREADS_203[k] for k in ks], [k - 1 for k in ks], -1)
    foot_hc = (free["O"] @ cam[2] + 0.025) / out["free"]["Hc"]          # stair foot in camera heights (scale-free)
    out["door36"] = dict(Hc=Hd, foot_to_front=(floor_pt(cam, FRONT_WALL_203)[1] - foot_hc) * Hd)
    return cam[0], out


def frame_312(f=None):
    cam = camera(**FRAMES[312], f=f)
    s = fit_line(cam, RISERS_312, range(13), 1)
    A, B = cam[1], cam[2]
    foot, wall = s["O"] @ B, s["O"] @ A
    pic = [floor_pt(cam, p) * s["Hc"] for p in PICTURE_312]
    door = [floor_pt(cam, p) * s["Hc"] for p in DOOR_312]
    flight = 12 * s["going"]
    return dict(f=cam[0], going=s["going"], rms=s["rms"], Hc=s["Hc"], flight=flight,
                picture=np.mean([p[1] for p in pic]) - foot, door_plane=door[0][1] - foot,
                door_width=abs(door[1][0] - door[0][0]), foyer_width=pic[1][0] - wall, door_across=(door[0][0] - wall, door[1][0] - wall))


def overhead():
    o = OVERHEAD
    p_lo, p_hi = (o["living_rear_floor"] - o["living_rear_top"]) / np.array([3.0, 2.44])   # px per m of height, cut 2.44-3.0 m
    rear_floor = o["foyer_rear_landing"] + 2.314 * np.array([p_lo, p_hi])
    return dict(px_per_m=(p_lo, p_hi), foyer_rear_floor=rear_floor, living_rear_floor=o["living_rear_floor"],
                top_offset=o["living_rear_top"] - o["foyer_rear_top"])


def views(out=ROOT / "spec/captures/views/views-foyer-length.json"):
    """Unity cameras matching 203 s and 312 s from the solved poses, placed on the BUILT stair (spec/house_spec.json):
    the pose is relative to the stair's first riser, so the render shows what Marina's camera saw from the same spot."""
    import json
    st = json.loads((ROOT / "spec/house_spec.json").read_text())["stair"]
    b1 = next(b for b in st["boxes"] if b["name"] == "flight1_step01")
    x1, (zo, zw), y0 = b1["x"][1], b1["z"], -st["floor_to_floor_m"]
    res = []
    for t, cam, O, ref, axes, note in (
            (203, camera(**FRAMES[203]), None, (x1 + 0.025, y0 + R - 0.025, zo), (1, 1), "facing the front door"),
            (312, camera(**FRAMES[312]), None, (x1, y0, zw), (-1, -1), "facing the rear")):
        f, A, B, U = cam
        if t == 203:
            ks = sorted(TREADS_203); O = fit_line(cam, [TREADS_203[k] for k in ks], [k - 1 for k in ks], -1)["O"]
        else:
            O = fit_line(cam, RISERS_312, range(13), 1)["O"]
        sb, sa = axes                       # spec x per unit of B, spec z per unit of A
        world = lambda v: np.array([sb * (v @ B), v @ U, sa * (v @ A)])   # camera-frame vector -> spec (x, y, z)
        c = np.array(ref) - world(O)
        fw = world(np.array([0, 0, 1.0]))
        pos = [c[0], c[1], -c[2]]; look = [c[0] + fw[0], c[1] + fw[1], -(c[2] + fw[2])]
        res.append({"name": f"../foyer-length/marina-{t}", "pos": [round(v, 3) for v in pos], "look_at": [round(v, 3) for v in look],
                    "vfov": round(float(2 * np.degrees(np.arctan(540 / f))), 2), "note": f"Marina Part 1 {t} s ({note}), foyer_length.py pose"})
    out.write_text(json.dumps(res, indent=1) + "\n")
    return res


def main():
    f203, a = frame_203()
    print(f"203 s (facing the front; focal {f203:.0f} px from two VPs):")
    for k, v in a.items():
        extra = f"going {v['going']:.3f} m, rms {v['rms']:.1f} px, " if "going" in v else ""
        print(f"  {k:<6} {extra}camera height {v['Hc']:.2f} m, stair foot -> front wall {v['foot_to_front']:.2f} m")
    print("312 s (facing the rear; focal swept):")
    sweep = [frame_312(f) for f in (1300, 1454, 1600)]
    for b in sweep:
        print(f"  f {b['f']:.0f}: going {b['going']:.3f} (rms {b['rms']:.1f}), camera {b['Hc']:.2f} m, flight {b['flight']:.2f}, "
              f"foot -> picture wall {b['picture']:.2f} ({b['picture'] / b['flight']:.2f} x flight), -> arched door {b['door_plane']:.2f} "
              f"({b['door_plane'] / b['flight']:.2f} x flight); door {b['door_width']:.2f} m wide at {b['door_across'][0]:.2f}-{b['door_across'][1]:.2f} "
              f"from the stair wall; foyer width at the picture wall {b['foyer_width']:.2f}")
    o = overhead()
    print(f"overhead: parallax {o['px_per_m'][0]:.1f}-{o['px_per_m'][1]:.1f} px/m of height; foyer rear wall floor line at y "
          f"{o['foyer_rear_floor'][0]:.0f}-{o['foyer_rear_floor'][1]:.0f} vs the living room's {o['living_rear_floor']} "
          f"(trace tops differ by {o['top_offset']} px = the tall wall)")
    return a, sweep, o


if __name__ == "__main__":
    a, sweep, o = main()
    for v in views():
        print(f"view {v['name']}: pos {v['pos']}, vfov {v['vfov']}")
    fronts = [v["foot_to_front"] for v in a.values()]
    assert 2.0 < min(fronts) and max(fronts) < 3.0, "stair foot to front wall outside 2-3 m: re-pick"
    assert all(abs(b["picture"] / b["flight"] - 1) < 0.08 for b in sweep), "landing front no longer flush with the top riser"
    assert all(1.3 < b["door_plane"] / b["flight"] < 1.5 for b in sweep)
    assert all(abs(b["foyer_width"] - 3.67) < 0.15 and 0.8 < b["door_width"] < 1.0 for b in sweep[1:2]), "f=1454 widths off"
    assert abs(o["foyer_rear_floor"].mean() - o["living_rear_floor"]) < 15, "foyer rear not flush with the living room's"
