# A2 Rev3 — exact PostgreSQL target URL guard review fix

Date: 2026-11-03  
Status: **XONG-CHƯA REVIEW**. This verification does not change A2's independent-review disposition.

## Finding and current working-tree state

The P2 finding in `A2_REV3_MAIN_DB_INDEPENDENT_REVIEW_20261103.md` requires the `sketch2life` test target to be restricted to port `5433` and explicit username `postgres`, while preserving loopback, `hostaddr`, service, and `be1_acceptance` behavior.

The current working-tree version of `backend/tests/integration/test_be1_synthetic_pilot_postgres.py` already enforces the requested exact URL port and username and validates `port`/`user` query overrides. Its URL cases include the approved `sketch2life` URL; rejection of port `5432`, omitted port, a different username, an omitted username, and mismatched query overrides; and unchanged positive/negative `be1_acceptance` examples. Existing loopback, `hostaddr`, service, and database override checks remain in place.

No source edit was needed in this turn: the file SHA-256 before verification, the snapshot copy, and the current file are all `D39A7F93717D281BDDB757DD490CE4E6778AA825E9B66FB1D3CFA5706FDD057D`. This report records a fresh focused verification of the already-present guard; it does not attribute the existing diff to this turn.

## Verification

Focused command:

```text
backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml -o addopts= backend/tests/integration/test_be1_synthetic_pilot_postgres.py -k "test_database_url_requires_loopback_and_approved_name or test_libpq_routing_environment" -q
```

Actual result: **35 passed, 65 deselected, 2.76 seconds, exit code 0**. The selection covers only pure URL/environment guard tests; it does not invoke the PostgreSQL fixture or connect to a database.

- Ruff check with cache disabled: **All checks passed**, exit code 0.
- Initial Ruff check without cache disabled: **NOT RUN to completion**, exit code 2 because Ruff could not create a temporary file under `.ruff_cache` (access denied). The same check with `--no-cache` completed successfully.
- Ruff format check: **not clean**, exit code 1; it reports an existing formatting difference around the unrelated AI-job cleanup test near line 2110, outside the URL guard. Left unchanged to keep this task limited to the guard.
- `git diff --check -- backend/tests/integration/test_be1_synthetic_pilot_postgres.py`: clean, exit code 0.
- PostgreSQL suite, PostgreSQL connection, Alembic, full offline runner, and DB cleanup: **NOT RUN**. The 58 previously disclosed synthetic rows were not inspected or changed.

## Checkout and scope

Branch: `feature/feat063-be-foundation`  
HEAD: `b6dbfa68e66718f3f40902c093e9ebd634b1ebb9`  
Index: empty. Existing unrelated working-tree changes were preserved. No approval, ledger, plan, source, database, or other test file was modified in this turn. No stage, commit, push, merge, Modal, provider, or external network operation occurred.

Snapshot: `.claude/handoff/snapshots/A2_URL_GUARD_REVIEW4_20261103T204801/`.