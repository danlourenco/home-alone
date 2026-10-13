"""Test the tests (verify-plan skill): every gate must be shown to FAIL on a known-bad input.

Injects known wall errors into a copy of the as-measured spec and asserts check_walls.py reports them:
  - untouched walls read within +-5 cm and are not flagged
  - a 10 cm or 20 cm wall error reads back within 4 cm of the injected amount and IS flagged
The 5 cm case is printed but not asserted: it reads back correctly but sits under the 8 cm flag threshold (the
documented detection limit). The Unity walk test's sensitivity (blocks doors under the 0.55 m adult capsule) is
proven separately with the inject_door variant; see the skill.
usage: uv run --with numpy python tools/house/test_checks.py
"""
import copy
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# (clip, space, wall axis, wall coordinate in the measured spec, outward sign used to move it)
WALLS = [("kevin", "kevin_jeff_room", "x", 11.66, +1), ("parents", "parents_bedroom", "x", 8.49, +1),
         ("hall-s1", "hall_corridor", "x", 7.16, -1)]


def offset(clip, variant, space, axis, coord):
    out = subprocess.run(["uv", "run", "-q", "--with", "numpy", "python", "tools/house/check_walls.py", clip, variant],
                         cwd=ROOT, capture_output=True, text=True, check=True).stdout
    for line in out.splitlines():
        f = line.split()
        if len(f) >= 6 and f[0] == space and f[1].startswith(f"{axis}=") and abs(float(f[1][2:]) - coord) < 0.03:
            return float(f[4]), "<-- check" in line
    raise AssertionError(f"{space} wall {axis}={coord:.2f} not seen by {clip}")


def main():
    base = json.loads((ROOT / "spec/house_spec.measured.json").read_text())
    try:
        for cm in (0, 5, 10, 20):
            s = copy.deepcopy(base)
            for _, name, axis, c, sgn in WALLS:
                k = 0 if axis == "x" else 1
                for sp in s["spaces"]:
                    if sp["name"] == name:
                        sp["polygon_xz"] = [[v[i] + (sgn * cm / 100 if i == k and abs(v[k] - c) < 0.02 else 0) for i in (0, 1)]
                                            for v in sp["polygon_xz"]]
            (ROOT / "spec/house_spec.test.json").write_text(json.dumps(s))
            for clip, name, axis, c, sgn in WALLS:
                got, flagged = offset(clip, "test", name, axis, c + sgn * cm / 100)
                base_off, _ = offset(clip, "measured", name, axis, c)
                moved = abs(got - base_off)
                print(f"inject {cm:2d} cm  {name:<16} {axis}={c:.2f}: reads {got:+.0f} cm (baseline {base_off:+.0f}), moved {moved:.0f}, flagged={flagged}")
                if cm == 0:
                    assert abs(got) <= 5 and not flagged, "an untouched wall must read within 5 cm and not be flagged"
                elif cm >= 10:
                    assert abs(moved - cm) <= 4 and flagged, f"a {cm} cm error must read back within 4 cm and be flagged"
    finally:
        (ROOT / "spec/house_spec.test.json").unlink(missing_ok=True)
    print("check_walls sensitivity: PASS")


if __name__ == "__main__":
    main()
