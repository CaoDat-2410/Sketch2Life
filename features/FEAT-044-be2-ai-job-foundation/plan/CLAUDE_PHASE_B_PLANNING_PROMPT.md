# Claude — lập plan BE2-01 Phase B, chưa triển khai

Mục tiêu lượt này: chuẩn bị plan Phase B có phạm vi nhỏ, tiêu chí kiểm chứng cụ thể và quyết định cần owner chốt. Chỉ đọc code và viết tài liệu trong FEAT-044. Có thể chuẩn bị plan khi Q00 đang chờ review/environment; không coi việc lập plan là nghiệm thu Phase A hoặc kích hoạt Q01 implementation.

## Nguồn bắt buộc

Trong worktree `.worktrees/be2-01-ai-job-foundation`, kiểm tra branch `feature/be2-01-ai-job-foundation` và git status; giữ mọi thay đổi ngoài task.

Đọc:
- AGENTS.md, docs/context/PROJECT_CONTEXT.md và SOURCE_REGISTER.md.
- FEAT-040 artifacts/TEAM_TASK_BREAKDOWN.md: BE2-01, ownership P2/P3/P4, H-OPERATIONS, dependency rules.
- Canonical SRS v3.1: DATA-25, CMD-44, B19.10/B19.11/B22.3 và scope/receipt/recovery quy tắc liên quan.
- ADR-0014/0015 và ADR hiện hành liên quan runtime/persistence.
- FEAT-044 CONTEXT/DECISIONS, approved plan/PLAN.md revision1, approvals/TASK_APPROVAL.md.
- plan/BE2_ROADMAP.md revision2, BE2_EXECUTION_TRACKER.md.
- evidence/notes/PHASE_A_Q00_FINAL_CODE_REVIEW_20261014.md, PHASE_A_HANDOFF.md, PHASE_A_ACCEPTANCE_GATE_RECORD.md và latest gate-delivery review nếu có.
- Domain/ports/service/fakes/test AI jobs hiện tại; backend dependency/config/migration/queue structure và generic persistence port BE1 nếu đã có.

Phase A approval không duyệt Phase B. Chưa có consumer decisions thì giữ PENDING; các adoption/stack choices chưa ghi nhận vẫn PROPOSED. Package xuất hiện trong pyproject hoặc legacy code không tự là ADR được adopt.

## Đầu ra: ba tài liệu nhỏ

Tạo trong `features/FEAT-044-be2-ai-job-foundation/plan/`:
1. `PHASE_B_PLAN.md`: revision1, PLANNED/AWAITING_APPROVAL; problem/result, exact outputs/file map, allowed changes/exclusions, source mapping, sáu batch dưới đây và acceptance/evidence.
2. `PHASE_B_ADR_PROPOSAL.md`: PROPOSED; chỉ các quyết định đang chặn durable AI job. Dùng lại stack/ports đã được adopt nếu có. Nếu chưa, một đề xuất ưu tiên với tradeoff cụ thể, phương án thay thế khi cần; không lựa chọn provider/model hoặc nghiên cứu stack không giới hạn.
3. `PHASE_B_PORT_REVIEW.md`: bảng P2/P3/P4 với interface/version hiện có, transaction/delivery semantics cần, compatibility delta, thiếu gì, câu hỏi owner và bằng chứng/decision nếu có.

Không tạo approval hoặc sửa approved PLAN.md/TASK_APPROVAL.md. Khi plan cụ thể đã review xong, owner duyệt Phase B bằng record riêng tham chiếu đúng file/revision; chuẩn bị được lời duyệt mẫu, nhưng mẫu không là approval.

## Sáu batch dự kiến, chưa code

| Batch | Scope cần mô tả | Exit/evidence dự kiến |
|---|---|---|
| B1 | Chốt thiết kế tối thiểu: DB/queue, unit-of-work, uniqueness/CAS, dispatch/ack recovery, worker identity; P2/P4 review ports | ADR/port decisions adopted trước implementation; sơ đồ transaction/failure points |
| B2 | AI-owned durable storage/migrations cho job/attempt, command/semantic/completion receipts, notices và outbox cần thiết | Fresh/existing schema migration, constraints/version preservation; restart còn đủ dữ liệu |
| B3 | Implement repository/unit-of-work adapter, CAS và immutable replay semantics theo ports | Actual DB tests: same-key same payload replay; changed payload conflict; semantic scope isolation; atomic rollback; concurrent one winner |
| B4 | Transactional outbox + selected queue adapter/dispatcher và bounded retry/ack recovery | Broker down vẫn recoverable; publish/crash/replay; duplicate delivery cùng attempt, không thêm semantic attempt |
| B5 | Durable worker/completion recovery và current cancellation/revocation/eligibility guards | Restart sau output/receipt; old attempt không overwrite; late output sau cancel/revoke không expose |
| B6 | Adapter conformance + restart/concurrency/fault evidence + handoff | Scoped real runtime receipts và regression/review; remaining integration/provider gates ghi riêng |

Tách transaction commit với external queue/artifact/audit side effects. Nêu crash windows và recoverability, không hứa exactly-once provider execution chỉ dựa queue acknowledgement. Nếu ports/service cần sửa tối thiểu cho adapter, liệt kê exact behavior, lý do và tests; không refactor toàn backend.

P3 giữ implementation durable AI jobs. P2 giữ generic persistence/auth/artifact authority; P4 giữ composition/live wiring theo task được duyệt. Không ghi DB của BE1, không chuyển toàn durable adapter sang P2/P4.

## Acceptance Phase B phải kiểm chứng được

Map các acceptance này về source và command/fixture/environment dự kiến, không ghi PASS:
- Restart sau commit giữ job/request/attempt revisions, receipts/fingerprints và outbox.
- Broker down không mất job; dispatcher replay không sinh semantic attempt mới.
- Same command key/payload replay và conflict khác payload đúng scope kể cả concurrent/process restart.
- Same-attempt redelivery được dedup; retry được phép mới tạo attempt tiếp theo.
- Concurrent completion chỉ một authoritative outcome/receipt; identical replay trả cùng result, conflicting completion không overwrite.
- Crash/replay quanh dispatch/output/persist bảo toàn identity, fingerprint, disposition và provenance; nêu external effects reconciliation.
- Cancel/revoke/recall/context-change race không reopen hoặc expose result cũ; check current authority trước read/cache/completion.
- Durable outbox/receipt/CAS và transaction rollback được kiểm tra trên adapter thật, không dùng fake pass thay runtime evidence.
- Migration/conformance/report và regression cho Phase A semantics đã được review; ghi check nào cần LightningAI.
- Namespace/live router/provider inference/actual copy deletion chưa được scope này chứng minh; integration handoff owner/remaining gates rõ.

Môi trường đề xuất phục vụ DB/queue tests phải riêng, synthetic-only. Lượt planning không cài package, khởi động DB/broker/container, chạy cloud, upload source hay gọi provider. Không dùng Wan2.2 environment.

## Gate và điểm dừng

Q00 vẫn ACTIVE nếu Phase A chưa có decision/disposition hợp lệ; Q01 chỉ ghi PLAN_PREPARATION, implementation NOT_STARTED/UNAPPROVED. Không đổi thứ tự 14 card hoặc tạo business task mới.

Trước Phase B code cần:
- Phase A checkpoint disposition hợp lệ, với remaining production adoption rõ.
- Plan B cụ thể + independent review + explicit approval đúng revision.
- Runtime/persistence/queue/transaction/recovery/service-identity ADR phù hợp và BE1 generic ports được adopt.
- Môi trường thực thi được phép dùng và kiểm tra đủ dependencies, không suy từ local fake tests.

Nếu owner decisions thiếu, hoàn tất các tài liệu độc lập và báo danh sách nhỏ cần quyết định; không dừng trước khi có bản plan reviewable. Không tự ghi acceptance/adoption, không liên hệ người khác.

Cập nhật FEAT-044 context/decisions/status/tracker/evidence index cho bước planning; giữ nguyên runtime/source/approval. Chạy harness --feature, repository security và git diff --check. Chỉ ghi actual docs-check results; không chạy lại backend suite vì docs-only.

Báo cáo tiếng Việt: sáu batch, file map, acceptance/source mapping, đề xuất ADR, câu hỏi P2/P4/owner và gates trước code. Kết thúc ở PLANNED/AWAITING_APPROVAL; chưa triển khai Phase B hoặc BE2-02–14, chưa commit/push/deploy.
