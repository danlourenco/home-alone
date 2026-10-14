---
name: room-feel
description: What to check, in order, when a room feels too big or too small (from a user feel note or a walkthrough) BEFORE moving any wall. Use whenever someone says a room feels cramped, huge, off or wrong, or proposes resizing, stretching or borrowing space between rooms.
---

# room-feel: diagnose before you move walls

A room that "feels small" is often fine. Rule from the user (Oct 13): **start with furniture sizes before assuming a room is too big or too small.** Work through these steps in order and stop at the first one that explains it.

1. **Units.** Find out what one scene unit is in metres before reading any number. The grey-box is metres. IntactHouseReference (the downloaded model) is native units: **0.774 m per unit**, from its 80 in doors. On Oct 13 I read that scene's bed as 1.22 × 2.30 m when it was 0.94 × 1.78 m, then blamed the bed. Convert first, every time.
2. **Furniture against standards.** In Unity run `SpecGreybox.DumpFurniture -scene <name>`, then `uv run python tools/house/furniture_check.py <name>`. An oversized bed or dresser makes a room feel small, so fix the furniture first. The standards are in `spec/furniture_standards.json`.
3. **Eye height and lens.** Players see from 1.65 m (adult) or 1.05 m (Kevin) in TRUE metres. A scene in other units changes this silently: IntactHouseReference's 1.65-unit eye is 1.28 m. A lower eye makes rooms read bigger. Compare against Marina's camera (`lens_compare.py`, ~1.0 m, 40° vertical field of view).
4. **The neighbours.** An over-wide hall or a deep neighbouring room makes this one read small by comparison. Measure those too, against Marina.
5. **The room itself, against Marina** (`shape_drift.py`, the room's SfM measurement). Only now consider moving a wall, and only through the `change-gate` skill (independent evidence, before/after renders, user walk). Move inside walls only, never the outside shell, and take the space from a neighbour that is oversized by the same evidence. Log the move in `docs/DEVIATIONS.md`.

Write down which step explained it in the feel note's follow-up (`spec/feedback/`), so the next room starts from evidence.
