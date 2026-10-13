# Marina ground-floor reconstruction

Authorized scope: foyer, breakfast room, kitchen, den and dining room, with the living room and empty side room needed for their connecting views. Marina Coates's Part 1 tour governs all visible choices. Deliver a separate editable Blender asset and Godot walkthrough; retain existing scenes.

Acceptance: aligned den/living/foyer/dining openings; foyer vestibule, red-carpeted turning stair, damask, white trim and console; breakfast table, glazed hutch and service stair; kitchen 477 ft² target, long blue-tiled L island, two window seats, sink/back door, dark cabinetry, ceiling beams and cookware; green furnished den; red dining room with white wainscot and glazed furniture. Ceilings remain present for eye-level renders. Materials must export, fixed furniture must collide, and all five rooms must be reachable.

Dimensions are calibrated estimates: kitchen interior target 44.315 m²; other dimensions follow the overhead's proportions and common furniture sizes. Unseen upstairs/basement connections are outside this ground-floor build. New source `tools/build_marina_interior.py`; output `art/home_alone/marina/interior.blend`, `assets/home_alone/marina/interior.glb`; scene `scenes/Marina_House_Walkthrough.tscn`. Reuse the existing movement controller and photographed oak maps. Preserve the downloaded asset unchanged.

Build: `/Applications/Blender.app/Contents/MacOS/Blender --background --python-exit-code 1 --python tools/build_marina_interior.py -- --render`

Verify: Godot import, `tools/check_marina_interior.gd`, source dimension assertions, exported image/material inspection, and eye-level Godot captures of all five rooms. Existing imported walkthrough baseline passed with 273 colliders, 0 failures.

- [x] Corrected shell, openings, stairs and plan render
- [x] Five-room furnishing and first material pass
- [x] Godot import, mesh/collision counts and foyer support check
- [x] Human-scale kitchen corrections and continuous ground-floor walking routes
- [x] Six Godot eye-level captures and updated Blender previews
- [x] Separate breakfast hutch/door/stair, enclose upper foyer and orient den seating
- [ ] Final camera matching, detailed furnishings/materials and interior lighting

2026-09-11 navigation slice: Blender coordinates `(x,y,z)` import as Godot `(x,z,-y)`. The original spawn was trapped behind the foyer console; it now starts near the entry. Replaced the disabled-physics floor check with gravity settling, a continuous route from foyer through living/den, dining, breakfast and around both sides of the kitchen island, the reverse route, solid wall/island checks and reset verification. No teleporting is used along the walking route.

Corrected kitchen furnishings that extended outside the floor, moved the sink to the rear window, aligned the L island toward the sink, lowered counters from 1.59 m to 0.92 m, added the two window seats, and cleared the circulation aisles. Dining/breakfast tables now run lengthwise. Added chair legs and separated overlapping curtain layers. Generator assertions guard countertop heights and kitchen furnishing bounds. The 477 ft² target remains a calibrated estimate, not a surveyed dimension.

Remaining fidelity work: glazed hutch doors and shelf contents, cabinet panels and tiled materials; window/back-door detailing; finer furniture profiles and upholstery; and room lighting. The saved Godot views document these limitations. This checklist supersedes the earlier claim that final visual work was complete.

Final navigation-slice verification: Marina **1,347 meshes / 245 colliders / 0 failures**; existing blockout **172 / 0**; downloaded walkthrough **273 / 0**. Six runtime captures saved and inspected. Blender rebuilt both previews and restored ceilings in the saved source.


## Geometry continuation

Reference anchors: [whole-floor overhead](../art/home_alone/references/tour/ground-floor-user.png), M18/M23 for the hutch/foyer doorway/service stair, M04/M05/M20 for the stairwell enclosure, and M08/M09/M26/M27 for den seating, desk and television shelving.

- Moved the hutch to the breakfast west wall below the foyer doorway. The doorway center is now Blender Y = 9.55 m; the service stair begins at Y = 10.4 m. Geometry assertions keep the hutch clear of the casing and the casing clear of the first step.
- Extended the breakfast rear boundary from Y = 12.7 m to 14.2 m and shortened the service stair's run from 4.15 m to 3.55 m to fit that door/hutch grouping at human scale. These are authored metric estimates, not a completed camera fit. The kitchen's 44.315 m² floor target is unchanged.
- Enclosed the foyer sides and front return up to its existing 6.7 m ceiling. Moved the console onto the right wall so the rear arch connects to breakfast. The service stair has a top landing and enclosed headroom volume; no upstairs exit is invented.
- Rotated the den sofa onto the side-window wall facing two leather chairs, added the central coffee table, and replaced the raised TV slab with shelving and a television at the middle shelf. The desk now has a supported, human-scale tabletop. Sofa/chair feet reach the floor.
- Expanded the continuous route through the rear foyer door to the service-stair foot and along the den seating aisle, retaining both directions of the existing ground-floor route. Rays against the imported collision check the upper foyer's sides, front return and ceiling. The prior model failed the blocked-arch and three missing-wall checks before this rebuild.

The next pass is detailed joinery and exportable surface materials, followed by Godot lighting. The new room dimensions still need comparison with additional matched tour cameras before being treated as final.

Geometry-pass validation: **1,413 meshes, 279 colliders, 0 failures**. The continuous route passes in both directions; upper foyer and service-stair enclosure rays pass. Six Godot captures, three Blender room comparisons and the updated plan were saved and inspected. Generation assertions, Python compilation, embedded-material inspection, document links and whitespace checks passed.

## 2026-09-11 survey supersedes the generator's dimensions

[art/home_alone/references/survey/README.md](../art/home_alone/references/survey/README.md) now holds calibrated room, opening and fixture dimensions for the ground floor, upper floor and attic. Known corrections to this model: kitchen is 5.46 × 8.08 m (wider, shorter); breakfast room is 2.53 m wide beside a 1.02 m service-stair bay; refrigerator sits in the kitchen's rear-right corner beside the window-seat wall, not free-standing; the four transverse openings sit 1.7–3.6 m behind the front wall. The upper floor does not stack on the ground floor in Marina's model and needs an authored reconciliation before it is built.
