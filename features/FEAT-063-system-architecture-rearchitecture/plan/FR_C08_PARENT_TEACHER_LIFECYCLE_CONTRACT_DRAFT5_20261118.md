# FR-C-08 Parent and Teacher StoryRun lifecycle contract — Draft 5

**Status: DRAFT / NOT APPROVED / NOT LAUNCHED. BLOCKED FOR IMPLEMENTATION.**
**Date:** 2026-11-18.
**Authority:** D-209 adopted, unsigned canonical working SRS, v2.7-draft.
**Purpose:** reconcile FR-C-08 planning against the adopted SRS and current source observations, identify unresolved owner decisions, and define the contract outcomes a later separately approved implementation must satisfy. This document authorizes no code, schema, tests, baseline, or launch.

## 1. Authority and precedence

The canonical SRS is `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`, 701,157 bytes, SHA-256 `B9B1F42D0BB118C19C81607D3913B7E4F1D8B6F673F0C3FBB6402888FEB675F5`. `docs/context/SRS_AUTHORITY.md` and D-209 identify these bytes as the single unsigned working SRS for current requirements. The Data Table Register is a companion model source and does not override it.

D-209 item 4 says D-208 directions stand only where consistent with the adopted SRS and leaves OPEN-OWNER whether UC-07 and §21.2 deletion of a run described as “đã hoàn tất” includes FAILED and ABANDONED as well as COMPLETED. D-208 item 6's earlier eligibility choice is historical planning direction, not the answer to that current question. See Q-A. D-208's other module responsibilities and default GET direction remain directions only where consistent with D-209; Q-PARENT and Q-READ remain open.

## 2. M2 closure and implementation boundary

The FEAT-063 approval record lines 3243–3247 records owner acceptance of S3 and closure of M2 with debt and deviations. `status/STATUS.md:876` records the same current closure; line 873 is a stale pre-acceptance snapshot. D-208 item 8 separately requires reconciliation and pinning of the partial, dirty M2 baseline before FR-C-08 implementation. Whether the accepted M2 closure satisfies that specific gate remains OPEN-OWNER (Q-M2-GATE); this draft does not infer an answer. M2 approval, allowlist, command ceilings, or evidence do not transfer to FR-C-08.

M2 source declares `POST /v1/story-runs/{run_id}/cancel`; its current repository path sets DELETE_PENDING, releases the active Parent lock, advances revision, and stores an idempotency receipt. The route is conditionally included by static composition. These are source/composition observations only: runtime deployment, route reachability, database state, and end-to-end purge were not verified. The M2 cancel slice does not establish the complete FR-C-08 lifecycle, including explicit DELETE, durable lifecycle request/receipt ownership, immediate revocation across owners, purge evidence, or the Teacher authorization path.

## 3. Adopted SRS contract

### 3.1 Cancel an unfinished run

FR-C-08 at SRS line 500 requires lifecycle cancellation of an unfinished run, immediate active-lock release, upload/playback revocation, best-effort job cancellation, deletion of linked content, and purge-progress reporting. Accepted video quota usage, minimum quota metadata, and a successful Teacher sample claim are preserved.

UC-11 at lines 1517–1523 requires current Parent ownership or the Teacher currently assigned to the class, current authorization and run revision, idempotency, a transaction that sets DELETE_PENDING and releases the active lock, playback/upload revocation, a cancellation notice and lifecycle request, best-effort job/provider cancellation, owner-module purge, and DELETED only after lifecycle completion. Worker checks must fence costly dispatch and result acceptance; late output must be stale, non-playable, and purged. No provider interruption result is purge proof.

The adopted 18-state inventory has 13 unfinished cancel-eligible states after excluding COMPLETED, FAILED, ABANDONED, DELETE_PENDING, and DELETED. The current M2 repository accepts seven source literals: five in that adopted set (`INPUT_PROCESSING`, `SUBJECT_REVIEW`, `PREPARATION_REVIEW`, `SCRIPT_REVIEW`, `VIDEO_ADMISSION_PENDING`) and two source-only literals (`SCRIPT_GENERATING`, `SCRIPT_GENERATION_UNKNOWN`). It rejects eight SRS-eligible states with 409 `INVALID_STATE_TRANSITION`: `DRAFT`, `INPUT_REVIEW`, `STORY_GENERATING`, `VIDEO_QUEUED`, `VIDEO_GENERATING`, `VIDEO_SAFETY_VALIDATING`, `VIDEO_READY`, and `SAFETY_BLOCKED`. The public response schema also lacks ABANDONED and DELETED. Q-STATES must be answered before this state behavior is implemented or represented as SRS-compatible.

### 3.2 Explicit DELETE

UC-07 at SRS lines 1469–1475 and §21.2 line 1674 specify an owner-authorized lifecycle DELETE for a run that has completed, a 202 deletion request/status, new playback-token blocking, deletion of eligible run-linked private content, retryable object deletion, preservation of valid independent shared-asset references, and metadata-only audit. D-209 explicitly leaves the meaning of “đã hoàn tất” for FAILED and ABANDONED open. No automatic purge of FAILED or ABANDONED is authorized. Q-A must be resolved against the SRS before implementation.

### 3.3 Read, purge progress, and terminal state

The SRS defines `StoryRunDetailV1` at line 780 and the aggregated `GET /v1/story-runs/{id}` at lines 805, 1164, and 1811, including a safe timeline, module-composed status, authorized references, and no cross-schema SQL or client-side fan-out. D-208 proposed this owner-scoped GET as the default and required DELETE_PENDING until verified deletion; D-209 carries that direction only where consistent. The M2 owner disposition at `approvals/TASK_APPROVAL.md:3250` records the missing StoryRunDetailV1 timeline as OPEN-OWNER and non-blocking for the bounded M2 client integration decision. It does not establish lifecycle purge evidence.

Keep DELETE_PENDING visible until the approved owner-module completion predicate is met. Report DELETED only after positive evidence for every required content reference or an approved, positively reconciled independent shared reference. Never treat access denial, a missing read response, or best-effort job cancellation as proof of deletion. The SRS does not define exact progress fields, internal phases, or a percentage scale. Q-READ, Q-PARENT, and Q-WORKFLOW remain open; do not invent a public state or progress percentage.

### 3.4 Preservation and retention

Do not refund accepted video quota or erase the minimum accounting metadata. Preserve a successful Teacher sample claim and its claim time; clear only run/media pointers supported by the approved Lesson contract. Do not purge content solely because a run is FAILED or ABANDONED. SRS NFR-31 and the retention register require user-requested deletion for retained synthetic content and a real-data gate until maximum retention, backup expiry/deletion, DSR, and deletion evidence are decided. Audit remains metadata-only; its readers, physical mapping, and record-type 180/365-day retention map remain open under the SRS.

## 4. Current source facts and verification limits

These are static observations in the root checkout at branch `feature/feat063-m2-parent-teacher-foundation`, HEAD `08439b22fc3c1f34786a3f45f34530075a3914e0`. They do not prove runtime, database, migration, generated OpenAPI, provider, or object-store behavior.

| Area | Source fact | Evidence and limit |
|---|---|---|
| Parent cancel route | `POST /v1/story-runs/{run_id}/cancel` is declared, returns HTTP 202, and accepts an `Idempotency-Key` length of 1–256. | `backend/src/sketch2life/interfaces/http/routers/parent_story_runs.py:253-294`; runtime not verified. |
| Composition | The Parent StoryRun router is included conditionally; the combined profile passes a non-demo condition. | `backend/src/sketch2life/interfaces/http/router_composition.py:61,75-76`; `backend/src/sketch2life/interfaces/http/app.py:1124-1127`; static registration only. |
| Cancel persistence | The repository checks stored receipt scope/fingerprint, replays an identical request, returns 400 `INVALID_IDEMPOTENCY_KEY` for a mismatched fingerprint, checks expected revision, applies the seven-state source set, sets DELETE_PENDING, releases the Parent active lock, increments revision/version, stores the successful receipt, and commits. | `backend/src/sketch2life/infrastructure/persistence/parent_story_repository.py:328-438`, especially 361-369. This method does not prove an integrated lifecycle request, notice, or purge receipt. |
| Idempotency provenance | SRS §21.4 line 1697 states that the same key/payload returns the initial result and reusing a key with a different payload returns `INVALID_IDEMPOTENCY_KEY`. D-066-68 C-D5 specifies one 1–128 visible-ASCII value and missing-key `400 INVALID_REQUEST`; C-D6 specifies durable successful receipts. Those D-066-68 items do not themselves state the changed-payload rule. | SRS `:1697`; FEAT-066 `DECISIONS.md` D-066-68 C-D5/C-D6; repository `:361-369`. The current route's 1–256 limit differs from C-D5 and needs a separately approved resolution. |
| State schema | `ParentStoryRunResponseV1` includes source-only script-generation values, FAILED, COMPLETED, and DELETE_PENDING; it omits ABANDONED and DELETED. | `backend/src/sketch2life/contracts/schemas/parent_story_runs.py:110-117`; no SRS-complete lifecycle response is established. |
| Parent lifecycle request | Existing `DataLifecycleRequestModel` requires `organization_id`. | `backend/src/sketch2life/infrastructure/persistence/be1_models.py:555-579`; it cannot represent Parent scope as-is. Never fabricate an organization ID. |
| Core Asset | `CoreAssetMetadataPort` exposes metadata save/get, not reference closure or deletion. Byte deletion alone cannot prove shared-reference safety. | `backend/src/sketch2life/application/ports/core_foundation.py:181-186`; `application/ports/object_storage.py`; `infrastructure/persistence/core_store.py`. No candidate path yet for the missing Core reference-closure contract. |
| Teacher authorization | No Teacher lifecycle route or current-assignment resolver was observed. `Be1ParentRoleAdapter` checks an active Parent role; it is not a current Teacher assignment resolver. | `backend/src/sketch2life/infrastructure/persistence/be1_parent_role_adapter.py`; no runtime authorization verified. No candidate path yet for the missing current-assignment authorization contract. |
| AI Jobs | Generic cancellation-notice support exists, but the Parent handler is not shown wired to it; the existing notice is organization-scoped. | `backend/src/sketch2life/application/services/ai_jobs.py:545-583` and AI Jobs ports. No proof of dispatch or provider interruption. |
| Runtime and data | Route calls, database contents, migrations, cache/token behavior, object storage, and provider behavior were not exercised. | NOT VERIFIED. |

## 5. Proposed transport conventions for a later approved slice

These conventions are recorded in FEAT-066 D-066-68 and are not a replacement for product requirements or an FR-C-08 approval. Confirm their exact scope at the later approval.

- Error body fields: `code`, `message`, `correlation_id`, `retryable`, `retry_after_seconds`, and `field_errors`; `current_version` may accompany `STALE_REVISION`; `request_id` may alias `correlation_id`.
- `X-Request-ID` equals body `correlation_id`.
- Shape validation returns HTTP 400 `INVALID_REQUEST`; semantic domain outcomes use their separately approved mappings.
- Nonexistent and out-of-scope resources return the same-shape 404 `RESOURCE_NOT_FOUND`; use 403 `ACTION_NOT_ALLOWED` only after scope is established.
- State-changing commands use exactly one `Idempotency-Key` value, 1–128 visible ASCII; missing key returns 400 `INVALID_REQUEST`. The same key/payload replays the original result; changed payload returns 400 `INVALID_IDEMPOTENCY_KEY` as required by SRS §21.4 and observed in M2 source, not by D-066-68 C-D5/C-D6.
- Parent concurrency uses body `expected_revision`; stale requests return 409 `STALE_REVISION` with current version, not 412.

The current M2 1–256 header limit is an observed source fact, not the selected convention. Resolve it only through a separately reviewed and approved exact scope.

## 6. Cross-module ownership and blockers

D-208 proposed BE1 coordination, Story ownership of run state/active lock/cancellation event, AI Jobs best-effort cancellation, Core Asset reference resolution/deletion, and Lesson preservation of successful sample claims. D-209 carries those directions only where consistent with the adopted SRS. They do not establish physical Parent-scope storage, a durable receipt owner, a Teacher assignment source, or owner-module purge evidence.

| Open item | Required decision or evidence |
|---|---|
| Q-A | Owner-defined explicit DELETE eligibility for COMPLETED, FAILED, and ABANDONED under D-209. |
| Q-STATES | Reconcile the M2 source state set and response schema with the adopted 13 eligible cancel states without silently adding a public state. |
| Q-PARENT | Typed `PARENT_ACCOUNT` request, durable receipt ownership, cross-module contract, and physical mapping. |
| Q-TEACHER | Current assignment/version source and adapter, including rechecks at command, read, and content-access boundaries. |
| Q-READ | Exact safe progress projection and positive terminal-deletion evidence predicate. |
| Q-FENCE | Acceptance-time fence across API, download, playback, cache/stream, upload, dispatch, and late results. |
| Q-PURGE | Owner-module reference enumeration/removal, retry, and positive shared-reference proof. |
| Q-WORKFLOW | Durable records for acceptance, per-owner work, retries, reconciliation, and completion without new public StoryRun states. |
| Q-AUDIT | Approved metadata fields/readers, Parent physical scope, and 180/365-day record-type map. |
| Q-BASE | Exact FR-C-08 branch/commit and sequence relative to CONV-1; current root records do not resolve this. |
| Q-M2-GATE | Owner disposition on whether the accepted M2 closure satisfies D-208 item 8. |
| Q-OWNERS | Named accountable people before launch, as a governance gate. |

Any required DTR row, physical schema, migration, route, public state, unallowlisted source path, or verification command requires separate review and approval. No owner decision is inferred from this list.

## 7. Acceptance outcomes for a future approved implementation

1. Owner-approved command eligibility and current Parent/Teacher authorization are explicit and mapped to the adopted SRS.
2. A successful cancel releases the active lock in its acceptance transaction and creates a typed, idempotent request/receipt without a fabricated `organization_id`.
3. Approved access and dispatch fences prevent new access and late results from becoming playable after accepted cancellation.
4. Best-effort provider cancellation is distinct from lifecycle purge; required content remains pending until owner-module evidence proves deletion or an approved independent reference remains valid.
5. Retries are restart-safe and idempotent; partial failure cannot report a false terminal state.
6. Accepted quota usage and successful Teacher sample claims remain; shared/unrelated assets are not deleted.
7. Audit contains only approved metadata and follows the approved scope, readers, and retention mapping.
8. Static composition/OpenAPI evidence remains distinct from runtime evidence.

## 8. Lineage, scope, and status

Lifecycle Contract Draft 3 and Allowlist Draft 5 are unavailable; see `FR_C08_LOST_DRAFTS_NOTE_REV2_20261118.md`. This Contract Draft 5 succeeds surviving Draft 4; it does not reconstruct the missing Draft 3. Allowlist Draft 7 is the matching successor. The broader pin audit is local and git-ignored at `tmp/frc08-wave1/PIN_AUDIT_R3.md`; the allowlist itself carries its candidate and relevant frozen-source pins.

**FR-C-08 remains DRAFT / NOT APPROVED / NOT LAUNCHED; implementation is blocked by open product interpretation, module contracts, authorization, lifecycle evidence, and separate approval.** No tests, validators, builds, OpenAPI generation, runtime, database, migration, Docker, network, provider, or Modal operation was run. No existing source, test, SRS, decision, approval, context, status, or predecessor file was changed.
