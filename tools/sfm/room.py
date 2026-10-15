"""Per-room measurement recipe (docs/RECONCILIATION.md, step 1). Workspace: sfm-work/rooms/<name>/.

  prepare <name> <video> <start_s> <end_s>   extract 4 fps frames + indexed contact sheet (pick clean CG stretches)
  solve   <name> <a-b,c-d,...>               kept frame ranges, one per continuous shot: COLMAP (camera per shot),
                                             VGGT one pass (<=60 frames), agreement gate, room shape from both,
                                             indexed sheet of VGGT frames for door picking
  analyze <name>                             re-run gate/shape/report on an existing solve
  scale   <name> <idx:x:ytop:ybot> ...       door edges in VGGT frames -> metres at 78/80/84 in; appends report.md

Run with: uv run --with numpy --with pillow python tools/sfm/room.py ...  (from the repo root)
"""
import re
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
VENV_PY = ROOT / "sfm-work/.venv/bin/python"


def ws(name):
    return ROOT / "sfm-work/rooms" / name


def run(cmd, log=None, env=None):
    print("$", " ".join(map(str, cmd)))
    out = subprocess.run(list(map(str, cmd)), cwd=ROOT, capture_output=True, text=True, env=env)
    if log:
        Path(log).write_text(out.stdout + out.stderr)
    if out.returncode:
        sys.exit(f"failed ({out.returncode}): {(out.stdout + out.stderr)[-800:]}")
    return out.stdout


def sheet(paths_or_arrays, out, cols=8, width=320):
    tiles = []
    for i, p in enumerate(paths_or_arrays):
        im = Image.open(p) if isinstance(p, Path) else Image.fromarray(p)
        im = im.convert("RGB").resize((width, int(width * im.height / im.width)))
        ImageDraw.Draw(im).text((4, 4), str(i if not isinstance(p, Path) else int(p.stem[2:])), fill="yellow")
        tiles.append(im)
    w, h = tiles[0].size
    s = Image.new("RGB", (cols * w, -(-len(tiles) // cols) * h))
    for i, t in enumerate(tiles):
        s.paste(t, ((i % cols) * w, (i // cols) * h))
    s.save(out)
    print("sheet:", out)


def prepare(name, video, start, end):
    w = ws(name)
    run([ROOT / "tools/sfm/extract.sh", video, start, end, w / "all"])
    frames = sorted((w / "all/images").glob("f_*.jpg"))
    sheet(frames[::4], w / "contact.jpg")  # every 4th frame (1 s); label = frame number


def solve(name, ranges):
    w = ws(name)
    shots = [tuple(map(int, r.split("-"))) for r in ranges.split(",")]
    for sub in ("colmap", "vggt"):
        shutil.rmtree(w / sub, ignore_errors=True)
    kept = []
    for k, (a, b) in enumerate(shots):
        d = w / f"colmap/images/shot{k:02d}"
        d.mkdir(parents=True)
        for i in range(a, b + 1):
            src = w / f"all/images/f_{i:05d}.jpg"
            if src.exists():
                shutil.copy(src, d / src.name)
                kept.append(src)
    (w / "kept.txt").write_text(ranges + "\n")
    # VGGT sees the whole room in one pass (chunks only see slices of a pan).
    pick = [kept[i] for i in np.linspace(0, len(kept) - 1, min(60, len(kept))).round().astype(int)]
    (w / "vggt/images/shot00").mkdir(parents=True)
    for p in pick:
        shutil.copy(p, w / "vggt/images/shot00" / p.name)

    env = {**__import__("os").environ, "SFM_PER_FOLDER": "1", "SFM_CAMERA": "SIMPLE_PINHOLE"}
    run([ROOT / "tools/sfm/solve.sh", w / "colmap"], log=w / "colmap/solve.log", env=env)
    run([VENV_PY, ROOT / "tools/sfm/vggt_solve.py", w / "vggt", "60"], log=w / "vggt/solve.log")
    analyze(name)


def analyze(name):
    """Agreement gate, room shape from both methods, VGGT door-picking sheet, report.md (re-runnable)."""
    w = ws(name)
    ranges = (w / "kept.txt").read_text().strip()

    uv = ["uv", "run", "-q", "--with", "numpy", "--with", "matplotlib", "python"]
    env = {**__import__("os").environ, "PYTHONPATH": str(ROOT / "tools/sfm")}
    # camera-path consistency gates promotion: an inconsistent pair stops here unless --force (Oct 15 review, item 1)
    import subprocess as _sp
    res = _sp.run(list(map(str, uv + [ROOT / "tools/sfm/agreement.py", "2", f"colmap={w / 'colmap'}", f"vggt={w / 'vggt'}"])),
                  cwd=ROOT, capture_output=True, text=True, env=env)
    agree = res.stdout + res.stderr
    if res.returncode and "--force" not in sys.argv:
        sys.exit(f"camera paths inconsistent: not promoted (rerun with --force to inspect anyway)\n{agree[-800:]}")
    for m in (w / "colmap/sparse").iterdir():
        (m / "txt").mkdir(exist_ok=True)
        run(["colmap", "model_converter", "--input_path", m, "--output_path", m / "txt", "--output_type", "TXT"])
    # Largest COLMAP model holds the room.
    best = max((w / "colmap/sparse").iterdir(), key=lambda m: (m / "txt/images.txt").read_text().count(".jpg"))
    dims = run(uv + [ROOT / "tools/sfm/room_dims.py", w / "dims.png",
                     f"colmap={best}:shot", f"vggt={w / 'vggt/sparse/0'}"], env=env)
    d = np.load(w / "vggt/sparse/0/pixels.npz")
    sheet(list(d["images"]), w / "vggt-frames.jpg", cols=6, width=518)
    (w / "report.md").write_text(f"# {name}\n\nKept frame ranges (4 fps): {ranges}\n\n"
                                 f"## Camera-path consistency (COLMAP vs VGGT, 2%; paths only, NOT room accuracy)\n```\n{agree.strip()}\n```\n\n"
                                 "Not accepted as geometry until held-out geometric checks pass (wall ratios, corners, door offsets in other views).\n\n"
                                 f"## Shape (dims.png)\n```\n{dims.strip()}\n```\n")
    print(agree.splitlines()[-1]); print(dims)


def scale(name, specs):
    w = ws(name)
    dims = (w / "report.md").read_text()
    m = re.search(r"^vggt\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)", dims, re.M)
    if not m:
        sys.exit("VGGT room shape incomplete; fix the solve before scaling")
    out = run([VENV_PY, ROOT / "tools/sfm/door_scale.py", w / "vggt/sparse/0", m[1], m[2], w / "door-measure.jpg", *specs])
    with open(w / "report.md", "a") as f:
        f.write(f"\n## Scale from door (door-measure.jpg; ceiling line unreliable, ignore)\n"
                f"Door picks: {' '.join(specs)}\n```\n{out.strip()}\n```\n")
    print(out)


if __name__ == "__main__":
    cmd, name, *rest = sys.argv[1:]
    {"prepare": lambda: prepare(name, *rest), "solve": lambda: solve(name, rest[0]), "analyze": lambda: analyze(name),
     "scale": lambda: scale(name, rest)}[cmd]()
