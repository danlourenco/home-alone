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
