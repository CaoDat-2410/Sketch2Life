# FR-C-08 Parent StoryRun lifecycle — data/table change request (DTR), Draft 2

**Status: DRAFT / NOT REVIEWED / NOT APPROVED.**
**Date:** 2026-11-19.
**Purpose:** propose the exact schema delta and migration steps that D-214 items 3, 8 and 9,
D-215 items 1, 2, 3 and 6, and D-216 items 3 and 5 leave to a reviewed DTR. This document
approves nothing. It grants no implementation, migration, database, test, route, push or
merge authority. An owner approval of a reviewed revision is required before any migration
file is written.

**Change from Draft 1:** the open items of Draft 1 (OD-1, T-1, T-2) and the related contract
items were settled from the canonical SRS (§12, proposed for recording as D-217). As a result
the delta also covers the Core outbox and aggregate-revision tables (§5.6, §5.7), retry uses
the outbox lease (§5.1), and no response body of a purged run holds private content (§6).

## 1. Authority and pins

| Input | Pin |
|---|---|
| Canonical working SRS (D-209) | `artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`, 701,157 bytes, SHA-256 `B9B1F42D0BB118C19C81607D3913B7E4F1D8B6F673F0C3FBB6402888FEB675F5` (owner-supplied, unsigned) |
| Companion data register | `artifacts/DATA_TABLE_REGISTER.md` Rev57 (supporting evidence only, as in D-215) |
| Owner decisions | FEAT-063 `DECISIONS.md` D-214, D-215, D-216 (working tree, uncommitted; 251,420 bytes, SHA-256 `76A8DB17…` at the D-216 close-out) |
| Planning contract | `plan/FR_C08_PARENT_TEACHER_LIFECYCLE_CONTRACT_DRAFT8_20261119.md` (not approved) |
| Code base (D-216 item 2) | local branch `feature/feat066-conv1`, commit `03342207ab10379e6c53449274edaf4d9bcf60e4`; every source fact below was read in the `.worktrees/conv1` checkout at that commit |

Scope limits carried from the decisions: Parent only (D-214 item 4, D-215 item 7); no new
table and no new public StoryRun state (D-215 item 2); no fabricated organization for a Parent
(SRS line 1048; register line 73); exact SQL types and migration steps need a separate owner
approval (register line 204; D-216 item 3).

## 2. What this DTR covers and what it does not

**Covers:** the stored shape that a Parent cancel or delete needs: typed owner scope on the
lifecycle receipt, on the AI Jobs cancellation notice, on the Core audit row, and on the Core
outbox event and aggregate revision that carry the Story lifecycle events; the value
vocabulary of the receipt columns; the terminal `DELETED` value on `story.runs`; what each
owner module removes or keeps; the access fence over existing columns; the audit field and
reader matrix; one migration and its downgrade rule.

**Does not cover (separate tasks):**
- the Core reference-closure and storage-ownership port (D-214 item 7, D-215 item 3) — §7
  states only the data predicate it must enforce;
- the route and response-schema work itself (the `DELETE /v1/story-runs/{id}` route of SRS
  line 1674, the content-free lifecycle projection, `ABANDONED` and `DELETED` in the response);
  §12 records how the SRS settles them, and the next Contract and Allowlist revision carries
  them;
- the SRS wording edit at nine sites (D-216 item 6);
- the Teacher slice (P2) and any Teacher-scoped row;
- retention periods, the 180/365-day map and an audit reader (D-216 item 5).

## 3. Source facts at the base (read-only, `03342207`)

| # | Fact | Evidence |
|---|---|---|
| S1 | `be1_data_lifecycle_requests` (public schema, BE1 Core metadata) has `request_id` PK, `organization_id` NOT NULL, `request_type` String(24), `target_ref` String(256), `state` String(32) with CHECK `requested, running, awaiting_external_purge, completed, exception`, `unresolved_items` ≥ 0, `result_ref` String(512) NULL, `requested_by`, `created_at`, `completed_at`. | `infrastructure/persistence/be1_models.py:555-578`; created by `alembic/versions/20261014_0002_be1_runtime.py` |
| S2 | Two writers use it today, both organization-scoped: the School Admin data-request route (`request_type` `export` or `delete`, `state='requested'`) and the BE1 retention worker (`request_type='delete'`, `target_ref='session:<id>'`, `state='awaiting_external_purge'`). The read route filters by `organization_id`, so a row with no organization can never appear there. | `interfaces/http/routers/be1_records.py:432-500`; `infrastructure/persistence/be1_worker.py:150-160`; `contracts/schemas/be1_runtime.py:147-149` |
| S3 | `ai_jobs.cancellation_notice` has `notice_id` PK, `organization_id` NOT NULL, `reason_code`, `session_id`, `job_type`, `subject_ref`, `status` (only `COMPLETE`), `applied_count` ≥ 0, `recorded_at`. The port type `CancellationNotice` has a non-optional `organization_id`. Matching jobs requires `job.organization_id = notice.organization_id`. | `infrastructure/ai_jobs/sql/tables.py:229-244`; `application/ports/ai_jobs.py:249-257`; `infrastructure/ai_jobs/sql/repository.py:888-939`; migration branch `ai_jobs`, head `20261015_ai_0001` |
| S4 | No Parent StoryRun creates an `ai_jobs.job` row at the base. Parent provider work is tracked on `story.runs` (`provider_job_id`, `provider_attempt_id`, `dispatch_gate_open`) and, for the StoryRun-lite photo bridge, in the vision invocation ledger under the fixed technical organization value `storyrun-lite-photo-bridge-v1`. That bridge only admits the synthetic local Parent scope; it is a demo-profile path. | `infrastructure/story_run_lite/photo_bridge.py:60, 160-168, 414-441`; `infrastructure/story_run_lite/tables.py:213-284` |
| S5 | `core_audit_entries` has `organization_id` NOT NULL and no owner-scope column, so a Parent audit row cannot be written without a fabricated organization. The M2 Parent StoryRun repository writes no audit row. | `infrastructure/persistence/core_models.py:187-203`; `infrastructure/persistence/parent_story_repository.py` (no audit write) |
| S6 | `core_asset_metadata` already carries `owner_scope_kind` (default `ORGANIZATION`), `owner_scope_ref`, nullable `organization_id`, and CHECK `ck_core_asset_owner_scope`: a `PARENT_ACCOUNT` row has a non-empty scope ref and no organization; an `ORGANIZATION` row has an organization and a scope ref that is NULL or equal to it. Migration `20261102_story_run_lite` introduced this pattern. | `infrastructure/persistence/core_models.py:143-184`; `alembic/versions/20261102_story_run_lite.py:16-60` |
| S7 | `core_outbox_events.organization_id` is NOT NULL. | `infrastructure/persistence/core_models.py:206-242` |
| S8 | `story.runs.run_state` CHECK `ck_story_run_state` allows ten values: `INPUT_PROCESSING, SUBJECT_REVIEW, PREPARATION_REVIEW, SCRIPT_GENERATING, SCRIPT_GENERATION_UNKNOWN, SCRIPT_REVIEW, VIDEO_ADMISSION_PENDING, DELETE_PENDING, FAILED, COMPLETED`. `DELETED` and `ABANDONED` cannot be stored. | `infrastructure/story_run_lite/tables.py:251-258` |
| S9 | The M2 Parent cancel locks the run, checks idempotency and revision, accepts seven source states, sets `DELETE_PENDING`, clears `active_owner_parent_account_id`, increments `revision` and `version`, stores a `FINAL` 202 receipt whose `response_body` is the full run envelope, and commits. It writes no lifecycle request, notice or audit row. | `infrastructure/persistence/parent_story_repository.py:328-438` |
| S10 | Run-owned private content at the base: `story.run_inputs` (typed idea, context snapshot, original and derived asset refs), `story.understanding_revisions`, `story.review_decisions`, `story.story_revisions`, `story.story_scenes`, `story.story_revision_reviews`, `story.command_receipts` (full response bodies), `storyrun_upload_sessions`/`storyrun_upload_parts` (states include `ABORTED`), `core_asset_metadata` rows and `core_asset_lineage` edges for the run's assets, and the stored objects. | `infrastructure/story_run_lite/tables.py:28-100, 171-210, 286-606` |
| S12 | `core_aggregate_revisions` has `aggregate_id` PK and `organization_id` NOT NULL; `core_outbox_events.aggregate_id` is a foreign key to it. A Parent event therefore needs a Parent-scoped aggregate-revision row as well. | `infrastructure/persistence/core_models.py:27-40, 224-229` |
| S13 | The Parent cancel response `ParentStoryRunCancelEnvelopeV1` embeds the full `ParentStoryRunResponseV1` (including `context_snapshot` and story content), and the stored `FINAL` receipt keeps that body for replay. | `contracts/schemas/parent_story_runs.py:148-151`; `interfaces/http/routers/parent_story_runs.py:276-283`; S9 |
| S11 | Alembic heads at the base include `20261101_be1_age_0001` (`be1_core` line), `20261015_ai_0001` (`ai_jobs`) and `20261112_parent_story_context` (`story_run_lite`). `core_audit_entries` and `be1_data_lifecycle_requests` were created by `20261014_0001` and `20261014_0002`, the root of the `be1_core` line. | `alembic heads` (script read only, no database) |

## 4. Design rules

1. **One owner-scope pattern.** Every changed table copies S6 exactly: `owner_scope_kind`
   String(32) NOT NULL DEFAULT `'ORGANIZATION'`, `owner_scope_ref` String(128) NULL,
   `organization_id` made nullable, and the same two-branch CHECK. Existing rows stay valid
   with no backfill (they are `ORGANIZATION` with an organization and a NULL scope ref).
   `GLOBAL` is not accepted on these tables (SRS line 1048: never the owner of a run or media).
2. **Parent scope value.** For a Parent row, `owner_scope_ref` is the Parent principal scope
   reference already used by `story.runs.actor_scope_ref` (SHA-256 of the canonical
   issuer/subject JSON, 64 hex characters). No subject, email or account UUID is stored in
   these columns.
3. **No new table, no new public state** (D-215 item 2). Retry and per-owner progress live in
   the existing `state`, `unresolved_items` and `result_ref` columns.
4. **Owner modules keep their own durable evidence.** Each owner step is idempotent and leaves
   a state that the coordinator can verify by query; the receipt records the verified outcome,
   not a claim.
5. **Events through the Core outbox, as the SRS requires.** A state-changing command writes its
   aggregate revision and outbox event in the owner's transaction (SRS lines 404, 904, 1778),
   and a flow across owners uses contract, idempotency receipt and saga, not a cross-module SQL
   transaction (line 404). The Story events `StoryRunCancellationRequestedV1` (payload: run
   ref, actor ref, expected revision, lifecycle request ref, safe reason code) and
   `StoryRunDeletedV1` (run ref, lifecycle request ref, scope) are named at SRS lines
   1845-1846. `core_outbox_events` is the Core-owned domain-event outbox (line 845). Because
   it and `core_aggregate_revisions` cannot hold a Parent scope today (S7, S12), both get the
   same owner-scope delta (§5.6, §5.7); no new table is added.

## 5. Proposed delta

### 5.1 `be1_data_lifecycle_requests` (BE1 owns the receipt; SRS lines 1475, 1523, 2339)

| Change | Exact proposal |
|---|---|
| `organization_id` | `ALTER … DROP NOT NULL` |
| `owner_scope_kind` | new, String(32) NOT NULL, server default `'ORGANIZATION'` |
| `owner_scope_ref` | new, String(128) NULL |
| CHECK `ck_be1_data_request_owner_scope` | `(owner_scope_kind = 'PARENT_ACCOUNT' AND owner_scope_ref IS NOT NULL AND length(owner_scope_ref) > 0 AND organization_id IS NULL) OR (owner_scope_kind = 'ORGANIZATION' AND organization_id IS NOT NULL AND (owner_scope_ref IS NULL OR (length(owner_scope_ref) > 0 AND owner_scope_ref = organization_id)))` |
| CHECK `ck_be1_data_request_completed` | `state <> 'completed' OR (unresolved_items = 0 AND result_ref IS NOT NULL AND completed_at IS NOT NULL)` — the receipt cannot claim completion without its evidence |
| Unique index `uq_be1_data_request_active_target` | on `(owner_scope_kind, owner_scope_ref, request_type, target_ref)` `WHERE owner_scope_kind = 'PARENT_ACCOUNT'` — one purge receipt per Parent run; cancel and delete of the same run converge on it |
| Index `ix_be1_data_request_scope_state` | on `(owner_scope_kind, owner_scope_ref, state)` `WHERE owner_scope_ref IS NOT NULL` |

The existing index `ix_be1_data_request_org_state` stays.

**Parent row values.** `request_type = 'delete'` (both cancel and delete use the same purge,
SRS line 1053); `target_ref = 'story_run:' || run_id`; `requested_by` = the Parent principal
scope reference (not the subject).

**Who writes the receipt.** The Story command (cancel or delete) generates the lifecycle
`request_id`, commits the run change with its outbox event that carries that ref (S12, §5.6),
and returns. The BE1 lifecycle consumer reads the event, inserts the receipt with that
`request_id` (idempotent on the primary key and on `uq_be1_data_request_active_target`), and
drives the owner steps of §6. Its progress is recorded in `core_outbox_consumer_receipts`
only when the receipt reaches `completed` or `exception`.

**State vocabulary for a Parent purge** (existing CHECK values, no change):

| `state` | Meaning | `unresolved_items` | `result_ref` |
|---|---|---|---|
| `requested` | Inserted by the BE1 consumer from the Story event; the run is already `DELETE_PENDING` and the active lock is already released in the Story transaction (SRS line 1520). | number of owner steps (§6), 5 | NULL |
| `running` | A worker holds the request and is calling owner steps. | steps not yet verified | NULL |
| `awaiting_external_purge` | At least one step failed or is not yet verifiable; it is retried idempotently and the run stays `DELETE_PENDING` (SRS lines 1473, 1951, 2144). | steps not yet verified | NULL |
| `exception` | A shared or unclear reference needs owner review; nothing more is purged automatically (SRS line 2146). | steps not yet verified | NULL |
| `completed` | Every step verified; the run becomes `DELETED` in the same transaction. | 0 | completion token (below) |

**Completion token in `result_ref`** (no content, ≤ 512 characters):
`lcr1;story=<n>;asset=<n>;upload=<n>;ai=<n>;audit=<n>;sha256=<64 hex>`, where each `<n>` is the
number of items the step removed or closed, and the hash is the SHA-256 of the canonical JSON
list of removed item identifiers (asset refs and versions, upload session ids, row ids), sorted.
It is the deletion receipt that the audit row references (SRS line 1056).

**Retry (T-1, settled).** No column is added. The outbox row already holds the lease and
retry fields (`status`, `attempt_count`, `available_at`, `lease_owner`, `lease_until`;
S7), which is the worker lease and heartbeat of SRS line 1780. While a step is not
verified, the consumer leaves the event undelivered, sets the receipt to
`awaiting_external_purge`, and the dispatcher redelivers it; each redelivery reruns only
unverified steps (SRS lines 1951, 2144).

### 5.2 `ai_jobs.cancellation_notice` (SRS line 1523; register line 213)

| Change | Exact proposal |
|---|---|
| `organization_id` | `ALTER … DROP NOT NULL` |
| `owner_scope_kind`, `owner_scope_ref` | new, same types, default and CHECK pattern as §5.1 (`ck_cancellation_notice_owner_scope`) |
| `story_run_ref` | new, String(128) NULL; CHECK `owner_scope_kind <> 'PARENT_ACCOUNT' OR story_run_ref IS NOT NULL` |

**Port change (code, listed for the implementation allowlist, not approved here):**
`CancellationNotice.organization_id` becomes optional and the type gains `owner_scope_kind`,
`owner_scope_ref` and `story_run_ref`; `jobs_for_notice` returns no rows for a
`PARENT_ACCOUNT` notice, because no Parent job exists in `ai_jobs.job` (S4) and that table has
no Parent scope. The notice is still recorded (`status='COMPLETE'`, `applied_count=0`) with
`notice_id = 'lifecycle:' || request_id`, which makes it idempotent and gives the SRS-named
record (line 1523). Interrupting Parent provider work relies on the access fence (§8): a late
result is stale and is purged (SRS line 1521). Provider cancellation stays best-effort and is
never purge evidence (D-214 item 6).

### 5.3 `core_audit_entries` (lifecycle audit, D-216 item 5; SRS line 1056; register line 198)

| Change | Exact proposal |
|---|---|
| `organization_id` | `ALTER … DROP NOT NULL` |
| `owner_scope_kind`, `owner_scope_ref` | new, same pattern as §5.1 (`ck_core_audit_owner_scope`) |
| Index `ix_core_audit_scope_created` | on `(owner_scope_kind, owner_scope_ref, created_at)` `WHERE owner_scope_ref IS NOT NULL` |

**OD-1, settled from the SRS.** D-216 item 3 named only the receipt and the notice. This table
is required because D-216 item 5 asks FR-C-08 to write lifecycle audit rows, the SRS keeps a
metadata-only deletion audit for Parent runs (lines 1056, 2513 BR-34), a Parent is never an
organization (line 1048), and the register says Core tables gain `OwnerScopeRefV1` when
needed (register line 198). The SRS name `core.audit_events` maps to the physical table
`core_audit_entries`.

### 5.4 `story.runs` terminal value

Replace CHECK `ck_story_run_state` with the same ten values plus `'DELETED'`. `ABANDONED` is not
added: no producer exists at the base, and nothing in this slice writes it. The other SRS
states that cannot be stored (S8) cannot occur, so the cancel command may list all 13
SRS-eligible states plus the two documented extensions (D-216 item 4) without a schema change.

### 5.6 `core_outbox_events` (Story lifecycle events; SRS lines 845, 1845-1846)

| Change | Exact proposal |
|---|---|
| `organization_id` | `ALTER … DROP NOT NULL` |
| `owner_scope_kind`, `owner_scope_ref` | new, same pattern as §5.1 (`ck_core_outbox_owner_scope`) |

Event payloads carry refs only (run ref, lifecycle request ref, scope ref, safe reason code),
never media, transcript, prompt or profile detail (SRS line 1845; §22.5 envelope rule). The
existing ready and lease indexes serve the Parent rows unchanged.

### 5.7 `core_aggregate_revisions` (outbox foreign key)

| Change | Exact proposal |
|---|---|
| `organization_id` | `ALTER … DROP NOT NULL` |
| `owner_scope_kind`, `owner_scope_ref` | new, same pattern as §5.1 (`ck_core_aggregate_owner_scope`) |

For a Parent run the row is keyed by `run_id`, its `revision` follows `story.runs.revision`, and
its scope is the Parent principal scope reference.

### 5.5 Tables with no schema change

`core_asset_metadata` (already typed, S6), `core_asset_lineage`, `core_outbox_consumer_receipts`
(no scope column), `storyrun_upload_sessions`, `storyrun_upload_parts`, and every `story.*`
table other than `runs`.

## 6. Owner steps of one Parent purge (what is removed, what is kept)

The coordinator runs these steps in order; each is idempotent and verifiable.

| # | Owner module | Removes or closes | Keeps | Verification query |
|---|---|---|---|---|
| 1 | Story | `run_inputs`, `understanding_revisions`, `review_decisions`, `story_revisions`, `story_scenes`, `story_revision_reviews` rows of the run; the response bodies of the run's earlier `story.command_receipts` (create and confirmations) are replaced by the content-free lifecycle projection, while the receipt keys, scopes and fingerprints are kept | the `story.runs` row as a tombstone; on that row `asset_ref`, `derived_asset_ref`, `subject_label`, `confidence`, `result_sha256`, `raw_body_sha256`, `child_age_months` are set to NULL | no child row for the run; tombstone columns NULL |
| 2 | Core Asset (port, §7) | object bytes, `core_asset_metadata` rows and `core_asset_lineage` edges of run-owned assets of this Parent scope | any asset with another valid reference (step goes to `exception`) | no metadata, lineage or object for the removed refs |
| 3 | Upload | open `storyrun_upload_sessions` of the run set to `ABORTED`; their parts removed | — | no non-terminal session or part for the run |
| 4 | AI Jobs | records the Parent notice (§5.2) | — | notice row exists |
| 5 | Audit | writes the completion audit row (§9) | — | audit row exists |

When all five are verified, the BE1 receipt is set to `completed` with the token and
`completed_at`; Story then sets the run to `DELETED` with incremented `revision` and `version`
and emits `StoryRunDeletedV1` in its own transaction (SRS lines 404, 1846). Until Story has
done so the run stays `DELETE_PENDING`. The
GET then reports `DELETED`; before that it reports `DELETE_PENDING` (SRS lines 805, 1520, 1951;
D-215 item 5).

**Preserved (SRS lines 1053, 1521, 1522):** consumed quota usage (no Parent quota row exists at the
base; when Billing adds one it is never refunded by a purge) and the Teacher sample claim (not
in this Parent-only slice).

**Replay after purge (T-2, settled).** Access is revoked when the command is accepted (SRS
lines 1053, 1520), so from `DELETE_PENDING` on, every Parent response for the run, including
the 202 body of cancel or delete, is the content-free lifecycle projection: run id, run state,
revision and version, lifecycle request ref and purge state (`PENDING` or `COMPLETED`), with no
context snapshot, story, candidate, subject label or asset ref. The stored cancel/delete
receipt therefore holds no private content and a replay returns exactly the original body (SRS
line 1697). Earlier receipts of the run (create, confirmations) keep their key and fingerprint,
so the key can never create a second run, and their body becomes the same projection.

## 7. Core reference-closure predicate (for the separate port design)

V1 has no asset sharing between runs (SRS line 1952), so the port verifies, it does not count
references. An asset ref of the run may be removed only when all of these hold:
- its `core_asset_metadata` row is `PARENT_ACCOUNT` with the same `owner_scope_ref` as the run;
- no `story.runs` or `story.run_inputs` row of **another** run references it;
- it is not a `source_refs` entry or `derived_from_ref` of an asset that is being kept;
- no `core_asset_lineage` edge links it to an asset that is being kept.

Otherwise the request goes to `exception` and nothing in that lineage group is purged (SRS
lines 1054, 2146; register lines 78, 547). The port shape, storage-key ownership and object
deletion API are the separate Core task (D-214 item 7).

## 8. Access fence (D-214 item 6) over existing columns

No schema change. The fence is `story.runs.run_state` with `version`:
- every Parent read of content, artifact download or playback, stream or cache fill, upload
  part or completion, job dispatch and late-result acceptance re-reads the run under the same
  transaction and refuses when `run_state` is `DELETE_PENDING` or `DELETED`;
- a worker result is accepted only with a compare-and-set on the `version` it was dispatched
  with; the cancel increments `version`, so every older result is stale;
- the lifecycle coordinator itself is the only writer after `DELETE_PENDING`.

Race evidence for each boundary is an implementation-approval requirement (Contract Draft 8
§3.5), not part of this DTR.

## 9. Audit matrix (D-214 item 9, D-215 item 6, D-216 item 5)

| Field | Value for a Parent lifecycle row |
|---|---|
| `audit_id` | UUID |
| `owner_scope_kind`, `owner_scope_ref` | `PARENT_ACCOUNT`, Parent principal scope reference |
| `organization_id` | NULL |
| `actor_ref` | Parent principal scope reference (accepted command) or `be1-lifecycle-worker` (completion, exception) |
| `action` | `lifecycle.cancel_accepted`, `lifecycle.delete_accepted`, `lifecycle.completed`, `lifecycle.exception` |
| `resource_type` | `story_run` |
| `resource_id` | `run_id` |
| `decision` | `accepted`, `completed` or `exception`; for `completed`, the receipt `request_id` is recoverable from the receipt row, whose `result_ref` is the deletion receipt |
| `created_at` | server time |

Never stored: media, transcript, typed idea, prompt, context snapshot, profile detail, storage
key. **Reader:** none in FR-C-08. **Retention:** the 180/365-day record-type map and the
physical retention job stay deferred and must be fixed before the real-data gate (SRS lines
656, 1057, 2758; D-216 item 5).

## 10. Migration plan (proposal; no file is written by this DTR)

- **Tables:** §5.1, §5.2, §5.3, §5.6, §5.7 (owner-scope delta) and §5.4 (`story.runs` CHECK).
- **One new Alembic revision** on its own branch, following the `20261102_story_run_lite`
  precedent: `revision = "20261120_frc08_lifecycle_scope"` (date set at approval),
  `down_revision = None`, `branch_labels = ("frc08_lifecycle",)`,
  `depends_on = ("20261101_be1_age_0001", "20261015_ai_0001", "20261112_parent_story_context")`.
- **Upgrade order:** §5.7, §5.6, §5.1, §5.2, §5.3 (drop NOT NULL, add columns with server
  default, add CHECKs and indexes), then §5.4 (drop and recreate `ck_story_run_state`). All steps are
  additive or widening; existing rows need no backfill.
- **Downgrade:** refuses (raises) when any row has `owner_scope_kind = 'PARENT_ACCOUNT'` in the
  five tables or any `story.runs` row is `DELETED`; otherwise it restores the original CHECK
  and drops the added columns, indexes and constraints, then restores NOT NULL.
- **Never** run against `sketch2life_m2_s1a`, `be1_acceptance`, or ports 5432 and 5433.
  Verification is owner-run on a disposable database fixed by the implementation approval.

## 11. Verification required from the later implementation task

- migration upgrade and downgrade on a fresh disposable database, and upgrade over a database
  that already holds organization rows in all five tables (no row changes);
- CHECK tests: a `PARENT_ACCOUNT` row with an organization fails; an `ORGANIZATION` row with a
  different scope ref fails; `completed` without token fails;
- unique index: a second Parent purge receipt for the same run fails; cancel and delete
  converge on one receipt;
- purge steps: each step rerun after a simulated failure is a no-op once verified; a shared
  reference sends the request to `exception` and purges nothing in that group;
- GET shows `DELETE_PENDING` until the completing transaction and `DELETED` after it;
- audit rows hold only the §9 fields;
- the School Admin data-request route and the BE1 retention worker behave exactly as before.

## 12. Items settled from the SRS (proposed for recording as D-217)

The owner asked for the open FR-C-08 items to be settled from the canonical SRS (pinned in §1).
Each line names the governing SRS text.

| # | Item | Settled as | SRS basis |
|---|---|---|---|
| 1 | OD-1: owner scope on the Core audit table | Yes (§5.3) | lines 1048, 1056, 2513; register line 198; D-216 item 5 |
| 2 | Lifecycle events and outbox | Story emits `StoryRunCancellationRequestedV1` on cancel and `StoryRunDeletedV1` at completion through `core_outbox_events`; owner scope added to the outbox and aggregate-revision tables (§5.6, §5.7) | lines 404, 845, 904, 1778, 1845-1846 |
| 3 | Delete-request event | The SRS catalog has no event for deleting a finished run; the event names are proposals (§22.5 heading). Delete emits `StoryRunDeletionRequestedV1` with the same payload as the cancellation event; this is a coordinator choice for the review to confirm | lines 1674, 1845-1846 |
| 4 | T-1: retry fields | No new column; retry and lease use the outbox row | lines 1780, 1951, 2144 |
| 5 | T-2 and response content | From `DELETE_PENDING` on, every Parent response for the run (GET, cancel 202, delete 202) is a content-free lifecycle projection; replay returns the original body | lines 1053, 1520, 1673-1674, 1697, 1736, 1811 |
| 6 | `DELETE /v1/story-runs/{id}` | In FR-C-08: eligible states `COMPLETED`, `FAILED`, `ABANDONED` (D-214 item 1); Idempotency-Key required; no expected revision; 202 with the lifecycle projection; same purge and receipt as cancel; a second request for the same run converges on the same receipt | lines 1674, 1697; D-214 item 1 |
| 7 | Idempotency-Key range on the FR-C-08 routes | Cancel and delete use the CONV-1 rule (1-128 visible ASCII; D-066-68 C-D5). The other four Parent POST routes keep 1-256 and are out of FR-C-08 scope | line 1697 (key per principal, operation and target); D-066-68 |
| 8 | GET lifecycle projection | Adds `lifecycle_request_ref` and `purge_state` (`PENDING`, `COMPLETED`); reports `DELETED` only after Story has written it; no percentage, counts, content or storage key | lines 805, 1736, 1809, 1811, 1951; D-215 item 5 |
| 9 | Core reference-closure predicate | §7 as written; the port design stays a separate task | lines 1052-1054, 1949, 1952, 2144-2146 |

**Still owner-only after this:** approval of this DTR after its independent review (with the
migration steps of §10), the separate Core port design, the response-schema and route work in
the next Contract and Allowlist revision with its review (the five-round limit of wave 1 is
spent, so the new wave needs the owner's go-ahead), the SRS wording edit at the nine sites, and
the implementation approval.

## 13. Not verified

- Any database behaviour; nothing was run against a database.
- Whether a later migration on another branch alters these tables after the base.
- Runtime reachability of any route or worker.
