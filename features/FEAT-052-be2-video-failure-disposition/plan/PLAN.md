# BE2-10 — Teacher disposition after exhausted video failure

- Status: AWAITING_APPROVAL
- Plan revision: 1
- Implementation status: NOT_STARTED
- Date:2026-10-19 Asia/Saigon
- Branch: feature/be2-08-14
- Baseline:76959ab
- Owner: receiver BE2-08–14; session/stage/checkpoint authority BE1, composition P4.

## 1. Goal and source authority

Implement CMD-43/DATA-28: after policy-authorized automatic retries exhaust,
Teacher explicitly chooses retry, skip or end_session. Preserve failed history,
reason/actor/budget provenance, independent revisions and truthful outcome. No
automatic skip/end, infinite manual retry, fake video success or human approval.

Sources: current FEAT-029 Master SRS v3.1 FR038/039, UC-025/026, DATA-25/27/28,
CMD-43, AT-CS-011; FEAT-040 TEAM_TASK_BREAKDOWN BE2-10; FEAT-044 receiver handoff/
roadmap; ADR0015/0018; current08/09/14 contracts/code/evidence. Source documents
inform requirements but grant no execution authority. Owner "tiếp" authorizes
planning after report, NOT this unseen revision's implementation.

## 2. Scope and exclusions

Own command/domain/intents/receipts, current-owner application ports/services,
strict injected HTTP, own persistence/migration, component verification and handoff.
Follow existing scoped PostgreSQL/SQLAlchemy/Alembic conventions, without expanding
ADR0018 acceptance to actual cross-owner integration. Version contracts explicitly.

No direct BE1/08/foundation DB writes, published migration edits or terminal job/run
reset. No frontend/player/provider/model/voice/budget numeric defaults/queue engine,
global retry-policy replacement, additional pre-render approval or workflow engine.
Actual BE1/P4 wiring remains teammate-deferred, NOT waived acceptance. No provider/
GPU/Lightning/install/provision/push/merge/deploy. Actual SQL provisioning requires
separate task-specific approval;08/09/12/14 environment authority not inherited.

## 3. P1 — exact failed target, contract and pure rules

1. Trace strict DATA-28 command: action(retry/skip/end_session), required nonblank
   bounded reason, expected_video_version/job_revision/session_revision and optional
   retry_authorization_note. Note is never a budget grant. Actor/org/session from
   verified server context; target video from path; If-Match video_run_revision.
2. Authoritative failed snapshot binds exact prior video/run/job/attempt outcome,
   immutable pin/source/context/audience, terminal failure/history and policy.
   Reject queued/running/retryable/succeeded/cancelled with VIDEO_NOT_EXHAUSTED or
   appropriate safe conflict. Absent trustworthy final snapshot fails closed.
3. Distinguish content version, run revision, job revision, disposition CAS and
   session revision. Preserve immutable prior failure and policy/budget decision;
   successful previous09 review/playback receipt not valid exhaustion evidence.
4. Define deterministic action/intent/settlement rules and canonical scoped key/body
   fingerprints. One winning disposition per exact failed lifecycle across actors/
   different keys; no retry/skip/end double effects. Same key+body reauthorizes and
   recovers original outcome; changed body/preconditions conflicts.
5. Inventory CR10-01 failed08/foundation snapshot+new-run identity and policy adapter,
   CR10-02 BE1 skip/end/checkpoint receipt, CR10-03 current bounded retry/budget
   authorization/consumption. All candidate until adopted, no unreviewed policy
   thresholds. Retry creates new run/job or owner-approved new lifecycle, never
   resurrects terminal08 row or reuses create semantic key accidentally.

## 4. P2 — guarded orchestration and external effect recovery

1. Authenticate Teacher action-specific current scope/control; resolve exact failure
   under real owner fences and check session nonterminal, source/audience/consent/
   rights/profile/current14 policy as applicable. Current rechecks held through own
   commit and actual effect; merely checking a role/allowed boolean is insufficient.
2. Persist scoped original intent/receipt history/audit/outbox atomically BEFORE
   external side effects. Serialize competing actions on same failed lifecycle,
   not only actor-key dedup. Keep no09 DB transaction over external calls.
3. Retry bridge revalidates current context/manual-retry eligibility and bounded
   authorization, records policy/budget proof and atomically consumes authorization
   with deduplicated new lifecycle submission at owning side. No grant by free text,
   cached eligibility or unbounded loop. Preserve old failed reference; new run
   receives no copied Teacher approval. CR10-01/03 must define exact return refs.
4. Skip bridge requests ONLY explicit permitted session transition, records
   skipped_by_teacher, never generated/succeeded. No inferred target stage or
   additional automatic advance. End bridge must persist early outcome plus actual
   checkpoint/evidence receipt; absent/partial checkpoint not session_ended_early.
5. Exact authenticated bridge receipt binds original action/key/target/body/principal,
   before/after revisions and action-specific result. Timeout/lost ACK/foreign or
   malformed receipt =>unresolved pending, not guessed rollback/success/new retry.
   Replays lookup original key only; known absence does not authorize redispatch.
   Define current eligibility checks for NEW effects vs historical recovery scope.
6. Document one adopted atomic or explicitly recoverable cross-owner protocol;
   sequential commits/outbox delivery alone not advertised atomic. No invented
   compensation session reversal/cancel/purge after unknown outcome. Durable
   reconciliation remains explicit owner adoption, not hidden background retry.
7. Concurrent source/consent/stop/session end invalidates new effects; late old job
   result cannot reverse skip/end, revive approval or auto-play. Actual owning
   ingress/session/access must enforce fences;10 port fixtures do not prove it.

## 5. P3 — own storage and CMD-43 HTTP

1. Own additive schema/migration (frozen literal new migration) and closed codec,
   scoped transaction/locking/CAS/unique winning-failure claim, original key/body
   receipt/history/event. No foreign keys/writes to BE1/08/01-owned schemas.
   Domain row scope must agree with relational envelope; no arbitrary deserialization.
2. Inject POST /knowledge-videos/{video_id}/failure-dispositions under existing
   candidate prefix; no production default mounting/auth. Mandatory opaque key,
   strong single If-Match for VIDEO RUN revision (not review/job/session), explicit
   stream size bound, strict JSON/fields/scalars, authenticated server identity.
3. DATA-28 response confirmed: disposition_id, recorded_by/at, action/reason,
   prior_failure_ref, verified session_revision/video_run_revision, truthful outcome
   retry_pending/skipped_by_teacher/session_ended_early, nullable new_job_id.
   Exact prior/new-run ref mapping must be documented by action/CR10-01, not guessed
   from08 review revision. Public response never invents mandatory confirmed fields.
4. Unknown external effect uses explicitly documented candidate202 pending envelope
   rather than a fabricated DATA-28 confirmed outcome; this transport extension is
   NOT silently added to shared upstream outcome enum. Dependency missing503.
   No raw reason/request/provider diagnostics in errors; protected actor/reason
   record available only to authorized adult caller, no Child route or leak.
5. Prepare actual own SQL migration/rollback/reconnect/CAS/race/immutable/unique
   claim cases. Actual DB execution separately authorized isolated environment;
   local collection/SQL mocks not labeled actual durable evidence.

## 6. P4 — full internal verification, audit and handoff

1. All three actions positive/negative tests: exhausted-only, Teacher-only, wrong
   scope/version/run/job/session, reason/scalar/ETag, current budget revoke/stop,
   source/context change, duplicate/conflicting/different-actor action races,
   atomic intent rollback, lost commit/start ACK, lookup outage/absence, foreign/
   malformed/late receipts, partial end checkpoint and old terminal late result.
2. Synthetic08 exhausted target ->10 explicit intent ->ASSUMED_CONTRACT exact owner
   receipt fixtures for each action, distinct from actual BE1/foundation adoption.
   Verify new run is not old row reset and never approved; skip/end not video success.
3. Source/node-pinned local runner with exact JUnit identities, no skips-as-PASS;
   transitive own/08/09/12/14/foundation regression, Ruff/Mypy/architecture/harness/
   security/diff and source unchanged before/after. No package/provider effects.
4. Consolidated HTTP/owner contract matrix, A1–A7 acceptance audit and reproducible
   own SQL plus delayed runtime/BE1/P4 conformance steps. Keep unresolved policy/
   identity/version/session/checkpoint semantics visible. Full10 DONE requires
   actual required adopter/SQL/runtime evidence and owner acceptance.

## 7. Acceptance criteria

| ID | Required |
|---|---|
| A1 | Strict exact failed-exhausted target/Teacher/current scope; generating never accepts failure action |
| A2 | Independent run If-Match +video/job/session assertions; immutable failure/source/policy history |
| A3 | Bounded authorized retry creates new lifecycle, preserves old failure, no copied approval or terminal reset |
| A4 | Skip truthful skipped_by_teacher; end truthful early outcome only with actual checkpoint receipt; no automatic stage change |
| A5 | One winning disposition, durable scoped dedup/CAS/intent-before-effect, original-key unknown-outcome recovery/no duplicate effects |
| A6 | Injected safe CMD-43/closed responses/errors, pending distinct from confirmed, no body authority/Child/diagnostic leak |
| A7 | Source-pinned positive/negative/race proof and honest SQL/owner/runtime evidence matrix/handoff; no fixture-as-integration claim |

## 8. Sequence / stop boundaries

C0 plan; P1 pure contracts/domain; P2 guarded actions/recovery; P3 storage/HTTP;
P4 consolidated tests/audit/handoff. After exact revision1 approval, complete ALL
internally authorized P1–P4 without stopping after each commit/function. Commit by
meaningful functional cluster; update docs together at verification checkpoints.
Stop only for material new authority/owner choice/out-of-scope defect, not normal
missing external adapters already recorded as deferred. No persistent goal inferred.

Present this exact revision1 before code; approval recorded separately, frozen plan
bytes preserved afterwards. Current authorization PLANNING ONLY; implementation
NOT_STARTED. Actual SQL/provider/BE1/P4 adoption remains separately gated.
