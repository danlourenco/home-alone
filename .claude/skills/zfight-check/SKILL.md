---
name: zfight-check
description: Prevent and verify z-fighting (flickering surfaces) in the Unity house. Use before handing over ANY build that adds or moves a visible surface (models, trim, wallpaper, dressing, fixtures, finish boxes), and whenever the user reports flicker, a ragged edge or "z fighting".
---

# zfight-check: no two visible surfaces share a plane

Z-fighting happens when two surfaces lie in (nearly) the same plane, face the same way and overlap: the depth buffer cannot
order them, so pixels flip between the two as the camera moves. Precision helps less than you would think: HDRP's reversed-Z
float depth is good, but exactly coplanar faces fight at any distance, and a 4 mm offset fought visibly at 3-5 m (Oct 16).

## Construction rules (follow while building, not after)
1. **One surface per physical surface.** A finish (wallpaper, paint, tile) is the material of the wall's face, not a second
   panel laid on it. Split a box where its finish changes (`SpecGreybox` walls are cut along their length where the rooms
   beside them change).
2. **Overlays stand >= 1 cm proud** of what they cover (raking wainscot 1.5 cm, chair rail 3 cm, carpet runner 1 cm). If
   real life is thinner, remove the covered face instead.
3. **Finish pieces never share faces with the solid they dress.** A tread overhangs its step on every side (2 cm nosing); a
   newel stands 1 cm proud of the stringer; trim never runs into a wall or floor (`SpecGreybox.Trim` skips such pieces).
4. **Faces point outward, and are never wound by hand.** An inside-out part draws its far faces, which then fight whatever
   they touch (the whole foyer stair was inside-out until Oct 16: `hifi_lib` reversed faces for a "reflection" that was a
   rotation). In the Blender scripts use `Part.box/lathe/sweep` and `Part.face(points, toward)`, never `poly`/`quad` with
   hand-chosen order.
5. **No large hidden overlaps either:** two boxes occupying the same volume (a tread inside its step) put their side faces in
   one plane where the edge shows.

## Verification (all three before handover)
1. **Build gate:** `SpecGreybox.BuildWallGrid` appends `Z-fight check: ... N coplanar pairs seen from rooms` to
   `spec/captures/walk-test-wallgrid.txt`. It tests every triangle of every visible mesh in the house (grey-box, dressing,
   models, fixtures): different materials, same facing, within 1 cm, overlapping > 50 cm2, the point in front lying in a
   walkable room and not inside a solid. **Must read 0.** Each `ZFIGHT` line names both surfaces, the gap and a spec point.
2. **Model orientation:** after any Blender export,
   `uv run --with trimesh --with numpy --with scipy --with networkx python -I tools/house/glb_orientation.py` must exit 0
   (every closed part outward, no flipped faces).
3. **Look:** render each walk note in the area from its own pose (`tools/house/note_views.py`) and look at edges where two
   finishes meet. The gate reasons from geometry; a render is the user's eye.

## When the user reports flicker
- Read the note's pose, run the build, and find the `ZFIGHT` line near that point. If the gate reads 0 there, the gate has a
  hole: probe the renderers at the spot (bounds intersect a small box), fix the gate first, then the geometry.
- Fix at the source (the generator or shared builder), never by nudging one instance; then add the trap to this file.

## Known limits
- Areas under 50 cm2 are not reported (flush mounts: fixture canopies on ceilings, a baluster touching a newel).
- Meshes that are not readable (some imported assets) are skipped and counted in the gate line; Poly Haven props are fine.
- The exterior (`Exterior/`, the old reference yard and neighbourhood) is not checked.
