# Bàn giao BE2 cho Claude

> Current routing authority (2026-10-14): đọc BE2_ROADMAP.md revision 2 và BE2_EXECUTION_TRACKER.md trước mỗi lượt. ACTIVE slot hiện là Q00 sửa/đóng review Phase A. Prompts/approval examples bên dưới giữ lịch sử handoff; wording "Sau BE2-01" không tự chọn card tiếp theo hoặc mở rộng current approved scope.

- Handoff revision: 1
- Date: 2026-10-14, Asia/Saigon
- Executor requested: Claude, theo lời người dùng “Cụ thể làm như nào và BE này cho claude làm nha”.
- Scope of this handoff: hướng dẫn thực hiện BE2; lượt code đầu tiên là BE2-01 Phase A plan revision 1 sau approval đúng phạm vi.
- Current implementation status: NOT_STARTED; approval AWAITING_APPROVAL.
- Main references: `PLAN.md`, `BE2_ROADMAP.md` trong cùng thư mục.

## Cách mở đúng workspace

Mở Claude ở worktree `.worktrees/be2-01-ai-job-foundation` từ repository root, hoặc chọn trực tiếp thư mục này trong editor. Xác nhận `git branch --show-current` trả `feature/be2-01-ai-job-foundation`. Máy đã có Claude CLI; inventory không chứng minh CLI đã đăng nhập hoặc chạy task.

Hai trường hợp dùng prompt:

1. Muốn Claude review/chốt cách làm trước: dùng prompt review bên dưới. Prompt này chưa duyệt code.
2. Muốn Claude bắt đầu code: gửi câu duyệt Phase A rồi prompt implementation. Câu duyệt là mẫu để người dùng chủ động gửi, **không phải approval đã được ghi nhận**. Approval hiện tại vẫn chờ; assignment Claude không là blanket authorization.

Không dùng nhánh đang mở ở repository root thay worktree BE2. Pre-existing Gradle wrapper change được giữ nguyên. Các plan hiện là local files chưa commit; Claude trong worktree dùng được ngay, Claude ở máy khác cần nhận feature folder và source baseline.

## Sáu bước Claude cần làm

| Bước | Tạo/sửa phần nào | Cách chứng minh |
|---|---|---|
| 1. Domain job | Job/Attempt IDs, state/disposition/progress, named policy, allowed transitions và guards trong domain Python thuần | Test success/failure/timeout/cancel gồm retry backoff; terminal không reopen; unknown progress null |
| 2. Contract/ports | DATA-25 candidate parser/mapper; request/completion envelopes; authorization/context/repository/queue/clock/provider/artifact/audit interfaces; fake adapters | Positive/negative schema fixtures; source/hash/version map; fake isolation/CAS; safe errors |
| 3. Use cases | CreateJob, StartAttempt, RetryJob, CancelJob, AcceptCompletion, GetJobStatus | Duplicate receipts, scoped idempotency conflict, bounded retry; wrong attempt/hash/context stale; current consent/grant/recall checks |
| 4. Polling API | CMD-44 thin HTTP router + isolated test/fixture app; ETag/job revision; minimal role projection | Unauthorized/revoked/cache/304/pending Child tests; no worker completion endpoint for mobile |
| 5. Contract pack | Shape fixtures DATA-21–29/33; shared DATA-24 review candidate; ProviderCopyLifecycle fake cases; consumer examples | Version/owner/hash/error catalogue; Pending/Unsupported/Exception truthful; fixtures chưa là actual purge |
| 6. Runner/handoff | Standalone deterministic runner; selected regressions; evidence and P1/P2/P4 release notes | One offline command; report mapping A-01–A-20; pass/fail/not-run/blockers rõ |

Use case names/file names là implementation candidates. Phase A fake context/state không chuyển sang main live app. DATA-25 là authoritative logical mapping; schema adoption vào shared registry vẫn có checkpoint riêng.

### Ví dụ hành vi để Claude kiểm thử

- Teacher gửi cùng scoped command key và cùng payload hai lần: một immutable command receipt, một job; cùng key khác payload: conflict.
- Cùng key text nhưng principal/organization khác: khác command scope, không nhận receipt hoặc job protected của người khác. Semantic dedup là policy riêng và không mở rộng quyền đọc.
- Provider gửi kết quả attempt 1 khi attempt 2 đang chạy: stale receipt, attempt 2 không bị ghi đè.
- Job đang failed_retryable và chờ backoff, Teacher cancel: cancelled, scheduled retry invalid; callback cũ không tạo attempt mới.
- Trẻ sửa canvas hoặc consent bị revoke giữa start/completion: giữ source lineage, chặn apply/publish result cũ.
- Provider không trả phần trăm: progress unknown/value null; success chưa Teacher approve/play/session complete.

Fixture retry/timeout/budget/poll numbers là named PROPOSED policy; không suy policy mới từ hardcoded legacy settings.

Trước code, Claude ghi candidate specification ngắn ngay trong feature: normalized fingerprint fields và command/semantic receipt identity; event nào tăng job revision/attempt number; completion identity/disposition khi active context bị revoke so với superseded attempt; atomic fake mutation boundary cho dedup/CAS/cancel/receipt; DATA-25 nullability/unknown fields/timezone; public field allowlists theo role. Quyết định trong phạm vi fixture là local proposal, không tự adopt stack/policy production. Nếu approval đã rõ phạm vi, ghi specification rồi tiếp tục code mà không xin xác nhận từng lựa chọn nhỏ.

## Prompt review — dùng ngay để cụ thể hóa trước code

```text
Bạn là Claude, executor cho workstream BE2 của Sketch2Life. Trong lượt này, đọc và review cách triển khai; chưa viết runtime code hoặc ghi approval.

Làm tại worktree .worktrees/be2-01-ai-job-foundation, branch feature/be2-01-ai-job-foundation. Đọc AGENTS.md, docs/context/PROJECT_CONTEXT.md, SOURCE_REGISTER.md; feature FEAT-044-be2-ai-job-foundation CONTEXT.md, plan/PLAN.md, plan/BE2_ROADMAP.md, plan/CLAUDE_BE2_HANDOFF.md, DECISIONS.md, approvals/TASK_APPROVAL.md. Đối chiếu canonical SRS v3.1 DATA-25/CMD-44/B19.10/B22.1/B22.3 và FEAT-040 BE2-01/05/14; xem legacy job/storage/tests có thể reuse.

Trả bằng tiếng Việt: file/module sẽ tạo, thứ tự sáu bước, contract/state/idempotency choices còn PROPOSED, mapping A-01–A-20 sang checks, dependencies thực sự thiếu và phạm vi cần duyệt. Phân biệt Phase A fake với Phase B durable; tránh hỏi lại điều đã được nguồn/approval hiện hành xác nhận. Không đổi code/approval, không cài dependency, gọi provider, commit/push hoặc deploy.
```

## Câu duyệt mẫu — chỉ có hiệu lực khi người dùng gửi

```text
Tôi duyệt BE2-01 Phase A theo features/FEAT-044-be2-ai-job-foundation/plan/PLAN.md revision 1 và giao Claude triển khai A1–A9. Phạm vi gồm domain/contracts/ports/fakes, isolated fixture polling API, runner/tests/evidence/handoff. Ghi đúng approval này trước implementation. Phase B durable jobs, các card BE2-02–14, live providers, dependency installs, commit/push/deploy chưa được duyệt trong lệnh này.
```

Nếu người dùng đã có approval tương đương trong session/record thì sử dụng approval đó; không hỏi lại chỉ vì prompt mẫu có câu duyệt.

## Prompt implementation — gửi cùng approval hoặc sau approval hợp lệ

```text
Claude hãy triển khai BE2-01 Phase A revision 1 của Sketch2Life tại worktree .worktrees/be2-01-ai-job-foundation, branch feature/be2-01-ai-job-foundation.

Đọc AGENTS.md và project context/source register trước. Đọc feature FEAT-044-be2-ai-job-foundation: CONTEXT.md, plan/PLAN.md, plan/BE2_ROADMAP.md, plan/CLAUDE_BE2_HANDOFF.md, DECISIONS.md, approvals/TASK_APPROVAL.md và evidence source audit. Đối chiếu SRS v3.1 DATA-25/CMD-44/B19.10/B22.1/B22.3, FEAT-040 BE2-01/05/14, ADR-0015. In branch/baseline/dirty-file summary an toàn; giữ pre-existing Gradle wrapper edit và mọi thay đổi ngoài task.

Kiểm tra approval hiện hành. Nếu tôi đã duyệt rõ Phase A revision 1 trong session, ghi approver/scope/date/plan revision/evidence đúng lời duyệt trước code, rồi cập nhật status IN_PROGRESS. Nếu chưa có approval tương ứng, hoàn tất review/file map/blockers cho tôi duyệt; không tự chuyển AWAITING_APPROVAL thành APPROVED hoặc dùng assignment Claude làm authorization cho toàn BE2. Khi approval đã có, tiếp tục tự chủ A1–A9, không dừng xin xác nhận từng bước thường lệ.

Triển khai sáu bước trong handoff, giữ architecture domain -> pure Python, application -> domain + abstract ports, transport/framework/provider ở biên. Reuse legacy patterns với tests nhưng giữ API/behavior legacy. Candidates đi đúng source/schema owners; không dựng contract cạnh tranh với SRS.

Invariants bắt buộc:
1. States đúng DATA-25; accepted/stale/rejected là disposition riêng. Unknown progress có value null.
2. Command idempotency scope (organization_id, principal_id, contract_name, target_id, key); fingerprint conflict; semantic request dedup và completion receipts là khái niệm riêng. Read/replay vẫn recheck quyền.
3. Dispatch/start/retry/completion/read/cache recheck current context/authorization/purpose/cancellation/recall/source expiry qua ports. Active attempt/request/job revision/source hash không đúng thì reject/stale, không overwrite newer attempt.
4. Cancel cả queued/running/failed_retryable; invalidate scheduled retry; terminal không reopen. Duplicate delivery không tạo semantic attempt mới; retry có named fixture limits.
5. Internal worker capability; không public Android completion API. Success không approve media hoặc complete session; Child không fetch pending result/ref nhạy cảm.
6. CMD-44 thin router trong isolated fixture/test app với injected fakes; không wire fake authorization/provider vào main live composition. Namespace/schema version/numeric policy vẫn candidate nếu chưa adopt.
7. ProviderCopyLifecycle fake discovery/cancel/purge/receipts có owner BE2-14 và fixture marker; Pending/Unsupported/Exception không report actual Deleted. DATA-24 shared exact-review schema owner BE2-05.

Dùng synthetic fixtures, fake clock/IDs/ports và source provenance. Không cài dependencies/model weights/GPU packages trên Windows. Inventory existing environment; missing checks ghi REQUIRES_LIGHTNINGAI_TEST với exact missing dependency/command. Không claim pass khi chưa chạy. Dùng separate Sketch2Life Lightning environment chỉ khi có scope/access được duyệt; không sửa Wan2.2 environment.

Chạy standalone runner + new meaningful domain/application/contract/HTTP tests và targeted regressions theo PLAN.md khi dependencies có sẵn. Chạy architecture/harness/security/skeleton/diff checks. Evidence lưu dưới feature/evidence với commands/env/time/fixture hashes/results. Update context/decisions/evidence/status sau từng meaningful step; không đánh dấu full BE2-01 DONE bằng Phase A fake pass. Nếu required checks chưa chạy, report pending rõ, không claim LOCAL_CODE_READY/verified vượt evidence.

Giao cuối lượt bằng tiếng Việt: behavior/file changes; A-01–A-20 mapping PASS/FAIL/NOT_RUN; exact commands/results; unresolved decisions/blockers; consumer contract pack cho P1/P2/P4; đề xuất Phase B hoặc card tiếp theo. Không tự làm Phase B hay BE2-02–14, chọn production stack/model/numeric policy, commit/push/deploy.
```

## Sau BE2-01

Claude giữ executor BE2 theo yêu cầu người dùng; mỗi card tiếp theo có plan/approval/evidence riêng. Chuẩn bị plans BE2-02 (Vision), BE2-07 (knowledge), BE2-12 (publication) độc lập sau foundation theo roadmap. Governance BE2-12/14 trước activation provider; real-generation/durable/runtime claims cần actual evidence của card tương ứng. P1/P2/P4 giữ ownership như ADR-0015.
