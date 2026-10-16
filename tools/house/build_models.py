"""build_models: rebuild every generated model whose sources changed, deterministically (Oct 16: a model was left stale
after its script changed, and a build then checked the wrong stair).

Each model lists the files that produce it. A stamp (Assets/Models/Foyer/stamps.json) records a hash of those files and of
the model. `--check` (run by the pre-commit hook) fails when a source changed since the model was built, or the model was
edited by hand; the default run rebuilds what is stale in Blender, runs glb_orientation.py on it and rewrites the stamps.

  python3 tools/house/build_models.py            # rebuild stale models
  python3 tools/house/build_models.py --check    # exit 1 if any model is stale
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODELS = ROOT / "unity/HomeAlone/Assets/Models/Foyer"
STAMPS = MODELS / "stamps.json"
BLENDER = "/Applications/Blender.app/Contents/MacOS/Blender"
LIB = "tools/house/hifi_lib.py"
# script -> (models it writes, data files it reads); Poly Haven downloads (sfm-work/, untracked) are not hashed
BUILDS = {
    "tools/house/hifi_foyer.py": (["MainStair.glb"], [LIB, "spec/house_spec.json", "spec/dressing/foyer.json"]),
    "tools/house/hifi_lights.py": (["Lantern.glb", "Sconce.glb", "Hurricane.glb", "Dome.glb"], [LIB]),
    "tools/house/hifi_props.py": (["Tree.glb"], ["spec/dressing/foyer.json"]),
    "tools/house/hifi_door.py": (["FrontDoor.glb"], [LIB]),
    "tools/house/hifi_dressing.py": (["FoyerDressing.glb"], [LIB, "spec/dressing/foyer.json"]),
    "tools/house/hifi_landing_window.py": (["LandingWindow.glb"], [LIB, "spec/house_spec.ground.json"]),
}


def digest(paths):
    h = hashlib.sha256()
    for p in paths:
        h.update(p.encode()); h.update((ROOT / p).read_bytes() if (ROOT / p).exists() else b"missing")   # a new model is stale until built
    return h.hexdigest()[:16]


def stamp_of(script):
    outs, deps = BUILDS[script]
    return {"sources": digest([script] + deps), "models": digest([str((MODELS / o).relative_to(ROOT)) for o in outs])}


def stale(stamps):
    return [s for s in BUILDS if stamps.get(s) != stamp_of(s)]


stamps = json.loads(STAMPS.read_text()) if STAMPS.exists() else {}
todo = stale(stamps)
if "--check" in sys.argv:
    for s in todo:
        print(f"stale model: {', '.join(BUILDS[s][0])} (from {s}); run python3 tools/house/build_models.py")
    sys.exit(1 if todo else 0)
for s in todo:
    print("building", s)
    before = {o: (MODELS / o).stat().st_mtime if (MODELS / o).exists() else 0 for o in BUILDS[s][0]}
    run = subprocess.run([BLENDER, "-b", "--factory-startup", "-P", str(ROOT / s)], capture_output=True, text=True)
    if any(not (MODELS / o).exists() or (MODELS / o).stat().st_mtime == before[o] for o in BUILDS[s][0]):   # Blender exits 0 on a script error
        sys.exit(f"{s} did not write its models:\n" + "\n".join((run.stdout + run.stderr).splitlines()[-15:]))
    if s != "tools/house/hifi_props.py":   # Poly Haven models are not ours to orient
        subprocess.run(["uv", "run", "-q", "--with", "trimesh", "--with", "numpy", "--with", "scipy", "--with", "networkx",
                        "python", "-I", str(ROOT / "tools/house/glb_orientation.py")] + [str(MODELS / o) for o in BUILDS[s][0]], check=True)
    stamps[s] = stamp_of(s)
STAMPS.write_text(json.dumps(stamps, indent=1, sort_keys=True) + "\n")
print("up to date" if not todo else f"rebuilt {len(todo)}")
