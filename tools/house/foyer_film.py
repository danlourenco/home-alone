"""The back of the foyer from the FILM (tasks/wall-grid-plan.md phase 4; user Oct 15: film over Marina here).

Film 1616, 10673 and 3175 (0-homealone/full) show the picture wall nearly face-on: a cased round-topped arch at its left
leads to the rear door; a low flat ceiling (soffit) runs along its top; its right end meets the north wall. Every number
below is read in that one wall plane, where the pixel scale is the same up and across, so these RATIOS need no ruler:
    wainscot / soffit height,  picture-wall length (arch casing to corner) / soffit height.
Turning them into metres needs one ruler; the candidates disagree and are printed side by side (never averaged).
Readings are full-resolution pixels (1920 x 1058), +-4 px, from gridded crops.
usage: uv run python -I tools/house/foyer_film.py
"""
FRAMES = {   # y floor (baseboard bottom), y soffit (top of the wallpaper), y wainscot top, x arch casing (outer), x corner
    1616:  {"floor": 772, "soffit": 272, "wainscot": 598, "arch": 1162, "corner": 1372},
    10673: {"floor": 640, "soffit": 215, "wainscot": 500, "arch": 1432, "corner": 1620},
    3175:  {"floor": 1037, "soffit": 432, "wainscot": 820, "arch": 1400, "corner": 1653},
}
# Rulers for the soffit height H (metres). Each has its own assumption.
WAINSCOT_MARINA = 0.705          # Marina 312 s, picture wall (foyer_length.py / dressing): H = wainscot / ratio
# 10673: the console top on the north wall reads flat at y ~500 = the horizon (a level line running away from the camera is
# flat only at eye height), and the wainscot top is at the same y, so wainscot = camera height. The rear door through the
# arch (80 in, a different depth) gives the camera height from its floor (y 613) and top (y ~280, partly behind the arch):
DOOR_10673 = {"horizon": 500, "door_floor": 613, "door_top": 280, "door_h": 2.032}
# 2677 and 3888 (near the dining opening): the arch and the rear door behind it, nearly face-on. In the arch's plane:
# floor, arch crown, springline, inner jambs, wainscot top, the ceiling line above; the door (80 in) a short passage behind.
ARCH = {
    3888: {"floor": 840, "crown": 179, "spring": 250, "left": 1322, "right": 1658, "wainscot": 625, "ceiling": 167,
           "door_top": 275, "door_floor": 821},
    2677: {"floor": 787, "crown": 117, "spring": 192, "left": 1283, "right": 1604, "wainscot": 557, "ceiling": 104,
           "door_top": 215, "door_floor": 738},
}
LANDING_FILM_THEN = (2.22, 2.57)  # film still then-foyer.png: landing underside 1.177 x the rear door head (film_ratios.py)


def ratios():
    out = {}
    for n, f in FRAMES.items():
        H = f["floor"] - f["soffit"]
        out[n] = {"wainscot": (f["floor"] - f["wainscot"]) / H, "wall": (f["corner"] - f["arch"]) / H}
    return out


def main():
    R = ratios()
    print("Scale-free, in the picture-wall plane (fractions of the soffit height H):")
    for n, r in R.items():
        print(f"  {n:>6}: wainscot {r['wainscot']:.3f} H   picture wall {r['wall']:.3f} H")
    w = [r["wainscot"] for r in R.values()]; p = [r["wall"] for r in R.values()]
    print(f"  spread: wainscot {min(w):.3f}-{max(w):.3f} H, picture wall {min(p):.3f}-{max(p):.3f} H")
    d = DOOR_10673; b_hc = d["door_floor"] - d["horizon"]; b_top = d["horizon"] - d["door_top"]
    hc = d["door_h"] * b_hc / (b_hc + b_top)                      # camera height from the door alone
    print("\nRulers for H (not averaged):")
    rows = [("Marina's wainscot 0.705 m", [WAINSCOT_MARINA / x for x in w]),
            (f"10673 rear door 80 in (camera height {hc:.2f} m = wainscot)", [hc / R[10673]["wainscot"]]),
            ("film still then-foyer.png: landing underside", list(LANDING_FILM_THEN))]
    for name, Hs in rows:
        lo, hi = min(Hs), max(Hs)
        print(f"  {name}: H {lo:.2f}-{hi:.2f} m ({lo / 0.3048:.1f}-{hi / 0.3048:.1f} ft) -> picture wall "
              f"{min(p) * lo:.2f}-{max(p) * hi:.2f} m")
    print("\nThe arch (2677, 3888), in its own plane (fractions of the ceiling height H over it):")
    for n, a in ARCH.items():
        H = a["floor"] - a["ceiling"]
        print(f"  {n}: crown {(a['floor'] - a['crown']) / H:.2f} H, springline {(a['floor'] - a['spring']) / H:.2f} H, "
              f"clear width {(a['right'] - a['left']) / H:.2f} H, wainscot {(a['floor'] - a['wainscot']) / H:.2f} H; "
              f"crown / door head (door a passage behind, so an upper bound on the true ratio) "
              f"{(a['floor'] - a['crown']) / (a['door_floor'] - a['door_top']):.2f}")
    print("  CONFLICT: at H ~2.1 m the crown (~2.06 m) barely clears the 2.03 m door, but the frames show ~1 ft of wall between")
    print("  them; door-vs-arch with a short passage gives a crown of ~2.4-2.6 m. Resolve with a vanishing-point camera solve")
    print("  of 2677 / 3888 (depth of the door behind the arch), not by choosing")
    return R


if __name__ == "__main__":
    R = main()
    assert all(0.3 < r["wainscot"] < 0.4 and 0.38 < r["wall"] < 0.48 for r in R.values())
