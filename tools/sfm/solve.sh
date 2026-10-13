#!/bin/sh
# Sparse SfM on an extracted workspace (CPU; Homebrew COLMAP has no CUDA).
# usage: tools/sfm/solve.sh <workspace>   (expects <workspace>/images)
set -eu
ws=$1; db=$ws/db.db
rm -rf "$db" "$ws/sparse"; mkdir -p "$ws/sparse"
colmap feature_extractor --database_path "$db" --image_path "$ws/images" \
  --ImageReader.single_camera 1 --ImageReader.camera_model SIMPLE_RADIAL \
  --FeatureExtraction.use_gpu 0
# Video frames: match neighbours in time, quadratic overlap catches revisits.
colmap sequential_matcher --database_path "$db" \
  --SequentialMatching.overlap 15 --FeatureMatching.use_gpu 0
colmap mapper --database_path "$db" --image_path "$ws/images" --output_path "$ws/sparse"
for m in "$ws"/sparse/*/; do echo "== $m"; colmap model_analyzer --path "$m" 2>&1 | grep -E "Images|Registered|Points|Mean reprojection|Mean track"; done
