# FEAT-030 Original-derived auto-rig context

- Status: REVISION_3_PART_AWARE_BASELINE_IMPLEMENTED; REVISION_4_SAM21_WORKER_IMPLEMENTATION_IN_PROGRESS; LIVE_ACTIVATION_PENDING_L4_BENCHMARK.
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
