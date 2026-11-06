# FEAT-063 Plan Rev51 — bounded Modal AI and legacy API retest

**Feature:** FEAT-063 — system architecture rearchitecture
**Date:** 2026-11-06 (Asia/Saigon)
**Canonical product/architecture source:** `artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` v2.4-draft.
**Runtime inventory:** `deployment/modal/srs_v23/workloads.json`, current backend OpenAPI at `http://127.0.0.1:8000/openapi.json`, and current FEAT-063 evidence.
**Execution status:** COMPLETE WITH FINDINGS - 2026-11-06.

## Goal

Diagnose and fix reproducible non-video Modal AI defects; verify the existing backend API surface, including legacy routes; preserve all test output and synthetic AI products together under one FEAT-063 evidence folder; stop Modal applications used by this task; and commit only coherent, security-validated changes.

## Scope and limits

1. **Canonical requirements:** use only the FEAT-063 v2.4-draft SRS for current product requirements. Treat earlier worker reports as dated implementation evidence, not as proof of current product API readiness.
2. **AI workload accounting:** inventory all non-video AI workloads in the Modal registry and distinguish worker inference from an authenticated, durable product API. Reuse verified 2026-11-05 outputs for workloads that already passed; do not spend GPU credits to repeat them.
3. **Unresolved AI work:** inspect the optional `drawing.segment` SAM 2.1 failure and Modal runtime/deployment evidence. At most one new synthetic call is permitted, only if Modal access and the app are available. Bound the full call/queue wait at 1,800 seconds. Record whether time was spent queued/cold-starting, loading weights, or executing inference. Do not retry an unknown/failed result unchanged.
4. **Timeout changes:** increase a timeout only when logs prove execution was interrupted by that timeout. A scheduler-capacity wait or cold-start queue is a distinct failure and must not be “fixed” by increasing an inference timeout. Any timeout edit must retain the existing request, output, safety, and business-rule contracts; run focused tests and one bounded retest.
5. **Video:** do not deploy or call video generation, video consistency, composition, final-video safety, or playback. Report their status as excluded/not tested in this pass.
6. **Legacy APIs:** record the live OpenAPI operation inventory (currently observed as 124 operations / 111 paths), run the backend API/contract regression tests that cover mounted and legacy routes, and perform only read-only live checks (`/health`, `/docs`, `/openapi.json`). Mutating API checks must use isolated test fixtures/databases. Do not write to the shared development database or run migrations.
7. **Legacy defects:** classify each failure as code defect, missing implementation, auth/test-fixture limitation, environment/dependency failure, or expected business-rule response. Fix only a reproducible defect directly in the Modal AI integration or its FEAT-063 contract. Record unrelated/legacy failures without broadening implementation scope.
8. **Inputs and privacy:** use generated/synthetic drawings, lesson data, text, and audio only. Do not use real child artwork, profiles, roster, voice samples, provider secrets, or credentials. Never read or write secret values.
9. **Workload state:** leave every product workload disabled. Do not change quota, permission, human-review, publication, safety, or production policy.
10. **One result folder:** collect report, machine-readable API/workload matrices, hashes, timings, logs with secrets scrubbed, and verified generated products in:
   `features/FEAT-063-system-architecture-rearchitecture/evidence/modal_ai_and_legacy_api_retest_20261106/`
   The required top-level report is `API_TONG_HOP_VA_SAN_PHAM_AI_MODAL_20261106.md`; place generated/captured products and a provenance/hash manifest under this same folder.
11. **Modal cleanup:** stop each Modal app/deployment started or used by this task and verify zero active tasks. Do not stop an unrelated pre-existing user app or delete shared Volumes/checkpoints. If Modal control-plane access is unavailable, record that as a blocker and do not claim shutdown was verified.
12. **Commits:** after each independently reviewable fix, run the focused checks and `python tools/validate_repository_security.py`, then create a conventional commit containing only that fix and its evidence. If no code fix is warranted, create one evidence/documentation commit after security validation. Do not push as this request does not ask for publication.

## Workload inventory to report

| Registry workload(s) | Current evidence to reconcile | This pass |
|---|---|---|
| `drawing.analyze` | Qwen3.5 synthetic worker passed; product dispatch/API not established | Reuse evidence; verify API inventory and contract tests |
| `story.generate`, `storyboard.generate` | Qwen3.5 worker/parser/business checks passed; product API remains fixture-only | Reuse evidence; verify legacy StoryRun API contracts; report missing durable dispatch |
| `parent.sketch-guide.generate` | FLUX.3 synthetic image passed after checkpoint staging fix | Reuse verified output; no duplicate inference |
| `teacher.sketch-deck.generate` | Qwen3.5 synthetic draft passed; durable occurrence/deck API absent | Reuse evidence; report API status |
| `lesson.plan.suggest` | Qwen3.5 draft-only output passed; durable API/job persistence absent | Reuse evidence; verify role/contract tests |
| `lesson.visual.generate` | FLUX.3 synthetic draft image passed with lesson lineage | Reuse verified output; no duplicate inference |
| `tts.narration.generate`, `asr.transcribe` | Synthetic Vietnamese WAV and exact-text round-trip passed | Reuse verified products; no duplicate inference |
| `drawing.segment` | SAM 2.1 remains unknown after a 1,800-second GPU scheduling wait | Diagnose; at most one synthetic attempt under the cap above |
| Video workloads | Deferred by owner in the previous AI validation pass | Excluded; no deployment or calls |

## Acceptance criteria

- **AC51.1:** Current SRS AI requirements and all Modal registry workloads are mapped to the observed worker/API status without conflating worker calls with product API readiness.
- **AC51.2:** All 124 currently mounted operations are represented in the API inventory and covered by the selected regression tests or explicitly marked as lacking a test. Read-only live health/docs/OpenAPI results are recorded.
- **AC51.3:** Any newly observed timeout is classified by queue/cold-start, model download/load, inference execution, client wait, or API deadline using available timestamps/logs. Timeout settings change only when execution deadline is the proven cause.
- **AC51.4:** The SAM 2.1 path either returns one validated synthetic result or is recorded with its exact terminal blocker; no unchanged retry occurs.
- **AC51.5:** Previously passed AI products are collected with original source evidence, SHA-256, model/version, and synthetic-data provenance. No unsupported new AI output is represented as generated in this pass.
- **AC51.6:** The consolidated report and all captured results are under the single specified evidence folder, with secrets and real-child data excluded.
- **AC51.7:** Relevant task-used Modal apps are stopped and zero tasks are verified, or the precise access blocker is recorded.
- **AC51.8:** Every code fix has focused verification and its own conventional commit after repository security validation. If no fix is supported by evidence, the final result remains a clearly scoped evidence/API audit rather than an arbitrary code change.

## Execution sequence

1. Save this plan and record the owner's direct approval in the root and FEAT-063 task approval registers, referencing the exact plan SHA-256.
2. Capture starting git state, API health/OpenAPI inventory, test environment boundaries, Modal app status, and current task counts without exposing credentials.
3. Run isolated backend API/contract regression coverage; map the tested route groups back to the 124-operation snapshot.
4. Diagnose the SAM 2.1 timeout and other unresolved findings. Make a narrowly scoped fix only where evidence identifies a code cause; retest once if a code/config fix is applied.
5. Copy/link verified synthetic model artifacts into the result folder and write per-artifact provenance and SHA-256.
6. Stop task-used Modal apps and verify zero active tasks. Recheck local services only if this task started them; leave shared services as found.
7. Complete the consolidated report, workload/API matrices, FEAT-063 context/decision/status/evidence links, and commit(s) according to the rules above.

## Explicit exclusions

No video generation or any video pipeline call; no new product API implementation unless a minimal AI integration defect fix is directly required and separately represented as a code fix; no database migration/schema change or shared DB write; no real-child data; no production enablement; no secret/credential read or mutation; no deleting Modal Volumes/checkpoints; no unrelated legacy refactor; no push, merge, rebase, amend, or force-push.


## Execution closeout - 2026-11-06

- Live API read-only checks passed: `/health`, `/docs`, `/openapi.json`; live OpenAPI has 111 paths / 124 operations. The complete operation inventory and direct-probe flags are in the result folder.
- Backend API/contract suite: 1,454 passed / 6 failed out of 1,460 collected. The six failures and their observed causes are listed in `evidence/modal_ai_and_legacy_api_retest_20261106/API_TONG_HOP_VA_SAN_PHAM_AI_MODAL_20261106.md` and `backend_api_test_summary.json`.
- Modal worker contract suite: 79 passed, 2 skipped. Existing Qwen3.5, FLUX.3, TTS, and ASR synthetic successes were reused; no model inference was repeated.
- SAM 2.1 remains capacity-blocked based on the prior 1,800-second GPU scheduling wait. Current Modal `dev` app listing is empty; no new app was deployed. Shared Volumes and secrets were not changed.
- No timeout was increased because no current worker execution deadline was observed; recorded failures were queue/capacity, unknown-before-worker-log, semantic output rejection, or API composition/fixture mismatch.
- Results and 16 synthetic/historical artifacts are grouped under `evidence/modal_ai_and_legacy_api_retest_20261106/`. No code fix was supported by this evidence; publication is limited to a local conventional documentation/evidence commit after security validation.
