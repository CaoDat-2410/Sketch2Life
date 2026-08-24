# FEAT-005 Backend and experience plan

- Status: AWAITING_APPROVAL
- Plan revision: 1
- Implementation status: NOT_STARTED
- Owner: Person 4

## Scope

FastAPI facade, session state machine, command/event persistence, job records, artifact lineage, experience planner, art/learning job join, reviewed-cache resolver, Wan2.2 generation boundary, media validation/fallback, feedback, deletion workflow, and E2E orchestration.

## Acceptance criteria

- [ ] Lifecycle transitions and recovery/abandon paths are explicit and version-checked.
- [ ] Async jobs carry expected session version and stale completion is discarded.
- [ ] ExperiencePlanV2 keeps activity/objective identity stable across all phases.
- [ ] Reviewed cache is checked before real generation.
- [ ] Video generation/validation failure produces a valid still+narration fallback.
- [ ] Ready package contains art animation, learning asset, validation/provenance, and ActivityHandoff.
- [ ] Feedback and fixture-only deletion workflow are auditable.
- [ ] E2E evidence covers the complete flow and screen/off-screen transition.

## Handoffs

- Integrates contracts from Persons 1-3.
- Publishes session/job/API contracts for mobile and evaluation.

Implementation is blocked until this plan is approved.
