# SfM reconstruction plan — October 12, 2026

Supersedes the per-room landmark calibration loop (Buzz depth gate, Sept 14–18). Unity is the only engine going forward; Godot is retired.

## Goal

A faithful, connected, walkable Unity reconstruction of the Home Alone house, whose every dimension traces to recorded evidence with a stated uncertainty, verified by scripts rather than by HANDOFF prose.

## Premise change (why)

Every failed Buzz fit assumed proportions could be recovered from hand-picked landmarks in a few frames. Errors grew with distance from the wall plane (headpost 5–8px, footpost 59px, then 92px): single-view depth ambiguity. Marina's tours are ~38 min of a moving camera through a static textured CG model: textbook structure-from-motion input. The solve recovers camera poses, per-shot intrinsics and 3D structure jointly, in one frame for all rooms.

## Spike result (done)

Part 2, 9:00–10:40, 4 fps, 400 frames, 38 excluded (title card + film insert). COLMAP 4.2.1 CPU, sequential matching.
- 362/362 frames registered across 4 models; mean reprojection 0.50–0.65 px; 6 min CPU.
- Model 2 contains Buzz's room (frames 1–96) and the upper hall (135–222) in one frame, linked by hall frames looking through Buzz's doorway.
- Solved focal lengths differ per model (1411 / 1565 / 1681 px): Marina's FOV varies between shots. Explains part of the fixed-60°-FOV failures.
- Buzz outline aspect ≈ 0.83 (arbitrary units), walls not yet separated from furniture faces. Not a measurement.
Artifacts: `sfm-work/buzz-hall/` (gitignored), `tools/sfm/{extract.sh,solve.sh,topdown.py}`.

## Phases (each ends in a scripted, re-runnable gate)

1. **Ingest lever.** Extract both 1080p tours at 2–4 fps; scene-cut log; exclude title cards, film/production inserts, overhead plan animations; mask caption overlays. Output: frame ledger (frame → video, timestamp, segment, kept/excluded + reason). Gate: every excluded frame has a reason; spot-check contact sheets per segment.
2. **Solve.** Per-segment intrinsics (camera per shot), sequential + loop-closure matching, merge segment models via shared frames/features. Gate: ≥90% of kept frames registered, mean reproj < 1 px, one connected model per floor (or a named list of unconnected pieces and why).
3. **Cross-check with MASt3R** (Apple GPU) on the same segments: densify low-texture walls, independently compare relative geometry. Gate: per-room width/depth ratios agree between COLMAP and MASt3R within a stated tolerance; disagreements logged, not averaged.
4. **Extract structure.** RANSAC wall/floor/ceiling planes per room; openings from gaps + door frames; stairs from tread planes. Output: `house_spec.json` (single source of truth) where every element carries provenance (frames, method) and uncertainty (spread across held-out subsets / bootstrap).
5. **Scale.** One global scale per connected model from Marina's stated areas (2,620 / 1,900 / 476 ft², kitchen 477 ft²) fitted jointly; per-anchor residuals reported. Conventional object sizes (doors, treads) as secondary sanity check only. Gate: anchors agree within stated tolerance or the outlier anchor is named.
6. **Floor stitching.** Align floors through main stair, landing, stair void, window relationships. Overheads (Part 1 ~1:34, Part 2 0:50, 14:00) used as held-out checks, not inputs.
7. **Unity generator.** One generator builds the blockout from `house_spec.json` only. Remove `SurveyHouse.cs` scale fudges and builder constants after the generator replaces them.
8. **`verify-house` skill** (pstack create-verification-skill shape). Launch: Unity batchmode build from spec. Drive: render blockout from every solved camera pose + run existing traversal routes. Evidence: per-view edge-overlay error vs. real frame on held-out views, traversal pass/fail, numbers with spread. Feature map: one file per room (views, thresholds, gotchas).
9. **Room-by-room sequence.** Ground floor first, all in the global frame. A room is done only when its gate is green; record before → change → after.
10. **Film deviation ledger.** Localize film stills against the model; where film set and Marina disagree, log a named deliberate deviation. Never average.
11. **Then** reuse existing assets/materials, reconcile exterior, resume lighting, then gameplay in Unity.

## Carried over

Frame ledger, source weights, traversal route scripts, poster/dimension reviews (as cross-checks), Unity assets and materials.

## Known risks

Flat-colour CG walls (mitigation: MASt3R); FOV changes (per-shot intrinsics); YouTube compression; Marina's model itself may be internally inconsistent (stitched rooms) — SfM will surface that rather than hide it; scale anchors are Marina's own claims, not independent survey.

## Adversarial review — October 12, 2026 (Fable 5.1)

Verdict: SfM is the right direction and the Buzz↔hall link is genuine, but the spike was overstated and the gates above cannot detect the error that sank September. Findings ([RAN] = checked on spike data):

1. **[RAN] Sub-pixel reprojection ≠ correct geometry.** Splitting Buzz/hall cameras in model 2 (focal 1578/1440 vs forced 1565) moved hall extents 1.009/1.173/1.124 and Buzz↔hall distance ~10%, while reprojection improved (0.648→0.583 px). Both pass "<1 px". Reprojection is a sanity check, not a geometry gate. Use SIMPLE_PINHOLE, fixed centre principal point (CG has no distortion); report intrinsics-sensitivity spread on every dimension.
2. **[RAN] Buzz aspect from SfM (0.75–0.80, clip-dependent; window/tree points pollute it) contradicts survey overhead (4.21×6.97 m, 0.60) by ~30%.** Survey's upper floor is itself suspect (19.2 m deep vs 16.9 m house). Resolve before going further.
3. **No test against known truth.** Every gate compares the pipeline to itself.
4. **"Held-out" views aren't.** Poses and blockout come from the same frames; 4 fps neighbours near-duplicate; image overlay is blind to global scale and to depth-stretch + compensating focal.
5. **[RAN] Spike overcounted.** Model 0 is junk (17 frames, 18 points, all also in model 1). Hall is in 3 pieces; `model_merger` fails for 2+3 and 3+1 despite shared frames. Registration thins at flat green walls (frames 220–222: 56–97 obs vs ~1,400).
6. **[RAN] Buzz↔hall link real but thin:** 281 shared points, frames 22–57 ↔ 163–211, single doorway aperture.
7. **[RAN] FOV claim confounded:** 1681 is from junk model 0; models 1/3 agree (1411/1416). Within-shot zoom not ruled out.
8. **Scale anchors:** "area" undefined (net vs gross ≈ ±5% linear); one anchor per floor model means no residuals; unclear whether areas describe Marina's model or the real house. Add door-leaf height and stair rise/going as co-equal per-room scale checks; report scale as a range. (Reviewer's claim that the 477 ft² kitchen anchor is discredited is WRONG: survey/README.md's Sept 11 banner reverses that dismissal. Kitchen anchor stays.)
9. **Floors don't stack in Marina's model** (survey Discrepancy #1; SurveyHouse.cs mirrors upstairs in X). If no continuous camera path crosses floors, stitching is an authored decision, not a measurement.
10. **Fidelity target underspecified.** Sept fixed film requirements (hallway silhouette, Buzz span definition, three-window Buzz) not carried over. Automatic film↔CG localization will mostly fail; scope film checks to named shots with manual line correspondences.
11. **[RAN] Ingest gaps:** frame 96 has the title ghost; captions unmasked; 14 image-fixed tracks; scene threshold misses dissolves.
12. **Bootstrap gives false tight error bars;** dominant errors are systematic (intrinsics, scale definition, link geometry).
13. **MASt3R and Unity generator/verify skill come too early.** MASt3R's learned priors make its agreement weak evidence.
14. **Nobody has asked Marina** for dimensions or the model file.

## Revised sequence (supersedes Phases 1–3 above until gates pass)

- **0a. Staircase stacking test (NEXT):** SfM on Part 1 "Tour of the Stairs and Landing" (5:33–5:53) and any continuous ground→upper camera path. One connected model across floors answers whether Marina's floors stack. (Contacting Marina dropped: no relationship; she is a YouTube creator whose CG is film-faithful, not a survey of the real house.)
- **0b. Synthetic truth test:** scripted Unity fly-through of the existing GLB (known metres) with per-shot and mid-shot FOV changes, title cards, captions, a dissolve, YouTube-like encode → unchanged pipeline → score room ratios and wall positions. Produces the real tolerances every later gate uses.
- **0c. Fix the spike clip:** pinhole intrinsics, per-shot cameras, caption masks, ±1 s padded exclusions, dissolve detection, dedupe; loop-closure/hierarchical mapper. Gate: the 100 s clip merges into one model.
- **0d. Resolve Buzz 0.77 vs 0.60:** wall-only points, intrinsics spread, cross-tour pass if Buzz appears in Part 1. Gate: discrepancy explained.
- **Gates from here on are independent:** cross-tour whole-pass holdout (solve Part 1, verify Part 2 via `image_registrator`), structural-line scoring, a +10%-depth negative control that must fail, uncertainty = max(cross-pass, intrinsics, scale-definition, synthetic-truth error).
- **Decisions needed from user:** (a) Marina governs geometry; film governs which named items? (b) floor stitching is authored, with options presented. Deviation ledger has two sections: Marina-internal inconsistencies, film vs Marina.
- MASt3R only when a room fails for lack of wall points. Minimal generator only after 0b–0d pass on one floor.

## Correction — floor stacking is UNVERIFIED (Oct 12)

The "upper floor doesn't stack" claim (survey/README.md Discrepancy #1: 19.2 m upper depth vs 16.9 m house, 13.0 vs 14.4 m facade, 1.5 m stair offset) comes from the Sept 11 overhead rectification — the same method that produced Buzz 4.21×6.97 m, which SfM contradicts by ~30%. A ~1.3× depth stretch would explain 19.2 m on its own. `SurveyHouse.cs` mirror/rescale is our workaround built on that measurement, not evidence. Real, separate fact: Muto says the upstairs was a separate set and the service stair never arrived upstairs.

## Reconciliation model (if floors or rooms don't fit)

Three constraint layers, in priority order:
1. **Envelope (hard):** the film exterior is the real Winnetka house — footprint, facade windows, roofline. Sources: exterior GLB, photos, dimensioned visitor plans (dimensional-baseline/).
2. **Film-faithful interiors (maximize):** per-room proportions, sightlines, compositions from SfM on Marina's model, checked against named film shots.
3. **Game usability (hard minimums):** capsule clearance, door width, stair rise/going, ceiling height.

Solve as a small optimization: each room keeps SfM proportions but may stretch within a tolerance; fit inside the envelope, align stair wells, meet usability minimums, minimize weighted deviation from layer 2. Output: per-room deviation ledger (how far, why). Infeasible → name the conflicting constraints for a user decision. Implements the Sept 11 "smallest local adaptation" policy.

## Experiment 0a result — staircase stacking test (Oct 12): INCONCLUSIVE, false link caught

Inputs: Part 1 305–360 s (stairs; kept 31–74, 116–199 — film/dissolve, arrow overlays, title excluded) + Part 2 573–618 s (upper hall). `tools/sfm/link.sh`: SIMPLE_PINHOLE per video, sequential + every-2nd-frame cross pairs, incremental mapper. 8.5 min mapper.
- Neither video climbs continuously between floors: Part 1 stops at the landing; Part 2 starts upstairs.
- One model held 125/128 p1 + 179/180 p2 frames, 0.44 px, 1,300 points seen by both — looked like success.
- `tools/sfm/link_check.py`: upper-hall cameras came out ~1.4 units BELOW the foyer (stairs climb 0.5→3.6). Physically impossible.
- Cause: strongest link p1 110–140 ↔ p2 160–180 joins the ground-floor stair wall (family photos) to a different upper-hall wall (landscape painting). Same repeating damask wallpaper → texture-pattern matches glued two walls.

Lessons, now gates: (1) any cross-segment link must pass a physical sanity check (camera heights / floor order) before use; (2) link evidence must include non-repeating features (frames, trim, fixtures), not wallpaper alone; (3) sub-pixel reprojection and high registration again said nothing about correctness.
Next: rerun with wallpaper regions masked or links restricted to unique-feature matches; target the real shared view — p2 frames looking over the railing down the stairwell vs p1 landing frames.

### 0a follow-up — wallpaper-filtered rerun (Oct 12): NO genuine cross-floor link in these clips

- Homography "planar" filter caught nothing (false pairs only 27–48% homography-explained: different pattern repeats, not one plane). Premise wrong; discarded.
- `tools/sfm/filter_cross_matches.py` (colour+texture damask mask, dilated): ~97% of cross-video matches were wallpaper; 2566 → 14 pairs.
- Both strongest survivors false on inspection: p1/198 is the "Living Room" title fade (exclusion should start ≤195) matched to the "Hall Bathroom" caption (same serif font); p1/65↔p2/177 is shadowed damask the mask missed.
- Conclusion: these segments share no genuine view. Ground-floor stair climb shows family photos on the stair wall; upstairs railing views show landscape paintings on damask — likely different sections of the stairwell, never seen by both videos.
- Ingest lessons: caption/title text produces confident cross-video matches → must be masked; exclusions need ±1 s padding (reviewer #11 confirmed twice).

Implication: floor stacking cannot come from a direct SfM link with this footage. Stacking becomes the reconciliation solver's job (envelope + stair geometry: rise/run and landing from Part 1, stairwell opening and railing from Part 2), with the result flagged as authored, not measured — unless a fuller search of Part 2 finds frames looking down onto the landing that Part 1 also sees.

## Experiment 0b — synthetic truth test (Oct 12): COLMAP SIFT pipeline FAILS outside feature-rich rooms

Harness (re-runnable): `Assets/Editor/SfmSyntheticFlythrough.cs` (Unity batchmode, textured House.unity, SurveyBuilder walk-checked ground-floor route, 984 frames, exact pose + vFOV in gt.json; shots FOV 55 / 42 / 62 / 50→36 zoom) → `tools/sfm/synthetic_run.sh` (compose title card + caption + dissolve, ~6 Mb/s H.264, extract every 6th frame, solve, score) → `tools/sfm/synthetic_score.py` (Sim3 to truth: registration, contaminants, cm error, floor-plane stretch, FOV).
Note: first attempt used IntactHouseReference; renders flat/dark without HDAdditionalCameraData — use House.unity.

| Variant | Good | Elsewhere |
|---|---|---|
| single camera (unchanged pipeline) | shot 1 (kitchen): 1.1 cm, 2.0% | 1–2.4 m, >100% stretch; forced vFOV 45° for 62°/zoom shots |
| oracle per-shot camera | shot 1: 0.8 cm, 1.6% | 0.4–6 m, 60–580% stretch despite correct FOVs (54.5/55, 42.1/42) |
| per-frame focal | none | focal unstable 8°–137°; ruled out |

Findings:
- Intrinsics are NOT the dominant error. With correct per-shot FOV, wallpapered halls and plain walls still reconstruct meters wrong; only the feature-rich kitchen passes. Same failure class as the staircase false link: repeating/low texture silently corrupts geometry at sub-pixel reprojection.
- Scene-cut detection can't segment shots: caught the title card; missed the dissolve and an in-motion FOV change; 8 false positives on fast pans.
- Contaminant frames mostly rejected (≤1 registered).
- Caveats: synthetic house is plainer than Marina's CG (pessimistic on texture). Floor-plane stretch metric is ill-conditioned on near-straight paths (shot 0); replace with error against true 3D geometry.

Next: benchmark learned methods on the same harness and scorer — hloc SuperPoint+LightGlue (MPS) and MASt3R/VGGT (MPS). Pass bar to define from these runs; nothing proceeds to Marina footage until a method passes on wallpapered/plain shots.

## Experiment 0b, continued — method benchmark on synthetic truth (Oct 12)

All variants: oracle per-shot cameras, same 169 frames (4 fps), scorer `tools/sfm/synthetic_score.py` (shared loader `synthetic_score_lib.py`).

| Shot | SIFT (COLMAP) | ALIKED+LightGlue (COLMAP 4.2 built-in ONNX) | VGGT-1B (MPS, per shot) |
|---|---|---|---|
| 0 foyer, long straight walk | 127 cm | false merges, 0.7–4 m | 222 cm |
| 1 kitchen loop | **0.8 cm, 1.6%** | false merges | 27 cm |
| 2 breakfast/dining, 62° | 79–594 cm | false merges | **6.4 cm, 4.3%** |
| 3 living→den, long straight walk | false merge | false merges | 190 cm |

- SIFT+LightGlue: ~218 s/frame on CPU (8192 SIFT features), then killed by macOS under memory pressure. Retry only with max_num_features ≈ 2000.
- VGGT: 5 min for all shots incl. weight download; weights facebook/VGGT-1B are NON-COMMERCIAL (VGGT-1B-Commercial needs an application). Code: `tools/sfm/vggt_solve.py`, env `sfm-work/.venv` (torch 2.14; pycolmap removed — OpenMP clash with torch).
- PyTorch + pycolmap in one process abort (duplicate libomp). Kept separate; no KMP_DUPLICATE_LIB_OK.
- Scorer bugs fixed: (a) images.txt pairing dropped blank 2D-point lines, halving/shifting frames — would also corrupt real COLMAP models with zero-observation images; (b) `synthetic_score.py` edited while a run used it.

Read: methods succeed in different places; both fail on long straight forward walks (low parallax, 4 fps ≈ 35 cm between samples) → meters of along-path drift.
Next: (1) denser sampling (10–12 fps) on shots 0/3 — tests the parallax/overlap hypothesis; (2) test whether COLMAP–VGGT agreement predicts correctness on synthetic, to use as the acceptance gate on Marina footage where there is no truth.

### Dense sampling (12.5 fps) on straight-walk shots 0 and 3 — partial
COLMAP SIFT, per-shot pinhole, 246 frames, 12.7 min. Shot 3 alone: 39 cm median over a 9 m walk (was false-merged / VGGT 190 cm). Shots 0+3 merged (plausibly legitimate: both pass the foyer) at ~187 cm median. Overlap is part of the cause, not all. Synthetic foyer's flat blue tile grid is a near-perfect repeating pattern — likely harsher than Marina's foyer, unproven.

## Where this leaves the plan (end of Oct 12)
- Trustworthy so far on synthetic: feature-rich rooms (COLMAP kitchen ~1 cm), VGGT on the breakfast/dining run (~6 cm). Long straight walks past repeating surfaces: unreliable with every method tried.
- Next, cheap: **agreement gate** — on synthetic, does COLMAP–VGGT agreement predict correctness? If yes, it's the acceptance test for Marina footage (no truth there).
- Likely main path for hard rooms: **analysis-by-synthesis** — render the house_spec blockout in Unity from estimated cameras and optimise room dimensions to align structural lines (corners, door frames, trim) across many Marina frames. Immune to wallpaper repetition; verified on the synthetic harness the same way.

## Experiment 0c — agreement gate (Oct 12): PASSES on synthetic
`tools/sfm/agreement.py`: shots split into 10-frame windows (~3.5 m); per window and method pair, Sim3 one method onto the other (disagreement) and each onto truth (error), as median residual / window path length.

| Gate | Accepted | Truly within gate | Worst true error accepted | Good windows rejected |
|---|---|---|---|---|
| 5%, colmap+vggt+aliked | 19/38 | 17 | 5.8% | 0 |
| 2%, colmap+vggt+aliked | 13/38 | 11 | 3.3% | 2 |
| 2%, colmap+vggt only | 3/12 | 3 | 2.0% | 0 |
Spearman(disagreement, worse true error) 0.93–0.96. Caveats: synthetic only; overlapping samples; COLMAP+VGGT overlap in only 12 windows; ALIKED shares COLMAP's mapper (not independent).

Insight: methods are usually right LOCALLY; the day's failures were GLOBAL (along-path drift, wrong merges).

### Strategy (supersedes chaining one global SfM model)
1. Local reconstruction per room-scale window with ≥2 independent methods (COLMAP SIFT, VGGT; others as available). Accept only where they agree (gate 2%, tighten after more synthetic evidence); attach the measured error bar.
2. Global assembly by constraints, not SfM chaining: doorways/shared walls between accepted pieces, house envelope, stair geometry; analysis-by-synthesis (align corners/door frames/trim of the house_spec blockout to Marina frames) for placement and for rooms with no agreement.
3. Rooms with no agreeing pair are flagged, never silently trusted.
Next: grow synthetic evidence for the gate (more routes/rooms, independent pairs), then first real run: Buzz room + hall with COLMAP and VGGT, gated.

## First gated run on real footage — Buzz room + upper hall (Oct 12)
Part 2 9:00–10:40 at 4 fps; shot_buzz frames 1–89, shot_hall 135–400 (90–134 excluded: title fade/card/film, padded). COLMAP SIFT per-shot pinhole (`sfm-work/real-colmap`) vs VGGT-1B 40-frame chunks (`sfm-work/real-vggt`); `tools/sfm/agreement.py 2 ...` (truth-free mode).
- 26/34 windows agree within 2%.
- Buzz room: every window agrees (0.6–1.9%).
- Hall frames ~206–265 disagree (3–22%) — the same flat-green-wall stretch where the Oct 12 spike split into pieces. Gate flagged the known weak spot unprompted.
- Hall frames ~265–400 agree (0.2–0.9%).
Next: fit Buzz walls from agreed-window points (COLMAP sparse + VGGT depth as cross-check), report Buzz width/depth with spread, and confront the 0.77–0.80 (spike) vs 0.60 (overhead survey) contradiction.

## Buzz room proportions — two independent methods agree (Oct 12)
`tools/sfm/room_dims.py` (Manhattan axes; each wall = outermost strong density peak beyond the camera path before a wide empty gap; mid-height band 15–85%). Diagnostic: `sfm-work/buzz-dims.png`.
- COLMAP SIFT (real-colmap model 3, shot_buzz points): short/long = **0.792**
- VGGT-1B, all Buzz frames in one pass (45 frames, every 2nd): **0.802**
- Agreement ~1.3%. Consistent with the spike's 0.77–0.80; contradicts the Sept 11 overhead survey (4.21×6.97 m = 0.60) → that survey's depth stretched ~30%, the likely root of the Buzz confusion and possibly of "floors don't stack".
Lessons: per-chunk VGGT on a camera pan sees only part of a room — run a room in one pass; first-peak wall picking grabs furniture fronts — use outermost peak before a gap.
Open: metric scale (door height / Marina's stated areas / stair rise); parameter-sensitivity spread; film-set check.

## Buzz room metric scale from door height (Oct 12) — provisional
`tools/sfm/door_scale.py` on the one-pass VGGT model (`real-vggt-buzzall`): door top/floor edges snapped to intensity edges in frames 38, 41, 44 (overlay `sfm-work/buzz-door-measure.jpg`, visually confirmed); 3D separation along up.
- Door height 0.997 / 0.997 / 1.011 units → median 0.9974, spread 1.4%.
- Buzz sides (room_dims VGGT 1.711 × 2.133 units) at assumed door height:
  | Door | Buzz room |
  |---|---|
  | 78 in | 3.40 × 4.24 m |
  | **80 in** | **3.49 × 4.35 m** |
  | 84 in | 3.66 × 4.56 m |
- Compare: Sept 18 walkable candidate 3.65 × 4.27 m (estimated); candidate B 3.90 × 4.80; overhead survey 4.21 × 6.97 (rejected).
- FAILED: ceiling height from point-histogram peaks (0.86 m — picked furniture planes). Discarded; measure the ceiling–wall junction directly instead.
- INCONCLUSIVE: door height/width shape check (2.05–2.32 vs 2.50 standard) — width edges caught casing vs leaf inconsistently.
Door height is an assumption (source weight 1/5). Next anchors to cross-check scale: Marina's stated floor areas (needs the upstairs floor assembled), other doors in other rooms (consistency), stair rise/going, bed length.

### Scale policy (Oct 12, user decision) + hall door
Scale each room from its own door at 80 in (78–84 in carried as the error bar). Door-model reuse is NOT a gate — it can't tell 80 from 84 in anyway; doors agreeing across rooms is a free sanity check. The 78/80/84 question is settled only by an independent anchor (Marina's stated areas).
- Hall (one-pass VGGT `real-vggt-hall`, frames 135–222 every 2nd): attic door 0.3714 / 0.3730 / 0.3738 units (frames 7, 10, 13; overlay `sfm-work/hall-door-measure.jpg`) → 0.373, spread 0.7% → 5.45 m/unit at 80 in.
Per-room recipe: (1) COLMAP + VGGT, accept agreed windows; (2) room_dims shape; (3) door_scale at 80 in.
Next: independent check of the 80 in assumption against Marina's stated areas — attic (476 ft², single room, orthographic overhead at Part 2 14:00) is the cleanest; kitchen 477 ft² has a zone-boundary definition problem.

### Attic area check — not possible as designed (Oct 12)
Part 2 775–935 s extracted (`sfm-work/attic`): film inserts + overhead plan, CG walk starts at frame ~304 mid-way up the attic stair. No door is ever visible in the attic footage, so door scale can't be applied; scaling from stair risers would test a riser assumption, not the door. Decision: carry 78–84 in (±4%) as the scale error bar; run the decisive independent check against Marina's 1,900 ft² upstairs total once the upstairs rooms are measured and assembled. Kitchen 477 ft² remains a secondary check (zone boundary ambiguous — compute for each plausible boundary).

## Per-room recipe in practice (Oct 12): tools/sfm/room.py
prepare / solve / analyze / scale. Rooms prepared: parents (CG 338–653), kevin (CG 192–352), hallbath (CG ~26–180). Girls' rooms: NO interior CG footage (only hall views, film, interviews) → authored; Marina's plan labels the partial girls' room 7' 6" deep (angled overhead: design constraint, not a scale anchor). Production-photo collages are interleaved with CG (parents 288–335, kevin 113–129) — exclude.
- Parents' suite: COLMAP+VGGT agree in 5/6 windows.
- agreement.py fix: windows now cut over frames both methods reconstructed (VGGT is subsampled). Synthetic re-check at 2%: 11/11 accepted truly within 2%, Spearman 0.95.
- room_dims.py: @frame-range filter (camera walks pass through several rooms).
- FINDING: one-box-per-room fitting fails on real rooms — bedroom frames see through the doorway into the bath (wall picked inside the bath), rooms have stepped corners/closets, the bath is L-shaped. Replace with plan extraction: top-down wall-density map per suite → Manhattan-aligned wall segments → polygons; this is also the form the reconciler needs.
- plan_extract.py (Oct 12): VGGT top-down density is effectively a floor plan (parents' suite: bedroom with angled corner, bath, crisp walls — `sfm-work/rooms/parents/plan-*.png`). Wall detection by mid-height (30–70%) point density; full-height span failed (floor+ceiling in every cell). Density falls with distance, so the threshold matters: WALL_FRAC 0.05–0.10 finds most walls; still misses the far bedroom wall in parts and keeps some furniture (bed rail/wardrobe). Output = candidate segments; a review pass (confirm walls, drop furniture, close gaps) is required before the reconciler.
- Parents' suite reviewed (Oct 13): `measurements/rooms/parents.json`, overlay via `tools/sfm/plan_review.py parents`. Scale from the closed hall door, frames 402/407/413 (0.586 units, 2.8% spread → 3.465 m/unit at 80 in). Bedroom 23.7 m² (255 ft²), bath 8.2 m² (89 ft²); both doorways measure 0.76 m (30 in), an independent sanity check on scale. Review caught a false wall: the density's "angled corner" is the folding screen (square corner per frames + Marina's overhead). Overhead confirms the bath's L-shape, the bath/bedroom width ratio (0.50), and that the bedroom's notch is the neighbouring bedroom. Open: whether the bath reaches the hall-side wall (overhead ambiguous).
- Kevin's room reviewed (Oct 13): `measurements/rooms/kevin.json`. Plain rectangle 4.57 × 3.60 m (16.5 m², 177 ft²) at 80 in; scale from both closed doors, frames 279/292/325, 0.7% spread (one pick dropped: edge snapped to hanging boxing gloves, caught on the overlay). Shape agrees COLMAP/VGGT 0.814/0.802 although the gate passed only 3/6 windows (late pans over plain dotted walls). Doors 0.83 m (may include casing) and 0.77 m. Which is hall vs closet: decide when the hall is placed. VGGT frame 59 (f_00352) already shows the next dissolve; trim the range to ≤348 on any re-solve.
- Hall bath NOT accepted (Oct 13): gate 3/6, and the disagreeing windows cover the door/tub stretch. The door bottom is never in frame (frames 84-122), so door-height scale is unavailable. Three scale estimates disagree: tub length as 60 in → 2.12 m/unit; door slab width as 30 in → 2.31; door top over floor level → ~2.66 (door-top heights scatter 0.27-0.35 units across frames 24-29). This scatter means the reconstruction itself is inconsistent across frames, not just badly scaled. Next: re-solve in two overlapping halves (window/sink pan; door/tub pan) and check each half against the tub's 2:1 ratio before trusting the top-down plan. Last kept frame (180) carries the "Buzz's Room" caption: trim to ≤176.
- Hall bath halves (Oct 13): worse, not better. Half A (frames 26-92) gate 2/6, half B (80-176) gate 1/6 and COLMAP can't close the room. Likely cause: in a ~2.5 m room the camera mostly pans in place (little baseline), which neither method handles. Decision: the hall bath joins the girls' rooms as authored-with-constraints. Layout and fixture order come from the frames; outline from Marina's overhead (girls/all/images/f_00041.jpg, centre-right room with the tub); size checked by the tub (60 × 30 in, measured 2.1:1 in VGGT) and 30 in door; final fit by the reconciler against the hall and neighbours.
- Upper hall (Oct 13): end-to-end reconstruction fails. Whole walk 135-376 in one VGGT pass: smeared fan, gate 2/6. Four overlapping clips (`sfm-work/rooms/hall-s1..s4`, chained with new `tools/sfm/stitch.py`, similarity fit on shared camera centres with residual reported): clips 135-205 (6/6) and 320-376 (5/5) pass; the middle (195-330: flat green walls, stair landing) fails (2/5, 2/6) and its link is degenerate (residual 8.9%, scale 59x). The good clips show only local corridor pieces and rooms seen through doorways. Decision: the hall is authored by the reconciler as the space between measured rooms, using the caption-derived door order (`measurements/rooms/hall.json`), Marina's overhead, and the one local width measured (1.58 m at the stair-top leg).
- Overhead calibration test (Oct 13). Marina's angled upstairs overhead (girls/all/images/f_00041.jpg), wall-top inner corners vs the measured parents' plan. Results:
  - Bedroom-only affine fit: 1-8 cm residuals, after removing a false "wall" that was the armoire front.
  - Bath width agrees (2.57 vs 2.63 m). Bath length disagrees: the overhead gives 3.59 m vs SfM 3.26, with the tub end ~1 m further. SfM was sparse there, so the overhead is favoured.
  - Kevin's room read through the bedroom calibration: 4.69 × 3.89 m vs SfM (own doors) 4.57 × 3.60. Width +2.6%, depth +8%.
  - The depth error grows down the image: an oblique view calibrated on one corner extrapolates poorly. A full perspective fit with control points spread over the image is the next step.
- NEW PRIMARY SOURCE (Oct 13): the same segment (girls/all frames 5-33) shows production designer John Muto's physical model of the upstairs SET, with labels: Master bathroom, Parent's room, Sister's room, Kevin & brother's room, Linen closet, Upstairs bathroom, Buzz's room. It is film-set topology from the set's designer, ranked above Marina for adjacency. Buzz's room is on this floor.

## Upstairs from the calibrated overhead (Oct 13) — passes
Method: `tools/sfm/overhead_fit.py measurements/overhead/upstairs.json` fits one homography to Marina's angled upstairs overhead (f_00041). It uses wall-top inner corners, all in one plane, of three SfM-measured rooms, each scaled from its own doors at 80 in: parents fixed, Kevin and Buzz with free offsets.
- Fit 5.2 cm median; leave-one-corner-out 9.1 cm median (max 17.8).
- Independent checks: Marina's 7'6" label → 2.27 m (−0.6%); parents' bath width 2.61 vs SfM 2.63 (−0.7%).
- Before Buzz was added as a control, Buzz predicted 5% large in both directions while its shape agreed to 1.8%. With Buzz included, one map fits all three rooms at 80 in, so that 5% was drift from calibrating on the top half only, not a scale conflict between rooms.
- Cross-source agreement: the parents' hall door, measured by SfM, lands exactly on the hall end in the overhead. Kevin's hall door and closet door fit the hall end and closets once Kevin's room is flipped vertically.

Trace: `measurements/overhead/upstairs-trace.json` → `tools/sfm/overhead_plan.py` → `upstairs-trace.plan.json/.png`. 14 spaces (6 rooms, 3 hall pieces, 3 closets, hall bath, stair opening).
- Net floor 118 m² (1,275 ft²).
- Gross outline 1,928 ft² at 80 in vs Marina's stated 1,900 (+1.5%). At 78 in it is 1,832 (−3.6%); at 84 in, 2,125 (+12%, ruled out).
- This is the decisive independent check of the door assumption: 80 in is supported.
- Caveat: the outline was read roughly (±10 px). The stair-opening stretch of the left edge is hidden and assumed straight.

Also:
- The uncaptioned Michael Jordan room in the hall walk is Buzz's room.
- The hall's arches and door headers hide doorways at wall-top level, so connections come from the captions and SfM doors.
- Open: the grey strip above girls_room_a (closet or shelf); the left edge of the stair opening; and which girls' room is which.
- Attic stair located (Oct 13). The hall walk's first view (frames 135-165) looks down the corridor past the stair rail to a door at the end of the south leg. That door matches the film's attic-door shot (Part 2 attic segment f17: green walls, sconce, table with red candles, picture). Behind it, the overhead shows a black well 1.36 × 2.66 m open to below (`attic_stair` in the trace). No end wall is drawn because the overhead cuts at wall-top height. The poster also places the attic stair beside Buzz's room. Confirm by render-and-compare from the CG stair frames (attic ~304-320). This also explains the black notch in the outline, which is not an exterior recess.
- Area check redone with the attic stairwell inside the outline: see the gross line printed by overhead_plan.py. 78 and 80 in now bracket Marina's 1,900 ft² and both lie within the outline-reading error (a few %). 84 in stays ruled out. Door height is 78-80 in; keep 80 as nominal.
- Hall end and ceilings (Oct 13). The gated hall clip (hall-s1, 6/6; attic door 0.3714 units, 0.9% spread → 5.47 m/unit) shows the corridor ending at a cross wall: Buzz's doorway, then the arch into a 2.03 m attic leg (overhead: 1.97 m). Just before it, an end bay widens east by 1.18 m over 1.92 m, and the hall bath door (0.70 m) is in the bay's east wall. That replaces the overhead's misread closet boxes in that corner; the linen closet is now the shallow space behind the bay's north wall (prop door). Ceilings were measured as wall height relative to door height on the same wall: parents 2.42 m and Kevin 2.30-2.33 m to the crown's lower edge; attic leg 2.29 m to the ceiling. Nominal 2.40 m (parents 2.50) replaces the assumed 2.74 m. The height-histogram method (2.22-2.46) is biased by camera tilt; don't use it.

## Matched-camera render-and-compare, first run (Oct 13)
`tools/house/match_cameras.py poses hall-s1 ...` maps the clip's VGGT camera poses into Unity: clip plan frame → registration (translation fitted on the arch and attic door) → spec → Unity, with world z = −spec z. `SpecGreybox.RenderMatched` renders the grey-box from those poses. `match_cameras.py compare` measures the chamfer distance from each grey-box edge pixel to the nearest strong edge in Marina's frame, at 960×540.
- Looking down the hall (f135/148/160): median 6.0 / 7.3 / 11.4 px. The attic door, arch, hall walls and rail land on Marina's edges, roughly 2–4 cm at those depths.
- Hall end (f178/192/205): median 22 / 17 / 18 px. Causes:
  - the camera is about 0.5 m from the doorways, so cm-level errors become tens of px
  - Marina's door casings aren't modelled in the grey-box
  - the bath and Buzz doorways look 5–10 cm off
  - Buzz's room corner matches
- Marina's camera eye height is 1.0–1.2 m (Kevin height).
- Lessons:
  - Grey-box renders need an absolute edge-strength threshold; a percentile cut picks up the ceiling light falloff.
  - The registration is translation-only (0.1 m residual), so it limits accuracy. Next: fit the registration from several features (rotation + translation + scale) and add door casings, then turn per-view thresholds into verify-plan checkpoints.
- Render-and-compare v2 (Oct 13):
  - **Registration.** The hall clip's registration is now a 2D similarity fitted only on wall lines that both the clip and the overhead show (`tools/house/register_clip.py`): rotation −0.14°, scale 1.0085, anchors within 0.2–5 cm. The scale agrees to 0.85%: an independent check that the door-based clip scale and the overhead calibration match. The old translation-only fit was 17.5 cm out along the hall.
  - **Clip-derived geometry is generated, not hand-copied.** The script writes the end bay, the bath/Buzz/attic doors and the checkpoint points from clip coordinates. The density check moved the bay's north wall to clip 3.05 (plan ~9.36); the earlier 2.4 was a plot misreading.
  - **Comparison renders** use a camera headlight with room lights off, because ceiling hotspots made false edges.
  - **Door casings** (7 cm, 2 cm proud) are added to every real door.
  - **Matched views per clip** (median px at 960×540): hall 6 / 3.6 / 5.4 / 16 / 18 / 8; parents 10 / 8.5 / 19 / 10 / 19 / 7.6; Kevin 7.1 / 31 / 7.3 / 9 / 9 / 6.4. Kevin's door views land on Marina's casings.
  - **Explained outliers:**
    - parents f402: the armoire hides the notch corner.
    - parents f498: tub/shower close-up, not modelled.
    - hall f178/f192: the bath door is under 1 m away and its open leaf isn't modelled.
  - **Unexplained, follow up:** Kevin f225, window-wall corner about 60 px (~25 cm) left of real. Every other Kevin view agrees, so check that frame's pose (VGGT chunk) before touching the plan.
- Verification rebuilt around 3D, not images (Oct 13):
  - **Image edge score dropped as a gate.** Sensitivity test: moving the camera 20 cm did not reliably worsen the chamfer score, and two views scored better. Two other variants (an inlier fraction, and orientation-aware snapping) scored mismatched pairs nearly as well as matched ones. Overlays are kept for eyes only.
  - **New gate, `tools/house/check_walls.py`.** Per-wall offset of a gated clip's wall-height points, using only points from frames whose camera is inside that space, against the spec walls.
  - **Findings and fixes:**
    - The hall reaches the stair rail. The reconciler now treats rails as 6 cm on the stairwell edge, and the hall takes the gap: +19 → +1 cm.
    - The parents' bath was traced 20 cm too far west. Far wall −21 and bedroom-side wall +19, so same width; now within ±3 cm, and the shared wall is back to ~15 cm (SfM 17).
    - Kevin's registration anchor for the south wall came from a `plan_extract` line 8 cm off the surface. Re-fitted on surface density peaks: rotation 90.02°, scale 1.0092; all walls within ±3 cm; room depth 3.60 m matches its door-scaled measurement.
  - **Result:** hall, parents and Kevin clips have every long wall within ±7 cm, and verify-plan passes 12/12.
  - **Supporting changes:** matched renders use per-frame focal, PnP poses from each frame's point map (camera head vs point map within 2 cm/0.7° except the bath close-up), and surface-ID colouring.
  - **New option:** `reconcile.py --measured` / `-variant measured` builds the house exactly as measured, so faithfulness and the gameplay wall-thinning are judged separately.
- Test the tests (Oct 13), prompted by the image score failing its sensitivity test:
  - `tools/house/test_checks.py` injects 0/5/10/20 cm wall errors into three rooms. `check_walls.py` reads them back exactly (moved 0/4–6/10/20 cm), flags every 10 and 20 cm case, and leaves untouched walls unflagged: PASS. The detection limit is 10 cm; 5 cm reads correctly but sits under the 8 cm threshold.
  - The Unity walk test with 0.45 and 0.50 m doors (`-variant inject_door`) gives both BLOCKED and the other 9 ok.
  - Checkpoints are now labelled independent or consistency. Only 3 of 12 are independent of the data the plan was built from (Marina's 7′6″, the parents' bath width, the overhead's open door leaf). The 3D wall checks on hall-s1/parents/Kevin are consistency checks (registrations fitted on those walls).
  - Independent evidence next: clips not used for the plan (hall-s4, Buzz), or held-out walls.
- Independent evidence (Oct 13):
  - **Leave-one-out registration** (`register_clip.py --loo --rigid`): hall-s1 held-out walls median 5 cm, max 10.5 cm (the attic leg's west wall: the clip sees the leg ~10 cm wider than the overhead). Kevin median 3.5 cm, max 6 cm (width 4.46 vs 4.52).
  - **Far-end clip hall-s4** (frames 320-376, gate 5/5), never used to build anything:
    - Scale 3.236 m/unit from the parents' doorway head to the floor (1.2% spread).
    - Rigid registration on the passage walls and the parents'-door wall only.
    - Held-out results: Kevin's hall door centre within 7 cm of the spec (that door came from Kevin's own clip); the parents' hall door within 7 cm; the passage is 1.22 m wide against the overhead's 1.07 (walls too thick there; the thinned build is 1.23).
    - The girls' room A door, a topology guess, was 28 cm off and is now measured (6.01-6.79).
    - My first reading of this clip mistook the start of the passage for the parents'-door wall and produced a phantom 1 m door conflict. Looking at the top-down with the camera path resolved it. Lesson: plot the clip before interpreting gaps.
  - **Door checkpoints** now compare door centres along the wall (before: any point inside the opening passed, so ~38 cm went unseen). Injected 10/20 cm shifts FAIL. The reconciler's silent slide (≤15 cm) can mask door errors; noted in the skill.
  - Checkpoints: 15/15 pass, 6 independent.

## Main staircase, flight 1 measured (Oct 13)
Clips from Part 1 at 1080p (the 640x360 original is deleted; use the `copy.mp4`): A = foyer pan 29-62 (gate 3/3), B = climb 116-187 (gate 6/6; the 640p solve failed its landing window at 2.6%, and 1080p fixed it). Record: `measurements/rooms/stairs.json`.
- **13 risers** foyer floor to landing: the image count fits an equal-spacing projective model (rms 3 px; 14 rejected), and clip B's 3D gives 12.95 rises.
- **Rise 0.169 m** (0.163-0.173) from clip A riser tops, door-scaled at 80 in.
- **Pitch 35.0 deg** (34.4-35.5) by vanishing points (`tools/sfm/stair_pitch.py`, `--selftest`: synthetic 30/35/40 deg read within 0.1 deg; a one-line image is rejected). **Going 0.241 m.** Tread band 1.12 m.
- **The 3D point clouds get the pitch wrong** (24-27 deg): looking along the flight, VGGT stretches depth by ~1.35 relative to height, and tread/riser normals are 75-80 deg apart. Use 3D only for vertical and lateral sizes on stairs.
- **Door edge pixels can lie.** The foyer door is recessed under an arch, so `door_scale.py`'s top-edge pixel took the arch's depth (14% short). The new robust method (`stair_measure.door_height`: slab-interior quadratic fit, extrapolated to the edges) changes the upstairs doors by <1% (Kevin +0.8%, parents +0.6%), so the upstairs scale stands.
- **Layout from Marina's main-floor overhead (Part 1 f216):** a straight flight along the foyer's left wall, rising toward the rear, onto a full-width landing at the rear wall (picture and table, then the big window), with a balustrade facing the foyer. In the upstairs plan: the landing is at the west end of `main_stair_opening`, spanning its 2.83 m, and flight 1 runs along the south side.
- **Flight 2 (landing to the upper floor) is in neither video nor Marina's main-floor model**, so it is authored. The landing is at 2.20 m. The upper floor height (floor-to-floor) is not measured: the foyer ceiling meets the wall at the landing-balustrade line, 2.32 m.
- Caption check (user question): the big "Buzz's Room" chapter title fades in over the hall-bath clip's last frames (179-180). Only the rejected hallbath 26-180 solve included them, and nothing built uses it. The small hall label at f152-156 marks Buzz's doorway; `hall.json`'s note is corrected.

## Main staircase built (Oct 13)
- User decisions: 15 risers floor-to-floor; flight 2 = 2 risers off the full-width landing's north end, rising east onto a north-side gallery.
- Evidence for flight 2: a main-floor plan drawing (user-found), the film (walk along the landing past the rear window), and the climb clip (floor ~2 rises past the rail).
- I first read the film clip as a long flight 2. That was wrong: perspective made Kate look higher as she walked toward the camera, and the wainscot cap stays level.
- Reconciler: a pair of spaces can now share several walls (door `wall_axis` + `near`). New door kind `open` (stair head: no wall, no rail). Wall extents are recomputed after thinning.
  - The last fix removes the hidden door "slides". The parents' hall door now reads 15 cm from the far-end clip (was 7 cm only because the slide moved it), so the two hall clips disagree by ~15 cm on that door.
- Unity: stair boxes, a stair walk test for both bodies (20/20), and an injected missing step (8 legs blocked).
- check_walls: hall-s1 5 walls / kevin 4 walls, 0 flagged. Parents: a 0.63 m bath stub at -9 cm, identical at the previous commit (pre-existing).

## Independent rulers, steps 1-2 (Oct 15, evening; method page https://claude.ai/artifact/XXuuXaREgFsR35eZ8QWYpR)
- **Marina's camera height is fixed: h = 0.639 x door height, spread 2.5%** (`tools/house/rig_check.py`, labels `measurements/rig/labels.json`):
  single-view metrology (cross ratio of door foot/top, horizon, vertical VP), no SfM, no scale. 6 doors, 4 rooms, both videos
  (kitchen 916 basement door 0.637 / pantry 0.627; Kevin 376/378 same door 0.641/0.642; parents 194 0.642; hall 578 0.630). = 1.30 m at 80 in.
  Self-test: exact on synthetic frames, 1 px label noise 0.8%, injected 10% door flagged.
  - Lesson: the horizon from the vertical VP + assumed f is ill-conditioned for a near-level camera (V tens of thousands of px away;
    gave 1.13-1.26 m and a 5% same-door mismatch). Horizon from the VP of receding level edges (beams, crown, floor lines) is primary;
    overlays `sfm-work/rig/*-overlay.jpg` show the edges used.
  - The VGGT review-still poses (spec/captures/sheet-matched/poses.json) put the eye at 1.27-1.40 in door-scaled rooms but 1.09-1.19 in the
    hall (passage-width scale) and hall bath (overhead scale): a -12..-14% lead on those rooms' scale, NOT yet a finding (pose noise ~±5%).
  - Use: in any Marina frame, horizon + floor contact gives depth h*f/(v-vh), and floor width at one depth W = h*du/(v-vh) (f cancels).
    First try, hall 615 s end wall: 0.98 m between the casings' outer edges at 80 in (door opening ~0.76 m). Not yet matched to a plan
    element; don't act on it.
- **Brick ruler** (`tools/house/brick_ruler.py`, outputs sfm-work/brick/): kitchen-wing rear wall from film 4575 + 7068, common bond,
  stretcher/course 3.02 (modular, same-lens assumption). Sink window trim ~0.94 w x 0.88 h m (build 0.75 x 0.98: wider, shorter); window-door
  centre spacing 1.81-1.93 m vs build 1.88; back-door trim-top 1.98 m modular (6'4" opening) mildly favours a 2.75 in course (~3% open).
  Front facade not resolved (1830 piers too narrow, 3237 oblique).
- **Rig ruler, room by room (Oct 15, late)**:
  - `rig_check.py floor` (self-test: a 3.40 m width and a 2.00 m point pair recovered exactly under pitch/yaw) gives floor distances
    from one frame: horizon (auto, or hand `h_lines`) + camera height 0.639 x 80 in. Labels `measurements/rig/floor.json`.
    - hall 615 s, far passage between the side walls' bases at the end wall: **1.16 m** vs 1.22 (hall-s4, door-scaled) / 1.23 built: -5%.
    - dining 1123 s, French-door wall from its left corner to the near jamb that hides the right corner: **>= 4.52 m** vs 4.63 built: consistent.
    - den 1161 s, green wall between the window corner and the bookshelf corner: **3.65 m** vs the den's 3.71 m side (-1.6%). I first
      paired it with the 6.91 m wall; the number says it is the short side. Which wall is which in `still_pose.ROOMS["den"]` is unchecked.
    - Hall bath: no frame in 440-488 s shows two floor corners (camera level, floor at the frame edge). Not measured by this ruler.
  - **Rejected: scaling the SfM clips by her camera height** (`still_pose.py rig` -> `measurements/rig/rooms.json`). It agrees in the
    door-scaled rooms (parents -2.5%, Kevin -2.1%, Buzz +0.9%) and the living room (-0.3%), but says hall +17%, dining +23%, den +22%,
    hall bath +11%, and the pixels above contradict the hall and dining. VGGT's height-vs-width ratio is not stable enough (same lesson as
    the stair pitch). Kept as a record. The "-12..-14% lead" on the hall/hall bath from the posed stills is the same artefact: dropped.
  - Net: no room measured by pixels is off by more than the ruler's own spread (~±3% labels, 2.5% rig). All three read 2-5% UNDER the
    build; with n=3 that is not a finding, but a 78 in door would push them further under, so keep it in view.
- **Joint fit, synthetic rehearsal (Oct 15, late)** (`tools/house/joint_fit.py rehearse`, PASS, ~1.5 min): the back stair as 8 parameters
  (newel x, open-side z, going, rise, basement door jambs and head, ceiling) plus a camera per frame (yaw, pitch, position, f),
  robust soft-L1 on labelled pixels, fixed anchors (foyer doorway jambs, back-right corner, side window, hutch corner), Marina's
  camera height 0.639 x 80 in as a prior; Marina and film fitted as separate sets.
  - 6 Marina frames, 1.5 px labels, 30% occluded, one 30 px mislabel a frame: every parameter within 0.3 cm, error bars calibrated
    (median |z| 0.67), 120/120 mislabels flagged, 0 false; held-out frame 1.6 px; newel +15 cm -> 21 px on the held-out frame.
  - Canon split: film newel 40 cm from Marina's -> flagged in 5/5 trials and nothing else. **Lesson:** the Jacobian error bar alone
    is sometimes too optimistic (a film fit put the basement door 10 cm off at "3 sigma" with no mislabel on it: a mislabel elsewhere
    moved a camera). Error bars are now max(Jacobian, leave-one-frame-out).
  - Anchors each off N(0, 5 cm): house error median 1.2 cm, max 2.3. A nosing labelled one step out: 81 px residual, flagged.
  - Budget: 3+ frames at <= 2 px labels keep every parameter within ~1 cm (2 frames: up to 3.7 cm). The real error will be
    dominated by what the rehearsal cannot contain: the parametric shape being wrong (step count, newel offsets) and labelling
    the wrong physical feature. The held-out frame and the overlay are the checks for those.
- **Back-stair pilot, labelling started (Oct 15, late)**:
  - Marina 916 s: the flight's tread profiles (going ~65 px, rise ~44 px, ratio 0.68) and the basement door put the stair ~5.8 m
    from her camera (camera height 1.30 m, horizon ~503). The foyer doorway, IF 0.98 x 2.20 m, would be ~9.5 m away; on the stair's
    plane it would be only ~0.57 m wide with a ~1.85 m head. So either her doorway is smaller and lower, or it sits well behind the
    stair's plane (end of a passage?). Lead only, by hand arithmetic; the fit decides.
  - Model revised: the doorway's plane and head, the basement door's plane (916 shows it flush with the wall to the corner), and the
    newel and post heights (authored in the build) are now fitted. Anchors left: the side window and the doorway's x.
  - Rehearsal still PASS (13 parameters), but the budget is stricter: ~6 Marina frames at <= 2 px for 1-2 cm; 2 frames can diverge.
  - `joint_fit.py segs FRAME x0 y0 x1 y1`: numbered Hough segments for labelling by segment id/intersection. Hough misses most of
    Marina's soft CG edges (door jambs), so labels are read on refcam grids; snapping where edges are clean.
  - Frames chosen from the 908-944 s sheet: 915, 917 (frontal, flight + door), 921, 924 (hutch wall, foyer doorway, newel),
    927, 929 (newel at the doorway), 933, 935 (close stair, door, window); held out: one of 917/929.
- **Back-stair pilot, first real fit: underdetermined (Oct 15, night)** (`joint_fit.py points labels/backstair-marina.json`):
  - The 8-parameter model's layout is wrong for Marina's stair (overhead 812 s: straight flight in an enclosure with winders at the
    bottom and a short foot out into the room; 929 s: the tall post stands nearer the room than the short newel). So the pilot
    switched to a hybrid: free 3D points for the irregular parts, one parametric nosing line for the flight, per-frame nosing-count
    shift search. Self-test PASS (nosings 0.9 cm; every point within 2.7 sd; a common shift is the same as moving the flight one
    step, so positions are compared, not shift numbers).
  - On 3 hand-labelled frames (916, 933, 935): first a telephoto collapse (cameras 100 m away, f ~37,000) with only the side window
    anchored; with Marina's fixed f 1428 as a prior it converges to nonsense (going 6 cm, rise 3.6 cm, door heads 3-4 m off).
    Labels by eye on soft CG edges + 2-3 frames from one side of the room + one anchor do not pin the cameras.
  - **Conclusion:** the cameras must come from automatic tracking (hundreds of correspondences per frame), not from a dozen hand
    labels. Labels then only triangulate the named points. Next: COLMAP sequential on every frame of Marina's 905-945 s walk
    (1080p), scale and gravity from her fixed rig (height 0.639 door, f 1428), then triangulate the labelled stair points.
- **Back-stair pilot with tracked cameras (Oct 15, night)** (`joint_fit.py track sfm-work/rooms/backstair labels/backstair-marina.json`;
  COLMAP sequential on Marina 914-945 s at 5 fps: 123/155 frames, 0.51 px, f 1324):
  - Gravity from roll 0 (up is perpendicular to every camera's x axis; agrees with the camera-centre plane to 0.4 deg); scale from
    her camera height over the floor band: 0.2686 m/unit. Self-test (`track-selftest`) PASS.
  - Bugs found on the way: the model pick (by file count, not frames); the floor taken as the densest low band, which was the
    patterned chair seats (1,522 points over 5x5 units vs the dark tiles' 140 over 16x12): every height 55% too large. The floor is
    now the lowest band that stands out 2x and spreads as far as the camera travels.
  - f fixed at 1428 (the refcam foyer value) fits worse (0.81 px) and distorts the walk: the data want ~1324. Revisit the 1428 prior.
  - Hand labels by eye do not mark the same corner across frames (6-31 px). Labels are now: a tracked point id (`kp`), a floor
    contact (ray meets the floor plane, one frame), or a pixel (triangulated: fallback, not trusted).
  - **First numbers (916 s, snapped/floor labels):** basement door leaf x -1.28 .. -0.45 (0.84 m; build -1.43 .. -0.72, 0.71 m),
    0.22 m of wall between leaf and corner (build 0.075); flight nosings x +1.19/+0.88/+0.58 at h 1.10/1.27/1.50 (going ~0.30,
    rise ~0.20; build 0.262/0.188), their open side 0.31-0.37 m in front of the door's wall (build: same plane). Flight line
    extrapolates to the floor near x 2.9 (the by-eye newel read). Newel, posts, doorway: triangulated from eye labels, not yet
    trustworthy. LEAD only; one frame; needs the held-out frame and more tracked-point labels before any build change.
- **Back stair rebuilt from measurements (Oct 15, night; TRIAL)**: `changes/2026-10-15-back-stair-measured.json` (gate 0 FAIL incl. new R7).
  - Mistake on the way, logged: I called her stair "one straight flight" from the upper flight's nosing line extended to the floor;
    the foot is behind the table/chairs in every eye-level frame of 914-945 s and 1104-1116 s, and in 926-927 s a chair-back top was
    nearly read as the floor (caught by projecting the tracked newel point: its floor lies 170 px lower). The user: "marina doesn't
    have a straight flight, her includes the turned foot". Guard: change_gate.py R7 (layout claims list alternatives incl. the build;
    every deciding part seen directly in 2+ frames, never extrapolated) + memory layout-claims-need-direct-view.
  - Deciding view: Marina 1073.5/1074.5 s through the foyer doorway: newel at the corner of a doorway-end landing, balustrade across
    its doorway-side edge, foot toward the table. Built: landing x 1.48-2.64 at 0.60 m, 2-step foot, flight going 0.30 / rise 0.20,
    newel x 2.64, tall post x 1.48, wall post x 2.50, basement door x -1.284..-0.445 in a wall 0.30 m proud. Gates: walks 0 blocked,
    seams 0/0/0 (the door wall's return is one going deep so its faces meet the step edges), leaks 0, peek 0.
- **Back stair, second pass (Oct 15, night; TRIAL)**: winders. User walk of 3cfb02c: "honestly not great" (no gradual turn; a strip of
  wall where the balustrade should be; the wall around the foyer doorway odd). Now 2 straight steps + 3 winders around the tall post
  (933 s wedges, 812 s two diagonals), rise 0.183 (tracked nosings at risers 6-8), one raking handrail, spandrel only under the flight.
  SpecGreybox: `poly` prisms (wedge treads) and `rise_x`/`rise_z` tilted boxes (raking rails). Checked by matched Unity renders from her
  tracked cameras faded on her frames BEFORE handing over (spec/captures/views/backstair-fade).
  - Found by that check: her cameras at 924-935 s stand ~4.45 m from the stair wall; the build's breakfast area is 3.99 m deep there
    (the chute pocket's wall) -> her breakfast area is >= 0.75 m deeper. Lead; measure from a pass facing that wall.
  - Foyer doorway: the film size (0.98) leaves a ~0.1 m pier to the corner beside an open hole in the hutch wall; Marina's 0.70 m with
    a casing leaves ~0.25 m. Decision for the user.
- **Winders were invisible and not solid (Oct 15, night; user note 22:57 "now you're just deleting stairs")**: the prism meshes rendered
  inside-out and their convex colliders failed to cook, so bodies walked through them. Nothing caught it: the back stair had no walk
  path and the matched views hid the turn behind chairs. Fixed (double-sided render mesh, separate one-sided collider mesh) and now
  guarded: a back-stair walk path (floor onto winder 1; bandit + Kevin pass; the Player arrives within 5 cm but is flagged STALLED
  nudging winder 2's edge, open) and a ServiceStair render check (outward faces). The user's note view is a standing render
  (spec/captures/views/backstair-note.json). Adults' heads reach the 2.44 m ceiling from winder 2 (stair closed at the ceiling, D30).
- **Upstairs hall ceiling slit (user notes 16:54, 23:01, the second time)**: the rail band where the stair opening meets the hall kept a
  2.40-2.55 m wall strip above the rail's cut (inside the ceiling's thickness); Unity papered it, so its underside showed as an L of
  wallpaper in the ceiling. wall_graph now emits such strips as ceiling pieces ("band": true). Every walk note is now re-rendered from
  its own recorded position/yaw/pitch (`tools/house/note_views.py` -> views/notes/), and a fix counts only when that view is clean.
- **Light seeping along the kitchen's wall/ceiling joint (user note 23:06)**: geometry closed (walls to 2.588, slab flush); a low sun
  (21 deg, 100 klx) leaked through with HDRP's default normal bias. Fixed: sun normalBias 0.1, 4096 shadow map, every house renderer
  casts two-sided shadows. (A shadows-only lid over each ceiling, tried first, did not fix it; kept, harmless.) Checked from the note's
  own view at fixed exposure (an unfixed exposure blew the first check out).
- **Foyer-kitchen doorway**: Marina's 0.70 x 2.03 cased was too narrow in the walk (user); now the film's 0.98 x 2.20, slid +2.7 cm to
  x 3.07-4.05 and cased both faces (DEVIATIONS 39). Cased plain openings: `"cased": true` in ground-doors.json flows to Unity trim.
