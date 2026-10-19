# RESUME HERE (Oct 19 2026): state, queue, job briefs, neighbourhood plan

The one hand-off doc for Claude or Codex (CLAUDE-HANDOFF.md was folded in here Oct 19). Read AGENTS.md first (its rules and the
Skills index apply to every job), then this, then docs/WALK-FEEDBACK-2026-10-19.md (the latest walk's defects + shots) and
docs/FOYER-WIP.md (the foyer job's checkpoints); STATUS.md is the long log. This file supersedes older pending/accepted wording there.

## 0. State
- Branch `unity-sfm-reconstruction`, pushed through the Codex session's work (3773db20). Trials since Oct 18 are in `changes/`.
- **Oct 19 walk verdict:** accepted: mirror, front door look + use, den arrangement, TV seat/view concept, the exterior/sky/drive
  trials except listed defects. **Rejected: the flight-2 soffit (does not connect).** Acceptance does not close defects.
- **Open defects** (details, shots and proposed fixes: docs/WALK-FEEDBACK-2026-10-19.md): disconnected soffit; exterior wallpaper on a
  jamb; jerky door swing (profile it first: the timing sample had zero moving-door frames, cause NOT proven); stoop/step overlap; noisy
  porch shadows; coarse/dry walk material; a protruding gutter/trim candidate; magenta breakfast hutch + a reference-correct built-in;
  flat interior doors; street-lamp style; a tree in the driveway; garage fence placement; den shelf lamp too broad/bright. Older notes:
  the STATUS checklist. Don't guess hutch geometry or neighbour facades.
- **Not yet implemented:** a general automated door validator; a real soffit-contact regression check (prove the rejected output
  fails it before accepting a fix). Door work follows `.claude/skills/door-assembly/SKILL.md`.
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
1. (done 55eca097) persist the live settings; the lamp comparison still needs the user's decision.
2. **Mac test app** (user-authorized; iOS out of scope; nothing built yet):
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
- Next (step 2+): style kit + generator from the manifest; the Murphys first.
