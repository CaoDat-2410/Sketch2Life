# Claude — bổ sung hai nhóm contract của plan Phase B, chưa code

Lượt này chỉ làm PB-C01 và PB-C02 trong `evidence/notes/PHASE_B_REV2_CLOSURE_REVIEW_20261015.md`. Sáu finding gốc PB-R01–PB-R06 đã CLOSED_ORIGINAL_PLAN_CASE ở mức thiết kế. Giữ B1–B6, B-01…B-12 và 14 card; không mở rộng task.

Làm tại worktree `.worktrees/be2-01-ai-job-foundation`, branch `feature/be2-01-ai-job-foundation`. Đọc AGENTS.md, project context/source register, FEAT-044 CONTEXT/DECISIONS/tracker/status/approval, ba tài liệu Phase B rev2 và closure review mới.

## 1. PB-C01 — transition dispatch-loss khi queued

Giữ cơ chế D5/Δ7 đã chọn. Ghi rõ một pure domain transition riêng cho queued khi DISPATCH_MAX hết:
- Chỉ dành cho dispatch-loss nội bộ, không mở generic provider-failure từ mọi state.
- started_at vẫn None; ghi finish/outcome/history/revision, giữ pinned request và provenance.
- Còn retry budget → failed_retryable + existing backoff; hết → failed_exhausted, không schedule/reopen.
- CAS cạnh tranh với start_attempt bảo vệ một winner; reconciler không overwrite job đã running/completed.
- Republish trước khi vượt bound không tạo attempt mới.

Đưa `domain/ai_jobs/model.py` cùng các delta service/fake/tests cần thiết vào allowed outputs/file map/§5. Đồng bộ câu “No other domain/contract change” với phạm vi này. Bổ sung các subcase trên vào B-04b, không thêm acceptance ID/card.

## 2. PB-C02 — carrier capability và quarantine event_id

Chọn và ghi một interface cụ thể cho từng đường truyền:
- Queue: transient WorkerDispatchEnvelope(message, capability) hoặc enqueue(message, capability=...), với issuer/adapter/worker call contract rõ. Persisted DispatchMessage/outbox/receipts/logs vẫn token-free. Map exact queue port + fake/worker compatibility delta.
- Quarantine: QuarantineIntent(event_id, refs, reason) hoặc event_id argument/envelope. Map exact ArtifactPort + fake/sink delta. Dispatcher giao đúng event_id của outbox, giữ nguyên khi redelivery.

B-05e/B-10c kiểm tra token đến worker qua broker và không vào SQL/receipt/log. B-06c/d kiểm tra crash sau quarantine effect trước ack, rồi replay idempotent bằng cùng event_id, giữ owned-lineage/rollback guards.

Đổi wording Δ9 thành “authoritative settlement” cho mọi completion thật sự đổi job (gồm unsafe/stale/rejected disposition); “non-authoritative rejection/conflict” mới dùng audit-only path. Không thay cơ chế audit đã đóng.

## 3. Đầu ra và điểm dừng

- Lưu rev2 plan nguyên byte tại `evidence/notes/PHASE_B_PLAN_REV2_ARCHIVE_20261015.md`; preserve rev1/reviews/receipts.
- Cập nhật PHASE_B_PLAN.md thành revision3; companion ADR/port review đồng bộ references/deltas. Status PLANNED/AWAITING_APPROVAL, implementation NOT_STARTED.
- Tạo `evidence/notes/PHASE_B_PLAN_REV3_EVIDENCE.md`: PB-C01/C02 → vị trí đổi/acceptance, status ADDRESSED_PENDING_REVIEW; không tự đóng independent review.
- Update context/decisions/status/tracker/index cho bước docs. ACTIVE Q00 vẫn chờ Phase A disposition; Q01 implementation NOT_STARTED/UNAPPROVED. D1–D7/Q1–Q8/policy/env choices vẫn PROPOSED/PENDING, không tạo sign-off.
- Chạy harness --feature, repository security, git diff --check; so hash24 source/test/runner/approved Phase A plan/approval giữ nguyên. Không chạy backend suite vì docs-only.

Không sửa backend/tests/fixtures/runners/dependencies, approved PLAN.md/TASK_APPROVAL.md, SRS/backlog/governance; không cài package/start services/cloud/provider/upload/commit/push/deploy hoặc liên hệ người khác.

Báo cáo tiếng Việt: hai correction đã đổi đâu, exact interface/transition được đề xuất, acceptance bổ sung, actual docs-check results và owner gates còn thiếu. Lượt này chỉ chuẩn bị rev3 để review; chưa triển khai code.
