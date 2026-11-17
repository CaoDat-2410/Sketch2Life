# Plan Rev34 — legacy non-AI API regression run

- Feature: FEAT-063 — whole-repository architecture redesign.
- Status: APPROVED for the exact test-only scope below by the project owner's direct instruction on 2026-10-29.
- Authority: owner requested rerunning all old APIs except those requiring AI and listing failures.

## Goal

Run the repository's existing HTTP/API regression coverage for legacy API surfaces, without calling AI-dependent endpoints or providers. Report which routes/suites passed, failed, were excluded, or lack executable coverage.

## Scope definition

- “Old APIs” means the pre-Lesson-Library surfaces in the Rev32 catalog: BE1/classroom routes (catalog rows 1–56) and Demo/local-flow routes (rows 57–91).
- The newly added Lesson Library routes (rows 92–121), conditional storage example (rows 122–124), framework docs endpoints, and candidate/fixture/unmounted declarations (rows 125–135) are outside this legacy regression run. Lesson Library coverage from Rev33 remains separately recorded in EV-063-26.
- Run existing non-AI HTTP/API test suites for the old surfaces, including the PostgreSQL-backed BE1 suite, local ephemeral-session API, health/route composition, and deterministic storyboard preview. Run only validation-only cases from mixed demo API tests when they do not call image/audio/understanding/classifier/ranker/video endpoints.
- Exclude calls to preference classification; audio/image ingestion or understanding; AI/P1 ranking; generated story/whiteboard video; AI-dependent renderer planning; AI job/policy/assistance endpoints; and any provider/Modal/GPU path. Do not use real child data.
- In addition to existing behavior tests, make one safe route-dispatch smoke request to every active old non-AI method/path in catalog rows 1–56 and 57–91, excluding AI-dependent rows 57–61, 64–67, 82, 87, and 89–91. Use unique synthetic path values, omit authentication and required mutation bodies, and do not send valid write commands. Expected auth/validation/not-found responses are recorded as smoke responses, not behavior passes; any 5xx is investigated and reported.
- Existing tests for candidate/unmounted routes may be run only as isolated contract tests where they do not invoke AI; report them separately from active production API coverage.

## Execution controls

1. Review the Rev31 inventory, Rev32 purpose catalog, current FEAT-063 context/status, test files, and router composition before testing.
2. Use only synthetic identities/content. Run PostgreSQL-backed tests against a disposable local database whose name contains `be1_acceptance`; do not write fixtures to the persistent `sketch2life` database.
3. Do not apply new migrations to the persistent application database. The existing local DB is already at the Rev33 target; migrate only the disposable test DB if the suite requires it.
4. Run test modules individually or in a bounded batch so every failure is attributable. Do not change product code or test expectations during this diagnostic run; record defects for follow-up.
5. Use a route-dispatch smoke with unauthenticated/invalid requests only; ensure no state-changing command can pass authorization or schema validation.
6. Drop only the disposable test database created for this run. Keep PostgreSQL's named volume and the application database intact.
7. Record commands/results, active-route coverage, exclusions, failures, environment, and cleanup in EV-063-27; update FEAT-063 context/status/source registers.

## Acceptance criteria

- AC1: The pre-existing active legacy API surfaces are reconciled against the Rev32 catalog, with AI-dependent and out-of-scope routes identified.
- AC2: Every active old non-AI method/path receives a safe route-dispatch smoke request, and every existing non-AI HTTP/API test suite selected for BE1/classroom and Demo/local-flow is run; PostgreSQL-backed tests use only the disposable acceptance DB.
- AC3: No AI-related API/provider/Modal/GPU call is made. Synthetic data only; no `.env`, remote-service, or persistent application-DB changes.
- AC4: Each test suite and smoke route is reported as passed, failed, blocked, or excluded. Missing endpoint-level behavioral coverage is listed explicitly; route-dispatch smoke and route-exposure checks are not presented as behavior tests.
- AC5: The BE1/classroom and Demo/local-flow legacy consent/session gaps and any newly discovered API failures are recorded with the failing test/route and observed result.
- AC6: The disposable DB is removed; the persistent application DB and PostgreSQL volume remain intact.

## Explicitly excluded

AI-related API calls/tests, AI model/provider/Modal/GPU execution, Lesson Library re-test, real MinIO/API network deployment, AWS/Firebase calls, persistent/remote database writes, real child data, product-code or test-expectation fixes, deployment, commit, and push.
