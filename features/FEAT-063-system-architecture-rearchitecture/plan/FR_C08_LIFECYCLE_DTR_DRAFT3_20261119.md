# FR-C-08 Parent StoryRun lifecycle — data/table change request (DTR), Draft 3

**Status: DRAFT / NOT APPROVED.** Round-2 candidate of the DTR review wave.
**Date:** 2026-11-19.
**Purpose:** the exact schema delta, purge order and migration steps that D-214 items 3, 7, 8
and 9, D-215 items 1-3 and 6, D-216 items 3 and 5 and D-217 leave to a reviewed DTR. This
document approves nothing and grants no implementation, migration, database, storage, test,
route, push or merge authority.

**Change from Draft 2:** fixes the round-1 cold review
(`tmp/frc08-dtr/review-r1/FR_C08_DTR_DRAFT2_COLD_REVIEW_R1_20261119.md`, NEEDS REVISION,
3 P1 / 8 P2 / 9 P3) and aligns with Core port design Draft 2. Main changes: a single purge order
in which Story writes `DELETED` before BE1 closes the receipt (P1-1); asset removal before Story
clears its refs, with the Core rows kept as the retry manifest (P1-2); `DELETE_RUN` added to the
receipt CHECK (P1-3); the lifecycle consumer named as new work using the real outbox API
(P2-1); the port and model change list (P2-2); a deterministic lifecycle request id and a
Story-only `purge_state` (P2-3); the receipt reference in the audit row (P2-4);
`StoryRunDeletedV1` used as the delete trigger as SRS line 1846 reads (P2-5); pre-existing
`DELETE_PENDING` runs (P2-6); migration dependencies and tests (P2-7); every remaining private
field decided (P2-8); and all P3 notes. The Draft 2 coordinator choices recorded in D-217
items 2 and 3 change; §13 lists them for the owner.

## 1. Authority and pins

| Input | Pin |
|---|---|
| Canonical working SRS (D-209) | `artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`, 701,157 bytes, SHA-256 `B9B1F42D0BB118C19C81607D3913B7E4F1D8B6F673F0C3FBB6402888FEB675F5` |
| Companion data register | `artifacts/DATA_TABLE_REGISTER.md` Rev57 (supporting evidence only) |
| Owner decisions | FEAT-063 `DECISIONS.md` D-214 to D-217 (working tree, uncommitted; 255,902 bytes, SHA-256 `80313F4D…` after D-217) |
| Planning contract | `plan/FR_C08_PARENT_TEACHER_LIFECYCLE_CONTRACT_DRAFT8_20261119.md` (not approved) |
| Core port | `plan/FR_C08_CORE_REFERENCE_CLOSURE_PORT_DESIGN_DRAFT2_20261119.md` (round-2 candidate) |
| Code base (D-216 item 2) | `feature/feat066-conv1` at `03342207ab10379e6c53449274edaf4d9bcf60e4`, read in `.worktrees/conv1` |

Scope limits: Parent only (D-214 item 4); no new table and no new public StoryRun state
(D-215 item 2); no fabricated organization (SRS line 1048; register line 73); exact SQL and
migration steps need a separate owner approval (register line 204; D-216 item 3).

## 2. Covers / does not cover

**Covers:** typed owner scope on the lifecycle receipt, the AI Jobs cancellation notice, the
Core audit row, the Core outbox event and the Core aggregate revision; the `DELETED` run state,
the `DELETE_RUN` receipt operation and a nullable profile pointer on `story.runs`; the purge
order and its retry; the receipt token; the audit rows; the access fence; one migration.

**Does not cover (separate tasks or documents):** the Core port contract itself (port design
Draft 2); the route and response-schema change (next Contract and Allowlist revision); the SRS
wording edit (D-216 item 6); Teacher; retention periods and an audit reader (D-216 item 5); the
owner-review re-open command for an `exception` receipt (§6.5 names it as separate work).

## 3. Source facts at the base (read-only, `03342207`)

| # | Fact | Evidence |
|---|---|---|
| S1 | `be1_data_lifecycle_requests`: `request_id` PK, `organization_id` NOT NULL, `request_type` String(24), `target_ref` String(256), `state` CHECK (`requested, running, awaiting_external_purge, completed, exception`), `unresolved_items` ≥ 0, `result_ref` String(512) NULL, `requested_by`, `created_at`, `completed_at`. | `infrastructure/persistence/be1_models.py:555-578`; migration `20261014_0002` |
| S2 | Its writers are organization-scoped and never set `completed`: the School Admin data-request route (`requested`) and the BE1 retention worker (`awaiting_external_purge`). The read route filters by `organization_id`. | `interfaces/http/routers/be1_records.py:432-500`; `infrastructure/persistence/be1_worker.py:150-160` |
| S3 | `ai_jobs.cancellation_notice`: `organization_id` NOT NULL; port `CancellationNotice.organization_id` non-optional; job matching requires the same organization. | `infrastructure/ai_jobs/sql/tables.py:229-244`; `application/ports/ai_jobs.py:249-257`; `infrastructure/ai_jobs/sql/repository.py:888-939` |
| S4 | No Parent product run creates an `ai_jobs.job` row. The vision invocation ledger (fixed technical organization `storyrun-lite-photo-bridge-v1`) is used only by the StoryRun-lite photo bridge and the pilot composition, not by the Parent product routes. | `infrastructure/story_run_lite/photo_bridge.py:60, 160-168, 414-441`; `infrastructure/vision_analysis/ledger.py`; `pilot_composition.py` |
| S5 | `core_audit_entries.organization_id` NOT NULL, no scope column; the M2 Parent repository writes no audit row. | `infrastructure/persistence/core_models.py:187-203` |
| S6 | `core_asset_metadata` already has the typed owner-scope pattern (columns, CHECK `ck_core_asset_owner_scope`); migration `20261102_story_run_lite` also added a guard trigger and a downgrade guard. | `core_models.py:143-184`; `alembic/versions/20261102_story_run_lite.py:16-97, 584-592` |
| S7 | `core_outbox_events.organization_id` NOT NULL; FK `aggregate_id` → `core_aggregate_revisions` (`organization_id` NOT NULL). | `core_models.py:27-40, 206-242` |
| S8 | `ck_story_run_state` allows ten values; `DELETED` and `ABANDONED` cannot be stored. `story.runs.profile_ref` is NOT NULL. | `infrastructure/story_run_lite/tables.py:213-284` |
| S9 | The M2 Parent cancel sets `DELETE_PENDING`, releases the active lock, increments `revision`/`version`, stores a `FINAL` 202 receipt whose body is the full run envelope, and writes no lifecycle request, notice, event or audit row. | `infrastructure/persistence/parent_story_repository.py:328-438` |
| S10 | Run-owned private content: `story.run_inputs`, `understanding_revisions`, `review_decisions`, `story_revisions`, `story_scenes`, `story_revision_reviews`, `story.command_receipts` bodies; on `story.runs`: `asset_ref`, `derived_asset_ref`, `subject_label`, `confidence`, `result_sha256`, `raw_body_sha256`, `child_age_months`, `profile_ref`, `provider_job_id`, `provider_attempt_id`, `understanding_revision`, `error_code`; Core asset rows and objects (port design C1-C2). | `tables.py:213-606` |
| S11 | The Parent product routes write no `storyrun_upload_sessions`, `storyrun_upload_parts` or `core_upload_command_receipts` rows; those are written by the StoryRun-lite demo path. | `interfaces/http/routers/parent_ai.py`; `infrastructure/story_run_lite/repository.py:686` |
| S12 | `ck_story_receipt_operation` allows `CREATE_RUN, ATTACH_ASSET, CONFIRM_SUBJECT, CONFIRM_CONTEXT, CANCEL_RUN, GENERATE_STORY_REVISION, CONFIRM_STORY_REVISION`. | `tables.py:438-444`; recreated in `20261104_story_revisions.py:38-41`, `20261112_parent_story_context.py:196-199` |
| S13 | The cancel response `ParentStoryRunCancelEnvelopeV1` embeds the full `ParentStoryRunResponseV1`; `request_id` is a random per-call UUID; `purge_state` is the literal `PENDING`. | `contracts/schemas/parent_story_runs.py:148-151`; `interfaces/http/routers/parent_story_runs.py:270-294` |
| S14 | `PostgresOutbox` (`claim_ready`, `defer`, `process_local_once`) has no caller at the base; `claim_ready` has no event-type filter; `delivered` is global per event; `process_local_once` runs its effect inside the claim transaction and is for DB-only effects; `attempt_count` is unbounded. | `infrastructure/persistence/outbox.py:26-181` |
| S15 | Core ports carry a non-optional `organization_id`: `OutboxEnvelope`, `OutboxState`, `CoreAuditRecord`, `AggregateRevisionPort.current_revision`, `OutboxStatePort.get_state`. | `application/ports/core_foundation.py:60-66, 85-107, 126-127, 189-190`; `infrastructure/persistence/core_store.py:325-334` |
| S16 | Alembic: `20261101_be1_age_0001` and `20261015_ai_0001` are already dependencies of `20261102_pv_0001`, which `20261102_story_run_lite` depends on; the database head of the Story line is `20261112_parent_story_context`. The PG gate test pins the stored version rows. | `alembic/versions/20261102_pilot_vision.py:13`; `tests/integration/test_m2_s2_g1_parent_story_postgres.py:85-96` |

## 4. Design rules

1. **One owner-scope pattern** on every changed table: `owner_scope_kind` String(32) NOT NULL
   DEFAULT `'ORGANIZATION'`, `owner_scope_ref` String(128) NULL, `organization_id` nullable,
   and the two-branch CHECK of S6. Existing rows need no backfill. `GLOBAL` is not accepted
   (SRS line 1048). The S6 guard trigger is **not** copied: legacy rows keep a NULL scope ref,
   and the CHECK alone enforces the Parent branch.
2. **Parent scope value:** the Parent principal scope ref already stored in
   `story.runs.actor_scope_ref` (64 hex characters). No subject, email or account UUID.
3. **No new table, no new public state** (D-215 item 2).
4. **Owner modules keep their own evidence;** the receipt records verified outcomes only.
5. **Events through the Core outbox** in the owner's transaction (SRS lines 404, 904, 1778);
   cross-owner work by contract, idempotency receipt and saga (line 404).
6. **One deterministic lifecycle id per run:** `request_id = UUIDv5(LIFECYCLE_NS, 'story_run:' || run_id)`.
   Cancel and delete of the same run converge on it by construction; Story never stores it.

## 5. Schema delta

### 5.1 `be1_data_lifecycle_requests` (BE1 owns the receipt; SRS lines 1475, 1523, 2339)

| Change | Exact proposal |
|---|---|
| `organization_id` | `DROP NOT NULL` |
| `owner_scope_kind`, `owner_scope_ref` | new, rule 1 |
| CHECK `ck_be1_data_request_owner_scope` | rule 1 expression |
| CHECK `ck_be1_data_request_parent_completed` | `owner_scope_kind <> 'PARENT_ACCOUNT' OR state <> 'completed' OR (unresolved_items = 0 AND result_ref LIKE 'lcr1;%' AND completed_at IS NOT NULL)` — Parent rows only; organization rows are not constrained (coordinator choice, review P3-1) |

No new index: the primary key serves every Parent lookup because the id is deterministic (rule 6).
Parent row values: `request_type = 'delete'`, `target_ref = 'story_run:' || run_id`,
`requested_by` = the Parent principal scope ref.

| `state` | Meaning | `unresolved_items` |
|---|---|---|
| `requested` | Inserted by the consumer on first delivery of the run's event | 4 (owner steps of §6.2) |
| `running` | A step is in progress | steps not yet verified |
| `awaiting_external_purge` | A step failed or is not yet verifiable; the event is deferred for retry | steps not yet verified |
| `exception` | A shared or unresolvable reference, or the retry bound was reached; owner review | steps not yet verified |
| `completed` | All steps verified and Story has written `DELETED` | 0 |

**`result_ref` progress and token** (≤ 512 characters, no content). It is rewritten after each
verified step and is final at `completed`:
`lcr1;upload=<n>:<h16>;ai=<n>:<h16>;asset=<n>:<h16>;story=<n>:<h16>[;sha256=<h64>]`, where `<n>`
is the number of items the step removed or closed, `<h16>` the first 16 hex characters of the
step's digest (SHA-256 of the canonical JSON list of the step's sorted item identifiers), and the
final `sha256` is the SHA-256 of the canonical JSON of the four full step digests in step order.
A step's entry is written **before** the step's last destructive commit (§6.2), so a crash
cannot lose it (port review P2-4).

### 5.2 `ai_jobs.cancellation_notice` (SRS line 1523; register line 213)

`organization_id` `DROP NOT NULL`; `owner_scope_kind`, `owner_scope_ref` (rule 1,
`ck_cancellation_notice_owner_scope`); `story_run_ref` String(128) NULL with CHECK
`owner_scope_kind <> 'PARENT_ACCOUNT' OR story_run_ref IS NOT NULL`. A Parent notice has
`notice_id = 'lifecycle:' || request_id`, matches no job (S4) and is recorded `COMPLETE` with
`applied_count = 0`. Provider interruption relies on the fence (§7); it is never purge evidence
(D-214 item 6).

### 5.3 `core_audit_entries` (SRS `core.audit_events`; lines 1056, 2513; D-216 item 5)

`organization_id` `DROP NOT NULL`; `owner_scope_kind`, `owner_scope_ref` (rule 1,
`ck_core_audit_owner_scope`). No new index: FR-C-08 has no audit reader (review P3-2).

### 5.4 Story tables

| Table | Change |
|---|---|
| `story.runs` | Recreate `ck_story_run_state` with the ten values plus `'DELETED'` (`ABANDONED` has no producer and is not added). `profile_ref` `DROP NOT NULL` so the tombstone keeps no child-profile pointer (SRS lines 1055-1056; coordinator choice, review P2-8). |
| `story.command_receipts` | Recreate `ck_story_receipt_operation` with the seven values plus `'DELETE_RUN'` (review P1-3). |

### 5.5 `core_outbox_events` and `core_aggregate_revisions`

Both: `organization_id` `DROP NOT NULL`; `owner_scope_kind`, `owner_scope_ref` (rule 1;
`ck_core_outbox_owner_scope`, `ck_core_aggregate_owner_scope`). A Parent run's aggregate row is
keyed by `run_id` with `revision` = `story.runs.revision`. Payloads carry refs only.

### 5.6 Unchanged tables

`core_asset_metadata`, `core_asset_lineage`, `core_outbox_consumer_receipts`, the upload tables
(S11), the vision ledger (S4), and the other `story.*` tables.

### 5.7 Code that must change with the schema (for the implementation allowlist; not approved here)

| Area | Change |
|---|---|
| ORM / Core tables | `DataLifecycleRequestModel`, `CoreAuditEntryModel`, `CoreOutboxEventModel`, `CoreAggregateRevisionModel`: nullable `organization_id`, new scope fields; `ai_jobs` `cancellation_notice` table; `story_run_lite` tables (`runs`, `command_receipts`) |
| Core ports (S15) | `OutboxEnvelope`, `OutboxState`, `CoreAuditRecord`: optional `organization_id` plus owner scope; `AggregateRevisionPort` and `OutboxStatePort` gain scope-keyed reads; existing organization reads unchanged |
| Outbox (S14) | `claim_ready` gains an event-type filter so the lifecycle consumer claims only its events |
| AI Jobs port | `CancellationNotice`: optional `organization_id`, scope fields, `story_run_ref`; `jobs_for_notice` returns nothing for a Parent notice |
| Storage port | per port design Draft 2 (`list_keys(prefix)`) |
| Tests | `_EXPECTED_VERSION_ROWS` in `tests/integration/test_m2_s2_g1_parent_story_postgres.py`; the existing cancel/GET body assertions at lines 746, 1026, 1039 of that file |

## 6. Lifecycle flow

### 6.1 Command (one Story transaction; SRS lines 1520, 1673-1674)

Cancel (eligible: 13 SRS states plus the two documented extensions, D-216 item 4) or delete
(eligible: `COMPLETED`, `FAILED`, `ABANDONED`, D-214 item 1):
1. lock the run; idempotency check (operation `CANCEL_RUN` or `DELETE_RUN`); cancel also checks
   `expected_revision` (SRS line 1673); delete has none (line 1674 names none);
2. set `DELETE_PENDING`, clear `active_owner_parent_account_id`, increment `revision` and `version`;
3. upsert the Parent-scoped `core_aggregate_revisions` row and write one outbox event:
   `StoryRunCancellationRequestedV1` for cancel (SRS line 1845), `StoryRunDeletedV1` for delete
   (line 1846 lists it as the event of the delete lifecycle, with run ref, lifecycle request ref
   and scope); both carry `request_id` (rule 6), run ref, scope ref and a safe reason code;
4. write the audit row `lifecycle.cancel_accepted` or `lifecycle.delete_accepted` (§8);
5. store the receipt with the content-free lifecycle projection as its body (§6.4) and commit.

No completion event is emitted; completion is the stored `DELETED` state (coordinator choice; SRS
§22.5 names are proposals).

### 6.2 Purge (BE1 lifecycle consumer; new work, review P2-1)

The consumer claims only the two event types (`claim_ready` with a type filter), then works
**outside** the claim transaction, committing progress to the receipt after each step:

| Order | Owner | Step | Commit point | Verified when |
|---|---|---|---|---|
| 0 | BE1 | Insert the receipt if absent (`requested`, `unresolved_items = 4`), then `running` | receipt row | — |
| 1 | Core (upload) | Close and remove any upload session, parts and upload receipts that reference the run (none on the Parent product path, S11) | per session | no session, part or upload receipt for the run |
| 2 | AI Jobs | Record the Parent notice (§5.2) | notice row | notice row exists |
| 3 | Core Asset (port Draft 2) | Plan; delete objects; prove the run prefix is empty; write the step entry to `result_ref`; then delete lineage edges and metadata rows | objects first, rows last; Core rows stay as the manifest until objects are proven gone | no Core row names the run and the prefix lists empty |
| 4 | Story | Delete `run_inputs`, `understanding_revisions`, `review_decisions`, `story_revisions`, `story_scenes`, `story_revision_reviews` of the run; set every S10 column of `story.runs` except the identity, scope, state, revision and version columns to NULL, including `profile_ref` and `current_input_revision`; replace the body of **every** `story.command_receipts` row of the run, `CANCEL_RUN` included, with the lifecycle projection (keys, scopes and fingerprints kept) | one Story transaction | no child row; tombstone columns NULL; no receipt body with content |
| 5 | Story | Set `DELETED`, increment `revision` and `version`, write the audit row `lifecycle.completed` | one Story transaction, idempotent on `run_id` | `run_state = 'DELETED'` |
| 6 | BE1 | Set the receipt `completed` with the final token and `completed_at`, then mark the event delivered with `process_local_once` (DB-only effect) | one BE1 transaction | receipt `completed` |

Assets go before Story refs (review P1-2); Story writes `DELETED` before BE1 closes (review P1-1).
A crash after step 5 and before step 6 is finished on redelivery: the consumer sees `DELETED`
and only completes step 6.

**Retry:** on a step failure the consumer sets `awaiting_external_purge` and calls `defer` with
a growing delay. After 10 failed attempts (configurable) it sets `exception`, writes
`lifecycle.exception`, and marks the event delivered (coordinator choice for the bound). The SRS
basis is lines 1951 and 2144; the mechanism is the outbox API (S14), not the AI worker rule of
line 1780.

### 6.3 Pre-existing `DELETE_PENDING` runs (review P2-6)

Runs cancelled by the M2 code have no event. A one-time reconciliation command emits
`StoryRunCancellationRequestedV1` for every Parent `DELETE_PENDING` run that has no receipt. It
runs once after the migration, owner-run, on the target database only. All such runs at the
base are synthetic development data.

### 6.4 Responses and replay (D-217 item 5)

From `DELETE_PENDING` on, every Parent response for the run (GET, cancel 202, delete 202) is the
content-free projection: `run_id`, `run_state`, `revision`, `version`, `lifecycle_request_ref`
(= `request_id`, derived, not stored) and `purge_state`, which is `COMPLETED` exactly when
`run_state = 'DELETED'` and `PENDING` otherwise; Story is the only source (review P2-3). New
cancel and delete receipts store this body, so their replay returns the original body (SRS
line 1697). **Deliberate deviation:** the bodies of earlier receipts of the run (create,
confirmations, and pre-FR-C-08 `CANCEL_RUN`) are rewritten to the projection, so their replay
returns the projection, not the original body; and the frozen `ParentStoryRunCancelEnvelopeV1`
changes shape. Both go to the Contract revision and the owner (§13).

### 6.5 `exception` re-open (review P3-9)

An `exception` receipt is re-opened only by an owner-review command (separate work, not in
FR-C-08 routes) that records the reconciliation (for example, the Core `release_run_reference`
of port design Draft 2), sets the receipt to `requested` and writes a new outbox event of the
same type and `request_id`.

## 7. Access fence (D-214 item 6) over existing columns

Every Parent read of content, artwork attach, upload, job dispatch and late-result acceptance
re-reads the run and refuses when `run_state` is `DELETE_PENDING` or `DELETED`; a worker result
is accepted only with a compare-and-set on the dispatched `version`. The artwork route already
requires `INPUT_PROCESSING` (`parent_story_repository.py:554-555`); objects it wrote before the
refusal are caught by the prefix sweep of step 3. Race evidence for each boundary is an
implementation-approval requirement.

## 8. Audit rows (metadata only; SRS lines 1056, 2513)

| Action | Writer and transaction | `decision` |
|---|---|---|
| `lifecycle.cancel_accepted` / `lifecycle.delete_accepted` | Story, §6.1 | `accepted:<request_id>` |
| `lifecycle.completed` | Story, §6.2 step 5 | `completed:<request_id>` (the deletion receipt, review P2-4) |
| `lifecycle.exception` | BE1 consumer, retry bound or retained reference | `exception:<request_id>` |

Common fields: `audit_id = UUIDv5(LIFECYCLE_NS, request_id || ':' || action)` (a rerun cannot
duplicate the row), `owner_scope_kind = 'PARENT_ACCOUNT'`, `owner_scope_ref` and `actor_ref` =
the Parent scope ref (or `be1-lifecycle-worker` for the exception row), `organization_id` NULL,
`resource_type = 'story_run'`, `resource_id = run_id`. Never stored: media, transcript, idea,
prompt, context, profile detail, storage key. No reader; retention deferred (D-216 item 5).

## 9. Migration

- One revision on its own branch: `revision = "<date>_frc08_lifecycle_scope"`,
  `down_revision = None`, `branch_labels = ("frc08_lifecycle",)`,
  `depends_on = ("20261112_parent_story_context",)` (the BE1 and AI Jobs heads are already its
  ancestors, S16). It becomes the head that replaces `20261112_parent_story_context` in
  `alembic_version`; deploy keeps using `upgrade heads`.
- Order: §5.5 aggregate revisions, outbox; §5.1; §5.2; §5.3 (drop NOT NULL, add columns with
  server default, add CHECKs); then §5.4 (recreate the two CHECKs, drop NOT NULL on
  `profile_ref`). CHECKs are added directly; on the disposable verification database the scan
  and lock cost is accepted; a production rollout would use `NOT VALID` then `VALIDATE`.
- Downgrade refuses when any of the five tables has a `PARENT_ACCOUNT` row or an `ORGANIZATION`
  row with a non-NULL scope ref, when any run is `DELETED` or has a NULL `profile_ref`, or when
  any `DELETE_RUN` receipt exists; otherwise it reverses every step.
- Never against `sketch2life_m2_s1a`, `be1_acceptance`, or ports 5432 and 5433.

## 10. Verification required from the implementation task

- upgrade and downgrade on a fresh disposable database; upgrade over organization rows in all
  five tables with no row change; the downgrade guard cases;
- CHECK cases for every scope table, `DELETE_RUN`, `DELETED`, Parent `completed` without token;
- cancel and delete of the same run converge on one `request_id` and one receipt;
- each purge step rerun after a forced failure is a no-op once verified; a crash between steps 5
  and 6 completes on redelivery; the retry bound ends in `exception`;
- an orphan object under the run prefix is found and removed (port design Draft 2);
- GET and both 202 bodies hold only the projection from `DELETE_PENDING` on;
- audit rows hold only §8 fields and are not duplicated by a rerun;
- the School Admin data-request route, the BE1 retention worker and the AI Jobs organization
  notices behave as before; `_EXPECTED_VERSION_ROWS` updated.

## 11. Items settled from the SRS (D-217, as amended by this draft)

| # | Item | Draft 3 |
|---|---|---|
| 1 | Audit owner scope | as D-217 item 1 |
| 2 | Events | Cancel → `StoryRunCancellationRequestedV1`; delete → `StoryRunDeletedV1` (SRS lines 1845-1846); no completion event. **Changes D-217 items 2-3** |
| 3 | Retry | outbox `defer`, bound 10, then `exception` (not SRS line 1780) |
| 4 | Responses | as D-217 item 5, with the §6.4 deviation stated |
| 5 | `DELETE` route | as D-217 item 6; "no expected revision" rests on SRS line 1674, not 1697 |
| 6 | Idempotency-Key | as D-217 item 7 |
| 7 | GET projection | `purge_state` derived from `run_state` (Story only); `lifecycle_request_ref` derived |
| 8 | Core predicate | port design Draft 2 replaces DTR Draft 2 §7 |

## 12. Not verified

- Any database or storage behaviour; nothing was run.
- Whether another branch alters these tables after the base.
- The lifecycle consumer does not exist yet (S14); its runtime behaviour is unproven.

## 13. Owner decisions at DTR approval

| ID | Decision | Recommendation |
|---|---|---|
| A-1 | Approve this DTR (after its round-2 review) as the schema and migration direction | after review |
| A-2 | Amend D-217 items 2-3 as §11 row 2 | yes: follows SRS line 1846 and drops an invented event |
| A-3 | Accept the §6.4 replay deviation and the cancel-envelope shape change | yes: SRS lines 1053 and 1520 (revoke access at acceptance) outweigh replaying private content |
| A-4 | Accept `profile_ref` nullable and cleared on the tombstone | yes: SRS lines 1055-1056 |
