# FEAT-018 full workflow debug and optional ASR integration plan

Status: APPROVED
Owner: shared integration
Scope: Android Emulator demo; synthetic/non-child image; backend-owned AI; no video

## 1. Purpose

Make the BaoVC React Native workflow honest and executable from input to output:

`image input -> optional narration input (audio or typed text) -> backend admission -> optional ASR -> Lightning Vision -> typed understanding result -> Gate A -> P1/activity -> Gate B -> Pixi/original-art handoff -> feedback`

This plan first reconciled the current code and contracts, then guided the approved implementation.
The owner approval and exact plan hash are recorded in the feature approval record.

## 2. Baseline findings

### Frontend

- `apps/ui-mobile/src/context/AppContext.tsx` calls the versioned image workflow for session,
  image admission, understanding, Gate A, P1, Gate B, renderer and feedback.
- The visible voice control is currently a local timer/toggle with a static transcript. It does not
  capture audio, request microphone permission, upload audio, call ASR, or submit typed narration.
- The current `VoiceScreen` is a dev-navigable screen, not an automatic step after image upload;
  `CaptureScreen` currently uploads the image and jumps directly to `ai_processing`. A text fallback
  must therefore be visible in the real capture/narration path, not hidden behind the unused voice
  route.
- Live analysis errors can be nested inside `payload.failure`; the UI previously collapsed them to
  `Backend không trả kết quả phân tích.`. A sanitized nested-error display patch is currently
  uncommitted and must be validated as part of this work.
- Mock scene/activity data remains as initial UI state and must not be used as a silent success path
  once the live workflow is selected.
- `video_player` and `StoryVideoResponse` are still present as legacy/mock navigation artifacts;
  they must be removed from the live reachable flow or explicitly marked out-of-scope so the demo
  cannot imply that video was generated.

### Backend

- The current `/v1/sessions/{session_id}/understanding` command is image-only and calls the injected
  `LightningVisionV2Adapter` after image admission.
- Existing ASR contracts and adapters exist, but the old `/v1/live-understanding` route is
  fixture-only and is not the session workflow used by the Android UI.
- The current session workflow has no audio upload/admission command and no narration input union.
- `MobileWorkflowResultV1` represents a typed blocked result through a payload; the UI must inspect
  the nested raw-understanding failure without weakening the contract.
- Settings load `.env` relative to the process working directory. Starting Uvicorn from the repo
  root can silently produce `ai_provider=disabled` even when `backend/.env` is configured. Startup
  diagnostics and a deterministic config path are required.

### Lightning

- `tools/lightning_vision_v2_server.py` exposes `/health` and `/v2/vision` only.
- `/v2/vision` may return HTTP 200 with a typed `FAILED` Vision result; HTTP status alone is not
  an inference-success signal.
- The server must expose a sanitized outcome log (`SUCCEEDED` counts or typed `error_code`) without
  logging image bytes, prompt text, provider output, tokens, or personal/child data.
- ASR must be an explicit, versioned backend-only provider path. The mobile client must never know
  Lightning credentials or provider URLs.

## 3. Owner decisions recorded — 2026-09-21

1. The image is mandatory. Narration is optional, with exactly one of `NONE`, recorded audio, or
   typed text when supplied.
2. Typed text is used directly as the transcript/context input and is marked with explicit
   `TEXT_TYPED` provenance. It is not converted to speech and is not sent through ASR.
3. Recorded audio is transcribed by `faster-whisper` in the Lightning environment. Vietnamese
   auto-detection is the initial language behavior unless a later contract adds an explicit hint.
4. The expected output is the typed Vision/ASR proposal plus Gate A review, followed by the
   existing P1/Pixi/activity flow. Video remains excluded.

These decisions are approved for implementation by the owner instruction recorded in the feature
approval addendum below. Live provider execution remains owner-triggered only.

## 4. Contract and state-machine work

Create a versioned narration input contract rather than adding ad-hoc fields to the existing
image command:

- `NarrationInputV1` discriminated union: `NONE`, `AUDIO`, `TEXT`.
- `AUDIO` carries an opaque audio artifact reference, content hash, MIME/size/duration metadata,
  admission provenance, language hint and ASR profile.
- `TEXT` carries bounded text, normalized language metadata and explicit `TEXT_TYPED` provenance.
- `NONE` preserves the current image-only behavior with `narration_status=NOT_SUPPLIED`.
- The command records one correlation ID and idempotency key for the full understanding attempt;
  provider calls are backend-only and never automatically retried.
- Preserve source hashes and provenance. Never label typed text as model-generated ASR.
- Define typed failure rows for image admission, audio admission, ASR timeout/model/runtime/schema
  failure, Vision failure, source mismatch, stale session version and invalid input combination.
- Add explicit transition fixtures:
  `CREATED -> MEDIA_ADMITTED -> UNDERSTANDING_RUNNING -> GATE_A_PENDING` on success, with
  `RECAPTURE_REQUIRED`/`BLOCKED` terminal branches and no Gate A bypass.
- Keep Gate A mandatory and preserve exact identity through P1, ExperienceSpec, Gate B, Pixi,
  handoff and feedback.

## 5. Backend implementation plan

### B1 — Configuration and observability

- Make backend config loading deterministic from the backend project root while preserving process
  environment override precedence.
- Add startup-only sanitized diagnostics: provider mode, endpoint path, base-url-present flag,
  token-file-present flag, model profile and whether the Vision/ASR adapters were constructed.
- Add provider outcome logs with correlation/request ID and typed status only. Redact payloads,
  media, secrets and provider response bodies.
- Add a non-provider readiness check that proves configuration/model-path presence without spending
  Lightning credits.

### B2 — Media and narration ingress

- Add bounded multipart audio upload with server-side content sniffing, size/duration limits,
  hash verification, temp-file cleanup and synthetic/non-child demo policy.
- Add typed-text command with length/language limits and no media artifact requirement.
- Store image/audio/text only in the existing ephemeral backend adapters for this demo; preserve
  application ports for future authenticated durable storage.
- Reject unsupported combinations before any AI call.

### B3 — AI orchestration

- Extend the session understanding application service to accept the narration union.
- For `AUDIO`, call one backend ASR adapter on Lightning, validate the typed result, then continue
  to Vision. For `TEXT`, skip ASR provider execution and map the supplied transcript through a
  clearly marked typed-text adapter. For `NONE`, preserve image-only behavior.
- Call Lightning Vision only after image admission and input checks pass.
- Validate both provider outputs against strict versioned schemas, preserve correlation/source
  identity, map to the Gate A raw-understanding contract and return a truthful result.
- No fixture substitution, silent mock fallback, automatic retry or video request.

### B4 — API and compatibility

- Add the minimum versioned routes under the existing session boundary for audio upload and
  narration selection; do not reuse the fixture-only `/v1/live-understanding` route.
- Keep old fixture route tests unchanged.
- Export/update OpenAPI and add request/response examples with redacted values.
- Add backward-compatible image-only behavior for clients that send `NONE`.

## 6. Lightning implementation plan

- Keep `/v2/vision` as the Vision V2 endpoint and make its typed success/failure outcome visible in
  logs.
- Add an explicit ASR endpoint using the approved ASR contract and the Lightning-hosted
  faster-whisper runtime, or document a separate approved ASR service if the current Studio cannot
  load Whisper. Do not overload `/v2/vision` with audio.
- Validate bearer auth, content hash, input bounds and request identity before model execution.
- Return schema-valid typed failures for auth, model unavailable, timeout, malformed output and
  unsupported audio; never return raw exception text.
- Run a no-credit health/readiness test first. The owner alone performs live AI smoke tests under
  the existing approximately 25-credit ceiling.

## 7. Frontend implementation plan

- Replace the recording timer with a real Android audio recorder compatible with the current Expo
  dev-client build; request microphone permission only when the user taps record and handle denial,
  cancel and max-duration states.
- Add a narration section to the existing BaoVC capture/voice UI with a visible text input fallback
  for non-speaking users. The control has three explicit choices: no narration, record audio, or
  enter text. Text submission uses the backend typed-text branch and is visibly labeled as typed
  input; the image remains independently required. The text box is mounted on the reachable
  `CaptureScreen` narration card; the recorder can remain a dedicated child screen/modal, but the
  submit action must return to the same session and not bypass the image admission state.
- Show one deterministic progress state machine: image admission -> narration admission/ASR (if
  selected) -> Vision -> Gate A. Remove fake timer progress and static transcript success.
- Disable duplicate submits while a request is active; after timeout/provider failure, allow only an
  explicit user retry with a new idempotency key and visible credit warning.
- Render the returned transcript with source/provenance, Vision claims, confidence/ambiguity and
  typed error code. Do not navigate to Gate A on an empty or failed result.
- Keep the current BaoVC layout and existing downstream P1/Gate B/Pixi screens, but drive their
  content only from backend payloads. Preserve the original drawing and the no-video wording.
- Remove the video screen from the live workflow/dev quick-switch and prevent `MOCK_STORY_VIDEO`
  from being presented as a successful AI result. Keep only a truthful static/original-art preview.
- Keep `AuthTokenProvider` optional and keep all future auth/save seams backend-owned.

## 8. Verification matrix and exit criteria

### Contract/backend tests

- Image-only success remains green.
- Audio success: image admission -> audio admission -> ASR -> Vision -> Gate A payload.
- Typed-text success: no ASR provider call, explicit typed provenance, Vision receives the
  transcript context.
- None success: no ASR call and `NOT_SUPPLIED` narration.
- Reject corrupt/oversize/unsupported image and audio, missing hashes, stale versions, duplicate
  idempotency keys, missing consent marker, unsupported combinations and empty text.
- Provider failures: auth, timeout, model unavailable, malformed schema, source/correlation
  mismatch; no raw payload leakage and no automatic retry.
- Backend restart/TTL loses the demo session honestly.

### Frontend/emulator tests

- Android Emulator can pick a synthetic image, record audio or type text, submit once, wait for the
  correct stage, review Gate A, continue through P1/Gate B, open source-preserving Pixi and submit
  feedback.
- Permission denial, cancel, network loss, provider failure, timeout and retry are recoverable.
- No microphone permission is requested before the record action; no provider token/URL is present
  in the mobile bundle.
- No mock data appears as a successful live result and no video route/player is invoked.

### Live acceptance

- First run `/health` and readiness only.
- Owner manually runs one image-only smoke, one typed-text smoke and—if approved—one audio/ASR
  smoke, checking Lightning logs and balance after each. Codex does not trigger live provider calls.
- Evidence is stored under this feature's `evidence/` directory, including request IDs, sanitized
  statuses, config fingerprint (not secrets), contract result and emulator screenshots.

## 9. Approval gate

Implementation was gated on:

1. The owner confirms the decisions in section 3 and approves the exact contract/state-machine
   scope, including the typed-text input fallback.
2. `features/FEAT-018-live-image-canvas-flow/approvals/TASK_APPROVAL.md` records the new scope,
   decision, date and plan hash.
3. The plan status changes from `AWAITING_APPROVAL` to `APPROVED`.

The gate is satisfied by the 2026-09-21 approval addendum. Live provider execution remains owner-only.

## 10. Implementation result — 2026-09-21

- Added `NarrationInputV1` (`NONE`, `TEXT`, `AUDIO`) and a session-local `NarrationReceiptV1`.
- Added bounded `/v1/sessions/{session_id}/media/audio` ingress with content sniffing, hash/size
  checks, session-version/idempotency handling and image-before-audio enforcement.
- Extended understanding orchestration so typed text goes directly to Vision context, audio calls
  backend-only faster-whisper ASR once before Vision, and ASR failure blocks before Vision.
- Added a strict `LightningAsrV2Adapter` plus `/v1/asr` on the existing Lightning server; the
  server loads faster-whisper lazily and returns the existing typed ASR Phase-A contract.
- Made settings load `backend/.env` deterministically from repo-root Uvicorn startup while keeping
  process environment precedence; startup logs expose only safe adapter/config presence flags.
- Connected BaoVC Capture to real optional narration controls. Android requests microphone permission
  only after the record tap; typed fallback is visible and uses `TEXT_TYPED` provenance. Audio upload
  and analysis use the current session version through a ref to avoid the upload-chain race.
- Removed video from the BaoVC developer quick-switch and corrected the AI checklist/copy so it no
  longer claims an AI request completed before the explicit analysis tap.
- Verified with `pnpm --dir apps/ui-mobile exec tsc --noEmit`, focused narration/image contract tests,
  and the full `backend/tests/contract` + `backend/tests/unit` collection using a writable temp
  directory. No live Lightning request was made.
