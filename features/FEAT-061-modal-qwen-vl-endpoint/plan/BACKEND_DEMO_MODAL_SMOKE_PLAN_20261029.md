# Supplemental plan: one dev-backend Vision smoke check

- Date: 2026-10-29 (Asia/Saigon).
- Status: APPROVED for the later bounded test scope recorded in `../approvals/BACKEND_DEMO_MODAL_SMOKE_AUTHORIZATION_20261029.md`.
- Goal: verify one synthetic image through the existing dev demo backend, image admission, Lightning Vision V2 adapter and existing Modal Qwen-only endpoint.
- This supplements the later owner-directed test work. It does not amend or reinterpret the original revision-1 `PLAN.md` or `TASK_APPROVAL.md` integration exclusions.

## Starting evidence and scope

The owner created `feature/modal-vision-dev` from `origin/dev` at `529cbef9`, completed the separate CPU runtime setup, and supplied `pip check` and admission-import success. The owner then reported token-file creation outside the repository and same-process environment assignment. Latest owner startup output reports `sketch2life.demo_main:app`, PID 44944, application startup complete on `127.0.0.1:8001`. These observations do not yet prove local HTTP readiness, image admission through this backend, or a backend-to-Modal result.

Keep the tested Modal configuration in the original checkout and the backend in the dev-based worktree. Reuse the existing wrapper, model, adapter, URL configuration and bearer boundary. No merge, backend-tree copy, new provider, runtime source change, schema/prompt/model change, dependency installation, endpoint deployment, or production change is included.

An optional test helper and sanitized state/evidence may be created only under this feature's `evidence/` directory. Do not read/print provider credentials or actual `.env` contents, include credentials in probe state, or persist raw model output, image base64 or predicted text. Use the backend's existing authenticated provider connection; the probe calls the loopback backend only.

## Ordered run and limits

1. Read local `/openapi.json` and confirm the demo session, image-upload and understanding paths. This profile does not mount `/health`; a health-route 404 is not a provider failure. No inference is triggered by this read.
2. Create exactly one new UUIDv4 demo session with `actor_ref=demo:local`, `CREATE_SESSION`, expected version zero, and persisted request/idempotency IDs. Confirm HTTP 201 and a typed successful session result. Read its observed version rather than assuming a version.
3. Upload exactly one existing synthetic non-child PNG/JPEG with the required synthetic confirmation, metadata/idempotency headers, and `IDENTITY_V1` normalization. Let this backend create its own admission receipt and artifact references; do not substitute an earlier direct-provider receipt. Require HTTP 200, outer `SUCCEEDED`, `ImageAdmissionReceiptV2`, `decision=ADMITTED`, and valid source/hash before proceeding. This is CPU-only preparation.
4. Wait for the owner to start the existing Modal serving configuration from the original checkout. Use the selected current function URL through the already prepared backend settings. A restart or URL adjustment, if required, remains an owner-guided setup step; do not infer readiness from startup settings alone or start another cloud session autonomously.
5. Send **at most one** `POST /v1/sessions/{id}/understanding` for this smoke check, with a persisted immutable command, current observed upload version, `RUN_UNDERSTANDING`, `user_initiated=true`, and `narration={kind:NONE}`. This is the only authorized inference-bearing request. Do not automatically retry, replay this POST, requery, or issue a second model request after an error, timeout, interruption, or unexpected response.
6. Validate the response below and record sanitized timing, typed status/error, counts, source/correlation checks and provenance. Stop before Gate A confirmation, subject changes, ranking, preference classification, ASR/audio, SAM, planner, recommendation or story/video calls. No mobile test is included in this run.

The owner controls provider startup/shutdown. Current Modal state remains unconfirmed until fresh owner evidence; earlier `App aborted` output is historical. Keep all GPU work bounded to the single understanding operation above and report the result before any further action.

## Acceptance and honest failure reporting

- Local route inspection and session/image responses must use the expected versioned contracts. Session creation normally returns observed version 0, admitted upload 1, and successful understanding 2; the actual returned versions are authoritative.
- Successful understanding requires HTTP 200 **and** outer `MobileWorkflowResultV1` status `SUCCEEDED`, nested `RawUnderstandingResultV1` status `SUCCEEDED`, `gate_a_required=true`, and narration `NOT_SUPPLIED`. HTTP 200 with `BLOCKED` or failed nested content is not an integration pass.
- Match session ID, correlation to the understanding request ID, and source reference/SHA-256 to the backend admission receipt. Confirm upstream `VisionUnderstandingResultV2` version `2.0`, profile `QWEN3_VL_8B_INSTRUCT_BF16_V1`, and complete model/config provenance for the pinned Qwen candidate.
- Require sanitized progress `TOPIC_READY`, `gate_a_ready=true` and `provider_attempt_count=1` for a passing result. `repair_attempted=true` is permitted for existing in-memory normalization and does not itself mean another inference.
- Inspect the synthetic proposal without persisting raw generated text. Do not require an exact entity count or claim model quality, production readiness, a benchmark, or completion of the wider app journey.
- Preserve any typed failure and uncertainty honestly. Actual backend startup was owner-reported; HTTP/model acceptance remains unverified until this run produces evidence.

## State persistence and duplicate prevention

Persist stage, session ID, image hash/reference, returned version, and each immutable command's request/idempotency IDs in feature-local sanitized state. Before the understanding HTTP call, durably mark its one-request budget reserved/consumed. Do not clear that mark on failure or restart. A probe seeing a prior reservation/send/outcome must refuse another understanding POST, including when the previous network outcome is unknown. Do not create a fresh session or change IDs to bypass the cap. Read-only inspection may help diagnose uncertainty; another inference requires a later owner instruction.

Evidence must distinguish owner reports, local CPU/HTTP observations and the one model-bearing result. Runtime credentials remain outside the repository. No commit or push is included.
