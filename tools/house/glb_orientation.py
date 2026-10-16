"""glb_orientation: every closed part of the generated models must face outward with every face wound the same way (an
inside-out part, or one flipped cap, draws far faces that z-fight whatever they touch; Oct 16). Exits 1 on any failure.

  uv run --with trimesh --with numpy --with scipy --with networkx python -I tools/house/glb_orientation.py [files...]
"""
import sys
from pathlib import Path

import trimesh

ROOT = Path(__file__).resolve().parents[2]
files = sys.argv[1:] or sorted(str(p) for p in (ROOT / "unity/HomeAlone/Assets/Models/Foyer").glob("*.glb") if p.name != "Tree.glb")
bad = 0
for f in files:
    for name, g in trimesh.load(f, force="scene").geometry.items():
        g = g.copy(); g.merge_vertices(merge_tex=True, merge_norm=True)
        parts = [p for p in g.split(only_watertight=False) if p.is_watertight]
        inward = sum(p.volume < 0 for p in parts); mixed = sum(not p.is_winding_consistent for p in parts); bad += inward + mixed
        print(f"{'FAIL' if inward or mixed else 'ok  '} {Path(f).name}:{name}: {len(parts)} closed parts, {inward} inward, {mixed} with flipped faces")
sys.exit(1 if bad else 0)
