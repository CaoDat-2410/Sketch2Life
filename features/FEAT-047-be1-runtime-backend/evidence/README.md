# Evidence index

Status: implementation is in progress. No real child data or seed accounts were used. Synthetic IDs and one synthetic pending profile exist only in the disposable PostgreSQL acceptance database and are removed after verification.

| Evidence ID | Related criteria | Type | Artifact | Status |
|---|---|---|---|---|
| E-001 | AC-01, AC-08 | PostgreSQL migration and metadata | `notes/IMPLEMENTATION_20261014.md` | Docker PostgreSQL 17; migrations 0001–0004 applied; no Alembic drift |
| E-002 | AC-01, AC-02 | Runtime composition and API schema | `../artifacts/API_CONTRACT.md`, `../artifacts/openapi-v1.json` | 42 BE1 paths / 47 operations; Firebase identity remains configuration-gated |
| E-003 | AC-03–AC-09 | Source and static checks | `notes/IMPLEMENTATION_20261014.md` | Changed BE1 source passes targeted Ruff and compile checks; child-data runtime blocked by approved consent gate |
| E-004 | AC-01, AC-07, AC-10 | Live HTTP, PostgreSQL, and worker evidence | `notes/API_CONTRACT_AND_SMOKE_20261015.md` | Live smoke: 200/401/422/404; PostgreSQL migrations and retention worker verified |
| E-005 | AC-01–AC-11 | Docker PostgreSQL acceptance | `raw/pytest-junit-be1-postgres-20261015.xml` | 3 focused HTTP/DB tests pass, including authorization, consent gates, persistence, and local retention |
| E-006 | AC-01–AC-11 | Full backend test suite | `raw/pytest-junit-acceptance-20261015.xml` | 2,173 collected: 2,167 passed, 6 skipped, 0 failures; initial in-repository basetemp attempt is retained separately for diagnosis |

Evidence is sanitized. It must not contain `.env` contents, credentials, access tokens, child data, or uploaded media.
