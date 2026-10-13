# Astra handoff: Home Alone house prototype

> Superseded 2026-09-11 by [HANDOFF.md](HANDOFF.md) (Unity rebuild). Kept for the Godot-era history below.

## Latest continuation: 2026-09-11

The active work is now the separate Marina interior, not the older blockout kitchen plan. See [tasks/marina-interior.md](tasks/marina-interior.md) and [its asset notes](art/home_alone/marina/README.md). Kitchen placement, counter height and circulation have been corrected. The latest geometry pass separates the breakfast hutch/door/stair, encloses the upper foyer and corrects den seating/TV shelving. The player route now includes the rear foyer-to-breakfast connection and service-stair foot as well as all five rooms and both kitchen aisles in both directions. Six Godot captures document the current furnished blockout. Final fidelity/material/lighting work remains listed explicitly in the current checklist.

## Earlier state

- User's reference priority: Marina Coates's tours/model are the primary authority for fidelity. The downloaded Blender asset is a starting point; correct it to match Marina when details disagree. Other sources fill gaps. Raise only concrete ambiguities or physical inconsistencies. See `art/home_alone/references/tour/README.md`.
- The user provided `Tour the Home Alone House_ Part 1, Main Floor [CG Tour].mp4` in the repository root. Motion video is 640 × 360 at 25 fps; the larger embedded image is cover art. `art/home_alone/references/tour/main-frames.md` links 29 extracted native PNGs, including the confirmed 477 ft² kitchen annotation. Part 2 references remain thumbnails.

- Working directory: `/Users/dlo/Dev/home-alone`
- Godot walkthrough: `scenes/House_Blockout_Preview.tscn`
- Blender generator: `tools/build_house.py`
- Current authored asset: `assets/home_alone/home_alone_blockout.glb`
- Separate downloaded asset: `assets/home_alone/online_home_alone/HOME_ALONE_FINAL.glb`
- Downloaded source package originally came from `/Users/dlo/Downloads/home-alone-final/`.
- The downloaded GLB imports in Blender and Godot. Blender reports 333 objects, 310 meshes, 225 materials; textures are mostly 256–1024 px.
- No license file was included with the downloaded package. Keep it separate until its license is confirmed.
- Preview scene for the downloaded asset: `scenes/Online_Home_Alone_Preview.tscn`.
- Preview render: `art/home_alone/online_preview.png`.

## Playable prototype features

- Human-scale FPS capsule: 1.8 m tall, 0.84 m diameter.
- WASD, mouse look, sprint, jump, guided tour (`T`), reset (`R`).
- Crouch toggle: `C` or `Ctrl`; crouch transitions smoothly to a 1.2 m capsule.
- Existing authored model has named collision meshes and invisible stair ramps.
- Validation command currently passes: `HOUSE CHECK: 172 colliders; 0 failures`.

## Visual work completed

- Approximate Home Alone inspired layout with foyer, stairs, kitchen, upper floor, attic, roof, and site.
- Foyer damask wallpaper, photographed oak floor maps, cranberry runner, molding, picture frames, pendant, plant.
- Kitchen tile, grout, dark cherry cabinetry, handles, countertops, toe kicks, sink, faucet, range, hood, refrigerator, microwave, curtains, island panels, and material bump variation.

## Recommended next Astra task

1. Inspect `online_preview.png` and `Online_Home_Alone_Preview.tscn`.
2. Use Marina Coates's tours as the fidelity target; treat the downloaded asset as a starting point and assess which geometry can be reused while matching her model.
3. Measure the downloaded model’s human scale and orientation before replacing the authored GLB.
4. If its license permits use, build a separate playable scene with generated or authored collision; do not overwrite the existing blockout until scale and navigation are verified.
5. Preserve the current route check and keep the downloaded asset separate until approved.

## Rebuild/check commands

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --python-exit-code 1 --python tools/build_house.py -- --render
/Applications/Godot.app/Contents/MacOS/Godot --headless --path . --editor --import --quit
/Applications/Godot.app/Contents/MacOS/Godot --headless --path . --fixed-fps 60 --script tools/check_house.gd
```
