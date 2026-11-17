# C2 persistence checkpoint — 2026-10-17

Approved architecture: FEAT-048 plan revision 1 P4. Source changes are limited to
content ports/SQL, a new frozen migration and additive shared Alembic metadata.
No old migration, BE1/job table or foundation source was changed.

## Implemented, not yet runtime-validated

- Owned learning_content schema: record/version/review/receipt/event/outbox.
- Global record CAS, immutable authored version fields and review/history;
  edit versions remain distinct. Shared read lock prevents torn head/version/
  review reads; writers acquire UPDATE at the start.
- One UoW transaction persists record/review/receipt/history/outbox together;
  typed conflicts roll back the whole candidate. No broker is started.
- New independent Alembic branch learning_content, revision 20261017_lc_0001.
  Frozen DDL does not import future runtime metadata. Triggers protect immutable
  authored fields and append-only review/event/receipt rows.
- Alembic env retains core and ai_jobs and adds only the new owned metadata.
- Nine disposable PostgreSQL 17 tests: upgrade/downgrade, restart/isolation,
  rollback, CAS/concurrency, version history and immutable SQL guards.

## Actual local verification

Existing Python venv, no install:
- Combined C1, C2 offline, runner classification and selected foundation tests:
  202 passed, 9 skipped in 4.72s. The nine SQL skips are NOT_RUN, not runtime acceptance.
- Focused Ruff: PASS after fixing SQL string line lengths/import formatting.
- Focused Mypy on content ports/infrastructure: PASS, four source files.
- Offline Alembic upgrade learning_content@head --sql: PASS, generated own DDL
  without opening a database. Connection string was a noncredential dummy.
- Five offline metadata tests PASS, including frozen-DDL equivalence and
  keeping all FK within the owned schema. Not evidence that SQL executes.
- No LC_TEST/BE2 PostgreSQL profile or SKETCH2LIFE_DATABASE_URL supplied in
  the current process. Docker CLI not found. No service or database created.
- Eight runner unit cases use mocked subprocess/JUnit and prove PASS vs
  missing/skip/extra/fail/collection-error classification only, not SQL behavior.
- Author source review caught and fixed missing PL/pgSQL END semicolons before
  publishing the new migration. Offline generation is not a SQL parser.

## Remaining gate and runtime pack

Before C2 durable acceptance, run src/run_c2_sql_checks.py with an explicitly
authorized disposable database profile as described in C2_RUNTIME.md.
It runs the actual test inventory, requires all nine unskipped cases, writes
source hashes/JUnit/raw output and returns PASS/FAIL/NOT_RUN distinctly.
This runner is C2-specific, not a full-card acceptance gate. It does not prove
HTTP, publication-service behavior or real cross-owner authority adoption.

C3 application/current eligibility/review integration and C4 dispatcher/API
are still required. No claim that SQL tests have executed successfully.
