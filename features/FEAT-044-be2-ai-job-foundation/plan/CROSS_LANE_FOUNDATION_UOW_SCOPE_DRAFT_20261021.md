# Cross-lane foundation-owned UoW for BE2-01 / BE2-07 / BE2-08 — scope draft

- Status: `DRAFT / AWAITING_INDEPENDENT_REVIEW_AND_IMPLEMENTATION_APPROVAL`
- Prepared: 2026-10-21 (Asia/Saigon)
- Owning card: BE2-01 / FEAT-044 for the foundation transaction boundary.
- Participants: BE2-08 / FEAT-050 video rows; BE2-07 / FEAT-056 source-validity fence.
- Integration plan: FEAT-057 `CROSS_LANE_X01_X05_SLICE_PLAN_DRAFT_20261021.md`, revision 4,
  SHA256 `6AF69E07E7FC51BD6AAA992A703FBE97AC2BC8E588FEC9F8735FBF74E88C6601`.
- Existing owner-approved BE2-01 route scope SHA256:
  `AD1BA2706655CD040ACBBBF508577F79A41F5D5B3EF57D1437DA4C7F7F185DBD`.
  That scope does not include the shared-UoW boundary in this draft.

This is a new scope proposal, not implementation approval. The exact user direction is
recorded in FEAT-044, FEAT-050, FEAT-056, FEAT-049, FEAT-051 and FEAT-057 `DECISIONS.md`;
the FEAT-057 evidence note records the verbatim instruction and this draft's hash. Existing
approved addenda remain byte-frozen. No source, test, schema, migration, card status or
acceptance change is authorized by this draft. Each owner-owned participant change needs its
own exact file manifest and supplemental approval before source edits.

## Owner-directed design

1. BE2-01 owns the foundation UoW and the authorized transaction boundary used by both video
   submission and finalization. BE2-08 is a participant for its owned rows and may not begin,
   commit, or roll back the foundation transaction.
2. Submission and finalization are two separate commits using the same foundation-owned UoW
   mechanism. External generation occurs between them; no UoW/transaction remains open over
   provider or media work.
3. BE2-07 source validity is checked and held within the finalizer's UoW only when producer
   source data and foundation/video writes can participate in the same transactional store.
   If they cannot, X01 remains `PARTIAL`. A same-store read alone is insufficient evidence of
   a held fence: the implementation must show a lock/CAS or equivalent serialization shared
   with source invalidation writes through final commit. Otherwise X01 remains `PARTIAL`.
4. The job → run → source-pin mapping is resolved from authoritative persisted foundation job/
   request/attempt data. Keep `WorkerDispatchEnvelope` unchanged. If persisted foundation data
   cannot provide the exact approved identity, stop for a versioned contract change; do not
   trust broker payload fields or synthesize the missing pin.
5. BE2-08 publishes a read-only finalized-artifact model for BE2-09. BE2-09 consumes it through
   the public contract and binds its own review state to the exact artifact identity.
6. BE2-14 keeps current-use eligibility, worker execution authorization, and budget/concurrency
   reservation/accounting separate. The owner will provide the budget unit and limit separately.
   Reservation expiry/renewal requires a versioned CR. Until those inputs and the CR are adopted,
   missing or unknown authorization/reservation must fail closed; no provider is enabled.

These dispositions preserve X05d as `BLOCKED`, X05c/CR09-02 as `OPEN`, X01 as `PARTIAL` unless
the same-store fence is implemented and proven, and X09-08 as `NOT_IMPLEMENTED` until persisted
job-to-VideoWorker composition is tested. They do not accept any card.

## Source facts reviewed

- `SqlAiJobRepository.transaction()` opens a connection and transaction and yields a
  `SqlAiJobUnitOfWork`; the unit of work is bound to that connection.
- `VideoRunRows` in `infrastructure/knowledge_video/sql.py` accepts a caller-supplied SQLAlchemy
  connection, requires an open transaction, and does not commit. Its module documentation says
  it is not `AtomicVideoSubmission`.
- `AtomicVideoSubmission` and `AtomicVideoFinalizer` are application protocols. Their
  docstrings require an authorized foundation UoW, but the reviewed candidate does not yet
  provide the durable cross-card composition adapter.
- The current FEAT-057 scope index records CR08-01 as lacking a foundation-owned shared
  UoW/recovery entrypoint in the approved file boundary.
- The approved BE2-01 typed-route implementation passes its focused unit batch but does not
  prove a persisted foundation job reaches the real composition receiver.

These are candidate-source observations, not runtime or SQL conformance evidence.

## Proposed boundaries

### Boundary A — video submission

One foundation-owned transaction creates or authoritatively replays the BE2-08 run, foundation
job/attempt, dispatch/outbox intent, idempotency receipt and required audit intent. The BE2-08
participant writes only its owned run/receipt rows using the transaction supplied by the
foundation boundary. A same-key/same-body retry returns the authoritative original receipt;
a changed body conflicts. If commit acknowledgement is ambiguous, use an authenticated,
original-scope lookup; if that lookup is unavailable, remain pending and do not guess or submit
again.

### External work

Source resolution, media preparation, generation, validation and private staging happen after
Boundary A commits and before Boundary B starts. No database transaction is held across these
effects. Worker admission must verify the persisted job, request, attempt, capability and mapped
video run before external work.

### Boundary B — finalization

One separately opened foundation-owned transaction commits the BE2-08 terminal run and exact
artifact lineage with the authoritative foundation completion receipt/job outcome, required
outbox/audit state, and eligible source-fence check. The source fence must be held through this
commit under the adopted same-store mechanism. If source and finalizer cannot share a store and
serialization boundary, record X01 `PARTIAL`; do not replace the requirement with a
process-local coordinator or a last-moment read.

The transaction owner, rows/receipt, rollback behavior, unique-conflict handling, authoritative
recovery query, and late-result winner/quarantine semantics must be specified and reviewed in
the supplemental CR08-01 before implementation. This draft does not silently decide those
remaining details.

## Acceptance criteria proposed for the new scope

| ID | Required result |
|---|---|
| U01 | Foundation owns and opens each transaction; BE2-08 participates with owned-row operations and cannot commit the enclosing UoW. |
| U02 | Submission and finalization use distinct transactions; fault/rollback tests show no split success within either boundary; no transaction spans external generation. |
| U03 | Persisted foundation facts authoritatively bind job, request, attempt, run and source pin; the dispatch envelope remains unchanged. Missing/mismatched facts fail closed. |
| U04 | Same-key replay, changed-body conflict, duplicate delivery, ambiguous commit acknowledgement and receipt-unavailable behavior have explicit single-source-of-truth tests. |
| U05 | Finalization checks the exact BE2-07 source validity in the same transaction and proves the invalidation writer contends on the same lock/version. If the stores or serialization boundary differ, X01 remains `PARTIAL`. |
| U06 | Late-result winner/quarantine semantics are explicitly adopted and tested; losing results cannot overwrite the accepted artifact. |
| U07 | BE2-08 exposes only a read-only finalized-artifact model containing the adopted exact identity needed by BE2-09; no BE2-09 write reaches BE2-08 storage. |
| U08 | BE2-14 phase gates remain separate and fail closed; budget unit/limit are not invented, and expiry/renewal behavior is implemented only under a versioned adopted CR. |
| U09 | Offline tests distinguish fakes from SQL transaction conformance. Any SQL/database test not run is reported `NOT_RUN`; no fixture result is described as durable store proof. |
| U10 | No card is marked accepted/DONE; X05d stays `BLOCKED`, X05c/CR09-02 stays `OPEN`, and runtime/provider/Modal/Lightning remain `NOT_RUN`. |

## Candidate ownership and file boundaries

The exact manifest must be narrowed and separately approved before implementation. Candidate
paths for the BE2-01 foundation-owned portion only:

- `backend/src/sketch2life/application/ports/ai_jobs.py`
- `backend/src/sketch2life/application/services/ai_jobs.py`
- `backend/src/sketch2life/infrastructure/ai_jobs/sql/repository.py`
- `backend/src/sketch2life/infrastructure/ai_jobs/fakes.py`
- `backend/tests/unit/test_ai_job_application.py`
- New contract/unit tests, only after their exact new paths are included in the approved
  manifest.

Required companion work is not authorized by this FEAT-044 draft:

- BE2-08 participant/adapters and owned tests remain under FEAT-050. The current BE2-08
  cross-lane addendum explicitly leaves CR08-01 open and excludes this new foundation UoW.
- BE2-07 source-validity participation remains under FEAT-056. Its approved addendum excludes
  a new database schema/migration, BE2-01 fence implementation, and a real cross-service lock;
  any such change needs a revised BE2-07 scope and approval.
- BE2-14 reservation expiry/renewal needs its versioned CR, owner-supplied budget unit/limit,
  and a separately approved file/schema manifest before implementation.
- BE2-09's artifact consumer remains under FEAT-051 and needs the finalized BE2-08 read-model
  contract before its own exact file manifest can be frozen.
- FEAT-057 composition tests remain owned by FEAT-057 and require their own pinned manifest.

No migration is included. If the design requires schema changes, a new schema-specific plan,
exact SHA, and approval are required. Do not modify an existing migration.

## Open points before implementation approval

- Confirm same-store and invalidation-lock/CAS feasibility from the actual BE2-07 and foundation
  persistence owners. If infeasible, keep X01 `PARTIAL` and do not claim the finalizer fence.
- Specify CR08-01 transaction owner details, allowed BE2-08 participant operations, rollback,
  uniqueness and scoped recovery lookups.
- Confirm exact persisted foundation fields sufficient to recover the run and source pin without
  changing `WorkerDispatchEnvelope`.
- Adopt the exact public BE2-08 artifact read-model fields and terminal-visibility rule.
- Owner budget unit and limit are pending. Reservation timing (before dispatch or at worker
  admission), expiry/renewal CR version, settlement, and lost-ack behavior remain open until
  recorded and adopted; do not implement guessed values.
- Independently review and fix this draft, pin its final SHA, then record a new supplemental
  implementation approval and per-card minimal manifests. Until then all changes remain
  documentation-only.

## Offline-only implementation order after approval

1. Close/revise CR08-01 and the BE2-07 same-store fence contract; freeze exact BE2-01/07/08
   manifests. If the same-store condition fails, record X01 `PARTIAL` and omit any false PASS.
2. Confirm persisted job/run/source-pin mapping and the BE2-08 public artifact model. Keep the
   envelope unchanged unless a separate versioned CR is reviewed and approved.
3. Close BE2-14 phase mapping and reservation CR using owner-supplied budget inputs. Keep
   generation disabled when a required execution or budget gate is unavailable.
4. Implement the foundation UoW and its offline unit/contract tests; then implement card-owned
   BE2-07/08 participants only under their own approved manifests.
5. Run offline regressions and FEAT-057 composition tests on one pinned source snapshot; report
   unrun SQL/durable/runtime evidence distinctly.
6. Obtain independent code review, fix findings, and rerun the affected offline checks. Card
   acceptance remains a separate owner decision.

## Approval state

No implementation approval is recorded for this draft. The owner-directed design is recorded,
but this new scope, its exact final SHA, participant manifests, any CRs, source edits, tests,
schema changes, card acceptance and publication remain pending. Modal, Lightning, provider,
server, database and runtime execution are excluded.
