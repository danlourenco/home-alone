# Walk feedback — Oct 19, 11:59–12:14

Current disposition: **partially accepted Oct19**. Mirror, front-door appearance/usability, den and TV are accepted. Soffit is rejected because it does not connect. Exterior and other trial changes accepted except all explicitly noted defects. The later notes and disposition below supersede earlier pending-verdict text.

| Time | Feedback | Finding / suspected cause | Proposed response |
|---|---|---|---|
| 11:59 | Interior wallpaper visible beside the front door from outside; reconsider assembly construction | Confirmed wallpaper on exposed reveal. CutWallOpenings copies the room material onto the cut wall pieces; fixed inside trim does not finish the full wall depth. | Finish the fixed assembly across the wall thickness: outer casing, painted jamb/reveal and stops, threshold, inner casing. End wallpaper at inside casing. Preserve aperture/house dimensions; avoid coplanar cover boards. |
| Verbal | Opening animation jerks / appears lower frame rate | Cause unconfirmed. EntranceDoor performs scene search, physics synchronization and nearby cached-shadow refresh while moving. Passive sample caught no motion: median16.5ms/p95 33.6ms is idle evidence only. | Profile a complete swing versus stationary frames; isolate physics, shadows and reflection costs. Remove avoidable work/cache references; adjust motion easing only after frame pacing is addressed. Retain collision and lock behavior. |
| 12:01 | Strange slab/top-step intersection | Screenshot shows a thin slab-like lip over the brick riser and a separate raised landing edge. Exact overlapping meshes not traced yet. | Identify all legacy/generated slabs and steps at this joint; reconcile tread, riser, landing and threshold as one consistent construction from film/measurements. Remove duplicate surfaces; check height/clearance and same-view renders. |
| 12:04 | Mirrored McCallister house across street | Confirmed old WinterBackdrop_NightHouse: mirrored film5546 on a 26m photo card. | Hidden live and verified gone. Remove card creation at source after walk so it cannot return; real neighbour facades follow neighbourhood evidence plan. |
| 12:05 | Dithered shadow around porch lantern/ceiling | Visible stippling confirmed in screenshot; exact rendering cause unconfirmed. Could involve shadow sampling/contact shadows or temporal accumulation. | Compare those features individually at the same pose, stationary and moving. Fix the responsible light/render setting and verify day/night; preserve appropriate shadow softness. |
| 12:11 | Stone/walk looks low resolution and dry against wet asphalt | Live probe confirms Walk_Front uses 1024px HiFi_ExtWetConcrete; legacy object248 with626px material is3cm below. Concrete smoothness.50 versus asphalt.86; identity/scale/wetness need review. | Use film-correct stone/paver material, higher effective density and correct physical scale, full normal/roughness maps, coordinated wet darkening/patchy sheen. Retain material differences. Compare exact note view day/night. |
| 12:12 | Gutter looks wrong; object protrudes through brick; prevent recurrence | Screenshot shows trim crossing the upper facade and a photographic rectangle at its side. Candidate for rectangle is a set-window backdrop extending beyond exterior skin; mesh identity not yet proven. | Trace both renderers, correct gutter/cornice registration from evidence, hide/contain interior-only image cards from exterior views. Add an exterior visibility/clash regression check at this pose; do not simply delete an unidentified object. |
| 12:13 | Magenta breakfast hutch; expected built-in; analyze film/Marina | Magenta is a material/shader binding/rendering failure, separate from design fidelity. Quick unsupported-shader query did not identify it; inspect exact renderer/material slots next. Existing curved-top freestanding hutch may be wrong for the intended built-in. | Repair exact material/import binding. Review film and Marina frames to establish built-in outline, top, trim and placement before replacing. Fixture replacement follows change gate. Add missing-material/HDRP render check. |
| 12:14 | Plain interior doors look low resolution and wonky; match exterior front-door fidelity | Screenshot confirms very flat panel fields, crude handle representation and harsh seams. Resolution alone cannot supply the missing profiles/hardware. Exact door assets still to inspect. | Audit measured openings and reference-specific door types; real panel mouldings/bevels, rounded hardware, suitable UV density, baked PBR and restrained painted-wood detail, consistent with front-door quality. Keep appropriate differences between door types. |

## Proposed order

1. Trace material failure and exterior protruding objects; gather film/Marina evidence for the hutch and door/step assemblies.
2. Correct entrance surround, step/landing joint and exterior trim/card containment together; keep dimensions evidence-led and run required geometry gates.
3. Profile door motion and stippled porch shadows at the reported views; make targeted performance/render fixes.
4. Upgrade stone/wetness and interior-door materials/geometry to a consistent close-range quality bar; rebuild the hutch only after its reference is resolved.
5. One verified day/night review covering all corrections. No user acceptance inferred from positive exterior-door feedback.

While user walks: no Play restart, scene reload or script recompilation. Only the erroneous night-house card has been hidden live; other items above are reviewed/proposed, not claimed fixed.

## Evidence

Original notes and exact poses: `spec/feedback/feel-notes.jsonl`. Screenshots under `spec/feedback/shots/`: 20261019-115840, -120117, -120359, -120516, -121036, -121159, -121259, -121349 (all `-House_WallGrid.png`). All eight screenshots inspected during this review sequence.

## TV feedback follow-up

User likes the GTA-style sit/watch interaction and requests a little more TV focus. Set DenMovieSeat.fieldOfView live **42→36 degrees**, eye/position unchanged; applies on next E sit. Preview captured and inspected (`~/.cache/home-alone-2/captures/den-seat-zoom36.png`). Walking FOV and E stand restoration unchanged. Default-source patch prepared at `changes/2026-10-19-tv-zoom.patch`; **apply after user finishes walking**, avoiding script/domain reload during the walk. This supersedes earlier42° target.

## What still needs the user's verdict

Positive feedback, not yet blanket acceptance: exterior front-door appearance; GTA-style den sit/watch concept. TV zoom36° is live and awaits review; source-default patch remains pending after walk.

No explicit verdict yet on this combined trial:
- Smooth flight2 stair soffit and its landing joins.
- Foyer mirror frame and sharp moving reflection, day/night.
- White inside front-door finish and single inside wreath. Doorway surround and animation remain corrections even if leaf appearance is accepted.
- Door usability: E from both sides, closed blocking/open clearance and obstruction behavior. Gameplay lock is developer-tested, not a user-walk control.
- Den chair position/angle, leather sheen, cleared table area and tray-lamp placement.
- Seated view36°, E stand restoration and V clip toggle, including adult mode if desired.
- Day sky/horizon and O weather states; K off-lot snow/ground behavior; driveway finish, piers/wing walls/garage fence grounding, separate from the rejected stone/step joints.
- Kitchen-back-door and basement-areaway lantern placement/night lighting, and front lantern/wreath illumination. Porch stippled shadow remains a correction.

Acceptance can be per feature. Keep known defects open and preserve approved work; no silence interpreted as approval.

Correction sequence agreed for handoff planning: exact mesh/material diagnosis + film/Marina evidence first; repair missing materials and permanently remove wrong night-house card; cohesive entrance/step/exterior trim fixes with regression gates; measure and fix door/frame pacing and noisy shadows; stone/interior-door fidelity and reference-led hutch replacement; persist36° seat default; build/bake/render and return one short regression walk. A change in sequence may be sensible if the hutch's reference evidence is available earlier, but do not guess its construction.

## User verdict and later notes, 12:26–12:34

- **REJECTED:** soffit does not connect. Required-contact verification added to zfight-check/room-upgrade; actual mesh-join check must fail the rejected build before the correction can pass. Soffit repair still pending.
- **ACCEPTED:** mirror, front-door appearance, usable door interaction, den arrangement, TV view36°. Jamb/wallpaper, animation and every other explicitly reported defect remain open. All other trial changes accepted unless noted.
- **12:31 void:** `(9.496,-40.836,6.476)` world. Nearby67/121 down-rays lacked ground collision. Root cause identified: both visible GroundSkirt meshes had no Collider. Added matching MeshColliders to existing meshes, with no moved vertices/grade, in source and saved current scene. Coverage now0/121 missing; kid/adult actual ground support tested with fall recovery disabled. Permanent FpsController last-supported fall recovery added as a second safeguard, threshold y−12 below basement; isolated automatic-fall/ledge/velocity/basement tests pass. `python3 tools/house/check_fall_recovery.py` reruns both checks in a temporary additive scene, Play stopped. Await user retrial; no whole-region/whole-map coverage claim.
- **12:32 exterior lighting looks good:** accepted, with separately noted porch-shadow defect preserved.
- **12:33 street-lamp style wrong:** inspect film stills against current globe/post proportions and placement before replacing.
- **12:33 tree in driveway:** identify the exact tree and driveway overlap, compare film/site planting evidence, move/remove the misplaced tree and verify the drive passage/render.
- **12:33 garage-side fence placement wrong:** solve placement/extent from movie stills; preserve its physical relationship to garage/drive/lot. Existing fence placement is not accepted.

After Unity was observed stopped: applied36° TV source patch and saved it in current scene; removed night-house card creation in builder and saved card inactive in current scene. No Play restart performed. Surface/collision meshes for ground were not reshaped; no lighting bake required for this collider-only correction. Broader geometry/material corrections remain queued.

## TV media edit and shelf-lamp note, 12:56

TV request complete live: removed baked-in widescreen bars with a centred344×258 crop (true4:3) and trimmed to79.946533s, before the final fade-to-black/text cards. Audio trimmed with video; looping H.264/AAC. Original preserved at `sfm-work/media/tv.original.mp4`, hash/edit metadata in `tv-edit.json`. Reproduce review output with `python3 tools/house/prepare_tv_clip.py`; install only while TV decoder is held off. Current `LocalMedia/tv.mp4` contains the edit. Live prepared/playing confirmed344×258,79.9465s, loop=true. Last frame and filled-screen live capture inspected (`~/.cache/home-alone-2/captures/den-tv-crop-check.png`). Render target changed/saved720×540 to avoid FitInside pillar bars; **apply `changes/2026-10-19-tv-aspect.patch` when walk stops** so builder retains this target, without script reload now.

New lamp defect12:56 (`20261019-125529-House_WallGrid.png`): den shelf lamp too bright, floods surroundings; user requests high-quality asset and a contained shelf/below light pool. Prior den acceptance stands except this new defect. Inspected film2877 panel in `spec/captures/views/den/compare-night-2877.jpg`: a dark urn base/red-brown cone/bell shade, small confined pool, visible shade rather than white blowout. Current bookcase lamp is1200lm point, no range override (builder defaults7m). New model alone will not fix emission/light placement/occlusion or the existing baked indirect pool. Plan restrained shaded output, light leaving the shade opening, realistic shelf shadowing, controlled shade emission and new bake, compared from film/note viewpoints.

Owned lamp audit: BankersLamp and Fadnn SM_Lamp_01/02 available; neither is an established match for this urn lamp. Marketplace candidate to compare: TurboSquid Bell Shade Table Lamp By Illumino (Sketchcore), ceramic base/fabric bell shade, FBX+PBR,36,685polygons: https://www.turbosquid.com/3d-models/bell-shade-table-lamp-by-illumino-3d-model-2207926 . Listing details found via search; direct page fetch failed. **Candidate only, no purchase/download or film-fidelity approval.** A model with an actual shade interior/open bottom and separately controllable shade material is needed; do not pick an unrelated modern/AI-generated lamp merely for its texture resolution.

## Temporary den comparison — user request

Shelf lamp beside TV and chair/tray lamp switched OFF live; banker DenLamp_desk stays ON. Disabled DenLamp_bookcase, DenLamp_floor (legacy), DenLamp_tray (actual chair lamp), plus generated shade/bulb emission via renderer property blocks. Existing Night APV/reflections still contain their baked contribution, so this is a direct-light/emission preview, not a new banker-only bake. N toggles can restore lamp states; no permanent off decision inferred. Capture `~/.cache/home-alone-2/captures/den-banker-only-preview.png`. Capture tool now avoids redundant SetNight calls when the requested state already matches, preserving live lamp overrides in same-mode captures.

BackgroundMusic AudioSource volume .35→.05 live for faint music behind the TV. This current preview level is global; follow-up implementation should duck the normal music mix specifically while the player is in the den and the movie plays, preserving volume controls and returning smoothly outside/when TV stops. No script recompilation or Play restart for this comparison.

Latest live preference: user requested tighter TV shot and music20%. Seated FOV now24° (was36); current seated camera changed immediately, stand still restores prior walking FOV. Music now.20 (supersedes.05). New default patch `changes/2026-10-19-tv-tight24.patch` awaits walk end; source/saved scene still36° until applied/persisted. Shelf/chair lamps remain off, banker on. Captured and inspected den-tv-tight24.png.
