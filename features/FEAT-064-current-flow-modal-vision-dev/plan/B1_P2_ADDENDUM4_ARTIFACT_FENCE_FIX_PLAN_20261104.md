# B1 P2 Addendum 4 — pilot artifact owner fence

**Status:** APPROVED for the bounded Addendum 4 scope by the owner's direct launch message in this chat. The existing approval record is not edited.  
**Diagnostic basis:** `evidence/B1_P2_ADDENDUM3_STALE_CONTEXT_DIAGNOSTIC_REPORT_20261104.md`, SHA-256 `28BCB6AC384A6769F1B6AD71CCBE41F530005C06097C5630A190547A00B3DE14`.

## Baseline

- Branch `feature/feat063-be-foundation`; HEAD `b6dbfa68e66718f3f40902c093e9ebd634b1ebb9`; index empty; 103 existing status entries.
- Before this task: `pilot_composition.py` SHA-256 `A0061FD6563694268A0B4FEF8D5BA5281B461B43DB9A47EC50297257376BAF44`; `test_pilot_queue_composition_b1.py` `5917CAAD6E318765CBA2026CA513D6FAED9C22BD0D739052F5D64E96EBC711F4`; `test_be1_synthetic_pilot_postgres.py` `40CF435AF6D6A5374F1A1692C92043D5CDF8EE295B894A7BA0EC8012B9CBAFC2`.
- Existing worktree contains extensive unrelated dirty work and prior B1 changes. Preserve all bytes outside the scoped edits; do not stage, commit, push, merge, reset, stash, or clean.

## Authorized paths and design

Implementation is limited to `backend/src/sketch2life/infrastructure/vision_analysis/pilot_composition.py` and pilot tests: `backend/tests/unit/test_pilot_queue_composition_b1.py`, a new `backend/tests/unit/test_be1_pilot_artifact_fence.py` if needed, and test-only edits in `backend/tests/integration/test_be1_synthetic_pilot_postgres.py`.

`PilotFakeArtifacts` will issue a versioned `be1-pilot-artifact-v1:` scope bound to the artifact reference, organization, and SHA-256, with a store-managed integer epoch. Under the artifact-store lock, its hold operation must fail closed unless the artifact exists, the bound organization and digest match stored metadata, it is not quarantined, and the epoch has exact type `int` and equals the current epoch. First quarantine changes the state and bumps the epoch. Unknown/malformed scopes and exceptions are stale. `_CombinedBe1OwnerFence` routes auth fences to the existing authorization check, BE1-facts fences to the existing PostgreSQL owner fence, and artifact fences to this store check; duplicate scopes and multiple auth fences remain stale. Existing auth/facts semantics are preserved.

The artifact store remains process-local and non-durable. Its fence is only valid within that pilot process and is not a production or cross-process guarantee. `ArtifactDescriptor` and shared ports remain unchanged.

## Acceptance and execution order

1. Add focused unit cases and run them against the current implementation to record red results before source edits. Cover descriptor fence issuance, valid artifact-only hold, mixed auth/facts/artifact hold, quarantine epoch change, absent artifact, forged organization/digest binding, non-integer epoch, unknown scope, duplicate scope, transaction requirement for the auth/facts branch, and unchanged auth/facts outcomes.
2. Make the minimal allowed source change and rerun focused tests to green.
3. Against only the retained task-owned PostgreSQL database `s2l_b1_review_20261104_6a1af65b` (PostgreSQL 17, explicit loopback, port 5433, user `postgres`), run and separately log the success, UNKNOWN, HOLD, artifact-stale, facts-stale, concurrent-duplicate, and replay-after-SENT test cases. No DB create/drop/reset/truncate/migration or manual cleanup. Preserve fixture-owned exact-row cleanup only. No connection URL or credential in logs.
4. If every PostgreSQL case passes, run the pinned full offline regression runner. Otherwise mark it NOT RUN with the blocking case.
5. Run Ruff check, Ruff format check (report only), strict mypy with a writable task-local cache directory, the three repository validators, and `git diff --check`. Do not format the whole pre-existing dirty integration test file.
6. Preserve the Addendum 3 diagnostic wrappers only if removal would erase needed evidence; otherwise remove them. Always retain the existing `head -> observation -> provider_result` ordering wrapper. Correct import order manually with only the needed import edit.
7. Route-surface comparison and historical URL-guard replay are optional and may be recorded NOT DETERMINED/NOT RUN if a clean baseline or exact command cannot be established without disturbing the dirty checkout.

## Stop conditions and records

If behavior requires an out-of-allowlist file, changes auth/facts semantics, weakens a guard, or any PostgreSQL case reveals a new out-of-scope defect, stop and report BLOCKED at that case. No approval record, production file outside the allowlist, schema, migration, AI Jobs core, route, worker, provider, Modal, GPU, external network, B2, or other task is in scope.

Full pytest stdout/stderr, exact relative command, and exit code for every run will be saved under the new ignored `.claude/handoff/snapshots/GB1_P2_A4_<timestamp>/logs/`. A new feature evidence report and snapshot manifest will state hashes, checkout counts, results, residual process-local limitation, and final status `XONG-CHƯA REVIEW` or `BLOCKED`.
