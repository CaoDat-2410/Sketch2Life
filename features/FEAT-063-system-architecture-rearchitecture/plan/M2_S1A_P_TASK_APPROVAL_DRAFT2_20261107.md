# M2 S1a-P Task Approval — Draft 2

**Status: DRAFT — NOT APPROVED, NOT LAUNCHED.** Bản này tiếp thu review Draft 1 và ghi các hướng owner đã chốt. Đây không phải Task Approval, không mở S1a-P và không cấp quyền sửa mã, migration, ghi database hay chạy lệnh.

**Owner decision record:** D-156 ghi hướng R1–R8; đây là direction, không phải implementation approval. Các ô owner, allowlist cuối và command ceiling vẫn cần được hoàn tất trong Task Approval riêng.

**Independent review of Draft 1:** NEEDS_REVISION, 0 P1 / 5 P2 / 10 P3; chat-only session `local_4989fa51-2bfb-4247-a10a-5a50d7ba8217`. Bản Draft 1 trước đó có một nhận xét review khác; báo cáo này theo phiên review độc lập được chỉ định ở D-156. Draft 2 chưa được review độc lập.

## Thay đổi từ Draft 1 sang Draft 2

| Phần Draft 1 | Thay đổi ở Draft 2 | Cơ sở |
|---|---|---|
| Trạng thái, decisions, dependency | Ghim D-156; S1a-T phải hoàn tất trước S1a-P trên cùng DB; inventory và mypy baseline được tính lại giữa hai pha; không chạy song song | D-156 R1 |
| Parent identity và routes | POST cho mọi principal đã xác minh, owner theo subject; GET/PATCH chỉ owner, IDOR không tiết lộ tồn tại; không giả định deny role ở POST | D-156 R4; review P2-N2 |
| DB và migration guard | Thêm guard target `current_database()` trước DDL, `CREATE SCHEMA parent` không `IF NOT EXISTS`; fixture dùng biến riêng và kiểm identity trên engine app thật; nêu khoảng trống nếu guard chỉ chạy trong migration `upgrade()` | D-156 R5; review P2-N3 |
| Parent schema và synthetic provenance | Thêm `data_origin` vào `parent.child_profiles` với CHECK `SYNTHETIC_DEV`, ghi đây là deviation giới hạn M2; không thêm cột khác; tách riêng các chi tiết DDL chưa được quyết | D-156 R6; review P2-N1 |
| Age bounds | CHECK DB và application 36–120 cho Parent; không đổi BE1 36–155 | D-156 R7 |
| OpenAPI và test composition | Thêm `test_app_composition.py`, runtime/common read paths, catalog test và số đếm; route mount/tag là ô owner | Review P2-N4, P3-N10 |
| Alembic SQL, tests, findings | Phân biệt SQL preview với apply, ngoại lệ `alembic_version`, cập nhật graph count sau root revision; ghi mapping finding cũ/mới và các test destructive bị loại | Review P3-N6..N15; Draft 1 findings |
| Acceptance và owner fields | Bỏ các nhãn P-AT mới; chỉ dùng M2-AT đã có; bổ sung các ô owner còn mở và stop gates | Review P3-N10; D-148/D-156 |

## 1. Baseline, nguồn và provenance

### 1.1. Checkout, hồ sơ và pins

| Mục | Giá trị lúc soạn | Ý nghĩa |
|---|---|---|
| Branch / HEAD | `feature/feat063-be-foundation` / `dd70685eae58aaaefea3e567f5c23d09345a8513` | Baseline của bản nháp; ghim lại trước Task Approval |
| Index | Rỗng | Không có staged path |
| S1a-P Draft 1 | SHA-256 `2875C0A5F25657BDCE2645CF2733FA0B5E52E4EE9EF9544C19C6AAA697400C58` | Đối tượng review, không sửa |
| S1a-T Draft 1 | SHA-256 `160511C0FF3643D7C53BDDB1AFBE974B38BF98DADBE4C8160B18943A676B7769` | Pha phải chạy trước theo R1 |
| S1a-T Draft 2 | SHA-256 `B18188217E4962E59C183463956DEF4FEECEEF6E7F81E2F69B1229027B249C39` | Bản nháp hiện tại; chưa được review/owner chấp nhận |
| S1a Draft 1 ban đầu | SHA-256 `55A2466D01487D239595BF4FE2E95973A9B57619C629835C8C6358A403CA3625` | Nguồn lịch sử, không sửa |
| M2 Draft 10 | SHA-256 `7539D642FFD95A9A21C99A0C17C5095FF1443E19538017A92789F631D633E2B1` | Planning baseline D-151 |
| M2 Draft 11 | SHA-256 `6F3EFD72D3A70209B06771AC437998AE241842ABD4F20D11019E6B1166B48A68` | DRAFT, không mở pha |
| SRS v2.3-draft | `artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`; SHA-256 `DCBF9786FF8983E34F2D3B4EBAB76301D0C52A6C9DE72CD08D0816BBD0D983FC` | Contract authority giữ nguyên; chưa ký |
| DTR v2.3 | `artifacts/DATA_TABLE_REGISTER.md`; working SHA-256 `3E793BB2C62C9E6C50780DE636EDDE442D382C62B4643552F2298AF374171E22`; LF blob SHA-256 `201D381C5025BF6BB5EA2415E916835EB291AFE96CD948D76C0DC5604C28D1B2` | Ghi cả hai hash do line ending; không đổi pin |
| DECISIONS.md | SHA-256 `73E7E11F7F3B75F966E9A844D573129B66AE772D4821132F09C0242592751971`; có D-156 | Direction, không phải approval |
| TASK_APPROVAL.md | SHA-256 `FEEE42E506F94352A8161EFE0B4B94870967072BEDF233285BFDF882352A3DF7` | S0-owner-run đã đóng; chưa có S1a-P approval |
| S0-doc evidence | SHA-256 `1BB71300A6A22487311A8D39EECB0EB1CE2664CB471EC2DAF45DA8DE2E244001` | Đóng ở phạm vi tài liệu theo D-150 |
| S0-owner-run inventory | `.claude/handoff/logs/M2_S0_OWNER_RUN_20261107/inventory.json`; SHA-256 `E4529F541002D840C3F2E1D25F24D00E7B92A65720E3036EB59BA71FD04DB64F` | Owner-run; không phải kết nối DB của phiên soạn |

Các pins cần được tính lại trước approval cuối. Không đọc `.env`; không dùng `fetch`, nhánh remote chưa được ghim, hoặc DB connection trong lượt soạn.

### 1.2. Quyết định và trạng thái DB

- D-152 chọn DB task-owned riêng cùng instance PostgreSQL native. D-155 Q8 làm rõ D-144 §9.5 không cấm thêm `parent.*` trong DB task-owned dưới approval S1a-P riêng; vẫn cấm migration vào `sketch2life` và các bảng BE1/Core/Story hiện có. D-155 Q9 chọn revision root độc lập `down_revision=None`, branch label `parent`, không `depends_on`; không stamp và không version table riêng.
- Theo owner report trước S1a-T, `sketch2life_m2_s1a` là schema-only copy từ dump SHA-256 `E02F2D6E43053FBBACC388002AC9A66FABC73A9AE51399704FB65179BD1BE2E8`, PostgreSQL 17 native tại `localhost:5433`, user `postgres`, 117 bảng, 0 hàng và `alembic_version` trống. Đây là trạng thái được báo trước khi T chạy, không phải trạng thái hiện tại đã xác minh.
- R1 yêu cầu S1a-T chạy trước S1a-P trên cùng database, không song song. Sau T, người chạy phải lập inventory mới, ghi những hàng test T còn lại theo nhãn, và lấy mypy baseline mới trước khi P code bắt đầu. Không áp lại giả định 117 bảng/0 hàng/version table trống nếu inventory mới không xác nhận.
- Các đường dùng chung cần khóa theo thứ tự này gồm `router_composition.py`, `openapi_contract.py`, `openapi_contract_amendments.py`, `openapi_srs_v22.py`, `test_openapi_contract_catalog.py`, `test_profile_age_invariant.py` và `test_synthetic_eligibility.py`; chỉ path nào có trong approval pha tương ứng mới được sửa.
- DB chính `sketch2life` không phải target ghi/migration/test. P không được chạm DB đó.

### 1.3. Source baseline và revision pins

#### 1.3.1. Source/test paths đã ghim từ Draft 1

| Path | SHA-256 lúc soạn | Vai trò đọc |
|---|---|---|
| `backend/alembic/env.py` | `FABE5736CC7A49CC3C3D36112B4780248113DEEA3DE9A3DA4D2C2CB85E937447` | `_MANAGED_SCHEMAS` hiện không gồm `parent`; offline env còn gọi `_database_url()` |
| `backend/src/sketch2life/infrastructure/persistence/core_models.py` | `47D60EEECEF12F583B927BAB7FE3B74B9F19F15231E84E4039187376A502473A` | Metadata nền |
| `backend/src/sketch2life/infrastructure/persistence/be1_models.py` | `6859CC8313482C70828176B4E12209B485B7D582C6831340AE0D451659219C1E` | Không sửa/migrate bảng BE1 |
| `backend/src/sketch2life/infrastructure/identity/firebase_token_verifier.py` | `0B2DEF14F43F80C311F4D0DBC71DD29F90C2E1FC0BA6032DB20B999CAE8287FD` | Test seam chỉ ở verifier boundary |
| `backend/src/sketch2life/interfaces/http/app.py` | `D9DCBDC5BF3B71840C98BEB50A80D5A7BC1D800C3F93FFBB05DD021E99A995C0` | Đọc; chỉ sửa nếu lựa chọn mount được approval và thực sự đòi hỏi |
| `backend/src/sketch2life/interfaces/http/router_composition.py` | `E06A158B3616583DF8ABBA21D52C62E769A6A9E7C75359D28D424AB15849CC` | Composition; chỉ sửa theo lựa chọn mount đã duyệt |
| `backend/src/sketch2life/domain/child_age.py` | `C4A1288A41D6EC52087A9BB83F7F8590D1084C367A41BD512D65ACA917A2838C` | Đọc; Parent không dùng helper này |
| `backend/tests/unit/test_synthetic_eligibility.py` | `B579975452443848A560B89D3CFCA433C5E644EC6CA30165A68D21285E29CBF1` | Graph assertions cũ cần cập nhật sau root revision |
| `backend/tests/integration/ai_jobs/test_migrations.py` | `BF1D51D21262C3E76206C9A0FD01EBD3B3FE7006AA0B00DC28109A81C0A9238E` | Chỉ đọc để xác định fixture; không chạy/sửa |

#### 1.3.2. Alembic migration files — pins kế thừa từ Draft 1

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

Các pins source/migration phải được rehash khi soạn Task Approval cuối; hash sai hoặc path ngoài allowlist là stop. Không dùng pin này như bằng chứng migration đã chạy trong lượt soạn.

## 2. S1a-P contract, scope và dependency

**Scope:** ba operation Parent được liệt kê ở SRS v2.3 §21.2. D-156 R4 chốt POST tạo hồ sơ cho principal đã xác minh, owner theo subject; GET/PATCH chỉ cho owner. D-148 và các hướng D-156 không mở route khác.

| Operation nguồn | Request/response và kiểm chứng cần có | NOT COVERED / ô owner |
|---|---|---|
| `POST /v1/parent/profiles` — SRS §21.2 | Request không nhận organization ID; tạo hồ sơ và revision đầu cho `subject` của principal đã xác minh; response `201` chứa profile reference và revision theo SRS | Prefix/mount thực tế; ID do client hay server cấp; idempotency; exact response fields |
| `GET /v1/parent/profiles/{profile_id}` — SRS §21.2 | Owner đọc được đúng hồ sơ theo subject; principal khác không nhận diện được sự tồn tại | Exact status/code/body của IDOR; deleted/state behavior |
| `PATCH /v1/parent/profiles/{profile_id}` — SRS §21.2 | Owner gửi expected revision; tạo revision bất biến mới và cập nhật current reference trong cùng transaction | Full snapshot hay partial patch; exact request/response fields; hash serialization |

Các path ở trên là SRS operation names; router prefix/mount và OpenAPI prefix vẫn là **ô owner mở**. Không tự chọn `/api/be1/v1`, không thêm `/v1/me`, `/v1/teacher/profiles`, list, delete, share/grant, consent, StoryRun hay alias. `POST` cho mọi principal đã xác minh là owner direction; không đặt một rule “deny role khác” lên POST. Platform Admin/Operator/content-admin negative tests **NOT RUN** vì identity model hiện không biểu diễn các roles đó.

### 2.1. Parent logical schema và DDL expectation

Nguồn DTR v2.3 §5.3 lines 321–322 và 418–419 chỉ mô tả logical fields/relations; DTR không chốt SQL type, nullability, exact constraint names, serialization, trigger hay cách giải vòng current-reference. SQL offline chỉ được đối chiếu với yêu cầu sau; không được để migration tự quyết các ô đang mở.

| Bảng | Logical fields tối thiểu theo DTR | Invariants đã chốt | Còn cần owner chốt trước final approval |
|---|---|---|---|
| `parent.child_profiles` | `parent_profile_id`; owner principal; `state`; `created_at`, `updated_at`, `deleted_at`; `current_revision_ref`; thêm `data_origin` theo R6 | Parent là owner duy nhất; giữ invariant “unique owner/profile key” của DTR §5.3 lines 418–419; `data_origin` có CHECK chỉ nhận `SYNTHETIC_DEV`; không có thêm cột ngoài deviation R6; không hợp nhất `be1.managed_profiles` | SQL types và nullability từng cột; cột tạo unique owner/profile key; biểu diễn subject/issuer; nullability của `data_origin` (CHECK đơn thuần không loại NULL); PK/unique/FK/CHECK/index names; state/deleted semantics; cách ràng buộc `current_revision_ref` mà không phá vòng FK |
| `parent.profile_revisions` | `profile_revision_id`, `parent_profile_id`, `revision_no`, `age_months`, `age_band_ref`/version, `display_name`, `interests_summary`, `authored_by`, `created_at`, `revision_hash` | Snapshot revision bất biến; unique `(parent_profile_id, revision_no)`; application và DB CHECK `36 <= age_months <= 120`; `age_band_ref`/version null và “not configured”, không tuyên bố đạt NFR-38/AC-65 | SQL types/nullability; exact PK/FK/UNIQUE/CHECK/index names; `authored_by` identity semantics; hash canonicalization; trigger hay app-only enforcement cho immutability; cách ghi current pointer và xử lý FK cycle |

R6 là deviation đã được owner chấp nhận riêng cho M2: thêm `data_origin` vào `parent.child_profiles`, CHECK bằng `SYNTHETIC_DEV`, dù DTR v2.3 không liệt kê cột này. D-155 Q10 ghi ánh xạ giá trị `SYNTHETIC_TEST` của SRS sang giá trị lưu `SYNTHETIC_DEV`; không tạo giá trị lưu thứ hai. Không mở rộng deviation sang `age_source`, consent refs hoặc cột khác. Age provenance ngoài các quyết định R6/R7 vẫn là ô owner. F-6 chặn `REAL` và `LEGACY_UNCLASSIFIED`; R8 chỉ cho HTTP `SYNTHETIC_DEV` khi `settings.env` là `local` hoặc `test` và `synthetic_pilot_enabled` bật. Exact row label/run-id dùng các trường đã cho phép, không thêm cột test-only, vẫn cần điền để inventory chỉ nhận diện hàng do test tạo.

### 2.2. Identity, ownership, revision behavior

- Test thay đúng Firebase token-verification boundary bằng test double; giữ thật router, verified-principal extraction, subject ownership, service, repository, transaction và PostgreSQL. Không override dependency đang được kiểm tra.
- POST tạo owner từ verified principal `subject`, không lấy owner từ body. GET/PATCH của principal khác phải trả cùng quan sát ngoài như profile không tồn tại; exact HTTP code/error body là ô owner. Đây là IDOR case; không mặc định lỗi BE1 `IDENTITY_ISSUER_MISMATCH` áp vào Parent.
- PATCH phải yêu cầu expected revision và tạo snapshot mới; trạng thái active/deleted, full-vs-partial input, profile/revision ID generation, hash serialization và idempotency còn mở. Không thêm endpoint để lấp các hành vi chưa có.
- `age_months` được kiểm trong service/application và CHECK DB ở 36–120; tuổi 35/121 bị từ chối. Không dùng `domain/child_age.py`, không clamping legacy và không ảnh hưởng CHECK BE1 36–155.
- Các test system-role cho Platform Admin, Operator và content-admin permission ghi **NOT RUN** do không có representation trong hệ thống; không chế fixture giả thành bằng chứng role policy.

## 3. DB policy, K4, migration và candidate command ceilings

### 3.1. Target và identity guard

| Trường | Target/hướng | Provenance |
|---|---|---|
| PostgreSQL instance | Cùng instance native Windows đã dùng cho S0-owner-run | Owner report; revalidate tại Task Approval |
| DB | `sketch2life_m2_s1a` | Owner report schema-only trước T; phải kiểm lại sau T |
| Host/port | `localhost:5433`, chỉ loopback `127.0.0.1` hoặc `::1` | Direction; executor phải xác minh lại trước mỗi command cần DB |
| User/version | `postgres`, PostgreSQL major 17 | Owner report; revalidate trước chạy |
| Main DB | `sketch2life` | Không được migrate, ghi hoặc dùng fixture test |
| Fixture variable | `S1A_P_TEST_DATABASE_URL` riêng; trong process dùng để cấu hình `SKETCH2LIFE_DATABASE_URL` cho `create_app()` | Hướng R5; không fallback BE1 variable hoặc `.env` |

Mọi PostgreSQL fixture phải fail-closed và xác minh identity trên đúng `runtime.engine` mà app sử dụng: `current_database() = sketch2life_m2_s1a`, user `postgres`, server port 5433, loopback, PostgreSQL major 17. Kiểm tra phải xảy ra trước test write. Không log URL/password. Không dùng `BE1_TEST_DATABASE_URL`, `backend/.env` hay root `.env`.

Migration path phải có target guard kiểm tra `current_database()` đúng DB trước schema/table DDL; dùng `CREATE SCHEMA parent` không `IF NOT EXISTS`. Một guard chỉ chạy trong thân `upgrade()` chưa được xem là đủ nếu Alembic có thể tạo `alembic_version` trước khi gọi revision. Task Approval phải chứng minh guard chạy trước mọi DDL, kể cả DDL version table, hoặc dừng xin quyết định sửa hẹp. Cách bảo đảm điều này và vị trí có thể cần sửa `env.py` là ô owner; không được tuyên bố đã giải quyết bằng inventory trước/sau không nguyên tử.

### 3.2. K4 inventory và Alembic branch

- K4 trước P phải là inventory source/target mới sau khi S1a-T kết thúc. Ghi riêng schema/table names, row counts theo nhãn test, `public.alembic_version`, server identity và nguồn từng artifact. Không đọc/copy row values và không tuyên bố DB đang còn 0 hàng.
- Revision candidate kế thừa hướng D-155 Q9: `revision = 20261107_m2_parent_profiles`, `down_revision = None`, `branch_labels = ("parent",)`, `depends_on = None`. Tên/file và graph phải kiểm collision lại trong approval cuối; không stamp, không version table riêng và không chạy `upgrade heads` không target.
- Upgrade chỉ được nhắm `parent@head` trên `sketch2life_m2_s1a`. DDL do revision tạo chỉ thuộc schema `parent.*`; Alembic bookkeeping là ngoại lệ có giới hạn: `alembic_version` có thể được tạo nếu chưa tồn tại và phải có đúng một version row cho revision Parent. Không cho DDL lên BE1/Core/Story hoặc schema khác.
- Offline SQL preview không phải apply. Preview từ base có thể phát `BEGIN`, `CREATE TABLE alembic_version` nếu offline context chưa có head, DDL parent, `INSERT INTO alembic_version`, `COMMIT`; khi online, version table có thể đã có nên Alembic không nhất thiết phát lệnh CREATE đó. Người duyệt phải so đúng SQL thật với inventory; không được dùng một số đếm tuyệt đối nếu pre-inventory khác.
- Nếu pre-inventory xác nhận 117 bảng và `public.alembic_version` đã tồn tại, hai Parent tables làm tổng dự kiến 119; nếu version table vắng, số tổng khác và phải ghi/duyệt trước apply. Sau migration, `parent.*` phải rỗng trước test; version table có đúng revision mới. Downgrade chỉ là giả thuyết/rollback không được chạy: phải từ chối khi một trong hai Parent tables có hàng; không cleanup rộng hoặc downgrade trên DB có dữ liệu.
- `backend/alembic/env.py` hiện không quản lý schema `parent`; import metadata/`_MANAGED_SCHEMAS` chỉ ảnh hưởng autogenerate/compare, không tự cần thiết cho explicit `op.*` upgrade. Việc sửa env.py là **ô owner** và phải có lý do, allowlist, guard placement và kiểm tra tác động riêng; không mặc định thêm metadata.
- Source graph tham chiếu từ review: 28 revision files, 12 raw heads chỉ xét `down_revision`, 9 heads khi resolve dependencies. Root Parent dự kiến 29/13/10. `test_synthetic_eligibility.py` assertion cũ 25 và (11,9) là stale; P phải sửa đúng thành 29/13/10 nếu source graph vẫn vậy. Đây là inventory source đã đọc/báo trong review, không phải Alembic command đã chạy ở lượt soạn.

### 3.3. Command ceiling candidates — không chạy trong Draft

Các câu lệnh dưới đây là phạm vi ứng viên để owner xem; phiên soạn không xác nhận cú pháp Windows, timeout thực tế, credential ingress hay output. Final Task Approval phải ghim nguyên lệnh, executable, timeout, log/cache path và cách owner nhập secret mà không vào history/log. Không đổi shell/cách gọi để lách lỗi.

| Mục | Candidate ceiling | Điều kiện/giới hạn |
|---|---|---|
| Baseline offline trước P | `backend/.venv/Scripts/python.exe -m pytest` chỉ các node unit/contract/offline đã ghim, `--disable-plugin-autoload`, `--basetemp=tmp/<task>/pytest-baseline`; cache/test temp dưới `tmp/` | Sau T và trước P code; lưu summary thật; test graph-count đỏ sẵn được ghi riêng, không tính là P pass/fail |
| Baseline mypy trước P | `backend/.venv/Scripts/mypy.exe --package sketch2life --config-file pyproject.toml --strict --cache-dir ../tmp/<task>/mypy-baseline` từ `backend` | Tính lại sau T; ghi version, exit và diagnostic; không dùng cache cũ |
| Source graph | `backend/.venv/Scripts/python.exe -m alembic -c alembic.ini heads --resolve-dependencies` từ `backend` | Không `--verbose` để tránh đường dẫn tuyệt đối; static/source read only; không kết nối DB |
| Offline SQL preview | `backend/.venv/Scripts/python.exe -m alembic -c alembic.ini upgrade parent@head --sql` từ `backend` | Giá trị process-local giữ chỗ nếu env.py yêu cầu URL; không kết nối. Giữ output ngoài file evidence chứa secret; owner review SQL trước khi quyết định |
| Read-only inventory pre/post | `psql -X -W -h localhost -p 5433 -U postgres -d sketch2life_m2_s1a` chạy tương tác; câu SQL chỉ đọc identity, schema/table names/counts và version rows trong READ ONLY transaction rồi rollback | Mỗi inventory một lượt, timeout đề xuất 300s; chưa xác minh `-W` cùng PowerShell input; không tự nhận có script/SQL runner đã kiểm chứng |
| Target apply | `backend/.venv/Scripts/python.exe -m alembic -c alembic.ini upgrade parent@head` từ `backend` | Tối đa một lần sau review SQL và Task Approval riêng; guard phải fail-closed trước DDL; không tự retry |
| Focused PostgreSQL | `backend/.venv/Scripts/python.exe -m pytest` với đúng node file mới Parent PostgreSQL, `--disable-plugin-autoload`, basetemp riêng | DB fixture xác minh chính app engine; không chạy `test_migrations.py`, suite directory hoặc fixture có CREATE/DROP DATABASE |
| Focused Ruff | `backend/.venv/Scripts/ruff.exe check --select E,F,I,UP,B,SIM` trên đúng allowlist | Cache dưới `tmp/`; format chỉ khi được ghi trong approval |
| Harness/security/architecture | Mỗi validator đúng một lần: `python tools/validate_harness.py`, `python tools/validate_repository_security.py`, `python tools/validate_architecture.py`; thêm `git diff --check` | Ghi output/exit code thật; không xem validator là verdict migration hay acceptance |
| Final mypy | Cùng binary/options với baseline nhưng cache và log mới | So baseline sau T; không dùng `python` ngoài backend venv |

Không chạy rộng `backend/tests/integration`. Loại khỏi mọi execution set: `backend/tests/integration/ai_jobs/conftest.py`, `backend/tests/integration/ai_policy/conftest.py`, `backend/tests/integration/learning_content/conftest.py`, `backend/tests/integration/be2_cross_lane/test_persisted_video_worker_flow.py` và `backend/tests/integration/ai_jobs/test_migrations.py` vì có hoặc liên quan fixture tạo/xóa database. Nếu exact test set không chứng minh an toàn trước khi connect/write, dừng.

## 4. K4 — source/target reconciliation trước migration

K4 cần owner-run inventory mới sau T, target identity guard, parent schema/table absence or exact expected pre-state, row-label policy, Alembic version rows và source graph. So sánh source branch với DTR/SRS pinned v2.3; SRS v2.7 chỉ là ghi chú chưa ký/chưa gộp. Không sửa `sketch2life`, không reset/restore/drop/truncate/cleanup. Nếu target lệch kỳ vọng, có bảng không rỗng ngoài test-label policy, version row không rõ, schema `parent` đã có, hoặc graph khác 28/12/9, dừng và xin owner review mới.

Không chạy `alembic current --verbose` vì có thể in DB identity/path. Revision hiện hành được đọc bằng psql SELECT chỉ đọc sau khi target identity được khẳng định. `heads --resolve-dependencies` là source graph; `heads --verbose` không cần và tránh in path.

## 5. Test seam, test behavior và affected suites

- Chỉ thay Firebase token verifier boundary bằng test double. Gắn test verifier vào `runtime.identity_verifier` của app runtime thật; không override `get_verified_adult` hay route dependency. Giữ thật principal extraction, subject ownership, router, authorization, service, repository, transaction và database.
- POST: kiểm verified principal tạo đúng owner subject và không thể gán owner khác từ request. GET/PATCH: owner thành công; non-owner nhận cùng response quan sát như nonexistent profile. Thêm IDOR cases qua hai subject khác nhau.
- R4 không cho biểu diễn hoặc kiểm thử deny theo role cho POST; Platform Admin/Operator/content-admin negative tests **NOT RUN**. Không đổi D-148 hay global `authorize_adult`.
- Test fixture lấy `S1A_P_TEST_DATABASE_URL` vào process-local `SKETCH2LIFE_DATABASE_URL`, không fallback; sau `create_app()`, kiểm identity bằng `app.state` runtime engine thực trước mọi write. Test không được tạo/drop database. Mỗi row synthetic có marker/run-id qua các field đã duyệt; không broad cleanup.
- `age_months`: cases 35/36/120/121; application check và named DB CHECK `36 <= age_months <= 120`. Append revision, reject duplicate revision number, verify snapshot immutability/current pointer and transaction atomicity. Cơ chế DB trigger hay app-only còn là ô owner.
- `data_origin`: chỉ `SYNTHETIC_DEV`; `REAL` và `LEGACY_UNCLASSIFIED` không được tạo/đọc như synthetic. HTTP gate phải require env local/test và `synthetic_pilot_enabled`. Kiểm tra NULL bị chặn cần DDL nullability được chốt, vì CHECK đơn thuần không chặn NULL.
- Không dùng `child_age.py`, không gọi StoryRun route, không dùng mock repository/PostgreSQL/transaction. Baseline offline và mypy được lấy lại sau T, trước P implementation. Các lỗi baseline đã tồn tại ghi riêng, không gộp thành P pass/fail.

## 6. Allowlist ứng viên — chưa có hiệu lực

Final Task Approval phải chuyển mọi path thành exact read/edit/new sets, ghim hash của file existing, nêu owner cho từng decision. Draft này không cho phép sửa file nào.

### 6.1. Existing paths — chỉ đọc

`backend/src/sketch2life/infrastructure/identity/firebase_token_verifier.py`; `backend/src/sketch2life/application/ports/identity.py`; `backend/src/sketch2life/interfaces/http/be1_runtime.py`; `backend/src/sketch2life/interfaces/http/routers/be1_common.py`; `backend/src/sketch2life/interfaces/http/routers/be1_registry.py`; `backend/src/sketch2life/infrastructure/config/settings.py`; `backend/src/sketch2life/infrastructure/persistence/core_models.py`; `backend/src/sketch2life/infrastructure/persistence/be1_models.py`; `backend/src/sketch2life/domain/child_age.py`; `backend/tests/unit/test_profile_age_invariant.py`; `backend/tests/unit/test_age_provenance_columns.py`; current S1a-T final artifact after its own review/owner disposition; SRS v2.3; DTR v2.3; M2 Draft 10/11; D-144, D-148, D-150–D-156; S0 inventory. `backend/tests/integration/ai_jobs/test_migrations.py` chỉ đọc để xác định fixture, tuyệt đối không chạy.

### 6.2. Existing paths — candidate edit, must pin again

- `backend/alembic/env.py`: chỉ nếu owner chọn chỉnh guard placement/managed metadata; không mặc định cần cho explicit `op.*` migration.
- `backend/src/sketch2life/interfaces/http/router_composition.py`: chỉ nếu lựa chọn mount Parent cần đăng ký router.
- `backend/src/sketch2life/interfaces/http/app.py`: read-only mặc định; chỉ candidate edit nếu cách mount đã chọn không thể làm ở composition layer và có approval amendment.
- `backend/src/sketch2life/interfaces/http/openapi_contract.py`; `openapi_contract_amendments.py`; `openapi_srs_v22.py`: catalog/schema contract theo route prefix được owner chọn.
- `backend/tests/contract/test_app_composition.py`: edit để cập nhật exact mounted route set.
- `backend/tests/contract/test_openapi_contract_catalog.py`: edit để catalog đúng ba operation và số đếm thực tế.
- `backend/tests/unit/test_synthetic_eligibility.py`: edit graph assertions sau root migration; không thêm creator allowlist mặc định.
- `backend/tests/unit/test_profile_age_invariant.py`: read-only mặc định. Chỉ xin amendment nếu Parent creator thật sự bị detector gắn cờ; AST allowlist hiện tập trung vào BE1 managed profiles và yêu cầu chính xác hai constructor. Không thêm path không cần thiết.

### 6.3. New paths — candidate, hiện chưa tồn tại

- `backend/src/sketch2life/domain/parent_profile.py`
- `backend/src/sketch2life/application/ports/parent_profiles.py`
- `backend/src/sketch2life/application/services/parent_profiles.py`
- `backend/src/sketch2life/contracts/schemas/parent_profiles.py`
- `backend/src/sketch2life/infrastructure/persistence/parent_models.py`
- `backend/src/sketch2life/infrastructure/persistence/parent_repository.py`
- `backend/src/sketch2life/interfaces/http/routers/parent_profiles.py`
- `backend/alembic/versions/20261107_m2_parent_profiles.py` — candidate filename; recheck ID/path collision and actual graph before final approval.
- `backend/tests/unit/test_m2_parent_profile_service.py`
- `backend/tests/contract/test_m2_parent_profile_routes.py`
- `backend/tests/integration/test_m2_s1a_parent_postgres.py`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S1A_P_K4_SCHEMA_SOURCE_RECONCILIATION_20261107.md`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S1A_P_IMPLEMENTATION_REPORT_20261107.md`

### 6.4. Explicit exclusions

No changes to BE1 model/migrations, source SRS/DTR, DECISIONS/TASK_APPROVAL, Bruno requests or `openapi.runtime.json` unless a separately approved amendment names them. No `.env`, no root settings, no runtime secret, no database dump in repository. Do not edit `backend/tools/be1_api_smoke.py`, `backend/tests/integration/ai_jobs/test_migrations.py`, destructive integration fixtures, or unrelated test contracts.

## 7. Acceptance mapping — existing M2 IDs only

Không tạo P-AT IDs mới. P chỉ đề nghị evidence cho các acceptance ID đã có trong Draft 10/11:

| M2-AT | Phạm vi P | Evidence phải có trong Task Approval cuối |
|---|---|---|
| M2-AT-01 | Parent verified-subject ownership; owner read/write; non-owner IDOR indistinguishable from nonexistent; authentication boundary test double only | Contract + PostgreSQL route test với real runtime/repository/transaction; system-role negative tests ngoài khả năng biểu diễn ghi NOT RUN |
| M2-AT-03 | Age 35/36/120/121, revision append/immutability/current ref, no DOB, không `child_age.py` | Unit/contract/PostgreSQL evidence; DB CHECK 36–120; `age_band_ref/version` null không đạt NFR-38/AC-65 |
| M2-AT-10 | Service/contract/persistence cho Parent revision, không gọi StoryRun endpoint | Service + contract + PostgreSQL persistence; không claim StoryRun route/lifecycle |
| M2-AT-11 | Synthetic eligibility theo R6/R8, `SYNTHETIC_DEV` only, REAL/LEGACY deny, local/test + feature flag | Route/DB evidence, synthetic row identifiers/run labels; stop nếu `data_origin` nullability hoặc row labeling chưa được duyệt |

Schema guard, source graph, K4 inventory, OpenAPI route count, validators, mypy và allowlist là các cổng kỹ thuật/exit riêng; không tạo acceptance ID mới và không gộp chúng thành PASS của M2-AT.

## 8. Xử lý findings

### 8.1. Review Draft 1 — P2-01..P2-13 và P3-01..P3-12

| Finding | Disposition trong Draft 2 |
|---|---|
| P2-01 creation-path AST | **RESOLVED AT PLAN LEVEL:** Parent ORM constructor không tự động thêm vào BE1 managed-profile allowlist; giữ test hiện có nguyên trạng trừ khi detector thực tế gắn cờ và có amendment riêng. T-side create_profile là S1a-T. |
| P2-02 route BE1 cũ | **OTHER PHASE:** legacy assignment route disposition nằm ở S1a-T; P không thêm alias hoặc sửa route BE1. |
| P2-03 Teacher cardinality/lock | **OTHER PHASE:** S1a-T; P không sở hữu assignment/Teacher route. |
| P2-04 allowlist/composition | **RESOLVED AT PLAN LEVEL:** bổ sung test composition edit, runtime/common read paths, catalog test; route mount layer là owner field, `app.py` không mặc định edit (§6). |
| P2-05 auth seam | **RESOLVED AT PLAN LEVEL:** thay Firebase verification boundary duy nhất; no dependency override, giữ subject/authz/repository/DB thật (§5). |
| P2-06 Parent identity/IDOR | **DIRECTION RESOLVED:** R4 POST cho mọi verified principal tự tạo owner subject; GET/PATCH non-owner là IDOR. System-role negative tests NOT RUN vì roles không biểu diễn. Exact denial body/status còn owner field. |
| P2-07 env/DB fixture | **RESOLVED AT PLAN LEVEL:** dedicated `S1A_P_TEST_DATABASE_URL`, app engine identity assertion; migration guard phải bảo vệ trước DDL, `.env` fallback không được làm target sai (§3.1). |
| P2-08 synthetic rows | **PARTIAL / OWNER FIELD:** R6/R8 chốt data_origin/gate; field nullability và marker/run-id dùng cột nào cần chốt trước approval (§2.1, §5). No zero-row criterion or broad cleanup. |
| P2-09 Alembic output/head | **RESOLVED AT PLAN LEVEL:** không `current --verbose`; psql read-only version inventory; source heads không verbose, graph split raw/resolved được ghi (§3.2–3.3). |
| P2-10 SRS route/test trace | **RESOLVED AT PLAN LEVEL:** ba operation, expected revision/ownership, NOT COVERED fields ghi ở §2; capacity/assignment fields thuộc T/Q7. |
| P2-11 Parent DDL/F-6 | **PARTIAL / OWNER BLOCKING:** DTR logical matrix, R6 deviation, R7 check được ghi; SQL types/nullability/constraints/FK cycle/immutability/state semantics và row label còn owner fields (§2.1). |
| P2-12 test/validator/mypy ceiling | **PARTIAL / FINAL PIN REQUIRED:** command categories, venv, cache, baselines và destructive exclusions ghi ở §3.3; exact nodes, ceilings, logs/secret ingress phải được pin ở final Task Approval. |
| P2-13 D-152/D-155 scope | **RESOLVED AT PLAN LEVEL:** DB riêng, D-144 §9.5 boundary, Q9 root branch and no stamp ghi ở §1–3; không phải migration approval. |
| P3-01 hash length | Full 64-hex SHA-256 pins; rehash all at final approval. |
| P3-02 DTR line endings | Working hash và LF blob hash đều ghi §1.1. |
| P3-03 stamp/story revision | Không stamp, không chạy `20261104_story_revisions`; Parent root độc lập. |
| P3-04 M2-AT-10 | Mapped to existing M2-AT-10 service/contract/persistence only; no `child_age.py` or StoryRun. |
| P3-05 deletion/FR-C-10/BR-35 | **NOT COVERED:** no profile delete route; giữ D-148 item 3. |
| P3-06 extra routes/fixtures | **NOT COVERED:** no `/v1/me`, `/v1/teacher/profiles`, list/read/delete or extra identity endpoint. |
| P3-07 psql syntax | **PARTIAL:** only an interactive candidate command is listed; Windows pipe/`-W`, SQL assertions and script behavior are unverified; final approval must pin the exact reviewed method. |
| P3-08 IDs/ownership | R4 fixes owner from verified subject; profile/revision ID source and idempotency remain owner fields. |
| P3-09 Python executable | Candidate uses `backend/.venv`; exact absolute executable resolved only at execution approval, not embedded here. |
| P3-10 revision graph | Current static reference 28/12/9; after root 29/13/10 if unchanged. Recheck; update exact stale test assertion. |
| P3-11 remote docs branch | **OUT OF SCOPE:** no fetch, merge or remote branch changes. |
| P3-12 destructive fixtures | Explicitly excluded in §3.3; no broad integration directory or `test_migrations.py`. |

### 8.2. Independent Draft 1 review findings — P2-N1..N5 and P3-N6..N15

| Finding | Draft 2 disposition |
|---|---|
| P2-N1 DDL expectation | **PARTIAL / OWNER BLOCKING:** §2.1 lists logical fields and fixed invariants but does not invent SQL types, nullability or constraint names; calls out FK cycle, immutability, unique owner/profile key, state/deleted semantics and age-band nulls. Resolve every blocking field before SQL approval. |
| P2-N2 Parent identity | **DIRECTION RESOLVED BY R4:** POST self-creates for any verified principal; GET/PATCH owner only. Platform Admin/Operator/content-admin tests NOT RUN; no claim of role-denial on POST. |
| P2-N3 target guard | **PARTIAL / OWNER BLOCKING:** migration guard and real app engine identity are required. Guard must execute before any DDL, including Alembic version bookkeeping; placement/config and secret ingress remain to be pinned. |
| P2-N4 composition/catalog | **RESOLVED AT PLAN LEVEL:** add exact app-composition test, OpenAPI catalog test, runtime/common read paths; baseline at Draft 1 was 129 runtime operations / 124 mounted / 111 paths / 18 tags. T Draft 2 records its legacy-route alternatives; after T, P must re-count and expect +3 operations, +3 mounted operations, +2 paths, and +0 or +1 tag depending on owner choice. |
| P2-N5 T/P shared DB | **RESOLVED BY R1:** T then P on same DB, never parallel; inventory and mypy baseline recomputed after T. Shared paths and dynamic table/row baseline are listed (§1.2, §3, §6). |
| P3-N6 offline SQL/version table | **RESOLVED AT PLAN LEVEL:** preview distinguished from online apply; allowed `alembic_version` bookkeeping and conditional table count are explicit; downgrade refusal with data. |
| P3-N7 AST attribution | **RESOLVED AT PLAN LEVEL:** creator allowlist is in `test_profile_age_invariant.py`; do not alter it unless actual detector flags a path and separate approval allows it. Graph count change belongs to `test_synthetic_eligibility.py`. |
| P3-N8 verbose heads/path | **RESOLVED:** use non-verbose resolved-head command; no absolute path output. |
| P3-N9 env.py autogenerate | **RESOLVED AT PLAN LEVEL:** env.py edit is optional/owner-controlled, not assumed necessary for explicit operations; guard placement remains separate blocker. |
| P3-N10 invented P-AT IDs | **RESOLVED:** §7 uses existing M2-AT-01/03/10/11 only. |
| P3-N11 psql syntax | **PARTIAL:** interactive `psql -X -W` candidate noted, but PowerShell prompt/input and exact read-only SQL are not verified. Pin one method in owner-signed approval before execution. |
| P3-N12 contract details | **PARTIAL / OWNER FIELD:** POST has no organization ID and returns profile ref/revision; PATCH full-vs-partial, identity issuer, exact fields and age-band compliance remain explicit. |
| P3-N13 regression baseline | **RESOLVED AT PLAN LEVEL:** offline baseline before P code after T is required; pre-existing stale graph failure recorded and excluded from P pass/fail. |
| P3-N14 create_app/.env side effects | **PARTIAL / STOP GATE:** app test engine must be set explicitly; `.env` not read. Lifespan/retention startup DB side effects must be inspected and target-guarded before approval. |
| P3-N15 app/allowlist ambiguity | **RESOLVED AT PLAN LEVEL:** app.py read-only by default; pin paths for SRS/DTR; exact edit/read/new sets must be finalized before approval. |

## 9. Stop gates, exit and validity

STOP if any pin/HEAD/index changes; S1a-T is not complete/reviewed; T→P order or between-phase inventory/mypy baseline is unavailable; target DB identity differs; a write could touch `sketch2life`; a non-test/unknown row is present or label policy cannot identify this test's rows; `parent` schema is unexpected; version state/graph differs; guard does not run before any DDL; SQL contains changes outside `parent.*` and the explicitly reviewed Alembic bookkeeping; migration needs BE1/Core/Story changes; Parent DDL requires an unfilled owner field; routes/count/catalog/mount differ from selected contract; dependency overrides or repository mocks replace the behavior under test; fixture can CREATE/DROP database; tests include broad integration or `test_migrations.py`; secret/URL/path leaks; command timeout/crash/no official summary/no verdict; or any required path is outside final allowlist. Preserve DB after failure; no auto retry, restore, downgrade or cleanup.

S1a-P may be considered complete only after a separate Task Approval is finalized and independently reviewed, S1a-T has been accepted and closed, all blocking owner fields are decided, K4 is accepted, target guard placement and SQL preview are reviewed, migration runs only on the approved DB under owner-run, exact PostgreSQL/contract tests and validators have official outputs, evidence is recorded and owner separately closes the phase.

This Draft does not open S1a-P, S1b, S2, S3 or M3–M6. `OWNER_MODAL_CALL_APPROVED=NO`. Executor and independent reviewer must be separate sessions; no subagent may substitute for independent review. No stage/commit/push/merge is authorized.

## 10. Owner fields — leave blank

Do not tick or fill these fields in this Draft. Resolve and record them only in a later owner-approved Task Approval.

| Owner field | State |
|---|---|
| Exact Parent router prefix, mount function and reused/new OpenAPI tag | [ ] Unchosen |
| S1a-T closure/review record and exact post-T target inventory | [ ] Pending; blocks P |
| Recomputed post-T offline test and mypy baseline, including known failures | [ ] Pending; blocks P |
| Exact Parent SQL types and nullability for every column | [ ] Blocking |
| `data_origin` nullability and exact CHECK/constraint names | [ ] Blocking; CHECK alone permits NULL |
| Principal subject/issuer storage and unique owner/profile key columns | [ ] Blocking |
| Current revision reference FK cycle strategy and constraint timing | [ ] Blocking |
| Revision immutability enforcement (DB trigger or app-only) | [ ] Blocking |
| `state` / `deleted_at` semantics without delete route | [ ] Blocking |
| `age_band_ref` and version null values; NFR-38/AC-65 remains unmet | [ ] Acknowledgement required |
| Parent age-source/provenance beyond R6/R7, and no extra column without approval | [ ] Unchosen |
| Parent profile/revision ID generation; PATCH full/partial; hash serialization; idempotency | [ ] Unchosen |
| Exact IDOR status/code/body and identity-issuer semantics | [ ] Unchosen |
| Test row synthetic/run-id marker using only approved columns; no broad cleanup | [ ] Blocking |
| Alembic pre-DDL target guard placement, including version-table creation | [ ] Blocking |
| `env.py` edit decision and exact allowlist read/edit/new paths + hashes | [ ] Unchosen |
| Revision ID collision check and 28/12/9 current graph recheck; expected 29/13/10 if unchanged | [ ] Pending |
| Pre/post inventory and SQL log locations, owners, restore method, ceilings, timeouts | [ ] Unchosen |
| Exact PowerShell/psql credential ingress and reviewed read-only inventory SQL | [ ] Blocking; not verified |
| Test nodes, cache/temp paths, Ruff/mypy/validator commands and reviewer pin | [ ] Unchosen |
| M2-AT ticks, final approval date/signature, executor and independent reviewer | [ ] Not entered |

**DRAFT END.** No approval, launch, migration, database write or implementation permission is granted by this document.
