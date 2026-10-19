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
  R6 every DISAGREEING check that is evidence needs a "disposition": why the claim stands against it, or what was done
     (Oct 15 review: a contradicting independent survey left R1 green; contradictions were never adjudicated).
  R7 a LAYOUT claim (a stair's or room's shape: which way it runs, turns, where its parts are; triggered by "layout" in the
     claim, a topological check, or stair/layout/turn/straight in the change or premise) must list "alternatives" (every competing
     layout, the current build included) and, under "layout": {"decides": [{"part", "observed_in": [frames], "extrapolated"}]},
     every part where the alternatives differ, each seen directly (unoccluded) in 2+ frames and not extrapolated. Records
     written from Oct 15 night on carry "gate": 7 (earlier records predate the rule and are not re-judged by it).
     (Oct 15: the back stair was called "one straight flight" from an upper-flight nosing line extended to the floor; the foot,
     where the options differ, was behind chairs in every frame used. The overhead, the film, the built TRIAL and the tool's
     own newel-to-wall-post line all showed the turned foot. The user: "marina doesn't have a straight flight".)
  R8 pick check (records with "gate": 8): every metric check measured on a film or Marina frame (data film:/film-frame:/marina-frame:)
     needs "pick": {"crop": <saved crop of the picked point, on disk>, "confirmed_by": <who/what independently said WHAT it is>}.
     (Oct 16-17: the arch crown was picked on the landing's fascia and a "casing" that the film doesn't have was measured.)
Check "type": metric (default) | angular | ratio | topological. Only a metric check needs a ruler; an angle, ratio or
topology read with scale "none" is evidence, not a lead (Oct 15 review: the 35 deg pitch printed as a lead).
Independence is per failure mode: a claim may list "risks" (e.g. extraction, scale, registration, model-fidelity) and
each check what it "tests"; R1 then needs an independent agreeing check for EVERY listed risk.
Independence compares RULER KINDS: "door-80in:1125" and "door-80in:1175" are one ruler (the 80 in door assumption).
(Oct 14: the 8 ft record passed R1 on a second door frame, the September model's doors and "the 8 ft standard".)
Leads are never evidence: a check resting only on a summary, an AI answer, a recollection or a standard does not count.
usage: uv run python tools/house/change_gate.py [changes/<file>.json ...]   (default: every record)
       uv run python tools/house/change_gate.py --selftest
"""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


LEADS = ("user-summary", "ai", "summary", "web-summary", "recollection", "standard", "none")
NOT_RULERS = {"count", "none"}   # a count has no scale to share
# self-consistency gates: they check the model against itself (mesh topology, overlaps, plan rules, trim runs), never against the
# house, so they can't be R1's independent ruler (Oct 17 Codex review: R1 passed the arch record on tools:model_quality alone)
SELF_GATES = ("model_quality", "zfight", "clash", "verify_plan", "trim_faces", "rail_joints", "soffit_joints", "unity:build", "unity:walk-test")


def kind(i):
    return i.split(":")[0]


def inputs(x):
    """Everything a number rests on: its data (by id), its rulers and what those were calibrated from (by KIND)."""
    up = x.get("upstream", [])
    return set(x["data"]) | set(up) | {kind(i) for i in x["scale"] + up if kind(i) not in NOT_RULERS}


def is_lead(x):
    """Rests only on summaries/standards/nothing. A non-metric check (angle, ratio, topology) needs no ruler."""
    if all(kind(i) in LEADS for i in x["data"]):
        return True
    return x.get("type", "metric") == "metric" and all(kind(i) in LEADS for i in x["scale"])


def is_self(x):
    """Rests only on the build's own self-consistency gates."""
    return all(any(g in i.lower() for g in SELF_GATES) for i in x["data"])


def gate(rec):
    out = []
    claim = rec["claim"]
    ci = inputs(claim)
    indep = [c for c in rec["checks"] if c["agrees"] and not (inputs(c) & ci) and not is_lead(c) and not is_self(c)]
    for c in rec["checks"]:
        shared = sorted(inputs(c) & ci)
        how = "LEAD, not evidence" if is_lead(c) else "self-consistency gate, not a ruler" if is_self(c) else "consistency (shares " + ", ".join(shared) + ")" if shared else "independent"
        disp = f" -> disposition: {c['disposition']}" if c.get("disposition") else ""
        out.append(("info", f"check '{c['what']}' [{c.get('type', 'metric')}]: {'agrees' if c['agrees'] else 'DISAGREES'}, {how}{disp}"))
    risks = claim.get("risks")
    if risks:
        missing = [r for r in risks if not any(r in c.get("tests", []) for c in indep)]
        out.append(("ok" if not missing else "FAIL", f"R1 independent agreeing checks: {len(indep)}; per risk: " +
                    ", ".join(f"{r} {'covered' if r not in missing else 'NOT covered'}" for r in risks)))
    else:
        out.append(("ok" if indep else "FAIL", f"R1 independent agreeing checks: {len(indep)}"))
    open_ = [c["what"] for c in rec["checks"] if not c["agrees"] and not is_lead(c) and not c.get("disposition", "").strip()]
    out.append(("ok" if not open_ else "FAIL", "R6 contradictions: " + ("each disagreeing check has a disposition" if not open_ else
                f"{len(open_)} without a disposition: " + "; ".join(w[:60] for w in open_))))
    # "failed (user walk ...)" and "rejected ..." count too: an exact match let a rejected attempt read as 0 failures (Oct 17 review)
    failed = [h for h in rec.get("history", []) if h["outcome"].split()[0].strip("(:,").lower() in ("failed", "rejected")]
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
    text = (rec["change"] + " " + rec["premise"]).lower()
    if rec.get("gate", 0) >= 7 and (claim.get("layout") or any(c.get("type") == "topological" for c in rec["checks"]) or any(w in text for w in ("stair", "layout", " turn", "straight"))):
        lay = claim.get("layout", {}); dec = lay.get("decides", [])
        weak = [d["part"] for d in dec if len(d.get("observed_in", [])) < 2 or d.get("extrapolated")]
        r7 = bool(claim.get("alternatives")) and bool(dec) and not weak
        out.append(("ok" if r7 else "FAIL", "R7 layout: " + ("no alternatives listed" if not claim.get("alternatives") else
                    "no deciding parts listed" if not dec else f"parts not seen directly in 2+ frames (or extrapolated): {weak}" if weak else
                    f"{len(dec)} deciding parts each seen in 2+ frames against {len(claim['alternatives'])} alternatives")))
    if rec.get("gate", 0) >= 8:
        frame = [c for c in rec["checks"] + [claim] if c.get("type", "metric") == "metric" and any(kind(i) in ("film", "film-frame", "marina-frame") for i in c["data"])]
        unpicked = [c.get("what", "claim")[:50] for c in frame if not (ROOT / c.get("pick", {}).get("crop", "\0")).is_file() or not c.get("pick", {}).get("confirmed_by", "").strip()]
        out.append(("ok" if not unpicked else "FAIL", "R8 pick check: " + (f"{len(frame)} frame measurements each with a crop and a confirmation" if not unpicked else
                    f"no saved crop or independent confirmation of what was picked: {unpicked}")))
    walk = rec.get("user_walk", "pending")
    out.append(("info", f"user walk: {walk}" + ("  (TRIAL: say so; not done until the user accepts it)" if walk == "pending" else "")))
    return out


def main(paths):
    bad = 0
    for p in paths:
        rec = json.loads(Path(p).read_text())
        print(f"\n{Path(p).name}: {rec['change']}\n  premise: {rec['premise']}")
        for level, msg in gate(rec):
            # unity_pipeline.sh preflight for the build that renders a record's AFTER views (HA_CHANGE=<record>, `build -views`): only
            # those missing after-renders wait for the build; every other rule, and the before renders, still fail here. Re-run after.
            r = rec.get("renders", {})
            if level == "FAIL" and msg.startswith("R3") and os.environ.get("HA_PREBUILD") == "1" and os.environ.get("HA_CHANGE") and \
                    Path(os.environ["HA_CHANGE"]).resolve() == Path(p).resolve() and r.get("before") and r.get("after") and \
                    all((ROOT / q).exists() for q in r["before"]):
                level, msg = "pend", msg + " (pending: this build renders them; re-run change_gate after it)"
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
    # as first written (Oct 14): no furniture check, foyer built in, no assumed rooms (the record has since been repaired)
    rec["checks"] = [c for c in rec["checks"] if "furniture" not in c["what"]]
    rec["claim"]["applies_to"] = sorted(set(rec["claim"]["applies_to"]) | {"foyer"}); rec["claim"].pop("assumed", None)
    res = {m.split()[0]: lvl for lvl, m in gate(rec) if lvl != "info"}
    assert res["R1"] == "FAIL" and res["R4"] == "FAIL", res
    rec["claim"]["surface"] = "landing-face"
    assert {m.split()[0]: lvl for lvl, m in gate(rec) if lvl != "info"}["R5"] == "FAIL"
    hist = {"history": [{"outcome": "failed (user walk: wrong)"}, {"outcome": "rejected by the user"}], "premise_reviewed": ""}
    assert {m.split()[0]: lvl for lvl, m in gate({**rec, **hist}) if lvl != "info"}["R2"] == "FAIL", "annotated failures not counted"
    rec = json.loads((ROOT / "changes/2026-10-15-foyer-length.json").read_text())
    rec["checks"].append({"what": "injected: independent survey says 9 m", "agrees": False, "data": ["survey:x"], "scale": ["tape:x"]})
    assert {m.split()[0]: lvl for lvl, m in gate(rec) if lvl != "info"}["R6"] == "FAIL", "an undisposed contradiction passed"
    rec["checks"][-1]["disposition"] = "injected"
    assert {m.split()[0]: lvl for lvl, m in gate(rec) if lvl != "info"}["R6"] == "ok"
    ang = {"what": "pitch", "agrees": True, "data": ["marina-frame:1"], "scale": ["none"], "type": "angular"}
    assert not is_lead(ang) and is_lead({**ang, "type": "metric"}), "an angle with no ruler must be evidence"
    rec["claim"]["risks"] = ["extraction", "scale"]
    rec["checks"][0]["tests"] = ["extraction"]
    assert {m.split()[0]: lvl for lvl, m in gate(rec) if lvl != "info"}["R1"] == "FAIL", "an uncovered risk passed"
    st = {"gate": 7, "change": "back stair as one straight flight", "premise": "Marina's back stair is straight", "history": [], "checks": [],
          "claim": {"data": ["colmap:backstair"], "scale": ["rig-height"], "alternatives": ["straight", "turned foot (build)"],
                    "layout": {"decides": [{"part": "foot", "observed_in": ["marina-frame:916"], "extrapolated": True}]}}}
    assert {m.split()[0]: lvl for lvl, m in gate(st) if lvl != "info"}["R7"] == "FAIL", "an extrapolated, once-seen foot decided a layout"
    st["claim"]["layout"]["decides"] = [{"part": "foot", "observed_in": ["marina-frame:926", "marina-frame:927.4"]}]
    assert {m.split()[0]: lvl for lvl, m in gate(st) if lvl != "info"}["R7"] == "ok"
    arch = json.loads((ROOT / "changes/2026-10-16-foyer-arch-model.json").read_text())
    arch["checks"] = [c for c in arch["checks"] if c["data"] == ["tools:model_quality"]]; arch["claim"].pop("risks", None)
    assert arch["checks"] and {m.split()[0]: lvl for lvl, m in gate(arch) if lvl != "info"}["R1"] == "FAIL", "model_quality alone passed R1"
    pk = {"gate": 8, "change": "x", "premise": "x", "history": [], "checks": [],
          "claim": {"data": ["film:10673"], "scale": ["door-80in:10673"], "pick": {"crop": "tools/house/change_gate.py"}}}
    assert {m.split()[0]: lvl for lvl, m in gate(pk) if lvl != "info"}["R8"] == "FAIL", "an unconfirmed frame pick passed R8"
    pk["claim"]["pick"]["confirmed_by"] = "subagent: the crown of the arch, not the landing fascia"
    assert {m.split()[0]: lvl for lvl, m in gate(pk) if lvl != "info"}["R8"] == "ok"
    print("selftest PASS: a frame measurement without a confirmed pick crop fails R8 (gate 8)")
    print("selftest PASS: a self-consistency gate (model_quality) alone fails R1")
    print("selftest PASS: a layout decided by an extrapolated, once-seen part fails R7")
    print("selftest PASS: an undisposed contradiction fails R6; an angle with no ruler is evidence; an uncovered listed risk fails R1")
    print("selftest PASS: the circular Buzz record fails R1/R2; adding an independent check and a review passes them;"
          " the Oct 14 8 ft record fails R1 (one door ruler + a standard), R4 (foyer unmeasured); a landing-face read fails R5")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        sys.exit(main(sys.argv[1:] or sorted(str(p) for p in (ROOT / "changes").glob("*.json"))))
