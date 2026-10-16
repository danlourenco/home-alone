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
6. **Lighting** from the stills: every fixture placed where the frames show it, warm, with fixed exposure (next for the foyer).

## Traps hit in the foyer (each cost the user a walk)
| Trap | Fix |
|---|---|
| Old pieces still drawn over the new model (grey-box `MainStair/*` AND `Dressing/*`: runner, handrail, newels, `bottom_step_bullnose`, tree boxes) | Hide by name across the whole scene (`FindObjectsByType`), list both parents; log what is hidden; probe the area for remaining renderers |
| Placed a wall panel at the plan's wall face; the visible face was 7 cm proud (a wall layer z 11.43-11.50 beside the flight) | Probe the renderers at the spot (`r.bounds.Intersects`) and use the face actually drawn; never assume the plan face |
| Z-fighting: a panel coplanar with an existing wall (under the landing) | Never overlay where a wall already exists; offset new faces >= 1 cm from any existing face |
| Single-sided panels wound wrong (spec -> Blender is a reflection: faces reversed on build) = invisible | Thin panels get both windings; then check them in a render |
| Per-step boxes for a stringer gave a stepped bottom edge ("this wall is a mess") | Build boards as one polygon: stepped top, straight edge parallel to the pitch |
| Baluster tops poked through the handrail (they ended at the grey-box's flat per-tread caps) | Derive dependent parts from the NEW geometry (top = rail line at that x minus the rail's half-depth) |
| A sweep path with a duplicate point (ZeroDivision) | Dedupe path points before sweeping |
| Floor read sky-blue (glossy wood, no reflection probe) | Smoothness <= 0.3 until the room has reflection probes |
| Wood looked grey: texture picked by name | Pick by measured mean albedo vs the colour sampled from Marina's frames, then look at it |
| A "fixed" view checked from a guessed camera; a camera inside geometry | `tools/house/note_views.py` renders each walk note from its own pose; close-up cameras stand in the open room |
| A missing piece the reference has (bullnose first step, raking wainscot) | Walk the reference sheet element by element before handing over |

## Gate before the user sees it
1. Walk/seam/leak/peek gates unchanged (`spec/captures/walk-test-wallgrid.txt`).
2. Every walk note in the room re-rendered from its own pose (note_views.py) and looked at next to the user's screenshot.
3. A render of each changed element from a camera in the open room, and a matched Marina/film view, looked at.
4. Load into the user's editor (memory load-scene-for-walk) and say what changed and what is still authored.
