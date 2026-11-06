# FEAT-063 Plan Rev52 - non-video Modal AI reliability and observability

**Date:** 2026-11-06 (Asia/Saigon)  
**Feature:** FEAT-063 - system architecture rearchitecture  
**Canonical product source:** FEAT-063 SRS v2.4-draft at `artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` (unsigned working baseline).  
**Branch base:** `dev` at `0fc773fafeb6f5443538f283cb891c67d379d9c6`; work branch `feature/feat063-modal-ai-reliability-20261106`.

## Goal

Make the currently registered non-video Modal AI workers reliable and diagnosable in the dev environment. Add privacy-safe worker and caller logs that distinguish dispatch/queue wait from container startup, checkpoint/model load, inference, parsing/business validation, and output transfer. Fix reproducible defects without weakening SRS contracts. Exercise every unique non-video worker and every currently mounted HTTP route that invokes AI, using synthetic inputs only; stop the task apps after verification.

This plan follows SRS sections 6-7, 24-27 and 31, especially FR-P-03/04/11, FR-T-18/19/20, FR-AI-01/02/03/11/14/15 and BR-23/34/36/42-46. Video generation, validation, composition, safety and playback are excluded.

## Baseline findings

- Rev51 recorded 9 non-video workload IDs: `asr.transcribe`, `drawing.analyze`, `story.generate`, `storyboard.generate`, `parent.sketch-guide.generate`, `teacher.sketch-deck.generate`, `lesson.plan.suggest`, `lesson.visual.generate`, and optional `drawing.segment`.
- Story and storyboard share one model call. Existing synthetic workers have prior success evidence, but worker logs are incomplete/inconsistent. SAM 2.1 previously waited 1,800 seconds for GPU scheduling without entering the worker.
- Only the Parent StoryRun-lite drawing and story paths currently invoke Modal through HTTP. Several registry workloads do not have an authenticated durable product HTTP API. A direct Modal worker pass must not be reported as proof that such a product API exists.
- Current backend AI Job composition is a foundation/fixture slice; the mounted AI Job status router is not a general Modal workload dispatcher. Existing schemas and SRS/API contracts must be used where present; do not invent a public route or bypass auth/quota/job ownership.

## Scope

1. Reconcile every non-video registry workload with its Modal function, pinned model/checkpoint, input/output contract, current HTTP caller (if any), readiness check, timeout and test coverage.
2. Add structured, machine-readable lifecycle logs to every non-video worker entry point and the Modal caller paths. Correlate with opaque job/generation/attempt and Modal call IDs; record timestamps, stage, elapsed time, model revision, GPU class/name when available, safe error code/type, output size/hash and artifact metadata where available.
3. Never log prompts, generated text, child/profile/roster data, images, audio, raw manifests, tokens/secrets, full exception text, or raw Modal log lines. Parse and retain only allowlisted worker event fields. Follow SRS FR-AI-11 and the existing capability-redaction rules.
4. Classify failures as pre-worker/queue-or-container-not-observed, container/image startup, GPU admission, checkpoint download/integrity, model load, inference, schema/parser/business guard, output encoding/transfer, caller/API deadline, or unknown. Preserve fail-closed behavior and no automatic retry on unknown outcomes.
5. Fix code/config defects directly evidenced by local tests or one bounded synthetic call. Do not relax schemas, safety/factual checks, human review, role, quota, privacy, or SRS business rules.
6. Run all focused worker/parser/API tests. After code changes, deploy only the non-video Modal apps required for verification; preflight CPU health, model/checkpoint readiness and Secret *name/presence* (never values) before GPU calls. Make one live synthetic call per unique workload; story/storyboard count as one. Repeat a failed workload only after a code/config fix or a new, evidence-based capacity strategy. Use existing verified outputs without duplicating inference when no change affects that worker.
7. For the optional `drawing.segment`, attempt one synthetic call with the configured ordered GPU fallback if capacity is available. A scheduler wait without `worker_started` is not an inference timeout and does not justify a larger execution timeout. If a worker-stage log proves execution was cut off by its configured timeout, raise only that function timeout enough for one bounded retest and retain an upper bound of 3,600 seconds.
8. Exercise the currently mounted Parent HTTP AI paths with isolated synthetic fixtures and a disposable test database. Do not mutate the shared development database. Record product APIs absent from the current contract/OpenAPI as `NOT_IMPLEMENTED`; do not fake or relabel direct Modal calls as product API success.
9. Store plans, safe logs, API/workload matrix, timings, outputs, hashes and shutdown evidence under `evidence/nonvideo_modal_ai_reliability_20261106/`. Keep original evidence untouched.
10. Keep registry workload switches disabled. Stop every app deployed/used in this task and verify no task-owned Modal work remains. Preserve shared Volumes/checkpoints and avoid inspecting secret values.
11. Commit each independently reviewable code fix with its focused evidence after `python tools/validate_repository_security.py`; no push is included in this plan.

## Acceptance criteria

- **AC52.1 Inventory:** all 9 non-video workload IDs have a current handler, model/revision, API exposure state, readiness status, test/evidence pointer and final result classification.
- **AC52.2 Worker logs:** each callable worker emits structured `worker_started`, phase start/end, and terminal success/failure events. Logs distinguish the last reached stage and include safe correlation/timing/error fields without user content or secrets.
- **AC52.3 Caller observability:** each existing backend Modal caller records request validation, scratch upload, spawn/call ID, wait result and cleanup. On failure/timeout, per-call Modal logs are summarized using allowlisted structured events; raw worker log bodies are not persisted.
- **AC52.4 Failure diagnosis:** injected worker/model/parser/transfer failures produce a safe stable failure code, stage and retryability/outcome classification. Unknown dispatch outcomes remain unknown and are never automatically retried.
- **AC52.5 Contracts:** all focused worker, parser, backend Modal client, and existing HTTP route tests pass, or each remaining environment/external blocker is linked to safe runtime evidence and not misreported as a code pass.
- **AC52.6 Live worker coverage:** every required non-video worker has one validated synthetic terminal output after the observability changes, reusing prior output only where the worker code/config is unchanged and the prior pinned-model evidence remains applicable. Story and storyboard share one call. Optional segmentation is attempted once and explicitly classified.
- **AC52.7 API boundary:** every mounted HTTP AI route is exercised with synthetic fixtures; each non-mounted product API remains explicitly `NOT_IMPLEMENTED` in the matrix until an approved versioned contract and implementation exist.
- **AC52.8 Cleanup:** only non-video apps are deployed; all task-used apps are stopped and no task-owned calls remain. Shared storage and production workload flags are unchanged.
- **AC52.9 Evidence/commit:** test commands, results, safe Modal call logs, durations, model pins, artifacts and SHA-256 values are in the feature evidence folder; security validation passes before each local conventional commit.

## Verification matrix

- Unit tests: structured logger allowlist/redaction, stage events, error classification, caller log-tail summarization, timeout/outcome-unknown behavior.
- Focused tests: `deployment/modal/srs_v23/tests`; backend Modal client and Parent StoryRun-lite route tests.
- Runtime preflight: Modal CLI/profile/environment, dev app/function lookup, CPU health, secret-name presence, checkpoint manifests and exact model pins; no GPU inference until preflight passes.
- Live synthetic workloads: one attempt each for drawing analysis, story+storyboard, Parent guide, Teacher deck, lesson suggestion, lesson visual, TTS, ASR and optional SAM2; no video.
- API flow: one synthetic Parent drawing-analysis request and one separate fixture-backed story request through the mounted HTTP test app/database; never reuse a request whose Modal outcome is unknown.
- Shutdown: Modal app/task inventory after all calls, plus local service/container state for anything this task started.

## Explicit exclusions

No video-related function, app, model, compose, safety or playback call; no production workload enablement; no real child/media data; no secret value access/change; no shared-database write/migration; no weakening of SRS or human/safety/business gates; no deleting shared Volumes/checkpoints; no invented public endpoint where an API contract is absent; no push, merge, rebase, amend, squash or force-push.
