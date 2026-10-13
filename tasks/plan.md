> CURRENT Buzz candidate B: 3.90×4.80×2.40m, estimated. Main house untouched. Shelves stop 65cm from door wall; dresser/bed clearance67cm. Fourteen waypoint route passes Edit/Play; Unity left in Play mode. Same-scale plan: art/home_alone/references/buzz-poc/footprint-comparison.svg. Poster is topology corroboration, NOT measured scale.

> September 18 CURRENT: BuzzWalkableCandidate.unity built, open and running. Plain furniture/window volumes; estimated 3.65×4.27×2.40m room. Eight-point controller route passed Edit and Play mode; main house unchanged. See art/home_alone/references/buzz-poc/WALKTHROUGH.md. Camera-depth fit is still rejected; do not resume endless calibration as prerequisite to reviewing candidate.

> September 15 CURRENT: Buzz cross-depth gate FAILED. Headpost 5–8px success did not generalize to footpost: 59px with prior calibration, 92px with joint near-point fit. No dimension changes applied. See buzz-poc/README.md and review.html. Next: longer-segment multi-depth feature/camera solve; do not promote 39° lens or 1.15 bed length as measurements.

> Latest Buzz PoC: joint camera/headpost fit applied ONLY to isolated scene. 559s new frame headpost errors 4.64/8.31px; head depth hits zero bound and room depth remains unresolved. Reproduce fit.py → rigid_fit.py → apply_joint.py → Unity Build. No house-wide propagation yet.

> Buzz PoC continuation: added third desk-wall window; verified three markers in isolated scene. Annotated comparison: `art/home_alone/references/buzz-poc/review.html`. Overhead apparent bed/depth fraction 0.414 vs PoC 0.467; unresolved parallax, no structural expansion applied. 54s/60s images are production photos, not CG views.

> September 14 — Buzz-only PoC built in separate `BuzzProportionPOC.unity`. See `art/home_alone/references/buzz-poc/README.md` for sources, measured ratios, checks and remaining gates. Wall-plane proof works; full room depth/furniture fit remains unvalidated. Main walkthrough untouched. Do not propagate dimensions yet.

# Current priority — Marina-first reconstruction reset

Follow [the reconstruction plan](marina-reconstruction.md). User wants a first-principles reset: recover Marina's connected proportions before further patching the imported shell. Preserve current prototype/assets. Hallway silhouette stays film-consistent; no alcove. Front adjustment is authorized in principle but95cm remains unverified and unapplied. Immediate task: Buzz/hall multi-view relative-geometry pilot. Earlier work below is implementation history, not proportional sign-off.

# Previous execution queue — September 14, 2026

User requests continuous autonomous progress without per-step confirmation; ask only for information needed to unblock a decision. User authorizes inferring Buzz proportions from Marina Part2 around0:50 rather than waiting for stated dimensions. Keep measured model values separate from inferred historical values.

- [x] Baseline inventory and source weights.
- [x] Test foyer width/opening candidates; retain current geometry because multi-view verification did not establish a replacement dimension. This is a decision to retain the base, not dimensional sign-off.
- [x] Buzz: consistent three-window dressing; inferred bed/bedside placement from0:50, dresser gap0.58→0.83m without bed resize; walking/wing/animation tests pass.
- [x] Ensuite: replace oval bowl with curved-front wall-backed bath/shared shower screen. Existing compact envelope retained and labelled provisional; surface/walking tests pass.
- [x] Kitchen/breakfast: add missing table and seating footprints; correct stair clearance; test furnished circuit through both dining openings and foyer.
- [ ] Review remaining major-room furniture footprints and existing basement/attic access for traversal defects; basement historical height/wall accuracy remains deferred.
  - September14: basement slab opening saved. Full kitchen→basement→exterior→kitchen route passes20 checkpoints; upper hall→attic landing→hall passes8. No jumps or intermediate teleports.
  - Kevin/Jeff review: Marina5:55–6:25 shows reading chair beside dresser and desk at opposite window. Corrected the reversed placements without resizing; expanded16-point route passes.
- [ ] Finish reference-based furniture silhouettes and doorway/trim transitions once each local layout holds. Kitchen seating is explicitly blockout; chandelier/table registration is now saved and checked.
- [ ] Resume foyer day/night visual benchmark, then carry material/light treatment into approved room layouts. Keep point shadows disabled.
- [ ] Whole-house motion/performance/build review.

Current implementation/evidence: [Buzz](../art/home_alone/references/buzz-bedroom/README.md), [ensuite](../art/home_alone/references/ensuite/README.md), [kitchen](../art/home_alone/references/kitchen/README.md). The September13 section below is retained as history; its repeated candidate requests have been executed.

# Previous priority — September 13, 2026

Stage 1 baseline completed: [dimensions and discrepancy ledger](../art/home_alone/references/dimensional-baseline/README.md). Living/dining are ~7–8% wider than plan labels; west/east wings ~30/35% wider. The foyer's width relative to adjacent rooms conflicts with the plan. No global resize; next is the D01/D04 foyer/stair candidate comparison. Exact film scale remains unverified.

Structure review now takes precedence over lighting and decoration. Use the native HOME_ALONE_FINAL base in `IntactHouseReference`, not the historical generated stair studies below. See the [current structure audit](../art/home_alone/references/structure-audit/README.md) for measured heights, tested routes, uncertainty and the next ordered comparisons. The breakfast stair's lack of an upstairs connection is explicitly accepted; basement height/walls are deferred. Important movie-room relationships remain the fidelity priority. Do not resize furniture or rooms merely to hide conflicts.

Next: matched foyer/upper-hall camera comparison, downstairs opening/circuit verification, then Buzz furniture-scale and ensuite fixture-outline reconciliation. Daylight tuning is paused. The older “both stairs connected” and generated floor-height checkpoints below are historical and do not describe the adopted scene.

# House reconciliation plan — 2026-09-11 (historical)

This extends the existing kitchen/Marina fidelity work to the Unity house. Earlier kitchen planning is preserved below as historical context; its engine-specific tasks and unqualified 477 ft² calibration are not the current build instructions. The user authorized the comparison work on 2026-09-11. The evidence packet and separate Unity stair studies are available; candidate dimensions are not yet adopted. Ordered work is in [todo.md](todo.md).

## Latest user direction — interior first

Get the interior right before fitting the exterior. The user explicitly deferred exterior constraints and allows sizing the exterior to the completed interior later. Current priorities are Marina's recognizable room relationships, complete stairs/landings, consistent levels, floor support and usable circulation. Door frames and finishes wait until layout is locked. Retain the original exterior for later; its present footprint does not block interior layout work. This supersedes earlier exterior-first checkpoints below. Next: fit upstairs room groups to both stair arrivals without silently mirroring or stretching an entire floor.

## Target and confirmed compromise policy

User confirmed on 2026-09-11: "A believable, fully connected house that preserves Marina’s recognizable rooms and the exterior’s appearance."

Build one continuous, believable Home Alone house in Unity, preserving Marina's recognizable interior compositions and the downloaded exterior's visual character. When those conflict physically, expose the smallest local adaptation. First investigate adjustments to uncertain circulation, closets and hidden stair continuations; verify that these preserve the important interior views and exterior proportions. This policy is confirmed; specific geometry remains to be resolved through the evidence and comparison work below.

## Comparison packet completed — 2026-09-11

[Six review plates, evidence ledger and main-stair fit candidate](../art/home_alone/references/reconciliation/README.md) are available. Native video frames and archived captions correct two inherited claims: the 477 ft² figure does describe the working kitchen, and the basement door is in breakfast. The main-stair candidate fits the foyer envelope arithmetically at +3.35 m; Unity traversal now passes in separate studies; camera fit and exterior registration remain outstanding. Earlier statements below describing a withdrawn kitchen check remain audit history, not a dismissal of Marina’s stated area.

## Current layout checkpoint

Both stairs now form a traversal-tested candidate loop at +3.35 m. The new upper return exceeds part of the original exterior upper-wing footprint; that reconciliation is deferred under the latest user direction. See the connected-study section and plate 07 in the packet. User direction: defer frames and finishes until layout is locked. Fix structural omissions (such as the main stair enclosure) and geometric conflicts first.

## What the audit establishes

- `Assets/Scripts/SurveyHouse.cs` mirrors the upstairs and scales its two horizontal axes differently: approximately 1.109 in X and 0.880 in depth. `SurveyBuilder.cs` then replaces the hall and trims overlapping rooms. This is a fit operation, not evidence that the floors stack correctly.
- Unity's main stair is one ramp from ground to +3.0 m. The older `tools/build_marina_interior.py` has a rear landing and four turning steps. Recover and compare that geometry, but do not assume its dimensions are measured.
- Unity's breakfast stair rises 2.2 m over 2.6 m of run to an approximately 2.84 m long landing; its onward flight is explicitly unmodelled. The current Godot service stair also has no upstairs exit. Neither is a complete structural solution.
- The survey README's original 475/477 ft² agreement is explicitly withdrawn later in the same document. `tools/survey/survey_out.py` fits the sum of selected room rectangles to 2,620 ft² by construction. Agreement with that total is not an independent validation. Area alone also cannot determine a rectangle's aspect ratio.
- The rectification tool exposes a depth/aspect parameter (`ky`). The existing ±0.15 m claim needs an independent error assessment, including aspect calibration, the boundary of the reported area, and wall-top versus floor-level parallax. A low vanishing-point residual alone does not establish dimensional accuracy.
- Several corrections live in builder constants rather than the survey JSON. The current pipeline therefore has multiple competing descriptions of the house. The survey output script also depends on an absolute scratch directory; preserve its inputs before relying on regeneration.
- `ExteriorShell.cs` uniformly scales the imported asset by 0.83, aligns one corner, and deletes triangles against room envelopes. This is an approximate shell-fitting method, not a measured registration. It can remove desired geometry; inspect the original exterior when assessing fidelity.
- The archived Godot breakfast capture is a useful comparison for the hutch/door/stair grouping. Its documentation also admits a 1.5 m extension of the breakfast rear wall and use of the disputed kitchen area. Reuse successful compositions and assets, not every coordinate.

Evidence inspected: Unity and Godot generators, survey scripts/JSON/notes, saved Unity foyer and Godot breakfast captures, original exterior preview, Marina frames M18/M23, upper overhead, floor-area annotation, and both visitor plans. No current Unity runtime test or new dimensional survey was performed in this planning pass.

## Source roles

| Source | Use | Limit |
| --- | --- | --- |
| Marina's video frames and stated dimensions | Primary interior appearance, visible spatial relationships, explicitly stated quantities | Separate directly stated measurements from our image-derived estimates; an unseen connection remains unresolved |
| Film and production photographs | Check recognizable stair profiles, openings, window/landing relationships | Distinguish film, production-stage set, and real property; camera perspective and special shot geometry matter |
| Visitor's first/second-floor drawings | Candidate stair topology, cross-floor anchors, rough dimensions | [Publisher identifies them as plans Eric worked out after visiting](https://hookedonhouses.net/2009/11/30/inside-the-real-home-alone-house/), not an architectural survey; period differences also need checking |
| Original downloaded Blender/GLB exterior | Preserve facade, roof/dormer character, windows, trim and material work | Appearance is not proof of scale; compare original geometry before any clipping |
| Godot Marina interior | Recover better room compositions and the turning main stair; reuse suitable meshes/materials | Ground-floor reconstruction with admitted estimates and no connected service stair |
| Current Unity project | Delivery engine, build tools, movement, existing detail work | Generated geometry and navigation success are not historical evidence |

Marina's [companion page](https://www.mockingbirdlane.design/post/home-alone-in-depth) provides production photographs attributed to John Muto and Dan Webster. Use these alongside the locally archived videos for unresolved stairs rather than treating successive written interpretations as new evidence.

## Method and order

1. **Resolve the evidence before geometry.** Record the main stair and breakfast stair in a small ledger: exact source/time, visible fact, inferred dimension, confidence, conflicting view, proposed adaptation. Review short continuous video sections around the existing frames; the main staircase visible through the breakfast doorway must not be mistaken for the breakfast staircase. Recheck the meaning of the floor-area figures and basement-door narration. Mark superseded statements clearly.
2. **Register the existing candidates in one coordinate system.** Keep the current metre-based Unity convention. Document each source transform; use multiple anchors such as front-door centre, main-block corners, rear foyer wall, stair wells and chimney positions. Compare outlines with a common scale and orientation, without silently stretching each floor to fit. Report residual differences. Include the exterior roof/eaves and floor elevations now, before locking interior dimensions.
3. **Solve the main stair as a complete vertical slice.** Fit the foyer, rear landing/window, final turning flight and upper gallery together. Produce a plan and a section with floor structure, tread/riser counts, landing elevation, openings and walking headroom. Compare the older Godot solution against tour views. Do not lock a particular turn merely from the handoff wording.
4. **Solve the breakfast connection as a second slice.** Preserve the hutch, door, table and visible stair composition from M18/M23; establish foot, winders/turns and actual corridor relationship using the moving camera and overhead together. Fit its hidden continuation and upstairs arrival alongside the master-area candidate. Label any invented continuation. Reserve basement access only after checking its source; do not let the existing basement dictate the stair.
5. **Fit upstairs rooms and attic around those connections.** Retain recognizable room proportions, door relationships and sightlines where supported. Prefer localized changes to uncertain hall/closet areas over global mirroring or unequal scaling. Keep an explicit discrepancy list if this cannot preserve important views. Fit attic stair, chimney and usable headroom to the roof rather than treating the attic as a rectangular box with an independent ceiling.
6. **Reconcile the exterior at component level.** First attempt rigid placement and a justified uniform scale. Preserve important facade and window proportions. If needed, adjust selected rear-wall/roof segments or rebuild only the incompatible shell portions while retaining materials and trim. Any change to the recognizable front silhouette should have a before/after comparison. Avoid using broad triangle clipping as the final seam solution.
7. **Consolidate and validate in Unity.** Extend the existing survey data with adopted levels, stairs, wells and source/adaptation notes; keep raw observations separate from adopted coordinates. Make structural geometry and cuts consume those same values instead of overriding them in several builders. Reuse suitable Godot/Blender detail assets after checking scale, axes, pivots and materials. Resume room detail only after the combined structure passes review.

## Review artifacts and acceptance

The first review packet should contain common-scale floor overlays, a section through each staircase, exterior elevations with interior levels superimposed, and source/candidate comparisons from the foyer and breakfast room. This is the next deliverable, not another furnished rebuild.

Structural success means stair runs actually meet landings, floor and ceiling wells agree, headroom is shown through each turn, windows relate plausibly to rooms, and attic geometry stays within the roof. Verify both directions in Unity with the actual player controller: capsule sweeps alone do not establish floor support, gravity traversal or visual correctness. Keep camera height and field of view consistent in asset-to-asset comparisons; fit source cameras separately when needed.

Checkpoints: review evidence/registration before committing to dimensions; review both staircase slices before completing upper rooms; review the enclosed shell and actual traversal before resuming materials/props. Unknowns and authored compromises remain labelled. No arbitrary centimetre tolerance is claimed until source uncertainty is assessed.

---

# Earlier kitchen realism implementation plan (preserved)

Status: research and planning complete; implementation has not started. Requested sequence: compile evidence and plan before updating the kitchen.

Reference priority (user direction): Marina Coates's tours govern layout, proportions and visual details. Correct the downloaded Blender asset against her model. Other references supplement unresolved details; defer to Marina when they disagree unless there is a concrete ambiguity or physical inconsistency to resolve. See the [reference priority](../art/home_alone/references/tour/README.md#reference-priority--user-direction).

2026-09-10 tour evidence update: [the complete caption/keyframe study](../art/home_alone/references/tour/README.md) supersedes the earlier green-tile assumption. Use blue ceramic, an L-shaped island and two window seats. The user-provided Part 1 MP4 now supplies [29 native-resolution frames](../art/home_alone/references/tour/main-frames.md), including onscreen confirmation of Marina's 477 ft² kitchen area at 13:23; use it as the scale target while fitting the outline. The breakfast stair has no established upstairs connection in the film set.

Baseline verification on 2026-09-10: the existing headless `tools/check_house.gd` run passed with **172 colliders and 0 failures**. This establishes existing navigation behavior, not visual correctness; several current kitchen appliances have no collision. Plan links and reference JSON were checked, and `git diff --check` passed.

## Outcome

Rebuild the kitchen so it reads as the 1990 Home Alone room at walking height: coherent working layout, convincing scale, dark wood joinery, glossy blue tiled counters, terracotta floor, floral walls, red curtains and a recognizable cooking island. Success is judged in Godot as well as Blender.

Evidence and annotated images: [kitchen reference packet](../art/home_alone/references/kitchen/README.md). Ordered acceptance checklist: [todo.md](todo.md).

## Approach

### 1. Lock the room arrangement before adding detail

Use Marina's tour views toward the back door and toward breakfast as the primary camera pair, reconciled with her overhead plan. Supplement unresolved details with film views and the production breakfast panorama. Prepare a top-down layout and simple massing at an eye height near 1.6 m before detailed modeling.

The intended arrangement, described while looking from breakfast into the working kitchen:

- Sink and supporting base cabinetry under the far-end window, checked against the tour overhead and the back-door view; supersedes the earlier left-perimeter placement assumption.
- Pale glazed back door between perimeter runs, with the adjoining rear window/counter grouping.
- Long L-shaped island aligned into the room, with dark inset cooking surface, stool side, end seating and a suspended pot rack.
- Two recessed window seats interrupt the side counter/cabinet elevation.
- Dark refrigerator at the breakfast/kitchen transition; breakfast table and pale glazed hutch visible in the reverse view.
- Red window dressings, cream floral walls and wood ceiling beams unify both spaces.

Start with 0.90–0.93 m worktops, 0.60–0.65 m perimeter depth, and about 1.1–1.2 m clear circulation where practical. These are design estimates to reconcile against the images, not claims about the set. Solve the long L-shaped island and its return from the newly available overhead and reverse views; the earlier rectangular island dimensions are superseded. Determine the cooking zone from furniture and aisle scale; the existing 9.8 × 8 m shell must not dictate oversized appliances. Repartition or locally resize the kitchen wing as needed while preserving connections to the existing house.

**Checkpoint:** overhead layout plus two eye-level massing views make the same spatial story as the references; sink, island and doors fit without intersections. Freeze layout before spending time on props.

### 2. Replace the accumulated kitchen placeholders

Consolidate the kitchen sections in `tools/build_house.py` into one coherent construction sequence using the existing mesh helpers. Replace conflicting boxes rather than layering another detail pass over them.

Build real cabinet face frames, inset/raised panels, drawer gaps, recessed toe-kicks, appropriate counter overhangs, edge tiles, sink cavity and a curved faucet. Use geometry for close-up silhouettes and shallow maps for fine surface detail. Choose bevel sizes by object scale instead of a universal 45 mm bevel. Put simple collision on fixed furniture; decorative handles and small props need none.

Model the island cooktop instead of the oversized rear-wall range. Retain an unobstructed exit. Add the correct kitchen ceiling and wall finish so exterior wall materials and hidden roof collections do not dictate the interior appearance.

### 3. Make the materials survive export

Use a small set of shared UV-mapped PBR textures: cabinet wood, blue tile/grout, terracotta and kitchen wallpaper. Compare the blue tile under the intended lighting with the green appearance of some film stills. Use original or clearly licensed assets, recording the source and scale. Existing photographed oak belongs to the foyer; it does not solve the kitchen floor or cabinet material.

Bake procedural surface detail to images when necessary. Wire normal maps as tangent-space normals, roughness as non-color data, and actual metals with metallic response. Verify texture bindings in the generated GLB before polishing the Blender render. Avoid modifying shared foyer materials as a side effect of kitchen work.

**Checkpoint:** close-up of cabinet + worktop + floor looks materially consistent in both Blender and Godot, including grazing-angle highlights and texture scale. No Blender-only noise detail accepted as finished game art.

### 4. Add the few details that identify the room

Prioritize hanging red/dark cookware, stools, kettle, knife block, pale countertop appliance, canisters, sink accessories and gathered curtains. Add the breakfast table/chairs, hutch and selected refrigerator papers because they appear in the main sightlines. Place objects on actual surfaces with plausible contact shadows. Keep clutter grouped around use areas and walking routes clear.

The service-stair connection can be represented at the visible breakfast boundary where the existing architecture permits; constructing a new working stair system is separate work. Do not reproduce hidden drawer contents, every label or unseen rooms in this pass.

### 5. Light and validate the playable room

Keep the ceiling present in all interior comparisons. Balance soft window daylight with warm practical fixtures, add a bounded interior reflection probe, and use shadow-casting lights where they establish contact. Tune exposure before adding more lights. Consider baked indirect light only if the first Godot comparison still lacks believable bounce; do not introduce a second lighting pipeline speculatively.

Capture three final Godot views: entry/breakfast toward island, sink/back door, and island toward breakfast. Include one cabinet/tile close-up and corresponding Blender views. Match image framing to the references sufficiently to compare relative size and placement. Check the room with the actual player capsule, not only a free camera.

## Files and dependency order

`reference packet → layout/massing → joinery and materials → dressing → runtime lighting and verification`

- Main authored changes: `tools/build_house.py`, kitchen texture files, `scenes/House_Blockout_Preview.tscn`.
- Focused verification: extend `tools/check_house.gd` only for kitchen navigation/solid furniture; keep existing house regression coverage.
- Generated outputs: existing `.blend`, `.glb`, exported texture files, and updated preview images. Save manual Blender work elsewhere before rebuilding, as the generator overwrites its outputs.
- Update `art/home_alone/README.md` with actual fidelity, sources and current limitations. Its current blanket statement that no third-party texture is embedded conflicts with its own Poly Haven attribution and needs correction when implementation documentation is updated.
- No multiplayer/gameplay redesign. Change walkthrough waypoints only if the corrected room layout requires it.

## Verification and completion criteria

1. Preserve baseline render and record current test failures before changes; do not disguise pre-existing failures by removing checks.
2. Run Blender generation with its existing structural assertions, then Godot import and `tools/check_house.gd`.
3. Add the smallest kitchen checks that catch impossible counter height, unsupported sink, exit obstruction and collision-free fixed furniture. Use a few dimensional assertions in the generator plus the existing movement harness.
4. Inspect GLB material texture references and metal values; visually compare exported normals, roughness and UV scale in Godot.
5. View the room at normal player height with ceiling intact. Reject floating props, overlapping joinery, blocked apertures, uniform plastic surfaces and oversized grout/bevels.
6. Run `git diff --check`. Report any remaining house regression separately from the kitchen result.

Commands, after implementation:

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --python-exit-code 1 --python tools/build_house.py -- --render
/Applications/Godot.app/Contents/MacOS/Godot --headless --path . --editor --import --quit
/Applications/Godot.app/Contents/MacOS/Godot --headless --path . --fixed-fps 60 --script tools/check_house.gd
git diff --check
```

## Risks and decisions

| Risk | Decision |
| --- | --- |
| References disagree | Marina's tour governs; film frames, production photos and visitor plans supplement unresolved details. Flag actual ambiguity or physical inconsistency. |
| No measured dimensions | Document estimated dimensions and validate proportions from multiple views |
| Source resolution | Local Part 1 MP4 supplies 29 decoded 640 × 360 frames, including reverse views and the area annotation. Part 2 still uses storyboard thumbnails. Proceed with main-floor layout; obtain sharper footage for fine details where needed. |
| Reference colors affected by lighting/scanned prints | Match material relationships and response, not sampled RGB values |
| Correct furniture collision reveals old navigation assumptions | Update justified kitchen routes; preserve checks for actual walkability |
| Blender preview looks better than runtime | Approve material and lighting passes in Godot before calling them complete |

No new asset purchases or dependencies are planned. The next work is the layout/massing checkpoint, followed by the remaining ordered tasks.
