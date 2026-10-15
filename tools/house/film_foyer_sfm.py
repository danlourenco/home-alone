"""Film-only 3D reconstruction of the foyer (tasks/wall-grid-plan.md phase 4; user Oct 15: 'go').
Picks frames from the foyer film index (art/home_alone/references/foyer-film/film-index.json): every run rated 3+ that
shows the architecture, up to 3 frames spread through a moving shot, 1 from a locked-off one; one folder (one camera,
its own lens) per run. Then tools/sfm/solve.sh with exhaustive matching. People move between shots and are outliers to
RANSAC; the walls, stair and doors are the static scene.
usage: uv run python -I tools/house/film_foyer_sfm.py   (writes sfm-work/film-foyer/images, then runs the solve)
"""
import json
import os
import sys
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WS = ROOT / "sfm-work/film-foyer"
# --back: only the shots that look toward the BACK of the foyer (stair, arch, picture wall). With every direction mixed,
# the repeating damask wallpaper folded the front wall onto the picture wall (Oct 15: all 92 cameras solved facing one way)
BACK_RUNS = {1612, 1687, 3170, 3199, 10671, 2675, 3886, 18, 770, 809, 822, 10684, 10705, 382, 11964, 12132, 1237, 1693, 10686, 10721}
SKIP = ("medium", "shot-reverse", "close")      # people-framed shots: little architecture


def pick():
    runs = json.loads((ROOT / "art/home_alone/references/foyer-film/film-index.json").read_text())
    runs = runs if isinstance(runs, list) else runs["runs"]
    out = {}
    for r in runs:
        if r["measure_value"] < 3 or any(k in r["camera"].lower() for k in SKIP):
            continue
        if "--back" in sys.argv and r["first"] not in BACK_RUNS:
            continue
        a, b = r["first"], r["last"]
        n = 1 if r["static"] else min(3, b - a + 1)
        out[f"{a:05d}-{b:05d}"] = sorted({a + round(i * (b - a) / max(n - 1, 1)) for i in range(n)})
    return out


if __name__ == "__main__":
    if "--back" in sys.argv:
        WS = ROOT / "sfm-work/film-foyer-back"
    sel = pick()
    if WS.exists():
        shutil.rmtree(WS)
    for run, frames in sel.items():
        d = WS / "images" / run; d.mkdir(parents=True)
        for f in frames:
            shutil.copy(ROOT / f"0-homealone/full/homealone-movie-screencaps.com-{f}.jpg", d / f"{f:05d}.jpg")
    print(f"{len(sel)} shots, {sum(len(v) for v in sel.values())} frames -> {WS.relative_to(ROOT)}/images")
    env = dict(os.environ, SFM_PER_FOLDER="1", SFM_EXHAUSTIVE="1")
    subprocess.run(["sh", str(ROOT / "tools/sfm/solve.sh"), str(WS)], check=True, env=env)
