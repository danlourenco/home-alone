# Marina reference interior asset

This is a separate ground-floor reconstruction generated from Marina Coates's CG tour. The editable Blender source is [interior.blend](interior.blend); the Godot asset is [interior.glb](../../../assets/home_alone/marina/interior.glb); the playable scene is [Marina_House_Walkthrough.tscn](../../../scenes/Marina_House_Walkthrough.tscn).

Launch the playable FPS walkthrough from any terminal directory:

```sh
/Applications/Godot.app/Contents/MacOS/Godot --path /Users/dlo/Dev/home-alone --scene res://scenes/Marina_House_Walkthrough.tscn
```

In the Godot editor, open `scenes/Marina_House_Walkthrough.tscn` and use **Run Current Scene (F6)**. On a Mac, use **Fn+F6** if the function keys control media. The project-wide Run button still starts the original multiplayer prototype.

Controls: **WASD** move, **mouse** look, **Shift** sprint, **Space** jump, **C/Ctrl** toggle crouch, **R** reset to the foyer. **Esc** releases the cursor; click the game to capture it again. Close the game window to exit. The service stair ends in this ground-floor model; it has no upstairs connection.

The Blender source has packed textures, per-room collections, centered mesh origins and a foyer viewport. Use **Save As** before manual modeling: the generator rebuilds `interior.blend` and its GLB output. Manual Blender edits reach Godot only after exporting the updated GLB.

The current slice establishes the foyer, living/den, dining room, breakfast room and kitchen shell, openings, windows, two stair groups, ceiling beams, large furnishings, and exported materials. The kitchen uses Marina's onscreen 477 sq ft target, blue tile, L-shaped island, and window-seat recesses. Eye-level and top-down plan renders are in this folder for visual comparison; final camera-matched dimensions remain in progress.

Build from the repository root:

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --python-exit-code 1 --python tools/build_marina_interior.py -- --render
/Applications/Godot.app/Contents/MacOS/Godot --headless --path . --editor --import --quit
/Applications/Godot.app/Contents/MacOS/Godot --headless --path . --fixed-fps 60 --script tools/check_marina_interior.gd
```

The check exercises the actual 1.8 m × 0.84 m player capsule under gravity: a clear foyer spawn, a continuous route through living/den, dining and breakfast, both kitchen aisles, and the return trip. It also checks room groups, worktop height, wall/island collision and reset. Blender `(x,y,z)` becomes Godot `(x,z,-y)`; worktops finish at 0.92 m. The kitchen floor remains a 44.315 m² estimate calibrated to Marina's 477 ft² annotation.

To regenerate the six runtime views after importing, run:

```sh
/Applications/Godot.app/Contents/MacOS/Godot --path . --fixed-fps 60 --script tools/check_marina_interior.gd -- --capture
```

Views: [foyer](godot-foyer.png), [den](godot-den.png), [dining](godot-dining.png), [breakfast](godot-breakfast.png), [kitchen toward sink](godot-kitchen.png), [kitchen reverse](godot-kitchen-reverse.png). Cameras are 1.55 m above the floor; ceilings remain visible. [Plan](plan.png) temporarily hides ceilings, beams and the upper hall to show the ground floor; the saved Blender file restores them.

This remains a furnished blockout. Glazed hutch doors, joinery, tile maps, furniture detailing and interior lighting still need fidelity work. See the [current checklist](../../../tasks/marina-interior.md). The oak floor and its normal map, foyer damask and kitchen floral image are embedded in the GLB; most other surfaces currently use plain PBR colors. Existing oak attribution is in the [parent asset notes](../README.md).

Validation on 2026-09-11: **1,347 meshes, 245 colliders, 0 failures** in the Marina check and six successful runtime captures. Existing blockout: **172 colliders, 0 failures**. Downloaded walkthrough: **273 colliders, 0 failures**. Blender generation/dimensional assertions, Python compilation, GLB material inspection and whitespace checks also passed.


The geometry continuation separates the west-wall breakfast hutch, foyer doorway and service stair; encloses the upper foyer; moves the console out of the rear passage; and places the den sofa and chairs across from each other with the TV in the rear shelving. The breakfast rear wall was extended by 1.5 m to fit that grouping; dimensions remain estimates pending a full camera fit. The service stair ends at an enclosed landing with no upstairs exit.

Blender comparison views: [foyer](blender-foyer.png), [den](blender-den.png), [breakfast](blender-breakfast.png). These show the same camera positions and look targets as the corresponding Godot captures, with diagnostic Blender lighting; they are not a final lighting match.

Geometry-pass validation: **1,413 meshes, 279 colliders, 0 failures**. The continuous route passes in both directions; upper foyer and service-stair enclosure rays pass. Six Godot captures, three Blender room comparisons and the updated plan were saved and inspected. Generation assertions, Python compilation, embedded-material inspection, document links and whitespace checks passed.
