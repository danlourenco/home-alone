#!/usr/bin/env bash
# perf_probe.sh: measure House_WallGrid in a STANDALONE macOS player at fixed poses (docs/PERFORMANCE.md).
#
#   tools/house/perf_probe.sh build          # APFS-clone the scratch copy ($HA_SCRATCH/ucopy, the last built+baked scene) to
#                                            # ~/.cache/home-alone-perf/HomeAlone and build ~/.cache/home-alone-perf/build/HomeAlonePerf.app
#   tools/house/perf_probe.sh run LABEL      # run the player's tour (PerfProbe.cs -perfprobe): 6 poses x day/night, 300 frames each,
#                                            # 1920x1080 windowed -> ~/.cache/home-alone-perf/runs/LABEL/*.json + *.png, and prints the table
#                                            # HA_PERF_ARGS="-perfoff ShadowMaps,SSAO": HDRP frame settings off (attribution runs)
#                                            # HA_PERF_ARGS="-perfab -perfoff SSAO": base/variant alternated per pose in one session
#   tools/house/perf_probe.sh ab NAME APP_A APP_B   # two builds (a project-setting change), tours A B A B -> base -> variant table
#                                            # (HA_PERF_APP=<.app> picks the player for run)
#   tools/house/perf_probe.sh table A [B]    # the table for run A, or A vs B (before/after) with the PNG difference per pose
#   tools/house/perf_probe.sh clean          # delete the clone + player (~0.5-1 GB real; the clone shares blocks until rebuilt)
# Wait for other Unity jobs first: the clone is taken from the scratch copy, so never while unity_pipeline.sh build|bake runs.
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
SRC="${HA_SCRATCH:-$HOME/.cache/home-alone}/ucopy/HomeAlone"
W="$HOME/.cache/home-alone-perf"; C="$W/HomeAlone"; APP="${HA_PERF_APP:-$W/build/HomeAlonePerf.app}"
UNITY=/Applications/Unity/Hub/Editor/6000.6.0f1/Unity.app/Contents/MacOS/Unity
case "${1:-}" in
build)
  pgrep -f "unity_pipeline.sh (build|bake)" >/dev/null && { echo "a pipeline build/bake is running: wait" >&2; exit 1; }
  mkdir -p "$W"; rm -rf "$C"; cp -Rc "$SRC" "$C"; rm -rf "$C/Temp"   # copy-on-write clone: seconds, ~no disk
  rm -f "$C/Assets/BankersLamp/Scripts/RenderTextureCaptureEditor.cs"*   # bought pack: an editor script outside Editor/ breaks player builds
  cp "$REPO/unity/HomeAlone/Assets/Scripts/PerfProbe.cs" "$C/Assets/Scripts/"; cp "$REPO/unity/HomeAlone/Assets/Editor/PerfBuild.cs" "$C/Assets/Editor/"
  T=$SECONDS; "$UNITY" -batchmode -projectPath "$C" -executeMethod PerfBuild.Build -perfOut "$APP" -quit -logFile "$W/build.log" || { grep -m5 -E "error|PerfBuild" "$W/build.log"; exit 1; }
  grep PerfBuild "$W/build.log"; echo "player built in $((SECONDS-T)) s";;
run)
  L="${2:?label}"; O="$W/runs/$L"; rm -rf "$O"; mkdir -p "$O"
  defaults write "$(defaults read "$APP/Contents/Info.plist" CFBundleIdentifier)" NSAppSleepDisabled -bool YES   # no App Nap throttling in the background
  "$APP/Contents/MacOS/"* -perfprobe "$O" -screen-width 1920 -screen-height 1080 -screen-fullscreen 0 -logFile "$O/player.log" ${HA_PERF_ARGS:-} >/dev/null 2>&1 &
  pid=$!; caffeinate -d -u -w $pid &   # display awake for the whole tour: with the display asleep GPU timings come back empty (Oct 18)
  for _ in $(seq 1 900); do [ -f "$O/done.txt" ] && break; kill -0 $pid 2>/dev/null || break
    [ "$(stat -f %z "$O/player.log" 2>/dev/null || echo 0)" -lt 200000000 ] || { echo "player log over 200 MB (error loop): killed" >&2; kill $pid; tail -c 3000 "$O/player.log" > "$O/player-tail.log"; rm "$O/player.log"; break; }
    sleep 2; done
  sleep 2; kill $pid 2>/dev/null || true
  [ -f "$O/done.txt" ] || { echo "tour did not finish: $O/player.log" >&2; exit 1; }
  uv run -q --with numpy --with pillow python -I "$REPO/tools/house/perf_table.py" "$O";;
ab)   # ab NAME APP_A APP_B: tours A, B, A, B (two builds, e.g. a project-setting change), then the base -> variant table
  N="${2:?name}"; for i in 1 2; do HA_PERF_APP="$3" "$0" run "$N-A$i" >/dev/null; HA_PERF_APP="$4" "$0" run "$N-B$i" >/dev/null; done
  uv run -q --with numpy --with pillow python -I "$REPO/tools/house/perf_table.py" --ab "$W/runs/$N-A1" "$W/runs/$N-B1" "$W/runs/$N-A2" "$W/runs/$N-B2";;
table) shift; uv run -q --with numpy --with pillow python -I "$REPO/tools/house/perf_table.py" "${@/#/$W/runs/}";;
clean) rm -rf "$C" "$W/build";;
*) sed -n 2,11p "$0"; exit 1;;
esac
