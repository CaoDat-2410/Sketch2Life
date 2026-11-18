# FEAT-081 Parent Mobile Read-Route Bruno Checks

## Scope

Added four read-only Bruno requests under `artifacts/be-full/bruno/requests/parent-mobile-read-routes/` for the FEAT-081 route alignment:

| Request | Method and path |
|---|---|
| 137 | `GET /v1/parent/profiles` |
| 138 | `GET /v1/parent/profiles/{profile_id}` |
| 139 | `GET /v1/story-runs/active/current` — backend source marks this route `[PROPOSAL]` |
| 140 | `GET /v1/story-runs/{run_id}` |

Each request includes bearer auth from the placeholder-only `local` environment and response assertions based on the current BE router/schema source. Added `parent_profile_id` and `parent_story_run_id` as UUID placeholders; no real credential or profile/run ID was stored. The four requests are supplemental and are not counted in the existing 136-operation `openapi.runtime.json` / `API_COVERAGE.csv` snapshot. The collection README now records this limitation.

## Runtime check

At 2026-11-15 17:11:08–17:11:11 +07, four GETs were sent to the local loopback API without an Authorization header. `curl.exe` discarded each response body and returned:

| Method and path | HTTP status |
|---|---:|
| `GET /v1/parent/profiles` | 401 |
| `GET /v1/parent/profiles/00000000-0000-4000-8000-000000000002` | 401 |
| `GET /v1/story-runs/active/current` | 401 |
| `GET /v1/story-runs/00000000-0000-4000-8000-000000000004` | 401 |

These status-only probes reached the authentication boundary without returning profile or StoryRun data. They are consistent with the routes being recognized and requiring authentication; they do **not** verify successful authorization, response-body assertions, ownership, or data presence. Separate earlier Docker logs in the FEAT-081 API implementation report recorded authenticated `200` responses for the profile list and active-run route, but did not capture response bodies.

## Bruno execution limitation

The connected Bruno MCP lists only `artifacts/storyrun-lite/bruno`; it reports no Bruno collection at `artifacts/be-full/bruno`. The `be-full/bruno/environments/local.bru` bearer token remains `REPLACE_WITH_LOCAL_TEST_BEARER_TOKEN`, and no valid disposable Parent token or profile/run IDs were provided. PowerShell command discovery did not find a local `bru` executable. Therefore the four Bruno test scripts were created but **not parsed or executed by Bruno**. No install was attempted. Authenticated contract execution remains pending access to this collection plus a disposable local/test Parent identity and existing synthetic profile/run IDs.

No database was queried, no API mutation was issued, and no backend source, SRS, or approval record was changed.
