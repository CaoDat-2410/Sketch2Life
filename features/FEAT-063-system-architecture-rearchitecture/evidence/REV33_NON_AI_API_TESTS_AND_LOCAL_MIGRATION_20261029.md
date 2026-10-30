# Rev33 non-AI API tests and local migration — 2026-10-29

## Authority and scope

- Approved Plan Rev33 SHA-256: `513FEE246CF1DD2B062BE146996C362C7C726667A9529E0E2342962084CF4DE1`; approval is recorded in `approvals/TASK_APPROVAL.md`.
- The owner authorized local API workflow testing and database migration. AI-related APIs were excluded.
- All identities, lessons, PDF content, and uploaded bytes used by the test suite were synthetic. No `.env` file was edited and no AWS, Firebase, remote database, or AI provider was accessed.

## Database migration

- Compose PostgreSQL was healthy on the existing named volume. The target was the local `sketch2life` database; before the migration it was at Alembic revision `20261014_0004` and had no `lesson` schema.
- Ran `docker compose run --rm --no-deps api alembic upgrade 20261028_ll_0001`.
- Alembic applied `20261014_0004 -> 20261024_0005 -> 20261028_ll_0001`. The unrelated independent AI/media heads were not applied.
- Afterward, `sketch2life` reported `20261028_ll_0001` (Lesson Library head) and `20261024_0005` (effective prerequisite head). The `lesson` schema contains seven base tables. The existing application database and named volume were retained.
- Created a separate `sketch2life_be1_acceptance` database, migrated it to the same target, and used it only for synthetic integration fixtures. It was dropped after the test run. The main `sketch2life` database remains present at the target revision.

## Reproduction commands

- `docker compose build api`
- `docker compose run --rm --no-deps api alembic upgrade 20261028_ll_0001`
- With `BE1_TEST_DATABASE_URL` set to a disposable local PostgreSQL URL whose database name contains `be1_acceptance`, run from `backend/`: `python -m pytest -q tests/integration/lesson_library/test_lesson_library_api.py` and `python -m pytest -q tests/integration/test_be1_postgres_api.py`.
- Synthetic pytest temporary files were retained locally during the run and are not included as repository artifacts.

## Build and API test results

- `docker compose build api` initially exposed that `backend/.dockerignore` excluded `alembic.ini` and `alembic/`, although the Dockerfile copies them. The ignore rules now explicitly include those migration files, and the API image build succeeded.
- Added `backend/tests/integration/lesson_library/test_lesson_library_api.py`. It uses real PostgreSQL, HTTP `TestClient`, synthetic verified-principal overrides, a deterministic PDF parser, and the local ClamAV service. The AI provider is disabled.
- Lesson Library HTTP suite: **5 passed**. Coverage includes Teacher CRUD/revision/organization scope; synthetic PDF upload, checksum, scan, extraction and revision preview; Manager publication; Parent discovery/read/export and moderation; direct/group invitations and revocation; and local storage-example upload/download/delete routes.
- Storage-example routes used an in-memory `ObjectStoragePort` override because MinIO could not be started. The MinIO adapter itself and private bucket initialization are therefore **unverified**.
- Existing BE1 HTTP suite `backend/tests/integration/test_be1_postgres_api.py`: **3 passed, 1 failed**. `test_room_code_start_revocation_stage_and_early_outcome_are_durable` expected HTTP 200 but received `409 CONSENT_NOT_EFFECTIVE`. This exposed a real consent-state contract defect: the `be1_consent_records` database check constraint and ORM permit only `pending`/`revoked`, while profile/admission/device authorization queries require `effective`. The successful consent-authorized path is therefore not representable in the current schema. Rev33 did not alter this consent model or add an unrelated migration; preserve the denial and resolve the state contract in a separately scoped change.
- Targeted Ruff checks and `compileall` for the changed backend files passed.

## Defects found and fixed during the approved test run

1. Parent access queries labeled `lesson_state` but the response mapper read `state`, returning `503 DATABASE_UNAVAILABLE`; the mapper now reads the selected label.
2. Parent-group membership responses omitted `revision`, causing the revoke route to fail while constructing its ETag; membership operations now return the revision.
3. BE1 session handling queried nonexistent `CoreCanvasCheckpointModel.session_id` attributes; checkpoint selection now uses the existing organization, canvas, and document-epoch scope.

## MinIO limitation

- The pinned `quay.io/minio/minio:RELEASE.2025-10-15T17-29-55Z` pull returned `401 UNAUTHORIZED`; a Docker Hub pull attempt also returned access denied. MinIO and its bucket-init service were not run.
- ClamAV started and reported healthy. The API image built successfully, but the full Compose API service could not be exercised against MinIO.
- The local storage-example HTTP routes were still exercised with the in-memory storage test adapter. This does not validate MinIO, S3 compatibility, container networking, or bucket initialization.

## Acceptance criteria disposition

| Criterion | Result |
|---|---|
| AC1 — local migration target and revisions recorded | Pass |
| AC2 — additive migration on application and isolated test DB | Pass |
| AC3 — HTTP workflows with real PostgreSQL and private MinIO | Partial: PostgreSQL and routes tested; MinIO unavailable, so the MinIO adapter was not exercised |
| AC4 — real auth/authorization/service/database/parser/storage boundaries | Partial: synthetic auth boundary and real DB/service/parser/ClamAV tested; object storage used an in-memory adapter |
| AC5 — negative authorization, revision, upload, and revocation behavior | Lesson Library covered cases pass; BE1 also surfaced the unrepresentable `effective` consent state described above |
| AC6 — AI APIs excluded | Pass; no AI API/provider was called |
| AC7 — synthetic-only data and no secret/remote service access | Pass |
| AC8 — results and limitations recorded | Pass |

Rev33 is submitted for review with the MinIO boundary and the BE1 consent-state defect disclosed. No commit or push was performed.
