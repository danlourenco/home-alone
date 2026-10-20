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
    "tools/house/hifi_foyer.py": (["MainStair.glb"], [LIB, "spec/house_spec.json", "spec/dressing/foyer.json", "spec/geometry.json"]),   # geometry: the foyer ceiling the soffit meets
    "tools/house/hifi_lights.py": (["Lantern.glb", "Sconce.glb", "Hurricane.glb", "Dome.glb"], [LIB]),
    "tools/house/hifi_props.py": (["Tree.glb"], ["spec/dressing/foyer.json"]),
    "tools/house/hifi_front_leaf.py": (["FrontLeaf.glb"], [LIB, "tools/house/hifi_pipeline.py", "tools/house/front_leaf_finish.py"]),
    "tools/house/hifi_door.py": (["FrontDoor.glb"], [LIB]),
    "tools/house/hifi_dressing.py": (["FoyerDressing.glb"], [LIB, "spec/dressing/foyer.json"]),
    "tools/house/hifi_landing_window.py": (["LandingWindow.glb"], [LIB, "spec/house_spec.ground.json", "spec/openings.json"]),
    "tools/house/hifi_swing_door.py": (["SwingDoor.glb"], [LIB, "spec/geometry.json"]),
    "tools/house/hifi_back_door.py": (["BackDoor.glb"], [LIB, "spec/house_spec.ground.json"]),
    "tools/house/hifi_kitchen.py": (["KitchenCabinets.glb"], [LIB, "spec/dressing/kitchen.json"]),
    "tools/house/hifi_kitchen_lights.py": (["KitchenChandelier.glb", "KitchenSconces.glb"], [LIB, "spec/dressing/kitchen.json"]),
    "tools/house/hifi_kitchen_gallery.py": (["KitchenGallery.glb"], [LIB, "spec/dressing/kitchen.json"]),
    "tools/house/hifi_kitchen_props.py": (["KitchenProps.glb"], [LIB, "spec/dressing/kitchen.json"]),   # kitchen fidelity (Oct 19): pot rack, stools, counter dressing
    "tools/house/hifi_breakfast_table.py": (["BreakfastTable.glb"], [LIB, "spec/dressing/kitchen.json"]),
    "tools/house/hifi_sheers.py": (["Sheers.glb"], [LIB, "spec/house_spec.ground.json"]),
    "tools/house/hifi_den.py": (["DenWindows.glb", "DenBuiltins.glb"], [LIB, "spec/house_spec.ground.json", "spec/dressing/den.json", "spec/dressing/den_fabric.json", "spec/dressing/den_labels.json", "tools/house/den_textures.py"]),
    "tools/house/hifi_den_props.py": (["DenProps.glb"], ["spec/dressing/den.json"]),
    "tools/house/hifi_foyer_mirror.py": (["FoyerMirror.glb"], [LIB, "tools/house/hifi_pipeline.py", "spec/dressing/foyer_props.json"]),
    "tools/house/hifi_foyer_props.py": (["FoyerProps.glb"], [LIB, "spec/dressing/foyer_props.json", "spec/dressing/foyer_art.json", "spec/dressing/foyer_art.png", "spec/dressing/rug_runner.png", "spec/dressing/rug_front.png"]),
    "tools/house/hifi_paint_can.py": (["PaintCan.glb", "PaintCanSatin.glb"], [LIB]),
    "tools/house/hifi_parents_dressing.py": (["ParentsDressing.glb"], [LIB, "tools/house/hifi_sheers.py", "spec/dressing/parents.json", "spec/openings.json", "spec/geometry.json"]),
    "tools/house/hifi_buzz_curtains.py": (["BuzzCurtains.glb"], [LIB, "tools/house/hifi_sheers.py", "spec/dressing/buzz_curtains.json", "spec/dressing/buzz.json", "spec/openings.json", "spec/geometry.json"]),
    "tools/house/hifi_parents_fireplace.py": (["ParentsFireplace.glb"], [LIB, "tools/house/hifi_den_props.py", "spec/dressing/parents_fireplace.json"]),
    "tools/house/hifi_attic.py": (["Attic.glb"], [LIB, "spec/house_spec.json"]),
    "tools/house/hifi_kevin.py": (["KevinRoom.glb", "KevinArmchair.glb"], [LIB, "spec/dressing/kevin.json", "spec/openings.json", "tools/house/hifi_sheers.py"]),   # Kevin+Jeff TRIAL 1 (Oct 18)
    "tools/house/hifi_basement.py": (["Basement.glb"], [LIB, "spec/house_spec.ground.json"]),
    "tools/house/hifi_treehouse.py": (["Treehouse.glb"], [LIB, "spec/dressing/treehouse.json", "tools/house/hifi_bare_trees.py"]),
    "tools/house/hifi_bare_trees.py": (["BareTrees.glb"], ["spec/dressing/treehouse.json"]),   # bare winter trees (Oct 18, decoration)
    "tools/house/hifi_living.py": (["LivingWindows.glb", "LivingBuiltins.glb"], [LIB, "spec/house_spec.ground.json", "spec/dressing/living.json", "tools/house/hifi_sheers.py", "spec/exterior_shell.json"]),
    "tools/house/hifi_living_props.py": (["LivingProps.glb"], ["spec/dressing/living.json", "tools/house/hifi_den_props.py"]),
    "tools/house/hifi_dining_props.py": (["DiningProps.glb"], ["spec/dressing/dining.json", "tools/house/hifi_den_props.py"]),   # props lane (Oct 18 overnight)
    "tools/house/hifi_hall.py": (["HallDressing.glb"], [LIB, "spec/dressing/hall.json", "spec/dressing/hall_art.json", "spec/dressing/hall_art.png", "spec/geometry.json"]),
    "tools/house/hifi_hall_arches.py": (["HallArches.glb"], ["tools/house/hifi_pipeline.py", LIB, "spec/geometry.json", "spec/dressing/hall.json", "spec/dressing/finishes.json"]),
    "tools/house/hifi_french_doors.py": (["FrenchDoors.glb"], [LIB, "spec/dressing/french_doors.json", "spec/geometry.json"]),
    "tools/house/hifi_buzz_props.py": (["BuzzProps.glb"], [LIB, "tools/house/hifi_pipeline.py", "spec/dressing/buzz.json", "spec/dressing/buzz_props_can.png", "spec/dressing/buzz_props_jordan.png", "spec/dressing/buzz_props_playboy.png", "spec/dressing/buzz_props_girlfriend.png", "spec/dressing/buzz_props_chips.png"]),   # props lane (Oct 17 overnight)
    "tools/house/hifi_exterior.py": (["Exterior.glb"], [LIB, "tools/house/exterior_shell.py", "spec/geometry.json", "spec/house_spec.json", "spec/house_spec.ground.json"]),   # exterior shell TRIAL 1 (Oct 18)
    "tools/house/hifi_ext_plants.py": (["ExteriorPlants.glb"], ["spec/dressing/exterior_plants.json"]),   # exterior polish (Oct 18), decoration
    "tools/house/hifi_entrance.py": (["FrontEntrance.glb"], [LIB, "tools/house/hifi_pipeline.py", "spec/geometry.json"]),   # front entrance TRIAL 1 (Oct 19): leaf outside, brass, wreath bulbs, lantern
    "tools/house/hifi_door_lamps.py": (["DoorLamps.glb"], [LIB, "tools/house/hifi_pipeline.py", "spec/geometry.json", "spec/house_spec.ground.json"]),   # back-door lanterns TRIAL 1 (Oct 19, walk note 09:03)
    "tools/house/hifi_bathrooms.py": (["Bathrooms.glb", "BathroomProps.glb"], [LIB, "tools/house/hifi_sheers.py", "spec/dressing/bathrooms.json", "spec/geometry.json", "spec/openings.json"]),   # bathrooms TRIAL 1 (Oct 19)
    "tools/house/hifi_foyer_arch.py": (["FoyerArch.glb"], [LIB, "tools/house/hifi_pipeline.py", "spec/geometry.json", "spec/house_spec.json"]),   # artist pipeline (+ Textures/Generated/FoyerArch)
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
if "--only" in sys.argv:   # rebuild just these scripts' models (others' work in progress stays as it is): --only hifi_hall,hifi_foyer
    want = sys.argv[sys.argv.index("--only") + 1].split(",")
    todo = [s for s in todo if Path(s).stem in want]
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
    if s not in ("tools/house/hifi_props.py", "tools/house/hifi_den_props.py", "tools/house/hifi_living_props.py"):   # Poly Haven models are not ours to orient
        subprocess.run(["uv", "run", "-q", "--with", "trimesh", "--with", "numpy", "--with", "scipy", "--with", "networkx",
                        "python", "-I", str(ROOT / "tools/house/glb_orientation.py")] + [str(MODELS / o) for o in BUILDS[s][0]], check=True)
    stamps[s] = stamp_of(s)
STAMPS.write_text(json.dumps(stamps, indent=1, sort_keys=True) + "\n")
print("up to date" if not todo else f"rebuilt {len(todo)}")
