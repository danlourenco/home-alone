# RESUME HERE (Oct 19 2026): queue, job briefs, neighbourhood plan

Written for whoever continues (Claude or Codex) if a session runs out. Read AGENTS.md first: its rules (film first, change gate,
one builder at a time, live-only while the user walks, no email in requests, never push) apply to every job below.

## 0. State at hand-off
- Branch `unity-sfm-reconstruction`, nothing pushed. Recent trials, all awaiting the user's walk (records in `changes/`):
  sun + sky + O weather toggle (8751ff6a), front entrance door/lantern/wreath (45758c0a), U-drive + piers + garage fence (d1cf0ebe),
  breakfast room prop pass (eae31dd9), den chair angle / table removed / leather sheen (f7b832e5, c3e0f6c0), K = hide off-lot (PropertyView.cs).
- **Possibly still running**: an "exterior-mess-lamps" job (walk notes 09:03, 09:04: the sunny backdrop dome shows a cemetery and
  an office tower at eye level, floating snow-bank strips near the street, the piers on a grey slab; missing lamps by the basement
  door and the kitchen back door). Check `tools/house/pipeline_busy.sh`, `git log`, and `git status` for its half-done work before
  starting anything; if it left no commit, redo it from the brief in section 1.
- Walk notes: `spec/feedback/feel-notes.jsonl` (+ shots in `spec/feedback/shots/`). Open items: the checklist at the top of docs/STATUS.md.
- Pipeline: `HA_SCRATCH=$HOME/.cache/home-alone-2 tools/house/unity_pipeline.sh preflight|all|load` ; `tools/house/csc_check.sh`
  (10 s compile check) ; `python3 tools/house/build_models.py` (regenerate stale models) ; live editor:
  `$HOME/.unity/bin/unity command eval --code '...'` (times out after 5 s but keeps running: write results to a file).
- Commits: normal commits run the change gate. Props/decorations use `git commit --no-verify` with "prop"/"decoration" in the
  message (change-gate skill); the Claude auto-mode classifier blocks that flag, so the user runs it.

## 1. Queue (one building job at a time, in this order)
1. **Exterior mess + door lamps** (if not finished, see section 0). Sky: a CC0 clear-winter HDRI with a clean horizon (film 4382: blue
   sky, bare trees); find the floating strips (ExteriorRealism Mound / FrontDrive banks); ground the piers. Lamps: film 9936 (basement
   door) + the back-door scenes ~9900-10400; real glass fixtures, night-layer lights. JPG renders, not PNG.
2. **Foyer job** (STATUS checklist "QUEUED Oct 19"): (a) smooth sloped soffit under flight 2 of the main stair in `hifi_foyer.py`
   (the grey-box soffit renderer is off and re-enabling it did not hide the steps); (b) a better foyer mirror (sharp reflection,
   proper frame; film 2677, Marina 193.5); (c) the front door as a hinged leaf: split it from the frame in `hifi_door.py`
   (FrontDoor_HiFi "Paint" is leaf+frame+sidelights) and the outside face (`hifi_entrance.py`), E opens, a `locked` flag for
   gameplay, remove the doorway's two Wall colliders when open; (d) one inside wreath only (film 40); (e) **sit and watch**: E at the
   den movie chair seats the player (seated eye, FOV in on the TV playing DenTV's clip), E stands; (f) the daycheck "buzz floor R/B"
   check fails on every load: fix the cause or the threshold.
3. **Texture job**: the garage's 13 GLB parts (256-1024 px) -> the house's brick/roof PBR + painted wood doors; the front terrace/walk
   strips (Site object27, object2923) -> the stone/paver set; basement metal (HiFi_GalvDuct, BS_Iron, BS_DoorPaint) -> Poly Haven
   galvanized/rusty metal. Tool: `tools/house/exterior_textures.py` (Poly Haven fetch, plain User-Agent, CREDITS).
4. **Breakfast-area measurement (no geometry change)**: the kitchen wing reads 5-9% longer in Marina's rulers than built
   (DEVIATIONS 46). Measure the breakfast end from the user's film stills (~/Downloads/IMG_4305.JPG, IMG_4306.JPG: back-stair risers,
   80 in doors, the fridge, island tiles, chairs) with `tools/house/wall_measure.py`; compare with Marina and the plan; show the user
   an overlay and a list of candidate changes before moving anything.
5. **Small follow-ups**: the 65 MB of PNG renders committed in d1cf0ebe -> JPG in a new commit; the breakfast hutch should become a
   generated flat-topped built-in (fixture gate); film 2850's glass table can return BESIDE the den chair on Kevin's left
   (den.json "removed" says how); the white picket fence (film 11294-11300) once its place is known.

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
  PropertyView's box is badly off (should take this polygon). **Open**: the piers (x 28.30-28.80) fall 1-1.5 m outside the parcel:
  a ~1 m registration error, or they stand in the right-of-way. Decide before PropertyView uses the polygon.
- Tier 2: lot_B0 = the Murphys (grey-blue clapboard Foursquare, 2.5 storeys, hip dormer, full-width white-column porch; film
  11551-11636 night), lot_A+1 / lot_A-1 neighbours (edge views only), lot_B+1 / lot_B-1 (no clean frame: style kit). The county
  height for our own house (9.2 m) is wrong: never use it for the house.
- Next (step 2+): style kit + generator from the manifest; the Murphys first.
