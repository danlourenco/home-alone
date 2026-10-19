---
name: zfight-check
description: Prevent and verify surface faults in the Unity house: z-fighting (flicker), clashes (one part passing through another) and stale generated models. Use before handing over ANY build that adds or moves a visible surface (models, trim, wallpaper, dressing, fixtures, finish boxes), and whenever the user reports flicker, a ragged edge, "z fighting" or parts running through each other.
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
   newel stands 1 cm proud of the stringer; trim never runs into a wall or floor (`SpecGreybox.Trim` skips such pieces). A window
   stool rests ON the wall: the wall is cut to the rough opening under it (`tools/house/openings.py` "rough"), never to the stool's
   top (the landing window's stool top was flush with its cut and fought the wall top, walk note 2026-10-17T13:32:54).
4. **Faces point outward, and are never wound by hand.** An inside-out part draws its far faces, which then fight whatever
   they touch (the whole foyer stair was inside-out until Oct 16: `hifi_lib` reversed faces for a "reflection" that was a
   rotation). In the Blender scripts use `Part.box/lathe/sweep` and `Part.face(points, toward)`, never `poly`/`quad` with
   hand-chosen order.
5. **No large hidden overlaps either:** two boxes occupying the same volume (a tread inside its step) put their side faces in
   one plane where the edge shows.

## Expected connections: absence of clashes is not proof of a sound join

Oct19 user rejected flight2 soffit: it did not connect to the landing although z-fight/clash were0. For every added/rebuilt architectural surface, identify the boundaries that MUST meet adjacent built surfaces (soffit/landing, wall/ceiling, jamb/head, slab/riser). Mark intentional openings and offsets separately; do not force unrelated planes together.

For each required join, declare the two actual built mesh boundaries, the intended join span and a justified tolerance. Check boundary distance and coverage ALONG that span, including ends and corners; a single touching point or overlapping renderer bounds is insufficient. Sloped surfaces can meet at a change of normal: they need a continuous shared boundary, not identical planes. Fail visible gaps, missing returns or insufficient spans; do not solve a gap by introducing a hidden overlap or moving measured structure arbitrarily.

Use exported/built mesh vertices in world coordinates to check contact against the independently built neighbour; reusing the generator's intended endpoint is not proof it connected. Inspect oblique before/after close views. Add a proven regression checkpoint for each repaired join. **Current gap:** structural SeamCheck does not certify all hi-fi surface connections. Implement and run the missing per-join check during the soffit correction; first demonstrate that it fails this rejected output. Do not label it automatically verified merely because this instruction exists.

## Clashes (one part through another)
The build appends `Clash check: ... N parts passing through another`. A part whose surface within 6 cm of a crossing reaches
more than 2 cm past both sides of the other part (its face and, by a ray, its far side), at a point seen from a room and not
inside another solid, is a clash: a baluster through a wainscot panel, a rail out the far side of a newel. A part that ends
inside another (a baluster on its tread, a rail into its newel) is a joint. Joints that do pass through by construction are
listed, with their reason, in `ClashAllowed` (`SpecGreybox.Checks.cs`); add to it only with a reason. **Must read 0.**
Proven Oct 16: the stair before the 08:40 fix reports balusters through the wainscot, the bullnose cutting the panel and a
baluster inside the bottom newel; after, 0.

## Generated models are never stale
`python3 tools/house/build_models.py` rebuilds every model whose script, `hifi_lib.py` or data changed (stamps in
`Assets/Models/Foyer/stamps.json`, orientation-checked); the pre-commit hook runs `--check` and refuses a commit with a stale
or hand-edited model. Add every new generator to its `BUILDS` table. To test a check against an older model, take it from git
through LFS (`git show REV:path | git lfs smudge`): a bare `git show` gives the LFS pointer, which fails to import.

## Verification (all before handover)
0. **Models current:** `python3 tools/house/build_models.py` (prints "up to date").
1. **Build gates:** `Z-fight check` and `Clash check` both 0. `SpecGreybox.BuildWallGrid` appends `Z-fight check: ... N coplanar pairs seen from rooms` to
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

## Check speed (a slow check is a bug)
Oct 17: ZFightCheck took 25 min 43 s, ClashCheck 80 s. Cause: 396k sliver triangles (cross product under 1e-5, so
`Vector3.normalized` gave a ZERO normal) all keyed to one plane bucket and compared pairwise, O(k^2), though a zero normal can
never pass the facing test. Now 2.2 s and 15.6 s on 1.47M / 1.64M triangles, with every visible mesh covered.
- **Broad phase rule:** bucket by plane (normal to 1/50, 1 cm slabs) as before, then a 25 cm grid in the plane; examine a pair only
  when its in-plane boxes overlap (2 cm slack), once, in the first grid cell both share; a surface's own triangles are contiguous
  and skipped as a run; slivers (zero normal) skipped. Clash: 10 cm 3-D grid, first shared cell instead of a pair set, boxes must
  meet, own renderer skipped as a run, and `Through()` reads the piercer's vertices from a 6 cm grid instead of every vertex.
  Any new pairwise check uses the same rule; never a nested loop over a bucket.
- **Proof it finds the same things:** `SpecGreybox.CheckBench` (Assets/Editor/CheckBench.cs; scratch copy only, after a build:
  `Unity -batchmode -projectPath ~/.cache/home-alone-2/ucopy/HomeAlone -executeMethod SpecGreybox.CheckBench -quit -logFile bench.log`, results in `Library/CheckBench.txt`)
  opens the built scene, restores the rooms from `Library/SeamRooms.json` (written by every build), plants two coplanar floor
  quads and a rod through a panel, and runs the old loops (verbatim copies) and the new ones on the same triangles. Oct 17:
  z-fight raw 309 / kept 43 pairs IDENTICAL on (pair, area, gap); clash crossings IDENTICAL on (pair, count); old 4.7 s vs new
  1.3 s (z-fight, slivers removed for the old loop), 406 s vs 15.8 s (clash). Both find the planted floor quad (2 mm) and the
  rod (16 crossings). Raw edge hits differ by 4 (Treads vs RisersStringers): the old loop's hits on triangles whose boxes are
  apart, off the face's plane by up to 6 cm, i.e. float noise from a near-parallel edge; none became a finding. Reported
  locations may differ (visit order), so compare on pair + area + gap. Re-run it after changing either loop.
- **Budgets** (`GateBudget` in SpecGreybox.cs): ZFightCheck 30 s, ClashCheck 60 s, every other gate 60 s. The long loops call
  `BudgetGuard()`, which throws `BUDGET FAIL <gate>` the moment a gate passes its budget (no silent hours); a gate that finishes
  late adds a `BUDGET FAIL` line to the report. `unity_pipeline.sh build` exits 1 on either (and on a Unity
  exit code, a quality-gate FAIL, or a preflight FAIL before Unity starts: `unity_pipeline.sh preflight`, skip with HA_NO_PREFLIGHT=1). Fix the algorithm or the input (a
  triangle-heavy model: artist-pipeline rule 8, the `Props triangle budget` line); never raise a budget to pass.
- **Reading the timings:** build.log has `[hh:mm:ss] BuildWallGrid: <gate>` when a gate starts and `<gate> done in N s (budget
  B s)` when it ends; `ZPairs:` and `ClashCheck:` lines give triangles, cells, pairs examined and overlaps. A silent log with no
  new stamp names the stuck gate.
- **No result cache** (decided Oct 17): both gates now cost ~18 s, and a per-mesh cache cannot be sound: `Hidden`/`Visible`
  ray-cast against every collider in the house, so one mesh's result depends on all the others.

## Coverage
The gate line ends `(every visible mesh checked)` or names the meshes NOT checked. Imported models with Read/Write off (25 on
Oct 17, LandingWindow among them) are read through `Mesh.AcquireReadOnlyMeshData` (`ReadMesh`), in both gates.
A face inside a wall's thickness (a window reveal, a recess) is outside every room outline; it counts as seen when a clear ray of
up to 0.6 m (four horizontal directions and the face normal) reaches a room. That hole hid the landing window's stool against the
wall top it sits on (walk note 2026-10-17T13:32:54; the check now reports `LandingWindow_HiFi/Paint vs Ground/Walls/Wall`).

## Known limits
- Areas under 50 cm2 are not reported (flush mounts: fixture canopies on ceilings, a baluster touching a newel).
- Two stacked surfaces 4-10 mm apart where the upper one is an OPEN sheet (no back faces) read as hidden: the ray from 4 mm in
  front of the lower one hits the sheet from behind, which the test takes for the inside of a solid (proven by CheckBench's
  planted quads: floor vs quad 2 mm apart is found; quad vs quad 6 mm apart is not). Closed models are judged correctly.
- Traps (Traps.cs) are added after the gates, so the paint cans' own lid/body overlaps are not checked in the build.
- The exterior (`Exterior/`, the old reference yard and neighbourhood) is not checked.
