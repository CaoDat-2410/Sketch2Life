# Backend Firebase Auth registration API — Rev62

**State:** implemented for local development; not a complete account-onboarding workflow.
**Endpoint:** `POST /api/auth/v1/registrations`
**OpenAPI tag:** `authentication`
**Authority:** FEAT-063 canonical SRS v2.7-draft, FR-C-01 and FR-O-09; the SRS is unsigned.

## Purpose

Create an email/password identity in Firebase Authentication from a backend request. Parent Android then signs in through Firebase Auth REST to obtain its Firebase ID token and refresh token. Firebase Admin credentials remain backend-only.

The route is local-only. It does not create a BE1 identity record, assign an application role, create a Parent profile, issue an email-verification link, or activate account scope. Therefore it does not satisfy the full target onboarding sequence in UC-13 and must not be enabled as a production registration workflow.

## Request

- Authentication: none; this is a public local-development registration operation.
- Content type: `application/json`.
- Fields:

| Field | Type | Rules | Purpose |
|---|---|---|---|
| `email` | string | 3–254 characters; trimmed and lowercased; basic email syntax | Firebase Auth account identifier |
| `password` | string | 6–128 characters | Passed to Firebase Admin to create the identity; never stored by this API |

Unknown fields are rejected. In particular, `role`, `uid`, and profile/scope fields are not accepted.

Example:

```http
POST /api/auth/v1/registrations HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "email": "parent@example.com",
  "password": "<local-development-password>"
}
```

## Responses

### `201 Created`

Firebase Auth identity was created with `email_verified=false`.

```json
{
  "status": "IDENTITY_CREATED",
  "email_verified": false
}
```

The response does not include email, Firebase UID, password, or tokens. It includes an `X-Request-ID` header.

### Errors

All error bodies have `{ "code", "message", "request_id" }`; messages are generic and never include submitted values or provider exception text.

| HTTP | Code | Meaning |
|---:|---|---|
| 404 | `REGISTRATION_UNAVAILABLE` | Route disabled outside `SKETCH2LIFE_ENV=local` |
| 409 | `ACCOUNT_SETUP_UNAVAILABLE` | Identity setup conflict, including an already-used account; no account/scope existence is disclosed |
| 422 | `INVALID_REGISTRATION_REQUEST` | Invalid email/password or extra field; submitted values are redacted |
| 429 | `RATE_LIMITED` | More than 5 attempts per client IP in the 15-minute window; `Retry-After: 900` |
| 503 | `IDENTITY_PROVIDER_UNAVAILABLE` | Firebase Admin is unavailable or cannot provision the identity |
| 500 | `INTERNAL_SERVER_ERROR` | Unexpected failure; response contains no provider detail |

The rate limiter is bounded and process-local. It is a development safeguard, not a production distributed abuse-control design.

## Server and client configuration

- Backend reads `SKETCH2LIFE_AUTH_PROVIDER`, `SKETCH2LIFE_FIREBASE_PROJECT_ID`, and `SKETCH2LIFE_FIREBASE_ADMIN_JSON_BASE64` from the single repository-root `.env`/container environment.
- Parent Android reads `SKETCH2LIFE_MOBILE_API_BASE_URL` plus public `VITE_FIREBASE_*` settings from the same root `.env`. The Android emulator default is `http://10.0.2.2:8000`; physical-device development needs a reachable host address and network binding.
- Mobile signup order: backend `POST /registrations` → Firebase Auth REST `accounts:signInWithPassword` → store ID/refresh tokens in process memory.
- The existing REST integration does not require Firebase Android app registration or `google-services.json`. Those are required if/when the client adopts Firebase Android SDK/native features.

## Current verification result

- Backend contract/focused tests: 18 passed; Parent auth Jest: 6 passed; mobile TypeScript check and backend Ruff check passed.
- One live backend request returned `201`; Firebase Admin lookup confirmed the synthetic identity in `sketch2life-dev`, with `email_verified=false`.
- A subsequent Firebase REST sign-in was rejected with `API key not valid` after the root `.env` was aligned to the key value supplied by the owner. The backend creation path is verified; the live client sign-in path remains blocked until a valid Web API key is copied from the Firebase project configuration.
