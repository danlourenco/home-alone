#!/bin/sh
# Phase 0b end to end, after Unity has rendered sfm-work/synthetic/render + gt.json:
# compose tour.mp4 -> extract every 6th video frame (named by video frame index) -> solve.sh unchanged -> score.
set -eu
ws=${1:-sfm-work/synthetic}
uv run -q --with numpy --with pillow python -I tools/sfm/synthetic_compose.py "$ws"
rm -rf "$ws/images"; mkdir -p "$ws/images"
ffmpeg -v error -i "$ws/tour.mp4" -vf "select='not(mod(n\,6))'" -fps_mode passthrough -q:v 2 "$ws/images/seq_%05d.jpg"
# seq k (1-based) is video frame 6*(k-1); scoring maps names back through timeline.json.
for f in "$ws"/images/seq_*.jpg; do k=$(basename "$f" .jpg | sed 's/seq_0*//'); mv "$f" "$ws/images/$(printf v_%05d.jpg $((6 * (k - 1))))"; done
echo "$(ls "$ws/images" | wc -l) frames extracted"
tools/sfm/solve.sh "$ws" > "$ws/solve.log" 2>&1
uv run -q --with numpy python -I tools/sfm/synthetic_score.py "$ws" "$ws/sparse"
