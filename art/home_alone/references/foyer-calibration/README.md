# Foyer comparison — September 13, 2026

Latest: [local upstairs opening study](fit/OPENING-REVIEW.md) tests the opening side edge independently of the main stair width, with directed rail-line fitting, before/after captures and walking checks. Working house restored; candidate remains provisional.

**Update:** the subsequent [numerical camera fits and disposable candidate review](fit/REVIEW.md) now include baseline/candidate captures and walking results. Automatic25% central-strip narrowing was tested and rejected for promotion; absolute dimensions remain unresolved. The text below records the earlier reference-collection pass.

Stage 2 evidence collection and preliminary comparison. **Camera matching and dimensional calibration remain incomplete.** No structural correction or resize candidate is accepted by this packet. See the governing [source weights](../dimensional-baseline/SOURCE_WEIGHTS.md) and [measured baseline](../dimensional-baseline/README.md).

## Additional original frames

Extracted directly with ffmpeg, without image generation, retouching or cropping. Times are source-video times. Part 1 source: repository-root `Tour the Home Alone House_ Part 1, Main Floor [CG Tour] copy.mp4`; Part 2: `Tour the Home Alone House_ Part 2  [CG Tour].mp4` ([published Part 2](https://www.youtube.com/watch?v=kU7aY1anpAI)).

| Frame | Time | Use / evidence class |
|---|---|---|
| [Entry](entry201.jpg), [reverse entry](entry205.jpg) | Part 1 3:21, 3:25 | Vestibule opening, dining opening and stair relationship. Marina CG: relationship weight 3; absolute dimensions 1 |
| [Entry opening](entry215.jpg) | Part 1 3:35 | Closer opening detail; CG, same weights |
| [Main stair](foyer338.jpg), [treads](stairs342.jpg) | Part 1 5:38, 5:42 | Tread edges, railing and approach to rear landing; CG, same weights |
| [Rear landing](landing350.jpg) | Part 1 5:50 | Table and picture left of paired sash; foreground railing and sloping panel transition. CG, relationship weight 4 where corroborated by supplied film foyer frame; absolute dimensions 1 |
| [Upper film insert](upper570.jpg) | Part 2 9:30 | Film still embedded in tour; visible relationships weight 5, dimensions 1. Orange annotation is not film evidence; not an independent source from the film |
| [Upper hall](upper580.jpg), [bath/Buzz doorway](upper590.jpg) | Part 2 9:40, 9:50 | Hall returns and room openings; CG, relationship weight 3, dimensions 1 |

Also inspected `entry220.jpg` (dining windows), `upper600.jpg` (another bedroom doorway), `upper640.jpg` (parents bedroom), and `upper948.jpg` (basement-door film insert). Retained for provenance, excluded from the foyer comparison. Filenames use seconds, not room identities.

## Current-model comparisons

These Unity captures are approximate viewpoints, **not matched-camera overlays**. Pixel-size differences cannot yet establish scale errors. Coordinates are Unity world metres; all three use vertical FOV 60 degrees. Working geometry and lighting were unchanged.

| View | Current capture / camera | Finding and confidence |
|---|---|---|
| Reverse entry | [Unity](../../../../unity/HomeAlone/Assets/Captures/IntactHouseReference/calibration-reverse-entry.png), position (2.8, 3, 6), yaw 180 | Front entry and flanking room openings are present. Reference includes substantial foreground stair/tree/furniture absent from this framing. Medium confidence in broad topology; no supported width correction |
| Rear landing | [Unity](../../../../unity/HomeAlone/Assets/Captures/IntactHouseReference/calibration-landing.png), position (0.1, 5.65, 7.5), yaw 0 | Table and picture sit left of paired window, with continuous adjoining wall. High confidence in this arrangement. Reference has a sloping-to-horizontal lower-panel transition and much more refined slender furniture. Current framing omits foreground balustrade, so it cannot establish landing depth or table scale |
| Upper crosswalk | [Unity](../../../../unity/HomeAlone/Assets/Captures/IntactHouseReference/calibration-upper.png), position (0.1, 6.9, 6.7), yaw 155 | Compare with [supplied film target](../foyer-film/upstairs-film-quality-target.png): green central closet wall, flanking passages and foreground guardrail broadly agree. Current flat arch/ceiling treatment and square railing remain visual discrepancies. Open bathroom door is an intentional walking-state difference; don't mistake it for missing structure |

The archived [Part 1 automatic transcript](../reconciliation/transcript.txt), 4:16–4:27, attributes deliberate stage staircase distortion for the sled scene to production designer John Muto. This is a secondary attribution in automatic captions, not a verified production measurement. It is a reason to keep the real-house plan and film set separate, not a numerical correction factor.

## Decision and remaining gate

- Retain current dimensions for this pass. The measurements establish what we built, while these frames constrain appearance and connections. Neither alone yields an authoritative shrink percentage.
- D01 foyer width and D04 stair proportions remain open. Fit camera position, rotation and lens against fixed structural landmarks first: entry jambs, stair nosings, rear window corners and crosswalk edge. Require agreement in entry, landing and upper views before accepting a local geometry candidate. Report residual mismatch and scale ambiguity rather than selecting an arbitrary standard door width as truth.
- Keep finishing discrepancies (panel transition, table detail, balusters, arch profile) separate from shell dimensions. Revisit after the structural comparison; do not use decoration to conceal a layout mismatch.
- Existing walking camera restored to local (0, 1.65, 0), identity rotation, FOV 75; FpsController enabled. No scene save or geometry mutation made by this comparison.
