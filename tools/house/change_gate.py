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
  R4 scope: the claim lists "applies_to" (rooms/elements it is built into) and "measured_in"; every applied-but-unmeasured
     item needs an "assumed" entry naming its DEVIATIONS row. (Oct 14: 8 ft measured in living + dining, built into
     every ground room including the foyer, which is ~10 ft.)
  R5 a ceiling claim (change or premise says "ceiling") must read the ceiling PLANE ("surface": "ceiling-plane"), not a crown, beam,
     landing or soffit edge. (Oct 14: the landing's front was read as the foyer ceiling twice.)
Independence compares RULER KINDS: "door-80in:1125" and "door-80in:1175" are one ruler (the 80 in door assumption).
(Oct 14: the 8 ft record passed R1 on a second door frame, the September model's doors and "the 8 ft standard".)
Leads are never evidence: a check resting only on a summary, an AI answer, a recollection or a standard does not count.
usage: uv run python tools/house/change_gate.py [changes/<file>.json ...]   (default: every record)
       uv run python tools/house/change_gate.py --selftest
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


LEADS = ("user-summary", "ai", "summary", "web-summary", "recollection", "standard", "none")
NOT_RULERS = {"count", "none"}   # a count has no scale to share


def kind(i):
    return i.split(":")[0]


def inputs(x):
    """Everything a number rests on: its data (by id), its rulers and what those were calibrated from (by KIND)."""
    up = x.get("upstream", [])
    return set(x["data"]) | set(up) | {kind(i) for i in x["scale"] + up if kind(i) not in NOT_RULERS}


def is_lead(x):
    return all(kind(i) in LEADS for i in x["data"]) or all(kind(i) in LEADS for i in x["scale"])


def gate(rec):
    out = []
    claim = rec["claim"]
    ci = inputs(claim)
    indep = [c for c in rec["checks"] if c["agrees"] and not (inputs(c) & ci) and not is_lead(c)]
    for c in rec["checks"]:
        shared = sorted(inputs(c) & ci)
        how = "LEAD, not evidence" if is_lead(c) else "consistency (shares " + ", ".join(shared) + ")" if shared else "independent"
        out.append(("info", f"check '{c['what']}': {'agrees' if c['agrees'] else 'DISAGREES'}, {how}"))
    out.append(("ok" if indep else "FAIL", f"R1 independent agreeing checks: {len(indep)}"))
    failed = [h for h in rec.get("history", []) if h["outcome"] == "failed"]
    r2 = len(failed) < 2 or rec.get("premise_reviewed", "").strip()
    out.append(("ok" if r2 else "FAIL", f"R2 failed attempts on record: {len(failed)}; premise reviewed: {'yes' if rec.get('premise_reviewed', '').strip() else 'no'}"))
    r = rec.get("renders", {})
    missing = [p for k in ("before", "after") for p in r.get(k, []) if not (ROOT / p).exists()]
    r3 = r.get("before") and r.get("after") and not missing
    out.append(("ok" if r3 else "FAIL", "R3 before/after renders" + (f": missing {missing}" if missing else "" if r3 else ": none listed")))
    unmeasured = sorted(set(claim.get("applies_to", [])) - set(claim.get("measured_in", [])) - set(claim.get("assumed", {})))
    r4 = claim.get("applies_to") and not unmeasured
    out.append(("ok" if r4 else "FAIL", "R4 scope: " + ("no applies_to/measured_in" if not claim.get("applies_to") else
                f"built into {unmeasured} without a measurement or a DEVIATIONS row" if unmeasured else "every applied item measured or logged")))
    if "ceiling" in (rec["change"] + rec["premise"]).lower():
        r5 = claim.get("surface") == "ceiling-plane"
        out.append(("ok" if r5 else "FAIL", f"R5 ceiling read surface: {claim.get('surface', 'not stated')}"))
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
    rec = json.loads((ROOT / "changes/2026-10-14-ground-ceiling-8ft.json").read_text())
    res = {m.split()[0]: lvl for lvl, m in gate(rec) if lvl != "info"}
    assert res["R1"] == "FAIL" and res["R4"] == "FAIL", res
    rec["claim"]["surface"] = "landing-face"
    assert {m.split()[0]: lvl for lvl, m in gate(rec) if lvl != "info"}["R5"] == "FAIL"
    print("selftest PASS: the circular Buzz record fails R1/R2; adding an independent check and a review passes them;"
          " the Oct 14 8 ft record fails R1 (one door ruler + a standard), R4 (foyer unmeasured); a landing-face read fails R5")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        sys.exit(main(sys.argv[1:] or sorted(str(p) for p in (ROOT / "changes").glob("*.json"))))
