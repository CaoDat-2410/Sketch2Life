# FEAT-066 EV-047 — School Manager API/UI crosswalk (Rev39)

- Date: 2026-11-17.
- Type: static source/API crosswalk; planning evidence only.
- Owner request: finish checking remaining Admin APIs and prepare the transition to School Manager when no more SRS-ready Admin feature API remains.
- Plan: `features/FEAT-066-fe-ui-srs-full-review/plan/PLAN_REV39_SCHOOL_MANAGER_API_UI_CROSSWALK_20261117.md` (SHA-256 `589D260604CE8DECBC54F8A88AE0F6749D3446CBA0155738B3FF3C3528E9C05F`).
- Canonical working requirements: FEAT-063 `SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`, v2.7-draft Rev60, unsigned; authority routed by `docs/context/SRS_AUTHORITY.md`.
- API baseline: `origin/dev` commit `1c9148e88600a101887e477541c4c4893ba1c7df`.
- Web baseline inspected: `codex/fe-ui-web-remediation` at `b72f9e46`. The worktree already contained local Rev36–Rev38 Admin and FEAT-066 changes; they were preserved. This revision changes documentation only.

## Admin result

- Already wired: `GET /api/platform-admin/v1/accounts`, `POST /api/platform-admin/v1/accounts`, `PATCH /api/platform-admin/v1/accounts/{account_id}`; shared `GET /health` is used only as an API health probe.
- Backend/client-only candidate: `PATCH /api/lesson-library/v1/platform/lessons/{lesson_id}/moderation`, with typed `moderateLesson` FE method. No platform moderation queue/list or exact immutable-version read was found. The route checks the `platform_admin` role but not the SRS Content Admin permission. The Admin page correctly keeps this flow blocked. No guessed ID/revision was submitted.
- Conclusion: no additional complete, SRS-ready Admin feature API can be integrated before Manager planning. The moderation command remains a backend/authorization follow-up.

## Manager result

Already wired in `origin/dev` web:

- Resolve active assignment with `GET /api/be1/v1/organizations/{organization_id}/me`.
- List/create classes via `GET` and `POST /api/be1/v1/organizations/{organization_id}/classes`.
- Load pending PUBLIC grants with cursor pagination from `GET /api/lesson-library/v1/organizations/{organization_id}/access-grants`.
- Read lesson details through `GET /api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}`; UI compares `current_version.version_id` with grant `version_id` and blocks mismatches.
- Decide grant using `POST /api/lesson-library/v1/organizations/{organization_id}/access-grants/{access_grant_id}/decision`, with revision/idempotency handling and reason for request-changes.

Available BE routes with no Manager UI wiring found in the reviewed module include class-teacher assignment (`POST /api/be1/v1/classes/{class_id}/assignments`), class profile/consent operations, and organization parent-group/invitation operations. No organization-scoped Teacher candidate-list route was found, so the assignment picker needs a read contract. The current mounted routers did not expose School Manager quota/billing/invoice/reconciliation or organization feedback-thread read/reply contracts. A supervised-flow feedback command is a different workflow and is not treated as Manager feedback support.

SRS boundaries carried into the plan: one assigned organization only; teacher lesson public approval must match the exact version in the grant; child media/story remains denied by default; quota-purchase/allocation stays open under Q193.

## Review limits

Static source inspection only. No live API request, authenticated mutation, browser session, test suite, production build, commit, or push. This evidence does not imply product SRS sign-off or implementation approval.
