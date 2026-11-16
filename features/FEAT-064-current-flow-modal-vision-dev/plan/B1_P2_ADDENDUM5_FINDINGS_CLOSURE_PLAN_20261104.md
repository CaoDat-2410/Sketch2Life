# B1 P2 Addendum 5 — close independent-review findings in pilot scope

**Status:** Owner-authorized by the direct Addendum 5 launch prompt. The prompt is the approval record for this bounded task; do not edit `approvals/TASK_APPROVAL.md`.

**Review basis:** `evidence/B1_P2_INDEPENDENT_REVIEW_20261104.md`, SHA-256 `BBB1934554B1C4DBFCBB94C7EA929CEC670EFE391336502F57AA251AF6E76364`.

## Baseline

- Branch: `feature/feat063-be-foundation`.
- Expected HEAD: `b6dbfa68e66718f3f40902c093e9ebd634b1ebb9`.
- At launch the index is empty and the working tree contains 108 existing status entries, including the independent-review report added after the reviewer's 107-entry pre-report capture. Their names and exact scoped-file bytes are captured under `.claude/handoff/snapshots/GB1_P2_A5_20261104T163618/baseline/`.
- Preserve all existing local work byte-for-byte except the expressly scoped edits below.

## Owner decisions and exact scope

- **FND-01 / decision (c):** accept point-in-time artifact-fence checking for this local synthetic default-off pilot. Do not hold the process lock through SQL commit. Document that limitation in the method docstring and test.
- **FND-02 / decision (d):** do not change AI Jobs runtime. Investigate recovery read-only, then pin the current stale-completion outcome with exact assertions. If no recovery exists, report that lifecycle finding open.
- **FND-07 / decision (e):** fix only the nine strict-mypy errors in `pilot_composition.py`; accept the PostgreSQL test file's existing typing debt for this task.

Allowed source/test files only:

1. `backend/src/sketch2life/infrastructure/vision_analysis/pilot_composition.py`: fix the nine specified typing diagnostics using the defining `ProviderContextMode` import, and clarify that `hold_fences` releases its lock before SQL commit. Do not change runtime behavior or public signatures.
2. `backend/tests/unit/test_be1_pilot_artifact_fence.py`: add a valid-format mismatching SHA-256 case and a point-in-time fence/quarantine property test.
3. `backend/tests/integration/test_be1_synthetic_pilot_postgres.py`: add durable PostgreSQL restart-after-SENT acceptance, assert exactly one authoritative completion receipt on success, and pin the currently observed stale-owner state without weakening assertions.
4. `backend/tests/unit/test_pilot_queue_composition_b1.py` may only be formatted if the final formatting gate requires it; no logic edits are planned.

No edits to services, repositories, ports, owner fence, schema, migrations, routes, worker/provider, approvals, status, or other files. Do not use `type: ignore`, broad `Any`, change AI Jobs behavior, or weaken assertions.

## Database and operating gates

- Before any DB connection, capture checkout metadata, the complete porcelain status-name list, and before-hashes/byte copies of the scoped files. Write this plan first.
- Use only retained database `s2l_b1_review_20261104_6a1af65b` on local PostgreSQL 17 at `127.0.0.1:5433`, user `postgres`, with `BE1_TEST_DATABASE_URL` scoped to each test command. Never print or persist the URL or credentials.
- No new/maintenance connection, DB create/drop/reset/truncate/migration, broad cleanup, other database, or manual deletion. Keep fixture cleanup limited to exact rows created by each test.
- No Modal, GPU, real provider, external network, stage, commit, push, merge, reset, stash, deletion, or B2.
- Every test/check command must save full output and exit status under the snapshot's `logs/` and be read back from that file. If a DB safety gate skips or produces no verdict, record NOT RUN and stop at that gate; do not retry with another shell, flag, URL, or database.

## Ordered acceptance

1. **Read-only recovery investigation:** trace `accept_completion`, `_decide_completion`, unresolved/lease/attempt handling, worker dispatch, and pilot queue. Record whether a STALE_CONTEXT job/attempt has an implemented exit from RUNNING and cite source locations.
2. **Red unit tests:** demonstrate the valid-format digest-mismatch test catches a real metadata mismatch and the point-in-time lifecycle test describes check → quarantine → stale recheck. Any mutation demonstration must occur only in a disposable copy outside the repository.
3. **Typing:** fix the nine `pilot_composition.py` diagnostics. Run strict mypy with `--no-incremental` and a TEMP cache on the same four logical files. Require zero errors in `pilot_composition.py` and both unit files; report the remaining PostgreSQL test diagnostics per file.
4. **PostgreSQL acceptance:** add the restart-after-SENT case using a newly constructed PostgreSQL-backed ledger/guard/worker, assert one success receipt, and assert the exact current stale-owner state. Run each new/changed node three times, then all seven focused nodes sequentially. A skip is not a pass; any skipped node stops this gate and the offline regression.
5. **Regression:** after all seven PG nodes pass, run the pinned Addendum 4 offline runner and the two focused unit files; report actual results.
6. **Formatting:** after logic is complete, hash first, format only `pilot_composition.py` and B1-created unit test files, hash after, then rerun unit tests, strict mypy, and Ruff check. Never format the pre-existing dirty PostgreSQL integration test wholesale.
7. **Repository checks:** from root run harness, security, architecture validators and `git diff --check`; save and inspect output.
8. **Closeout:** create one evidence report and a supplemental snapshot. Verify final hashes, complete status names, branch/HEAD/index, and that only allowed files plus this plan/report/snapshot changed. End `XONG-CHƯA REVIEW` if acceptance is complete, otherwise `BLOCKED`. Do not claim F2 or B1 accepted; independent review is still required.
