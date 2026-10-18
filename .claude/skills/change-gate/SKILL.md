---
name: change-gate
description: Gate for ANY change that moves, resizes or adds geometry in either model (IntactHouseReference or the grey-box): walls, rooms, doors, windows, stairs, furniture placement. Use BEFORE proposing or making such a change, and before telling the user a change is verified. Enforced by the pre-commit hook (.githooks/pre-commit) and tools/house/change_gate.py.
---

# change-gate: prove the number independently, look at the result, let the user accept it

Why this exists (Oct 13): Buzz's room was resized to the SfM size 4.35 m. The "proof" was that Marina's cameras now stood inside the room, but those cameras came from the same reconstruction and door scale as the 4.35 m, so they could not have disagreed. Four attempts on that same premise had already failed. The result looked broken, and the user called it "terrible". It was reverted. `changes/2026-10-13-buzz-resize.json` is that change as a record; the gate fails it on all three rules, and `--selftest` keeps it failing.

**Decorations skip this gate** (user Oct 17: "a wreath on a door is not load bearing like a wall. it's just a decoration"; rule approved: "yes"): a wreath, ornament, picture, plant or other dressing that nothing walks on, hides under or measures from needs no change record. Place it, build once through `unity_pipeline.sh` (preflight, z-fight and clash still run), look at one render, load it, and commit with `git commit --no-verify`, saying "decoration" in the message. Furniture and anything that changes where Kevin or a bandit can walk or hide is NOT decoration.

**Props lane** (user Oct 17, on a 25-minute trunk job: "we might need to revisit our approach for something like a trunk vs more permanent fixtures"; approved: "yes, that's much better"): movable props (a trunk, a bin, books, toys, posters, easter eggs, an animal) and freestanding furniture that nothing is built from also skip this gate, like decorations. Size from the product's real dimensions or ONE ruler in a film frame (no spread, no second ruler); place by eye from the film (Marina where the film doesn't show it); no change record, no bake; batch several props per build; one render; the user nudges them in the walk or places them in the Scene view (W move, E rotate) and clicks **Home Alone > Save Prop Placement** (Editor/SavePropPlacement.cs writes store_props.json / buzz_trunk.json); commit with `--no-verify`, "prop" in the message. Still required: z-fight/clash 0 and the walk passages clear (an adult, radius 0.275 + skin 0.02). Stays a FIXTURE (full gate): walls, openings, trim, stairs, built-ins, and any furniture Kevin or a bandit can hide under or inside (e.g. Buzz's low bed).

## Steps, in order. Don't skip ahead.

1. **Write the record first**, `changes/<date>-<slug>.json` (copy the Buzz record's shape), before touching geometry:
   - `premise`: the one sentence the change assumes.
   - `claim`: the target numbers, with `data` (which clip, frames or image), `scale` (which door or object set the metres) and `upstream` (what those were calibrated from). Use the same ids everywhere: `vggt:<run>`, `door-80in:<clip>`, `marina-frame:<s>`, `overhead-trace:<floor>`.
   - `history`: every earlier attempt on the same room or element. Grep `docs/DEVIATIONS.md`, `tasks/*.md` and `art/home_alone/references/<room>/README.md` for it.
2. **Premise check (R2).** If two or more attempts failed, stop. Before any fix, write in `premise_reviewed` why the premise still stands, with a census (skill principle-attack-the-premise): which inputs every failed attempt shared. Usually the shared input is the suspect.
3. **Independent evidence (R1).** At least one check must agree with the claim **and share no data, scale or upstream id with it**. Ways to get one:
   - **A known-size object as the ruler** in a frame the measurement didn't use: a twin mattress 0.99 m wide, an 80 in door, a 30 in door leaf, a standard window.
   - **A different clip, or a held-out wall** (verify-plan: hall-s4).
   - **Film frames.**
   - **A source with its own scale**: Marina's on-screen dimensions, or the real-house plan.

   **Pick check (before measuring any pixel feature in a film or Marina frame):** save a crop of the picked point (e.g. `spec/captures/picks/<slug>-<frame>.png`) and get an independent look that says WHAT it is: a subagent shown only the crop and asked to name the feature, or the same feature found in a second frame. Record it on the check (or claim) as `"pick": {"crop": "<path>", "confirmed_by": "<who/what, and what they said it is>"}`. R8 enforces it for records with `"gate": 8` (Oct 16-17: the arch crown was picked on the landing's fascia, and a "casing" the film doesn't have was measured).

   The build's self-consistency gates (`model_quality`, `zfight`, `clash`, `verify_plan`, `trim_faces`, `unity:build`, `unity:walk-test`) check the model against itself, never against the house: they are never the independent ruler.

   A check that reuses the claim's clip, solve or door scale is consistency. It's still worth running, but it never counts as proof and must never be reported as proof. If no independent check exists, **don't make the change**. Tell the user what evidence is missing.
4. **Make the smallest change**, re-runnable and reversible: editor scripts or the spec, never hand edits. The source GLB stays untouched.
5. **Look at it (R3).** Render before and after from the same fixed views, inside and outside, and list the paths. Open the images and look for breakage: stretched or smeared textures, seams, gaps, floating or buried objects, doors and windows out of their walls, and bumps in the exterior. Numbers passing doesn't mean it looks right.
6. **Run the gates:** `uv run python tools/house/change_gate.py changes/<file>.json` (0 FAIL), plus the usual verify-plan, shape_drift, ledger_lint and walk checks.
7. **Report it as a TRIAL.** `user_walk: pending` until the user walks it. Tell them what to look at, and never call it done or verified before they accept it. Record their words and the outcome (`accepted` / `rejected`). A rejection adds a `failed` history entry, which feeds R2 next time.

## Rules the tool enforces

| Rule | Fails when |
|---|---|
| R1 | No agreeing check is independent of the claim's data, scale and upstream (self-consistency gates never count) |
| R2 | Two or more failed attempts are on record and `premise_reviewed` is empty |
| R3 | Before or after renders are missing on disk |
| R4 | The claim doesn't list `applies_to` and `measured_in`, or it is built into an item it wasn't measured in without an `assumed` DEVIATIONS row |
| R5 | A ceiling claim's `surface` is not `ceiling-plane` (crown, beam, landing or soffit edges are not ceilings) |
| R6 | A disagreeing check that is evidence has no `disposition` (why the claim stands, or what was done about it) |
| R8 | (records with `"gate": 8`) A metric check (or claim) on a film/Marina frame lacks `pick.crop` on disk or `pick.confirmed_by` |
| R7 | (records with `"gate": 7`) A layout claim (which way a stair runs or turns, where its parts are) lacks `alternatives` (the current build included), or a part where the alternatives differ is not seen directly in 2+ unoccluded frames, or is extrapolated (`claim.layout.decides`) |

Each check may give a `type`: `metric` (default), `angular`, `ratio` or `topological`. Only a metric check needs a ruler; an angle or ratio with scale `none` is evidence. If the claim lists `risks` (e.g. `extraction`, `scale`, `registration`, `model-fidelity`), R1 needs an independent agreeing check whose `tests` covers each one: two Marina clips can test extraction but not her model's film accuracy, and two frames on one assumed door can't test the door.

Seams: a committed grey-box scene must also pass `tools/house/seam_gate.py` (no unexplained flicker, ledge or gap in the build's seam check; known ones live in `measurements/checkpoints/seams-known.json` with a reason). The pre-commit hook runs it.

Independence is judged by **ruler kind**: `door-80in:1125` and `door-80in:1175` are the same ruler. A check resting only on a lead (`user-summary`, `ai`, `summary`, `web-summary`, `recollection`, `standard`, `none`) never counts as evidence. When geometry is committed, every record not rejected is re-gated, so nothing new lands on a change the gate now fails.

**Talking to the user:** say only what the gate says. Never "ruled out", "confirmed" or "proven" for a number whose record fails, and name the ruler and its assumption in the same sentence.

The pre-commit hook blocks commits that touch `measurements/`, `spec/house_spec*`, `spec/furniture.json`, `spec/geometry.json`, `spec/trim_faces.json`, `spec/dressing/`, `tools/house/reconcile.py`, `tools/house/hifi_*.py` or the house scenes (IntactHouseReference, Greybox_Upstairs, House_WallGrid) unless a staged `changes/*.json` passes. Commit pure rebuild outputs (same inputs, rebuilt) with `--no-verify`, and say so in the message.

Prove the gate still works after editing it: `uv run python tools/house/change_gate.py --selftest`.
