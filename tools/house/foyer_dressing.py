"""Foyer dressing from Marina's frames: every piece is placed by intersecting picked pixel rays with the wall or floor it
stands on, using the cameras solved in foyer_length.py (203 s facing the front door, 312 s facing the rear), each pinned to
the BUILT stair's first riser. Sizes not visible in a frame are US standards and say so. Colours are sampled from the
frames. Writes spec/dressing/foyer.json, which SpecGreybox.Dressing builds on the ground floor (y = above the foyer floor).

Stair and soffit pieces come from the built stair boxes, so they follow the stair if it changes.
usage: uv run --with numpy --with scipy --with pillow python -I tools/house/foyer_dressing.py
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/house"))
import foyer_length as FL  # noqa: E402

OUT = ROOT / "spec/dressing/foyer.json"
WHITE = 0.85                                   # albedo of white paint
TILE = ROOT / "spec/dressing/wallpaper.png"    # one repeat of the damask, cut from 203 s (front wall, near face-on)
# one repeat: autocorrelation of the wall at x 285-500, y 0-230 peaks at (83, 4) and (5, 88) px, a straight 83 x 88 px repeat;
# at 275 px/m there (wainscot 0.73 m at row 497, casing head 1.99 m at row 150) that is 0.32 m wide x 0.30 m tall
TILE_PX, REPEAT_M = (303, 40, 391, 123), (0.32, 0.30)
VIDEO = ROOT / "Tour the Home Alone House_ Part 1, Main Floor [CG Tour] copy.mp4"
FRAMES = ROOT / "sfm-work/foyer-frames"


def frame_image(t):
    from PIL import Image
    p = FRAMES / f"{t}.png"
    if not p.exists():
        FRAMES.mkdir(parents=True, exist_ok=True)
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-ss", str(t), "-i", str(VIDEO), "-frames:v", "1", str(p)], check=True)
    return np.asarray(Image.open(p).convert("RGB"), float)


class Cam:
    """A solved frame as a spec-space camera: centre c (spec x, y above the foyer floor, z) and pixel ray directions."""

    def __init__(self, t, st):
        b1 = next(b for b in st["boxes"] if b["name"] == "flight1_step01")
        x1, (zo, zw) = b1["x"][1], b1["z"]
        self.cam = FL.camera(**FL.FRAMES[t])
        f, A, B, U = self.cam
        if t == 203:
            ks = sorted(FL.TREADS_203)
            O = FL.fit_line(self.cam, [FL.TREADS_203[k] for k in ks], [k - 1 for k in ks], -1)["O"]
            ref, (self.sb, self.sa) = np.array([x1 + 0.025, FL.R - 0.025, zo]), (1, 1)
        else:
            O = FL.fit_line(self.cam, FL.RISERS_312, range(13), 1)["O"]
            ref, (self.sb, self.sa) = np.array([x1, 0.0, zw]), (-1, -1)
        self.c = ref - self.world(O)
        self.img = frame_image(t)
        wp = {312: (1640, 720, 1700, 820), 203: (300, 520, 480, 640)}[t]      # lit white wainscot in each frame
        self.white = np.median(self.img[wp[1]:wp[3], wp[0]:wp[2]].reshape(-1, 3), 0)

    def world(self, v):
        f, A, B, U = self.cam
        return np.array([self.sb * (v @ B), v @ U, self.sa * (v @ A)])

    def ray(self, px):
        return self.world(np.array([px[0] - FL.P0[0], px[1] - FL.P0[1], self.cam[0]]))

    def on(self, px, axis, value):
        """Spec point where pixel px's ray meets the plane spec[axis] = value (axis 0 x, 1 y, 2 z)."""
        d = self.ray(px); t = (value - self.c[axis]) / d[axis]
        return self.c + t * d

    def colour(self, x0, y0, x1, y1):
        """Surface colour: the patch's median over this frame's white-wainscot median, times white paint's ~0.85, so
        Marina's lighting (and the frame's exposure) divides out"""
        m = np.median(self.img[y0:y1, x0:x1].reshape(-1, 3), 0)
        return [round(float(min(1.0, v)), 3) for v in m / self.white * WHITE]


def box(name, x, y, z, colour, collide=False, note=""):
    return {"name": name, "x": [round(float(min(x)), 3), round(float(max(x)), 3)], "y": [round(float(min(y)), 3), round(float(max(y)), 3)],
            "z": [round(float(min(z)), 3), round(float(max(z)), 3)], "colour": colour, "collide": collide, "note": note}


def seg(name, a, b, w, t, colour, collide=False, note=""):
    """A box whose long axis runs a -> b (spec, y above the foyer floor); w across horizontally, t across in the vertical plane."""
    return {"name": name, "a": [round(float(v), 3) for v in a], "b": [round(float(v), 3) for v in b], "w": w, "t": t,
            "colour": colour, "collide": collide, "note": note}


def service_soffit(g, white):
    """The service stair's underside over the basement flight (walk note 2026-10-20 07:13, 'i'd expect a soffit here'): its solid step
    boxes left a dark sawtooth over the basement stair. As flight 2's soffit: a 12 mm white board on the line through each straight step's
    low (-x) bottom corner, from the winders to the end wall, and a flat ceiling under the winders closed by a short vertical face.
    Built from the spec's step boxes (ground y), so it follows the stair."""
    st = g["stair"]; B = {b["name"]: b for b in st["boxes"] if b["kind"] == "step"}
    run = sorted((b for n, b in B.items() if n.startswith("service_step")), key=lambda b: -b["x"][1])
    if not run:
        return []
    r, go = st["rise_m"], st["going_m"]; z0, z1 = run[0]["z"]
    x_hi = run[0]["x"][1]                                         # the winders' low-x edge
    x_end = min(o["x"][0] for o in st["ceiling_openings"])       # the bay's end wall
    slope = r / go
    y_at = lambda x: run[0]["y"][0] + (run[0]["x"][0] - x) * slope   # the line through the low (-x) bottom corners
    assert all(y_at(b["x"][0]) <= b["y"][0] + 1e-6 and y_at(b["x"][1]) <= b["y"][0] + 1e-6 for b in run), "soffit above a step"
    win = [b for n, b in B.items() if n.startswith("service_winder")]
    yw = min(b["y"][0] for b in win)                             # under the lowest winder
    note = "walk note 2026-10-20 07:13: the service stair's underside over the basement flight, as flight 2's soffit (white board, 12 mm)"
    return [seg("service_soffit", [x_hi, y_at(x_hi) - 0.006, (z0 + z1) / 2], [x_end, y_at(x_end) - 0.006, (z0 + z1) / 2], z1 - z0, 0.012, white, note=note),
            box("service_soffit_winders", [x_hi, max(b["x"][1] for b in win)], [yw - 0.012, yw], [z0, z1], white, note=note),
            box("service_soffit_step", [x_hi - 0.012, x_hi], [yw - 0.012, y_at(x_hi) - 0.012], [z0, z1], white, note=note)]


def main():
    up = json.loads((ROOT / "spec/house_spec.json").read_text())
    st = up["stair"]; F = st["floor_to_floor_m"]
    g = json.loads((ROOT / "spec/house_spec.ground.json").read_text())
    foyer = np.array(next(s["polygon_xz"] for s in g["spaces"] if s["name"] == "foyer"))
    vest = np.array(next(s["polygon_xz"] for s in g["spaces"] if s["name"] == "vestibule"))
    XF = foyer[:, 0].max()                                   # front wall (foyer/vestibule partition)
    ZN, ZS = foyer[:, 1].min(), foyer[:, 1].max()           # north (dining side) wall, south (stair) wall
    XV = vest[:, 0].max()                                    # vestibule front (the front door's wall)
    B = {b["name"]: b for b in st["boxes"]}
    land = B["landing"]; XL = land["x"][1]; ZN2 = land["z"][0]
    XR = land["x"][0]                                        # rear wall (the foyer itself now ends at the back wall under the landing, Oct 15)
    s1 = B["flight1_step01"]; X1 = s1["x"][1]; z1, zs = s1["z"]
    r, g1 = st["rise_m"], st["going_m"]
    LT = land["y"][1] + F                                    # landing top above the foyer floor
    f2 = sorted((b for b in st["boxes"] if b["name"].startswith("flight2_step")), key=lambda b: b["name"])
    XH = f2[-1]["x"][1]; zg = f2[0]["z"][1]
    c312, c203 = Cam(312, st), Cam(203, st)

    # colours, median of patches in Marina's frames
    C = {"wallpaper": c312.colour(1500, 300, 1650, 500), "white": c312.colour(1640, 720, 1700, 820),
         "runner": c312.colour(300, 700, 450, 900), "floor": c203.colour(300, 1000, 560, 1070),
         "rug_red": c312.colour(1000, 880, 1100, 980), "front_rug": c203.colour(700, 735, 1000, 790),
         "green": c312.colour(735, 680, 790, 800), "pot": c312.colour(760, 830, 860, 900), "wood": c312.colour(1300, 650, 1450, 680),
         "seat": c312.colour(1420, 770, 1560, 795), "gilt": c312.colour(1400, 450, 1410, 520), "mirror": c312.colour(1430, 400, 1460, 520),
         "glass": c312.colour(760, 30, 840, 80), "leaves": c312.colour(900, 300, 960, 450), "rail": [0.25, 0.14, 0.08]}
    P = []

    # --- stair: runner over every tread and riser (nearly full width; white riser ends at the wall), carpet on the landing
    RW = 1.10                                                # measured tread band 1.125 (stairs.json) less the visible white ends
    zc = (z1 + zs) / 2
    for b in sorted((b for b in st["boxes"] if b["name"].startswith("flight1_step")), key=lambda b: b["name"]):
        top = b["y"][1] + F
        P.append(box(b["name"] + "_runner", b["x"], [top, top + 0.012], [zc - RW / 2, zc + RW / 2], C["runner"]))
        P.append(box(b["name"] + "_runner_riser", [b["x"][1], b["x"][1] + 0.012], [top - r, top + 0.012], [zc - RW / 2, zc + RW / 2], C["runner"]))
    P.append(box("landing_carpet", land["x"], [LT, LT + 0.012], land["z"], C["runner"], note="Marina 346-350 s: wall-to-wall red on the landing"))
    P.append(box("landing_riser_runner", [XL, XL + 0.012], [LT - r, LT], [zc - RW / 2, zc + RW / 2], C["runner"]))
    zc2 = (ZN2 + zg) / 2
    for b in f2:   # flight 2's step boxes are hidden (colliders kept): thin white treads and risers over a smooth soffit
        top = b["y"][1] + F
        P.append(box(b["name"] + "_tread", b["x"], [top - 0.03, top], b["z"], C["white"]))
        P.append(box(b["name"] + "_riser", [b["x"][0] - 0.02, b["x"][0]], [top - r, top], b["z"], C["white"]))
        P.append(box(b["name"] + "_runner", b["x"], [top, top + 0.012], [zc2 - RW / 2, zc2 + RW / 2], C["runner"]))
        P.append(box(b["name"] + "_runner_riser", [b["x"][0] - 0.012, b["x"][0]], [top - r, top], [zc2 - RW / 2, zc2 + RW / 2], C["runner"]))
    # flight 2's smooth white soffit (Marina 312 s: starts at the picture wall's top, 2.26 m, rises to the upper floor)
    lo = f2[0]["y"][0] + F   # flight 2's own underside (was the landing's: 9 cm lower since the landing's fascia deepened, a gap; walk note Oct 15)
    P.append(seg("flight2_soffit", [XL, lo - 0.006, zc2], [XH, lo + (len(f2)) * r - 0.006, zc2], zg - ZN2, 0.012, C["white"],
                 note="Marina 312 s: white sloped soffit meeting the north wall in a diagonal"))
    # flight 2's open-side stringer: a white band from the soffit up to the tread line, closing the side (walk note Oct 15: 'I can
    # see through to the wall on the landing')
    sl = f2[0]["y"][1] - f2[0]["y"][0] - r                      # the flight's construction depth below the first tread
    hb = sl + r - 0.03; p2 = np.arctan2(r, (XH - XL) / len(f2))
    P.append(seg("flight2_stringer_open", [XL, lo + hb / 2, zg - 0.012], [XH, lo + len(f2) * r + hb / 2, zg - 0.012], 0.024, hb * np.cos(p2), C["white"]))
    # open-side stringer: white band along the nosing line; handrail on it; newels (Marina 334 s: white square newel, dark rail)
    pitch = np.arctan2(r, g1)
    drop = 0.12 / np.cos(pitch)
    a = np.array([X1, -drop + r * 0.5, z1 - 0.012]); b_ = np.array([XL, LT - drop - r * 0.5, z1 - 0.012])
    P.append(seg("flight1_stringer_open", a, b_, 0.024, 0.26, C["white"]))
    P.append(seg("flight1_skirt_wall", [X1, r * 0.5 + 0.02, zs - 0.012], [XL, LT + 0.02, zs - 0.012], 0.024, 0.30, C["white"],
                 note="Marina 334-342 s: tall white skirt along the stair wall"))
    RH = 0.86                                                # handrail height above the nosing line (US standard 34-38 in)
    P.append(seg("flight1_handrail", [X1 + 0.05, r + RH + 0.15, z1 - 0.03], [XL, LT + RH, z1 - 0.03], 0.07, 0.06, C["rail"],
                 note="continuous dark rail; rises to meet the bottom newel's cap"))
    P.append(box("newel_bottom", [X1 - 0.02, X1 + 0.13], [0, 1.12], [z1 - 0.12, z1 + 0.03], C["white"], collide=True,
                 note="Marina 312 s: square white newel at the bottom step, open side; height standard ~44 in"))
    P.append(box("newel_bottom_cap", [X1 - 0.04, X1 + 0.15], [1.12, 1.18], [z1 - 0.14, z1 + 0.05], C["rail"]))
    P.append(box("newel_landing", [XL - 0.13, XL + 0.02], [LT - 0.6, LT + 1.12], [z1 - 0.12, z1 + 0.03], C["white"], collide=True))
    P.append(box("bottom_step_bullnose", [X1, X1 + 0.12], [0, r], [z1 - 0.2, zs], C["white"], collide=True,
                 note="Marina 334 s: the bottom step curls out past the newel; built square"))
    P.append(box("bottom_step_bullnose_runner", [X1, X1 + 0.13], [r, r + 0.012], [zc - RW / 2, zc + RW / 2], C["runner"]))

    # --- landing rear wall (x = XR): window, painting and half-round table (Marina 312 s; 346-350 s)
    # the landing window is a real opening: measured in measurements/windows/ground.json (wall_openings; sill 2.69 from this frame,
    # 312 s glass x 735-965 at row 235), cut by SpecGreybox.CutWallOpenings and built by tools/house/hifi_landing_window.py
    pa, pb = c312.on((560, 20), 0, XR), c312.on((668, 140), 0, XR)
    P.append(box("landing_painting", [XR + 0.01, XR + 0.04], [pb[1], pa[1]], [pa[2], pb[2]], [0.62, 0.36, 0.30], note="312 s, frame x 560-668 y 20-140"))
    ta, tb = c312.on((540, 180), 0, XR), c312.on((680, 180), 0, XR)
    P.append(box("landing_table", [XR, XR + 0.32], [LT, ta[1]], [ta[2], tb[2]], C["wood"], collide=True, note="312 s top row 180; depth standard"))

    # --- north wall: console, mirror, chairs (312 s). The wall is seen at a grazing angle, so rays meet MARINA's wall plane
    # (3.71 m from the stair wall, foyer_length.py) and the piece is set against the built wall at that x
    ZM = ZS - FL.frame_312(1454)["foyer_width"]
    # along the grazing wall only heights are trusted; positions come from the chairs' feet on the floor (312 s), which the
    # overhead's floor-level offsets from the stair foot agree with (chairs ~0.1 and ~1.8 m behind it, console between)
    chairs = {name: c312.on(px, 1, 0.0)[0] for name, px in (("chair_rear", (1227, 845)), ("chair_front", (1520, 1000)))}
    mid = (chairs["chair_rear"] + chairs["chair_front"]) / 2
    ch = c312.on((1290, 632), 2, ZM)[1]
    P.append(box("console", [mid - 0.5, mid + 0.5], [0, ch], [ZN, ZN + 0.36], C["wood"], collide=True,
                 note=f"centred between the chairs (x {mid:.2f}); top {ch:.2f} m (312 s row 632 on the wall); 1.0 x 0.36 demilune standard"))
    mt, mb = c312.on((1440, 280), 2, ZM)[1], c312.on((1440, 580), 2, ZM)[1]
    P.append(box("mirror_frame", [mid - 0.28, mid + 0.28], [mb, mt], [ZN, ZN + 0.03], C["gilt"],
                 note=f"312 s oval rows 280-580 -> {mb:.2f}-{mt:.2f} m, centred over the console; width 0.56 assumed (grazing view)"))
    P.append(box("mirror_glass", [mid - 0.2, mid + 0.2], [mb + 0.08, mt - 0.08], [ZN + 0.03, ZN + 0.035], C["mirror"]))
    for name, cx in chairs.items():
        cz = ZN + 0.35
        P.append(box(name + "_seat", [cx - 0.22, cx + 0.22], [0.40, 0.46], [cz - 0.22, cz + 0.22], C["seat"], collide=True,
                     note=f"312 s front-leg foot -> x {cx:.2f}; seat 0.44 m (clip A solve), 18 in square standard"))
        P.append(box(name + "_back", [cx - 0.2, cx + 0.2], [0.46, 0.92], [cz - 0.24, cz - 0.2], C["wood"], collide=True))

    # --- picture wall (x = XL plane, z ZN..8.95): framed picture
    qa, qb = c312.on((1075, 410), 0, XL), c312.on((1165, 530), 0, XL)
    P.append(box("picture_wall_picture", [XL + 0.01, XL + 0.04], [qb[1], qa[1]], [qb[2], qa[2]], [0.85, 0.82, 0.75], note="312 s x 1075-1165 y 410-530"))
    P.append(box("picture_wall_picture_flowers", [XL + 0.04, XL + 0.045], [qb[1] + 0.08, qa[1] - 0.08], [qb[2] + 0.06, qa[2] - 0.06], c312.colour(1085, 420, 1155, 520)))

    # --- floor pieces
    rq = [c312.on(p, 1, 0.0) for p in ((900, 795), (1040, 795), (1260, 1035), (980, 1050))]
    P.append(box("runner_rug", [min(p[0] for p in rq), max(p[0] for p in rq)], [0, 0.01], [np.mean([rq[1][2], rq[2][2]]), np.mean([rq[0][2], rq[3][2]])],
                 C["rug_red"], note="312 s corners (900,795) (1040,795) (1260,1035) (980,1050)"))
    fq = [c203.on(p, 1, 0.0) for p in ((585, 712), (1035, 678), (1127, 757), (603, 833))]
    P.append(box("front_rug", [min(p[0] for p in fq), max(p[0] for p in fq)], [0, 0.01], [min(p[2] for p in fq), max(p[2] for p in fq)],
                 C["front_rug"], note="203 s corners (585,712) (1035,678) (1127,757) (603,833)"))
    pf = c312.on((810, 928), 1, 0.0); pw = np.linalg.norm(c312.on((745, 928), 1, 0.0) - c312.on((875, 928), 1, 0.0))
    pc = pf + np.array([-pw / 2, 0, 0])
    P.append(box("tree_pot", [pc[0] - pw / 2, pc[0] + pw / 2], [0, 0.42], [pc[2] - pw / 2, pc[2] + pw / 2], C["pot"], collide=True,
                 note=f"312 s pot front foot (810,928), width {pw:.2f} m"))
    P.append(box("tree_trunk", [pc[0] - 0.03, pc[0] + 0.03], [0.42, 1.5], [pc[2] - 0.03, pc[2] + 0.03], [0.55, 0.5, 0.42]))
    k0, k1 = c312.on((810, 510), 0, pc[0])[1], c312.on((810, 210), 0, pc[0])[1]
    kw = abs(c312.on((660, 360), 0, pc[0])[2] - c312.on((960, 360), 0, pc[0])[2])
    kw = min(kw, 0.6)   # the frame's crown is see-through foliage; a solid box that wide hides the stair behind it
    P.append(box("tree_crown", [pc[0] - kw / 2, pc[0] + kw / 2], [k0, k1], [pc[2] - kw / 2, pc[2] + kw / 2], C["leaves"],
                 note=f"312 s crown rows 210-510, x 660-960 at the pot -> {k0:.2f}-{k1:.2f} m, {kw:.2f} m across (a solid box: Marina's is see-through)"))
    bq = c312.on((797, 832), 1, 0.0)
    P.append(box("bench", [bq[0] - 1.25, bq[0]], [0, 0.45], [z1 - 0.06 - 0.48, z1 - 0.06], C["green"], collide=True,
                 note=f"312 s near-end foot (797,832) -> x {bq[0]:.2f}; against the stair's open side; 1.25 x 0.48 (overhead 77 x 22 px)"))
    for side, (px, py) in (("left", (420, 690)), ("right", (1085, 642))):
        q = c203.on((px, py), 1, 0.0); q[0] = XF - 0.17   # its feet sit on the wall's base line (203 s): against the wall
        P.append(box(f"flower_stand_{side}", [q[0] - 0.14, q[0] + 0.14], [0, 0.95], [q[2] - 0.14, q[2] + 0.14], C["wood"], collide=True,
                     note=f"203 s foot ({px},{py}) -> z {q[2]:.2f}, against the front wall; height ~0.95 (203 s)"))
        P.append(box(f"flowers_{side}", [q[0] - 0.2, q[0] + 0.2], [0.95, 1.3], [q[2] - 0.2, q[2] + 0.2], [0.93, 0.93, 0.9]))
        P.append(box(f"print_{side}", [XF - 0.03, XF], [1.37, 1.95], [q[2] - 0.24, q[2] + 0.24], [0.22, 0.38, 0.33],
                     note="green-matted lily print over each stand (Marina 214-217 s); size from 203 s rows ~240-460"))
        P.append(box(f"print_{side}_paper", [XF - 0.035, XF - 0.03], [1.45, 1.87], [q[2] - 0.17, q[2] + 0.17], [0.85, 0.83, 0.78]))

    # French door leaves: NOT built. A front-jamb leaf open 90 deg would hide the left flower stand in 203 s, where Marina shows
    # it; how her leaves swing is unmeasured (DEVIATIONS 29)

    # --- front: casing around the foyer/vestibule opening (203 s) and the vestibule's front door with sidelights
    # the opening's casing is NOT placed here: casing is generated from the opening's cut (SpecGreybox, cased openings), so the two
    # cannot disagree (user note Oct 16 09:41: a gap above a placed casing showed into the vestibule). Its head, 1.99 m from these
    # inner jambs (203 s x 545/975 at row 150), is the opening's crown in measurements/overhead/ground-doors.json
    da, db = c203.on((638, 215), 0, XV), c203.on((810, 215), 0, XV)
    P.append(box("front_door", [XV - 0.05, XV], [0, da[1]], [db[2], da[2]], C["white"], note=f"203 s leaf x 638-810, head row 215 -> {da[1]:.2f} m"))
    for name, (u0, u1) in (("sidelight_left", (550, 618)), ("sidelight_right", (830, 900))):
        sa_, sb_ = c203.on((u0, 230), 0, XV), c203.on((u1, 495), 0, XV)
        P.append(box(name, [XV - 0.03, XV], [sb_[1], sa_[1]], [min(sa_[2], sb_[2]), max(sa_[2], sb_[2])], C["glass"]))
        P.append(box(name + "_panel", [XV - 0.05, XV], [0, sb_[1]], [min(sa_[2], sb_[2]), max(sa_[2], sb_[2])], C["white"]))

    # --- wall finishes: wainscot to the chair rail, wallpaper above (heights from the frames)
    wn = c312.on((1600, 662), 2, ZS - FL.frame_312(1454)['foyer_width'])[1]; wp = c312.on((1100, 610), 0, XL)[1]; wf = c203.on((400, 497), 0, XF)[1]
    from PIL import Image
    x0, y0, x1, y1 = TILE_PX
    tile = np.clip(c203.img[y0:y1, x0:x1] / c203.white * WHITE * 255, 0, 255).astype(np.uint8)
    Image.fromarray(tile).resize((528, 498), Image.LANCZOS).save(TILE)
    film = ROOT / "spec/dressing/wallpaper_film.png"   # the film's red damask (tools/house/film_wallpaper.py) wins when present (user, Oct 15)
    tex, rep = (film, json.loads(film.with_suffix(".json").read_text())["repeat_m"]) if film.exists() else (TILE, list(REPEAT_M))
    walls = {"wallpaper_texture": str(tex.relative_to(ROOT)), "wallpaper_repeat_m": rep, "wainscot_m": round(float(np.median([wn, wp, wf])), 3), "reads": {"north wall 312 s": round(float(wn), 3), "picture wall 312 s": round(float(wp), 3),
             "front wall 203 s": round(float(wf), 3)}, "wainscot": C["white"], "wallpaper": C["wallpaper"], "floor": C["floor"],
             "spaces": ["foyer", "vestibule", "rear_passage"],   # rear_passage: film 2677, the damask runs on inside the arch
             "wainscot_by_space": {"vestibule": 0.14, "main_stair_opening": 0.0},   # the stair well's walls: papered, no floor at the
                                                                                   # upstairs level, so no wainscot or trim (film 384, 11966)
             "wainscot_by_space_note": "film 10248 (camera solved, tools/house/film_solve_10248.py): the vestibule's walls are papered to a ~0.14 m baseboard, no 0.7 m wainscot"}
    P += service_soffit(g, C["white"])
    # the colours table's runner (read by the hi-fi stair) was set by hand in the json (ef5a94a1, film 1616/10673, user: "Fix the stair
    # runner too"); the pieces above keep the sampled colour, as committed
    C = dict(C, runner=[0.36, 0.035, 0.06])
    out = {"note": __doc__.split("\n\n")[0], "colours": C, "walls": walls,
           "stair": {"step": C["white"], "spindle": C["white"], "landing": C["white"], "well_wall": C["wallpaper"], "hide": ["flight1_rail*_cap", "flight2_step*"]},
           "pieces": P}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1) + "\n")
    return out, c312, c203


if __name__ == "__main__":
    out, c312, c203 = main()
    w = out["walls"]
    print(f"cameras: 312 s at spec {np.round(c312.c, 2)}, 203 s at {np.round(c203.c, 2)}")
    print(f"wainscot reads {w['reads']} -> {w['wainscot_m']} m")
    for p in out["pieces"]:
        if "x" in p and p["note"]:
            print(f"  {p['name']:<26} x {p['x']} y {p['y']} z {p['z']}  {p['note'][:70]}")
    reads = list(w["reads"].values())
    assert max(reads) - min(reads) < 0.12, "wainscot heights disagree across walls/frames: re-pick"
    assert all(0.6 < v < 1.1 for v in reads), "wainscot outside 0.6-1.1 m"
    print("->", OUT.relative_to(ROOT))
