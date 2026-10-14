# BE2-01 Phase B — port review (P2 / P3 / P4)

- Revision: 3 (rev 1 sha256 `b4e67a83…677074e`; rev 2 sha256 `bfe46316…f2f46cac`, closure-reviewed in
  `PHASE_B_REV2_CLOSURE_REVIEW_20261015.md`; rev 3 adds the PB-C02 carrier deltas). Status: PENDING owner
  answers. Date: 2026-10-15, Asia/Saigon. Prepared by Claude; no message sent, no decision inferred.
- Companion to `PHASE_B_PLAN.md` revision 3 (§5 deltas Δ1–Δ15) and `PHASE_B_ADR_PROPOSAL.md` rev 3.
- Current interface versions: Phase A ports/contracts `0.1-candidate`
  (`backend/src/sketch2life/application/ports/ai_jobs.py`); candidate adoption pending in
  `evidence/notes/PHASE_A_ACCEPTANCE_GATE_RECORD.md`. BE1-02 generic persistence has no
  implementation/adopted contract in this repository.

| Owner | Interface / version now | Transaction / delivery semantics Phase B needs | Compatibility delta | Missing | Owner question | Evidence / decision |
|---|---|---|---|---|---|---|
| P3 / BE2 (own) | `AiJobRepository`/`AiJobUnitOfWork` `0.1-candidate` (fake) | Transaction per use case; job CAS; plain INSERT + typed `UniqueConflict` ⇒ full rollback + re-read; fenced outbox lease; reconciler with pure `record_dispatch_loss`; transient `WorkerDispatchEnvelope` + `WorkerCapabilityIssuer`; atomic notices; authoritative-settlement vs audit-only incident transactions | Δ4–Δ7, Δ9–Δ14 (Δ13 domain, Δ14 queue carrier) | SQL adapter, migrations, dispatcher, reconciler, worker | — (P3 implements after approval) | Plan §5–7 |
| P2 / BE1 — persistence conventions | None adopted | Shared PostgreSQL, module schemas, Alembic branch per module | BE2 owns schema `ai_jobs` only | Conventions | Q1: May BE2 own schema `ai_jobs` + Alembic branch in the shared database before BE1-02 lands? | PENDING_OWNER_DECISION |
| P2 — owner-decision fence (new, rev2) | None | Fence row per decision scope; epoch bumped `FOR UPDATE` in the same transaction as the decision change and its notice; BE2 holds fences `FOR SHARE` in its write transaction via a P2-owned function on the same connection; linearization = fence-row commit order | Δ1–Δ3: `OwnerFence` on eligibility/authorization/artifact decisions, `OwnerFencePort.hold` | Fence schema/function, scope granularity (subject, session, request, artifact, grant) | **Q8:** Will P2 own and adopt this fence protocol (or name an equivalent with a defined linearization point)? Which scopes carry epochs? If rejected, BE2 falls back to record-epoch + read-time exposure check (weaker; plan amendment) | PENDING_OWNER_DECISION |
| P2 — authorization | `AuthorizationPort.decide` `0.1-candidate` | Decision + grant fence before create/cancel writes; live check before ETag/304 | Δ1 | Real adapter (BE1-03) | Q2: Confirm synchronous in-process decision with a grant epoch and immediate revocation | PENDING_OWNER_DECISION |
| P2 — eligibility / notices | `EligibilityPort.check`, `CancellationNotice` `0.1-candidate` | Decision + fence; notices delivered at-least-once **after** the epoch bump commit, idempotent by `notice_id`; BE2 cancels all matches atomically (Δ10) | Δ1, Δ10 | Notice channel | Q3: Notice channel (BE1 outbox consumer) and confirmation that each notice is emitted in the same transaction as its epoch bump | PENDING_OWNER_DECISION |
| P2 — artifacts | `ArtifactPort.describe/quarantine(artifact_refs, reason_code)`, descriptor with lineage + `quarantine_reason` `0.1-candidate` | Descriptor adds state `fence`; lineage recorded at upload from the worker capability; **`ArtifactPort.quarantine(intent: QuarantineIntent)`** with `QuarantineIntent(event_id, organization_id, job_id, attempt_id, artifact_refs, reason_code)`, idempotent by the exact stored `event_id` across redeliveries, requested only from committed BE2 intents built from owned-lineage refs | Δ1 (artifact fence), Δ9, **Δ15** (signature change) | Lineage/fence-aware artifact adapter | Q4: Can the artifact store record producer lineage, expose a state version/fence and accept idempotent quarantine keyed by `event_id`? | PENDING_OWNER_DECISION |
| P2 — audit | `AuditPort.record` `0.1-candidate` (no event id) | At-least-once from BE2 outbox; dedup by deterministic `event_id`; incident (rejection/conflict) events committed via audit-only transaction | Δ9: `AuditEvent.event_id` | Durable audit sink with dedup | Q5: Accept at-least-once audit with `event_id` dedup and the incident path? | PENDING_OWNER_DECISION |
| P4 / integration — composition | `AiJobDependencies`, fixture router only | Entrypoints for API, dispatcher, reconciler, worker; HMAC key from runtime secrets (never outbox/logs/mobile); health/readiness for DB/Redis | Δ8 + Δ14: `WorkerCapabilityIssuer` wired into dispatcher/reconciler; `DispatchQueuePort.enqueue(WorkerDispatchEnvelope)`; RQ adapter `description=message_id`, `result_ttl=0`, no argument logging | Process model, secret provisioning | Q6: Process model and ownership of entrypoint wiring vs BE2 test entry modules; secret provisioning for the capability key | PENDING_OWNER_DECISION |
| P4 — migrations / environments | None | Migration ordering across module branches; disposable PostgreSQL 17 + Redis for tests | — | Environment + run order | Q7: Which authorised environment runs integration tests, and the migration ordering rule? | PENDING_OWNER_DECISION |
| P4 — contract names / namespace | `AsyncJobView` ≙ `JobStatusV1`, `/api/collaboration/v1` candidate | Unchanged by Phase B | None | Registry adoption (Phase A gate) | — | PENDING (Phase A record) |

## Small decision list for the owner

1. Phase A checkpoint disposition (G1) — task owner.
2. ADR D1–D7 adoption (or D3/D7 alternatives with plan amendment) and ADR location — owner.
3. P2 Q1–Q5 and **Q8 (owner fence)** — P2/BE1.
4. P4 Q6–Q7 — P4.
5. Authorised synthetic Linux environment with PostgreSQL 17 + Redis — owner/P4.
