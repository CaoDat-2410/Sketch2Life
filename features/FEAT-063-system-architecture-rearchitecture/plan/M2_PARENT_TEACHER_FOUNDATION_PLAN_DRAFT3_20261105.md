# Kế hoạch M2 — Parent / Teacher Foundation (Draft 3)

**Feature:** FEAT-063 — System Architecture Rearchitecture  
**Ngày:** 2026-11-05  
**Trạng thái:** **DRAFT / AWAITING OWNER REVIEW**  
**Phạm vi:** sửa kế hoạch theo F1–F9 và các điểm còn lại sau rà soát Draft 2; không phải phê duyệt triển khai, không phải blanket approval cho M3–M6; M2 chưa launch.

## Thay đổi so với Draft 2

Draft 1 và Draft 2 được giữ nguyên, không sửa. Draft 2 đã xử lý đúng F1, F4, F6, F8, F9 và các pin nguồn; 64 đường dẫn repo trong Draft 2 đều tồn tại khi rà soát. Draft 3 chỉ sửa các điểm sau:

| # | Điểm còn lại ở Draft 2 | Cách xử lý ở Draft 3 |
|---|---|---|
| D3-1 | §8 S0-doc liệt kê Draft 1 là candidate path nhưng lại cấm sửa Draft 1; không phân biệt path chỉ đọc với path có thể sửa; hồ sơ CONTEXT/DECISIONS/STATUS/TASK_APPROVAL xuất hiện như candidate sửa. | §8 tách hai cột "Chỉ đọc" và "Candidate có thể sửa". Draft 1/2/3 là chỉ đọc. Hồ sơ governance chỉ do phiên ghi (Codex) cập nhật sau lệnh của owner, nằm ngoài allowlist của phiên thực thi. Test hiện có là baseline hồi quy chỉ đọc; test M2 là file mới chưa xác minh. |
| D3-2 | BR-58 được map sang M2-AT-04 (assignment/enrollment), không phải primitive grant/revoke như F5 yêu cầu. | BR-58 phần M2 map sang primitive grant/revoke có thể thu hồi (M2-AT-05/06, S1b); M2-AT-04 chỉ còn FR-PL-02/BR-49. Group/invitee lesson đầy đủ vẫn thuộc M6. |
| D3-3 | M2-AT-07 (NFR-36) không có trong tiêu chí thoát của pha nào. | Gán M2-AT-07 vào tiêu chí thoát S1b và đối chiếu ở S3. |
| D3-4 | M2-AT-08 gắn FR-PL-01 dù là test lifecycle/idempotency, không có nguồn FR-PL. | Nguồn ghi là roadmap Mốc 2 (owner-lock/cancel/restart), D-127 và NFR-34; nêu rõ không phải FR-PL. |
| D3-5 | S1a "S0-owner-run nếu approval yêu cầu DB", trong khi M2-AT-01/02/03/04/10 cần PostgreSQL. | S1a phụ thuộc S0-owner-run đã đóng; S1a-doc/unit chỉ chạy được trước đó nếu approval tách riêng. |
| D3-6 | N-1 là cổng S2 nhưng không có vị trí test trong §8 S2; test route hiện có monkeypatch `_build_child_binding`. | §8 S2 thêm test N-1 là file mới chưa xác minh; test_pilot_assistance_routes_t9.py ghi là chỉ đọc, dùng để đối chiếu vì nó monkeypatch `_build_child_binding` (dòng 257). |
| D3-7 | S0-owner-run chỉ liệt kê migration là input; đối soát schema vật lý còn cần module định nghĩa bảng. | Thêm be1_models.py, ai_jobs/sql/tables.py, story_run_lite/tables.py là input chỉ đọc; module bảng Core/Parent chưa xác minh. |

## Thay đổi của Draft 2 so với Draft 1 (giữ để truy vết)

| Finding | Cách xử lý |
|---|---|
| F1 — Xung đột namespace kiểm thử | Đổi mã test của kế hoạch sang tiền tố M2-AT; định nghĩa Given/When/Then, tầng test, nhu cầu DB và requirement tại §4.2. |
| F2 — Allowlist chưa cụ thể | Viết lại §8 theo S0-doc, S0-owner-run, S1a, S1b, S2, S3; chỉ nêu file hiện có, file mới ghi chưa xác minh, có exclusions và hard stop. Đây không phải quyền sửa file. |
| F3 — Thiếu route trong crosswalk | Thêm cột Route tại §4, phân biệt route SRS §21.2, suy luận và chưa xác minh. |
| F4 — NFR-38 | Đánh dấu PARTIAL; M2 chỉ claim metadata vi-VN và tuổi 36–120 được bảo toàn qua contract. AC-65 về chất lượng sư phạm chuyển sang M4/M5, chờ owner xác nhận. |
| F5 — BR-58 | Dùng đúng nghĩa SRS: lesson audience là nhóm Parent hoặc người được mời cụ thể và có thể thu hồi. Primitive grant/revoke thuộc nền M2; audience lesson đầy đủ thuộc M6. |
| F6 — Provenance B0 | Dẫn evidence chuẩn hóa và hash; yêu cầu owner xác nhận normalized bytes tương đương. Bản gốc trong snapshot git-ignore chưa được phiên này xác minh. |
| F7 — Phân pha | Tách S0 thành S0-doc/S0-owner-run và S1 thành S1a/S1b; thêm tiêu chí đóng/stop gate. N-1 và stale-owner B1 là cổng thoát S2; OpenAPI P3/freeze là cổng S3. |
| F8 — Quyết định owner | Thêm lựa chọn, hệ quả, pha bị chặn và mặc định đề xuất. Ghi nhận roadmap đã yêu cầu baseline mypy và không thêm lỗi mới. |
| F9 — Migration evidence | Phân biệt kế hoạch ngoại tuyến với migration đã chạy. Không khẳng định 27 bước đã chạy hoặc chạy trong một transaction; full-head downgrade không được thực thi trong evidence đã rà. |

## 0. Trạng thái, checkout và sai lệch quy trình pin

Checkout khi lập Draft 3: branch feature/feat063-be-foundation, HEAD 1e109b1726f327ac9383457b0dbdd535ef5c6518, parent b6dbfa68e66718f3f40902c093e9ebd634b1ebb9. Index rỗng. Trước khi tạo Draft 3, thay đổi local duy nhất được ghi nhận là Draft 1 và Draft 2 untracked. Hash Draft 1: F47393FD1028B20D841114786E7D07B12BC8C89A67EF6697F0396EFCA7942E81. Hash Draft 2: A09F7E6BF8534E85EE4EE4573209B5346861008AA4A5C4A8C907CF4EFEDCFE66.

Prompt ban đầu lập Draft 1 ghim HEAD b6dbfa68e66718f3f40902c093e9ebd634b1ebb9, nhưng checkout là commit 1e109b1726f327ac9383457b0dbdd535ef5c6518, con trực tiếp sau commit hợp nhất B1/B2. Lượt độc lập đầu tiên đã dừng đúng cổng. Sau đó phiên điều phối cập nhật pin HEAD trong lời nhắn tiếp tục và cho cùng phiên làm tiếp mà chưa có xác nhận riêng của owner. Đây là sai lệch quy trình cần owner xác nhận qua approval; Draft 2 và Draft 3 không hợp thức hóa nó. Mười hai hash tài liệu được kiểm tra lại và đều khớp pin. Việc kiểm tra đó không thay cho owner xác nhận.

Tài liệu này chỉ là kế hoạch. Không có quyền implementation, migration, thao tác DB, provider, Modal, tích hợp frontend hoặc M3–M6. B2 được owner chấp nhận có điều kiện trong FEAT-064; điều đó không phải approval M2. OWNER_MODAL_CALL_APPROVED vẫn NO.

## 1. Căn cứ và pin nguồn

Các hash là giá trị của bytes trong working copy, đã kiểm tra trước khi tạo Draft 2. Không chuẩn hóa line ending hoặc thay pin.

### 1.1. FEAT-063

| Tài liệu | SHA-256 |
|---|---|
| features/FEAT-063-system-architecture-rearchitecture/plan/BE_PARENT_TEACHER_VISION_DEMO_ROADMAP_20261102.md | A0A485EE421FBB1DA9DEC99DD8EC08279D14EAF27EC548AD6A0A4CE8F234F8FA |
| features/FEAT-063-system-architecture-rearchitecture/plan/B0_B13_SIX_MILESTONE_REDISPOSITION_PLAN_20261102.md | 773C4A8340C8E33AE39764D920B042AC19BACBAF6DC561FE9D5D3DFFCC4B5A5A |
| features/FEAT-063-system-architecture-rearchitecture/plan/BACKLOG_API_REV37_SRS23_MODAL_20261030.md | 380BF9F813CF809E35D9EA6F843E33A0DF892BA886E8C366AEB1C0F757A57391 |
| features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md | DCBF9786FF8983E34F2D3B4EBAB76301D0C52A6C9DE72CD08D0816BBD0D983FC |
| features/FEAT-063-system-architecture-rearchitecture/artifacts/DATA_TABLE_REGISTER.md | 3E793BB2C62C9E6C50780DE636EDDE442D382C62B4643552F2298AF374171E22 |
| features/FEAT-063-system-architecture-rearchitecture/status/STATUS.md | 436273EC326CB43540ADB8EC1E03B0D65AFEDC60D2C643D44D1D2ADD5B21AC88 |
| features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md | 12DC66EDC384179FB28957F2121BC49981E72F7A24759560C86EF11023FD3E3C |
| features/FEAT-063-system-architecture-rearchitecture/CONTEXT.md | 602A026DB577644427FA65E85244E30C3F53A3B31D78A849C5D0F0D258E665E8 |
| features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md | 3023D112B3BCDF7534CC3D0399D517AD27193B228CE8CF8B54FEC94F5569E18A |

### 1.2. FEAT-064

| Tài liệu | SHA-256 |
|---|---|
| features/FEAT-064-current-flow-modal-vision-dev/evidence/A2_REV3_INDEPENDENT_REVIEW_CLOSEOUT_20261103.md | 10B12F4417A5E29DF0ED1697F33A8FAA08D692E71015998CCC8DE297328A1C36 |
| features/FEAT-064-current-flow-modal-vision-dev/plan/FEAT064_A2_B1_B2_SEQUENTIAL_GOAL_20261103.md | D7DEE2977C5AA28B26FCB117281DE8B23E4D4AA85A42922B8B37752FBDA8752A |
| features/FEAT-064-current-flow-modal-vision-dev/approvals/TASK_APPROVAL.md | 9D07B88190E8F5831D79431A79C2AAC944B266CB28CD29265E5D0283B77921B8 |

### 1.3. Căn cứ và provenance

- Đã đọc AGENTS.md, .codex/sketch2life-harness.md, CONTEXT.md, SOURCE_REGISTER.md, DECISIONS.md, roadmap, status, approvals, backlog, SRS, DTR, A2/B2 records và migration liên quan. Các pin ở §1.1–§1.2 là nguồn làm việc; không suy diễn ngoài nguồn.
- D-132 chấp nhận roadmap sáu mốc làm baseline lập kế hoạch. SRS v2.3-draft chưa ký; route matrix chưa phải OpenAPI cuối.
- DTR mô tả ownership logic, không xác nhận schema vật lý. S0-owner-run cần đối soát owner-run và approval riêng.
- B0 plan hiện có hash 773C4A8340C8E33AE39764D920B042AC19BACBAF6DC561FE9D5D3DFFCC4B5A5A; hồ sơ duyệt ghi bytes gốc hash 03AEA386B8545624100688B68AA828A84CD154B47857CB5E98FB06354D6BB582.
- Evidence features/FEAT-063-system-architecture-rearchitecture/evidence/COMMIT_WHITESPACE_NORMALIZATION_20261103.md có SHA-256 AF649B1518C4D550C2AEDE173063D6C46A889A7ADC9A70F187E86A23C72199C2. Evidence ghi nhận tám file được chuẩn hóa khoảng trắng/line ending theo yêu cầu owner và bảng hash gốc → chuẩn hóa, gồm hai hash B0 trên. Evidence nói bản gốc được sao lưu trong snapshot cục bộ git-ignore; phiên này không đọc hoặc xác minh snapshot đó. Vì vậy không tự kết luận normalized bytes tương đương nội dung đã duyệt; cần owner xác nhận.
- OI-05..08 được tìm thấy trong SRS lịch sử v2.2; mapping sang SRS v2.3 chưa xác minh. Các câu hỏi được giữ mở tại §9.
- Route share Parent, schema vật lý Parent, catalog tuổi và một số owner columns chưa được đóng; đánh dấu chưa xác minh.
- M1 là demo synthetic local. M1/A2/B1/B2 không cấp quyền cho M2.

## 2. Mục tiêu M2 và phạm vi

### 2.1. Mục tiêu đề xuất

Thiết lập nền tảng Parent/Teacher cho identity, tenant/role, profile, age provenance, owner/scope, asset, revision, durable job và lifecycle. Consent/share chỉ triển khai nếu quyết định owner và các cổng nguồn/chính sách được thỏa.

Mục tiêu là hợp đồng và ranh giới owner rõ ràng. Không tạo FK hoặc SQL join xuyên owner/schema; cross-owner reference là typed opaque reference được xác minh qua application port.

Roadmap đề xuất B3 (manifest mới và owner/sign-off), B4b (consent sau khi xác định OI-05..08; trước khi mở gate phải từ chối REAL và LEGACY_UNCLASSIFIED), phần nền B6/B7/B10; B5 chỉ nếu còn requirement receipt legacy. B12 áp dụng xuyên pha.

### 2.2. Ngoài phạm vi

- M3: media intake, transcript/input revision và Parent line-sketch theo Q146.
- M4: story content, script, rewrite và đánh giá chất lượng sư phạm theo AC-65.
- M5: video, quota/usage/compute, provider, Modal/GPU.
- M6: lesson audience đầy đủ, occurrence/sample, roster, sharing/moderation/history/commerce/billing.
- Không khóa model/version, lịch line-sketch, consent policy hoặc lesson access thay owner.
- Không có quyền provider, Modal, GPU, external service hoặc network.

### 2.3. NFR-38 trong M2

M2 chỉ claim metadata ngôn ngữ vi-VN và tuổi 36–120 được bảo toàn qua profile contract/revision. Không claim chất lượng Montessori-inspired, child-centered hoặc adult-guided. AC-65 cho chất lượng story/video chuyển sang M4/M5; vì roadmap hiện gán NFR-38 cho M2 nên việc chuyển cần owner xác nhận. NFR-38 là PARTIAL, không phải PASS.

## 3. Subphase M2 đề xuất

Đây là thứ tự để owner xét. Mỗi subphase cần Task Approval riêng với scope, file allowlist, evidence, DB identity và command ceiling. Hoàn tất một pha không tự mở pha kế tiếp.

| Pha | Phụ thuộc | Nội dung | Tiêu chí thoát có thể kiểm chứng | Stop gate |
|---|---|---|---|---|
| S0-doc | Không | Đối chiếu nguồn, mapping schema, owner decisions, B0 provenance và migration graph trên giấy; không chạy command/DB. | Requirement có source ID; unknown được gắn nhãn; route/table/owner/AT có crosswalk; B0 provenance được owner disposition hoặc vẫn block; không claim implementation approval. | Hash lệch, owner assumption bị coi là quyết định, hoặc cần truy cập DB/file ngoài approval. |
| S0-owner-run | S0-doc; owner chọn DB và ghi approval riêng | Owner chạy đối soát schema vật lý/Alembic và ghi mypy baseline theo command/hash được duyệt. | DB identity khớp manifest; bảng/version/chênh lệch được ghi; baseline mypy có output thật, không suy diễn phần chưa chạy. | Chỉ dùng DB task-owned được pin; sai identity, thấy dữ liệu không synthetic hoặc cần write/migration thì dừng. Pha này không cấp phép migration. |
| S1a identity/tenant/profile/age | S0-doc đóng; S0-owner-run đóng (M2-AT-01/02/03/04/10 cần PostgreSQL thật; phần unit/doc chỉ chạy trước nếu approval tách riêng) | Identity/role assignment, tenant isolation, profile ownership và age provenance. | M2-AT-01/02/03/04/10 đạt theo tầng đã duyệt; route test persistence dùng PostgreSQL thật và wiring thật. | Thiếu role matrix, profile owner hoặc age policy thì deny-by-default; không tự tạo route/policy. |
| S1b grant/revoke/consent | S1a; owner quyết định 3; OI gate đã xác định | Scoped grant/revoke, purpose/expiry/audit và consent/data authorization trong phạm vi được chọn. | M2-AT-05/06/07 đạt; thiếu, pending, revoked hoặc expired đều deny; admin thiếu scope/reason bị deny. Nếu B4b hoãn thì REAL và LEGACY_UNCLASSIFIED bị từ chối; không claim consent production-ready. | OI mapping, purpose, fields, expiry hoặc policy chưa chốt thì không bật share/consent. |
| S2 owner/job/asset/revision/lifecycle | S1a; S1b nếu bật; migration target đã duyệt | Durable owner/scope refs, job/asset/revision, AiJobService mapping, idempotency/replay, cancel, restart/recovery, DELETE_PENDING/D-127. | M2-AT-07/08/09 đạt. N-1 route PostgreSQL test child request → job → status phải dùng wiring thật. B1 orphan có invalidation/reconciliation/read-exposure contract và regression trước dữ liệu non-synthetic/provider. | Orphan có thể được đọc/công bố như accepted result, job/aggregate lệch, hoặc thiếu N-1 thì chưa thoát S2. |
| S3 freeze và đóng M2 | S1a, S1b theo disposition, S2 | Đối chiếu evidence và freeze contract; đóng OpenAPI P3 hai POST submit/cancel trước frontend/client. | Tất cả M2-AT (gồm đối chiếu M2-AT-07) pass hoặc PARTIAL disposition được owner ghi; OpenAPI parity được kiểm; conditions được gán owner/phase; independent review ACCEPTED. | Không tích hợp frontend/client khi OpenAPI P3 còn mở; không tự mở M3. |

## 4. Traceability requirement → route/API → bảng → owner → acceptance

Route là candidate theo SRS v2.3-draft, chưa freeze. “SRS §21.2” nghĩa là path có trong route table; “suy luận” là mapping chưa gắn trực tiếp; “chưa xác minh” là chưa có route canonical.

| Requirement | Route/API và nguồn | Bảng/owner logic theo DTR | Acceptance |
|---|---|---|---|
| FR-PL-01 | POST /v1/parent/profiles; GET/PATCH /v1/parent/profiles/{profile_id} — SRS §21.2. Identity endpoint — chưa xác minh. | parent.child_profiles, parent.profile_share_grants; be1.adult_identities, be1.organization_assignments; core audit — Parent/BE1/Core. | M2-AT-01/05. |
| FR-PL-02 | POST /v1/organizations/{org_id}/classes; POST /v1/classes/{class_id}/assignments; POST /v1/classes/{class_id}/profiles — SRS §21.2. List/read routes chưa xác minh. | be1.organizations, classrooms, organization_assignments, enrollments — BE1; consumer scope thuộc owner tương ứng. | M2-AT-02/04. |
| FR-PL-07 | Parent profile POST/GET/PATCH là SRS §21.2, không phải grant. Invite/accept/revoke route — chưa xác minh. | parent.profile_share_grants, parent.child_profiles, parent.data_authorizations; be1.managed_profiles — Parent/BE1. | M2-AT-05. |
| FR-PL-08 | Profile GET/PATCH và POST /v1/story-runs — SRS §21.2. Grant/download/token/cache/revoke route — chưa xác minh. | parent.profile_share_grants, core.asset_lineage, ai_jobs.job/receipts — Parent/Core/AI Jobs. | M2-AT-06/09. |
| FR-PL-25 | Parent profile POST/GET/PATCH và POST /v1/classes/{class_id}/profiles — SRS §21.2. Age-band catalog route — chưa xác minh. | parent.profile_revisions, be1.profile_revisions, age-band catalog — Parent/BE1/catalog owner chưa xác minh. | M2-AT-03/10. |
| BR-48 | Profile route không phải share route. Parent share invite/accept/revoke — chưa xác minh. | parent.profile_share_grants, parent.data_authorizations — Parent. | M2-AT-05/06; thiếu grant phải deny. |
| BR-49 | POST /v1/organizations/{org_id}/classes; POST /v1/classes/{class_id}/assignments; POST /v1/classes/{class_id}/profiles — SRS §21.2. | be1.organizations, classrooms, organization_assignments, enrollments — BE1. | M2-AT-01/02/04. |
| BR-57 | Age qua profile routes SRS §21.2; catalog/version route — chưa xác minh. | Profile revisions, age-band catalog — Parent/BE1/catalog owner chưa xác minh. | M2-AT-03/10. |
| BR-58 | Nghĩa SRS: audience lesson là nhóm Parent hoặc người được mời cụ thể và có thể thu hồi. Route class assignment/profile (SRS §21.2) không phải lesson-audience grant và không dùng để chứng minh BR-58. Route grant/revoke và route lesson grant cho nhóm Parent hoặc invitee — chưa xác minh; phần audience đầy đủ thuộc M6. | be1.parent_groups/parent_group_members (BE1); lesson.access_grants (Lesson); primitive M2 dùng parent.profile_share_grants. | M2: chỉ primitive grant/revoke có thể thu hồi qua M2-AT-05/06 (S1b). M6: audience nhóm/invitee đầy đủ; BR-58 PARTIAL trong M2. |
| NFR-34 | Áp dụng cross-cutting trên profile, assignment, grant, asset/job routes; share/token routes — chưa xác minh. | Parent, BE1, Core, AI Jobs qua contract/ports. | M2-AT-01/02/05/06/08/09. |
| NFR-36 | Admin/class assignment route trong SRS §21.2; media/admin-grant/feedback paths chưa xác minh trong M2; feedback đầy đủ thuộc mốc sau. | BE1/Parent/Core/Lesson owners. | M2-AT-07 cho access primitive/audit. |
| NFR-38 | Profile/age routes trong SRS §21.2; story/video quality routes thuộc M4/M5. | Profile metadata M2; story/video owner M4/M5. | M2-AT-10 chỉ metadata; NFR-38 PARTIAL tới khi owner disposition và AC-65 thực hiện ở mốc phù hợp. |

### 4.1. Route candidates theo SRS

SRS §21.2 nêu các route nền M2:

- POST /v1/parent/profiles
- GET/PATCH /v1/parent/profiles/{profile_id}
- POST /v1/organizations/{org_id}/classes
- POST /v1/classes/{class_id}/assignments
- POST /v1/classes/{class_id}/profiles

Không tự thêm route share, identity, revoke, admin media hoặc age-band. GET /v1/me từng là suy luận độ tin cậy thấp, không phải route canonical. SRS §21.2 có các route upload/story/job; chỉ dùng trong M2 khi owner duyệt scope. Placeholder org/organization phải thống nhất trước freeze OpenAPI.

### 4.2. Định nghĩa M2 acceptance tests

Các test dưới đây là kế hoạch, chưa chạy. Route test phải dùng PostgreSQL thật, wiring thật, không monkeypatch route/dependency cần kiểm.

| ID | Requirement/pha | Given / When / Then | Tầng | DB task-owned |
|---|---|---|---|---|
| M2-AT-01 | FR-PL-01, BR-49, NFR-34; S1a | Given Parent/Teacher/Admin có role/assignment hợp lệ hoặc thiếu/thu hồi; when đọc/ghi resource; then chỉ role/scope hợp lệ được phép, denial không lộ metadata ngoài scope, audit metadata-only. | Domain/service unit, HTTP contract, route PostgreSQL. | Có cho route/persistence; không cho unit. |
| M2-AT-02 | FR-PL-02, BR-49; S1a | Given hai organization; when principal tenant A truy cập resource tenant B; then deny theo contract, không lộ existence/content. | Unit matrix và route integration wiring thật. | Có cho integration. |
| M2-AT-03 | FR-PL-25, BR-57; S1a | Given tuổi 36/120, ngoài biên, provenance/version; when tạo và đọc profile revision; then áp dải owner chốt, giữ provenance và không suy ra band chưa định nghĩa. | Domain/contract unit và repository integration. | Có cho persistence. |
| M2-AT-04 | FR-PL-02, BR-49; S1a | Given Teacher active hoặc không có assignment; when POST assignment/profile theo route SRS; then chỉ actor đủ quyền tạo đúng assignment/enrollment, revoked/sai tenant bị deny. | Route PostgreSQL acceptance không mock wiring. | Có. |
| M2-AT-05 | FR-PL-07, BR-48, BR-58 (primitive thu hồi được); S1b | Given grant pending/active/revoked/expired với purpose/scope; when đọc profile; then chỉ grant active đúng scope cho phép. Nếu canonical route chưa chốt, chỉ test domain/service và S1b chưa đóng. | Unit trước; route PostgreSQL sau khi route được duyệt. | Có cho route/persistence. |
| M2-AT-06 | FR-PL-08, BR-48, BR-58 (primitive thu hồi được), NFR-34; S1b | Given field-scoped grant liên kết asset/token/cache/job; when revoke; then lần đọc/tải mới, token/cache access và job chưa accepted bị chặn, audit không ghi content/token. | API/asset/job integration; không gọi provider. | Có. |
| M2-AT-07 | NFR-36; thoát S1b, đối chiếu S3 | Given Admin thiếu scope/reason hoặc access hợp lệ; when thao tác admin thuộc M2; then thiếu điều kiện bị deny, access hợp lệ audit metadata. Feedback cross-org bị từ chối ở owner/mốc feedback. | Unit + route integration cho primitive M2; feedback ở mốc sau. | Có cho route M2. |
| M2-AT-08 | Roadmap Mốc 2 (owner-lock, cancel, restart, ownership của job), D-127, NFR-34 — nguồn roadmap/decision, không phải FR-PL; S2 | Given idempotency key, owner-lock cạnh tranh, stale/replay và restart; when retry/cancel/recover; then không tác dụng phụ trùng, stale result không accepted, aggregate/job/receipt khớp contract. | PostgreSQL integration/restart với repository thật. | Có. |
| M2-AT-09 | FR-PL-08, NFR-34; S2 | Given child request → job → status với success/timeout/orphan/recovery; when đi qua route/lifecycle thật; then status có thẩm quyền, orphan không được đọc/công bố như accepted; N-1 và B1 gate đạt. | Route PostgreSQL với wiring thật, không monkeypatch. | Có, bắt buộc. |
| M2-AT-10 | FR-PL-25, BR-57, NFR-38; S1a | Given locale vi-VN và tuổi 36–120; when serialize, persist, đọc profile revision; then metadata được giữ. Không đánh giá chất lượng Montessori/child-centered/adult-guided. | Contract/unit và persistence integration. | Có cho persistence. |

## 5. Dữ liệu, ownership và migration

### 5.1. Ownership logic theo DTR

| Owner | Nhóm bảng logic |
|---|---|
| BE1 | organizations, adult_identities, organization_assignments, classrooms, managed_profiles, enrollments, consent_records, data_lifecycle_requests, profile_revisions, profile_context_entries, profile_support_needs. |
| Parent | child_profiles, profile_revisions, profile_context_entries, profile_support_needs, data_authorizations, profile_share_grants. |
| Core | asset_lineage, upload_sessions, upload_parts, upload_command_receipts và Core metadata/audit/revision hiện hành. |
| AI Jobs | job, attempt, command/completion receipts, semantic_request, cancellation_notice, outbox, job_events. |
| Story | runs, run_inputs, review_decisions, command receipts và các bảng Story theo DTR. |

Đây là ownership logic theo DTR, không xác nhận schema vật lý. Không tạo FK/SQL join xuyên owner/schema. Aggregate, job, asset và receipt có state riêng; job progress không thay aggregate state.

### 5.2. Mapping demo và 58 hàng synthetic

- Map storyrun_upload_sessions sang core.upload_sessions; map story.runs.run_id sang story.runs.story_run_id; ghi owner columns, asset refs và history. Không đổi nghĩa hoặc xóa history âm thầm.
- B3 manifest/sign-off là đề xuất tới khi owner ký đúng bytes.
- A2 ghi còn 58 synthetic rows sau lỗi teardown. Owner chọn giữ, copy/di trú có mapping và approval, hoặc cleanup qua approval riêng. Mặc định giữ nguyên; không reset shared sketch2life.
- Trước migration: DB task-owned, physical schema inventory, target Alembic graph/revision, snapshot/restore expectation, exact approval. Kết quả B2 không chứng minh trạng thái DB hiện tại.

### 5.3. Alembic graph và command ceiling

Repository có nhiều root/head và depends_on; không dùng upgrade heads làm đích M2 mặc định. Offline graph check owner-run ghi upgrade plan step count 27 khi tính từ DB rỗng. Đây là kế hoạch ngoại tuyến, không chứng minh migration đã chạy. Evidence .claude/handoff/logs/GB2_T12_OFFLINE_20261105A/offline-check.txt có SHA-256 6FF16B2E77EE7DB7CE18521484B92FAA9B40F685393D35A7746E74236313E143. Evidence đã rà không đủ để khẳng định 27 bước đã chạy trong một transaction.

Approval features/FEAT-064-current-flow-modal-vision-dev/approvals/TASK_APPROVAL.md ghi kế hoạch downgrade pilot_vision@base từ full heads có ba bước; bước đầu là 20261103_story_upload_compat, migration source ném RuntimeError vì không reversible. Đây là kết quả graph/source trong hồ sơ, không phải bằng chứng full-head downgrade thực tế đã chạy rồi thất bại. Round-trip thực tế được giới hạn ở nhánh pilot_vision, trạng thái trung gian, DB mới và chín bảng pilot rỗng.

Điều kiện migration tương lai:

1. S0-doc ghi graph, target revision, depends_on và lý do chọn.
2. S0-owner-run chỉ đọc physical schema/Alembic trên DB task-owned sau approval riêng.
3. Migration irreversible không rollback bằng downgrade; cần compatibility/additive rollback được duyệt. Không sửa 20261103_story_upload_compat.py để làm test xanh.
4. DB task-owned: tối đa một upgrade tới target revision đã pin. Downgrade chỉ khi static graph chứng minh reversible, target cụ thể và approval ghi rõ; tối đa một downgrade rồi một re-upgrade nếu được duyệt. Nhánh irreversible: upgrade disposable rồi dừng.
5. Không drop DB/cleanup mặc định. Chỉ xóa rows do test tạo, có owner rõ và FK order, trong approval.
6. backend/tests/integration/ai_jobs/test_migrations.py dùng maintenance connection để tạo/xóa DB; phần DB của test không chạy trên DB duy nhất nếu chưa có thiết kế/approval riêng.

## 6. Lifecycle, authorization và điều kiện kế thừa

### 6.1. Lifecycle

- Tách state aggregate, job, asset, receipt; định nghĩa owner-lock, concurrency, idempotency, cancel và stale/replay.
- D-127: cancel sau PREPARATION_REVIEW chuyển DELETE_PENDING, nhả active owner nhưng giữ result/assets/receipts. DELETE_PENDING không có nghĩa dữ liệu đã bị xóa.
- Đánh giá lại nếu thêm worker/process hoặc durable AI Jobs; M1 StoryRun-lite chưa tích hợp AiJobService.
- Không nhận stale/orphan result là accepted. Trước worker/provider hoặc dữ liệu non-synthetic phải có invalidation/reconciliation, read-exposure contract, terminal state và regression. Chưa có evidence orphan được đọc/công bố như accepted; cũng không coi absence-of-evidence là đã xử lý.

### 6.2. B12 và privacy

B12 áp dụng xuyên pha: privacy, authorization, safety, idempotency, stale/replay, observability, restart/recovery, failure mapping. Deny-by-default; revoke phải được kiểm tra trên API, asset/download, token, cache và job dispatch thuộc scope. Audit metadata-only, không log child content/media/token/secret. Admin access cần scope/reason/audit. Không ghi “role matrix đã được owner duyệt” hoặc “contract đã được owner duyệt” khi không có pin nguồn.

### 6.3. A2/B1/B2 conditions

- A2/FEAT-064 còn 58 synthetic rows và physical-schema/Alembic mismatch cần đối soát; không dọn DB chung.
- B1 stale-owner orphan cần invalidation/reconciliation/read-exposure contract và regression trước dữ liệu non-synthetic/provider. N-1 phải là route-level PostgreSQL test child request → job → status với wiring thật, không monkeypatch; cả hai là cổng thoát S2.
- B2 T13 chỉ chứng minh timeout của script-local helper với stub, không chứng minh job thật chuyển UNKNOWN.
- B2 T12 chỉ chứng minh pilot_vision intermediate-state round-trip trên DB mới với bảng pilot rỗng; không phải full-graph/story_run_lite. test_migrations.py DB NOT RUN.
- OpenAPI P3 hai POST submit/cancel phải đóng trước frontend/client. Route dùng shared router; scope file phải được nêu/duyệt rõ ở S3.
- mypy test_be1_postgres_api.py NO VERDICT; cần baseline thật và không thêm diagnostic.
- Dữ liệu DB A2/B1/B2 là owner-run, không phải coordinator độc lập xác minh. OWNER_MODAL_CALL_APPROVED=NO.

## 7. Acceptance criteria và stop gates

1. Mỗi requirement §4 có route status, bảng logic, owner, M2-AT và evidence. Cho phép NFR-38 PARTIAL chỉ khi owner ghi disposition và AC-65 được chuyển có chủ đích sang M4/M5; BR-58 PARTIAL (chỉ primitive thu hồi được, audience lesson đầy đủ ở M6) cũng cần owner ghi disposition; PARTIAL không phải PASS.
2. Identity, role, tenant, profile ownership, assignment và age provenance đạt M2-AT-01/02/03/04/10 với positive/negative tests; DB thật cho route/persistence.
3. Grant/consent theo quyết định 3/OI gate; thiếu grant/policy thì deny, REAL và LEGACY_UNCLASSIFIED bị chặn nếu B4b hoãn.
4. Lifecycle đạt M2-AT-08/09; N-1 PostgreSQL route test với wiring thật bắt buộc; B1 orphan có reconciliation/read-exposure contract và regression trước khi thoát S2.
5. Target migration/schema inventory/data disposition/rollback limits được owner phê duyệt; DB/source/snapshot gate lệch thì dừng.
6. OpenAPI request/response/error parity được freeze trước client integration; P3 đóng trong S3.
7. Evidence lưu tại feature evidence path được approval chỉ định; PARTIAL/NOT RUN/owner-run provenance ghi đúng. Plan review và implementation review là hai việc riêng.
8. Không mở M3–M6 và không bật provider/Modal.

## 8. Candidate allowlist theo subphase

Các path dưới đây đã được xác nhận tồn tại khi rà soát (trừ cột "Path mới", ghi chưa xác minh). Bảng chỉ là candidate để owner/reviewer xem xét trước Task Approval; không cấp quyền sửa. Không dùng wildcard.

Quy ước:

- **Chỉ đọc:** tham chiếu hoặc baseline hồi quy; không được sửa nếu Task Approval không nêu đích danh file và lý do.
- **Candidate có thể sửa:** chỉ được sửa khi Task Approval của đúng pha liệt kê file đó, kèm hash trước khi sửa.
- **Path mới:** file chưa tồn tại; tên và hash phải có trong approval trước khi tạo. Test hiện có là baseline hồi quy chỉ đọc; test M2 là file mới.
- **Hồ sơ governance** (CONTEXT, DECISIONS, STATUS, TASK_APPROVAL của FEAT-063/FEAT-064, ledger) chỉ do phiên ghi (Codex) cập nhật sau lệnh của owner. Chúng nằm ngoài allowlist của mọi phiên thực thi và chỉ đọc đối với phiên thực thi.
- Draft 1, Draft 2 và Draft 3 của plan này là chỉ đọc; bản kế tiếp phải là file mới.

| Pha | Chỉ đọc | Candidate có thể sửa | Path mới (chưa xác minh) | Exclusions / hard stop |
|---|---|---|---|---|
| S0-doc | Mọi tài liệu pin ở §1; features/FEAT-063-system-architecture-rearchitecture/SOURCE_REGISTER.md; features/FEAT-063-system-architecture-rearchitecture/evidence/COMMIT_WHITESPACE_NORMALIZATION_20261103.md; Draft 1/2/3 của plan này; hồ sơ governance. | Không có file hiện có. | Bản plan kế tiếp; evidence addendum S0-doc (tên chưa xác minh). | Không sửa source/test/migration/SRS/DTR/roadmap/governance. Cần DB hoặc file ngoài approval thì dừng. |
| S0-owner-run | backend/alembic/env.py; backend/alembic/versions/20261014_0002_be1_runtime.py; backend/alembic/versions/20261015_ai_0001_ai_jobs_schema.py; backend/alembic/versions/20261028_ll_0001_lesson_library.py; backend/alembic/versions/20261031_be1_synthetic_eligibility.py; backend/alembic/versions/20261101_be1_age_provenance.py; backend/alembic/versions/20261102_pilot_vision.py; backend/alembic/versions/20261102_story_run_lite.py; backend/alembic/versions/20261103_story_upload_compat.py; backend/src/sketch2life/infrastructure/persistence/be1_models.py; backend/src/sketch2life/infrastructure/ai_jobs/sql/tables.py; backend/src/sketch2life/infrastructure/story_run_lite/tables.py. Module định nghĩa bảng Core/Parent: chưa xác minh. | Không có; allowlist ghi repo rỗng. | Đường dẫn evidence output và script owner-run (hash ghim trong approval) — chưa xác minh. | Chưa có DB identity, command, hash, snapshot, approval thì không chạy. Không migration, không shared DB, không ghi source. |
| S1a | backend/src/sketch2life/infrastructure/identity/firebase_token_verifier.py; backend/src/sketch2life/domain/child_age.py; backend/src/sketch2life/contracts/schemas/child_learning_profile.py (hai file này chỉ chuyển sang candidate sửa nếu approval đổi chính sách tuổi/contract); baseline hồi quy: backend/tests/unit/test_profile_age_invariant.py; backend/tests/unit/test_age_provenance_columns.py; backend/tests/unit/test_child_learning_profile_contract.py; backend/tests/contract/test_be1_synthetic_pilot.py; backend/tests/integration/test_be1_age_provenance_postgres.py. | backend/src/sketch2life/application/ports/identity.py; backend/src/sketch2life/application/services/be1_runtime.py; backend/src/sketch2life/interfaces/http/routers/be1_registry.py; backend/src/sketch2life/interfaces/http/routers/be1_records.py; backend/src/sketch2life/infrastructure/persistence/be1_models.py (chỉ nếu schema đổi và migration được duyệt). | Module/route/bảng/migration Parent identity-profile và test M2-AT-01/02/03/04/10. | Không sửa .env, credential, Firebase secret, shared DB, FEAT-064, M3–M6. |
| S1b | backend/tests/unit/test_member_fact_consent_rules.py (baseline); các file S1a sau khi S1a đóng (hash ghim lại). | backend/src/sketch2life/application/ports/identity.py; backend/src/sketch2life/infrastructure/persistence/core_store.py; backend/src/sketch2life/interfaces/http/routers/be1_registry.py; backend/src/sketch2life/interfaces/http/routers/be1_records.py. Các file dùng chung với S1a chỉ sửa sau khi S1a đóng; không sửa song song. | Module share-grant/data-authorization, route canonical, migration và test M2-AT-05/06/07. | REAL/LEGACY_UNCLASSIFIED bị deny nếu owner/OI gate chưa đóng. BE1 consent không tự động là Parent authorization. |
| S2 | Mặc định chỉ đọc: backend/src/sketch2life/application/ports/ai_jobs.py; backend/src/sketch2life/application/services/ai_jobs.py; backend/src/sketch2life/domain/ai_jobs/model.py; backend/src/sketch2life/infrastructure/ai_jobs/sql/tables.py; backend/src/sketch2life/infrastructure/ai_jobs/sql/repository.py; backend/src/sketch2life/infrastructure/ai_jobs/worker.py; backend/src/sketch2life/infrastructure/ai_jobs/reconciler.py; backend/src/sketch2life/domain/story_run_lite.py; backend/src/sketch2life/application/services/story_run_lite.py; backend/src/sketch2life/infrastructure/story_run_lite/repository.py; backend/src/sketch2life/infrastructure/story_run_lite/tables.py; baseline hồi quy: backend/tests/unit/test_ai_job_lifecycle.py; backend/tests/integration/ai_jobs/test_restart_recovery.py; backend/tests/integration/ai_jobs/test_owner_fence.py; backend/tests/integration/test_story_run_lite_postgres.py; backend/tests/integration/test_story_run_lite_replay_concurrency.py; backend/tests/integration/test_pilot_assistance_routes_t9.py (dùng để đối chiếu: test này monkeypatch `_build_child_binding` ở dòng 257 nên không thay N-1). | Không có mặc định. File hiện có ở cột Chỉ đọc chỉ chuyển sang candidate sửa khi Task Approval nêu từng file và lý do (ví dụ mapping của quyết định 5 hoặc reconciliation B1). | Module Parent aggregate/asset/revision; migration; test N-1 (PostgreSQL thật, wiring thật, không monkeypatch); regression B1 orphan; evidence S2. | Không sửa backend/tests/integration/ai_jobs/test_migrations.py hoặc fixture tạo/xóa DB khi chưa có approval riêng; không sửa backend/alembic/versions/20261103_story_upload_compat.py; không chấp nhận orphan. |
| S3 | backend/src/sketch2life/interfaces/http/story_run_lite_openapi.json; backend/src/sketch2life/contracts/schemas/story_run_lite.py (liên quan P3 chưa xác minh); baseline: backend/tests/contract/test_story_run_lite_api.py; backend/tests/integration/test_pilot_assistance_routes_t9.py; backend/tests/integration/test_be1_postgres_api.py. | backend/src/sketch2life/interfaces/http/routers/assistance_requests.py (OpenAPI P3 hai POST submit/cancel). | Test OpenAPI parity, artifact OpenAPI sinh ra nếu cần, evidence S3, route module/test M2 — chưa xác minh. | Frontend/client chờ OpenAPI P3. Không sửa ngoài approval; không M3–M6, provider, Modal. |

Trước mỗi launch, coordinator phải xác minh lại từng path, chốt path mới, snapshot/hash và xin owner approval. Bảng này không thay allowlist cuối cùng của Task Approval.

## 9. CẦN QUYẾT ĐỊNH CỦA OWNER

| # | Lựa chọn | Hệ quả | Pha bị chặn | Mặc định đề xuất, không phải quyết định |
|---|---|---|---|---|
| 1. DB task-owned | Chọn DB, người tạo/sở hữu, identity và restore expectation; hoặc chưa cấp DB. | Không dùng sketch2life nếu chưa có quyết định riêng; thiếu identity thì không migration/route acceptance PostgreSQL. | S0-owner-run và pha cần persistence. | DB mới rỗng, task-owned, identity pin trong approval, owner chạy. |
| 2. 58 synthetic rows | Giữ; copy/di trú có mapping và approval; hoặc cleanup có approval riêng. | Copy/cleanup có thể mất history/đổi owner; chưa quyết thì giữ nguyên. | S0-owner-run/S2. | Giữ nguyên, không cleanup. |
| 3. B4b/OI-05..08 | Bật consent/share sau khi OI được xác định; hoặc hoãn và giữ synthetic-only/deny REAL, LEGACY_UNCLASSIFIED. | OI-05..08 trong SRS v2.2 lịch sử nói về controller/processor/privacy/DSR/DPIA/breach; retention/backup; provider/storage region/cross-border; production host/region/SLO/RPO/RTO/restore. Mapping v2.3 chưa xác minh. | S1b và dữ liệu thật. | Hoãn REAL; chỉ xây primitive deny-by-default nếu được duyệt. |
| 4. B5 receipt legacy | Còn requirement hay owner disposition không dùng? | Nếu còn: xác định consumer, payload, retention, mapping; nếu không: disposition chính thức. | S1b/S2 nơi receipt dùng. | Không mở B5 khi chưa có consumer xác nhận. |
| 5. Schema convergence | Chọn owner chốt storyrun_upload_sessions → core.upload_sessions, run_id → story_run_id, owner columns, asset refs, history. | Mapping không rõ có thể mất liên kết/history hoặc tạo hai nguồn sự thật. | S0-doc/S2 migration. | Giữ history; chưa migrate khi chưa có mapping ký duyệt. |
| 6. Mypy baseline | Roadmap đã nêu “Ghi mypy baseline exception và không thêm lỗi mới”. Owner xác nhận baseline chính xác theo file/command và không thêm diagnostic; hoặc yêu cầu xử lý trước khi đóng pha. | test_be1_postgres_api.py hiện NO VERDICT; crash tool không phải pass. Quyết định không miễn kiểm tra lỗi mới. | S0-owner-run; S1/S2 nếu sửa target; S3 closeout. | Đo baseline read-only có approval, cùng command/version, không thêm lỗi; không suy diễn phần chưa chạy. |
| 7. B0 provenance | Owner xác nhận normalized bytes tương đương bytes duyệt; hoặc không xác nhận và B0 chưa làm căn cứ có thẩm quyền cho M2. | Hash hiện tại 773C khác hash gốc 03AEA; evidence normalization tại §1.3. Snapshot git-ignore chưa được phiên này xác minh. | S0-doc và mọi requirement dựa B0. | Owner ghi xác nhận qua approval ghim evidence; không sửa pin để làm hash khớp. |

Các câu hỏi bổ sung chưa xác minh: age-band boundary/catalog và physical mapping; field/purpose/expiry của share; canonical route/method cho Parent invite/accept/revoke và Teacher profile; placeholder organization/org_id; cleanup sau DELETE_PENDING; NFR-38/AC-65 disposition. Nếu chưa quyết thì deny hoặc hoãn surface liên quan.

## 10. Gói cần có trước launch

- Owner xác nhận sai lệch HEAD tại §0 và quyết định B0 provenance tại §9.7.
- Owner quyết các mục §9 ảnh hưởng đến pha được launch; lưu trong approval.
- Ghim plan hash, branch/HEAD, nguồn, snapshot manifest.
- Ghi exact file allowlist từng path, path mới, exclusions; không wildcard.
- Ghi DB task-owned identity, người tạo/chạy, dữ liệu, snapshot/restore và cleanup boundary.
- Ghi Alembic graph/target revision, offline plan/SQL review và command ceiling.
- Ghi test matrix/tầng test; route acceptance dùng PostgreSQL thật/wiring thật khi route là đối tượng.
- Ghi disposition B1 orphan, B2 OpenAPI/T12/T13/mypy conditions và mọi PARTIAL/NOT RUN.
- Owner ghi Task Approval cho đúng subphase qua phiên điều phối. Approval một pha không mở pha khác, M3–M6 hoặc provider.

Cho tới khi các điều kiện này được ghi nhận, kế hoạch vẫn **DRAFT / AWAITING OWNER REVIEW**; M2 chưa launch và không có quyền sửa code, migration, DB hoặc gọi provider.
