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

case "${1:-}" in
setup)
  mkdir -p "$ROOT/ucopy"; rsync -a --exclude Temp "$P/" "$S/"; ln -sfn "$REPO/spec" "$ROOT/spec"
  echo "scratch copy at $S (first open imports the Library: minutes)";;
build)
  rsync -a "$P/Assets/Editor/" "$S/Assets/Editor/"; rsync -a "$P/Assets/Scripts/" "$S/Assets/Scripts/"
  rsync -a "$P/Assets/Models/" "$S/Assets/Models/"; cp "$P/Assets/Settings/HDRP.asset" "$S/Assets/Settings/"
  rsync -a --exclude Greybox --exclude Greybox.meta "$P/Assets/Textures/" "$S/Assets/Textures/"   # generated + Poly Haven maps (kitchen); Greybox/ is the build's own
  for pk in "Fadnn - Vintage Interior Furniture Pack" "Classic Wooden Furniture Pack" "Free Wood Door Pack" "VTC_AV-2062s" "ChristmasTreeAndGarland"; do   # Asset Store packs (gitignored; may be absent)
    [ -d "$P/Assets/$pk" ] && rsync -a "$P/Assets/$pk" "$P/Assets/$pk.meta" "$S/Assets/"; done
  [ -d "$P/Assets/Purchased" ] && rsync -a "$P/Assets/Purchased" "$S/Assets/" && { [ -f "$P/Assets/Purchased.meta" ] && cp "$P/Assets/Purchased.meta" "$S/Assets/" || true; }   # CGTrader buys (gitignored; may be absent: generated plants then)
  "$UNITY" -batchmode -projectPath "$S" -executeMethod SpecGreybox.BuildWallGrid -quit -logFile "$ROOT/build.log" || true
  if grep -q "error CS" "$ROOT/build.log"; then grep "error CS" "$ROOT/build.log" | head -5; exit 1; fi
  # artist-pipeline quality gate on the generated models (tools/house/model_quality.py; .claude/skills/artist-pipeline)
  (cd "$REPO" && uv run -q --with numpy --with pillow python -I tools/house/model_quality.py --report >> spec/captures/walk-test-wallgrid.txt) || true
  grep -E "^(Seam|Z-fight|Clash|Casing|Arch|Trim|Envelope|Props|Leak|Peek|Quality)|BLOCKED" "$REPO/spec/captures/walk-test-wallgrid.txt";;
bake)
  # the windowed bake opens the scratch project: no HDRP wizard popping up each time (a user-local editor preference)
  sed -i '' 's/m_WizardPopupAtStart: 1/m_WizardPopupAtStart: 0/' "$S/UserSettings/HDRPUserSettings.asset" 2>/dev/null || true
  "$UNITY" -projectPath "$S" -executeMethod BakeLighting.Bake -logFile "$ROOT/bake.log" || true   # windowed; exits when done
  grep -E "BakeLighting [DN]|xception" "$ROOT/bake.log";;
load)
  (cd "$P" && "$CLI" command editor_stop >/dev/null 2>&1 || true)
  # switch the editor to an empty scene BEFORE overwriting House_WallGrid.unity: overwriting the open scene raised Unity's modal
  # "scene changed on disk, reload?" dialog, which froze the editor (and every command) for hours on Oct 17
  ev 'UnityEditor.SceneManagement.EditorSceneManager.NewScene(UnityEditor.SceneManagement.NewSceneSetup.EmptyScene, UnityEditor.SceneManagement.NewSceneMode.Single); return "empty";' >/dev/null || true
  cp "$S/Assets/Scenes/House_WallGrid.unity" "$P/Assets/Scenes/"
  rsync -a "$S/Assets/Scenes/House_WallGrid/" "$P/Assets/Scenes/House_WallGrid/"
  cp "$S/Assets/Settings/HouseLighting.lighting" "$S/Assets/Settings/"*.asset "$P/Assets/Settings/"
  # Asset Store packs (gitignored): the whole pack folders from scratch, incl. the HDRP copies StoreProps saves inside them; a pack
  # imported only in scratch, or a missing *_HDRP.mat, leaves the scene with missing meshes or magenta (Oct 16)
  for pk in "Fadnn - Vintage Interior Furniture Pack" "Classic Wooden Furniture Pack" "Free Wood Door Pack" "VTC_AV-2062s" "ChristmasTreeAndGarland"; do
    [ -d "$S/Assets/$pk" ] && rsync -a "$S/Assets/$pk" "$S/Assets/$pk.meta" "$P/Assets/"; done
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
  ev "$clear var hm=UnityEngine.Object.FindFirstObjectByType<HouseNightMode>(); UnityEngine.PlayerPrefs.SetInt(\"tmpwas\", hm.night?1:0); hm.SetNight($night); var g=UnityEngine.Object.Instantiate(UnityEngine.Camera.main.gameObject); g.name=\"TmpCam\"; foreach(var a in g.GetComponentsInChildren<UnityEngine.AudioListener>()) UnityEngine.Object.Destroy(a); foreach(var m in g.GetComponents<UnityEngine.MonoBehaviour>()) if(!(m is UnityEngine.Rendering.HighDefinition.HDAdditionalCameraData)) UnityEngine.Object.Destroy(m); var c=g.GetComponent<UnityEngine.Camera>(); c.enabled=false; var hd=g.GetComponent<UnityEngine.Rendering.HighDefinition.HDAdditionalCameraData>(); hd.customRenderingSettings=true; hd.renderingPathCustomFrameSettingsOverrideMask.mask[(uint)UnityEngine.Rendering.HighDefinition.FrameSettingsField.MotionBlur]=true; hd.renderingPathCustomFrameSettings.SetEnabled(UnityEngine.Rendering.HighDefinition.FrameSettingsField.MotionBlur,false); $pose for(int i=0;i<30;i++) c.Render(); return \"ok\";" >/dev/null
  (cd "$P" && "$CLI" command capture_game_view --camera TmpCam --save_path "Temp/$name.png" >/dev/null)
  ev "$clear UnityEngine.Object.FindFirstObjectByType<HouseNightMode>().SetNight(UnityEngine.PlayerPrefs.GetInt(\"tmpwas\")==1); return \"x\";" >/dev/null
  mv "$P/Assets/Temp/$name.png" "$CAP/"; rm -rf "$P/Assets/Temp" "$P/Assets/Temp.meta"; echo "$CAP/$name.png";;
*) sed -n 2,14p "$0"; exit 1;;
esac
