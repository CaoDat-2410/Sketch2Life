# FEAT-020 Implementation Decisions

## DEC-020-01 — Application-level orchestration

The workflow is coordinated by `BackendAiWorkflow` in the application layer. Providers are injected through the existing ASR and vision ports; the orchestrator does not import provider SDKs. This keeps domain/application behavior independent from Qwen, faster-whisper, Lightning, and future UI adapters.

## DEC-020-02 — Real adapters only for acceptance

The acceptance path constructs `QwenVisionAdapter` and `FasterWhisperAsrAdapter`. Typed fakes are useful only for local contract smoke checks and are not used by the public E2E test. If runtime readiness fails, the command reports a typed failure instead of substituting fixture data.

## DEC-020-03 — Static PixiJS asset catalog

PixiJS assets are resolved from the checked-in catalog and render-intent files. The runtime selects existing assets and preserves the original child drawing. AI-generated asset creation is outside this demo run and the PixiJS runtime itself is deferred.

## DEC-020-04 — Four age bands in one invocation

The default demo runs all four supported age bands (`0-3`, `3-6`, `6-9`, `9-12`) from the same validated input. A derived seed controls candidate ordering while avoiding immediate reuse when alternatives exist, so repeated runs are reproducible for debugging without producing one hard-coded result for every band.

## DEC-020-05 — Demo operator compatibility

Decision records use the explicit `DEMO_OPERATOR` actor required by the demo plan. The existing P1 semantic-anchor contract currently restricts its confirmation actor enum to `CAREGIVER`, `GUIDE`, and `PROJECT_OWNER`; the workflow therefore records the compatible contract value `PROJECT_OWNER` inside the anchor set while retaining `DEMO_OPERATOR` in the decision audit trail. This is an intentional compatibility boundary, not an implicit bypass.

## DEC-020-06 — Video is a typed deferred boundary

Video generation is not implemented in this slice. Each successful band emits a `VIDEO_DEFERRED` record with the learning objective, scene context, and provider boundary needed by the next feature. The workflow still reaches the activity bridge and feedback/history stages.
