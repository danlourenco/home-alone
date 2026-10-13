#!/bin/sh
# Solve two video segments jointly to test whether they share geometry.
# usage: tools/sfm/link.sh <workspace>   (expects <workspace>/images/{p1,p2})
# One pinhole camera per folder (CG render: no distortion, centred principal point).
# Sequential matching within each video, plus every-2nd-frame cross pairs between them.
set -eu
ws=$1; db=$ws/db.db
rm -rf "$db" "$ws/sparse"; mkdir -p "$ws/sparse"
colmap feature_extractor --database_path "$db" --image_path "$ws/images" \
  --ImageReader.single_camera_per_folder 1 --ImageReader.camera_model SIMPLE_PINHOLE \
  --FeatureExtraction.use_gpu 0
colmap sequential_matcher --database_path "$db" \
  --SequentialMatching.overlap 15 --FeatureMatching.use_gpu 0
a=$(cd "$ws/images" && ls p1/*.jpg | awk 'NR%2'); b=$(cd "$ws/images" && ls p2/*.jpg | awk 'NR%2')
for x in $a; do for y in $b; do echo "$x $y"; done; done > "$ws/cross_pairs.txt"
colmap matches_importer --database_path "$db" --match_list_path "$ws/cross_pairs.txt" \
  --match_type pairs --FeatureMatching.use_gpu 0
colmap mapper --database_path "$db" --image_path "$ws/images" --output_path "$ws/sparse" \
  --Mapper.ba_refine_principal_point 0
for m in "$ws"/sparse/*/; do
  mkdir -p "$m/txt"; colmap model_converter --input_path "$m" --output_path "$m/txt" --output_type TXT
  n1=$(grep -c ' p1/' "$m/txt/images.txt" || true); n2=$(grep -c ' p2/' "$m/txt/images.txt" || true)
  echo "== $m p1=$n1 p2=$n2 $(colmap model_analyzer --path "$m" 2>&1 | grep -E 'Points|reprojection' | sed 's/.*\] //' | tr '\n' ' ')"
done
