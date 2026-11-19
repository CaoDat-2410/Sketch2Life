# FR-C-08 Core reference-closure and storage-ownership port — design, Draft 6

**Status: DRAFT / NOT APPROVED.** Draft 6 = Draft 5 (round 5, the last round allowed by the
five-round cap: READY WITH NOTES, 0 P1 / 0 P2 / 5 P3) plus the five P3 notes; the fixes of Draft 6
are not reviewed (no sixth round). V1 stays
simplified as the owner chose: any retained asset sends the request to `exception` with no asset
deleted, and there is no release path.
**Date:** 2026-11-19.
**Purpose:** the Core Asset contract that D-214 item 7 and D-215 item 3 require before FR-C-08
can be implemented. This document approves nothing and grants no implementation, command,
database, storage or test authority.

**Change from Draft 5.** Applies the round-5 review
(`tmp/frc08-goal/review-port-r5/FR_C08_CORE_PORT_DESIGN_DRAFT5_COLD_REVIEW_R5_20261119.md`, READY
WITH NOTES, 0 P1 / 0 P2 / 5 P3). The lifecycle DTR is changed in the same step
(`plan/FR_C08_LIFECYCLE_DTR_DRAFT6_20261119.md`). The mapping of Draft 4 to the earlier rounds is
in Draft 5 and is not repeated.

| Finding | Fix in Draft 6 |
|---|---|
| P3-1 "empty plan" undefined; a retained plan has count 0 | §5.1 defines it (no candidates); a plan with a non-empty `retained` list is never empty; §12 assertion |
| P3-2 sweep "safe at any time" | §5.1: precondition, only for a run in `DELETE_PENDING` or `DELETED`; "at any time" removed |
| P3-3 `run_ref` shape rule admits misplaced hyphens | §4 item 6: equals `str(UUID(value))`; §12 test |
| P3-4 review report and exit rules cover only retention | `ReviewReport.listed_candidate_keys` for a stuck delete; §6.2 says a Story-side reference is cleared in Story data and a re-open after a non-retention exception is a plain retry |
| P3-5 step 6 failure branch; "every attempt" wording | DTR step 6 fails the attempt when still not complete; §6.3 step 3 wording |
| DTR N4-2(b) asset element form | the canonical JSON elements are `asset_ref` strings (§5.1) |

## 1. Pins

| Input | Pin |
|---|---|
| Canonical SRS (D-209) | 701,157 bytes, SHA-256 `B9B1F42D0BB118C19C81607D3913B7E4F1D8B6F673F0C3FBB6402888FEB675F5` |
| Decisions | FEAT-063 D-214 items 6-7, D-215 item 3, D-216, D-217 (working tree) |
| Companion | `plan/FR_C08_LIFECYCLE_DTR_DRAFT6_20261119.md` (round 4: READY WITH NOTES; Draft 6 carries its P3 fixes, unreviewed); it owns the token and the coordinator order |
| Code base | `feature/feat066-conv1` at `03342207`, read in `.worktrees/conv1` |

## 2. SRS requirements

SRS lines 805 (no cross-schema SQL), 1004 (Core owns asset metadata/lineage and upload records),
1052-1054 (asset identity; purge every eligible object and metadata; a still-referenced asset is
deleted only when no valid reference remains), 1473 (retry idempotently; keep shared assets until
other references are reconciled), 1949-1952 (owner scope and deletion state per object;
idempotent batches; not complete until all objects are reconciled; **no sharing between runs in
V1**), 2144-2146 (pending until refs reconciled; no object key in client errors; unclear shared
references go to owner review and are not purged); register lines 78 and 547.

## 3. Source facts at the base

| # | Fact | Evidence |
|---|---|---|
| C1 | The Parent artwork route reads the run, scans and prepares the image, writes two objects through `app.state.lesson_library_storage`, then calls `attach_artwork`. Key = asset ref: `parent/{run_id}/{hex}/original`, `parent/{run_id}/{hex}/normalized.png`. | `interfaces/http/routers/parent_ai.py:236-240, 281-310`; `interfaces/http/app.py:1084-1093` |
| C2 | `attach_artwork` refuses unless `INPUT_PROCESSING`, then writes two `core_asset_metadata` rows (`PARENT_ACCOUNT`, organization NULL, scope ref = Parent principal scope ref, `source_refs = [run_id]`, `asset_version = 1`; normalized row `derived_from_ref` = original) and one lineage edge. | `infrastructure/persistence/parent_story_repository.py:539-660` |
| C3 | `core_asset_lineage` has `RESTRICT` FKs from source and derived refs to `core_asset_metadata`. | `alembic/versions/20261102_story_run_lite.py:295-304` |
| C4 | `CoreAssetMetadataPort` has no Parent read, reference query or deletion. | `application/ports/core_foundation.py:181-186` |
| C5 | `ObjectStoragePort`: `put_object`, `get_object` (`None` on `NoSuchKey` and `NoSuchBucket`), `delete_object`; S3 `DeleteObject` does not report whether the key existed. | `application/ports/object_storage.py:27-40`; `infrastructure/storage/s3_compatible.py:81-105` |
| C6 | A failed attach deletes both keys best-effort and swallows `ObjectStorageFailure`. | `parent_ai.py:311-325` |
| C7 | No Parent product run stores scene, video or audio objects at the base. | `infrastructure/story_run_lite/tables.py:498-606` |
| C8 | Lesson Library keys differ from asset refs; prefixes are disjoint (`lesson-library/…`, `parent/…`). The StoryRun-lite demo path writes `source_refs = []`. | `infrastructure/lesson_library/service.py:850-851`; `infrastructure/story_run_lite/repository.py:1077, 1089` |
| C9 | The combined-profile S3 adapter uses `storage_example_settings` (`s3_bucket`, `s3_endpoint`, `s3_region`, `s3_access_key`, `s3_secret_key`); a test fake of the port exists. The existing BE1 worker is a separate argparse CLI. | `app.py:1084-1093`; `tests/integration/lesson_library/test_lesson_library_api.py:68`; `infrastructure/persistence/be1_worker.py` |

## 4. Ownership

1. Core Asset alone deletes `core_asset_metadata`, `core_asset_lineage` and the objects they name.
2. Story owns run-to-asset references and answers through a Story port (§5.2); Core never reads
   `story.*` (SRS line 805).
3. **Bucket (V1):** Parent objects stay in the bucket of the C9 settings. **The V1 worker uses the
   application's key pair from those settings**; a separate least-privilege principal (list on
   `parent/`, delete on `parent/*`) is a deployment follow-up before real data, not part of
   FR-C-08.
4. Only `parent/{run_ref}/` keys are ever deleted; lesson sources are unreachable.
5. Upload records and `QuarantineStore` files of the StoryRun-lite demo path are out of scope;
   the DTR's upload step closes any upload record that names the run.
6. **`run_ref`** is the canonical lower-case string form of `story.runs.run_id` (a UUID, the bare
   id used in C1 and C2), never `story_run:…`. Every Core port entry validates its shape (36
   characters; equals `str(UUID(value))`, the 8-4-4-4-12 lower-case form, so misplaced hyphens fail) and raises the typed error
   `RUN_REF_INVALID` before any read, list or delete; a malformed value is never read as
   "nothing to do".
7. **Token ownership.** The lifecycle DTR owns the receipt entry and the final token (DTR §5.1).
   Nothing in this port reads or writes an entry.

## 5. Ports

### 5.1 Core: `RunAssetPurgePort`

```text
closure_candidates(scope, run_ref) -> CandidateSet                        # read-only
plan_run_purge(candidates, referenced_elsewhere: frozenset[str]) -> RunAssetPurgePlan
purge_objects(plan) -> ObjectPurgeResult       # pre-check, then delete removable objects only
sweep_run_prefix(scope, run_ref) -> SweepResult # idempotent; independent of any plan or entry
delete_rows(plan, referenced_elsewhere_now: frozenset[str]) -> RowPurgeResult
verify_run_purged(scope, run_ref) -> RunAssetPurgeVerification
review_report(scope, run_ref, referenced_elsewhere: frozenset[str]) -> ReviewReport  # operator-side only

CandidateSet:      scope, run_ref, assets: tuple[AssetKey, ...], edges
RunAssetPurgePlan: scope, run_ref, referenced_elsewhere (sorted), removable: tuple[AssetKey, ...],
                   retained: tuple[RetainedAsset, ...],
                   removable_key_count, removable_digest (64 lower-case hex of the SHA-256 of the
                   canonical JSON array of the sorted removable `asset_ref` strings (version is always 1); `[]` when empty), plan_sha256
AssetKey:          asset_ref, asset_version (always 1 in V1, C2)
RetainedAsset:     key, reason_code  (SHARED_REFERENCE | SCOPE_MISMATCH | KEY_UNKNOWN | LINEAGE_KEPT)
ObjectPurgeResult: deleted_object_count
SweepResult:       swept_count          # keys with no metadata row, deleted
RowPurgeResult:    metadata_rows_deleted, lineage_edges_deleted
RunAssetPurgeVerification: complete, remaining_row_count, unexpected_object_count
ReviewReport:      retained: tuple[RetainedAsset, ...] (primary reasons first),
                   unclean_keys: tuple[str, ...]   # keys under the prefix that have a metadata row
                                                   # but are not candidates (PREFIX_NOT_CLEAN cause)
                   listed_candidate_keys: tuple[str, ...]  # candidate keys still listed under the prefix
                                                   # (a stuck delete after purge_objects)
```

- `LINEAGE_KEPT` means "retained only because another candidate of the same group is retained"
  (§6.1 item 4); a report lists the true causes first and the siblings after them.
- **Empty plan** = `candidates` empty: no removable and no retained asset. A plan with a non-empty
  `retained` list is never empty, although its `removable_key_count` is 0 and its digest is that of
  `[]`; the coordinator branches on `retained` first (DTR §6.2 step 3, T3), and a count of 0 is
  never a test for "nothing to do".
- `purge_objects` and `delete_rows` raise `PLAN_RETAINED` when `plan.retained` is non-empty,
  before any delete.
- `sweep_run_prefix(scope, run_ref)` lists `parent/{run_ref}/`, deletes every listed key that
  has no `core_asset_metadata` row in any scope, then lists again; a second listing that is not
  empty raises `PREFIX_NOT_CLEAN`. It deletes no key that has a row, depends on no plan and no
  entry, and may be repeated safely. **Precondition:** call it only for a run in `DELETE_PENDING` or
  `DELETED`; the port cannot check Story state, and before the fence a sweep between the artwork
  route's `put_object` calls and `attach_artwork` (`parent_ai.py:281-310`) would delete live
  objects that have no row yet. DTR steps 3, 5 and 6 satisfy it.
- Results carry counts and digests only; no key appears in any error, response or log line (SRS
  line 2145). `review_report` returns keys and reason codes only to the operator-side owner-review
  command (an in-process caller that is never an HTTP handler), never to logs or a client.

### 5.2 Story: `RunAssetReferencePort`

`assets_referenced_by_other_runs(scope, run_ref, asset_refs) -> frozenset[str]` — the subset of
`asset_refs` that any **other** run's `story.runs` or `story.run_inputs` row references. The
coordinator passes **all** candidate refs.

### 5.3 Storage: `ObjectStoragePort.list_keys(prefix) -> tuple[str, ...]`

S3 `ListObjectsV2` over the prefix, all pages. Only a successful listing returns; `NoSuchBucket`,
403, 5xx, timeouts and any other error raise `ObjectStorageFailure`. Every fake adds it (C9).

## 6. Rules

### 6.1 Plan (each attempt)

1. `closure_candidates`: seed rows are those in the run's scope whose `source_refs` contains
   `run_ref`; the closure then follows `derived_from_ref` and lineage edges in both directions
   **across any scope** (so a foreign-scope neighbour is found and becomes `SCOPE_MISMATCH`).
2. The coordinator asks Story with all candidate refs → `referenced_elsewhere` (every attempt).
3. `plan_run_purge`: an asset is removable only when it has the run's scope (`SCOPE_MISMATCH`), a
   `parent/{run_ref}/` key (`KEY_UNKNOWN`), every `source_refs` entry is `run_ref` or another
   candidate ref (`SHARED_REFERENCE`), and it is not in `referenced_elsewhere`
   (`SHARED_REFERENCE`). Classification is by `asset_ref` (version 1 only in V1).
4. **All or nothing (owner simplification):** if any candidate is retained, the plan's
   `removable` list is empty and every other candidate is `LINEAGE_KEPT`. `plan_sha256` covers the
   sorted candidates, their classification and `referenced_elsewhere`.
5. `plan_run_purge` also computes `removable_key_count` and `removable_digest`, so the lifecycle
   coordinator can write its receipt entry **before** any object or row is touched (DTR §5.1 T3).

### 6.2 Retained plan → `exception`

When `retained` is non-empty: no asset object and no row is deleted; `purge_objects` and
`delete_rows` raise `PLAN_RETAINED`; the coordinator calls no sweep, writes no asset entry and
records the `exception` (DTR §6.2); orphans without a row wait for the re-open. The owner review
reads the keys through `review_report`; resolving them is a manual data fix outside FR-C-08.
**Acceptance condition of the fix:** the owner-review command re-opens the request (DTR §6.6)
only when the next plan has an empty `retained` list, which means either the group is detached
from every other reference (its foreign `source_refs` entries, `derived_from_ref` and lineage
edges toward foreign assets are cut) or the run's rows and objects were removed by hand so the
plan is empty; clearing the run reference from a shared asset's `source_refs` alone does not do
it, because the asset stays a closure neighbour with a foreign entry. V1 has no sharing (SRS line
1952), so this path is an anomaly path. A Story-side `SHARED_REFERENCE` (a ref in `referenced_elsewhere`)
is cleared in Story data, not in Core; cutting Core links alone does not change Story's answer. After
an exception that was not a retention (for example `PREFIX_NOT_CLEAN` from a stuck delete), the
empty-`retained` condition holds trivially and a re-open is a plain retry.

### 6.3 Removable or empty plan, every attempt

The coordinator calls, in this order (DTR §6.2 step 3):

1. the entry is written by the coordinator from the plan facts (not a port call);
2. **Pre-check** inside `purge_objects(plan)` (short read transaction): re-derive the candidates
   and classification with `plan.referenced_elsewhere`; raise `PLAN_CHANGED` on a hash difference.
   Nothing is deleted before this. Then `delete_object` for each removable key. Skipped when
   `removable` is empty.
3. `sweep_run_prefix(scope, run_ref)`, **on every attempt of step 3 that is not skipped as verified, including an empty plan** (DTR
   steps 5 and 6 sweep again when not complete). Its
   post-condition is that the listing after the sweep is empty; any other result is
   `PREFIX_NOT_CLEAN` (a removable key that is still listed means its delete had no effect).
4. the coordinator re-asks Story immediately before `delete_rows` (round-3 P3-1);
5. `delete_rows(plan, referenced_elsewhere_now)`: one transaction, `SELECT … FOR UPDATE` on the
   candidate rows, re-derive with `referenced_elsewhere_now`; raise `PLAN_CHANGED` if the
   classification differs from the plan; delete the lineage edges touching any removable key,
   then the removable rows. Skipped when `removable` is empty.
6. `verify_run_purged`, then the coordinator flips its entry (DTR §5.1 T4).

The empty-plan skip applies to `purge_objects` and `delete_rows` only; the sweep and the
verification never depend on the plan being non-empty.

### 6.4 Plan facts for the DTR entry (round-4 P2-1)

The DTR asset entry uses `n = removable_key_count`, `h16` = the first 16 hex characters of
`removable_digest`, `p8` = the first 8 hex characters of `plan_sha256` (all lower-case). The
entry is written before the act and flipped to verified keeping those values (DTR T3, T4). On a
retry after the rows are gone the plan is empty (count 0, digest of `[]`, a different
`plan_sha256`); under DTR T3 an empty plan **never overwrites** an existing entry, and with no
entry (a run that never had artwork) it writes `p:0:…`. The final receipt hash is computed by
the DTR from the persisted entries, so nothing outside the receipt is needed after a crash. The
count of orphans swept is the DTR's informational `orph` (DTR T6) and is returned only as
`SweepResult.swept_count`.

### 6.5 `verify_run_purged`

`complete` is true only when no row in the scope has `run_ref` in `source_refs` and
`list_keys('parent/' + run_ref + '/')` is empty. A retained plan is never complete. Errors raise
and are never read as absence. Lineage needs no clause: the `RESTRICT` FKs (C3) forbid an edge to
a deleted row. The DTR coordinator runs it in step 3, before step 5's `finalize_deleted`, and in
step 6; when it is not `complete` there it calls `sweep_run_prefix` and verifies again.

## 7. Residual windows (stated; each row names its guard)

| Window | Guard or why accepted for V1 |
|---|---|
| A Story reference to an asset of this run added by another run between the first Story answer (§6.1 item 2) and `purge_objects` (object deleted, Core pre-check cannot see Story state) | V1 has no feature that adds an existing asset to another run (SRS line 1952); the effect would be a lost artwork of the other run |
| A Story reference added after the re-ask before `delete_rows` | same |
| Objects deleted, then a crash, then a re-plan whose Story answer now retains an asset | same; the object is already gone and the plan goes to `exception` for review |
| `put_object` by the artwork route after the last verification (a late-write race, not a sharing case) | after the route change of §11 the route re-checks the state immediately before `put_object` and `attach_artwork` refuses under lock; its best-effort cleanup (C6) is the only further guard; an object written after the receipt is `completed` stays until a later manual sweep |
| Core trusts the coordinator's `referenced_elsewhere` | a deployment assumption for the implementation task to confirm: the lifecycle consumer calls both ports in one process (the existing BE1 worker is a separate CLI, C9); an empty answer from a fault would delete only run-owned `parent/{run_ref}/` objects |

## 8. Failure and retry

| Case | Result | Receipt (DTR) |
|---|---|---|
| Storage error | raises; rows untouched | retry (outbox `defer`) |
| `PLAN_CHANGED` / `PREFIX_NOT_CLEAN` | raises | retry; next attempt re-plans |
| `RUN_REF_INVALID` | raises before any read | retry bound ends in `exception` |
| Retained plan | nothing deleted; `PLAN_RETAINED` on any delete call | `exception` |
| Rerun after success | empty plan; entry kept; sweep finds nothing | unchanged |

**Logging rule:** log only the typed error code; never an exception's `__cause__` or a traceback.

## 9. Deletion state per object (SRS line 1949) — owner decision A-5

Rows are hard-deleted and the deletion state lives on the lifecycle receipt; no per-row column.
Deviation from SRS line 1949, for the owner at DTR approval (DTR Draft 6 A-5). Recommendation:
accept for V1.

## 10. What the DTR took from this document (done in DTR Draft 6)

- the release path and `lifecycle.reference_released` are removed from DTR §6.6 and §8;
- DTR §6.2 "when step 3 ends in `exception`": no asset is deleted (all or nothing);
- DTR §6.2 step 3 "verified when" is the §6.5 `complete` rule;
- DTR §6.2 steps 5 and 6 run `sweep_run_prefix` when not complete, then verify again;
- the token (entry format, timing, write-once, empty-plan rule, final string, `orph`) is owned by
  DTR §5.1.

## 11. Candidate implementation paths (not approved)

`application/ports/core_foundation.py` (Core port and types); a Story port module for §5.2;
`application/ports/object_storage.py`, `infrastructure/storage/s3_compatible.py` and every port
fake (`list_keys`); a Core SQL adapter under `infrastructure/persistence/`;
`interfaces/http/routers/parent_ai.py` (state re-check before `put_object`); unit tests; adapter
error-mapping tests; an owner-run PostgreSQL plus MinIO test on a disposable target.

## 12. Verification required from the implementation task

- the two artwork assets of a run are removable; a run with any retained asset deletes nothing and
  ends in `exception`, and `review_report` lists it (Story-side reasons included, primary reasons
  first);
- a retained plan with an orphan under the prefix: nothing is deleted, the orphan survives, and
  `purge_objects`, `delete_rows` raise `PLAN_RETAINED`;
- a `PREFIX_NOT_CLEAN` case (a row-bearing key under the prefix that is not a candidate) is shown
  by `review_report.unclean_keys`;
- after a manual fix that detaches the group (and, separately, after the rows and objects are
  removed by hand), the next plan has an empty `retained` list and the request can be re-opened;
  clearing `source_refs` alone leaves it retained;
- a retained plan writes no entry and runs no sweep (a plan with a non-empty `retained` list is
  never read as empty); a stuck delete of a removable key is shown by
  `review_report.listed_candidate_keys`;
- a malformed `run_ref` (`story_run:…`, upper-case, empty, with `/`, a 36-character string with
  misplaced hyphens) raises `RUN_REF_INVALID` at
  every entry and never reports `complete`;
- `PLAN_CHANGED` before any delete when a Core-side reference is added after planning; and before
  row deletion when Story's re-ask differs;
- an orphan written after the rows are gone is removed by the next sweep and `complete` becomes
  true; a removable key whose delete had no effect makes the sweep raise `PREFIX_NOT_CLEAN`;
- a crash after objects, after the sweep and after rows re-runs to the same entry values and the
  same final token (compared with a crash-free run); an empty plan with an existing entry keeps
  it; a run with no artwork ends with `asset=v:0:…` (DTR §10);
- `list_keys` raises on 403, `NoSuchBucket` and 5xx; no key in any error body or captured log.

## 13. Not verified

- Real S3/MinIO behaviour (paging, delete on a missing key, versioning and delete markers,
  retention, replication, backups).
- Database behaviour (JSONB containment cost, `FOR UPDATE` over the candidate set).
- Whether another branch adds writers of Parent `source_refs`.
- The lifecycle consumer's process model (C9).
