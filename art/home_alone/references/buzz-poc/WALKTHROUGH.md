# Buzz room — walkable candidate

September 18. Open `unity/HomeAlone/Assets/Scenes/BuzzWalkableCandidate.unity`, press Play, click Game view. WASD move, mouse look, Shift faster, C crouch, R reset, Esc releases mouse. Currently left running in Game view.

## Review assumptions

| Item | Candidate | Evidence / status |
|---|---|---|
| Room clear footprint | 3.90 × 4.80m | Working estimate; NOT a recovered measurement |
| Ceiling | 2.40m | Provisional |
| Door height | 2.032m | Explicit scale assumption |
| Bed footprint | approximately 1.10 × 1.99m | Working furniture envelope; not verified product dimensions |
| Player height / eye height | 1.70 / 1.55m | Walkthrough reference |
| Window arrangement | Two dresser-wall windows, one desk-wall window | Marina reference; openings represented by blue markers |

Layout includes bed, headboard/footboard, pillow, bedside table/lamp, shelves, dresser, desk/chair, terrarium footprint, closet-door placeholder, three window markers and ceiling. These are simple volumes, not final modeled props, textures, or an animated tarantula. All earlier detailed main-house assets remain untouched.

The entry is open. A small enclosed test apron outside it allows doorway passage without inventing a new house hallway. It is only test space. The actual movie hallway silhouette remains protected.

## Verification

`BuzzProportionPOC.CheckWalkable()` passed fourteen waypoint segments in Edit mode and Play mode using the existing FpsController: shelves, entry out and back, bed foot, dresser-side bed access, desk approach and return. Player remained above the floor; runtime feet settled to Y≈0.02m. This is a representative route check, not a claim that every corner is accessible.

Main house SHA1 unchanged: `9025a626afcaadded033f19406e42964dfff9009`.

[Bed-wall eye-level view](../../../../unity/HomeAlone/Assets/Captures/BuzzPOC/walkable-entry.png) · [Desk-side view](../../../../unity/HomeAlone/Assets/Captures/BuzzPOC/walkable-desk.png)

Rebuild outside Play mode using `HomeAlone > Marina PoC > Build walkable Buzz candidate`. This builds the separate normalized study first, then saves the walkable scene. The estimated room dimensions remain editable in study.json; rebuild to apply. Do not run the rejected camera-fit scripts as if they supplied verified dimensions.

## What to judge

Can the bed/door/shelves composition feel like Marina's room while leaving credible walking space? Does the desk/dresser end feel too compressed or too empty? Does 2.40m ceiling height feel low? These are review questions, not blockers requiring an answer before other work can continue.

## Candidate B — footprint review

[Same-scale A/B plan](footprint-comparison.svg). B retains the 25cm width addition needed for circulation and adds approximately 53cm toward the desk wall. Furniture sizes and the hallway-side opening stay fixed. Shelves stop 65cm before the doorway wall; a 60cm doorway approach is checked for shelf intrusion. Dresser/bed lateral clearance is 67cm. Fourteen waypoint route passes in Edit and Play mode.

Marina supports furniture/window arrangement; poster supports surrounding adjacency and known conflicts. The photograph does not establish a trustworthy metric footprint or aspect ratio, so no claimed poster-derived dimensional trace is used. The 4.80m depth is a working design estimate for comparison, not a validated reconstruction. The original poster photo is archived at ../poster/full-poster.jpg.
