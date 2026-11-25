# Plan Rev17 — subject confirmation projection and activity handoff

## Status

APPROVED under Addendum 23. This is a narrow repair required to continue the already-approved real synthetic Parent E2E on run `c1004974-7634-4399-a55f-3d4fc1cbee62`.

## Evidence and defect

- The real Modal drawing request succeeded and returned a valid `butterfly` result.
- The Parent subject-confirmation endpoint returned HTTP 202. PostgreSQL records the run in `PREPARATION_REVIEW`, subject `butterfly`, understanding revision 1, and a `SUBJECT/CONFIRM` decision targeting revision 1.
- The subsequent `GET /v1/story-runs/{run_id}` projection still presents the original candidate snapshot without the adult-confirmation decision. The mobile `isConfirmedRunSubject` guard therefore rejects the confirmed server state as stale and never calls `GET /v1/activities`.
- The controller also starts activity loading immediately after `setSubjectConfirmed(true)`. React state updates are asynchronous, so that first call can read the old `false` closure and show `SUBJECT_NOT_CONFIRMED` without calling the backend.

## Objective

Make the persisted subject decision visible in the run read model and pass the confirmed run explicitly to the activity loader. Preserve the immutable VLM result snapshot; derive only the client-facing confirmation decision from the current persisted review decision.

## Scope

1. In the Parent run read projection, detect a `SUBJECT/CONFIRM` decision for the current understanding revision and authorized run owner. Present `CONFIRMED_BY_ADULT` or `CORRECTED_BY_ADULT` consistently with the persisted subject label, without rewriting the stored VLM snapshot.
2. In the mobile Parent controller, call activity loading with the just-confirmed/latest run as an explicit source so it does not depend on a React state update having committed.
3. Add focused regression coverage for the backend read projection and the mobile handoff.
4. Rebuild/restart only the API and Parent app pieces required by these source changes, then continue the same synthetic run through activity selection, story review, video admission/generation and playback under existing approvals and gates.
5. Record API status, elapsed time, Modal call refs, output artifacts, screenshots and any terminal failure in FEAT-085 evidence. Do not resubmit any accepted or ambiguous AI call.

## Acceptance criteria

- A confirmed Parent run's read response contains the persisted subject label and adult-confirmed candidate decision for the same understanding revision.
- The VLM result snapshot and provenance remain unchanged.
- The activity list endpoint is reached once after subject confirmation; a catalog/AI activity result is displayed or a specific downstream error is captured.
- Story generation can start only after an activity is selected and the existing context/profile/safety gates pass.
- No fixture outputs, direct worker calls, DB writes, quota/safety bypass, or duplicate AI submissions.
- Focused tests pass; then the same run is exercised on Android with ADB.

## Out of scope

- Changing product policy, canonical SRS, worker prompts/models, Modal deployment/limits/billing, quota rules, consent gates, or video pipeline implementation.
- Creating a second Parent run or another drawing inference for this defect.
- Commit or push.
