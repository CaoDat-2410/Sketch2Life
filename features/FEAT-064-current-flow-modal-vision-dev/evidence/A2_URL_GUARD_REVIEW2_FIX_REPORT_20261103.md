# A2 Rev3 — second URL guard review finding fix

Date: 2026-11-03  
Status: **FIXED — XONG-CHƯA REVIEW**. A2 is not accepted until the independent rereview returns `ACCEPTED`.

## Independent finding and reproduction

The independent review thread `01a1a16f-ac73-7d32-8964-37f1428787cf` returned `NEEDS_REVISION` with one P2: a loopback URL whose path named `be1_acceptance` could use a `dbname` or `database` query override to target another database. The reviewer cited:

`postgresql+psycopg://other@127.0.0.1:5432/be1_acceptance?dbname=sketch2life`

Before the fix, an offline call to `_is_safe_acceptance_database_url()` returned `True` for that URL. No database connection was opened.

## Change

Only the URL predicate and its parameterized cases in `backend/tests/integration/test_be1_synthetic_pilot_postgres.py` changed for this finding. Every allowed URL now rejects `dbname` or `database` query values that differ from the path database; repeated values must all match. This blocks the `be1_acceptance` to `sketch2life` redirection. Matching overrides remain accepted. The existing `sketch2life` restrictions remain: port `5433`, user `postgres`, loopback host/hostaddr, no service routing, and matching target overrides. No runtime source, migration, or database state changed.

The narrow plan and owner approval are recorded in:

- `plan/A2_URL_GUARD_REVIEW2_FIX_PLAN_20261103.md` — SHA-256 `C1DD0313D0D5398F836EE4F38AA625F82A394ECC138A894B19AC35DAE0F5A590`.
- Append-only `approvals/TASK_APPROVAL.md` entry — SHA-256 at verification `88B91DF7CA594266EB00009B8DC1072CB3AC749CBB6BDA66CA7C688E270FC06F`.

## Verification

- Offline regression command: `backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml -o addopts= backend/tests/integration/test_be1_synthetic_pilot_postgres.py -k test_database_url_requires_loopback_and_approved_name -q`
- Actual result: **26 passed, 65 deselected**, exit code `0`. This selected test has no database fixture; no DB URL or connection was used.
- Ruff: `backend/.venv/Scripts/python.exe -m ruff check --no-cache --config backend/pyproject.toml backend/tests/integration/test_be1_synthetic_pilot_postgres.py` — **All checks passed**, exit code `0`.
- `git diff --check` on the test, approval, and plan paths — clean, exit code `0`.
- Current test file SHA-256: `634BBBFF89D346935C72D721C3FF966A007F4508A0B694FD71CE60366A2286AC`.

PostgreSQL/Alembic, the full offline GA2 runner, strict mypy, repository-wide validators, Modal/GPU/provider, and external network were **NOT RUN** in this narrow correction. Earlier A2 suite results remain historical evidence, not rerun results. The 58 synthetic rows disclosed after the earlier teardown failure were not inspected, modified, or cleaned.

## Checkout and handoff

Branch remains `feature/feat063-be-foundation`; HEAD remains `b6dbfa68e66718f3f40902c093e9ebd634b1ebb9`; index is empty. Existing unrelated working-tree changes were preserved. No database operation, stage, commit, push, merge, or B1/B2 work occurred.

Snapshot: `.claude/handoff/snapshots/A2_URL_GUARD_REVIEW2_FIX_20261103/`.  
The snapshot manifest records the exact test, plan, approval, report, and A2 status/context/ledger bytes for independent rereview.
