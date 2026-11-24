# Parent Android E2E + backend activity quality fix — 2026-11-21

## Kết luận

Đã kiểm tra luồng bằng ứng dụng Parent thật trên Android emulator, API backend thật và Modal; không dùng preview harness hay response fixture cho lượt E2E. Luồng đi qua chọn chủ đề, ảnh rùa biển tổng hợp, nhận diện tranh, xác nhận chủ thể/context và gọi gợi ý hoạt động.

**Luồng dừng ở bước gợi ý hoạt động.** API đã lưu ba bản nháp AI có câu tiếng Việt bị cụt nhưng vẫn trả thành công cho UI. Đây là lỗi quality gate ở backend/worker, không phải lỗi render của UI. Không chọn hoạt động, không gọi tạo kịch bản/video và không đọc hoặc thay đổi quota.

## Runtime evidence

- Android: `emulator-5554`, ứng dụng Expo thật từ worktree `feature/fe-mobile-remediation`.
- API: task API `/health` trả HTTP 200.
- Dùng StoryRun synthetic đã có; không tạo tài khoản/hồ sơ/run mới trong lượt này.
- Catalog-first lookup chạy đúng nguồn published/shared lesson. Kết quả đọc catalog: `accessible_lesson_count=0`, `eligible_activity_count=0`, `candidate_count_sent=0`; vì vậy hệ thống đi vào nhánh AI fallback theo contract.
- Drawing Modal call `fc-01M7XJH73NXHASRVB70REA0WA6`: Qwen3.5-9B nhận diện “con rùa”, worker elapsed `44,370 ms`. UI hiển thị confidence 90% và các đặc điểm nhìn thấy; người lớn xác nhận subject/context.
- Activity API request ID `cc698d79-db5f-4c4c-a882-6bdf3be22224`; Modal call `fc-01M7XJR9P6THVS4TQRWQW7QRRK`, workload `parent.activity.suggest`, elapsed `136,751 ms`. Worker trả ba hoạt động; backend persist và API trả các câu bị cắt giữa ý, ví dụ kết thúc bằng `môi trường tự`, `hoạt động bình th`, `hình lục`, `để trẻ`, `hoặc có`, `con r`.
- Read-only DB verification: run ở revision 2 / `PREPARATION_REVIEW`; activity job `SUCCEEDED`; có một suggestion set ở `AI_GENERATED_FALLBACK`; chưa có activity selection.
- Screenshot kết quả AI lỗi: [parent-activity-result.png](screenshots/parent-activity-result.png). Các checkpoint khác: [parent-drawing-wait.png](screenshots/parent-drawing-wait.png), [parent-after-subject-confirmed.png](screenshots/parent-after-subject-confirmed.png), [parent-after-context.png](screenshots/parent-after-context.png), [parent-activity-request.png](screenshots/parent-activity-request.png).

## Nguyên nhân backend

1. Worker yêu cầu dấu kết câu và giới hạn ký tự, nhưng parser cũ chấp nhận phần thân câu bị cắt ở những vị trí ngữ pháp chưa hoàn chỉnh.
2. Backend fallback quality gate chỉ kiểm tra dấu kết câu, marker nội dung và một số ràng buộc an toàn; chưa phát hiện đuôi câu tiếng Việt dang dở.
3. API vì vậy persist và trả dữ liệu lỗi. UI đã hiển thị đúng payload nhận được; sửa riêng UI sẽ không ngăn dữ liệu lỗi được lưu.

## Sửa mã nguồn đã thực hiện (chưa deploy)

- Backend `parent_activity_suggestions.py`: thêm kiểm tra phần cuối câu tiếng Việt bị cụt; từ chối bằng mã chẩn đoán ổn định `ACTIVITY_TEXT_INCOMPLETE`. Áp dụng cho fallback AI; không thay đổi catalog-selected teacher-authored activity.
- Modal worker `language_audio_app.py`: thêm cùng kiểm tra trước khi chấp nhận output; prompt yêu cầu kết thúc ý trọn vẹn và rút ngắn câu thay vì cắt từ/cụm bổ nghĩa; thu giới hạn body để chừa chỗ cho terminator.
- Regression tests: bao phủ các đuôi cụt đã xuất hiện và đồng bộ worker contract tests với schema câu có `body` + `terminator` hiện tại.

**Giới hạn triển khai:** code sửa chưa được deploy vào task API hoặc Modal. Approval Addendum 88 chỉ cho phép sửa và kiểm tra offline; cấm Modal deploy/warm/stop và lượt inference hoạt động thứ hai. Vì vậy runtime hiện tại vẫn có thể tái hiện lỗi cũ cho đến khi worker/backend được triển khai theo approval mới. Không có lượt AI lặp lại.

## Verification

| Kiểm tra | Kết quả |
|---|---|
| `backend/tests/unit/test_parent_activity_worker_contract.py` + `backend/tests/unit/test_parent_activity_suggestions.py` | PASS — 36 tests |
| `deployment/modal/srs_v23/tests/test_parent_activity_workload_gate.py` + Qwen activity contract subset | PASS — 24 tests; 40 deselected |
| Mobile `parentDrawingTerminal.test.ts` | PASS — 6 tests (đã chạy trước bước backend activity) |
| Mobile typecheck | PASS — 0 lỗi (đã chạy trước bước backend activity) |
| `git diff --check` | PASS |
| Ruff | Không chạy được: `ruff` không có trong `.venv-modal` và không cài trong Python env đang dùng |
| Repository security validator | FAIL do các finding lịch sử trong worktree (đường dẫn máy Windows trong tài liệu cũ và một placeholder bị rule nhận diện); không thêm secret hoặc credential mới. Không commit/push trong lượt này. |

## Phạm vi luồng

| Bước | Kết quả |
|---|---|
| Chọn topic và ảnh synthetic | PASS |
| Drawing VLM qua Modal | PASS sau đúng một lần retry pre-dispatch đã được phê duyệt |
| Xác nhận chủ thể và context | PASS |
| Query lesson/activity catalog | PASS về tích hợp; catalog hiện không có ứng viên truy cập được cho context này |
| AI fallback activity | API/Modal trả kết quả nhưng **FAIL quality**; đã giữ nguyên để điều tra |
| Chọn hoạt động | Chưa thực hiện |
| Story generation/review | Chưa gọi |
| Video | Chưa gọi |
| Quota/payment | Không truy cập |

