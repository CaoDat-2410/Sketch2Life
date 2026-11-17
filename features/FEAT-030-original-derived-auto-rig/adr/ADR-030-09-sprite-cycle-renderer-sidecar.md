# ADR-030-09: Capability-bound sprite-cycle renderer sidecar

- Status: Accepted for additive implementation under `approvals/TASK_APPROVAL.md` revision 1
- Date: 2026-10-02
- Feature: FEAT-030 with FEAT-028

## Context

The V3 Pixi show path can read one rights-cleared PNG per selected static asset and animate its
placement, but it has no frame-cycle transport or playback-clock integration. FEAT-028's 37 cycle
sheets now have owner visual approval, but their rights, crop/pivot/loop QA, catalog and production
runtime states are still gated. Reusing V3's static sprite type would misrepresent a 4-frame cycle and
make frame identity/hash failures difficult to diagnose.

## Decision

1. Preserve all current V1/V2/V3 contracts. Add `PixiSpriteCycleReadV1`,
   `PixiRendererShowEnvelopeV2`, and `RendererLoadCommandV4` as additive contracts.
2. A cycle read contains a stable cycle ID, behavior class ID, variant ID, bounded timing/placement,
   and exactly one static texture for transform-only motion or four per-frame PNG capabilities for
   frame animation. The renderer never accepts file paths, URLs, arbitrary code, or model-supplied
   asset locations.
3. The backend serves only immutable FEAT-028 `assets/approved/` derivatives whose manifest hash,
   owner visual approval, rights clearance, frame QA, catalog registration, renderer verification,
   and runtime eligibility all pass. Each frame is hash/byte/dimension checked and accessed through a
   short-lived single-purpose capability. The checked-in expansion currently fails closed because
   independent gates remain pending.
4. Pixi decodes every frame before playback and selects frames from the existing master show clock.
   Pause/seek/replay therefore cannot drift on a second ticker. One-shot sequences hold their final
   frame; looping sequences are bounded to their show beat. Teardown destroys textures/container.
5. The cycle is a companion, not a replacement or mask for the confirmed drawing. Backend placement
   must be within stage bounds and outside the padded Gate-A subject region; otherwise no cycle is
   issued. Existing Gate-A/B identity and fixed-camera/source-preservation rules remain authoritative.
6. `motion.object-slide.v1` is registered as a single-frame transform-driven slider, not a 4-frame
   animation; repeated poses are never reported as a sprite cycle.
7. Emit allowlisted structured events for eligibility, capability read, decode, ready, play and
   failure. Logs may include stable cycle/frame IDs, frame index/count and safe reason codes only;
   never pixels, child/source identifiers, crops, tokens, URLs, prompts or provider payloads.
8. Runtime remains disabled until the rights/provenance, technical QA, catalog, renderer, security
   and Android visual gates are separately recorded as passed.

## Consequences

- The renderer will have a real, testable frame-cycle path without changing old clients.
- Current generated/approved art can be inventoried and reviewed without becoming runtime-visible.
- The runtime cannot yet play these assets in the app; a blocked cycle is a typed outcome, not a silent
  fallback. Fresh Android visual acceptance remains mandatory after later gate clearance.
