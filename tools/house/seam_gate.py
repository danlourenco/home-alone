"""Seam gate: fails on any flicker (coplanar overlap), ledge or gap the Unity build's seam check reports (spec/captures/
walk-test.txt, SpecGreybox.SeamCheck) that is not listed with a reason in measurements/checkpoints/seams-known.json.
usage: uv run python -I tools/house/seam_gate.py [--selftest]
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def check(report, known):
    head = next((l for l in report.splitlines() if l.startswith("Seam check:")), None)
    if head is None:
        return ["no seam check in the build report: rebuild the grey-box (SpecGreybox.Build)"]
    bad = []
    for line in report.splitlines():
        m = re.match(r"(OVERLAP|LEDGE|GAP)\b", line)
        if m and not any(k["kind"] == m.group(1) and all(x in line for x in k["match"]) for k in known):
            bad.append(line)
    n = [int(v) for v in re.findall(r"(\d+) (?:overlaps|ledges|gaps)", head)]
    listed = sum(1 for l in report.splitlines() if re.match(r"(OVERLAP|LEDGE|GAP)\b", l))
    if sum(n) > listed:
        bad.append(f"report truncated: {sum(n)} seams counted, {listed} listed (raise the listing caps)")
    return bad


def selftest():
    known = [{"match": ["a/Wall", "b/Wall"], "kind": "LEDGE"}]
    ok = "Seam check: 3 structural boxes, 0 overlaps (flicker), 1 ledges, 0 gaps\nLEDGE   x 1 vs 2 (1 cm): a/Wall at () | b/Wall at ()\n"
    bad = ok.replace("0 overlaps", "1 overlaps") + "OVERLAP x=1: c/Wall at () | d/Floor at ()\n"
    assert check(ok, known) == [], "known seam failed"
    assert len(check(bad, known)) == 1, "unknown overlap passed"
    assert check("nothing", known), "missing seam check passed"
    print("selftest ok")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest(); sys.exit(0)
    known = json.loads((ROOT / "measurements/checkpoints/seams-known.json").read_text())["known"]
    bad = check((ROOT / "spec/captures/walk-test.txt").read_text(), known)
    for b in bad:
        print("FAIL", b)
    print(f"seam gate: {len(bad)} unexplained seam(s)")
    sys.exit(1 if bad else 0)
