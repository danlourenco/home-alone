# Interior structure audit — September 13, 2026

## September 14 completed full access routes

Supersedes the pending access notes below. [Basement round trip](basement-round-trip.cs.txt):20 continuous checkpoints pass from kitchen through its basement doorway, down native stairs, around existing basement objects viaX11.5/Z16.5, through rear doorway and up exterior stairs, then back to kitchen. [Attic round trip](attic-round-trip.cs.txt):8 checkpoints pass from upper hall to attic landing and back. Actual FpsController at60Hz with gravity, no jumping or intermediate teleport; original player state restored. The first basement straight-line test hit an existing object nearX13.85/Z12; routing via the open central aisle resolved it, so no further geometry was removed. This validates specified routes, not every basement corner or historic dimensions.

Furnished-room regression checks also pass: Kevin16, kitchen10, parents10, ensuite9, Buzz14 plus alternate wing and animated tarantula containment. Normal walkthrough restored; point shadow light count0. New geometry changes this continuation: none to shell; breakfast fixture aligned and Kevin desk/chair arrangement corrected separately.

## Follow-up completed: stairs, crosswalk, downstairs circuit and Buzz clearance

The current base has the expected major connections in the areas tested. **Retain the shell for now.** This pass does not establish exact film dimensions, and no walls/floors/furniture were moved. The specifically requested Buzz daylight exposure fix was completed separately after the initial audit below.

### Stair and hallway findings

- Fresh entry comparisons at camera `(1.9,3.0,0.5)`, yaw0, vertical FOV60 and a closer view at Z2.5 show the main flight, rear window/landing and right-side return/ceiling. Changing camera position alone substantially changes the apparent stair size. Neither view is a solved match to the film lens; do not derive a percentage scale error from it.
- Crosswalk camera `(0.1,6.9,6.7)`, yaw155, vertical FOV60 shows the broad upper arch, foreground balustrade, projecting closet wall and adjacent bathroom opening. This supports the broad film arrangement visible in the supplied upper-hall target. Exact arch profile, railing proportions, window size and relative doorway spacing remain approximate.
- Live raycasts at X0 locate the rear edge of the front crosswalk floor at **Z4.670**, with floor Y5.21. Relative to the closet-wall front at Z1.71, the projected depth is **2.96 m**. This is not the unobstructed width of every part of the hall: railing thickness and the closet's lateral footprint also matter.
- The ceiling really does extend over the beginning of the stairs. At Z4.25 the tread is Y1.506 and overhead Y4.920 (**3.41 m clearance**); at Z4.50 the tread is Y1.703 and overhead Y4.724 (**3.02 m**). By Z4.75 the overhead opens to Y8.358. These samples support the user's ceiling-over-stair-foot observation; there is no sampled low-headroom reason to cut back that crosswalk.
- Foyer side-wall ray hits away from openings are X−0.94 and X4.71: approximately **5.65 m wall-to-wall** in the current base. That is a model width, not verified film width. No global scale change is justified by camera appearance alone.

### Downstairs findings

- At eye/torso height, the dining/breakfast partition is around Z7.26. Its two openings are approximately X5.1–6.4 and X8.3–9.7 in a 0.1 m ray sweep; intervening wall remains solid. These are sampled open intervals, not precise finished-jamb dimensions.
- The walking controller passed through **both openings**, then into the kitchen and back to the foyer through the rear breakfast connection at about Z8.
- Complete **19-checkpoint continuous route passed**: foyer → living → foyer → dining → west breakfast opening → east breakfast opening back into dining and out again → kitchen aisle → breakfast → rear foyer → front foyer. Gravity and floor support were checked at each stop; no teleporting between route checkpoints or jumping. Test setup/cleanup restores the original player position.
- Two initial waypoint choices encountered geometry: the living-room target crossed the wall at Z0 instead of the opening at Z1.4; the kitchen target crossed object193 at X10.62,Z8 rather than going around at Z10. Correcting the route resolved both. These were not missing-door defects and no collision geometry was deleted to make the route pass.
- This confirms downstairs circulation, not kitchen island scale, basement descent, every corner or full-house dimensional accuracy.

### Buzz: the clearance question is now more specific

Live bed assembly bounds: X−3.990..−1.410, Z−1.090..0.390. Dresser bounds: X−3.950..−3.150, Z−2.240..−1.670. The overlapping X ranges and **0.580 m Z gap** place this bottleneck beside the bed, near its foot, rather than beyond the end of its long axis.

The mattress's **2.30 m length runs along X**; its **1.22 m width runs along Z**. Shortening the length alone would not directly widen this side gap. Relevant variables are bed width/post projection, dresser depth and the bed's front-to-back placement. Do not change one without checking the reference composition.

Re-inspected Marina `tour556.jpg` (headboard immediately beside door, bedside table toward window) and `overhead78.jpg` (bed/window/dresser relationships). They support the intended relationships but contain no known scale. The bed silhouette is more slender/detailed than the current simplified asset, but an exact replacement width cannot responsibly be calculated from these differently projected images alone. Keep the shell and furniture position pending calibration; no arbitrary mattress shortening or room enlargement was performed.

### Review images and repeatability

Fresh Unity images:
- [Entry comparison](../../../../unity/HomeAlone/Assets/Captures/IntactHouseReference/audit-entry.png)
- [Closer stair/landing](../../../../unity/HomeAlone/Assets/Captures/IntactHouseReference/audit-foyer.png)
- [Upper crosswalk comparison](../../../../unity/HomeAlone/Assets/Captures/IntactHouseReference/audit-upper.png)

Compare with [movie foyer](../reconciliation/first-floor-user-shots/12-movie-foyer.png), [upper film target](../foyer-film/upstairs-film-quality-target.png), and [upper isometric](../reconciliation/first-floor-user-shots/08-upper-isometric.png). Camera framing is approximate, not calibrated photogrammetry.

The successful Unity CLI evaluation is preserved in `downstairs-route.cs.txt` alongside this report for repeat checks in Play mode. The test temporarily disables input and restores position/input in `finally`. Preview camera offsets were discarded/restored to normal walking configuration after the audit.

**Next unresolved evidence:** obtain a scale anchor or better-matched view before changing foyer/stair width or Buzz's bed width. The ensuite fixture outline remains the clearest already-supported shape mismatch for a future modeling pass. Accepted breakfast-stair and basement exceptions remain unchanged.

---

## Initial audit (retained below; follow-up above supersedes pending circulation items)

Current priority, authorized by the user: validate recognizable rooms and their connections before further lighting or decorative refinement. Working scene: `Assets/Scenes/IntactHouseReference.unity`, native-scale HOME_ALONE_FINAL base. Earlier generated SurveyHouse/ConnectedStairStudy dimensions are historical, not this scene's measurements.

## Accepted compromises and deferred work

- Breakfast-room staircase need not connect upstairs. Preserve important room layouts rather than inventing an arrival through the parents' suite. This is an accepted exception, not a traversal defect to fix.
- Basement wall completeness and ceiling-height fidelity are deferred. Do not extrapolate that acceptance to main-floor or bedroom discrepancies.
- Linen closet stays closed; its interior is not required for the walkthrough.
- Daylight exposure/bounce, finishes and decorative fidelity are paused. Existing lighting remains unchanged. Global day EV10–14 versus local foyer EV4–10 is an identified exposure inconsistency; its contribution to the reported entry flare still needs a controlled motion comparison.
- Original source asset remains intact. No shell, furniture, lighting or camera settings changed in this audit.

## Evidence and status ledger

“Walkable” means the tested controller route passes; it does not certify film accuracy. “Supported relationships” means qualitative evidence, not a measured film-set plan. No area is dimensionally signed off yet.

| Area | Supported / current working arrangement | Unresolved structure question | Status / next action |
|---|---|---|---|
| Foyer and main stairs | Main flight rises rearward, rear cross-landing at window, return flight reaches upper hall. Side passage remains beside stairs. Current captured view and supplied movie foyer show these broad relationships. | Fit entry camera to film before judging apparent stair width/run, rear window size and front ceiling-overhang depth. Current view uses a wider/different camera; pixel proportions are not measurements. | Retain base; main stairs and spawn pass live traversal. First camera/proportion comparison priority. |
| Rear landing | Window and table/picture to its left, enclosing wall and balustrade retained. | Window center/arch dimensions and exact landing depth remain visual approximations. | Supported arrangement; dimensions pending. |
| Upper hall / stair opening | Return reaches gallery; closet closed, adjacent bathroom and bedroom access retained. | Compare arch/opening silhouette, closet projection, gallery width and front crosswalk over the stair foot against the supplied isometric and film views. Do not certify these from the close-up decorated-door capture. | Hall route passes; wider matched view needed before structural sign-off. |
| Living / dining / breakfast | Native first-floor shell retained. User supplied overhead identifies two dining-to-breakfast openings. | Explicitly verify both openings and the foyer-to-breakfast/basement-door relationship against the current scene; no fresh continuous downstairs circuit test in this pass. | Reference available; next downstairs audit item, not yet confirmed. |
| Kitchen | Native shell retained; two unobstructed samples give about 3.34 m overhead clearance. | Island/circulation and room aspect ratio require current overhead comparison. | Pending comparative audit; no resizing. |
| Parents' room | Bed, hearth, bedroom entrance and ensuite route retained. | Absolute room/furniture dimensions and hearth-wall/window spacing not calibrated to film. | Live 10-point route passes. Preserve focal composition while comparing references. |
| Ensuite | Bedroom connection, vanity approach and bath/shower access work. | Existing oval bowl + separate tray differs from the reference's integrated curved-front bath/shared-screen arrangement. This is a known fixture-layout mismatch, not proof that the shell is too small. | Live 9-point route passes. Reconcile fixture outline before any room resize; dimension investigation remains deferred. |
| Kevin/Jeff room | Hall entry, beds and front-window desk/dresser relationships recorded in existing furnishing work. | Furniture scale, window spacing and exact envelope still unverified. | Live 12-point route passes; reference-scale review pending. |
| Buzz room | East headboard/entry, front windows/dresser, west desk/Jordan, north display/terrarium relationships recorded from film/tour. Unsupported west doorway was infilled; side wing uses rear-bedroom access. | Bed-to-dresser projected gap is only 0.58 m including posts/hardware; mattress is 2.30 × 1.22 m. Determine furniture scale before blaming or moving walls. | Existing room/wing check passes. Highest-priority bedroom dimensional question. Do not shrink furniture merely to conceal it. |
| Basement / attic / secondary rooms | Retain current base. | Basement ceiling and walls are known provisional areas; attic/secondary-room fidelity not covered by this pass. | Deferred, not signed off. Basement vertical samples below are not a full traversal or minimum-headroom survey. |

## Live height measurements

Unity world metres, rounded to centimetres. Recorded September 13 in Play mode. Each sample casts down/up from a known interior point, triggers ignored, mesh backfaces enabled temporarily and restored afterward. Results are nearest collision surfaces at that point, not a whole-room minimum or an architectural survey. Furniture hits were excluded from room-height conclusions after resampling. World Y is an arbitrary datum.

| Area | Sample X,Z | Floor Y | Overhead Y | Clearance |
|---|---|---:|---:|---:|
| Vestibule | 1.90, −1.50 | 1.312 | 4.455 | 3.14 m |
| Foyer front | 1.90, 1.00 | 1.311 | 4.921 | 3.61 m |
| Foyer side passage | 3.40, 5.00 | 1.310 | 4.920 | 3.61 m |
| Living | −3.70, 4.40 | 1.310 | 4.453 | 3.14 m |
| Dining | 7.40, 1.80 | 1.311 | 4.454 | 3.14 m |
| Breakfast | 7.40, 8.00 | 1.309 | 4.649 | 3.34 m |
| Kitchen | 11.00, 15.00 / 13.00, 11.00 | 1.306 / 1.308 | 4.646 / 4.648 | 3.34 m |
| Rear stair landing | 0.10, 8.80 | 4.452 | 8.357 | 3.90 m |
| Upper hall | 3.55, 3.50 | 5.215 | 8.359 | 3.14 m |
| Parents | 10.30, 4.00 | 5.215 | 8.358 | 3.14 m |
| Ensuite | 10.00, 8.00 | 5.214 | 8.357 | 3.14 m |
| Kevin | 6.40, 0.20 | 5.216 | 8.360 | 3.14 m |
| Buzz | −4.50, 0.70 | 5.216 | 8.360 | 3.14 m |
| Basement central overhead object221 | 1.90, 1.00 / 1.90, 4.00 | −2.225 / −2.226 | 0.623 / 0.622 | 2.85 m |
| Basement overhead object130 | −3.00, 4.00 / 7.00, 4.00 | −2.226 | 0.917 | 3.14 m |

Ground-to-upper floor separation is about **3.90 m**, with the rear landing about **0.76 m below** the upper floor. Foyer ceiling samples are about **0.47 m higher** than living/dining samples. These are useful model constraints; none establishes the movie's actual height. Repeated 3.14 m values across rooms and basement warrant investigation of the base's vertical proportions, not an immediate global scale change.

Rejected kitchen samples: at X13.5,Z14.4 and X12,Z13, downward rays hit object163/object181 at Y2.289 (raised surfaces), so the resulting 2.36/2.16 m intervals were not called floor-to-ceiling heights.

## Checks completed this pass

Ran existing `SurveyBuilder.CheckIntactMainStairs`, `CheckParentsBedroom`, `CheckParentsEnsuite`, `CheckKevinBedroom`, and `CheckBuzzBedroom` in the current Play scene. All returned PASS; checks restore the player's position and controller state. Main-stair check includes settling on the spawn floor, ascent, rear crossing, return to upstairs, gallery crossing and descent. This is bounded route coverage, not proof every square metre is walkable.

Visually reviewed the archived current `FoyerBenchmark/day-final.png` and `upper-hall-day-final.png` against supplied `12-movie-foyer.png` and `08-upper-isometric.png`. These are differently framed views; they establish comparison priorities, not camera-calibrated size errors. Existing room evidence/dimension ledgers were reviewed, not independently re-photogrammetrized.

## Next work and useful additional references

1. Match a current Unity camera to the movie entry/stair view and the upstairs crosswalk view. Establish stair/door/window/ceiling-edge landmarks before adjusting geometry.
2. Verify downstairs opening topology and a continuous foyer → living/dining → breakfast → kitchen route. Preserve the accepted nonconnecting breakfast stair.
3. Calibrate Buzz's bed/dresser relationship, then parents/ensuite fixture outlines. Record a proposed dimensional change and its affected rooms before implementation.
4. Revisit basement height and missing boundaries after the important-room structure holds. Resume lighting/decorative work after the layout checkpoint.

Most useful new material, if available: **a wider Buzz view showing the entire bed, dresser and doorway together**, or a **continuous upstairs shot showing the stair arrival, closet and adjoining openings**. Existing foyer references are enough to start camera matching. A basement shot including floor, ceiling/beam and a complete door/person would help later. Screenshots without a known scale help relationships but cannot establish centimetre accuracy; no reference collection is blocking the next step.

Related evidence: [dimension review](../dimension-review/README.md), [Buzz](../buzz-bedroom/README.md), [reconciliation images](../reconciliation/first-floor-user-shots/), [foyer references](../foyer-film/README.md).
# September 14: existing attic and basement flights

Current Unity evidence (weight5 for model state,0 for historical dimensions): native attic stairs run from X−3.6,Y5.22 toX−8.95,Y8.56 atZ3.28; actual controller ascends/descends without jumping. Basement stair centreX5.59 runs Z14.6,Y0.91 toZ10,Y−2.23. Imported slab object250 covered its treads atY0.82; descent stopped atZ12.26. Temporarily excluding that collider made both directions pass, establishing the obstruction.

Saved correction cuts only the existing stair opening X4.93..6.25,Z9.86..13.86 through that slab, with render/collision agreement. Source GLB unchanged, no resized stairs. Six local stair checkpoints pass after saving; floor collision remains beside the cut. [Runnable Unity eval check](secondary-stair-route.cs.txt). Window clipping area/UV regression also passes. Full approach/circuit remains unverified; historical basement dimensions remain deferred. Capture `Assets/Captures/IntactHouseReference/basement-stair-opening.png` is too dark for appearance sign-off.
