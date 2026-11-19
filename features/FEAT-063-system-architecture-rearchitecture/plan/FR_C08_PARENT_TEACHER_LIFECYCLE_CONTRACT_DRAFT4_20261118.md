# FR-C-08 Parent and Teacher StoryRun lifecycle contract — Draft 4

**Status: DRAFT / NOT APPROVED / NOT LAUNCHED. BLOCKED FOR IMPLEMENTATION.**  
**Date:** 2026-11-18.  
**Authority:** D-209 adopted, unsigned canonical working SRS, v2.7-draft.  
**Purpose:** reconcile surviving FR-C-08 planning against the adopted SRS and closed M2, record current source facts, and isolate decisions needed before an implementation approval. This document does not choose unresolved owner policy or authorize code, schema, tests, or launch.

## 1. Authority and precedence

The canonical bytes are `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`, pinned at 701,157 bytes with SHA-256 `B9B1F42D0BB118C19C81607D3913B7E4F1D8B6F673F0C3FBB6402888FEB675F5`. D-209 makes this the single working SRS for FEAT-063. It remains unsigned and is not final product sign-off. Rev60, Rev67, and the Rev68 working copy used by earlier FR-C-08 drafts are historical for requirements. D-208 dispositions may be carried forward only where they agree with D-209.

The material difference that affects this contract is deletion eligibility. Earlier Rev68/D-208 planning selected explicit DELETE for COMPLETED, FAILED, and ABANDONED. D-209 says “đã hoàn tất” in FR-C-08 and §21.2, while UC-07 requires a completed run and §21.2's DELETE row says “Chỉ run đã hoàn tất”. D-209 expressly leaves open whether FAILED and ABANDONED count as “đã hoàn tất”. This draft does not import the older selection. See Q-A in the owner-question register.

The Data Table Register is a companion model source. It does not override the SRS. Any new physical scope, lifecycle work item, receipt, audit mapping, reference model, or retention field requires a separately reviewed DTR/schema decision and, if needed, a separately approved migration task.

## 2. M2 closure and implementation boundary

M2-S3 was accepted and M2 closed by the owner on 2026-11-18 with recorded debt and deviations. The acceptance is recorded in the feature-local approval ledger and status record. It supersedes earlier status snapshots that predate the acceptance. The closure is not FR-C-08 approval and transfers no M2 implementation approval, allowlist, command ceiling, or evidence claim.

M2 source already declares `POST /v1/story-runs/{run_id}/cancel`. In the current source, the accepted cancellation moves the run to `DELETE_PENDING`, releases the active Parent lock, advances revision, and stores an idempotency receipt. This is the M2 cancel slice, not the complete FR-C-08 lifecycle. The route is conditionally included by static composition; no runtime deployment or route call was verified in this task.

Recorded M2 debt remains relevant: the OpenAPI P3 is open; M2-AT-09 is deferred; and the cancel operation is absent from the client-facing projection. This draft does not authorize client integration. It addresses the additional lifecycle work still missing, including explicit DELETE, request/receipt ownership, revocation and dispatch fences, cross-module purge and verification, Teacher authorization, and audit/retention mapping.

## 3. SRS contract

### 3.1 Cancel an unfinished run

FR-C-08 at SRS line 500 requires cancellation of an unfinished run through lifecycle, immediate active-lock release, upload/playback revocation, best-effort job cancellation, linked-content deletion, and purge progress reporting. It preserves accepted video quota usage, minimum quota metadata, and a successful Teacher sample claim.

UC-11 at lines 1517–1523 specifies the current Parent owner or currently assigned Teacher, current authorization and run revision, idempotency, a transaction that sets `DELETE_PENDING` and releases the active lock, playback/upload revocation, a cancellation notice and lifecycle request, best-effort job/provider cancellation, lifecycle purge, and `DELETED` only after the lifecycle completes. Accepted video quota and a successful Teacher sample claim are retained. Late results are stale, non-playable, and purged.

The cancel-eligible states are the 13 unfinished states described by UC-11 and the 18-state inventory at line 394, excluding COMPLETED, FAILED, ABANDONED, DELETE_PENDING, and DELETED. Compatibility between source-only `SCRIPT_GENERATING` / `SCRIPT_GENERATION_UNKNOWN` and the adopted SRS state model is unresolved; do not add a public state by inference.

### 3.2 Explicit delete of a completed run

UC-07 at lines 1469–1475 requires a Parent owner or currently assigned Teacher, a completed run, current authorization, a lifecycle request, blocking new playback tokens, deletion of run-linked private content, retryable object deletion, retention of a shared asset until valid independent references are reconciled, and metadata-only audit. §21.2 line 1674 specifies `DELETE /v1/story-runs/{id}` and a 202 deletion request/status for a completed run. The inclusion of FAILED and ABANDONED is left to Q-A; no automatic purge is authorized by this draft.

### 3.3 Read, progress, and terminal state

The lifecycle read should use the existing owner-scoped `GET /v1/story-runs/{id}` by default, subject to a contract check. Keep `DELETE_PENDING` visible until required purge is positively verified; report `DELETED` only after the owner modules provide the approved completion evidence. Do not invent public StoryRun states or percentage progress. The SRS requires progress reporting but does not define exact fields, internal phases, or a percentage scale; resolve the minimum safe read/progress contract before implementation.

### 3.4 State and data preservation

No separate video-delete command is added. Do not refund accepted video quota or erase the minimum quota ledger metadata required for accounting. Preserve a successful Teacher sample claim and claim time while clearing run/media references where the approved Lesson contract permits. Do not purge content solely because a run is FAILED or ABANDONED; explicit deletion eligibility remains subject to Q-A.

## 4. Current source observations

Evidence is static source inspection at the root checkout on branch `feature/feat063-m2-parent-teacher-foundation`, HEAD `08439b22fc3c1f34786a3f45f34530075a3914e0`. It is not runtime, database, migration, provider, or generated-OpenAPI evidence.

| Area | Current observation | Evidence and limit |
|---|---|---|
| Parent cancel route | `POST /v1/story-runs/{run_id}/cancel` is declared; it returns HTTP 202 with `DELETE_PENDING` and pending purge indication. The source currently accepts an `Idempotency-Key` length of 1–256. | `backend/src/sketch2life/interfaces/http/routers/parent_story_runs.py:253-294`. D-066-68 convention requires one value, 1–128 visible ASCII; current mismatch needs scoped resolution. |
| Composition | The Parent StoryRun router is included by a composition flag. The combined profile passes a non-demo condition. | `backend/src/sketch2life/interfaces/http/router_composition.py:61,75-76`; `backend/src/sketch2life/interfaces/http/app.py:1124-1127`. Static registration only; runtime not verified. |
| Cancel persistence | The repository replays a stored receipt for an identical key, checks revision, sets `DELETE_PENDING`, releases the active Parent owner lock, increments revision/version, stores the receipt, and commits. Its accepted source-state set is `INPUT_PROCESSING`, `SUBJECT_REVIEW`, `PREPARATION_REVIEW`, `SCRIPT_GENERATING`, `SCRIPT_GENERATION_UNKNOWN`, `SCRIPT_REVIEW`, and `VIDEO_ADMISSION_PENDING`. | `backend/src/sketch2life/infrastructure/persistence/parent_story_repository.py:328-438`. It does not create an integrated lifecycle request, cancellation notice, or purge proof in this method. Five source states intersect the adopted 13-state cancel set; the eight adopted eligible states not represented are `DRAFT`, `INPUT_REVIEW`, `STORY_GENERATING`, `VIDEO_QUEUED`, `VIDEO_GENERATING`, `VIDEO_SAFETY_VALIDATING`, `VIDEO_READY`, and `SAFETY_BLOCKED`. The source-only script-generation states need a compatibility decision. |
| State schema | `ParentStoryRunResponseV1` includes FAILED, COMPLETED, and DELETE_PENDING but omits ABANDONED and DELETED. It also has source-only script-generation values. | `backend/src/sketch2life/contracts/schemas/parent_story_runs.py:110-117`. No full SRS-compatible lifecycle response is established. |
| BE1 lifecycle request | The existing `DataLifecycleRequestModel` requires `organization_id`. | `backend/src/sketch2life/infrastructure/persistence/be1_models.py:555-579`. It cannot represent Parent scope as-is; do not fabricate an organization ID. |
| Core Asset | `CoreAssetMetadataPort` exposes metadata save/get, not reference-closure or deletion. Object storage has a byte-delete boundary, which alone does not prove safe shared-reference deletion. | `backend/src/sketch2life/application/ports/core_foundation.py:181-186`; `backend/src/sketch2life/application/ports/object_storage.py`; persistence implementation in `core_store.py`. No destructive operation was run. |
| AI Jobs | Generic cancellation-notice support exists in AI Jobs source, but the Parent cancel handler is not shown wired to it. Existing notice scope requires organization information. | `backend/src/sketch2life/application/services/ai_jobs.py:545-583` and AI Jobs ports. This is not proof of cancellation dispatch or provider interruption. |
| Runtime and data | No runtime route, database contents, migration state, object store, token/cache behavior, or provider behavior was exercised. | Explicitly not verified. |

## 5. Proposed contract conventions for a later reviewed slice

These transport conventions are sourced from FEAT-066 D-066-68, not invented as new product requirements or as a replacement for D-209. A later implementation approval must confirm the applicable convention version and exact route scope.

- Error body fields: `code`, `message`, `correlation_id`, `retryable`, `retry_after_seconds`, and `field_errors`. `current_version` may accompany `STALE_REVISION`; `request_id` may be an alias equal to `correlation_id`.
- `X-Request-ID` equals body `correlation_id`.
- Schema/shape validation: HTTP 400 `INVALID_REQUEST`; semantic domain outcomes retain their approved domain mapping.
- For nonexistent and out-of-scope resources, return the same-shape 404 `RESOURCE_NOT_FOUND`; use 403 `ACTION_NOT_ALLOWED` only after the resource is established in scope.
- State-changing commands require exactly one `Idempotency-Key` value, 1–128 visible ASCII characters. Missing key returns 400 `INVALID_REQUEST`; same key and payload replays the original result; changed payload returns 400 `INVALID_IDEMPOTENCY_KEY`.
- Parent concurrency uses body `expected_revision`; stale requests return 409 `STALE_REVISION` with current version, never 412.

Current M2's 1–256 length rule is a source fact, not the selected convention. Reconcile through the later exact implementation allowlist and approval; do not silently change current M2 source under this planning document.

## 6. Cross-module ownership model and blockers

The SRS identifies `story.runs`, `be1.data_lifecycle_requests`, `ai_jobs.cancellation_notice`, and `core.asset_metadata/lineage` as relevant data. It does not itself settle the physical Parent-scope request/receipt schema, durable purge worker records, or exact module-owned proof. The proposed logical responsibilities are: Story owns run state, active lock, expected-revision transition and cancellation event; BE1 coordinates a typed Parent-scoped lifecycle request; AI Jobs receives best-effort cancellation; Core Asset resolves references and owns safe deletion; Lesson preserves the successful sample claim and removes only approved run/media pointers. This is a boundary proposal for owner review, not a selected database mapping.

Implementation remains blocked by: Q-A deletion eligibility; Parent-scope request and durable receipt ownership; current Teacher assignment/version authorization; acceptance-time access and dispatch fences; owner-module purge, retries, and shared-reference proof; a lifecycle progress/terminal-read predicate; internal retry/reconciliation representation; audit field/read/storage/retention mapping; and the eventual implementation base and named accountability. If any solution requires a new DTR row, table, column, constraint, public state, migration, or path not in Allowlist Draft 6, stop for separate review and approval.

## 7. Acceptance criteria for a future approved implementation

These are contract outcomes, not authorization to run checks now:

1. Cancel and DELETE are distinct commands with owner-approved state eligibility and current Parent/Teacher authorization.
2. A successful cancel releases the active lock in its acceptance transaction, revokes future and in-flight access according to an approved fence, and records a durable idempotent lifecycle request/receipt without fabricated `organization_id`.
3. Worker dispatch and completion check cancellation/revision fences; best-effort provider cancellation is not treated as proof of purge; late results remain non-playable and enter owner-module purge.
4. The lifecycle read shows pending until every required content reference has owner evidence of deletion or an approved valid independent shared reference; only then can it show DELETED. No percentage or new public state is inferred.
5. Retries are idempotent and restart-safe. Partial failure cannot produce a false terminal state.
6. Quota usage and successful sample claim/time remain; unrelated/shared assets are not deleted; run-owned references and eligible private derivatives are purged by their owner modules.
7. Audit contains only approved metadata and obeys an approved reader, physical-scope, and record-type retention map.
8. OpenAPI/composition evidence is separated from runtime evidence. Verification commands run only under a separate exact approval and launch instruction.

## 8. Open questions and evidence

The owner questions, each with an exact adopted-SRS quotation and line, options, and a non-binding recommendation, are in `FR_C08_OWNER_QUESTIONS_20261118.md`. No answer is implied by this contract.

Predecessor, authority, and source pins are audited in `tmp/frc08-wave1/PIN_AUDIT.md`. The exact candidate path set and verification ceilings are in `FR_C08_PARENT_TEACHER_CANCEL_PURGE_IMPLEMENTATION_ALLOWLIST_DRAFT6_20261118.md`. Both are planning artifacts; neither is approved.

## 9. Status

**FR-C-08: DRAFT / NOT APPROVED / NOT LAUNCHED; implementation blocked pending owner decisions and separate approval.** M2 is closed with recorded debt. No tests, validators, builds, OpenAPI generation, runtime, database, migration, Docker, network, provider, or Modal operation was run for this planning pass. No code, test, SRS, decision, approval, context, or status file was changed.
