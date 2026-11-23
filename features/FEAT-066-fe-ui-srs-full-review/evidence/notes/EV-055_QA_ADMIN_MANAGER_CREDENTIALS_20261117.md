# FEAT-066 EV-055 — Admin and Manager QA credentials

- Date: 2026-11-17 (Asia/Bangkok).
- Plan: plan/PLAN_REV49_QA_ADMIN_MANAGER_CREDENTIALS_20261117.md.
- Approval: FEAT-066 Revision 49 in approvals/TASK_APPROVAL.md.
- Product authority: FEAT-063 SRS v2.7-draft Rev60 through docs/context/SRS_AUTHORITY.md; unsigned.
- Credentials: stored only in the local Git-ignored file tmp/qa-test-accounts.local.md at the owner's request. Credential values are intentionally absent from this evidence and all command output.

## Provisioning result

- Confirmed the configured Firebase project was sketch2life-dev before the password changes.
- Read-only preflight found one active reserved-domain Platform Admin identity and one active reserved-domain School Manager identity. The Manager had one active organization-wide school_admin assignment.
- Reset the passwords on those same two QA identities. No duplicate account was created; email, active state, roles, organization and assignment were preserved.
- Both Firebase Admin password updates succeeded. A temporary copy in the API container was removed after copying the credential file to the ignored local tmp directory.
- git check-ignore confirms tmp/qa-test-accounts.local.md is excluded by the repository's tmp/ rule.

## Verification

- Platform Admin Firebase email/password sign-in: 200.
- Platform Admin GET /api/auth/v1/me: 200, role platform_admin.
- Platform Admin GET /api/platform-admin/v1/accounts: 200; response rows were not printed.
- School Manager Firebase email/password sign-in: 200.
- Manager GET /api/auth/v1/me: 200, role school_manager.
- Manager GET /api/be1/v1/organizations/{organization_id}/me: 200 with the existing organization-wide school_admin assignment (class_id null).
- FE login routes /login?role=admin and /login?role=manager both returned 200 at the existing local Vite server on port 5173.
- Browser-based form interaction was not automated; the owner can now sign in with the local credential file.

## Boundaries

No role, account state, organization, assignment, application source, PostgreSQL row, email delivery, production resource, or unrelated Firebase identity was changed. No token, password, email, UID, organization ID, or API key is recorded here. No commit or push was performed.
