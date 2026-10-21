# Performance: how to measure, what was found (perf pass, Oct 18 2026; baseline Oct 20)

## BUDGET (the gates read this table: `perf_probe.sh gate LABEL`, `unity_practices.py` shadowbudget, the build's ShadowBudget line)

**Floor (Oct 20, user): 30 fps = 33.3 ms frame MEAN at every tour pose, day and night, windowed 1920x1080 AND full screen on the 5K
Studio Display: the gate FAILS over it.** Target: 60 fps = 16.7 ms, with 3 ms held back for the neighbourhood, so the house today gets
13.7 ms: reported as OVER TARGET, not failed. Motion steps (PerfProbe `door-*`, `can-*`: 10 s after the front door opens / a paint can is
knocked) get the same floor and target and a time to rest (failed). `static-*` rows are scene/settings limits checked without a tour
(`unity_practices.py` reads their floor column); lower them when a change is accepted (never raise one to pass). First matching row wins.

| pose | floor ms (gate: 30 fps) | target ms (60 fps) | rest s |
|---|---|---|---|
| static-shadowed-lights | 60 | - | - |
| static-sun-distance | 80 | - | - |
| static-street-casters | 4100 | - | - |
| door-* | 33.3 | 13.7 | 2 |
| can-* | 33.3 | 13.7 | 10 |
| * | 33.3 | 13.7 | - |

## PERF PASS 1 (Oct 20, evening): what changed, measured in-session A/B in the standalone app

**1. Motion shadows** (user, in the app: "if i open the door or hit a paint can, the fps becomes laughable again ... it gets lousy for a
few seconds"). Every lamp whose range sphere reached a moving door / can redrew all 6 cube faces EVERY frame of the motion, lamps behind
walls and floors included. `Scripts/ShadowRefresh.cs` now queues only the lamps that can SEE the moving bounds (range, spot cone, a line
past the shadow-casting colliders) and a pump (`ShadowRefreshPump`) redraws at most 2 per frame, each at most once per 4 frames, nearest
first, plus a final at-rest redraw. The paint can snaps to sleep under ~1 cm of swing left. Gate: the build's MotionShadow lines
(`SpecGreybox.MotionShadow.cs`, batch, night, 10 s at 60 Hz; the legacy behaviour is printed beside it as "before"):

| motion | before (legacy) | after |
|---|---|---|
| front door opens | 27 lamps, max 174 faces/frame, 10710 faces | 9 lamps, max 12, 810 |
| paint can knocked 1.4 m/s | 36 lamps, mean 189 faces/frame (max 468) for 6.1 s | 17 lamps, mean 7.5 (max 12) |

Standalone (`runs/motion-ab`, `-perfab -perfposes motion -perfshadowlegacy`, 10 s means; the editor was open and busy, so absolute
numbers are inflated, the pairs are fair): can at night 380 -> 77 ms (worst seconds 470-640 -> 85), door at night 87 -> 66 (worst
second 270-380 -> 79-87), door by day 35-60 -> 32-57. Rest: door 1.0 s, can 6.2 s. PerfProbe's new motion step: `-perfposes motion`
(door day + night, can at night; JSON `rest_s`, per-frame `moving`, `shadow_lamps`).

**2. Lamp zones** (`SpecGreybox.LampZones.cs`): what remained of the motion cost was each point-lamp redraw rendering ~25 M shadow
triangles (every caster in its 7-9 m sphere, the rooms behind its walls and the yard included). Each cached lamp now casts only what a
lamp of its zone can see (HDRP shadow layers: linkShadowLayers off, 11 free rendering-layer bits; zones = agglomerative clustering by
the triangle cost of the union). Lighting layers untouched. Full redraw of the 60 lamps: 595 -> 196 M triangles (-67%; a zone per lamp
would be 154 M). PerfProbe `-perfvariants lampzones=off` is the before.

**3. Sun cascades 150 -> 80 m** (`SpecGreybox.cs` SunShadowDistance in the GreyboxVolume profile; gate static-sun-distance).
`runs/sun-ab` (clean): street day 34.2 -> 29.8 ms (-13%; tris 47.6 -> 37.9 M, casters 28.3 k -> 17.9 k), foyer 30.7 -> 30.4, attic
32.5 -> 31.3, hall 16.4 -> 16.4; PNG difference 1.2 at the street = TAA edge noise, no shadow moved
(`spec/captures/perf/street-sun-150-vs-80.jpg`, top 150 m). 60 m: street -21% but the trees' shadows on the facade change; 100 m: -7%.
Upper bounds (casters switched off, not looks): all small interior props -6..-15%, all big interior pieces -9..-15%, exterior -2..-11%.
The sun's cascades are at most ~25-30% of a day frame.

**4. Sun cull** (`SpecGreybox.SunCull.cs`): small interior pieces that no sun of any weather can reach past the walls, floors and shell,
and that no day-lit lamp sees, cast no shadows by day (`HouseNightMode.sunlessCasters`, restored at night): 970 of 2071, 1.12 M triangles
out of each cascade. Exact by construction (a point behind such a piece along a sun ray is behind the same wall). `sunless` variant = before.

## BASELINE (Oct 20, before the neighbourhood work): the local Mac test app

**App:** `~/.cache/home-alone-perf/build/HomeAlone.app` (LOCAL ONLY: it carries gitignored store assets and the unlicensed exterior
GLB; never distribute or commit it). Bundle id `com.homealone.local`, arm64 IL2CPP release, windowed 1920x1080, 3.1 GB. Built by
`tools/house/perf_probe.sh build` from an APFS clone of the MAIN project as on disk (the exterior-shrubs and trim/French-windows
TRIALs applied, the saved day/night bake, no new bake). `build dev` makes HomeAloneDev.app (development player, profiler markers).
Feel notes and M screenshots from the app go to `~/Library/Application Support/com.homealone.local/feedback` (FeelNotes.cs).

**How to read the numbers (new, Oct 20):** the player is GPU-bound at every pose, and Metal queues frames: a run alternates fast
frames (3-20 ms) with frames that block in `Gfx.WaitForPresentOnGfxThread` (25-90 ms; 25-45% of frames, tagged on 100% of them).
So the **frame MEAN is the real frame time** (1/fps); p50 understates it and the old tables' "CPU ms median" is not a frame time.
FrameTimingManager's GPU time is sparse on this Metal player (a handful of samples per 300 frames) and the profiler's "GPU Frame
Time", "Draw Calls Count" and "Batches Count" read 0 even in a development player (HDRP / SRP Batcher on Metal): set-pass calls and
triangles are the render counters we get.

Editor stopped, display awake, app frontmost (caffeinate; checked: every sample focused at 1920x1080); `rel-oct20` (release) and
`dev-oct20` (development) agree within ~3%. Foyer mirror at 512 (`-perfmirror 512`). Run JSON: `spec/captures/perf/runs/rel-oct20`.

| pose | frame mean ms (fps) | p50 | p95 | p99 | main / render thread ms | tris M | set-pass | shadow casters | rt lights (shadowed) | sys MB |
|---|---|---|---|---|---|---|---|---|---|---|
| street day | 32.1 (31) | 19.6 | 62.9 | 64.2 | 11.3 / 11.9 | 47.6 | 892 | 28318 | 17 (10) | 7170 |
| street night | 21.7 (46) | 20.3 | 43.4 | 45.2 | 8.5 / 8.2 | 15.6 | 455 | 0 | 107 (60) | 8119 |
| foyer day | 28.3 (35) | 18.5 | 56.7 | 58.5 | 8.7 / 8.9 | 31.6 | 691 | 26935 | 17 (10) | 7097 |
| foyer night | 34.2 (29) | 25.3 | 92.3 | 99.2 | 6.5 / 6.1 | 5.5 | 307 | 0 | 107 (60) | 7997 |
| living day | 10.8 (92) | 3.6 | 36.7 | 42.3 | 2.7 / 2.2 | 5.6 | 168 | 3108 | 17 (10) | 6873 |
| living night | 15.8 (63) | 4.9 | 56.6 | 72.9 | 2.7 / 1.7 | 1.6 | 71 | 0 | 107 (60) | 7268 |
| upstairs hall day | 16.2 (62) | 4.4 | 46.1 | 59.0 | 3.5 / 3.0 | 9.6 | 227 | 5270 | 17 (10) | 6882 |
| upstairs hall night | 28.9 (35) | 17.4 | 111.0 | 139.2 | 2.7 / 1.6 | 3.1 | 100 | 0 | 107 (60) | 7489 |
| attic day | 27.6 (36) | 17.0 | 55.7 | 58.0 | 11.6 / 11.9 | 39.0 | 956 | 28098 | 17 (10) | 7120 |
| attic night | 25.7 (39) | 15.9 | 51.1 | 52.6 | 8.0 / 7.4 | 14.7 | 474 | 0 | 107 (60) | 7632 |
| parents day | 13.2 (76) | 5.8 | 35.4 | 39.6 | 4.4 / 4.0 | 6.5 | 323 | 6309 | 17 (10) | 7066 |
| parents night | 16.9 (59) | 5.6 | 46.2 | 46.9 | 4.7 / 3.0 | 1.9 | 171 | 0 | 107 (60) | 8089 |
| yard day | 7.5 (133) | 2.7 | 25.8 | 35.4 | 2.0 / 1.5 | 1.8 | 93 | 966 | 17 (10) | 7080 |
| yard night | 7.8 (128) | 2.7 | 27.7 | 36.2 | 2.3 / 1.3 | 0.5 | 44 | 0 | 107 (60) | 7668 |

**Heavy-frame attribution** (`perf_probe.sh attrib dev-oct20`, perf_attrib.py): at every pose the heavy frames are the present
waits (GPU behind), with NO other named cause: no GC, no ShadowRefresh map requests, no reflection-probe/atlas updates, no APV
streaming, no light switching on those frames. So there are no hitches to fix; the cost is the steady GPU frame.

**Cost centres (ranked):**
1. **Day: sun shadow cascades + geometry.** The slow day poses are the ones with 27-28 k shadow casters and 31-48 M triangles
   (street, foyer, attic: 28-32 ms); the light day poses have 1-6 k casters and 2-10 M tris (7-16 ms). Day triangles are 3-9x
   night's at the same pose, i.e. mostly the sun's 4 cascades over 150 m (the Oct 18 open item: 80 m, interior props out of the
   cascades). The neighbourhood adds exactly this kind of load (more casters in the cascades).
2. **Night: 107 real-time lights, 60 shadowed** (was 60 / 52 on Oct 18), plus forward-lit transparents: foyer night 34 ms and
   hall night 29 ms with only 3-6 M tris. Bake the generic `Light_` fills, fit ranges to rooms, fix the cached shadow atlas
   overflow (above).
3. **Realtime planar mirror:** the foyer mirror at 1024 costs +10 ms at night and ~+17 ms by day at the foyer pose (`mirror-ab`,
   `-perfab -perfmirror 512,1024`: night 49.2 / 49.6 -> 60.7 / 58.0 ms; day 27.0 / 17.4 -> 37.4 / 41.6 ms, frame p50, Oct 20 first
   build): keep 512 (`spec/captures/perf/foyer-mirror-1024-vs-512.jpg`, left 1024, right 512: softer up close).
Memory: 6.9-8.1 GB system; player 3.1 GB, textures still dominate (item 4 below).

**Reflection probe atlas (Oct 20):** HDRP 17.6 stores each probe texture once (not per camera); a cube of face F takes
(max(F,32) x4)^2 texels (x2 from 512), a planar its resolution^2. Across a day/night switch the LRU keeps both scenarios' cubes:
live read in the editor, 61 entries = 60 x 512^2 + 1024^2, the 4096^2 atlas 100% full ("No more space in Reflection Probe Atlas").
Fix: atlas 8192x4096 (HDRP.asset `reflectionProbeTexCacheSize 536875008`; 85 -> ~170 MB VRAM, measured 85.3 MB for 4096^2) and the
foyer mirror 512. Gate: `unity_practices.py` probeatlas (static: HDRP.asset + baked Probe_*.exr + SpecGreybox*.cs planars), fails
above 85%: 4096 atlas with mirror 1024 = 105% FAIL, 512 = 100% FAIL; 8192x4096 = 50% pass. `reflectionCacheCompressed` is a no-op
in 17.6 and 128 is already the smallest cube tier.
**Ring buffer** ("Ran out of Graphics Ring Buffer space"): editor-only here; the release player has no such message and the
development player's tour logged none. If a player ever shows it: launch with `-gfx-ring-buffer-size <bytes>` (present in this
UnityPlayer.dylib).


Target: the user's 14" M3 Pro MacBook Pro (36 GB), measured in a **standalone** macOS player, not editor Play.

## How to re-measure

```
tools/house/perf_probe.sh build        # clone the MAIN project -> IL2CPP player HomeAlone.app (~19 min; HA_REUSE=1 ~3 min; `build dev`)
tools/house/perf_probe.sh attrib LABEL # heavy frames per pose and their named cause (dev player tour)
tools/house/perf_probe.sh run LABEL    # 6 poses x day/night, 300 frames each, 1920x1080 -> ~/.cache/home-alone-perf/runs/LABEL + table
tools/house/perf_probe.sh table A B    # before -> after per pose, with the mean pixel difference of the pose PNGs
tools/house/perf_probe.sh clean        # delete the clone and player (several GB)
```

- The poses are in `Assets/Scripts/PerfProbe.cs` (`POSES`): street (34, -2.7, -9.7 looking at the front), foyer, living, upstairs
  hall, attic stair head, rear yard by the treehouse. The player runs with `-perfprobe <dir>`, turns off the walk controller, and per
  pose writes JSON (CPU/GPU ms median, GPU p10, triangles, set-pass calls, shadow casters, real-time lights, memory) and a PNG.
- **Noise: the user's editor in Play shares the GPU** (run in background is on). Back-to-back runs of the same build varied up to 2x.
  Compare like with like:
  - feature cost in one session: `HA_PERF_ARGS="-perfab -perfoff ShadowMaps"` samples base, variant, base, variant at every pose
    (HDRP FrameSettingsField names). Two more knobs: `-perflightsoff Light_` (lamps by name prefix) and `-perfrange 0.7` (lamp ranges
    times F);
  - project settings (these can't be switched in a running player): build two players and run `perf_probe.sh ab NAME A.app B.app`
    (tours A B A B).
- **The display must be awake.** With it asleep or locked, FrameTimingManager returns no GPU times (`gpu_ms` null) and CPU ms drops to
  ~5. The run keeps the display awake with `caffeinate -d -u`, but that can't get past a locked screen.
- Batches and draw calls read 0 even in a development player (HDRP on Metal); gfx memory is counted only in a development player.
- Player-build traps this tool works around (in the clone only): this Unity install's Mac support has IL2CPP variations only, so the
  default Mono backend compiles against editor assemblies and fails (`PerfBuild` sets IL2CPP). The bought BankersLamp pack has an editor
  script outside an Editor folder (`RenderTextureCaptureEditor.cs`), which breaks any player build, so it is deleted from the clone.
  `Light.lightmapBakeType` is editor-only: runtime code must use `bakingOutput`.

## Before (current house, Oct 18, standalone, editor in Play alongside)

| pose | GPU ms | CPU ms | tris M | set-pass | shadow casters | real-time lights (shadowed) |
|---|---|---|---|---|---|---|
| street day | 27.7 | 22.0 | 13.10 | 268 | 8233 | 6 (4) |
| street night | 23.1 | 17.6 | 5.11 | 130 | 0 | 60 (52) |
| foyer day | 29.4 | 23.2 | 8.79 | 191 | 6800 | 6 (4) |
| foyer night | 60.1 | 34.5 | 1.90 | 77 | 0 | 60 (52) |
| living day | 29.2 | 23.3 | 12.43 | 177 | 11775 | 6 (4) |
| living night | 39.4 | 22.6 | 1.33 | 56 | 0 | 60 (52) |
| hall day | 35.1 | 26.9 | 13.87 | 233 | 12493 | 6 (4) |
| hall night | 59.1 | 35.7 | 2.93 | 92 | 0 | 60 (52) |
| attic day | 25.2 | 19.6 | 7.00 | 215 | 5372 | 6 (4) |
| attic night | 29.6 | 19.9 | 2.81 | 100 | 0 | 60 (52) |
| yard day | 38.6* | 15.3 | 1.27 | 78 | 688 | 6 (4) |
| yard night | 20.7 | 13.9 | 0.36 | 33 | 0 | 60 (52) |

GPU-bound everywhere (CPU waits on the GPU). Sys memory 4.7-5.3 GB. *outlier: the repeat run read 22.2.

## What was tried, measured A/B

| change | result | verdict |
|---|---|---|
| GPU Resident Drawer + GPU occlusion culling (HDRP.asset `gpuResidentDrawerSettings.mode 1`, `enableOcclusionCullingInCameras 1`; GraphicsSettings `m_BrgStripping 2`) | pictures identical (mean diff 0-2.5/255), triangles counted -20..-40% by day, but **GPU +7..10% slower** at 9 of 12 poses in tours A B A B | not shipped: geometry is not the bottleneck; the culling compute and depth pyramid cost more than they save |
| baked (Umbra) occlusion culling | not built: the same reason. To work it also needs every glass, sheer, ShadowsOnly and HouseSplit piece taken out of Occluder Static | skipped |
| sun shadow distance 150 -> 80 m | lost in the noise (run before the A/B tools existed) | open |
| cached punctual shadow atlas 8192 -> 16384 (HDRP.asset `cachedPunctualLightShadowAtlas`) | see below | TRIAL candidate, not applied |

In-session attribution (`-perfab -perfoff X`, GPU p10, % of frame): **shadow maps** -15..-29% of interior day frames and up to -38%
of the foyer at night. **Transparent objects** -17..-38% at night in the foyer/hall (forward-lit glass, sheers and leaves evaluate
every lamp). SSAO, contact shadows, subsurface scattering, volumetrics and post: each within ±5-10%, under the noise.

## Root cause found at night: the cached shadow atlas overflows

At night 47 shadowed lamps want **82.1 M texels** of cached punctual shadow maps (point lamp = 6 faces; tiers 256/512/1024), but the
8192² atlas holds **67.1 M** (Oct 17's audit: 58.9 M for 41 lamps, before the attic, basement, Kevin, guest and treehouse lamps).
Lamps HDRP can't place lose their shadow maps. That is the most likely cause of the unstable night frame times (foyer night
39-83 ms from run to run) and a candidate for the flicker STATUS still lists.

With a 16384 atlas (A/B, same frames) day is pixel-identical, but **night changes visibly**: hall 43% of pixels, attic 32%, living 2%.
The hall walls are brighter, and the attic stair goes dark where a lamp now casts its shadow. See
`spec/captures/perf/atlas-8192-vs-16384-night.jpg` (left 8192, right 16384). Not applied: it changes the night look the user
calibrated, and GPU timings couldn't be read (the display slept). Cost: +768 MB of GPU memory (32-bit depth). The alternative is
lower tiers: the four 1024 hero lamps take 25 M texels, so at 512 everything fits at 94%.

Run data: `spec/captures/perf/runs/` (the JSON of the before, GRD A/B and atlas A/B tours; the atlas runs have no GPU times
because the display was asleep).

The build now logs `SHADOW ATLAS OVER BUDGET` (SpecGreybox.Shadows.cs, LimitShadows) when the lamps want more than 95% of either
cached atlas. Make it a `BUDGET FAIL` once a fix is accepted.

## What's left (ranked)

1. **Night: real-time lamp count per pixel.** 60 real-time lamps, 47 of them shadowed, with ranges of 7-9 m. In the foyer view 63
   lights reach the frustum, including basement and attic lamps through floors. Options, each a visible change, so each needs the
   user's walk:
   - fix the atlas overflow (above);
   - bake the generic grey-box `Light_<room>` fills the way the day FilmFill is baked;
   - fit ranges to rooms;
   - try punctual shadow filtering Low.

   Measure each with `-perfab -perflightsoff Light_` / `-perfrange 0.7` once the display is awake.
2. **Transparents** at night: check which glass and leaves are alpha-blended where alpha clip would do.
3. **Sun shadows by day**: 5-12 k casters across 150 m and 4 cascades. Try 80 m, and keep small interior props out of the sun cascades.
4. **Textures 2.1 GB of a 3.3 GB player**, mostly uncompressed textures embedded in GLBs (glTFast imports them as RGBA32):
   LivingProps.glb 320 MB, DiningProps.glb 224 MB, mannequin 150 MB, ExteriorPlants.glb 103 MB. Fix: export the GLBs with KTX2/basis
   textures, or move the textures out to compressed PNG/JPG assets with max sizes set.
5. Editor in Play competing for the GPU: measure with the editor stopped for clean absolute numbers.

## PCSS soft shadows (Oct 18, interior-notes job; user: "can we use HDRP's high-quality soft-shadow mode where necessitated?")

HDRP's PCSS is global for punctual lights: HDRP.asset `punctualShadowFilteringQuality` 1 (Medium, PCF) -> 2 (High, PCSS). Tried and
measured, **left OFF (1)**: its night cost is not established and the one awake reading was far over the night baseline (below).
Ready for it: every lamp now has a source size, so switching the asset to 2 is the whole change (and drop the parents' dimmer). Each lamp's source size sets its penumbra (SpecGreybox.Shadows.cs `SourceRadius`: bare bulbs and under-cabinet strips 3 cm,
sconces/hurricanes/lanterns 4 cm, chandeliers 6 cm, shaded lamps 9 cm, domes and generic room lamps 12 cm; the parents' bedside lamps
12 cm and floor lamp 10 cm from their builder). The parents' 55% shadow dimmer stays while PCSS is off. Look: `spec/captures/views/interior-notes/
pcss-*-medium-vs-high.jpg` (left Medium, right High, same build): penumbrae soften (bedposts, shade cones, picture-frame shadows); the
living room's view through the den door is a little darker.

**Cost: NOT established.** Players Medium.app / PCSS.app built from the same scene (scratch home-alone-3, build 3). The display slept
through most tours (GPU ms null; CPU ms ~5 then is not a frame time), so the cross-build A/B (`runs/pcss-A1`, `pcss-B1`) is not
evidence. The one awake tour (PCSS player, in-session `-perfab`, `runs/pcss-samples-nofill`) read night GPU p10 foyer 151, hall 181,
living 72, parents 68 ms (98 real-time lights now, 56 shadowed; the Oct 18 Medium baseline above, before the exterior's lights, read
39-60 ms median); one awake Medium sample read parents-night p10 69 ms. Knobs tried in-session: PCSS samples 24/16 -> 8/8 (no change
measurable), generic `Light_` lamps without shadows (-13..-23% GPU at night, but they then light through walls: not applied).
Re-measure with the display awake and the editor stopped: `tools/house/perf_probe.sh ab pcss <Medium.app> <PCSS.app>` (build the
Medium player from the perf clone with punctualShadowFilteringQuality 1). If night GPU is no worse than Medium, set 2 and drop the
parents' `shadowDimmer = 0.55f` (SpecGreybox.Curtains.cs).
New PerfProbe knobs: `-perfpcss B,F` (PCSS sample counts in the variant), `-perfnoshadow P1,P2` (lamps by prefix lose shadows), and a
`parents` pose (the bedside-lamp view of walk note 21:16).

## Resolution A/B (Oct 20, HomeAloneRes.app: HDRP dynamic resolution + STP, clone-only; run res-ab)
Frame mean ms, 100% -> 75% -> 67%: street day 27.3 -> 32.9 -> 32.4; street night 23.9 -> 28.6 -> 28.0; foyer day 27.3 -> 31.8 -> 30.4;
foyer night 36.0 -> 37.6 -> 31.8; living day 12.4 -> 8.8 -> 8.4; living night 17.6 -> 11.0 -> 10.0. Image difference 0.5-1.8 (hard to see;
spec/captures/perf/resolution-100-75-67.jpg). Verdict: only the pixel-bound rooms (living) gain; the heavy poses get SLOWER (STP's fixed
cost) because their cost does not scale with pixels: shadow-map rendering and geometry. Not shipped; the heavy poses need geometry/shadow
work (lamp ranges per room, fewer shadowed lamps, cheaper transparents), not a lower resolution.

## Full screen 5K + render scale (Oct 20, late; user: "even better in full screen on my Studio Display, but noticeably slower")
**Shipped now:** HDRP.asset dynamic resolution ON (hardware, STP, mip bias, 33-100%); `Scripts/RenderScale.cs` drives it with a
percentage scaler (`DynamicResolutionHandler.SetDynamicResScaler`, ReturnsPercentage) and opts the main camera in below 100% (at 100%
the camera renders exactly as before: no STP pass). **P** cycles 100/75/50/38% while walking (on-screen value, saved in PlayerPrefs
`RenderScale`). Fresh-install default: `RenderScale.Default` = **50** (change the constant and rebuild, `HA_REUSE=1 perf_probe.sh build`;
a saved P choice wins over it). The old clone-only `-perfDynRes` build flag is gone.

**Tour** (`runs/fs5k-scale`, `spec/captures/perf/runs/fs5k-scale`): `HA_DISPLAY="Studio Display" HA_PERF_ARGS='-perfab -perfrounds 1
-perfposes street-day,foyer,hall-night,living-night,kitchen-night -perfvariants scale=75;scale=50;scale=38' perf_probe.sh run fs5k-scale`.
`HA_DISPLAY` reads the display's native pixels from system_profiler; PerfProbe `-perfdisplay` moves the window there and goes
FullScreenWindow. display.txt: Studio Display matched, **backbuffer 5120x2880** (Screen, currentResolution, Metal surface; not the
2560x1440 "looks like" size). Every sample focused. Editor closed, Caffeine on. (A first run while the screen was locked had 11 of 24
samples unfocused: discarded.) Internal sizes measured (ScalableBufferManager): 100% 5120x2880, 75% 3840x2160, 50% 2560x1440,
38% 2048x1152 (the hardware scaler rounds 38 to 40%).

| pose | 100% (native) | 75% | 50% | 38% |
|---|---|---|---|---|
| street day | 14.5 fps (69.0 ms) | 15.1 (66.2) | 19.6 (51.1) | 21.4 (46.8) |
| foyer day | 11.9 (84.3) | 13.7 (72.9) | 19.0 (52.7) | 21.0 (47.6) |
| foyer night | 6.4 (155.5) | 8.8 (113.2) | 14.1 (70.9) | 17.0 (58.8) |
| hall night | 6.7 (148.8) | 10.2 (98.2) | 18.0 (55.6) | 23.7 (42.2) |
| living night | 9.7 (103.1) | 14.9 (67.3) | 27.6 (36.2) | 36.8 (27.2) |
| kitchen night | 8.8 (114.1) | 10.9 (91.6) | 16.7 (60.0) | 18.8 (53.3) |

Sheet: `spec/captures/perf/fullscreen-5k-scale-100-75-50-38.jpg` (each tile: the frame, a red box, and that box at 1:1 pixels).
Look: 75 and 50 are hard to tell from native at 1:1; STP also anti-aliases (native has no AA: the fascia and window edges stair-step);
38 is a little softer on wallpaper. Image difference 0.7-3.5. Night white balance holds at every scale (frame R/B within 0.6%, e.g.
kitchen 2.852 / 2.867 / 2.870 / 2.872). **Verdict: 50% default** (about 2x native fps at night, 1.4-1.6x by day, no visible loss).
Unlike the 1080p A/B above, 5K full screen IS pixel-bound. Still far from 60 fps: 50% at 5K (2560x1440 internal) costs ~25 ms more
than the 1920x1080 window's native frame (foyer night 71 vs 34 ms): STP's 5K output and everything after it (post, UI) runs at 5K.
Next levers: STP injection point after post (`STPInjectionPoint` in HDRP.asset; post at the internal size), or full screen at the
display's "looks like" 2560x1440 size.

## 30 fps floor (Oct 20, night; user: "30 fps is the floor, 60 the target, windowed and full screen 5K")
The BUDGET table above now gates on the floor (33.3 ms mean; `perf_table.py --gate` FAILS over it) and reports the 60 fps target
column as OVER TARGET. Against the Oct 20 windowed baseline (`rel-oct20`): 1 FAIL (foyer night 34.2 ms), 9 more over target. Full
screen 5K at auto (`fs5k-scale`, 38-40%): every pose but living night misses the floor (38%: street day 46.8 ms, foyer night 58.8, hall night 42.2, kitchen night 53.3).

**Phase A, the 5K tax (prepared; tour pending the user's go).** Three levers, each a PerfProbe variant (in-session, no rebuild between):
- `inject=after` (also `dof`, `before`): STP's injection point (`RenderScale.Injection`; HDRP.asset `STPInjectionPoint` 0 = BeforePost,
  so bloom, tonemapping and the rest of post run at 5K). AfterPost runs post at the internal size; STP then upscales the tonemapped
  image. Switched at runtime through the asset's serialized settings (the public setter calls OnValidate, which re-creates HDRP).
- `screen=2560x1440`: the backbuffer at the display's "looks like" size, full screen (the OS scales it to the panel). JSON `screen` and
  `backbuffer` (Display.main.rendering size) record what the player got; the sheet scales such a frame to the panel's pixels before
  the 1:1 crop, so tiles compare the same panel area. AUTO there is 80% = 2048x1152 internal, the same as 40% of 5K.
- `scale=adaptive` (`RenderScale` mode -1, P cycles auto/adaptive/100/75/50/38): auto's size is the ceiling; per 0.5 s window, a frame
  mean over 33.3 ms steps down 5 points, under 25 ms steps up; never below ~720 px high; a step down that doesn't cut the mean by 3%
  is undone and held 30 s (STP's fixed cost in a 1080p window). JSON `frame_log.scale` is the per-frame percent.
- `-perfbasescale auto`: the base is today's shipped AUTO (default base stays 100 = native).
Tour (one session, full screen on the Studio Display; keys of one variant joined by `+`):
```
HA_DISPLAY="Studio Display" HA_PERF_ARGS='-perfab -perfrounds 1 -perfbasescale auto -perfposes street-day,foyer,hall-night,living-night,kitchen-night -perfvariants inject=after;screen=2560x1440;scale=adaptive;screen=2560x1440+inject=after;screen=2560x1440+inject=after+scale=adaptive' tools/house/perf_probe.sh run fs5k-phaseA
```
Each sample's JSON also lists the transparent materials in the camera's frustum (`transparents`: material -> renderers), the
inventory Phase B needs.

**Phase B, the night content (prepared; each its own A/B with a sheet, no visible change shipped without the user's pick):**
- transparents: `hide=T1,T2` (renderers with a material whose name contains a token switched off: the upper bound of what they cost)
  and `lowres=T1,T2|all` (HDRP's low-resolution transparent pass: quarter pixels, checkerboard depth, depth-aware upsample, so every
  lamp is evaluated for a quarter of the sheer/glass pixels; no shader variant change, only the material's render queue). Tokens
  from the Phase A `transparents` inventory (HiFi_Sheer also matches HiFi_SheerShade, the lamp shades). Windowed, night:
  `HA_PERF_ARGS='-perfab -perfdn night -perfposes foyer,hall -perfvariants hide=Sheer,Voile;hide=Glass;lowres=Sheer,Voile;lowres=all'`.
- lamp ranges per room: `fit=M`, each lamp's range = its room's extent + M m (the 90th percentile of 128 ray hits against the
  colliders: the rays out through doorways are the top 10%), never above its own range. Runtime stand-in for room bounds; the pick gets
  written into the lamp builders. `HA_PERF_ARGS='-perfab -perfdn night -perfposes foyer,hall,living,kitchen,parents -perfvariants fit=1;fit=2;range=0.7'`
  windowed, then the same with `HA_DISPLAY="Studio Display"`.

**Phase A result (Oct 21, run by the user: HomeAlonePerfA.app, `runs/fs5k-phaseA`, sheet `spec/captures/perf/fullscreen-5k-phaseA.jpg`).**
Full screen 5K, base auto 40% (2048x1152 internal). FPS (internal size):

| pose | A base | B inject=after | C 2560x1440 | D adaptive | E 2560+after | F 2560+after+adaptive |
|---|---|---|---|---|---|---|
| street-day | 20 | 18 | 17 | 17 | 17 | 17 (1920x1080) |
| street-night | 17 | 17 | 16 | 17 | 17 | 17 (1920x1080) |
| van-night | 22 | 24 | 25 | 18 | 16 | 16 (1920x1080) |
| foyer-day | 19 | 20 | 21 | 20 | 22 | 22 (1536x864) |
| foyer-night | 17 | 19 | 20 | 17 | 20 | 27 (1280x720) |
| hall-night | 24 | 27 | 27 | 24 | 27 | 27 |
| kitchen-night | 18 | 19 | 20 | 18 | 20 | 20 |
| attic-day | 16 | 16 | 16 | 16 | 16 | 15 |
| living-night | 36 | 43 | 46 | 36 | 47 | 47 |

No variant reaches the 30 fps floor except living night. **Anomaly:** the 1920x1080 window at 100% (no dynamic resolution) runs
the same street poses at 34-43 fps (NB4) and the interiors far faster, at about the same pixel count. In every dynamic-resolution
sample of a heavy pose the RENDER THREAD's busy time equals the frame (foyer night: render 56.7 ms of a 57.5 ms frame; street day
50 of 51), while without dynamic resolution it is 6-15 ms (5K native foyer night: 5.5 ms; 1080p window street day: 11). The same
happened in the 1080p window's res-ab (foyer night 75%: render 36.6 of 37.6 ms; 100%: 6.0) and fs5k-scale. Light poses (living
night) don't show it (render 2 ms). Adaptive stepped down and undid the step at most heavy poses: the cost does not follow pixels.
So the heavy-pose cost is a stall that comes with dynamic resolution (hardware DRS on Metal, STP, or render-target churn), not
pixels, post or the 5K present. Hypothesis (4), the neighbourhood's day cascades: the 1080p window draws the same 42 M triangles /
12.7 k casters at street day in 29 ms, so they are not the 5K anomaly (they do keep street day near the floor at any size).

**Diagnostic tour (prepared):** new readouts in each JSON: `dynres` (camera pixel and scaled sizes, HDCamera actual size, handler
scale and last scaled size, RTHandles max size, ScalableBufferManager factors), `mode`, `window_display`, `vsync`. New variant keys:
`dynres=soft|hard`, `upscaler=none` (CatmullRom instead of STP), `screen=WxHw` (windowed). The sides: A base (full screen 5K,
auto, hardware, STP before post); B the NB4 window (1920x1080 windowed, 100%); C full screen with a 2048x1152 backbuffer at 100%
(the base's internal size, no dynamic resolution); D 1920x1080 window at 75% (dynamic resolution in a window); E software dynamic
resolution; F no STP. Reading: B and C fast and A, D slow = dynamic resolution itself; E fast = hardware DRS on Metal; F fast = STP.

**fs5k-diag (Oct 21, user-run; `runs/fs5k-diag`).** FPS, A base (5K full screen, 40% hardware dynamic resolution + STP) -> B 1920x1080
window 100% / C full screen 2048x1152 backbuffer 100% / D 1080 window 75% / E software dynamic resolution / F no STP:
foyer night 17 -> 26 / 23 / 26 / 22 / 17; hall night 24 -> 33 / 29 / 33 / 29 / 24; kitchen night 17 -> 29 / 26 / 27 / 25 / 18; street
day 20 -> 31 / 30 / 26 / 29 / 19. STP is not the cost (F = A); dynamic resolution is (35-70%; software only partly helps). C's readout:
camera 2048x1152, no dynamic resolution, render thread 7.8 ms (A: the whole frame).
**Shipped (C):** `RenderScale.cs` no longer uses dynamic resolution. Full screen sets the BACKBUFFER to about AutoHeight (1152 px;
5K -> 2048x1152) and macOS scales it to the panel; P steps the backbuffer (auto/100/75/50/38% of the display); windows always render
natively. The adaptive scaler and the STP injection choice are gone with it (`RenderScale.DynRes` stays for PerfProbe diagnostics).
Still under the floor at about 1080p: the heavy night interiors (foyer 23-26, kitchen 26-29 fps), GPU-bound: Phase B.

**Phase B attribution (prepared):** night, full screen at the shipped C, each frame setting / content group off or cheaper:
`off=Volumetrics;off=SSR;off=SSAO;off=ContactShadows;off=ShadowMaps;off=TransparentObjects;off=PlanarProbe;hide=Glass;hide=Voile;lowres=all;fit=1;range=0.7`
at foyer-night, kitchen-night, hall-night (`perf_probe.sh run fs-nightB`). The off= rows are upper bounds (attribution, not looks);
hide=/lowres=/fit=/range= are the candidates the sheet trades look against FPS.

**fs-nightB (Oct 21, user-run; `runs/fs-nightB`, `spec/captures/perf/fs-nightB-sheet.jpg`).** Night, full screen 2048x1152. FPS base
-> fit=1: foyer 23 -> 36, hall 29 -> 45, kitchen 26 -> 32 (range x0.7: 30 / 38 / 30; lamp shadows off 29 / 38 / 29; fog, SSR, SSAO,
glass, sheers: within 1 fps; all transparents off 33 / 48 / 31 although glass and sheers cost nothing: some other transparent-pass
cost, open). **Shipped: fit=1** (user: "was great, keep it"): `Scripts/LampFit.cs` fits every real-time punctual lamp at scene load
(room extent + 1 m, the same rays as the variant); `-nolampfit` is the before. PerfProbe tours now sample the fitted ranges as base.

**fs-aa (Oct 21, user-run; `runs/fs-aa`, sheets `spec/captures/perf/fs-aa-{edges,picks,sheet}.jpg`).** The main camera had NO
anti-aliasing at 2048x1152 (STP did it before). FPS none / FXAA / SMAA / TAA / STP@100%: piers day 83/83/76/80/76, street night
36/36/35/35/35, foyer night 36/36/35/36/35, hall night 45/46/44/44/43; 2560x1440 + TAA or SMAA: foyer 27, street 29 (under the floor).
STP forced to 100% does not bring back the dynamic-resolution stall (-4%). Edges at 2x: FXAA blurs shingles and wallpaper; SMAA keeps
texture but twigs stay broken; TAA and STP draw twigs whole, STP crisper. Recommended STP@100% (not shipped: the user picks).
With fit=1 the transparent-pass split (prepass, postpass, low-res, refraction, distortion, motion vectors, SSR, lens flare) changes
nothing (36 -> 36-37 fps foyer).
