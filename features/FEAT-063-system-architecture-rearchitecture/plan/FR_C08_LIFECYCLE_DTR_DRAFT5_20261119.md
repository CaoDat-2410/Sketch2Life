# FR-C-08 Parent StoryRun lifecycle — data/table change request (DTR), Draft 5

**Status: DRAFT / NOT APPROVED.** Round-4 candidate (owner extended the D-171 repeat-class stop on
2026-11-19 so the remaining rounds up to the five-round cap may run).
**Date:** 2026-11-19.
**Purpose:** the exact schema delta, purge protocol and migration steps that D-214 items 3, 7, 8
and 9, D-215 items 1-3 and 6, D-216 items 3 and 5 and D-217 leave to a reviewed DTR. This
document approves nothing and grants no implementation, migration, database, storage, test,
route, push or merge authority.

**Change from Draft 4.** Fixes the round-3 review
(`tmp/frc08-dtr/review-r3/FR_C08_DTR_DRAFT4_COLD_REVIEW_R3_20261119.md`, NEEDS REVISION,
0 P1 / 2 P2 / 11 P3) and takes over §10 of Core port design Draft 4. The port design
(`plan/FR_C08_CORE_REFERENCE_CLOSURE_PORT_DESIGN_DRAFT5_20261119.md`) is changed in the same
step so the two documents agree.

| Finding | Fix in Draft 5 |
|---|---|
| **N3-1** token not reproducible at the act-to-flip crash; DTR and port disagree on the entry | **One token rule, owned by this DTR** (§5.1, rules T1-T7): the DTR owns the receipt entry and the token; the port only returns plan facts (counts, full 64-hex digests, plan hash). Step-plan identifiers are defined for every step; a flip keeps the recorded values; an empty plan never overwrites an entry; a crash table shows that no crash point changes the final token |
| **N3-2** late-object recovery unreachable | The orphan sweep is its own idempotent Core call `sweep_run_prefix(scope, run_ref)`, independent of any plan or entry; it runs in step 3 and in the verifications of steps 5 and 6; the empty-plan skip applies only to delete calls; a late sweep never edits an entry (§5.1 T7, §6.2) |
| P3-1 states the table cannot hold | §5.4 and §6.1 say eligibility for states the table cannot store is vacuous and not tested |
| P3-2 A-3 omits the fingerprint and replay deviations; §6.5 bullets 2 and 3 contradict | §6.5 picks one rule (cancel/delete receipts keep their content-free fingerprint and return their stored projection; other receipts of a purged run return the current projection); A-3 now names both deviations (§12) |
| P3-3 canonical string and `orph` underspecified | T6 defines the exact string, the position of `sha256` and the writing time of `orph` |
| P3-4 audit ids repeat across re-open | `lifecycle.exception` is keyed by the processed `event_id`; the release action is gone (rule 6, §8) |
| P3-5 outbox details | §6.3: zero-row CAS raises inside the effect; `limit = 1`; per-step timeout; "at or above 10"; delay schedule |
| P3-6 `exception` event end | Both exception paths run `process_local_once` and deliver the event (§6.2, §6.3) |
| P3-7 audit/GET after a failed step 6 | §6.3 states what `lifecycle.completed` and `DELETED` prove in that window |
| P3-8 event payload fields | §6.1 carries the SRS 1845 fields |
| P3-9 `read_current_input` and replay path | S18, §5.8, §6.5, §10 |
| P3-10 demo path | S19, §7, §6.4 |
| P3-11 stale cites | S13 now cites `:413`; S15 `core_foundation.py:126-127` re-read and correct (the review's `:124-125` was not reproduced); port design cross-references updated |
| R2 P3-10 (remaining) | §10 tests that the database accepts `profile_ref IS NULL` for any run |
| Port R4 P2-1 and P3-1..P3-8 | port design Draft 5; the release path, `lifecycle.reference_released` and the Core `release_run_reference` are removed from §6.6 and §8; step 3 is all-or-nothing; "verified when" is the port `complete` rule; steps 5 and 6 sweep when not complete |

## 1. Authority and pins

| Input | Pin |
|---|---|
| Canonical working SRS (D-209) | `artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`, 701,157 bytes, SHA-256 `B9B1F42D0BB118C19C81607D3913B7E4F1D8B6F673F0C3FBB6402888FEB675F5` |
| Companion data register | `artifacts/DATA_TABLE_REGISTER.md` Rev57 (supporting evidence only) |
| Owner decisions | FEAT-063 `DECISIONS.md` D-214 to D-217 (working tree, uncommitted) |
| Planning contract | `plan/FR_C08_PARENT_TEACHER_LIFECYCLE_CONTRACT_DRAFT8_20261119.md` (not approved) |
| Core port | `plan/FR_C08_CORE_REFERENCE_CLOSURE_PORT_DESIGN_DRAFT5_20261119.md` (under round-5 review) |
| Code base (D-216 item 2) | `feature/feat066-conv1` at `03342207ab10379e6c53449274edaf4d9bcf60e4`, read in `.worktrees/conv1` |

Scope limits: Parent only (D-214 item 4); no new table and no new public StoryRun state
(D-215 item 2); no fabricated organization (SRS line 1048; register line 73); exact SQL and
migration steps need a separate owner approval (register line 204; D-216 item 3).

## 2. Covers / does not cover

**Covers:** typed owner scope on five tables; the `DELETED` state, the `DELETE_RUN` receipt
operation and a nullable `profile_ref`; the purge protocol, its ports and retry; the receipt
token; audit rows; the access fence; one migration; the read and replay paths that the schema
change forces.

**Does not cover:** the Core asset port contract (port design Draft 5); the route and
response-schema change itself (next Contract and Allowlist revision); the SRS wording edit;
Teacher; retention periods and an audit reader; the owner-review re-open command itself (§6.6
names what it must do).

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
| S8 | `ck_story_run_state` has ten values (no `ABANDONED`, no `DELETED`); `profile_ref` NOT NULL. | `infrastructure/story_run_lite/tables.py:213-284` |
| S9 | M2 cancel: `DELETE_PENDING`, lock released, revision/version +1, `FINAL` receipt with the full run envelope; no request, notice, event or audit. The M2 code accepts cancel only in seven states. | `parent_story_repository.py:328-438` (states at `:385-394`) |
| S10 | Run-owned private content: child rows (`run_inputs`, `understanding_revisions`, `review_decisions`, `story_revisions`, `story_scenes`, `story_revision_reviews`); `story.runs` columns `asset_ref`, `derived_asset_ref`, `subject_label`, `confidence`, `result_sha256`, `raw_body_sha256`, `child_age_months`, `profile_ref`, `provider_job_id`, `provider_attempt_id`, `understanding_revision`, `error_code`; Core asset rows and objects. | `tables.py:213-606` |
| S11 | The Parent product routes write no upload sessions, parts or upload receipts. | `interfaces/http/routers/parent_ai.py`; `infrastructure/story_run_lite/repository.py` |
| S12 | `ck_story_receipt_operation` has seven values (no `DELETE_RUN`); `request_fingerprint_sha256` NOT NULL, length 64. Fingerprint contents: `CANCEL_RUN` = run id and expected revision; confirm-context = revision numbers and a snapshot hash; confirm-subject = the confirmed subject text; rewrite = the rewrite instruction and model ids; `CREATE_RUN` = profile id, topic, adult-confirmed idea and lesson version. | `tables.py:408-460`; `parent_story_repository.py:340, 453, 756, 886, 1317, 1619-1640` |
| S13 | `get_run` reads the current input and builds `UUID(profile_ref)`; `replay_create_run` ends in `get_run`; the cancel response is built from `get_run`; `ParentStoryRunRecord.parent_profile_id` is a non-optional UUID. | `parent_story_repository.py:217, 223, 269, 413`; `application/ports/parent_story_runs.py:26-50`; `interfaces/http/routers/parent_story_runs.py:97-123` |
| S14 | `PostgresOutbox`: `claim_ready(worker_id, limit, lease_seconds 1-3600)` leases a whole batch with one lease and increments `attempt_count` per claim; no lease renewal; `defer(event_id, worker_id, retry_after_seconds 1-86400)` and `process_local_once(event_id, worker_id, consumer_name, effect)` return `False` when the lease is lost and mark the event delivered after the effect returns; the claimed envelope carries no `attempt_count`; `get_state` is organization-keyed. No caller at the base. | `infrastructure/persistence/outbox.py:26-181` |
| S15 | Core ports with non-optional `organization_id`: `OutboxEnvelope`, `OutboxState`, `CoreAuditRecord`, `AggregateRevisionPort.current_revision`, `OutboxStatePort.get_state`. | `application/ports/core_foundation.py:60-66, 85-107, 126-127, 189-190` |
| S16 | Story writers that refuse only `DELETE_PENDING`: `complete_story_revision`, `fail_story_revision`, `fail_drawing_analysis` (the last writes `INPUT_PROCESSING` or `FAILED`). | `parent_story_repository.py:1092-1093, 1208-1209, 1279-1290` |
| S17 | Alembic: the database head of the Story line is `20261112_parent_story_context`, whose ancestors include the BE1 and AI Jobs heads; the README documents per-module `upgrade <branch>@head` commands; the PG gate test pins stored version rows. | `alembic/versions/20261102_pilot_vision.py:13`; `backend/alembic/README.md:10-11`; `tests/integration/test_m2_s2_g1_parent_story_postgres.py:85-96` |
| S18 | `read_current_input` has no state guard and is called by the artwork route; after the tombstone its `_current_input` raises 409 `PARENT_STORY_CONTEXT_UNAVAILABLE`; the artwork route's replay branch rebuilds its body from `get_run`. | `parent_story_repository.py:674-679, 1555-1558`; `parent_ai.py:238, 472` |
| S19 | The StoryRun-lite demo path writes the same `story.runs` rows and accepts `PARENT_ACCOUNT` scope; its composition is mounted instead of the Parent router; its own cancel writes `DELETE_PENDING` with no event. | `infrastructure/story_run_lite/repository.py:2672-2680`; `interfaces/http/app.py:1057-1060` |

## 4. Design rules

1. **One owner-scope pattern** (S6 CHECK) on the five tables; existing rows need no backfill;
   `GLOBAL` not accepted. The S6 guard trigger is not copied. **ORM default for the five models:
   `owner_scope_ref` is NULL for organization rows** (no copy of `organization_id`), so the
   downgrade guard of §9 stays usable.
2. **Parent scope value:** the Parent principal scope ref stored in `story.runs.actor_scope_ref`.
3. **No new table, no new public state.**
4. **Owner modules keep their own evidence;** the receipt records verified outcomes only.
5. **Events through the Core outbox** in the owner's transaction (SRS lines 404, 904, 1778).
6. **Deterministic ids** from `LIFECYCLE_NS = 3f6c1a52-9d4e-5b70-8c21-7a5e0b9d4f13` (a fixed
   UUID constant defined once in the Story lifecycle port module; names are UTF-8 strings):
   `request_id = UUIDv5(NS, 'story_run:' || run_id)`;
   `event_id = UUIDv5(NS, request_id || ':' || event_type)`;
   `audit_id = UUIDv5(NS, request_id || ':' || action)` for `lifecycle.cancel_accepted`,
   `lifecycle.delete_accepted` and `lifecycle.completed` (each is written at most once per
   request); `audit_id = UUIDv5(NS, processed_event_id || ':lifecycle.exception')` for
   `lifecycle.exception` (the processed `event_id` is unique per re-open, §6.6).
7. **`run_ref`** at every Core port is the canonical lower-case string of `story.runs.run_id`
   (port design §4).

## 5. Schema delta

### 5.1 `be1_data_lifecycle_requests` and the token rule

| Change | Exact proposal |
|---|---|
| `organization_id` | `DROP NOT NULL` |
| `owner_scope_kind`, `owner_scope_ref` | rule 1 |
| CHECK `ck_be1_data_request_owner_scope` | rule 1 expression |
| CHECK `ck_be1_data_request_parent_completed` | `owner_scope_kind <> 'PARENT_ACCOUNT' OR state <> 'completed' OR (unresolved_items = 0 AND completed_at IS NOT NULL AND result_ref ~ '^lcr1;upload=v:[0-9]+:[0-9a-f]{16}@[0-9a-f]{8};ai=v:[0-9]+:[0-9a-f]{16}@[0-9a-f]{8};asset=v:[0-9]+:[0-9a-f]{16}@[0-9a-f]{8};story=v:[0-9]+:[0-9a-f]{16}@[0-9a-f]{8};sha256=[0-9a-f]{64}(;orph=[0-9]+)?$')` — Parent rows only. The CHECK guards the shape; it cannot validate the hash |

Parent values: `request_type = 'delete'`, `target_ref = 'story_run:' || run_id`, `requested_by` =
Parent scope ref. `state` vocabulary unchanged (S1); `unresolved_items` = number of the four
steps 1-4 not yet verified (start 4).

**Token rule (owned by this DTR; the Core port only returns plan facts).** `result_ref` holds
`lcr1` followed by the step entries in the fixed order `upload, ai, asset, story` (an entry
appears once its step has written it), then `sha256=<h64>` and `orph=<m>` only at completion.
Each entry is `<step>=<s>:<n>:<h16>@<p8>`, all hex lower-case.

- **T1 entry.** `s` is `p` (pending) or `v` (verified). `n` = number of identifiers in the step
  plan; `h16` = first 16 hex characters of the SHA-256 of the canonical JSON (UTF-8, no
  whitespace, sorted identifiers) of the identifier list; `p8` = first 8 hex characters of the
  step-plan hash.
- **T2 step plans.** Every step first computes its plan from current state, before any action.

  | Step | Identifiers (sorted) | `p8` source |
  |---|---|---|
  | `upload` | upload session ids that name the run (Core `plan_close_run_uploads`) | SHA-256 of canonical JSON `{"step":"upload","ids":[…]}` |
  | `ai` | `["lifecycle:" \|\| request_id]` (always one) | same form with `"ai"` |
  | `asset` | removable asset keys of the Core plan (`plan.removable_digest` is `h16`'s source) | `plan.plan_sha256` of the port |
  | `story` | `table:pk` of every child row, `receipt:<receipt_id>` of every receipt whose content-bearing body or fingerprint is not yet tombstoned, and `run:<run_id>` when any S10 column of the run is not NULL | SHA-256 of canonical JSON `{"step":"story","ids":[…]}` |

  An empty plan has `n = 0` and `h16` of the canonical JSON `[]`.
- **T3 write.** The coordinator writes the entry with a compare-and-set before it acts:
  no entry exists → write the pending entry of this plan (an empty plan is allowed);
  a verified entry exists → the step is skipped; a pending entry exists → keep it when the new
  `p8` is equal or the new plan is empty, and replace it only by a pending entry of a
  **non-empty** plan with a different `p8`. An empty plan never overwrites an entry.
- **T4 flip.** After the step's verification (§6.2 "verified when") the pending entry becomes
  verified by changing only `p` to `v`, **keeping its recorded `n`, `h16` and `p8`**; the values
  are never recomputed from a later plan. A verified entry is write-once.
- **T5 atomic act.** The state a step derives its plan from changes only in the step's last
  atomic commit (uploads closed in one Core transaction; the notice inserted in one statement;
  Story content purged in one Story transaction; asset rows deleted last, in one Core
  transaction, after the objects). Hence a rerun after any crash computes either the same plan
  or an empty one.
- **T6 final string.** When the four entries are `v`, the effect of step 6 re-reads the receipt
  row and computes `sha256` = SHA-256 of the UTF-8 bytes of the four entry segments **exactly as
  persisted, keys included** (`upload=v:…;ai=v:…;asset=v:…;story=v:…`, joined by `;`), then
  writes `…;story=v:…;sha256=<h64>[;orph=<m>]` with `state = 'completed'`. It raises (rollback)
  when any entry is missing or pending. `orph` = the sum of the orphan counts that
  `sweep_run_prefix` calls returned during the attempt that completes the receipt; it is
  informational, not hashed, and not reproducible across crashes. It is the only segment that
  can differ between two runs that did the same work.
- **T7 sweep.** The orphan sweep is not a step and has no entry. It is the idempotent Core call
  `sweep_run_prefix(scope, run_ref)` (port design §5.1); it depends on no plan and no entry; the
  skip of an empty plan applies only to the delete calls; a sweep at any time never edits an
  entry.

Crash points (every one ends at the same four verified entries and the same `sha256`; a run
without artwork has an empty asset plan and ends `asset=v:0:…`):

| Crash point | Rerun result |
|---|---|
| before the pending entry | no entry: same plan, entry written |
| after the pending entry, before the act | same `p8`: entry kept, act runs |
| after the act, before verification or flip | plan empty: entry kept; verification passes; flip keeps `n`, `h16`, `p8` |
| after the flip | verified: step skipped |
| asset: after objects, after sweep or after the rows (before flip) | rows still hold the manifest → same plan and `p8`, or rows gone → empty plan: entry kept; the sweep runs again; verification then flips |

The count of a pending entry changes only when new work for the step appears after the earlier
plan was written and the earlier act did not commit; a writer that could add such work after
`DELETE_PENDING` is fenced out (§7).

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
| `story.runs` | `ck_story_run_state` + `'DELETED'`; `profile_ref` `DROP NOT NULL`. Code, not the database, keeps `profile_ref` required for every non-`DELETED` run. Nulling it on the tombstone is a coordinator inference from SRS lines 270 (BR-26: the run's profile snapshot is deleted) and 1056 (no profile detail kept) |
| `story.command_receipts` | `ck_story_receipt_operation` + `'DELETE_RUN'` |

`ABANDONED` and the other SRS-only states are **not** stored values at the base (S8; the base
accepts cancel in seven states, S9). This DTR does not add them. Eligibility for those states
(delete of `ABANDONED`, cancel of any state the table cannot hold) is therefore vacuous until a
later change stores them; the migration and verification here neither assert nor depend on it.

### 5.5 `core_outbox_events` and `core_aggregate_revisions`

Both: `organization_id` `DROP NOT NULL`; scope columns (rule 1). Parent aggregate row keyed by
`run_id`, `revision` = `story.runs.revision`.

### 5.6 Unchanged tables

`core_asset_metadata`, `core_asset_lineage`, `core_outbox_consumer_receipts`, the upload tables
(S11), the vision ledger (S4), the other `story.*` tables.

### 5.7 Owner decision on per-object deletion state (port design §9)

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
| Core upload port (new) | `plan_close_run_uploads(scope, run_ref) -> (count, digest)` (read only) and `close_run_uploads(scope, run_ref)` (idempotent, one transaction) |
| Core asset port | port design Draft 5 (`closure_candidates`, `plan_run_purge`, `purge_objects`, `sweep_run_prefix`, `delete_rows`, `verify_run_purged`, `review_report`) |
| Story repository and router (S13, S16, S18) | projection read for `DELETE_PENDING`/`DELETED` before any input or profile access, including `read_current_input` and the artwork route's replay branch (`parent_ai.py:238, 472`); a lifecycle record type with optional profile fields; replays of a purged run per §6.5; cancel and delete responses built from the projection; the three S16 writers refuse `DELETE_PENDING` and `DELETED` and update with `WHERE run_state NOT IN ('DELETE_PENDING','DELETED')` |
| Artwork route | state re-check before the first `put_object` (port design §7) |
| Storage | `list_keys(prefix)` in the port, the S3 adapter and every fake |
| Tests and docs | `_EXPECTED_VERSION_ROWS`; the cancel/GET body assertions of `test_m2_s2_g1_parent_story_postgres.py` (lines 746, 1026, 1039); `backend/alembic/README.md` line on `upgrade heads` |

## 6. Lifecycle protocol

### 6.1 Command (one Story transaction; SRS lines 1520, 1673-1674)

Cancel (13 SRS states plus the two documented extensions; D-216 item 4; only the states the
table can hold, §5.4) or delete (`COMPLETED`, `FAILED`, `ABANDONED`; D-214 item 1; `ABANDONED`
only once stored):
1. lock the run; idempotency (`CANCEL_RUN` or `DELETE_RUN`); cancel checks `expected_revision`
   (line 1673); delete has none (line 1674);
2. set `DELETE_PENDING`, release the active lock, `revision` and `version` +1;
3. upsert the Parent aggregate row; insert the outbox event with the deterministic `event_id`
   (insert-if-absent): `StoryRunCancellationRequestedV1` (line 1845) or `StoryRunDeletedV1`
   (line 1846). Payload, with the fields SRS 1845-1846 list: run ref, lifecycle request ref
   (`request_id`), actor ref (the Parent scope ref), expected revision (cancel only), safe reason
   code; no media or content;
4. audit `lifecycle.cancel_accepted` / `lifecycle.delete_accepted`;
5. receipt body = the lifecycle projection; commit.

**Stated deviation:** SRS lines 1520 and 1797 write the notice and the lifecycle request at
acceptance. Here the deterministic `request_id` and the event exist at acceptance and GET shows
`lifecycle_request_ref` from then on, but the BE1 receipt row and the notice are written by the
consumer (no cross-module transaction, SRS line 404).

### 6.2 Purge steps (BE1 lifecycle consumer; new work)

The BE1 consumer is the coordinator of the three owner ports. Each step 1-4 follows rules T2-T5:
compute the plan → write the entry (CAS) → act → verify → flip (CAS). A verified step is skipped.

| # | Owner, port | Action | Verified when |
|---|---|---|---|
| 0 | BE1 | insert the receipt if absent (`requested`, `unresolved_items = 4`), then `running` | — |
| 1 | Core upload port | `plan_close_run_uploads`; `close_run_uploads` (none on the Parent product path, S11) | `plan_close_run_uploads` returns an empty plan |
| 2 | AI Jobs | record the Parent notice (insert-if-absent) | notice row exists |
| 3 | Core asset port, Story answer | `closure_candidates` → Story `assets_referenced_by_other_runs` with **all** candidate refs → `plan_run_purge`. **Retained plan:** no entry, no sweep, nothing deleted → exception path below. **Removable or empty plan:** entry (T3) → `purge_objects` (skipped when the plan is empty) → `sweep_run_prefix` → re-ask Story → `delete_rows` (skipped when empty) → `verify_run_purged` | `verify_run_purged` returns `complete` (port design §6.5) |
| 4 | Story, `plan_story_purge`, `purge_story_content` | one Story transaction: delete the child rows; NULL every S10 `story.runs` column except identity, scope, state, revision and version (including `profile_ref`, `current_input_revision`); replace the content-bearing body of every pre-existing `CANCEL_RUN` receipt by the projection; replace `request_fingerprint_sha256` by SHA-256 of `'tombstone:' \|\| receipt_id` on every receipt of the run **except** `CANCEL_RUN` and `DELETE_RUN` receipts (their fingerprint holds the run id and expected revision only, S12) | `plan_story_purge` returns an empty plan |
| 5 | coordinator, then Story `finalize_deleted` | only if the asset entry is verified: `verify_run_purged`; if not `complete`, `sweep_run_prefix` and verify again (still not complete → fail the attempt, retry); then Story `finalize_deleted(run_ref, request_id)`: `DELETED`, `revision`/`version` +1, aggregate row `revision` updated, audit `lifecycle.completed`; idempotent on `run_id` | `lifecycle_state` = `DELETED` |
| 6 | BE1 | `verify_run_purged` once more; if not `complete`, `sweep_run_prefix` and verify again; then `process_local_once` with the effect: receipt `completed` and the final token (T6), `completed_at`; event delivered | receipt `completed` |

**When step 3 ends in `exception`** (a retained asset; port design §6.2): no asset object or row
is deleted. Steps 1, 2 and 4 still run (Story content is not shared); step 5 does not run; the
run stays `DELETE_PENDING` (SRS line 1951: not complete until reconciled). The consumer then
runs `process_local_once` whose effect sets the receipt `exception` (CAS; a zero-row CAS raises)
and writes `lifecycle.exception`; the event is delivered, so the old event does not return. The
re-open (§6.6) is the only way back.

### 6.3 Leases, concurrency and retry

- Claim with `limit = 1` and `lease_seconds = 900` (configurable up to 3600). Each step has a hard
  time limit of 300 seconds (statement and storage-client timeouts; the implementation task
  evidences them), and the consumer calls `renew_lease` before every step and stops if renewal
  fails (another worker owns the event).
- **Every receipt update is a compare-and-set** on the previous `state` and `result_ref`
  (`UPDATE … WHERE request_id = :id AND state = :old_state AND result_ref IS NOT DISTINCT FROM
  :old_ref`). A zero-row update means another worker progressed: outside an effect the worker
  stops; **inside a `process_local_once` effect it raises**, so the transaction rolls back and the
  event is not marked delivered.
- On a failed step: receipt `awaiting_external_purge` (CAS), then `defer` with the delay
  30, 60, 120, … seconds (doubling, capped at 3600).
- **Retry bound:** the claimed envelope's `attempt_count` (S14 change). A claim with
  `attempt_count` at or above 10 does no purge work: it runs `process_local_once` whose effect
  sets the receipt `exception` (CAS) and writes `lifecycle.exception`, and the event is
  delivered. So at most nine real purge attempts happen (intended).
- If step 6 reaches the bound after step 5, the run stays `DELETED` and GET shows
  `purge_state = COMPLETED`, and the receipt is `exception` until the re-open finishes it. In that
  window the audit row `lifecycle.completed` and the GET state are evidence of the **step 5
  verification only**; SRS line 1951 and D-208 item 1 ("`DELETED` only after purge verification")
  are met by the step 5 `verify_run_purged`, and the `completed` receipt is the later BE1
  reconciliation evidence.

### 6.4 Pre-existing `DELETE_PENDING` runs

A one-time, owner-run, re-runnable command, used only on a deployment where the Parent router is
mounted (S19): for every Parent `DELETE_PENDING` run that has **no outbox event for its
aggregate**, insert `StoryRunCancellationRequestedV1` with the deterministic `event_id`
(insert-if-absent) and the aggregate row. Runs cancelled by the new code already have their event
and are skipped; a second run inserts nothing. The StoryRun-lite demo path is out of scope; it
is not co-active with the Parent router (S19), and its own cancel leaves `DELETE_PENDING` rows
without an event, which this command would select if such rows exist in a Parent deployment.

### 6.5 Reads and replays (D-217 item 5)

- From `DELETE_PENDING` on, the repository returns the **lifecycle projection** before touching
  `run_inputs` or `profile_ref`: `run_id`, `run_state`, `revision`, `version`,
  `lifecycle_request_ref` (derived, rule 6), `purge_state` (`COMPLETED` exactly when `run_state =
  'DELETED'`, else `PENDING`). GET, the cancel 202, the delete 202, `read_current_input` (a
  lifecycle error, not `PARENT_STORY_CONTEXT_UNAVAILABLE`) and the artwork route's replay
  branch use it.
- **Replay of a cancel or delete receipt** keeps the fingerprint check of SRS line 1697 (same key
  and payload returns the original result; a changed payload returns 400
  `INVALID_IDEMPOTENCY_KEY`) and returns the **stored body**. A new receipt stores the
  projection as it was at acceptance. The body of a pre-existing M2 `CANCEL_RUN` receipt is
  rewritten in step 4 and, until then, replays return the current projection.
- **Replay of any other receipt** (create, attach, confirmations) of a run in `DELETE_PENDING`
  or `DELETED` returns the current projection **without the fingerprint check**.
- **Deviations (A-3):** the fingerprint replacement of step 4 (D-217 item 5 says earlier receipts
  keep their fingerprint); the replay without a fingerprint check for the other receipts (SRS
  line 1697, D-200); the change of the frozen `ParentStoryRunCancelEnvelopeV1` shape; the rewrite
  of pre-existing `CANCEL_RUN` bodies. Only the body of a pre-existing `CANCEL_RUN` receipt holds
  run content; the other bodies hold ids, revisions and hashes and are kept.

### 6.6 `exception` re-open

Only an owner-review command (separate work) re-opens. Resolving a retained asset is a manual
data fix outside FR-C-08 (port design §6.2); no Core release call and no release audit exist. The
command: (1) reads the keys and reasons through the port `review_report` before the fix;
(2) after the fix, runs the dry plan and re-opens only when it has an empty `retained` list
(port design §6.2); (3) sets the receipt to `requested` (CAS) and (4) inserts a new outbox event
of the same type with `event_id = UUIDv5(NS, request_id || ':' || event_type || ':reopen:' || n)`,
where `n` is the smallest integer ≥ 1 whose `event_id` does not exist. Steps 1, 2 and 4 are
already verified on the rerun, so only the missing steps run.

## 7. Access fence (D-214 item 6)

`DELETE_PENDING` and `DELETED` are treated alike by every Story writer, and `DELETED` is
terminal: the three S16 writers and every other writer of the Parent Story router path refuse
both states and update with `WHERE run_state NOT IN ('DELETE_PENDING','DELETED')`. A worker
result is accepted only by a compare-and-set on the dispatched `version`. The artwork route
re-checks the state before its first `put_object`; late objects are caught by the verifications
of steps 5 and 6. The StoryRun-lite demo writers are not part of this fence: that composition is
mounted instead of the Parent router (S19). Race evidence for each boundary is an
implementation-approval requirement.

## 8. Audit rows (metadata only)

| Action | Writer | `decision` | `audit_id` |
|---|---|---|---|
| `lifecycle.cancel_accepted` / `lifecycle.delete_accepted` | Story, §6.1 | `accepted:<request_id>` | rule 6, request-keyed |
| `lifecycle.completed` | Story, step 5 | `completed:<request_id>` | rule 6, request-keyed |
| `lifecycle.exception` | BE1, §6.2 and §6.3 | `exception:<request_id>` | rule 6, event-keyed |

Common: `audit_id` String(36); `decision` at most 46 characters (String(64)); scope
`PARENT_ACCOUNT`; `actor_ref` = Parent scope ref or `be1-lifecycle-worker`; `organization_id`
NULL; `resource_type = 'story_run'`; `resource_id = run_id`. Never stored: media, transcript,
idea, prompt, context, profile detail, storage key. Rows are inserted in the same transaction as
the state change and are insert-if-absent on the deterministic id. No reader; retention deferred.
There is no release audit row.

## 9. Migration

- One revision on its own branch: `down_revision = None`, `branch_labels = ("frc08_lifecycle",)`,
  `depends_on = ("20261112_parent_story_context",)`; it replaces that revision in
  `alembic_version`. Deploy uses `upgrade heads`; the README states that per-module
  `upgrade <branch>@head` commands skip this revision.
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
  scope ref; the database accepts `profile_ref IS NULL` for any run and only code requires it;
- every CHECK, including the Parent `completed` token pattern;
- a second cancel or delete on a `DELETE_PENDING` run is refused (409) and writes nothing;
- **token:** kill the worker at each crash point of §5.1 for each of the four steps (before the
  entry, after it, after the act, after the flip; for the asset step also after the objects,
  after the sweep, after the rows, and once with a failing verification), rerun, and compare the
  full receipt and the final `sha256` with a crash-free run; a run with no artwork completes with
  `asset=v:0:…`; an empty plan never overwrites an existing entry; a verified entry is never
  rewritten; the canonical string hashed is the persisted four segments;
- **sweep:** an orphan object written after step 3 is removed by the sweep of step 5 or 6 and the
  run completes; a sweep never edits an entry; a retained plan runs no sweep;
- two workers on one event: the CAS stops the second (a zero-row CAS inside an effect rolls back);
  a lost lease stops work; `limit = 1` claims; the bound ends in `exception` and delivers the
  event; the retained-asset `exception` also delivers the event and the old event does not
  return;
- step 3 `exception`: Story content purged, run stays `DELETE_PENDING`, nothing deleted in Core;
- the reconciliation command inserts one event per eligible run and nothing on a second run; a
  re-open uses a fresh event id and a second `lifecycle.exception` gets a fresh `audit_id`;
- GET, both 202 bodies, `read_current_input`, the artwork route and every replay of a purged run
  return only the projection or the stored body, with no error on `DELETE_PENDING` after step 4
  or on `DELETED`; a cancel replay with a changed payload still returns 400;
- `fail_drawing_analysis`, `fail_story_revision` and `complete_story_revision` cannot change a
  `DELETED` run;
- audit rows hold only §8 fields, are not duplicated by a rerun, and fit their column lengths;
- the School Admin data-request route, the BE1 retention worker and AI Jobs organization notices
  behave as before; `_EXPECTED_VERSION_ROWS` updated.

## 11. Items settled from the SRS (D-217, as amended)

| # | Item | Draft 5 |
|---|---|---|
| 1 | Audit owner scope | as D-217 item 1 |
| 2 | Events | cancel → `StoryRunCancellationRequestedV1`; delete → `StoryRunDeletedV1` (SRS 1845-1846); no completion event (**amends D-217 items 2-3**, A-2) |
| 3 | Retry | outbox lease, renewal, CAS, bound 10 (§6.3) |
| 4 | Responses | projection from `DELETE_PENDING` on; deviations in §6.5 and A-3 |
| 5 | `DELETE` route | as D-217 item 6; no expected revision per SRS line 1674 |
| 6 | Idempotency-Key | as D-217 item 7 |
| 7 | GET projection | `purge_state` from `run_state`; `lifecycle_request_ref` derived |
| 8 | Core predicate | port design Draft 5 |

## 12. Owner decisions at DTR approval

| ID | Decision | Recommendation |
|---|---|---|
| A-1 | Approve this DTR (after review) as the schema and migration direction | after review |
| A-2 | Amend D-217 items 2-3 as §11 row 2 | yes (SRS line 1846) |
| A-3 | Accept the response and replay deviations of §6.5: the cancel-envelope change, the rewrite of pre-existing `CANCEL_RUN` bodies, the fingerprint replacement on the other receipts (amends D-217 item 5), and the replay of those receipts without a fingerprint check | yes (SRS lines 1053, 1520; privacy need of S12) |
| A-4 | Accept nullable `profile_ref`, cleared on the tombstone | yes (SRS lines 270, 1056; coordinator inference) |
| A-5 | Accept no per-object deletion-state column (SRS line 1949) | yes for V1 (port design §9) |

## 13. Not verified

- Any database or storage behaviour; nothing was run.
- Whether another branch alters these tables after the base.
- The lifecycle consumer and the new ports do not exist yet; their runtime behaviour, the 300 s
  step limit and the 900 s lease are unproven.
- Whether `alembic` removes the dependency row from `alembic_version` as §9 assumes.
