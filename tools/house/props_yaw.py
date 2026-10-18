"""props_yaw: furniture store props must have a PINNED yaw (Oct 18: shape-guessed fronts kept coming out 180 deg wrong under both the
vertex and the area heuristic: armoire, clock, guest and attic beds). Lists every non-door, non-book piece with a "back" but no
"yaw": pin each after a front render. Informational in preflight (never fails), so it nags until they're all pinned.
  python3 tools/house/props_yaw.py
"""
import json
from pathlib import Path
SKIP = ("door", "book")
P = json.loads((Path(__file__).resolve().parents[2] / "spec/dressing/store_props.json").read_text())["pieces"]
todo = [p["name"] for p in P if p.get("back") and p.get("yaw") is None and not any(k in p["name"] for k in SKIP)]
print(f"props_yaw: {len(todo)} furniture piece(s) on a guessed turn" + (": " + ", ".join(todo) if todo else ""))
