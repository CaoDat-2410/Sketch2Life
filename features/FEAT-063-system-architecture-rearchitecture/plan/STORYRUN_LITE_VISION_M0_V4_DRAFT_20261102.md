# M0 V4 — Đề xuất chốt StoryRun-lite Vision cho BE demo

Ngày: 2026-11-02. Trạng thái: **DRAFT / CHỜ OWNER DUYỆT / CHỜ REVIEW ĐỘC LẬP**. Đây là đề xuất quyết định phạm vi, không phải approval triển khai. Việc ghi phương án trong tài liệu không có nghĩa owner đã chấp thuận.

V4 tiếp nhận review độc lập M0 V3 do owner cung cấp: **CHƯA ACCEPTED**, 0 finding P0, 5 finding P1, 4 finding P2. V4 giữ nguyên V2 và V3 để đối chiếu; chưa sửa source, schema, approval hoặc working tree A2.

## 1. Mục tiêu và baseline

Mục tiêu đề xuất là một flow BE demo Parent, chỉ với dữ liệu tổng hợp: tạo một run → nhận ảnh tranh giấy → kiểm tra và ràng buộc nguồn ảnh → gọi Vision đúng một lần → API cho frontend đọc trạng thái/kết quả → người lớn xác nhận chủ thể. Bruno và OpenAPI dùng để kiểm tra/ghép API; phần UI do người khác phụ trách.

Goal gộp S1+S2 chỉ được viết sau khi owner chấp nhận M0 và có kế hoạch cùng approval riêng. Goal đó dùng fake/loopback để chứng minh hợp đồng, persistence, guard và failure handling. Gọi Modal thật là cổng riêng, cần readiness và chỉ thị/approval riêng.

Baseline đọc để soạn:

- M0 V3: SHA-256 **2223310837BD1B42757CE818BF932FF5F98D1AE9EB7FB5552904F3AF9A51FCEE**.
- M0 V2: SHA-256 **06346124F6851DD401148CE25EC2541B29C2738E0D67A77FE3258666F81CB71B**.
- HEAD: **a88de875ff92e9b4d4fa5cc2f5f8d5fc1f626f58**, nhánh **feature/feat063-be-foundation**.
- Working tree có A2 review-fix chưa commit và nhiều thay đổi cục bộ. Future goal nên dùng worktree/snapshot riêng ghim ở HEAD để không nhập nhầm A2 vào baseline; không sửa, dọn hay commit phần A2 từ M0.
- A2 pause report ghi cleanup PostgreSQL bị lỗi FK và database cục bộ có thể còn hàng synthetic. Không dùng lại database đó làm baseline kiểm thử; không tự dọn hoặc suy đoán trạng thái database.
- SRS FEAT-063 v2.3 và DATA_TABLE_REGISTER hiện là draft. Rev37 là catalog baseline cũ; route pilot phải được thống kê riêng, không âm thầm đổi số Rev37.
- Smoke FEAT-061 chứng minh một đường demo Modal cũ với ảnh synthetic; không chứng minh A1 guard/ledger/transport chạy qua Modal thật.

## 2. Quyết định owner được đề xuất

Các giá trị dưới đây là phương án nghiêng về để owner duyệt. Mỗi mục vẫn **CHỜ OWNER**.

| ID | Đề xuất | Lý do và giới hạn |
|---|---|---|
| D1 — Scope demo | Parent synthetic trước; một run, một ảnh, một lần phân tích; trả ứng viên chủ thể và độ không chắc chắn; chỉ có thao tác xác nhận. Không triển khai Teacher auth/assignment thật, story/video, audio, quota hoặc UI. | Giữ đúng mục tiêu “BE chạy được để ghép UI”. Tạm hoãn sửa chủ thể/rerun VLM và ghi deviation rõ so với SRS AT-14; không tuyên bố hoàn tất AT-14. |
| D2 — Identity | Local/test cố định một synthetic actor/profile do server cấu hình. Không nhận X-Actor-Ref hay owner ID do client chọn; chỉ cho phép môi trường local/test và synthetic gate. | Đây là test harness, không phải Parent authentication, BOLA protection hay authorization cho dữ liệu thật. Startup phải fail-closed nếu cấu hình bị dùng ngoài môi trường demo. |
| D3 — API | Dùng tên resource của SRS: /v1/story-runs, /assets, /subject-confirmation; không dùng các tên draft /drawing hoặc /subject-review. OpenAPI versioned cho pilot là deliverable bắt buộc trước bàn giao UI. | Bản OpenAPI phải có DTO mẫu, trạng thái, status code, safe error, polling, idempotency và ví dụ request/response; test contract với route thực. Giữ catalog Rev37 riêng với phần pilot. |
| D4 — Ảnh và binding | Tạo binding/port ảnh riêng có version; không giả checkpoint canvas và không thay đổi RenderBinding, CheckpointBinding, codec hay payload canvas A1. Dùng policy ảnh Story riêng nếu admission FEAT-018 không khớp. | Tránh làm hỏng dữ liệu canvas cũ và bảo đảm receipt gắn với đúng byte được gửi Vision. |
| D5 — Admission và hash | Theo đề xuất SRS §24.2 cho demo: ảnh gốc JPEG/PNG/WebP tối đa 20 MiB và 40 MP; backend kiểm tra/decode có giới hạn, chuẩn hóa orientation/màu thành asset dẫn xuất, giữ nguyên ảnh gốc. Lưu riêng hash ảnh gốc và hash của đúng byte dẫn xuất gửi Vision; version policy nằm trong receipt/provenance. | FEAT-018 hiện có baseline khác; không tuyên bố đã hỗ trợ ảnh điện thoại 12 MP cho tới khi goal chứng minh bằng fixture tổng hợp. Lỗi admission, lỗi xử lý và lỗi provider có mã riêng; không gộp lỗi hệ thống thành RECAPTURE. |
| D6 — Owner scope và asset | Story/asset Parent dùng PARENT_ACCOUNT với ref có kiểu; không tạo organization giả. Bổ sung/ánh xạ owner scope trong metadata Core theo DATA_TABLE_REGISTER; ảnh gốc và ảnh chuẩn hóa là asset riêng, nối bằng core.asset_lineage; không ghi lineage mới vào source_refs. | Dùng adapter lưu byte local/private chỉ trong demo, qua port hiện có nếu phù hợp. Không lựa chọn storage production. Migration chỉ được làm trong goal đã duyệt. |
| D7 — Namespace của ledger A1 | Không dùng owner scope Parent làm organization_id cho ledger. Chỉ dùng ledger namespace synthetic riêng nếu code/schema A1 xác nhận giá trị đó hợp lệ và không tạo organization giả; nếu A1 bắt buộc tổ chức canonical thì dừng, đưa mapping lên owner duyệt. | Giữ ranh giới kỹ thuật của A1 tách khỏi quyền sở hữu Story và asset. |
| D8 — Ghi kết quả và finalize | Mở một Story-specific persistence boundary trước khi ledger chuyển SUCCEEDED: lưu payload hiểu ảnh đầy đủ thành revision bất biến và receipt gắn run_id/attempt_id/result hash; chỉ sau khi revision đọc lại được mới finalize thành công. Nếu Story đã lưu mà ledger chưa terminal, reconcile từ receipt mà không gọi provider lại. | Ledger A1 chỉ có result hash nên không đủ dựng lại payload. Giữ nguyên hành vi canvas mặc định; bất kỳ mở rộng guard/finalize nào phải là thay đổi có allowlist và regression riêng. API không bao giờ trả thành công nếu không đọc được revision kết quả. |
| D9 — Attempt, stale claim và UNKNOWN | Một inference attempt mỗi run trong demo; không có endpoint reanalyze. Cùng idempotency key/fingerprint trả lại cùng run; key trùng nhưng fingerprint khác trả 409. CLAIMED, SENT hoặc UNKNOWN cũ không được sweeper mở attempt mới theo thời gian. Khi cần hold, API trả trạng thái/error versioned với retry_allowed=false; chỉ xử lý tiếp sau khi owner xác nhận worker cũ đã quiesce. Không dùng cooldown 170/190 giây để suy ra GPU đã dừng. | Một process đơn lẻ hoặc timeout không tự tạo fencing. Không tự retry live sau UNKNOWN; lệnh gọi live đầu tiên là one-shot và lần gọi lại cần quyết định riêng, chấp nhận rõ nguy cơ gọi trùng. |
| D10 — AiJobService | Tạm hoãn full AiJobService, outbox và retry đa stage cho demo một bước. Story run/revision giữ trạng thái nghiệp vụ; A1 ledger giữ trạng thái invocation; không tạo projection job thứ hai. Process crash có thể để run ở hold/failed cần owner xử lý, không tự dispatch lại. | Đây là nợ kỹ thuật có ghi nhận, không phải khẳng định đã đạt lifecycle production của SRS §22. |
| D11 — Test DB và baseline | Goal dùng worktree/snapshot riêng ghim HEAD trên, chạy PostgreSQL chỉ trên disposable DB mới, kiểm tra tạo/xóa DB thành công. Không dùng hoặc dọn DB A2/BE1 đang có dữ liệu chưa xác nhận. | Nếu không chứng minh được DB disposable và cleanup, chỉ chạy fake/offline; báo rõ phần chưa kiểm. |

## 3. Hợp đồng API tối thiểu để frontend ghép

V4 đề xuất dùng các thao tác của SRS phù hợp với flow demo:

1. POST /v1/story-runs tạo run Parent tổng hợp; yêu cầu Idempotency-Key, trả 201 và run ref/state/version.
2. POST /v1/upload-sessions, GET /v1/upload-sessions/{upload_id}, PUT /v1/upload-sessions/{upload_id}/parts/{part_no} và POST /v1/upload-sessions/{upload_id}/complete nhận ảnh theo upload-session contract của SRS; không trả storage URL/credential.
3. POST /v1/story-runs/{id}/assets gắn asset đã validate với run cùng owner scope; trả 202 khi bắt đầu xử lý Vision.
4. GET /v1/story-runs/{id} là polling resource duy nhất của demo. Response có state/version/update time; chỉ đưa understanding revision khi payload đã bền vững; không đưa provider URL/token hoặc URL object storage. Response 202 ban đầu cung cấp Location và Retry-After; terminal response có mã lỗi ổn định.
5. POST /v1/story-runs/{id}/subject-confirmation chỉ nhận xác nhận với expected understanding revision; response lặp cùng key idempotent. Correction/rerun không có trong demo.

OpenAPI pilot phải định nghĩa field bắt buộc/tùy chọn, mã lỗi và ví dụ cho ít nhất: input không hợp lệ, ảnh quá cỡ, unsupported media, owner mismatch, idempotency conflict, revision conflict, rate limit, provider failure và provider outcome unknown. Phân biệt lỗi cho phép chụp lại với lỗi hệ thống; khi UNKNOWN, API không hứa cho phép retry. Contract test phải so khớp method/path/schema/status thực tế và giữ báo cáo Rev37 độc lập.

## 4. Ranh giới kết quả A1 và ca phục hồi bắt buộc

Worker/app gọi theo đúng A1 hiện có: transport claim, ghi SENT bền trước ranh giới gửi HTTP, guarded observation xử lý và finalize. Không giao việc claim/finalize cho controller hoặc UI.

Để khắc phục P1 về mất payload, goal sau M0 phải thực hiện và kiểm ít nhất các crash point sau:

- Provider response hợp lệ nhưng Story chưa ghi được: không ghi ledger SUCCEEDED; run được giữ ở trạng thái an toàn, không tự gửi lại.
- Story revision/receipt đã bền vững nhưng ledger chưa terminal: startup/command reconciliation hoàn tất trạng thái từ attempt receipt; không gọi HTTP lần hai.
- Ledger terminal SUCCEEDED: Story revision đầy đủ phải tồn tại và đọc lại được trước khi API báo thành công.
- Hai request đồng thời cùng run: tối đa một provider send. Stale CLAIMED không được cấp attempt khác; SENT/UNKNOWN không được mở lại theo tuổi.
- Lỗi guard, ledger, admission, scope hoặc idempotency trước khi gửi: zero provider send.

Nếu muốn giữ decorator A1 hiện tại thì cần một Story-specific hook/port nằm trước finalize; nếu phải sửa phần shared guard, goal phải nêu file và compatibility test rõ ràng. Không đổi ObservationRequest/canvas binding ngầm, không sửa application/services/vision_analysis.py nếu chưa được ghi trong allowlist/approval mới.

## 5. Cổng sau M0

Review độc lập M0 V4 cần xác nhận từng D1–D11, đặc biệt:

- Cơ chế Story-first/prefinalize thực sự ngăn SUCCEEDED khi thiếu payload, và có thể reconcile crash mà không redispatch.
- One-attempt/hold policy xử lý worker đang pause, stale CLAIMED, SENT, UNKNOWN, concurrent request và cost risk.
- Owner scope Parent, Core Asset và lineage bám DATA_TABLE_REGISTER mà không tạo organization giả; ledger namespace có hợp lệ không.
- API/OpenAPI đủ cho UI, không lệch SRS ngoài deviation được nêu.
- Admission 20 MiB/40 MP/server normalization có khả thi trong repo và receipt gắn đúng byte; policy chưa được coi là đã kiểm chứng.
- Correction-only-confirm, AiJobService defer, local storage và disposable DB là các deviation/nợ chấp nhận được cho demo hay cần thu hẹp thêm.

Sau khi review, owner chọn/đổi các D và ghi approval. Chỉ khi đó mới viết goal S1+S2 với allowlist, acceptance, snapshot/baseline, test matrix fake/loopback và kế hoạch disposable DB. Goal đó dừng ở XONG-CHƯA REVIEW; live Modal là cổng riêng sau review readiness và approval live.

## 6. Không nằm trong M0/goal demo

- Không triển khai UI, Teacher thật, story/storyboard, ASR, video/TTS, billing/quota production, consent dữ liệu thật hoặc multi-stage orchestration.
- Không sửa/đóng A2, B1, B2 canvas; không đọc/dọn database A2 có khả năng còn synthetic rows.
- Không gọi PostgreSQL, Modal/GPU/provider, không chạy test, không stage/commit/push/merge trong quá trình soạn và review M0.
- Không gọi đây là approval triển khai, production design hoặc bằng chứng A1 chạy với Modal thật.
