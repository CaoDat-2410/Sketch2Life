# A2 Rev3 — libpq environment routing guard review finding fix

Date: 2026-11-03  
Status: **FIXED — XONG-CHƯA REVIEW**. A2 remains unaccepted pending independent rereview.

## Independent finding

The second independent rereview confirmed the prior query database-override finding was fixed, then found that libpq can use environment-provided routing values even when the URL itself names a loopback host. The reported high-risk key was `PGHOSTADDR`; service selection can also supply connection defaults. A Python socket monkeypatch is not a boundary for libpq native sockets.

No local environment values were read or printed. The fix fails closed on the presence of target-routing environment keys before the fixture configures settings or creates a database engine.

## Change

Only `backend/tests/integration/test_be1_synthetic_pilot_postgres.py` changed for this finding. The fixture now rejects presence of `PGHOST`, `PGHOSTADDR`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGSERVICE`, or `PGSERVICEFILE` before engine creation. Its error reports only variable names, never values. URL host/hostaddr/service and effective database override checks from the previous fix remain. Focused tests cover every listed variable, a clean environment, and reporting multiple keys without values.

Plan: `plan/A2_URL_GUARD_REVIEW3_FIX_PLAN_20261103.md`, SHA-256 `A147E9199D5391DAD3A86762C1C4B23D8454C80E06A69589546E34FCFF5354F6`.  
Approval: append-only `approvals/TASK_APPROVAL.md`, SHA-256 at verification `FE8F14D0FE7A6E65A8B7CDBB6F8A8DD0955DF378A1DFAAA176C18A99D08C03B0`.

## Verification

- Focused command: `backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml -o addopts= backend/tests/integration/test_be1_synthetic_pilot_postgres.py -k "test_database_url_requires_loopback_and_approved_name or test_libpq_routing_environment" -q`
- Actual result: **35 passed, 65 deselected**, exit code `0`; these tests do not use the PostgreSQL fixture or open a connection.
- Ruff on the exact test file: **All checks passed**, exit code `0`.
- `git diff --check`: clean, exit code `0`.
- Current test file SHA-256: `D39A7F93717D281BDDB757DD490CE4E6778AA825E9B66FB1D3CFA5706FDD057D`.

PostgreSQL/Alembic, full GA2 runner, strict mypy, repository-wide validators, Modal/GPU/provider, and external network were **NOT RUN** for this narrow correction. Earlier A2 pass counts are historical, not rerun. The previously disclosed 58 synthetic rows from the earlier teardown failure were not inspected, changed, or cleaned. No credentials or environment values were accessed.

## Checkout and handoff

Branch remains `feature/feat063-be-foundation`; HEAD remains `b6dbfa68e66718f3f40902c093e9ebd634b1ebb9`; index is empty. Unrelated working-tree changes were preserved. No DB operation, migration, stage, commit, push, merge, or B1/B2 work occurred.

Snapshot: `.claude/handoff/snapshots/A2_URL_GUARD_REVIEW3_FIX_20261103/`. Its manifest records the exact test, plan, approval, report, context/status/ledger, and saved focused outputs for independent rereview.
