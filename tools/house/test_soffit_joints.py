"""Regression: walked stair fails, supported stair passes, incomplete fascia fails.

uv run -q --with trimesh --with numpy --with scipy python -I tools/house/test_soffit_joints.py
The old model comes from its committed LFS object; no working files are replaced.
"""
import contextlib
import io
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import trimesh

sys.path.insert(0, str(Path(__file__).resolve().parent))
import soffit_joints as gate


def check(path):
    output = io.StringIO()
    with contextlib.redirect_stdout(output):
        result = gate.main(path)
    return result, output.getvalue()


def main():
    model = "unity/HomeAlone/Assets/Models/Foyer/MainStair.glb"
    with tempfile.TemporaryDirectory() as directory:
        old = Path(directory) / "walked.glb"
        pointer = subprocess.check_output(["git", "show", f"381c7e42:{model}"], cwd=gate.ROOT)
        old.write_bytes(subprocess.run(["git", "lfs", "smudge"], input=pointer, capture_output=True, check=True, cwd=gate.ROOT).stdout)
        result, output = check(old)
        assert result == 1 and "HANGING 47 of 90" in output and "50 mm off" in output, output
        result, output = check(gate.ROOT / model)
        assert result == 0 and "90 baluster feet checked" in output, output

        # Leave a corner on the correct plane but remove half the fascia's surface.
        scene = trimesh.load(gate.ROOT / model, force="scene")
        stair = json.loads((gate.ROOT / "spec/house_spec.json").read_text())["stair"]
        boxes = {b["name"]: b for b in stair["boxes"]}
        outer = boxes["landing_rail_cap"]["x"][1]
        landing = boxes["landing"]
        removed = False
        for node in scene.graph.nodes_geometry:
            transform, name = scene.graph[node]
            if not node.startswith("RisersStringers"):
                continue
            mesh = scene.geometry[name]
            vertices = mesh.vertices @ transform[:3, :3].T + transform[:3, 3]
            vertices = np.c_[-vertices[:, 0], vertices[:, 1], -vertices[:, 2]]
            triangles = vertices[mesh.faces]
            centre = triangles.mean(1)
            faces = np.flatnonzero((np.abs(triangles[:, :, 0] - outer).max(1) < 1e-5) &
                                   (centre[:, 1] > landing["y"][0]) & (centre[:, 1] < landing["y"][1] - 0.025))
            assert len(faces) == 2, faces
            keep = np.ones(len(mesh.faces), bool)
            keep[faces[0]] = False
            mesh.update_faces(keep)
            removed = True
        assert removed
        broken = Path(directory) / "missing-fascia.glb"
        scene.export(broken)
        result, output = check(broken)
        assert result == 1 and "landing fascia coverage" in output, output
    print("PASS walked model rejected; supported model passes; incomplete fascia rejected.")


if __name__ == "__main__":
    main()
