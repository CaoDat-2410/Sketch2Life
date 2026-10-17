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
