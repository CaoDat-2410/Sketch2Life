# Local API runtime availability smoke — 2026-11-03

## Status and authorization

- Status: APPROVED for read-only API availability and route-discovery requests.
- Feature: FEAT-063; the canonical product contract remains the current SRS v2.3-draft.
- Owner authorization: direct instruction in this chat to run the APIs after asking whether requests had been tested.
- Scope is restricted to the already-running local API: GET `/health`, GET `/openapi.json`, and a read-only GET probe of `/v1/story-runs/synthetic-smoke`; inspect only non-secret AI/provider configuration presence.

## Acceptance criteria

1. Record HTTP status and bounded response summary for each GET.
2. Determine whether the live OpenAPI exposes StoryRun or an HTTP route to the newly deployed Modal workers.
3. Do not send POST/PUT/PATCH/DELETE requests, trigger provider inference, alter databases, restart containers, add an endpoint, or change backend/Modal integration.
4. If the current API cannot dispatch to the new workers, record the exact runtime/configuration gap and stop this smoke task without claiming model API integration passed.

## Risks and limits

- The owner asked to run APIs but this plan does not authorize creating or wiring a new route. HTTP route discovery may show the service is stale or AI is disabled; in that case the backend-to-new-worker request remains untested.
- No credentials or configuration values are to be read or recorded. Only whether relevant values are set may be noted.
- No code, database, Docker lifecycle, Modal deployment, or model call is changed by this smoke.
