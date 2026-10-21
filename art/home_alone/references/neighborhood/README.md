# Winnetka neighborhood — 2026-09-12

Reference-inspired winter backdrop, not a surveyed replica. Built by `SurveyBuilder.BuildWinterNeighborhood()` under `WinterNeighborhood` in IntactHouseReference. Fifteen simplified neighboring houses, street, sidewalks, verge trees, shrubs and utility wires. Nine shutter pairs fitted to existing main front windows; dormers unchanged. Original house mesh asset and interior unchanged.

Only detached outer snow banks object2946–object2955 have renderers and mesh colliders disabled. Objects/assets are retained. Other original site surfaces remain; snow texture/grade transitions still need refinement. Trees and neighboring architecture are visibly simplified and require higher-detail assets for the requested photoreal target.

Reference photos: Famartin, May 11 2015, Wikimedia Commons, CC BY-SA 4.0. Used for visual reference, not applied as textures.
- [House](https://commons.wikimedia.org/wiki/File:2015-05-11_06_38_29_View_of_the_%22Home_Alone%22_house_at_671_Lincoln_Avenue_in_Winnetka,_Illinois.jpg)
- [Street northwest](https://commons.wikimedia.org/wiki/File:2015-05-11_06_41_49_View_northwest_up_Lincoln_Avenue_from_in_front_of_the_%22Home_Alone%22_house_at_671_Lincoln_Avenue_in_Winnetka,_Illinois.jpg)
- [Street southeast](https://commons.wikimedia.org/wiki/File:2015-05-11_06_41_46_View_southeast_down_Lincoln_Avenue_from_in_front_of_the_%22Home_Alone%22_house_at_671_Lincoln_Avenue_in_Winnetka,_Illinois.jpg)

Validation: CheckWinterNeighborhood passes eight real-controller street/sidewalk/front-walk checkpoints; CheckIntactMainStairs passes spawn and eleven house checkpoints. Exterior route stops before existing entrance steps; it does not verify every yard or neighboring interior. Initial front-walk endpoint near the original step produced a height mismatch, so the endpoint was moved back to the level approach. Captures neighborhood-front.png and neighborhood-outward.png inspected. Daytime retained.

# Step 2 (Oct 20 2026): style kit, Tier 2 houses, the street (PREP, not built into Unity)
Open in Preview: `plan.png` (whole extent, by tier), `plan_tier2.png` (zoom), `murphys_film11581_compare.jpg` (film | render | overlay),
`murphys_film11581_closeup.jpg`, `tier2_contact.jpg` (the five Tier 2 houses by day, the Murphys' LOD1 stand-in, an aerial, the plan).
- **Lidar fix:** the step-1 nDSM was georeferenced with the requested bbox; ArcGIS returned a widened extent, so every lidar tree was ~45 m
  off and the footprints sat on bare ground (median p25 0.1 m). Re-fetched with the server's extent (`nb_evidence.py --fetch`, 0.5 m):
  footprints now sit on roofs (p25 5.3 m). Trees and roof profiles below use the fixed raster.
- **Tools:** `nb_textures.py` (kit PBR: Poly Haven CC0 + procedural clapboard/shingle), `nb_kits.py` (writes every kit into
  spec/neighborhood.json with its sources, plus `tiers` and `budgets`), `nb_house.py` (Blender: kit -> <lot>.glb, LOD0 hero + LOD1 stand-in +
  NightGlow + Collider + C7 bulbs json), `nb_street.py` (layout + Street.glb + LampPost.glb), `nb_film_camera.py` (film 11581 camera:
  art/home_alone/references/neighborhood/data/film11581_camera.json), `nb_render.py` / `nb_compare.py` (review renders), `nb_plan.py` (plan map).
  Unity: `SpecGreybox.Neighborhood.cs`, off unless `HA_NEIGHBORHOOD=1`.
- **Murphys (lot_B0), medium:** massing county + lidar; film camera fit (6 corners + the far kerb, rms 11 px) gives eave edge 7.10 +-0.94,
  ridge 11.5, porch roof 4.17. The lidar reads ~6.0 at the wall line: film kept (0.5 m pixels smear the eave); logged DEVIATIONS 121.
  Known differences from 11581 (closeup sheet): the film's porch runs further left past the house corner, its dormer is a little taller,
  the film has a 2-storey side projection at the right rear, bushes hide the porch skirt; lit windows have no curtains yet.
- **Other Tier 2:** lot_B-1 white front-gable (lidar ridge along x), lot_B+1 cream side-hip colonial (G), lot_A-1 white + green shutters
  (film 6399), lot_A+1 cream stucco + red clay tile (film 1886/1891; may be lot_A+2's): confidence per lot in the manifest (`kit_confidence`).
- **Street:** kerb to kerb 10.7 m (our kerb 30.62 as built, far kerb 41.30 inferred from the lidar parkway trees + OSM's B sidewalk), the
  film's acorn lamp (1471/3297/9511), 58 lidar trees (5 m apart, post-1990 trees in front of the Murphys dropped: 11581 shows none).

# Step 3 (Oct 20 2026): the Murphys polished, Marley's house, Tier 3 + 4, street life, the walk boundary (TRIAL, built in scratch)
User direction mid-job (via the coordinator): the walkable heroes are OUR lot, **Marley's (lot_A+1)** and **the Murphys' (lot_B0)**;
every other house is a backdrop past a walk boundary. Sheets (Preview): `murphys_film11581_before_after.jpg` (film | step 2 | step 3),
`murphys_film11581_compare.jpg`, `marley_film1888_compare.jpg` (solved 1888 camera), `step3_street_contact.jpg`, `aerial_step3.jpg`, `plan.png`,
`yard_trees_proposal.png` (front-yard trees: a PROPOSAL, nothing moved); the step-2 sheets are kept in `step3/before/`.
- **Murphys (lot_B0):** house +0.55 m z (both film eave corners and the bays read there), the porch from the house's left corner with the
  film's two left columns (11576), a taller front dormer, a 1-storey side bay at the +z front (11581, grazing; low), room cards behind the
  lit windows (nb_textures.room_cards: sheers + drapes, a lamp, a half shade, a tree), the film's lights (front eave only, a line over the
  porch roof, windows and French doors outlined, swags on the rails, the eave turning the porch's right corner, five lit foundation
  shrubs), the post mailbox and three yard stakes (back-projected through the 11581 camera). Not modelled: 3241's pediment over the steps
  (conflicts with 11581).
- **Marley's house (lot_A+1):** the left neighbour seen from the street (+z). Film 1888 (day) shows an octagonal turret with a tall red
  cone, pale rose walls (sampled: R/G 1.23, G/B 1.03 in sun, 6 % redder than our white portico), white cornice and sashes, red hip roofs, a
  chimney on the left; the 2022 lidar has a 12.5 m peak over the footprint's octagonal corners. Shingle Style kit (nb_house: turret with a
  flared cone and a window band above the wings, flared hip eaves, eyebrow hoods, a recessed entry with round columns up stone steps, a hip
  dormer, the chimney). Film 1888's camera solved on our facade (`tools/house/nb_film1888_camera.py`, 7 points, rms 6.2 px; the van's
  height and no roll as priors). Today's colours (brown shakes, dark green trim, grey roofs; the user's photo) kept as `palette_today`.
- **Tier 2 evidence** (manifest `evidence_step3`): lot_A-1 medium (3246 day: white, green shutters, arched hood), lot_A+1 medium, lot_B-1 and
  lot_B+1 low-medium/low (11576/11581 edges, 3241). These three are now **backdrop** (no colliders, LOD0 only above 25 % of the screen).
- **Tier 3:** 25 lots (8 added past the fork, the bend west and Pine), each footprint split into up to 3 rectangles (nb_kits.rects), fronts
  toward Lincoln's nearest centreline point, outbuildings, ~30 % lit windows, C7s on ~40 % of eaves. Lincoln now ends at its bend (z -118).
- **Tier 4:** 319 bare-tree cards in two rings at r 160-215 m (nb_textures.tree_cards), a snow ground annulus 0.4 m under the lawns; the
  photo dome moves out to R 320 (its photo band reads as the far horizon above the cards). Plan for the window views: the real neighbourhood
  now stands in every window; no dome or card is needed inside 150 m. The wrong-house night card (`WinterBackdrop_NightHouse`) exists only
  in the user's saved scene (the build no longer makes it): any build + load replaces it. The old WinterNeighborhood's street, kerbs,
  sidewalks, houses, poles, wires, ground and street trees (33 swapped trees) are off inside x -60..100, |z| < 150.
- **Street life** (nb_life.py, StreetLife.glb): the film's two police cruisers at the Murphys (night only, red beacon light), the bandits'
  Dodge Ram van by our lamp post (3297), a blue sedan at our kerb (1888), poles and three wires on our side (1564/1888/11581), a red hydrant
  (3295), patchy lawns (nb_textures.snow_patchy), plowed snow piles and hedges at the walk boundary. The cars are PROXIES: a bought model at
  `Assets/Purchased/Vehicles/<kind>.prefab` replaces one at build time (kinds: Car_CapricePolice, Car_RamVan, Car_Caprice).
- **Walk boundary:** invisible 12 m walls around our lot + the stretch of Lincoln (both sidewalks, the road) between Marley's far line and our
  -z side + Marley's and the Murphys' front yards/porches; hedges and snow piles as the soft edge. Build check: every edge cast outward from
  1.5 m inside must be BLOCKED; walk-test routes LINCOLN, OUR SIDEWALK, B SIDEWALK, MARLEY must stay open.
