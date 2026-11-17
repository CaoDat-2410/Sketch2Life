# A2 Rev3 — libpq environment routing guard review fix

- Status: **PLAN DRAFT; owner authorized fixing independent-review findings in this conversation.**
- Date: 2026-11-03.
- Parent scope: GOAL A2 Rev3 and the owner-approved main-BE database addendum.
- Branch / HEAD baseline: `feature/feat063-be-foundation` / `b6dbfa68e66718f3f40902c093e9ebd634b1ebb9`; index empty.
- Current test-file baseline SHA-256: `634BBBFF89D346935C72D721C3FF966A007F4508A0B694FD71CE60366A2286AC`.
- Previous URL-override plan SHA-256: `C1DD0313D0D5398F836EE4F38AA625F82A394ECC138A894B19AC35DAE0F5A590`.
- Independent rereview thread `01a1a16f-ac73-7d32-8964-37f1428787cf`, turn `01a1a176-8fbd-7540-ae86-3ac444403c2a`: `NEEDS_REVISION`, one P2.

## Finding

The test guard validates URL host and URL/query `hostaddr`, but psycopg/libpq can obtain routing settings from process environment. In particular, `PGHOSTADDR` can direct a connection for a loopback URL to a non-loopback address; service selection can also supply connection defaults. Python socket monkeypatches do not constrain libpq's native socket.

## Exact scope

Only `backend/tests/integration/test_be1_synthetic_pilot_postgres.py`, limited to a test-only routing-environment guard and focused offline cases.

1. Define the libpq environment variables that can supply or alter the destination: `PGHOST`, `PGHOSTADDR`, `PGPORT`, `PGDATABASE`, `PGUSER`, `PGSERVICE`, and `PGSERVICEFILE`.
2. Before any database engine or connection is created, fail closed if any listed variable is present in the test process environment. The error may name variable keys but must never print their values.
3. Add focused offline tests proving each listed variable and multiple simultaneous variables are detected, while a clean environment is allowed. Keep URL host/hostaddr/service and both database-name checks intact.
4. Do not clear or rewrite the process environment silently; do not change runtime source, DB configuration, migrations, cleanup, assertions, or unrelated tests.

## Verification and stop conditions

- Confirm the independent finding from source/context without opening a database connection.
- Run only the URL/environment guard tests with no database fixture or connection.
- Run Ruff on the one integration-test file and `git diff --check`.
- Do not run PostgreSQL/Alembic, full GA2 runner, repository-wide validators, Modal/GPU/provider, or external network.
- Keep branch and HEAD fixed, index empty, and preserve all unrelated worktree paths.
- Record actual outputs, create one additive snapshot, and stop at `FIXED — XONG-CHƯA REVIEW` for independent rereview.

## Owner instruction

The owner requested a separate independent A2 review and authorized fixing review findings afterward: “Tạo đc phiên độc lập r đó tạo cho review sau đó sửa gì thì sửa đi”. This plan narrows that authorization to the single environment-routing P2 and one test file. It does not authorize database access/maintenance, runtime changes, B1/B2, or Git publication.
