> **October 12, 2026 — CURRENT PRIORITY: [SfM reconstruction plan](tasks/sfm-plan.md).** Supersedes everything below, including the Buzz landmark-calibration loop (do not resume it). Unity only; Godot retired. Spike passed: Buzz room + upper hall solved jointly from Marina Part 2 via COLMAP (`tools/sfm/`, outputs in gitignored `sfm-work/`). Entries below are history.

> CURRENT Buzz candidate B: 3.90×4.80×2.40m, estimated. Main house untouched. Shelves stop 65cm from door wall; dresser/bed clearance67cm. Fourteen waypoint route passes Edit/Play; Unity left in Play mode. Same-scale plan: art/home_alone/references/buzz-poc/footprint-comparison.svg. Poster is topology corroboration, NOT measured scale.

> September 18 CURRENT: BuzzWalkableCandidate.unity built, open and running. Plain furniture/window volumes; estimated 3.65×4.27×2.40m room. Eight-point controller route passed Edit and Play mode; main house unchanged. See art/home_alone/references/buzz-poc/WALKTHROUGH.md. Camera-depth fit is still rejected; do not resume endless calibration as prerequisite to reviewing candidate.

> September 15 CURRENT: Buzz cross-depth gate FAILED. Headpost 5–8px success did not generalize to footpost: 59px with prior calibration, 92px with joint near-point fit. No dimension changes applied. See buzz-poc/README.md and review.html. Next: longer-segment multi-depth feature/camera solve; do not promote 39° lens or 1.15 bed length as measurements.

> Latest Buzz PoC: joint camera/headpost fit applied ONLY to isolated scene. 559s new frame headpost errors 4.64/8.31px; head depth hits zero bound and room depth remains unresolved. Reproduce fit.py → rigid_fit.py → apply_joint.py → Unity Build. No house-wide propagation yet.

> Buzz PoC continuation: added third desk-wall window; verified three markers in isolated scene. Annotated comparison: `art/home_alone/references/buzz-poc/review.html`. Overhead apparent bed/depth fraction 0.414 vs PoC 0.467; unresolved parallax, no structural expansion applied. 54s/60s images are production photos, not CG views.

> September 14 — Buzz-only PoC built in separate `BuzzProportionPOC.unity`. See `art/home_alone/references/buzz-poc/README.md` for sources, measured ratios, checks and remaining gates. Wall-plane proof works; full room depth/furniture fit remains unvalidated. Main walkthrough untouched. Do not propagate dimensions yet.

## CURRENT OVERRIDE: Marina-first reconstruction reset

User asks whether incremental patches muddied the reconstruction and wants first-principles thinking. Yes: imported dimensions were overconstrained and walking tests were not visual validation. Read tasks/marina-reconstruction.md and current tasks/plan.md before more geometry edits. Marina is primary design reference. Preserve movie hallway silhouette; proposed entrance alcove explicitly rejected and never applied. Temporary BuzzRoomProportions.cs was deleted; original Buzz walking route restored. User allows coordinated front-wall adjustment, but proposed95cm expansion was never implemented/applied/saved. Current scene remains previous walkthrough. Next is Buzz/hall multi-view relative-dimension fit, then connected floor plans and separate neutral blockout. No missing reference request blocks this. Do not resume blanket front deformation or treat previous candidate centimetres as established measurements. Living/dining review was interrupted and is not complete.

## Autonomous continuation — September14
- User explicitly says keep proceeding without per-step stops; requests missing information only when needed. Then says no Buzz stated measurement; infer from Part2 around0:50. Extracted overhead50.jpg (CG whole upstairs) and overhead54.jpg (production-set framing/windows, no furniture). Adopted inferred bed + bedside +.25Z, no resize; bed root(-2.85,0,-4.15), bedside(1.10,0,-2.59), builder updated. Dresser gap .58→.83m; Buzz14/wing8/containment/windows PASS; overhead capture inspected. Low confidence in exact metres, appropriate as authored fit per user.
- Ensuite saved shape correction: ParentsEnsuite.cs BuildEnsuiteBathShower shared by full builder/scoped ReconcileEnsuiteBathShower. Curved-front straight-backed bath footprint1.18×1.24m, rim5.83, basin5.38; wall upstands/shared divider and glass screen; original compact allocation remains provisional. Bath upward-normal/rim/basin collider checks +ensuite9/parents10 PASS. Settled ensuite-bath-approach.png inspected; before frame smeared, not reliable comparison.
- Kitchen saved circulation blockout in new KitchenLayout.cs: oval1.05×2.8 breakfast table centre8.8,10.8,8chairs;8islandstools (5long/3short). First table centre8.0 crowded actual stair, moved+.8X, no shrink. 10local checkpoints PASS. Original full circuit crosses new table; updated20point path in structure-audit/downstairs-furnished-route.cs.txt PASS both dining openings/foyer. One rejected local test waypoint10.5,8 hit existing wall, use10.5,10. Chandelier is now offset from table, registration pending; no lighting changes. Kitchen source packet now clearly separates old generated-model findings from current scene.
- kitchen-structure-overhead.png diagnostic EV5/AA-off, before furniture; kitchen-seating-layout.png normal lighting with furniture. Both inspected. Table/stools simplified footprints, not final movie assets.
- Plan top updated tasks/plan.md to avoid repeatedly restarting completed comparisons. Next: remaining major furniture footprint/access checks, then local silhouettes, then deferred lighting benchmark.
- All temporary diagnostics removed by Play exit or explicit cleanup. Current Play/daytime, normal perspectiveFOV75/near.05/AA restored, Player approx(-4.5,5.3,.7),yaw135, enabled. Last Buzz/windows checks PASS. No active requests remain (user answered). Original foyer candidate still HOLD.

## Buzz window dressing fixed — September14
- Saved `BuzzBedroom.cs` DressBuzzWindows + CheckBuzzWindows. Shared scoped method called by FurnishBuzzBedroom; replaces old front-only ellipsoid curtains with three pleated pairs and ivory reveal/casing/sill. Side lacked curtains/casing and showed brick. Existing75 sash assemblies untouched; clear sizes front .94×1.62, side .872×1.621. Sill difference1.5mm. No resize or furniture/room/light changes.
- Scene IntactHouseReference saved, Play/daytime resumed in Buzz at roughly(-2.2,5.3,.65), yaw227.05, normal camera75. Three-window check +75-window checks PASS, Buzz14/wing8 +tarantula containment PASS. Point shadows0, controls enabled. First post-route capture stale/smeared, settled recapture inspected. Before/after buzz-window-audit-before/after.png. New trim not a baked-lighting benchmark.
- README in references/buzz-bedroom cites film500 and tour550/556 with weights and dimensions. Bed/dresser Zgap confirmed .580m; nominal capsule diameter.6m. Passing traversal does not resolve comfort/film-scale discrepancy. Preserve furniture until stronger sizing evidence. Foyer candidate remains HOLD.

## Multi-view opening review — September13 follow-up
- HOLD candidate, retain working geometry. OPENING-REVIEW.md now indexes seven additional reference views/sets with question-specific weights. Ground cutaway removes upper edge; upstairs overhead omits stairwell; reverse rail/isometric support topology without calibrated edge position. Marina views are one evidence family. Film IMG_3844/45/46 support fixture/rear landing appearance, not the provisional fixture shift.
- New fit/landing-depth.py reuses tread-only camera fit and varies rear wall depth against held-out corner. Best sampled case still12px tread RMS/32px corner residual; unchanged width45.8px/115px. Rear-depth-only correction rejected, numerical depths NOT target measurements. Synthetic recovery assertion PASS; JSON saved. Python hashlib warnings unrelated to successful numerical run.
- Do not finish provisional floor/rail or claim foyer sign-off. Need simultaneous visible corner/rear landing/wall anchors or scoped measurement before dimension changes. Independent Buzz consistency work can proceed; avoid further one-view parameter churn.
- No Unity mutation this follow-up; read-only check confirms Play active. No scene save. Existing walkthrough retained.

## Local opening edge study — September13
- New `art/home_alone/references/foyer-calibration/fit/OPENING-REVIEW.md`: joint door+rail+DIRECTED return-line fit favours upper opening side edge X2.0 versus current2.689, with transverse rail Z4.6265 unchanged. Conditional on authored door/hand-picked frame;0.689m is not a verified film dimension. Initial tight-lens cutaway fit rejected because return slanted the wrong way.
- Disposable two-mesh rail replacement +0.689×2.81m floor strip top5.215 tested; no room/stair/height changes.14routepoints PASS; headroom3.414/3.021 unchanged; parents10/ensuite9/Buzz14+containment PASS. Chandelier overlaps added floor: copied fixture shifted−.70mX clears standing-envelope bounds; placement provisional.
- Current/candidate images opening-before.png / opening-candidate.png, downstairs opening-entry-before.png / opening-entry-candidate.png. Prototype shading not a lighting benchmark. Severe new-object ghosting cleared with temporary AA/lens-effects disable. A separate initial clone-transform error corrected by preserving world position/rotation/lossyScale. No permanent changes to rendering.
- RECOMMEND local opening change for multi-view confirmation, not main-flight narrowing. Rear landing depth, arch profile and panel heights remain unresolved. Original two mesh objects and chandelier restored; candidate removed. FPS75 near.05 TemporalAntialiasing restored, preview exposure removed, original stair test PASS. No scene save. Do not claim dimensional sign-off or applied architecture.

## Camera fits and disposable narrowing experiment — September 13
- Completed exploratory fit/candidate review: `art/home_alone/references/foyer-calibration/fit/REVIEW.md`. fit.py retains hand-picked points, camera/FOV grid, synthetic recovery assertions and JSON results. Four views: film stair, Marina5:38 (338seconds), new5:46 landing, upper film door. Numeric fits are not full-room calibration or dimension sign-off.
- Disposable central-strip compression25% tested in Play: X−.943..1.170 width2.113→1.585m, all geometry to right shifts−.52825m. Original11 roots inactive while cloned/deformed meshes/colliders used. No scene or original mesh saved. Clone lighting is invalid for comparison (no rebake, normals/fixtures differ); use edges only.
- Film fit baseline80°FOV3.14px vs candidate60°2.58px: difference below manual3px uncertainty. Marina landing tread fit45.78→12.06px but held-out wall/floor corner still95px off. Upper door-only fit2.36px leaves foreground rail/arch mismatch. Recommend RETAIN baseline; reject automatic narrowing, not claim25%correct. Need off-plane landmarks in joint solve.
- Candidate11-point stair/gallery walking PASS; headroom3.414/3.021m unchanged. Candidate adjoining-room routes NOT run, not certified. Original roots restored, disposable objects/meshes removed. Original mainstairs + parents10 + ensuite9 + Buzz14/containment PASS. FPS75normal restored, point shadows0.
- User correctly noted Muto account is in Marina interview. Transcript explicitly introduces him4:09–4:14, staircase stage/distortion account4:16–4:27. Production account weight5 for provenance, not numerical scale; distinguish it from Marina CG. Hunker direct Eve Cauley interview corroborates separate floor sets. Claude checklist useful for per-room inventory/stitching log, but universal standard dimensions and categorical Real labels rejected; accepted project priorities preserved. Details/citations in review and source ledger.

## Additional foyer references and preliminary comparisons — September 13
- `art/home_alone/references/foyer-calibration/README.md` indexes fresh original video frames, source times/classes and three current Unity views. Additional frames support rear table/picture/window arrangement and upper hall relationships; do not establish a stair shrink factor.
- Stage 2 remains incomplete: viewpoints approximate, no solved camera calibration or accepted proportion candidate. D01/D04 still open. No geometry/lighting changes. Distinguish visible furniture/panel/railing discrepancies from shell scale.
- Walking restored and verified: FpsController enabled, camera local(0,1.65,0), identity rotation, FOV75. Play/daytime retained; comparison poses not saved.

## Source weighting added — September 13
- User requires citations and explicit evidence weights. `art/home_alone/references/dimensional-baseline/SOURCE_WEIGHTS.md` now governs calibration, with 0–5 question-specific weights, claim confidence, source-family dependence and change criteria. Weights are project priorities, not statistical probabilities; do not average model measurements with unverified plan targets.
- Rechecked Hooked on Houses publisher: Eric visited/photographed real house in2004 and worked out the floor plans afterward. Dimensioned pair is visitor reconstruction, not verified film-set survey. Baseline +8/+30/+35% figures remain comparisons, not required shrink percentages.
- Film visible relationships5; Marina reconstruction3–4 depending corroboration, explicit scoped measurements3; visitor-plan labels2 as film targets; illustrated PDF0 absolute/1 relative dimensions; nativeGLB1 as film-scale evidence. Live Unity samples5 only for current-model quantities. User compromises are constraints outside weighting.

## Stage 1 dimensional baseline complete — September 13
- Current authoritative measurement packet: `art/home_alone/references/dimensional-baseline/README.md`; supplied first/second-floor screenshots and illustrated PDF archived alongside it. No geometry/lighting/camera changes.
- Live wall-face widths: living4.938m; dining4.938m upper/4.891m lower finish vs15ft=4.572m (+7–8%). Westwing4.748m and eastwing4.938m vs12ft=3.6576m (+29.8/+35%). Window-glazing offsets excluded; backface ray queries required for some imported partitions and restored after sampling.
- Foyer5.65–5.70m is wider than living/dining, while supplied plan depicts it narrower. Plan authorship/film-set scale unverified, so do not call differences proven movie errors. Global scale cannot reconcile room ratios.
- Main flight measured16 rises≈.196m, going≈.261m, first riseZ4.16, landingZ8.08/Y4.452; tread surface width≈2.10m atZ5. Floor separation≈3.90m unchanged. Stage1 complete means inventory/baseline, not film dimension sign-off.
- Stage2 next: D01/D04 foyer/stair local comparison candidate before modifying base. Preserve accepted nonconnecting breakfast stairs; basement fidelity deferred. D05 Buzz window mismatch also recorded; no window edits yet.

## Structural follow-up completed — September 13
- See structure-audit/README.md follow-up section. Fresh entry, closer stair and upper-crosswalk images captured; framing approximate, not solved film-camera calibration. Broad arch/closet/bath/gallery arrangement supported; exact proportions remain unverified. No shell or furniture edits.
- 19-point continuous downstairs circuit PASS, including both dining-breakfast openings and rear breakfast-to-foyer return. Successful repeat eval stored in structure-audit/downstairs-route.cs.txt. Initial failures were waypoints through walls/obstruction, corrected without geometry changes.
- Crosswalk rear edge X0,Z4.670; projected depth from closet face Z1.71 =2.96 m. Ceiling covers initial stair treads; sampled clearance3.41 m atZ4.25 and3.02 m atZ4.5, opening overhead byZ4.75. Foyer wall-to-wall5.65 m remains uncalibrated against film.
- Buzz 0.58m gap is along Z beside bed; 2.30m mattress length is along X. Shortening length alone does not widen that side passage. Bed width/post projection/dresser depth/position require reference calibration before changes. Re-inspected tour556 andoverhead78; no reliable absolute scale.
- Normal FPS camera/controls restored, Play/daytime retained. Next evidence-dependent work: camera/scale calibration for foyer and Buzz. Ensuite integrated fixture remains a supported future shape correction. Breakfast-stair connectivity and basement stay deferred.

## Buzz daylight correction — September 13
- User specifically requested this lighting fix despite the broader daylight pause. `RoomLighting.BuildBuzzDayExposure()` adds a local day-only volume under dayLayer, center(-3.63,6.8,-.2), size(4.8,3.1,4.1), blend .6, priority130. Saved profile BuzzDayExposure.asset uses Automatic clamped EV7, compensation0, Progressive adaptation3/1.5. This retains the global Automatic mode while interpolating bounds at the doorway; full room exposure stays stable when windows enter/leave view.
- Matched reverse-view A/B confirms outdoor EV10–14 made the interior nearly black; EV7 restores bed/shelves/wallpaper readability. No new lights, room geometry or bake changes. This is an exposure correction, not completed physically accurate daylight GI. Baseline/corrected captures: buzz-reverse-before.png / buzz-day-reverse.png under Assets/Captures/IntactHouseReference.
- Scene saved. Day-only activation/night exclusion and Buzz traversal check PASS. Play restored inside Buzz with normal FPS controls, daytime. Broader structural audit remains priority; other rooms' exposure issues are still deferred.

## Structure audit priority — September 13
- Latest user direction: validate important movie rooms/layout before further daytime/decoration tweaks. Breakfast stair need not connect upstairs; basement heights/wall completeness may wait. Do not invent a service-stair arrival through the parents' suite.
- Initial audit saved at `art/home_alone/references/structure-audit/README.md`: accepted compromises, room-by-room evidence/uncertainty, live sampled ceiling clearances and next reference needs. No geometry/lighting changed. Current Play scene IntactHouseReference; existing stair/parents/ensuite/Kevin/Buzz route checks rerun, all PASS, player restored by each check.
- Measured samples: living/dining/upper rooms ~3.14 m; foyer ~3.61 m; kitchen/breakfast ~3.34 m; basement ~2.85–3.14 m to sampled overhead collision surfaces. These are native-model dimensions, not film measurements or whole-room minimums. Kitchen counter hits excluded. Ground-to-upper separation ~3.90 m, rear landing ~0.76 m below upper floor.
- Next structural work: matched foyer/upstairs cameras to compare ceiling edge/window/stair proportions; verify two dining-breakfast openings and continuous downstairs circuit; resolve Buzz furniture scale (0.58 m projected gap, 2.30 m mattress) and ensuite integrated fixture outline before shell edits. These remain pending, not signed off by traversal. Existing reference collection is sufficient to begin; wider Buzz and continuous upstairs arrival/doorway views would be useful supplements.
- Daylight deferred: source inspection found global day EV10–14 vs local foyer EV4–10. This is a concrete settings mismatch, but the reported entry flare has not received a controlled motion A/B. No exposure changes made.

## Upper-hall continuation — September 13
- Final pass saved: 3 day + 3 night lightmaps for 415 surfaces. PASS CheckFoyerBenchmark, CheckFoyerReflections in both day/night, CheckFilmLinenDoor, CheckFilmUpperHall and all 11 main-stair route checkpoints. Day/night upper-hall captures and corrected day foyer inspected under Assets/Captures/FoyerBenchmark. Daytime scene saved, Play active, normal FPS camera/controls restored.
- Corrected the reflection diagnosis: synchronous ReadPixels on the cubemap produced misleading zero output. AsyncGPUReadback shows proper room capture. SSR was masking local cubemaps with blue sky reflections; SSR-off/probes-on vs probes-off captures confirm contribution. Local day/night SSR overrides are now OFF, reflection multiplier restored to 1. Exterior volume/settings unchanged.
- Both room probes now cover X−1.85..5.55 with 7.4 × 4.4 × 13 m boxes, centers (1.85,2.9,5.2) and (1.85,6.7,5.5). Original upstairs box excluded the closet wall at Z1.71. On-demand, non-time-sliced captures update on day/night switch; no every-frame capture. `CheckFoyerReflections` verifies all 12 faces with GPU readback plus coverage/SSR settings.
- `DressFilmUpperHall` adds botanical picture using the supplied film print, paired oval brass/ivory ornament, dark modeled urn and red/green poinsettia bracts. Clean green paint on hall faces of object231 and ivory on object203 replace textured painted-in molding; chair rail/baseboard/crown have geometry. Closet door/casing brought back toward wall by .14 m; frame no longer projects excessively. Source shell/collision retained.
- A small upper-gallery ceiling practical provides day/night light, at measured ceiling Y8.36. Its fixture design is provisional, not confirmed from film. Reference limitations recorded in foyer-film/README.md. New preparation contains 415 surfaces. Preparation now clears obsolete atlas assignment arrays; both fresh bakes are mandatory after geometry preparation.
- Trim endpoints measured by raycast at X0.9322 and X4.7307, panel top approximately Y6.49. Rails/crown now meet those surfaces; `CheckFilmUpperHall` guards against detached rails or projection into the adjacent opening. Broad door panel fields now use separate flat normals from their bevels. `FoyerAssign` clears an existing saved mesh before CopySerialized to avoid stale render buffers on repeat builds.
- Supersedes the previous unresolved-reflection note below. Remaining wider benchmark work: film wallpaper, richer foyer furniture/balustrade and performance evaluation. No claim of finished AAA fidelity.

## Foyer lighting benchmark and film linen door — September 13
- Final verification: six-panel door collision and all 11 main-stair route checkpoints pass; 331 surface day/night map assignments pass. Static batching is disabled for these surfaces because Unity otherwise burns in one atlas's UV offsets and refuses runtime changes. Native collision meshes remain intact.
- **Reflection work is NOT complete:** probes allocate 128px textures but sampled positive-Z face was entirely zero in CLI captures; disabling probes made no visible difference. Global reflection flag, camera frame override, every-frame/non-time-sliced test and layer masks did not resolve it; experimental runtime changes discarded. Saved probes remain on-demand. Day local IndirectLightingController reflection multiplier .02 reduces the intrusive blue outdoor reflection; this is provisional compensation, not a physically verified room reflection solution. Day upper hall still needs better diffuse/practical illumination. Do not claim full benchmark completion. Final captures in Assets/Captures/FoyerBenchmark; scene saved daytime with normal FPS camera, Play restored.
- `FilmLinenDoor.cs`: custom ivory six-panel door, profiled casing and brass knob replace original 2981/2983 and frame rendering 2982. Closed collision retained, adjacent bathroom remains open. Visual fit 1.10 × 2.51 m, not film measurements. Reference saved under `references/foyer-film/upstairs-film-quality-target.png`. The user's target remains substantially richer than our hall; wall pictures/oval ornament and furnishing/trim fidelity remain work.
- `FoyerBenchmark.cs`: 331 static render meshes given secondary UVs, separate day/night GPU bakes, two 128px on-demand HDRP reflection probes, wood normal/roughness mask. `FoyerBakedLighting` swaps maps and renderer assignments on HouseNightMode.SetNight. Copies preserved in Assets/Lighting/FoyerBenchmark/Day and Night. Bake preparation uses point shadows only while stopped in the editor; Finish restores NONE. Runtime point shadows must remain NONE.
- Local foyer exposure volumes: day automatic EV4–10, night fixed EV2.5, 1.2 m transition. Global outdoor exposure unchanged. Fake foyer bounce lights now zero; baked contribution replaces them. Avoid rerunning BuildRoomLighting/FoyerAssign blindly: they can overwrite these settings/UVs. Geometry rebuilds require PrepareFoyerBenchmark and BOTH new bakes.
- Bake workflow: BeginFoyerBake(false), wait for Lightmapping.isRunning=false, FinishFoyerBake(false), repeat true. Unity CLI timeout does not mean the operation stopped; inspect asset/state/log before repeating. ProgressiveGPU works on Apple Silicon; CPU mode failed. Optional APV dialog was declined. No Rosetta installation performed.
- Benchmark is a first lighting/material pass, **not completed AAA fidelity**. Continue matched-camera furnishing/wall finish refinement, then motion/performance evaluation; see VISUAL_QUALITY_PLAN.md.

## Curtains, room lighting, scenery boundary and dimensional review — September 13
- `HouseSheers.cs / AddFilmSheers`: 16 translucent folded curtain sections in supported living/dining/parents window groups. No colliders, point shadows untouched; Buzz dressing unchanged. Sources/limits in references/sheers/README.md.
- `RoomLighting.cs / BuildRoomLighting`: removes per-window interior helpers, adds 13 provisional ceiling/room sources and three actual bedside sources. Decorative window spill reduced to 3; foyer bounce to 30. Existing ensuite/foyer practicals included in day/night states. This is still direct-light approximation, **not baked GI or a completed AAA lighting pass**; ceiling-source locations await detailed fixtures. BuildExteriorNight now calls this builder.
- Found daylight sun/GlobalVolume inactive under legacy scene objects. HouseNightMode now toggles a separate dayLayer with active sun and copied RoomDayVolume. Automatic exposure bounded EV10–14, immediate adaptation, compensation −0.5. Original HouseVolume retained. Night point shadows remain NONE; sun/moon directional shadows retained.
- `BuildNeighborhoodBoundary`: four collider walls enclosing X−30..23, Z−34..42, vertical −12..18, low side/rear evergreen edges. All 15 neighboring houses have physics disabled and static renderer batching flags. Background remains simple 3D set dressing with perspective/parallax, no explorable interiors. House/yard/near street remain walkable. Neighborhood builder reapplies boundary.
- `RoomDimensionReview.cs / ReviewRoomDimensions`: live measurements saved in references/dimension-review/README.md. Buzz passage **0.58 m including posts/hardware**, mattress 2.30×1.22 m. Ensuite oval bowl fails to represent the reference's integrated curved-front bath/shower; no shell-size error percentage established, no furniture/walls resized. Next dimensional step: fixture shape reconstruction/calibration before shell edits.
- PASS sheers, room/night toggle, four boundaries, eight street checks, Buzz/Jordan/tarantula containment plus room/wing traversal, nine ensuite points and main stair route. Captures: sheers-day.png, room-lighting-night.png, neighborhood-boundary.png. Day exposure was adjusted after initial washed-out preview. Scene saved in daytime; Play active.
- User asks for a more realistic AAA appearance. Next visual benchmark should be foyer: stable baked indirect light/contact detail, room reflections, material roughness/normals and better furniture geometry. See VISUAL_QUALITY_PLAN.md. Do not claim the current simplified furnishing/lighting pass is AAA quality.

## Rear landing correction — September 13
`Assets/Editor/RearLanding.cs` rebuilds `Film rear landing`: continuous rear wallpaper/lower-panel surround around the replacement arched paired sash, shallow flat-backed demilune console with drawer/slender legs/curved stretcher, small green planter, floral picture sampled by UV from Marina 05:50 (`Assets/Textures/LandingReference.jpg`, original full reference retained). Source GLB untouched; derived opening mesh assets updated. Window centres X1.39/2.71,Y6.30 remain visual approximations, not verified dimensions. Removed landing lamp references pruned from HouseNightMode parallel arrays. Point shadows remain off. `CheckFilmRearLanding`, main stair traversal, 75-window check and day/night check pass. Visually inspected `Assets/Captures/IntactHouseReference/landing-final.png`; wall gap closed. Play active at rear landing with normal walking controls. Plant remains simplified geometry; window/glass brightness and exact film proportions still need visual refinement.

## Latest confirmed fix — point-light shadow flicker

User said exterior flicker remained unacceptable after window cleanup. Live A/B disabled only point-light shadows; user confirmed twice that flicker stopped. Saved exact working setup: all point shadows OFF, moon directional shadows retained. FoyerLamp creates unshadowed lights; ExteriorNight.StabilizeHousePointLights applies to existing scene and builder; CheckExteriorNight rejects active shadow-casting point lights. Do not re-enable point shadows casually. Atlas oversubscription is a plausible contributor (128 request limit, 4096 atlas, many six-face point lights), not fully proven mechanism. Tradeoff: no local-light occlusion/wall leakage possible; bounded/baked shadows are future work. User-confirmed motion result is stronger evidence than previous static captures. No geometry changed in this fix.

## Latest correction — exterior flicker and lantern

FrontWindows now uses WindowMeshClip.cs for oriented clipping of crossing original triangles. New frame joints/bank frames no longer overlap. CheckFrontWindows includes solid-joint overlap assertion; CheckWindowClipping checks area and UVs (vertical and sloped). Both pass, plus night/stair/exterior routes. Saved camera TAA enabled (was None). Lantern bottom raised to Y3.88, light Y4.10, chain4.35–4.65; cage does not cast enlarged point-light shadow. Scene saved. A huge inline eval audit hung Unity and required forced close after normal timeout; reopened saved scene successfully. Keep future checks compiled and bounded. Recovery asset retained. See night-study README.

## Latest update — night and windows

ExteriorNight.cs and HouseNightMode.cs add N-key reversible night/day lighting; night is saved. FrontWindows.cs now covers 75 window sections on all elevations, including three dormers and three sloped roof panes. Original source GLB intact, copied render meshes cut only contained window triangles, original collision retained. Four original sloped-roof renderers disabled. CheckFrontWindows, CheckExteriorNight, main stairs, exterior route, Kevin room and ensuite pass. See references/night-study/README.md for source limits. Final app left in night walkthrough near front sidewalk, N toggles day.

Latest user direction: neighboring homes should be non-playable scenery. Boundary/backdrop implementation is next; not yet added. Detailed rear window patterns and dimensions remain provisional.

## Latest update — 2026-09-12 neighborhood

Use IntactHouseReference and intact GLB baseline; old layout instructions below are historical. Added WinterNeighborhood via WinnetkaNeighborhood.cs: reference-inspired simple houses/street/trees and nine front shutter pairs. Only outer snow banks object2946–2955 renderers/colliders suppressed; house geometry intact. Eight exterior controller checkpoints and main stairs pass. See references/neighborhood/README.md. Daytime walkthrough restored.

Night-video review and Parade comparison saved in references/night-study/README.md; preview frames reviewed, full download blocked. Night photoreal pass is pending. Buzz room furnished with Jordan cutout and animated terrarium; see references/buzz-bedroom/README.md. Film furniture relationships take precedence over fitting the base. Unsupported west side-wing doorway infilled; alternate rear-bedroom route verified. Exact film dimensions remain unverified. Ensuite dimensions deferred per user.

Kevin/Jeff room pass: KevinBedroom.cs / FurnishKevinBedroom creates KevinBedroomDetails. Uses native front-right room X4.92–9.86, Z−2.30–2.01, floor5.21. Bunks beside entrance, dresser on east wall, front-window desk/bookcase, reading chair/trunk/pinboard. Scene overrides object81 and object80 wallpaper; original object15 shoes moved beside trunk and object0 ball moved beside window to clear paths. Procedural wallpaper/check repeats approximate reference; mirror environment-only. Twelve CheckKevinBedroom checkpoints pass hall entry/return, bed sides, desk/bookcase approaches. Captured kevin-after.png. Source GLB unchanged. References: art/home_alone/references/kevin-bedroom/README.md. Walkthrough left ready in room, daylight retained.

Ensuite pass: ParentsEnsuite.cs / FurnishParentsEnsuite creates ParentsEnsuiteDetails. Scene-local finish mesh splits on object117 walls, object139 floor, object230 old vanity (local old vanity render faces hidden, original collider retained). Source GLB intact. References and deferred dimensional question: art/home_alone/references/ensuite/README.md. User suggested secondary staircase reduces room; checked treads west at X5.8, not below northeast inset. Cause remains unconfirmed. Rounded bath 1.16x1.24 m and shower 1.11x0.84 m are provisional fit dimensions, not reference measurements. Nine ensuite and ten bedroom walking checks pass. Captures ensuite-after.png and ensuite-vanity.png. Mirror environment-only; no planar reflection. Daylight retained, local warm vanity lamp added. Walkthrough left at ensuite entrance.

Parents bedroom furnishing pass: ParentsBedroom.cs / FurnishParentsBedroom adds scene-local ParentsBedroomDetails to IntactHouseReference. Four-poster red bed faces away from Z7.29 wall, bathroom opening left of headboard, white mantel/dark hearth on adjacent west wall, green bedside lamps, dressing table/stool and armoire. Dedicated floral-stripe material overrides object115 only; source GLB unchanged. References extracted from local Part 2 tour to art/home_alone/references/parents-bedroom (105s film; 195/200/255s CG). Furniture is a simplified reference-based approximation; curtains, upholstery refinement and framed artwork remain future details. User corrected protruding fireplace: seated in actual recess with offset (+.2,0,-.3), surround overlapping X8.91 wall face; hearth-recess.png inspected. Added initial gathered window panels, oval dressing mirror (environment reflection only) and green chair; parents-dressing.png inspected. Traversal rechecked after furnishing. CheckParentsBedroom passes 10 real-controller checkpoints covering both bed sides, bathroom and entrance. Render: Assets/Captures/IntactHouseReference/parents-after.png. Walkthrough left in bedroom.

Daytime restored at user request: saved IntactHouseReference has FoyerNight Volume disabled and its Light components disabled. Fixtures/furniture retained. Night builder re-enables night when called. Fixture refinements deferred; walkthrough left running.

## Separate lighting fixtures reconciled — latest

Four scene fixtures now coexist: glass-shaded brass stairwell pendant, shallow rear arch light, provisional entrance light, breakfast chandelier with upward opal bowls. See art/home_alone/references/foyer-film/README.md for map/evidence and limitations. FoyerChandelier now takes optional breakfast bool to reuse arms/chain with distinct mesh assets. New FixtureShade helper builds open double-sided lathe surfaces. Existing generated meshes must use Clear/set vertices/set triangles to refresh GPU buffers (CopySerialized alone left old geometry drawing in wrong locations). 271 source colliders unchanged, spawn/11 stair checkpoints pass. Render inspections: fixtures-reconciled.png and breakfast-fixture.png. Film wallpaper correction not part of this fixture pass.

## Chandelier moved over stairwell — latest user correction

Supersedes entrance-ceiling placement below. Fixture now suspended from upper ceiling Y8.36 on alternating oval brass chain links, centered X1.9/Z7.2, hub Y5.6, lowest arms about Y5.27. Ceiling and open void verified by rays; six arm-extremity rays all hit ground floor, not stair/landing. Longer drop makes candle arms visible through opening from entrance; chain is naturally occluded by front ceiling until closer. Source placeholders remain hidden. Main stair/spawn check passed during this move; final footprint checked after drop adjustment. Render inspected: Assets/Captures/IntactHouseReference/chandelier-stairwell.png. Final location remains reference-informed approximation.

## Entrance chandelier — 2026-09-12

User supplied cropped film reference, then explicitly requested placement above foyer entrance from vestibule. FoyerChandelier.cs replaces original placeholder objects236/237 (hidden in scene, source untouched) with six swept brass arms, ivory candles/emissive bulbs, central rod and ceiling rose. Integrated into SetIntactFoyerNight. Center X1.9/Z1.2, hub Y4.08, ceiling ray verified Y4.92; lowest curved arms about Y3.76 (roughly 2.45 above ground). Approximation of partly obscured fixture, not exact replica. Light moved from old low foyer placeholder to chandelier. Active original colliders now271; stair check accommodates baseline273 vs chandelier271. Spawn and all11 checkpoints pass. Settled render inspected: Assets/Captures/IntactHouseReference/chandelier.png. Walk controls restored afterward.

## Foyer finishes and night scene — 2026-09-12

IntactHouseReference now has scene-local foyer material overrides and FoyerNight furnishings/lights. Editor builders: IntactFoyerFinishes.cs (ApplyIntactFoyerFinishes), IntactFoyerNight.cs (SetIntactFoyerNight). Menu HomeAlone > Reference. If rebuilding baseline, reapply finishes then night setup. Imported GLB stays unchanged. Finish render meshes split material submeshes from original collision meshes; source vertex arrays and triangle counts verified unchanged. 273 original colliders, spawn and 11 stair checkpoints still pass with furnishings.

Wallpaper Assets/Textures/MarinaFoyerDamask.png is AI reconstructed from local Marina M01-03m20s reference (not an exact sampled historical wallpaper). Palette: cream, ochre, dusty rose, sage. New materials/mesh assets and night volume live Assets/Materials/IntactFoyer. Foyer region restricts overrides; adjacent rear recess retains its original finishes. Warm sconces, table lamps and fill light; fixed exposure EV4, dark gradient sky. Tables/chairs are simple procedural stand-ins, not final replica furniture. Night applies globally, other rooms do not yet have their own nighttime lighting. Original hanging lantern remains low-detail. Screenshot Assets/Captures/IntactHouseReference/foyer-night.png inspected. Basement walls/height deferred.

## Open-door walkthrough ready

User requested all doors open/removed for exploration. IntactHouseReference now hides all 18 identified door leaves and 18 handles (same IDs as Godot), retaining frames and original source asset. 273 active mesh colliders remain. Spawn settlement and 11 main-stair/landing/cross-hall checkpoints pass; foyer–breakfast–kitchen round trip passes 15 checkpoints. Reports: unity/HomeAlone/Captures/IntactHouseReference/{traversal,kitchen-traversal}.txt. Other individual rooms have not all been traversal-tested. Editor left in Play. FpsController R now resets to its own scene's starting pose, not SurveyHouse.Spawn. User was already moving around during checks; tests restore their prior position.

## Intact GLB walkthrough now active

IntactHouseReference.unity contains the complete imported GLB at native scale, original geometry/materials/doors, with 309 mesh colliders. Custom House is inactive in this reference scene. Main stair, rear landing and cross-hall round trip passed 11 checkpoints. Initial build failed due to Unity object null semantics and user fell through missing colliders; fixed with if(!collider), plus explicit spawn-ground validation. Avatar starts (1.9,1.4,0), ground surface ~1.31. Source files untouched. User explicitly chose GLB as structural baseline and Marina for textures/details. Do not resume custom layout work. Other door/room routes still need audit before claiming full-house traversal.

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

## Current: foyer proportion reset (user rejected upstairs fit)

Active scene: `Assets/Scenes/FoyerProportions.unity`; builder `Assets/Editor/FoyerProportions.cs`. The previous UpperInterior layout and 0.80-scale registration are rejected by the user for a narrow hallway and projecting rooms. Do not use its passing traversal tests as acceptance of its proportions.

The new plain blockout starts from the main-stair-only downstairs scene, without the rejected upper rooms/cross-hall. Trial main-flight width is 1.50 m (previously 1.25), side-hall/return width is 1.80 m (previously 1.64). No 0.96 m cross-hall remains. The existing 4.80 m lower run, 2.68 m landing and 3.35 m upper level are deliberately retained as provisional comparison values, not established measurements. Landing depth remains 2.55 m. Widening the flight reduces the ground-floor aisle; assess both levels together before committing further.

Neutral materials and hidden furniture/details make the space easier to assess. Original scenes and shared finish materials are preserved. Fourteen real-controller checkpoints verify ascent/descent, movement along both sides of the wider hall, and the rear recess. Captures: `Assets/Captures/FoyerProportions/foyer.png` and `hall.png`. These are uncalibrated views, not a verified photographic match.

Next: visually establish foyer/stair/hall proportions with the supplied movie and Marina views before attaching bedrooms again. The transcript's “10 feet tall and 30 feet long” describes the outdoor photographic backdrop, NOT the foyer or staircase; do not use it as an interior measurement. Breakfast upstairs stairs remain omitted and basement entrance reserved.

## Latest update: upstairs connected and reviewed

Current saved scene: Assets/Scenes/UpperInterior.unity, built by Assets/Editor/UpperInterior.cs from ConnectedStairStudy. Main stairs reach every upstairs room. Clockwise rotation with uniform 0.80 scale; exact dimensions remain provisional. Bathroom overlaps front foyer/vestibule. Corrected mislabelled linen closet/hall and Buzz/bath boundary; narrowed west bedrooms, recessed cross-hall edge for headroom, widened ensuite entry. Walking check: 41 upper/main-stair checkpoints and 26 ground checkpoints pass. See current upstairs section of reconciliation/README.md and 08-upstairs-registration.png. Old upper geometry stays disabled. Full furniture/trim, exact hall arch, exterior fit, attic and basement are pending. No service staircase restoration.

## Latest update: rear landing correction and service stair removal

User approved main staircase only, preserving parents’ suite. Current saved ConnectedStairStudy has broad rear landing/window, forward return flight, rear arch/recess and widened vestibule. Breakfast upstairs flight and invented upper connection removed. Basement entrance retained as closed placeholder on breakfast-facing side of former stair bay; descent remains pending. Old upper rooms still disabled. See the current revision at the top of art/home_alone/references/reconciliation/README.md; older connected-loop descriptions below are superseded. Source screenshots 06–13 archived there. Do not restore secondary staircase or treat proposed 90-degree upper-plan rotation as verified. Exterior, frames and residual z-fighting remain deferred.

# Current handoff — 2026-09-11, interior reconciliation

Read [tasks/plan.md](tasks/plan.md), [tasks/todo.md](tasks/todo.md) and the [reconciliation packet](art/home_alone/references/reconciliation/README.md) first. They supersede the historical notes below, including the old ±0.15 m accuracy claim and the real-house-plan authority claim.

- Latest user direction: **interior first; fit/size the exterior later.** Defer door frames and finishes until layout is locked. Preserve Marina's recognizable room relationships and a believable continuous house.
- Unity CLI is working against Unity 6000.6.0f1, project `unity/HomeAlone`, port 7800. Use the CLI for scene build/play/eval/capture. Sandbox access to its local connection requires the already-approved `unity command` prefix with escalation enabled. No repeated authorization is needed for routine project work.
- Active saved scene: `Assets/Scenes/ConnectedStairStudy.unity`, Play mode off. Separate `MainStairStudy.unity` is preserved. `House.unity` remains byte-identical (SHA-1 `839716dfea818296e96da96d0ebad8ef6855432f`).
- Builders: `Assets/Editor/MainStairStudy.cs`, `ConnectedStairStudy.cs`. Shared `StudyFlight` now uses solid steps; the main flight has an enclosed spandrel. Openings in the connected study are plain; obsolete doorway trim was removed.
- Fixed disappearing wallpaper: adjacent foyer/dining walls were coincident. `SeparateSharedWalls` partitions opposing overlapping room walls into half-slabs. Called by the full generator and both studies. Existing House scene is not regenerated.
- Final checks: main route 13 checkpoints and connected circuit 42 checkpoints pass, gravity enabled, no jumps. Tests also check stacked openings, shared-wall thickness/faces and the solid main-stair enclosure. Logs and exported bounds: `unity/HomeAlone/Captures/`. Views: `Assets/Captures/ConnectedStairStudy/`.
- Candidate service stair: 12 + 8 rises at 0.1675 m to the same +3.35 m upper level as the main stair. Source-visible hutch/door/stair sequence restored. Hidden east turn, rear bay extension and upper return are authored. Plate 07 records the footprint, including exterior conflicts deferred by the user.
- Next: reconcile upstairs room groups and their door relationships around the two stair arrivals. Avoid whole-floor mirroring/unequal scaling. Main-window/landing camera fit and service riser count remain unresolved; do not mistake traversal for source accuracy.
- Source corrections: Marina states the working kitchen alone is 477 ft²; the basement door is off breakfast. Upper service arrival is hypothetical near the parents area, not a confirmed hall-bathroom connection. See timestamps in the packet.

---

## Historical Unity handoff (superseded where inconsistent)

# Handoff — 2026-09-11 (Unity rebuild, structural pass)

Read this first. It replaces `ASTRA_HANDOFF.md` as the current state. The goal is unchanged: a walkable, faithful Home Alone house at Rainbow Six Siege (PS4) fidelity, house before gameplay, Marina Coates's tours as the fidelity authority. Engine is now **Unity 6 (6000.6) + HDRP**, project at `unity/HomeAlone`. Godot scenes are frozen, not deleted.

## Where things stand

**Works, keep:**
- `art/home_alone/references/survey/` — the ground-floor survey. Marina's overhead rectified (vanishing point fitted, residual 8 px) and calibrated to her onscreen 2,620 ft². Room, opening and fixture dimensions in `house_survey.json`, method and evidence in `README.md`. Cross-checked against her 13:10 kitchen overhead and the real house's first-floor plan. Ground-floor walls are good to ~0.15 m. **This is the layout authority for the ground floor.**
- `unity/HomeAlone/Assets/Editor/SurveyBuilder.cs` builds the whole scene from `house_survey.json`: rooms, openings, stairs, fixtures, lights, player. Menu: HomeAlone ▸ Build House From Survey. Nothing in the scene is hand-placed; change the JSON or the builder, never the scene.
- `WalkCheck()` in the builder sweeps the adult capsule (r 0.3, h 1.8) along a route through every storey after each build and logs every blocked segment. **Zero blocked is the acceptance bar.** Ground floor: 17 segments, 0 blocked. Upper/attic/basement: 5 still blocked (see below).
- `Assets/Editor/RoomDetail.cs` — foyer and kitchen fidelity pass: damask, oak floor, real stair treads/balusters/runner, casings, baseboards, beams, floral paper, terracotta, blue-tile counters, island, cabinets, window seats, table, hutch. Textures: Astra's wallpapers, Poly Haven oak and terracotta (CC0), generated blue tile.
- `Assets/Editor/ExteriorShell.cs` — places the downloaded `HOME ALONE FINAL.glb` (no license file; prototype use only) as an exterior skin: rotated, scaled 0.83, aligned on the front-left corner, interior triangles clipped, colliders only on ground-level site meshes. Garage and tree house are in it but out of scope.
- Unity CLI + Pipeline package + MCP server (`.mcp.json` at repo root) let Claude drive the open Editor: rebuild, sweep, capture, play. `HdrpBootstrap.cs` sets HDRP headlessly.
- Standalone macOS build at `unity/HomeAlone/Builds/HomeAlone.app` (ground floor only; predates the upper storeys).

**Broken or provisional, fix next:**
1. **Main stair is wrong.** Built as one straight run to the second floor. Film still, Marina's survey note and the real first-floor plan all show a straight flight to a **landing across the rear wall under the arched window**, with the rear door beneath it, then a **return flight** up to the second-floor gallery. Rebuild as two flights with the rear landing.
2. **Service (kitchen) stair is wrong in feel** even after two reversals. Current: foot at the breakfast front, rising rearward along the west wall of the bay to a 2.2 m landing over the corridor from the foyer. Ambiguity between Marina's overhead, the pizza-scene still (13:15) and the real plan (winder at the front, flight rising rearward, arriving by the master bath upstairs). Decide from the real plan and Marina's 15:25/18:34 frames together, then lock it.
3. **Second floor is not established.** Built from Marina's Part 2 overhead mirrored/scaled onto the ground frame with the hall snapped over the foyer stair. Her upstairs set does not stack on her downstairs set. The **real house's second-floor plan** (hookedonhouses.net, scratch copy under the survey tools) is the stacking authority and has not been measured yet. It shows: main stair well "open below" mid-hall, back stair arriving beside the master bath at the rear right, attic flight off the hall by the front-left office, bath and two bedrooms across the front, master suite over the kitchen wing.
4. **Attic placement is authored.** Room 5.15 × 8.58 m, well and chimney from Marina's true top-down frame; where it sits is a guess (over the hall, rear at Y 11.5).
5. **Basement is entirely authored.** No source at all. Current: full basement under the main block, flight under the main stair entered from the foyer's rear. Real houses of this type put it under the back stair; Muto says the door is off the rear hall.
6. **Exterior shell disagrees with the survey** by up to 1 m (its kitchen wing is bigger, its main block only ~10.5 m deep). The survey's upper floor pierces its roof. A rear chunk is missing from the clip. Reconcile after the interior is right, not before.
7. Sweep failures to clear: main stair headroom under the upper slab (well must start at Y ≈ 4.4, not 4.8), attic-stair top needs 0.4 m before the attic front wall, plus three test-route brushes (handrail, sill, rail). Kitchen landing over the corridor is legal at 2.0 m but feels low.

## The plan for the next session: reconcile, then lock

Goal: openings, staircases, walls and room sizes "pretty correct", every storey reachable, sweep at zero. Not inch-perfect.

1. **Adopt three authorities and write them down** in `house_survey.json`:
   - Ground floor: Marina survey (done).
   - Second floor: real house second-floor plan for **topology and stair positions**, Marina's Part 2 rooms for **sizes and finishes**. Measure the real plan the same way the ground floor was done (its own first-floor drawing is already matched to the survey, so the two drawings share a scale via the 12'/15' annotations).
   - Attic: Marina's frame for the room, real plan's attic-flight position for placement.
   - Basement: authored, but placed under the back stair per the real plan's stair positions. Say so in the JSON.
2. **Stairs first, before any room.** Model all four as explicit flights with landings: main (two flights, rear landing), service (winder at front per real plan, arrival by master bath), attic (straight, steep, from the hall's rear-left), basement (under the back stair). Put their wells in the JSON so floors above cut correctly.
3. **Rebuild, sweep, capture** each storey. The sweep route already covers all storeys; extend it as stairs move. Zero blocked before any fidelity work.
4. **Then reconcile the exterior**: decide whether to stretch the downloaded shell to the survey footprint (it is 19 % larger) or replace its main block. Only after the interior is locked.
5. Fidelity work resumes room by room after that: foyer and kitchen are already started in `RoomDetail.cs`.

## Reference material on disk

- `art/home_alone/references/survey/` — survey README, JSON, rectified plans, calibration frames, kitchen comparison.
- `art/home_alone/references/tour/frames-hd/` — Astra's 29 Part 1 keyframes at 1080p. `references/tour/part2/` — Part 2 frames.
- Both 1080p tour MP4s are in the repo root (Part 1 is the file ending "copy").
- Real-house plans: hookedonhouses.net/2009/11/30/inside-the-real-home-alone-house/ (first floor and upstairs images).
- `tools/survey/` — vanishing-point, rectify, mask, probe and output scripts used for the survey.
- Downloaded exterior model: `/Users/dlo/Downloads/home-alone-final/source/HOME ALONE FINAL.glb`, copied to `unity/HomeAlone/Assets/ThirdParty/HomeAloneExterior/`.

## Commands

```sh
# drive the open Editor (Unity CLI, project pinned)
unity status --format json
unity command eval --code 'SurveyBuilder.Build(); return "ok";' --project-path unity/HomeAlone --timeout 900
unity command get_console_logs --limit 400 --project-path unity/HomeAlone --format json | grep -o 'WALK CHECK[^"]*'
unity command capture_game_view --camera Camera --save_path Captures/x.png --project-path unity/HomeAlone
unity command editor_play --project-path unity/HomeAlone

# headless rebuild with the Editor closed
/Applications/Unity/Hub/Editor/6000.6.0f1/Unity.app/Contents/MacOS/Unity -batchmode -projectPath unity/HomeAlone -executeMethod SurveyBuilder.Build -quit -logFile unity/build.log
```

Playing: Editor ▸ Play, click in the **Game** tab. WASD, mouse, Shift sprint, Space jump, C crouch, R reset to vestibule, Esc frees the mouse.

## Gotchas learned today

- Marina's overheads are perspective; never read dimensions off them without rectifying. Front of the house draws ~17 % larger than the back.
- Cased openings keep their header, so they do not show as gaps in a wall-top mask. Read them from eye-level frames.
- Her 477 ft² kitchen figure is not the kitchen rectangle; the oval circles the breakfast/stair zone. Do not calibrate on it.
- HDRP API pitfalls: `StaticEditorFlags.Everything` does not exist, `HDRenderPipelineGlobalSettings` is internal, `QualitySettings.renderPipeline` must be set per level, `-nographics` breaks captures. `Object` is ambiguous in files that `using System`.
- Upper-floor rooms from Marina are ±5 %; the hall must be at least 2.4 m wide to walk beside the stair well.
- Nothing is committed. Everything from today is untracked or modified in the working tree.
# Basement/attic access continuation — September 14

Saved `SurveyBuilder.OpenIntactBasementStairSlab()` correction in IntactHouseReference. Imported object250 slab covered native basement stair at X5.59,Z9.86..13.86. Cut only X4.93..6.25, through slab height, using existing polygon clipper with optional depth (default preserves window behavior). Saved separate BasementStairSlabCut mesh; original GLB untouched. Four source triangles clipped. Both render and collider use corrected mesh. Attic up/down passes unchanged. Basement up/down initially failed Z12.26; isolating slab collider proved cause; after saved cut six total stair checkpoints pass. Side floor rays X4.8 and6.4 still hit; centre5.59 does not. Window clipper area/UV regression passes. Runnable `art/home_alone/references/structure-audit/secondary-stair-route.cs.txt`.

Play active, camera/FPS restored after capture. `basement-stair-opening.png` inspected but too dark for finish sign-off; no lighting changes. Remaining: kitchen-to-basement approach and basement/exterior circuit, other major-room footprints. Stair test starts on local landings, not full-house route. Basement historical height/walls still deferred.
# Latest continuation — full access routes and two placement fixes

September14: kitchen→basement→exterior→kitchen20-point round trip PASS; upper hall→attic landing→hall8-point round trip PASS. Saved runnable eval scripts in structure-audit/basement-round-trip.cs.txt and attic-round-trip.cs.txt. These supersede pending approach/circuit notes below. No extra basement geometry changes: routed around native obstacles viaX11.5,Z16.5.

Saved breakfast fixture/light registration to tableX8.8,Z10.8, retaining height and light settings; FoyerChandelier builder updated and KitchenLayout.AlignBreakfastChandelier scoped method added; kitchen test checks alignment. Re-reviewed Marina Kevin room355/365/375/385s: desk/chair were reversed relative to dresser. Saved desk−2.75X, chair+3.30X using KevinBedroom.ReconcileKevinWindowFurniture, invoked by fullbuilder. Kept room/furniture sizes. Expanded Kevin route16PASS; kitchen10,parents10,ensuite9,Buzz14+wing+tarantula PASS. Inspected settled kevin-window-layout.png; appearance remains provisional.

Unity Play active, normal camera/FPS restored,0 point shadow lights, all permanent changes saved. No pending user questions or active agents. Next remaining work is living/dining/secondary-room reference footprint review and reference furniture silhouettes; don't ask user to authorize routine continuation. Broader lighting and historical basement heights still deferred.
