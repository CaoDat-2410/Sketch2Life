# FEAT-066-EV-041 — Active FE port API proxy

- Date: 2026-11-17
- Plan: plan/PLAN_REV35_ACTIVE_FE_PORT_API_PROXY_20261117.md
- Plan SHA-256: 479A937FDDDD09AD6CC681B5D951C7D434B9ACAD29B3ECBB4918EC3225B9E200
- Owner approval: approvals/TASK_APPROVAL.md, FEAT-066 Rev35.

## Finding and correction

The screenshot was on port 5173. That port was served by Vite from the active worktree but had no same-origin proxy; the backend returns no CORS header. The prior runtime workaround and Firebase config were on port 5174. Replaced only the verified worktree's Vite process on 5173 with an equivalent temporary ignored proxy config at `tmp/vite-api-proxy-5173.config.ts`, set the FE API base to its own origin, and injected the existing dev Firebase web settings into that process environment. Port 5174 remains available; no tracked source changed.

## Verification

- `GET /login?role=admin` at port 5173: HTTP 200.
- Same-origin `GET /health` through Vite proxy at port 5173: HTTP 200, `{"status":"ok","service":"sketch2life-api"}`.
- Unauthenticated same-origin `GET /api/auth/v1/me`: HTTP 401, showing the request reaches the protected API path.
- The transformed FE auth module contains project `sketch2life-dev`; the backend API module uses `http://127.0.0.1:5173`.
- Port 5174 remains available and API/account services were not changed.

No credentials or tokens were submitted in this port correction. The Platform Admin test account and authenticated API verification remain as recorded in EV-040. No app tests, source changes, commit or push.