"""Table of a PerfProbe standalone tour (tools/house/perf_probe.sh), or before vs after.

  perf_table.py RUN_DIR             -> one row per pose
  perf_table.py BEFORE_DIR AFTER_DIR -> before -> after per metric, plus the mean RGB difference of the pose PNGs (0-255;
                                       > ~3 means the picture changed: look at both PNGs)
  perf_table.py --gate RUN_DIR [MD]  -> exit 1 if any pose's frame mean (or a motion step's time to rest) is over its budget in the
                                       "## BUDGET" table of docs/PERFORMANCE.md (first matching pose pattern wins)
  perf_table.py --sheet RUN_DIR [POSE ...] -> RUN_DIR/sheet.jpg: the visual comparison (pose rows x variant columns, FPS on each tile)
  perf_table.py --selftest
"""
import fnmatch
import re
import json
import sys
from pathlib import Path

# cpu_ms_* is the frame's wall time (unscaledDeltaTime): "frame p50/p95/p99". main/render ms are the threads' busy time per frame
# (FrameTiming): GPU ms well above both = GPU-bound. Older runs lack the GPU p95 / thread columns ("-").
COLS = [("frame_ms_mean", "frame mean"), ("cpu_ms_median", "frame p50"), ("cpu_ms_p95", "frame p95"), ("cpu_ms_p99", "frame p99"), ("gpu_ms_p10", "GPU p10"), ("gpu_ms_median", "GPU p50"),
        ("gpu_ms_p95", "GPU p95"), ("main_ms_median", "main ms"), ("render_ms_median", "render ms"), ("triangles", "tris M"), ("setpass", "setpass"),
        ("shadow_casters", "shadow casters"), ("rt_lights", "rt lights"), ("rt_shadow_lights", "rt shadow lights"), ("sys_mem_mb", "sys MB")]
DEV_COLS = [("draw_calls", "draw calls"), ("batches", "batches"), ("gfx_mem_mb", "gfx MB")]   # 0 in a release player: shown when counted


def load(d):
    out = {p.stem: json.loads(p.read_text()) for p in sorted(Path(d).glob("*.json"))}
    for r in out.values():
        ms = r.get("frame_log", {}).get("ms")
        if ms:   # Metal queues frames (fast ones, then one that waits for present): the MEAN is the real frame time, p50 is not
            r["frame_ms_mean"] = round(sum(ms) / len(ms), 1)
    for r in out.values():   # FrameTiming's GPU time is sparse on Metal: fall back to the profiler's GPU Frame Time (development player)
        g = [v for v in r.get("frame_log", {}).get("gpu_ms", []) if v > 0]
        if g and r.get("gpu_ms_median") is None:
            g.sort(); q = lambda f: g[min(int(f * (len(g) - 1)), len(g) - 1)]
            r.update(gpu_ms_median=q(0.5), gpu_ms_p10=q(0.1), gpu_ms_p95=q(0.95), gpu_ms_p99=q(0.99))
    return out


def fmt(k, v):
    if v is None:
        return "-"
    return f"{v / 1e6:.2f}" if k == "triangles" else (f"{v:.1f}" if isinstance(v, float) else str(v))


def fps(ms):
    return round(1000.0 / ms) if ms else 0


def sheet(d, poses=None, out=None):
    """A visual comparison sheet for one -perfab run (user, Oct 20: every shadow/lighting change gets one): one row per pose, one column
    per variant (A = base), each tile labelled with its variant and FPS. Variant names come from args.txt (perf_probe.sh run writes it)."""
    from PIL import Image, ImageDraw, ImageFont
    d = Path(d); names = {"A": "base"}
    a = (d / "args.txt").read_text() if (d / "args.txt").exists() else ""
    m = re.search(r"-perfvariants\s+['\"]?([^'\"]+)", a)
    for i, v in enumerate(m.group(1).split(";") if m else []):
        names[chr(ord("B") + i)] = v.strip()
    last = max((int(q.stem[-1]) for q in d.glob("*-A?.json")), default=1)
    letters = ["A"] + sorted({q.stem[-2] for q in d.glob(f"*-?{last}.png")} - {"A"})
    poses = poses or sorted({q.stem[:-3] for q in d.glob(f"*-A{last}.png")})
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 22)
    except OSError:
        font = ImageFont.load_default()
    W = 640; rows = []
    for p in poses:
        row = []
        for x in letters:
            png, js = d / f"{p}-{x}{last}.png", d / f"{p}-{x}{last}.json"
            if not png.exists():
                continue
            im = Image.open(png).convert("RGB"); im = im.resize((W, int(im.height * W / im.width)))
            r = load(d).get(f"{p}-{x}{last}", {}); ms = r.get("frame_ms_mean")
            dr = ImageDraw.Draw(im); dr.rectangle([0, 0, W, 32], fill=(0, 0, 0))
            dr.text((8, 4), f"{p}  {names.get(x, x)}  {fps(ms) if ms else '?'} fps", fill=(255, 255, 255), font=font)
            row.append(im)
        if row:
            rows.append(row)
    if not rows:
        return None
    sh = Image.new("RGB", (max(sum(i.width + 8 for i in r) for r in rows), sum(r[0].height + 8 for r in rows)), (20, 20, 20)); y = 0
    for r in rows:
        x = 0
        for i in r:
            sh.paste(i, (x, y)); x += i.width + 8
        y += r[0].height + 8
    out = Path(out or d / "sheet.jpg"); sh.save(out, quality=88); print(f"sheet: {out}"); return out


def img_diff(a, b):
    try:
        import numpy as np
        from PIL import Image
    except ImportError:
        return None
    if not (a.exists() and b.exists()):
        return None
    x = np.asarray(Image.open(a).convert("RGB"), dtype=float)
    y = np.asarray(Image.open(b).convert("RGB"), dtype=float)
    return float(abs(x - y).mean()) if x.shape == y.shape else None


def ab(base, variant, pngs=None):
    """Base vs variant, each a list of (run dir, tag suffix) samples, e.g. [(run, "-A1"), (run, "-A2")] for one -perfab run, or
    [(runA1, ""), (runA2, "")] for two builds run alternately (perf_probe.sh ab). Means of GPU p10 / median, CPU median, triangles."""
    def side(samples):
        out = {}
        for d, suf in samples:
            for k, v in load(d).items():
                if k.endswith(suf) and (suf or k[-3:-1] not in ("-A", "-B")):
                    out.setdefault(k[: len(k) - len(suf)] if suf else k, []).append(v)
        return out
    A, B = side(base), side(variant)
    print("| pose | FPS base -> variant (frame mean ms) | GPU p10 | GPU median | frame p50 | tris M | shadow casters | img diff |\n|---|---|---|---|---|---|---|---|")
    for p in sorted(set(A) & set(B)):
        cells = []
        for key in ("frame_ms_mean", "gpu_ms_p10", "gpu_ms_median", "cpu_ms_median", "triangles", "shadow_casters"):
            v = [[r[key] for r in X[p] if r.get(key) is not None] for X in (A, B)]
            m = [sum(x) / len(x) if x else 0 for x in v]
            sc = 1e6 if key == "triangles" else 1
            if key == "frame_ms_mean" and m[0] and m[1]:   # user, Oct 20: report FPS (ms kept beside it: ms add up, fps don't)
                cells.append(f"{fps(m[0])} -> {fps(m[1])} fps ({m[0]:.1f} -> {m[1]:.1f} ms, {(fps(m[1]) - fps(m[0])) / fps(m[0]) * 100:+.0f}% fps)"); continue
            cells.append(f"{m[0] / sc:.1f} -> {m[1] / sc:.1f} ({(m[1] - m[0]) / m[0] * 100:+.0f}%)" if m[0] else "-")
        d = img_diff(*[Path(x) for x in pngs(p)]) if pngs else None
        print(f"| {p} | " + " | ".join(cells) + f" | {'-' if d is None else f'{d:.1f}'} |")


def budgets(md):
    """rows of the '## BUDGET' table: (pose glob, mean ms, rest s or None)"""
    text = Path(md).read_text(); sec = text[text.index("## BUDGET"):]
    rows = []
    for line in sec.splitlines()[1:]:
        if line.startswith("## "):
            break
        m = re.match(r"\|\s*`?([\w*?\-]+)`?\s*\|\s*([\d.]+)\s*\|\s*([\d.]+|-)\s*\|", line)
        if m:
            rows.append((m[1], float(m[2]), None if m[3] == "-" else float(m[3])))
    return rows


def gate(run, md):
    rows, bad = budgets(md), 0
    poses = {k: v for k, v in load(run).items() if not re.search(r"-[A-Z]\d$", k)}   # -perfab samples are not the shipped state
    if not poses:
        print(f"FAIL perf gate: no poses in {run}"); return 1
    for pose, r in sorted(poses.items()):
        b = next((x for x in rows if fnmatch.fnmatch(pose, x[0])), None)
        if b is None:
            print(f"FAIL {pose}: no budget row"); bad += 1; continue
        mean, rest = r.get("frame_ms_mean"), r.get("rest_s")
        over = mean is None or mean > b[1] or (b[2] is not None and (rest is None or rest < 0 or rest > b[2]))
        bad += over
        print(f"{'FAIL' if over else 'ok  '} {pose}: mean {mean} ms (budget {b[1]})" + (f", rest {rest} s (budget {b[2]})" if b[2] is not None else ""))
    print(f"perf gate: {'FAILED' if bad else 'ok'} ({bad} over budget, {len(poses)} poses)")
    return 1 if bad else 0


def selftest():
    import tempfile
    with tempfile.TemporaryDirectory() as t:
        t = Path(t)
        (t / "PERF.md").write_text("## BUDGET\n| pose | mean ms | rest s |\n|---|---|---|\n| door-* | 13.7 | 2 |\n| * | 13.7 | - |\n## next\n")
        (t / "foyer-day.json").write_text(json.dumps({"frame_log": {"ms": [10, 12]}}))
        (t / "foyer-day-B1.json").write_text(json.dumps({"frame_log": {"ms": [99]}}))   # an A/B sample: ignored
        (t / "door-day.json").write_text(json.dumps({"frame_log": {"ms": [10]}, "rest_s": 1.0}))
        assert gate(t, t / "PERF.md") == 0
        (t / "door-day.json").write_text(json.dumps({"frame_log": {"ms": [10]}, "rest_s": 3.0}))
        assert gate(t, t / "PERF.md") == 1
        (t / "door-day.json").write_text(json.dumps({"frame_log": {"ms": [20]}, "rest_s": 1.0}))
        assert gate(t, t / "PERF.md") == 1
    print("selftest ok")


def main(args):
    if args[0] == "--selftest":
        return selftest()
    if args[0] == "--gate":
        sys.exit(gate(args[1], args[2] if len(args) > 2 else Path(__file__).resolve().parents[2] / "docs/PERFORMANCE.md"))
    if args[0] == "--sheet":   # --sheet RUN_DIR [POSE ...]
        return sheet(args[1], args[2:] or None)
    if args[0] == "--ab":   # --ab A1 B1 A2 B2 ...: alternate tours of two builds
        return ab([(d, "") for d in args[1::2]], [(d, "") for d in args[2::2]])
    if len(args) == 1 and any(Path(args[0]).glob("*-A1.json")):   # one -perfab run: A (base) vs each variant B, C, ... (-perfvariants)
        d = Path(args[0]); letters = sorted({q.stem[-2] for q in d.glob("*-?1.json")} - {"A"})
        last = max(int(q.stem[-1]) for q in d.glob("*-A?.json"))   # -perfrounds: the PNGs are the last round's
        for x in letters:
            print(f"\nvariant {x} (base A):")
            ab([(d, f"-A{i}") for i in range(1, last + 1)], [(d, f"-{x}{i}") for i in range(1, last + 1)], lambda p, x=x: (d / f"{p}-A{last}.png", d / f"{p}-{x}{last}.png"))
        return
    runs = [load(d) for d in args]
    cols = COLS + [c for c in DEV_COLS if any(r.get(c[0]) for run in runs for r in run.values())]
    head = ["pose"] + [c[1] for c in cols] + (["img diff"] if len(runs) == 2 else [])
    print("| " + " | ".join(head) + " |")
    print("|" + "---|" * len(head))
    for pose in runs[-1]:
        cells = [pose]
        for k, _ in cols:
            vals = [fmt(k, r.get(pose, {}).get(k)) for r in runs]
            cells.append(" -> ".join(vals))
        if len(runs) == 2:
            d = img_diff(Path(args[0]) / f"{pose}.png", Path(args[1]) / f"{pose}.png")
            cells.append("-" if d is None else f"{d:.1f}")
        print("| " + " | ".join(cells) + " |")


if __name__ == "__main__":
    if not sys.argv[1:] or (sys.argv[1] not in ("--ab", "--gate", "--sheet") and len(sys.argv) > 3):
        sys.exit(__doc__)
    main(sys.argv[1:])
