# Source weights and calibration rules

September 13, 2026. These are **project decision weights**, not probabilities of truth, statistical confidence or percentages to average. Scale: 5 primary, 4 strong, 3 supporting, 2 tentative, 1 weak, 0 not evidence for that question. Weights can change when provenance/calibration improves; record why.

## Target and constraints

The target is the first film's recognizable interiors in one believable playable house. User-approved compromises (nonconnecting breakfast stair, closed linen closet, deferred basement fidelity) are requirements, not evidence weights. Keep Home Alone 2, production sets, the real property at other dates, and reconstructions separately identified. A physically connected solution must respect those requirements; the source with the highest weight does not erase a user decision.

## Evidence matrix

Production interview clarification: Part1 introduces John Muto at4:09–4:14, followed at4:16–4:27 by his account of building/distorting the staircase on stage for the sled exit ([archived transcript](../reconciliation/transcript.txt)). Treat the named production participant's account as weight5 for that production-history claim, **not** as Marina CG geometry or as a stated measurement. Automatic captions limit exact wording. This contradicts adopting “foyer/landing—Real” as an unquestioned scale premise. See the [candidate review](../foyer-calibration/fit/REVIEW.md) for corroborating interview and checklist corrections.

| Source | Visible interior appearance | Visible room connections | Absolute film dimensions | Application / citation |
|---|---:|---:|---:|---|
| Identified first-film frame / continuous scene | 5 | 5 for connections actually visible; 0 for unseen arrival | 1 uncalibrated; up to 4 with independently established scale and camera solution | [Foyer film frame](../reconciliation/first-floor-user-shots/12-movie-foyer.png), [upper hall target](../foyer-film/upstairs-film-quality-target.png). Perspective and cuts prevent treating pixel distance or sequential shots as one physical measurement |
| Attributed production photograph of the relevant set | 4 | 4 for visible structure | 1 uncalibrated; higher only with a documented scale | [Production-photo reference page](https://www.mockingbirdlane.design/post/home-alone-in-depth). This is an index to previously archived evidence, not a declaration that every image on the page is verified. Identify individual photo/set before use; final-film view wins for final appearance |
| Marina's CG tour reconstruction | 4 where film corroborates; 3 otherwise | 3 | 1 for image-derived metres; 3 for explicit stated measurements with identified scope | [Part 2](https://www.youtube.com/watch?v=kU7aY1anpAI), [archived room references](../buzz-bedroom/README.md), [main transcript](../reconciliation/transcript.txt), [measurement ledger](../reconciliation/README.md). Film stills embedded in her video retain their film-source class; they are not additional independent votes |
| Eric's visitor floor plans published by Hooked on Houses | 1 for decor | 3 for depicted real-house arrangement; 2 for film-only connections | 2 for readable labels as film targets | [Publisher and provenance](https://hookedonhouses.net/2009/11/30/inside-the-real-home-alone-house/), [first-floor image](https://hookedonhouses.net/wp-content/uploads/2009/11/Home-Alone-house-floor-plan-first-floor-2.jpg), [upstairs image](https://hookedonhouses.net/wp-content/uploads/2009/11/Home-Alone-house-floor-plan-upstairs1.jpg). Publisher identifies Eric as a visitor who worked out plans after visiting, not an architectural surveyor supplying production drawings |
| User-supplied illustrated 11×17 PDF | 2 for schematic furnishing placement | 2 | 0 for absolute metres; 1 for relative proportions | [Archived PDF](illustrated-first-floor.pdf). No scale bar, dimension labels or established authorship; print size is not house scale |
| HOME_ALONE_FINAL GLB | 2 as an artistic reference; never overrides clear film evidence | 2 as a candidate connected house | 1 as film evidence | [Adopted source asset](../../../../unity/HomeAlone/Assets/ThirdParty/HomeAloneExterior/HomeAloneExterior.glb). Provenance of measurements unknown; its cohesion is why it is the working base, not proof of scale |
| Current Unity measurements / walking tests | 0 as historical evidence | 5 for **tested current-model** connections, 0 for untested routes | 5 for **sampled current-model** dimensions, 0 for film dimensions | [Baseline and method](README.md), [traversal audit](../structure-audit/README.md). Collider samples require boundary checks; movement success cannot establish film accuracy |
| Earlier generated Godot/Unity layouts | 1 unless directly traced to evidence | 1 | 0 for authored dimensions | [Historical reconciliation](../reconciliation/README.md). Reuse useful implementation, not invented dimensions or repeated historical summaries |

Real-house photographs are strong evidence for the property at their documented date, but not automatically for the film-set interior. For exterior appearance they can receive 4–5 when date/view is relevant; for film-room dimensions they remain low without demonstrated correspondence. User observations are useful leads; attached film images get the image's evidence class, while recollections remain provisional until corroborated.

## Provenance update affecting Stage 1

The publisher was rechecked on September 13. It says Eric photographed the real property in 2004 and worked out the accompanying floor plans after visiting. The floor-plan pair is therefore a **visitor reconstruction of the real house**, not a verified movie-set survey. This supersedes the baseline's earlier “authorship not established here” status. Survey method and dimensional accuracy remain undocumented.

Consequently, the +8%, +30% and +35% comparisons in the baseline describe differences from Eric's stated dimensions. They **do not establish that our movie house must shrink by those amounts**. The foyer-width-ratio conflict merits a film comparison, not immediate remodeling to the plan.

## Claim-level ledger

Source weight and claim confidence are recorded separately. “High” below means confidence in the stated observation, not in a broader inference.

| Claim | Supporting source / weight | Confidence and limits | Current decision |
|---|---|---|---|
| Living/dining labels say 15 ft | [First-floor screenshot](dimensioned-first-floor.png), Eric plan / 2 as film target | High transcription confidence; low-to-medium applicability to film-set dimensions | Use as comparison candidate, not adopted target |
| Side-wing labels say 12 ft | Same / 2 | High transcription confidence; film applicability unverified | Defer wing resizing |
| Current living/dining upper wall width is about 4.938 m | [Live baseline](README.md) / 5 for current model | High at sampled wall locations; trim changes dining clear width to4.891 m | Freeze as measured current baseline |
| Current foyer is wider than adjacent main rooms; the plan depicts the reverse | Live baseline + Eric plan / 5 current, 2 target | High model ratio; medium qualitative drawing comparison; unknown film target | Prioritize matched-film comparison, no automatic shrink |
| Main stair has a rear landing/window and return to upper gallery | [Film foyer](../reconciliation/first-floor-user-shots/12-movie-foyer.png), [upper target](../foyer-film/upstairs-film-quality-target.png), Marina views / 5 visible film, 3 reconstruction | Strong arrangement evidence; not a complete metric survey | Preserve this topology |
| Two dining/breakfast openings | [User-supplied Marina overhead](../reconciliation/first-floor-user-shots/06-ground-overhead.png), Eric plan, illustrated PDF / 3,2,2 | Medium-to-high relationship confidence; sources may be dependent. Current traversal verifies implementation | Retain both openings |
| Working kitchen is stated to be477 ft² | [Archived transcript/frame ledger](../reconciliation/README.md), Part1 13:17–13:24 / 3 | High that the archived reference states it; perimeter definition and independent measurement unverified | Treat as area claim, not a scale factor for the whole floor or proof of room aspect ratio |
| Buzz side passage is0.58 m in model | [Live bounds](../structure-audit/README.md) / 5 current | High projected-bounds calculation; not exact curved-surface minimum or film measurement | Investigate width/depth/placement, not arbitrary mattress shortening |
| Buzz window replacement sills differ only≈2 mm | [Builder](../../../../unity/HomeAlone/Assets/Editor/FrontWindows.cs), live checks / 5 current | High for replacement geometry; says nothing about original casing appearance or correct film sill height | Compare entire room window assemblies against references |
| Basement must be2.85–3.14 m high | Only current-model samples / 0 as film target | Unsupported as a film claim | Do not adopt; defer fidelity review |

## How weights guide an actual change

1. State the exact claim and identify its subject: film set, real property/date, reconstruction or current model. Attach a frame/time, drawing label or measurement method.
2. Use the highest-weight evidence applicable to that claim. A low-weight numeric claim does not beat a high-weight visible relationship simply because it has a number.
3. Count dependent sources once. A screenshot, repost, tracing and our generated model derived from one plan are one evidence family. Treat unknown independence conservatively; film frames repeated in Marina's tour are still the same film evidence.
4. Do not average incompatible targets. Model4.938 m plus visitor-plan4.572 m does not imply a “correct”4.755 m room. The model is what we have, not an independent observation of the film.
5. A major room/stair resize requires a documented applicable dimensional anchor or a multi-view camera fit with stated uncertainty, plus evidence that adjoining important rooms and circulation remain coherent. Without it, keep a reversible candidate and label the result approximate.
6. Record each accepted change with source IDs/links, question-specific weights, confidence, remaining conflict and affected neighbouring rooms. If new evidence contradicts it, revise the decision explicitly rather than silently replacing the baseline.

Next calibration task remains foyer/stair camera matching. Eric's plan is a supporting hypothesis; film views constrain the resulting appearance. This ledger is the governing rule for Stage 2.
