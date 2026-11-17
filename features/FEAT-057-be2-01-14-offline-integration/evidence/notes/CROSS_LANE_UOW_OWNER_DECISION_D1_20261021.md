# Owner decision D1 — paired BE2-01 / BE2-08 lifecycle UoW

- Status: OWNER DESIGN DIRECTION DECIDED / INDEPENDENT REVIEW REQUIRED
- Date: 2026-10-21 (Asia/Saigon)
- Scope successor: `features/FEAT-044-be2-ai-job-foundation/plan/CROSS_LANE_FOUNDATION_UOW_SCOPE_REV3_DRAFT_20261021.md`
- Scope SHA256: `507EF55787A36EAE2E75E1BBACD8EBDD8DA8A5ED68DB190974289D88C7666C56`
- This decision is not implementation approval.

## Owner disposition

The owner selected **A** and added these binding design conditions:

1. BE2-01 owns and opens the UoW for start, retry, fail, cancel and timeout, as well as submission and successful finalization. Reconciler retry/timeout/cancel transitions also go through the BE2-01 UoW with a BE2-08 video participant. A reconciler or outbox dispatcher may not update a foundation job while bypassing its paired video run.
2. BE2-08 is a non-committing participant. It may mutate only BE2-08 video rows (start, retry with a new attempt, fail, cancel, timeout). It may not begin, commit or roll back the enclosing UoW.
3. If finalization is rejected, persist the quarantine/cleanup intent in a separately committed **reject** boundary through the existing foundation quarantine-intent path. Never rely on rollback to preserve an intent. Rollback of successful finalization is reserved for infrastructure errors and must have an explicit recovery path.
4. Use one lock order for foundation job, video run and source-fence rows, including failure/cancel paths, to avoid deadlock with finalization. The selected scope order is: job row → video-run row → source-fence rows in stable canonical-key order. Claude must check it against all actual lock paths. Placement of a transaction-held creation-lease row remains for CR08-01 review; if it is separate, do not claim it is atomic.
5. The lifecycle matrix must include A (submit), S (start), B (successful finalize), and F (fail/cancel/timeout/retry/reject). Each row must identify UoW owner/callers, enlisted rows, the paired job/run CAS, and its recovery point.

Verbatim owner instruction:

> Chốt: A.
>
> BE2-01 giữ quyền mở UoW cho cả start, retry, fail, cancel và timeout. BE2-08 chỉ cập nhật các row video của mình. Chọn A kèm các điều kiện sau, hãy đưa vào bản scope sửa:
>
> Retry, timeout và cancel của reconciler cũng đi qua UoW của BE2-01, có participant video. Không để reconciler hay outbox dispatcher cập nhật job mà bỏ qua run.
> Participant video chỉ có thao tác trên hàng video của BE2-08 (start, retry với attempt mới, fail, cancel, timeout). Participant không được begin, commit hay rollback UoW.
> Finalization bị từ chối thì lưu quarantine/cleanup intent bằng một commit “reject” riêng, dùng đường quarantine intent có sẵn của foundation. Không dựa vào rollback để giữ intent. Rollback của finalization chỉ dành cho lỗi hạ tầng và phải có đường recovery.
> Chốt một thứ tự khoá thống nhất cho hàng job, hàng run và hàng fence, áp dụng cho cả đường fail/cancel, để tránh deadlock với finalization.
> Thêm bảng boundary A (submit) / S (start) / B (finalize thành công) / F (fail, cancel, timeout, retry, reject). Mỗi dòng ghi owner, các hàng được enlist, cặp CAS job/run và điểm recovery.
>
> Giữ nguyên các điểm sau:
>
> Việc thêm boundary S và F vẫn cần review và supplemental approval riêng. Quyết định này chưa phải approval để code.
> X01 giữ PARTIAL, X05d giữ BLOCKED, X05c/CR09-02 giữ mở.
> Budget unit/limit tôi sẽ cung cấp sau, chưa suy đoán giá trị nào.
> Chỉ làm offline. Chưa chạy Modal, Lightning, provider hay runtime.

## Boundaries unchanged by this decision

- X01 remains `PARTIAL`; current BE2-07 scope does not provide the required durable shared-store source fence.
- X05d remains `BLOCKED`.
- X05c / CR09-02 remains open.
- BE2-14 budget unit and limit remain unprovided; do not invent numeric values. Reservation expiry/renewal remains a versioned-CR gate.
- The FEAT-057 slice plan revision 4 is not silently amended. It predates D1 and still describes S/F as pending; the independent reviewer must identify whether a successor plan revision or another erratum is required and list the exact clauses to align.
- Independent review and separate supplemental approval for S/F and affected implementation scopes are still required. No implementation, acceptance, publication or runtime approval is given.
- Offline documentation only for this step. No Modal, Lightning, provider, server, database or runtime execution.

The original ballot `CROSS_LANE_UOW_OWNER_DECISION_20261021.md` is preserved as the historical request for D1. This note records the owner's answer and supersedes its `AWAITING_OWNER_DECISION` status without changing the original bytes.
