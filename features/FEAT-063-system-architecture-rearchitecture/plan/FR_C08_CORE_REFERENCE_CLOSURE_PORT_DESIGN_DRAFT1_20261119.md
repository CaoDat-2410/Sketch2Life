# FR-C-08 Core reference-closure and storage-ownership port — design, Draft 1

**Status: DRAFT / NOT REVIEWED / NOT APPROVED.**
**Date:** 2026-11-19.
**Purpose:** the Core Asset contract that D-214 item 7 and D-215 item 3 require before FR-C-08
can be implemented: how a Parent run's assets are found, which may be removed, who deletes the
stored objects, and how removal is verified. Settled from the canonical SRS where the SRS
speaks; the remaining choices are marked as coordinator choices for the review. This document
approves nothing and grants no implementation, command, database, storage or test authority.

## 1. Pins

| Input | Pin |
|---|---|
| Canonical SRS (D-209) | `artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`, 701,157 bytes, SHA-256 `B9B1F42D0BB118C19C81607D3913B7E4F1D8B6F673F0C3FBB6402888FEB675F5` |
| Decisions | FEAT-063 D-214 items 6-7, D-215 item 3, D-216, D-217 items 4 and 9 (working tree, uncommitted) |
| Companion | `plan/FR_C08_LIFECYCLE_DTR_DRAFT2_20261119.md` (§6 step 2, §7), under review |
| Code base | `feature/feat066-conv1` at `03342207`, read in `.worktrees/conv1` |

## 2. SRS requirements this port must meet

| SRS line | Requirement |
|---|---|
| 1004 | Core owns shared audit, aggregate revision, outbox, asset metadata/lineage, upload sessions and part receipts |
| 1052 | Each source and derived artifact has an immutable asset identity and source lineage |
| 1053 | Cancel uses the same lifecycle purge as delete: revoke access at acceptance, cancel jobs best-effort, delete every eligible object and metadata |
| 1054 | Delete creates a lifecycle request for the run's private content and generated artifacts; an asset still referenced by another valid object is deleted only when no valid stored reference remains, per the owner lifecycle |
| 1949 | Each source/derived object records owner scope, media type, size, checksum, time, source ref, model/config revision and deletion state |
| 1951 | Lifecycle revokes access, cancels jobs, then deletes eligible objects/metadata in idempotent batches; failure keeps deletion pending for retry; not complete until all objects are reconciled |
| 1952 | Sharing assets between runs is not a V1 feature; a referenced asset is deleted only when the lifecycle confirms no valid reference remains |
| 2144-2146 | Keep the deletion request pending until required object refs are reconciled; never return an internal object key in a client error; raise unclear shared references to owner review and do not purge a source that may still be retained |
| 805 | No cross-schema SQL: modules compose through ports |
| register 78, 547 | Do not delete a retained original or a shared reference because one run reference is removed; the owning lifecycle reconciles references before purge; a lesson source used by an occurrence is never silently deleted by a run delete |

## 3. Source facts at the base (read-only)

| # | Fact | Evidence |
|---|---|---|
| C1 | The Parent artwork route stores two objects per run through the `ObjectStoragePort` instance `app.state.lesson_library_storage` (an S3-compatible bucket adapter). The object key **is** the asset ref: `parent/{run_id}/{random hex}/original` and `parent/{run_id}/{random hex}/normalized.png`. Object metadata carries the hash and the run ref. | `interfaces/http/routers/parent_ai.py:255-320`; `interfaces/http/app.py:1084-1093` |
| C2 | The same transaction path writes two `core_asset_metadata` rows (`PARENT_ACCOUNT`, `organization_id` NULL, `owner_scope_ref` = Parent principal scope ref, `source_refs = [run_id]`, the normalized image with `derived_from_ref` = the original) and one `core_asset_lineage` edge (original → normalized). A run accepts artwork once (`PARENT_STORY_ARTWORK_ALREADY_ATTACHED`). | `infrastructure/persistence/parent_story_repository.py:539-660` |
| C3 | `core_asset_lineage` has foreign keys to `core_asset_metadata` that are checked immediately, so lineage edges must be removed before the metadata rows they point at. | `parent_story_repository.py:593-594` (comment); `infrastructure/story_run_lite/tables.py:209-210` (composite FKs added by migration) |
| C4 | `CoreAssetMetadataPort` offers only `save_asset_metadata` and `get_asset_metadata(asset_ref, version, organization_id=…)`; it has no Parent-scope read, no reference query and no deletion. | `application/ports/core_foundation.py:181-186` |
| C5 | `ObjectStoragePort` offers `put_object`, `get_object` (returns `None` for a missing key) and `delete_object`. The S3 adapter maps `NoSuchKey`/`404` to `None` on read; S3 `DeleteObject` on a missing key succeeds. | `application/ports/object_storage.py:27-40`; `infrastructure/storage/s3_compatible.py:81-105` |
| C6 | On a failed attach, the route itself deletes both object keys (best-effort). | `parent_ai.py:311-325` |
| C7 | No Parent run at the base stores scene, video or audio assets; story revisions and scenes hold text and refs only. | `infrastructure/story_run_lite/tables.py:498-606` |
| C8 | The StoryRun-lite demo path keeps assets in a local quarantine directory (`QuarantineStore`, key `{asset_ref}.bin`), separate from the Parent product path. | `infrastructure/story_run_lite/quarantine.py:20-145` |

## 4. Ownership (settled)

1. **Core Asset owns the run's asset records and their objects.** It is the only module that
   deletes `core_asset_metadata` rows, `core_asset_lineage` edges and the stored objects they
   name (SRS line 1004; register line 78). Story never deletes an object or a Core row.
2. **Story owns the run's references to assets** (`story.runs`, `story.run_inputs` asset ref
   columns). It clears them in its own purge step (DTR §6 step 1). Core never reads `story.*`
   (SRS line 805).
3. **Which bucket.** At the base the Parent objects live in the bucket behind
   `app.state.lesson_library_storage` (C1). The Core purge adapter is given that same
   `ObjectStoragePort` instance. Moving Parent objects to a separate Core bucket is out of
   FR-C-08 scope; it would need a data migration and its own approval. *(Coordinator choice: it
   avoids moving data; the review should confirm.)*
4. **Lesson sources are never in scope.** A Parent run's assets are only those whose metadata
   names the run in `source_refs` (C2); a lesson source never does, so a run purge cannot reach
   it (register line 547).

## 5. Port

A new Core port, separate from `CoreAssetMetadataPort` so that existing callers are unchanged:

```text
class RunAssetPurgePort(Protocol):
    def plan_run_purge(self, *, scope: OwnerScopeRef, run_ref: str) -> RunAssetPurgePlan: ...
    def purge(self, *, plan: RunAssetPurgePlan, lifecycle_request_ref: str) -> RunAssetPurgeResult: ...
    def verify_run_purged(self, *, scope: OwnerScopeRef, run_ref: str) -> RunAssetPurgeVerification: ...

RunAssetPurgePlan:         scope, run_ref, removable: tuple[AssetKey, ...],
                           retained: tuple[RetainedAsset, ...], plan_sha256
AssetKey:                  asset_ref, asset_version
RetainedAsset:             asset_ref, asset_version, reason_code   (SHARED_REFERENCE, SCOPE_MISMATCH, LINEAGE_KEPT)
RunAssetPurgeResult:       removed_count, already_absent_count, retained_count, removed_sha256
RunAssetPurgeVerification: complete: bool, remaining_count, retained_count
```

`OwnerScopeRef` is the SRS `OwnerScopeRefV1` (kind and ref; SRS lines 771, 1048). Results carry
counts and digests only; no object key leaves Core in an error or a client response (SRS line
2145). The lifecycle receipt token (DTR §5.1) uses `removed_count` and `removed_sha256`.

**Supporting adapter change:** `ObjectStoragePort` gains `object_exists(key) -> bool` (S3
`HeadObject`), so verification does not download object bytes. *(Coordinator choice; the
alternative, `get_object(...)` and closing the body, works with no port change but reads data.)*

## 6. Rules

### 6.1 Plan (read-only)

1. Candidates: every `core_asset_metadata` row with the run's `owner_scope_kind` and
   `owner_scope_ref` whose `source_refs` contains `run_ref`, plus every row reachable from those
   through `derived_from_ref` or a `core_asset_lineage` edge (both directions).
2. A candidate is **removable** only when all hold:
   - its owner scope equals the run's scope; otherwise `SCOPE_MISMATCH`;
   - its `source_refs` equals exactly `[run_ref]`; any other entry means another valid
     reference, `SHARED_REFERENCE` (SRS lines 1054, 1952);
   - every asset linked to it by `derived_from_ref` or lineage is also removable; otherwise
     `LINEAGE_KEPT` (register line 78).
3. `plan_sha256` is the SHA-256 of the canonical JSON of the sorted removable and retained keys.

### 6.2 Purge (idempotent)

For each removable key, in sorted order:
1. delete the object (`delete_object`; a missing key is success);
2. then, in one database transaction: delete lineage edges that touch any removable key, then
   the metadata rows (C3 order).

Object first, rows second: if the row transaction fails, a retry still finds the rows and
deletes again (a missing object is success). The reverse order could leave an object with no
row to find it by. Between the two steps the run is already fenced (`DELETE_PENDING`; DTR §8),
so a dangling row is never served.

If the plan has any retained asset, `purge` removes nothing in that lineage group and the
lifecycle request goes to `exception` for owner review (SRS line 2146; DTR §5.1).

### 6.3 Verify (positive evidence)

`complete` is true only when, for this scope and run: no metadata row has `run_ref` in
`source_refs`, no lineage edge touches a removed key, and `object_exists` is false for every
removed key recorded in the plan. Access denial or a failed read is never treated as absence
(Contract Draft 8 §3.3; D-215 item 5).

## 7. Correction to DTR Draft 2 §7

DTR Draft 2 §7 also asks that "no `story.runs` or `story.run_inputs` row of another run
references it". Core cannot read `story.*` (SRS line 805). The equivalent Core-side test is the
`source_refs` rule of §6.1 (a second run's reference would appear in `source_refs`, C2). The
next DTR revision should replace that bullet with a pointer to this section.

## 8. Failure and retry

| Case | Port result | Lifecycle effect (DTR §5.1) |
|---|---|---|
| Storage unavailable on delete or head | `ObjectStorageFailure` raised; no row deleted for that key | receipt `awaiting_external_purge`; outbox redelivers; run stays `DELETE_PENDING` |
| Row transaction fails | error raised after objects were deleted | same; the retry deletes the rows |
| Retained asset in the plan | nothing in that group purged | receipt `exception`; owner review |
| Second call after success | `already_absent_count` > 0, `removed_count` 0 | verification is `complete` |

## 9. Candidate implementation paths (not approved; for the next allowlist)

| Kind | Path |
|---|---|
| Port types | `backend/src/sketch2life/application/ports/core_foundation.py` (new protocol and value types) |
| Storage port | `backend/src/sketch2life/application/ports/object_storage.py` (`object_exists`) |
| S3 adapter | `backend/src/sketch2life/infrastructure/storage/s3_compatible.py` |
| Core adapter | a new SQL adapter under `backend/src/sketch2life/infrastructure/persistence/` |
| Tests | unit tests for the plan rules and order; an owner-run PostgreSQL and MinIO test on a disposable target |

## 10. Verification required from the implementation task

- plan: a run with its two artwork assets is fully removable; a hand-made asset with
  `source_refs` of two runs is retained as `SHARED_REFERENCE` and keeps its lineage group;
  an asset of another scope is never a candidate;
- purge: object-first order; a simulated row failure followed by a retry ends complete; a second
  purge is a no-op;
- verify: false while any object or row remains; true only after all are gone; a storage error
  does not return true;
- no object key appears in any error body or log line produced by the port.

## 11. Open items

| ID | Item | Proposed handling |
|---|---|---|
| P-1 | Same bucket as Lesson Library (§4 item 3) | Accept for V1; review to confirm |
| P-2 | `object_exists` port addition (§5) | Accept; review to confirm |
| P-3 | Deletion state per object (SRS line 1949 lists "deletion state") | Not stored as a column; the lifecycle receipt carries the state for the run and the object is removed. If the review reads line 1949 as a per-row column, that is a DTR revision |

## 12. Not verified

- Behaviour of the bucket's versioning or retention settings (a versioned bucket keeps deleted
  versions; backups also keep copies). Provider-copy and backup treatment stay gated before real
  data (Contract Draft 8 §3.5).
- Whether any non-Parent writer ever puts a Parent run id in `source_refs`.
