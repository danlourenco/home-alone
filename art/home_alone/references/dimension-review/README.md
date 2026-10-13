# Room dimension review — September 13, 2026

This review measures the adopted Unity geometry and compares visible relationships against the archived Marina tour. It does not establish surveyed film-set room dimensions. The original GLB and room boundaries were not changed.

| Item | Current model measurement | Meaning |
|---|---:|---|
| Buzz room interior envelope | about 4.94 × 4.18 m | Native GLB shell, not film dimensions |
| Buzz bed including posts | 2.58 × 1.48 m | World horizontal bounds |
| Buzz mattress | 2.30 × 1.22 m | Check against reference furniture before resizing the room |
| Dresser including hardware | 0.80 × 0.57 m | World horizontal bounds |
| Bed-to-dresser projected gap | **0.58 m** | Includes posts and drawer handle; supersedes approximate 0.67 m estimate. Projected bounding-box clearance is conservative, not an exact curved-surface minimum |
| Ensuite outer bounding envelope | about 3.80 × 3.48 m | Irregular room; northeast inset removes usable area |
| Bath porcelain exterior | 1.16 × 1.24 m | Existing oval approximation |
| Bath assembly with surround/fittings | 1.22 × 1.27 m | World horizontal bounds |
| Bowl inside at rim | 0.98 × 1.05 m | Derived from procedural profile |
| Bowl base | about 0.64 × 0.68 m | Derived from procedural profile |
| Shower tray | 1.11 × 0.84 m | Excludes brass frame |

## Findings and next dimensional decisions

**Buzz:** `../buzz-bedroom/overhead78.jpg`, `tour556.jpg`, and the film stills support the headboard/entry, window/dresser, desk/Jordan and display-wall relationships. The 2.30 m mattress is an authored model dimension; it has not been verified against the film. Measure that asset against a calibrated film view before moving the room shell. Moving the dresser or shrinking the bed merely to conceal the 0.58 m gap would violate the agreed reference priority. The unsupported west doorway remains closed, with the side wing accessible through the rear bedroom.

**Ensuite:** `../ensuite/part2-165s.jpg` shows a production reference photo; `part2-215s.jpg` shows Marina's reconstruction. Together they support an integrated bath/shower arrangement with a curved exposed bath front, straight wall-side boundaries and a shared screen. Our complete oval bowl plus separate tray is a shape/topology approximation, not simply evidence of an undersized room. Rebuild that fixture relationship against these views before deciding whether a wall must move. A generic conventional tub size would not establish the unusual film fixture's dimensions.

The suspected secondary staircase is west of the ensuite (near X5.8), not directly beneath its northeast inset. Its removal has not been shown to recover the missing corner.

## What remains unknown

The archived upstairs transcript gives no numeric dimensions for these rooms. The overhead reconstruction is perspective-projected and contains no scale bar. Neither a film-room error percentage nor an exact amount of bath/shower compaction is defensible yet. A calibrated plan, fixture identification or orthographic model export would resolve scale; until then retain the native shell and label fixture dimensions provisional.

Run `SurveyBuilder.ReviewRoomDimensions()` in Unity to regenerate the current asset measurements. Values above were read from live renderer bounds and the bowl's authored profile. Room envelopes come from the previously recorded collider surveys.
