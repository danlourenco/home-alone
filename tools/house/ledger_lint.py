"""Ledger linter: nothing guessed, authored or drifting may be missing from docs/DEVIATIONS.md.

Scans the built specs and their inputs for every place geometry did NOT come straight from measurement, and fails
unless the ledger's Open section names it:
  - doors placed from topology (no measured position)
  - unresolved items and soft flags from the reconciler
  - the stair's authored parts, default (unmeasured) ceilings, any front-to-back stretch
  - rooms that tools/house/shape_drift.py flags
usage: uv run --with numpy python tools/house/ledger_lint.py      (exit 1 when anything is unlisted)
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def ledger_open():
    text = (ROOT / "docs/DEVIATIONS.md").read_text()
    return text.split("## Settled")[0].lower()


def needs():
    """(what, keywords): the item is covered when ALL keywords appear in the ledger's Open section."""
    out = []
    for floor, spec_path in (("upstairs", "spec/house_spec.json"), ("ground", "spec/house_spec.ground.json")):
        p = ROOT / spec_path
        if not p.exists():
            continue
        spec = json.loads(p.read_text())
        for d in spec["doors"]:
            if d["placed_from"].startswith("topology"):
                a, b = d["between"]
                out.append((f"{floor}: door {a}/{b} placed from topology", [a.split("_")[0], b.split("_")[0]]))
        for f in spec["flags"]:
            if f.startswith("ceiling"):
                out.append((f"{floor}: unmeasured default ceilings", ["ceilings"]))
            elif "thick" in f:
                a, b = re.search(r"wall (\S+)/(\S+)", f).groups()
                out.append((f"{floor}: {f}", [a.split("_")[0], b.split("_")[0]]))
        if spec.get("stair"):
            out.append((f"{floor}: stair authored parts ({spec['stair']['authored'][:40]}...)", ["flight 2", "gallery"]))
        doors = json.loads((ROOT / f"measurements/overhead/{floor}-doors.json").read_text())
        for u in doors.get("unresolved", []):
            key = re.findall(r"[a-z]{5,}", u.lower())[:2]
            out.append((f"{floor}: unresolved '{u[:60]}'", key))
        trace = json.loads((ROOT / f"measurements/overhead/{floor}-trace.json").read_text())
        if "stretch" in trace:
            out.append((f"{floor}: front-to-back stretch is applied", ["stretch"]))
    drift = subprocess.run(["uv", "run", "-q", "--with", "numpy", "python", "tools/house/shape_drift.py"],
                           cwd=ROOT, capture_output=True, text=True).stdout
    for line in drift.splitlines():
        if "<-- DRIFT" in line:
            room = line.split()[0]
            out.append((f"shape drift: {room}", [room.split("_")[0]]))
    return out


def main():
    led = ledger_open()
    missing = [(w, k) for w, k in needs() if not all(x.lower() in led for x in k)]
    for w, k in needs():
        print(f"{'MISSING' if (w, k) in missing else 'listed '}  {w}   [{', '.join(k)}]")
    print(f"\n{len(missing)} item(s) not in docs/DEVIATIONS.md (Open section)")
    sys.exit(1 if missing else 0)


if __name__ == "__main__":
    main()
