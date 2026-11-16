# EV-063-60 — Đánh giá độc lập hai agent về mức sẵn sàng của 11 sơ đồ

- **Evidence ID:** EV-063-60
- **Ngày:** 2026-11-07
- **Loại:** Đánh giá tài liệu / rà soát chéo độc lập
- **Trạng thái:** Hoàn tất; chưa tạo sơ đồ, chưa sign-off SRS
- **Nhánh ghi nhận:** docs/feat063-diagram-readiness-20261107

## Phạm vi và nguồn chuẩn

Hai agent được giao đánh giá độc lập cùng một baseline, với hai trọng tâm khác nhau: hành vi/luồng và kiến trúc/dữ liệu. Baseline sản phẩm là FEAT-063 SRS v2.7-draft tại commit 98cc34a39af279560b5f8d39f18939a376535834 trên nhánh docs/feat063-srs-v26-checklist-20261107, cùng Data Table Register v2.7-draft.

Áp dụng quy tắc nguồn trong docs/context/SRS_AUTHORITY.md: §§1–31 là yêu cầu đích; §32 là bằng chứng source/as-built theo thời điểm và môi trường, không thay thế yêu cầu đích. Rev54 diagram crosswalk/catalog được dùng làm tài liệu hỗ trợ, không làm nguồn yêu cầu thay SRS.

Các sơ đồ được đánh giá: Context, Use Case, Workflow, Activity, Sequence, Screen Flow, Class, ERD conceptual/logical/physical, State Machine, System Architecture và Package.

## Kết luận chung

Hai đánh giá độc lập thống nhất rằng SRS đủ để dựng bản nháp có đánh dấu các điểm mở cho phần lớn sơ đồ. Chưa đủ cơ sở để chốt bộ sơ đồ như baseline chính thức. Screen Flow chưa có bản đồ điều hướng; ERD physical chưa có DDL/schema đích được duyệt. Các sơ đồ khác cần giữ rõ ranh giới target, phần đề xuất và quyết định còn mở.

| Sơ đồ | Mức sẵn sàng | Căn cứ và điều kiện chính |
|---|---|---|
| 1. Context Diagram | Đủ có điều kiện để soạn nháp | §§2.3, 3, 9.1 mô tả actor, ranh giới và hệ thống liên quan. Phải đánh dấu production host/region và một số provider chưa chọn; không biến hướng phát triển thành deployment đã chốt. |
| 2. Use Case Diagram | Đủ có điều kiện | §§3, 19–20, 30.1 có actor, ma trận quyền và UC-01–17. Cần để mở chính sách chọn trẻ mẫu Teacher; “Quản trị nội dung” là permission của Platform Admin theo §31.13, không phải principal riêng. |
| 3. Workflow Diagram | Đủ có điều kiện | §§5–6, 19, 22–23 mô tả luồng Parent, Teacher, billing, review, retry và xóa. Chưa chốt activity cho Parent không có lesson preset (§31.10 #13), chọn trẻ mẫu (#4) và xử lý plan bị supersede sau khi đã pin (#15). |
| 4. Activity Diagram | Đủ có điều kiện | §§6.1–6.1.1, 19, 21.6, 22.2–22.3 nêu guard, lỗi, retry, timeout và closeout. Cần chốt các nhánh đang mở và cách xử lý song song/compensation trước khi xem là workflow chính thức. |
| 5. Sequence Diagram | Đủ có điều kiện ở mức contract | §§9.5–9.6, 21.7, 22.1–22.5 mô tả versioned contract, job dispatch/completion và saga admission. Route hiện là nhóm đề xuất; OI-04, provider callback, timeout và lựa chọn orchestration còn mở. |
| 6. Screen Flow Diagram | Chưa đủ cho flow chính thức | §21.5 là danh mục màn/surface theo role; §21.6 mô tả phục hồi lỗi. Chưa có liên kết screen-to-screen, navigation, back/cancel/resume và đầy đủ loading/empty/denied/error. OI-17 yêu cầu wireframe/interaction sign-off. |
| 7. Class Diagram | Đủ có điều kiện cho domain model | §§9.9, 11 và Data Table Register §§5–7 cho aggregate/entity, field logic và quan hệ. Chưa đủ cho class code-level: method/signature, kiểu/nullability chuẩn và package boundary chưa được khóa; role resolver còn mở (§31.10 #14). |
| 8a. ERD conceptual | Đủ để soạn nháp | §§11–12 và Data Table Register §§2, 6 mô tả owner, aggregate và quan hệ. Phải tách active target khỏi legacy/read-only và thể hiện cross-owner refs theo contract, không tự nối FK xuyên owner. |
| 8b. ERD logical | Đủ có điều kiện | Data Table Register §§5–7 có tên bảng, field logic, PK/FK, uniqueness và invariants. Cần xác nhận cardinality/optionality còn thiếu, role/identity persistence và một số grant/audit relationships trước khi chốt. |
| 8c. ERD physical | Chưa đủ | Field list hiện là thiết kế logic, không phải DDL. Còn thiếu kiểu SQL/nullability đầy đủ, constraint/index cụ thể, DDL đã duyệt, schema inventory và migration/reconciliation thực tế (OI-11; Register §§12, 14.3). |
| 9. State Machine Diagram | Đủ có điều kiện | §6.1.1 mô tả StoryRun, VideoGeneration, LessonOccurrence, SketchDeckRevision, AiJob, Subscription và PaymentAttempt. StoryRun là phần rõ nhất; chưa đủ state/transition cho toàn bộ profile sharing, upload, publication/access grant và lifecycle. Plan supersession còn mở (§31.10 #15). |
| 10. System Architecture Diagram | Đủ có điều kiện cho kiến trúc logic | §§2.3, 9, 11, 22, 24–27 mô tả modular monolith, owner module, contracts, Compose local và provider boundary. Production topology, host/region, orchestration và recovery còn mở (OI-04, OI-08). |
| 11. Package Diagram | Đủ có điều kiện | §§9.1–9.2 định nghĩa Clean Architecture và package tree đề xuất; §9.5 nêu contract boundaries. Cây package chưa thể hiện rõ learning_content, ai_jobs và ai_policy như các owner/module trong §§11–12; chưa có dependency matrix được duyệt. |

## Mâu thuẫn và điểm mở đã đối chiếu trực tiếp

1. **Chọn trẻ đại diện cho video Teacher:** UC-05 trigger, actor/permission và screen catalog mô tả Teacher chọn trẻ; §5.2, FR-PL-20 và AC-56 mô tả hệ thống chọn ngẫu nhiên trẻ đủ điều kiện. Đây là mâu thuẫn ảnh hưởng Use Case, Workflow, Activity, Sequence và Screen Flow. Eligibility, consent/thông báo và loại trừ còn mở tại §31.10 #4.
2. **Quản trị nội dung:** một số surface đặt tên “Quản trị nội dung”; §31.13 xác định đây là permission của Platform Admin. Sơ đồ phải thể hiện đúng một principal với permission tương ứng.
3. **Parent activity timing:** §5.1 và §6.2.2 thống nhất Parent không chọn activity trước video; §6.2.2 chỉ cho Teacher thêm một activity đã duyệt vào story input. Đây là phân biệt theo role, không phải mâu thuẫn. Việc Parent không dùng preset có query catalog hay không vẫn OPEN tại §31.10 #13.
4. **Plan/lesson bị thay thế sau khi pin:** tác động lên occurrence, run, job, deck, sample claim và quyền chiếu còn OPEN tại §31.10 #15.
5. **Role/invitation/audit:** persistence và resolver của permission, người nhận có quyền chấp nhận invitation gửi cho cả school, force-close, và field mapping của audit vẫn mở tại §31.10 #8, #14, #17.
6. **Số lượng bảng:** SRS §12.1 ghi 86 mapping nguồn; §12.2 giải thích target hiện hành là 38 retained/refactored + 54 new = 92 active, cộng 48 legacy = 140 projected. Data Table Register phân biệt 89 source-declared sau Rev31 với 89 active/137 physical của baseline lịch sử v2.3. Phép tính được giải thích, nhưng cùng số 89 được dùng cho hai baseline khác nhau; trên sơ đồ cần ghi nhãn mốc rõ, không ghi “89 tables” đơn lẻ.

## Cổng trước khi chốt sơ đồ

- Chủ sở hữu duyệt cả SRS và Data Table Register; cả hai hiện là v2.7-draft chưa sign-off. Front matter SRS yêu cầu duyệt hai Markdown trước khi tạo diagram conceptual/logical cuối và PDF.
- Chốt các câu hỏi có ảnh hưởng trực tiếp: chọn trẻ Teacher; catalog Parent không preset; plan supersession; resolver/invitation; age migration; audit mapping.
- Screen Flow cần screen IDs và chuyển tiếp được duyệt.
- ERD physical cần DDL đích, inventory môi trường đích và migration/reconciliation được xác minh.
- Sơ đồ architecture/package triển khai cần ADR cho topology production/orchestration nếu được mô tả như production, không chỉ target logic hoặc local Compose.

## Giới hạn đánh giá

Đây là review tài liệu bằng hai agent độc lập và một lượt đối chiếu trực tiếp nguồn. Không chỉnh SRS/Data Table Register, không tạo diagram, không chạy product tests/build, API/runtime, database/migration hoặc provider. §32 không được dùng để sửa nghĩa của target requirements §§1–31.
