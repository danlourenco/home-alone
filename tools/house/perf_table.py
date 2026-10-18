"""Table of a PerfProbe standalone tour (tools/house/perf_probe.sh), or before vs after.

  perf_table.py RUN_DIR             -> one row per pose
  perf_table.py BEFORE_DIR AFTER_DIR -> before -> after per metric, plus the mean RGB difference of the pose PNGs (0-255;
                                       > ~3 means the picture changed: look at both PNGs)
"""
import json
import sys
from pathlib import Path

COLS = [("gpu_ms_p10", "GPU ms p10"), ("gpu_ms_median", "GPU ms"), ("cpu_ms_median", "CPU ms"), ("triangles", "tris M"), ("setpass", "setpass"), ("shadow_casters", "shadow casters"), ("rt_lights", "rt lights"),
        ("rt_shadow_lights", "rt shadow lights"), ("sys_mem_mb", "sys MB")]
# batches / draw calls / gfx memory are 0 in a release player (Unity only counts them in development builds): kept in the JSON, not shown


def load(d):
    return {p.stem: json.loads(p.read_text()) for p in sorted(Path(d).glob("*.json"))}


def fmt(k, v):
    if v is None:
        return "-"
    return f"{v / 1e6:.2f}" if k == "triangles" else (f"{v:.1f}" if isinstance(v, float) else str(v))


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


def ab(base, variant):
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
    print("| pose | GPU p10 base -> variant | GPU median | CPU median | tris M |\n|---|---|---|---|---|")
    for p in sorted(set(A) & set(B)):
        cells = []
        for key in ("gpu_ms_p10", "gpu_ms_median", "cpu_ms_median", "triangles"):
            v = [[r[key] for r in X[p] if r.get(key) is not None] for X in (A, B)]
            m = [sum(x) / len(x) if x else 0 for x in v]
            sc = 1e6 if key == "triangles" else 1
            cells.append(f"{m[0] / sc:.1f} -> {m[1] / sc:.1f} ({(m[1] - m[0]) / m[0] * 100:+.0f}%)" if m[0] else "-")
        print(f"| {p} | " + " | ".join(cells) + " |")


def main(args):
    if args[0] == "--ab":   # --ab A1 B1 A2 B2 ...: alternate tours of two builds
        return ab([(d, "") for d in args[1::2]], [(d, "") for d in args[2::2]])
    if len(args) == 1 and any(Path(args[0]).glob("*-A1.json")):   # one -perfab run
        return ab([(args[0], "-A1"), (args[0], "-A2")], [(args[0], "-B1"), (args[0], "-B2")])
    runs = [load(d) for d in args]
    head = ["pose"] + [c[1] for c in COLS] + (["img diff"] if len(runs) == 2 else [])
    print("| " + " | ".join(head) + " |")
    print("|" + "---|" * len(head))
    for pose in runs[-1]:
        cells = [pose]
        for k, _ in COLS:
            vals = [fmt(k, r.get(pose, {}).get(k)) for r in runs]
            cells.append(" -> ".join(vals))
        if len(runs) == 2:
            d = img_diff(Path(args[0]) / f"{pose}.png", Path(args[1]) / f"{pose}.png")
            cells.append("-" if d is None else f"{d:.1f}")
        print("| " + " | ".join(cells) + " |")


if __name__ == "__main__":
    if not sys.argv[1:] or (sys.argv[1] != "--ab" and len(sys.argv) > 3):
        sys.exit(__doc__)
    main(sys.argv[1:])
