# FEAT-018 new mobile UI → backend Lightning integration plan

- Status: AWAITING_APPROVAL
- Plan revision: 1
- Feature: `FEAT-018-live-image-canvas-flow`
- Implementation status: not started
- Requested by: project owner, direct request on 2026-09-18

## Goal

Connect the newly added `apps/ui-mobile` demo to the existing Sketch2Life backend's
development-only live-understanding route, so the screen flow can receive a validated proposal
from the already implemented backend → Lightning adapter when the developer configures that
provider. Preserve the existing mock experience as the default and preserve adult review at Gate A.

## Current facts and constraints

- The new UI currently defaults to mock behavior and points its generic API client at `/api`;
  those generic endpoints do not exist in the current FastAPI app.
- The backend exposes `POST /v1/live-understanding`. It accepts only the allowlisted
  `integration-fixture-v1`, loads its synthetic image/audio from the backend fixture directory,
  and calls the existing backend-only Lightning ASR/Vision adapters when
  `SKETCH2LIFE_AI_PROVIDER=lightning_dev` and the endpoint/token-file settings are configured.
- The new UI's camera/gallery and voice controls are visual placeholders: they do not capture or
  record actual media. Therefore this plan sends no image/audio bytes and does not claim that the
  visible sample artwork is what Lightning analyzes.
- Existing screens after Gate A, including story/video, activity recommendation/detail, and
  feedback, have no matching live backend endpoints in this branch and remain fixture/demo data.
- FEAT-017's Lightning provider contract, credentials boundary, and backend adapter are reused;
  this plan does not replace them or introduce a second provider contract.

## Proposed scope

1. Add an explicit public configuration switch for the UI, e.g. `EXPO_PUBLIC_USE_LIVE_AI=true`,
   plus a backend base URL setting usable for Expo web, Android emulator, and a developer's LAN
   device. Mock mode remains the default. No provider URL, token, or SDK credential enters the app.
2. Add a typed UI client for `POST /v1/live-understanding`, sending only the fixed fixture ID,
   a generated demo session/request ID, and `expected_session_version=1`.
3. Validate the returned envelope and map its ASR transcript, VLM entity/action proposals, status,
   and Gate-A requirement into the existing screen model. Render actual returned proposals on the
   Gate A screen; keep adult confirmation mandatory and do not infer Gate-A approval from the AI.
4. Make live loading, retry, and failure visible. A live request failure must not silently display
   mock results. Keep the current deterministic simulation when live mode is off.
5. Clearly label live mode as using the backend's synthetic fixture. Do not imply that the current
   placeholder camera/microphone uploaded media.
6. Support the Expo web development origin with a narrow local-only CORS allowlist if required;
   do not use wildcard origins or enable permissive CORS in staging/production by default.
7. Update `apps/ui-mobile/BACKEND_INTEGRATION.md` with the actual route, current limitations,
   backend/Lightning configuration references, emulator/LAN URL guidance, and secret-handling
   instructions. Do not copy credentials into frontend environment variables.

## Explicit exclusions

- Real camera/gallery selection, microphone recording, or arbitrary media upload/inference.
- Real child or personal data; only the checked-in synthetic backend fixture may reach Lightning.
- New public/session contracts, FEAT-018 contract-freeze changes, authentication, database or
  persistence work.
- Wiring story/video/activity/feedback screens to nonexistent backend endpoints; those remain
  clearly identified demo/fixture content.
- Runpod, production deployment, Android release, or any provider credential in the mobile bundle.
- A live Lightning request during implementation/verification. Automated tests use injected/fake
  provider transport; a real provider smoke run remains separately gated on configured endpoint,
  token file, and explicit run approval because it can consume account quota.

## Expected implementation files

- `apps/ui-mobile/src/config/apiConfig.ts`
- `apps/ui-mobile/src/services/api.ts`
- `apps/ui-mobile/src/services/api.types.ts`
- `apps/ui-mobile/src/context/AppContext.tsx`
- `apps/ui-mobile/src/screens/Flow2Screens.tsx`
- `apps/ui-mobile/BACKEND_INTEGRATION.md`
- Local-development CORS configuration and tests in the backend, only if needed for Expo web.
- Feature-local implementation/verification notes under
  `features/FEAT-018-live-image-canvas-flow/evidence/`.

Any material expansion beyond these paths/scope requires a revised plan and approval addendum.

## Acceptance criteria

- [ ] Mock mode remains the default and the existing demo works without the backend.
- [ ] With live mode enabled and the backend configured, the UI calls only
      `POST /v1/live-understanding` with `integration-fixture-v1`; the UI sends no media bytes or
      provider credentials.
- [ ] A valid backend `PROPOSAL` is rendered on the Gate A screen with transcript/entity data and
      an explicit adult-confirmation requirement.
- [ ] Invalid, failed, timed-out, or unreachable live responses show a retryable error and never
      silently fall back to mock data.
- [ ] Gate A cannot be skipped by the processing screen or accepted automatically from AI output.
- [ ] The app contains no Lightning URL/token/SDK credential, and local web CORS is exact-origin
      allowlisted and disabled outside local development unless explicitly configured.
- [ ] UI TypeScript check and web export pass; focused live-route/settings/CORS backend tests pass;
      applicable repository architecture/security/harness checks pass.
- [ ] Evidence records commands, environment class, fixture identity, and test result without
      provider credentials, raw media, prompts, or raw provider output.
- [ ] Actual Lightning-provider smoke status is reported as `NOT_RUN` unless separately approved
      and configured; fake-transport tests are not described as proof of a live provider call.

## Verification plan

- UI: validate mock and live configuration, response validation/mapping, Gate A presentation,
  retry/error behavior, `pnpm --dir apps/ui-mobile exec tsc --noEmit`, and web export/bundle scan.
- Backend: run focused existing Lightning client/live-understanding/settings tests and any new
  local-CORS tests with fake transport only.
- Repository: run architecture, harness, repository-security validators and `git diff --check`;
  preserve/identify any pre-existing findings separately.
- Manual local smoke: exercise the UI against the backend route with injected test adapters or a
  configured local fake service; do not contact Lightning during this task.

## Risks and rollback

- A configured Lightning Studio may be unavailable, incompatible, or over quota. Mock mode remains
  a one-toggle rollback, and a real provider smoke is not a prerequisite for offline integration
  verification.
- UI controls currently simulate image/audio input. This integration demonstrates the backend to
  Lightning path with a known synthetic fixture, not arbitrary user-media inference.
- In live mode, provider failures must remain visible so the user is not misled by mock results.

## Approval gate

This document is a plan only. No implementation is authorized until the project owner approves
this exact revision and the approval is recorded in the FEAT-018 `approvals/TASK_APPROVAL.md`.
