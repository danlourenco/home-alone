# Home Alone house

Goal: a faithful, walkable Unity recreation of the McCallister house. Faithfulness is non-negotiable; do not propose "good enough" geometry.

- **Current state and next step (read first):** [docs/STATUS.md](docs/STATUS.md).
- **Every departure from measurement** (stretches, assumptions, authored sizes) goes in [docs/DEVIATIONS.md](docs/DEVIATIONS.md) with its size and how to revisit it. The house must feel authentic: a room of notably different shape or size than Marina's is not acceptable.
- **How the house gets built:** [docs/RECONCILIATION.md](docs/RECONCILIATION.md). Experiment log: [tasks/sfm-plan.md](tasks/sfm-plan.md). HANDOFF.md below its first entry is history.
- **Scale the players, not the house:** true-scale house; Kevin is a kid-sized body (can hide under beds), bandits are adults.
- **Engine:** Unity only (`unity/HomeAlone`). The Godot files at repo root are retired; don't extend them.
- **Method:** geometry comes from structure-from-motion on Marina Coates's tour videos (repo root `*.mp4`, 1080p copies), not hand-picked landmarks. Tooling in `tools/sfm/`; regenerable outputs in `sfm-work/` (gitignored). Python via `uv run --with numpy --with matplotlib python -I ...`; COLMAP is Homebrew 4.2.1, CPU only.
- **Verification:** a dimension isn't accepted without a re-runnable script, a spread, and a check on held-out views. Never average conflicting sources; log deviations.
- **Plan changes:** after any edit to a trace, doors file, room measurement or the reconciler, run the `verify-plan` skill (`.claude/skills/verify-plan/SKILL.md`; `tools/house/verify_plan.py`). 0 FAIL before building the grey-box. Every fixed tracing mistake adds a proven checkpoint.
- **Geometry changes (either model):** follow the `change-gate` skill (`.claude/skills/change-gate/SKILL.md`). Write the record first. At least one agreeing check must share no data, scale or upstream with the number. Look at before/after renders. Report the change as a TRIAL until the user walks it. The pre-commit hook enforces this (`git config core.hooksPath .githooks` once per clone).
- Evidence and source weights: `art/home_alone/references/` (see `dimensional-baseline/SOURCE_WEIGHTS.md`).
- **Slow jobs:** `tools/house/slow_jobs.py` (run at session start by `.claude/settings.json`, and in preflight) flags recurring slow work and builds since the last bake. When it flags a job kind, propose the tool that removes the slowness before running another job of that kind. Log every agent job when it hands back: `python3 tools/house/slow_jobs.py log --kind prop|fixture|tool|search|render --job NAME --s SECONDS --tools N`.
