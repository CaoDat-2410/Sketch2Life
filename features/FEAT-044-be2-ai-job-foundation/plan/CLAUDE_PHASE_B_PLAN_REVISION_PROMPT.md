# Claude — sửa plan Phase B revision 1 thành revision 2, chưa code

Mục tiêu: xử lý sáu nhóm PB-R01–PB-R06 trong `evidence/notes/PHASE_B_PLAN_CODEX_REVIEW_20261014.md`, để plan đủ cụ thể cho review/owner quyết định. Giữ sáu batch B1–B6 và roadmap14 card; không bắt đầu implementation.

## Nguồn và quyền

Làm trong worktree `.worktrees/be2-01-ai-job-foundation`, xác nhận branch `feature/be2-01-ai-job-foundation` và git status. Đọc AGENTS.md, project context/source register, FEAT-044 context/decisions/tracker/status/approval.

Đọc:
- PHASE_B_PLAN.md rev1, PHASE_B_ADR_PROPOSAL.md, PHASE_B_PORT_REVIEW.md.
- PHASE_B_PLAN_CODEX_REVIEW_20261014.md; final Phase A review/gate record.
- Current ports/services/fakes cần thiết cho sáu findings và canonical SRS B19.11/B22.1/B22.3/DATA-25/FIX-NFR-03.
- Primary PostgreSQL17 references và installed RQ source receipt được review dẫn chiếu nếu cần.

Approval hiện có chỉ Phase A. Lượt này là docs-only; không sửa backend/tests/runners/fixtures/dependencies, approved PLAN.md, TASK_APPROVAL.md, nguồn SRS/backlog hoặc governance.

## Sáu correction trong chính Phase B

| ID | Điều cần viết rõ ở revision2 | Acceptance cần bổ sung/làm cụ thể |
|---|---|---|
| PB-R01 | Job CAS chỉ bảo vệ AI rows. Đề xuất một protocol tối thiểu với owner để fence decision/epoch và định nghĩa điểm ordering/linearization; ghi exact port delta + P2 question/adoption gate. Không dùng precheck không fence hoặc SERIALIZABLE chỉ ở AI DB làm bằng chứng bảo vệ owner state | Owner consent/context/quarantine đổi giữa precheck và write, không tăng job_revision và không giao notice; stale decision không authorize acceptance/exposure. Tách proof theo assumed port contract với real owner integration |
| PB-R02 | Chốt xử lý session_id=NULL và canonical subject hash. Quy định unique conflict loser rollback toàn candidate UoW trước re-read/replay winner; không để ON CONFLICT DO NOTHING silently commit job/attempt/outbox dư | Parallel same key; different keys/same semantic; different payload; session null/non-null; đảo subject order; exact one job/attempt/dispatch/semantic row, correct per-key receipts, no orphan, restart |
| PB-R03 | Chốt receive/start/ack và recovery khi worker chết trước DB start commit. Chọn bounded transport retry hoặc SQL queued reconciliation cho SAME attempt; lease owner/generation phải fence mark/release. Chốt nguồn của same-claim recovery hoặc mô tả rõ output chưa commit mất/retry, không hứa phục hồi claim không được lưu | Kill sau broker receive trước durable start, restart tiến triển đúng attempt; old lease ack/release sau takeover; enqueue/mark crash, broker-down và output/completion crash windows |
| PB-R04 | List verifier/call-site changes để signed attempt được so với requested/claimed attempt, hoặc typed capability với scope check. Chốt issuer/service identity, issue/expiry/reissue và allowed replay/recovery behavior | Token attempt A không start/progress/complete B; wrong-job/tamper/expired denied; delayed queue/restart và historical replay có hành vi rõ |
| PB-R05 | Phân biệt accepted mutation+audit-intent transaction với rejection/conflict incident commit. Quy định audit-only/post-rollback path và failure behavior; stable event/message id interface delta. Quarantine intent rollback-safe | Conflict vẫn409, receipt/job immutable, durable redacted audit còn sau restart; audit redelivery dedup; DB failure không tạo accepted success thiếu audit intent, không delivery quarantine từ loser/rollback |
| PB-R06 | Notice phải phủ toàn scope. Chọn giữ all-match atomic query hoặc durable progress/cursor với COMPLETE sau khi hết pages; không giữ seen marker hoàn tất sau first limited page | >2 pages, duplicate notice, crash sau page1 rồi resume; mọi match được cancel, không reopen; concurrent create theo PB-R01 |

Không biến corrections thành features hoặc platform mới. Có thể dùng cách đơn giản giữ toàn bộ notice matches atomic thay vì thêm pagination engine nếu phù hợp scope. Các external owner semantics/secret/runtime decisions vẫn PROPOSED chờ owner; không implement BE1 để trả lời câu hỏi.

Đối với D3: chọn một preferred plan nhất quán. Nếu giữ PostgreSQL-only alternative, ghi rõ điều kiện phải chỉnh file map, G5/Q7 và broker-specific checks trước approval; không vừa chọn alternate vừa bắt buộc Redis. Không xây cả hai queue adapters trong scope này.

## Tài liệu và revision

1. Giữ bản rev1 tại `evidence/notes/PHASE_B_PLAN_REV1_ARCHIVE_20261014.md` trước khi thay plan. Không sửa review cũ hoặc receipts.
2. Cập nhật `plan/PHASE_B_PLAN.md` revision2, PLANNED/AWAITING_APPROVAL, implementation NOT_STARTED; companion ADR/port review đồng bộ references/deltas. Approved Phase A PLAN.md/approval giữ nguyên.
3. Phần §5 cần đủ mọi port/service/fake delta phát sinh từ protocol đã chọn; data model, crash matrix và B-01…B-12 phải đồng bộ. Giữ acceptance IDs hiện có, bổ sung subcases thay vì thêm business tasks.
4. Tạo `evidence/notes/PHASE_B_PLAN_REVISION_EVIDENCE.md`: mapping mỗi PB-R ID → vị trí đổi + acceptance + assumption/owner decision còn thiếu. Status của findings là ADDRESSED_PENDING_REVIEW, Claude không tự đóng independent review.
5. Cập nhật context/decisions/status/tracker/evidence index. ACTIVE Q00 vẫn chờ Phase A gates; Q01 plan rev2 prepared pending review, implementation NOT_STARTED/UNAPPROVED.

Làm xong phần docs độc lập trước khi báo cần owner quyết định. Không coi các câu hỏi chưa trả lời là lý do dừng trước khi có phương án PROPOSED reviewable.

## Kiểm tra và báo cáo

Run harness --feature, repository security và git diff --check; kiểm tra mọi source/test/runner/approved-plan/approval trong final Phase A snapshot giữ nguyên hash. Không chạy lại backend suite vì docs-only; không khởi động PostgreSQL/Redis, cài package, dùng cloud/upload source, gọi provider, commit/push/deploy hoặc liên hệ người khác.

Báo cáo tiếng Việt: sáu corrections đã đổi ở đâu, acceptance bổ sung, protocol/recovery được đề xuất, những quyết định owner còn thiếu và actual docs-check results. Kết thúc bằng plan rev2 chờ independent review/approval; không viết code Phase B hay mở BE2-02–14.
