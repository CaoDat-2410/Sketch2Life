# Kế hoạch M2 — Parent / Teacher Foundation (Draft 11)

**Feature:** FEAT-063 — System Architecture Rearchitecture
**Ngày:** 2026-11-06
**Trạng thái:** **DRAFT 11 / AWAITING INDEPENDENT REVIEW AND OWNER DECISION**
**Phạm vi:** Draft 11 dùng Draft 10 làm nền lập kế hoạch được owner chấp nhận theo D-151, nhưng bản thân Draft 11 vẫn là ứng viên DRAFT chờ review độc lập và owner quyết định. SRS v2.3-draft giữ nguyên pin; v2.5–v2.7 chỉ là đối chiếu bản nháp, chưa ký/chưa gộp. S0-doc CLOSED theo D-150 và S0-owner-run CLOSED chỉ trong phạm vi một lượt inventory chỉ đọc theo D-154; lượt đó có K3 FAIL, K4/K6 COLLECTED, K5/K7 NOT RUN. S1a, S1b, S2, S3 và M3–M6 chưa mở; không có implementation approval, quyền migration/ghi DB, provider, Modal hay workload.

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
| §4 intro, FR-PL-08, M2-AT-08, M2-AT-10 | Ghi POST /v1/story-runs và /cancel là route/service S2 ngoài năm route nền M2; N-1 là một route test ngoài tập nền. | D-148 mục 4; review Draft 8 P3-9 |
| §5.2–§5.3 | Gắn provenance cho các khẳng định tables.py và migration 20261102/20261103: được phiên soạn trước ghi nhận từ source, nằm ngoài allowlist S0-doc theo evidence §6 và chưa được S0-doc xác minh; Draft 9 không xác nhận độc lập các file đó. | Review Draft 8 P3-11; evidence §6 |

**Đính chính bảng D8→D9:** Đối chiếu Draft 8 và Draft 9 bằng git diff --no-index --unified=0 (0 dòng ngữ cảnh) cho 38 hunk và git diff --no-index --unified=3 (3 dòng ngữ cảnh) cho 17 hunk. Số hunk phụ thuộc ngữ cảnh nên con số “23 hunk” trong ghi nhận trước không tái tạo được. Hàng 2 gán “Tác động của merge” cho thay đổi ở §1 dù phần đó không đổi trong diff, đồng thời bỏ sót §5.3 dòng 343 của Draft 9; hàng 6 ghi §2.2 nhưng thay đổi thực tế ở §2.3; hàng 8 ghi §4 BR-58 dù hàng BR-58 ở §4 giống Draft 8, thay đổi thực tế nằm ở §7 tiêu chí 1. Bảng D8→D9 cũng bỏ sót việc tiêu chí S3 đổi từ “Tất cả M2-AT pass” trong Draft 8 sang “Các M2-AT đã chạy pass” trong Draft 9.

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

## 0. Trạng thái, checkout, merge và baseline đã ghi nhận

Trong lịch sử, Draft 5 được lập trên branch feature/feat063-be-foundation, HEAD dd70685eae58aaaefea3e567f5c23d09345a8513. HEAD có first parent 1e109b1726f327ac9383457b0dbdd535ef5c6518 và second parent fb834771c24957bb8e289fb95d21410b14181e57. Chuỗi lịch sử ghi nhận trong Draft 4 là b6dbfa68e66718f3f40902c093e9ebd634b1ebb9 → 1e109b1726f327ac9383457b0dbdd535ef5c6518 → dd70685eae58aaaefea3e567f5c23d09345a8513.

Trước khi tạo Draft 5, index rỗng và working tree có đúng bốn path untracked: Draft 1–4. Hash trước khi ghi: Draft 1 F47393FD1028B20D841114786E7D07B12BC8C89A67EF6697F0396EFCA7942E81; Draft 2 A09F7E6BF8534E85EE4EE4573209B5346861008AA4A5C4A8C907CF4EFEDCFE66; Draft 3 A6F8CE23DA3650B38FF7E13BAF9052371B1655BE400BB6D5F9053A5D5E2C638D; Draft 4 A31DCEA8DBEF0CF9E59FC7E9F3346C35B1F278DC1D6AAB3E992B436E1590FEEC. Branch, HEAD, parent commits, empty index, bốn path untracked và cả 17 hash nguồn được ghim tại §1 đều khớp trước khi ghi Draft 5. Draft 1–4 là đầu vào chỉ đọc. Git status đồng thời phát sinh warning rằng user-level global ignore config không đọc được; không dùng warning đó để khẳng định path nào cụ thể bị ảnh hưởng.
Trong lần ghi nhận lịch sử D6-1, trước khi tạo bản ghi đó, index rỗng, tracked worktree diff rỗng và đúng năm file Draft 1–5 là untracked. Hash pre-edit: Draft 1 F47393FD1028B20D841114786E7D07B12BC8C89A67EF6697F0396EFCA7942E81; Draft 2 A09F7E6BF8534E85EE4EE4573209B5346861008AA4A5C4A8C907CF4EFEDCFE66; Draft 3 A6F8CE23DA3650B38FF7E13BAF9052371B1655BE400BB6D5F9053A5D5E2C638D; Draft 4 A31DCEA8DBEF0CF9E59FC7E9F3346C35B1F278DC1D6AAB3E992B436E1590FEEC; Draft 5 B1C39C63314274137699F06B219C531E92BE0727D6120D7F06445F9C326283D7. Các hash này là baseline của file đầu vào, không thay thế owner review. Git status đồng thời phát warning user-level global-ignore config bị Permission Denied; đây là warning riêng, không chứng minh path repo nào bị ảnh hưởng. Báo cáo cũ về backend/.pytest-phase8-precommit/ là từ reviewer trước; lần status này không phát warning cho path đó.

Trước khi lập Draft 7, branch feature/feat063-be-foundation ở HEAD dd70685eae58aaaefea3e567f5c23d09345a8513 với hai parent 1e109b1726f327ac9383457b0dbdd535ef5c6518 và fb834771c24957bb8e289fb95d21410b14181e57; index rỗng, working tree chỉ có sáu artifact kế hoạch tiền nhiệm chưa theo dõi. Draft 7 được lập từ bản kế hoạch tiền nhiệm chỉ đọc, SHA-256 C836A72A84D5EED70427CC69540050852D54C83D94745DAFEF02A0A0704FD537; ghi nhận pin của phiên đó là lịch sử, không thay thế kết quả final audit Draft 8 tại §1. Các bản kế hoạch tiền nhiệm không bị sửa.
Phiên lập Draft 7 chỉ đọc tài liệu/metadata, kiểm tra hash và Git, rồi đếm path bằng git diff --name-status; không chạy Alembic, DB, mypy hay test. Git status cảnh báo không đọc được user-level global ignore config; cảnh báo riêng theo thông tin đầu vào rằng backend/.pytest-phase8-precommit/ không đọc được cũng được ghi nhận, không xem là lỗi kế hoạch.
Trước khi tạo Draft 8, branch feature/feat063-be-foundation ở HEAD dd70685eae58aaaefea3e567f5c23d09345a8513 và index rỗng. Git status --short ban đầu có hai tracked path modified là features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md và features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md; tám untracked path gồm evidence S0-doc và Draft 1–7. Các thay đổi đó có trước tác vụ Draft 8. Đường dẫn Draft 8 chưa tồn tại trước khi ghi; Draft 1–7 và các hồ sơ hiện có không thuộc phạm vi sửa của tác vụ này.
D-142 xác nhận dd70685eae58aaaefea3e567f5c23d09345a8513 làm review baseline cho Draft 7; Draft 8 và Draft 9 được soạn trên cùng HEAD, và cổng Draft 10 cũng khớp HEAD đó. Đây là baseline review, không phải implementation approval.
Ngay trước khi tạo Draft 10, branch feature/feat063-be-foundation ở HEAD dd70685eae58aaaefea3e567f5c23d09345a8513; index rỗng. git status --short thực tế:
```
 M features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md
 M features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md
?? features/FEAT-063-system-architecture-rearchitecture/evidence/M2_S0_DOC_SOURCE_RECONCILIATION_20261106.md
?? features/FEAT-063-system-architecture-rearchitecture/plan/M2_PARENT_TEACHER_FOUNDATION_PLAN_DRAFT1_20261105.md
?? features/FEAT-063-system-architecture-rearchitecture/plan/M2_PARENT_TEACHER_FOUNDATION_PLAN_DRAFT2_20261105.md
?? features/FEAT-063-system-architecture-rearchitecture/plan/M2_PARENT_TEACHER_FOUNDATION_PLAN_DRAFT3_20261105.md
?? features/FEAT-063-system-architecture-rearchitecture/plan/M2_PARENT_TEACHER_FOUNDATION_PLAN_DRAFT4_20261106.md
?? features/FEAT-063-system-architecture-rearchitecture/plan/M2_PARENT_TEACHER_FOUNDATION_PLAN_DRAFT5_20261106.md
?? features/FEAT-063-system-architecture-rearchitecture/plan/M2_PARENT_TEACHER_FOUNDATION_PLAN_DRAFT6_20261106.md
?? features/FEAT-063-system-architecture-rearchitecture/plan/M2_PARENT_TEACHER_FOUNDATION_PLAN_DRAFT7_20261106.md
?? features/FEAT-063-system-architecture-rearchitecture/plan/M2_PARENT_TEACHER_FOUNDATION_PLAN_DRAFT8_20261106.md
?? features/FEAT-063-system-architecture-rearchitecture/plan/M2_PARENT_TEACHER_FOUNDATION_PLAN_DRAFT9_20261106.md
```
git diff --cached --name-only không có đầu ra. Draft 10 ghi lại trạng thái trước lần tạo của nó; trạng thái mới nhất trước Draft 11 được ghi bổ sung tại §0. Git cảnh báo không đọc được user-level global ignore config; cảnh báo không xác định path repo nào bị ảnh hưởng.

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

Draft 10 trực tiếp dùng Draft 9 làm nguồn, SHA-256 1B738FE7558156E0227D75715737B4A9BE35B93C7B25739B91A5DF2DECD13916; Draft 8 là bản lịch sử, SHA-256 188417FCCAEC1F64F1DEE0AD435B51DFE117AA404928942E656E878494DFEA3D. Draft 10 đã đọc lại bytes của 19 nguồn được ghim tại §1.1–§1.3: 19/19 hash khớp, gồm offline-check.txt. Không chuẩn hóa bytes để làm khớp pin; việc kiểm tra bytes không phải owner approval.
Bản ghi lịch sử D6-1 dùng Draft 5 làm nền chỉ đọc; SHA-256 Draft 5 là B1C39C63314274137699F06B219C531E92BE0727D6120D7F06445F9C326283D7. Lịch sử pin của lần ghi D6-1 không phải kết quả final audit Draft 10 tại §1; audit hiện tại ghi đủ 19/19 pin khớp. Điều này chỉ xác nhận bytes đã quan sát, không phải owner approval.

Draft 7 dùng bản kế hoạch tiền nhiệm làm nền chỉ đọc, SHA-256 C836A72A84D5EED70427CC69540050852D54C83D94745DAFEF02A0A0704FD537. Số re-hash của Draft 7 là lịch sử, không thay kết quả hiện tại: Draft 10 đã đọc lại 19/19 pin như ghi đầu §1. Đây chỉ xác nhận bytes, không phải owner approval.
Draft 8 kế thừa Draft 7 chỉ đọc, SHA-256 BB3C9F165731B1AEE261265270526B791FEE7BD622CE7D614514F2622DEFD099. Audit Draft 8 từng ghi 14 hash unchanged và 2 pin DECISIONS.md/TASK_APPROVAL.md cập nhật khớp; offline-check.txt (6FF16B2E77EE7DB7CE18521484B92FAA9B40F685393D35A7746E74236313E143) khi đó báo ENOENT/không re-verified; hai pin mới khớp nên tổng là 18/19 ở lượt Draft 8. Draft 9 đọc bytes hiện tại của 19 pin và báo 19/19; Draft 10 cũng re-read 19 pin và xác nhận 19/19 khớp. Việc kiểm tra bytes không phải owner approval.

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
- OI-05..08 trong SRS v2.3 đã ghim nằm tại §14.1, dòng 1130–1133; đây là các câu hỏi về chuyên gia/privacy, retention/backup, region/cross-border và production/operations. Chúng vẫn mở, chưa tạo authority cho consent hoặc dữ liệu thật. Draft 10 từng ghi nhầm §29.2; Draft 11 sửa nhãn nguồn mà không sửa Draft 10 hay thay pin.
- Route share Parent, schema vật lý Parent, catalog tuổi và một số owner columns chưa được đóng; đánh dấu chưa xác minh.
- Migration 20261104_story_revisions.py hiện có trong source và được ghim riêng ở §1.3; pin nguồn chứng minh file bytes, không chứng minh migration đã chạy.
- Offline-check ghi rõ không có DB connection, network hay migration execution và kết thúc bằng facts only; not a pass/fail verdict. Log báo kế hoạch upgrade 27 bước cùng số 9 observed version rows / 9 script_heads tại thời điểm ghi; đây là dữ kiện lịch sử, không phải cổng pass/fail. Danh sách script_heads dừng ở 20261103_story_upload_compat, không chứa migration 20261104_story_revisions; log không chứng minh graph/head hiện tại hay migration đã chạy.
- M1 là demo synthetic local. M1/A2/B1/B2 không cấp quyền cho M2.
- Review Draft 3 được báo cáo ngoài repository; không có artifact/hash pinned ở đây nên verdict không được phiên này xác minh độc lập. Reviewer trước đó báo cáo permission denied khi đọc .pytest-phase8-precommit. Phiên Draft 5 thấy bốn Draft 1–4 untracked cùng warning riêng về user-level global ignore config; không có căn cứ nói path .pytest-phase8-precommit được tái kiểm tra hoặc kiểm kê toàn bộ path không đọc được.
- PostgreSQL details ở FEAT-064 là owner-run; B0 original bytes và các canonical Parent share/Teacher routes không được xác minh độc lập trong phiên tài liệu này. Phiên lập Draft 5 (lịch sử) chỉ cập nhật plan; không chạy validation, owner-run command, test, DB, migration, provider hoặc network action.

### 1.5. Đối chiếu SRS v2.5–v2.7 (nháp, chưa ký)

SRS v2.3-draft tại §1.1 vẫn là pin của kế hoạch theo lựa chọn A của owner. Các bản dưới đây chỉ là đối chiếu từ refs đã có sẵn trong local Git; không đổi pin, không nhập nhánh và không tự nâng authority. Independent review được chủ sở hữu cung cấp dưới dạng tóm tắt chat-only; không tìm thấy báo cáo review tương ứng trong repo. Các khẳng định kỹ thuật sau đây được kiểm lại bằng git show trên đúng refs.

| Bản | Git ref | SHA-256 SRS | Vai trò |
|---|---|---|---|
| v2.3-draft | Working tree và origin/feature/feat063-be-foundation | DCBF9786FF8983E34F2D3B4EBAB76301D0C52A6C9DE72CD08D0816BBD0D983FC | Pin kế hoạch hiện tại, chưa ký. |
| v2.5 | origin/docs/feat063-rev45-srs-code-alignment-20261106 | B513AD2F510A7CDA6C54FB0B49523005A60A2F918B4AC705231006EC6BE9DA7E | Bản trung gian để đối chiếu. |
| v2.6, conflict-remediation | origin/docs/feat063-srs-conflict-remediation-20261106 | DD9382FE0EB8A32C4E0206F0E5107DAB49CEF063E2B73156D1EFB51A08007F4F | Nhánh là tổ tiên của v2.7 theo merge-base. |
| v2.6, v25-report-remediation | origin/docs/feat063-v25-report-remediation-20261106 | 56ACA9FAC892F189653D59120AC8AFAEB1C7730ADDD60076BD7FC39436F931A7 | Nhánh không là tổ tiên của v2.7; ghi chờ Q-13 và không tự coi “organization admin” là alias của School Manager. |
| v2.7-draft | origin/docs/feat063-srs-v26-checklist-20261107; cùng bytes với origin/docs/feat063-diagram-readiness-20261107 | 3869BA77EA0867FF7C7DAD491D9D0D6B90E332CA936B4236EE3AA7AEF4027696 | Draft chưa ký/chưa gộp vào be-foundation. |

DTR ở ref v2.7 có SHA-256 8A39DF26D8BE42031233629F5617FB660E25E71C07AE3FA282D7CF45B472C303. DTR v2.7 thể hiện 92 bảng active và 140 bảng projected; so với bản DTR được ghim ở §1.1, chuỗi đếm lịch sử được báo là 94/142. Bản v2.7 không giữ amendment StoryRun-lite cho core.upload_command_receipts và story.command_receipts; vì vậy đây là mục cần chủ schema đối chiếu ở S2, không phải chỉ thị sửa DTR hay kết luận DTR nào được áp dụng.

Hai v2.6 refs có khác biệt về cách gọi/ánh xạ role. Nhánh v25-report-remediation nêu role “organization admin” chưa được đồng nhất với School Manager cho tới khi owner giải Q-13; nhánh conflict-remediation là tổ tiên của v2.7 và dùng một disposition khác. V2.7 chuẩn hóa tên School Manager, nhưng chưa được owner chọn làm pin. Các quyết định D-135..D-138 ở docs refs mang nghĩa khác D-135..D-138 trong ledger origin/feature/feat063-be-foundation (ledger hiện tại ghi nhóm quyết định Modal). Do va chạm ID, các hồ sơ M2 phải ghi kèm branch/ref và phiên bản, không trích D-ID trần. Tóm tắt review cũng nêu v2.7 có D-146 mang nghĩa khác; tìm trực tiếp trong blob SRS/DTR v2.7 không tái hiện được tham chiếu này, nên điểm đó chưa xác minh. Trong be-foundation, D-146 là quyết định không có implementation approval.

### Bảng tham chiếu số dòng v2.3 → v2.7 (không phải pin)

| Hạng mục | v2.3-draft | v2.7-draft | Ghi chú |
|---|---:|---:|---|
| SRS §21.2, POST classes | 1557 | 1578 | Cùng route; chỉ số dòng thay đổi. |
| SRS §21.2, POST assignments | 1558 | 1579 | Cùng yêu cầu đúng một Teacher phụ trách active. |
| OI-05..08, §14.1 | 1130–1133 | 1146–1149 | Đây là §14.1; không phải §29.2. |
| BR-18, SRS requirement table | 2396 | 2417 | Yêu cầu 36–120 tháng. |
| BR-18, §31.8 index | 225 | 235 | Tham chiếu chéo. |
| BR-49, §30.4 / §31.8.1 | 2428 / 2558 | 2449 / 2582 | Tenant isolation. |
| BR-57, §30.4 / §31.8.1 | 2436 / 2566 | 2457 / 2590 | Age/age-band scope. |
| BR-58, §30.4 / §31.8.1 | 2437 / 2567 | 2458 / 2591 | Audience/share scope. |
| FR-PL-25, requirement index / table | 2370 / 2550 | 2391 / 2574 | Line mapping only. |
| AC-62 | 2599 | 2623 | Acceptance table. |
| AC-65 | 2602 | 2626 | Acceptance table. |
| NFR-38 | 2579 | 2603 | Requirement table. |
| DTR §14.2 item 10 | 683 | 677 | Quota scope note; source-version difference remains open. |

SRS v2.3 và v2.7 đều giữ yêu cầu nền cho S1a: năm route ở §21.2, chính xác một Teacher phụ trách active, tuổi 36–120 tháng, origin/consent và các lát BR-49/BR-58. Kết luận so sánh là ảnh hưởng nhỏ tới phạm vi nền S1a; nó không thay đổi pin, D-148, allowlist hay status pha.

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

### 2.4. Ghi chú role từ SRS v2.7 (chỉ đối chiếu)

SRS v2.7 dùng “School Manager” nhất quán ở §§3, 20 và 31.3; đây là ghi chú so sánh với v2.3-draft đã ghim, không sửa D-148 mục 1/2 và không đổi pin. Mã school_admin tiếp tục chỉ đến từ D-148; SRS v2.7 không định nghĩa mã role đó. “Admin nội dung” trong v2.7 là permission của Platform Admin để review/publish/moderate, không phải role hay principal đăng nhập riêng; permission này không cấp quyền xem profile/media trẻ. Platform Admin bị deny child-media access mặc định. M2-AT-01 giữ nguyên ca âm tính và expected denial; chỉ làm rõ cách hiểu actor. V2.7 §31.10 mục 14 vẫn để mở persistence/resolver của role và permission.

## 3. Subphase M2 đề xuất

Trạng thái dưới đây không thay thế Task Approval riêng cho từng pha. S0-doc CLOSED theo D-150; S0-owner-run CLOSED theo D-154 chỉ ở phạm vi một lượt inventory chỉ đọc. Không có pha implementation nào được mở.

| Pha | Trạng thái | Phụ thuộc | Nội dung | Tiêu chí thoát có thể kiểm chứng | Stop gate |
|---|---|---|---|---|---|
| S0-doc | CLOSED — phạm vi tài liệu | Không | Đối chiếu nguồn, mapping schema, owner directions, B0 provenance và migration graph bằng source; không chạy command/DB. | Sáu tiêu chí thoát S0-doc: (1) mỗi requirement có source ID; (2) unknown được gắn nhãn; (3) route/table/owner/M2-AT có crosswalk; (4) B0 provenance có owner disposition hoặc tiếp tục block (D-144 §9.7 disposition trong giới hạn đã ghi); (5) giới hạn evidence được ghi; (6) không claim implementation approval. D-150 ghi cả sáu tiêu chí đã đạt trên evidence M2_S0_DOC_SOURCE_RECONCILIATION_20261106.md SHA-256 1BB71300A6A22487311A8D39EECB0EB1CE2664CB471EC2DAF45DA8DE2E244001; closure chỉ ở phạm vi tài liệu, không xác nhận implementation hoặc schema vật lý. | Không dùng closure này để chạy DB, migration, mypy hoặc mở pha khác. |
| S0-owner-run | CLOSED — chỉ phạm vi một lượt inventory chỉ đọc theo D-154 | S0-doc CLOSED; D-153 là approval, sau đó owner có chỉ thị launch riêng; D-154 ghi lượt đã chạy. | Một lượt PostgreSQL 17.11 native, database sketch2life, loopback 5433; K1/K2 PASS, K3 FAIL, K4/K6 COLLECTED, K5/K7 NOT RUN. Không phải migration, mypy baseline hay synthetic-only proof đầy đủ. | D-154 ghi nhận inventory và giới hạn; K3 mismatch không được sửa. Không mở S1a hoặc cho phép ghi DB. |
| S1a identity/tenant/profile/age | DRAFT | S0-doc và S0-owner-run đóng; cần Task Approval riêng. D-148 là hướng thiết kế, không phải approval S1a. | Identity/role assignment, tenant isolation, profile ownership và age provenance theo các directions D-148. | Acceptance đề xuất M2-AT-01/02/03/04A/04B/10/11; ca thiếu consent record trong AT-11 chỉ áp dụng nếu F-6 được giải quyết trong Task Approval S1a theo hướng giữ yêu cầu này ở S1a. Route test persistence dùng PostgreSQL thật và wiring thật. | Thiếu role matrix, profile owner hoặc age source trong Task Approval thì deny-by-default; không tự tạo route/policy. |
| S1b grant/revoke/consent | DEFERRED | Chỉ xem xét lại sau khi S1a đóng và owner quyết định tiếp; D-144 §9.3 và D-148 mục 8. | Scoped grant/revoke, purpose/expiry/audit và consent/data authorization chỉ được xét nếu owner mở lại bằng quyết định và approval riêng. | Hiện không có tiêu chí thoát đang hoạt động; M2-AT-05/06/07 NOT RUN. Nếu owner mở lại sau S1a, acceptance phải được ghi trong approval riêng. | Không bật share/consent hoặc chạy AT-05/06/07 trong trạng thái DEFERRED. REAL và LEGACY_UNCLASSIFIED bị từ chối theo D-144. |
| S2 owner/job/asset/revision/lifecycle | DRAFT | S1a; S1b nếu bật; migration target đã duyệt | Durable owner/scope refs, job/asset/revision, AiJobService mapping, idempotency/replay, cancel, restart/recovery, DELETE_PENDING/D-127. | M2-AT-08/09 đạt. N-1 phải test PostgreSQL mức route cho request → job → status, gồm request VÀ cancel qua route thật với wiring thật, không monkeypatch/override dependency; đạt trước khi thoát S2 và trước D9/client integration. B1 orphan có invalidation/reconciliation/read-exposure contract và regression trước dữ liệu non-synthetic/provider. | Orphan có thể được đọc/công bố như accepted result, job/aggregate lệch hoặc thiếu N-1 thì chưa thoát S2; evidence NOT RUN không đóng gate. |
| S3 freeze và đóng M2 | DRAFT | S1a, S1b theo disposition, S2 | Đối chiếu evidence và freeze contract; đóng OpenAPI P3 hai POST submit/cancel trước frontend/client. | Điều kiện đề xuất, owner phải chấp nhận trong Task Approval S3: chỉ M2-AT-05/06/07 được phép ở trạng thái NOT RUN/DEFERRED khi S1b vẫn DEFERRED; mọi M2-AT khác phải chạy và pass. NFR-36 và NFR-38 có disposition; OpenAPI parity được kiểm; conditions được gán owner/phase; independent review ACCEPTED. | Không tích hợp frontend/client khi OpenAPI P3 còn mở; không tự mở M3 hoặc bật workload. |

M2-AT-05/06/07 không được coi là đạt: theo D-148 mục 8, S1b hoãn và cả ba test đều NOT RUN. S2 và S3 giữ nguyên các cổng N-1 route PostgreSQL, B1 stale-owner orphan và OpenAPI P3; ghi trạng thái DRAFT không mở các cổng đó.

### 3.1. Kết quả S0-owner-run và phạm vi đóng theo D-154

D-154 ghi một lượt owner-run ngày 2026-11-07 trên PostgreSQL 17.11 native, database sketch2life, loopback 5433; owner báo exit code 0. Đây là nguồn owner-run được hồ sơ ghi nhận, không phải phiên Draft 11 kết nối DB. Inventory files chỉ được dẫn làm tham chiếu local, không chép nội dung: inventory.json SHA-256 E4529F541002D840C3F2E1D25F24D00E7B92A65720E3036EB59BA71FD04DB64F; inventory.txt SHA-256 E37B07E82DB8E22B53F93D12F9400912271AD25135EB4103A99DFA2EDAB51025.

Quan sát D-154: 117 bảng, tổng 82 hàng (24+58), 9 hàng public.alembic_version; 26 bảng có dữ liệu theo báo cáo trước đó. Số hàng từng bảng được ghi là giống snapshot A2 hậu teardown lỗi. K1 PASS chỉ xác nhận tên DB; K2 PASS; K3 FAIL; K4/K6 COLLECTED; K5/K7 NOT RUN. K3 là mismatch chưa sửa: DB ghi 20261103_story_upload_compat trong khi source head là 20261104_story_revisions; migration story_revisions chưa được ghi nhận là applied và schema story chỉ có năm bảng command_receipts, review_decisions, run_inputs, runs, understanding_revisions. Không suy ra graph đã hội tụ.

K5 không có synthetic-only proof đầy đủ: chỉ be1_managed_profiles và be1_synthetic_eligibility_proofs có data_origin, mỗi bảng một hàng SYNTHETIC_DEV; 115 bảng không có data_origin; chưa có proof cho 15 hàng ứng dụng baseline. K6 chỉ thu thập CHECK tuổi 36–155 và CHECK origin/consent; K7 không chạy theo lựa chọn MYPY_DECISION=A. Do vậy D-154 chỉ đóng thủ tục S0-owner-run cho lượt inventory đã duyệt; không biến K3 thành PASS, không xác nhận dữ liệu toàn DB synthetic, không chạy migration và không mở S1a.

## 4. Traceability requirement → route/API → bảng → owner → acceptance

Route là candidate theo SRS v2.3-draft, chưa freeze. Tập route nền Parent/Teacher của M2 chỉ gồm năm route SRS §21.2 liệt kê tại §4.1 theo D-148 mục 4; nhóm route SRS §9.6 không tự tạo method contract. SRS §21.2 cũng có POST /v1/story-runs và POST /v1/story-runs/{run_id}/cancel, là route/service S2 ngoài năm route nền M2. M2-AT-08 và M2-AT-09 là route test S2 ngoài năm route nền: AT-08 dùng các route StoryRun trong §21.2, AT-09 dùng các route /api/be1/… không thuộc SRS §21.2. Đây là suy luận của kế hoạch; D-148 không nói về S2, chờ Task Approval S2. Không thêm route vào tập nền M2 và S2 chưa mở. “Suy luận” là mapping chưa gắn trực tiếp; “chưa xác minh” là chưa có contract theo method.

| Requirement | Route/API và nguồn | Bảng/owner logic theo DTR | Acceptance |
|---|---|---|---|
| FR-PL-01 | POST /v1/parent/profiles; GET/PATCH /v1/parent/profiles/{profile_id} — SRS §21.2. SRS §9.6 có nhóm route /v1/me, nhưng §21.2 không có method contract cho nhóm đó; không suy ra method /v1/me. Identity được giải quyết nội bộ từ token theo D-148 mục 4. | parent.child_profiles, parent.profile_share_grants; be1.adult_identities, be1.organization_assignments; core audit — Parent/BE1/Core. | M2-AT-01/11; M2-AT-05 NOT RUN vì S1b DEFERRED. |
| FR-PL-02 | POST /v1/organizations/{org_id}/classes và POST /v1/classes/{class_id}/assignments — actor “Admin tổ chức”/“School Manager” (mã school_admin theo D-148 mục 1), quyền chỉ theo SRS §20; SRS §§20/3/31.3 không nhất quán tên role. POST /v1/classes/{class_id}/profiles — Teacher được phân công; SRS §21.2. List/read routes chưa xác minh. | be1.organizations, classrooms, organization_assignments, enrollments — BE1; consumer scope thuộc owner tương ứng. | M2-AT-02/04A/04B. |
| FR-PL-07 | Parent profile POST/GET/PATCH là các route SRS §21.2, không phải grant. Invite/accept/revoke route chưa có contract theo method trong tập năm route M2. | parent.profile_share_grants, parent.child_profiles, parent.data_authorizations; be1.managed_profiles — Parent/BE1. | Grant/share scope NOT COVERED trong M2 theo D-148 mục 8; M2-AT-05 NOT RUN vì S1b DEFERRED. |
| FR-PL-08 | Profile GET/PATCH — SRS §21.2. Grant/download/token/cache/revoke surface chưa có contract theo method trong tập năm route M2; lifecycle S2 giữ cổng riêng. POST /v1/story-runs và POST /v1/story-runs/{run_id}/cancel có trong SRS §21.2 nhưng là route/service S2 ngoài năm route nền M2; M2-AT-08/09 là các route test S2 ngoài route set nền, đây là suy luận của kế hoạch, D-148 không bàn S2 và đang chờ Task Approval S2. | parent.profile_share_grants, core.asset_lineage — Parent/Core. | Grant/share scope NOT COVERED trong M2 theo D-148 mục 8; M2-AT-06 NOT RUN vì S1b DEFERRED; AT-09 là gate N-1 của FEAT-064, không phải acceptance FR-PL-08. |
| FR-PL-25 | Parent profile POST/GET/PATCH và POST /v1/classes/{class_id}/profiles — SRS §21.2. Age-band catalog route — chưa xác minh. | parent.profile_revisions, be1.profile_revisions, age-band catalog — Parent/BE1/catalog owner chưa xác minh. | M2-AT-03/10. |
| BR-48 | Profile route không phải share route. Parent share invite/accept/revoke chưa có contract theo method trong tập năm route M2. | parent.profile_share_grants, parent.data_authorizations — Parent. | Grant/share scope NOT COVERED trong M2 theo D-148 mục 8; M2-AT-05/06 NOT RUN vì S1b DEFERRED; thiếu grant phải deny nếu S1b được mở lại. |
| BR-49 | POST /v1/organizations/{org_id}/classes; POST /v1/classes/{class_id}/assignments; POST /v1/classes/{class_id}/profiles — SRS §21.2; Admin tổ chức cho hai route đầu và Teacher được phân công cho route profile. | Lát M2: be1.organizations, be1.classrooms, be1.organization_assignments, be1.enrollments (BE1). Ngoài lát: be1.parent_groups và be1.parent_group_members (BE1, DTR §5.4.1), lesson.access_grants (Lesson, §5.5), lesson.delivery_recipients, lesson.delivery_feedback, lesson.feedback_replies (Lesson, §5.5/§14.1), billing.video_quota_grants và billing.video_quota_usage (Billing, §5.7). Các bảng parent group/lesson access không được M2-AT-05/06 nghiệm thu; hai test này chỉ nêu primitive parent.profile_share_grants và S1b đang hoãn. | M2-AT-01/02/04A/04B. PARTIAL: M2 chỉ là lát tenant/class foundation, không phải acceptance đầy đủ BR-49. |
| BR-57 | Age qua profile routes SRS §21.2; catalog/version route — chưa xác minh. | Profile revisions, age-band catalog — Parent/BE1/catalog owner chưa xác minh. | M2-AT-03/10. |
| BR-58 | SRS §30.4 map BR-58 với FR-PL-06/FR-PL-23; SRS §31.8.1 mô tả audience là nhóm Parent hoặc invitee cụ thể có thể thu hồi. Năm route nền M2 không kiểm nghiệm lesson audience; parent.profile_share_grants chỉ là primitive profile-share. | be1.parent_groups/parent_group_members (BE1); lesson.access_grants (Lesson); parent.profile_share_grants không đồng nghĩa lesson grant. | M2-AT-05/06 NOT RUN; grant/audience của BR-58 NOT COVERED trong M2 vì S1b DEFERRED theo D-144 §9.3 và D-148 mục 8. |
| NFR-34 | Áp dụng cross-cutting trên profile, assignment, grant, asset/job routes; share/token routes chưa có contract theo method trong tập năm route nền M2. | Parent, BE1, Core, AI Jobs qua contract/ports. | M2-AT-01/02/08/09 là các acceptance tương ứng; phần grant NOT COVERED trong M2 vì S1b DEFERRED, M2-AT-05/06 NOT RUN. Không claim toàn NFR-34 PASS. |
| NFR-36 | SRS §8/§31.9: Admin access child media, profile data và cross-role grant phải theo permission/reason/audit; feedback không lộ organization khác. Grant portion NOT COVERED trong M2 vì S1b DEFERRED; media access và cross-org feedback cũng không được năm route nền M2 chứng minh. | BE1/Parent/Core/Lesson owners. | PARTIAL theo D-143; M2-AT-07 NOT RUN do S1b DEFERRED. Child media→M5 và cross-org feedback→M6 vẫn là mapping đề xuất, owner chưa chọn. |
| NFR-38 | SRS §8/§31.9 AC-65; M2 profile/age metadata là phần nền. Story và video quality chưa được roadmap phân bổ rõ toàn bộ. | Profile metadata M2; Story M4/Video M5 là phân bổ đề xuất cần owner xác nhận. | M2-AT-10 chỉ kiểm metadata; band reference null/“chưa cấu hình” không tính là đạt NFR-38/AC-65 theo D-148 mục 6; NFR-38 PARTIAL tới khi owner disposition và xác nhận phase AC-65. |

**Ghi chú hồ sơ BR-58:** Evidence S0-doc §2 dòng 53 vẫn ghi BR-58 “PARTIAL ở M2”, mâu thuẫn với D-148 mục 8 (BR-58 NOT COVERED trong M2 khi S1b DEFERRED). D-150 chuyển tiếp mâu thuẫn này sang Draft kế tiếp/Task Approval, không tự quyết. Draft 10 theo D-148 mục 8. Evidence S0-doc là hồ sơ đã đóng; không sửa.

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
| M2-AT-01 | FR-PL-01, BR-49, NFR-34; S1a | Given Parent/Teacher/Admin có role/assignment hợp lệ hoặc thiếu/thu hồi; when đọc/ghi resource qua một trong năm route nền M2; then chỉ role/scope hợp lệ được phép, denial không lộ metadata ngoài scope, audit metadata-only. Token Platform Admin, Operator hoặc Admin nội dung bị từ chối trên cả năm route. Theo ghi chú đối chiếu v2.7 tại §2.4, Admin nội dung là permission của Platform Admin, không phải principal/role riêng; ca âm tính giữ nguyên, không đổi kết quả mong đợi. Không có grant thì mọi cross-role read bị từ chối. | Domain/service unit, HTTP contract, route PostgreSQL. | Có cho route/persistence; không cho unit. |
| M2-AT-02 | FR-PL-02, BR-49; S1a | Given actor không có assignment, class không tồn tại, class thuộc organization khác, hoặc actor gọi POST /v1/organizations/{org_id}/classes với org_id ngoài assignment active (gồm organization khác hoặc không tồn tại); ca org_id này là suy luận của kế hoạch từ D-148 mục 5, vì mục 5 chỉ nêu không có assignment, class không tồn tại hoặc class thuộc organization khác; when gọi route; then mọi ca được nêu trả cùng denial/status/error shape, không lộ existence/content. Với {org_id}, server so sánh với assignment active; với {class_id}, server suy ra organization từ class record rồi so assignment. Không lấy organization từ claim hoặc header. | Unit matrix và route integration wiring thật. | Có cho integration. |
| M2-AT-03 | FR-PL-25, BR-57; S1a | Given tuổi nguyên 35, 36, 120 hoặc 121 tháng; when tạo hoặc cập nhật profile; then 36 và 120 được chấp nhận, còn giá trị mới 35 và 121 bị từ chối ở application layer. Band reference null và hiển thị “chưa cấu hình”; trạng thái null không đạt NFR-38/AC-65 theo D-148 mục 6; không dùng child_age.py. Hàng cũ được giữ nguyên, không sửa; chỉ revalidate khi trường tuổi đổi. Test không giả định DB từ chối 121 vì CHECK hiện tại 36–155 còn nguyên tới khi có migration được duyệt riêng. | Domain/contract unit và repository integration. | Có cho persistence. |
| M2-AT-04A | FR-PL-02, BR-49; S1a; SRS §21.2 | Given Admin tổ chức thuộc đúng org và còn capacity cùng một Teacher active; when POST /v1/organizations/{org_id}/classes rồi POST /v1/classes/{class_id}/assignments; then class và assignment được tạo theo response contract. Given capacity hết; when Admin gửi POST tạo class; then không tạo class/assignment; chỉ kỳ vọng CLASS_CAPACITY_REACHED nếu contract hiện hành định nghĩa mã này. Tách riêng: Given Teacher gọi route Admin để tạo assignment; when gửi request; then authorization deny và không tạo assignment; không gán mã capacity cho lỗi quyền. Given class đã có một Teacher active; when thử assign Teacher thứ hai trong lúc Teacher hiện tại vẫn active; then acceptance phải giữ bất biến “chính xác một Teacher phụ trách active” theo SRS §21.2 dòng 1558. D-148 F-2 yêu cầu Task Approval S1a ghi rõ acceptance/cardinality; kế hoạch không tự xác định response hoặc transition. | Route PostgreSQL acceptance với actor đã xác thực và wiring thật. | Có. |
| M2-AT-04B | FR-PL-02, BR-49; S1a; SRS §21.2 | Given Teacher được phân công vào class cùng tenant và expected class revision hiện tại; when POST /v1/classes/{class_id}/profiles với trường profile có cấu trúc; then tạo 201 profile/enrollment ref và tối đa một enrollment active. Given Teacher không được phân công, sai tenant hoặc Admin gọi route Teacher; when gửi command; then deny theo error envelope, không tạo profile/enrollment và không lộ dữ liệu ngoài scope. | Route PostgreSQL acceptance với actor Teacher đã xác thực và wiring thật. | Có. |
| M2-AT-05 | FR-PL-07, BR-48; S1b DEFERRED — NOT RUN | Given grant pending/active/revoked/expired với purpose/scope; when đọc profile; then chỉ grant active đúng scope cho phép. Đây là acceptance intent nếu owner mở lại S1b bằng quyết định và approval riêng; hiện chưa chạy. | Unit trước khi được mở; route PostgreSQL chỉ sau route được duyệt. | NOT RUN hiện tại. |
| M2-AT-06 | FR-PL-08, BR-48, NFR-34 grant portion; S1b DEFERRED — NOT RUN | Given field-scoped grant liên kết asset/token/cache/job; when revoke; then lần đọc/tải mới, token/cache access và job chưa accepted bị chặn, audit không ghi content/token. Đây là acceptance intent nếu owner mở lại S1b bằng quyết định và approval riêng; hiện chưa chạy. | Domain/service; API/asset/job integration sau route approval; không gọi provider. | NOT RUN hiện tại. |
| M2-AT-07 | NFR-36; S1b DEFERRED — NOT RUN | Given Admin thiếu permission, scope hoặc reason code; when gọi operation profile/grant thuộc M2; then deny và không lộ resource. Given permission/scope/reason hợp lệ theo policy owner đã duyệt; when gọi operation; then chỉ scope được cấp được phép và audit metadata-only. Media access và cross-org feedback không tính vào M2. Acceptance intent này không chạy khi S1b DEFERRED; NFR-36 vẫn PARTIAL theo D-143. | Domain/service; route PostgreSQL integration chỉ sau route/policy được duyệt. | NOT RUN hiện tại. |
| M2-AT-08 | Roadmap Mốc 2 (owner-lock, cancel, restart, ownership của job), D-127, NFR-34 — nguồn roadmap/decision, không phải FR-PL; S2. POST /v1/story-runs và POST /v1/story-runs/{id}/cancel là route test PostgreSQL S2 ngoài năm route nền M2; việc xếp các route này vào S2 là suy luận của kế hoạch, D-148 không nói về S2, chờ Task Approval S2. Không thêm route vào tập nền M2 và S2 chưa mở. | Given synthetic Parent/Teacher cùng owner lock có quyền hợp lệ; when concurrent separate POST /v1/story-runs requests submit cùng active owner; then có không hơn một active run/job/receipt hoặc side effect; không áp đặt loser status/error nếu contract chưa định nghĩa. Given run qua PREPARATION_REVIEW; when POST /v1/story-runs/{id}/cancel; then áp dụng D-127: DELETE_PENDING, nhả active-owner trong transaction, giữ result/assets/receipts và không coi là đã xóa. Replay/cancel lặp không tạo side effect trùng. Sau đó dừng tiến trình hệ điều hành thật, khởi động process mới với app composition mới trên cùng DB; recovery không tạo duplicate và stale result không được accepted. Recreate object trong cùng process không tính là restart. | PostgreSQL integration qua route, process stop/start thực, composition/repository/wiring thật. | Có. |
| M2-AT-09 | FEAT-064 N-1 route crosswalk; S2 (không phải FR-PL-08; các route /api/be1/... không thuộc SRS §21.2, đây là route test S2 ngoài năm route nền M2 theo suy luận của kế hoạch; D-148 không nói về S2, chờ Task Approval S2. Không thêm route vào tập nền M2 và S2 chưa mở) | Given child request tổng hợp và actor/device hợp lệ; when POST /api/be1/v1/assistance-requests, GET /api/be1/v1/organizations/{organization_id}/sessions/{session_id}/assistance-requests/{assistance_id}/status và POST /api/be1/v1/assistance-requests/{assistance_id}/cancel đi qua route thật; then auth, app composition, dependency wiring và PostgreSQL đều thật, không monkeypatch _build_child_binding hoặc override dependency cần kiểm. Bao phủ các trạng thái: success chỉ được expose sau durable committed SUCCEEDED; timeout phải giữ durable request/job/receipt facts nhưng không có authoritative successful result, không tự định nghĩa transition; orphan theo FEAT-064 approval là analysis invocation SUCCEEDED trong khi job RUNNING, không có result ref hoặc authoritative receipt, nên API/status không expose accepted. Dừng process hệ điều hành thật, khởi động app process mới cùng DB và kiểm tra recovery/status không công bố stale/orphan result như accepted. Timeout/recovery/terminal semantics chưa có owner quyết định thì giữ gate mở, không bịa status/error. Bắt buộc trước khi thoát S2 và trước D9 hoặc frontend/client integration. | PostgreSQL route integration qua real app composition/auth/dependency wiring và process restart. | Có, bắt buộc. |
| M2-AT-10 | FR-PL-25, BR-57, NFR-38; S1a | Given locale vi-VN, tuổi nguyên 36/120 và hàng cũ ngoài khoảng; when serialize/persist/read profile revision và thử tạo StoryRun; then metadata được giữ, hai biên hợp lệ; hàng cũ ngoài 36–120 không đủ điều kiện tạo StoryRun và bị từ chối rõ ràng, không clamp. Test không giả định DB chặn 121. Hành vi StoryRun với tuổi cũ 121–155 chưa được xác minh. POST /v1/story-runs và POST /v1/story-runs/{id}/cancel là route/service S2 ngoài năm route nền M2; M2-AT-08/09 là các route test S2 ngoài năm route nền theo suy luận của kế hoạch, D-148 không bàn S2 và chờ Task Approval S2. M2-AT-10 không thêm StoryRun hoặc route /api/be1 vào tập route nền; S2 chưa mở. Không đánh giá chất lượng AC-65 trong M2. | Contract/unit và persistence integration. | Có cho persistence. |
| M2-AT-11 | FR-PL-01; S1a; D-144 §9.3 và D-148 F-6 | Given yêu cầu tạo profile với data_origin REAL hoặc LEGACY_UNCLASSIFIED; when gửi yêu cầu; then bị từ chối và không tạo profile. Given thiếu consent record; then chỉ từ chối theo ca này nếu F-6 được giải quyết trong Task Approval S1a để giữ yêu cầu consent record ở S1a; nếu không, ca này chưa phải acceptance đã quyết. Chỉ profile có data_origin synthetic hợp lệ mới được tạo khi cặp origin/consent thỏa contract được owner duyệt. Test không giả định default data_origin trong mã; cách reconcile default và origin/consent CHECK tiếp tục là F-6 cần Task Approval S1a quyết. | Route PostgreSQL acceptance với actor đã xác thực và wiring thật. | Có. |

## 5. Dữ liệu, ownership và migration

### 5.1. Ownership logic theo DTR và code hiện có

| Owner | Nhóm bảng logic |
|---|---|
| BE1 | organizations, adult_identities, organization_assignments, classrooms, managed_profiles, enrollments, consent_records, data_lifecycle_requests, profile_revisions, profile_context_entries, profile_support_needs. |
| Parent | child_profiles, profile_revisions, profile_context_entries, profile_support_needs, data_authorizations, profile_share_grants. |
| Core | asset_lineage, upload_sessions, upload_parts, upload_command_receipts và Core metadata/audit/revision hiện hành theo DTR. |
| AI Jobs | job, attempt, command/completion receipts, semantic_request, cancellation_notice, outbox, job_events. |
| Story | runs, run_inputs, review_decisions, command receipts và các bảng Story theo DTR. |

Đây là ownership logic theo DTR, không xác nhận schema vật lý. backend/src/sketch2life/infrastructure/persistence/core_models.py là module Core hiện có; nó khai báo các mapping Core như core_aggregate_revisions, core_asset_metadata, core_audit_entries, core_outbox_events và các mapping canvas/receipt hiện hữu. Nó không định nghĩa bảng Parent. backend/src/sketch2life/infrastructure/story_run_lite/tables.py cũng khai báo mapping Core upload và StoryRun-lite. Chưa tìm thấy module persistence Parent; parent.* trong DTR vẫn là bảng logic đích chưa được hiện thực hóa trong source đã rà. Không suy ra schema vật lý Parent từ Core hoặc BE1. Ghi chú provenance: khẳng định về story_run_lite/tables.py trong đoạn này được phiên soạn trước ghi nhận từ source; path nằm ngoài allowlist S0-doc theo evidence §6 và chưa được S0-doc xác minh. Phiên Draft 10 chưa đọc lại source này.

Không tạo FK/SQL join xuyên owner/schema. Aggregate, job, asset và receipt có state riêng; job progress không thay aggregate state.

### 5.2. Mapping StoryRun-lite, DTR và 58 hàng synthetic

Provenance theo Draft 10: các khẳng định dưới đây về backend/src/sketch2life/infrastructure/story_run_lite/tables.py, migrations 20261102_story_run_lite.py, 20261103_story_upload_compat.py và metadata 20261102_pv_0001/pilot_vision ở §5.3 được phiên soạn trước ghi nhận từ source. Các source path này nằm ngoài allowlist S0-doc theo evidence §6 và chưa được S0-doc xác minh. Phiên Draft 10 chưa đọc lại các file đó; thông tin tương ứng tiếp tục là chưa xác minh.

- Source StoryRun-lite hiện có physical story.runs. Baseline đã cho phép DELETE_PENDING và FAILED; migration 20261104_story_revisions thêm child_age_months nullable với check 36–120 và mở rộng run_state cho SCRIPT_GENERATING, SCRIPT_GENERATION_UNKNOWN, SCRIPT_REVIEW và VIDEO_ADMISSION_PENDING. DELETE_PENDING/FAILED không phải các state mới do migration này thêm. Đây là static source mapping, không phải bằng chứng migration đã chạy.
- DTR mô tả logic story.runs với story_run_id, profile/owner refs và current_story_revision_ref; StoryRun-lite hiện dùng cột physical run_id. Giữ mapping run_id → story_run_id là crosswalk cần owner/chủ schema đối chiếu, không tự đổi tên hay giả định dữ liệu đã chuyển.
- Source tables.py đã khai báo physical story.review_decisions. Migration 20261104_story_revisions tạo physical story.story_revisions, story.story_scenes và story.story_revision_reviews; bảng mới story_revision_reviews khác với story.review_decisions đã có. DTR mô tả logic revisions/scenes/review_decisions; field/key/owner mapping với các bảng physical chưa được chứng minh tương đương. S0-doc phải lập crosswalk và đánh dấu unknown đến khi owner duyệt.
- Giữ mapping storyrun_upload_sessions → core.upload_sessions cùng upload parts/receipts; ghi owner columns, asset refs và history. Không đổi nghĩa hoặc xóa history âm thầm.
- Parent parent.child_profiles, parent.profile_revisions, parent.profile_share_grants và parent.data_authorizations vẫn là logical target trong DTR, không phải module/bảng hiện có được migration Story revisions tạo.
- B3 manifest/sign-off là đề xuất tới khi owner ký đúng bytes.
- D-144 §9.2 owner chọn giữ nguyên cả 58 hàng synthetic lịch sử và không cleanup. D-152 chọn schema-only copy cho S1a/S2, không sao chép application data. D-154 ghi nhận 58 hàng vẫn nằm trong sketch2life; không có quyền cleanup trong Draft 11.
- Trước migration: DB task-owned, physical schema inventory, target Alembic graph/revision, snapshot/restore expectation, exact approval. Kết quả B2 không chứng minh trạng thái DB hiện tại.

### 5.3. Alembic graph và command ceiling

Provenance theo Draft 10: ancestry gồm 20261102_pv_0001/pilot_vision và các dòng revision dưới đây được phiên soạn trước ghi nhận từ source; migration module 20261102_pilot_vision.py nằm ngoài allowlist S0-doc theo evidence §6 và chưa được S0-doc xác minh. Phiên Draft 10 chưa đọc lại migration module này; metadata tiếp tục là chưa xác minh. Repository có nhiều root/head và depends_on;

| Revision trên nhánh | down_revision | branch_labels | depends_on | Vai trò |
|---|---|---|---|---|
| 20261104_story_revisions | 20261103_story_upload_compat | None | None | Endpoint hiện thấy của nhánh StoryRun-lite trong source; chưa khẳng định toàn bộ các head của repository. |
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
6. backend/tests/integration/ai_jobs/test_migrations.py dùng maintenance connection để tạo/xóa DB; phần DB của test không chạy trên DB chính nếu chưa có thiết kế/approval riêng.

### 5.4. Delta SRS/DTR v2.7 và DB owner-reported cho các pha sau

**Origin và consent.** SRS v2.3 đã ghim và SRS v2.7 dùng SYNTHETIC_TEST; CHECK vật lý được D-154 ghi nhận dùng SYNTHETIC_DEV. Sai khác có trước v2.7, không phát sinh từ việc đối chiếu draft. F-7 mới cho Task Approval S1a: owner chọn tên chuẩn và cách ánh xạ giữa contract với schema; Draft 11 không tự chọn và không cho migrate theo lựa chọn này. CHECK ck_be1_profile_origin_consent_refs chỉ cho SYNTHETIC_DEV khi consent_id và consent_purpose_ref đều NULL; trong khi đường tạo profile hiện được D-148 mô tả là yêu cầu consent record. Đây là mâu thuẫn quan sát được giữa hướng synthetic consent và CHECK vật lý; F-6 vẫn là quyết định owner, không được suy ra đã giải quyết.

**Tuổi.** D-148 mục 6 và 7 giữ nguyên. SRS v2.7 §31.10 mục 16 để mở quyền read/edit/new run/archive/delete với bản ghi legacy 121–155 tháng. Quy tắc trong M2 “không đủ điều kiện tạo StoryRun” là quy tắc cục bộ của kế hoạch trên một mục SRS còn mở, không phải câu chữ SRS. CHECK vật lý 36 ≤ age_months ≤ 155 là dữ kiện D-154; Task Approval S1a phải chốt nguồn tuổi và phạm vi hành động, không migration trong Draft 11.

**Quota.** SRS v2.7 §11.2 và DTR v2.7 §14.2 item 10 ghi Teacher video dùng school organization pool, không có TEACHER_ACCOUNT. DTR v2.3 đang ghim vẫn liệt kê TEACHER_ACCOUNT nên dòng Draft 10 nói quota Teacher còn mở là đúng theo pin cũ; khác biệt v2.7 chỉ là note so sánh cho tới khi owner đổi pin. Không ảnh hưởng route S1a. Evidence S0-doc đã đóng theo D-150, không sửa.

**S1b.** V2.7 NFR-36/AC-49/§31.3 yêu cầu grant chỉ ACTIVE sau khi Teacher được nêu tên chấp nhận; actor chấp nhận lời mời gửi cho cả trường vẫn mở. S1b giữ DEFERRED. Nếu owner mở lại S1b, M2-AT-05 cần được viết lại theo trạng thái invitation/acceptance khi đó; không đổi test hoặc status trong Draft 11.

**S2 và DTR receipt.** V2.7 SRS §21.2 ghi POST /v1/story-runs có typed optional LessonVersionRefV1 (dòng 1592); POST /v1/story-runs/{id}/cancel vẫn dùng {id} (dòng 1602). Draft 11 chuẩn hóa tham chiếu hiện hành trong M2-AT-10 sang {id}; đây là chỉnh nhãn theo contract source, không mở S2. DTR v2.7 thiếu core.upload_command_receipts và story.command_receipts so với amendment StoryRun-lite được ghi trong nguồn DTR v2.3; số đếm liên quan đổi 94/142 thành 92/140. Chủ schema cần đối chiếu hai receipt trước S2; không sửa DTR, migration hoặc D-151 tại đây.

**DB S1a/S2 sau D-154.** D-152 chọn cùng instance PostgreSQL 17 native, nhưng database riêng schema-only copy, không copy data. D-154 ghi DB này chưa được tạo tại thời điểm closure; owner cập nhật sau đó rằng sketch2life_m2_s1a đã tạo, có 117 bảng và be1_organizations có 0 hàng. Owner cũng cung cấp tên dump sketch2life-schema-only-20261107.dump, SHA-256 E02F2D6E43053FBBACC388002AC9A66FABC73A9AE51399704FB65179BD1BE2E8. Đây là cập nhật owner-provided sau D-154, Draft 11 không độc lập kết nối hoặc kiểm tra dump. Chưa chạy Alembic trên DB copy; cách đánh dấu/current revision và target thuộc Task Approval S1a. Không có approval ghi/migration vào DB này.

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
2. Identity, role, tenant, profile ownership, Admin class/assignment, Teacher profile/enrollment, age provenance và synthetic-only đạt M2-AT-01/02/03/04A/04B/10/11 theo acceptance được duyệt; ca thiếu consent record của AT-11 chỉ là bắt buộc nếu Task Approval S1a giải quyết F-6 theo hướng giữ consent record ở S1a. DB thật cho route/persistence.
3. D-144 §9.3 hoãn consent/share và OI-05..08, yêu cầu synthetic-only và deny REAL/LEGACY_UNCLASSIFIED; D-148 mục 8 giữ S1b (grant/consent/share) DEFERRED để xem xét lại sau khi S1a đóng. D-148 F-6 ghi nhận mã hiện tại yêu cầu consent record và có mismatch với synthetic-only/origin CHECK; F-6 còn mở cho Task Approval S1a. Cách xử lý consent record ở S1a trong khi consent/share thuộc S1b vẫn cần owner quyết; không tự chọn. Ca thiếu consent record trong M2-AT-11 chỉ áp dụng nếu Task Approval S1a giữ yêu cầu đó.
4. Lifecycle đạt M2-AT-08/09; request và cancel phải được gọi qua route thật. N-1 PostgreSQL route test với wiring thật bắt buộc trước khi thoát S2 và trước D9/client integration; B1 orphan có reconciliation/read-exposure contract và regression trước dữ liệu non-synthetic/provider.
5. Target migration/schema inventory/data disposition/rollback limits được owner phê duyệt; DB/source/snapshot gate lệch thì dừng. Offline-check là historical fact-only; Alembic execution, live graph reconciliation và M2 mypy baseline chưa chạy nên không đóng gate.
6. OpenAPI request/response/error parity được freeze trước client integration; P3 đóng trong S3.
7. Evidence lưu tại feature evidence path được approval chỉ định; PARTIAL/NOT RUN/owner-run provenance ghi đúng. Plan review và implementation review là hai việc riêng.
8. Không mở M3–M6, không bật provider/Modal hoặc workload.
9. Draft 10 vẫn DRAFT / AWAITING INDEPENDENT REVIEW; chưa có review Draft 10, owner approval hay implementation approval.

## 8. Candidate allowlist theo subphase

Draft 4 báo cáo 49 path đã được xác nhận tồn tại; phiên lập Draft 5 (lịch sử) không kiểm lại toàn bộ danh sách này. Các path dưới đây là candidate trong kế hoạch, trừ cột "Path mới", ghi chưa xác minh. Bảng chỉ để owner/reviewer xem xét trước Task Approval; không cấp quyền sửa. Các nguồn mới ở S0-doc chỉ đọc, không mở allowlist thực thi. Không dùng wildcard.

Quy ước:

- **Chỉ đọc:** tham chiếu hoặc baseline hồi quy; không được sửa nếu Task Approval không nêu đích danh file và lý do.
- **Candidate có thể sửa:** chỉ được sửa khi Task Approval của đúng pha liệt kê file đó, kèm hash trước khi sửa.
- **Path mới:** file chưa tồn tại; tên và hash phải có trong approval trước khi tạo. Test hiện có là baseline hồi quy chỉ đọc; test M2 là file mới.
- **Hồ sơ governance** (CONTEXT, DECISIONS, STATUS, TASK_APPROVAL của FEAT-063/FEAT-064, ledger) chỉ do phiên ghi (Codex) cập nhật sau lệnh của owner. Chúng nằm ngoài allowlist của mọi phiên thực thi và chỉ đọc đối với phiên thực thi.
- Draft 1–10 của plan này là đầu vào chỉ đọc; Draft 11 là artifact DRAFT đang chờ review độc lập và owner quyết định.

| Pha | Chỉ đọc | Candidate có thể sửa | Path mới (chưa xác minh) | Exclusions / hard stop |
|---|---|---|---|---|
| S0-doc | Mọi tài liệu pin ở §1; features/FEAT-063-system-architecture-rearchitecture/SOURCE_REGISTER.md; features/FEAT-063-system-architecture-rearchitecture/evidence/COMMIT_WHITESPACE_NORMALIZATION_20261103.md; Draft 1–9 của plan này; backend/alembic/versions/20261104_story_revisions.py; backend/src/sketch2life/infrastructure/persistence/core_models.py; .claude/handoff/logs/GB2_T12_OFFLINE_20261105A/offline-check.txt (local, git-ignore; Draft 8 từng báo ENOENT; Draft 10 đọc bytes hiện tại và re-verify hash 6FF16B2E77EE7DB7CE18521484B92FAA9B40F685393D35A7746E74236313E143 khớp); hồ sơ governance. | Không có file hiện có. | Kế hoạch tiếp theo nếu owner yêu cầu; evidence bổ sung chỉ khi được duyệt (tên chưa xác minh). | Không sửa source/test/migration/SRS/DTR/roadmap/governance. Cần DB hoặc file ngoài approval thì dừng. |
| S0-owner-run | backend/alembic/env.py; backend/alembic/versions/20261014_0002_be1_runtime.py; backend/alembic/versions/20261015_ai_0001_ai_jobs_schema.py; backend/alembic/versions/20261028_ll_0001_lesson_library.py; backend/alembic/versions/20261031_be1_synthetic_eligibility.py; backend/alembic/versions/20261101_be1_age_provenance.py; backend/alembic/versions/20261102_pilot_vision.py; backend/alembic/versions/20261102_story_run_lite.py; backend/alembic/versions/20261103_story_upload_compat.py; backend/alembic/versions/20261104_story_revisions.py; backend/src/sketch2life/infrastructure/persistence/be1_models.py; backend/src/sketch2life/infrastructure/persistence/core_models.py; backend/src/sketch2life/infrastructure/ai_jobs/sql/tables.py; backend/src/sketch2life/infrastructure/story_run_lite/tables.py. Các path này là lịch sử input chỉ đọc của lượt S0-owner-run đã đóng theo D-154. | Không có. | Inventory owner-run theo hash trong D-154; kết quả được ghi là quan sát, không phải approval ghi. | S0-owner-run CLOSED đúng phạm vi lượt đọc; không có migration, mypy hoặc proof synthetic-only đầy đủ. S1a vẫn cần Task Approval riêng và không dùng shared DB cho ghi. |
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

### Draft 11 — việc còn phải chốt trong Task Approval

- F-1 route assignment, F-2 cardinality một Teacher active, F-4 quyền gọi Teacher profile route, F-6 origin/consent và F-7 canonical data_origin mapping đều còn cần owner quyết định/Task Approval. Owner từng nghiêng về các hướng đề xuất F-1/F-2/F-4/F-6/F-7 nhưng chưa có quyết định chính thức; ghi là đề xuất, không chuyển thành owner decision.
- Nguồn tuổi cần được chốt cùng D-148 mục 6/7; C5 vẫn hỏi liệu giới hạn năm route nền của D-148 mục 4 có áp dụng cho S2 route tests hay không.
- D-151 C1–C4 vẫn phải được disposition trong approval phù hợp: C1 khôi phục guardrail upgrade-heads mặc định và sửa lead-in Alembic bị cụt; C2 ghi rõ tầng/layer của M2-AT-10 thuộc S1a trước S2; C3 dùng path placeholder {id} theo SRS §21.2 và kiểm nhất quán các test/approval; C4 giới hạn pass gate S3 vào acceptance đã được Task Approval S1a duyệt. C5 là câu hỏi riêng trước S2 Task Approval.
- F-3 (denial thống nhất cho assignment/scope) và F-5 (giới hạn tuổi) là nhãn coordinator ánh xạ từ D-148 mục 5–7; nội dung hướng đã được D-148 chốt, không phát minh thêm decision ID.
- F-7 bổ sung mapping dữ liệu synthetic; không được gộp nó với F-6 hoặc tự quyết thay owner. Mỗi Task Approval cần pin đúng nguồn, database/identity, allowlist, test matrix, command ceiling và stop gate.

## 9. CẦN QUYẾT ĐỊNH CỦA OWNER

D-142..D-154 ghi các hướng, owner dispositions và giới hạn hiện hành. D-151 chấp nhận Draft 10 làm planning baseline, không phải approval triển khai; D-150 đóng S0-doc ở phạm vi tài liệu; D-154 đóng S0-owner-run ở phạm vi một lượt inventory chỉ đọc. D-148 vẫn là hướng thiết kế chứ không phải approval S1a. D-146 xác nhận hiện không có implementation approval. Các cột “Mặc định đề xuất, không phải quyết định” vẫn chỉ là gợi ý.

| # | Trạng thái theo D-142..D-150 | Lựa chọn | Hệ quả | Pha bị chặn | Mặc định đề xuất, không phải quyết định |
|---|---|---|---|---|---|
| 1. DB task-owned | D-144 §9.1 được hiệu chỉnh về instance native theo D-152; S0-owner-run đã đóng theo D-154 | S0-owner-run chỉ đọc dùng database sketch2life trên PostgreSQL 17 native Windows localhost:5433. Các pha có ghi S1a/S2 dùng database riêng cùng instance, tạo bằng schema-only copy, không chép dữ liệu; D-152. Task Approval S1a vẫn phải pin identity, người chạy, restore, bằng chứng dữ liệu, target revision và command ceiling. | DB sketch2life không được dùng cho ghi; DB riêng không tự cấp quyền chạy migration/route test. Cần approval từng pha và xác minh lại identity. | S1a/S2 acceptance có persistence. | Dùng database riêng task-owned theo bản schema-only copy đã tạo; mọi chi tiết thực thi còn phải được S1a Task Approval duyệt. |
| 2. 58 synthetic rows | Đã quyết theo D-144 §9.2 | Giữ nguyên cả 58 hàng synthetic; không cleanup. | Copy/cleanup có thể mất history/đổi owner; không được tự làm. | S0-owner-run/S2. | Giữ nguyên, không cleanup. |
| 3. B4b/OI-05..08 | Hoãn theo D-144 §9.3; S1b DEFERRED theo D-148 mục 8 | Hiện hoãn consent/share và OI-05..08; synthetic-only, deny REAL và LEGACY_UNCLASSIFIED. SRS v2.3 đã ghim đặt OI-05..08 tại §14.1, dòng 1130–1133. SRS/DTR v2.7 là draft chưa gộp và được ghi riêng ở §1.5/§5.4. | Chưa có authority cho consent hoặc dữ liệu thật; không biến v2.7 thành pin. | S1b và dữ liệu thật. | Giữ hoãn tới khi owner có quyết định và approval riêng. |
| 4. B5 receipt legacy | Tạm hoãn theo D-144 §9.4; nhu cầu consumer còn mở | Giữ B5 unopened đến khi consumer xác nhận cần; đây không phải kết luận B5 không được dùng. | Nếu cần: xác định consumer, payload, retention, mapping; nếu không: disposition chính thức. | S1b/S2 nơi receipt dùng. | Không mở B5 khi chưa có consumer xác nhận. |
| 5. Schema convergence | Hướng không migrate/preserve history đã quyết theo D-144 §9.5; mapping còn mở | Không migrate schema; giữ history; mapping được soạn để owner review nhưng chưa được chọn. | Mapping không rõ có thể mất liên kết/history hoặc tạo hai nguồn sự thật. | S0-owner-run/S2 migration. | Giữ history; chưa migrate khi chưa có mapping ký duyệt. |
| 6. Mypy baseline | Hướng read-only baseline đã quyết theo D-144 §9.6; command và output còn mở | Owner-run một baseline read-only, ghi command/version; M2 không thêm diagnostic. Draft 9 chưa có command/output; Draft 10 giữ NOT RUN. | test_be1_postgres_api.py hiện NO VERDICT; crash tool không phải pass. Quyết định không miễn kiểm tra lỗi mới. | S0-owner-run; S1/S2 nếu sửa target; S3 closeout. | Đo baseline read-only có approval, cùng command/version, không thêm lỗi; không suy diễn phần chưa chạy. |
| 7. B0 provenance | Đã quyết theo D-144 §9.7; S0-doc đóng theo D-150 | Owner xác nhận normalized bytes tương đương chỉ cho B0 plan: original hash 03AEA386B8545624100688B68AA828A84CD154B47857CB5E98FB06354D6BB582; current hash 773C4A8340C8E33AE39764D920B042AC19BACBAF6DC561FE9D5D3DFFCC4B5A5A. So sánh do coordinator thực hiện, không phải independent reviewer. | Xác nhận không mở rộng sang bảy file khác trong normalization evidence, không xác nhận snapshot, và không thay independent review. | Không còn chặn S0-doc; các requirement khác dựa B0 vẫn chịu source limits. | Owner ghi xác nhận qua approval ghim evidence; không sửa pin để làm hash khớp. |
| 8. Baseline review | Đã xác nhận theo D-142 cho review Draft 7; Draft 8, Draft 9 và Draft 10 dùng cùng HEAD | dd70685eae58aaaefea3e567f5c23d09345a8513 là review baseline; nếu HEAD thay đổi thì phải xác nhận lại. Đây chỉ là baseline, không phải scope approval. | Draft 9 được lập trên cùng HEAD; review độc lập Draft 9 NEEDS_REVISION. Draft 10 cổng HEAD khớp; hash phù hợp không thay owner review hoặc mở pha. | Baseline của review kế hoạch. | Không có mặc định đề xuất; nếu HEAD đổi thì xác nhận lại theo D-142. |
| 9. NFR-36 disposition | PARTIAL đã quyết theo D-143; milestone mapping còn mở | Giữ PARTIAL cho M2. Child media→M5 và cross-org feedback→M6 vẫn là đề xuất, owner chưa chọn. | NFR-36 gồm access child media/profile và cross-role grant theo permission/reason/audit; M2-AT-07 NOT RUN khi S1b hoãn; không claim toàn requirement PASS. | M2-AT-07, media và feedback phase tương ứng. | Không claim toàn NFR-36 PASS từ M2. |
| 10. NFR-38 / AC-65 disposition | PARTIAL đã quyết theo D-143; milestone mapping còn mở | Giữ PARTIAL cho M2. AC-65 story→M4 và video→M5 vẫn là đề xuất, owner chưa chọn. | M2-AT-10 chỉ kiểm metadata locale/age; AC-65 còn age-band/context đã duyệt, Vietnamese content và video cá nhân hóa theo tranh trẻ. | M2-AT-10, M4 story và M5 video. | Mapping M4/M5 là đề xuất; không claim chất lượng AC-65 đã đạt. |

Các mục còn mở: S0-owner-run đã CLOSED trong giới hạn D-154; K3 FAIL, K4 source comparison và mypy baseline còn nợ, K5/K7 NOT RUN. DB schema-only copy sketch2life_m2_s1a được owner báo đã tạo sau D-154; chi tiết ở §5.4, chưa có approval ghi/migration. Trước S1a Task Approval cần chốt F-1, F-2, F-4, F-6, F-7, nguồn tuổi, C5 và điều kiện C1–C4 của D-151; F-3/F-5 là cách đánh số do coordinator ánh xạ từ các quyết định D-148. Age-band catalog, share purpose/expiry, B5 consumer, DELETE_PENDING cleanup và quota-scope khác biệt giữa các phiên bản SRS/DTR còn mở. S1b chỉ được xem xét sau S1a và quyết định riêng. Các default vẫn không phải quyết định owner.

## 10. Gói cần có trước launch

- Draft 11 đang DRAFT / chờ review độc lập và owner quyết định; D-151 chỉ chấp nhận Draft 10 làm planning baseline. Review Draft 9 là NEEDS_REVISION (0 P1 / 1 P2 / 7 P3; 9/11 finding Draft 8 RESOLVED, 2 PARTIAL), không phải verdict của Draft 11. D-150 chỉ đóng S0-doc ở phạm vi tài liệu; D-154 đóng S0-owner-run trong phạm vi một lượt đọc chỉ đọc.
- S0-owner-run đã CLOSED ở phạm vi D-154; K3 FAIL, K4/K6 COLLECTED, K5/K7 NOT RUN. Không suy ra schema/Alembic đã hội tụ hoặc dữ liệu synthetic-only.
- S1a dùng D-148 làm hướng thiết kế nhưng vẫn cần Task Approval riêng, giải quyết các mục tại §8 và nêu exact file allowlist theo từng path, path mới, exclusions; không dùng wildcard và §8 không tự cấp quyền sửa file.
- Owner quyết các lựa chọn còn mở tại §9 ảnh hưởng tới pha được launch và ghi lựa chọn trong Task Approval. S1b hiện DEFERRED, chỉ được xem xét lại sau khi S1a đóng; D-148 không approve S1a hoặc thay đổi SRS.
- Ghim plan hash, branch/HEAD, nguồn, snapshot manifest khi một pha được đề xuất để launch; không tự ghi hash Draft 10 vào hồ sơ governance nào.
- Ghi DB task-owned identity, database name/container, người tạo/chạy, dữ liệu, snapshot/restore, proof synthetic-only và cleanup boundary.
- Ghi Alembic graph/target revision, offline plan/SQL review và command ceiling; chưa có approval thì không chạy migration.
- Ghi test matrix/tầng test; route acceptance dùng PostgreSQL thật/wiring thật khi route là đối tượng.
- Ghi disposition B1 stale-owner orphan, N-1 route PostgreSQL request/cancel, OpenAPI P3, mypy baseline và mọi PARTIAL/NOT RUN. Draft 10 ghi 19/19 pin khớp tại thời điểm tạo; Draft 11 rehash 19 nguồn: 17 khớp, hai pin governance DECISIONS.md/TASK_APPROVAL.md khác do D-152–D-154 được append sau đó. Các giá trị lịch sử trong §1.1 không đổi. Offline-check là fact-only; không có mypy baseline M2 và không chạy migration trong S0-owner-run.
- Task Approval phải nêu rõ phase, scope, file allowlist, evidence, DB identity và command ceiling. Approval một pha không mở pha khác, M3–M6, provider hay Modal. D-146 xác nhận hiện không có implementation approval; OWNER_MODAL_CALL_APPROVED=NO không đổi.

Cho tới khi các quyết định và approval đúng pha được ghi nhận, Draft 11 vẫn DRAFT / AWAITING INDEPENDENT REVIEW; không launch M2 và không có quyền sửa code, migration, DB hoặc gọi provider.

### 10.1. Ghi chú tác động SRS v2.7 lên M3–M6 (không đổi phạm vi)

Các điểm sau chỉ để cảnh báo dependency khi soạn kế hoạch riêng; không sửa B0 plan, không đổi mốc và không mở M3–M6:
- SRS v2.7 §11.1 liệt kê tám AI job target: STORY_RUN, VIDEO_GENERATION, VIDEO_GENERATION_SCENE, LESSON_SOURCE_DOCUMENT, LESSON_LIBRARY_VERSION, LESSON_VERSION_VISUAL_ASSET, LESSON_SKETCH_DECK_REVISION và PARENT_SKETCH_GUIDE.
- FR-T-08 ghim LessonVersionRefV1 typed theo version/hash; §6.3 cập nhật hướng model AI.
- UC-06/08/12/13 đổi tên School Manager; §31.10 mục 14–17 thêm câu hỏi role/permission persistence-resolver, plan supersession, age legacy và audit.
- DTR v2.7 §§14.5–14.6 nêu 41 bảng local được kiểm kê trong tài liệu; đây không phải inventory live do Draft 11 chạy.
- Những ghi chú này không thay đổi pin SRS v2.3, B0 plan theo D-144 §9.7, thứ tự milestone hoặc owner authority.

### 10.2. Trình tự đề xuất và checkpoint (ước lượng sơ bộ, không phải cam kết)

| ID | Công việc | Phụ thuộc | Song song | Acceptance/checkpoint | Ước lượng | Rủi ro |
|---|---|---|---|---|---|---|
| P1 | Chốt owner questions và viết Task Approval S1a riêng | Draft 11 review/owner decision | Có thể đối chiếu tài liệu v2.7 độc lập; không ghi cùng file governance đồng thời | Owner quyết F-1/F-2/F-4/F-6/F-7, tuổi, C1–C4/C5; exact DB/allowlist/command | Nhỏ, 0.5–1 ngày; giả định owner phản hồi liền | Quyết định chưa chốt sẽ chặn S1a |
| P2 | Thực thi S1a sau approval | P1 và database identity/restore được xác nhận | Không song song trên file BE1 dùng chung | Role/tenant/profile/age cases chạy đúng tầng đã duyệt; PostgreSQL route tests dùng wiring thật; evidence đủ | Lớn, 3–7 ngày; giả định DB task-owned sẵn sàng | K3 mismatch và synthetic-only proof chưa có |
| P3 | Review độc lập và owner close S1a | P2 | Không song song với sửa cùng diff | Findings được xử lý; owner ghi closure riêng; không tự mở S1b | Trung bình, 1–2 ngày | Review có thể yêu cầu vòng sửa |
| P4 | Quyết định có mở lại S1b không; nếu có, lập approval mới | P3; hiện S1b DEFERRED | Chỉ làm hồ sơ riêng; hiện DEFERRED | Owner quyết; nếu không mở, ghi NOT RUN/DEFERRED và dừng | Chưa ước lượng tới khi owner quyết | Consent/share và OI-05..08 còn gate |
| P5 | Chuẩn bị Task Approval S2 và đối chiếu schema receipt/route | P3; C5; DTR/schema owner đối chiếu | Có thể làm tài liệu, không chạy DB | Chốt scope, path {id}, hai receipt, target Alembic, N-1, orphan B1, DB identity | Trung bình, 1–2 ngày; giả định chủ schema sẵn sàng | DTR v2.7 chưa pin và graph DB lệch |
| P6 | Thực thi S2 sau approval | P5 và S1b disposition | Không song song với S1a trên file chung | AT-08/09 theo approval; route request/cancel thật, recovery/orphan gates, migration chỉ đúng target được duyệt | Lớn, 5–10 ngày; giả định môi trường task-owned sẵn sàng | Rủi ro persistence, lifecycle và reconciliation |
| P7 | S3 freeze/review sau các pha được owner mở | P2/P3 và P6; S1b disposition | Không song song với sửa contract cuối | OpenAPI P3, N-1, B1 orphan và mọi PARTIAL/NOT RUN được disposition; review và owner closure riêng | Trung bình, 2–4 ngày | Gate frontend và phụ thuộc schema |

Critical path đề xuất là P1 → P2 → P3 → P5 → P6 → P7; P4 chỉ chạy nếu owner mở lại S1b. Không có bước nào trong bảng được launch bởi Draft 11. Nguồn: D-144, D-148, D-151–D-154, DTR/SRS pinned v2.3 và các ghi chú đối chiếu v2.7 ở §1.5/§5.4.

Lịch sử bản: Draft 7 → Draft 8 — cập nhật theo D-142..D-150 và evidence S0-doc; sửa status/gates, traceability, Task Approval items và owner-decision ledger. Draft 8 vẫn chờ review độc lập. Draft 8 → Draft 9 — xử lý các finding được liệt kê ở bảng thay đổi; Draft 9 vẫn DRAFT, chờ review độc lập. Draft 9 → Draft 10 — sửa các finding F-1..F-8 theo review độc lập Draft 9; D-151 sau đó chấp nhận Draft 10 làm planning baseline. Draft 10 → Draft 11 — giữ pin v2.3, thêm so sánh v2.5–v2.7, cập nhật S0-owner-run theo D-154, ghi DB S1a owner-reported, cập nhật các điều kiện còn mở; Draft 11 vẫn DRAFT.

## Thay đổi từ Draft 9 sang Draft 10

| Mục và dòng (Draft 10 / Draft 9) | Thay đổi | Nguồn review |
|---|---|---|
| Đầu file — Draft 10 dòng 1, 5–6 / Draft 9 dòng 1, 5–6 | Đổi tiêu đề và trạng thái; ghi review Draft 9 NEEDS_REVISION (0 P1 / 1 P2 / 7 P3; 9/11 finding Draft 8 RESOLVED, 2 PARTIAL), giới hạn cập nhật và trạng thái DRAFT. | Review Draft 9; F-1–F-8 |
| Lịch sử D8→D9 — Draft 10 dòng 37, 40 / Draft 9 dòng 37; đoạn đính chính chưa có | Sửa mô tả route test trong lịch sử; thêm đính chính các neo bảng sai, mục bị bỏ sót, tiêu chí S3 bị bỏ sót và số hunk phụ thuộc công cụ/ngữ cảnh. | F-1, F-2 |
| §0 Git baseline — Draft 10 dòng 120–136 / Draft 9 dòng 118 | Ghi HEAD, index rỗng và toàn bộ git status --short trước khi tạo Draft 10; giữ rõ warning global-ignore không xác định path bị ảnh hưởng. | F-3 |
| §1 pins — Draft 10 dòng 175–179 / Draft 9 dòng 157–161 | Ghim hash Draft 9 làm nguồn trực tiếp, Draft 8 làm lịch sử; ghi kết quả đọc lại 19/19 pin tại thời điểm soạn. | F-3 |
| §3 subphase — Draft 10 dòng 262, 265 / Draft 9 dòng 244, 247 | Gắn điều kiện consent-record AT-11 vào F-6/Task Approval S1a; giới hạn S3 để chỉ AT-05/06/07 có thể NOT RUN/DEFERRED và mọi AT khác phải chạy, pass theo điều kiện đề xuất owner chấp nhận. | F-5, F-6 |
| §4 route crosswalk — Draft 10 dòng 271, 278 / Draft 9 dòng 253, 260 | Ghi M2-AT-08/09 là route test S2 ngoài năm route nền M2; AT-09 dùng /api/be1 routes không thuộc SRS §21.2; gắn nhãn suy luận, D-148 không nói về S2, chờ Task Approval S2; không thêm route hoặc mở S2. | F-1 |
| §4 evidence note — Draft 10 dòng 288 / Draft 9: không có | Ghi xung đột BR-58 giữa evidence dòng 53 và D-148 mục 8; theo D-148, nhắc D-150 đã chuyển tiếp, giữ evidence S0-doc đã đóng và không sửa. | F-8 |
| §4.2 tests — Draft 10 dòng 309, 311, 316–319 / Draft 9 dòng 289, 291, 296–299 | Gắn org_id case là suy luận từ D-148 mục 5; viện dẫn đúng SRS §21.2 dòng 1558 cho cardinality Teacher; làm rõ AT-08/09 ngoài route set và gắn điều kiện F-6 vào ca thiếu consent record ở AT-11. | F-1, F-5, F-7 |
| §5 provenance — Draft 10 dòng 333, 339, 352 / Draft 9 dòng 313, 319, 332 | Mở rộng provenance cho tables.py và metadata 20261102_pv_0001/pilot_vision: phiên soạn trước ghi nhận từ source, ngoài allowlist S0-doc, chưa được S0-doc xác minh; Draft 10 chưa đọc lại. | F-4 |
| §5 wording sweep — Draft 10 dòng 356, 374 / Draft 9 dòng 336, 354 | Làm rõ các câu về migration head và database trong lần quét toàn văn, không thay đổi trạng thái hay authority. | F-1 |
| §7 criteria — Draft 10 dòng 405, 406, 412 / Draft 9 dòng 385, 386, 392 | Thống nhất consent/share được hoãn theo D-144 §9.3 và D-148 mục 8; để F-6 cho Task Approval S1a; cập nhật trạng thái Draft 10. | F-3, F-5 |
| §8 allowlist — Draft 10 dòng 424, 428 / Draft 9 dòng 404, 408 | Cập nhật phạm vi đầu vào chỉ đọc từ Draft 1–8 sang Draft 1–9 và nhận diện Draft 10 là artifact chờ review. | F-3 |
| §9–§10 launch notes — Draft 10 dòng 461, 463, 471, 475, 479, 482 / Draft 9 dòng 441, 443, 451, 455, 459, 462 | Sửa các nhãn Draft 8 đã cũ, ghi verdict Draft 9, cập nhật re-hash 19/19 và giữ Draft 10 ở trạng thái DRAFT; không tự ghi hash Draft 10 vào hồ sơ. | F-3 |
| Lịch sử bản — Draft 10 dòng 484 / Draft 9 dòng 464 | Thêm mục Draft 9 → Draft 10 và ghi trạng thái chờ review. | F-3 |
| Bảng thay đổi — Draft 10 dòng 486–504 / Draft 9: không có | Thêm bảng đối chiếu từng thay đổi Draft 9 → Draft 10 theo mục, số dòng và finding review; đây là bảng được yêu cầu cho Draft 10. | Yêu cầu soạn Draft 10 |

## Thay đổi từ Draft 10 sang Draft 11

| Mục / dòng Draft 11 (đối chiếu Draft 10) | Thay đổi thực tế | Căn cứ |
|---|---|---|
| Đầu file, dòng 1 và 3–6 (Draft 10 dòng 1 và 3–6) | Đổi nhãn Draft 11, cập nhật trạng thái chờ review/owner; giữ pin SRS v2.3 và ghi rõ v2.5–v2.7 chỉ là draft đối chiếu, S0-owner-run chỉ đóng trong phạm vi đọc inventory với các kết quả K3/K4/K5/K6/K7 được nêu. | Yêu cầu Draft 11; D-150, D-151, D-154 |
| §0, dòng 110 và 136 (Draft 10 cùng dòng) | Đổi mô tả baseline từ cần xác nhận sang đã ghi nhận; phân biệt trạng thái trước Draft 10 với status trước Draft 11. | Checkout read-only; Draft 10 |
| §1.4, dòng 221; §1.5, dòng 229–264 (Draft 10 dòng 221; không có §1.5) | Sửa nhãn OI-05..08 từ §29.2 thành §14.1; thêm refs/hash v2.5–v2.7, khác biệt nhánh/decision-ID, bảng ánh xạ dòng v2.3→v2.7 và kết luận phạm vi S1a không đổi. | SRS/DTR refs qua `git show`; review đối chiếu được owner cung cấp |
| §2.4, dòng 290–293 (không có phần tương ứng trong Draft 10) | Thêm ghi chú role v2.7: School Manager, Admin nội dung là permission, deny mặc định cho child media; giữ nguyên D-148 và ca âm tính M2-AT-01. | SRS v2.7 §§3, 20, 31.3, §31.10 mục 14; D-148 |
| §3, dòng 296 và 301; §3.1, dòng 309–316 (Draft 10 dòng 296, 301; không có §3.1) | Cập nhật trạng thái S0-owner-run theo D-154; thêm provenance, inventory, K1–K7, K3 mismatch, giới hạn synthetic-only và các mục chưa chạy; không suy ra migration hoặc mở S1a. | D-153/D-154 và kết quả owner-run được ghi trong hồ sơ |
| §4.2, dòng 356 và 366 (Draft 10 dòng 308 và 318) | Ghi rõ cách hiểu Admin nội dung trong M2-AT-01; chuẩn hóa route cancel trong M2-AT-10 thành `/{id}` theo SRS §21.2, không mở S2. | SRS v2.7; D-148; D-151 |
| §5.2, dòng 395 (Draft 10 dòng 347) | Thay các lựa chọn giữ/copy/cleanup còn mở bằng disposition D-144 giữ 58 hàng, D-152 schema-only copy không dữ liệu, D-154 xác nhận hàng còn trong DB; không cấp quyền cleanup. | D-144, D-152, D-154 |
| §5.4, dòng 424–437 (không có phần tương ứng trong Draft 10) | Thêm delta về origin/consent, tuổi legacy, quota, S1b, route/receipt S2 và DB schema-only copy được owner báo tạo; phân biệt quan sát với dữ kiện chưa tự xác minh. | SRS/DTR v2.7 qua `git show`; D-144, D-148, D-152, D-154; owner update |
| §8, dòng 486 và 491 (Draft 10 dòng 424 và 429) | Mở rộng danh sách input tới Draft 1–10; thay S0-owner-run từ kế hoạch chưa chạy sang lượt inventory đã đóng trong giới hạn D-154. | D-154 |
| §8, dòng 512–519 (không có phần tương ứng trong Draft 10) | Thêm F-1/F-2/F-4/F-6/F-7, nguồn tuổi, C5 và D-151 C1–C4 làm việc cần disposition trong Task Approval S1a; nêu rõ đề xuất owner chưa phải quyết định và F-3/F-5 là nhãn coordinator ánh xạ. | D-148, D-151; hướng owner đã nêu nhưng chưa chốt |
| §9, dòng 522, 526, 528 và 537 (Draft 10 dòng 452, 456, 458 và 467) | Cập nhật tham chiếu D-142..D-154, DB target theo D-152, OI-05..08 theo pin v2.3 và các việc còn mở sau lượt S0-owner-run. | D-142..D-154; SRS v2.3/v2.7 đối chiếu |
| §10, dòng 541–552 (Draft 10 dòng 471–482) | Giữ Draft 11 ở trạng thái DRAFT; ghi S0-owner-run đã đóng có điều kiện, 17/19 pin hiện khớp và hai pin governance đổi sau các append D-152–D-154; không tuyên bố graph/mypy/dữ liệu đã đạt. | Kiểm tra pin Draft 10; D-152–D-154 |
| §10.1–§10.2, dòng 554–576 (không có phần tương ứng trong Draft 10) | Thêm ghi chú phụ thuộc M3–M6 và thứ tự/ước lượng sơ bộ; nội dung chỉ để lập kế hoạch, không đổi scope, milestone, pin hay authority. | SRS/DTR v2.7 đối chiếu; D-144, D-148, D-151–D-154 |
| Lịch sử bản, dòng 577 (Draft 10 dòng 484) | Thêm bản ghi Draft 10→Draft 11: giữ pin v2.3, thêm đối chiếu v2.5–v2.7, cập nhật S0-owner-run, DB owner-reported và việc còn mở; vẫn chờ review. | Lịch sử soạn Draft 11 |
| Định dạng đầu file, dòng 3–5 | Bỏ ba hard-break trailing spaces kế thừa ở các dòng header; nội dung header được cập nhật như mô tả ở hàng đầu. | Đối chiếu byte Draft 10→Draft 11 |
