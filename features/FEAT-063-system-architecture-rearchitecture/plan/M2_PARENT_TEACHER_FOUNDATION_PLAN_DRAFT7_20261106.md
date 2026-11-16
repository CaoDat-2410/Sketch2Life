# Kế hoạch M2 — Parent / Teacher Foundation (Draft 7)

**Feature:** FEAT-063 — System Architecture Rearchitecture  
**Ngày:** 2026-11-06  
**Trạng thái:** **DRAFT / AWAITING OWNER REVIEW**  
**Phạm vi:** Draft 7 xử lý bốn finding P3 còn mở theo review độc lập Draft 6, có kết luận ACCEPTED_WITH_CONDITIONS và 0 P1/P2. Kết luận đó chỉ áp dụng cho Draft 6; Draft 7 vẫn là artifact DRAFT / AWAITING OWNER REVIEW, chưa có independent review hoặc owner approval và không phê duyệt implementation, M2, M3–M6, DB, migration, provider, Modal hay workload.

## Thay đổi so với Draft 6

| ID | Finding review | Cách xử lý trong Draft 7 | Bác bỏ/không sửa |
|---|---|---|---|
| D7-1 | R6-1 (P3) — D6-2 chưa mô tả đúng cụm được giữ tại D5-8. | D6-2 nêu đúng cụm “safety check” chung ở D5-8 và nói rõ nội dung §5.3 của Draft 5 đã được thay bằng điều kiện tại §5.3 mục 2. | Không đổi hàng lịch sử D5-8; không gán cho hàng đó cụm “safety verdict” vốn không xuất hiện ở D5-8. |
| D7-2 | R6-2 (P3) — §0 thiếu tóm tắt các nhóm còn lại của diff ngoài StoryRun-lite. | §0 thêm một câu đếm path theo nhóm từ git diff --name-status 1e109b17 dd70685e. | Không thêm path vào allowlist §8, không đổi cột chỉ đọc/candidate; số đếm source-control không chứng minh code, migration, test hoặc deploy đã chạy. |
| D7-3 | R6-3 (P3) — §0 dùng lẫn đơn vị “byte”/“dòng” và hai dạng phân tách số. | §0 dùng “9 path đã nêu”, thống nhất số dòng diff thành 20,294 và chỉ mô tả git diff --name-status là inventory path; câu giới hạn chỉ nói path và số dòng. | Không suy ra byte từ name-status và không đổi các số liệu đã đóng 154 path, +20,294/−56 dòng, 5 file nhị phân, 414/0 cho năm hồ sơ governance. |
| D7-4 | R6-4 (P3) — vài câu lịch sử có thể bị hiểu nhầm là Draft 5 đang chờ review; §9.8 nêu sai đời tài liệu. | §0/§7/§8/§9.8 gọi Draft 7 là tài liệu hiện chờ review, ghi rõ các Draft 5/6 là lịch sử khi nhắc baseline, và ghi phạm vi kiểm tra chỉ đọc của phiên lập Draft 7. | Giữ các mốc Draft 5 mô tả đúng lịch sử; không đổi 10 quyết định owner còn mở, biến baseline confirmation thành approval, hoặc đổi trạng thái DRAFT. |

## Thay đổi so với Draft 5

| ID | Finding review | Cách xử lý trong Draft 6 | Bác bỏ/không sửa |
|---|---|---|---|
| D6-1 | F-A (P2) — §0 có thể bị hiểu là inventory đầy đủ dù chỉ nêu 9 path cho S2/S3. | §0 ghi rõ các path là TIÊU BIỂU/không đầy đủ; giữ 154 path và +20,294/−56 dòng (không phải byte), nêu các StoryRun-lite/Bruno paths bổ sung, 5 file nhị phân, lệnh lấy danh sách đầy đủ, và giới hạn rằng diff không chứng minh code/migration/test đã chạy. | Không thêm path vào allowlist §8, không đổi cột chỉ đọc/candidate. Việc thêm router/schema/photo bridge làm input chỉ đọc S2/S3 chỉ là đề xuất chờ owner/coordinator. |
| D6-2 | F-B (P3) — §5.3 còn yêu cầu một verdict an toàn mà không định nghĩa điều kiện. | §5.3 yêu cầu approval riêng ghi đích DB task-owned, command, SHA-256 script/snapshot và tiêu chí kết quả; vì chưa có các thông tin/approval này nên trạng thái là NOT RUN. Câu ở đoạn N-3 cũng không còn gọi các rerun chưa ghim hash là verdict. D5-8 chỉ giữ cụm “safety check” chung làm dấu vết lịch sử; câu mô tả §5.3 trong Draft 5 chưa đóng finding F-B và được thay bằng điều kiện ở §5.3 mục 2. | Offline-check ghi facts only, không có pass/fail; không suy ra verdict hoặc thay bằng lệnh/validator khác. |
| D6-3 | F-C (P3) — nhãn trên bảng D4-1…D4-9 bị trùng nhãn D3. | Đổi nhãn bảng D4 thành Draft 4 so với Draft 3; giữ bảng D3-1…D3-7 nguyên nội dung và thêm bảng D6 này. | Không sửa nội dung D3-1…D3-7 hoặc quyết định/allowlist khác. |

## Thay đổi của Draft 5 so với Draft 4 (giữ để truy vết)

| ID | Finding / điểm cần sửa | Cách xử lý trong Draft 5 | Giới hạn |
|---|---|---|---|
| D5-1 | P2-A — mô tả merge chỉ như 414 dòng governance không bao quát diff first-parent. | §0 ghi tổng diff 154 path, 20,294 dòng thêm và 56 dòng xóa; giữ riêng 414/0 cho đúng năm hồ sơ governance và nêu các nhóm byte đã đổi. | Diff là dữ liệu source-control; không cho biết code hoặc migration đã chạy. |
| D5-2 | P2-B — AT-08/09 chưa đặt đủ concurrency, process restart và trạng thái orphan/timeout. | §4.2 tách các kịch bản owner-lock/cancel/restart của AT-08 và success/timeout/orphan/recovery của FEAT-064 N-1 ở AT-09. | Không tự đặt status/error hoặc transition chưa có trong contract/owner decision. |
| D5-3 | P2-C — route AT-06/07 và FR-PL mapping còn gộp hoặc có thể bị hiểu là đã canonical. | §4 và §4.2 giới hạn FR-PL-08 ở AT-06; AT-06/07 route phụ thuộc canonical route được owner chọn. | Chưa chọn route thì chỉ domain/service acceptance có thể được xét; S1b route gate vẫn mở. |
| D5-4 | P2-D — AT-04A gộp capacity với quyền actor. | §4.2 tách case capacity của Admin khỏi Teacher gọi route Admin; chỉ dùng mã capacity nếu contract định nghĩa. | Không suy diễn error capacity thành error authorization. |
| D5-5 | P2-E — OI-05..08 được trích từ bản SRS cũ mà thiếu đối chiếu hiện hành. | §1.4 và §9 trỏ rõ SRS hiện hành §29.2; giữ nguyên các quyết định privacy, retention, region/cross-border và production/ops ở trạng thái mở. | Không cấp consent, dữ liệu thật hoặc production authority. |
| D5-6 | P2-F — chênh B0 hash được diễn đạt như vấn đề chưa phân loại. | §1.4 phân biệt normalization evidence, các loại whitespace/line ending, hash bytes và giới hạn không có original bytes để đối chiếu. | Không gọi đây là contradiction đã chứng minh; authority vẫn do owner quyết định. |
| D5-7 | P2-G — migration/downgrade chưa nêu state constraint và bảng review hiện có. | §5.2–5.3 ghi rõ state mới, bảng vật lý có sẵn, bảng mới và giới hạn rollback suy ra từ source. | Static source reading; không phải kết quả chạy migration hoặc downgrade. |
| D5-8 | P2-H — “safety check” chung tạo stop gate không định danh. | §3, §5.3, §7 và §10 nêu đúng evidence/command nào NOT RUN và không dùng nhãn safety check chung. | Không thay một verdict đang thiếu bằng lệnh khác. |
| D5-9 | P2-I — N-1 và BR-58 có nguy cơ gán sai requirement hoặc phase. | §4/§4.2 phân biệt FEAT-064 N-1 với FR-PL-08; BR-58 trỏ SRS §30.4 và giữ audience đầy đủ ở M6. | Không đổi owner mapping hoặc mở M6. |
| D5-10 | Provenance review và owner choices cần được bảo toàn. | §0, §1.4, §8 và §9 nêu phạm vi xác minh của phiên này, giữ đủ 10 owner choices và các pin/limits hiện có. | Draft 5 chưa có review verdict, owner decision hay implementation approval. |

## Thay đổi của Draft 4 so với Draft 3 (giữ để truy vết)

| ID | Finding review | Cách xử lý và vị trí | Bác bỏ/không sửa |
|---|---|---|---|
| D4-1 | P1-1 — HEAD Draft 3 và pin governance cũ làm S0-doc dừng trên checkout hiện tại. | Draft 4 đã ghi chuỗi HEAD b6dbfa68… → 1e109b17… → dd70685e… và ghi nhầm tổng tác động merge là 414/0 từ năm hồ sơ governance; Draft 5 sửa phạm vi này tại §0 và giữ 414/0 chỉ cho năm hồ sơ. | Không hợp thức hóa mismatch cũ; owner xác nhận baseline vẫn đang chờ. |
| D4-2 | P1-2 — allowlist thiếu core_models.py, migration Story revisions và offline-check; StoryRun-lite/DTR chưa phản ánh migration mới. | §1.3–1.4, §5.1–5.3 và §8 ghim/đọc đúng ba nguồn, ghi ancestry revision/down_revision/branch_labels/depends_on, phân biệt Core hiện có với Parent module chưa có, và nêu khác biệt vật lý–logic cần owner đối chiếu. | Không coi migration đã chạy; không coi log offline là verdict hoặc graph hiện tại. |
| D4-3 | P2-1 — M2-AT-07 chỉ phủ một phần NFR-36. | §3, §4, §4.2 và §7 bắt buộc owner ghi disposition PARTIAL; M2 chỉ xét access profile/grant trong scope được duyệt, media access đề xuất M5, cross-org feedback đề xuất M6. | Không claim toàn NFR-36 PASS từ M2-AT-07. |
| D4-4 | P2-2 — M2-AT-04 gộp hai actor và hai thao tác. | §3, §4 và §4.2 tách M2-AT-04A cho Admin tổ chức tạo class/assignment và M2-AT-04B cho Teacher được phân công tạo profile/enrollment; mỗi test nêu route, allow và deny theo SRS §21.2. | Giữ các route SRS hiện có; không thêm route hoặc quyền actor. |
| D4-5 | P2-3 — request/cancel qua route thật và bất biến D-127 chưa đủ rõ trước N-1. | §4.2, §6.1, §6.3 và §7 yêu cầu test route request lẫn cancel, trạng thái DELETE_PENDING, nhả active-owner nhưng giữ result/assets/receipts; N-1 là test PostgreSQL route với wiring thật trước khi thoát S2 và trước D9/client integration. | Không thay route test bằng unit/repository test hoặc test có monkeypatch. |
| D4-6 | P2-4 — điều kiện B2 và N-3 chưa phản ánh đúng approval FEAT-064. | §3, §5.3, §6.3, §7 và §10 ghi B2 được owner chấp nhận ACCEPTED_WITH_CONDITIONS trong scope T9/T13/T12 hẹp; N-3 về runner rerun bốn suite không ghim hash và runner đối soát hiện không còn trong thư mục script. | Không mở rộng điều kiện B2 sang M2; không xem T12 là toàn graph hoặc DB đã được xác minh độc lập. |
| D4-7 | P2-5 — OWNER_MODAL_CALL_APPROVED=NO chưa rõ phạm vi. | §0, §2.2, §6.3, §7 và §10 nói rõ approval POC/retest Modal sau merge có phạm vi riêng, không cấp phép M2 hay bật workload. | Không suy ra quyền gọi Modal/provider từ approval của task khác. |
| D4-8 | P2-6 — phân NFR-38 cho M2 là suy luận từ profile/age, AC-65 rộng hơn. | §2.3, §4, §4.2, §7 và §9 giữ giới hạn metadata tuổi/ngôn ngữ ở M2; mô tả AC-65 đủ nghĩa; M4 cho story và M5 cho video là phân bổ đề xuất cần owner xác nhận. | Không biến mapping roadmap thành quyết định owner hoặc claim chất lượng sư phạm. |
| D4-9 | Draft 4 ghi nhận các điểm được báo cáo là đã xác nhận đạt. | Draft 4 báo cáo 49 path đã tồn tại và ghi nhận các review points tại §1, §4, §4.1, §5, §6 và §8. Draft 5 không kiểm lại toàn bộ 49 path hoặc độc lập xác nhận verdict review đó; các giới hạn source/evidence liên quan được làm rõ ở §1.4 và §8. | Không thêm owner decision hoặc review verdict mới. |

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

Trong lịch sử, Draft 5 được lập trên branch feature/feat063-be-foundation, HEAD dd70685eae58aaaefea3e567f5c23d09345a8513. HEAD có first parent 1e109b1726f327ac9383457b0dbdd535ef5c6518 và second parent fb834771c24957bb8e289fb95d21410b14181e57. Chuỗi lịch sử ghi nhận trong Draft 4 là b6dbfa68e66718f3f40902c093e9ebd634b1ebb9 → 1e109b1726f327ac9383457b0dbdd535ef5c6518 → dd70685eae58aaaefea3e567f5c23d09345a8513.

Trước khi tạo Draft 5, index rỗng và working tree có đúng bốn path untracked: Draft 1–4. Hash trước khi ghi: Draft 1 F47393FD1028B20D841114786E7D07B12BC8C89A67EF6697F0396EFCA7942E81; Draft 2 A09F7E6BF8534E85EE4EE4573209B5346861008AA4A5C4A8C907CF4EFEDCFE66; Draft 3 A6F8CE23DA3650B38FF7E13BAF9052371B1655BE400BB6D5F9053A5D5E2C638D; Draft 4 A31DCEA8DBEF0CF9E59FC7E9F3346C35B1F278DC1D6AAB3E992B436E1590FEEC. Branch, HEAD, parent commits, empty index, bốn path untracked và cả 17 hash nguồn được ghim tại §1 đều khớp trước khi ghi file này. Draft 1–4 là đầu vào chỉ đọc. Git status đồng thời phát sinh warning rằng user-level global ignore config không đọc được; không dùng warning đó để khẳng định path nào cụ thể bị ảnh hưởng.
Trước khi tạo Draft 6 tại features/FEAT-063-system-architecture-rearchitecture/plan/M2_PARENT_TEACHER_FOUNDATION_PLAN_DRAFT6_20261106.md, index rỗng, tracked worktree diff rỗng và đúng năm file Draft 1–5 là untracked. Hash pre-edit: Draft 1 F47393FD1028B20D841114786E7D07B12BC8C89A67EF6697F0396EFCA7942E81; Draft 2 A09F7E6BF8534E85EE4EE4573209B5346861008AA4A5C4A8C907CF4EFEDCFE66; Draft 3 A6F8CE23DA3650B38FF7E13BAF9052371B1655BE400BB6D5F9053A5D5E2C638D; Draft 4 A31DCEA8DBEF0CF9E59FC7E9F3346C35B1F278DC1D6AAB3E992B436E1590FEEC; Draft 5 B1C39C63314274137699F06B219C531E92BE0727D6120D7F06445F9C326283D7. Các hash này là baseline của file đầu vào, không thay thế owner review. Git status đồng thời phát warning user-level global-ignore config bị Permission Denied; đây là warning riêng, không chứng minh path repo nào bị ảnh hưởng. Báo cáo cũ về backend/.pytest-phase8-precommit/ là từ reviewer trước; lần status này không phát warning cho path đó.

Trước khi lập Draft 7, branch feature/feat063-be-foundation ở HEAD dd70685eae58aaaefea3e567f5c23d09345a8513 với hai parent 1e109b1726f327ac9383457b0dbdd535ef5c6518 và fb834771c24957bb8e289fb95d21410b14181e57; index rỗng, working tree chỉ có Draft 1–6 untracked. Draft 7 được lập từ bản sao chỉ đọc Draft 6, SHA-256 C836A72A84D5EED70427CC69540050852D54C83D94745DAFEF02A0A0704FD537; cả 17 nguồn ở §1.1–§1.3 đã re-hash trong phiên này và khớp pin. Draft 1–6 không bị sửa.
Phiên lập Draft 7 chỉ đọc tài liệu/metadata, kiểm tra hash và Git, rồi đếm path bằng git diff --name-status; không chạy Alembic, DB, mypy hay test. Git status cảnh báo không đọc được user-level global ignore config; cảnh báo riêng theo thông tin đầu vào rằng backend/.pytest-phase8-precommit/ không đọc được cũng được ghi nhận, không xem là lỗi kế hoạch.

### Tác động của merge

Diff first-parent của merge HEAD dd70685e… so với 1e109b17… gồm 154 path, 20,294 dòng thêm và 56 dòng xóa trên toàn bộ merge. Năm hồ sơ governance dưới đây là một tập con của diff:

| Hồ sơ governance | Thêm | Xóa |
|---|---:|---:|
| CONTEXT.md | 72 | 0 |
| DECISIONS.md | 36 | 0 |
| SOURCE_REGISTER.md | 42 | 0 |
| approvals/TASK_APPROVAL.md | 190 | 0 |
| status/STATUS.md | 74 | 0 |
| Tổng năm hồ sơ | 414 | 0 |

Đếm từ git diff --name-status 1e109b17 dd70685e: 120 path dưới features/FEAT-063-system-architecture-rearchitecture, 12 dưới backend/src, 11 dưới deployment/modal, 6 dưới backend/tests, 1 dưới backend/alembic, 3 file backend gốc (Dockerfile, pyproject.toml, uv.lock) và 1 dưới docs; tổng cộng 154 path.

Các nhóm/path dưới đây là TIÊU BIỂU, KHÔNG ĐẦY ĐỦ cho diff 154 path. Năm hồ sơ governance ở trên và 9 path đã nêu cho S2/S3 là các tập con; số +20,294/−56 là số dòng diff, không phải byte. Những 9 path đã nêu làm read-only inputs cho §5.2–5.3/S2 (backend/alembic/versions/20261104_story_revisions.py, backend/src/sketch2life/domain/story_run_lite.py, backend/src/sketch2life/application/services/story_run_lite.py, backend/src/sketch2life/infrastructure/story_run_lite/repository.py, backend/src/sketch2life/infrastructure/story_run_lite/tables.py, backend/tests/integration/test_story_run_lite_postgres.py) và §4/S3 (backend/src/sketch2life/contracts/schemas/story_run_lite.py, backend/src/sketch2life/interfaces/http/story_run_lite_openapi.json, backend/tests/contract/test_story_run_lite_api.py).

Diff name-status cũng cho thấy StoryRun-lite paths chưa nêu trong nhóm 9 path trên: backend/src/sketch2life/application/ports/story_run_lite.py; backend/src/sketch2life/infrastructure/story_run_lite/composition.py; backend/src/sketch2life/infrastructure/story_run_lite/photo_bridge.py; backend/src/sketch2life/interfaces/http/routers/story_run_lite.py; backend/src/sketch2life/contracts/schemas/ai_story.py (file mới); backend/tests/integration/test_story_run_lite_loopback.py; backend/tests/unit/test_ai_story_contracts.py (file mới); backend/tests/unit/test_modal_story_function_client.py (file mới); backend/tests/unit/test_story_run_lite_photo_bridge.py; features/FEAT-063-system-architecture-rearchitecture/artifacts/storyrun-lite/openapi.json; và các Bruno files dưới features/FEAT-063-system-architecture-rearchitecture/artifacts/storyrun-lite/bruno/ (environments/local.bru, requests/01-create-run.bru, requests/11-generate-story-revision.bru, requests/12-get-story-revision.bru, requests/13-confirm-story-revision.bru). Đây chỉ là inventory mô tả diff ở §0, không phải bổ sung vào allowlist §8. Đề xuất chờ owner/coordinator: nếu cần, xem xét riêng routers/story_run_lite.py, schemas/ai_story.py và photo_bridge.py làm input chỉ đọc S2/S3; Draft 6 không thêm chúng vào allowlist.

Năm file nhị phân trong evidence/assets là synthetic_vietnamese_narration.wav, drawing_vlm_synthetic_butterfly.png, flux2_klein_synthetic_butterfly_guide.png, vieneu_synthetic_narration.wav và synthetic_childlike_butterfly.png.

Lấy inventory path đầy đủ bằng git diff --name-status 1e109b17 dd70685e. Diff/source-control chỉ cho biết path và số dòng thay đổi; nó không chứng minh code, migration hoặc test đã chạy.

Các bản ghi mới liên quan gồm:

- D-139: giữ nguyên kết quả Parent AI mơ hồ; không retry hoặc coi là thành công; probe story tách rời không phải Parent API end-to-end.
- D-140: phân biệt manifest story với drawing; lỗi contract đã biết là terminal, outcome unknown không retry; activity Parent sau video; Teacher Deck/lesson visuals còn DRAFT và chịu gate SRS.
- D-141: owner cho phép một đợt retest non-video synthetic riêng, có retry fence và thời hạn chờ; thêm POC ảnh SAM2.1; không promotion, không bật workload, không video.
- Mục Merge reconciliation for decision IDs: dải D-127..D-135 trên nhánh Modal được đổi thành D-133..D-141 do trùng ID; mục D-120 trùng nội dung với D-131 không lặp lại.
- Các approval/retest Modal riêng gồm scaffold; drawing VLM L4 POC và corrective retry; hosting wave; API availability smoke; backend-to-Modal drawing slice; Parent image-to-script và generated-image/story/activity retest; AI flow/Teacher Deck POC; full non-video retest. Phạm vi, kết quả và giới hạn mỗi việc chỉ áp dụng cho plan/evidence của việc đó. Chúng không phê duyệt M2, không bật workload và không cấp quyền Modal/provider cho kế hoạch này.

Draft 4 đã yêu cầu owner xác nhận dd70685eae58aaaefea3e567f5c23d09345a8513 làm baseline. Draft 5 (bản lịch sử) ghi nhận cùng checkout và pin source hiện tại tại §1, nhưng việc hash khớp không phải owner confirmation. Owner vẫn cần xác nhận HEAD này làm baseline review trước khi kế hoạch được chấp nhận hoặc dùng làm căn cứ cho phase kế tiếp.

Tài liệu này chỉ là kế hoạch DRAFT. Không có quyền implementation, migration, thao tác DB, provider, Modal, tích hợp frontend hoặc M3–M6. B2 được owner chấp nhận có điều kiện trong FEAT-064, đúng giới hạn ở §6.3; điều đó không phải approval M2. OWNER_MODAL_CALL_APPROVED=NO áp dụng cho mọi Modal/live call ngoài approval riêng có phạm vi riêng; approval POC/retest sau merge không cho phép triển khai M2 hay bật workload.

## 1. Căn cứ và pin nguồn

Các SHA-256 kế thừa từ Draft 4 đã được re-hash trên working copy trước khi tạo Draft 5; cả 17 pin khớp. Không chuẩn hóa bytes để làm khớp pin. Các Draft 1–4 được giữ nguyên.
Draft 6 dùng Draft 5 làm nền chỉ đọc; SHA-256 Draft 5 là B1C39C63314274137699F06B219C531E92BE0727D6120D7F06445F9C326283D7. Trước khi tạo Draft 6, cả 17 nguồn liệt kê tại §1 đã được re-hash và khớp đúng các giá trị pin bên dưới. Điều này chỉ xác nhận bytes đã quan sát, không phải owner approval.

Draft 7 dùng Draft 6 làm nền chỉ đọc, SHA-256 C836A72A84D5EED70427CC69540050852D54C83D94745DAFEF02A0A0704FD537. Trong phiên này, 17 nguồn liệt kê tại §1.1–§1.3 được re-hash và đều khớp các pin; đây chỉ xác nhận bytes đã quan sát, không phải owner approval.

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

- Draft 6 ghi nhận đã đọc AGENTS.md, .codex/sketch2life-harness.md, FEAT-063 CONTEXT.md, SOURCE_REGISTER.md, DECISIONS.md, STATUS.md, TASK_APPROVAL.md, roadmap, backlog, SRS, DTR, evidence normalization, FEAT-064 A2/B2 records, StoryRun-lite/Core models và migrations liên quan. Phiên lập Draft 7 re-hash 17 pin tại §1.1–§1.3; hash Draft 6 và nguồn khớp trước khi ghi.
- D-132 chấp nhận roadmap sáu mốc làm baseline lập kế hoạch. SRS v2.3-draft chưa ký; route matrix chưa phải OpenAPI cuối.
- DTR mô tả ownership logic, không xác nhận schema vật lý. core_models.py là module Core hiện có; không tìm thấy module persistence Parent trong source tree được rà. Parent tables trong DTR vẫn là mô hình logic, không phải bằng chứng implementation.
- B0 plan hiện có hash 773C4A8340C8E33AE39764D920B042AC19BACBAF6DC561FE9D5D3DFFCC4B5A5A; hồ sơ duyệt ghi bytes gốc hash 03AEA386B8545624100688B68AA828A84CD154B47857CB5E98FB06354D6BB582. Evidence normalization tại §1.1 quy provenance cho trailing whitespace, final blank lines và line endings; original bytes trong snapshot git-ignore không có trong repo đã rà và không được xác minh trong phiên này. Hai hash bytes khác nhau không tự chứng minh khác biệt ngữ nghĩa. Source register ghi nội dung không chỉ khác line ending; điều đó có thể đồng thời đúng với việc normalization evidence nêu thêm whitespace cuối dòng/blank lines, nên hiện chưa chứng minh được contradiction. Owner vẫn quyết định authority/tương đương.
- OI-05..08 hiện được ghi tại SRS §29.2, dòng 1130–1133. Chúng để mở các câu hỏi về chuyên gia/privacy, retention/backup, region/cross-border và production/operations; chưa có authority cho consent hoặc dữ liệu thật. Các lựa chọn giữ mở tại §9.
- Route share Parent, schema vật lý Parent, catalog tuổi và một số owner columns chưa được đóng; đánh dấu chưa xác minh.
- Migration 20261104_story_revisions.py hiện có trong source và được ghim riêng ở §1.3; pin nguồn chứng minh file bytes, không chứng minh migration đã chạy.
- Offline-check ghi rõ không có DB connection, network hay migration execution, và kết thúc bằng facts only; not a pass/fail verdict. Danh sách script_heads trong file kết thúc ở 20261103_story_upload_compat, không chứa migration mới 20261104_story_revisions; do đó log này không phải graph/head evidence cho checkout hiện tại và không được tính là PASS.
- M1 là demo synthetic local. M1/A2/B1/B2 không cấp quyền cho M2.
- Review Draft 3 được báo cáo ngoài repository; không có artifact/hash pinned ở đây nên verdict không được phiên này xác minh độc lập. Reviewer trước đó báo cáo permission denied khi đọc .pytest-phase8-precommit. Phiên Draft 5 thấy bốn Draft 1–4 untracked cùng warning riêng về user-level global ignore config; không có căn cứ nói path .pytest-phase8-precommit được tái kiểm tra hoặc kiểm kê toàn bộ path không đọc được.
- PostgreSQL details ở FEAT-064 là owner-run; B0 original bytes và các canonical Parent share/Teacher routes không được xác minh độc lập trong phiên tài liệu này. Phiên lập Draft 5 (lịch sử) chỉ cập nhật plan; không chạy validation, owner-run command, test, DB, migration, provider hoặc network action.

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
| S0-owner-run | S0-doc đóng; owner chọn DB và ghi approval riêng | Owner-run chỉ đọc để đối soát schema vật lý/Alembic và ghi mypy baseline theo command/hash được duyệt. | DB identity khớp manifest; bảng/version/chênh lệch current source được ghi; baseline mypy có output thật, không suy diễn phần chưa chạy. | Chưa có command/output owner-run được chỉ định và duyệt thì không ghi verdict đối soát schema hoặc mypy; chỉ lưu trạng thái NOT RUN và giữ pha bị chặn. Không chạy lệnh thay thế. Sai identity, dữ liệu không synthetic hoặc cần write/migration thì dừng. Pha này không cấp phép migration. |
| S1a identity/tenant/profile/age | S0-doc và S0-owner-run đóng (route/persistence acceptance cần PostgreSQL thật; unit/doc chỉ chạy trước nếu approval tách riêng) | Identity/role assignment, tenant isolation, profile ownership và age provenance. | M2-AT-01/02/03/04A/04B/10 đạt theo tầng đã duyệt; route test persistence dùng PostgreSQL thật và wiring thật. | Thiếu role matrix, profile owner hoặc age policy thì deny-by-default; không tự tạo route/policy. |
| S1b grant/revoke/consent | S1a; owner quyết định 3; OI gate đã xác định | Scoped grant/revoke, purpose/expiry/audit và consent/data authorization trong scope được chọn; NFR-36 M2 chỉ PARTIAL. | M2-AT-05/06/07 đạt trong scope được duyệt; owner ghi PARTIAL cho NFR-36 và disposition các phần hoãn; thiếu, pending, revoked hoặc expired đều deny. Nếu B4b hoãn thì REAL và LEGACY_UNCLASSIFIED bị từ chối; không claim consent production-ready. | OI mapping, purpose, fields, expiry, admin scope/reason/audit policy hoặc disposition chưa chốt thì không bật share/consent. |
| S2 owner/job/asset/revision/lifecycle | S1a; S1b nếu bật; migration target đã duyệt | Durable owner/scope refs, job/asset/revision, AiJobService mapping, idempotency/replay, cancel, restart/recovery, DELETE_PENDING/D-127. | M2-AT-08/09 đạt. N-1 phải test PostgreSQL mức route cho request → job → status, gồm request VÀ cancel qua route thật với wiring thật, không monkeypatch/override dependency; đạt trước khi thoát S2 và trước D9/client integration. B1 orphan có invalidation/reconciliation/read-exposure contract và regression trước dữ liệu non-synthetic/provider. | Orphan có thể được đọc/công bố như accepted result, job/aggregate lệch hoặc thiếu N-1 thì chưa thoát S2; evidence NOT RUN không đóng gate. |
| S3 freeze và đóng M2 | S1a, S1b theo disposition, S2 | Đối chiếu evidence và freeze contract; đóng OpenAPI P3 hai POST submit/cancel trước frontend/client. | Tất cả M2-AT pass hoặc PARTIAL disposition được owner ghi; NFR-36 và NFR-38 có disposition; OpenAPI parity được kiểm; conditions được gán owner/phase; independent review ACCEPTED. | Không tích hợp frontend/client khi OpenAPI P3 còn mở; không tự mở M3 hoặc bật workload. |

## 4. Traceability requirement → route/API → bảng → owner → acceptance

Route là candidate theo SRS v2.3-draft, chưa freeze. “SRS §21.2” nghĩa là path có trong route table; “suy luận” là mapping chưa gắn trực tiếp; “chưa xác minh” là chưa có route canonical.

| Requirement | Route/API và nguồn | Bảng/owner logic theo DTR | Acceptance |
|---|---|---|---|
| FR-PL-01 | POST /v1/parent/profiles; GET/PATCH /v1/parent/profiles/{profile_id} — SRS §21.2. Identity endpoint — chưa xác minh. | parent.child_profiles, parent.profile_share_grants; be1.adult_identities, be1.organization_assignments; core audit — Parent/BE1/Core. | M2-AT-01/05. |
| FR-PL-02 | POST /v1/organizations/{org_id}/classes và POST /v1/classes/{class_id}/assignments — Actor Admin tổ chức; POST /v1/classes/{class_id}/profiles — Teacher được phân công; SRS §21.2. List/read routes chưa xác minh. | be1.organizations, classrooms, organization_assignments, enrollments — BE1; consumer scope thuộc owner tương ứng. | M2-AT-02/04A/04B. |
| FR-PL-07 | Parent profile POST/GET/PATCH là SRS §21.2, không phải grant. Invite/accept/revoke route — chưa xác minh. | parent.profile_share_grants, parent.child_profiles, parent.data_authorizations; be1.managed_profiles — Parent/BE1. | M2-AT-05. |
| FR-PL-08 | Profile GET/PATCH và POST /v1/story-runs — SRS §21.2. Grant/download/token/cache/revoke route — chưa xác minh. | parent.profile_share_grants, core.asset_lineage — Parent/Core. | M2-AT-06. AT-09 là gate N-1 của FEAT-064, không phải acceptance FR-PL-08. |
| FR-PL-25 | Parent profile POST/GET/PATCH và POST /v1/classes/{class_id}/profiles — SRS §21.2. Age-band catalog route — chưa xác minh. | parent.profile_revisions, be1.profile_revisions, age-band catalog — Parent/BE1/catalog owner chưa xác minh. | M2-AT-03/10. |
| BR-48 | Profile route không phải share route. Parent share invite/accept/revoke — chưa xác minh. | parent.profile_share_grants, parent.data_authorizations — Parent. | M2-AT-05/06; thiếu grant phải deny. |
| BR-49 | POST /v1/organizations/{org_id}/classes; POST /v1/classes/{class_id}/assignments; POST /v1/classes/{class_id}/profiles — SRS §21.2, actor Admin cho hai route đầu và Teacher được phân công cho route profile. | be1.organizations, classrooms, organization_assignments, enrollments — BE1. | M2-AT-01/02/04A/04B. |
| BR-57 | Age qua profile routes SRS §21.2; catalog/version route — chưa xác minh. | Profile revisions, age-band catalog — Parent/BE1/catalog owner chưa xác minh. | M2-AT-03/10. |
| BR-58 | SRS §30.4 map BR-58 với FR-PL-06/FR-PL-23; SRS §31.8.1 mô tả audience là nhóm Parent hoặc invitee cụ thể có thể thu hồi. Assignment/profile route §21.2 không chứng minh lesson audience. | be1.parent_groups/parent_group_members (BE1); lesson.access_grants (Lesson); primitive M2 dùng parent.profile_share_grants. | M2: chỉ primitive grant/revoke có thể thu hồi qua M2-AT-05/06 (S1b). M6: audience nhóm/invitee đầy đủ; BR-58 PARTIAL trong M2. |
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

Các test dưới đây là kế hoạch, chưa chạy. Route acceptance phải dùng PostgreSQL task-owned, app composition, authentication và dependency wiring thật. Không monkeypatch _build_child_binding hoặc override dependency cần kiểm. Nếu canonical route chưa được owner chọn/duyệt, chỉ domain/service acceptance có thể được xét; route acceptance chưa chạy và gate S1b còn mở. AT-09 là crosswalk FEAT-064 N-1, không phải acceptance FR-PL-08.

| ID | Requirement/pha | Given / When / Then | Tầng | DB task-owned |
|---|---|---|---|---|
| M2-AT-01 | FR-PL-01, BR-49, NFR-34; S1a | Given Parent/Teacher/Admin có role/assignment hợp lệ hoặc thiếu/thu hồi; when đọc/ghi resource; then chỉ role/scope hợp lệ được phép, denial không lộ metadata ngoài scope, audit metadata-only. | Domain/service unit, HTTP contract, route PostgreSQL. | Có cho route/persistence; không cho unit. |
| M2-AT-02 | FR-PL-02, BR-49; S1a | Given hai organization; when principal tenant A truy cập resource tenant B; then deny theo contract, không lộ existence/content. | Unit matrix và route integration wiring thật. | Có cho integration. |
| M2-AT-03 | FR-PL-25, BR-57; S1a | Given tuổi 36/120, ngoài biên, provenance/version; when tạo và đọc profile revision; then áp dải owner chốt, giữ provenance và không suy ra band chưa định nghĩa. | Domain/contract unit và repository integration. | Có cho persistence. |
| M2-AT-04A | FR-PL-02, BR-49; S1a; SRS §21.2 | Given Admin tổ chức thuộc đúng org và còn capacity cùng một Teacher active; when POST /v1/organizations/{org_id}/classes rồi POST /v1/classes/{class_id}/assignments; then class và assignment được tạo theo response contract. Given capacity hết; when Admin gửi POST tạo class; then không tạo class/assignment; chỉ kỳ vọng CLASS_CAPACITY_REACHED nếu contract hiện hành định nghĩa mã này. Tách riêng: Given Teacher gọi route Admin để tạo assignment; when gửi request; then authorization deny và không tạo assignment; không gán mã capacity cho lỗi quyền. | Route PostgreSQL acceptance với actor đã xác thực và wiring thật. | Có. |
| M2-AT-04B | FR-PL-02, BR-49; S1a; SRS §21.2 | Given Teacher được phân công vào class cùng tenant và expected class revision hiện tại; when POST /v1/classes/{class_id}/profiles với trường profile có cấu trúc; then tạo 201 profile/enrollment ref và tối đa một enrollment active. Given Teacher không được phân công, sai tenant hoặc Admin gọi route Teacher; when gửi command; then deny theo error envelope, không tạo profile/enrollment và không lộ dữ liệu ngoài scope. | Route PostgreSQL acceptance với actor Teacher đã xác thực và wiring thật. | Có. |
| M2-AT-05 | FR-PL-07, BR-48, BR-58 (primitive thu hồi được); S1b | Given grant pending/active/revoked/expired với purpose/scope; when đọc profile; then chỉ grant active đúng scope cho phép. Nếu canonical route chưa chốt, chỉ test domain/service và S1b chưa đóng. | Unit trước; route PostgreSQL sau khi route được duyệt. | Có cho route/persistence. |
| M2-AT-06 | FR-PL-08, BR-48, BR-58 (primitive thu hồi được), NFR-34; S1b | Given field-scoped grant liên kết asset/token/cache/job; when revoke; then lần đọc/tải mới, token/cache access và job chưa accepted bị chặn, audit không ghi content/token. Route acceptance chỉ sau khi canonical grant/revoke route được owner chọn và duyệt; nếu chưa có thì domain/service only và S1b vẫn mở. | Domain/service; API/asset/job integration sau route approval; không gọi provider. | Có cho persistence/route. |
| M2-AT-07 | NFR-36; thoát S1b, đối chiếu S3 | Given Admin thiếu permission, scope hoặc reason code; when gọi operation profile/grant thuộc M2; then deny và không lộ resource. Given permission/scope/reason hợp lệ theo policy owner đã duyệt; when gọi operation; then chỉ scope được cấp được phép và audit metadata-only. Media access và cross-org feedback không được tính vào test M2; chúng cần disposition PARTIAL và phase riêng. Route acceptance chỉ sau khi canonical operation được owner chọn và duyệt; nếu chưa có thì domain/service only, route check chưa chạy và S1b vẫn mở. | Domain/service; route PostgreSQL integration sau khi route/policy được owner duyệt. | Có cho persistence/route. |
| M2-AT-08 | Roadmap Mốc 2 (owner-lock, cancel, restart, ownership của job), D-127, NFR-34 — nguồn roadmap/decision, không phải FR-PL; S2 | Given synthetic Parent/Teacher cùng owner lock có quyền hợp lệ; when concurrent separate POST /v1/story-runs requests submit cùng active owner; then có không hơn một active run/job/receipt hoặc side effect; không áp đặt loser status/error nếu contract chưa định nghĩa. Given run qua PREPARATION_REVIEW; when POST /v1/story-runs/{id}/cancel; then áp dụng D-127: DELETE_PENDING, nhả active-owner trong transaction, giữ result/assets/receipts và không coi là đã xóa. Replay/cancel lặp không tạo side effect trùng. Sau đó dừng tiến trình hệ điều hành thật, khởi động process mới với app composition mới trên cùng DB; recovery không tạo duplicate và stale result không được accepted. Recreate object trong cùng process không tính là restart. | PostgreSQL integration qua route, process stop/start thực, composition/repository/wiring thật. | Có. |
| M2-AT-09 | FEAT-064 N-1 route crosswalk; S2 (không phải FR-PL-08) | Given child request tổng hợp và actor/device hợp lệ; when POST /api/be1/v1/assistance-requests, GET /api/be1/v1/organizations/{organization_id}/sessions/{session_id}/assistance-requests/{assistance_id}/status và POST /api/be1/v1/assistance-requests/{assistance_id}/cancel đi qua route thật; then auth, app composition, dependency wiring và PostgreSQL đều thật, không monkeypatch _build_child_binding hoặc override dependency cần kiểm. Bao phủ các trạng thái: success chỉ được expose sau durable committed SUCCEEDED; timeout phải giữ durable request/job/receipt facts nhưng không có authoritative successful result, không tự định nghĩa transition; orphan theo FEAT-064 approval là analysis invocation SUCCEEDED trong khi job RUNNING, không có result ref hoặc authoritative receipt, nên API/status không expose accepted. Dừng process hệ điều hành thật, khởi động app process mới cùng DB và kiểm tra recovery/status không công bố stale/orphan result như accepted. Timeout/recovery/terminal semantics chưa có owner quyết định thì giữ gate mở, không bịa status/error. Bắt buộc trước khi thoát S2 và trước D9 hoặc frontend/client integration. | PostgreSQL route integration qua real app composition/auth/dependency wiring và process restart. | Có, bắt buộc. |
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

- Source StoryRun-lite hiện có physical story.runs. Baseline đã cho phép DELETE_PENDING và FAILED; migration 20261104_story_revisions thêm child_age_months nullable với check 36–120 và mở rộng run_state cho SCRIPT_GENERATING, SCRIPT_GENERATION_UNKNOWN, SCRIPT_REVIEW và VIDEO_ADMISSION_PENDING. DELETE_PENDING/FAILED không phải các state mới do migration này thêm. Đây là static source mapping, không phải bằng chứng migration đã chạy.
- DTR mô tả logic story.runs với story_run_id, profile/owner refs và current_story_revision_ref; StoryRun-lite hiện dùng cột physical run_id. Giữ mapping run_id → story_run_id là crosswalk cần owner/chủ schema đối chiếu, không tự đổi tên hay giả định dữ liệu đã chuyển.
- Source tables.py đã khai báo physical story.review_decisions. Migration 20261104_story_revisions tạo physical story.story_revisions, story.story_scenes và story.story_revision_reviews; bảng mới story_revision_reviews khác với story.review_decisions đã có. DTR mô tả logic revisions/scenes/review_decisions; field/key/owner mapping với các bảng physical chưa được chứng minh tương đương. S0-doc phải lập crosswalk và đánh dấu unknown đến khi owner duyệt.
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

Migration 20261104_story_revisions nối sau 20261103_story_upload_compat; theo source, nó thêm tuổi vào run, mở rộng state constraint/receipt operation và tạo bảng revision/scene/review mới nêu ở §5.2. Đây là diff source-level; migration không được thực thi trong task tài liệu. Theo source, downgrade khôi phục state check hẹp hơn. Nếu row còn dùng state mới được chấp nhận, việc khôi phục constraint có thể thất bại; không chạy downgrade và không khẳng định runtime outcome. Đây là giới hạn rollback từ source, không phải execution evidence.

Offline-check owner-run được ghim tại §1.3 ghi upgrade plan 27 bước từ DB rỗng và 9 hàng version/9 script_heads khớp nhau tại thời điểm log; log ghi không có DB connection, network hoặc migration execution. script_heads trong log kết thúc ở 20261103_story_upload_compat và không có 20261104_story_revisions, nên đây là facts lịch sử, không phải graph hiện tại hoặc bằng chứng migration đã chạy. Phiên lập Draft 5 (lịch sử) không chạy Alembic, không kết nối DB và không chạy mypy; migration execution, graph đối soát live và M2 mypy baseline đều NOT RUN. Không thay các kết quả còn thiếu bằng lệnh khác.

FEAT-064 approval ghi kế hoạch downgrade pilot_vision@base từ graph khi đó gồm ba bước; bước đầu 20261103_story_upload_compat có source không reversible. Đây là ghi nhận graph/source trong hồ sơ, không phải bằng chứng full-head downgrade đã chạy rồi thất bại. Round-trip owner-run chỉ thuộc nhánh pilot_vision, trạng thái trung gian, DB mới và chín bảng pilot rỗng.

Điều kiện migration tương lai:

1. S0-doc ghi ancestry, target revision, down_revision, branch_labels, depends_on, current source head candidates và lý do chọn; không chạy Alembic.
2. Offline-check không có verdict và không bao gồm migration mới nên không mở cổng graph/current-schema. S0-owner-run chỉ có thể chạy trên DB task-owned sau approval riêng ghi rõ identity/manifest của đích DB task-owned, command chính xác, SHA-256 của script và snapshot, cùng tiêu chí đánh giá kết quả. Approval, đích DB, command, hash và tiêu chí đó hiện chưa có; trạng thái là NOT RUN và gate vẫn đóng. Offline-check ghi “facts only; not a pass/fail verdict”, không tạo verdict cho gate này.
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
- Finding N-3 vẫn phải được ghi đúng: lần rerun bốn suite GB2_T12_RERUN_20261105T013143 dùng runner mới không có hash trong approval; danh tính/hash runner đó không được ghi và không xác định trong thư mục script cục bộ. Runner đối soát run_b2_t12_readonly_recon.ps1 (hash trong approval 7466CB770F65F17477089A1C5962E4774E462059941F108017B67B2023DA70F2) hiện không còn được tìm thấy trong thư mục script cục bộ; nguyên nhân chưa biết. Helper b2_t12_readonly_recon.py vẫn còn. Không khẳng định runner đã được kiểm chứng lại; các rerun này không cung cấp căn cứ pass/fail cho S0-owner-run.
- OpenAPI P3 cho hai POST submit/cancel của assistance_requests.py phải đóng trước frontend/client integration. Đây là gate riêng S3; không thay thế N-1 route test.
- B2 mypy limitation và evidence owner-run không tạo baseline cho M2. M2 cần baseline được owner duyệt riêng, nếu scope/command yêu cầu.
- OWNER_MODAL_CALL_APPROVED=NO: các approval POC/retest Modal sau merge chỉ áp dụng plan riêng, chủ yếu synthetic/dev và có retry/workload fence; không approval nào trong merge cho phép triển khai M2 hoặc bật workload.

## 7. Acceptance criteria và stop gates

1. Mỗi requirement §4 có route status, bảng logic, owner, mã M2-AT và evidence. NFR-36 phải có owner disposition PARTIAL cho M2 và ghi rõ child media access được đề xuất hoãn M5, cross-org feedback được đề xuất hoãn M6; M2-AT-07 không chứng minh phần hoãn. NFR-38 phải có disposition PARTIAL; M2 chỉ claim metadata tuổi/ngôn ngữ, AC-65 story/video là phân bổ M4/M5 đề xuất chờ owner xác nhận. BR-58 vẫn PARTIAL: primitive thu hồi được ở M2, audience group/invitee đầy đủ ở M6. PARTIAL không phải PASS.
2. Identity, role, tenant, profile ownership, Admin class/assignment, Teacher profile/enrollment và age provenance đạt M2-AT-01/02/03/04A/04B/10 với positive/negative tests; DB thật cho route/persistence.
3. Grant/consent theo quyết định 3/OI gate; thiếu grant/policy thì deny, REAL và LEGACY_UNCLASSIFIED bị chặn nếu B4b hoãn.
4. Lifecycle đạt M2-AT-08/09; request và cancel phải được gọi qua route thật. N-1 PostgreSQL route test với wiring thật bắt buộc trước khi thoát S2 và trước D9/client integration; B1 orphan có reconciliation/read-exposure contract và regression trước dữ liệu non-synthetic/provider.
5. Target migration/schema inventory/data disposition/rollback limits được owner phê duyệt; DB/source/snapshot gate lệch thì dừng. Offline-check là historical fact-only; Alembic execution, live graph reconciliation và M2 mypy baseline chưa chạy nên không đóng gate.
6. OpenAPI request/response/error parity được freeze trước client integration; P3 đóng trong S3.
7. Evidence lưu tại feature evidence path được approval chỉ định; PARTIAL/NOT RUN/owner-run provenance ghi đúng. Plan review và implementation review là hai việc riêng.
8. Không mở M3–M6, không bật provider/Modal hoặc workload.
9. Draft 7 vẫn DRAFT / AWAITING OWNER REVIEW; chưa có independent review, owner approval hay implementation approval.

## 8. Candidate allowlist theo subphase

Draft 4 báo cáo 49 path đã được xác nhận tồn tại; phiên lập Draft 5 (lịch sử) không kiểm lại toàn bộ danh sách này. Các path dưới đây là candidate trong kế hoạch, trừ cột "Path mới", ghi chưa xác minh. Bảng chỉ để owner/reviewer xem xét trước Task Approval; không cấp quyền sửa. Các nguồn mới ở S0-doc chỉ đọc, không mở allowlist thực thi. Không dùng wildcard.

Quy ước:

- **Chỉ đọc:** tham chiếu hoặc baseline hồi quy; không được sửa nếu Task Approval không nêu đích danh file và lý do.
- **Candidate có thể sửa:** chỉ được sửa khi Task Approval của đúng pha liệt kê file đó, kèm hash trước khi sửa.
- **Path mới:** file chưa tồn tại; tên và hash phải có trong approval trước khi tạo. Test hiện có là baseline hồi quy chỉ đọc; test M2 là file mới.
- **Hồ sơ governance** (CONTEXT, DECISIONS, STATUS, TASK_APPROVAL của FEAT-063/FEAT-064, ledger) chỉ do phiên ghi (Codex) cập nhật sau lệnh của owner. Chúng nằm ngoài allowlist của mọi phiên thực thi và chỉ đọc đối với phiên thực thi.
- Draft 1–6 của plan này là đầu vào chỉ đọc; Draft 7 là artifact đang chờ review, không phải plan được duyệt.

| Pha | Chỉ đọc | Candidate có thể sửa | Path mới (chưa xác minh) | Exclusions / hard stop |
|---|---|---|---|---|
| S0-doc | Mọi tài liệu pin ở §1; features/FEAT-063-system-architecture-rearchitecture/SOURCE_REGISTER.md; features/FEAT-063-system-architecture-rearchitecture/evidence/COMMIT_WHITESPACE_NORMALIZATION_20261103.md; Draft 1/2/3/4 của plan này; backend/alembic/versions/20261104_story_revisions.py; backend/src/sketch2life/infrastructure/persistence/core_models.py; .claude/handoff/logs/GB2_T12_OFFLINE_20261105A/offline-check.txt (local, git-ignore); hồ sơ governance. | Không có file hiện có. | Bản plan kế tiếp; evidence addendum S0-doc (tên chưa xác minh). | Không sửa source/test/migration/SRS/DTR/roadmap/governance. Cần DB hoặc file ngoài approval thì dừng. |
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
| 3. B4b/OI-05..08 | Bật consent/share sau khi OI được xác định; hoặc hoãn và giữ synthetic-only/deny REAL, LEGACY_UNCLASSIFIED. | SRS hiện hành §29.2, dòng 1130–1133 vẫn để mở chuyên gia/privacy, retention/backup, region/cross-border và production/operations. Mapping/disposition cụ thể cần owner ghi nhận; không có consent hoặc dữ liệu thật authority. | S1b và dữ liệu thật. | Hoãn REAL; chỉ xây primitive deny-by-default nếu được duyệt. |
| 4. B5 receipt legacy | Còn requirement hay owner disposition không dùng? | Nếu còn: xác định consumer, payload, retention, mapping; nếu không: disposition chính thức. | S1b/S2 nơi receipt dùng. | Không mở B5 khi chưa có consumer xác nhận. |
| 5. Schema convergence | Chọn owner chốt storyrun_upload_sessions → core.upload_sessions, run_id → story_run_id, owner columns, asset refs, history. | Mapping không rõ có thể mất liên kết/history hoặc tạo hai nguồn sự thật. | S0-doc/S2 migration. | Giữ history; chưa migrate khi chưa có mapping ký duyệt. |
| 6. Mypy baseline | Roadmap đã nêu “Ghi mypy baseline exception và không thêm lỗi mới”. Owner xác nhận baseline chính xác theo file/command và không thêm diagnostic; hoặc yêu cầu xử lý trước khi đóng pha. | test_be1_postgres_api.py hiện NO VERDICT; crash tool không phải pass. Quyết định không miễn kiểm tra lỗi mới. | S0-owner-run; S1/S2 nếu sửa target; S3 closeout. | Đo baseline read-only có approval, cùng command/version, không thêm lỗi; không suy diễn phần chưa chạy. |
| 7. B0 provenance | Owner xác nhận normalized bytes tương đương bytes duyệt; hoặc không xác nhận và B0 chưa làm căn cứ có thẩm quyền cho M2. | Hash hiện tại 773C khác hash gốc 03AEA; evidence normalization tại §1.1 ghi trailing whitespace, final blank lines và line endings. Original snapshot bytes chưa được phiên này xác minh. | S0-doc và mọi requirement dựa B0. | Owner ghi xác nhận qua approval ghim evidence; không sửa pin để làm hash khớp. |
| 8. Baseline review | Owner xác nhận dd70685eae58aaaefea3e567f5c23d09345a8513 là baseline review cho Draft 7 (Draft 5/6 là lịch sử), hoặc dừng và cập nhật pins sau khi xác định checkout có thẩm quyền. | Đây là checkout hiện tại được quan sát trước khi lập Draft 7; việc hash khớp không thay owner confirmation. Đây là xác nhận baseline, không phải approval scope. | S0-doc và mọi phase tiếp nối. | Chưa dùng kế hoạch cho phase tiếp theo tới khi owner ghi nhận baseline. |
| 9. NFR-36 disposition | Owner xác nhận PARTIAL cho M2 và mapping đề xuất child media sang M5, cross-org feedback sang M6; hoặc chốt mapping khác. | NFR-36 bao gồm access child media/profile và cross-role grants theo permission/reason/audit; M2-AT-07 chỉ phủ profile/grant trong scope M2. | M2-AT-07, M5 media và M6 feedback. | Không claim toàn NFR-36 PASS từ M2. |
| 10. NFR-38 / AC-65 disposition | Owner xác nhận PARTIAL cho M2 và mapping đề xuất AC-65 story sang M4, video sang M5; hoặc chốt mapping khác. | M2-AT-10 chỉ kiểm metadata locale/age; AC-65 còn age-band/context đã duyệt, Vietnamese content và video cá nhân hóa theo tranh trẻ. | M2-AT-10, M4 story và M5 video. | Mapping M4/M5 là đề xuất; không claim chất lượng AC-65 đã đạt. |

Các câu hỏi bổ sung chưa xác minh: age-band boundary/catalog và physical mapping; field/purpose/expiry của share; canonical route/method cho Parent invite/accept/revoke và Teacher profile; placeholder organization/org_id; cleanup sau DELETE_PENDING. NFR-36/NFR-38 disposition và mapping pha được ghi là quyết định owner đang chờ tại §9. Nếu chưa quyết thì deny hoặc hoãn surface liên quan.

## 10. Gói cần có trước launch

- Owner xác nhận dd70685eae58aaaefea3e567f5c23d09345a8513 là baseline review Draft 7 tại §0/§9.8 (Draft 5/6 là lịch sử) và quyết định B0 provenance tại §9.7.
- Owner quyết các mục §9 ảnh hưởng đến pha được launch; lưu trong approval, gồm disposition PARTIAL cho NFR-36/NFR-38 và chốt hoặc sửa mapping M5/M6, M4/M5 đề xuất.
- Ghim plan hash, branch/HEAD, nguồn, snapshot manifest.
- Ghi exact file allowlist từng path, path mới, exclusions; không wildcard.
- Ghi DB task-owned identity, người tạo/chạy, dữ liệu, snapshot/restore và cleanup boundary.
- Ghi Alembic graph/target revision, offline plan/SQL review và command ceiling.
- Ghi test matrix/tầng test; route acceptance dùng PostgreSQL thật/wiring thật khi route là đối tượng.
- Ghi disposition B1 orphan, B2 OpenAPI/T12/T13/mypy conditions và mọi PARTIAL/NOT RUN; ghi rõ offline-check là historical fact-only, còn Alembic execution/live graph/mypy baseline của M2 chưa chạy.
- Owner ghi Task Approval cho đúng subphase qua phiên điều phối. Approval một pha không mở pha khác, M3–M6 hoặc provider.

Cho tới khi các điều kiện này được ghi nhận, kế hoạch vẫn **DRAFT / AWAITING OWNER REVIEW**; M2 chưa launch và không có quyền sửa code, migration, DB hoặc gọi provider.
