#!/usr/bin/env python3
"""walk_notes.py: every M walk note must get a disposition, so none slips (Oct 20: the 19:04 French-window note was never queued).
Notes come from spec/feedback/feel-notes.jsonl; dispositions live in docs/walk-notes-ledger.json keyed by the note's time.

  python3 tools/house/walk_notes.py                       # list notes since the ledger start with no disposition (exit 1 if any)
  python3 tools/house/walk_notes.py set TIME STATUS TEXT  # TIME = "2026-10-19T19:04" (prefix ok); STATUS = fixed|open|queued|wontfix|info
  python3 tools/house/walk_notes.py open                  # list the open/queued ones
  python3 tools/house/walk_notes.py --selftest
Run at session start (.claude/settings.json) and in preflight (informational: it never blocks a build).
"""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
NOTES = ROOT / "spec/feedback/feel-notes.jsonl"
LEDGER = ROOT / "docs/walk-notes-ledger.json"
STATUSES = {"fixed", "open", "queued", "wontfix", "info"}


def notes():
    return [json.loads(l) for l in NOTES.read_text().splitlines() if l.strip()]


def ledger():
    return json.loads(LEDGER.read_text()) if LEDGER.exists() else {"since": "2026-10-19", "notes": {}}


def key(n):
    return n["time"][:19]   # to the second: several notes can share a minute (three at 2026-10-19 12:33)


def pending(ns, led):
    return [n for n in ns if key(n) >= led["since"] and key(n) not in led["notes"]]


def main(a):
    led = ledger()
    if a[:1] == ["set"]:
        t, st, text = a[1], a[2], " ".join(a[3:])
        assert st in STATUSES, f"status must be one of {sorted(STATUSES)}"
        hits = [key(n) for n in notes() if key(n).startswith(t)]
        assert len(hits) == 1, f"{len(hits)} notes match {t}: {hits[:5]}"
        led["notes"][hits[0]] = {"status": st, "what": text}
        LEDGER.write_text(json.dumps(led, indent=1, sort_keys=True) + "\n"); print(f"{hits[0]} -> {st}"); return 0
    ns = {key(n): n for n in notes()}
    if a[:1] == ["open"]:
        for k, v in sorted(led["notes"].items()):
            if v["status"] in ("open", "queued"):
                print(f"  {v['status']:6} {k} {ns.get(k, {}).get('note', '')[:80]} -> {v['what'][:80]}")
        return 0
    p = pending(list(ns.values()), led)
    print(f"walk notes: {len(p)} without a disposition since {led['since']}")
    for n in p:
        print(f"  {key(n)} {n.get('pos')} \"{n['note'][:100]}\"")
    return 1 if p else 0


def selftest():
    ns = [{"time": "2026-10-19T19:04:16", "note": "a"}, {"time": "2026-10-18T10:00:00", "note": "old"}]
    led = {"since": "2026-10-19", "notes": {}}
    assert [key(n) for n in pending(ns, led)] == ["2026-10-19T19:04:16"]
    led["notes"]["2026-10-19T19:04:16"] = {"status": "open", "what": "x"}
    assert pending(ns, led) == []
    print("selftest ok")


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else main(sys.argv[1:]))
