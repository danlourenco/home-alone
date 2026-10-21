#!/usr/bin/env bash
# unity_pipeline.sh: build, bake, load and capture House_WallGrid without touching the user's open editor until the load.
#
#   tools/house/unity_pipeline.sh setup      # (once) make the scratch build copy: ~/.cache/home-alone/ucopy/HomeAlone (+ spec link)
#   tools/house/unity_pipeline.sh preflight  # the cheap Python gates (verify_plan, change_gate, build_models/openings/trim_faces --check, model_quality);
#                                            # build runs it first and refuses to launch Unity on a FAIL (HA_NO_PREFLIGHT=1 skips it);
#                                            # HA_CHANGE=<changes/x.json>: that record's missing AFTER renders wait for this build (`build -views`)
#   tools/house/unity_pipeline.sh build [unity args]   # copy Editor/Scripts/Models/HDRP.asset in, build the scene (batch); gates -> spec/captures/walk-test-wallgrid.txt
#                                            # extra args go to Unity (e.g. -views trim-after.json: renders in the same session);
#                                            # HA_OVERLAY=<dir>: drafts (dir/Editor, dir/Models ...) copied over Assets/ after the repo's, so
#                                            # uncompiled C# or a model the open editor must not see yet never touches the repo
#   tools/house/unity_pipeline.sh bake       # bake day + night (WINDOWED: batch mode has no sky; BakeLighting refuses it)
#   tools/house/unity_pipeline.sh load       # copy scene + bake into the project, wait for import/compile, open, Play (bakes first if the build is unbaked)
#   tools/house/unity_pipeline.sh nightcheck # live: night shots at 3 room poses must reach a luminance floor (load runs it last)
#   tools/house/unity_pipeline.sh daycheck   # live: APV loaded + day saturation floor at 2 Buzz views (load runs it after nightcheck)
#   tools/house/unity_pipeline.sh all        # build, bake, load (stops at the first failure: every step exits non-zero on a FAIL)
# build and bake append one line to spec/captures/build-log.jsonl (time, cmd, job=$HA_JOB, why=$HA_WHY, wall_s, exit): rebuilds per job
#   tools/house/unity_pipeline.sh shot NAME x y z yaw pitch [day|night]     # live capture from a player pose (feet; eye +1.28)
#   tools/house/unity_pipeline.sh cam  NAME px py pz lx ly lz vfov near [day|night]   # live capture from a camera pose (look-at)
# Captures land in ~/.cache/home-alone/captures/NAME.png. They use a CLONE of the player camera in the user's running editor (batch
# renders are not reliable for lighting) and never move the player; day/night is switched for the shot and restored.
#
# Lessons built in (Oct 16 2026):
#  - captures had motion blur: the clone teleports from the player's pose and its warm-up renders share one frame, so HDRP sees a
#    huge camera move; motion blur is switched off on the capture camera only
#  - never enter Play mid-import/compile (a native crash): wait until isCompiling and isUpdating are both false
#  - a new Assets/Scripts/*.cs gets its own .meta GUID per project: create it in the repo project first; this script copies .cs AND .meta
#  - wait for the bake by its Unity process path, not a pattern that matches this shell
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
ROOT="${HA_SCRATCH:-$HOME/.cache/home-alone}"
S="$ROOT/ucopy/HomeAlone"
P="$REPO/unity/HomeAlone"
UNITY=/Applications/Unity/Hub/Editor/6000.6.0f1/Unity.app/Contents/MacOS/Unity
CLI="$HOME/.unity/bin/unity"
CAP="$ROOT/captures"; mkdir -p "$CAP"

ev() { (cd "$P" && "$CLI" command eval --code "$1" 2>&1 | grep -oE 'result":"[^"]*' | cut -c10-); }
idle() {   # the user's editor: not compiling, not importing
  for _ in $(seq 1 120); do
    [ "$(ev 'return UnityEditor.EditorApplication.isCompiling+" "+UnityEditor.EditorApplication.isUpdating;')" = "False False" ] && return 0; sleep 3
  done; echo "editor never went idle" >&2; return 1
}

CMD="${1:-}"; T0=$SECONDS
case "$CMD" in build|bake)   # one JSON line per build/bake, whatever its outcome (STATUS 8p j)
  trap 'e=$?; python3 -c "import json,sys,time; print(json.dumps({\"time\": time.strftime(\"%Y-%m-%dT%H:%M:%S\"), \"cmd\": sys.argv[1], \"job\": sys.argv[2], \"why\": sys.argv[3], \"wall_s\": int(sys.argv[4]), \"exit\": int(sys.argv[5])}))" "$CMD" "${HA_JOB:-}" "${HA_WHY:-}" $((SECONDS-T0)) $e >> "$REPO/spec/captures/build-log.jsonl"' EXIT;;
esac

case "$CMD" in
setup)
  mkdir -p "$ROOT/ucopy"; rsync -a --exclude Temp "$P/" "$S/"; ln -sfn "$REPO/spec" "$ROOT/spec"
  echo "scratch copy at $S (first open imports the Library: minutes)";;
preflight)   # cheap gates before any Unity launch (STATUS 8p f); runs them all, then fails if any failed
  cd "$REPO"; bad=0
  free_gb=$(df -g "$HOME" | awk 'NR==2{print $4}')   # Oct 18: a full disk broke a video encode and every tool call; builds + bakes need room
  if [ "${free_gb:-0}" -lt 15 ]; then echo "FAIL disk: only ${free_gb} GB free on the home volume (need 15)"; bad=1; else echo "ok   disk: ${free_gb} GB free"; fi
  for g in "python3 tools/house/build_models.py --check" "python3 tools/house/openings.py --check" "python3 tools/house/trim_faces.py --check" "python3 tools/house/stair_arrival.py" "uv run -q --with trimesh --with numpy python -I tools/house/rail_joints.py" "uv run -q --with trimesh --with numpy python -I tools/house/soffit_joints.py" \
           "uv run -q --with numpy --with matplotlib --with pillow python -I tools/house/verify_plan.py" \
           "uv run -q --with numpy --with pillow python -I tools/house/model_quality.py --report" "python3 tools/house/unity_practices.py" \
           "env HA_PREBUILD=1 uv run -q python -I tools/house/change_gate.py $(grep -L '"user_walk": "rejected"' changes/*.json | tr '\n' ' ')"; do
    n=$(echo "$g" | grep -oE '[a-z_]+\.py( --[a-z]+)?')
    if out=$($g 2>&1); then echo "ok   $n"; else echo "FAIL $n"; echo "$out" | grep -E '^[^ ].*\.json:|^ *FAIL|Error' | grep -B1 -E '^ *FAIL|Error' | cut -c1-160 | head -8 || true; bad=1; fi
  done
  python3 tools/house/props_yaw.py | sed 's/^/     /'   # informational: furniture still on a shape-guessed turn (pin after a front render)
  python3 tools/house/walk_notes.py | sed 's/^/     /' || true   # informational: walk notes with no disposition (docs/walk-notes-ledger.json)
  python3 tools/house/slow_jobs.py | sed 's/^/     /'   # informational: recurring slow work and builds since the last bake (never fails)
  [ $bad = 0 ] || { echo "preflight FAILED: Unity not launched (HA_NO_PREFLIGHT=1 to override)" >&2; exit 1; };;
build)
  python3 "$REPO/tools/house/openings.py"     # every opening's casing, header and limits (HOUSE-KERNEL step 2; refused if a limit breaks)
  python3 "$REPO/tools/house/trim_faces.py"   # the face model the trim is laid from (HOUSE-KERNEL step 1; the build refuses a stale one)
  [ "${HA_NO_PREFLIGHT:-}" = 1 ] || "$0" preflight
  rsync -a "$P/Assets/Editor/" "$S/Assets/Editor/"; rsync -a "$P/Assets/Scripts/" "$S/Assets/Scripts/"
  rsync -a "$P/Assets/Models/" "$S/Assets/Models/"; cp "$P/Assets/Settings/HDRP.asset" "$S/Assets/Settings/"
  rsync -a --exclude Greybox --exclude Greybox.meta "$P/Assets/Textures/" "$S/Assets/Textures/"   # generated + Poly Haven maps (kitchen); Greybox/ is the build's own
  for pk in "Fadnn - Vintage Interior Furniture Pack" "Classic Wooden Furniture Pack" "Free Wood Door Pack" "VTC_AV-2062s" "ChristmasTreeAndGarland" "Tarantula" "BankersLamp" "ZNS3D"; do   # Asset Store packs (gitignored; may be absent)
    [ -d "$P/Assets/$pk" ] && rsync -a "$P/Assets/$pk" "$P/Assets/$pk.meta" "$S/Assets/"; done
  [ -d "$P/Assets/Purchased" ] && rsync -a "$P/Assets/Purchased" "$S/Assets/" && { [ -f "$P/Assets/Purchased.meta" ] && cp "$P/Assets/Purchased.meta" "$S/Assets/" || true; }   # CGTrader buys (gitignored; may be absent: generated plants then)
  [ -n "${HA_OVERLAY:-}" ] && rsync -a "$HA_OVERLAY/" "$S/Assets/"
  rm -rf "$S/Temp/__Backupscenes"   # Oct 20: a killed scratch run leaves scene backups; a windowed relaunch then blocks on a modal "Scene Backup Detected" dialog (scratch only, never the user project)
  ux=0; "$UNITY" -batchmode -projectPath "$S" -executeMethod SpecGreybox.BuildWallGrid -quit -logFile "$ROOT/build.log" "${@:2}" || ux=$?
  for d in Scripts Editor; do rsync -a --ignore-existing --include='*/' --include='*.meta' --exclude='*' "$S/Assets/$d/" "$P/Assets/$d/"; done   # a new script's .meta: the scratch's GUID is the one the scene references (PlacedProp, Oct 17)
  if grep -q "error CS" "$ROOT/build.log"; then grep "error CS" "$ROOT/build.log" | head -5; exit 1; fi
  # a gate over its time budget (SpecGreybox.Step/BudgetGuard; zfight-check skill "Check speed") fails the build, naming the gate
  if grep -q "BUDGET FAIL" "$ROOT/build.log"; then grep -m5 "BUDGET FAIL" "$ROOT/build.log"; exit 1; fi
  [ $ux = 0 ] || { grep -m5 -iE "exception|error" "$ROOT/build.log"; echo "Unity build exited $ux" >&2; exit $ux; }
  # artist-pipeline quality gate on the generated models (tools/house/model_quality.py; .claude/skills/artist-pipeline)
  (cd "$REPO" && uv run -q --with numpy --with pillow python -I tools/house/model_quality.py --report >> spec/captures/walk-test-wallgrid.txt) || q=$?
  grep -E "^(Seam|Z-fight|Clash|Casing|Opening|Arch|Trim|Envelope|Props|Leak|Peek|Quality|MotionShadow|ShadowBudget|LampZones|SunCull|ok   front door|ok   paint|FAIL front door|FAIL paint)|BLOCKED" "$REPO/spec/captures/walk-test-wallgrid.txt"
  grep -E "^(Split drawn-outside|FAIL split drawn outside)" "$REPO/spec/captures/walk-test-wallgrid.txt" || true
  # walk note 2026-10-21T06:45:32: an upstairs piece drawn outside the film's front from outside fails the build (SpecGreybox.Split.cs)
  if grep -q "^FAIL split drawn outside" "$REPO/spec/captures/walk-test-wallgrid.txt"; then echo "split drawn-outside gate FAILED" >&2; exit 1; fi
  if grep -q "^FAIL lamp " "$REPO/spec/captures/walk-test-wallgrid.txt"; then grep -m5 "^FAIL lamp " "$REPO/spec/captures/walk-test-wallgrid.txt"; echo "lamp split gate FAILED (SpecGreybox.LampSplitCheck)" >&2; exit 1; fi
  [ "${q:-0}" = 0 ] || { echo "quality gate FAILED (model_quality.py)" >&2; exit 1; };;
bake)
  # the windowed bake opens the scratch project: no HDRP wizard popping up each time (a user-local editor preference)
  sed -i '' 's/m_WizardPopupAtStart: 1/m_WizardPopupAtStart: 0/' "$S/UserSettings/HDRPUserSettings.asset" 2>/dev/null || true
  rsync -a "$P/Assets/Editor/" "$S/Assets/Editor/"   # the bake runs the repo's BakeLighting, not the last build's copy (overnight3b: a bake-only fix never ran)
  # known modal blockers of the windowed bake (each stops it until someone clicks): "Scene Backup Detected" (build: Temp/__Backupscenes
  # removed), the HDRP wizard (above), "Incompatible Layout ... invalidate all previously bake data" (Oct 21: the probe volume's size
  # changed; BakeLighting clears the old bake before its first scenario)
  bx=0; "$UNITY" -projectPath "$S" -executeMethod BakeLighting.Bake -logFile "$ROOT/bake.log" || bx=$?   # windowed; exits when done
  grep -E "BakeLighting [DN]|Baked lights|Realtime lights|probe classes|xception" "$ROOT/bake.log" || true   # display only; the checks below decide
  # every authored-Baked light must be recorded as baked in the saved scene (BakeLighting.CheckBakedLights; the FilmFill bug, Oct 17)
  if grep -q "BakeLighting FAIL" "$ROOT/bake.log" || ! grep -q "^Baked lights:" "$ROOT/bake.log"; then grep -m5 "BakeLighting FAIL" "$ROOT/bake.log"; echo "bake FAILED the baked-lights check" >&2; exit 1; fi
  [ $bx = 0 ] || { echo "bake: Unity exited $bx" >&2; exit $bx; };;
load)
  # a build writes a fresh scene with no lighting data (default LightingDataAsset, no APV baking set, no probe images): loaded as is, day
  # is lit by the flat blue sky ambient only (user Oct 17 "the daytime lighting seems a little... flatter": 3 builds since the last bake;
  # day saturation 0.04-0.07 vs 0.11-0.15 baked). Bake first whenever the scratch scene is unbaked
  if grep -q 'm_LightingDataAsset: {fileID: 20201, guid: 0000000000000000f000000000000000' "$S/Assets/Scenes/House_WallGrid.unity"; then
    echo "load: the built scene has no bake (builds since the last bake): baking first"; HA_WHY="${HA_WHY:-auto: load of an unbaked build}" "$0" bake; fi
  (cd "$P" && "$CLI" command editor_stop >/dev/null 2>&1 || true)
  # switch the editor to an empty scene BEFORE overwriting House_WallGrid.unity: overwriting the open scene raised Unity's modal
  # "scene changed on disk, reload?" dialog, which froze the editor (and every command) for hours on Oct 17
  ev 'UnityEditor.SceneManagement.EditorSceneManager.NewScene(UnityEditor.SceneManagement.NewSceneSetup.EmptyScene, UnityEditor.SceneManagement.NewSceneMode.Single); return "empty";' >/dev/null || true
  cp "$S/Assets/Scenes/House_WallGrid.unity" "$P/Assets/Scenes/"
  rsync -a "$S/Assets/Scenes/House_WallGrid/" "$P/Assets/Scenes/House_WallGrid/"
  cp "$S/Assets/Settings/HouseLighting.lighting" "$S/Assets/Settings/"*.asset "$S/Assets/Settings/"*.asset.meta "$P/Assets/Settings/"   # metas too: a profile new to the build (ExteriorNight, Oct 18) got a fresh GUID in the project and the scene's volume lost it
  # Asset Store packs (gitignored): the whole pack folders from scratch, incl. the HDRP copies StoreProps saves inside them; a pack
  # imported only in scratch, or a missing *_HDRP.mat, leaves the scene with missing meshes or magenta (Oct 16)
  for pk in "Fadnn - Vintage Interior Furniture Pack" "Classic Wooden Furniture Pack" "Free Wood Door Pack" "VTC_AV-2062s" "ChristmasTreeAndGarland" "Tarantula" "BankersLamp" "ZNS3D"; do
    [ -d "$S/Assets/$pk" ] && rsync -a "$S/Assets/$pk" "$S/Assets/$pk.meta" "$P/Assets/"; done
  # StoreProps' HDRP copies of a GLB's materials (Purchased/, e.g. BuzzChest_BC_Mahogany_HDRP.mat) exist only in scratch: magenta without (Oct 18)
  for d in Purchased Models; do   # Models too: a generated GLB placed as a store prop (KevinArmchair.glb) came up magenta in the walk (Oct 18)
    [ -d "$S/Assets/$d" ] && (cd "$S/Assets" && find "$d" -name '*_HDRP.mat*') | while read -r f; do cp "$S/Assets/$f" "$P/Assets/$f"; done
  done
  [ -d "$S/Assets/Materials/Neighborhood" ] && rsync -a "$S/Assets/Materials/Neighborhood" "$S/Assets/Materials/Neighborhood.meta" "$P/Assets/Materials/"   # the neighbourhood's shared NB_* (HA_NEIGHBORHOOD=1 builds)
  rsync -a "$S/Assets/Materials/Greybox/" "$P/Assets/Materials/Greybox/"; rsync -a "$S/Assets/Textures/Greybox/" "$P/Assets/Textures/Greybox/" 2>/dev/null || true
  # the scene was built against the SCRATCH copy's asset GUIDs: a model or texture new to both projects gets its own GUID in each
  # (the open editor imports it separately), and the loaded scene then shows empty meshes / missing maps (kitchen cabinets, Oct 16).
  # Make the project's .meta match scratch for every built model and texture.
  for d in Models Textures Purchased; do
    (cd "$S/Assets" && find "$d" -name '*.meta') | while read -r m; do
      if [ -f "$P/Assets/${m%.meta}" ] && ! cmp -s "$S/Assets/$m" "$P/Assets/$m"; then cp "$S/Assets/$m" "$P/Assets/$m"; echo "synced GUID: $m"; fi
    done   # if/fi, not &&: a false test as the loop's last command killed the script under set -e (Oct 16)
  done
  for m in "$S"/Assets/Scripts/*.cs.meta; do cmp -s "$m" "$P/Assets/Scripts/$(basename "$m")" || echo "WARNING: $(basename "$m") GUID differs from the project's"; done
  ev 'UnityEditor.AssetDatabase.Refresh(); return "r";' >/dev/null || echo "load: the editor was busy importing (Refresh timed out); waiting for it" >&2; idle   # Oct 20: a big new store asset made this time out and set -e ended the load silently
  (cd "$P" && "$CLI" command open_scene Assets/Scenes/House_WallGrid.unity >/dev/null); idle
  # the first Play after a load can come up dull (lighting data still settling; user Oct 17, "sometimes this happens before it's
  # loaded"): a second Play cycle fixed it each time. ponytail: workaround, find why the first Play misses the baked data if it persists
  (cd "$P" && "$CLI" command editor_play >/dev/null); idle; (cd "$P" && "$CLI" command editor_stop >/dev/null); idle
  (cd "$P" && "$CLI" command editor_play | tail -1)
  # HA_START="x,y,z,yaw" (world feet, Unity coords): start the walk in the room under review (user Oct 17), not at the spawn
  if [ -n "${HA_START:-}" ]; then sleep 5; IFS=, read -r sx sy sz syaw <<< "$HA_START"
    for _t in 1 2 3 4 5 6; do r=$(ev "var f=UnityEngine.Object.FindFirstObjectByType<FpsController>(); var cc=f.GetComponent<UnityEngine.CharacterController>(); cc.enabled=false; f.transform.SetPositionAndRotation(new UnityEngine.Vector3(${sx}f,${sy}f,${sz}f), UnityEngine.Quaternion.Euler(0,${syaw}f,0)); f.cam.localRotation=UnityEngine.Quaternion.identity; cc.enabled=true; return \"start \"+f.transform.position;" || true); case "$r" in start*) break;; esac; sleep 5; done; [ "${r#start}" != "$r" ] || echo "HA_START: editor never answered (player left at the spawn)" >&2; fi   # Oct 18: the editor is busy for a while after Play/checks; retry instead of failing
  nc=0; "$0" nightcheck || nc=$?   # night lit at 3 room poses (shots use a camera clone)
  "$0" daycheck || nc=1             # day has its baked bounce (APV loaded, colour not flat)
  # the player came back at the spawn after the night check (user Oct 17): put the walk start back in the reviewed room
  if [ -n "${HA_START:-}" ]; then IFS=, read -r sx sy sz syaw <<< "$HA_START"
    for _t in 1 2 3 4 5 6; do r=$(ev "var f=UnityEngine.Object.FindFirstObjectByType<FpsController>(); var cc=f.GetComponent<UnityEngine.CharacterController>(); cc.enabled=false; f.transform.SetPositionAndRotation(new UnityEngine.Vector3(${sx}f,${sy}f,${sz}f), UnityEngine.Quaternion.Euler(0,${syaw}f,0)); f.cam.localRotation=UnityEngine.Quaternion.identity; cc.enabled=true; return \"start \"+f.transform.position;" || true); case "$r" in start*) break;; esac; sleep 5; done; [ "${r#start}" != "$r" ] || echo "HA_START: editor never answered (player left at the spawn)" >&2; fi   # Oct 18: the editor is busy for a while after Play/checks; retry instead of failing
  exit $nc;;
nightcheck)   # night must be lit: mean luminance of night shots at 3 room poses >= a floor (user Oct 17 "why are all the lights off at night?")
  # broken state it catches: a Scene-view search filter ("piano") made HDRP force fixed exposure from the physical camera (EV 14.6):
  # night means were 0.011 / 0.001 / 0.000; fixed (SceneFilterExposureGuard) 0.339 / 0.311 / 0.290. Floor 0.10 each. load runs it last.
  fails=0
  for p in "foyer 1.5 -3.0 -10.0 90 0.10" "living 6.5 -3.0 -13.8 180 0.10" "buzz 8.45 0.03 -13.0 340 0.10" "parents 6.455 0.03 -3.07 286 0.20" "attic 6.556 2.65 -16.95 0 0.05"; do   # attic (Oct 18): one bedside lamp + two bare bulbs, attic-dim by design: half the floor
    set -- $p; f=$("$0" shot "nightcheck-$1" "$2" "$3" "$4" "$5" 0 night)
    m=$(uv run -q --with pillow python -I -c "import sys; from PIL import Image, ImageStat; print('%.3f'%(ImageStat.Stat(Image.open(sys.argv[1]).convert('L')).mean[0]/255))" "$f")
    ok=$(python3 -c "print(1 if $m >= $6 else 0)"); [ "$ok" = 1 ] && echo "ok   night $1 mean $m (floor $6)" || { echo "FAIL night $1 mean $m < floor $6: $f"; fails=1; }
  done
  [ $fails = 0 ] || { echo "nightcheck FAILED: night is dark (Scene-view search filter on? HDRP exposure stuck?)" >&2; exit 1; };;
daycheck)   # day must have its baked bounce: the APV baking set loaded, and day colour above a measured floor (user Oct 17 "flatter")
  # broken state it catches: a build loaded without a bake (no APV, sky ambient only): saturation marina-16 0.042, kevin-front 0.059;
  # baked 0.114 / 0.118 (accepted Buzz trial 2: 0.113 / 0.118). Floor 0.085 each. load runs it after nightcheck.
  fails=0
  # The colour floors were calibrated in the Sunny baked scenario. Morning/Overcast
  # change realtime light, so testing arbitrary user weather makes the result non-reproducible.
  weather=$(ev 'var w=UnityEngine.Object.FindObjectsByType<HouseWeather>(UnityEngine.FindObjectsInactive.Include,UnityEngine.FindObjectsSortMode.None)[0]; var was=(int)w.state; w.Apply(HouseWeather.State.Sunny); return was.ToString();')
  case "$weather" in 0|1|2) trap 'ev "var w=UnityEngine.Object.FindObjectsByType<HouseWeather>(UnityEngine.FindObjectsInactive.Include,UnityEngine.FindObjectsSortMode.None)[0]; w.Apply((HouseWeather.State)$weather); return \"restored\";" >/dev/null || true' EXIT;; *) echo "FAIL day: weather state unavailable"; exit 1;; esac
  apv=$(ev 'var p=UnityEngine.Rendering.ProbeReferenceVolume.instance; return (p.currentBakingSet!=null && p.DataHasBeenLoaded())?"yes":"no";')
  [ "$apv" = yes ] && echo "ok   day APV baking set loaded" || { echo "FAIL day: no APV baking set loaded (scene unbaked?)"; fails=1; }
  for p in "marina-16 8.652 1.304 -13.193 9.536 1.197 -13.649 37.57 0.05 0.085" "kevin-front 8.4 1.1 -12.6 11.15 0.9 -14.2 60 0.05 0.085"; do
    set -- $p; f=$("$0" cam "daycheck-$1" "$2" "$3" "$4" "$5" "$6" "$7" "$8" "$9" day)
    m=$(uv run -q --with pillow --with numpy python -I -c "import sys,numpy as n; from PIL import Image; a=n.asarray(Image.open(sys.argv[1]).convert('RGB'))/255.; print('%.3f'%(a.max(-1)-a.min(-1)).mean())" "$f")
    ok=$(python3 -c "print(1 if $m >= ${10} else 0)"); [ "$ok" = 1 ] && echo "ok   day $1 saturation $m (floor ${10})" || { echo "FAIL day $1 saturation $m < floor ${10}: $f"; fails=1; }
  done
  # Buzz's wood floor must read brown, not navy (overnight3b, Oct 18): linear R/B of the floor beside the chest. The room probes lit only
  # rendering layer 1 and Buzz's furniture/floor (LayerOverhang) reflected the blue sky: R/B 0.65; probes on every layer 8.2, with DayGrade WB removed 6.3. Floor 1.5
  f=$("$0" shot daycheck-buzz-floor 9.3 0.03 -13.4 120 35 day)
  m=$(uv run -q --with pillow --with numpy python -I -c "import sys,numpy as n; from PIL import Image; a=(n.asarray(Image.open(sys.argv[1]).convert('RGB').resize((640,360)))[160:220,420:540]/255.)**2.2; m=a.reshape(-1,3).mean(0); print('%.2f'%(m[0]/m[2]))" "$f")
  ok=$(python3 -c "print(1 if $m >= 1.5 else 0)"); [ "$ok" = 1 ] && echo "ok   day buzz floor warmth R/B $m (floor 1.5)" || { echo "FAIL day buzz floor R/B $m < 1.5 (blue: probes not lighting its layer?): $f"; fails=1; }
  [ $fails = 0 ] || { echo "daycheck FAILED: day is flat (unbaked build loaded? APV missing?)" >&2; exit 1; };;
all) "$0" build && "$0" bake && "$0" load;;
shot|cam)
  mode="$1"; name="$2"; shift 2
  if [ "$mode" = shot ]; then x=$1 y=$2 z=$3 yaw=$4 pitch=$5; dn=${6:-day}
    pose="g.transform.position=new UnityEngine.Vector3(${x}f,${y}f+1.28f,${z}f); g.transform.rotation=UnityEngine.Quaternion.Euler(${pitch}f,${yaw}f,0);"
  else px=$1 py=$2 pz=$3 lx=$4 ly=$5 lz=$6 fov=$7 near=$8; dn=${9:-day}
    pose="var p=new UnityEngine.Vector3(${px}f,${py}f,${pz}f); g.transform.position=p; g.transform.rotation=UnityEngine.Quaternion.LookRotation(new UnityEngine.Vector3(${lx}f,${ly}f,${lz}f)-p); c.fieldOfView=${fov}f; c.nearClipPlane=${near}f;"
  fi
  night=$([ "$dn" = night ] && echo true || echo false)
  clear='foreach(var o in UnityEngine.Object.FindObjectsByType<UnityEngine.Camera>(UnityEngine.FindObjectsSortMode.None)) if(o.name=="TmpCam") UnityEngine.Object.DestroyImmediate(o.gameObject);'
  ev "$clear var hm=UnityEngine.Object.FindFirstObjectByType<HouseNightMode>(); UnityEngine.PlayerPrefs.SetInt(\"tmpwas\", hm.night?1:0); if(hm.night!=$night) hm.SetNight($night); var g=UnityEngine.Object.Instantiate(UnityEngine.Camera.main.gameObject); g.name=\"TmpCam\"; g.tag=\"Untagged\"; foreach(var a in g.GetComponentsInChildren<UnityEngine.AudioListener>()) UnityEngine.Object.Destroy(a); foreach(var m in g.GetComponents<UnityEngine.MonoBehaviour>()) if(!(m is UnityEngine.Rendering.HighDefinition.HDAdditionalCameraData)) UnityEngine.Object.Destroy(m); var c=g.GetComponent<UnityEngine.Camera>(); c.enabled=false; var hd=g.GetComponent<UnityEngine.Rendering.HighDefinition.HDAdditionalCameraData>(); hd.customRenderingSettings=true; hd.renderingPathCustomFrameSettingsOverrideMask.mask[(uint)UnityEngine.Rendering.HighDefinition.FrameSettingsField.MotionBlur]=true; hd.renderingPathCustomFrameSettings.SetEnabled(UnityEngine.Rendering.HighDefinition.FrameSettingsField.MotionBlur,false); $pose for(int i=0;i<30;i++) c.Render(); return \"ok\";" >/dev/null
  (cd "$P" && "$CLI" command capture_game_view --camera TmpCam --save_path "Temp/$name.png" >/dev/null)
  ev "$clear var hm=UnityEngine.Object.FindFirstObjectByType<HouseNightMode>(); bool was=UnityEngine.PlayerPrefs.GetInt(\"tmpwas\")==1; if(hm.night!=was) hm.SetNight(was); return \"x\";" >/dev/null
  mv "$P/Assets/Temp/$name.png" "$CAP/"; rm -rf "$P/Assets/Temp" "$P/Assets/Temp.meta"; echo "$CAP/$name.png";;
*) sed -n 2,17p "$0"; exit 1;;
esac
