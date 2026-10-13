## Adopted GLB baseline

- [x] Remaining exterior flicker isolated by live point-shadow A/B; user confirmed it stopped twice. Save point-light shadows OFF, retain moon shadows, guard against accidental reintroduction. Prior geometry cleanup alone was insufficient.
- [ ] Reintroduce physically appropriate local-light occlusion via a bounded/baked lighting pass, with motion validation. Current stable point lights do not cast shadows and may leak through walls.


- [x] Exterior flicker fix: clip crossing original window triangles, eliminate overlapping new frame joints/bank edges, enable temporal AA. Clipping area/UV and 75-window joint checks pass; exterior/stair walking passes. Raise porch lantern 90 cm and suppress exaggerated cage shadow.


- [x] Initial reference-inspired Winnetka neighborhood and front shutter pass. Eight exterior controller checkpoints and main-stair regression pass. Simplified scenery; reference/limitations in references/neighborhood/README.md.
- [x] Review available Pietro Chiovaro video preview frames and creator metadata against user Parade photo; findings in references/night-study/README.md. Full tutorial access blocked; exact settings unverified.
- [x] First exterior night lighting pass: warm rooms, entrance lantern, decorative front/dormer lights, cool fill and N-key day/night toggle. GI/material realism refinement still pending.
- [x] Replace 75 mapped exterior window sections with modeled frames and transparent glazing, including all three dormers and sloped roof panes; add room lighting. Rear patterns and exact dimensions remain provisional. Window/toggle/walking checks pass.
- [ ] Follow user neighborhood direction: neighbors are scenery, not destinations. Add playable boundary around house/yard/limited street; use nearby simple 3D scenery and distant matte/skybox, with day/night lighting. Do not furnish neighbor interiors.
- [ ] Buzz room: include Michael Jordan cutout and terrarium with animated tarantula. Keep tarantula a separate object for possible future throwable interaction; throwing gameplay not yet requested for implementation.


- [x] Kevin/Jeff room furnishing pass: wooden bunk beds, green bedding, dresser/mirror, desk/lamp/chair, low bookcase, reading chair, trunk, pinboard, checked front curtains and small-motif wallpaper. Twelve real-controller room/hall checkpoints pass. Original walls/windows retained; reference limitations in references/kevin-bedroom/README.md.

- [x] Ensuite reference-based furnishing pass: blush/ivory/green palette, vanity and inset sink, brass framed mirror/taps, shelves/towels, provisional rounded bath and open shower, window dressing. Nine ensuite and ten bedroom controller checkpoints pass. Fixture sizes and reference limitations recorded in references/ensuite/README.md.

- [ ] Investigate ensuite dimensions later (user request): current outer interior envelope approximately X8.34–12.14 / Z7.29–10.77 (3.80 × 3.48 m), with northeast inset and existing vanity reducing usable space. No verified Marina bathroom dimensions or percentage mismatch established. Compare source overhead and stated measurements before resizing structure or accepting compact bath/shower as accurate. Current fixture fit is provisional, not evidence that the GLB is undersized.

- [x] Parents bedroom: four-poster bed placement, red bedding, green bedside lamps, white mantel/hearth seated in existing recess. Ten walking checkpoints pass.
- [x] Next furnishing slice started and initial pass saved: gathered ivory window panels, dressing-table mirror and green upholstered chair. Inspected parents-dressing.png. These are simplified furnishings; mirror uses environment reflection, not a planar room reflection.
- [ ] Refine bedroom fabrics, artwork and furniture profiles against film close-ups after this placement pass.

- [ ] Reconcile separate foyer fixtures from references/foyer-film: glass/brass stairwell pendant, confirmed shallow light in rear arched recess, user-reported entrance fixture (not clearly shown), and distinct breakfast bowl-shade chandelier. Refine wallpaper from film close-ups; current generated damask is approximate.

- [ ] Deferred, low priority (user report 2026-09-12): basement appears to be missing some walls and may have height issues. Inspect later; neither cause nor dimensions verified. Keep current base unchanged for now.
- [x] Audit intact GLB and confirm Unity source is byte-identical.
- [x] Identify main-stair dimensional mismatch with custom blockout.
- [x] Open intact Unity reference; verify spawn and main-stair/cross-hall route.
- [x] First foyer finish/night pass: reference-based damask, ivory paneling, burgundy runner, dark wood; simple tables/chairs and warm lighting.
- [ ] Refine furniture replicas and extend finishes/lighting beyond foyer after visual review.
- [ ] Keep structural changes limited to demonstrated mismatches; custom room-fit work is superseded.

## Central hall increment

- [x] Build broad cross-hall plus front-centre bathroom and linen closet only.
- [x] Test stair route, both sides of hall, and both new room entrances; inspect arrival view.
- [ ] Review central proportions before adding bedrooms or extending hall beyond foyer boundaries.

## Foyer proportion reset

- [x] Set rejected upstairs fit aside and open a plain foyer/stair/hall blockout.
- [x] Trial wider flight and side hall; test traversal.
- [ ] Establish source-consistent stair width, rise/run, landing depth and hallway shape before rebuilding bedrooms.

## Upstairs registration update

- [x] Build clockwise upper layout anchored to main stair, with explicit fit compromises.
- [x] Check all upstairs rooms and downstairs circulation using the real controller.
- [x] Export upstairs/downstairs overlay and inspect Unity views.
- [ ] Review room proportions and hallway composition against sources before final dimensions/finishes.

# House reconciliation tasks — 2026-09-11

Current proposed sequence extends the kitchen/Marina work; historical tasks remain below. See [plan.md](plan.md) for findings, source roles and assumptions. [Comparison packet](../art/home_alone/references/reconciliation/README.md) completed; separate main-stair and connected-stair candidates are built and traversal-tested; exterior registration and camera fit remain open.

## Current priority

Interior first, per latest user direction. Fit upstairs rooms around both connected stairs; validate openings, floor support and levels. Defer exterior fit and door frames/finishes. Earlier exterior prerequisites below are superseded.

## Progress: initial review packet

- [x] Six visual plates, timestamped evidence and a proposed main-stair footprint saved.
- [x] Candidate arithmetic and plot transforms checked; plates visually inspected.
- [ ] Complete moving-view/camera-fit work and multi-anchor registration before locking stair geometry.

## R1: Evidence packet for both stairs

**Description:** Review video motion, source plans and existing candidates; separate observations from adaptations.

**Acceptance:**
- [ ] Each stair has timestamped views, direction/turn evidence and unresolved facts recorded.
- [x] Area calibration, visitor-plan provenance and superseded survey claims are explicitly classified in the packet, including the restored 477 ft² kitchen statement.
- [x] User confirmed a believable, fully connected house preserving Marina's recognizable rooms and the exterior's appearance (2026-09-11; recorded in plan.md).

**Verification:** Compare ledger entries directly with frames and narration, not just handoff notes.
**Dependencies:** None. **Likely files:** survey README, selected evidence frames/index. **Scope:** small documentation/evidence set.

## R2: Common-frame comparison

**Description:** Register the ground/upper plans, Godot interior and original exterior with documented transforms.

**Acceptance:**
- [ ] Overlay shows shared anchors, remaining offsets and source uncertainty without hidden per-floor distortion.
- [x] Original exterior wire projections include current/candidate floor levels and roof/window geometry; final attic-specific sections remain required.
- [x] Rectifications, transforms, vanishing points and source frames preserved; remaining scratch-path dependency documented.

**Verification:** Check multiple independent landmarks and dimensional/area definitions.
**Dependencies:** R1. **Likely files:** survey tools, comparison images, survey README. **Scope:** medium.

## Checkpoint: Evidence and registration

- [ ] Review the overlay packet and unresolved source conflicts before locking dimensions.

## R3: Main stair / upper gallery slice

**Description:** Build the complete stair connection using the older Godot geometry as a candidate.

**Acceptance:**
- [ ] Plan and section show flights, landing, rear window, gallery and consistent slab openings.
- [ ] Eye-level comparisons preserve the reference composition; adopted departures are labelled.
- [x] Actual Unity player traverses both directions with floor support and clearance in the isolated candidate (13 continuous checkpoints; no jumps).

**Verification:** Rebuild, focused sweep and player traversal; saved section and matching views.
**Dependencies:** R2. **Likely files:** survey JSON, SurveyHouse.cs, SurveyBuilder.cs, RoomDetail.cs, comparison artifact. **Scope:** medium.

## R4: Breakfast stair / upper arrival slice

Candidate built with a 12 + 8 rise connection. See plate 07: the upper return exceeds part of the original upper-wing outline. Exterior fit is deferred while the interior is developed. Frames/finishes are deferred at the user’s direction.

**Description:** Resolve the visible breakfast grouping and a physically connected continuation.

**Acceptance:**
- [ ] Hutch, doorway and stair agree with the checked video viewpoints.
- [ ] Section includes landings, corridor clearance and upper arrival; uncertain continuation is labelled.
- [x] Player traverses both directions and passes the nearby doors/table in the separate candidate (42 checkpoints); final dimensions remain unadopted.

**Verification:** Rebuild, focused movement checks, plan/section and M18/M23 camera comparisons.
**Dependencies:** R3. **Likely files:** survey JSON, SurveyBuilder.cs, RoomDetail.cs, comparison artifacts. **Scope:** medium.

## Checkpoint: Connected stairs

- [x] Both vertical connections pass candidate traversal.
- [ ] Fit upstairs room groups to the arrivals; exterior-level fit is deferred.

## R5: Upper-floor fit

**Description:** Fit upper rooms around the candidate circulation, preserving recognizable room relationships and a coherent interior. Size the exterior afterward.

**Acceptance:**
- [ ] No global mirror/stretch or silent room trimming substitutes for adopted coordinates.
- [ ] Room entries, external windows and floor support fit; departures from Marina are listed.
- [ ] Rooms are reachable with the player controller.

**Verification:** Shared-scale overlay, window elevations and Unity traversal.
**Dependencies:** R4. **Likely files:** survey JSON, SurveyHouse.cs, SurveyBuilder.cs, comparison artifacts. **Scope:** medium.

## R6: Attic and basement connections

**Description:** Resolve attic roof/headroom and the evidence-supported basement access location.

**Acceptance:**
- [ ] Attic floor, stair, chimney and usable space fit the roof in section.
- [ ] Basement unknowns remain labelled; no unsupported detailed layout is presented as surveyed.
- [ ] Both connections pass actual movement checks.

**Verification:** Sections and bidirectional traversal, including turns and top/bottom exits.
**Dependencies:** R5. **Likely files:** survey JSON, SurveyBuilder.cs, comparison artifacts. **Scope:** medium.

## R7: Exterior reconciliation

**Description:** Retain original exterior detail and repair only incompatible components.

**Acceptance:**
- [ ] Facade/roof before-and-after comparisons show retained character and explicit changes.
- [ ] Shell encloses rooms without missing patches, interior intrusions or mismatched openings.
- [ ] Structural positions and cuts consume adopted survey values rather than competing overrides.

**Verification:** Enclosed Unity walkthrough, exterior views and final floor/section overlays.
**Dependencies:** R6. **Likely files:** ExteriorShell.cs, survey JSON, targeted exterior mesh, comparison artifacts. **Scope:** medium.

## Checkpoint: Structure complete

- [ ] Review shell, all-floor traversal and discrepancy ledger before resuming room detailing.
- [ ] Capture current Unity validation results; historical Godot passes are not counted as new Unity checks.

---

# Earlier kitchen realism tasks (preserved)

- [x] Inspect current generator, saved preview, scene lighting and exported materials.
- [x] Compile sourced film stills, production photos, visitor plan and tour chapter metadata.
- [x] Save an evidence-based plan before changing the model.
- [x] Establish current regression baseline: 172 colliders, 0 failures.
- [x] Analyze both tour caption tracks, inspect selected visuals and save a [32-frame reference index](../art/home_alone/references/tour/README.md); correct the blue-tile and L-shaped-island brief.
- [x] Replace the main-floor thumbnails with [29 native MP4 frames](../art/home_alone/references/tour/main-frames.md), inspect reverse views and verify the 477 ft² onscreen annotation. The 16 upstairs thumbnails remain available.

## Task 1: Layout and human scale

Correct the working kitchen/breakfast arrangement from the reference packet, using estimated human-scale dimensions and the current house connections.

**Acceptance:**
- [ ] Save a top-down layout and two eye-level massing views aligned with the reference directions.
- [ ] Counters, sink support, island cooktop, refrigerator, windows and back door agree spatially; counter top is 0.90–0.93 m above finished floor.
- [ ] Long L-shaped island and two window seats agree with the overhead and reverse tour views; reported kitchen area is checked without treating it as a survey.
- [ ] Door and island routes remain usable by the player capsule; no scaled-up furniture used to fill excess space.

**Verification:** generator dimensional assertions; visual comparison to both film directions; focused kitchen movement through existing harness.

**Dependencies:** reference study. **Files:** `tools/build_house.py`, `tools/check_house.gd`, layout/preview artifacts. **Scope:** medium.

## Task 2: Joinery and exported materials

Replace kitchen placeholder boxes and shader-only noise with believable cabinetry and shared exportable surface maps.

**Acceptance:**
- [ ] Cabinet panels, toe-kicks, sink cavity, appliance seams and tile edges have correct visible geometry.
- [ ] Dark wood, blue ceramic, terracotta and floral walls use correctly scaled textures; brass has metallic response.
- [ ] The GLB contains expected image maps; close-up Godot appearance agrees with Blender.

**Verification:** Blender generation, Godot import, GLB material inspection and a cabinet/worktop/floor close-up in both renderers.

**Dependencies:** Task 1. **Files:** generator, kitchen texture sets, generated model outputs. **Scope:** medium (material sets are grouped assets).

## Checkpoint: Room and materials

- [ ] Review layout against references before dressing.
- [ ] Confirm kitchen geometry and textures are convincing in Godot with the ceiling intact.
- [ ] Existing regression results are preserved and any failure is explained.

## Task 3: Film-specific dressing

Add recognizable silhouettes and the breakfast-room context seen in the chosen views.

**Acceptance:**
- [ ] Pot rack/cookware, stools, kettle, canisters, knife block, appliance and gathered curtains appear in their reference-relative positions.
- [ ] Breakfast table, chairs and hutch establish the reverse sightline.
- [ ] Every prop rests on or attaches to a supporting surface, and clutter leaves movement routes open.

**Verification:** three eye-level comparisons plus collision route check.

**Dependencies:** Task 2. **Files:** generator, model outputs, comparison renders. **Scope:** small.

## Task 4: Runtime lighting and final validation

Finish the enclosed room under believable light and document the result.

**Acceptance:**
- [ ] Local reflections and contact shadows distinguish glossy ceramic, satin wood, matte fabric and brass.
- [ ] Save three Godot views and one close-up, with corresponding Blender comparisons; no hidden ceiling shortcut.
- [ ] Rebuild/import checks and focused kitchen checks pass; broader pre-existing failures are resolved or explicitly reported; attribution is accurate.

**Verification:** commands in `plan.md`, manual player walkthrough and GLB material inspection; `git diff --check`.

**Dependencies:** Task 3. **Files:** preview scene, check script, reference/readme documentation, final comparison artifacts. **Scope:** medium.

## Checkpoint: Complete

- [ ] All kitchen acceptance criteria verified in the playable Godot scene.
- [ ] Final comparisons and source attribution available for review.
- [ ] No unrelated project edits overwritten.
