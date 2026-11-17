# M2 S1a-P Task Approval — Draft 1

**Status: DRAFT — NOT APPROVED, NOT LAUNCHED.** Đây là bản nháp để owner và reviewer xem. Không phải approval; không mở S1a-P và không cấp quyền sửa code, migration, ghi DB hay chạy lệnh.

**Owner decision record:** CHƯA ĐIỀN. D-155 ghi hướng S1a-T/S1a-P ngày 2026-11-07; đây là hướng, không phải Task Approval.

**Independent review:** Review Draft 1: NEEDS_REVISION, 0 P1, 13 P2, 12 P3 (phiên chat-only `local_2d0f86ee-4999-485a-b637-c0c48fde225a`). Bản này là đề xuất xử lý; chưa được review.

## 1. Baseline, nguồn và provenance

### 1.1. Checkout, quyết định và pin

| Mục | Giá trị lúc soạn | Ý nghĩa |
|---|---|---|
| Branch / HEAD | `feature/feat063-be-foundation` / `dd70685eae58aaaefea3e567f5c23d09345a8513` | Baseline nháp; phải ghim lại trước launch |
| Index | Rỗng | Không có staged path |
| S1a Draft 1 gốc | SHA-256 `55A2466D01487D239595BF4FE2E95973A9B57619C629835C8C6358A403CA3625` | Đối tượng review, không sửa |
| M2 plan Draft 10 | SHA-256 `7539D642FFD95A9A21C99A0C17C5095FF1443E19538017A92789F631D633E2B1` | Planning baseline theo D-151 |
| M2 plan Draft 11 | SHA-256 `6F3EFD72D3A70209B06771AC437998AE241842ABD4F20D11019E6B1166B48A68` | DRAFT, chưa phải approval |
| SRS v2.3-draft | SHA-256 `DCBF9786FF8983E34F2D3B4EBAB76301D0C52A6C9DE72CD08D0816BBD0D983FC` | Authority được giữ nguyên; chưa ký |
| DTR v2.3 | working SHA `3E793BB2C62C9E6C50780DE636EDDE442D382C62B4643552F2298AF374171E22`; LF blob SHA `201D381C5025BF6BB5EA2415E916835EB291AFE96CD948D76C0DC5604C28D1B2` | Ghi cả hai line-ending hash; không đổi pin |
| DECISIONS.md | SHA-256 `16F1B6C7EDA309A4E7B62B4F67F086D6B082A5C885C1D2B8FBEE4BE63D59BF89`, có D-155 | Decision direction; không phải approval |
| TASK_APPROVAL.md | SHA-256 `FEEE42E506F94352A8161EFE0B4B94870967072BEDF233285BFDF882352A3DF7` | S0 closed; chưa có S1a-P approval |
| S0-doc evidence | SHA-256 `1BB71300A6A22487311A8D39EECB0EB1CE2664CB471EC2DAF45DA8DE2E244001` | D-150 đóng ở phạm vi tài liệu |
| S0-owner-run inventory | `.claude/handoff/logs/M2_S0_OWNER_RUN_20261107/inventory.json`, SHA-256 `E4529F541002D840C3F2E1D25F24D00E7B92A65720E3036EB59BA71FD04DB64F` | Owner-run; không phải kết nối DB của phiên soạn |

### 1.2. DB và Alembic provenance

- D-154 ghi inventory owner-run trên `sketch2life`, PostgreSQL 17.11 native localhost:5433: 117 bảng, 82 hàng, 9 hàng `public.alembic_version`; K3 FAIL (`20261103_story_upload_compat` trong DB so với source `20261104_story_revisions`); K4 source comparison chưa chạy, K5 synthetic-only proof cho 15 hàng baseline NOT RUN, K7 mypy NOT RUN. Không sửa discrepancy.
- Owner báo DB task-owned `sketch2life_m2_s1a` là schema-only copy từ dump SHA-256 `E02F2D6E43053FBBACC388002AC9A66FABC73A9AE51399704FB65179BD1BE2E8`, PostgreSQL 17 native localhost:5433, user `postgres`, 117 bảng, 0 hàng, `alembic_version` trống. Phiên này không kết nối; các thuộc tính là owner report.
- D-152 chọn DB riêng cùng native instance; D-155 Q8 làm rõ D-144 §9.5 không cấm thêm bảng `parent.*` trong DB task-owned dưới S1a-P Task Approval tương lai. Vẫn cấm migration `sketch2life` và bảng BE1/Core/Story đang có. D-155 Q9 chọn hướng root revision độc lập `down_revision=None`, branch label `parent`, không `depends_on`; không chọn stamp hoặc version table riêng. Chưa có migration approval.
- SRS v2.3 là pin. SRS v2.7 chỉ đối chiếu nháp chưa ký/chưa gộp; không lấy nó làm authority hay đổi contract pin.

### 1.3. Source baseline chính

| Path | SHA-256 lúc soạn | Phạm vi đọc |
|---|---|---|
| `backend/alembic/env.py` | `FABE5736CC7A49CC3C3D36112B4780248113DEEA3DE9A3DA4D2C2CB85E937447` | `_MANAGED_SCHEMAS` hiện chưa có `parent`; offline env vẫn gọi `_database_url()` |
| `backend/src/sketch2life/infrastructure/persistence/core_models.py` | `47D60EEECEF12F583B927BAB7FE3B74B9F19F15231E84E4039187376A502473A` | Metadata nền |
| `backend/src/sketch2life/infrastructure/persistence/be1_models.py` | `6859CC8313482C70828176B4E12209B485B7D582C6831340AE0D451659219C1E` | Không sửa/migrate bảng BE1 |
| `backend/src/sketch2life/infrastructure/identity/firebase_token_verifier.py` | `0B2DEF14F43F80C311F4D0DBC71DD29F90C2E1FC0BA6032DB20B999CAE8287FD` | Auth boundary; test chỉ thay boundary |
| `backend/src/sketch2life/interfaces/http/app.py` | `D9DCBDC5BF3B71840C98BEB50A80D5A7BC1D800C3F93FFBB05DD021E99A995C0` | Composition/route mount candidate cần lý do |
| `backend/src/sketch2life/interfaces/http/router_composition.py` | `E06A158B3616583DF8ABBA21D52C62E769AFA6A9E7C75359D28D424AB15849CC` | Router mounting |
| `backend/src/sketch2life/domain/child_age.py` | `C4A1288A41D6EC52087A9BB83F7F8590D1084C367A41BD512D65ACA917A2838C` | Read-only; Parent không dùng |
| `backend/tests/unit/test_synthetic_eligibility.py` | `B579975452443848A560B89D3CFCA433C5E644EC6CA30165A68D21285E29CBF1` | AST creator allowlist và stale revision count assertions |
| `backend/tests/integration/ai_jobs/test_migrations.py` | `BF1D51D21262C3E76206C9A0FD01EBD3B3FE7006AA0B00DC28109A81C0A9238E` | Chỉ đọc; fixture có thể tạo/xóa DB, bị loại khỏi execution |

Mọi hash phải được kiểm lại ở approval cuối. Không đọc `.env`; không dùng remote branch hoặc fetch.

## 2. Pha và phạm vi đề nghị

**Pha:** S1a-P — ba operation Parent trên `parent.child_profiles` và `parent.profile_revisions`; Alembic chỉ trên `sketch2life_m2_s1a`, chỉ thêm `parent.*`. D-155 Q1/Q5/Q8/Q9 là hướng, chưa cấp quyền thực thi.

### 2.1. Operation và DDL mục tiêu

| Operation | Contract nguồn | Behavior candidate |
|---|---|---|
| Tạo Parent profile | `POST /v1/parent/profiles`, SRS v2.3 §21.2 | Tạo owner theo principal đã xác minh, ghi revision đầu và current revision ref |
| Đọc Parent profile | `GET /v1/parent/profiles/{profile_id}`, SRS §21.2 | Chỉ owner theo principal subject; không trả profile của người khác |
| Sửa Parent profile | `PATCH /v1/parent/profiles/{profile_id}`, SRS §21.2 | Expected revision bắt buộc; append revision bất biến, cập nhật current ref trong cùng transaction |

Prefix mount thực tế cho Parent router là **ô owner mở**; không tự áp `/api/be1/v1` hoặc prefix khác. Không thêm `/v1/me`, `/v1/teacher/profiles`, list/read/delete, share/grant, StoryRun hoặc alias.

DTR v2.3 §5.3, lines 321–322:

- `parent.child_profiles`: PK `parent_profile_id`; owner là principal Firebase đã xác minh; state/timestamps/deleted/current revision ref; Parent sole owner; không merge `be1.managed_profiles`, không FK chéo owner.
- `parent.profile_revisions`: PK `profile_revision_id`; FK nội bộ `parent_profile_id`; `revision_no`, age 36–120, age band ref/version, display name, interests summary, authored_by, created_at, revision hash; unique `(parent_profile_id, revision_no)`, immutable snapshot, không DOB chính xác.
- Không thêm `parent.profile_context_entries`, support needs, data authorizations, share grants hoặc bảng nào khác trong S1a-P.
- DTR không định nghĩa cột `data_origin`/`age_source` cho hai bảng này. F-6 yêu cầu synthetic-only/deny REAL, nhưng cách biểu diễn Parent synthetic và provenance phải được owner điền trước final approval; không tự thêm cột, enum hay consent table.

### 2.2. Phân ranh T/P và phụ thuộc

- S1a-T dùng bảng BE1 hiện có, không migration; S1a-P dùng Parent tables mới. Mỗi pha có Task Approval riêng.
- S1a-P không ghi vào DB `sketch2life`. Chỉ xem xét `sketch2life_m2_s1a` sau owner identity guard.
- Việc S1a-P có thể launch độc lập hay phải chờ S1a-T đóng là **ô owner mở**. Hai pha không chạy song song nếu cùng sửa `app.py`, `router_composition.py`, `test_synthetic_eligibility.py` hoặc shared test/runtime path.
- D-148 item 3: profile deletion, FR-C-10/BR-35 NOT COVERED. Item 4: không `/v1/me`, `/v1/teacher/profiles`, extra list/read; identity fixtures là seed, không phải route. S1b và M2-AT-05/06/07 NOT RUN.

## 3. DB policy, migration strategy và command ceilings

### 3.1. Target guard

| Trường | Giá trị dự kiến | Provenance |
|---|---|---|
| DB | `sketch2life_m2_s1a` | Owner báo schema-only, 117 tables, 0 rows |
| Instance/version | PostgreSQL native Windows, major 17 | Owner report; chưa xác minh trong lượt soạn |
| Host/port | `localhost:5433`, địa chỉ chỉ loopback `127.0.0.1` hoặc `::1` | Không non-loopback |
| User | `postgres` | Owner report; least privilege chưa chứng minh |
| DB chính | `sketch2life` | Tuyệt đối không dùng cho ghi/migration/test |

Biến fixture riêng đề xuất `S1A_P_TEST_DATABASE_URL`; không dùng `BE1_TEST_DATABASE_URL`, settings fallback hoặc `.env`. Test fixture phải fail-closed và kiểm `current_database()`, `current_user`, `inet_server_addr()`, `inet_server_port()`, major 17 trước ghi. Không in URL/mật khẩu. Dữ liệu tạo bởi test chỉ được phép nếu prefix synthetic và run-id; không broad cleanup; acceptance sau chạy là “chỉ còn test rows có nhãn”, không phải 0 rows.

### 3.2. F-9 — strategy đã được owner chọn về hướng, chưa có command approval

- Candidate là revision root độc lập: `down_revision = None`, `branch_labels = ('parent',)`, `depends_on = None`; exact revision ID/file name phải kiểm collision trước approval.
- Alembic source hiện có `_MANAGED_SCHEMAS` không gồm `parent`; `env.py` phải nạp Parent metadata và cho phép schema `parent` theo scope. Offline mode vẫn gọi `_database_url()`; cần giá trị cấu hình local hợp cú pháp nhưng không kết nối. Không ghi URL vào file/log.
- SQL preview offline trước bất kỳ apply nào; owner kiểm SQL chỉ có schema/tables/constraints `parent.*` và `alembic_version` state của branch. Sau review/approval riêng, owner mới apply `upgrade parent@head` trên đúng DB target.
- Không stamp; không version table riêng; không `upgrade heads` mặc định; không upgrade/downgrade StoryRun hoặc BE1/Core. Failure giữ nguyên DB, không auto retry; không downgrade trên DB có data.
- Source test hiện có ghi 25 revision và heads `(11,9)`; static source theo review ghi 28 revision files/12 raw heads/9 dependency-resolved heads. Root mới dự kiến thành 29/13/10 nếu baseline không đổi; trước khi pin assertion phải đối chiếu lại source và dừng nếu con số khác. Việc thêm head ảnh hưởng test ghim head count.

### 3.3. Candidate commands — không được chạy bởi bản nháp

Mỗi command chỉ có hiệu lực nếu owner ký final approval; không dùng command thay thế khi lỗi.

| Giai đoạn | Candidate | Trần đề xuất |
|---|---|---|
| Inventory pre/post | PowerShell here-string truyền vào `psql -X -W -v ON_ERROR_STOP=1 -h localhost -p 5433 -U postgres -d sketch2life_m2_s1a -f -`; trong READ ONLY transaction, tự assert DB/user/port/loopback/version; hỗ trợ `127.0.0.1` và `::1`; đọc bảng/count và `public.alembic_version`, rollback | Mỗi lần 1, 300 giây |
| Source heads | `& .\.venv\Scripts\python.exe -m alembic -c alembic.ini heads --verbose`, `cwd=backend` | 1, 300 giây |
| Offline SQL preview | `& .\.venv\Scripts\python.exe -m alembic -c alembic.ini upgrade parent@head --sql`, `cwd=backend`; dùng setting placeholder local hợp lệ, không kết nối | 1, 300 giây |
| Owner apply | `& .\.venv\Scripts\python.exe -m alembic -c alembic.ini upgrade parent@head`, `cwd=backend`; chỉ sau SQL review và separate approval | 1, 900 giây |
| Offline tests | `& .\.venv\Scripts\python.exe -m pytest -q tests/unit/test_m2_parent_profile_service.py tests/contract/test_m2_parent_profile_routes.py tests/unit/test_profile_age_invariant.py tests/unit/test_synthetic_eligibility.py`, `cwd=backend` | 1, 600 giây |
| PostgreSQL tests | `& .\.venv\Scripts\python.exe -m pytest -q tests/integration/test_m2_s1a_parent_postgres.py`, `cwd=backend`; không tự create/drop database | 1, 1800 giây |
| Ruff / validators | Tại `cwd=backend`: `& .\.venv\Scripts\ruff.exe check --select E,F,I,UP,B,SIM <approved-paths>`; tại repo root: `& .\backend\.venv\Scripts\python.exe tools\validate_harness.py`, `& .\backend\.venv\Scripts\python.exe tools\validate_repository_security.py`, `& .\backend\.venv\Scripts\python.exe tools\validate_architecture.py`, `git diff --check` | Mỗi lệnh 1, 300 giây |
| Mypy | `& .\.venv\Scripts\python.exe -m mypy --version`, rồi `& .\.venv\Scripts\python.exe -m mypy --package sketch2life --config-file pyproject.toml --strict --no-incremental --cache-dir ..\tmp\m2-s1a-p\mypy-cache`, `cwd=backend`; owner-run version/baseline trước code và final sau code, stdout/stderr redirect trực tiếp trong `cmd.exe`, cache/log dưới `tmp/`, không Tee/transcript | version 1/60 giây; baseline/final 1/900 giây |

Không dùng `alembic current --verbose` vì có thể in target identity. Revision hiện hành đọc qua psql sau DB self-check. `backend/tests/integration/ai_jobs/test_migrations.py` tuyệt đối không chạy: fixture có thể `CREATE DATABASE` và `DROP DATABASE ... FORCE`. C1 D-151 cấm mặc định `upgrade heads`. `SKIP`, NOT RUN, crash, timeout, thiếu pytest summary hoặc validator không verdict không phải PASS.

## 4. K4 — source/target reconciliation trước migration

K4 source-only trước sửa; sau đó owner-run read-only inventory target trước migration. So sánh schema-only target với source metadata, `backend/alembic/env.py`, các 28 migration source hiện có và inventory D-154. D-154 K3 mismatch không được sửa bằng migration ngoài `parent.*`. Lập evidence phân biệt owner report, đọc source, inference, chưa xác minh. Parent schema phải vắng hoặc được giải thích trước migration; mọi DDL có thể sửa `public`, `be1_*`, Core, Story hoặc schema ngoài `parent` là STOP. Evidence candidate: `evidence/M2_S1A_P_K4_SCHEMA_SOURCE_RECONCILIATION_20261107.md`, chưa tồn tại.

## 5. Hành vi Parent và acceptance

- Parent là verified principal; owner key là principal subject. Người khác, Teacher, `school_admin`, Platform Admin, Operator và Admin nội dung bị deny nếu không sở hữu; không lộ việc profile có tồn tại. Test chỉ thay Firebase verifier boundary bằng double; router, authz, transaction, repository và PostgreSQL thật.
- POST tạo profile và revision đầu; GET chỉ owner; PATCH yêu cầu expected revision và append immutable revision; profile current pointer cập nhật atomically. Thêm IDOR tests cho Parent khác và role khác.
- Dùng một hằng application-level 36–120; không dùng `child_age.py` (0–107); không lưu DOB. 35/121 giá trị mới bị từ chối, 36/120 chấp nhận; không clamp/viết lại legacy rows.
- F-6 synthetic-only: không nhận REAL/LEGACY_UNCLASSIFIED. DTR không có origin/age_source columns nên representation, ID/name markers, API mapping và chính sách seed là ô owner blocking; không tự thêm cột.
- M2-AT-03 và phần Parent của M2-AT-01/10 thuộc S1a-P. M2-AT-10 chỉ service/contract/persistence; không gọi StoryRun route theo D-151 C2. AT-05/06/07 S1b NOT RUN; AT-08/09 S2 ngoài scope. NFR-36/38 vẫn PARTIAL; không claim full acceptance.

## 6. Allowlist ứng viên — chưa có hiệu lực

### 6.1. Existing paths — chỉ đọc

`backend/src/sketch2life/infrastructure/identity/firebase_token_verifier.py`; `backend/src/sketch2life/application/ports/identity.py`; `backend/src/sketch2life/interfaces/http/app.py`; `backend/src/sketch2life/interfaces/http/router_composition.py`; `backend/src/sketch2life/interfaces/http/routers/be1_runtime.py`; `backend/src/sketch2life/interfaces/http/routers/be1_registry.py`; `backend/src/sketch2life/infrastructure/config/settings.py`; `backend/src/sketch2life/infrastructure/persistence/core_models.py`; `backend/src/sketch2life/infrastructure/persistence/be1_models.py`; `backend/src/sketch2life/domain/child_age.py`; `backend/alembic/env.py`; 28 revision source files with exact path/hash in §6.1.1; `backend/tests/unit/test_profile_age_invariant.py`; `backend/tests/unit/test_age_provenance_columns.py`; `backend/tests/unit/test_synthetic_eligibility.py`; `backend/tests/integration/ai_jobs/test_migrations.py` (read-only only, identify destructive fixture); SRS v2.3, DTR v2.3, Draft 10/11, D-144/D-148/D-151/D-152/D-154/D-155, S0 inventory.

#### 6.1.1. Migration source read-only pins at draft time

| Path | SHA-256 |
|---|---|
| `backend/alembic/versions/20261014_0001_core_persistence.py` | `55F415847B3E8AB5A96023CFC58C9C229056213AF92690865CF70F728290535C` |
| `backend/alembic/versions/20261014_0002_be1_runtime.py` | `08014F5F5CD8A48FC21102090776128712EDEA1D04703853F9A0CC78CADAC520` |
| `backend/alembic/versions/20261014_0003_canvas_payload.py` | `194A831C661CA84C796557CCCF762715F6C0CC0E747521D588D1F30E1A5BB9E5` |
| `backend/alembic/versions/20261014_0004_be1_constraint_names.py` | `AB15DFCE0738D994B14B337A03B34F7365BBBC67AFFE3BB01F24901F87BAFFFD` |
| `backend/alembic/versions/20261015_ai_0001_ai_jobs_schema.py` | `D86BD759FCB5DC644C94007FCA3650C6315903EC39EE4DA99579C4E23E656714` |
| `backend/alembic/versions/20261017_ap_0001_policy_lifecycle.py` | `81F84E9B3C4C7929018EB0A82ABED1DC2581811BB178EC6097E3134BBD8D765A` |
| `backend/alembic/versions/20261017_ap_0002_effective_scope.py` | `35DBAA33A4F41EC69A01E03D688AF9B9238145EE0006D54CA67C115D0987CDE7` |
| `backend/alembic/versions/20261017_ap_0003_resource_ledger.py` | `FEE3A90E27691B90B1D45E6DE7D14C3DB77311EBE86414051B55C75D02AB1924` |
| `backend/alembic/versions/20261017_ap_0004_copy_inventory.py` | `3EC8747A198941C9C4B36C4FDD0E08986355F0B2334589951EEA99BBF20AC2E7` |
| `backend/alembic/versions/20261017_ap_0005_copy_evidence.py` | `9E364BF938C2D6B6714FDE8C2A2527AAB84D3DD378C1AE16C0578FD86B9B8C12` |
| `backend/alembic/versions/20261017_lc_0001_content_publication.py` | `DA2B372442A7CF234B8C1FC0FC7472B5A068FE8F832B6465C1BC1E4D2FE2F498` |
| `backend/alembic/versions/20261018_ap_0006_copy_operations.py` | `B266744B3792E0E68347FA674B374A54D14CC33E4776106ADE91E2E407C447F7` |
| `backend/alembic/versions/20261018_ap_0007_copy_delivery.py` | `3BF400A165F5D681017FFE1AADEEAEB724BFFF5992289FB21331F5247C479E52` |
| `backend/alembic/versions/20261018_ap_0008_delivery_authority.py` | `9D8171F8B00C603FD350E32B6D6412B049A504F47B4D4F92355D654C86B71E05` |
| `backend/alembic/versions/20261018_ap_0009_copy_resolution.py` | `465A3421BC54895D2969AE95B1E3A9425689D1ED38B1CD6BCD8FE29D9B961A44` |
| `backend/alembic/versions/20261018_kv_0001_knowledge_video.py` | `E7EFE124ECBFC5D1E280529DBA3B05EB2B00DCE04C24BF9EAC11BCE516B15D87` |
| `backend/alembic/versions/20261018_vr_0001_video_review.py` | `3E489443949C0934B414E4A69C6BD01B09782F4653042803C79291D66B415FC7` |
| `backend/alembic/versions/20261019_ae_0001_activity_execution.py` | `56993DC8CE1507D471ED3E3052F99A3A05B9D26C64E979822198946CD9EF9C30` |
| `backend/alembic/versions/20261019_pa_0001_preset_automation.py` | `D2A8B958D6BD9411D040E3358F5568E2C728C1095D5395D55532916ACC5182E8` |
| `backend/alembic/versions/20261019_vf_0001_video_failure.py` | `0520CB0EB850D1BB4A267571F30937677908E505B77E221D1F0C90EE806FD178` |
| `backend/alembic/versions/20261024_0005_classroom_srs_contracts.py` | `E533FC15447222C334A82CD162DC01FEB7B94221B402552D774CBD11E7D7289C` |
| `backend/alembic/versions/20261028_ll_0001_lesson_library.py` | `733836723A95834C721E6CD0CA3527D73EA6EFE089B2F109A956EA484DFE1D83` |
| `backend/alembic/versions/20261031_be1_synthetic_eligibility.py` | `421F695FE49193C4A2EDCAC66B4461D8AFCB47B825813918E0083B21BC1483FC` |
| `backend/alembic/versions/20261101_be1_age_provenance.py` | `2A634DC4DDF00326AFEF4079F7795A185D458DE2DB65BA6FD3C40291BBA5614E` |
| `backend/alembic/versions/20261102_pilot_vision.py` | `6335AD224708AEC8251447A296458854B663FC7DD763EFB184E4AFF156E86BD9` |
| `backend/alembic/versions/20261102_story_run_lite.py` | `D5E5F85EA3A7545538D6F1DE1E17D3869FD9AA7A543F870EAD54297F70D6E143` |
| `backend/alembic/versions/20261103_story_upload_compat.py` | `F16346F5D0D320B22AF0767F387FE066ED3683D57DDD380804424B5A837CA166` |
| `backend/alembic/versions/20261104_story_revisions.py` | `3618BEF0ECCB0E01EE61F65E1065F7AE8EA6297FE0781D965588614D0F1C37F8` |
### 6.2. Existing paths — candidate sửa

`backend/alembic/env.py`; `backend/src/sketch2life/interfaces/http/app.py`; `backend/src/sketch2life/interfaces/http/router_composition.py`; `backend/src/sketch2life/interfaces/http/openapi_contract.py`; `backend/src/sketch2life/interfaces/http/openapi_contract_amendments.py`; `backend/src/sketch2life/interfaces/http/openapi_srs_v22.py`; `backend/tests/unit/test_profile_age_invariant.py` (only add Parent creator AST path); `backend/tests/unit/test_synthetic_eligibility.py` (Parent creator AST and exact graph counts after new root); `backend/tests/contract/test_openapi_contract_catalog.py` (Parent operations only if route is catalogued). No edits to BE1 model/migrations or `backend/tests/integration/ai_jobs/test_migrations.py`.

### 6.3. New paths — candidate, hiện chưa tồn tại

`backend/src/sketch2life/domain/parent_profile.py`; `backend/src/sketch2life/application/ports/parent_profiles.py`; `backend/src/sketch2life/application/services/parent_profiles.py`; `backend/src/sketch2life/contracts/schemas/parent_profiles.py`; `backend/src/sketch2life/infrastructure/persistence/parent_models.py`; `backend/src/sketch2life/infrastructure/persistence/parent_repository.py`; `backend/src/sketch2life/interfaces/http/routers/parent_profiles.py`; `backend/alembic/versions/20261107_m2_parent_profiles.py` (candidate name, check collision); `backend/tests/unit/test_m2_parent_profile_service.py`; `backend/tests/contract/test_m2_parent_profile_routes.py`; `backend/tests/integration/test_m2_s1a_parent_postgres.py`; `features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S1A_P_K4_SCHEMA_SOURCE_RECONCILIATION_20261107.md`; `features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S1A_P_IMPLEMENTATION_REPORT_20261107.md`.

### 6.4. Exclusions

Không sửa `backend/src/sketch2life/infrastructure/persistence/be1_models.py`, Core/Story/BE1 migration, `backend/alembic/versions/20261103_story_upload_compat.py`, `backend/alembic/versions/20261104_story_revisions.py`, `.env`, DB `sketch2life`, `test_migrations.py`, SRS/DTR/roadmap/Draft 1–11, decisions/approvals/status/context/source register, FEAT-064, provider/Modal/Docker hoặc path ngoài §6.2–6.3. Không sửa remote docs branch/StoryRun-lite.

## 7. Acceptance matrix đề nghị

| ID | Acceptance | Candidate evidence |
|---|---|---|
| P-AT-01 / M2-AT-01 | Owner Parent đọc/sửa đúng subject; roles khác deny; error không lộ existence; IDOR owner mismatch | Route contract + PostgreSQL wiring thật |
| P-AT-02 / M2-AT-03 | 35/36/120/121; 36–120 app-level; immutable age/profile revisions; no DOB/child_age | Service/unit/contract và PostgreSQL persistence |
| P-AT-03 / M2-AT-10 | Serialize/persist/read revision; service/contract only, không gọi StoryRun route | Unit/contract/PostgreSQL |
| P-AT-04 / F-6 | REAL/LEGACY deny; chỉ dữ liệu synthetic theo representation owner chốt; test rows synthetic prefix/run-id | Route + DB; không PASS nếu representation chưa được quyết |
| P-AT-05 / F-8/F-9 | DDL tạo đúng hai Parent tables trong schema parent; immutable revision uniqueness/FK; không DDL hiện có bị đổi | Offline SQL review, owner apply, pre/post inventory |
| P-AT-06 | Alembic branch parent độc lập; source graph/head assertion cập nhật chính xác; test không tạo/drop DB | Static graph test và Alembic target-only evidence |
| P-AT-07 | OpenAPI phản ánh đúng ba operation Parent, prefix owner đã điền | Catalog/route test |

Không nhận M2-AT-04A/04B của Teacher là P acceptance. Tất cả persistence tests phải dùng DB task-owned; không monkeypatch repository, routing, authz, transaction hoặc PostgreSQL. Chỉ Firebase verification boundary được thay. Test rows có nhãn; không cleanup rộng.

## 8. Xử lý finding review Draft 1

| Finding | Đề xuất xử lý trong S1a-P |
|---|---|
| P2-01 | Parent creator là creation path mới; cập nhật `ALLOWED_CREATION_PATHS` và AST test chỉ cho Parent route/service thực sự ghi; T-side create_profile invariant thuộc S1a-T. Không bỏ test guard. |
| P2-02 | Teacher route và legacy assignment disposition thuộc S1a-T; P không thêm alias hay route ngoài ba Parent operations. |
| P2-03 | Role cardinality/row lock thuộc S1a-T. |
| P2-04 | Thêm đủ exact Parent model/port/service/schema/repository/router/migration/test/env/composition paths; `app.py` không tự động candidate nếu không cần mount. |
| P2-05 | Chỉ Firebase token-verification boundary được thay bằng test double; subject/issuer, router, authorization, transaction và PostgreSQL là thật. `VerifiedPrincipal.roles` có thể rỗng; policy hiện kiểm role qua assignments, không qua `principal.roles`; không override dependency đang được kiểm. |
| P2-06 | Định nghĩa Parent là verified principal theo subject; thêm IDOR và denial cases; admin/system roles deny. Exact error code vẫn owner field. |
| P2-07 | Biến `S1A_P_TEST_DATABASE_URL`; fixture không fallback sang `.env`/BE1 var; xác minh identity/loopback/major trước ghi. |
| P2-08 | Chỉ test rows synthetic prefix + run-id; thay gate 0 rows thành only-labelled-test-rows; no broad cleanup. |
| P2-09 | Bỏ `alembic current --verbose`; đọc `alembic_version` qua guarded psql; chỉ `heads --verbose` cho source graph; interpreter là `backend/.venv`. |
| P2-10 | Trace Parent request/response, expected revision, ownership và NOT COVERED fields; không claim class capacity/assignment response/idempotency vì thuộc T/Q7. |
| P2-11 | DDL Parent bám DTR lines 321–322; không tự thêm data_origin/age_source; tenant denial shape và synthetic representation là owner fields. |
| P2-12 | §3.3 pin offline/PostgreSQL pytest node sets, Alembic source-head/offline-preview/owner-apply calls and ceilings; Ruff uses `check --select E,F,I,UP,B,SIM`; harness/security/architecture validators and `git diff --check` run once each; strict mypy version/baseline/final uses the backend venv, direct stdout/stderr capture, and a `tmp/` cache/log. `test_migrations.py` remains forbidden. |
| P2-13 | Dẫn D-152/D-155; Alembic chỉ trên `sketch2life_m2_s1a`, chỉ parent.*, không DB chính/bảng hiện có. |
| P3-01 | SHA-256 đủ 64 ký tự; final approval rehash tất cả. |
| P3-02 | Ghi cả working DTR hash và LF blob hash; không nhầm line endings thành semantic change. |
| P3-03 | Q9 không chọn stamp; không chạy/story stamp `20261104_story_revisions`; branch mới chỉ parent. |
| P3-04 | AT-10 là service/contract/persistence; không dùng `child_age.py` và không gọi StoryRun route. |
| P3-05 | D-148 item 3: profile deletion và FR-C-10/BR-35 NOT COVERED. |
| P3-06 | D-148 item 4: không `/v1/me`, `/v1/teacher/profiles`, extra list/read/delete; identity fixtures là seed, không public route. |
| P3-07 | psql candidate dùng PowerShell here-string hợp lệ, loopback `127.0.0.1`/`::1`, tự assert current DB/user/port/version trước inventory. |
| P3-08 | Client/server ID choice thuộc Teacher profile S1a-T; Parent profile key/subject ownership không lấy owner từ client. |
| P3-09 | Chỉ `backend/.venv` Python/Alembic; không Python trần. |
| P3-10 | Ghi đúng baseline test lỗi thời: 25/(11,9) so với static 28/12/9; branch parent dự kiến thêm một revision/head; cập nhật assertion chính xác và dừng nếu graph thay đổi. |
| P3-11 | Remote docs branch thay StoryRun-lite ngoài phạm vi; không fetch/merge, không allowlist. |
| P3-12 | `test_migrations.py` có fixture CREATE/DROP DATABASE FORCE; cấm chạy và không dùng làm acceptance. |

## 9. Exit, stop gates và hiệu lực

S1a-P chỉ được xem xét đóng sau Task Approval riêng được review độc lập và owner ký; S1a-P dependency được quyết; K4 source/target đạt; F-6 provenance, route prefix, denial response và tuổi được điền; offline SQL được owner review; migration được giới hạn parent.*; target pre/post inventory đủ; tests và validators có verdict thật; evidence được lập; owner ra quyết định đóng. Bản nháp không mở pha.

STOP nếu: pin/HEAD/index đổi; target identity/loopback/version sai; DB chính bị chỉ định; row không synthetic/không rõ nguồn; K3 bị định sửa ngoài parent; K4 thiếu/mismatch; offline SQL có DDL ngoài parent; migration cần sửa BE1/Core/Story; version baseline không rõ; branch label/revision collision; fixture tạo/drop DB; need real data/consent/share; F-6 representation chưa owner quyết; denial lộ existence; test auth/repository/PostgreSQL bị giả; timeout/crash/no summary/no verdict; secret/URL lộ; hoặc cần path ngoài allowlist. Giữ nguyên DB khi lỗi; không retry/restore/downgrade/cleanup tự động.

Không mở S1a-T, S1b, S2, S3, M3–M6. `OWNER_MODAL_CALL_APPROVED=NO`. Không stage/commit/push/merge. Reviewer và executor phải là hai phiên độc lập; không dùng subagent làm reviewer.

## 10. Owner fields và quyết định còn mở

Checkbox để trống; owner tự điền tại approval cuối.

| Owner field | Trạng thái |
|---|---|
| S1a-P được bắt đầu độc lập hay chỉ sau S1a-T đóng; không chạy song song nếu shared path overlap | [ ] Chưa chọn |
| Parent route prefix thực tế/mount và OpenAPI prefix | [ ] Chưa chọn |
| Synthetic-only representation cho Parent khi DTR không có `data_origin`/`age_source`; deny REAL/LEGACY bằng cơ chế nào | [ ] Blocking, chưa chọn |
| Age provenance semantics; có/không cột mới; không thêm cột nếu chưa duyệt | [ ] Chưa chọn |
| Exact denial status/code/body cho tenant/IDOR | [ ] Chưa chọn |
| Exact request/response field limits, profile/revision IDs, hash serialization và idempotency | [ ] Chưa chọn |
| K4 evidence target identity, restore/rollback và synthetic proof | [ ] Chưa xác minh; owner điền |
| Alembic revision ID/file collision, branch-head expectation, offline SQL output path/hash | [ ] Chưa pin |
| Process-local test env, psql executable, Python executable, ceilings, cache/log path | [ ] Chưa duyệt |
| P-AT tick, final exact read/edit/new allowlist + hashes, reviewer, owner signature/date | [ ] Chưa điền |

**Approval basis/signature/date:** CHƯA ĐIỀN.
**Final approval hash:** CHƯA CÓ.
**OWNER_MODAL_CALL_APPROVED:** NO.
