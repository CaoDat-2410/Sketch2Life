# Parent Android và Teacher Presentation — kiểm thử E2E thật

**Ngày:** 2026-11-12 (Asia/Saigon)<br>
**Kết quả chung:** **PARTIAL / BLOCKED**<br>
**Video inference:** không chạy<br>
**Fixture:** không dùng làm input/output của workflow. Dùng một ảnh hươu tổng hợp, không có dữ liệu trẻ thật.

## Tóm tắt

- Chạy Parent qua Android emulator `emulator-5554`, Expo app, Firebase Auth Emulator và backend Docker ở cổng `58000`.
- Đăng nhập và tạo hồ sơ synthetic được. Ảnh synthetic được chọn từ thư viện Android và đi qua API thật.
- Hai request AI thật đã được gửi: FLUX line-sketch và Qwen3.5 drawing understanding. Cả hai đều không tạo được kết quả được sản phẩm chấp nhận.
- Qwen đã tải model và hoàn tất inference; lỗi cuối là đầu ra không parse được thành JSON (`MODAL_MODEL_OUTPUT_INVALID`). API đã trả 504 trước khi worker ghi terminal event; sau đó Modal log xác nhận lỗi terminal. StoryRun vẫn `AWAITING_RECONCILIATION`; không gửi lại request.
- Không gọi activity suggestion hay story generation vì chưa có subject candidate được xác nhận. Không gọi video theo yêu cầu.
- Teacher Presentation không thể chạy thật trong stack này: database không có Teacher, organization, class hay bài giảng do Teacher duyệt để mở occurrence. Có một lesson library seed dùng cho Parent, không phải Teacher classroom content. Modal cũng không tìm thấy các function của language/audio app. Không tạo deck giả để lấp chỗ trống.
- Vì không có ảnh AI nào qua quality/contract gate, thư mục `ai_outputs` và `screenshots` để trống. Không chụp UI chung theo yêu cầu chỉ lưu ảnh kết quả AI.

## Môi trường và dữ liệu

| Thành phần | Trạng thái khi kiểm thử |
|---|---|
| Android | `emulator-5554`, Parent Expo app |
| Backend | `http://127.0.0.1:58000`, Docker API healthy |
| PostgreSQL / Firebase Auth Emulator / MinIO / Redis / ClamAV | Healthy |
| Modal health sidecar | `DEGRADED`, Docker health `unhealthy` |
| Parent account/profile | Firebase Auth Emulator; hồ sơ synthetic, 72 tháng |
| Consent | Chỉ local synthetic authorization `local-synthetic-demo-v1`; **không phải consent pháp lý** |
| Ảnh | `inputs/synthetic_deer_drawing.png`, SHA-256 `3B3B027F2310A568D64009564BBE7DF2CE702EE8FC9EDF75328817EDD40DFBBD` |
| Video | 0 request |

Database kiểm tra theo aggregate: có 2 identity Parent active; không có identity/assignment Teacher, organization hoặc class. Lesson library có 1 seeded item/version và 3 activity rows, nhưng đây không phải lesson/occurrence của Teacher. Không đọc email, mật khẩu, token hay nội dung bài giảng.

## Kết quả Parent trên Android

| Bước | API / worker | Kết quả | Thời gian và dấu vết |
|---|---|---|---|
| Đăng nhập Parent | Firebase Auth Emulator → backend | PASS; phiên đã được tái sử dụng, không tạo lại tài khoản | Thao tác trên emulator |
| Tạo hồ sơ và synthetic authorization | Parent profile/consent flow | PASS cho local dev synthetic; không đại diện luồng consent hợp pháp | Hồ sơ `Synthetic Deer Demo`, 72 tháng |
| Tạo line-sketch tùy chọn | `POST /api/parent/v1/ai/sketch-guides` → `parent.sketch-guide.generate` → `black-forest-labs/flux-3-image-klein` (`09561231f44e41381c461caf53d5452005a60ac9`, L40S) | FAIL: worker tạo candidate nhưng progressive quality gate từ chối `MODAL_PROGRESSIVE_GUIDE_STROKES_CHANGED`; API trả 502 `MODAL_WORKER_FAILED_TERMINAL`. Không có ảnh được lưu/trả cho UI | Bắt đầu khoảng 09:13:40 +07; worker khoảng 65.272 giây; request/UI tổng khoảng 90 giây. Request `d3be8101-25fe-4215-999b-9fb60397ce4a`, job `d70ca26151427b6f`, Modal call `fc-01M76RGA2YJH6414XESWPMXJT9` |
| Chụp/chọn tranh | Android gallery → artwork upload/attach | PASS sau khi sửa lỗi FK bên dưới; ảnh đến được worker phân tích, kích thước upload 1,819,185 byte | Input synthetic ở `inputs/` |
| Tạo StoryRun | `POST /api/parent/v1/story-runs` | PASS: 201 sau hai lỗi contract/persistence được sửa trong worktree/runtime | Run `a533da13-f60b-41dc-af96-91dbc9f31578` |
| Hiểu tranh | `POST /api/parent/v1/ai/drawing-understandings` → `drawing.analyze`, Qwen/Qwen3.5-9B | FAIL. Worker đã load model, inference thành công trong 30.509 giây, nhưng JSON đầu ra hỏng: `JSONDecodeError: Unterminated string at line 6 column 5 (char 130)`; terminal code `MODAL_MODEL_OUTPUT_INVALID`. API ban đầu trả 504 `MODAL_OUTCOME_UNKNOWN` sau khoảng 65 giây | Modal call `fc-01M76TA2PCDT4TDCZ1ZWPZ9RJR`; request `fbb47d97-3c6f-4215-88bd-64cb879fac04`; model load 17.375 giây, tiền xử lý 0.038 giây, encode prompt 0.074 giây, inference 30.509 giây |
| Trạng thái sau lỗi | `GET /api/parent/v1/story-runs/{run_id}` | 200 nhưng run chưa hoàn tất: `INPUT_PROCESSING` / `AWAITING_RECONCILIATION`, `DRAWING_OUTCOME_UNKNOWN`, revision 3, input revision 2, `retryable=false` | Đọc read-only từ DB sau khi Modal ghi terminal failure. Không thử gửi lại |
| Lịch sử | `GET /api/parent/v1/story-runs?profile_id=…&limit=20` | FAIL: 405 Method Not Allowed. UI gọi collection GET nhưng router hiện không hỗ trợ method/path đó | Query string đã được loại khỏi log evidence |
| Chọn hoạt động | Catalog-first + Qwen | **Chưa chạy**: thiếu subject AI hợp lệ để xác nhận; không bypass gate | Không phát sinh request |
| Kịch bản/storyboard | Qwen `story.generate` | **Chưa chạy**: điều kiện hiểu tranh/xác nhận chủ thể chưa đạt; ngoài ra language/audio Modal functions không resolve | Không phát sinh request |
| Tạo video | LTX-2.5 | **Không chạy theo yêu cầu** | 0 request |

### Lỗi đã sửa trong lúc kiểm thử

1. `POST /api/parent/v1/story-runs` ban đầu 422: Pydantic `strict=True` từ chối UUID dạng chuỗi của JSON wire request. Hai UUID wire fields đổi sang `Field(strict=False)`; các field còn lại vẫn strict.
2. Tạo run tiếp theo 409 do Python `None` được lưu thành JSON `null` trong JSONB, làm sai check phân biệt SQL `NULL`. Cột `lesson_pin_snapshot` đổi sang `JSONB(none_as_null=True)`.
3. Đính kèm artwork trả 409 do `core_asset_lineage` insert chạy trước khi ORM flush các CoreAsset rows (session dùng `autoflush=False`). Thêm flush trước insert lineage; sau đó ảnh đến được worker.
4. Parent Capture screen từng lỗi `ReferenceError` do dùng `workflowNotice` nhưng không destructure prop. Đã sửa destructuring; màn chụp ảnh tiếp tục hoạt động.

Các thay đổi source nằm trong worktree, chưa commit. API container được cập nhật file source có mục tiêu rồi restart để kiểm tra; lượt chạy này **không chứng minh** Docker image mới đã build hoàn chỉnh từ source. Compose recreate sẽ cần build/recreate để loại bỏ overlay sửa nóng.

## Modal startup/warmup từ Docker

Sidecar status là `DEGRADED`; warmup không tạo product output và không gọi inference:

| App / workload | Warmup | `/health` probe |
|---|---|---|
| Drawing VLM / `drawing.analyze` | READY, 33.849 giây | FAILED `TimeoutError` |
| FLUX / Parent guide | READY, 48.139 giây | FAILED `TimeoutError` |
| FLUX / lesson visual | READY, 49.968 giây | FAILED `TimeoutError` |
| Language/audio / story, activity, Teacher deck, lesson plan | FAILED `NotFoundError` khi resolve các function | FAILED `NotFoundError` |

Điều này giải thích vì sao container `modal-health` unhealthy. Cần đồng bộ lại tên/environment/deployment của language/audio functions; với drawing/FLUX cần tìm vì sao health web endpoint timeout dù warmup function trả READY. Warmup pass không đồng nghĩa endpoint product `/health` pass.

## Teacher Presentation

**Không thể bắt đầu E2E thật trong lượt này.** Database hiện không có tài khoản Teacher, organization, class hay lesson được Teacher duyệt để chạy classroom occurrence; lesson library seed hiện có chỉ phục vụ luồng Parent. Không có dữ liệu đăng nhập Teacher đã seed. Sidecar cũng không resolve được `generate-teacher-sketch-deck`/`suggest-lesson-plan` trong `sketch2life-srs23-language-audio-dev`. Vì vậy không có presentation AI thật để chụp full slide. Không dùng output cũ, fixture hay nội dung giả làm bằng chứng.

Để chạy tiếp cần: (1) tạo/seed Teacher qua luồng auth + role được backend cho phép; (2) có organization/class và lesson version do Teacher tạo/duyệt; (3) deploy/resolve các language/audio Modal functions trong đúng `dev` environment; (4) health probe app pass. Sau đó mới chạy presentation từ UI Teacher và lưu ảnh AI thực.

## API và vấn đề cần sửa tiếp

| Mức | API / thành phần | Tình trạng | Hướng xử lý |
|---|---|---|---|
| P0 | `POST /api/parent/v1/ai/drawing-understandings` | Qwen3.5 inference cho JSON sai format; backend trả 504 trước terminal failure, run mắc `AWAITING_RECONCILIATION` | Ràng buộc JSON output/decoder và parser; xử lý outcome reconciliation để UI không giữ trạng thái không rõ mãi. Chỉ gửi request mới sau khi có quyết định retry an toàn |
| P0 | Modal language/audio app | Các function story/activity/Teacher không resolve (`NotFoundError`) | Xác minh app/function deployment trong `dev`, tên registry và health URL; chạy health trước workflow |
| P1 | `POST /api/parent/v1/ai/sketch-guides` | FLUX candidate bị progressive-stroke gate từ chối | Sửa cấu trúc nét tích lũy theo stage; không nới gate nếu chưa có rubric thị giác xác nhận |
| P1 | Parent history collection GET | UI nhận 405 | Đối chiếu OpenAPI/router và cập nhật UI gọi đúng API hiện hành hoặc bổ sung contract nếu thiếu |
| P1 | Docker Modal health sidecar | `DEGRADED`/`unhealthy`, dù một số warmups READY | Sửa health endpoint/discovery trước khi coi startup AI đã sẵn sàng |
| BLOCKED | Teacher full presentation | Không có Teacher/org/class/lesson test data; language app chưa resolve | Chuẩn bị Teacher tenant thật qua luồng chuẩn rồi chạy trên Teacher UI |

## Evidence, ảnh và giới hạn

- Không có AI image/artifact nào vượt qua gate và được trả lại. Vì vậy `ai_outputs/parent`, `ai_outputs/teacher/presentation`, `screenshots/parent_ai_results` và `screenshots/teacher_presentation` cố ý không có file.
- Không chụp UI thông thường; chỉ ảnh tranh input synthetic được giữ làm provenance.
- Không gửi request activity, story, teacher deck, video, SAM2, ASR/TTS; các luồng đó là chưa test, không được đánh dấu PASS.
- Không thay đổi root `.env`, credentials, production Firebase, shared Modal Apps, volumes hoặc dữ liệu ngoài phạm vi. Docker stack vẫn chạy để giữ nguyên môi trường người dùng.
- Log đã lọc, không chứa token, email hay query string cá nhân: `logs/modal_qwen35_drawing_terminal.txt`, `logs/modal_startup_health_summary.json`, `logs/parent_api_access_summary.txt`, `logs/docker_service_status.txt`.
