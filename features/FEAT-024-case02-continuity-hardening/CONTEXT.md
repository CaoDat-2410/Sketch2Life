# FEAT-024 — Case 02 resilience and experience continuity

## Status

`IMPLEMENTED_WITH_LIGHTNING_SMOKE_PENDING`

The user approved `plan/PLAN.md` on 2026-09-15. The bounded implementation
and offline verification are complete. The remaining release gate is a real
case 01/case 02 Lightning Studio smoke with the pinned local model weights.

## Problem statement

The second real multimodal demo pair passes deterministic media validation but
fails before catalog selection:

- image: `features/FEAT-023-catalog-contract-hardening/test-assets/demo-case-02/input-image-framing-safe.png`;
- audio: `features/FEAT-023-catalog-contract-hardening/test-assets/demo-case-02/narration.wav`;
- media validation: `PASS`;
- ASR projection: `ASR_UNAVAILABLE` with empty transcript;
- VLM: `VISION_SCHEMA_INVALID` / `OUTPUT_MAPPING_FAILED`;
- all age bands: `AI_FAILED` because the shared scene understanding is
  unavailable.

The current VLM boundary is strict enough to protect the contract, but it does
not provide enough bounded structural repair/diagnostic detail for a different
real drawing. Separately, the successful butterfly output exposes continuity
debt: planned video continuity is reported as if a real video had been
rendered, age-specific objective text can drift from the actual activity, and
the video-to-off-screen bridge is generic.

## Goal

Make the backend demo resilient to the second real input while preserving
fail-closed safety and provenance, and make the generated experience explicit
about:

1. what is directly grounded in the child's drawing;
2. what is a related educational expansion;
3. what the video is planned to set up;
4. what has actually been validated after video generation (currently nothing,
   because video remains deferred).

## In scope

- VLM structured-output diagnostics and bounded, semantics-preserving repair.
- ASR failure observability and real-AI smoke coverage for case 02.
- Age-variant objective/goal alignment, especially the 0–3 butterfly route.
- Direct-continuation versus related-expansion classification in the semantic
  catalog.
- Planned versus actual continuity scoring.
- Typed video-to-off-screen activity bridge content and provenance.
- Offline corpus, case 01 regression, and case 02 Lightning smoke evidence.

## Out of scope

- UI integration.
- Actual video generation or video provider selection.
- PixiJS rendering implementation.
- Production approval of demo catalog rows.
- Storing raw VLM output, prompts, tokens, credentials, or real child data.

## Dependencies and constraints

- FEAT-023 catalog revision and its 200-row variant contract remain the active
  catalog baseline.
- The case 02 media pair remains replaceable and immutable by hash.
- No fixture recommendation, fixture transcript, or fixture VLM result may be
  injected into the real-AI smoke.
- Firebase Storage/Firestore/Realtime Database remain forbidden.
- The existing V1 projection remains readable for compatibility; new
  continuity semantics must be versioned rather than silently redefining a V1
  field.

## Evidence baseline

The supplied case 02 result is recorded as the implementation starting point:
`VISION_SCHEMA_INVALID`, `OUTPUT_MAPPING_FAILED`, `ASR_UNAVAILABLE`,
`gate_a_status=UNAVAILABLE`, and `ready_age_bands=[]`. The existing FEAT-023
offline report remains valid for catalog coverage, but it does not yet prove
real ASR/VLM success or video continuity.
