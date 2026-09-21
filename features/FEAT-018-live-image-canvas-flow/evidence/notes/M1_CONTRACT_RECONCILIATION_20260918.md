# M1 contract reconciliation — 2026-09-18

Status: `PARTIAL — contract and reducer foundation implemented; API/OpenAPI and Android wiring remain open`.

Plan authority: `plan/UI_MOBILE_LIGHTNING_ANDROID_DEMO_PLAN_REV2_DETAILED.md`, image-only
scope-corrected SHA-256 recorded in `approvals/TASK_APPROVAL.md`.

## Completed in this slice

- Added strict `MobileWorkflowCommandV1` / `MobileWorkflowResultV1`, typed provenance/failure,
  `GateAConfirmationV1`, `SessionSnapshotV1`, `WorkflowJobV1`, `SessionGalleryV1`,
  `SessionJourneyEntryV1`, and identity-locked `FeedbackV1` schemas.
- Added a single request-ID adapter: `request_id` maps to FEAT-016 `command_id`; the
  idempotency key remains outside the reducer envelope. Added strict integer ↔ P4 `vN` and
  integer ↔ renderer decimal version adapters.
- Reconciled the FEAT-016 fixture reducer to candidate → immutable ExperienceSpec/fit → exact
  Gate B ordering. Retake clears dependent results; context requires explicit
  `completed_activity_ids`; Gate B checks activity/objective/template/spec IDs and versions.
- Corrected fixture identity for `ACT-0004` v2 to primary `OBJ_OBJECT_PERMANENCE` v1.
- Added backend renderer contracts for an approved-only Pixi manifest, source-locked
  `ArtAnimationPlanV1` wrapper around unchanged renderer protocol 1, bootstrap, and bounded
  discriminated playback events. The TypeScript mirror is strict; bridge JSON is capped at
  4096 bytes. Every plan object must retain the immutable source hash; supplemental manifest
  entries require both visual approval and rights clearance.
- Added application ports and thread-safe in-memory adapters for sessions, jobs, idempotency and
  artifacts. The `SessionSnapshotV1` and gallery schemas have no owner field and explicitly state
  that the demo is non-durable. Existing `IdentityTokenVerifier` / `VerifiedPrincipal` remain the
  provider-neutral future-auth boundary.
- Corrected the approved demo scope to image-only: no microphone permission, audio capture/upload,
  or ASR request. `narration_status` is `NOT_SUPPLIED`. Updated the approval plan hash; no live
  provider call or asset promotion was performed.

## Verification

- Backend contract/storage/P1 target set: 98 passed; Ruff passed.
- FEAT-016 runtime reducer tests: 13 passed; Ruff passed.
- Pixi renderer: 8 Vitest tests passed; TypeScript typecheck passed.
- Existing native fixture UI: 7 Jest tests passed; TypeScript typecheck passed.
- Pytest emitted a local cache-path warning (`WinError 183`) while writing `.pytest_cache`; tests
  passed and no cache cleanup was attempted.

## Remaining before M1 exit

- Add/validate the versioned session HTTP/OpenAPI surface and export a compatibility report covering
  every API/mobile/renderer producer-consumer pair.
- Validate the approved fixture manifest against the current registry and write the remaining
  migration/stale/error fixtures.
- Wire actual `apps/ui-mobile` session and image-only backend actions, then run the app on Android
  Emulator. Its present screens are still mock-first and still contain a video prototype route.
- Resolve the separate ADR-0005 amendment and cost/quota ceiling before any dynamic image is sent to
  Lightning. No such call is made by this evidence run.
- Individually review rights and visuals for FEAT-028 assets. All 144 remain `REVIEW_PENDING`, so the
  renderer manifest currently permits source-art-only operation and no supplemental asset.

## Auth/save boundary

This slice does not add sign-in, authorization claims, `owner_ref`, a save command, a database, or
object storage. Demo session state is process-local. Later explicit save must authenticate through a
verified backend principal and replace the in-memory adapters with backend-owned persistence; mobile
must not provide the account/owner identifier. That later work needs its own contract, privacy plan,
approval, and tests.
