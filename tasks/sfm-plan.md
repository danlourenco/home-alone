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
