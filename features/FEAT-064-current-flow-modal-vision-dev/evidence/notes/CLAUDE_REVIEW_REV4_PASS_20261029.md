# Claude review rev4 — 2026-10-29

Chủ task cung cấp review `PLAN_REVIEW_PASS` cho rev4 SHA-256 `E109585296D9A937319C16EE2A0B7305D8577FE3E6A42B593A9877FE42385E7A`. Reviewer báo không còn P1/P2, có P3-C cần xử lý tại T0. Đây là review plan; không phải task approval hoặc evidence runtime. Plan và approval giữ nguyên.

## P3-C — việc cần đặc tả tại T0

- Chốt invariant `send ⇒ ledger commit ⇒ witness consumed`, phase/outcome provenance, ownership T6/T8, projection `NOT_SENT_*` không nút retry, và witness failure model + test plan trong T0/manifest. Trước implementation, cập nhật contract/plan và lấy review/approval theo revision/hash thực tế nếu cần thay đổi.
- Lưu ý bảo thủ: sau restore DB về trước commit, witness consumed nhưng ledger vắng vẫn có thể là trường hợp **đã gửi trước restore**. Không suy `ledger vắng ⇒ chắc chắn chưa gửi` trừ khi chứng minh được DB chưa rollback hoặc có evidence độc lập đủ tin cậy. Thiếu bằng chứng thì cap đóng và outcome UNKNOWN. Bất biến một chiều không tự chứng minh điều ngược lại sau restore. Rà fault injection trường hợp này trong T7c/T12 sau approval.

## OD-3 — lựa chọn đang chờ chủ task

Claude đề xuất kho witness từ xa có conditional writes, hoặc file local với tuyên bố chấp nhận rủi ro host rollback. Cả hai là đề xuất, chưa được chọn. Kho từ xa cũng chỉ đạt invariant nếu có điều kiện atomic/durable và bảo vệ rollback đã được chứng minh. Chọn risk acceptance cho host rollback sẽ nới AC18 hiện tại, cần đổi plan và review/approval đúng scope trước M3; không tự coi là tương đương bảo đảm hiện tại. Không chọn nhà cung cấp hoặc phát sinh chi phí khi chưa được duyệt.

OD-1–OD-4/owner/manifests còn mở. Approval `AWAITING_APPROVAL`, chưa có implementation/DB/witness/provider authorization; Modal/backend ở checkpoint đã dừng. Không commit/push hoặc đọc secret.
