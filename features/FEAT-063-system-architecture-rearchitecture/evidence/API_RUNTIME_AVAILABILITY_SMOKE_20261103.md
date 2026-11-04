# Local API runtime availability smoke — 2026-11-03

## Scope

- Approved plan: `plan/API_RUNTIME_AVAILABILITY_SMOKE_20261103.md`.
- Read-only requests to the existing local Docker API on `127.0.0.1:8000`; no mutation request or provider inference was sent.
- Container inventory showed `sketch2life-api` started on 2026-10-30 and has no source bind mount. Only non-secret configuration presence was checked.

## Results

| Request/check | Result |
|---|---|
| `GET /health` | HTTP 200; `{"status":"ok","service":"sketch2life-api"}` |
| `GET /openapi.json` | HTTP 200; title `Sketch2Life API`, version `1.0.0` |
| `GET /v1/story-runs/synthetic-smoke` | HTTP 404 `Not Found` |
| `SKETCH2LIFE_AI_PROVIDER` in the running container | Unset |
| StoryRun Modal base URL/token presence | Both unset; token value was not read |

The live OpenAPI exposes existing session story-video/whiteboard routes and Lesson Library revision lookup, but no `/v1/story-runs` API and no HTTP route for the newly deployed Qwen, TTS/ASR, FLUX, or Wan Modal workers. The four new apps are private Modal function apps without web endpoints; their previous synthetic calls were made through the Modal function runner, not through this backend API.

## Conclusion

The live local API is healthy, but **an API request from this running backend to the new Modal workers was not run**: the active container is an older image, AI provider configuration is absent, and the required routes/dispatch integration are not present in its OpenAPI. No POST was sent because it could not reach those workers. This smoke does not alter the approved Modal hosting-wave scope, which excludes backend/API integration.

Separate earlier evidence records one successful synthetic StoryRun request through the main backend to a temporary older Modal Vision app; that temporary app was stopped after the run and does not prove integration with the new worker apps: `STORYRUN_LITE_MAIN_BE_INTEGRATION_20261103.md`.
