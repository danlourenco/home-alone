Latest walkthrough update: 18 door leaves and their 18 handles are hidden in the Unity scene at the user's request, retaining frames and the original GLB. Active colliders: 273. Spawn and 11 stair checkpoints pass, plus 15 foyer–breakfast–kitchen round-trip checkpoints. Other room routes remain unverified. R returns to this scene's entrance.

# Intact GLB baseline audit

User decision: use HOME_ALONE_FINAL.glb as the cohesive architectural base; Marina supplies textures, furnishing and recognizable details. Keep custom blockouts separate and superseded.

The original GLB and Unity import are byte-identical (SHA1 `483ae5da33fce6d17082408d4821664932537c42`). The importer contains 309 meshes; its anonymous object names require geometry-based identification. Existing exterior processing clipped interiors only in generated scenes; the source is intact.

| Feature | Intact model, native units (approximate) | At former 0.83 shell scale | Custom blockout |
| --- | ---: | ---: | ---: |
| Main tread span | 2.11 | 1.75 | 1.50 |
| Lower flight run | 3.92 | 3.25 | 4.80 |
| Ground to rear landing | 3.14 | 2.61 | 2.68 |
| Ground to upper floor | 3.91 | 3.25 | 3.35 |

These values come from planar surfaces and repeated tread geometry in the intact mesh, not a survey of the physical house. The main flight is identified near Blender X -0.94..1.17, Y 4.15..8.07. Its ground floor is near Z 1.31, rear landing near 4.45 and upper floor near 5.22. The old 0.83 scale is reproduced only to compare our earlier assumptions; it is not adopted as an accurate unit conversion. The custom flight was much longer/shallower, despite similar total rise at that scale.

[Native floor sections](native-floor-sections.png) show walls, openings and balustrade intersections at heights 2.5 and 5.7. Distant site geometry is outside the plotted region. The upper section has a broad cross-hall, front bathroom/closet grouping, rear stair landing and side return; these should be inspected in 3D rather than inferred anew from room rectangles.

`inventory.json` records object bounds and horizontal surface areas; `triangles.npz` preserves the extracted native triangles. `tools/survey/audit_intact_glb.py` regenerates those two files in Blender without saving or modifying the source model.

The Unity reference builder preserves native scale and geometry, adds mesh collision, and places the avatar in the foyer. Doors are retained intact. Runtime verification: 309 mesh colliders; 11 continuous checkpoints pass up the main flight, across the rear landing, along the side hall and cross-hall, then back downstairs. The source rooms and doors are unmodified; those other routes are not yet all tested. The initial reference build failed before colliders were added, causing the reported fall; the builder now uses Unity-aware null checks and validates floor collision before saving.

Current scene: `Assets/Scenes/IntactHouseReference.unity`. [Foyer capture](../../../../unity/HomeAlone/Assets/Captures/IntactHouseReference/foyer.png).
