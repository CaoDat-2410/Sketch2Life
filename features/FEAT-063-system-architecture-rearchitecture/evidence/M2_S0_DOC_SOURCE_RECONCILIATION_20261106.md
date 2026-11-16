# M2 S0-doc — đối chiếu nguồn, route, schema và migration

Ngày: 2026-11-06  
Trạng thái: **Đã lập evidence tài liệu; chờ review độc lập. Không tuyên bố S0-doc đã đóng.**  
Phạm vi: chỉ đọc các nguồn nằm trong approval S0-doc; không thực thi ứng dụng, test, validator, mypy, Alembic, database, Modal hoặc provider.

## 1. Baseline và kiểm soát nguồn

- Branch: `feature/feat063-be-foundation`.
- HEAD: `dd70685eae58aaaefea3e567f5c23d09345a8513`; parents: `1e109b1726f327ac9383457b0dbdd535ef5c6518` và `fb834771c24957bb8e289fb95d21410b14181e57`.
- Index sạch trước khi tạo evidence. Trước đó working tree có đúng hai file tracked được owner thay đổi (`DECISIONS.md`, `approvals/TASK_APPROVAL.md`) và bảy Draft 1–7 mới; hai file tracked có `git diff --numstat` lần lượt `11 0` và `22 0`.
- Draft 7 SHA-256: `BB3C9F165731B1AEE261265270526B791FEE7BD622CE7D614514F2622DEFD099`.
- Mục approval `M2 S0-doc Task Approval — Draft 7 — 2026-11-06` (trạng thái lịch sử `NOT LAUNCHED`) quy định phạm vi và đúng một file evidence mới; approval này không tự khởi chạy S0-doc. Việc thực thi bắt đầu bằng chỉ thị trực tiếp của owner trong hội thoại ngày 2026-11-06, chỉ thị này chưa được ghi riêng trong các hồ sơ repo đã đọc. Approval không cho sửa nguồn, snapshot, test, schema hoặc chạy lệnh sản phẩm.

### 1.1. Các nguồn ghim trong Draft 7 §1

Mười lăm hash ban đầu còn khớp. Hai hồ sơ thay đổi sau khi Draft 7 được ghim khớp đúng hash hiện hành do prompt S0-doc nêu; thay đổi được kỳ vọng này không được coi là mismatch.

| Nguồn | Hash quan sát | Đối chiếu |
|---|---|---|
| `plan/BE_PARENT_TEACHER_VISION_DEMO_ROADMAP_20261102.md` | `A0A485EE421FBB1DA9DEC99DD8EC08279D14EAF27EC548AD6A0A4CE8F234F8FA` | Khớp Draft 7 §1.1 |
| `plan/B0_B13_SIX_MILESTONE_REDISPOSITION_PLAN_20261102.md` | `773C4A8340C8E33AE39764D920B042AC19BACBAF6DC561FE9D5D3DFFCC4B5A5A` | Khớp hash hiện tại; provenance theo D-144, xem §6 |
| `plan/BACKLOG_API_REV37_SRS23_MODAL_20261030.md` | `380BF9F813CF809E35D9EA6F843E33A0DF892BA886E8C366AEB1C0F757A57391` | Khớp Draft 7 §1.1 |
| `artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` | `DCBF9786FF8983E34F2D3B4EBAB76301D0C52A6C9DE72CD08D0816BBD0D983FC` | Khớp Draft 7 §1.1; SRS v2.3-draft, chưa ký |
| `artifacts/DATA_TABLE_REGISTER.md` | `3E793BB2C62C9E6C50780DE636EDDE442D382C62B4643552F2298AF374171E22` | Khớp Draft 7 §1.1; DTR mô tả logical target |
| `evidence/COMMIT_WHITESPACE_NORMALIZATION_20261103.md` | `AF649B1518C4D550C2AEDE173063D6C46A889A7ADC9A70F187E86A23C72199C2` | Khớp Draft 7 §1.1 |
| `status/STATUS.md` | `827007578ABDAA78C7F987DC574268AA264FA666496C8A86C5D0F3E148035F9F` | Khớp Draft 7 §1.1 |
| `approvals/TASK_APPROVAL.md` | `DDA7C807882D3954A2ABCF1F0214F1F26991539A7BE22A5D50F54E4156C2EC1E` | Khớp hash hiện hành do S0-doc ghim; Draft 7 §1.1 pin cũ đã được append sau đó |
| `CONTEXT.md` | `6CAA4A5BE423383B026A662051FB54709AF73B1178A5673849AD44B6B6697F1D` | Khớp Draft 7 §1.1 |
| `DECISIONS.md` | `A1602850CB0237FC8BED6DD29E608260E32CFE65AFB07F141EDAE43B673BA8BC` | Khớp hash hiện hành do S0-doc ghim; Draft 7 §1.1 pin cũ đã được append sau đó |
| `SOURCE_REGISTER.md` | `2A419E529CE9603FF03A0697CC800A56826BC6EAD51B1596135AAA84B9FCF98B` | Khớp Draft 7 §1.1 |
| FEAT-064 `evidence/A2_REV3_INDEPENDENT_REVIEW_CLOSEOUT_20261103.md` | `10B12F4417A5E29DF0ED1697F33A8FAA08D692E71015998CCC8DE297328A1C36` | Khớp Draft 7 §1.2 |
| FEAT-064 `plan/FEAT064_A2_B1_B2_SEQUENTIAL_GOAL_20261103.md` | `D7DEE2977C5AA28B26FCB117281DE8B23E4D4AA85A42922B8B37752FBDA8752A` | Khớp Draft 7 §1.2 |
| FEAT-064 `approvals/TASK_APPROVAL.md` | `9D07B88190E8F5831D79431A79C2AAC944B266CB28CD29265E5D0283B77921B8` | Khớp Draft 7 §1.2 |
| `backend/alembic/versions/20261104_story_revisions.py` | `3618BEF0ECCB0E01EE61F65E1065F7AE8EA6297FE0781D965588614D0F1C37F8` | Khớp Draft 7 §1.3 |
| `backend/src/sketch2life/infrastructure/persistence/core_models.py` | `47D60EEECEF12F583B927BAB7FE3B74B9F19F15231E84E4039187376A502473A` | Khớp Draft 7 §1.3 |
| `.claude/handoff/logs/GB2_T12_OFFLINE_20261105A/offline-check.txt` | `6FF16B2E77EE7DB7CE18521484B92FAA9B40F685393D35A7746E74236313E143` | Khớp Draft 7 §1.3; local historical log, not execution verdict |

## 2. Requirement crosswalk

SRS v2.3-draft là nguồn requirement nhưng chưa ký. Roadmap được owner chấp nhận làm baseline lập kế hoạch, không phải implementation approval. B0–B13 là hồ sơ redisposition cũ; nó không thay ID hoặc nội dung chuẩn của SRS. Exact IDs dưới đây không xuất hiện trong B0 plan đã ghim; B0 chỉ cung cấp ngữ cảnh task/milestone, trong giới hạn provenance đã được D-144 xác nhận. DTR ghi logical table/owner, không chứng minh physical schema.

| ID | Vị trí nguồn và roadmap | Route evidence theo SRS | Logical tables / owners theo DTR | M2 acceptance trong Draft 7 | Phạm vi claim / trạng thái |
|---|---|---|---|---|---|
| FR-PL-01 | SRS §31.8; roadmap §“Traceability SRS”, Mốc 2 | `/v1/me` được nêu như **nhóm route đề xuất** tại SRS §9.6; §21.2 không mô tả method/request/response cho nó. Parent profile POST/GET/PATCH có ở §21.2. Không có identity API contract canonical đã xác minh. | `parent.child_profiles`, `parent.profile_share_grants` (Parent); `be1.adult_identities`, `be1.organization_assignments` (BE1); audit (Core). | M2-AT-01/05 | M2 kiểm nền role/scope và grant trong scope; không claim toàn bộ platform authorization/revoke đã đạt. |
| FR-PL-02 | SRS §31.8; roadmap Mốc 2 | `POST /v1/organizations/{org_id}/classes`, `POST /v1/classes/{class_id}/assignments`, `POST /v1/classes/{class_id}/profiles` — SRS §21.2. Danh sách/read route chưa được mô tả đầy đủ. | `be1.organizations`, `be1.classrooms`, `be1.organization_assignments`, `be1.enrollments` (BE1); tenant-owned lesson/feedback/quota thuộc owner tương ứng. | M2-AT-02/04A/04B | M2 là tenant/class/profile foundation; không chứng minh tất cả record tenant-scoped của hệ thống. |
| FR-PL-07 | SRS §31.8; roadmap Mốc 2 | Profile POST/GET/PATCH có ở §21.2; invitation/accept/revoke route chưa có contract canonical trong route table. | `parent.profile_share_grants`, `parent.child_profiles` (Parent); `be1.managed_profiles` (BE1). | M2-AT-05 | Grant lifecycle là phần M2 đề xuất nhưng consent/share đang defer theo D-144; chỉ synthetic, REAL và LEGACY_UNCLASSIFIED bị từ chối. Không claim share đã triển khai. |
| FR-PL-08 | SRS §31.8; roadmap Mốc 2 | Profile GET/PATCH và `POST /v1/story-runs` có trong §21.2; grant/download/token/cache/revoke surface chưa canonical. | `parent.profile_share_grants` (Parent), `core.asset_lineage` (Core), AI Jobs qua contract/port. | M2-AT-06 | M2 kiểm primitive field scope/revoke dự kiến; chưa có route acceptance và không claim mọi token/cache/job path đã được chứng minh. |
| FR-PL-25 | SRS §31.8; roadmap Mốc 2 | Profile POST/GET/PATCH và Teacher profile creation tại §21.2; age-band catalog/version route chưa xác minh. | `parent.profile_revisions` (Parent), `be1.profile_revisions` (BE1), age-band catalog owner chưa xác minh. | M2-AT-03/10 | Tuổi 36–120 và metadata là phần nền; age-band boundaries/catalog và full AC-65 chưa chốt. |
| BR-48 | SRS §31.8.1; roadmap Mốc 2 | Profile routes không tự chứng minh invitation/share; invite/accept/revoke route chưa canonical. | `parent.profile_share_grants`, `parent.child_profiles`, `parent.data_authorizations` (Parent). | M2-AT-05/06 | Grant phải deny khi thiếu/pending/revoked/expired; đây là primitive profile-share, không phải bằng chứng consent policy đã mở. |
| BR-49 | SRS §31.8.1; roadmap Mốc 2 | Class/org routes §21.2 là một phần; scope lesson, feedback, quota không được đại diện đầy đủ bởi ba route này. | Trong hàng BR-49 của Draft 7 §4 (dòng 230): `be1.organizations`, `be1.classrooms`, `be1.organization_assignments`, `be1.enrollments` (BE1). Các bảng sau không được gắn M2-AT nào ở hàng BR-49; tên và owner theo DTR: `be1.parent_groups`, `be1.parent_group_members` (BE1, §5.4.1) và `lesson.access_grants` (Lesson, §5.5) xuất hiện ở hàng BR-58 (Draft 7 dòng 232), nhưng M2-AT-05/06 (S1b, hoãn theo D-144 và D-148) chỉ kiểm primitive thu hồi qua `parent.profile_share_grants`, không nghiệm thu chính các bảng này; `lesson.delivery_recipients`, `lesson.delivery_feedback`, `lesson.feedback_replies` (Lesson, §5.5/§14.1) và `billing.video_quota_grants`, `billing.video_quota_usage` (Billing, §5.7) không xuất hiện trong Draft 7 và không có M2-AT. Nguồn: SRS §31.8.1 (dòng 2558) nêu quy tắc BR-49 là lesson, feedback, quota và group membership không lộ chéo tenant; SRS §30.4 (dòng 2428) nêu `be1.organizations`, `lesson.access_grants`, feedback/quota scope. Quota: DTR §5.7 và §14.2 mục 10 liệt kê scope `PARENT_ACCOUNT`, `TEACHER_ACCOUNT`, `ORGANIZATION`; grant source, allocation, package và charge priority còn phải chốt trước schema implementation; SRS §31.10 mục 7 ghi Teacher quota pool riêng hay nằm trong school còn mở, và SRS §11.2 chỉ liệt kê `ORGANIZATION`/`PARENT_ACCOUNT`/`GLOBAL`. | M2-AT-01/02/04A/04B | **M2 chỉ là tenant/class foundation, không phải acceptance đầy đủ BR-49.** Các miền lesson/feedback/quota cần acceptance ở owner/phase tương ứng. Xem finding F-01. |
| BR-57 | SRS §31.8.1; roadmap Mốc 2 | Age qua profile routes §21.2; catalog/version route chưa xác minh. | Profile revisions Parent/BE1; age-band catalog owner chưa xác minh. | M2-AT-03/10 | Age bounds có nguồn; band names/boundaries/version catalog còn mở. Không claim đầy đủ personalization. |
| BR-58 | SRS §30.4, §31.8.1; roadmap Mốc 2 và Mốc 6 | SRS định nghĩa lesson audience là Parent group hoặc named invitee; canonical lesson-audience routes chưa được xác minh trong M2 crosswalk. | `be1.parent_groups`, `be1.parent_group_members` (BE1); `lesson.access_grants` (Lesson); `parent.profile_share_grants` chỉ là primitive M2, không đồng nghĩa lesson grant. | M2-AT-05/06 | **PARTIAL ở M2**: primitive thu hồi được; audience group/invitee đầy đủ ở M6. |
| NFR-34 | SRS §31.9; roadmap Mốc 2, cross-cutting | Áp dụng profile/assignment/grant/asset/job routes; share/token routes còn chưa canonical. | Parent, BE1, Core, AI Jobs qua typed contracts/ports. | M2-AT-01/02/05/06/08/09 | Yêu cầu cross-cutting, không phải một test đơn lẻ. AT là kế hoạch chưa chạy; không claim NFR đã PASS. |
| NFR-36 | SRS §8, §31.9; roadmap Mốc 2, Mốc 5/6 đề xuất | M2 profile/grant operation có thể thuộc scope; media-access và feedback routes không được chứng minh bởi M2 route set. | BE1/Parent/Core; Lesson/media và feedback owners. | M2-AT-07 | **PARTIAL theo D-143**. Child media→M5 và cross-org feedback→M6 vẫn là đề xuất chưa được owner chọn; AT-07 loại trừ hai phần đó. |
| NFR-38 | SRS §8, §31.9, AC-65; roadmap Mốc 2, Mốc 4/5 đề xuất | Profile/age routes ở §21.2; Story route có mặt nhưng chưa đủ để chứng minh story/video quality contract. | Profile revisions M2; Story M4/Video M5 là mapping đề xuất. | M2-AT-10 | **PARTIAL theo D-143**: M2 chỉ giữ/kiểm locale và age metadata. AC-65 story/video mappings M4/M5 chưa được owner chọn; không claim quality đã đạt. |

### 2.1. Route source precision

SRS §9.6 liệt kê `/v1/me` với mục đích resolve verified identity, role và scope; chính phần đó nói đây là nhóm resource route đề xuất, chưa phải OpenAPI cuối. SRS §21.2 không nêu method/path `/v1/me` hoặc request/response contract. Vì vậy kết luận chính xác là **route group có trong SRS §9.6; method-level canonical contract chưa xác minh trong §21.2**. Draft 7 §4.1 nói GET `/v1/me` không phải route canonical là phù hợp; dòng §4 cần giữ phân biệt này thay vì mô tả route group là hoàn toàn vắng nguồn.

### 2.2. Crosswalk gaps

- **F-01 — P2, BR-49 scope cần được thể hiện PARTIAL rõ:** SRS §31.8/§31.8.1 đưa lesson, feedback, quota và group membership vào tenant boundary. Draft 7 §4 row BR-49 liệt kê các bảng BE1 class/org/enrollment và AT-01/02/04A/04B, nhưng chưa nêu tại chính row đó rằng đây chỉ là M2 foundation slice, không cover đủ lesson/feedback/quota. Roadmap liệt kê BR-49 ở Mốc 2 và trong dải BR-47–54 của Mốc 6 như acceptance xuyên miền, và không tách bảng hay owner riêng cho BR-49; vì vậy đây không chứng minh implementation sai; đây là gap trong traceability để tránh hiểu M2-AT là full BR-49 acceptance. M2 plan/evidence không được claim BR-49 full PASS.
- **F-02 — P3, route wording cần giữ hai tầng nguồn:** `/v1/me` là route group ở SRS §9.6 nhưng thiếu method-level entry trong §21.2. Không tự thêm GET route hoặc biến resource-group proposal thành canonical API.
- Không thấy xung đột trực tiếp giữa phần còn lại của route/table/AT mapping và các nguồn được phép đọc; các mục chưa có bằng chứng vật lý được liệt kê là unknown ở §4, không được suy thành pass.

## 3. Schema và ownership — logical target đối chiếu với physical source

### 3.1. DTR logical ownership

- **Core:** `core.upload_sessions`, `core.upload_parts`, `core.asset_lineage`; `core_asset_metadata` là canonical cho hash, media type, byte size, version và storage/quarantine metadata. Core sở hữu metadata/audit/outbox; asset refs không chứa binary.
- **Parent:** `parent.child_profiles`, `parent.profile_revisions`, `parent.profile_share_grants`, `parent.data_authorizations`. Parent giữ quyền sở hữu profile; grant chỉ cấp scope, không chuyển owner.
- **BE1:** `be1.organizations`, `be1.organization_assignments`, `be1.classrooms`, `be1.managed_profiles`, `be1.enrollments`, profile revisions và Parent groups.
- **Story:** logical `story.runs` dùng `story_run_id`; `story.run_inputs` giữ revision, drawing/voice asset refs và profile/context snapshot; `story.story_revisions`, `story.story_scenes`, `story.review_decisions` là các entity logical trong DTR.
- **Lesson:** `lesson.access_grants` sở hữu audience/capability/state/revocation. Nó không cùng nghĩa với Parent profile share grant.
- **AI Jobs:** DTR mô tả job/attempt/receipts/events qua owner AI Jobs; không có SQL join xuyên owner, dùng typed opaque refs/ports.

### 3.2. Physical source facts và mapping proposal

| Mục | Fact đọc được | Kết luận S0-doc |
|---|---|---|
| Core model | `core_models.py` khai báo Core aggregate revisions, asset metadata có typed owner scope, audit và outbox. | Đây là một phần physical source; không chứng minh toàn DTR Core schema hoặc upload-session persistence. |
| `storyrun_upload_sessions` → `core.upload_sessions` | Draft 7 mô tả physical mapping qua `story_run_lite/tables.py`, nhưng file `tables.py` nằm ngoài approval S0-doc và không được mở. | Chỉ là mapping candidate cần owner/schema review; physical columns/FK chưa xác minh. |
| `run_id` → `story_run_id` | DTR logical `story.runs` dùng `story_run_id`; migration `20261104_story_revisions.py` trực tiếp khai FK tới physical `story.runs.run_id`. | Không tự coi hai tên là cùng định danh hoặc rename-equivalent. Cần mapping có kiểm soát và bảo toàn liên kết/history. |
| Story revision history | Migration trực tiếp tạo physical `story.story_revisions`, `story.story_scenes`, `story.story_revision_reviews`; tạo FK bằng `run_id`, revision ID, scene/review IDs. DTR logical model có `story.story_revisions`, `story.story_scenes`, `story.review_decisions`. | `story_revision_reviews` không được đồng nhất với `story.review_decisions`; `source_asset_sha256` không phải `drawing_asset_ref` hoặc asset version. Field/key/owner mapping chưa được chứng minh. |
| Story owner columns | DTR yêu cầu typed owner scope; `core_models.py` xác nhận typed owner scope ở một số Core model. Base `story.runs` physical definition nằm ở file ngoài approval. | Owner columns của Story run chưa xác minh; không suy từ Core model sang Story. |
| Parent persistence | DTR định nghĩa Parent logical tables; Draft 7 ghi nhận chưa có Parent persistence module trong source review trước đó. | S0-doc không đọc ngoài allowlist để tái xác minh. Physical Parent tables, FK, indexes và implementation status đều **chưa xác minh**. |
| History / asset provenance | DTR đặt asset hash/media canonical tại Core và lineage ở Core; migration thêm `source_asset_sha256`. | Hash là bằng chứng nội dung, không thay opaque asset ref/version. Không xóa hoặc hợp nhất history bằng suy luận. |

**Đề xuất mapping để owner xem (không phải quyết định schema):** giữ `storyrun_upload_sessions` → `core.upload_sessions` và upload parts/receipts như candidate; lập bảng ánh xạ `run_id` ↔ `story_run_id` chỉ khi xác minh được identity/foreign references; xác định typed owner columns cho từng aggregate; ánh xạ asset refs/version riêng khỏi hash; bảo toàn bảng review/history hiện có và phân biệt `story_revision_reviews` với logical `story.review_decisions`. Không có migration hoặc thay schema được đề xuất trong S0-doc.

## 4. Migration graph và bằng chứng thực thi

### 4.1. Nhánh StoryRun-lite

| Revision | `down_revision` | `branch_labels` | `depends_on` | Mức xác minh / ghi chú |
|---|---|---|---|---|
| `20261104_story_revisions` | `20261103_story_upload_compat` | `None` | `None` | Metadata và operation được đọc trực tiếp từ file pin. Thêm `child_age_months`/state checks, tạo revision, scene, review tables; downgrade source thả bảng mới và thu hẹp constraints. Source có downgrade function không bảo đảm downgrade sẽ thành công khi có rows dùng state mới. |
| `20261103_story_upload_compat` | `20261102_story_run_lite` | `None` | `None` | Metadata được báo trong Draft 7; migration module không nằm trong allowlist đọc trực tiếp. Hồ sơ FEAT-064 mô tả non-reversible; chưa xác minh từ module source ở S0-doc. |
| `20261102_story_run_lite` | `None` | `story_run_lite` | `20261102_pv_0001` | Metadata được báo trong Draft 7; module source ngoài allowlist. |
| `20261102_pv_0001` | `None` | `pilot_vision` | `20261101_be1_age_0001`, `20261015_ai_0001` | Metadata được báo trong Draft 7; module source ngoài allowlist. |

Đây chỉ là ancestry nhánh được mô tả, không phải toàn graph/head của checkout. `alembic heads`, `alembic current`, Alembic upgrade/downgrade và `test_migrations.py` đều **NOT RUN**.

### 4.2. Log offline lịch sử

Nguồn owner-run `.claude/handoff/logs/GB2_T12_OFFLINE_20261105A/offline-check.txt` nói rõ không kết nối DB, không network, không thực thi migration; kết thúc “facts only”, không có pass/fail verdict. Log ghi:

- 9 `observed_version_rows` và cùng 9 `script_heads` tại thời điểm đó.
- `current_expansion_of_rows` có 12 mục; `current_expansion_equals_heads=False`, với 3 revision `20261015_ai_0001`, `20261101_be1_age_0001`, `20261102_pv_0001` ở `expansion_not_in_heads`.
- Kế hoạch downgrade chỉ là tính toán: 3 bước qua `20261103_story_upload_compat`, `20261102_story_run_lite`, `20261102_pv_0001`; log ghi 27 bước upgrade plan.
- Sau khi import modules, metadata có 117 bảng; log inventory cũng báo 117 bảng và hai danh sách chênh lệch rỗng.

Log được tạo trước migration `20261104_story_revisions`; không phải graph/head hiện tại, trạng thái DB hiện tại, migration execution evidence hay verdict cho S0-owner-run. Không dùng 9 rows bằng 9 heads của log đó để khẳng định graph checkout hiện hành đã được đối soát.

## 5. Owner decisions và các cổng còn mở

- **D-142:** xác nhận HEAD `dd70685e...` chỉ làm review baseline; không phải implementation approval.
- **D-143:** NFR-36 và NFR-38/AC-65 là PARTIAL trong M2. Child media→M5, cross-org feedback→M6, story→M4, video→M5 vẫn là mapping đề xuất; owner chưa chọn mapping pha.
- **D-144 §9.1:** S0-owner-run dùng DB BE tổng trong Docker chỉ đọc; các pha ghi dùng DB riêng cùng container. Tên/identity DB, người chạy, restore method và bằng chứng synthetic-only phải nằm trong approval S0-owner-run riêng trước khi chạy.
- **D-144 §9.2–§9.4:** giữ 58 synthetic rows, không cleanup; hoãn consent/share và OI-05..08, synthetic-only, deny `REAL`/`LEGACY_UNCLASSIFIED`; B5 legacy receipt chưa mở tới khi consumer xác nhận — đây là hoãn, không phải kết luận không dùng.
- **D-144 §9.5–§9.6:** chưa migrate, giữ history; S0-doc chỉ lập mapping; mypy baseline phải do owner chạy read-only với command/version ghi rõ, M2 không thêm diagnostic.
- **D-144 §9.7:** owner chọn hướng a và xác nhận tương đương chỉ cho B0 plan `plan/B0_B13_SIX_MILESTONE_REDISPOSITION_PLAN_20261102.md`. Hash gốc trong snapshot `03AEA386B8545624100688B68AA828A84CD154B47857CB5E98FB06354D6BB582`; bytes hiện tại `773C4A8340C8E33AE39764D920B042AC19BACBAF6DC561FE9D5D3DFFCC4B5A5A`. Theo D-144, phép so sánh chỉ đọc do phiên điều phối (coordinator) thực hiện (cột Basis của D-144 còn ghi "owner-supplied comparison"; S0-doc chỉ ghi lại theo D-144 và không tự tái kiểm snapshot vì nằm ngoài allowlist): trim trailing whitespace, normalize line endings và bỏ blank cuối thì nội dung tương đương; bỏ mọi whitespace cũng cho kết quả tương đương; cả hai không có CRLF, 3293 so với 3292 bytes. Đây là owner disposition dựa trên kiểm tra chỉ đọc của coordinator, không phải independent review. Không áp dụng cho bảy file khác trong normalization evidence.
- **D-145:** Draft 7 chỉ là planning basis cho S0-doc; S0-owner-run, S1a, S1b, S2, S3 vẫn DRAFT.
- **D-146:** không có implementation approval; DB work, migration, provider, Modal và các phase sau vẫn đóng; `OWNER_MODAL_CALL_APPROVED=NO`.

Các cổng/unknown còn lại gồm: S0-owner-run approval và exact DB identity; route/method contract cho `/v1/me`, invitation/accept/revoke và canonical Teacher profile; profile-share fields/purpose/expiry; age-band catalog/boundaries; physical Parent/Story mapping và owner columns; consumer cần B5 receipt hay không; mypy command/version/output; migration graph hiện tại và schema reconciliation. Không biến default trong Draft 7 thành quyết định.

## 6. Giới hạn của lần đối chiếu này

Đã đọc các nguồn hash-pinned ở §1 trong phạm vi liên quan, Draft 1–4 để xem lịch sử thay đổi, FEAT-063 governance/context/source register, FEAT-064 hồ sơ được ghim, migration `20261104_story_revisions.py`, Core model và offline log. Đây là đọc tài liệu/source theo approval, không phải kiểm thử.

Các đường dẫn sau nằm ngoài allowlist của S0-doc và không được mở; mọi khẳng định cần chúng tiếp tục là **chưa xác minh (ngoài approval)**:

- `backend/src/sketch2life/infrastructure/story_run_lite/tables.py` — physical StoryRun-lite upload/run tables.
- `backend/src/sketch2life/infrastructure/persistence/be1_models.py` — physical BE1 model declarations.
- Các migration module khác, gồm `20261103_story_upload_compat.py`, `20261102_story_run_lite.py`, `20261102_pilot_vision.py` và BE1/AI Jobs migrations.
- Runtime routers, auth/composition source, Parent persistence modules và route tests.
- Database contents/catalog, live Alembic state và `backend/tests/integration/ai_jobs/test_migrations.py` database fixture.

**NOT RUN:** Alembic commands; database/SQL; PostgreSQL tests; `test_migrations.py`; pytest/unit/contract/integration tests; mypy; repository validators; Modal/GPU/provider/network. Không có source/schema thay đổi và không có implementation approval.

## 7. Kết luận cho S0-doc

Evidence này lập crosswalk requirement → route → logical table/owner → M2-AT và ghi rõ unknowns, owner disposition, B0 provenance cùng giới hạn migration/evidence. Finding F-01 và F-02 cần được xem trong review Draft 7; không tự sửa kế hoạch ở đây. S0-doc chỉ có thể được xem là hoàn tất sau independent review và owner decision theo quy trình. Không mở S0-owner-run hoặc phase tiếp theo; không cấp quyền chạy DB, migration, provider hay Modal.
