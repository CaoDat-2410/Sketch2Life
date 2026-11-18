# MGR-6 Draft 1 — Exact LessonVersion review source evidence

Status: DRAFT / NOT APPROVED / NOT LAUNCHED. Corrected in place after cold review R1; this remains Draft 1. Static source review only; no tests, build, OpenAPI generation, or runtime verification was performed.

Pre-correction pins: plan 13,110 bytes / SHA-256 F6986B16836B98F9D82C811B4C82166F7551AA36DF5CCBC4D733F445E16E6D0B; this evidence note 11,157 bytes / SHA-256 3443AB0F9735E1D64FD5DA9F22E58CB3D11E0458F50F265802A2A847E2ADF237. Historical cold review R1 is unchanged at 7,900 bytes / SHA-256 9B26DB1474F29C52A642B816CC2100EEA880CDC9DE60F45220B6F3E9DFA69297.

## Pins and authority

- BE worktree: D:\GitHub\Sketch2Life\.worktrees\manager-api; branch feature/feat066-manager-api-contracts; HEAD 1c9148e88600a101887e477541c4c4893ba1c7df.
- FE worktree: D:\GitHub\Sketch2Life\.worktrees\ui; branch codex/fe-ui-web-remediation; HEAD 297a28b1f406ab80e25d6e0aa5577e4b6f505ee2.
- Canonical Rev60: 553,948 bytes; SHA-256 70DA43A35106E8C02B4BB8FCCB9628C0376C9E7EA6CFC51909ACB569703B218B. Authority register remains Rev60. External Rev69-header copy referenced historically in MGR-2 is not used as product authority.
- SRS REQUIREMENT — Rev60 §31.3 line 2536 requires exact LessonVersionRefV1 version/hash pinning for occurrence, plan revision, and StoryRun use; it forbids resolving latest or silently retargeting existing refs and requires edits to create a new version/copy with lineage. It does not define a Manager review API or require a grant hash.
- SRS REQUIREMENT — Rev60 §31.3 lines 2538, 2547, and 2560, FR-PL-05 line 2619, Q168 line 2776, and BR-51 line 2649 require School Manager review of Teacher lesson content before PUBLIC within organization scope. They do not specify a route, DTO, Manager review hash binding, or superseded pending-grant outcome.
- SRS REQUIREMENT — Rev60 §31.3 lines 2538–2540 preserves content/history while unpublish/revoke removes library access; republish or a valid grant is needed to regain library content access. This does not define review of a pending grant after its version is superseded.
- SRS REQUIREMENT — Rev60 §21.1 line 1613 sets cursor pagination, default 25, maximum 100, and explicit stable ordering; §21.4 lines 1670–1672 requires idempotency for state-changing commands and expected revision/hash for the named profile/lesson-plan/story/script changes. The cited clause does not define an access-grant-specific revision protocol. §9.8 lines 824–839 defines the standard error envelope/codes. These generic requirements inform a future contract; they do not specify route-specific error mappings beyond the stated standard.
- D-066-62 is an MGR-5 owner decision recorded in the current working-tree DECISIONS.md (38,951 bytes; SHA-256 A99E5AC92E747E199E350F842C6E7444942FFDD1610205B3F07AB79F60E5F61C) at lines 260–268, but absent from DECISIONS.md at pinned HEAD (blob ca0143cfd432bb70bfdf79e988228ef2066d9b50; 34,226 bytes). It does not define MGR-6 lesson-review policy and is not used as a product requirement here.

## BE route, DTO, persistence, and behavior evidence

Router is backend/src/sketch2life/interfaces/http/routers/lesson_library.py with prefix /api/lesson-library/v1 at line 53. These are source declarations, not runtime observations. Static composition includes lesson_library.router at router_composition.py:73; app.py:256 and 1004–1011 show application selection. This proves code registration only, not deployed/runtime reachability or gateway path mapping.

| Method/path | Evidence | What the source establishes | What it does not establish |
|---|---|---|---|
| GET /api/lesson-library/v1/organizations/{organization_id}/lessons | lesson_library.py:182–199 | Organization lesson list/current summaries with cursor | Exact historical version payload/hash for a grant. |
| GET /api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id} | lesson_library.py:201–216; service.py:430–445 | Current lesson detail and current_version including structured_content_hash; ETag from lesson revision | Exact requested grant version when it is no longer current. |
| POST /api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}/versions | lesson_library.py:386–410 | Teacher creation of a new version, strong numeric If-Match, content input, response with version/hash | Manager exact-version read. |
| POST /api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}/access-grants | lesson_library.py:413–433; service.py:1065–1152 | Teacher creates a grant with version_id; service validates that version belongs to lesson (1073–1080), stores the supplied version_id (1110–1117), and returns it in LessonAccessGrantV1 (_grant_response at 1311–1327); Idempotency-Key required; PUBLIC becomes PENDING_REVIEW | Request/record/response carry version_id, not a content hash. |
| GET /api/lesson-library/v1/organizations/{organization_id}/access-grants | lesson_library.py:436–453; service.py:1154–1178 | Manager-only, organization scoped; filters audience_kind/state/optional lesson_id; cursor and limit; grant response has version_id/revision. BE default limit=50, max=100. | Correct route is organization-level, with optional lesson_id query. Default 50 differs from Rev60 §21.1 default 25; max 100 matches. |
| POST /api/lesson-library/v1/organizations/{organization_id}/access-grants/{access_grant_id}/decision | lesson_library.py:456–479; service.py:1180–1240 | Manager-only; requires If-Match and Idempotency-Key; decision body contains decision/reason; service checks stored grant revision/state and uses grant.version_id | Correct route is organization-level. Request includes no version_id/hash and does not bind a reviewed content hash. |

The request/response DTO definitions in contracts/schemas/lesson_library.py:79–107, 126–158, 172–192, and 236–242 show that CreateLessonAccessGrantRequestV1 accepts version_id but no hash; LessonVersionV1 contains version_id, version_no, review_state, structured_content_hash, and content; LessonDetailV1 returns current_version; LessonAccessGrantV1 returns version_id and revision but no hash/content; and the decision request/response do not carry the reviewed version/hash. The detail route reads current_version, not an arbitrary historical version.

Persistence evidence: infrastructure/lesson_library/tables.py:144–168 stores library versions, content/hash, and a unique lesson/version number; lines 184–225 store access-grant version_id but no hash column. Service.py:275–332 and 340–374 creates version rows and moves the current pointer. Decision service.py:1193–1220 checks grant revision/state and updates review_state on the version_id stored by the grant. It does not compare that ID with the lesson's current_version_id or verify a hash. Thus the inspected static BE path does not explicitly reject a superseded pending grant; it can proceed against the grant's historical version if the source preconditions pass. This is a source-path description only, not a runtime/concurrency guarantee. No database trigger/constraint preventing content/hash mutation was established; DB-level immutability is NOT VERIFIED.

Pagination: GET access-grants at lesson_library.py:442 declares limit default 50 and maximum 100, with cursor at line 443; service.py:1165–1173 uses a stable created_at/access_grant_id descending order and next_cursor. Rev60 §21.1 line 1613 requires default 25 and max 100. The default is a contract gap even though the maximum matches. FE API accepts cursor but no explicit limit option (backendApi.tsx:446–447); ManagerScreens.tsx:98–105 and 140–153 loads the first page and follows nextCursor. Proposed contract: BE default 25/max 100, retain stable cursor order; FE may omit limit or expose it only if the reviewed UX needs it. No code change is authorized here.

Replay/revision/errors: service.py:491–507 maps same key/different payload to 409 IDEMPOTENCY_KEY_REUSED, while Rev60 §9.8 line 835 names 400 INVALID_IDEMPOTENCY_KEY; Rev60 §21.4 line 1670 requires same-key/same-payload replay to return the original result. Router If-Match helper at routers/lesson_library.py:83–99 returns 428 when absent and 422 when malformed; service.py:597–599 maps stale revision to 409 STALE_REVISION. These are current source semantics; the cited SRS §21.4 text does not define an access-grant-specific revision protocol. Lesson Library HTTPException, request-validation, and unhandled-exception branches at app.py:467–491, 612–622, and 725–740 statically return `code`, `message`, `request_id` and `X-Request-ID`; compared with Rev60 §9.8 lines 824–839, the body uses `request_id` where the SRS names `correlation_id`, and omits required `retryable` (optional `retry_after_seconds` and `field_errors` need not appear). This is a source-visible response-shape mismatch, not a runtime observation. The source uses grant row-lock/revision checks but no race guarantee is claimed. No runtime success/failure is claimed.

Parent access is distinct: GET /api/lesson-library/v1/me/lessons/{lesson_id} appears at lesson_library.py:695–705, and service.py:2038–2055 resolves version/hash through Parent access. This is not evidence that Manager has equivalent authorization or contract.

## Composition, OpenAPI, and tests — evidence levels kept separate

- Static route inclusion: backend/src/sketch2life/interfaces/http/router_composition.py:60–77 includes lesson_library.router in combined composition; app.py:256 and 1004–1011 show composition selection. This proves code composition only.
- Static catalog: backend/src/sketch2life/interfaces/http/openapi_contract.py has operation entries near lines 9509, 9575, 9667, 9822, and 10192 for grant list/decision, lesson list/detail, and version creation. It has no exact Manager version-read operation in the inspected catalog.
- Public projection: backend/src/sketch2life/interfaces/http/openapi_srs_v22.py:8–92 includes list/detail/version-create operations but omits Manager grant list/decision. This is a legacy projection, not the full OpenAPI output.
- Tests: backend/tests/integration/lesson_library/test_lesson_library_api.py contains integration test source for the existing routes. It was not run and is not proof of runtime behavior.
- No generated full OpenAPI document, gateway mapping, deployed environment, database state, or runtime was inspected.

## FE caller and guard evidence

- FE worktree pinned above. ManagerScreens.tsx:98–105 calls the grant list; lines 116–138 calls current lesson detail. The guard at lines 69–72 compares selected grant.version_id with lesson.current_version.version_id and requires content. On mismatch, lines 247–248 show a warning and no review content; if content is missing, canReview is false. Decision controls are disabled while canReview is false at lines 256–265. When IDs match and content exists, the FE can enable a decision; this is not a content-hash check and is not a BE stale/hash check.
- FE API at apps/web/src/shared/api/backendApi.tsx:446–453 calls GET /api/lesson-library/v1/organizations/{organization_id}/access-grants with cursor/filter query parameters and POST /api/lesson-library/v1/organizations/{organization_id}/access-grants/{access_grant_id}/decision with If-Match and Idempotency-Key. The accessGrants options type has no limit. X-Request-ID in the shared client is correlation, not idempotency.
- Integration gate: do not rely on the current ID-only guard to establish exact-version/hash review. Until the exact-version contract and separately approved verification pass, Manager approve/request-changes must remain unavailable for integration. No FE change is authorized here.

## Proposed target and unresolved decisions

SRS REQUIREMENT: Rev60 requires School Manager approval before Teacher content becomes PUBLIC within the school scope, requires version/hash pins for the specified occurrence/plan/StoryRun references, and prohibits silently retargeting those refs. It does not directly require an exact-version Manager review API or grant hash.

TECHNICAL PROPOSAL: MGR-6 should bind the Manager's review and decision to the grant's exact version and verifiable structured content hash, with no current/latest fallback. A future decision contract must choose how it proves which content was reviewed: expected version_id/hash preconditions or a server-verifiable review receipt are candidates; current request DTO has neither. Any submitted precondition must be compared with authoritative grant/version data. The endpoint path, response allowlist, stale/superseded pending-grant outcome, exact revision/error mapping, idempotency receipt details, and database immutability enforcement remain OPEN. Do not add a public error code or schema field by inference.

### Version/hash binding options — OPEN / PROPOSED

| Option | Candidate binding | Trade-off; not selected |
|---|---|---|
| Snapshot hash on grant | Add and persist the submitted version's structured_content_hash with version_id; verify both at create, read, and decision. | Explicit grant identity and review receipt; requires DTO/OpenAPI/storage changes and consistency validation. |
| Resolve from immutable version row | Keep version_id on grant; fetch content/hash from that exact version row and enforce immutability at the approved application/persistence boundary. | Avoids duplicate hash state; depends on durable immutability and stable hash canonicalization, neither established at DB level now. |

Neither option is selected. Any future contract must specify which mechanism is authoritative, how the decision is bound to the exact version/hash the Manager reviewed, and how the BE revalidates it at decision time; FE-supplied values alone are not authoritative.

Suggested minimum response for contract review (proposal, not selected schema): grant ID/state/revision; organization and lesson IDs; exact version ID/number/hash; structured lesson content required for review; approved attribution/provenance; and no child media. The decision command must bind the decision to the same version/hash that was displayed and revalidate authorization, scope, state and revision at write time.

## Planning-only likely file set

BE: backend/src/sketch2life/interfaces/http/routers/lesson_library.py; backend/src/sketch2life/contracts/schemas/lesson_library.py; backend/src/sketch2life/infrastructure/lesson_library/service.py; infrastructure/lesson_library/tables.py only if persistence integrity changes are approved; interfaces/http/openapi_contract.py; openapi_srs_v22.py only if projection scope is approved; backend/tests/integration/lesson_library/test_lesson_library_api.py.

FE: apps/web/src/shared/api/backendApi.tsx; apps/web/src/modules/school-manager/pages/ManagerScreens.tsx; apps/web/src/modules/school-manager/be1/App.tsx only if route state changes; related school-manager tests. Planning evidence only; no files outside this note were changed.

## Source pins captured during authoring

| Worktree-relative source | Bytes | SHA-256 |
|---|---:|---|
| BE backend/src/sketch2life/interfaces/http/routers/lesson_library.py | 28,784 | DB70B5DC5B21BEA706A3AF961330D5A425A5846D671C3741DD849A1196F2884A |
| BE backend/src/sketch2life/contracts/schemas/lesson_library.py | 12,465 | EBF3CBC5B57488E4942EDC02B57DA3E66947549AF0164F7693CC55C989AEB77D |
| BE backend/src/sketch2life/infrastructure/lesson_library/service.py | 91,446 | 68EDDED6CC374EE954FF98C2F558883E5B6887EA721638ACD64D166825D1D4D6 |
| BE backend/src/sketch2life/infrastructure/lesson_library/tables.py | 16,009 | FE43AD061B69D4D1B8191AB52705A72C59BAA42605AB9167F4AADF3EF74EFDAF |
| BE backend/src/sketch2life/interfaces/http/router_composition.py | 3,743 | 2CC4EA02A69E115C684B4383A1CA9BB63A4AAAB4B0E6C848852968C5E9599463 |
| BE backend/src/sketch2life/interfaces/http/app.py | 73,905 | A25495D8F61590926B90F08BE3044B588E1C81F55C33C0377C5ECEB73271C8DC |
| BE backend/src/sketch2life/interfaces/http/openapi_contract.py | 1,377,229 | 175FA3B3BDE475BA32743569DD276924CD20E32F8D29AA65F6C7AB68B2C9E9AE |
| BE backend/src/sketch2life/interfaces/http/openapi_srs_v22.py | 11,122 | 29A0288E9F48EDD60F5E49A28360189BA68084B21A6A0FA2EAB2E5E0D3B6BCB3 |
| FE apps/web/src/shared/api/backendApi.tsx | 25,951 | 4047674F9434E489205995E0BDA44E2654482AA5DBCF953399B83120225C986F |
| FE apps/web/src/modules/school-manager/pages/ManagerScreens.tsx | 16,775 | D7C71D0F634D6429B1BB021CE79A3060B107A3ADC96A2CC6580BF3011433A985 |
| FE apps/web/src/modules/school-manager/be1/App.tsx | 7,740 | 4E9C1A93789919D28C7AF7DAB0265CB87947614A0F5B941B313C6C79985F2FFD |
| BE backend/tests/integration/lesson_library/test_lesson_library_api.py | 43,954 | 7C9F2777BE238367582A06E795378EB654911E36B7019EBDE93E2C5C61A707CB |

## Required future verification

After approval, verify generated full OpenAPI separately from the public projection; verify access-grant cursor order, default page size 25 and maximum 100; test exact current and superseded versions, hash binding/tampering, cross-organization access, role denial, author self-review, stale revision, state transitions, replay and key mismatch, and §9.8 response shape; verify FE never displays current/latest content as the grant version and disables decision when exact data cannot be loaded. Tests/runtime were not run for this draft.
