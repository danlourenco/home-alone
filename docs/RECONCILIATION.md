# How the house gets built

Goal: one cohesive, faithful McCallister house that feels like the film and plays as an asymmetric FPS (Kevin vs. the bandits). This is the reference for every session; experiment logs live in [tasks/sfm-plan.md](../tasks/sfm-plan.md).

## Each source is the authority for something different

| Source | Authority for | Not trusted for |
|---|---|---|
| Real house exterior (Winnetka: photos, exterior GLB, visitor plans in `art/home_alone/references/dimensional-baseline/`) | Envelope: footprint, facade, window positions, roofline, floor levels | Interior layout (film interiors were sets) |
| Marina Coates's CG tours, measured with SfM | Room shapes, sizes, adjacency, furniture placement | Absolute scale (comes from doors, ±4%) |
| The film | The look; a named list of must-match shots | Measurements (lenses and sets distort) |
| Marina's stated areas (2,620 / 1,900 / 476 ft²) | Scale cross-check | Per-room values |
| Marina's overhead plan views, calibrated on SfM-measured rooms (`tools/sfm/overhead_fit.py`) | Whole-floor layout: rooms SfM can't reach, halls, closets | Doorways (hidden under headers) |
| John Muto's set model (production designer; Part 2 overhead segment, frames 5–33) | Which rooms adjoin which on the film set | Dimensions |
| Game rules | Hard limits for both player bodies (below) | — |

## Pipeline

```
Marina video --SfM, 2 methods must agree--> room shapes +- error  ┐
Doors (80 in, 78-84 range) ---------------> scale +- 4%            ├-> RECONCILER -> house_spec.json -> Unity generator -> playable house
Exterior / real house --------------------> envelope               │   (best fit       (single source     (only reads        │
Film must-match shots --------------------> visual checks ---------┤    + change log)    of truth)          the spec)         │
Game rules (two bodies) ------------------> hard limits -----------┘                                                         v
                                                                                verify: renders vs Marina/film frames + walk routes
```

1. **Measure.** Per room: COLMAP and VGGT reconstructions, accept only windows where they agree (validated on synthetic truth); `room_dims.py` for shape; `door_scale.py` for scale. Every number carries an error range and provenance (frames, method).
2. **Reconcile.** A solver treats each measurement as "about this, within its error" and the rules below as requirements, then moves measurements as little as possible (weighted by confidence). Output: `house_spec.json` plus a change log per element ("Buzz widened 6 cm to meet the exterior wall, within ±4%"). Anything that can't fit is named, not hidden; the user chooses the compromise and it is logged as a deliberate decision.
   - Requirements: rooms inside the envelope; shared walls with realistic thickness; doors aligned on both sides; upper stairwell over the lower stair; upper exterior walls over lower ones; both players' body rules.
3. **Build.** One Unity generator reads only `house_spec.json`. No geometry constants elsewhere.
4. **Verify (automated).** Looks right: render from Marina's solved cameras and the film must-match shots, compare structural lines (corners, door frames, trim). Plays right: scripted routes with each player's capsule through every door, stair and hiding spot.
5. **Art.** Materials, furniture models, lighting from existing assets. Never moves walls; geometry changes go through the spec.

## Scale and feel: scale the players, not the house

The house stays at true, faithful scale. Feel comes from the bodies:

| | Kevin | Bandits |
|---|---|---|
| Eye height | ~1.1 m | ~1.7 m |
| Collision | kid capsule; crawl ~0.4 m tall | adult capsule; crouch ~1.1 m at best |
| Under beds, behind furniture, small gaps | yes | no |
| Feel | rooms loom, furniture is big | rooms tight and cluttered |

Two rule sets in the reconciler:
- **Adult rules (hard):** every doorway, stair and hallway passes the adult capsule with headroom.
- **Kid-only spaces (designed):** furniture tagged with gameplay roles (e.g. `hideable`). A hideable bed's under-frame clearance must fit Kevin's crawl capsule and not the adult's. Furniture dimensions therefore live in `house_spec.json`, measured from Marina where possible; gameplay-forced adjustments appear in the change log.

Exact capsule sizes and eye heights are tuned by playtesting the grey-box house.

## Status (Oct 12, 2026)

| Step | Status |
|---|---|
| Measure | Upstairs done (Oct 13). SfM measured Buzz, Kevin and the parents' suite. Marina's angled overhead, calibrated on those rooms (9 cm held-out), gives the whole floor. Total 1,928 ft² vs Marina's 1,900 supports 80 in doors. Remaining: ground floor, ceiling heights, furniture clearances |
| Envelope | Data exists, not yet in the pipeline |
| Reconcile | v0 for upstairs (Oct 13): `tools/house/reconcile.py` → `spec/house_spec.json` + `spec/upstairs-changes.md`. Squares, aligns, measures walls, places doors, checks adult rules. Open: hall bath access, linen closet walls, assumed ceiling |
| Generator | `Assets/Editor/SpecGreybox.cs` builds `Greybox_Upstairs.unity` from `spec/house_spec.json` only (Oct 13). Floors, walls, door cuts, rails, prop doors; world z = −spec z (Unity is left-handed) |
| Verify | `verify-plan` skill: checkpoints 12/12; 3D wall check (`check_walls.py`) on 3 gated clips, every long wall within ±7 cm; adult walk test 11/11 (built and as-measured); matched-camera overlays for visual review |
| Art | Assets exist; waits for geometry |

Open questions answered at the reconcile step: how the floors stack; how much the envelope forces interior rooms to change; whether doors are 80 in (checked against Marina's 1,900 ft² upstairs total).
