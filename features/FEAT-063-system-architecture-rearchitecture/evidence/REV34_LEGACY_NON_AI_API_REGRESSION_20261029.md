# Rev34 legacy non-AI API regression — 2026-10-29

## Authority and scope

- Approved Plan Rev34 SHA-256: `308F4FEA6576BAB08ACCD86B62616FE463C94D099FC27EBF301E855C4756F5B1`; direct owner approval is recorded in `approvals/TASK_APPROVAL.md`.
- “Old APIs” means the pre-Lesson-Library BE1/classroom and Demo/local-flow surfaces in Rev32 catalog rows 1–91.
- AI-dependent catalog rows excluded from calls: 57–61 (preference/media/understanding), 64–67 (story video), 82 (AI ranking), 87 (AI-dependent renderer planning), and 89–91 (whiteboard video). No AI API/provider, Modal, or GPU call was made.
- Lesson Library and conditional storage example are newer APIs, not part of this regression. Candidate/unmounted APIs are reported separately from the active app surface.
- All requests/data were synthetic. The persistent application DB and `.env` files were not modified.

## Test environment and cleanup

- Used local Compose PostgreSQL on its existing healthy container/volume.
- Created `sketch2life_be1_acceptance`, applied Alembic target `20261028_ll_0001` and its declared prerequisite `20261024_0005`, and ran the PostgreSQL-backed BE1 HTTP suite against it. The test database was dropped after execution.
- Verified the test DB no longer exists. The persistent `sketch2life` DB remains at its pre-run Rev33 Alembic state: `20261028_ll_0001 (head)` and `20261024_0005 (effective head)`.
- No API code or existing test expectation was changed. The only new executable artifact is the feature-local, dispatch-only smoke helper referenced below.

## Commands

- Created the isolated DB with `docker compose exec -T postgres psql -U sketch2life -d postgres -c "CREATE DATABASE sketch2life_be1_acceptance;"`.
- Migrated only that DB by temporarily setting `SKETCH2LIFE_POSTGRES_DB=sketch2life_be1_acceptance` for `docker compose run --rm --no-deps api alembic upgrade 20261028_ll_0001`.
- Ran the non-PostgreSQL HTTP/API batch from `backend/` with `.venv/Scripts/python.exe -m pytest -p no:cacheprovider --tb=no --junitxml=<feature-evidence>/rev34-contract-junit.xml`, covering `test_session_http_api.py`, `test_health.py`, `test_app_composition.py`, `test_whiteboard_storyboard_api.py`, `test_activity_execution_http.py`, `test_learning_content_http.py`, `test_profile_context_validation_returns_safe_typed_failure` and `test_context_options_query_validation_returns_safe_typed_failure` from `test_live_image_demo_api.py`, and `test_preset_uses_same_http_route_etag_and_safe_business_errors` plus `test_preset_http_safe_error_allowlist` from `test_preset_automation_governance.py`.
- Ran the BE1 suite from `backend/` with `BE1_TEST_DATABASE_URL` set to the disposable acceptance DB and `.venv/Scripts/python.exe -m pytest -p no:cacheprovider --tb=no --junitxml=<feature-evidence>/rev34-be1-junit.xml tests/integration/test_be1_postgres_api.py`.
- Ran the route smoke from `backend/` with `SKETCH2LIFE_DATABASE_URL` pointing to the disposable DB: `.venv/Scripts/python.exe ..\features\FEAT-063-system-architecture-rearchitecture\evidence\rev34_legacy_route_smoke.py`.
- Dropped only the task-created test DB with `docker compose exec -T postgres psql -U sketch2life -d postgres -c "DROP DATABASE sketch2life_be1_acceptance WITH (FORCE);"` and verified that only `sketch2life` remained from the two checked DB names.

## Results

### Active legacy non-AI route smoke

- Smoke-tested all **77** active pre-Lesson-Library non-AI method/path operations in catalog rows 1–56 and 57–91, excluding the AI-dependent rows listed above.
- The smoke used unique synthetic path parameters and deliberately omitted credentials and valid mutation bodies. This checks route dispatch and safe rejection only; a 4xx is not a business-flow pass.
- Results: **77 HTTP responses, 0 HTTP 5xx** — 2 health routes returned 200, 52 protected routes returned 401, and 23 incomplete/invalid requests returned 422.
- Helper: `rev34_legacy_route_smoke.py`; per-route status matrix: `REV34_LEGACY_ROUTE_SMOKE_20261029.csv`.

### Existing HTTP/API suites

- Non-PostgreSQL API/contract batch: **109 passed, 1 failed** (110 collected). Suites covered demo sessions, health and app composition, deterministic whiteboard storyboard preview, validation-only P1 context requests, plus isolated candidate activity-assignment, learning-content and preset-governance route tests.
- PostgreSQL-backed BE1 API suite: **3 passed, 1 failed** (4 collected).
- JUnit results: `rev34-contract-junit.xml` and `rev34-be1-junit.xml`.

## Failures

1. `tests/integration/test_be1_postgres_api.py::test_room_code_start_revocation_stage_and_early_outcome_are_durable` expected the synthetic drawing operation to return 200, but received `409 CONSENT_NOT_EFFECTIVE`. This is the known BE1 consent-state defect: the database/ORM constraint allows only `pending` and `revoked`, while BE1 authorization requires `effective`. The successful consent-authorized state cannot currently be stored. The denial was preserved; no schema or policy change was attempted.
2. `tests/contract/test_app_composition.py::test_compatibility_app_preserves_baseline_route_surface` failed its exact route-difference assertion. Its expected delta allows only eight BE1 paths, while the combined app now also mounts the newer Lesson Library paths. Its earlier subset assertion passes; the failure is a stale route-baseline expectation, not an observed 5xx or missing old route. The 77-route smoke had no 5xx.

## Coverage limits and interpretation

- The 77-route smoke does not replace authenticated success-path tests. Deeper behavior coverage comes from the listed HTTP/API suites; not every non-AI legacy endpoint has an individual successful workflow test.
- Candidate/unmounted routes exercised by isolated tests are not production-mounted APIs. The 11 candidate/fixture declarations from Rev32 were not included in the active-route smoke.
- AI-dependent endpoints were deliberately not called. The Lesson Library result from Rev33 remains in EV-063-26 and was not rerun.
- API execution used FastAPI `TestClient`; this did not start a network-facing API container.

## Acceptance criteria disposition

| Criterion | Result |
|---|---|
| AC1 — classify old active, AI, and out-of-scope routes | Pass |
| AC2 — smoke all active old non-AI routes and run existing API suites | Pass; route smoke 77/77, suites have the two reported failures |
| AC3 — no AI calls, synthetic data, no persistent DB/secret changes | Pass |
| AC4 — report tests and coverage gaps accurately | Pass |
| AC5 — record API failures and consent/session gaps | Pass |
| AC6 — remove disposable database and preserve the application DB | Pass |

Rev34 is submitted for review with both test failures and the distinction between route smoke and business-flow coverage disclosed. No commit or push was performed.
