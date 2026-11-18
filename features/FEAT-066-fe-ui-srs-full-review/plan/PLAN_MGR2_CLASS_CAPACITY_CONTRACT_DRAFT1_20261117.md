# MGR-2 — Billing-owned class-capacity contract

**Status:** DRAFT / NOT APPROVED / NOT LAUNCHED  
**Date:** 2026-11-17  
**Scope:** Contract planning and source evidence only. This draft authorizes no source, schema, migration, OpenAPI, test, runtime, or FE changes.

## Objective

Define the owner-review contract needed before the existing School Manager class-create operation can safely enforce the current effective organization capacity. Keep the current UI action unavailable until the BE contract and a separately approved verification pass are complete.

**Historical task-input provenance only:** The original MGR-2 task record states that the owner selected the unsigned external SRS at D:\Downloads\SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS (2).md, recording 701,157 bytes, SHA-256 B9B1F42D0BB118C19C81607D3913B7E4F1D8B6F673F0C3FBB6402888FEB675F5, and §§1–31. That record also reports a Rev69 header and revision history ending at Rev68; preserve this as OPEN / NOT VERIFIED. The external file, hash, and revision discrepancy were not independently inspected for this citation update. They are not current SRS authority. Current product requirements in this plan use only the repository canonical FEAT-063 v2.7-draft Rev60 named by docs/context/SRS_AUTHORITY.md. The accompanying evidence note maps each retained external locator to a directly checked Rev60 locator; all SRS clause references below mean Rev60.

## Current implementation surface

| Evidence level | Finding |
|---|---|
| Declared route | POST /api/be1/v1/organizations/{organization_id}/classes, declared in backend/src/sketch2life/interfaces/http/routers/be1_registry.py:235-268. |
| Mounted composition | be1_registry.router is included by be1_runtime.router (backend/src/sketch2life/interfaces/http/routers/be1_runtime.py:20); classroom composition mounts that router and combined composition calls classroom composition (backend/src/sketch2life/interfaces/http/router_composition.py:35-75). create_app selects combined or classroom composition (backend/src/sketch2life/interfaces/http/app.py:1004-1009); main.py:5 uses create_app(). This is static composition evidence, not runtime proof. |
| Request/auth | CreateClassRequest accepts only display_name (1–200 characters; extra fields forbidden), get_verified_adult requires bearer authentication, and the handler currently requires an active school_admin assignment for the path organization. X-Request-ID is described by the OpenAPI catalog and sent by the FE client for correlation. No capacity, revision, or idempotency key is present in this route contract. |
| Write boundary | The route itself creates ClassroomModel, flushes, audits/emits an event, and commits through the injected SQLAlchemy session. No class-creation application service or repository boundary is used by this handler. |
| Capacity source | No Billing-owned organization-capacity/entitlement port or adapter was found in the checked BE source baseline. The route neither reads Billing nor checks capacity before inserting. The organization path parameter is an authorization scope only; it must never become entitlement evidence. |
| Concurrency | The create handler contains no capacity count, capacity lock, version comparison, or serialization mechanism. Its ordinary DB write transaction does not establish the SRS no-over-capacity invariant. |
| Class state | ClassroomModel has a string state defaulting to active; the current class list filters to active. No Billing capacity period or suspension event is represented in this route/model path. |
| OpenAPI source | openapi_contract.py has a mounted-operation catalog entry for the exact BE path with CreateClassRequest, X-Request-ID, bearer auth, and a generic JSON object success response; it does not list an idempotency key. openapi_srs_v22.py includes the same method/path in its public projection allowlist. The full or projected schema was not generated during this task. |
| SRS API projection | Rev60 §9.6 lines 766–775 lists the proposed organization/class route group; §21.2 lines 1616–1622 specifies POST /v1/organizations/{org_id}/classes, a transactional effective-capacity check, and 201 class ref or CLASS_CAPACITY_REACHED. The shorter SRS path and the implemented /api/be1/v1/... path have not been formally mapped; treat the prefix/parameter-name relationship as OPEN rather than silently changing either source. |
| FE adapter/UI | classService.createClass exists and sends only display_name; no page calls it. ClassesPage displays that creation is temporarily locked because capacity is not checked, and contains no create action. The FE test source asserts the service is not called while unavailable; that test was not run. |

## Contract state: specified, proposed, and OPEN

| Topic | State | Contract statement |
|---|---|---|
| Capacity ownership | SPECIFIED by Rev60 §§9.7 lines 793–815, 23.1 lines 1832–1834, 23.4 lines 1867–1869; §21.2 line 1622 defines the class-create contract | Billing owns organization subscription and effective capacity: 10 included base slots plus paid add-on slots, with Billing-selected class suspensions applied at their effective time. BE1 owns class records and consumes a versioned Billing entitlement decision; do not duplicate Billing calculations or read Billing-owned storage directly from the BE1 route. The exact representation of the selected suspension set remains tied to the approved Billing contract. |
| Create-time guard | SPECIFIED by Rev60 FR-T-03 line 522, UC-06 lines 1426–1436, and §21.2 line 1622 | Check effective capacity at command/transaction time. Concurrent create commands must be serialized so active writable classes cannot exceed current capacity. |
| Capacity evidence | PROPOSED bounded contract; protocol OPEN | Before a class insert, BE1 must obtain an authoritative, current, versioned Billing decision for the authorized organization, including the effective capacity and Billing-selected suspension set effective for that decision, and enforce it with a concurrency-safe admission/serialization guarantee. Apply the versioned, idempotent Billing-to-BE1 projection at its effective time. A read-only snapshot followed by an independent insert is insufficient. Exact counting across suspension transitions, the port, receipt/reservation strategy, recovery, and owner-side transaction boundaries remain OPEN; do not assume a cross-module SQL transaction. |
| Organization scope | CURRENT SOURCE OBSERVATION; broader resolver OPEN | The current handler verifies a principal and requires school_admin assignment in the path organization. D-066-62 specifically governs verified same-organization Teacher candidates for assignment; it does not decide the broader create-class authorization resolver. Rev60 FR-T-02 line 521 and §31.10 line 2726 leave permission storage/resolution OPEN. Keep the current guard as source evidence and the target resolver OPEN. The path organization ID is not entitlement evidence. |
| Request body | CURRENT SOURCE | display_name only, bounded 1–200 characters. The current request has no client capacity, expected revision, or idempotency key. |
| Request headers and idempotency | SRS SPECIFIED / CURRENT SOURCE GAP | Class creation is a state-changing command, so Rev60 §9.6 line 791 gives the general requirement for an idempotency key; §§21.1 line 1609 and 21.4 line 1670 define its scope and retry behavior. A retry with the same key and payload returns the original result; reuse of the same key with a different payload returns HTTP 400 INVALID_IDEMPOTENCY_KEY (Rev60 §9.8 line 835 and §21.4 line 1670). The route-group list in §9.6 lines 766–775 does not define the concrete key protocol. X-Request-ID is correlation only, not idempotency. The current BE route and FE adapter do not accept/send an idempotency key. Keep the literal wire header name, format/length, missing-key response mapping, payload fingerprint/canonicalization, and receipt-retention policy OPEN unless directly established by an approved source. |
| Success response | SRS SPECIFIED; source observed | Rev60 §21.2 line 1622 requires 201 on success. Current response is {contract: Be1ClassV1, class_id, display_name} with a generic object OpenAPI schema. Whether this is the final public class-ref shape is OPEN. |
| Error envelope | CURRENT SOURCE / CONTRACT GAP | BE1 Be1Error contains code, message, and request_id. Rev60 §9.8 lines 820–831 requires code, safe message, correlation_id, retryable, and optional retry_after_seconds/field_errors. Reconcile this operation's final envelope and OpenAPI schema; do not assume the current BE1 shape satisfies the target SRS. |
| Full capacity | SRS SPECIFIED | Return CLASS_CAPACITY_REACHED; Rev60 §9.8 line 839 assigns it HTTP 409 and §21.2 line 1622 names it as the full-capacity result. Current handler does not return it. |
| Subscription state | SRS SPECIFIED | During the seven-day GRACE period after failed renewal, new class/run creation remains allowed. Once subscription becomes RESTRICTED, new class creation is blocked while existing class/roster data remain readable/manageable (Rev60 §23.3 lines 1857–1859). Rev60 §9.8 line 839 lists SUBSCRIPTION_RESTRICTED as HTTP 409. Current handler does not check Billing subscription state. |
| Billing missing/unavailable | FAIL CLOSED from MGR-1; public mapping OPEN | Do not insert a class unless effective capacity is verified. SRS/source does not define a Billing-specific public status or error code. HTTP 503 or any named dependency code is PROPOSED/OPEN only, not SRS-mandated; do not invent or publish one before owner/API review. Retryability and retry-after behavior are also OPEN. |
| Stale entitlement | Guard principle specified; public outcome OPEN | Do not create from a stale or unverified capacity decision. Rev60 §9.7 line 815 requires a versioned entitlement decision but does not define this command's stale code, status, or client retry behavior. The owner contract must define whether to re-resolve internally or reject safely. |
| Suspended classes | SRS SPECIFIED; implementation absent | At the downgrade effective time, admission must use Billing's effective capacity and the Billing-selected suspension set (Rev60 §23.1 lines 1832–1834 and §23.4 lines 1867–1869). Billing emits a versioned CapacityClassSuspensionScheduledV1 projection; BE1 applies it idempotently. Suspended classes remain readable/read-only and history is retained. Any unspecified count/transition details remain OPEN; do not infer them. Current BE1 class list exposes only active rows and has no observed Billing event consumer here. |
| Unauthorized/cross-organization | SRS target specified; current source gap | Rev60 §9.8 lines 837–838 requires the same 404 error shape for nonexistent and out-of-scope resources; 403 is only for an action denial after the resource is known to be in scope. Current handler returns 403 ACCOUNT_SCOPE_UNAVAILABLE or maps selected denials to 403 SCOPE_DENIED for missing/wrong organization assignment. Treat this as a source gap unless an owner-approved exception exists; do not present current 403 behavior as target policy. |

## Ownership boundary and proposed command flow

1. Authenticate the bearer principal. The current route checks a school_admin assignment, but the broader target create-class permission resolver remains OPEN under Rev60 FR-T-02 line 521 and §31.10 line 2726.
2. Apply the approved organization-scope policy before reading Billing. Target behavior follows Rev60 §9.8 lines 837–838: use the same 404 shape for nonexistent and out-of-scope resources, and use 403 only for a known in-scope action denial. The current 403 path behavior is a source gap unless an owner-approved exception exists.
3. Require the SRS-mandated idempotency key for this state-changing command. Scope it by principal, operation, and applicable resource target; same key/payload replays the original result, while same key with a different payload returns 400 INVALID_IDEMPOTENCY_KEY (Rev60 §§21.1/21.4 lines 1609/1670; §9.8 line 835). Exact wire header name, format/length, missing-key response mapping, fingerprint/canonicalization, and receipt retention remain OPEN.
4. Ask a Billing-owned, versioned contract for current organization entitlement, effective capacity, and the Billing-selected suspension set effective for that capacity period. Billing remains authoritative for subscription state, paid add-ons, effective period, and downgrade decisions.
5. Require a concurrency-safe admission decision before creating the BE1 class. The exact reservation/receipt/locking mechanism and recovery are PROPOSED/OPEN; owner review must ensure two concurrent requests cannot consume the same final slot without assuming a cross-owner SQL transaction.
6. On accepted admission, create the class under BE1 ownership and return the approved 201 class reference (Rev60 §21.2 line 1622). On known full capacity, return SRS-defined 409 CLASS_CAPACITY_REACHED (Rev60 §§9.8 line 839, 21.2 line 1622). During GRACE, class creation remains allowed; once RESTRICTED, block new class creation with the SRS-defined outcome (Rev60 §23.3 lines 1857–1859). On unknown/unavailable/stale capacity, fail closed and return only a separately approved safe contract outcome; any 503/code mapping is PROPOSED/OPEN.
7. Apply Billing's versioned, idempotent suspension projection at its effective time (Rev60 §23.4 lines 1867–1869). Suspended classes remain readable/read-only and history is retained. Any unspecified class-count or transition detail remains OPEN.

This flow is a contract proposal, not an implementation decision. It does not define a new public route, Billing table, schema, receipt format, or owner allocation beyond the SRS's named ownership.

## Negative-case contract matrix

| Case | Required behavior | Public result |
|---|---|---|
| Capacity available and current | Permit BE1 class creation only after verified, concurrency-safe admission. | Rev60 §21.2 line 1622 specifies 201; final class-ref schema remains OPEN. |
| Capacity full | Do not insert or emit a successful class-created result. | Rev60 §9.8 line 839 and §21.2 line 1622 specify 409 CLASS_CAPACITY_REACHED. |
| Two requests for final slot | At most one may be admitted; no execution ordering may exceed effective capacity. | Rev60 FR-T-03 line 522 and UC-06 lines 1433–1435 require serialization; exact mechanism and loser mapping for races remain OPEN. |
| Idempotency key missing | This state-changing command requires a key. | The general requirement appears in Rev60 §9.6 line 791; §§21.1 line 1609 and 21.4 line 1670 provide command/retry detail. Exact wire header and missing-key error mapping remain OPEN unless established by the approved API contract. |
| Same key and same payload retry | Return the original result; do not create a second class. | Rev60 §21.4 line 1670 specifies replay; the current route has no receipt/idempotency handling. |
| Same key with different payload | Do not execute as a second command. | HTTP 400 INVALID_IDEMPOTENCY_KEY is specified by Rev60 §9.8 line 835 and §21.4 line 1670. |
| Entitlement version stale | Do not create from the stale result. Resolve current version or fail closed. | Rev60 §9.7 line 815 requires a versioned entitlement decision; public code/status/retry semantics remain OPEN. |
| Billing contract missing, timeout, or unavailable | Do not create. Preserve only safe correlation metadata required by the approved contract; do not invent an event/table. | Public status/code/retryability OPEN. A 503 or named dependency code is PROPOSED/OPEN, not SRS-mandated. |
| Subscription GRACE | Permit new class creation during the seven-day grace period after failed renewal, subject to verified effective capacity. | Rev60 §23.3 line 1857 specifies creation remains allowed during GRACE. |
| Subscription RESTRICTED | Block new class creation and preserve existing read/manage behavior. | Rev60 §23.3 line 1859 and §9.8 line 839 specify 409 SUBSCRIPTION_RESTRICTED after restriction. |
| Missing/invalid bearer or inactive/unauthorized assignment | Do not query/create outside approved scope. | Current source provides authentication/scope errors including 403 ACCOUNT_SCOPE_UNAVAILABLE / SCOPE_DENIED. Target out-of-scope behavior is 404 per Rev60 §9.8 lines 837–838; current 403 is a source gap unless owner-approved exception. |
| Downgrade/suspension effective | Admission uses effective capacity and Billing-selected suspension set at the effective time; apply versioned, idempotent projection; keep suspended class readable/read-only and retain history. | Rev60 §23.1 lines 1832–1834 and §23.4 lines 1867–1869 specify this behavior. Any unspecified counting/transition detail stays OPEN. |
| Retry after lost response | Current behavior can create another class because it has no idempotency key/receipt. | Rev60 §21.4 line 1670 requires same-key/same-payload replay; §9.8 line 835 and §21.4 line 1670 specify HTTP 400 for same-key/different-payload. Exact wire header, format, and receipt retention stay OPEN. |

## Future exact allowlist candidates

These are planning candidates only. No file is approved for change by this draft.

| Area | Existing candidate paths | Missing/new path decision |
|---|---|---|
| BE1 route/auth/request | backend/src/sketch2life/interfaces/http/routers/be1_registry.py; backend/src/sketch2life/interfaces/http/routers/be1_common.py; backend/src/sketch2life/contracts/schemas/be1_runtime.py | Confirm route/service boundary and any request change only after the public contract is approved. |
| Billing owner contract/adapter | No matching Billing capacity port, adapter, or implementation was found under backend/src/sketch2life at the pinned HEAD. | Exact Billing-owned contract, adapter, and persistence paths are OPEN and must be assigned by the responsible owners. Do not create them by inference. |
| BE1 persistence/projection | backend/src/sketch2life/infrastructure/persistence/be1_models.py | Change only if approved class-state projection needs it; exact state/event contract is OPEN. |
| Composition | backend/src/sketch2life/interfaces/http/routers/be1_runtime.py; backend/src/sketch2life/interfaces/http/router_composition.py; backend/src/sketch2life/interfaces/http/app.py | Include only if a separately approved adapter/use-case requires composition wiring. |
| Full OpenAPI and public OpenAPI projection | backend/src/sketch2life/interfaces/http/openapi_contract.py; backend/src/sketch2life/interfaces/http/openapi_srs_v22.py; backend/tests/contract/test_openapi_contract_catalog.py; backend/tests/contract/test_app_composition.py | Update only after path, body, error and response contracts are frozen. The public SRS document itself is not an implementation allowlist. |
| BE contract/integration verification | backend/tests/contract/test_app_composition.py; backend/tests/contract/test_openapi_contract_catalog.py; backend/tests/integration/test_be1_synthetic_pilot_postgres.py | Proposed new focused contract test: backend/tests/contract/test_be1_class_capacity_contract.py. Proposed isolated concurrency acceptance test: backend/tests/integration/test_be1_class_capacity_concurrency_postgres.py. Neither file exists in this baseline. |
| FE preservation gate | apps/web/src/modules/school-manager/be1/services/classService.ts; apps/web/src/modules/school-manager/be1/pages/ClassesPage.tsx; apps/web/src/modules/school-manager/be1/__tests__/managerBusinessPages.test.tsx | No FE change in MGR-2. Keep create unavailable until BE contract and approved verification pass; FE wiring requires a later explicit allowlist. |

## Acceptance criteria for the approved contract

1. Name the Billing-owned source and versioned effective-capacity decision without making BE1 the entitlement authority or allowing client-supplied capacity.
2. Define a concurrency-safe admission guarantee that prevents more active writable classes than effective capacity, including races for the final slot and the Billing-selected suspension set at its effective time.
3. Preserve Rev60 §21.2 line 1622's 201, §9.8 line 839's 409 CLASS_CAPACITY_REACHED, and §23.3 lines 1857–1859's GRACE/RESTRICTED behavior.
4. Require idempotency for this state-changing command under Rev60 §21.1 line 1609 and §21.4 line 1670; specify same-key/same-payload replay and HTTP 400 INVALID_IDEMPOTENCY_KEY under §9.8 line 835 and §21.4 line 1670. Keep unspecified wire header spelling, format/length, missing-key mapping, fingerprint details, and receipt retention OPEN.
5. Define a fail-closed response for missing/unavailable/stale Billing decisions. Any 503 or named dependency code is PROPOSED/OPEN, not SRS-mandated.
6. Define how Billing downgrade/suspension versions and selected class sets become BE1 read-only projections at their effective time. Leave unspecified counting/transition detail OPEN.
7. Resolve the Rev60 §9.6 line 774 / §21.2 line 1622 shorthand route to the implemented public path and freeze request, response, generic error envelope, and correlation/idempotency semantics.
8. Keep the current school_admin guard as source evidence, leave the broader Rev60 FR-T-02 line 521 / §31.10 line 2726 permission resolver OPEN, and align out-of-scope requests to Rev60 §9.8 lines 837–838's 404 shape unless an owner-approved exception exists.
9. Update the full OpenAPI contract and public projection consistently, and provide source/test evidence without presenting declarations as runtime success.
10. Keep the Manager UI create action unavailable until a separate approved verification pass establishes the BE behavior.
11. Produce a separate exact MGR-7 implementation allowlist and official Task Approval before any implementation work.

## Verification plan (not run in MGR-2)

- Static review of finalized route, Billing port/adapter, assignment guard, state projection, and transaction boundary.
- Contract coverage for capacity available, base 10 slots, paid add-ons, full capacity, GRACE-allowed and RESTRICTED-blocked creation, missing/unavailable Billing, stale version, required idempotency key, same-key/same-payload replay, same-key/different-payload HTTP 400, unauthorized/cross-organization actor, and suspended-class projection/read-only behavior at its effective time.
- Database-backed concurrency acceptance showing many simultaneous attempts cannot admit more writable classes than capacity; test only with an explicitly approved isolated synthetic environment.
- Full OpenAPI and public SRS projection checks for exact method/path, body, headers, success/error envelopes, and operation visibility.
- FE verification that class creation remains unavailable until the BE contract has passed its separately approved verification gate.

No test, build, validator, backend/runtime, database, Docker, network/provider, or Modal command was run for this draft.

## Dependencies and next owner action

1. Assign the Billing owner to identify or propose the authoritative versioned capacity contract and confirm how its decision stays safe under concurrent BE1 create commands.
2. Preserve Rev60 §21.1 line 1609 / §21.4 line 1670 idempotency semantics; review only unspecified wire header, key format/length, fingerprint/receipt retention, and missing-key response mapping.
3. Resolve fail-closed and stale-entitlement public outcomes; any 503/code mapping for Billing unavailable is PROPOSED/OPEN, not an SRS mandate.
4. Confirm Rev60 §23.3 lines 1857–1859 GRACE/RESTRICTED behavior, §23.4 lines 1867–1869 suspension-set effective-time projection, broader create-class permission resolver, §9.8 lines 837–838 404/403 mapping, and §9.6 line 774 / §21.2 line 1622 shorthand path mapping.
5. Review and disposition this draft. Only after those contract decisions should MGR-7 prepare an exact implementation allowlist and official Task Approval.

**Launch gate:** Not approved. No implementation authorization is granted.

## Rev69 owner-input crosswalk and checkpoint — 2026-11-18

This append-only planning checkpoint compares the owner-designated SRS input with the repository authority. It does not change the requirements authority, decide open contract details, or approve implementation.

| Input | Observed pin and authority |
|---|---|
| Repository authority | docs/context/SRS_AUTHORITY.md, 4,054 bytes, SHA-256 032223EDDD46D251DE052C54BFF16AB1D4D794F865A457272507D893E3C1521F; it identifies the canonical FEAT-063 Rev60 working SRS at 553,948 bytes, SHA-256 70DA43A35106E8C02B4BB8FCCB9628C0376C9E7EA6CFC51909ACB569703B218B. Rev60 remains the repository-authoritative, unsigned working SRS. |
| Owner-designated comparison input | D:\Downloads\SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS (2).md, 701,157 bytes, SHA-256 B9B1F42D0BB118C19C81607D3913B7E4F1D8B6F673F0C3FBB6402888FEB675F5; read in full through line 3427. Its header identifies Rev69, while its revision-history presentation ends at Rev68 and the later §32 snapshot uses Rev69 numbering. Keep that provenance inconsistency OPEN / NOT VERIFIED. It is a planning comparison input, not an authority replacement. |
| Existing MGR-2 review basis | This plan before the present append: 24,013 bytes, SHA-256 8D9780892575675DAC9FB7436D8A587FDDC61C0A9F2E5C27153969CAD1E1C055. R4 review: 2,894 bytes, SHA-256 0851B872F15718840ECFE0A92B5C055EF38617E52ACB8779D8360FC72F69A4E3. Owner disposition: 3,808 bytes, SHA-256 7F6BD4C2E9A9562904ABE55C4C26E7DE53CAD0077F88951E203B3DAE08DF2C47. These reviews do not cover this appended crosswalk. |

### MGR-2 comparison

| Topic | Current SRS and owner decision | Rev69 comparison and consequence |
|---|---|---|
| Capacity admission | Rev60 §§21.2, 23.3–23.4 require the class-create capacity gate, preserve the 10 included school slots plus applicable add-ons, permit creation during GRACE only when effective capacity is verified, block new classes in RESTRICTED, and apply Billing-selected suspension at its effective time. The current working-tree owner decision D-066-63 records Billing as capacity authority and requires a versioned, concurrency-safe admission result before BE1 writes; D-066-63 is uncommitted and absent at the pinned BE HEAD. | Owner-input §31.10 items 2 and 6 address video-generation quota assumptions and commercial/allocation questions, not school class-slot capacity. They leave buyer/allocator/payment, exhaustion, top-up terminal expiry, and role-change effects OPEN and do not alter the class-capacity requirement. They provide no Billing wire protocol, receipt/reservation semantics, BE1 error mapping, or final public endpoint contract. |
| Idempotency and errors | Rev60 §§9.8, 21.1, 21.4 define the required command replay semantics and same-key/different-payload HTTP 400 INVALID_IDEMPOTENCY_KEY; known-full and restricted outcomes remain SRS-defined. | No comparison finding closes the literal header, key validation, receipt retention, unavailable/stale Billing mapping, or recovery details. Keep those items OPEN as this plan already does; do not infer a 503 or a new error code. |
| Authorization and path | Rev60 §9.8 distinguishes uniform 404 for missing/out-of-scope resources from 403 for a known in-scope action denial. The current BE1 source guard and /api/be1/v1 prefix remain source observations, not target approval. | Rev69 does not resolve the permission resolver, source mapping, gateway-prefix relationship, generated OpenAPI, or runtime behavior. D-066-63 does not select a route change. |

### Disposition after the comparison

- The Rev69 input adds no verified Billing API, DTO, route, persistence, public error envelope, or concurrency receipt contract. MGR-2 remains contract planning; class creation remains unavailable until a final BE contract is approved, implemented, and verified under a separate authorization.
- The MGR-7/MGR-8 work does not implement MGR-2: the exact six-file MGR-7 allowlist covers the Lesson Library router/service and tests plus the shared OpenAPI contract/catalog test; it contains no BE1 class-capacity path. Current MGR-8 edits do not add BE1 class-capacity admission. They are unverified and are not evidence that this dependency is satisfied.
- The previously recorded R4 review and owner disposition apply to the earlier plan pin only; they are historical review records. This plan remains DRAFT / NOT APPROVED / NOT LAUNCHED pending separate MGR-2 owner disposition.
- No FE action is ready to enable from this comparison. No source, test, OpenAPI, decision, approval, or SRS was changed; no runtime behavior or tests were verified.
