#!/usr/bin/env bash
# ship.sh NAME [TOURFILE]: the whole build end to end with no agent watching it (user, Oct 21: agents babysitting builds were the
# biggest token spend). Each step logs to ~/.cache/home-alone-ship/NAME/<step>.log; the terminal gets one line per step and a
# short summary at the end (also summary.txt). Stops at the first failing step. An agent reads summary.txt, nothing else, unless a step failed.
#
#   HA_SCRATCH=$HOME/.cache/home-alone-2 HA_NEIGHBORHOOD=1 tools/house/ship.sh NB12 tours.txt
#
# Steps: preflight -> build (gates) -> bake -> app (perf clone from the scratch build) -> tours -> checks -> board -> promote.
#   TOURFILE: one tour per line, "LABEL<TAB>perf args" (e.g. "nb12-front<TAB>-perfrounds 1 -perfdn night -perfposes front6399,walk0645").
#     Optional. Blank lines and #comments skipped. Tours run windowed on the app just built.
#   CHECKS: each tools/house check that knows a run (brick_storeys, window_glow, xmas_lights_check) runs on the tours' outputs when
#     present; its last line goes in the summary.
#   HA_SKIP="bake promote" skips steps; HA_NO_PROMOTE=1 = no Dock promotion.
set -uo pipefail
NAME="${1:?usage: ship.sh NAME [TOURFILE]}"; TOURS="${2:-}"
REPO="$(cd "$(dirname "$0")/../.." && pwd)"; H="$REPO/tools/house"
OUT="$HOME/.cache/home-alone-ship/$NAME"; mkdir -p "$OUT"; SUM="$OUT/summary.txt"; : > "$SUM"
APP="$HOME/.cache/home-alone-perf/build/HomeAlone$NAME.app"; RUNS="$HOME/.cache/home-alone-perf/runs"
T0=$(date +%s)
say() { echo "$*" | tee -a "$SUM"; }
skip() { [[ " ${HA_SKIP:-} " == *" $1 "* ]]; }

# step NAME CMD...: run, log, one line; on failure print the log's FAIL/error lines and stop
step() {
  local s="$1"; shift; skip "$s" && { say "$(printf '%-9s SKIP' "$s")"; return 0; }
  local t=$(date +%s) log="$OUT/$s.log"
  "$@" > "$log" 2>&1; local rc=$?
  local key; key=$(grep -E "FAIL|BLOCKED|error CS|Exception|Succeeded|PASS|baked|ok " "$log" | grep -v "^ *#" | tail -3 | tr '\n' ' ' | cut -c1-160)
  [ -z "$key" ] && key=$(tail -1 "$log" | cut -c1-160)
  if [ $rc -eq 0 ]; then say "$(printf '%-9s PASS %4ss  %s' "$s" $(( $(date +%s) - t )) "$key")"
  else say "$(printf '%-9s FAIL %4ss  rc=%s  %s' "$s" $(( $(date +%s) - t )) "$rc" "$key")"
       grep -nE "FAIL|BLOCKED|error|Exception" "$log" | head -12 | sed 's/^/          /' | tee -a "$SUM"
       say "stopped at $s (log $log)"; exit 1; fi
}

"$H/pipeline_busy.sh" >/dev/null 2>&1 && { say "pipeline busy: another build/bake is running"; exit 2; }
say "ship $NAME  $(date '+%F %T')  HEAD $(git -C "$REPO" rev-parse --short HEAD)$(git -C "$REPO" diff --quiet || echo ' +dirty')"

step preflight "$H/unity_pipeline.sh" preflight
step build     "$H/unity_pipeline.sh" build
step bake      "$H/unity_pipeline.sh" bake
step app       env HA_PERF_SRC="${HA_SCRATCH:-$HOME/.cache/home-alone-2}/ucopy/HomeAlone" HA_PERF_APP="$APP" "$H/perf_probe.sh" build

# tours: one perf_probe run per line
if [ -n "$TOURS" ] && ! skip tours; then
  while IFS=$'\t' read -r label args; do
    [[ -z "$label" || "$label" == \#* ]] && continue
    step "tour:$label" env HA_PERF_APP="$APP" HA_PERF_ARGS="$args" "$H/perf_probe.sh" run "$NAME-$label"
  done < "$TOURS"
fi

# checks: whichever apply to the tours' outputs (each prints its verdict last)
if ! skip checks && [ -n "$TOURS" ]; then
  while IFS=$'\t' read -r label args; do
    [[ -z "$label" || "$label" == \#* ]] && continue; R="$RUNS/$NAME-$label"
    [ -f "$R/walk0645-day-A1.png" ] && { r=$(uv run -q --with numpy --with pillow python -I "$H/brick_storeys.py" "$R" 2>&1 | tail -1); say "$(printf '%-9s %s' brick "$r")"; }
    for f in "$R"/front6399-night-A1.png; do [ -f "$f" ] || continue
      r=$(uv run -q --with numpy --with pillow python -I "$H/window_glow.py" "$f" 2>&1 | tail -1); say "$(printf '%-9s %s' windows "$r")"
      r=$(uv run -q --with numpy --with pillow python -I "$H/xmas_lights_check.py" "$f" 2>&1 | tail -1); say "$(printf '%-9s %s' xmas "$r")"; done
  done < "$TOURS"
fi

step board env uv run -q --with pillow python -I "$H/test_board.py"
[ -z "${HA_NO_PROMOTE:-}" ] && step promote "$H/promote_app.sh" "$APP"
say "done $NAME in $(( ($(date +%s) - T0) / 60 )) min  app $APP  (board rebuilt: publish ~/.cache/home-alone-board/test-board.html)"
