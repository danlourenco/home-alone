# Process review (Codex, Oct 17 2026, read-only audit; requested by the user)

**The process is better at proving that the build matches its inputs than proving that those inputs describe the right thing.** The arch failure was not a lack of checks: it was a misidentified feature propagated through checks that could not challenge its identity.

Ranked below by expected rework, damage to accepted work, and wasted user review time. “Studio approach” means the production practice I would require here, not a claim that every studio uses it. Runtime consequences marked as hypotheses were not tested.

1. **Critical: nobody independently verifies what the measured pixels represent.**

   **Now:** Solved cameras, ratios, and multiple frames validate measurements. But the same interpretation can contaminate every frame. The [arch record](changes/2026-10-16-foyer-arch-model.json) explicitly says the crown was picked on the landing fascia and the apparent casing was a closet-door edge. Before/after film views already existed.

   **Studio approach:** Approve feature identification before approving its measurement. A second reader examines annotated source crops without being given the proposed answer. Room reference boards distinguish opening edges, fascia, trim, occluding furniture, and uncertain features.

   **Failure:** A beautifully constructed, precisely fitted version of the wrong object reaches the walk.

   **Smallest fix:** For each changed architectural feature, require one annotated source crop, one alternative interpretation, and one independent reading. Overlay the proposed **blockout silhouette** on the reference before bevels, maps, or baking. The arch’s “paper must continue above the crown” relationship should have been the first check.

2. **Critical: R1 can count the generated model as independent historical evidence.**

   **Now:** [change_gate.py](tools/house/change_gate.py) compares declared identifier sets and trusts `agrees`. It does not establish that a check measures the claim, nor resolve dependencies transitively. Risk coverage is optional. The arch record includes `tools:model_quality` and `unity:build` as agreeing topological checks.

   **Verified:** In memory, I removed every arch check except `tools:model_quality`. **R1 still passed with one “independent” check.** No files changed.

   **Studio approach:** Separate reference evidence, measurement consistency, implementation QA, and user acceptance. Implementation QA cannot validate historical geometry.

   **Failure:** This recreates the circular proof behind the [reverted Buzz resize](changes/2026-10-13-buzz-resize.json), with different identifiers. A ratio proving a paper band exists also does not independently establish an absolute crown height.

   **Smallest fix:** Add a check category and explicit claim-component IDs. Exclude generated-build checks from R1; require evidence for each changed metric or topology claim. Make extraction/scale/registration risks explicit, with justified “not applicable” values.

3. **Critical: “gate” failures do not reliably stop build-to-load.**

   **Now:** [unity_pipeline.sh](tools/house/unity_pipeline.sh) suppresses Unity’s exit status and the quality checker’s exit status with `|| true`. It searches for C# errors, then prints matching report lines. Finding a failure line is still a successful `grep`. `all` chains this into bake and load.

   The [existing report](spec/captures/walk-test-wallgrid.txt) contains a blocked service-stair leg and four HallArches quality problems.

   **Studio approach:** Promotion requires a fresh, complete validation result for the exact candidate. Known exceptions are explicit and narrowly scoped.

   **Failure:** A failed build can leave an older scene/report available; a quality failure can reach the user despite the skill saying zero problems.

   **Smallest fix:** Fail on unsuccessful build, missing completion marker, stale report, or unwaived failure. Have `load` require that result. Preserve the known stair exception explicitly instead of treating all failures as printable information.

4. **Critical: the commit gate watches the retired pipeline more closely than the current one.**

   **Now:** [.githooks/pre-commit](.githooks/pre-commit) watches measurements, `house_spec*`, furniture, the reconciler, and two older scenes. Its geometry trigger omits `spec/geometry.json`, `spec/dressing/`, `hifi_*.py`, current builder scripts, and `House_WallGrid.unity`. Seam enforcement names only `Greybox_Upstairs.unity`.

   **Studio approach:** Protect the actual dependency graph and promotion artifact, not an outdated filename list.

   **Failure:** Current furniture placement, generated architecture, or scene changes can avoid the change-record gate. This exposes exactly the surface changes implicated in the arch and living-room incidents.

   **Smallest fix:** Expand the trigger to current geometry producers and outputs, require records to identify affected elements/files, and apply the scene gate to `House_WallGrid`. Add small tests proving each current change category triggers enforcement.

5. **High: scratch copies are not isolated build inputs.**

   **Now:** `setup` in [unity_pipeline.sh](tools/house/unity_pipeline.sh) links every scratch copy to the repository’s live `spec`. Reports also land in shared locations. Builds copy current repository scripts over scratch scripts. [room-upgrade](.claude/skills/room-upgrade/SKILL.md) records an actual scratch draft being overwritten by another build.

   Disk inspection showed **23 GiB available**; [STATUS](docs/STATUS.md) records a 26 GB Library.

   **Studio approach:** One serialized build worker consumes an immutable input snapshot, retaining its import cache. Promotion transfers a complete candidate with a manifest.

   **Failure:** A scratch scene can combine one job’s models, another job’s spec, and a shared report from a third build. One active agent reduces concurrency but does not prevent sequential contamination.

   **Smallest fix:** Use one lock and one reusable scratch Library. Snapshot spec and scripts per candidate; give reports a build ID. Refuse promotion if source hashes changed. Check free space before copying. Do not start by creating more full project copies or a build farm.

6. **High: low camera residuals are being asked to prove too much.**

   **Now:** [refcam.py](tools/house/refcam.py) fits level cameras with a centered principal point. It reports fitting residuals, but `measure` returns a single ray-plane intersection without uncertainty propagation or a grazing-angle rejection. It does not require held-out controls.

   **Studio approach:** Treat camera calibration, feature identification, and measurement uncertainty as separate approvals. Lock cameras for comparison; do not let a new fit absorb a geometry error.

   **Failure:** [room-upgrade](.claude/skills/room-upgrade/SKILL.md) records grazing-wall placements moving roughly a metre with small yaw changes. [DEVIATIONS 59](docs/DEVIATIONS.md) says pitched living-room shots were placed by eye because the level-camera model did not apply.

   **Smallest fix:** Require held-out controls on another depth plane and a pixel/pose perturbation spread for each new measurement. Refuse unstable intersections. Route pitched shots through the existing pitched solver rather than falling back to eyeballing.

7. **High: the approved interior/exterior split lacks an early gameplay acceptance test.**

   **Now:** [DEVIATIONS 1](docs/DEVIATIONS.md) approves preserving Marina’s upstairs while showing the film exterior, with window positions differing by up to 1.5 m. It explicitly leaves upstairs-window/yard sightline mapping open.

   **Studio approach:** Prototype the consequences of this architectural decision before completing affected rooms: stair transitions, window views, exterior observers, shadows, and interaction across the boundary.

   **Failure — hypothesis:** Later gameplay may reveal that seeing Kevin through a window, aiming through it, or moving an object between spaces cannot agree with the visual mapping. That could force expensive architectural work after dressing.

   **Smallest fix:** Specify three acceptance scenarios now: crossing the stair transition, looking out of an upstairs window, and looking back at that window from outside. Preserve the approved split; prove its required behavior before expanding detail.

8. **High: “replay the user’s view” currently replays a different camera.**

   **Now:** [FpsController.cs](unity/HomeAlone/Assets/Scripts/FpsController.cs) defaults to Kevin’s 1.10 m eye. [note_views.py](tools/house/note_views.py) adds 1.65 m and hardcodes 60° vertical FOV. `unity_pipeline.sh shot` adds 1.28 m. [FeelNotes.cs](unity/HomeAlone/Assets/Scripts/FeelNotes.cs) records the player root and view angles, but not actual camera position, FOV, body/crouch state, or day/night state.

   **Studio approach:** Capture the camera and gameplay state at the same instant as the screenshot.

   **Failure:** A Kevin complaint replayed by `note_views` is viewed **55 cm too high**. The arch record’s separate Kevin and 1.28 m renders already expose this ambiguity.

   **Smallest fix:** Store world camera transform, projection/FOV, body state, lighting mode, and build ID in each note. Replayers consume those values directly. Mark old notes as approximate reconstructions.

9. **High: expensive detail is allowed before layout uncertainty is resolved.**

   **Now:** [room-upgrade](.claude/skills/room-upgrade/SKILL.md) calls for reference sheets and measured placement, but [DEVIATIONS 59](docs/DEVIATIONS.md) records by-eye living-room placement and standard sizes. [STATUS](docs/STATUS.md) then queues sofa-wall, piano-rotation, desk-rotation, and tree-placement corrections. The breakfast table needs a film-first pedestal revision.

   **Studio approach:** Approve room composition and circulation using cheap measured proxies, then spend on final assets and lighting.

   **Failure:** Every layout correction invalidates placement, colliders, dressing, captures, and potentially the bake. The documented approximately 30-second build and 60-second bake are not the main waste; rebuilding the wrong premise is.

   **Smallest fix:** Add a room-level layout checkpoint: reference board, solved views, furniture envelopes, and Kevin/adult circulation. Keep polished work provisional until that checkpoint passes. Bake for lighting review, not every geometry experiment.

10. **High: zero counts conceal untested player-visible surfaces and routes.**

    **Now:** The [report](spec/captures/walk-test-wallgrid.txt) says Z-fight zero while skipping 25 unreadable meshes. [BuildWallGrid](unity/HomeAlone/Assets/Editor/SpecGreybox.cs:295) disables `Ground/Dressing` during several checks and adds traps after the checks. [STATUS](docs/STATUS.md) records a triangular stair-wainscot gap despite Trim reporting zero.

    **Studio approach:** Report coverage beside results. Maintain separate structural checks and finished-scene gameplay/visual checks.

    **Failure:** A valid wall graph does not prove a clean stair finish, usable furniture passage, or working trap route. Arch fit proves fit to the opening, not resemblance to the film.

    **Smallest fix:** Name skipped assets and excluded systems in the handover. Add a short final-scene route covering stairs, furniture gaps, kid hiding, adult exclusion, and body expansion under obstacles. Add fixed crops for actual visual failures.

    Use screenshot diffs to flag regressions, not automatically certify fidelity: [verify-plan](.claude/skills/verify-plan/SKILL.md) already demonstrated that its edge score missed a 20 cm perturbation.

11. **High: rejection history and acceptance are not dependable state.**

    **Now:** R2 counts only `outcome == "failed"`. The [arch history](changes/2026-10-16-foyer-arch-model.json) uses `"failed (user walk…)"`. Running its gate read-only reported **zero failed attempts**. Its manually supplied premise review saved the documentation, not the enforcement.

    Records and [feel-notes.jsonl](spec/feedback/feel-notes.jsonl) also lack a common immutable candidate ID. Tree height is accepted while its position remains open—legitimate partial acceptance that a room-wide status cannot express.

    **Studio approach:** Track issues and sign-off per element, aspect, and candidate.

    **Failure:** Rejections disappear from automated history; an old acceptance can appear to cover a later rebuild. The user repeatedly discovers the same class of defect.

    **Smallest fix:** Validate outcome enums; move prose to a separate field. Link each rejection to its issue and successor attempt. Before a walk, provide a compact packet: exact candidate, changed items, reference comparisons, unresolved exceptions, and a short route with explicit questions.

12. **High: runtime measurement is deferred while rendering cost accumulates.**

    **Now:** [ShadowAudit.cs](unity/HomeAlone/Assets/Editor/ShadowAudit.cs) already measures atlas behavior and temporal differences—useful groundwork. But [STATUS](docs/STATUS.md) says flicker remains after the shadow pass. [DEVIATIONS 61–62](docs/DEVIATIONS.md) records an undecimated 115k-face ficus and 57.3 million cached shadow texels used out of 67.1 million.

    **Studio approach:** Establish the target hardware, resolution, and frame budget before further dressing; profile a repeatable representative route.

    **Failure — hypothesis:** More lights, foliage, transparency, and materials may require broad asset or lighting rework. A passing atlas allocation check does not establish stable frame time.

    **Smallest fix:** Schedule a baseline capture of CPU/GPU frame time, p95/p99 spikes, draw calls, visible triangles, memory, shadow requests, and cache refresh cost across day/night routes. Include TV, moving traps, and camera pans. Honor the deferred optimization decision; measure first without starting an unsolicited optimization pass.

13. **Medium-high: the art gate checks ingredients, not the finished runtime asset.**

    **Now:** [model_quality.py](tools/house/model_quality.py) has valuable geometry/map checks, but `--report` only gates tagged pipeline models: the current report covers **2 of 30**. LOD acceptance is a node name containing `_LOD` or a `lod_reason`. [hifi_pipeline.py](tools/house/hifi_pipeline.py) creates decimated copies; that alone does not prove runtime switching.

    **Studio approach:** Standardize the imported result: material families, texture scale, channel interpretation, silhouette, LOD behavior, collider fidelity, and reference lighting.

    **Failure:** The raw-plaster speckles on the arch and missing/magenta imported assets documented in [artist-pipeline](.claude/skills/artist-pipeline/SKILL.md) and room-upgrade show why Blender-side correctness is insufficient. **Hypothesis:** named LOD copies could pass without useful runtime LOD behavior; I did not verify importer behavior.

    **Smallest fix:** Require every changed asset to pass the new standard, without demanding a house-wide conversion first. Verify its assigned Unity materials and actual LODGroup or budgeted exemption. Judge finish under one neutral setup and the room’s live day/night setup.

14. **Medium-high: freshness stamps cover only the dependencies someone remembered to list.**

    **Now:** [build_models.py](tools/house/build_models.py) hashes declared sources and GLBs; downloaded inputs are explicitly excluded. The current table omits [hifi_french_doors.py](tools/house/hifi_french_doors.py), although its [change record](changes/2026-10-16-french-doors.json) describes a generated model driven by dressing and geometry.

    **Studio approach:** Keep a complete build/asset manifest, including private dependencies without publishing them.

    **Failure:** A French-door input can change without the freshness checker noticing. A clean clone can intentionally substitute generated plants for purchased ones, so “same commit” does not mean “same reviewed house.”

    **Smallest fix:** Register the missing generator and its dependencies. Check generator coverage. Include output textures, tool versions, asset hashes, and required/private asset presence in the candidate manifest. Refuse fidelity promotion when a required purchased asset silently falls back.

15. **Medium-high: conflicting documentation can resurrect rejected premises.**

    **Now:** [RECONCILIATION](docs/RECONCILIATION.md) says Unity reads only `house_spec.json`, while the current builder reads geometry and dressing files too. It excludes film measurements broadly, while current work uses calibrated film measurements. [DEVIATIONS](docs/DEVIATIONS.md) has duplicate IDs 50–52, old crown measurements beside their correction, and an old Buzz section still calling the camera-inside-room argument “Independent proof.”

    **Studio approach:** Separate current decisions from historical evidence. Give each element a current authoritative measurement/decision and explicit supersession links.

    **Failure:** The next agent can faithfully follow a document and repeat a known error. A reference such as “DEVIATIONS 52” is no longer unambiguous.

    **Smallest fix:** Repair duplicate IDs and mark disproven claims as superseded in place. Reduce STATUS to current candidate, accepted decisions, open issues, and next work. Update the data-flow diagram to the real pipeline. Keep history, but stop presenting it as current authority.

**First three things to do this week**

1. **Make promotion trustworthy:** fail-closed build/load, current-path hook coverage, strict history enums, and exclusion of generated QA from R1. Add regression tests for the two in-memory failures demonstrated here.
2. **Make one review reproducible:** immutable candidate inputs, build ID, exact camera-state notes, and a small pre-walk packet. Use the arch as the pilot.
3. **Start Buzz with evidence and blockout only:** independently reviewed feature picks, explicit unresolved depth evidence, measured furniture sequence, locked reference views, and Kevin/adult routes before detailed assets.

Skipped: Unity execution, renders, edits, commits, and all web requests; Git status failed under read-only/LFS restrictions.  
Risk: this is a process/code audit, not visual acceptance of the current house or a measured runtime-performance verdict.

