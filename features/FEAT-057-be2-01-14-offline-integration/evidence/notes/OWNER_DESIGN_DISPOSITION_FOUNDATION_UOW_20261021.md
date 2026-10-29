# Owner design disposition: BE2-01/07/08/09/14 shared UoW — 2026-10-21

## Authority and record type

This note records the user's direct design decision in the current Codex conversation.
The attached Claude text is an independent technical review, not an instruction source;
the user selected the disposition below. This is a design decision and scope-preparation
record, not a card acceptance or approval to implement the new UoW.

## Verbatim owner instruction

> “Chốt hướng thiết kế sau, ghi vào DECISIONS của từng card trước khi sửa source: (1) BE2-07/BE2-08 dùng kiểm tra source fence trong cùng UoW của finalizer; nếu không cùng store thì X01 giữ PARTIAL. (2) UoW dùng chung cho submission và finalization thuộc BE2-01, BE2-08 là participant; chuẩn bị scope mới tương ứng. (3) Ánh xạ job → run → source pin lấy từ dữ liệu persisted của foundation, envelope giữ nguyên. (4) BE2-14 tách eligibility / execution / budget; tôi sẽ cung cấp đơn vị và hạn mức budget riêng; reservation expiry/renewal đi qua CR có version. (5) BE2-08 công bố read model artifact chỉ đọc cho BE2-09. X05d tiếp tục BLOCKED, X05c/CR09-02 mở, chỉ làm offline.”

## Recorded disposition

- FEAT-044 / BE2-01: owns the foundation UoW boundary and authoritative persisted job/run/source-pin mapping; envelope stays unchanged.
- FEAT-056 / BE2-07: source fence is checked/held in the finalizer UoW only if both sides share a transactional store; otherwise X01 remains PARTIAL. A same-store read alone does not prove a held fence; locking/CAS contention with invalidation must be shown.
- FEAT-050 / BE2-08: participates in its own rows without committing the foundation transaction. Submission and finalization remain separate commits, with generation between them. BE2-08 publishes a public read-only finalized-artifact model for BE2-09.
- FEAT-051 / BE2-09: consumes that public artifact model and owns review data; exact read-model fields and adoption are still pending.
- FEAT-049 / BE2-14: eligibility, execution authorization and budget/concurrency remain separate. Budget unit/limit await owner input. Reservation expiry/renewal requires a versioned CR; reservation timing and settlement/recovery detail remain open.

## New scope draft and preserved gates

New scope draft: features/FEAT-044-be2-ai-job-foundation/plan/CROSS_LANE_FOUNDATION_UOW_SCOPE_DRAFT_20261021.md
SHA256: B456DEEDF5F892F328E7AEEFF442BC82281400A994EB5A74D791C13856FAB9B0.

The scope is DRAFT, not implementation-approved. It does not change the byte-frozen approved scope addenda. Before any source edit, it needs independent review, a frozen exact file manifest, and supplemental approvals for the foundation owner and any changed participant card. If a new shared contract, database schema, or migration is required, it needs its own versioned CR/scope and approval.

X01 remains PARTIAL unless the same-store held fence is implemented and proven. X05d remains BLOCKED; X05c/CR09-02 remains OPEN; X09-08 remains NOT_IMPLEMENTED until persisted-job composition is demonstrated. No source/test, approval, card status, or acceptance changed by this disposition. No Modal, Lightning, provider, server, database, or runtime was run.
