# FEAT-063 FR-C-08 Parent/Teacher StoryRun Cancellation, Deletion and Purge — Implementation Specification Draft 4

Status: DRAFT / NOT APPROVED / NOT LAUNCHED
Document date: 2026-11-15

## 1. Purpose and boundary

This specification reconciles the FR-C-08 implementation plan to canonical working SRS Rev68 and owner decision D-208. It is a planning artifact only. It authorizes no implementation, route, schema or migration change, command, test run, allowlist, Task Approval, gate, provider call, deployment, or launch. OWNER_MODAL_CALL_APPROVED=NO.

Rev67 remains preserved as the prior unsigned SRS revision and D-203 provenance. Rev68 is the current unsigned working SRS after the D-208 documentation-only reconciliation. DTR remains the matching companion data-model source and was not changed. No runtime or database behavior is inferred from the SRS or DTR. D-208 records planning direction and is not implementation authorization.

## 2. Authority and trace

| Source | Planning use |
|---|---|
| Rev68 §§6.1.1, FR-C-08, BR-26/34/40, UC-07/11, §§9.8, 21.2, 21.4, 21.6, 22.3, 24.3, event catalog, NFR-34 and §31.10(17) | Product requirements and open technical boundaries. Rev68 remains unsigned. |
| D-208 | Controlling owner dispositions for this documentation reconciliation: cancel/delete eligibility; current authorization; immediate access fencing; owning-module purge; metadata-only audit; independent M2 gate. It directs no implementation or schema change. |
| D-199 through D-207 | Historical and M2-only scope/approval records. They remain in force in their own scope; none authorizes FR-C-08 implementation. |
| DATA_TABLE_REGISTER.md | Companion logical data-model source. It is not an alternate SRS, runtime proof, or permission to alter physical schema. |
| Spec Draft 2, Lifecycle Plan Draft 2 and Allowlist Draft 1 | Historical planning inputs. Draft 4 derives DELETE eligibility only from Rev68/D-208; Allowlist Draft 1 remains unapproved and does not define that eligibility. |

## 3. Evidence classification and baseline

- **Document/decision observed:** Rev68, D-208, DTR, Draft 2, Lifecycle Plan Draft 2, Allowlist Draft 1, M2 records and roadmap were read and pinned as listed in §12.
- **Recorded implementation evidence:** the pinned M2 implementation report says M2 S2 is PARTIAL / NOT COMPLETE and records incomplete/failing or unavailable evidence, including the OpenAPI tag mismatch, pytest temporary-path setup error, 335 mypy errors across 63 files, and 17 Ruff diagnostics. Those are report contents, not new results from this task.
- **Not runtime/database verified here:** current route behavior, all authorization adapters, existing token/cache/upload invalidation, lifecycle request persistence, worker/provider cancellation, object deletion, reference closure, backup expiry, effective permissions, and database contents. No runtime, test, database or migration command was run.
- **Separate coordination gate:** reconcile and pin the dirty/partial M2 baseline before any FR-C-08 implementation begins. Planning and review may proceed, but no implementation may rely on the unreconciled baseline. M2 approvals, allowlists, command ceilings and test authorization do not transfer to this task.

## 4. D-208 policy: operations and state inventory

Rev68 retains the existing 18 StoryRun states. This matrix does not add a public state or route.

| StoryRun state | Cancel unfinished run | Explicit DELETE request | Required disposition |
|---|---|---|---|
| DRAFT | Allowed | No | Cancel only while in this UC-11 eligible state. |
| INPUT_PROCESSING | Allowed | No | Cancel only while eligible; fence late processing output. |
| INPUT_REVIEW | Allowed | No | Cancel only while eligible. |
| SUBJECT_REVIEW | Allowed | No | Cancel only while eligible. |
| PREPARATION_REVIEW | Allowed | No | Cancel only while eligible. |
| STORY_GENERATING | Allowed | No | Cancel; fence late result. |
| SCRIPT_REVIEW | Allowed | No | Cancel only while eligible. |
| VIDEO_ADMISSION_PENDING | Allowed | No | Cancel; admission/dispatch must be fenced. |
| VIDEO_QUEUED | Allowed | No | Cancel; request best-effort job cancellation. |
| VIDEO_GENERATING | Allowed | No | Cancel; provider/job interruption is best-effort and output is fenced. |
| VIDEO_SAFETY_VALIDATING | Allowed | No | Cancel; output remains non-playable and is purged. |
| VIDEO_READY | Allowed | No | Cancel if it is still an unfinished run under UC-11. |
| SAFETY_BLOCKED | Allowed | No | Cancel only while eligible. |
| COMPLETED | No | Allowed, explicit user request | Never infer deletion from completion; process through lifecycle. |
| FAILED | No | Allowed, explicit user request | Content remains until an authorized user requests deletion; never auto-purge. |
| ABANDONED | No | Allowed, explicit user request | Content remains until an authorized user requests deletion; never auto-purge. |
| DELETE_PENDING | No | No | Keep public pending status until purge verification; reject new user delete/cancel command. |
| DELETED | No | No | Terminal only after required purge verification. |

The 13 cancel-eligible states are exactly DRAFT, INPUT_PROCESSING, INPUT_REVIEW, SUBJECT_REVIEW, PREPARATION_REVIEW, STORY_GENERATING, SCRIPT_REVIEW, VIDEO_ADMISSION_PENDING, VIDEO_QUEUED, VIDEO_GENERATING, VIDEO_SAFETY_VALIDATING, VIDEO_READY, and SAFETY_BLOCKED. UC-11 excludes COMPLETED, FAILED, ABANDONED, DELETE_PENDING and DELETED. SCRIPT_GENERATION_UNKNOWN is not one of Rev68’s 18 states and must not be added as a replacement state or silently treated as a valid state.

## 5. Authorization, requests and public read

### 5.1 Current authority

Every cancel or DELETE request must authorize the current Parent owner or the Teacher currently assigned to the class, rechecked against the current BE1 assignment/version. A former Teacher and creator provenance alone have no authority. Do not trust a caller-supplied organization identifier or assignment. D-208 requires named accountable module owners before launch; their absence alone does not block drafting, review, an allowlist proposal, or implementation approval. Unresolved technical ownership, interface, receipt, and schema contracts remain blockers for the affected implementation scope.

### 5.2 Cancel and explicit DELETE

- Cancel is available only in the 13 UC-11 states. On accepted cancel, Story changes the run to DELETE_PENDING and releases the active lock in its own transaction. The lifecycle request then coordinates work across the owning modules.
- DELETE uses the existing lifecycle path and is accepted only for a user-requested deletion of COMPLETED, FAILED or ABANDONED. It is not a new route. FAILED and ABANDONED are not scheduled or purged automatically.
- DELETE_PENDING remains the externally visible run lifecycle state until all required run-owned content is verified deleted. DELETED is not returned merely because a request was accepted, a lock was released, a job was cancelled, access was revoked, or a delete was attempted.
- Use the existing owner-scoped GET /v1/story-runs/{id} as the default lifecycle read. First verify that its approved response can carry the needed pending/deleted status and version. Add no route, public status, version field, percentage, or count by inference. If the existing read cannot meet Rev68, stop for a separate owner-reviewed contract decision.

### 5.3 Immediate access revocation and late results

Acceptance must immediately fence API reads/writes, downloads, playback-token issuance and use, stream/cache/proxy paths, active upload sessions and partial-upload parts, and job dispatch. The design must account for already-issued credentials and cached responses, not just new requests. The current BE1 assignment/version must be checked at protected Teacher boundaries. Job/provider cancellation is best-effort; it must not delay lock release. Every late or duplicate result must fail the run fence, remain non-playable, and enter the purge path. Exact fences and failure behavior remain technical work until evidenced for each owning path.

## 6. Ownership, purge and retained records

- **BE1:** coordinates the lifecycle request; no named person/module owner is established beyond the D-208 responsibility boundary.
- **Story:** owns the StoryRun transition, active-lock release, cancellation event and late-result fence.
- **Core Asset:** owns asset/reference resolution and deletion; do not bypass it with cross-module SQL.
- **AI Jobs:** receives best-effort cancellation requests. It does not own the Parent lifecycle request or StoryRun state by inference.
- **Parent scope:** requests use typed PARENT_ACCOUNT; never fabricate organization_id. Physical Parent-scope representation, the versioned cross-module contract, and durable receipt ownership/schema are OPEN-TECHNICAL blockers.
- Purge all required run-owned linked content, private derivatives and incomplete upload data through their owning modules. Retry idempotently and reconcile interrupted work. A shared asset may remain only after the run reference is removed and a valid independent reference is verified. If required run-owned content remains or its deletion cannot be verified, keep the lifecycle pending; do not emit DELETED.
- Preserve accepted quota usage and invoice/usage history. For a Teacher occurrence, remove the run/media pointer while retaining SAMPLE_USED and claim time; never reopen the slot. By default, only SRS-permitted audit, quota and successful Teacher sample-claim metadata may remain after purge.
- Do not claim provider-copy or backup deletion without evidence. If provider copies/backups or policy-retained run-owned content cannot be verified deleted, the lifecycle remains pending and the retention/real-data gate remains open.
- Audit is metadata-only: the D-208 logical categories are actor, action, resource type/ID, time, outcome and deletion receipt. Exclude child media/content, transcript, prompt and profile-support details. Audit-reader permissions, the exact physical field allowlist/mapping, and the mapping of Rev68’s 180/365-day targets to record types remain OPEN-TECHNICAL; do not infer them.

## 7. Acceptance criteria for a separately approved implementation

1. **Eligibility:** contract evidence covers exactly the 13 cancel states; explicit DELETE accepts only COMPLETED/FAILED/ABANDONED; FAILED/ABANDONED are never auto-purged; DELETE_PENDING/DELETED reject new cancel/delete commands.
2. **Authorization:** current Parent owner and currently assigned Teacher succeed only after current BE1 assignment/version checks; former Teacher and creator-only access fail closed.
3. **Atomic acceptance:** accepted cancel transitions to DELETE_PENDING and releases the active lock atomically. Idempotency, request/receipt ownership, revision and error details must come from an approved contract; no fields are invented here.
4. **Immediate revocation:** evidence covers newly requested and previously issued API/download/playback/token/cache/upload/partial-upload/job-dispatch access after acceptance.
5. **Best-effort cancellation and fencing:** queued/running job/provider cancellation is requested but does not hold the lock; late, duplicate and unknown results cannot become current or playable and are purged.
6. **Purge/retry:** owner modules delete all required run-owned content, private derivatives and incomplete upload data idempotently. Shared assets remain only after run-reference removal and independent-reference verification. Interrupted/partial work stays pending and reconciles safely.
7. **Terminal state:** an owner-scoped read reports DELETE_PENDING until all required deletion is verified and reports DELETED only afterward. No percentage/count or new public state is introduced without a separate contract decision.
8. **Accounting/sample:** accepted quota usage and invoice/usage history remain; Teacher occurrence pointer is cleared while SAMPLE_USED and claim time remain; no refund or slot reopening occurs.
9. **Audit/retention:** payloads contain only approved metadata categories and exclude child content; field-level authorization, physical mapping and record-type duration map are approved or remain explicit blockers.
10. **Evidence boundary:** tests and isolated integration evidence use synthetic data and a separately approved environment. No real child data or provider/Modal access is required or authorized by this specification.

## 8. Open decisions and technical questions carried from Draft 2 §9

D-208 resolves the policy direction in the earlier questions; the listed technical evidence, ownership and schema gates remain open. No question below authorizes a route, schema change or implementation.

| # | D-208 disposition | Remaining technical question / blocker |
|---|---|---|
| 1. Progress/read contract | Reuse owner-scoped GET /v1/story-runs/{id} by default; no new route unless insufficient. | Which existing response fields/version let a client distinguish DELETE_PENDING from verified DELETED, and what evidence proves the read is owner-scoped? If insufficient, what separate contract decision is needed? |
| 2. Lifecycle status model | Public run remains DELETE_PENDING until verified purge, then DELETED; no percentages/new StoryRun states. Internal BE1 lifecycle-request, AiJob and purge states remain separate. | Which already-defined internal values and reconciliation evidence represent queued, running, retry, unresolved external deletion and completion? If no current mapping exists, keep the public state pending and ask the owner before adding a contract value. |
| 3. Request owner and Parent scope | Responsibility boundary is BE1 coordinator, Story transition/event, Core Asset purge, AI Jobs best-effort cancellation; use typed PARENT_ACCOUNT. | Which existing versioned cross-module contract and durable receipt owner apply? How is Parent scope represented without organization_id; does it require DTR/schema work? These gaps block approval/implementation of the dependent request/receipt paths. A candidate allowlist may record them as blockers, but must not authorize those paths before the contracts are resolved. |
| 4. Teacher authorization | Current assigned Teacher validated against current BE1 assignment/version; former Teacher and creator provenance have no authority. | Which exact BE1 assignment/version source and route/application adapter will enforce this, and who owns that adapter? Prove revocation after reassignment. |
| 5. Immediate revocation | Immediate fence is required for API, download, playback/token, cache, upload and job dispatch. | For every previously issued token/grant, cache/stream, active upload and partial part, what exact fence invalidates it and what fail-closed behavior applies if revocation is delayed? |
| 6. State/action compatibility | Cancel exactly the 13 UC-11 states; explicit user DELETE for COMPLETED/FAILED/ABANDONED; no auto-purge; neither for DELETE_PENDING/DELETED. | How do current adapters map to all 18 Rev68 states without inventing storage states? SCRIPT_GENERATION_UNKNOWN is outside Rev68; identify existing compatibility handling or stop for a separate owner decision if mapping needs a new public/domain state. |
| 7. Storage, sharing and retention | Purge required run-owned content/private derivatives/incomplete uploads; shared asset only after independent-reference verification; no unsupported provider/backup deletion claim. | Which owning-module references/objects and idempotent delete/reconcile contracts prove closure? What separate retention evidence is required before production/real data? |
| 8. M2 evidence | M2 remains a separate PARTIAL / NOT COMPLETE coordination gate. | D-208 requires reconciliation and pinning of the current dirty M2 baseline and disposition of its failed/unavailable evidence before any FR-C-08 implementation begins. No M2 approval, allowlist, command ceiling or run authorization transfers. |
| 9. Audit/retention | Metadata-only categories and exclusions are set; 180/365-day targets remain in Rev68. | What exact field allowlist, audit-reader permissions, physical mapping and record-type-to-duration assignment are approved? Keep this gate open until sourced. |

## 9. Conflict and approval gates

Allowlist Draft 1 remains PROPOSED / NOT APPROVED / NOT LAUNCHED and is not usable as authorization. Its section 3 Parent-router E-path row records that no completed-delete route was selected; it does not define DELETE eligibility. Rev68 and D-208 are the sources for explicit user-requested DELETE of COMPLETED, FAILED and ABANDONED. This specification does not edit or approve the historical allowlist.

Before any separate implementation approval: complete an independent review of the current specification, lifecycle plan, and allowlist; resolve the OPEN-TECHNICAL blockers that affect the proposed implementation scope without inferring an SRS exception; update the corresponding versioned implementation contract to the SRS wording and independently review that updated contract, as D-208 requires; reconcile and pin the M2 baseline before any implementation begins; reconcile DTR/physical schema only through its own approved process if needed; prepare a fresh exact-path allowlist with its own command ceilings; and obtain explicit Task Approval. Rev68 records the SRS wording reconciliation; this package does not claim the separate implementation-contract review gate is closed. Named accountable people must be recorded before launch under D-208, not before proposing/reviewing an allowlist or granting a bounded implementation approval. That timing does not waive technical ownership or contract blockers. A separate pinned launch prompt is still required. None of these gates is satisfied or authorized by this document.

## 10. Changes from Spec Draft 3

- Corrects named-owner timing to match D-208: accountable people are required before launch, not before proposing/reviewing an allowlist or approving bounded implementation; technical contracts remain blockers.
- Makes the M2 coordination prerequisite unconditional before any FR-C-08 implementation, while allowing planning/review beforehand.
- Clarifies that unresolved audit fields, readers, physical scope, and retention mapping block dependent audit implementation and full lifecycle acceptance.
- Makes D-208's requirement to update and independently review the corresponding SRS-aligned implementation contract an explicit pre-implementation gate.
- Corrects the historical Allowlist Draft 1 description; its section 3 route-selection row did not define DELETE eligibility.
- Keeps all Rev68/D-208 lifecycle policy, unresolved technical blockers, and the DRAFT / NOT APPROVED / NOT LAUNCHED boundary unchanged.

## 11. Status

DRAFT / NOT APPROVED / NOT LAUNCHED. Planning only. No implementation, source change, test, validator, migration, database access, approval, allowlist, command ceiling, gate, provider action, or launch is authorized. OWNER_MODAL_CALL_APPROVED=NO.

## 12. Pinned planning inputs observed 2026-11-15

| Input | Bytes | SHA-256 |
|---|---:|---|
| Canonical FEAT-063 SRS Rev68 | 639948 | 69C83FE49CD4689D5D2540656D3319721838CF7343BAD00E24CDE558B8F5E944 |
| Historical Rev67 source at D-203 | 634291 | B704163C9AAF7BB198D8578699F75DB8766C2226A52CD48B0ED1314AF5E21996 |
| SRS authority pointer | 4313 | D6153D38000C95E43A4091C5DF2E856FAD872A33177E3A8542E30EF2BEDCAB60 |
| Project Context | 83919 | B53D00641590E5B0DB7D6D19603AB796F19658F9F3F6AD8BC31076FDF51D631D |
| Source Register | 116802 | AA85FBB167AB065322258C5C90F05AF40B331BA30F9009020E40147B9DEACC6B |
| Data Table Register, unchanged companion | 171609 | 7CDFDBECDC24E28BB08E62C98A33B338165350204447EBC59B86F5BE69899BC2 |
| DECISIONS.md through D-208 | 216212 | 52F2E141244829281FF762BA100D1A991D5CADFF042A237C8C125F324300725F |
| FEAT-063 TASK_APPROVAL.md including D-207 | 410676 | C6A506404AF68A6180E150B83DE120113CE5EA54FCD7DEDFF9EAB01E4D375088 |
| M2 S2 implementation report | 25879 | F49D1FDB2B3C26387FFABC51C316F226C5D1FC5FC12B4856B0A6172A81941F55 |
| FR-C-08 Spec Draft 2 | 44378 | 4C4C905B19883C94C8E60109E9731B9289B5F4C31A780020DAD9420211EB7318 |
| FR-C-08 Lifecycle Plan Draft 2 | 24996 | 300BEC5A0716B8CFC09896E52B9752F5D6EBF499C4BB86822A71AF9D29A41310 |
| FR-C-08 Allowlist Draft 1 | 44643 | 82978E82A2A07A94007E7574BC43FA45663CA3B03D72FAEFDD24C15964D01800 |
| M2 S2 Draft 18 | 101153 | 5CA09CC6F9D936C1BA74772251F4D3A9C0480F3E6F82818FE11114205FD3E331 |
| M2 Draft 18 independent review | 5169 | 4CE583BA092D140C62E7F1600E4B58778569885D7F7E3B62FB812839DD09835B |
| M2 implementation allowlist Draft 1 | 14768 | 7DCEEB785C2121D250B7C016EDC2030E2CD7912F87BE537F07CC8B359A2A0CE8 |
| M2 allowlist independent review R2 | 2715 | 6872DA02B2CD88644AED71BA039D9ABBD38F243639DD44EDCCBAF2000C57645D |
| M5/M6 roadmap | 20115 | A0A485EE421FBB1DA9DEC99DD8EC08279D14EAF27EC548AD6A0A4CE8F234F8FA |
