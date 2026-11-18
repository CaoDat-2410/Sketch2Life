# MGR-4 Parent Group Invitation and Membership Lifecycle — Source Evidence, Draft 1

**Date:** 2026-11-17 (Asia/Saigon)  
**Purpose:** read-only source reconciliation supporting the MGR-4 contract plan. This is evidence, not a runtime report, owner-policy decision, approval, or implementation authorization.

## 1. Baseline identity and pre-existing state

| Worktree | Branch / HEAD | Preflight status | Result |
|---|---|---|---|
| BE | `D:\GitHub\Sketch2Life\.worktrees\manager-api` — `feature/feat066-manager-api-contracts` / `1c9148e88600a101887e477541c4c4893ba1c7df` | Pre-existing modified `CONTEXT.md`, `DECISIONS.md`, `status/STATUS.md`; pre-existing untracked MGR-1 through MGR-3 records and roadmap. No audited BE/FE source file was modified. Staged path count: 0. | Expected identity matched; existing work preserved. |
| FE | `D:\GitHub\Sketch2Life\.worktrees\ui` — `codex/fe-ui-web-remediation` / `297a28b1f406ab80e25d6e0aa5577e4b6f505ee2` | Clean; staged path count: 0. | Expected consumer baseline matched. |

The MGR-4 plan, evidence note, and cold-review report paths were absent before writing. No branch or worktree state was changed. All observations below are static. No tests, builds, validators, OpenAPI generation, backend/runtime, database, Docker, network/provider, or Modal commands were run.

## 2. Decision provenance

- Working-tree `features/FEAT-066-fe-ui-srs-full-review/DECISIONS.md`: 38,951 bytes; SHA-256 `A99E5AC92E747E199E350F842C6E7444942FFDD1610205B3F07AB79F60E5F61C`. D-066-62 is at lines 260–268; D-066-63 at lines 270–280.
- Pinned-HEAD `DECISIONS.md` blob: `ca0143cfd432bb70bfdf79e988228ef2066d9b50`; that content contains neither D-066-62 nor D-066-63. HEAD blob is 34,226 bytes; SHA-256 `6BA0A8D21A2A78D03A121B1851F0B76CAFAB914309B3E00C7DF5D1E0A5371172`.
- `evidence/notes/MGR_1_OWNER_DISPOSITION_20261117.md`, lines 14–18, records the owner's MGR-1 choices and supports D-066-62: do not enable Manager-to-Parent discovery/invitation before a separately approved verified tenant-scoped contract; Parent remains the actor for Parent-profile consent/grants; Teacher candidate policy is separate.
- Accordingly, D-066-62 is an **OWNER DECISION recorded in the current working tree, not present at pinned HEAD**. It is not presented as committed baseline. D-066-63 is MGR-2-only and is not used for MGR-4. MGR-3 R2's `ACCEPT WITH NOTES` is review evidence, not implementation approval.

## 3. Governing requirements reviewed

Repository authority `docs/context/SRS_AUTHORITY.md` (4,054 bytes; SHA-256 `032223EDDD46D251DE052C54BFF16AB1D4D794F865A457272507D893E3C1521F`) points to canonical FEAT-063 v2.7-draft Rev60 (553,948 bytes; SHA-256 `70DA43A35106E8C02B4BB8FCCB9628C0376C9E7EA6CFC51909ACB569703B218B`). Rev60 is unsigned and is the only product SRS used.

| SRS reference | Direct evidence and treatment |
|---|---|
| §§3/4 lines 208–217; §31.3 lines 2547–2553 | School Manager is scoped to one organization; Parent groups are tenant-bound. Parent/Teacher roles do not cross tenant. Server checks current organization and resource scope. |
| §31.3 lines 2555, 2559–2562; AC-49 line 2691 | SRS profile-sharing invitation/grant is Parent-to-named-Teacher/school; Parent owns consent and may revoke. It is separate from Manager-to-Parent group membership. Group membership is not profile consent or child-media access. |
| §9.6 lines 766–791 | Proposed resource groups only, not final OpenAPI; no Parent candidate or group-membership route is specified. |
| §9.7 lines 793–818 | BE1 owns authenticated adult/Parent/Teacher scope and org/class/Teacher roster facts. No complete Parent candidate lookup or Parent-group membership API/owner contract is specified. |
| §9.8 lines 820–840 | Safe envelope: `code`, `message`, `correlation_id`, `retryable`, optional `retry_after_seconds` / `field_errors`; 403 `ACTION_NOT_ALLOWED` only for known in-scope action denial; same-shape 404 `RESOURCE_NOT_FOUND` for absent/out-of-scope; HTTP 400 `INVALID_IDEMPOTENCY_KEY`. |
| §21.1 lines 1605–1614 | Versioned `/v1`; server verifies Bearer token and scope; response correlation ID; opaque deterministic cursors default 25/max 100; versioned resource/command response. |
| §21.4 lines 1668–1672 | State commands use principal/operation/target-scoped idempotency; same key/payload returns original result; different payload is `INVALID_IDEMPOTENCY_KEY`. Specific expected revisions are named there for other resources, not Parent-group membership; exact membership `If-Match`/ETag representation remains open. |
| FR-PL-06, FR-PL-23, BR-49, BR-58 lines 2620, 2637, 2647, 2656 | Parent-group audiences and membership/grants are tenant-bound and revocable. These do not define candidate fields, complete invite lifecycle/API, or whether a Parent may self-leave a group. |
| §31.10(14), (17), lines 2726, 2729 | Role/permission resolver and audit metadata/retention remain owner-open. No resolver or retention policy was invented. |

## 4. BE source pins and observations

The following files were present and unchanged in the BE worktree at preflight. Hashes are SHA-256.

| BE source | Bytes | SHA-256 | Relevant lines / observation |
|---|---:|---|---|
| `backend/src/sketch2life/interfaces/http/routers/lesson_library.py` | 28,784 | `DB70B5DC5B21BEA706A3AF961330D5A425A5846D671C3741DD849A1196F2884A` | 53 router prefix; 83–100 strong revision/ETag; 111–130 actor checks; 506–624 group create/list, invite, Parent-self pending list/accept, revoke. Revoke tries Manager authorization at 611–617 but does not call `_parent_actor`. |
| `backend/src/sketch2life/interfaces/http/routers/be1_common.py` | 16,142 | `74AA865DFB2C925244F1CA446BFA054F48A42B0645E39FF0C144657E5510B3CC` | 83–138 `require_assignment`: reads AdultIdentity and active organization assignments; returns 403 `ACCOUNT_SCOPE_UNAVAILABLE` for missing/inactive identity, unsupported role, or no active assignment before service lookup. |
| `backend/src/sketch2life/interfaces/http/be1_runtime.py` | 16,807 | `62691ECC532F4544DBE4ABE0D277A67922CAA505DAF4D4803D1754039D754C85` | 169–182 `get_verified_adult` verifies Bearer credentials into `VerifiedPrincipal`; it does not establish current DB Parent role/state or compare issuer to stored Parent identity. |
| `backend/src/sketch2life/contracts/schemas/lesson_library.py` | 12,465 | `EBF3CBC5B57488E4942EDC02B57DA3E66947549AF0164F7693CC55C989AEB77D` | 110–118 create/invite requests; 245–275 group, membership and page DTOs. `parent_principal_ref` is only syntactically opaque, not recipient verification. |
| `backend/src/sketch2life/infrastructure/lesson_library/service.py` | 91,446 | `68EDDED6CC374EE954FF98C2F558883E5B6887EA721638ACD64D166825D1D4D6` | 465–600 receipt/replay, mismatch, audit/commit/revision helpers; 68 source TTL; 1329–1505 group create/list/invite/outbox/group scope; 1519–1649 Parent pending list/accept/revoke. |
| `backend/src/sketch2life/infrastructure/lesson_library/receipt_compat.py` | 6,169 | `BC22DC7982D601397997FECA223A61A1392B4392EE24D7F21B9F756ED1F60A47` | 81–166 receipt validation; current versioned receipt returned as stored; legacy receipt without revision may reconstruct revision from current membership row. |
| `backend/src/sketch2life/infrastructure/lesson_library/tables.py` | 16,009 | `FE43AD061B69D4D1B8191AB52705A72C59BAA42605AB9167F4AADF3EF74EFDAF` | 14–56 group/member metadata, unique group+principal, states and revision; 293–304 command receipts. Metadata alone does not prove migration or runtime persistence. |
| `backend/src/sketch2life/interfaces/http/router_composition.py` | 3,743 | `2CC4EA02A69E115C684B4383A1CA9BB63A4AAAB4B0E6C848852968C5E9599463` | 60–75 combined `mount_all_routers` includes Lesson Library router. |
| `backend/src/sketch2life/interfaces/http/app.py` | 73,905 | `A25495D8F61590926B90F08BE3044B588E1C81F55C33C0377C5ECEB73271C8DC` | `create_app` defaults combined at 256; combined mounts at 1004–1005; classroom/demo choose different composition at 1008–1011; request context 317–345; Lesson Library error handler 467–490 emits `code`, `message`, `request_id` and `X-Request-ID`. Static evidence only. |
| `backend/src/sketch2life/interfaces/http/openapi_contract.py` | 1,377,229 | `175FA3B3BDE475BA32743569DD276924CD20E32F8D29AA65F6C7AB68B2C9E9AE` | Static full catalog entries: Parent invitation list/accept around 9430/9460; group list/create around 10252/10303; invite around 10358; revoke around 10415. No candidate or Manager membership list/detail path found. Actual emitted OpenAPI not generated. |
| `backend/src/sketch2life/interfaces/http/openapi_srs_v22.py` | 11,122 | `29A0288E9F48EDD60F5E49A28360189BA68084B21A6A0FA2EAB2E5E0D3B6BCB3` | No Parent-group path match in the Rev22 projection source. Projection source is separate from catalog and generated output. |
| `backend/tests/integration/lesson_library/test_lesson_library_api.py` | 43,954 | `7C9F2777BE238367582A06E795378EB654911E36B7019EBDE93E2C5C61A707CB` | 827–895 source scenario creates/lists group, invites synthetic Parent, reads/accepts, Manager-revokes with `If-Match`; asserts revision 3/ETag `"3"` and later lesson list lacks shared lesson. 950–1054 source test covers legacy accept receipt and same-key/different-payload 409. Not run. |
| `backend/tests/contract/test_app_composition.py` | 13,699 | `90006674F68D0B0E9843DD848EE9A652A63B299BFBA0FDC6A6F1F2DF7C454504` | 95–164 expected mounted method/path set includes group list/create, invite, Parent-self list/accept, revoke. Test source only; not run. |

### BE route-level facts

- Router prefix is `/api/lesson-library/v1`. `create_app` defaults to combined; combined source includes the router, while classroom/demo source profiles do not. No app factory was executed.
- Manager authorization uses `require_assignment(... roles={"school_admin"})`. For group create/list/invite, `_manager` runs before service/resource lookup (`lesson_library.py:519, 535, 556`); `require_assignment` returns HTTP 403 `ACCOUNT_SCOPE_UNAVAILABLE` when identity is missing/inactive, account role unsupported, or no active assignment exists (`be1_common.py:83–114`). An out-of-scope organization request can therefore receive 403 before group lookup. This is a **CURRENT SOURCE GAP** against Rev60 §9.8 uniform 404 for out-of-scope resources. The target must not reveal whether the resource exists; the safe guard/lookup/error-mapping design remains OPEN.
- `get_verified_adult` verifies Bearer credentials into a `VerifiedPrincipal` (`be1_runtime.py:169–182`), but revoke only tries `_manager`, catches any 403, and passes the verified subject onward (`lesson_library.py:601–622`). The service scopes the group and compares `parent_principal_ref` to the subject only (`service.py:1605–1611`). Revoke does not call `_parent_actor`, which checks active Parent role/state and stored identity issuer (`lesson_library.py:119–130`). This source path does not prove the caller is a currently active Parent. Whether Parent self-leave is allowed is **OPEN-OWNER / NOT VERIFIED**.
- Invite service scopes group lookup to the path organization, rejects non-active groups, checks only whether the target principal has an active organization assignment (staff exclusion), then creates/reuses membership. It does not verify that target Parent identity exists, is active, has Parent role, or is linked to the organization. No candidate read source was found.
- Group and Parent invitation lists use default `limit=50`, max 100 and cursor order. Rev60 §21.1 default is 25. Parent-self list returns only `INVITED` rows whose expiry is in the future.
- Invite adds pending outbox event `lesson.parent_group_invited.v1` and allow audit entry in the command path. Search of audited `backend/src` found only producer references; no delivery consumer was identified. Outbox insert is not delivery evidence.
- `_idempotent` stores receipts for group create, invite and accept. Same-key/different-payload currently maps to HTTP 409 `IDEMPOTENCY_KEY_REUSED`, not SRS HTTP 400 `INVALID_IDEMPOTENCY_KEY`. Revoke has no Idempotency-Key header/receipt wrapper. Current versioned receipts are returned as stored; compatibility logic can reconstruct revision for legacy responses. No runtime replay/concurrency claim is made.
- Revoke source takes `FOR UPDATE`, checks expected revision before already-revoked handling, changes a non-revoked current state to revoked, increments revision, audits allow, commits, then returns membership/ETag. Retry using the pre-revoke If-Match after success is stale. DB isolation, conflict behavior, cross-writer guarantees, and runtime persistence are **NOT VERIFIED**. Stored principal-reference equality alone does not verify current Parent account state, role, or issuer.
- Current Lesson Library error handler emits `{code, message, request_id}` and `X-Request-ID` (`app.py:467–489`); Rev60 requires `correlation_id`, `retryable`, and optional standard fields. The guard 403 `ACCOUNT_SCOPE_UNAVAILABLE` is preserved. For an out-of-scope organization, this pre-lookup 403 is a source gap against Rev60 §9.8: target behavior is same-shape 404 `RESOURCE_NOT_FOUND` for nonexistent/out-of-scope resources, no existence leak, and 403 `ACTION_NOT_ALLOWED` only after known in-scope denial. Safe guard/lookup/error mapping is **OPEN / NOT VERIFIED**.

## 5. FE source pins and observations

The pinned FE worktree was clean at inspection. These files were unchanged; hashes are SHA-256.

| FE source | Bytes | SHA-256 | Relevant lines / observation |
|---|---:|---|---|
| `apps/web/src/modules/school-manager/be1/services/managerBusinessService.ts` | 2,409 | `2FDE883554E5A1D7E02B74ED80A7B1B1D145A92315A2EA391A2E7ADD22414B8D` | 24–37 group/page types; 39–43 organization path; 64–81 list/create methods. No candidate, invite, membership-read, or revoke client. |
| `apps/web/src/modules/school-manager/be1/pages/ParentGroupsPage.tsx` | 9,473 | `E31EF487E32BFFE9892158A20172D7F6331144233AB54207BAB1E0CEE7BDA67A` | 23–103 list/create; 143–168 create form available when non-empty/not submitting; 228–238 invitation/member revoke are “Chưa khả dụng / Chờ API.” |
| `apps/web/src/modules/school-manager/be1/App.tsx` | 7,740 | `4E9C1A93789919D28C7AF7DAB0265CB87947614A0F5B941B313C6C79985F2FFD` | 130–142 routes `/school/parent-groups` to page behind Manager access gate. |
| `apps/web/src/modules/school-manager/be1/services/be1Client.ts` | 3,018 | `D262D3511DE7C0C98B989B4BCABD3D2CF9DF4F0F7B59D720B1DDB5BC9ACCAC26` | 15–18 organization environment setting; 48–73 `adminApiRequest` adds `/api`, Bearer, `X-Request-ID`. Static URL construction matches current BE route prefix; configured host/proxy/runtime not verified. |
| `apps/web/src/modules/school-manager/be1/__tests__/managerBusinessService.test.ts` | 2,226 | `639244AA3DCF76A0910930D8EB022E95CB5AB5C32B93E8A81CC00D07F911AEF1` | 43–60 source tests for group list/create URLs and idempotency header. Not run. |
| `apps/web/src/modules/school-manager/be1/__tests__/managerBusinessPages.test.tsx` | 4,761 | `F868ED273926A56831D0C3EF8DB260FB0DDBEFE9DA3DDF0E24AC1A736D2A12C3` | Source tests for explicit group-create submit and available page. Not run. |
| `apps/web/src/shared/navigation/WebAppShell.tsx` | 14,523 | `02644E875B94DE7C60698C29A522802859C25B61D1C524043B80593B7BAAE38E` | Line 80 Parent Groups navigation item is marked available. |

Generic FE methods named `parentInvitations` / `answerParentInvitation` target `/api/lesson-library/v1/me/lesson-invitations` and accept/decline. Those are Lesson access-grant invitations, not Parent-group membership. No Manager Parent-group invite/read/revoke caller was found. FE test presence is not execution or runtime evidence.

## 6. Evidence-level ledger

| Level | Result |
|---|---|
| BE route declaration | Group create/list, Manager invite, Parent-self invitation list/accept, and membership DELETE are in router source. Parent candidate read and Manager membership list/detail are absent from audited files. |
| Static app composition | Lesson Library router included by combined/default app source; omitted from classroom/demo source profiles. No profile executed. |
| Full static OpenAPI catalog | Existing group, invite, Parent-self list/accept, and revoke paths listed; candidate and Manager membership-read paths absent. Catalog source is not generated output. |
| Public SRS projection source | Parent-group paths not found in Rev22 projection. Separate from catalog and not current SRS authority. |
| FE adapter/page | Group list/create are connected and called. Invite, Manager membership read and revoke have no client/caller and are visibly unavailable. |
| BE/FE test source | Composition/API lifecycle and FE list/create test sources exist. None executed. |
| Generated OpenAPI | **NOT VERIFIED**; no generation/emitted document inspection. |
| Test execution | **NOT RUN** by instruction. |
| Runtime/app reachability | **NOT VERIFIED**; no server, endpoint, database, proxy, or live environment accessed. |
| Invitation delivery | Outbox producer source exists; consumer and runtime delivery **NOT VERIFIED**. |

## 7. Review limits and artifact state

FEAT-066 records and tests are implementation evidence only. Route declarations, static composition, catalog entries, and test-file presence do not prove runtime behavior. No Parent/child business data, identity secret, provider credential, or live service was accessed.

No owner policy, route, field list, table, schema, error code, concurrency guarantee, runtime behavior, or implementation approval was created by recording these observations. No source, FE, SRS, authority, decision, approval, or status file was edited. The plan and this note remain **DRAFT / NOT APPROVED / NOT LAUNCHED**. Manager invitation and membership controls remain unavailable pending the approved BE contract and separately approved verification.

## 8. Planning-input pins and disposition status

| Planning input | Bytes | SHA-256 | Review use/status |
|---|---:|---|---|
| Root `AGENTS.md` | 3,406 | `89ACC84AA4D838730205A03917B40DEB37E9622AAF7092E982476D934EC29A61` | Read before task; repository governance. |
| Root `.codex/sketch2life-harness.md` | 2,178 | `0364DD280483D7AB56EAAF7F0B2CEF56A86D627393CA9996FC88A14E3318E12F` | Read; plan/evidence language and review workflow followed. |
| `docs/context/PROJECT_CONTEXT.md` | 81,664 | `EDEC7010C6B351E6DC6E9145941F479E5C39DF4770060625FD9BBAF719AD04BF` | Read as project context. |
| `docs/context/SOURCE_REGISTER.md` | 113,526 | `D09F5849F4A3829EC4241FF1A840319225909E0EECA93A9BF6964625C4E987A0` | Read as source register. |
| MGR roadmap `plan/PLAN_MANAGER_API_GAP_CLOSURE_DRAFT1_20261117.md` | 18,974 | `5E7CDB0AF03A27FF0DABFE949E41F7230D1BE7453EF56274E8CED388F6F196ED` | MGR-4 depends on MGR-2/3/5/6; membership read/revision is contract work; invite and revoke actions stay unwired pending contract. |
| MGR-1 owner disposition `evidence/notes/MGR_1_OWNER_DISPOSITION_20261117.md` | 4,016 | `B32D4CBC47811960A5DE2B2F1A3CAA9C84B64F8F9DC7F79CD0CD68F92F37883A` | Lines 14–18 support current-working-tree D-066-62 provenance and policy. |
| MGR-2 plan | 22,177 | `900EA080B8E3E3C59FCF338D2249E1967FBEAEE87FF072422C1C534DB72A5A8E` | Contract planning source; not implementation authorization. |
| MGR-2 evidence note | 12,644 | `EEA5343F1FA42A8EE1E06B97329A4C9D814144E4FC8E0EE56F37E6CEC3CAE0C5` | Source/SRS evidence; MGR-2 uses its task-specific SRS input only, not adopted for MGR-4. |
| MGR-2 owner cold-review disposition | 3,808 | `7F6BD4C2E9A9562904ABE55C4C26E7DE53CAD0077F88951E203B3DAE08DF2C47` | Records MGR-2 `ACCEPT WITH NOTES`, zero actionable findings; explicitly no implementation approval. |
| MGR-3 plan | 30,329 | `D3B591600ED23597ADA10A087B644C00766DF8F8416DE9F540ECB867B3D9CBE7` | Separate Teacher assignment contract; D-066-62 provenance is working-tree-only. |
| MGR-3 evidence note | 20,056 | `AE4C66C6FE1642EE12597B44C8EC00F28CEBC99FF590C22B0C84067A868FCFFB` | Read as MGR-3 source/provenance evidence. |
| MGR-3 R2 cold review | 4,121 | `96211C3D973A81923316EF9F20894A31878F2FB3B9C82A170B5D3919969232B8` | `ACCEPT WITH NOTES`; P3 is locator-only and confers no implementation approval. |

MGR-5 and MGR-6 have not been completed in the inspected roadmap records; their required interfaces remain OPEN. MGR-2/MGR-3 review records are planning evidence only. MGR-7 still requires an exact allowlist and separate approval before implementation.

The worktree did not contain a separate .codex/sketch2life-harness.md; the repository-root harness under D:\GitHub\Sketch2Life\.codex\sketch2life-harness.md was read and followed.

