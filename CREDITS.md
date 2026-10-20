# Credits

Third-party assets used by the Unity build. The model files themselves are not in this repository (gitignored under
`unity/HomeAlone/Assets/Purchased/`); the scripts that adapt them are.

- "Worn Black Trunk" by tommccall41 (https://sketchfab.com/tommccall41), https://sketchfab.com/3d-models/cd4f656a7736481993234dbdfba48fd9,
  licensed CC Attribution (CC BY 4.0). Modified: split into body and lid, hollowed with a lining, brass rim added, rescaled
  (`tools/house/purchased_trunk.py`). Used as Buzz's footlocker.
- "Henry Lever-Action Rifle" by Zverev Kirill (https://sketchfab.com/Zverev), https://sketchfab.com/3d-models/henry-lever-action-rifle-98000c9642354a65b3203f76403128db, CC BY 4.0. Stand-in for Buzz's BB gun (recoloured/rescaled).
- "Baseball Glove" by m.lando (https://sketchfab.com/m.lando), https://sketchfab.com/3d-models/baseball-glove-f4652dd83c134e17a730e02a2cdd234e, CC BY 4.0.
- "Baseball Bat and Helmet" by MutualMole5181 (https://sketchfab.com/MutualMole5181), https://sketchfab.com/3d-models/baseball-bat-and-helmet-edcb11f8f1674cb18ded9a3589b47533, CC BY 4.0.
- "Golden Trophy" by Incg5764 (https://sketchfab.com/incg5764), https://sketchfab.com/3d-models/golden-trophy-79389eecca164e27a75d362fbbecfe3b, CC BY 4.0.
- "Framed Corkboard | Crafted by jerovdl" by Jerovdl (https://sketchfab.com/Jerovdl), https://sketchfab.com/3d-models/framed-corkboard-crafted-by-jerovdl-b8285b2078f04afe87abd1f1ead48a66, CC BY 4.0. Buzz's bulletin board.
- "Hershey's Chocolate Bar Unwrapped" by Anthony Yanez (https://sketchfab.com/paulyanez), https://sketchfab.com/3d-models/hersheys-chocolate-bar-unwrapped-32e0201d12be42b3b15557f2f576ea3e, CC BY 4.0.
- "Coffee Table (Astro)" by Domingos Studios (https://sketchfab.com/domingos), https://sketchfab.com/3d-models/coffee-table-astro-7dfe3fd68cbe4c45b58ea47697e69113, CC BY 4.0. The den's glass-top table (film 2850).
- "Persian Nain Carpet" by mfb64 (https://sketchfab.com/mfb64), https://sketchfab.com/3d-models/persian-nain-carpet-dc98944361654db191422c91e685371a,
  CC BY 4.0. Modified: fringe thinned to every 4th strand and decimated (628k to 32k triangles), a pile normal map derived from its
  photo, scaled non-uniformly to the measured box, matte (`tools/house/purchased_rugs.py`). The foyer's front rug.
- "Fine Persian Heriz Carpet" by mfb64 (https://sketchfab.com/mfb64), https://sketchfab.com/3d-models/fine-persian-heriz-carpet-e198f1099ac34274ae2c867226adde79,
  CC BY 4.0. Modified as the Nain (628k to 33k triangles), scaled to the measured box (`tools/house/purchased_rugs.py`). The living room's rug; its photo is also cut (borders, corners, medallion band, one scale) into the foyer floor runner, with its own fringe strands.
- "Mannequin (1900s): M size" by Aleksei Moskvin (https://sketchfab.com/alekseimoskvin1), https://sketchfab.com/3d-models/mannequin-1900s-m-size-edce03ca9ee8410b8e0485504597389b, CC BY 4.0. The parents' bedroom dress form (rescaled).
- "Sewing Machine" by Akram090 (https://sketchfab.com/Akram090), https://sketchfab.com/3d-models/sewing-machine-78c947841f4c4c27bf169b4e78ad189f, CC BY 4.0. The parents' bedroom treadle sewing table (rescaled).
- "Still Life of White Roses" (1870) by Henri Fantin-Latour, public domain (https://commons.wikimedia.org/wiki/File:Henri_Fantin-Latour_-_Still_Life_of_White_Roses_-_Google_Art_Project.jpg). The painting over the parents' mantel.
- Poly Haven "Standing Picture Frame 01/02" (CC0, https://polyhaven.com/models). The parents' mantel photo frames.
- "VR-ready PBR toilet" by Tobiesen (Unity Asset Store, bought/downloaded by the user, Oct 20 2026; Asset Store EULA, file gitignored under `unity/HomeAlone/Assets/Purchased/Toilet/`). Both bathrooms' toilets, maps downscaled to 2K and a mask map packed by `tools/house/purchased_toilet.py`.
- "Rusty Blow Torch" (CGTrader, free download by the user, Oct 18 2026; royalty-free licence, file gitignored). Kevin's blowtorch trap by the kitchen back door (film 10351-10363), re-exported to GLB with 2K maps.
- "Impact Sounds" by Kenney (https://kenney.nl/assets/impact-sounds), CC0 1.0 (no attribution required, credited anyway). Footsteps (`footstep_wood/carpet/concrete/snow`, plus `impactPlate_light` as `tile_*` and `impactPlank_medium` as `stair_*`) in `unity/HomeAlone/Assets/Audio/Footsteps/` for `FpsController` walking sounds. Licence copy beside them.
- Poly Haven textures "Bark Willow 02" and "Bark Brown 02" (CC0, https://polyhaven.com/textures). The generated bare winter trees (`tools/house/hifi_bare_trees.py`) and the treehouse trunk.
- Poly Haven "Fir Sapling" (https://polyhaven.com/a/fir_sapling), CC0. Decimated to 20% and scaled (`tools/house/hifi_ext_plants.py`). The two evergreens at the front corners (exterior polish, Oct 18).
- Poly Haven HDRIs "Horn-koppe Snow" by Grzegorz Wronkowski (https://polyhaven.com/a/horn-koppe_snow) and "Snowy Park 01" by Oleksiy Yakovlyev (https://polyhaven.com/a/snowy_park_01), CC0. Tonemapped JPGs as the window/backdrop dome (`tools/house/window_backdrop.py`): the clear-winter sky for the sunny/morning states (O, `HouseWeather`; "Snowy Cemetery" until Oct 19: its graves and an office tower showed on the horizon) and the overcast one.
- Poly Haven "Wooden Stool 01", "Brass Pan 01", "Pot Enamel 01", "Food Apple 01" (CC0, https://polyhaven.com/models). Recoloured to the film by `tools/house/kitchen_ph_props.py`: the kitchen's counter stools, pot-rack pans and fruit (Oct 19).
