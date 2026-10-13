#!/bin/sh
# Move <ws>/images/v_<frame>.jpg into <ws>/images/shotNN/ by scene cuts detected in <video>.
# usage: tools/sfm/split_shots.sh <ws> <video> [threshold=0.3]
set -eu
ws=$1; video=$2; th=${3:-0.3}
ffmpeg -v info -i "$video" -vf "select='gt(scene,$th)',showinfo" -f null - 2>&1 | sed -n 's/.* n: *\([0-9]*\) .*/\1/p' > "$ws/cut_frames.txt"
for f in "$ws"/images/v_*.jpg; do
  n=$(basename "$f" .jpg | sed 's/v_0*//'); n=${n:-0}
  shot=$(awk -v n="$n" '$1 <= n {s++} END {printf "shot%02d", s}' "$ws/cut_frames.txt")
  mkdir -p "$ws/images/$shot"; mv "$f" "$ws/images/$shot/"
done
echo "cuts at video frames: $(tr '\n' ' ' < "$ws/cut_frames.txt")"; for d in "$ws"/images/shot*; do echo "$(basename "$d"): $(ls "$d" | wc -l)"; done
