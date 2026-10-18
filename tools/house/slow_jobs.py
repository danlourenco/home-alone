#!/usr/bin/env python3
"""Slow jobs: flag recurring work that should become a tool (user Oct 17: "what is the trigger for the agent to determine when
routine work becomes slow? what's the right mechanism for this?").

Reads spec/captures/build-log.jsonl (every build/bake, written by unity_pipeline.sh) and spec/captures/agent-log.jsonl (one line
per agent job, appended with `slow_jobs.py log ...` when an agent hands back). Prints a few lines; the SessionStart hook in
.claude/settings.json runs it so the report lands in Claude's context without anyone remembering to look.

  python3 tools/house/slow_jobs.py                       # the report
  python3 tools/house/slow_jobs.py log --kind prop --job buzztrunk --s 1258 --tools 101 [--builds 2]

Flags:
  - a job kind done 2+ times averaging over 5 min   -> propose a tool before the next one (AGENTS.md)
  - one job that was mostly agent steps (40+ tool calls, builds under 20% of its time)
  - builds since the last bake (a build without a bake leaves the lighting stale)
"""
import argparse, json, sys, time
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BUILDS = ROOT / "spec/captures/build-log.jsonl"
AGENTS = ROOT / "spec/captures/agent-log.jsonl"
SLOW_S, REPEAT, STEPS, BUILD_SHARE = 300, 2, 40, 0.2


def rows(p):
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()] if p.exists() else []


def report(builds, agents):
    out = []
    by = defaultdict(list)
    for a in agents:
        by[a["kind"]].append(a)
    for kind, js in sorted(by.items()):
        avg = sum(j["s"] for j in js) / len(js)
        if len(js) >= REPEAT and avg > SLOW_S:
            out.append(f"SLOW  {kind}: {len(js)} jobs, {avg / 60:.0f} min average -> propose a tool before the next {kind} job")
    for j in agents[-10:]:
        built = sum(b.get("wall_s", 0) for b in builds if b.get("job") == j["job"])
        if j.get("tools", 0) >= STEPS and built < BUILD_SHARE * j["s"]:
            out.append(f"STEPS {j['job']} ({j['kind']}): {j['tools']} agent steps, {j['s'] / 60:.0f} min, builds {built / 60:.1f} min "
                       f"({100 * built / j['s']:.0f}%) -> mostly agent steps; a script or a direct edit would do it")
    last_bake = max((i for i, b in enumerate(builds) if b.get("cmd") == "bake"), default=-1)
    n = sum(1 for b in builds[last_bake + 1:] if b.get("cmd") == "build")
    if n:
        out.append(f"BAKE  {n} build(s) since the last bake: bake before handing a walk over")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", nargs="?", default="report", choices=["report", "log"])
    ap.add_argument("--kind"); ap.add_argument("--job"); ap.add_argument("--s", type=float); ap.add_argument("--tools", type=int, default=0)
    a = ap.parse_args()
    if a.cmd == "log":
        if not (a.kind and a.job and a.s):
            sys.exit("log needs --kind --job --s")
        with AGENTS.open("a") as f:
            f.write(json.dumps({"time": time.strftime("%Y-%m-%dT%H:%M:%S"), "kind": a.kind, "job": a.job, "s": a.s, "tools": a.tools}) + "\n")
        return
    lines = report(rows(BUILDS), rows(AGENTS))
    print("slow_jobs: " + ("nothing flagged" if not lines else f"{len(lines)} flag(s)"))
    for l in lines:
        print("  " + l)


def demo():
    b = [{"cmd": "build", "job": "t1", "wall_s": 80}, {"cmd": "bake", "job": "t1", "wall_s": 90}, {"cmd": "build", "job": "t2", "wall_s": 80}]
    ag = [{"kind": "prop", "job": "t1", "s": 1200, "tools": 100}, {"kind": "prop", "job": "t2", "s": 600, "tools": 20}]
    r = report(b, ag)
    assert any(l.startswith("SLOW  prop") for l in r), r
    assert any(l.startswith("STEPS t1") for l in r), r          # 170 s of builds in a 1200 s job
    assert not any(l.startswith("STEPS t2") for l in r), r      # only 20 steps
    assert any(l.startswith("BAKE  1 build") for l in r), r
    assert report([], []) == []


if __name__ == "__main__":
    if "--demo" in sys.argv:
        demo(); print("demo ok")
    else:
        main()
