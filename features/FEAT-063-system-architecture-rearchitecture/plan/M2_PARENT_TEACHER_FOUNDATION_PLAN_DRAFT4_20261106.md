# Kế hoạch M2 — Parent / Teacher Foundation (Draft 4)

**Feature:** FEAT-063 — System Architecture Rearchitecture  
**Ngày:** 2026-11-06  
**Trạng thái:** **DRAFT / AWAITING OWNER REVIEW**  
**Phạm vi:** bản sửa tài liệu theo Draft 3 và review độc lập NEEDS_REVISION; không phải approval triển khai, không cấp quyền M2, M3–M6, DB, migration, provider, Modal hay bật workload. Trạng thái vẫn DRAFT / AWAITING OWNER REVIEW.

## Thay đổi so với Draft 3

| ID | Finding review | Cách xử lý và vị trí | Bác bỏ/không sửa |
|---|---|---|---|
| D4-1 | P1-1 — HEAD Draft 3 và pin governance cũ làm S0-doc dừng trên checkout hiện tại. | §0 ghi chuỗi HEAD b6dbfa68… → 1e109b17… → dd70685e…, tác động merge 414 dòng chỉ thêm vào năm hồ sơ FEAT-063, các bản ghi mới liên quan và yêu cầu owner xác nhận dd70685e… làm baseline. §1 thay pin governance bằng hash hiện tại. | Không hợp thức hóa mismatch cũ; owner xác nhận baseline vẫn đang chờ. |
| D4-2 | P1-2 — allowlist thiếu core_models.py, migration Story revisions và offline-check; StoryRun-lite/DTR chưa phản ánh migration mới. | §1.3–1.4, §5.1–5.3 và §8 ghim/đọc đúng ba nguồn, ghi ancestry revision/down_revision/branch_labels/depends_on, phân biệt Core hiện có với Parent module chưa có, và nêu khác biệt vật lý–logic cần owner đối chiếu. | Không coi migration đã chạy; không coi log offline là verdict hoặc graph hiện tại. |
| D4-3 | P2-1 — M2-AT-07 chỉ phủ một phần NFR-36. | §3, §4, §4.2 và §7 bắt buộc owner ghi disposition PARTIAL; M2 chỉ xét access profile/grant trong scope được duyệt, media access đề xuất M5, cross-org feedback đề xuất M6. | Không claim toàn NFR-36 PASS từ M2-AT-07. |
| D4-4 | P2-2 — M2-AT-04 gộp hai actor và hai thao tác. | §3, §4 và §4.2 tách M2-AT-04A cho Admin tổ chức tạo class/assignment và M2-AT-04B cho Teacher được phân công tạo profile/enrollment; mỗi test nêu route, allow và deny theo SRS §21.2. | Giữ các route SRS hiện có; không thêm route hoặc quyền actor. |
| D4-5 | P2-3 — request/cancel qua route thật và bất biến D-127 chưa đủ rõ trước N-1. | §4.2, §6.1, §6.3 và §7 yêu cầu test route request lẫn cancel, trạng thái DELETE_PENDING, nhả active-owner nhưng giữ result/assets/receipts; N-1 là test PostgreSQL route với wiring thật trước khi thoát S2 và trước D9/client integration. | Không thay route test bằng unit/repository test hoặc test có monkeypatch. |
| D4-6 | P2-4 — điều kiện B2 và N-3 chưa phản ánh đúng approval FEAT-064. | §3, §5.3, §6.3, §7 và §10 ghi B2 được owner chấp nhận ACCEPTED_WITH_CONDITIONS trong scope T9/T13/T12 hẹp; N-3 về runner rerun bốn suite không ghim hash và runner đối soát hiện không còn trong thư mục script. | Không mở rộng điều kiện B2 sang M2; không xem T12 là toàn graph hoặc DB đã được xác minh độc lập. |
| D4-7 | P2-5 — OWNER_MODAL_CALL_APPROVED=NO chưa rõ phạm vi. | §0, §2.2, §6.3, §7 và §10 nói rõ approval POC/retest Modal sau merge có phạm vi riêng, không cấp phép M2 hay bật workload. | Không suy ra quyền gọi Modal/provider từ approval của task khác. |
| D4-8 | P2-6 — phân NFR-38 cho M2 là suy luận từ profile/age, AC-65 rộng hơn. | §2.3, §4, §4.2, §7 và §9 giữ giới hạn metadata tuổi/ngôn ngữ ở M2; mô tả AC-65 đủ nghĩa; M4 cho story và M5 cho video là phân bổ đề xuất cần owner xác nhận. | Không biến mapping roadmap thành quyết định owner hoặc claim chất lượng sư phạm. |
| D4-9 | Các điểm đã được reviewer xác nhận đạt. | §1, §4, §4.1, §5, §6 và §8 giữ nguyên 49 path đã được xác nhận tồn tại, route SRS, tiền tố M2-AT, BR-58 primitive/grant và audience M6, giới hạn NFR-38, synthetic-only, T12/T13 cùng các giới hạn của chúng; chỉ bổ sung nguồn thiếu và finding mới. | Không bác bỏ finding review nào. Không sửa các nội dung đã đạt ngoài phần cần liên kết với finding. |

## Thay đổi của Draft 3 so với Draft 2 (giữ để truy vết)

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

## 0. Trạng thái, checkout, merge và baseline cần owner xác nhận

Draft 4 được lập trên branch feature/feat063-be-foundation, HEAD dd70685eae58aaaefea3e567f5c23d09345a8513. Merge commit này có first parent 1e109b1726f327ac9383457b0dbdd535ef5c6518 và second parent fb834771c24957bb8e289fb95d21410b14181e57. Chuỗi lịch sử cần giữ rõ là b6dbfa68e66718f3f40902c093e9ebd634b1ebb9 → 1e109b1726f327ac9383457b0dbdd535ef5c6518 → dd70685eae58aaaefea3e567f5c23d09345a8513.

Trước khi tạo Draft 4, index rỗng và working tree chỉ có Draft 1, Draft 2, Draft 3 dưới dạng untracked. Các SHA-256 Draft 1/2/3 lần lượt là F47393FD1028B20D841114786E7D07B12BC8C89A67EF6697F0396EFCA7942E81, A09F7E6BF8534E85EE4EE4573209B5346861008AA4A5C4A8C907CF4EFEDCFE66 và A6F8CE23DA3650B38FF7E13BAF9052371B1655BE400BB6D5F9053A5D5E2C638D. Trước khi sửa, branch, HEAD, index, đúng ba path untracked và mọi hash nguồn được cung cấp đều đã khớp. Draft 1/2/3 là đầu vào chỉ đọc.

### Tác động của merge

So với first parent 1e109b17…, merge chỉ thêm 414 dòng, không xóa dòng nào, vào đúng năm hồ sơ FEAT-063:

| Hồ sơ | Thêm | Xóa |
|---|---:|---:|
| CONTEXT.md | 72 | 0 |
| DECISIONS.md | 36 | 0 |
| SOURCE_REGISTER.md | 42 | 0 |
| approvals/TASK_APPROVAL.md | 190 | 0 |
| status/STATUS.md | 74 | 0 |
| Tổng | 414 | 0 |

Các bản ghi mới liên quan gồm:

- D-139: giữ nguyên kết quả Parent AI mơ hồ; không retry hoặc coi là thành công; probe story tách rời không phải Parent API end-to-end.
- D-140: phân biệt manifest story với drawing; lỗi contract đã biết là terminal, outcome unknown không retry; activity Parent sau video; Teacher Deck/lesson visuals còn DRAFT và chịu gate SRS.
- D-141: owner cho phép một đợt retest non-video synthetic riêng, có retry fence và thời hạn chờ; thêm POC ảnh SAM2.1; không promotion, không bật workload, không video.
- Mục Merge reconciliation for decision IDs: dải D-127..D-135 trên nhánh Modal được đổi thành D-133..D-141 do trùng ID; mục D-120 trùng nội dung với D-131 không lặp lại.
- Các approval/retest Modal riêng gồm scaffold; drawing VLM L4 POC và corrective retry; hosting wave; API availability smoke; backend-to-Modal drawing slice; Parent image-to-script và generated-image/story/activity retest; AI flow/Teacher Deck POC; full non-video retest. Phạm vi, kết quả và giới hạn mỗi việc chỉ áp dụng cho plan/evidence của việc đó. Chúng không phê duyệt M2, không bật workload và không cấp quyền Modal/provider cho kế hoạch này.

Draft 3 ghim HEAD 1e109b17… và hash governance trước merge; các pin đó không còn khớp checkout này. Draft 4 ghim HEAD dd70685e… và hash bytes hiện tại tại §1. Việc pin lại là ghi nhận đúng nguồn hiện hành, không hợp thức hóa sai lệch pin lịch sử. Owner cần xác nhận dd70685eae58aaaefea3e567f5c23d09345a8513 là baseline cho lần review Draft 4 trước khi kế hoạch được chấp nhận hoặc dùng làm căn cứ cho phase kế tiếp.

Tài liệu này chỉ là kế hoạch DRAFT. Không có quyền implementation, migration, thao tác DB, provider, Modal, tích hợp frontend hoặc M3–M6. B2 được owner chấp nhận có điều kiện trong FEAT-064, đúng giới hạn ở §6.3; điều đó không phải approval M2. OWNER_MODAL_CALL_APPROVED=NO áp dụng cho mọi Modal/live call ngoài approval riêng có phạm vi riêng; approval POC/retest sau merge không cho phép triển khai M2 hay bật workload.

## 1. Căn cứ và pin nguồn

Các SHA-256 dưới đây là hash của bytes trong working copy đã kiểm tra trước khi tạo Draft 4. Không chuẩn hóa line ending và không thay pin để làm khớp. Mọi nguồn mới trong §1.3 đã được đọc trước khi đưa vào kế hoạch.

### 1.1. FEAT-063

| Tài liệu | SHA-256 |
|---|---|
| features/FEAT-063-system-architecture-rearchitecture/plan/BE_PARENT_TEACHER_VISION_DEMO_ROADMAP_20261102.md | A0A485EE421FBB1DA9DEC99DD8EC08279D14EAF27EC548AD6A0A4CE8F234F8FA |
| features/FEAT-063-system-architecture-rearchitecture/plan/B0_B13_SIX_MILESTONE_REDISPOSITION_PLAN_20261102.md | 773C4A8340C8E33AE39764D920B042AC19BACBAF6DC561FE9D5D3DFFCC4B5A5A |
| features/FEAT-063-system-architecture-rearchitecture/plan/BACKLOG_API_REV37_SRS23_MODAL_20261030.md | 380BF9F813CF809E35D9EA6F843E33A0DF892BA886E8C366AEB1C0F757A57391 |
| features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md | DCBF9786FF8983E34F2D3B4EBAB76301D0C52A6C9DE72CD08D0816BBD0D983FC |
| features/FEAT-063-system-architecture-rearchitecture/artifacts/DATA_TABLE_REGISTER.md | 3E793BB2C62C9E6C50780DE636EDDE442D382C62B4643552F2298AF374171E22 |
| features/FEAT-063-system-architecture-rearchitecture/evidence/COMMIT_WHITESPACE_NORMALIZATION_20261103.md | AF649B1518C4D550C2AEDE173063D6C46A889A7ADC9A70F187E86A23C72199C2 |
| features/FEAT-063-system-architecture-rearchitecture/status/STATUS.md | 827007578ABDAA78C7F987DC574268AA264FA666496C8A86C5D0F3E148035F9F |
| features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md | BD37F42EB3D20B98B0AC27C26F911CF86AD2290127EB0DC20F1253392C502962 |
| features/FEAT-063-system-architecture-rearchitecture/CONTEXT.md | 6CAA4A5BE423383B026A662051FB54709AF73B1178A5673849AD44B6B6697F1D |
| features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md | 7A16172EDBD3A701F3EC17FE277A05A1722B8DBD936F5C70BA0E87D91DD3EB2F |
| features/FEAT-063-system-architecture-rearchitecture/SOURCE_REGISTER.md | 2A419E529CE9603FF03A0697CC800A56826BC6EAD51B1596135AAA84B9FCF98B |

### 1.2. FEAT-064

| Tài liệu | SHA-256 |
|---|---|
| features/FEAT-064-current-flow-modal-vision-dev/evidence/A2_REV3_INDEPENDENT_REVIEW_CLOSEOUT_20261103.md | 10B12F4417A5E29DF0ED1697F33A8FAA08D692E71015998CCC8DE297328A1C36 |
| features/FEAT-064-current-flow-modal-vision-dev/plan/FEAT064_A2_B1_B2_SEQUENTIAL_GOAL_20261103.md | D7DEE2977C5AA28B26FCB117281DE8B23E4D4AA85A42922B8B37752FBDA8752A |
| features/FEAT-064-current-flow-modal-vision-dev/approvals/TASK_APPROVAL.md | 9D07B88190E8F5831D79431A79C2AAC944B266CB28CD29265E5D0283B77921B8 |

### 1.3. Nguồn mới sau merge và nguồn migration

| Nguồn | SHA-256 |
|---|---|
| backend/alembic/versions/20261104_story_revisions.py | 3618BEF0ECCB0E01EE61F65E1065F7AE8EA6297FE0781D965588614D0F1C37F8 |
| backend/src/sketch2life/infrastructure/persistence/core_models.py | 47D60EEECEF12F583B927BAB7FE3B74B9F19F15231E84E4039187376A502473A |
| .claude/handoff/logs/GB2_T12_OFFLINE_20261105A/offline-check.txt (local, git-ignore) | 6FF16B2E77EE7DB7CE18521484B92FAA9B40F685393D35A7746E74236313E143 |

### 1.4. Căn cứ và provenance

- Đã đọc AGENTS.md, .codex/sketch2life-harness.md, FEAT-063 CONTEXT.md, SOURCE_REGISTER.md, DECISIONS.md, STATUS.md, TASK_APPROVAL.md, roadmap, backlog, SRS, DTR, evidence normalization, FEAT-064 A2/B2 records, StoryRun-lite/Core models và migrations liên quan. Các pin tại §1.1–§1.3 là nguồn làm việc.
- D-132 chấp nhận roadmap sáu mốc làm baseline lập kế hoạch. SRS v2.3-draft chưa ký; route matrix chưa phải OpenAPI cuối.
- DTR mô tả ownership logic, không xác nhận schema vật lý. core_models.py là module Core hiện có; không tìm thấy module persistence Parent trong source tree được rà. Parent tables trong DTR vẫn là mô hình logic, không phải bằng chứng implementation.
- B0 plan hiện có hash 773C4A8340C8E33AE39764D920B042AC19BACBAF6DC561FE9D5D3DFFCC4B5A5A; hồ sơ duyệt ghi bytes gốc hash 03AEA386B8545624100688B68AA828A84CD154B47857CB5E98FB06354D6BB582. Evidence normalization nói bản gốc trong snapshot cục bộ git-ignore; phiên này không đọc hoặc xác minh snapshot. Không tự kết luận normalized bytes tương đương nội dung đã duyệt; cần owner xác nhận.
- OI-05..08 có trong SRS lịch sử v2.2; mapping sang SRS v2.3 chưa xác minh. Câu hỏi giữ mở tại §9.
- Route share Parent, schema vật lý Parent, catalog tuổi và một số owner columns chưa được đóng; đánh dấu chưa xác minh.
- Migration 20261104_story_revisions.py hiện có trong source và được ghim riêng ở §1.3; pin nguồn chứng minh file bytes, không chứng minh migration đã chạy.
- Offline-check ghi rõ không có DB connection, network hay migration execution, và kết thúc bằng facts only; not a pass/fail verdict. Danh sách script_heads trong file kết thúc ở 20261103_story_upload_compat, không chứa migration mới 20261104_story_revisions; do đó log này không phải graph/head evidence cho checkout hiện tại và không được tính là PASS.
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

Roadmap matrix liệt kê NFR-38 cạnh M2 nhưng không giao rõ toàn bộ AC-65 cho M2. Gán toàn bộ NFR-38 vào M2 chỉ từ profile/age là suy luận của kế hoạch, không phải quyết định owner. M2 chỉ đề xuất kiểm tra metadata vi-VN và tuổi 36–120 tháng được bảo toàn qua profile contract/revision và StoryRun. Không claim age-band catalog/version đã chốt, hay chất lượng Montessori-inspired, child-centered hoặc người lớn là guide/observer/supporter.

AC-65 yêu cầu: khi Parent/Teacher dùng profile cá nhân hóa và lesson để AI lập story/video, kết quả tuân age band/context đã duyệt, nội dung tiếng Việt, và video được tạo riêng theo tranh trẻ. NFR-38 phải ghi disposition PARTIAL cho M2. Story/AC-65 được đề xuất phân bổ vào M4; video/AC-65 vào M5. Đây là đề xuất lập pha cần owner xác nhận, không phải quyết định mặc định.

## 3. Subphase M2 đề xuất

Đây là thứ tự để owner xét. Mỗi subphase cần Task Approval riêng với scope, file allowlist, evidence, DB identity và command ceiling. Hoàn tất một pha không tự mở pha kế tiếp.

| Pha | Phụ thuộc | Nội dung | Tiêu chí thoát có thể kiểm chứng | Stop gate |
|---|---|---|---|---|
| S0-doc | Không | Đối chiếu nguồn, mapping schema, owner decisions, B0 provenance và migration graph bằng source; không chạy command/DB. | Requirement có source ID; unknown được gắn nhãn; route/table/owner/M2-AT có crosswalk; B0 provenance được owner disposition hoặc vẫn block; các giới hạn evidence được ghi; không claim implementation approval. | Hash lệch, owner assumption bị coi là quyết định, hoặc cần DB/file ngoài approval thì dừng. |
| S0-owner-run | S0-doc đóng; owner chọn DB và ghi approval riêng | Owner-run chỉ đọc để đối soát schema vật lý/Alembic và ghi mypy baseline theo command/hash được duyệt. | DB identity khớp manifest; bảng/version/chênh lệch current source được ghi; baseline mypy có output thật, không suy diễn phần chưa chạy. | Nếu safety check không có verdict thì ghi NOT RUN và dừng tại cổng; không thay bằng lệnh/shell khác. Sai identity, dữ liệu không synthetic hoặc cần write/migration thì dừng. Pha này không cấp phép migration. |
| S1a identity/tenant/profile/age | S0-doc và S0-owner-run đóng (route/persistence acceptance cần PostgreSQL thật; unit/doc chỉ chạy trước nếu approval tách riêng) | Identity/role assignment, tenant isolation, profile ownership và age provenance. | M2-AT-01/02/03/04A/04B/10 đạt theo tầng đã duyệt; route test persistence dùng PostgreSQL thật và wiring thật. | Thiếu role matrix, profile owner hoặc age policy thì deny-by-default; không tự tạo route/policy. |
| S1b grant/revoke/consent | S1a; owner quyết định 3; OI gate đã xác định | Scoped grant/revoke, purpose/expiry/audit và consent/data authorization trong scope được chọn; NFR-36 M2 chỉ PARTIAL. | M2-AT-05/06/07 đạt trong scope được duyệt; owner ghi PARTIAL cho NFR-36 và disposition các phần hoãn; thiếu, pending, revoked hoặc expired đều deny. Nếu B4b hoãn thì REAL và LEGACY_UNCLASSIFIED bị từ chối; không claim consent production-ready. | OI mapping, purpose, fields, expiry, admin scope/reason/audit policy hoặc disposition chưa chốt thì không bật share/consent. |
| S2 owner/job/asset/revision/lifecycle | S1a; S1b nếu bật; migration target đã duyệt | Durable owner/scope refs, job/asset/revision, AiJobService mapping, idempotency/replay, cancel, restart/recovery, DELETE_PENDING/D-127. | M2-AT-08/09 đạt. N-1 phải test PostgreSQL mức route cho request → job → status, gồm request VÀ cancel qua route thật với wiring thật, không monkeypatch/override dependency; đạt trước khi thoát S2 và trước D9/client integration. B1 orphan có invalidation/reconciliation/read-exposure contract và regression trước dữ liệu non-synthetic/provider. | Orphan có thể được đọc/công bố như accepted result, job/aggregate lệch, thiếu N-1, hoặc safety check NOT RUN thì chưa thoát S2. |
| S3 freeze và đóng M2 | S1a, S1b theo disposition, S2 | Đối chiếu evidence và freeze contract; đóng OpenAPI P3 hai POST submit/cancel trước frontend/client. | Tất cả M2-AT pass hoặc PARTIAL disposition được owner ghi; NFR-36 và NFR-38 có disposition; OpenAPI parity được kiểm; conditions được gán owner/phase; independent review ACCEPTED. | Không tích hợp frontend/client khi OpenAPI P3 còn mở; không tự mở M3 hoặc bật workload. |

## 4. Traceability requirement → route/API → bảng → owner → acceptance

Route là candidate theo SRS v2.3-draft, chưa freeze. “SRS §21.2” nghĩa là path có trong route table; “suy luận” là mapping chưa gắn trực tiếp; “chưa xác minh” là chưa có route canonical.

| Requirement | Route/API và nguồn | Bảng/owner logic theo DTR | Acceptance |
|---|---|---|---|
| FR-PL-01 | POST /v1/parent/profiles; GET/PATCH /v1/parent/profiles/{profile_id} — SRS §21.2. Identity endpoint — chưa xác minh. | parent.child_profiles, parent.profile_share_grants; be1.adult_identities, be1.organization_assignments; core audit — Parent/BE1/Core. | M2-AT-01/05. |
| FR-PL-02 | POST /v1/organizations/{org_id}/classes và POST /v1/classes/{class_id}/assignments — Actor Admin tổ chức; POST /v1/classes/{class_id}/profiles — Teacher được phân công; SRS §21.2. List/read routes chưa xác minh. | be1.organizations, classrooms, organization_assignments, enrollments — BE1; consumer scope thuộc owner tương ứng. | M2-AT-02/04A/04B. |
| FR-PL-07 | Parent profile POST/GET/PATCH là SRS §21.2, không phải grant. Invite/accept/revoke route — chưa xác minh. | parent.profile_share_grants, parent.child_profiles, parent.data_authorizations; be1.managed_profiles — Parent/BE1. | M2-AT-05. |
| FR-PL-08 | Profile GET/PATCH và POST /v1/story-runs — SRS §21.2. Grant/download/token/cache/revoke route — chưa xác minh. | parent.profile_share_grants, core.asset_lineage, ai_jobs.job/receipts — Parent/Core/AI Jobs. | M2-AT-06/09. |
| FR-PL-25 | Parent profile POST/GET/PATCH và POST /v1/classes/{class_id}/profiles — SRS §21.2. Age-band catalog route — chưa xác minh. | parent.profile_revisions, be1.profile_revisions, age-band catalog — Parent/BE1/catalog owner chưa xác minh. | M2-AT-03/10. |
| BR-48 | Profile route không phải share route. Parent share invite/accept/revoke — chưa xác minh. | parent.profile_share_grants, parent.data_authorizations — Parent. | M2-AT-05/06; thiếu grant phải deny. |
| BR-49 | POST /v1/organizations/{org_id}/classes; POST /v1/classes/{class_id}/assignments; POST /v1/classes/{class_id}/profiles — SRS §21.2, actor Admin cho hai route đầu và Teacher được phân công cho route profile. | be1.organizations, classrooms, organization_assignments, enrollments — BE1. | M2-AT-01/02/04A/04B. |
| BR-57 | Age qua profile routes SRS §21.2; catalog/version route — chưa xác minh. | Profile revisions, age-band catalog — Parent/BE1/catalog owner chưa xác minh. | M2-AT-03/10. |
| BR-58 | Nghĩa SRS: audience lesson là nhóm Parent hoặc người được mời cụ thể và có thể thu hồi. Route class assignment/profile (SRS §21.2) không phải lesson-audience grant và không dùng để chứng minh BR-58. Route grant/revoke và route lesson grant cho nhóm Parent hoặc invitee — chưa xác minh; phần audience đầy đủ thuộc M6. | be1.parent_groups/parent_group_members (BE1); lesson.access_grants (Lesson); primitive M2 dùng parent.profile_share_grants. | M2: chỉ primitive grant/revoke có thể thu hồi qua M2-AT-05/06 (S1b). M6: audience nhóm/invitee đầy đủ; BR-58 PARTIAL trong M2. |
| NFR-34 | Áp dụng cross-cutting trên profile, assignment, grant, asset/job routes; share/token routes — chưa xác minh. | Parent, BE1, Core, AI Jobs qua contract/ports. | M2-AT-01/02/05/06/08/09. |
| NFR-36 | SRS §8/§31.9: Admin access child media, profile data và cross-role grant phải theo permission/reason/audit; feedback không lộ organization khác. M2 chỉ profile/grant primitive trong scope được duyệt. Media access đề xuất hoãn M5; cross-org feedback đề xuất hoãn M6 theo roadmap, cần owner disposition. | BE1/Parent/Core/Lesson owners. | M2-AT-07 kiểm phần M2; disposition NFR-36 bắt buộc PARTIAL, không phải PASS. |
| NFR-38 | SRS §8/§31.9 AC-65; M2 profile/age metadata là phần nền. Story và video quality chưa được roadmap phân bổ rõ toàn bộ. | Profile metadata M2; Story M4/Video M5 là phân bổ đề xuất cần owner xác nhận. | M2-AT-10 chỉ kiểm metadata; NFR-38 PARTIAL tới khi owner disposition và xác nhận phase AC-65. |

### 4.1. Route candidates theo SRS

SRS §21.2 nêu các route nền M2:

- POST /v1/parent/profiles
- GET/PATCH /v1/parent/profiles/{profile_id}
- POST /v1/organizations/{org_id}/classes
- POST /v1/classes/{class_id}/assignments
- POST /v1/classes/{class_id}/profiles

Không tự thêm route share, identity, revoke, admin media hoặc age-band. GET /v1/me từng là suy luận độ tin cậy thấp, không phải route canonical. SRS §21.2 có các route upload/story/job; chỉ dùng trong M2 khi owner duyệt scope. Placeholder org/organization phải thống nhất trước freeze OpenAPI.

### 4.2. Định nghĩa M2 acceptance tests

Các test dưới đây là kế hoạch, chưa chạy. Route acceptance phải dùng PostgreSQL task-owned, router/composition và dependency wiring thật; không monkeypatch route/dependency cần kiểm. Các test FEAT-064 N-1 dưới đây là gate route riêng, không chứng minh M2 route đã đạt.

| ID | Requirement/pha | Given / When / Then | Tầng | DB task-owned |
|---|---|---|---|---|
| M2-AT-01 | FR-PL-01, BR-49, NFR-34; S1a | Given Parent/Teacher/Admin có role/assignment hợp lệ hoặc thiếu/thu hồi; when đọc/ghi resource; then chỉ role/scope hợp lệ được phép, denial không lộ metadata ngoài scope, audit metadata-only. | Domain/service unit, HTTP contract, route PostgreSQL. | Có cho route/persistence; không cho unit. |
| M2-AT-02 | FR-PL-02, BR-49; S1a | Given hai organization; when principal tenant A truy cập resource tenant B; then deny theo contract, không lộ existence/content. | Unit matrix và route integration wiring thật. | Có cho integration. |
| M2-AT-03 | FR-PL-25, BR-57; S1a | Given tuổi 36/120, ngoài biên, provenance/version; when tạo và đọc profile revision; then áp dải owner chốt, giữ provenance và không suy ra band chưa định nghĩa. | Domain/contract unit và repository integration. | Có cho persistence. |
| M2-AT-04A | FR-PL-02, BR-49; S1a; SRS §21.2 | Given Admin tổ chức thuộc đúng org và còn capacity; when POST /v1/organizations/{org_id}/classes rồi POST /v1/classes/{class_id}/assignments với đúng một Teacher active; then class tạo thành công (201 class ref) và assignment được ghi (200 assignment revision). Given capacity hết, sai tenant hoặc Teacher gọi route Admin; when gửi cùng command; then deny/CLASS_CAPACITY_REACHED theo contract, không tạo assignment hoặc lộ resource ngoài scope. | Route PostgreSQL acceptance với actor Admin đã xác thực và wiring thật. | Có. |
| M2-AT-04B | FR-PL-02, BR-49; S1a; SRS §21.2 | Given Teacher được phân công vào class cùng tenant và expected class revision hiện tại; when POST /v1/classes/{class_id}/profiles với trường profile có cấu trúc; then tạo 201 profile/enrollment ref và tối đa một enrollment active. Given Teacher không được phân công, sai tenant hoặc Admin gọi route Teacher; when gửi command; then deny theo error envelope, không tạo profile/enrollment và không lộ dữ liệu ngoài scope. | Route PostgreSQL acceptance với actor Teacher đã xác thực và wiring thật. | Có. |
| M2-AT-05 | FR-PL-07, BR-48, BR-58 (primitive thu hồi được); S1b | Given grant pending/active/revoked/expired với purpose/scope; when đọc profile; then chỉ grant active đúng scope cho phép. Nếu canonical route chưa chốt, chỉ test domain/service và S1b chưa đóng. | Unit trước; route PostgreSQL sau khi route được duyệt. | Có cho route/persistence. |
| M2-AT-06 | FR-PL-08, BR-48, BR-58 (primitive thu hồi được), NFR-34; S1b | Given field-scoped grant liên kết asset/token/cache/job; when revoke; then lần đọc/tải mới, token/cache access và job chưa accepted bị chặn, audit không ghi content/token. | API/asset/job integration; không gọi provider. | Có. |
| M2-AT-07 | NFR-36; thoát S1b, đối chiếu S3 | Given Admin thiếu permission, scope hoặc reason code; when gọi operation profile/grant thuộc M2; then deny và không lộ resource. Given permission/scope/reason hợp lệ theo policy owner đã duyệt; when gọi operation; then chỉ scope được cấp được phép và audit metadata-only. Media access và cross-org feedback không được tính vào test M2; chúng cần disposition PARTIAL và phase riêng. | Unit + route integration cho primitive M2; không giả lập media/feedback đã hoàn tất. | Có cho route M2. |
| M2-AT-08 | Roadmap Mốc 2 (owner-lock, cancel, restart, ownership của job), D-127, NFR-34 — nguồn roadmap/decision, không phải FR-PL; S2 | Given synthetic Parent/Teacher actor có quyền và run ở trạng thái hợp lệ; when POST /v1/story-runs tạo request qua router thật, sau đó POST /v1/story-runs/{id}/cancel sau PREPARATION_REVIEW; then request tạo đúng một run/job theo idempotency và cancellation chuyển DELETE_PENDING, nhả active-owner ngay trong transaction nhưng giữ result/assets/receipts; không coi DELETE_PENDING là đã xóa. Replay/cancel lặp không tạo side effect trùng; stale result không accepted. | Route + PostgreSQL integration/restart với composition, repository và wiring thật. | Có. |
| M2-AT-09 | FR-PL-08, NFR-34 và FEAT-064 N-1; S2 | Given child request tổng hợp và actor/device hợp lệ; when gọi POST /api/be1/v1/assistance-requests, đọc status qua GET /api/be1/v1/organizations/{organization_id}/sessions/{session_id}/assistance-requests/{assistance_id}/status, rồi gọi POST /api/be1/v1/assistance-requests/{assistance_id}/cancel; then request → job → status và cancel đều đi qua route thật với authentication/dependency wiring thật; không monkeypatch _build_child_binding hoặc override dependency cần kiểm. Status đúng scope; orphan không được đọc/công bố như accepted. Đây là điều kiện N-1 trước khi thoát S2 và trước D9 hoặc frontend/client integration. | PostgreSQL route integration, real app composition/wiring. | Có, bắt buộc. |
| M2-AT-10 | FR-PL-25, BR-57, NFR-38; S1a | Given locale vi-VN và tuổi 36–120; when serialize, persist, đọc profile revision và StoryRun; then metadata được giữ và tuổi ngoài biên bị xử lý theo policy đã duyệt. Không đánh giá chất lượng AC-65 trong test M2. | Contract/unit và persistence integration. | Có cho persistence. |

## 5. Dữ liệu, ownership và migration

### 5.1. Ownership logic theo DTR và code hiện có

| Owner | Nhóm bảng logic |
|---|---|
| BE1 | organizations, adult_identities, organization_assignments, classrooms, managed_profiles, enrollments, consent_records, data_lifecycle_requests, profile_revisions, profile_context_entries, profile_support_needs. |
| Parent | child_profiles, profile_revisions, profile_context_entries, profile_support_needs, data_authorizations, profile_share_grants. |
| Core | asset_lineage, upload_sessions, upload_parts, upload_command_receipts và Core metadata/audit/revision hiện hành theo DTR. |
| AI Jobs | job, attempt, command/completion receipts, semantic_request, cancellation_notice, outbox, job_events. |
| Story | runs, run_inputs, review_decisions, command receipts và các bảng Story theo DTR. |

Đây là ownership logic theo DTR, không xác nhận schema vật lý. backend/src/sketch2life/infrastructure/persistence/core_models.py là module Core hiện có; nó khai báo các mapping Core như core_aggregate_revisions, core_asset_metadata, core_audit_entries, core_outbox_events và các mapping canvas/receipt hiện hữu. Nó không định nghĩa bảng Parent. backend/src/sketch2life/infrastructure/story_run_lite/tables.py cũng khai báo mapping Core upload và StoryRun-lite. Chưa tìm thấy module persistence Parent; parent.* trong DTR vẫn là bảng logic đích chưa được hiện thực hóa trong source đã rà. Không suy ra schema vật lý Parent từ Core hoặc BE1.

Không tạo FK/SQL join xuyên owner/schema. Aggregate, job, asset và receipt có state riêng; job progress không thay aggregate state.

### 5.2. Mapping StoryRun-lite, DTR và 58 hàng synthetic

- Source StoryRun-lite hiện có physical story.runs; migration 20261104_story_revisions thêm child_age_months nullable với check 36–120 và mở rộng run_state cho các state script, VIDEO_ADMISSION_PENDING, DELETE_PENDING, FAILED. Đây là source/migration mapping, không phải bằng chứng đã chạy.
- DTR mô tả logic story.runs với story_run_id, profile/owner refs và current_story_revision_ref; StoryRun-lite hiện dùng cột physical run_id. Giữ mapping run_id → story_run_id là crosswalk cần owner/chủ schema đối chiếu, không tự đổi tên hay giả định dữ liệu đã chuyển.
- Migration tạo physical story.story_revisions, story.story_scenes và story.story_revision_reviews. DTR có logic story.story_revisions, story.story_scenes và story.review_decisions; field/key mapping chưa tương đương được chứng minh. Đặc biệt, không tự đồng nhất story_revision_reviews với review_decisions; S0-doc phải lập field/key/owner crosswalk và đánh dấu unknown đến khi được owner duyệt.
- Giữ mapping storyrun_upload_sessions → core.upload_sessions cùng upload parts/receipts; ghi owner columns, asset refs và history. Không đổi nghĩa hoặc xóa history âm thầm.
- Parent parent.child_profiles, parent.profile_revisions, parent.profile_share_grants và parent.data_authorizations vẫn là logical target trong DTR, không phải module/bảng hiện có được migration Story revisions tạo.
- B3 manifest/sign-off là đề xuất tới khi owner ký đúng bytes.
- A2 ghi còn 58 synthetic rows sau lỗi teardown. Owner chọn giữ, copy/di trú có mapping và approval, hoặc cleanup qua approval riêng. Mặc định giữ nguyên; không reset shared sketch2life.
- Trước migration: DB task-owned, physical schema inventory, target Alembic graph/revision, snapshot/restore expectation, exact approval. Kết quả B2 không chứng minh trạng thái DB hiện tại.

### 5.3. Alembic graph và command ceiling

Repository có nhiều root/head và depends_on; không dùng upgrade heads làm đích M2 mặc định. Ancestry của nhánh StoryRun-lite theo source đã đọc:

| Revision trên nhánh | down_revision | branch_labels | depends_on | Vai trò |
|---|---|---|---|---|
| 20261104_story_revisions | 20261103_story_upload_compat | None | None | Endpoint hiện thấy của nhánh StoryRun-lite trong source; không khẳng định là head duy nhất của toàn repository. |
| 20261103_story_upload_compat | 20261102_story_run_lite | None | None | Compatibility migration cho Story upload. |
| 20261102_story_run_lite | None | story_run_lite | 20261102_pv_0001 | Gốc nhánh StoryRun-lite, phụ thuộc pilot vision. |
| 20261102_pv_0001 | None | pilot_vision | 20261101_be1_age_0001, 20261015_ai_0001 | Gốc nhánh pilot_vision và hai dependency được khai báo trong source. |

Migration 20261104_story_revisions nối sau 20261103_story_upload_compat; nó thêm tuổi vào run, cập nhật state constraint/receipt operation và tạo các bảng revision/scene/review ở §5.2. Source này không được thực thi trong task tài liệu.

Offline-check owner-run đã ghim ở §1.3 ghi upgrade plan 27 bước từ DB rỗng, 9 hàng version và 9 script_heads khớp nhau tại thời điểm log; log ghi không có DB connection, network hay migration execution. Danh sách script_heads của log kết thúc ở 20261103_story_upload_compat, không có 20261104_story_revisions. Vì vậy 27 bước và danh sách head đó là facts lịch sử của log, không phải graph hiện tại sau merge, không chứng minh migration đã chạy, và không có safety/pass verdict. Safety check của task này: NOT RUN; dừng ở cổng tương ứng, không thử lệnh hoặc shell khác để thay verdict.

FEAT-064 approval ghi kế hoạch downgrade pilot_vision@base từ graph khi đó gồm ba bước; bước đầu 20261103_story_upload_compat có source không reversible. Đây là ghi nhận graph/source trong hồ sơ, không phải bằng chứng full-head downgrade đã chạy rồi thất bại. Round-trip owner-run chỉ thuộc nhánh pilot_vision, trạng thái trung gian, DB mới và chín bảng pilot rỗng.

Điều kiện migration tương lai:

1. S0-doc ghi ancestry, target revision, down_revision, branch_labels, depends_on, current source head candidates và lý do chọn; không chạy Alembic.
2. Offline-check không có verdict và không bao gồm migration mới nên không mở cổng graph/current-schema. S0-owner-run chỉ đọc physical schema/Alembic trên DB task-owned sau approval riêng và safety verdict rõ ràng.
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
- B1 stale-owner orphan cần invalidation/reconciliation/read-exposure contract và regression trước dữ liệu non-synthetic/provider.
- B2 được Project owner chấp nhận ACCEPTED_WITH_CONDITIONS, không phải M2 approval. Phạm vi chấp nhận là plan B2 đã ghim: T9 bốn operation assistance gateway, T13 synthetic dry-run với stub loopback và T12 trong giới hạn nêu dưới; không có quyền M2, provider/live call hay production readiness.
- B2 T12 chỉ là round-trip nhánh pilot_vision ở trạng thái trung gian, DB mới với bảng pilot rỗng; không có dữ liệu, không có chuỗi story_run_lite, không phải full graph. Phần DB test_migrations.py là NOT RUN. Mypy backend/tests/integration/test_be1_postgres_api.py là NO VERDICT và được owner chấp nhận làm giới hạn, không phải PASS. Mọi dữ kiện PostgreSQL là owner-run, chưa được reviewer xác minh qua DB độc lập.
- B2 T13 chỉ chứng minh timeout của hàm script-local _invoke_slow_stub_once với stub; pilot_job_repository=None làm trạng thái child/teacher là unknown. Không chứng minh job thật chuyển UNKNOWN qua worker/provider lifecycle.
- Finding N-1 (P2, không chặn B2) còn là điều kiện: chưa có test chạy luồng POST request và POST cancel qua route thật. M2-AT-09 phải đi qua route PostgreSQL, wiring/auth thật, không monkeypatch _build_child_binding hoặc override dependency cần kiểm; test request → job → status và cancel phải đạt trước khi thoát S2 và trước D9 hoặc frontend/client integration.
- Finding N-3 vẫn phải được ghi đúng: lần rerun bốn suite GB2_T12_RERUN_20261105T013143 dùng runner mới không có hash trong approval; danh tính/hash runner đó không được ghi và không xác định trong thư mục script cục bộ. Runner đối soát run_b2_t12_readonly_recon.ps1 (hash trong approval 7466CB770F65F17477089A1C5962E4774E462059941F108017B67B2023DA70F2) hiện không còn được tìm thấy trong thư mục script cục bộ; nguyên nhân chưa biết. Helper b2_t12_readonly_recon.py vẫn còn. Không khẳng định đã kiểm chứng lại runner hay dùng các rerun đó làm safety verdict.
- OpenAPI P3 cho hai POST submit/cancel của assistance_requests.py phải đóng trước frontend/client integration. Đây là gate riêng S3; không thay thế N-1 route test.
- B2 mypy limitation và evidence owner-run không tạo baseline cho M2. M2 cần baseline được owner duyệt riêng, nếu scope/command yêu cầu.
- OWNER_MODAL_CALL_APPROVED=NO: các approval POC/retest Modal sau merge chỉ áp dụng plan riêng, chủ yếu synthetic/dev và có retry/workload fence; không approval nào trong merge cho phép triển khai M2 hoặc bật workload.

## 7. Acceptance criteria và stop gates

1. Mỗi requirement §4 có route status, bảng logic, owner, mã M2-AT và evidence. NFR-36 phải có owner disposition PARTIAL cho M2 và ghi rõ child media access được đề xuất hoãn M5, cross-org feedback được đề xuất hoãn M6; M2-AT-07 không chứng minh phần hoãn. NFR-38 phải có disposition PARTIAL; M2 chỉ claim metadata tuổi/ngôn ngữ, AC-65 story/video là phân bổ M4/M5 đề xuất chờ owner xác nhận. BR-58 vẫn PARTIAL: primitive thu hồi được ở M2, audience group/invitee đầy đủ ở M6. PARTIAL không phải PASS.
2. Identity, role, tenant, profile ownership, Admin class/assignment, Teacher profile/enrollment và age provenance đạt M2-AT-01/02/03/04A/04B/10 với positive/negative tests; DB thật cho route/persistence.
3. Grant/consent theo quyết định 3/OI gate; thiếu grant/policy thì deny, REAL và LEGACY_UNCLASSIFIED bị chặn nếu B4b hoãn.
4. Lifecycle đạt M2-AT-08/09; request và cancel phải được gọi qua route thật. N-1 PostgreSQL route test với wiring thật bắt buộc trước khi thoát S2 và trước D9/client integration; B1 orphan có reconciliation/read-exposure contract và regression trước dữ liệu non-synthetic/provider.
5. Target migration/schema inventory/data disposition/rollback limits được owner phê duyệt; DB/source/snapshot gate lệch thì dừng. Offline-check fact-only không phải verdict; safety check NOT RUN không mở gate.
6. OpenAPI request/response/error parity được freeze trước client integration; P3 đóng trong S3.
7. Evidence lưu tại feature evidence path được approval chỉ định; PARTIAL/NOT RUN/owner-run provenance ghi đúng. Plan review và implementation review là hai việc riêng.
8. Không mở M3–M6, không bật provider/Modal hoặc workload.
9. Draft 4 vẫn DRAFT / AWAITING OWNER REVIEW cho tới khi owner xác nhận baseline và review; chưa có implementation approval.

## 8. Candidate allowlist theo subphase

Các path dưới đây đã được xác nhận tồn tại khi rà soát (trừ cột "Path mới", ghi chưa xác minh); giữ nguyên 49 path đã được reviewer xác nhận. Bảng chỉ là candidate để owner/reviewer xem xét trước Task Approval; không cấp quyền sửa. Các nguồn mới ở S0-doc chỉ đọc, không mở allowlist thực thi. Không dùng wildcard.

Quy ước:

- **Chỉ đọc:** tham chiếu hoặc baseline hồi quy; không được sửa nếu Task Approval không nêu đích danh file và lý do.
- **Candidate có thể sửa:** chỉ được sửa khi Task Approval của đúng pha liệt kê file đó, kèm hash trước khi sửa.
- **Path mới:** file chưa tồn tại; tên và hash phải có trong approval trước khi tạo. Test hiện có là baseline hồi quy chỉ đọc; test M2 là file mới.
- **Hồ sơ governance** (CONTEXT, DECISIONS, STATUS, TASK_APPROVAL của FEAT-063/FEAT-064, ledger) chỉ do phiên ghi (Codex) cập nhật sau lệnh của owner. Chúng nằm ngoài allowlist của mọi phiên thực thi và chỉ đọc đối với phiên thực thi.
- Draft 1, Draft 2 và Draft 3 của plan này là đầu vào chỉ đọc; Draft 4 là artifact review hiện tại, không phải plan được duyệt.

| Pha | Chỉ đọc | Candidate có thể sửa | Path mới (chưa xác minh) | Exclusions / hard stop |
|---|---|---|---|---|
| S0-doc | Mọi tài liệu pin ở §1; features/FEAT-063-system-architecture-rearchitecture/SOURCE_REGISTER.md; features/FEAT-063-system-architecture-rearchitecture/evidence/COMMIT_WHITESPACE_NORMALIZATION_20261103.md; Draft 1/2/3 của plan này; backend/alembic/versions/20261104_story_revisions.py; backend/src/sketch2life/infrastructure/persistence/core_models.py; .claude/handoff/logs/GB2_T12_OFFLINE_20261105A/offline-check.txt (local, git-ignore); hồ sơ governance. | Không có file hiện có. | Bản plan kế tiếp; evidence addendum S0-doc (tên chưa xác minh). | Không sửa source/test/migration/SRS/DTR/roadmap/governance. Cần DB hoặc file ngoài approval thì dừng. |
| S0-owner-run | backend/alembic/env.py; backend/alembic/versions/20261014_0002_be1_runtime.py; backend/alembic/versions/20261015_ai_0001_ai_jobs_schema.py; backend/alembic/versions/20261028_ll_0001_lesson_library.py; backend/alembic/versions/20261031_be1_synthetic_eligibility.py; backend/alembic/versions/20261101_be1_age_provenance.py; backend/alembic/versions/20261102_pilot_vision.py; backend/alembic/versions/20261102_story_run_lite.py; backend/alembic/versions/20261103_story_upload_compat.py; backend/alembic/versions/20261104_story_revisions.py; backend/src/sketch2life/infrastructure/persistence/be1_models.py; backend/src/sketch2life/infrastructure/persistence/core_models.py; backend/src/sketch2life/infrastructure/ai_jobs/sql/tables.py; backend/src/sketch2life/infrastructure/story_run_lite/tables.py. core_models.py là Core hiện có; chưa tìm thấy module persistence Parent trong source đã rà. Chỉ đọc. | Không có; allowlist ghi repo rỗng. | Đường dẫn evidence output và script owner-run (hash ghim trong approval) — chưa xác minh. | Chưa có DB identity, command, hash, snapshot, approval thì không chạy. Không migration, không shared DB, không ghi source. |
| S1a | backend/src/sketch2life/infrastructure/identity/firebase_token_verifier.py; backend/src/sketch2life/domain/child_age.py; backend/src/sketch2life/contracts/schemas/child_learning_profile.py (hai file này chỉ chuyển sang candidate sửa nếu approval đổi chính sách tuổi/contract); baseline hồi quy: backend/tests/unit/test_profile_age_invariant.py; backend/tests/unit/test_age_provenance_columns.py; backend/tests/unit/test_child_learning_profile_contract.py; backend/tests/contract/test_be1_synthetic_pilot.py; backend/tests/integration/test_be1_age_provenance_postgres.py. | backend/src/sketch2life/application/ports/identity.py; backend/src/sketch2life/application/services/be1_runtime.py; backend/src/sketch2life/interfaces/http/routers/be1_registry.py; backend/src/sketch2life/interfaces/http/routers/be1_records.py; backend/src/sketch2life/infrastructure/persistence/be1_models.py (chỉ nếu schema đổi và migration được duyệt). | Module/route/bảng/migration Parent identity-profile và test M2-AT-01/02/03/04A/04B/10. | Không sửa .env, credential, Firebase secret, shared DB, FEAT-064, M3–M6. |
| S1b | backend/tests/unit/test_member_fact_consent_rules.py (baseline); các file S1a sau khi S1a đóng (hash ghim lại). | backend/src/sketch2life/application/ports/identity.py; backend/src/sketch2life/infrastructure/persistence/core_store.py; backend/src/sketch2life/interfaces/http/routers/be1_registry.py; backend/src/sketch2life/interfaces/http/routers/be1_records.py. Các file dùng chung với S1a chỉ sửa sau khi S1a đóng; không sửa song song. | Module share-grant/data-authorization, route canonical, migration và test M2-AT-05/06/07. | REAL/LEGACY_UNCLASSIFIED bị deny nếu owner/OI gate chưa đóng. BE1 consent không tự động là Parent authorization. |
| S2 | Mặc định chỉ đọc: backend/src/sketch2life/application/ports/ai_jobs.py; backend/src/sketch2life/application/services/ai_jobs.py; backend/src/sketch2life/domain/ai_jobs/model.py; backend/src/sketch2life/infrastructure/ai_jobs/sql/tables.py; backend/src/sketch2life/infrastructure/ai_jobs/sql/repository.py; backend/src/sketch2life/infrastructure/ai_jobs/worker.py; backend/src/sketch2life/infrastructure/ai_jobs/reconciler.py; backend/src/sketch2life/domain/story_run_lite.py; backend/src/sketch2life/application/services/story_run_lite.py; backend/src/sketch2life/infrastructure/story_run_lite/repository.py; backend/src/sketch2life/infrastructure/story_run_lite/tables.py; baseline hồi quy: backend/tests/unit/test_ai_job_lifecycle.py; backend/tests/integration/ai_jobs/test_restart_recovery.py; backend/tests/integration/ai_jobs/test_owner_fence.py; backend/tests/integration/test_story_run_lite_postgres.py; backend/tests/integration/test_story_run_lite_replay_concurrency.py; backend/tests/integration/test_pilot_assistance_routes_t9.py (dùng để đối chiếu: test này monkeypatch `_build_child_binding` ở dòng 257 nên không thay N-1). | Không có mặc định. File hiện có ở cột Chỉ đọc chỉ chuyển sang candidate sửa khi Task Approval nêu từng file và lý do (ví dụ mapping của quyết định 5 hoặc reconciliation B1). | Module Parent aggregate/asset/revision; migration; test N-1 qua route request và cancel thật (PostgreSQL thật, wiring thật, không monkeypatch); regression B1 orphan; evidence S2. | Không sửa backend/tests/integration/ai_jobs/test_migrations.py hoặc fixture tạo/xóa DB khi chưa có approval riêng; không sửa backend/alembic/versions/20261103_story_upload_compat.py; không chấp nhận orphan. |
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
| 8. Baseline Draft 4 | Owner xác nhận dd70685eae58aaaefea3e567f5c23d09345a8513 là baseline review Draft 4, hoặc dừng và cập nhật pins sau khi xác định checkout có thẩm quyền. | Merge HEAD chứa hồ sơ governance mới; pin HEAD Draft 3 không còn khớp checkout. Đây là xác nhận baseline, không phải approval scope. | S0-doc và mọi phase tiếp nối. | Chưa dùng kế hoạch cho phase tiếp theo tới khi owner ghi nhận baseline. |
| 9. NFR-36 disposition | Owner xác nhận PARTIAL cho M2 và mapping đề xuất child media sang M5, cross-org feedback sang M6; hoặc chốt mapping khác. | NFR-36 bao gồm access child media/profile và cross-role grants theo permission/reason/audit; M2-AT-07 chỉ phủ profile/grant trong scope M2. | M2-AT-07, M5 media và M6 feedback. | Không claim toàn NFR-36 PASS từ M2. |
| 10. NFR-38 / AC-65 disposition | Owner xác nhận PARTIAL cho M2 và mapping đề xuất AC-65 story sang M4, video sang M5; hoặc chốt mapping khác. | M2-AT-10 chỉ kiểm metadata locale/age; AC-65 còn age-band/context đã duyệt, Vietnamese content và video cá nhân hóa theo tranh trẻ. | M2-AT-10, M4 story và M5 video. | Mapping M4/M5 là đề xuất; không claim chất lượng AC-65 đã đạt. |

Các câu hỏi bổ sung chưa xác minh: age-band boundary/catalog và physical mapping; field/purpose/expiry của share; canonical route/method cho Parent invite/accept/revoke và Teacher profile; placeholder organization/org_id; cleanup sau DELETE_PENDING. NFR-36/NFR-38 disposition và mapping pha được ghi là quyết định owner đang chờ tại §9. Nếu chưa quyết thì deny hoặc hoãn surface liên quan.

## 10. Gói cần có trước launch

- Owner xác nhận dd70685eae58aaaefea3e567f5c23d09345a8513 là baseline tại §0/§9.8 và quyết định B0 provenance tại §9.7.
- Owner quyết các mục §9 ảnh hưởng đến pha được launch; lưu trong approval, gồm disposition PARTIAL cho NFR-36/NFR-38 và chốt hoặc sửa mapping M5/M6, M4/M5 đề xuất.
- Ghim plan hash, branch/HEAD, nguồn, snapshot manifest.
- Ghi exact file allowlist từng path, path mới, exclusions; không wildcard.
- Ghi DB task-owned identity, người tạo/chạy, dữ liệu, snapshot/restore và cleanup boundary.
- Ghi Alembic graph/target revision, offline plan/SQL review và command ceiling.
- Ghi test matrix/tầng test; route acceptance dùng PostgreSQL thật/wiring thật khi route là đối tượng.
- Ghi disposition B1 orphan, B2 OpenAPI/T12/T13/mypy conditions và mọi PARTIAL/NOT RUN. Safety check hiện NOT RUN; không có verdict nên dừng tại gate, không bypass bằng lệnh hoặc shell khác.
- Owner ghi Task Approval cho đúng subphase qua phiên điều phối. Approval một pha không mở pha khác, M3–M6 hoặc provider.

Cho tới khi các điều kiện này được ghi nhận, kế hoạch vẫn **DRAFT / AWAITING OWNER REVIEW**; M2 chưa launch và không có quyền sửa code, migration, DB hoặc gọi provider.
