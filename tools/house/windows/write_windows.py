import json, sys
from pathlib import Path
R = Path(sys.argv[1])
OV_UP = "overhead sfm-work/rooms/girls/all/images/f_00041.jpg (Part 2 0:50)"
OV_GR = "overhead sfm-work/ground/overhead_994.jpg (Part 1 16:34)"
def W(room, name, side, frac, width, sill, head, width_source, source, confidence, kind="window", edge=None):
    d = {"room": room, "name": name, "side": side}
    if edge is not None: d["edge"] = edge
    d.update({"centre_frac": frac, "width_m": width, "sill_m": sill, "head_m": head, "kind": kind,
              "width_source": width_source, "source": source, "confidence": confidence})
    return d
SH_UP = "sill/head assumed = Buzz measured (0.81/2.15)"
up = [
 W("parents_bedroom", "side_bank", "z_min", 0.50, 3.30, 0.81, 2.15, "overhead blind band x 880-1060 px over a 282 px face (5.28 m wall); valance/rod 843-1065 not counted",
   f"{OV_UP}: top-wall face, glass band x 880-1060 between face corners 826/1108 at window height (wall top 822/1113 less parallax). Part 2 240 s: multi-unit bank with swag sheers, ends ~0.5-0.8 m short of the screen corner. {SH_UP}", "low-medium"),
 W("parents_bedroom", "front_twin", "x_max", 0.615, 1.54, 0.81, 2.15, "joint perspective fit: twin glass span 0.415 of the wall (sash ~0.71 m each, cf. Buzz 0.72)",
   f"Part 2 182 s (sashes 260-500/510-800 px, far corner 1105) + 240 s (screen corner 872, sashes 1150-1320/1395-1650): joint 1-D projective fit, residuals <=18 px (scratchpad parents_xmax.py). Overhead face hidden behind the screen. {SH_UP}", "low", edge=1),
 W("parents_bath", "rear", "x_min", 0.697, 0.60, 0.54, 2.15, "ASSUMED 0.60: drapes hide the casing; >=0.37 m glass visible (209 s)",
   "Part 2 209 s (face-on: vanity-side corner 610, drapes 845-1135, first picture 1228 px) + 213 s (pictures 785-1378, tub-side corner 1775), chained at the drape-to-picture gap: centre 0.303 of the wall from the vanity (z_max) end. Sill 0.54 = 209 s glass bottom at the 2.50 m ceiling scale; head ASSUMED 2.15 (swag hides it, glass top >=2.04). Overhead face unreadable here", "medium-low"),
 W("kevin_jeff_room", "front_dresser_side", "x_max", 0.20, 0.60, 0.82, 2.20, "estimated 0.60: glass >=0.48 m at 318 px/m (356 s) plus sash stiles; equal-width fit gives 0.52",
   f"Part 2 356 s: corners 735/1895 px, glass 848-945 & 1350-1505, rods 772-1035 & 1243-1650; equal-width projective fit -> centres 0.20/0.70 (glass and rods agree to 0.01). {OV_UP}: curtain strips y 283-350 -> 0.199 (agrees). Sill 0.82/head 2.20 measured in 356 s at the 2.31 m ceiling", "medium"),
 W("kevin_jeff_room", "front_desk_side", "x_max", 0.70, 0.60, 0.82, 2.20, "as front_dresser_side",
   f"Part 2 356 s (as front_dresser_side): 0.70. DISAGREES with {OV_UP}: curtain strip y 395-472 -> 0.79-0.81 (its lower end runs under the z_max wall top, occluded). Frame chosen: in-room view, both windows and the corner in one image; not averaged", "low"),
 W("hall_bath", "front", "x_max", 0.515, 0.72, 0.81, 2.15, "ASSUMED = Buzz window (curtains hide the casing)",
   f"{OV_UP}: right-wall face, curtained window y 552-620 px (glass 580-597) between face ends 486/680. Part 2 450-470 s: one window on this wall, by the toilet. {SH_UP}", "medium"),
 W("girls_room_a", "rear", "x_min", 0.66, 0.72, 0.81, 2.15, "ASSUMED = Buzz window",
   f"{OV_UP}: left-wall face, white sash frames y ~400-445 px (centre 424) between face corners 345/464 at window height; desk and chair occlude. Not toured. {SH_UP}", "low"),
 W("girls_room_b", "rear_front_side", "x_min", 0.25, 0.72, 0.81, 2.15, "ASSUMED = Buzz window (curtain rods 72-77 px = ~1.1 m incl. curtains)",
   f"{OV_UP}: left-wall face, rod y 733-805 / glass 758-780 (centre 769) between face corners 698/982 at window height. Rear wall is the authored one (DEVIATIONS 32): window rides the built wall. Never toured. {SH_UP}", "medium-low"),
 W("girls_room_b", "rear_side_end", "x_min", 0.859, 0.72, 0.81, 2.15, "ASSUMED = Buzz window",
   f"{OV_UP}: rod y 904-981 / glass 928-956 (centre 942) on the same face. {SH_UP}", "medium-low"),
]
gr = [
 W("den", "side_twin", "z_max", 0.651, 2.30, 0.53, 2.15, "glass 0.77 of the valance (556 s) x valance 3.07 m (overhead curtain run 190 px of a 427 px face)",
   f"{OV_GR}: left-wall face, curtain run y 650-840 px (centre 745) between face ends 467/894 at window height; Part 1 556 s face-on: wide twin unit, centre ~2.0 m from the front corner (overhead 2.4 m). Sill 0.53 measured 556 s (8 ft wall scale); head ASSUMED 2.15 (valance hides it; glass top >=1.86)", "medium"),
 W("den", "front_wide", "x_max", 0.525, 2.55, 0.53, 2.15, "curtain hem strip 194 px of 244 px (3.71 m wall) = 2.95 m incl. drapes x glass/valance 0.86 (586 s)",
   f"{OV_GR}: hem/stool strip x 261-455 px on the front wall (trace 486->242) -> 0.525 from the living-side end; Part 1 586 s: ~0.3-0.45 m plain wall at the living-side corner, glass runs nearly to the side corner (556 s). Sill ASSUMED = side window (586 s reads ~0.45); head ASSUMED 2.15", "medium-low"),
 W("living_room", "rear_den_side", "x_min", 0.871, 0.52, 0.82, 2.15, "glass between drapes, 458 s at wall-width scale (lower bound: drapes may hide the casing)",
   f"Part 1 458 s face-on: corners 612/1490, glass 675-775 px -> 0.129 from the den end. {OV_GR}: drape group x 565-625 on the rear face (corners 565/807 at window height) -> 0.124 (agrees). Head 2.17 measured 458 s; sill ASSUMED 0.82 (tree/chair hide it)", "medium"),
 W("living_room", "rear_foyer_side", "x_min", 0.151, 0.52, 0.82, 2.15, "as rear_den_side (glass 1305-1410 px)",
   f"Part 1 458 s: glass 1305-1410 px -> 0.849 from the den end; {OV_GR}: drape group 740-795 -> 0.835 (agrees). Sill ASSUMED 0.82", "medium"),
 W("living_room", "front_french_foyer_side", "x_max", 0.304, 0.75, 0.0, 2.03, "glazed pair 437-622 px of a 1235 px wall (4.5 m) = 0.67 m + frame",
   f"Part 1 438 s face-on: corners 155/1390, door pair 437-622 px (knobs, floor length) -> 0.304 from the foyer end. {OV_GR}: floor strip x 550-640 (centre 595) -> 0.317 (agrees; door spacing 114 px both). Head ASSUMED 2.03 (80 in; valance hides it, >=1.80 visible)", "medium", kind="door_glazed"),
 W("living_room", "front_french_den_side", "x_max", 0.683, 0.75, 0.0, 2.03, "as front_french_foyer_side (912-1085 px)",
   f"Part 1 438 s: 912-1085 px -> 0.683; {OV_GR}: strip 670-770 (centre 720) -> 0.733. Frame chosen (in-room, face-on); head ASSUMED 2.03", "medium", kind="door_glazed"),
 W("dining_room", "front_french_sunroom_side", "x_max", 0.375, 0.75, 0.0, 2.03, "ASSUMED = living front French doors",
   f"{OV_GR}: front-wall floor strip x 1230-1290 (centre 1260) on trace 1065->1377 -> 0.375 from the sunroom end (0.30 on the floor-level corners 1062/1345). Part 1 214 s: glazed French pair with knobs and sheers on this wall (seen through the foyer doors). Head ASSUMED 2.03", "low-medium", kind="door_glazed"),
 W("dining_room", "front_french_foyer_side", "x_max", 0.798, 0.75, 0.0, 2.03, "ASSUMED = living front French doors",
   f"{OV_GR}: strip x 1098-1158 (centre 1128) -> 0.798 (0.767 on floor-level corners). Head ASSUMED 2.03", "low-medium", kind="door_glazed"),
 W("kitchen", "back_door", "x_min", 0.789, 0.82, 0.0, 2.03, "door slab 54 px of the 232 px face (4.20 m) = 0.98 m incl. casing, less 2 x 0.08",
   f"{OV_GR}: rear-wall face, half-glazed back door x 1260-1314 (glass 1280-1300, red curtains) between face ends 1238/1470 -> 0.211 from the high-z end. Part 1 945 s / 1096 s: half-lite door with red side curtains at this end. Head = 80 in door (the scale)", "medium", kind="door_glazed", edge=0),
 W("kitchen", "sink", "x_min", 0.341, 0.75, 1.05, 2.03, "glass+frame 153 px at door-casing scale (1096 s)",
   f"{OV_GR}: window frame x 1362-1422 (panes 1372-1410) on the same face -> 0.659 from the high-z end; Part 1 1096 s face-on: door-to-window 1.71 m at door-casing scale vs overhead 1.88 m. Sill 1.05 measured 1096 s (80 in door scale); head 2.03 ASSUMED (valance hides; glass top >=1.92)", "medium", edge=0),
 W("kitchen", "side_rear", "z_min", 0.18, 0.72, 1.05, 2.03, "ASSUMED = Buzz window",
   f"{OV_GR}: light feature on the right-wall face y 165-200 px, face ends 118/470 at window height. Part 1 945 s/1096 s: a window just past the oven column at the rear corner (frame suggests ~1.05 m from the corner vs overhead 1.35 m). Sill ASSUMED = sink window", "low", edge=1),
 W("kitchen", "side_seat", "z_min", 0.60, 1.20, 1.05, 2.03, "ASSUMED twin unit (945 s: about twice the rear window)",
   f"{OV_GR}: red window-seat cushion on the right wall y 315-345 px -> 0.60. Part 1 945 s / 896 s: large window over the counter with a cushioned seat. Sill/head ASSUMED", "low", edge=1),
 W("kitchen", "side_front", "z_min", 0.85, 0.72, 0.82, 2.03, "ASSUMED = Buzz window",
   "Part 1 896 s looking +x along the right wall: a smaller window past the seat window, ~1 m short of the breakfast-end wall (pantry). Position read by eye from one oblique frame; not visible in the overhead", "low", edge=1),
 W("kitchen", "breakfast_rear", "x_min", 0.537, 0.80, 0.82, 2.15, "panes 41 px of a 136 px face (2.73 m wall); valance 64 px",
   f"{OV_GR}: breakfast-area rear-wall face, red valance x 1134-1198, panes 1140-1181 (centre 1163) between face ends 1100/1236 -> 0.537 from the low-z end. Part 1 928-934 s: window with red valance in the breakfast area. Sill/head ASSUMED", "medium", edge=8),
 W("kitchen", "side_upper", "z_max", 0.44, 0.72, 0.82, 2.15, "ASSUMED = Buzz window",
   f"{OV_GR}: white window on the EXTERIOR face of the kitchen's upper side wall (x 1190-1210, y ~120-180 px) between face ends ~70/250. Not checked in a tour frame", "low", edge=9),
]
p = R / "measurements/windows/upstairs.json"
d = json.loads(p.read_text())
d["windows"] = [w for w in d["windows"] if w["room"] == "buzz_room"] + up
d["inventory_note"] = ("Non-Buzz windows (Oct 15 inventory): positions from Marina's overheads (fractions of a wall face between its corners at "
    "window height) cross-checked against tour frames where a room is filmed facing the wall. 'confidence' and 'source' say which; "
    "ASSUMED values are marked. Not added: attic-stair/hall (no windows seen); girls_room_b side wall (none visible).")
p.write_text(json.dumps(d, indent=1) + "\n")
g = {"note": d["note"].split(" Written by")[0] + ". Written by hand from the Oct 15 window inventory (overhead + Part 1 frames); sources per window.",
     "not_here": {"sunroom": "sealed, never seen (DEVIATIONS 33): Marina's sunroom is glazed on its outer walls (two banks of 4 tall windows on the right wall in the ground overhead, light patches on the lawn) - not built",
                  "foyer landing window": "built as foyer dressing (tools/house/foyer_dressing.py, 312 s), not cut here",
                  "front door + sidelights": "built as foyer dressing (foyer_dressing.py, 203 s); the leaf itself is solid panels",
                  "dining->sunroom French doors": "interior, a closed prop door in ground-doors.json (fake_door)"},
     "windows": gr}
(R / "measurements/windows/ground.json").write_text(json.dumps(g, indent=1) + "\n")
print(len(up), len(gr))
