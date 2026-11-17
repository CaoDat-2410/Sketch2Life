# FEAT-066-EV-040 — Platform Admin local test account

- Date: 2026-11-17
- Plan: plan/PLAN_REV34_PLATFORM_ADMIN_TEST_ACCOUNT_20261117.md
- Plan SHA-256: 3EBDE69AFFA105F09DFB04901DA5539EE555361EBCBC3F8D035831A5291A9EBE
- Owner approval: approvals/TASK_APPROVAL.md, FEAT-066 Rev34.
- Worktree: `codex/fe-ui-web-remediation`.

## Provisioning

- Verified the existing ignored local Firebase config points to the nonproduction project `sketch2life-dev`; no credential value was printed or added to the repository.
- The Docker PostgreSQL database had no schema or tables before setup. Applied only `be1_core@head` and `lesson_library@head`, which contain the BE1 identity, audit, and account-role columns needed by the supported bootstrap flow. No other module branches were upgraded and no volume was reset.
- Used `bootstrap_platform_admin` to create exactly one Platform Admin identity in local PostgreSQL and Firebase Authentication. Set a generated 256-bit password through Firebase Admin SDK. The email uses reserved `example.com`, remains unverified, and no email was sent.
- The email/password are delivered only in the owner-facing Codex response. Password and bearer token are not present in this evidence, source, environment file, or runtime logs.

## Verification

- Firebase email/password sign-in: HTTP 200 against the dev project.
- Authenticated `GET /api/auth/v1/me`: role `platform_admin`.
- Authenticated `GET /api/platform-admin/v1/accounts`: HTTP 200, total 1. Account rows/email fields and the Firebase ID token were not printed.
- FE at `http://127.0.0.1:5174/login`: HTTP 200; transformed auth module contains the dev project config and API client uses the same-origin proxy. Existing port 5173 was preserved.

## Boundaries

- This is a test identity in the dev project, not production and not a repository seed account.
- No Content Admin permission was added and no child profile/media was read.
- No email delivery, other account mutation, app test suite, source-code edit, commit or push occurred in Rev34. The API image and required local schema were already running from the preceding approved handoff; this task only upgraded the two required schema branches and created the requested account.