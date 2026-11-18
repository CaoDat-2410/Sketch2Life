# FR-C-08 Parent/Teacher Cancellation, Deletion, and Purge — Implementation Specification Draft 1

**Status: DRAFT / NOT APPROVED / NOT LAUNCHED.** Planning only. This specification authorizes no source or test edits, database or migration access, provider or Modal call, gate, implementation allowlist, command, Task Approval, staging, commit, push, or launch. `OWNER_MODAL_CALL_APPROVED=NO`.

## 1. Purpose and boundary

Define the separate future implementation task needed to complete Rev67 FR-C-08 for Parent and Teacher StoryRuns. The task must cover the full lifecycle after an adult cancels an unfinished run or requests deletion of a completed run: immediate authorization and access revocation, best-effort AI-job/provider cancellation, late-result fencing, durable lifecycle work, idempotent purge/retry, safe progress reporting, and the `DELETED` completion condition.

This is not an M2 S2 continuation or a declaration that M2 is complete. D-205 approves Draft 18 only as the bounded S2 specification; D-207 approves only the separate M2 allowlist and its command ceilings. Neither record authorizes this FR-C-08 work. Do not reuse D-207's M2 path list or its consumed command ceilings. Preserve D-194 through D-207 and Draft 18 unchanged. In particular, preserve the M2 response/cancel contracts and recorded Rev67 deviations; any change to them requires a separate owner decision.

## 2. Authority and evidence classes

### Canonical requirements

The current working SRS is FEAT-063 v2.7-draft Rev67 (2026-11-13), canonical under D-203 and still unsigned. The matching Data Table Register (DTR) is a logical model register; it does not prove the current task database or a deployed physical schema. Relevant requirements are:

| Source | Requirement used by this specification |
|---|---|
| Rev67 §6.1.1, lines 387–395 | StoryRun state inventory and separation from AiJob state; cancellation enters `DELETE_PENDING`; closed states release the active lock; Teacher sample claim survives run deletion. |
| Rev67 FR-C-08, line 499; UC-07, lines 1464–1474; UC-11, lines 1512–1522 | Cancel an unfinished run or delete a completed run through lifecycle; current Parent owner or currently assigned Teacher; immediate lock release; revocation, lifecycle request, best-effort job/provider cancel, linked-content purge, progress, and metadata-only audit. |
| Rev67 BR-26, line 269; BR-40, line 283 | Delete linked run content, do not reopen a claimed Teacher sample, do not refund accepted video quota, and retain only the required metadata. |
| Rev67 §§9.8, 21.2, 21.3, 21.4, and 21.6, lines 846–861 and 1629–1728 | Safe public error envelope; proposed resource route shapes; upload/playback controls; idempotency/revision rules; recovery and polling behavior. §21.2 says route shapes are framework for a contract that must be finalized, not authorization to invent an API. |
| Rev67 event catalog, lines 1844–1845 | `StoryRunCancellationRequestedV1` is Story-owned and contains run ref, actor ref, expected revision, lifecycle request ref, and safe reason code, with no media/content. `StoryRunDeletedV1` contains run ref, lifecycle request ref, and scope. |
| Rev67 NFR-34, line 2706; §31.10(17), line 2757 | Deny-by-default and tenant isolation apply to API, download, token, cache, and job dispatch; changes are audited metadata-only. Audit field allowlist, authorization, physical mapping, and the record-type assignment of 180/365-day retention targets remain OPEN-TECHNICAL. |
| Matching DTR, §§4–6 and 14.7, including lines 247, 310–312, 352, and 395 | BE1 lifecycle requests, Core asset metadata/lineage and upload sessions/parts, Lesson occurrence sample pointers, and append-only Billing usage have separate owners and typed references. A logical mapping is not evidence of database contents. |

### Evidence classes

- **Observed source fact** means read from the current worktree bytes and pinned below. It does not establish that code was exercised or that a database is at that revision.
- **Runtime-verified fact:** none was produced for this planning task. No app, worker, database, provider, storage service, or test was run.
- **Proposed behavior** below is a requirement-derived future acceptance target. Where Rev67, DTR, or the preserved owner decisions do not define a value or route, the item stays OPEN and is not turned into an implementation contract here.

### Authority and decision constraints

- D-203 makes Rev67 the canonical working SRS and supersedes D-195 only for that selection. Rev67 remains unsigned.
- D-196 through D-204 and D-206 preserve M2 S2's bounded decisions, including no-additive-DDL in S2, the Parent cancel response/receipt, `run_revision`, cancel idempotency/revision behavior, and late-result guard behavior. D-205 approves only the Draft 18 specification. D-207 approves only its M2 implementation allowlist and launch boundary.
- This task does not revise any of those records. It does not claim that `DELETE_PENDING` or D-199's `purge_state=PENDING` means deletion completed.
- S2 remains **PARTIAL / NOT COMPLETE** in the pinned implementation report. That report records an OpenAPI tag mismatch, an app-composition `tmp_path` `WinError 5`, 335 mypy errors, and 17 Ruff diagnostics. Those are not resolved or accepted by this plan, and M2's earlier test/typecheck/lint ceilings do not transfer here.

## 3. Current static baseline

The M2 working tree already has Parent cancel code that statically checks an expected run revision, replays a saved `CANCEL_RUN` receipt before comparing the revision, changes an eligible run to `DELETE_PENDING`, clears `active_owner_parent_account_id`, and advances the revision. The current handler is Parent-only and its current seven-state guard accepts `INPUT_PROCESSING`, `SUBJECT_REVIEW`, `PREPARATION_REVIEW`, `SCRIPT_GENERATING`, `SCRIPT_GENERATION_UNKNOWN`, `SCRIPT_REVIEW`, and `VIDEO_ADMISSION_PENDING`. The `SCRIPT_GENERATION_UNKNOWN` value is not in Rev67's StoryRun inventory. This is source inspection only (`parent_story_repository.py`, `cancel_run`; `parent_story_runs.py`, `_require_parent` and cancel route); it does not prove runtime behavior or complete SRS state coverage.

The current cancel path records a pending receipt. Static inspection does not show it creating the Rev67 lifecycle request/event, revoking existing playback/upload access, cancelling an AI job/provider, or running a content purge. Therefore the present `DELETE_PENDING` transition is only an entry point, not FR-C-08 completion.

Other source evidence is partial:

- `DataLifecycleRequestModel` statically maps `be1_data_lifecycle_requests` with request, state, unresolved-item count, result reference, actor, and timestamps; its `organization_id` is non-null, and its source check lists `requested`, `running`, `awaiting_external_purge`, `completed`, and `exception`. The DTR requires Parent-owned records to use typed `PARENT_ACCOUNT` scope and forbids a fake organization. This plan identifies no approved Parent-scoped representation, so the BE1 row cannot be presumed to store a Parent lifecycle request. This does not select the FR-C-08 state contract or prove the task database has the model.
- The AI Jobs service statically has `cancel_job` and idempotent `apply_cancellation_notice`; the SQL repository and migration statically define cancellation-notice storage. The current Parent cancel path does not call them. Cross-owner routing and retry/reconciliation remain unverified.
- `ObjectStoragePort` has `delete_object`; the S3-compatible adapter maps storage errors to `ObjectStorageFailure`. This deletes object bytes only; it does not remove Core metadata/lineage or resolve shared references. This does not prove request-level idempotency, shared-asset safety, token/cache revocation, or retry durability.
- The current `CoreAssetMetadataPort` and `CoreStore` expose save/get operations only in the inspected source. The DTR and migration source describe Core asset metadata/lineage, upload sessions/parts, Lesson occurrence sample fields, and Billing usage, but neither source establishes the current task database, physical foreign keys, all StoryRun content references, a Core-owned metadata/lineage deletion and reference-resolution operation, or an end-to-end purge worker. The Core Asset owner contract and exact implementation paths are therefore a hard prerequisite for C5; Story-owned direct writes to Core tables are not an alternative.

Dirty M2 source is a moving implementation snapshot. The current repository and router hashes still match Draft 2's two informational source pins. Other M2-edited files were not pinned by Draft 2 §9; their current values are recorded in the companion allowlist, not treated as a failed hard pin. The separate plan is based on a fresh recheck before any future launch.

## 4. Lifecycle state and action semantics

### Rev67 StoryRun state inventory

The complete Rev67 StoryRun state inventory in §6.1.1 is:

`DRAFT`, `INPUT_PROCESSING`, `INPUT_REVIEW`, `SUBJECT_REVIEW`, `PREPARATION_REVIEW`, `STORY_GENERATING`, `SCRIPT_REVIEW`, `VIDEO_ADMISSION_PENDING`, `VIDEO_QUEUED`, `VIDEO_GENERATING`, `VIDEO_SAFETY_VALIDATING`, `VIDEO_READY`, `SAFETY_BLOCKED`, `COMPLETED`, `FAILED`, `ABANDONED`, `DELETE_PENDING`, `DELETED`.

AiJob is a separate aggregate with `QUEUED`, `RUNNING`, `RETRY_WAIT`, `SUCCEEDED`, `FAILED`, `CANCEL_REQUESTED`, `CANCELLED`, `STALE`, and `AWAITING_RECONCILIATION`. Never substitute an AiJob state for a StoryRun state or invent a purge state by borrowing an unrelated enum.

### Cancel unfinished run versus delete completed run

- **Cancel:** Rev67 UC-11 describes an unfinished run whose current run revision is known. The operation must check current authorization, action eligibility, expected revision and idempotency. On accepted cancellation, the Story owner atomically moves the run to `DELETE_PENDING` and releases its active lock. It must not wait for a provider interrupt to release the lock. D-199–D-204 remain controlling for the already-approved M2 Parent cancel response and replay behavior; this plan neither edits that API nor claims it is sufficient for Teacher or the full FR-C-08 lifecycle.
- **Delete completed:** Rev67 UC-07 is a separate adult request for an already completed run and starts lifecycle deletion. It is not the unfinished-run cancel command, is not a video-only delete, and must not be given a route/body/status not selected by the owner. Rev67 §21.2 includes a proposed DELETE shape, but the final route/response remains OPEN under OQ-1.
- **Eligibility gap:** UC-07 names completed runs and UC-11 excludes `COMPLETED`, `FAILED`, `ABANDONED`, `DELETE_PENDING`, and `DELETED` from cancellation. Rev67 does not provide a complete public command contract for deletion of `FAILED` or `ABANDONED` runs. OQ-6 must resolve this before endpoint implementation; this plan does not classify them by inference.
- **No state invention:** The full inventory above is the source. Reconcile the current seven-state cancel whitelist and `SCRIPT_GENERATION_UNKNOWN` drift with an owner-approved transition matrix. If supporting the required current run states needs a new state or unmapped storage, stop for a decision and schema review.

## 5. Proposed end-to-end behavior (not an approved contract)

The steps are a planning sequence only. Exact route, status fields, lifecycle states, owners, and event delivery details remain subject to the open decisions in §10.

1. **Authorize and fence the request.** Resolve an authenticated Parent as the run owner or a Teacher with the currently effective assignment for the run's organization/class/occurrence. Do not authorize by `created_by_actor_ref` or historical assignment. Deny by default and recheck the relevant owner/assignment version before issuing access or accepting lifecycle work. The production Parent role adapter remains NOT COVERED under D-190; Teacher current-assignment resolution and accountable route owner are OPEN.
2. **Check command identity and state.** Use the owner-approved expected run revision and idempotency contract. Preserve D-200 HTTP 400 `INVALID_IDEMPOTENCY_KEY`, D-201 `run_revision`/`expected_revision`, D-204's exact existing M2 cancel success body, and D-206's cancel-only stale `current_version`. Do not create a new receipt field or alter the approved M2 route body in this plan. Define the completed-delete command separately after OQ-1.
3. **Commit cancellation intent.** For accepted unfinished cancel, the Story transaction performs the `DELETE_PENDING` transition and active-lock release. The target workflow must also durably create the SRS-scoped lifecycle request and cancellation intent/event through owner ports/outbox only after the owners confirm the physical mapping. Do not claim a cross-schema SQL transaction. If the current transaction/receipts/outbox cannot record required intent without DDL, stop; the current M2 no-DDL decision is not silently broadened.
4. **Revoke access immediately.** Stop new playback token/grant issuance and prevent prior run-scoped tokens, caches, stream/download paths, upload sessions, and incomplete upload parts from serving or attaching content to the cancelled/deleting run. SRS prohibits public export/download; only the approved private stream path may remain. Determine whether existing short-lived signed grants, HTTP/proxy caches, and partial object uploads can actually be invalidated or fenced. If access persists past acceptance, the request cannot be reported as safely accepted or fully purged; resolve OQ-5.
5. **Request best-effort job/provider cancellation.** Send the agreed idempotent cancellation notice to eligible queued/running AI jobs and provider attempts. This is asynchronous/best-effort; a provider that cannot interrupt does not restore the StoryRun or active lock. Preserve already accepted Billing usage. Do not introduce a new AI Job state, reason code, event field, or callback contract. Define ownership and safe correlation refs under OQ-3.
6. **Fence late results before writes.** Every AI/provider success, failure, timeout/unknown, reconciliation, and dispatch path that could change a cancelled run must recheck the current run state/revision before attaching an asset, changing a StoryRun/job projection, writing a Story revision/result/receipt, or making content playable. A `DELETE_PENDING` run must remain fenced. Late output is stale and cannot be served; any privately written orphan output must be discoverable and cleaned idempotently. Existing D-201/D-202 guards are preserved but do not by themselves prove all video/AI-job callback paths are fenced.
7. **Purge run-owned content idempotently.** Enumerate run-linked input art/audio, transcript/understanding, context/profile snapshot, Story revisions, scene/video outputs, private derived assets, upload session/part objects, and other explicitly mapped run-owned content. Delete through each owning module's port. Check typed references/lineage before deleting a shared asset; retain it while any approved live reference remains. Never delete unrelated profile history, Lesson source documents/plans, or assets belonging to another run solely because one run points to them.
8. **Retry and reconcile.** Persist enough already-mapped owner data/outbox evidence to resume after duplicate delivery, partial object-store failure, timeout, process restart, or uncertain provider response. Retry only idempotently; preserve `unresolved_items`/result references only if the owner-approved mapping supports their meaning. Do not invent lifecycle state names, percentages, retry counts, error fields, or a per-object table. If durable work/retry state needs an unmapped field/table, stop for DTR amendment, owner decision, and a separate migration approval.
9. **Report progress and finish.** Provide only the owner-authorized read surface and fields selected in OQ-1/OQ-2. Do not claim `purge_state=PENDING` is completion and do not invent percentages. `DELETED` is reached only when the approved deletion scope has been verified: every run-owned/private content item and unattached partial upload byte in scope has been deleted through its owning module/store and the deletion outcome verified. Access revocation or proof that retained bytes are inaccessible is a separate security fence and does not satisfy purge. Shared assets are excluded from deletion only while a valid independent reference remains; that shared reference does not make run-owned copies or partial upload bytes purged. The late-result fence must be effective, and no required purge item may be unresolved. If policy requires retaining run-owned content or deletion cannot be verified, keep the lifecycle pending and seek explicit SRS/owner reconciliation; do not report `DELETED` by inference. If late provider output can still appear and cannot be fenced/orphan-cleaned, the lifecycle must not be reported complete. The exact status representation remains OPEN.

### Event boundaries

Rev67's `StoryRunCancellationRequestedV1` and `StoryRunDeletedV1` payloads are the only lifecycle event shapes sourced here (event catalog lines 1844–1845). Carry only the listed opaque refs and safe reason code. Do not put artwork, transcript, Story text, signed URL, provider payload, child identity data, or deletion manifests into the event. Whether these are emitted through the current outbox and which module owns the lifecycle request are OPEN. No additional event or field is proposed.

## 6. Invariants and acceptance targets

Acceptance below is a future test/evidence target, **NOT RUN** and not an API/Task Approval.

| ID | Future acceptance target | Trace / stop condition |
|---|---|---|
| FR08-01 | Parent owner and currently assigned Teacher can request only the allowed action; former Teacher, unrelated Parent, creator provenance, cross-tenant IDs, and unauthenticated callers cannot access or delete the run. | Rev67 UC-07/UC-11, NFR-34; D-190 coverage limitation. Stop if assignment resolver, role, or route owner is unassigned. |
| FR08-02 | Cancel changes an eligible unfinished run once to `DELETE_PENDING` and releases the active lock atomically; replay/conflict/stale behavior matches D-199–D-204 and the eventual approved contract. Completed delete is a separate command after OQ-1. | Rev67 UC-11/§21.4; D-199–D-204, D-206. Do not create a second route/body contract by inference. |
| FR08-03 | New and previously issued playback/upload/download/cache access is refused after accepted cancel/delete; a partial upload cannot be finalized or attached after its run is fenced. | Rev67 FR-C-08/§21.3/NFR-34; prove each token, cache, stream, upload-session and part path. Stop if an already issued credential remains usable. |
| FR08-04 | Best-effort cancellation is delivered idempotently to eligible jobs/providers without refunding an accepted video request; unavailable providers do not retain the active StoryRun lock. | Rev67 UC-11, BR-26/40, §21.6; keep AiJob separate. Do not claim provider invocation in planning evidence. |
| FR08-05 | Every late success/failure/unknown/reconciliation path is fenced before run/result/revision/receipt writes; late output cannot restore state or become playable and is handled by purge. | Rev67 §6.1.1/§21.6, D-201/D-202. Cover Story, artwork, video, worker and reconciler callbacks; stop on an unguarded writer. |
| FR08-06 | Repeated or restarted lifecycle work converges idempotently after partial failure. Shared assets remain while a valid independent reference exists; unrelated profile, Lesson, quota, and audit records are not deleted. | Rev67 UC-07/BR-26, DTR Core/Lesson/Billing mappings. Physical task DB and reference resolver must be verified under a separate approval. |
| FR08-07 | The approved owner-scoped read reports lifecycle progress with exactly the chosen status contract; no unsupported percentage or guessed state is exposed. | Rev67 FR-C-08/§21.2/§21.6; OQ-1/OQ-2. |
| FR08-08 | `DELETED` is emitted only after deletion of every required run-owned item is verified and no required work remains; access revocation alone is not purge completion, and duplicates, late outputs, or shared references do not falsely complete it. | Rev67 FR-C-08/UC-07/UC-11/event catalog; DTR §8; OQ-2/OQ-3/OQ-5/OQ-7. No new completion state or unresolved-item meaning is inferred. |
| FR08-09 | An accepted Billing quota usage row remains append-only and is not refunded/deleted. For a successful Teacher sample, clear only the run/media pointer while retaining `SAMPLE_USED` and the original claim time; never reopen the slot. | Rev67 BR-26/BR-40, §6.1.1; DTR `billing.video_quota_usage` and `lesson.occurrences`. |
| FR08-10 | Audit contains only owner-approved metadata fields, is permission-checked, and follows an approved record-type retention mapping. No child content, media, transcript, prompt, token, URL, or provider payload is logged. | Rev67 NFR-34/§31.10(17). Keep the field allowlist, audit authorization, physical mapping, and 180/365-day assignment OPEN until approved. |

## 7. Work breakdown and dependencies

| ID | Outcome | Depends on | Acceptance evidence | Effort / risk |
|---|---|---|---|---|
| C0 | Freeze a fresh code/data baseline; inventory every StoryRun writer, route, media grant/cache, upload session/part, job/provider callback, asset lineage, Teacher occurrence pointer and relevant owner port. | Separate task opened; re-pin current working tree. | Pin report; source-to-requirement matrix; no database claim. | Medium / high because current M2 tree is dirty and route evidence is incomplete. |
| C1 | Resolve Draft 2 §7 decisions 1–9 and assign accountable Story, BE1, AI Jobs, Core Asset, Lesson, Billing, security, and test owners. | C0. | Recorded owner answers and final route/event/state/data-owner contracts. | Large / blocking. |
| C2 | Specify authorization, idempotency/revision, cancellation/deletion requests, events, progress/read contract and API error/status envelope. | C1. | Independent contract review; every public field maps to Rev67 or an owner decision. | Large / blocking. |
| C3 | Implement the atomic Story fence/lock behavior and durable lifecycle intent through approved owner ports/outbox. | C1–C2; current D-199–D-206 preserved. | Transactional concurrency, replay, restart and no-cross-owner-SQL evidence. | Large / high. |
| C4 | Implement immediate revocation, best-effort job/provider cancellation and all late-result fences. | C2–C3; token/upload/cache/job owners identified. | Path-by-path deny evidence and late callback regression tests. | Large / high. |
| C5 | Implement purge traversal/retry, Core-owned metadata/lineage deletion and reference reconciliation, Teacher pointer clearing, accounting/audit preservation and approved `DELETED` predicate. | C1–C4; Core Asset owner contract and exact paths approved; schema mapping/DDL disposition approved. | Synthetic object+metadata purge, valid shared-reference retention, partial failure, duplicate/restart, Teacher and billing evidence. | Large / high; BLOCKED until the Core Asset owner contract and required allowlist paths are approved; also blocked if schema or another owner contract is missing. |
| C6 | Run the separately approved checks and fresh independent cold review; record failures honestly. | C2–C5; fresh launch prompt and command ceilings. | All gates and findings dispositioned; no claim beyond evidence. | Large / high. |

## 8. Migration and physical-schema disposition

This draft authorizes **no database or migration action** and contains no migration path in its implementation E/N allowlist. Static migration/model sources include BE1 `be1_data_lifecycle_requests` (`20261014_0002_be1_runtime.py`), Core asset metadata/base tables (`20261014_0001_core_persistence.py`), the AI `cancellation_notice` table (`20261015_ai_0001_ai_jobs_schema.py`), Lesson occurrence/upload tables (`20261028_ll_0001_lesson_library.py`), and StoryRun/Core lineage/upload structures (`20261102_story_run_lite.py`). `20261112_parent_story_context.py` is a later Story migration branch. These file definitions are static evidence only; no Alembic graph/head command or database inspection was performed.

**Core Asset hard blocker:** Rev67 FR-C-08/UC-07/UC-11 and the DTR require deletion of eligible linked content and metadata while retaining a shared asset only when a valid independent reference remains. The inspected `CoreAssetMetadataPort`/`CoreStore` expose save/get only; `ObjectStoragePort.delete_object` does not remove Core metadata/lineage or prove reference closure. The current E/N allowlist therefore cannot complete FR08-06/08 or establish `DELETED`. Do not bypass Core ownership with direct Story writes to Core tables. Before any implementation launch, the Core Asset owner must define the exact reference-resolution, run-owned lineage/metadata deletion, object-deletion ordering, and idempotent result contract; then an owner-approved allowlist revision must name the exact Core-owned paths and acceptance evidence. If that contract needs unmapped schema, use the separate DTR amendment/migration approval path below. Until the Core contract and paths are approved, C5 and any claim of full FR-C-08 completion are blocked; this is not itself an authorization to open the Core task or perform DDL.

The DTR maps the logical owners and fields but also says several physical constraints/owner mappings remain design/DDL gates. The current BE1 lifecycle request model has no evident per-content manifest in the fields read here; the current work item/late-output reconciliation mapping is not established. Do not add a table, column, state value, retention field, FK, or migration to the proposed allowlist. If the agreed workflow cannot be represented by already mapped fields, receipts, outbox and owner APIs, **BLOCK** pending a DTR amendment, exact migration proposal, separate owner approval, and isolated database authorization. Never use or clean the shared task database.

**Parent lifecycle-request scope blocker:** The current BE1 `DataLifecycleRequestModel.organization_id` is non-null, while DTR §2.2 requires Parent-owned rows to use `PARENT_ACCOUNT` scope and explicitly prohibits a fake organization. No approved Parent-scoped request mapping is selected in this plan. Do not write a Parent request into the BE1 organization-scoped row by inventing an organization ID. The owner must define and approve a valid typed Parent scope/owner contract; if that cannot use existing mapped fields and ports, block until the DTR and a separate schema/migration approval define it. Parent lifecycle-request implementation and any full Parent-and-Teacher FR-C-08 completion claim remain blocked until this is resolved.

The migration `20261112_parent_story_context.py` contains an empty-`story.runs` baseline guard. The exact task database state is **NOT VERIFIED**. No conclusion about applied migrations, heads, seeded rows, or runtime schema is made.

## 9. Open decisions and owner questions (carried from Draft 2 §7)

All nine Draft 2 decisions remain OPEN. Each must be answered or explicitly accepted as a blocker before the implementation allowlist can be approved.

| # | Open decision | Dependency | Exact question for the owner |
|---|---|---|---|
| 1 | Progress/read contract | Route owner; current Parent owner-scoped run GET; approved UI/runtime consumers. | Is the existing owner-scoped `GET /v1/story-runs/{run_id}` sufficient to expose deletion progress, or should a separate lifecycle-status route be specified? Which exact route, fields, statuses, actor scope and version rules are approved? |
| 2 | Lifecycle status model | BE1 lifecycle owner and current DTR/request model. | Which already-mapped values represent queued, running, retryable failure, unresolved external purge and terminal completion? What does each mean? Are any progress counts safe and defined? If not, shall the API expose status only without percentages/counts? |
| 3 | Lifecycle request owner and Parent scope representation | DTR names BE1 for `be1.data_lifecycle_requests`; current model requires non-null `organization_id`; DTR §2.2 requires Parent scope `PARENT_ACCOUNT` and forbids a fake organization. Story/BE1/Core/AI Jobs ports and outbox. | Which accountable module/team owns request creation, transition, retry, reconciliation, external-purge wait and final result? How is a Parent-scoped request represented without overloading or fabricating `organization_id`? Which existing versioned contract connects Story to it, who owns delivery receipts, and does the chosen mapping require a DTR/schema amendment? Until answered, do not create Parent requests through the BE1 organization-scoped model. |
| 4 | Teacher authorization | Current BE1 assignment source, Parent/Teacher role adapters, route/application owner. | What exact current assignment/version is authoritative for a Teacher cancel/delete request, and which route/application adapter checks it? How is former Teacher access revoked? Who owns this path? |
| 5 | Immediate upload/playback revocation | API stream/token, signed grants, cache/proxy, Core upload-session/part and object storage owners. | Can every previously issued token/grant, cache/stream, active upload session, partial part and download path be denied immediately after acceptance? What exact fence invalidates each, and what is the failure behavior if a credential remains valid? |
| 6 | State/action compatibility | Rev67 §6.1.1/UC-07/UC-11; current seven-state M2 guard; `SCRIPT_GENERATION_UNKNOWN` drift. | Which of the 18 Rev67 StoryRun states are valid for cancel, completed delete, or neither? How are `FAILED`/`ABANDONED` content requests handled? What is the approved disposition of the current extra `SCRIPT_GENERATION_UNKNOWN` value and states omitted by the M2 guard? No new state unless separately approved. |
| 7 | Storage, sharing and retention | Core asset/lineage, upload parts, provider copies/backups, physical ref resolver, real-data gate. | Which exact run-owned refs/objects are in purge scope, how are shared references counted, and what durable retry/reconciliation contract is already mapped? Are backups/provider copies excluded pending a separate retention gate? Which precondition prevents real-data use before retention approval? |
| 8 | M2 evidence disposition | M2 implementation report, D-205/D-207 and fresh current code pins. | Does the owner accept the recorded M2 incomplete baseline for this separate task, or require a separately authorized S2 completion/repair first? Which S2 failures and evidence remain gating? No M2 test or lint ceiling transfers. |
| 9 | Audit fields and retention | Rev67 §31.10(17), DTR audit mapping, audit access owner. | What exact metadata-only fields and actor/resource permissions are approved, where are they physically mapped, and which record types use the 180-day versus 365-day retention target? If no mapping is approved, should the audit criterion remain blocked? |

## 10. Required gates before any implementation approval

1. Resolve §9 decisions or record exact owner-approved blockers; identify named module owners and route/API contracts, including a valid Parent-scoped lifecycle-request representation that does not fabricate an organization.
2. Reconcile current M2 dirty source/test/document paths against a committed or otherwise frozen baseline. Preserve all existing local changes; do not describe them as clean.
3. Complete a static StoryRun transition/writer matrix and lifecycle data-reference map; have each domain owner review their part.
4. Verify current physical migration/schema mapping only under a separate, task-owned database authorization. If DDL is necessary, stop this allowlist and obtain a separate DTR/migration decision.
5. Produce a revised exact-path allowlist with fresh E pins and absent N paths, a fresh independent review, and newly authorized command ceilings.
6. Obtain explicit Task Approval and a separate pinned implementation launch prompt. This Draft 1 does neither.

## 11. Planning input pins

Verified read-only on 2026-11-15. Draft 2 §9 strict pins were rehashed and match. Dirty source pins are informational snapshots, not cleanliness claims.

| Input | Bytes | SHA-256 |
|---|---:|---|
| Frozen lifecycle plan Draft 2 | 24,996 | `300BEC5A0716B8CFC09896E52B9752F5D6EBF499C4BB86822A71AF9D29A41310` |
| `docs/context/SRS_AUTHORITY.md` | 4,054 | `E3783924BCDF0327CCCDA8806773FB4407ED311C7074289D74AB9B9124EAF662` |
| Canonical Rev67 SRS | 634,291 | `B704163C9AAF7BB198D8578699F75DB8766C2226A52CD48B0ED1314AF5E21996` |
| Matching DTR | 171,609 | `7CDFDBECDC24E28BB08E62C98A33B338165350204447EBC59B86F5BE69899BC2` |
| `DECISIONS.md` through D-207 | 212,068 | `191D68D7344FE2146E75F339185065234D092887C341AB487FB2DBEA8511C2BF` |
| `approvals/TASK_APPROVAL.md` including D-207 overlay | 410,676 | `C6A506404AF68A6180E150B83DE120113CE5EA54FCD7DEDFF9EAB01E4D375088` |
| M2 S2 Draft 18 | 101,153 | `5CA09CC6F9D936C1BA74772251F4D3A9C0480F3E6F82818FE11114205FD3E331` |
| M2 Draft 18 cold review | 5,169 | `4CE583BA092D140C62E7F1600E4B58778569885D7F7E3B62FB812839DD09835B` |
| M2 implementation allowlist Draft 1 | 14,768 | `7DCEEB785C2121D250B7C016EDC2030E2CD7912F87BE537F07CC8B359A2A0CE8` |
| M2 implementation allowlist independent review R2 | 2,715 | `6872DA02B2CD88644AED71BA039D9ABBD38F243639DD44EDCCBAF2000C57645D` |
| M2 implementation report | 25,879 | `F49D1FDB2B3C26387FFABC51C316F226C5D1FC5FC12B4856B0A6172A81941F55` |
| M5/M6 BE planning roadmap (historical planning context only) | 20,115 | `A0A485EE421FBB1DA9DEC99DD8EC08279D14EAF27EC548AD6A0A4CE8F234F8FA` |
| Draft 2's reviewed Draft 1 lifecycle plan | 22,501 | `2F879E24BCD50849B2CC826D5E6F510C9173C92C1595503F6BCDA0D40F045D9C` |
| Separate shared OpenAPI mapper planning draft | 20,784 | `48B7A95133BDEAB9D14EE947BAF44D5B475ED60B99D118EAC24B51C9E0561BD6` |
| `docs/context/PROJECT_CONTEXT.md` current working copy | 83,909 | `56DC16E4802A6598E6232D3A4B3361F802BDB54F461C3AE27B9AF2E31D63D061` |
| `docs/context/SOURCE_REGISTER.md` current working copy | 115,881 | `39D8BD4F68ECCB75FF16BBFE775A9BBDB13151E7BD948EE1791071A0DA0B39FC` |
| FEAT-063 `CONTEXT.md` | 113,670 | `7137B59263B7B886F3EB5A18D741DB08F976E3E08947C7BE80679ED3FE50EDEF` |
| FEAT-063 `SOURCE_REGISTER.md` | 66,896 | `08A0AE379D87CD237A923F921E2FC7F1385BAAE63C74F264FEBD24721FC1EED1` |

The companion allowlist records current working-copy pins for each proposed E/N path, including dirty M2 collisions. No source/test runtime, validator, lint, database, or migration verification was performed.

## 12. Work performed and completion status

This draft and its companion allowlist are new planning documents only. No decision, Task Approval, source, test, SRS, DTR, or existing evidence file was changed. No tests, typecheck, lint, validator, diff check, backend, database, migration, Docker, install, network, provider, Modal, stage, commit, or push command was run. All runtime, database, provider, real-data, and purge claims remain unverified.

This document remains **DRAFT / NOT APPROVED / NOT LAUNCHED**. It authorizes no implementation.

## 13. Post-review correction — 2026-11-15

The independent cold review of the prior file pin found P1: §5 step 9 allowed run-owned content and partial upload bytes to be treated as complete when merely proven inaccessible. That conflated immediate access revocation with deletion required by Rev67 FR-C-08, UC-07 and UC-11 and the DTR §8 purge boundary. §5 step 9 and FR08-08 now require verified deletion through the owning module/store; access revocation alone cannot satisfy purge, and unverified or policy-retained content keeps the lifecycle pending until explicit SRS/owner reconciliation. No route, state, owner, schema, retention exception, or implementation authorization was added. This correction changes only this planning document; the companion allowlist remains unchanged. The prior cold-review verdict applies to the prior file pin, so the corrected document needs a fresh independent review before it can be considered ready.

## 14. Post-review correction 2 — 2026-11-15

The next independent cold review found that the companion allowlist had low-level object-byte deletion but no Core-owned metadata/lineage deletion or valid-reference resolution operation. Static source inspection confirms `CoreAssetMetadataPort` and `CoreStore` expose save/get only. This specification now records Core Asset ownership and the exact contract/path approval as a hard prerequisite for C5; the allowlist must be revised before implementation. No direct Story-owned Core-table writes, schema change, migration, route, or implementation authorization was added. The prior review applies to the prior package pins, so the corrected specification and allowlist require another fresh independent review.

## 15. Post-review correction 3 — 2026-11-15

The next independent cold review found that the current BE1 lifecycle-request model requires non-null `organization_id`, while the DTR requires Parent-owned data to use `PARENT_ACCOUNT` scope and forbids a fake organization. This specification now makes the mismatch explicit in the static baseline, expands OQ-3 to require an approved Parent-scoped request representation, and blocks Parent lifecycle-request writes and full FR-C-08 completion until that mapping is resolved. No scope identifier, table, field, contract, DTR amendment, migration, or implementation authorization was invented. A fresh independent review is required for the corrected package pins.
