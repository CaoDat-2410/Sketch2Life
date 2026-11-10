# Plan Rev61 — Single root `.env` for Firebase Auth and Docker — 2026-11-10

**Status: APPROVED** by the owner's direct instruction in this conversation. Implementation is restricted to the existing `repository root` checkout. Do not create, switch to, or modify a sibling checkout/worktree.

## Objective

Use one root `.env` as the local configuration source for Docker API Firebase Admin verification, the existing Teacher Web Firebase client, and the active Parent Android Firebase client. Keep `.env.example` as the single placeholder template. Implement Parent email/password sign-in and sign-up through Firebase Authentication behind the existing `AuthSessionPort`; the backend verifies issued ID tokens and does not store a second password/account identity.

## Scope and architecture

- Root `.env` contains the Firebase Web public config, `SKETCH2LIFE_AUTH_PROVIDER`, Firebase project ID, and a single-line Base64 encoding of the Firebase Admin service-account JSON for local Docker verification.
- Docker Compose passes Admin credentials only to the API container. The mobile Babel environment transform exposes only the allow-listed `VITE_FIREBASE_*` client configuration; backend Admin credential values must never be inlined into app bundles.
- Teacher Vite reads the same root `.env` through its configured `envDir`.
- Parent Android uses Firebase Authentication's HTTPS email/password REST endpoints (signup, signin, refresh, local signout) behind the existing `AuthSessionPort`. The Web API key is public client config; the Firebase Admin credential remains backend-only. This avoids another native Firebase config file. Firebase Storage/Firestore/Realtime Database are not used.
- Root `.env` is ignored and local. `.env.example` contains no usable credentials. No JSON key file or nested `.env` is required in the project.
- Scope is limited to Firebase config/auth wiring and FEAT-063 tracking. No Parent profile/StoryRun APIs, role provisioning, consent, product data, or SRS business rules are added.

## Acceptance criteria

1. Docker, Teacher Web and Parent Android Firebase settings are represented in one root `.env`; no app-local `.env` is needed.
2. Parent Android exposes email/password sign-in, sign-up and sign-out through a Firebase Auth client adapter implementing the existing auth boundary; ID token refresh works for the active app process.
3. Backend Firebase Admin verifier accepts the Admin service-account JSON supplied as Base64 in the root `.env`, without logging credential contents. Firebase project/issuer validation and revoked-token policy remain enforced.
4. Compose forwards only backend Firebase settings to the API; no Admin secret is available to Vite or mobile. Existing Docker services are not started/stopped by this task.
5. Teacher Vite and Parent Android obtain only public client values from the same root `.env`.
6. Root `.env` and all credentials remain ignored; `.env.example` has placeholders only; `git check-ignore` confirms the actual local env.
7. Focused mobile and backend verification plus Teacher production build and `docker compose config -q` pass. No live Firebase account, user, token, database, or provider call is created.
8. Feature evidence/context/source/status/decision and this plan/approval are updated. Canonical SRS remains unchanged and authoritative.

## Verification

- Confirm only the root `.env` supplies local Firebase configuration.
- Run the Firebase credential decoder/verifier unit tests with synthetic credentials, focused mobile typecheck/tests, Teacher UI production build, and `docker compose config -q`.
- Inspect app bundle configuration to confirm the Admin credential key is not exposed.
- Do not start/recreate/stop Docker services; do not make a live Firebase Auth request.

## Exclusions and limits

- No worktree creation/deletion, branch switch, checkout cleanup, or edits outside `repository root`.
- No Firebase Console changes, live account creation, real child data, database/API mutations, migrations, AI/Modal requests, commit, push, or deployment.
- No Parent role/profile/consent provisioning. Current Parent profile and StoryRun API gaps remain open.
- No secure refresh-token persistence across process restarts in this first auth adapter; the account remains in Firebase and the adult signs in again after the app process is cleared.
- No edits to the canonical SRS; it remains an unsigned v2.7-draft.

## Path manifest

- `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV61_SINGLE_ROOT_ENV_FIREBASE_AUTH_20261110.md`
- `features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md`
- `features/FEAT-063-system-architecture-rearchitecture/CONTEXT.md`
- `features/FEAT-063-system-architecture-rearchitecture/SOURCE_REGISTER.md`
- `features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md`
- `features/FEAT-063-system-architecture-rearchitecture/status/STATUS.md`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/README.md`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-71_SINGLE_ROOT_ENV_FIREBASE_AUTH_20261110.md`
- `.env.example`
- `.env` (ignored local configuration; never stage/commit)
- `.gitignore` only if needed to retain root `.env` ignore
- `compose.yaml`
- `backend/src/sketch2life/infrastructure/config/settings.py`
- `backend/src/sketch2life/infrastructure/identity/firebase_token_verifier.py`
- focused backend verifier tests under `backend/tests/`
- `apps/mobile/package.json`, `apps/mobile/src/infrastructure/auth/`, `apps/mobile/src/app/`, `apps/mobile/babel.config.js`, `apps/mobile` lockfile/dependencies as needed
- `apps/teacher-ui/vite.config.ts`

## Approval basis

The owner explicitly directed that the work stay in the single `repository root` folder, use one project-root `.env`, avoid splitting config across app/worktree folders, and make the Firebase/Docker setup usable from that configuration. This direct request approves the exact scope above; it does not authorize live cloud account creation or publication.
