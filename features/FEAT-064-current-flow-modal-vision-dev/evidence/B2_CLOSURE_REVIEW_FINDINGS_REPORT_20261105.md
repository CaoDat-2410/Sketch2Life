# FEAT-064 Goal B2 — closure-review findings remediation

Ngày: 2026-11-05  
Phạm vi: hồ sơ và kiểm tra tĩnh theo mục “B2 closure-review finding remediation scope (2026-11-05)” trong `approvals/TASK_APPROVAL.md`.

## Nguồn review và trạng thái

Review độc lập đóng B2 được owner chuyển lại bằng bản tóm tắt; văn bản review đầy đủ không có trong repository. Theo tóm tắt đó, B2 đang **NEEDS_REVISION** và chưa được owner chấp nhận. T12 chỉ được đóng có điều kiện trong giới hạn đã ghi ở approval: PostgreSQL do owner chạy; round-trip chỉ nhánh `pilot_vision` trên database mới với bảng pilot rỗng; reviewer không kết nối database.

## Findings

### P2 — Báo cáo sửa assertion nằm ngoài allowlist và snapshot cơ sở

`evidence/B2_T12_ASSERTION_FIX_REPORT_20261105.md` được phiên triển khai trước tạo theo prompt điều phối cho addendum sửa assertion ngày 2026-11-05. Đường dẫn này không nằm trong allowlist ban đầu ở plan §5 hoặc snapshot cơ sở `GB2_BASE_20261104T212854`; không giả định plan đã liệt kê file này. Mục approval dòng 893 đã ghi nhận file là bằng chứng bổ sung được giữ trong hồ sơ B2. Snapshot bổ sung cho closure review được tạo tại `.claude/handoff/snapshots/GB2_CLOSURE_20261105T111756/` và có manifest hash riêng được báo trong chat.

### P2 — Ledger B2 lỗi thời

Điều phối đã ghi mục hiệu chỉnh append-only tại ledger dòng 799. Phiên này không sửa ledger. Snapshot closure bổ sung bao gồm byte-copy của ledger hiện tại để đóng gói cùng các bằng chứng liên quan.

### P3 — Chưa có verdict mypy

Đã chạy từ thư mục `backend` đúng lệnh đã nêu ở `evidence/B2_T12_ASSERTION_FIX_REPORT_20261105.md` dòng 51:

```text
.venv/Scripts/mypy.exe --no-incremental tests/integration/test_be1_postgres_api.py
```

Output của lần chạy:

```text
error: INTERNAL ERROR -- Please try using mypy master on GitHub: [URL đã lược theo ràng buộc không ghi URL]
If this issue continues with mypy master, please report a bug at [URL đã lược theo ràng buộc không ghi URL]
version: 1.20.2
note: please use --show-traceback to print a traceback when reporting a bug
```

Hai URL trong output console được lược khỏi bản ghi này theo yêu cầu không ghi URL; phần văn bản còn lại và thứ tự dòng được giữ nguyên. Exit code: **2**. Kết quả là **NO VERDICT**: không có diagnostic type của source, finding P3 vẫn mở và không được tính là pass hay fail B2. Báo cáo sửa assertion dòng 51 ghi nhận cùng `INTERNAL ERROR`, exit 1, ở cả lần chạy trước và sau sửa assertion; vì vậy lỗi này đã tồn tại trước bản sửa assertion. `git status` sau lệnh không cho thấy file mới do mypy tạo.

## Bốn kiểm tra tĩnh — lần chạy trước khi tạo báo cáo

`validate_harness.py` in đường dẫn root tuyệt đối; trong báo cáo này giá trị đó đã được chuẩn hóa thành `root=.`. Các kết quả lần chạy trước khi tạo báo cáo:

| Lệnh | Output | Exit |
|---|---|---:|
| `python tools/validate_harness.py` | `HARNESS_VALID`; `root=.` (đã chuẩn hóa); `approval_gate=enabled`; `frontend_asset_gate=enabled` | 0 |
| `python tools/validate_repository_security.py` | `REPOSITORY_SECURITY_VALID`; `publishable_files_scanned=6424`; environment files, seed accounts, credentials/signing keys và external reference documents được loại trừ; `absolute_machine_paths=absent` | 0 |
| `python tools/validate_architecture.py` | `ARCHITECTURE_VALID`; dependency direction, mobile feature isolation, frontend asset gate, mobile AI boundary hợp lệ; Firebase data products absent | 0 |
| `git diff --check` | Exit 0, không có lỗi whitespace. Git đưa cảnh báo CRLF-to-LF cho các file dirty có sẵn trong context, decisions, source register, approval, ledger và status của FEAT-063/FEAT-064. | 0 |

Lần chạy lại sau khi báo cáo đã nằm trong repository:

| Lệnh | Output | Exit |
|---|---|---:|
| `python tools/validate_harness.py` | `HARNESS_VALID`; `root=.` (đường dẫn tuyệt đối đã chuẩn hóa); `approval_gate=enabled`; `frontend_asset_gate=enabled` | 0 |
| `python tools/validate_repository_security.py` | `REPOSITORY_SECURITY_VALID`; `publishable_files_scanned=6425`; các nhóm loại trừ như trên; `absolute_machine_paths=absent` | 0 |
| `python tools/validate_architecture.py` | Output giống lần trước: `ARCHITECTURE_VALID` và cả năm kiểm tra hợp lệ/absent như trên | 0 |
| `git diff --check` | Output giống lần trước: không có lỗi whitespace; các cảnh báo CRLF-to-LF hiện có vẫn xuất hiện. | 0 |

Khác biệt giữa hai lượt: số file publishable được quét tăng từ 6424 lên 6425 sau khi thêm báo cáo này. Ba lệnh còn lại có cùng verdict; `git diff --check` exit 0 ở cả hai lượt.

## Trạng thái và giới hạn còn nguyên

- B2 vẫn **NEEDS_REVISION** cho tới khi có review độc lập lại và owner đưa ra quyết định riêng. Phiên này không tuyên bố finding đã được reviewer chấp nhận, B2/T12 accepted hoặc pass.
- Phần database của `test_migrations.py` là **NOT RUN**. Round-trip chỉ bao phủ nhánh `pilot_vision` ở trạng thái trung gian, với bảng pilot rỗng; không bao phủ toàn đồ thị migration và không có dữ liệu.
- OpenAPI P3 được hoãn đến trước khi frontend/client tích hợp.
- T13 chỉ chứng minh helper timeout trả `unknown` với một lần gửi tới stub; không chứng minh job thật chuyển sang `UNKNOWN`.
- Orphan B1 là điều kiện riêng phải xử lý trước dữ liệu không synthetic hoặc trước khi dùng provider.
- Mọi dữ kiện database đều là owner-run. `OWNER_MODAL_CALL_APPROVED=NO`.
- Điểm dừng của phiên: **XONG-CHƯA REVIEW**; chờ phiên review độc lập khác.
