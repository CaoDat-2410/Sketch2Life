# FR-C-08 Core reference-closure and storage-ownership port — design, Draft 4

**Status: DRAFT / NOT APPROVED.** Round-4 candidate. The owner allowed round 4 after the D-171
stop of round 3 and chose to **simplify V1**: any retained asset sends the request to
`exception` with no asset deleted, and there is no release path.
**Date:** 2026-11-19.
**Purpose:** the Core Asset contract that D-214 item 7 and D-215 item 3 require before FR-C-08
can be implemented. This document approves nothing and grants no implementation, command,
database, storage or test authority.

**Change from Draft 3:** fixes the round-3 cold review
(`tmp/frc08-port/review-r3/FR_C08_CORE_PORT_DESIGN_COLD_REVIEW_R3_20261119.md`, NEEDS REVISION,
0 P1 / 3 P2 / 6 P3):
- **N2 (retained/released exit) removed by the owner's simplification:** no
  `release_run_reference`, no partial purge by group; a retained asset anywhere in the plan means
  no asset deletion at all and `exception` for a manual data fix outside FR-C-08 (§6.5).
- **N1 (sweep starvation):** the orphan sweep and its post-condition run on every attempt; only
  the entry write and row deletion are skipped for an empty plan (§6.3).
- **N3 (token):** the port returns the step values; the receipt entry and the final hash follow
  DTR Draft 4 §5.1 (pending/verified, write-once, final hash over the persisted entries) (§6.4).
- P3-1 to P3-6: residual windows stated with V1 no-sharing as their guard; the Story answer is
  re-asked before row deletion; the worker key is named as a deployment follow-up; the owner
  learns the retained keys through a guarded Core read; drafting points.

## 1. Pins

| Input | Pin |
|---|---|
| Canonical SRS (D-209) | 701,157 bytes, SHA-256 `B9B1F42D0BB118C19C81607D3913B7E4F1D8B6F673F0C3FBB6402888FEB675F5` |
| Decisions | FEAT-063 D-214 items 6-7, D-215 item 3, D-216, D-217 (working tree) |
| Companion | `plan/FR_C08_LIFECYCLE_DTR_DRAFT4_20261119.md` (under round-3 review); §10 lists what its next draft takes from here |
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
| C9 | The combined-profile S3 adapter uses `storage_example_settings` (`s3_bucket`, `s3_endpoint`, `s3_region`, `s3_access_key`, `s3_secret_key`); a test fake of the port exists. | `app.py:1084-1093`; `tests/integration/lesson_library/test_lesson_library_api.py:68` |

## 4. Ownership

1. Core Asset alone deletes `core_asset_metadata`, `core_asset_lineage` and the objects they name.
2. Story owns run-to-asset references and answers through a Story port (§5.2); Core never reads
   `story.*` (SRS line 805).
3. **Bucket (P-1, V1):** Parent objects stay in the bucket of the C9 settings. **The V1 worker
   uses the application's key pair from those settings**; a separate least-privilege principal
   (list on `parent/`, delete on `parent/*`) is a deployment follow-up before real data, not part
   of FR-C-08 (round-3 P3-3).
4. Only `parent/{run_ref}/` keys are ever deleted; lesson sources are unreachable.
5. Upload records and `QuarantineStore` files of the StoryRun-lite demo path are out of scope;
   the DTR's upload step closes any upload record that names the run.

## 5. Ports

### 5.1 Core: `RunAssetPurgePort`

```text
closure_candidates(scope, run_ref) -> CandidateSet                        # read-only
plan_run_purge(candidates, referenced_elsewhere: frozenset[str]) -> RunAssetPurgePlan
purge_objects(plan) -> ObjectPurgeResult       # pre-check, delete removable objects, sweep orphans
delete_rows(plan, referenced_elsewhere_now: frozenset[str]) -> RowPurgeResult
verify_run_purged(scope, run_ref) -> RunAssetPurgeVerification
retained_assets_for_review(scope, run_ref) -> tuple[RetainedAsset, ...]   # owner-review caller only

CandidateSet:      scope, run_ref, assets: tuple[AssetKey, ...], edges
RunAssetPurgePlan: scope, run_ref, referenced_elsewhere (sorted), removable: tuple[AssetKey, ...],
                   retained: tuple[RetainedAsset, ...], plan_sha256
AssetKey:          asset_ref, asset_version (always 1 in V1, C2)
RetainedAsset:     key, reason_code  (SHARED_REFERENCE | SCOPE_MISMATCH | KEY_UNKNOWN | LINEAGE_KEPT)
ObjectPurgeResult: removable_key_count, removable_digest (64 hex), orphan_swept_count
RowPurgeResult:    metadata_rows_deleted, lineage_edges_deleted
RunAssetPurgeVerification: complete, remaining_row_count, unexpected_object_count
```

Results carry counts and digests only; no key appears in any error, response or log line (SRS
line 2145). `retained_assets_for_review` returns keys and reason codes only to the owner-review
command (an authorized caller), never to logs or a client (round-3 P3-5).

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

### 6.2 Retained plan → `exception`

When `retained` is non-empty: no object and no row is deleted; the coordinator records the
`exception` (DTR) and stops the asset step. The owner review reads the keys through
`retained_assets_for_review`; resolving them is a manual data fix outside FR-C-08. After that fix,
the owner-review command re-opens the request (DTR re-open) and the next attempt plans again. V1
has no sharing (SRS line 1952), so this path is an anomaly path.

### 6.3 Removable plan, every attempt

1. **Pre-check** (short read transaction): re-derive the candidates and classification with
   `plan.referenced_elsewhere`; raise `PLAN_CHANGED` on a hash difference. Nothing is deleted
   before this.
2. `delete_object` for each removable key (skipped when `removable` is empty).
3. **Sweep, on every attempt including an empty plan:** `list_keys('parent/' + run_ref + '/')`;
   delete every listed key that has no `core_asset_metadata` row in any scope; list again.
   Post-condition: the listing is empty, or every remaining key is a removable key of the current
   plan whose row has not yet been deleted. Otherwise `PREFIX_NOT_CLEAN` (round-3 N1).
4. The coordinator writes the asset step entry (DTR §5.1 pending/verified rule) — skipped when an
   entry for this step is already verified.
5. `delete_rows(plan, referenced_elsewhere_now)`: the coordinator re-asks Story immediately
   before this call (round-3 P3-1); one transaction, `SELECT … FOR UPDATE` on the candidate rows,
   re-derive with `referenced_elsewhere_now`; raise `PLAN_CHANGED` if the classification differs
   from the plan; delete the lineage edges touching any removable key, then the removable rows.
   Skipped when `removable` is empty.

### 6.4 Token values (round-3 N3)

`purge_objects` returns `removable_key_count`, the full 64-hex `removable_digest` (SHA-256 of the
canonical JSON of the sorted removable keys) and `orphan_swept_count`. The DTR asset entry uses
`n = removable_key_count`, `h16` = the first 16 hex characters of `removable_digest`, `p8` = the
first 8 hex characters of `plan_sha256`; the final receipt hash is computed over the persisted
entries (DTR Draft 4 §5.1), so nothing outside the receipt is needed after a crash. An orphan swept
after the entry is verified is not added to it.

### 6.5 `verify_run_purged`

`complete` is true only when no row in the scope has `run_ref` in `source_refs` and
`list_keys('parent/' + run_ref + '/')` is empty. A retained plan is never complete. Errors raise
and are never read as absence. Lineage needs no clause: the `RESTRICT` FKs (C3) forbid an edge to
a deleted row.

## 7. Residual windows (stated; V1 no-sharing is their guard)

| Window | Why it is accepted for V1 |
|---|---|
| A Story reference from another run added after `delete_rows`'s re-ask | V1 has no feature that adds an existing asset to another run (SRS line 1952) |
| Objects deleted, then a crash, then a re-plan whose Story answer now retains an asset | same; the asset's object would already be gone, and the plan goes to `exception` for review |
| `put_object` by the artwork route after the last verification | the route re-checks the state immediately before `put_object` and `attach_artwork` refuses under lock; its best-effort cleanup is the only further guard (round-3 P3-2) |
| Core trusts the coordinator's `referenced_elsewhere` | the coordinator and both ports run in the same backend process; an empty answer from a fault would delete only run-owned `parent/{run_ref}/` objects |

## 8. Failure and retry

| Case | Result | Receipt (DTR) |
|---|---|---|
| Storage error | raises; rows untouched | retry (outbox `defer`) |
| `PLAN_CHANGED` / `PREFIX_NOT_CLEAN` | raises | retry; next attempt re-plans |
| Retained plan | nothing deleted | `exception` |
| Rerun after success | empty plan; sweep finds nothing; entry kept | unchanged |

**Logging rule:** log only the typed error code; never an exception's `__cause__` or a traceback.

## 9. Deletion state per object (SRS line 1949) — owner decision A-5

Rows are hard-deleted and the deletion state lives on the lifecycle receipt; no per-row column.
Deviation from SRS line 1949, for the owner at DTR approval (DTR Draft 4 A-5). Recommendation:
accept for V1.

## 10. Items for DTR Draft 5

- Remove the release path from DTR §6.6 and §8 (`lifecycle.reference_released`); the re-open
  follows a manual data fix.
- DTR §6.2 "when step 3 ends in `exception`": no asset is deleted (all or nothing).
- DTR §6.2 step 3 "verified when": the §6.5 `complete` rule.
- DTR §6.2 steps 5 and 6: the second and third verifications run the sweep (§6.3 step 3) when not
  complete, then verify again.

## 11. Candidate implementation paths (not approved)

`application/ports/core_foundation.py` (Core port and types); a Story port module for §5.2;
`application/ports/object_storage.py`, `infrastructure/storage/s3_compatible.py` and every port
fake (`list_keys`); a Core SQL adapter under `infrastructure/persistence/`;
`interfaces/http/routers/parent_ai.py` (state re-check before `put_object`); unit tests; adapter
error-mapping tests; an owner-run PostgreSQL plus MinIO test on a disposable target.

## 12. Verification required from the implementation task

- the two artwork assets of a run are removable; a run with any retained asset deletes nothing and
  ends in `exception`, and `retained_assets_for_review` lists it;
- `PLAN_CHANGED` before any delete when a Core-side reference is added after planning; and before
  row deletion when Story's re-ask differs;
- an orphan written after the rows are gone is removed by the next attempt and `complete` becomes
  true (round-3 N1);
- a crash after objects, after the entry write and after rows re-runs to the same entry values;
- `list_keys` raises on 403, `NoSuchBucket` and 5xx; no key in any error body or captured log.

## 13. Not verified

- Real S3/MinIO behaviour (paging, delete on a missing key, versioning and delete markers,
  retention, replication, backups).
- Database behaviour (JSONB containment cost, `FOR UPDATE` over the candidate set).
- Whether another branch adds writers of Parent `source_refs`.
