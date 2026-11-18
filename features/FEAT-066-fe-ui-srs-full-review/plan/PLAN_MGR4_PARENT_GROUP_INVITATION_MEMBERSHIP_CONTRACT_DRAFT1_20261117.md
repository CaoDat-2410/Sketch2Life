# FEAT-066 MGR-4 — Parent Group Invitation and Membership Lifecycle Contract — Draft 1

- **Status:** DRAFT / NOT APPROVED / NOT LAUNCHED.
- **Date:** 2026-11-17 (Asia/Saigon).
- **Purpose:** define bounded BE contract-planning work for tenant-scoped Parent discovery, group invitation, membership read with current revision, and safe membership revocation. This document authorizes no implementation, API enablement, FE integration, test execution, or launch.
- **BE planning baseline:** `D:\GitHub\Sketch2Life\.worktrees\manager-api`, branch `feature/feat066-manager-api-contracts`, HEAD `1c9148e88600a101887e477541c4c4893ba1c7df`.
- **FE inspection baseline:** `D:\GitHub\Sketch2Life\.worktrees\ui`, branch `codex/fe-ui-web-remediation`, HEAD `297a28b1f406ab80e25d6e0aa5577e4b6f505ee2`.
- **Current product SRS:** repository authority `docs/context/SRS_AUTHORITY.md` points to FEAT-063 v2.7-draft Rev60, unsigned. Rev60 is the sole SRS authority for this task. No external SRS copy is used.
- **Evidence companion:** `features/FEAT-066-fe-ui-srs-full-review/evidence/notes/MGR_4_PARENT_GROUP_INVITATION_MEMBERSHIP_CONTRACT_DRAFT1_20261117.md`.

## 1. Source and decision provenance

The repository SRS authority record and canonical Rev60 SRS remain unchanged. Rev60 is a draft, not a signed product approval. FEAT-066 plans, decisions, route catalogs, tests, and UI are implementation/planning evidence only; they do not override Rev60.

**OWNER DECISION — D-066-62, working-tree-only:** the current `DECISIONS.md` working copy records that Manager-to-Parent group discovery and invitation must remain unavailable until a separately approved tenant-scoped contract defines a verified Parent reference, minimum visible fields, authority, acceptance, expiry, revocation, and audit. Guessed principal references are prohibited. It also preserves Parent as the actor for effective Parent-profile sharing consent/grants. This decision is recorded in the current working tree at `DECISIONS.md` lines 260–268, but is absent from pinned HEAD blob `ca0143cfd432bb70bfdf79e988228ef2066d9b50`. The owner-authored MGR-1 disposition note, lines 14–18, corroborates the decision. Do not describe D-066-62 as content present at pinned HEAD; do not edit `DECISIONS.md`.

D-066-63 concerns MGR-2 class-capacity planning only and is not a basis for MGR-4. The MGR-3 R2 review verdict `ACCEPT WITH NOTES` and its P3 locator note are review evidence, not implementation or FE approval. MGR-2 and MGR-3 contract records remain planning artifacts. MGR-5 and MGR-6 remain roadmap dependencies whose uncompleted interfaces are OPEN.

## 2. Scope, terms, and boundaries

### In scope

1. Define requirements and open decisions for organization-scoped Parent candidate discovery.
2. Define a safe invitation command and contract questions for recipient verification, acceptance, expiry, revoke, replay, audit, and delivery.
3. Define a manager-scoped membership list/detail read that returns only approved fields and a current revision representation.
4. Define safe membership revocation with authorization, a stale-write fence, idempotency semantics, and non-disclosing errors.

### Out of scope

- Parent-profile sharing consent or grants. Parent-group membership/invitation is not consent and does not itself authorize Manager access to child profiles or media.
- MGR-5 school-managed consent policy; MGR-3 Teacher assignment and the larger UC-12 reassignment/offboarding saga; MGR-2 class capacity; MGR-6 immutable lesson-version review; MGR-10 inbox/notification delivery.
- Any source, schema, migration, OpenAPI, FE, test, runtime, database, or live-data change in this planning task.
- Any decision about the general Manager permission resolver, Parent identity owner, candidate display fields, or who may leave/revoke membership beyond what is already established in source.

### Evidence labels

- **SRS REQUIREMENT:** specified in canonical Rev60.
- **OWNER DECISION:** owner direction recorded in the current working tree, with its baseline stated explicitly.
- **CURRENT SOURCE FACT:** directly observed static source or test-file content; never a runtime claim.
- **PROPOSAL:** a candidate contract direction for owner/API review only.
- **OPEN / NOT VERIFIED:** not specified, not established by inspected source, or not exercised in this task.

## 3. Rev60 traceability

| Requirement | Rev60 evidence | MGR-4 treatment |
|---|---|---|
| School Manager is scoped to one school organization; Parent groups are tenant-bound; roles do not cross organization boundaries. | §§3/4, lines 208–217; §31.3, lines 2547–2553; BR-49, line 2647. | **SRS REQUIREMENT.** Candidate, invitation, membership read, and revoke must be checked server-side against current organization/resource. Exact API path and permission resolver are not specified. |
| Backend derives principal/scope from verified authentication and server-side facts, not request-body role/owner/organization assertions. | §21.1, lines 1608–1614; authorization principle at line 1600. | **SRS REQUIREMENT.** A supplied `parent_principal_ref` is not proof of a verified Parent or organizational eligibility. |
| Manager can manage Parent groups; Parent remains actor for Parent-profile sharing consent/grants. | §31.3, lines 2547–2555 and permission matrix 2557–2562. | **SRS REQUIREMENT.** Group membership and profile-sharing consent are separate. The SRS Parent-to-named-Teacher/school profile-share invitation lifecycle does not define Manager-to-Parent group invitations. |
| Group audiences/membership and grants can be revoked; tenant isolation is required. | FR-PL-06, FR-PL-23, BR-49, BR-58, lines 2620, 2637, 2647, 2656. | **SRS REQUIREMENT.** Membership is tenant-scoped and revocable. Rev60 does not define MGR-4 routes, candidate fields, or complete group-membership state transitions. |
| Rev60 §9.6 lists proposed resource groups, not final OpenAPI; it does not specify Parent candidate or membership routes. | §9.6, lines 766–791. | **OPEN.** Do not select a public route or infer a final path from current `/api/lesson-library/v1` implementation. |
| Identity and organization/class facts have owners, but Parent-group membership and a tenant-scoped Parent-discovery adapter are not specified as a complete API contract. | §9.7, lines 793–818; BE1 identity scope at 799 and organization/class/roster at 800. | **OPEN / NOT VERIFIED.** No physical data owner or supported Parent candidate lookup is selected. A table name/current principal field is not proof of a canonical owner. |
| Lists use opaque cursor pagination, default 25, maximum 100, deterministic server-defined order. Each response is versioned or a standard error. | §21.1, lines 1605–1614. | **SRS REQUIREMENT.** New candidate/member lists follow these rules. Existing group and Parent-pending-invitation lists use default 50, a source gap against the shared default. |
| State commands use principal/operation/target-scoped idempotency; same key/payload replays original result; different payload returns `INVALID_IDEMPOTENCY_KEY`. | §21.1 line 1609; §21.4 lines 1668–1672; §9.8 line 835 (HTTP 400). | **SRS REQUIREMENT.** Applies to invite create/accept and revoke. Literal header, format/length, receipt storage/retention, and target encoding remain **OPEN**. `X-Request-ID` is correlation, not idempotency. |
| Standard error envelope and non-disclosure: 403 only for known in-scope denial; 404 same safe shape for absent/out-of-scope. | §9.8, lines 820–840. | **SRS REQUIREMENT.** Envelope is `code`, `message`, `correlation_id`, `retryable`, optional `retry_after_seconds` and `field_errors`. Operation-specific invite/membership codes and status mappings not stated by Rev60 remain **OPEN**. |
| Role/permission persistence, resolver/version/revoke mapping and audit metadata/retention remain unresolved. | §31.3 line 2551; §31.10(14) line 2726 and (17) line 2729. | **OPEN.** Do not invent a resolver, audit retention, table, or event schema. D-066-62 separately requires authority and audit definition before Manager invitation enablement. |

## 4. Current source inventory by capability

The source evidence note contains live source pins and line-level references. `Declared`, `mounted`, catalogued, projected, FE-connected, test-source-present, test-run, and runtime-verified are separate evidence levels.

| Capability | BE declaration and composition | OpenAPI source | FE adapter and UI | Test source / execution | Current blocker and classification |
|---|---|---|---|---|---|
| Parent candidate discovery | No candidate route, DTO, service method, or verified Parent lookup was found in the audited Lesson Library router/service/schema. Group listing is not person search. | No candidate path in static full catalog; no Parent-group path in Rev22 SRS projection source. | No candidate method/caller. Parent Groups page says inviting members is unavailable pending Parent lookup and membership read. | No candidate test found in reviewed route/FE files. Not run. | **ABSENT / BLOCKED.** D-066-62; candidate authority, tenant binding, minimum fields, and permission resolver **OPEN**. No guessed IDs/global search. |
| Invitation create/send | `POST .../parent-groups/{parent_group_id}/invitations` declared and included in combined composition source. Handler accepts caller-supplied `parent_principal_ref` without verified-candidate binding; service does not establish an existing active verified Parent in target organization. It writes an outbox event, but no delivery consumer was found in audited BE source. | Route in static full catalog; absent from Rev22 projection. Actual emitted OpenAPI not generated/inspected. | No invitation client/caller. Manager UI labels invitation unavailable. | Integration test source covers synthetic invite and Parent pending-invite read/accept. Not run. | **DECLARED / STATICALLY MOUNTED / UI UNAVAILABLE.** Blocked by D-066-62 and missing verified recipient binding. Delivery, retry, expiry, audit, and state outcomes are not established as target behavior. |
| Membership read | No Manager membership list/detail route found. `GET /me/parent-group-invitations` is Parent-self pending/unexpired invitation read; `GET .../parent-groups` returns group records only. | Parent-self list is catalogued; no Manager membership list/detail path. Neither is in Rev22 projection source. | No Manager membership-read method/caller. Page says it needs membership read and revision before invite/revoke can be enabled. | Integration test source covers Parent-self pending list. Not run. | **PARTIALLY PRESENT FOR PARENT SELF, ABSENT FOR MANAGER.** Exact fields, scope, current revision/ETag, pagination, and route **OPEN**. |
| Membership revoke | `DELETE .../parent-groups/{parent_group_id}/members/{membership_id}` declared and included in combined composition source. Allows Manager or matching Parent member, requires strong numeric `If-Match` through handler validation, and returns ETag. No idempotency key/receipt. | Route in static full catalog; absent from Rev22 projection. Actual emitted OpenAPI **NOT VERIFIED**. | No revoke method/caller. Manager UI labels revoke unavailable and “Chờ API.” | Integration test source asserts Manager revoke and resulting revision/ETag; not run. | **BE SOURCE EXISTS, FE ACTION UNAVAILABLE.** Actor policy, membership read, stale/replay outcomes, consent boundary, and approved audit behavior **OPEN**. Current source lacks SRS idempotency semantics for this DELETE. |

**Supporting group directory:** `GET` and `POST /api/lesson-library/v1/organizations/{organization_id}/parent-groups` are declared, statically mounted in combined composition, and present in the catalog. The FE adapter and `/school/parent-groups` page call list/create; those controls are available in source. This does not provide Parent discovery, invitation, or membership read. FE list hard-codes limit 50 while Rev60 §21.1 defines default 25. No runtime request was made.

## 5. Existing BE contract surface (source facts only)

All routes below use router prefix `/api/lesson-library/v1`. This is a source fact, not a selected public SRS path. `Authorization: Bearer` is required by `get_verified_adult`. The FE `adminApiRequest` adds `/api` to its `/lesson-library/v1/...` path and sends Bearer plus `X-Request-ID`; configured base URL, proxy/gateway behavior, and runtime reachability are **NOT VERIFIED**.

| Method and full source path | Request / response DTO | Current authorization and scope | Headers, status, source behavior |
|---|---|---|---|
| `GET /api/lesson-library/v1/organizations/{organization_id}/parent-groups` | Query `limit` (default 50, 1–100) and `cursor`; `ParentGroupPageV1` of `ParentGroupV1 {parent_group_id, organization_id, display_name, state, created_at}`. | `_manager` requires `school_admin` org assignment; service filters by organization. | Bearer; optional `X-Request-ID`; 200. Cursor order `created_at DESC, parent_group_id DESC`. Group enumeration, not Parent/member discovery. |
| `POST /api/lesson-library/v1/organizations/{organization_id}/parent-groups` | `CreateParentGroupRequestV1 {display_name}`; 201 `ParentGroupV1`. | `_manager` requires `school_admin`; row stores path organization. | Bearer; required `Idempotency-Key` length 1–128; source uses receipt helper and records allow audit. |
| `POST /api/lesson-library/v1/organizations/{organization_id}/parent-groups/{parent_group_id}/invitations` | `InviteParentToGroupRequestV1 {parent_principal_ref}`; 201 `ParentGroupInvitationV1`, with membership/group IDs, state, timestamps, revision. Response omits recipient ref and organization. | `_manager` requires `school_admin`; service loads group in path organization. It only rejects a target with any active organization assignment; it does not verify target existence, active Parent role, issuer, or same-org Parent linkage. | Bearer; required `Idempotency-Key` length 1–128. Existing `INVITED`/`ACTIVE` returns source `409 INVITATION_EXISTS`; expired/revoked row can be reused with revision increment. Source TTL is 30 days, not SRS policy. Enqueues `lesson.parent_group_invited.v1`; delivery **NOT VERIFIED**. |
| `GET /api/lesson-library/v1/me/parent-group-invitations` | Query `limit` (default 50, 1–100), `cursor`; `ParentGroupInvitationPageV1` of membership DTOs. | `_parent_actor` requires active `AdultIdentityModel`, role `parent`, matching issuer; service filters exact authenticated principal and `INVITED` with future expiry. | Bearer; optional `X-Request-ID`; 200. Not a Manager membership history/list. |
| `POST /api/lesson-library/v1/me/parent-group-invitations/{membership_id}/accept` | No body; 200 `ParentGroupMembershipV1`. | Active Parent actor; service requires membership principal == actor. | Bearer; required `Idempotency-Key` length 1–128. Source locks membership, transitions invited to active, increments revision, audits and stores receipt. Already active may return current membership; expired may be marked expired then return source 409 `INVITATION_EXPIRED`; other non-invited state returns `409 INVALID_TRANSITION`. |
| `DELETE /api/lesson-library/v1/organizations/{organization_id}/parent-groups/{parent_group_id}/members/{membership_id}` | No body; 200 `ParentGroupMembershipV1`; response `ETag: "{revision}"`. | **CURRENT SOURCE FACT:** `get_verified_adult` verifies a bearer token into `VerifiedPrincipal` (`be1_runtime.py:169–182`). The handler tries `_manager`, catches any 403 and continues with `manager=False` (`lesson_library.py:611–622`); service checks group and compares only stored `parent_principal_ref` to `actor` when `manager=False` (`service.py:1605–1611`). It does not call `_parent_actor` (`lesson_library.py:119–130`) to validate active Parent role or match stored identity issuer. A stored subject match therefore does not establish a currently authorized Parent. Whether Parent self-leave is permitted remains **OPEN-OWNER**. | Bearer; strong numeric `If-Match` effectively required (`428 PRECONDITION_REQUIRED` if absent, `422 INVALID_REQUEST` if malformed); no `Idempotency-Key`. Revision mismatch yields `409 STALE_REVISION`. With matching revision, already-revoked returns as-is; otherwise source revokes and commits. Retrying with old revision after success is stale, not replay. |

`ParentGroupMembershipV1` contains `membership_id`, `parent_group_id`, `state` (`INVITED|ACTIVE|REVOKED|EXPIRED`), `invited_at`, `expires_at`, `accepted_at`, `revision`, and optional `revision_source`. Physical `be1_parent_groups` / `be1_parent_group_members` metadata is under Lesson Library source; name/location does not establish logical ownership, migration state, authoritative Parent discovery, or runtime persistence.

The current Lesson Library error handler serializes `{code, message, request_id}` and an `X-Request-ID` response header (`app.py:467–489`). **CURRENT SOURCE GAP — organization scope:** group create/list/invite handlers call `_manager` before the service lookup (`lesson_library.py:519, 535, 556`); `_manager` requires `school_admin` (`lesson_library.py:111–112`) and `require_assignment` can return HTTP 403 `ACCOUNT_SCOPE_UNAVAILABLE` when identity is missing/inactive, role unsupported, or no active organization assignment exists (`be1_common.py:83–114`). An out-of-scope organization request can therefore receive 403 before a group lookup. Rev60 §9.8 requires the same-shape HTTP 404 `RESOURCE_NOT_FOUND` for nonexistent and out-of-scope resources with no existence leak, and 403 `ACTION_NOT_ALLOWED` only for known in-scope action denial (SRS lines 833–839). The current behavior is a source gap, not target policy; the safe resolver/lookup/error mapping remains OPEN and runtime is NOT VERIFIED. The FE client sends `X-Request-ID`, which is correlation only. Current source includes codes such as `FORBIDDEN`, `ACCOUNT_SCOPE_UNAVAILABLE`, `INVITATION_EXISTS`, `INVITATION_EXPIRED`, `INVALID_TRANSITION`, `STALE_REVISION`, and `IDEMPOTENCY_KEY_REUSED`; these are implementation observations, not target policy. Current mismatched-payload idempotency maps to HTTP 409 `IDEMPOTENCY_KEY_REUSED`, while Rev60 requires HTTP 400 `INVALID_IDEMPOTENCY_KEY`. Error serialization lacks Rev60 `correlation_id` and `retryable` fields.

## 6. Contract direction for owner/API review

Everything here is **PROPOSAL** or **OPEN**, not an SRS route or approved implementation.

| Capability | Contract target for review | Unresolved decision |
|---|---|---|
| Parent discovery | Manager discovery limited to verified Parent candidates eligible for the target organization, through server-authorized tenant-scoped lookup. Return only owner-approved minimum display fields and an opaque scoped reference; no guessed/global identity search or raw provider UID/email/child/profile/media by default. | Identity authority/adapter, verification/current-active definition, organization link, path, field allowlist/label, filtering/order, cursor behavior, resolver. |
| Invitation command/lifecycle | Bind to authenticated Manager, current org, active group, and verified selected Parent. **PROPOSAL:** bind acceptance to the authenticated invited Parent, subject to owner confirmation. Keep membership separate from profile consent. Apply Rev60 idempotency semantics to state commands. | Create vs delivery split, recipient-ref mechanism, who may invite, pending/accepted/declined/expired/revoked transitions, expiry, duplicate/resend/reinvite, outbox consumer, audit/retention, operation-specific outcomes. No route or TTL selected. |
| Membership read | Organization/group-scoped Manager list/detail with only approved fields and a current revision/version or approved ETag. Use Rev60 opaque cursor rules (default 25/max 100/deterministic order). Parent-self pending read is not a substitute. | Route, field list, actor permission/self-read, revision source, cursor behavior under concurrent changes, whether pending invites are included. |
| Revoke | Check current actor authorization and expected revision; stale writes do not overwrite newer state. Apply Rev60 idempotency key/replay semantics; return versioned current result and standard safe errors. **PROPOSAL:** if owner approves Parent self-leave, revalidate the bearer principal against a current active Parent identity/role and issuer before allowing it; stored principal-reference equality alone is insufficient. | Manager-only vs Parent self-leave, authoritative identity/issuer check, pending/active/expired/already-revoked behavior, precondition representation, stale mapping, replay, operation codes, effect on Lesson Library caches/jobs. Self-leave remains **OPEN-OWNER** because Rev60 does not assign that actor. |
| Errors/privacy | Use Rev60 §9.8. Same-shape 404 for missing/out-of-scope; 403 only for known in-scope action denial. | Operation-specific status/codes, retryability, and denial-vs-nondisclosing lookup boundaries. |

The source’s 30-day TTL, `INVITATION_EXISTS` / `INVITATION_EXPIRED` / `INVALID_TRANSITION`, current DTOs, and numeric `If-Match` are **CURRENT SOURCE FACTS**, not SRS target policy.

### 6.1 Lifecycle cases to settle

| Case | Current source observation | Contract status |
|---|---|---|
| Recipient verification | Handler accepts opaque string; service does not prove active verified Parent or same-org eligibility. | **OPEN / BLOCKER** under D-066-62. |
| Duplicate pending/active invite | Source returns `409 INVITATION_EXISTS`. | Status/code and safe resend/replay distinction **OPEN**. |
| Expiry | Source assigns 30-day TTL; Parent list hides expired rows; accept can mark expired then return 409. | Duration, transition, response, audit **OPEN**. |
| Acceptance | Source requires same Parent principal, changes invited to active, increments revision. | D-066-62 requires acceptance behavior to be defined; current source binds accept to the authenticated Parent principal, while target actor and exact states/replay/error representation remain **OPEN**. |
| Revoke | Source accepts current `If-Match` and locks the row. If `_manager` returns 403, handler falls back to `manager=False`; service compares the stored member principal reference to token subject only and does not establish active Parent role/issuer. | Parent self-leave authority and current identity/account/role/issuer revalidation are **OPEN-OWNER / NOT VERIFIED**. Pending-vs-active behavior, replay, audit, and side effects remain OPEN. |
| Re-invite after expired/revoked | Source reuses membership row and increments revision. | Reuse vs new invite identity **OPEN**; table constraint does not settle policy. |
| Same key/different payload | Source returns 409 `IDEMPOTENCY_KEY_REUSED`. | Rev60 target: HTTP 400 `INVALID_IDEMPOTENCY_KEY`; source gap. |
| Concurrent operations | Source uses `FOR UPDATE` for accept/revoke and existing-row invite lock; no global/runtime guarantee established. | Transaction boundary, absent-row race, isolation, replay race, cross-writer guarantee **OPEN / NOT VERIFIED**. |

## 7. Dependencies and owner questions

| Dependency / question | Evidence and disposition |
|---|---|
| MGR-1 / D-066-62 | Discovery/invitation stays unavailable until verified recipient, minimum fields, authority, acceptance, expiry, revoke, audit are defined and separately approved. D-066-62 is current-working-tree-only, absent pinned HEAD; this draft does not satisfy approval gate. |
| MGR-2 | Separate class-capacity contract/D-066-63; no capacity policy imported. Reconcile shared BE files in MGR-7. |
| MGR-3 | Separate Teacher candidate/assignment; MGR-3 R2 is `ACCEPT WITH NOTES` with a P3 note only. Teacher assignment and UC-12 remain out of scope. |
| MGR-5 | Consent actor/source/effective-state contract remains a dependency. Parent remains actor for Parent-profile consent/grants under D-066-62; MGR-4 cannot create staff-origin consent. |
| MGR-6 | Immutable LessonVersion read/review remains a roadmap dependency; MGR-4 cannot claim exact-version review. |
| MGR-10 | Invite producer inserts an outbox event; no delivery consumer found in audited BE source. Inbox/channel/retry/dedupe/retention remain separate; outbox is not delivery proof. |
| Parent identity and scoped lookup | Rev60 names BE1 for adult/Parent/Teacher scope generally, but no supported candidate lookup/approved Manager discovery contract was found. BE/API and identity owners must identify the source. |
| Authority/revoke policy | Current route checks `school_admin`; on a 403 it falls back to a stored principal-reference match without verifying active Parent role or matching stored identity issuer. D-066-62 does not settle the general Manager resolver or group self-leave. Rev60 §31.3 Parent revocation concerns profile-share consent; FR-PL-23/BR-58 say group membership is revocable but do not name a self-leave actor. | Owner/security review must decide actor set and current identity/authority checks. If Parent self-leave is approved, require verified current Parent role/account state and issuer binding; until supported, that path remains **OPEN-OWNER / NOT VERIFIED**. |
| Fields/privacy | D-066-62 requires minimum fields; no candidate/member field allowlist chosen. Exclude child profile/media and avoid matching by name/date of birth. |
| Revision/idempotency/errors | SRS fixes command idempotency and error envelope. Membership revision/ETag and exact stale mappings remain MGR-4 contract work. Literal header/receipt retention remain open. |
| Invitation lifecycle | Expiry, decline, resend, duplicate, revoke timing, delivery responsibility require owner/API disposition. Source 30-day TTL is not target policy. |
| Route mapping | Rev60 generally uses `/v1`; BE/FE source uses `/api/lesson-library/v1`. Confirm public/gateway/proxy mapping before selecting a route. |
| Audit/concurrency | Define metadata-only audit/retention consistent with §31.10(17). Prove concurrency in approved isolated tests later; source locks are not runtime proof. |

## 8. Candidate future implementation allowlist (not approved)

This bounded list is for MGR-7 review only; it grants no implementation authorization.

- BE route/DTO candidates: `backend/src/sketch2life/interfaces/http/routers/lesson_library.py`, `backend/src/sketch2life/contracts/schemas/lesson_library.py`.
- Service/persistence candidates: `backend/src/sketch2life/infrastructure/lesson_library/service.py`, `tables.py`, `receipt_compat.py`, only if an approved contract needs changes. No new table/schema/migration/logical owner is assumed.
- Identity/scope: exact adapter/port is unidentified and must be named after authoritative Parent source is evidenced. No raw identity-directory query is preapproved.
- OpenAPI candidates: `backend/src/sketch2life/interfaces/http/openapi_contract.py`, `openapi_srs_v22.py`, only after route/prefix/projection decisions.
- BE verification candidates: `backend/tests/contract/test_app_composition.py`, `backend/tests/integration/lesson_library/test_lesson_library_api.py`, plus explicitly named isolated privacy/scope/lifecycle/replay/stale/concurrency tests. None is authorized or run now.
- FE excluded from BE implementation. Later FE work needs its own plan/approval; likely pinned FE candidates are `managerBusinessService.ts` and `ParentGroupsPage.tsx`. Invite/member controls remain unavailable until BE contract approval and separately approved verification.
- Notification consumer files are unidentified and excluded until MGR-10 names them.
- No SRS/authority, `DECISIONS.md`, approvals, `CONTEXT.md`, `STATUS.md`, database state, or runtime environment is in this candidate allowlist.

## 9. Acceptance criteria and future verification (not executed)

A future approved contract/implementation must: (1) resolve Parent candidates from an identified authoritative source, verify current eligibility and org scope, and expose only approved fields; (2) name and revalidate the owner-approved acceptance actor (proposal: the authenticated invited Parent) and keep group membership separate from profile consent/media access; (3) define owner-approved lifecycle, expiry, decline/revoke, duplicate/resend, audit, and delivery; (4) provide tenant/group-scoped Manager membership read with approved fields, current revision, and Rev60 cursor rules; (5) fence revoke with current authorization and expected revision; if Parent self-leave is owner-approved, revalidate a verified bearer principal against current active Parent account/role and issuer authority—stored principal-reference equality alone is insufficient; otherwise keep self-leave unavailable; (6) apply Rev60 idempotency including original result replay and HTTP 400 `INVALID_IDEMPOTENCY_KEY` for mismatched payload; (7) use the §9.8 envelope, return the same-shape HTTP 404 `RESOURCE_NOT_FOUND` for nonexistent and out-of-scope resources without disclosing existence, and reserve 403 `ACTION_NOT_ALLOWED` for known in-scope denials; (8) demonstrate transaction/concurrency across all approved writers; (9) separately verify composition, rendered full OpenAPI, SRS projection, FE caller/guard, and runtime on pinned inputs; and (10) keep Manager invite/member actions unavailable until approved BE contract and separately approved verification pass.

After MGR-7 and task approval, verify selected route composition; inspect generated OpenAPI and the approved public projection separately; test same-org/cross-org/missing/unauthorized cases, candidate privacy, invitation acceptance/expiry/revoke/retry, idempotency, revision/stale behavior, concurrent invite/accept/revoke, audit/outbox transaction, and the separately owned notification consumer; then verify FE guard behavior. Any runtime work needs separate environment approval.

No tests, builds, validators, OpenAPI generation, backend/runtime, database, Docker, network/provider, or Modal commands were run for this planning draft. No source, FE, SRS, authority, decision, approval, or status file was edited. MGR-4 remains **DRAFT / NOT APPROVED / NOT LAUNCHED**.


