# Winnetka neighborhood — 2026-09-12

Reference-inspired winter backdrop, not a surveyed replica. Built by `SurveyBuilder.BuildWinterNeighborhood()` under `WinterNeighborhood` in IntactHouseReference. Fifteen simplified neighboring houses, street, sidewalks, verge trees, shrubs and utility wires. Nine shutter pairs fitted to existing main front windows; dormers unchanged. Original house mesh asset and interior unchanged.

Only detached outer snow banks object2946–object2955 have renderers and mesh colliders disabled. Objects/assets are retained. Other original site surfaces remain; snow texture/grade transitions still need refinement. Trees and neighboring architecture are visibly simplified and require higher-detail assets for the requested photoreal target.

Reference photos: Famartin, May 11 2015, Wikimedia Commons, CC BY-SA 4.0. Used for visual reference, not applied as textures.
- [House](https://commons.wikimedia.org/wiki/File:2015-05-11_06_38_29_View_of_the_%22Home_Alone%22_house_at_671_Lincoln_Avenue_in_Winnetka,_Illinois.jpg)
- [Street northwest](https://commons.wikimedia.org/wiki/File:2015-05-11_06_41_49_View_northwest_up_Lincoln_Avenue_from_in_front_of_the_%22Home_Alone%22_house_at_671_Lincoln_Avenue_in_Winnetka,_Illinois.jpg)
- [Street southeast](https://commons.wikimedia.org/wiki/File:2015-05-11_06_41_46_View_southeast_down_Lincoln_Avenue_from_in_front_of_the_%22Home_Alone%22_house_at_671_Lincoln_Avenue_in_Winnetka,_Illinois.jpg)

Validation: CheckWinterNeighborhood passes eight real-controller street/sidewalk/front-walk checkpoints; CheckIntactMainStairs passes spawn and eleven house checkpoints. Exterior route stops before existing entrance steps; it does not verify every yard or neighboring interior. Initial front-walk endpoint near the original step produced a height mismatch, so the endpoint was moved back to the level approach. Captures neighborhood-front.png and neighborhood-outward.png inspected. Daytime retained.
