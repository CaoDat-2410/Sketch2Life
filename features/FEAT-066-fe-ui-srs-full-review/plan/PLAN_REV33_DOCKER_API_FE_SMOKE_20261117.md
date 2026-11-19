# FEAT-066 — Local Docker API and FE handoff check

- Plan revision: 33
- Status: APPROVED_FOR_EXECUTION
- Date: 2026-11-17
- Scope: local runtime verification only; no application source changes

## Owner request

The owner directly requested: “chạy BE ở docker sau đó chạy thử api xem đã nhận chưa sau đó để tôi test trên FE”.

## Exact scope

1. Start the repository's Docker Compose API service and its declared dependencies using local compose defaults; do not reset or remove volumes.
2. Verify the API with read-only requests only: `GET /health`, `GET /openapi.json`, unauthenticated `GET /api/auth/v1/me`, and unauthenticated `GET /api/platform-admin/v1/accounts`. Record expected status codes without tokens or account data.
3. Verify browser-origin access to `GET /health` from `http://127.0.0.1:5173` using the `Origin` header; do not submit credentials.
4. Confirm the existing FE dev server remains reachable at `http://127.0.0.1:5173` and leave it running with the API for owner testing.
5. Do not create/update/delete accounts, use real or fabricated auth tokens, run app tests/builds, alter code/contracts/env/secrets, or commit/push.

## Acceptance criteria

- AC1: Docker engine is running and Compose API plus required dependencies reach healthy/started states.
- AC2: `GET /health` returns a successful response from the containerized API.
- AC3: OpenAPI confirms the role/account paths are mounted; unauthenticated auth/account reads return the documented auth rejection without exposing data.
- AC4: A request with the FE origin receives the expected CORS permission for `GET /health`.
- AC5: FE remains reachable at port 5173 and the API remains running for the owner to test.
- AC6: Only read-only probes are issued; no credentials or business data are sent or printed.
- AC7: Record runtime results in FEAT-066 evidence/status; no app tests/builds, source changes, commit or push.

## Runtime boundary

The approved API probe is not proof of authenticated Platform Admin account behavior. A real authorized Firebase session is required for the account page. No authentication bypass or seeded account is authorized by this plan.
## Build prerequisite amendment

The first API image build stopped because the Dockerfile's required `packages/art-renderer/dist-demo` directory is absent. The owner request to run the backend includes permission for this narrow prerequisite only: use the repository package's `build:demo` script to produce the Git-ignored artifact. If dependencies must be linked, allow only an offline frozen-lockfile install for `@sketch2life/art-renderer`; do not fetch dependencies over the network. Do not modify tracked source. The renderer demo is synthetic package output, not a new product visual. If offline dependencies are unavailable, stop and report the blocker.
## Local API-only image fallback

The package manager's offline install stopped on its configured supply-chain policy check because package mirror metadata is missing. Do not bypass that policy or fetch packages. To continue the requested Admin API verification, allow an ephemeral Dockerfile streamed to `docker build -f -` that mirrors `backend/Dockerfile` but omits only the optional `packages/art-renderer/dist-demo` copy. Run the API with the existing Compose environment and healthy PostgreSQL, using `--no-deps`; do not claim the renderer, MinIO, or ClamAV features are running. Do not write a Dockerfile or source change into the worktree. The API probes remain read-only.
## FE browser handoff adjustment

Runtime inspection showed the API does not emit `Access-Control-Allow-Origin` and the standard Vite config has no proxy. Keep the existing FE server on port 5173 untouched; allow a second temporary Vite server on loopback port 5174 using a config under ignored `tmp/`, `VITE_SKETCH2LIFE_API_BASE_URL=http://127.0.0.1:5174`, and same-origin proxies for `/health` and `/api` to the API on port 8000. Verify `/login` and proxied `GET /health`, then leave the FE server running for the owner. The public `/openapi.json` is SRS-projected and omits these two route families; use the router declarations and unauthenticated 401 responses to record that protected routes are mounted. No bypass or credentials are allowed.