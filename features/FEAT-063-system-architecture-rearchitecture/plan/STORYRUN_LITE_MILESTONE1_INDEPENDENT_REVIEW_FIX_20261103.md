# Kế hoạch xử lý review độc lập Mốc 1 — 2026-11-03

Trạng thái: APPROVED / IN PROGRESS theo câu trả lời owner “Cho phép ghi approval và sửa 6 finding”. Nguồn: review độc lập commit `c4edf51fd5af69a327d6776625cf387447f4ec59`, kết luận NEEDS_REVISION với một P1, bốn P2 và một P3. Giữ HEAD, index, 55 thay đổi local A2 và dữ liệu hiện có. Chỉ sửa lát cắt StoryRun-lite và tài liệu/test liên quan; không triển khai A2 hoặc Mốc 2. Snapshot trước review và evidence Modal cũ là lịch sử.

Quyết định triển khai: D1 của M0 V12 đã cho phép cancel làm lối thoát khi `PREPARATION_REVIEW`; dùng lại route cancel, state `DELETE_PENDING` và receipt hiện có, không thêm state hay migration. Reconciliation dựa trên kết quả bất biến cùng tuple lưu trên run và input, không lọc theo trạng thái run. Phạm vi code: `repository.py`, `composition.py` và `photo_bridge.py` trong infrastructure/story_run_lite; application port/service StoryRun-lite; router StoryRun-lite nếu cần readiness. Tests: các test StoryRun-lite liên quan và test mới theo finding. Tài liệu: artifacts/storyrun-lite, plan, approval append-only, evidence, context/decisions/source/status. Không sửa source hoặc migration A1, canvas hay A2.

## Phạm vi và tiêu chí

1. **P1, lượt demo kế tiếp.** Thiết kế và kiểm thử đường kết thúc rõ ràng cho run sau `PREPARATION_REVIEW`, nhả active owner atomically mà không xóa asset/receipt/result. Ưu tiên tái sử dụng cancel nếu contract/state cho phép và làm rõ đây là đóng demo; nếu phải thêm state hoặc migration, xác minh SRS, constraint, contract và upgrade cũ trước, không sửa migration đã áp tùy tiện. Kiểm tra hai lượt ảnh khác nhau thành công trên cùng DB, cạnh tranh tạo run, replay và bảo toàn dữ liệu lượt trước.
2. **P2, ledger reconciliation.** Nhận diện kết quả Story đã commit bằng identity và hash kết quả bền vững, kể cả khi state đã chuyển do confirm/cancel/close; chỉ terminalize khi tuple run/job/attempt khớp và ledger `SENT`. Không suy đoán outcome, không gửi lại inference. Test crash/finalization failure sau khi commit Story cùng đua confirm/cancel, restart và mismatch identity.
3. **P2, replay attach.** Tra receipt đúng actor/scope/key/fingerprint trước điều kiện chỉ dành cho attach mới; đúng replay trả snapshot ban đầu sau thành công, recovery và cancel. Key trùng fingerprint khác trả conflict; actor khác không thấy receipt; replay không dispatch thêm. Kiểm thử qua HTTP/service và PostgreSQL thật, không chỉ repository.
4. **P2, singleton.** Startup dùng lock không chờ và fail closed khi lock đang giữ. Phát hiện kết nối lock mất/sai owner, readiness fail và từ chối lệnh mới; phân biệt claimant đang chạy theo giới hạn D17, không tuyên bố hủy được request provider. Kiểm thử ngắt session lock thật, instance cũ từ chối lệnh, instance mới có thể nhận lock, và lỗi DB không bị hiểu là lock an toàn.
5. **P2, Bruno upload.** Thêm bước `03-upload-part` trước complete, hướng dẫn các header/hash đúng và kiểm tra luồng thủ công/Bruno trên DB task-owned.
6. **P3, GET sau confirm.** Thêm request hoặc hướng dẫn GET riêng có assertion `PREPARATION_REVIEW`, không dùng assertion `SUBJECT_REVIEW` của request 07; cập nhật hướng dẫn và collection đồng bộ.

## Kiểm chứng và bàn giao

- Viết focused test có ý nghĩa cho từng finding; chạy unit/contract, PostgreSQL tích hợp trên DB loopback task-owned mới với test fixtures synthetic, guard/ledger, migration nếu có, Bruno local với ClamAV/Vision stub khi đủ môi trường; báo riêng PASS/FAIL/SKIP/NOT RUN. Không dùng hoặc reset DB `sketch2life`, A2 hay DB hiện có.
- Chạy Ruff, mypy theo phạm vi, harness, security, architecture, `git diff --check`; lưu evidence và snapshot. Không gọi Modal/GPU/provider, không stage/commit/push/merge. Ghi rõ không chạy lại live và không tuyên bố review đã ACCEPTED.
- Cập nhật trạng thái Mốc 1 thành FIXED — CHỜ REVIEW ĐỘC LẬP khi mọi kiểm tra bắt buộc đạt; nếu blocker thì ghi thực trạng. Soạn prompt review vòng 2 kiểm tra cả sáu finding và tác động chéo.
- Approval mới cần ghi rõ owner yêu cầu sửa sáu finding, hash plan, scope và giới hạn; không thay đổi hoặc xóa approval lịch sử. Chỉ bắt đầu implementation sau khi owner cho phép ghi approval theo `.codex/sketch2life-harness.md`.
