# Cross-lane foundation-owned UoW for BE2-01 / BE2-07 / BE2-08 — scope revision 3 draft

- Status: DRAFT / OWNER_DIRECTION_RECORDED / READY_FOR_INDEPENDENT_REREVIEW
- Prepared: 2026-10-21 (Asia/Saigon)
- Owning card for foundation transaction: BE2-01 / FEAT-044
- Participants: BE2-08 / FEAT-050 video rows; BE2-07 / FEAT-056 producer currentness only under a separately approved durable fence
- Supersedes for review only: CROSS_LANE_FOUNDATION_UOW_SCOPE_REV2_DRAFT_20261021.md
- Parent SHA256: 39B0FD5958D2C298460F7605A7F73E8BDC7BC9D269B6399822FD2A2EAAC4DDC4
- Related FEAT-057 erratum: CROSS_LANE_X01_X05_PLAN_ERRATUM_20261021.md
  SHA256 7530294B18B30616EB9A968ABF0AD227C661294500CD0789A7EC514D54E5FE39
- Source snapshot hashes: features/FEAT-057-be2-01-14-offline-integration/evidence/metrics/CROSS_LANE_UOW_SOURCE_HASHES_20261021.json
  SHA256 88368265E8EE262F7DA6DEC23F3DAB6C749F482016EC79AA69F40B186DD5B92F
- Candidate branch/HEAD: feature/be2-backend-ai-integration / 1649b72978877d82b4d7662040ff3555dee0a3a7; source worktree was dirty and is identified by the per-file hashes above.

This revision incorporates the independent review verdict CHANGES_REQUIRED and the owner's D1 selection A with the added conditions recorded in `features/FEAT-057-be2-01-14-offline-integration/evidence/notes/CROSS_LANE_UOW_OWNER_DECISION_D1_20261021.md`. It is still a design/scope draft, not implementation approval, adopted cross-card contract, card acceptance, or runtime evidence. S and F have an owner-selected direction, but still require independent review and separate supplemental approvals for affected card scopes before code. Existing approved addenda and approval files remain byte-frozen. No source, test, schema, migration, card status, or acceptance change is authorized by this document.

## Owner-directed design, with limits

1. BE2-01 owns and opens the foundation UoW for submission, start, successful finalization, retry, failure, cancellation, timeout, reconciliation-driven transitions, outbox-driven job transitions, and rejection. BE2-08 participates only for its owned video rows; it cannot begin, commit, or roll back the foundation transaction.
2. Submission and successful finalization are separate commit boundaries, with external generation between them. Start and F lifecycle transitions use their own BE2-01-owned UoWs. No transaction remains open over provider, media, or model work.
3. The BE2-07 source fence is required inside the successful finalizer boundary only if source-currentness rows and all relevant invalidation writers can serialize on the same transactional store. A read/revalidation alone is not a held fence. With current source and approved scope, X01 is PARTIAL by default.
4. Keep WorkerDispatchEnvelope unchanged. Resolve job, attempt, video run, and source-pin identity from authoritative persisted records; fail closed if the exact relationship cannot be established. No mapping is yet adopted.
5. BE2-08 is directed to publish a read-only finalized-artifact model for BE2-09. Its exact fields, visibility, read-after-commit and supersession rules belong to a separate BE2-08 scope supplement.
6. BE2-14 eligibility, execution authorization, and budget/concurrency remain separate. Owner budget unit/limit are pending; reservation expiry/renewal requires a versioned CR. No budget value or provider permission is inferred.

These directions do not establish an adopted durable fence or complete lifecycle contract. X01 remains PARTIAL by default; X05d remains BLOCKED; X05c/CR09-02 remains OPEN; X09-08 remains NOT_IMPLEMENTED until persisted-job composition is proved.

The owner's selection A is a design disposition, not implementation approval. Every reconciler or outbox dispatcher that changes a foundation job in a paired BE2-08 lifecycle must call the BE2-01 UoW path with the BE2-08 participant. It may not update the job alone and leave the run behind. A rejected finalization writes its quarantine/cleanup intent in a separately committed reject boundary through the existing foundation quarantine-intent path; rollback is not used to preserve that intent. A finalization rollback is reserved for infrastructure failure and must have an explicit idempotent recovery path. Boundary S and F remain subject to independent review and separate supplemental approval.

## Source facts pinned for this review

The review used the exact source bytes listed in the companion hash manifest, not HEAD alone:

- The foundation SQL repository opens one PostgreSQL connection at READ COMMITTED and holds its OwnerFencePort lock through that UoW. The existing port's FOR SHARE behavior proves only a fence implementation that shares those rows and that connection; it does not create a BE2-07 adapter.
- BE2-07 resolve_exact opens its own transaction. Currentness depends on multiple facts, including bundle head/version, basis/context, audience, policy reference, catalog claims, and source records. The existing BE2-07 scope has no SQL store and excludes a real cross-service lock or new schema/migration.
- VideoRunRows accepts a caller-supplied SQLAlchemy connection, writes BE2-08-owned rows, and does not commit. Its persisted run has a unique organization/job relationship and stores its source pin in the run record. No durable create route/factory is supplied.
- Foundation request_ref contains request identity/revision, input hash, and context revision; WorkerDispatchEnvelope does not directly carry a video run or source pin. No rule proves input_hash equals pin_digest or request_id equals video_id.
- VideoRun.start changes run lifecycle and records attempt identity. Worker/finalizer ports also require durable cleanup intent for rejected output.
- BE2-14 accounting opens its own transaction. Reservation currently has no expiry field.

These observations are source facts for this dirty snapshot, not SQL conformance, contract adoption, or proof that all rows share one store.

## Lifecycle boundary matrix

The owner selected model A. The table records the required direction, while exact enum names, row manifests, CAS predicates, receipt ownership, and retry policy remain CR08-01 implementation details that require independent review and separate supplemental approval. A participant only mutates BE2-08-owned rows on the connection/UoW supplied by BE2-01; the participant cannot begin, commit, or roll back.

| Boundary | UoW owner and callers | Rows enlisted (each owner writes only its rows) | Required paired job/run CAS | Recovery point |
|---|---|---|---|---|
| A — submit | BE2-01 opens/commits. BE2-08 joins as participant. | BE2-01: job, initial attempt, dispatch/outbox, idempotency/replay receipt. BE2-08: initial run and video receipt. Any creation lease must be specified as enlisted or an explicitly separate guard. | Insert one `queued` job/attempt and one `queued` video run bound to the same organization/job and initial attempt; create-if-absent/unique constraints must make the pair all-or-nothing. Exact run/replay identity is frozen in CR08-01. | On unique conflict, roll back the entire UoW and perform authoritative replay lookup in a new transaction. On lost acknowledgement, read the durable receipt in a new transaction; never create a second run or dispatch based on guesswork. |
| S — start/admission | BE2-01 opens/commits. Worker, reconciler, and dispatcher call this boundary; BE2-08 joins only as participant. | BE2-01: job and active attempt. BE2-08: run start state and matching attempt identity. | CAS job `queued → running` and video run `queued → running` for the same attempt ID/number. Both must win or neither authoritative transition commits. | After crash/lost acknowledgement, recover by reading the persisted job, attempt, run, and receipt in a new UoW. A mismatched/missing pair fails closed; duplicate delivery cannot create a second start for the same attempt. |
| B — successful finalization | BE2-01 opens/commits. Finalizer calls this boundary; BE2-08 joins only as participant. | BE2-01: job completion, attempt result, finalization receipt, required outbox/audit rows. BE2-08: terminal run and immutable artifact row. Source-fence locks join only if a separately adopted same-store fence exists. | CAS job `running → succeeded` and video run `running → succeeded` for the exact winning attempt, with one exact artifact identity. The pair and receipt commit together. | Lost acknowledgement resolves by receipt lookup in a new UoW. A stale/late attempt loses CAS and cannot overwrite the winner. Infrastructure rollback leaves no accepted artifact and enters the explicit idempotent recovery path; no transaction spans external generation. |
| F — failure, cancel, timeout, retry, reject | BE2-01 opens/commits every paired transition. Reconciler/outbox dispatcher must use this route and may not update a job without the BE2-08 participant. BE2-08 joins only for its rows. | BE2-01: job, attempt, retry/outbox, and—on a rejection—the existing foundation quarantine-intent record. BE2-08: matching run state and attempt. Include source-fence rows only when the operation actually acquires them under the common order below. | Fail/timeout CAS job and run for the same attempt to `failed_retryable` or `failed_exhausted` per the existing retry policy; cancel CASes both to `cancelled`. Retry CASes the paired `failed_retryable` attempt to a new `queued` attempt ID/number on both records. For a current-attempt rejection, use the existing foundation terminal state/reason and matching video `generation_state`; do not invent a `rejected` JobState. For already-terminal, cancelled, or superseded output, preserve the authoritative job/run state and CAS no state transition. The quarantine-intent insert is separately committed in either case. | Retry/timeout/cancel reconcilers repeat idempotently through BE2-01 UoW. Lost acknowledgement is resolved from durable job/run/attempt/intent receipts in a new UoW. A failed reject commit leaves the result durably unhandled and retryable; it does not claim successful finalization. Rollback is only for infrastructure failure; its recovery is explicit and cannot depend on an intent inside the rolled-back transaction. |

### Shared lock order and deadlock handling

The selected lock order for this scope is **foundation job row → BE2-08 video-run row → source-fence rows in stable canonical-key order**. Every transaction that locks more than one of these rows must follow it. F paths that do not need source-fence rows use the same order as a prefix (job then run); they must not acquire a fence and then reach back for job/run. The independent reviewer must verify that all existing and proposed writers can follow this order. The existing foundation repository also owns attempt/outbox records under the parent job lock. CR08-01 must pin how those records are read/written without acquiring an outbox/attempt lock before the job/run/fence sequence; in particular, an outbox delivery lease must not be held while waiting to enter the paired transition UoW. If the creation lease is a transaction-held row, CR08-01 must place it after the fence rows and require every multi-row writer to use that same order; if it remains a separate guard, its acquisition/release is not claimed atomic with A/B/S/F. All lock waits, deadlocks, unknown fence rows, or unavailable owner data fail closed or leave the transition pending; they never convert missing currentness into success. The source-fence protocol and its PostgreSQL race evidence remain future gates, not authorization to run a database now.

Reconciler and outbox-dispatcher paths are part of S/F: they must call the BE2-01 orchestration/UoW route for any job mutation and enlist the matching BE2-08 run participant. A job-only timeout, retry, cancel, or failure update is forbidden by this scope direction.

The reject commit is distinct from a successful finalization commit. “Existing foundation quarantine-intent path” refers to the foundation `AiJobUnitOfWork.add_quarantine_intent` and its durable side-effect outbox/delivery path. Current completion code writes this intent in its own completion transaction; the selected design requires a distinct BE2-01-owned reject transaction that reuses the foundation writer/delivery path. It does not claim that a standalone reject API already exists. For a business/policy rejection, commit the reject intent before reporting it as durably handled. Where the current attempt is still authoritative and a terminal job/run transition applies, pair its existing foundation `JobState` CAS with the matching video `generation_state` CAS in this reject UoW; for already-cancelled, terminal, or superseded output, preserve the state and commit only the idempotent intent. Do not invent a `REJECTED` job state and do not rely on rolling back B to retain an intent. A B rollback is only for infrastructure errors and must be recoverable from persisted state/retry metadata; the exact retry owner and idempotency receipt remain to be specified in CR08-01.

The FEAT-057 slice plan revision 4 and its current erratum predate this D1 selection: their lifecycle text leaves S/F pending and limits the owner-directed atomic boundaries to A/B. This revision does not silently amend that plan. Independent review must identify whether a successor slice-plan revision or another erratum is required and enumerate the exact clauses to align before implementation approval.

External generation occurs only after A commits and before B begins. No transaction spans generation.

## Job, attempt, run, and source-pin mapping

Candidate lookup starts with the persisted foundation job_id and resolves the unique BE2-08 run row by organization plus job_id. The composition must then verify persisted organization, session/subject, request ID/revision, attempt ID/number, source bundle/version/hash, audience/context, and idempotency identity against their owning records.

Do not treat request_id, input_hash, pin_digest, video_id, or run ID as interchangeable without an adopted field-level rule. The BE2-08 run-owned pin and foundation request_ref must be linked and checked in both directions using an explicit rule. If the stored foundation data cannot prove the exact source pin or the run relationship, fail closed and keep X09-08 NOT_IMPLEMENTED. If a new persisted linkage is required, prepare a versioned CR under the owning card; do not add it to the broker envelope by assumption.

## Source-fence protocol and current blocker

A candidate held fence would require all of the following:

1. Inventory each currentness input: bundle head/version, basis/context, audience, policy reference, catalog claims, and each source record/version/hash. For every input name its owner, persisted fence key, and every invalidation writer.
2. Demonstrate that the finalizer, BE2-07 currentness owner, and every invalidator use the same PostgreSQL database and transactionally visible fence rows. A same-store read without a lock/CAS is insufficient.
3. Before final CAS, the finalizer acquires FOR SHARE on every fence row using the same connection as the foundation UoW and holds those locks until commit. Every invalidator uses FOR UPDATE on those same rows or CASes the same monotonic epoch.
4. Define deterministic lock order across source fences, job row, video run, and any creation lease. Define lock timeout/deadlock handling as fail-closed or pending; never convert an unavailable fence to current.
5. With two PostgreSQL sessions, test both orders: invalidation wins first and finalization commits no output; finalization wins first and the invalidator cannot pass the locked fence until final commit. A process-local coordinator or SQLite test does not prove this.

This is not achievable under the reviewed BE2-07 source and approved addendum: resolve_exact has an independent transaction, BE2-07 has no SQL persistence in the approved scope, and a new cross-service fence/schema is excluded. Therefore current X01 result is PARTIAL. Only a separately revised and approved scope from BE2-07 plus all owners of the currentness rows can change that result. If no shared store/fence is available, keep X01 PARTIAL and stop; do not substitute a last-moment read.

This fence orders finalization against invalidation at that commit only. It does not provide the post-commit current-use resolver required for X05d or implement X02 delivery.

## Composition adapter and recovery ownership

- BE2-01 owns the foundation UoW provider and its transaction-scoped enlistment API.
- BE2-08 owns VideoRunRows and its state transitions.
- FEAT-057 owns cross-lane composition adapters/tests under its separately approved integration scope. Candidate adapter path is backend/src/sketch2life/infrastructure/cross_lane/knowledge_video.py; this path is not yet approved.
- Keep SQLAlchemy connection details in infrastructure; do not add a SQL connection to an application protocol.
- Apply the shared order in this revision: foundation job → BE2-08 run → source-fence rows in stable key order. Confirm whether a creation-lease row is enlisted after those locks or remains a separate guard; no writer may invert the order.
- On a PostgreSQL unique conflict, roll back the entire transaction. Resolve replay from the authoritative receipt in a new transaction; never continue querying in the failed transaction.
- Specify whether the existing creation lease is enlisted in A or is acquired/released separately. If separate, it is not part of the atomic commit.
- Lost acknowledgement with an unavailable authoritative lookup remains pending; do not resubmit or regenerate based on a guess.

## BE2-08 read-only artifact model is a separate scope

The direction to publish a read-only finalized-artifact model belongs to FEAT-050/BE2-08. It is not a BE2-01 UoW acceptance criterion and is not implemented by this draft. Before FEAT-051/BE2-09 consumes it, BE2-08 must approve the exact identity fields, organization/session/principal access rules, read-after-commit behavior, immutable hash/version semantics, and stale/superseded behavior. See features/FEAT-050-be2-knowledge-video/plan/CROSS_LANE_BE2_08_ARTIFACT_READ_MODEL_SCOPE_DRAFT_20261021.md. Until both sides adopt it, CR09-01 is blocked and X05 does not advance.

## BE2-14 boundary

The BE2-14 ledger transaction is separate from the foundation UoW today, and Reservation has no expiry field. Do not claim budget reservation is atomic with A, S, B, or F. Owner budget unit/limit, reservation timing, expiry/renewal CR version, settlement, retry, lost-ack and recovery semantics remain pending. Any offline budget values must be labeled synthetic in tests/evidence and cannot authorize provider work. Eligibility, worker execution authorization, and budget/concurrency remain distinct fail-closed gates.

## Acceptance evidence proposed for a later approved scope

| ID | Required evidence |
|---|---|
| U01 | Foundation owns and opens each approved UoW; BE2-08 can mutate only owned rows and cannot commit the enclosing transaction. |
| U02 | A, S, B, and F lifecycle cases use the paired owner-selected job/run CAS where a transition applies; failure injection proves no split authoritative state. Business reject intent is separately committed; rollback never acts as intent storage. |
| U03 | External generation occurs between commits; no database/UoW remains open during provider/media work. |
| U04 | Same-key replay, changed-body conflict, duplicate delivery, unique-conflict rollback/new-transaction replay, lost acknowledgement, and unavailable receipt are explicit tests. |
| U05 | Persisted job_id → run row → source pin mapping is verified against owner records; missing or mismatched identity fails closed; envelope unchanged. |
| U06 | The complete source-fence inventory, lock/CAS protocol, lock order and two-session PostgreSQL races are proven. Without this, X01 remains PARTIAL. |
| U07 | Late-result winner is enforced by attempt/revision CAS; reject intent survives independently of finalization rollback via a separate foundation reject commit; infrastructure rollback has a tested idempotent recovery route. |
| U08 | BE2-08 artifact read contract is separately adopted; BE2-09 never writes BE2-08 state. |
| U09 | BE2-14 gates remain distinct; unprovided budget values are never presented as owner limits or provider permission. |
| U10 | Fake/unit evidence is labeled as such. SQL race tests not run are NOT_RUN; no fixture or Modal result is called durable transaction proof. |
| U11 | Card status and acceptance remain unchanged; X05d BLOCKED, X05c/CR09-02 OPEN, runtime/provider/Modal/Lightning NOT_RUN. |

Candidate test names, to be frozen only in approved manifests:
- backend/tests/unit/test_ai_job_video_uow.py
- backend/tests/integration/be2_cross_lane/test_video_uow_boundaries.py
- backend/tests/integration/be2_cross_lane/test_video_source_fence_postgres.py

The PostgreSQL race suite is a future evidence requirement, not authorization to provision or run a database now.

## Candidate ownership and file boundary

This is a candidate boundary for review, not permission to edit every path.

- BE2-01 foundation UoW candidates: backend/src/sketch2life/application/ports/ai_jobs.py; backend/src/sketch2life/application/services/ai_jobs.py; backend/src/sketch2life/infrastructure/ai_jobs/sql/repository.py; backend/src/sketch2life/infrastructure/ai_jobs/fakes.py; backend/tests/unit/test_ai_job_application.py; new exact tests only after manifest approval.
- BE2-08 participant candidates: backend/src/sketch2life/application/knowledge_video_create.py; backend/src/sketch2life/application/knowledge_video_worker.py; its owned ports and infrastructure/knowledge_video/sql.py; its owned tests. Read-only artifact model is a separate FEAT-050 supplement.
- FEAT-057 composition candidates: backend/src/sketch2life/infrastructure/cross_lane/knowledge_video.py and backend/tests/integration/be2_cross_lane/test_video_uow_boundaries.py. Exact manifest requires a FEAT-057 scope revision/approval.
- BE2-07 source fence: current approved scope excludes SQL persistence, schema/migration and real cross-service lock. No implementation candidate is authorized until a revised FEAT-056 scope names exact owner-owned paths and tests.
- BE2-14 reservation expiry/renewal: separate versioned CR, owner budget inputs and a separate manifest/approval are required.
- No BE2-09 consumer source change until the FEAT-050 artifact contract is adopted and FEAT-051 freezes its own manifest.

Any schema, migration, shared contract, or file outside an approved minimal manifest stops implementation for a revised scope and approval. Never edit an existing published migration.

## Open owner/card decisions before scope approval

1. Independently review the selected A/S/B/F lifecycle model, paired CAS/state table, reject commit, recovery points, and lock order; settle exact enum names, receipts and lease placement in CR08-01 and per-card supplemental scopes.
2. Confirm the job_id → BE2-08 run lookup plus the persisted field-level rule that binds foundation request_ref to the run's source pin. If existing fields do not express it, prepare a versioned CR, not an envelope edit.
3. Keep X01 PARTIAL under the current BE2-07 approval unless a separate scope for shared-store fencing is reviewed and the same-store protocol is proven.
4. Review the BE2-08 artifact-read supplement separately before BE2-09 implementation; exact fields and access/supersession rules remain to be selected.
5. Supply BE2-14 budget unit/limit and decide reservation timing/settlement/recovery only through its versioned CR.
6. Reconcile this successor scope with FEAT-057 slice-plan revision 4; review whether a new plan revision or erratum is needed. Until that is resolved, do not call the two documents aligned.

After these decisions, revise/pin the exact card-owned manifests and obtain supplemental approval in each owning card. Existing approvals do not cover this UoW or any new fence/read-model contract.

## Offline-only sequence after approvals

1. Close CR08-01 with the A/S/B/F lifecycle model, transaction owner/participant rules, row/receipt scope, deterministic lock order, unique-conflict recovery, lost-ack and late-result semantics.
2. Resolve persisted job/run/source-pin identity from owning records without changing WorkerDispatchEnvelope.
3. Decide source-fence feasibility. If the shared transactional store cannot be adopted, record X01 PARTIAL and omit the claimed held fence.
4. Separately adopt the FEAT-050 read-only artifact model before BE2-09 CR09-01 work.
5. Resolve BE2-14 phase and reservation CR using owner-supplied budget inputs; keep provider generation gated.
6. Freeze per-card minimal manifests and approvals before source edits. Run offline tests first; report SQL/database/provider/runtime evidence separately and as NOT_RUN when not executed.
7. Obtain independent code review, fix findings, and rerun affected offline checks. Component acceptance remains a separate owner decision.

## Approval state

No implementation approval exists for this revision. It is ready only for another independent scope review. Owner selection A and its conditions are design direction only. They do not modify FEAT-057 slice-plan revision 4, existing card scope approvals, TASK_APPROVAL records, source/tests, schema/migrations, card status, acceptance, publication, Modal, Lightning, provider, server, database, or runtime authority. S and F require independent review and separate supplemental approvals in the owning records before implementation. X01 remains PARTIAL; X05d remains BLOCKED; X05c/CR09-02 remains OPEN; budget unit/limit remain unprovided; runtime/Modal/Lightning/provider work remains deferred.
