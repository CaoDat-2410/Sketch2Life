# StoryRun-lite S1→S2 environment record — 2026-11-02

## Runtime

- OS: Windows 10 x64.
- Python: 3.12.10, using the repository virtual environment `backend/.venv`.
- The backend environment has the project SQLAlchemy, Alembic, psycopg, FastAPI, Pillow and pytest dependencies available. Ruff and mypy are available from the same environment.
- Windows Job Objects are available to the isolated image worker; local kill-on-close, memory/CPU hard-cap readback, 40MP synthetic image processing and usage measurement passed. See `STORYRUN_LITE_S1_CHECKPOINT_20261102.md` for exact sample values.

## Local services and gates

- PostgreSQL Windows services `postgresql-x64-17` and `postgresql-x64-18` reported `Running`. No `SKETCH2LIFE_DATABASE_URL` or `STORYRUN_LITE_DATABASE_URL` was configured in the process environment or repository `.env` files. Loopback maintenance-only connection attempts did not establish a usable connection. No pre-existing application database was contacted; no database was created, inspected, migrated or dropped.
- `clamd.exe` and `clamscan.exe` were not found on PATH. The production scanner therefore remains unavailable and upload admission fails closed.
- Docker/container runtime was unavailable, so it was not used as an alternative worker limit mechanism.
- `bru` and `bruno` executables were not installed. OpenAPI/runtime/Bruno method-path consistency was checked by the contract test; the collection was not executed through the Bruno CLI.
- No Modal, GPU, external provider, remote inference, production endpoint, real child data or external network inference was used.

## Verification scope

- Test invocations used only the repository virtual environment. PostgreSQL integration fixtures require the verified goal-owned database; the five dependent cases were skipped when no `STORYRUN_LITE_DATABASE_URL` was present.
- The Windows image worker measurement used a temporary directory managed by `TemporaryDirectory`; it was removed at process exit. Pytest temporary fixtures stayed under the operating system temp root. No system configuration or service was changed.
- No database URL, password, token, or other secret was written to evidence.

## Final goal-owned local environment and cleanup — 2026-11-02

- The initially unavailable local runtime was supplied with isolated, goal-owned resources permitted by the launch prompt: a PostgreSQL 17 cluster on loopback port `55432`, three disposable `storyrun_lite_*` databases owned by `storyrun_lite_owner`, a portable signed ClamAV 1.5.4 package, and a local HTTP Vision stub. All database owner and loopback checks passed before migration/use. No system PostgreSQL service/configuration was used or changed.
- Only the `20261102_story_run_lite` migration branch was applied to the three goal-created databases. The database used for the combined test run reported the StoryRun-lite migration as the current head.
- After verification, the exact three goal databases were dropped and a query for those exact names returned zero rows. The goal-owned API processes, Vision stub, ClamAV daemon and PostgreSQL process were stopped; loopback listeners on their goal ports were absent afterward. Existing PostgreSQL Windows services were left running and untouched.
- The goal's temporary CLI/package and portable-scanner directories were removed after the evidence was captured. No secret or real child data was used.
