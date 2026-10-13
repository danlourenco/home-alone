# Home Alone house

Goal: a faithful, walkable Unity recreation of the McCallister house. Faithfulness is non-negotiable; do not propose "good enough" geometry.

- **Current plan:** [tasks/sfm-plan.md](tasks/sfm-plan.md). Start there. HANDOFF.md below its first entry is history.
- **Engine:** Unity only (`unity/HomeAlone`). The Godot files at repo root are retired; don't extend them.
- **Method:** geometry comes from structure-from-motion on Marina Coates's tour videos (repo root `*.mp4`, 1080p copies), not hand-picked landmarks. Tooling in `tools/sfm/`; regenerable outputs in `sfm-work/` (gitignored). Python via `uv run --with numpy --with matplotlib python -I ...`; COLMAP is Homebrew 4.2.1, CPU only.
- **Verification:** a dimension isn't accepted without a re-runnable script, a spread, and a check on held-out views. Never average conflicting sources; log deviations.
- Evidence and source weights: `art/home_alone/references/` (see `dimensional-baseline/SOURCE_WEIGHTS.md`).
