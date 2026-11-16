# M2 S1a-T Task Approval — Draft 4

**Status: DRAFT — NOT APPROVED, NOT LAUNCHED.** Draft 4 là bản kế hoạch tiếp tục từ Draft 3 với năm hiệu chỉnh hẹp được liệt kê bên dưới; không phải Task Approval, không mở S1a-T, không cấp quyền sửa code, chạy test, ghi DB hay chạy lệnh.

**Owner decision record:** Chưa có Task Approval/launch record. D-156 ghi hướng R1–R8; D-157 ghi hướng O1/O3/O4/O5/O7. Đây chỉ là direction, không phải approval thực thi. Owner fields, command ceilings và allowlist cuối còn chờ owner điền/duyệt.

**Independent review of Draft 1:** NEEDS_REVISION, 0 P1 / 3 P2 / 14 P3; chat-only session local_2b185df6-3608-47a3-8d9a-45cc09a0c43a. Báo cáo review chi tiết được đọc tại phiên soạn. Draft 4 đang chờ review độc lập; chưa có owner approval.

## Thay đổi từ Draft 3 sang Draft 4

| Phần Draft 3 | Hiệu chỉnh ở Draft 4 | Cơ sở |
|---|---|---|
| §1.3 | Sửa số pin source/test từ 17 thành 31, khớp số dòng trong bảng và kết quả rehash từng file | Bảng §1.3 |
| §2.4, §6.1 | Kiểm kê artifact/evidence lịch sử còn nhắc hai route assignment organization-scoped đã bị gỡ; ghi số lần nhắc và SHA-256, giữ chúng read-only | Tìm kiếm tĩnh và SHA-256 |
| §2.3, §6.1, §6.3, §7 | Nêu GET portfolio hiện có, cách kiểm ID do server cấp tới được lookup, và test/assertion ứng viên trong file PostgreSQL đã có trong candidate list | Đọc router và test/source |
| §3.2 | Chuẩn hóa executable theo cwd, các đường dẫn log/cache/basetemp tương đối với cwd và capture trực tiếp theo Baseline Draft 2 | Baseline Draft 2 |
| §3.2–3.3, §6.1, §9–10 | Ghi đánh giá source-only về app/settings/engine, seam an toàn ứng viên do owner chọn, giới hạn baseline after-only và stop gate | Baseline Draft 2 §3.1; đọc mã, chưa chạy |

Đối chiếu thay đổi bằng `git diff --no-index` giữa Draft 3 và Draft 4; năm hàng trên liệt kê các vùng hiệu chỉnh theo thứ tự tài liệu. Tiêu đề và trạng thái chỉ được cập nhật để nhận diện bản Draft 4.

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
| DECISIONS.md | SHA-256 DE0BBA068ECB7080DD1150EAF8C73CDA29790C4831C5EF8EBB660E357127E9F4; có D-142..D-157 | Directions đã ghi; không phải approval |
| TASK_APPROVAL.md | SHA-256 FEEE42E506F94352A8161EFE0B4B94870967072BEDF233285BFDF882352A3DF7 | S0-owner-run đóng; chưa có S1a-T approval |
| S0-doc evidence | SHA-256 1BB71300A6A22487311A8D39EECB0EB1CE2664CB471EC2DAF45DA8DE2E244001 | Đóng ở phạm vi tài liệu theo D-150 |
| S0-owner-run inventory | .claude/handoff/logs/M2_S0_OWNER_RUN_20261107/inventory.json; SHA-256 E4529F541002D840C3F2E1D25F24D00E7B92A65720E3036EB59BA71FD04DB64F | Artifact owner-run, không phải kết nối DB của phiên soạn |

Các pin đã được tính lại trong phiên soạn: ba Draft 1, Draft 10/11, SRS working tree và raw Git blob, DTR working tree, inventory, DECISIONS và TASK_APPROVAL. Bảng §1.3 có 31 pin source/test; đã đếm và rehash đủ 31, tất cả đều khớp. Không đọc .env.

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
| backend/src/sketch2life/domain/assistance.py | 1AF5211FB97C2E2175A673EC9E6A79D531187D2026DF8A53395CFD346F0A8488 |
| backend/src/sketch2life/domain/vision_context.py | 9501F2194A2896DF121C50AF2A1DF29B7003C7F2029AF0FEBD461664886E04EB |
| backend/src/sketch2life/application/services/vision_analysis.py | 1BCFB18F07613EF3377D34EE85091FD349EB502178F0A04F8B511A2A969E48C1 |
| backend/src/sketch2life/infrastructure/assistance/be1_fact_reader.py | 348E18B395A35DF0D05EC8E1DCB56F8ECBDF64C7F181250A2C3F132CA53A535E |
| backend/src/sketch2life/interfaces/http/openapi_contract.py | 2A5A5DAB4B2CFAECC4F30099E1CD2D862DEBC9CFCE066D623C7CE441C5E7AA81 |
| backend/src/sketch2life/interfaces/http/openapi_contract_amendments.py | C23BC0C8E9BE6E1989DCDA656588D498F67789EC65D0FE4967C2A64B5E0A2EFC |
| backend/src/sketch2life/interfaces/http/openapi_srs_v22.py | 2D07A5D299FFBBA5264247A107065044DE215C156DC50C1431949FFAF3285B11 |
| backend/src/sketch2life/interfaces/http/router_composition.py | E06A158B3616583DF8ABBA21D52C62E769AFA6A9E7C75359D28D424AB15849CC |
| backend/src/sketch2life/interfaces/http/app.py | D9DCBDC5BF3B71840C98BEB50A80D5A7BC1D800C3F93FFBB05DD021E99A995C0 |
| backend/src/sketch2life/contracts/schemas/be1_runtime.py | 59A2CA1A356916816A788C77E4B03D4FA1A716ECF5CC245B515A39E146B14F11 |
| backend/tests/unit/test_profile_age_invariant.py | B166C424BC64F35CBB0F1454964F8459FA67B6D956C811C33A854E6B70E76BAB |
| backend/tests/contract/test_be1_synthetic_pilot.py | 03CCBCE40EB3DA13FA15D3C128F22CF70B6AEE4968CF0B726A7ED8B136C74611 |
| backend/tests/unit/test_age_provenance_columns.py | DE1B745B83AE490C4ACAD8F1D457B3CF1E16420B06F79B19DDFF3576BE778C97 |
| backend/tests/integration/test_be1_postgres_api.py | 49F14546F4A3B6684466CAF7215CE35466548E90AF11E5F1604BE4C343033E0E |
| backend/tests/unit/test_synthetic_eligibility.py | B579975452443848A560B89D3CFCA433C5E644EC6CA30165A68D21285E29CBF1 |
| backend/tests/contract/test_openapi_contract_catalog.py | 401952E5588C96415B2D275565137C1D4D0A2B795056D39A2B0E962C326B6C40 |
| backend/tests/contract/test_app_composition.py | 2E6E9DD2E7C915F4E43EB3E0CB4682FDE6FF848D31F8714EFC7C59D9F4A1D49A |
| backend/tests/unit/test_assistance_domain.py | AFABE3545E47EAB5101551B1642855143D71E9FD910DA0BA8F213A9B78A89DC8 |
| backend/tests/unit/test_assistance_service.py | A40BF516BD7232F7E641EF0168764F7B61ADE0E0A895C0A7B03A74B60ABFDAAC |
| backend/tests/unit/test_be1_fact_reader.py | F234E7056F0FAFD0479519AB419271E3EE19552E1AF55A17E5A09CD387F5F815 |
| backend/tests/unit/test_vision_analysis_service.py | D5B5A3F23A69B6CFD8079EBF57A6BDE85AC0CBB7699A586C03B14789FC8C8CDD |
| backend/tests/unit/test_vision_analysis_review_fixes.py | CC3F777F2C7D48733B9C2444FC0DC3D496FC8D914A0DF4469DAE2EABB54EBD3D |
| backend/tests/unit/test_vision_context_domain.py | 4A457F16A74C0CEEA9C2C53BB85174C7D2067C2113E80558E79266F234E43F96 |
| backend/tests/unit/test_vision_context_service.py | E7E9BAAC7D54C42F45F7F56E9D8A99942290EEAB7F15620DE1B3911666D78348 |
| backend/tools/be1_api_smoke.py | BDA07ECA4FC63D4EF3D7F14B758F25E3B79AEA92B3CF4C53FAA84D76198582C5 |

These are Draft 1-time baselines; final Task Approval must rehash every exact read/edit/new path. The smoke tool is listed only as a read-only negative scope check; it is not a candidate edit or acceptance test.

## 2. Phase and route contract

**Phase:** S1a-T, Teacher/organization foundation on existing BE1 tables; no BE1 migration. D-156 R1–R3 and D-157 O1/O3/O4/O5/O7 are directions only.

### 2.1. Operations and legacy-write disposition

| Operation | SRS v2.3 and mount candidate | Direction / remaining input |
|---|---|---|
| Create class | SRS §21.2 POST /v1/organizations/{org_id}/classes; existing prefix candidate POST /api/be1/v1/organizations/{organization_id}/classes | school_admin only; capacity and CLASS_CAPACITY_REACHED are NOT COVERED by D-155 Q7 |
| Assign one Teacher | SRS §21.2 POST /v1/classes/{class_id}/assignments; mount candidate POST /api/be1/v1/classes/{class_id}/assignments | class_id is required in path; new operation accepts only role teacher; exact body fields and response remain owner fields |
| Create Teacher profile/enrollment | SRS §21.2 POST /v1/classes/{class_id}/profiles; existing prefix candidate POST /api/be1/v1/organizations/{organization_id}/classes/{class_id}/profiles | Teacher must have an active class-level assignment; organization-wide assignment with class_id NULL is insufficient; school_admin is denied |

The existing POST `/api/be1/v1/organizations/{organization_id}/assignments` and DELETE `/api/be1/v1/organizations/{organization_id}/assignments/{assignment_id}` routes are removed from the router and OpenAPI catalog under D-157 O1. Do not leave blocked stubs or writable aliases. Revoking or replacing a Teacher has no route and remains debt under D-156 R2; the removed DELETE route does not supply that capability.

### 2.2. Teacher cardinality, denial and scope

- Count only rows where class_id equals the class path parameter, role equals teacher, and active is true. The new route cannot create organization-wide class_id NULL assignments and cannot create school_admin, guide or observer assignments.
- A class may have zero active Teachers. A second active Teacher is rejected with HTTP 409 and the fixed code `CLASS_TEACHER_EXISTS`; the response body must not disclose the existing Teacher's identity. Exact explanatory body text remains an owner field. The route serializes competing assignment attempts with a lock on the classroom row in the same transaction, then counts/creates. No BE1 migration or new database uniqueness constraint is authorized. Existing `uq_be1_assignment` permits `class_id` NULL and does not by itself establish the new invariant.
- The Teacher profile route requires an active class-level Teacher assignment for the exact class. Existing authorize_adult accepts organization-wide assignments when a class_id is supplied; the M2 route must add a narrow class-level check without changing authorize_adult globally.
- For M2 routes only, no assignment, nonexistent class and class belonging to another organization all produce HTTP 403 with code SCOPE_DENIED and an indistinguishable response shape. Do not globally change authorization helpers or legacy routes. Legacy error codes outside the M2 routes remain unchanged.
- Audit is metadata-only. Tests include missing and revoked assignment. No row values, child content, tokens or consent evidence are written to audit.

### 2.3. Synthetic profile rules and limitations

- The M2 Teacher profile operation creates only SYNTHETIC_DEV; consent_id and consent_purpose_ref are NULL. It uses existing table/model, creates profile and enrollment in one transaction, and does not call the operator-only core_store helper that commits separately.
- The server generates `child_id` with the prefix `synthetic-` plus a random suffix; the client does not send `child_id`. The request schema, handler, profile/enrollment/audit linkage, and tests must use the generated ID. The generator must fit the existing database column constraint; the random algorithm and exact response fields are not newly chosen here. `display_name` begins `Synthetic ` and `age_source` is `SYNTHETIC_FIXTURE`.
- Apply D-157 O5: the API returns `SYNTHETIC_DEV` exactly as stored. Document the mapping from the SRS name `SYNTHETIC_TEST` to stored/API `SYNTHETIC_DEV`; do not change the enum. `consent_id` and `consent_purpose_ref` remain NULL under D-155 Q2. This is not consent bypass for a real profile: REAL and LEGACY_UNCLASSIFIED creation are blocked in this S1a-T route.
- HTTP SYNTHETIC_DEV creation is allowed only when settings.env is local or test and synthetic_pilot_enabled is true. Other environments and disabled flag fail closed.
- Apply D-157 O7 for new values: the shared `validate_age_months` source and request schema use 36–120; the existing BE1 database CHECK 36–155 is unchanged, and existing rows are neither clamped nor rewritten. Every Teacher route that creates a profile uses the same source. Because the helper is shared, this also affects any other BE1 profile-creation route that calls it; enumerate those callers and test impacts before code. Do not use `child_age.py`.
- `validate_age_months` is shared by BE1 and assistance/vision code. Changing it can affect callers that validate existing facts, not only new Teacher profile creation. Before implementation, classify every caller and preserve the ability to read existing 121–155 rows; if the shared change rejects such a read or changes an unrelated contract, stop for an owner decision rather than silently widening this phase. The exact synthetic request field allowlist must be reviewed; the client must not choose `data_origin` or consent state.

### 2.4. Direction-to-section and affected-test map

| Direction | Draft 3 location and treatment |
|---|---|
| O1 | §2.1, §6, §7, §8 and §9: remove both legacy assignment operations from router/catalog; no stub; existing Bruno/OpenAPI artifacts are identified as read-only drift. |
| O2 | Not included in D-157; no new disposition is inferred. Existing one-Teacher/cardinality direction remains D-156 R2 and §2.2. |
| O3 | §2.2/§10: fixed HTTP 409 and `CLASS_TEACHER_EXISTS`; no existing identity in body; exact body wording remains open. |
| O4 | §2.3/§6/§7: server-generated `synthetic-` child ID; request, handler, linkage, response and contract tests must align; idempotency remains NOT COVERED. |
| O5 | §2.3/§7: return stored `SYNTHETIC_DEV`, document SRS mapping, do not change enum. |
| O6 | Not included in D-157; no new disposition is inferred. Synthetic-only/local-test gate and consent-null direction remain D-155 Q2/F-6 and D-156 R8. |
| O7 | §2.3–2.4, §6–9: one 36–120 validation source for new values; DB check stays 36–155; inspect shared-callers and preserve existing-row reads. |

O1 references found by static search: `backend/src/sketch2life/interfaces/http/routers/be1_registry.py`, `openapi_srs_v22.py`, `openapi_contract_amendments.py`, `openapi_contract.py`, plus `backend/tests/contract/test_app_composition.py::test_compatibility_app_preserves_baseline_route_surface` and `backend/tests/contract/test_openapi_contract_catalog.py::test_runtime_openapi_matches_all_mounted_rev37_operations_and_records_unmounted_candidates`. Both route-set/count tests need their expected surface/count updated. Historical artifacts/evidence that still contain the removed organization-scoped routes are inventoried with hashes in §6.1.1; they remain read-only drift, not acceptance. Static search found no old-path reference in `backend/tools/be1_api_smoke.py`.

O7 test cases requiring explicit review/update if they assert the changed shared boundary:

- `backend/tests/unit/test_assistance_domain.py::test_audience_refusal_checks_each_member_without_averaging` currently treats age 155 as supported.
- `backend/tests/unit/test_vision_analysis_service.py::test_v15_authoritative_age_window_not_legacy_under_nine_helper` includes 155 as allowed; its group-age case also uses a 155-month fact.
- `backend/tests/unit/test_vision_analysis_review_fixes.py::test_r02_age_boundaries_after_provider_stay_accepted` includes 155 as accepted.
- `backend/tests/unit/test_vision_context_domain.py::test_c2_a03_projection_is_per_member_sorted_bands_without_identity_or_mean` supplies a 155-month member. `test_c2_a03_fixture_bands_cover_36_to_155_exactly_once` tests a separate fixture-band range and must not be changed merely because the shared validator changes.
- `backend/tests/unit/test_assistance_service.py::test_n05_each_member_age_is_checked_without_averaging`, `backend/tests/unit/test_be1_fact_reader.py`, and `backend/tests/unit/test_vision_context_service.py` also exercise shared age-validation callers and belong in regression review even though they do not themselves pin a literal 155 boundary; update boundary cases to 121 only if they are validating the same new-value rule, not persisted-row reads.
- `backend/tests/contract/test_learning_content_commands.py` has an independent request-schema boundary of 155, and `backend/tests/unit/test_t2c_digest_pin.py` pins a proposed age-policy reference. These are not automatically in O7 scope; leave unchanged unless static caller analysis shows the shared helper is part of their contract and an owner-approved amendment includes them.
- `backend/tests/learning_content_fixtures.py` defines a content-fixture `max_months` of 155; it is not by itself proof that this fixture calls the shared BE1 validator, so keep it outside the O7 edit set unless caller analysis and a separate amendment establish that relationship.
- `backend/tests/contract/test_be1_synthetic_pilot.py::test_registry_and_records_do_not_gain_a_synthetic_path` directly asserts that no synthetic path is added to `be1_registry`; D-155 Q2 authorizes the new SYNTHETIC_DEV creation path, so revise that assertion to verify the approved local/test gate, NULL consent refs and retained legal-only checks on unrelated routes. Do not weaken the other legal-consent assertions in this module.
- The consent-null synthetic direction changes test setup/expectations for the new profile request: `backend/tests/unit/test_age_provenance_columns.py::test_registry_profile_creation_records_adult_declared_age_source` must omit the client child ID and use NULL consent refs for the approved synthetic case while retaining its adult-declared age-source assertion. `backend/tests/integration/test_be1_postgres_api.py::test_pending_consent_stays_pending_and_blocks_profile_admission_and_canvas` must be split/rewritten so it continues to prove pending-consent denial for the consent-bound path without requiring the new SYNTHETIC_DEV route to have consent. That integration fixture is tied to a `be1_acceptance` database and cannot run as S1a-T acceptance on `sketch2life_m2_s1a`; cover the new route on the dedicated T integration target instead. Keep the generic eligibility invariant that synthetic data cannot carry effective legal consent.

O4 request/handler impact identified from source: `CreateProfileRequest` currently requires `child_id`; `be1_registry.create_profile` reads it for the profile and related enrollment/audit writes. The candidate edit/test list must remove the client-supplied field, generate one ID before writes, use that same ID for all linked rows and the response, and verify an existing GET-by-child-ID path can consume the returned ID. The existing `GET /api/be1/v1/organizations/{organization_id}/classes/{class_id}/profiles/{child_id}/portfolio` in `be1_records.py` (source around line 402) is the existing lookup path identified for that check; the assertion must distinguish a found profile that reaches the consent guard (`409 CONSENT_NOT_EFFECTIVE`) from a missing profile (`404 PROFILE_NOT_FOUND`) and must not return child data. Candidate test: `backend/tests/integration/test_m2_s1a_teacher_postgres.py::test_server_issued_child_id_resolves_portfolio_lookup_before_consent_guard`. This test file is already listed in §6.3. No new GET route or route behavior change is proposed; the test is not run by this Draft.

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
| Offline baseline before T code | The single source for pre-code offline pytest, strict mypy, Ruff and validator candidates is `plan/M2_BASELINE_RUN_APPROVAL_DRAFT2_20261107.md`. It is still DRAFT; this reference grants no permission. Record every baseline failure verbatim; do not redefine its selection or command here. |
| Offline tests after T code | From cwd `backend`, executable `.venv/Scripts/python.exe`; one pytest invocation, ceiling 1800 seconds, `-p no:cacheprovider`, a new `--basetemp` under `../tmp/M2_S1A_T_20261107/pytest`, and separate stdout/stderr/exit files under `../.claude/handoff/logs/M2_S1A_T_20261107/`. Candidate nodes: `tests/unit/test_profile_age_invariant.py`, `tests/contract/test_be1_synthetic_pilot.py`, `tests/unit/test_age_provenance_columns.py`, `tests/unit/test_synthetic_eligibility.py` excluding only `test_head_counts_by_both_methods_match_the_derived_expectation` (NOT RUN, not PASS), the O7 caller tests listed in §2.4, and new `test_m2_s1a_teacher_service.py` / `test_m2_s1a_teacher_routes.py`. Exact selection must be pinned in the final approval. The composition/OpenAPI modules are handled separately in §3.3. |
| Post-code app composition/OpenAPI tests | From cwd `backend`, executable `.venv/Scripts/python.exe`; one invocation of `tests/contract/test_app_composition.py` and `tests/contract/test_openapi_contract_catalog.py`, ceiling 1800 seconds, only after the owner selects and approves the §3.3 seam. These modules are NOT BASELINEABLE per Baseline Draft 2 §3.1, so an after-code result is not a before/after delta unless the owner separately amends the baseline approval before implementation. |
| PostgreSQL route test | From cwd `backend`, executable `.venv/Scripts/python.exe`; one invocation of only `tests/integration/test_m2_s1a_teacher_postgres.py`, ceiling 1800 seconds, `S1A_T_TEST_DATABASE_URL` plus the real `runtime.engine` identity guard, output/exit captured separately under the same task log directory. Do not include `test_be1_postgres_api.py`: its fixture requires `BE1_TEST_DATABASE_URL` and a database name containing `be1_acceptance`. |
| Inventory | An exact owner field, not a runnable command: owner must pin the `psql` executable, a full read-only SQL body, cwd, one-run ceiling, credential prompt and separate output/exit files. Require `BEGIN READ ONLY`, exact target identity assertions, table inventory and labelled-row counts only. Do not claim the current prose is executable. |
| Post-code mypy | From cwd `backend`, executable `.venv/Scripts/mypy.exe`; one strict package invocation with `--no-incremental` and a new cache under `../tmp/M2_S1A_T_20261107/mypy-cache`, ceiling 900 seconds. Use the capture convention below; do not add a bare duplicate command. |
| Post-code Ruff | From cwd `backend`, executable `.venv/Scripts/ruff.exe`; one `check --select E,F,I,UP,B,SIM` invocation over exact approved paths, ceiling 300 seconds; no format/autofix. |
| Repository checks | From repo root, executable `backend/.venv/Scripts/python.exe` for each of `tools/validate_harness.py`, `tools/validate_repository_security.py`, and `tools/validate_architecture.py`; then `git diff --check`. Each once, each ceiling 300 seconds. No result is implied by this draft. |

For every command invocation above, use `cmd.exe /d /c` from the stated cwd, with executable and file paths interpreted relative to that cwd. Redirect stdout and stderr directly to separate files and record the process exit status in a separate file under the task log directory; do not use a PowerShell pipeline, `Tee-Object`, or transcript. From cwd `backend` the log directory is `../.claude/handoff/logs/M2_S1A_T_20261107/`; from repo root it is `.claude/handoff/logs/M2_S1A_T_20261107/`. These are candidate capture rules, not authorization to run commands.

### 3.3. App/OpenAPI test seam — source-read only, not run

| Source | What the code shows |
|---|---|
| `backend/src/sketch2life/interfaces/http/app.py:238-267` | `create_app` reads Settings and the StoryRun flag; the main demo lifespan is attached only when that flag is `1`. |
| `backend/src/sketch2life/interfaces/http/app.py:731-733` and `backend/src/sketch2life/interfaces/http/be1_runtime.py:96-118` | App composition calls `build_be1_runtime`, which reads the database settings and creates the runtime engine/session factory. |
| `backend/src/sketch2life/infrastructure/persistence/database.py:16-39` | `create_core_engine` calls SQLAlchemy `create_engine` and returns the Engine; this function contains no explicit connect or checkout call. |
| `backend/src/sketch2life/infrastructure/config/settings.py:15-20,117-123` | Settings may read backend/root `.env` files, while process environment values take precedence. No `.env` content was read. |
| `backend/tests/contract/test_app_composition.py` and `backend/tests/contract/test_openapi_contract_catalog.py` | The tests compose the app and inspect OpenAPI; the latter also uses TestClient for docs/OpenAPI requests. This is source inspection, not a runtime result. |

**Source-reading conclusion, not run:** with `STORYRUN_LITE_MAIN_DEMO_ENABLED=0`, the StoryRun main lifespan is not attached. The inspected composition path builds a SQLAlchemy Engine but does not explicitly open a database connection during `create_app`. This conclusion does not prove behavior outside the inspected paths or after code changes.

**Candidate seam for owner decision, not selected:** before starting Python, set process-level `SKETCH2LIFE_ENV=test`, `STORYRUN_LITE_MAIN_DEMO_ENABLED=0` and `SKETCH2LIFE_DATABASE_URL` to a non-secret placeholder PostgreSQL value targeting a closed loopback port. The process variable should override the dotenv fallback; the placeholder pattern is analogous to the offline render in `backend/tests/unit/test_ai_policy_persistence_shape.py:102-118`. The tests must not attempt a connection to that placeholder. If source review cannot establish that no database access is needed, run only in an owner-approved context using `S1A_T_TEST_DATABASE_URL` and the guard on the actual `app.state.be1_runtime.engine` before any write. The owner must choose the seam and its acceptance evidence.

Baseline Draft 2 §3.1 excludes these two modules from pre-code baseline. The required post-code run therefore yields after-only evidence, not a measured before/after delta. Owner options are to accept and report that limitation, or amend the baseline approval before implementation if a comparable pre-code result is required; this Draft does not choose.

The pre-code baseline is owned only by Baseline Run Approval Draft 2. Record any pre-existing red tests verbatim and keep them separate from the S1a-T verdict; do not alter shell, selection or command after a failure to bypass a gate. Under D-156 R1, inventory and offline/mypy baseline after T and before P require a freshly pinned, separately approved owner-run record; this one-use pre-T baseline draft does not authorize a second run.

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

- backend/src/sketch2life/interfaces/http/routers/be1_common.py, backend/src/sketch2life/interfaces/http/routers/be1_records.py, and backend/src/sketch2life/interfaces/http/be1_runtime.py: read to understand shared policy, the existing portfolio lookup, and the actual runtime engine/test seam; no edit.
- backend/src/sketch2life/interfaces/http/router_composition.py and app.py: read-only; current BE1 router is already mounted, so no change is presumed.
- backend/src/sketch2life/infrastructure/identity/firebase_token_verifier.py; application/ports/identity.py; infrastructure/config/settings.py; infrastructure/persistence/database.py, be1_models.py, core_models.py, core_store.py; domain/core_foundation.py; domain/assistance.py; domain/vision_context.py; application/services/vision_analysis.py; infrastructure/assistance/be1_fact_reader.py; domain/child_age.py; application/services/be1_runtime.py.
- backend/alembic/env.py; 20261103_story_upload_compat.py; 20261104_story_revisions.py: read-only.
- Existing tests: test_profile_age_invariant.py, test_synthetic_eligibility.py, test_app_composition.py, test_openapi_contract_catalog.py, `backend/tests/unit/test_ai_policy_persistence_shape.py` (read only as the placeholder-settings pattern example), the O7 caller tests listed in §2.4, `backend/tests/contract/test_learning_content_commands.py` and `backend/tests/unit/test_t2c_digest_pin.py`. `backend/tests/integration/test_be1_postgres_api.py` is read only to inspect its existing fixture and the named pending-consent case; the edit boundary is stated in §6.2 and the fixture may not run for S1a-T. The PostgreSQL fixture and graph-count exclusions in §3.2 apply.
- SRS v2.3, DTR v2.3, M2 Draft 10/11, S1a-T/P Draft 1, D-144/D-148/D-151/D-152/D-154/D-155/D-156 and the pinned S0 inventory.
- Historical artifacts/evidence found by a repository-wide read-only search for the old organization-scoped assignment routes are inventoried in §6.1.1 with occurrence counts and SHA-256. They are read-only drift; no update is approved here.

### 6.1.1. Historical artifacts containing legacy organization-scoped assignment routes — read-only

The search covered feature artifacts and evidence for the old POST/DELETE organization-scoped assignment paths, including the assignment-id suffix where present. It found 19 historical files and 35 matching route references. These records preserve history and do not belong to the S1a-T edit allowlist.

| Historical artifact/evidence path | Matching route references | SHA-256 |
|---|---:|---|
| features/FEAT-063-system-architecture-rearchitecture/artifacts/OPENAPI_FEAT063_REV45_20261101.json | 2 | 352EA298525A36B046D34D90DB97D7C0057F9D026582E52DD002710A56805C05 |
| features/FEAT-063-system-architecture-rearchitecture/artifacts/OPENAPI_FEAT063_REV37_20261030.json | 2 | 764C3915BFF1795E12A70486247B76E76E6DCE077E25116D69D4E1ED312EE8A4 |
| features/FEAT-063-system-architecture-rearchitecture/artifacts/API_INVENTORY_FEAT063_REV31_20261028.md | 2 | 985BFE1625E1C1A7A80BBFB4AF8A6E673787243ADAC7291EAB0CE3AF90AB8E81 |
| features/FEAT-063-system-architecture-rearchitecture/artifacts/API_PURPOSE_CATALOG_FEAT063_REV32_20261028.md | 2 | E65582C197FCF9DC134294D140B5289C44B82E6A81AC6DB6C23C0AFE3800A881 |
| features/FEAT-063-system-architecture-rearchitecture/artifacts/be-full/openapi.runtime.json | 2 | A701C5FF1E429FD74F982F614E355A375B07F85D22440FD658A5EDA7871DAB19 |
| features/FEAT-063-system-architecture-rearchitecture/artifacts/be-full/API_COVERAGE.csv | 2 | 30D9B0D0D4B51014CA71DD27D1999A5AB23E9AA5EDE190043E0F3BB2CE4E2D84 |
| features/FEAT-063-system-architecture-rearchitecture/artifacts/be-full/bruno/requests/organizations-classes/004-create-assignment-api-be1-v1-organizations-organization-id.bru | 1 | 3E6E9C432C9911214FA81EBD0394A32BBB1D24A80280720F4D4AEEE8BE69A76F |
| features/FEAT-063-system-architecture-rearchitecture/artifacts/be-full/bruno/requests/organizations-classes/005-revoke-assignment-api-be1-v1-organizations-organization-id.bru | 1 | B3025EFADB9C36DF1EE1D5B838B0E5FCFEAA081E5E107E53A1471DD67D93C8E1 |
| features/FEAT-063-system-architecture-rearchitecture/evidence/REV34_LEGACY_ROUTE_SMOKE_20261029.csv | 2 | E5DFE58302ED396D2196AD363527902432BC58A1229F57437DE2A3D27C6980ED |
| features/FEAT-063-system-architecture-rearchitecture/evidence/B1_API_CROSSWALK_20261030.md | 2 | E657774B1483B68A35EE8A2CF617113221F0AC43B15447E9A43335D130C17DB8 |
| features/FEAT-063-system-architecture-rearchitecture/evidence/B1_API_CROSSWALK_20261030.csv | 2 | BA017D25C047A3B65EECF6408342D322FA54953E5C78E54100EC8A2BACE4E2FB |
| features/FEAT-063-system-architecture-rearchitecture/evidence/B0_openapi_combined_storage-off_20261030.json | 2 | 252D318DB7F97F94FC81C6483F0B0E56E62DE87036041BEE5E0D85889304DBF1 |
| features/FEAT-063-system-architecture-rearchitecture/evidence/B0_openapi_combined_storage-on_20261030.json | 2 | F139B41B6EBC1EA61CDDEB99003F62D08E17C7DB42CF8BB23959DCAEB417808B |
| features/FEAT-047-be1-runtime-backend/artifacts/openapi-v1.json | 2 | 55ED7B231B28FAF1F5A30345DE279E7E0CD05A94DFC739DCC41006A52ADA3349 |
| features/FEAT-047-be1-runtime-backend/artifacts/API_MAP.md | 1 | 128BA8EFF4437CDB7D1D3E5EF77440EEF87C67926B613DBA4CE4DEEE8152A693 |
| features/FEAT-047-be1-runtime-backend/artifacts/API_CONTRACT.md | 2 | DAB6A73D041B41D31EC4D5A7599BABBAB9B3EA1F25DDDCCF01470CE3F0815994 |
| features/FEAT-058-review2-document-package/evidence/metrics/be2_route_inventory.json | 2 | 4CC2F900AE1054C527E893F31EA4FE9735845EA9E7C9E79637797584E79C77D6 |
| features/FEAT-059-code-structure-cleanup/evidence/metrics/baseline_routes.json | 2 | A0CB85E214E80BED8EE9AEEF665CC9979F579553BD9117D0D8D682DF641AD8F5 |
| features/FEAT-060-classroom-integration-and-review-remediation/evidence/notes/SRS_STAGE_API_TRACEABILITY_20261023.md | 2 | 449A054E25AAF254512DA68783231066776F40B932B5AB8718ADCF9D63360985 |

### 6.2. Candidate existing paths to edit

Only these exact paths are candidates; final hashes and selected edits must be added to Task Approval:
- backend/src/sketch2life/interfaces/http/routers/be1_registry.py
- backend/src/sketch2life/contracts/schemas/be1_runtime.py
- backend/src/sketch2life/domain/core_foundation.py (shared `validate_age_months`; O7 blast radius must be constrained to new values and read behavior reviewed)
- backend/src/sketch2life/application/services/be1_runtime.py is NOT in this edit list; a change to global BE1 policy is out of scope.
- backend/src/sketch2life/interfaces/http/openapi_contract.py
- backend/src/sketch2life/interfaces/http/openapi_contract_amendments.py
- backend/src/sketch2life/interfaces/http/openapi_srs_v22.py
- backend/tests/unit/test_age_provenance_columns.py
- backend/tests/contract/test_be1_synthetic_pilot.py — only the named synthetic-path invariant must be revised to cover the D-155 Q2 path; preserve legal-only route assertions.
- backend/tests/integration/test_be1_postgres_api.py — only `test_pending_consent_stays_pending_and_blocks_profile_admission_and_canvas`, to preserve pending-consent denial for the consent-bound path while removing the assumption that the new synthetic route requires consent; this fixture is not run for S1a-T.
- backend/tests/contract/test_openapi_contract_catalog.py
- backend/tests/contract/test_app_composition.py
- backend/tests/unit/test_assistance_domain.py
- backend/tests/unit/test_assistance_service.py
- backend/tests/unit/test_be1_fact_reader.py
- backend/tests/unit/test_vision_analysis_service.py
- backend/tests/unit/test_vision_analysis_review_fixes.py
- backend/tests/unit/test_vision_context_domain.py
- backend/tests/unit/test_vision_context_service.py

Do not edit test_profile_age_invariant.py unless the unchanged create_profile AST path is actually flagged; if flagged, stop and obtain an explicit approval amendment. Do not edit test_synthetic_eligibility.py for migration-count assertions in T. Do not run test_be1_postgres_api.py under its current `be1_acceptance` fixture; only the named consent case is a candidate edit, and no other test in that file may change without an amendment. Do not edit tools/be1_api_smoke.py; static review found no old assignment-route reference or class/profile mutation there. Do not edit the read-only Bruno/API artifacts in this phase.

### 6.3. Candidate new paths

- backend/tests/unit/test_m2_s1a_teacher_service.py
- backend/tests/contract/test_m2_s1a_teacher_routes.py
- backend/tests/integration/test_m2_s1a_teacher_postgres.py — includes candidate `test_server_issued_child_id_resolves_portfolio_lookup_before_consent_guard` described in §2.3; the assertion must observe `CONSENT_NOT_EFFECTIVE`, not `PROFILE_NOT_FOUND`.
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
| M2-AT-04A | One active Teacher/class and race serialization; zero allowed; second returns 409 `CLASS_TEACHER_EXISTS` without disclosing identity. PARTIAL because capacity and CLASS_CAPACITY_REACHED are NOT COVERED |
| M2-AT-04B | Assigned Teacher creates one synthetic profile/enrollment atomically; school_admin denied. The server-issued `child_id` is then used with the existing class-scoped portfolio GET; the expected `409 CONSENT_NOT_EFFECTIVE` rather than `404 PROFILE_NOT_FOUND` demonstrates lookup before the consent guard, with no child data returned. Candidate test is named in §2.3/§6.3. PARTIAL because expected class revision is NOT COVERED |
| M2-AT-10 | Service/contract/persistence age projection only. No StoryRun route; legacy 121–155 rows not clamped. |
| M2-AT-11 | SYNTHETIC_DEV, null consent refs, synthetic markers, environment/feature gate; REAL and LEGACY_UNCLASSIFIED blocked |

M2-AT-05/06/07 are NOT RUN because S1b is deferred. M2-AT-08/09 and S2 routes are outside T. M2-AT-10 does not call StoryRun. The read isolation of Teacher profiles is NOT RUN per D-148 item 4. Q7 debt: capacity and CLASS_CAPACITY_REACHED, expected class revision, assignment revision in response, idempotency key. Do not mark any of these as passed.

OpenAPI baseline is 129 runtime operations, 124 mounted catalog operations, 111 paths and 18 tags. Under D-157 O1, remove the old POST and DELETE operations and add the new class-scoped assignment POST: expected after T is 128 runtime operations / 123 mounted operations / 110 paths / 18 tags. This follows the current catalog's two legacy operations on two paths, one added operation on one path, and reuse of the existing BE1 tag. Recompute from `openapi_contract.py`, the amendments/SRS catalogs and both route-count tests; any differing count is a stop gate, not an invitation to choose another disposition. P starts from 128/123/110/18 and adds three Parent operations on two paths, so its expected counts are 131/126/112; its tag total remains 18 only if the existing tag is reused, otherwise add one tag and record that still-open owner choice.

## 8. Review finding dispositions

### 8.1. New findings from independent Draft 1 review

| Finding | Draft 3 disposition |
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
| N-12 | §1.2/§6/§7 preserves T→P sequencing and pins the O1-derived count 128/123/110/18; any different observed count stops for review. |
| N-13 | §5/§6 records Bruno/OpenAPI artifacts as read-only legacy drift. |
| N-14 | §2.1 and §7 remove any claim that assignment revision is satisfied; D-144 §9.5 is cited correctly as clarified by D-155 Q8. |
| N-15 | §3.1/§7 counts only rows with approved synthetic prefix and run marker; no row values and no broad cleanup. |
| N-16 | §2.1 records replacing/removing Teacher as debt; O1 removes old assignment POST/DELETE and O3 fixes the second-Teacher 409 code while leaving only body wording open. |
| N-17 | §2.2/§5 scopes SCOPE_DENIED to M2 routes and preserves global/legacy BE1 behavior. |

### 8.2. Review Draft 1 findings P2-01..P2-13 and P3-01..P3-12

| Finding | Status and section in Draft 3 |
|---|---|
| P2-01 | RESOLVED at plan level: insertion is in create_profile; test names are exact; creation-path allowlist stays unchanged unless AST actually reports a new path (§2.3, §6.2). |
| P2-02 | RESOLVED at direction level by D-157 O1: both old routes are removed from router/OpenAPI; no stub or writable alias; removal debt is explicit (§2.1, §6). |
| P2-03 | RESOLVED at direction level: role, class scope, zero/one active rule, lock, no migration and O3 409 code are explicit; only body wording and assignment response remain open (§2.2, §10). |
| P2-04 | RESOLVED at plan level: router/schema/shared age helper, OpenAPI catalogs, route-count tests, composition tests and O7 regression paths are listed (§1.3, §6). |
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
| P3-08 | PARTIAL: O4 fixes server-generated `synthetic-` child ID and removes client input; idempotency remains NOT COVERED and assignment response remains an owner field (§2.3, §10). |
| P3-09 | RESOLVED: only backend/.venv executable is proposed (§3.2). |
| P3-10 | RESOLVED for T: stale graph test is not modified or counted in T; P will update after its root revision (§3.2, §6). |
| P3-11 | RESOLVED: no remote docs branch/fetch/merge (§6). |
| P3-12 | RESOLVED: destructive DB fixture files are excluded from every candidate test set; see stop gate (§9). |

## 9. Stop gates and validity

STOP without retry if any pin/HEAD/index changes; target DB identity differs; a write could touch sketch2life; any unlabelled/unknown rows exist; a test fixture can create/drop a DB; M2 route cannot normalize denial without changing global BE1 behavior; either removed legacy assignment route or its OpenAPI operation remains; a second-Teacher body can identify a person; a generated child ID violates the existing database length constraint or differs across linked rows; changing the shared age validator rejects an existing 121–155 row or changes an unrelated contract without owner disposition; a REAL/LEGACY_UNCLASSIFIED path is reachable; a change needs BE1/Core/Story migration; test writes are not synthetic-labelled; a required path is outside the approved allowlist; route/OpenAPI counts differ from 128/123/110/18; the safe-settings seam attempts a database connection to its closed placeholder or connects to an identity other than sketch2life_m2_s1a; secret or URL appears in output; setup error, crash, timeout, no official test summary, no validator verdict or command ceiling is missing.

Never run integration directories broadly. Known test fixtures with CREATE/DROP DATABASE are backend/tests/integration/ai_jobs/conftest.py, backend/tests/integration/ai_policy/conftest.py, backend/tests/integration/learning_content/conftest.py and backend/tests/integration/be2_cross_lane/test_persisted_video_worker_flow.py. Also exclude backend/tests/integration/ai_jobs/test_migrations.py. The future acceptance must pin exact nodes, not a broad directory.

This Draft does not open S1a-P, S1b, S2, S3 or M3–M6. OWNER_MODAL_CALL_APPROVED=NO. Executor and independent reviewer must be separate sessions. No stage/commit/push/merge is authorized. This document ends at DRAFT.

## 10. Owner fields — leave blank

| Owner field | Status |
|---|---|
| Exact request body and response payload for the new class-scoped assignment route | [ ] Chưa chọn |
| Exact body wording for `CLASS_TEACHER_EXISTS` and route-level `SCOPE_DENIED` while preserving fixed codes/no identity disclosure | [ ] Chưa chọn |
| Random child-ID suffix algorithm/length within existing DB constraint; idempotency key remains NOT COVERED | [ ] Implementation detail / debt |
| Exact split of the named pending-consent PostgreSQL test to preserve REAL/legal denial while covering SYNTHETIC_DEV separately on the approved T target; current fixture cannot target this database | [ ] Implementation detail / test design to pin |
| Secure process-variable ingress without shell history/log; psql executable, SQL body, log path and ceiling | [ ] Chưa chọn |
| Safe-settings seam for post-code app/OpenAPI tests; choose the closed-loopback placeholder or guarded target context, and decide how to report after-only evidence versus a baseline amendment | [ ] Chưa chọn |
| Exact read/edit/new path allowlist with final hashes and command list, including shared-age side-effect boundary | [ ] Chưa chọn |
| Final M2-AT applicability/PARTIAL dispositions, pre-code offline and mypy baseline evidence | [ ] Chưa điền |
| Independent reviewer, owner signature/date and final Task Approval hash | [ ] Chưa điền |

**Approval basis/signature/date:** CHƯA ĐIỀN.
**Final approval hash:** CHƯA CÓ.
**OWNER_MODAL_CALL_APPROVED:** NO.

