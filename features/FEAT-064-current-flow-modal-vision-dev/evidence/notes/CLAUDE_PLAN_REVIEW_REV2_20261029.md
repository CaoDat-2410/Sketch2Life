# Claude review rev1 → plan rev2 — 2026-10-29

## Nguồn và authority

Chủ task dán kết quả Claude review đúng plan rev1 SHA-256 `B563BEB6552AADB4B2658BE8DE3806CE1DF401DAF5BF96D38D413DF56246155A`, verdict **NEEDS_REVISION**, 0 P1 / 3 P2 / 4 P3. Review đề nghị sửa tài liệu trước khi chốt OD-1–OD-4. Không diễn giải review, technical PASS hoặc yêu cầu lập plan thành implementation/DB/provider approval.

Rev1 nguyên bytes được giữ tại `PLAN_REV1_REVIEWED_20261029.md`; SHA-256 snapshot khớp hash Claude đã review. Active plan là `../../plan/PLAN.md`, revision **2**, vẫn DRAFT / NOT_STARTED:

`F321EE9FECF0870D52CC25B50F51B510F8046938A6D9AB99F188534DB9C7290F`

`../../approvals/TASK_APPROVAL.md` không sửa; hash vẫn `71514E7F2BDA2AAE96374135FE6DE450F15816567191DBBF74B4F23EAA0B5A8B`, AWAITING_APPROVAL, approver/scope trống.

## Đối chiếu và disposition

| Finding Claude | Kết luận đối chiếu | Sửa trong rev2 |
| --- | --- | --- |
| F1 P2 — consent inventory/NOT NULL | Đúng là thiếu chi tiết call-site/representation, không thiếu invariant synthetic riêng ở rev1. NOT NULL chỉ là string constraint; API mới đòi effective record. Registry :276 là list_profiles, không phải enrollment | Inventory mới, T0/T1/AC17, OD-2, owner map registry/session/common/records; chưa chọn representation hoặc sửa real constraints |
| F2 P2 — retry policy | Default job có 3 attempts và timeout sweep/recovery; adapter OSError retryable nhưng không có retry loop riêng | Pilot max_attempts=1 + reviewed deadlines; duplicate/recovery không send; known typed failure khác possible-send UNKNOWN; invocation cap/outcome tách A1 started-attempt consumed accounting |
| F3 P2 — durable stores/fence | Assistance/analysis chỉ in-memory, owner fence SQL test-only. Rev1 đã dự kiến minimal durable state và T7=L; không thể suy ra phải triển khai toàn bộ persistence của BE2 | T7a selected-state repositories/migration, T7b owner-signed fence/UoW, T7c run ledger; freeze inventory/version/manifests và review riêng, không full BE2 adoption |
| F4 P3 — run authority | Cần quy định issuance, approval/expiry, DB identity/reset và scope xuyên session/canvas/IDs | Server/operator-issued run ngoài client API, monotonic cap; missing/mismatched/lost/rolled-back ledger hủy live authority; preserving migration không reset/cấp lượt |
| F5 P3 — status sau turn | Rủi ro nếu dùng shared write guard, chưa phải bug endpoint đã tồn tại/chạy. Grant/membership đơn thuần không đủ quyền đọc | T2/T9/T10/AC05/19, read auth riêng vẫn kiểm tra grant/identity/request scope/eligibility/revoke; pause/closed turn có disposition, unavailable không giả provider failure hoặc resubmit |
| F6 P3 — visual gate/Teacher panel | Prototype Teacher có nút chỉnh/duyệt Sketch; không phù hợp làm màn read-only analysis bằng đổi nhãn | Panel/component/route riêng chốt T0; T3/T10/T11/AC20 và assets record dùng components/style có sẵn, asset/visual mới qua AGENTS generated/provenance/approval/approved/applied |
| F7 P3 — classroom fence terminology | Baseline có classroom/demo composition, chưa có Rev33 retirement fence; khác owner fence BE2 | Runtime classroom opt-in, không demo/combined, không dependency ngầm S1 Rev33; owner fence là contract riêng |

Source facts/locators được bổ sung vào `SOURCE_REVIEW_20261029.md`. Hai reviewer độc lập đối chiếu F1/F5 và F2/F3/F4, rồi rà delta: không còn material finding trong phạm vi đó. Một nhãn list_profiles đã được sửa. Đây không phải Claude review PASS cho rev2, không kiểm chứng runtime và không cấp approval.

## Giữ phạm vi

Luồng Child UI/BE1 hiện tại → source/render/admission → BE2 → Qwen → Teacher unconfirmed/pending. Không Parent/Teacher mới, không full BE2 adoption, không Sketch/correction/delivery hoặc ASR/SAM/video/Pixi. OD-1–OD-4, owner-signed contract/ADR, manifests/migration ownership và authority cho từng task còn chờ chốt.

Chỉ sửa planning/context/evidence/status và cập nhật bàn giao local. Không sửa runtime source, migrations hoặc approval; không cài package, chạy test ứng dụng, DB, service, worker hay Modal; không commit/push. FEAT-063 concurrent docs và protected FEAT-061 plan/approval giữ nguyên.

## Kiểm chứng

Static checks chạy trên dev worktree, không dùng thay cho application/DB/UI/live evidence:

| Kiểm tra | Kết quả thực tế |
| --- | --- |
| `validate_skeleton.py` | `SKELETON_VALID` |
| `validate_repository_security.py` | `REPOSITORY_SECURITY_VALID`, 5703 publishable files tại thời điểm quét |
| `validate_harness.py --feature features/FEAT-064-current-flow-modal-vision-dev` | `HARNESS_INVALID`: thiếu evidence paths ở FEAT-043 và FEAT-063; không báo lỗi FEAT-064 |
| `git diff --check` | Exit 0, không báo lỗi |
| `git diff --name-only -- backend/src apps` | Exit 0, không có tracked source/UI diff trong dev worktree |
| Handoff Claude local | `git check-ignore` xác nhận entry trong `.git/info/exclude`; không stage/push |

Lệnh kiểm tra ignore đầu tiên bị Git từ chối do ownership của sandbox; đọc lại thành công bằng `git -c safe.directory=...` chỉ cho lệnh đó, không đổi Git config. FEAT-063 context/Rev33 và FEAT-061 plan/approval hashes trước/sau không đổi. Source/UI diff check chỉ phản ánh tracked changes; không tuyên bố kiểm tra mọi untracked file bằng lệnh đó.

## Bước kế tiếp

Rà delta rev2, chốt OD-1–OD-4 và M0 owners/manifests, rồi chủ task mới duyệt đúng scope/revision/hash. Modal giữ ở checkpoint đã dừng; chỉ cần khởi động recipe hiện có khi M1/M2 CPU đạt và M3 mới được duyệt, tối đa một live call mới. Không phải tạo catalog Endpoint hay tải lại model/Volume/Secret từ việc sửa plan.
