# Paint-can trap (TRIAL, Oct 16 2026)

A full gallon of paint on a rope tied to the upstairs gallery rail, swung down flight 1 into the face of someone climbing it.
Gameplay rig, not house geometry: no wall, stair or room moved (no change-gate record), and the build's gates are byte-identical
with and without it.

## What the film shows (`0-homealone/full/homealone-movie-screencaps.com-<N>.jpg`)
| Frames | What |
|---|---|
| 10684 | Kevin runs up flight 1 past the landing (the rig is already set) |
| 10700, 10702, 10730 | From below: **two ropes wrapped round the gallery handrail**, two balusters apart; Kevin lifts a can over the rail and drops it. A second can (blue "SATIN" label) waits on the rail |
| 10706, 10708 | From the foyer looking up flight 1: the can (white, red drips, wire bail) swings down the flight toward the camera on a white cord that runs straight up out of frame |
| 10710-10714 | It meets Marv on the flight, at face height; he falls back flat onto the foyer floor |
| 10716-10724 | The second can hits Harry the same way on the lower half of flight 1 (10724 wide: his feet around steps 3-5, the can swinging back up afterwards) |
| 10770-10827 | They climb again and reach the top |

So: rope tied to the **gallery rail over flight 1** (not the newel, not the ceiling). The can swings in the plane of the flight,
from the landing side toward the foyer, and meets a man facing up the stair face-first, low on the flight. Two cans, both built:

- **Can 1 (Marv's, 10706-10714):** silver can, white-painted lid, red paint over the whole top rim running down the side in drips,
  a blue label panel beside one ear (10708). Its knot is the LEFT one seen from the stair (10700/10702/10730).
- **Can 2 (Harry's, 10700 on the rail, 10716-10724):** cream-painted can, a wide blue "SATIN" label, cream runs down the label's front
  (10722). Its knot is the RIGHT one.
- **Knot spacing:** x 860 and 1015 px (of 1920) in 10700, with two balusters between them. The baluster pitch there is ~95 px, so the
  spacing is 1.63 pitches = **0.19 m** at our rail's 0.116 m pitch. Image right = spec +z (the camera looks +x from the well), so can 1
  is at spec z 10.735 and can 2 at 10.925, either side of the flight's walk line (10.83). At rest they hang 2.5 cm apart.
- **Can 2's rope length cannot be read from the film:** its cord runs out of frame in 10720/10722, and no frame shows a knot and its
  can together with a ruler. It gets the same length as can 1; 10720/10724 show it at Harry's head on the same lower steps.

## In our house
- The gallery rail over flight 1 is `geometry.json` upstairs `openings` kind `rail`, axis x, c 5.647 (spec z 9.23-11.43). Its edge
  crosses directly over **flight1_step04** (x 5.345-5.640): the bottom of the arc lands on the 4th step, inside the film's 3-6.
- Probed in the built scene (`SpecGreybox.Traps`, rays onto the built colliders, not assumed): handrail top **0.950 m** above the
  upper floor (3.976 m above the ground floor), stairwell face x 5.617, floor edge x 5.577, its underside -0.206 (the foyer ceiling).
- Tie point (pivot): just clear of the floor edge, at the handrail's middle: (5.570, 0.920, spec z 10.83, the flight's walk line).

## Parameters
| Item | Value | Where it comes from |
|---|---|---|
| Cans | 0.165 m dia x 0.19 m, wire bail rising 0.08 m. Models from `tools/house/hifi_paint_can.py`: `PaintCan.glb` (Marv's: label panel ~110 deg by one ear, paint skin over the top rim, 10 red drips of 4-15 cm ending in beads) and `PaintCanSatin.glb` (Harry's: label ~260 deg, cream rim, 4 long cream runs down the label's front plus 1 behind). Shared: closed body with rolled chime rims top and bottom, lid sunk in the rim with its groove, two ear lugs, 2.5 mm wire bail. Orientation check: every part closed and outward | US 1-gallon can, 6.5 x 7.5 in; rims, lid and bail authored to the usual can; label extents and drip layout authored to 10708 / 10700 / 10722 |
| Colours | Film pixels hue-classified on each can, then one factor x1.30 that brings can 1's white lid (srgb 167/163/161) to albedo 0.85. Can 1: red paint 125/53/55, blue label 95/106/143, bare metal authored silver 0.78 (10708). Can 2: label 32/70/87 and cream paint 143/128/87 (10722), can body 140/122/96 (10700) | `spec/dressing/traps.json` `colours`; film lighting is unknown, so these are tints, not albedos |
| Mass | 5.2 kg | 3.785 L latex paint at ~1.3 kg/L + ~0.3 kg can |
| Rope | 8 mm cotton line, **1.509 m** from the tie point to the bail (was 1.409; user walk note Oct 16: "slightly lower") | film: white braided cord |
| Can centre at the bottom of the arc | **1.55 m above the step-4 tread** (was 1.65): mouth/chin of a 1.80 m adult. Same can: 1.73 m above step 3 (forehead), 1.37 m above step 5 (chest). At rest it hangs with its centre 2.262 m and its bottom 2.167 m above the ground floor | step 4 tread is 0.712 m above the ground floor; the film hits fall on steps 3-5 |
| Pivot to can centre | 1.684 m | rope + bail rise + half the can |
| Release | rope taut and horizontal toward the landing (90 deg), can held upright, let go | the film's drop from rail height (10700-10702). A throw from the rail itself reaches the same height with a jerk when the rope catches, so 90 deg is the upper bound |
| Dummy | capsule 1.80 x 0.40 m, kinematic, climbs at 0.6 m/s from x 7.2 to step 4's centre | adult bandit; ~2 steps/s |

## Physics design (and why)
- **Rope = one distance limit**, not a chain of bodies. A `ConfigurableJoint` on the can with all three linear axes `Limited` is a
  sphere of radius = rope length round the tie point: hard, no spring, no bounce. The rope goes slack but never stretches. A 5 kg
  can on a ~0.05 kg rope is a 100:1 mass ratio. A chain of jointed rope segments at the project's 50 Hz (`Time.fixedDeltaTime`
  0.02, default solver 6/1) stretches and jitters under that ratio, and the rope's own mass changes the swing by under 1%.
- **The rope you see** is a verlet line (24 segments, ends pinned to the tie point and the bail, visual only). It is drawn straight
  when taut and sags when slack.
- **Wrapping:** the tie point sits just outside the gallery floor's edge. When the can swings in under the gallery, the rope wraps
  that edge, so the limit moves to the edge with the rope that is left (1.509 - 1.126 = 0.38 m). The can then strikes the foyer
  ceiling, as a real one would.
- **Can body:** an invisible convex cylinder collider the can's size (the model draws it), CCD `ContinuousDynamic` (the balusters are 4 cm), interpolation on, solver 12/4 (set in
  `PaintCanTrap.Setup`, because these are runtime-only properties), linear damping 0.005 (a tuning knob for air and rope-on-rail
  friction), angular damping 0.05. The bail is rigid to the can, which turns freely on the joint, so it tips and spins like 10708.
- **The player** is a `CharacterController`. It ignores the rig's colliders, and instead pushes the can at its own speed when the
  two touch, so a hanging can never blocks the stair. The can hangs 0.76 m below the upper floor; a 1.85 m capsule on step 4
  reaches it.
- **Gates:** the rig is built after every BuildWallGrid check has run, and lives on the Ignore Raycast layer (2). No walk, seam,
  z-fight, clash, casing, trim, envelope, props, leak or peek check sees it.

## Test (batch, no play mode)
`Unity -batchmode -projectPath ~/.cache/home-alone/ucopy/HomeAlone -executeMethod SpecGreybox.TrapTest -quit` writes
`spec/captures/paint-can-test.txt`, the trajectory `~/.cache/home-alone/paint-can-traj.csv` and renders in
`spec/captures/views/traps/`. Results (Oct 16):

Every row holds for EACH can (identical to the reported digits). Tests 1-3 run each can alone, because the other hangs only 2.5 cm
away and a swing across the flight would hit it.

| Check | Result (paint_can_1 and paint_can_2) |
|---|---|
| At rest 10 s | 0.00 mm drift, <= 0.01 mm/s: no jitter |
| Both at rest together, 5 s after a reset | 0.01 mm/s, 0.00 deg tilt |
| Period, 10 deg swing across the flight | 2.606 s vs 2.608 s for a simple pendulum of 1.684 m (-0.1%), over 7 periods |
| 90 deg release, time to the bottom | 0.764 s vs 0.766 s quarter period |
| Speed at the bottom | 5.02 m/s. Its centre falls 1.509 m (5.44 m/s if nothing else took energy); the rest goes into spinning the can on its bail |
| Energy | never above the start (0.00%); -23.6% after 20 s of free swinging (linear damping 0.005, a tuning knob) |
| Rope stretch | up to 14 mm (0.9%) at peak tension (real cotton line stretches a few %) |
| Hit (P pulls both back, the dummy climbs to step 4, then this can alone is let go) | **HEAD, 1.64 m above the feet, 5.01 m/s (18 km/h), 65 J, impulse 15.4 N s**, 0.72 s after letting go |
| Player climbs the walk line between the hanging cans | reaches the landing in 1.2 s; the cans are shoved aside (up to 1.4 m) and swing back |

Renders: `dangling-foyer` and `dangling-side` (both cans); per can, `held-dummy-side-<can>`, `hit-side-<can>`, `hit-foyer-<can>`, `closeup-below-<can>` (the closed bottoms) and `closeup-side-<can>` (drips, labels, bail).

## Keys (Play)
- **P**: pull BOTH cans back to the release pose and hold them.
- **L**: let go of can 1 (Marv's).
- **K**: let go of can 2 (Harry's).
- **B**: the dummy climbs flight 1 to step 4 and waits.
- **T**: reset (cans hanging at rest, dummy gone).

The keys are per can in `spec/dressing/traps.json`. The film's order is P, then L for Marv, then K for Harry; try P, B, wait until the
dummy stops, then L or K. Each hit is logged to the console (`PaintCanTrap paint_can_1: hit HEAD ... m/s, J, N s`). There is one
dummy, shared: the first can's rig owns it and walks it, and either can's hit is detected on it.

## Files
- `spec/dressing/traps.json`: data.
- `unity/HomeAlone/Assets/Scripts/PaintCanTrap.cs`: runtime.
- `unity/HomeAlone/Assets/Editor/Traps.cs`: `SpecGreybox.Traps` builder and `SpecGreybox.TrapTest`.
- `tools/house/hifi_paint_can.py` -> `PaintCan.glb`, `PaintCanSatin.glb` (registered in `tools/house/build_models.py`).
- One call in `SpecGreybox.BuildWallGrid`.

## Open
- **Release:** 90 deg here. The film's throw from the rail would land a bit softer.
- **Bandit reaction:** the dummy only stops when hit; the film's fall backward down the flight is not modelled.
- **Drips** are flat-sided strips with a square bead at the end (authored), not the film's rounded runs. The red paint skin on can 1's
  rim is complete; the film's is too. The 'SATIN' lettering is not modelled.
- **Can 2's rope length** is can 1's (not readable from the film, see above).
