# Furniture and prop sourcing (research, Oct 16 2026)

Room-by-room inventory of the furniture and props that make each room read right, with the best 3D-model candidates found online. This is research only: nothing here is placed, bought or committed. Every placement still goes through `change-gate` and `spec/dressing/*.json`.

Already chosen by the user and left out of this list: the landing demilune (Classic Wooden Furniture Pack `SIDE_TABLE_01`), the grandfather clock (Fadnn `SM_PendulumClock_01`), the Free Wood Door Pack `Door_3_White` doors, and the kitchen cabinets, counters and island (procedural).

## How to read this

- **Authority.** The film decides what a piece looks like wherever the film shows it. Marina's tour decides layout and fills in rooms the film never shows. Frame numbers like `5650` are `0-homealone/full/homealone-movie-screencaps.com-5650.jpg`. `M07` is `art/home_alone/references/tour/frames/M07-07m20s.png` (Part 1). `p2-235s` is a Part 2 frame in the room's reference folder.
- **Size.** "measured" means a box already in `spec/dressing/foyer.json`, `spec/furniture.json` or a reference README, solved from Marina's frames. "standard" means a US furniture standard, not measured. "inferred" is a blockout size nobody has checked.
- **Confidence.** `seen` means visible in at least one frame I inspected. `partial` means glimpsed, cropped or dark. `unseen` means I did not find it in any frame, so it is listed only because Marina or the README has it.
- **Licence key.** `CC0` can be committed (public repo). `CC-BY` can be committed with an attribution line. `CC-BY-NC` / `CC-BY-SA` / `Sketchfab Free Standard` are flagged below. `RF (no AI)` is CGTrader's Royalty-Free licence: game use is fine, no AI training, no redistribution, so keep it gitignored. `AS EULA` is the Asset Store EULA: no redistribution, so gitignore it like the current packs. `TS Std` is the TurboSquid Standard licence: same rule.
- **Prices** are what the listing showed on Oct 16 (CGTrader often runs 30-50% sales). Prices marked `~` come from a search snippet and were not confirmed on the page, because CGTrader rate-limited my scraper partway through.
- **Pipeline.** Poly Haven, Sketchfab and CGTrader files are FBX/GLB/OBJ with metal-roughness PBR maps. In HDRP they need an HDRP/Lit material with a mask map (metal R, AO G, detail mask B, smoothness A) packed from the separate maps. Nothing in this list ships HDRP prefabs except the Asset Store packs that say so.

## Already owned (check these first)

I rendered both owned packs in Blender (`/Applications/Blender.app`, workbench) to see what they hold. Sizes are the FBX bounds (W x D x H in metres).

| Pack | Piece | Size | Use in the house | Verdict |
|---|---|---|---|---|
| Classic Wooden Furniture Pack | `BEDSIDE_CAB_01` 3-drawer nightstand | 0.53 x 0.44 x 0.64 | Buzz's nightstand (measured box 0.66 x 0.40 x 0.65) | **Good fit**, plain traditional |
| Classic Wooden Furniture Pack | `DRAWER_CAB_01` low 4-drawer dresser | 1.14 x 0.39 x 0.70 | Kevin and Jeff's low dresser (Marina p2-365s) | Good shape; add a separate mirror |
| Classic Wooden Furniture Pack | `DINING_TABLE_01` turned-leg table | 2.19 x 1.02 x 0.74 | Dining-room table (film 250 hides it under a cloth) | Usable under a tablecloth |
| Classic Wooden Furniture Pack | `CHAIR_01` ladder-back chair | 0.52 x 0.49 x 0.97 | Kevin's desk chair, attic | Fair |
| Classic Wooden Furniture Pack | `BED_01` double, turned posts | 1.82 x 1.75 x 1.07 | Not the parents' bed (too short, no tall posts) | Attic or girls' room filler |
| Classic Wooden Furniture Pack | `WARDROBE_01`, `BOOKCASE_01`, `SHELVES_01`, `WALL_SHELF_01` | | Bedroom fillers | Plain, usable |
| Fadnn Vintage Interior | `SM_Desk_01` pedestal desk | 1.61 x 0.94 x 0.86 | Den window desk (Marina M09) | Good |
| Fadnn Vintage Interior | `SM_Couch_v01` rolled-arm sofa | 1.82 x 1.08 x 0.83 | Den sofa (Marina M26, red) | Fair; low-poly (1k faces) |
| Fadnn Vintage Interior | `SM_Lamp_02` floor lamp, `SM_Lamp_01` table lamp | 1.33 / 0.40 tall | Den, living room | Fair |
| Fadnn Vintage Interior | `SM_Table_01` pedestal side table | 0.59 x 0.59 x 0.69 | Living-room or den side table | Good |
| Fadnn Vintage Interior | `SM_Piano_01` **grand** piano | 1.59 x 3.31 x 1.00 | **Wrong piano**: the film has an upright (see Living room) | Do not use |
| Fadnn Vintage Interior | `SM_OldPhone_01`, `SM_ClassicPhone_01`, books, `SM_BaseballBat_01` | | Desk props; the bat suits Buzz's room or the basement | Good small props |
| Fadnn Vintage Interior | indoor plants (Banyan, Palm, Fern, Snake, ZZ) | | Stylised, very low poly (200-500 faces) | Too low for walking distance |

## Packs that cover many items

| Pack | Source | Price | Licence | Covers | Notes |
|---|---|---|---|---|---|
| [Poly Haven models](https://polyhaven.com/models) | Poly Haven | free | **CC0** | dining crystal chandelier, breakfast brass chandelier, pedestal plant stands, CRT TV, picture frames, mantel clock, candlesticks, luggage, dartboard, ottoman, Chesterfield sofa, books, side tables, potted tree | Photoreal, scanned-quality PBR, 1-8K maps, glTF/FBX/blend. Can be committed. Best value overall. |
| [Christmas Tree, Wreath, Garland and Bubble Lights](https://assetstore.unity.com/packages/3d/vegetation/trees/christmas-tree-full-size-with-ornaments-and-lights-187396) | Unity Asset Store | not confirmed | AS EULA | tree, wreath, garland, lights | Realistic, but listed **Built-in only**: convert its materials to HDRP/Lit. |
| [Christmas Decor Pack](https://assetstore.unity.com/packages/3d/props/christmas-decor-pack-291100) (Jesse Mario) | Unity Asset Store | $9.99 | AS EULA | 39 LOD meshes, PBR | HDRP listed as compatible. The page does not list its contents; check the Package Content tab before buying. |
| [Zowwy's Kitchen Appliances](https://assetstore.unity.com/packages/3d/props/furniture/zowwy-s-kitchen-appliances-212035) | Unity Asset Store | $15.99 | AS EULA | fridges, oven, microwave, hood, hob, toaster | Built for HDRP first. Its style is modern, so it is a fallback for the film's 1990 appliances. |
| [Victorian Chairs Pack](https://assetstore.unity.com/packages/3d/props/interior/victorian-chairs-pack-295359) (G-Star) | Unity Asset Store | $9.49 | AS EULA | 27 chairs, armchairs, stools (400-4,600 polys, 1K maps) | HDRP compatible. Low texture resolution. Might hold a Chippendale-like dining chair; contents not shown on the page. |
| [Mad_Lobster_Workshop on Sketchfab](https://sketchfab.com/Mad_Lobster_Workshop) | Sketchfab | free | CC-BY | Windsor bow-back chairs (2 sets), steamer trunks, vintage suitcases, French and Austrian vanities | Consistent, good-quality period sets. Credit the author. |

## Foyer, vestibule, stair and landing

Film: 3225, 10248, 9358, 11966, 12133, 2677, 1690 (`best-film-1690.jpg`), 3888. Marina: M01, M04, M05, M20, M29, `foyer-film/best-tour-*`.

| # | Item | Film version | Seen in | Size | Qty | Best candidates | Fidelity note |
|---|---|---|---|---|---|---|---|
| F1 | **Poinsettias, red, gold-foil pots** (stair treads, landing table, upstairs hall floor) | Full red bracts on dark green, in crinkled gold-foil wrapped pots | 3225, 11966, 12133, 1333, 1350, 1400, 3900 (seen) | ~0.40 dia x 0.35 h plant (foyer.json `flowers_*` box, measured); pot ~0.15-0.20 standard | ~6-10 | See the **Poinsettia evaluation** below. Pick: [Poinsettia Gift Plant](https://www.cgtrader.com/3d-models/plant/flower/poinsettia-gift-plant-21cb2b31-91f8-481b-b9dc-e82ca532d633) (3dia, CGTrader, $5, RF no AI, FBX/OBJ, low-poly, verified FBX). Alt: [Poinsettia](https://sketchfab.com/3d-models/de8ba50efa3f4dc8b319758e26217ea7) (Sketchfab, free, CC-BY, 27k faces, no foil) | Gift Plant has a foil-wrapped pot, but the foil is red: retint the foil material to gold. |
| F2 | **Poinsettias, white, gold pots** on the pedestals either side of the front door | White bracts in gold foil on dark pedestals | 10248, 9358, 5650 (living room, seen) | 0.40 x 0.35 (measured box) | 2 + 1 | CGTrader [Poinsettia plant 06](https://www.cgtrader.com/3d-models/plant/bush/poinsettia-plant-06) / [07](https://www.cgtrader.com/3d-models/plant/bush/poinsettia-plant-07) (white, $10 each, RF no AI, **3ds Max V-Ray/Corona only**, no pot); or the Gift Plant with white bract texture | Plant 06/07 look right but need a Max-to-FBX conversion and decimation. A bract recolour of F1 is the cheaper path. |
| F3 | **Pedestal plant stands** (front door pair) | Tall dark wood column stands, round top | 10248, 9358 (seen) | 0.28 x 0.28 x 0.95 (measured) | 2 (+1 living room) | [side_table_tall_01](https://polyhaven.com/a/side_table_tall_01) (Poly Haven, CC0); [Old Vintage Furniture Pack](https://assetstore.unity.com/packages/3d/props/furniture/old-vintage-furniture-pack-227706) (contents unconfirmed) | Poly Haven stand has splayed legs and a shelf; the film's are straighter columns. Close silhouette, right colour. |
| F4 | **Weeping fig (ficus) tree** beside the stair | ~2 m ficus, dense small leaves, in a brass/wicker pot | 2677, 1690, 3888, M01, M04, M20 (seen) | 0.60 crown, 1.89 m top, pot 0.33 (measured) | 1 | [Indoor Decorative Ficus Tree](https://www.cgtrader.com/3d-models/plant/pot-plant/indoor-decorative-ficus-tree) (CGTrader, $10, FBX/blend, PBR, low-poly); [Variegated Ficus Tree](https://www.cgtrader.com/3d-models/plant/pot-plant/variegated-ficus-tree-3d-model) ($12); [potted_plant_01](https://polyhaven.com/a/potted_plant_01) (Poly Haven, CC0, terracotta urn) | Swap the pot for a brass one. TurboSquid has game-ready weeping figs with LODs and wind at $34-39 (TS Std) if these look thin. |
| F5 | **Hall bench** against the stair | Marina: green velvet bench with scrolled arms. Film: not clearly seen | M01 (Marina, seen); film unseen | 1.25 x 0.48 x 0.45 (measured) | 1 | [Small upholstered bench with bolsters](https://sketchfab.com/3d-models/fe99fcfb6bbb45649e9e38de24b23109) (Sketchfab, CC-BY, 37k faces) | Right type, wrong colour: recolour to green velvet. No close period match found; a model or procedural build is reasonable. |
| F6 | **Side chairs** flanking the console | Dark wood, red upholstered seat, shield/splat back | 1690, M20, M29 (seen) | seat 0.44 square (measured) | 2 | Owned `CHAIR_01` (ladder back) as a stand-in; [Victorian Chairs Pack](https://assetstore.unity.com/packages/3d/props/interior/victorian-chairs-pack-295359) | Same family as the dining chairs (D2); buying one Chippendale-style chair covers both rooms. |
| F7 | **Console / demilune** under the mirror | Dark mahogany demilune | M20, M29 (seen); film partial | 1.0 x 0.36 x 0.61 (measured top) | 1 | Owned `SIDE_TABLE_01` (same piece as the landing); [ClassicConsole_01](https://polyhaven.com/a/ClassicConsole_01) (Poly Haven, CC0) | Reusing the landing model keeps the house consistent. |
| F8 | **Oval gilt mirror** over the console | Oval glass, gilt frame with a crest | M20, M29 (seen) | 0.56 x 1.04 (measured; width assumed) | 1 | [Kirkland Gold Oval Baroque Wall Mirror](https://www.cgtrader.com/3d-models/furniture/other/kirkland-gold-oval-baroque-wall-mirror) (CGTrader, price not confirmed, FBX/Max); [Oval Victorian mirror](https://www.turbosquid.com/3d-models/oval-victorian-mirror-3d-model/1134121) (TurboSquid, ~52k polys, FBX); [ornate_mirror_01](https://polyhaven.com/a/ornate_mirror_01) (CC0, arched not oval) | Kirkland is the closest shape. Poly Haven is the free fallback but the wrong outline. |
| F9 | **Oriental rugs** (front-door rug, foyer runner) | Red, navy and cream Persian patterns | 2677, 1690, 3888, M01 (seen) | front rug 1.26 x 1.70 (measured) | 2-3 | [Orientteppich Agra Täbriz](https://sketchfab.com/3d-models/75e3aa2070f14720ad768cff77efa919) (Sketchfab, CC-BY, scanned); or a flat plane with a CC0 rug texture | Rugs are better made procedurally (a thin box plus a texture). Only the texture needs sourcing. |
| F10 | **Framed pictures** (stair gallery, botanical prints by the door, landing painting) | Gilt and dark frames; green-matted botanical prints | 10248, 3225, 2677, M04 (seen) | prints 0.48 x 0.58; landing 0.57 x 0.63 (measured) | ~12 | [fancy_picture_frame_01/02](https://polyhaven.com/a/fancy_picture_frame_01), [hanging_picture_frame_01-03](https://polyhaven.com/a/hanging_picture_frame_01) (CC0) | Frames are easy. The artwork must be public-domain images, not film captures. |
| F11 | **Brass candle wall sconces** | Two-arm brass sconces, shades | 10248, 9358 (seen) | ~0.25 x 0.35 standard | 2-4 | No close match found. Model or procedural build. | |

### Poinsettia evaluation (CGTrader `/3d-models/poinsettia`, all 20 listings checked)

The film's poinsettias (3225, 11966, 1333, 3900) are compact red plants in **crinkled gold-foil wrapped nursery pots**. No listing has a gold-foil pot. Every candidate needs a pot retint or a new pot.

| Listing | Price | Format | Pot | Verdict |
|---|---|---|---|---|
| [Poinsettia Gift Plant](https://www.cgtrader.com/3d-models/plant/flower/poinsettia-gift-plant-21cb2b31-91f8-481b-b9dc-e82ca532d633) (3dia) | $5 | FBX, OBJ, textures; low-poly; CGT-verified FBX | **Foil-wrapped**, red | **Best match.** Retint the foil to gold. |
| [Festive Poinsettia Pack](https://www.cgtrader.com/3d-models/plant/flower/festive-poinsettia-pack) (WonderFuel) | $19.99 | FBX (1.02 GB), glTF (470 MB), PNG | 20 variants, several pot styles | Very heavy (FBX over 1 GB): it needs decimation and texture downsizing. The marketing render looks AI-assisted, so check the actual meshes before buying. |
| [Christmas Poinsettias](https://www.cgtrader.com/3d-models/plant/flower/christmas-poinsettias) | $15 | FBX, OBJ, blend | white ceramic | Fair. Swap the pot. |
| [Poinsettia Christmas](https://www.cgtrader.com/3d-models/plant/flower/poinsettia-christmas) (archienvo) | $22 | FBX/OBJ/C4D/blend, ~200 MB | none | Too heavy, no pot. |
| [Poinsettia plant / 02-08](https://www.cgtrader.com/3d-models/plant/bush/poinsettia-plant-02) (set) | $10-12 each | **3ds Max (V-Ray/Corona) only** | none | Photoreal, but needs Max to export and heavy decimation. 06 and 07 are the white ones. |
| [XfrogPlants Poinsettia](https://www.cgtrader.com/3d-models/plant/flower/xfrogplants-poinsettia) | $19.98 | Xfrog and exports | none | High poly, no pot. |
| [Poinsettia Parrot Beak](https://www.cgtrader.com/3d-models/plant/leaf/poinsettia-parrot-beak-plant) | $14 | C4D (159 MB) | small red pot | Wrong format. |
| [Flower Euphorbia Pulcherrima](https://www.cgtrader.com/3d-models/plant/flower/flower-euphorbia-pulcherrima) | $8.99 | unitypackage | none | **Editorial licence: do not use in the game.** |
| [Red Potted Flowers](https://www.cgtrader.com/3d-models/plant/flower/red-potted-flowers) (Evermotion) | $9.66 | OBJ only | red ceramic | Silk faux poinsettia, old, no materials. |
| Poinsettia low poly / Poinsettia Flower / D Model Pack / African violets | $4-45 | various | | Single flower heads, 3D-print packs or stylised. Not useful. |

Free alternatives on Sketchfab: [Poinsettia (gggp999)](https://sketchfab.com/3d-models/de8ba50efa3f4dc8b319758e26217ea7) (CC-BY, 27k faces) and [Poinsettia 3D Photoscan](https://sketchfab.com/3d-models/a473413e1b764f678d908fa60c3aecf2) (CC-BY, 116k faces, scanned). Avoid [Christmas Poinsettia (globalmobisoft)](https://sketchfab.com/3d-models/5440b61bd26a4cf5887943616a6df2aa): it is CC-BY-NC-SA. Daz3D's [Predatron Poinsettias](https://www.daz3d.com/predatron-poinsettias) needs a Daz Interactive licence for game use.

**Recommendation:** buy the $5 Gift Plant and retint its foil gold. Make a white variant (F2) with a bract-texture recolour. If the leaves read too low-poly up close on the stair, use the CC-BY photoscan for the plant and keep the Gift Plant's foil pot.

## Living room

Film: 5650 (piano wall, seen clearly), 10600 (tree and fireplace), 5750 (green sofa; room likely the living room, not certain), 10685/10706 in `foyer-film/`. Marina: M06, M07, M25, M28.

| # | Item | Film version | Seen in | Size | Qty | Best candidates | Fidelity note |
|---|---|---|---|---|---|---|---|
| L1 | **Upright (console) piano + bench** | **Mahogany console upright** with music desk, matching bench on cabriole legs, brass piano lamp on top. **Marina has a grand piano; the film shows an upright.** | 5650 (seen clearly) | ~1.47 W x 0.60 D x 1.07 H (standard console) | 1 + bench | [Kimball Artist Console Upright Piano (antique walnut)](https://www.cgtrader.com/3d-models/furniture/other/kimball-artist-console-upright-piano-80-antique-walnut) (CGTrader, ~$25, RF, FBX/OBJ, made from manufacturer dimensions); [Brown Cherry Wood Upright Piano](https://sketchfab.com/3d-models/ae0529d9da834820b8a9c30ec0b6228f) (Sketchfab, free, CC-BY, 1.8k faces); [Vintage Upright Piano](https://sketchfab.com/3d-models/535d2c6465d243c4a17dd87650fa2c88) (CC-BY, 10.8k, has a bench, white) | Kimball is the right era and type: retint walnut to mahogany and strip the logo. **Log the film-vs-Marina conflict in DEVIATIONS before placing it.** |
| L2 | **Brass piano lamp** | Brass bar-shade piano lamp | 5650 (seen) | ~0.35 W standard | 1 | No good match found. Model it (a bar shade on an arm is simple). | |
| L3 | **Christmas tree** | Tall, dense natural fir, multicolour lights, tinsel, many ornaments, gifts underneath | 10600 (seen); Marina M06 | ~2.4 m H x 1.4 m dia (standard for 8 ft ceilings) | 1 | [Christmas Tree, Wreath, Garland and Bubble Lights](https://assetstore.unity.com/packages/3d/vegetation/trees/christmas-tree-full-size-with-ornaments-and-lights-187396) (Asset Store, realistic, Built-in only); CGTrader [Christmas tree ($11)](https://www.cgtrader.com/3d-models/interior/other/christmas-tree-273bdf2a-0a70-4638-b815-af4b57deaf03), [Christmas Tree ($12)](https://www.cgtrader.com/3d-models/interior/other/christmas-tree-e2dec448-cb94-4aca-afe3-6fc741586c79) (FBX/Max, archviz-heavy) | No game-ready realistic tree with the film's coloured C7 bulbs turned up. Expect to decimate an archviz tree and add emissive bulbs. **High impact, low confidence.** |
| L4 | **Wingback armchair, red** | Marina: red wingback at the piano end. Film: not clearly seen | M07 (Marina, seen); film unseen | ~0.80 x 0.85 x 1.10 standard | 1 | [Queen Anne Wingback Armchair](https://www.cgtrader.com/3d-models/furniture/chair/queen-anne-wingback-armchair) (CGTrader, price not confirmed); [Brown Wingback Chair](https://sketchfab.com/3d-models/ccd0712b0d76408fbc95952cabf067c5) (Sketchfab, CC-BY, 58k); [Vintage Wingback Armchair](https://sketchfab.com/3d-models/d606a3eb868d4122855bc7a82d2889a9) (CC-BY, 103k) | Recolour to red. Queen Anne cabriole legs match Marina. |
| L5 | **Green sofa** | Green velvet roll-arm sofa, red throw | 5750 (seen; room inferred) | ~2.1 x 0.9 x 0.85 standard | 1 | Owned Fadnn `SM_Couch_v01` (recolour); [sofa_03](https://polyhaven.com/a/sofa_03) (Poly Haven, CC0, camelback); [Chesterfield Sofa - 6 versions](https://www.cgtrader.com/3d-models/furniture/sofa/chesterfield-couch-6-versions) ($20) | Poly Haven `sofa_03` (camelback, ornate) is the closest free shape: re-skin it with green velvet. |
| L6 | **Fireplace screen + tools** | Brass folding screen | 10600 (partial), M06 | ~0.8 x 0.75 | 1 | [Fireplace Screen](https://sketchfab.com/3d-models/f6612d6deeb6498aaa95b07bfcc94987) (Sketchfab, CC-BY, 18k) | Iron, not brass: retint it. |
| L7 | **Mantel garniture**: stockings, wreath, clock, candles | Stockings and garland (Marina) | M06 (Marina) | | set | [mantel_clock_01](https://polyhaven.com/a/mantel_clock_01), [brass_candleholders](https://polyhaven.com/a/brass_candleholders) (CC0); Christmas Decor Pack (above) | |
| L8 | **Sofa table / console with lamp** | Dark wood; black lamp with shade | 5650, M06 (seen) | ~1.5 x 0.4 x 0.75 standard | 1-2 | [ClassicConsole_01](https://polyhaven.com/a/ClassicConsole_01) (CC0); owned `SM_Lamp_01` | |
| L9 | **Wall shelf brackets with porcelain figurines** | White Staffordshire-style dogs on gilt brackets | 5650 (seen) | small | 2 | No match. Low priority. | |
| L10 | **Nutcrackers** | Red-coated soldier nutcrackers, ~0.4 m | 5650 (seen) | ~0.4 H | 2-3 | [Nutcracker (julialemke)](https://sketchfab.com/3d-models/bb182cd70cd244b291ba0e3020f132ce) (CC-BY, 9.9k); [Nutcracker (fccooper)](https://sketchfab.com/3d-models/55ad862de9d14e88b9f4280431b9c6ed) (CC-BY, 134k) | Good. |
| L11 | **Toy train set** around the tree | Black steam train, oval track | 5650 (seen) | ~1.5 m oval | 1 | No good game-ready match found. | Low priority. |
| L12 | **Drapes** | Deep green damask with tie-backs | 5650 (seen) | per window | n | Procedural (as the current sheers) | |
| L13 | **Oriental rug** | Large red Persian | 10600, M06 | ~2.7 x 3.7 standard | 1 | Texture on a plane (see F9) | |

## Den (family room)

Film: not identified in the frames I checked. Marina: M08, M09, M26, M27.

| # | Item | Version (Marina) | Seen in | Size | Qty | Best candidates | Fidelity note |
|---|---|---|---|---|---|---|---|
| N1 | Built-in bookcase / TV wall | Dark-stained built-in shelving with a CRT | M08 (Marina) | built-in | 1 | Procedural (joinery, like the kitchen) + [book_encyclopedia_set_01](https://polyhaven.com/a/book_encyclopedia_set_01), [decorative_book_set_01](https://polyhaven.com/a/decorative_book_set_01) (CC0), owned Fadnn books | |
| N2 | **CRT television** | Late-80s console CRT | M08 | ~0.65 W | 1 | [television_02](https://polyhaven.com/a/television_02) (Poly Haven, CC0) | Very good era match. |
| N3 | Sofa, red/burgundy | Rolled arms | M26 | ~2.1 m | 1 | [sofa_02](https://polyhaven.com/a/sofa_02) (CC0, black leather Chesterfield); [Tufted Chesterfield Sofa Pack](https://www.cgtrader.com/3d-models/furniture/chair/tufted-chesterfield-sofa-pack) ($17.99, glTF/FBX, PBR, low-poly); [William Blake Chesterfield sofa + armchair](https://www.cgtrader.com/3d-models/furniture/sofa/william-blake-chesterfield-armchair-and-sofa) ($45) | Recolour to Marina's red. |
| N4 | Leather club armchair | Brown leather | M27 | ~0.9 m | 1-2 | [Old Armchair](https://sketchfab.com/3d-models/c20f084f29bd440197a18b4c750f69eb) (CC-BY, 2.6k); [Ottoman_01](https://polyhaven.com/a/Ottoman_01) (CC0) | |
| N5 | Round coffee table, floor lamp | Wood; brass lamp with cream shade | M26 | | 1 + 1 | [round_wooden_table_01](https://polyhaven.com/a/round_wooden_table_01) (CC0); [Classic Brass Floor Lamp](https://sketchfab.com/3d-models/6a622c7295c64317bcf8166ff23f9aa5) (CC-BY, 10k); owned `SM_Lamp_02` | |
| N6 | Window desk + chair + green lamp | Dark desk, bentwood chair | M09 | ~1.2 m | 1 | Owned Fadnn `SM_Desk_01` + `SM_Chair_01`; [Desk lamp (7ASSAN)](https://sketchfab.com/3d-models/b9458e04d30e4b6284d46d35880a9b95) (CC-BY banker's lamp, 7.5k) | Good from owned packs. |

## Dining room

Film: 250 (table, chairs, chandelier), 10550 (china cabinet). Marina: M02, M03, M16, M24.

| # | Item | Film version | Seen in | Size | Qty | Best candidates | Fidelity note |
|---|---|---|---|---|---|---|---|
| D1 | Dining table | Under a white lace-edged cloth (film); dark rectangular (Marina) | 250, M02 (seen) | ~2.2 x 1.0 x 0.74 standard | 1 | Owned `DINING_TABLE_01` (2.19 x 1.02 x 0.74) + a procedural tablecloth | Good. |
| D2 | **Dining chairs, Chippendale style** | Dark mahogany, pierced splat back, upholstered seats | 250, M02, M24 (seen) | 0.56 x 0.65 x 1.02 standard | 8 | [Victorian Chippendale Dinning Chair](https://sketchfab.com/3d-models/victorian-chippendale-dinning-chair-49a5ed3d03534fd4959111bcd6f97f3d) (Sketchfab Store, paid, price not confirmed); [CHIPPENDALE CHAIR](https://www.cgtrader.com/3d-models/furniture/chair/chippendale-chair) (CGTrader, SketchUp, ~$25); [Victorian Chairs Pack](https://assetstore.unity.com/packages/3d/props/interior/victorian-chairs-pack-295359) ($9.49, HDRP) | No verified game-ready Chippendale chair found. These 8 chairs read strongly, so **consider modelling one chair** to the film (one mesh x 8, also used for F6). |
| D3 | **Crystal chandelier** | Brass and crystal, candle arms | 250 (seen) | ~0.7 dia standard | 1 | [Chandelier_03](https://polyhaven.com/a/Chandelier_03) (Poly Haven, CC0, crystal) | Very close. |
| D4 | **China cabinet** | Dark mahogany, glazed upper doors full of stemware | 10550 (seen), M03 | ~1.2 x 0.45 x 2.0 standard | 1 | [vintage_cabinet_01](https://polyhaven.com/a/vintage_cabinet_01) (CC0, dark, glazed upper); [China cabinet (TurboSquid)](https://www.turbosquid.com/3d-models/3d-model-china-cabinet/423947) (~50k polys, Max, with dishware); [Low Poly China Cabinet](https://sketchfab.com/3d-models/df702c25881e4e31a431bce54b197f0f) (CC-BY, 4.4k) | Poly Haven is the best free start; add glassware. |
| D5 | Centrepiece, candlesticks | Red poinsettia/roses centrepiece, brass candles | M02, M16, M24 | | 1 | F1 poinsettia; [brass_candleholders](https://polyhaven.com/a/brass_candleholders) (CC0) | |
| D6 | Paintings in gilt frames | Landscapes/still life | 250, M02 | ~0.8 x 0.6 | 2-3 | [fancy_picture_frame_01](https://polyhaven.com/a/fancy_picture_frame_01) (CC0) | |
| D7 | Sideboard / buffet | Partial view only | M24 (partial) | | 1 | owned `DRAWER_CAB_01` stand-in | Low confidence: not clearly seen. |

## Kitchen and breakfast area

Film: 1150, 2200, 2800, 9450, 9500, `kitchen/film-kitchen-wide.jpg`, `film-kitchen-reverse.jpg`, `film-island-detail.jpg`, `back-stair/best-film-2528.jpg`, `kitchen/production-breakfast-hutch.jpg`, `foyer-film/IMG_3842.JPG`. Marina: M12-M15, M18, M19, M21-M23.

| # | Item | Film version | Seen in | Size | Qty | Best candidates | Fidelity note |
|---|---|---|---|---|---|---|---|
| K1 | **Refrigerator, black** | Tall black side-by-side or top-freezer, near the breakfast transition | 1150, M19 (seen) | ~0.91 x 0.75 x 1.75 standard | 1 | [Zowwy's Kitchen Appliances](https://assetstore.unity.com/packages/3d/props/furniture/zowwy-s-kitchen-appliances-212035) ($15.99, HDRP); black side-by-side models on TurboSquid (modern, TS Std) | None are 1990 era. A **procedural box** with door seams and handles reads as well as a bought model. |
| K2 | **Island stools** | Natural oak, round seat, four splayed legs, foot ring, no back | `film-kitchen-reverse`, `film-island-detail`, 2200 (seen) | seat ~0.76 H standard | 5 + 3 | [wooden_stool_01](https://polyhaven.com/a/wooden_stool_01) (CC0; scale to bar height); [Wooden Bar Stool](https://sketchfab.com/3d-models/c6b783ab624d42f992331a0ac002b2b5) (CC-BY, 2.2k) | Poly Haven's stool is the right construction; stretch its legs to bar height. |
| K3 | **Hanging pot rack with pots** | Iron ring/bar over the island, red and black enamel pots | `film-island-detail`, 1150 (seen) | ~1.2 x 0.5 | 1 | [Hanging Pot Rack](https://sketchfab.com/3d-models/d5dd65f6e88442dca5b49229f724f6c0) (CC-BY, 46k); [Kitchen Asset Pack - Pots, pans](https://sketchfab.com/3d-models/ad96f9a6f4894a74a96b7e917a36936c) (CC-BY); [pot_enamel_01](https://polyhaven.com/a/pot_enamel_01) (CC0) | Strong identifying feature of the film kitchen. |
| K4 | **Breakfast table** | Light oak oval table | 2528, M23 (seen) | 1.05 x 2.80 (blockout, inferred, unchecked) | 1 | No good match found. Model or procedural build (oval top, trestle or pedestal). | |
| K5 | **Breakfast chairs** | Light oak spindle-back Windsor / captain's chairs | 2528, M15, M19, M23 (seen) | 0.45 x 0.5 x 0.95 standard | 8 | [1800s Windsor Bow-Back Chairs](https://sketchfab.com/3d-models/3f1d7ca9158446d0a7fbdd829c195d43) and [Type B](https://sketchfab.com/3d-models/71b5523651014b8e857180bdd0a7b56a) (Mad_Lobster_Workshop, CC-BY, 37k / 74k); [Windsor Chair](https://sketchfab.com/3d-models/5e5cdf7b3b0d468ea12d5e2a1e9840e0) (CC-BY, 12k) | Good. Lighten the wood to oak. |
| K6 | Breakfast hutch | White glazed built-in hutch | production photo, M18 (seen) | built-in | 1 | **Procedural** with the kitchen cabinetry. Fallback: [Vintage Shaker Hutch](https://www.cgtrader.com/free-3d-models/furniture/kitchen-cabinet/vintage-shaker-hutch-or-buffet) (CGTrader, free, glTF/FBX, PBR) | Built-in, so generate it. |
| K7 | Breakfast chandelier | Brass multi-arm with upward white glass bowls | IMG_3842, M23 (seen) | ~0.7 dia | 1 | [Chandelier_02](https://polyhaven.com/a/Chandelier_02) / [Chandelier_01](https://polyhaven.com/a/Chandelier_01) (CC0) | Poly Haven shades hang down; the film's bowls face up. Close enough at a distance. |
| K8 | Microwave (white, 1990) | White countertop microwave, digital panel | 9500 (seen) | ~0.5 x 0.38 x 0.3 | 1 | [70s Retro Microwave](https://sketchfab.com/3d-models/bdab9eb27f524fb19de649151905bbf7) (CC-BY, 1.9k); [vintage_microwave](https://polyhaven.com/a/vintage_microwave) (CC0, but brown 70s) | Neither is the white 1990 unit. Small item; procedural is fine. |
| K9 | Wall oven, cooktop | Black glass wall oven, island cooktop | M13, M14, `film-kitchen-wide` (seen) | built-in | 1 | Procedural with the cabinets | |
| K10 | Countertop props | Red kettle, white drip coffee maker, toaster, paper towels | `film-kitchen-reverse`, 1150 (seen) | small | set | [Vintage Style Kettle](https://sketchfab.com/3d-models/8e53dadfbcdf4875bc6190545f9f688b) (CC-BY; retint red); [vintage_electric_kettle](https://polyhaven.com/a/vintage_electric_kettle) (CC0) | |
| K11 | Window-seat cushions, red | Red cushions in two recesses | M13, M14 (seen) | per recess | 2 | Procedural | |
| K12 | Plants, wall plates, sconces | Small pictures and plates on the floral paper | M15, `film-island-detail` | | set | Poly Haven frames, `potted_plant_02` (CC0) | |

## Back (service) stair

Film: 912, 2528, 3607. Marina: p1-916s, p1-933s. Only the stair itself and the dining/breakfast pieces above show; no free-standing furniture seen on the stair. Nothing to source.

## Kevin and Jeff's room

Film: the room is barely shown; frame 300 shows a wooden ladder or bunk end and a red suitcase, room not certain. Marina: p2-355s, 365s, 375s, 385s (`kevin-bedroom/`).

| # | Item | Version (Marina) | Seen in | Size | Qty | Best candidates | Fidelity note |
|---|---|---|---|---|---|---|---|
| KV1 | **Wooden bunk beds** | Honey pine, panel ends, ladder, green quilts | p2-355s, p2-375s (seen) | twin 0.99 x 1.91 mattress; ~1.05 x 2.05 x 1.6 frame (standard) | 1 | [simple wooden bunk bed](https://sketchfab.com/3d-models/a7685bd7b2354157b4c1a8264892acf0) (CC-BY, 19k); [Bunk Bed](https://www.cgtrader.com/free-3d-models/interior/bedroom/bunk-bed-fd1bd2f8-20ad-4c54-8060-ffc0077f4d69) (CGTrader free, FBX/blend) | Neither has Marina's panel ends. Matters for gameplay (Kevin hides), so **model it**, or kit-bash from the owned `BED_01` posts. |
| KV2 | Low dresser with mirror | Honey pine, 6 drawers; separate wall mirror | p2-365s, p2-375s | ~1.3 x 0.45 x 0.8 | 1 | Owned `DRAWER_CAB_01` + a wood-frame mirror | Good. |
| KV3 | Reading armchair | Pale grey upholstered, wood arms | p2-365s | ~0.75 m | 1 | [ArmChair_01](https://polyhaven.com/a/ArmChair_01) (CC0, grey, ornate legs) | Close in colour, fancier legs. |
| KV4 | Desk + spindle chair + green banker's lamp | Pine | p2-385s | ~1.1 x 0.55 | 1 | Owned `SM_Desk_01` / `CHAIR_01`; [Desk lamp](https://sketchfab.com/3d-models/b9458e04d30e4b6284d46d35880a9b95) (CC-BY) | |
| KV5 | Toy trunk | Wicker / pine trunk | p2-385s | ~0.8 x 0.45 x 0.5 | 1 | [treasure_chest](https://polyhaven.com/a/treasure_chest) (CC0); [Vintage Steamer Trunk](https://sketchfab.com/3d-models/78d7b6f1e70041c498663b4a4145c559) (CC-BY, 11.6k) | |
| KV6 | Dartboard, pinboard, globe, bookcase | | p2-355s, p2-385s | | set | [dartboard](https://polyhaven.com/a/dartboard) (CC0); owned `BOOKCASE_01` | |
| KV7 | Checked curtains | Green/white gingham | p2-355s | per window | n | Procedural | |

## Buzz's room

Film: 500, 510, 518, 529 (`buzz-bedroom/`), 2350, 4450, 4500. Marina: 532-560 s. Boxes already in `spec/furniture.json`.

| # | Item | Film / Marina version | Seen in | Size | Qty | Best candidates | Fidelity note |
|---|---|---|---|---|---|---|---|
| B1 | **Twin bed** | Dark turned-post twin bed, green and white bedding | 2350 (film, partial), p2-556s (seen) | frame 1.19 x 2.05; headboard 1.10 H (measured, `spec/furniture.json`) | 1 | Owned `BED_01` narrowed to twin; [Iron Bed Royce](https://sketchfab.com/3d-models/9bcbb93e9818426f8c501a52be1af166) (no: metal) | Owned bed has the right turned posts; check its width scales cleanly. |
| B2 | Nightstand + lamp | | p2-556s (seen) | 0.66 x 0.40 x 0.65 (measured) | 1 | Owned **`BEDSIDE_CAB_01`** (0.53 x 0.44 x 0.64) | Good fit. |
| B3 | Tall chest of drawers | 2 columns x 5 drawers, honey wood | p2-550s (seen) | 0.84 x 0.44 x 1.27 (DEVIATIONS O5) | 1 | [Old Chest Of Drawers 1/2](https://sketchfab.com/3d-models/93b6cef3362c4e84ac6f12b6af11a8e1) (CC-BY, 1.6k); [Dressers and Chest Of Drawers](https://sketchfab.com/3d-models/7a80ff60fb574ef3a2971b3b7fd8e8c2) (CC-BY, 84k) | No exact 2 x 5 found. Procedural drawers are easy. |
| B4 | Desk, chair, pinboard | Cluttered student desk | 500, 529 (seen) | 1.41 x 0.60 x 0.75 (measured) | 1 | Owned `SM_Desk_01`, `SM_Chair_01` | |
| B5 | Wall shelves with trophies, helmets, game boxes | | 4500, 529 (seen) | 2.7 x 0.30 x 1.8 (measured) | 1 | Owned `SHELVES_01` / `WALL_SHELF_01` + props | |
| B6 | Terrarium (tarantula) | Glass tank on the lower shelf | 529 (seen) | ~0.6 x 0.3 x 0.3 | 1 | Procedural (glass box; exists in the old builder) | |
| B7 | Navajo zigzag rug | Black/white/grey zigzag | 4450 (seen) | ~1.5 x 2.4 | 1 | Texture on a plane | |
| B8 | Posters, Jordan cutout, BB gun, mini hoop | | 529, p2-556s | | set | Film-accurate: reuse the Jordan photo cutout, posters and logos (user Oct 17: hobby project) | Overridden Oct 17 |

## Parents' bedroom

Film: 1600, 2650, `parents-bedroom/part2-105s.jpg` (film still in the tour). Marina: p2-180s, 195s, 200s, 235s, 255s.

| # | Item | Film version | Seen in | Size | Qty | Best candidates | Fidelity note |
|---|---|---|---|---|---|---|---|
| P1 | **Four-poster rice bed** | Dark mahogany, tall carved/turned posts with finials, scrolled headboard, red bedding | 1600, 2650, p2-105s (film), p2-235s/255s (seen) | queen ~1.65 x 2.2 x 2.2 H (standard) | 1 | [Four-Poster Bed (AbCritch)](https://sketchfab.com/3d-models/four-poster-bed-221c20f44cc2472485a7a72156d9d055) (Sketchfab, licence not checked); [Four poster bed XYZ HW](https://sketchfab.com/3d-models/52f396e305a74a3bbaa6c0bb66a508f8) (CC-BY, 185k); [four posture bed 2](https://sketchfab.com/3d-models/714bba66830045ac98b2eedbc7948731) (CC-BY, 8k) | **No true rice-carved bed found** on any store. The bed dominates the room in the film: **model it** (turned posts are lathe work, easy procedurally), or buy a generic four-poster and swap the posts. |
| P2 | Dressing table + stool + lamp | Dark wood table, green-upholstered stool, green-shade lamp | p2-105s (film, seen) | ~1.1 x 0.5 x 0.76 | 1 | [Late 1800s French Vanity Desks](https://sketchfab.com/3d-models/b4193e4ae59b4756a9988d5ee1770a0e) (Mad_Lobster, CC-BY, 27k) | Good period piece. |
| P3 | Armoire | Tall dark armoire | p2-180s, p2-235s (Marina) | ~1.1 x 0.6 x 2.1 | 1 | [wardrobe antique](https://sketchfab.com/3d-models/b003c56eb67e487d93c7cdc83497a5ba) (CC-BY, 1.8k); owned `WARDROBE_01` | |
| P4 | Dress form | Cream dress form on a stand | p2-105s (film), p2-235s | ~1.6 H | 1 | [1900 dress form](https://sketchfab.com/3d-models/6353b94707ae4e799509364efb4480c1) (CC-BY, 18k); [Vintage Dress Form (PBR)](https://sketchfab.com/3d-models/a84e3425e3d74d56b10aa71750ca7d77) (CC-BY, 2.4k) | Good. |
| P5 | Folding screen | Dark painted oriental screen | p2-235s (Marina) | ~1.6 x 1.8 | 1 | [Mid Century Mahogany Folding Screen](https://sketchfab.com/3d-models/02d573740af34facac3bc3e6f5369bb4) (CC-BY, 73k); [chinese_screen_panels](https://polyhaven.com/a/chinese_screen_panels) (CC0) | Poly Haven's is the closer painted look. |
| P6 | Armchair, dark red | Dark wood, red seat | p2-180s | | 1 | [Victorian Chairs Pack](https://assetstore.unity.com/packages/3d/props/interior/victorian-chairs-pack-295359) | |
| P7 | Nightstands + green lamps | | p2-255s, p2-105s | 0.53 x 0.44 x 0.64 | 2 | [ClassicNightstand_01](https://polyhaven.com/a/ClassicNightstand_01) (CC0) or owned `BEDSIDE_CAB_01` | |
| P8 | Foot-of-bed bench | Floral upholstered | p2-255s (Marina) | ~1.2 x 0.45 | 1 | Recoloured F5 bench | |
| P9 | Luggage (packing scene) | Garment bags, suitcases | 1600, p2-105s (film) | | set | [vintage_suitcase](https://polyhaven.com/a/vintage_suitcase) (CC0); [Stylish Vintage Suitcases](https://sketchfab.com/3d-models/65bdcef112744e86832e22b7c7f69897) (CC-BY) | |
| P10 | Fireplace mantel, plant, framed pictures, oriental rug | White mantel | p2-195s, p2-200s | | set | Procedural mantel; Poly Haven frames | |

## Parents' bath (ensuite)

Film: 4400 (the aftershave scene; vanity and brass mirror, seen). Marina: p2-138s, 145s, 165s, 215s. Fixtures already have chosen sizes (`ensuite/README.md`: bath 1.16 x 1.24, vanity 0.62 x 2.08).

| # | Item | Version | Seen in | Size | Qty | Best candidates |
|---|---|---|---|---|---|---|
| E1 | Vanity with green marble top, brass taps, brass-framed mirror, bulb strip | | 4400, p2-138s (seen) | 0.62 x 2.08 (chosen) | 1 | **Procedural** (built-in) |
| E2 | Towels (layered green), toiletries | | 4400, p2-215s | | set | Procedural folded towels (nothing suitable found) |
| E3 | Botanical prints | | p2-215s | | 3 | Poly Haven frames + public-domain botanicals |

The hall bath, girls' rooms and sunroom: **not shown in any frame I inspected**, and the tour README says the film never established the girls' rooms or the sunroom. Not inventoried. Dress them from Marina only if the user wants them furnished.

## Upstairs hall

Film: 2296, 352, 1333, 10736, 3900, 1350, 1400 (`film-upstairs-hall/`).

| # | Item | Film version | Seen in | Size | Qty | Best candidates |
|---|---|---|---|---|---|---|
| H1 | Red poinsettias in gold foil on the floor | | 1333, 1350, 1400, 3900 (seen) | as F1 | 3-4 | F1 |
| H2 | Demilune / hall table with lamp | Dark wood | 2296, 10736 (seen) | ~0.9 x 0.4 x 0.75 | 1 | Owned `SIDE_TABLE_01` |
| H3 | Framed prints, oval brass ornaments | | `upstairs-film-quality-target.png`, 2296 | | set | Poly Haven frames |
| H4 | Brass wall sconces with shades | | 352, 1333 (seen) | | 3-4 | Same as F11 (model) |
| H5 | Plant urn (dark) | | `upstairs-film-quality-target.png` | | 1 | [ceramic_pot](https://polyhaven.com/a/ceramic_pot) (CC0) + F1 plant |

## Attic

Film: 1420 (Fuller's bed, railing; seen). Marina: Part 2 14:00-14:50 (not inspected this pass).

| # | Item | Version | Seen in | Size | Qty | Best candidates |
|---|---|---|---|---|---|---|
| A1 | Bed with patterned quilt, lamp | | 1420 (seen) | full/twin standard | 1-2 | Owned `BED_01`; [old_bed_frame](https://polyhaven.com/a/old_bed_frame) (CC0, iron) |
| A2 | Trunks, boxes, suitcases, toys | Clutter | 1420 (partial) | | many | [Antique Luggage - Steamer Trunks Type B](https://sketchfab.com/3d-models/21284fec9b0a4debae036ee309feac55) (CC-BY); [vintage_suitcase](https://polyhaven.com/a/vintage_suitcase) (CC0); procedural cardboard boxes |

## Basement

**Not inspected this pass.** The film's furnace (the "talking" octopus furnace) is iconic, but I did not find or view its frames in the sampled set, so I am not describing it. Free furnace models on Sketchfab are stylised or industrial ([Old Furnace](https://sketchfab.com/3d-models/7f607b4b0d514789b97270f83a6f4a93), 394 faces), and none is an octopus gravity furnace. **Recommendation: model it**, once its film frames are pulled. Washer, dryer and shelving are also unverified.

## Summary

- **Items inventoried:** 84 rows across 12 rooms, plus the basement furnace (unseen, no row). Some rows group sets: frames, mantel garniture, countertop props.
- **Good match (usable with at most a retint, rescale or logo strip):** about 47.
- **Partial match (right type, visible differences):** about 18. White poinsettias, bench, side and dining chairs, oval mirror, Christmas tree, wingback, green sofa, fire screen, china cabinet, sideboard, fridge, breakfast chandelier, microwave, bunk bed, reading chair, Buzz's chest, parents' armchair.
- **Needs modelling or procedural build (nothing decent found, or built-in):** about 19 (2 of them texture-only). Rice four-poster bed, piano lamp, brass sconces (foyer and hall), breakfast table, toy train, porcelain figurines, built-in den shelving, hutch, wall oven, window seats, vanity, towels, mantel, drapes and curtains, terrarium, rugs (texture only), and the furnace.

### Highest impact (most visible, best matches)

1. Foyer **poinsettias**: CGTrader Poinsettia Gift Plant ($5), retinted gold. Seen on every stair shot.
2. Dining **crystal chandelier**: Poly Haven `Chandelier_03` (CC0).
3. Living-room **upright piano**: Kimball Artist Console (CGTrader, ~$25). It also fixes the Marina grand-piano conflict in favour of the film.
4. Foyer **ficus tree**: CGTrader Indoor Decorative Ficus Tree ($10) with a brass pot.
5. Foyer **pedestal stands**: Poly Haven `side_table_tall_01` (CC0).
6. Breakfast **Windsor chairs** x8: Mad_Lobster_Workshop bow-backs (CC-BY).
7. Kitchen **pot rack and pots**: Sketchfab Hanging Pot Rack (CC-BY) + Poly Haven `pot_enamel_01` (CC0).
8. Den **CRT TV**: Poly Haven `television_02` (CC0).
9. Dining **china cabinet**: Poly Haven `vintage_cabinet_01` (CC0), dressed with glassware.
10. Parents' **dressing table** and **dress form**: Mad_Lobster French vanity + 1900 dress form (both CC-BY).

The Christmas tree and the Chippendale chairs are higher impact than several of these, but their candidates are weaker; they are the two pieces most worth a custom model or a careful paid pick.

### Licence red flags

- **Editorial licence**: CGTrader "Flower Euphorbia Pulcherrima" ($8.99) cannot be used in a game.
- **Non-commercial (CC-BY-NC / NC-SA)**: Sketchfab Old China Cabinet (IvanovichRU), La Parisienne Four Poster Bed, Banker's Lamp (ArthurBoni), CRT TV (oddviz), Christmas Poinsettia (globalmobisoft), Saloon Piano. Avoid them even for a free project, since the repo is public.
- **Share-alike (CC-BY-SA)**: Bar Stool (shuvalov.di), Wooden Stool (OVROO), Used Dartboard. Derivatives must carry the same licence.
- **Sketchfab "Free Standard"**: free to use, but it forbids redistributing the files, so do not commit them (Steinway K-52, Chinese Cabinet, Vintage Microwave by cacybernetic and others).
- **CGTrader "Royalty Free (no AI)", TurboSquid Standard, Asset Store EULA**: game use is fine, redistribution is not. Keep them gitignored like the current packs. All bought CGTrader items above carry "(no AI)": no use as AI training data.
- **Daz3D** (Predatron Poinsettias): game use needs a separate Interactive licence.
- **Trademarks** (overridden Oct 17, user: "forget those sourcing notes. this is just for me. it's totally fine, this is a hobby project for me."): film-accurate props, logos and posters are fine. Store-pack files still stay gitignored (their EULAs forbid redistribution) and CC-BY models still get a CREDITS.md line.
- **Possibly AI-made**: the Festive Poinsettia Pack's marketing image looks AI-assisted, and search results also surfaced Hyper3D/Rodin AI-generated chairs. Their licensing is unclear, so I left them out.
- **Committable**: only Poly Haven (CC0) outright. CC-BY items can be committed with an `ATTRIBUTION.md` entry.

### Method and gaps

- Frames: tour keyframes M01-M29, Part 2 room folders, the curated film folders and a 150-frame-stride sample of the 12,611 screencaps, all as contact sheets. Rooms with no matching frame are marked unseen above rather than guessed.
- Searches: Poly Haven API (full model list), the Sketchfab search API (downloadable, with licence and face count), CGTrader tag pages scraped with headless Chrome (all 20 poinsettia listings read; CloudFront rate-limited the later product pages, so some prices come from search snippets and are marked `~` or "not confirmed"), Unity Asset Store pages (descriptions are often empty, so pack contents are unverified), and web search for TurboSquid and Fab. Fab, BlenderKit, 3DSky, ambientCG and Free3D were only touched through web search. A second pass on Fab (Megascans furniture) and BlenderKit could improve the chairs, the tree and the bed.
- Owned packs were rendered in Blender to confirm what each mesh is. They are not shown in Unity.
