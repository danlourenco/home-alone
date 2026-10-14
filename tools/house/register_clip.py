"""Register a gated SfM clip onto the floor plan, then derive the clip-measured geometry in plan metres.

The registration is a 2D similarity (rotation, scale, translation) fitted ONLY on wall lines that the clip and the
overhead both show independently (measurements/checkpoints/<floor>.json -> registrations.<clip>.anchors). The
clip-measured features (doorways, bay walls) are then mapped through it, so checkpoints built from them are not circular.
Writes the registration back to the checkpoints file and the derived geometry into the trace ("m" polygons) and
doors file, each with its source. Re-run after changing anchors or features, then run the verify-plan skill.
usage: uv run --with numpy --with scipy python tools/house/register_clip.py hall-s1 [--loo]
  --loo: leave-one-out over the anchor walls (held-out, independent); writes nothing
"""
import json
import sys
from pathlib import Path

import numpy as np
from scipy.optimize import least_squares

ROOT = Path(__file__).resolve().parents[2]
_CLIP = next((a for a in sys.argv[1:] if not a.startswith("--")), None)
FLOOR = next((f for f in ("upstairs", "ground") if _CLIP and (ROOT / f"measurements/checkpoints/{f}.json").exists()
              and _CLIP in json.loads((ROOT / f"measurements/checkpoints/{f}.json").read_text()).get("registrations", {})), "upstairs")
CHECKS = ROOT / f"measurements/checkpoints/{FLOOR}.json"
TRACE = ROOT / f"measurements/overhead/{FLOOR}-trace.json"
DOORS = ROOT / f"measurements/overhead/{FLOOR}-doors.json"


def apply(params, P):
    th, s, tx, ty = params
    c, n = np.cos(th), np.sin(th)
    P = np.atleast_2d(P)
    return s * P @ np.array([[c, n], [-n, c]]) + [tx, ty]


def fit(anchors, start=(0.0, 1.0, 6.3, 1.6), rigid=False):
    """Each anchor: clip segment (2 points, clip plan metres) lies on plan line x=c or y=c.
    rigid=True fixes scale at 1 (both sides are independently metric), fitting rotation + translation only."""
    def resid(q):
        p = [q[0], 1.0, q[1], q[2]] if rigid else q
        r = []
        for a in anchors:
            q = apply(p, np.array(a["clip"]))
            k = 0 if a["plan_axis"] == "x" else 1
            r += list((q[:, k] - a["plan"]) * a.get("weight", 1.0))
        return r
    x0 = [start[0], start[2], start[3]] if rigid else list(start)
    sol = least_squares(resid, x0)
    res = np.array(resid(sol.x)).reshape(-1, 2)
    params = np.array([sol.x[0], 1.0, sol.x[1], sol.x[2]]) if rigid else sol.x
    return params, res


def loo(clip, rigid=False):
    """Held-out test: refit without each anchor wall, predict where that wall lands in the plan. The held-out wall
    played no part in its own prediction, so this is independent evidence (unlike the fit residuals)."""
    reg = json.loads(CHECKS.read_text())["registrations"][clip]
    an = reg["anchors"]
    prev = reg.get("similarity")
    start = (np.radians(prev["rotation_deg"]), prev["scale"], *prev["translation"]) if prev else (0.0, 1.0, 6.3, 1.6)
    print(f"{clip}: leave-one-out over {len(an)} anchor walls ({'rigid, scale fixed at 1' if rigid else 'similarity'})")
    errs = []
    for i, a in enumerate(an):
        params, _ = fit(an[:i] + an[i + 1:], start, rigid or reg.get("rigid", False))
        q = apply(params, np.array(a["clip"]))
        k = 0 if a["plan_axis"] == "x" else 1
        e = float(np.abs(q[:, k] - a["plan"]).max() * 100); errs.append(e)
        print(f"  held out {a['name']:<36} predicted {q[:, k].mean():7.3f} vs plan {a['plan']:7.3f}: {e:5.1f} cm")
    print(f"  median {np.median(errs):.1f} cm, max {max(errs):.1f} cm")
    return errs


def main(clip):
    C = json.loads(CHECKS.read_text())
    reg = C["registrations"][clip]
    prev = reg.get("similarity")
    start = (np.radians(prev["rotation_deg"]), prev["scale"], *prev["translation"]) if prev else (0.0, 1.0, 6.3, 1.6)
    params, res = fit(reg["anchors"], start, reg.get("rigid", False))
    print(f"{clip}: rotation {np.degrees(params[0]):+.2f} deg, scale {params[1]:.4f}, translation ({params[2]:.3f}, {params[3]:.3f})")
    for a, r in zip(reg["anchors"], res):
        print(f"  anchor {a['name']:<34} residual {np.abs(r).max() * 100:5.1f} cm")
    reg["similarity"] = {"rotation_deg": round(float(np.degrees(params[0])), 3), "scale": round(float(params[1]), 5),
                         "translation": [round(float(params[2]), 4), round(float(params[3]), 4)],
                         "anchor_residual_cm_max": round(float(np.abs(res).max() * 100), 1)}
    P = lambda pts: apply(params, np.array(pts, float))

    # derived geometry
    F = reg.get("features", {})
    T = json.loads(TRACE.read_text()); D = json.loads(DOORS.read_text())
    S = {s["name"]: s for s in T["spaces"]}
    for name, spec in F.get("polygons", {}).items():
        poly = []
        for v in spec["vertices"]:   # each vertex: plan value, or {"clip": [f, s], "use": "x"|"y"|"xy"}
            out = []
            for k, axis in enumerate("xy"):
                val = v[k]
                if isinstance(val, dict):
                    val = float(P([val["clip"]])[0][k])
                out.append(round(float(val), 3))
            poly.append(out)
        S[name].pop("px", None); S[name]["m"] = poly
        S[name]["notes"] = spec["note"] + f" (clip {clip}, registration residual <= {reg['similarity']['anchor_residual_cm_max']} cm)"
    for dname, spec in F.get("doors", {}).items():
        a, b = spec["between"]
        ends = P(spec["clip"])
        k = 1 if spec["along"] == "y" else 0
        lo, hi = sorted(float(v) for v in ends[:, k])
        if "standard_width" in spec:   # measured jambs include casing: centre a standard door in them
            mid = (lo + hi) / 2; lo, hi = mid - spec["standard_width"] / 2, mid + spec["standard_width"] / 2
        for d in D["doors"]:
            if sorted((d["a"], d["b"])) == sorted((a, b)) and not d.get("pinned"):   # pinned: placed from other evidence (its source says which)
                d["span"] = [round(lo, 3), round(hi, 3)]
                d["source"] = spec["note"] + f" (clip {clip} via registration)"
    for cp in C["checks"]:
        if cp.get("clip") == clip:
            cp["plan"] = [round(float(v), 3) for v in P([cp["clip_point"]])[0]]
    TRACE.write_text(json.dumps(T, indent=1) + "\n"); DOORS.write_text(json.dumps(D, indent=1) + "\n")
    CHECKS.write_text(json.dumps(C, indent=1) + "\n")
    print("wrote derived geometry to the trace, doors file and checkpoints")


if __name__ == "__main__":
    # self-check: straight plan walls mapped into a clip by a known similarity are registered back exactly
    true = [np.radians(2.0), 1.05, 6.0, 1.5]
    th, sc = true[0], true[1]; M = np.array([[np.cos(th), np.sin(th)], [-np.sin(th), np.cos(th)]])
    inv = lambda Q: (np.array(Q, float) - true[2:]) @ M.T / sc
    walls = [([[7, 2.6], [9, 2.6]], "y", 2.6), ([[10.6, 0], [10.6, 2]], "x", 10.6), ([[12.7, 1], [12.7, 2.5]], "x", 12.7), ([[8, 1.2], [10, 1.2]], "y", 1.2)]
    an = [{"name": str(i), "clip": inv(w).tolist(), "plan_axis": ax, "plan": v} for i, (w, ax, v) in enumerate(walls)]
    assert np.allclose(fit(an)[0], true, atol=1e-4)
    if "--loo" in sys.argv:
        loo(sys.argv[1], rigid="--rigid" in sys.argv)
    else:
        main(sys.argv[1])
