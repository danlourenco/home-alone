#!/bin/bash
# promote_app.sh APP: make APP the one the Dock icon opens (user, Oct 21: "make sure that the icon in the dock points to this latest app").
# The Dock is pinned to build/HomeAlone.app, so the newest walkable build is copied there; the previous one is kept as HomeAlone.prev.app.
# Refuses while HomeAlone.app is running (never kill the user's app).
set -euo pipefail
B="$HOME/.cache/home-alone-perf/build"; SRC="${1:?usage: promote_app.sh path/to/HomeAloneNBx.app}"; DST="$B/HomeAlone.app"
[ -d "$SRC/Contents/MacOS" ] || { echo "not an app: $SRC" >&2; exit 2; }
if pgrep -f "$DST/Contents/MacOS" >/dev/null; then echo "HomeAlone.app is open: quit it first (Cmd+Q)" >&2; exit 1; fi
rm -rf "$B/HomeAlone.prev.app"; [ -d "$DST" ] && mv "$DST" "$B/HomeAlone.prev.app"
ditto "$SRC" "$DST"
/System/Library/Frameworks/CoreServices.framework/Frameworks/LaunchServices.framework/Support/lsregister -f "$DST" >/dev/null 2>&1 || true
echo "Dock HomeAlone.app <- $(basename "$SRC") (previous kept as HomeAlone.prev.app)"
