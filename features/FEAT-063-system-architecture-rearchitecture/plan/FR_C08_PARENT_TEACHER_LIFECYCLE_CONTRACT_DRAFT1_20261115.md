# FR-C-08 Parent/Teacher StoryRun Lifecycle Contract — Draft 1

**Status: DRAFT / NOT APPROVED / NOT LAUNCHED. BLOCKED FOR IMPLEMENTATION.**  
**Date:** 2026-11-15  
**Authority:** unsigned canonical working SRS Rev68 under D-203 and D-208.  
**Purpose:** record the requirements already settled for cancel, explicit delete, and purge; classify the remaining technical contract gaps using the current source snapshot. This document selects no implementation, route, field, schema, event, state, owner, retention mapping, or command ceiling.

## 1. Authority, scope, and evidence labels

SRS_AUTHORITY.md identifies the current canonical working SRS as Rev68. Rev68 remains an unsigned draft. D-208 supplies nine owner dispositions for FR-C-08 planning; it is not implementation or launch approval. The Data Table Register (DTR) is a companion data-model source, not an alternate SRS. M2 D-205/D-207 approvals are scoped to S2 and do not authorize FR-C-08. The pinned M2 report says PARTIAL / NOT COMPLETE. [DOC-01; DOC-02:39; DOC-03:532-535; DOC-04; DOC-09; DOC-10:3,106,119,133]

Evidence labels used below:

- **Requirement/owner decision:** Rev68 or D-208 states the target rule. This is not evidence that a runtime implements it.
- **Source observed:** a declaration or code path exists in the pinned, dirty BE worktree. It is not proof of runtime behavior, deployment, database contents, or complete contract conformance.
- **Statically composed:** source registration includes a router under a composition path. No app was run and no endpoint was exercised.
- **Test present, not run here:** the named test file exists. This task ran no tests. Historical test output is identified separately as output recorded in the pinned M2 report.
- **Runtime/database not verified:** this review performed no backend, database, migration, or provider operation.

No approved FR-C-08 implementation contract was found in the reviewed records. The M2 Parent StoryRun route and its bounded S2 approval are not a purge lifecycle contract. The BE1 organization data-request route is not a typed Parent-scope StoryRun request contract. The SRS and D-208 are the requirements authority for this draft; missing implementation details remain open.

## 2. Settled requirements — do not reopen in this draft

1. **Distinct actions and eligibility.** Cancel is only for the 13 unfinished states listed by UC-11. Explicit user-requested DELETE is for COMPLETED, FAILED, and ABANDONED. FAILED and ABANDONED content is retained until an authorized user requests DELETE; neither state is auto-purged. DELETE_PENDING and DELETED accept no new cancel or delete command. [DOC-02:270,383-384,1518-1521; DOC-03:535]
2. **Terminal reporting.** Keep DELETE_PENDING public until all required run-owned content is verified purged. Only then report DELETED. Do not invent progress percentages or additional public StoryRun states. Use owner-scoped GET /v1/story-runs/{id} as the default lifecycle read; propose a read-contract change only if evidence shows it cannot meet these requirements. [DOC-02:383-384,1736; DOC-03:535]
3. **Ownership and authority.** BE1 coordinates the lifecycle request. Story owns StoryRun state transition, active-lock release, and the cancellation event. Core Asset owns asset/reference resolution and deletion. AI Jobs receives best-effort cancellation requests. Use typed PARENT_ACCOUNT scope; never fabricate organization_id. Authorize the current Parent owner or currently assigned Teacher using current BE1 assignment/version. Former Teacher status and creator provenance alone confer no authority. [DOC-02:270,771,1518,1797,1845,1951; DOC-03:535]
4. **Access and asynchronous work.** On accepted cancel/delete, immediately fence API, download, playback-token, cache, upload, and job-dispatch access. Job/provider cancellation is best-effort. Late results must be fenced, non-playable, and purged. Failure to establish current authorization must deny access; exact in-flight stream/cache/upload behavior still needs a cross-module contract. [DOC-02:270,284,2707; DOC-03:535]
5. **Purge and preservation.** Purge run-owned content, private derivatives, and incomplete upload data through owning modules. A shared asset may remain only after removing the run reference and verifying a valid independent reference. Retained required content keeps the lifecycle pending. Do not claim provider-copy or backup deletion without evidence. Preserve accepted quota usage and a successful Teacher sample claim/time; clear the run/media pointer and do not reopen the sample slot. [DOC-02:270,284,1951; DOC-03:535; DOC-04:284]
6. **Audit.** Audit is metadata-only: actor, action, resource type/ID, time, outcome, and deletion receipt; exclude child media/content, transcript, prompt, and profile-support details. Exact fields, readers, physical mapping, and the assignment of record types to 180/365-day targets remain OPEN-TECHNICAL. [DOC-02:278,2758; DOC-03:535]
7. **M2 coordination.** Reconcile and pin the partial, dirty M2 baseline before FR-C-08 implementation. No M2 approval, allowlist, or command ceiling transfers. [DOC-03:535; DOC-10:3,8-9,119]

## 3. Source and contract observations

### 3.1 Parent run route and lifecycle read

The current BE source declares the Parent run create, active/current, detail, cancel, and other command routes in parent_story_runs.py. The detail GET at lines 232-250 uses the Parent authentication dependency and returns the mapped ParentStoryRunResponseV1. The response mapping includes run_revision and run_state. The schema's run_state literal is not the complete Rev68 inventory and includes SCRIPT_GENERATION_UNKNOWN and DELETE_PENDING but no DELETED value in the inspected definition. The inspected router file contains no DELETE handler. This is source evidence for the current M2 Parent path only; no runtime call was made. [CODE-01:75,97-123,126-353; CODE-02:110-137; CODE-03:104-115; CODE-04:217-317,326-418]

The application composition statically includes Parent StoryRun routes for the non-demo combined profile, while StoryRun-lite demo composition can omit Parent StoryRun routes and mount the demo router. This is source composition, not a runtime deployment assertion. [CODE-07:60-76; CODE-08:271-304,1027-1032; CODE-21; CODE-22]

The current Parent GET source can expose a run revision and some run states, but it does not prove that a purge-verification predicate exists or that GET can safely distinguish verified DELETED from pending purge. It is also Parent-authenticated in the inspected route, not evidence of the current-Teacher assignment/version read contract. Therefore the D-208 default read is settled; the complete lifecycle read contract and terminal proof are not.

### 3.2 BE1 request and assignment sources

The BE1 records router declares organization-scoped data-request create/read operations. It is included in be1_runtime and that router is included by the app's static composition. The request route requires school-admin assignment and constructs a DataLifecycleRequestModel with organization_id. The model's organization_id is required and its lifecycle values describe the existing BE1 request flow. This is not evidence of a Parent-scope StoryRun lifecycle contract or a reusable receipt schema. [CODE-05:46-48,431-498; CODE-06:19-24; CODE-07:40-43; CODE-08:1027-1032; CODE-09:555-583]

The current M2 Parent route checks a verified Parent principal. BE1 has an OrganizationAssignmentModel and role/identity records, but the inspected model and adapter do not establish the D-208 current Teacher assignment/version check across lifecycle reads, media access, upload, and job dispatch. No runtime reassignment/revocation test was run. [CODE-01:75,169-250; CODE-09:37-87; CODE-10:20-39; DOC-03:535]

### 3.3 Story, Core, AI Jobs, and demo sources

- The current Parent repository has an M2 cancel transaction that moves its run to DELETE_PENDING, releases the active Parent lock, and records an M2 command receipt. The reviewed method is not an FR-C08 delete/purge workflow and does not prove cross-module event publication or purge completion. [CODE-04:326-418]
- Rev68 names StoryRunCancellationRequestedV1 and gives a metadata-only logical payload (run ref, actor ref, expected revision, lifecycle request ref, safe reason code). The current source search did not find an implementation of this exact event in the inspected BE source. The event's versioned transport, receipt linkage, and delivery/reconciliation contract remain OPEN-TECHNICAL. [DOC-02:1797,1845; CODE-04]
- CoreAssetMetadataModel can represent PARENT_ACCOUNT with a typed owner reference and a null organization_id. However, the CoreAssetMetadata application value and metadata port/store methods inspected remain organization_id-oriented. The inspected asset port supports save/get, not run-reference enumeration, reference-closure verification, or metadata deletion. ObjectStoragePort exposes raw object deletion, which is not proof of safe asset/reference deletion. [CODE-11:47-57,181-186; CODE-12:143-182; CODE-13:413-465; CODE-14:27-40]
- The existing AI Jobs CancellationNotice requires organization_id. Its cancellation service and JobState lifecycle are separate from public StoryRun state. Provider-copy registry interfaces are also organization-scoped. They are source interfaces, not an approved typed Parent lifecycle contract or evidence that provider copies/backups were deleted. [CODE-15:249-259,550-575; CODE-16:488-584; CODE-17:17-35]
- StoryRun-lite has its own domain, persistence and demo cancellation code. It is not a substitute for the Parent StoryRun/FR-C08 contract. Its state and upload behavior must not be imported into the 18-state Rev68 inventory by analogy. [CODE-21; CODE-22:2575-2690; CODE-23; CODE-08:1027-1032]
- Video playback and Story video routes exist in source, but the inspected interfaces are not proof of FR-C08 run-scoped invalidation of issued tokens, active streams, caches, downloads, or partially uploaded content. No runtime fence or denial was exercised. [CODE-18; CODE-19; CODE-20]

### 3.4 Tests and runtime evidence

The cancellation route test, repository cancellation tests, and Parent AI late-result guard test are present in the source tree. They were not run in this task and do not establish complete FR-C08 behavior. [TEST-01:67-90; TEST-02:77-257; TEST-03:24-49]

The pinned M2 report records the M2 status as PARTIAL / NOT COMPLETE, an owner-reported 82-test selection with 81 passed and one OpenAPI description failure, a later authorized invocation with an OpenAPI tag mismatch and pytest tmp_path PermissionError, and prior mypy/Ruff failures. These are historical test outputs captured by that report, not checks performed or revalidated here. The M2 evidence remains a separate prerequisite; there is no FR-C08 runtime or database verification in this draft. [DOC-10:3,49-53,103-119,133-164]

## 4. Lifecycle contract draft

The following is a transcription and organization of Rev68/D-208 requirements, not an implementation choice. Anything not stated here as settled is listed OPEN in §5.

### 4.1 Public StoryRun state/action matrix

The 18-state inventory is taken verbatim in substance from Rev68 §6.1.1. The action mapping follows Rev68 UC-11, BR-26/BR-40 and D-208. [DOC-02:270,383-394,1518-1521; DOC-03:535]

| Rev68 public StoryRun state | User cancel | Explicit user-requested DELETE | Required disposition |
|---|---|---|---|
| DRAFT | Eligible | No | If cancel is accepted, release active lock and begin lifecycle; keep DELETE_PENDING until verified purge. |
| INPUT_PROCESSING | Eligible | No | Same cancel disposition. |
| INPUT_REVIEW | Eligible | No | Same cancel disposition. |
| SUBJECT_REVIEW | Eligible | No | Same cancel disposition. |
| PREPARATION_REVIEW | Eligible | No | Same cancel disposition. |
| STORY_GENERATING | Eligible | No | Same cancel disposition; fence late results. |
| SCRIPT_REVIEW | Eligible | No | Same cancel disposition. |
| VIDEO_ADMISSION_PENDING | Eligible | No | Same cancel disposition; reconcile pending work without inventing job/purge states. |
| VIDEO_QUEUED | Eligible | No | Same cancel disposition; request best-effort job cancellation and fence results. |
| VIDEO_GENERATING | Eligible | No | Same cancel disposition; provider interruption is best-effort; late output is non-playable and purged. |
| VIDEO_SAFETY_VALIDATING | Eligible | No | Same cancel disposition; fence any result that arrives after cancellation. |
| VIDEO_READY | Eligible | No | Same cancel disposition. |
| SAFETY_BLOCKED | Eligible | No | Same cancel disposition. |
| COMPLETED | No | Eligible | Retain until an authorized user requests DELETE; then keep DELETE_PENDING until verified purge. |
| FAILED | No | Eligible | Never auto-purge; retain until an authorized user explicitly requests DELETE. |
| ABANDONED | No | Eligible | Never auto-purge; retain until an authorized user explicitly requests DELETE. |
| DELETE_PENDING | No | No | Continue owner-module purge/retry/reconciliation; do not accept a new user lifecycle command. |
| DELETED | No | No | Terminal public state only after required purge verification; only SRS-permitted metadata exceptions may remain. |

SCRIPT_GENERATION_UNKNOWN appears in the current M2 Parent source/schema but is not one of Rev68's 18 states. This draft does not add it to the inventory or authorize cancel/delete for it. The compatibility mapping must use an already-approved existing contract or stop for an owner/SRS decision; no replacement state is inferred. [CODE-02:110-137; CODE-04:1204-1208; DOC-02:394; DOC-03:535]

### 4.2 Authorization and typed scope

Every cancel and explicit DELETE is authorized against the current Parent owner or current assigned Teacher. Teacher authorization must use the current BE1 assignment/version on each applicable command/read/access decision; a former assignment, creator ref, cached stale grant, caller-supplied organization ID, or provenance field does not authorize. Deny by default if current authority cannot be resolved. Use typed PARENT_ACCOUNT for Parent-owned request scope; never synthesize organization_id. [DOC-02:270,771,1518,2707,2755; DOC-03:535]

The precise principal/assignment resolver and version source, how the Parent scope is represented across BE1/Story/Core/AI Jobs/Lesson, and how receipt ownership works are OPEN-TECHNICAL. The existing Parent-only role dependency and organization-oriented BE1 assignment/data-request source do not close those gaps. [CODE-01:75,169-250; CODE-05:431-498; CODE-09:63-87,555-583; CODE-10:20-39]

### 4.3 Commands, receipts, revision, and lifecycle read

Rev68 §21.2 describes the cancel and DELETE operations, their actor/state preconditions and lifecycle response. Section 21.4 supplies general command semantics: a state-changing command is idempotent by principal, operation, and target; the same key and payload returns the original result; a different payload with a reused key returns INVALID_IDEMPOTENCY_KEY; revision/hash-sensitive commands reject stale values as STALE_REVISION with the current version. Section 9.8 supplies the safe API error envelope and status/code examples, including HTTP 400 for INVALID_IDEMPOTENCY_KEY. These rules constrain a later lifecycle contract, but do not define its durable receipt owner/schema, cross-module replay boundary, event linkage, or exact DELETE response body. [DOC-02:§9.8,§21.2,§21.4,§21.6,1663-1674,1736,1811; DOC-03:535]

D-208 selects the owner-scoped GET /v1/story-runs/{id} as the default read. This draft adds no route and no response field. If the existing approved read cannot expose the required pending/verified terminal distinction under current authorization, stop and bring the minimal read-contract proposal for separate review; do not infer a status, version, percentage, or receipt field. The M2 cancel request/receipt details remain limited to their S2 approval and are not silently adopted as an FR-C08 DELETE or purge-receipt contract. [DOC-02:1663-1674,1736,1811; DOC-03:535; DOC-09]

A versioned request/receipt contract must eventually define typed scope, aggregate owner, replay boundary, revision check, idempotency behavior, event linkage, and what durable evidence proves purge. D-208 assigns BE1 lifecycle coordination and Story aggregate transition/event ownership; it does not specify a complete cross-module payload or receipt schema. M2's cancel receipt and revision behavior are confined to M2's approved S2 boundary and do not automatically define FR-C08 DELETE or cross-module purge receipts. [DOC-03:535; DOC-04:204,253-254; CODE-04:326-418; DOC-09]

### 4.4 Story transition, lifecycle request, AI Jobs, and late results

On accepted cancel of an eligible unfinished run, Story changes the StoryRun to DELETE_PENDING and releases its active lock in Story's transaction. Story emits the logical StoryRunCancellationRequestedV1 event described by Rev68; BE1 coordinates the lifecycle request. A DELETE request for COMPLETED, FAILED, or ABANDONED follows the same pending-until-verified lifecycle rule, but this draft does not invent whether that request uses an existing Story event, a separate event, or a particular receipt. [DOC-02:270,383-384,1518-1521,1797,1845,1951; DOC-03:535]

AI Job states remain a separate internal lifecycle; they are not StoryRun states or public purge progress. Request cancellation for queued/running work best-effort. A provider may not stop; any late/duplicate output must be fenced from Story state and playback, treated as non-playable, and purged by its owning module. Exact event delivery, cancellation request payload, worker acknowledgment, reconciliation, and proof of late-output removal remain OPEN-TECHNICAL. [DOC-02:394,1520-1521,1797,1845,1951; CODE-15:249-259; CODE-16:488-584; CODE-17:17-35]

### 4.5 Immediate access-revocation requirements

At accepted cancel or DELETE, revocation must apply immediately to each surface below. The requirements are settled; source presence alone is not a revocation proof.

| Surface | Requirement | Current evidence and limit |
|---|---|---|
| API reads and commands | Re-evaluate current authorization and lifecycle fence; deny after acceptance where operation is no longer permitted. | Parent GET/command route is Parent-authenticated in the inspected source; it does not prove current Teacher assignment/version across all paths. [CODE-01:75,169-250] |
| Download | Block new downloads using current run/access state. | No complete FR-C08 download-grant contract or runtime revocation evidence identified in the inspected route set. |
| Playback token | Block issuing a new token after lifecycle acceptance; revoke/fence extant token use. | Playback interfaces exist, but no FR-C08 acceptance fence was runtime verified. [CODE-18:46-123; CODE-19:16-73; CODE-20:56-100] |
| Cache and active stream | Fence cached responses and ongoing streams according to the accepted lifecycle state. | No end-to-end purge/revocation proof; cache invalidation and in-flight stream contract OPEN-TECHNICAL. |
| Upload session/parts | Prevent new parts/finalization and purge incomplete run-owned upload data through Core Upload Session. | Rev68 states the requirement; demo upload tables/code do not prove the production Parent integration or a purge receipt. [DOC-02:270,1951; CODE-21:13-40; CODE-23:28-101] |
| Job dispatch | Prevent a queued/unaccepted job from starting after cancellation; request cancellation for accepted/running work best-effort. | AI Jobs source has cancellation interfaces with organization scope, not an approved Parent typed contract or end-to-end dispatch fence. [CODE-15:249-259,550-575; CODE-16:545-584] |

For every surface, if the current assignment/version, run fence, or revocation result cannot be established, deny new access/acceptance. Exact handling for already-open streams, issued token expiry, cache propagation, upload-part races, and job-dispatch races needs an approved versioned contract and synthetic evidence before implementation.

### 4.6 Purge, shared assets, retries, and proof of DELETED

Purge is performed through each owning module. The minimum requirement is to remove run-owned content, private derivatives, and incomplete upload data; remove all references owned by the run; resolve each asset's ownership and lineage; and verify the deletion outcome from the owning module. A shared asset may be retained only after the run reference is removed and a valid independent reference is positively verified. If that condition cannot be proven, the lifecycle cannot claim DELETED. [DOC-02:270,384,1951; DOC-03:535; DOC-04:253-254]

Retry and reconciliation must be idempotent. A failed, ambiguous, or not-yet-verified purge remains DELETE_PENDING. The terminal predicate is not a new public counter or percentage: it is evidence that every required run-owned content item and private derivative has been removed or safely retained only under the shared-reference rule, all incomplete upload data is purged, all late results are fenced and purged, and owning modules report the required work complete. The exact evidence record, receipt fields, acknowledgments, retry states, and cross-module consistency procedure remain OPEN-TECHNICAL; this draft does not prescribe a new state or schema. [DOC-02:383-384,1520-1521,1951; DOC-03:535]

Do not claim provider-copy or backup deletion unless separately supported by verifiable evidence. Rev68 says the copy/backup disposition needs evidence/policy; provider/backup physical removal is not established by the current source inspection. If any required run-owned content may still exist in a provider copy or backup and there is no approved disposition/evidence, do not report DELETED under an invented exception. [DOC-02:656,1951,2758; DOC-03:535]

### 4.7 Quota, Teacher sample claims, and retained metadata

Accepted quota usage is not refunded because of cancel/delete. A successful Teacher sample claim remains SAMPLE_USED with its original claim time; remove its run/media pointer but never reopen the occurrence slot. There is no separate video-delete operation. These are settled invariants; implementation must show the owning Story/Billing/Lesson evidence and must not infer field-level changes from a logical rule. [DOC-02:270,284,1037; DOC-03:535; DOC-04:284]

Only metadata expressly permitted by Rev68/D-208 may remain by default: lifecycle audit metadata, consumed quota usage metadata, and successful Teacher sample-claim metadata. This does not authorize retaining content, transcript, prompts, support details, media bytes, signed URLs, or provider credentials in audit/log/metric labels. Exact physical fields, owners, and deletion proof remain open. [DOC-02:270,278,2758; DOC-03:535; DOC-04:284]

### 4.8 Audit and retention contract

Logical audit content is limited to actor, action, resource type/ID, time, outcome, and deletion receipt. Child media/content, transcript, prompt, profile-support details, token, and signed URL are excluded. Audit readers must be authorized, but D-208 does not choose the reader role or permission. The exact field allowlist, Parent typed-scope storage, cross-module audit owner, physical mapping, and assignment of each record type to 180 or 365 days are OPEN-TECHNICAL. Do not map the current organization-scoped CoreAuditEntryModel to Parent lifecycle audit by assumption. [DOC-02:278,2758,2996; DOC-03:535; CODE-11:85-93,157-165; CODE-12:187-203; CODE-13:303-324]

## 5. Decision-versus-technical gap assessment

The ten rows below follow Allowlist Draft 4 §5. “OPEN-OWNER” is used only for an owner policy/accountability choice not already settled by D-208. A settled D-208 policy is not relabeled open just because its implementation contract is missing.

| Draft 4 §5 issue and settled authority | Source/contract evidence and classification | Missing decision or contract; effect | Precise question required to close the gap |
|---|---|---|---|
| **1. Lifecycle read and terminal proof.** D-208 selects the owner-scoped GET as default; DELETE_PENDING remains until purge is verified; DELETED only after verification. | Parent GET and response mapping exist in source, with run_revision and a partial run_state schema; inspected schema has no DELETED member. Source does not prove a verified-purge predicate, current Teacher read authorization, or runtime behavior. **OPEN-TECHNICAL; source exists, no complete approved FR-C08 read contract.** [DOC-02:1736; CODE-01:97-123,232-250; CODE-02:110-137] | Define which existing owner-module evidence proves purge and how the default GET exposes pending versus verified terminal state under current authorization. If current GET cannot do so, a separately reviewed read-contract change is required. Blocks implementation/approval of terminal reporting. | Which existing response contract and owner-module evidence can prove DELETE_PENDING versus verified DELETED for both current Parent owner and currently assigned Teacher? If no existing response can represent it, what minimal read-contract revision should be reviewed? |
| **2. Internal lifecycle phases, retries, reconciliation.** StoryRun public states stay separate from BE1 lifecycle request, AI Job, and purge-worker state. | Rev68 defines public StoryRun states and terminal behavior. BE1 organization request and AI Job states exist in source, but are not a complete typed Parent purge workflow; no runtime or persisted purge proof was inspected. **OPEN-TECHNICAL; requirement defined, internal mapping not an approved FR-C08 contract.** [DOC-02:383-394,1520-1521; CODE-05:431-498; CODE-09:555-583; CODE-17:17-35] | Map existing internal values and durable evidence for accepted, in progress, retryable failure, unresolved external deletion, and verified completion without adding StoryRun states. Blocks safe implementation/reconciliation; DTR/schema gate if needed. | Which already-approved internal records and statuses represent each lifecycle phase and retry outcome, and which owner module supplies each completion proof? If none do, what DTR/SRS contract proposal is needed before implementation? |
| **3. Typed Parent scope, cross-module request, receipt ownership.** D-208 requires PARENT_ACCOUNT and forbids fabricated organization_id; it assigns BE1 coordination, Story transition/event, Core deletion/reference resolution, AI Jobs best-effort cancellation. | Core model has a typed Parent owner-scope representation, but current Core application value/metadata port, Core audit, BE1 data-request model, and AI cancellation notice include organization_id. No single approved typed Parent lifecycle request/receipt contract was found. **OPEN-TECHNICAL plus separate DTR/schema gate if existing mapping cannot represent it.** [DOC-02:771,1845; DOC-03:535; CODE-05:431-498; CODE-09:555-583; CODE-11:47-57,181-186; CODE-12:143-182; CODE-15:249-259] | Specify versioned message boundaries, typed owner scope, request/receipt owner, event/receipt correlation, and persistence without inventing fields or SQL. Blocks implementation and approval of cross-module writes. | Which existing approved contract and physical mapping carries PARENT_ACCOUNT through BE1, Story, Core, AI Jobs, and Lesson while preserving each module's ownership? Which module owns the durable lifecycle request and receipt? If none fits, what exact schema/DTR proposal requires separate review? |
| **4. Named accountable people.** D-208 assigns responsibilities and requires named accountable module owners before launch. | D-208 assigns domain boundaries but no people; Draft 4 correctly classifies named-person assignment as a launch gate, distinct from technical ownership/contract gaps. **OPEN-OWNER, G-LAUNCH only.** [DOC-03:535; DOC-07:192-209] | Named accountability is required before launch. It does not by itself block a technical design or implementation approval; unresolved technical interfaces in rows 1-3 and 5-10 remain blockers. | Which named individual accepts accountability for BE1 coordination, Story state/event/fence, Core Asset references/deletion, AI Jobs cancellation, Lesson claim update, and HTTP/test integration, and where will that assignment be recorded before launch? |
| **5. Current Teacher authorization.** Current Parent owner or currently assigned Teacher must be checked against current BE1 assignment/version; former Teacher/creator provenance gives no authority. | Current M2 Parent route authenticates Parent. BE1 has organization assignments and role checks, but inspected sources do not establish one current assignment/version resolver applied to lifecycle reads, commands, media, upload, and dispatch. **OPEN-TECHNICAL; policy settled, enforcement contract/source coverage incomplete.** [DOC-02:270,2707,2755; CODE-01:75,169-250; CODE-05:438,482; CODE-09:63-87; CODE-10:20-39] | Identify the owning current-assignment/version source and enforce/recheck points across all affected surfaces. Blocks implementation/approval of Teacher authorization. | Which BE1 source and versioned adapter must each lifecycle/access path consult, and what contract evidence demonstrates denial immediately after reassignment or revocation? |
| **6. Immediate revocation and in-flight access.** API, download, playback-token, cache/stream, upload, and job-dispatch access are fenced immediately on accepted cancel/delete. | Related routes/ports exist, but the inspected code set does not prove one run-scoped acceptance fence across issued grants, open streams, caches, partial uploads, and queued dispatch. No runtime denial test was run. **OPEN-TECHNICAL; target requirement settled, no complete approved revocation contract/evidence.** [DOC-02:270,2707,1797,1951; CODE-18; CODE-19; CODE-20; CODE-23; CODE-15:249-259] | Contract each path's recheck/invalidation point, race boundary, fail-closed result, and evidence. Blocks implementation/approval of acceptance-time revocation. | For each affected surface, which owner-owned fence invalidates existing and new access at acceptance; what happens when the check/cache/stream/upload/dispatch owner is unavailable; and which synthetic negative evidence proves the fence? |
| **7. State/action mapping.** Rev68 lists 18 public states; D-208 fixes cancel eligibility at 13, explicit DELETE at COMPLETED/FAILED/ABANDONED, and neither at DELETE_PENDING/DELETED. | Source/schema contains partial M2 states and SCRIPT_GENERATION_UNKNOWN, which is absent from Rev68's 18-state list. No FR-C08 adapter mapping or complete test evidence exists. **OPEN-TECHNICAL; owner policy settled, compatibility mapping unresolved.** [DOC-02:394,1518-1521; DOC-03:535; CODE-02:110-137; CODE-04:388,1204-1208] | Preserve the SRS inventory. Resolve how existing source-only SCRIPT_GENERATION_UNKNOWN is handled without inventing a public/domain state. If it needs a new public state or changes eligibility, stop for separate owner/SRS decision. Blocks affected transition implementation. | Which existing compatibility behavior maps SCRIPT_GENERATION_UNKNOWN to an allowed existing outcome without changing Rev68? If none is valid, what separate owner decision is required before implementation? |
| **8. Storage, sharing, incomplete uploads, retries, provider/backup.** Purge through owners; remove run reference before retaining a shared asset and verify an independent valid reference; retries are idempotent; no unsupported provider/backup deletion claim. | Core model supports typed owner scope but the inspected Core port/store expose metadata save/get, not run-reference closure/deletion. Object storage exposes raw byte deletion. Provider-copy interfaces are organization-scoped; no physical provider/backup result was verified. **OPEN-TECHNICAL; separate DTR/schema gate if required owner data or work state is absent.** [DOC-02:270,1951; DOC-03:535; CODE-11:181-186; CODE-12:143-182; CODE-13:413-465; CODE-14:27-40; CODE-15:550-575] | Define owner APIs for enumerating/removing run references, deleting metadata/bytes/incomplete upload parts, confirming independent shared refs, retries, and evidence. Do not infer a table, state, or provider cleanup. Blocks safe purge implementation/approval. | Which existing owner-module contracts enumerate every run-owned ref and prove reference closure, byte/metadata deletion, incomplete-upload cleanup, and safe shared-asset retention? What approved evidence/disposition applies to provider copies and backups? |
| **9. Dirty/partial M2 baseline.** D-208 requires separate reconciliation and pinning before FR-C08 implementation; no M2 authorization transfers. | M2 report is pinned PARTIAL / NOT COMPLETE and records the failed/unavailable checks listed in §3.4. Current worktree also has many dirty M2 paths; no new commands were run here. **G-IMPLEMENTATION coordination prerequisite, not an FR-C08 owner policy question.** [DOC-03:535; DOC-10:3,8-9,49-53,103-119,133-164] | Freeze/reconcile the M2 state and state which evidence is reusable; do not import M2 approval, allowlist, or command ceiling. Blocks FR-C08 implementation start. | Who will reconcile and pin the M2 baseline, disposition the recorded failures/unavailable results, and identify the exact evidence that may be relied on for FR-C08 without marking S2 complete? |
| **10. Audit fields, readers, physical mapping, retention.** Metadata-only categories/exclusions and 180/365-day targets are settled; exact fields/readers/storage/type-to-duration assignment remain open. | Rev68 §31.10(17) and D-208 leave the physical field allowlist, audit reader permission, mapping, and record-type assignment open. Current Core audit port/model is organization-scoped and does not prove a Parent audit mapping. **OPEN-TECHNICAL; DTR/physical-schema gate for dependent audit writes/reads.** [DOC-02:278,2758,2996; DOC-03:535; DOC-04:253-254; CODE-11:85-93,157-165; CODE-12:187-203; CODE-13:303-324] | Approve exact metadata fields and readers, map Parent scope and storage through the owning module, and assign each record class to 180 or 365 days. Blocks implementation of dependent audit behavior and full acceptance. | Which exact metadata fields and roles/readers are authorized, which module and typed scope physically store them, and which record types map to 180 versus 365 days? Which owner-reviewed DTR revision records that mapping? |

## 6. Evidence required before any later implementation proposal

The following are evidence expectations for a future separately approved task, not a test allowlist or authorization:

1. A reviewed versioned contract for request, receipt, replay/revision boundary, event correlation, and owner scope; no fabricated organization_id for Parent.
2. A state/action mapping for all 18 Rev68 states and an explicit existing-source compatibility disposition for SCRIPT_GENERATION_UNKNOWN.
3. Authorization evidence for current Parent owner/current Teacher assignment-version, including former-Teacher denial after reassignment.
4. Per-surface acceptance-fence evidence for API, download, playback tokens, active streams/caches, upload sessions/parts, and dispatch races.
5. Owner-module purge and retry evidence, including private derivatives, shared-reference validation, late results, and proof that DELETE_PENDING cannot become DELETED before required purge closure.
6. Quota and Teacher sample-claim invariants, including preserving accepted usage/SAMPLE_USED/time while clearing the run/media pointer.
7. Metadata-only audit evidence with an owner-approved field/read authorization/physical/retention mapping.
8. A separately reconciled and pinned M2 baseline. FR-C08 test results must come from a later task-specific approval and actual captured output.

No test, typecheck, lint, validator, runtime, database, or migration command was run for this draft. Test existence and historical report outputs are not substitutes for these gates.

## 7. Open questions and stop conditions

These are technical questions remaining after D-208; they do not reopen D-208's settled policy:

- **Lifecycle read:** provide the existing approved read response and owner-module purge proof that establish pending versus verified DELETED. Stop if a new route/status/field is needed; prepare a separate reviewed contract.
- **Lifecycle internal workflow:** identify existing lifecycle-request, worker, retry, reconciliation, and terminal evidence without reusing AiJob or public StoryRun state names by analogy. Stop if new states/schema are required.
- **Parent scope and receipts:** identify the approved typed PARENT_ACCOUNT cross-module request and durable receipt owner/schema. Stop if DTR or physical schema must change pending separate review.
- **Teacher authorization:** identify the current BE1 assignment/version resolver and every required read/command/access check. Stop if authorization depends on unversioned or stale assignment evidence.
- **Revocation:** specify race and failure behavior for every access surface. Stop if any surface can continue to grant access after acceptance or if fail-closed behavior is undefined.
- **State compatibility:** identify an existing mapping for SCRIPT_GENERATION_UNKNOWN without adding it to Rev68. Stop if correct behavior would require a new state or change cancel/delete eligibility.
- **Purge proof:** identify module-owned reference enumeration, deletion, retries, shared-reference proof, upload-part cleanup, and completion evidence. Stop if any required content cannot be verified or if schema work is needed without separate DTR approval.
- **Named accountable people:** obtain named assignments before launch. This remains G-LAUNCH and does not remove technical blockers.
- **M2 coordination:** reconcile and pin the partial/dirty S2 baseline before FR-C08 implementation. No M2 command ceiling transfers.
- **Audit and retention:** obtain an owner-reviewed field/read permission map, physical Parent scope mapping, and record-type-to-180/365-day assignment. Stop before dependent audit implementation until resolved.

## 8. Status and boundaries

FR-C-08 remains **DRAFT / NOT APPROVED / NOT LAUNCHED; BLOCKED FOR IMPLEMENTATION**. This document does not approve an allowlist, a Task Approval, an owner assignment, a command ceiling, a route, a DDL/migration, a provider action, or a launch. It changes no source or test file. It does not claim M2 is complete. A clean independent review of this contract would still be a planning review only.

No database, migration, backend/runtime, provider, Docker, network, Modal, install, test, typecheck, lint, validator, stage, commit, or push operation was performed.

## 9. Evidence and pin register

Paths below are repository-relative to the m2-s2 worktree. Source hashes identify the observed dirty worktree snapshot at the time of drafting; they are not clean-branch or runtime attestations. Exact line citations in the text refer to the pinned bytes in this table.

| ID | File | Bytes | SHA-256 |
|---|---|---:|---|
| DOC-01 | docs/context/SRS_AUTHORITY.md | 4,313 | D6153D38000C95E43A4091C5DF2E856FAD872A33177E3A8542E30EF2BEDCAB60 |
| DOC-02 | features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md (Rev68, unsigned) | 639,948 | 69C83FE49CD4689D5D2540656D3319721838CF7343BAD00E24CDE558B8F5E944 |
| DOC-03 | features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md through D-208 | 216,212 | 52F2E141244829281FF762BA100D1A991D5CADFF042A237C8C125F324300725F |
| DOC-04 | features/FEAT-063-system-architecture-rearchitecture/artifacts/DATA_TABLE_REGISTER.md | 171,609 | 7CDFDBECDC24E28BB08E62C98A33B338165350204447EBC59B86F5BE69899BC2 |
| DOC-05 | features/FEAT-063-system-architecture-rearchitecture/plan/FR_C08_PARENT_TEACHER_CANCEL_PURGE_IMPLEMENTATION_SPEC_DRAFT4_20261115.md | 20,897 | BC268E2354AED6FDC142CCD58BFDF89BACF6585F15B7ED75C8AE7C4C41ED9B70 |
| DOC-06 | features/FEAT-063-system-architecture-rearchitecture/plan/FR_C08_PARENT_TEACHER_CANCEL_PURGE_LIFECYCLE_PLAN_DRAFT4_20261115.md | 13,871 | 483A228C65400016964F43C4C52082E49CAF232C49B8AB8E8E6692DB6E21B385 |
| DOC-07 | features/FEAT-063-system-architecture-rearchitecture/plan/FR_C08_PARENT_TEACHER_CANCEL_PURGE_IMPLEMENTATION_ALLOWLIST_DRAFT4_20261115.md | 65,130 | F4C76422DDE39A2B34A5364BC6F7F77B3A960331F4DBA00939082FBE54E3512A |
| DOC-08 | features/FEAT-063-system-architecture-rearchitecture/evidence/FR_C08_DRAFT4_INDEPENDENT_COLD_REVIEW_20261115.md | 3,084 | 9C6A39CD071DA247C3B7F484C7536ED84BDF33CEA2D3BAE3BDCFF0C56F23118F |
| DOC-09 | features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md | 410,676 | C6A506404AF68A6180E150B83DE120113CE5EA54FCD7DEDFF9EAB01E4D375088 |
| DOC-10 | features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S2_IMPLEMENTATION_REPORT_20261114.md | 25,879 | F49D1FDB2B3C26387FFABC51C316F226C5D1FC5FC12B4856B0A6172A81941F55 |
| CODE-01 | backend/src/sketch2life/interfaces/http/routers/parent_story_runs.py | 14,626 | A2BA4553785BE7367A7F105708CE1A7F618DFE4A3538D85F00DDD9AE938467DD |
| CODE-02 | backend/src/sketch2life/contracts/schemas/parent_story_runs.py | 7,889 | 1214B0777688CB76043F6D519BF208871F4B1CAEC96E890C64292A89AE950749 |
| CODE-03 | backend/src/sketch2life/application/services/parent_story_runs.py | 7,630 | FED7AC29F02C34F19F093AF471017447F5E5FA3453D399E2A155067609958B14 |
| CODE-04 | backend/src/sketch2life/infrastructure/persistence/parent_story_repository.py | 69,489 | 237398C01E11BECFD89CE095C217035680D01E2EFFCF95CDD61C7438DEC5DA8C |
| CODE-05 | backend/src/sketch2life/interfaces/http/routers/be1_records.py | 16,381 | 05A9EB9A1C1E732EB3801213798A3DEE74B96E52517545513B42886DA392D9CF |
| CODE-06 | backend/src/sketch2life/interfaces/http/routers/be1_runtime.py | 1,014 | 89C54AC8EDB63FD2DC9A92910BE817645D9429B8A54E0485F86A826BA6A863A7 |
| CODE-07 | backend/src/sketch2life/interfaces/http/router_composition.py | 3,743 | 2CC4EA02A69E115C684B4383A1CA9BB63A4AAAB4B0E6C848852968C5E9599463 |
| CODE-08 | backend/src/sketch2life/interfaces/http/app.py | 74,637 | E7AE7BEA097929B83950B585A3ED9DEB682A4FF2A0D5E0CBE7ED36A1C1FCC031 |
| CODE-09 | backend/src/sketch2life/infrastructure/persistence/be1_models.py | 28,152 | 515208EC993E2F7B37CB4CB273469D342329801FE1DDA029736934BA91048666 |
| CODE-10 | backend/src/sketch2life/infrastructure/persistence/be1_parent_role_adapter.py | 1,507 | 1B83B95341D7AD98360CC98AF640CFAF5750A21FCE4CE971F0EE2D1DF66795E1 |
| CODE-11 | backend/src/sketch2life/application/ports/core_foundation.py | 5,512 | 2F6F55A0C576AF78DCB24219254DE6DE3C9063C4A868D0B27F2D91356268FB13 |
| CODE-12 | backend/src/sketch2life/infrastructure/persistence/core_models.py | 11,578 | 47D60EEECEF12F583B927BAB7FE3B74B9F19F15231E84E4039187376A502473A |
| CODE-13 | backend/src/sketch2life/infrastructure/persistence/core_store.py | 24,471 | AB2E86FD002E51A4FDB377644EE376E30AF6E6D888B270C4C1B3646BCB201F94 |
| CODE-14 | backend/src/sketch2life/application/ports/object_storage.py | 1,060 | CEC4214DDF3488D2C996368813B2B74D24C525ED86371E70D89F8AA9FA6EC9A4 |
| CODE-15 | backend/src/sketch2life/application/ports/ai_jobs.py | 19,923 | ACC3E27EA6B3A70E3DE267E4BD892D97FACF02D2B9F994817771BED3F584B3E3 |
| CODE-16 | backend/src/sketch2life/application/services/ai_jobs.py | 72,962 | 15DCD532D56EFF811A7DE937938E8D5F942AC7B29CDE26043A3B572DB02E08AE |
| CODE-17 | backend/src/sketch2life/domain/ai_jobs/model.py | 17,113 | 512B604636C1A22E231AC3276D3E537AE0DEAE4D9BB6652CCB064FAB7314DB99 |
| CODE-18 | backend/src/sketch2life/application/video_playback.py | 6,188 | EEB251839FAA384E68824A4DD79EF55CE5FD553F5ED8FFA72B308082E0CD57A2 |
| CODE-19 | backend/src/sketch2life/application/ports/video_playback.py | 3,436 | 7621F128D136853F3C9E815A6A70BE250D8D222865861F1F94E03F79023ABE79 |
| CODE-20 | backend/src/sketch2life/interfaces/http/routers/story_video.py | 4,576 | C7FEFFEAD0393444BC9CB8A518E471C0D6F64F3D33D3B540002CA1DC51F48F31 |
| CODE-21 | backend/src/sketch2life/domain/story_run_lite.py | 5,617 | B5F3EE06A08074D2CF9FD19E74AD9AF316447523E9C3C39B5FBC95DE697A31D9 |
| CODE-22 | backend/src/sketch2life/infrastructure/story_run_lite/repository.py | 132,748 | 58952C2A210785DBC6459C6FAC6203C5F5460DFEDD7852CD1375E12821E709D5 |
| CODE-23 | backend/src/sketch2life/infrastructure/story_run_lite/tables.py | 26,995 | 703018AE4BF81D51C565EFC4626ED07C973823E5FB582EF69DA7BB490923F034 |
| CODE-24 | backend/src/sketch2life/infrastructure/lesson_library/tables.py | 16,009 | FE43AD061B69D4D1B8191AB52705A72C59BAA42605AB9167F4AADF3EF74EFDAF |
| TEST-01 | backend/tests/contract/test_parent_story_run_cancel_route.py | 3,601 | 98B4522D441F223F4BC6A17256982B4E3E9484D7EE1692A753162DDBF17CBBDE |
| TEST-02 | backend/tests/unit/test_parent_story_run_cancel_repository.py | 10,111 | A7CE542F352E9E51A0C5B32444240E6A84866C7452293BFBE15EB38E02689D9E |
| TEST-03 | backend/tests/contract/test_parent_ai_late_result_guards.py | 3,467 | 7C9EF0E89B77E1566A33C386854174A56E9BABB88732A94BDB499898D42D2BEC |

## 10. Draft history and approval boundary

This is a new contract draft, not an edit to FR-C08 Spec Draft 4, Lifecycle Plan Draft 4, or Allowlist Draft 4. The prior review remains historical evidence about those frozen inputs. Draft 4 §5's open-issue table is the source for the ten-row gap assessment above. No existing approval ledger entry is extended by this document; M2 scope remains separate, and FR-C08 remains blocked pending its own reviewed contract, technical resolutions, later allowlist/approval, and launch authorization.
