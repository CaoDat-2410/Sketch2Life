# A2 Rev3 — URL database-override guard review fix

- Status: **PLAN DRAFT; owner launch instruction grants this narrow fix after independent review.**
- Date: 2026-11-03.
- Parent scope: GOAL A2 Rev3 and the owner-approved main-BE database addendum.
- Branch / HEAD baseline: `feature/feat063-be-foundation` / `b6dbfa68e66718f3f40902c093e9ebd634b1ebb9`; index empty.
- Current test-file baseline SHA-256: `D3F37B9F05B952C51D7A6A36807AA3D4E429FE564DB9989D8C44475B7E0D949E`.
- Independent review thread: `01a1a16f-ac73-7d32-8964-37f1428787cf`; verdict `NEEDS_REVISION`, one P2.

## Finding

The PostgreSQL URL safety predicate accepts a URL whose path names a loopback `*_be1_acceptance` database while a query parameter overrides the effective database name. Reproduction without opening a connection:

`postgresql+psycopg://other@127.0.0.1:5432/be1_acceptance?dbname=sketch2life`

The SQLAlchemy psycopg dialect forwards `dbname` to the driver's effective database argument. The URL guard currently applies database override checks only to the `sketch2life` path.

## Exact scope

Only `backend/tests/integration/test_be1_synthetic_pilot_postgres.py`, limited to the database URL safety predicate and its parameterized offline cases.

1. For every URL accepted by the existing predicate, reject `dbname` or `database` query values that differ from the database named in the URL path. If a query key is repeated, every value must match.
2. Preserve valid `*_be1_acceptance` URLs, including existing loopback callers and matching database query overrides.
3. Preserve the exact `sketch2life` restriction: port `5433`, username `postgres`, loopback-only host/hostaddr, no `service`, and all effective database/user/port overrides matching the approved target.
4. Add parameterized regression cases proving that a `be1_acceptance` path cannot be redirected to `sketch2life` through either `dbname` or `database`, including URLs whose port/user differ from the approved main database. Keep an accepted matching override case.
5. Do not change runtime code, database setup, migrations, existing assertions outside this guard, or the `be1_acceptance` path's valid target semantics.

## Verification and stop conditions

- Reproduce the pre-fix predicate acceptance locally without connecting to any database.
- Run only `test_database_url_requires_loopback_and_approved_name`; it must pass without a database fixture or DB URL.
- Run Ruff on the one test file and `git diff --check`.
- Do not run PostgreSQL/Alembic, repository-wide suites, Modal/GPU/provider, or external network.
- Keep branch and HEAD fixed; index remains empty. Preserve every unrelated worktree path.
- Record exact command outputs and status, create one additive snapshot with test-file/report hashes, then stop at `FIXED — XONG-CHƯA REVIEW` for independent rereview.

## Owner instruction

The owner requested creation of a separate independent A2 review and authorized fixing the review findings afterward in the direct message: “Tạo đc phiên độc lập r đó tạo cho review sau đó sửa gì thì sửa đi”. This plan narrows that authorization to the single P2 and exact test-only path above. It does not authorize PostgreSQL access, any runtime/source change, B1/B2, or Git publication.
