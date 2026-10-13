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

- **0a. Ask Marina** (user decision) for dimensions / plan export / model file.
- **0b. Synthetic truth test:** scripted Unity fly-through of the existing GLB (known metres) with per-shot and mid-shot FOV changes, title cards, captions, a dissolve, YouTube-like encode → unchanged pipeline → score room ratios and wall positions. Produces the real tolerances every later gate uses.
- **0c. Fix the spike clip:** pinhole intrinsics, per-shot cameras, caption masks, ±1 s padded exclusions, dissolve detection, dedupe; loop-closure/hierarchical mapper. Gate: the 100 s clip merges into one model.
- **0d. Resolve Buzz 0.77 vs 0.60:** wall-only points, intrinsics spread, cross-tour pass if Buzz appears in Part 1. Gate: discrepancy explained.
- **Gates from here on are independent:** cross-tour whole-pass holdout (solve Part 1, verify Part 2 via `image_registrator`), structural-line scoring, a +10%-depth negative control that must fail, uncertainty = max(cross-pass, intrinsics, scale-definition, synthetic-truth error).
- **Decisions needed from user:** (a) Marina governs geometry; film governs which named items? (b) floor stitching is authored, with options presented. Deviation ledger has two sections: Marina-internal inconsistencies, film vs Marina.
- MASt3R only when a room fails for lack of wall points. Minimal generator only after 0b–0d pass on one floor.
