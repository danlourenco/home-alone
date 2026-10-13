# Night lighting reference review — 2026-09-12

[Video: Pietro Chiovaro, I Remade the Home Alone House in Blender](https://www.youtube.com/watch?v=pBYY_bOJq4I).
Creator description specifies Blender 4.1, Cycles and Poly Haven textures. It links [this exact Parade reference](https://parade.com/.image/t_share/MTkwNTgwODMzNDk3ODUxMDA1/home-alone-house.jpg) supplied by the user and [ArtStation breakdown](https://www.artstation.com/artwork/1xoW5e).

Access limits: full video download returned HTTP403; no English captions available. Reviewed metadata and four preview storyboard contact sheets (0,18,21,24), including final render frames, not the entire motion tutorial. ArtStation breakdown also unavailable. Exact shader nodes, wattages, exposure and render settings cannot be established from these previews.

Observed: matching reference behind initial model, modeled layered cornices/trim, brick textures, illuminated windows, extensive planting and trees. Final frames show dark roof/trees, warm window rectangles, small decorative lights, local pools of light, and foreground out-of-focus highlights. Parade photo itself is not snowy; winter snow is a project adaptation.

Proposed Unity sequence (not implemented):
1. A separate night preset with restrained ambient illumination and controlled exposure; preserve daytime toggle.
2. Warm room lighting visible through existing windows, emissive bulb geometry plus a small number of lights to illuminate surfaces. Avoid flattening all windows into white panels where players can see through them.
3. Entry lantern and window/hedge string lights, keeping dark roof and shadowed recesses. Verify light spill onto trim, brick, steps and snow.
4. Baked indirect light where supported by existing meshes/UVs, reflection probes and selected shadow-casting lights; test budget in walkthrough. Cycles is an offline renderer, not evidence of equivalent real-time performance.
5. Refine roughness/normal maps, contact detail, restrained bloom; replace angular backdrop trees and simple neighboring facades for close scrutiny. Snow should pick up adjacent warm light with cooler unlit areas; that is a proposed adaptation, not a measurement from Parade.

Local HDRP documentation consulted: Post-Processing-Bloom.md (bright-area halo, not surface illumination), Reflection-Probes-Intro.md (surroundings captured for material reflections). No claim that bloom alone supplies realistic lighting. No night changes applied during neighborhood work.

## Implemented first pass

`ExteriorNight.cs` builds a separate night layer with fixed exposure 1, ACES, restrained bloom, cool directional fill, warm room lights, entry lantern and front/dormer decorative bulbs. `HouseNightMode` toggles N and restores captured foyer daytime light states. No GI bake or detailed materials overhaul yet; grouped lights approximate illumination. Garden strings were omitted because there are no suitable detailed planting assets to support them. Night is the saved preview mode.

`FrontWindows.cs` now maps 75 window sections: nine main front, three dormers, wing groups, side/rear/service windows and three sloped roof panes. Name remains historical; all elevations are covered by its opening list. Ivory modeled frames/sills/muntins and transparent HDRP glazing replace wholly contained original window triangles in copied render meshes. Source GLB and original colliders retained. Roof window source renderers object3009/3011/3013/3015 are disabled; their replacements retain the adopted roof-window configuration, which is not established by the real-house front photo. Less-visible rear pane patterns and retained GLB opening dimensions remain provisional; this is not a surveyed replica.

Root cause: imported texture has alpha-zero panes, but glTF shader alphaCutoff was zero on the inspected original window; panes rendered as black surfaces. Replacement glazing avoids that shader. Main photo comparison supports different tall lower casement and upper sash patterns; detailed sash hardware and beveled moldings remain future refinement.

Checks: CheckFrontWindows (75), CheckExteriorNight (day/night round trip and no lighting colliders), CheckIntactMainStairs, CheckWinterNeighborhood, CheckKevinBedroom and CheckParentsEnsuite pass. Day front, night front/dormers and night rear/side captures inspected. Normal 75-degree walkthrough camera restored after captures. No measured frame-time/performance target established yet.

## Exterior flicker and porch clearance correction

User reported exterior flicker and low hanging porch light. Corrected overlapping generated frame joints and adjacent bank frames; `WindowMeshClip.cs` now subtracts oriented opening boxes from crossing triangles instead of only discarding wholly contained triangles. Interpolates UVs, normals/tangents and colors; source GLB and collision remain unchanged. `CheckWindowClipping` verifies removed area and UV preservation for vertical and sloped cases. `CheckFrontWindows` now rejects overlapping solid frame joints across all 75 assemblies. Both pass, as do night toggle and stair/exterior walking checks.

Camera anti-aliasing was None; saved TemporalAntialiasing to reduce texture/thin-edge motion shimmer. Near/far clipping unchanged. Raised porch lantern 0.90 m: bottom about 3.88 world Y, approximately 2.57 m above entrance floor. Shortened chain to 4.35–4.65 Y, moved light to 4.10 Y and disabled cage mesh shadow casting to avoid oversized fixture silhouette. Captures exterior-flicker-fixed.png and window-joints-fixed.png inspected. Static captures cannot prove every movement artifact is gone.

A broad inline geometry audit stalled Unity; forced close was required after normal close timed out. Saved scene reopened successfully. Avoid huge inline eval loops; use compiled bounded checks. Recovery scene was retained. Walkthrough restored near original exterior position after verification.

## Confirmed remaining flicker: point-light shadows

User reported severe exterior flicker remained after geometric cleanup. Live A/B disabled only point-light shadows, leaving geometry and camera unchanged. User confirmed twice that flicker stopped. This isolates the remaining artifact to point-light shadows; the prior geometry fix was not sufficient.

Saved the exact confirmed configuration: all scene point-light shadows disabled, directional moon shadows retained. `FoyerLamp` now creates unshadowed practical/fill lights; `StabilizeHousePointLights` applies the policy to existing lights, and `CheckExteriorNight` rejects active shadow-casting point lights. The tradeoff is no point-light occlusion: warm lights can leak through walls. Do not call this a completed physically accurate night solution.

Likely contributing risk (not independently proven as sole cause): dozens of point lights requesting six shadow maps each, with HDRP Max Shadows on Screen 128 and a 4096 atlas using dynamic rescale. Exact atlas overflow versus other shadow behavior was not isolated. Reintroducing a bounded/cached/baked lighting solution requires a separate moving-view comparison before replacing this stable configuration. No atlas settings changed during the confirmed fix.
