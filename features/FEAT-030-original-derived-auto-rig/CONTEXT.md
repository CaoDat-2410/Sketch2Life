# FEAT-030 Original-derived auto-rig context

- Status: REVISION_3_PART_AWARE_BASELINE_IMPLEMENTED; REVISION_4_SAM21_WORKER_IMPLEMENTATION_IN_PROGRESS; QWEN_SINGLE_PASS_AND_SAM_PROMPT_FIX_IMPLEMENTED; SAM2_SUCCESS_MASK_HANDOFF_FIX_IMPLEMENTED_LOCALLY; PIXI_STARTUP_BRIDGE_REPLAY_IMPLEMENTED_LOCALLY; ANDROID_LIGHTNING_VISUAL_RETEST_PENDING; LIVE_ACTIVATION_PENDING_L4_BENCHMARK.
- Owner: Project owner; Revision 4 implementation is explicitly approved, while live default activation remains benchmark-gated.
- Goal: turn a validated subject from the child's immutable drawing into a bounded, explainable PixiJS 2D rig so the drawing visibly moves while remaining recognizably the child's work.
- Scope: target selection, spatial grounding, segmentation, original-derived masks/textures, mesh and skeleton generation, skin weights, rig validation, bounded motion profiles, asynchronous preparation, Renderer V2 loading, PixiJS CPU skinning, deterministic fallback, provenance, metrics, and golden-scene evidence.
- Non-goals: generative redrawing; replacing the original; semantic re-analysis through a second Qwen request; AI video generation; changing Gate A or Gate B authority; letting the renderer or mobile app call model providers; inventing actions unsupported by the drawing and learning objective; removing Renderer V1.
- Dependencies: FEAT-003 canonical understanding, FEAT-004 art player invariants, FEAT-005/018 supervised flow and Gate B, FEAT-028 approved supplemental assets, FEAT-029 master SRS, `docs/governance/FRONTEND_ASSET_GATE.md`, and the repository approval/evidence policies.
- Risks: poor masks on children's drawings, GPU contention with Qwen, long preparation time, bridge payload size, background holes/ghosting, unstable mesh topology, unsafe or semantically invented motion, and derived artifacts being mistaken for approved creative assets.

## Owner brief

The requested direction is an automatic 2D rig pipeline:

`OriginalDrawing + CanonicalUnderstanding + Gate B`

→ target selection → localization → segmentation → mask cleanup → archetype → keypoints/skeleton → mesh → bones → weights → validation → motion profile → `RiggedArtworkPackageV1` → `VisualAnimationPlanV2` → `RendererLoadCommandV2` → PixiJS mesh deformation.

The original drawing remains immutable. Every mask, crop, texture, mesh, rig, and background patch is a derived artifact with a source hash and derivation record. A rigging failure must never fail the supervised session.

## Current product boundary

- Gate A remains the semantic authority for the selected subject and learning direction.
- Gate B remains the authority for the activity/experience to be shown.
- The auto-rig pipeline may derive geometry; it must not independently reinterpret the story or select another subject.
- The mobile app receives only backend-issued launch contracts and short-lived capabilities. Provider credentials and internal endpoints remain backend-only.
- Renderer V1 remains available until V2 quality, latency, stability, and rollback evidence are accepted.

## Source and authority

- Direct owner request and the supplied auto-rig proposal define the desired direction for this feature.
- `feat-029-master-srs`, `sketch2life-workflow`, and accepted feature records are requirement baselines, not implementation approval.
- Exact segmentation, grounding, and geometry libraries remain candidates until an ADR records benchmark evidence. The handbook explicitly does not freeze providers without evaluation.

## Revision 4 implementation boundary

The approved implementation now includes the typed SAM 2.1 worker contract, a lazy process-scoped
Lightning runtime, a backend-only adapter, deterministic bounded box proposal, mask provenance,
and safe typed fallback. The SAM2 dependency/checkpoint is not installed or downloaded by the
repository change. Live activation remains opt-in via `SKETCH2LIFE_LIGHTNING_SAM21_ENABLED=true`
until the L4 benchmark and deployment ADR evidence are recorded.

## Owner closure — 2026-09-25

- Spatial grounding and segmentation may begin after Gate A to hide latency. Gate B is still required before the final motion/experience plan is compiled or presented.
- Coverage must address the full range of children's drawing topics. This means all initially identified archetype families plus deterministic `generic_organic`, `rigid`, and `unknown` handling; it does not permit fabricated semantics or guarantee a bespoke skeleton for every possible object.
- Auto-rig may run as a separate worker/service on the same Lightning L4 host. Because Qwen currently lazy-loads when used, implementation must measure combined VRAM and coordinate GPU work rather than assuming both models can run concurrently without limits.
- Lightning `/v2/vision` keeps bounded repair disabled by default so one live request performs at most one Qwen inference; repair remains an explicit benchmark opt-in through `SKETCH2LIFE_LIGHTNING_VISION_BOUNDED_REPAIR=true`.
- The same live route enables in-memory structural normalization separately, so common Qwen JSON shape drift is canonicalized without starting a second model attempt.
- Lightning runtime logging is explicitly INFO-level so typed vision outcomes are visible even when the worker returns HTTP 200; greedy generation removes unused sampling fields to avoid misleading Transformers warnings.
- The Lightning worker also emits a sanitized stdout completion line, and the mobile client preserves closed, parent-facing workflow messages instead of collapsing them into a generic image-read error.
- The backend SAM2 adapter now creates a bounded box from clustered colored ink before calling `/v2/rig/segment`; blank or invalid images still fail closed. Pillow is a runtime dependency because prompt extraction occurs in the backend process.
- The 2026-09-27 Lightning evidence confirms Qwen is single-pass and successful while SAM2 returns typed `MODEL_UNAVAILABLE`. The worker now resolves standard checkpoint/config locations from `SAM2_MODEL_DIR` and logs a closed private diagnostic reason without exposing provider details to mobile; live SAM2 activation still requires the private runtime dependency/checkpoint setup.
- The 2026-09-27 SAM2-success runtime fix now gives the WebView a separate short-lived mask capability, verifies source/package/mask hashes and mask dimensions, and composes a subject-only cutout only when neutral-paper corner checks validate a safe local background patch. Subject-only masks stay at `CUTOUT_MICRO_MOTION`; missing/unsafe masks use V1 and send a playback result so the mobile screen cannot remain indefinitely at zero duration. Android + live Lightning visual retest is still pending.
- The 2026-09-28 emulator retest disproved the earlier Pixi-init-stall hypothesis: WebGL/Pixi became ready, but no source/package/mask request followed. The startup bridge now caches one validated launch and replays that exact message after Pixi readiness; renderer-side handling deduplicates it, and native timeout copy distinguishes handshake, Pixi initialization, and post-ready loading. Unit/type/build checks pass. Full post-fix artifact-flow verification is pending because the configured image workflow may invoke live Lightning inference.
- Metadata-only part proposals no longer promote a package to `FULL_AUTO_RIG`; the current package/renderer path does not yet deliver independent part masks to PixiJS.
- The approved 2026-09-28 part-motion restoration is implemented locally and passes focused offline checks. It carries bounded part-mask capabilities and source provenance from SAM2.1 through the renderer command. The worker encodes the image once and attempts role-specific SAM prompts; a rejected part prompt does not discard a valid subject mask. If fewer than two quality-checked model parts survive, deterministic archetype-anchored image processing partitions only pixels already inside the subject mask; unsupported/generic shapes remain lower-tier.
- `FULL_AUTO_RIG` now reaches separate source-derived Pixi sprite textures for every validated part (not rectangular butterfly crops). The whole-subject fallback keeps fixed framing and may only use small translations; V2 zoom/rotation and the post-completion infinite idle were removed. The default plan is 20 seconds, semantic tracks end at 14.4 seconds, and the remaining 5.6 seconds holds neutral.
- Whole-drawing and V2 canvases now use aspect-preserving contain-fit with a 12% margin, avoiding the natural-pixel-scale crop when the renderer enters the original-art fallback. Backend auto-rig logs identify whether validated part masks came from SAM2.1 or image processing, or why a partition was unavailable.
- Focused offline checks pass for synthetic butterfly, bird, flower, tree, fish and biped partitions, package/capability handoff, renderer part sprite/keyframe/rest behavior, and the legacy fixed-camera fallback. No live Lightning/SAM/Qwen request or Android visual smoke was performed; real-drawing mask quality, background seam quality and L4 latency remain unverified.
