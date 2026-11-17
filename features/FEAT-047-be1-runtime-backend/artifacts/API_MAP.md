# BE1 v1 API map

Base path: `/api/be1/v1`. There are 47 HTTP operations across 42 paths. The full method/path/request/auth/response/error contract is in [`API_CONTRACT.md`](API_CONTRACT.md), with the BE1-only machine-readable OpenAPI 3.1 document at [`openapi-v1.json`](openapi-v1.json). Contracts are versioned in responses and Pydantic request schemas. All database operations require PostgreSQL. Adult routes require a verified Firebase Authentication ID token plus an active backend organization/class assignment. Device routes require a server-issued admitted grant and the device key. No route accepts a client-supplied role as authorization.

| BE1 capability | Routes | Durable behavior and gate |
|---|---|---|
| Runtime readiness | `GET /health` | Executes a PostgreSQL probe; does not report ready without DB connectivity. |
| Identity/organization/class | `GET /organizations/{org}`, `GET /organizations/{org}/me`, `POST/DELETE /organizations/{org}/assignments`, `GET/POST /organizations/{org}/classes` | Firebase subject is mapped to persisted assignments; organization and class scope checked on reads/writes. |
| Profiles/enrollment/consent | `GET/POST /organizations/{org}/classes/{class}/profiles`, `POST/GET .../consents`, `POST .../consents/{consent}/revoke` | Consent can be recorded only as `pending` or `revoked`. Profile create/list and all child-data operations deny while consent is not effective. No API can mark it effective. |
| Session and devices | `POST /organizations/{org}/sessions`, `GET /organizations/{org}/sessions/{session}`, session `lobby/start/pause/resume/finish` commands, `POST .../join`, join request list/admit/revoke, `POST .../device-grants/{grant}/refresh` | Session state uses optimistic revision checks and emits audit/outbox records. Join codes are returned once and persisted as hashes; device keys are persisted as hashes. Refresh proves possession of the current device key, rotates it, and returns the replacement once. Start/admission are consent gated. |
| Group and turn controls | Session `groups`, group member assignment, `POST .../groups/{group}/control` (`lock`/`unlock`), membership `progress/help/leave`, group `turns/{child}` | Teacher/Guide roles and class/session scope enforced. Lock closes active turns and blocks device canvas reads/writes; unlock requires an explicit new turn. Move closes the prior turn, and re-admission reuses the membership row without restoring its old group. Child-owned state is consent gated. Automatic grouping (BE1-16) is excluded. |
| Canvas and reconnect | Device `canvas/operations` append/sync, group `checkpoints` save/latest, group `restore`, device `reconnect` | Operations persist immutable attribution, bounded payload, idempotency receipt, expected revision and document epoch. Checkpoint files use opaque local filesystem references and checksums. Group/session are checked before checkpoint access. |
| Artifacts | Session `artifacts` upload/download | Validates PNG/JPEG/WebP bytes, dimensions and size; bytes persist under configured local root; metadata is organization/session/contributor scoped. Production returns unavailable until a provider is selected. |
| Gallery and portfolio | `POST/GET /organizations/{org}/gallery`, gallery `publish/annotations`, class `observations`, profile `portfolio` | Gallery and observations have durable metadata, provenance, and audit/outbox. Child data remains blocked pending consent and an approved portfolio purpose. |
| Data requests/retention | `POST/GET /organizations/{org}/data-requests`; `python -m sketch2life.infrastructure.persistence.be1_worker` | Requests are durable. Worker purges local session copies after 90 days and leaves the request `awaiting_external_purge` while provider-copy evidence is unavailable; it does not claim completion. |

## HTTP response contract

- Interactive reference is served at `/docs`; machine-readable OpenAPI is `/openapi.json`.
- Successful responses use the versioned `contract` field and resource-specific fields documented by each operation. `GET /api/be1/v1/health` returns `{"status":"ready","database":"postgresql","api":"be1-v1"}` only after a PostgreSQL probe succeeds.
- Every BE1 response carries `X-Request-ID`. A valid caller ID (`[A-Za-z0-9._:-]{1,120}`) is propagated; otherwise the server generates an ID.
- BE1 errors use `{"code":"ERROR_CODE","message":"Safe explanation","request_id":"..."}`. OpenAPI publishes the `Be1Error` schema for 401, 403, 404, 409, 410, 413, 415, 422, 500 and 503 responses. Request validation messages do not echo submitted values.
- The read-only API smoke command and captured live HTTP results are recorded in `evidence/notes/API_CONTRACT_AND_SMOKE_20261015.md`.

## Current gates

- A human owner must configure Firebase Authentication project settings/credentials before any authenticated adult CRUD call succeeds.
- An approved consent verification procedure and purpose catalogue are required before child profiles, admission, canvas, artifacts, gallery, observations, or portfolio data can flow. Current behavior is intentionally fail closed.
- Local filesystem artifact bytes are for local/test only. Production object storage and provider purge receipts remain unselected.
- SRS B22 proposed routes and DTOs are not asserted as the adopted product-wide API. The table above documents the FEAT-047 implementation contract.

Implementation details are in `backend/src/sketch2life/interfaces/http/routers/be1_*.py`, migrations in `backend/alembic/versions/`, and runtime evidence in `evidence/notes/IMPLEMENTATION_20261014.md`.
