# Performance: how to measure, what was found (perf pass, Oct 18 2026)

Target: the user's 14" M3 Pro MacBook Pro (36 GB), measured in a **standalone** macOS player, not editor Play.

## How to re-measure

```
tools/house/perf_probe.sh build        # clone the scratch copy (last built + baked scene) -> IL2CPP player (~11 min first time, ~1 min after)
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
- Batches, draw calls and gfx memory read 0 in a release player (Unity counts them only in development builds).
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
