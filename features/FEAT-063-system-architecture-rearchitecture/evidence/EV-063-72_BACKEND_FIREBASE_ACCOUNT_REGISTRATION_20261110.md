# EV-063-72 — Backend Firebase account registration

**Date:** 2026-11-10
**Plan:** Rev62, final SHA-256 `1C245F296FDFBBEACDEF3AEC6D1D1C9AF21122A457490F3AE801DEEB11532FDE`
**Lifecycle:** REVIEW — backend account creation is verified; Firebase REST sign-in is blocked by the Web API key currently configured in the root `.env`.

## Scope and authority

The owner requested a backend registration API and a test that confirms the account is created in Firebase. Current product requirements were read from `docs/context/SRS_AUTHORITY.md` and the FEAT-063 canonical SRS v2.7-draft, especially FR-C-01, FR-O-09, UC-13, and §3. UC-13 describes fuller identity registry, action-link, verification, and activation behavior; this local slice implements only identity creation.

## Implementation

- Added `POST /api/auth/v1/registrations`, mounted in the durable/classroom app profile without a database dependency.
- Endpoint is available only for `SKETCH2LIFE_ENV=local`, caps each client IP at five attempts per 15 minutes, validates email/password, rejects extra fields such as role, and uses generic errors with request IDs.
- Firebase Admin identity creation uses the same project-scoped Admin app/config as ID-token verification. The identity is created with `email_verified=false`; no application role, UID, profile, or token is returned or persisted.
- Parent mobile signup calls the backend first, then Firebase Auth REST `accounts:signInWithPassword`. Normal sign-in, in-memory refresh and sign-out remain in place.
- `SKETCH2LIFE_MOBILE_API_BASE_URL` is read from the single root `.env`; `.env.example` gives the Android emulator host address. No Android SDK config file, Admin credential copy, Firestore, Realtime Database, or Firebase Storage was added.
- The local root `.env` was given the emulator API base URL and its Web API key line was aligned to the owner-provided value. `.env` is ignored and was not printed or included in repository changes.

## Automated verification

- Backend focused contract, composition, Admin adapter and credential tests: **18 passed**.
- Parent `firebaseAuthSession` Jest suite: **6 passed**.
- Parent TypeScript check: **passed**.
- Backend Ruff check on changed Python files: **passed**.
- `docker compose config -q`: **passed**; no Docker services were started or changed.
- The frozen route-surface test was run with the repository's conditional local storage example disabled for that process; storage routes remain unchanged.

## Live Firebase smoke result

- Backend HTTP request start: `2026-11-09T21:55:11Z` (2026-11-10 04:55:11 Asia/Saigon).
- Synthetic account: `synthetic Firebase identity (identifier redacted)`.
- Backend response: **201 Created**, `IDENTITY_CREATED`.
- Firebase Admin `get_user_by_email` lookup in project `sketch2life-dev`: **PASS**; `email_verified=false`.
- The account was retained in Firebase for owner inspection. Its password was generated randomly in memory; it was not written to evidence, logs, `.env`, or repository files. For the subsequent REST sign-in probe, the same synthetic account was given a fresh random password via Admin and that value was discarded.
- Firebase Auth REST sign-in: **FAIL**, provider response `API key not valid. Please pass a valid API key.` The root `.env` value matches the string previously provided by the owner, so the supplied key itself may be deleted, associated with another project, or restricted. Project ID and auth domain match `sketch2life-dev`.
- No second Firebase account was created. The retained synthetic account is not usable without an owner-controlled password reset; it remains unverified and has no Parent profile/scope.

This verifies that backend-created identities appear in Firebase Auth. It does **not** verify that the Parent app can finish sign-in until a valid Firebase Web API key is supplied and the REST probe is rerun.

## Limits and remaining work

- No DB identity registry, Parent role/scope/profile, email-verification action-link/email delivery, account activation, recovery, or full UC-13 flow.
- Local-only, process-local throttling is not production protection. Production registration needs an authorized onboarding design and distributed abuse controls.
- The live request used FastAPI `TestClient` against the backend ASGI app and the configured real Firebase Admin adapter; Docker services were not started or modified. No database/migration, AI/video call, commit, or push occurred.
- Owner action needed: copy a fresh Web API key from Firebase Console → Project settings → General → `sketch2life-dev` Web app config; ensure it belongs to this Firebase project, is not deleted/restricted from matching the app, and allows Identity Toolkit (`identitytoolkit.googleapis.com`) and Secure Token (`securetoken.googleapis.com`). Then update only `VITE_FIREBASE_API_KEY` in the root `.env` and rerun REST sign-in.

## Primary sources

- [Firebase Admin Python Auth reference](https://firebase.google.com/docs/reference/admin/python/firebase_admin.auth) — server-side `create_user` API.
- [Firebase Auth REST API](https://firebase.google.com/docs/reference/rest/auth) — email/password sign-in and Web API key use.
- [Add Firebase to an Android project](https://firebase.google.com/docs/android/setup) — native SDK setup and `google-services.json`; not required by the REST-based client in this slice.
- [Manage Firebase API keys](https://firebase.google.com/docs/projects/api-keys) — key/project association, API restrictions, and common invalid-key causes.
