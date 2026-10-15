# Core database migrations

The initial `20261014_0001` revision creates only the FEAT-046 core persistence tables. It has no seed rows. Configure `SKETCH2LIFE_DATABASE_URL` in the backend's ignored local `.env` or runtime environment/secret manager using the `postgresql+psycopg` driver, then run Alembic from the repository root:

```powershell
python -m alembic -c backend/alembic.ini upgrade head
```

The URL is required at runtime; no credential or default URL is stored in this repository. Do not print it in logs or command transcripts. The migration does not upload media or connect to Redis, Firebase, or an object store.

The downgrade drops the new FEAT-046 tables and their records. Before using it against any database with data, take and verify a database backup; restore uses the database's normal PostgreSQL backup/restore procedure. No deployment or live database migration is authorized by FEAT-046.

`features/FEAT-046-be1-durable-core-adapters/fixtures/core_persistence.synthetic.json` contains synthetic metadata only and is not loaded by Alembic. The migration intentionally creates no seed rows; use the fixture only in an explicitly prepared isolated local verification workflow.
