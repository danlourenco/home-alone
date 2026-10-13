"""Drop cross-video match pairs that a single homography explains (planar-only, e.g. repeating wallpaper).
Writes a filtered copy of the database; the original is untouched.
usage: uv run --with numpy --with opencv-python-headless python -I tools/sfm/drop_planar_links.py <db> <out_db> [planar_frac=0.8]
"""
import shutil
import sqlite3
import sys

import cv2
import numpy as np

MAX_ID = 2147483647
src_db, out_db = sys.argv[1], sys.argv[2]
planar_frac = float(sys.argv[3]) if len(sys.argv) > 3 else 0.8
shutil.copyfile(src_db, out_db)
con = sqlite3.connect(out_db)
video = {i: n[:2] for i, n in con.execute("SELECT image_id, name FROM images")}
kps = {}
for i, rows, cols, blob in con.execute("SELECT image_id, rows, cols, data FROM keypoints"):
    kps[i] = np.frombuffer(blob, np.float32).reshape(rows, cols)[:, :2]

drop, keep = [], []
for pid, rows, blob in con.execute("SELECT pair_id, rows, data FROM two_view_geometries WHERE rows > 0").fetchall():
    a, b = divmod(pid, MAX_ID)
    if video[a] == video[b]:
        continue
    m = np.frombuffer(blob, np.uint32).reshape(rows, 2)
    p, q = kps[a][m[:, 0]], kps[b][m[:, 1]]
    frac = 1.0
    if rows >= 8:
        _, mask = cv2.findHomography(p, q, cv2.RANSAC, 3.0)
        frac = mask.mean() if mask is not None else 1.0
    # ponytail: <8 matches treated as planar (too weak to trust as a cross-floor link)
    (drop if frac >= planar_frac else keep).append((pid, rows, frac))

con.executemany("DELETE FROM two_view_geometries WHERE pair_id = ?", [(d[0],) for d in drop])
con.commit()
print(f"cross-video pairs: {len(drop) + len(keep)}, dropped planar/weak: {len(drop)}, kept: {len(keep)}")
for pid, rows, frac in sorted(keep, key=lambda k: -k[1])[:10]:
    a, b = divmod(pid, MAX_ID)
    na, nb = (con.execute("SELECT name FROM images WHERE image_id=?", (x,)).fetchone()[0] for x in (a, b))
    print(f"  kept {na} <-> {nb}: {rows} inliers, homography explains {frac:.0%}")
