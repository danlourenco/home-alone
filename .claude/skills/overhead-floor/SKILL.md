---
name: overhead-floor
description: The faster route to a floor plan. Calibrate Marina's angled overhead render of a whole floor from its own wall directions, plus one measured room shape and one stated area, then prove it with independent checks. No per-room SfM. Use when a floor (the ground floor, the basement) needs a plan and the user wants confidence quickly, or when room video is unusable (repeating wallpaper, camera only panning).
---

# overhead-floor

The upstairs was calibrated on three SfM-measured rooms (`overhead_fit.py`). That took hours, and on the ground floor the living room and kitchen clips failed their gates (floral wallpaper, pan-only cameras). This route needs no room SfM:

1. **Wall directions fix the tilt.** Every wall is square, so the overhead's two families of wall lines meet at two vanishing points. Sending them to the plan's x and y axes removes the perspective.
2. **One measured room fixes the stretch.** The x-versus-y stretch is the one thing the lines can't tell you. Take it from one room's proportions measured elsewhere (a gated SfM clip, no scale needed).
3. **One stated area fixes the size.** Marina's stated floor area works, as does any length or area at wall-top height.
4. **Everything else is a check**, and the checks decide whether to trust it.

## Run it

```bash
uv run --with numpy --with opencv-python-headless python tools/sfm/overhead_rectify.py --selftest     # must PASS first
uv run --with numpy --with opencv-python-headless python tools/sfm/overhead_rectify.py measurements/overhead/<floor>.json
```

It writes `measurements/overhead/<floor>.H.txt` (overhead pixels to plan metres). Trace rooms in `<floor>-trace.json` exactly as for the upstairs; `overhead_plan.py` reads the same calibration file.

The spec (`measurements/overhead/ground.json` is the worked example):
- `image`: a frame with no arrows or labels. Check that two neighbouring frames are identical, so it isn't mid-dissolve.
- `aspect`: one room's four inner wall-top corners (TL, TR, BR, BL) and its measured width/height ratio.
- `scale`: anchors (`area` in m², or `length` in m). `use: true` sets the scale. Mark the others `use: false`, and they are printed as checks.
- `checks`: `dims` (w × h), `ratio`, `area_m2`, each with traced pixels.

Read corners from 2× gridded crops; ±3–5 px is normal. Wall-top **inner** edges for rooms, **outer** edges for a gross outline.

## Confidence: what counts

Report every check with its kind. Proceed only when at least two **independent** checks agree within a few percent.

| Check | Independent? | Ground floor, Oct 13 |
|---|---|---|
| A room's width AND depth vs another model, when both directions agree | Yes, if that model wasn't used | Den vs the downloaded model: +1.7%, +0.1% |
| A measured width at ONE height (the stair runner) | Yes | 1.12 m vs 1.125 m measured |
| A second stated area (kitchen 477 ft²) | Weak (boundary ambiguous) | −8% in area |

## Traps (both hit on Oct 13)

- **Only compare things at one height.** In an angled view, a point's image position depends on its height. The stair run spans floor to landing (2.2 m) and read 4.14 m against 2.89 m. Widths across the stair are at one height and read true. Wall tops are one plane; use them, or same-height floor features for ratios only.
- **Another model checks only where its rooms have the same shape.** The downloaded model's den matched to 2%, but its living and dining rooms have different proportions from Marina's (living depth / den depth: 1.49 vs 1.20, in pixels). That's a different model, not a calibration error. Look at ratios within each model before blaming the calibration. Marina is the authority (`docs/STATUS.md`).
- **The stretch comes from one room.** If that room's ratio is wrong by x%, every room's depth is wrong by x%. The self-test shows a 10% stretch error is visible in a second room. So always keep one checked room whose two directions are independent.
- Don't run per-room SfM unless a check fails. That's the slow route this skill replaces.
