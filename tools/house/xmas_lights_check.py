#!/usr/bin/env python3
"""xmas_lights_check: scores a night render's Christmas lights against the film (docs/XMAS-LIGHTS.md, acceptance criteria).

The film authority is frame 5545 (McCallister front at night, warm C7s round every window). Our tour pose is front6399 (film 6399's
solved camera, a day frame) or any pose with the same two upper front windows in view: every metric is in METRES or a scale-free
ratio, measured on two windows whose outline size is known (exterior_shell.py UPW_LIST: 0.86 x 1.34 m openings, the strand 0.08 m
outside the casing and 0.09 m under the sill: a 1.02 x 1.51 m loop), so the two framings need not match.

Per window (a quad of the bulb loop's four corners in image px, picked once per pose on a gridded crop, see QUADS):
  pitch_m      perimeter / bulbs found along the loop (1-D luminance profile, max across the band, local maxima with prominence)
  glow_m       half-maximum glow diameter of a bulb (core + shoulder), median over the bulbs, in metres
  halo_m       radius where the glow falls to 15% of (peak - background): bloom's reach, in metres
  warmth       (R - B) / (R + G + B) of the halo shoulder (15%-max blob minus the half-max core): the bulb's colour where it doesn't clip
  bulb_brick   mean glow luminance / mean brick luminance beside the window (the spill: brick lit warm by the bulbs)
  brick_rb     brick R / B (film: warm red-brown under the strands; ours: blue-violet)
A metric passes inside the film's value times the TOL band. Score = passes / metrics. Exit 1 when any metric fails.

  uv run -q --with numpy --with pillow python -I tools/house/xmas_lights_check.py RUN.png [--pose front6399] [--json] [--sheet OUT.jpg]
  uv run -q --with numpy --with pillow python -I tools/house/xmas_lights_check.py --film      # the film's own numbers
  uv run -q --with numpy --with pillow python -I tools/house/xmas_lights_check.py --film-extra   # film bulb colour + steadiness
  uv run -q --with numpy --with pillow python -I tools/house/xmas_lights_check.py --scene [X.unity]   # practice: strand lights <= the
      pool (24), strand renderers <= 150 (chunked meshes, never a GameObject or a Light per bulb)
  uv run -q --with numpy --with pillow python -I tools/house/xmas_lights_check.py --selftest
"""
import json, math, sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
FILM = ROOT / "0-homealone/full/homealone-movie-screencaps.com-5545.jpg"
LOOP_W, LOOP_H = 1.02, 1.51   # metres: 0.86 + 2 x 0.08 wide, 1.34 + 0.09 + 0.08 tall (exterior_shell.xmas_lights, out / lo)

# bulb-loop corners TL, TR, BR, BL (px) of the 1st and 2nd upper front windows right of the den, and a brick patch (x0, y0, x1, y1)
# under them (picked on 4x / 6x gridded crops, Oct 21). frame size each was picked at: the image is rescaled to it.
QUADS = {
    "film5545": {"size": (1920, 1058),
                 "windows": [[(549, 316), (631, 315), (630, 437), (548, 438)], [(727, 315), (804, 315), (803, 437), (727, 437)]],
                 "brick": [(560, 452, 620, 470), (735, 452, 795, 470)]},
    "front6399": {"size": (1920, 1080),
                  "windows": [[(841, 440), (896, 444), (895, 527), (840, 523)], [(931, 449), (982, 453), (982, 535), (931, 527)]],
                  "brick": [(846, 534, 890, 548), (936, 541, 978, 555)]},
}
# pass band as (low, high) multipliers of the film's value (warmth: absolute +-). Wide enough for film grain and lens blur, tight enough
# that a 1-px white dot or a 3x-dense strand can never pass.
TOL = {"pitch_m": (0.8, 1.25), "glow_m": (0.65, 1.5), "halo_m": (0.6, 1.6), "warmth": (-0.05, 0.05), "bulb_brick": (0.6, 1.6),
       "brick_rb": (0.75, 1.33)}


def lum(a):
    return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]


def load(path, size):
    im = Image.open(path).convert("RGB")
    if im.size != tuple(size):
        im = im.resize(size, Image.LANCZOS)
    return np.asarray(im, dtype=np.float64)


def sample(L, x, y):
    """bilinear sample of L at float (x, y)"""
    h, w = L.shape; x = min(max(x, 0), w - 1.001); y = min(max(y, 0), h - 1.001)
    x0, y0 = int(x), int(y); fx, fy = x - x0, y - y0
    return (L[y0, x0] * (1 - fx) * (1 - fy) + L[y0, x0 + 1] * fx * (1 - fy) + L[y0 + 1, x0] * (1 - fx) * fy + L[y0 + 1, x0 + 1] * fx * fy)


def loop_profile(L, quad, band):
    """(points, profile): every 0.25 px along the quad's 4 edges, the max of L across +-band px perpendicular to the edge"""
    pts, prof = [], []
    for i in range(4):
        (ax, ay), (bx, by) = quad[i], quad[(i + 1) % 4]
        n = max(2, int(math.hypot(bx - ax, by - ay) * 4)); tx, ty = (bx - ax) / n, (by - ay) / n
        ln = math.hypot(tx, ty); nx, ny = -ty / ln, tx / ln
        for k in range(n):
            x, y = ax + tx * k, ay + ty * k
            vals = [sample(L, x + nx * o, y + ny * o) for o in np.arange(-band, band + 0.01, 0.5)]
            j = int(np.argmax(vals)); o = -band + 0.5 * j
            pts.append((x + nx * o, y + ny * o)); prof.append(vals[j])
    return pts, np.array(prof)


def peaks(prof, min_sep):
    """local maxima of a closed profile, each the max within +-min_sep samples and prominent over the loop's background"""
    p = np.convolve(np.concatenate([prof[-3:], prof, prof[:3]]), np.ones(3) / 3, "same")[3:-3]
    lo, hi = np.percentile(p, 15), np.percentile(p, 98); thr = lo + 0.30 * (hi - lo)
    n = len(p); out = []
    for i in range(n):
        if p[i] < thr: continue
        win = [p[(i + d) % n] for d in range(-min_sep, min_sep + 1)]
        if p[i] >= max(win) and (not out or i - out[-1] > min_sep): out.append(i)
    if len(out) > 1 and (out[0] + n - out[-1]) <= min_sep: out.pop()
    return out, lo


def blob(L, x, y, bg, frac, rmax):
    """pixels around (x, y) within rmax that are 4-connected to its brightest pixel and above bg + frac * (peak - bg)"""
    h, w = L.shape; cx, cy = int(round(x)), int(round(y)); r = int(math.ceil(rmax))
    x0, x1, y0, y1 = max(cx - r, 0), min(cx + r + 1, w), max(cy - r, 0), min(cy + r + 1, h)
    win = L[y0:y1, x0:x1]; sy, sx = np.unravel_index(np.argmax(win), win.shape); pk = win[sy, sx]
    thr = bg + frac * (pk - bg); seen = {(sy, sx)}; stack = [(sy, sx)]
    while stack:
        j, i = stack.pop()
        for dj, di in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            q = (j + dj, i + di)
            if 0 <= q[0] < win.shape[0] and 0 <= q[1] < win.shape[1] and q not in seen and win[q] > thr \
                    and (q[0] - sy) ** 2 + (q[1] - sx) ** 2 <= rmax * rmax:
                seen.add(q); stack.append(q)
    return [(y0 + j, x0 + i) for j, i in seen]


def measure(img, spec):
    """the six metrics for one image (H x W x 3 float, 0-255) and its QUADS entry"""
    L = lum(img); res = {"windows": []}; glow_px, halo_px, glow_rgb, halo_rgb, pitch, ppm_all = [], [], [], [], [], []
    for q in spec["windows"]:
        wpx = (math.dist(q[0], q[1]) + math.dist(q[3], q[2])) / 2; hpx = (math.dist(q[0], q[3]) + math.dist(q[1], q[2])) / 2
        ppm = (wpx / LOOP_W + hpx / LOOP_H) / 2; ppm_all.append(ppm)
        band = max(1.5, 0.035 * wpx)
        pts, prof = loop_profile(L, q, band)
        idx, bg = peaks(prof, max(6, int(0.045 * ppm * 4)))   # bulbs at least 4.5 cm (and 1.5 px) apart: closer is film grain (samples are 0.25 px)
        per_m = 2 * (LOOP_W + LOOP_H); n = len(idx); pitch.append(per_m / max(n, 1))
        for i in idx:
            x, y = pts[i]; rmax = max(2.0, 0.12 * ppm)
            g = blob(L, x, y, bg, 0.5, rmax); h_ = blob(L, x, y, bg, 0.15, max(3.0, 0.25 * ppm))
            glow_px.append(2 * math.sqrt(len(g) / math.pi) / ppm); halo_px.append(math.sqrt(len(h_) / math.pi) / ppm)
            ring = set(h_) - set(g) or set(g)   # the halo's shoulder carries the bulb's colour (the core clips to white)
            glow_rgb.append(np.mean([img[j, i_] for j, i_ in g], axis=0)); halo_rgb.append(np.mean([img[j, i_] for j, i_ in ring], axis=0))
        res["windows"].append({"bulbs": n, "px_per_m": round(ppm, 1), "pitch_m": round(per_m / max(n, 1), 3)})
    rgb = np.mean(glow_rgb, axis=0) if glow_rgb else np.zeros(3); hrgb = np.mean(halo_rgb, axis=0) if halo_rgb else np.zeros(3)
    brick = np.concatenate([img[y0:y1, x0:x1].reshape(-1, 3) for x0, y0, x1, y1 in spec["brick"]]); brgb = brick.mean(axis=0)
    res.update({
        "pitch_m": float(np.mean(pitch)), "glow_m": float(np.median(glow_px)) if glow_px else 0.0,
        "halo_m": float(np.median(halo_px)) if halo_px else 0.0,
        "warmth": float((hrgb[0] - hrgb[2]) / max(hrgb.sum(), 1e-6)),
        "bulb_brick": float(lum(rgb) / max(lum(brgb), 1e-6)), "brick_rb": float(brgb[0] / max(brgb[2], 1e-6)),
        "glow_rgb": [round(float(c), 1) for c in rgb], "halo_rgb": [round(float(c), 1) for c in hrgb], "brick_rgb": [round(float(c), 1) for c in brgb]})
    return res


def score(ours, film):
    rows, ok = [], 0
    for k, (lo, hi) in TOL.items():
        f, o = film[k], ours[k]
        band = (f + lo, f + hi) if k == "warmth" else (f * lo, f * hi)
        p = band[0] <= o <= band[1]; ok += p
        rows.append((k, f, o, band, p))
    return rows, ok


def film_metrics():
    return measure(load(FILM, QUADS["film5545"]["size"]), QUADS["film5545"])


def overlay(path, spec, out_crop):
    """the two windows' region with the loops and brick patches drawn, for the sheet"""
    from PIL import ImageDraw
    im = Image.fromarray(load(path, spec["size"]).astype(np.uint8)); d = ImageDraw.Draw(im)
    for q in spec["windows"]:   # corner marks only: a drawn loop would hide the bulbs
        for x, y in q: d.ellipse((x - 3, y - 3, x + 3, y + 3), outline=(0, 255, 120))
    for b in spec["brick"]: d.rectangle(b, outline=(80, 160, 255))
    xs = [x for q in spec["windows"] for x, _ in q]; ys = [y for q in spec["windows"] for _, y in q] + [b[3] for b in spec["brick"]]
    m = 0.25 * (max(xs) - min(xs)); return im.crop((int(min(xs) - m), int(min(ys) - m), int(max(xs) + m), int(max(ys) + m)))


def report(path, pose, as_json, sheet_out=None):
    spec = QUADS[pose]; ours = measure(load(path, spec["size"]), spec); film = film_metrics()
    rows, ok = score(ours, film)
    if sheet_out:
        sys.path.insert(0, str(Path(__file__).parent)); from sheet_tiles import sheet
        cap = "  ".join(f"{k} {o:.3f}{'' if p else '!'}" for k, f, o, b, p in rows)
        sheet([[(overlay(FILM, QUADS["film5545"], None), "film 5545"), (overlay(path, spec, None), f"{Path(path).name} {ok}/{len(rows)}")]],
              sheet_out, "xmas_lights_check: " + cap, cell=(720, 420))
    if as_json:
        print(json.dumps({"image": str(path), "pose": pose, "score": f"{ok}/{len(rows)}", "pass": ok == len(rows), "ours": ours,
                          "film": film, "rows": [dict(metric=k, film=f, ours=o, band=b, ok=p) for k, f, o, b, p in rows]}, indent=1))
    else:
        print(f"xmas_lights_check {path} ({pose}) vs film 5545")
        print(f"  bulbs found per window: ours {[w['bulbs'] for w in ours['windows']]}, film {[w['bulbs'] for w in film['windows']]}")
        print(f"  {'metric':11s} {'film':>8s} {'ours':>8s}  pass band")
        for k, f, o, b, p in rows:
            print(f"  {k:11s} {f:8.3f} {o:8.3f}  [{b[0]:.3f}, {b[1]:.3f}]  {'ok' if p else 'FAIL'}")
        print(f"  glow RGB ours {ours['glow_rgb']} film {film['glow_rgb']}; halo RGB ours {ours['halo_rgb']} film {film['halo_rgb']}; brick RGB ours {ours['brick_rgb']} film {film['brick_rgb']}")
        print(f"SCORE {ok}/{len(rows)} {'PASS' if ok == len(rows) else 'FAIL'}")
    return 0 if ok == len(rows) else 1


POOL_MAX, DRAWS_MAX = 24, 150   # real-time lights the strands may own (the pool), renderers they may add (chunks x bulb/wire/card + LODs)
SCENE = ROOT / "unity/HomeAlone/Assets/Scenes/House_WallGrid.unity"
LIGHT_NAMES = ("ShrubGlow", "XmasPool", "XmasSpill")   # the strands' lights, today's and the design's


def scene_check(path=SCENE):
    """practice check on the saved scene: Light components on strand objects (pool only) and strand renderers (chunked, not per bulb)"""
    import re
    name, comps = {}, []
    for doc in path.read_text(errors="replace").split("--- !u!")[1:]:
        head, _, body = doc.partition("\n"); cls, _, fid = head.partition(" &"); fid = fid.split()[0] if fid else ""
        if cls == "1":
            m = re.search(r"m_Name: (.*)", body); name[fid] = m.group(1).strip() if m else ""
        elif cls in ("108", "23"):
            m = re.search(r"m_GameObject: {fileID: (\d+)}", body); comps.append((cls, m.group(1) if m else ""))
    lights = sum(1 for c, g in comps if c == "108" and name.get(g, "").startswith(LIGHT_NAMES))
    rend = sum(1 for c, g in comps if c == "23" and re.match(r"(Xmas|NB_C7|XmasC7)", name.get(g, "")))
    ok = lights <= POOL_MAX and rend <= DRAWS_MAX
    print(f"xmas scene check {path.name}: strand lights {lights} (max {POOL_MAX}), strand renderers {rend} (max {DRAWS_MAX}) {'ok' if ok else 'FAIL'}")
    return 0 if ok else 1


def _maxf(a, r):
    """max filter of radius r (square), numpy only"""
    p = np.pad(a, r, mode="edge"); out = np.full_like(a, -np.inf)
    for dy in range(2 * r + 1):
        for dx in range(2 * r + 1): out = np.maximum(out, p[dy:dy + a.shape[0], dx:dx + a.shape[1]])
    return out


def film_extra():
    """the film's bulb colour (halo shoulder, linear light, local background removed, on bulbs against dark ground: the left tree and
    the shrubs) and steadiness (per-bulb peak variation across 5543-5550, the same locked-off shot about 0.5 s apart)"""
    F = lambda k: ROOT / f"0-homealone/full/homealone-movie-screencaps.com-{k}.jpg"
    im = np.asarray(Image.open(FILM).convert("RGB"), dtype=np.float64) / 255
    lin = np.where(im <= 0.04045, im / 12.92, ((im + 0.055) / 1.055) ** 2.4); L = lin @ [0.2126, 0.7152, 0.0722]
    yy, xx = np.mgrid[-6:7, -6:7]; d = np.hypot(yy, xx)
    for name, (y0, y1, x0, x1) in {"tree-left": (0, 700, 0, 200), "shrubs": (680, 900, 100, 900)}.items():
        r = L[y0:y1, x0:x1]; pk = np.argwhere((r == _maxf(r, 4)) & (r > 0.35)); sh = []
        for y, x in pk:
            w = lin[y + y0 - 6:y + y0 + 7, x + x0 - 6:x + x0 + 7]
            if w.shape[:2] != (13, 13): continue
            sh.append(w[(d >= 2) & (d < 4)].mean(0) - np.percentile(w.reshape(-1, 3), 10, axis=0))
        m = np.mean(sh, axis=0); print(f"colour {name}: {len(sh)} bulbs, shoulder linear RGB / R = {np.round(m / m[0], 3).tolist()}")
    ims = [np.asarray(Image.open(F(k)).convert("L"), dtype=np.float64)[300:700, 200:1850] for k in range(5543, 5551)]
    a = ims[2]; pk = np.argwhere((a == _maxf(a, 3)) & (a > 200))
    v = np.array([_maxf(b, 2)[pk[:, 0], pk[:, 1]] for b in ims]); rel = (v / v.mean(0)).std(0)
    print(f"steadiness 5543-5550: {len(pk)} bulbs, per-bulb relative std median {np.median(rel):.3f} p90 {np.percentile(rel, 90):.3f}")


def synth(pitch_m, glow_m, warm, ppm=60.0, size=(400, 300)):
    """a window loop of gaussian bulbs on a dark brick field: a known answer for the self-test"""
    W, H = size; img = np.zeros((H, W, 3)); img[...] = (40, 22, 18) if warm else (14, 14, 22)
    x0, y0 = 100.0, 60.0; w, h = LOOP_W * ppm, LOOP_H * ppm
    quad = [(x0, y0), (x0 + w, y0), (x0 + w, y0 + h), (x0, y0 + h)]
    per = 2 * (w + h); n = int(round(per / (pitch_m * ppm))); yy, xx = np.mgrid[0:H, 0:W]
    col = np.array((255, 190, 110)) if warm else np.array((250, 250, 255)); s = glow_m * ppm / 2.355
    for k in range(n):
        d = (k + 0.5) * per / n
        if d < w: x, y = x0 + d, y0
        elif d < w + h: x, y = x0 + w, y0 + d - w
        elif d < 2 * w + h: x, y = x0 + w - (d - w - h), y0 + h
        else: x, y = x0, y0 + h - (d - 2 * w - h)
        g = np.exp(-((xx - x) ** 2 + (yy - y) ** 2) / (2 * s * s))[..., None] * 1.6
        img = np.maximum(img, np.minimum(255, img + g * col))
    return img.clip(0, 255), {"size": size, "windows": [quad], "brick": [(int(x0) + 10, int(y0 + h) + 12, int(x0 + w) - 10, int(y0 + h) + 30)]}, n


def selftest():
    img, spec, n = synth(0.21, 0.06, True)
    m = measure(img, spec)
    assert m["windows"][0]["bulbs"] == n, (m["windows"], n)
    assert abs(m["pitch_m"] / 0.21 - 1) < 0.08, m["pitch_m"]
    assert 0.6 < m["glow_m"] / 0.06 < 1.6, m["glow_m"]
    assert m["warmth"] > 0.15, m["warmth"]
    dots, dspec, _ = synth(0.055, 0.012, False)   # today's look: dense, tiny, white
    d = measure(dots, dspec)
    assert d["pitch_m"] < 0.08 and d["glow_m"] < 0.035 and abs(d["warmth"]) < 0.05, d
    rows, ok = score(d, m); assert ok < len(rows), rows   # the dense white dots must fail against the warm loop
    rows, ok = score(m, m); assert ok == len(rows)
    if FILM.exists():
        f = film_metrics(); assert all(15 <= w["bulbs"] <= 35 for w in f["windows"]), f["windows"]   # film: ~24 C7s per upper loop
        sp = QUADS["film5545"]; s = 0.67   # the film at our pose's scale (front6399 ~54 px/m vs 5545 ~80) must still pass: metric, not px
        im = Image.open(FILM).convert("RGB").resize((round(sp["size"][0] * s), round(sp["size"][1] * s)), Image.LANCZOS)
        small = {"windows": [[(x * s, y * s) for x, y in w] for w in sp["windows"]], "brick": [tuple(round(v * s) for v in b) for b in sp["brick"]]}
        rows, ok = score(measure(np.asarray(im, dtype=np.float64), small), f); assert ok == len(rows), rows
        ex = Path.home() / ".cache/home-alone-perf/runs/fr-NB9/front6399-night-A1.png"
        if ex.exists():
            rows, ok = score(measure(load(ex, QUADS["front6399"]["size"]), QUADS["front6399"]), f)
            assert ok < len(rows), "today's look (NB9) must fail"
    import tempfile   # the scene check: 25 strand lights fail, 24 pass, an unrelated lamp is not counted
    def yaml(n):
        docs = [f"--- !u!1 &{10 + i}\nGameObject:\n  m_Name: XmasPool_{i}\n--- !u!108 &{500 + i}\nLight:\n  m_GameObject: {{fileID: {10 + i}}}\n" for i in range(n)]
        return "%YAML 1.1\n" + "".join(docs) + "--- !u!1 &9\nGameObject:\n  m_Name: Light_Foyer\n--- !u!108 &8\nLight:\n  m_GameObject: {fileID: 9}\n"
    with tempfile.TemporaryDirectory() as td:
        for n, want in ((POOL_MAX, 0), (POOL_MAX + 1, 1)):
            f = Path(td) / "s.unity"; f.write_text(yaml(n)); assert scene_check(f) == want, n
    print("xmas_lights_check selftest ok")
    return 0


if __name__ == "__main__":
    a = sys.argv[1:]
    if "--selftest" in a: sys.exit(selftest())
    if "--scene" in a: sys.exit(scene_check(Path(a[a.index("--scene") + 1]) if len(a) > a.index("--scene") + 1 else SCENE))
    if "--film-extra" in a: film_extra(); sys.exit(0)
    if "--film" in a: print(json.dumps(film_metrics(), indent=1)); sys.exit(0)
    if not a or a[0].startswith("-"): print(__doc__); sys.exit(2)
    pose = a[a.index("--pose") + 1] if "--pose" in a else "front6399"
    sys.exit(report(Path(a[0]), pose, "--json" in a, a[a.index("--sheet") + 1] if "--sheet" in a else None))
