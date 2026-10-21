---
name: xmas-lights
description: Rules for the exterior Christmas lights (house window loops, eaves, porch, shrubs, trees, the neighbours' C7s): bulb size and pitch, colour, emission vs exposure, halos, spill, draw-call and light budgets, and the film-match checker. Use BEFORE changing any bulb, strand, glow, spill light or night bloom/exposure setting outside, and before saying the lights look right.
---

# xmas-lights: the film's strands, measured, at a fixed cost

Design and sources: [docs/XMAS-LIGHTS.md](../../../docs/XMAS-LIGHTS.md). Checker: `tools/house/xmas_lights_check.py`.

## The numbers (film 5545, measured by the checker; do not change without re-measuring)
- **Pitch 0.21 m** (between the stock 6 in and 12 in stringers) round the upper windows, not 5.5 cm and not 30 cm. ~24 bulbs per upper window loop.
- **Glow 5.4 cm** half-maximum diameter, **halo 11 cm** radius at 15 %: the halo is the lens's, so it comes from glow cards
  and bloom, never from a bigger bulb.
- **Colour:** the film is tungsten-balanced, so a 2400-2700 K bulb reads warm-white with an amber shoulder: linear
  (1.0, 0.53, 0.32) measured on 419 isolated bulbs (`--film-extra`). A D65 2700 K blackbody (1, 0.42, 0.10) is too orange; (1, 0.78, 0.50)
  clips to white. The McCallister house is ONE warm colour; the coloured mix (red/green/amber/blue/white) is the Murphys'
  (film 11581) and the street's.
- **Steady:** per-bulb variation 0.9 % across 5543-5550. No twinkle on the McCallister house.
- **Spill:** brick under the strands is warm (R/B 2.1) at about 1/7 of the bulbs' glow luminance.

## Rules
1. A bulb is never a GameObject and never owns a Light. Bulbs are chunked static meshes (one per strand group of about
   4 m, with a LODGroup), colour and intensity in vertex colour, ONE shared material (SRP Batcher). Instancing does not
   pay for a 60-triangle mesh (Unity manual: avoid instancing meshes under 256 vertices); if you try it, measure it as a
   variant.
2. The strands' real-time lights are the pool only: at most 24 (`xmas_lights_check.py --scene`), unshadowed, exterior
   rendering layer, range at most 2.5 m, placed by the pool script. Today's 35 `ShrubGlow` lights are retired by the pool.
3. Glow cards are view-facing quads billboarded in the vertex shader. Unlit additive, colour scaled by HDRP's Exposure node,
   so the card is in screen units and the same at any EV. Analytic falloff (no texture), soft depth fade, and a low-resolution
   transparent pass. They fade out closer than about 4 m, so a shrub at Kevin's knee can't fill the screen with overdraw.
   Inflate the mesh bounds by the card radius, or the chunk is culled while its cards are still on screen.
4. Bulb emission stays physical (Lit, Exposure Weight 1, about 1,600 nits: a C7 is 10 lm at 2700 K). The core clips. Don't raise
   the nits to get a halo: a 1-pixel source can't make one.
5. Bulbs have a minimum on-screen size (the card's pixel floor). A sub-pixel bulb aliases: NB9 lost about half its bulbs to
   gaps and shimmer (the checker found 39-49 of the 92 built per window).
6. Night bloom and exposure belong to `ExteriorNight` (SpecGreybox.ExteriorRealism.cs: bloom 0.8 / scatter 0.78 /
   threshold 0.3, auto exposure 5.6-12 EV, ACES). Changing them changes every night look, so it needs its own A/B.
7. Every change gets a `-perfab` sheet (AGENTS.md). Use the `xmas=` variants in docs/XMAS-LIGHTS.md at street, foyer, walk0645
   and front6399, night. Budget: at most 5 % FPS at the heavy night poses.

## Done means
- `xmas_lights_check.py <front6399-night PNG>` scores 6/6 (today: 0/6, `spec/captures/perf/xmas/nb9-front6399.txt`).
- `xmas_lights_check.py --scene` is ok, `unity_practices.py` has no new failures, and the FPS cost is within budget.
- The user has walked it (the decoration lane: no change record; z-fight/clash still run).

## Traps
| Trap | Fix |
|---|---|
| Strand pitch copied from a guess (the brief said 30 cm; the old build used 5.5 cm) | Measure on a window of known size (the checker's loop rulers) |
| A "warm" colour that clips to white in every channel, then ACES desaturates it: cool-white dots | Saturated enough that the shoulder keeps its hue; judge the halo, not the core |
| Film colour compared in D65 terms | The film is tungsten-balanced: match the film's pixels, not the Kelvin |
| One light per shrub "for the glow" (35 lights) | The pool (24, nearest clusters, faded in and out) or a bake |
| Camera-facing cards culled at screen edges | Inflate the bounds by the card radius |
| Lens Flare (SRP) components per bulb | At most a handful (the porch lantern); the film's star glints are a card term on the brightest few % |
