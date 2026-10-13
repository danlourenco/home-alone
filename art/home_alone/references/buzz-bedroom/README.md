# Buzz bedroom — film relationships govern the furnishing pass

## September 14: inferred bed placement from the overhead

User directed us to infer proportions from layout, specifically Part 2 around0:50; no stated dimensions are available. Extracted and inspected [0:50 overhead](overhead50.jpg) and [0:54 production-set image](overhead54.jpg). The latter supports set/window context, not furniture measurements.

The overhead puts the bed slightly toward the hall side, with a substantial passage beside the front-wall dresser. Approximate image readings in the Buzz region: room span near bed/dresser about240px; mattress width about70px; bed-to-chest visible separation roughly40–60px depending on post versus mattress edge. Those are different elevations in an oblique view, not a rectified survey. They suggest maintaining the current mattress-to-room-width ratio (~0.29) and adjusting lateral placement before shrinking the mattress. Weight3 for Marina's arrangement,1 for image-derived metres; user authorization permits an explicitly inferred working fit.

Adopted a **+0.25m Z offset** of the bed and bedside table toward the hall side. Room walls, dresser, shelves and bed dimensions unchanged. This is a conservative authored placement within the broad visual estimate; neither25cm nor the resulting83cm is claimed as a film measurement. Bed bounds now Z−0.840..0.640; dresser forward edge Z−1.670 gives **0.830m** separation instead of0.580m. The bedside table follows the bed to retain their relationship.

Runtime14 room and8 wing checkpoints, animated tarantula containment and window checks PASS after saving. [Overhead comparison](../../../../unity/HomeAlone/Assets/Captures/IntactHouseReference/buzz-layout-overhead.png) inspected in the reference orientation, using a temporary cutaway/EV5 diagnostic view; normal perspective, exposure, AA and walking restored. Absolute room dimensions and final furniture silhouettes remain provisional. This supersedes the earlier hold on changing the bed position below.

## Window consistency pass — September 14, 2026

Applied and saved `SurveyBuilder.DressBuzzWindows()` in `BuzzBedroom.cs`: all three openings now have ivory interior reveals/casing/sills and green pleated curtains. The side opening previously lacked the dressing and exposed a brick border. Front curtains previously used long ellipsoid folds; all three now use the same pleated treatment fitted to each existing opening. The furnishing builder calls this same method so rebuilding preserves the correction. No room boundary, sash dimension, furniture placement or lighting setting changed.

Evidence inspected: [film desk/window at 500s](film500.jpg), [Marina front windows at 550s](tour550.jpg), [Marina bed/door at 556s](tour556.jpg). Film has weight5 for visible curtain/window relationships,1 for dimensions; Marina weight3 for inferred dressing/arrangement and1 for uncalibrated dimensions. These are not independent votes for a measured room size. Side two-column pattern is retained; the evidence does not require all windows to have identical widths.

| Live assembly | Clear width × height | Glazing bottom Y | New sill top Y |
| --- | --- | --- | --- |
| Front pair | 0.940 × 1.620m each | 5.830 | 5.855 |
| Side | 0.872 × 1.621m | 5.8315 | 5.8565 |

The sill difference is approximately1.5mm, not a major floor-height discrepancy. The apparent size difference also includes perspective, a68mm width difference and previously missing side dressing. These dimensions describe the model, not verified film measurements.

Furniture remeasurement: bed bounds X−3.990..−1.410,Z−1.090..0.390; dresser bounds X−3.950..−3.150,Z−2.240..−1.670. Their Z gap is **0.580m**. Controller nominal diameter is0.600m; skin/contact handling means a successful walk test is not a comfortable-clearance or film-scale sign-off. Keep this discrepancy open; no furniture was shrunk, rotated or moved.

Validation: `CheckBuzzWindows` PASS (three dressed windows, sill spread≤3mm, no dressing colliders); existing75-window transparency/barrier/joint check PASS. `CheckBuzzBedroom` PASS (14 room checkpoints,8 side-wing checkpoints, Jordan, eight legs and60-second sampled tarantula containment). Walk controls enabled and point-shadow count0. Scene saved, Play/daytime restored in Buzz. First post-traversal capture was temporally smeared; settled replacement inspected. No AA or exposure changes.

[Before](../../../../unity/HomeAlone/Assets/Captures/IntactHouseReference/buzz-window-audit-before.png) · [After](../../../../unity/HomeAlone/Assets/Captures/IntactHouseReference/buzz-window-audit-after.png). Comparable room views; small camera settling differences prevent pixel-level overlay claims. New trim is not a lighting bake or final material-quality pass.

User correction: preserve the film furniture layout. Do not rotate furniture or shrink it simply to make the base fit; expose shell/dimension conflicts instead.

Sources inspected:
- Locally archived Marina Coates Part 2 tour, https://www.youtube.com/watch?v=kU7aY1anpAI : 500s film desk/window still; 529s film Jordan/desk/shelves/terrarium still; 532/535/540/545/550/556/560s reconstruction views; 78s upstairs overview. Film stills take precedence; the reconstruction fills gaps without constituting a survey.
- 1987 Jordan Measure Up poster photograph: https://www.ebay.com/itm/256975015023 ; image https://i.ebayimg.com/images/g/1tkAAOSwd31oTLI5/s-l1600.jpg . The Unity cutout traces the figure in mesh UVs, retaining the opening between his legs. No purchase made.
- Supporting film-room inventory: https://uncletnuc.com/2015/12/29/buzzs-bedroom/ .

Layout anchors in Unity: south/front sash pair and dresser between them; west side window and desk with bulletin board; Jordan at west/north corner; north-wall display shelves with lower-shelf terrarium; east-wall headboard beside the hall entrance, with bedside table toward the front window. The first arbitrary furniture adaptation was discarded following the user's correction.

Base conflict found: the west-wall doorway to the side wing occupied the film's desk/Jordan corner. It is infilled by a separate removable wall object; the source door frame object43 is hidden. The side wing remains connected through the rear bedroom at X approximately -6.14, Z6.43. Eight controller checkpoints verified entry, travel through the wing, and return. Original GLB is untouched. No room boundary was moved or furniture uniformly scaled down to hide a conflict.

Measured base interior approximately X -6.10..-1.16, Z -2.30..1.88, floor Y5.22: 4.94 x 4.18 m in adopted native units. This is NOT a measured film-room size. Exact film dimensions, window spacing and furniture dimensions remain unverified; no defensible percentage size discrepancy is available yet. The furniture follows observed relationships, not a claim of survey precision. The bed-to-dresser passage is0.58m in the September14 full-renderer bounds check, superseding the earlier approximate0.67m estimate.

Builder: Assets/Editor/BuzzBedroom.cs, root BuzzBedroomDetails. Props include bed/green quilt, bedside cabinet/lamp, dresser, shelves/game boxes/trophies, green curtains, desk bulletin board, sports and Ice T prints, mini hoop, Jordan cutout and terrarium. The source west desk/chair is retained; a floating shade is hidden and clock moved onto the desk. Only Buzz's old north-wall prop fragments are clipped from the intersecting combined prop render/collision meshes into dedicated derived mesh assets; room wall meshes are excluded. Original source asset is unchanged.

Tarantula: separate object with eight articulated legs, abdomen, carapace and pedipalps; TerrariumTarantula.Pose animates a contained patrol. The terrarium includes single-surface transparent glass, soil, hide, water dish and ventilated lid. Geometry and animation are simplified; no pickup/throw mechanic or collapsing shelves implemented. Reference-derived poster textures and grain are a furnishing pass, not final scanned materials.

Validation: CheckBuzzBedroom passes 14 room controller checkpoints, eight side-wing checkpoints, eight-leg presence, movement and a 60-second sampled containment check. CheckExteriorNight passes; point-light shadows remain disabled as confirmed by the user. Sheer-curtain task was interrupted by this prioritized room task and remains unfinished.
