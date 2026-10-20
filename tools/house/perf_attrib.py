#!/usr/bin/env python3
"""perf_attrib.py: name the cause of each pose's heavy frames from a PerfProbe tour's per-frame tags (deterministic attribution).

  python3 tools/house/perf_attrib.py RUN_DIR [--selftest]     (perf_probe.sh attrib LABEL)

A development player's tour writes frame_log per pose (PerfProbe.cs): frame ms, profiler GPU ms, GC runs, ShadowRefresh shadow-map
requests, reflection-camera renders (realtime planar mirrors / probes), lights on, and HDRP/core profiler markers (CPU us).
Heavy frame: ms > max(2 x median, median + 8). A tag "fires" on a frame when a count is > 0, the light count changes, or a marker
takes > 2 x its median and > 200 us. Profiler values arrive a frame late, so each tag is tested at lag -1, 0 and +1 and the best lag
kept. Gfx.WaitForPresentOnGfxThread on the heavy frames names the BOUND (GPU), not a cause. A cause is named when it fires on >= 50% of heavy frames and at >= 3x its rate on normal frames; otherwise "unattributed"
(the cost is then inside the GPU frame: compare GPU ms heavy vs normal).
"""
import json
import statistics as st
import sys
from pathlib import Path


PRESENT = "Gfx.WaitForPresentOnGfxThread"


def fires(log):
    n = len(log["ms"])
    out = {k: [v > 0 for v in log[k]] for k in ("gc", "shadow_requests", "reflection_renders") if k in log}
    if "lights_on" in log:
        lo = log["lights_on"]; out["lights_changed"] = [i > 0 and lo[i] != lo[i - 1] for i in range(n)]
    for name, us in log.get("markers_us", {}).items():
        m = st.median(us) if us else 0
        out[name] = [u > 2 * m and u > 200 for u in us]
    return out


def attribute(log):
    ms = log["ms"]; med = st.median(ms); thr = max(2 * med, med + 8)
    heavy = [i for i, v in enumerate(ms) if v > thr]; normal = [i for i, v in enumerate(ms) if v <= thr]
    causes = []
    for tag, f in fires(log).items():
        best = None
        for lag in (-1, 0, 1):
            at = lambda i: 0 <= i + lag < len(f) and f[i + lag]
            h = sum(at(i) for i in heavy) / len(heavy) if heavy else 0
            b = sum(at(i) for i in normal) / len(normal) if normal else 0
            if best is None or h > best[1]:
                best = (lag, h, b)
        lag, h, b = best
        if h >= 0.5 and h >= 3 * max(b, 0.01):
            causes.append((tag, h, b, lag))
    # the render thread blocked on present = the GPU is behind (Metal queues frames: fast frames, then one that waits): that names
    # the bound, not a cause; the cause is whatever else fires
    bound = next((c for c in causes if c[0] == PRESENT), None); causes = [c for c in causes if c[0] != PRESENT]
    g = log.get("gpu_ms", [])
    gpu = lambda idx: st.median([g[i] for i in idx if i < len(g) and g[i] > 0]) if any(i < len(g) and g[i] > 0 for i in idx) else None
    return dict(bound="GPU (waits for present)" if bound else "-", mean=st.mean(ms), median=med, thr=thr, heavy=len(heavy), n=len(ms), heavy_ms=st.median([ms[i] for i in heavy]) if heavy else None,
                gpu_heavy=gpu(heavy), gpu_normal=gpu(normal), causes=sorted(causes, key=lambda c: -c[1]))


def main(d):
    print("| pose | frame mean (fps) | frame p50 | heavy frames | heavy ms | bound | named cause (heavy % vs normal %, lag) |\n|---|---|---|---|---|---|---|")
    for p in sorted(Path(d).glob("*.json")):
        log = json.loads(p.read_text()).get("frame_log")
        if not log:
            continue
        a = attribute(log)
        c = "; ".join(f"{t} {h:.0%} vs {b:.0%} ({l:+d})" for t, h, b, l in a["causes"]) or ("unattributed" if a["heavy"] else "-")
        f = lambda v: "-" if v is None else f"{v:.1f}"
        print(f"| {p.stem} | {a['mean']:.1f} ({1000 / a['mean']:.0f}) | {a['median']:.1f} | {a['heavy']}/{a['n']} | {f(a['heavy_ms'])} | {a['bound']} | {c} |")


def selftest():
    ms = [10.0] * 100; gc = [0] * 100
    for i in range(5, 100, 10):
        ms[i] = 60.0; gc[i - 1] = 1   # GC on the frame before each spike
    a = attribute({"ms": ms, "gc": gc, "markers_us": {"RenderShadowMaps": [300] * 100}})
    assert a["heavy"] == 10 and a["causes"][0][0] == "gc" and a["causes"][0][3] == -1, a
    assert not any(c[0] == "RenderShadowMaps" for c in a["causes"])
    print("selftest ok")


if __name__ == "__main__":
    selftest() if "--selftest" in sys.argv else main(sys.argv[1])
