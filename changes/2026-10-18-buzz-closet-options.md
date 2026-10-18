# Buzz's closet door (film 478/480/524/526): options, not built (overnight 4, Oct 18)

User, Oct 17: "the jordan poster is actually on what appears to be a closet door; you can make out the knob coming through on the
ruler". Film 526 (clearest) and 480 show a white-cased door, knob through the yellow ruler strip (480: at the chart's ~2.9 ft, i.e. a
standard 36 in knob if the chart's 0 is near the floor), the poster covering the leaf, in the corner between the desk wall and the shelves wall. Marina has plain wall.

## What is behind that wall in the plan: nothing usable

The poster hangs on Buzz's **desk wall** (spec z 15.998, built wall z 15.998-16.138) next to the **shelves corner** (x 7.473).
That wall is the upstairs' **exterior** wall (the desk-wall window, x 10.20-10.92, is in it). Behind it:

- z > 16.138 at x 7.47-8.9: outside, over the den wing (den ceiling top at upstairs y -0.44; den z 16.21-19.92).
- The only neighbour bump is the attic stair (x 5.78-7.333), whose outer wall stands at z 16.396-16.536: it is beyond the
  shelves wall, not behind the desk wall.
- No closet poly, void, hall or room touches that stretch of wall.

So a closet there needs new floor outside Marina's envelope (B, C) or space taken from Buzz's room (D). Per the brief, not forced.

## Where the film puts the door (one frame each, not a gate-grade measure)

- Film 526 (crop `~/.cache/home-alone-2/captures/overnight4-film526-door.png`), ruler = the poster's own width 0.735 m
  (hifi_buzz_props.py, from its printed 1 ft = 211 px): ~469 px/m at the door. Poster right edge -> hinge-side casing outer edge
  0.11 m; casing outer edge -> shelves corner ~0.26 m (0.2-0.4: the corner sits in a soft shadow). Knob 0.10 m in from the ruler
  strip's outer edge: the leaf's latch edge is at, or ~3 cm inside, the poster's ruler edge. Leaf ~ poster width + a few cm:
  a stock **30 x 80 in** leaf.
- Implied leaf: 0.33-1.09 m from the shelves corner, i.e. **x 7.80-8.57**, casing ~7.73-8.64. The desk (x 8.751) clears the
  casing by 0.11 m, as in the film (lamp just left of the door).
- Agreeing read of a different kind: Marina's growth chart (Marina 540 s frames 0 and 2, rays cut with the solve's desk-wall
  plane, twin-mattress ruler; scratch script used buzz_layout.py's planes): ruler-side edge 1.017 m from her shelves corner
  (2.564 m from her front corner; chart ruler 1.027). Poster 0.28-1.02 m from the corner vs the film's 0.33-1.09: 5-7 cm apart.
- The built poster (props lane) is at x 7.83-8.57 = 0.36-1.09 m from the shelves corner (placed from the front corner; the built
  room is 0.10 m wider than Marina's): it already sits where the film's leaf would be.

## Options (all keep Buzz's room faces where Marina measured them, except D)

| | What | Plan change | Cost |
|---|---|---|---|
| **A** | Faux door: pack 30x80 leaf (Door_3 White, as buzz_door) + casing on the desk-wall face at x 7.80-8.57, fixed shut; poster moved onto the leaf, knob through the ruler | none (dressing on the wall; verify_plan untouched) | the door leads nowhere (breaks "a door must lead somewhere": a DEVIATIONS row); can't be opened or hidden in |
| **B** | Shelf closet flush with the attic-stair bump: closet x 7.473-8.90, z 16.138-16.396 (**0.258 m clear**, 10 in), outer wall z 16.396-16.536 continuing the attic stair's outer wall from x 7.333 to 9.04, end wall x 8.90-9.04; 30x80 opening cut in the desk wall at x 7.80-8.57 | +0.37 m^2 outside Marina's envelope; no neighbour moves; the exterior line already exists west of it | shelves only (a rod needs >= 0.5 m); Kevin can't hide (0.26 m); upstairs only rendered from inside (DEVIATIONS 1) so invisible outdoors, but check the film shell's den roof doesn't poke into it |
| **C** | Reach-in closet: as B but **0.61 m clear** (24 in), z 16.138-16.748, outer wall 16.748-16.888 (0.35 m past the attic-stair bump); shelf 1.68 + rod 1.60 | +0.87 m^2 outside the envelope; new exterior jog over the den roof | Kevin can hide in it; most invented space; same den-roof check |
| **D** | Closet inside the room: 0.61 deep + 0.14 wall = 0.75 m into Buzz's room over x 7.473-8.90 | room -1.07 m^2 (-6.6%); the poster plane moves 0.75 m into the room; shelves end (z 15.192) 5.6 cm from the new wall | notably different room from Marina's: **not acceptable** (AGENTS.md). Shallow 0.30 version: 0.44 m in, -0.63 m^2 (-3.9%), still a shape change |

**Best guess: C** if the closet should open (a hiding place fits the game; the door is the film's; nothing Marina measured moves),
**A** if a look-only door is enough (zero plan risk, one build). B is the carpenter-clean line but a 10 in closet is odd for a bedroom.
Either way the door goes at x 7.80-8.57 (30 x 80, hinge at the shelves end, knob at the desk end: film 526) and the poster
moves onto the leaf, ruler edge at the latch edge.

To build C or B: add the closet space to the upstairs trace (`authored` override, as girls_room_b) + the door to
`measurements/overhead/upstairs-doors.json` -> reconcile.py -> verify_plan.py 0 FAIL; casing via openings.py; leaf from store_props
(buzz_door's Door_3 White at 30 in); shelf + rod generated; change record `changes/2026-10-18-buzz-closet.json` (claim: door
position, film 526 poster ruler; independent: Marina chart at the mattress ruler; the closet depth is AUTHORED -> DEVIATIONS row).

Current build from the walk start pose (HA_START 9.3,0.03,-13.4,200; poster flat on the wall):
`~/.cache/home-alone-2/captures/overnight4-before-film480view.png`. Film crops: `overnight4-film526-door.png`,
`overnight4-film480-door.png`; Marina's chart: `overnight4-marina540-chart.jpg` (same folder).
