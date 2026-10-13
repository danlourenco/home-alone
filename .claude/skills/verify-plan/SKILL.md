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
- **Height histograms mis-measure ceilings** because of camera tilt. Measure ceilings on a door wall as wall height relative to door height.
- **Captions and dissolves** sit at the ends of kept frame ranges. Trim them before solving.
