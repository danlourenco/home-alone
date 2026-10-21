# Exterior Christmas lights: design, costs, acceptance, bake-off (Oct 21, prep only: nothing built)

Rules for agents: [.claude/skills/xmas-lights/SKILL.md](../.claude/skills/xmas-lights/SKILL.md). Checker:
`tools/house/xmas_lights_check.py` (`--selftest`, `--film`, `--scene`, `RUN.png [--sheet OUT.jpg]`).

## 1. What the film shows (measured, not eyeballed)

The authority is film 5545 (McCallister front, night). Frames 10 and 11581 add to it. 11581 is the **Murphys'** house, not ours.
All numbers come from `xmas_lights_check.py --film` and the one-off scripts quoted below, on the first two upper front windows right of the
den. Their bulb loop is a known **1.02 x 1.51 m** (0.86 x 1.34 m opening, `exterior_shell.py` UPW_LIST, plus the strand's 0.08 m
offset), which gives the ruler in metres.

| quantity | film 5545 | ours today (NB9, front6399 night) | note |
|---|---|---|---|
| strand pitch | **0.21 m** (22 and 26 bulbs per loop) | 0.055 m built (92 per loop); 0.117 m visible, about half the bulbs alias away | between the stock 6 in (15 cm) and 12 in (30 cm) stringers [S12]; 8 in appears only in blog claims. Built to the film's 0.21 m (film first). Not 30 cm |
| glow diameter (half max) | **5.4 cm** | 2.1 cm (one pixel) | a C7 is 2.2 cm. The rest is the lens and film halation |
| halo radius (15 % of peak) | **11 cm** | 1.1 cm | ours has no halo |
| halo colour (shoulder) | warm: (R-B)/sum 0.106 | 0.019 (white) | see colour below |
| glow / brick luminance | **7.4** | 28 | our brick is too dark, with no spill |
| brick R/B under the strands | **2.1** (warm red-brown) | 1.5 (blue-violet) | the spill warms the brick |
| twinkle | **none**: per-bulb peak variation 0.9 % median (p90 2.3 %) across 5543-5550 (same shot, about 0.5 s apart) | steady | McCallister lights are steady |
| colours | **one warm white** on the house, shrubs and trees | warm/dim/bright tints | the 5-colour mix is the Murphys' (11581) and the street's |

**Colour.** Isolated bulbs (the left tree, 78 bulbs; the shrubs, 341; `--film-extra`), measured on the halo shoulder in linear light minus the local
background: **(1.00, 0.50-0.53, 0.33-0.35)**. A blackbody under a D65 white point (Planck x CIE 1931 fit, D65 sRGB) is 2400 K
(1, 0.36, 0.05) and 2700 K (1, 0.42, 0.10): much more orange. Night exteriors were shot on tungsten-balanced stock, so 2400-2700 K bulbs
read warm-white with an amber shoulder. **Target the film's pixels, not the Kelvin:** emissive linear (1.0, 0.53, 0.32). Today's
(1, 0.78, 0.50) at 2500 nits clips all three channels, and ACES then desaturates the result to white. The cores in 5545 sit at about
sRGB (217-231, 172-180, 144-153), warm-white and not quite clipped.

**Why ours look thin, faint and cool (the root cause).** At the front6399 pose (about 25 m, 1080p, 60 degree vertical FOV), a 1.8 cm bulb
is about 0.9 px. A sub-pixel source cannot make a halo, whatever its nits. HDRP bloom spreads energy, and a 1-pixel source has
almost none to spread. TAA/STP averages such a source with its neighbours, so bulbs flicker in and out. The checker counts 39-49 visible
of 92 built. Raising the nits only makes the white dots harder. The film's halo is an optical effect, and it has to be rendered as one.

## 2. Our constraints (measured in the repo)

- 30 fps floor (33.3 ms) at full screen 2048x1152 with STP@100 % (PERFORMANCE.md BUDGET, fs-aa). Night today: street 35-36 fps
  (about 28 ms), foyer 36, hall 45. **5 % = about 1.4 ms** at street night.
- HDRP deferred. 123 real-time lights at front6399 night, 60 shadowed (cap 60). LampFit fits interior ranges.
- Night look (`Assets/Settings/ExteriorNight.asset`, `SpecGreybox.ExteriorRealism.cs` ExteriorLook):
  - Exposure **Automatic, 5.6-12 EV100**, metering 2. With EV 5.6, scene white = 1.2 x 2^5.6 = **58 nits** maps to 1.0.
  - Bloom **intensity 0.8, scatter 0.78, threshold 0.3**.
  - Tonemapping **ACES** (default profile, mode 2).
  - Volumetric fog, mean free path 110 m.
  - No lens flares: ScreenSpaceLensFlare 0 and no LensFlareComponentSRP (VehicleProbe readout).
- Today's bulbs:
  - window loops: about 1,212 bulbs, 38.8 k faces, in the exterior GLB (`exterior_shell.py` bulb_loop, `EX_Bulb*`);
  - shrubs: 2,977 boxwood plus the other shrubs' bulbs (`SpecGreybox.Shell.cs` Bulbs: 36-triangle ellipsoids, combined per tint);
  - neighbourhood: 1,329 C7s in 5 colours (`nb_house.py` -> `<lot>_xmas.json` -> `SpecGreybox.Neighborhood.cs`);
  - **35 `ShrubGlow` real-time lights** (unshadowed, one per lit shrub).
- GPU Resident Drawer is OFF: it was measured 7-10 % slower here (PERFORMANCE.md). Batches and draw calls read 0 on Metal; set-pass
  calls and triangles are the counters we get.

## 3. The design

Four layers, each one doing the part it does best and cheapest:

| layer | what | how | why this and not the alternative |
|---|---|---|---|
| 1 bulb | C7 at the film's pitch, warm white | chunked static mesh, vertex colour, one shared Lit material, LODs | the shape by day; the clipped core at night |
| 2 glow | the film's 5 cm glow and 11 cm halo, at any distance | billboard glow cards: one static mesh per chunk, unlit additive, exposure-compensated, low-res transparent | the only layer that can give a sub-pixel source a defined halo |
| 3 bloom | the wide soft veil | the existing night Bloom, unchanged | free: it is already paid for |
| 4 spill | warm brick, snow and leaves | a pool of 24 unshadowed lights on the exterior layer, plus emissive decals behind each window loop; a bake later if picked | the film's brick ratio; the pool replaces 35 ShrubGlow lights |

### 3.1 Bulb mesh (Blender generator, artist-pipeline)
- **C7 teardrop**, 2.2 cm wide x 4.5 cm with a **green socket** (2.4 x 1.6 cm) and clip. The film's era is smooth, coated warm-white
  glass. Faceted "strawberry" C7/C9s are later, so a faceted C9 is not the film's.
- Strand wire: the existing dark green `EX_Wire`, a 3 mm tube.
- **LOD0** (under 4 m): about 60 triangles (bulb 48, socket 12), 12-sided.
- **LOD1** (4-15 m): 12 triangles, no socket.
- **LOD2** (over 15 m): nothing; the card carries the bulb. In variant A (no cards), LOD2 is LOD1.
- **Chunks:** one mesh per strand group of about 4 m (a window loop, an eave run, one shrub), with one LODGroup per chunk. About 40-60
  chunks for the house and yard, and 1 per neighbour lot.
- **Per-bulb data in vertex colour:** rgb = tint, a = intensity, so the Murphys' 5-colour mix shares the material.
- **ONE shared material:** a Shader Graph HDRP Lit reading Vertex Color into Emission (SRP Batcher compatible, no MaterialPropertyBlock).
  Emission is physical, in nits, Exposure Weight 1 [S1]. A 5 W C7 gives **10 lm at 2700 K** [S12]. Over about 20 cm2 of glass,
  Lambertian, that is 10 / (pi x 0.0020) = **about 1,600 nits** (use 1,200-2,000, jittered), so a bulb is 20-35x scene white at
  EV 5.6. The core clips, as in the film. Today's 2,000-2,500 nits are already physical: the nits were never the problem.
  - The colour is (1, 0.53, 0.32) x intensity, with alpha 0.7-1.0 jittered (film: dim and bright neighbours).
  - Day: base colour = coated glass, emission off through HouseNightMode's glow list, as today.
- **Departure from "instancing over combined meshes" (AGENTS.md):** Unity's manual advises against GPU instancing meshes under
  256 vertices: the GPU can't spread the work, and it recommends packing them into one buffer instead [S6c]. A bulb is about 40 vertices.
  GPU Resident Drawer is off here (measured slower). So chunked static meshes are the Unity-sanctioned choice. Measure the instanced
  path anyway as variant `xinst=1` (Graphics.RenderMeshInstanced, a per-instance colour from a StructuredBuffer read through
  a Shader Graph Custom Function node on Instance ID: the one place the unity `shader-graph-create-custom-node` skill applies).

### 3.2 Glow cards (the halo)
- Per bulb, a quad of 4 vertices in the chunk's card mesh. Each vertex stores the bulb centre (position), the corner (UV0 = plus or
  minus 1) and the tint (vertex colour).
- The vertex stage billboards it: `centre + (camRight*u + camUp*v) * r`, where `r = max(0.11 m, 3 px x pixel size at depth)`. Cards
  therefore keep the film's 11 cm halo up close and a pixel floor at distance, which also ends the aliasing dropouts.
- The pixel stage is analytic, with no texture: `I = core * exp(-d^2 / 0.18^2) + halo / (1 + (d / 0.35)^2 * 8)` over d in 0-1.
  Out = tint x I x k x **Exposure node (Inverse Current Exposure Multiplier)**. The card's output is therefore in exposed units:
  the peak sits at about 1.5 and the shoulder at about 0.4 on screen at ANY EV. That is the emission level "set by maths relative to the
  night EV": `nits = target x 1.2 x 2^EV100` is what the node does each frame, so auto exposure can't wash the halos out or blow them up.
- Unlit, additive, transparent. **Low Resolution** transparent pass (quarter pixels; HDRP upsamples depth-aware). Soft depth fade over
  0.1 m (Scene Depth node), so a card never cuts a hard line into the brick or a leaf.
- **Near fade 3-5 m:** up close the bulb mesh is resolved and bloom does the halo. This also caps overdraw: one shrub at 1 m would
  otherwise be about 200 cards of 50 k px.
- **Mesh bounds inflated by r_max** (the vertex shader moves vertices off the CPU's bounds).
- Optional star glint (5545's 4-point stars on the topiary spirals): a cross term in the same shader on bulbs whose alpha exceeds 0.95
  (about 3 %).
- No LensFlare components: Lens Flare (SRP) occlusion is CPU-sampled per flare [S3]. The screen-space lens flare override
  (it runs off the bloom buffer; the Samples setting has "a big impact on performance" [S3]) is a global look change for another A/B.
- Prior art: GTA V draws "every single small light spot" as a quad with a 32x32 texture, heavily batched into instanced geometry,
  and distant cars as 2 headlight sprites [S8a]. That is this layer.
- VFX Graph was rejected for these: they are static points. VFX Graph adds compute dispatches, bounds and sorting each frame for
  nothing [S5]. Use VFX Graph only if a twinkle or chase pattern is ever wanted, and the film says it isn't.

### 3.3 Bloom
Unchanged (0.8 / 0.78 / 0.3). The threshold is in gamma space [S2]: 0.3 already lets every clipped bulb core bloom. Leave High Quality
Prefiltering on the list as a cheap extra variant (`xbloomhq=1`): HDRP says it cuts the flicker of small bright objects at a cost [S2]. The cards supply the defined halo, so bloom does not have to be pushed. Pushing bloom would veil the whole
night frame (the windows, the lamp posts).

### 3.4 Spill (brick, snow, leaves)
- **Pool of 24 real lights:** Point, unshadowed, LightLayer = exterior only (`SpecGreybox.LayerOutside` renderers), range 1.6-2.5 m, about
  100-300 lm each (a loop of 22-26 C7s at 10 lm [S12]; a light lights only renderers on a matching layer [S4]).
  - They are placed at precomputed **clusters** (one per window loop, eave run of about 3 m, and lit shrub; each carrying the
    strand's summed flux).
  - `XmasLightPool.cs` picks the 24 nearest clusters in view every 0.25 s and fades a light in or out over 0.5 s (no popping).
  - **It retires the 35 `ShrubGlow` lights**, so the real-time light count goes DOWN by 11.
- **Emissive decals** behind each window loop: about 30 projectors, one shared material, an analytic soft rectangular ring in the
  decal's emissive (Affect Emissive: an additive contribution, opaque decals only; same-material decals are instanced [S7]),
  exposure-weighted. They give the rim glow on the brick at 0.3 m that 2 m lights spread too
  wide, at a cost that doesn't depend on light count [S7].
- **If C is picked,** the shipping form of the pool can be **baked**: the same clusters as Baked lights in the Night/NightFilm scenarios,
  APV at its probe spacing, zero runtime cost. That costs a bake and loses the specular on wet snow, so it is a later A/B, not a guess.
  Emissive bulbs alone are a poor bake source: they are tiny, so the progressive lightmapper finds them only by chance (noise). Also,
  no HDRP 17 page found says emissive surfaces bake into APV: the docs describe Baked emission for lightmaps and static objects [S1].
  Use Baked lights.

### 3.5 Colour per house
- McCallister (house, shrubs, trees): one warm white, (1, 0.53, 0.32), intensity jitter 0.7-1.0.
- Murphys and the street: the existing 5-colour index, with colours to be sampled from 11581 the same way (the next checker frame).

### 3.6 Cost estimate (2048x1152, M3 Pro, at street night of about 28 ms)

| piece | load | estimate | reasoning |
|---|---|---|---|
| bulb meshes | about 5-6 k bulbs; most at LOD1/2: about 100-200 k triangles, 40-60 chunks | **0.05-0.15 ms**, about 0 net | today's bulbs are already about 250 k triangles; window loops drop 4x (0.055 -> 0.21 m pitch); 17.5 M triangles in the frame |
| glow cards | about 5 k quads; at 25 m a card is about 9-12 px across (about 0.6 M px at full resolution, 0.15 M at low res) | **0.2-0.5 ms** | unlit additive, no light loop; the near fade caps the worst case; the low-res pass has a fixed upsample of about 0.1-0.2 ms if nothing else uses it |
| bloom | unchanged | 0 | |
| pool, 24 lights | unshadowed, small range, exterior layer only | **-0.1 to +0.1 ms** | replaces 35 ShrubGlow lights with the same or larger footprint |
| decals, 30 emissive | small screen area at street distance | **0.1-0.3 ms** | the emissive decal pass, one material |
| draw calls | (bulb + wire + card) x about 50 chunks = 150 (`DRAWS_MAX`); one shader each, SRP Batcher | **0.1 ms** CPU render thread | |
| **total C** | | **about 0.5-1.1 ms = 2-4 % FPS** at street night | under the 5 % budget, to be proved by the bake-off |

## 4. Acceptance criteria (measurable; the checker fails today's look)

1. **Film match** (`xmas_lights_check.py <night PNG>`, front6399 pose; any pose with QUADS for the two windows works). Pass band ×film:
   pitch 0.8-1.25, glow 0.65-1.5, halo 0.6-1.6, warmth +-0.05, glow/brick 0.6-1.6, brick R/B 0.75-1.33. **6/6 required.**
   - The selftest proves the bands: the film at our pose's scale (0.67x) still passes 6/6; the dense white dots and NB9 fail.
   - **Today (NB9): 0/6 FAIL** (`spec/captures/perf/xmas/nb9-front6399.txt`, sheet `nb9-front6399-vs-5545.jpg`). NB8 scores 1/6:
     only brick R/B passes.
   - Framing: front6399 is film 6399's solved camera (a day frame). No night film frame is solved, so the metrics are in metres on
     the window rulers and do not need the same framing (scale-checked in the selftest). A front5545 pose (exterior_film_fit.py on
     5545) would add a direct side-by-side for the user. It is optional; it isn't needed for the score.
2. **FPS:** at most 5 % below base at street, foyer, walk0645 and front6399, night (`perf_probe.sh gate` rules; report FPS with ms).
3. **Practice:**
   - `xmas_lights_check.py --scene`: strand Lights ≤ 24 and strand renderers ≤ 150. **Today: FAIL** (35 ShrubGlow lights).
   - `unity_practices.py`: 0 new failures. csc_check clean.
   - One shared material for all bulbs and one for all cards (checked by name in the build log: `XmasLights: N chunks, M bulbs, 1+1
     materials`). No per-bulb GameObject.

## 5. Bake-off: one build, PerfProbe variants (prepared here; build when the machine is free)

The build generates every layer. The variants switch them live, so there is no rebuild between them. Base = today's look (`xmas=old`).

| variant | contents | for |
|---|---|---|
| `xmas=old` (base) | today's bulbs, ShrubGlow lights | the before |
| `xmas=A` | new C7 meshes at 0.21 m, film colour, physical emission + existing bloom | the cheapest; does bloom alone reach the film? (expected: no, halo fails) |
| `xmas=B` | A + glow cards | the recommended look |
| `xmas=C` | B + pool of 24 + emissive decals (ShrubGlow off) | the recommended full set |
| `xmas=C+xdecal=0`, `xmas=C+xpool=0` | attribution | which spill does the work |
| `xmas=B+xinst=1` | bulbs drawn instanced | the AGENTS.md instancing rule, measured |

```
HA_PERF_ARGS='-perfab -perfdn night -perfrounds 1 -perfposes street,foyer,walk0645,front6399 -perfvariants xmas=A;xmas=B;xmas=C;xmas=C+xdecal=0;xmas=C+xpool=0;xmas=B+xinst=1' tools/house/perf_probe.sh run xmas-bakeoff
for v in A1 B1 C1 D1 E1 F1 G1; do uv run -q --with numpy --with pillow python -I tools/house/xmas_lights_check.py ~/.cache/home-alone-perf/runs/xmas-bakeoff/front6399-night-$v.png --sheet spec/captures/perf/xmas/bakeoff-$v.jpg; done
```

The sheet is pose rows x variant columns, FPS on each tile (perf_probe.sh), plus the checker's score per variant at front6399. The user
picks.

**Code to write (when the build is free; the decoration lane, plus generators):**
- `tools/house/hifi_xmas_bulb.py` (Blender: C7 + socket, LOD0/1, artist-pipeline gate);
- `tools/house/xmas_strands.py` (pitch 0.21 m loops from UPW_LIST/OPEN/dormers/eaves, the shrub and tree points from today's
  generators, clusters for the pool -> `spec/dressing/xmas.json`);
- `Editor/SpecGreybox.Xmas.cs` (chunks, LODGroups, the card meshes, decals, the old set kept under `xmas=old`);
- `Shaders/XmasBulb.shadergraph`, `XmasGlowCard.shadergraph`;
- `Scripts/XmasLightPool.cs`;
- PerfProbe keys `xmas`, `xdecal`, `xpool`, `xinst`.

## 6. Unity plugin skills (checked, `unity/0.1.6-beta/skills`)
- **Apply:** `unity-cli` (live preview of card k and colour in the open editor; the project already drives it), and
  `shader-graph-create-custom-node`, only for the instanced variant's StructuredBuffer read.
- **Don't apply:**
  - `urp-postprocessing`, `migrate-birp-to-urp`, `validate-urp-render-graph-renderer-feature`: URP only; we are HDRP.
  - `optimize-web`: WebGL.
  - the 2D, tilemap, sprite and UI skills; audio, IAP, multiplayer, Vivox, LevelPlay, localization, navigation and physics.
  - `build-live-game`, `new-unity-project`, `unity-package-management`: nothing to add here.

## 7. Community tools (ideas, licences)
- **FlexiCurve (RED_SIM)** [S9]
  - Free and open source (a permissive, MIT-style licence; mark modified versions).
  - Installs through UPM git or VRChat VCC.
  - Features: curve points snap to world geometry with Ctrl+click; bulbs scattered along a wire; light animations; static batchable
    meshes.
  - **Pipeline not stated** (VRChat-oriented, so Built-in is likely; HDRP unverified). Not on the Asset Store.
  - Worth taking: the snap-to-surface idea, for hand-placed runs (trees, porch rail swags). Our strands come from the spec
    (`xmas_strands.py`), so they need no editor tool. Its animated patterns aren't needed: the film's lights are steady.
- **"Xmas Lights Free Pack":** not found on the Asset Store under that name (three searches). Nothing to evaluate. Send the link if
  you have it.
- **Christmas Light System and Framework** (301645, Golem Kin Games, $8.99) [S11]
  - **Built-in only; URP and HDRP marked "Not compatible".**
  - Features: line-only, lights-only and combined modes; synced and unsynced colour cycling; patterns; intensity pulsing.
  - Ideas only. Nothing in it beats the design above for HDRP, so there is **no purchase**.

## Sources (fetched Oct 21; HDRP / VFX Graph pages are 17.0.4, manual pages 6000.0)
- [S1] HDRP Lit inspector, emission (Nits/EV100, Exposure Weight, GI Realtime/Baked/None):
  https://docs.unity3d.com/Packages/com.unity.render-pipelines.high-definition@17.0/manual/lit-material-inspector-reference.html ;
  emissive GI (static objects, probes for dynamic objects): https://docs.unity3d.com/6000.0/Documentation/Manual/lighting-emissive-materials.html
- [S2] HDRP Bloom (threshold in gamma space; HQ prefiltering 13 samples, less flicker from small bright objects; half/quarter):
  https://docs.unity3d.com/Packages/com.unity.render-pipelines.high-definition@17.0/manual/Post-Processing-Bloom.html
- [S3] Lens Flare (SRP) (depth occlusion, CPU sample count):
  https://docs.unity3d.com/Packages/com.unity.render-pipelines.high-definition@17.0/manual/shared/lens-flare/lens-flare-srp-reference.html ;
  frame setting Lens Flare Data Driven: https://docs.unity3d.com/Packages/com.unity.render-pipelines.high-definition@17.0/manual/frame-settings-reference.html ;
  screen-space lens flare: https://docs.unity3d.com/Packages/com.unity.render-pipelines.high-definition@17.0/manual/shared/lens-flare/reference-screen-space-lens-flare.html
- [S4] Rendering/Light Layers (first 16 layers; a light lights only matching renderers):
  https://docs.unity3d.com/Packages/com.unity.render-pipelines.high-definition@17.0/manual/Rendering-Layers.html ;
  HDRP asset light limits: https://docs.unity3d.com/Packages/com.unity.render-pipelines.high-definition@17.0/manual/HDRP-Asset.html (no
  defaults on the page; 512 punctual on screen and 63 per FPTL tile are from older source and forum posts, not confirmed for 17);
  deferred vs forward ("deferred ... faster in most scenarios ... multiple local Lights"):
  https://docs.unity3d.com/Packages/com.unity.render-pipelines.high-definition@17.0/manual/Forward-And-Deferred-Rendering.html
- [S5] VFX Graph outputs (unlit/lit quads, soft particles, sorting cost):
  https://docs.unity3d.com/Packages/com.unity.visualeffectgraph@17.0/manual/Context-OutputPrimitive.html ,
  https://docs.unity3d.com/Packages/com.unity.visualeffectgraph@17.0/manual/Context-OutputSharedSettings.html ; requirements (compute):
  https://docs.unity3d.com/Packages/com.unity.visualeffectgraph@17.0/manual/System-Requirements.html
- [S6] GPU Resident Drawer (BRG, DOTS-instancing shaders, no MaterialPropertyBlock):
  https://docs.unity3d.com/Packages/com.unity.render-pipelines.high-definition@17.0/manual/gpu-resident-drawer.html ,
  https://docs.unity3d.com/Packages/com.unity.render-pipelines.high-definition@17.0/manual/make-object-compatible-gpu-rendering.html ;
  choosing a draw-call method ("Avoid using the MaterialPropertyBlock API in URP and HDRP"):
  https://docs.unity3d.com/6000.0/Documentation/Manual/optimizing-draw-calls-choose-method.html ;
  SRP Batcher incompatibility: https://docs.unity3d.com/6000.0/Documentation/Manual/SRPBatcher-Incompatible.html ;
  RenderMeshInstanced (1023/511 per call): https://docs.unity3d.com/6000.0/Documentation/ScriptReference/Graphics.RenderMeshInstanced.html ;
  [S6c] instancing troubleshooting (don't instance meshes under 256 vertices; put the data in one buffer):
  https://docs.unity3d.com/Manual/gpu-instancing-troubleshoot.html
- [S7] HDRP decals (instanced with a shared material; Affect Emissive additive, opaque only):
  https://docs.unity3d.com/Packages/com.unity.render-pipelines.high-definition@17.0/manual/understand-decals.html ,
  https://docs.unity3d.com/Packages/com.unity.render-pipelines.high-definition@17.0/manual/decal-material-inspector-reference.html
- [S8] Shipped games and talks:
  - [S8a] GTA V light spots as batched 32x32 quads: https://www.adriancourreges.com/blog/2015/11/02/gta-v-graphics-study-part-2/ ;
    sprite vs image flares: https://www.adriancourreges.com/blog/2015/11/02/gta-v-graphics-study-part-3/
  - Persson, Practical Clustered Shading (Just Cause 3): https://www.humus.name/Articles/PracticalClusteredShading.pdf
  - Lagarde and de Rousiers, Moving Frostbite to PBR (emissive and the physical camera behind HDRP's nits/EV100):
    https://www.ea.com/frostbite/news/moving-frostbite-to-pb
  - Unreal Niagara light renderer (keep particle lights few and small):
    https://dev.epicgames.com/documentation/en-us/unreal-engine/render-module-reference-for-niagara-effects-in-unreal-engine
- [S9] FlexiCurve: https://github.com/REDSIM/FlexiCurve , https://booth.pm/en/items/7676455
- [S11] Christmas Light System and Framework: https://assetstore.unity.com/packages/tools/level-design/christmas-lights-christmas-light-system-and-framework-301645
- [S12] Bulbs:
  - C7 / C9 sizes and wattage: https://blog.1000bulbs.com/home/c7-vs-c9-christmas-lights
  - C7 5 W, 10 lm, 2700 K, 0.88 in: https://grandbrass.com/5-watt-c7-incandescent-1000-average-rated-hours-10-lumens-candelabra-base-120-volt-2-card/
  - C9 7 W, 30 lm, 2600 K: https://lightbulbsurplus.com/sunlite-01315-su-7c9-cl-25pk/
  - 12 in reels: https://www.bestbuy.ca/en-ca/product/novelty-lights-500-foot-c9-christmas-stringer-bulk-reel-green-wire-12-spacing-intermediate-base-c9-e17-spt-1-8-amp-wire/17154138
- Film measurements: `xmas_lights_check.py --film` (geometry and ratios) and `--film-extra` (colour on 78 + 341 isolated bulbs;
  steadiness on 910 bulbs over 5543-5550).
