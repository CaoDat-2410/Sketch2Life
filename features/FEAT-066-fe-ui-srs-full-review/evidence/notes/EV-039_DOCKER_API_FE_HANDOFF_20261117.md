# FEAT-066-EV-039 — Docker API verification and FE handoff

- Date: 2026-11-17
- Plan: plan/PLAN_REV33_DOCKER_API_FE_SMOKE_20261117.md
- Plan SHA-256: 0AB2F79A26EDCBA27871C559016A8A6A56466DA82867519E2FB147995C8380F0
- Owner approval: approvals/TASK_APPROVAL.md, FEAT-066 Rev33.
- Worktree: `codex/fe-ui-web-remediation`; no commit or push.

## Runtime setup

- Docker Desktop 29.9.3 was started. Existing PostgreSQL container restarted against its existing volume (not reset) and reached `healthy`.
- Full `docker compose up -d --build api` could not pull the configured MinIO image from `quay.io` (HTTP 401); the subsequent Python API build also revealed the ignored `packages/art-renderer/dist-demo` artifact was absent.
- The repository-pinned offline renderer dependency install stopped on pnpm's supply-chain policy check because mirror metadata for `@0no-co/graphql.web` was unavailable. No policy was bypassed and no frontend dependency was downloaded.
- Built the backend image locally from the repository Dockerfile instructions, omitting only the optional renderer static-bundle copy, then started the API with Compose `--no-deps` against PostgreSQL. API container reports `healthy`.
- Running services: API at `http://127.0.0.1:8000`, PostgreSQL at `5432`; MinIO, ClamAV, and Redis are not running. Renderer static demo is not mounted. Admin health/account reads do not require those omitted services; their dependent features are not verified.

## Read-only API results

- `GET /health` -> HTTP 200, `{"status":"ok","service":"sketch2life-api"}`.
- `GET /openapi.json` -> HTTP 200. The default FE-projected document omits `/api/auth/v1/me` and `/api/platform-admin/v1/accounts`; source registration is present in `mount_classroom_routers`, with route decorators in `auth_registration.py` and `platform_admin_accounts.py`.
- Unauthenticated `GET /api/auth/v1/me` -> HTTP 401.
- Unauthenticated `GET /api/platform-admin/v1/accounts` -> HTTP 401.
- These 401 responses confirm the protected read paths are reached without disclosing account data. No Firebase token was available or submitted; account data was not verified. POST/PATCH mutations were not called.

## FE handoff

- Existing FE at `http://127.0.0.1:5173/login` remains reachable (HTTP 200) and was left untouched.
- Direct API health response has no `Access-Control-Allow-Origin` for the FE origin. To make same-origin browser requests possible without editing tracked source, a second Vite process was started on loopback `http://127.0.0.1:5174/login`, using ignored `tmp/vite-api-proxy.config.ts` and proxies for `/health` and `/api` to port 8000. Its bundle resolves `VITE_SKETCH2LIFE_API_BASE_URL` to its own origin.
- Proxy checks: `/login` -> HTTP 200; `/health` -> HTTP 200 with the API health body; unauthenticated `/api/auth/v1/me` and `/api/platform-admin/v1/accounts` -> HTTP 401.
- Use port 5174 for FE/API testing. A real authorized Firebase session and matching backend identity configuration are still required to test authenticated account data. No credentials or account mutations were used.

No application tests or frontend production build were run. The Docker image build was necessary to start the backend. The only runtime support file is under Git-ignored `tmp/`; no tracked application code/config was changed during this verification.