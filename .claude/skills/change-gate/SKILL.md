---
name: change-gate
description: Gate for ANY change that moves, resizes or adds geometry in either model (IntactHouseReference or the grey-box): walls, rooms, doors, windows, stairs, furniture placement. Use BEFORE proposing or making such a change, and before telling the user a change is verified. Enforced by the pre-commit hook (.githooks/pre-commit) and tools/house/change_gate.py.
---

# change-gate: prove the number independently, look at the result, let the user accept it

Why this exists (Oct 13): Buzz's room was resized to the SfM size 4.35 m. The "proof" was that Marina's cameras now stood inside the room, but those cameras came from the same reconstruction and door scale as the 4.35 m, so they could not have disagreed. Four attempts on that same premise had already failed. The result looked broken, and the user called it "terrible". It was reverted. `changes/2026-10-13-buzz-resize.json` is that change as a record; the gate fails it on all three rules, and `--selftest` keeps it failing.

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

   A check that reuses the claim's clip, solve or door scale is consistency. It's still worth running, but it never counts as proof and must never be reported as proof. If no independent check exists, **don't make the change**. Tell the user what evidence is missing.
4. **Make the smallest change**, re-runnable and reversible: editor scripts or the spec, never hand edits. The source GLB stays untouched.
5. **Look at it (R3).** Render before and after from the same fixed views, inside and outside, and list the paths. Open the images and look for breakage: stretched or smeared textures, seams, gaps, floating or buried objects, doors and windows out of their walls, and bumps in the exterior. Numbers passing doesn't mean it looks right.
6. **Run the gates:** `uv run python tools/house/change_gate.py changes/<file>.json` (0 FAIL), plus the usual verify-plan, shape_drift, ledger_lint and walk checks.
7. **Report it as a TRIAL.** `user_walk: pending` until the user walks it. Tell them what to look at, and never call it done or verified before they accept it. Record their words and the outcome (`accepted` / `rejected`). A rejection adds a `failed` history entry, which feeds R2 next time.

## Rules the tool enforces

| Rule | Fails when |
|---|---|
| R1 | No agreeing check is independent of the claim's data, scale and upstream |
| R2 | Two or more failed attempts are on record and `premise_reviewed` is empty |
| R3 | Before or after renders are missing on disk |

The pre-commit hook blocks commits that touch `measurements/`, `spec/house_spec*`, `spec/furniture.json`, `tools/house/reconcile.py` or the two house scenes unless a staged `changes/*.json` passes. Commit pure rebuild outputs (same inputs, rebuilt) with `--no-verify`, and say so in the message.

Prove the gate still works after editing it: `uv run python tools/house/change_gate.py --selftest`.
