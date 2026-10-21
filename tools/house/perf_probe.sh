#!/usr/bin/env bash
# perf_probe.sh: measure House_WallGrid in a STANDALONE macOS player at fixed poses (docs/PERFORMANCE.md).
#
#   tools/house/perf_probe.sh build [dev]    # APFS-clone the MAIN project (unity/HomeAlone: the scene + bake the user walks, as it is
#                                            # on disk, uncommitted trials included) to ~/.cache/home-alone-perf/HomeAlone (no Temp, no
#                                            # lock files) and build ~/.cache/home-alone-perf/build/HomeAlone.app (the local Mac test app;
#                                            # `dev`: HomeAloneDev.app, a development player: draw calls/batches + ring-buffer warnings)
#                                            # HA_REUSE=1: rebuild in the existing clone (scripts changed only; ~3 min)
#                                            # HA_PERF_APP=<other.app>: a variant player (PerfBuild.cs flags)
#                                            # HA_OVERLAY=<dir>: drafts (dir/Scripts, dir/Editor ...) copied over the clone's Assets/
#   tools/house/perf_probe.sh run LABEL      # run the player's tour (PerfProbe.cs -perfprobe): 6 poses x day/night, 300 frames each,
#                                            # 1920x1080 windowed -> ~/.cache/home-alone-perf/runs/LABEL/*.json + *.png, and prints the table
#                                            # HA_PERF_ARGS="-perfoff ShadowMaps,SSAO": HDRP frame settings off (attribution runs)
#                                            # HA_PERF_ARGS="-perfab -perfoff SSAO": base/variant alternated per pose in one session
#                                            # HA_DISPLAY="Studio Display": full screen on that display at its native pixels (display.txt)
#   tools/house/perf_probe.sh ab NAME APP_A APP_B   # two builds (a project-setting change), tours A B A B -> base -> variant table
#                                            # (HA_PERF_APP=<.app> picks the player for run)
#   tools/house/perf_probe.sh table A [B]    # the table for run A, or A vs B (before/after) with the PNG difference per pose
#   tools/house/perf_probe.sh gate LABEL     # tour (if LABEL isn't done) + FAIL over the BUDGET table in docs/PERFORMANCE.md
#   tools/house/perf_probe.sh attrib LABEL   # heavy frames per pose and their named cause (perf_attrib.py; HA_PERF_APP=<dev .app> tour)
#   tools/house/perf_probe.sh clean          # delete the clone + player (~0.5-1 GB real; the clone shares blocks until rebuilt)
# Wait for other Unity jobs first (one builder): never while tools/house/pipeline_busy.sh reports a build/bake/load.
# LOCAL ONLY: the app carries gitignored store assets and the unlicensed exterior GLB; never distribute it, never commit build/.
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
SRC="${HA_PERF_SRC:-$REPO/unity/HomeAlone}"   # HA_PERF_SRC: clone another project (a scratch house build: ~/.cache/home-alone-2/ucopy/HomeAlone)
W="$HOME/.cache/home-alone-perf"; C="$W/HomeAlone"; APP="${HA_PERF_APP:-$W/build/HomeAlone.app}"
UNITY=/Applications/Unity/Hub/Editor/6000.6.0f1/Unity.app/Contents/MacOS/Unity
case "${1:-}" in
build)
  "$REPO/tools/house/pipeline_busy.sh" && { echo "a pipeline build/bake/load is running: wait" >&2; exit 1; }
  [ "${2:-}" = dev ] && { APP="$W/build/HomeAloneDev.app"; DEV=-perfDev; } || DEV=
  if [ -z "$DEV" ] && [ -z "${HA_REUSE:-}" ] || [ ! -d "$C" ]; then   # `dev` reuses the release build's clone (same scene; IL2CPP caches warm)
    mkdir -p "$W"; rm -rf "$C"; cp -Rc "$SRC" "$C"; rm -rf "$C/Temp" "$C/Logs"   # copy-on-write clone: seconds, ~no disk
    find "$C/Library" \( -name "*-lock" -o -name "*.lock" \) -delete   # the open editor's LMDB/DataStore locks
    rm -f "$C/Assets/BankersLamp/Scripts/RenderTextureCaptureEditor.cs"*   # bought pack: an editor script outside Editor/ breaks player builds
    [ -n "${HA_OVERLAY:-}" ] && cp -R "$HA_OVERLAY/." "$C/Assets/"
    [ -n "${HA_PERF_SRC:-}" ] && { rsync -a "$REPO/unity/HomeAlone/Assets/Scripts/" "$C/Assets/Scripts/"; rsync -a "$REPO/unity/HomeAlone/Assets/Editor/" "$C/Assets/Editor/"; }   # the repo's scripts over a scratch clone
  elif [ -n "${HA_REUSE:-}" ]; then   # scripts only: the repo's Scripts + Editor into the existing clone (the scene and bake stay as cloned)
    rsync -a "$SRC/Assets/Scripts/" "$C/Assets/Scripts/"; rsync -a "$SRC/Assets/Editor/" "$C/Assets/Editor/"; mkdir -p "$C/Assets/Branding"; rsync -a "$SRC/Assets/Branding/" "$C/Assets/Branding/"   # + the app icon
    for d in UI Shaders; do [ -d "$SRC/Assets/$d" ] && rsync -a "$SRC/Assets/$d" "$C/Assets/" && { [ -f "$SRC/Assets/$d.meta" ] && cp "$SRC/Assets/$d.meta" "$C/Assets/" || true; }; done   # runtime UI + shaders (Oct 21: F1 panel missing its UXML)
  fi
  T=$SECONDS; "$UNITY" -batchmode -projectPath "$C" -executeMethod PerfBuild.Build -perfOut "$APP" $DEV ${HA_BUILD_ARGS:-} -quit -logFile "$W/build.log" || { grep -m5 -E "error|PerfBuild" "$W/build.log"; exit 1; }
  grep PerfBuild "$W/build.log"; echo "player built in $((SECONDS-T)) s";;
run)
  L="${2:?label}"; O="$W/runs/$L"; rm -rf "$O"; mkdir -p "$O"; printf '%s\n' "${HA_PERF_ARGS:-}" > "$O/args.txt"   # the sheet names variants from it
  defaults write "$(defaults read "$APP/Contents/Info.plist" CFBundleIdentifier)" NSAppSleepDisabled -bool YES   # no App Nap throttling in the background
  SCR=(-screen-width 1920 -screen-height 1080 -screen-fullscreen 0)
  if [ -n "${HA_DISPLAY:-}" ]; then   # HA_DISPLAY="Studio Display": full screen there at its native pixels (system_profiler), not its "looks like" size
    WH=$(system_profiler SPDisplaysDataType | awk -v d="$HA_DISPLAY:" '$0 ~ "^ +"d"$" {f=1} f && /Resolution:/ {print $2"x"$4; exit}')
    [ -n "$WH" ] || { echo "display '$HA_DISPLAY' not found (system_profiler SPDisplaysDataType)" >&2; exit 1; }
    SCR=(-screen-width "${WH%x*}" -screen-height "${WH#*x}" -screen-fullscreen 0 -perfdisplay "$HA_DISPLAY"); echo "full screen on $HA_DISPLAY at $WH"   # PerfProbe moves the window there, then goes full screen
  fi
  "$APP/Contents/MacOS/"* -perfprobe "$O" "${SCR[@]}" -logFile "$O/player.log" ${HA_PERF_ARGS:-} >/dev/null 2>&1 &
  pid=$!; caffeinate -d -u -w $pid &   # display awake for the whole tour: with the display asleep GPU timings come back empty (Oct 18)
  for _ in $(seq 1 900); do [ -f "$O/done.txt" ] && break; kill -0 $pid 2>/dev/null || break
    [ "$(stat -f %z "$O/player.log" 2>/dev/null || echo 0)" -lt 200000000 ] || { echo "player log over 200 MB (error loop): killed" >&2; kill $pid; tail -c 3000 "$O/player.log" > "$O/player-tail.log"; rm "$O/player.log"; break; }
    sleep 2; done
  sleep 2; kill $pid 2>/dev/null || true
  [ -f "$O/done.txt" ] || { echo "tour did not finish: $O/player.log" >&2; exit 1; }
  uv run -q --with numpy --with pillow python -I "$REPO/tools/house/perf_table.py" "$O"
  # every A/B gets its visual comparison (user, Oct 20): pose rows x variant columns, FPS on each tile, opened for the user
  if ls "$O"/*-B1.png >/dev/null 2>&1; then uv run -q --with numpy --with pillow python -I "$REPO/tools/house/perf_table.py" --sheet "$O" && { [ -n "${HA_OPEN:-}" ] && open -a Preview "$O/sheet.jpg"; true; } 2>/dev/null || true; fi;;   # sheets go to the test board (tools/house/test_board.py); HA_OPEN=1 opens it
ab)   # ab NAME APP_A APP_B: tours A, B, A, B (two builds, e.g. a project-setting change), then the base -> variant table
  N="${2:?name}"; for i in 1 2; do HA_PERF_APP="$3" "$0" run "$N-A$i" >/dev/null; HA_PERF_APP="$4" "$0" run "$N-B$i" >/dev/null; done
  uv run -q --with numpy --with pillow python -I "$REPO/tools/house/perf_table.py" --ab "$W/runs/$N-A1" "$W/runs/$N-B1" "$W/runs/$N-A2" "$W/runs/$N-B2";;
gate)   # gate LABEL: tour LABEL (unless that run is already done), then FAIL if any pose's frame mean / motion time to rest is over the
        # "## BUDGET" table in docs/PERFORMANCE.md (perf_table.py --gate). On demand only: a tour is ~8 quiet minutes, too slow for a build
  L="${2:?label}"; [ -f "$W/runs/$L/done.txt" ] || "$0" run "$L" >/dev/null
  python3 -I "$REPO/tools/house/perf_table.py" --gate "$W/runs/$L" "$REPO/docs/PERFORMANCE.md";;
attrib) python3 -I "$REPO/tools/house/perf_attrib.py" "$W/runs/${2:?label}";;   # name each pose's heavy frames' cause (needs a dev player's tour)
sheet) shift; uv run -q --with numpy --with pillow python -I "$REPO/tools/house/perf_table.py" --sheet "$W/runs/$1" "${@:2}";;   # sheet LABEL [POSE ...]
table) shift; uv run -q --with numpy --with pillow python -I "$REPO/tools/house/perf_table.py" "${@/#/$W/runs/}";;
clean) rm -rf "$C" "$W/build";;   # runs/ (the benchmark history) is kept
*) sed -n 2,20p "$0"; exit 1;;
esac
