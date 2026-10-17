# C3c3 accounting — invariants before atomic SQL/application integration

Approved P3. No money/credit/time-window/TTL default or provider estimate chosen.
Current trusted budget definition supplies unit, opaque window identity, exact
definition refs, ceiling, concurrency ceiling and estimate for exact held request
pin/attempt. Reference syntax alone does not adopt values. Missing verified quote
fails closed; current-use lease still required before reserve/dispatch.

First coherent step is pure domain plus exact quote/settlement ports/contracts:
budget held/spent counters are scoped by org/feature/definition/unit/window;
occupied concurrency slots are GLOBAL to org/feature across definition/window
changes, never reset by creating a new budget bucket. SQL adapter must load these
separate counters atomically and persist deltas with reservation/receipt/audit intent.

Reserve validates nonnegative integral estimate (including explicit zero-cost
estimate still consumes one slot), held+spent+estimate <= approved ceiling and
scope occupied+1 <= approved concurrency ceiling. Zero ceiling is explicit deny,
not unlimited. Duplicate exact live reservation returns no delta; changed
attempt/request/terms conflict, terminal reservation cannot auto-resume.

Final consume/release/reconcile needs authoritative exact request/attempt/unit/
reservation receipt under backend accounting guard. Releasing zero spent only
with verified disposition; no automatic expiry/refund or assumed cancellation.
Consume frees held estimate/slot and records VERIFIED actual units. If actual
exceeds estimate or ceiling, record truthful overrun rather than hide incurred
usage or pretend execution budget authorization; deny new reserves over ceiling.
Such evidence does not itself authorize another attempt. Fixture proof remains
fixture, never actual provider/cost measurement. Same terminal proof replays with
no delta; conflicting terminal proof denied, never charge/refund twice.

Original window/terms retained for settlement even when current policy/window is
different or work revoked. Cleanup/accounting may be allowed after stop, not AI
execution. Actual owner adapter must verify reservation-specific authority and
receipt evidence; caller verified=true or quantity assertion is insufficient.
Domain has no identity/provider/storage implementation and no actual cost claim.

Following step must add own atomic SQL concurrency/bucket/reservation/command
receipt+audit/outbox, current guarded reserve/settle/reconcile services, migration,
runtime races/restart/rollback/stop-window tests. Pure transition tests are NOT
atomic/concurrent-runtime proof and do not close AC06. No SQL service provision
or other owner's job/session writes authorized by this checkpoint.

## C3c3b persistence implementation order

One own resource_scope UPDATE lock serializes counters for org/feature, including
across budget windows and definitions. Lock/create scope before bucket/reservation;
never acquire policy/owner locks from inside ledger transaction. Caller retains
current-use and accounting guards before entry and through commit. No provider
network work under ledger lock. Same ledger UoW stores reservation transition,
bucket held/spent, global slots, immutable audit/outbox intent and scoped command
receipt. All rollback together on any failure. Exact attempt unique across windows;
no new bucket or client request key can allocate the same attempt twice.

Forward ap_0003 adds only own ai_policy tables. Terminal reservation/provenance,
command receipts and audit payloads protected against rewrite; outbox delivery
marker alone may change. Current-use service composition remains a following
step, not implied by a directly callable persistence adapter. Offline DDL/shape
and controlled connection tests prove code paths only. Prepare actual PG race,
rollback, restart, window rollover and immutable-history tests separately; until
executed those remain NOT_RUN and AC06 remains open.
