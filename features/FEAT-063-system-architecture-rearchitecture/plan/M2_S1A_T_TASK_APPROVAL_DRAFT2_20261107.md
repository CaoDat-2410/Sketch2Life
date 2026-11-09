# M2 S1a-T Task Approval — Draft 2

**Status: DRAFT — NOT APPROVED, NOT LAUNCHED.** Bản này là bản kế hoạch đã tiếp thu review Draft 1; không phải Task Approval, không mở S1a-T, không cấp quyền sửa code, chạy test, ghi DB hay chạy lệnh.

**Owner decision record:** D-156 ghi các hướng R1–R8; đây vẫn là direction, không phải approval thực thi. Owner field, command ceiling và allowlist cuối còn chờ owner điền/duyệt.

**Independent review of Draft 1:** NEEDS_REVISION, 0 P1 / 3 P2 / 14 P3; chat-only session local_2b185df6-3608-47a3-8d9a-45cc09a0c43a. Báo cáo review chi tiết được đọc tại phiên soạn. Draft 2 chưa được review độc lập.

## Thay đổi từ Draft 1 sang Draft 2

| Phần Draft 1 | Thay đổi ở Draft 2 | Cơ sở |
|---|---|---|
| §1.1 và trạng thái review | Ghim DECISIONS có D-156; cập nhật review Draft 1 thành 3 P2/14 P3; phân biệt direction với approval | D-156; hash hiện tại |
| §2.1–2.2 và §5 | Chốt quy tắc đếm theo class_id/teacher/active, assignment class-level cho profile route, denial 403 SCOPE_DENIED chỉ trên M2 routes, không sửa authorization toàn cục; thay/gỡ Teacher thành debt | D-156 R2–R3 |
| §2.2, §3.1, §5 | Thêm synthetic prefix/name/age-source, consent refs NULL, local/test + feature gate; cập nhật request schema/test ảnh hưởng; bỏ khẳng định route được phép dùng REAL | D-155 Q2/F-6; D-156 R8 |
| §3.1–3.2 | Dùng biến dedicated để cấu hình app engine thật; ghi rõ fixture BE1 cũ không dùng được nguyên trạng; sửa đường dẫn mypy và cache; loại test graph cũ khỏi verdict T | Review N-01/N-03/N-06/N-07/N-09 |
| §2, §6, §7 | Nêu rõ test/app/API files, tài liệu Bruno là drift read-only; cập nhật OpenAPI count theo quyết định legacy route; không claim assignment revision response là đạt | Review N-08/N-09/N-12/N-13/N-14 |
| §7–8 | Đo hàng test theo synthetic prefix + run-id, disposition PARTIAL/NOT RUN, bảng mapping đủ P2-01..13, P3-01..12 và N-01..17 | Review Draft 1; D-151/D-155/D-156 |
| §9–10 | Ghi rõ cổng, debt và owner fields còn mở; không tự chọn disposition route legacy, error body hay cách đưa secret vào process | D-156; giới hạn Draft |

## 1. Baseline, nguồn và provenance

### 1.1. Checkout, hồ sơ và pins

| Mục | Giá trị | Ý nghĩa |
|---|---|---|
| Branch / HEAD | feature/feat063-be-foundation / dd70685eae58aaaefea3e567f5c23d09345a8513 | Baseline của bản nháp; phải ghim lại trước approval |
| Index | Rỗng | Không có staged path |
| S1a-T Draft 1 | SHA-256 160511C0FF3643D7C53BDDB1AFBE974B38BF98DADBE4C8160B18943A676B7769 | Đối tượng review, không sửa |
| S1a-P Draft 1 | SHA-256 2875C0A5F25657BDCE2645CF2733FA0B5E52E4EE9EF9544C19C6AAA697400C58 | Bản pha kế tiếp; không sửa |
| S1a Draft 1 ban đầu | SHA-256 55A2466D01487D239595BF4FE2E95973A9B57619C629835C8C6358A403CA3625 | Nguồn lịch sử, không sửa |
| M2 Draft 10 | SHA-256 7539D642FFD95A9A21C99A0C17C5095FF1443E19538017A92789F631D633E2B1 | Planning baseline D-151 |
| M2 Draft 11 | SHA-256 6F3EFD72D3A70209B06771AC437998AE241842ABD4F20D11019E6B1166B48A68 | DRAFT, chưa mở pha |
| SRS v2.3-draft | artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md; SHA-256 DCBF9786FF8983E34F2D3B4EBAB76301D0C52A6C9DE72CD08D0816BBD0D983FC | Contract authority được giữ; chưa ký |
| DTR v2.3 | artifacts/DATA_TABLE_REGISTER.md; working SHA-256 3E793BB2C62C9E6C50780DE636EDDE442D382C62B4643552F2298AF374171E22; LF blob SHA-256 201D381C5025BF6BB5EA2415E916835EB291AFE96CD948D76C0DC5604C28D1B2 | Ghi cả hai hash; khác line ending không đổi pin |
| DECISIONS.md | SHA-256 73E7E11F7F3B75F966E9A844D573129B66AE772D4821132F09C0242592751971; có D-156 | Direction đã ghi; không phải approval |
| TASK_APPROVAL.md | SHA-256 FEEE42E506F94352A8161EFE0B4B94870967072BEDF233285BFDF882352A3DF7 | S0-owner-run đóng; chưa có S1a-T approval |
| S0-doc evidence | SHA-256 1BB71300A6A22487311A8D39EECB0EB1CE2664CB471EC2DAF45DA8DE2E244001 | Đóng ở phạm vi tài liệu theo D-150 |
| S0-owner-run inventory | .claude/handoff/logs/M2_S0_OWNER_RUN_20261107/inventory.json; SHA-256 E4529F541002D840C3F2E1D25F24D00E7B92A65720E3036EB59BA71FD04DB64F | Artifact owner-run, không phải kết nối DB của phiên soạn |

Các pin đã được tính lại trong phiên soạn: ba Draft 1, Draft 10/11, SRS working tree và raw Git blob, DTR working tree, inventory, DECISIONS và TASK_APPROVAL. 17 pin source/test trong §1.3 đều khớp. Không đọc .env.

### 1.2. DB, provenance và thứ tự

- D-154 ghi một inventory owner-run chỉ đọc trên database sketch2life, PostgreSQL 17.11 native localhost:5433: 117 bảng, 82 hàng tổng, 9 hàng public.alembic_version. K3 FAIL; K4 source comparison, K5 synthetic-only proof cho 15 hàng baseline và K7 mypy là NOT RUN. Đây là trạng thái lượt S0-owner-run, không phải quyền dùng database chính.
- Owner báo database task-owned sketch2life_m2_s1a được tạo từ schema-only dump SHA-256 E02F2D6E43053FBBACC388002AC9A66FABC73A9AE51399704FB65179BD1BE2E8, PostgreSQL 17 native localhost:5433, user postgres, 117 bảng, 0 hàng, alembic_version trống. Phiên soạn không kết nối, không xác minh dump/database.
- Theo D-156 R1, S1a-T chạy trước S1a-P trên cùng database. S1a-P không chạy song song. Pha T phải giữ lại mọi hàng test có nhãn; Pha P chụp inventory và mypy baseline mới sau khi T hoàn tất, không giả định database của P còn 117 bảng/0 hàng.
- Không ghi, migrate, reset, drop, truncate hay cleanup database sketch2life. Không dùng database tổng cho test ghi. S1a-T chỉ được xem xét trên sketch2life_m2_s1a.
- D-152 xác nhận target là PostgreSQL native Windows, không phải Docker. D-155 Q8/D-156 không mở quyền migrate; mọi thao tác cần Task Approval riêng. OWNER_MODAL_CALL_APPROVED=NO.

### 1.3. Source pins chính

| Path | SHA-256 lúc soạn |
|---|---|
| backend/src/sketch2life/interfaces/http/routers/be1_registry.py | ACB51CA040306198BA5B95F77091717BB73797E80BBA28CDE8C1DB14D97C8A54 |
| backend/src/sketch2life/interfaces/http/routers/be1_common.py | 40DDE6F9B2AC91A78FE2A2F65B15EFCB1B76D132D49BB5580338710B12B9C45C |
| backend/src/sketch2life/application/services/be1_runtime.py | BD1D57B2E69ABB71F6FB933BF66CC499F36CA8F79D1FE03F6CE99FFD6AEBC3E4 |
| backend/src/sketch2life/infrastructure/persistence/be1_models.py | 6859CC8313482C70828176B4E12209B485B7D582C6831340AE0D451659219C1E |
| backend/src/sketch2life/infrastructure/persistence/core_store.py | AB2E86FD002E51A4FDB377644EE376E30AF6E6D888B270C4C1B3646BCB201F94 |
| backend/src/sketch2life/domain/core_foundation.py | FFC7B8BBAA1AF2CB0D63479AAA598B74AFD1B4FB4DD58088A5706235A16C19B3 |
| backend/src/sketch2life/interfaces/http/openapi_contract.py | 2A5A5DAB4B2CFAECC4F30099E1CD2D862DEBC9CFCE066D623C7CE441C5E7AA81 |
| backend/src/sketch2life/interfaces/http/openapi_contract_amendments.py | C23BC0C8E9BE6E1989DCDA656588D498F67789EC65D0FE4967C2A64B5E0A2EFC |
| backend/src/sketch2life/interfaces/http/openapi_srs_v22.py | 2D07A5D299FFBBA5264247A107065044DE215C156DC50C1431949FFAF3285B11 |
| backend/src/sketch2life/contracts/schemas/be1_runtime.py | 59A2CA1A356916816A788C77E4B03D4FA1A716ECF5CC245B515A39E146B14F11 |
| backend/tests/unit/test_profile_age_invariant.py | B166C424BC64F35CBB0F1454964F8459FA67B6D956C811C33A854E6B70E76BAB |
| backend/tests/contract/test_be1_synthetic_pilot.py | 03CCBCE40EB3DA13FA15D3C128F22CF70B6AEE4968CF0B726A7ED8B136C74611 |
| backend/tests/unit/test_age_provenance_columns.py | DE1B745B83AE490C4ACAD8F1D457B3CF1E16420B06F79B19DDFF3576BE778C97 |
| backend/tests/integration/test_be1_postgres_api.py | 49F14546F4A3B6684466CAF7215CE35466548E90AF11E5F1604BE4C343033E0E |
| backend/tests/unit/test_synthetic_eligibility.py | B579975452443848A560B89D3CFCA433C5E644EC6CA30165A68D21285E29CBF1 |
| backend/tests/contract/test_openapi_contract_catalog.py | 401952E5588C96415B2D275565137C1D4D0A2B795056D39A2B0E962C326B6C40 |
| backend/tools/be1_api_smoke.py | BDA07ECA4FC63D4EF3D7F14B758F25E3B79AEA92B3CF4C53FAA84D76198582C5 |

These are Draft 1-time baselines; final Task Approval must rehash every exact read/edit/new path. The smoke tool is listed only as a read-only negative scope check; it is not a candidate edit or acceptance test.

## 2. Phase and route contract

**Phase:** S1a-T, Teacher/organization foundation on existing BE1 tables; no BE1 migration. D-156 R1–R3 are directions only.

### 2.1. Operations and legacy-write disposition

| Operation | SRS v2.3 and mount candidate | Direction / remaining input |
|---|---|---|
| Create class | SRS §21.2 POST /v1/organizations/{org_id}/classes; existing prefix candidate POST /api/be1/v1/organizations/{organization_id}/classes | school_admin only; capacity and CLASS_CAPACITY_REACHED are NOT COVERED by D-155 Q7 |
| Assign one Teacher | SRS §21.2 POST /v1/classes/{class_id}/assignments; mount candidate POST /api/be1/v1/classes/{class_id}/assignments | class_id is required in path; new operation accepts only role teacher; exact body fields and response remain owner fields |
| Create Teacher profile/enrollment | SRS §21.2 POST /v1/classes/{class_id}/profiles; existing prefix candidate POST /api/be1/v1/organizations/{organization_id}/classes/{class_id}/profiles | Teacher must have an active class-level assignment; organization-wide assignment with class_id NULL is insufficient; school_admin is denied |

Current legacy routes in be1_registry.py are POST /api/be1/v1/organizations/{organization_id}/assignments and DELETE /api/be1/v1/organizations/{organization_id}/assignments/{assignment_id}. D-155 Q4 requires write access through old assignment routes to be removed or blocked. Owner must select remove versus block, status/error response, and OpenAPI representation before final approval. Do not leave both old and new assignment creation routes writable. No route for replacing/removing a Teacher is included; this is explicit debt under D-156 R2. Do not infer that the old DELETE route can replace the missing M2 Teacher replacement/removal operation.

### 2.2. Teacher cardinality, denial and scope

- Count only rows where class_id equals the class path parameter, role equals teacher, and active is true. The new route cannot create organization-wide class_id NULL assignments and cannot create school_admin, guide or observer assignments.
- A class may have zero active Teachers. A second active Teacher is rejected. The route serializes competing assignment attempts with a lock on the classroom row in the same transaction, then counts/creates. No BE1 migration or new database uniqueness constraint is authorized. Existing uq_be1_assignment permits class_id NULL and does not by itself establish the new invariant.
- The Teacher profile route requires an active class-level Teacher assignment for the exact class. Existing authorize_adult accepts organization-wide assignments when a class_id is supplied; the M2 route must add a narrow class-level check without changing authorize_adult globally.
- For M2 routes only, no assignment, nonexistent class and class belonging to another organization all produce HTTP 403 with code SCOPE_DENIED and an indistinguishable response shape. Do not globally change authorization helpers or legacy routes. Legacy error codes outside the M2 routes remain unchanged.
- Audit is metadata-only. Tests include missing and revoked assignment. No row values, child content, tokens or consent evidence are written to audit.

### 2.3. Synthetic profile rules and limitations

- The M2 Teacher profile operation creates only SYNTHETIC_DEV; consent_id and consent_purpose_ref are NULL. It uses existing table/model, creates profile and enrollment in one transaction, and does not call the operator-only core_store helper that commits separately.
- Apply the existing synthetic markers: child_id begins synthetic- and display_name begins Synthetic .; age_source is SYNTHETIC_FIXTURE. Keep the existing data_origin/consent database check satisfied. This is not consent bypass for a real profile: REAL and LEGACY_UNCLASSIFIED creation are blocked in this S1a-T route.
- HTTP SYNTHETIC_DEV creation is allowed only when settings.env is local or test and synthetic_pilot_enabled is true. Other environments and disabled flag fail closed.
- Enforce integer age 36–120 in the M2 route/application and request schema. Do not alter BE1 database check 36–155 or globally change core age policy. Do not use child_age.py. Existing profiles are not clamped or rewritten.
- Request schema currently requires consent identifiers and has an upper bound of 155. The exact synthetic request field allowlist must be reviewed; client must not choose data_origin or consent state. These schema changes and the named tests below are intentional consequences of D-155 Q2/R8.

## 3. DB policy and command ceiling candidates

All entries here are proposals for a future owner-signed approval, not permission to run them.

### 3.1. Target and runtime-engine guard

- Target database: sketch2life_m2_s1a; PostgreSQL 17 native Windows on localhost:5433; current_user postgres is owner-reported, not independently connected/verified here.
- Dedicated process variable: S1A_T_TEST_DATABASE_URL. Fixture must fail before seeding if it is absent/empty. It sets the process-level SKETCH2LIFE_DATABASE_URL from this dedicated value, clears cached database/settings factories, creates the real app, and asserts identity using app.state.be1_runtime.engine before any write: current_database equals sketch2life_m2_s1a, current_user postgres, port 5433, server address loopback, server major 17.
- This addresses the actual engine the application uses; a separate “guard connection” is not sufficient. The process variable takes precedence over .env. The fixture must not fall back to a value found in .env when the dedicated variable is absent. Do not read .env. The secret-ingress method that avoids PSReadLine history and logs is an owner field for final approval.
- Test-generated rows use existing IDs with synthetic prefix and test-run identifier; no new DB column or broad cleanup. After tests, inventory counts only IDs with the approved prefix/run marker and does not select row values. Any unlabelled/unknown rows are a STOP.
- Never write, migrate, restore, drop, truncate or clean up sketch2life.

### 3.2. Candidate commands and ceilings

Commands below are candidate text only; an owner must pin exact executable, process environment, log/cache path, timeout and count in a separate Task Approval. No command was run for this draft.

| Work | Candidate and boundary |
|---|---|
| Offline baseline before T code | From cwd backend, backend/.venv/Scripts/python.exe -m pytest -q -p no:cacheprovider --basetemp ../tmp/m2-s1a-t/baseline on the existing profile-age, synthetic-pilot, age-provenance, migration-count and OpenAPI-contract files. Record the actual baseline. Static source review identifies test_head_counts_by_both_methods_match_the_derived_expectation at test_synthetic_eligibility.py:454–466 as stale at this HEAD; the assertion expects 25/(11,9), while the repository has 28 revision files. Do not call that result PASS or include its known baseline failure in T PASS/FAIL.
| Offline tests after T code | Same selected files plus test_m2_s1a_teacher_service.py and test_m2_s1a_teacher_routes.py; exclude only test_synthetic_eligibility.py::test_head_counts_by_both_methods_match_the_derived_expectation until the P root revision updates graph counts. Use -p no:cacheprovider and --basetemp under ../tmp/m2-s1a-t. A deselected/excluded node is NOT RUN, not PASS.
| PostgreSQL route test | Only tests/integration/test_m2_s1a_teacher_postgres.py using S1A_T_TEST_DATABASE_URL and runtime.engine identity guard. Do not include test_be1_postgres_api.py: its fixture currently requires BE1_TEST_DATABASE_URL and a database name containing be1_acceptance; it is not valid for this target without a separately approved fixture change.
| Inventory | Owner-pinned psql executable and a complete read-only SQL/body are not yet supplied. Require a READ ONLY transaction, exact DB/user/port/address/version assertions, table inventory and labelled-row counts only. Exact psql path, password prompt method and log destinations remain owner fields; do not claim the existing prose is a runnable command.
| Mypy baseline and final | From cwd backend, .\\.venv\\Scripts\\python.exe -m mypy --version, then strict package run with --no-incremental and cache under ../tmp/m2-s1a-t/mypy-cache. For stdout/stderr use a pinned cmd.exe direct redirection to distinct files under ../tmp/m2-s1a-t; no Tee/transcript. Pin timeout and command hash in final approval.
| Ruff | Use backend/.venv/Scripts/ruff.exe check --select E,F,I,UP,B,SIM on the exact approved paths, with cache under ../tmp/m2-s1a-t.
| Repository checks | Candidate once each from repo root: validate_harness.py, validate_repository_security.py, validate_architecture.py and git diff --check. No result is implied by this draft. |

Before T code, owner-run offline pytest and strict mypy baselines are recorded. Record pre-existing red tests verbatim and exclude them from the S1a-T verdict; do not change shell, selection or command after a failure to bypass a gate. Recompute inventory and mypy baseline after T and before P under D-156 R1.

## 4. K4 — source-only reconciliation before code

K4 is a read-only source comparison, not a database operation. Compare the D-154 inventory and schema definitions with BE1/core models, routers, application policy, migration source and test expectations. Record separately: owner-reported facts, source facts, inference and unknown. K3 mismatch between 20261103_story_upload_compat and 20261104_story_revisions is not repaired or converted into a claim about live DB heads. If a change needs BE1/Core/Story DDL or an unapproved path, STOP. Evidence file candidate: evidence/M2_S1A_T_K4_SOURCE_RECONCILIATION_20261107.md; it does not exist and cannot be created under this DRAFT.

## 5. Authentication test seam and route behavior

- Keep real routing, assignment lookup, authorization, transaction handling and PostgreSQL. Replace only Firebase token verification by assigning app.state.be1_runtime.identity_verifier a test double whose async verify method returns a test VerifiedPrincipal; send the normal Bearer Authorization header. Do not use dependency_overrides for the identity dependency being tested.
- Current verifier returns an empty roles set and authorize_adult derives rights from assignment rows, not principal.roles. A verified principal without a qualifying assignment is the denial case; do not claim a Platform Admin/Operator/content-admin role test when the system does not represent those roles.
- M2 route-level scope denial follows §2.2. Do not edit the global authorize_adult implementation or shared be1_common helper to normalize all BE1 routes. A proposed path change in either shared helper is a STOP pending a new decision/approval.
- Class and assignment actor is school_admin; Teacher profile actor is assigned Teacher; school_admin is denied on Teacher profile route. D-148 item 4 says isolating reads of Teacher profiles is NOT RUN because M2 has no such route. No /v1/me, /v1/teacher/profiles, profile list/read/delete, S1b grants, StoryRun, or real data.
- F-1 uses one new per-class assignment write endpoint. Existing Bruno files 004-create-assignment and 005-revoke-assignment plus artifacts/be-full/openapi.runtime.json still describe legacy routes. They are read-only drift, not acceptance and not edited by S1a-T.

## 6. Allowlist candidate — no effect until separately approved

### 6.1. Read-only paths

- backend/src/sketch2life/interfaces/http/routers/be1_common.py and interfaces/http/be1_runtime.py: read to understand shared policy and actual runtime engine/test seam; no edit.
- backend/src/sketch2life/interfaces/http/router_composition.py and app.py: read-only; current BE1 router is already mounted, so no change is presumed.
- backend/src/sketch2life/infrastructure/identity/firebase_token_verifier.py; application/ports/identity.py; infrastructure/config/settings.py; infrastructure/persistence/be1_models.py; infrastructure/persistence/core_models.py; infrastructure/persistence/core_store.py; domain/core_foundation.py; domain/child_age.py; application/services/be1_runtime.py.
- backend/alembic/env.py; 20261103_story_upload_compat.py; 20261104_story_revisions.py: read-only.
- Existing tests: test_profile_age_invariant.py, test_synthetic_eligibility.py, test_be1_postgres_api.py, tests/integration/ai_jobs/test_migrations.py. The PostgreSQL fixture and graph-count exclusions in §3.2 apply.
- SRS v2.3, DTR v2.3, M2 Draft 10/11, S1a-T/P Draft 1, D-144/D-148/D-151/D-152/D-154/D-155/D-156 and the pinned S0 inventory.
- Bruno/OpenAPI artifacts under features/FEAT-063-system-architecture-rearchitecture/artifacts/be-full are read-only drift, including the two legacy assignment requests and openapi.runtime.json. No update is approved here.

### 6.2. Candidate existing paths to edit

Only these exact paths are candidates; final hashes and selected edits must be added to Task Approval:
- backend/src/sketch2life/interfaces/http/routers/be1_registry.py
- backend/src/sketch2life/contracts/schemas/be1_runtime.py
- backend/src/sketch2life/application/services/be1_runtime.py is NOT in this edit list; a change to global BE1 policy is out of scope.
- backend/src/sketch2life/interfaces/http/openapi_contract.py
- backend/src/sketch2life/interfaces/http/openapi_contract_amendments.py
- backend/src/sketch2life/interfaces/http/openapi_srs_v22.py
- backend/tests/unit/test_age_provenance_columns.py
- backend/tests/contract/test_be1_synthetic_pilot.py
- backend/tests/contract/test_openapi_contract_catalog.py

Do not edit test_profile_age_invariant.py unless the unchanged create_profile AST path is actually flagged; if flagged, stop and obtain an explicit approval amendment. Do not edit test_synthetic_eligibility.py in T for its migration-count assertions. Do not edit or run test_be1_postgres_api.py under the current fixture. Do not edit tools/be1_api_smoke.py; static review shows it does not exercise assignment/profile/class mutation.

### 6.3. Candidate new paths

- backend/tests/unit/test_m2_s1a_teacher_service.py
- backend/tests/contract/test_m2_s1a_teacher_routes.py
- backend/tests/integration/test_m2_s1a_teacher_postgres.py
- features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S1A_T_K4_SOURCE_RECONCILIATION_20261107.md
- features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S1A_T_IMPLEMENTATION_REPORT_20261107.md

No file in this list is created by this Draft.

## 7. Acceptance mapping

Only items marked applicable and later selected by owner in a final Task Approval can become exit gates.

| Existing M2-AT | S1a-T evidence |
|---|---|
| M2-AT-01 | Assignment authorization, missing/revoked assignment and metadata-only audit; role-denial cases representable in current identity model only |
| M2-AT-02 | Organization/class scope derived server-side; class-wide assignment cannot satisfy the Teacher-profile route |
| M2-AT-03 | Integer ages 36 and 120 accepted for new synthetic profile; 35 and 121 rejected; no child_age.py |
| M2-AT-04A | One active Teacher/class and race serialization; zero allowed, second rejected. PARTIAL because capacity and CLASS_CAPACITY_REACHED are NOT COVERED |
| M2-AT-04B | Assigned Teacher creates one synthetic profile/enrollment atomically; school_admin denied. PARTIAL because expected class revision is NOT COVERED |
| M2-AT-10 | Service/contract/persistence age projection only. No StoryRun route; legacy 121–155 rows not clamped. |
| M2-AT-11 | SYNTHETIC_DEV, null consent refs, synthetic markers, environment/feature gate; REAL and LEGACY_UNCLASSIFIED blocked |

M2-AT-05/06/07 are NOT RUN because S1b is deferred. M2-AT-08/09 and S2 routes are outside T. M2-AT-10 does not call StoryRun. The read isolation of Teacher profiles is NOT RUN per D-148 item 4. Q7 debt: capacity and CLASS_CAPACITY_REACHED, expected class revision, assignment revision in response, idempotency key. Do not mark any of these as passed.

OpenAPI baseline is 129 runtime operations, 124 mounted catalog operations, 111 paths and 18 tags. Adding the new assignment operation changes counts depending on the owner’s remove/block choice for the old POST and DELETE: remove both and add new gives 128/123/111; remove old POST only and retain DELETE gives 129/124/112; retain both old operations as blocked/deprecated and add new gives 130/125/112. Counts are ordered runtime operations / mounted operations / paths. Recalculate from the final route disposition; do not pin a chosen alternative here. Existing BE1 tag reuse keeps 18; adding a new tag changes the count and needs owner selection.

## 8. Review finding dispositions

### 8.1. New findings from independent Draft 1 review

| Finding | Draft 2 disposition |
|---|---|
| N-01 | §3.2 records the stale graph-count node (test_synthetic_eligibility.py:454–466), the pre-code baseline and its exclusion from T PASS/FAIL. P updates graph counts later. |
| N-02 | §2.2 defines role, path scope, active-row count, org-wide exclusion, class-level profile authorization and a test for an org-wide seeded assignment. |
| N-03 | §3.1 asserts identity on app.state.be1_runtime.engine after setting the dedicated process variable and clearing caches; no separate guard connection. Secret ingress stays an owner field. |
| N-04 | §5 names the identity_verifier test seam and Bearer header; no dependency override. Unsupported system-role tests are explicitly NOT RUN. |
| N-05 | §3.2 does not claim to contain a runnable psql script; executable, password prompt and log path remain owner fields. |
| N-06 | §3.2 uses the backend virtualenv path from cwd=backend and requires direct cmd.exe redirection to pinned tmp logs. |
| N-07 | §3.2 places pytest basetemp and ruff/mypy cache under tmp; test cache provider is disabled. |
| N-08 | §2.3 and §6.2 name the actual age-source and consent assertions; no new Parent AST entry. Exact test-be1 PostgreSQL case remains NOT RUN pending a safe fixture decision. |
| N-09 | §3.2 explicitly excludes the current BE1 PostgreSQL fixture and removes be1_api_smoke from edit/acceptance scope. |
| N-10 | §2.3 pins child_id/name/age_source markers and env/flag gating; no real path. |
| N-11 | §7 adds missing/revoked assignment and metadata-only audit; AT-04A/04B PARTIAL; Teacher read isolation NOT RUN. |
| N-12 | §1.2/§6/§7 requires T→P sequencing and re-counts OpenAPI after the old-route choice. |
| N-13 | §5/§6 records Bruno/OpenAPI artifacts as read-only legacy drift. |
| N-14 | §2.1 and §7 remove any claim that assignment revision is satisfied; D-144 §9.5 is cited correctly as clarified by D-155 Q8. |
| N-15 | §3.1/§7 counts only rows with approved synthetic prefix and run marker; no row values and no broad cleanup. |
| N-16 | §2.1 records replacing/removing Teacher as debt and leaves old route disposition for owner; no speculative 409 behavior. |
| N-17 | §2.2/§5 scopes SCOPE_DENIED to M2 routes and preserves global/legacy BE1 behavior. |

### 8.2. Review Draft 1 findings P2-01..P2-13 and P3-01..P3-12

| Finding | Status and section |
|---|---|
| P2-01 | RESOLVED at plan level: insertion is in create_profile; test names are exact; creation-path allowlist stays unchanged unless AST actually reports a new path (§2.3, §6.2). |
| P2-02 | PARTIAL / owner field: exact old/new paths and no writable alias are listed; owner must choose remove or block for legacy POST/DELETE (§2.1). |
| P2-03 | RESOLVED at direction level: role, class scope, zero/one active rule, lock and no migration are explicit; old route choice remains gated (§2.2). |
| P2-04 | RESOLVED at plan level: exact source/catalog/schema/test edits and read-only composition files are separated (§6). |
| P2-05 | RESOLVED: only Firebase verifier is doubled; runtime identity, assignment, authz, transaction and PostgreSQL stay real (§5). |
| P2-06 | RESOLVED for T; Parent identity/IDOR is mapped to S1a-P (§5, out-of-scope). |
| P2-07 | RESOLVED at design level; dedicated process variable is asserted on real app engine. Secure environment injection method remains owner field (§3.1). |
| P2-08 | RESOLVED: Q6 synthetic prefix + run-id labels; no 0-row requirement, no broad cleanup (§3.1). |
| P2-09 | RESOLVED: T runs no Alembic; version inventory only via owner-approved read-only psql (§3.2). |
| P2-10 | RESOLVED: each SRS §21.2 operation and Q7 not-covered field is traced (§2, §7). |
| P2-11 | RESOLVED: one M2 403 SCOPE_DENIED; shared authorization helper is not changed (§2.2, §5). |
| P2-12 | PARTIAL: cache, executable and baseline issues corrected; exact psql command, credentials ingress and final ceilings need owner fields (§3.2, §10). |
| P2-13 | RESOLVED: D-152 and D-155 Q8 are cited without inventing a D-155 section (§1.2, §2.1). |
| P3-01 | RESOLVED: all hashes in this draft are full 64-character SHA-256 values; rehash before approval (§1). |
| P3-02 | RESOLVED: both DTR working and LF blob hashes are recorded (§1.1). |
| P3-03 | OTHER PHASE: stamp/Parent migration belongs to S1a-P; T runs no Alembic (§6). |
| P3-04 | RESOLVED: age checks do not use child_age.py or invoke StoryRun (§2.3, §7). |
| P3-05 | OUT OF SCOPE: FR-C-10/BR-35, profile delete not covered (§5). |
| P3-06 | RESOLVED: no /v1/me, /v1/teacher/profiles or extra list/read; Teacher read isolation NOT RUN (§5, §7). |
| P3-07 | PARTIAL: no false claim of runnable psql body; executable, SQL, secret prompt and log path remain owner fields (§3.2, §10). |
| P3-08 | OWNER FIELD: client/server profile ID and idempotency behavior remain unchosen (§10). |
| P3-09 | RESOLVED: only backend/.venv executable is proposed (§3.2). |
| P3-10 | RESOLVED for T: stale graph test is not modified or counted in T; P will update after its root revision (§3.2, §6). |
| P3-11 | RESOLVED: no remote docs branch/fetch/merge (§6). |
| P3-12 | RESOLVED: destructive DB fixture files are excluded from every candidate test set; see stop gate (§9). |

## 9. Stop gates and validity

STOP without retry if any pin/HEAD/index changes; target DB identity differs; a write could touch sketch2life; any unlabelled/unknown rows exist; a test fixture can create/drop a DB; M2 route cannot normalize denial without changing global BE1 behavior; legacy assignment writes remain parallel; a REAL/LEGACY_UNCLASSIFIED path is reachable; a change needs BE1/Core/Story migration; test writes are not synthetic-labelled; a required path is outside the approved allowlist; route/OpenAPI counts differ from the owner-selected alternative; secret or URL appears in output; setup error, crash, timeout, no official test summary, no validator verdict or command ceiling is missing.

Never run integration directories broadly. Known test fixtures with CREATE/DROP DATABASE are backend/tests/integration/ai_jobs/conftest.py, backend/tests/integration/ai_policy/conftest.py, backend/tests/integration/learning_content/conftest.py and backend/tests/integration/be2_cross_lane/test_persisted_video_worker_flow.py. Also exclude backend/tests/integration/ai_jobs/test_migrations.py. The future acceptance must pin exact nodes, not a broad directory.

This Draft does not open S1a-P, S1b, S2, S3 or M3–M6. OWNER_MODAL_CALL_APPROVED=NO. Executor and independent reviewer must be separate sessions. No stage/commit/push/merge is authorized. This document ends at DRAFT.

## 10. Owner fields — leave blank

| Owner field | Status |
|---|---|
| Remove or block legacy assignment POST/DELETE; exact response and OpenAPI disposition | [ ] Chưa chọn |
| Exact request body/response fields for new assignment and profile | [ ] Chưa chọn |
| Teacher-second-assignment denial body; route-level SCOPE_DENIED body shape | [ ] Chưa chọn |
| Profile/child ID source, idempotency key behavior | [ ] Chưa chọn |
| Whether and how the pending-consent legacy PostgreSQL assertion is updated; current fixture cannot target this database | [ ] Chưa chọn |
| Secure process-variable ingress without shell history/log; psql executable, SQL body, log path and ceiling | [ ] Chưa chọn |
| Exact read/edit/new path allowlist with final hashes and command list | [ ] Chưa chọn |
| Final M2-AT applicability/PARTIAL dispositions, pre-code offline and mypy baseline evidence | [ ] Chưa điền |
| Independent reviewer, owner signature/date and final Task Approval hash | [ ] Chưa điền |

**Approval basis/signature/date:** CHƯA ĐIỀN.
**Final approval hash:** CHƯA CÓ.
**OWNER_MODAL_CALL_APPROVED:** NO.

