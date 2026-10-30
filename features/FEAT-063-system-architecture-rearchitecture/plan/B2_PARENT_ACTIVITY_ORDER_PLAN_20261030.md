# B2 — Kế hoạch hòa giải thứ tự hoạt động của Parent (DRAFT)

- Trạng thái: **DRAFT** — kế hoạch làm tài liệu, không phải approval. B2 chỉ lập bảng đối chiếu và trang quyết định; **không sửa SRS, register, ADR, DECISIONS, approval hay code**. Không chạy backend/DB/MinIO/Modal/GPU.
- Ngày: 2026-10-30. Nguồn mục tiêu: dòng B2 trong [backlog](BACKLOG_API_REV37_SRS23_MODAL_20261030.md).
- Mục đích: SRS 2.3 và register đang mâu thuẫn về **thời điểm Parent có hoạt động ngoài trời**. B2 liệt kê hết các đoạn, đưa ra phương án kèm ảnh hưởng, rồi **owner chọn**. Kết quả mở khóa contract StoryRun (B9) và các dòng `blocked_by B2` trong B1.
- **B2 không chặn pilot FEAT-064** (pilot loại Parent/StoryRun khỏi scope: `FEAT-064/plan/PLAN.md:34`).

## 1. Hai phía mâu thuẫn (điểm xuất phát, phải xác minh lại từng dòng)

Số dòng là của `artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` trừ khi ghi khác.

| Nhóm | Đoạn | Nói gì (tóm tắt) |
|---|---|---|
| **POST_VIDEO** (hoạt động hiện sau video) | 76, 130, 215 (BR-08), 216 (BR-09), 222 (BR-15), 273, 388, 390, 455 (FR-P-05), 1041 (AC-05); `DECISIONS.md:104` (D-99); Rev36 plan `:60-61` | Parent không chọn hoạt động trước video; danh sách hoạt động của lesson hiện khi video đã playable |
| **PRE_VIDEO** (Parent chọn/ghim hoạt động trước story) | 81, 339 (chuyển trạng thái đòi "hoạt động đã xác nhận"), 592 (P1 slice), 801 (entity StoryRun "một hoạt động"), 932, 1072 (AC-36), 1319 và 1321 (UC-02: "chọn một hoạt động trong catalog" trước snapshot context), 1323, 1522 (ma trận quyền "Chọn hoạt động Parent"), 1571 (`POST /v1/story-runs` nhận "activity Parent" lúc tạo), 1615 (màn hình "catalog hoạt động"); register `DATA_TABLE_REGISTER.md:369` (`story.runs.activity_ref/version`) | Parent chọn hoạt động từ catalog trước khi tạo story/video |
| **TEACHER_PRE_VIDEO** (đúng, không đổi) | 291, 360, 476 (FR-T-10), 1357, 1359; register `lesson.plan_activities` (352) | Teacher ghim đúng một hoạt động đã duyệt trước video mẫu |
| **CẦN ĐỌC KỸ** (mơ hồ) | 718 (`/v1/activities`), 746, 1206, 1268; `DECISIONS.md:33` (D-29) | Nói "Parent dùng catalog đã duyệt" mà chưa nói thời điểm |

Một điểm liên quan phải kiểm trong B2: BR-08 và AC-05 cho Parent xem danh sách hoạt động của **lesson** sau video, tức là run của Parent cần biết lesson/version nào. Register dòng 369 ghi Parent "không có tham chiếu org/class/lesson". Hai ý này có thể chồng nhau; B2 phải làm rõ, **không kết luận trước**.

## 2. Đầu vào phải ghim (ghi hash vào đầu tài liệu kết quả)

SRS (SHA-256 bắt đầu `7EE8CD8511AF722E`), register (`BE34CF5475550CF3`), `DECISIONS.md`, `docs/adr/ADR-0021*` và `ADR-0022*`, Rev36 plan, B1 crosswalk (`evidence/B1_API_CROSSWALK_20261030.csv`), FEAT-064 plan (chỉ để xác nhận B2 không chặn pilot). Ghi hash đầy đủ khi chạy.

## 3. Nguyên tắc

1. **Không chọn phía.** Phương án chỉ là đề xuất; owner quyết. Không tự xóa hay sửa đoạn mâu thuẫn.
2. **Mỗi đoạn một phân loại** (§1: POST_VIDEO / PRE_VIDEO / TEACHER_PRE_VIDEO / NEUTRAL) kèm số dòng và trích ngắn; đoạn mơ hồ ghi `AMBIGUOUS` + câu hỏi.
3. **Không sửa file nguồn.** B1 đang được bảo vệ bởi approval của nó ("không đổi nếu chưa có mục mới"), nên kết quả cập nhật B1 là một **phụ lục riêng**, không sửa CSV/Markdown B1.
4. **Không tự suy luận quyết định của owner.** Nếu D-99 và UC-02 mâu thuẫn, ghi cả hai nguồn và ngày; đừng tự coi D-99 là đúng.
5. **Không nâng bản nháp thành chuẩn.** SRS/register vẫn là draft chưa ký.

## 4. Các bước

| Bước | Việc | Đầu ra | Xong khi |
|---|---|---|---|
| S0 | Preflight: đọc `AGENTS.md`; `git status`/`git log -3`; ghi hash đầu vào; xác nhận file local-only của owner không bị đổi | Khối preflight | Hash khớp bản ghi |
| S1 | Kiểm kê toàn bộ đoạn nhắc hoạt động của Parent/Teacher trong SRS, register, DECISIONS, ADR-0021/0022, bảng truy vết, AC/AT/OI/Q-trace, phần màn hình và API | Bảng kiểm kê: nguồn, dòng, phân loại, trích ngắn | Mọi đoạn có phân loại; số đoạn mỗi nhóm được đếm; danh sách điểm xuất phát §1 đã được đối chiếu (thêm/bớt ghi rõ) |
| S2 | Lần lại lịch sử quyết định: D-99, Rev25 (nếu ghi nhận trong `approvals/TASK_APPROVAL.md`), D-29, Q-trace; xác định đoạn PRE_VIDEO có từ phiên bản SRS nào | Dòng thời gian ngắn | Ghi rõ đoạn PRE_VIDEO là tàn dư từ v2.2 hay quyết định mới |
| S3 | Soạn trang quyết định với 3 phương án: **A** Parent không chọn trước video (`activity_ref` rỗng lúc tạo, danh sách lấy từ lesson sau `VIDEO_READY`); **B** giữ Parent chọn trước video (đổi BR-08/09/15, FR-P-05, AC-05, D-99); **C** lai (chọn tùy chọn trước video làm gợi ý, danh sách vẫn hiện sau video). Mỗi phương án nêu: đoạn phải đổi, ảnh hưởng tới `POST /v1/story-runs`, `story.runs` (cột `activity_ref`, tham chiếu lesson của Parent), state machine (dòng 339), UC-02/AC-36/AC-05, màn hình, pipeline stage 4 | Trang quyết định | Mỗi phương án có danh sách đoạn phải đổi và rủi ro |
| S4 | Đề xuất và nêu lý do (đề xuất ban đầu: A vì khớp D-99, BR-08/09/15, FR-P-05 và nhiều nhất các đoạn) nhưng đánh dấu rõ là đề xuất | Mục "Đề xuất" | Nêu cả lý do ngược lại |
| S5 | Phụ lục B1: với 16 dòng `blocked_by` chứa `B2` (T018–T031, T046, T047), nêu dòng nào được gỡ chặn bởi từng phương án và dòng nào vẫn bị chặn vì lý do khác (ví dụ trạng thái StoryRun, B3) | Bảng phụ lục | 16 dòng đều có kết luận theo từng phương án; không sửa B1 |
| S6 | Danh sách câu hỏi cho owner (tối đa 8, mỗi câu có mặc định đề xuất) | Mục câu hỏi | Mỗi câu có đủ ngữ cảnh để trả lời ngắn |
| S7 | Tự kiểm: xem §6 | Bảng kiểm | Mọi kiểm tra đạt hoặc ghi lệch có lý do |
| S8 | Chạy `validate_harness`, `validate_repository_security`, `validate_architecture`, `git diff --check`; báo kết quả thật | Báo cáo cuối | Cả bốn exit 0, hoặc ghi blocker |

## 5. Sản phẩm

- `evidence/B2_PARENT_ACTIVITY_ORDER_CROSSWALK_20261030.md`: khối giới hạn, hash đầu vào, kiểm kê (S1), dòng thời gian (S2), trang quyết định + đề xuất (S3–S4), phụ lục B1 (S5), câu hỏi owner (S6), bảng tự kiểm (S7).
- Tùy chọn: `evidence/B2_PARENT_ACTIVITY_ORDER_INVENTORY_20261030.csv` (bảng kiểm kê đầy đủ, UTF-8).
- Sau khi owner chọn phương án: **một bản ghi quyết định** (tài liệu riêng) và, nếu owner muốn SRS/register nhất quán, một **kế hoạch sửa tài liệu riêng cần approval riêng** (giống các lần sửa SRS trước). Không nằm trong B2.

## 6. Kiểm tra bắt buộc (S7)

1. Mọi đoạn trong §1 có mặt trong kiểm kê với dòng xác minh được (mở lại file, không chép).
2. Không đoạn nào có phân loại trống; đoạn `AMBIGUOUS` có câu hỏi.
3. Mỗi phương án liệt kê đủ nhóm ảnh hưởng: API, schema, state, UI, AC, pipeline, B1.
4. 16 dòng B1 đều có kết luận theo từng phương án.
5. Không file nguồn nào bị sửa (kiểm bằng `git status` và hash).
6. Không đường dẫn tuyệt đối local, token, dữ liệu trẻ.

## 7. Ranh giới

- Không sửa: SRS, register, ADR, `DECISIONS.md`, `approvals/TASK_APPROVAL.md`, B0/B1 và các plan hiện có, code, 8 file local owner giữ.
- Không chạy dịch vụ/test; không dùng token; không chọn phương án thay owner.
- **Commit:** theo quy tắc của owner, **một commit duy nhất khi cả task xong**, và chỉ khi owner yêu cầu. Không commit hay push theo từng bước.

## 8. Giả định (owner có thể đổi)

| Giả định | Lý do |
|---|---|
| B2 là tài liệu thuần túy, tự nó không cần approval triển khai, nhưng có thể ghi một mục approval documentation-only như B1 | Theo nếp B1 |
| Kết quả cập nhật B1 để ở phụ lục, không sửa B1 | Approval của B1 cấm đổi file kết quả nếu chưa có mục mới |
| Phương án A là điểm xuất phát | Khớp quyết định D-99 và đa số đoạn POST_VIDEO |

## 9. Việc owner sau khi B2 xong

1. Chọn phương án A, B hoặc C (hoặc phương án khác).
2. Quyết định có lập kế hoạch sửa SRS/register hay không.
3. Cho phép cập nhật B1 (mục approval mới) để gỡ `B2` khỏi các dòng đã được giải quyết.
