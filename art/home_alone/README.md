# Home Alone — blockout 01

Open `home_alone_blockout.blend` in Blender. The editable source uses meters,
separate named objects, and collections for Ground, Upper, Attic, Roof, Details,
Site, Collision, and Presentation. Hide Roof / Attic / Upper to inspect downstairs.
`exterior.png`, `ground_floor.png`, and `kitchen_detail.png` are rendered previews.

This is an original, movie-inspired layout study with estimated dimensions, not
a measured reconstruction of the video or the real property. Ground-floor room
relationships follow the reference plan; upstairs is simplified to four bedrooms
around a hall. Side wings are single story. The attic flight, roof proportions,
furniture, and clearances are design approximations. Basement, rear service stair,
bathrooms, garage, and detailed movie decor are not modeled in this first pass.

## Walk through it in Godot

Open `scenes/House_Blockout_Preview.tscn` and press F6, or run from the repository:

```sh
/Applications/Godot.app/Contents/MacOS/Godot --path . --scene scenes/House_Blockout_Preview.tscn
```

WASD moves, mouse looks, Shift sprints, Space jumps, Esc releases the cursor,
click recaptures it, T starts a guided tour, and R stops the tour and resets to the front approach. The scene uses a 0.84 m wide,
1.8 m tall capsule. Enter through the open front doorway. Main stairs are on the
left of the foyer; cross the upstairs rear landing for the opposite attic flight.
The main multiplayer scene is not switched to this model.

The foyer and kitchen now have a first realism pass: generated floral damask wallpaper,
photographed oak floor color/normal/roughness maps from Poly Haven (CC0), dark cherry
cabinet faces with handles, green ceramic tile, grout, stainless range, sink, and faucet.
`assets/home_alone/home_alone_blockout.glb` contains the model with these materials
and Godot collision naming: `-col` for structural meshes, `-colonly` for invisible
stair ramps. Window panes and rail details are visual placeholders; windows have
no glass collision. Doors are open gaps. Walls are static, separate segments;
destruction, door interaction, and trap placement still need gameplay integration.
Blender Z-up exports to Godot Y-up: `(x, y, z)` becomes `(x, z, -y)`.
Floor elevations are 0, 3.4, and 6.8 m; principal doors are 1.6–1.8 m wide.

## Rebuild and check

From the repository root (Blender 4.3.2 and Godot 4.5.1 used here):

```sh
/Applications/Blender.app/Contents/MacOS/Blender --background --python-exit-code 1 --python tools/build_house.py -- --render
/Applications/Godot.app/Contents/MacOS/Godot --headless --path . --editor --import --quit
/Applications/Godot.app/Contents/MacOS/Godot --headless --path . --fixed-fps 60 --script tools/check_house.gd
```

Rebuilding overwrites the `.blend`, `.glb`, and (with `--render`) previews. Save
manual Blender edits to a different file first. No downloads or extra packages
are required. The `.gdignore` keeps source art out of Godot's automatic import;
Godot imports only the GLB. The check exercises entrances, room connections,
ascending and descending both stairs, floor heights, and solid-wall collision.

## References

- [Tour reconstruction study](references/tour/README.md): both automatic caption tracks analyzed, [29 native Part 1 MP4 frames](references/tour/main-frames.md) and 16 upstairs storyboard thumbnails indexed, and clean overhead screenshot preserved. Includes corrections and unresolved set-layout gaps for the next modeling pass. The current model has not yet been rebuilt from this evidence.
- [Marina interior asset](marina/README.md): separate editable ground-floor shell for the foyer, living/den, dining, breakfast and kitchen, generated from Marina's plan and local MP4 frames. It is the active fidelity work area; the original blockout and downloaded GLB remain preserved.

- [Mockingbird Lane: Home Alone in depth](https://www.mockingbirdlane.design/post/home-alone-in-depth): creator's companion page, production set photos, and both tour links. Video playback was unavailable during the original blockout pass; the model is not traced from its frames. See the later tour study above for newly inspected evidence.
- [Main floor tour](https://www.youtube.com/watch?v=5GByoLZIzlM) and [upstairs / attic tour](https://www.youtube.com/watch?v=kU7aY1anpAI): references for a later accuracy pass.
- [Hooked on Houses: inside the house](https://hookedonhouses.net/2009/11/30/inside-the-real-home-alone-house/): facade photo and visitor-drawn first/second-floor plans inspected as visual references. These are not survey drawings.
- [Godot import naming](https://docs.godotengine.org/en/4.4/tutorials/assets_pipeline/importing_3d_scenes/node_type_customization.html): structural and collision-only mesh suffixes.
- [Poly Haven Wood Floor](https://polyhaven.com/a/wood_floor): CC0 photographed oak floor maps used in the foyer.

No third-party mesh, image, video frame, or texture is embedded in the deliverables.

- [House survey](references/survey/README.md): 2026-09-11 metric dimensions for all three floors, rectified from Marina's overheads and calibrated to her onscreen floor areas (2,620 / 1,900 / 476 ft²; kitchen 477 ft² cross-check within 0.5 %). This is the layout authority for the Unity rebuild; it supersedes the estimated room sizes in both generators.
