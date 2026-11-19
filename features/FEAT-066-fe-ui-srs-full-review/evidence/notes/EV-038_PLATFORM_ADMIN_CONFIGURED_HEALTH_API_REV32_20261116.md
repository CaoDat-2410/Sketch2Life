# FEAT-066-EV-038 — Platform Admin configured health API integration

- Date: 2026-11-16
- Plan: plan/PLAN_REV32_PLATFORM_ADMIN_AVAILABLE_API_INTEGRATION_20261116.md
- Plan SHA-256: 56A6985B7D486E79F1B8C9AB39B4C56275BC401C7ECF4730014D01BC167A1A92
- Owner approval: approvals/TASK_APPROVAL.md, FEAT-066 Rev32.
- Requirements: canonical FEAT-063 v2.7-draft Rev60, unsigned.
- API source: origin/dev 1c9148e88600a101887e477541c4c4893ba1c7df.
- UI source: codex/fe-ui-web-remediation, starting HEAD b72f9e46f9c63e019807d7c4a2c309b0aa46a133.

## Work completed

- Platform Admin overview Health panel now calls the existing typed GET /health using the API base resolved by runtimeConfig/apiBaseUrl; the former loopback-only condition was removed.
- The panel remains behind the authenticated Platform Admin app route. If the Firebase auth bridge is unavailable, it stays blocked without issuing a request.
- Loading, successful API response, connection error and manual retry states remain visible and accessible. The heading/status copy identifies this as an API probe and does not claim queue, billing, database, provider or whole-platform health. The configured host is not displayed.
- Confirmed the existing shared GET /api/auth/v1/me role resolution and GET/POST/PATCH /api/platform-admin/v1/accounts page integration remain in place; no account mutation behavior was changed.
- Lesson moderation remains blocked because the API lacks a queue/exact-version read path and the command guard does not resolve the SRS Content Admin permission.

## Limits and validation

- Static source review only. No live health/account/moderation API request, credentials, account data or provider call was made.
- No app tests or build were run.
- git diff --check and direct whitespace scan results are recorded in the Rev32 status entry.
- No backend, API contract, authorization, environment, secret, generated asset, mobile, other-role, commit or push change was made.