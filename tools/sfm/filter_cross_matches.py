"""Remove cross-video matches that land on repeating damask wallpaper; keep within-video matches.
Repeating wallpaper glues different walls together across videos (Oct 12 staircase test).
Writes a filtered copy of the database; drops cross pairs left with < min_matches.
usage: uv run --with numpy --with opencv-python-headless python -I tools/sfm/filter_cross_matches.py <db> <out_db> [min_matches=15]
"""
import shutil
import sqlite3
import sys
from pathlib import Path

import cv2
import numpy as np

MAX_ID = 2147483647


def wallpaper_mask(path):
    """Damask = warm hue, mid saturation (white trim is low-sat), busy texture. Dilated to fill motif gaps."""
    bgr = cv2.imread(str(path))
    h, s, v = cv2.split(cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV))
    warm = ((h >= 3) & (h <= 28) & (s >= 45) & (s <= 150) & (v >= 80)).astype(np.float32)
    g = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY).astype(np.float32)
    mu = cv2.blur(g, (21, 21))
    sd = np.sqrt(np.maximum(cv2.blur(g * g, (21, 21)) - mu * mu, 0))
    m = ((cv2.blur(warm, (31, 31)) > 0.35) & (sd > 12)).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((15, 15), np.uint8))
    # ponytail: colour/texture heuristic tuned on this damask; other wallpapers need their own check
    return cv2.dilate(m, np.ones((45, 45), np.uint8)) > 0


src_db, out_db = sys.argv[1], sys.argv[2]
min_matches = int(sys.argv[3]) if len(sys.argv) > 3 else 15
images_dir = Path(src_db).parent / "images"
shutil.copyfile(src_db, out_db)
con = sqlite3.connect(out_db)
names = dict(con.execute("SELECT image_id, name FROM images"))
kps = {i: np.frombuffer(b, np.float32).reshape(r, c)[:, :2]
       for i, r, c, b in con.execute("SELECT image_id, rows, cols, data FROM keypoints")}
masks = {}

stats = {"pairs": 0, "dropped": 0, "matches_in": 0, "matches_out": 0}
for pid, rows, blob in con.execute("SELECT pair_id, rows, data FROM two_view_geometries WHERE rows > 0").fetchall():
    a, b = divmod(pid, MAX_ID)
    if names[a][:2] == names[b][:2]:
        continue
    for i in (a, b):
        if i not in masks:
            masks[i] = wallpaper_mask(images_dir / names[i])
    m = np.frombuffer(blob, np.uint32).reshape(rows, 2)
    pa, pb = kps[a][m[:, 0]].astype(int), kps[b][m[:, 1]].astype(int)
    on_paper = masks[a][pa[:, 1].clip(0, 1079), pa[:, 0].clip(0, 1919)] | masks[b][pb[:, 1].clip(0, 1079), pb[:, 0].clip(0, 1919)]
    keep = m[~on_paper]
    stats["pairs"] += 1; stats["matches_in"] += rows; stats["matches_out"] += len(keep)
    if len(keep) < min_matches:
        stats["dropped"] += 1
        con.execute("DELETE FROM two_view_geometries WHERE pair_id = ?", (pid,))
    else:
        con.execute("UPDATE two_view_geometries SET rows = ?, data = ? WHERE pair_id = ?",
                    (len(keep), np.ascontiguousarray(keep).tobytes(), pid))
con.commit()
print(f"cross pairs {stats['pairs']}: dropped {stats['dropped']}, kept {stats['pairs'] - stats['dropped']}; "
      f"cross matches {stats['matches_in']} -> {stats['matches_out']}")
