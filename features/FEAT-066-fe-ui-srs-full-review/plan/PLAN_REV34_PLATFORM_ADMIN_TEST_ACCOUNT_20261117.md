# FEAT-066 — Platform Admin test account for local FE verification

- Plan revision: 34
- Status: APPROVED_FOR_EXECUTION
- Date: 2026-11-17
- Scope: one test identity in the configured nonproduction Firebase project and local Docker PostgreSQL

## Owner request

The owner requested: “đưa account test đi”. In the current Admin API/FE context, interpret this as one Platform Admin QA account for the local Admin screen.

## Exact scope

1. Use only the existing ignored local Firebase settings whose project identifier was verified in memory as `sketch2life-dev`; do not print, copy to Git, or otherwise expose the service-account credential.
2. The local PostgreSQL database has no Alembic schema/tables. Apply only the `be1_core@head` and `lesson_library@head` migration branches required for adult identity, audit and role columns; do not reset volumes or upgrade unrelated module branches.
3. Create exactly one active Platform Admin through the supported `bootstrap_platform_admin` command using a unique address on the reserved `example.com` domain, then set a generated password through Firebase Admin SDK. Keep email unverified and send no email.
4. Configure the loopback FE test server at port 5174 with the existing dev Firebase web settings and same-origin API proxy; preserve port 5173.
5. Verify sign-in against the dev Firebase project and use the resulting ID token only in memory to verify `GET /api/auth/v1/me` returns `platform_admin` and `GET /api/platform-admin/v1/accounts` succeeds. Never print/store the ID token or account-list PII.
6. Return the test email and generated password directly to the owner. Do not store the password in repository files, runtime logs or evidence.

## Acceptance criteria

- AC1: Project ID is exactly the known dev project, and no production project is used.
- AC2: Required migrations succeed on the empty local schema without dropping/resetting volumes or creating unrelated branch schemas.
- AC3: Exactly one new Firebase Auth user and one active `platform_admin` identity are provisioned; no other identity/account is modified.
- AC4: Password login succeeds in the dev project; the ID token is not emitted to command output or logs.
- AC5: Auth role lookup returns `platform_admin`; account list returns HTTP 200, but response rows/emails are never printed.
- AC6: FE on port 5174 receives the Firebase dev config and API same-origin proxy; existing port 5173 remains running.
- AC7: No Content Admin permission is added, no child media is accessed, no email is sent, and no production service/data is touched.
- AC8: No app test suite, backend/frontend source change, secret commit, commit or push.

## Security and SRS boundary

Use the canonical unsigned FEAT-063 v2.7-draft Rev60. A `platform_admin` role does not imply Content Admin permission or child-media access. This is a local QA identity, not a product seed account and not a production credential. Keep generated credentials only in the owner-facing response; the generated email uses the reserved example.com domain and is not intended to receive mail.