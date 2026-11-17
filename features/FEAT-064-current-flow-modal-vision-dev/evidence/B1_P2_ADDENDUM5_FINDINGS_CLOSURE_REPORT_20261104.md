# B1 P2 Addendum 5 — findings closure report

**Final state: BLOCKED.** PostgreSQL acceptance could not start because the approved `BE1_TEST_DATABASE_URL` was absent from this process. No database connection was attempted, and the PostgreSQL-dependent findings remain unverified. No source files outside the authorized list, `TASK_APPROVAL.md`, or `STATUS` files were changed.

## Checkout and preservation

- Branch: `feature/feat063-be-foundation`.
- HEAD: `b6dbfa68e66718f3f40902c093e9ebd634b1ebb9` (unchanged).
- Index: 0 staged paths.
- Launch snapshot: 108 porcelain status entries; after adding the Addendum 5 plan and this evidence report there are 110. The complete launch and final path-name lists are in the snapshot.
- The four scoped files’ launch/current SHA-256 values:

| File | Launch SHA-256 | Final SHA-256 |
| --- | --- | --- |
| `backend/src/sketch2life/infrastructure/vision_analysis/pilot_composition.py` | `D79726EAEB949DA5EDBC7C95F5AF5C101A3BFC29A9114A165B35F7EB71C6AE9F` | `2D4A99E15C3650A3E30538B9557251872CAFEE338E3F82FF7917A55D8284F004` |
| `backend/tests/unit/test_be1_pilot_artifact_fence.py` | `364C430A317F569082F2578CA1EB190DB871F9E39D0ACEF6FE5459A309763756` | `3D3683640B3876E1431E02294561AF9C90C616FA0FC5C32711F1D6311B84FA1D` |
| `backend/tests/integration/test_be1_synthetic_pilot_postgres.py` | `25278C81DC842265B2CC73F7E62C8D9CBA4275B87983A3E8AF61DC9918244C7C` | `0620AFDEBDB83584C2AA97BE9BCD6E1437CD99B84C912E4EF216BA4B1885440D` |
| `backend/tests/unit/test_pilot_queue_composition_b1.py` | `5917CAAD6E318765CBA2026CA513D6FAED9C22BD0D739052F5D64E96EBC711F4` | `5917CAAD6E318765CBA2026CA513D6FAED9C22BD0D739052F5D64E96EBC711F4` |

The queue composition test has no net byte change from launch. `pilot_composition.py` changes are the requested annotations/import correction, `hold_fences` limitation text, and permitted Ruff formatting; no runtime behavior or public signature was changed. The B1 plan SHA-256 is `F52C1B733900CEDF8391C2DD2A619560EB8B630CE06BCF0426626004AD94A3AC`.

## FND-01..07 disposition

| Finding | Status | Result and evidence |
| --- | --- | --- |
| FND-01 | **ĐÃ GHI GIỚI HẠN THEO QUYẾT ĐỊNH OWNER** | `PilotFakeArtifacts.hold_fences` now states the lock releases at method return before SQL commit and does not prevent intervening quarantine (`pilot_composition.py:434`). The point-in-time test models current → quarantine → stale (`test_be1_pilot_artifact_fence.py:234`); final unit suite passed. |
| FND-02 | **ĐÃ GHI GIỚI HẠN THEO QUYẾT ĐỊNH OWNER** | Read-only investigation: **CÓ generic recovery**, through `expire_overdue_attempts()` (`ai_jobs.py:946-970`) or `Reconciler.run_once()` (`reconciler.py:27-32`). With the pilot’s `max_attempts=1`, this can expire a still-running attempt to `FAILED_EXHAUSTED` after its 180-second attempt timeout (`pilot_policy.py:5-11`). This is not wired into `PilotVisionComposition.dispatch_one()` (`pilot_composition.py:517-520`); the pilot dispatcher does not sweep, and pilot authorization allows only `CREATE_JOB` (`pilot_composition.py:185-195`), so a stale completion can remain `RUNNING` until an external caller invokes recovery. Current stale state is pinned in the PG test (`test_be1_synthetic_pilot_postgres.py:3570`) but that test is NOT RUN. No AI Jobs runtime change was made. Full excerpts are in `recovery-investigation.txt`. |
| FND-03 | **MỞ — chưa kiểm chứng PostgreSQL** | Added a process-rebuild acceptance case that simulates a crash after a successful loopback HTTP response while the durable invocation remains `SENT`, rebuilds composition/ledger/worker/envelope, then asserts the restarted provider cannot send a second request or accept a job result (`test_be1_synthetic_pilot_postgres.py:3388`). PostgreSQL test was NOT RUN. |
| FND-04 | **MỞ — chưa kiểm chứng PostgreSQL** | The success case now requires exactly one persisted accepted completion receipt and checks its `job_revision_after` against the final job revision and returned receipt (`test_be1_synthetic_pilot_postgres.py:3305`). PostgreSQL test was NOT RUN. |
| FND-05 | **MỞ — chưa kiểm chứng PostgreSQL** | Replaced loose inequalities with exact assertions: worker `rejected/STALE_CONTEXT`, job `running`, null result disposition, zero result refs/receipts, `SUCCEEDED` invocation, and `(None,)` attempt outcome, with a comment referencing owner decision (d) (`test_be1_synthetic_pilot_postgres.py:3570`). PostgreSQL test was NOT RUN. |
| FND-06 | **ĐÃ ĐÓNG ở unit-level** | Added a valid-format, different 64-character SHA-256 case (`test_be1_pilot_artifact_fence.py:158,191`). The mutation proof removed digest equality only in a disposable copy and the test failed at the intended assertion: 1 failed, 20 deselected. Final unit suite passed. |
| FND-07 | **ĐÃ ĐÓNG theo phạm vi owner** | Fixed the nine specified strict-mypy diagnostics in `pilot_composition.py`, including importing `ProviderContextMode` from its defining domain module (`pilot_composition.py:88`). Final strict mypy reports zero errors in that source and both unit files; the accepted 60 remaining errors are all in the PostgreSQL integration test file. |

## Verification actually run

- Unit tests after final formatting: **29 passed**, 0 failed (`unit-final.txt`). The digest mutation proof intentionally produced **1 failed, 20 deselected** in a disposable project, as expected; two earlier import-path probes passed and are not counted as mutation proof.
- Strict mypy: **60 errors**, all in `test_be1_synthetic_pilot_postgres.py`; **0** in `pilot_composition.py` and the two unit files. This is the accepted typing debt; mypy overall is not green (`mypy-final-pinned.txt`).
- Ruff check with the explicit backend config: **PASS** across all four scoped source/test files (`ruff-final.txt`). Ruff format check: **PASS**, three permitted files already formatted (`ruff-format-final-pinned.txt`). The first formatter invocation hit a `.ruff_cache` access-denied error after formatting the source; the same scope was rerun with `--no-cache`, then the pinned final check passed. Hashes before/after are in `format-hashes-before-pinned-format.txt` and `format-hashes-after-pinned-format.txt`.
- Integration-test syntax compile: **PASS** (`py-compile-integration-final.txt`).
- Harness, repository security (6,414 publishable files on final rerun), architecture, and `git diff --check`: **PASS**. Git reported only CRLF normalization warnings for existing dirty documentation files. The untracked evidence report also passed an explicit trailing-whitespace check.

## PostgreSQL and dependent regression gate

The approved database is only `s2l_b1_review_20261104_6a1af65b` at PostgreSQL 17 / `127.0.0.1:5433` / `postgres`, passed through `BE1_TEST_DATABASE_URL` for each command. The safety check found that variable absent and no `PGHOST`, `PGHOSTADDR`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGSERVICE`, or `PGSERVICEFILE` overrides (`environment-safety-check.txt`). No URL or credential was read from another source. Therefore:

- All seven focused PostgreSQL nodes, including three repeats for each changed node: **NOT RUN**.
- Pinned Addendum 4 offline regression: **NOT RUN**, because its acceptance prerequisite (all seven PostgreSQL nodes passing) was not met.
- Modal/GPU/provider/external network: **NOT RUN**.

No alternative shell, URL, database, maintenance connection, migration, reset, or broad cleanup was attempted. To resume this gate, launch with the approved database URL available only in the test-command process, then follow the exact sequence in Addendum 5. The current code and tests remain **unaccepted until the PostgreSQL cases run**.

## Snapshot and report hashes

- Snapshot: `.claude/handoff/snapshots/GB1_P2_A5_20261104T163618/`.
- Snapshot manifest SHA-256: `D2D63B42B85037A50D89C063942438729DA4493A0F4D0A867C9323485D319E2D`.
- Plan SHA-256: `F52C1B733900CEDF8391C2DD2A619560EB8B630CE06BCF0426626004AD94A3AC`.
- Evidence report SHA-256: recorded in `final/report.sha256` in the snapshot. That sidecar is explicitly excluded from the manifest because it would create a hash cycle; the report itself is outside the snapshot tree.

No approval/status ledger was edited. No database was accessed. No Modal/provider was called. No file was staged, committed, pushed, merged, reset, stashed, or deleted.
