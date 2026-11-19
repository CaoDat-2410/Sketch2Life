# FEAT-066 — Enable the active FE port to reach the local API

- Plan revision: 35
- Status: APPROVED_FOR_EXECUTION
- Date: 2026-11-17
- Scope: temporary loopback Vite runtime configuration only

## Owner request

The owner showed the backend-data error on `http://127.0.0.1:5173/login?role=admin` and asked: “là chưa ghép à ?”. The earlier same-origin proxy was on port 5174, while the active 5173 Vite process had no API proxy.

## Exact scope

1. Replace the port 5173 Vite process only after verifying its command belongs to the active `fe-ui-web-remediation` worktree.
2. Start that same FE on `127.0.0.1:5173` with a temporary ignored config that proxies `/health` and `/api` to the local Docker API on port 8000.
3. Load the verified `sketch2life-dev` Firebase web configuration from the ignored main-checkout `.env` into the Vite process environment only; do not print or persist values.
4. Keep port 5174 available as a fallback; make no tracked source, backend, account, environment-file, or credential changes.
5. Verify FE login HTTP 200, proxied health HTTP 200, same-origin API base and protected unauthenticated route status; do not submit or store credentials/tokens.

## Acceptance criteria

- AC1: Port 5173 is served by this worktree and injects the same dev Firebase project as port 5174.
- AC2: The FE API base points to port 5173 and `/health` proxies to the healthy Docker API with HTTP 200.
- AC3: Existing login route loads without the browser cross-origin failure; no account/password/token is submitted by this check.
- AC4: Port 5174 remains available, backend and local test account are unchanged, and no tracked code is modified.
- AC5: Keep the runtime config under Git-ignored `tmp/`; no commit or push.