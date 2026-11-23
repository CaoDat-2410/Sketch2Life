# FEAT-066 Plan Rev49 — Admin and Manager QA credentials in ignored temp storage

- Date: 2026-11-17 (Asia/Bangkok).
- Status: APPROVED_FOR_EXECUTION from the owner's direct request to reseed one Admin and one Manager test account and place credentials in tmp.
- Worktree: codex/fe-ui-web-remediation.
- Product authority: FEAT-063 SRS v2.7-draft Rev60 via docs/context/SRS_AUTHORITY.md; unsigned.
- Environment: Firebase Authentication project sketch2life-dev and local Docker API/PostgreSQL only.

## Preflight

Read-only verification found exactly one active Firebase reserved-domain account mapped to an active platform_admin identity, and exactly one mapped to an active school_manager identity. The Manager has one active organization-wide school_admin assignment. No email, UID, organization ID, credential, or token was printed. The repo ignores tmp/ (confirmed by git check-ignore).

## Approved scope

1. Reset the password of only those two existing dedicated QA identities through Firebase Admin SDK, preserving their email, role, account state, Manager organization, and assignment.
2. Generate independent high-entropy passwords in memory; do not print them to console or logs.
3. Save the two emails/passwords and role-specific login URLs to tmp/qa-test-accounts.local.md. This file is ignored by Git. The user's direct request supersedes the earlier no-persistence boundary only for this local ignored tmp file; do not copy credentials to plans, evidence, source, .env, screenshots, or Git.
4. Verify Firebase password sign-in for both identities; verify GET /api/auth/v1/me returns platform_admin and school_manager respectively; verify Manager GET /api/be1/v1/organizations/{organization_id}/me returns the existing organization-wide school_admin assignment. Verify an Admin read endpoint returns success without printing response data.
5. Record sanitized outcomes in EV-055. Do not include credentials or token material in repository evidence.

## Safety and stop conditions

- Confirm the configured Firebase project is exactly sketch2life-dev immediately before password changes. Never use production.
- Do not create duplicate users, delete users, change roles, create organizations, alter database rows, send email, or touch non-QA identities.
- If the exact two reserved-domain QA identities or the Manager assignment no longer match preflight, stop without mutation and report the discrepancy.
- Credentials may exist only in process memory and the ignored tmp file. Do not commit or push this task.
- Do not print Firebase configuration, admin keys, ID tokens, database URLs, passwords, or account-list rows.
- Preserve all unrelated dirty worktree changes.

## Acceptance criteria

- The same two QA accounts remain active with their existing Admin/Manager roles and Manager scope.
- Both new passwords authenticate against sketch2life-dev and role resolution matches the stored role.
- The Manager assignment remains organization-wide school_admin.
- tmp/qa-test-accounts.local.md contains the retrievable credentials and is confirmed ignored by Git.
- EV-055 reports only sanitized status codes, role checks, and limitations.
- No production resource, email delivery, account outside the selected pair, application source, commit, or push is changed.
