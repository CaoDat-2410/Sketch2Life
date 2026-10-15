# BE1 API contract and live smoke evidence — 2026-10-15

## Scope and method

- Branch: `codex/be1-real-backend`.
- The user requested recorded API tests and representative response bodies. The smoke command is `backend/tools/be1_api_smoke.py` and targets a running local BE1 API.
- API process was started on loopback against the running Docker PostgreSQL 17 service. Connection details and local credentials are intentionally excluded from this evidence.
- A separate startup probe without database runtime configuration returned HTTP 503 `DATABASE_NOT_CONFIGURED` and did not claim readiness. The passing run supplied the local Compose PostgreSQL configuration to the process.
- No Firebase bearer token, seeded adult, profile, child, session, device grant, artifact, or lifecycle request was created. Requests consisted of a PostgreSQL-backed health probe, missing-token request, malformed JSON request rejected during parsing, unknown BE1 route, and OpenAPI fetch.
- The malformed JSON request targets a POST route but is rejected before the endpoint executes; no business state is written.

## Results

| Check | Result |
|---|---|
| `GET /api/be1/v1/health` | HTTP 200; PostgreSQL probe succeeded |
| Protected classes route without bearer token | HTTP 401 `AUTHENTICATION_REQUIRED` |
| Session POST with malformed JSON | HTTP 422 `REQUEST_VALIDATION_FAILED` |
| Unknown `/api/be1/v1` route | HTTP 404 `NOT_FOUND` |
| `GET /openapi.json` | HTTP 200; 42 BE1 paths; `Be1Error` schema present |
| Request correlation | Caller-supplied safe ID echoed; generated IDs appear in both error body and response header |
| Database schema drift | Alembic `check` reports `No new upgrade operations detected.` |
| Static checks | Targeted Ruff and Python compilation pass; OpenAPI includes BE1 error statuses, `HTTPBearer` security, and request-ID parameter/response headers |

## Captured response examples

### Health (live)

```json
{
  "status": "ready",
  "database": "postgresql",
  "api": "be1-v1"
}
```

### Missing bearer token (live)

```http
HTTP/1.1 401 Unauthorized
X-Request-ID: be1-smoke-unauthenticated
Content-Type: application/json
```

```json
{
  "code": "AUTHENTICATION_REQUIRED",
  "message": "A verified bearer token is required",
  "request_id": "be1-smoke-unauthenticated"
}
```

### Malformed JSON (live)

```json
{
  "code": "REQUEST_VALIDATION_FAILED",
  "message": "The request does not match the BE1 API contract",
  "request_id": "<generated-request-id>"
}
```

HTTP status: `422 Unprocessable Entity`. The API does not echo submitted request bytes or Pydantic's raw input values.

### Unknown route (live)

```json
{
  "code": "NOT_FOUND",
  "message": "The requested BE1 resource was not found",
  "request_id": "<generated-request-id>"
}
```

HTTP status: `404 Not Found`.

### Database configuration unavailable (live fail-closed probe)

```json
{
  "code": "DATABASE_NOT_CONFIGURED",
  "message": "database is not configured for BE1 runtime",
  "request_id": "<generated-request-id>"
}
```

HTTP status: `503 Service Unavailable`. This was observed before supplying the process with its local PostgreSQL configuration; after configuration, the health check returned 200.

### Stale session revision (PostgreSQL acceptance exercised)

```json
{
  "code": "STALE_SESSION_REVISION",
  "message": "Session changed; reload before retrying",
  "request_id": "<generated-request-id>"
}
```

HTTP status: `409 Conflict`. The PostgreSQL-backed TestClient acceptance exercised this result using a synthetic verified principal; a live Firebase bearer token was not used.

### Pending consent (PostgreSQL acceptance exercised)

```json
{
  "code": "CONSENT_NOT_EFFECTIVE",
  "message": "Consent verification and purpose approval are pending; child data is blocked",
  "request_id": "<generated-request-id>"
}
```

HTTP status: `409 Conflict`. The TestClient acceptance exercised profile, admission, and session-start denial against pending consent using only synthetic IDs in the disposable database.

## Stateful API examples

These request examples show the client-facing bearer/device headers. No live Firebase token was available; the equivalent database-backed business handlers were exercised using a test-only synthetic identity override and the real PostgreSQL/filesystem adapters.

### Lock a group

```http
POST /api/be1/v1/organizations/{organization_id}/sessions/{session_id}/groups/{group_id}/control
Authorization: Bearer <firebase-id-token>
Content-Type: application/json
X-Request-ID: teacher-lock-01
```

```json
{
  "action": "lock",
  "expected_revision": 8
}
```

```json
{
  "contract": "Be1GroupControlV1",
  "group_id": "<group-id>",
  "state": "locked",
  "session_revision": 9
}
```

### Refresh an admitted device grant

```http
POST /api/be1/v1/organizations/{organization_id}/sessions/{session_id}/device-grants/{grant_id}/refresh
X-Be1-Device-Key: <current-device-key>
```

```json
{
  "contract": "Be1DeviceGrantRefreshV1",
  "grant_id": "<grant-id>",
  "device_key": "<replacement-key-returned-once>",
  "state": "admitted"
}
```

The client must replace the old key immediately. The backend stores only a SHA-256 digest of the key and does not write either key into audit or outbox payloads.

## Smoke command

From `backend/` with the API and local PostgreSQL already running:

```powershell
python tools/be1_api_smoke.py --base-url http://127.0.0.1:8000
```

The command exits non-zero on a failed status/body/header assertion and prints a JSON report on success.

## Limitations

- The read-only live HTTP smoke below does not verify a real Firebase token. The dedicated TestClient/PostgreSQL acceptance suite separately exercises authenticated route behavior with a synthetic test principal; Firebase identity verification itself remains untested without project runtime configuration.
- Child-data acceptance remains intentionally denied under the approved pending-consent decision. Synthetic database setup tests that a pending-consent profile cannot be enrolled/admitted or start a session; no real child record is used.
- This evidence is a local development smoke, not a production, privacy, load, or end-to-end acceptance claim.

## Docker PostgreSQL acceptance and full test run — 2026-10-15

- Docker PostgreSQL 17 was running as sketch2life-postgres-1. Acceptance used the disposable sketch2life_be1_acceptance database; the existing sketch2life database was not used for BE1 test records.
- Alembic migrations 20261014_0001 through 20261014_0004 applied successfully. alembic check returned No new upgrade operations detected.
- The BE1 PostgreSQL integration suite passed 3 tests. It verifies durable class/session/group/data-request state, audit/outbox writes, stale revision rejection, role denial and forged-role rejection, stable duplicate-join response, pending-consent profile/admission/session denial, device-key hash-only persistence, OpenAPI security/error declarations, filesystem read across a new store instance, one-time local retention purge, and awaiting_external_purge status.
- The integration tests replace only the Firebase verification dependency with a synthetic verified adult. Authorization, route handlers, SQLAlchemy transactions, PostgreSQL records, filesystem adapter, and retention worker are real. A synthetic child identifier and one synthetic pending profile are used only inside the disposable database to exercise the deny path.
- The full backend suite collected 2,173 tests: 2,167 passed, 6 skipped, and 0 failed. An earlier run put tmp_path inside the repository and tripped media-fixture tests that explicitly require an external output directory; rerunning with an external basetemp passed.
- Targeted Ruff passed for the BE1 routers/runtime/persistence and the integration test. Python compilation passed for 12 BE1 source/test files.
- The written route matrix cross-checks exactly 47 method/path rows against the BE1-only OpenAPI artifact: 42 paths, 47 operations, 0 missing/extra operations, and the HTTPBearer scheme is present.
- The worker command python -m sketch2life.infrastructure.persistence.be1_worker --once started against the disposable database and safely reported sessions_purged_locally=0 after the due synthetic session had already been processed by the acceptance test.
- The disposable database was dropped after verification; the existing sketch2life database remains. Automatic command review rejected cleanup of generated pytest temporary directories after their targets were verified; ignored local outputs containing only synthetic test artifacts remain in task temporary storage.

### Stateful response shapes exercised against PostgreSQL

Values below are generated per test run; identifiers are omitted here while preserving the actual response shape.

POST /organizations/{organization_id}/classes (201):

    {
      "contract": "Be1ClassV1",
      "class_id": "<generated-id>",
      "display_name": "Synthetic Class"
    }

POST /organizations/{organization_id}/sessions/{session_id}/lobby (200):

    {
      "contract": "Be1SessionV1",
      "state": "lobby",
      "revision": 2
    }

The session response also includes its scoped IDs/configuration and nullable start/end/retention timestamps.

Stale revision and pending-consent denials both returned HTTP 409 with the documented {code,message,request_id} body; the request ID matched the X-Request-ID header. The data-request create/read responses stayed state=requested and completion_claimed=false until the worker had verifiable results.

The latest full-suite report is [pytest-junit-acceptance-20261015.xml](../raw/pytest-junit-acceptance-20261015.xml); the latest focused database report is [pytest-junit-be1-postgres-20261015.xml](../raw/pytest-junit-be1-postgres-20261015.xml).
