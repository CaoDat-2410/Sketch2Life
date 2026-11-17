# FEAT-046 implementation review — 2026-10-14

## Reviewed source

- SQLAlchemy 2.x PostgreSQL records cover aggregate revisions, canvas operation metadata, idempotency receipts, checkpoint metadata, asset metadata/lineage, audit entries, outbox events, and consumer receipts.
- `PostgresCoreStore.commit_canvas_mutation` conditionally advances the aggregate revision and persists the operation, receipt, audit entry, and outbox event in one database transaction. A stale compare-and-swap writes no dependent rows; integrity errors roll the transaction back and do not produce an accepted outcome.
- Organization-scoped reads return plain application/domain records for revisions, idempotency receipts, operations, audit history, checkpoint/asset metadata, and outbox state. The adapter does not expose SQLAlchemy ORM objects to application/domain callers. Idempotency receipt identity is `(organization_id, scope, key)`.
- Checkpoints reference both the aggregate and through-operation. The adapter checks organization, canvas, epoch, and revision bounds. Operation uniqueness includes document epoch so a new epoch can restart its own revision sequence.
- Outbox claims use row locks with `SKIP LOCKED` and expiring leases. A local consumer receipt, session-bound callback, and delivered state commit together. Remote effects are outside this exactly-once local boundary and require their own idempotency contract.
- Alembic revision `20261014_0001` creates the feature tables with no seed rows. Downgrade drops only these tables; the migration guide requires a verified backup before destructive rollback and describes restore from a PostgreSQL backup.
- `fixtures/core_persistence.synthetic.json` supplies synthetic relational seed data with no credentials or media bytes. It is marked `auto_seed: false` and must only be used by an explicit local verification workflow.
- Asset bytes remain outside PostgreSQL behind opaque references. No Firebase data service, queue, provider, deployment, credential, or real child record was added.
- Database URL loading uses a database-only settings model that ignores unrelated application keys from local `.env` files, so Alembic and the core engine do not trigger unrelated production AI/auth provider validation.

## Static checks run

```powershell
python -m ruff check --no-cache --config backend/pyproject.toml backend/alembic/env.py backend/alembic/versions/20261014_0001_core_persistence.py backend/src/sketch2life/application/ports/core_foundation.py backend/src/sketch2life/application/services/core_foundation.py backend/src/sketch2life/infrastructure/config/settings.py backend/src/sketch2life/infrastructure/persistence/__init__.py backend/src/sketch2life/infrastructure/persistence/core_models.py backend/src/sketch2life/infrastructure/persistence/core_store.py backend/src/sketch2life/infrastructure/persistence/database.py backend/src/sketch2life/infrastructure/persistence/outbox.py features/FEAT-045-be1-core-domain-foundation/src/in_memory.py
```

Result: `All checks passed!`

```powershell
python -m ruff format --check --config backend/pyproject.toml backend/alembic/env.py backend/alembic/versions/20261014_0001_core_persistence.py backend/src/sketch2life/application/ports/core_foundation.py backend/src/sketch2life/application/services/core_foundation.py backend/src/sketch2life/infrastructure/config/settings.py backend/src/sketch2life/infrastructure/persistence/__init__.py backend/src/sketch2life/infrastructure/persistence/core_models.py backend/src/sketch2life/infrastructure/persistence/core_store.py backend/src/sketch2life/infrastructure/persistence/database.py backend/src/sketch2life/infrastructure/persistence/outbox.py features/FEAT-045-be1-core-domain-foundation/src/in_memory.py
```

Result: `11 files already formatted`.

```powershell
$env:MYPYPATH = 'src'
.\.venv\Scripts\python.exe -m mypy --config-file pyproject.toml --follow-imports=silent src\sketch2life\application\ports\core_foundation.py src\sketch2life\application\services\core_foundation.py src\sketch2life\infrastructure\config\settings.py src\sketch2life\infrastructure\persistence\__init__.py src\sketch2life\infrastructure\persistence\core_models.py src\sketch2life\infrastructure\persistence\core_store.py src\sketch2life\infrastructure\persistence\database.py src\sketch2life\infrastructure\persistence\outbox.py
```

Result: `Success: no issues found in 8 source files`.

No test suite or database-connected migration was run; only offline SQL generation via Alembic was performed.

## Offline migration render

The repository backend virtualenv is Python 3.12.14 and has SQLAlchemy, Alembic, and psycopg installed. The supported interpreter can render both migration directions without a database connection:

```powershell
$env:SKETCH2LIFE_DATABASE_URL = 'postgresql+psycopg://localhost/sketch2life'
& .\backend\.venv\Scripts\python.exe -m alembic -c backend\alembic.ini upgrade head --sql 1> features\FEAT-046-be1-durable-core-adapters\evidence\raw\alembic_upgrade_head_offline_20261014.sql 2> $null
& .\backend\.venv\Scripts\python.exe -m alembic -c backend\alembic.ini downgrade 20261014_0001:base --sql 1> features\FEAT-046-be1-durable-core-adapters\evidence\raw\alembic_downgrade_base_offline_20261014.sql 2> $null
```

The URL above is synthetic and used only for SQL rendering. Upgrade contains 8 core tables and 8 indexes plus Alembic's version table. Downgrade drops all 8 core tables in reverse dependency order. Both artifacts are transactional and contain no logging/traceback text. Neither command connects to or modifies PostgreSQL.

## Database integration gate

`docker info --format '{{.ServerVersion}}'` could not connect to `//./pipe/dockerDesktopLinuxEngine`; `Test-NetConnection 127.0.0.1 -Port 5432` returned `False`, and no PostgreSQL Windows service was found. Therefore migrations have not been applied to a database, and restart persistence, transaction failure, or duplicate outbox delivery have not been exercised. Keep FEAT-046 `IN_PROGRESS` until those acceptance checks have feature-local database evidence.

The shell's global Python 3.14.7 is outside the package's `>=3.12,<3.14` range and lacks SQLAlchemy/Alembic/psycopg; use the backend virtualenv for future local verification.

## Final static validation

After adding the application ports/services, contract schemas, and domain modules, final checks were run from the repository root with the backend virtualenv:

```powershell
backend/.venv/Scripts/python.exe -m ruff check --no-cache --config backend/pyproject.toml <11 changed Python files>
backend/.venv/Scripts/python.exe -m ruff format --check --config backend/pyproject.toml <11 changed Python files>
backend/.venv/Scripts/python.exe -m mypy --config-file backend/pyproject.toml <11 changed Python files>
```

Results: Ruff checks passed; all 11 files were already formatted after formatting one remaining line in `core_store.py`; mypy reported no issues in 11 source files. The approved plan hash remains unchanged. These are static checks only; live database behavior is recorded below. No test suite was added or run.

## Tenant-scope review follow-up

Review found that aggregate revision and idempotency receipt reads did not require an organization scope even though the remaining reads did. The application ports now require `organization_id` for both operations. The initial migration stores receipt identity as `(organization_id, scope, key)`, and canvas mutation receipt writes persist the organization. The synthetic fixture and offline Alembic SQL artifacts were regenerated to match. Static checks passed again.

## Live PostgreSQL acceptance

The owner confirmed Docker PostgreSQL could be used. An ephemeral official `postgres:17` container was started on loopback port 55432 with a tmpfs data directory and synthetic-only credentials. The image reported PostgreSQL 17.11. The runtime migration was applied, downgraded to base, and applied again successfully; final inspection reported Alembic revision `20261014_0001`, 8 core tables, and 8 core indexes.

Manual acceptance checks using only synthetic identifiers verified atomic mutation writes, changed-fingerprint conflict rollback, stale CAS rejection, database-error rollback, organization-scoped reads, persistence of operation/receipt/audit/checkpoint/asset/outbox state after engine recreation, expired-lease reclaim, handler-failure rollback, and one-time local consumer effects. Exact results are recorded in `evidence/raw/postgres_acceptance_smoke_20261014.txt` and migration lifecycle output in `evidence/raw/postgres_migration_runtime_20261014.txt`. No test suite was added or run. The database was ephemeral and does not establish API wiring, deployment, or production readiness.
