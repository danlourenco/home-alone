# Current status — start here (October 13, 2026)

The upstairs is measured, reconciled into a spec, built as a walkable Unity grey-box, and verified against video. That includes independent evidence. **Next: the ground floor.** Background reading: [RECONCILIATION.md](RECONCILIATION.md) for the architecture, [tasks/sfm-plan.md](../tasks/sfm-plan.md) for the full experiment log, and the `verify-plan` skill for every check.

Branch `unity-sfm-reconstruction`, pushed to `origin`. Git LFS covers `*.glb *.blend *.exr *.fbx *.psd *.tif *.tiff *.npz`.

## User decisions (binding)

- **Faithfulness is non-negotiable.** Never propose "good enough" geometry.
- **Unity only.** Godot is retired.
- **Scale the players, not the house.** Kevin is about 1.1 m eye height and can crawl in about 0.4 m. The bandits are about 1.7 m eye height, with a hard adult-capsule rule (0.55 m diameter, 1.85 m tall).
- **Thin the interior walls to 14 cm.** Marina's are 25–45 cm. Keep each wall's centre line; rooms take the freed space. Exterior walls are unchanged.
  - Independent evidence backs this: the far-end hall passage measures 1.22 m, the overhead traced 1.07 m, and the thinned build gives 1.23 m.
- **Closets don't need to open.** The linen closet has a prop door; the other shallow closets are sealed.
- **Door height** is 80 in nominal, 78–80 in honest. The area check brackets Marina's 1,900 ft², and 84 in is ruled out.
- **Marina's model is the authority for both floors and how they stack** (user, Oct 13). The downloaded whole-house model (`HOME_ALONE_FINAL.glb`, IntactHouseReference, 0.774 m/unit from its doors) is a sanity check only. A uniform house or player scale for feel is allowed later as a build-time knob.
- **Never contact Marina.**
- Commit and push work. The user likes plain-language summaries.

## Pipeline (all re-runnable)

```
Marina video (gated SfM clips) ┐
Marina's angled overhead ──────┼─ trace + calibration ─ reconciler ─ spec ─ Unity grey-box ─ checks
Muto set model, captions ──────┘
```

| Step | Command | Output |
|---|---|---|
| Calibrate the overhead | `uv run --with numpy --with scipy python tools/sfm/overhead_fit.py measurements/overhead/upstairs.json` | `upstairs.H.txt` (held-out 9 cm) |
| Trace to plan | `uv run --with numpy --with matplotlib --with pillow python tools/sfm/overhead_plan.py measurements/overhead/upstairs-trace.json` | `upstairs-trace.plan.json/.png` |
| Clip registrations and derived geometry | `uv run --with numpy --with scipy python tools/house/register_clip.py <clip> [--loo [--rigid]]` | writes doors, trace `"m"` polygons, checkpoints |
| Reconcile | `uv run --with numpy python tools/house/reconcile.py [--measured]` | `spec/house_spec[.measured].json`, `spec/upstairs-changes*.md` |
| Grey-box | `Unity -batchmode -projectPath unity/HomeAlone -executeMethod SpecGreybox.Build -quit -logFile - [-variant measured]` | `Greybox_Upstairs[_measured].unity`, walk test |
| Verify | see `.claude/skills/verify-plan/SKILL.md` | `verify_plan.py`, `check_walls.py`, `test_checks.py`, matched renders |

Unity binary: `/Applications/Unity/Hub/Editor/6000.6.0f1/Unity.app/Contents/MacOS/Unity`. Python: `uv run --with ...`. VGGT and PyTorch live in `sfm-work/.venv`. COLMAP is Homebrew 4.2.1, CPU only.

Key files:

- **Spec (the only thing Unity reads):** `spec/house_spec.json`
- **Inputs:** `measurements/overhead/upstairs{.json,-trace.json,-doors.json}`, `measurements/rooms/*.json`, `measurements/checkpoints/upstairs.json`. The checkpoints file holds the clip registrations and all checkpoints.
- **Builder:** `unity/HomeAlone/Assets/Editor/SpecGreybox.cs`
- **Gated clips:** `sfm-work/rooms/{hall-s1, hall-s4, parents, kevin}`. `sfm-work/` is gitignored and regenerable with `tools/sfm/room.py`.

## Where the upstairs stands

- **Spaces:** 15 (6 rooms, hall with end bay, 3 hall pieces, closets, hall bath, main stair opening, attic stair). Gross footprint 1,972 ft² at 80 in (1,874 at 78 in) against Marina's 1,900.
- **Ceilings:** measured 2.29–2.50 m; 2.40 m nominal.
- **Checks:**
  - `verify_plan.py`: 15/15 pass, **6 independent**: Marina's 7′6″ label, the parents' bath width, the overhead's open door leaf, and three from the far-end clip.
  - `check_walls.py`: every long wall seen by hall-s1, parents and Kevin is within ±7 cm. These are consistency checks, because those registrations were fitted on those walls.
  - Leave-one-out (rigid): hall median 5 cm, max 10.5 cm; Kevin median 3.5 cm, max 6 cm.
  - The far-end clip, which never built anything, confirms Kevin's and the parents' hall doors within 7 cm.
  - Adult walk test: 11/11 in both builds.
- **Proven detection limits:** wall check 10 cm; door centres 10 cm; walk test blocks doors under 0.55 m. The image edge score **cannot** detect 20 cm and is visual-only.

## Open items

1. **The ground floor** (next). Same method; Marina Part 1 (the 1080p `copy.mp4`) is the main-floor tour. The stair's foot and foyer are only a floor patch so far.
2. **Hall feels narrow in play (user, Oct 13).** Built widths match the measurements: 1.59 m at the stair top vs 1.58 measured, 1.25 m at the far end vs 1.22 measured. Before changing anything, check against a film shot of the hall: matched camera, then overlay. Possible causes: the play FOV/eye height, no trim or furniture, or Marina's model being narrower than the set. Scale work is deferred by the user.
3. The attic leg looks about 10 cm wider in hall-s1 than in the overhead (leave-one-out); unresolved.
4. Buzz's room, the girls' rooms and the hall bath have only consistency or overhead evidence. Buzz's own clip calibrated the overhead, and the girls' rooms have no interior video.
5. Kevin's crawl test and hideable furniture (bed clearances) are not started.
6. The attic stair is located (behind the hall-end door, matching the film shot) but has no steps modelled.

## The main staircase (done): evidence, method and plan as run

**Done (Oct 13, later): the main stair is measured, decided and built.** Record: `measurements/rooms/stairs.json`.
- Measured (flight 1): 13 risers of 0.169 m, going 0.241 m (pitch 35.0 deg by vanishing points), tread band 1.12 m; landing at 2.20 m.
- Decided by the user: floor-to-floor 15 risers (2.54 m). Flight 2 is 2 risers at the north end of a full-width rear landing, rising toward the front onto a 1.2 m gallery along the north side of the well, which runs to the hall.
  - Evidence: Marina's main-floor overhead, a main-floor plan drawing the user found (not yet in the repo), the film's landing walk (Kate and Kevin), and the climb clip.
- Built: `stair` block in the spec (reconciler), boxes plus walk path in `SpecGreybox`. The stair walk test (adult and Kevin, up and down) gives 20/20 legs; removing one step blocks it.
- Not modelled: the landing window, the newels, and the landing's true ~4 m width. Marina's main floor is wider than the upstairs well; settle that when the ground floor is built.

**Evidence on hand:**

- **Overhead.** `main_stair_opening` is black (open to below) at plan x 7.83–10.66, y −4.71…0.94 (about 2.8 × 5.6 m). Its west (left) edge is hidden against the background and assumed straight at the building edge.
- **Hall walk.** A balustrade runs along the hall's west side (hall-s1 frames 135–160; rail sits on the stairwell edge, hall reaches it, rule `RAIL_T`). From the landing gallery, frames 255–300 show the damask stair wall and the rail turning (`real-colmap/images/shot_hall`). The hall-s1 middle clip (195–330) failed its gate, so don't measure from it.
- **Part 1 (main floor tour).** Stair footage at 305–360 s is already extracted in `sfm-work/stairs/images` (4 fps, 220 frames). Kept frames are 31–74 and 116–199; the others are film, dissolves, arrow overlays and the title.
- **Neither video climbs continuously between floors.** Part 1 stops at the landing, and Part 2 starts upstairs.
- **Muto says the upstairs was a separate set**, and the service (back) stair never arrived upstairs. So floor stacking is partly an authored decision; log it as one. A cross-video link from Part 1 to Part 2 FAILED: repeating damask wallpaper glued two different walls together. **Never link the two videos.** Each floor is solved on its own, and the stair is measured within itself.
- **Muto's set model** shows a damask-papered stairwell. **The poster** (`art/home_alone/references/poster/second-floor-closeup.jpg`) shows the stair with a landing turn (21), and the hall walk agrees with it.
- **The old Unity model** (`dimensional-baseline/README.md`): 16 rises of about 0.196 m, going about 0.261 m, a landing. That model is unverified; use it as a hypothesis only.

**Plan (same method as the upstairs, gates first):**

1. **Find stair-only clips** in Part 1 (305–360 s) and in Part 2's hall frames that look down the stair. Solve each with `tools/sfm/room.py`, and keep only clips that pass the COLMAP/VGGT agreement gate. Trim captions and dissolves.
2. **Measure the stair within itself.** Scale from a door, or from the riser count once the scale is checked. Measure the riser count, rise and going per flight; the width; the landing size and position; the turn direction; and the rail line. Treat a riser count from frames as a checkpoint: counted by eye, then confirmed in 3D.
3. **Floor-to-floor height** comes from rises × rise. It's independent of any cross-video link, and sets how the floors stack.
4. **Register the stair to the upstairs** using the rail edge and the stair-opening walls seen in hall-s1, rigidly. Settle the hidden west edge of `main_stair_opening`.
5. **Extend the spec.** Add a `stair` element (flights, risers, landing, rails) to the reconciler. Have `SpecGreybox` build the steps. Walk tests go up and down for both bodies.
6. **Checkpoints.** Mark independent vs consistency, prove sensitivity (for example, inject a missing riser), and run the `verify-plan` skill.

**Lessons that apply here:**

- Plot every clip from above with its camera path before interpreting gaps.
- Wallpaper repeats; don't trust any link across videos.
- Register rigidly when both sides are metric.
- Prove every new check can fail.
- Furniture and trim read as walls.
- Rails are not walls.
