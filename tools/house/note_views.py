"""Every in-game walk note (spec/feedback/feel-notes.jsonl, key M) as a Unity RenderViews entry from the note's own position, yaw and
pitch, so a fix is checked from exactly the view the user complained about (Oct 15: two "fixed" ceilings were checked from guessed views).

  uv run python -I tools/house/note_views.py [--since 2026-10-15T16:00] [--scene House_WallGrid]   -> spec/captures/views/notes.json
  then: Unity -batchmode ... -executeMethod SpecGreybox.RenderViews -scene House_WallGrid -views notes.json   (renders views/notes/<time>.png)
"""
import json, math, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
EYE, VFOV = 1.65, 60.0     # Player eye: standHeight 1.8 - eyeOffset 0.15 above its root (FpsController; FeelNotes logs the root), and its camera's vertical field of view

def view(n):
    yaw, pitch = math.radians(n["yaw"]), math.radians(n["pitch"])
    f = [math.sin(yaw) * math.cos(pitch), -math.sin(pitch), math.cos(yaw) * math.cos(pitch)]   # Unity: pitch > 0 looks down
    p = [n["pos"][0], n["pos"][1] + EYE, n["pos"][2]]
    return {"name": "notes/" + n["time"].replace(":", ""), "pos": [round(v, 3) for v in p], "look_at": [round(p[i] + f[i], 3) for i in range(3)], "vfov": VFOV}

if __name__ == "__main__":
    since = sys.argv[sys.argv.index("--since") + 1] if "--since" in sys.argv else ""
    scene = sys.argv[sys.argv.index("--scene") + 1] if "--scene" in sys.argv else "House_WallGrid"
    N = [json.loads(l) for l in (ROOT / "spec/feedback/feel-notes.jsonl").read_text().splitlines() if l.strip()]
    V = [view(n) for n in N if n["time"] >= since and n.get("scene") == scene]
    assert view({"time": "t", "pos": [0, 0, 0], "yaw": 90, "pitch": 0})["look_at"] == [1.0, EYE, 0.0]   # yaw 90 looks along +x
    (ROOT / "spec/captures/views/notes.json").write_text(json.dumps(V, indent=1)); print(len(V), "note views ->", "spec/captures/views/notes.json")
