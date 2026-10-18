# Current status — start here

## RESUME HERE (Oct 17, 2026, morning): downstairs dressed room by room; artist pipeline + upstairs hall paused mid-way

**Read this section first.** Everything below is history except where pointed to. All work is TRIAL unless a change record says
`user_walk: accepted`. The latest full build (scratch `~/.cache/home-alone/ucopy`) is LOADED in the user's editor (Oct 17 ~06:30)
but the user has not walked it yet.

### State of each job
| Job | State | Where |
|---|---|---|
| Kitchen wing 5.00 m, back door + dog door, cabinets/island/tile | ACCEPTED (user: "EXCELLENT") | changes/2026-10-16-kitchen-wing.json, -kitchen-cabinets.json |
| Kitchen wallpaper (film 6910 cut), curtains/sheers (dining + kitchen) | TRIAL, loaded | DEVIATIONS 50; tools/house/hifi_sheers.py |
| Kitchen night lights (under-cabinet strips, breakfast chandelier) | TRIAL | changes/2026-10-16-kitchen-night-lights.json |
| Breakfast table (Marina oval, 2 pedestals) | TRIAL; FILM shows a SINGLE turned pedestal (1151, 1049); top shape round vs oval NOT measured (steep view): solve film 1151's camera and measure the top before changing | hifi_breakfast_table.py, spec/dressing/kitchen.json |
| Kitchen/breakfast fixtures: sconce pair + gallery + desk, back-stair sconce (only ONE found; user: second not clearly seen: leave), chandelier 6 arms | TRIAL | changes/2026-10-17-kitchen-fixtures.json |
| French doors: 4 pairs (foyer/dining, foyer/living, den/living open; sunroom closed) | TRIAL; user Oct 17: KEEP all. Film confirms foyer/living (10636, 12138); dining + den pairs are Marina-only | changes/2026-10-16-french-doors.json |
| Den: film teal paint (wall colour too red/grey: candidate linear 0.052/0.179/0.170, user decision open), windows, bookcase + clutter, lamps, JVC TV (bought pack VTC_AV-2062s) playing the user's clip (Assets/StreamingAssets/LocalMedia/tv.mp4, gitignored; walls muffle it) | den ACCEPTED ("fantastic"); TV/lamps TRIAL | changes/2026-10-16-den.json; DenTV.cs |
| Living room: film paper, windows/drapes, mantel, generated console upright piano (user: keep), bought Christmas tree (AlterEgos pack) with C7 bulbs | TRIAL | changes/2026-10-16-living-room.json; check: tree hides the den-side rear window; possible doubled white poinsettia; den/living French door vs piano |
| Foyer finish: film console/mirror/chairs, bench, rugs, gallery (public-domain art), purchased ficus + poinsettias | TRIAL; user OK'd a WIDER ficus crown (~0.75 m, pot 0.1 m off the stair): not done yet | changes/2026-10-16-foyer-finish.json; tools/house/purchased_plants.py |
| Kevin mode (FpsController: kid body default, eye 1.10, G toggles adult, H toggles step bob) | ACCEPTED (user Oct 17: "i like kevin mode") | Scripts/FpsController.cs |
| Paint-can trap (2 cans, film 10700-10724) | TRIAL | docs/paint-can-trap.md; keys P/L/K/B/T |
| House-wide shadow pass: cached shadows (fixes flicker squares), tiers, contact shadows | TRIAL, loaded, NOT checked live | DEVIATIONS 62; Editor/SpecGreybox.Shadows.cs, ShadowAudit.cs, Scripts/ShadowRefresh.cs |
| Artist pipeline (skill .claude/skills/artist-pipeline) + foyer arch rebuilt smooth | Oct 17 attempt 2 REJECTED on walk; attempt 3 TRIAL (crown 2.17 -> 2.05 with paper over it, no casing; built in ~/.cache/home-alone-2, gates clean, NOT loaded, not re-baked; renders spec/captures/views/arch/{before,after}2-*.png). Earlier: gate finished (model_quality: Unity maps + detail albedo checks, self-test 8 cases), arch passes 0 problems; scratch build ~/.cache/home-alone-2: Arch fit 0, Z-fight 0, Clash 0; renders spec/captures/views/arch/. NOT loaded (user loads). Rollout to other models not started. HallArches.glb (hall job) now FAILS the detail-albedo check: apply DETAIL_ALBEDO there | changes/2026-10-16-foyer-arch-model.json; tools/house/hifi_pipeline.py, hifi_foyer_arch.py, model_quality.py |
| Upstairs hall: film teal paint, trim, sconces, dressing, the film's elliptical ARCH (film 2080-2100; 2050-2060 for sconces), black-urn poinsettias (H1) | PAUSED mid-way, in its own scratch copy ~/.cache/home-alone-3 | changes/2026-10-17-upstairs-hall.json, -upstairs-arches.json; hifi_hall*.py; build reports Clash 2 in HallDressing (WIP) |

Gameplay ideas (parked, user's words): [docs/GAMEPLAY-IDEAS.md](GAMEPLAY-IDEAS.md) (stealth/lure, sit-and-watch TV, prep music, web).

### NEXT (in order; run ONE agent at a time: the user hit the usage limit twice running six in parallel)
1. User walks the loaded build (day + night): shadow flicker gone (den plant pose 7.407,-2.996,-17.872 yaw 284), French doors,
   kitchen fixtures, plants, tree, TV. Answer each walk note from its own pose (live capture).
2. Resume the artist pipeline + foyer arch (finish model_quality.py gate, arch proof, before/after), then roll the pipeline out.
3. Resume the upstairs hall (user walk notes Oct 17, spec/feedback/feel-notes.jsonl 08:28: at the stair-hall arch the side facing the stair should be PAINT not wallpaper per the film; 'random vertical stripe... bad connections' beside the hall arch jambs at 6.969,0.030,-9.737; the arch at 6.893,0.030,-9.487 yaw 188 'looks good') (in ~/.cache/home-alone-3) incl. the arch and H1 poinsettias.
4. Breakfast table: single pedestal; measure the top shape from a solved film-1151 camera.
5. Ficus crown wider; den wall saturation (ask the user); night white balance (agents measured nights 3-10x warmer than the film:
   ask the user about a house-wide night grade); sheers too bright at night (shared voile material).
6. Z-fight reported 2 pairs in some builds: trace and fix.
7b. BASEMENT SHELL TRIAL 1 (Oct 18, NOT walked; changes/2026-10-18-basement-shell.json, DEVIATIONS 91): the old model's basement registered to ours (ground storey less the den, 2.68 m deep), a step down inside Kevin's door to a landing, open 14-riser stair under the back stair, film furnace / laundry (27 in washer ruler) / pull-cord bulbs / chute foot / stone areaway (1.07 m, door ruler) with a half-glazed gingham door; walk 36 legs 0 blocked. Loaded at the stair foot facing the furnace (3.0,-5.70,-8.0,180). OPEN: exterior site not registered (areaway proud of the lot), chute top route, depth has no film ruler, areaway lamp, props (traps).
7q. ATTIC SHELL TRIAL 2 (Oct 18, NOT walked; trial 1 rejected: "the orientation of the bed looks off, and the steps lead directly into a wall"; changes/2026-10-18-attic-shell.json, DEVIATIONS 21 + 90). Layout from the user's poster (IMG_4295; spec/captures/picks/attic/poster_*.jpg), the old model agreeing: 14.44 x 5.20 m along the main block (z 5.47-19.92), hipped over the den (an upper room there is NOT built: the user's "hidden room"), the stair head into open floor (stair_arrival.py ok), sofa bed with its back to the rear knee wall beside the parents' flue chimney, zipline dormer over the landing window. Floor 2.62 in 15 risers of 0.1747: all three bodies climb (step offset unchanged). Loaded at the stair head facing the bed (6.556,2.65,-16.95,351). OPEN: the upper room over the den; the poster's two front dormers; props (crib, chest, boxes, table and chairs, gumball, flag); night light; boards too orange.
7p. PARENTS' BEDROOM TRIAL 1 (overnight8, Oct 18, NOT walked; changes/2026-10-18-parents-room.json, DEVIATIONS 85): four-poster (BED_01 reworked, 2.00 m over the posts, posts 2.15, under-rail 0.48), nightstands + generated lamps, etagere, armoire, writing table, chairs, floor lamp, hall door leaf, film-1610 paper, film-2648 damask curtains. Loaded facing the bed (HA_START 6.45,0.030,-1.84,270). Next: fireplace + mantel, rice-carved posts, sash windows, screen/dress form/sewing table, rug.
7a. [ORDER, user Oct 17: rugs (PAUSED) -> HOUSE KERNEL step 1 (trim from faces) ACCEPTED Oct 17 -> FAST CHECKS (ZFight/Clash broad phase + per-mesh cache + per-gate timing + time budget + import triangle budget; equivalence proof old vs new; update zfight-check skill; user: "if you can find improvements to the algorithm, do them") -> FILL-LIGHT FIX (7a) ACCEPTED Oct 17 -> 8p process fixes DONE -> kernel step 2 ACCEPTED Oct 17 -> 8z BUZZ (as kernel step 5: furniture against faces; Buzz queue Oct 17: door casing TRIAL (walk) -> footlocker prop -> PROP TOOLS (live placement into the open editor written back to store_props.json + an in-walk nudge mode that saves; user: "yes, absolutely. see this is the type of streamline and tooling we should be doing") -> tarantula prop (Assets/Tarantula, needs HDRP materials) -> BUZZ CLOSET DOOR (fixture; user Oct 17: "the jordan poster is actually on what appears to be a closet door; you can make out the knob coming through on the ruler": film 480/526 show a brass knob through the growth-chart strip below the 5 ft mark and white casing left of it, in the lamp/desk corner; Marina has plain wall there. First check what is behind that wall in the plan (a door must lead somewhere); the knob (36 in) + chart foot marks are also a film ruler for the pinstripe scale) -> bed fixture trial (the footlocker moves with the bed: spec/dressing/buzz_trunk.json x by the same -0.14; pack bed reworked, nudge ~0.14 m for adult passage, film pinstripes ~11.3 cm) -> chest of drawers) -> night shadows (8n) -> kernel steps 3, 4, 6 -> 8a furniture -> 8b compare page. REORDERED user Oct 17: "Right after step 2" (anxious to start Buzz)]
   FLICKER TEST RESULTS (Oct 17, live Play, foyer pose 8.4,-2.996,-9.4 yaw 268, still camera, day, AA off; tool Scripts/FlickerProbe.cs:
   FlickerProbe.Run(name,180) -> spec/captures/flicker/<name>.json/-first.png/-heat.png; needs Application.runInBackground=true when the
   editor is unfocused). Baseline maxLightsPerClusterCell 8: 4714 / 3902 / 4413 pop pixels (76/85/69 of 179 frames). 24: 1311, 5648,
   160665 (an outlier). 48: 3128. => the per-tile light limit is NOT the cause (run-to-run noise is larger than any effect; the first
   72% drop was noise). Shadows OFF on all 52 punctual lights: 2.46 M and 3.09 M pop pixels (far worse, every frame): the shadow/light
   system is implicated but not explained. Setting restored to 8 (asset unchanged). Day: 53 lights on, all shadowed; night: 45 + sun.
   ROOT CAUSE FOUND (Oct 17, measured): the 52 FilmFill ceiling area lights (SpecGreybox.Envelope.cs FilmFill, authored Baked, soft
   shadows) are NOT baked at runtime: BakeLighting.cs bakes Default then Night LAST with the day layer inactive, so the lighting data
   records the fills as not baked (in Play: bakingOutput.isBaked 0/52; night lamps Mixed->baked fine) and Unity renders them REALTIME
   with every-frame shadows. Foyer day, still camera: as built 72.4 M tris/frame, pops 1353/2090/1865; fill shadows off 6.6 M tris,
   pops 3350/2328; fills disabled pops 0/0/0 (3 runs). Night: no fills, no flicker (user saw the same). Also: day rooms are lit TWICE
   (fills baked into the Default APV scenario + realtime), and the day film calibration was tuned on that.
   FIX DONE and ACCEPTED (Oct 17, user walk; live: flicker 0/0/0, 72.4M -> 6.6M tris, GPU 144 -> 13.6 ms; changes/2026-10-17-filmfill-baked.json, DEVIATIONS 44):
   BakeLighting bakes Night first and Default LAST (the scene's one lighting data asset records the last bake's lights; restoring
   bakingOutput by hand would not persist: the scene YAML has no m_BakingOutput, it comes from LightingData.asset). New invariant
   BakeLighting.CheckBakedLights: after the bake the SAVED scene is reopened and every authored-Baked light must report isBaked
   ("Baked lights: N of M baked"; else "BakeLighting FAIL" and unity_pipeline.sh bake exits 1); also logs every light still real time
   in the saved day state. BakeLighting.VerifyBakedLights runs it on a saved scene in batch. Scratch: before 0 of 52, realtime 53;
   after 52 of 52, realtime 1 (Sun). Night lamps (Mixed, Baked Indirect) are now recorded unbaked: night renders pixel-identical to
   recorded-baked. FillNits 300 -> 600 (300 was tuned on the double light): film_light_match day 2677 wallpaper/stringer, 10248
   wallpaper/door: double-lit 0.62/0.90/1.07/1.19, baked 300 0.58/0.93/0.98/1.23, baked 600 0.56/0.88/1.07/1.19; fixed-EV level vs
   double-lit 0.94-1.05 at 600. Renders spec/captures/views/filmlight/. TO DO when loaded: in Play isBaked 52/52, FlickerProbe 3 runs
   (expect 0 pops) and PerfProbe (expect ~fills-disabled tris) before/after; user walk the day look.
   (Superseded) NEXT: a fresh-context investigation with research (HDRP square/tile flicker with many lights: light list ordering, shadow atlas
   eviction with OnDemand caching, contact shadows, SSAO/SSGI), each hypothesis tested with >= 3 probe runs against the baseline
   spread; HDRP Rendering Debugger overlays (light count per tile, shadow atlas). Fix must keep the look and frame time.

7. LATER (user Oct 17): shadow flicker STILL visible after the shadow pass (DEVIATIONS 62 did not fix it). Deferred to a dedicated
   performance + optimization pass; troubleshoot it there, not before. Same pass: ~80 CS0618 obsolete-API warnings (Unity 6.6:
   FindObjectsByType/FindFirstObjectByType sort-mode overloads, HDAdditionalLightData.spotLightShape): mechanical renames.
8. Living-room tree HEIGHT: ACCEPTED (user Oct 17: "the height seems right"): 2.40 -> 1.70 m from film 10645 (changes/2026-10-17-living-tree-height.json; 1.6-1.8 m
   after the depth correction). Built with the arch in copy 2; load + walk pending.
8s. [PAUSED by the user Oct 17; WIP on branch wip/foyer-rugs-stair (75caab5d), never built/reviewed; wainscot part superseded by HOUSE-KERNEL step 1] Main stair + landing finish (user walk notes Oct 17 08:30, spec/feedback/feel-notes.jsonl): (1) "shouldn't the rug be red?":
   the stair/landing carpet is built near-black; film 1616/2677 show a deep RED stair runner (measure colour from the film like the
   wallpaper); (2) landing wainscot on the right looks unfinished (pose 4.117,0.030,-8.559 yaw 264 pitch 33); (3) "weird triangular
   gap in the wainscotting" on the stair wall (pose 2.791,-0.682,-10.621 yaw 119 pitch 41). Trim check reports 0 gaps there: the
   check misses stair/landing wainscot: extend it (encode the lesson as a check).
8c. Foyer/living opening + antialiasing (walk note Oct 17 10:37, pose 7.575,-2.996,-9.748 yaw 182: "why is the casing missing on the
   right side? also is there no antialiasing? things looking a little jagged"). FOUND: (1) the casing leg IS built (Openings/Casing
   x 8.580-8.650, z -11.43..-11.41, full height); it is hidden by the French door leaf, which stands open INTO THE FOYER at the hi jamb
   (changes/2026-10-16-french-doors.json, TRIAL), so from the foyer the leaf covers the leg and wallpaper shows beside it. Decide from
   the film which way the foyer/living leaves swing and where they rest (10636/10645/12138/5650; leaves folded back against the wall
   outside the casing, or into the living room), then fix. Add a verification step: render every cased opening from both faces at
   Kevin + adult eye and set the film view beside it (an "opening review" sheet) before handover; a casing hidden by a model in its
   resting pose must be a stated, film-backed choice. (2) Player camera antialiasing was NONE (HDAdditionalCameraData.antialiasing):
   set live to TAA High for the walk (not persistent); make it permanent in SpecGreybox.Player() after the rug agent (it edits builder
   files): TAA (or SMAA High if the TV/traps ghost).
8w. Landing window + table (walk note Oct 17 10:18, pose 3.462,-0.977,-10.830 yaw 289): "the window still reads low; some shots of
   the foyer in the movie suggest it's a little taller and the bottom sill starts a bit higher up. we're also missing the matching
   table on the other side of the window" (DEVIATIONS 29: landing window head ASSUMED 72 in sash). Measure sill/head from film with
   solved cameras + a second ruler; add the pair table (film).
8r. [FRONT RUG DONE Oct 18 overnight11 (prop, not walked): tools/house/purchased_rugs.py thins+decimates both downloads to ~32k tris, pile normal from the photo; Nain on the front rug, Heriz on the living rug (DEVIATIONS 87). Runner from the film still on wip/foyer-rugs-stair] Foyer rugs (user Oct 17; next agent job after the arch/tree load): FRONT RUG = mfb64 'Persian Nain' (CC BY 4.0, credit
   required; Assets/Purchased/Rugs/persian_nain_carpet.glb, gitignored) fitted to foyer_props front_rug (cream field per film 1616/1690;
   squash 1.88 x 2.18: crop instead if motifs read squashed), purchased_plants.py-style fit, generated rug stays the fallback.
   RUNNER = the FILM'S OWN pattern (user pick): rectify from 2677/1616 like film_wallpaper.py (red field, hooked-lozenge chain, navy
   border, tan guards), generated mesh 0.74 x 3.41 with fringe + pile (artist-pipeline gate). heriz glb also downloaded (unused).
   STATE (Oct 17 rug agent, TRIAL): RUNNER built (hifi_foyer_runner.py, film_runner.py; changes/2026-10-17-foyer-runner-film.json;
   measured: no navy on film, the dark guards are red-brown). FRONT RUG: the Nain fit is DEFERRED to its own small trial (user):
   decimate the 628k-tri download to ~30-60k + a baked normal map, THEN fit (tools/house/purchased_rugs.py is ready; switch
   SpecGreybox.UsePurchasedRug on). The 190k-tri fit made the build's triangle checks run 27+ min. Until then the generated front rug
   (invented pattern) stays: the front rug's colour/pattern is still wrong. Credit line already in docs/CREDITS.md.
8n. NIGHT FRAME RATE (user Oct 17: "triangles baloon from 6.6 million during the day to north of 200 million at night"): FIXED. The paint cans (PaintCanTrap) had no damping; a nudge from the player (PushByPlayer) left them swinging forever, and ShadowRefresh.Near redrew every lamp in range each frame. Now damped while slow (<0.5 m/s), so the trap swing is unchanged. Live, night, foyer (1.5,-3.0,-10.0) yaw 90: swinging 209M tris / GPU 254 ms -> settled 2.1M / 35-46 ms (spec/captures/perf/night-cans-*). LEFT for the perf pass: night still costs ~3x day GPU at that pose (day 14 ms; 43 realtime shadowed lamps): fewer shadowed lamps, smaller ranges or shadow resolution. Any new moving thing that calls ShadowRefresh.Near must come to rest. NEXT (after kernel step 2, own small job; user Oct 17: "should it really be bumped up quite that high after hitting the trap?"): a swinging can still makes every lamp in range redraw ALL its casters (~200-370M tris/frame while it moves). Switch the lamps to HDRP mixed cached shadows (HDRP asset: allow mixed cached shadows; lamps OnDemand + alwaysDrawDynamicShadows; static casters cached, moving ones drawn each frame), then delete ShadowRefresh.Near and its callers (PaintCanTrap, SwingDoor). Prove: night, trap sprung, triangles while swinging ~= at rest (PerfProbe, 3 runs), lamp shadows unchanged in renders.
8f. FIDELITY PASS for generated models (user Oct 17, screenshot of the front door: "it still looks jagged. not a deal breaker for now, but i want it to eventually match the fidelity of the other higher quality assets we've used in the game"). Only 2 of 30 generated models went through the artist pipeline (model_quality: bevels, normal/ORM maps, baked albedo); the rest are sharp boxes. FRONT DOOR FIRST (hifi_door.py): moulded raised-panel profiles, bevels on every stile/rail/casing, a smooth elliptical arch, fanlight muntins that meet the hub cleanly, painted-wood maps; real brass hardware from a bought/scanned set fitted to the measured positions; the sidelight sheers (DEVIATIONS 41). Then audit the other pre-pipeline models, ranked by how visible they are (stair, windows, kitchen cabinets), and run each through the pipeline. Keep every dimension; this is look only.
8d. PAINT-CAN TRAP / TEST DUMMY: PAUSED (user Oct 17: "let's pause the dummy work for now"). Explainer: https://claude.ai/artifact/3weTsQs7HPMdi96GNXSBGM. On resume: test keys behind Shift (B sits beside N/M; the user summoned the dummy by accident); re-run SpecGreybox.TrapTest after the Oct 17 slow-can damping (check 2's 10 deg swing is now damped); mixed cached shadows (8n); bandit fall reaction.
8t. KERNEL STEP 1 follow-ups (user walk Oct 17 13:32: "mostly better now"): (1) top of flight 2: the raked panel/rail ends into the
   hall wainscot with visible misaligned joints ("small issues with alignment here", pose 3.010,-0.504,-8.502 yaw 56; the known 2.5 cm
   step, DEVIATIONS 66); (2) Z-FIGHT at the landing window stool/panelling (pose 2.235,-0.682,-9.391 yaw 266 pitch 39): the build's
   Z-fight check said 0 because it skips 25 unreadable meshes (Codex #10): the fast-checks job now makes the check see it; the fix
   (landing window panelling vs face trim: the window wall is "checked but not laid", yet something doubles) is a small follow-up.
   (3) landing inside corner (note 13:34, pose 2.671,-0.682,-9.090 yaw 320: "this alignment on wainscotting can't be right"): the
   landing-window wall's panelling (LandingWindow.glb, its own generator, cap level with the window stool) meets the north wall's
   face trim (0.705 cap, ASSUMED) at different heights. One wainscot height must run round the landing. Likely tied to 8w (user:
   the landing window reads low; film suggests a higher sill): if the film's sill sits on the wainscot cap, measuring the sill fixes
   both. This is kernel step 2 territory (openings own their trim): the window must take its panelling from the face trim.
    (4) walk note Oct 17 15:39 (7.33,-3.00,-9.59 yaw 297): the smooth underside under flight 2 is gone, the treads show from the hall. Cause found: the grey-box Dressing/Ground/flight2_soffit and flight2_stringer_open still exist but their renderers are off (the detailed stair replaced the grey-box look, and its model has no flight-2 soffit). Fix: give the detailed stair model a soffit, or re-enable those two renderers. (5) the foyer mirror reads low-res/blurry (reflection resolution or a better mirror asset): finishing pass.
    (6) walk note Oct 17 16:23 (1.967,-0.682,-8.378 yaw 328 pitch 35, kid eye): "you can tell in the corner here that the join isn't perfect": at the landing inside corner one cap rail's end pokes past the other's face (a nub). Construction rule for trim_faces.py: at an inside corner one run ends ON the other run's profile face (coped), the other runs into the corner; no end passes the other's front face; add it to trim_faces --check as an invariant over every inside corner. PROCESS MISS (user: "where's the miss in your process?"): (a) the trim check proved run ends TERMINATE (topology) but never the joint's GEOMETRY; (b) likely: the inside-corner setback uses the run's OWN depth, should be the depth of the run it meets (equal profiles hid it; the new landing-window rail may differ); (c) hand-back renders were metres away and reviewed as half-size thumbnails. Fix: the invariant above + coped-joint rule in the generator + every trim hand-back adds Kevin-eye close-ups of one joint per kind touched (add to zfight-check/room-upgrade skills). Do with 8w (sill re-measure) and the landing table 5 mm nudge (store_props x 1.596).
8u. KERNEL STEP 2 (TRIAL, Oct 17, not committed; changes/2026-10-17-openings-own-trim.json, DEVIATIONS 67): openings own their casing, header
   and limits. tools/house/openings.py -> spec/openings.json (54 openings, 182 casing pieces laid by SpecGreybox, 17 recorded drops, 151 limits:
   head under header, sill on wall, under ceiling, spring under crown, swing clear to 90 deg; a breach refuses the file, selftest plants the
   Oct 16 arch, a head off its header and a swing into a wall). Editor/SpecGreybox.Openings.cs lays it; switch openings.py OWN_TRIM (one line:
   also read by trim_faces.py and hifi_landing_window.py). Old vs new: 182/182 casings identical within 1 mm (old scene had 2 duplicate hall-arch-C
   legs); trim strips 93 identical, 14 moved (girls A/B + attic baseboard/cap +21.6/22.7 mm to the pack frames; vestibule baseboard cut at the
   front door plinths in data), 10 added (landing window wall: skirt, panel scribed under the apron/stool ears, rail to the casing legs). 8t-2
   z-fight fixed (wall cut to the rough opening under the stool: Z-fight 2 -> 0), 8t-3 fixed (one 0.705 wainscot round the landing; the panel
   stands 0.33 m above the stool beside the window until 8w re-measures the sill). Found, not changed: Props check landing_table back -0.5 cm into
   the new 1.5 cm landing panel (table at x 1.59; furniture out of scope: move to 1.596 if the user agrees). Preflight: HA_CHANGE=<record> lets
   only that record's missing AFTER renders wait for its `build -views`. Hall arches detail map fixed (preflight was red).
8p. PROCESS FIXES (full review: docs/reviews/2026-10-17-codex-process.md, 15 findings; its top three = this week's first work) (Codex review, Oct 17; do before Buzz): (a) unity_pipeline.sh build/bake swallow failures (`|| true` on the Unity
   build, the quality gate): stop build->bake->load on any failure; (b) change_gate R1 accepts model_quality alone as independent proof:
   topological gates must not count as the independent ruler; (c) pre-commit hook watches old paths, misses spec/geometry.json,
   hifi_*.py, spec/dressing/, House_WallGrid.unity; (d) walk notes don't store camera height/fov/day-night and note_views.py replays a
   Kevin-height note 0.55 m too high: record them in FeelNotes.cs, replay exactly; (e) "pick check": someone independent confirms WHAT
   a measured pixel shows before it is measured (the arch crown + "casing" were both the wrong feature). DONE: R2 now counts
   "failed (...)"/"rejected" outcomes (change_gate.py + selftest).
   BUILD TIME FOUND (Oct 17, measured with the step-1 agent's per-step stamps "[hh:mm:ss] BuildWallGrid: <step>"): generating the
   whole house ~1 min; every gate before ZFightCheck ~2 s combined; ZFightCheck (SpecGreybox.Checks.cs:29) is where the build sits
   for many minutes ("stuck" twice today: silent log, the report is only written at the end). Cause in the code: triangles are
   bucketed by PLANE only (normal + 1 cm offset), so every coplanar triangle in the house (all floor plates, rugs, ceilings at one
   height, wainscot faces on one line) lands in one bucket and is compared pairwise (O(k^2)); a 628k-tri rug on the floor plane
   made it effectively endless. Fix: add an in-plane 2-D grid (compare only triangles whose in-plane boxes overlap), skip pairs within
   one mesh, and cache results per mesh hash so unchanged geometry isn't re-checked; log each gate's duration as it finishes.
   BASELINE (step-1 build, Oct 17 12:42-13:10): all gates before ZFight 2 s; ZFightCheck 25 min 43 s; ClashCheck 80 s (already
   gridded, 0.1 m cells: second target); the rest ~1 s. Draft broad phase: tools/house/drafts/zfight-broadphase.cs.txt.
   GOAL (user Oct 17): FEWER EXPENSIVE REBUILDS. Measured on the rug job: ~60% inference, ~40% local, nearly all of it Unity batch
   builds at 7-10 min each. Do: (f) PREFLIGHT before any Unity build: every cheap Python gate (verify_plan, change_gate, build_models
   --check, model_quality, JSON/spec lint, refcam overlays) must pass first; (g) BLOCKOUT OVERLAY without Unity: project the planned
   geometry/furniture boxes through the solved film cameras onto the stills (refcam proj) so wrong features and layouts are caught for
   seconds, not a build; (h) ONE Unity session per candidate: build + checks + renders in a single -executeMethod (no relaunch between
   build and RenderViews); try a persistent warm scratch editor driven by the unity CLI instead of cold batch launches, and measure
   the saving; (i) stop at the first failure (no renders/bake after a failed gate); (j) log every build (id, job, wall time, why) to
   spec/captures/build-log.jsonl so rebuilds per job are counted and reported in each hand-back.
   8p STATE (Oct 17 afternoon; process/tooling only, no geometry):
   (a) DONE: unity_pipeline.sh build/bake keep Unity's exit code (no `|| true`), the quality gate (model_quality --report) fails the build.
   (b) DONE: change_gate.py SELF_GATES (model_quality, zfight, clash, verify_plan, trim_faces, unity:build, unity:walk-test) never count
       for R1; selftest: the arch record with only tools:model_quality fails R1 (passed before). No existing record changed outcome.
   (c) DONE: .githooks/pre-commit also watches spec/geometry.json, spec/trim_faces.json, spec/dressing/, tools/house/hifi_*.py, House_WallGrid.unity.
   (d) DONE: FeelNotes.cs logs "eye" (camera world y), "fov", "kid", "night"; note_views.py replays eye/fov exactly and writes night notes
       to views/notes-night.json (render with -night); old notes unchanged (47/47 identical views).
   (e) DONE: change-gate skill step 3 "pick check" (crop + independent confirmation of WHAT was picked) and R8 in change_gate.py for
       records with "gate": 8 (claim/check "pick": {"crop", "confirmed_by"}), with a selftest.
   (f) DONE: `unity_pipeline.sh preflight` (build_models/trim_faces --check, verify_plan, model_quality --report, change_gate over every
       record not rejected); build runs it first and refuses Unity on a FAIL; HA_NO_PREFLIGHT=1 skips. ON THE CURRENT TREE IT FAILS on two
       pre-existing problems: HallArches.glb 4 quality problems (Soffit_C detail map albedo; the paused upstairs-arches TRIAL) and
       changes/2026-10-17-filmfill-baked.json R7 (its live-play check is typed "topological", which triggers the layout rule). Decide:
       fix the HallArches detail map, and retype that check (e.g. "count") or narrow R7's topological trigger. Until then: HA_NO_PREFLIGHT=1.
       The extended pre-commit hook (c) also re-gates every record on those paths, so the filmfill R7 FAIL blocks such commits too.
   (i) DONE: `all` = build && bake && load, each now exits non-zero on any failure, so nothing runs after a failed step.
   (j) DONE: build/bake append {"time","cmd","job"($HA_JOB),"why"($HA_WHY),"wall_s","exit"} to spec/captures/build-log.jsonl (EXIT trap,
       refused builds included).
   (g) PLAN: refcam.py already solves film/Marina cameras (13 in measurements/cameras/) and `overlay` draws spec/geometry.json walls,
       openings, stairs and foyer dressing on the frame. Missing: (1) overlay every dressing file (spec/dressing/*.json, store_props boxes,
       furniture.json), not just foyer.json; (2) a `--spec DIR` / candidate geometry option so a draft is overlaid BEFORE it is in spec;
       (3) `overlay-all` over every solved camera seeing the touched room -> one contact sheet; (4) a pre-build checklist line in
       room-upgrade/change-gate: look at the overlay sheet first. No Unity involved; seconds per candidate.
   (h) PLAN: half exists: `build -views FILE` already renders in the build's session (SpecGreybox.cs:392). Missing: (1) make that the
       default for candidates (views list in the change record -> passed automatically); (2) a warm scratch editor: open ~/.cache/
       home-alone/ucopy/HomeAlone windowed once, drive SpecGreybox.BuildWallGrid/RenderViews through `unity command eval` (as `ev` does
       for the user's editor) instead of cold -batchmode launches; (3) measure cold vs warm with the build-log (j) wall_s over 3 builds
       each before switching; keep cold batch as the fallback (domain reload after C# changes still needed).
8y. LATER (user Oct 17, 'for another day'): recess the under-stair door in the rear passage like Marina's (her passage widens left beyond the stair line into a recess, DEVIATIONS 35); the foyer arch attempt 3 is accepted for now.
8z-1. BUZZ TRIAL 1 (layout) ACCEPTED Oct 17 ("left a comment, but i generally accept"). Follow-ups for trial 2: (a) the black boxes hanging by each window (pre-existing, likely valances: identify and replace with the film/Marina curtains); (b) dark dithered lines along the wall/ceiling and vertical corners (night, note 18:10 at 8.449,0.030,-14.174 yaw 77): find what is drawn there (envelope/shadow caps seen through a seam? AO?) before fixing; (c) DECIDE with the user: Kevin cannot hide under the low bed (DEVIATIONS 72); (d) door-to-bed gap 0.69 vs Marina 0.48 (DEVIATIONS 69). NEXT TRIALS: film wallpaper/paint, real furniture models (bed, chest, shelves, tank), lighting.
8z-2. BUZZ TRIAL 2 (Oct 17, TRIAL, loaded, not walked): (a) corner lines = APV probe cells with no valid probe in the overhang strip (BakeLighting invalidated the strip's probes; raw outdoor light: bright by day, dark by night; Kevin's room too): the strip now bakes with its own walls, FilmFront out of the bake, and the bake FAILs any invalidation inside a room; (b) the black boxes were the reference scene's facade shutters inside the rooms: SpecGreybox.Exterior removes any exterior part reaching into a room; (c) drapes (film grey + sheer on Marina's geometry, DEVIATIONS 74; decoration) and film paper + baseboard + wood floor (changes/2026-10-17-buzz-finish.json, DEVIATIONS 75). Open: frieze + crown (75), Buzz's blue day floor (77, lighting trial), grey vs green drapes (user).
8z-3. BUZZ DAYLIGHT COLOUR (Oct 18, overnight3b, TRIAL, loaded, not walked; DEVIATIONS 83): navy floor/chest by day = room reflection probes not lighting LayerOverhang (sky specular); probes now on every layer and re-rendered after each scenario's bake; DayGrade white balance removed; paper ground chroma from film 2766. Floor R/B 0.65 -> 6.3, paper 2.9 -> 2.2; foyer film warmth closer on all 4 regions. daycheck gained a Buzz floor-warmth gate. Captures ~/.cache/home-alone-2/captures/overnight3b-*.png. Also: `unity_pipeline.sh bake` now syncs Editor/ first (a bake-only BakeLighting change never ran).
8z. NEXT BIG JOB (user Oct 17, after this TRIAL is walked): BUZZ'S ROOM, room + furniture, nailed. It caused most of the Oct 13-14
   drama (resize reverted, changes/2026-10-13-buzz-resize.json; furniture didn't fit). change-gate R2 applies (4+ failed attempts):
   start with premise_reviewed + a census of what every failed attempt shared; DEVIATIONS 23-26 (door-to-desk wall 4.46 m has no
   independent check); furniture by furniture-placement-faithful (measure each piece from the corner, place the whole sequence);
   film (500-518) + Marina tour; walk it at Kevin's eye. User: "if we can nail this room i'll feel great about things".
   USER: same approach as the den and living room = the room-upgrade skill's full dressing pass (film paint/paper, windows as
   models, generated built-ins via artist-pipeline, bought/CC0 hero props, lamps + night light-match, colliders, before/after vs
   film + Marina). Lesson from the living room: place every piece from SOLVED cameras, never by eye.
8a. Living + den furniture re-layout (user walk Oct 17: piano needs rotating, sofa on the WRONG WALL, den desk needs rotating).
   User rule: FILM where it shows the piece, Marina only for what the film never shows. Living positions were placed by eye
   (DEVIATIONS 59): solve pitched film cameras (10636/10645, 5650, 10600; living_walls.py model) and re-place sofa, console,
   piano, coffee table from them. USER (Oct 17): in the film the SOFA FACES THE FIREPLACE (rear wall); find the frames that
   show it and set its line and distance from them.
   TREE POSITION (walk note 08:32, pose 4.711,-2.996,-12.289): "the tree should sit a little bit further from the window; marv enters
   through the window and steps on ornaments as a trap. i want to leave that as an option" -> keep the floor in front of the den-side
   rear window (z 15.015-15.825 on the rear wall x 1.58) clear for Marv's landing + an ornament trap (film 10590-10620); film 11995 shows
   the tree BESIDE the window (the film's window stands further from the corner than ours: DEVIATIONS 59). Re-place with the solved cameras.
   Walk notes Oct 17 08:31: 'couch still doesn't appear where expected' (8.433,-2.996,-12.943 yaw 245); 'piano position is off' (7.505,-2.996,-13.158 yaw 149).
   FILM 11995 + 12115 (Christmas morning, found Oct 17) are the KEY frames: wide view of the rear wall: sofa (green) faces the
   fireplace; floral armchair + ottoman right of it; tree stands BESIDE (left of) the den-side window, not in front of it; tree has
   small multicolour MINI lights (not C7s: revisit hifi_living.py C7 choice from 10600); wreath + two green-shaded lamps + photo on
   the mantel; red Oriental rug; side table with milk/cookies by the tools. Check which wall the film's console wall is (10645: French door at its left end, tree in the
   corner to its right). Den desk: film if seen, else Marina f153/f161. Change-gate + before/after; then 8b re-renders.
8b. Fidelity compare page (artifact https://claude.ai/artifact/GqCSM6YXCgvsJpy6grdm8U; builder tools/house/fidelity_page/ (fid_build.py ROOT OUT; index.html embeds pairs.json)):
   after the arch + tree, re-render every pair from the current build, add dining (Marina 228) and kitchen 2528, and solve film
   10636/5650 cameras (pitched model, living_walls.py) so those two views match; republish to the same URL.
9. FINISHING PASS (user Oct 17, skip until then): fireplace mantel regenerated via the artist pipeline (film Adam style, Marina f165
   sizes) + a toggleable log fire; needs the firebox recessed ~0.4-0.5 m into the outside chimney (change-gate).

### Operating rules learned Oct 16-17 (also in memory)
- One scratch copy per heavy job (HA_SCRATCH=~/.cache/home-alone-N tools/house/unity_pipeline.sh ...); disk is tight (~34 GB free;
  copy 1's Library is 26 GB). Wait for a copy with an ANCHORED pattern:
  `while pgrep -f '^/Applications/Unity/Hub/Editor/[^ ]*/MacOS/Unity .*/\.cache/home-alone/ucopy' >/dev/null; do sleep 10; done`
  (unanchored patterns match the waiting shell itself and deadlock).
- Never save uncompiled C# into the repo's Assets/Editor or Scripts: the user's open editor compiles them live (Safe Mode once).
  Draft and compile in scratch, then copy.
- `load` now switches the editor to an empty scene before copying (overwriting the open scene raised a modal reload dialog that froze
  the editor for hours). If editor commands time out with the screen awake, ask what dialog is showing. The editor also freezes
  while the Mac's screen sleeps.
- Purchased assets (Asset Store packs, CGTrader models, the user's video) are gitignored: the repo is public. Never send the user's
  email or personal data in any web request (one agent leaked it into Wikimedia's logs via User-Agent).
- Built-ins are generated to measurement (artist-pipeline skill); organic/soft hero pieces are bought or scanned
  (docs/furniture-plan.json: $0 start plan, hero upgrades $81.99).

## RESUME HERE (Oct 16, 2026, afternoon): systems pass done; day lighting matches the film's set; walk notes queued

**Read this section first. Then read `tasks/wall-grid-plan.md` ("Walk notes queued", including the deferred overhang split) and
`docs/DEVIATIONS.md` 1, 34 and 40-45.** The Oct 15 section below is history except where this one points to it.

### How to build, bake, load and look (one script: `tools/house/unity_pipeline.sh`)
- `setup`, once per machine: makes the scratch build copy at `~/.cache/home-alone/ucopy/HomeAlone`, plus a `spec` link. It exists now,
  Library imported. Never build in the user's open editor.
- `build`: copies Editor, Scripts, Models and `HDRP.asset` into scratch and builds `House_WallGrid` in batch (~30 s). Gates go to
  `spec/captures/walk-test-wallgrid.txt`:
  - Seam, Z-fight, Clash, Casing, **Trim**, **Envelope** must all be 0.
  - The walks pass except the pre-existing back-stair stall at winder 2.
- `bake`: day and night, ~60 s. It runs WINDOWED on purpose: batch mode has no render loop, so no sky, and `BakeLighting.Bake` refuses
  batch mode. It renders a camera for the sky; it does not wait on editor frames (a background editor ticks only every few seconds).
- `load`: copies the scene and bake into the project, waits until the editor is neither compiling nor importing, opens the scene and
  enters Play. Entering Play mid-import crashed Unity natively on Oct 16.
- `all`: build, bake, load. Spec or reconciler edits still go through `verify_plan.py` and the change gate first, as before.
- `shot NAME x y z yaw pitch [day|night]` (player pose; feet, eye +1.28) and `cam NAME px py pz lx ly lz vfov near [day|night]` take
  live captures in the user's running editor, with a clone of the player camera. They never move the player. They land in
  `~/.cache/home-alone/captures/`.
  - **Judge lighting only from live captures**; batch renders lie about it.
  - Walk-note poses are in `spec/feedback/feel-notes.jsonl` (pos = feet, yaw, pitch).
  - Film camera poses solved earlier are in `spec/captures/views/views-foyer-film-after.json` and `film10248.json`.
- New script in `Assets/Scripts`: create it in the repo project FIRST. Each project gives a new `.cs` its own `.meta` GUID, and a
  scene built in scratch then points to a missing script. `load` warns when they differ.
- The same GUID trap hits new MODELS and TEXTURES (Oct 16: the kitchen cabinets loaded with empty meshes): `load` now copies the
  scratch copy's `.meta` for every built model and texture into the project ("synced GUID: ...").
- Discriminator technique for "why does it look wrong":
  - Capture the same view with one HDRP frame setting off (SkyReflection, ReflectionProbe, SSR) and compare region means. That found
    the reflection-probe box bug in minutes.
  - For "is X in the bake", bake with X on and off and diff the scenario's `CellData.bytes`. The sky changes ~8% of it.

### The lighting model now (Oct 16), so nobody re-litigates it
- **The house is light-tight** (DEVIATIONS 43). `SpecGreybox.Envelope` generates invisible shadow-only skins, lids, floor framing and
  recess framing from the spec, clipped out of every room. The Envelope check (rays to the sky from every room joint must cross
  >= 0.3 m of structure) is 0.
- **Trim is laid along room outlines**, so joints close by construction. The Trim check ray-tests the built scene.
- **The bake** (`Editor/BakeLighting.cs`):
  - Probes outside the room volumes are invalidated: the ceiling band, note 11:16.
  - Glass doesn't block the bake.
  - Reflection probes come from the room volumes (`SpecGreybox.EnvelopeRooms`, which runs the stair well down to the ground) and
    reach 7 cm past every surface with a 5 cm fade. A short box let the sky fill in: grey-blue rooms by day.
  - Day and night each have their own reflection images, swapped by `HouseNightMode`.
- **Day look = the film's set lighting** (user choice, DEVIATIONS 44). `SpecGreybox.FilmFill` puts baked-only ceiling fills in every
  room: 600 nits (300 until Oct 17, tuned while the fills were also drawn in real time: STATUS 7a), 5200 K, solved against film 2677 and 10248 by `tools/house/film_light_match.py`.
- **The foyer fixtures** are lit at night only; by day the bulbs and shades are dark too.
- **Orientation:** the front faces 227.6 deg (SW), measured (`tools/house/house_bearing.py`, OpenStreetMap). The film was shot here,
  so this is not a deviation. The sun's TIME is still a placeholder (DEVIATIONS 34).
- **Overhang stop-gap** (DEVIATIONS 45). `SpecGreybox.FilmFront` is a shadow-only flush "film front". The upstairs pieces past the
  ground footprint go on rendering layer 1. `StoreyShadows` switches the one sun's shadow casters per storey (HDRP allows a single
  shadowed directional light). The proper split is deferred (tasks/wall-grid-plan.md).
- Mac: Unity HDRP has no ray tracing on Metal (measured: `SystemInfo.supportsRayTracing` False; Unity 6000.6 reports macOS RT
  features None). Bounce light is baked.

### Oct 16 late: answered so far
- Lighting notes 11:16 / 11:43 / 11:49 / 12:03 / 12:48 re-captured live: they read right now.
- Note 11:26 (landing window low): no change. Film 11966 puts the sill at ~0.52 of the hall table (0.385-0.405 m above the landing
  for a 0.74-0.78 m table) vs our 0.36 m; the undressed landing table makes it feel lower.
- **Note 15:06 (kitchen back door + dog door): waiting on a user decision**, https://claude.ai/artifact/9EFUbsKnUxUx6Pvc6U16Gg.
  `tools/house/kitchen_walls.py` (new SfM `sfm-work/rooms/kitchen-sink`, Part 1 1088-1112 s, door wall + sink wall planes) puts
  Marina's kitchen end wall at 5.27 m inside (80 in door ruler; the counter lands on 0.911 m high, 0.641 m deep; tiles 0.286 m) vs the
  traced 4.20 m. The door casing is 1.05 m from the sink-wall corner (ours 0.40), the leaf is 36 x 80 in (film 6902 ratio 0.44),
  and the sink-window stool is at 1.23 m (our sill 0.82, below the counter). Her stated 477 ft2 also says the traced kitchen zone
  (340 ft2) is too small. Recommended: re-measure the whole kitchen/breakfast wing and rebuild it wider. The film exterior's
  window-door spacing (1.81-1.93, brick ruler) still holds.
- **Kitchen wing rebuilt (TRIAL, not committed, not loaded; changes/2026-10-16-kitchen-wing.json, DEVIATIONS 46):** 5.00 m wide inside (seat wall flush with the sunroom at z -0.915, sink wall z 4.085), length unchanged; back door 36 x 80 in at z 2.525 as a model (`tools/house/hifi_back_door.py` -> BackDoor.glb: nine-lite sash, dog door, tie-back curtains + sheer, brass knob/deadbolt/hinges); end and sink windows 32 x 32 in, sills 1.22. Linen-closet prop door 30 in (changes/2026-10-16-linen-door-30in.json). Scratch copy built and baked (gates 0); `unity_pipeline.sh load` NOT run (user busy in the editor). Renders: spec/captures/views/kitchen/{before,after}-*.png. Measurement tool: `tools/house/kitchen_walls.py` (default / --wing / --plan).
- **Kitchen cabinets (TRIAL, not committed, not loaded; changes/2026-10-16-kitchen-cabinets.json, DEVIATIONS 47):** `tools/house/hifi_kitchen.py` (data spec/dressing/kitchen.json, positions from `kitchen_walls.py --fixtures`) -> KitchenCabinets.glb; tile maps `tools/house/kitchen_tile_tex.py`; wood Poly Haven cherry_veneer; colliders from kitchen.json; seat-wall windows now Marina's two (over the seats). Pipeline `build` now also syncs Assets/Textures.
- **Kitchen night lighting (TRIAL, not committed, not loaded; changes/2026-10-16-kitchen-night-lights.json, DEVIATIONS 48):** under-cabinet strips (hifi_kitchen.py KT_UnderLight + rectangle lights) and the breakfast chandelier (`tools/house/hifi_kitchen_lights.py`), placed by SpecGreybox.KitchenFixtures, on the night layer; generic Light_kitchen/Light_back_stair removed. Calibration: `film_light_match.py --night spec/captures/views/kitchen` (re-run on live captures).
- **Breakfast table (TRIAL, not committed, not loaded; changes/2026-10-16-breakfast-table.json, DEVIATIONS 49):** `tools/house/hifi_breakfast_table.py` -> BreakfastTable.glb (oval 2.20 x 1.26, double pedestal, oak_veneer_01), colliders in kitchen.json; back-stair walk test start moved east of it (reconcile.py).
- **Kitchen wallpaper from film 6910 (TRIAL, not committed; DEVIATIONS 50):** `film_wallpaper.py --kitchen` -> spec/dressing/kitchen_wallpaper.png/.json, applied by SpecGreybox.KitchenPaper() to kitchen + back-stair walls.
- **Den upgrade (TRIAL, not committed, not loaded; changes/2026-10-16-den.json, DEVIATIONS 51-53):** film teal paint (film 2877; Marina's is a darker green: user call), both windows as four mulled 24 x 66 in 6-over-6 units (tools/house/den_walls.py: cameras solved on the built den's corners in Marina's den clip; the real-house plan agrees on the front window), Marina's floral valance + tie-back drapes (no sheers: the sheer pass), built-in bookcase + TV/VCR/books, Poly Haven sofa/armchair/coffee table/TV, Fadnn desk/chairs/lamps/side table. Models: tools/house/hifi_den.py, hifi_den_props.py, SpecGreybox.Den.cs, spec/dressing/den.json. Renders: spec/captures/views/den/compare-*.jpg. Scratch built and baked, gates 0.
- **Foyer finish (TRIAL, not committed, not loaded; changes/2026-10-16-foyer-finish.json, DEVIATIONS 56):** film-first furniture and decor from spec/dressing/foyer_props.json (readings: tools/house/foyer_props_measure.py on film-1616fc / film-2677): Hepplewhite console (top 0.762), two mahogany side chairs (red seats, vase splat), tall gilt pier mirror with crest (1.12-2.20 m), green rolled-arm bench, film-sized runner and front rug (invented Persian patterns), a 10-frame stair gallery (8 measured), the picture under the landing, the landing camellia print, poinsettias (console, under it, landing table) and a vestibule basket plant. Pictures are public-domain works (spec/dressing/foyer_art.json); the door prints' film cuts were replaced the same way. Models: tools/house/hifi_foyer_props.py -> FoyerProps.glb, textures tools/house/foyer_textures.py, placed by SpecGreybox.FoyerProps.cs. Renders: spec/captures/views/foyer-finish/compare-*.jpg. Scratch built and baked, gates 0. Found, not changed: the film's wainscot cap reads 6-8 cm above our 0.705.
- **Bought plants (TRIAL, not committed, not loaded; DEVIATIONS 61):** CGTrader ficus (foyer, by the stair) and poinsettia gift plant (foyer x5, den x2, living x1; gold foil, white copies) fitted by tools/house/purchased_plants.py into the GITIGNORED unity/HomeAlone/Assets/Purchased/ (raw downloads in sfm-work/purchased/; Royalty Free, no redistribution). SpecGreybox.PurchasedPlants places them and hides the generated plants; without the folder the generated ones stay. unity_pipeline.sh build/load sync Assets/Purchased. Rebuild after a fresh download: unpack into sfm-work/purchased/{ficus,poinsettia} (bsdtar -xf textures.rar), then run the Blender script. Renders: spec/captures/views/purchased/compare-*.jpg.
- **Living room upgrade (TRIAL, not committed, not loaded; changes/2026-10-16-living-room.json, DEVIATIONS 57-60):** the film's rose-swag paper (film 10636; `film_wallpaper.py --living`, 0.533 x 0.79 m) over a 0.14 baseboard, wood floor; rear windows widened to stock 2'8" 6-over-6 (Marina f165 + the real-house plan), French pairs in the front cuts, the film's green damask drapes + sheers + Marina's valances (`tools/house/hifi_living.py` -> LivingWindows.glb, reusing hifi_sheers.py's cloth); fireplace/hearth/screen/stockings, the film's console upright piano + bench + lamp (Marina has a grand: user call), lamps, brackets with dogs, nutcrackers, train, rug, the user's Asset Store Christmas tree (AlterEgos, gitignored `Assets/ChristmasTreeAndGarland`, store_props living_tree, mini lights replaced by generated C7 bulbs; StoreProps gained `hide_parts` and converts alpha-cutout pack materials) (LivingBuiltins.glb); piano: the user keeps the generated upright; Poly Haven sofa/console/coffee table/painting/clock/stand (`hifi_living_props.py` -> LivingProps.glb); pack chest (store_props living_chest); `SpecGreybox.Living.cs`, spec/dressing/living.json, finishes.json `paper`. Cameras: `tools/house/living_walls.py` (Marina's living clip needs pitch/roll: refcam's level model left 13 px). Room walk test now stands a body beside furniture at a room's centre (den and living were skipped). Night calibration `film_light_match.py --living-night` (sheers +1.4-2.2 stops, warmth far orange: see DEVIATIONS 60). Renders spec/captures/views/living/compare-*.jpg. Scratch built and baked, gates 0.
- **French doors + kitchen sconces/gallery/desk (TRIAL, not committed; changes/2026-10-16-french-doors.json, 2026-10-17-kitchen-fixtures.json, DEVIATIONS 51-52):** tools/house/hifi_french_doors.py, hifi_kitchen_gallery.py, hifi_kitchen_lights.py (sconces); Editor/FrenchDoors.cs, Editor/SpecGreybox.KitchenLights.cs. Open: the film's breakfast table reads ROUND (1151, 1049) vs Marina's oval (built); the second stair sconce not found.
- **Upstairs halls + arches (TRIAL, not committed, not loaded; changes/2026-10-17-upstairs-hall.json, changes/2026-10-17-upstairs-arches.json, DEVIATIONS 63-64):** the film's teal paint over a white wainscot (cap 0.76, baseboard 0.11; `tools/house/hall_walls.py --paint/--heights/--arches`), wood floor, fitted crimson runner, crown, four brass tulip sconces lit at night (350 lm; `film_light_match.py --hall-night`: wall falloff -0.1 stop vs film 10819, floor +1.4 stops brighter, light warmer), urn stands with the purchased poinsettias, ficus, two SIDE_TABLE_01 hall tables, public-domain pictures (`hall_textures.py`), tapestry, clock/barometer (`hifi_hall.py`, data `spec/dressing/hall.json`, `SpecGreybox.Hall.cs`). Arches: B and C segmental (doors file crown/spring -> reconcile; verify_plan 0 FAIL), A the film's elliptical gallery arch (2085 solved) as a papered header, crown 2.30 under our 2.40 ceiling (film 2.39: user call). Built in ~/.cache/home-alone-3. Renders spec/captures/views/hall/compare-*.jpg.
- User, Oct 16: use stock door/window sizes wherever possible (the front door excepted). The upstairs linen-closet prop door
  (24 in) is too small: 30 in fits its 0.986 m wall centred. Not built yet.

### NEXT (in order)
1. **Read the user's walk notes on the TRIALs** (commits 4168e17, 09dd918, e30aa30, 0e3b560): the last lines of
   `spec/feedback/feel-notes.jsonl`. Answer each from its own pose, captured live.
2. **Note 11:26 "this window feels a bit low, can you confirm?"** (pos 3.993, 0.03, -8.677; yaw 251, pitch 22.6: upstairs, looking at
   the landing window). Its numbers are in `measurements/windows/ground.json` `wall_openings.landing_window`: sill y 2.69 ground
   metres, from film 11966 / 12133 and Marina 312 s. Check them with refcam from a solved film camera before changing anything.
3. **Note 11:47:** is the foyer-living opening sized like the living-den opening? (the den one looks smaller). Case both. Measure both
   from frames; the casing comes from the cut automatically (`kind: arch` + `cased: true`).
4. **Note 10:48:** the dining front windows faithful to the film and Marina. They're French windows to the floor now; check against
   the film's front (frame 4382 shows them) and Marina.
5. **The rest of the day look:**
   - Our wallpaper texture is deeper red than the film's pink-cream (2677 wallpaper 0.6x relative).
   - The foyer floor reads grey-brown, not the film's dark wood with a red rug.
   - Solve film 11966's camera and add it to `film_light_match.py`, then re-solve FillNits/FillKelvin.
   - The dining and living rooms aren't compared with film frames yet.
6. **Time of day** (DEVIATIONS 34): solve the sun from film 4382 (portico and branch shadows on the facade).
7. **Exterior shutters** (WinterNeighborhood) stand inside Kevin's room (the upper ones, x 10.43) and hang over our front windows (the
   ground ones). This is split and exterior work.
8. Carried over from Oct 16 morning:
   - The back-stair foot: Marina 321 / 1072.5 s show ONE foot step vs our 2. Solve those frames first.
   - The back-stair stall at winder 2.
   - The rest of the dining dressing (hutch, table, chairs, paintings, French doors).
   - ~~Mirror boxes, bench, the picture under the landing.~~ Done as the foyer finish TRIAL (Oct 16). Still open: upstairs-hall poinsettias (H1), the upper gallery frames (solve film 3225/10775).
   - Real sheers (DEVIATIONS 41).
9. Deferred by the user: **the upstairs split** (overhang exists only from the stair up; tasks/wall-grid-plan.md).

### Working rules learned Oct 16 (also in memory)
- Joints that should meet must meet by construction; prove it with a scene check (walls-touch, pstack memories).
- After two failed fixes on one symptom, write the shared premise down and test it directly (e.g. bake with X on and off). Research
  online instead of spinning.
- Never claim a look is fixed without a live capture from the user's view. Commit messages say TRIAL and claim only what was checked.

---

## RESUME HERE (Oct 15, 2026, evening): phase 5 done, back stair in progress

**Read this section, then `tasks/wall-grid-plan.md` (phases + "Walk notes queued"), then `docs/DEVIATIONS.md` 20-22 and 30-38.**

### The working scene is now `House_WallGrid` (wall-grid builder), not the old `Greybox_Upstairs`
- Build: `uv run --with numpy python -I tools/house/wall_graph.py --json` (spec -> `spec/geometry.json`), then in the batch copy
  (a copy of `unity/HomeAlone` in the session scratchpad: `rsync -a --exclude Library --exclude Temp unity/HomeAlone/ <scratch>/ucopy/HomeAlone/`, plus a `spec` symlink at `<scratch>/spec -> repo spec`;
  never build in the user's open editor): copy `SpecGreybox.cs` in, run `-executeMethod SpecGreybox.BuildWallGrid`, copy
  `Scenes/House_WallGrid.unity` + `Materials/Greybox` + `Settings/GreyboxVolume.asset` back. Gates land in `spec/captures/walk-test-wallgrid.txt`
  (door walks, stair walks incl. the Player's controller, seams 0/0/0, leaks, PEEK = no sight line into a closed space, room walks).
- Spec changes go through the trace/doors files (`measurements/overhead/ground-trace.json` "m" polygons, `ground-doors.json`) and
  `tools/house/reconcile.py` (stairs are generated there: main stair, `service_stair_spec`, attic), then `verify_plan.py` (both floors),
  then the change gate (`changes/*.json`, `tools/house/change_gate.py`). Pre-commit hook enforces it.
- Load for the user (memory: load-scene-for-walk): `~/.unity/bin/unity command list_open_scenes` (isDirty false) -> `editor_stop` ->
  `recompile` if the script changed -> `open_scene Assets/Scenes/House_WallGrid.unity` -> `editor_play` -> `editor_focus`. Retry if Unity is busy.
- The user leaves walk notes in Unity (key M): `spec/feedback/feel-notes.jsonl` + `spec/feedback/shots/`. "Look at my comment" = read the last lines there.

### Verification rule (user, Oct 15: "give yourself the tools you need to become as accurate as possible")
Every placement read from a reference frame goes through **`tools/house/refcam.py`** before it is built:
`frame` (get a Marina/film frame) -> `grid` (read pixels) -> `solve NAME FRAME points.json` (camera from known 3D points, per-point
residuals; points files in `measurements/cameras/points/`, cameras in `measurements/cameras/`) -> `measure NAME u v --plane x=..|z=..|h=..`
(read a position in plan metres) -> `overlay NAME --floor ground` (the build's walls/openings/stairs drawn on the frame) -> `view NAME`
(Unity camera for a matched render). Never place by eye or from a subagent's plan-terms description alone; name the spaces on both sides
of any door first (memory: check-placements-against-plan). Known-good: refcam reproduces the film 2677 camera (x 10.50, h 0.81, f 2263).

### What was done Oct 15 (all committed and pushed on branch unity-sfm-reconstruction)
- **Foyer back wall from the film** (foyer_cameras.py: two film cameras solved from flight 1's nosings): cased segmental arch, crown 2.17,
  springline 1.91; rear passage to the rear door; the arch's LEFT side runs to the main stair's side (no pier: Marina 195 s / 1070.5 s
  + user). Passage left wall flush with the stair's side (user). Closet door on the passage's right wall; the user's circled "door
  under the stair" is on the passage's left wall facing it (both closed props, sizes authored, DEVIATIONS 36).
- **Phase 5 (wall-grid house, scene House_WallGrid)**: stair hall as one two-storey space (stack decisions in `grid-snaps.json`,
  DEVIATIONS 37), landing as a slab, rails as 6 cm bands, floor per room, PEEK gate. **User walked it: "looks generally good."**
- **Comparison pages (fade sliders)**: arch/foyer https://claude.ai/artifact/X3oYBgypJhhUAZ53Vikxg8 ; stair hall vs Marina/film
  https://claude.ai/artifact/MWNxwxzmFcgFHhvFezCjdN ; back stair / breakfast room https://claude.ai/artifact/Y6g9C2T959jaikXUE66jv8
- **Back stair rebuilt (TRIAL, d4b1605)**: 4 foot steps toward the wall between a dark newel and a tall post, quarter landing 0.89 m,
  flight along the wall (going 0.262) to the ceiling; dark treads, white risers/stringer/balusters; papered spandrel; Kevin's basement
  door under the flight's high end (first put on an outside wall: wrong). Kitchen walls cream, floor quarry tile (colours only).

### NEXT (in order)
1. **Back stair: the user says it is "still kind of messed up".** My read from the Marina 916 s fade (camera placed by eye, so verify):
   her stair sits ~0.5 m further toward the foyer doorway (newel just right of the doorway, ~x 2.9; tall post ~x 1.8), her flight is
   shorter/steeper and meets the ceiling ~x 0.0, and her basement door (~x -1.2 to -0.3, with casing) has wall to spare before the corner
   (x -1.505). Ours: newel x 2.37, post 1.39, ceiling at -0.71, door jammed at the end (-1.43 to -0.72). Do it properly with refcam:
   solve Marina 916 s and 933 s cameras from the room's known points (foyer doorway jambs x 3.043/4.025 on the z 7.638 face, head
   2.20; the back-right corner x -1.505 / z 7.638; the side-wall window x -1.505, z 4.99-5.79, sill 0.82, head 2.15; ceiling 2.438; the
   hutch-wall corner x 4.12), then `measure` the newel, tall post, the flight's nosings and ceiling arrival, and the door's jambs; then
   film 2528/928/912 the same way; rebuild `reconcile.service_stair_spec` from those numbers (the stair may extend past the traced
   back_stair enclosure toward the doorway: check the kitchen floor between it and the hutch wall); overlay before building; update the
   kitchen-compare page; load for the user. Back-stair references: `art/home_alone/references/back-stair/` and `kitchen/frames/` (best-*.jpg);
   key ones: film 912, 928, 1044, 2528, 3607-3617; Marina Part 1 916, 924, 933, 934, 938 s; kitchen overhead 812 s.
2. Queued walk notes (tasks/wall-grid-plan.md): the arch a bit lower (Marina ~1.9-1.95 m vs film 2.17: decide with the user); the passage
   width and its doors (later); the foyer's north wall line (DEVIATIONS 35); the kitchen's left side / rear wall length (Marina's
   overhead and interiors disagree); finishes (floral paper, beams, cabinets, hutch, table, fridge).
3. Phase 6-8 of the wall-grid plan (rest of the house, windows, the chute shaft and hatch, user walk), then the exterior against the film.

---


**PIVOT (user, Oct 13 evening): correct the EXISTING model, not the grey-box.** The working scene is again `IntactHouseReference` (the downloaded GLB at 0.774 m/unit, edited by the September `SurveyBuilder` editor scripts; the source GLB stays untouched). The ground floor there feels right to the user. Upstairs, Buzz's room feels cramped (3.82 × 3.24 m against Marina's 4.35 × 3.49 m; the hall beside it is 1.89 m wide against her 1.58 m). Apply the same principles to the old model: Marina is the authority, cite frames, take a census before fixing, prove every check fails on an injected error, log departures in DEVIATIONS.md, never move outside walls, and use the room-feel skill order. The grey-box, spec and checks below stay as the measurement record and as the target numbers.

The upstairs is measured, reconciled into a spec, built as a walkable Unity grey-box, and verified against video. That includes independent evidence. **Next: the ground floor.** Every deviation from measurement is in [DEVIATIONS.md](DEVIATIONS.md) (top: the upstairs front wall overhangs the ground floor's by ~1.6 m; rooms keep Marina's shapes). Shape check: `uv run --with numpy python tools/house/shape_drift.py`. Background reading: [RECONCILIATION.md](RECONCILIATION.md) for the architecture, [tasks/sfm-plan.md](../tasks/sfm-plan.md) for the full experiment log, and the `verify-plan` skill for every check.

Branch `unity-sfm-reconstruction`, pushed to `origin`. Git LFS covers `*.glb *.blend *.exr *.fbx *.psd *.tif *.tiff *.npz`.

**NOW (Oct 15): the wall-grid rebuild, [tasks/wall-grid-plan.md](../tasks/wall-grid-plan.md).** Build the house like a house: one shared grid of wall lines across both floors, walls as objects shared by the rooms on both sides, one floor plate and ceiling per storey, openings cut into walls, all generated and verified in Python before Unity. The uncommitted corner-post/threshold stopgaps in SpecGreybox.cs are removed by it. Its verification plan (V1-V6) is the bar for every phase.

## User decisions (binding)

- **Exterior = the film's house; upstairs drawn only from inside** (user, Oct 15: "the outside needs to look the same as the movie"). Marina's upstairs set is 11.3 m deep and cannot fit the real 8.75 m house; her ground floor does. Ground floor and exterior share one space; the upstairs keeps Marina's rooms and is rendered only when the player is upstairs/on the stair (DEVIATIONS 1). Next: measure the exterior against film stills and fix the shell.

- **Faithfulness is non-negotiable.** Never propose "good enough" geometry.
- **Unity only.** Godot is retired.
- **Scale the players, not the house.** Kevin is about 1.1 m eye height and can crawl in about 0.4 m. The bandits are about 1.7 m eye height, with a hard adult-capsule rule (0.55 m diameter, 1.85 m tall).
- **Thin the interior walls to 14 cm.** Marina's are 25–45 cm. Keep each wall's centre line; rooms take the freed space. Exterior walls are unchanged.
  - Independent evidence backs this: the far-end hall passage measures 1.22 m, the overhead traced 1.07 m, and the thinned build gives 1.23 m.
- **Closets don't need to open.** The linen closet has a prop door; the other shallow closets are sealed.
- **Door height** is 80 in nominal, 78–80 in honest. The area check brackets Marina's 1,900 ft², and 84 in is ruled out.
- **Marina's model is the authority for both floors and how they stack** (user, Oct 13). The downloaded whole-house model (`HOME_ALONE_FINAL.glb`, IntactHouseReference, 0.774 m/unit from its doors) is a sanity check only. A uniform house or player scale for feel is allowed later as a build-time knob.
- **Agents never contact Marina.** The user wrote to her on Oct 14, 2026 (mockingbirdlanedesign@gmail.com) asking for room dimensions or plans and where her furniture came from. If she replies, her numbers are a new source: log them with their provenance and use them as independent checks (Buzz door-to-desk length, DEVIATIONS 23, first).
- Commit and push work. The user likes plain-language summaries.

## Pipeline (all re-runnable)

```
Marina video (gated SfM clips) ┐
Marina's angled overhead ──────┼─ trace + calibration ─ reconciler ─ spec ─ Unity grey-box ─ checks
Muto set model, captions ──────┘
```

| Step | Command | Output |
|---|---|---|
| Calibrate the overhead | `uv run --with numpy --with scipy python tools/sfm/overhead_fit.py measurements/overhead/upstairs.json` | `upstairs.H.txt` (held-out 9 cm) |
| Trace to plan | `uv run --with numpy --with matplotlib --with pillow python tools/sfm/overhead_plan.py measurements/overhead/upstairs-trace.json` | `upstairs-trace.plan.json/.png` |
| Clip registrations and derived geometry | `uv run --with numpy --with scipy python tools/house/register_clip.py <clip> [--loo [--rigid]]` | writes doors, trace `"m"` polygons, checkpoints |
| Reconcile | `uv run --with numpy python tools/house/reconcile.py [--measured]` | `spec/house_spec[.measured].json`, `spec/upstairs-changes*.md` |
| Grey-box | `Unity -batchmode -projectPath unity/HomeAlone -executeMethod SpecGreybox.Build -quit -logFile - [-variant measured]` | `Greybox_Upstairs[_measured].unity`, walk test |
| Verify | see `.claude/skills/verify-plan/SKILL.md` | `verify_plan.py`, `check_walls.py`, `test_checks.py`, matched renders |

Unity binary: `/Applications/Unity/Hub/Editor/6000.6.0f1/Unity.app/Contents/MacOS/Unity`. Python: `uv run --with ...`. VGGT and PyTorch live in `sfm-work/.venv`. COLMAP is Homebrew 4.2.1, CPU only.

Key files:

- **Spec (the only thing Unity reads):** `spec/house_spec.json`
- **Inputs:** `measurements/overhead/upstairs{.json,-trace.json,-doors.json}`, `measurements/rooms/*.json`, `measurements/checkpoints/upstairs.json`. The checkpoints file holds the clip registrations and all checkpoints.
- **Builder:** `unity/HomeAlone/Assets/Editor/SpecGreybox.cs`
- **Gated clips:** `sfm-work/rooms/{hall-s1, hall-s4, parents, kevin}`. `sfm-work/` is gitignored and regenerable with `tools/sfm/room.py`.

## Where the upstairs stands

- **Spaces:** 15 (6 rooms, hall with end bay, 3 hall pieces, closets, hall bath, main stair opening, attic stair). Gross footprint 1,972 ft² at 80 in (1,874 at 78 in) against Marina's 1,900.
- **Ceilings:** measured 2.29–2.50 m; 2.40 m nominal.
- **Checks:**
  - `verify_plan.py`: 15/15 pass, **6 independent**: Marina's 7′6″ label, the parents' bath width, the overhead's open door leaf, and three from the far-end clip.
  - `check_walls.py`: every long wall seen by hall-s1, parents and Kevin is within ±7 cm. These are consistency checks, because those registrations were fitted on those walls.
  - Leave-one-out (rigid): hall median 5 cm, max 10.5 cm; Kevin median 3.5 cm, max 6 cm.
  - The far-end clip, which never built anything, confirms Kevin's and the parents' hall doors within 7 cm.
  - Adult walk test: 11/11 in both builds.
- **Proven detection limits:** wall check 10 cm; door centres 10 cm; walk test blocks doors under 0.55 m. The image edge score **cannot** detect 20 cm and is visual-only.

## Feel notes (walk-and-annotate, Unity key M; `tools/house/feel_notes.py`)

The user walks a scene and rates each spot's shape/size and lighting separately. First pass, old model (IntactHouseReference), Oct 13:
- Living room and dining room: shape right, lighting too dark. Old model 3.8 x 10.1 m and 3.8 x 7.4 m; Marina (new build) 4.5 x 8.4 m and 4.6 x 5.9 m. Same floor area (±3%), different proportions. **Next:** rate the same rooms in the new grey-box, to tell whether it's the area or the proportions that feels right.
- Buzz's room: shape off ("too small for a bed and dresser"). Old model ~3.8 x 3.2 m; Marina 4.35 x 3.49 m from Buzz's own door (new build 4.46 x 3.68). Marina's tour frame (references/buzz-bedroom/tour556.jpg) shows clear wall either side of the bed. The new build is the bigger, Marina-measured room.
  - **Census done (Oct 13, later), old model vs Marina:** `docs/DEVIATIONS.md` section "Old model: Buzz's room vs Marina" (O1-O7) and `spec/captures/buzz-old-vs-marina/all.png` (her frame beside the old scene rendered from her own camera: `SpecGreybox.RenderViews -scene IntactHouseReference -views views-buzz-old.json`). Same layout, turned 90 deg; the old room is 0.53 m too short door-to-desk (her 556-562 s camera stands beyond the old west wall) and 0.24-0.39 m too narrow, while the hall band beside it is 0.5 m too wide. Chest resized to Marina's (applied). **Wall move is a user decision:** north wall +0.30 m into the hall is interior-only and recommended; the west wall carries an exterior window.
- **Room comparison from Marina's own cameras (Oct 14):** `spec/captures/sheet-matched/<still>-triple.jpg` (Marina | September | grey-box) for 31 review stills, poses in `poses.json` (distances from named walls, eye height, lens, reprojection error, per-still findings). Tool: `tools/house/still_pose.py` (VGGT solve per room with the exact still, PnP, Manhattan wall fit, pinned at the nearest corner in each model). Replaces the generic doorway/far-corner sheet. Unreliable: the two foyer stills (poor solve); kitchen +-1 m.
- **September census (Oct 14):** `tools/house/sept_census.py` (`--selftest`) measures every room of the September model (GLB section above door heads, flood fill, closures listed in the script; map `spec/captures/sept-census.png`) against Marina's traced overhead at ±5% per side. 1 of 15 rooms passes (den). Fails: living −12/+20%, dining −13/+30%, foyer +22% wide, sunroom −9% deep, kitchen +7/−4% (turned), Buzz −11/−11%, girls B −14/−10%, Kevin −9/−17% (turned), hall bath +28/−46%, parents' bedroom −12/+19%, parents' bath −18/−8%. Missing: rear girls' room (back-stair hall in its place), back stair as a room. Extra: an upstairs room over the den that Marina's plan doesn't have. Agrees within 7 cm with the earlier Unity raycasts (living, dining, Buzz). The grey-box is within ±5% of the same trace by construction, so its real accuracy rests on its independent checks.
- Ground-floor lighting is far too dark in the old model (all three ground notes). That's for the art/lighting pass; the grey-box only carries layout.

## Open items

1. **Foyer length (Oct 15, TRIAL, user walk pending):** Marina's foyer is ~24 ft, not 29. The overhead trace took its rear edge from a two-storey wall's top; at floor level it is flush with the living room's (`tools/house/foyer_length.py`, single-frame metrology at 203 s and 312 s, rise-scaled). Stair foot now 2.43 m from the front wall (was 4.48), going 0.295 m (pitch 31 deg; conflicts with the 35 deg VP read, DEVIATIONS 6), landing 1.40 m; upstairs well and stair head follow. Closed `back_hall` behind the arched door (DEVIATIONS 22). Sheet `spec/captures/foyer-length/compare.jpg`; record `changes/2026-10-15-foyer-length.json`. Next: dress the foyer (white stair side, spindles, newel, soffit, doors, wainscot, furniture) against the same matched cameras.
1. **The ground floor: first build done (Oct 13).** Calibrated with the `overhead-floor` skill, stacked under the upstairs by `tools/house/stack_floor.py` (no stretch, user decision: rooms keep Marina's shapes, the upstairs overhangs the front by ~1.6 m), reconciled with `reconcile.py --floor ground`, built at -2.535 m. Tests: ground doors 7/7, stair 20/20. `verify_plan.py --floor ground`: 4/4 (2 independent: stair width -0.4%, den width +1.7%; both FAIL on an injected 6% scale error). Den/living doorway placed from the den clip's wall gap. Stairs use the adult-body rule, not the 0.90 m hall minimum. Side effect of the stretch: gross 2,988 ft2 vs Marina's 2,620, kitchen 590 vs 477 (the stretch also pushed the rear kitchen wing back). Open: sunroom in/out of 2,620; second dining door; foyer width 3.76 traced vs 3.49 from clip A (lateral). Was: Same method; Marina Part 1 (the 1080p `copy.mp4`) is the main-floor tour. The stair's foot and foyer are only a floor patch so far.
2. **Hall feels narrow in play (user, Oct 13).** Built widths match the measurements: 1.59 m at the stair top vs 1.58 measured, 1.25 m at the far end vs 1.22 measured. Before changing anything, check against a film shot of the hall: matched camera, then overlay. Possible causes: the play FOV/eye height, no trim or furniture, or Marina's model being narrower than the set. Scale work is deferred by the user.
3. The attic leg looks about 10 cm wider in hall-s1 than in the overhead (leave-one-out); unresolved.
4. Buzz's room, the girls' rooms and the hall bath have only consistency or overhead evidence. Buzz's own clip calibrated the overhead, and the girls' rooms have no interior video.
5. Kevin's crawl test and hideable furniture (bed clearances) are not started.
6. The attic stair is located (behind the hall-end door, matching the film shot) but has no steps modelled.

## The main staircase (done): evidence, method and plan as run

**Done (Oct 13, later): the main stair is measured, decided and built.** Record: `measurements/rooms/stairs.json`.
- Measured (flight 1): 13 risers of 0.169 m, going 0.241 m (pitch 35.0 deg by vanishing points), tread band 1.12 m; landing at 2.20 m.
- Decided by the user: floor-to-floor 15 risers (2.54 m). Flight 2 is 2 risers at the north end of a full-width rear landing, rising toward the front onto a 1.2 m gallery along the north side of the well, which runs to the hall.
  - Evidence: Marina's main-floor overhead, a main-floor plan drawing the user found (not yet in the repo), the film's landing walk (Kate and Kevin), and the climb clip.
- Built: `stair` block in the spec (reconciler), boxes plus walk path in `SpecGreybox`. The stair walk test (adult and Kevin, up and down) gives 20/20 legs; removing one step blocks it.
- Not modelled: the landing window, the newels, and the landing's true ~4 m width. Marina's main floor is wider than the upstairs well; settle that when the ground floor is built.

**Evidence on hand:**

- **Overhead.** `main_stair_opening` is black (open to below) at plan x 7.83–10.66, y −4.71…0.94 (about 2.8 × 5.6 m). Its west (left) edge is hidden against the background and assumed straight at the building edge.
- **Hall walk.** A balustrade runs along the hall's west side (hall-s1 frames 135–160; rail sits on the stairwell edge, hall reaches it, rule `RAIL_T`). From the landing gallery, frames 255–300 show the damask stair wall and the rail turning (`real-colmap/images/shot_hall`). The hall-s1 middle clip (195–330) failed its gate, so don't measure from it.
- **Part 1 (main floor tour).** Stair footage at 305–360 s is already extracted in `sfm-work/stairs/images` (4 fps, 220 frames). Kept frames are 31–74 and 116–199; the others are film, dissolves, arrow overlays and the title.
- **Neither video climbs continuously between floors.** Part 1 stops at the landing, and Part 2 starts upstairs.
- **Muto says the upstairs was a separate set**, and the service (back) stair never arrived upstairs. So floor stacking is partly an authored decision; log it as one. A cross-video link from Part 1 to Part 2 FAILED: repeating damask wallpaper glued two different walls together. **Never link the two videos.** Each floor is solved on its own, and the stair is measured within itself.
- **Muto's set model** shows a damask-papered stairwell. **The poster** (`art/home_alone/references/poster/second-floor-closeup.jpg`) shows the stair with a landing turn (21), and the hall walk agrees with it.
- **The old Unity model** (`dimensional-baseline/README.md`): 16 rises of about 0.196 m, going about 0.261 m, a landing. That model is unverified; use it as a hypothesis only.

**Plan (same method as the upstairs, gates first):**

1. **Find stair-only clips** in Part 1 (305–360 s) and in Part 2's hall frames that look down the stair. Solve each with `tools/sfm/room.py`, and keep only clips that pass the COLMAP/VGGT agreement gate. Trim captions and dissolves.
2. **Measure the stair within itself.** Scale from a door, or from the riser count once the scale is checked. Measure the riser count, rise and going per flight; the width; the landing size and position; the turn direction; and the rail line. Treat a riser count from frames as a checkpoint: counted by eye, then confirmed in 3D.
3. **Floor-to-floor height** comes from rises × rise. It's independent of any cross-video link, and sets how the floors stack.
4. **Register the stair to the upstairs** using the rail edge and the stair-opening walls seen in hall-s1, rigidly. Settle the hidden west edge of `main_stair_opening`.
5. **Extend the spec.** Add a `stair` element (flights, risers, landing, rails) to the reconciler. Have `SpecGreybox` build the steps. Walk tests go up and down for both bodies.
6. **Checkpoints.** Mark independent vs consistency, prove sensitivity (for example, inject a missing riser), and run the `verify-plan` skill.

**Lessons that apply here:**

- Plot every clip from above with its camera path before interpreting gaps.
- Wallpaper repeats; don't trust any link across videos.
- Register rigidly when both sides are metric.
- Prove every new check can fail.
- Furniture and trim read as walls.
- Rails are not walls.
