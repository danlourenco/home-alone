# Stage 1 — dimensional baseline

**Source weighting added:** [Source weights, provenance and claim confidence](SOURCE_WEIGHTS.md) governs interpretation of this baseline. The plan publisher identifies the dimensioned pair as Eric's visitor reconstruction of the real house. That resolves the earlier unknown attribution below, but does not verify the dimensions as film-set measurements. The measured differences are comparison results, not prescribed corrections.

September 13, 2026. This is the current dimensional baseline for `Assets/Scenes/IntactHouseReference.unity`, using the native-scale HOME_ALONE_FINAL base. It replaces historical generated-house dimensions as the working description. **Stage 1 measurement and discrepancy inventory is complete; film/set dimensional accuracy is not certified.** No scene geometry, camera, lighting or furniture was changed in this pass.

## Source hierarchy and limits

1. Film views establish recognizable relationships; Marina's reconstruction helps interpret them. Neither is automatically a dimensional survey.
2. The user-supplied dimensioned first/second-floor screenshots supply comparison dimensions. Source authorship, survey method and whether they describe the film set or real property are not established here. An explicit dimension is recorded as a plan claim, not film truth.
3. The illustrated PDF supplies an additional flat layout comparison but no scale/dimensions. Independence from other reconstructions is unknown.
4. Unity measurements describe our actual adopted model. A successful walk does not validate scale.

Archived inputs: `dimensioned-first-floor.png` (Desktop 8.36.10 PM), `dimensioned-second-floor.png` (8.36.31 PM), and `illustrated-first-floor.pdf` (Downloads Home+Alone+-+11x17+-+PDF+Print+File.pdf). Originals preserved. Use readable explicit labels only; do not transcribe blurred small labels as exact dimensions.

## Width comparison

Feet convert exactly at 0.3048 m/ft. Positive difference means the model exceeds the supplied plan claim, **not a measured error against the movie**.

| Space | Readable plan claim | Model wall-face width | Difference from plan | Confidence / boundary caveat |
|---|---:|---:|---:|---|
| Living | 15 ft = 4.572 m | 4.938 m (16.20 ft) | +0.366 m / +8.0% | Consistent at Z3,5,6; wall faces X−6.095..−1.157 |
| Dining | 15 ft = 4.572 m | 4.938 m (16.20 ft) | +0.366 m / +8.0% | Upper wall faces X4.921..9.859; projecting lower finish gives 4.891 m, or +7.0% |
| West family wing | 12 ft = 3.6576 m | 4.748 m (15.58 ft) | +1.090 m / +29.8% | Faces X−11.033..−6.285 at Z5,6; window glazing is farther out and excluded |
| East sunroom/greenhouse wing | 12 ft = 3.6576 m | 4.938 m (16.20 ft) | +1.280 m / +35.0% | Faces X9.859..14.797 at Y2.8,Z5; lower surface interval 4.962 m. One-sided partition requires backface queries |
| Central foyer | Small text not reliably transcribed | 5.650 m lower finish / 5.698 m upper faces | No defensible absolute percentage | Plan visibly places foyer narrower than living/dining; model foyer is about 14–15% wider than those rooms. This relative-width conflict does not depend on guessing the blurred foyer dimension |

These differences exceed the measured trim/reveal offsets. A living-room-based global factor of approximately **0.926** would still leave the west wing about **20%** and east wing **25%** wider than the plan claims. It would also reduce every ceiling height, stair riser and unrelated room. **Do not apply a global scale correction.**

## Main stairs and vertical baseline

| Item | Current model | Evidence/status |
|---|---:|---|
| Ground floor | Y≈1.31 m | Existing and current live floor samples |
| Rear stair landing | Y≈4.452 m | Live tread/landing scan |
| Upper floor | Y≈5.215 m | Earlier live room samples |
| Ground-to-upper separation | ≈3.90 m | Model level difference; no verified plan/film height target |
| Main-flight rise | ≈3.142 m | Ground to rear landing |
| Main flight | 16 rises of ≈0.196 m | Live scan detects successive elevations 1.506…4.452 |
| Main-flight going | ≈0.261 m | Transition scan at 0.02 m Z intervals; rounded location uncertainty ±0.02 m |
| First rise / landing start | Z≈4.16 / Z≈8.08 | Same scan at X0 |
| Tread lateral interval at Z5 | X≈−0.94..1.16, ≈2.10 m | Downward sample every 0.01 m; tread surface width, not guaranteed handrail clear width |
| Landing-to-upper difference | ≈0.76 m | Existing levels; full return flight traversable |
| Front crosswalk rear floor edge | Z4.670 at X0 | Prior bisection measurement |
| Crosswalk projected depth | ≈2.96 m from closet face Z1.71 | Not an unobstructed clearance throughout the hall |
| Initial-step overhead clearance | ≈3.41 m at Z4.25; ≈3.02 m at Z4.50 | Prior live samples; ceiling correctly extends over first steps |

Room heights retained from the [structure audit](../structure-audit/README.md): living/dining and sampled upstairs rooms ≈3.14 m; foyer ≈3.61 m; breakfast/kitchen ≈3.34 m. Basement sampled overhead clearances ≈2.85–3.14 m remain deferred. No supplied plan establishes these vertical dimensions.

## How the measurements were checked

Unity Physics raycasts, metres, active adopted scene; triggers ignored. Wall widths sampled in both directions at Y1.55 and Y2.8, and Z3,5,6 where useful. `Physics.queriesHitBackfaces` temporarily enabled in a try/finally because some imported partitions are single-sided. The previous value was restored.

Rejected measurements included window glazing (about 0.22 m outside the relevant interior wall face), rays through doorway openings into a neighbouring room, and the one-sided east-wing partition missed when backface queries were off. Lower finish versus upper wall offsets are reported explicitly. Results are point samples of adopted collision geometry, not room-volume reconstructions.

Prior stage checks remain evidence for connectivity: main stairs and important upstairs room routes pass; a continuous 19-checkpoint downstairs circuit passes through both dining-breakfast openings and the rear foyer return. No geometry has changed since those checks, so they were not unnecessarily repeated here.

## Stage 2 discrepancy punch list

| ID | Priority | Discrepancy / uncertainty | Next action and completion condition |
|---|---|---|---|
| D01 | High | Foyer is wider than living/dining in the model; plan shows the opposite relationship | Compare film camera landmarks with a local foyer/stair-width candidate before touching the adopted scene. Accept only a candidate preserving stair circulation, upper gallery and recognizable views |
| D02 | Medium | Living/dining are 0.32–0.37 m wider than the stated 15 ft | Determine whether plan dimensions are applicable to intended film interiors. Test alongside D01, not by shrinking furniture independently |
| D03 | Lower than main rooms | Side wings exceed stated 12 ft by about 1.09/1.28 m | Keep current wings until core dimensions settle; any candidate narrowing must account for upstairs rooms and facade consequences |
| D04 | High, evidence pending | Stair tread width ≈2.10 m and storey separation ≈3.90 m have no verified film targets | Calibrate stair/door/window relationships from film; do not infer stair width from an assumed standard doorway or globally shrink all dimensions |
| D05 | High, local | Buzz front and side window widths/pane patterns differ; replacement sill heights differ only ~2 mm | Reconcile interior openings, pane pattern and trim together against room reference; dimensions were inherited from exterior model, not room-validated |
| D06 | Medium, local | Buzz side passage 0.58 m; mattress length is perpendicular to bottleneck | Check bed width/post projection, dresser depth and placement against references; shortening mattress alone does not widen the side gap |
| D07 | Medium, local | Ensuite uses oval tub + separate tray instead of integrated reference fixture | Rebuild/reference-fit fixture outline before concluding shell is too small |

## Accepted working decisions

- Freeze existing native-scale geometry as the baseline while candidates are evaluated; it is not dimensionally signed off.
- No global scaling. Important film rooms and connections take precedence over an unverified printed plan.
- Breakfast stair need not connect upstairs. Do not create an arrival through the parents' suite.
- Basement dimensional fidelity and side-wing/exterior redesign remain deferred. Required safe traversal is still mandatory.
- Lighting/decorative production stays behind structural decisions, except specifically requested fixes such as Buzz's completed daytime exposure correction.

Stage 1 deliverables: archived input set, model/plan width comparison, stair/height baseline, and ordered discrepancy ledger. Stage 2 starts with D01/D04: the foyer/stair relationship, evaluated as a local candidate rather than an irreversible remodel.
