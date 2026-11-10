# Account role and Firebase recovery API contract — Rev63

**State:** implementation contract for the Rev63 auth slice; backend role/account APIs, additive migration, and Firebase Identity Toolkit password lifecycle passed isolated runtime acceptance. Interactive UI and signed-token role-gate acceptance remain pending.
**Authority:** FEAT-063 v2.7-draft SRS, §§3, 7 (FR-C-01/FR-O-09), UC-13, §31.3 and §31.10(14).
**Role values:** `parent`, `teacher`, `school_manager`, `platform_admin`.

## Authorization rules

- Firebase Authentication verifies the adult identity. PostgreSQL `be1_adult_identities.account_role` resolves the application role; Firebase custom claims and client-supplied roles are not used. An identity with no server-assigned role is denied protected account and organization routes.
- `school_manager` is separate from `platform_admin`; its school/class authority remains in BE1 organization assignments. `teacher` accounts receive no implicit organization or class access.
- Parent and Teacher are separate accounts. Platform Admin role does not grant child profile/media access.
- Only an active Platform Admin may use `/api/platform-admin/v1/accounts`.
- Passwords are sent only to Firebase Authentication. They are not returned by or persisted in the application API.

## Endpoints

### `POST /api/auth/v1/registrations`

Creates a Firebase email/password identity, then persists a server-assigned Parent role. The database write is compensated by deleting the just-created Firebase identity if persistence fails.

Request:

```json
{
  "email": "parent@example.com",
  "password": "at-least-6-characters"
}
```

`role`, Firebase UID, tokens and profile data are forbidden in the request.

201 response:

```json
{
  "status": "IDENTITY_CREATED",
  "role": "parent",
  "email_verified": false
}
```

Errors: `409 ACCOUNT_SETUP_UNAVAILABLE`, `422 INVALID_REGISTRATION_REQUEST`, `429 RATE_LIMITED`, `503 IDENTITY_PROVIDER_UNAVAILABLE` or `503 ACCOUNT_SETUP_UNAVAILABLE`. Conflict responses do not reveal whether an email belongs to a Parent, Teacher or another role. Public registration is rate limited per client IP in the API process; production deployment also needs a shared edge/API rate limit.

### `GET /api/auth/v1/me`

Requires a verified Firebase bearer ID token. Resolves the signed-in user's server role and account state; it returns no Firebase UID or email.

200 response:

```json
{
  "role": "teacher",
  "state": "active",
  "role_revision": 3
}
```

An invalid Firebase ID token receives `401 INVALID_IDENTITY_TOKEN`. An identity without an active persisted role or with an issuer mismatch receives the generic `403 ACCOUNT_SETUP_UNAVAILABLE` response.

### `GET /api/platform-admin/v1/accounts`

Platform Admin only. Query parameters: optional `role`, `state`, `search`, `limit` (1–100, default 50), `offset` (default 0). Returns opaque account references; the Firebase UID is not included. Email and display name are loaded from Firebase Auth for the authorized Platform Admin response and are not persisted in PostgreSQL or audit records. Search is performed against those provider-owned fields before pagination. Historical identity rows whose role could not be safely backfilled are returned with `role: null`, so Platform Admin can assign them a role; protected app routes deny those accounts until then.

```json
{
  "items": [
    {
      "account_id": "opaque-uuid",
      "email": "teacher@example.com",
      "display_name": "Cô An",
      "role": "teacher",
      "state": "active",
      "revision": 2
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

### `POST /api/platform-admin/v1/accounts`

Creates an unverified Firebase identity without an application-generated password, then stores the role in PostgreSQL. The user sets a password through Firebase password recovery. A `school_manager` account requires an existing `organization_id` and receives an organization-wide `school_admin` BE1 assignment. A new `teacher` account gets no implicit class assignment; the School Manager assigns its classes through the existing BE1 assignment workflow.

Request:

```json
{
  "email": "teacher@example.com",
  "display_name": "Cô An",
  "role": "teacher"
}
```

For a School Manager, also include `"organization_id": "school-opaque-id"`. Parent and Platform Admin accounts cannot be attached to an organization in this request.

201 response is an account object matching the list item. Email and display name in this response come directly from the admin request and are not stored in the application database. Admin Web then asks Firebase Auth to send a password-reset email; if that request fails, the account remains created and the UI directs the user to use “Quên mật khẩu”. Errors include `403 FORBIDDEN`, generic `409 ACCOUNT_SETUP_UNAVAILABLE`, `422 INVALID_ACCOUNT_REQUEST`/`ORGANIZATION_UNAVAILABLE`, and `503 IDENTITY_PROVIDER_UNAVAILABLE`/`ACCOUNT_SETUP_UNAVAILABLE`.

### `PATCH /api/platform-admin/v1/accounts/{account_id}`

Platform Admin only. `account_id` is the opaque account reference from the list response.

Change role:

```json
{ "role": "school_manager", "organization_id": "school-opaque-id" }
```

Disable or re-enable:

```json
{ "state": "disabled" }
```

Role changes increment `revision`; incompatible active BE1 assignments are revoked in the same transaction. Disabling updates Firebase Auth, revokes refresh tokens and marks the backend identity inactive. Self-demotion and removal/disablement of the last active Platform Admin return `409`. Changes are recorded as metadata-only audit entries.

## Password recovery and change

- Parent Android calls Firebase Identity Toolkit `accounts:sendOobCode` with `PASSWORD_RESET`; authenticated change reauthenticates with the current password and calls `accounts:update` with the Firebase ID token.
- Teacher and management Web use Firebase Authentication SDK `sendPasswordResetEmail`, `reauthenticateWithCredential`, and `updatePassword`.
- After Platform Admin creates an account, Admin Web requests Firebase Auth to send the new user a password-reset email. The account remains created if the email request fails; the UI then tells the user to initiate “Quên mật khẩu”.
- UI reset responses are generic and do not confirm whether an email exists. Backend never receives the password-reset token or new password.

## One-time Platform Admin seed

1. Set `SKETCH2LIFE_PLATFORM_ADMIN_BOOTSTRAP_EMAIL` in the repository-root `.env` to an email not already attached to an unrelated Firebase identity.
2. Rebuild/recreate the API container so it receives the updated root `.env`, then apply the additive migrations with `docker compose exec api alembic upgrade heads`.
3. Run from the API container: `docker compose exec api python -m sketch2life.infrastructure.identity.bootstrap_platform_admin`.
4. The command creates an identity without a password; use the management login's Firebase password-reset action to set one. It is idempotent only when that same Firebase identity is already an active Platform Admin. It refuses to adopt an unrelated existing Firebase identity and refuses to bootstrap a second Platform Admin after the first exists.

The `.env.example` contains only a blank placeholder. No seed account, password, reset link, service-account JSON or credential is stored in the repository.

## Known verification limits

- The Rev63 E2E run applied all Alembic heads to a disposable PostgreSQL database and exercised registration, role gates, Platform Admin bootstrap/account lifecycle, and error mapping. Detailed results and cleanup are in `evidence/EV-063-73_ROLE_BASED_AUTH_AND_RECOVERY_20261110.md`.
- The root `.env` initially held a Web API key different from the owner-provided Firebase Web app config. After correcting it, a non-mutating Identity Toolkit probe returned HTTP 200 and a synthetic reset/sign-in/change-password lifecycle passed; no email was sent and the test identity was deleted. See `evidence/EV-063-73_ROLE_BASED_AUTH_AND_RECOVERY_20261110.md`.
- Full Compose startup was blocked because the MinIO image registry returned HTTP 401. The E2E used isolated disposable API/PostgreSQL containers; pre-existing API/ClamAV services were preserved and the disposable containers were removed afterward.
- Admin/Teacher production builds and Parent mobile typecheck passed, but no browser-based interactive UI E2E was run.
- Role-gated business API cases used a test-only `VerifiedPrincipal` dependency override; the E2E did not validate a Firebase-signed ID token against the running application.
- The root `.env` still has no Platform Admin bootstrap email. The E2E exercised bootstrap with a synthetic runtime value; no real or persistent admin seed was created.
- Parent sign-up currently assigns an active Parent role before email verification. UC-13 verification-state activation and delivery of invitation/verification messages remain unimplemented; this slice does not close that SRS requirement.
- Public registration rate limiting is process-local. A production deployment must configure a shared edge/API limit before public exposure at scale.
- This contract does not claim complete UC-13 email verification/email delivery. The repository has no mail delivery adapter, and the seed/admin-create flow relies on Firebase password recovery. Treat verified-email activation and invitation email delivery as a release follow-up.
