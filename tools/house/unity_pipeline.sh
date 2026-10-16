#!/usr/bin/env bash
# unity_pipeline.sh: build, bake, load and capture House_WallGrid without touching the user's open editor until the load.
#
#   tools/house/unity_pipeline.sh setup      # (once) make the scratch build copy: ~/.cache/home-alone/ucopy/HomeAlone (+ spec link)
#   tools/house/unity_pipeline.sh build      # copy Editor/Scripts/Models/HDRP.asset in, build the scene (batch); gates -> spec/captures/walk-test-wallgrid.txt
#   tools/house/unity_pipeline.sh bake       # bake day + night (WINDOWED: batch mode has no sky; BakeLighting refuses it)
#   tools/house/unity_pipeline.sh load       # copy scene + bake into the project, wait for import/compile, open, Play
#   tools/house/unity_pipeline.sh all        # build, bake, load
#   tools/house/unity_pipeline.sh shot NAME x y z yaw pitch [day|night]     # live capture from a player pose (feet; eye +1.28)
#   tools/house/unity_pipeline.sh cam  NAME px py pz lx ly lz vfov near [day|night]   # live capture from a camera pose (look-at)
# Captures land in ~/.cache/home-alone/captures/NAME.png. They use a CLONE of the player camera in the user's running editor (batch
# renders are not reliable for lighting) and never move the player; day/night is switched for the shot and restored.
#
# Lessons built in (Oct 16 2026):
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

case "${1:-}" in
setup)
  mkdir -p "$ROOT/ucopy"; rsync -a --exclude Temp "$P/" "$S/"; ln -sfn "$REPO/spec" "$ROOT/spec"
  echo "scratch copy at $S (first open imports the Library: minutes)";;
build)
  rsync -a "$P/Assets/Editor/" "$S/Assets/Editor/"; rsync -a "$P/Assets/Scripts/" "$S/Assets/Scripts/"
  rsync -a "$P/Assets/Models/" "$S/Assets/Models/"; cp "$P/Assets/Settings/HDRP.asset" "$S/Assets/Settings/"
  "$UNITY" -batchmode -projectPath "$S" -executeMethod SpecGreybox.BuildWallGrid -quit -logFile "$ROOT/build.log" || true
  if grep -q "error CS" "$ROOT/build.log"; then grep "error CS" "$ROOT/build.log" | head -5; exit 1; fi
  grep -E "^(Seam|Z-fight|Clash|Casing|Trim|Envelope|Leak|Peek)|BLOCKED" "$REPO/spec/captures/walk-test-wallgrid.txt";;
bake)
  "$UNITY" -projectPath "$S" -executeMethod BakeLighting.Bake -logFile "$ROOT/bake.log" || true   # windowed; exits when done
  grep -E "BakeLighting [DN]|xception" "$ROOT/bake.log";;
load)
  (cd "$P" && "$CLI" command editor_stop >/dev/null 2>&1 || true)
  cp "$S/Assets/Scenes/House_WallGrid.unity" "$P/Assets/Scenes/"
  rsync -a "$S/Assets/Scenes/House_WallGrid/" "$P/Assets/Scenes/House_WallGrid/"
  cp "$S/Assets/Settings/HouseLighting.lighting" "$S/Assets/Settings/"*.asset "$P/Assets/Settings/"
  rsync -a "$S/Assets/Materials/Greybox/" "$P/Assets/Materials/Greybox/"; rsync -a "$S/Assets/Textures/Greybox/" "$P/Assets/Textures/Greybox/" 2>/dev/null || true
  for m in "$S"/Assets/Scripts/*.cs.meta; do cmp -s "$m" "$P/Assets/Scripts/$(basename "$m")" || echo "WARNING: $(basename "$m") GUID differs from the project's"; done
  ev 'UnityEditor.AssetDatabase.Refresh(); return "r";' >/dev/null; idle
  (cd "$P" && "$CLI" command open_scene Assets/Scenes/House_WallGrid.unity >/dev/null); idle
  (cd "$P" && "$CLI" command editor_play | tail -1);;
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
  ev "$clear var hm=UnityEngine.Object.FindFirstObjectByType<HouseNightMode>(); UnityEngine.PlayerPrefs.SetInt(\"tmpwas\", hm.night?1:0); hm.SetNight($night); var g=UnityEngine.Object.Instantiate(UnityEngine.Camera.main.gameObject); g.name=\"TmpCam\"; foreach(var a in g.GetComponentsInChildren<UnityEngine.AudioListener>()) UnityEngine.Object.Destroy(a); foreach(var m in g.GetComponents<UnityEngine.MonoBehaviour>()) if(!(m is UnityEngine.Rendering.HighDefinition.HDAdditionalCameraData)) UnityEngine.Object.Destroy(m); var c=g.GetComponent<UnityEngine.Camera>(); c.enabled=false; $pose for(int i=0;i<30;i++) c.Render(); return \"ok\";" >/dev/null
  (cd "$P" && "$CLI" command capture_game_view --camera TmpCam --save_path "Temp/$name.png" >/dev/null)
  ev "$clear UnityEngine.Object.FindFirstObjectByType<HouseNightMode>().SetNight(UnityEngine.PlayerPrefs.GetInt(\"tmpwas\")==1); return \"x\";" >/dev/null
  mv "$P/Assets/Temp/$name.png" "$CAP/"; rm -rf "$P/Assets/Temp" "$P/Assets/Temp.meta"; echo "$CAP/$name.png";;
*) sed -n 2,14p "$0"; exit 1;;
esac
