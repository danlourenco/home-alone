# Deviations ledger: every place the build departs from measurement

The house must **feel** authentic. A room that is a notably different shape or size from Marina's model is not acceptable (user, Oct 13). Every entry here departs from what was measured, guesses where nothing was measured, or chooses between conflicting sources. Each has a size, a reason and a way to revisit it. Add an entry whenever a step moves, stretches, assumes or authors geometry. Remove it only when evidence settles it.

**Shape risk**: high = changes how a room feels (proportions or size by more than ~5%); medium = noticeable on inspection; low = within measurement error, or invisible in play.

## Open, sorted by shape risk

| # | What | Size | Why | Shape risk | How to revisit |
|---|---|---|---|---|---|
| 1 | **Upstairs front wall overhangs the ground floor's front wall by ~1.6 m** (floors pinned at the stair; no stretch) | Marina's ground main block is 10.4 m deep, her upstairs 12.0 m; side-to-side they match. Every room on both floors keeps Marina's shape (`shape_drift.py`: ground main rooms within ±5%) | The film's upstairs was a separate set and never had to stack (Muto). The real-house plan (`dimensional-baseline/dimensioned-first-floor.png`, living 15 x ~28.9 ft, w/d 0.52) matches Marina's ground floor as measured (0.54), not the 1.141 stretch tried first (0.47). User decision Oct 13 | Interior: none. **Exterior: high** (front facade steps out upstairs) | When the exterior shell is built: a porch roof or a deeper ground facade (a strip of non-room space), never by reshaping rooms. `stack_floor.py` still reports the stretch that would stack the facades (1.141). |
| 2 | Interior walls thinned to 14 cm (`reconcile.py` WALL_T) | Rooms +2-6% where Marina's walls were 25-45 cm | User decision (gameplay space); far-end hall clip supports the hall width | Low-medium | Remove with `--measured` builds; compare the feel |
| 3 | Floor-to-floor 15 risers = 2.54 m | The downloaded model implies 16 risers (landing at 80% of floor height) | User decision; foyer ceiling line measured at 2.32 m | Medium (stair feel, ceiling height downstairs) | A film or Marina frame that shows the steps above the landing |
| 4 | Stair landing width = upstairs well width (2.83 m) | Marina's main-floor landing spans the foyer, ~4.0 m in the climb clip (ground foyer here is 3.67-3.76 m) | The landing must sit under the well | Medium | Widen the well to the foyer width if the upstairs north side allows |
| 5 | Upstairs stairwell's rear (west) edge assumed at the building edge | Hidden in the upstairs overhead | Landing window is on the rear exterior wall | Medium (stacking pin depends on it) | Part 2 frames looking across the well at the rear wall (hall walk ~f258-300) |
| 6 | Flight 2 + gallery: 2 risers, 1.2 m wide, gallery 1.2 m along the north side; landing depth 1.58 m | Authored sizes; landing depth corrected for VGGT depth stretch ±0.15 m | Never filmed in full; user's plan drawing, film and climb clip agree on the layout only | Medium | Matched-camera render vs the Kate/Kevin film shot and Part 2 f258 |
| 7 | Ground scale from Marina's 2,620 ft² with the sunroom included | If her figure excludes the sunroom, the ground floor is ~5% too small | Downloaded model also includes it | Medium | Marina's tour wording around her area figures |
| 8 | Ground aspect from one room (den SfM, 0.53) | Every ground depth scales with it (±2% measured) | No per-room SfM on the ground floor (skill overhead-floor) | Low (proven ±2%) | A second room's ratio from a gated clip |
| 9 | Foyer width 3.76 m traced vs 3.49 m from clip A (lateral, door-scaled) | 7% | Unresolved | Medium | Re-trace the foyer walls at 4x; clip A density peaks per wall |
| 10 | Kitchen + breakfast 519 ft² traced vs Marina's stated 477 | +9% (boundary ambiguous) | Which zone Marina measured is unclear | Low-medium | Identify the boundary Marina used for 477 |
| 11 | Ceilings: upstairs default 2.40 m in unmeasured rooms; ground 2.32 m everywhere | Measured in 3 upstairs spaces and the foyer only | No other door-wall measurements yet | Low-medium | Door-wall ceiling measurement per room (as upstairs) |
| 12 | Door height 80 in nominal (78-80 honest) | ±1.3% overall scale | Area check brackets 78-80 | Low | — |
| 13 | Upstairs hall feels narrow (user) | Built 1.59 m vs 1.58 measured | Matches Marina; may be lens/eye height/emptiness | Medium (feel) | Matched film shot of the hall |
| 14 | Parents' hall door: hall-s1 and the far-end clip disagree by ~15 cm | The reconciler used to slide it to agree; slide removed Oct 13 | Two gated clips disagree | Low | A third view of that door |
| 15 | Second dining-room door (rear wall, right) not modelled; service stair has no steps; landing window, newels not modelled | — | Not needed for layout | Low | Next ground-floor detail pass |
| 16 | Stairs use the adult-body rule (0.65 m), not the 0.90 m hall minimum | Service stair is 0.90 m | A stair is not a corridor | Low | — |
| 18 | Vestibule +8% wide; service stair 10 cm narrower than traced (`shape_drift.py`) | Small spaces: wall thinning; the stair's left edge aligned onto the foyer wall 7 cm away | Reconciler rules | Low | Trace both at 4x; keep the stair's measured width |
| 17 | Parents' bath 0.63 m wall stub reads -9 cm | Pre-existing | Likely furniture against the wall | Low | Look at the frames |

## Settled (kept for the record)

- Ground floor front-to-back stretch (×1.141, tried Oct 13): removed. It changed every main-block room's proportions by 12-18%, and the real-house plan sided with Marina's ground floor as measured. Replaced by #1.

- Upstairs closets don't open (user decision). Linen closet has a prop door.
- Scale the players, not the house (user decision). A uniform house or player scale for feel is allowed later; it never changes shapes.
- Marina is the geometric authority; the downloaded model (`HOME_ALONE_FINAL.glb`) is a check only.
