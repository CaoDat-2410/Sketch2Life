# EV-063-12 — Rà soát toàn bộ mô hình bảng và quan hệ

## Phạm vi

Rà soát chỉ đọc danh mục persistence trong repository, SRS, Data Table Register, proposed ADR-0021 và hồ sơ FEAT-063 theo Plan revision 19. Chủ sở hữu yêu cầu giảm entity không cần thiết, xác định nguồn dữ liệu chuẩn và nối rõ quan hệ. Đây là cập nhật tài liệu; không sửa product code/schema/migration và không truy cập database đang chạy.

## Kết quả kiểm kê

| Hạng mục | Số lượng | Cách tính/đối chiếu |
|---|---:|---|
| Production mappings được khai báo | 86 | 86 dòng nguồn đánh số trong DATA_TABLE_REGISTER §3; đây không phải kết quả introspection database |
| Fixture chỉ phục vụ kiểm thử | 5 | Loại khỏi bảng production và phép đếm đích |
| Mapping hiện có giữ/tái cấu trúc | 51 | Core 5 + BE1 8 + AI Jobs 7 + AI Policy 25 + Learning Content 6 |
| Bảng mới còn cần trong target | 40 | Core 3 + AI Jobs 1 + Parent 5 + BE1 3 + Lesson 7 + Story 9 + Billing 9 + Notifications 3 |
| Active target | 91 | 51 + 40 |
| Legacy giữ read-only | 35 | Giữ bảng/row và quan hệ lịch sử tại chỗ; không thuộc ERD target |
| Physical target dự kiến | 126 | 91 active + 35 legacy; chưa xác nhận schema database thật |

Kiểm tra tĩnh trên Markdown: từ điển có 40 tên bảng duy nhất; relationship catalogue §6.1 có đúng 40 tên duy nhất và tập tên khớp hoàn toàn với từ điển; source inventory có 86 dòng đánh số. Phép đếm hiện hành thay thế D-81 (44 bảng mới/95 active/130 physical), không thay đổi bất kỳ bảng thật nào.

## Bốn entity proposal đã gỡ khỏi target

| Entity proposal bị bỏ | Thay thế bằng nguồn chuẩn | Lý do |
|---|---|---|
| `ai_jobs.job_subject_refs` | `story.runs` giữ đúng một scalar profile ref; AI Job giữ một target StoryRun | Tránh lưu lặp quan hệ trẻ/job và tránh khả năng subject list lệch StoryRun |
| `ai_jobs.job_result_assets` | Story/Lesson aggregate sở hữu asset đầu ra; `ai_jobs.completion_receipt` ghi disposition/hash/idempotency | Tránh bảng trung gian chung không có lifecycle ownership; asset hash/type/size đã thuộc Core Asset |
| `story.profile_context_snapshots` | `story.run_inputs` bất biến | Snapshot bounded, versioned, allowlisted và có hash gắn cùng revision input, không cần entity riêng |
| `story.profile_context_snapshot_items` | JSON snapshot có giới hạn bên trong `story.run_inputs` | Không cần từng item thành bảng riêng vì không có vòng đời/cập nhật/query độc lập; JSON không được dùng làm hồ sơ hay lịch sử vô hạn |

Đây là bốn bảng được đề xuất trong target trước đó, không phải bốn bảng đang tồn tại trong database để xóa. Sáu entity nghiệp vụ cần riêng vẫn được giữ: `billing.video_quota_usage`, `notifications.push_endpoints`, `core.upload_sessions`, `core.upload_parts`, `lesson.sketch_deck_revisions`, `lesson.sketch_deck_steps`.

## Nguồn dữ liệu chuẩn và chống lưu lặp

- Profile root giữ identity/lifecycle/current-revision pointer; profile revision là nguồn chuẩn cho tuổi, nhóm tuổi, tên hiển thị và sở thích.
- Context entry ghi trải nghiệm/thành tích/quan sát ngoài app do người lớn nhập; lịch sử app lấy từ Story, không nhập lại thành context.
- Nhu cầu hỗ trợ tách bảng để giới hạn quyền và mã hóa; mặc định không đưa vào AI context. Parent và Teacher giữ owner/schema riêng, không dùng một bảng polymorphic làm lối tắt xuyên quyền.
- `story.run_inputs` ghim asset gốc, ý tưởng/transcript, profile revision và snapshot context được duyệt. Run/job không có bản snapshot lặp.
- Core Asset là nguồn chuẩn duy nhất cho media hash/type/size/version/state; Core `asset_lineage` là nơi ghi cạnh nguồn-phái sinh mới. Lesson/Story lưu asset ref/version.
- Story/Lesson aggregate lưu output refs của chính mình. AI Job giữ target, trạng thái/attempt và completion receipt; không sở hữu asset list.
- Billing sở hữu price/invoice/payment/subscription/capacity/quota grant/usage; không tạo mutable balance và không ghi product quota trong AI Policy.
- Lesson `sketch_deck_steps` nối với deck revision và activity. Không lặp `plan_revision_id` trên từng step; Lesson transaction xác minh activity nằm trong plan đã pin.
- `billing.provider_event_receipts` cho phép receipt chưa xác minh/chưa resolve target tồn tại với 0 FK; khi callback được xác minh/xử lý phải có đúng một FK tới payment attempt hoặc subscription.

## Quan hệ xuyên module

Quan hệ trong owner được thể hiện bằng FK/unique/check. Quan hệ qua owner dùng typed opaque ref, versioned port/contract, authorization và idempotency receipt; không tạo FK chéo module. Data Register §6.1 liệt kê từng bảng mới và §6.2 mô tả chuỗi 51 bảng hiện có được giữ. §6.4 tóm tắt các đường đi Parent → run → media, Teacher → roster/lesson → sample run, Sketch plan → deck/assets, Billing → quota, AI Policy → provider-copy lifecycle và event → inbox/delivery.

Các aggregate gốc như principal/profile, organization, occurrence, StoryRun, policy version, catalog record, invoice và inbox là đầu mút gốc có chủ ý, không phải bảng mồ côi. Parent/Teacher không nối trực tiếp profile vì đó là hai vùng quyền sở hữu tách biệt. Ba mươi lăm legacy tables vẫn có quan hệ lịch sử nội bộ nhưng không có reference mới từ luồng target.

AI Policy còn 25 bảng nguồn active: nhóm policy/version/review/event/receipt/outbox, activation scope/transition, resource budget/reservation/event/receipt và provider-copy scope/registration/evidence/operation/authority/delivery/history/lifecycle/resolution. Mỗi nhánh lưu trạng thái hoặc bằng chứng có vòng đời/authority riêng; quota video không nằm trong nhóm này. Rà soát giữ các bảng này vì hợp nhất sẽ làm mất lịch sử/phân quyền/reconciliation riêng; độ phức tạp còn phải được đo trong implementation planning.

## Kiểm tra và giới hạn

- Đối chiếu source inventory, 51 retained source maps, 40 dictionary entries, 40 relationship entries, canonical-field rules, traceability và số lượng ở SRS/register/ADR/plan/context/decisions/status/approval.
- Chỉ chạy kiểm tra văn bản/count, không chạy product tests/builds, linter, benchmark hoặc test database.
- Không có live DB inspection, migration, schema introspection, provider/Modal/payment call, deployment hoặc dữ liệu trẻ thật.
- 91/126 là target logic dựa trên source declarations; phải đối soát migration và database thật trong một nhiệm vụ đã được duyệt riêng.

## Trạng thái

SRS và Data Table Register vẫn là bản nháp chờ chủ sở hữu xem xét. Chưa tạo diagram cuối hoặc PDF; tiếp tục chỉ sau khi chủ sở hữu duyệt rõ cả hai Markdown baseline.
