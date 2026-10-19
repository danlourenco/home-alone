# Foyer trial ready — Oct 19, 2026

## Latest disposition — supersedes earlier checkpoints

User accepted mirror, front-door appearance/usability, den arrangement and tighter TV view; accepts all other trial changes except explicitly noted defects. **Soffit rejected: disconnected planes.** All logged defects remain open, including new street-lamp style, driveway tree and fence placement notes.

Unity was observed STOPPED. Permanent fall recovery implemented/tested; exact visible GroundSkirt and OffLot meshes now have matching colliders in builder and saved main scene (no shape/grade changes). Nearby121 probes:67 missing before,0 after; kid/adult support tested with emergency recovery disabled. Isolated fall/ledge/velocity/basement checks pass. Re-run `python3 tools/house/check_fall_recovery.py` with Play stopped. Main scene36° seat view saved, source patch applied; mirrored night-house card inactive in saved scene and creation removed from builder. Source compile passes. No Play restart or full build/bake performed for these collision/control corrections.

Required surface contact verification added to zfight-check/room-upgrade. **Actual general hi-fi contact gate is not implemented yet**: add the soffit regression on correction, prove rejected output fails, then pass connected output. See WALK-FEEDBACK for all verdicts and remaining work.


The authorized foyer pass is implemented, baked and loaded in the main editor. **TRIAL: walk in progress; entrance corrections below remain open.** Play is running at `(7.35,-2.996,-9.628)`, facing the stair. Door closed/unlocked, seat empty, normal controls, Sunny day, TV playing. No Blender or building job remains. Nothing committed/pushed by this pass. Preserve the shared dirty tree.

Use [the combined exterior/den/foyer walkthrough](WALKTHROUGH-2026-10-19.md). Do not rebuild/reload if the user is walking; use live previews only. User asked to ignore harmless hook errors.

## What shipped

- Continuous white flight-2 soffit from the existing stair/landing boxes; no tread elevation or room-size changes.
- Separate gilt mirror frame (rounded mouldings and scrolls), smooth mirror glass, localized realtime 1024 planar reflection. HDRP planar atlas 2048. Sharp reflection confirmed in live day/night captures; batch RenderViews deliberately disables reflection lighting and cannot validate it.
- One physical 50 mm leaf carrying BOTH white inside and dark green outside, six profiled panels per side, rounded hardware, independent 4096² atlases, baked normal/AO/curvature and fine paint detail. Existing opening .811 × 1.898 retained; leaf recessed 184 mm to inner reveal, fixed frame/sidelights. Both wreaths and outside bulbs follow the same hinge; one inside wreath. Authored details in DEVIATIONS 105.
- E opens/closes, public gameplay `locked`, moving leaf collider, inward 100° swing, pauses against the player.
- E sits/stands at den movie chair: kid/adult seated eye, 42° view at actual TV screen; V retains DenTV clip toggle. Camera/control state restored when standing.
- Captures use their own HouseSplit viewpoint and an untagged camera clone. Daycheck temporarily selects its calibrated Sunny state and restores prior weather; thresholds unchanged. A/B did not conclusively reproduce the exact original floor failure, so do not claim one proven root cause.

## Verification

Final scratch build `~/.cache/home-alone-2`: preflight all pass; models current; C# compile pass; model orientation and artist quality pass; **0 z-fights, 0 clashes**. No new BLOCKED line vs HEAD (existing service-winder leg2 identical). Casing/opening/arch/envelope checks pass. Legacy props warnings (142), 4 old models over triangle budget, 1 trim gap remain; do not claim every diagnostic is clear.

Night/Default lighting baked and reflection probes rerendered; **76/76** authored baked lights. Night means foyer .286, living .312, Buzz .292, parents .322, attic .183, all above their floors. Day saturation .104/.127 (floor .085); Buzz floor R/B **8.08** from foyer and **8.09** with player outside (floor **1.5**). Outside test started Overcast and confirmed it was restored. Final state reset to Sunny.

Live: adult capsule closed blocked/open clear; lock refuses opening; closing pauses against player at 52.18°, completes to 0 after player leaves. Kid/adult each sit/stand twice, correct eye/FOV and controls restored; video prepared/playing. Initial teleport tests placed the return capsule in wall/lamp colliders and correctly refused standing; valid reachable approach `(5.1,-2.996,-17.0)` passes all four cycles.

Live day/night door faces, mirror, soffit, open leaf and seated TV renders inspected, saved as JPG in `spec/captures/views/foyer-interactions/`. Open/pause captures precede the final material-only relief reduction; geometry unchanged. Painted-wood normal strengths were reduced after live close-up comparison, saved in main/scratch materials and persisted in the builder. No new geometry or lighting after bake.

## Sources and reproduction

- Record `changes/2026-10-19-foyer-interactions.json`, DEVIATIONS 105. Evidence film1690/9358/778 and independently inspected Marina312.
- New generators `hifi_front_leaf.py`, `hifi_foyer_mirror.py`; `front_leaf_finish.py` removes covered paint faces and separates hardware by side without changing UVs/maps. The same finish function ran on the already-baked mesh, orientation/quality passed, and its stamp was updated. Future generator builds include that function. Avoid redundant full 4K bakes.
- `SpecGreybox.FoyerInteractions.cs`, `EntranceDoor.cs`, `DenSeat.cs`. New opening in measurements/windows/ground.json cuts wall and envelope; reconciled ground spec, openings and trim regenerated; verify-plan 0 FAIL.
- Removed old inside/outside leaf render exports and doubled generated wreath; retained fixed frame. Removed two covered gift bottom faces to resolve pre-existing rug z-fights; gifts unchanged in place/size.
- Logs: `/tmp/foyer-preflight-final.log`, `foyer-build-final.log`, `foyer-bake-final.log`, `foyer-load-final2.log`, `foyer-seat-test3.log`, `foyer-day-outside.log`, `foyer-door-pause-test.log`. Full final gate report remains `spec/captures/walk-test-wallgrid.txt`.
- Standard rebuild: `HA_SCRATCH=$HOME/.cache/home-alone-2 HA_CHANGE=changes/2026-10-19-foyer-interactions.json tools/house/unity_pipeline.sh preflight|build|bake|load`. One builder at a time; check pipeline_busy.sh and Blender separately. Main editor must never be killed. New trial needs a new bake after any full scene build.

Next: user walks once, then accept/revise; texture queue remains next. Neighbourhood evidence and earlier trials preserved in RESUME/STATUS.

## Walk review, 12:0x — corrections pending

User note 11:59: wallpaper exposed on exterior jamb, screenshot `spec/feedback/shots/20261019-115840-House_WallGrid.png`. It is on the reveal next to the leaf, not merely an interior wall seen through glass. `CutWallOpenings` clones the wallpaper wall material onto every face of the cut pieces; inner fixed mullions stop at WF. Treat the entrance as a fixed assembly spanning wall depth (outer casing, painted jamb/reveal + stops, threshold, inner casing), with only the two-sided leaf/hardware/wreaths rotating. Preserve the existing aperture and house dimensions. Correct face materials at source; do not cover wallpaper with coplanar boards. Live preview/capture first; gates before handing over a rebuild.

User also reports jerky door swing; exterior leaf looks pretty good. Passive 20-second timing sample: 1216 frames, median 16.5 ms, p95 33.6 ms, **zero moving-door frames**, so this does not establish animation cost. Suspects in EntranceDoor.Update: per-moving-frame FindFirstObjectByType, physics synchronization and ShadowRefresh.Near requests. Measure the swing before claiming a cause or fix. No scripts/models changed during this review, because the user is still walking. No acceptance of the rest inferred.

## Night backdrop review, 12:0x

Note12:04 sees a mirrored McCallister facade across Lincoln Avenue. Confirmed intentional old placeholder: `SpecGreybox.Backdrop.cs` creates `WinterBackdrop_NightHouse`, a 26m photo card at x52; texture `card_night.png` is film5546 mirrored by window_backdrop.py. Hidden live with SetActive(false), no Play restart. **Still remove the card creation at source after the walk**, otherwise it returns on load/build. Do not substitute another invented house; use neighbourhood evidence plan. New notes12:01 slab/steps and12:05 dithered shadows also remain open.

## Walk material note, 12:11

Stone/concrete vs asphalt contrast at `(24.304,-4.181,-9.831)` yaw272.5, screenshot `20261019-121036-House_WallGrid.png`. Live down-ray hits Walk_Front, HiFi_ExtWetConcrete, 1024px scan; legacy object248/Material_254 (626px) lies 3cm below. Current concrete uses concrete_floor_01_x at 2m scale, smoothness .50 vs asphalt .86. This belongs in the next texture pass: film-correct stone/paver identity, higher effective density, scale and normal/roughness detail; coordinated wet darkening/variable roughness so the shovelled walk and drive share weather while retaining distinct materials. Live material comparison first, same day/night viewpoint. No material edits made during this note review.

Full current-walk feedback and proposed correction order: [WALK-FEEDBACK-2026-10-19.md](WALK-FEEDBACK-2026-10-19.md). Eight saved notes plus animation comment; latest interior-door and hutch/gutter notes included.

User likes sit/watch; requested slightly tighter zoom. Live seat FOV now36° (was42), screenshot inspected; seated location unchanged. **Apply `changes/2026-10-19-tv-zoom.patch` once walk ends** to persist runtime/default builder values without recompiling during the walk.

User requested carpenter-style shared door verification for Claude. Added `.claude/skills/door-assembly/SKILL.md`, linked from AGENTS, artist-pipeline and room-upgrade. Read before entrance/interior-door corrections. It requires implementing/generalizing automated per-door checks on first application and explicitly does not claim a general validator exists yet.

TV media now cropped4:3 and end cards removed, live playback verified, original preserved. RT asset720×540 saved; builder default patch `changes/2026-10-19-tv-aspect.patch` awaits walk end. New12:56 shelf-lamp brightness/quality defect recorded with film reference and marketplace candidate in WALK-FEEDBACK; den otherwise accepted.

Current LIVE comparison requested by user: den bookcase + actual tray/chair lamp and legacy floor lamp OFF, generated shade/bulb glow off, banker lamp ON. Background music .05 (was.35) for preview. Baked bounce remains; N can reset live lamp overrides. See WALK-FEEDBACK for source/persistence limitations and future contextual music duck. Do not treat as final lighting acceptance.

Latest live preference: user requested tighter TV shot and music20%. Seated FOV now24° (was36); current seated camera changed immediately, stand still restores prior walking FOV. Music now.20 (supersedes.05). New default patch `changes/2026-10-19-tv-tight24.patch` awaits walk end; source/saved scene still36° until applied/persisted. Shelf/chair lamps remain off, banker on. Captured and inspected den-tv-tight24.png.
