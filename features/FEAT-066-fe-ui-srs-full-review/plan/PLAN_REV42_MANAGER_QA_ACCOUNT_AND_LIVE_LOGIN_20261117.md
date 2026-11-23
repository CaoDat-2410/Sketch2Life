# FEAT-066 Plan Rev42 — School Manager QA account and live login

- Status: APPROVED_FOR_EXECUTION; waiting for local Firebase Web configuration before provisioning.
- Owner request: “Cho account test lun sau đó login đồ ổn thì qua tiếp nối các api nghiệp vụ”.
- Worktree/branch: `F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation`; `codex/fe-ui-web-remediation` at `b72f9e46`.
- Product authority: FEAT-063 SRS v2.7-draft Rev60 via `docs/context/SRS_AUTHORITY.md`; unsigned.
- Dev target: Firebase project `sketch2life-dev` and the local Docker API/PostgreSQL only.

## Pre-change observations

- Local API and PostgreSQL containers report healthy.
- Read-only database counts: one active `platform_admin`, no `school_manager`, no organization, and no organization assignment.
- Firebase Admin credentials are configured in the API container. The worktree has no Firebase Web config or `.env.local`; the FE dev server on port 5173 is not running.
- Rev41 explicitly excluded account creation, so this is a separate owner-approved scope. No existing Platform Admin identity or password will be changed.

## Approved scope

Provision exactly one non-production Manager QA identity with a generated reserved-domain email and high-entropy password, and a dedicated QA organization. Do not send email or use real user data. Create the identity in Firebase Authentication and establish `school_manager` plus an organization-wide `school_admin` assignment through the supported first-school-admin bootstrap flow. Verify password sign-in, authenticated `GET /api/auth/v1/me`, and authenticated `GET /api/be1/v1/organizations/{organization_id}/me`; then verify the FE login route opens the Manager portal. Deliver the one-time credentials directly to the owner only after verification. Never persist password, Firebase ID token, or API key in repo files, logs, screenshots, or evidence.

The account must not be created until a valid local Firebase Web config for `sketch2life-dev` is available. Use ignored `apps/web/.env.local` or an owner-provided local config path. Read only the required public Web config fields; do not request or change the existing Admin password. If Web config is absent, stop before creating any Firebase user to avoid an orphan identity.

## Acceptance criteria

1. Confirm the Web config's project ID matches `sketch2life-dev` without printing the API key.
2. Provision one account and one dedicated organization without touching the existing Platform Admin, unrelated organizations, child/profile data, or email delivery.
3. Password sign-in succeeds; authenticated `/api/auth/v1/me` reports `school_manager`; the assignment read returns the same organization and an organization-wide `school_admin` assignment.
4. The FE route `/login?role=manager` authenticates with Firebase and both APIs, then opens `/school`; wrong role/assignment continues to fail closed.
5. Record sanitized statuses and role/assignment shape in EV-050. Deliver credentials in the owner-facing response only. No credentials/tokens in evidence.

## Work sequence

1. Record this plan and direct owner approval before account/API mutation.
2. Wait for the required local Firebase Web config; verify project match without exposing its key.
3. Generate credentials in memory, create the Firebase identity, and use the verified Firebase token with the supported BE1 first-school-admin bootstrap to establish the QA organization and Manager assignment.
4. Verify both authenticated read APIs, then run the FE dev server with same-origin local API proxy and configured `organization_id`; perform the Manager sign-in route smoke.
5. On any failure, delete only the newly created QA Firebase identity and remove its dedicated DB organization/role/assignment if bootstrap completed; preserve all existing rows. Record sanitized failure and cleanup status.
6. Record verification, limitations, and one-time owner credential delivery without writing the password or token to repository files.

## Exclusions and security

- No production project, real emails, email delivery, child/profile/consent/story data, existing-account/password/role changes, general organization provisioning UI, application source changes, business API integration, commit, or push.
- Do not store the generated credential in `.env`, source, logs, evidence, screenshots, or seed data. Remove transient credential material after verification; return the credential directly to the owner.
- Existing Rev41 and unrelated worktree changes remain preserved.
