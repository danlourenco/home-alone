---
name: verify-plan
description: Verify the traced, calibrated floor plan and the reconciled house_spec.json against independent measurements, and lock in every fixed tracing mistake as a checkpoint. Use after ANY edit to measurements/overhead/*-trace.json, *-doors.json, measurements/rooms/*.json or tools/house/reconcile.py, before building the Unity grey-box, and whenever a render, video frame or playtest suggests a wall, door or room is in the wrong place.
---

# verify-plan

The plan is drawn by hand from an angled overhead render, so tracing mistakes are expected. On Oct 13, four corner boxes in the overhead were misread: a bath door ended up behind closets and Buzz's door on the wrong wall. This skill makes such mistakes fail loudly, and once a mistake is fixed it stays caught.

## Run it

```bash
uv run --with numpy --with matplotlib --with pillow python tools/house/verify_plan.py
```

The script rebuilds the plan (`tools/sfm/overhead_plan.py`) and the spec (`tools/house/reconcile.py`), then checks the result. It exits 1 on any FAIL. Do not build or ship the grey-box while it fails.

It prints one line per check:

- **reconciler**: a hard flag from the reconciler. Hard flags are walls under 8 cm (rooms overlap), doors with no shared wall or too little wall, failed adult body rules, and wall clusters spread over 20 cm.
- **on_door**: a measured doorway must fall on the spec door between the named spaces, within `tol`.
- **inside**: a measured open-floor point must lie inside the named space.
- **dimension**: a room's squared size must match an independent measurement within `tol_pct`.

It also writes `spec/captures/trace-review.png`: one zoomed tile per traced space, with the trace drawn on Marina's overhead. **Always look at it.** A plan can pass every number and still have a wall on a piece of furniture.

## When a check fails

1. Find out which side is wrong before changing anything. Gather evidence in this order:
   1. Gated SfM clips: the video passed COLMAP/VGGT agreement and is scaled from a door.
   2. Hall-walk and room frames, looked at directly.
   3. The overhead, read at 4x zoom with `zoom.py`-style gridded crops at ±3 px.
   4. Hand-placed topology.
2. **If the trace is wrong**, fix the trace. Where a gated clip measured the space, put the measured polygon in the trace as `"m"` (plan metres), with its source in `notes`. That overrides the overhead reading for that space.
3. **If the checkpoint is wrong or too strict**, edit it only with a written reason in its `source`, saying what was zoomed or measured and why. For example, the 7′ 6″ bracket check: Marina's bracket is drawn about 3 px past each inner wall edge. Never loosen a tolerance silently.
4. Rerun until it reaches 0 FAIL. Then rerun the Unity build (`SpecGreybox.Build`) and confirm its walk test still passes.

## Lock in the fix (required)

Every tracing mistake you fix adds the checkpoint that would have caught it, in `measurements/checkpoints/<floor>.json`. Fill in `caught` with the date and the mistake. Then prove the checkpoint works:

1. Put back the bad version (`git show <old>:<file> > <file>`).
2. Run the verifier and see it FAIL.
3. Restore the file and see it pass.

Unproven checkpoints don't count. The Oct 13 proof: the pre-fix trace fails 7 checks, and the fixed trace passes 12.

## Shape drift: does every room still feel like Marina's? (gate)

```bash
uv run --with numpy python tools/house/shape_drift.py        # both floors; exit 1 if a room drifts past 5%
uv run --with numpy --with matplotlib --with pillow python tools/house/verify_plan.py --floor ground
```

Compares each built room with Marina's overhead as traced, before stretching, thinning or stacking. Width, depth, proportion and area are checked per room. The rule (user, Oct 13): a room of notably different shape or size than Marina's is not acceptable. Every flagged room must be fixed or listed in `docs/DEVIATIONS.md`. Wall thinning makes small rooms read +10-15% (they gain a fixed 10-30 cm per side). Proportion changes are the ones that change feel.

## Wall-by-wall 3D check against the video (numeric gate)

```bash
uv run --with numpy python tools/house/reconcile.py --measured          # the house as measured (walls not thinned)
for c in hall-s1 parents kevin; do uv run --with numpy python tools/house/check_walls.py $c measured; done
```

This is the main check. For every wall of every space, it takes the gated clip's 3D wall points, but only from frames whose camera stands inside that space, and finds where they actually pile up relative to the spec's wall. The result is each wall's offset in centimetres (+ means the real room is bigger). A wall more than 8 cm out with a clear peak is flagged. On Oct 13 all three clips pass, with every long wall within ±7 cm.

How to read it:

- **A + offset** is unambiguous, because nothing stands beyond a wall.
- **A − offset** can be furniture against the wall (a dresser, a vanity). Look at the frames before moving a wall.
- **Glass walls give weak peaks** (a low peak share) and are not flagged.
- **Two opposite walls offset by the same amount** means the room is shifted, not resized. That's how the parents' bath was found 20 cm out.
- **Registration anchors must be wall-surface density peaks**, not `plan_extract` lines. One of Kevin's lines sat 8 cm off the surface.

## Visual check: matched-camera renders (not a gate)

```bash
uv run --with numpy --with scipy python tools/house/register_clip.py <clip>          # after changing anchors/features
for c in "hall-s1 0,11,21,36,48,59" "parents 0,6,12,21,30,46" "kevin 0,12,24,32,41,49"; do
  set -- ${=c}; uv run --with numpy --with scipy --with pillow --with opencv-python-headless python tools/house/match_cameras.py poses $1 $2; done
Unity -batchmode -projectPath unity/HomeAlone -executeMethod SpecGreybox.Build -quit -logFile -                       # built house
Unity -batchmode -projectPath unity/HomeAlone -executeMethod SpecGreybox.Build -quit -logFile - -variant measured     # as measured
Unity -batchmode -projectPath unity/HomeAlone -executeMethod SpecGreybox.RenderMatched -quit -logFile - [-variant measured]
for c in hall-s1 parents kevin; do uv run --with numpy --with scipy --with pillow python tools/house/match_cameras.py compare $c [measured]; done
```

- Each camera is re-solved from its own frame's point map (PnP), because VGGT's camera head and point head disagree slightly.
- The renders give every surface its own flat colour, so a colour change is exactly a geometric edge.
- `compare.png` draws the grey-box edges over Marina's frames. **Look at it; don't gate on its number.** In the Oct 13 sensitivity test, moving the camera 20 cm did not reliably worsen the edge score, and some views scored better. Faint real corners lose to nearby clutter.

## Test the tests (required for every gate)

A check counts only once it has been shown to FAIL on a known-bad input, and its detection limit is written down. The image edge score looked fine on real data, but when the camera was moved 20 cm on purpose it couldn't tell, so it is now visual-only. Proven limits (Oct 13):

| Gate | Proof | Detection limit |
|---|---|---|
| `verify_plan.py` checkpoints | The pre-fix trace (`git show 50b9f54:...`) gives 7 FAIL; the current trace gives 0 | Door checks: 30 cm (loose, by design for overhead reading error). Dimensions: 4–6% |
| `check_walls.py` | `tools/house/test_checks.py` injects 0/5/10/20 cm wall errors in 3 rooms | Reads errors to within 1–3 cm; **flags 10 cm or more**. 5 cm reads correctly but isn't flagged |
| Unity stair walk test (adult + Kevin, up and down the main stair) | Removing one step (a 0.34 m double rise) blocks 8 of 20 legs and names the step | Blocks any single rise over the 0.30 m step offset; it does not see cm-level rise errors |
| Unity adult walk test | `-variant inject_door` with 0.45 and 0.50 m doors gives both BLOCKED, every other door ok | Physically blocks doors narrower than the 0.55 m capsule. The reconciler rule flags under 0.65 m |
| Door checkpoints (centre along the wall) | Kevin's hall door shifted 10 and 20 cm in the inputs: FAIL at 17 and 26 cm against a 7 cm baseline | 10 cm (tol 15). Across-wall tolerance is separate (`tol_across`) because a door measured on one face sits half a wall-thickness off the centre line |
| Registration (`register_clip.py --loo [--rigid]`) | Leave-one-out over anchor walls | Hall (rigid): median 5, max 10.5 cm. Kevin: median 3.5, max 6 |
| Matched-camera edge score | A 20 cm camera shift did not reliably worsen it | **None. Visual only** |

Run `uv run --with numpy python tools/house/test_checks.py` after changing `check_walls.py`, the registrations or the tolerances.

## Independent vs consistency checks

A check is **independent** only if its evidence played no part in building the plan. As of Oct 13 there are 6 of 15: Marina's 7′ 6″ label, the parents' bath width, the overhead's open door leaf, plus three from the far-end hall clip (hall-s4), which never built anything. That clip has a rigid registration on the passage and end walls only. Its checks are Kevin's hall door (7 cm), the parents' hall door (7 cm) and the passage width (1.22 m, where the overhead traced 1.07: walls too thick there, and the thinned build matches). The others are **consistency** checks; they still matter, because they catch edits that break agreement:

- The hall doorways come from the same clip that placed the doors.
- The room sizes of Kevin and Buzz were inputs to the overhead calibration.
- The walls checked by `check_walls.py` for hall-s1, parents and Kevin were partly used to fit those clips' registrations.

`verify_plan.py` prints each check's kind. To get independent evidence, use clips the plan was not built from (hall-s4, the Buzz clip). Alternatively, fit a registration on some walls and check the others (held-out). Never count a consistency pass as proof of faithfulness. Before any geometry change, the `change-gate` skill makes this mechanical: its tool fails a change with no independent agreeing check.

## Where checkpoints come from

- **Gated SfM clips** (`sfm-work/rooms/<name>/`): door jambs, wall lines, open floor.
  - Measure 3D points from `pixels.npz` in the clip's plan frame. Scale them by the clip's door (`tools/sfm/door_scale.py`).
  - Register the clip to the plan by matching two features both sources show, such as an arch and a door.
  - Record the registration in `registrations`.
- **SfM-measured rooms**: their size, scaled from their own doors.
- **Marina's on-screen dimensions and the overhead's visible details**, such as an open door leaf.
- **The film's must-match shots**, once the camera matching exists.

## Gotchas (from real mistakes)

- **Furniture reads as walls** in SfM density, both tall pieces (an armoire, a folding screen) and bed rails. Check every short wall step against the frames.
- **Small boxes in the overhead lie.** Wall tops hide doorways, and shelves look like closets. A space that touches nothing walkable is a red flag.
- **Walls in Marina's model are 25–45 cm thick.** The spec thins interior walls to 14 cm (user decision). Compare room sizes on the plan stage, not the thinned spec.
- **Measured door spans often include casing**, typically +4 to 8 cm. Centre a standard door inside them.
- **Unity is left-handed.** World z = −spec z, otherwise the house builds mirrored. The bird's-eye capture must match Marina's overhead room for room.
- **Image edge scores can't see 20 cm.** Use `check_walls.py` for numbers and the overlays for eyes.
- **The reconciler slides a measured door up to 15 cm to fit its wall without flagging it**, which can hide a door error. A +20 cm injected shift was slid back onto the measured spot. When a door check passes suspiciously well, look at the slide note in `spec/upstairs-changes.md`.
- **Fitting scale can absorb the error you're testing for.** When both sides are metric, register rigidly (`"rigid": true`); the far-end clip's scale fit would have hidden a 15 cm width difference.
- **A railing is not a wall.** The rail stands on the stairwell's edge, and the hall reaches it (`RAIL_T` in the reconciler).
- **Height histograms mis-measure ceilings** because of camera tilt. Measure ceilings on a door wall as wall height relative to door height.
- **On stairs, VGGT depth lies along the flight.** Both stair clips gave 24-27 deg pitch against 35 deg from vanishing points. Measure pitch with `tools/sfm/stair_pitch.py` (it has a `--selftest`). Take only heights and lateral sizes from 3D.
- **Door edge pixels can sit on a depth jump** (a door recessed under an arch read 14% short). `stair_measure.door_height` fits the slab's interior instead.
- **Never run two `test_checks.py` at once**: they share `spec/house_spec.test.json`.
- **Captions and dissolves** sit at the ends of kept frame ranges. Trim them before solving.
