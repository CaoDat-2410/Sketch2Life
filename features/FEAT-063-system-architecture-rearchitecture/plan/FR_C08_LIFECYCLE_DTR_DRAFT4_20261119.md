# FR-C-08 Parent StoryRun lifecycle — data/table change request (DTR), Draft 4

**Status: DRAFT / NOT APPROVED.** Round-3 candidate (owner allowed the round after the D-171
stop of round 2).
**Date:** 2026-11-19.
**Purpose:** the exact schema delta, purge protocol and migration steps that D-214 items 3, 7, 8
and 9, D-215 items 1-3 and 6, D-216 items 3 and 5 and D-217 leave to a reviewed DTR. This
document approves nothing and grants no implementation, migration, database, storage, test,
route, push or merge authority.

**Change from Draft 3:** fixes the round-2 cold review
(`tmp/frc08-dtr/review-r2/FR_C08_DTR_DRAFT3_COLD_REVIEW_R2_20261119.md`, NEEDS REVISION,
0 P1 / 6 P2 / 10 P3; N-1 and N-2 repeat round-1 classes) and takes over §11 of Core port design
Draft 3:
- **N-1 token:** one protocol — each step writes a pending entry derived from its own plan, then
  flips it to verified; verified entries are write-once; the final hash is over the persisted
  entries (§5.1).
- **N-2 outbox:** a lease longer than any step plus a lease-renewal call, a compare-and-set on
  every receipt update, the retry count from the outbox row, and the exception path through
  `process_local_once` (§6.3).
- **N-3 ports:** a Story lifecycle port and a Core upload port; the coordinator order for the
  Core/Story/Core asset plan (§6.2, §5.8).
- **N-4 read paths:** the projection read short-circuits before any input or profile access, and
  replays of a purged run return the projection (§6.5, §5.8).
- **N-5 fence:** every writer treats `DELETE_PENDING` and `DELETED` alike and `DELETED` is
  terminal; a final object check in step 6 (§7).
- **N-6 reconciliation:** selected by "no outbox event", with deterministic event ids (§6.4).
- P3-1 to P3-10 and port design §11 items as noted in place.

## 1. Authority and pins

| Input | Pin |
|---|---|
| Canonical working SRS (D-209) | `artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`, 701,157 bytes, SHA-256 `B9B1F42D0BB118C19C81607D3913B7E4F1D8B6F673F0C3FBB6402888FEB675F5` |
| Companion data register | `artifacts/DATA_TABLE_REGISTER.md` Rev57 (supporting evidence only) |
| Owner decisions | FEAT-063 `DECISIONS.md` D-214 to D-217 (working tree, uncommitted) |
| Planning contract | `plan/FR_C08_PARENT_TEACHER_LIFECYCLE_CONTRACT_DRAFT8_20261119.md` (not approved) |
| Core port | `plan/FR_C08_CORE_REFERENCE_CLOSURE_PORT_DESIGN_DRAFT3_20261119.md` (under round-3 review) |
| Code base (D-216 item 2) | `feature/feat066-conv1` at `03342207ab10379e6c53449274edaf4d9bcf60e4`, read in `.worktrees/conv1` |

Scope limits: Parent only (D-214 item 4); no new table and no new public StoryRun state
(D-215 item 2); no fabricated organization (SRS line 1048; register line 73); exact SQL and
migration steps need a separate owner approval (register line 204; D-216 item 3).

## 2. Covers / does not cover

**Covers:** typed owner scope on five tables; the `DELETED` state, the `DELETE_RUN` receipt
operation and a nullable `profile_ref`; the purge protocol, its ports and retry; the receipt
token; audit rows; the access fence; one migration; the read and replay paths that the schema
change forces.

**Does not cover:** the Core asset port contract (port design Draft 3); the route and
response-schema change itself (next Contract and Allowlist revision); the SRS wording edit;
Teacher; retention periods and an audit reader; the owner-review re-open command (§6.6 names it).

## 3. Source facts at the base (read-only, `03342207`)

| # | Fact | Evidence |
|---|---|---|
| S1 | `be1_data_lifecycle_requests`: `request_id` PK String(36), `organization_id` NOT NULL, `request_type` String(24), `target_ref` String(256), `state` CHECK (`requested, running, awaiting_external_purge, completed, exception`), `unresolved_items` ≥ 0, `result_ref` String(512) NULL, `requested_by` String(256), `created_at`, `completed_at`; no version column. | `infrastructure/persistence/be1_models.py:555-578` |
| S2 | Its writers are organization-scoped and never set `completed`. | `interfaces/http/routers/be1_records.py:432-500`; `infrastructure/persistence/be1_worker.py:150-160` |
| S3 | `ai_jobs.cancellation_notice.organization_id` NOT NULL; `CancellationNotice.organization_id` non-optional. | `infrastructure/ai_jobs/sql/tables.py:229-244`; `application/ports/ai_jobs.py:249-257` |
| S4 | No Parent product run creates an `ai_jobs.job` row; the vision invocation ledger is used only by the StoryRun-lite photo bridge and the pilot composition. | `infrastructure/story_run_lite/photo_bridge.py`; `infrastructure/vision_analysis/ledger.py` |
| S5 | `core_audit_entries.organization_id` NOT NULL; no scope column. | `infrastructure/persistence/core_models.py:187-203` |
| S6 | `core_asset_metadata` has the typed scope pattern; its ORM default copies `organization_id` into `owner_scope_ref`. | `core_models.py:143-184` |
| S7 | `core_outbox_events.organization_id` NOT NULL, `event_id` String(36) PK, FK `aggregate_id` → `core_aggregate_revisions` (`organization_id` NOT NULL). | `core_models.py:27-40, 206-242` |
| S8 | `ck_story_run_state` has ten values; `profile_ref` NOT NULL. | `infrastructure/story_run_lite/tables.py:213-284` |
| S9 | M2 cancel: `DELETE_PENDING`, lock released, revision/version +1, `FINAL` receipt with the full run envelope; no request, notice, event or audit. | `parent_story_repository.py:328-438` |
| S10 | Run-owned private content: child rows (`run_inputs`, `understanding_revisions`, `review_decisions`, `story_revisions`, `story_scenes`, `story_revision_reviews`); `story.runs` columns `asset_ref`, `derived_asset_ref`, `subject_label`, `confidence`, `result_sha256`, `raw_body_sha256`, `child_age_months`, `profile_ref`, `provider_job_id`, `provider_attempt_id`, `understanding_revision`, `error_code`; Core asset rows and objects. | `tables.py:213-606` |
| S11 | The Parent product routes write no upload sessions, parts or upload receipts. | `interfaces/http/routers/parent_ai.py`; `infrastructure/story_run_lite/repository.py` |
| S12 | `ck_story_receipt_operation` has seven values (no `DELETE_RUN`); `request_fingerprint_sha256` NOT NULL, length 64. | `tables.py:408-460` |
| S13 | `get_run` reads the current input and builds `UUID(profile_ref)`; `replay_create_run` ends in `get_run`; the cancel response is built from `get_run`; `ParentStoryRunRecord.parent_profile_id` is a non-optional UUID. | `parent_story_repository.py:217, 223, 269, 411`; `application/ports/parent_story_runs.py:26-50`; `interfaces/http/routers/parent_story_runs.py:97-123` |
| S14 | `PostgresOutbox`: `claim_ready(worker_id, limit, lease_seconds 1-3600)` increments `attempt_count` per claim; no lease renewal; `defer(event_id, worker_id, retry_after_seconds)` and `process_local_once(event_id, worker_id, consumer_name, effect)` return `False` when the lease is lost; the claimed envelope carries no `attempt_count`; `get_state` is organization-keyed. No caller at the base. | `infrastructure/persistence/outbox.py:26-181` |
| S15 | Core ports with non-optional `organization_id`: `OutboxEnvelope`, `OutboxState`, `CoreAuditRecord`, `AggregateRevisionPort.current_revision`, `OutboxStatePort.get_state`. | `application/ports/core_foundation.py:60-66, 85-107, 126-127, 189-190` |
| S16 | Story writers that refuse only `DELETE_PENDING`: `complete_story_revision`, `fail_story_revision`, `fail_drawing_analysis` (the last writes `INPUT_PROCESSING` or `FAILED`). | `parent_story_repository.py:1092-1093, 1208-1209, 1279-1290` |
| S17 | Alembic: the database head of the Story line is `20261112_parent_story_context`, whose ancestors include the BE1 and AI Jobs heads; the README documents per-module `upgrade <branch>@head` commands; the PG gate test pins stored version rows. | `alembic/versions/20261102_pilot_vision.py:13`; `backend/alembic/README.md:10-11`; `tests/integration/test_m2_s2_g1_parent_story_postgres.py:85-96` |

## 4. Design rules

1. **One owner-scope pattern** (S6 CHECK) on the five tables; existing rows need no backfill;
   `GLOBAL` not accepted. The S6 guard trigger is not copied. **ORM default for the five models:
   `owner_scope_ref` is NULL for organization rows** (no copy of `organization_id`), so the
   downgrade guard of §9 stays usable (review P3-4).
2. **Parent scope value:** the Parent principal scope ref stored in `story.runs.actor_scope_ref`.
3. **No new table, no new public state.**
4. **Owner modules keep their own evidence;** the receipt records verified outcomes only.
5. **Events through the Core outbox** in the owner's transaction (SRS lines 404, 904, 1778).
6. **Deterministic ids** from `LIFECYCLE_NS = 3f6c1a52-9d4e-5b70-8c21-7a5e0b9d4f13` (a fixed
   UUID constant defined once in the Story lifecycle port module; review P3-1):
   `request_id = UUIDv5(NS, 'story_run:' || run_id)`;
   `event_id = UUIDv5(NS, request_id || ':' || event_type)`;
   `audit_id = UUIDv5(NS, request_id || ':' || action)`.

## 5. Schema delta

### 5.1 `be1_data_lifecycle_requests`

| Change | Exact proposal |
|---|---|
| `organization_id` | `DROP NOT NULL` |
| `owner_scope_kind`, `owner_scope_ref` | rule 1 |
| CHECK `ck_be1_data_request_owner_scope` | rule 1 expression |
| CHECK `ck_be1_data_request_parent_completed` | `owner_scope_kind <> 'PARENT_ACCOUNT' OR state <> 'completed' OR (unresolved_items = 0 AND completed_at IS NOT NULL AND result_ref ~ '^lcr1;upload=v:[0-9]+:[0-9a-f]{16}@[0-9a-f]{8};ai=v:[0-9]+:[0-9a-f]{16}@[0-9a-f]{8};asset=v:[0-9]+:[0-9a-f]{16}@[0-9a-f]{8};story=v:[0-9]+:[0-9a-f]{16}@[0-9a-f]{8};sha256=[0-9a-f]{64}(;orph=[0-9]+)?$')` — Parent rows only (review P3-3) |

Parent values: `request_type = 'delete'`, `target_ref = 'story_run:' || run_id`, `requested_by` =
Parent scope ref. `state` vocabulary unchanged (S1); `unresolved_items` = number of steps of §6.2
not yet verified (start 4).

**Token protocol (review N-1; port design §6.5).** `result_ref` holds
`lcr1;upload=<e>;ai=<e>;asset=<e>;story=<e>[;sha256=<h64>][;orph=<m>]` with each `<e>` =
`<p|v>:<n>:<h16>@<p8>`:
- each step first computes its **step plan** (the sorted identifiers it will act on), then
  writes a **pending** entry `p:<n>:<h16>@<p8>` — `<n>` = number of identifiers, `<h16>` = first 16
  hex characters of the SHA-256 of their canonical JSON, `<p8>` = first 8 hex characters of the
  step plan hash;
- after the step's verification it flips the entry to **verified** `v:…` with the same values;
- a verified entry is **write-once**; a rerun skips that step; a pending entry is replaced only
  by a pending entry of a newer step plan;
- `<n>` per step: upload = sessions closed; ai = notices recorded (1); asset = removable keys in
  the Core plan (objects); story = child rows deleted plus receipt bodies rewritten;
- `sha256` = SHA-256 of the UTF-8 bytes of the four persisted `v` entries joined by `;`, so it can
  always be recomputed from the receipt itself;
- `orph=<m>`: orphan objects swept (port design §6.2), informational, not hashed.

### 5.2 `ai_jobs.cancellation_notice`

`organization_id` `DROP NOT NULL`; scope columns (rule 1, `ck_cancellation_notice_owner_scope`);
`story_run_ref` String(128) NULL, CHECK `owner_scope_kind <> 'PARENT_ACCOUNT' OR story_run_ref IS
NOT NULL`. Parent notice: `notice_id = 'lifecycle:' || request_id`, matches no job (S4),
recorded `COMPLETE` with `applied_count = 0`.

### 5.3 `core_audit_entries`

`organization_id` `DROP NOT NULL`; scope columns (rule 1, `ck_core_audit_owner_scope`). No index.

### 5.4 Story tables

| Table | Change |
|---|---|
| `story.runs` | `ck_story_run_state` + `'DELETED'`; `profile_ref` `DROP NOT NULL`. Code, not the database, keeps `profile_ref` required for every non-`DELETED` run (review P3-10). Nulling it on the tombstone is a coordinator inference from SRS lines 270 (BR-26: the run's profile snapshot is deleted) and 1056 (no profile detail kept); review P3-8 |
| `story.command_receipts` | `ck_story_receipt_operation` + `'DELETE_RUN'` |

### 5.5 `core_outbox_events` and `core_aggregate_revisions`

Both: `organization_id` `DROP NOT NULL`; scope columns (rule 1). Parent aggregate row keyed by
`run_id`, `revision` = `story.runs.revision`.

### 5.6 Unchanged tables

`core_asset_metadata`, `core_asset_lineage`, `core_outbox_consumer_receipts`, the upload tables
(S11), the vision ledger (S4), the other `story.*` tables.

### 5.7 Owner decision on per-object deletion state (port design §8)

No per-row deletion-state column on `core_asset_metadata`; the deletion state lives on the
receipt. SRS line 1949 lists it per object, so this is deviation A-5 (§12).

### 5.8 Code that must change with the schema (for the allowlist; not approved here)

| Area | Change |
|---|---|
| ORM / tables | five models as rule 1 (NULL default for `owner_scope_ref`); `cancellation_notice`; `runs`, `command_receipts` |
| Core ports (S15) | optional `organization_id` plus scope on `OutboxEnvelope`, `OutboxState`, `CoreAuditRecord`; scope-keyed `AggregateRevisionPort` and `OutboxStatePort.get_state` |
| Outbox (S14) | `claim_ready` event-type filter; new `renew_lease(event_id, worker_id, lease_seconds)`; the claimed envelope exposes `attempt_count` |
| AI Jobs | `CancellationNotice` optional organization, scope, `story_run_ref`; Parent notice matches no job |
| Story lifecycle port (new) | `plan_story_purge(run_ref)`, `purge_story_content(plan)`, `finalize_deleted(run_ref, request_id)`, `lifecycle_state(run_ref)`, `assets_referenced_by_other_runs(scope, run_ref, asset_refs)` |
| Core upload port (new) | `close_run_uploads(scope, run_ref) -> (count, digest)` |
| Core asset port | port design Draft 3 |
| Story repository and router (S13, S16) | projection read for `DELETE_PENDING`/`DELETED` before any input or profile access; a lifecycle record type with optional profile fields; replays of a purged run return the projection; cancel and delete responses built from the projection; the three S16 writers refuse `DELETE_PENDING` and `DELETED` and update with `WHERE run_state NOT IN ('DELETE_PENDING','DELETED')` |
| Artwork route | state re-check before the first `put_object` (port design §6.7) |
| Storage | `list_keys(prefix)` in the port, the S3 adapter and every fake |
| Tests and docs | `_EXPECTED_VERSION_ROWS`; the cancel/GET body assertions of `test_m2_s2_g1_parent_story_postgres.py` (lines 746, 1026, 1039); `backend/alembic/README.md` line on `upgrade heads` (review P3-7) |

## 6. Lifecycle protocol

### 6.1 Command (one Story transaction; SRS lines 1520, 1673-1674)

Cancel (13 SRS states plus the two documented extensions; D-216 item 4) or delete (`COMPLETED`,
`FAILED`, `ABANDONED`; D-214 item 1):
1. lock the run; idempotency (`CANCEL_RUN` or `DELETE_RUN`); cancel checks `expected_revision`
   (line 1673); delete has none (line 1674);
2. set `DELETE_PENDING`, release the active lock, `revision` and `version` +1;
3. upsert the Parent aggregate row; insert the outbox event with the deterministic `event_id`
   (insert-if-absent): `StoryRunCancellationRequestedV1` (line 1845) or `StoryRunDeletedV1`
   (line 1846), payload: run ref, `request_id`, scope ref, safe reason code;
4. audit `lifecycle.cancel_accepted` / `lifecycle.delete_accepted`;
5. receipt body = the lifecycle projection; commit.

**Stated deviation (review P3-9):** SRS lines 1520 and 1797 write the notice and the lifecycle
request at acceptance. Here the deterministic `request_id` and the event exist at acceptance and
GET shows `lifecycle_request_ref` from then on, but the BE1 receipt row and the notice are written
by the consumer (no cross-module transaction, SRS line 404).

### 6.2 Purge steps (BE1 lifecycle consumer; new work)

Each step: compute its step plan → write the pending entry (CAS) → act → verify → flip to
verified (CAS). A verified step is skipped on a rerun.

| # | Owner, port | Action | Verified when |
|---|---|---|---|
| 0 | BE1 | insert the receipt if absent (`requested`, `unresolved_items = 4`), then `running` | — |
| 1 | Core, `close_run_uploads` | close and remove any upload session, parts and upload receipts naming the run (none on the Parent product path, S11) | none remain |
| 2 | AI Jobs | record the Parent notice | notice row exists |
| 3 | Core, asset port | `closure_candidates` → Story `assets_referenced_by_other_runs` with **all** candidate refs → `plan_run_purge` → `purge_objects` → `delete_rows` (port design §6.1-§6.3) | `verify_run_purged` complete |
| 4 | Story, `purge_story_content` | delete the child rows; NULL every S10 `story.runs` column except identity, scope, state, revision and version (including `profile_ref`, `current_input_revision`); rewrite the body of a pre-existing `CANCEL_RUN` receipt to the projection; on **every** receipt of the run replace `request_fingerprint_sha256` with SHA-256 of `'tombstone:' || receipt_id` (review P3-5) | no child row; columns NULL; no body with content |
| 5 | Story, `finalize_deleted` | only if step 3 is verified: `verify_run_purged` again (late writes, port design §6.7); then `DELETED`, `revision`/`version` +1, aggregate row `revision` updated, audit `lifecycle.completed`; idempotent on `run_id` | `lifecycle_state` = `DELETED` |
| 6 | BE1 | `verify_run_purged` once more; if not complete, rerun step 3's sweep; then `process_local_once` with the effect: receipt `completed`, final token, `completed_at`; event delivered | receipt `completed` |

**When step 3 ends in `exception`** (retained group): steps 1, 2 and 4 still run (Story content
is not shared, so it is purged); step 5 does not run; the run stays `DELETE_PENDING` (SRS line
1951: not complete until reconciled); the receipt goes to `exception` (review P3-2).

### 6.3 Leases, concurrency and retry (review N-2)

- Claim with `lease_seconds = 900` (configurable up to 3600), longer than any step; the consumer
  calls `renew_lease` before each step and stops if renewal fails (another worker owns the event).
- **Every receipt update is a compare-and-set** on the previous `state` and `result_ref`
  (`UPDATE … WHERE request_id = :id AND state = :old_state AND result_ref IS NOT DISTINCT FROM
  :old_ref`); a zero-row update means another worker progressed, and this worker stops.
- On a failed step: receipt `awaiting_external_purge` (CAS), then `defer` with a growing delay.
- **Retry bound:** the claimed envelope's `attempt_count` (S14 change); at 10 the consumer runs
  `process_local_once` whose effect sets the receipt `exception` (CAS) and writes
  `lifecycle.exception`, and the event is delivered.
- If step 6 reaches the bound after step 5, the run stays `DELETED` (Story is the truth for GET)
  and the receipt is `exception` until the owner-review re-open finishes it.

### 6.4 Pre-existing `DELETE_PENDING` runs (review N-6)

A one-time, owner-run, re-runnable command: for every Parent `DELETE_PENDING` run that has **no
outbox event for its aggregate**, insert `StoryRunCancellationRequestedV1` with the deterministic
`event_id` (insert-if-absent) and the aggregate row. Runs cancelled by the new code already have
their event and are skipped; a second run of the command inserts nothing.

### 6.5 Reads and replays (review N-4, P3-6; D-217 item 5)

- From `DELETE_PENDING` on, the repository returns the **lifecycle projection** before touching
  `run_inputs` or `profile_ref`: `run_id`, `run_state`, `revision`, `version`,
  `lifecycle_request_ref` (derived, rule 6), `purge_state` (`COMPLETED` exactly when `run_state =
  'DELETED'`, else `PENDING`). GET, the cancel 202 and the delete 202 return it.
- **Any replay** (create, attach, confirmations, cancel, delete) whose receipt names a run in
  `DELETE_PENDING` or `DELETED` returns the projection without the fingerprint check.
- New cancel and delete receipts store the projection, so their replay returns the original body.
- **Deviation, narrowed:** only the body of a pre-existing (M2) `CANCEL_RUN` receipt is rewritten,
  because only that body holds run content; other receipt bodies hold ids, revisions and hashes
  and are kept. The frozen `ParentStoryRunCancelEnvelopeV1` shape changes (A-3).

### 6.6 `exception` re-open

Only an owner-review command (separate work) re-opens: it records the reconciliation (for
example Core `release_run_reference`, audit `lifecycle.reference_released`), sets the receipt to
`requested` (CAS) and inserts a new outbox event of the same type with
`event_id = UUIDv5(NS, request_id || ':' || event_type || ':reopen:' || n)`.

## 7. Access fence (D-214 item 6; review N-5)

`DELETE_PENDING` and `DELETED` are treated alike by every Story writer, and `DELETED` is terminal:
the three S16 writers and every other Story state writer refuse both states and update with
`WHERE run_state NOT IN ('DELETE_PENDING','DELETED')`. A worker result is accepted only by a
compare-and-set on the dispatched `version`. The artwork route re-checks the state before its
first `put_object`; late objects are caught by the verifications of steps 5 and 6. Race evidence
for each boundary is an implementation-approval requirement.

## 8. Audit rows (metadata only)

| Action | Writer | `decision` |
|---|---|---|
| `lifecycle.cancel_accepted` / `lifecycle.delete_accepted` | Story, §6.1 | `accepted:<request_id>` |
| `lifecycle.completed` | Story, step 5 | `completed:<request_id>` (the deletion receipt) |
| `lifecycle.exception` | BE1, §6.3 | `exception:<request_id>` |
| `lifecycle.reference_released` | Core, §6.6 | `released:<reconciliation_ref>` |

Common: `audit_id` rule 6 (String(36)); `decision` at most 46 characters for the request-id forms
(String(64)); scope `PARENT_ACCOUNT`; `actor_ref` = Parent scope ref or `be1-lifecycle-worker`;
`organization_id` NULL; `resource_type = 'story_run'`; `resource_id = run_id`. Never stored:
media, transcript, idea, prompt, context, profile detail, storage key. No reader; retention
deferred.

## 9. Migration

- One revision on its own branch: `down_revision = None`, `branch_labels = ("frc08_lifecycle",)`,
  `depends_on = ("20261112_parent_story_context",)`; it replaces that revision in
  `alembic_version`. Deploy uses `upgrade heads`; the README states that per-module
  `upgrade <branch>@head` commands skip this revision (review P3-7).
- Order: §5.5, §5.1, §5.2, §5.3 (drop NOT NULL, add columns, add CHECKs), then §5.4. Direct
  CHECKs on the disposable verification database; `NOT VALID` then `VALIDATE` for a production
  rollout.
- Downgrade refuses when any of the five tables has a `PARENT_ACCOUNT` row or an `ORGANIZATION`
  row with a non-NULL scope ref, when any run is `DELETED` or has a NULL `profile_ref`, or when a
  `DELETE_RUN` receipt exists; otherwise it reverses every step.
- Never against `sketch2life_m2_s1a`, `be1_acceptance`, or ports 5432 and 5433.

## 10. Verification required from the implementation task

- upgrade and downgrade on a fresh disposable database; upgrade over organization rows with no
  row change; every downgrade-guard case; organization rows written after the upgrade keep a NULL
  scope ref;
- every CHECK, including the Parent `completed` token pattern;
- a second cancel or delete on a `DELETE_PENDING` run is refused (409) and writes nothing
  (review P3-1);
- a crash at each step boundary and between act and verify re-runs to the same verified entries
  and final token; two workers on one event: the CAS stops the second; a lost lease stops work;
  the bound ends in `exception`;
- step 3 `exception`: Story content purged, run stays `DELETE_PENDING`;
- the reconciliation command inserts one event per eligible run and nothing on a second run;
- GET, both 202 bodies and every replay of a purged run return only the projection, with no
  error on `DELETE_PENDING` after step 4 or on `DELETED`;
- `fail_drawing_analysis`, `fail_story_revision` and `complete_story_revision` cannot change a
  `DELETED` run;
- audit rows hold only §8 fields, are not duplicated by a rerun, and fit their column lengths;
- the School Admin data-request route, the BE1 retention worker and AI Jobs organization notices
  behave as before; `_EXPECTED_VERSION_ROWS` updated.

## 11. Items settled from the SRS (D-217, as amended)

| # | Item | Draft 4 |
|---|---|---|
| 1 | Audit owner scope | as D-217 item 1 |
| 2 | Events | cancel → `StoryRunCancellationRequestedV1`; delete → `StoryRunDeletedV1` (SRS 1845-1846); no completion event (**amends D-217 items 2-3**, A-2) |
| 3 | Retry | outbox lease, renewal, CAS, bound 10 (§6.3) |
| 4 | Responses | projection from `DELETE_PENDING` on; deviation narrowed to the pre-existing `CANCEL_RUN` body and the cancel envelope (A-3) |
| 5 | `DELETE` route | as D-217 item 6; no expected revision per SRS line 1674 |
| 6 | Idempotency-Key | as D-217 item 7 |
| 7 | GET projection | `purge_state` from `run_state`; `lifecycle_request_ref` derived |
| 8 | Core predicate | port design Draft 3 |

## 12. Owner decisions at DTR approval

| ID | Decision | Recommendation |
|---|---|---|
| A-1 | Approve this DTR (after review) as the schema and migration direction | after review |
| A-2 | Amend D-217 items 2-3 as §11 row 2 | yes (SRS line 1846) |
| A-3 | Accept the cancel-envelope change and the rewrite of pre-existing `CANCEL_RUN` bodies | yes (SRS lines 1053, 1520) |
| A-4 | Accept nullable `profile_ref`, cleared on the tombstone | yes (SRS lines 270, 1056; coordinator inference) |
| A-5 | Accept no per-object deletion-state column (SRS line 1949) | yes for V1 (port design §8) |

## 13. Not verified

- Any database or storage behaviour; nothing was run.
- Whether another branch alters these tables after the base.
- The lifecycle consumer and the new ports do not exist yet; their runtime behaviour is unproven.
