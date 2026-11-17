# Task approval

- Status: APPROVED
- Approver: user (project/task owner), direct instruction in the Claude session
- Approved scope: BE2-01 Phase A per `plan/PLAN.md` revision 1, steps A1–A9 only: domain job/attempt and lifecycle; DATA-25, contracts, ports and fake adapters; create/retry/cancel/completion with dedup and stale guards; CMD-44 in isolated fixture/test app; synthetic fixtures, standalone runner, tests, evidence and handoff. Six handoff steps and A-01..A-20 cross-check required.
- Plan revision: 1
- Approved at: 2026-10-14, Asia/Saigon; recorded 2026-10-14 20:43 +07:00 before implementation
- Worktree/branch: `.worktrees/be2-01-ai-job-foundation`, `feature/be2-01-ai-job-foundation`
- Baseline: `b9204d8c9eb4f8a1ee6d4db4de5ee23672e0392c`
- Executor: Claude
- Excluded: Phase B, BE2-02..BE2-14, real provider calls, dependency installation, commit/push/deploy. Unrelated working-tree changes (pre-existing Gradle wrapper edit) preserved.
- Missing-dependency rule: record `REQUIRES_LIGHTNINGAI_TEST` with the exact unrun command, continue independent work; no pass claim or DONE without evidence.
- Notes: routine steps within scope proceed without re-confirmation. Approval does not adopt production stack, schema registry entries or numeric policy.

## Approval evidence (verbatim)

```text
Tôi duyệt BE2-01 Phase A theo
features/FEAT-044-be2-ai-job-foundation/plan/PLAN.md revision 1
và giao Claude triển khai A1–A9 ngay.

Làm trong worktree:
D:\GitHub\Sketch2Life\.worktrees\be2-01-ai-job-foundation
Nhánh: feature/be2-01-ai-job-foundation.

Đọc AGENTS.md, các nguồn và prompt implementation trong
features/FEAT-044-be2-ai-job-foundation/plan/CLAUDE_BE2_HANDOFF.md.

Ghi approval đúng phạm vi và nguyên văn lệnh này vào
approvals/TASK_APPROVAL.md trước khi code, rồi cập nhật IN_PROGRESS.

Phạm vi được duyệt:
- Domain job/attempt và lifecycle.
- DATA-25, contracts, ports và fake adapters.
- Create/retry/cancel/completion với dedup và stale guards.
- CMD-44 trong isolated fixture/test app.
- Synthetic fixtures, standalone runner, tests, evidence và handoff.

Thực hiện đủ sáu bước trong bàn giao và đối chiếu A-01 đến A-20.
Tiếp tục tự chủ trong phạm vi đã duyệt, không hỏi lại từng bước thường lệ.

Giữ nguyên thay đổi ngoài task. Không triển khai Phase B,
BE2-02–14, gọi provider thật, cài dependency, commit/push/deploy.

Nếu thiếu dependency, ghi REQUIRES_LIGHTNINGAI_TEST cùng lệnh
chưa chạy và tiếp tục phần độc lập làm được. Không báo test pass
hoặc đánh dấu DONE khi chưa đủ evidence.

Báo cáo cuối bằng tiếng Việt: thay đổi, kết quả từng tiêu chí,
lệnh kiểm tra thực tế, blockers và đầu ra bàn giao.
```
