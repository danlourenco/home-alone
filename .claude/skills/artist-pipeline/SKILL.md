---
name: artist-pipeline
description: Build generated models (doors, windows, arches, mouldings, cabinets, tables, built-ins) to near-AAA quality the way a game artist would: true curves, bevelled edges, high-poly detail baked to normal/AO/curvature maps, map-driven PBR materials with wear and grime, LODs, checked by a quality gate. Use for ANY new or rebuilt hifi_*.py model, and whenever the user says a generated piece looks cheap, jagged, flat or "just triangles".
---

# artist-pipeline: generated models at the quality of bought ones

Why (Oct 16, user): "the stuff that you generated is decent, but comes nowhere near to the quality of most of the imported
artifacts ... the arch is jagged; poinsettias ... essentially just a bunch of triangles. I want the depth of a near AAA game, at
least Rainbow Six Siege quality." Generated pieces had razor edges, stepped curves (ArchTop built from slices), no baked detail
and one tinted texture. Bought assets differ by process, not by magic: this skill is that process, scripted in headless Blender.

## Decide first: generate, buy or scan
- **Generate** (this skill): architecture and joinery that must fit measured openings and runs: doors, windows, casings, arches,
  mouldings, stairs, cabinets, built-ins, tables, simple case furniture. Done properly this reaches AAA.
- **Buy or download scans**: organic and soft hero pieces: plants, trees, upholstered furniture, fabric-heavy items, sculpted
  ornaments, food. Poly Haven / free Megascans on Fab (licence checked: public repo) or a store purchase (gitignored). Never ship
  a scripted plant or sofa as final.
- Measurement rules don't change: every size from the spec/film/Marina measurements (room-upgrade, change-gate).

## The pipeline (tools/house/hifi_lib.py helpers; one hifi_*.py per piece)
1. **Low-poly game mesh**, real-world metres:
   - Curves are true curves: segment count from the arc's size so the facet chord error is <= 1 mm at 1 m viewing distance
     (an arch, round top, turned leg or cove is never built from stepped boxes or slices).
   - Every hard edge bevelled: 2-6 mm on joinery and trim, 1-2 mm on hardware, 3-5 mm on plaster/arch corners; use weighted
     normals (Blender "Weighted Normal" modifier) so big faces stay flat and edges catch highlights.
   - Clean manifold, outward normals (glb_orientation), no faces closer than 1 cm to the surface behind (zfight-check).
2. **High-poly detail mesh** (only for baking): subdivision + real profiles (panel raise, mitred mouldings, plaster unevenness,
   wood end grain, screw heads, keyhole), small noise displacement where the material is uneven (plaster 0.5-1 mm, painted wood
   0.2 mm).
3. **Bake** high -> low in Cycles (headless): tangent-space normal (OpenGL/DirectX handedness as Unity HDRP expects), ambient
   occlusion, curvature (edge mask), thickness if translucent. Cage/ray distance set from the bevel size; check for baking
   artefacts (waviness, seams) in the output before using it.
4. **UVs and texel density**: unwrap with seams in hidden places; >= 512 px per metre for anything within arm's reach of the
   walk path (1024 px/m for hero pieces seen up close: doors, mantel, stair), packed, padded 8 px.
5. **Materials** (HDRP Lit: base colour, mask map R metal / G AO / B detail mask / A smoothness, normal):
   - Base from a CC0 scanned material (Poly Haven / ambientCG) tinted to the film's measured albedo (room-upgrade: pick by
     measured colour, never by name), at its true scale.
   - Map-driven variation: edge wear and lighter paint on convex edges from curvature, grime/darkening in crevices from AO,
     roughness variation (handled areas smoother), subtle colour variation; amount set per material (new paint: little wear;
     a 1990 family house: light wear on doors and handles, none on ceilings).
   - Detail normal/detail map for close range (wood grain, paint orange-peel, plaster).
6. **LODs**: LOD0 full, LOD1 ~50%, LOD2 ~20% (Blender decimate, normals preserved), cull distance per size; or a single LOD for
   small rooms if the triangle budget allows (state it).
7. **Export** glTF/GLB with the maps; Unity import: materials remapped to HDRP Lit with the baked maps, mipmaps on, anisotropic 8.
8. **Triangle budget: <= 150k triangles per model file** (LOD0, all its meshes; generated, bought or CC0). Detail beyond that goes
   into the baked normal map; decimate a bought model in Blender before import. The build's `Props triangle budget` line names
   every model file over it (`SpecGreybox.TriangleBudget`) and must read 0. Why (Oct 17): a 628k-triangle rug made the z-fight
   gate run 27 minutes; catch it at import, not as a hung build.

## The quality gate (build: "Quality check"; a tool tools/house/model_quality.py for the Blender side)
A generated model FAILS when it has any of:
- a curve whose facet chord error > 1 mm per metre of radius (measured on the exported mesh),
- an unbevelled convex edge longer than 5 cm (dihedral angle < 150 degrees with no bevel loop),
- no baked normal map, or a normal map that is flat (std dev of tangent normals < threshold),
- texel density < 512 px/m on a face within 3 m of the walk path,
- missing base/mask/normal maps, or a base colour outside the film-measured range for that material,
- no LODs (or no stated reason for one),
- Unity maps (Assets/Textures/Generated/<model>/<part>_{base,mask,normal,detail}.png, what SpecGreybox.BakedMat renders) missing
  or not the GLB's maps, or a detail map that takes the measured albedo outside +-2 x albedo_tol (2nd/98th percentile).
Report counts like the other gates; 0 before handing over.

## Before / after (always)
Render the piece's own close view (0.8-1.5 m) and room view, day and night, next to the film or Marina frame and the previous
build, in the live editor (batch renders lie about lighting). Say what changed; the user decides.

## Traps
| Trap | Fix |
|---|---|
| Arch built from stepped slices (SpecGreybox.ArchTop) read jagged | A true curved mesh with enough segments and a bevelled edge, generated in Blender, replacing the stepped boxes (the walk layer can keep simple colliders) |
| A single tinted texture on every face reads flat and fake | Baked normal/AO/curvature + wear/grime driven by those maps |
| Scripted organic shapes (leaves, cushions) read as triangles | Buy or scan them; scripts are for hard-surface |
| Pipeline helpers put in hifi_lib.py would stale every generated model (build_models.py hashes it into every stamp) | They live in `tools/house/hifi_pipeline.py`; a script using them lists it in its BUILDS entry (proof piece: `hifi_foyer_arch.py`) |
| AO bake had black blobs where the high-poly's noise pushed into a touching wall/landing | Displace the high-poly OUTWARD only (`displace`: mid_level 0); occluders are the real neighbours (geometry.json boxes) |
| Base colour exported black | Set a Blender image's colourspace BEFORE writing its pixels (`to_image(..., colorspace=)`) |
| Grime darkened the whole base on top of the AO map (double darkening; albedo gate failed) | Grime only in crevices: `(1 - ao)^2`; the AO map does the rest in HDRP |
| A mitred moulding's joint read as a "coarse facet" to the gate | model_quality judges facets only where the faces on both sides are about as wide (a curve); a wide flat meeting a narrow face is a crease or mitre |
| A casing inside a model fails the build's Casing check | Generated architecture is placed by the openings loop from its own cut (`SpecGreybox.ArchModel`), not as a `*_HiFi` dressing model; the build's **Arch fit** line proves every joint is on the cut (1 mm) |
| Moulding running into a neighbour (the arch's casing at the stair's flank) | Sweep the full path with a short tail, then cut it at the neighbour's plane (`to_object(..., cuts=)`, before the normals); legs only where `free()` finds a wall face with nothing in front |
| A raw-plaster scan's detail map put dark specks on painted plaster (detail albedo 0.18-0.84: paint at 0.66; the arch read dirty) | Scale the detail albedo for paint (`DETAIL_ALBEDO` 0.25 in hifi_foyer_arch.py); model_quality fails a detail map outside +-2 x albedo_tol |
| The gate judged the GLB's maps while Unity renders the PNG copies in Textures/Generated (a stale copy would pass) | model_quality's `unity` check compares them (base, normal, mask AO/smoothness) |
| Arch fit's jamb rays found no wall (they probed at the upper floor's height: the check ran with FloorY back at 0) | Probe from the arch model's own transform (`fy = g.transform.position.y`, SpecGreybox.Arch.cs) |
