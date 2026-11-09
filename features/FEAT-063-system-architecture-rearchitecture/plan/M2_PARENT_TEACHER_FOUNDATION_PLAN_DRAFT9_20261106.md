# Kế hoạch M2 — Parent / Teacher Foundation (Draft 9)

**Feature:** FEAT-063 — System Architecture Rearchitecture  
**Ngày:** 2026-11-06  
**Trạng thái:** **DRAFT 9 / AWAITING INDEPENDENT REVIEW**  
**Phạm vi:** Draft 9 tiếp nối Draft 8 theo review độc lập NEEDS_REVISION (0 P1 / 3 P2 / 8 P3); chỉ cập nhật các mục trong bảng thay đổi Draft 8 → Draft 9. Draft 9 là kế hoạch DRAFT, chưa có review độc lập hoặc owner approval; không phê duyệt implementation, M2, M3–M6, DB, migration, provider, Modal hay workload. S0-doc chỉ CLOSED ở phạm vi tài liệu theo D-150; S0-owner-run, S1a, S1b, S2, S3 và M3–M6 chưa mở.

## Thay đổi từ Draft 7 sang Draft 8

| Mục | Thay đổi từ Draft 7 sang Draft 8 | Nguồn |
|---|---|---|
| Đầu file, §0 và §7 | Đổi tên/trạng thái artifact sang DRAFT 8 / AWAITING OWNER REVIEW; ghi HEAD dd70685eae58aaaefea3e567f5c23d09345a8513, S0-doc CLOSED chỉ ở phạm vi tài liệu, không có implementation approval; cập nhật §7 để nói đúng Draft 8 đang chờ review; ghi trạng thái Git có trước khi tạo Draft 8. | D-142, D-145, D-146, D-150; Git metadata đã quan sát |
| §1 | Draft 8 ghi nhận tại thời điểm soạn: 17 pin kế thừa gồm 14 unchanged khớp, 2 pin DECISIONS.md/TASK_APPROVAL.md được cập nhật và khớp, 1 offline-check ENOENT; 2 pin mới khớp, tổng 18/19. Draft 9 đọc lại bytes hiện tại của cả 19 pin và xác nhận 19/19 khớp, gồm offline-check. | Hash cổng Draft 9; evidence S0-doc; Draft 7; review Draft 8 P3-4 |
| §3 | Ghi CLOSED cho S0-doc; S0-owner-run và S1a vẫn DRAFT với điều kiện approval riêng; S1b DEFERRED; S2/S3 vẫn DRAFT với N-1, B1 và OpenAPI P3 gates. | D-144, D-145, D-146, D-148 mục 8, D-150 |
| §4 | Thêm PARTIAL cho BR-49 chỉ trên lát tenant/class foundation và nêu bảng ngoài lát cùng owner theo DTR; ghi NOT COVERED cho BR-58 và grant portion của NFR-34/NFR-36 vì S1b hoãn; giữ PARTIAL đã quyết cho NFR-36, còn nhãn PARTIAL của NFR-38 giữ nguyên không đổi. | Evidence S0-doc §2 dòng 51; D-143; D-148 mục 8 |
| §4.1 | Giới hạn Parent/Teacher foundation route set ở năm route SRS §21.2; làm rõ /v1/me chỉ là route group ở SRS §9.6, /v1/teacher/profiles chỉ xuất hiện ở §9.6, không thêm route xóa; ghi identity fixture là seed. | Evidence S0-doc §2.1; D-148 mục 3–4 |
| §4.2 | Bổ sung deny cases cho role đặc quyền và thiếu grant; đồng nhất denial giữa ba trường hợp tenant/class; cố định acceptance tuổi 36–120 và null band; đánh dấu M2-AT-05/06/07 NOT RUN khi S1b hoãn. | D-148 mục 2, 5–8; D-143 |
| §8 | Draft 8 đã ghi Draft 1–7 là read-only và báo offline-check.txt ENOENT/không re-verified; Draft 9 re-read path, hash khớp và ghi tổng 19/19. Các nội dung S0-owner-run, F-1/F-2/F-4/F-6, denial codes, nguồn tuổi và giới hạn S0-doc vẫn theo D-144/D-148 và evidence. | D-144 §9.1/§9.3/§9.6; D-148 mục 4–8; evidence §6; review Draft 8 P3-4 |
| §9 | Phân biệt direction đã được quyết định theo D-142..D-150 với chi tiết còn mở; giữ các default ở trạng thái đề xuất, không phải quyết định. | D-142..D-150 |
| §10 | Cập nhật launch package theo trạng thái đóng S0-doc và các approval còn cần; thêm lịch sử Draft 7 → Draft 8. | D-142, D-144, D-145, D-146, D-148, D-150 |
| §0 và dấu vết review | Gọi rõ Draft 5 tại câu lịch sử, đánh dấu D6-1 là finding lịch sử Draft 5 → Draft 6 được giữ nguyên; change table này liệt kê riêng thay đổi ở §1 và §10 mà review Draft 7 trước đó đã nêu thiếu. | Review Draft 7 về tính đầy đủ danh sách thay đổi |

## Thay đổi từ Draft 8 sang Draft 9

| Mục | Thay đổi | Nguồn |
|---|---|---|
| Đầu file, §7 mục 9, §8, §10 và lịch sử bản | Ghi trạng thái Draft 9 là DRAFT / AWAITING INDEPENDENT REVIEW; nêu review Draft 8 NEEDS_REVISION (0 P1 / 3 P2 / 8 P3) và giữ rõ không có approval implementation hay mở pha. | Review độc lập Draft 8; D-150 |
| Bảng D7→D8; Tác động của merge; §1.3–§1.4; §8; §10 | Giữ 18/19 là kết quả lịch sử Draft 8 khi offline-check báo ENOENT; Draft 9 đọc lại 19 pin, hash đều khớp (19/19), gồm offline-check. Ghi log 27 bước và 9/9 là dữ kiện lịch sử, không phải pass/fail gate. | Review Draft 8 P3-4 |
| Bổ sung lịch sử D7→D8; §3; §10 | Ghi lại các mục bị thiếu trong bảng D7→D8; khôi phục sáu tiêu chí S0-doc, giữ S1b DEFERRED theo D-148 mục 8; khôi phục yêu cầu exact allowlist từng path, không wildcard, owner quyết các mục §9 và câu giữ kế hoạch DRAFT tới khi điều kiện được ghi nhận. | Review Draft 8 P3-5, P3-6; D-148 mục 8; đối chiếu diff Draft 7/Draft 8 |
| §3 S1a/S3; §4 FR-PL-01; §4.2 M2-AT-11; §7; §8 | Thêm acceptance synthetic-only/consent M2-AT-11 cho S1a và điều kiện thoát S1a; không giả định default data_origin, giữ F-6 cho Task Approval S1a. Đề xuất owner chấp nhận disposition NOT RUN/DEFERRED của AT-05/06/07 trong Task Approval S3. | Review Draft 8 P2-3, P3-6; D-144 §9.3; D-148 F-6 |
| §2.1; §4 FR-PL-02; §8 | Ghi D-148 mục 1: “Admin tổ chức” (SRS §20) và “School Manager” (SRS §§3/31.3) là một role M2, mã school_admin, quyền chỉ theo §20; nêu bất nhất tên gọi giữa các phần SRS. | D-148 mục 1; review Draft 8 P3-8 |
| §2.2; §4 NFR-38; §8 | Ghi band null/“chưa cấu hình” không tính là đạt NFR-38/AC-65. | D-148 mục 6; review Draft 8 P3-8 |
| §4 FR-PL-07, FR-PL-08, BR-48 | Gắn nhãn scope grant/share là NOT COVERED trong M2; giữ NOT RUN cho các acceptance test tương ứng khi S1b DEFERRED. | D-148 mục 8; review Draft 8 P3-7 |
| §4 BR-58; §7; lịch sử D3-2, F5, D5-9 | Đổi BR-58 của M2 thành NOT COVERED, audience nhóm Parent/invitee thuộc M6; đánh dấu các câu về primitive/partial trong bảng D3-2, F5, D5-9 là lịch sử của Draft cụ thể. | D-148 mục 8; review Draft 8 P2-1 |
| §4.2 M2-AT-02 | Thêm deny case POST classes với org_id ngoài assignment active hoặc org không tồn tại; cùng denial/status/error shape như ba ca class, không lộ existence. | D-148 mục 5; review Draft 8 P2-2 |
| §4.2 M2-AT-03, M2-AT-04A | Nêu rõ tuổi 35/121 bị application từ chối, 36/120 hợp lệ; thêm Teacher thứ hai cho cùng class với kết quả để Task Approval S1a quyết nếu mã chưa ép cardinality. | D-148 mục 5–7/F-2; review Draft 8 P3-10 |
| §4 intro, FR-PL-08, M2-AT-08, M2-AT-10 | Ghi POST /v1/story-runs và /cancel là route/service S2 ngoài năm route nền M2; N-1 là ngoại lệ duy nhất cho route test ngoài tập nền. | D-148 mục 4; review Draft 8 P3-9 |
| §5.2–§5.3 | Gắn provenance cho các khẳng định tables.py và migration 20261102/20261103: được phiên soạn trước ghi nhận từ source, nằm ngoài allowlist S0-doc theo evidence §6 và chưa được S0-doc xác minh; Draft 9 không xác nhận độc lập các file đó. | Review Draft 8 P3-11; evidence §6 |

**Bổ sung bảng D7→D8 (theo review Draft 8):** Diff Draft 7/Draft 8 xác nhận Draft 8 thay bảng D7-1..D7-4 bằng change table D7→D8: D7-1 ghi cách diễn đạt D5-8; D7-2 bổ sung tóm tắt nhóm diff trong §0; D7-3 chuẩn hóa đơn vị path/dòng; D7-4 làm rõ trạng thái lịch sử Draft 5/6 và §9.8. Draft 9 ghi các mục này trong đoạn bổ sung thay vì chèn lại bảng D7 riêng, vì change table D7→D8 của Draft 8 đã thay vai trò bảng đó và các sửa chữa vẫn là lịch sử. Draft 8 viết lại provenance Draft 6/7 ở §0, bỏ đoạn “Trước khi tạo Draft 6…” và câu re-hash 17 nguồn của phiên Draft 7; Draft 9 không phục hồi các câu lịch sử đó vì §0 và §1 hiện ghi đúng provenance của từng lần và audit hiện tại. Draft 8 thay sáu tiêu chí S0-doc trong §3 bằng dẫn chiếu closure D-150; Draft 9 phục hồi từng tiêu chí dưới đây. Draft 7 từng có tiêu chí thoát S1b, nhưng Draft 9 không khôi phục một gate chạy được vì D-148 mục 8 giữ S1b DEFERRED và M2-AT-05/06/07 NOT RUN. Trong §10, Draft 8 không còn câu exact allowlist từng path/không wildcard, câu owner quyết mục §9 và câu “Cho tới khi các điều kiện này…”; Draft 9 phục hồi rõ cả ba nội dung.

## Thay đổi so với Draft 5


| ID | Finding review | Cách xử lý trong ghi nhận lịch sử | Bác bỏ/không sửa |
|---|---|---|---|
| D6-1 (lịch sử Draft 5 → Draft 6; giữ nguyên trong Draft 8) | F-A (P2) — §0 có thể bị hiểu là inventory đầy đủ dù chỉ nêu 9 path cho S2/S3. | §0 ghi rõ các path là TIÊU BIỂU/không đầy đủ; giữ 154 path và +20,294/−56 dòng (không phải byte), nêu các StoryRun-lite/Bruno paths bổ sung, 5 file nhị phân, lệnh lấy danh sách đầy đủ, và giới hạn rằng diff không chứng minh code/migration/test đã chạy. | Không thêm path vào allowlist §8, không đổi cột chỉ đọc/candidate. Việc thêm router/schema/photo bridge làm input chỉ đọc S2/S3 chỉ là đề xuất chờ owner/coordinator. |
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
| D5-9 (lịch sử Draft 5) | P2-I — N-1 và BR-58 có nguy cơ gán sai requirement hoặc phase. | Lịch sử Draft 5: §4/§4.2 phân biệt FEAT-064 N-1 với FR-PL-08; BR-58 trỏ SRS §30.4 và giữ audience đầy đủ ở M6. Đây không phải disposition hiện tại; Draft 9 ghi BR-58 NOT COVERED trong M2 theo D-148 mục 8. | Không đổi owner mapping hoặc mở M6. |
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
| D3-2 (lịch sử Draft 3) | BR-58 được map sang M2-AT-04 (assignment/enrollment), không phải primitive grant/revoke như F5 yêu cầu. | Lịch sử của Draft 3: BR-58 phần M2 được map sang primitive grant/revoke có thể thu hồi (M2-AT-05/06, S1b), còn audience lesson nhóm/invitee thuộc M6. Đây không phải kết quả hiện tại; Draft 9 áp dụng D-148 mục 8: BR-58 NOT COVERED trong M2. |
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
| F5 — BR-58 (lịch sử Draft 2) | Lịch sử Draft 2 ghi lesson audience là nhóm Parent hoặc invitee cụ thể có thể thu hồi; primitive grant/revoke được ghi là nền M2 và audience lesson đầy đủ thuộc M6. Đây không phải kết quả M2 hiện tại; Draft 9 ghi BR-58 NOT COVERED trong M2 theo D-148 mục 8. |
| F6 — Provenance B0 | Dẫn evidence chuẩn hóa và hash; yêu cầu owner xác nhận normalized bytes tương đương. Bản gốc trong snapshot git-ignore chưa được phiên này xác minh. |
| F7 — Phân pha | Tách S0 thành S0-doc/S0-owner-run và S1 thành S1a/S1b; thêm tiêu chí đóng/stop gate. N-1 và stale-owner B1 là cổng thoát S2; OpenAPI P3/freeze là cổng S3. |
| F8 — Quyết định owner | Thêm lựa chọn, hệ quả, pha bị chặn và mặc định đề xuất. Ghi nhận roadmap đã yêu cầu baseline mypy và không thêm lỗi mới. |
| F9 — Migration evidence | Phân biệt kế hoạch ngoại tuyến với migration đã chạy. Không khẳng định 27 bước đã chạy hoặc chạy trong một transaction; full-head downgrade không được thực thi trong evidence đã rà. |

## 0. Trạng thái, checkout, merge và baseline cần owner xác nhận

Trong lịch sử, Draft 5 được lập trên branch feature/feat063-be-foundation, HEAD dd70685eae58aaaefea3e567f5c23d09345a8513. HEAD có first parent 1e109b1726f327ac9383457b0dbdd535ef5c6518 và second parent fb834771c24957bb8e289fb95d21410b14181e57. Chuỗi lịch sử ghi nhận trong Draft 4 là b6dbfa68e66718f3f40902c093e9ebd634b1ebb9 → 1e109b1726f327ac9383457b0dbdd535ef5c6518 → dd70685eae58aaaefea3e567f5c23d09345a8513.

Trước khi tạo Draft 5, index rỗng và working tree có đúng bốn path untracked: Draft 1–4. Hash trước khi ghi: Draft 1 F47393FD1028B20D841114786E7D07B12BC8C89A67EF6697F0396EFCA7942E81; Draft 2 A09F7E6BF8534E85EE4EE4573209B5346861008AA4A5C4A8C907CF4EFEDCFE66; Draft 3 A6F8CE23DA3650B38FF7E13BAF9052371B1655BE400BB6D5F9053A5D5E2C638D; Draft 4 A31DCEA8DBEF0CF9E59FC7E9F3346C35B1F278DC1D6AAB3E992B436E1590FEEC. Branch, HEAD, parent commits, empty index, bốn path untracked và cả 17 hash nguồn được ghim tại §1 đều khớp trước khi ghi Draft 5. Draft 1–4 là đầu vào chỉ đọc. Git status đồng thời phát sinh warning rằng user-level global ignore config không đọc được; không dùng warning đó để khẳng định path nào cụ thể bị ảnh hưởng.
Trong lần ghi nhận lịch sử D6-1, trước khi tạo bản ghi đó, index rỗng, tracked worktree diff rỗng và đúng năm file Draft 1–5 là untracked. Hash pre-edit: Draft 1 F47393FD1028B20D841114786E7D07B12BC8C89A67EF6697F0396EFCA7942E81; Draft 2 A09F7E6BF8534E85EE4EE4573209B5346861008AA4A5C4A8C907CF4EFEDCFE66; Draft 3 A6F8CE23DA3650B38FF7E13BAF9052371B1655BE400BB6D5F9053A5D5E2C638D; Draft 4 A31DCEA8DBEF0CF9E59FC7E9F3346C35B1F278DC1D6AAB3E992B436E1590FEEC; Draft 5 B1C39C63314274137699F06B219C531E92BE0727D6120D7F06445F9C326283D7. Các hash này là baseline của file đầu vào, không thay thế owner review. Git status đồng thời phát warning user-level global-ignore config bị Permission Denied; đây là warning riêng, không chứng minh path repo nào bị ảnh hưởng. Báo cáo cũ về backend/.pytest-phase8-precommit/ là từ reviewer trước; lần status này không phát warning cho path đó.

Trước khi lập Draft 7, branch feature/feat063-be-foundation ở HEAD dd70685eae58aaaefea3e567f5c23d09345a8513 với hai parent 1e109b1726f327ac9383457b0dbdd535ef5c6518 và fb834771c24957bb8e289fb95d21410b14181e57; index rỗng, working tree chỉ có sáu artifact kế hoạch tiền nhiệm chưa theo dõi. Draft 7 được lập từ bản kế hoạch tiền nhiệm chỉ đọc, SHA-256 C836A72A84D5EED70427CC69540050852D54C83D94745DAFEF02A0A0704FD537; ghi nhận pin của phiên đó là lịch sử, không thay thế kết quả final audit Draft 8 tại §1. Các bản kế hoạch tiền nhiệm không bị sửa.
Phiên lập Draft 7 chỉ đọc tài liệu/metadata, kiểm tra hash và Git, rồi đếm path bằng git diff --name-status; không chạy Alembic, DB, mypy hay test. Git status cảnh báo không đọc được user-level global ignore config; cảnh báo riêng theo thông tin đầu vào rằng backend/.pytest-phase8-precommit/ không đọc được cũng được ghi nhận, không xem là lỗi kế hoạch.
Trước khi tạo Draft 8, branch feature/feat063-be-foundation ở HEAD dd70685eae58aaaefea3e567f5c23d09345a8513 và index rỗng. Git status --short ban đầu có hai tracked path modified là features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md và features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md; tám untracked path gồm evidence S0-doc và Draft 1–7. Các thay đổi đó có trước tác vụ Draft 8. Đường dẫn Draft 8 chưa tồn tại trước khi ghi; Draft 1–7 và các hồ sơ hiện có không thuộc phạm vi sửa của tác vụ này.
D-142 xác nhận dd70685eae58aaaefea3e567f5c23d09345a8513 làm review baseline cho Draft 7; Draft 8 được soạn trên cùng HEAD. Theo D-150, S0-doc CLOSED ở phạm vi tài liệu với evidence được ghim tại §1; D-145/D-146 không mở S0-owner-run, S1a, S1b, S2, S3 hay cấp implementation approval. Trạng thái hiện tại của từng pha được ghi tại §3.

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

Diff name-status cũng cho thấy StoryRun-lite paths chưa nêu trong nhóm 9 path trên: backend/src/sketch2life/application/ports/story_run_lite.py; backend/src/sketch2life/infrastructure/story_run_lite/composition.py; backend/src/sketch2life/infrastructure/story_run_lite/photo_bridge.py; backend/src/sketch2life/interfaces/http/routers/story_run_lite.py; backend/src/sketch2life/contracts/schemas/ai_story.py (file mới); backend/tests/integration/test_story_run_lite_loopback.py; backend/tests/unit/test_ai_story_contracts.py (file mới); backend/tests/unit/test_modal_story_function_client.py (file mới); backend/tests/unit/test_story_run_lite_photo_bridge.py; features/FEAT-063-system-architecture-rearchitecture/artifacts/storyrun-lite/openapi.json; và các Bruno files dưới features/FEAT-063-system-architecture-rearchitecture/artifacts/storyrun-lite/bruno/ (environments/local.bru, requests/01-create-run.bru, requests/11-generate-story-revision.bru, requests/12-get-story-revision.bru, requests/13-confirm-story-revision.bru). Đây chỉ là inventory mô tả diff ở §0, không phải bổ sung vào allowlist §8. Đề xuất chờ owner/coordinator: nếu cần, xem xét riêng routers/story_run_lite.py, schemas/ai_story.py và photo_bridge.py làm input chỉ đọc S2/S3; bản kế hoạch tiền nhiệm không thêm chúng vào allowlist.

Năm file nhị phân trong evidence/assets là synthetic_vietnamese_narration.wav, drawing_vlm_synthetic_butterfly.png, flux2_klein_synthetic_butterfly_guide.png, vieneu_synthetic_narration.wav và synthetic_childlike_butterfly.png.

Lấy inventory path đầy đủ bằng git diff --name-status 1e109b17 dd70685e. Diff/source-control chỉ cho biết path và số dòng thay đổi; nó không chứng minh code, migration hoặc test đã chạy.

Các bản ghi mới liên quan gồm:

- D-139: giữ nguyên kết quả Parent AI mơ hồ; không retry hoặc coi là thành công; probe story tách rời không phải Parent API end-to-end.
- D-140: phân biệt manifest story với drawing; lỗi contract đã biết là terminal, outcome unknown không retry; activity Parent sau video; Teacher Deck/lesson visuals còn DRAFT và chịu gate SRS.
- D-141: owner cho phép một đợt retest non-video synthetic riêng, có retry fence và thời hạn chờ; thêm POC ảnh SAM2.1; không promotion, không bật workload, không video.
- Mục Merge reconciliation for decision IDs: dải D-127..D-135 trên nhánh Modal được đổi thành D-133..D-141 do trùng ID; mục D-120 trùng nội dung với D-131 không lặp lại.
- Các approval/retest Modal riêng gồm scaffold; drawing VLM L4 POC và corrective retry; hosting wave; API availability smoke; backend-to-Modal drawing slice; Parent image-to-script và generated-image/story/activity retest; AI flow/Teacher Deck POC; full non-video retest. Phạm vi, kết quả và giới hạn mỗi việc chỉ áp dụng cho plan/evidence của việc đó. Chúng không phê duyệt M2, không bật workload và không cấp quyền Modal/provider cho kế hoạch này.

Draft 4 từng yêu cầu owner xác nhận dd70685eae58aaaefea3e567f5c23d09345a8513 làm baseline. D-142 hiện xác nhận HEAD đó làm review baseline cho Draft 7; Draft 8 dùng cùng checkout. Đây là baseline review, không phải implementation approval.

Tài liệu này chỉ là kế hoạch DRAFT. Không có quyền implementation, migration, thao tác DB, provider, Modal, tích hợp frontend hoặc M3–M6. B2 được owner chấp nhận có điều kiện trong FEAT-064, đúng giới hạn ở §6.3; điều đó không phải approval M2. OWNER_MODAL_CALL_APPROVED=NO áp dụng cho mọi Modal/live call ngoài approval riêng có phạm vi riêng; approval POC/retest sau merge không cho phép triển khai M2 hay bật workload.

## 1. Căn cứ và pin nguồn

Ghi nhận re-hash đi cùng Draft 5 là lịch sử, không thay thế final audit Draft 9 tại §1: 17 pin kế thừa và 2 pin mới đều khớp (19/19). Draft 8 từng báo offline-check ENOENT; Draft 9 đã đọc bytes hiện tại và re-verify đúng hash. Không chuẩn hóa bytes để làm khớp pin. Các Draft 1–4 được giữ nguyên.
Bản ghi lịch sử D6-1 dùng Draft 5 làm nền chỉ đọc; SHA-256 Draft 5 là B1C39C63314274137699F06B219C531E92BE0727D6120D7F06445F9C326283D7. Lịch sử pin của lần ghi D6-1 không phải kết quả final audit Draft 9; audit hiện tại ghi đủ 19/19 pin khớp như tại §1. Điều này chỉ xác nhận bytes đã quan sát, không phải owner approval.

Draft 7 dùng bản kế hoạch tiền nhiệm làm nền chỉ đọc, SHA-256 C836A72A84D5EED70427CC69540050852D54C83D94745DAFEF02A0A0704FD537. Số re-hash của Draft 7 là lịch sử, không thay kết quả hiện tại. Draft 8 từng ghi 18/19 do offline-check báo ENOENT; Draft 9 đã re-verify đủ 19/19 pin từ bytes hiện tại. Đây chỉ xác nhận bytes, không phải owner approval.
Draft 8 kế thừa Draft 7 chỉ đọc, SHA-256 BB3C9F165731B1AEE261265270526B791FEE7BD622CE7D614514F2622DEFD099. Audit Draft 8 từng ghi 14 hash unchanged và 2 pin DECISIONS.md/TASK_APPROVAL.md cập nhật khớp; offline-check.txt (6FF16B2E77EE7DB7CE18521484B92FAA9B40F685393D35A7746E74236313E143) khi đó báo ENOENT/không re-verified; hai pin mới khớp nên tổng là 18/19 ở lượt Draft 8. Draft 9 đọc bytes hiện tại của cả 17 pin kế thừa và 2 pin mới; tất cả khớp (19/19), gồm offline-check. Việc kiểm tra bytes không phải owner approval.

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
| features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md | AE98557F3125362E4540F1EF8A235BF9F20442BF9A97E47D3B05ACB0BD096EC5 |
| features/FEAT-063-system-architecture-rearchitecture/CONTEXT.md | 6CAA4A5BE423383B026A662051FB54709AF73B1178A5673849AD44B6B6697F1D |
| features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md | 8278548B48BFFDF207C158E7F18038EA8495749A594EF59DC0DE6894C83ACCBE |
| features/FEAT-063-system-architecture-rearchitecture/SOURCE_REGISTER.md | 2A419E529CE9603FF03A0697CC800A56826BC6EAD51B1596135AAA84B9FCF98B |

### 1.2. FEAT-064

| Tài liệu | SHA-256 |
|---|---|
| features/FEAT-064-current-flow-modal-vision-dev/evidence/A2_REV3_INDEPENDENT_REVIEW_CLOSEOUT_20261103.md | 10B12F4417A5E29DF0ED1697F33A8FAA08D692E71015998CCC8DE297328A1C36 |
| features/FEAT-064-current-flow-modal-vision-dev/plan/FEAT064_A2_B1_B2_SEQUENTIAL_GOAL_20261103.md | D7DEE2977C5AA28B26FCB117281DE8B23E4D4AA85A42922B8B37752FBDA8752A |
| features/FEAT-064-current-flow-modal-vision-dev/approvals/TASK_APPROVAL.md | 9D07B88190E8F5831D79431A79C2AAC944B266CB28CD29265E5D0283B77921B8 |

### 1.3. Nguồn mới sau merge, kế hoạch kế thừa, evidence và migration

| Nguồn | SHA-256 |
|---|---|
| backend/alembic/versions/20261104_story_revisions.py | 3618BEF0ECCB0E01EE61F65E1065F7AE8EA6297FE0781D965588614D0F1C37F8 |
| backend/src/sketch2life/infrastructure/persistence/core_models.py | 47D60EEECEF12F583B927BAB7FE3B74B9F19F15231E84E4039187376A502473A |
| .claude/handoff/logs/GB2_T12_OFFLINE_20261105A/offline-check.txt (local, git-ignore; pin inherited/reference từ Draft 7; Draft 8 từng báo ENOENT/không re-verified; Draft 9 đã đọc bytes hiện tại, hash khớp và re-verified) | 6FF16B2E77EE7DB7CE18521484B92FAA9B40F685393D35A7746E74236313E143 |
| features/FEAT-063-system-architecture-rearchitecture/plan/M2_PARENT_TEACHER_FOUNDATION_PLAN_DRAFT7_20261106.md (nguồn kế thừa) | BB3C9F165731B1AEE261265270526B791FEE7BD622CE7D614514F2622DEFD099 |
| features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S0_DOC_SOURCE_RECONCILIATION_20261106.md | 1BB71300A6A22487311A8D39EECB0EB1CE2664CB471EC2DAF45DA8DE2E244001 |

### 1.4. Căn cứ và provenance

- Bản ghi lịch sử D6-1 ghi nhận đã đọc AGENTS.md, .codex/sketch2life-harness.md, FEAT-063 CONTEXT.md, SOURCE_REGISTER.md, DECISIONS.md, STATUS.md, TASK_APPROVAL.md, roadmap, backlog, SRS, DTR, evidence normalization, FEAT-064 A2/B2 records, StoryRun-lite/Core models và migrations liên quan. Draft 8 từng báo 18/19 do offline-check ENOENT; Draft 9 đã re-verify toàn bộ 19 pin bytes hiện tại, như ghi ở §1.
- D-132 chấp nhận roadmap sáu mốc làm baseline lập kế hoạch. SRS v2.3-draft chưa ký; route matrix chưa phải OpenAPI cuối.
- DTR mô tả ownership logic, không xác nhận schema vật lý. core_models.py là module Core hiện có; không tìm thấy module persistence Parent trong source tree được rà. Parent tables trong DTR vẫn là mô hình logic, không phải bằng chứng implementation.
- B0 plan hiện có hash 773C4A8340C8E33AE39764D920B042AC19BACBAF6DC561FE9D5D3DFFCC4B5A5A; hồ sơ duyệt ghi bytes gốc hash 03AEA386B8545624100688B68AA828A84CD154B47857CB5E98FB06354D6BB582. Evidence normalization tại §1.1 quy provenance cho trailing whitespace, final blank lines và line endings; original bytes trong snapshot git-ignore không có trong repo đã rà và không được xác minh trong phiên này. Hai hash bytes khác nhau không tự chứng minh khác biệt ngữ nghĩa. Source register ghi nội dung không chỉ khác line ending; điều đó có thể đồng thời đúng với việc normalization evidence nêu thêm whitespace cuối dòng/blank lines, nên hiện chưa chứng minh được contradiction. Owner vẫn quyết định authority/tương đương.
- OI-05..08 hiện được ghi tại SRS §29.2, dòng 1130–1133. Chúng để mở các câu hỏi về chuyên gia/privacy, retention/backup, region/cross-border và production/operations; chưa có authority cho consent hoặc dữ liệu thật. Các lựa chọn giữ mở tại §9.
- Route share Parent, schema vật lý Parent, catalog tuổi và một số owner columns chưa được đóng; đánh dấu chưa xác minh.
- Migration 20261104_story_revisions.py hiện có trong source và được ghim riêng ở §1.3; pin nguồn chứng minh file bytes, không chứng minh migration đã chạy.
- Offline-check ghi rõ không có DB connection, network hay migration execution và kết thúc bằng facts only; not a pass/fail verdict. Log báo kế hoạch upgrade 27 bước cùng số 9 observed version rows / 9 script_heads tại thời điểm ghi; đây là dữ kiện lịch sử, không phải cổng pass/fail. Danh sách script_heads dừng ở 20261103_story_upload_compat, không chứa migration 20261104_story_revisions; log không chứng minh graph/head hiện tại hay migration đã chạy.
- M1 là demo synthetic local. M1/A2/B1/B2 không cấp quyền cho M2.
- Review Draft 3 được báo cáo ngoài repository; không có artifact/hash pinned ở đây nên verdict không được phiên này xác minh độc lập. Reviewer trước đó báo cáo permission denied khi đọc .pytest-phase8-precommit. Phiên Draft 5 thấy bốn Draft 1–4 untracked cùng warning riêng về user-level global ignore config; không có căn cứ nói path .pytest-phase8-precommit được tái kiểm tra hoặc kiểm kê toàn bộ path không đọc được.
- PostgreSQL details ở FEAT-064 là owner-run; B0 original bytes và các canonical Parent share/Teacher routes không được xác minh độc lập trong phiên tài liệu này. Phiên lập Draft 5 (lịch sử) chỉ cập nhật plan; không chạy validation, owner-run command, test, DB, migration, provider hoặc network action.

## 2. Mục tiêu M2 và phạm vi

### 2.1. Mục tiêu đề xuất

Thiết lập nền tảng Parent/Teacher cho identity, tenant/role, profile, age provenance, owner/scope, asset, revision, durable job và lifecycle. Consent/share chỉ triển khai nếu quyết định owner và các cổng nguồn/chính sách được thỏa.

Mục tiêu là hợp đồng và ranh giới owner rõ ràng. Theo D-148 mục 1, “Admin tổ chức” ở SRS §20 và “School Manager” ở SRS §§3/31.3 là một role M2, code value theo D-148 là school_admin; quyền M2 chỉ theo SRS §20. Tên role giữa các phần SRS này không nhất quán. Không tạo FK hoặc SQL join xuyên owner/schema; cross-owner reference là typed opaque reference được xác minh qua application port.

Roadmap đề xuất B3 (manifest mới và owner/sign-off), B4b (consent sau khi xác định OI-05..08; trước khi mở gate phải từ chối REAL và LEGACY_UNCLASSIFIED), phần nền B6/B7/B10; B5 chỉ nếu còn requirement receipt legacy. B12 áp dụng xuyên pha.

### 2.2. Ngoài phạm vi

- M3: media intake, transcript/input revision và Parent line-sketch theo Q146.
- M4: story content, script, rewrite và đánh giá chất lượng sư phạm theo AC-65.
- M5: video, quota/usage/compute, provider, Modal/GPU.
- M6: lesson audience đầy đủ, occurrence/sample, roster, sharing/moderation/history/commerce/billing.
- Không khóa model/version, lịch line-sketch, consent policy hoặc lesson access thay owner.
- Không có quyền provider, Modal, GPU, external service hoặc network.

### 2.3. NFR-38 trong M2

Roadmap matrix liệt kê NFR-38 cạnh M2 nhưng không giao rõ toàn bộ AC-65 cho M2. Gán toàn bộ NFR-38 vào M2 chỉ từ profile/age là suy luận của kế hoạch, không phải quyết định owner. M2 chỉ đề xuất kiểm tra metadata vi-VN và tuổi 36–120 tháng được bảo toàn qua profile contract/revision và StoryRun. Theo D-148 mục 6, band reference null/“chưa cấu hình” không được tính là đạt NFR-38 hoặc AC-65. Không claim age-band catalog/version đã chốt, hay chất lượng Montessori-inspired, child-centered hoặc người lớn là guide/observer/supporter.

AC-65 yêu cầu: khi Parent/Teacher dùng profile cá nhân hóa và lesson để AI lập story/video, kết quả tuân age band/context đã duyệt, nội dung tiếng Việt, và video được tạo riêng theo tranh trẻ. NFR-38 phải ghi disposition PARTIAL cho M2. Story/AC-65 được đề xuất phân bổ vào M4; video/AC-65 vào M5. Đây là đề xuất lập pha cần owner xác nhận, không phải quyết định mặc định.

## 3. Subphase M2 đề xuất

Trạng thái dưới đây không thay thế Task Approval riêng cho từng pha. Chỉ S0-doc đã đóng ở phạm vi tài liệu; không có pha implementation nào được mở.

| Pha | Trạng thái | Phụ thuộc | Nội dung | Tiêu chí thoát có thể kiểm chứng | Stop gate |
|---|---|---|---|---|---|
| S0-doc | CLOSED — phạm vi tài liệu | Không | Đối chiếu nguồn, mapping schema, owner directions, B0 provenance và migration graph bằng source; không chạy command/DB. | Sáu tiêu chí thoát S0-doc: (1) mỗi requirement có source ID; (2) unknown được gắn nhãn; (3) route/table/owner/M2-AT có crosswalk; (4) B0 provenance có owner disposition hoặc tiếp tục block (D-144 §9.7 disposition trong giới hạn đã ghi); (5) giới hạn evidence được ghi; (6) không claim implementation approval. D-150 ghi cả sáu tiêu chí đã đạt trên evidence M2_S0_DOC_SOURCE_RECONCILIATION_20261106.md SHA-256 1BB71300A6A22487311A8D39EECB0EB1CE2664CB471EC2DAF45DA8DE2E244001; closure chỉ ở phạm vi tài liệu, không xác nhận implementation hoặc schema vật lý. | Không dùng closure này để chạy DB, migration, mypy hoặc mở pha khác. |
| S0-owner-run | DRAFT | S0-doc đóng; cần Task Approval riêng ghi tên DB, container, identity, người chạy, restore, bằng chứng synthetic-only, hash script chỉ đọc và command ceiling. | Owner-run chỉ đọc để đối soát schema vật lý/Alembic và ghi mypy baseline theo command/hash được duyệt. | DB identity khớp approval; bảng/version/chênh lệch current source được ghi; baseline mypy có output thật, command/version được ghi; phần chưa chạy vẫn NOT RUN. | Thiếu bất kỳ chi tiết hoặc approval nào thì không chạy lệnh hay ghi verdict; không chạy lệnh thay thế. Sai identity, dữ liệu không synthetic, hoặc cần write/migration thì dừng. Pha này không cấp phép migration. |
| S1a identity/tenant/profile/age | DRAFT | S0-doc và S0-owner-run đóng; cần Task Approval riêng. D-148 là hướng thiết kế, không phải approval S1a. | Identity/role assignment, tenant isolation, profile ownership và age provenance theo các directions D-148. | M2-AT-01/02/03/04A/04B/10/11 đạt theo tầng được duyệt; route test persistence dùng PostgreSQL thật và wiring thật. M2-AT-11 chỉ là acceptance đề xuất, không cấp quyền sửa mã. | Thiếu role matrix, profile owner hoặc age source trong Task Approval thì deny-by-default; không tự tạo route/policy. |
| S1b grant/revoke/consent | DEFERRED | Chỉ xem xét lại sau khi S1a đóng và owner quyết định tiếp; D-144 §9.3 và D-148 mục 8. | Scoped grant/revoke, purpose/expiry/audit và consent/data authorization chỉ được xét nếu owner mở lại bằng quyết định và approval riêng. | Hiện không có tiêu chí thoát đang hoạt động; M2-AT-05/06/07 NOT RUN. Nếu owner mở lại sau S1a, acceptance phải được ghi trong approval riêng. | Không bật share/consent hoặc chạy AT-05/06/07 trong trạng thái DEFERRED. REAL và LEGACY_UNCLASSIFIED bị từ chối theo D-144. |
| S2 owner/job/asset/revision/lifecycle | DRAFT | S1a; S1b nếu bật; migration target đã duyệt | Durable owner/scope refs, job/asset/revision, AiJobService mapping, idempotency/replay, cancel, restart/recovery, DELETE_PENDING/D-127. | M2-AT-08/09 đạt. N-1 phải test PostgreSQL mức route cho request → job → status, gồm request VÀ cancel qua route thật với wiring thật, không monkeypatch/override dependency; đạt trước khi thoát S2 và trước D9/client integration. B1 orphan có invalidation/reconciliation/read-exposure contract và regression trước dữ liệu non-synthetic/provider. | Orphan có thể được đọc/công bố như accepted result, job/aggregate lệch hoặc thiếu N-1 thì chưa thoát S2; evidence NOT RUN không đóng gate. |
| S3 freeze và đóng M2 | DRAFT | S1a, S1b theo disposition, S2 | Đối chiếu evidence và freeze contract; đóng OpenAPI P3 hai POST submit/cancel trước frontend/client. | Các M2-AT đã chạy pass hoặc có PARTIAL disposition do owner ghi; NFR-36 và NFR-38 có disposition; OpenAPI parity được kiểm; conditions được gán owner/phase; independent review ACCEPTED. Đề xuất điều kiện: disposition NOT RUN/DEFERRED của M2-AT-05/06/07 phải được owner chấp nhận rõ trong Task Approval S3 khi S1b vẫn DEFERRED. | Không tích hợp frontend/client khi OpenAPI P3 còn mở; không tự mở M3 hoặc bật workload. |

M2-AT-05/06/07 không được coi là đạt: theo D-148 mục 8, S1b hoãn và cả ba test đều NOT RUN. S2 và S3 giữ nguyên các cổng N-1 route PostgreSQL, B1 stale-owner orphan và OpenAPI P3; ghi trạng thái DRAFT không mở các cổng đó.

## 4. Traceability requirement → route/API → bảng → owner → acceptance

Route là candidate theo SRS v2.3-draft, chưa freeze. Tập route nền Parent/Teacher của M2 chỉ gồm năm route SRS §21.2 liệt kê tại §4.1 theo D-148 mục 4; nhóm route SRS §9.6 không tự tạo method contract. SRS §21.2 cũng có POST /v1/story-runs và POST /v1/story-runs/{run_id}/cancel; đây là route/service S2 ngoài năm route nền M2. N-1 là ngoại lệ duy nhất cho route test ngoài tập nền trong kế hoạch này và không mở rộng tập route nền Parent/Teacher. “Suy luận” là mapping chưa gắn trực tiếp; “chưa xác minh” là chưa có contract theo method.

| Requirement | Route/API và nguồn | Bảng/owner logic theo DTR | Acceptance |
|---|---|---|---|
| FR-PL-01 | POST /v1/parent/profiles; GET/PATCH /v1/parent/profiles/{profile_id} — SRS §21.2. SRS §9.6 có nhóm route /v1/me, nhưng §21.2 không có method contract cho nhóm đó; không suy ra method /v1/me. Identity được giải quyết nội bộ từ token theo D-148 mục 4. | parent.child_profiles, parent.profile_share_grants; be1.adult_identities, be1.organization_assignments; core audit — Parent/BE1/Core. | M2-AT-01/11; M2-AT-05 NOT RUN vì S1b DEFERRED. |
| FR-PL-02 | POST /v1/organizations/{org_id}/classes và POST /v1/classes/{class_id}/assignments — actor “Admin tổ chức”/“School Manager” (mã school_admin theo D-148 mục 1), quyền chỉ theo SRS §20; SRS §§20/3/31.3 không nhất quán tên role. POST /v1/classes/{class_id}/profiles — Teacher được phân công; SRS §21.2. List/read routes chưa xác minh. | be1.organizations, classrooms, organization_assignments, enrollments — BE1; consumer scope thuộc owner tương ứng. | M2-AT-02/04A/04B. |
| FR-PL-07 | Parent profile POST/GET/PATCH là các route SRS §21.2, không phải grant. Invite/accept/revoke route chưa có contract theo method trong tập năm route M2. | parent.profile_share_grants, parent.child_profiles, parent.data_authorizations; be1.managed_profiles — Parent/BE1. | Grant/share scope NOT COVERED trong M2 theo D-148 mục 8; M2-AT-05 NOT RUN vì S1b DEFERRED. |
| FR-PL-08 | Profile GET/PATCH — SRS §21.2. Grant/download/token/cache/revoke surface chưa có contract theo method trong tập năm route M2; lifecycle S2 giữ cổng riêng. POST /v1/story-runs và POST /v1/story-runs/{run_id}/cancel có trong SRS §21.2 nhưng là route/service S2 ngoài năm route nền M2; N-1 là ngoại lệ route test duy nhất ngoài tập nền. | parent.profile_share_grants, core.asset_lineage — Parent/Core. | Grant/share scope NOT COVERED trong M2 theo D-148 mục 8; M2-AT-06 NOT RUN vì S1b DEFERRED; AT-09 là gate N-1 của FEAT-064, không phải acceptance FR-PL-08. |
| FR-PL-25 | Parent profile POST/GET/PATCH và POST /v1/classes/{class_id}/profiles — SRS §21.2. Age-band catalog route — chưa xác minh. | parent.profile_revisions, be1.profile_revisions, age-band catalog — Parent/BE1/catalog owner chưa xác minh. | M2-AT-03/10. |
| BR-48 | Profile route không phải share route. Parent share invite/accept/revoke chưa có contract theo method trong tập năm route M2. | parent.profile_share_grants, parent.data_authorizations — Parent. | Grant/share scope NOT COVERED trong M2 theo D-148 mục 8; M2-AT-05/06 NOT RUN vì S1b DEFERRED; thiếu grant phải deny nếu S1b được mở lại. |
| BR-49 | POST /v1/organizations/{org_id}/classes; POST /v1/classes/{class_id}/assignments; POST /v1/classes/{class_id}/profiles — SRS §21.2; Admin tổ chức cho hai route đầu và Teacher được phân công cho route profile. | Lát M2: be1.organizations, be1.classrooms, be1.organization_assignments, be1.enrollments (BE1). Ngoài lát: be1.parent_groups và be1.parent_group_members (BE1, DTR §5.4.1), lesson.access_grants (Lesson, §5.5), lesson.delivery_recipients, lesson.delivery_feedback, lesson.feedback_replies (Lesson, §5.5/§14.1), billing.video_quota_grants và billing.video_quota_usage (Billing, §5.7). Các bảng parent group/lesson access không được M2-AT-05/06 nghiệm thu; hai test này chỉ nêu primitive parent.profile_share_grants và S1b đang hoãn. | M2-AT-01/02/04A/04B. PARTIAL: M2 chỉ là lát tenant/class foundation, không phải acceptance đầy đủ BR-49. |
| BR-57 | Age qua profile routes SRS §21.2; catalog/version route — chưa xác minh. | Profile revisions, age-band catalog — Parent/BE1/catalog owner chưa xác minh. | M2-AT-03/10. |
| BR-58 | SRS §30.4 map BR-58 với FR-PL-06/FR-PL-23; SRS §31.8.1 mô tả audience là nhóm Parent hoặc invitee cụ thể có thể thu hồi. Năm route nền M2 không kiểm nghiệm lesson audience; parent.profile_share_grants chỉ là primitive profile-share. | be1.parent_groups/parent_group_members (BE1); lesson.access_grants (Lesson); parent.profile_share_grants không đồng nghĩa lesson grant. | M2-AT-05/06 NOT RUN; grant/audience của BR-58 NOT COVERED trong M2 vì S1b DEFERRED theo D-144 §9.3 và D-148 mục 8. |
| NFR-34 | Áp dụng cross-cutting trên profile, assignment, grant, asset/job routes; share/token routes chưa có contract theo method trong tập năm route nền M2. | Parent, BE1, Core, AI Jobs qua contract/ports. | M2-AT-01/02/08/09 là các acceptance tương ứng; phần grant NOT COVERED trong M2 vì S1b DEFERRED, M2-AT-05/06 NOT RUN. Không claim toàn NFR-34 PASS. |
| NFR-36 | SRS §8/§31.9: Admin access child media, profile data và cross-role grant phải theo permission/reason/audit; feedback không lộ organization khác. Grant portion NOT COVERED trong M2 vì S1b DEFERRED; media access và cross-org feedback cũng không được năm route nền M2 chứng minh. | BE1/Parent/Core/Lesson owners. | PARTIAL theo D-143; M2-AT-07 NOT RUN do S1b DEFERRED. Child media→M5 và cross-org feedback→M6 vẫn là mapping đề xuất, owner chưa chọn. |
| NFR-38 | SRS §8/§31.9 AC-65; M2 profile/age metadata là phần nền. Story và video quality chưa được roadmap phân bổ rõ toàn bộ. | Profile metadata M2; Story M4/Video M5 là phân bổ đề xuất cần owner xác nhận. | M2-AT-10 chỉ kiểm metadata; band reference null/“chưa cấu hình” không tính là đạt NFR-38/AC-65 theo D-148 mục 6; NFR-38 PARTIAL tới khi owner disposition và xác nhận phase AC-65. |

### 4.1. Route candidates theo SRS

SRS §21.2 nêu đúng năm route nền M2 theo D-148 mục 4:

- POST /v1/parent/profiles
- GET/PATCH /v1/parent/profiles/{profile_id}
- POST /v1/organizations/{org_id}/classes
- POST /v1/classes/{class_id}/assignments
- POST /v1/classes/{class_id}/profiles

SRS §9.6 nêu /v1/me như một nhóm route, nhưng §21.2 không có method-level contract cho nhóm này; không tự thêm GET /v1/me. /v1/teacher/profiles chỉ xuất hiện ở §9.6, không thuộc năm route nền M2. Không có route xóa profile Parent hoặc Teacher trong M2; FR-C-10 và BR-35 NOT COVERED. Không có list/read route bổ sung ngoài Parent profile GET/PATCH nêu trên. Cô lập Teacher-profile reads không kiểm tra được qua các route M2 và được ghi NOT RUN. Identity fixture Parent/Teacher là seed, không phải route; identity được giải quyết nội bộ từ token. Client không có cách khám phá org_id/class_id trước S3. Placeholder spelling được chốt tại OpenAPI freeze S3.

### 4.2. Định nghĩa M2 acceptance tests

Các test dưới đây là kế hoạch, chưa chạy. Route acceptance phải dùng PostgreSQL task-owned, app composition, authentication và dependency wiring thật. Không monkeypatch _build_child_binding hoặc override dependency cần kiểm. Nếu canonical route chưa được owner chọn/duyệt, chỉ domain/service acceptance có thể được xét; route acceptance chưa chạy và gate S1b còn mở. AT-09 là crosswalk FEAT-064 N-1, không phải acceptance FR-PL-08.

| ID | Requirement/pha | Given / When / Then | Tầng | DB task-owned |
|---|---|---|---|---|
| M2-AT-01 | FR-PL-01, BR-49, NFR-34; S1a | Given Parent/Teacher/Admin có role/assignment hợp lệ hoặc thiếu/thu hồi; when đọc/ghi resource qua một trong năm route nền M2; then chỉ role/scope hợp lệ được phép, denial không lộ metadata ngoài scope, audit metadata-only. Token Platform Admin, Operator hoặc Admin nội dung bị từ chối trên cả năm route. Không có grant thì mọi cross-role read bị từ chối. | Domain/service unit, HTTP contract, route PostgreSQL. | Có cho route/persistence; không cho unit. |
| M2-AT-02 | FR-PL-02, BR-49; S1a | Given actor không có assignment, class không tồn tại, class thuộc organization khác, hoặc actor gọi POST /v1/organizations/{org_id}/classes với org_id không khớp assignment active của actor (kể cả organization khác hoặc không tồn tại); when gọi route; then mọi trường hợp trả cùng denial/status/error shape, không lộ existence/content. Với {org_id}, server so sánh với assignment active; với {class_id}, server suy ra organization từ class record rồi so assignment. Không lấy organization từ claim hoặc header. | Unit matrix và route integration wiring thật. | Có cho integration. |
| M2-AT-03 | FR-PL-25, BR-57; S1a | Given tuổi nguyên 35, 36, 120 hoặc 121 tháng; when tạo hoặc cập nhật profile; then 36 và 120 được chấp nhận, còn giá trị mới 35 và 121 bị từ chối ở application layer. Band reference null và hiển thị “chưa cấu hình”; trạng thái null không đạt NFR-38/AC-65 theo D-148 mục 6; không dùng child_age.py. Hàng cũ được giữ nguyên, không sửa; chỉ revalidate khi trường tuổi đổi. Test không giả định DB từ chối 121 vì CHECK hiện tại 36–155 còn nguyên tới khi có migration được duyệt riêng. | Domain/contract unit và repository integration. | Có cho persistence. |
| M2-AT-04A | FR-PL-02, BR-49; S1a; SRS §21.2 | Given Admin tổ chức thuộc đúng org và còn capacity cùng một Teacher active; when POST /v1/organizations/{org_id}/classes rồi POST /v1/classes/{class_id}/assignments; then class và assignment được tạo theo response contract. Given capacity hết; when Admin gửi POST tạo class; then không tạo class/assignment; chỉ kỳ vọng CLASS_CAPACITY_REACHED nếu contract hiện hành định nghĩa mã này. Tách riêng: Given Teacher gọi route Admin để tạo assignment; when gửi request; then authorization deny và không tạo assignment; không gán mã capacity cho lỗi quyền. Given class đó đã có một Teacher active; when thử assign Teacher thứ hai cho cùng class; then expected outcome là quyết định F-2 được ghi trong Task Approval S1a nếu mã hiện tại chưa ép đúng một Teacher active; kế hoạch không tự định kết quả thay owner. | Route PostgreSQL acceptance với actor đã xác thực và wiring thật. | Có. |
| M2-AT-04B | FR-PL-02, BR-49; S1a; SRS §21.2 | Given Teacher được phân công vào class cùng tenant và expected class revision hiện tại; when POST /v1/classes/{class_id}/profiles với trường profile có cấu trúc; then tạo 201 profile/enrollment ref và tối đa một enrollment active. Given Teacher không được phân công, sai tenant hoặc Admin gọi route Teacher; when gửi command; then deny theo error envelope, không tạo profile/enrollment và không lộ dữ liệu ngoài scope. | Route PostgreSQL acceptance với actor Teacher đã xác thực và wiring thật. | Có. |
| M2-AT-05 | FR-PL-07, BR-48; S1b DEFERRED — NOT RUN | Given grant pending/active/revoked/expired với purpose/scope; when đọc profile; then chỉ grant active đúng scope cho phép. Đây là acceptance intent nếu owner mở lại S1b bằng quyết định và approval riêng; hiện chưa chạy. | Unit trước khi được mở; route PostgreSQL chỉ sau route được duyệt. | NOT RUN hiện tại. |
| M2-AT-06 | FR-PL-08, BR-48, NFR-34 grant portion; S1b DEFERRED — NOT RUN | Given field-scoped grant liên kết asset/token/cache/job; when revoke; then lần đọc/tải mới, token/cache access và job chưa accepted bị chặn, audit không ghi content/token. Đây là acceptance intent nếu owner mở lại S1b bằng quyết định và approval riêng; hiện chưa chạy. | Domain/service; API/asset/job integration sau route approval; không gọi provider. | NOT RUN hiện tại. |
| M2-AT-07 | NFR-36; S1b DEFERRED — NOT RUN | Given Admin thiếu permission, scope hoặc reason code; when gọi operation profile/grant thuộc M2; then deny và không lộ resource. Given permission/scope/reason hợp lệ theo policy owner đã duyệt; when gọi operation; then chỉ scope được cấp được phép và audit metadata-only. Media access và cross-org feedback không tính vào M2. Acceptance intent này không chạy khi S1b DEFERRED; NFR-36 vẫn PARTIAL theo D-143. | Domain/service; route PostgreSQL integration chỉ sau route/policy được duyệt. | NOT RUN hiện tại. |
| M2-AT-08 | Roadmap Mốc 2 (owner-lock, cancel, restart, ownership của job), D-127, NFR-34 — nguồn roadmap/decision, không phải FR-PL; S2. POST /v1/story-runs và POST /v1/story-runs/{id}/cancel là route/service S2 ngoài năm route nền M2 (SRS §21.2); chỉ N-1 là ngoại lệ route test ngoài tập nền. | Given synthetic Parent/Teacher cùng owner lock có quyền hợp lệ; when concurrent separate POST /v1/story-runs requests submit cùng active owner; then có không hơn một active run/job/receipt hoặc side effect; không áp đặt loser status/error nếu contract chưa định nghĩa. Given run qua PREPARATION_REVIEW; when POST /v1/story-runs/{id}/cancel; then áp dụng D-127: DELETE_PENDING, nhả active-owner trong transaction, giữ result/assets/receipts và không coi là đã xóa. Replay/cancel lặp không tạo side effect trùng. Sau đó dừng tiến trình hệ điều hành thật, khởi động process mới với app composition mới trên cùng DB; recovery không tạo duplicate và stale result không được accepted. Recreate object trong cùng process không tính là restart. | PostgreSQL integration qua route, process stop/start thực, composition/repository/wiring thật. | Có. |
| M2-AT-09 | FEAT-064 N-1 route crosswalk; S2 (không phải FR-PL-08) | Given child request tổng hợp và actor/device hợp lệ; when POST /api/be1/v1/assistance-requests, GET /api/be1/v1/organizations/{organization_id}/sessions/{session_id}/assistance-requests/{assistance_id}/status và POST /api/be1/v1/assistance-requests/{assistance_id}/cancel đi qua route thật; then auth, app composition, dependency wiring và PostgreSQL đều thật, không monkeypatch _build_child_binding hoặc override dependency cần kiểm. Bao phủ các trạng thái: success chỉ được expose sau durable committed SUCCEEDED; timeout phải giữ durable request/job/receipt facts nhưng không có authoritative successful result, không tự định nghĩa transition; orphan theo FEAT-064 approval là analysis invocation SUCCEEDED trong khi job RUNNING, không có result ref hoặc authoritative receipt, nên API/status không expose accepted. Dừng process hệ điều hành thật, khởi động app process mới cùng DB và kiểm tra recovery/status không công bố stale/orphan result như accepted. Timeout/recovery/terminal semantics chưa có owner quyết định thì giữ gate mở, không bịa status/error. Bắt buộc trước khi thoát S2 và trước D9 hoặc frontend/client integration. | PostgreSQL route integration qua real app composition/auth/dependency wiring và process restart. | Có, bắt buộc. |
| M2-AT-10 | FR-PL-25, BR-57, NFR-38; S1a | Given locale vi-VN, tuổi nguyên 36/120 và hàng cũ ngoài khoảng; when serialize/persist/read profile revision và thử tạo StoryRun; then metadata được giữ, hai biên hợp lệ; hàng cũ ngoài 36–120 không đủ điều kiện tạo StoryRun và bị từ chối rõ ràng, không clamp. Test không giả định DB chặn 121. Hành vi StoryRun với tuổi cũ 121–155 chưa được xác minh. POST /v1/story-runs và POST /v1/story-runs/{run_id}/cancel là route/service S2 ngoài năm route nền M2; chỉ N-1 là ngoại lệ route test ngoài tập nền, không bổ sung StoryRun vào route set. Không đánh giá chất lượng AC-65 trong M2. | Contract/unit và persistence integration. | Có cho persistence. |
| M2-AT-11 | FR-PL-01; S1a; D-144 §9.3 và D-148 F-6 | Given yêu cầu tạo profile với data_origin REAL, LEGACY_UNCLASSIFIED, hoặc thiếu consent record; when gửi yêu cầu; then bị từ chối và không tạo profile. Chỉ profile có data_origin synthetic hợp lệ mới được tạo khi cặp origin/consent thỏa contract được owner duyệt. Test không giả định default data_origin trong mã; cách reconcile default và origin/consent CHECK tiếp tục là F-6 cần Task Approval S1a quyết. | Route PostgreSQL acceptance với actor đã xác thực và wiring thật. | Có. |

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

Provenance theo Draft 9: các khẳng định dưới đây về backend/src/sketch2life/infrastructure/story_run_lite/tables.py và migrations 20261102_story_run_lite.py / 20261103_story_upload_compat.py được ghi từ source bởi phiên soạn trước. Các path này nằm ngoài allowlist S0-doc theo evidence §6 và chưa được S0-doc xác minh. Phiên Draft 9 không đọc lại các file đó; các khẳng định tương ứng tiếp tục là chưa xác minh.

- Source StoryRun-lite hiện có physical story.runs. Baseline đã cho phép DELETE_PENDING và FAILED; migration 20261104_story_revisions thêm child_age_months nullable với check 36–120 và mở rộng run_state cho SCRIPT_GENERATING, SCRIPT_GENERATION_UNKNOWN, SCRIPT_REVIEW và VIDEO_ADMISSION_PENDING. DELETE_PENDING/FAILED không phải các state mới do migration này thêm. Đây là static source mapping, không phải bằng chứng migration đã chạy.
- DTR mô tả logic story.runs với story_run_id, profile/owner refs và current_story_revision_ref; StoryRun-lite hiện dùng cột physical run_id. Giữ mapping run_id → story_run_id là crosswalk cần owner/chủ schema đối chiếu, không tự đổi tên hay giả định dữ liệu đã chuyển.
- Source tables.py đã khai báo physical story.review_decisions. Migration 20261104_story_revisions tạo physical story.story_revisions, story.story_scenes và story.story_revision_reviews; bảng mới story_revision_reviews khác với story.review_decisions đã có. DTR mô tả logic revisions/scenes/review_decisions; field/key/owner mapping với các bảng physical chưa được chứng minh tương đương. S0-doc phải lập crosswalk và đánh dấu unknown đến khi owner duyệt.
- Giữ mapping storyrun_upload_sessions → core.upload_sessions cùng upload parts/receipts; ghi owner columns, asset refs và history. Không đổi nghĩa hoặc xóa history âm thầm.
- Parent parent.child_profiles, parent.profile_revisions, parent.profile_share_grants và parent.data_authorizations vẫn là logical target trong DTR, không phải module/bảng hiện có được migration Story revisions tạo.
- B3 manifest/sign-off là đề xuất tới khi owner ký đúng bytes.
- A2 ghi còn 58 synthetic rows sau lỗi teardown. Owner chọn giữ, copy/di trú có mapping và approval, hoặc cleanup qua approval riêng. Mặc định giữ nguyên; không reset shared sketch2life.
- Trước migration: DB task-owned, physical schema inventory, target Alembic graph/revision, snapshot/restore expectation, exact approval. Kết quả B2 không chứng minh trạng thái DB hiện tại.

### 5.3. Alembic graph và command ceiling

Repository có nhiều root/head và depends_on; không dùng upgrade heads làm đích M2 mặc định. Provenance theo Draft 9: các khẳng định về tables.py và migrations 20261102_story_run_lite.py / 20261103_story_upload_compat.py trong bảng dưới được phiên soạn trước ghi từ source; các file nằm ngoài allowlist S0-doc theo evidence §6 và chưa được S0-doc xác minh. Phiên Draft 9 không đọc lại các file đó; các khẳng định tương ứng tiếp tục là chưa xác minh. Ancestry của nhánh StoryRun-lite theo source đã đọc:

| Revision trên nhánh | down_revision | branch_labels | depends_on | Vai trò |
|---|---|---|---|---|
| 20261104_story_revisions | 20261103_story_upload_compat | None | None | Endpoint hiện thấy của nhánh StoryRun-lite trong source; không khẳng định là head duy nhất của toàn repository. |
| 20261103_story_upload_compat | 20261102_story_run_lite | None | None | Compatibility migration cho Story upload. |
| 20261102_story_run_lite | None | story_run_lite | 20261102_pv_0001 | Gốc nhánh StoryRun-lite, phụ thuộc pilot vision. |
| 20261102_pv_0001 | None | pilot_vision | 20261101_be1_age_0001, 20261015_ai_0001 | Gốc nhánh pilot_vision và hai dependency được khai báo trong source. |

Migration 20261104_story_revisions nối sau 20261103_story_upload_compat; theo source, nó thêm tuổi vào run, mở rộng state constraint/receipt operation và tạo bảng revision/scene/review mới nêu ở §5.2. Đây là diff source-level; migration không được thực thi trong task tài liệu. Theo source, downgrade khôi phục state check hẹp hơn. Nếu row còn dùng state mới được chấp nhận, việc khôi phục constraint có thể thất bại; không chạy downgrade và không khẳng định runtime outcome. Đây là giới hạn rollback từ source, không phải execution evidence.

Offline-check owner-run được ghim tại §1.3 ghi upgrade plan 27 bước từ DB rỗng và 9 observed version rows/9 script_heads tại thời điểm log; các con số này là dữ kiện lịch sử, không phải cổng pass/fail. Log ghi không có DB connection, network hoặc migration execution. script_heads trong log kết thúc ở 20261103_story_upload_compat và không có 20261104_story_revisions, nên đây không phải graph hiện tại hoặc bằng chứng migration đã chạy. Phiên lập Draft 5 (lịch sử) không chạy Alembic, không kết nối DB và không chạy mypy; migration execution, graph đối soát live và M2 mypy baseline đều NOT RUN. Không thay các kết quả còn thiếu bằng lệnh khác.

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

1. Mỗi requirement §4 có route status, bảng logic, owner, mã M2-AT và evidence. NFR-36 phải có owner disposition PARTIAL cho M2 và ghi rõ child media access được đề xuất hoãn M5, cross-org feedback được đề xuất hoãn M6; M2-AT-07 không chứng minh phần hoãn. NFR-38 phải có disposition PARTIAL; M2 chỉ claim metadata tuổi/ngôn ngữ, AC-65 story/video là phân bổ M4/M5 đề xuất chờ owner xác nhận. BR-58 NOT COVERED trong M2 theo D-148 mục 8; audience lesson cho nhóm Parent/invitee thuộc M6. PARTIAL không phải PASS.
2. Identity, role, tenant, profile ownership, Admin class/assignment, Teacher profile/enrollment, age provenance và synthetic-only/consent đạt M2-AT-01/02/03/04A/04B/10/11 với positive/negative tests; DB thật cho route/persistence.
3. Grant/consent theo quyết định 3/OI gate; thiếu grant/policy thì deny, REAL và LEGACY_UNCLASSIFIED bị chặn nếu B4b hoãn.
4. Lifecycle đạt M2-AT-08/09; request và cancel phải được gọi qua route thật. N-1 PostgreSQL route test với wiring thật bắt buộc trước khi thoát S2 và trước D9/client integration; B1 orphan có reconciliation/read-exposure contract và regression trước dữ liệu non-synthetic/provider.
5. Target migration/schema inventory/data disposition/rollback limits được owner phê duyệt; DB/source/snapshot gate lệch thì dừng. Offline-check là historical fact-only; Alembic execution, live graph reconciliation và M2 mypy baseline chưa chạy nên không đóng gate.
6. OpenAPI request/response/error parity được freeze trước client integration; P3 đóng trong S3.
7. Evidence lưu tại feature evidence path được approval chỉ định; PARTIAL/NOT RUN/owner-run provenance ghi đúng. Plan review và implementation review là hai việc riêng.
8. Không mở M3–M6, không bật provider/Modal hoặc workload.
9. Draft 9 vẫn DRAFT / AWAITING INDEPENDENT REVIEW; chưa có independent review, owner approval hay implementation approval.

## 8. Candidate allowlist theo subphase

Draft 4 báo cáo 49 path đã được xác nhận tồn tại; phiên lập Draft 5 (lịch sử) không kiểm lại toàn bộ danh sách này. Các path dưới đây là candidate trong kế hoạch, trừ cột "Path mới", ghi chưa xác minh. Bảng chỉ để owner/reviewer xem xét trước Task Approval; không cấp quyền sửa. Các nguồn mới ở S0-doc chỉ đọc, không mở allowlist thực thi. Không dùng wildcard.

Quy ước:

- **Chỉ đọc:** tham chiếu hoặc baseline hồi quy; không được sửa nếu Task Approval không nêu đích danh file và lý do.
- **Candidate có thể sửa:** chỉ được sửa khi Task Approval của đúng pha liệt kê file đó, kèm hash trước khi sửa.
- **Path mới:** file chưa tồn tại; tên và hash phải có trong approval trước khi tạo. Test hiện có là baseline hồi quy chỉ đọc; test M2 là file mới.
- **Hồ sơ governance** (CONTEXT, DECISIONS, STATUS, TASK_APPROVAL của FEAT-063/FEAT-064, ledger) chỉ do phiên ghi (Codex) cập nhật sau lệnh của owner. Chúng nằm ngoài allowlist của mọi phiên thực thi và chỉ đọc đối với phiên thực thi.
- Draft 1–8 của plan này là đầu vào chỉ đọc; Draft 9 là artifact đang chờ review độc lập, chưa được duyệt.

| Pha | Chỉ đọc | Candidate có thể sửa | Path mới (chưa xác minh) | Exclusions / hard stop |
|---|---|---|---|---|
| S0-doc | Mọi tài liệu pin ở §1; features/FEAT-063-system-architecture-rearchitecture/SOURCE_REGISTER.md; features/FEAT-063-system-architecture-rearchitecture/evidence/COMMIT_WHITESPACE_NORMALIZATION_20261103.md; Draft 1–8 của plan này; backend/alembic/versions/20261104_story_revisions.py; backend/src/sketch2life/infrastructure/persistence/core_models.py; .claude/handoff/logs/GB2_T12_OFFLINE_20261105A/offline-check.txt (local, git-ignore; Draft 8 từng báo ENOENT, Draft 9 đọc bytes hiện tại và re-verify hash 6FF16B2E77EE7DB7CE18521484B92FAA9B40F685393D35A7746E74236313E143 khớp); hồ sơ governance. | Không có file hiện có. | Kế hoạch tiếp theo nếu owner yêu cầu; evidence bổ sung chỉ khi được duyệt (tên chưa xác minh). | Không sửa source/test/migration/SRS/DTR/roadmap/governance. Cần DB hoặc file ngoài approval thì dừng. |
| S0-owner-run | backend/alembic/env.py; backend/alembic/versions/20261014_0002_be1_runtime.py; backend/alembic/versions/20261015_ai_0001_ai_jobs_schema.py; backend/alembic/versions/20261028_ll_0001_lesson_library.py; backend/alembic/versions/20261031_be1_synthetic_eligibility.py; backend/alembic/versions/20261101_be1_age_provenance.py; backend/alembic/versions/20261102_pilot_vision.py; backend/alembic/versions/20261102_story_run_lite.py; backend/alembic/versions/20261103_story_upload_compat.py; backend/alembic/versions/20261104_story_revisions.py; backend/src/sketch2life/infrastructure/persistence/be1_models.py; backend/src/sketch2life/infrastructure/persistence/core_models.py; backend/src/sketch2life/infrastructure/ai_jobs/sql/tables.py; backend/src/sketch2life/infrastructure/story_run_lite/tables.py. core_models.py là Core hiện có; chưa tìm thấy module persistence Parent trong source đã rà. Chỉ đọc. | Không có; allowlist ghi repo rỗng. | Đường dẫn evidence output và script owner-run (hash ghim trong approval) — chưa xác minh. | Chưa có tên DB/container/identity, người chạy, restore, bằng chứng synthetic-only, hash script chỉ đọc, command ceiling và approval thì không chạy. Không migration, không shared DB, không ghi source. |
| S1a | backend/src/sketch2life/infrastructure/identity/firebase_token_verifier.py; backend/src/sketch2life/domain/child_age.py; backend/src/sketch2life/contracts/schemas/child_learning_profile.py (backend/src/sketch2life/domain/child_age.py và backend/src/sketch2life/contracts/schemas/child_learning_profile.py chỉ chuyển sang candidate sửa nếu approval đổi chính sách tuổi/contract); baseline hồi quy: backend/tests/unit/test_profile_age_invariant.py; backend/tests/unit/test_age_provenance_columns.py; backend/tests/unit/test_child_learning_profile_contract.py; backend/tests/contract/test_be1_synthetic_pilot.py; backend/tests/integration/test_be1_age_provenance_postgres.py. | backend/src/sketch2life/application/ports/identity.py; backend/src/sketch2life/application/services/be1_runtime.py; backend/src/sketch2life/interfaces/http/routers/be1_registry.py; backend/src/sketch2life/interfaces/http/routers/be1_records.py; backend/src/sketch2life/infrastructure/persistence/be1_models.py (chỉ nếu schema đổi và migration được duyệt). | Module/route/bảng/migration Parent identity-profile và test M2-AT-01/02/03/04A/04B/10/11. | Không sửa .env, credential, Firebase secret, shared DB, FEAT-064, M3–M6. |
| S1b | backend/tests/unit/test_member_fact_consent_rules.py (baseline); các file S1a sau khi S1a đóng (hash ghim lại). | backend/src/sketch2life/application/ports/identity.py; backend/src/sketch2life/infrastructure/persistence/core_store.py; backend/src/sketch2life/interfaces/http/routers/be1_registry.py; backend/src/sketch2life/interfaces/http/routers/be1_records.py. Các file dùng chung với S1a chỉ sửa sau khi S1a đóng; không sửa song song. | Module share-grant/data-authorization, route canonical, migration và test M2-AT-05/06/07. | REAL/LEGACY_UNCLASSIFIED bị deny nếu owner/OI gate chưa đóng. BE1 consent không tự động là Parent authorization. |
| S2 | Mặc định chỉ đọc: backend/src/sketch2life/application/ports/ai_jobs.py; backend/src/sketch2life/application/services/ai_jobs.py; backend/src/sketch2life/domain/ai_jobs/model.py; backend/src/sketch2life/infrastructure/ai_jobs/sql/tables.py; backend/src/sketch2life/infrastructure/ai_jobs/sql/repository.py; backend/src/sketch2life/infrastructure/ai_jobs/worker.py; backend/src/sketch2life/infrastructure/ai_jobs/reconciler.py; backend/src/sketch2life/domain/story_run_lite.py; backend/src/sketch2life/application/services/story_run_lite.py; backend/src/sketch2life/infrastructure/story_run_lite/repository.py; backend/src/sketch2life/infrastructure/story_run_lite/tables.py; baseline hồi quy: backend/tests/unit/test_ai_job_lifecycle.py; backend/tests/integration/ai_jobs/test_restart_recovery.py; backend/tests/integration/ai_jobs/test_owner_fence.py; backend/tests/integration/test_story_run_lite_postgres.py; backend/tests/integration/test_story_run_lite_replay_concurrency.py; backend/tests/integration/test_pilot_assistance_routes_t9.py (dùng để đối chiếu: test này monkeypatch `_build_child_binding` ở dòng 257 nên không thay N-1). | Không có mặc định. File hiện có ở cột Chỉ đọc chỉ chuyển sang candidate sửa khi Task Approval nêu từng file và lý do (ví dụ mapping của quyết định 5 hoặc reconciliation B1). | Module Parent aggregate/asset/revision; migration; test N-1 qua route request và cancel thật (PostgreSQL thật, wiring thật, không monkeypatch); regression B1 orphan; evidence S2. | Không sửa backend/tests/integration/ai_jobs/test_migrations.py hoặc fixture tạo/xóa DB khi chưa có approval riêng; không sửa backend/alembic/versions/20261103_story_upload_compat.py; không chấp nhận orphan. |
| S3 | backend/src/sketch2life/interfaces/http/story_run_lite_openapi.json; backend/src/sketch2life/contracts/schemas/story_run_lite.py (liên quan P3 chưa xác minh); baseline: backend/tests/contract/test_story_run_lite_api.py; backend/tests/integration/test_pilot_assistance_routes_t9.py; backend/tests/integration/test_be1_postgres_api.py. | backend/src/sketch2life/interfaces/http/routers/assistance_requests.py (OpenAPI P3 hai POST submit/cancel). | Test OpenAPI parity, artifact OpenAPI sinh ra nếu cần, evidence S3, route module/test M2 — chưa xác minh. | Frontend/client chờ OpenAPI P3. Không sửa ngoài approval; không M3–M6, provider, Modal. |

### Việc Task Approval S1a phải quyết

Các mục dưới đây chưa được xác minh đầy đủ trong mã: S0-doc chỉ đọc tài liệu, nên mô tả hành vi mã được ghi nhận theo D-148 chứ chưa được kiểm tra trực tiếp trong source code. Đây là các câu hỏi cần giải quyết/ghi trong Task Approval S1a; danh sách này KHÔNG cấp quyền sửa file. Mọi file thực thi vẫn phải được nêu đích danh trong approval.
- D-148 mục 1: giữ role “Admin tổ chức” = “School Manager”, mã school_admin, và chỉ các quyền SRS §20; ghi nhận tên gọi SRS §§20/3/31.3 không nhất quán.
- D-148 mục 6: band reference null/“chưa cấu hình” không được tính là đạt NFR-38 hoặc AC-65.

- F-1: D-148 ghi nhận route assignment trong mã là POST /organizations/{org}/assignments, với class trong body và prefix khác, so với SRS POST /classes/{class_id}/assignments. Task Approval phải chốt cách đưa route triển khai khớp contract SRS.
- F-2: D-148 ghi nhận mã chưa ép đúng một Teacher phụ trách mỗi class và M2-AT-04A chưa có case Teacher thứ hai. Task Approval phải ghi rõ acceptance cho cardinality này.
- D-148 mục 5: cùng một denial phải áp dụng khi không có assignment, class không tồn tại, hoặc class thuộc organization khác. D-148 ghi nhận mã hiện trả hai 403 code ADULT_NOT_ASSIGNED và SCOPE_DENIED; mã chưa được S0-doc kiểm tra trực tiếp. Task Approval phải ghi cách dùng một response/code thống nhất mà không lộ existence.
- F-4: D-148 ghi nhận route tạo profile trong mã cho phép school_admin, trong khi M2-AT-04B yêu cầu school_admin/Admin gọi Teacher route phải bị từ chối. S0-doc chưa xác minh trực tiếp hành vi trong mã.
- F-6: D-148 ghi nhận route tạo profile yêu cầu consent record và origin/consent CHECK không khớp synthetic-only, deny REAL; giá trị data_origin mặc định chưa xác minh. Task Approval phải ghi cách giữ scope synthetic-only và xác minh origin/consent trước khi có triển khai.
- Nguồn tuổi: D-148 mục 6 chọn hướng M2 chỉ dùng 36–120 tháng, nhưng ghi nhận ba rule tuổi trong mã là 36–155, 0–107 và 36–120. Task Approval phải chỉ rõ nguồn có thẩm quyền cho M2 và cách reconcile các rule; S0-doc chưa kiểm tra trực tiếp mã.

Trước mỗi launch, coordinator phải xác minh lại từng path, chốt path mới, snapshot/hash và xin owner approval. Bảng này không thay allowlist cuối cùng của Task Approval.

## 9. CẦN QUYẾT ĐỊNH CỦA OWNER

D-145 chỉ chấp nhận Draft 7 làm planning basis cho S0-doc; D-150 đã đóng S0-doc ở phạm vi tài liệu. D-147 và D-149 ghi nhận các sửa evidence; D-148 là hướng thiết kế chứ không phải approval S1a. D-146 xác nhận không có implementation approval. Cột “Mặc định đề xuất, không phải quyết định” vẫn chỉ là gợi ý; direction đã quyết theo D-142..D-150 được ghi riêng ở cột trạng thái.

| # | Trạng thái theo D-142..D-150 | Lựa chọn | Hệ quả | Pha bị chặn | Mặc định đề xuất, không phải quyết định |
|---|---|---|---|---|---|
| 1. DB task-owned | Hướng đã quyết theo D-144 §9.1; chi tiết còn mở | Chỉ đọc S0-owner-run dùng total BE Docker database; các pha ghi S1a/S2 dùng database riêng trong cùng container. Task Approval S0-owner-run còn phải ghi tên DB, identity, người chạy, restore và bằng chứng synthetic-only. | Không dùng shared/write DB trước khi identity và approval phù hợp được ghi; thiếu identity thì không migration/route acceptance PostgreSQL. | S0-owner-run và pha cần persistence. | DB mới rỗng, task-owned, identity pin trong approval, owner chạy. |
| 2. 58 synthetic rows | Đã quyết theo D-144 §9.2 | Giữ nguyên cả 58 hàng synthetic; không cleanup. | Copy/cleanup có thể mất history/đổi owner; không được tự làm. | S0-owner-run/S2. | Giữ nguyên, không cleanup. |
| 3. B4b/OI-05..08 | Hoãn đã quyết theo D-144 §9.3; xem xét lại sau khi S1a đóng theo D-148 mục 8 | Hiện hoãn consent/share và OI-05..08; synthetic-only, deny REAL và LEGACY_UNCLASSIFIED. S1b đang DEFERRED, không phải pha đã mở. | SRS hiện hành §29.2, dòng 1130–1133 vẫn để mở chuyên gia/privacy, retention/backup, region/cross-border và production/operations. Chưa có authority cho consent hoặc dữ liệu thật. | S1b và dữ liệu thật. | Đề xuất cho lần xem xét sau: deny REAL; primitive chỉ sau approval riêng. |
| 4. B5 receipt legacy | Tạm hoãn theo D-144 §9.4; nhu cầu consumer còn mở | Giữ B5 unopened đến khi consumer xác nhận cần; đây không phải kết luận B5 không được dùng. | Nếu cần: xác định consumer, payload, retention, mapping; nếu không: disposition chính thức. | S1b/S2 nơi receipt dùng. | Không mở B5 khi chưa có consumer xác nhận. |
| 5. Schema convergence | Hướng không migrate/preserve history đã quyết theo D-144 §9.5; mapping còn mở | Không migrate schema; giữ history; mapping được soạn để owner review nhưng chưa được chọn. | Mapping không rõ có thể mất liên kết/history hoặc tạo hai nguồn sự thật. | S0-owner-run/S2 migration. | Giữ history; chưa migrate khi chưa có mapping ký duyệt. |
| 6. Mypy baseline | Hướng read-only baseline đã quyết theo D-144 §9.6; command và output còn mở | Owner-run một baseline read-only, ghi command/version; M2 không thêm diagnostic. Chưa có command/output trong Draft 8. | test_be1_postgres_api.py hiện NO VERDICT; crash tool không phải pass. Quyết định không miễn kiểm tra lỗi mới. | S0-owner-run; S1/S2 nếu sửa target; S3 closeout. | Đo baseline read-only có approval, cùng command/version, không thêm lỗi; không suy diễn phần chưa chạy. |
| 7. B0 provenance | Đã quyết theo D-144 §9.7; S0-doc đóng theo D-150 | Owner xác nhận normalized bytes tương đương chỉ cho B0 plan: original hash 03AEA386B8545624100688B68AA828A84CD154B47857CB5E98FB06354D6BB582; current hash 773C4A8340C8E33AE39764D920B042AC19BACBAF6DC561FE9D5D3DFFCC4B5A5A. So sánh do coordinator thực hiện, không phải independent reviewer. | Xác nhận không mở rộng sang bảy file khác trong normalization evidence, không xác nhận snapshot, và không thay independent review. | Không còn chặn S0-doc; các requirement khác dựa B0 vẫn chịu source limits. | Owner ghi xác nhận qua approval ghim evidence; không sửa pin để làm hash khớp. |
| 8. Baseline review | Đã xác nhận theo D-142 cho review Draft 7; Draft 8 dùng cùng HEAD | dd70685eae58aaaefea3e567f5c23d09345a8513 là review baseline; nếu HEAD thay đổi thì phải xác nhận lại. Đây chỉ là baseline, không phải scope approval. | Draft 8 được lập trên đúng HEAD này; hash phù hợp không thay owner review Draft 8. | Baseline của review kế hoạch. | Không có mặc định đề xuất; nếu HEAD đổi thì xác nhận lại theo D-142. |
| 9. NFR-36 disposition | PARTIAL đã quyết theo D-143; milestone mapping còn mở | Giữ PARTIAL cho M2. Child media→M5 và cross-org feedback→M6 vẫn là đề xuất, owner chưa chọn. | NFR-36 gồm access child media/profile và cross-role grant theo permission/reason/audit; M2-AT-07 NOT RUN khi S1b hoãn; không claim toàn requirement PASS. | M2-AT-07, media và feedback phase tương ứng. | Không claim toàn NFR-36 PASS từ M2. |
| 10. NFR-38 / AC-65 disposition | PARTIAL đã quyết theo D-143; milestone mapping còn mở | Giữ PARTIAL cho M2. AC-65 story→M4 và video→M5 vẫn là đề xuất, owner chưa chọn. | M2-AT-10 chỉ kiểm metadata locale/age; AC-65 còn age-band/context đã duyệt, Vietnamese content và video cá nhân hóa theo tranh trẻ. | M2-AT-10, M4 story và M5 video. | Mapping M4/M5 là đề xuất; không claim chất lượng AC-65 đã đạt. |

Các mục còn mở: S0-owner-run cần tên DB/container, identity, runner, restore, proof synthetic-only, hash script chỉ đọc, command ceiling và mypy command/version/output trong Task Approval riêng. S1a cần ghi các mục ở §8, profile ownership/role matrix, physical mapping và nguồn tuổi; hành vi StoryRun với hàng tuổi cũ 121–155 chưa xác minh. Age-band boundaries/catalog, field/purpose/expiry của share, consumer B5, cleanup sau DELETE_PENDING, placeholder spelling trước OpenAPI freeze S3 và việc thống nhất quota owner scopes giữa SRS §11.2 với DTR §14.2 mục 10 vẫn còn mở. S1b chỉ được xem xét lại sau khi S1a đóng và owner quyết định riêng. Các default trong bảng không thay thế các quyết định còn mở.

## 10. Gói cần có trước launch

- Draft 9 đang DRAFT / AWAITING INDEPENDENT REVIEW; Draft 8 có review NEEDS_REVISION (0 P1 / 3 P2 / 8 P3). Draft 9 chưa có review hoặc owner approval. D-142 xác nhận HEAD dd70685eae58aaaefea3e567f5c23d09345a8513 làm review baseline cho Draft 7; D-144 đã xử lý B0 provenance; D-150 chỉ đóng S0-doc ở phạm vi tài liệu.
- S0-owner-run vẫn DRAFT và cần Task Approval riêng ghi tên database, container, identity, người chạy, restore, bằng chứng synthetic-only, hash script chỉ đọc, command ceiling, mypy command/version và người chịu trách nhiệm.
- S1a dùng D-148 làm hướng thiết kế nhưng vẫn cần Task Approval riêng, giải quyết các mục tại §8 và nêu exact file allowlist theo từng path, path mới, exclusions; không dùng wildcard và §8 không tự cấp quyền sửa file.
- Owner quyết các lựa chọn còn mở tại §9 ảnh hưởng tới pha được launch và ghi lựa chọn trong Task Approval. S1b hiện DEFERRED, chỉ được xem xét lại sau khi S1a đóng; D-148 không approve S1a hoặc thay đổi SRS.
- Ghim plan hash, branch/HEAD, nguồn, snapshot manifest khi một pha được đề xuất để launch; không tự ghi hash Draft 8 vào hồ sơ khác.
- Ghi DB task-owned identity, database name/container, người tạo/chạy, dữ liệu, snapshot/restore, proof synthetic-only và cleanup boundary.
- Ghi Alembic graph/target revision, offline plan/SQL review và command ceiling; chưa có approval thì không chạy migration.
- Ghi test matrix/tầng test; route acceptance dùng PostgreSQL thật/wiring thật khi route là đối tượng.
- Ghi disposition B1 stale-owner orphan, N-1 route PostgreSQL request/cancel, OpenAPI P3, mypy baseline và mọi PARTIAL/NOT RUN. Draft 8 từng báo offline-check.txt (pin inherited/reference từ Draft 7: 6FF16B2E77EE7DB7CE18521484B92FAA9B40F685393D35A7746E74236313E143) ENOENT; Draft 9 đã đọc bytes hiện tại và re-verify hash khớp. Log ghi 27 bước và 9/9 là dữ kiện lịch sử, không phải pass/fail gate; Alembic execution/live graph/mypy baseline của M2 chưa chạy.
- Task Approval phải nêu rõ phase, scope, file allowlist, evidence, DB identity và command ceiling. Approval một pha không mở pha khác, M3–M6, provider hay Modal. D-146 xác nhận hiện không có implementation approval; OWNER_MODAL_CALL_APPROVED=NO không đổi.

Cho tới khi các điều kiện này được ghi nhận, Draft 9 vẫn **DRAFT / AWAITING INDEPENDENT REVIEW**; M2 chưa launch và không có quyền sửa code, migration, DB hoặc gọi provider.

Lịch sử bản: Draft 7 → Draft 8 — cập nhật theo D-142..D-150 và evidence S0-doc; sửa status/gates, traceability, Task Approval items và owner-decision ledger. Draft 8 vẫn chờ review độc lập. Draft 8 → Draft 9 — xử lý các finding được liệt kê ở bảng thay đổi; Draft 9 vẫn DRAFT, chờ review độc lập.
