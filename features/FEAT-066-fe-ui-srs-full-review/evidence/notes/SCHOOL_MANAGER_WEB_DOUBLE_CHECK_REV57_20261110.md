# Double-check School Manager Web sau remediation — SRS v2.7-draft Rev57

Ngày rà: 2026-11-10 (Asia/Bangkok)
Worktree: `F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation`
Branch: `codex/fe-ui-web-remediation`
HEAD đầu lượt double-check: `bd55ffd8cff06d0f395f1afa5a8a8ac4081d5c75`
Plan/approval: FEAT-066 revision 6, `APPROVED_FOR_IMPLEMENTATION`, plan SHA-256 `25E24871660A892C3380A359EA5285C6148B4C47FC75248C35D71FAC303231C9`.

## Authority và cách rà

- Đã đọc `docs/context/SRS_AUTHORITY.md`; authority trỏ tới SRS FEAT-063 duy nhất. SHA-256 xác minh là `BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5`, v2.7-draft Rev57, vẫn chờ owner sign-off. Dùng §§1–31 làm yêu cầu; không dùng bản SRS cũ trong worktree hay §32 làm yêu cầu.
- Xác minh Git root là worktree được chỉ định và branch là `codex/fe-ui-web-remediation`. Các thay đổi ngoài FEAT-066 đang có trong worktree (root `approvals/TASK_APPROVAL.md`, Parent UI và FEAT-070) được giữ nguyên, không stage.
- Dùng Vite School Manager đã chạy ở `http://127.0.0.1:5173/`; `netstat` xác nhận listener là `127.0.0.1:5173`, PID 19084. Không khởi chạy lại FE. Browser capture dùng Edge headless trên CDP loopback `127.0.0.1:9233`; capture helper chặn HTTPS và backend localhost. Chỉ dùng fixture xem thử; không dùng credential, backend, provider, dữ liệu thật hoặc media trẻ.
- Chụp lại `/login`, M01 và M02 dashboard, teachers, classes, quota, settings ở desktop 1440×900 và viewport hẹp 390×844. Ảnh và số đo nằm ở `../screenshots/double-check/`; các ảnh trước remediation vẫn được giữ nguyên.

## Kết quả xác minh

| Hạng mục | Kết quả double-check |
|---|---|
| M01 — Yêu cầu chỉnh sửa | Sau thao tác fixture: `Chờ duyệt: 2`, `Đã duyệt: 0`, `Yêu cầu chỉnh sửa: 1`. Toast nói rõ đây là state local và chưa gửi API. Không tăng nhầm bộ đếm duyệt. |
| M01 — tab/panel | Tab có `role=tablist/tab`, ID và `aria-controls`; panel có `role=tabpanel` và `aria-labelledby`; selected/hidden/roving tabindex khớp. ArrowRight chuyển focus, selected state và panel sang tab kế tiếp. Source handler có ArrowLeft, Home, End; không dùng screen reader thật trong lượt rà này. |
| Inbox | Header hiển thị status tĩnh `Hộp thư chưa khả dụng`, không phải nút, không có unread dot. Không tìm thấy inbox API/route phù hợp trong contract đã rà. |
| Organization pill | Organization context là `DIV` tĩnh; không có mũi tên hoặc affordance dropdown/chuyển tổ chức. |
| Responsive M02 | Tất cả trang đã chụp đều không có document-level horizontal overflow ở 390px. Tiêu đề/actions lớp không chồng; nút tạo lớp nằm trọn trong viewport (x=113–357). Nút quota nằm trọn trong viewport (x=174–354); desktop cũng nằm trong viewport. Bảng lớp dùng scroll container ngang riêng ở 390px (244px viewport, 552px nội dung), không làm tràn toàn trang. CSS đặt min-height 44px cho action ở breakpoint hẹp. |
| Login/logout | Login không tràn ở hai kích thước; label email và required state còn. Logout vẫn đạt kiểm tra EV-005: Enter từ dashboard/settings về `/login`, xóa hai session key, route bảo vệ không mở lại; icon logout hẹp có tên truy cập và 44×44px. Đây là fixture session, không chứng minh Firebase sign-out vì bridge không cấu hình. |
| Billing label | Double-check phát hiện nhãn “Tự động gia hạn gói hàng tháng (MoMo / VNPAY)” hàm ý chu kỳ cố định dù chưa có API. Đã đổi thành “Tự động gia hạn”; state vẫn `Chưa khả dụng`. SRS yêu cầu kỳ billing được chọn và không chốt riêng nhãn tháng cho UI này. |
| Quyền riêng tư | Các màn School Manager không yêu cầu/tải/hiển thị ảnh, video, story hay playback của trẻ. Roster API mode (đã đọc source) chỉ render tên; không gọi API trong local capture. |

Không có automated tests/builds chạy trong lượt này theo giới hạn đã nêu.

## Ma trận luồng SRS §21.5 và phụ thuộc còn thiếu

| Luồng | Trạng thái FE/API đã xác minh | Cách hoàn tất thật / dependency |
|---|---|---|
| Dashboard và tenant context | Dashboard local dùng fixture có banner; không có summary API. Tenant label tĩnh. Login preview không xác thực production. | Cần auth/permission server và API summary có tenant scope; kiểm thử isolation bằng môi trường backend và dữ liệu tổng hợp được phê duyệt. |
| Capacity, tạo/archive/tạm ngưng lớp | Class list có API đọc. Create bị disable vì endpoint hiện không enforce capacity; archive/suspend chưa có endpoint. Preview chỉ là fixture. | Backend cần capacity entitlement/summary và transaction guard, class lifecycle endpoints, trạng thái pending/error/response. |
| Teacher provision, directory, assignment/transfer/offboard, groups | Assignment write endpoint mức thấp không đủ chọn identity trong organization; thiếu Teacher directory/provision/invitation và transfer saga/UI; Parent group flow chưa nối. Các fixture/actions được đánh dấu unavailable. | Cần API directory/provision/invitation, assignment scope và transfer saga/audit; group contract nếu scope yêu cầu. Không tự nhập opaque identity hoặc gửi email giả. |
| Roster | BE1 profile-list read contract có; API mode có read-only list/roster hiển thị tên. Local screenshot không gọi backend. | Khi có staging/test session được duyệt, xác nhận scope assignment/consent bằng dữ liệu tổng hợp; full add/edit/reassignment enrollment cần contract riêng. Không mở media. |
| Invoice/payment/subscription/renewal/downgrade | Settings nêu unavailable; nút tắt; không có giá hoặc giao dịch giả. Label chu kỳ đã được trung tính hóa. | Cần invoice, payment attempt/callback, subscription/capacity-period API, idempotency/audit và policy/price version đã được owner chốt. |
| Quota organization/top-up | Số liệu chỉ là fixture, cảnh báo nói rõ; add-slot/top-up disabled. | Cần quota summary từ grants/usage ledger và API purchase/payment grant; price/included units/allocation còn OPEN trong SRS. |
| Inbox thông báo | Không có route/API phù hợp; FE hiển thị status unavailable, không báo unread. | Cần inbox API/route và dedupe/delivery state; payload phải tránh child data/media. |
| M01 duyệt PUBLIC | Có API access-grant list/decision trong source và API mode; local fixture kiểm tra count/interaction. Không gọi authenticated backend. | Integration QA cần backend test/staging và response/error state thật; giữ media ngoài response. |
| Feedback reply của trường | Chưa có School Manager route/list/reply API; chỉ được báo unavailable trên dashboard. | Cần school-scoped feedback list/reply contract và UI route; không thay bằng chat/inbox. |

## Điểm cần owner xác nhận, chưa tự đổi chính sách

M01 hiện yêu cầu check đủ “4 tiêu chí sư phạm” trước khi approve. FR-PL-05 yêu cầu Manager approval trước PUBLIC nhưng không định nghĩa rubric hoặc số tiêu chí. Ghi nhận đây là quy tắc UI chưa trace được vào SRS; owner cần xác nhận rubric trước khi coi đó là policy chính thức. Lượt này chỉ xác minh hành vi, không tự bỏ/đổi gate.

## Kết luận

Các lỗi UI M01 counter, inbox unread affordance, responsive M02, tab semantics/keyboard và organization dropdown cue đã được xác minh đạt theo remediation. Các flow chưa hỗ trợ được hiển thị unavailable, không giả lập giao dịch/thành công; các dependency cụ thể ở bảng trên. Đây là kết quả review FE local/source, không phải xác nhận end-to-end backend, authorization, payment hay sign-off cho SRS.
## Repository checks before commit

- `python tools/validate_repository_security.py`: PASS (`REPOSITORY_SECURITY_VALID`; 6,845 publishable files scanned; no absolute machine paths detected).
- `python tools/validate_architecture.py`: PASS.
- `git diff --check`: PASS (Git emitted only CRLF-to-LF normalization warnings for the four edited Markdown files).
- `python tools/validate_harness.py`: FAIL due solely to the pre-existing untracked `features/FEAT-070-parent-web-video-admission-demo-fix` missing `evidence/raw`, `screenshots`, `metrics`, and `notes`. FEAT-070 is outside the authorized School Manager/FEAT-066 scope and was left unchanged.
- No tests or builds were run.