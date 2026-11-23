# FR-C-08 Core reference-closure and storage-ownership port — design, Draft 3

**Status: DRAFT / NOT APPROVED.** Round-3 candidate (owner allowed the round after the D-171
stop of round 2).
**Date:** 2026-11-19.
**Purpose:** the Core Asset contract that D-214 item 7 and D-215 item 3 require before FR-C-08
can be implemented. This document approves nothing and grants no implementation, command,
database, storage or test authority.

**Change from Draft 2:** fixes the round-2 cold review
(`tmp/frc08-port/review-r2/FR_C08_CORE_PORT_DESIGN_COLD_REVIEW_R2_20261119.md`, NEEDS REVISION,
0 P1 / 3 P2 / 6 P3; three P2 repeat round-1 classes):
- **P2-1 (retained assets vs the sweep):** the sweep deletes only keys with no Core row; the
  post-condition and `complete` allow the objects of retained and released assets (§6.2, §6.3).
- **P2-2 (token on retry):** the step entry is computed over the plan's removable keys only and
  is written once per plan hash; orphans are a separate informational count (§6.5).
- **P2-3 (Story input):** a three-call sequence gives Story the full candidate set; the Story
  answer is stored and hashed in the plan, so every re-check uses the plan alone (§5, §6.1).
- P3-1 to P3-6: plan re-check before the first object delete; a second verification right before
  Story writes `DELETED`; storage wording, credentials and test fakes; the `<n>` mapping; items
  for DTR Draft 4; the C8 citation.

## 1. Pins

| Input | Pin |
|---|---|
| Canonical SRS (D-209) | 701,157 bytes, SHA-256 `B9B1F42D0BB118C19C81607D3913B7E4F1D8B6F673F0C3FBB6402888FEB675F5` |
| Decisions | FEAT-063 D-214 items 6-7, D-215 item 3, D-216, D-217 (working tree) |
| Companion | `plan/FR_C08_LIFECYCLE_DTR_DRAFT3_20261119.md` (under round-2 review); §11 lists what its next draft takes from here |
| Code base | `feature/feat066-conv1` at `03342207`, read in `.worktrees/conv1` |

## 2. SRS requirements

SRS lines 805 (no cross-schema SQL), 1004 (Core owns asset metadata/lineage and upload
records), 1052-1054 (asset identity; cancel and delete purge every eligible object and metadata;
a still-referenced asset is deleted only when no valid reference remains), 1473 (retry
idempotently; keep shared assets until other references are reconciled), 1949-1952 (owner scope
and deletion state per object; idempotent batches; not complete until all objects are
reconciled; no sharing between runs in V1), 2144-2146 (pending until refs reconciled; no object
key in client errors; unclear shared references go to owner review); register lines 78 and 547.

## 3. Source facts at the base

| # | Fact | Evidence |
|---|---|---|
| C1 | The Parent artwork route reads the run once, scans and prepares the image, then writes two objects through `app.state.lesson_library_storage` (S3-compatible), then calls `attach_artwork`. Key = asset ref: `parent/{run_id}/{hex}/original`, `parent/{run_id}/{hex}/normalized.png`. The original's object metadata carries `sha256` and `run-ref`; the normalized object's carries `sha256` and `source-ref`. | `interfaces/http/routers/parent_ai.py:236-240, 281-310`; `interfaces/http/app.py:1084-1093` |
| C2 | `attach_artwork` refuses unless the run is `INPUT_PROCESSING`, then writes two `core_asset_metadata` rows (`PARENT_ACCOUNT`, organization NULL, scope ref = Parent principal scope ref, `source_refs = [run_id]`; normalized row `derived_from_ref` = original) and one lineage edge. | `infrastructure/persistence/parent_story_repository.py:539-660, 554-555` |
| C3 | `core_asset_lineage` has `RESTRICT` FKs from source and derived refs to `core_asset_metadata`; edges go before rows. | `alembic/versions/20261102_story_run_lite.py:295-304` |
| C4 | `CoreAssetMetadataPort` has no Parent read, reference query or deletion. | `application/ports/core_foundation.py:181-186` |
| C5 | `ObjectStoragePort`: `put_object`, `get_object` (`None` on `NoSuchKey` and `NoSuchBucket`), `delete_object`; S3 `DeleteObject` does not report whether the key existed. | `application/ports/object_storage.py:27-40`; `infrastructure/storage/s3_compatible.py:81-105` |
| C6 | A failed attach deletes both keys best-effort and swallows `ObjectStorageFailure`; an orphan object with no row can remain. | `parent_ai.py:311-325` |
| C7 | No Parent product run stores scene, video or audio objects at the base. | `infrastructure/story_run_lite/tables.py:498-606` |
| C8 | Lesson Library keys differ from asset refs (`lesson-source:{id}`); prefixes are disjoint (`lesson-library/…`, `parent/…`). The StoryRun-lite demo path writes metadata with `source_refs = []` and keeps files in a local `QuarantineStore`. | `infrastructure/lesson_library/service.py:850-851`; `infrastructure/story_run_lite/repository.py:1077, 1089`; `quarantine.py:20-145` |
| C9 | The S3 adapter in the combined profile is built from `storage_example_settings` (`s3_bucket`, `s3_endpoint`, `s3_region`, `s3_access_key`, `s3_secret_key`). A test fake of `ObjectStoragePort` exists. | `app.py:1084-1093`; `tests/integration/lesson_library/test_lesson_library_api.py:68` |

## 4. Ownership

1. Core Asset alone deletes `core_asset_metadata`, `core_asset_lineage` and the objects they name
   (SRS line 1004; register line 78).
2. Story owns run-to-asset references in `story.*` and answers through a Story port (§5.2). Core
   never reads `story.*` (SRS line 805).
3. **Bucket (P-1, accepted for V1):** Parent objects stay in the bucket configured by the C9
   settings. The lifecycle worker builds its own adapter from those settings, with credentials
   limited to `ListBucket` on the `parent/` prefix and `DeleteObject` on `parent/*`.
4. Only `parent/{run_ref}/` keys can ever be deleted (§6.1); lesson sources are unreachable.
5. **A released asset** (§6.6) stays owned by Core under its Parent scope; it is now referenced
   only by the other run(s) in its `source_refs`, and their lifecycle purges it later.
6. **Out of scope, stated:** `storyrun_upload_*` rows and `QuarantineStore` files of the
   StoryRun-lite demo path (DTR Draft 3 step 1 closes any upload record that names the run).

## 5. Ports

### 5.1 Core: `RunAssetPurgePort`

```text
closure_candidates(scope, run_ref) -> CandidateSet                      # read-only
plan_run_purge(candidates, referenced_elsewhere: frozenset[str]) -> RunAssetPurgePlan
purge_objects(plan) -> ObjectPurgeResult        # re-checks plan, deletes removable objects, sweeps orphans
delete_rows(plan) -> RowPurgeResult             # re-checks plan FOR UPDATE, deletes removable groups' rows
verify_run_purged(scope, run_ref) -> RunAssetPurgeVerification
release_run_reference(scope, run_ref, asset: AssetKey, reconciliation_ref: str) -> None   # owner review only

CandidateSet:      scope, run_ref, assets: tuple[AssetKey, ...], edges, candidate_sha256
RunAssetPurgePlan: scope, run_ref, referenced_elsewhere (stored, sorted), groups: tuple[AssetGroup, ...], plan_sha256
AssetGroup:        group_id, removable: tuple[AssetKey, ...], retained: tuple[RetainedAsset, ...]
AssetKey:          asset_ref, asset_version
RetainedAsset:     key, reason_code  (SHARED_REFERENCE | SCOPE_MISMATCH | KEY_UNKNOWN | LINEAGE_KEPT)
ObjectPurgeResult: removable_key_count, removable_digest, orphan_swept_count
RowPurgeResult:    metadata_rows_deleted, lineage_edges_deleted
RunAssetPurgeVerification: complete, remaining_referencing_rows, unexpected_object_count, unreleased_retained_count
```

Results carry counts and digests only; no key appears in any error, response or log line (SRS
line 2145).

### 5.2 Story: `RunAssetReferencePort`

`assets_referenced_by_other_runs(scope, run_ref, asset_refs) -> frozenset[str]` — the subset of
`asset_refs` that any **other** run's `story.runs` or `story.run_inputs` row references. The
coordinator passes **all** candidate refs from `closure_candidates`, so the check covers the
whole closure (round-2 P2-3).

### 5.3 Storage: `ObjectStoragePort.list_keys(prefix) -> tuple[str, ...]`

S3 `ListObjectsV2` over the prefix, all pages. Only a successful listing returns; `NoSuchBucket`,
403, 5xx, timeouts and any other error raise `ObjectStorageFailure`. Every fake of the port must
add the method (C9).

## 6. Rules

### 6.1 Sequence for one attempt

1. `closure_candidates(scope, run_ref)`: rows in the run's scope whose `source_refs` contains
   `run_ref`, closed transitively over `derived_from_ref` and lineage edges in both directions.
2. Story port with **all** candidate refs → `referenced_elsewhere` (refreshed on every attempt).
3. `plan_run_purge(candidates, referenced_elsewhere)`: groups = connected components; an asset is
   removable only when it has the run's scope (`SCOPE_MISMATCH`), a `parent/{run_ref}/` key
   (`KEY_UNKNOWN`), every `source_refs` entry is `run_ref` or a ref in the same group
   (`SHARED_REFERENCE`), and it is not in `referenced_elsewhere` (`SHARED_REFERENCE`); a group with
   any retained asset is retained whole (`LINEAGE_KEPT`). `plan_sha256` covers the sorted groups
   **and** `referenced_elsewhere`.

### 6.2 `purge_objects(plan)`

1. In a short read transaction, re-derive candidates and classification using
   `plan.referenced_elsewhere`; raise `PLAN_CHANGED` if the hash differs (round-2 P3-1). No
   object is deleted before this check.
2. `delete_object` for every removable key of every removable group.
3. Sweep: `list_keys('parent/' + run_ref + '/')`; delete every listed key that has **no**
   `core_asset_metadata` row in any scope (orphans, C6); list again.
4. Post-condition: every listed key has a Core row, and that row belongs to a retained or
   released asset. Otherwise raise `PREFIX_NOT_CLEAN`.

The objects of retained and released assets are never deleted (round-2 P2-1).

### 6.3 `delete_rows(plan)`

One transaction: re-derive with `SELECT … FOR UPDATE` on the candidate rows, using
`plan.referenced_elsewhere`; raise `PLAN_CHANGED` if the hash differs; delete the lineage edges
touching any removable key (source and derived), then the removable metadata rows. Retained
groups are left untouched in the same transaction, so other groups proceed and the plan does not
loop on `PLAN_CHANGED` (round-2 P2-3).

### 6.4 `verify_run_purged(scope, run_ref)`

`complete` is true only when (a) no row in the scope has `run_ref` in `source_refs`, and (b) every
key under `parent/{run_ref}/` has a Core row whose `source_refs` no longer contains `run_ref`
(a released asset). A retained, unreleased asset fails (a); an orphan fails (b). Errors raise and
are never read as absence. Lineage needs no separate clause: the `RESTRICT` FKs (C3) make an edge
to a deleted row impossible.

### 6.5 Step entry for the lifecycle token (round-2 P2-2, P3-4)

- The coordinator writes the asset entry to the receipt between §6.2 and §6.3:
  `asset=<n>:<h16>@<p8>`, where `<n>` = number of removable keys in the plan (objects),
  `<h16>` = the first 16 hex characters of `removable_digest` (SHA-256 of the canonical JSON of
  the sorted removable keys), and `<p8>` = the first 8 hex characters of `plan_sha256`. Row counts
  are not part of the token.
- **Write once per plan hash:** if the receipt already holds an asset entry with the same `<p8>`,
  the coordinator does not rewrite it; if the plan hash differs, the new entry supersedes it.
  If the plan has no removable key (rows already gone) and an entry exists, the existing entry is
  kept and §6.2-§6.3 are skipped.
- `orphan_swept_count` is informational: it is added as `;orph=<m>` the first time the entry is
  written and is not part of any hash. An orphan swept by an attempt that crashed before the
  entry write is not counted.

### 6.6 Release after owner review (round-1 P2-7)

`release_run_reference` removes `run_ref` from one retained asset's `source_refs` when the
asset's other references are confirmed, and writes a Core audit row
`lifecycle.reference_released` with `decision = 'released:' || reconciliation_ref`. It is called
only by the owner-review command of DTR §6.5. A retained asset with no other reference
(`SCOPE_MISMATCH`, `KEY_UNKNOWN`) cannot be released; the request stays in `exception` until a
separate data fix.

### 6.7 Late artwork write (round-2 P3-2)

The coordinator calls `verify_run_purged` again immediately before DTR step 5 (Story writes
`DELETED`); if it is not complete, the attempt returns to §6.1. The artwork route also re-checks
the run state immediately before its first `put_object` (route change for the allowlist).

## 7. Failure and retry

| Case | Result | Receipt (DTR) |
|---|---|---|
| Storage error | raises; rows untouched | `awaiting_external_purge`; outbox `defer` |
| `PLAN_CHANGED` | raises before any deletion of that kind | same; next attempt re-plans (new Story answer) |
| `PREFIX_NOT_CLEAN` | raises | same |
| Retained group | removable groups purged; retained group untouched | `exception`; owner review |
| Rerun after success | plan empty; entry kept; verify complete | unchanged |

**Logging rule:** log only the typed error code; never an exception's `__cause__` or a
traceback (botocore errors can embed the endpoint and key).

## 8. Deletion state per object (SRS line 1949) — owner decision P-3

Rows are hard-deleted and the deletion state lives on the lifecycle receipt for the run; no
per-row column is added. SRS line 1949 lists a deletion state per object (register line 204 names
it as a possible field), so this is a deviation for the owner to accept at DTR approval.
**Recommendation:** accept for V1; Parent rows are unreachable through the organization-scoped
Core port and the run fence blocks reads during the purge.

## 9. Candidate implementation paths (not approved)

`application/ports/core_foundation.py` (Core port and types); a Story port module for §5.2;
`application/ports/object_storage.py`, `infrastructure/storage/s3_compatible.py` and every port
fake, including `tests/integration/lesson_library/test_lesson_library_api.py` (`list_keys`); a
Core SQL adapter under `infrastructure/persistence/`; `interfaces/http/routers/parent_ai.py`
(state re-check before `put_object`); unit tests; adapter error-mapping tests; an owner-run
PostgreSQL plus MinIO test on a disposable target.

## 10. Verification required from the implementation task

- plan: the two artwork assets form one removable group; assets with another run in
  `source_refs`, in `referenced_elsewhere`, of another scope, or with a non-`parent/{run_ref}/`
  key are retained with the right code and their group kept; a run with one retained and one
  removable group deletes the removable group and does not loop;
- objects: `PLAN_CHANGED` before any delete when a reference is added after planning; an orphan
  is swept; a retained asset with a `parent/{run_ref}/` key keeps its object through purge, retry
  and verify; release then retry deletes nothing and `complete` becomes true;
- token: a crash at each point (after objects, after the entry write, after rows) re-runs to the
  same entry; an empty plan keeps the existing entry;
- late write: an object written after the sweep is caught by the second verification;
- `list_keys` raises on 403, `NoSuchBucket` and 5xx; no key in any error body or captured log.

## 11. Items for DTR Draft 4

- §5.1 token: the asset entry format of §6.5 (`@<p8>`, write-once, `orph`).
- §6.2: steps 1-3 of §6.1 and the second verification of §6.7 before step 5.
- §8: audit action `lifecycle.reference_released` (§6.6).
- §13: owner decision A-5 = P-3 (§8 here).

## 12. Not verified

- Real S3/MinIO behaviour (paging, `DeleteObject` on a missing key, prefix policy conditions),
  bucket versioning, retention, replication and backups.
- Database behaviour (JSONB containment cost, `FOR UPDATE` over the candidate set, concurrent
  consumers writing `result_ref`).
- Whether another branch adds writers of Parent `source_refs`.
