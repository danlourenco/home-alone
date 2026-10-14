# Deviations ledger: every place the build departs from measurement

The house must **feel** authentic. A room that is a notably different shape or size from Marina's model is not acceptable (user, Oct 13). Every entry here departs from what was measured, guesses where nothing was measured, or chooses between conflicting sources. Each has a size, a reason and a way to revisit it. Add an entry whenever a step moves, stretches, assumes or authors geometry. Remove it only when evidence settles it.

**Shape risk**: high = changes how a room feels (proportions or size by more than ~5%); medium = noticeable on inspection; low = within measurement error, or invisible in play.

## Open, sorted by shape risk

| # | What | Size | Why | Shape risk | How to revisit |
|---|---|---|---|---|---|
| 1 | **Upstairs front wall overhangs the ground floor's front wall by ~1.6 m** (floors pinned at the stair; no stretch) | Marina's ground main block is 10.4 m deep, her upstairs 12.0 m; side-to-side they match. Every room on both floors keeps Marina's shape (`shape_drift.py`: ground main rooms within ±5%) | The film's upstairs was a separate set and never had to stack (Muto). The real-house plan (`dimensional-baseline/dimensioned-first-floor.png`, living 15 x ~28.9 ft, w/d 0.52) matches Marina's ground floor as measured (0.54), not the 1.141 stretch tried first (0.47). User decision Oct 13 | Interior: none. **Exterior: high** (front facade steps out upstairs) | When the exterior shell is built: a porch roof or a deeper ground facade (a strip of non-room space), never by reshaping rooms. `stack_floor.py` still reports the stretch that would stack the facades (1.141). |
| 2 | Interior walls thinned to 14 cm (`reconcile.py` WALL_T) | Rooms +2-6% where Marina's walls were 25-45 cm. `shape_drift.py` flags: kevin_jeff_room +7% wide, hall_bath +10% wide, buzz_room +6% area, hall_end / hall_corridor / hall_corridor_south +14-16% per side (proportions kept) | User decision (gameplay space); far-end hall clip supports the hall width | Low-medium | Remove with `--measured` builds; compare the feel |
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
| 18 | Vestibule +8% wide; service stair (back_stair) 10 cm narrower than traced (`shape_drift.py`) | Small spaces: wall thinning; the stair's left edge aligned onto the foyer wall 7 cm away | Reconciler rules | Low | Trace both at 4x; keep the stair's measured width |
| 19 | Doors placed from topology (centred on the shared wall, position not measured): linen_closet / hall_corridor (prop door), girls_room_b / hall_corridor_south | Up to half the wall length | No view of the door position; girls' room B is checked loosely by the overhead's open door leaf (17 cm, tol 40) | Low | A frame showing each doorway; then a measured span |
| 20 | Landing and flight-2 slab depth 0.20 m (authored): headroom under the landing is 1.95 m (leak/headroom check reports 21 points) | Marina's landing top is 2.20 m above the foyer; slab depth not measured | Marina's walk 1068-1072 s passes under the landing, so it must be a slab | Low-medium (an adult walks under it) | Measure the landing underside in Marina's walk frames (door-scaled) |
| 21 | Attic stairwell open above (no attic built) | — | Attic not in scope yet | Low | Build the attic |
| 22 | What is behind the arched foyer door (rear right) is unknown: built as a closed prop door | — | Marina's walk shows it closed (1068-1071 s) | Low | A frame with the door open, or the film |
| 17 | Parents' bath 0.63 m wall stub reads -9 cm | Pre-existing | Likely furniture against the wall | Low | Look at the frames |

## Old model (IntactHouseReference): Buzz's room vs Marina (Oct 13, census; walls NOT moved, user decision pending)

Marina's overhead is turned 90 deg relative to the old model: her door wall = old east wall (X -1.16 native), her shelves wall = old north wall (Y 1.88). Same topology (door at the corner, bed off the door wall, shelves wall, chest between two front windows, third window on the desk wall, attic stair beside the shelves wall). Sizes differ. Evidence: `spec/captures/buzz-old-vs-marina/all.png` (Marina frame | old scene rendered from her own camera, poses from the gated Buzz clip `sfm-work/real-vggt-buzzall`, 2.038 m/unit at 80 in doors, pinned at the door corner, eye 1.28 m from the clip's floor peak).

| # | What | Old model | Marina | Shape risk | How to revisit |
|---|---|---|---|---|---|
| O1 | **Room depth, door wall to desk wall** | 3.82 m (triangle census X -6.10..-1.16) | 4.35 m (VGGT) / 4.37 (trace): old is **-0.53 m, -12%**. Independent proof: 9 of her 45 camera positions (556-562 s) stand 3.9-4.10 m from the door wall, beyond the old west wall; still beyond at a 76 in door (3.90 m), inside only below ~75 in. The 560 s render is black (camera in the wall) | **High** (the "cramped" feel) | West wall borders the wing room (object52/93) for Y > -0.95 m but is EXTERIOR with the side window for Y -1.80..-0.95 (recessed side sash at -1.40 m). Growing west moves an outside wall and its window: user decision. Growing east takes the 1.45 m corridor to 0.92 m |
| O2 | **Room width, shelves wall to front-window wall** | 3.25 m (Y -2.32..1.88) | 3.49 (VGGT) / 3.64 (trace): old **-0.24..-0.39 m, -7..-11%** | High | The hall band north of Buzz (Y 1.59..3.46 m) is 1.87 m where Marina's corridor piece + attic-stair strip is 1.35-1.37 m (+0.50 m). Moving Buzz's north wall north 0.30 m (0.39 native) gives 3.55 m and leaves 1.57 m of hall: interior walls only. Recommended; the attic stairwell (Y 1.78..3.27 m, 1.49 wide vs Marina 1.37) shifts with it |
| O3 | Door position along the door wall | leaf 0.33..1.11 m from the shelves-wall corner | casing 0.04..0.80 m (hall-s1 148-192; tour556 shows the casing at the corner) | Medium | Moves with any wall fix; 0.29 m |
| O4 | Front windows | sill 0.47 m, head 1.73 m, 0.73 m wide (native 0.94 x 1.62 at y 6.64), 1.04 m of wall between | sill 0.82 m, head >= 1.97 m, ~1.08 m wide incl. curtains, 1.10 m between (tour550 at the 550 s pose) | Medium (exterior, not touched) | Exterior shell pass |
| O5 | Chest between the front windows | was 0.56 w x 0.80 h, 1 column x 4 drawers | 0.87 w x 1.31 h, 2 columns x 5 drawers (tour550, pose-derived; +-0.1 m from the eye height) | — | **Applied Oct 13** (`BuzzBedroom.cs`): 0.84 x 0.44 x 1.27 m, front face unchanged. `CheckBuzzBedroom` (Play mode) not yet re-run |
| O6 | Bed to chest passage | 0.70 m (bed frame Z -0.75 to chest front -1.70 native) | ~0.83 m (overhead50, oblique reading) | Medium | Follows O2 |
| O7 | Ceiling | 2.41-2.43 m (horizontal planes at z 8.34-8.36 over the room) | unmeasured in Buzz; 2.29-2.42 next door | Low | — |

Not changed by any of this: the bed (0.94 x 1.78 m mattress, old; Marina ~1.0 x 1.82 from the overhead), shelves, desk, Jordan, windows, walls.

## Settled (kept for the record)

- Ground floor front-to-back stretch (×1.141, tried Oct 13): removed. It changed every main-block room's proportions by 12-18%, and the real-house plan sided with Marina's ground floor as measured. Replaced by #1.

- Upstairs closets don't open (user decision). Linen closet has a prop door.
- Scale the players, not the house (user decision). A uniform house or player scale for feel is allowed later; it never changes shapes.
- Marina is the geometric authority; the downloaded model (`HOME_ALONE_FINAL.glb`) is a check only.
