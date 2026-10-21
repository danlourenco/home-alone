---
name: house-split
description: The film's exterior wrapped around Marina's bigger upstairs (HouseSplit). Use BEFORE changing anything that can be seen or lit across that boundary (the skin, the upstairs strip rooms, front windows, upstairs lamps, light bakes, probes, night window glow), and whenever the user reports artifacts at the front, "the upstairs protrudes", dark or odd upstairs brick, glow on the facade, or dark upstairs windows.
---

# house-split: two houses in one place, and nothing may leak between them

The film's house (outside) is smaller upstairs than Marina's house (inside). Her front rooms stand up to ~1.7 m in front of the
film's upper wall (the "strip"). `HouseSplit.cs` shows one or the other by where the camera is: upstairs (above switchY and inside the
storey envelope, with hysteresis) draws Marina's upstairs; anywhere else draws the film's skin. Every bug below came from something
of one house showing, lighting or being baked into the other. Read the ledger before you add a fix.

## The rules
1. **Drawn:** nothing of Marina's upstairs is drawn from outside or downstairs; nothing of the film's upper skin is drawn upstairs.
   Gate: `Split drawn-outside check` (every house renderer above the ground storey that pokes > 5 cm past the skin must be hidden from
   outside). The camera-position `Split check` alone does NOT prove this.
2. **Lit:** a lamp that stands outside the film's walls (in the strip) is dark while the camera is outside or downstairs and is left
   out of the film's bakes; an unshadowed interior lamp lights only inside surfaces (the inside-only rendering layer). Gate: `Lamp split check`
   (`FAIL lamp outside the skin` / `FAIL lamp through the wall`).
3. **Baked:** the film bakes (DayFilm, NightFilm) contain the film's house only; every Marina-strip renderer, visible or
   shadows-only (the Envelope, baseboards), is out of them; Marina's bakes (Default, Night) contain hers. The bake asserts that each
   renderer's include flag matches `BakeLighting.Contributes()` for every pass (`BakeLighting FAIL`). Probes are classed Exterior / Interior
   (rendering-layer masks on the probe volumes); outside walls read Exterior probes only.
4. **Seen through glass:** from outside, every film window must look lit at night like the film (5545: warm sheers, every upstairs window
   and both dormers), even though the rooms behind it are hidden. That is a stand-in behind the glass, emissive only, never a lamp.
5. **Film first:** the outside is judged against the film at the film's solved camera (`front6399`, `walk0645`; `exterior_film_fit.py`),
   at true aspect (`tools/house/sheet_tiles.py`; never stretch a tile).

## Checks to run (and what each proves)
| Check | Proves |
|---|---|
| build log `Split check` / `Split drawn-outside check` / `Lamp split check` = 0 FAIL | rules 1-2 |
| bake log: 4 scenarios baked, no `BakeLighting FAIL` | rule 3 |
| `tools/house/brick_storeys.py RUN` (walk0645 sunny/overcast/night; upper within 5% of lower) | the facade reads as one wall |
| `brick_storeys.py --rooms BEFORE AFTER poses...` (upstairs rooms within 5%) | a fix outside didn't move Marina's rooms |
| `Facade sun` / `Facade sky` gates | the skin's own lighting |
| `ProbeDump.Probes` (batch editor) | what the baked probes actually hold in front of each storey |
| `xmas_lights_check.py` | the window loops and bulbs against 5545 |
| `tools/house/window_glow.py RUN/front6399-night-A1.png` | every film window lit and warm at night, against 5545 (rule 4) |

## Diagnose before fixing (the ledger, Oct 20-21)
- **Doorway artifacts** (roof, gutter, icicles inside the parents' room): the switch used the camera's floor height only -> storey
  envelope + hysteresis.
- **"The upstairs protrudes"** (white ledges over the ground-floor windows): upstairs baseboards built under Ground/Trim were never in
  the hide list; the camera check passed -> the drawn-outside check.
- **Warm band under the upper eave at night**: the hall-bath sconces in the strip were baked into the film's night probes -> rule 2 + lamp split check.
- **Upstairs brick darker than downstairs** (three fixes missed: view bias, probe layers, bake order): the strip's shadows-only Envelope
  still counted in the film bakes and boxed in the probes in front of the upper wall. Found only by reading the probes (`ProbeDump`), not
  by shading tweaks -> rule 3 + the Contributes assert.
- **Dark upstairs windows from the street**: hiding Marina's rooms left nothing lit behind the film's glass, AND the skin's glass is
  opaque, so the "drawn shades" modelled behind it (exterior_shell.sash_unit) never showed at all -> rule 4: the upper sashes and dormers
  get their own glass (EX_GlassLit, night-only warm emission, black to GI); check `tools/house/window_glow.py` (per window lum vs the
  frame's brightest ground window, and R/B, against film 5545; NB10: 11 FAIL).
- **Cool-white sunroom windows at night**: the sunroom's sheer emission was its neutral grey base colour (R/B 0.99) -> warm emission,
  base kept for the day (window_glow.py ground).

Pattern: when a split symptom survives two fixes, stop and measure the state directly (probe dump, renderer census, lamp list per
pass) instead of a third tweak. Every new split bug adds a row here and a check that fails before its fix.
