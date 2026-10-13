#!/bin/sh
# Extract SfM frames from a tour video segment and log scene cuts.
# usage: tools/sfm/extract.sh <video> <start_s> <end_s> <out_dir> [fps]
set -eu
video=$1; start=$2; end=$3; out=$4; fps=${5:-4}
mkdir -p "$out/images"
ffmpeg -v error -ss "$start" -to "$end" -i "$video" -vf "fps=$fps" -q:v 2 "$out/images/f_%05d.jpg"
# Cut timestamps (relative to start) so segments can be solved separately.
ffmpeg -v info -ss "$start" -to "$end" -i "$video" -vf "select='gt(scene,0.3)',showinfo" -f null - 2>&1 \
  | sed -n 's/.*pts_time:\([0-9.]*\).*/\1/p' > "$out/cuts.txt"
echo "$(ls "$out/images" | wc -l) frames, $(wc -l < "$out/cuts.txt") cuts -> $out"
