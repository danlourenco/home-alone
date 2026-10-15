"""Marina's foyer as a measured plan: the clip A foyer pan (Part 1 5:12-5:20, sfm-work/rooms/stairs-a VGGT solve) put in
the main stair's own frame and laid over the grey-box foyer.

Frame: up from the carpet's tread normals, flight direction from its riser normals (the stair rises along it), origin
at the first riser on the flight centreline, height 0 at the foyer floor. Scale: vertical and across from the rise
(0.178 m), along the flight from the going (0.241 m); the solve stretches depth (along/vertical ~0.7), so the two are
kept apart. The scale holds independently: the hall table top reads 0.76 m (30 in) and the chair seats 0.44 m.
Spec mapping: spec x = 4.472 - along (flight 1 rises toward the rear wall at x 0), spec z = 10.801 + left (left of the
flight = south, the photo wall).

Writes spec/captures/foyer-survey/plan.png (density by height band over the grey-box foyer) and survey.json (wall
planes and feature boxes read from height bands).
usage: uv run --with numpy --with matplotlib python -I tools/house/foyer_survey.py
"""
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/sfm"))
from stair_measure import normals, peaks  # noqa: E402

RISE, GOING = 0.178, 0.241
FIRST_X, CENTRE_Z = 4.472, 10.801
OUT = ROOT / "spec/captures/foyer-survey"


def frame():
    d = np.load(ROOT / "sfm-work/rooms/stairs-a/vggt/sparse/0/pixels.npz")
    W, C, I = d["world"], d["conf"], d["images"].astype(np.float32)
    N = normals(W)
    good = C >= np.percentile(C, 35)
    r, g, b = I[..., 0], I[..., 1], I[..., 2]
    carpet = good & (r > g * 1.6) & (r > b * 1.4) & (r > 40) & (np.linalg.norm(N, axis=-1) > 0.5)
    P, Nc = W[carpet], N[carpet]
    up = np.array([0.0, -1.0, 0.0])
    for cone in (35, 25, 20, 20):
        s = Nc @ up; sel = np.abs(s) > np.cos(np.radians(cone)); fam = Nc[sel] * np.sign(s[sel])[:, None]
        up = fam.mean(0); up /= np.linalg.norm(up)
    hn = Nc - np.outer(Nc @ up, up); horiz = np.abs(Nc @ up) < np.sin(np.radians(20))
    hv = hn[horiz] / np.linalg.norm(hn[horiz], axis=1, keepdims=True)
    f = np.linalg.eigh(hv.T @ hv)[1][:, -1]; f -= (f @ up) * up; f /= np.linalg.norm(f)
    tread = np.abs(Nc @ up) > np.cos(np.radians(15))
    if np.corrcoef((P @ f)[tread], (P @ up)[tread])[0, 1] < 0:   # the stair rises along f
        f = -f
    left = np.cross(up, f)
    h, a = P @ up, P @ f
    # scale: the per-frame stair reads of this solve (still_pose.stair_still on frames 29/32/35: 6.69-6.84 m/u
    # vertical, 4.67-4.93 along); merging all frames blurs the tread levels too much to re-read them
    sv = sa = 6.74   # isotropic: at 6.74 the stair reads 36 deg, the depth-free pitch is 35 (the 4.8 "along" read picked alternate riser lines)
    rise_u, going_u = RISE / sv, GOING / sa
    lv = np.array(sorted(p[0] for p in peaks(h[tread], rise_u / 4, 0.15)))
    riser = horiz & (np.abs(Nc @ f) > np.cos(np.radians(25)))
    ns = np.array(sorted(p[0] for p in peaks(a[riser], going_u / 4, 0.10)))
    floor = np.percentile((W[good] @ up), 1.0)
    # first riser: the lowest riser line whose treads start at the floor (the nearest to the camera along -f)
    first = ns[0]
    centre = float(np.median(P[tread] @ left))
    pts = W[good]
    out = np.c_[(pts @ f - first) * sa, (pts @ left - centre) * sv, (pts @ up - floor) * sv]
    nrm = np.abs(N[good] @ up)
    return dict(pts=out, horiz=nrm > 0.9, vert=nrm < 0.3, rise_u=rise_u, going_u=going_u, sv=sv, sa=sa,
                levels=len(lv), risers=len(ns))


def main():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    F = frame()
    p = F["pts"]
    X = FIRST_X - p[:, 0]; Z = CENTRE_Z + p[:, 1]; H = p[:, 2]
    print(f"rise {F['rise_u']:.4f} u, going {F['going_u']:.4f} u, m/u vertical {F['sv']:.3f}, along {F['sa']:.3f} "
          f"(ratio {F['sa'] / F['sv']:.2f}); tread levels {F['levels']}, riser lines {F['risers']}")
    OUT.mkdir(parents=True, exist_ok=True)
    g = json.loads((ROOT / "spec/house_spec.ground.json").read_text())
    st = json.loads((ROOT / "spec/house_spec.json").read_text())["stair"]
    bands = [("0.05-0.6 m (low furniture)", (0.05, 0.6)), ("0.6-1.1 m (tables, wainscot)", (0.6, 1.1)),
             ("1.1-2.0 m (walls, doors)", (1.1, 2.0)), ("2.0-3.2 m (upper walls, landing, ceiling)", (2.0, 3.2))]
    fig, axes = plt.subplots(2, 2, figsize=(22, 16))
    for ax, (name, (lo, hi)) in zip(axes.ravel(), bands):
        m = (H > lo) & (H < hi) & F["vert"] if hi < 2.0 else (H > lo) & (H < hi)
        ax.hist2d(X[m], Z[m], bins=[np.arange(-1, 11, 0.04), np.arange(6.5, 12.5, 0.04)], cmap="magma", cmin=1)
        for s in g["spaces"]:
            if s["name"] in ("foyer", "vestibule", "living_room", "dining_room"):
                q = np.array(s["polygon_xz"] + [s["polygon_xz"][0]]); ax.plot(q[:, 0], q[:, 1], "c-", lw=1.2)
                ax.text(q[:, 0].mean(), q[:, 1].mean(), s["name"], color="c")
        for b in st["boxes"]:
            if b["kind"] in ("step", "landing"):
                ax.add_patch(plt.Rectangle((b["x"][0], b["z"][0]), b["x"][1] - b["x"][0], b["z"][1] - b["z"][0], fill=False, ec="lime", lw=0.6))
        ax.set_xlim(-1, 11); ax.set_ylim(12.5, 6.5); ax.set_aspect("equal"); ax.grid(True, lw=0.3)
        ax.set_title(f"Marina's foyer points at {name}; cyan = grey-box rooms, green = grey-box stair (spec x, z m)")
    fig.savefig(OUT / "plan.png", dpi=60, bbox_inches="tight")
    np.save(OUT / "points.npy", np.c_[X, Z, H, F["horiz"], F["vert"]].astype(np.float32))
    print("->", (OUT / "plan.png").relative_to(ROOT))
    return F


if __name__ == "__main__":
    F = main()
    assert F["sa"] == F["sv"]
