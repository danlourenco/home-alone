# Home Alone — Gameplay Vision & Design Handoff

> The user's vision document (Oct 19 2026), kept verbatim as the source. The living design doc that builds on it (critiques,
> decisions, slice candidates, backlog) is [GDD.md](GDD.md).

**Status:** Early gameplay design exploration
**Engine:** Unity 6
**Development approach:** AI-assisted development using Claude, Codex, Blender, and Unity tooling
**Project type:** Personal hobby project / experimental game prototype

## 1. Purpose of This Document
This document captures a discussion about the gameplay direction for a Unity-based recreation of the McCallister house from *Home Alone* (1990).
The goal is to give Claude enough context to continue exploring gameplay design without revisiting foundational discussions or prematurely committing to specific implementations.
**Important:** This is not a finalized game design document. It distinguishes between ideas we've reached broad agreement on, promising concepts, and unresolved design questions.
The immediate objective is to establish a cohesive gameplay identity before investing heavily in gameplay mechanics.

## 2. Developer Background and Existing Project
### Developer experience
The developer is an experienced professional software engineer with a background primarily in full-stack TypeScript and front-end development. They are relatively new to: Unity and its editor; C# and Unity-specific programming patterns; 3D game development; game design principles and terminology; character controllers, AI behavior, and multiplayer networking; environment art and asset production.
They prefer learning by experimentation: build something, gain hands-on familiarity, then revisit first principles to understand the concepts and architecture. Explain unfamiliar game development concepts using software engineering analogies where helpful, but avoid overexplaining general programming fundamentals.

### Current project state
The developer has already recreated most of the McCallister house in Unity 6. This is **not a project starting from a blank scene**. Existing accomplishments include: reconstructed house architecture and interior floor plan; most major rooms, including Kevin's bedroom, Buzz's bedroom, the den, and upstairs spaces; exterior shell integrated with the reconstructed interior; several iconic props and traps, including the upstairs paint cans; functional first-person navigation with WASD and crouching; lighting that the developer is generally happy with; an established asset pipeline using Blender, Unity, external assets, and AI-generated geometry; a substantial movie-reference library containing screenshots captured at regular intervals; architectural reconstruction informed by floor plans, movie references, third-party models, and CGI walkthroughs; a custom visual feedback mechanism: pressing **M** during a walkthrough captures the current camera view and allows the developer to annotate what needs fixing. Claude or Codex can subsequently process that feedback.
The architectural reconstruction has followed a constraint-driven methodology, using evidence, shared walls, dimensions, and real-world construction principles rather than placing unrelated pieces of geometry. Most of the house is in good shape. The basement still needs substantial refinement.

### Current environment-art limitations
The biggest visual problem is **visual coherence**, rather than architectural accuracy or lighting. The environment mixes simple geometric placeholders; AI-generated Blender geometry of varying sophistication; higher-quality imported assets; assets sourced from Poly Haven, the Unity Asset Store, and other locations; custom architectural and decorative details. Some objects are geometrically plausible but aesthetically unconvincing. Others look good in isolation but don't match the movie. There are also occasional placement problems, particularly in rooms with limited photographic evidence.
The developer wants exploring the house to be rewarding independently of the actual game. The home itself should feel like an immersive, lovingly reconstructed tribute to the film.
**Design implication:** The house serves two purposes: an explorable cinematic environment and a gameplay sandbox. Neither objective should unnecessarily compromise the other.

## 3. High-Level Gameplay Vision
### The central concept
An asymmetric home-defense game in which Kevin McCallister protects his house against Harry and Marv through preparation, environmental manipulation, traps, stealth, and improvisation. The inspiration is a combination of:
- **Rainbow Six Siege:** attacker-versus-defender structure; timed preparation or fortification phase; environmental hazards and placed traps; tactical decisions involving entry points and defensive positioning; opportunities for attackers to identify and counter traps.
- **Splinter Cell — Spies vs. Mercs:** asymmetric abilities, information, mobility, and perspective; stealth-oriented gameplay for the physically weaker character; cat-and-mouse encounters; different movement opportunities and interactions with the same environment; potentially different camera perspectives for the opposing teams.
- **Hitman:** sandbox-style problem solving; multiple viable approaches to accomplishing objectives; interactive environments that reward observation and creativity; opportunities to arrange elaborate consequences rather than rely on conventional combat.
- **Home Alone:** the house is a character in its own right; preparation followed by escalating chaos; iconic traps and physical comedy; Kevin's resourcefulness compensating for his physical disadvantages; Harry and Marv becoming increasingly frustrated and reckless; players experiencing the joy of watching carefully laid plans pay off.

### Proposed design identity
**A tactical slapstick stealth game where preparation gives you an advantage, but improvisation determines whether you survive.**
Kevin should feel clever, resourceful, and vulnerable. Harry and Marv should feel physically imposing but susceptible to deception and environmental hazards. The outcome should emerge primarily from how players exploit the environment, not from conventional weapons or combat proficiency.

## 4. The Core Gameplay Loop
### Phase 1 — Preparation
Kevin has a limited period to prepare the home before the burglars arrive. Potential activities: place traps; activate existing environmental hazards; prepare escape routes; choose which entrances or routes to defend; move or configure useful objects; establish distractions or opportunities for misdirection.
A key design opportunity is **resource scarcity**. Kevin should not necessarily be able to prepare every possible trap during a single round. The player must choose where to invest preparation time and resources, making each defensive setup somewhat different. This is strongly inspired by Siege's preparation phase.
### Phase 2 — Intrusion
Harry and Marv attempt to enter the home and accomplish their objectives. The important conceptual decision is that **the burglars initially want to rob the house, not simply hunt Kevin**. They have an objective that progresses even when Kevin does nothing. This creates a reason for Kevin to engage with them. If Kevin simply hides under a bed throughout the match, the burglars can continue stealing valuables. He must actively disrupt them.
### Phase 3 — Escalation and Improvisation
Once the burglars encounter Kevin's traps and interference, their behavior begins changing. What began as a burglary evolves into an increasingly personal confrontation. Kevin must: move between rooms; avoid direct confrontation; lure burglars toward traps; trigger environmental hazards; create distractions; improvise when defensive plans fail; exploit his knowledge of the house. Harry and Marv may become increasingly focused on catching Kevin rather than completing the burglary. This creates a natural progression from tactical preparation to tense stealth and slapstick chaos.
### Phase 4 — Resolution
**Not yet determined.** Potential victory conditions include: preventing the burglars from stealing a required amount of property; delaying or disrupting them sufficiently; forcing them to abandon the burglary; escaping after meeting certain conditions; successfully obtaining help once the situation escalates. We discussed police arrival and escape as possible endings, but have not selected a final objective. Crucially, we rejected the idea that victory must require reducing Harry and Marv's health to zero. The game should not become a conventional deathmatch disguised as Home Alone.

## 5. Asymmetric Gameplay
One of the strongest ideas to emerge from the discussion was the parallel with *Splinter Cell: Pandora Tomorrow* and its Spies vs. Mercs multiplayer mode. The appeal of Spies vs. Mercs wasn't simply different weapons or player appearances. **Each side had fundamentally different capabilities and ways of experiencing the same environment.** We want to explore that principle here.
### Kevin — The Defender
Strengths: superior knowledge of the house; preparation opportunities; access to traps and distractions; ability to exploit tight spaces; stealth and evasion; environmental manipulation; potentially greater agility and mobility through certain areas.
Weaknesses: physically vulnerable; cannot reliably overpower the burglars; may have limited trap resources; can be caught if cornered or discovered.
Kevin's gameplay fantasy is about **outsmarting**, not overpowering.
### Harry and Marv — The Attackers
Strengths: physical strength; ability to force certain entrances or overcome obstacles; potentially greater reach and environmental disruption; advantages in direct confrontation; ability to investigate, detect, and potentially disable traps.
Weaknesses: unfamiliarity with the home's defensive setup; exposure to environmental hazards; reduced access to certain hiding places or traversal routes; susceptibility to distractions, deception, and frustration.
Harry and Marv should not merely be identical enemies with different character models. Their personalities could inform different behavioral parameters. For example, one might be more aggressive or impatient while the other is more cautious or susceptible to distractions. The exact behaviors remain to be designed.
### Environmental affordances
A useful concept from our discussion is **affordances**: the interactions that an object or environment makes possible. In an asymmetric game, an object may offer different affordances to different characters. Examples: Kevin can hide beneath a bed; a burglar may need to search it. Kevin can exploit a narrow route that the burglars cannot traverse. A burglar may be able to force open an entrance that Kevin cannot. Kevin can prepare a trap that a burglar must learn to recognize. This distinction should inform both environmental design and gameplay implementation. The house should not simply contain obstacles. Its architecture should enable asymmetric gameplay.

## 6. Stealth Mechanics
Stealth should be an important part of Kevin's toolkit, but not necessarily the primary victory condition. The design objective is to create a player who survives through observation, movement, deception, and planning. Potential mechanics: crouching; hiding under beds or behind furniture; using sightlines and cover; sound-based distractions; taunting burglars to lure them elsewhere; moving quietly through the house; breaking line of sight; escaping through alternate routes; using trap activations to create opportunities for repositioning.
### Important design principle
**Stealth enables Kevin to manipulate encounters; it should not encourage indefinite hiding.** A player who remains completely passive should risk losing because the burglary continues. This gives stealth a clear purpose within the broader game. Kevin hides to reposition, survive, or establish an advantage—not simply to avoid participating.

## 7. Traps and Environmental Interaction
Traps are one of the game's defining features. They should provide anticipation, surprise, physical comedy, and meaningful tactical consequences.
### Iconic movie-inspired examples
| Trap / object | Potential gameplay effect |
|---|---|
| Swinging paint cans | Knockback, temporary incapacitation, interruption |
| Icy exterior steps | Slipping, delays, loss of control |
| Basement stairs with tar and nail | Area hazard and movement disruption |
| Blowtorch door trap | Dramatic slapstick reaction and deterrence |
| Micro Machines | Slip or stumble hazard |
| Christmas ornaments beneath a window | Punishes careless entry or movement |
| Buzz's BB gun | Distraction, interruption, or taunting |
| Tarantula | Panic, distraction, temporary behavioral disruption |
| Treehouse zipline | Escape route with potential environmental interactions |

These are conceptual possibilities, not approved mechanical specifications.
### Traps should do more than damage
The discussion converged on a preference for **disruption over damage**. A trap might: knock a burglar down; delay movement; interrupt an interaction; cause temporary disorientation; redirect the burglar's attention; produce noise; create an escape opportunity; increase frustration or aggression; trigger a comedic animation. This preserves the slapstick nature of Home Alone. A successful trap should feel rewarding even if nobody is eliminated.
### Counterplay
Borrowing from Rainbow Six Siege, burglars should have some ability to detect and avoid traps. Examples: a careful player notices a suspicious object; an attacker recognizes a prepared doorway; a burglar investigates before crossing a hazardous area; some traps can be bypassed or disabled. The exact detection and disarming mechanics are unresolved. This becomes particularly important in multiplayer, where human opponents will not deliberately make the mistakes of the movie characters.
### Fixed traps versus improvisation
We discussed two approaches: (1) faithful recreations of iconic movie traps; (2) sandbox-like freedom to devise alternative solutions. The preferred direction is a **blend**, at least conceptually. The game could provide predefined interaction opportunities in recognizable locations while allowing alternative preparations or strategies. For instance, a staircase could support more than one defensive approach. We do not necessarily need a fully freeform trap-construction system. A smaller collection of well-designed interactions may create more interesting decisions with substantially less implementation complexity.

## 8. The Comedic Payoff
An important realization was that the traps are not merely gameplay mechanics. **The payoff of a trap is the reaction.** A swinging paint can is only an interesting physics event until the game communicates its effect through: character animation; sound; timing; camera movement; physical reactions; environmental consequences; character personality. This falls under the game development concept of **game feel**.
### The camera problem
When Kevin activates a trap from another room, the most entertaining moment may happen outside the player's view. We discussed a possible cinematic reaction camera or kill-cam-style replay. However, automatically interrupting gameplay could be frustrating, especially during stealth. Potential solutions worth exploring: optional short reaction replays; contextual cinematic cameras; delayed replay functionality; strong audio and character reactions audible from elsewhere in the house; other ways to communicate trap success without taking control away from the player. No solution has been selected. This is an important design question because the game needs to balance the satisfaction of slapstick reactions against the continuity of active gameplay.

## 9. Camera Perspectives
We discussed first-person versus third-person gameplay at length.
**First-person** advantages: strong immersion in the reconstructed house; heightened tension when searching for hazards; more deliberate environmental observation; fits the burglar perspective well; makes walking through the home feel like personally inhabiting the movie environment.
**Third-person** advantages: better visibility around the player character; stronger communication of crouching, hiding, and physical movement; greater visibility of Kevin's personality and animations; familiarity with classic Splinter Cell-style stealth; better awareness of the character's relationship to nearby objects.
### Promising direction: asymmetric perspectives
One possibility is **Kevin: third-person; Harry and Marv: first-person.** This follows the spirit of Spies vs. Mercs. The different cameras could reinforce asymmetric mechanics rather than serve as arbitrary presentation choices. For example, Kevin's third-person perspective emphasizes stealth, agility, and spatial awareness. The burglars' first-person perspective emphasizes searching, navigating unfamiliar territory, and detecting traps.
**Status:** Promising concept, not a final decision. We should experiment before committing.

## 10. AI Behavior and Escalation
One of the strongest emerging design ideas is a shift in the burglars' motivation during a match.
### Initial motivation: Burglary
Harry and Marv enter with the objective of stealing valuables. They may explore rooms, search for objects, and attempt to overcome obstacles. Kevin must interrupt their progress.
### Escalating motivation: Revenge
As Kevin successfully interferes with the burglars, their behavior changes. They may: become more impatient; investigate Kevin's whereabouts more aggressively; abandon some burglary objectives; focus increasingly on capturing him; behave more recklessly; make mistakes as a result of frustration. This progression is inspired by the movie.
### Pacing versus reactivity
We discussed a distinction between **pacing** (the game's need to progress toward increasing tension) and **reactivity** (the burglars responding to what Kevin actually does). A hybrid approach appears promising. Kevin's behavior should be the principal driver of the burglars' changing priorities, but the game also needs mechanisms that prevent the situation from stagnating.
### Separate behavioral state from motivation
A useful implementation principle is distinguishing between: what a burglar is currently doing; what that burglar is trying to achieve; how aggressive, suspicious, or frustrated the burglar has become. These are related but should not necessarily be represented as a single state. The underlying behaviors could be shared between Harry and Marv, with character-specific parameters influencing their decisions.
### Believable stupidity
The burglars must be intelligent enough to create tactical tension without becoming so competent that the comedy disappears. A key design principle: **The game should reward the player's cleverness, not punish them for successfully exploiting an intended trap.** Their foolishness should be legible and entertaining, while still allowing counterplay. We have not chosen an AI implementation approach, such as behavior trees, finite-state machines, utility AI, or a hybrid.

## 11. Multiplayer Direction
The developer ultimately wants to explore human-controlled burglars. The inspiration is again Spies vs. Mercs, where players experience genuinely different roles. However, multiplayer is not a requirement for the first playable prototype.
### Proposed progression
Start with AI-controlled Harry and Marv to validate the gameplay fundamentals. Once the core mechanics are enjoyable, explore player-controlled burglars.
### Architectural consideration
Ideally, gameplay rules should be separated from the source of character input. For example: an actor has movement and interaction capabilities; a controller supplies intentions or commands; that controller might eventually be human or AI; game systems govern valid interactions and outcomes. This resembles separation of concerns in conventional software development. However, **being controller-agnostic is not the same thing as being network-ready**. Networking introduces authoritative state, replication, timing, physics synchronization, and other requirements. The goal is to avoid unnecessary coupling without prematurely implementing a complete multiplayer architecture.
### Multiplayer design challenge
Human-controlled attackers are less likely to fall for scripted tricks. Therefore, Kevin's abilities and traps must provide real tactical advantages rather than rely on opponents deliberately behaving foolishly. This reinforces the need for: environmental asymmetry; stealth; limited information; meaningful attacker counterplay; strategic trap placement; incentives that keep attackers moving and pursuing objectives.

## 12. Relationship Between Environment and Gameplay
The developer's work on the house is an intentional part of the project's creative goal. The reconstruction itself is valuable. We should avoid treating visual refinement as wasted effort simply because the gameplay is not yet fully implemented. At the same time, there are distinct disciplines involved: **environment modeling** (geometry, dimensions, spatial accuracy, construction); **environment art** (materials, assets, decorative detail, visual coherence, authenticity); **gameplay development** (interactions, character capabilities, objectives, AI, rules, and feedback). These disciplines overlap but solve different problems.
### Art pipeline recommendations from our discussion
The developer already has an AI-assisted art pipeline. There is no need to invent an elaborate replacement without first examining the existing implementation. The main opportunities appear to be: improving the quality of placeholder replacements; prioritizing proportions, recognizable silhouette, and materials rather than simply increasing geometric detail; ensuring assets match movie references; verifying object placement in the Unity scene; using consistent camera viewpoints for before-and-after review; establishing one representative room as a visual quality benchmark. The developer remains the final visual reviewer. Automation should support that judgment rather than attempt to replace it.

## 13. Design Principles We've Converged On
1. **The house is the sandbox.** Its architecture should meaningfully shape the gameplay.
2. **Kevin wins through cleverness.** Preparation, stealth, misdirection, and environmental manipulation should be more useful than direct combat.
3. **The burglars have real objectives.** They are there to rob the house. Kevin must disrupt them, not simply wait for a timer to expire.
4. **The burglars' motivations evolve.** The initial burglary can escalate toward a personal pursuit of Kevin.
5. **Traps are about memorable consequences.** Animations, reactions, comedic timing, and disruption matter at least as much as numerical damage.
6. **Stealth serves a purpose.** Hiding and evasion should help Kevin accomplish his objectives, rather than become a passive strategy.
7. **Asymmetry is central.** Kevin and the burglars should experience the same environment through different capabilities, information, and possibly camera perspectives.
8. **Player choice should matter.** There should be meaningful decisions in preparation, trap placement, movement, and improvisation.
9. **Preserve the spirit of Home Alone.** The game's emotional character should mix childhood ingenuity, tension, escalating chaos, and physical comedy.
10. **Prototype before committing to complexity.** Validate compelling gameplay before investing heavily in sophisticated AI, networking, or large-scale content systems.

## 14. Questions Still to Resolve
These are open questions, not missing requirements that should automatically be filled with assumptions.
- **Victory conditions:** What does it mean for Kevin to win? What exactly are Harry and Marv trying to steal? How does the game end? Is police involvement part of the resolution?
- **Match structure:** How long should preparation last? Are matches timed? Can Kevin continue placing traps after the burglars enter? What creates pressure without feeling artificially restrictive?
- **Escalation:** How do the burglars transition from burglary to hunting Kevin? How much of this is driven by player actions versus match progression? Can their behavior de-escalate?
- **Trap systems:** How much trap placement freedom should players have? Which traps are location-specific? What resources constrain preparation? Can burglars disarm or repurpose traps? How should the game communicate trap effects?
- **Stealth:** How sophisticated should vision and sound detection be? What hiding and traversal mechanics are most important? What makes stealth fun rather than tedious?
- **Camera:** Should Kevin be third-person? Should burglars be first-person? How should trap reactions be presented? Would different camera perspectives introduce balance concerns?
- **AI and multiplayer:** Which behaviors are necessary for an enjoyable single-player prototype? How should the architecture support future human-controlled attackers? Which mechanics depend too heavily on scripted character stupidity?
- **Environment:** Which rooms and interactions make the strongest prototype? How much environment-art refinement is necessary before testing gameplay? How can the existing visual feedback pipeline assist gameplay development?

## 15. Suggested Next Step: Gameplay Design Before Implementation
The recommendation is to establish a small but coherent **vertical slice** of the intended experience. A vertical slice should validate the interaction between several essential systems, not merely demonstrate each system independently. It should answer a question such as: *Is it fun to prepare a trap, manipulate an intruder into encountering it, experience the resulting reaction, and use the resulting disruption to accomplish an objective?*
The slice should ideally demonstrate: a meaningful defender objective; a meaningful attacker objective; at least one preparation choice; a usable trap; a method for luring or distracting an attacker; a stealth or evasion opportunity; a convincing reaction to the trap; a clear result for the encounter.
The exact room, trap, and scenario should be chosen after inspecting the existing Unity project. **Do not assume that the den or any other particular room is the correct starting point.** The entire house largely exists already, and its current assets and interactions should inform the choice.
### Development philosophy
Prefer a tracer-bullet approach: (1) implement a narrow end-to-end gameplay scenario; (2) verify it in the running game; (3) evaluate whether it is enjoyable; (4) refine the architecture or mechanics based on evidence; (5) expand only after establishing that the preceding slice works. Avoid creating a large speculative gameplay framework before testing the underlying experience.

## 16. Guidance for Claude
When continuing this discussion or working in the Unity repository:
1. **Inspect before prescribing.** Do not assume what systems, models, assets, or tools already exist.
2. **Distinguish confirmed decisions from suggestions.** Many design questions remain intentionally open.
3. **Do not jump straight into implementation.** The current priority is understanding and refining the intended gameplay experience.
4. **Challenge ideas constructively.** The developer specifically wants help identifying ideas that make the experience less cohesive.
5. **Respect the existing environment.** The house reconstruction has already received significant attention and effort.
6. **Favor game design coherence over feature accumulation.** A smaller collection of mutually reinforcing mechanics is preferable to a large collection of disconnected mechanics.
7. **Explain game development principles.** The developer is experienced in software engineering but wants to understand the underlying concepts of game development.
8. **Avoid speculative rewrites.** The current art, verification, and development pipelines may already solve problems that would otherwise be reinvented.
9. **Keep multiplayer in mind without prematurely building it.**
10. **Preserve the movie's personality.** Tension, improvisation, traps, and comedic consequences are fundamental to this concept.

### Intellectual property consideration
This is currently a personal hobby project based directly on *Home Alone*, with recognizable locations, characters, and film-specific elements. The developer understands that distributing or commercializing such a game could present intellectual-property issues. The underlying gameplay concept could potentially be adapted into an original game with new characters, environments, and creative expression. There is no immediate requirement to strip away the Home Alone identity from the current prototype.

## 17. Final Creative Direction
The strongest gameplay direction to emerge is not a traditional first-person shooter, a pure stealth game, or a conventional tower-defense game. It is a blend of: **Siege-style preparation**; **Spies vs. Mercs-style asymmetry**; **Hitman-style environmental problem solving**; **Splinter Cell-style stealth and evasion**; **Home Alone-style physical comedy and escalating chaos**.
The essential player fantasy is this: *You've spent your preparation time turning an ordinary home into a carefully planned defensive playground. Two burglars enter expecting an easy robbery. You know every hiding spot, every shortcut, and every trap. But they have objectives of their own, and your plans don't always survive contact with reality. You need to think quickly, stay out of reach, and turn their growing frustration against them.*
**The goal is not simply to survive the burglars. It's to outsmart them—and have a ridiculous amount of fun watching the consequences.**
