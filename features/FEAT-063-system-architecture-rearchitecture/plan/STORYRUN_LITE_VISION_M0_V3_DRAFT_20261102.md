# M0 V3 nháp — BE Vision demo cho Parent/Teacher

Ngày: 2026-11-02. Trạng thái: **DRAFT / CHƯA REVIEW / CHƯA APPROVAL TRIỂN KHAI**. Bản ghi điều phối tiếp nhận từ M0 V2 và báo cáo review vòng hai do owner cung cấp; không sửa V1/V2. SRS FEAT-063 là v2.3-draft. Mọi cơ chế, schema, đường dẫn API và quyết định kỹ thuật bên dưới là đề xuất, chưa được chấp nhận chỉ vì được ghi ở đây.

## 1. Mục tiêu và ranh giới

Ưu tiên một flow BE demo để frontend ghép: ảnh tranh synthetic → API BE nhận và kiểm tra ảnh → Vision trên Modal → API trả trạng thái và kết quả. Bruno dùng thử chính API đó. Identity giả lập chỉ local/test, có gate synthetic; UI do người khác triển khai. Parent trước; Teacher và quyền/assignment thật là bước tiếp theo sau demo.

Một goal gộp S1+S2 dự kiến thực hiện API, persistence/contract, fake và loopback cùng nối guard/ledger/transport phù hợp; dừng `XONG-CHƯA REVIEW`. Lần gọi Modal thật là hoạt động riêng sau review, readiness và chỉ thị/approval live tương ứng. Chưa bao gồm story/storyboard/video, production, dữ liệu trẻ thật hay legal consent.

## 2. Nguồn và trạng thái

- V2: `.claude/handoff/STORYRUN_LITE_VISION_DECISIONS_V2_DRAFT_20261102.md`, SHA-256 `06346124F6851DD401148CE25EC2541B29C2738E0D67A77FE3258666F81CB71B`. Đối chiếu lại nếu file thay đổi. V2 chỉ là nháp; trạng thái review vòng hai theo báo cáo owner cung cấp là **ĐỒNG Ý CÓ SỬA**, không phải acceptance.
- SRS/register: `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` và `DATA_TABLE_REGISTER.md`; bản nháp còn các quyết định mở. Bám ý nghĩa và ràng buộc, không mặc định đặt cùng tên bảng là đã tuân SRS.
- A1 được ghi COMPLETE sau review; A2 đang tạm dừng, review-fix chưa accepted, B1/B2 canvas tạm gác. Báo cáo pause: `features/FEAT-064-current-flow-modal-vision-dev/evidence/A2_REVIEW_FIX_PAUSE_REPORT_GA2_20261102.md`. Snapshot local: `.claude/handoff/snapshots/GA2_REVIEWFIX_PAUSE_20261102T121026/` và `.claude/handoff/snapshots/CLAUDE_A2_PAUSE_20261102T121212/`.
- PostgreSQL A2 có thể còn dữ liệu synthetic do cleanup rollback; chưa có bằng chứng sạch. Kiểm đúng database/nguồn/ownership và xử lý riêng đúng phạm vi trước khi dùng lại; không xóa theo suy đoán.
- FEAT-061 smoke 29/10 là bằng chứng một luồng demo cũ qua Modal. Ghi chép 01/11 chỉ là tự thuật, thiếu log thô; không coi là bằng chứng độc lập. Chưa có bằng chứng A1 guard/transport/ledger chạy với Modal thật.

## 3. Sửa dữ kiện V2: ranh giới A1

Đã đọc `backend/src/sketch2life/infrastructure/vision_analysis/transport.py` và `invocation_guard.py`: transport `post_json` gọi `guard.claim()`, rồi `guard.mark_sent()` trước khi gửi HTTP; decorator gọi `finalize()` trong `observe()` trước khi trả outcome cho worker. Worker không tự gọi lại các bước này. Ledger giữ hash kết quả, không phải toàn bộ response.

Vì vậy trình tự V2 “worker tự claim/mark_sent → ghi Story → hoàn tất ledger” không khớp code A1. Crash có thể xảy ra sau khi ledger terminal nhưng trước khi Story lưu response. Một `SUCCEEDED` trong ledger không đủ để tái tạo payload bị mất; không được tuyên bố Story đã lưu kết quả. Cần review giải pháp reconciliation, mô tả rõ dữ kiện còn lại và trạng thái hiển thị, không tự gọi lại provider.

Ràng buộc `UNIQUE(run_id)` và `UNIQUE(job_id, attempt_id)` chỉ chặn trùng theo các khóa đó; các attempt khác nhau của cùng StoryRun cần kiểm soát đồng thời và idempotency riêng ở tầng Story. Không suy ra ledger ngăn mọi lần gọi lặp. `CLAIMED` không chứng minh một worker khác đã dừng; không đánh dấu NOT_SENT/chạy lại chỉ từ thời gian hoặc thiếu heartbeat nếu chưa có cơ chế fence được chứng minh.

Ledger CAS trước là một phương án để phân xử, **chưa kết luận là đủ**. Thiết kế phải kiểm cả crash giữa hai transaction, lỗi DB, worker còn sống, sweeper cạnh tranh, cancel, response đến muộn, result đã mất và duplicate idempotency key; chỉ công bố outcome được chứng minh. Không dùng một ngưỡng 170/190 giây làm bằng chứng GPU đã dừng hoặc cho phép tự retry. Không tự gửi lại khi UNKNOWN; hành động tiếp theo và mức chi phí/lượt gọi do owner quyết định.

`HttpJsonTransport` chỉ có POST; `/health` nếu chạy là kiểm tra riêng và không chứng minh model đã sẵn sàng, token đúng, hay A1 hoạt động. V4 D9 là chiến lược của pilot canvas cũ, không mặc định áp dụng nguyên cho goal mới. Bất kỳ chính sách live mới cần được ghi rõ và duyệt riêng.

## 4. Hợp đồng demo đề xuất, chưa khóa

- Hướng API: tạo run một trẻ synthetic; upload ảnh; đọc trạng thái và kết quả; xác nhận hoặc sửa chủ thể; hủy. Nếu có thao tác phân tích lại phải là command có idempotency, version, giới hạn, quy tắc UNKNOWN và authorization cụ thể. Tên route/số operation chỉ là đề xuất; kiểm catalog ở cả gate bật và tắt thay vì giả định không ảnh hưởng test.
- Giữ ảnh gốc và provenance khi cần, xác minh byte/hash của ảnh thực sự gửi VLM và receipt admission gắn đúng ảnh. Phân biệt RECAPTURE, lỗi xử lý và lỗi provider. Server hoặc client chuẩn hóa ảnh là quyết định mở; không khai `EXPO_*` khi client không thực hiện đúng policy. Test bằng ảnh synthetic nhỏ và các trường hợp kích thước/định dạng trước khi chốt.
- `CheckpointBinding`/`RenderBinding` gắn canvas; không đưa hash ảnh vào trường checkpoint sai ý nghĩa. So sánh kiểu ảnh riêng với Protocol/Union hoặc lựa chọn khác; kiểm codec, call sites, mypy, regression A1 và versioned contracts. Nhãn `photo-*` không tự chứng minh provenance; không chấp nhận đường tắt chỉ vì bridge chưa dùng field đó.
- Storage: kiểm `CoreAssetMetadataModel`, `LocalArtifactStore`, tenant scope, receipt/admission, cleanup và restart. Chưa duyệt storage, migration, bốn bảng `story.*` hay bảng receipt mới. Nếu dùng giải pháp tạm phải ghi sai lệch register và đường hoàn thiện. Idempotency không được coi là đã có chỉ vì API nhận header; phải lưu/kiểm fingerprint và replay theo contract được review.
- Xác thực stand-in local/test chỉ cho synthetic, không suy ra Teacher/Parent thật. Kiểm người dùng chéo run/ảnh và gate cấu hình. Không để token hoặc URL provider vào response/log/client.

## 5. Sửa chủ thể và chứng cứ Modal

SRS AT-14 mô tả sửa chủ thể tạo revision/VLM job mới trên cùng image hash. Review vòng hai báo server V2 đã hỗ trợ `narration_context` và adapter có `understand_with_narration`, còn bridge hiện tại chỉ `IMAGE_ONLY`. Điều này là khả năng cần kiểm contract, policy và regression; **chưa chứng minh** chỉ sửa bridge là đủ cho luồng mới hoặc đảm bảo AI tuân theo lời sửa.

Lựa chọn còn mở: (S) thêm đường chạy lại AI theo contract được duyệt; (A) lưu correction của người lớn không gọi AI, ghi rõ lệch AT-14 trong demo. Có thể tách thao tác “xác nhận” khỏi phần “sửa” nếu owner chọn scope demo tối thiểu; không tự tuyên bố đầy đủ SRS.

## 6. Các quyết định cần chốt trước goal

1. Binding ảnh và cách mở rộng contract mà không làm giả checkpoint; xác định exact paths và hồi quy A1.
2. Storage/receipt/migration và có dùng `AiJobService` ở demo hay ghi nợ kỹ thuật, cùng ngữ nghĩa restart/cancel/idempotency.
3. Client hay server chuẩn hóa; giới hạn ảnh synthetic và provenance/hash, theo evidence admission.
4. Scope subject-review (chỉ xác nhận / correction thủ công / chạy lại VLM), ghi rõ tương ứng với SRS và chi phí.
5. Chính sách UNKNOWN, concurrency, recovery và hạn mức live; không suy đoán cooldown bảo đảm provider dừng.
6. Cách dùng baseline A2, giữ snapshot, xử lý DB test và tích hợp dev; ghim HEAD theo thực tế trước launch.

Đây là danh sách cần reviewer đề xuất phương án và owner chốt những lựa chọn ảnh hưởng sản phẩm/phạm vi. Không tự coi bản nháp cấp quyền sửa A1, schema hay gọi Modal.

## 7. Tiêu chí review/đầu ra

- Reviewer độc lập kiểm từng đề xuất ở mục 3–6 và đối chiếu code hiện tại; nêu finding, file/dòng, bằng chứng và phần chưa kiểm. Không dùng kết quả fake làm bằng chứng live.
- Goal gộp chỉ viết sau review M0 và quyết định owner; có danh sách file chính xác, plan, approval, baseline, test fake/loopback/DB, contract cho frontend, điều kiện dừng và evidence.
- Mốc live riêng phải có API chạy qua BE, ảnh synthetic, kiểm trạng thái/response/ledger, số lần gọi thực và xử lý UNKNOWN; không khẳng định thành công nếu chưa có kết quả.
- Không stage/commit/push/merge, không gọi Modal/provider, không chạy PG hay thay đổi A2 trong công việc soạn nháp này.
