# Gameplay ideas (parked until the house is faithful and walkable)

The user's ideas for the game, kept here so they survive sessions. None is scheduled; the house comes first (Sept 11 decision).
Add new ones at the bottom with the date and the user's words.

- **Stealth and lure, not a shooter** (Oct 17). Kevin hides (under beds, in gaps adults can't fit), makes noise or switches
  lamps to lure Harry and Marv into traps, and springs them at the right moment. Needs bandit AI (patrol, hear, search, chase;
  Unity AI Navigation), a sight cone against light/shadow, noise from running/stairs, lures (noise, lamp, the gangster tape,
  doors), more film traps (doorknob, ornaments, tar, iron). First- vs third-person (or both) undecided. Suggested first test: one
  bandit with a patrol and sight cone on the accepted downstairs.
- **Ornament trap at the living-room window** (Oct 17): Marv climbs in the den-side rear window and steps on ornaments (film
  10590-10620). Keep the floor in front of that window clear (STATUS 8a moves the tree off it).
- **Prep-phase music** (Oct 17): "Setting the Trap" plays while Kevin sets traps. Done as a hook: Assets/StreamingAssets/
  LocalMedia/music_prep.mp3 (gitignored) and `BackgroundMusic.Phase("prep")` / `Phase("")` for the main title
  (Scripts/BackgroundMusic.cs; U cycles tracks for listening until phases exist).
- **Sit and watch TV, GTA V style** (Oct 17): "when you approach the tv in the den, you can choose to sit down to watch tv, and
  then it switches to a view closer to the tv so you can watch what's on in the den until you decide to 'get up'." Sketch: an
  interaction prompt near the den sofa/armchair facing the TV (Scripts/DenTV.cs plays the user's clip), the camera blends to a
  seated view framed on the screen, movement locked, the TV's sound un-muffled; "get up" blends back to the player.
- **Web build** (Oct 17, question): Unity web needs URP (HDRP has no web target); three.js could load the generated GLBs and
  spec JSON with baked lighting. Decide before gameplay code; licences of bought assets and the film IP matter more than the
  engine.
