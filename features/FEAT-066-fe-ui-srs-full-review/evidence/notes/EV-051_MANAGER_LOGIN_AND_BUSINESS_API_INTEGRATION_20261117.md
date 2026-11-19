# FEAT-066 EV-051 — Manager QA login and business API integration

- Date: 2026-11-17.
- Plans: Rev42 `plan/PLAN_REV42_MANAGER_QA_ACCOUNT_AND_LIVE_LOGIN_20261117.md` (SHA-256 `96AE1FC25F8BAE840371D9CB41D5F52652F74C1F59C0F6D2A6AD22F5848C9D6D`); Rev43 `plan/PLAN_REV43_MANAGER_BUSINESS_API_INTEGRATION_20261117.md` (SHA-256 `239A1E64E5C3269A7536497DB5DDAA2A582EC7844E25468837A9F1B3286AA597`); Rev44 `plan/PLAN_REV44_MANAGER_QA_BOOTSTRAP_ORDERING_FIX_20261117.md` (SHA-256 `31E7CD3445AE6290387F118F9B761DF14397D7C0BB6BD03C366624A2604E38D9`).
- Approval: Rev42 and Rev44 are approved for execution; Rev43's owner-approved login gate was fulfilled before its implementation.
- Worktree: `codex/fe-ui-web-remediation`; no commit or push.
- SRS: repository authority remains FEAT-063 v2.7-draft Rev60 via `docs/context/SRS_AUTHORITY.md`; unsigned.

## Manager QA account and authentication

- The owner-provided, Git-ignored root `.env` contained Firebase Web config for `sketch2life-dev`; no config value is recorded here.
- The supported bootstrap initially failed with PostgreSQL `be1_organization_assignments_organization_id_fkey`. The transaction rolled back and each temporary Firebase identity was deleted. Rev44 adds an explicit flush of the organization and adult identity before the assignment insert.
- `backend/tests/unit/test_be1_bootstrap.py`: 1 passed in the Docker API container using a temporary pytest install; the test verifies parent flush precedes assignment insertion. The API image was rebuilt from the worktree, and Docker health returned 200.
- Final reserved-domain QA identity: Firebase password sign-in succeeded and its subject matched the bootstrapped Manager identity. Authenticated `GET /api/auth/v1/me` returned 200 with role `school_manager`. Authenticated `GET /api/be1/v1/organizations/{organization_id}/me` returned 200 with organization-wide `school_admin` (`class_id: null`).
- No existing Platform Admin, unrelated organization, child data, email delivery or business row was changed. One dedicated QA organization and one Manager assignment remain for owner testing. The email/password are intentionally absent from this evidence and are provided only in the owner response.

## Rev43 frontend integration

Connected:

1. `GET /api/be1/v1/organizations/{organization_id}` — organization name and ID on Manager overview.
2. `GET /api/be1/v1/organizations/{organization_id}/classes/{class_id}/profiles` — minimal display name and age only, after class selection; opaque child IDs are not rendered.
3. `GET /api/be1/v1/organizations/{organization_id}/classes/{class_id}/consents` — read-only status and effective flag, independently loaded from roster.
4. `GET /api/lesson-library/v1/organizations/{organization_id}/parent-groups` — cursor pagination.
5. `POST /api/lesson-library/v1/organizations/{organization_id}/parent-groups` — explicit submit with an Idempotency-Key and same-key retry for uncertain outcomes.

The Manager UI now has organization details, a class-scoped Roster & consent page, and Parent groups. Class creation displays an unavailable state because its API does not enforce SRS FR-T-03 capacity. Teacher assignment, Parent invitation, membership revoke, consent writes, class assignment, capacity, billing, quota and feedback stay unavailable under the Rev43 route contract review.

## Verification and limits

- Live authenticated GETs on the QA organization: organization 200, classes 200 with 0 items, Parent groups 200 with 0 items.
- Profile and consent GETs were not called live because the QA organization has no class; no class, child, consent, group or membership was seeded. Parent-group POST and class POST were not sent.
- FE dev server is available at `http://127.0.0.1:5173/login?role=manager`; login route, parent-group SPA route, roster/group modules and proxied `/health` each returned 200. The server uses the ignored root config and process-only organization ID.
- No browser automation tool was available for a full interactive Firebase SDK login. Firebase password sign-in and both backend authorization reads were verified live; existing FE auth-flow coverage passed, and the user can complete the interactive check in the running FE.
- Focused FE tests: 18 passed across Manager gate, business API adapter/pages and login flow. Production TypeScript/Vite build passed. Targeted Oxlint exited 0 with existing warnings in `WebAppShell.tsx`; changed Manager files had no lint findings. `git diff --check` passed; Git printed line-ending normalization warnings only.
- No credentials, Firebase ID token, API key, child data, screenshot, commit or push is included.
