# Kế hoạch M2 — Parent / Teacher Foundation (Draft 2)

**Feature:** FEAT-063 — System Architecture Rearchitecture  
**Ngày:** 2026-11-05  
**Trạng thái:** **DRAFT / AWAITING OWNER REVIEW**  
**Phạm vi:** sửa kế hoạch theo F1–F9; không phải phê duyệt triển khai, không phải blanket approval cho M3–M6; M2 chưa launch.

## Thay đổi so với Draft 1

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

Checkout khi lập Draft 2: branch feature/feat063-be-foundation, HEAD 1e109b1726f327ac9383457b0dbdd535ef5c6518, parent b6dbfa68e66718f3f40902c093e9ebd634b1ebb9. Index rỗng. Trước khi tạo Draft 2, thay đổi local duy nhất được ghi nhận là Draft 1 untracked.

Prompt ban đầu lập Draft 1 ghim HEAD b6dbfa68e66718f3f40902c093e9ebd634b1ebb9, nhưng checkout là commit 1e109b1726f327ac9383457b0dbdd535ef5c6518, con trực tiếp sau commit hợp nhất B1/B2. Lượt độc lập đầu tiên đã dừng đúng cổng. Sau đó phiên điều phối cập nhật pin HEAD trong lời nhắn tiếp tục và cho cùng phiên làm tiếp mà chưa có xác nhận riêng của owner. Đây là sai lệch quy trình cần owner xác nhận qua approval; Draft 2 không hợp thức hóa nó. Mười hai hash tài liệu được kiểm tra lại và đều khớp pin. Việc kiểm tra đó không thay cho owner xác nhận.

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
| S1a identity/tenant/profile/age | S0-doc đóng; S0-owner-run nếu approval phase yêu cầu DB | Identity/role assignment, tenant isolation, profile ownership và age provenance. | M2-AT-01/02/03/04/10 đạt theo tầng đã duyệt; route test persistence dùng PostgreSQL thật và wiring thật. | Thiếu role matrix, profile owner hoặc age policy thì deny-by-default; không tự tạo route/policy. |
| S1b grant/revoke/consent | S1a; owner quyết định 3; OI gate đã xác định | Scoped grant/revoke, purpose/expiry/audit và consent/data authorization trong phạm vi được chọn. | M2-AT-05/06 đạt; thiếu, pending, revoked hoặc expired đều deny. Nếu B4b hoãn thì REAL và LEGACY_UNCLASSIFIED bị từ chối; không claim consent production-ready. | OI mapping, purpose, fields, expiry hoặc policy chưa chốt thì không bật share/consent. |
| S2 owner/job/asset/revision/lifecycle | S1a; S1b nếu bật; migration target đã duyệt | Durable owner/scope refs, job/asset/revision, AiJobService mapping, idempotency/replay, cancel, restart/recovery, DELETE_PENDING/D-127. | M2-AT-07/08/09 đạt. N-1 route PostgreSQL test child request → job → status phải dùng wiring thật. B1 orphan có invalidation/reconciliation/read-exposure contract và regression trước dữ liệu non-synthetic/provider. | Orphan có thể được đọc/công bố như accepted result, job/aggregate lệch, hoặc thiếu N-1 thì chưa thoát S2. |
| S3 freeze và đóng M2 | S1a, S1b theo disposition, S2 | Đối chiếu evidence và freeze contract; đóng OpenAPI P3 hai POST submit/cancel trước frontend/client. | Tất cả tiêu chí pass hoặc PARTIAL disposition được owner ghi; OpenAPI parity được kiểm; conditions được gán owner/phase; independent review ACCEPTED. | Không tích hợp frontend/client khi OpenAPI P3 còn mở; không tự mở M3. |

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
| BR-58 | POST /v1/classes/{class_id}/assignments và POST /v1/classes/{class_id}/profiles tạo assignment/enrollment — SRS §21.2; không phải lesson-audience grant. Route lesson grant cho nhóm Parent hoặc invitee — chưa xác minh, thuộc M6. | be1.parent_groups/parent_group_members; lesson.access_grants — BE1/Lesson. | M2-AT-04 cho teacher assignment/profile primitive; M6 cho audience lesson đầy đủ. |
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
| M2-AT-04 | FR-PL-02, BR-49/58; S1a | Given Teacher active hoặc không có assignment; when POST assignment/profile theo route SRS; then chỉ actor đủ quyền tạo đúng assignment/enrollment, revoked/sai tenant bị deny. | Route PostgreSQL acceptance không mock wiring. | Có. |
| M2-AT-05 | FR-PL-07, BR-48; S1b | Given grant pending/active/revoked/expired với purpose/scope; when đọc profile; then chỉ grant active đúng scope cho phép. Nếu canonical route chưa chốt, chỉ test domain/service và S1b chưa đóng. | Unit trước; route PostgreSQL sau khi route được duyệt. | Có cho route/persistence. |
| M2-AT-06 | FR-PL-08, BR-48, NFR-34; S1b | Given field-scoped grant liên kết asset/token/cache/job; when revoke; then lần đọc/tải mới, token/cache access và job chưa accepted bị chặn, audit không ghi content/token. | API/asset/job integration; không gọi provider. | Có. |
| M2-AT-07 | NFR-36; S1b/S3 | Given Admin thiếu scope/reason hoặc access hợp lệ; when thao tác admin thuộc M2; then thiếu điều kiện bị deny, access hợp lệ audit metadata. Feedback cross-org bị từ chối ở owner/mốc feedback. | Unit + route integration cho primitive M2; feedback ở mốc sau. | Có cho route M2. |
| M2-AT-08 | FR-PL-01, NFR-34; S2 | Given idempotency key, owner-lock cạnh tranh, stale/replay và restart; when retry/cancel/recover; then không tác dụng phụ trùng, stale result không accepted, aggregate/job/receipt khớp contract. | PostgreSQL integration/restart với repository thật. | Có. |
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

1. Mỗi requirement §4 có route status, bảng logic, owner, M2-AT và evidence. Cho phép NFR-38 PARTIAL chỉ khi owner ghi disposition và AC-65 được chuyển có chủ đích sang M4/M5; PARTIAL không phải PASS.
2. Identity, role, tenant, profile ownership, assignment và age provenance đạt M2-AT-01/02/03/04/10 với positive/negative tests; DB thật cho route/persistence.
3. Grant/consent theo quyết định 3/OI gate; thiếu grant/policy thì deny, REAL và LEGACY_UNCLASSIFIED bị chặn nếu B4b hoãn.
4. Lifecycle đạt M2-AT-08/09; N-1 PostgreSQL route test với wiring thật bắt buộc; B1 orphan có reconciliation/read-exposure contract và regression trước khi thoát S2.
5. Target migration/schema inventory/data disposition/rollback limits được owner phê duyệt; DB/source/snapshot gate lệch thì dừng.
6. OpenAPI request/response/error parity được freeze trước client integration; P3 đóng trong S3.
7. Evidence lưu tại feature evidence path được approval chỉ định; PARTIAL/NOT RUN/owner-run provenance ghi đúng. Plan review và implementation review là hai việc riêng.
8. Không mở M3–M6 và không bật provider/Modal.

## 8. Candidate allowlist theo subphase

Các path dưới đây là candidate đã xác nhận tồn tại để owner/reviewer xem xét trước Task Approval. Chúng không cấp quyền sửa. Không dùng wildcard. File mới chưa tồn tại được ghi chưa xác minh và phải có tên/hash trong approval trước khi tạo.

| Pha | Candidate paths hiện có | Path mới chưa xác minh | Exclusions / hard stop |
|---|---|---|---|
| S0-doc | features/FEAT-063-system-architecture-rearchitecture/plan/M2_PARENT_TEACHER_FOUNDATION_PLAN_DRAFT1_20261105.md; features/FEAT-063-system-architecture-rearchitecture/CONTEXT.md; features/FEAT-063-system-architecture-rearchitecture/SOURCE_REGISTER.md; features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md; features/FEAT-063-system-architecture-rearchitecture/status/STATUS.md; features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md | Evidence addendum filename chưa xác minh. | Không sửa Draft 1, SRS, DTR, roadmap, source/test/migration. Mọi thay đổi cần approval riêng. |
| S0-owner-run | Read-only inputs: backend/alembic/env.py; backend/alembic/versions/20261014_0002_be1_runtime.py; backend/alembic/versions/20261015_ai_0001_ai_jobs_schema.py; backend/alembic/versions/20261028_ll_0001_lesson_library.py; backend/alembic/versions/20261031_be1_synthetic_eligibility.py; backend/alembic/versions/20261101_be1_age_provenance.py; backend/alembic/versions/20261102_pilot_vision.py; backend/alembic/versions/20261102_story_run_lite.py; backend/alembic/versions/20261103_story_upload_compat.py | Evidence output path chưa xác minh; repo write allowlist rỗng cho đối soát read-only. | Chưa có DB identity/command/hash/snapshot/approval thì không chạy. Không migration, shared DB hoặc source writes. |
| S1a | backend/src/sketch2life/domain/child_age.py; backend/src/sketch2life/application/ports/identity.py; backend/src/sketch2life/infrastructure/identity/firebase_token_verifier.py; backend/src/sketch2life/contracts/schemas/child_learning_profile.py; backend/src/sketch2life/application/services/be1_runtime.py; backend/src/sketch2life/interfaces/http/routers/be1_registry.py; backend/src/sketch2life/interfaces/http/routers/be1_records.py; backend/src/sketch2life/infrastructure/persistence/be1_models.py; backend/tests/unit/test_profile_age_invariant.py; backend/tests/unit/test_age_provenance_columns.py; backend/tests/unit/test_child_learning_profile_contract.py; backend/tests/contract/test_be1_synthetic_pilot.py; backend/tests/integration/test_be1_age_provenance_postgres.py | Parent-specific identity/profile modules, routes, tables, migration filename và tests chưa xác minh. | Không sửa .env/credentials/Firebase secrets, shared DB, FEAT-064 hoặc M3–M6. |
| S1b | backend/src/sketch2life/application/ports/identity.py; backend/src/sketch2life/infrastructure/persistence/core_store.py; backend/src/sketch2life/interfaces/http/routers/be1_registry.py; backend/src/sketch2life/interfaces/http/routers/be1_records.py; backend/tests/unit/test_member_fact_consent_rules.py | Parent share-grant/data-authorization modules, canonical routes, migration và route tests chưa xác minh. | REAL/LEGACY_UNCLASSIFIED bị deny nếu owner/OI gate chưa đóng. Không coi BE1 consent tự động là Parent authorization. |
| S2 | backend/src/sketch2life/application/ports/ai_jobs.py; backend/src/sketch2life/application/services/ai_jobs.py; backend/src/sketch2life/domain/ai_jobs/model.py; backend/src/sketch2life/infrastructure/ai_jobs/sql/tables.py; backend/src/sketch2life/infrastructure/ai_jobs/sql/repository.py; backend/src/sketch2life/infrastructure/ai_jobs/worker.py; backend/src/sketch2life/infrastructure/ai_jobs/reconciler.py; backend/src/sketch2life/domain/story_run_lite.py; backend/src/sketch2life/application/services/story_run_lite.py; backend/src/sketch2life/infrastructure/story_run_lite/repository.py; backend/src/sketch2life/infrastructure/story_run_lite/tables.py; backend/tests/unit/test_ai_job_lifecycle.py; backend/tests/integration/ai_jobs/test_restart_recovery.py; backend/tests/integration/ai_jobs/test_owner_fence.py; backend/tests/integration/test_story_run_lite_postgres.py; backend/tests/integration/test_story_run_lite_replay_concurrency.py | Parent aggregate/asset/revision modules, new migration, tests và evidence chưa xác minh. | Không sửa backend/tests/integration/ai_jobs/test_migrations.py hoặc dùng fixture tạo/drop DB nếu chưa có approval riêng; không sửa migration irreversible 20261103_story_upload_compat.py; không chấp nhận orphan. |
| S3 | features/FEAT-063-system-architecture-rearchitecture/CONTEXT.md; features/FEAT-063-system-architecture-rearchitecture/SOURCE_REGISTER.md; features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md; features/FEAT-063-system-architecture-rearchitecture/status/STATUS.md; features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md; backend/src/sketch2life/interfaces/http/routers/assistance_requests.py; backend/src/sketch2life/interfaces/http/story_run_lite_openapi.json; backend/src/sketch2life/contracts/schemas/story_run_lite.py; backend/tests/contract/test_story_run_lite_api.py; backend/tests/integration/test_pilot_assistance_routes_t9.py; backend/tests/integration/test_be1_postgres_api.py | S3 evidence filename, M2 route modules/tests và generated OpenAPI artifact mới nếu cần: chưa xác minh. | Frontend/client chờ OpenAPI P3; không sửa ngoài approval; không M3–M6/provider/Modal. |

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
