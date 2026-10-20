#!/usr/bin/env bash
# play_views.sh: render a views JSON in the SCRATCH copy's windowed Play (ShadowAudit.PlayViews: baked lighting, cached shadows, per-view
# frame time) without touching the user's editor.
#   tools/house/play_views.sh spec/captures/views/<views>.json <audit-out.txt>      (HA_SCRATCH as unity_pipeline.sh; default ~/.cache/home-alone)
# Oct 20: a killed scratch run left Temp/__Backupscenes, and the next launch stopped on Unity's modal "Scene Backup Detected" dialog;
# the scratch's backup is removed first (scratch only, never the user's project). A windowed Unity in the background is throttled
# (frame times read 200 ms): keep the window in front for the frame-time numbers, and compare runs made the same way.
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../.." && pwd)"; S="${HA_SCRATCH:-$HOME/.cache/home-alone}/ucopy/HomeAlone"
[ -f "$1" ] || { echo "no views file $1" >&2; exit 1; }
rm -rf "$S/Temp/__Backupscenes"
timeout "${HA_VIEWS_TIMEOUT:-600}" /Applications/Unity/Hub/Editor/6000.6.0f1/Unity.app/Contents/MacOS/Unity -projectPath "$S" \
  -executeMethod ShadowAudit.PlayViews -views "$(cd "$(dirname "$1")" && pwd)/$(basename "$1")" -auditOut "$2" -logFile "${2%.txt}.log"
cat "$2"
