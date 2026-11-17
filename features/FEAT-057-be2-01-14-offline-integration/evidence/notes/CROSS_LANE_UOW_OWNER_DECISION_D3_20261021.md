# FEAT-057 owner decision D3 — 2026-10-21

- Status: OWNER_DESIGN_DIRECTION_RECORDED / NOT IMPLEMENTATION APPROVAL.
- Source: direct owner message in the active conversation, reproduced below in plain text with code-markup removed; semantic text is preserved.
- Supersedes the PENDING status of C1/C2 in the D3 ballot as a design response. Historical ballot/spec/report bytes remain unchanged.
- Scope: update owning-card scope/CR drafts and the next review package only. No source, tests, schema, migrations, official approval, acceptance, runtime, or Git publication is granted here.

## Owner instruction

Chốt C1-A và C2-A. Khi ghi D3 và cập nhật scope/CR, vui lòng đưa vào các điều kiện sau:

**C1-A (hoãn budget bền)**

1. Trạng thái hoãn là dữ liệu bền do BE2-01 sở hữu. Job và run đều giữ QUEUED. Không thêm state video mới và không thêm giá trị vào JobState nếu tránh được. Nếu cần cột hoặc bảng mới thì viết CR schema/migration riêng cho BE2-01, không sửa migration đã publish.
2. _recover_unstarted và dispatch-loss không được tính thời gian hoãn là dispatch miss, không tiêu retry budget.
3. Giới hạn trên của thời gian hoãn dùng số do owner cung cấp sau. Chưa có thì ghi pending, không đặt giá trị.
4. Ba nhánh _dispatch_one, start_attempt, retry_job thuộc BE2-01 phải đổi: BUDGET_EXCEEDED thì hoãn, không cancel. Consent và kill switch vẫn cancel như cũ. BE2-14 chỉ cung cấp hợp đồng deny/defer, không tự cấp budget hay execution authority.
5. Không gọi provider khi đang hoãn. Hết hoãn thì chạy lại eligibility và reservation.
6. Ghi owner và CR chung BE2-01/BE2-14, đồng thời nêu rõ điểm kết thúc của trạng thái hoãn.

**C2-A (cleanup intent cùng commit B-stale)**

1. B-stale là boundary kiểu B: job SUCCEEDED + STALE kèm receipt, run sang stale terminal, không artifact, không ready-for-review, và intent ghi cùng một commit. BE2-01 đổi nhánh stale trong _decide_completion (hiện không ghi quarantine) thông qua CR của BE2-01.
2. Intent chỉ trỏ tới artifact_refs là descriptor của artifacts port BE1 do đúng job/attempt tạo. Không map được thì fail-closed. Cần owner artifacts BE1 xác nhận việc quarantine các ref đang nằm trong result_refs của một job SUCCEEDED, dùng reason code cố định và event_id deterministic.
3. Intent chỉ là “giữ private/dọn stage”, không xóa artifact accepted. Accepted vẫn thắng.
4. Vẫn phải có bảng phân loại đầu ra của _decide_completion sang boundary (accepted → B, failure → F, rejection → F-reject, stale → B-stale, tạm thời → không commit), và bảng cặp hợp lệ giữa (JobState, disposition) của job với state của run.
5. CR BE2-08 phải bao gồm model, codec, TERMINAL_STATES trong save(), _receipt, và các file domain/codec đang bị loại khỏi danh sách trong BE2-08 scope addendum.

Gói review tiếp theo cần gồm cả các điểm P3 còn lại: event_id

## Exact disposition and limits

C1-A is selected with the owner's additional requirement that BOTH job and VideoRun are QUEUED while budget-deferred. This supersedes the earlier proposal that retained FAILED_RETRYABLE during retry deferral. No budget-specific video/foundation state is introduced. The D2/C2 video terminal STALE state is unrelated to budget and remains required.

The next joint CR must elaborate the source transition from retry's current FAILED_RETRYABLE entry to one QUEUED job/run pair: only a due, otherwise authorized retry may perform its normal requeue once, atomically with the durable hold; repeated budget denial cannot allocate/finish more attempts or spend dispatch-loss recovery allowance. VideoRun attempt_id is cleared under D2; S alone binds. This is a D3-constrained candidate for independent review, not an implemented or separately approved source change. Normal retry cap/backoff/history are not bypassed.

The owner supplies the maximum defer duration later. Its numeric value is PENDING. Deadline action and reservation expiry/renewal remain explicit versioned-CR gates; no TTL, scheduler interval, cancellation/failure action, or budget amount is invented. Exit by verified resume and exit by genuine eligibility/owner cancellation are defined in the joint CR.

C2-A is selected: B-stale owns the authoritative stale job/receipt + video stale + durable private-stage intent commit. BE2-01 owns the _decide_completion stale-branch change; BE2-08 owns its state/codec/persistence/receipt/projection changes; BE1 artifacts ownership/adoption remains required. A proposed fixed source-existing reason code and deterministic event-id material are review candidates, not proof of BE1 approval.

The last owner sentence ends at “event_id”. The next review packet includes the complete P3 checklist from the preserved Claude rereview 3 rather than inventing additional owner conditions.

## Continuing gates

D1/D2 remain in force. Supplemental S/F approvals and exact implementation manifests remain pending. X01 PARTIAL; X05d BLOCKED; X05c/CR09-02 OPEN; X09-08 NOT_IMPLEMENTED. Budget unit/limit/max-defer duration are unprovided. No Modal, Lightning, provider, server, database, or runtime is run.
