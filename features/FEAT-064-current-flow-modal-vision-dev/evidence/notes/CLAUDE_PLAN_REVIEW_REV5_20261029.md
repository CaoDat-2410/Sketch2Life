# Rev4 → rev5 — 2026-10-29

Claude review rev4 `PLAN_REVIEW_PASS` với P3-C; đây không phải PASS rev5 hoặc approval thực thi. Theo yêu cầu chủ task, rev5 ghi OD-3=B và P3-C. Rev4 snapshot `PLAN_REV4_REVIEWED_20261029.md` SHA-256 `E109585296D9A937319C16EE2A0B7305D8577FE3E6A42B593A9877FE42385E7A`; rev5 `plan/PLAN.md` SHA-256 `D457DC5DC2E75890E8ACC0BB59DA6C0F354BA118E196D0A1CFC46B677E85BF6B`.

| Nội dung | Disposition rev5 |
| --- | --- |
| OD-3=B | D-03 ghi quyết định trong chat: witness local single-host, rủi ro dư host rollback cần chấp nhận bằng văn bản trong approval M3. Token UNUSED có mặt, xóa/mất fail-closed; restore DB không mở cap. T0 đặc tả Windows, T12 thử throwaway sau approval; restore DB/host hủy authority. |
| P3-C a | Invariant send ⇒ ledger commit ⇒ witness consumed; bảng outcome có điều kiện không rollback. Sau DB restore, witness consumed + ledger vắng có thể đã gửi nên UNKNOWN; host rollback có thể làm UNUSED cũ không đáng tin. |
| P3-C b | T6/T8 phân loại known/UNKNOWN/NOT_SENT_*, giữ phase/status; UI không hiện NOT_SENT là lỗi provider, không retry, AC06. |
| P3-C c | T0 và owner path map ghi witness spec, Windows failure model/test plan và nội dung chấp nhận rủi ro. |

Rủi ro host rollback là residual risk được chọn cho draft, không phải proof bảo vệ rollback. Nếu lặp restore có thể phát sinh nhiều call có phí; chỉ synthetic data. Chưa có evidence thử Windows, witness, DB, Modal hoặc runtime. Approval không sửa.

## Static checks

| Kiểm tra | Kết quả thực tế |
| --- | --- |
| `python tools/validate_skeleton.py` qua venv backend worktree | `SKELETON_VALID`, exit 0 |
| `python tools/validate_repository_security.py` qua cùng venv | `REPOSITORY_SECURITY_VALID`, `publishable_files_scanned=5710`, exit 0 |
| `git diff --check` | Exit 0, không output |
| SHA-256 plan rev5 | `D457DC5DC2E75890E8ACC0BB59DA6C0F354BA118E196D0A1CFC46B677E85BF6B` |
| SHA-256 snapshot rev4 | `E109585296D9A937319C16EE2A0B7305D8577FE3E6A42B593A9877FE42385E7A` |
| SHA-256 approval | `71514E7F2BDA2AAE96374135FE6DE450F15816567191DBBF74B4F23EAA0B5A8B`, không đổi |
| `git status --short` | `M docs/context/SOURCE_REGISTER.md`, `M features/FEAT-063-system-architecture-rearchitecture/CONTEXT.md`, untracked Rev33 của FEAT-063, untracked feature FEAT-064; warning đọc global ignore bị từ chối. Các thay đổi Source Register/FEAT-063 đã có trước lượt rev5, hash hai file FEAT-063 không đổi. |
| Scoped `git status --short --untracked-files=all` | Không có mục `backend/src`, `apps` hoặc FEAT-061; approval FEAT-064 hiện untracked vì cả feature chưa tracked, hash không đổi. |

Không chạy lại harness; rev2 từng HARNESS_INVALID do evidence paths FEAT-043/063. Không chạy application test, witness, DB, backend, worker, Docker hay Modal. Không commit/push.
