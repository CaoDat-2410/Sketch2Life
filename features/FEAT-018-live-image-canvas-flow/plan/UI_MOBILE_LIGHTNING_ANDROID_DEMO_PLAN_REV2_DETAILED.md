# FEAT-018 Shared Integration Addendum Rev 2 — Android / Lightning / Pixi Non-Video Flow

**Base plan:** FEAT-018 plan revision 2 (already approved for earlier isolated/offline slices; this addendum does not relabel or supersede it).  
**Status:** APPROVED — plan approval recorded in `approvals/TASK_APPROVAL.md`; implementation follows the gates/phases below. No provider call or asset promotion is authorized by approval alone.  
**Target branch:** `codex/feat-018-contract-plan`  
**Scope:** Android Emulator demo of the complete non-video FEAT-018 journey, including the PixiJS original-art canvas and P4 still/fallback/handoff flow. No video generation, video API, or video playback.  
**Contract status:** The FEAT-018 registry and approved revision-2 engine schemas are authoritative. Shared transport, Gate, Pixi manifest/plan and renderer event mappings are being reconciled against that registry before API/UI wiring. No parallel domain DTOs or silent version changes.  
**Canonical addendum:** This file is the approved integration plan. Other untracked `UI_MOBILE_LIGHTNING_*` files are earlier drafts, not separate approvals.
**Future account/save requirement:** Build current session/backend services behind replaceable repository and artifact-store ports so Firebase Authentication and backend-owned durable saving can be added later without changing FEAT-018 domain contracts. Auth and persistence remain out of this emulator-demo implementation.

## 1. Decisions and objective

Confirmed with the user:

- Android Emulator is the first build/demo target.
- The only demo media input is an actual selected/captured non-child synthetic/test image, sent by the backend to Lightning Vision with results derived from that call after the provider gate is cleared. The demo does not request microphone permission, record/upload audio, or call ASR. Fixture output is for tests/offline development only and cannot satisfy live-demo acceptance.
- Session and uploaded media are temporary and do not survive the local backend process/session. Authentication is deferred.
- PixiJS original-art animation, reviewed supplemental assets, P4 cache/fallback, activity handoff, gallery/session journey, and feedback are included. Video generation/API/playback are the only intentionally excluded media path; the video consumer identity remains in canonical `ExperienceSpecV1` but is not executed or rendered.
- “Review assets” means audit current generated atlases/sprites and rights/provenance, record per-sprite decisions, and expose only explicitly approved/applied entries to runtime. This plan does not mark assets approved by itself.

Objective: connect the `apps/ui-mobile` Expo prototype to FastAPI for a local Android Emulator demo. The required image-only, non-video path is: session → synthetic non-child image capture/selection → media validation → backend-only Lightning Vision → Gate A → adult context and deterministic P1 selection → version-locked Gate B/ExperienceSpec → PixiJS original-art reveal with approved asset overlays → P4 cache or whole-image fallback → supervised activity handoff → gallery/session read model → feedback. Narration remains explicitly `NOT_SUPPLIED`; no ASR lane is wired. `apps/ui-mobile` is the demo shell only; this does not declare it the production Android app or replace `apps/mobile`.

“About 80% of production” means workflow coverage, not production readiness. Use only a synthetic/non-child image. Consent does not waive the current no-real-child-data boundary. This is a trusted local development demo, not a real-child-data deployment.

## 2. Current-state baseline and constraints

- UI screens exist, but capture/recording, processing, scene data, story, activity data, and feedback are largely mock or local state. The UI defaults to mock mode and can silently return mock success after failures.
- UI integration notes advertise `/api/...`; FastAPI currently exposes `/health` and fixture-only `/v1/live-understanding`.
- Existing `/v1/live-understanding` requires a fixed fixture ID, does not accept media from the UI, and does not implement session state, caregiver decisions, activities, or feedback.
- Existing session/gate/media/P1/P3/P4 contracts and the fixture-only Lightning route are inputs to the design, not proof that arbitrary uploaded media is supported.
- ADR-0005 currently limits Lightning to fixture-only use on the normal low-credit account. Dynamic non-child demo-media inference therefore requires a separately approved ADR-0005 addendum before any live-provider implementation or call.
- FEAT-028 currently has 24 generated atlases / 144 indexed sprite IDs, but all visual/rights states are review-pending; its selector is not provider-wired or a public FEAT-018 contract. No such sprite may be treated as runtime-approved until individually reviewed and recorded.
- Repository constraints remain binding: Firebase Authentication only; no Firebase Storage/Firestore/Realtime Database; no provider credentials or endpoints in mobile; no secrets, real child media, or credentials committed.

## 3. Proposed architecture and data lifetime

```text
Expo Android Emulator
  └─ HTTPS/HTTP dev API ─> FastAPI session + application services
                              ├─ temporary media staging + FEAT-018 media validator
                              ├─ AiGateway → Lightning Vision adapter (image only)
                              ├─ RawUnderstandingResultV1 → Gate A → P1/ExperienceSpec
                              ├─ P3 Pixi manifest/animation plan + approved-only asset IDs
                              ├─ P4 cache/fallback + exact-identity activity handoff
                              └─ application ports → in-memory session/job/artifact adapters
                                  (future: verified principal + PostgreSQL/S3-compatible adapters)
```

- Android Emulator uses the configured host mapping (normally `10.0.2.2:<port>`); dev-only cleartext/network policy is scoped to the debug build and local demo. If Uvicorn must bind `0.0.0.0`, document and apply a host-firewall rule limited to the emulator/private test network; do not leave an unauthenticated API exposed on a shared/public network.
- Generate an opaque UUIDv4 `session_id` in the client at session creation so every command, including bootstrap, can carry the frozen session/version envelope. Session metadata, job state, idempotency records and gate state live in one backend process; run one Uvicorn worker only. No DB, durable queue, Firebase data store or object store is introduced.
- Application services depend on `SessionRepository`, `JobStore` and `ArtifactStore`-style ports; this demo supplies in-memory/session-temp adapters only. HTTP routers do not own mutable session state or write files directly. Keep opaque session/artifact IDs stable across adapters and keep storage keys/paths out of domain and mobile contracts. The later persistent adapters are separately planned; this interface seam is the only persistence preparation in this scope.
- Stage original media in a private, per-session temporary directory outside Git. Compute SHA-256 and preserve immutable source references; derived/normalized working copies point back to the original and never replace it. Delete source bytes when no retry needs them, and on session completion/TTL. Shutdown cleanup is best effort; run a startup janitor for stale FEAT-018-owned temp directories and document that abrupt power loss cannot guarantee secure erasure. Demo inputs are non-child and non-sensitive.
- Use a proposed 30-minute idle TTL, configurable for the demo and aligned with provider timeouts. Backend restart invalidates sessions/jobs; expired or missing sessions return a typed failure and the UI starts over. No resume across process restart.
- No auth in this feature, per the user’s local-demo decision, but this does not change the accepted Firebase Authentication architecture for future app/API access. Do not send names, exact DOB, account IDs, child photos, child voice, or identifying notes. Any P1 context is a fictional adult-entered demo profile and remains session-only.
- Distinguish command `actor_ref` from future session `owner_ref`. Current `actor_ref` is a random demo-local principal marker, not a Firebase UID or user ID; do not add an unreviewed owner field to frozen session contracts. Later auth resolves a verified principal server-side and authorizes ownership; the mobile client never assigns ownership by posting a user ID.
- Provider request/response bodies, tokens, media, transcripts, prompts, and raw model output are never logged/evidenced. Logs may include request ID, session ID hash/short ID, model/config profile, stage, duration, safe status/failure code, and artifact hashes only where the frozen evidence policy allows.
- Pending FEAT-028 atlas/sprite records are never passed to Pixi or Lightning. The selector receives only post-Gate-A, adult-confirmed topic text and the bounded descriptors of entries that have passed the separate visual + rights review.

## 4. Contract reconciliation and proposed HTTP mapping

The routes below are a transport proposal, not new domain contracts. JSON is UTF-8. Uploads use `multipart/form-data`; the backend owns validation and maps each accepted artifact to the existing versioned FEAT-018 contract. Before coding, export JSON Schemas, register fixtures, reconcile the open items below, and approve a compatibility report. Do not use lowercase UI states or invented story/activity/gate DTOs in place of the canonical contracts.

### 4.1 Known contract mismatches to close before implementation

| Gap found | Current authority/evidence | Required resolution before code |
|---|---|---|
| `request_id` / idempotency vs `command_id` | FEAT-018 freeze requires `session_id`, `expected_session_version`, `request_id`, and idempotency key on every request. FEAT-016 `CommandEnvelope` has `command_id`, `session_id`, `expected_session_version`, `actor_ref`; its `TransportEnvelope` has `command_id` but no idempotency key or actor. | Define a versioned HTTP transport wrapper in the canonical backend schema location. Map `request_id` to FEAT-016 `command_id` exactly once; carry `idempotency_key` and a non-identifying `actor_ref`; document that the wrapper adapts but does not fork domain contracts. Add positive, replay, key-conflict, and migration fixtures. |
| Session bootstrap cannot satisfy required envelope | FEAT-016 needs session ID and expected version. A server-generated ID would leave create-session without the required session identity. | Client generates an opaque UUIDv4 before `POST /sessions`; bootstrap carries that ID and `expected_session_version=0`. Server accepts only an unused ID. If the shared owner rejects this, record a reviewed explicit bootstrap exception before implementation; do not silently omit required fields. |
| Gate A schema differs between registry and executable type | Freeze lists `IntegrationGateDecisionV1` for A/B; current FEAT-016 `GateAConfirmation` carries meaning version/confirmed claim IDs/correction but is not versioned; current P1 schema implementation of `IntegrationGateDecisionV1` is Gate-B-only. | Before coding, decide and record one canonical Gate-A wire representation that preserves `meaning_version`, confirmed claim IDs, adult actor, expected version and optional correction. Version/freeze it with owner review and fixtures; preserve the separate FEAT-016 domain semantics. Do not put Gate-A decision fields into the Gate-B-only implementation or reuse a generic boolean. |
| Gate B executable type does not carry full Rev-2 identity | FEAT-016 `GateBApproval` carries activity/objective ID+version; the integration flow also locks template and `ExperienceSpec` refs/versions in `IntegrationGateDecisionV1`. | Choose one frozen Gate-B boundary that preserves activity, objective, template and spec refs/versions plus expected session version. Cross-validate any narrower FEAT-016 value; do not accept an approval that loses template/spec identity. |
| Current reducer orders Gate B before ExperienceSpec | FEAT-016 `filter_candidates()` currently enters `GATE_B_PENDING`; `approve_gate_b()` moves to `CANDIDATES_READY`; only then `attach_experience()` enters `EXPERIENCE_READY`. That order cannot let Gate B approve the exact `spec_ref` required by Rev-2. | Update and review the FEAT-016 reducer/transition fixtures before integration: valid filter → `CANDIDATES_READY`; compile + fit an immutable draft spec → `GATE_B_PENDING`; Gate B approves/blocks exact activity/objective/template/spec refs; only approval → `EXPERIENCE_READY`. Do not ship Gate B as a boolean or claim the present reducer already satisfies the freeze. |
| Retake is a state but has no reducer command | `MEDIA_RECAPTURE` exists and media upload accepts that state, but current aggregate has no explicit Gate-A retake command or downstream invalidation behavior. | Add a versioned idempotent retake command and reducer tests: clear proposal/P1/spec/P4/asset selection/handoff results, retain only allowed source status, then accept replacement media and require new validation/inference/Gate A. |
| Revision-2 engine schemas are not at same freeze level as registry | `CONTRACT_FREEZE.md` labels `SemanticAnchorSetV1`, `LearningFocusV1`, `ActivityTemplateV1`, `ExperienceSpecV1`, `ActivityFitEvaluationV1`, and `BridgeSentenceV1` as proposed until owner freeze; Pydantic fixtures already exist. | Treat them as proposed/test-only until this integration addendum explicitly freezes compatible schemas, versions, JSON Schema exports and fixtures. Fix the recorded ACT-0004/objective mismatch before selecting it in the demo. |
| Demo media scope must stay image-only | Shared media contracts can represent audio, but the approved demo path has no audio capture/upload and no ASR call. `narration_status` remains `NOT_SUPPLIED`; it is not successful empty ASR. | Accept only the required image part; preserve the immutable source/hash and image validation result. `RECAPTURE` blocks Vision. Do not request microphone permission or add an audio endpoint for this demo. |
| P1 context cannot be derived from drawing or age-band shortcut | `P1ContextV1` requires explicit adult-supplied exact fields; engine may return `MISSING_CONTEXT`. | Capture the required fictional adult-provided context for the demo or show `CONTEXT_REQUIRED`; do not infer age, readiness, materials, supervision, policy flags or prior activity from media. |
| P1 runtime required-field list is narrower than `P1ContextV1` | `P1ContextV1.missing_fields()` requires `completed_activity_ids`; current FEAT-016 `filter_candidates()` hard-rule set omits it. | Align the reducer/validator to every canonical P1 required field, including explicit empty completed-activity list when appropriate. Add one-negative-fixture-per-missing-field; never substitute an implicit default. |
| Pixi contracts exist as registry requirements but runtime is incomplete | Freeze names `PixiArtAssetManifestV1`, `ArtAnimationPlanV1`, `RendererBootstrap` and event protocol; `packages/art-renderer` currently has protocol types only. | Freeze/validate concrete renderer JSON schemas and bridge fixtures without changing protocol version silently. Preserve source hash and exact ExperienceSpec identity; fail to whole-image display on invalid bootstrap/plan. |
| P1/P4/renderer version encodings differ | Rev-2 `VersionedRefV1` uses integer versions; `LearningMediaRequestV1` uses `vN`; renderer protocol 1 uses canonical decimal strings. | Define strict lossless adapters (`1` ↔ `v1`, integer `1` ↔ renderer string `"1"`); reject zero, leading-zero, malformed, stale or ambiguous versions. Cache identity uses canonical IDs/versions plus renderer config—not media content. |
| Session TTL/job lifecycle fields are not frozen in the core snapshot | FEAT-016 `SessionSnapshot` has state/version/artifact/gate data; `JobSnapshot.status` is an unconstrained string. Current `LocalJobStore` uses `QUEUED`, `SUCCEEDED`, `FAILED`, `CANCELLED`, with no `RUNNING` state or progress percentage; TTL is also absent. | Add only a reviewed transport projection for expiry/last-job status. Either use the existing coarse job states honestly or approve a versioned `RUNNING`/progress extension; never fabricate progress. Freeze restart/TTL behavior in schema + fixtures before UI depends on it. |
| FEAT-028 candidate selection is internal, not public or provider-wired | Internal FEAT-028 contracts and allowlist validator exist; current 144 sprites remain `REVIEW_PENDING`; no Lightning selection call is wired. | Keep FEAT-028 contracts internal. Feed only the top bounded approved candidates and post-Gate-A adult-confirmed text to an explicit backend `AssetRanker` port; validate returned IDs against the approved catalog and renderer manifest. If no candidate, use typed no-match and preserve original art. |
| Gallery/feedback transport not fully implemented | Frozen registry requires session journey read model and `FeedbackV1`; P4 reconciliation requires exact activity/objective/renderer identity and typed result/fallback. | Define only the transport projection of those canonical contracts; feedback records non-identifying actor and exact IDs/versions. Do not invent a second persisted history or personal profile. |
| Video fields are required in `ExperienceSpecV1` despite video being excluded | `ExperienceSpecV1` includes `video_plan`; fit evaluation includes `video_continuity`. | Keep the mandatory plan/score as inert identity/continuity metadata required by the schema. The demo makes no video request, creates/stores no video artifact, returns no video URL, and renders no player. `LearningMediaResultV1.generation_called` must be `false` for this demo. If metadata itself is unacceptable, that is a separately versioned contract change, not an implementation shortcut. |

### 4.2 Transport envelope, concurrency and idempotency

Proposed wrapper name `MobileWorkflowCommandV1` and response `MobileWorkflowResultV1` are pending registry approval; they are not frozen domain schemas. The request wrapper contains `contract_name`, `contract_version`, `request_id`, `idempotency_key`, `session_id`, `expected_session_version`, `actor_ref`, and a typed `payload`. `request_id` maps to `CommandEnvelope.command_id`; the adapter must not generate a second unrelated command ID. Use one version source: body `expected_session_version` must equal `If-Match` when that header is present.

- Every API request, including reads and multipart uploads, carries the required session/version/request/idempotency metadata. Read keys are trace/deduplication metadata only and never mutate state. A read may return a newer `observed_session_version`; a mutating command with a stale expected version is rejected.
- Every successful mutating command increments session version once. Job progress polling does not increment session version on every poll; the accepted command and terminal result each follow the reviewed aggregate/version transition policy. Return ETag and observed version consistently.
- Idempotency scope is `(session_id, operation, idempotency_key)`. Same key + same normalized request replays the recorded result for the in-memory session lifetime; same key + different payload returns the frozen typed idempotency failure. Restart clears the idempotency store with the session.
- All result envelopes carry `contract_name`, `contract_version`, status, provenance and typed failure when failed. Transport maps domain failures to HTTP status without inventing replacement domain codes. Reject unknown fields (`extra=forbid`) unless the approved compatibility report explicitly selects another policy.
- Generate UUIDv4 IDs, never encode names/media in IDs or URLs. Demo `actor_ref` is an opaque local caregiver/operator label, not an account identifier.
- For future authenticated saving, keep `actor_ref` (who performed a command) distinct from `owner_ref` (which account owns a saved session); the latter is a separate, versioned persistence/authorization contract to design later. Never accept a client-supplied owner ID as authority.

### 4.3 Proposed endpoint table (transport only)

All endpoint names are provisional until the OpenAPI addendum is reviewed. Payloads are the named canonical contract or an approved transport wrapper around it; table does not authorize parallel DTOs.

| Endpoint | Purpose and canonical payload/result | State/gate rule |
|---|---|---|
| `POST /v1/sessions` | Create in-memory session using client UUID, version `0`, locale/platform metadata; returns `SessionSnapshot`-compatible projection and TTL. | One worker/process; no durable persistence. |
| `POST /v1/sessions/{id}/media/image` | Multipart `command` JSON part plus `file` part. Return opaque `SourceMediaReferenceV1` and current snapshot; never return path or bytes. | Image only. Replacement only after a reviewed retake transition and invalidates dependent artifacts. No audio upload route in this demo. |
| `POST /v1/sessions/{id}/media-validation` | Return exact `MediaValidationResultV1` for original image ref/hash and validator policy version; audio remains `NOT_SUPPLIED`. | `RECAPTURE` blocks Vision; UI must replace the image before analysis. |
| `POST /v1/sessions/{id}/understanding` | Start bounded job. Backend maps the validated image to FEAT-003 `VisionUnderstandingRequestV2/ResultV2` through the approved adapter and maps it to FEAT-018 `RawUnderstandingResultV1` with `narration_status=NOT_SUPPLIED`. | Backend-only `AiGateway`; Gate A remains required; no client-to-Lightning or ASR call. |
| `GET /v1/sessions/{id}/jobs/{job_id}` | Read `JobSnapshot` plus typed result/failure; safe progress only. | Poll with 2-second initial interval, backoff to 10 seconds; use ETag/job version and stop at terminal/background. |
| `POST /v1/sessions/{id}/gate-a` | Versioned adapter for Gate-A confirmation: exact meaning version, confirmed claim IDs, adult actor and optional correction. | Cannot pass without adult confirmation; retake invalidates understanding and downstream results. |
| `POST /v1/sessions/{id}/p1-context` | Exact adult-supplied `P1ContextV1`. | Missing any required field yields `CONTEXT_REQUIRED`; no inference from the image. |
| `POST /v1/sessions/{id}/p1-filter` | Return `P1FilterResultV1` and, when eligible, exact selected activity/objective/template refs. | Exactly one confirmed primary anchor, one objective and one curated template; no eligible result stays blocked, never fabricate a recommendation. Success enters `CANDIDATES_READY`. |
| `POST /v1/sessions/{id}/experience/prepare` | Compile/validate immutable `SemanticAnchorSetV1`, `LearningFocusV1`, `ActivityTemplateV1`, `ActivityFitEvaluationV1`, and draft `ExperienceSpecV1` from the eligible P1 result. | Fit must pass; bind the spec ref/version before entering `GATE_B_PENDING`. No video generation or renderer call. |
| `POST /v1/sessions/{id}/gate-b` | Submit/return exact `IntegrationGateDecisionV1` with activity/objective/template/spec refs and versions. | Adult approves/blocks the prepared spec; stale/mismatched/missing context blocked. Only approval enters `EXPERIENCE_READY`; not a UI-only checklist. |
| `GET /v1/sessions/{id}/experience` | Read Gate-B-approved `ExperienceSpecV1`, `PixiArtAssetManifestV1`, `ArtAnimationPlanV1`, and renderer bootstrap projection. | Original drawing remains immutable; `video_plan` is present only as a required inert field in the current `ExperienceSpecV1`. No video asset/status/URL, video call or playable control is exposed. |
| `POST /v1/sessions/{id}/asset-selection` | Backend-internal FEAT-028 candidate context and validated selected IDs; mobile sees only safe selected descriptor/manifest refs. | Only after Gate A. Candidate context from `AdultConfirmedTopicV1`; only approved/applied + rights-cleared descriptors. On no match return typed authoring-queue proposal, keep source-art-only mode. |
| `POST /v1/sessions/{id}/learning-media/resolve` | Exact `LearningMediaRequestV1` → `LearningMediaResultV1`. | Preserve activity/objective/renderer versions; cache hit/miss/fallback identity exact; `generation_called=false` for non-video demo. |
| `POST /v1/sessions/{id}/renderer-events` | Validated protocol-v1 `RendererBootstrap`/`PlaybackEvent` bridge events. | Bounded event allowlist and payload size; renderer cannot mutate session decisions or policy. |
| `POST /v1/sessions/{id}/handoff` | `ActivityHandoffV1` exact session/spec/activity/objective/template identity. | Available only after Gate B and P4 resolution; no independent activity re-selection in renderer. |
| `GET /v1/sessions/{id}/gallery` | Session-scoped journey projection from original source, Gate A, Pixi/P4, handoff and feedback statuses. | Not a general asset gallery, not durable, no media bytes/transcript dump. |
| `POST /v1/sessions/{id}/feedback` | `FeedbackV1` exact actor/activity/objective/spec refs and recorded status. | Allowed only at the approved journey point; no child diagnosis/personality or identifying free text. |
| `GET /v1/sessions/{id}` | Compact `SessionSnapshot` projection and safe last-job status. | Resume only while same backend process and TTL remain live. |

Multipart uses a JSON `command` part plus one binary part. React Native must not set a manual multipart `Content-Type`; let the native networking stack add the boundary. Remove the API client's global JSON content-type for this request only. Verify SHA-256 from accepted original bytes, inspect file signatures, reject spoofed MIME/extensions, store no original filename, and enforce byte/duration/pixel limits after confirming provider limits. Candidate caps and all limits belong in versioned config and tests, not hard-coded UI assumptions.

### 4.4 Mapping and semantic invariants

1. Preserve immutable source `artifact_ref` and SHA-256 in `SourceMediaReferenceV1`; derived/normalized bytes retain parent reference. Never overwrite original drawing.
2. `MediaValidationResultV1` has PASS/RECAPTURE, ordered stable image reasons, an explicit absent-audio state and policy version. This demo always records narration as `NOT_SUPPLIED`; it does not construct an empty ASR result.
3. Successful Vision requires source match and full `ModelProvenanceV1` (provider, exact model, adapter/config versions). Failures use existing `AdapterFailureV1` codes (`VALIDATION_REJECTED`, `TIMEOUT`, `PROVIDER_ERROR`, `RATE_LIMITED`, `MALFORMED_OUTPUT`, `PROHIBITED_FIELD`, `SOURCE_MISMATCH`). No raw provider body escapes the adapter.
4. `RawUnderstandingResultV1` preserves Vision and ASR separately, claim source, uncertain/ambiguous observations, conflicts, confidence bounds, source hash and `gate_a_required=true`. Do not alias FEAT-017 flat V1. Provider confidence is shown only when its meaning/calibration is documented; otherwise label it as an uncalibrated estimate or omit it. No psychological/personality or eligibility claims.
5. Gate A confirms meaning only; it does not approve P1 suitability or safety. P1 consumes the adult-confirmed anchor and exact adult context; Gate B freezes exact activity/objective/template/spec versions.
6. `ExperienceSpecV1` is the single identity source for original-art animation and off-screen activity. Its required video-plan data is inert continuity metadata only. No narration/story is generated in this image-only demo; do not fabricate a separate story schema or video screenplay.
7. Pixi manifests and plans reference immutable original + bounded derived regions. P4 `LearningMediaRequestV1` cache key is versioned identity/config only—never raw media, transcript, provider output, credential, signed URL or personal metadata. `LearningMediaResultV1` must preserve identity through HIT/MISS/timeout/fallback.
8. `ActivityHandoffV1` and `FeedbackV1` are emitted from the same approved identity; gallery is an in-memory projection, not a new child profile or persistence layer.

## 5. Session/job state machine and invariants

Do not invent `created`, `analysis_running`, `story_ready`, `complete`, `expired`, or lowercase states in the domain. Session state uses the FEAT-016 `SessionState` enum exactly: `CREATED`, `MEDIA_RECAPTURE`, `UNDERSTANDING_PROPOSED`, `GATE_A_PENDING`, `CONTEXT_REQUIRED`, `CANDIDATES_READY`, `GATE_B_PENDING`, `EXPERIENCE_READY`, `HANDOFF_READY`, `FEEDBACK_RECORDED`. Current `LocalJobStore` uses `QUEUED`, `SUCCEEDED`, `FAILED`, `CANCELLED`; it has no `RUNNING`/percent progress. Use those coarse values or freeze an extension first. The reducer sequence below is a required reviewed correction to current FEAT-016 behavior, not a claim that its implementation already matches.

| Session state | Accepted operation/event | Resulting state | Required guard |
|---|---|---|---|
| `CREATED` | Store source image ref; validate image | `CREATED` or `MEDIA_RECAPTURE` | Image required; audio remains `NOT_SUPPLIED`; no inference before validation PASS. |
| `MEDIA_RECAPTURE` | Replace/remove invalid input and validate again | `CREATED` or remain `MEDIA_RECAPTURE` | Invalidate all derived artifacts and prior jobs. |
| `CREATED` | Start understanding job | Session stays `CREATED`; job status changes independently | Single active job; idempotent key; Vision image is non-child synthetic/test image only. |
| Understanding completed | Persist `RawUnderstandingResultV1` proposal | `GATE_A_PENDING` | Typed success + provenance; adult gate mandatory. |
| `GATE_A_PENDING` | Confirm/correct claims | `UNDERSTANDING_PROPOSED` | Actor, expected version, meaning version and claim IDs must match. |
| `GATE_A_PENDING` | Request retake | `MEDIA_RECAPTURE` | New reviewed reducer command clears all derived results; no stale proposal survives. |
| `UNDERSTANDING_PROPOSED` | Run P1 with context missing | `CONTEXT_REQUIRED` | Return exact missing fields; no inferred context. |
| `UNDERSTANDING_PROPOSED` or `CONTEXT_REQUIRED` | Submit exact adult context/run deterministic P1 | `CANDIDATES_READY` only for a valid result; otherwise no state advance and return typed `P1FilterResultV1` | Missing fields enter/remain `CONTEXT_REQUIRED`; no eligible activity is not mislabeled as missing context. |
| `CANDIDATES_READY` | Compile immutable spec and fit evaluation | `GATE_B_PENDING` | Spec and fit pass first; all exact identity refs/versioned before adult review. |
| `GATE_B_PENDING` | Approve exact spec | `EXPERIENCE_READY` | Gate-B decision binds activity/objective/template/spec refs+versions; stale/mismatch rejected. |
| `GATE_B_PENDING` | Block/reject spec | Remain pending or explicitly return to candidates through reviewed command | Do not mark ready or handoff; candidate change requires a new spec and approval. |
| `EXPERIENCE_READY` | Resolve P4 media and prepare handoff | `HANDOFF_READY` | Same spec identity; renderer failure uses typed fallback, not new activity/objective. |
| `HANDOFF_READY` | Record feedback | `FEEDBACK_RECORDED` | Feedback references exact actor/session/activity/objective/spec. |

The required state correction changes current FEAT-016 behavior and therefore must be separately recorded/frozen and tested before integration: today `confirm_gate_a()` moves to `UNDERSTANDING_PROPOSED`; valid `filter_candidates()` currently skips `CANDIDATES_READY` to `GATE_B_PENDING`; `approve_gate_b()` currently returns to `CANDIDATES_READY`; and `attach_experience()` is only allowed from `CANDIDATES_READY`. Align the reducer with this plan so ExperienceSpec exists before Gate B and the approved exact spec advances to `EXPERIENCE_READY`. Do not add enum members just to represent screen progress. Read-only gallery/job reads never advance state. Session version changes only through reviewed aggregate command/result transitions; UI route navigation never advances a gate. A process restart drops all sessions/jobs/idempotency state; TTL cleanup drops expired state/media, and resume then starts a new session.

## 6. Typed failures and HTTP translation

Wire failures retain the canonical `contract_name`/version, typed failure, provenance and request/session IDs. The FastAPI boundary maps failure type to HTTP status; it does not replace domain failure codes with a parallel `error.code` vocabulary. Before implementation, publish a one-page mapping fixture covering at least:

| Condition | Canonical behavior | HTTP class (proposed) | UI action |
|---|---|---|---|
| Invalid request/unsupported contract version | Existing validation/transport rejection | 400 | Show safe error; no retry until corrected. |
| Unknown session/artifact/job | Typed not-found adapter result | 404 | Offer restart. |
| Stale session version/illegal state/idempotency key reused with different payload | FEAT-016 rejection code; return current observed state/version | 409 | Refresh snapshot; do not replay mutation with a new key automatically. |
| Expired in-memory session | Typed unavailable/expired result approved in addendum | 410 | Restart; explain demo session is temporary. |
| Upload too large/unsupported/unreadable | `MediaValidationResultV1` and typed validation failure | 413/415/422 | Fix selection or recapture. |
| Missing P1 context / P1 no eligible candidate | Exact `P1FilterResultV1` status + reason codes | 200 blocked result or agreed 422 mapping | Ask adult for required context or explain no safe activity. |
| AI adapter timeout/provider/rate/malformed/source mismatch | `AsrResultV1`, Vision V2 or `RawUnderstandingResultV1` typed failure | 502/503/504/429 mapping | Retry only when typed failure allows; never show fabricated fixture success. |
| P4 fallback/block/cache issue | `LearningMediaResultV1` status/reason + exact identity | 200 typed result unless transport itself failed | Continue with documented still/reveal/handoff fallback or stop if BLOCKED. |
| Renderer protocol/source hash mismatch | Typed renderer/manifest failure, preserve source | 422/409 mapping after freeze | Fall back to source-image view; no activity gate bypass. |

Never include stack traces, provider bodies, endpoint URLs, credentials, local paths, media, prompt, transcript or personal metadata in errors/logs/evidence. Redact error details and cap user-readable strings. Only the accepted versioned failure semantics determine retries.

## 7. Lightning boundary, data scope and cost gate

- Live vision input is restricted to non-child synthetic/test images, e.g. generated flat 2D art or a deliberately fictional adult-created sketch. No child photographs, identifiable people, school records or real child artwork. The demo is image-only: no audio is captured, uploaded, or sent to ASR. Consent does not expand this boundary.
- The UI uploads to FastAPI only. FastAPI validates and stages locally, then calls provider adapters through `AiGateway`; no mobile Lightning endpoint/token, signed URL, or direct provider request.
- Current route is fixture-ID-only. ADR-0005 explicitly treats Lightning as fixture-only on the normal low-credit account. Before any dynamic media call, approve a narrowly scoped ADR-0005 addendum covering provider endpoints/models, data boundary, adapter inputs, payload/content type, quota/cost ceiling, timeout/rate/retry policy, retention/logging and rollback. Until then, run tests with mocks/fixtures only; do not claim live connection.
- Read the configured Lightning API docs and current backend adapter implementation. Verify the Vision image input method, supported image containers, byte/pixel limits, timeout, response schema and networking/auth. ASR/audio is outside this demo. No provider-side media hosting unless separately reviewed; prefer backend-transmitted bytes.
- Every provider call is backend-only, has request correlation/provenance but no raw body logging, and is bounded by timeout/retry. User-facing output shows the actual provider-derived `RawUnderstandingResultV1`; failure stays a failure. No implicit mock fallback in demo mode.
- Asset selection is a separate optional text-only model call through a backend `AssetRanker` port and must be included in the ADR cost/quota estimate. It receives only post-Gate-A confirmed topic labels and a bounded list (max 8) of eligible descriptor candidates; never receives the drawing/image bytes, transcript, file paths, hashes or frame coordinates. Backend validates the returned ≤4 asset IDs and roles against the exact eligible catalog before making a Pixi manifest.
- Automated tests use fixtures/mocked ports. The first live smoke test is a separately confirmed user action after ADR approval and quota/cost is known; use only a synthetic non-child image.

## 8. Asset review, coverage and PixiJS runtime

Current baseline is 24 generated atlases / 144 indexed sprites. Every entry is `REVIEW_PENDING`; license/rights are not cleared; there are zero runtime-eligible sprites. “Plan approved” is not asset visual approval. The source atlases remain under FEAT-028 `assets/generated/` unless each frame is explicitly reviewed and its provenance/rights recorded.

### 8.1 Asset review gate

Review each of 144 frames individually and record reviewer/date/decision/reason in FEAT-028 `assets/REVIEW.md` and its catalog. Check:

- exact semantic label, aliases and topic tags; avoid culturally narrow or misleading labels;
- flat 2D hand-drawn style fit with children’s source drawings, outline/fill/color consistency and visual legibility at target size;
- correct crop/frame bounds, transparent background, no neighboring-frame bleed, no hidden watermark/text, no duplicate/broken sprite;
- correct role (`SUBJECT`, `ENVIRONMENT`, `PROP`, `EFFECT`), appropriate scale and intended use; `confusable_with` lists meaningful near-matches;
- child-safe content, no stereotype/unsafe depiction, and age-appropriate visual treatment;
- source/generation provenance, atlas hash and a cleared rights basis before runtime eligibility.

Only assets with explicit per-frame visual approval, `review_status=APPROVED` or `APPLIED`, `runtime_eligible=true`, and `license_status=CLEARED` can enter the FEAT-028 candidate shortlist, `assets/approved/`, `assets/applied/`, or Pixi runtime. Never mark a whole atlas approved based on a single representative frame. Do not bypass review by loading a generated atlas directly from its pending path.

### 8.2 Coverage and AI choice

Build a coverage matrix across broad everyday/nature/animal/transport/food/place/people/creative/fantasy/science themes, roles and common aliases; run Vietnamese/English topic fixtures including confusable pairs. Current 24-family coverage is broad but finite and cannot guarantee every topic a child may invent. A missing match must produce the existing typed `PixiTopicAssetCandidateContextV1(status=NO_MATCH)` plus `PixiTopicAssetAuthoringQueueProposalV1`; the product still shows the original drawing and does not fabricate/generate a replacement at runtime.

If the coverage audit identifies high-priority gaps, propose supplemental flat assets into FEAT-028 `assets/generated/`, record imagegen provenance/hash, perform per-frame visual and rights review, then promote only after approval to `assets/approved/`/`assets/applied/`. This plan does not generate/promote assets or self-approve them. Static catalog selection and AI selection must share the same allowlist and deterministic post-validation; AI can rank only candidates the backend has already filtered to approved, licensed, role-compatible entries. Ranking is a choice aid, not authority to invent asset IDs or semantic claims.

### 8.3 PixiJS / P3 / P4 integration

- Preserve original drawing as immutable visible source. PixiJS scene layers: original image, optional approved transparent sprite overlays, bounded source-art regions/masks, accessibility labels, and controls. Overlays complement—not cover, recolor, or replace—the child/adult-created source art.
- Compile `PixiArtAssetManifestV1` with source ref/hash, atlas and sprite IDs/versions, extraction status and provenance. Compile `ArtAnimationPlanV1` with bounded targets/motions/durations tied to the same `ExperienceSpecV1` anchor/objective/template. Validate both on backend and again in renderer; never accept filesystem paths from AI.
- Run PixiJS in controlled React Native WebView if the Expo target supports it, behind existing `RendererBootstrap` protocol v1. If the prototype cannot safely host the bridge, record the dependency/decision before porting; do not invent an unversioned WebView message format. Bridge messages are size-bounded, sequenced, allowlisted and tied to session/spec/renderer instance IDs.
- P4 resolves reviewed cache or safe fallback using `LearningMediaRequestV1` / `LearningMediaResultV1`. Preserve exact activity/objective/renderer-plan identity for cache hit, miss, timeout and fallback. For this image-only demo the permitted fallbacks are `WHOLE_IMAGE_REVEAL` or `SUPERVISED_HANDOFF`; narration fallback is not used. `generation_called=false`; P4 must not call a video/image-generation provider.
- Renderer failure or no approved topic asset falls back to the original-image canvas/static whole-image reveal. It must not block supervised handoff if the canonical `ActivityHandoffV1` permits that fallback; otherwise show the typed blocked reason and stop. The no-video screen is an explicit static still/reveal, never a fake video player.

## 9. Android UI integration and workflow contract

`apps/ui-mobile` is the target for this emulator demo only. It is an Expo SDK 52 / React Native 0.76.7 prototype, currently mock-first and missing image-picker/WebView dependencies. It is not a substitute for canonical `apps/mobile` or a production-ready native app. Keep changes local to the approved feature and update backend integration notes/runbook. Demo mode has no auth token, microphone permission or saved-session action; keep the API/client auth-header injection point optional so a future Firebase ID token can be added without leaking Firebase-specific logic into screens or domain contracts.

| Screen/workflow | Backend-owned data/contract | UI behavior |
|---|---|---|
| Start/resume | session snapshot, version and TTL | Create client UUID session; keep only opaque ID in in-memory app context. Resume only while backend process has session; otherwise explain restart. |
| Image input | source ref + media validation | Use Android picker/camera with preview/retake; real demo image must be synthetic/non-child. Validate locally for UX and repeat all checks server-side. |
| Image validation/analysis | `MediaValidationResultV1`, `WorkflowJobV1`, `RawUnderstandingResultV1` | Render ordered image recapture reasons; no Vision on RECAPTURE; narration remains `NOT_SUPPLIED`; poll 2 sec then back off to max 10 sec, pause in background, stop terminal. |
| Gate A | versioned adult claim confirmation | Show source image next to claims, uncertainty and conflicts; confirm/correct/retake; cannot continue until server accepted. |
| P1 context/filter | `P1ContextV1`, `P1FilterResultV1` | Ask for missing adult-entered fictional context; show typed no-eligible state; no screen-level assumptions/default approval. |
| Topic assets / Pixi | approved descriptor/manifest, `PixiArtAssetManifestV1`, `ArtAnimationPlanV1`, renderer protocol | Show original art first; add only manifest IDs accepted by backend. If no-match, source-only scene. Reduced-motion/renderer error fallback. |
| Experience/activity/Gate B | `ExperienceSpecV1`, `ActivityFitEvaluationV1`, `IntegrationGateDecisionV1` | Show one objective/activity consistent with spec. Gate B confirms exact identity and versions; no separate UI re-selection that changes contract identity. |
| P4/offscreen handoff | `LearningMediaResultV1`, `ActivityHandoffV1` | Show cache/fallback state truthfully, then hand off to same activity. No video route/control/URL. |
| Gallery/feedback | session projection, `FeedbackV1` | Show this session journey only; submit non-identifying feedback with exact activity/objective/spec refs. No durable account or child profile. |

Implementation checks before selecting packages/build mode: choose an SDK-52-compatible image picker; decide Expo Go vs custom dev client/native build based on WebView/native module requirements; configure only required camera/photo permissions and denial/retry UI (never microphone); wire API base URL to emulator host mapping `10.0.2.2:<backend-port>`; use cleartext only in debug if local HTTP is unavoidable; document private host binding/firewall. Do not claim emulator capture or WebView works until built and run on the target emulator. Remove global JSON `Content-Type` from multipart calls. Remove silent mock fallback; mock mode must be a deliberately selected test configuration and visibly distinct from live mode.

## 10. Phased implementation and deliverables

User approval and the repository’s written task approval are recorded. Implementation proceeds only through the gates in this plan; provider calls and asset promotion remain separately gated. Each phase stores plan/status/contract/test evidence under the owning feature; do not write to shared evidence dumps.

| Phase | Work / exit criteria | Depends on |
|---|---|---|
| M0 — Scope/authority freeze | Confirm image-only non-child synthetic/test boundary; record non-video scope and future auth/save seams; map UI fields to every authoritative contract; approve exact integration addendum/hash in FEAT-018 `approvals/TASK_APPROVAL.md`. | User approval. |
| M1 — Contract reconciliation | Close transport/command ID/idempotency, bootstrap ID, Gate A/B identity, Gate-B-before-spec reducer order, retake command/invalidation, rev-2 P1 schema status, version encoding, Pixi bridge, job/TTL, gallery/feedback and error mapping gaps. Export schemas, compatibility report, corrected state-transition fixtures (including old-order rejection), positive/negative/migration fixtures, OpenAPI and sequence diagram. No API implementation before owner freeze. | M0; relevant contract owners. |
| M2 — ADR/provider feasibility | Verify Lightning Vision image input format/limits; add ADR-0005 addendum with provider, budget/quota, privacy, networking and rollback. Audio/ASR is excluded. Run fixture/mock tests only until separately authorized live smoke. | M0 and ADR approval. |
| M3 — Asset audit/coverage | Review all 144 sprites and rights individually; record decisions; build topic/role/alias coverage matrix, confusable tests and gap list. Generate supplemental flat assets only if approved, to `assets/generated/`, with provenance; do not runtime-reference until review gates pass. | M0; owner visual/rights decisions. |
| M4 — Backend ephemeral session/API | Implement one-process in-memory aggregate/job/idempotency adapters behind application ports, versioned router, multipart admission, media validation, typed errors, cleanup/TTL and session gallery/feedback projection. Keep routers independent of storage. One Uvicorn worker; no DB/object storage. | M1; M2 for live adapters may be parallel only behind port. |
| M5 — Live AI/P1 | Backend `AiGateway` Lightning Vision adapter for validated dynamic images; map to FEAT-003 V2 + image-only `RawUnderstandingResultV1`; Gate A; adult P1 context; deterministic filter/ExperienceSpec/fit/Gate B. Add bounded FEAT-028 text-only candidate ranker and backend allowlist. | M1, M2, reviewed/eligible assets for asset ranking. |
| M6 — Pixi/P4/handoff | Implement renderer protocol v1 and WebView lifecycle, source-preserving scene, approved-only manifest/animation, reviewed P4 cache/fallback, same-identity handoff and renderer failure handling. `generation_called=false`; no video endpoint/player. | M1, M3, P1 identity. |
| M7 — Expo Android demo shell | Add compatible image-picker/WebView dependencies and only needed image permissions; connect demo screens to backend; remove silent mocks; configure emulator URL/debug networking; implement errors, polling and retry. No audio or microphone permission. | M4, M5, M6. |
| M8 — Verification/demo evidence | Contract/API/security/renderer/UI tests, Android Emulator walk-through with synthetic non-child image, one separately confirmed live Lightning Vision smoke; update `apps/ui-mobile/BACKEND_INTEGRATION.md`; write per-feature evidence/runbook. | All earlier phases and provider cost approval. |

## 11. Test matrix and acceptance criteria

| Area | Required evidence/tests |
|---|---|
| Contract registry | Schema export, registry/version check, compatibility report, strict extra-field tests, positive/negative/migration fixtures; prove HTTP `request_id` maps to one FEAT-016 command ID and carries idempotency/actor/version; prove exact sequence P1 candidate → compiled spec → Gate B → `EXPERIENCE_READY` and reject the current reversed order. |
| Session/idempotency | UUID bootstrap v0; in-memory create/resume/TTL/restart loss; same-key replay; different-payload key conflict; stale mutation conflict; one worker enforced/documented; no durable writes; application service tests run through the in-memory ports rather than router-owned state. |
| Media admission | Synthetic JPEG/PNG (plus only provider-verified formats), correct hashes/original refs, spoofed MIME, corrupt/empty/oversize, pixel limits, audio explicitly `NOT_SUPPLIED`, no inference on RECAPTURE, replacement invalidation and cleanup. |
| Lightning | Mocked Vision success/failure/timeout/rate-limit/malformed/source mismatch; provenance exact; no provider calls before PASS; live smoke derived from uploaded non-child image; no audio/ASR path; no silent fixture substitution. |
| Gate A / P1 / Gate B | Confirmation cannot bypass Gate A; adult correction changes downstream anchor; retake invalidates results; every P1 context field—including explicit `completed_activity_ids`—is validated; missing context/no eligible activity typed; exact one-anchor/objective/template; stale/mismatched Gate B identity rejected. |
| Asset review/selector | Every used sprite has per-frame approval + cleared rights + hash; review-pending assets excluded; candidate set top-bounded and text-only; no source image/path/hash sent to ranker; unknown model IDs rejected; confusable-topic tests; no-match preserves source and returns authoring-queue proposal. |
| Pixi/P4 | Source hash/manifest/plan consistency; bounds/motion/protocol/schema; WebView handshake, pause/resume, malformed/oversized message, reduced motion, renderer crash; P4 hit/miss/timeout/fallback/blocked preserve activity/objective/renderer IDs and versions; `generation_called=false`. |
| Handoff/gallery/feedback | `ActivityHandoffV1` exact same spec identity; gallery is session-only and has no media bytes; `FeedbackV1` exact identity and no personal/child fields; restart removes session. |
| Video exclusion | Assert no video endpoint, provider request, job, asset, persisted artifact, response URL, download or player/control is invoked/rendered. `ExperienceSpecV1.video_plan` remains metadata-only to satisfy current schema. |
| Android | Emulator build mode/dependencies/permissions; allow/deny paths; actual synthetic image picker/camera; no microphone permission; `10.0.2.2` reachability; multipart boundary; live mode cannot fall back to mock; poll/backoff/background stop; network/provider/session failures and recovery. |
| Security/governance | No secrets/endpoints in app bundle or Git; no media/transcript/provider body in logs; no child media; temp files cleaned; feature-scoped evidence; repository security validator before any eventual commit/push. |

Demo acceptance requires: (1) Android Emulator executes session → non-child image upload → backend validation → actual Lightning Vision-derived image understanding → Gate A → adult-provided P1 context → P1/Gate B/ExperienceSpec → PixiJS original-art scene using only approved assets or typed no-match → P4 cache/fallback → exact-identity activity handoff → session gallery/feedback; (2) no audio capture/upload or ASR call, with narration explicitly `NOT_SUPPLIED`; (3) no live call occurs before approved ADR/cost gate; (4) no video execution/UI; (5) backend restart/expiry and provider failure are honest and recoverable; and (6) evidence/runbook is stored under FEAT-018. Fixture-only tests do not satisfy live Lightning acceptance.

## 12. Future auth and durable-save readiness (design constraint; not demo implementation)

The user wants the later product to authenticate and save sessions. Preserve that path now without turning on auth or persistence during this demo:

1. **Identity boundary:** the repo already has provider-neutral `IdentityTokenVerifier` and `VerifiedPrincipal` contracts, and ADR-0005 selects Firebase Authentication only. Later the mobile app sends its Firebase ID token over HTTPS; the backend verifier checks signature, issuer, audience, expiry and revocation, then authorization maps it to an internal account/owner reference. Screens and domain code consume a principal/authorization result, never Firebase SDK state, raw UID, email, or role claims supplied by the client.
2. **Guest-to-account save:** current demo remains guest/ephemeral. Later saving is an explicit authenticated command (not automatic just because login exists). Server validates the token and permission, then claims/saves the in-memory session for that verified owner using a versioned ownership command. The client never posts `owner_ref`; a session cannot be claimed by a second account, and retries are idempotent. Define exact guest-session transfer/expiry semantics in a later contract/ADR before implementing.
3. **Persistence seam:** this addendum must keep application use cases behind `SessionRepository`, `JobStore` and `ArtifactStore`-style ports and supply in-memory/temp adapters for the demo. Later adapters use backend-owned PostgreSQL for session/state/provenance and S3-compatible object storage for immutable original/derived media per accepted ADR-0003/0005; Firebase Storage, Firestore and Realtime Database remain forbidden. Mobile talks only to the backend; no S3 credentials, URLs or object keys are exposed.
4. **Saved-session behavior:** later explicit save should persist the session snapshot, immutable original and derived refs/hashes, model/config provenance, Gate A/B confirmations, approved ExperienceSpec, Pixi/P4 identity, handoff and permitted feedback under one owner. Keep `session_id`/artifact refs stable through adapter change, do not silently rewrite source media, and make partial-save failure recoverable without duplicate/orphaned records.
5. **Privacy/lifecycle gate:** before real user/child data is persisted, a separate approved feature plan must specify consent, access control, retention, deletion/export, encryption, backup, audit/redaction and recovery. The current demo stores nothing durably and must not implement the future save endpoint or add ownership/persistence fields to frozen FEAT-018 contracts.
6. **Future tests:** require token invalid/expired/revoked, cross-account access denial, guest-save/replay, ownership collision, artifact hash continuity, partial failure/recovery, deletion/retention and repository/artifact adapter contract tests before calling auth/save production-ready.

The approved ADRs already name Firebase Auth plus PostgreSQL/S3-compatible backend-owned persistence, so this plan preserves those boundaries but does not provision services, select cloud vendors, or authorize an auth/persistence implementation. Any change to those accepted decisions needs a separate ADR review.

## 13. Out of scope, risks and approval gates

Out of scope for this addendum: video generation/endpoint/player/storage; auth sign-in/token verification and saved-session endpoint; persistent DB/object-store adapters; Firebase data services; real child media; production deployment/monitoring; replacing `apps/mobile`; and commits/pushes absent a separate request. Repository/artifact ports and opaque identity refs are in-scope seams only. The finite reviewed asset catalog cannot promise an approved overlay for every imaginable topic; original-art-only plus typed no-match is the safe coverage fallback. “80% of production” means journey coverage for a local demo, not security, reliability or production readiness.

Key risks: ADR-0005 presently forbids live dynamic provider use; Lightning may not accept the uploaded image format/bytes; all 144 candidate sprites are still awaiting per-frame and rights review; Expo SDK 52 module/build constraints may require a dev client; and process restart intentionally loses state/media. Surface each blocker explicitly; never hide it with mock data, an unreviewed asset, an invented contract state or a video placeholder.

This approved integration addendum is being implemented. Contract/reducer work has started and is recorded in feature-local evidence. This implementation does not call Lightning, approve assets, alter ADRs, commit, or push. Live provider smoke remains a separately confirmed cost/quota-gated action.
