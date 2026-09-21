# FEAT-018 Plan Revision 2 — UI Mobile to Backend/Lightning Demo Workflow

**Status:** AWAITING_APPROVAL  
**Approval record:** None. Do not implement until the user explicitly approves this revision.  
**Branch:** `codex/feat-018-contract-plan`  
**Scope target:** A coherent, demo-ready caregiver workflow, roughly 80% of the product experience, with video deliberately excluded.

## User intent and planning assumption

Connect the existing `apps/ui-mobile` screens to the backend so a presenter can demonstrate the complete non-video workflow rather than a UI-only simulation. For this plan, “about 80% of production” means the critical path is genuinely interactive and backend-backed, including drawing/photo selection, voice capture, AI results, caregiver gates, activity guidance, and feedback. It does not mean production-grade identity, durable storage, operational resilience, or real-child-data readiness.

The demo will use newly captured or selected media on a test device and synthetic/consented demonstration content only. Media and session state are temporary and development-only. No video generation/playback integration, production deployment, Firebase data storage, or real child data is in scope. Lightning credentials and provider URLs remain backend-only. A live Lightning smoke test is a separately gated validation step requiring configured secrets and explicit confirmation of the test data/provider cost; the default end-to-end automated path must also work with a deterministic local fixture provider.

## Current-state findings

- `apps/ui-mobile` contains the desired screens, but capture, recording, processing, scene results, story, activities, and most feedback are currently mock or local-only.
- `apiConfig.ts` defaults to `USE_MOCK_API: true`; `api.ts` silently substitutes mock responses on request failures.
- The advertised `/api/...` routes in `BACKEND_INTEGRATION.md` are not implemented by the current FastAPI application.
- The backend currently exposes `/health` and `/v1/live-understanding`. The latter accepts a fixed synthetic fixture id, invokes backend-side Lightning adapters, and returns a proposal requiring Gate A; it does not accept device media or implement the full session/activity/feedback lifecycle.
- Existing session/gate contracts and the fixture-only Lightning path can inform the design, but they do not by themselves provide a UI-ready API workflow.
- The video player is a static placeholder and is intentionally excluded from integration. The non-video story screen must still provide a useful static scene/storyboard preview so the workflow does not dead-end at that point.

## Goals

1. Make the existing UI’s non-video critical path operate against a versioned backend contract.
2. Replace fake camera/gallery and voice controls with actual device capture/selection and safe upload to the local development backend.
3. Keep AI provider details, credentials, and asset-selection policy on the backend; return typed, explainable results the UI can render and let the caregiver correct.
4. Make Gate A and Gate B explicit backend state transitions; the UI cannot bypass them by navigating directly to a later screen.
5. Provide a deterministic fixture-backed demo/test path, plus an opt-in Lightning development path using synthetic/consented media.
6. Keep video as the only intentionally unconnected workflow surface and make that boundary visible in the demo.

## In scope

### UI workflow

- Preserve the current visual direction and screen order.
- Wire dashboard/child selection to a demo-safe local session context; do not add an account or production identity system as part of this task.
- Implement image selection/capture (camera and gallery) with preview, retake, basic size/type validation, and upload progress/error/retry feedback.
- Implement actual microphone recording, playback/re-record, permission-denied handling, recording limits, and transcription/upload progress. Do not silently submit a fake recording.
- Show real backend processing state, actionable errors, and retry/resume behavior instead of timer-only `runAiSimulation` behavior.
- Render Gate A values from the backend proposal, allow caregiver review/correction, and submit an explicit approval/edit/reject decision.
- Render a static story/scene preview (text plus still illustration/asset references where available); do not call or embed video generation/playback.
- Render backend-recommended activities, details, materials, and safety notes; support Gate B confirmation/checklist and submit its decision.
- Submit feedback to the backend and show acknowledged success/failure without mock-success fallback.
- Ensure debug navigation or test shortcuts cannot mark a gate complete or bypass backend state validation.

### Backend and contracts

- Define versioned request/response schemas and state transitions for a demo session: create/resume, upload drawing/audio, start/inspect analysis, Gate A decision, story/scene preview, activity recommendation/detail, Gate B decision, and feedback.
- Use opaque session identifiers, session version/ETag or equivalent optimistic concurrency, idempotency for retried mutations, and typed domain errors.
- Validate media MIME type, size, duration where applicable, and request ownership/session association. Use temporary local development storage with explicit cleanup/retention behavior; do not introduce Firebase Storage, Firestore, or Realtime Database.
- Adapt current Lightning interfaces behind backend ports. Provider credentials and endpoint configuration stay in ignored local environment/secret files and never enter UI bundles, logs, screenshots, or committed fixtures.
- Return structured AI output and asset references/metadata suitable for UI rendering; the backend is authoritative for role/safety filtering. UI may display and collect corrections but must not infer trusted safety decisions from labels.
- Provide a deterministic fixture provider and contract tests so the workflow is repeatable without network/provider credentials. Keep any live Lightning test opt-in and isolated.
- Define local CORS allowlist only if the supported Expo Web demo requires it; native-device access uses the configured local backend host. Document Android emulator host mapping and never ship a Lightning URL/token to mobile.

### Documentation and evidence

- Replace stale `/api/...` mock-first instructions with the implemented `/v1/...` contract and explicit fixture-vs-Lightning run modes.
- Add a short demo runbook, supported device/platform assumptions, sample synthetic media provenance, and troubleshooting for permissions/network/backend/provider failures.
- Store automated test reports and demo evidence in this feature’s own `evidence/` directory. Any new visual assets require provenance and the project’s visual approval workflow; do not generate or apply new artwork in this plan phase.

## Out of scope

- Video generation, video API calls, video playback integration, and production video infrastructure.
- Production authentication, multi-user authorization, durable cloud media/session storage, account management, and deployment/monitoring hardening.
- Real child data or unattended provider calls on real child media.
- Paid/live Lightning smoke without separately confirming credentials, input data, and cost/quota implications.
- Rebuilding the UI design system, replacing Expo, or adding unrelated asset-library expansion.
- Committing secrets, `.env`, provider tokens, real media, or generated private data.

## Proposed implementation sequence (only after approval)

1. **Contract and state design:** map UI fields/screens to FEAT-018 contracts; settle session state/version/idempotency and error semantics; update feature context/ADR if a material architecture choice is needed.
2. **Backend vertical slice:** implement schemas, application use cases, provider/storage ports and local adapters; add deterministic fixture flow; enforce Gate A/B server-side and media limits.
3. **Backend verification:** contract/unit/API tests for valid path, retries, stale versions, invalid media, rejected/edited gates, and prohibited gate bypass; verify fixture Lightning adapters without contacting an external provider.
4. **Device input:** implement camera/gallery and microphone capture with platform permissions, previews, validation, and uploads; verify iOS/Android or explicitly record supported demo target if hardware is unavailable.
5. **UI workflow integration:** remove silent mock fallbacks for the integrated path; wire processing, Gate A, static story preview, activity/Gate B, and feedback; preserve retryable states and backend authority.
6. **End-to-end demo and docs:** run backend plus UI on the supported target using synthetic/consented media; capture evidence; update setup/runbook. Only after this may the user separately authorize an opt-in live Lightning smoke.

## Acceptance criteria

- A presenter can start at the dashboard and complete the non-video critical path using a real image chosen/captured on device and a real audio recording, with all data submitted to the local backend.
- The default fixture-backed workflow produces a stable, repeatable analysis/storyboard/activity result without Lightning credentials or external network access.
- The Lightning development mode can be configured exclusively on the backend and is covered by adapter/configuration tests; no secret, provider endpoint, or provider token appears in the mobile bundle or repository.
- Backend session state is authoritative: Gate A must be resolved before story/activity progression; Gate B must be resolved before completion/feedback; invalid, stale, duplicate, or out-of-order requests return typed errors and do not silently advance state.
- Caregiver-visible AI proposal fields are editable/rejectable at Gate A; the resulting accepted/corrected state is what downstream UI receives.
- Activity content includes backend-returned materials and safety notes, and Gate B checklist/decision persists for the demo session.
- Feedback is actually submitted; network/backend failure is surfaced and retryable rather than reported as success.
- Video remains uncalled and unintegrated; the static story preview prevents a dead end and its controls do not falsely imply a playable video exists.
- No synthetic timer or debug shortcut can masquerade as successful AI processing or completed gates in the normal demo route.
- Automated checks cover contracts, state transitions, UI API behavior, and at least one full fixture-backed end-to-end run.
- Documentation identifies the demo-only/privacy boundary, supported target, setup, failure modes, and evidence location.
- `python tools/validate_repository_security.py` passes before any eventual commit/push; implementation does not commit or push unless separately requested.

## Risks and decisions to resolve during implementation

- Device media capture may require native permission/configuration changes and testing on physical hardware; platform limitations must be reported rather than masked.
- Current Lightning integration is fixture-oriented; if its configured endpoint cannot accept arbitrary uploaded media in the available dev environment, the real-media UI demo can use the deterministic local fixture result, while live-provider support remains explicitly separate. Do not claim a live real-media Lightning path until verified.
- The current backend contract may not yet define persistence across process restarts. This demo plan requires only temporary session continuity while the local backend runs; durable persistence is production work.
- The phrase “80%” is treated as workflow completeness, not an objective production-readiness score. Production security, privacy, reliability, accessibility, and deployment gates remain future work.

## Approval gate

This is a planning artifact only. No code, endpoint, environment, or UI changes are authorized by this document. Implementation may begin only after the user explicitly approves Revision 2 and the approval is recorded in `approvals/TASK_APPROVAL.md` as required by repository governance.
