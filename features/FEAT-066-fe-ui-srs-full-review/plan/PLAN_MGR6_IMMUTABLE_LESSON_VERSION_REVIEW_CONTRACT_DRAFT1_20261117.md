# MGR-6 — Exact immutable LessonVersion review contract (Draft 1)

Status: DRAFT / NOT APPROVED / NOT LAUNCHED  
Revision note: Draft 1 corrected in place after the independent cold review recorded in MGR_5_MGR_6_COLD_REVIEW_DRAFT1_20261117.md. No Draft 2 is created.  
Scope: planning and contract review only; no API or web implementation is authorized.

## Goal

Define the source-backed boundary and proposed technical safety contract for reviewing a Teacher's PUBLIC access grant. Rev60 requires School Manager review before PUBLIC and exact lesson-version/hash pins for specified occurrence/plan/StoryRun flows; it does not specify a Manager review endpoint or require the grant itself to carry a hash. The MGR-6 proposal is to make review content demonstrably match the grant's version and hash. Current Manager reads resolve current lesson state, and no Manager GET-by-version route is declared in the inspected router/catalog. This draft does not select a new route or claim current source satisfies the proposed binding.

## Authority and SRS requirements

- Use repository SRS_AUTHORITY.md and canonical FEAT-063 Rev60 only. Rev60 is unsigned but remains the repository's current product authority.
- SRS REQUIREMENT — Rev60 §31.2 line 2536 requires a typed LessonVersionRefV1 with exact version and content hash when a lesson preset is pinned through occurrence, plan revision, and StoryRun; those existing refs are not resolved to latest or silently retargeted. Edits create a new draft/version/copy with lineage rather than overwriting the published source version. This clause does not specify a Manager review API or a grant hash field.
- SRS REQUIREMENT — Rev60 §31.2 line 2538; §31.3 lines 2547 and 2560; FR-PL-05 line 2619; Q168 line 2776; and BR-51 line 2649 require Teacher lesson review by the School Manager before PUBLIC, within organization scope. They do not define an exact review route, response DTO, version/hash payload for Manager review, or the outcome for a pending grant whose version is superseded.
- SRS REQUIREMENT — Rev60 §31.2 lines 2538–2540 requires preserving lesson/version/history while unpublish/revoke removes library access; content access returns only after republish or a valid grant. This informs scope and lifecycle but does not define superseded pending-grant review behavior.
- SRS REQUIREMENT — Rev60 §21.1 line 1613 requires cursor pagination, default 25, maximum 100, and explicit stable ordering. Rev60 §21.4 lines 1670–1672 requires idempotency for state-changing commands and expected revision/hash for the named profile/lesson-plan/story/script changes; this citation does not define an access-grant-specific revision protocol. Rev60 §9.8 lines 824–839 defines envelope fields and standard status/error codes. Route-specific detail remains to be designed.
- TECHNICAL PROPOSAL — Bind Manager review to the exact grant version and content hash, with no fallback to current/latest. This is a safety contract proposal derived from the source gap and SRS pinning principles; it is not a direct Manager-review/hash requirement stated by Rev60.

## Current source route inventory

BE router prefix: /api/lesson-library/v1 (backend/src/sketch2life/interfaces/http/routers/lesson_library.py:53). Full paths below are declared source paths. Static composition includes this router at backend/src/sketch2life/interfaces/http/router_composition.py:73; app.py:256 and 1004–1011 select/create the combined application. This is static mount evidence only; deployed routing and gateway/proxy rewriting are OPEN / NOT VERIFIED.

| Method and path | Source behavior and scope | Current DTO/revision/idempotency evidence | Contract implication |
|---|---|---|---|
| GET /api/lesson-library/v1/organizations/{organization_id}/lessons | lesson_library.py:182–199 lists organization-visible lesson summaries | Cursor page; summary does not provide exact version content/hash | Catalog/current list only; does not satisfy exact grant-version review. |
| GET /api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id} | lesson_library.py:201–216; service resolves current_version_id at 430–445 | Returns current detail, including current_version and its hash, with ETag from lesson revision | Current version detail is not a historical/exact grant-version read. |
| POST /api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}/versions | lesson_library.py:386–410 | Teacher-only; strong numeric If-Match; request includes source revision and content; response includes created LessonVersion and structured content hash/content | Version creation only; not a Manager read. |
| POST /api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}/access-grants | lesson_library.py:413–433; service.py:1065–1152 | Teacher-only; Idempotency-Key required (1–128 chars); body names version_id, audience, capability, expiry; service validates the version belongs to that lesson (1073–1080), stores that version_id (1110–1117), and response returns it through _grant_response (1311–1327); PUBLIC becomes PENDING_REVIEW | Grant request/record/response names a version_id; no hash is accepted or captured on the grant in inspected DTO/persistence. |
| GET /api/lesson-library/v1/organizations/{organization_id}/access-grants | lesson_library.py:436–453; service.py:1154–1178 | Manager-only and organization scoped; optional audience_kind, state, lesson_id filters; cursor. BE limit defaults to 50 and maxes at 100. Grant DTO contains version_id/revision, no hash/content. | Exact source path is organization-level, not nested beneath a lesson. Default 50 conflicts with Rev60 §21.1 default 25; max 100 matches. |
| POST /api/lesson-library/v1/organizations/{organization_id}/access-grants/{access_grant_id}/decision | lesson_library.py:456–479; service.py:1180–1240 | Manager-only; If-Match is parsed as required strong numeric revision; Idempotency-Key required (1–128 chars); body has decision and optional reason | Exact source path is organization-level. Decision request contains no version_id/hash; service uses the grant's stored version_id and revision. |

No GET-by-version-ID route was found in the inspected Manager router or static operation catalog. A Parent-specific GET /api/lesson-library/v1/me/lessons/{lesson_id} (router lines 695–705; service.py:2038–2055) resolves a grant version/hash under Parent access. That separate Parent route is not Manager authorization precedent and is not proposed as the Manager API.

Static API catalog has the corrected organization-level GET and POST paths at openapi_contract.py:9509 and 9575. The legacy v2.2 projection is separate and omits Manager grant list/decision. No full OpenAPI output was generated or inspected.

## Current implementation evidence and gaps

- LessonVersionV1 schema at contracts/schemas/lesson_library.py:126–158 includes version_id, version_no, review_state, structured_content_hash, and structured content. LessonDetailV1 exposes current_version, not an arbitrary requested version. LessonAccessGrantV1 at lines 172–186 returns version_id and revision but not hash/content. LessonAccessGrantDecisionResponseV1 at lines 236–242 lacks the reviewed hash/version identity.
- CreateLessonAccessGrantRequestV1 at schemas/lesson_library.py:79–93 accepts version_id and audience/capability/expiry fields; it has no hash field. ACCESS_GRANTS persistence at infrastructure/lesson_library/tables.py:184–225 stores version_id but no hash column. Version rows at tables.py:144–168 store content/hash. Version creation service.py:275–332 and 340–374 creates version rows and updates the current pointer.
- Decision service.py:1193–1220 locks/loads the grant, checks its revision and pending PUBLIC state, loads the lesson for author self-review validation, then updates review_state for the version_id stored on that grant. The inspected path does not compare grant.version_id to the lesson's current_version_id and does not validate a content hash. Static source therefore does not explicitly reject a superseded pending grant; no runtime/concurrency guarantee is claimed. DB-level enforcement preventing mutation of version content/hash was not established, so persistence-boundary immutability is NOT VERIFIED.
- Manager grant-list pagination at lesson_library.py:436–453 accepts cursor and limit, but defaults limit to 50 (maximum 100); Rev60 §21.1 line 1613 requires default 25 and maximum 100. FE supplies cursor but no limit in the accessGrants options type (backendApi.tsx:446–447). Proposed contract/implementation should set the server default to 25 while preserving a maximum of 100; FE may omit limit or pass a supported value, but this draft authorizes no change.
- Access-grant replay logic at service.py:491–507 currently returns 409 IDEMPOTENCY_KEY_REUSED for changed payload; Rev60 §9.8 line 835 requires 400 INVALID_IDEMPOTENCY_KEY. Rev60 §21.4 requires same-key/same-payload replay to return the original result. This is a source gap. Exact receipt retention policy remains OPEN where Rev60 does not specify it.
- Router If-Match parsing at routers/lesson_library.py:83–99 returns 428 when absent and 422 for malformed values; service stale revision maps at service.py:597–599 to 409 STALE_REVISION. The Lesson Library HTTPException, request-validation, and unhandled-exception branches at app.py:467–491, 612–622, and 725–740 all statically return `code`, `message`, and `request_id`, plus `X-Request-ID`; Rev60 §9.8 lines 824–839 instead names required body fields `code`, `message`, `correlation_id`, and `retryable`. This is a source-visible response-shape mismatch (the request identifier may be related, but its field name differs and `retryable` is absent); optional `retry_after_seconds` and `field_errors` need not appear. Runtime responses were not verified. The decision route checks grant revision in source; this static check does not establish race behavior or a concurrency guarantee.
- Composition is statically evidenced in router_composition.py:60–77 and app.py:256, 1004–1011. openapi_contract.py contains static operation entries for grant list/decision, lesson list/detail, and version-create near 9509, 9575, 9667, 9822, and 10192. The legacy v2.2 projection in openapi_srs_v22.py:8–92 includes list/detail/version-create but omits Manager grant list/decision. No full generated OpenAPI output or runtime was checked; static catalog and projection are separate evidence levels.

## Proposed target contract (not an approved route/schema)

TECHNICAL PROPOSAL — The Manager review read should expose enough structured lesson content for the grant's exact version and a verifiable content hash, with grant identity/state/revision, organization/lesson identity, audience/publication context, and approved attribution/provenance. It should not silently substitute current/latest content. Exclude child profile/media and unrelated authoring fields. This exact Manager hash-binding requirement is a proposed safety boundary, not a direct API requirement in Rev60.

TECHNICAL PROPOSAL — The decision command should server-side revalidate authenticated Manager role and organization scope, grant ownership/current state/revision, and the exact version/hash that the reviewer saw. Preserve the current author self-review denial in source unless a separately reviewed requirement changes it. A future contract must decide how the command proves which version/hash the Manager reviewed, such as expected version/hash preconditions or a server-verifiable review receipt; current decision DTO has neither. Retain Rev60 §9.8 error-envelope semantics and §§21.1/21.4 list/idempotency requirements. The current route's public path is the source path above; any route extension for exact-version review remains unselected. Do not infer stale/superseded outcome or race guarantees.

### Version/hash binding options — OPEN / PROPOSED

| Option | Candidate binding | Trade-off; not selected |
|---|---|---|
| A. Snapshot hash on grant | Extend grant creation/storage/response with the structured content hash for the submitted version; verify version_id and hash together at creation, read, and decision. | Explicit review receipt and easier client comparison; requires DTO/OpenAPI/schema/storage migration and consistency checks. |
| B. Resolve through immutable version record | Keep grant.version_id and resolve hash/content from that exact version row; enforce content/hash immutability at the persistence/application boundary and re-read/verify at decision. | Avoids duplicating hash on grant; depends on a proven immutable version-row guarantee and stable canonical hash. Current database enforcement is NOT VERIFIED. |

No policy or technical choice is made here. Either option still needs an exact-version read contract and decision-time binding. FE-supplied values alone are not authoritative.

### OPEN contract decisions

1. New exact-version read route/path and mapping through any gateway/proxy. Existing grant list/decision paths above are verified source paths; no extension route is selected.
2. Product outcome for a pending grant whose version is superseded: continue reviewing that original version, reject it as stale, or require a new grant. Current BE source updates review_state for the grant's stored version_id without comparing it to lesson.current_version_id; current FE blocks when current version ID differs. Runtime behavior is NOT VERIFIED.
3. Owner/technical choice between explicit hash snapshot on the grant and hash resolution via an immutability-enforced version row; canonical hash and enforcement boundary are open.
4. Decision binding shape: whether the future decision request carries expected version_id/hash or a server-verifiable review receipt; source request has neither. The BE must compare any submitted precondition to authoritative grant/version data.
5. Exact response field allowlist and any preview asset handling; exclude child media.
6. Owner/BE selection of Manager permission and state/hash-mismatch errors, correction or explicit resolution of the source-visible §9.8 response-shape mismatch across Lesson Library exception branches (`request_id`/`X-Request-ID` and missing `retryable`), and runtime response verification. Runtime wire behavior remains NOT VERIFIED.
7. Idempotency receipt retention/storage details where Rev60 leaves them unspecified. Current changed-payload code is a source gap.
8. Decision concurrency/race guarantee. Source uses grant revision checks and a row-lock request; no concurrency result is claimed without approved verification.

## FE behavior observed and target gate

Current Manager page is apps/web/src/modules/school-manager/pages/ManagerScreens.tsx. It loads organization-scoped grant rows at lines 92–105 and reads current lesson detail at lines 116–138. The guard at lines 69–72 compares selected grant.version_id to lesson.current_version.version_id and requires content. On mismatch it shows the old-version warning at lines 247–248; missing structured content also leaves canReview false. Decision buttons are disabled when canReview is false (lines 256–265). This is an FE ID/current-version guard only: it does not compare a content hash and does not replace BE stale/hash checks.

The shared client at apps/web/src/shared/api/backendApi.tsx:446–453 calls the corrected organization-level grant list and decision paths. It sends cursor/filter query options for list and If-Match plus Idempotency-Key for decision. The page uses this decision API when the FE guard allows it. Exact version/hash equality is not verified by current FE. X-Request-ID is correlation in the shared client, not an idempotency key.

The new MGR-9 exact-version review slice remains blocked until an exact-version contract is accepted and a separately approved verification pass completes; do not add the slice or claim it ready. The existing wired Manager decision controls are observed to depend on the current ID/content guard plus existing busy, reason, and confirmation conditions; they may become available when the IDs match and the required content is present. This planning draft neither authorizes nor directs changes to those existing controls. Their ID-only guard has no hash proof and does not satisfy the exact-version target. Before future MGR-9 review work, the owner must explicitly decide whether to authorize a separate FE gating change that disables the existing controls until grant-bound version/hash data is available. No FE change is authorized here.

## Planning-only file allowlist for a future implementation package

BE candidates: backend/src/sketch2life/interfaces/http/routers/lesson_library.py; backend/src/sketch2life/contracts/schemas/lesson_library.py; backend/src/sketch2life/infrastructure/lesson_library/service.py; backend/src/sketch2life/infrastructure/lesson_library/tables.py only if an approved integrity/persistence change is required; backend/src/sketch2life/interfaces/http/openapi_contract.py; backend/src/sketch2life/interfaces/http/openapi_srs_v22.py only if its public projection is explicitly in scope; and backend/tests/integration/lesson_library/test_lesson_library_api.py.

FE candidates: apps/web/src/shared/api/backendApi.tsx; apps/web/src/modules/school-manager/pages/ManagerScreens.tsx; apps/web/src/modules/school-manager/be1/App.tsx only if route state changes; and the matching Manager screen/service tests. These are planning candidates only, not an implementation allowlist or authorization.

## Dependencies and exclusions

- Depends on MGR-0 route inventory and owner/API contract review. MGR-2/3/4/5 may proceed in parallel while scopes remain disjoint.
- MGR-7 depends on all MGR-1–6 dispositions and reviewed contracts; it cannot authorize this work from this draft alone.
- Excludes public publication policy redesign, Platform Admin moderation, Teacher authoring, Parent lesson access, lesson migrations, FE edits, and runtime claims.

## Acceptance criteria for a future contract

1. A future contract explicitly selects and verifies one grant-to-version/hash binding mechanism; Rev60's exact pinning clauses remain correctly scoped to their specified flows, with Manager review binding labeled as the selected safety contract.
2. There is no fallback to current/latest version, and the owner-approved outcome for a superseded pending grant is defined.
3. Decision requires server-side tenant/role authorization, grant/version/hash validation, current revision, and an allowed transition; source or tests alone do not claim race guarantees.
4. List pagination follows Rev60 §21.1 default 25/max 100; idempotency replay/mismatch and error envelope follow Rev60 §§21.4/9.8.
5. FE displays the exact grant-bound version/hash and keeps decision unavailable on missing, stale, or mismatched content; it does not rely on the current ID-only guard as hash verification.
6. Content/hash immutability is enforced at the selected boundary or its limitation is explicitly accepted by an owner/technical decision.

## Future verification plan (not run)

After contract and implementation approval: verify route declaration and composition; compare generated full OpenAPI with the static catalog and public SRS projection separately; verify access-grant cursor ordering, default page size 25, and maximum 100; use synthetic fixtures for exact current and superseded versions, hash mismatch/tampering, cross-organization access, unauthorized actor, author self-approval, pending/decided grant, stale revision, duplicate/replayed decision, and standardized errors; verify FE displays the grant's exact version/hash and blocks action when exact data is unavailable. Do not infer runtime behavior from tests or source. No tests, build, validator, OpenAPI generation, or runtime command was run for this planning draft.

## Planning disposition

Draft 1 proposes the minimum exact-version review boundary and records implementation gaps and open choices. It is not a selected route, approved schema, implementation authorization, or launch authorization.

## Rev69 owner-input crosswalk and checkpoint — 2026-11-18

This append-only planning checkpoint compares the owner-designated SRS input with the repository authority. It preserves the distinction between School Manager review of Teacher-authored PUBLIC content and Platform Admin moderation/publication.

| Input | Observed pin and authority |
|---|---|
| Repository authority | docs/context/SRS_AUTHORITY.md, 4,054 bytes, SHA-256 032223EDDD46D251DE052C54BFF16AB1D4D794F865A457272507D893E3C1521F; canonical FEAT-063 Rev60 SRS, 553,948 bytes, SHA-256 70DA43A35106E8C02B4BB8FCCB9628C0376C9E7EA6CFC51909ACB569703B218B. Rev60 remains the repository-authoritative, unsigned working SRS. |
| Owner-designated comparison input | D:\Downloads\SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS (2).md, 701,157 bytes, SHA-256 B9B1F42D0BB118C19C81607D3913B7E4F1D8B6F673F0C3FBB6402888FEB675F5; read in full through line 3427. The header identifies Rev69, while its revision-history presentation ends at Rev68 and a later §32 snapshot uses Rev69 numbering. Preserve this as OPEN / NOT VERIFIED; it does not replace repository authority. |
| Existing MGR-6 review basis | This plan before the present append: 19,776 bytes, SHA-256 514066776BFAF0AC5BABDC9BE4D87C3E1A2C9892E28DB51B6F39BE9AEEB7FFAC. R3 review: 7,311 bytes, SHA-256 73293D0645F29994C5946E84BC3171E3D601112F16DAC0BF98BACE45198499DC. Those pins predate this crosswalk. |

### Lesson-version and publication-flow comparison

- Owner-input §31.2 requires exact optional LessonVersionRefV1 version and content hash to remain pinned across the relevant lesson/occurrence/plan/run flow, with no resolution to latest and no retargeting of old work. This supports exact version identity as a product invariant. It does not prescribe that a grant row store a duplicate hash; the two binding options in this plan remain technical proposals pending an approved contract and a verified immutability boundary.
- Rev60 plus owner-input FR-PL-05 and §31.3 retain the School Manager approval gate for Teacher-authored PUBLIC lessons. The owner input separately resolves Platform Admin-authored PUBLIC lessons to require independent review by another Platform Admin with Content Admin permission. That Platform Admin workflow is a separate publication/moderation capability; it is not the MGR-6 School Manager decision and must not be merged into it.
- Owner-input §31.10 item 7 leaves review/publish event schema and moderation evidence as technical gates. The exact Manager route/DTO, grant-bound version/hash read, superseded-pending outcome, decision precondition, standardized error mapping, and decision concurrency/race contract remain open as this plan records. No hash-on-grant storage rule is inferred.
- The current FE guard compares version IDs/current lesson detail and requires content; it does not prove hash equality. Existing FE calls or current button behavior do not satisfy the owner-input exact-pin requirement.

### Disposition after the comparison

- MGR-6 is limited to School Manager review of the exact Teacher-authored lesson version. Platform Admin moderation remains separately blocked until its authorized queue and exact-version read/decision contracts exist. Neither flow is ready for FE integration from this comparison.
- MGR-7/MGR-8 does not close MGR-6. The approved MGR-7 allowlist is confined to Lesson Library pagination and idempotency behavior; the current source edits do not implement an exact-version review route or grant/hash binding and remain unverified.
- R3, R4, and R5 are historical reviews of the exact pins recorded in their respective evidence notes; R4's P2 FE-gate ambiguity was clarified in this plan after review. The plan remains DRAFT / NOT APPROVED / NOT LAUNCHED pending separate MGR-6 owner contract/implementation disposition.
- Status remains DRAFT / NOT APPROVED / NOT LAUNCHED. No source, test, OpenAPI, decision, approval, or SRS was changed; no runtime behavior or tests were verified.
