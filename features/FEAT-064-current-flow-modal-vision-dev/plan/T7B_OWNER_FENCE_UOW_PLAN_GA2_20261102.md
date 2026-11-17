# T7b — PostgreSQL owner-fence adapter and same-transaction source check (GA2)

- Status: **APPROVED for this synthetic-only GA2 task by the owner's direct launch message**, subject to the append-only approval entry pinning this file's SHA-256.
- Parent: GOAL A2 REV2; V4 §1 and §3 D5. The prior T7b blocker plan remains unchanged as historical evidence.
- Dependency: T2C plan `T2C_BE1_CANVAS_OWNER_FACT_ADAPTER_PLAN_GA2_20261102.md` and its implementation. If T2C cannot expose a connection-bound current-facts resolver, T7b stops BLOCKED; no fixture epoch may substitute.

## Contract and exact allowlist

Implement a concrete `OwnerFenceFactory = Callable[[Connection], OwnerFencePort]` adapter only under `backend/src/sketch2life/infrastructure/assistance/**`. It imports the existing OwnerFence protocol/factory contract but does not modify any `ai_jobs` source. The factory is bound to the exact SQLAlchemy `Connection` used by `SqlAiJobRepository`'s transaction. It receives a connection-bound resolver from T2C to recompute the same current `ResolvedFacts` without opening another connection.

The fence scope is versioned and canonical, contains only the BE1 scope identifiers plus the pinned full `ResolvedFacts` digest and the minimum source/purpose identifiers required to recompute that binding, and rejects malformed/unknown versions, duplicate audience IDs, missing fields, and cross-organization scope. `OwnerFence.epoch` is the positive 31-bit value from `infrastructure/assistance/context_revision.py` over the pinned resolved-facts digest payload. `hold()` returns `FenceResult(current=False, stale=(...))` for unknown or changed facts; it never treats an unknown fence as current.

Before recomputing facts, the adapter applies transaction-local PostgreSQL `lock_timeout` and takes `FOR SHARE` locks on existing aggregate-revision, session, group, membership, synthetic-proof, and profile rows in deterministic `(table name, primary key)` order. Missing required rows are stale. Locks are held only by the caller's transaction and never across provider work. A concurrent UPDATE to a locked existing row waits until the owning transaction ends.

`FOR SHARE` does **not** prevent a phantom INSERT of a new membership row. The contract does not claim serializable exclusion after `hold()` returns. The regression test inserts a synthetic membership after the expected digest was captured but before `hold()`; the INSERT must complete without waiting, then the fence's same-connection recomputation must return STALE because the roster/`ResolvedFacts` digest changed.

Exact write/test allowlist:

- New `backend/src/sketch2life/infrastructure/assistance/owner_fence.py`
- New `backend/tests/unit/test_be1_owner_fence_t7b.py`
- `backend/tests/integration/test_be1_synthetic_pilot_postgres.py` only for T7b PostgreSQL lock/digest cases using its existing disposable synthetic harness.
- This plan, one new T7b report, append-only FEAT-064 approval/goal-ledger entries, and one GA2 snapshot.

No other source, test, schema, migration, route, composition, or record path is authorized by this plan. In particular do not edit `application/ports/ai_jobs.py`, `infrastructure/ai_jobs/sql/repository.py`, `infrastructure/ai_jobs/sql/tables.py`, `services/ai_jobs.py`, or `sketch_generation/adapters.py`.

## Implementation and acceptance

| Layer | Acceptance |
|---|---|
| L1 contract consumption | Correct protocol version; complete canonical scope encodes/decodes deterministically; malformed, unknown, or missing owner scope is stale. |
| L3 transaction | Factory uses exactly the supplied connection; sets bounded `SET LOCAL`/`set_config(..., true)` lock timeout; locks all existing required owner rows in sorted table/PK order with PostgreSQL `FOR SHARE`; no new transaction or commit is opened. |
| L4 current facts | Recompute through T2C's PostgreSQL resolver on the same connection after locks; compare both the full pinned digest and its 31-bit compatibility epoch. A digest difference, even if integer epoch collides, is STALE. |
| L7 update race | In a real PostgreSQL test, hold the fence transaction open; a second connection's UPDATE of a locked BE1 row remains blocked until release and then completes. Assert using synchronization/events and bounded waits, not sleep-only ordering. |
| L7 phantom membership | Insert a new synthetic roster member without waiting on an existing-row share lock; when the original pinned fence is subsequently checked, it returns STALE from the recomputed full digest. Explicitly document that inserts after `hold()` are outside this lock guarantee. |
| L7 failure behavior | Lock timeout, database read error, invalid current facts, unknown scope, or resolver error fails closed and does not return current. |

Tests: focused unit tests for scope encoding, sorting, lock SQL construction, malformed/stale/error cases; the two PostgreSQL concurrency/digest regressions; all T2C integration tests after T7b. Run no external provider. Use the one-time loopback acceptance DB only under the corrected T12 procedure; synthetic rows only, clean up only test-owned rows, never DROP/TRUNCATE.

After implementation run Ruff check/format with `backend/pyproject.toml`, focused strict mypy, the three repository validators, and `git diff --check`. Record actual test counts and any skipped DB case. No PostgreSQL/Alembic migration application is needed; PostgreSQL is only for the approved T7b integration checks.

## Limitations and stop conditions

- This is not a signature by BE1, BE2, or integration co-owners. `OwnerFenceV1` remains an unsigned pilot implementation until independent review and required owner signatures.
- If T2C cannot recompute the exact `ResolvedFacts` on the supplied connection, if a required lock target has no stable key, or if the synthetic PG fixture cannot safely isolate and clean its own rows, stop T7b and report BLOCKED/NOT RUN. Do not edit out-of-allowlist paths to make it work.
- No migration/schema, provider, Modal/GPU, external network, real-child data, or Git stage/commit/push.
