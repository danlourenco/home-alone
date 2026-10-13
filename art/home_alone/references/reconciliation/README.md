## Adopted direction: intact HOME_ALONE_FINAL.glb as the base

User explicitly selected the cohesive imported GLB as the structural/layout baseline. Marina supplies textures, furnishings and recognizable details. Do not resume survey-based room rebuilding or force the GLB into the rejected custom blockouts. Structural edits require a specific demonstrated mismatch. Existing blockouts remain separate for comparison.

The source assets/home_alone/online_home_alone/HOME_ALONE_FINAL.glb and Unity's misleadingly named Assets/ThirdParty/HomeAloneExterior/HomeAloneExterior.glb are byte-identical: SHA1 483ae5da33fce6d17082408d4821664932537c42. The source has 309 meshes / 330 nodes. ExteriorShell.cs previously disabled/clipped its interiors in generated scenes; the original GLB is intact. New IntactHouseReference builder instantiates the original prefab without that clipping or 0.83 scale. It adds collision but does not reshape geometry, remove doors or change materials.

Mesh audit (native model units; these are not measured real-house metres): main treads span approximately X -0.94..1.17, giving 2.11 width; lower run Y 4.15..8.07 gives 3.92. Ground floor surface ~1.31, rear landing ~4.45, upper floor ~5.22. At the previous arbitrary shell scale of 0.83, this corresponds to about 1.75 width, 3.25 run, 2.61 landing rise and 3.25 upper-floor rise relative to its own ground floor. Current custom flight was 1.50 wide / 4.80 run / 2.68 landing rise / 3.35 upper rise. The biggest discrepancy is the longer, shallower custom flight, not just floor height. Scale and datum must be handled together: GLB ground is not at native zero.

Audit artifacts: art/home_alone/references/glb-audit/inventory.json, triangles.npz, native-floor-sections.png. Audit script: tools/survey/audit_intact_glb.py (Blender background; reads GLB, writes only audit artifacts). Source plan cuts are at native elevations 2.5 and 5.7; clipped plotting bounds omit distant site geometry, not GLB geometry. Heights include finishes and remain approximate. Unity reference scene is Assets/Scenes/IntactHouseReference.unity, built by Assets/Editor/IntactHouseReference.cs; runtime walking verification status is recorded in the audit README.

## Current central-hall increment

Active saved scene: Assets/Scenes/CentralHall.unity. Build Central Hall / Check Central Hall are in Assets/Editor/FoyerProportions.cs and the HomeAlone > Interior menu. This increment starts from the accepted front-floor extension in FoyerProportions, leaving that baseline intact.

Only three internal partitions are added: the bathroom/linen hall wall at Z 2.99–3.15, linen side at X 11.90–12.06, and linen front at Z 1.63–1.79. Cross-hall spans the existing 4.13 m front foyer width with 1.90 m wall-to-stairwell-edge depth (slightly less to rail face). Two 1.00 m plain openings face it. Bathroom is an L-shaped unfurnished space at front centre; closet internal footprint is 1.22 by 1.20 m. No bedroom extensions or old upper registration are restored. Stair dimensions, opening edge, front floor and ceiling are unchanged.

23 real-controller checkpoints pass, testing both sides of the broad hall, bathroom including its front extension, linen entry, ascent/descent and rear ground-floor recess. Stair-arrival render inspected: Assets/Captures/CentralHall/arrival.png. Dimensions/partitions are a reviewable hypothesis using the supplied rough plan; exact room dimensions, windows, fixtures, doors, trim and outward hall connections remain pending.

## Latest: front foyer ceiling / upstairs floor extension

FoyerProportions now has a full-width upper floor over the front foyer (X 9.15–13.28, Z 0.20–5.05). The side gallery begins at Z 5.05, avoiding overlapping slabs. The exposed stairwell begins 1.35 m along the lower flight; an L-shaped guard connects its front edge to the gallery rail. This restores about 13.86 square metres of floor relative to the previous open-front blockout. Upper elevation, stair rise/run and trial widths are unchanged.

The edge is a clearance-based trial prompted by supplied ceiling reference 14, not a calibrated image measurement. Sampling the covered steps gives minimum vertical clearance 2.2225 m to the solid ceiling underside at +3.08 m. Eighteen real-controller walking checkpoints pass, including ascent/descent and traversal across the new front floor. Images: Assets/Captures/FoyerProportions/extended-ceiling.png and front-upper-floor.png. Do not reintroduce the rejected upstairs room fit without first reviewing this floor/opening arrangement.

# Reconciliation review packet — 2026-09-11

Target confirmed by the user: a believable, fully connected house preserving Marina's recognizable rooms and the exterior's appearance.

**Latest user direction:** interior first. Defer exterior fitting and size it to the resolved interior later. Door frames and finishes wait until the basic layout is locked. Exterior conflicts in this packet remain a record for later, not a gate on interior work.

## Current: foyer proportion reset (user rejected upstairs fit)

Active scene: `Assets/Scenes/FoyerProportions.unity`; builder `Assets/Editor/FoyerProportions.cs`. The previous UpperInterior layout and 0.80-scale registration are rejected by the user for a narrow hallway and projecting rooms. Do not use its passing traversal tests as acceptance of its proportions.

The new plain blockout starts from the main-stair-only downstairs scene, without the rejected upper rooms/cross-hall. Trial main-flight width is 1.50 m (previously 1.25), side-hall/return width is 1.80 m (previously 1.64). No 0.96 m cross-hall remains. The existing 4.80 m lower run, 2.68 m landing and 3.35 m upper level are deliberately retained as provisional comparison values, not established measurements. Landing depth remains 2.55 m. Widening the flight reduces the ground-floor aisle; assess both levels together before committing further.

Neutral materials and hidden furniture/details make the space easier to assess. Original scenes and shared finish materials are preserved. Fourteen real-controller checkpoints verify ascent/descent, movement along both sides of the wider hall, and the rear recess. Captures: `Assets/Captures/FoyerProportions/foyer.png` and `hall.png`. These are uncalibrated views, not a verified photographic match.

Next: visually establish foyer/stair/hall proportions with the supplied movie and Marina views before attaching bedrooms again. The transcript's “10 feet tall and 30 feet long” describes the outdoor photographic backdrop, NOT the foyer or staircase; do not use it as an interior measurement. Breakfast upstairs stairs remain omitted and basement entrance reserved.

## Rejected upstairs build — 2026-09-11

**Active scene:** `Assets/Scenes/UpperInterior.unity`. Build via **HomeAlone > Interior > Build Upstairs Layout**, starting from the saved main-stair-only `ConnectedStairStudy.unity`. This is an unfurnished layout for review, not a claim of measured architectural accuracy. The prior standalone downstairs scene remains available.

[Floor stacking overlay](08-upstairs-registration.png) · [Hall from stairs](../../../../unity/HomeAlone/Assets/Captures/UpperInterior/hall-from-stairs.png) · [Parents’ entry](../../../../unity/HomeAlone/Assets/Captures/UpperInterior/parents-entry.png) · [Walking test](../../../../unity/HomeAlone/Captures/UpperInterior/traversal.txt)

The user's clockwise-rotation hypothesis is implemented without mirroring: `X = 5.336 + 0.80 * surveyY`, `Z = 11 - 0.80 * surveyX`. This uniformly scales the old image-derived metre estimates; 0.80 is an authored fit, not an independently measured scale. It puts Kevin's room at the front-right and the hall bathroom above part of the front foyer/vestibule. The room pattern, rather than the previous distorted transform in SurveyHouse, supplies the starting point.

**Corrections and compromises:**

- The old survey’s `linen_closet` rectangle beside the parents’ entrance is actually hall space in the supplied overhead. The actual linen closet is beside the hall bathroom. Its rectangular boundary and the bathroom's L shape are approximated from the overhead/isometric views.
- Buzz’s old rectangle extended into the bathroom. That partition is corrected. The two west bedrooms are also narrowed by about 0.77 m relative to the rotated/scaled rectangles to clear the existing foyer wall and main flight.
- The side gallery connects to a transverse hall near the lower part of the main flight. Its rear edge is recessed 0.36 m over the flight after a runtime head collision exposed insufficient clearance. The local hall width is 0.96 m before the rail thickness; most of the hall is 1.32 m. This is a navigable compromise, not a source-verified hallway width.
- The ensuite entry is widened by 0.52 m to avoid the parents’ room corner pinching the doorway. Parents’ bedroom retains the L-shaped entry and separate ensuite access; no secondary stair cuts through it.
- Windows are plain provisional openings. Room trim, furnishing, the exact upper hall arch/profile, exterior fit, attic and basement descent remain unresolved. Old Upper/Attic/Basement groups remain disabled; UpperInterior supplies the new upper rooms.

**Verification:** 41 continuous checkpoints cover ascent, every bedroom, both bathrooms, the linen closet, the L-shaped extensions, return descent and the downstairs rear recess. All pass with the real 1.8 m character controller, gravity and no jumps. The 26-point ground circuit also passes after adding the upper geometry. The white floor soffits are visual only and do not alter those collisions. Unity captures were inspected for the stair arrival, parents’ approach and downstairs foyer; these are uncalibrated views and do not establish a photographic match.

`Assets/Editor/UpperInterior.cs` contains the layout and runnable walking check. The builder exports room rectangles to `Captures/UpperInterior/layout.json`; `python3 tools/survey/upper_interior_review.py` regenerates the overlay against the downstairs survey and old upstairs rectangles. The red overlay lines show stair footprints at different heights: overlap with the hall is deliberate above the lower steps, with the cut reserving headroom at the higher ones.

## Current revision — main staircase only (2026-09-11 evening)

The user approved removing the breakfast-to-upstairs staircase to preserve the parents’ bedroom and ensuite. Its basement entrance remains on the breakfast-facing side of the former bay, as identified in supplied screenshot 13. The closed white door reserves that location; the basement descent is not built or traversable yet.

The saved `ConnectedStairStudy.unity` now has a crosswise rear landing spanning X 9.15–13.28, Z 8.50–11.05 at +2.68 m, in front of the rear window. Four provisional turning steps run forward along the right side to the +3.35 m hall. A transverse arch at Z 8.50 opens into the recess beneath the landing, with a separate plain closed door at the back. The side gallery terminates at the turning flight; white soffits replace its exposed wood underside. The stair side has a continuous triangular enclosure. The inner vestibule opening is now 2.50 m wide, with a separate plain front door and sidelights. Door detailing remains deferred.

The secondary flight, invented hidden turn, rear extension and upper return/link have been removed from this working scene. Both dining/breakfast openings remain. Main/upper/attic room registration is still unresolved: the old upper rooms remain disabled, and no fully reconciled upstairs is claimed. The turning-flight dimensions are authored, not measured from the supplied images. Residual wallpaper conflicts and exterior fitting remain deferred.

Runtime checks: main stair/vestibule/recess round trip (18 checkpoints); ground circuit including both dining doors and approach to basement door (26 checkpoints), in both directions, using the real character controller with gravity and no jumps. Additional checks cover the rear openings, shared wall, solid spandrel, removed service geometry and basement door orientation.

Current captures: [foyer](../../../../unity/HomeAlone/Assets/Captures/ConnectedStairStudy/revised-foyer.png), [rear landing](../../../../unity/HomeAlone/Assets/Captures/ConnectedStairStudy/revised-landing.png), [breakfast/basement entrance](../../../../unity/HomeAlone/Assets/Captures/ConnectedStairStudy/revised-breakfast.png). Supplied references 06–13 are archived in [first-floor-user-shots](first-floor-user-shots/).

**Earlier study descriptions and footprint/circulation diagrams below are historical and superseded by this revision.** Rebuild still uses Build Main Stair Candidate followed by Build Connected Stair Candidate; the legacy filenames/menu names remain for compatibility.

## Start here

**First-floor screenshot review, late 2026-09-11:** the five [user-supplied views](first-floor-user-shots/) and Marina's ground-floor overhead agree on the broad arrangement, but **do not validate the current connected-stair study**. No scene geometry was changed during this review.

| Evidence | Reconciliation with current study |
| --- | --- |
| Rear-facing foyer view (05), also the supplied inline view | The transverse arch sits forward of a separate recessed door. The study instead cuts a rectangular opening directly into the rear wall at Z 11.05; it omits this intermediate wall and passage depth. The breakfast opening is on the perpendicular right wall and must remain a distinct opening. |
| Rear-facing view (05) and ground-floor overhead | The landing/window composition and white overhead enclosure are not reproduced by the study's oak gallery spanning Z 0.20–11.01 with a long exposed rail. Resolve the landing, stairwell opening and ceiling boundaries together; these views alone do not establish their exact dimensions. |
| Stair side view (02) | The enclosure has a continuous diagonal stringer above a wallpapered triangular wall, ending beside a rear passage. Our per-tread boxes approximate enclosure but leave a stepped profile. Filling beneath the flight did not complete the reference geometry. |
| Front-facing views (01, 03) | A broad inner vestibule opening frames a separate entrance door with two sidelights. The survey's 1.20 m inner opening is not supported by these proportions; the retained vestibule needs revision together with the front entrance assembly. |
| Dining rear wall (04), checked against ground-floor overhead | Two doors flank the china cabinet on the breakfast-facing wall. The study preserves two openings on that wall, but their widths, spacing and relationship to the breakfast hutch are not dimensionally verified. |

The room adjacency is broadly consistent: living room left and dining room right when facing rearward, breakfast behind dining, main stair along the foyer's left side. Correct the foyer's vestibule, arch/recess, landing and ceiling as one basic volume before accepting its dimensions or detailing frames. The older Godot generator already represents a separate arch wall and a wider vestibule opening; recover those source-supported relationships without treating its metre values as measurements. Navigation checks remain useful but are not evidence of visual fidelity. Residual z-fighting is deferred at the user's request.

1. [Existing floor overlays](01-floor-overlays.png): raw Marina-derived ground survey, two upper-floor registrations, older Godot outline and original exterior slice in common metres.
2. [Stair sections](02-stair-sections.png): why the current main and breakfast stairs do not solve the same vertical problem. Landings/arrival lines are schematic; labelled flight rise/run values come from the generators.
3. [Exterior and floor levels](03-exterior-levels.png): original mesh wire projections with Unity and Godot levels. Includes surfaces behind the facade; this is a diagnostic projection, not a hidden-line elevation.
4. [Visitor-plan overlay](04-visitor-plan-overlay.png): the two visitor drawings register substantially better than our Marina-derived upstairs. This supports using their connections as candidates, not overriding Marina's interior compositions.
5. [Interior comparisons](05-interior-comparisons.png): source versus saved Godot compositions. Directions are similar, but cameras are not calibrated matches.
6. [Main stair fit candidate](06-main-stair-fit-candidate.png): a dimensioned, **authored hypothesis** restoring a turning flight at a +3.35 m upper level. It fits the selected foyer envelope arithmetically; it now has a separate Unity traversal study (below), but has not been camera-fitted.

## Connected-stair layout study — 2026-09-11

Current scene: `unity/HomeAlone/Assets/Scenes/ConnectedStairStudy.unity`. This is a candidate circulation loop, not the adopted full-house layout. **User direction: defer door frames and finishes until basic layout, floor levels, openings and clearances are locked.** New breakfast/foyer and dining openings remain plain.

- [Built footprint against original exterior](07-connected-stair-footprint.png)
- [Breakfast layout view](../../../../unity/HomeAlone/Assets/Captures/ConnectedStairStudy/breakfast.png)
- [Main stair enclosure](../../../../unity/HomeAlone/Assets/Captures/ConnectedStairStudy/stair-enclosure.png)
- [Final traversal log](../../../../unity/HomeAlone/Captures/ConnectedStairStudy/traversal.txt)
- [Exported Unity geometry bounds](../../../../unity/HomeAlone/Captures/ConnectedStairStudy/geometry.json)
- [Moving-view contact sheet, Part 1 18:26–18:48, two-second intervals](breakfast-motion-18m26s-18m48s.jpg)

**Source-supported arrangement:** M18, M23 and the moving view place the hutch, foyer doorway and breakfast stair foot sequentially along the west side. The old Unity layout placed the hutch against the stair and passed the foyer doorway under the landing. The Godot model preserves this sequence better. The study restores that grouping and provides a dining doorway beside the hutch. Exact positions and sizes remain authored. The main flight now has solid steps and an enclosed spandrel, consistent with M04/M18, rather than floating tread boxes.

**Authored connection:** service foot at `(13.44, 0, 10.60)` in Unity coordinates; width 1.18 m, 12 rises of 0.1675 m over 3.00 m to a +2.01 m landing, then eight eastward rises over 2.00 m to +3.35 m. The 1.20 m rear landing reaches Z 14.80 m, **2.16 m beyond the old breakfast rear wall**. The upstairs return occupies X 16.62–17.82 m and links to the main gallery above the low end of the service flight at Z 10.40–11.60 m. The first deeper crossing caused a real head collision and was moved forward. This connection is not claimed to exist in Marina's model or the movie set.

**Unresolved fit:** plate 07 shows the return extending beyond part of the original upper-wing outline at the current exterior transform. The user has since deferred exterior fitting: continue resolving interior room relationships around the candidate arrivals and revisit the shell after the interior is established. Original roof containment, the parents-room arrival, main landing/window proportions and the exact visible service tread count remain unverified. A one-view main-stair nosing fit was explored but not adopted: coplanar tread edges alone cannot establish the whole stair's dimensions. No source-calibrated camera match is claimed.

**Verification:** the real `FpsController` passed 42 continuous circuit checkpoints, including the reverse circuit, with gravity and no jumps. The main stair's separate 13-checkpoint route also passed after the enclosure change. Shared-wall and stacked-opening regressions passed. These tests check navigation and geometry, not architectural accuracy.

**Rendering defect fixed:** adjacent foyer and dining rooms emitted coincident full-thickness walls with different materials, producing the reported disappearing wallpaper. `SeparateSharedWalls` partitions overlapping opposing room walls at their midpoint while preserving their room-facing planes and total thickness. It runs in the main generator and both studies. The original `House.unity` remains unchanged; its saved geometry receives the fix only when regenerated. Old breakfast doorway trim was removed; subsequent frame detailing is deferred per user direction.

Rebuild through **HomeAlone > Studies > Build Main Stair Candidate**, then **Build Connected Stair Candidate**, with the current scene saved and Play mode off. Run **Check Connected Stairs In Play Mode** to repeat the circuit. Geometry bounds for plate 07 were exported from Unity; `python3 tools/survey/reconciliation_packet.py` regenerates the plate from that export.

## Unity main-stair study — 2026-09-11

Open `unity/HomeAlone/Assets/Scenes/MainStairStudy.unity`, then press Play. Rebuild via **HomeAlone > Studies > Build Main Stair Candidate** while out of Play mode with the current scene saved. Run **HomeAlone > Studies > Check Main Stair In Play Mode** to repeat verification.

The study restores the proposed 16-rise main flight, rear landing and four-rise east turn to a +3.35 m gallery. Existing upper, attic and basement geometry is disabled in this scene. These are candidate dimensions, not surveyed measurements. The original `House.unity` remains byte-identical (SHA-1 `839716dfea818296e96da96d0ebad8ef6855432f`), and build settings have not been changed.

The actual FPS controller passed all 13 continuous round-trip waypoints at 60 Hz, gravity enabled, without jumping: ascent, turning flight, gallery, descent and passage beneath the landing. A regression check also verifies the stacked rear doorway/window and solid wall between them. Visual inspection exposed overlapping headers in the shared wall generator; its opening calculation now subtracts all openings together. Existing saved scenes only acquire that correction when regenerated.

- [Traversal log](../../../../unity/HomeAlone/Captures/MainStairStudy/traversal.txt)
- [Initial foyer capture, before enclosure/wall repairs](../../../../unity/HomeAlone/Assets/Captures/MainStairStudy/foyer.png)
- [Initial landing capture](../../../../unity/HomeAlone/Assets/Captures/MainStairStudy/landing.png)
- Builder: `unity/HomeAlone/Assets/Editor/MainStairStudy.cs`; movement check calls the same `FpsController.TickMotion` used by keyboard movement.

These are geometry inspection views, not calibrated matches to Marina. Rail profiles, runner risers, window shape, adjacent-room trim and lighting still need refinement. The retained exterior shell was already clipped by the older Unity generator, so this scene cannot validate original roof clearance or facade/window alignment. Breakfast stairs and complete floor stacking remain unresolved. Next: camera-fit this connection and register the original exterior against several shared anchors before promoting its dimensions into the full house.

Unity startup recovered after reinstalling the missing Mac IL2CPP support module and the user accepting Unity's launch repair. The exact repair dialog text was not captured. The editor subsequently compiled, built and ran this study successfully.

## Findings that change the proposed work

**Restore the kitchen area as an explicit source statement.** The later survey correction saying the oval circles breakfast is wrong. [Part 1 at 13:20](breakfast-800.jpg) shows the oval around the working kitchen. The archived automatic captions at 13:17–13:24 say the adjoining kitchen, on its own, comes in at 477 ft². This establishes the stated area, not a precise boundary trace or independent verification of our rectification. The 41.2 m² rectangle and the claimed ±0.15 m accuracy remain unvalidated. Do not repeat either the original “proven by agreement” claim or the later “not the kitchen” dismissal.

**Place basement access off breakfast.** The [Part 2 frames](upper-evidence.jpg) and narration at 15:35–15:53 explicitly identify the breakfast-room door. The current foyer basement entrance is an authored mismatch. The descent itself is not measured, so reserve it without inventing a complete basement plan.

**Recover the main stair's form, not all Godot dimensions.** [Part 1 05:40–05:50](main-evidence.jpg) establishes the long flight, rear landing and window composition. The Godot generator includes a turning flight; the Unity generator does not. Godot's +3.35 m upper level versus Unity's +3.00 m changes the geometry materially. The proposed candidate retains 16 + 4 rises at 0.1675 m and a 1.59 m gallery before rails/trim. The 3.35 m level is a hypothesis to test against the exterior, not a newly discovered measurement.

**Breakfast stair: an authored continuation is unavoidable.** Part 2 06:58–07:24 states the set stair did not emerge upstairs, with a hypothetical arrival near the parents' room. At [07:24](upper-444.jpg) Marina marks a possible location. The subsequent phrase introducing the hall bathroom is a new topic; it should not be transcribed as the stair's confirmed destination. Keep the visible stair in the breakfast room and design its hidden continuation jointly with the upper landing and basement access.

**Do not mistake the foyer stair seen through a door for the service stair.** The [15:25 view](breakfast-925.jpg) shows both: the foyer flight through the opening, and the breakfast newel at the right edge. [15:15](breakfast-915.jpg), [18:34](breakfast-1114.jpg) and [13:10 overhead](breakfast-790.jpg) provide complementary views. They support the hutch/door/stair composition; exact foot/winder coordinates and the corridor-under-landing assumption remain unresolved. Do not reverse the entire stair again from a single still.

## Evidence ledger

| Feature | Evidence inspected | Established observation | Remaining uncertainty / action |
| --- | --- | --- | --- |
| Main stair | Part 1 03:20, 05:20, 05:40, 05:50; Godot generator | Long visible flight, rear landing/window; Godot retains a turning flight | Camera-fit turn, riser count and landing level; test proposed plan |
| Breakfast composition | Part 1 13:10, 15:15, 15:25, 18:34, 18:45 | Separate main-stair sightline and breakfast stair; hutch and door grouping | Resolve foot and turns against full moving view, not image screen direction alone |
| Service upstairs arrival | Part 2 06:58–07:24 captions and 07:24 frame | Set has no actual arrival; proposed near parents' room | Design and label hidden connection |
| Basement door | Part 2 15:35–15:53 captions and selected film frames | Door in breakfast room | Exact descent, well and basement extent unknown |
| Kitchen area | Part 1 13:17–13:24 captions, 13:20 and archived 13:23 frames | Kitchen is explicitly stated as 477 ft² | Define perimeter and projection calibration before assigning dimensions |
| Floor areas | Archived Part 2 11:01 frame | Displayed 2,620 / 1,900 / 476 ft² | Definition of counted area and relation to room polygons not established |
| Upper proportions | Raw survey + `upper_rect.png.json` | Current rectification used `ky=1.0`; subsequent Unity fit uses unequal scales | Validate aspect ratio before declaring all raw room dimensions accurate |
| Exterior | Original GLB, freshly extracted world-space slices/edges | Existing scale/translation can be reproduced | Multiple-anchor fit and attic-specific roof section remain necessary |

Caption tracks are automatic; see [main transcript](transcript.txt) and [Part 2 transcript](upstairs-transcript.txt). They are existing locally archived source material, not newly verified manual transcription. Selected native frames were extracted with ffmpeg at the times in their filenames. No claim is made that the entire videos were replayed in this pass.

## Coordinate and measurement notes

- All plan plots use X right, rear coordinate increasing upward; vertical elevations are metres above the imported ground datum.
- Original exterior Blender coordinates are transformed by `0.83 * (x,y,z) + (9.445,2.208,0)`, reproducing `ExteriorShell.cs`. No meshes are clipped or modified.
- First upper overlay: translation `(4.10, 0.08)`, no reflection or scaling. This aligns approximate front datums; it is not a best-fit registration.
- Second overlay reproduces Unity's mirror and scales, **before** its hall replacement/room trimming. It is not a plot of the final Unity room geometry.
- Godot outline is translated `(11.20, 0.20)` to align the foyer centre/front. Dimensions remain the existing generator estimates.
- Visitor drawing scale: ground 168 px / 4.572 m, from the labelled living-room width; upper 169 px / 4.572 m, transferring the corresponding span. This assumes that span is unchanged across floors. Front anchors: ground `(379,580)` px, upper `(400,436)` px, both mapped to `(11.20,0.20)` m. Main-block rear-line residual is approximately 0.17 m; left facade residual approximately 0.07 m. Pixel picks are approximate. These residuals measure agreement between drawings, not accuracy against the real building.
- The [publisher](https://hookedonhouses.net/2009/11/30/inside-the-real-home-alone-house/) attributes those plans to a visitor, Eric. Marina's [production-photo page](https://www.mockingbirdlane.design/post/home-alone-in-depth) remains a source for the next camera-fit pass.

## What to build next

Test the main-stair candidate as one coupled foyer/landing/gallery slice, with the original exterior visible. Compare the 3.35 m hypothesis against the current 3.0 m level before adopting either. Keep the main flight in a double-height void; derive floor/ceiling cuts from the accepted stair envelope. Check the rear-door passage under the landing, window sill relationship and full turn with the actual Unity player.

For breakfast, retain the verified downstairs composition and reserve an upper arrival near the parents' area. Resolve its foot/winders and hidden continuation before furnishing or fitting upper rooms. Use the visitor plans as a connection hypothesis, with departures from Marina listed explicitly. Do not substitute the existing incomplete Godot service flight wholesale.

This packet establishes the comparison baseline and a main-stair candidate. It does **not** yet establish final stair geometry, a complete stacked house or tested headroom. R1/R2 items needing camera calibration, moving-view review or a full multi-anchor registration remain open in the task list.

## Reproduction and preserved inputs

- `python3 tools/survey/reconciliation_packet.py` regenerates the six plates from the survey JSON, original mesh extraction and source images. Uses existing NumPy/Pillow; no new dependency installed.
- `Blender --background --python-exit-code 1 --python tools/survey/extract_exterior_sections.py` refreshes `exterior-slices.npz` from the original GLB. It opens a clean transient scene and saves no Blender model.
- `survey-inputs/` preserves ground/upper/kitchen rectifications, transform metadata, vanishing-point arrays, and the selected kitchen/upper/attic source frames from the earlier scratch directory. The original `survey_out.py` still points to scratch; it was not run or silently rewritten. The ground input remains `../tour/ground-floor-user.png`.
- Arithmetic assertions verify the existing upper transform endpoints, stair rise totals and candidate clearance budget. Six plates were visually inspected. That initial packet pass changed no Unity runtime geometry; subsequent study validation is recorded above.
