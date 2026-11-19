# FR-C-08 Core reference-closure and storage-ownership port — design, Draft 2

**Status: DRAFT / NOT APPROVED.** Round-2 candidate.
**Date:** 2026-11-19.
**Purpose:** the Core Asset contract that D-214 item 7 and D-215 item 3 require before FR-C-08
can be implemented. This document approves nothing and grants no implementation, command,
database, storage or test authority.

**Change from Draft 1:** fixes the round-1 cold review
(`tmp/frc08-port/review-r1/FR_C08_CORE_PORT_DESIGN_COLD_REVIEW_R1_20261119.md`, NEEDS REVISION,
0 P1 / 7 P2 / 7 P3): purge proves absence before the rows go, so the rows are the retry manifest
(P2-1); a strict `list_keys(prefix)` replaces `object_exists` (P2-2) and also sweeps orphans
(P2-3); the plan is re-derived and hash-checked inside `delete_rows`, and the step digest is
handed back before rows go (P2-4); a Story-supplied other-run reference set plus the key-shape
rule replace the claimed equivalence (P2-5); only `parent/{run_ref}/` keys are ever deleted
(P2-6); an owner-review release path lets a retained asset close (P2-7); and all P3 notes.

## 1. Pins

| Input | Pin |
|---|---|
| Canonical SRS (D-209) | 701,157 bytes, SHA-256 `B9B1F42D0BB118C19C81607D3913B7E4F1D8B6F673F0C3FBB6402888FEB675F5` |
| Decisions | FEAT-063 D-214 items 6-7, D-215 item 3, D-216, D-217 (working tree) |
| Companion | `plan/FR_C08_LIFECYCLE_DTR_DRAFT3_20261119.md` §6.2 step 3 |
| Code base | `feature/feat066-conv1` at `03342207`, read in `.worktrees/conv1` |

## 2. SRS requirements

SRS lines 805 (no cross-schema SQL), 1004 (Core owns asset metadata/lineage and upload
records), 1052-1054 (asset identity; cancel and delete purge every eligible object and metadata;
a still-referenced asset is deleted only when no valid reference remains), 1473 (retry
idempotently, keep shared assets until other references are reconciled), 1949-1952 (owner scope
and deletion state per object; idempotent batches; not complete until all objects are
reconciled; no sharing between runs in V1), 2144-2146 (keep pending until refs reconciled; no
object key in client errors; unclear shared references go to owner review); register lines 78
and 547.

## 3. Source facts at the base

| # | Fact | Evidence |
|---|---|---|
| C1 | The Parent artwork route writes two objects through `app.state.lesson_library_storage` (S3-compatible). Key = asset ref: `parent/{run_id}/{hex}/original` and `parent/{run_id}/{hex}/normalized.png`. The original's object metadata carries `sha256` and `run-ref`; the normalized object's carries `sha256` and `source-ref` (the original's key). | `interfaces/http/routers/parent_ai.py:281-297`; `interfaces/http/app.py:1084-1093` |
| C2 | Then it writes two `core_asset_metadata` rows (`PARENT_ACCOUNT`, organization NULL, scope ref = Parent principal scope ref, `source_refs = [run_id]`; the normalized row has `derived_from_ref` = original) and one `core_asset_lineage` edge. Objects are written before rows. | `infrastructure/persistence/parent_story_repository.py:539-660` |
| C3 | `core_asset_lineage` has `RESTRICT` foreign keys from both source and derived refs to `core_asset_metadata`; edges must go before rows. | `alembic/versions/20261102_story_run_lite.py:295-304`; `parent_story_repository.py:593-594` |
| C4 | `CoreAssetMetadataPort` has no Parent read, reference query or deletion. | `application/ports/core_foundation.py:181-186` |
| C5 | `ObjectStoragePort` has `put_object`, `get_object` (`None` on `NoSuchKey` **and** `NoSuchBucket`), `delete_object`. | `application/ports/object_storage.py:27-40`; `infrastructure/storage/s3_compatible.py:81-105` |
| C6 | On a failed attach the route deletes both keys best-effort and swallows `ObjectStorageFailure`, so an orphan object with no row can remain. | `parent_ai.py:311-325` |
| C7 | No Parent product run stores scene, video or audio objects at the base. | `infrastructure/story_run_lite/tables.py:498-606` |
| C8 | Lesson Library keys differ from asset refs (`lesson-source:{id}` maps to a derived key); bucket prefixes are disjoint (`lesson-library/…`, `parent/…`). The StoryRun-lite demo path uses a local `QuarantineStore` with `source_refs = []`. | `infrastructure/lesson_library/service.py:850-851`; `infrastructure/story_run_lite/quarantine.py:20-145` |

## 4. Ownership

1. Core Asset alone deletes `core_asset_metadata`, `core_asset_lineage` and the objects they name
   (SRS line 1004; register line 78).
2. Story owns run-to-asset references in `story.*` and answers questions about them only through
   a Story port (§5.2). Core never reads `story.*` (SRS line 805).
3. **Bucket (P-1, accepted for V1):** Parent objects stay in the bucket configured for
   `lesson_library_storage`. The lifecycle worker builds its own adapter from the same bucket
   settings, with credentials limited to list, head and delete on the `parent/` prefix. Moving
   Parent objects to a separate bucket is out of scope.
4. Lesson sources are never reachable: only `parent/{run_ref}/` keys can be deleted (§6.1).
5. **Out of scope, stated:** `storyrun_upload_*` rows and `QuarantineStore` files belong to the
   StoryRun-lite demo path; DTR Draft 3 step 1 closes any upload record that names the run, and
   deleting quarantine files is a separate demo-path task if a database ever holds both.

## 5. Ports

### 5.1 Core: `RunAssetPurgePort`

```text
plan_run_purge(scope, run_ref, other_run_refs: frozenset[str]) -> RunAssetPurgePlan
purge_objects(plan) -> ObjectPurgeResult                # deletes objects, proves prefix empty
delete_rows(plan) -> RowPurgeResult                     # re-derives plan FOR UPDATE, checks plan_sha256
verify_run_purged(scope, run_ref) -> RunAssetPurgeVerification
release_run_reference(scope, run_ref, asset: AssetKey, reconciliation_ref: str) -> None   # owner review only

RunAssetPurgePlan:   scope, run_ref, groups: tuple[AssetGroup, ...], plan_sha256
AssetGroup:          group_id, removable: tuple[AssetKey, ...], retained: tuple[RetainedAsset, ...]
AssetKey:            asset_ref, asset_version
RetainedAsset:       key, reason_code  (SHARED_REFERENCE | SCOPE_MISMATCH | KEY_UNKNOWN | LINEAGE_KEPT)
ObjectPurgeResult:   deleted_keys_count, swept_orphan_count, step_digest   (SHA-256, canonical JSON of sorted keys)
RowPurgeResult:      metadata_rows_deleted, lineage_edges_deleted
RunAssetPurgeVerification: complete, remaining_row_count, remaining_object_count, unreconciled_retained_count
```

Results carry counts and digests only. No key appears in any error, response or log line
(SRS line 2145).

### 5.2 Story: `RunAssetReferencePort`

`assets_referenced_by_other_runs(scope, run_ref, asset_refs) -> frozenset[str]`: Story checks
`story.runs` and `story.run_inputs` of every **other** run for the given refs. The coordinator
passes the answer to `plan_run_purge` as `other_run_refs` (port review P2-5). This keeps the SRS
"positively reconciled" check (line 1473; D-214 item 7) without cross-schema SQL.

### 5.3 Storage: `ObjectStoragePort.list_keys(prefix) -> tuple[str, ...]`

S3 `ListObjectsV2` over the prefix, all pages. Only a successful listing returns; `NoSuchBucket`,
403, 5xx, timeouts and every other error raise `ObjectStorageFailure` (fail closed, port review
P2-2). `object_exists` from Draft 1 is dropped. Adapter tests cover 403, `NoSuchBucket` and 5xx.

## 6. Rules

### 6.1 Plan

1. **Candidates:** rows in the run's scope whose `source_refs` contains `run_ref`, closed
   transitively (fixed point) over `derived_from_ref` and lineage edges in both directions.
2. **Groups:** connected components of the candidate graph.
3. **Removable** asset — all must hold, else the reason code:
   - same owner scope as the run (`SCOPE_MISMATCH`);
   - key of the form `parent/{run_ref}/…` (`KEY_UNKNOWN`; never passed to `delete_object`);
   - every `source_refs` entry is `run_ref` or the ref of an asset in the same group
     (`SHARED_REFERENCE`); this is the V1 invariant, fail-closed;
   - not in `other_run_refs` (`SHARED_REFERENCE`).
4. A group with any retained asset is retained whole (`LINEAGE_KEPT` for its other members).
   Other groups of the run proceed; the request ends in `exception` (SRS line 2146).
5. `plan_sha256` = SHA-256 of the canonical JSON of the sorted groups.

### 6.2 Purge, in this order

1. `purge_objects(plan)`: `delete_object` for every removable key of every removable group, then
   `list_keys('parent/' + run_ref + '/')`, delete every listed key (orphans, C6), and list again;
   the step succeeds only when the final listing is empty. `step_digest` covers the removable
   keys plus the swept keys.
2. The coordinator writes the step entry (count and digest) to the receipt (DTR Draft 3 §5.1).
3. `delete_rows(plan)`: one transaction; re-derive the plan with `SELECT … FOR UPDATE` on the
   candidate rows; abort with a typed `PLAN_CHANGED` error if `plan_sha256` differs; delete
   lineage edges touching any removable key (source and derived), then the metadata rows.

The rows remain until objects are proven gone, so every retry recomputes the same plan from them
(port review P2-1). A retry after step 3 finds no rows and an empty prefix, and the receipt
already holds the step entry from step 2.

### 6.3 Verify

`complete` is true only when no row in the scope names `run_ref` in `source_refs`, no edge
touches a removed key, `list_keys('parent/' + run_ref + '/')` returns empty, and every retained
asset has been released by `release_run_reference`. A storage or database error raises; it is
never read as absence (Contract Draft 8 §3.3).

### 6.4 Release after owner review (port review P2-7)

`release_run_reference` removes `run_ref` from one retained asset's `source_refs`, records the
`reconciliation_ref` in the Core audit, and is called only by the owner-review command of DTR
Draft 3 §6.5. V1 has no sharing, so this is an anomaly path.

## 7. Failure and retry

| Case | Result | Receipt (DTR Draft 3) |
|---|---|---|
| Storage error in `purge_objects` | raises; no row touched | `awaiting_external_purge`; outbox `defer` |
| Prefix not empty after sweep | typed error | same |
| `PLAN_CHANGED` in `delete_rows` | raises; nothing deleted | same; next attempt re-plans |
| Retained group | other groups purged; this group untouched | `exception`; owner review |
| Rerun after success | no rows, empty prefix, counts 0 | step already recorded; verification `complete` |

**Logging rule:** the port and the lifecycle consumer log only the typed error code; they never
log an exception's `__cause__` or a traceback, because botocore errors can embed the endpoint and
key (port review P3-5).

## 8. Deletion state per object (SRS line 1949) — owner decision P-3

The design hard-deletes the rows and keeps the deletion state on the lifecycle receipt for the
run; no per-row deletion-state column is added. SRS line 1949 lists "deletion state" per object,
and register line 204 names a deletion-state field as a possible cross-module field, so this is
an explicit deviation for the owner to accept at DTR approval (port review P3-7).
**Recommendation:** accept for V1; Parent rows are unreachable through the organization-scoped
Core port and the run fence blocks reads while the purge runs.

## 9. Candidate implementation paths (not approved)

`application/ports/core_foundation.py` (Core port and types), a Story port module for §5.2,
`application/ports/object_storage.py` and `infrastructure/storage/s3_compatible.py`
(`list_keys`), a Core SQL adapter under `infrastructure/persistence/`, unit tests for the plan
rules and order, adapter error-mapping tests, and an owner-run PostgreSQL plus MinIO test on a
disposable target.

## 10. Verification required from the implementation task

- plan: the two artwork assets of a run form one removable group; an asset with another run in
  `source_refs`, in `other_run_refs`, of another scope, or with a non-`parent/{run_ref}/` key is
  retained with the right code and its group kept; other groups still proceed;
- purge: objects first; an orphan under the prefix is swept; a forced storage error leaves every
  row; `PLAN_CHANGED` aborts; a crash after rows go re-runs as a no-op with the receipt entry
  intact;
- verify: false while any object, row or unreleased retained asset remains; storage errors raise;
- `list_keys` raises on 403, `NoSuchBucket` and 5xx;
- no key in any error body or captured log line for a forced failure.

## 11. Open items

| ID | Item | Handling |
|---|---|---|
| P-1 | Shared bucket | accepted for V1 with the §4 item 3 least-privilege note |
| P-2 | Storage port addition | `list_keys(prefix)`, fail closed |
| P-3 | Per-object deletion state | owner decision at DTR approval (§8) |

## 12. Not verified

- Bucket versioning or retention settings (a versioned bucket keeps deleted versions); backups.
- Whether any writer other than C2 puts a Parent run id in `source_refs`.
