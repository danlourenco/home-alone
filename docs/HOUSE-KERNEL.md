# Build the house like a carpenter: a design proposal

**Status:** APPROVED by the user Oct 17, 2026 (step 1 right after the rug/stair/wainscot job; the whole plan before Buzz's room;
success = fewer checks and fewer joint complaints). Was: proposal for the user's review. Nothing in it is built yet; the current pipeline stays the
authority until a step here proves itself (see "Reverting").

## The problem in one sentence

We describe the house as **pieces with coordinates** and then **check after the fact** that the pieces meet, so every
new kind of piece brings a new kind of gap, and every gap brings a new check, rule or skill trap.

Evidence from Oct 16-17:

- `spec/geometry.json` stores the 95 ground walls as axis-aligned **boxes** (`x`, `z`, `y` extents), not as walls
  with faces, ends and joints. Two boxes can overlap (flicker), stop short (gap) or meet at an angle nobody intended;
  the Seam, Z-fight, Clash and Envelope checks exist to catch that.
- Stairs, the landing, the arch, the French doors, windows and most built-ins are separate generators (26 `hifi_*.py`
  plus `SpecGreybox.*.cs` partials), each placing its parts by its own coordinates. Today's triangular stair-wainscot
  gap and the unfinished landing wainscot sit exactly where the outline-derived trim (Oct 16) stops and these
  generators start.
- The arch crown was built at 2.17 m under a 2.155 m passage ceiling. That is physically impossible, yet nothing
  refused it: the model had no idea that an opening lives in a wall under a header under a ceiling.
- The answer each time was another check or rule: about 12 build checks, change-gate rules R1-R7, verify-plan
  checkpoints, and a growing list of traps in the room-upgrade and artist-pipeline skills.

The user's rule since Oct 16 ("think like a carpenter: every joint meets by construction") was right. We applied it
as a fix in places (trim from room outlines) instead of as the way the house is represented.

## The idea: derive joints, never place them

A carpenter can't leave a gap in casing, because the casing is cut to the opening it trims. The same holds here if
every part is **computed from the part it attaches to**, in the order a house is built.

### 1. One structural model, in building order

| Stage | What it holds | Reads only |
|---|---|---|
| 1. Plan | room polygons, levels, floor and ceiling heights | measurements |
| 2. Walls | a wall **graph**: centre lines with thickness; corners and T-joints are nodes | plan |
| 3. Openings | doors, arches, windows as **features of a wall** (offset along it, width, head, sill); headers above them | walls |
| 4. Structure | stairs, landings, under-stair walls as structure that walls attach to (a stair's side is a wall face) | walls, plan |
| 5. Faces | every visible wall face, split by openings and floors, each with its room | walls, openings, structure |
| 6. Finishes | paper, paint, wainscot zones per face | faces, room finishes |
| 7. Trim | baseboard, cap rail, crown and casing as **runs along faces** (stair rakes and landing edges included); casing from each opening | faces, openings |
| 8. Furniture | placed against faces and corners ("0.10 m from the front corner along the headboard wall"), never by world position | faces |

Nothing in a later stage can name a coordinate an earlier stage didn't produce. Casing without an opening, wainscot
not on a face and a stair side that isn't a wall all become impossible to write down.

### 2. Plausibility is part of the model

Rules every builder knows, enforced when the data enters the model rather than seen in a walk:

- An opening fits in its wall: its head stays under the header, and the header under the ceiling (catches the arch).
- A door has a swing and somewhere to rest; trim it would cover is a decision recorded in its data (the French doors).
- Stair rise and run, headroom and a landing's depth fall within a carpenter's range.
- Trim runs end at a corner, an opening or another run; casing meets the baseboard by rule.
- Furniture stands on a floor, against a face, clear of door swings, inside the room.

A measurement that breaks one of these is refused with the reason, so a misread (the arch's fascia-for-crown) costs
seconds, not a build and a walk.

### 3. Checks shrink to a few invariants

What construction guarantees needs no per-case check. What stays:

- **Invariants, generic and few:** every visible face has a finish; every trim run terminates; nothing intersects;
  every room is reachable by the adult and the kid body.
- **Data checks, where construction can't help:** does a measurement read the right feature (the feature-ID step),
  does the layout match the film (a blockout overlay through the solved cameras), does it look right (the walk).

**Rule for the future:** a new check is allowed only if it is a general invariant. A fix for one incident goes into
the generator that produced it, so that class of defect can't recur. Each existing check, gate rule and skill trap
gets audited into one of three bins: *becomes a construction rule*, *stays as a data check*, *deleted*.

### 4. What this looks like in practice

- Today's two wainscot defects: fixed by stage 7 running the cap rail along the stair's wall face and the landing
  edge. No new check.
- The arch: stage 3 refuses a crown above the header; the casing question becomes "does this opening carry casing on
  this face" in its data, decided from the film.
- Buzz's room: the walls and their faces come from the graph, furniture is placed along faces in Marina's order from
  the corner, and "does the furniture fit" is a stage-8 rule (it stands inside the room, clear of swings), not a hope.

## How we get there without a rewrite

Small steps, each proving itself on the real house before the next. The wall grid already behaves like stages 1-3
for plain walls.

1. **Trim from faces, stairs and landings included** (stage 7). Fixes the current wainscot defects; proves the idea.
2. **Openings own their header, trim and limits** (stage 3 plausibility). Covers the arch and door-swing cases.
3. **Walls as a graph** behind the box export: generate the same boxes from centre lines and nodes, so joints are
   exact by construction; then retire the seam patches it makes unnecessary.
4. **Stairs and landings as structure** that walls and trim attach to (stage 4).
5. **Furniture placed relative to faces** (stage 8), starting with Buzz's room.
6. **The audit**: every check, gate rule and skill trap binned; skills rewritten to describe the model, not a list of
   past accidents.

Each step builds the house both ways and compares them before the old way is switched off.

## Reverting

Nothing here removes the safety net until it has been replaced and proven:

- **Git:** the current, accepted state is commit `41ecdd39`. The work happens on its own branch; `main` and the
  current branch keep the existing pipeline.
- **Side by side:** each step runs next to the old generator. All existing checks keep running on the new output,
  and an old check is only retired once the new construction passes it on the whole house and on the cases that
  created it (the arch picks, the wainscot gaps, the seam history).
- **Switch, not delete:** the builder takes a switch (old path / new path) per stage until the user has walked the
  new path. Turning a stage back is a one-line change and a rebuild.
- **Skills:** the current skill files stay as they are until the audit replaces them; their old versions remain in
  git history either way.

If the approach doesn't hold up, we stop at the last step that worked, flip the switches back, and keep the
skills and checks we have today.

## What it costs, and what it saves

- Steps 1-2 are about the size of the current rug job each; step 3 is the largest (the wall export behind
  everything). One agent at a time, one step per trial.
- It saves rebuilds: impossible data is refused in seconds instead of after a 7-10 minute Unity build and a walk,
  and a class of defect is closed once instead of being found room by room.
- It stops the rulebook growing. The measure of success is a **shorter** list of checks and skill traps after the
  audit than before it, with fewer walk notes about joints.

## Decisions (user, Oct 17)

1. Step 1 (trim from faces) runs as its own trial right after the rug/stair/wainscot job.
2. The plan runs before Buzz's room; Buzz is the first room built on it.
3. Success measure accepted: fewer checks and skill traps after the audit, fewer joint complaints in walks.
