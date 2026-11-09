# Kế hoạch M2 — Parent / Teacher Foundation (Draft 1)

**Feature:** FEAT-063 — System Architecture Rearchitecture  
**Ngày:** 2026-11-05  
**Trạng thái:** **DRAFT / AWAITING OWNER REVIEW**  
**Phạm vi của tài liệu:** kế hoạch và tiêu chí chấp nhận; chưa phải phê duyệt thực thi.

## 0. Trạng thái và bối cảnh checkout

Commit 1e109b1726f327ac9383457b0dbdd535ef5c6518 đã được đẩy lên origin/feature/feat063-be-foundation. Kiểm tra read-only xác nhận branch feature/feat063-be-foundation, HEAD đúng commit trên, index rỗng và working tree sạch. Không xác minh remote qua mạng.

Tài liệu này chỉ đề xuất cách chia M2, ranh giới dữ liệu, cổng kiểm soát và tiêu chí chấp nhận. Nó không phê duyệt implementation, migration, thao tác cơ sở dữ liệu, sử dụng nhà cung cấp, Modal, tích hợp frontend, hoặc M3–M6. Không cập nhật approvals/TASK_APPROVAL.md; M2 vẫn chưa được phép launch. Chưa có independent review cho kế hoạch này.

## 1. Thứ tự đọc và nguồn căn cứ

Các pin hiện có đã được kiểm tra bằng SHA-256 trên đúng bytes trong working copy. Giữ nguyên các pin này; danh sách dưới đây ghi lại giá trị đã xác minh, không thay thế hay chuẩn hóa pin.

### 1.1. FEAT-063 — nguồn chính

| Tài liệu | SHA-256 đã pin và xác minh |
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

### 1.2. FEAT-064 — evidence về các điều kiện kế thừa

| Tài liệu | SHA-256 đã pin và xác minh |
|---|---|
| features/FEAT-064-current-flow-modal-vision-dev/evidence/A2_REV3_INDEPENDENT_REVIEW_CLOSEOUT_20261103.md | 10B12F4417A5E29DF0ED1697F33A8FAA08D692E71015998CCC8DE297328A1C36 |
| features/FEAT-064-current-flow-modal-vision-dev/plan/FEAT064_A2_B1_B2_SEQUENTIAL_GOAL_20261103.md | D7DEE2977C5AA28B26FCB117281DE8B23E4D4AA85A42922B8B37752FBDA8752A |
| features/FEAT-064-current-flow-modal-vision-dev/approvals/TASK_APPROVAL.md | 9D07B88190E8F5831D79431A79C2AAC944B266CB28CD29265E5D0283B77921B8 |

### 1.3. Căn cứ và giới hạn thẩm quyền

- D-132 chấp nhận roadmap của FEAT-063 làm baseline lập kế hoạch; không phê duyệt M2–M6 implementation.
- SRS v2.3 là draft chưa ký; route matrix là hợp đồng đề xuất, chưa phải OpenAPI cuối cùng.
- DTR mô tả mô hình logic và chủ sở hữu dự kiến; các con số trong đó không thay thế việc kiểm tra schema vật lý.
- B0 plan có vấn đề provenance: report B0 ghi hash của plan được duyệt là 03AEA386B8545624100688B68AA828A84CD154B47857CB5E98FB06354D6BB582, trong khi bytes của plan đang được pin ở trên cho hash 773C4A8340C8E33AE39764D920B042AC19BACBAF6DC561FE9D5D3DFFCC4B5A5A. Không coi B0 plan là thẩm quyền cho tới khi owner xác nhận đúng bytes hoặc phê duyệt addendum. Không sửa pin để làm hai giá trị khớp nhau.
- M1 là demo Vision tổng hợp chạy local; điều đó không chứng minh đã tích hợp Modal, provider thật hoặc production.
- M1, A2 và B2 đã hoàn tất trong phạm vi riêng được duyệt; acceptance của chúng không mở quyền triển khai M2.

## 2. Mục tiêu, phạm vi và phần loại trừ

### 2.1. Mục tiêu M2 đề xuất

Thiết lập nền tảng Parent/Teacher gồm:

1. danh tính người lớn, vai trò và tenant/org scope;
2. hồ sơ và quyền truy cập hồ sơ theo chủ sở hữu;
3. consent/data authorization và parent-to-teacher grant có phạm vi, thu hồi và audit, chỉ bật dữ liệu thật sau các cổng pháp lý/chính sách;
4. quy tắc tuổi và provenance có phiên bản;
5. ranh giới owner/scope giữa aggregate, AI job, asset, revision và persistence;
6. lifecycle bền vững, idempotency, hủy, phục hồi và xử lý trạng thái xóa.

Mục tiêu kiến trúc là hợp đồng rõ ràng giữa các owner, không tạo FK hoặc SQL join xuyên schema. Cross-owner reference phải là opaque, có kiểu và được xác minh qua application port.

### 2.2. Không thuộc M2

- M3: intake media, transcript, input/revision và Parent line-sketch tùy chọn theo Q146/B13.
- M4: nội dung story, script và rewrite.
- M5: video, quota/usage/compute, Modal hoặc provider. Mọi provider cần phê duyệt riêng; hiện không có quyền gọi Modal/GPU/provider/network.
- M6: teacher lesson đầy đủ, occurrence/sample, roster, chia sẻ/moderation/history/commerce/billing.
- Định nghĩa cuối cho activity/lesson D-114, vị trí vật lý hoặc openings còn chưa chốt.
- Không tuyên bố M2 chứng minh chất lượng giáo dục của story/model; NFR-38 cần kiểm tra vertical ở scope thích hợp sau này.

## 3. Các giai đoạn M2 đề xuất

Các giai đoạn dưới đây là trình tự để owner duyệt. Mỗi giai đoạn cần scope, allowlist file, snapshot và approval riêng trước khi thực thi; hoàn tất một giai đoạn không tự cấp quyền cho giai đoạn kế tiếp.

| Giai đoạn | Nội dung | Điều kiện đóng giai đoạn |
|---|---|---|
| **S0 — Scope, data và migration reconciliation** | Chốt owner decisions ở §9; xác định DB task-owned, người sở hữu và dữ liệu synthetic được phép dùng; đối chiếu schema vật lý với toàn bộ Alembic graph trên DB task-owned; lập mapping từ demo sang DTR; ghi baseline lỗi mypy. | Tất cả unknown có ảnh hưởng migration/access được quyết định hoặc giữ ở chế độ deny-by-default; manifest/allowlist và điểm rollback được duyệt; không đụng shared DB. |
| **S1 — Identity, tenant, profile và grant** | Identity/role/org assignment; Parent profile ownership; Teacher/BE1 class assignment; tenant isolation; consent/data authorization; field-scoped share grant; tuổi/provenance. Bật dữ liệu thật chỉ khi B4b/OI gate đã được owner chấp thuận. | Positive và negative authorization cases chạy trên task-owned DB; revoke có hiệu lực trên API và các đường truy cập liên quan; audit chỉ ghi metadata cần thiết; review chấp nhận. |
| **S2 — Owner, job, asset, revision và lifecycle** | Opaque owner/scope refs; quan hệ aggregate ↔ job ↔ asset ↔ revision; persistence, receipts, idempotency, cancellation, restart/recovery và delete-pending. Giữ AiJobService trong bản đồ tích hợp; không giả định M1 đã dùng service này. | Contract và trạng thái nhất quán khi retry, timeout, hủy và restart; không có kết quả stale/orphan được coi là accepted; integration test dùng wiring thật trên DB task-owned; review chấp nhận. |
| **S3 — Đóng M2 và bàn giao** | Đối chiếu acceptance với source IDs; chốt evidence, giới hạn dữ liệu, unresolved items và migration outcome; xác nhận không phát sinh scope M3–M6. | Tất cả AC/AT đạt hoặc có disposition owner ký; independent review ACCEPTED; cập nhật trạng thái qua quy trình được duyệt. Không tự động mở M3. |

**Cổng dừng:** nếu một hash nguồn không khớp, DB identity khác manifest, phát hiện dữ liệu không tổng hợp, có đường đọc ngoài scope, migration graph/schema vật lý khác hồ sơ, hoặc cần tác động file/DB/provider ngoài allowlist thì dừng bước đó và xin quyết định mới. Không tự sửa pin hoặc tiếp tục bằng giả định.

## 4. Traceability yêu cầu → hợp đồng → kiểm chứng

Các API trong bảng là route candidate từ SRS/crosswalk, chưa đóng băng. AT là kiểm chứng đề xuất cho plan, chưa phải đã chạy.

| Nguồn | Hành vi M2 cần chứng minh | Owner/table logic liên quan | Kiểm chứng M2 đề xuất |
|---|---|---|---|
| FR-PL-01; AC-46/64 | Server xác thực role và scope trước khi đọc/ghi profile; grant/revoke có audit. | parent.child_profiles, parent.profile_share_grants; be1.adult_identities, be1.organization_assignments | AT-01: role thiếu/sai scope bị deny; đúng owner được phép; revoke chặn lần đọc tiếp theo. |
| FR-PL-02; AC-46/57/63; BR-49/58 | Org/class isolation; không tiết lộ sự tồn tại hoặc metadata của tenant khác. | be1.organizations, be1.classrooms, be1.enrollments; parent.child_profiles | AT-02: hai tenant fixtures; mọi truy vấn chéo trả kết quả deny/không lộ metadata theo hợp đồng đã duyệt. |
| FR-PL-07; AC-49/57; BR-48 | Parent share grant có lifecycle invite/active/revoked/expired và purpose rõ. | parent.profile_share_grants; parent.data_authorizations | AT-03: chỉ grant đang hiệu lực mới cấp đúng quyền; revoke/expire ngăn truy cập. Route share chính xác: **chưa xác minh**. |
| FR-PL-08; AC-49/57/64; NFR-34 | Field scope được áp dụng thống nhất tại API, download/token/cache và job dispatch; thu hồi chặn mọi đường đã định nghĩa. | parent.profile_share_grants; core.asset_lineage; ai_jobs.job và command/receipt | AT-04: grant field hẹp không lộ field khác; revoke chặn API, token/download và job chưa được nhận theo contract. Cần owner chốt các surface thuộc M2. |
| FR-PL-25; AC-62/65; BR-57 | Tuổi 36–120 tháng, nguồn và revision của tuổi có provenance; phiên bản age band được tham chiếu. | parent.profile_revisions.age_months, age_band_ref/version; be1.profile_revisions.age_months, age_band | AT-05: kiểm tra biên 36/120 và ngoài biên; provenance/revision được lưu hoặc từ chối theo contract. Bảng catalog age-band và mapping provenance vật lý: **chưa xác minh**. |
| BR-48 | Quyền chia sẻ chỉ qua grant có purpose, trạng thái và scope. | parent.profile_share_grants, parent.data_authorizations | AT-03/04 và kiểm tra deny khi thiếu grant. Không coi be1.consent_records là thay thế tự động cho Parent authorization. |
| BR-49 | Membership/scope server-side; mặc định deny. | be1.organization_assignments, be1.enrollments, be1.classrooms | AT-02 và role matrix đã được owner duyệt. |
| BR-57 | Age band nằm trong dải được duyệt, có version. | Profile revision tables | AT-05; boundary policy và bảng tham chiếu cần owner chốt. |
| BR-58 | Role/org/class assignment hợp lệ trước khi cấp quyền. | be1.adult_identities, be1.organization_assignments, be1.classrooms, be1.enrollments | AT-02 với assignment revoked, sai org và role không đủ quyền. |
| NFR-34 | Deny-by-default; revoke xuyên API/download/token/cache/job dispatch; audit metadata-only. | Parent, Core và AI Jobs qua port/contracts | AT-04; audit không ghi child content/media/secret/token. |
| NFR-36 | Admin truy cập media/profile hoặc grant cross-role cần scope, reason và audit; school feedback không vượt org. | BE1/Parent/Core ownership boundary | AT-06: admin access thiếu reason/scope bị deny; feedback cross-org bị deny. M2 chỉ làm foundation, không mở màn hình/admin workflow mới. |
| NFR-38 | Contract hỗ trợ tiếng Việt, độ tuổi 3–10, Montessori-inspired, child-centered/adult-guided. | Locale/age metadata trong profile và các contract liên quan | AT-07: xác nhận locale/age metadata không bị mất; chất lượng nội dung là kiểm tra vertical sau, không phải bằng chứng của M2. |

### 4.1. Route candidate và điểm chưa đóng

SRS §21.2 đề xuất POST /v1/parent/profiles, GET/PATCH /v1/parent/profiles/{profile_id}, tạo org/class/assignment, các upload-session, story-run, cancel/delete và GET /v1/jobs/{job_id}. Đây là candidate để crosswalk, không phải OpenAPI cuối. SRS §9.6 và §21.2 dùng placeholder khác nhau cho organization/org_id; phải thống nhất khi freeze OpenAPI.

- GET /v1/me là suy luận độ tin cậy thấp trong B1 crosswalk.
- GET /v1/parent/profiles, DELETE parent profile và method cho teacher profile là suy luận/chưa xác định.
- Parent share invite/accept/revoke chưa có route canonical trong SRS; **chưa xác minh**.
- BE1 consent route hiện hữu không tự động trở thành route consent Parent. be1.consent_records và parent.data_authorizations là hai owner/model khác nhau.
- Lesson access-grant hiện hữu do Lesson Library sở hữu; M2 chỉ chốt nền tảng tenant/grant và contract cần thiết. Không mở rộng thành Lesson feature.

## 5. Ranh giới dữ liệu, migration và vận hành DB

### 5.1. Logical ownership đề xuất theo DTR

| Owner | Nhóm bảng logic thuộc trách nhiệm |
|---|---|
| BE1 | be1.organizations, be1.adult_identities, be1.organization_assignments, be1.classrooms, be1.managed_profiles, be1.enrollments, be1.consent_records, be1.data_lifecycle_requests, be1.profile_revisions, be1.profile_context_entries, be1.profile_support_needs |
| Parent | parent.child_profiles, parent.profile_revisions, parent.profile_context_entries, parent.profile_support_needs, parent.data_authorizations, parent.profile_share_grants |
| Core | core.asset_lineage, core.upload_sessions, core.upload_parts, core.upload_command_receipts, cùng các bảng metadata/audit/revision Core hiện hành |
| AI Jobs | ai_jobs.job, attempt, command_receipt, semantic_request, completion_receipt, cancellation_notice, outbox, job_events |
| Story | story.runs, run_inputs, review_decisions, command_receipts và các bảng story do DTR chỉ định |

Danh sách là ownership logic theo DTR, không xác nhận schema vật lý hiện tại. Không tạo FK/SQL join xuyên schema. Mỗi aggregate có typed owner-scope và target-kind/ref; event append-only; trạng thái/progress job không thay thế trạng thái aggregate.

### 5.2. Mapping và dữ liệu tồn dư

- M1 demo storyrun_upload_sessions cần được map rõ với core.upload_sessions.
- Demo story.runs.run_id cần được map với DTR story.runs.story_run_id; mapping owner columns, asset refs và history cũng phải được ghi rõ.
- B3 ownership/migration manifest hiện là đề xuất; co-sign còn thiếu, không phải lệnh thi hành.
- FEAT-064 A2 ghi nhận 58 synthetic rows còn lại sau teardown lỗi. Chỉ owner được chọn: giữ nguyên; chuyển/copy với mapping chính xác và approval; hoặc cleanup với approval riêng. Mặc định **không cleanup** và không reset shared sketch2life.
- Trước bất kỳ migration nào trong tương lai: schema vật lý phải được đối chiếu với Alembic trên DB task-owned, có snapshot/restore plan và manifest owner ký.

### 5.3. Alembic và giới hạn thao tác tương lai

Hồ sơ static cho thấy nhiều root/head độc lập và depends_on; các nhánh Core/BE1, AI Jobs, AI Policy, Lesson Library và nhánh khác không được gom tùy tiện vào một target heads. B2 từng ghi nhận 9 DB heads/version rows tại thời điểm owner-run; không suy ra DB hiện tại vẫn như vậy.

20261102_pilot_vision có down_revision=None và phụ thuộc revision BE1/AI; 20261102_story_run_lite có down_revision=None và phụ thuộc pilot; 20261103_story_upload_compat đi sau story-run-lite nhưng downgrade() chủ động raise RuntimeError. Vì vậy:

1. S0 phải chốt graph đích, depends_on, merge rationale và target revision cụ thể; không chọn heads chung làm đích.
2. Trước DB mutation ở task tương lai cần offline graph/SQL preflight và xác nhận schema vật lý.
3. Nhánh irreversible không được tuyên bố reversible; nếu đi qua nhánh đó thì không chạy downgrade. Dùng additive/compatibility rollback đã được duyệt.
4. Đề xuất giới hạn ban đầu cho DB task-owned: tối đa một upgrade tới target revision chính xác. Chỉ cho phép tối đa một downgrade nếu chứng minh static là reversible và được duyệt rõ, rồi tối đa một re-upgrade. Với nhánh irreversible: một upgrade trên DB disposable rồi dừng. Không retry hoặc thêm lệnh khi chưa có approval mới.
5. Không drop DB; mặc định giữ DB và snapshot. Drop/cleanup cần explicit approval riêng.
6. Phần DB của backend/tests/integration/ai_jobs/test_migrations.py chưa chạy và có tạo/xóa DB qua maintenance connection. Không dùng trong M2 nếu chưa viết lại trong scope được duyệt hoặc có approval riêng.

Mọi thao tác DB trong M2 tương lai do owner chạy trên DB task-owned; không dùng coordinator connection để kiểm tra/đọc DB. Fixture chỉ được xóa đúng rows do chính test run tạo. Nếu xác định khác DB hoặc có dữ liệu không tổng hợp thì dừng.

## 6. Lifecycle, authorization và các điều kiện kế thừa

### 6.1. Hợp đồng lifecycle tối thiểu

- Phân biệt trạng thái aggregate, job, asset và command receipt; retry không tạo tác dụng phụ trùng.
- Có owner-lock/concurrency rule, cancellation và kiểm tra stale/replay.
- D-127: sau PREPARATION_REVIEW, cancel chuyển sang DELETE_PENDING, giải phóng active owner nhưng giữ result/assets/receipts. DELETE_PENDING không có nghĩa là dữ liệu đã bị xóa.
- Xác định restart/recovery và cách xử lý job/worker mất liên lạc; không nhận kết quả mồ côi/stale là accepted.
- Trước worker/process mới hoặc dữ liệu không tổng hợp, cần xử lý finding B1: có thể có invocation SUCCEEDED trong khi job RUNNING, thiếu receipt/ref authoritative; chưa có bằng chứng read/exposure/accepted result. Chốt invalidation/reconciliation, độc giả dữ liệu và regression trước khi mở cổng.

### 6.2. Privacy, security và quan sát

Áp dụng B12 xuyên các giai đoạn: authorization, privacy, safety, idempotency, stale/replay, observability, restart/recovery và failure mapping. Audit chỉ lưu metadata tối thiểu; không ghi child content, media, token hay secret. Revoke phải được kiểm tra qua mọi surface được chốt trong contract. Admin access cần scope/reason/audit. Tenant isolation là deny-by-default.

### 6.3. Điều kiện kế thừa B2/A2

- A2 closeout được ACCEPTED/COMPLETE trong scope riêng; còn 58 synthetic rows và Alembic/physical-schema mismatch chưa được giải quyết.
- Strict mypy từng có một lỗi protocol trong infrastructure/assistance/harness.py:380, giống baseline lưu trước đó. B2 không có verdict cho mypy tests/integration/test_be1_postgres_api.py và thiếu baseline trước B2. Không gọi mypy là xanh; owner phải chọn disposition ở §9.
- B2: hai POST submit/cancel operation trong backend/src/sketch2life/interfaces/http/routers/assistance_requests.py cần OpenAPI đầy đủ trước frontend/client integration.
- B2 T13 chỉ kiểm tra timeout của script-local helper với stub; chưa chứng minh lifecycle job/worker thật.
- B2 T12 round-trip chỉ pilot_vision, intermediate và bảng pilot rỗng; chưa chứng minh full graph hoặc story_run_lite.
- N-1 route-level PostgreSQL test cho child request → job → status cần chạy trước D9/frontend, dùng wiring thật, không monkeypatch route wiring/dependencies.
- N-3 runner chưa pin và recon runner còn thiếu; chưa coi là fully verified.
- Không có quyền provider: OWNER_MODAL_CALL_APPROVED=NO. Không gọi Modal, GPU, provider hoặc external service trong plan này.

## 7. Acceptance criteria dự thảo

M2 chỉ có thể đóng khi tất cả điều kiện sau đạt hoặc có disposition owner được ghi rõ:

1. Mỗi requirement FR/BR/NFR trong §4 truy tới contract, owner, AC/AT và evidence cụ thể.
2. Identity, role, tenant, ownership, grant và revoke được kiểm chứng với positive/negative cases; cross-tenant không lộ metadata.
3. Tuổi/provenance dùng contract có version; boundary và catalog mapping được owner quyết định; dữ liệu ngoài dải bị xử lý đúng contract.
4. Owner/scope/ref giữa aggregate, AI Jobs, Core và Story được kiểm tra; không có cross-schema FK/join.
5. Idempotency, replay/stale, cancellation, restart/recovery, job/aggregate consistency và D-127 được kiểm tra bằng integration path phù hợp.
6. OpenAPI candidate được freeze trước client integration; các route suy luận không âm thầm trở thành contract.
7. Migration chạy đúng target graph trên DB task-owned, nếu migration đã được duyệt; shared DB và dữ liệu thật không bị chạm tới.
8. Evidence nằm trong features/FEAT-063-system-architecture-rearchitecture/evidence/ theo phase; independent review kết luận ACCEPTED.
9. Không mở phạm vi M3–M6 và không bật provider/Modal.

## 8. Allowlist và giới hạn thay đổi cho lần triển khai tương lai

Kế hoạch này không cấp quyền sửa code. Trước mỗi subphase, owner phải ghi allowlist file paths tương đối và exact target revision/migration IDs trong approval tương ứng. Chỉ các file được nêu chính xác mới được sửa; không dùng wildcard directory như quyền mặc định.

Nhóm path có thể cần xem xét sau khi scope được duyệt (chưa phải allowlist): backend/src/sketch2life/domain/, backend/src/sketch2life/application/, các adapter/interface có liên quan, migration files đúng owner và các test tương ứng. Không tạo/sửa gì trong các nhóm này trong bước lập kế hoạch hiện tại. Mọi path, migration mới, file generated, OpenAPI snapshot và evidence phải xuất hiện trong scope được ký trước khi bắt đầu subphase.

## 9. CẦN QUYẾT ĐỊNH CỦA OWNER

Không tự chọn thay owner. Mỗi câu trả lời cần được ghi vào hồ sơ FEAT-063 qua quy trình approval trước khi launch.

1. **DB task-owned:** DB nào sẽ dùng, ai sở hữu/tạo nó, cách xác nhận đúng DB và snapshot/restore expectation là gì? Shared sketch2life không phải lựa chọn mặc định.
2. **58 synthetic rows:** giữ; chuyển/copy theo mapping chính xác với approval; hay cleanup bằng explicit approval riêng? Mặc định giữ, không cleanup.
3. **B4b và OI-05..08:** có bật luồng consent/authorization cho dữ liệu thật trong M2 hay giữ synthetic-only? Nếu giữ thì mặc định từ chối REAL và LEGACY_UNCLASSIFIED. OI-05..08 trong tài liệu SRS v2.2 lịch sử nói về: controller/processor và DPA/consent/privacy/DSR/DPIA/breach; retention và backup deletion; provider/storage region/cross-border transfer; production host/network/region, SLO, RPO/RTO, alert và restore. Mapping của các định nghĩa lịch sử này sang SRS v2.3 hiện hành **chưa xác minh**; owner cần xác nhận hoặc thay bằng định nghĩa mới.
4. **B5 legacy receipt:** receipt legacy còn cần thiết không? Nếu có, nêu consumer, dữ liệu/retention và migration mapping; nếu không, owner cần disposition chính thức.
5. **Demo ↔ canonical ownership:** ai chốt mapping storyrun_upload_sessions → core.upload_sessions, run_id → story_run_id, owner columns và asset refs; history cũ được giữ/di trú thế nào?
6. **Mypy baseline:** có chấp nhận ghi nhận đúng một diagnostic baseline hiện hữu với điều kiện không phát sinh lỗi mới, hay yêu cầu sửa trước khi đóng M2? Cần xác lập baseline cho test target hiện chưa có verdict.
7. **B0 provenance:** owner xác nhận bytes/hash nào của B0 là bản được duyệt, hay phê duyệt addendum? Có chấp nhận dùng roadmap owner-approved cùng các pin SRS/DTR/status/approval và FEAT-064 evidence làm căn cứ lập kế hoạch thay thế không? Không sửa pin hiện hữu để hợp thức hóa khác biệt.

Các câu hỏi chưa được gộp vào lựa chọn thay owner: age-band boundary/catalog và provenance mapping; fields, purpose, expiry của share grant; chính xác route/method cho Parent share và Teacher profile; OpenAPI placeholder organization/org_id; định nghĩa DELETE_PENDING/cleanup sau này. Nếu không được owner chốt thì giữ ở trạng thái **chưa xác minh** và đóng access tương ứng bằng deny-by-default.

## 10. Gói cần có trước khi xin launch M2

Trước implementation, owner cần duyệt và ghi nhận tối thiểu:

- quyết định §9 và nguồn căn cứ B0;
- plan version/hash được duyệt, scope của một subphase và acceptance criteria;
- task-owned DB identity, người chạy lệnh, snapshot/restore, dữ liệu được phép và cleanup boundary;
- exact file allowlist, migration IDs/target revision, offline graph/SQL review và command ceiling;
- manifest ownership/schema và mapping demo-to-canonical;
- disposition cho B1 orphan, B2 conditions, mypy baseline, OpenAPI gaps và runner gap;
- explicit Task Approval trong features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md cho đúng subphase; phê duyệt một subphase không phê duyệt phase khác.

Cho tới lúc các điều kiện đó được ghi nhận, trạng thái vẫn là **DRAFT / AWAITING OWNER REVIEW**, M2 chưa launch và không có quyền triển khai hay thao tác DB.
