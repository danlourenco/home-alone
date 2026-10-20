#!/usr/bin/env python3
"""Slow jobs: flag recurring work that should become a tool (user Oct 17: "what is the trigger for the agent to determine when
routine work becomes slow? what's the right mechanism for this?").

Reads spec/captures/build-log.jsonl (every build/bake, written by unity_pipeline.sh) and spec/captures/agent-log.jsonl (one line
per agent job, appended with `slow_jobs.py log ...` when an agent hands back). Prints a few lines; the SessionStart hook in
.claude/settings.json runs it so the report lands in Claude's context without anyone remembering to look.

  python3 tools/house/slow_jobs.py                       # the report
  python3 tools/house/slow_jobs.py log --kind prop --job buzztrunk --s 1258 --tools 101 [--builds 2]
  python3 tools/house/slow_jobs.py start --kind fixture --job basement-shell [--at 11:08]   # when an agent is launched
  python3 tools/house/slow_jobs.py eta [--line]          # running jobs: elapsed vs the kind's past median/p75 (statusline: --line)

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
RUNNING = Path.home() / ".cache/home-alone-2/running.jsonl"   # runtime state, not in the repo
STALE = 6 * 3600                                               # no agent job runs 6 h; older entries are dead
BUILDLOG = Path.home() / ".cache/home-alone-2/build.log"
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


def short(running, agents, now, building=None):
    """the status-line form: 'basement-shell 44m (over usual) · guest-room 36m (~0-7m left) · Unity building'"""
    out = []
    for r in running:
        past = sorted(a["s"] for a in agents if a["kind"] == r["kind"])
        el = now - r["start"]
        if past:
            med, p75 = past[len(past) // 2], past[min(len(past) - 1, (3 * len(past)) // 4)]
            tag = f"~{max(0, med - el) / 60:.0f}-{max(0, p75 - el) / 60:.0f}m left" if el < p75 else "over usual"
        else:
            tag = "no history"
        out.append(f"{r['job']} {el / 60:.0f}m ({tag})")
    if building:
        out.append("Unity " + building)
    return out


def eta(running, agents, now, building=None):
    """one line per running job: elapsed, and the remaining time against the median and 75th percentile of past jobs of its kind"""
    out = []
    for r in running:
        past = sorted(a["s"] for a in agents if a["kind"] == r["kind"])
        el = now - r["start"]
        if past:
            med, p75 = past[len(past) // 2], past[min(len(past) - 1, (3 * len(past)) // 4)]
            left = f"~{max(0, med - el) / 60:.0f}-{max(0, p75 - el) / 60:.0f} min left" if el < p75 else "past the usual time"
            out.append(f"{r['job']} ({r['kind']}): {el / 60:.0f} min in, {left} (median {med / 60:.0f}, n={len(past)})")
        else:
            out.append(f"{r['job']} ({r['kind']}): {el / 60:.0f} min in, no history")
    if building:
        out.append(f"Unity: {building}")
    return out


def building_now():
    import subprocess
    if subprocess.run(["pgrep", "-f", "unity_pipeline.sh"], capture_output=True).returncode != 0:
        return None
    step = [l for l in BUILDLOG.read_text(errors="ignore").splitlines()[-400:] if "BuildWallGrid:" in l or "Bake" in l] if BUILDLOG.exists() else []
    return "building" + (f" ({step[-1].split('BuildWallGrid:')[-1].strip()[:50]})" if step else "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", nargs="?", default="report", choices=["report", "log", "start", "eta"])
    ap.add_argument("--at"); ap.add_argument("--line", action="store_true")
    ap.add_argument("--kind"); ap.add_argument("--job"); ap.add_argument("--s", type=float); ap.add_argument("--tools", type=int, default=0)
    a = ap.parse_args()
    if a.cmd == "log":
        if not (a.kind and a.job and a.s):
            sys.exit("log needs --kind --job --s")
        with AGENTS.open("a") as f:
            f.write(json.dumps({"time": time.strftime("%Y-%m-%dT%H:%M:%S"), "kind": a.kind, "job": a.job, "s": a.s, "tools": a.tools}) + "\n")
        RUNNING.parent.mkdir(parents=True, exist_ok=True)
        RUNNING.write_text("".join(json.dumps(r) + "\n" for r in rows(RUNNING) if r["job"] != a.job))   # it handed back
        return
    if a.cmd == "start":
        t = time.time()
        if a.at:
            h, m = map(int, a.at.split(":")); lt = time.localtime(); t = time.mktime((lt.tm_year, lt.tm_mon, lt.tm_mday, h, m, 0, 0, 0, -1))
        RUNNING.parent.mkdir(parents=True, exist_ok=True)
        keep = [r for r in rows(RUNNING) if r["job"] != a.job]          # a re-start of the same job replaces it (no duplicates)
        if any(r["job"] == a.job for r in rows(RUNNING)):
            t = min(r["start"] for r in rows(RUNNING) if r["job"] == a.job)
        RUNNING.write_text("".join(json.dumps(r) + "\n" for r in keep + [{"kind": a.kind, "job": a.job, "start": t}]))
        return
    if a.cmd == "eta":
        live = [r for r in rows(RUNNING) if time.time() - r["start"] < STALE]   # a job never logged (died, or logged by another name) drops off
        if len(live) != len(rows(RUNNING)):
            RUNNING.write_text("".join(json.dumps(r) + "\n" for r in live))
        args = (live, rows(AGENTS), time.time(), building_now())
        lines = short(*args) if a.line else eta(*args)
        print("\n".join(lines) or "no agent jobs running")
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
    e = eta([{"kind": "prop", "job": "t3", "start": 0}], ag, 300)
    assert "t3 (prop): 5 min in, ~15-15 min left" in e[0], e       # median and p75 of [600, 1200] are both 1200 here
    assert short([{"kind": "prop", "job": "t3", "start": 0}], ag, 300) == ["t3 5m (~15-15m left)"]
    assert "past the usual time" in eta([{"kind": "prop", "job": "t4", "start": 0}], ag, 2000)[0]


if __name__ == "__main__":
    if "--demo" in sys.argv:
        demo(); print("demo ok")
    else:
        main()
