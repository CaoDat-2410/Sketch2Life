# Core database migrations

The initial `20261014_0001` revision creates only the FEAT-046 core persistence tables. It has no seed rows. Configure `SKETCH2LIFE_DATABASE_URL` in the backend's ignored local `.env` or runtime environment/secret manager using the `postgresql+psycopg` driver, then run Alembic from the repository root:

```powershell
python -m alembic -c backend/alembic.ini upgrade be1_core@head
```

The environment holds independent module branches: `be1_core` (BE1) and `ai_jobs` (BE2, FEAT-044 Phase B,
schema `ai_jobs`). Use `upgrade be1_core@head` or `upgrade ai_jobs@head` for one module, or `upgrade heads`
for all modules. Plain `upgrade head` is ambiguous and fails with "Multiple head revisions" without changing
the database.

The BE1 runtime needs every head, not only `be1_core`: the classroom revision (`20261120_cls_0001`, branch `lesson_library`) and the Teacher profile revision head (`20261121_bpr_0001`, goal v4 T-12b, branch `frc08_lifecycle`) sit on other branches, so `upgrade be1_core@head` alone leaves the BE1 models without their columns. An existing database needs one `upgrade heads` before the new code runs.

Deploy with `upgrade heads`: the FR-C-08 lifecycle revision `20261119_frc08_lifecycle_scope` (branch `frc08_lifecycle`) only depends on the Story head, so a per-module `upgrade <branch>@head` skips it.

The URL is required at runtime; no credential or default URL is stored in this repository. Do not print it in logs or command transcripts. The migration does not upload media or connect to Redis, Firebase, or an object store.

The downgrade drops the new FEAT-046 tables and their records. Before using it against any database with data, take and verify a database backup; restore uses the database's normal PostgreSQL backup/restore procedure. No deployment or live database migration is authorized by FEAT-046.

`features/FEAT-046-be1-durable-core-adapters/fixtures/core_persistence.synthetic.json` contains synthetic metadata only and is not loaded by Alembic. The migration intentionally creates no seed rows; use the fixture only in an explicitly prepared isolated local verification workflow.
