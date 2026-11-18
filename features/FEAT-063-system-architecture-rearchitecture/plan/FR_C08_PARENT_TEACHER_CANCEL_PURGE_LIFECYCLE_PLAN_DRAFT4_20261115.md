# FEAT-063 FR-C-08 Parent/Teacher StoryRun Cancellation, Deletion and Purge — Lifecycle Plan Draft 4

Status: DRAFT / NOT APPROVED / NOT LAUNCHED
Document date: 2026-11-15

## 1. Purpose and outcome

Plan the separate work needed to satisfy FR-C-08 under canonical working SRS Rev68 and owner decision D-208. This plan covers explicit user deletion of COMPLETED, FAILED and ABANDONED runs; cancellation of only the 13 UC-11 unfinished states; immediate access revocation; best-effort job/provider cancellation; late-result fencing; and verified purge through owning modules.

This is planning only. It does not approve implementation, DTR/DDL, a route, an allowlist, command ceiling, Task Approval, a test run, a gate, provider use or launch. OWNER_MODAL_CALL_APPROVED=NO.

## 2. Authority and baseline

Rev68 is the unsigned canonical working SRS under D-203/D-208. Rev67 and its D-203 pin remain historical provenance. The unchanged DATA_TABLE_REGISTER.md is a companion data-model source, not runtime evidence or an alternate SRS. The M2 report is a pinned PARTIAL / NOT COMPLETE record; the M2 tree was dirty at planning preflight and must be reconciled as a separate coordination gate. M2 approvals, allowlists, and command ceilings do not transfer.

The recorded M2 report includes failed/unavailable evidence, including an OpenAPI tag mismatch, pytest temporary-path setup error, 335 mypy errors across 63 files and 17 Ruff diagnostics. This plan did not run or retry these checks. The report’s recorded evidence is not a passing FR-C-08 lifecycle test.

## 3. D-208 lifecycle contract

| Concern | Required planning outcome |
|---|---|
| Cancel | Only DRAFT, INPUT_PROCESSING, INPUT_REVIEW, SUBJECT_REVIEW, PREPARATION_REVIEW, STORY_GENERATING, SCRIPT_REVIEW, VIDEO_ADMISSION_PENDING, VIDEO_QUEUED, VIDEO_GENERATING, VIDEO_SAFETY_VALIDATING, VIDEO_READY, SAFETY_BLOCKED. COMPLETED, FAILED, ABANDONED, DELETE_PENDING and DELETED are excluded. |
| Explicit DELETE | Authorized user must explicitly request deletion for COMPLETED, FAILED or ABANDONED. FAILED and ABANDONED are never automatic purge candidates. |
| Authorization | Current Parent owner or currently assigned Teacher verified against current BE1 assignment/version. Former Teacher and creator provenance alone do not authorize. |
| Acceptance/revocation | Story records DELETE_PENDING and releases its active lock in its transaction. Immediately fence API, download, playback/token, cache, upload/partial parts and job dispatch. |
| Cancellation/fencing | Best-effort job/provider cancellation; late results fenced, non-playable and purged. Failure to interrupt a provider does not hold the lock. |
| Purge | Owning modules delete run-owned content, private derivatives and incomplete uploads. Shared asset can remain only after removing the run reference and verifying a valid independent reference. Retries are idempotent. |
| Completion/read | Existing owner-scoped GET /v1/story-runs/{id} is the default progress read. Public status remains DELETE_PENDING until all required run-owned deletion is verified; then DELETED. No new route, state, percentage or count by inference. |
| Retention | Preserve accepted quota/invoice usage and successful Teacher sample claim/time; clear Teacher run/media pointer without reopening slot. Only SRS-permitted audit, quota and sample-claim metadata may remain by default. No unsupported provider-copy or backup deletion claim. |
| Audit | Metadata-only. D-208 logical categories are actor, action, resource type/ID, time, outcome and deletion receipt; exact field allowlist, reader authorization, physical mapping and 180/365-day record mapping remain OPEN. |

## 4. Work packages and gates

| ID | Work package | Dependencies / blocker | Acceptance evidence required in a separately approved task |
|---|---|---|---|
| C0 | Reconcile and freeze the M2 baseline | Current M2 tree and evidence are dirty/partial. M2 pins/approvals/ceilings do not transfer. | Fresh pinned status and evidence disposition; identify what M2 code can be reused without claiming complete lifecycle coverage. Separate owner coordination gate. |
| C1 | Resolve Parent scope, receipt, and cross-module contracts | Parent typed scope, versioned cross-module contract and durable receipt ownership/schema are open. | Approve versioned contracts and demonstrate Parent scope as PARENT_ACCOUNT without fabricated organization_id. Any DTR/schema change follows its own review/approval path. Named accountable people are a separate D-208 launch gate; they do not block proposing/reviewing this plan or resolving the technical contracts. |
| C2 | Resolve public read and lifecycle request mapping | Existing owner-scoped GET is default; exact status/version sufficiency and internal state mapping unverified. | Contract review shows the GET can report DELETE_PENDING and verified DELETED. If not, stop for separate owner choice before adding a route/field/status. No percentages/counts. |
| C3 | Implement authorization and immediate access fencing | Current BE1 assignment/version source and all active token/cache/download/upload fences require inventory and named owners. | Synthetic contract evidence covers current Parent/Teacher, former Teacher denial, current-assignment recheck, old tokens/cache, downloads, streams, upload sessions/parts and dispatch. |
| C4 | Implement Story cancellation, deletion and late-result boundary | Story owns transition, lock and cancellation event; event/receipt details require approved contract. | Matrix tests cover exactly 13 cancel states and explicit DELETE only for COMPLETED/FAILED/ABANDONED; wrong-state behavior; atomic lock release; stale/duplicate/unknown outputs cannot become current/playable. FAILED/ABANDONED never auto-purge. |
| C5 | Implement owning-module job cancellation and purge | Core Asset reference/deletion contract, AI Jobs interface and BE1 lifecycle request/retry mapping remain open. | Best-effort cancellation; all required run-owned/private/incomplete-upload data is purged idempotently; shared reference closure verified; partial failure/restart remains pending; late output enters purge. No direct cross-module SQL. |
| C6 | Preserve quota, Teacher claim and audit invariants | Billing/Lesson ownership; exact audit fields, readers, physical mapping and retention mapping remain OPEN-TECHNICAL. | Quota usage and invoice history unchanged; Teacher SAMPLE_USED/claim time retained while pointer cleared. Do not implement audit persistence/read behavior until its required field, reader, physical-scope and retention decisions are approved. Full lifecycle acceptance remains blocked until required metadata-only audit evidence is approved and verified. |
| C7 | Independent verification and separate approval package | C1–C6 specifications and blockers resolved; this document alone does not authorize a command. | Update the corresponding versioned implementation contract to the SRS wording and obtain a separate independent review of that contract, as D-208 requires; then obtain independent review of the exact-path allowlist, owner Task Approval and a pinned launch instruction. No M2 ceiling or approval is reused. |

## 5. Purge completion and failure handling

The implementation must distinguish access revocation from deletion. Revocation is immediate at acceptance. A purge attempt, job-cancel receipt, cleared lock, inaccessible object, or lifecycle request creation is not proof that required content was deleted. Keep the public run state DELETE_PENDING while any required run-owned object, private derivative or incomplete upload remains or cannot be verified deleted. Emit/return DELETED only after owning-module evidence verifies all required deletion.

Remove a run’s reference before considering a shared asset for retention. Retain that asset only when a valid independent reference is positively verified; otherwise purge it through Core Asset. Retry idempotently after partial failure and reconcile after worker/process interruption. Preserve accepted quota use and successful Teacher sample claim. Do not claim provider copies or backups were deleted unless evidence specifically covers them. If retained content is required by an unresolved policy, keep deletion pending and block completion/real-data use rather than inventing an exception.

## 6. Open technical questions carried from Draft 2

D-208 resolves the owner policy for the nine Draft 2 questions. The technical portions remain gates:

1. **Read/progress:** confirm the current owner-scoped GET exposes sufficient status/version; otherwise seek a separate contract decision before any route/field.
2. **Lifecycle mapping:** identify already-defined internal lifecycle/AiJob/purge states and reconciliation evidence; do not add public state names or percentages.
3. **Ownership/scope/receipts:** assign named BE1, Story, Core Asset and AI Jobs owners; define typed Parent scope without organization_id and versioned contract/receipt ownership; assess whether a DTR/schema gate is required.
4. **Teacher authorization:** source and prove current BE1 assignment/version enforcement and revocation after reassignment.
5. **Immediate revocation:** inventory existing credentials, downloads, playback tokens, stream/cache paths, upload sessions/partial parts and job dispatch; prove each can be fenced on acceptance.
6. **State compatibility:** map existing code to all 18 Rev68 states; keep cancel 13-state and explicit DELETE 3-state policy; SCRIPT_GENERATION_UNKNOWN is outside the SRS inventory. If a new state is required, stop for owner direction.
7. **Storage/retention:** establish owning-module reference closure, idempotent delete/retry, shared-asset handling and required deletion evidence. Provider/backup and real-data gates stay open without evidence/policy.
8. **M2 baseline:** reconcile and pin the partial/dirty state and disposition failed/unavailable evidence before any FR-C-08 implementation; no test/run ceiling transfers. Planning and review may proceed before that gate, but implementation may not.
9. **Audit:** the field allowlist, reader permissions, physical Parent scope/mapping and type-to-180/365-day assignment are OPEN-TECHNICAL. They block implementation of dependent audit writes/reads and block full lifecycle acceptance; approve them before those behaviors are implemented or claimed complete.

## 7. Historical allowlist boundary and current proposal

Allowlist Draft 1 remains unapproved and unchanged. Its section 3 Parent-router E-path row records that no completed-delete route was selected; it does not define DELETE eligibility. Rev68/D-208 supply the explicit user-requested DELETE rule for COMPLETED, FAILED and ABANDONED. Lifecycle Plan Draft 3 repeated an unsupported completed-run-only attribution; this revision corrects that provenance. Allowlist Draft 4 is a separate proposal and remains unapproved pending its own independent review and owner approval.

## 8. Changes from Lifecycle Plan Draft 3

- Separates named-person accountability (required before launch) from unresolved technical contracts that block the affected implementation.
- Makes reconciliation and pinning of M2 mandatory before any FR-C-08 implementation; planning and review may proceed before that gate.
- Clarifies that unresolved audit mapping blocks dependent audit implementation and full lifecycle acceptance.
- Adds D-208's pre-implementation gate to update and independently review the corresponding SRS-aligned implementation contract.
- Corrects the Draft 1 history: its route-selection row did not define DELETE eligibility.
- Preserves Rev68/D-208 lifecycle policy and keeps this plan DRAFT / NOT APPROVED / NOT LAUNCHED; no implementation is authorized.

## 9. Status

DRAFT / NOT APPROVED / NOT LAUNCHED. No implementation, test, validator, migration, database access, allowlist, command ceiling, Task Approval, gate, provider action or launch is authorized. OWNER_MODAL_CALL_APPROVED=NO.

## 10. Pinned planning inputs observed 2026-11-15

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
