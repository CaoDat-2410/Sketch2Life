# Claude — ba correction còn lại trong Q00

> Historical prompt — 2026-10-14 final Q00 code review has CLOSED original R01–R11 and R03a/R04a/A18a. Do not redispatch this fix prompt. Follow BE2_EXECUTION_TRACKER.md for remaining adoption/Pillow acceptance gates. Original body retained as evidence.

- Scope: existing approved Phase A revision1; no new business card or Phase B.
- Latest review: evidence/notes/PHASE_A_Q00_CODEX_CLOSURE_REVIEW_20261014.md.

```text
Claude tiếp tục ACTIVE Q00 trên feature/be2-01-ai-job-foundation, worktree
.worktrees/be2-01-ai-job-foundation. Đọc AGENTS/context/register/approval,
BE2_ROADMAP.md revision2, BE2_EXECUTION_TRACKER.md và review mới:
features/FEAT-044-be2-ai-job-foundation/evidence/notes/PHASE_A_Q00_CODEX_CLOSURE_REVIEW_20261014.md.

11 repro gốc R01–R11 đã được reviewer xác nhận hết lỗi; giữ các fixes đó.
Lượt này chỉ sửa ba correction trong cùng Phase A đã duyệt:

1. R03a: completion bị temporary INVALID_STATE rồi được chấp nhận không được
   trả artifact vẫn đang quarantined. Xử lý nhất quán cả corrected INPUT_MISMATCH.
   Không blind-release unsafe/revoked/foreign output; giữ R01 lineage và accepted
   completion replay/conflict. Thêm assertions artifact availability ở positive
   corrected-completion tests.
2. R04a: failure_code list/dict làm allowlist lookup TypeError. Type-check trước
   lookup, trả safe PROVIDER_ERROR hoặc non-authoritative MALFORMED_CLAIM;
   kiểm later valid completion và diagnostic redaction.
3. A18a: gap có sẵn, cancel đọc state cũ rồi save sau purge làm mất DELETED/receipt.
   Dùng atomic scope boundary/CAS hiện có cho cancellation read/dispatch/save;
   test event-controlled cancel↔purge. Không thêm infra hay privacy feature.

Tái hiện trước/sau; thêm regression có ý nghĩa; cập nhật candidate spec/handoff
chỉ khi semantics/port affected. Giữ original review và mọi receipts. Ghi executor
FIXED_PENDING_REVIEW, không tự đóng independent review.

Chạy targeted corrections tests, current Phase A tests + planned regressions,
runner và applicable static/repository gates bằng existing environment, pinned
PYTHONPATH/MYPYPATH. Lưu evidence riêng. Thiếu Pillow/other dependency giữ NOT_RUN,
không cài mới hoặc claim PASS.

Không mở task mới/Phase B/BE2-02–14, provider/model live, legacy-wide refactor,
commit/push/deploy. Tiếp tục tự chủ trong exact Phase A corrections đã duyệt.
Kết thúc bằng bảng ba lỗi trước/sau, actual tests/commands, remaining gates và
files cần reviewer verify. Giữ ACTIVE Q00 và whole BE2-01 IN_PROGRESS.
```
