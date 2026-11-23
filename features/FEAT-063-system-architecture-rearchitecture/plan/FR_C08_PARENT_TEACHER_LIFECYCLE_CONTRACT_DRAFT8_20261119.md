# FR-C-08 Parent StoryRun lifecycle contract — Draft 8

**Status: DRAFT / NOT APPROVED / NOT LAUNCHED.**
**Date:** 2026-11-19.
**Purpose:** Reconcile the planning contract to D-214 and the canonical unsigned SRS. This is not an implementation specification or approval.

## 1. Authority and decisions

D-209 designates the canonical FEAT-063 SRS at features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md as the single unsigned working SRS. The pinned file is 701,157 bytes with SHA-256 B9B1F42D0BB118C19C81607D3913B7E4F1D8B6F673F0C3FBB6402888FEB675F5. Older Rev60, Rev67, and Rev68 files are historical inputs only. The Data Table Register is a companion model source.

D-214 records owner planning dispositions for the twelve questions in Owner Questions Revision 5. It adds to D-208 and D-209; D-208 directions stand only where consistent with D-209. D-214 does not approve this contract, an allowlist, an implementation task, commands, schema changes, tests, launch, provider use, push, or merge.

The D-214 working-tree decision record is 240,776 bytes with SHA-256 6E30C69B5E43C2124B9083B6904FEEAE80D7BCEE0917C635F381BA518D32C723. It is not the same blob as DECISIONS.md at provisional code base 2dddc607, which predates this owner decision. Preserve that provenance distinction and pin the final implementation base later.

D-214 item 11 selects that the owner-accepted M2 closure and limitation ledger satisfy D-208 item 8. The closure is recorded at features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md lines 3243-3247 and features/FEAT-063-system-architecture-rearchitecture/status/STATUS.md line 876; line 873 of that status file is a stale snapshot that predates the owner acceptance. M2 approvals, allowlists, command ceilings, and evidence do not transfer to FR-C-08, and the FR-C-08 baseline is re-pinned at the selected base.

## 2. Scope and phase boundary

The first implementation scope selected by D-214 is Parent only. The lifecycle architecture remains shared across Parent and Teacher. The Teacher authorization adapter is deferred to a separately reviewed contract over a versioned current assignment. This is a recorded scope limit against FR-C-08 and UC-07 wording that also names Teacher. The SRS places the Parent vertical slice in P1 and the Teacher vertical slice in P2 (lines 667-668).

The allowlist is a set of candidate paths only. It does not permit adding a route, schema, migration, DTR delta, or unlisted source path. Existing operations and any new SRS-required route need an exact separately reviewed scope. No application route is authorized by this draft.

## 3. Adopted lifecycle contract

### 3.1 Cancel an unfinished Parent-owned run

SRS line 394 defines the 18 public StoryRun states. UC-11 line 1518 excludes COMPLETED, FAILED, ABANDONED, DELETE_PENDING, and DELETED, leaving 13 cancel-eligible states: DRAFT, INPUT_PROCESSING, INPUT_REVIEW, SUBJECT_REVIEW, PREPARATION_REVIEW, STORY_GENERATING, SCRIPT_REVIEW, VIDEO_ADMISSION_PENDING, VIDEO_QUEUED, VIDEO_GENERATING, VIDEO_SAFETY_VALIDATING, VIDEO_READY, and SAFETY_BLOCKED.

D-214 selects that 13-state set. The two source-only values SCRIPT_GENERATING and SCRIPT_GENERATION_UNKNOWN require an explicit compatibility map or removal. They must not become public StoryRun states. A separate response-schema decision is required because the current source response type omits ABANDONED and DELETED. No state mapping or response-schema design is approved by this document.

### 3.2 Explicit user-requested DELETE

D-214 selects user-triggered DELETE eligibility for COMPLETED, FAILED, and ABANDONED. FAILED and ABANDONED are never purged automatically; their content remains until an authorized user requests deletion. DELETE_PENDING and DELETED accept no new user delete/cancel command.

This owner-selected planning disposition goes beyond the current wording of UC-07, §21.2, and BR-26, which must be aligned in a separate documentation-only SRS revision and independently reviewed before implementation. The SRS currently states that only a completed run can be deleted at UC-07 line 1470 and Section 21.2 line 1674. No automatic purge, new public state, or route is inferred here.

### 3.3 Read progress and verified completion

D-214 selects an owner-approved lifecycle projection on the existing owner-scoped GET /v1/story-runs/{id}; it selects no second read route. An owner-scoped Parent GET already exists in source (section 4) and carries no lifecycle projection. The projection must preserve the SRS StoryRunDetailV1 contract (lines 780, 805, 1164, and 1811), including safe aggregated status and no client-side module fan-out.

The exact fields, actor/scope check, owner evidence, completion predicate, and compatible response schema remain open. Keep DELETE_PENDING until every required owner-module completion condition is positively evidenced. Report DELETED only after verified deletion or an approved independent shared reference has been positively reconciled. Never treat access denial, missing read data, or best-effort provider cancellation as deletion evidence. The source response currently omits ABANDONED and DELETED.

### 3.4 Parent scope, durable workflow, and DTR delta

D-214 selects a separately reviewed DTR/schema and contract proposal that carries typed PARENT_ACCOUNT scope as a delta to the SRS-named be1.data_lifecycle_requests. Never fabricate organization_id for a Parent request. Neither the existing lifecycle request model nor the existing AI Jobs cancellation notice can carry Parent scope as-is, because each has a non-optional organization_id (section 4).

The DTR delta starts from the SRS-named records for UC-11 at line 1523: story.runs, be1.data_lifecycle_requests, ai_jobs.cancellation_notice, and core.asset_metadata/lineage. It adds only what is missing for Parent scope, per-owner acknowledgement, retry, and verified-completion evidence. It adds no public StoryRun state and does not reuse AiJob state as purge state. The physical mapping, durable receipt owner, cross-module contract, and schema changes require a separate review and approval.

### 3.5 Access fence, purge, quota, and audit

D-214 selects a shared lifecycle version/fence checked at each owner access and worker boundary. Race evidence is required for API, download, playback, cache/stream, in-flight upload, job dispatch, and late-result acceptance. Provider interruption remains best-effort and is not proof of purge.

Owner-module acknowledgements, reference closure, and idempotent retry are selected as the purge approach. The Core reference-closure and storage-ownership contracts are missing and block implementation. Keep a shared asset until an independent valid reference has been positively reconciled. Purge must include run-owned linked content, private derivatives, and incomplete upload data through their owning modules. Provider-copy and backup treatment remain unverified; real-data use remains gated.

Accepted quota usage and a successful Teacher sample claim must be preserved. The Teacher claim is outside the first Parent-only implementation scope and cannot be changed by this slice.

D-214 selects a field, reader, scope, and retention matrix in the DTR before any dependent audit write or read. Audit remains metadata-only. The exact field allowlist, reader permissions, Parent physical mapping, and 180/365-day record-type map remain OPEN-TECHNICAL.

## 4. Static source facts at the provisional base

The following are read-only observations from git show at commit 2dddc6076c793b44cbcd5c0fa3e02a4ccc9902df. They do not establish runtime reachability, generated OpenAPI, database state, migration state, provider behavior, or end-to-end purge.

| Area | Observed source fact | Evidence and limit |
|---|---|---|
| Parent cancel operation | A Parent route declares POST /v1/story-runs/{run_id}/cancel, HTTP 202, a body expected_revision, and Idempotency-Key length 1-256. | backend/src/sketch2life/interfaces/http/routers/parent_story_runs.py:253-294; declaration only. |
| Parent response | The cancel response builder writes purge_state=PENDING as a fixed literal; it does not read lifecycle progress or purge receipts. | backend/src/sketch2life/interfaces/http/routers/parent_story_runs.py:276-283; static source only. |
| Parent owner-scoped read | A Parent route declares GET /v1/story-runs/{run_id} with response model ParentStoryRunEnvelopeV1; it checks the Parent principal and reads the caller's run. It is the existing owner-scoped GET that D-214 item 5 extends. | backend/src/sketch2life/interfaces/http/routers/parent_story_runs.py:232-250; declaration only; it carries no lifecycle projection and its response type omits ABANDONED and DELETED. |
| Cancel persistence | The M2 repository checks the stored receipt scope and fingerprint, replays an identical request, returns 400 INVALID_IDEMPOTENCY_KEY for a mismatched fingerprint, checks the expected revision (409 STALE_REVISION with the current version), applies the seven-state source set, sets DELETE_PENDING, releases the Parent active lock, increments revision and version, stores the successful receipt, and commits. | backend/src/sketch2life/infrastructure/persistence/parent_story_repository.py:328-438, especially 360-383. This method does not prove an integrated lifecycle request, notice, or purge receipt. |
| Static composition | The combined profile mounts the Parent router when the demo flag is false. The StoryRun-lite router is mounted in the combined profile when the demo flag is true. | backend/src/sketch2life/interfaces/http/router_composition.py:60-76; backend/src/sketch2life/interfaces/http/app.py:1057-1064; composition only. |
| Separate demo cancel | A second cancel handler is declared at POST /story-runs/{run_ref}/cancel in the StoryRun-lite router and is a separate demo-profile operation. It is not an E candidate for the Parent product route. | backend/src/sketch2life/interfaces/http/routers/story_run_lite.py:193-208 and app.py:1057-1060; static declaration/mount only. |
| Current source state set | The M2 repository accepts five SRS-eligible literals plus SCRIPT_GENERATING and SCRIPT_GENERATION_UNKNOWN; it rejects the remaining eight eligible states. | backend/src/sketch2life/infrastructure/persistence/parent_story_repository.py:385-394; static source only. |
| Current response type | ParentStoryRunResponseV1 omits ABANDONED and DELETED. Its source schema is excluded from this allowlist because a response-schema change needs separate review. | backend/src/sketch2life/contracts/schemas/parent_story_runs.py:110-117; source observation only. |
| Idempotency behavior | SRS §21.4 requires INVALID_IDEMPOTENCY_KEY for a reused key with a changed payload but does not set an HTTP status. D-200 selects HTTP 400; the M2 source returns that code with HTTP 400 at the fingerprint mismatch. | SRS line 1697; FEAT-063 DECISIONS.md D-200; backend/src/sketch2life/infrastructure/persistence/parent_story_repository.py:360-374; source status is not a new FR-C-08 decision. |
| Idempotency-Key range | Five Parent StoryRun POST routes (create, cancel, context-confirmation, subject-confirmation, script-confirmation) declare the Idempotency-Key header with min_length=1 and max_length=256. The CONV-1 convention parser accepts exactly one value of 1 to 128 visible ASCII characters and otherwise returns 400 INVALID_REQUEST. | backend/src/sketch2life/interfaces/http/routers/parent_story_runs.py lines 136, 269, 306, 331, and 362; backend/src/sketch2life/interfaces/http/api_conventions.py:59-69 (range check at line 67). The mismatch needs a separately reviewed resolution; the route range is an observed source fact, not the selected convention. |
| Parent lifecycle mapping | DataLifecycleRequestModel has a non-null organization_id field. | backend/src/sketch2life/infrastructure/persistence/be1_models.py:555-578 at the provisional base; this cannot represent Parent scope without an approved delta. |
| Cancellation notice scope | The existing AI Jobs CancellationNotice has a non-optional organization_id. The SRS UC-11 data list (line 1523) includes ai_jobs.cancellation_notice, so this is a second place, besides the lifecycle request model, where Parent scope cannot be represented. | backend/src/sketch2life/application/ports/ai_jobs.py:249-257; no Parent-scope representation without an approved delta. |
| Teacher assignment source | No versioned current-assignment resolver for the Story lifecycle is established. The existing assignment helper checks active identity/assignment and role/scope but has no assignment-version field. | backend/src/sketch2life/interfaces/http/routers/be1_common.py:88-156; backend/src/sketch2life/interfaces/http/routers/be1_registry.py:107-125; backend/src/sketch2life/infrastructure/persistence/be1_models.py:63-90; runtime freshness is not established. |
| Core reference closure | CoreAssetMetadataPort exposes metadata save/get operations and no reference-closure or deletion operation. | backend/src/sketch2life/application/ports/core_foundation.py:181-186; no Core contract path is added to the allowlist. |
| AI Jobs cancellation | A generic cancellation-notice service method exists, but this source review does not establish that the Parent handler is wired to it or that a provider is interrupted. | backend/src/sketch2life/application/services/ai_jobs.py:545-583; static source only. |
| Client OpenAPI projection | D-212 item 2 records the Parent cancel operation absent from the client-facing projection; D-213 item 3 says the placeholder-name mismatch alone is not independently blocking. | FEAT-063 DECISIONS.md:539-540; governance evidence, not generated OpenAPI or runtime proof. |

### 4.1 Transport conventions recorded for a later approved slice

D-066-68 in the FEAT-066 decision record on the local branch (not in the root checkout) fixes these conventions for later slices, and CONV-1 implements parts of them at the provisional base. They are not an FR-C-08 approval; confirm their exact scope at any later approval.

- Error body fields: code, message, correlation_id, retryable, retry_after_seconds, and field_errors; current_version accompanies STALE_REVISION only (D-066-68 C-D1; backend/src/sketch2life/interfaces/http/error_envelope.py:213-234). The X-Request-ID header equals the body correlation_id (C-D2).
- Shape validation returns HTTP 400 INVALID_REQUEST (C-D3). A nonexistent or out-of-scope resource returns the same-shape 404 RESOURCE_NOT_FOUND; 403 ACTION_NOT_ALLOWED is used only after scope is established (C-D4).
- State-changing commands use exactly one Idempotency-Key value of 1 to 128 visible ASCII characters; a missing key returns 400 INVALID_REQUEST (C-D5; backend/src/sketch2life/interfaces/http/api_conventions.py:59-69). The same key and payload replay the original result; the changed-payload code INVALID_IDEMPOTENCY_KEY comes from SRS §21.4 and the M2 source, not from C-D5 or C-D6.
- Parent concurrency uses a body expected_revision; a stale request returns 409 STALE_REVISION with the current version, never 412 (C-D7; api_conventions.py:72-80).

## 5. Remaining blockers

Before an implementation approval can be considered:
1. A documentation-only SRS revision must align UC-07, §21.2, and BR-26 with D-214 explicit DELETE eligibility.
2. A reviewed compatibility map and response-schema decision must resolve source-only values and the omitted ABANDONED/DELETED values.
3. A DTR/schema and cross-module contract must define Parent scope (for both the lifecycle request and the AI Jobs cancellation notice, each of which has a non-optional organization_id), durable receipt ownership, per-owner acknowledgements, retries, verified completion, and audit mapping.
4. Core Asset must provide the reference-closure and storage-ownership contract; no candidate Core path is known.
5. The GET projection fields, authorization, owner evidence, and positive DELETED predicate must be approved.
6. The exact implementation base and all shared-path pins must be named and recomputed. D-214 is an uncommitted working-tree record and is not present in the base commit pin for DECISIONS.md.
7. Named module owners and the record location must be supplied before launch.
8. The separate client-facing OpenAPI projection issue, route scope, exact error and idempotency transport (including the Idempotency-Key range mismatch between the Parent routes and the CONV-1 convention), and any new route must be reviewed. This draft authorizes no new route.
9. Real-data use remains gated until SRS retention, backup, DSR, and deletion-evidence requirements are resolved.

## 6. Acceptance conditions for a future separately approved task

A later reviewed implementation task must demonstrate:
- exactly the 13 SRS cancel-eligible states with the source-only compatibility map and approved response schema;
- user-requested DELETE for the three D-214-selected states after SRS wording alignment, with no automatic FAILED/ABANDONED purge;
- current Parent authorization and a shared acceptance-time access/worker fence with race evidence;
- typed Parent scope and durable lifecycle receipt without a fabricated organization_id;
- owner-module purge acknowledgements, retry-safe reconciliation, and positive shared-reference closure;
- truthful DELETE_PENDING to DELETED transition from approved evidence;
- preserved consumed quota and successful Teacher sample claim;
- metadata-only audit under the approved matrix and retention map;
- static composition/OpenAPI evidence separate from runtime evidence.

## 7. Lineage and boundary

Contract Draft 8 succeeds Contract Draft 7. Owner Questions Revision 5 records the D-214 dispositions. The matching allowlist successor is Draft 10. The pin audit in tmp/frc08-wave1/PIN_AUDIT_R6.md is local and git-ignored, not a durable repository record.

This contract and the companion allowlist remain DRAFT / NOT APPROVED / NOT LAUNCHED. No existing file was edited and no test, validator, OpenAPI generation, runtime, database, migration, Docker, network, provider, or Modal operation was run.
