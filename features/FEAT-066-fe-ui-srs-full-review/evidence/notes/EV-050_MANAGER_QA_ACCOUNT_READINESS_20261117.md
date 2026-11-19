# FEAT-066 EV-050 — School Manager QA account readiness (Rev42/43)

- Date: 2026-11-17.
- Plans: Rev42 `plan/PLAN_REV42_MANAGER_QA_ACCOUNT_AND_LIVE_LOGIN_20261117.md` (SHA-256 `96AE1FC25F8BAE840371D9CB41D5F52652F74C1F59C0F6D2A6AD22F5848C9D6D`); conditional Rev43 `plan/PLAN_REV43_MANAGER_BUSINESS_API_INTEGRATION_20261117.md` (SHA-256 `239A1E64E5C3269A7536497DB5DDAA2A582EC7844E25468837A9F1B3286AA597`).
- Approval: FEAT-066 Rev42 and conditional Rev43 in `approvals/TASK_APPROVAL.md` before any account/API mutation.
- Worktree: `codex/fe-ui-web-remediation`, baseline `b72f9e46`; existing dirty files preserved.

## Read-only preflight

- Docker API and PostgreSQL report healthy; API project is `sketch2life-dev`; Firebase Admin configuration is present in the API container.
- Read-only database counts: one `platform_admin`, zero `school_manager`, zero organizations, zero organization assignments. No row values or email addresses were read.
- The worktree has no `.env` or `.env.local`. The ignored temporary Vite file contains a local API proxy only and no Firebase Web config. FE port 5173 refused connection.
- Rev42 requires a Firebase Web config whose project matches `sketch2life-dev`; the config must not be printed or stored in evidence.

## Current outcome and gate

Account provisioning has **not started**. No Firebase user, organization, assignment, password, token, database row, or email was created or changed. Waiting for the owner to provide the config via Git-ignored `apps/web/.env.local` or point to an existing local config. This gate avoids creating an orphan Firebase identity that cannot be signed in or validated.

Static Rev43 route audit found five operations suitable to connect under current guards/contracts (organization read, minimal roster read, consent-status read, Parent-group list/create) and five operations to keep unavailable pending compatible backend policy/reads. The already-connected class-create endpoint does not enforce SRS capacity. No Rev43 app/API implementation has started.

After Rev42 login succeeds, conditional Rev43 authorizes the five suitable operations and SRS gap handling described in its exact plan.

No credentials, API key, child data, or bearer token are present in this note. No commit or push.

## Follow-up — config supplied and task completed

The owner supplied the Git-ignored worktree-root .env path. Its four Firebase Web config fields were present and its project ID matched sketch2life-dev; no values were recorded. The first two temporary Firebase identities used to diagnose bootstrap ordering were deleted after failed transactions. Rev44 records and fixes the assignment foreign-key ordering issue. The final QA account was provisioned and retained only after Firebase password sign-in, authenticated role resolution and organization-wide school_admin assignment reads passed. Sanitized results and Rev43 implementation checks are in EV-051. The final account credential is delivered directly in the owner response only.
