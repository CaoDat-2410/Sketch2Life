# EV-063-73 — Role-based authentication and Firebase account recovery

**Date:** 2026-11-10
**Plan:** Rev63 — `plan/PLAN_REV63_ROLE_BASED_AUTH_AND_ACCOUNT_RECOVERY_20261110.md`
**Latest approved Plan SHA-256:** `120FF1994CE81BD6D6A25BD37543B748D5EDDD26A35D57F18903C7E0559DA048`
**Lifecycle:** REVIEW — backend/database role flows and Firebase Identity Toolkit password lifecycle are runtime-verified; interactive app UI and signed-token role-gate acceptance remain outstanding.

## Implemented in source

- Added `account_id`, nullable server-managed `account_role`, and `role_revision` to the existing BE1 adult identity model, with an additive Alembic migration. Backfill maps only roles unambiguously evidenced by existing active BE1 assignments.
- Parent signup creates a Firebase email/password identity, persists `parent` in the backend, and does not accept a role from the client. `/api/auth/v1/me` resolves the role from the database.
- Teacher Web requires `teacher`; management Web routes require `school_manager` or `platform_admin` as appropriate. Organization-scoped BE1 requests reject missing/unsupported stored roles and assignment/role mismatches.
- Added Platform Admin account list/search/pagination, Firebase identity creation, role changes, account disable/re-enable, audit metadata, self-demotion/last-admin checks, and incompatible assignment revocation. Existing ambiguous legacy rows are shown with no role so Platform Admin can resolve them; access stays denied until a role is assigned.
- Admin account list reads email/display name from Firebase Auth only for an authorized Platform Admin. Neither field is written to PostgreSQL or audit entries. Admin Web requests Firebase to send the created account a password-reset email and shows a fallback instruction if that request fails.
- Added an explicit first Platform Admin bootstrap command configured with `SKETCH2LIFE_PLATFORM_ADMIN_BOOTSTRAP_EMAIL` in the one repository-root `.env`. No seed account, password, service-account JSON, token or provider secret is added to the repository.
- Compose passes the root bootstrap-email setting to the API container and no longer forwards the retired subject allowlist.
- Parent Android, Teacher Web and management Web include Firebase password reset and authenticated password change flows.

## End-to-end verification

All identities and data used for this run were synthetic. No child profile or media was created.

| Area | Result | Method and boundary |
|---|---|---|
| Database migration | **PASS** | Applied all Alembic heads, including `20261110_ar_0001`, to disposable PostgreSQL database `sketch2life_rev63_e2e`. The shared development database and its volumes were not used. |
| API health and runtime | **PASS** | Started an isolated API container against that database; `/health` returned HTTP 200 and Firebase Admin initialized for the configured development project. |
| Parent registration | **PASS** | Real HTTP request returned 201; Firebase Admin confirmed the synthetic identity. The new identity was deleted during cleanup. |
| Role lookup and authorization | **PASS with test seam** | `/me`, client role-injection rejection, Parent denial of Platform Admin routes, Teacher and School Manager role/access checks, and Parent denial of organization roster access passed. Authenticated role cases used an explicit `VerifiedPrincipal` dependency override, so Firebase signed-token verification was not exercised for these cases. |
| Platform Admin bootstrap/account lifecycle | **PASS** | Against disposable PostgreSQL and Firebase Admin: bootstrap, account listing, Teacher and School Manager creation, role change/revision, disable/re-enable synchronization, self-demotion rejection, and protection of the last active Platform Admin passed. |
| Firebase Web API key | **PASS after config correction** | The root `.env` key did not match the Web app config supplied by the owner, while project ID, auth domain and app ID matched. The key value was corrected locally. A non-mutating Identity Toolkit `accounts:createAuthUri` probe returned HTTP 200. |
| Firebase password lifecycle | **PASS at Identity Toolkit API level** | Created one `example.invalid` synthetic identity through Firebase Admin, generated a reset action link without sending email, completed reset with Identity Toolkit, signed in, changed the password, signed in again, and deleted the identity. No credential or action code was written to evidence. |
| HTTP invalid-token handling | **PASS after fix** | A live Uvicorn request with an invalid Bearer token now returns HTTP 401 with `INVALID_IDENTITY_TOKEN` and a generic message. This safe error mapping was added in `backend/src/sketch2life/interfaces/http/app.py` and documented in the API contract. |
| Frontend checks | **PASS** | Admin Web production build, Teacher Web production build and Parent mobile TypeScript check passed. Teacher Web reports an existing large-chunk warning (683.07 kB); builds/typecheck do not prove interactive UI behavior. |
| Interactive UI E2E | **NOT RUN** | No browser-based signup/login/reset/change flow was run. Firebase provider APIs now pass, but Admin/Teacher Firebase JS SDK screens and the Parent Android UI still need an interactive run. |

The main backend business-flow script completed in about **16.26 seconds**, excluding image pulls, migration setup and frontend builds. A first harness assertion parsed the generic conflict response at the wrong JSON nesting; the harness was corrected and rerun successfully. This was a test-harness issue, not an API failure.

## Environment issue and cleanup

- `docker compose up -d --build api` could not pull `quay.io/minio/minio:RELEASE.2025-10-15T17-29-55Z` (registry returned HTTP 401). To avoid depending on that image, the API and PostgreSQL were run as isolated disposable containers on the existing Compose network.
- The root `.env` initially contained a different `VITE_FIREBASE_API_KEY` from the owner-provided Web app config. It was updated locally to the supplied key; the non-mutating probe and synthetic Identity Toolkit password lifecycle then passed. No account was left behind and no email was sent.
- The existing `sketch2life-api-1` and `sketch2life-clamav-1` services were already running and were left untouched. Existing stopped PostgreSQL/Redis containers and their volumes were also left untouched.
- All Firebase identities created by the E2E run were removed; the main-flow cleanup reported 5 deleted and 0 failures. HTTP smoke identities were also verified removed.
- The disposable API and PostgreSQL containers were stopped/removed. A final container listing showed only the pre-existing API and ClamAV services running.
- The repository-root `.env` still lacks the Platform Admin bootstrap email. No real account was bootstrapped or left behind. No secret, API key, password, token, or action link is recorded here.
- No commit or push was made.

## Remaining acceptance gaps

- Run interactive Admin/Teacher Web and Parent Android login/reset/change flows after restarting their dev servers so they load the corrected root `.env`. No browser UI was exercised in this run.
- Configure a reserved synthetic bootstrap email in the root `.env` before verifying the operator bootstrap command through the normal Compose service.
- Once the MinIO image pull is available, rerun through the full Compose stack and run browser/UI flows; the present acceptance pass used isolated API/PostgreSQL containers.
- Parent registration assigns an active Parent role before email verification. UC-13 email-verification activation and production delivery remain unimplemented. The registration limiter is process-local; production needs shared edge/API throttling.
- FEAT-063 SRS §31.10(14) remains open. This evidence does not claim full permission-resolver sign-off or production readiness.

## Primary artifacts

- API contract: `artifacts/AUTH_ROLE_API_CONTRACT_REV63_20261110.md`
- Schema register: `artifacts/DATA_TABLE_REGISTER.md`
- Plan and path manifest: `plan/PLAN_REV63_ROLE_BASED_AUTH_AND_ACCOUNT_RECOVERY_20261110.md`
- Approval: `approvals/TASK_APPROVAL.md`
