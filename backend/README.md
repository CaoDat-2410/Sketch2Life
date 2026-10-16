# Backend modular monolith

The backend owns session truth, domain policies, application use cases, contracts, and infrastructure adapters. Keep provider and framework details at the outer boundary.

The backend is a Python package organized as a modular monolith. It is not a collection of route handlers that directly call the database or model providers.

See:

- [Python backend architecture](../docs/architecture/PYTHON_BACKEND_ARCHITECTURE.md)
- [Backend layer map](src/sketch2life/README.md)
- [Contract and integration rules](../docs/architecture/CONTRACTS_AND_INTEGRATION.md)

## BE1 runtime API

FEAT-047 exposes the durable BE1 API under `/api/be1/v1`. It requires PostgreSQL; there is no fixture or in-memory fallback for these routes. Apply Alembic migrations before starting the API:

```powershell
cd backend
$env:SKETCH2LIFE_DATABASE_URL = "postgresql+psycopg://<user>:<password>@<host>:5432/<database>"
.\.venv\Scripts\alembic.exe upgrade be1_core@head
.\.venv\Scripts\uvicorn.exe sketch2life.main:app --host 127.0.0.1 --port 8000
```

Configure Firebase Authentication with `SKETCH2LIFE_AUTH_PROVIDER=firebase`, `SKETCH2LIFE_FIREBASE_PROJECT_ID`, and either Application Default Credentials or the ignored local credentials file setting. The bootstrap command accepts a Firebase ID token interactively and provisions the first organization administrator without persisting the token:

```powershell
python -m sketch2life.infrastructure.persistence.be1_bootstrap "<organization name>"
```

The command prompts for the organization name and hidden Firebase ID token, then prints the generated organization ID and verified subject.

The `GET /api/be1/v1/health` endpoint checks PostgreSQL connectivity. Adult endpoints require a verified Firebase bearer token and a backend assignment. Consent records remain pending; the approved project decision blocks profile creation and all child-data paths until a consent verifier and purpose catalogue are approved. Local artifact bytes use the persistent directory configured by `SKETCH2LIFE_BE1_ARTIFACT_ROOT`; non-local environments return an unavailable-provider response until an object-storage adapter is selected.

BE1 responses echo a safe `X-Request-ID` header. If the caller does not provide a valid ID, the API generates one. BE1 errors use the versioned response shape `{"code":"...","message":"...","request_id":"..."}` for authentication, authorization, not-found, conflict, validation and dependency failures. The same response schema is declared in OpenAPI. Run the non-mutating HTTP smoke checks against a running API and PostgreSQL with:

```powershell
python tools/be1_api_smoke.py --base-url http://127.0.0.1:8000
```

The script checks PostgreSQL-backed health, missing-token rejection, BE1 404 handling, request-ID propagation, and the published OpenAPI contract. It does not create profiles, sessions, grants, or other business data. Successful authenticated business calls require the project's configured Firebase identity and an existing authorized assignment; consent-gated child-data calls remain unavailable until the owner-approved verification procedure exists.

Run the local retention worker with `python -m sketch2life.infrastructure.persistence.be1_worker --once` or omit `--once` for polling. It purges local copies after the configured 90-day session retention and records external copies as unresolved; it does not claim external purge completion.

The complete feature-scoped method/path/request/response/auth/error contract is documented in [FEAT-047 API_CONTRACT.md](../features/FEAT-047-be1-runtime-backend/artifacts/API_CONTRACT.md); the BE1-only OpenAPI 3.1 document is [openapi-v1.json](../features/FEAT-047-be1-runtime-backend/artifacts/openapi-v1.json). PostgreSQL-backed acceptance tests are in tests/integration/test_be1_postgres_api.py. They require BE1_TEST_DATABASE_URL to point at a disposable database with “be1_acceptance” in its name, migrated to Alembic head. The test-only identity override does not change runtime authentication.
