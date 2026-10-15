"""Baseline for the wall-grid rebuild (tasks/wall-grid-plan.md, phase 0 / V3): every room's size, every door's position
and the stair's key numbers, so any later rebuild can be diffed against them in feet and inches.
usage: uv run python -I tools/house/baseline.py              write measurements/baseline/pre-grid.json (refuses to overwrite)
       uv run python -I tools/house/baseline.py --diff       compare the current spec with it; exit 1 past --tol (m, default 0.05)
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "measurements/baseline/pre-grid.json"


def area(P):
    return 0.5 * abs(sum(x1 * z2 - x2 * z1 for (x1, z1), (x2, z2) in zip(P, P[1:] + P[:1])))


def snapshot():
    snap = {}
    for floor, f in (("upstairs", "spec/house_spec.json"), ("ground", "spec/house_spec.ground.json")):
        s = json.loads((ROOT / f).read_text())
        rooms = {}
        for r in s["spaces"]:
            xs, zs = [p[0] for p in r["polygon_xz"]], [p[1] for p in r["polygon_xz"]]
            rooms[r["name"]] = {"x": [min(xs), max(xs)], "z": [min(zs), max(zs)], "depth_x": round(max(xs) - min(xs), 4),
                                "width_z": round(max(zs) - min(zs), 4), "area": round(area(r["polygon_xz"]), 3), "ceiling": r["ceiling_m"]}
        doors = {f"{'/'.join(d['between'])}@{d['spec_axis']}={d['wall_coord_spec']:.2f}": {"coord": d["wall_coord_spec"], "span": d["span_spec"],
                 "width": d["width"], "kind": d["kind"]} for d in s["doors"]}
        snap[floor] = {"rooms": rooms, "doors": doors, "windows": len(s.get("windows") or [])}
        if s.get("stair"):
            snap[floor]["stair"] = {k: s["stair"].get(k) for k in ("rise_m", "going_m", "risers", "floor_to_floor_m") if k in s["stair"]}
    return snap


def ftin(m):
    t = abs(m) / 0.0254
    return f"{'-' if m < 0 else '+'}{int(t // 12)}' {t % 12:.1f}\""


def diff(old, new, tol):
    bad, lines = 0, []
    for floor in old:
        for name, a in old[floor]["rooms"].items():
            b = new[floor]["rooms"].get(name)
            if b is None:
                lines.append(f"{floor} {name}: GONE"); bad += 1; continue
            for k in ("depth_x", "width_z"):
                d = b[k] - a[k]
                if abs(d) > 0.0005:
                    flag = abs(d) > tol; bad += flag
                    lines.append(f"{'!!' if flag else '  '} {floor:8s} {name:20s} {k:8s} {a[k]:.3f} -> {b[k]:.3f} ({ftin(d)})")
        for name in new[floor]["rooms"].keys() - old[floor]["rooms"].keys():
            lines.append(f"   {floor} {name}: NEW")
        for key, a in old[floor]["doors"].items():
            m = [b for b in new[floor]["doors"].values() if b["kind"] == a["kind"] and abs(b["coord"] - a["coord"]) < 0.3
                 and abs(b["span"][0] - a["span"][0]) < 0.5]
            if not m:
                lines.append(f"!! {floor} door {key}: not found"); bad += 1; continue
            d = min((b["span"][0] - a["span"][0] for b in m), key=abs)
            if abs(d) > 0.0005:
                flag = abs(d) > tol; bad += flag
                lines.append(f"{'!!' if flag else '  '} {floor:8s} door {key}: moved {ftin(d)} along its wall")
    return bad, lines


if __name__ == "__main__":
    # self-check: a 6 cm change trips the 5 cm tolerance, a 1 cm change does not
    a = {"f": {"rooms": {"r": {"depth_x": 3.0, "width_z": 4.0}}, "doors": {}}}
    b = {"f": {"rooms": {"r": {"depth_x": 3.06, "width_z": 4.01}}, "doors": {}}}
    assert diff(a, b, 0.05)[0] == 1
    if "--diff" in sys.argv:
        tol = float(sys.argv[sys.argv.index("--tol") + 1]) if "--tol" in sys.argv else 0.05
        n, L = diff(json.loads(OUT.read_text()), snapshot(), tol)
        print("\n".join(L) or "no change")
        print(f"{n} change(s) past {tol * 100:.0f} cm")
        sys.exit(1 if n else 0)
    if OUT.exists():
        sys.exit(f"{OUT.relative_to(ROOT)} exists; the baseline is written once")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(snapshot(), indent=1))
    print("->", OUT.relative_to(ROOT))
