import json, os, sys
from PIL import Image
R = sys.argv[1]; OUT = sys.argv[2]
V = R + "/spec/captures/views/"; F = lambda n: f"{R}/0-homealone/full/homealone-movie-screencaps.com-{n}.jpg"
M = lambda room, n: f"{R}/sfm-work/rooms/{room}/colmap/images/shot00/f_{n:05d}.jpg"
C = R + "/spec/captures/compare-marina/web/"
P = [  # room, label, ref, render, source kind, note
 ("Foyer", "Film 1616: front door to stair", F(1616), V+"purchased/after-film-1616.png", "film", ""),
 ("Foyer", "Film 2677: stair and arch", F(2677), V+"purchased/after-film-2677.png", "film", "Arch still the old stepped version"),
 ("Foyer", "Film 10248: vestibule", F(10248), V+"foyer-finish/after-film-10248.png", "film", ""),
 ("Foyer", "Marina 312 s", C+"marina-312-ref.jpg", V+"foyer-finish/after-marina-312.png", "marina", ""),
 ("Foyer", "Marina 1068 s", C+"marina-1068-ref.jpg", V+"foyer-finish/after-marina-1068.png", "marina", ""),
 ("Living room", "Film 10600: tree and fireplace", F(10600), V+"living/tree-after-film10600.png", "film", "Pose by eye (no solved film camera)"),
 ("Living room", "Film 10636: through the foyer opening", F(10636), V+"living/tree-after-film10636.png", "film", "Pose by eye"),
 ("Living room", "Film 5650: train and piano", F(5650), V+"living/tree-after-film5650.png", "film", "Pose by eye"),
 ("Living room", "Marina f165: fireplace wall", M("living",165), V+"living/tree-after-f165.png", "marina", ""),
 ("Living room", "Marina f89", M("living",89), V+"living/tree-after-f89.png", "marina", ""),
 ("Den", "Marina f9", M("den",9), V+"den/after-f9.png", "marina", ""),
 ("Den", "Marina f57", M("den",57), V+"den/after-f57.png", "marina", ""),
 ("Den", "Marina f153", M("den",153), V+"den/after-f153.png", "marina", ""),
 ("Den", "Marina f161", M("den",161), V+"den/after-f161.png", "marina", ""),
 ("Den", "Film 2877 (night)", F(2877), V+"shadows/after/den/night-film2877.png", "film", "Batch render; nights read warmer than the film"),
 ("Den", "Film 2868 (night)", F(2868), V+"shadows/after/den/night-film2868.png", "film", "Batch render; nights read warmer than the film"),
 ("Dining", "Marina 228 s", V+"dining/marina-228-ref.png", V+"dining/marina-228.png", "marina", ""),
 ("Kitchen", "Film 6902", F(6902), V+"kitchen/after-paper-film6902.png", "film", ""),
 ("Kitchen", "Film 6910", F(6910), V+"kitchen/after-paper-film6910.png", "film", ""),
 ("Kitchen", "Film 9812", F(9812), V+"kitchen/after-day-film9812.png", "film", ""),
 ("Kitchen", "Film 1151: breakfast area", F(1151), V+"kitchen/after-fix-film1151.png", "film", "Table: film has a single pedestal (queued)"),
 ("Kitchen", "Film 2528", F(2528), V+"kitchen/after-table-film2528.png", "film", ""),
 ("Kitchen", "Film 10448 (night)", F(10448), V+"shadows/after/kitchen/after-night-film10448.png", "film", "Batch render; nights read warmer"),
 ("Kitchen", "Film 10452 (night)", F(10452), V+"shadows/after/kitchen/after-night-film10452.png", "film", "Batch render; nights read warmer"),
 ("Kitchen", "Film 6042 (night)", F(6042), V+"shadows/after/kitchen/after-night-film6042.png", "film", "Batch render; nights read warmer"),
 ("Upstairs hall (WIP)", "Film 2085: hall arch", F(2085), V+"hall/after-film2085.png", "film", "Paused work in progress"),
 ("Upstairs hall (WIP)", "Film 2055: sconces", F(2055), V+"hall/after-film2055.png", "film", "Paused work in progress"),
 ("Upstairs hall (WIP)", "Film 2687", F(2687), V+"hall/after-film2687.png", "film", "Paused work in progress"),
 ("Upstairs hall (WIP)", "Film 10819", F(10819), V+"hall/after-film10819.png", "film", "Paused work in progress"),
 ("Upstairs hall (WIP)", "Film 410", F(410), V+"hall/after-film410.png", "film", "Paused work in progress"),
]
W = 1280; out = []
for i, (room, label, ref, ren, kind, note) in enumerate(P):
    if not (os.path.exists(ref) and os.path.exists(ren)): print("MISSING", label, ref if not os.path.exists(ref) else ren); continue
    a = Image.open(ref).convert("RGB"); b = Image.open(ren).convert("RGB")
    H = round(W * a.height / a.width)   # ref aspect wins; render centre-cropped to it
    bw, bh = b.size; th = round(bw * a.height / a.width)
    if th <= bh: b = b.crop((0, (bh - th) // 2, bw, (bh - th) // 2 + th))
    a = a.resize((W, H), Image.LANCZOS); b = b.resize((W, H), Image.LANCZOS)
    a.save(f"{OUT}/img/{i:02d}r.jpg", quality=80); b.save(f"{OUT}/img/{i:02d}b.jpg", quality=80)
    out.append(dict(room=room, label=label, kind=kind, note=note, ref=f"img/{i:02d}r.jpg", ren=f"img/{i:02d}b.jpg", w=W, h=H,
                    when=__import__("time").strftime("%b %d %H:%M", __import__("time").localtime(os.path.getmtime(ren)))))
json.dump(out, open(f"{OUT}/pairs.json", "w"), indent=1); print(len(out), "pairs")
