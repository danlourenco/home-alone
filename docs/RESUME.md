# RESUME HERE (Oct 19 2026): state, queue, job briefs, neighbourhood plan

The one hand-off doc for Claude or Codex (CLAUDE-HANDOFF.md was folded in here Oct 19). Read AGENTS.md first (its rules and the
Skills index apply to every job), then this, then docs/WALK-FEEDBACK-2026-10-19.md (the latest walk's defects + shots) and
docs/FOYER-WIP.md (the foyer job's checkpoints); STATUS.md is the long log. This file supersedes older pending/accepted wording there.

## 0. State

> **Nutcracker replacement ACCEPTED:** all six living-room figures replaced LIVE with the user's red/green downloaded models (35.5cm, original base locations; one inherited float corrected15mm). Private assets in `Assets/Purchased/Nutcrackers`, source placement in `spec/dressing/store_props.json`; generator now separates fallback figures from shared train/decor meshes.0 prop/z-fight/clash problems; existing baked scratch scene updated in place, no new full build/bake. Main still walking: live preview is lost on Stop; load the checked scratch scene when ready, or Refresh Props in stopped editor then save. Details/comparisons: `spec/captures/views/living/nutcrackers/`. User accepted the live walk: “ok i accept, it's good”.

> **Stair/soffit ACCEPTED, Oct19:** user loaded the baked3a0e0afe trial and said "it looks great. approved." Night/day load checks all passed.90/90 baluster feet supported,5 aligned edge planes,0 z-fights/clashes and no new blocked routes. Comparison: `spec/captures/views/foyer/stair-support/compare-note1623.jpg`. Stair support/soffit defect closed; preserve this version. Hall-runner work remains paused; other defects remain open.

- Branch `unity-sfm-reconstruction`, pushed through the Codex session's work (3773db20). Trials since Oct 18 are in `changes/`.
- **Oct 19 walk verdict:** accepted: mirror, front door look + use, den arrangement, TV seat/view concept, the exterior/sky/drive
  trials except listed defects. **Flight-2 soffit/open-side support correction now ACCEPTED** after the latest loaded walk. Other reported defects remain open.
- **Open defects** (details, shots and proposed fixes: docs/WALK-FEEDBACK-2026-10-19.md): soffit/support CLOSED by user approval
  (changes/2026-10-19-soffit-joints.json); exterior wallpaper on a
  jamb; jerky door swing (profile it first: the timing sample had zero moving-door frames, cause NOT proven); stoop/step overlap; noisy
  porch shadows; coarse/dry walk material; a protruding gutter/trim candidate; magenta breakfast hutch + a reference-correct built-in;
  flat interior doors; street-lamp style; a tree in the driveway; garage fence placement; den shelf lamp too broad/bright. Older notes:
  the STATUS checklist. Don't guess hutch geometry or neighbour facades.
- **Not yet implemented:** a general automated door validator. (Done Oct 19: `tools/house/soffit_joints.py` in preflight; the
  rejected soffit fails it, the fix passes.) Door work follows `.claude/skills/door-assembly/SKILL.md`.
- **Fall prevention:** the visible GroundSkirt/OffLot lacked colliders (the void); exact mesh colliders + last-supported recovery
  added. Re-run `python3 tools/house/check_fall_recovery.py` with Play STOPPED. Not a whole-map coverage claim; the user's retrial
  of the void area is pending.

### Live settings (TV FOV, TV target and music PERSISTED Oct 19, 55eca097 + the saved scene; the lamp comparison is still live-only)
| Item | Live | To persist |
|---|---|---|
| TV seat FOV | 24 deg | apply `changes/2026-10-19-tv-tight24.patch` (the 42->36 patch is already applied; don't re-apply), set the saved seat component to 24, save |
| Music | volume 0.20 | `BackgroundMusic.Awake` default 0.35 -> 0.20 (contextual ducking discussed, not built) |
| TV render target | 720x540 RenderTexture saved | apply `changes/2026-10-19-tv-aspect.patch` (the builder still expects 768x540) |
| TV clip | edited 4:3 clip, 344x258, ~79.9 s | in gitignored StreamingAssets/LocalMedia; original sfm-work/media/tv.original.mp4, edit sfm-work/media/tv-edit.json; regenerate with tools/house/prepare_tv_clip.py |
| Lamp comparison | bookcase/TV-side, tray/chair and legacy floor lamps OFF, banker/desk ON (user: "for now") | NOT a lighting decision; baked bounce still has the old lamps; N restores lamps. Ask before making it the default |

### Editor and tree safety
- Recheck Play before anything; never stop Play, reload or force a recompile while the user walks. Unity CLI flags:
  `--caller plugin --skill unity-cli --project-path /Users/dlo/Dev/home-alone/unity/HomeAlone`.
- The main project's saved scene is NEWER than the scratch builds (fall colliders, the inactive wrong across-street house
  `WinterBackdrop_NightHouse`, builder fixed). Never `load` an old scratch scene over it; build from current sources.
- Not committed on purpose: Settings/*.asset other than HDRP.asset (build-generated), Packages/manifest + ProjectSettings (Unity AI
  assistant/inference packages and a SENTIS define appeared: the user's or Unity's, not ours to commit), feel-notes.jsonl and
  feedback shots, 0-homealone/ (film frames, gitignored).
- Live evals: read-only except the one thing previewed; static (batched) pieces need hide-original + preview-copy; confirm with
  `unity_pipeline.sh shot|cam`. Keep >= 15 GB free.
- Commits: normal commits run the change gate; props/decorations use `git commit --no-verify` with "prop"/"decoration" (the Claude
  classifier blocks the flag, so the user runs it). Standing rules: agents never contact Marina Coates; never move outside walls
  without asking; never kill the user's Unity editor.

## 1. Queue (one building job at a time)
0. **The user's must-have house pass, then call the environment (user, Oct 19)**: "refine the house just a little bit more" to pick a
   direction (stealth vs Rainbow Six Siege-like), then stop polishing and start core game development (a GDD with pillars, then a
   vertical slice; GitHub issues as the backlog once the pillars are signed off). Must-haves named so far: **the upstairs hall
   bathroom** (missing), **the kitchen finished** (it "still feels unfinished": ask what reads unfinished), **walk out the kitchen
   back door to the exterior**. Confirm the full list with the user before starting; everything else waits for the slice.
   - **Kitchen part (Oct 19, TRIAL, built + baked + loaded; changes/2026-10-19-kitchen-fidelity.json, DEVIATIONS 106):** pot rack + 14 pans,
     four pine stools, counter dressing (kettle, knife block, spaghetti, canisters, coffee maker, microwave, toaster, fruit, mortar, towels),
     pine stacked corner cupboard, black wall oven, fridge dispenser + papers, six snapshots + calendar + memo board (all
     tools/house/hifi_kitchen_props.py / hifi_kitchen.py / hifi_kitchen_gallery.py from spec/dressing/kitchen.json "wares"). The back door
     opens (E; `locked` for gameplay; SpecGreybox.BackDoor.cs): BACK DOOR route bandit/kevin/player out and in 0 blocked, Back door check
     passes (closed/open/swept 25-100 deg/locked). Gates: z-fight 0, clash 0. Pending: the user's walk; `python3 tools/house/check_fall_recovery.py`
     with Play stopped; duck decoy, the film's pine pigeonhole desk, a wall phone (no film frame found).
   - **Bathrooms (Oct 19, TRIAL 1, built + baked, NOT loaded; changes/2026-10-19-bathrooms.json + -hall-bath-tile.json, DEVIATIONS 110):** both were empty grey-box shells (doors + windows only). Parents' ensuite from film 4386-4438/6402-6474 + the set photo (Marina 160-169 s): dark-green marble vanity, undermount sink, brass taps, ivory drawers, knee space (Kevin hides there), gilt mirror with a planar reflection, bracket shelves, curved-front tub, black-framed quadrant shower (also a hiding spot), 4-globe light bar, prints over layered green towels, toilet, lace dressing, blush paint, green carpet, the aftershave/Shower to Shower/Aquafresh clutter (movable). Hall bath from film 332-344: subway-tile wainscot with black liner + cap (heights on Marina 468.5's door ruler), the film's tureen paper (drawn), alcove tub + green curtain (hide behind it), toilet, pedestal sink, medicine cabinet + frosted globe, towel bar, wicker shelf + hamper, grass plant, hex floor. tools/house/hifi_bathrooms.py, bathroom_textures.py, spec/dressing/bathrooms.json, SpecGreybox.Bathrooms.cs. Renders: spec/captures/views/bathrooms/. Follow-ups: the wall flower spray and the Windsor chair (film 4398), a film ruler for the vanity height, artist-pipeline maps on the vanity/mirror if they read flat.
   - **Bathroom assets (Oct 20, NOTED, nothing bought):** research report in the session scratch (copy in the bathrooms follow-up when acted on). Free picks need the user's Sketchfab login: Memoirs pedestal sink (CC-BY-SA), CWI Davinci frosted-globe sconce, Windsor armchair, brass towel rack, tissue box; Poly Haven (CC0, fetchable): wicker baskets, grass + pot, ornate mirror. Store toilet DONE (faa53de1). Rejected: Unity "Victorian Bathroom Props" $24.99 (clawfoot tub, high-tank toilet: wrong era). Paid search (Oct 20): no ready match for either. Faucet: maybe CGHawk combo $19.99 (renderhub.com/cghawk/bathroom-faucet-3d-model-combo; brass/widespread unverified) else generate from Kingston Brass 8 in widespread dims. Bean-front whirlpool: none sold; generate in Blender from a Kohler oval/Sunward 72 in drawing (corner fallback: CGTrader "bathtub 01" $8.90). Make ourselves: brass taps if no buy, terry-cloth towels/bath mat.
   - **Cupboard + hutch sizing (Oct 19, TRIAL, built + baked, NOT loaded; changes/2026-10-19-kitchen-cupboard-hutch.json, DEVIATIONS 109):** sized from IMG_4305 = film 2104 with a solved film camera (tools/house/film2104_measure.py: tile-grid ruler, sconce-height check 1.68 vs Marina 1.66). The corner pantry is now the film's freestanding pine stack (0.33 x 0.30 x 1.85, turned 45 deg, one door per section); the seat counter runs on to 0.30 m short of the gallery wall and seat_U2 to x 1.75; the hutch is generated (3 bays, 1.83 wide, flat top 2.33, glazed 3x4-pane doors, open band with red canisters, cubbies, drawers + doors) and the kitchen_hutch store prop is gone. Sheets: spec/captures/views/kitchen/sizing/. Load: `HA_SCRATCH=$HOME/.cache/home-alone-2 tools/house/unity_pipeline.sh load` (Play stopped). Follow-ups: goose decoy (no free model found; purchase note), the film's pine pigeonhole desk, a poinsettia on the counter end; the stack's side 0.25-0.33 in the film (built 0.30) if it reads thin.
1. (done 55eca097) persist the live settings; the lamp comparison still needs the user's decision.
2. **Mac test app** (user-authorized; iOS out of scope). **BUILT Oct 20** (steps 1-5 done; baseline in docs/PERFORMANCE.md):
   `~/.cache/home-alone-perf/build/HomeAlone.app`, local only. Automated tour checks passed (loads, no magenta, no player errors);
   the interactive keys in step 6 (WASD..K lot view, M note) are still for the user to try. Original steps:
   1. Fix standalone feedback storage: `FeelNotes.Dir` writes repo-relative `../../../spec/feedback`; keep that in the Editor, use
      `Path.Combine(Application.persistentDataPath, "feedback")` in the player (check startup + M screenshot outside the repo).
      Review PerfProbe/FlickerProbe output paths only where the app exercises them.
   2. Reuse `Assets/Editor/PerfBuild.cs` (House_WallGrid, IL2CPP, StandaloneOSX, frame timing; keep IL2CPP). `tools/house/perf_probe.sh
      build` shows the copy-on-write throwaway project and removes the bought pack's misplaced editor-only
      `Assets/BankersLamp/Scripts/RenderTextureCaptureEditor.cs` from that copy; reuse that or guard the script properly.
   3. perf_probe.sh defaults to the stale scratch (`$HA_SCRATCH/ucopy/HomeAlone`): point it at the CURRENT main project via its clone
      recipe; no Temp/lock state in the clone; keep old benchmark outputs; one builder at a time.
   4. EditorBuildSettings lists only the old House.unity: switch to House_WallGrid. Pick a stable local bundle id (player settings
      are still DefaultCompany/HomeAlone, no id); windowed Apple Silicon build with the installed Mac support
      (`/Applications/Unity/Hub/Editor/6000.6.0f1/PlaybackEngines/MacStandaloneSupport`; Xcode installed; host arm64).
   5. Include the saved lighting/APV/reflections, the 4K door assets and the StreamingAssets media. No new bake for packaging alone.
   6. Build, launch the real .app, read the player log. Smoke test: WASD/mouse/Esc, kid/adult (G), door E, seat/stand E, V video
      with audio and 4:3 fill, J/-/= music, N day/night, O weather, K lot view, M screenshot into app data, the repaired ground +
      recovery; look for magenta materials and frame pacing (`-perfprobe DIR` runs the automated tour). Report known art defects
      honestly; don't block the prototype on unrelated art.
3. **Defect fixes** from section 0 (soffit first, with its regression check).
4. **Texture job**: garage's 13 GLB parts (256-1024 px) -> the house's brick/roof PBR + painted wood doors; front terrace/walk strips
   (Site object27, object2923) -> stone/paver; basement metal (HiFi_GalvDuct, BS_Iron, BS_DoorPaint) -> Poly Haven galvanized/rusty
   metal (`tools/house/exterior_textures.py`, plain User-Agent, CREDITS).
5. **Breakfast-area measurement (no geometry change)**: the kitchen wing reads 5-9% longer in Marina's rulers than built (DEVIATIONS
   46). Measure from the user's stills (~/Downloads/IMG_4305.JPG, IMG_4306.JPG) with `tools/house/wall_measure.py`; compare with
   Marina and the plan; show an overlay before moving anything.
6. **Small follow-ups**: 65 MB of PNG renders in d1cf0ebe -> JPG; film 2850's glass table could return BESIDE the den chair (den.json
   "removed"); the white picket fence (film 11294-11300) once its place is known; the always-failing daycheck "buzz floor R/B"
   (cause not reproduced) makes every load exit 1.
7. **Duplicate Unity project names** ("Home Alone" and "Home Alone (1)"): the user asked why; where they appear (Hub, Dashboard,
   editor) is unanswered. Only one HomeAlone editor is connected; the Hub's local list doesn't show these names; cloudProjectId/name
   are blank. Identify IDs/paths before renaming or removing anything.
8. **Cruft to remove (Oct 20; the auto-mode classifier blocks agent deletes, so the USER runs it).** Checked: nothing references
   these. `Assets/VR-ready PBR toilet/` (611 MB raw store package; the house uses the converted `Assets/Purchased/Toilet`, made by
   tools/house/purchased_toilet.py from the Asset Store cache; NOT gitignored, so never `git add` it), the 23 MB
   `Scenes/House_WallGrid_unsaved_backup_20261019.unity` (Oct 19 freeze), `Assets/Resources/PerformanceTest*` (auto-made), the
   orphan `Models/PolyHaven/Kitchen/kettle_red_*` materials, the unreferenced Oct 18 `spec/captures/views/o67-*.png`. Command:
   `cd ~/Dev/home-alone && A=unity/HomeAlone/Assets && T=~/.Trash/home-alone-cruft && mkdir -p $T && mv "$A/VR-ready PBR toilet" "$A/VR-ready PBR toilet.meta" $A/Scenes/House_WallGrid_unsaved_backup_20261019.unity* $A/Resources $A/Resources.meta $A/Models/PolyHaven/Kitchen/kettle_red_* spec/captures/views/o67-*.png spec/captures/props-front.png $T/`
   Never commit: the ~34 re-import-churned .mat files (property reorders), spec/feedback/ shots, ProjectSettings AI-assistant
   settings. Rule: a store package goes to Assets/Purchased/ (gitignored), never unpacked at the Assets root.
9. **Obsolete-API migration (Oct 20, deterministic: a codemod, not an agent):** 63 CS0618 sites in Editor/Scripts
   (unity_practices.py baseline): `FindObjectsByType<T>(FindObjectsSortMode.None)` -> `FindObjectsByType<T>()`, the
   `(FindObjectsInactive.X, FindObjectsSortMode.None)` overload -> `(FindObjectsInactive.X)`, `FindFirstObjectByType` ->
   `FindAnyObjectByType` (check the one `FindObjectsSortMode.InstanceID` caller needs no order), ShadowAudit's `spotLightShape` ->
   `Light.type`. Only while the user is NOT in Play; csc_check.sh, then `unity_practices.py --update-baseline` to lock it in.

## 2. Neighbourhood plan (user, Oct 19: "recreate the scene systematically ... period-accurate ... the Murphys across the street")
Tiers by player distance; detail follows sightlines (window views, the film's exterior cameras, the bandits' routes):

| Tier | What | Detail |
|---|---|---|
| 0 House | done | full gate |
| 1 Lot | piers, U-drive, garage, treehouse, beds, walks, planting | hero assets, real trees/shrubs |
| 2 Frontage | Lincoln Ave, sidewalks, parkway trees, lamp posts, Marley's next door, the Murphys across, the neighbours either side | walkable, film-matched facades |
| 3 Block | surrounding streets | footprint + height + roofline, simple facades, low-detail stand-ins, not reachable |
| 4 Horizon | treeline, sky | backdrop |

- **Evidence ladder** (film first): (1) the film, 1990: index every exterior shot by which neighbour it shows; (2) footprints/heights:
  OSM (`art/home_alone/references/site/osm-671-lincoln.json`), Cook County parcel + building-footprint GIS (also our true lot line,
  replacing PropertyView's approximate box), Illinois statewide LiDAR (roof heights, real tree positions/heights); (3) current
  street photos only as a fallback, user-supplied, drop post-1990 changes; (4) guesses built from a **period style kit** (1910s-30s
  North Shore Georgian/Colonial Revival, Tudor, shingle: brick/clapboard sets, hip/gable roofs, shutters, 6-over-6 sashes,
  porticos, dormers), each guess logged with its confidence.
- **One manifest**: `spec/neighborhood.json`, one entry per parcel (tier, footprint source, height source, style kit pieces,
  evidence frames, confidence, status); a generator builds the neighbourhood from it, like the house from its spec.
- **Privacy**: model the 1990 film appearance and massing only; no current residents' names or house numbers in the repo.
- **Order**: (1) evidence pass, no builds: parcel/footprint/LiDAR data, film shot index per neighbour, a reference board per parcel
  (Murphys first), manifest draft + a plan map for the user to mark up; (2) Tier 1 upgrade (lock the hero structures, texture job,
  real shrubs/topiary, varied trees at LiDAR positions: the Sereib oak trial was rejected as "too thick and similar"); (3) Tier 2;
  (4) Tier 3 + 4; (5) performance pass (low-detail versions, occlusion; measure standalone with the display awake).
- **Decided (user, Oct 19)**: Tier 2 is walkable: cross Lincoln Ave and go "one house over" left and right (the McCallister lot, the
  neighbour on each side, the Murphys across the street and the house on each side of theirs). "The main action happens in the
  McCallister property." Tier 3 extent is ours to choose for performance without losing feel: the street faces visible from the
  lot and the Tier 2 sidewalks (both sides of Lincoln, ~150 m each way) as low-detail stand-ins, everything further is the
  Tier 4 horizon. **Revisit if it ever feels off** (too empty at the street ends, or a frame-time cost).
- **Step 1 started Oct 19** (evidence pass, no builds): outputs in `art/home_alone/references/neighborhood/` and `spec/neighborhood.json`.

## 3. Step 1 results (43875efb; tools/house/nb_*.py regenerate)
- Data in `art/home_alone/references/neighborhood/data/` (Cook County parcels + 2022 lidar building footprints with heights, OSM,
  ISGS 2022 nDSM: 2516 trees > 6 m, post-1990 canopy). Manifest `spec/neighborhood.json` (18 parcels), `film_index.json`, `boards/`, `plan.png`.
- True McCallister lot (spec x,z): (-30.16,30.58) (27.38,30.72) (27.36,19.17) (27.30,-3.91) (-34.16,-4.06): front line x ~27.35.
  **Decided (user, Oct 19)**: the lot's front is the public sidewalk's back edge (x 28.87), the parcel's sides/rear kept:
  (-30.16,30.58) (28.87,30.72) (28.87,-3.91) (-34.16,-4.06), now in PropertyView.cs (K, and ExteriorRealism's on/off-lot ground
  split). Why: the walk piers (x 28.30-28.80) sit there in film 11908/12030/12066 (a truck at the kerb beside the right pier), and
  the 2015 Commons photo shows the owner's fence on that line right behind the sidewalk (the piers themselves are gone by 2015);
  the parcel's own front plots ~1.5 m further back (registration, or a right-of-way strip in use by the owner).
- Tier 2: lot_B0 = the Murphys (grey-blue clapboard Foursquare, 2.5 storeys, hip dormer, full-width white-column porch; film
  11551-11636 night), lot_A+1 / lot_A-1 neighbours (edge views only), lot_B+1 / lot_B-1 (no clean frame: style kit). The county
  height for our own house (9.2 m) is wrong: never use it for the house.
- Step 2 (Oct 20, PREP, no Unity build): see section 4.

## 4. Step 2 results (Oct 20; art/home_alone/references/neighborhood/README.md "Step 2")
- Sheets (Preview): neighborhood/plan.png, plan_tier2.png, murphys_film11581_compare.jpg, murphys_film11581_closeup.jpg, tier2_contact.jpg.
- Lidar fix: step 1's nDSM was ~45 m off (requested vs returned extent); re-fetched, trees and roof profiles redone.
- Kit: nb_textures.py, nb_kits.py (kits + tiers + budgets in the manifest), nb_house.py (LOD0 hero ~10-36k tris, LOD1 stand-in 4-5 %), nb_street.py,
  nb_film_camera.py, nb_render.py, nb_compare.py. GLBs in Assets/Models/Neighborhood (5 Tier 2 + 10 Tier 3, Street, LampPost).
- **Ready for ONE Unity build** (when the pipeline is free): `HA_NEIGHBORHOOD=1` + the normal build; SpecGreybox.Neighborhood.cs (csc_check clean) places it,
  swaps the lamp posts (walk note 12:33), hides the WinterNeighborhood inside the extent. Then: z-fight/clash 0, the walk test (street and the
  new sidewalks), K, N; render 11581's camera live beside the film; the user walks across Lincoln.
- Open: Tier 3 extension + Tier 4 treeline + the dome (manifest "tiers"), the Mac baseline into "budgets.baseline_ms", the user's decisions (hand-back).

## 5. Step 3 results (Oct 20-21; art/home_alone/references/neighborhood/README.md "Step 3"; DEVIATIONS 125)
- **User direction (Oct 20):** walkable heroes = our lot, **Marley's (lot_A+1, the left neighbour from the street)** (SETTLED by the user Oct 20 and confirmed Oct 21 from the reunion 12490-12538 + film 1888: the pink turret house; no a/b/c, the right-side Tudor in nb-tudor-pending is discarded) and **the Murphys'
  (lot_B0)**; everything else is a realistic, unreachable backdrop behind a walk boundary. Vehicles: realistic models are being sourced by a
  separate agent; the proxies swap via `Assets/Purchased/Vehicles/<kind>.prefab`.
- Built and gated in scratch (`HA_NEIGHBORHOOD=1`, ~/.cache/home-alone-2, build 7, UNBAKED): z-fight 0, clash 0, Opening clear 0, walk
  boundary 33/33 legs blocked, walk routes LINCOLN / OUR SIDEWALK / B SIDEWALK / MARLEY 0 blocked. App from build 3 (before Marley and the
  boundary): ~/.cache/home-alone-perf/build/HomeAloneNB.app. The one-line `Neighborhood(ext, gy)` call in SpecGreybox.cs, the 4 walk
  routes and PerfProbe's piers/murphys/upwindow poses + `nbold` variant are patches in ~/.cache/home-alone-2/nb-patches (SpecGreybox.cs and
  PerfProbe.cs were open in another agent's working copy): merge them before the combined build.
- Next: one combined build + bake + HomeAloneNB3.app; the old-vs-new tour (`perf_probe.sh run` with `-perfposes piers,murphys,upwindow,street
  -perfab -perfvariants nbold`); the user's walk; then the front-yard trees (PROPOSAL `yard_trees_proposal.png`: film 12030/11908/5545 put
  two big trunks RIGHT of the portico; needs a solved 12030 camera, and it meets the wet-walk job's drive at x 17.35); WetGround for the
  street once Scripts/WetGround.cs lands; kerb-cut end caps (a dark slit at the drive mouths in the renders).
