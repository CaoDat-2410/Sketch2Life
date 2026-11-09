# FEAT-063 Rev52 — API tổng hợp và kết quả AI Modal (không gồm video)

**Ngày:** 2026-11-06
**SRS chuẩn:** FEAT-063 `SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` v2.4-draft (bản nháp, chưa ký).
**Kế hoạch/phê duyệt:** [Plan Rev52](../../plan/PLAN_REV52_NONVIDEO_MODAL_AI_RELIABILITY_20261106.md), SHA-256 `6B3B1C25CD2A9974860A93551CDAD0FB3363DB38CB00D293ABB4818C9F0782D2`.
**Môi trường:** Modal `dev`; chỉ dùng dữ liệu tổng hợp, không dùng dữ liệu hay media của trẻ thật.

## Kết quả

- Tám worker không-video đang được phép gọi đều trả kết quả hợp lệ trong lần kiểm chứng sau khi bổ sung log theo phase và sửa parser story. `story.generate` và `storyboard.generate` dùng chung worker.
- Worker tùy chọn `drawing.segment` dừng ở feature gate với `MODAL_WORKLOAD_NOT_ALLOWED`; không tải model, không chạy suy luận. Registry vẫn tắt workload này theo cấu hình hiện tại.
- 33/33 request kiểm tra Parent API trả đúng kết quả mong đợi trên 13 route. Bốn request tiếp nối xác nhận kịch bản hợp lệ và run đến `VIDEO_ADMISSION_PENDING`; video không được gọi.
- Kết quả worker trực tiếp không đồng nghĩa với API sản phẩm đã tích hợp. Chỉ đường Parent phân tích tranh có HTTP→Modal live dispatch trong lần này. Story HTTP dùng fixture đã kiểm chứng; worker story Modal được gọi riêng. Các workload không có route sản phẩm được ghi `NOT_IMPLEMENTED` bên dưới.
- Không gọi bất kỳ API tạo video nào.

## Ma trận worker

| Workload | Model/revision đã ghim | Kết quả | Thời gian worker | Ghi chú |
|---|---|---:|---:|---|
| `drawing.analyze` | `Qwen/Qwen3.5-9B` / `c202236235762e1c871ad0ccb60c8ee5ba337b9a` | PASS | 28.039 giây | Phân tích ảnh tổng hợp; worker log có 22 event. |
| `story.generate` (`storyboard.generate`) | `Qwen/Qwen3.5-9B` / `c202236235762e1c871ad0ccb60c8ee5ba337b9a` | PASS | 107.469 giây ở lần retest cuối | Đúng `StoryRevisionDraftV1`, 5 cảnh, 30 giây; xác nhận vòng đời bướm và business rules. Toàn bộ lần gọi mất 135.740 giây. |
| `parent.sketch-guide.generate` | `black-forest-labs/flux-3-image-klein` / `09561231f44e41381c461caf53d5452005a60ac9` | PASS | 39.481 giây | Sinh line-sketch tổng hợp. |
| `teacher.sketch-deck.generate` | `Qwen/Qwen3.5-9B` / `c202236235762e1c871ad0ccb60c8ee5ba337b9a` | PASS | 34.047 giây | Deck theo lesson contract đã duyệt. |
| `lesson.plan.suggest` | `Qwen/Qwen3.5-9B` / `c202236235762e1c871ad0ccb60c8ee5ba337b9a` | PASS | 81.172 giây | Gợi ý lesson synthetic qua worker contract. |
| `lesson.visual.generate` | `black-forest-labs/flux-3-image-klein` / `09561231f44e41381c461caf53d5452005a60ac9` | PASS | 60.230 giây | Ảnh hoạt động synthetic, có metadata và output hash. |
| `tts.narration.generate` | `pnnbao-ump/VieNeu-TTS-v3-Turbo` / `61b85e3d937fbbacb387714180e8182823512523` | PASS | 9.646 giây | Tạo audio tổng hợp trên CPU. |
| `asr.transcribe` | `Systran/faster-whisper-large-v3` / `edaa852ec7e145841d8ffdb056a99866b5f0a478` | PASS | 17.095 giây | Chuyển audio tổng hợp thành transcript. |
| `drawing.segment` (SAM 2.1, tùy chọn) | `facebookresearch/sam2.1-hiera-small` / `2b90b9f5ceec907a1c18123530e92e794ad901a4` | BLOCKED BY FEATURE GATE | 0 giây inference | `MODAL_WORKLOAD_NOT_ALLOWED` tại `input_envelope`; không phải GPU queue timeout hay model failure. Giữ trạng thái tắt; không tính là worker đang hoạt động. |

Log summary sau kiểm chứng: [`runtime/recovery_after_wait_fix_20261106/workload_matrix.json`](runtime/recovery_after_wait_fix_20261106/workload_matrix.json), [`runtime/recovery_after_wait_fix_20261106/summary.json`](runtime/recovery_after_wait_fix_20261106/summary.json), [`runtime/worker_log_summaries.json`](runtime/worker_log_summaries.json).

## Sửa lỗi story và khả năng chẩn đoán

Các lần lỗi trước chỉ ra giới hạn chuỗi trong constrained decoder chặn trường story/scene ở độ dài thấp; worker kết thúc nhưng output không thỏa schema. Một số trường hợp còn bị từ chối bởi kiểm tra dấu câu cuối câu mà SRS không yêu cầu. Bản sửa tăng giới hạn trường nội bộ cho nội dung action/visual prompt/narration và bỏ điều kiện dấu câu tự đặt. Schema bắt buộc, kiểm tra nội dung không rỗng, thứ tự sự kiện vòng đời, fact checks, số cảnh và kiểm tra business rule vẫn giữ nguyên.

Log worker giờ ghi event bắt đầu/kết thúc cho các phase như đọc input, kiểm tra checkpoint, load model, inference, parse/validation và encode/transfer; kèm thời gian, model/revision, GPU, mã lỗi ổn định, kích thước/hash output và call correlation ID. Modal caller chỉ giữ event/field allowlist; không lưu prompt, story, text/audio/image, raw log body hay exception message. Khi không thấy terminal worker event, kết quả giữ trạng thái chưa xác định và không tự retry.

Kết quả story sau sửa: [`runtime/story_parser_srs_aligned_text_contract_retest_20261106/summary.json`](runtime/story_parser_srs_aligned_text_contract_retest_20261106/summary.json) và [`runtime/story_parser_srs_aligned_text_contract_retest_20261106/story_generate_result.json`](runtime/story_parser_srs_aligned_text_contract_retest_20261106/story_generate_result.json). Summary phase chi tiết ghi model load 11.577 giây, constrained decoder 3.703 giây, inference 87.941 giây và business validation thành công.

## Parent API

Trace synthetic ghi **33 request, tất cả đạt expected outcome**, qua 13 route. Mã HTTP gồm 200 (11), 201 (7), 202 (6), 422 (3), 409 (3), 404 (3); các mã lỗi là kết quả âm đã mong đợi của test case, không phải test fail. Trace chỉ giữ route, status, response field names, thời gian và mã lỗi; không lưu request/story text. Danh sách route đầy đủ ở [`runtime/parent_api_20261106/api_requests/api_request_trace_safe.json`](runtime/parent_api_20261106/api_requests/api_request_trace_safe.json).

Parent drawing API đã dispatch một ảnh tổng hợp qua Modal và nhận kết quả Qwen3.5; chi tiết ở [`runtime/parent_api_20261106/parent_api_drawing_worker.json`](runtime/parent_api_20261106/parent_api_drawing_worker.json). Story HTTP flow được kiểm thử qua fixture đã xác minh, không dispatch Modal trong HTTP request đó. Worker story được kiểm tra bằng live Modal call riêng. Bốn request tiếp nối đều đạt expected outcome, story schema/lifecycle hợp lệ, run kết thúc ở `VIDEO_ADMISSION_PENDING`, `video_calls=0`: [`runtime/parent_api_confirmation_resume_20261106/summary.json`](runtime/parent_api_confirmation_resume_20261106/summary.json).

### API sản phẩm chưa được triển khai

Các mục sau mới có worker/contract-level evidence hoặc AI candidate; chưa có authenticated, durable product API nối đầy đủ với job ownership, quota, persistence và review flow. Chúng **không được báo là API đã chạy thành công**:

- Parent: `parent.sketch-guide.generate`.
- Teacher: `teacher.sketch-deck.generate`.
- Admin/Teacher lesson authoring: `lesson.plan.suggest`, `lesson.visual.generate`.
- Speech API sản phẩm cho `tts.narration.generate` và `asr.transcribe`.
- SAM 2.1 segmentation hiện bị gate và không có route sản phẩm đã triển khai trong scope này.

Các route Parent hiện có được liệt kê trong trace; không thêm endpoint mới hoặc bật workload registry trong task này.

## Kiểm tra cuối và cleanup

- Modal worker suite: **97 passed**.
- Backend focused AI/parser/Parent API contract set: **59 passed**.
- Ruff `--select E4,E7,E9,F`: pass trên file implementation và script Rev52.
- `py_compile`: pass trên file Python đã sửa và script Rev52; `git diff --check`: pass.
- Modal app list sau cleanup: không còn app/task của lần chạy này. Container `sketch2life-rev52-parent-api-pg-20261106` ở trạng thái `Exited (0)`.
- Registry workload flags vẫn tắt. Không sửa secret, không xóa shared Volume/checkpoint, không ghi shared database, không dùng dữ liệu thật.
- Chưa bật production, chưa kiểm thử video và chưa kiểm thử các API sản phẩm còn thiếu ở trên.

## Evidence index

- Toàn bộ runtime JSON/ảnh/audio tổng hợp: [`runtime/`](runtime/).
- Worker phase history: [`runtime/recovery_after_wait_fix_20261106/workload_matrix.json`](runtime/recovery_after_wait_fix_20261106/workload_matrix.json).
- API trace và kết quả continuation: [`runtime/parent_api_20261106/api_requests/api_request_trace_safe.json`](runtime/parent_api_20261106/api_requests/api_request_trace_safe.json), [`runtime/parent_api_confirmation_resume_20261106/summary.json`](runtime/parent_api_confirmation_resume_20261106/summary.json).
- Runner và log summarizer: [`../scripts/`](../scripts/).
