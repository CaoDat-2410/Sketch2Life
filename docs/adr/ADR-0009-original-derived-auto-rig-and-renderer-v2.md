# ADR-0009: Original-derived auto-rig and Renderer V2

- Status: Accepted for staged implementation
- Date: 2026-09-25
- Owners: Project owner and Sketch2Life implementation team
- Feature: FEAT-030

## Context

Renderer V1 animates whole-drawing and crop sprites. It has no subject segmentation, mesh, skeleton, weights, or pixel deformation. Reusing the Qwen vision endpoint for a second localization request previously caused duplicate model work and invalid-region failures. The product requires visible subject-specific motion while preserving the child's original drawing and Gate A/B authority.

## Decision

1. Start spatial grounding/segmentation after Gate A to hide latency. Do not compile or publish the experience-specific motion plan until Gate B is approved.
2. Track preparation in an independent auto-rig job. Do not add media-generation states to the business session state machine.
3. Run auto-rig through a replaceable worker/service on the same Lightning L4 host. Default to serialized GPU admission until measured evidence proves safe concurrency with lazy-loaded Qwen.
4. Cover all admitted topics through the initial registry (`butterfly`, `bird`, `flower`, `tree_branch`, `fish`, `biped`, `rigid`, `generic_organic`, `unknown`) and explicit generic/rigid/unknown fallback. Do not invent anatomy or semantics.
5. Introduce additive V2 contracts. `RendererLoadCommandV2` carries capability-protected references and hashes, not inline mesh or image data.
6. Keep Renderer V1 unchanged and use fallback order `FULL_AUTO_RIG -> CUTOUT_MICRO_MOTION -> BBOX_VISUAL_FOCUS -> WHOLE_DRAWING_V1`.
7. Treat masks, cutouts, mesh data, and source-derived patches as `ORIGINAL_DERIVED`; retain source hashes, operation versions, and provenance.
8. Begin with CPU skinning in PixiJS and GSAP-driven bone/parameter tracks. GPU skinning requires later evidence and approval.
9. Do not unconditionally reactivate `/v2/localize`. Grounding and segmentation are replaceable ports; exact models/libraries are chosen by benchmark evidence.

## Consequences

- The system gains an asynchronous derived-media subsystem and V2 renderer path.
- Initial latency can overlap the parent decision period after Gate A.
- The same L4 requires explicit GPU admission, memory metrics, and bounded timeout/fallback.
- Every topic has a safe path, but not every topic is promised a bespoke skeleton.
- Old clients and failed/slow preparations continue through V1.

## Rejected alternatives

- A second general Qwen semantic request for localization: duplicate latency and unreliable geometry.
- Inline mesh payloads through the WebView bridge: exceeds the bounded command envelope.
- Generative redraw or inpainting: violates original-art authority.
- Removing V1 at launch: no safe rollback or old-client compatibility.
