# M2 S1a-T Task Approval — Draft 1

**Status: DRAFT — NOT APPROVED, NOT LAUNCHED.** Đây là bản nháp để owner và reviewer xem. Không phải approval; không mở S1a-T và không cấp quyền sửa code, chạy test, ghi DB hay chạy lệnh.

**Owner decision record:** CHƯA ĐIỀN. D-155 ghi hướng S1a-T/S1a-P ngày 2026-11-07; đây là hướng, không phải Task Approval.

**Independent review:** Review Draft 1: NEEDS_REVISION, 0 P1, 13 P2, 12 P3 (phiên chat-only `local_2d0f86ee-4999-485a-b637-c0c48fde225a`). Bản này là đề xuất xử lý; chưa được review.

## 1. Baseline, nguồn và provenance

### 1.1. Checkout và hồ sơ

| Mục | Giá trị tại lúc soạn | Ý nghĩa |
|---|---|---|
| Branch / HEAD | `feature/feat063-be-foundation` / `dd70685eae58aaaefea3e567f5c23d09345a8513` | Baseline nháp; phải ghim lại trước launch |
| Index | Rỗng | Không có staged path |
| Draft S1a gốc | `M2_S1A_TASK_APPROVAL_DRAFT1_20261107.md`, SHA-256 `55A2466D01487D239595BF4FE2E95973A9B57619C629835C8C6358A403CA3625` | Chỉ làm nguồn review; không sửa |
| M2 plan Draft 10 | SHA-256 `7539D642FFD95A9A21C99A0C17C5095FF1443E19538017A92789F631D633E2B1` | Planning baseline theo D-151, không phải approval |
| M2 plan Draft 11 | SHA-256 `6F3EFD72D3A70209B06771AC437998AE241842ABD4F20D11019E6B1166B48A68` | DRAFT, chưa được duyệt để mở pha |
| SRS v2.3-draft | `artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`, SHA-256 `DCBF9786FF8983E34F2D3B4EBAB76301D0C52A6C9DE72CD08D0816BBD0D983FC` | Authority được giữ nguyên; chưa ký |
| DTR v2.3 | `artifacts/DATA_TABLE_REGISTER.md`, working-tree SHA-256 `3E793BB2C62C9E6C50780DE636EDDE442D382C62B4643552F2298AF374171E22` | Authority được giữ nguyên |
| DTR blob LF đối chiếu | SHA-256 `201D381C5025BF6BB5EA2415E916835EB291AFE96CD948D76C0DC5604C28D1B2` | Hash khác do bản blob LF; phải ghi cả hai, không đổi pin nguồn |
| DECISIONS.md | SHA-256 `16F1B6C7EDA309A4E7B62B4F67F086D6B082A5C885C1D2B8FBEE4BE63D59BF89`; có D-155 | Hướng đã ghi; không thay bằng hash cụt trong Draft S1a gốc |
| TASK_APPROVAL.md | SHA-256 `FEEE42E506F94352A8161EFE0B4B94870967072BEDF233285BFDF882352A3DF7` | Có closure S0; chưa có approval S1a-T |
| S0-doc evidence | SHA-256 `1BB71300A6A22487311A8D39EECB0EB1CE2664CB471EC2DAF45DA8DE2E244001` | Đóng trong phạm vi tài liệu theo D-150 |
| S0-owner-run inventory | `.claude/handoff/logs/M2_S0_OWNER_RUN_20261107/inventory.json`, SHA-256 `E4529F541002D840C3F2E1D25F24D00E7B92A65720E3036EB59BA71FD04DB64F` | Owner-run; coordinator đọc artifact, không phải kết nối DB của phiên soạn |

### 1.2. DB và trạng thái nguồn

- D-154 đóng đúng một lượt inventory chỉ đọc trên `sketch2life`, PostgreSQL 17.11 native, localhost:5433. Inventory ghi 117 bảng, 82 hàng tổng, 9 hàng `public.alembic_version`; K3 FAIL vì DB ghi `20261103_story_upload_compat`, còn source có revision `20261104_story_revisions`; schema `story` có năm bảng. K4 source comparison chưa chạy, K5 synthetic-only proof cho 15 hàng baseline chưa có và NOT RUN, K7 mypy NOT RUN.
- Owner báo DB riêng `sketch2life_m2_s1a` đã tạo từ schema-only dump, PostgreSQL 17 native localhost:5433, user `postgres`, 117 bảng, 0 hàng, `alembic_version` trống. Dump `sketch2life-schema-only-20261107.dump` có SHA-256 `E02F2D6E43053FBBACC388002AC9A66FABC73A9AE51399704FB65179BD1BE2E8`. Phiên soạn không kết nối DB; đây là owner report, không phải xác minh độc lập.
- Không có bằng chứng synthetic-only cho toàn bộ 15 hàng ứng dụng baseline của DB chính. Không dùng `sketch2life` cho test ghi; không suy synthetic từ số hàng. DB đích duy nhất được xem xét cho S1a-T là `sketch2life_m2_s1a`.
- D-152 hiệu chỉnh D-144 §9.1: target là PostgreSQL native Windows, không phải Docker; S1a/S2 dùng DB riêng từ schema-only copy cùng instance. D-155 §9.5 tiếp tục cấm migrate DB `sketch2life` và bảng BE1/Core/Story hiện có.
- SRS v2.7 chỉ là ghi chú nháp chưa ký/chưa gộp; v2.3 vẫn là pin. SRS §21.2 dòng 1557–1559 nêu capacity, đúng một Teacher active, expected class revision và enrollment behavior; D-155 Q7 loại các mục cần đổi schema BE1 khỏi S1a-T.

### 1.3. Mã nguồn và test được ghim để review

| Path | SHA-256 lúc soạn | Vai trò |
|---|---|---|
| `backend/src/sketch2life/interfaces/http/routers/be1_registry.py` | `ACB51CA040306198BA5B95F77091717BB73797E80BBA28CDE8C1DB14D97C8A54` | Routes hiện hành; create/revoke assignment, class, profile |
| `backend/src/sketch2life/interfaces/http/routers/be1_common.py` | `40DDE6F9B2AC91A78FE2A2F65B15EFCB1B76D132D49BB5580338710B12B9C45C` | Assignment/denial helpers |
| `backend/src/sketch2life/application/services/be1_runtime.py` | `BD1D57B2E69ABB71F6FB933BF66CC499F36CA8F79D1FE03F6CE99FFD6AEBC3E4` | Application policy |
| `backend/src/sketch2life/infrastructure/persistence/be1_models.py` | `6859CC8313482C70828176B4E12209B485B7D582C6831340AE0D451659219C1E` | Existing BE1 constraints/defaults |
| `backend/src/sketch2life/infrastructure/persistence/core_store.py` | `AB2E86FD002E51A4FDB377644EE376E30AF6E6D888B270C4C1B3646BCB201F94` | Synthetic guard precedent |
| `backend/src/sketch2life/domain/core_foundation.py` | `FFC7B8BBAA1AF2CB0D63479AAA598B74AFD1B4FB4DD58088A5706235A16C19B3` | Existing 36–155 validator; read-only |
| `backend/src/sketch2life/interfaces/http/openapi_contract.py` | `2A5A5DAB4B2CFAECC4F30099E1CD2D862DEBC9CFCE066D623C7CE441C5E7AA81` | Catalog counts, mounted operations |
| `backend/src/sketch2life/interfaces/http/openapi_contract_amendments.py` | `C23BC0C8E9BE6E1989DCDA656588D498F67789EC65D0FE4967C2A64B5E0A2EFC` | Published contract amendments |
| `backend/src/sketch2life/interfaces/http/openapi_srs_v22.py` | `2D07A5D299FFBBA5264247A107065044DE215C156DC50C1431949FFAF3285B11` | OpenAPI SRS catalog |
| `backend/src/sketch2life/contracts/schemas/be1_runtime.py` | `59A2CA1A356916816A788C77E4B03D4FA1A716ECF5CC245B515A39E146B14F11` | BE1 request/response schema |
| `backend/tests/unit/test_profile_age_invariant.py` | `B166C424BC64F35CBB0F1454964F8459FA67B6D956C811C33A854E6B70E76BAB` | Creation-path AST allowlist |
| `backend/tests/contract/test_be1_synthetic_pilot.py` | `03CCBCE40EB3DA13FA15D3C128F22CF70B6AEE4968CF0B726A7ED8B136C74611` | Synthetic/consent behavior |
| `backend/tests/unit/test_age_provenance_columns.py` | `DE1B745B83AE490C4ACAD8F1D457B3CF1E16420B06F79B19DDFF3576BE778C97` | Age provenance contract |
| `backend/tests/integration/test_be1_postgres_api.py` | `49F14546F4A3B6684466CAF7215CE35466548E90AF11E5F1604BE4C343033E0E` | Existing PostgreSQL API tests; fixture currently requires `be1_acceptance` |
| `backend/tests/unit/test_synthetic_eligibility.py` | `B579975452443848A560B89D3CFCA433C5E644EC6CA30165A68D21285E29CBF1` | Synthetic AST and stale migration-count assertions |
| `backend/tests/contract/test_openapi_contract_catalog.py` | `401952E5588C96415B2D275565137C1D4D0A2B795056D39A2B0E962C326B6C40` | Catalog/count assertions |
| `backend/tools/be1_api_smoke.py` | `BDA07ECA4FC63D4EF3D7F14B758F25E3B79AEA92B3CF4C53FAA84D76198582C5` | Existing smoke contract |

Hash này là baseline nháp; final approval phải băm lại mọi path. Không đọc `.env`; không dùng ref ngoài checkout hoặc thay pin SRS.

## 2. Pha và phạm vi đề nghị

**Pha:** S1a-T — Teacher/tổ chức trên bảng BE1 hiện có; không migration. D-155 Q1/Q3/Q4/Q7 được ghi nhận là hướng owner, chưa phải quyền triển khai.

### 2.1. Ba operation và đường tương thích

| Operation | Route đề nghị | Ghi chú |
|---|---|---|
| Tạo lớp | SRS §21.2: `POST /v1/organizations/{org_id}/classes`; mount đề nghị: `POST /api/be1/v1/organizations/{organization_id}/classes` | Giữ prefix và spelling hiện hành theo Q3. SRS yêu cầu kiểm capacity hiệu lực trong transaction; Q7 để capacity/`CLASS_CAPACITY_REACHED` NOT COVERED và cần pha/schema riêng. |
| Gán Teacher | SRS §21.2: `POST /v1/classes/{class_id}/assignments`; mount đề nghị: `POST /api/be1/v1/classes/{class_id}/assignments` | Điểm ghi duy nhất theo F-1; route canonical SRS được mount dưới prefix BE1 theo Q3. Thành công trả assignment revision theo contract, nhưng field/status/error cụ thể còn là ô owner. |
| Tạo Teacher profile/enrollment tổng hợp | SRS §21.2: `POST /v1/classes/{class_id}/profiles`; mount đề nghị giữ route hiện hành `POST /api/be1/v1/organizations/{organization_id}/classes/{class_id}/profiles` | Q3 chỉ đổi assignment route. SRS yêu cầu expected class revision và một enrollment active; expected revision NOT COVERED, enrollment active được kiểm trong transaction. Chỉ synthetic theo Q2; không dùng route để tạo REAL profile. |

SRS §21.2 request/invariant crosswalk: actor Admin tổ chức ở class/assignment được ánh xạ sang role `school_admin` theo D-148; chính xác một Teacher active/class là Q4; Teacher profile phải có trường hồ sơ giới hạn, expected class revision và một enrollment active (expected revision NOT COVERED; field allowlist còn owner). Response class ref / assignment revision / profile-enrollment ref cần được thể hiện trong schema/OpenAPI candidate, nhưng response fields và denial contract chưa owner chốt. Capacity behavior không được tính là đạt.

Route ghi cũ hiện có: `POST /api/be1/v1/organizations/{organization_id}/assignments` và `DELETE /api/be1/v1/organizations/{organization_id}/assignments/{assignment_id}`. Q4 yêu cầu gỡ hoặc chặn quyền ghi qua các route cũ; lựa chọn cụ thể, status/error và OpenAPI representation là ô owner. Không giữ alias writable song song. `create_class` và route Teacher profile được phân biệt khỏi hai assignment route cũ.

### 2.2. Định hướng đã ghi và giới hạn

- F-1: route assignment mới là một điểm ghi duy nhất theo SRS §21.2; `school_admin` là actor theo D-148 item 1. Không tự thêm alias.
- F-2/Q4: tối đa một Teacher active/class; zero Teacher được phép; assignment thứ hai bị từ chối; route khóa dòng `be1_classrooms` trong cùng transaction trước khi kiểm tra/ghi. Không có migration BE1 hoặc unique constraint mới. Schema hiện có unique theo organization/subject/class/role, không chứng minh cardinality này.
- F-4: `school_admin` bị từ chối ở route Teacher profile.
- F-6/Q2: tại handler hiện có `create_profile` trong `be1_registry.py`, nhánh synthetic đề nghị đặt ngay trước truy vấn consent effective và thay điểm dựng `ManagedProfileModel`/`db.add_all`: chỉ tạo `SYNTHETIC_DEV`, `age_source=SYNTHETIC_FIXTURE`, `consent_id=NULL`, `consent_purpose_ref=NULL`, marker synthetic và enrollment cùng transaction; REAL/LEGACY_UNCLASSIFIED bị chặn. Không nới consent guard tổng quát. Không gọi `core_store.create_synthetic_profile` làm route writer vì nó là operator-only và tự commit profile riêng, không tạo enrollment atomically. D-155 xác nhận có chủ ý sửa đúng các test invariant được liệt kê ở §8/P2-01.
- F-7: lưu `SYNTHETIC_DEV`, ghi mapping sang `SYNTHETIC_TEST`; không sửa enum/schema. Biểu diễn API còn là ô owner.
- F-8: chỉ các bảng BE1 hiện có `be1_organizations`, `be1_classrooms`, `be1_organization_assignments`, `be1_enrollments`, `be1_managed_profiles` và phụ thuộc hiện có; không ghi vào Parent tables.
- Q7/NOT COVERED: capacity check và `CLASS_CAPACITY_REACHED`, expected class revision, assignment revision trong response, idempotency key. Không giả vờ đạt SRS §21.2 các phần này, không sửa schema BE1 để thêm chúng.
- F-3/F-5 là nhãn coordinator cho D-148 mục 5–7, không phải ID độc lập. D-148 item 3 giữ FR-C-10/BR-35 ngoài M2; item 4 loại `/v1/me`, `/v1/teacher/profiles`, list/read bổ sung; identity fixture là seed, không phải route.

### 2.3. Ngoài phạm vi

S1a-P/Parent, Parent tables, Alembic, S1b grant/share/consent, M2-AT-05/06/07, S2/StoryRun/AI Jobs, S3, M3–M6, OpenAPI P3, dữ liệu thật, schema BE1/Core/Story hiện có, delete profile và mọi provider/Modal/GPU/mạng.

## 3. DB policy và command ceiling đề xuất

### 3.1. Target và guard

| Trường | Giá trị dự kiến | Provenance/điều kiện |
|---|---|---|
| Database | `sketch2life_m2_s1a` | Owner báo đã tạo; phải xác minh trước mỗi lệnh |
| Instance | PostgreSQL native Windows, major 17 | Owner báo; không Docker |
| Host/port | `localhost:5433`, loopback `127.0.0.1` hoặc `::1` | Không non-loopback |
| User | `postgres` | Owner báo; least-privilege chưa được chứng minh |
| Schema | schema-only copy, 117 bảng, 0 hàng, version table trống theo owner | Chưa được phiên này kiểm qua kết nối |

Không kết nối/đọc/ghi `sketch2life`, không reset/drop/truncate/restore/clone/cleanup. Không tự tạo role. Mọi PostgreSQL test T chỉ được dùng đúng DB target trên; test data phải có prefix synthetic và test-run identifier. Sau suite chấp nhận chỉ còn hàng có nhãn test; không yêu cầu 0 hàng và không cleanup rộng.

Fixture mới phải lấy cấu hình từ biến process riêng `S1A_T_TEST_DATABASE_URL`; không dùng `BE1_TEST_DATABASE_URL`, `SKETCH2LIFE_DATABASE_URL` fallback hoặc `.env`. Fixture fail-closed phải xác minh `current_database() = sketch2life_m2_s1a`, `current_user = postgres`, port 5433, địa chỉ server loopback và major 17 trước mọi ghi. Không log URL/mật khẩu; không yêu cầu owner gửi secret qua chat. Tên biến là đề xuất, owner xác nhận ở approval cuối.

### 3.2. Candidate commands — không được chạy bởi bản nháp này

Mọi command, timeout và số lần dưới đây là đề xuất, không phải cho phép chạy. Future approval phải pin executable, `cwd`, env, log path đã ignore, target guard và command hash.

| Lệnh/công việc | Candidate | Trần đề xuất |
|---|---|---|
| Inventory trước/sau | Một session psql `READ ONLY`; query identity/loopback/version, schemas/tables/counts và `public.alembic_version`; không đọc row values | Mỗi thời điểm 1 lần, 300 giây |
| Offline regression | Tại `cwd=backend`: `.\.venv\Scripts\python.exe -m pytest -q tests/unit/test_profile_age_invariant.py tests/contract/test_be1_synthetic_pilot.py tests/unit/test_age_provenance_columns.py tests/unit/test_synthetic_eligibility.py tests/contract/test_openapi_contract_catalog.py tests/unit/test_m2_s1a_teacher_service.py tests/contract/test_m2_s1a_teacher_routes.py` | 1 lần, 600 giây |
| PostgreSQL route acceptance | Tại `cwd=backend`: `.\.venv\Scripts\python.exe -m pytest -q tests/integration/test_m2_s1a_teacher_postgres.py` | 1 lần, 1800 giây |
| Ruff | Tại `cwd=backend`: `.\.venv\Scripts\ruff.exe check --select E,F,I,UP,B,SIM` trên đúng paths được duyệt | 1 lần, 300 giây |
| Harness/security/architecture | Tại repo root: `& .\backend\.venv\Scripts\python.exe tools\validate_harness.py`; `& .\backend\.venv\Scripts\python.exe tools\validate_repository_security.py`; `& .\backend\.venv\Scripts\python.exe tools\validate_architecture.py`; và `git diff --check` | Mỗi lệnh 1 lần, 300 giây |
| Mypy version/baseline/final | Tại `cwd=backend`: `\.venv\Scripts\python.exe -m mypy --version`; `\.venv\Scripts\python.exe -m mypy --package sketch2life --config-file pyproject.toml --strict --no-incremental --cache-dir ..\tmp\m2-s1a-t\mypy-cache`; redirect stdout/stderr trực tiếp trong `cmd.exe`, không Tee/transcript | Version 1/60 giây; baseline trước code 1/900; final 1/900 |

Mypy baseline phải do owner chạy trước code S1a đầu tiên, ghi executable/version/command/hash output; so sánh trước/sau. Crash/timeout/no verdict là NOT RUN, không PASS. `SKIP`, NOT RUN, setup error, không summary chính thức hoặc timeout không tính PASS. Không dùng Alembic CLI `current --verbose` vì có thể in user/host/port/database; revision hiện tại chỉ đọc bằng psql từ `public.alembic_version` sau target guard.

## 4. K4 — đối chiếu source trước khi sửa

K4 là source-only, không kết nối DB. Đối chiếu inventory D-154 với `be1_models.py`, `core_models.py`, `be1_registry.py`, `be1_common.py`, `be1_runtime.py`, `core_foundation.py`, `core_store.py`, `alembic/env.py`, migration nguồn và tests. Ghi riêng owner observations, source facts, inference và unknowns. K3 mismatch `20261103_story_upload_compat`/`20261104_story_revisions` không được tự sửa hoặc suy ra graph DB đã hội tụ. Nếu route/schema cần sửa bảng BE1 hoặc K4 cho thấy migration/DDL rộng hơn scope: STOP. Evidence path ứng viên: `evidence/M2_S1A_T_K4_SOURCE_RECONCILIATION_20261107.md`, hiện chưa tồn tại và chưa được phép tạo.

## 5. Route contract và behavioral rules

- Principal phải được xác minh; owner, organization, class và role không lấy từ client claims/headers. Test chỉ thay Firebase verification boundary bằng test double; routing, authorization, transactions và PostgreSQL thật.
- Organization route so assignment theo `organization_id`; class route suy organization từ class record. Thiếu assignment, class không có, class khác tenant và org không có quyền phải có cùng denial/status/shape, không lộ existence. Exact code/status còn mở; hiện source có `ADULT_NOT_ASSIGNED`, `IDENTITY_ISSUER_MISMATCH`, `SCOPE_DENIED` và `404 CLASS_NOT_FOUND` sau authz.
- Tạo class/assignment chỉ actor `school_admin`; Teacher profile route chỉ Teacher được phân công. Negative tests cho Platform Admin, Operator, Admin nội dung và `school_admin` trên Teacher route.
- Assignment operation mới chỉ nhận scope đã được owner chọn ở final approval; route cũ không còn quyền ghi theo Q4. Lựa chọn gỡ hay block và response là ô owner, không bịa response code.
- T profile insertion dùng `SYNTHETIC_DEV`, consent refs NULL, marker synthetic; REAL/LEGACY_UNCLASSIFIED bị từ chối. Route hiện tại cần consent `effective`, trong khi `ck_be1_consent_state` chỉ nhận `pending`/`revoked`; không nới consent test tổng quát. Chỉ sửa đúng invariant tests và path mà Q2 cho phép.
- Child/profile ID client cấp hay server cấp chưa được owner quyết; không ghi contract tự chọn. Không dùng `child_age.py`; application layer có đúng một hằng 36–120, không đổi DB check 36–155. Giá trị mới ngoài biên bị từ chối; hàng cũ được giữ nguyên.

## 6. Allowlist ứng viên theo path — chưa có hiệu lực

Nếu cần path khác, dừng và xin approval mới. Không wildcard.

### 6.1. Existing paths — chỉ đọc

`backend/src/sketch2life/infrastructure/identity/firebase_token_verifier.py`; `backend/src/sketch2life/application/ports/identity.py`; `backend/src/sketch2life/interfaces/http/router_composition.py`; `backend/src/sketch2life/interfaces/http/routers/be1_runtime.py`; `backend/src/sketch2life/interfaces/http/routers/be1_registry.py`; `backend/src/sketch2life/interfaces/http/app.py`; `backend/src/sketch2life/infrastructure/persistence/core_models.py`; `backend/src/sketch2life/infrastructure/persistence/be1_models.py`; `backend/src/sketch2life/infrastructure/persistence/core_store.py`; `backend/src/sketch2life/domain/core_foundation.py`; `backend/src/sketch2life/domain/child_age.py`; `backend/src/sketch2life/application/services/be1_runtime.py`; `backend/src/sketch2life/infrastructure/config/settings.py`; `backend/alembic/env.py`; `backend/alembic/versions/20261103_story_upload_compat.py`; `backend/alembic/versions/20261104_story_revisions.py`; `backend/tests/integration/test_be1_age_provenance_postgres.py`; `backend/tests/integration/ai_jobs/test_migrations.py` (chỉ đọc để nhận diện fixture tạo/xóa DB); SRS v2.3, DTR v2.3, Draft 10/11, Draft S1a 1, D-144/D-148/D-151/D-152/D-154/D-155 và S0-owner inventory đã ghim.

### 6.2. Existing paths — candidate sửa, cần final hash

`backend/src/sketch2life/interfaces/http/routers/be1_registry.py`; `backend/src/sketch2life/interfaces/http/routers/be1_common.py` (chỉ nếu exact denial đã được owner chọn); `backend/src/sketch2life/application/services/be1_runtime.py`; `backend/src/sketch2life/contracts/schemas/be1_runtime.py`; `backend/src/sketch2life/interfaces/http/openapi_contract.py`; `backend/src/sketch2life/interfaces/http/openapi_contract_amendments.py`; `backend/src/sketch2life/interfaces/http/openapi_srs_v22.py`; `backend/tests/unit/test_profile_age_invariant.py`; `backend/tests/contract/test_be1_synthetic_pilot.py`; `backend/tests/unit/test_age_provenance_columns.py`; `backend/tests/integration/test_be1_postgres_api.py` (chỉ target fixture/ca synthetic được duyệt); `backend/tests/unit/test_synthetic_eligibility.py` (AST path S1a-T; không sửa phần graph count trong pha T); `backend/tests/contract/test_openapi_contract_catalog.py`; `backend/tools/be1_api_smoke.py` (chỉ contract fixture nếu cần).

### 6.3. New paths — candidate, hiện chưa tồn tại

`backend/tests/unit/test_m2_s1a_teacher_service.py`; `backend/tests/contract/test_m2_s1a_teacher_routes.py`; `backend/tests/integration/test_m2_s1a_teacher_postgres.py`; `features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S1A_T_K4_SOURCE_RECONCILIATION_20261107.md`; `features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S1A_T_IMPLEMENTATION_REPORT_20261107.md`. Không tạo file test/mã/evidence nào khi chỉ có Draft này.

### 6.4. Exclusions

Không sửa `backend/alembic/versions/*`, `backend/src/sketch2life/domain/core_foundation.py`, `child_age.py`, Firebase verifier, `.env`, DB chính, Docker/Compose, SRS/DTR/roadmap/Draft 1–11, DECISIONS, TASK_APPROVAL, STATUS, CONTEXT, SOURCE_REGISTER, FEAT-064 hoặc mọi path ngoài §6.2–6.3. Không chạy `backend/tests/integration/ai_jobs/test_migrations.py`: fixture có thể `CREATE DATABASE`/`DROP DATABASE ... FORCE`.

## 7. Acceptance matrix đề nghị

Chỉ ca được owner tick ở bản approval cuối mới là exit gate.

| ID | Acceptance | Bằng chứng/test candidate |
|---|---|---|
| T-AT-01 / M2-AT-01 | Role hợp lệ/sai, school_admin bị deny trên Teacher profile; Platform Admin/Operator/Admin nội dung deny; không rò data | `test_m2_s1a_teacher_routes.py` + PostgreSQL route test; auth boundary duy nhất được thay bằng double |
| T-AT-02 / M2-AT-02 | No assignment, missing/cross-org class và unauthorized organization cùng denial; server suy org từ class | Service/contract matrix và PostgreSQL thật |
| T-AT-03 / M2-AT-04A | Admin tạo class/assignment; chính xác một Teacher active/class; zero allowed; Teacher thứ hai bị reject; đồng thời hai transaction không tạo hai active Teacher | PostgreSQL race test, row lock trên class row, không BE1 migration |
| T-AT-04 / M2-AT-04B/11 | Teacher được phân công tạo profile/enrollment synthetic; sai role/tenant bị deny; REAL/LEGACY bị chặn; consent refs NULL | PostgreSQL thật; sửa invariant tests theo Q2; marker/run ID |
| T-AT-05 / M2-AT-03 | 35/36/120/121; 36–120 đạt ở app, giá trị mới ngoài biên bị từ chối; không dùng `child_age.py` hoặc đổi DB check | Unit/service/contract và persistence |
| T-AT-06 / M2-AT-10 | Locale/age/revision được serialize; hàng legacy ngoài range không clamp; chỉ service/contract/persistence, không gọi StoryRun route | Unit + persistence; StoryRun behavior không thuộc T |
| T-AT-07 | OpenAPI catalog phản ánh operation/legacy write disposition đã chọn; các con số operation/path được tính lại từ quyết định cuối | `test_openapi_contract_catalog.py`, `openapi_contract.py`; stop nếu count delta ngoài dự kiến |
| T-AT-08 | Test rows đều prefix synthetic + run-id; sau chạy chỉ labelled test rows; không cleanup rộng | Read-only pre/post inventory và fixture guard |

M2-AT-05/06/07 NOT RUN vì S1b DEFERRED; M2-AT-08/09 không thuộc T/S1a; M2-AT-10 chỉ phần service/contract theo D-151 C2. D-151 C1 không cho mặc định `upgrade heads`; C3 `/cancel` placeholder `{id}` thuộc S2; C4 chỉ tests được approval S1a cuối chọn; C5 để S2 Task Approval. FR-C-10/BR-35 và list/read `/v1/me`, `/v1/teacher/profiles` NOT COVERED/ngoài route set.

## 8. Xử lý finding review Draft 1

| Finding | Đề xuất xử lý trong S1a-T |
|---|---|
| P2-01 | Điểm ghi cụ thể là nhánh synthetic của handler `be1_registry.create_profile`, ngay trước consent-effective lookup và tại điểm dựng `ManagedProfileModel`/`db.add_all`, giữ profile + enrollment cùng transaction. Ghi rõ `SYNTHETIC_DEV`, `SYNTHETIC_FIXTURE`, null consent refs và marker synthetic; không tái dùng helper operator-only có transaction riêng. Cập nhật `ALLOWED_CREATION_PATHS` cùng đúng các test `test_profile_age_invariant.py`, `test_be1_synthetic_pilot.py`, `test_age_provenance_columns.py`, `test_be1_postgres_api.py`, `test_synthetic_eligibility.py`; owner đã xác nhận Q2. Không nới consent guard tổng quát. Parent creation AST thuộc S1a-P. |
| P2-02 | Ghi exact routes hiện có/mới và disposition `create_assignment`, `revoke_assignment`, `create_class`, `create_profile`; không writable alias. |
| P2-03 | Ghi roles, role payload, zero/one cardinality, row lock, second-Teacher rejection, route cũ bị gỡ/chặn; no BE1 migration. |
| P2-04 | Allowlist tách rõ read/edit/new ở §6, gồm registry/router composition/runtime, OpenAPI catalog/amendments/SRS catalog, request/response schemas, core foundation, test catalog/eligibility/PostgreSQL và smoke contract. `app.py`/composition chỉ sửa nếu route thực sự cần mount và phải nằm trong candidate edit path; không sửa vì tiện. Stop nếu catalog/count thay đổi ngoài delta owner chọn. |
| P2-05 | Chỉ thay Firebase token-verification boundary bằng test double. Principal subject/issuer, assignment lookup, router, transaction, authorization và PostgreSQL là thật; không `dependency_overrides` cho các dependency đang được kiểm. `VerifiedPrincipal.roles` có thể rỗng và `authorize_adult` hiện xác thực role qua assignment rows, không qua `principal.roles`; test phải ghim đúng seam này. |
| P2-06 | Parent/IDOR thuộc P; T vẫn có admin/Teacher negative tests. D-148 items 3–4 giữ nguyên exclusions. |
| P2-07 | Biến `S1A_T_TEST_DATABASE_URL` đề xuất; fail-closed identity assertion trước write; không settings/.env fallback; secret không log. |
| P2-08 | Thay acceptance 0 rows bằng chỉ test rows có synthetic prefix/run-id; no broad cleanup. |
| P2-09 | Không dùng `alembic current --verbose`; T không chạy Alembic; version read-only chỉ qua target-guard psql. |
| P2-10 | Trace từng mục SRS §21.2 trong §2/§7; capacity, expected revision, assignment revision, idempotency là NOT COVERED/debt theo Q7. |
| P2-11 | Ghi DTR/code ownership; denial code/shape là owner field; Parent columns thuộc P. |
| P2-12 | Ghi commands/ceilings cho harness, security, architecture, Ruff, strict mypy baseline và test; caches/logs chỉ dưới `tmp/`; tests chính thức pinned cuối. |
| P2-13 | Dẫn D-152/D-155; cấm `sketch2life` và bảng BE1/Core/Story hiện có. |
| P3-01 | Dùng đủ SHA-256 64 ký tự từ bảng §1; không hash cụt. |
| P3-02 | Ghi cả DTR working SHA và LF blob SHA; không nhầm khác biệt line ending thành nội dung. |
| P3-03 | Thuộc P: không stamp; không chạy `20261104_story_revisions` hoặc sửa version state. |
| P3-04 | M2-AT-10 service/contract; không dùng `child_age.py`; route StoryRun không chạy. |
| P3-05 | D-148 item 3: profile deletion và FR-C-10/BR-35 NOT COVERED. |
| P3-06 | D-148 item 4: identity fixture là seed, không route; không thêm `/v1/me`, `/v1/teacher/profiles`, extra list/read/delete. |
| P3-07 | Inventory psql candidate dùng PowerShell here-string hợp lệ (`@' ... '@ | & $psql ... -f -`), READ ONLY transaction, hỗ trợ địa chỉ loopback IPv4/IPv6 và tự assert DB/user/port/version trước khi liệt kê. |
| P3-08 | Chưa chọn child/profile ID do client hay server cấp; để owner điền trước approval cuối. |
| P3-09 | Chỉ `backend/.venv` executable; không dùng Python trần. |
| P3-10 | Migration-count assertions thuộc P; static baseline trong test đang ghi 25 và 11/9, nguồn hiện có 28 revisions và 12/9 heads theo đối chiếu kế hoạch; T không chỉnh graph assertions. |
| P3-11 | Remote docs branch thay đổi `story_run_lite` không nằm allowlist; không fetch/merge/đưa vào T. |
| P3-12 | `test_migrations.py` có fixture tạo/xóa DB; nêu rõ loại khỏi mọi command, không được chạy. |

## 9. Exit criteria, stop gates và hiệu lực

S1a-T chỉ được xem xét đóng sau Task Approval cuối được owner ký và review độc lập, K4 T hoàn tất, exact denial/legacy route/ID/contract fields được điền, baseline mypy có verdict, tests được chọn chạy trên đúng DB, kết quả chính thức đủ summary, validator có verdict, evidence/status được owner cập nhật và owner ra quyết định đóng. Draft này tự nó không mở pha.

STOP nếu: pin/HEAD/index lệch; identity DB lệch; DB chính bị chỉ định; target có hàng không synthetic/không rõ nguồn; test có thể tạo/drop DB; phải migrate/ALTER BE1; row-lock không đủ đảm bảo invariant; route cũ còn write; auth dependency bị giả ngoài Firebase boundary; denial lộ tenant; REAL path còn dùng được; consent/schema phải đổi; file ngoài allowlist cần sửa; route/OpenAPI count ngoài delta owner duyệt; lỗi/timeout/crash/setup failure/no summary/validator no verdict; hoặc secret xuất hiện trong output. Không retry, đổi DB/port/shell, cleanup hay dùng skip để đạt xanh.

Không mở S1a-P, S1b, S2, S3, M3–M6. `OWNER_MODAL_CALL_APPROVED=NO`. Không stage/commit/push/merge nếu không có chỉ thị riêng. Phiên triển khai và independent reviewer là hai phiên riêng; không dùng subagent làm reviewer.

## 10. Owner fields và quyết định còn mở

Checkbox nào cũng để trống; owner tự điền ở bản final.

| Owner field | Trạng thái |
|---|---|
| Chọn cách disposition `POST .../organizations/{organization_id}/assignments` và `DELETE .../assignments/{assignment_id}`: remove hay block, status/error/OpenAPI | [ ] Chưa chọn |
| Exact denial HTTP status/code/body; hiện code nguồn có ba mã 403 và 404 sau authz | [ ] Chưa chọn |
| Teacher thứ hai: reject response cụ thể; payload/role của canonical assignment | [ ] Reject direction đã chốt; response/payload chưa chọn |
| Child/profile ID cấp bởi client hay server; duplicate/idempotency behavior | [ ] Chưa chọn |
| API representation của SYNTHETIC_DEV ↔ SYNTHETIC_TEST; cách giới hạn REAL path | [ ] Chưa chọn |
| Cơ chế không consent cho synthetic, chính xác các assertion/test được đổi theo Q2 | [ ] Owner xác nhận trong final approval |
| Age provenance semantics và hằng application 36–120 | [ ] Hướng tuổi có trong D-148; nguồn/provenance còn mở |
| Env var/database guard, owner-run inventory, command/executable/log/cache/ceilings | [ ] Chưa duyệt thực thi |
| T-AT acceptance tick, final file allowlist/hash, reviewer, owner signature/date | [ ] Chưa điền |

**Approval basis/signature/date:** CHƯA ĐIỀN.
**Final approval hash:** CHƯA CÓ.
**OWNER_MODAL_CALL_APPROVED:** NO.
