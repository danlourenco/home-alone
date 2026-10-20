# Game Design Doc (living, Oct 19 2026)

The source of truth for the gameplay vision is the user's document, [GAMEPLAY-VISION.md](GAMEPLAY-VISION.md) (verbatim). This
file builds on it: Claude's critique, the ideas the user has since agreed with, slice candidates, the decisions still needed,
and everything else still open. **Nothing here is final until the user signs it off.** Current build state: [RESUME.md](RESUME.md).

**Identity (from the vision):** a tactical slapstick stealth game where preparation gives you an advantage, but improvisation
determines whether you survive. Kevin wins by outsmarting, not overpowering.

## 1. Agreed since the vision (user, Oct 19)
- **Single player vs AI first.** Multiplayer stays a later mode; it does not constrain today's designs (vision §11 progression).
- **Misdirection as a mechanic family: "poisoning the burglars' beliefs."** The user likes the **cardboard party** and the
  **gangster tape** as misdirection, especially against AI.
  - Each burglar acts on a small **belief model**, not the truth: is anyone home? are adults here? where is the kid? what was
    that noise? (In software terms the AI works from a local cache of the world; misdirection poisons the cache.)
  - **Cardboard party** (mannequins, the cutout on the train, music): SIGHT from outside -> "the house is full of adults" ->
    delay, abort an approach, or switch entry point (entry denial without a trap). Prep cost: gather and set it up. Decays: each
    viewing raises suspicion; a close look breaks it for good and spikes frustration ("being fooled is humiliating").
  - **Gangster tape** ("Keep the change, ya filthy animal"): SOUND -> "an armed adult behind that door" -> panic, freeze, flee:
    time, or herding into a trap. Timing is the skill. Spent once heard twice or once the VCR is seen; frustration jumps.
  - **Architecture consequence:** the burglars must PERCEIVE (sight and sound stimuli tagged with meaning), never cheat with
    omniscience. One perception system then serves stealth (seen/heard), lures (noise), traps (startle) and misdirection.

## 2. Critique of the vision (Claude, for the user to accept or reject)
1. **Five reference games risk a diffuse identity.** Siege (outplay a human) and Hitman (solve a predictable system) pull
   opposite ways. Proposal: one primary verb, **"set it up, lure them in, watch it pay off"** (Hitman's observe-and-engineer +
   Home Alone's payoff). Prep and stealth feed that verb; Siege contributes the STRUCTURE (prep, then raid), not PvP skill play.
2. **Single-player comedy vs multiplayer fairness conflict.** Humans will check every doorknob; caution kills slapstick. Design
   for AI; keep the controller/actor split so multiplayer stays possible; don't shape traps around human counterplay yet.
3. **Stealth needs information design.** Kevin must know where they are and what they're taking. 1990 sources: sound carried
   through the house, glimpses from windows / the stair gallery / the treehouse, and the misdirection tools themselves.
4. **Escalation needs a player-side cost.** One "heat" (frustration) value per burglar: more heat = more reckless (more
   trap-prone) AND more dangerous (faster, searches harder, chases longer). Provoking them becomes a real decision.
5. **A victory candidate that ties the loop together:** Kevin must reach the phone and call the police (a risky trip), then keep
   the burglars in the house until help arrives, while keeping stolen value under a threshold. Combines the loot objective,
   the reason to engage, escalation and an ending (the film's own shape). One option; vision §14 keeps it open.
6. **Trap sockets + scavenger prep.** Fixed sockets at the film's trap locations, each with 2-3 valid setups (like Siege's
   reinforceable walls): far cheaper than freeform placement and faithful to the house. Kevin must FETCH trap items (paint cans
   from the basement, ornaments from the tree, the tarantula from Buzz's room): prep rewards knowing the house, so the faithful
   environment becomes gameplay.
7. **The hidden cost is animation.** Slapstick payoff = burglar reaction animations (slips, falls, hits, recovery); a
   third-person Kevin = a rigged, animated kid (crouch, crawl, hide). Mitigate: physics ragdoll + a few canned clips (Mixamo);
   prototype Kevin in first person (exists, sells the house); try a third-person camera on a mannequin before committing.
8. **Off-screen trap payoff: "hear it, then you may look."** A scream and crash carry through the house; a small picture-in-
   picture of the trap is OFFERED, never forced. Keeps control with the player and doubles as information.
9. **Pace tension and release.** Stealth builds tension; the trap releases it. Judge the slice on that rhythm, not only on "did
   the trap fire".

## 3. What exists to build a slice on (inspected Oct 19)
- Scripts: PaintCanTrap (gallery-rail drop down flight 1), TankTarantula / TerrariumTarantula, ZipLine (attic to treehouse),
  EntranceDoor (front + kitchen back door: E opens, `locked` flag), SwingDoor, TrunkLid, DenSeat + DenTV (a seated camera
  precedent), HouseNightMode (N), HouseWeather (O), FpsController (kid/adult bodies, crouch/crawl, kid-scale hiding works).
- The blowtorch at the back door (prop), the film's walk-tested entry routes (Marv to the basement door, the back door, the
  front walk), fall recovery, day/night lighting.
- Missing: AI (perception, beliefs, navigation), objectives/loot, inventory/carry, trap sockets, reactions/animation, UI.

## 4. Vertical slice candidates (to choose; vision §15 criteria)
- **A. "Casing the house" (misdirection-first).** Night 1, one AI burglar outside choosing an entry. Kevin sets the cardboard
  party and cues the gangster tape. Tests perception, beliefs, timing and payoff end to end with no trap physics and few
  reaction animations. Weakest on "a usable trap".
- **B. "The back door" (trap-first).** One burglar entering by the kitchen back door: the blowtorch socket (or the icy steps),
  the basement stairs as a second route, a loot target in the kitchen, Kevin luring with noise and hiding. Strongest comedy
  test; needs a reaction animation.
- **C. "Battle plan" (both).** A short prep phase (fetch 2 items, arm 1 of 2 sockets) then one burglar with a loot goal on the
  ground floor + basement; the gangster tape as the lure. The fullest slice; the largest.
- Recommendation: **C, built as A then B** (each a tracer bullet): misdirection + perception first, then one trap with a reaction.

## 5. Decisions needed before code
1. Sign off the identity, the vision's §13 principles and §2 critiques (accept/reject each).
2. The victory condition for the slice (the phone + police candidate, or another).
3. First person for the slice? (Recommended: yes; third person tested later on a mannequin.)
4. Trap sockets vs freeform placement for the slice (recommended: sockets).
5. Slice A, B or C (recommended: C as A then B).
6. What the burglars steal in the slice (a few film-plausible valuables, e.g. in the dining room / living room).

## 6. Platform and tech
Unity 6000.6.0f1, HDRP, Mac first (a local Mac test app is authorized: RESUME queue). Performance target the user's M3 Pro,
measured standalone. HDRP has no web target. AI: Unity AI Navigation for movement; the decision layer (state machine, utility,
behaviour tree or hybrid) is open (vision §10), chosen in the slice. Multiplayer later: Netcode for GameObjects is the likely
route, not now. Licences: a personal hobby project; purchased assets and the film IP limit distribution.

## 7. Everything else still open (Oct 19)
- **House must-haves before calling the environment:** the upstairs hall bathroom (missing); the parents' ensuite (asked Oct 18);
  the kitchen remainder (island small props read as simple shapes; stools a bit pale; the white goose decoy, a purchase; the
  film's pine pigeonhole desk; a poinsettia on the seat counter's end). The pine stack and the breakfast hutch are sized from
  IMG_4305 (TRIAL, changes/2026-10-19-kitchen-cupboard-hutch.json), awaiting the walk.
- **Walk defects:** hall runner jogs / possible corridor misalignment (job prepared, parked); arch B "awkward"; exterior wallpaper
  on the front door jamb; jerky door swing; stoop/step overlap; noisy porch shadows; coarse/dry walk material; a protruding
  gutter/trim; flat interior doors; street-lamp style; a tree in the driveway; garage fence placement; the den shelf lamp too
  bright; stray steps at the front-right yard; daylight through a basement gap; the kitchen casing vs the soffit; the
  banker-only lamp comparison needs a decision. The basement needs substantial refinement (vision §2).
- **In progress by Codex:** the stair/soffit (done, accepted); nutcrackers in the living room.
- **Queued:** the Mac test app; the texture job (garage, terrace, basement metal); the breakfast-area measurement; the
  neighbourhood plan (step 1 done); PNG renders to JPG; film 2850's glass table beside the den chair; the picket fence; the
  always-failing Buzz-floor check; duplicate Unity project names; ~38 older TRIAL records to batch-accept.
- **Visual coherence (vision §2, §12):** pick one benchmark room at final quality and hold every other room to it.
- **Process:** GitHub issues as the backlog after sign-off (labels env / gameplay / tech / bug; milestones environment-done,
  slice, alpha, beta; each issue with a playable acceptance check); walk notes -> draft issues by a script; cadence build ->
  playtest -> triage -> fix; done = gates pass + the user's playtest says yes.
