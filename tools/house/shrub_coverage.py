"""shrub_coverage: no shrub may be see-through or show a smooth core (user, Oct 20: "a big green ball in the center of the foliage";
then "smooth painted balls"). A deterministic check on the downloaded-boxwood shrubs (tools/house/scan_shrubs.py -> ScanShrubs.glb +
bux_albedo.png), not a look by eye.

For every foliage piece (a round shrub, a topiary ball, an urn's shrub) it casts N rays from points round it, 0.5-1.0 m outside it,
all the way round and from the ground plane up to 60 degrees above it, each aimed at a random point inside its middle half. A ray
passes a leaf card wherever the map's alpha is under the HDRP cutoff (0.45) at the hit's UV, and stops at the first opaque texel.
The piece FAILS when more than MAX_GAP of its rays pass right through (a hole to the far side: the bed or the wall shows through).

  uv run --with trimesh --with numpy --with pillow --with scipy --with rtree python -I tools/house/shrub_coverage.py [DIR] [--rays N]
  (DIR: the ScanShrubs folder; default unity/HomeAlone/Assets/Purchased/Sketchfab/ScanShrubs, gitignored: absent = skipped, exit 0)
  --selftest: the same piece with its map fully transparent must FAIL, the real one must pass
Exit 1 on a failing piece.
"""
import re
import sys
from pathlib import Path

import numpy as np
import trimesh
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
MAX_GAP, CUT = 0.02, 0.45
args = [a for a in sys.argv[1:] if not a.startswith("--") and not a.isdigit()]
DIR = Path(args[0]) if args else ROOT / "unity/HomeAlone/Assets/Purchased/Sketchfab/ScanShrubs"
NR = int(sys.argv[sys.argv.index("--rays") + 1]) if "--rays" in sys.argv else 300
PIECE = re.compile(r"^(P\d+_[a-z]+_(?:leaf|ball\d)_scan)(?:_[0-9a-f]+)?$")   # trimesh suffixes a node per primitive (leaves, snow cards)


def pieces(scene):
    parts = {}
    for node in scene.graph.nodes_geometry:
        mt = PIECE.match(node)
        if not mt: continue
        T, g = scene.graph[node]
        parts.setdefault(mt.group(1), []).append(scene.geometry[g].copy().apply_transform(T))
    return {k: (trimesh.util.concatenate(v), np.concatenate([m.visual.uv for m in v])) for k, v in parts.items()}


def gap_fraction(mesh, uvs, alpha, rng, nr=NR):
    h, w = alpha.shape
    c = mesh.bounds.mean(0); ce = (mesh.bounds[1] - mesh.bounds[0]) / 2
    R = np.max(ce)
    az = rng.uniform(0, 2 * np.pi, nr); el = np.radians(rng.uniform(0, 60, nr)); d = R + rng.uniform(0.5, 1.0, nr)
    eye = c + np.stack([np.cos(az) * np.cos(el) * d, np.sin(el) * d, np.sin(az) * np.cos(el) * d], 1)   # glTF is y-up
    tgt = c + rng.uniform(-0.5, 0.5, (nr, 3)) * ce
    dirs = tgt - eye; dirs /= np.linalg.norm(dirs, axis=1, keepdims=True)
    loc, ir, it = mesh.ray.intersects_location(eye, dirs, multiple_hits=True)
    through = 0
    for r in range(nr):
        sel = np.where(ir == r)[0]
        hit = False
        for k in sel[np.argsort(np.linalg.norm(loc[sel] - eye[r], axis=1))]:
            f = it[k]; bc = trimesh.triangles.points_to_barycentric(mesh.triangles[f][None], loc[k][None])[0]
            u, v = np.clip(bc @ uvs[mesh.faces[f]], 0, 1)
            if alpha[min(h - 1, int(v * h)), min(w - 1, int(u * w))] >= CUT: hit = True; break   # glTF UVs: v down the image
        through += not hit
    return through / nr


def main():
    glb = DIR / "ScanShrubs.glb"
    if not glb.exists():
        print(f"Shrub coverage: skipped ({glb} not present: the generated shrubs are in use)"); return
    alpha = np.asarray(Image.open(DIR / "bux_albedo.png").convert("RGBA"))[..., 3].astype(np.float32) / 255
    rng = np.random.default_rng(7)
    pc = pieces(trimesh.load(glb))
    if "--selftest" in sys.argv:
        name = sorted(pc)[0]; m, uv = pc[name]
        bare = gap_fraction(m, uv, np.zeros_like(alpha), rng); full = gap_fraction(m, uv, alpha, rng)
        ok = bare > 0.9 and full <= MAX_GAP
        print(f"selftest {name}: transparent map {bare:.3f} through (must be > 0.9), real {full:.3f} (must be <= {MAX_GAP}) -> {'ok' if ok else 'FAIL'}")
        sys.exit(0 if ok else 1)
    bad = 0; worst = (0, "")
    for name in sorted(pc, key=lambda s: int(s[1:].split("_")[0])):
        f = gap_fraction(*pc[name], alpha, rng)
        worst = max(worst, (f, name))
        if f > MAX_GAP: bad += 1; print(f"FAIL {name}: {f:.1%} of {NR} rays pass through")
    print(f"Shrub coverage: {len(pc)} foliage pieces, {bad} see-through on more than {MAX_GAP:.0%} of rays from 0.5-1.0 m (worst {worst[1]} {worst[0]:.1%}); {glb}")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
