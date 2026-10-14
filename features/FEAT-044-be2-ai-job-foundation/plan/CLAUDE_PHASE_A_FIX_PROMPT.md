# Prompt sửa lỗi Phase A sau review độc lập

> Historical prompt — 2026-10-14 final Q00 code review has CLOSED original R01–R11 and R03a/R04a/A18a. Do not redispatch this fix prompt. Follow BE2_EXECUTION_TRACKER.md for remaining adoption/Pillow acceptance gates. Original body retained as evidence.

- Date: 2026-10-14, Asia/Saigon.
- Purpose: ready-to-send remediation instruction for Claude; no code changed by this document.
- Scope: corrections to already-approved BE2-01 Phase A revision 1; no Phase B or new card activation.

```text
Claude tiếp tục BE2-01 Phase A trên worktree .worktrees/be2-01-ai-job-foundation,
branch feature/be2-01-ai-job-foundation, dựa trên approval Phase A revision 1 đã có.

Đọc plan/BE2_ROADMAP.md revision 2 và plan/BE2_EXECUTION_TRACKER.md trước khi chọn việc.
ACTIVE slot là Q00; chỉ sửa/đóng Phase A trong lượt này. Mọi next-step/scope phát sinh
đi qua roadmap/tracker, không mở card khác từ lời gợi ý trong tài liệu cũ.

Đọc AGENTS/context/source register và feature records hiện hành. Đọc review độc lập:
features/FEAT-044-be2-ai-job-foundation/evidence/notes/PHASE_A_CODEX_INDEPENDENT_REVIEW_20261014.md
và các raw/codex_review_* receipts/probes. Review result NEEDS_REVISION;
tests hiện có vẫn PASS nhưng chưa cover R01–R11.

Sửa R01–R10 và bổ sung consistency Child schema R11, với regression tests/fixtures
cho từng scenario. Ưu tiên R01 foreign quarantine, R02 scope dedup, R03 completion
receipt poisoning, R04 malformed failure→poll HTTP500, R05/R06 purge concurrency/replay.

Giữ accepted command/completion receipts immutable; không dùng "cho phép mọi completion
ghi đè" để sửa R03. Fake atomic claim/lock/CAS chỉ chứng minh fixture semantics,
không đưa DB/broker/provider runtime vào Phase A. Quarantine phải scope đúng organization
và valid job/attempt lineage cả ở rejection paths. Giữ unknown progress, human review,
authorization trước ETag/cache và live app isolation.

Ghi local candidate decisions cần thiết và cập nhật conformance/handoff/manifest cùng
implementation nếu contract thay đổi; adoption vẫn pending đúng owner. Giữ lịch sử
receipts/review, không xóa failures hoặc tự đổi độc lập review thành PASS.

Chạy tests/runner affected, targeted regressions và repository checks; dùng existing venv
với PYTHONPATH/MYPYPATH ghim worktree, không cài dependency. Lưu actual evidence riêng
trong feature/evidence, mapping R01–R11 fixed/not-fixed và A-01–A-20 revalidation.
Thiếu dependency ghi NOT_RUN/REQUIRES_LIGHTNINGAI_TEST; giữ live Pillow check pending
nếu môi trường vẫn thiếu.

Tiếp tục tự chủ trong phạm vi sửa lỗi Phase A đã duyệt, không xin xác nhận từng bước.
Không sửa unrelated Gradle/code, không triển khai Phase B/BE2-02–14, gọi provider thật,
commit/push/deploy. Báo cáo bằng tiếng Việt: repro trước/sau, code changes, test commands
actual results, unresolved findings/gates và files cần review lại. Sau sửa, để independent
reviewer verify closure; chưa đánh dấu full BE2-01 DONE.
```
