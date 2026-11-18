# FR-C-08 implementation readiness and gate order — Addendum Draft 1

Status: DRAFT / NOT INDEPENDENTLY REVIEWED / NOT APPROVED / NOT LAUNCHED  
Observed: 2026-11-15 22:52 Asia/Saigon (2026-11-15 15:52 UTC)

## 1. Purpose and authority

This addendum records the current source-level blockers and the order in which FR-C-08 can proceed. It accompanies, but does not replace, the clean-reviewed `FR_C08_PARENT_TEACHER_CANCEL_PURGE_IMPLEMENTATION_SPEC_DRAFT4_20261115.md`, `FR_C08_PARENT_TEACHER_CANCEL_PURGE_LIFECYCLE_PLAN_DRAFT4_20261115.md`, and `FR_C08_PARENT_TEACHER_CANCEL_PURGE_IMPLEMENTATION_ALLOWLIST_DRAFT4_20261115.md`. It does not authorize implementation, schema/DDL, migrations, tests, validators, runtime, provider/Modal use, approval, or launch. `OWNER_MODAL_CALL_APPROVED=NO`.

The owner-supplied file `D:\Downloads\SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` is exactly Rev67, 634,291 bytes, SHA-256 `B704163C9AAF7BB198D8578699F75DB8766C2226A52CD48B0ED1314AF5E21996`. It is the Rev67 selected by D-203, so it is the correct historical owner-supplied source. It is not the latest authority in this BE worktree: worktree `docs/context/SRS_AUTHORITY.md` and D-208 identify unsigned Rev68, 639,948 bytes, SHA-256 `69C83FE49CD4689D5D2540656D3319721838CF7343BAD00E24CDE558B8F5E944`, as the canonical working SRS after the documentation-only reconciliation. Use Rev68 for current FR-C-08 requirements in this worktree; retain Rev67 as provenance. The root checkout still points to Rev60, so do not copy this worktree plan into the root checkout without reconciling that authority pointer.

Rev68 and D-208 settle the product policy: the 18-state inventory; cancel for the 13 UC-11 unfinished states; explicit user-requested DELETE for `COMPLETED`, `FAILED`, and `ABANDONED`; no automatic purge for `FAILED` or `ABANDONED`; current Parent owner/current Teacher assignment authorization; immediate revocation; best-effort job/provider cancellation; late-result fencing; owner-module purge and shared-reference verification; `DELETE_PENDING` until verified purge then `DELETED`; quota/sample-claim preservation; and metadata-only audit. These decisions do not supply the missing physical contracts or approve implementation.

## 2. Live preflight and evidence boundary

- Worktree: `.worktrees/m2-s2`; branch `feature/feat063-m2-s2`; HEAD `5de30674bc826591ad4b3cc00fca53c7597ead51`.
- At pre-edit observation, `git status --short` had 58 entries and the staged-path count was 0. The worktree was already dirty; those changes were preserved.
- M2 S2 implementation report: 25,879 bytes, SHA-256 `F49D1FDB2B3C26387FFABC51C316F226C5D1FC5FC12B4856B0A6172A81941F55`. It says S2 is `PARTIAL / NOT COMPLETE`; the recorded combined targeted test exited 1 with an OpenAPI catalog tag assertion failure and an app-composition `tmp_path` permission error, mypy reported 335 errors in 63 files, and Ruff reported 17 diagnostics. These are recorded M2 outcomes, not new test results and not FR-C-08 evidence. M2 command ceilings and approvals do not transfer.
- FR-C-08 Draft 4 allowlist remains `PROPOSED / BLOCKED FOR IMPLEMENTATION / NOT APPROVED / NOT LAUNCHED`. There is no separate FR-C-08 Task Approval or pinned launch instruction in this package.
- All source findings below are static observations from the M2 working tree at the timestamp above. They do not prove a mounted runtime route, database state, token/cache behavior, object deletion, worker behavior, or passing tests.

## 3. Current source gaps relevant to the blockers

| Area | Current static observation | Why it blocks FR-C-08 |
|---|---|---|
| Route and mount | `backend/src/sketch2life/interfaces/http/routers/parent_story_runs.py:232-250,253-294` declares the Parent GET-by-ID and POST cancel. `router_composition.py:61-76` includes the router only when `include_parent_story_runs` is true; `app.py:1029` supplies `not story_demo_enabled`. | Source declaration is conditional composition, not proof the endpoint is mounted in a particular runtime. No runtime check was performed. |
| Explicit DELETE operation | Rev68 §21.2, line 1674, specifies `DELETE /v1/story-runs/{id}` for an explicit request on `COMPLETED`, `FAILED`, or `ABANDONED`, returning 202 with `DELETE_PENDING` until verified purge then `DELETED`. A read-only search of the current HTTP routers found no `DELETE /v1/story-runs/{id}` decorator; `parent_story_runs.py` currently declares GET and POST operations only. | The URL/method are already specified by the SRS, so this is not a request to invent a new product route. The endpoint is absent from current source. Spec Draft 4 §5.2's “not a new route” wording and Allowlist Draft 4 §4.2's “No new route ... is proposed” wording must be clarified: the implementation must add the SRS-defined DELETE operation to the approved route/schema path set. Exact request/replay/error details still require a reviewed contract. |
| Public GET state | `contracts/schemas/parent_story_runs.py:110-141` omits `DELETED`, `ABANDONED`, and several Rev68 states from `ParentStoryRunResponseV1`; it includes `SCRIPT_GENERATING` and `SCRIPT_GENERATION_UNKNOWN`, which are not Rev68 StoryRun states. | The existing GET cannot currently express the full SRS lifecycle vocabulary or verified terminal `DELETED`. Reconcile the existing response/state mapping first; do not add a route or state by inference. |
| Cancel eligibility and transaction | `parent_story_repository.py:326-427` accepts seven values: `INPUT_PROCESSING`, `SUBJECT_REVIEW`, `PREPARATION_REVIEW`, `SCRIPT_GENERATING`, `SCRIPT_GENERATION_UNKNOWN`, `SCRIPT_REVIEW`, and `VIDEO_ADMISSION_PENDING`. The two script values are outside Rev68's StoryRun state inventory. It changes the run to `DELETE_PENDING`, clears the active Parent lock, increments revision/version, and stores a `CANCEL_RUN` response receipt with `purge_state=PENDING`. | This is a bounded M2 cancel path, not the Rev68 13-state policy. It also accepts out-of-inventory values. Map current source to the SRS before reusing or expanding it. |
| Actor authorization | `parent_story_runs.py:243-244,273` calls `_require_parent`; the inspected route is Parent-only. | D-208 also requires the currently assigned Teacher to be authorized against the current BE1 assignment/version. That adapter and reassignment behavior are not established by this route. |
| Parent request and job-cancel scope | `be1_models.py:555-578` models `be1_data_lifecycle_requests` with non-null `organization_id`; `ai_jobs/sql/tables.py:229-244` similarly requires `organization_id` on `cancellation_notice`. The inspected cancel repository path writes its Story command receipt but does not create either cross-module request/notice. | Existing models do not demonstrate typed `PARENT_ACCOUNT` scope or a durable cross-module request/receipt contract. Do not synthesize an organization ID. A DTR/schema decision may be required. |
| Core Asset and storage | `application/ports/core_foundation.py:181-184` exposes metadata save/read in the inspected port. A low-level `delete_asset` exists in `story_run_lite/quarantine.py:140-145`, but this does not itself enumerate valid references, remove run lineage, prove shared-reference closure, or provide a run-lifecycle completion receipt. | Storage deletion alone cannot satisfy the owner-module purge and positive shared-reference verification required by D-208. The owning-module contract and evidence remain open. |
| Revocation, late results, retry and purge | The inspected cancel repository path performs the state/lock/receipt transaction. No lifecycle coordinator, purge worker, or access-fence call is made by that function. Separate API/download/playback/cache/upload/job-dispatch fences, late-result handling, purge retries and completion proof remain unverified. | The system must revoke access immediately, keep `DELETE_PENDING` through partial/unknown deletion, and expose `DELETED` only after owner-module evidence. This is not implemented by the observed state transition alone. |
| Audit and retention | D-208/Rev68 give metadata categories and 180/365-day targets, but leave reader permissions, exact physical fields/scope and record-type duration mapping open. | Do not implement or claim audit completion by guessing. These decisions block dependent audit writes/reads and full lifecycle acceptance. |

## 4. Gate status and ordered next work

| Order | Gate | Current status | Required closure before proceeding |
|---:|---|---|---|
| 0 | Freeze/reconcile M2 baseline | **BLOCKED — mandatory before any FR-C-08 implementation.** | Reconcile and pin the dirty M2 tree; disposition the failed/unavailable test, typecheck and lint evidence; state exactly which code/evidence may be reused. This does not by itself claim S2 complete. |
| 1 | Versioned lifecycle contract and typed request/receipt | **BLOCKED.** | Define BE1 coordination, Story transition/event/lock, Core Asset ownership, AI Jobs best-effort cancellation, typed `PARENT_ACCOUNT`, durable receipt owner/replay boundary, and any DTR/schema consequence. No fabricated `organization_id`; migration work requires its own approved plan. |
| 2 | Existing read and state/action contract | **BLOCKED.** | Reconcile the existing owner-scoped GET with the 18 SRS states and verified `DELETE_PENDING`/`DELETED` predicate. The first candidate is to correct the existing response contract to use SRS states; add no read route, public state, percentage, or count unless an independently reviewed contract proves it is necessary and the owner approves it. Add the explicit DELETE operation already specified by Rev68 §21.2 to the approved route/schema scope; do not describe its SRS-defined path as an invented route. Reconcile the current seven-value cancel set, including two out-of-inventory script values, to exactly the 13-state rule. |
| 3 | Current authorization and immediate revocation | **BLOCKED.** | Specify and inventory current Parent ownership and Teacher assignment/version checks, then define fail-closed fences for API, download, playback token, stream/cache, upload/partial upload and job dispatch, including already-issued credentials and reassignment. |
| 4 | Owner-module cancellation, purge and reconciliation | **BLOCKED.** | Define AI Jobs best-effort cancellation and Story late-result fencing; define Core Asset reference enumeration/removal, incomplete-upload cleanup, shared-reference proof, idempotent retries, restart/reconciliation and evidence required before `DELETED`. No cross-module SQL assumption. |
| 5 | Audit field and retention contract | **BLOCKED for audit behavior and full acceptance.** | Obtain an approved field allowlist, reader permission, Parent physical mapping and record-type mapping to 180 or 365 days. Keep dependent audit code out of scope until resolved. |
| 6 | Contract review, allowlist, task approval and launch | **NOT READY.** | Update the corresponding versioned implementation contract to Rev68 and independently review it; then revise the exact-path allowlist against the frozen baseline, independently review it, obtain separate owner Task Approval and a pinned launch instruction. No M2 approval, allowlist, ceiling or test run transfers. |
| 7 | Named accountable people | **OPEN — launch gate only.** | D-208 requires named accountable module owners before launch. Names are not a prerequisite to this planning addendum, contract drafting/review, or by themselves to bounded implementation approval. Technical module boundaries/contracts remain blockers. |
| 8 | Real-data/production use | **GATED.** | Synthetic-only evidence until all Rev68 §29.2 and D-208 gates are separately met and the owner grants the required authorization. No provider/Modal use is approved here. |

The first immediate blocker is Gate 0 for any code implementation. Even after it is closed, Gates 1–6 are not currently closed, and no implementation approval or launch instruction exists. Planning and contract work may continue now. Gate 0 is specifically a baseline freeze/disposition requirement; it must not be misreported as proof that every M2 feature is complete. For M3 acceptance, the broader M2 exit and separately approved S3 remainder remain dependencies in the roadmap.

## 5. Clarification to Lifecycle Plan Draft 4

D-208 makes named accountable people a **before-launch** requirement. Any reading of Lifecycle Plan Draft 4 §4 C3 or §6 item 3 as requiring named individuals before technical planning or implementation approval is not adopted by this addendum. Keep the D-208 module responsibility boundaries as technical design inputs; record the names separately as a launch gate. This clarification does not reduce the technical requirements for Parent scope, receipts, current Teacher authorization, revocation, purge, audit or retention.

## 6. Completion boundary

This addendum fixes the gate ordering and source-status record only. It does not close the technical blockers, authorize implementation, approve Allowlist Draft 4, or declare FR-C-08 started. The next useful work is a reviewed versioned cross-module contract and M2 baseline reconciliation; separate owner decisions may be needed where the SRS/D-208 leaves physical schema, audit authorization/retention, or contract choices open. Named accountable people must also be recorded before launch. No tests, typecheck, Ruff, validators, runtime, database, migration, Docker, network, provider or Modal command was run for this addendum.

## 7. Observed pins

| Input | Bytes | SHA-256 |
|---|---:|---|
| Owner-supplied SRS Rev67 (`D:\Downloads\SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`) | 634291 | B704163C9AAF7BB198D8578699F75DB8766C2226A52CD48B0ED1314AF5E21996 |
| Worktree SRS authority | 4313 | D6153D38000C95E43A4091C5DF2E856FAD872A33177E3A8542E30EF2BEDCAB60 |
| Worktree canonical SRS Rev68 | 639948 | 69C83FE49CD4689D5D2540656D3319721838CF7343BAD00E24CDE558B8F5E944 |
| DECISIONS.md through D-208 | 216212 | 52F2E141244829281FF762BA100D1A991D5CADFF042A237C8C125F324300725F |
| M2 S2 implementation report | 25879 | F49D1FDB2B3C26387FFABC51C316F226C5D1FC5FC12B4856B0A6172A81941F55 |
| Spec Draft 4 | 20897 | BC268E2354AED6FDC142CCD58BFDF89BACF6585F15B7ED75C8AE7C4C41ED9B70 |
| Lifecycle Plan Draft 4 | 13871 | 483A228C65400016964F43C4C52082E49CAF232C49B8AB8E8E6692DB6E21B385 |
| Allowlist Draft 4 | 65130 | F4C76422DDE39A2B34A5364BC6F7F77B3A960331F4DBA00939082FBE54E3512A |
| Draft 4 independent review | 3084 | 9C6A39CD071DA247C3B7F484C7536ED84BDF33CEA2D3BAE3BDCFF0C56F23118F |
| Data Table Register companion | 171609 | 7CDFDBECDC24E28BB08E62C98A33B338165350204447EBC59B86F5BE69899BC2 |
| HTTP app composition (last observed) | 74637 | E7AE7BEA097929B83950B585A3ED9DEB682A4FF2A0D5E0CBE7ED36A1C1FCC031 |
| HTTP router composition (last observed) | 3743 | 2CC4EA02A69E115C684B4383A1CA9BB63A4AAAB4B0E6C848852968C5E9599463 |
| Parent StoryRun router (last observed) | 14626 | A2BA4553785BE7367A7F105708CE1A7F618DFE4A3538D85F00DDD9AE938467DD |
| Parent StoryRun schema (last observed) | 7889 | 1214B0777688CB76043F6D519BF208871F4B1CAEC96E890C64292A89AE950749 |
| Parent StoryRun repository (last observed) | 69489 | 237398C01E11BECFD89CE095C217035680D01E2EFFCF95CDD61C7438DEC5DA8C |
| BE1 persistence models (last observed) | 28152 | 515208EC993E2F7B37CB4CB273469D342329801FE1DDA029736934BA91048666 |
| AI Jobs SQL tables (last observed) | 12426 | 12F6CE1EDAB047EFDD81D495B44DF08DC6F990692860621F37FC73778006F888 |
| Core foundation port (last observed) | 5512 | 2F6F55A0C576AF78DCB24219254DE6DE3C9063C4A868D0B27F2D91356268FB13 |
| Core persistence store (last observed) | 24471 | AB2E86FD002E51A4FDB377644EE376E30AF6E6D888B270C4C1B3646BCB201F94 |
| StoryRun Lite quarantine storage (last observed) | 7375 | B39B459F5ABA072EDB164D25D4986261EF14D04F13C13108F04BCA5EF3F86EA1 |
