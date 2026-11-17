# GA1 revision-count test alignment (2026-11-01)

**Status:** Owner-approved narrow test-only scope. The owner’s explicit approval is recorded append-only in `approvals/TASK_APPROVAL.md` before implementation.

## Reason

T7a adds the independent Alembic revision `20261102_pv_0001` in `backend/alembic/versions/20261102_pilot_vision.py`. The graph enumerator in `backend/tests/unit/test_synthetic_eligibility.py` therefore sees 25 revisions. Its existing fixed count of 24 and comment describing only the synthetic and age revisions are stale; the graph and head assertions remain the behavior under test.

## Exact scope and allowlist

- Change only the revision-count assertion and its adjacent explanatory comment in `backend/tests/unit/test_synthetic_eligibility.py` from 24 to 25, naming the additional pilot-vision revision in the comment.
- Add this plan, append one approval record to `approvals/TASK_APPROVAL.md`, add one evidence report under `evidence/`, and append the outcome to `status/PILOT_GOAL_LEDGER_20261101.md`.
- Store the exact offline-runner copy and output, plus the task snapshot, in the local-only `.claude/handoff/snapshots/GA1_TESTFIX_20261101T200313/` directory. Existing snapshots remain unchanged.

No other test, product source, migration, schema, or runtime file is in scope.

## Acceptance criteria

1. The test continues to derive the migration graph from repository files and expects 25 revisions, with the comment explaining the 22 baseline revisions plus synthetic, age, and pilot-vision revisions.
2. `test_head_counts_by_both_methods_match_the_derived_expectation` passes by itself.
3. The established GA1 offline suite is rerun from the copied, network-blocking runner with both existing add-ons (`test_canvas_render_limits_ga1.py` and `test_pilot_vision_persistence_ga1.py`), with database-test configuration removed and pytest temporary files outside the repository. Expected result after the single stale assertion is corrected: 618 passed, 4 skipped, 0 failed.
4. If the focused test or aggregate suite has any other failure, stop and retain the result as a blocker; do not infer the regression gate has passed.

## Exclusions

This addendum does not authorize T6 changes, PostgreSQL operations, Modal/GPU/provider calls, external network access, real-child data, or any Git staging/commit/push operation. T6 may be considered only after the aggregate regression gate is green and under its existing task approval and exact allowlist.
