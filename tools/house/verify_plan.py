"""Verify a traced floor plan and its reconciled spec against independent measurements (.claude/skills/verify-plan).

Rebuilds the plan (overhead_plan.py) and spec (reconcile.py) from their inputs, then checks:
  1. reconciler flags: walls that overlap, doors with no wall or too little wall, failed body rules -> FAIL
  2. checkpoints (measurements/checkpoints/<floor>.json): measured doorways must land on the right door, measured
     open floor must be inside the right space, measured room sizes must match within tolerance -> FAIL on miss
  3. a zoomed review sheet of every traced space on the overhead (spec/captures/trace-review.png) for the eye pass
Exit code 1 on any FAIL, so it can gate the generator.
usage: uv run --with numpy --with matplotlib --with pillow python tools/house/verify_plan.py [--no-rebuild]
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/house"))
from reconcile import edges_of, rebuild  # noqa: E402

TRACE = ROOT / "measurements/overhead/upstairs-trace.json"
PLAN = ROOT / "measurements/overhead/upstairs-trace.plan.json"
SPEC = ROOT / "spec/house_spec.json"
CHECKS = ROOT / "measurements/checkpoints/upstairs.json"
HARD = ("too thin", "no shared wall", "on only", "rule failed", "needs", "conflict")


def inside(poly, pt):
    x, y = pt; c = False
    for (x1, y1), (x2, y2) in zip(poly, np.roll(poly, -1, 0)):
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            c = not c
    return c


def main():
    if "--no-rebuild" not in sys.argv:
        for cmd in (["uv", "run", "-q", "--with", "numpy", "--with", "matplotlib", "--with", "pillow", "python",
                     "tools/sfm/overhead_plan.py", str(TRACE.relative_to(ROOT))],
                    ["uv", "run", "-q", "--with", "numpy", "python", "tools/house/reconcile.py"]):
            subprocess.run(cmd, cwd=ROOT, check=True, capture_output=True)
    trace, plan, spec, checks = (json.loads(p.read_text()) for p in (TRACE, PLAN, SPEC, CHECKS))
    H = np.loadtxt(ROOT / trace["calibration"])
    o = np.array(spec["origin_plan_m"])
    to_spec = lambda p: np.array([p[1] - o[1], p[0] - o[0]])     # plan (x down, y right) -> spec (x, z)
    spaces = {s["name"]: np.array(s["polygon_xz"]) for s in spec["spaces"]}
    planpoly = {s["name"]: np.array(s["polygon_m"]) for s in plan["spaces"]}
    doors = {tuple(sorted(d["between"])): d for d in spec["doors"]}
    rows, fails = [], 0

    for f in spec["flags"]:
        hard = any(h in f.lower() for h in HARD)
        fails += hard
        rows.append(("FAIL" if hard else "warn", "reconciler", f))

    for c in checks["checks"]:
        if "overhead_px" in c:
            q = H @ np.r_[c["overhead_px"], 1]; pt = q[:2] / q[2]
        else:
            pt = np.array(c.get("plan", [0, 0]), float)
        ok, detail = False, ""
        if c["type"] == "on_door":
            d = doors.get(tuple(sorted(c["door"])))
            if not d:
                detail = f"no door between {c['door'][0]} and {c['door'][1]} in the spec"
            else:
                sx, sz = to_spec(pt)
                along, across = (sx, sz) if d["spec_axis"] == "z" else (sz, sx)
                lo, hi = d["span_spec"]
                off_wall = abs(across - d["wall_coord_spec"])
                off_span = abs(along - (lo + hi) / 2)       # checkpoint points are measured door centres
                # along the wall is the door's position (tight); across is the wall's own location, and a point
                # measured on one face sits half a wall-thickness off the centre line (tol_across, default = tol)
                ta = c.get("tol_across", c["tol"])
                ok = off_wall <= ta and off_span <= c["tol"]
                detail = (f"door centre {off_span * 100:.0f} cm along the wall from the measured centre (tol {c['tol'] * 100:.0f}); "
                          f"{off_wall * 100:.0f} cm off the wall centre line (tol {ta * 100:.0f})")
        elif c["type"] == "inside":
            sp = to_spec(pt)
            hit = [n for n, poly in spaces.items() if inside(poly, sp)]
            ok = c["space"] in hit
            detail = f"point lies in {hit[0] if hit else 'no space'} (expected {c['space']})"
        elif c["type"] == "dimension":
            if c.get("stage") == "spec":   # the built spec (walls thinned); spec (x, z) -> plan order (x=z, y=x)
                dims = np.ptp(spaces[c["space"]], axis=0)[::-1]
            else:
                dims = np.ptp(rebuild(edges_of(planpoly[c["space"]])), axis=0)
            exp = np.atleast_1d(c["expect_m"]).astype(float)
            got = {"x": dims[:1], "y": dims[1:], "both": dims}[c["axis"]]
            err = got / exp - 1
            ok = bool(np.all(np.abs(err) * 100 <= c["tol_pct"]))
            detail = f"{' x '.join(f'{g:.2f}' for g in got)} m vs {' x '.join(f'{e:.2f}' for e in exp)} ({', '.join(f'{e:+.1%}' for e in err)}; tol {c['tol_pct']}%)"
        fails += not ok
        kind = "independent" if c.get("independent") else "consistency"
        rows.append(("ok" if ok else "FAIL", f"{c['name']} [{kind}]", detail))

    review_sheet(trace)
    w = max(len(r[1]) for r in rows)
    for st, name, detail in rows:
        print(f"{st:<5} {name:<{w}}  {detail}")
    n_ind = sum(1 for c in checks["checks"] if c.get("independent"))
    print(f"\n{n_ind} of {len(checks['checks'])} checkpoints are independent of the data the plan was built from; "
          f"the rest catch edits that break agreement (regressions), not original errors")
    print(f"{sum(r[0] == 'ok' for r in rows)} ok, {sum(r[0] == 'warn' for r in rows)} warnings, {fails} FAIL"
          f"  ->  review sheet: spec/captures/trace-review.png")
    sys.exit(1 if fails else 0)


def review_sheet(trace):
    """One zoomed tile per traced space: the overhead around it with the trace drawn on top, for the eye pass."""
    im = Image.open(ROOT / trace["image"]).convert("RGB")
    H = np.loadtxt(ROOT / trace["calibration"]); Hi = np.linalg.inv(H)
    plan = {s["name"]: np.array(s["polygon_m"]) for s in json.loads(PLAN.read_text())["spaces"]}
    tiles = []
    for s in trace["spaces"]:
        pm = plan[s["name"]]
        q = np.c_[pm, np.ones(len(pm))] @ Hi.T; px = q[:, :2] / q[:, 2:]
        (x0, y0), (x1, y1) = px.min(0) - 40, px.max(0) + 40
        crop = im.crop((int(x0), int(y0), int(x1), int(y1)))
        k = 360 / max(crop.size); crop = crop.resize((int(crop.width * k), int(crop.height * k)))
        d = ImageDraw.Draw(crop)
        pts = [((x - x0) * k, (y - y0) * k) for x, y in px]
        d.line(pts + pts[:1], fill=(255, 40, 200), width=2)
        d.text((4, 4), s["name"] + (" (measured, not traced)" if "m" in s else ""), fill="yellow")
        tile = Image.new("RGB", (380, 380), (15, 15, 15)); tile.paste(crop, (10, 10)); tiles.append(tile)
    cols = 5
    sheet = Image.new("RGB", (cols * 380, -(-len(tiles) // cols) * 380))
    for i, t in enumerate(tiles):
        sheet.paste(t, ((i % cols) * 380, (i // cols) * 380))
    out = ROOT / "spec/captures/trace-review.png"; out.parent.mkdir(exist_ok=True); sheet.save(out)


if __name__ == "__main__":
    assert inside(np.array([[0, 0], [2, 0], [2, 2], [0, 2]]), (1, 1)) and not inside(np.array([[0, 0], [2, 0], [2, 2], [0, 2]]), (3, 1))
    main()
