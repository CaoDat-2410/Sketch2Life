# Plan Rev62 — Parent account registration through backend and Firebase Auth

**Date:** 2026-11-10
**Feature:** FEAT-063 — system architecture rearchitecture
**Lifecycle:** REVIEW — implementation and focused checks are complete; live Parent sign-in remains blocked by the configured Firebase Web API key.

## Goal

Complete the local Parent signup path so the mobile client asks the backend to create the Firebase Authentication identity, then signs in through Firebase Auth REST to obtain its ID and refresh tokens. Verify one real backend request creates an account visible through Firebase Admin SDK in `sketch2life-dev`.

## Authority and source boundary

- Current product requirements: `docs/context/SRS_AUTHORITY.md` and the canonical FEAT-063 SRS v2.7-draft, §§1–31. The SRS is unsigned; its §32 is an environment-specific snapshot.
- Relevant requirements: FR-C-01 and FR-O-09; UC-13 informs safe identity provisioning but is a fuller Teacher/recovery workflow than this task.
- Firebase Authentication is the only Firebase product in scope. The server owns role assignment; a registration request cannot choose Parent, Teacher, Manager, or Admin.
- Firebase's Admin SDK supports server-side user creation. Firebase Auth REST supports email/password sign-in using the project's public Web API key. This slice does not claim to implement all of UC-13.

## Approved implementation scope

1. Add a versioned public endpoint `POST /api/auth/v1/registrations` with an explicit request/response/error contract. Accept only email and password; never accept a role or Firebase UID.
2. Implement an application provisioner port and a Firebase Admin adapter sharing the existing project-scoped Admin app/configuration path with token verification.
3. Restrict this endpoint to `SKETCH2LIFE_ENV=local`; reject it outside local mode. Apply bounded per-process IP throttling (5 attempts per 15 minutes) as a local development safeguard. This is not a production rate-limit design.
4. Return a generic `ACCOUNT_SETUP_UNAVAILABLE` response for duplicate/identity setup conflicts and a generic provider-unavailable response for service failures. Do not return UID, provider exception text, password, or account-existence details. Redact validation errors so they cannot echo submitted values.
5. Wire Parent mobile signup through the backend endpoint, then use the existing Firebase Auth REST password sign-in operation to establish its session. Keep sign-in/refresh/sign-out behavior intact.
6. Keep all configuration in the single repository-root `.env`; add only a non-secret mobile API base URL to `.env.example` and the root-env Babel allowlist. Do not add an Android Firebase SDK or `google-services.json` for the existing REST-based flow.
7. Add focused backend contract/unit coverage and Parent auth adapter tests, then run those tests and a live smoke request through the backend endpoint. Use a unique synthetic `example.com` email and random password held only in memory. Verify the user via Firebase Admin lookup. Keep the synthetic Firebase account so the owner can inspect it; record no password, service-account JSON, private key, or ID token.
8. Record the final endpoint contract, tests, live verification outcome, limits, decisions, source references, and lifecycle in FEAT-063 context/decision/source/evidence/status records.

## Exact planned path manifest

- `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV62_BACKEND_FIREBASE_ACCOUNT_REGISTRATION_20261110.md`
- `features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md`
- `features/FEAT-063-system-architecture-rearchitecture/artifacts/AUTH_REGISTRATION_API_CONTRACT_REV62.md`
- `features/FEAT-063-system-architecture-rearchitecture/CONTEXT.md`
- `features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md`
- `features/FEAT-063-system-architecture-rearchitecture/SOURCE_REGISTER.md`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/README.md`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-72_BACKEND_FIREBASE_ACCOUNT_REGISTRATION_20261110.md`
- `features/FEAT-063-system-architecture-rearchitecture/status/STATUS.md`
- `.env.example`
- `apps/mobile/babel.config.js`
- `apps/mobile/src/infrastructure/auth/firebasePublicConfig.ts`
- `apps/mobile/src/infrastructure/auth/firebaseAuthSession.ts`
- `apps/mobile/__tests__/firebaseAuthSession.test.ts`
- `backend/src/sketch2life/application/ports/identity.py`
- `backend/src/sketch2life/infrastructure/identity/firebase_admin_app.py` (new)
- `backend/src/sketch2life/infrastructure/identity/firebase_token_verifier.py`
- `backend/src/sketch2life/infrastructure/identity/firebase_admin_account_provisioner.py` (new)
- `backend/src/sketch2life/interfaces/http/router_composition.py`
- `backend/src/sketch2life/interfaces/http/app.py`
- `backend/src/sketch2life/interfaces/http/routers/auth_registration.py` (new)
- `backend/tests/contract/test_auth_registration_api.py` (new)
- `backend/tests/contract/test_app_composition.py` (update the frozen route-surface assertion for the approved auth route)
- `backend/tests/unit/test_firebase_admin_credentials.py`
- `backend/tests/unit/test_firebase_admin_account_provisioner.py` (new)

The ignored root `.env` may receive only `SKETCH2LIFE_MOBILE_API_BASE_URL=http://10.0.2.2:8000` if it is absent. It remains local-only and is not part of Git publication.

## Acceptance criteria

- **AC1:** OpenAPI contains only the reviewed `POST /api/auth/v1/registrations` registration operation for this slice; its schema omits any role/UID input and does not expose password in responses.
- **AC2:** The route is unavailable outside local mode, rejects malformed email/password safely, enforces the bounded local rate limit, and never uses the database.
- **AC3:** The Firebase Admin adapter creates an unverified email/password identity in the configured Firebase project, maps conflicts/provider failures to safe errors, and never logs or returns credentials/provider payloads.
- **AC4:** Mobile signup calls the backend first and only then signs in with Firebase Auth REST; normal sign-in and refresh continue to work. API base URL and public Firebase settings resolve from the single root `.env`.
- **AC5:** Focused tests pass. One live backend API request creates a synthetic account in `sketch2life-dev`, and a subsequent Firebase Admin lookup confirms the account exists and is unverified. Evidence identifies the generated synthetic email and timestamps but contains no password/token/credential.
- **AC6:** FEAT-063 contract, context, decisions, source register, evidence index, and status record match the code and clearly state that full SRS onboarding (identity registry, Parent scope/profile, email-verification action link/delivery, activation, production-grade distributed throttling) is not implemented by this slice.

## Exclusions and safety boundaries

- No DB schema, migration, identity-registry record, Parent profile, role claim, account recovery, Teacher invitation, email-verification link/email delivery, or complete UC-13 implementation.
- No Firebase Storage, Firestore, Realtime Database, Android Firebase SDK, Firebase Console app registration, or `google-services.json`.
- No root `.env` secret changes, copying service-account JSON into the repository, logging/printing secrets, or publishing any credential.
- No production enablement, Docker service lifecycle change, unrelated auth/provider changes, commit, push, branch/worktree switch, or edit outside the manifest.
- The live smoke account is synthetic and intentionally remains in Firebase for owner inspection; its generated password is discarded after the sign-in check, if performed.

## Verification plan

1. Backend contract tests with fake provisioner: success, local-only guard, malformed requests with response redaction, duplicate conflict, provider outage, rate limit, and OpenAPI contract.
2. Backend unit tests for Firebase Admin project/config reuse and safe exception mapping.
3. Parent Jest tests for backend-first signup and Firebase REST sign-in, plus existing mobile typecheck.
4. Live smoke through the backend app's HTTP route using configured root `.env`; verify account via Firebase Admin lookup. Do not test video/AI or unrelated APIs.

## Outcome — review required

- AC1–AC3: pass. The versioned route is local-only, validates/redacts requests, rejects client-selected role, applies the local rate limit, uses the shared Firebase Admin app and returns no UID/password.
- AC4: implementation, Jest sequence test (backend registration before Firebase REST sign-in), and mobile typecheck pass. Live REST sign-in could not complete because Firebase rejected the configured Web API key as invalid.
- AC5: pass for backend creation and Firebase visibility. The backend returned HTTP 201 for `synthetic Firebase identity (identifier redacted)`; a Firebase Admin lookup found it with `email_verified=false`. The same account was retained. No password or token was saved.
- AC6: FEAT-063 contract/context/decision/source/evidence/status records were updated. The full identity-registry/Parent-profile/email-verification/activation workflow remains out of scope.
- Focused backend tests: 18 passed. Parent auth Jest: 6 passed. Parent TypeScript check: passed. Ruff check: passed.
- The Web API key in the root `.env` was aligned to the value previously supplied by the owner, but Firebase still returned `API key not valid`; the value may be deleted, belong to another project, or be restricted. The owner must copy a fresh key from the `sketch2life-dev` Web app config and confirm the Identity Toolkit API is allowed before the real mobile sign-in can be verified.
- Live verification used FastAPI `TestClient` against the backend app with the real Firebase Admin adapter. Docker services were not started or changed. No DB/migration, commit, or push occurred.
