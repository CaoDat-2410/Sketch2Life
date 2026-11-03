# Bruno collection: full BE API surface

This is a separate contract inventory for the current backend. It contains one Bruno request for each operation in the union of the combined, classroom, demo, opt-in StoryRun-lite, and optional local-storage profiles. The existing StoryRun-lite demo collection under `artifacts/storyrun-lite/bruno/` remains the guided synthetic flow and is unchanged by this task.

## Inventory

| Runtime configuration | Operations |
| --- | ---: |
| Combined default | 122 |
| Combined + StoryRun-lite main demo flag | 133 |
| Combined + local storage example flag | 125 |
| Combined with both optional groups enabled | 136 |
| Classroom profile | 57 |
| Demo profile | 35 |

The full runtime schema contains **136 operations across 122 paths** and maps one-to-one to **136 Bruno requests**. The coverage CSV also lists 11 historical candidate/fixture declarations as `unmounted-candidate`; those rows have no request file and are not included in the active count.

`API_INVENTORY_FEAT063_REV31_20261028.md` recorded 135 declarations: 124 entries in the static mounted catalog (121 unconditional plus three local storage examples) and 11 unmounted candidates. The current runtime has 122 default combined operations, one more than the historical unconditional count. The additional current route is `GET /api/be1/v1/organizations/{organization_id}/sessions/{session_id}/pilot-profiles`; it is mounted in the current runtime but absent from the Rev31 static catalog. StoryRun-lite contributes 11 opt-in operations, and the same three storage examples remain local-only and opt-in. That reconciles the current union to 136 without counting the 11 unmounted candidates.

The schema is generated from `application.state.runtime_openapi_schema`, not the public FE/SRS `/openapi.json` projection. The export retains operation/parameter/body/response schemas and removes optional example payloads. Request bodies are starter templates made from required schema fields; `REPLACE_ME` and `REPLACE_WITH_*` values are placeholders, not contract-valid test records.

The guided-session create/read pair is process-local and synthetic. Its request bodies and headers use the `request_id`, `idempotency_key`, `session_id`, and `demo_actor_ref` local variables. For this local demo only, set `demo_actor_ref` to the fixed marker `demo:local`; use a fresh UUIDv4 for `session_id`. This is not a real user identity and creates no database record; the session disappears when the API process exits.

## Open in Bruno

1. In Bruno, choose **Open Collection** and select this folder: `artifacts/be-full/bruno/`.
2. Select the `local` environment. Its base URL is `http://127.0.0.1:8000`; the bearer token and all IDs are placeholders.
3. Replace placeholders only with synthetic values from a disposable local/test setup. This collection does not create accounts, seed records, or provision a database.

Do not use Bruno's **Run Collection** action against a persistent database. Many requests create, update, cancel, upload, or delete state. Requests are visibly labeled `STATE CHANGE`, `POST/ACTION`, `QUERY-STYLE POST`, or `PROVIDER-CAPABLE`; check the corresponding handler and data prerequisites before sending one. A valid bearer token is not included. Protected operations need an independently configured local/test identity. Multipart requests need a synthetic file with the correct type and size at the request's relative placeholder path.

The `PROVIDER-CAPABLE` label is a warning, not a run configuration. The collection has no Modal/provider URL or credentials. Do not run those requests for this inventory task. No BE server, database, Modal app, GPU or provider was started or called while generating these artifacts.

## Files

- `openapi.runtime.json` — combined runtime schema with both optional local groups enabled for inventory.
- `API_COVERAGE.csv` — method/path-to-request matrix, profile exposure, auth/body/header prerequisites, response status contract, and side-effect classification.
- `bruno/` — independent full-BE Bruno collection and loopback-only `local` environment.
- Generation and validation helper scripts are retained locally and intentionally excluded from the requested collection commit; the checked-in Bruno artifacts are complete and importable.


## Validation status

The local validator verifies all 136 method/path pairs, request files, profile counts, loopback-only request URLs, placeholder auth, and that every environment value except the loopback `baseUrl` is an explicit `REPLACE_WITH_*` placeholder. It also checks exclusion of the 11 unmounted candidates. Bruno CLI 4.3.0 successfully parsed all requests and generated documentation for all environments with `bru docs generate --all-envs --no-git-link`; every one of the 136 request names appeared in the generated output. The CLI has no separate list command, and the connected Bruno MCP currently exposes only the existing StoryRun-lite collection, so its request-list operation cannot inspect this new path. A limited safe loopback smoke passed 3/3: `GET /health` 200, process-local synthetic `POST /v1/sessions` 201, and `GET /v1/sessions/{session_id}` 200. The API ran on loopback with AI provider disabled, StoryRun-lite database-backed routes disabled, and no database URL; its in-memory session disappeared when the temporary server stopped. Bruno reported 0 request tests and 0 assertions, so the three HTTP statuses were checked directly from CLI/server output. No DB-backed BE1/Lesson Library route or StoryRun-lite flow was exercised.
