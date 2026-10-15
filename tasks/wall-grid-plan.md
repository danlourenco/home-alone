# Wall-grid rebuild: build the house like a house

Started Oct 15, 2026. The user's direction (Oct 15):

> "how do we get these rooms and walls such that there are clean angles and alignments instead of weird patches? it feels shoddy, i want the digital equivalent of reconstructing a real house. everything should line up flush"

They then approved the approach below: "this seems like a good approach! Let's get back to fundamentals."

## Why the current build looks shoddy

The grey-box is built **room by room**:
- Each space in `spec/house_spec*.json` draws its own floor, its own ceiling and half of every wall around it (`SpecGreybox.Walls`, `HalfWall` 7 cm outward).
- Two rooms meet cleanly only if their separately traced edges agree. They often disagree by 1–5 cm.
- `reconcile.py align()` merges lines only within 12 cm and 1 m of reach, so long walls keep jogs.
- Corners and doorway thresholds belong to neither room, so they were holes. Daylight showed them on Oct 15: a slit at the parents' bedroom corner, and blue strips under doorways.
- The two floors are traced separately, so walls that stack across floors do not line up. The picture wall sits at 8.953 while flight 2 and the gallery edge sit at 9.17.

The Oct 15 stopgaps (corner posts, threshold boxes; uncommitted, in `SpecGreybox.cs`) patch symptoms and already create new ledges. **They are removed by this plan, not kept.**

## Target architecture

```
trace + measurements ──> reconcile.py (rooms in metres, as now)
                            │
                            ▼
                    tools/house/wall_graph.py   (NEW, pure Python, tested)
                    1. grid: shared wall lines across both floors
                    2. walls: one object per wall segment, shared by the rooms on both sides
                    3. geometry: walls / floor plates / ceilings / openings as non-overlapping boxes
                    4. verification (raster watertightness, overlaps, measurement drift)
                            │  spec/geometry*.json
                            ▼
                    SpecGreybox.cs: instantiates boxes + finish planes; no geometry decisions
```

### 1. The grid (`wall_graph.grid`)
- Collect every room edge on **both floors** as a wall-face line: axis, coordinate, extent, room and side.
- Pair facing faces across a wall into a wall **centreline**. An exterior face takes the building's outer line.
- Cluster centrelines per axis into grid lines. Two lines join a cluster when both hold:
  - they are within `SNAP_TOL`, starting at 0.10 m;
  - they are connected: collinear continuations, through a T-junction, or stacked across floors with overlapping plan extents.
- The cluster's coordinate is the **weighted** mean:
  - measured anchors (SfM rooms, film-verified lines) ×5;
  - lines the user or the film fixed: exact (infinite weight).
- **Snap log:** every line that moves is written with its distance, its source and its cluster.
- Thresholds:
  - a snap over 0.04 m must be listed in `measurements/grid-snaps.json` with a reason;
  - a snap over 0.10 m is refused unless that file names a measurement or user decision behind it.
- Designated stacks, which must share a line. This list is reviewed with the user:
  - the stairwell walls on both floors;
  - the exterior facades where the floors share them;
  - the picture wall / flight-2 edge / gallery edge (resolved from the film: see foyer below);
  - the hall walls over the foyer walls where they stack.

### 2. Walls as objects (`wall_graph.walls`)
- One wall per grid segment between junctions:
  - centreline;
  - thickness: interior 0.14 (user decision Oct 13), exterior as measured;
  - the room on each side, and the finish of each face.
- The wall footprints are unioned in 2D, a rectilinear polygon union. Corners and T-junctions therefore close by construction: no posts, no gaps.
- Room interior faces = centreline ± thickness/2. A room is the face between its walls; it no longer draws walls.

### 3. Geometry (`wall_graph.geometry`)
Everything comes out as **non-overlapping boxes**: a rectangle decomposition of each union, so no two boxes share volume.
- **Walls:** the union footprint, extruded from the floor to that storey's ceiling or to the underside of the floor above, as now. Doors, arches and windows are cut out as volumes: below the sill, above the head and beside the jambs.
- **Floor plate:** one per storey, the union of rooms and walls, minus the stairwell holes. No per-room floors, so no thresholds.
- **Ceilings:** one plate per ceiling-height zone (2.4, 2.5, 2.29, the foyer's 2.82, the landing underside). Walls rise to the plate they meet.
- **Trim:** casings on both faces of each opening, sized so they always fit. An opening keeps its trim width (0.07) clear of any perpendicular wall. Example: the parents' door against the hall's left wall, where the film shows the casing meeting the wall (10819, 10741, 2687).
- **Finishes:** each room face gets a finish plane 2 mm proud, clipped to the face's exact rectangle (wallpaper, wainscot). Walls themselves are one structural material. Two rooms' finishes never share a plane.

### 4. Unity (`SpecGreybox`)
The builder reads `spec/geometry*.json` and instantiates boxes, finish planes, glass and trim. It keeps:
- the stairs (already boxes from `reconcile.py`);
- the dressing;
- daylight;
- the walk, seam and leak checks.

It loses room-by-room wall, floor and ceiling generation, `CornerPosts`, `Threshold` and the hole-edge snapping.

## Verification plan

Each layer has its own check. Every check is first proven to **fail on an injected error** (AGENTS.md; `--selftest` style). A green check that has never been seen to fail is not evidence.

### V1. Unit tests: pure Python, seconds (`tools/house/test_wall_graph.py`)
| Test | Passes when | Injected error that must fail it |
|---|---|---|
| Grid snapping on synthetic plans | Two rooms 3 cm apart share one line; two 30 cm apart don't; an anchor stays put | Turn off the anchor weight; widen SNAP_TOL to 0.5 |
| Rectangle decomposition | The boxes' area equals the union's area to 1 cm²; no two boxes intersect | Drop one box; duplicate one |
| Opening cuts | Wall area = full area − openings; the header sits at the door height | Cut the opening 1 cm narrow |
| Trim clearance | Every casing fits beside a perpendicular wall | Put a door flush against a wall |

### V2. Plan integrity: Python, on the real house, every reconcile (`wall_graph.py --check`)
- **Watertight raster:** rasterize each storey at 1 cm. Every cell must be exactly one of room, wall, stairwell or outside.
  - **Fail** if a room cell touches an outside cell except through a door or window opening.
  - **Fail** on any unclassified cell inside the building outline. That is a gap such as the Oct 15 corner slit.
  - **Fail** on any wall sliver under 2 cm.
- **No overlaps:** no two geometry boxes share volume (≥ 1 mm³).
- **Coplanarity:** faces from different boxes that are coplanar and overlap (z-fighting) must be 0, as must the finish planes of two rooms on one face.
- **Stacking:** every designated stack has identical coordinates on both floors (0 mm).
- **Snap budget:** every snap is ≤ 0.04 m or is listed in `grid-snaps.json` with a reason. Total snap distance is reported.

### V3. Measurements preserved: Python, every reconcile
- `verify_plan.py` (upstairs 15 checkpoints, ground 4): **0 FAIL**, both floors, after the grid.
- `shape_drift.py`: no room moves more than its pre-grid value by more than 2% in width, depth or area. Authored rooms (girls B, DEVIATIONS 32) excepted.
- **Anchors stay inside their measured spread:**
  - Buzz: 3.49–3.68 × 4.37–4.46;
  - Kevin: vs its own doors, 0.7%;
  - parents' bath width;
  - hall_end 1.22 ± 0.05;
  - girls A depth 7'6".
- **Baseline file:** `measurements/baseline/pre-grid.json` holds every room's dimensions, every door's position and every checkpoint value before the rebuild. A diff report lists every change in feet and inches.

### V4. Film agreement: Python and renders, the ones the user asked for
- Foyer: the picture wall's corner, flight 2's side and the gallery edge on one vertical line.
  - Marina 312 s already shows this.
  - The film frames 1616, 3175 and 10673 decide the coordinate, via a scale-free ratio against the newel / landing edge at the same depth.
- Parents' door: the left casing meets the hall's left wall; the right gap is 0–20% of the end wall (frames 10819, 10741, 2687, 10828).
- Each becomes a checkpoint in `measurements/checkpoints/*.json` with its frame and tolerance, so it can never silently regress.

### V5. Unity build gates: every build
- **Seam check:** 0 overlaps, 0 ledges, 0 gaps.
  - The two known upstairs ledges (`seams-known.json`) must disappear. The known list ends **empty**.
- **Hole probes:** every threshold and outside corner is solid.
- **Light-tight test (new):** cast rays from a dense grid of points inside every room, including 5 cm from every corner and along every threshold, in all directions. A ray that leaves the building except through glass or an open exterior door fails.
- **Walk tests:** rooms, stairs, attic, service stair, both bodies plus the Player's own controller: 0 blocked, no stall.
- **Leak and headroom check:** 0 / 0.

### V6. Look at it
- Before/after renders from fixed cameras:
  - one per room;
  - Marina's matched cameras (`RenderMatched`);
  - the film-matched foyer and hall cameras.
- Daylight renders with the lamps off at fixed EV: corners and thresholds must show no light.
- A comparison sheet per phase. I open every image before reporting.
- **The user walks it.** Nothing is "done" before they accept it (change-gate TRIAL rule).

## The stair hall: the highest-risk part (user concern, Oct 15: "i don't want many [surprises]")

Today's problems clustered here:
- the stall between risers 5 and 6;
- z-fighting on the well walls;
- the thick landing;
- the wall and ceiling misaligned under the gallery;
- the 8.5 in picture-wall / gallery mismatch.

The current builder carries the most special cases here: walls cut under the landing, ceilings stopped at landings, well edges snapped to the foyer's walls, and a soffit and well walls dressed separately. To keep surprises down:

1. **Decide before building.** Settle the open foyer/stair geometry from the film first: the picture-wall corner vs flight 2's edge vs the gallery edge (frames 1616, 3175, 10673, 2090), plus the landing and well edges. The rebuild then reproduces decided numbers and discovers nothing.
2. **Build it as a real stair hall.** One two-storey space whose walls run from the main floor to the upstairs ceiling. The landing and flights are objects inside it. This replaces "two floors' walls meeting at the well" and removes most special cases instead of re-coding them.
3. **Every past stair fix becomes a test first,** written before any stair-hall code and kept green throughout:
   - the Player's own controller climbs and descends with no stall;
   - landing underside 2.26 m;
   - 0 overlaps on the well walls;
   - the wall under the gallery is flush with the ceiling edge;
   - headroom on every tread;
   - back_hall closed;
   - the open middle between the flights;
   - flight 2's side, the picture-wall corner and the gallery edge on one line (the V4 film checkpoint).

   The existing stair walk tests run unchanged as regression.
4. **Its own phase,** after the pilot. It is judged against fixed before/after renders: the stair from the foot and the gallery, Marina 203 s / 312 s matched cameras, film frames. The user walks it before anything else moves.

## Phases (each ends green on its checks, committed, pushed)

| # | Phase | Ends when |
|---|---|---|
| 0 | Baseline: `measurements/baseline/pre-grid.json`; V1 test harness; injected-error proofs | DONE Oct 15 (e9aaf37): baseline + `baseline.py --diff`, proven on injected changes |
| 1 | Grid + snap log (`wall_graph.grid`); decisions in `measurements/grid-snaps.json` | V1 grid tests; snap report reviewed (preview page); V3 unchanged |
| 2 | Walls + geometry in Python | V1 all; V2 all on the real house |
| 3 | **Pilot in Unity:** upstairs from geometry (Pilot_WallGrid) | DONE Oct 15 (ee5eadc, dcdb923): 0/0/0 seams, 0 leaks, 0 blocked; user approved the renders ('that looked good') and walked it ('looks very good'; one note, the stair-head notch, fixed in ec5761a) |
| 4 | Foyer/stair geometry decided from the film (V4) | Film checkpoints written and agreeing |
| 5 | **Stair hall** as one two-storey space (see above) | Every stair regression test green; matched renders; user walks it |
| 6 | Rest of the house; remove the stopgaps | V5 all, known-seams list empty; V6 renders |
| 7 | Windows (inventory done) onto the new walls; the chute shaft | Light-tight test with glass |
| 8 | User walk | User accepts or leaves notes |

Each geometry phase gets a `changes/<date>-wall-grid-<phase>.json` record (change gate).

## Source priority when they disagree (user direction, Oct 15)
1. **The film.** For anything the film shows: the foyer, the upstairs hall, the parents' door, the exterior. ("reconcile this to a movie still rather than marina's model")
2. **Marina's measured rooms:** SfM, in-room frames.
3. **Marina's overhead tracing.**
4. **The real-house plan (Eric):** a secondary check only.

Never average conflicting sources. Log the choice in DEVIATIONS.

## Not in scope here
- The exterior shell vs the film (next, after this).
- The attic interior.
- The upstairs-only-from-inside rendering split (DEVIATIONS 1).
- Lighting bakes; the sky-light leak indoors needs a probe-volume bake later.
