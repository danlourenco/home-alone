# Current status — start here

## RESUME HERE (Oct 16, 2026, afternoon): systems pass done; day lighting matches the film's set; walk notes queued

**Read this section first. Then read `tasks/wall-grid-plan.md` ("Walk notes queued", including the deferred overhang split) and
`docs/DEVIATIONS.md` 1, 34 and 40-45.** The Oct 15 section below is history except where this one points to it.

### How to build, bake, load and look (one script: `tools/house/unity_pipeline.sh`)
- `setup`, once per machine: makes the scratch build copy at `~/.cache/home-alone/ucopy/HomeAlone`, plus a `spec` link. It exists now,
  Library imported. Never build in the user's open editor.
- `build`: copies Editor, Scripts, Models and `HDRP.asset` into scratch and builds `House_WallGrid` in batch (~30 s). Gates go to
  `spec/captures/walk-test-wallgrid.txt`:
  - Seam, Z-fight, Clash, Casing, **Trim**, **Envelope** must all be 0.
  - The walks pass except the pre-existing back-stair stall at winder 2.
- `bake`: day and night, ~60 s. It runs WINDOWED on purpose: batch mode has no render loop, so no sky, and `BakeLighting.Bake` refuses
  batch mode. It renders a camera for the sky; it does not wait on editor frames (a background editor ticks only every few seconds).
- `load`: copies the scene and bake into the project, waits until the editor is neither compiling nor importing, opens the scene and
  enters Play. Entering Play mid-import crashed Unity natively on Oct 16.
- `all`: build, bake, load. Spec or reconciler edits still go through `verify_plan.py` and the change gate first, as before.
- `shot NAME x y z yaw pitch [day|night]` (player pose; feet, eye +1.28) and `cam NAME px py pz lx ly lz vfov near [day|night]` take
  live captures in the user's running editor, with a clone of the player camera. They never move the player. They land in
  `~/.cache/home-alone/captures/`.
  - **Judge lighting only from live captures**; batch renders lie about it.
  - Walk-note poses are in `spec/feedback/feel-notes.jsonl` (pos = feet, yaw, pitch).
  - Film camera poses solved earlier are in `spec/captures/views/views-foyer-film-after.json` and `film10248.json`.
- New script in `Assets/Scripts`: create it in the repo project FIRST. Each project gives a new `.cs` its own `.meta` GUID, and a
  scene built in scratch then points to a missing script. `load` warns when they differ.
- Discriminator technique for "why does it look wrong":
  - Capture the same view with one HDRP frame setting off (SkyReflection, ReflectionProbe, SSR) and compare region means. That found
    the reflection-probe box bug in minutes.
  - For "is X in the bake", bake with X on and off and diff the scenario's `CellData.bytes`. The sky changes ~8% of it.

### The lighting model now (Oct 16), so nobody re-litigates it
- **The house is light-tight** (DEVIATIONS 43). `SpecGreybox.Envelope` generates invisible shadow-only skins, lids, floor framing and
  recess framing from the spec, clipped out of every room. The Envelope check (rays to the sky from every room joint must cross
  >= 0.3 m of structure) is 0.
- **Trim is laid along room outlines**, so joints close by construction. The Trim check ray-tests the built scene.
- **The bake** (`Editor/BakeLighting.cs`):
  - Probes outside the room volumes are invalidated: the ceiling band, note 11:16.
  - Glass doesn't block the bake.
  - Reflection probes come from the room volumes (`SpecGreybox.EnvelopeRooms`, which runs the stair well down to the ground) and
    reach 7 cm past every surface with a 5 cm fade. A short box let the sky fill in: grey-blue rooms by day.
  - Day and night each have their own reflection images, swapped by `HouseNightMode`.
- **Day look = the film's set lighting** (user choice, DEVIATIONS 44). `SpecGreybox.FilmFill` puts baked-only ceiling fills in every
  room: 300 nits, 5200 K, solved against film 2677 and 10248 by `tools/house/film_light_match.py`.
- **The foyer fixtures** are lit at night only; by day the bulbs and shades are dark too.
- **Orientation:** the front faces 227.6 deg (SW), measured (`tools/house/house_bearing.py`, OpenStreetMap). The film was shot here,
  so this is not a deviation. The sun's TIME is still a placeholder (DEVIATIONS 34).
- **Overhang stop-gap** (DEVIATIONS 45). `SpecGreybox.FilmFront` is a shadow-only flush "film front". The upstairs pieces past the
  ground footprint go on rendering layer 1. `StoreyShadows` switches the one sun's shadow casters per storey (HDRP allows a single
  shadowed directional light). The proper split is deferred (tasks/wall-grid-plan.md).
- Mac: Unity HDRP has no ray tracing on Metal (measured: `SystemInfo.supportsRayTracing` False; Unity 6000.6 reports macOS RT
  features None). Bounce light is baked.

### NEXT (in order)
1. **Read the user's walk notes on the TRIALs** (commits 4168e17, 09dd918, e30aa30, 0e3b560): the last lines of
   `spec/feedback/feel-notes.jsonl`. Answer each from its own pose, captured live.
2. **Note 11:26 "this window feels a bit low, can you confirm?"** (pos 3.993, 0.03, -8.677; yaw 251, pitch 22.6: upstairs, looking at
   the landing window). Its numbers are in `measurements/windows/ground.json` `wall_openings.landing_window`: sill y 2.69 ground
   metres, from film 11966 / 12133 and Marina 312 s. Check them with refcam from a solved film camera before changing anything.
3. **Note 11:47:** is the foyer-living opening sized like the living-den opening? (the den one looks smaller). Case both. Measure both
   from frames; the casing comes from the cut automatically (`kind: arch` + `cased: true`).
4. **Note 10:48:** the dining front windows faithful to the film and Marina. They're French windows to the floor now; check against
   the film's front (frame 4382 shows them) and Marina.
5. **The rest of the day look:**
   - Our wallpaper texture is deeper red than the film's pink-cream (2677 wallpaper 0.6x relative).
   - The foyer floor reads grey-brown, not the film's dark wood with a red rug.
   - Solve film 11966's camera and add it to `film_light_match.py`, then re-solve FillNits/FillKelvin.
   - The dining and living rooms aren't compared with film frames yet.
6. **Time of day** (DEVIATIONS 34): solve the sun from film 4382 (portico and branch shadows on the facade).
7. **Exterior shutters** (WinterNeighborhood) stand inside Kevin's room (the upper ones, x 10.43) and hang over our front windows (the
   ground ones). This is split and exterior work.
8. Carried over from Oct 16 morning:
   - The back-stair foot: Marina 321 / 1072.5 s show ONE foot step vs our 2. Solve those frames first.
   - The back-stair stall at winder 2.
   - The rest of the dining dressing (hutch, table, chairs, paintings, French doors).
   - Mirror boxes, bench, the picture under the landing.
   - Real sheers (DEVIATIONS 41).
9. Deferred by the user: **the upstairs split** (overhang exists only from the stair up; tasks/wall-grid-plan.md).

### Working rules learned Oct 16 (also in memory)
- Joints that should meet must meet by construction; prove it with a scene check (walls-touch, pstack memories).
- After two failed fixes on one symptom, write the shared premise down and test it directly (e.g. bake with X on and off). Research
  online instead of spinning.
- Never claim a look is fixed without a live capture from the user's view. Commit messages say TRIAL and claim only what was checked.

---

## RESUME HERE (Oct 15, 2026, evening): phase 5 done, back stair in progress

**Read this section, then `tasks/wall-grid-plan.md` (phases + "Walk notes queued"), then `docs/DEVIATIONS.md` 20-22 and 30-38.**

### The working scene is now `House_WallGrid` (wall-grid builder), not the old `Greybox_Upstairs`
- Build: `uv run --with numpy python -I tools/house/wall_graph.py --json` (spec -> `spec/geometry.json`), then in the batch copy
  (a copy of `unity/HomeAlone` in the session scratchpad: `rsync -a --exclude Library --exclude Temp unity/HomeAlone/ <scratch>/ucopy/HomeAlone/`, plus a `spec` symlink at `<scratch>/spec -> repo spec`;
  never build in the user's open editor): copy `SpecGreybox.cs` in, run `-executeMethod SpecGreybox.BuildWallGrid`, copy
  `Scenes/House_WallGrid.unity` + `Materials/Greybox` + `Settings/GreyboxVolume.asset` back. Gates land in `spec/captures/walk-test-wallgrid.txt`
  (door walks, stair walks incl. the Player's controller, seams 0/0/0, leaks, PEEK = no sight line into a closed space, room walks).
- Spec changes go through the trace/doors files (`measurements/overhead/ground-trace.json` "m" polygons, `ground-doors.json`) and
  `tools/house/reconcile.py` (stairs are generated there: main stair, `service_stair_spec`, attic), then `verify_plan.py` (both floors),
  then the change gate (`changes/*.json`, `tools/house/change_gate.py`). Pre-commit hook enforces it.
- Load for the user (memory: load-scene-for-walk): `~/.unity/bin/unity command list_open_scenes` (isDirty false) -> `editor_stop` ->
  `recompile` if the script changed -> `open_scene Assets/Scenes/House_WallGrid.unity` -> `editor_play` -> `editor_focus`. Retry if Unity is busy.
- The user leaves walk notes in Unity (key M): `spec/feedback/feel-notes.jsonl` + `spec/feedback/shots/`. "Look at my comment" = read the last lines there.

### Verification rule (user, Oct 15: "give yourself the tools you need to become as accurate as possible")
Every placement read from a reference frame goes through **`tools/house/refcam.py`** before it is built:
`frame` (get a Marina/film frame) -> `grid` (read pixels) -> `solve NAME FRAME points.json` (camera from known 3D points, per-point
residuals; points files in `measurements/cameras/points/`, cameras in `measurements/cameras/`) -> `measure NAME u v --plane x=..|z=..|h=..`
(read a position in plan metres) -> `overlay NAME --floor ground` (the build's walls/openings/stairs drawn on the frame) -> `view NAME`
(Unity camera for a matched render). Never place by eye or from a subagent's plan-terms description alone; name the spaces on both sides
of any door first (memory: check-placements-against-plan). Known-good: refcam reproduces the film 2677 camera (x 10.50, h 0.81, f 2263).

### What was done Oct 15 (all committed and pushed on branch unity-sfm-reconstruction)
- **Foyer back wall from the film** (foyer_cameras.py: two film cameras solved from flight 1's nosings): cased segmental arch, crown 2.17,
  springline 1.91; rear passage to the rear door; the arch's LEFT side runs to the main stair's side (no pier: Marina 195 s / 1070.5 s
  + user). Passage left wall flush with the stair's side (user). Closet door on the passage's right wall; the user's circled "door
  under the stair" is on the passage's left wall facing it (both closed props, sizes authored, DEVIATIONS 36).
- **Phase 5 (wall-grid house, scene House_WallGrid)**: stair hall as one two-storey space (stack decisions in `grid-snaps.json`,
  DEVIATIONS 37), landing as a slab, rails as 6 cm bands, floor per room, PEEK gate. **User walked it: "looks generally good."**
- **Comparison pages (fade sliders)**: arch/foyer https://claude.ai/artifact/X3oYBgypJhhUAZ53Vikxg8 ; stair hall vs Marina/film
  https://claude.ai/artifact/MWNxwxzmFcgFHhvFezCjdN ; back stair / breakfast room https://claude.ai/artifact/Y6g9C2T959jaikXUE66jv8
- **Back stair rebuilt (TRIAL, d4b1605)**: 4 foot steps toward the wall between a dark newel and a tall post, quarter landing 0.89 m,
  flight along the wall (going 0.262) to the ceiling; dark treads, white risers/stringer/balusters; papered spandrel; Kevin's basement
  door under the flight's high end (first put on an outside wall: wrong). Kitchen walls cream, floor quarry tile (colours only).

### NEXT (in order)
1. **Back stair: the user says it is "still kind of messed up".** My read from the Marina 916 s fade (camera placed by eye, so verify):
   her stair sits ~0.5 m further toward the foyer doorway (newel just right of the doorway, ~x 2.9; tall post ~x 1.8), her flight is
   shorter/steeper and meets the ceiling ~x 0.0, and her basement door (~x -1.2 to -0.3, with casing) has wall to spare before the corner
   (x -1.505). Ours: newel x 2.37, post 1.39, ceiling at -0.71, door jammed at the end (-1.43 to -0.72). Do it properly with refcam:
   solve Marina 916 s and 933 s cameras from the room's known points (foyer doorway jambs x 3.043/4.025 on the z 7.638 face, head
   2.20; the back-right corner x -1.505 / z 7.638; the side-wall window x -1.505, z 4.99-5.79, sill 0.82, head 2.15; ceiling 2.438; the
   hutch-wall corner x 4.12), then `measure` the newel, tall post, the flight's nosings and ceiling arrival, and the door's jambs; then
   film 2528/928/912 the same way; rebuild `reconcile.service_stair_spec` from those numbers (the stair may extend past the traced
   back_stair enclosure toward the doorway: check the kitchen floor between it and the hutch wall); overlay before building; update the
   kitchen-compare page; load for the user. Back-stair references: `art/home_alone/references/back-stair/` and `kitchen/frames/` (best-*.jpg);
   key ones: film 912, 928, 1044, 2528, 3607-3617; Marina Part 1 916, 924, 933, 934, 938 s; kitchen overhead 812 s.
2. Queued walk notes (tasks/wall-grid-plan.md): the arch a bit lower (Marina ~1.9-1.95 m vs film 2.17: decide with the user); the passage
   width and its doors (later); the foyer's north wall line (DEVIATIONS 35); the kitchen's left side / rear wall length (Marina's
   overhead and interiors disagree); finishes (floral paper, beams, cabinets, hutch, table, fridge).
3. Phase 6-8 of the wall-grid plan (rest of the house, windows, the chute shaft and hatch, user walk), then the exterior against the film.

---


**PIVOT (user, Oct 13 evening): correct the EXISTING model, not the grey-box.** The working scene is again `IntactHouseReference` (the downloaded GLB at 0.774 m/unit, edited by the September `SurveyBuilder` editor scripts; the source GLB stays untouched). The ground floor there feels right to the user. Upstairs, Buzz's room feels cramped (3.82 × 3.24 m against Marina's 4.35 × 3.49 m; the hall beside it is 1.89 m wide against her 1.58 m). Apply the same principles to the old model: Marina is the authority, cite frames, take a census before fixing, prove every check fails on an injected error, log departures in DEVIATIONS.md, never move outside walls, and use the room-feel skill order. The grey-box, spec and checks below stay as the measurement record and as the target numbers.

The upstairs is measured, reconciled into a spec, built as a walkable Unity grey-box, and verified against video. That includes independent evidence. **Next: the ground floor.** Every deviation from measurement is in [DEVIATIONS.md](DEVIATIONS.md) (top: the upstairs front wall overhangs the ground floor's by ~1.6 m; rooms keep Marina's shapes). Shape check: `uv run --with numpy python tools/house/shape_drift.py`. Background reading: [RECONCILIATION.md](RECONCILIATION.md) for the architecture, [tasks/sfm-plan.md](../tasks/sfm-plan.md) for the full experiment log, and the `verify-plan` skill for every check.

Branch `unity-sfm-reconstruction`, pushed to `origin`. Git LFS covers `*.glb *.blend *.exr *.fbx *.psd *.tif *.tiff *.npz`.

**NOW (Oct 15): the wall-grid rebuild, [tasks/wall-grid-plan.md](../tasks/wall-grid-plan.md).** Build the house like a house: one shared grid of wall lines across both floors, walls as objects shared by the rooms on both sides, one floor plate and ceiling per storey, openings cut into walls, all generated and verified in Python before Unity. The uncommitted corner-post/threshold stopgaps in SpecGreybox.cs are removed by it. Its verification plan (V1-V6) is the bar for every phase.

## User decisions (binding)

- **Exterior = the film's house; upstairs drawn only from inside** (user, Oct 15: "the outside needs to look the same as the movie"). Marina's upstairs set is 11.3 m deep and cannot fit the real 8.75 m house; her ground floor does. Ground floor and exterior share one space; the upstairs keeps Marina's rooms and is rendered only when the player is upstairs/on the stair (DEVIATIONS 1). Next: measure the exterior against film stills and fix the shell.

- **Faithfulness is non-negotiable.** Never propose "good enough" geometry.
- **Unity only.** Godot is retired.
- **Scale the players, not the house.** Kevin is about 1.1 m eye height and can crawl in about 0.4 m. The bandits are about 1.7 m eye height, with a hard adult-capsule rule (0.55 m diameter, 1.85 m tall).
- **Thin the interior walls to 14 cm.** Marina's are 25–45 cm. Keep each wall's centre line; rooms take the freed space. Exterior walls are unchanged.
  - Independent evidence backs this: the far-end hall passage measures 1.22 m, the overhead traced 1.07 m, and the thinned build gives 1.23 m.
- **Closets don't need to open.** The linen closet has a prop door; the other shallow closets are sealed.
- **Door height** is 80 in nominal, 78–80 in honest. The area check brackets Marina's 1,900 ft², and 84 in is ruled out.
- **Marina's model is the authority for both floors and how they stack** (user, Oct 13). The downloaded whole-house model (`HOME_ALONE_FINAL.glb`, IntactHouseReference, 0.774 m/unit from its doors) is a sanity check only. A uniform house or player scale for feel is allowed later as a build-time knob.
- **Agents never contact Marina.** The user wrote to her on Oct 14, 2026 (mockingbirdlanedesign@gmail.com) asking for room dimensions or plans and where her furniture came from. If she replies, her numbers are a new source: log them with their provenance and use them as independent checks (Buzz door-to-desk length, DEVIATIONS 23, first).
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

## Feel notes (walk-and-annotate, Unity key M; `tools/house/feel_notes.py`)

The user walks a scene and rates each spot's shape/size and lighting separately. First pass, old model (IntactHouseReference), Oct 13:
- Living room and dining room: shape right, lighting too dark. Old model 3.8 x 10.1 m and 3.8 x 7.4 m; Marina (new build) 4.5 x 8.4 m and 4.6 x 5.9 m. Same floor area (±3%), different proportions. **Next:** rate the same rooms in the new grey-box, to tell whether it's the area or the proportions that feels right.
- Buzz's room: shape off ("too small for a bed and dresser"). Old model ~3.8 x 3.2 m; Marina 4.35 x 3.49 m from Buzz's own door (new build 4.46 x 3.68). Marina's tour frame (references/buzz-bedroom/tour556.jpg) shows clear wall either side of the bed. The new build is the bigger, Marina-measured room.
  - **Census done (Oct 13, later), old model vs Marina:** `docs/DEVIATIONS.md` section "Old model: Buzz's room vs Marina" (O1-O7) and `spec/captures/buzz-old-vs-marina/all.png` (her frame beside the old scene rendered from her own camera: `SpecGreybox.RenderViews -scene IntactHouseReference -views views-buzz-old.json`). Same layout, turned 90 deg; the old room is 0.53 m too short door-to-desk (her 556-562 s camera stands beyond the old west wall) and 0.24-0.39 m too narrow, while the hall band beside it is 0.5 m too wide. Chest resized to Marina's (applied). **Wall move is a user decision:** north wall +0.30 m into the hall is interior-only and recommended; the west wall carries an exterior window.
- **Room comparison from Marina's own cameras (Oct 14):** `spec/captures/sheet-matched/<still>-triple.jpg` (Marina | September | grey-box) for 31 review stills, poses in `poses.json` (distances from named walls, eye height, lens, reprojection error, per-still findings). Tool: `tools/house/still_pose.py` (VGGT solve per room with the exact still, PnP, Manhattan wall fit, pinned at the nearest corner in each model). Replaces the generic doorway/far-corner sheet. Unreliable: the two foyer stills (poor solve); kitchen +-1 m.
- **September census (Oct 14):** `tools/house/sept_census.py` (`--selftest`) measures every room of the September model (GLB section above door heads, flood fill, closures listed in the script; map `spec/captures/sept-census.png`) against Marina's traced overhead at ±5% per side. 1 of 15 rooms passes (den). Fails: living −12/+20%, dining −13/+30%, foyer +22% wide, sunroom −9% deep, kitchen +7/−4% (turned), Buzz −11/−11%, girls B −14/−10%, Kevin −9/−17% (turned), hall bath +28/−46%, parents' bedroom −12/+19%, parents' bath −18/−8%. Missing: rear girls' room (back-stair hall in its place), back stair as a room. Extra: an upstairs room over the den that Marina's plan doesn't have. Agrees within 7 cm with the earlier Unity raycasts (living, dining, Buzz). The grey-box is within ±5% of the same trace by construction, so its real accuracy rests on its independent checks.
- Ground-floor lighting is far too dark in the old model (all three ground notes). That's for the art/lighting pass; the grey-box only carries layout.

## Open items

1. **Foyer length (Oct 15, TRIAL, user walk pending):** Marina's foyer is ~24 ft, not 29. The overhead trace took its rear edge from a two-storey wall's top; at floor level it is flush with the living room's (`tools/house/foyer_length.py`, single-frame metrology at 203 s and 312 s, rise-scaled). Stair foot now 2.43 m from the front wall (was 4.48), going 0.295 m (pitch 31 deg; conflicts with the 35 deg VP read, DEVIATIONS 6), landing 1.40 m; upstairs well and stair head follow. Closed `back_hall` behind the arched door (DEVIATIONS 22). Sheet `spec/captures/foyer-length/compare.jpg`; record `changes/2026-10-15-foyer-length.json`. Next: dress the foyer (white stair side, spindles, newel, soffit, doors, wainscot, furniture) against the same matched cameras.
1. **The ground floor: first build done (Oct 13).** Calibrated with the `overhead-floor` skill, stacked under the upstairs by `tools/house/stack_floor.py` (no stretch, user decision: rooms keep Marina's shapes, the upstairs overhangs the front by ~1.6 m), reconciled with `reconcile.py --floor ground`, built at -2.535 m. Tests: ground doors 7/7, stair 20/20. `verify_plan.py --floor ground`: 4/4 (2 independent: stair width -0.4%, den width +1.7%; both FAIL on an injected 6% scale error). Den/living doorway placed from the den clip's wall gap. Stairs use the adult-body rule, not the 0.90 m hall minimum. Side effect of the stretch: gross 2,988 ft2 vs Marina's 2,620, kitchen 590 vs 477 (the stretch also pushed the rear kitchen wing back). Open: sunroom in/out of 2,620; second dining door; foyer width 3.76 traced vs 3.49 from clip A (lateral). Was: Same method; Marina Part 1 (the 1080p `copy.mp4`) is the main-floor tour. The stair's foot and foyer are only a floor patch so far.
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
