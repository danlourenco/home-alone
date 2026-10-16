---
name: room-upgrade
description: How to take a room from grey-box to a detailed look (models, trim, textures, props, lighting) without breaking the walkable build. Use for ANY visual upgrade of a room (foyer done first, Oct 15 2026). Lists the traps the foyer hit, each with its fix.
---

# room-upgrade: detail over the grey-box, checked from the user's eyes

The grey-box stays the walking and collision layer: its walk, seam, leak and peek gates must not change. The look is a separate
layer of models generated from the same spec, plus real textures, props and lights. Reference: the foyer (Oct 15),
`tools/house/hifi_foyer.py` (stair, trim), `tools/house/hifi_props.py` (props), `SpecGreybox.HiFiStair` / `TexMat`.

## Order of work (the user's eye ranks it: lighting > materials > models)
1. **Reference sheet first.** Pull Marina's frames and film stills of the room (the room's `art/home_alone/references/*` and
   `spec/captures/compare-marina/web/*-ref.jpg`). List every element: trim (baseboard, wainscot height and cap, chair/dado rail,
   raking rails on stair walls, crown, casings), fixtures (chandelier, sconces, switch plates), furniture, wallpaper, floor.
2. **Geometry from the spec, in Blender** (`/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P <script>`), one
   script per room, every position read from `spec/house_spec*.json` / `spec/dressing/*.json`; only profiles are authored.
3. **Unity:** instantiate the .glb under the right floor root, remap materials by name, strip its colliders, hide the grey-box AND
   dressing renderers it replaces (keep their colliders).
4. **Textures:** Poly Haven (CC0, user OK Oct 15) via `TexMat(name, id, tint, tile_m, smoothness)`: world-space triplanar, no UVs.
5. **Props:** Poly Haven models sized and placed by the dressing piece's measured footprint and height (`hifi_props.py`).
6. **Lighting** from the stills, then `-executeMethod BakeLighting.Bake` (bounce light): every fixture placed where the frames show it (`tools/house/hifi_lights.py` models, `SpecGreybox.HiFiLights` places them with 2700 K point lights), checked from the frame's own view.

## Traps hit in the foyer (each cost the user a walk)
| Trap | Fix |
|---|---|
| Old pieces still drawn over the new model (grey-box `MainStair/*` AND `Dressing/*`: runner, handrail, newels, `bottom_step_bullnose`, tree boxes) | Hide by name across the whole scene (`FindObjectsByType`), list both parents; log what is hidden; probe the area for remaining renderers |
| Placed a wall panel at the plan's wall face; the visible face was 7 cm proud (a wall layer z 11.43-11.50 beside the flight) | Probe the renderers at the spot (`r.bounds.Intersects`) and use the face actually drawn; never assume the plan face |
| Z-fighting: a panel coplanar with an existing wall (under the landing); a raking wainscot 4 mm off the paper; the whole stair inside-out | Follow `.claude/skills/zfight-check`: overlays >= 1 cm proud, faces via `Part.face`, the build's z-fight gate at 0 and `glb_orientation.py` passing |
| Single-sided panels wound wrong = invisible (the spec -> Blender map is a rotation, not a reflection; `hifi_lib` reversed every face until Oct 16) | `Part.face(points, toward)` orients every flat face; never wind by hand |
| Per-step boxes for a stringer gave a stepped bottom edge ("this wall is a mess") | Build boards as one polygon: stepped top, straight edge parallel to the pitch |
| Baluster tops poked through the handrail (they ended at the grey-box's flat per-tread caps) | Derive dependent parts from the NEW geometry (top = rail line at that x minus the rail's half-depth) |
| A sweep path with a duplicate point (ZeroDivision) | Dedupe path points before sweeping |
| Floor read sky-blue (glossy wood, no reflection probe) | Smoothness <= 0.3 until the room has reflection probes |
| Wood looked grey: texture picked by name | Pick by measured mean albedo vs the colour sampled from Marina's frames, then look at it |
| A "fixed" view checked from a guessed camera; a camera inside geometry | `tools/house/note_views.py` renders each walk note from its own pose; close-up cameras stand in the open room |
| A missing piece the reference has (bullnose first step, raking wainscot) | Walk the reference sheet element by element before handing over |
| Wallpaper: Marina's paper is a different colourway from the film's | Use the film's (user, Oct 15): `tools/house/film_wallpaper.py` cuts one repeat from a frontal daylight still by 2-D autocorrelation (mask fixtures or cut the tile above them, never patch: patches show as blocks), flattens the light, and the loader tiles it at its own width and height (a square triplanar scale stretched it 9%) |
| Fixture placed from a misread frame (sconces first put on the foyer face beside the inner opening; the film has them on the vestibule's front wall by the sidelights) | Place each fixture from the frame where its wall's other features (door, sidelight, print) are all in view, and check that frame's view after building |
| Hanging fixture put in the wrong room (lantern in the vestibule; the film's chain shows against the foyer wall ABOVE the opening's head, so it hangs on the foyer side) | Read depth from occlusion: what passes in front of an opening's head is on the near side. Film shots "from inside the door" may be from outside it (film-1616 camera x 12.3): check a calibrated camera before inferring a second fixture; look for frames where the supposed fixture should show and does not (384, 3175, IMG_3843 ruled out a stair-well chandelier) |
| Flat, washed-out interior (no bounce light; HDRP ray tracing is DirectX 12 only, not on the Mac) | `BakeLighting.Bake` after each build: Adaptive Probe Volume over the house, lights Mixed (Baked Indirect), sky through the windows; ~20 s on the M3 |
| A wall's fittings judged by eye from a still ("sconces should be outside the vestibule") | Solve the film camera from known corners (`tools/house/film_solve_10248.py`: door leaf, sidelights, jamb edges), draw our outlines over the still, back-project the film's fittings, then render ours from that camera beside the still |
| Trim laid per wall ran behind doors, casings and the stair's skirt | Record trim runs while building walls and lay them last (`SpecGreybox.LayTrim`), sampled every 2 cm against the surfaces of what is on the wall; a baseboard 1 cm shallower than the skirt it meets |
| Full-metal brass read black (nothing bright to reflect) | Part-metallic brass (`BrassMat`) plus baked reflection probes (`BakeLighting`) |
| An editor command times out (the open editor is blocked by a dialog) | Copy the build into the project and commit anyway; ask the user to dismiss the dialog, then load |

## Gate before the user sees it
1. Walk/seam/leak/peek gates unchanged and the z-fight gate at 0 (`spec/captures/walk-test-wallgrid.txt`); `glb_orientation.py` exits 0.
2. Every walk note in the room re-rendered from its own pose (note_views.py) and looked at next to the user's screenshot.
3. A render of each changed element from a camera in the open room, and a matched Marina/film view, looked at.
4. Load into the user's editor (memory load-scene-for-walk) and say what changed and what is still authored.
