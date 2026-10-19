#!/usr/bin/env bash
# csc_check.sh: compile the repo's Assets/Scripts/*.cs and Assets/Editor/*.cs against the scratch copy's last-built assemblies in
# ~10 s (no Unity launch), so a compile error never costs a house build or a bake (Oct 18: a build died on another file's CS0103).
#   tools/house/csc_check.sh        # exit 1 and print the errors on a failure
set -euo pipefail
REPO="$(cd "$(dirname "$0")/../.." && pwd)"; S="${HA_SCRATCH:-$HOME/.cache/home-alone}/ucopy/HomeAlone"; A="$REPO/unity/HomeAlone/Assets"
D=/Applications/Unity/Hub/Editor/6000.6.0f1/Unity.app/Contents/Resources/Scripting; CSC=$(ls "$D"/DotNetSdk/sdk/*/Roslyn/bincore/csc.dll | head -1)
DAG=$(dirname "$(ls -t "$S"/Library/Bee/artifacts/*.dag/Assembly-CSharp-Editor.rsp | head -1)"); T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
rsp() {   # rsp ASSEMBLY SRC_DIR: the scratch response file with the repo's sources, our output, and our Assembly-CSharp.dll
  grep -v '^"Assets/' "$DAG/$1.rsp" | grep -v '^-out:\|^-refout:' | sed "s#^-r:\"[^\"]*/Assembly-CSharp\(\.ref\)\{0,1\}\.dll\"#-r:\"$T/Assembly-CSharp.dll\"#"
  echo "-out:\"$T/$1.dll\""; for f in "$2"/*.cs; do echo "\"$f\""; done; }
cd "$S"; out=""
rsp Assembly-CSharp "$A/Scripts" > "$T/a.rsp"; out+=$("$D/DotNetSdk/dotnet" exec "$CSC" /nologo "@$T/a.rsp" 2>&1 || true)
rsp Assembly-CSharp-Editor "$A/Editor" > "$T/e.rsp"; out+=$("$D/DotNetSdk/dotnet" exec "$CSC" /nologo "@$T/e.rsp" 2>&1 || true)
if echo "$out" | grep -q "error CS"; then echo "$out" | grep "error CS" | sort -u | head -20; exit 1; fi; echo "ok   csc_check: Scripts + Editor compile"
