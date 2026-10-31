# T7a — durable repositories and invocation ledger report (GOAL A1)

**Status:** XONG-CHƯA REVIEW. Repository and ledger implementation, PostgreSQL migration roundtrip, and the focused PostgreSQL tests completed. The full offline regression set has one migration-count assertion made stale by the new pilot revision; it needs an explicitly scoped test update.

## Scope and files

Implemented the approved `pilot_vision` persistence branch, fixed-type JSON codec, scoped Assistance and Analysis repositories, and single-use invocation ledger. No service/port/ai_jobs changes, route composition, provider transport, Modal call, Git operation, or non-synthetic input was used.

Files in this task:

- `backend/src/sketch2life/infrastructure/vision_analysis/tables.py`
- `backend/src/sketch2life/infrastructure/vision_analysis/codec.py`
- `backend/src/sketch2life/infrastructure/vision_analysis/repository.py`
- `backend/src/sketch2life/infrastructure/vision_analysis/ledger.py`
- `backend/src/sketch2life/infrastructure/assistance/sql_repository.py`
- `backend/alembic/env.py`
- `backend/alembic/versions/20261102_pilot_vision.py`
- `backend/tests/unit/test_pilot_vision_persistence_ga1.py`
- `backend/tests/integration/test_pilot_vision_persistence_ga1_postgres.py`

## Verification

| Check | Result |
|---|---|
| Initial focused unit run | Collection failed because `SqlAssistanceUnitOfWork` did not yet exist; recorded as test-first red. |
| Focused T7a unit tests | 17 passed. |
| Ruff check / format check | Passed for the nine T7a Python files. |
| mypy | Success, no issues in five T7a source files. The first invocation could not open its cache DB; rerunning with a temporary cache path succeeded. |
| PostgreSQL preflight | Approved loopback acceptance DB; 98 application tables plus `alembic_version`, 561 application rows, 10 prior version rows; `pilot_vision` absent. |
| Migration graph | 11 script heads after adding the pilot branch. |
| Migration roundtrip | Upgrade, branch downgrade, upgrade succeeded; 9 pilot tables created, dropped, and recreated empty. Existing application row counts remained unchanged. The downgrade target was corrected to `pilot_vision@base`; the earlier reversed label `base@pilot_vision` was a no-op and was detected before running PG tests. |
| PostgreSQL persistence module | 5 passed, 1 pytest plugin warning. Cleanup restored all 107 application-table counts to the post-migration baseline (561 rows). |
| Full offline regression set, including the M1 canvas-render unit module and T7a unit module | 617 passed, 1 failed, 4 skipped. The single failure is `tests/unit/test_synthetic_eligibility.py::test_head_counts_by_both_methods_match_the_derived_expectation` at line 456: it asserts 24 total script revisions, but the new pilot migration makes the actual graph count 25. This test is outside the T7a write allowlist and was not changed. |
| Repository validators after report/ledger update | `HARNESS_VALID`; `REPOSITORY_SECURITY_VALID` (6,053 files scanned); `ARCHITECTURE_VALID`; `git diff --check` clean. |

The migration roundtrip resulted in 10 version rows after the branch downgrade (restoring the two dependencies) and 9 version rows at the final pilot head. The pilot schema contains exactly nine tables and zero rows. No preexisting application rows were deleted or rewritten.

## Outstanding

The focused T7a persistence tests and database acceptance completed. The aggregate offline suite is not fully green until the stale global revision-count assertion is addressed under an approved scope. This report does not label that suite as passing or the T7a work as independently reviewed.
