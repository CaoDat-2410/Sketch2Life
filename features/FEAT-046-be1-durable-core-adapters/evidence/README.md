# Evidence index

Status: approved BE1-02 acceptance criteria implemented and verified with synthetic data on ephemeral PostgreSQL 17.11; production/API integration remains outside this feature scope.

| Evidence ID | Related criteria | Type | Artifact | Status |
|---|---|---|---|---|
| E-001 | AC-01, AC-07–AC-09 | Static implementation/type review, dependency/privacy review, and synthetic fixture | `notes/IMPLEMENTATION_REVIEW_20261014.md` | Ruff lint/format and targeted mypy passed; scope and limitations recorded |
| E-002 | AC-02 | Offline and live Alembic upgrade/downgrade | `raw/alembic_upgrade_head_offline_20261014.sql`, `raw/alembic_downgrade_base_offline_20261014.sql`, `raw/postgres_migration_runtime_20261014.txt` | Passed: live PostgreSQL 17.11 upgrade, downgrade, and re-upgrade; final schema has 8 core tables and 8 indexes |
| E-003 | AC-03–AC-06 | Synthetic PostgreSQL transaction, isolation, restart, and outbox acceptance verification | `raw/postgres_acceptance_smoke_20261014.txt` | Passed on ephemeral Docker PostgreSQL 17.11; no test suite added or run |
