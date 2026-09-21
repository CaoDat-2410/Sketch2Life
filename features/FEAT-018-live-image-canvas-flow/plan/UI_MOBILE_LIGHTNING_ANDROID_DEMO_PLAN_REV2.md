# FEAT-018 Revision 2 — Android Emulator UI-to-Lightning Demo

**Status:** AWAITING_APPROVAL — planning only; no implementation is authorized yet.  
**Branch:** `codex/feat-018-contract-plan`  
**Target:** One complete demo workflow, approximately 80% of the intended product experience, with video excluded.

## Decisions confirmed with the user

- Build and demo on Android Emulator first.
- The demo must send the actual selected/captured drawing image and actual recorded voice through the backend to Lightning and display the resulting AI output. A fixture response does not satisfy the Lightning demo acceptance criteria; fixtures are for automated/offline tests only.
- Session, uploaded media, and workflow state are temporary and last only while the local backend process/session is active. Authentication is deferred to a later feature.
- Video generation/playback remains out of scope. The story step will use a static text/illustration/storyboard preview so the non-video journey can continue.

## Objective

Connect `apps/ui-mobile` to a backend workflow so a caregiver can, on Android Emulator, select/capture a drawing, record speech, send both media inputs via the backend to Lightning, review/correct the AI interpretation, view a static story preview, review recommended activities and safety guidance, complete Gate B, and submit feedback. The backend owns provider access and authoritative workflow state.

“80%” means the main user journey is demonstrable and genuinely integrated. It is not a claim of production readiness, security certification, availability, or privacy compliance for real child data.

## Current-state baseline

- The Expo UI has the desired screens, but image capture, audio recording, AI processing, Gate A data, story, activities, and feedback are mostly mock/local state.
- UI API configuration defaults to mock mode and silently substitutes mock results after failures.
- UI documentation advertises `/api/...` routes, while the FastAPI app currently exposes `/health` and fixture-only `/v1/live-understanding`.
- The current live-understanding route accepts a fixed fixture ID and does not accept UI-uploaded media or manage the full session/Gate A/Gate B/activity/feedback lifecycle.
- Therefore this work needs a versioned UI-facing API and a dynamic-media Lightning path; merely pointing the UI at the existing fixture route is insufficient.

## In scope

### 1. Lightning feasibility and backend-only integration

- Before choosing adapter details, inspect the configured Lightning endpoint contract: accepted image/audio formats, request size/duration limits, authentication method, response schema, timeout behavior, and whether ASR and vision are separate endpoints/workflows.
- Define a provider port in the backend and implement the adapter for the configured Lightning endpoint(s). The mobile app sends media only to the backend; only the backend calls Lightning. No provider URL/token is bundled into the app.
- Map ASR/transcription and drawing/vision results into a typed application result, then into a caregiver-reviewable proposal. Preserve provider errors as safe, typed API errors without exposing secrets or raw provider diagnostics to the UI.
- Use only synthetic or explicitly consented demo media for provider verification. Do not log raw audio/image bytes, transcripts, child identifiers, or secrets.
- If Lightning cannot accept the uploaded image/audio in the available configuration, stop at that dependency and report the exact limitation for a user decision. Do not silently show fixture output as if it came from Lightning.

### 2. Versioned, ephemeral session API

Create/extend versioned `/v1` contracts for:

1. Create a demo session and return an opaque session ID/version.
2. Upload a drawing image and a voice recording as separate media resources associated with that session.
3. Start AI processing and retrieve its status/result.
4. Submit Gate A approval, correction, or rejection.
5. Retrieve the static story/scene preview and activity recommendations/details.
6. Submit Gate B checklist/decision.
7. Submit feedback and receive an acknowledgement.

Use an explicit state machine, approximately: `CREATED → MEDIA_READY → ANALYZING → GATE_A_PENDING → STORY_AND_ACTIVITIES_READY → GATE_B_PENDING → COMPLETE → FEEDBACK_SUBMITTED`. Exact names may follow existing FEAT-018 contracts. Gate decisions and ordering are enforced by the backend, not by screen navigation. Use session version/ETag (or equivalent) and idempotency for retried writes; return typed errors for stale, duplicate, invalid, or out-of-order requests.

Session metadata/state remains in memory for the life of the backend process. Uploaded bytes use a private temporary development directory with size/type/duration limits and cleanup on completion, expiry, and process restart; no durable database or cloud media store is added. Document this dev-only behavior and ensure temporary files are ignored and not included in evidence/commits.

### 3. Android Emulator media input and networking

- Replace fake capture controls with actual Android camera/gallery selection and microphone recording using the existing Expo stack where supported.
- Implement permissions, preview/playback, retake/re-record, validation, upload progress, retry/cancel, and clear permission/network errors.
- Verify emulator media availability and microphone behavior. Provide a documented synthetic image/audio sample path for repeatable demos if emulator camera hardware is unavailable; the selected/recorded bytes must still be uploaded and sent to Lightning.
- Configure the dev UI to reach the host backend through Android Emulator host mapping (normally `10.0.2.2`), without hard-coding a production or Lightning endpoint in the app.
- Keep local demo identity/session flow simple; no login/account/auth integration in this feature.

### 4. Connect the non-video UI journey

- Wire dashboard/session start, capture, recording, processing, Gate A, static story preview, activity list/detail, Gate B, and feedback to the versioned backend API.
- Remove silent mock-success fallback from this integrated route. Make fixture mode explicit and limited to tests/offline development; production-like Lightning demo mode must visibly report provider/network failure rather than fabricate success.
- Render Gate A proposal from backend data and submit caregiver edits/approval/rejection before proceeding.
- Render backend activity recommendations, materials, instructions, and safety notes; submit checklist and Gate B decision.
- Use existing approved asset metadata/references where available for static story illustrations; this feature consumes the current catalog but does not expand or regenerate the asset library. Backend-provided asset roles/IDs are treated as data, while the backend remains responsible for safety/role filtering.
- Replace video-player navigation with a clearly static preview/“video not included in this demo” state. No video API is called and no control implies that video exists.

### 5. Tests, docs, and evidence

- Unit/contract tests for schemas, state transitions, idempotency/version conflicts, upload validation/limits, provider error mapping, and gate bypass prevention.
- Provider-adapter tests use mocked Lightning HTTP responses; API/UI integration tests can use a deterministic fake provider. These tests do not count as the live Lightning demo.
- Android Emulator end-to-end verification must exercise uploaded demo media through the configured Lightning endpoint, then complete Gate A, static story preview, activity/Gate B, and feedback.
- Update `apps/ui-mobile/BACKEND_INTEGRATION.md` and add a concise runbook for backend/UI startup, emulator host mapping, provider config, temporary-data behavior, media permissions, and troubleshooting.
- Store test output/screenshots and verification notes under this feature's `evidence/` directory. Run repository security validation before any eventual commit/push.

## Explicitly out of scope

- Video generation, video API calls, video playback integration, and video infrastructure.
- Authentication, account management, durable session/media storage, database/cloud storage, production deployment, and operational monitoring.
- Real child media or production data handling; the demo uses synthetic/consented test media only.
- Mobile access to Lightning credentials/endpoints, Firebase Storage/Firestore/Realtime Database, or any new provider secret in source control.
- General redesign of the UI or expansion/regeneration of the asset library.
- Commit or push unless separately requested.

## Implementation sequence after approval

**Milestone 0 — Contract/provider feasibility.** Confirm the Lightning dynamic-input contract and limits; trace current FEAT-018 schemas, FEAT-017 provider configuration, and UI field mapping. Record any material architecture decision before implementation. If the configured Lightning service cannot accept image/audio, pause and request a decision rather than substituting a fixture.

**Milestone 1 — API and ephemeral backend session.** Define versioned contracts/state machine, in-memory session service, temporary media handling/cleanup, typed errors, concurrency/idempotency, and upload validation. Add contract and state tests.

**Milestone 2 — Lightning adapter.** Implement backend-only dynamic image/audio calls, transcription/vision orchestration, normalized result mapping, timeouts, safe error handling, and adapter tests. Keep all keys in ignored local configuration/secret files.

**Milestone 3 — Android input.** Implement real camera/gallery and microphone paths, permissions, preview/retry, and uploads. Verify emulator-to-backend networking.

**Milestone 4 — Workflow UI.** Connect processing, caregiver Gate A, static story, activity details/safety, Gate B, and feedback. Remove misleading mock fallback and guard direct navigation against server state.

**Milestone 5 — Demo verification.** Run deterministic tests, then an explicitly configured Lightning smoke with synthetic/consented media, followed by full Android Emulator walkthrough and evidence/runbook updates. Any provider call that may incur quota/cost must be confirmed before it is run.

## Acceptance criteria

1. Android Emulator can reach the local backend and complete the full non-video flow from drawing selection/capture through feedback.
2. Actual image and recorded/selected audio bytes are uploaded to the backend and forwarded to the configured Lightning endpoint; the displayed AI result is derived from that provider response, not a fixture.
3. A repeatable synthetic/consented demo input is available, and the runbook records exact setup and supported emulator behavior.
4. No Lightning token, provider endpoint, or provider credential is present in mobile code/bundle or committed files; no raw media/secrets are logged.
5. Session state is process-scoped; uploaded media is temporary and cleaned up according to documented completion/expiry/restart behavior.
6. Gate A and Gate B are enforced server-side; caregiver edits and checklist decisions are reflected in subsequent backend state; stale/out-of-order/bypassing requests cannot advance the workflow.
7. Activities include backend-provided materials and safety notes; feedback is submitted and acknowledged by the backend.
8. The story step is useful as a static preview, while video remains uncalled/unintegrated and clearly identified as excluded.
9. Provider failures, timeouts, permission denial, invalid/oversized media, and backend connectivity failures are surfaced as actionable, retryable states; none is reported as AI success.
10. Backend/API/UI tests pass, and a full Android Emulator Lightning walkthrough is recorded in feature evidence. Fixture-only tests cannot satisfy item 2 or item 10.
11. `python tools/validate_repository_security.py` passes before any eventual commit/push.

## Risks and boundaries

- The largest dependency is Lightning endpoint support for dynamic image/audio payloads and the exact ASR/vision workflow. This is the first milestone and a hard gate, not an assumption.
- Android Emulator camera/microphone availability depends on host configuration; media picker/fixture sample may be needed for deterministic selection, but still must travel through the real upload and Lightning path.
- A process-scoped session intentionally disappears on backend restart. The UI must show session expiry and offer a clean restart; persistence/auth is future work.
- This demo path is not approved for real child data or exposure beyond a trusted local development environment.
- “80%” is a workflow-completeness target, not a measured production-readiness percentage.

## Approval gate

This document is a plan only. No code/configuration/provider call is authorized yet. Implementation starts only after explicit user approval is recorded in `approvals/TASK_APPROVAL.md`. A live Lightning call will use synthetic/consented media and must be confirmed before execution if it may consume paid quota or incur cost.
