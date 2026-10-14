# BE2-01 Phase B — ADR proposal (durable AI jobs)

- Revision: 3 (rev 1 sha256 `04f6c35b…b6b2d03`; rev 2 sha256 `48fa3c0e…fddae5b93`, closure-reviewed in
  `PHASE_B_REV2_CLOSURE_REVIEW_20261015.md`). Rev 3 changes only D5/D6 wording for PB-C01/PB-C02.
- Status: PROPOSED (not adopted). Date: 2026-10-15, Asia/Saigon. Author: Claude (executor).
- Scope: only decisions blocking durable AI jobs (`PHASE_B_PLAN.md` revision 3). No provider,
  model, web, deployment or cloud choice.
- Existing positions: ADR-0003 (ACCEPTED WITH ADR-0004 CONSTRAINTS) lists PostgreSQL,
  SQLAlchemy/Alembic, Redis/RQ for the original product; ADR-0014 calls them reuse
  candidates/current constraints for the replacement scope; ADR-0015 confirms only
  Android/FastAPI/React Native; ADR-0005 keeps product state in backend-owned PostgreSQL/S3.
  Repo declares sqlalchemy/psycopg/alembic/redis/rq and compose has postgres:17 + redis:8; no
  DB/queue/migration code exists. Declarations are not adoption.

| ID | Decision | Preferred proposal | Tradeoff | Alternative |
|---|---|---|---|---|
| D1 | Authoritative store | PostgreSQL 17 via SQLAlchemy Core 2.x + psycopg 3; AI-owned schema `ai_jobs`; **shared database with P2 schemas** so the owner fence (D7) can run in the same transaction | Real row CAS, unique constraints, SKIP LOCKED, same-connection fence. Tests need a Linux PostgreSQL | None for durable truth |
| D2 | Migrations | Alembic, one repo env, per-module branch labels (`ai_jobs` first); forward-only in shared envs; downgrade only on disposable DBs | BE1 adds its branch later; ordering agreed with P4 (Q7) | Separate env per module |
| D3 | Queue transport | **Preferred and only planned adapter:** Redis + RQ, at-least-once, broker job id = outbox `message_id`, **RQ retries disabled**; PostgreSQL outbox + SQL reconciler own redelivery (rev2 PB-R03) | Continuity with ADR-0003/compose; proves SRS broker-down recovery; RQ fork workers ⇒ Linux | PostgreSQL-only queue (rows claimed `FOR UPDATE SKIP LOCKED` + lease). Choosing it **before approval** requires editing plan §4 (drop `rq_queue.py`, add claim worker), G5/Q7 (no Redis), B-02/B-04 (replace broker-down with claim-worker death) and re-review. Not planned alongside RQ |
| D4 | Unit of work / isolation | One transaction per use case at READ COMMITTED; job row CAS; PK/unique constraints with **plain INSERT + typed unique-violation ⇒ full rollback + fresh re-read** (rev2 PB-R02); owner fences held inside the write transaction (D7) | Correct with explicit rules; no silent ignored inserts | SERIALIZABLE (does not fence owner state across modules either) |
| D5 | Dispatch / ack recovery | Lease with owner + **generation** fencing for mark/release; SQL reconciler republishes the **same attempt** when dispatched but not durably started after `DISPATCH_START_TIMEOUT`, bounded by `DISPATCH_MAX`, then the pure queued-only domain transition `record_dispatch_loss` (plan Δ13: `failed_retryable` with existing backoff, or `failed_exhausted` without budget; `started_at` stays null; CAS race with start has one winner) → policy retry; no same-claim recovery after provider output (rev2 PB-R03, rev3 PB-C01) | At-least-once; duplicates absorbed by attempt identity; bounded loss of uncommitted output stated explicitly | Transport retries in RQ (rejected: abandoned executions become FAILED when `retries_left=0`, and retries would duplicate SQL recovery) |
| D6 | Worker identity / capability | Backend service identity holds an HMAC key (runtime secret, `key_id` rotation); dispatcher/reconciler mint a capability **per publish** binding `(job_id, attempt_id, issued_at, expires_at)` with TTL = `DISPATCH_START_TIMEOUT` + attempt timeout + slack; token carried only by the transient `WorkerDispatchEnvelope(message, capability)` passed to `DispatchQueuePort.enqueue(envelope)` and issued via `WorkerCapabilityIssuer.issue(job_id, attempt_id, now)` just before enqueue (plan Δ14; never outbox, receipts, logs, mobile); verifier returns typed `VerifiedCapability` and the service compares job **and** attempt at start/progress/completion; republish mints a new token; expired token ⇒ denied (attempt then times out → retry); completion replay of a stored receipt requires a valid token for that attempt (rev2 PB-R04, rev3 PB-C02) | Stateless, attempt-scoped, short-lived; replay after expiry intentionally denied | DB-stored revocable tokens |
| D7 | Owner-decision fence (new, rev2 PB-R01) | P2-owned fence rows/function in the shared DB: owner bumps epoch `FOR UPDATE` in the decision-changing transaction (plus notice); BE2 holds the decision's fences `FOR SHARE` inside its write transaction via `OwnerFencePort`; linearization = commit order on the fence row | Real fencing without BE2 writing BE1 data; requires P2 to own and adopt the function (cross-module DB contract) | Epoch recorded per acceptance + read-time exposure check + notice reconciliation: acceptance can race an owner change (never exposed). Weaker; needs B-09 rewrite and re-review |

## Consequences and limits

- Named PROPOSED values: retry/poll/IDEMPOTENCY_TTL (Phase A), plus `DISPATCH_START_TIMEOUT`,
  `DISPATCH_MAX`, `NOTICE_ATOMIC_MAX`, capability slack. Production values need a versioned policy.
- No exactly-once provider execution; provider-side idempotency belongs to BE2-04/08 adapters.
- Durable ProviderCopyLifecycle, BE1 persistence/fence implementation, artifact and audit storage
  are outside this ADR; BE2 uses their ports.
- Test environment: Linux PostgreSQL 17 + Redis, synthetic-only, disposable databases; owner-fence
  component tests run against a test-only fixture labelled ASSUMED_CONTRACT.

## Decisions required from owner

1. Adopt D1–D7 as written, or choose the D3/D7 alternative (each forces a plan amendment and
   re-review before approval).
2. ADR record location/number (e.g. new `docs/adr/ADR-0016-…` vs feature-local record).
3. Authorise the synthetic test environment for B2–B6.
