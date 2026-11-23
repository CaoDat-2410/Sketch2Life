# Parent E2E trên Android emulator — 2026-11-20

## Kết luận

**PARTIAL / BLOCKED tại bước gợi ý hoạt động; chưa phải E2E hoàn chỉnh.** Đã chạy app Expo thật trên `emulator-5554`, xác thực Firebase thật với tài khoản Parent synthetic vừa đăng ký, backend local, PostgreSQL/MinIO/ClamAV của stack FEAT-081 và Modal workers thật. Không dùng preview harness, fixture, mock, hoặc dữ liệu trẻ thật.

Seed mới từ `dev` không cung cấp Firebase login. Seed package tạo principal/content trong PostgreSQL cho chế độ development, bị guard khi auth Firebase và AI Modal đang bật. Không chạy seed và không bỏ qua guard. Đăng ký một tài khoản Parent synthetic mới qua Android UI; thông tin đăng nhập không được ghi vào evidence.

## Kết quả theo bước và API

| Bước | API / workload | Kết quả | Bằng chứng |
|---|---|---|---|
| Đăng ký và xác thực | `POST /api/auth/v1/registrations`; `GET /api/auth/v1/me` | **PASS** — đăng ký synthetic mới `201`, hồ sơ auth `200`. Một lần thử email synthetic cũ nhận `409` do đã tồn tại; không retry email đó. | Backend access log |
| Tạo hồ sơ Parent | `POST /v1/parent/profiles` | **PASS** — synthetic profile 60 tháng được tạo qua UI. UI hiện “Nhóm tuổi chưa khả dụng” dù profile tạo thành công; cần xem lại mapping nhãn tuổi. | Backend access log; profile UI trước đó |
| Gợi ý chủ đề | `GET /api/parent/v1/topics/suggestions` | **PASS** — API trả `200`, UI đưa ra lựa chọn chủ đề. | Backend access log |
| Gợi ý đối tượng theo chủ đề | `GET /api/parent/v1/topics/animals/drawing-subject-suggestions` | **PASS** — API trả `200`; chọn “Rùa con”. | Backend access log |
| Hướng dẫn SVG | Không gọi | **SKIP — tùy chọn**; phụ huynh bỏ qua guide và tiếp tục chụp tranh. | Không phát sinh request |
| Tạo buổi và tải tranh synthetic | `POST /v1/story-runs`; `GET /v1/story-runs/{run_id}` | **PASS** — `201` và `200`; StoryRun `343d11c6-73fe-48e7-913a-069324b63b3d`. Ảnh là tranh rùa synthetic được tạo riêng cho kiểm thử. | `screenshots/04_parent_capture_selected.png`; API access log |
| Hiểu tranh bằng AI | `POST /api/parent/v1/ai/drawing-understandings`; Modal `drawing.analyze` | **PASS về kết quả API/UI** — HTTP `200`, Modal Call ID `fc-01M7TE95BG3GAJXK1CWM0TXV3K`, tổng thời gian API `66.203s`. UI nhận diện “con rùa”, độ tin cậy hiển thị 95% và các đặc điểm tranh; người lớn xác nhận chủ thể. | `screenshots/05_drawing_understanding.png`; `logs/api-e2e-events.log` |
| Xác nhận chủ thể và context | `POST /v1/story-runs/{run_id}/subject-confirmation`; `POST /v1/story-runs/{run_id}/context-confirmation` | **PASS** — cả hai API trả `200`. | Backend access log |
| Gợi ý hoạt động | `POST /api/parent/v1/ai/story-runs/{run_id}/activity-suggestions`; Modal `parent.activity.suggest` | **FAIL / terminal timeout** — xem chi tiết bên dưới. Không có activity selection receipt nên không đạt business gate để tạo story. | `screenshots/activity-after-timeout.png`; `logs/activity-modal-timeout.md` |
| Chọn và lưu hoạt động | `POST /api/parent/v1/ai/story-runs/{run_id}/activity-selection` | **NOT REACHED** — không có suggestion set hợp lệ. | Bị chặn theo gate |
| Sinh/review/xác nhận story | `POST /api/parent/v1/ai/story-runs/{run_id}/story-revisions` và các bước review | **NOT REACHED** — không có activity đã chọn. | Bị chặn theo gate |
| Tạo video im lặng LTX-2.5 | Video API/Modal | **NOT REACHED** — không gửi request video. | Bị chặn theo gate; video app không bị chạm |
| Quota/payment | — | **OUT OF SCOPE**, không gọi API và không sửa quota. | — |

## Diễn tiến và log lỗi activity

1. **17:42:46 UTC — HTTP 504 trước khi có Modal Call ID.** Language/audio app chưa được deploy; không có worker inference.
2. **17:45:57 UTC — HTTP 502, Call ID `fc-01M7TEMQ3PXNDNZRFP0K4EF8VM`.** Worker dừng ở `input_envelope` với `MODAL_WORKLOAD_NOT_ALLOWED`, trước khi nạp model. Nguyên nhân: allowlist L4 thiếu `parent.activity.suggest`. Đã thêm workload và test hồi quy offline (`3 passed`), sau đó deploy lại app.
3. **17:51:09 UTC — một request phục hồi duy nhất qua UI; HTTP 504 sau 1,800.048 giây.** Modal Call ID `fc-01M7TEYCN2MXMSY61WJN09TRRQ`; job `7d772621ac72ab90`; generation `7bda3e98b05bc804`; attempt `beb518acc5726d88`. Worker xác nhận envelope, workload, manifest, input, checkpoint, model load, prompt encoding và constrained decoder thành công. Nạp model mất `15.692s`; `model_inference` bắt đầu 17:51:43 UTC nhưng không có token/progress log hay terminal event trong 30 phút. Backend trả `504 PARENT_ACTIVITY_OUTCOME_UNKNOWN`, `worker_failure_boundary=worker_started_without_terminal_event`, `worker_last_stage=model_inference`, `worker_terminal_event=null`.

Modal phát cảnh báo Transformers rằng thiếu `causal-conv1d` và `flash-linear-attention`, nên dùng PyTorch reference fallback “much slower”. Đây là **dấu hiệu có thể góp phần làm chậm**, chưa đủ log để khẳng định là nguyên nhân duy nhất. Không có output để đánh giá schema/quality gate.

Sau timeout, Modal vẫn còn container chạy. Đã stop language/audio app lúc `01:22:15 +07`; xác nhận container list rỗng, app state `stopped`. Drawing app task-used cũng được stop lúc `01:23:42 +07`, tasks `0`. Video app không được gọi và vẫn để nguyên.

Không bấm nút “Thử lấy gợi ý lại” lần nữa. Theo Addendum 47, lượt phục hồi đã dùng hết; không có selection hợp lệ nên dừng tại đây, không tự chọn activity để lách gate, không gọi story hoặc video.

## Evidence

- Màn activity sau timeout: `screenshots/activity-after-timeout.png`.
- Ảnh chọn tranh: `screenshots/04_parent_capture_selected.png`.
- Kết quả hiểu tranh: `screenshots/05_drawing_understanding.png`.
- Log timeout Modal/API: `logs/activity-modal-timeout.md` và `logs/api-e2e-events.log`.
- Ảnh synthetic đầu vào: `input/synthetic-sea-turtle-drawing.png`.
- Task Compose stack và Metro được dừng lúc `01:27 +07` (không xóa volumes); emulator vẫn online tại màn lỗi để người dùng kiểm tra.

