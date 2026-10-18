"""buzz_trunk: Buzz's footlocker (the film's hero prop, Kevin rummages through it, film 2688-2766): its size from two rulers of
different kinds, its lining tile cut from the film, and its spot in Buzz's room checked against the adult passage.
Writes spec/dressing/buzz_trunk.json (read by tools/house/purchased_trunk.py and SpecGreybox.Trunk) and
spec/dressing/buzz_trunk_lining.png (FILM-derived, not from the bought model), pick crops in spec/captures/picks/buzztrunk/ and the
passage plot spec/captures/views/buzztrunk/passage.png.

  uv run --with numpy --with scipy --with pillow --with matplotlib python -I tools/house/buzz_trunk.py

SIZE (film 2704, the overhead insert: box open, rim seen whole across the frame, the Playboy's back cover lying flat on top)
  Ruler 1, object: the Playboy (21.0 x 27.6 cm), long side across the frame, 500 px (x 1212-1712, row 700) -> 18.1 px/cm at the
  magazine's depth. The magazine lies against the right wall (its right edge = where the wall's lining starts, x 1712); the rim's
  inner edge on that wall is at x 1801, so the rim is nearer the camera by (1801-cx)/(1712-cx) (cx = 960, principal point assumed
  central; +-50 px moves it 0.8%). Rim outer edges at row 700: x 70 / 1813 -> outer length = 1743 px / rim scale.
  Ruler 2, anatomy: Kevin's fist on the right rim (film 2700, x ~1740-1890): its breadth across the knuckles 140 +- 10 px, at about
  rim depth; a 10-year-old boy's hand breadth 6.4-7.2 cm (child anthropometry, a range, not one number).
  Depth (front to back): >= the rim seen from the front rim (row 880) to the frame's top (the back rim is at or above row 0 in every
  overhead frame), at the magazine's vertical/horizontal foreshortening (340/500 px vs 21/27.6 cm = 0.885): a LOWER bound only.
  Height: NOT seen in any frame (the outside is only seen from above, 2688-2691); kept from the scan's own proportions (uniform scale)
  and checked loosely against Kevin kneeling with his forearm on the rim (2720). DEVIATIONS.
"""
import json
from pathlib import Path

import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt, gaussian_filter, label

ROOT = Path(__file__).resolve().parents[2]
FILM = lambda n: ROOT / f"0-homealone/full/homealone-movie-screencaps.com-{n}.jpg"
OUT = ROOT / "spec/dressing/buzz_trunk.json"
PICKS = ROOT / "spec/captures/picks/buzztrunk"

# ---- picks (film pixels, 1920 x 1080), read on 4-5x gridded crops; +- is the read spread
MAG_L, MAG_R, MAG_ROW, MAG_PX_TALL = 1212, 1712, 700, 340      # 2704: Playboy back cover, edges at row 700; height 525-865
RIM_IN_R, RIM_OUT_L, RIM_OUT_R = 1801, 70, 1813               # 2704 row 700: rim inner edge on the right wall, outer edges both sides
EDGE = 5                                                       # px, each edge
CX = 960
FIST_PX, FIST_SD = 140, 10                                     # 2700: Kevin's fist on the right rim
HAND_CM = (6.4, 7.2)                                           # 10-year-old boy, hand breadth range
FRONT_ROW = 880                                                # 2704: front rim (top of the brass) at the frame's centre


def size():
    def L_mag(ml, mr, ri, ro_l, ro_r):
        s_mag = (mr - ml) / 27.6
        k = (ri - CX) / (mr - CX)                               # rim nearer than the magazine
        return (ro_r - ro_l) / (s_mag * k) / 100, s_mag * k
    L0, s_rim = L_mag(MAG_L, MAG_R, RIM_IN_R, RIM_OUT_L, RIM_OUT_R)
    runs = [L_mag(MAG_L + a, MAG_R + b, RIM_IN_R + c, RIM_OUT_L + d, RIM_OUT_R + e)[0]
            for a in (-EDGE, EDGE) for b in (-EDGE, EDGE) for c in (-EDGE, EDGE) for d in (-EDGE, EDGE) for e in (-EDGE, EDGE)]
    # a 1 cm gap between the magazine and the wall (its edge not touching): wall 18 px further in
    runs.append((RIM_OUT_R - RIM_OUT_L) / ((MAG_R - MAG_L) / 27.6 * (RIM_IN_R - CX) / (MAG_R - 18 - CX)) / 100)
    fist = [(RIM_OUT_R - RIM_OUT_L) * h / (FIST_PX + d) / 100 for h in HAND_CM for d in (-FIST_SD, FIST_SD)]
    fist_c = (RIM_OUT_R - RIM_OUT_L) * np.mean(HAND_CM) / FIST_PX / 100
    fore = MAG_PX_TALL / (MAG_R - MAG_L) / (21.0 / 27.6)          # vertical / horizontal foreshortening at the magazine
    depth_min = FRONT_ROW / (s_rim * fore) / 100
    return dict(L_playboy=round(L0, 3), L_playboy_spread=[round(min(runs), 3), round(max(runs), 3)],
                L_fist=round(fist_c, 3), L_fist_spread=[round(min(fist), 3), round(max(fist), 3)],
                rim_px_per_cm=round(s_rim, 2), foreshortening=round(fore, 3), depth_min=round(depth_min, 3))


def crops():
    PICKS.mkdir(parents=True, exist_ok=True)
    im = Image.open(FILM(2704))
    im.crop((1150, 480, 1850, 900)).save(PICKS / "playboy-2704.png")
    im.crop((1660, 620, 1860, 780)).resize((400, 320), Image.NEAREST).save(PICKS / "rim_right-2704.png")
    im.crop((20, 620, 220, 780)).resize((400, 320), Image.NEAREST).save(PICKS / "rim_left-2704.png")
    Image.open(FILM(2700)).crop((1600, 700, 1920, 960)).save(PICKS / "fist-2700.png")


# ---- lining tile: the box's back wall in 2704 (crisp, in shade), x 160-1640, rows 2-68. The chips are foreshortened vertically
# (autocorrelation half-widths 4 px across vs 2 down): stretched x2 down on the assumption the chips lie at random (OSB-look paper).
# Three strips cut from different stretches of the band are stacked and cross-faded (the pattern is random: no repeat to find);
# colour from the lit lining in 2718 (x 40-600, rows 690-850) against Kevin's cream sweater in the same frame (albedo 0.75 assumed).
def lining():
    band = np.asarray(Image.open(FILM(2704)).convert("RGB"), float)[2:68, 160:1640]
    band = np.asarray(Image.fromarray(band.astype(np.uint8)).resize((band.shape[1], band.shape[0] * 2), Image.BICUBIC), float)
    W, H, F = 384, band.shape[0], 16                            # tile width px, strip height, cross-fade rows
    strips = [band[:, x0:x0 + W] for x0 in (0, 520, 1040)]
    rows = H * 3 - F * 3
    tile = np.zeros((rows, W, 3)); wsum = np.zeros((rows, 1, 1))
    ramp = np.ones(H); ramp[:F] = np.linspace(0, 1, F); ramp[-F:] = np.linspace(1, 0, F)
    for i, s in enumerate(strips):   # wrapped: the last strip fades into the first
        for r in range(H):
            y = (i * (H - F) + r) % rows
            tile[y] += s[r] * ramp[r]; wsum[y] += ramp[r]
    tile /= np.maximum(wsum, 1e-6)
    xf = 24; a = np.linspace(0, 1, xf)[None, :, None]           # wrap across: the left edge fades into the right
    tile[:, :xf] = tile[:, :xf] * a + tile[:, -xf:][:, ::-1] * 0 + tile[:, -xf:] * (1 - a)
    tile = tile[:, : W - xf]
    lum = tile.mean(2); bg = gaussian_filter(lum, 30, mode="wrap")
    tile = tile / bg[..., None] * lum.mean()
    lin = lambda c: np.where(c / 255 <= 0.04045, c / 255 / 12.92, ((c / 255 + 0.055) / 1.055) ** 2.4)
    f2718 = np.asarray(Image.open(FILM(2718)).convert("RGB"), float)
    lit = lin(f2718[690:850, 40:600]).reshape(-1, 3).mean(0); sweater = lin(f2718[700:900, 1300:1500]).reshape(-1, 3).mean(0)
    target = lit / sweater.mean() * 0.75
    t = lin(tile); t = np.clip(t * (target / t.reshape(-1, 3).mean(0)), 0, 1)
    srgb = np.where(t <= 0.0031308, t * 12.92, 1.055 * t ** (1 / 2.4) - 0.055)
    img = Image.fromarray((srgb * 255 + 0.5).astype(np.uint8))
    px_per_cm = 20.33 * 0.94                                     # rim scale at the far side of the box (rims converge 0.94)
    rep = [round(img.width / px_per_cm / 100, 3), round(img.height / px_per_cm / 100, 3)]   # stretched x2 above: pixels are isotropic now
    img.resize((512, round(512 * img.height / img.width)), Image.LANCZOS).save(ROOT / "spec/dressing/buzz_trunk_lining.png")
    return dict(png="spec/dressing/buzz_trunk_lining.png", repeat_m=rep, albedo_lin=[round(float(v), 3) for v in target])


# ---- placement and the adult passage
ROOM = next(r for r in json.loads((ROOT / "spec/geometry.json").read_text())["upstairs"]["rooms"] if r["name"] == "buzz_room")["poly"]
X0, X1 = min(p[0] for p in ROOM), max(p[0] for p in ROOM)
Z0, Z1 = min(p[1] for p in ROOM), max(p[1] for p in ROOM)
BED_SHIFT = 0.0              # the bed's -0.14 m in x is now in buzz.json itself (buzz_layout.py BED_SHIFT, changes/2026-10-18-buzz-bed.json)
R_ADULT = 0.275 + 0.02       # CharacterController radius + skin
WALL_PROUD = 0.03            # wainscot cap rail proud of the wall face
LID_BACK = 0.12              # the open lid stands behind the hinge by its own depth (~0.11 m) + 1 cm: clear of the chest's front


def boxes(trunk=None):
    B = json.loads((ROOT / "spec/dressing/buzz.json").read_text())["boxes"]
    out = []
    for b in B:
        if b["y"][0] > 1.8:
            continue
        x = list(b["x"])
        if b["name"].startswith("buzz_bed"):
            x = [x[0] + BED_SHIFT, x[1] + BED_SHIFT]
        out.append((b["name"], x, b["z"]))
    if trunk:
        out.append(("trunk", trunk["x"], trunk["z"]))
    return out


def passage(trunk, plot=None):
    """bottleneck width (m) of the best path for a body between the front-window pocket (between the bed and the front wall) and the
    room's open middle, and the door: 2 x the largest clearance radius at which they stay connected (1 cm grid)"""
    h = 0.01; xs = np.arange(X0, X1, h); zs = np.arange(Z0, Z1, h)
    occ = np.zeros((len(zs), len(xs)), bool)
    occ[:, xs < X0 + WALL_PROUD] = occ[:, xs > X1 - WALL_PROUD] = True
    occ[zs < Z0 + WALL_PROUD, :] = occ[zs > Z1 - WALL_PROUD, :] = True
    for _, x, z in boxes(trunk):
        occ[np.ix_((zs >= z[0]) & (zs <= z[1]), (xs >= x[0]) & (xs <= x[1]))] = True
    d = distance_transform_edt(~occ) * h
    ij = lambda x, z: (int((z - Z0) / h), int((x - X0) / h))
    A, Bm, D = ij(10.75, 12.85), ij(8.6, 14.4), ij(7.9, 12.0)   # pocket, open middle, inside the door
    def joined(r, p, q):
        lab, _ = label(d >= r); return lab[p] != 0 and lab[p] == lab[q]
    lo, hi = 0.0, 1.0
    for _ in range(30):
        m = (lo + hi) / 2
        if joined(m, A, Bm) and joined(m, A, D): lo = m
        else: hi = m
    if plot:
        import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(7, 8))
        ax.imshow(np.where(occ, np.nan, d), origin="lower", extent=[X0, X1, Z0, Z1], cmap="viridis")
        ax.contour(xs, zs, d, levels=[R_ADULT], colors="r", linewidths=1)
        for n, x, z in boxes(trunk):
            ax.add_patch(plt.Rectangle((x[0], z[0]), x[1] - x[0], z[1] - z[0], fill=False, ec="orange" if n == "trunk" else "w", lw=1.5 if n == "trunk" else .6))
        ax.set_title(f"Buzz: adult passage {2 * lo:.3f} m (needs {2 * R_ADULT:.2f}); red = body-centre limit\nbed shifted {BED_SHIFT} m in x (assumed), trunk orange")
        ax.set_xlabel("spec x (front wall right)"); ax.set_ylabel("spec z (desk wall top)")
        Path(plot).parent.mkdir(parents=True, exist_ok=True); fig.savefig(plot, dpi=110, bbox_inches="tight"); plt.close(fig)
    return 2 * lo


def place(L, D):
    """at the foot of the bed, back toward the footboard, long side along it, latches toward the room (user Oct 17: "put the trunk
    where it looks like it is from your movie stills or marina's overhead views ... the back is flush with the foot of the bed"):
    centred on the (shifted) bed, LID_BACK off the foot posts so the open lid clears the footboard. Props lane: placed by eye"""
    bed = [b for b in boxes() if b[0].startswith("buzz_bed")]
    bx0, bx1 = min(b[1][0] for b in bed), max(b[1][1] for b in bed); foot = max(b[2][1] for b in bed)
    cx = (bx0 + bx1) / 2; z0 = foot + LID_BACK
    t = dict(x=[round(cx - L / 2, 3), round(cx + L / 2, 3)], z=[round(z0, 3), round(z0 + D, 3)])
    chest = next(b for b in json.loads((ROOT / "spec/dressing/buzz.json").read_text())["boxes"] if b["name"] == "buzz_chest")
    return t, 0.0, chest


def main():
    S = size()
    print("size:", json.dumps(S))
    crops()
    lin = lining(); print("lining:", lin)
    L = 0.86                                                      # built outer length at the rim (both rulers' overlap)
    scan = json.loads(OUT.read_text())["scan"] if OUT.exists() and "scan" in json.loads(OUT.read_text()) else None
    D = scan["body_depth_m"] if scan else 0.51                    # the scan's body depth at L (purchased_trunk.py --probe writes it)
    t, shift, chest = place(L, D)
    if OUT.exists() and json.loads(OUT.read_text()).get("placement", "").startswith("PLACED BY THE USER"):   # keep the user's editor placement
        prev = json.loads(OUT.read_text()); t = dict(x=prev["x"], z=prev["z"])
    w0 = passage(None); w1 = passage(t, ROOT / "spec/captures/views/buzztrunk/passage.png")
    bed_x1 = max(b[1][1] for b in boxes() if b[0].startswith("buzz_bed"))
    bed_z1 = max(b[2][1] for b in boxes() if b[0].startswith("buzz_bed"))
    print(f"trunk x {t['x']} z {t['z']} (shifted {shift:+.3f} m along the wall from the chest's middle); passage {w0:.3f} m without it, {w1:.3f} with it (needs {2 * R_ADULT:.2f})")
    print(f"  gaps: bed side to chest {chest['x'][0] - bed_x1:.3f}, bed foot to trunk {t['z'][0] - bed_z1:.3f}, trunk back to chest {chest['x'][0] - t['x'][1]:.3f}")
    out = dict(note="Buzz's footlocker (TRIAL, changes/2026-10-17-buzz-trunk.json). Written by tools/house/buzz_trunk.py; the GLB by tools/house/purchased_trunk.py "
                    "(gitignored Assets/Purchased/Trunk/BuzzTrunk.glb, from the bought scan); placed by SpecGreybox.Trunk. Spec metres, y above the upper floor.",
               size=S, outer_length_m=L, x=t["x"], z=t["z"], front="+z", hinge="-z", yaw_deg=90, placement=json.loads(OUT.read_text()).get("placement", "foot of the bed (user)") if OUT.exists() else "foot of the bed (user)",
               passage_m=round(w1, 3), passage_without_m=round(w0, 3), bed_shift_assumed_m=BED_SHIFT, lining=lin)
    if scan:
        out["scan"] = scan
    OUT.write_text(json.dumps(out, indent=1) + "\n"); print("wrote", OUT)


if __name__ == "__main__":
    main()
