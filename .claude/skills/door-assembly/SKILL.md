---
name: door-assembly
description: Build, upgrade or verify a house doorway as a cohesive carpentry assembly, including its fixed frame, moving leaf, wall-depth finishes, hardware and clearance. Use for interior/exterior doors and door quality defects.
---

# Door assembly: construct the opening as a carpenter would

User Oct19: doors must be built consistently as one cohesive assembly. Walk failures: wallpaper exposed on exterior jambs, separate inside/outside leaves, flat interior panels/hardware, jerky swing. Consistency means a shared construction method and quality bar; preserve the different reference-specific doors.

**Trigger (Oct 20, hall bath tile across its door):** anything built on a wall that has an opening (tile, wainscot, panelling, shelving, a fixture run) triggers this skill: cut it at the opening's void (lo..hi, sill or floor..head), not just at its casings, and before handover render every doorway into the changed room from the far side (the hall looking in). The build's `Opening clear check` must read 0.

Read alongside [change-gate](../change-gate/SKILL.md), [artist-pipeline](../artist-pipeline/SKILL.md), and [zfight-check](../zfight-check/SKILL.md). These retain their measurement, surface and user-acceptance requirements. Never recompile scripts/reload Play during the user's walk; prepare the source correction for afterward.

## Establish the opening and its owners

Use the existing measured opening as the common datum for inside model, outside model, wall cut, frame and collision. Identify the source of finished floor, wall thickness/finish faces, clear width/head, hinge side and swing. Resolve conflicts explicitly; do not enlarge openings or move the shell to fit a stock model. Log authored profiles, thicknesses and clearances in DEVIATIONS. Stock sizes are a check, not authority to override evidence.

Before modeling, draw a small plan section through a jamb and vertical section through head/threshold. Mark exterior/interior faces, leaf closed position, stops, hinge axis and finishes. Account for the complete wall depth. Reuse existing opening data and extend only missing component fields; no independently hardcoded inside/outside door positions. Trace the film/Marina references for door type, panel layout, casing, sill and hardware.

Give every physical part one owner under a logical DoorAssembly root. Multiple meshes/materials/export files are fine when driven by the same opening data:

| Fixed to building | Moves with leaf |
|---|---|
| Head and side jambs/liners, inner/outer casings, stops/rebate, threshold where present, frame glazing/sidelights/fanlight, building-mounted fittings | One leaf spanning both faces and its edges, leaf-mounted handle/lock/mail fittings, leaf-side hinge parts, leaf-mounted decorations |

Jamb-side hinge parts stay fixed; pin axes align. Paired/double-acting/sliding doors need their actual mechanism and appropriate leaf count. Do not force the single hinged entrance design onto every door.

## Fit and finish the assembly

- Frame/liners finish the wall depth; jamb legs meet the head and terminate correctly at floor/threshold. Leaf closes against its stop/rebate. A wall cut alone is not a finished doorway.
- Interior wallpaper ends at the inside casing/finish boundary. Exposed exterior jamb/head returns receive the reference's painted wood or masonry finish. Interior wallpaper can legitimately be seen through glazing; it must not wrap onto the exterior reveal.
- Assign the finish to the actual face. Remove covered faces where necessary; do not hide wallpaper or gaps with coplanar overlays. Keep casing/reveal construction consistent with the repo's opening-generated casing rules.
- The leaf has real thickness and finished hinge/latch/top/bottom edges. Both face finishes meet on that same leaf. A detached decorative outside slab is not a second door face.
- Profiles and panel fields have real relief and bevels; handles/escutcheons are shaped fittings. Apply the artist pipeline's UV density, normal/AO/roughness, restrained paint detail and triangle budget. A 4K flat colour map does not replace joinery or hardware.
- Fit hardware to its mounting surface, align spindle/latch/strike, and use one hinge datum for geometry and collision. Avoid combined opposite-side fittings that falsely span the leaf in through-surface tests; split by physical part/side where needed.
- Preserve intentional glazing and measured gaps. Do not seal a sidelight or invent a threshold for an interior door merely to hide unfinished geometry.

## Verify before handing over

Report per assembly by name; unresolved applicable failures remain failures. Existing global gates do not replace door-specific checks.

**Construction / geometry**
- Compare built dimensions and wall-cut/frame registration with the canonical opening, with explicit tolerances. Check head/jamb/threshold joins, finishes on all visible returns, no duplicate leaves or stale surround surfaces.
- Run model freshness, orientation/artist quality and existing seam/z-fight/clash gates. Add no broad exception for doors. Explain any legitimate joint using the existing gate's mechanism.
- Check fully closed, fully open and intermediate swing positions; a clean closed pose alone cannot reveal a leaf passing through a wall, frame or fitting. Frame/sidelights stay fixed; mounted decorations follow their owner once.

**Interaction / collision, for operable doors**
- Test passage with Kevin and adult capsules through the actual opening. Closed blocks; open clears. Test lock refusal, opening/closing from both sides, repeated toggles and obstruction during swing. Check for trapping/teleporting the player and stale colliders. Decorative fixed leaves should not be advertised as operable.
- Sample frame time while stationary and during complete swings at the same view. Distinguish uneven angle progression from a rendering/physics stall. Profile scene searches, transform synchronization, reflection updates and shadow redraws before choosing a fix. Do not disable needed collision/shadows just to smooth motion.

**Visible result**
- Inspect live baked day/night close views from both sides, oblique views down both jambs, and the open leaf edge/head/threshold. Include the reported walk pose. Verify painted-wood texture scale and relief, hardware shape, correct roughness and no magenta/missing materials.
- Look from inside and outside at clearances, finish transitions and fixed/moving ownership. Inspect captures, not only transform values or thumbnails. Preserve the before/after and report TRIAL until walked.

## Make repeated checks executable

When implementing this skill on a door upgrade, reuse/generalize the existing `EntranceCheck` in `SpecGreybox.FoyerInteractions.cs` into a per-assembly verification path driven by the same opening data. Add deterministic checks for the invariants above that can be computed; retain explicit visual checks for finish fidelity. Prove new checks against the known faults (wallpaper reveal, duplicated leaf, misplaced pivot, blocked open passage, missing material), then against the corrected assembly. Wire the resulting report into build/preflight as appropriate.

**Current limitation:** this skill is instructions, not an installed general-purpose automated door validator. The current entrance check covers its one leaf's closed/open ray and lock refusal; it does not certify all doors, adult clearance, materials or intermediate motion. Do not claim those checks exist or pass until implemented and run. Extend tests from demonstrated faults rather than adding a checklist that merely restates generator output.

First application: entrance reveal + swing fixes and the interior doors in `docs/WALK-FEEDBACK-2026-10-19.md`. Keep both sides tied to their real references and measured opening; use the upgraded front leaf as a finish-quality comparison, not a universal style template.
