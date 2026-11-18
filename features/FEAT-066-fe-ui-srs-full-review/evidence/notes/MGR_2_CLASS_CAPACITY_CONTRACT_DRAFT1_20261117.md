# MGR-2 source evidence — class-capacity contract draft

**Date:** 2026-11-17  
**Status:** Planning evidence only; DRAFT / NOT APPROVED / NOT LAUNCHED  
**Baseline:** BE worktree D:\GitHub\Sketch2Life\.worktrees\manager-api, branch feature/feat066-manager-api-contracts, HEAD 1c9148e88600a101887e477541c4c4893ba1c7df; FE source inspected at its pinned baseline 297a28b1f406ab80e25d6e0aa5577e4b6f505ee2.

## Worktree state

- BE branch and HEAD matched the expected baseline. Before this draft, the manager worktree already had local changes in CONTEXT.md, DECISIONS.md, STATUS.md, the MGR-1 evidence note, and the MGR plan. Those changes were preserved. After adding this draft, status showed only those existing changes plus these two new MGR-2 documents.
- BE staged-file count was zero before and after this draft.
- FE branch was codex/fe-ui-web-remediation at HEAD 297a28b1f406ab80e25d6e0aa5577e4b6f505ee2 and its worktree status was clean. It was not modified.

## Pin and MGR-1 verification

The table below preserves input pins/results recorded during the original MGR-2 preflight; it is historical task evidence, not a fresh validation in this citation update. In particular, the owner-selected external SRS is retained only as task-input provenance and is not current product authority.

| Input | Expected bytes / SHA-256 | Result |
|---|---|---|
| features/FEAT-066-fe-ui-srs-full-review/DECISIONS.md | 35,781 / 731FB2BD5FAFF0A2F91D55EF2AF087F34C0C2735B743057CD6CA961407B363AF | MATCH |
| features/FEAT-066-fe-ui-srs-full-review/plan/PLAN_MANAGER_API_GAP_CLOSURE_DRAFT1_20261117.md | 18,974 / 5E7CDB0AF03A27FF0DABFE949E41F7230D1BE7453EF56274E8CED388F6F196ED | MATCH |
| features/FEAT-066-fe-ui-srs-full-review/evidence/notes/MGR_1_OWNER_DISPOSITION_20261117.md | 4,016 / B32D4CBC47811960A5DE2B2F1A3CAA9C84B64F8F9DC7F79CD0CD68F92F37883A | MATCH |
| Owner-selected unsigned external SRS recorded for this MGR-2 task, D:\Downloads\SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS (2).md | 701,157 / B9B1F42D0BB118C19C81607D3913B7E4F1D8B6F673F0C3FBB6402888FEB675F5 | Original task preflight recorded MATCH; NOT REVERIFIED in this citation update; provenance only |

The table above records file pins from the original MGR-2 preflight. Its `DECISIONS.md` file hash is not the Git blob at pinned HEAD and does not establish whether a decision was committed.

**D-066-62 provenance correction, verified 2026-11-17:** D-066-62 is absent from `DECISIONS.md` at pinned HEAD `1c9148e88600a101887e477541c4c4893ba1c7df`. The HEAD Git blob is `ca0143cfd432bb70bfdf79e988228ef2066d9b50` (34,226 bytes); a direct search of `git show HEAD:features/FEAT-066-fe-ui-srs-full-review/DECISIONS.md` returned no D-066-62 match. The current working-tree `DECISIONS.md` contains D-066-62 at lines 260–268 (38,951 bytes; SHA-256 `A99E5AC92E747E199E350F842C6E7444942FFDD1610205B3F07AB79F60E5F61C`). It is therefore an **owner decision recorded in the current working tree, not present at pinned HEAD**. The owner’s direct instruction is recorded at working-tree `DECISIONS.md` lines 262–268 and corroborated by `MGR_1_OWNER_DISPOSITION_20261117.md` lines 14–18 (4,016 bytes; SHA-256 `B32D4CBC47811960A5DE2B2F1A3CAA9C84B64F8F9DC7F79CD0CD68F92F37883A`); this is not a claim that D-066-62 was committed at the pinned baseline.

Separately, for class capacity, MGR-1 records Billing as effective-capacity owner, requires a transaction-time check and 201 or CLASS_CAPACITY_REACHED, prohibits class creation without verified effective capacity, and leaves the Billing-unavailable public result to MGR-2. D-066-62's verified same-organization Teacher rule is specific to assignment candidates; this MGR-2 review does not broaden it into a class-create permission decision. MGR-1 keeps Manager profile creation outside scope and Q193 OPEN; this MGR-2 slice does not reopen either item.

The original MGR-2 task record states that the owner selected D:\Downloads\SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS (2).md, §§1–31, as a task-specific input. That record reports a Rev69 header and revision history ending at Rev68; preserve the discrepancy as OPEN / NOT VERIFIED. The external file, its hash, and the discrepancy were not opened or independently verified during this citation update. Repository AGENTS.md and docs/context/SRS_AUTHORITY.md identify the in-repository FEAT-063 v2.7-draft Rev60 as the sole current product SRS; the historical task selection does not change that authority.

## SRS evidence

| Owner-selected external locator (original task record only; not reverified) | Canonical repository SRS locator (Rev60, directly checked) | Current requirement / traceability result |
|---|---|---|
| §7, FR-T-03 (:542) | §7.3 FR-T-03 line 522; UC-06 lines 1426–1436; §21.2 line 1622 | 10 paid base slots plus purchased slots; transaction-time admission must prevent concurrent creation beyond effective capacity. |
| §9.7 (:842) | §9.7 lines 793–818, especially 815; §23.1 lines 1832–1834; §23.4 lines 1867–1869 | Billing owns organization subscription/class capacity; BE1 class state is a projection and queries a versioned entitlement decision. Suspension uses Billing-selected classes and effective-time events/projection. |
| §9.6 (:816) | Rev60 §9.6 lines 766–775 lists proposed route groups; line 791 gives the general idempotency-key requirement. Detailed command scope/replay semantics are in §§21.1 line 1609 and 21.4 line 1670; mismatch response is §9.8 line 835. | State-changing commands require an idempotency key; same key/payload replays the result; a different payload returns HTTP 400 `INVALID_IDEMPOTENCY_KEY`. The old external §9.6 locator is historical only and is not an exact locator for Rev60's detailed semantics. |
| §9.8 (:849–866) | §9.8 lines 820–839 | Standard error envelope fields are lines 822–831; HTTP 400 `INVALID_IDEMPOTENCY_KEY` is line 835; 409 `CLASS_CAPACITY_REACHED` and `SUBSCRIPTION_RESTRICTED` are line 839. |
| §21.1 (:1636) | §21.1 lines 1605–1614 | Backend returns correlation IDs, clients send/retain idempotency keys for state-changing retries, and lists/versioned responses follow the common rules. `X-Request-ID` remains source correlation evidence, not SRS idempotency header spelling. |
| §21.2 (:1649) | §21.2 lines 1616–1625, especially class-create row 1622; proposed path group also appears at §9.6 line 774 | School Manager class creation checks effective capacity in a transaction and returns 201 class ref or `CLASS_CAPACITY_REACHED`. Public path mapping to current BE prefix remains OPEN. |
| §21.4 (:1697) | §21.4 lines 1668–1674, especially 1670; §9.8 line 835 | State-changing command idempotency is scoped by principal/operation/target; same key/payload replays; mismatched payload uses `INVALID_IDEMPOTENCY_KEY`. |
| §21, School Manager (:1709) | §21.5 line 1682; §31.3 lines 2547–2553; UC-06 lines 1426–1436; class-create path in §21.2 line 1622 | Rev60 includes a Manager surface for capacity, class create/archive/suspend, assignments/roster, and billing context. The BE source does not provide all such areas; the broad API surface remains OPEN. |
| §23.1 (:1859–1861) | §23.1 lines 1830–1834 | Effective capacity is 10 base slots plus paid add-ons, minus Billing-selected suspensions at the effective time; classes within capacity are writable, suspended classes read-only. |
| §23.3 (:1877, :1884–1886) | §23.3 lines 1850–1863, especially 1857–1859 | New class/run creation remains allowed during seven-day GRACE after failed renewal; it is blocked after RESTRICTED while existing data remain readable/manageable. |
| §23.4 (:1894–1896) | §23.4 lines 1865–1869 | Downgrade selection, versioned effective-time Billing events, idempotent BE1 projection, and retained read-only class/roster/run history are specified. |

## BE implementation evidence

| Source | Observation |
|---|---|
| backend/src/sketch2life/interfaces/http/routers/be1_registry.py:54 | Registry router prefix is /api/be1/v1. |
| backend/src/sketch2life/interfaces/http/routers/be1_registry.py:235-268 | Declares POST create-class, returns 201; currently requires school_admin, constructs a new class UUID/model, flushes, writes audit/event, commits, then returns Be1ClassV1, class_id, and display_name. No Billing read, capacity check, or idempotency key appears in this handler. |
| backend/src/sketch2life/contracts/schemas/be1_runtime.py:19-35 | Request base forbids extra fields; display_name is required and limited to 1–200 characters. No client capacity, expected revision, or idempotency input. |
| backend/src/sketch2life/contracts/schemas/be1_runtime.py:449-452 | Current Be1Error schema contains code, message, and request_id. Canonical Rev60 §9.8 lines 820–831 specifies correlation_id, retryable, optional retry_after_seconds, and field_errors as well; the public error-envelope mapping is unresolved. |
| backend/src/sketch2life/interfaces/http/be1_runtime.py:169-176 | Handler dependency verifies bearer credentials into a verified adult principal. |
| backend/src/sketch2life/interfaces/http/routers/be1_registry.py:61-82; backend/src/sketch2life/interfaces/http/routers/be1_common.py:83-124 | Current source role/scope behavior resolves an active assignment by principal subject and organization. Missing/inactive assignment can return 403 ACCOUNT_SCOPE_UNAVAILABLE; selected policy denials map to 403 SCOPE_DENIED. The route requires school_admin. This is observed behavior, not closure of the broader SRS create-class resolver. |
| backend/src/sketch2life/interfaces/http/routers/be1_registry.py:210-232 | Class list returns only rows with state active; it does not expose Billing period or suspension history. |
| backend/src/sketch2life/infrastructure/persistence/be1_models.py:93-112 | Classroom persistence stores organization ID, name, free-form string state defaulting to active, creator, and timestamp. Its listed unique constraint is organization/class ID, with organization/state index; no capacity enforcement is visible here. |
| backend/src/sketch2life/application/ports, application/services, infrastructure, and infrastructure/persistence search at pinned HEAD | No Billing organization-capacity/entitlement port, adapter, capacity-period implementation, or suspension-event consumer was found. Capacity matches in the inspected source are unrelated canvas/queue limits. This is a source-search result, not proof about deployment/runtime. |
| backend/src/sketch2life/interfaces/http/routers/be1_runtime.py:20; backend/src/sketch2life/interfaces/http/router_composition.py:35-75; backend/src/sketch2life/interfaces/http/app.py:1004-1009,1347-1353; backend/src/sketch2life/main.py:5 | Static composition mounts BE1 registry in classroom composition; combined composition includes classroom composition; main.py calls create_app(). This establishes source registration only. No app was started and no composition test was run. |

## OpenAPI and FE evidence

- backend/src/sketch2life/interfaces/http/openapi_contract.py:2839- has a mounted-operation catalog entry for POST /api/be1/v1/organizations/{organization_id}/classes. It records CreateClassRequest {display_name}, X-Request-ID, bearer security, 201 generic object, and generic BE1 errors; it does not list an idempotency key. Its verification text references API-family evidence EV-063-30 and explicitly says this operation was not individually live-probed.
- backend/src/sketch2life/interfaces/http/openapi_srs_v22.py:8-45 includes the exact BE path/method in the public projection allowlist. :194-215 filters the runtime schema through that allowlist. app.py:1054-1118,1318-1343 builds/annotates runtime OpenAPI and applies the projection for the combined profile. These are source declarations; the full and projected outputs were not generated here.
- backend/tests/contract/test_openapi_contract_catalog.py:237- and :291- describe assertions over mounted operations. backend/tests/contract/test_app_composition.py:196- checks composition/OpenAPI for profiles. Test-file presence is not a test result; neither file was run.
- FE apps/web/src/modules/school-manager/be1/services/classService.ts:14-34 has createClass(displayName) and sends only JSON display_name. be1Client.ts:20-40 supplies bearer auth, X-Request-ID, and JSON content type, but no idempotency key. X-Request-ID is correlation only. Its error adapter reads status, code, and message, not request_id/retry metadata.
- FE apps/web/src/modules/school-manager/be1/pages/ClassesPage.tsx:62-68 shows a capacity-disabled notice and renders no create action. Search of the Manager BE1 module found no UI call to classService.createClass; __tests__/managerBusinessPages.test.tsx:100-107 states the create action remains unavailable and asserts the create service is not called. FE tests were not run and the FE worktree was not modified.

## Classification and unresolved contract details

- **Existing and mounted by source:** BE1 class-create route under the combined/classroom composition.
- **OpenAPI source declared:** mounted-operation metadata exists; the implementation's public v2.2 OpenAPI projection allowlist includes the operation. This is implementation evidence, not proof of conformance to canonical Rev60. Generated full/projection outputs are NOT VERIFIED in this read-only task.
- **Adapter-backed but not UI-called:** FE classService.createClass; no page caller exists, and the create action is unavailable.
- **Intentionally unwired:** class create from the UI until capacity is enforced and separately verified.
- **Capacity implementation absent:** Billing-owned port/adapter and BE1 admission call; no direct Billing capacity state or version reaches this handler.
- **Concurrency blocker:** no current guard can establish the SRS invariant against simultaneous requests.
- **Suspension blocker:** Billing event/version ownership and effective-time projection are in SRS, but no matching implementation was found in this route/state path.
- **SRS-specified, current source gap:** this state-changing command requires idempotency; same key/payload replays the original result; same key/different payload returns HTTP 400 INVALID_IDEMPOTENCY_KEY.
- **Public contract OPEN:** literal idempotency header name, format/length, missing-key error mapping, fingerprint/canonicalization and receipt retention; Billing unavailable/stale outcome (including any 503/code); exact class-ref schema; current BE1-to-SRS error-envelope mapping; broader create-class permission resolver; SRS-required 404 versus current source 403 unless an owner-approved exception exists; mapping from SRS shorthand route to source path; exact concurrency/reservation/receipt mechanism.

## Review limits

This evidence records source declarations and static documentation only. No tests, build, validator, diff-check, backend/runtime, database, Docker, installation, network/provider, or Modal command was run. No source/test/schema/migration/OpenAPI/approval/SRS/FE file was changed. The accompanying draft is not implementation approval; MGR-7 still requires an exact approved allowlist and official Task Approval.
