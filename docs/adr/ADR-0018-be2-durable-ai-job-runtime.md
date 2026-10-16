# ADR-0018 — BE2 durable AI job component architecture

- Date: 2026-10-15, Asia/Saigon.
- Status: **ACCEPTED_ARCHITECTURE_FOR_BE2_01_COMPONENT**; actual O-09 component contract
  directives and separate Phase B implementation approval recorded2026-10-15. Runtime proof pending.
- Decision source: project owner replied **"Ổn đó"** to the immediately preceding concrete
  recommendation of preferred D1–D7, strong fence with fixture-first proof, the current fixture
  test profile and running the missing Phase A test before acceptance.
- Exact quote is recorded separately from its contextual interpretation in FEAT-044
  `plan/PHASE_B_DECISION_RECORD.md` revision4, decision O-01.
- Refines ADR-0003/0014/0015; reuses BE1 context from ADR-0016/0017 without extending their approval.
- Basis: FEAT-044 PHASE_B_PLAN.md / ADR_PROPOSAL.md / PORT_REVIEW.md revision3, design review PASS;
  their historical proposal bytes remain unchanged.

## Context and scope

BE2-01 Phase A provides candidate job/attempt contracts and fake adapters. Phase B needs durable
job state, atomic receipts/outbox, worker identity and recovery under concurrent writes/crashes.
The BE1 merge provides an existing PostgreSQL adapter and `backend/alembic` environment with
branch `be1_core`; BE2 does not create a competing migration environment by default.

Architecture source O-01 is retained below. Actual O-09 now accepts component Q1–Q8 and Phase A
candidate/fixture checkpoint, authorizes named synthetic Studio use and approves Phase B rev3 B1–B6
in the separate feature approval. This ADR is not a P2/P4 role sign-off or runtime proof.

## Decisions D1–D7

1. **D1 — Durable store:** PostgreSQL17 with SQLAlchemy Core2.x and psycopg3. BE2 owns schema
   `ai_jobs` in the same database as the owner schemas needed for D7. Same server with different
   databases does not satisfy the same-connection transaction. BE2 does not write BE1 tables.
2. **D2 — Migrations:** reuse the existing `backend/alembic` environment and add a BE2 `ai_jobs`
   branch alongside `be1_core`. Preserve BE1 history; wire schema/metadata and module-branch
   upgrade commands explicitly in B2. Migration ordering remains Q7; no autogenerate operation
   may silently drop another module's tables. Shared environments use forward migrations;
   downgrade tests use disposable databases only.
3. **D3 — Transport:** Redis/RQ is the only planned broker adapter. PostgreSQL owns state,
   dispatch outbox and redelivery; RQ transport retries are disabled. No PostgreSQL-only second
   queue adapter is added. SQL receipts and active-attempt identity absorb duplicate delivery.
4. **D4 — Transactions:** READ COMMITTED, job-revision CAS and unique constraints. A typed
   insertion conflict rolls back the entire candidate before a fresh transaction reads the
   winner, with the plan's bounded retry. Owner-decision fences remain necessary.
5. **D5 — Recovery:** lease owner+generation guards the entire acknowledgement bundle. An
   unstarted queued attempt is republished with its same attempt_id within the selected bound;
   exceeding it uses pure `record_dispatch_loss`, then existing retry backoff or exhaustion.
   Running timeout uses policy retry. An uncommitted completion claim is not reconstructed;
   provider output/work may be lost or repeated. No exactly-once provider execution is claimed.
6. **D6 — Worker identity:** short-lived HMAC capability bound to job+attempt with issuance/expiry
   and key_id; mint per publish, carry in transient WorkerDispatchEnvelope. No raw token in SQL
   outbox/receipts/audit/mobile/logs. Verification applies at start/progress/completion, including
   stored-receipt replay. Suppress structured RQ argument extras as well as formatted logs.
7. **D7 — Owner fence:** select the strong shared-transaction protocol. Owner bumps epoch under
   FOR UPDATE with the decision change and notice; BE2 holds a versioned OwnerFencePort contract
   under FOR SHARE on its own UoW connection until commit. BE2 tests first against a test-only
   ASSUMED_CONTRACT fixture. This selects the approach, not actual P2 adapter/adoption/sign-off;
   O-09 accepts OwnerFenceV1 0.1-candidate and the scopes/protocol in the component addendum
   below. Real P2 adapter/adoption/concurrence and integration remain separate B-12.

## Test profile and remaining inputs

The current `fixture.durable_jobs.v0` profile is selected for synthetic component testing only:
5s dispatch-start timeout,3 total publishes per attempt,3 policy attempts with30s attempt timeout,
40s worker capability TTL and100 atomic notice matches; existing auxiliary fixture settings stay
in the feature record. No production numeric policy is adopted and tests are not yet run.

The earlier O-02 inventory request is resolved by O-03…O-08: a separate CPU Studio
sketch2life-backend-test has user-reported Linux/Python3.12.15, PostgreSQL17.11/Redis8.10.2,
matching packages, authenticated connections and the missing live-route1 passed,0 skipped.
O-09 authorizes this named synthetic test environment and the private-file DB/per-run HMAC
mechanism in the accepted packet. No direct Codex remote execution or Phase B runtime proof
is claimed. FEAT-018/Wan environment stays outside scope.

## Consequences and implementation boundary

Preferred mechanisms and B-01..B-12 acceptance remain as reviewed. Actual O-09 approval and
accepted component answers/diagram reconciliation close B1 at component scope. B2–B6 have
separate task approval; first Claude code turn B2 only, stop for review before B3.
Claude is the implementation executor; one implementation batch is active at a time in the
existing six-batch/14-card roadmap. No live route, provider inference, durable ProviderCopyLifecycle,
BE1 fence implementation, production policy/deployment, commit or push is authorized here.

An alternative store/queue/fence/recovery choice requires the bounded amendment/review already
described in the decision record, rather than silently changing this selected architecture.

## O-09 component addendum —2026-10-15

The project owner explicitly accepts FEAT-044 decision record revision8 §13 as
PROJECT_OWNER_DIRECTIVE and approves PHASE_B_PLAN.md revision3 B1–B6. Actual reply is verbatim
in features/FEAT-044-be2-ai-job-foundation/approvals/PHASE_B_TASK_APPROVAL.md; current decision
record revision9 records reconciliation. No P1/P2/P4 role concurrence is inferred.

- Q1/Q7: qualified ai_jobs schema and ai_jobs branch in existing backend/alembic, module order
  follows its dependency graph; preserve BE1 history; disposable synthetic DB testing only.
- Q2/Q8: OwnerFenceV1 0.1-candidate epochs cover consent/purpose, session/context, recall,
  source-expiry, kill-switch, grant and artifact state. Owner FOR UPDATE epoch+decision+notice
  is one transaction; BE2 FOR SHARE on its own same-UoW connection through commit. Future P2
  rows/function ownership is retained, component proof uses ASSUMED_CONTRACT fixture.
- Q3: at-least-once post-commit cancellation notice with notice_id dedup; actual BE1 transport
  integration remains B-12.
- Q4/Q5: owned org/job/attempt artifact lineage/state fence, quarantine by exact stored event_id;
  durable BE2 audit outbox/at-least-once dedup and audit-only incident transaction before response;
  component sinks first, no real BE1 audit/artifact adapter claim.
- Q6: test dispatcher/reconciler/worker processes with fake provider. Coordinator generates one
  ephemeral HMAC key per test run, shares it through child-process restarts, never logs/persists
  it. DB password uses observed private-file mount. Production wiring/key rotation INTG-02 deferred.

B1 documentation is closed only for this component scope. Implementation NOT_STARTED, next
Q01/B2 READY_FOR_CLAUDE. Full feature/runtime/integration criteria remain open.
