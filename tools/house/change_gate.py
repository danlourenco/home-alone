"""Change gate: no geometry change (either model) without independent evidence, a premise review and a visual check.

Every change that moves, resizes or adds geometry has a record changes/<date>-<slug>.json (skill change-gate):
  premise    the one sentence the change assumes ("Marina's Buzz room is 4.35 x 3.49 m")
  claim      the number(s) the change builds to, with the DATA and the SCALE they came from, plus "upstream": what
             those were calibrated from (leave it out and a shared root looks independent)
  history    earlier attempts on the same thing, each {date, what, outcome: ok|failed}
  checks     evidence for the claim, each with its own data and scale and whether it agrees
  renders    before/after images from the same fixed views (looked at, not scored)
  user_walk  pending | accepted | rejected  (only the user's walk accepts a change)
Rules (exit 1 on any FAIL):
  R1 at least one AGREEING check is independent: shares no data, scale or upstream input with the claim.
     (Oct 13: Marina's cameras "landing inside" the resized room came from the same VGGT solve and door scale as the
     4.35 m claim, so they could not disagree. The user found the result terrible.)
  R2 two or more failed attempts on record: premise_reviewed must say why this premise survives (skill
     principle-attack-the-premise: census before the next fix).
  R3 before and after renders exist on disk.
usage: uv run python tools/house/change_gate.py [changes/<file>.json ...]   (default: every record)
       uv run python tools/house/change_gate.py --selftest
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def inputs(x):
    """Everything a number rests on: its data, its scale, and what those were calibrated from ("upstream")."""
    return set(x["data"]) | set(x["scale"]) | set(x.get("upstream", []))


def gate(rec):
    out = []
    claim = rec["claim"]
    ci = inputs(claim)
    indep = [c for c in rec["checks"] if c["agrees"] and not (inputs(c) & ci)]
    for c in rec["checks"]:
        shared = sorted(inputs(c) & ci)
        kind = "consistency (shares " + ", ".join(shared) + ")" if shared else "independent"
        out.append(("info", f"check '{c['what']}': {'agrees' if c['agrees'] else 'DISAGREES'}, {kind}"))
    out.append(("ok" if indep else "FAIL", f"R1 independent agreeing checks: {len(indep)}"))
    failed = [h for h in rec.get("history", []) if h["outcome"] == "failed"]
    r2 = len(failed) < 2 or rec.get("premise_reviewed", "").strip()
    out.append(("ok" if r2 else "FAIL", f"R2 failed attempts on record: {len(failed)}; premise reviewed: {'yes' if rec.get('premise_reviewed', '').strip() else 'no'}"))
    r = rec.get("renders", {})
    missing = [p for k in ("before", "after") for p in r.get(k, []) if not (ROOT / p).exists()]
    r3 = r.get("before") and r.get("after") and not missing
    out.append(("ok" if r3 else "FAIL", "R3 before/after renders" + (f": missing {missing}" if missing else "" if r3 else ": none listed")))
    walk = rec.get("user_walk", "pending")
    out.append(("info", f"user walk: {walk}" + ("  (TRIAL: say so; not done until the user accepts it)" if walk == "pending" else "")))
    return out


def main(paths):
    bad = 0
    for p in paths:
        rec = json.loads(Path(p).read_text())
        print(f"\n{Path(p).name}: {rec['change']}\n  premise: {rec['premise']}")
        for level, msg in gate(rec):
            bad += level == "FAIL"
            print(f"  {level:<4} {msg}")
    print(f"\n{bad} FAIL")
    return 1 if bad else 0


def selftest():
    """The Oct 13 Buzz resize must fail R1 and R2; the same record with one independent check and a review must pass."""
    rec = json.loads((ROOT / "changes/2026-10-13-buzz-resize.json").read_text())
    res = {m.split()[0]: lvl for lvl, m in gate(rec) if lvl != "info"}
    assert res["R1"] == "FAIL" and res["R2"] == "FAIL", res
    rec["checks"].append({"what": "injected: bed width as ruler", "agrees": True, "data": ["marina-frame:556"], "scale": ["twin-mattress-0.99m"]})
    rec["premise_reviewed"] = "injected"
    res = {m.split()[0]: lvl for lvl, m in gate(rec) if lvl != "info"}
    assert res["R1"] == "ok" and res["R2"] == "ok", res
    print("selftest PASS: the circular Buzz record fails R1/R2; adding an independent check and a review passes them")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        sys.exit(main(sys.argv[1:] or sorted(str(p) for p in (ROOT / "changes").glob("*.json"))))
