# BE2-01 Phase B — B1 decision record (G1–G5)

- Status: **APPROVED_COMPONENT_SCOPE / B1_CLOSED_COMPONENT_SCOPE / B2_READY_FOR_CLAUDE**.
- Record revision: 9. Date: 2026-10-15, Asia/Saigon. Codex records actual user O-09; Claude
  remains backend executor. This revision adopts the exact revision8 §13 packet accepted by user,
  without changing planrev3/ADR proposal/port-review bytes or adding a business card.
- Phase A: ACCEPTED_CANDIDATE_FIXTURE. G1/G2/G3/G4/G5 are resolved for component implementation.
  P1/P2/P4 concurrence, registry/production adoption and actual B-12 integration remain deferred.
- Actual approval: `approvals/PHASE_B_TASK_APPROVAL.md` (verbatim). Approved revision8 sha256
  `0d5fdbfd783ddde3c08e739c23fe936784be73bcf8cb43dddf079dffde67164f`, preserved byte-identically at
  `evidence/local/phase-b-approval-20261015/before/plan/PHASE_B_DECISION_RECORD.md`.
- First Claude code turn B2 only; review before B3. Backend implementation NOT_STARTED;
  ACTIVE Q01/B2 READY_FOR_CLAUDE, WIP1/cards14, parent BE2-01 IN_PROGRESS/full-cardDONE0.
- Current bound inputs (sha256). Immutable reviewed proposals retain their historical pending
  tables; actual approval/current gate records supersede those dated gate cells.

| Input | sha256 |
|---|---|
| `plan/PHASE_B_PLAN.md` revision 3 | `bb20d5be45dc0552a803f67b5927d4a38dc113cabe10b3a6088644d874ba5848` |
| `plan/PHASE_B_ADR_PROPOSAL.md` revision 3 | `756b6df5ab8e8ec659ffabdc26a0083f035d28d63b86cebc54c6071c9f8ad0ac` |
| `plan/PHASE_B_PORT_REVIEW.md` revision 3 | `3af783a7efca61c5f098f7679b70bbdee4eb6034b9370291c282064ee5579699` |
| `evidence/notes/PHASE_B_PLAN_FINAL_REVIEW_20261015.md` (design review PASS) | `8ea35f4957600818f3794bcabef6d8694c66dce6fb1a8df1c67099c27bab5bb5` |
| `evidence/notes/PHASE_A_ACCEPTANCE_GATE_RECORD.md` (current G1) | `0b3ddbc02ef139ac8a28fc0c344d9cb21d7837105859ca4ad62f6c4d91527644` |

- B1 exit: ADR-0018 + Q1–Q8 accepted as PROJECT_OWNER_DIRECTIVE + seven reviewed diagrams/
  twelve crash windows reconciled. See evidence/notes/PHASE_B_B1_CLOSURE_AND_HANDOFF_20261015.md.
  Diagrams remain ASSUMED_CONTRACT / NOT_RUNTIME_EVIDENCE; no runtime PASS is inferred.

## How a row gets decided

The owner answers by row ID with: **ACCEPT**, **ACCEPT_WITH_CHANGE** (state the change),
**REJECT → alternative**, or **DEFER**. Each answer also needs the name or role of the person
deciding, the date, and where the answer lives (chat message, signed note, meeting record). Claude
copies the answer verbatim into §7 and updates the row. Two kinds of record are kept apart:

- **ROLE_OWNER_RECORD**: P1/FE, P2/BE1 or P4/integration answers for its own interface (ADR-0015
  role split).
- **PROJECT_OWNER_DIRECTIVE**: the project/task owner decides scope, environment, ADR adoption or
  approval. If the project owner answers a role question, it is recorded as a directive, together
  with whether the role owner concurred. It is never relabelled as that role owner's sign-off.

An answer that selects an alternative (D3/D7 or any other ADR alternative) is not adopted quietly.
It triggers the plan amendment in §3.1 and a focused review **before** G2.

## 1. Existing inputs found (searched first)

Sources searched: FEAT-044 CONTEXT/DECISIONS/STATUS/tracker/approval/evidence notes,
`docs/context/PROJECT_CONTEXT.md`, `SOURCE_REGISTER.md`, `docs/adr/`, FEAT-040 team breakdown,
backend `pyproject.toml`, `compose.yaml`, `scripts/lightningai/`, the git branches/worktrees, and
this Claude session.

| Source | Type | What it decides | What it does not decide |
|---|---|---|---|
| `approvals/TASK_APPROVAL.md` (user, 2026-10-14) | PROJECT_OWNER_DIRECTIVE | BE2-01 Phase A rev 1, A1–A9 only | Phase B, stack adoption, numeric policy, registry |
| `PROJECT_CONTEXT.md` “Environment policy (owner override, 2026-10-10)” | PROJECT_OWNER_DIRECTIVE (policy level) | Windows = code/static tests only, no Docker images or GPU packages installed there; LightningAI = dependency-install and integration-test environment, separate Sketch2Life venv, Wan2.2 env never modified; `scripts/lightningai/setup.sh` needs explicit `SKETCH2LIFE_ALLOW_INSTALL=1`; readiness and test PASS gates kept separate | Authorization of a specific PostgreSQL 17 + Redis environment for B2–B6, or how those servers are provided. `setup.sh` installs Python packages only and provisions no database or broker |
| ADR-0015 (OWNER_ROLE_ALLOCATION_ACCEPTED) | PROJECT_OWNER_DIRECTIVE | P1 FE, P2 BE1, P3 BE2 (owns durable AI job adapters), P4 composition, shared run environment and integration; no integration through direct cross-module DB writes; names of people unspecified | Any port contract, ADR D1–D7 or environment |
| ADR-0003 / ADR-0014 | Accepted historical stack / scope replacement | PostgreSQL, SQLAlchemy/Alembic, Redis/RQ are reuse candidates and current constraints | Adoption for BE2 durable jobs (needs G3) |
| FEAT-044 DECISIONS 31–33, 37 | Process rules (Codex/Claude), not owner decisions | Phase A may be accepted at candidate/fixture scope with production adoption deferred; the skipped test must become 1 passed/0 skipped; “tiếp tục đi” means continue documentation only | Any acceptance |
| `PUBLICATION_SELECTION_20261015.md` + commit `882e904` on `origin/feature/be2-01-ai-job-foundation` | User-requested publication triage | Reviewed Phase A source and records are published at `882e904` | Acceptance, approval or runtime scope |
| `evidence/notes/Q00_FOLLOWUPS_EOF_DISPOSITION_20261015.md` | User-approved whitespace fix (another session, uncommitted) | One trailing blank line removed from `test_ai_job_q00_followups.py`; new expected hash `9a1f5ad6…` | Q00/Phase A/Phase B acceptance |
| Codex reviews (Phase A final, Phase B rev 1/rev 2/rev 3) | Independent review | Code PASS (fake/contract scope); plan rev 3 PASS (design scope) | Owner decisions, adoption, approval |

**Historical result at revision1:** no role-owner inputs or project-owner gate decisions were found.
**Current update:** O-01 selects the preferred architecture and fixture profile; O-02 requests
read-only inventory. No P1/P2/P4 concurrence or environment authorization is supplied by either.

## 2. G1 — Phase A checkpoint (reuse gate record; nothing re-asked)

The questions are already recorded verbatim in `evidence/notes/PHASE_A_ACCEPTANCE_GATE_RECORD.md`
and are not repeated or reworded here.

| ID | Gate | Current proposal / source | Exact owner question | Owner | Actual decision + source/date | Effect / condition for code |
|---|---|---|---|---|---|---|
| G1-P1 | Candidate consumer review | `AsyncJobView`/`AsyncJobChildView` `0.1-candidate`, CMD-44 shape (gate record row “P1 / FE”) | As recorded in gate record row “P1 / FE” (unchanged) | P1 / FE | ACCEPTED_CANDIDATE_BY_PROJECT_OWNER — O-09,2026-10-15; approved rev8 §13 and approvals/PHASE_B_TASK_APPROVAL.md. ROLE_CONCURRENCE_DEFERRED | G1 component checkpoint satisfied; actual role-owner concurrence/production adoption remains deferred |
| G1-P2 | Candidate port semantics | Phase A ports `0.1-candidate` (gate record row “P2 / BE1”) | As recorded in gate record row “P2 / BE1” (unchanged). Durable BE1 capability is asked separately in G4, not here | P2 / BE1 | ACCEPTED_CANDIDATE_BY_PROJECT_OWNER — O-09,2026-10-15; approved rev8 §13 and approvals/PHASE_B_TASK_APPROVAL.md. ROLE_CONCURRENCE_DEFERRED | G1 component checkpoint satisfied; actual role-owner concurrence/production adoption remains deferred |
| G1-P4 | Names/versions/namespace | `AsyncJobView` ≙ `JobStatusV1`, `/api/collaboration/v1` candidate (gate record row “P4 / integration”) | As recorded in gate record row “P4 / integration” (unchanged) | P4 / integration | ACCEPTED_CANDIDATE_BY_PROJECT_OWNER — O-09,2026-10-15; approved rev8 §13 and approvals/PHASE_B_TASK_APPROVAL.md. ROLE_CONCURRENCE_DEFERRED | G1 component checkpoint satisfied; actual role-owner concurrence/production adoption remains deferred |
| G1-LIVE | Live-app route negative test | `python -B -m pytest backend/tests/contract/test_ai_job_polling.py::test_live_app_routes_have_no_candidate_job_route -p no:cacheprovider -rs` must give **1 passed, 0 skipped** | Either (a) the test runs in an existing or authorised environment that has pytest + FastAPI + Pillow, or (b) the optional deviation question in the gate record (scope, risk, re-run condition) is answered | Task owner (deviation); runner = Claude/P4 in an authorised environment | PASS_USER_REPORTED — O-08,2026-10-15: exact test1 passed,0 skipped in2.72s; Python3.12.15/Pillow12.3.0/av18.1.0; source993a26c; metrics/PHASE_B_LIGHTNING_ENVIRONMENT_20261015.json | Missing test obligation satisfied; no deviation needed. Earlier skip retained as historical evidence; no owner acceptance or Phase B approval supplied by the result |
| G1-TASK | Phase A checkpoint disposition | Accept at **candidate/fixture checkpoint** with production adoption deferred (DECISIONS 32). Meaning: `0.1-candidate` names/semantics accepted as consumer fixtures. Not included: production adoption, registry entry, live router, production retry/poll policy, durable recovery | As recorded in gate record row “Phase A checkpoint (task owner)” (unchanged). Possible outcomes: accept as scoped / accept with explicit live-route deviation / request change (back to Q00) | Task owner (project owner who approved Phase A) | ACCEPTED_CANDIDATE_FIXTURE — actual user O-09,2026-10-15; verbatim Phase B approval record; live-route PASS_USER_REPORTED | G1 satisfied for B2–B6 component scope; Q00 accepted; parent BE2-01 remains IN_PROGRESS |
| G1-DEF | DATA-24 / ProviderCopyLifecycle shapes | Gate record rows BE2-05, BE2-14 | — | BE2-05 / BE2-14 owning cards | DEFERRED_TO_OWNING_CARD | Not a G1 prerequisite. Phase B keeps the ProviderCopyLifecycle fake |

## 3. G3 — ADR D1–D7 (from `PHASE_B_ADR_PROPOSAL.md` rev 3)

Adoption owner: the **project owner**, who adopts the ADR (FEAT-044 tracker). P3/BE2 is the
proposer. P2 and P4 concurrence is listed where the decision binds their module or environment.

| ID | Gate | Current proposal / source | Exact owner question | Owner | Actual decision + source/date | Effect / condition for code |
|---|---|---|---|---|---|---|
| G3-D1 | Authoritative store | PostgreSQL 17 + SQLAlchemy Core 2.x + psycopg 3; AI-owned schema `ai_jobs`; **shared database with P2 schemas** so D7 runs in one transaction (ADR D1) | Adopt PostgreSQL 17 / SQLAlchemy Core / psycopg 3 as the BE2 durable job store, with BE2 owning schema `ai_jobs` inside a database shared with P2 schemas? | Project owner; P2 concurrence (shared DB) | ACCEPTED_COMPONENT_BY_PROJECT_OWNER — architecture O-01, confirmed by O-09 approved rev8 §13/Phase B rev3. ADR-0018; actual role concurrence deferred | Blocks B2 (`tables.py`, §6 model) and B3. A separate database would break the D7 same-transaction fence → only possible with D7-alt (§3.1) |
| G3-D2 | Migrations | Reuse existing backend/alembic environment; add ai_jobs branch alongside be1_core; preserve BE1 history. Forward-only in shared environments; disposable DB downgrade tests only | Adopt one Alembic environment with per-module branch labels, BE2 branch `ai_jobs`, forward-only outside disposable test DBs? | Project owner; P4 concurrence (ordering, Q7) | ACCEPTED_COMPONENT_BY_PROJECT_OWNER — architecture O-01, confirmed by O-09 approved rev8 §13/Phase B rev3. ADR-0018; actual role concurrence deferred | Blocks B2 migration layout and B-01/B-11 migration matrix |
| G3-D3 | Queue transport | Redis + RQ, at-least-once, broker job id = outbox `message_id`, **RQ retries disabled**; SQL outbox + reconciler own redelivery (ADR D3). Implementation must also strip RQ structured-log job args (final review note, part of B-05e/B-10c) | Adopt Redis + RQ as the only planned queue adapter, with RQ retries disabled and SQL-owned redelivery? | Project owner; P4 concurrence (process model) | ACCEPTED_COMPONENT_BY_PROJECT_OWNER — architecture O-01, confirmed by O-09 approved rev8 §13/Phase B rev3. ADR-0018; actual role concurrence deferred | Blocks B4 (`rq_queue.py`, Δ14 envelope), B-02/B-04/B-10c. D3-alt → §3.1 amendment first |
| G3-D4 | Unit of work / isolation | One transaction per use case at READ COMMITTED; job row CAS; plain INSERT + typed unique violation ⇒ full rollback + fresh re-read; owner fences held inside the write transaction (ADR D4) | Adopt READ COMMITTED transactions with job CAS and rollback-on-conflict creates as specified in plan §7.2? | Project owner; P2 concurrence (fence in the same transaction) | ACCEPTED_COMPONENT_BY_PROJECT_OWNER — architecture O-01, confirmed by O-09 approved rev8 §13/Phase B rev3. ADR-0018; actual role concurrence deferred | Blocks B3 (Δ4/Δ5), B-03/B-07/B-08 |
| G3-D5 | Dispatch / ack recovery | Lease with owner + generation fencing; reconciler republishes the same attempt after `DISPATCH_START_TIMEOUT`, bounded by `DISPATCH_MAX`, then pure `record_dispatch_loss` (Δ13) → policy retry; no same-claim recovery after provider output (ADR D5) | Adopt generation-fenced leases, same-attempt republish bounded by named values, and `record_dispatch_loss` as the only queued-loss transition, accepting the stated bounded loss after provider output? | Project owner | ACCEPTED_COMPONENT_BY_PROJECT_OWNER — architecture O-01, confirmed by O-09 approved rev8 §13/Phase B rev3. ADR-0018; actual role concurrence deferred | Blocks B4 reconciler + Δ13 domain change. Values come from G5-PROFILE |
| G3-D6 | Worker identity / capability | Backend service HMAC key (`key_id` rotation); per-publish capability bound to `(job_id, attempt_id, issued_at, expires_at)`; carried only by transient `WorkerDispatchEnvelope` via `WorkerCapabilityIssuer` (Δ8/Δ14); never in outbox/receipts/logs/mobile; expired ⇒ denied (ADR D6) | Adopt a stateless HMAC attempt-bound capability, carried only in the transient broker envelope, with TTL = `DISPATCH_START_TIMEOUT` + attempt timeout + slack? | Project owner; P4 concurrence (key provisioning, Q6) | ACCEPTED_COMPONENT_BY_PROJECT_OWNER — architecture O-01, confirmed by O-09 approved rev8 §13/Phase B rev3. ADR-0018; actual role concurrence deferred | Blocks B5 (`worker_capability.py`, B-05e/B-10c) |
| G3-D7 | Owner-decision fence | P2-owned fence rows + read function in the shared DB; P2 bumps the epoch `FOR UPDATE` in the decision-changing transaction (plus notice); BE2 holds fences `FOR SHARE` in its write transaction on the same connection via `OwnerFencePort`; linearization = commit order on the fence row (ADR D7) | Adopt the shared-transaction owner fence as the Phase B protocol? This includes confirming that a P2-owned, **versioned** fence function on the shared database is an acceptable cross-module contract under AGENTS.md ("versioned contracts, not direct database coupling") and ADR-0015 #4. BE2 only calls the function and never writes P2 rows | Project owner; G4-Q8 needs an explicit versioned-contract/component-assumptions decision, recorded as a P2 ROLE_OWNER_RECORD or PROJECT_OWNER_DIRECTIVE. A directive is not P2 concurrence | ACCEPTED_COMPONENT_BY_PROJECT_OWNER — O-09 adopts OwnerFenceV1 0.1-candidate scopes/protocol and ASSUMED_CONTRACT proof in §13/Q8. No P2 concurrence | G3/G4 component design satisfied; actual P2 adapter/integration remains B-12; no D7-alt selected |
| G3-LOC | ADR location | Recorded at docs/adr/ADR-0018-be2-durable-ai-job-runtime.md; free number verified, existing BE1 ADR0016/0017 preserved | Where is the adopted ADR recorded: new `docs/adr/ADR-0018-…` (or next free number at creation) or a FEAT-044-local record? | Project owner | RECORDED — routine repository location chosen by Codex for the accepted architecture; O-01, 2026-10-15 | Adopted architecture path/hash are captured in the owner-selection checks; actual Phase B approval remains G2 |

### 3.1 Exact deltas if an alternative is chosen (amendment + focused review before G2)

| Alternative | Plan sections that change | Acceptance delta |
|---|---|---|
| **D3-alt** PostgreSQL-only queue (rows claimed `FOR UPDATE SKIP LOCKED` + lease) | §4: drop `rq_queue.py`, add claim worker module; §5 Δ14: there is no broker envelope, so the claiming worker must obtain the capability in-process from `WorkerCapabilityIssuer` at claim time, still never persisted; §7.1 receive/start rows become claim/start rows; G5/Q7 no Redis | B-02 broker-down → DB-unavailable/claim-worker death; B-04a kill-after-receive → kill-after-claim; B-05e/B-10c “token only via broker envelope / real Redis/RQ” → “issued at claim, absent from SQL rows/receipts/audit/logs”; the RQ structured-log check no longer applies. Plan revision 4 + review |
| **D7-alt** record-epoch fallback | §5.1/Δ2/Δ3: no `OwnerFencePort.hold`; epochs recorded in `job.accepted_fences` at acceptance + read-time exposure check + notice reconciliation; `owner_fence_fixture.py` becomes an epoch-source fixture; D1 shared DB no longer strictly required | B-09a–c change from “stale decision does not authorise create/start/completion” to “acceptance may commit concurrently but is never exposed and is reconciled by the notice”. The owner must explicitly accept this weaker guarantee. Plan revision 4 + review |
| D2-alt separate Alembic env per module | §4 migrations layout; Q7 ordering rule | B-01/B-11 matrix per env |
| D4-alt SERIALIZABLE | §7.2 create race rule (serialization-failure retry instead of unique-violation rollback); still needs D7 for owner state | B-03/B-08 rewritten for serialization retries |
| D5-alt RQ transport retries | Conflicts with closed PB-R03 (duplicate recovery paths, abandoned job FAILED at `retries_left=0`) | B-04/B-06a rewritten; full re-review |
| D6-alt DB-stored revocable tokens | §6 adds a token table holding only token hashes; Δ8/Δ14 verifier becomes a lookup | B-05e: no raw token at rest; revocation tests added |

## 4. G4 — P2/P4 port answers (the eight existing questions, deduplicated)

Questions Q1–Q8 are copied unchanged from `PHASE_B_PORT_REVIEW.md` rev 3. The “answer must cover”
column only lists what the existing question already implies, so a reply is complete. It adds no
new question.

**What B1 needs from P2:** a contract decision (semantics + version label). B1 does **not** need P2
to implement BE1-02/BE1-03 or any adapter. B3–B5 component proof uses the Phase A fakes and the
test-only owner-fence fixture labelled `ASSUMED_CONTRACT`. That fixture is never an actual P2
adapter. Real owner integration stays B-12, NOT claimed by Phase B.

| ID | Existing question (verbatim) | Answer must cover | Owner | Actual decision + source/date | Effect / condition for code |
|---|---|---|---|---|---|
| G4-Q1 | “May BE2 own schema `ai_jobs` + Alembic branch in the shared database before BE1-02 lands?” | Yes/no; whether BE1 conventions (naming, roles, search_path) are fixed later without blocking BE2 | P2 / BE1 | ACCEPTED_PROJECT_OWNER_DIRECTIVE — O-09 §13/Q1: PostgreSQL17/shared database, qualified ai_jobs schema, existing backend/alembic + ai_jobs branch; preserve BE1 history, disposable synthetic DB tests only | Component gate answered by actual owner directive; implementation proof remains in its approved batch. No real role-owner sign-off or adapter integration claimed |
| G4-Q2 | “Confirm synchronous in-process decision with a grant epoch and immediate revocation” | Authorization decision carries `fence: OwnerFence` (Δ1); revocation bumps the grant epoch | P2 / BE1 | ACCEPTED_PROJECT_OWNER_DIRECTIVE — O-09 §13/Q2: synchronous decision with grant epoch, revoke bumps epoch; ASSUMED_CONTRACT fixture before real owner adapter | Component gate answered by actual owner directive; implementation proof remains in its approved batch. No real role-owner sign-off or adapter integration claimed |
| G4-Q3 | “Notice channel (BE1 outbox consumer) and confirmation that each notice is emitted in the same transaction as its epoch bump” | Channel; at-least-once delivery after commit; idempotency by `notice_id` | P2 / BE1 | ACCEPTED_PROJECT_OWNER_DIRECTIVE — O-09 §13/Q3: owner epoch+decision+notice in one transaction; at-least-once post-commit fixture delivery, notice_id dedup; actual transport integration B-12 deferred | Component gate answered by actual owner directive; implementation proof remains in its approved batch. No real role-owner sign-off or adapter integration claimed |
| G4-Q4 | “Can the artifact store record producer lineage, expose a state version/fence and accept idempotent quarantine keyed by `event_id`?” | Acceptance of `ArtifactPort.quarantine(intent: QuarantineIntent)` with `QuarantineIntent(event_id, organization_id, job_id, attempt_id, artifact_refs, reason_code)` (Δ15). The sink treats a repeated **exact stored** `event_id` as a no-op. Lineage is recorded at upload | P2 / BE1 | ACCEPTED_PROJECT_OWNER_DIRECTIVE — O-09 §13/Q4: org/job/attempt lineage and artifact-state fence; owned refs only, quarantine sink dedup by exact stored event_id; fixture adapter | Component gate answered by actual owner directive; implementation proof remains in its approved batch. No real role-owner sign-off or adapter integration claimed |
| G4-Q5 | “Accept at-least-once audit with `event_id` dedup and the incident path?” | Deterministic `AuditEvent.event_id` (Δ9); dedup at the audit sink; audit-only incident transaction for non-authoritative rejection/conflict | P2 / BE1 | ACCEPTED_PROJECT_OWNER_DIRECTIVE — O-09 §13/Q5: BE2 durable audit outbox/at-least-once deterministic event_id; audit-only incident transaction before response; component sink | Component gate answered by actual owner directive; implementation proof remains in its approved batch. No real role-owner sign-off or adapter integration claimed |
| G4-Q6 | “Process model and ownership of entrypoint wiring vs BE2 test entry modules; secret provisioning for the capability key” | Separate API/dispatcher/reconciler/worker processes or not; INTG-02 owns production wiring and BE2 ships test entry modules only. The signing-key provisioning **mechanism** and `key_id` rotation must be named; values never go into the repo, outbox, logs or mobile | P4 / integration | ACCEPTED_PROJECT_OWNER_DIRECTIVE — O-09 §13/Q6: dispatcher/reconciler/worker test processes and fake provider; coordinator shares one ephemeral key per test run through child restarts, never persists/logs key; production provisioning/rotation INTG-02 deferred | Component gate answered by actual owner directive; implementation proof remains in its approved batch. No real role-owner sign-off or adapter integration claimed |
| G4-Q7 | “Which authorised environment runs integration tests, and the migration ordering rule?” | Environment part is answered **once** in G5-ENV (dedup). Q7 keeps only the migration ordering rule across module branches | P4 / integration | ACCEPTED_PROJECT_OWNER_DIRECTIVE — O-09 §13/Q7: sketch2life-backend-test, Python3.12/PostgreSQL17/Redis8; existing Alembic dependency graph determines module ordering, preserve BE1; exact commands are B2 work | Component gate answered by actual owner directive; implementation proof remains in its approved batch. No real role-owner sign-off or adapter integration claimed |
| G4-Q8 | “Will P2 own and adopt this fence protocol (or name an equivalent with a defined linearization point)? Which scopes carry epochs? If rejected, BE2 falls back to record-epoch + read-time exposure check (weaker; plan amendment)” | **Scope:** which of subject consent/purpose, session/context revision, recall/source-expiry/kill-switch, authorization grant and artifact state carry epochs. **Epoch:** bumped `FOR UPDATE` in the same transaction as the decision change and its notice. **Connection ownership:** P2's function runs read-only (`FOR SHARE`) on the **BE2 unit-of-work connection**; BE2 owns the connection and transaction, P2 owns the rows and function. **Version:** contract label (e.g. `OwnerFenceV1 0.1-candidate`). Confirm that the `ASSUMED_CONTRACT` fixture may stand in until a P2 adapter exists | P2 / BE1 | ACCEPTED_PROJECT_OWNER_DIRECTIVE — O-09 §13/Q8: OwnerFenceV1 0.1-candidate, all listed consent/purpose/session/context/recall/source-expiry/kill-switch/grant/artifact-state epochs; owner FOR UPDATE epoch+decision+notice, BE2 FOR SHARE same UoW through commit. ASSUMED_CONTRACT fixture allowed; no P2 concurrence | Component gate answered by actual owner directive; implementation proof remains in its approved batch. No real role-owner sign-off or adapter integration claimed |

## 5. G5 — environment, inventory, secrets and test profile

| ID | Gate | Current proposal / source | Exact owner question | Owner | Actual decision + source/date | Effect / condition for code |
|---|---|---|---|---|---|---|
| G5-ENV | Execution environment | The policy directive (2026-10-10) points to LightningAI with a separate Sketch2Life venv (`scripts/lightningai/setup.sh`, `SKETCH2LIFE_ALLOW_INSTALL=1`), Wan2.2 untouched. Installing Docker images on Windows (local `compose.yaml` services) is excluded by the same directive. PostgreSQL 17 + Redis provisioning is not covered by any script | Authorise <named environment> as the synthetic-only Linux environment for B2–B6, with PostgreSQL 17 and Redis provided by <mechanism>, disposable databases only, synthetic data only (no child media, no provider calls), source checked out from a published commit of `feature/be2-01-ai-job-foundation`, Wan2.2 environment unchanged? Who operates it? | Project owner (authorization); P4 (shared run environment, ADR-0015) | AUTHORIZED_COMPONENT_TEST_ENVIRONMENT — O-09 approved rev8 §13, named Studio sketch2life-backend-test; O-08 baseline readiness USER_REPORTED | Synthetic tests and selected source/test synchronization authorized; no secret/media/data transfer, commit/push/deploy or production evidence |
| G5-INV | Dependency inventory | Declared in `backend/pyproject.toml` main deps: `sqlalchemy>=2.0,<3`, `psycopg[binary]>=3.2,<4`, `alembic>=1.16,<2`, `redis>=6,<7`, `rq>=2,<3`, `fastapi>=0.141,<1`, `Pillow>=11,<13`; dev: `pytest>=8.4,<9`. `compose.yaml` names `postgres:17-alpine`, `redis:8-alpine` (reference only). Installed versions in the target environment: unknown | Accept these declared ranges as the B2–B6 baseline, with exact installed versions (Python, packages, PostgreSQL server 17.x, Redis server, RQ) captured at setup by `tools/verify_lightning_runtime.py --mode inventory` plus server version queries? | P4 + P3 | PASS_USER_REPORTED — O-08 inventory in metrics/PHASE_B_LIGHTNING_ENVIRONMENT_20261015.json; observed versions match manifest ranges; no new pins/dependency change required | Use the recorded environment versions for component evidence. New Phase B code still validates B-01..B-12; original standalone pip-check output was not pasted |
| G5-SECRET | Secret source | Capability signing key, DB URL and Redis URL come from the authorised environment's runtime settings. Proposal for synthetic tests: per-run ephemeral signing key generated in-process and never written to disk or logs | Confirm the secret **mechanism** for the test environment (ephemeral per-run key for synthetic tests; operator-provided runtime settings for DB/Redis), and leave production provisioning to Q6/INTG-02? | P4 + project owner | ACCEPTED_PROJECT_OWNER_DIRECTIVE — O-09 §13/Q6: observed private-file DB password; coordinator ephemeral per-run HMAC key shared through child-process restarts, no persistence/logging | Component key mechanism accepted; production secret wiring/rotation remains INTG-02; values never enter repository/logs/evidence |
| G5-PROFILE | Named test/runtime values | Plan/ADR named PROPOSED values plus existing attempt policy; proposal = separate fixture profile below, **not** production | Approve fixture profile `fixture.durable_jobs.v0` (values below) for B2–B6 synthetic tests only, keeping every value PROPOSED and outside production policy? | Task owner (can be named in the G2 approval); P3 proposes | AUTHORIZED_FIXTURE_ONLY — architecture O-01 and actual O-09 B1–B6 approval; fixture.durable_jobs.v0 and auxiliary values remain non-production | Approved for synthetic component tests; no production numeric-policy adoption or runtime PASS |

### 5.1 Proposed fixture profile `fixture.durable_jobs.v0` (PROPOSED, FIXTURE_ONLY)

| Name | Proposed fixture value | Basis | Status |
|---|---|---|---|
| `DISPATCH_START_TIMEOUT` | 5 s | Short enough for process-kill tests (B-04a) | PROPOSED, fixture only |
| `DISPATCH_MAX` | 3 publishes per attempt (first + 2 republishes) | Exercises B-04(v) republish and B-04b(i/ii) exceed | PROPOSED, fixture only |
| `NOTICE_ATOMIC_MAX` | 100 matches | B-09e uses > 50 matches; a separate case > 100 checks the typed failure without marking | PROPOSED, fixture only |
| Capability slack | 5 s ⇒ capability TTL = 5 + 30 + 5 = 40 s | ADR D6 formula with the fixture attempt timeout | PROPOSED, fixture only |
| Outbox lease / claim limit | 10 s / 50 rows | Plan Δ6 `claim_outbox(owner, now, lease, limit)` parameters (not separately named in the plan) | PROPOSED, fixture only |
| RQ `failure_ttl` / `result_ttl` | 60 s / 0 | Δ14 “short `failure_ttl`”, `result_ttl=0` | PROPOSED, fixture only |
| Attempt policy | Reuse `fixture.job_retry.v0` unchanged: 3 attempts, backoff 1000 ms × 2 up to 8000 ms, attempt timeout 30000 ms | Phase A frozen code. Consistent with SRS `VIDEO_RETRY_BUDGET` (2 auto retries, PROPOSED) but not an adoption of it | PROPOSED (existing) |
| Poll policy | Reuse `fixture.job_poll.v0` unchanged: 2000–10000 ms, 10 s step | SRS `JOB_POLL_MIN_INTERVAL` 2 s PROPOSED | PROPOSED (existing) |
| `IDEMPOTENCY_TTL` | SRS 86400 s, PROPOSED | No B-01..B-12 check depends on its expiry | PROPOSED (SRS) |

SRS `CAPABILITY_TTL` (3600 s) belongs to the participant/session capability, not to the worker
capability, and is not reused here. None of these values is a production default.

## 6. G2 — Phase B approval (APPROVED by actual O-09)

Actual user reply accepts rev8 §13 and approves planrev3 B1–B6. The complete real reply is
recorded verbatim in approvals/PHASE_B_TASK_APPROVAL.md. G1–G5 are satisfied for component scope;
first Claude code turn B2 only, review before B3. The original checklist/sample below is retained
as historical preparation; the sample is not the approval.

Preconditions before the user can validly approve Phase B code:

1. G1-TASK decided (with G1-LIVE run as 1 passed/0 skipped, or a recorded deviation).
2. G3-D1…D7 + G3-LOC decided, and the adopted ADR written at the chosen path (path + sha256 known).
3. G4-Q1…Q8 answered as ROLE_OWNER_RECORD, or as an explicit PROJECT_OWNER_DIRECTIVE recorded as
   such. For Q8, a directive must explicitly adopt/assign the versioned component contract and
   accept the ASSUMED_CONTRACT proof; it does not establish P2 concurrence or real integration.
4. G5-ENV/INV/SECRET/PROFILE decided; inventory receipt captured before the first runtime test.
5. If any alternative was chosen: plan revision 4 + focused review PASS first; the approval then
   names that revision instead of revision 3.

Proposed approval location: a **separate** `approvals/PHASE_B_TASK_APPROVAL.md`, written only when
the user actually sends an approval with this scope and the preconditions hold. The Phase A
`approvals/TASK_APPROVAL.md` is not modified. Nothing in this record, the prompt or this turn is
an approval.

Sample approval text — **MẪU, KHÔNG PHẢI APPROVAL**:

```text
Tôi duyệt BE2-01 Phase B theo features/FEAT-044-be2-ai-job-foundation/plan/PHASE_B_PLAN.md
revision 3 (sha256 bb20d5be…74ba5848), batch B1–B6.
Phase A checkpoint: <quyết định G1-TASK + nguồn/ngày>.
ADR D1–D7 đã adopt tại <đường dẫn ADR + sha256> (từ PHASE_B_ADR_PROPOSAL.md revision 3).
Câu trả lời P2/P4 Q1–Q8 (gồm owner-fence Q8) tại plan/PHASE_B_DECISION_RECORD.md revision <n>
(sha256 <…>), dựa trên PHASE_B_PORT_REVIEW.md revision 3.
Môi trường: <môi trường synthetic G5-ENV đã được phép>, inventory <receipt>, secret theo
<cơ chế G5-SECRET>. Profile test: fixture.durable_jobs.v0 (PROPOSED, chỉ fixture).
Không gồm live router, provider/model, durable ProviderCopyLifecycle, BE1 tables/fence
implementation, production policy, commit/push/deploy.
```

## 7. Decision log (actual inputs, verbatim)

Actual user replies are quoted verbatim below. Interpretation is listed separately; it is not
presented as a longer quote, role-owner concurrence or blanket approval.

| Date | Row IDs | Record type | Person / role | Verbatim decision | Source |
|---|---|---|---|---|---|
| 2026-10-15 | O-01: D1–D7, fixture profile, test-first path | PROJECT_OWNER_DIRECTIVE | User / project owner | **Ổn đó** | This Codex chat, reply immediately after the concrete alternatives/recommendation |
| 2026-10-15 | O-02: G5 environment inventory | PROJECT_OWNER_DIRECTIVE | User / project owner | **Chưa rõ; cần kiểm kê môi trường hiện có** | This chat, answer to the PostgreSQL17/Redis environment question |
| 2026-10-15 | O-03: new separate CPU Studio | PROJECT_OWNER_DIRECTIVE | User / project owner | **tên gì ? g coi như tạo mới lun đi** | This chat, following recommendation to separate FEAT-018 and backend test Studios |

| 2026-10-15 | O-09: G1/G2/G3/G4/G5 component scope | PROJECT_OWNER_DIRECTIVE | User / project-task owner | Full actual reply preserved verbatim in approvals/PHASE_B_TASK_APPROVAL.md | This Codex chat; explicit Phase A acceptance, rev8 §13 acceptance and planrev3 B1–B6 approval |

### O-01 interpretation and limits (historical scope of O-01/O-02 only)

The immediately preceding recommendation was: preferred D1–D7, strong fence with fixture first,
run the missing Phase A test, retain the current fixture test profile; select E1/E2 according to
actual infrastructure. The owner accepted that package. This records the architecture/profile
choice; it does not invent answers to the detailed Q2–Q7 questions or the rest of Q8.
O-02 explicitly leaves the environment unknown and requests inventory only.

- Selected ADR: `docs/adr/ADR-0018-be2-durable-ai-job-runtime.md`.
- No Phase A acceptance, test deviation, runtime PASS, production adoption, install/start, remote
  access, cloud spending, contact with role owners, Phase B code approval, commit or push follows
  from these replies. Historical proposal/review hashes are kept as dated evidence.

## 8. Current execution gate summary — after actual O-09

- G1 Phase A candidate/fixture checkpoint ACCEPTED; missing live-route1 passed,0 skipped remains
  PASS_USER_REPORTED. P1/P2/P4 actual role concurrence and production adoption remain deferred.
- G2 planrev3 B1–B6 APPROVED, separate verbatim approval file; first Claude code turn B2 only,
  review before B3. Do not ask again for unchanged authorized routine scope.
- G3 ADR-0018/D1–D7 accepted; G4 Q1–Q8 accepted as PROJECT_OWNER_DIRECTIVE including versioned
  OwnerFenceV1 0.1-candidate and ASSUMED_CONTRACT proof, never P2 role sign-off.
- G5 named synthetic Studio/key mechanism/profile authorized; baseline inventory/connections
  are user-reported. Migrations, durability, fault/concurrency and real integration remain unproven.
- B1 CLOSED_COMPONENT_SCOPE after diagram reconciliation; ACTIVE Q01/B2 READY_FOR_CLAUDE,
  backend code NOT_STARTED, WIP1/cards14/full-cardDONE0. Parent BE2-01 remains IN_PROGRESS.
- Exact next work order: plan/CLAUDE_PHASE_B_IMPLEMENTATION_PROMPT.md. Later dated inventory
  entries preserve their original state and are superseded by this summary/O-09 where applicable.

## 9. Local read-only inventory result (O-02)

Inventory is local Windows only: Python3.12.10 and declared database/queue client packages are
present; Pillow is absent. Service metadata reports postgresql-x64-18 RUNNING, not a verified
PostgreSQL17 target. Docker CLI29.5.3 exists but neither tested local engine pipe was available;
Docker Desktop service was stopped. No redis service/client was found by the checks used; this
does not prove absence of every Redis process. WSL and listener enumeration were access-denied
in this session, so Linux availability and listening ports are unknown. No server login,
secret/config values or business data were read.

G5 target remains NOT_VERIFIED. No named LightningAI/remote Linux environment was supplied or
inspected. Existing access/target information is needed to inventory there. Next Claude handoff:
`plan/CLAUDE_PHASE_B_ENVIRONMENT_INVENTORY_PROMPT.md`. Raw inventory stays feature-local under
`evidence/local/phase-b-owner-selection-20261015/`; public checks contain only the safe summary.

## 10. New Studio selection (O-03)

The user selects a new CPU Studio instead of reusing FEAT-018. The routine proposed name is
`sketch2life-backend-test`, intended for synthetic BE1/BE2 component/integration tests. Treat
Studio creation as requested, not completed: this session has no Lightning connector/CLI or SDK
available, and no authenticated target/teamspace was supplied. No remote resource was created.
User can create the named CPU Studio via the Lightning dashboard; capture its actual target and
inventory next. Do not switch or modify the FEAT-018 Studio/Wan environment.

This changes the environment choice from unknown to new-CPU-target selected; it does not establish
PostgreSQL17/Redis availability, setup completion, G1 test PASS, remaining port contracts, production
policy or Phase B code approval. Server provisioning remains to be made concrete in the new target.

## 11. User-reported Studio inventory (O-04, 2026-10-15)

After reporting the new Studio created, the user pasted terminal output: Linux6.8.0-110-generic
x86_64, Python3.14.7, git and Docker client/server28.0.1. The docker ps output contains no running
container rows; stopped containers were not checked. This is user-supplied remote evidence, not
a direct Codex remote inspection. Full safe summary in evidence/notes/PHASE_B_ENVIRONMENT_RECORD.md.

Backend pyproject requires Python>=3.12,<3.14; keep host Python untouched and use the existing
Dockerfile baseline python:3.12-slim for an isolated runner. Next obtain the published BE2 source,
verify branch/commit and runner version. PostgreSQL17/Redis provisioning, actual dependency
inventory and Phase A test remain pending. No B2 implementation approval is supplied by output.

## 12. O-05/O-06 partial setup evidence

See evidence/notes/PHASE_B_ENVIRONMENT_RECORD.md for user-reported Python3.12.15 runner success,
PostgreSQL17.11/Redis healthy output and image digests. Git branch/log was invoked outside a
checkout; source branch/commit remains unresolved. Do not recreate the healthy services. Next
verify source, then install backend dependencies and prove authenticated runner connectivity and
the missing Phase A test. This is environment progress, not Phase A acceptance or Phase B approval.

## 13. Accepted component decision packet (approved revision8 §13)

Status: **ACCEPTED_PROJECT_OWNER_DIRECTIVE — actual O-09,2026-10-15**. The user explicitly
accepted revision8 §13 and approved planrev3 B1–B6. The following packet content retains its
accepted semantics. It records project-owner component decisions, never P1/P2/P4 sign-off.
The original revision8 is byte-preserved locally; exact actual reply is in the separate approval.

### Phase A checkpoint and evidence

Accepted by actual O-09: Phase A at candidate/fixture scope based on the existing independent code review
and the now-passed missing live-route test. Accept the recorded P1 payload/state/projection,
P2 candidate ports and P4 candidate names/namespace/composition as project-owner fixture decisions;
production registry/adoption and actual role-owner concurrence/integration stay deferred. Do not
label this project-owner directive as a genuine P1/P2/P4 sign-off or a completed live integration.

### Accepted Q1–Q8 component answers

| ID | Accepted project-owner component directive | Proof/ownership limit |
|---|---|---|
| Q1 | PostgreSQL17, AI-owned schema ai_jobs, existing backend/alembic env + ai_jobs branch alongside be1_core. Use schema-qualified names and preserve BE1 migration/history. | Disposable synthetic DBs for tests; no BE1 table writes or production migration |
| Q2 | Synchronous authorization contract carries a grant epoch; revoke changes that epoch so later stale acceptance fails its fence. | Test owner fixture; no actual BE1 auth adapter claim |
| Q3 | Cancellation notices at-least-once after the owner decision/epoch transaction commits, idempotent notice_id. | Component fixture delivers/redelivers after commit; actual BE1 transport/outbox integration is B-12 |
| Q4 | Artifact descriptor has org/job/attempt lineage and state fence; QuarantineIntent uses exact stored event_id with sink dedup, owned refs only. | Component fixture/sink; actual artifact persistence/adapter remains owner integration |
| Q5 | Durable BE2 audit outbox, at-least-once delivery with deterministic event_id dedup; audit-only incident transaction before response. | Component sink proof, not actual BE1 audit storage/integration |
| Q6 | Test entrypoints/processes for dispatcher, reconciler and worker with fake provider. Test coordinator creates one ephemeral HMAC key per test run, shares it with all required child processes and preserves it through their restarts within that run, without logging/persisting it. DB secret keeps the observed private-file mechanism. | INTG-02 owns production wiring/key provisioning; no live API or provider |
| Q7 | Use sketch2life-backend-test, isolated Python3.12 venv and dedicated PostgreSQL17/Redis8; module migration order follows the existing dependency graph in the one Alembic env, preserving BE1 history. | B2 records/tests exact commands on disposable databases; routine graph/command choices are implementation work, not a new owner question |
| Q8 | Adopt OwnerFenceV1 0.1-candidate for the component assumption: consent/purpose, session/context, recall/source-expiry/kill-switch, grant and artifact-state scopes carry epochs; owner bump FOR UPDATE + decision + notice in one transaction; BE2 hold FOR SHARE on the same UoW connection through commit. P2 owns future rows/function, BE2 owns connection/transaction and never writes P2 rows. | ASSUMED_CONTRACT fixture allowed before actual P2 adapter; no P2 concurrence or real B-12 integration inferred |

### Accepted environment/code scope

Use this selected Studio only for synthetic component setup/tests, no provider/model/media or
production data. Retain the already selected fixture.durable_jobs.v0 profile. User-reported
inventory/test evidence remains labelled as such; Phase B B-01..B-12 runtime proof is still future.

Actual O-09 accepts this packet and approves PHASE_B_PLAN.md rev3 B1–B6. The real reply is
recorded verbatim in approvals/PHASE_B_TASK_APPROVAL.md, preserving Phase A TASK_APPROVAL.md.
The accepted component answers are PROJECT_OWNER_DIRECTIVE; role sign-offs are not fabricated.
The test scope includes selected source/test synchronization to the named Studio only, without
secret/media/data transfer or commit/push/deploy. First Claude implementation turn is **B2 only**,
followed by evidence and review before B3. Do not ask again for unchanged approved scope.

## 14. O-09 — actual acceptance, approval and B1 reconciliation

Source: explicit user message in this Codex chat,2026-10-15. Full reply is preserved verbatim in
approvals/PHASE_B_TASK_APPROVAL.md; record type PROJECT_OWNER_DIRECTIVE, actual role concurrence absent.
Approved snapshot is revision8 with sha2560d5fdbfd783ddde3c08e739c23fe936784be73bcf8cb43dddf079dffde67164f.

B1 closure compares every accepted Q1–Q8 decision against the reviewed seven sequences/twelve
crash windows: no behavior mismatch or alternative requiring plan amendment. Q6 key sharing
is operational test setup; A5's original pre-decision repository observation is historical.
Details: evidence/notes/PHASE_B_B1_CLOSURE_AND_HANDOFF_20261015.md and diagrams §14.

ACTIVE Q01/B2 READY_FOR_CLAUDE; backend code NOT_STARTED. Exactly14 cards, WIP1, parent
BE2-01 IN_PROGRESS/full-cardDONE0. Runtime/provider/real B-12 integration proof remains future.
