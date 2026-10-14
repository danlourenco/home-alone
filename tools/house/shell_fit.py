"""Can the downloaded model's exterior (the September GLB) wrap the grey-box interior? Fits the grey-box footprint into
the GLB's exterior footprint, floor by floor, and reports where they disagree.

GLB footprint: a horizontal section above the door heads (sept_census raster), flood-filled from outside; everything not
reached is the building, walls included. Grey-box footprint: the union of the spec's spaces, plus the 14 cm walls.
The two are put in one frame by the plan mapping found in the September census (GLB X = c - spec z, GLB Y = d - spec x),
then c, d (and optionally a uniform scale) are fitted on the GROUND floor only, so the upper floor is a held-out test.
Output: overlap, grey-box area outside the shell (pokes through), shell area not covered (gaps), per floor; a map at
spec/captures/shell-fit.png.
usage: uv run --with numpy --with scipy --with matplotlib python -I tools/house/shell_fit.py
"""
import json
import sys
from pathlib import Path

import numpy as np
from scipy import ndimage, optimize

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/house"))
import sept_census as sc  # noqa: E402

RES = sc.RES


def glb_footprint(floor):
    wall, lo = sc.raster(floor)
    wall = ndimage.binary_dilation(wall, iterations=3)          # seal small gaps (windows cut low, door frames)
    outside = ndimage.label(~wall)[0]
    out = outside == outside[0, 0]
    return ~out, lo


def spec_polys(floor):
    p = ROOT / ("spec/house_spec.json" if floor == "upstairs" else "spec/house_spec.ground.json")
    return [np.array(s["polygon_xz"], float) for s in json.loads(p.read_text())["spaces"]]


def to_glb(P, c, d, s):
    """spec (x, z) -> GLB plan metres (X, Y)."""
    return np.stack([c - s * P[:, 1], d - s * P[:, 0]], 1)


def mask(polys, shape, lo, grow=0.07):
    from matplotlib.path import Path as MPath
    gx = lo[0] + np.arange(shape[0]) * RES
    gy = lo[1] + np.arange(shape[1]) * RES
    X, Y = np.meshgrid(gx, gy, indexing="ij")
    pts = np.stack([X.ravel(), Y.ravel()], 1)
    m = np.zeros(len(pts), bool)
    for P in polys:
        m |= MPath(P).contains_points(pts)
    m = m.reshape(shape)
    return ndimage.binary_dilation(m, iterations=int(round(grow / RES)))


def score(params, floor, shell, lo, scale_free):
    c, d = params[:2]; s = params[2] if scale_free else 1.0
    g = mask([to_glb(P, c, d, s) for P in spec_polys(floor)], shell.shape, lo)
    return g, (g & shell).sum() / (g | shell).sum()


def main():
    scale_free = "--scale" in sys.argv
    shell_g, lo_g = glb_footprint("ground")
    x0 = [10.2 + 0.704, 4.0 + 4.578] + ([1.0] if scale_free else [])
    best = optimize.minimize(lambda p: -score(p, "ground", shell_g, lo_g, scale_free)[1], x0, method="Nelder-Mead",
                             options={"xatol": 0.01, "fatol": 1e-4, "initial_simplex": None})
    p = best.x
    print(f"fit on the ground floor: c={p[0]:.2f} d={p[1]:.2f}" + (f" scale={p[2]:.3f}" if scale_free else " (scale 1, both at 80 in doors)"))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(24, 11))
    for ax, floor in zip(axes, ("ground", "upstairs")):
        shell, lo = (shell_g, lo_g) if floor == "ground" else glb_footprint("upstairs")
        g, iou = score(p, floor, shell, lo, scale_free)
        a = RES * RES
        poke, gap = (g & ~shell).sum() * a, (shell & ~g).sum() * a
        print(f"{floor:<9} overlap (IoU) {iou:.2f}; grey-box outside the shell {poke:5.1f} m2; shell not filled {gap:5.1f} m2;"
              f" grey-box {g.sum() * a:5.1f} m2, shell {shell.sum() * a:5.1f} m2")
        img = np.zeros(shell.shape + (3,))
        img[shell & g] = (0.75, 0.75, 0.75); img[g & ~shell] = (0.85, 0.2, 0.2); img[shell & ~g] = (0.2, 0.4, 0.85)
        ext = (lo[0], lo[0] + shell.shape[0] * RES, lo[1], lo[1] + shell.shape[1] * RES)
        ax.imshow(img.transpose(1, 0, 2), origin="lower", extent=ext)
        ax.set_title(f"{floor}: grey = both, RED = grey-box pokes outside the September shell, BLUE = shell with no grey-box room")
        ax.grid(True, lw=0.3)
    out = ROOT / "spec/captures/shell-fit.png"
    fig.savefig(out, dpi=55, bbox_inches="tight"); print(f"map -> {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
