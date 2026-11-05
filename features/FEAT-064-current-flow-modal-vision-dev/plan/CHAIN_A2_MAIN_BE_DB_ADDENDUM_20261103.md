# FEAT-064 Goal A2 — use the existing full BE database

- Status: **OWNER-APPROVED SCOPE ADDENDUM; fresh execution launch required**.
- Date: 2026-11-03.
- Applies only to GOAL A2 Rev3 and its PostgreSQL verification. It does not authorize B1/B2, migrations, Modal/provider calls, or database maintenance.
- This addendum supersedes the A2 Rev3 plan's task-owned/disposable-database restriction only. The original plan and prior approval remain unchanged as historical records.

## Owner decision

The owner instructed: “Xài mẹ data BE tổng đi khỏi riêng j hết mệt” (use the full BE database instead of a separate database).

For A2, use the existing main BE database `sketch2life`, previously observed on local PostgreSQL 17 at `127.0.0.1:5433`, with the normal `postgres` account. Re-verify every identity field read-only at the start of the fresh launch. Expected values are:

- database: `sketch2life`;
- host/port: loopback `127.0.0.1:5433`;
- PostgreSQL major version: 17;
- authenticated user and database owner: `postgres`.

If any value differs, credentials are unavailable locally, or the connection resolves to a non-loopback target, stop before test writes and report PostgreSQL `NOT RUN / BLOCKED`. Do not print a URL, password, or other credential.

## Required test-only adaptation

The current PostgreSQL test fixture rejects the main database because its safety predicate requires a database name containing `be1_acceptance`. The fixture also creates a uniquely generated synthetic organization and adult identity, then its teardown scans tables and deletes rows scoped to that generated organization (plus the generated adult identities). Therefore, simply pointing the old test at `sketch2life` will fail the guard, and bypassing the guard externally is not allowed.

The next A2 launch may make only these test-file changes in `backend/tests/integration/test_be1_synthetic_pilot_postgres.py`:

1. Extend the database-name safety predicate to accept the exact name `sketch2life`, only when all loopback and connection-target checks still pass; retain acceptance-database coverage for existing callers.
2. Add focused predicate tests showing `sketch2life` at loopback is accepted and a remote host, non-loopback `hostaddr`, service-based routing, or any other database name is rejected.
3. Audit and preserve test cleanup as strictly scoped to the current fixture's generated organization/adult identifiers. Do not broaden it, delete rows by table or organization prefix, or clean rows left by prior runs.
4. Keep the already-approved A2 teardown correction limited to deleting the exact test-created `attempt_id` before the exact test-created `job_id`, only if the previously reported FK teardown error reproduces.

No runtime source, migration, schema, table, existing BE record, or test behavior/assertion may be changed under this addendum. Do not apply Alembic or any migration. If the existing schema is not already sufficient, stop and request a separate scope.

## Database write and preservation boundaries

- Use the existing full BE database as-is; do not create another database or schema.
- Do not reset, drop, truncate, recreate, migrate, or broadly clean any database or schema.
- Do not seed, edit, or delete existing BE records. The only permitted writes are synthetic records created by the current test run using its fresh random identifiers; cleanup may remove only rows provably owned by that exact fixture invocation.
- Do not run the test concurrently with another integration suite or a BE process that writes to this database. If exclusive test access cannot be established, mark PostgreSQL `NOT RUN / BLOCKED`.
- Before tests, record a read-only inventory sufficient to verify the target identity and that the existing BE schema is present. Preserve all pre-existing row counts and values; do not compare or export personal data. If any setup or teardown could touch rows outside the current fixture identifiers, stop before that operation.
- Re-run the focused teardown case first. Only if it passes and all guards/cleanup are proven scoped may the A2 PostgreSQL module run serially against `sketch2life`.

## Acceptance and stop conditions

1. The exact database identity is verified read-only and matches the expected main BE target.
2. New guard tests pass; the guard fails closed for every non-approved target.
3. The teardown failure is freshly classified. Apply the already-approved exact attempt-before-job cleanup only if that failure reproduces.
4. All PostgreSQL tests run serially; report actual pass/fail/skip/error counts and real tracebacks. No prior database/test result is carried forward as current.
5. Existing BE data is unchanged. Synthetic rows created by the current run are cleaned only by exact fixture identifiers; any cleanup ambiguity or failure is a hard stop, with no manual cleanup of earlier rows.
6. No source/migration change, Modal/GPU/provider call, external network, stage, commit, push, or merge.

After the addendum and new launch, A2 remains subject to every other Rev3 acceptance gate, including the offline runner, strict mypy delta, Ruff, validators, diff-check, snapshot, and independent review. This addendum does not close A2 or authorize B1.
