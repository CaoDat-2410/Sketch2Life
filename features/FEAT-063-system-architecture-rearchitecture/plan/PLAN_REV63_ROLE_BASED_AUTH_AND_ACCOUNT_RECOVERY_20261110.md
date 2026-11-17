# Plan Rev63 — Server-managed roles, account administration and Firebase recovery

**Status:** PLANNED; implementation authorization is recorded in `approvals/TASK_APPROVAL.md` after hashing this plan.
**Date:** 2026-11-10
**Authority:** Current FEAT-063 SRS v2.7-draft, §§3, 7 (FR-C-01/FR-O-09), UC-13, §31.3 and §31.10(14). The SRS remains unsigned. This plan implements the owner-directed account-role slice and does not claim to close the broader permission-resolver questions in §31.10.

## Goal

Deliver a usable authentication and account-administration slice across Parent Android, Teacher Web and the management web app:

- Parent self-registration is assigned `parent` by the backend.
- Teacher Web accepts only a server-resolved `teacher` account; Parent Android accepts only `parent`.
- Management Web retains the existing School Manager class-management route and adds a Platform Admin-only account-management route.
- Platform Admin can create Firebase identities, list accounts, change product roles, and disable/enable accounts. Changing role never trusts or writes client-supplied Firebase claims.
- Bootstrap the first Platform Admin through an explicit one-time operator command using the single root `.env`; no seeded credentials or accounts are committed.
- Add Firebase password-reset and authenticated password-change actions to Parent Android, Teacher Web, and management Web.

## Product/account rules

1. Product roles are `parent`, `teacher`, `school_manager`, and `platform_admin`. `school_manager` maps to the organization-scoped BE1 `school_admin` assignment; `teacher` still needs active BE1 class assignments to access class resources.
2. Parent and Teacher remain separate Firebase identities. An identity has one active product role. Role comes from PostgreSQL after Firebase ID-token verification; the client cannot choose it, and no Firebase custom role claim is introduced.
3. Only an active `platform_admin` can create or change account roles. A role change away from school-scoped access revokes incompatible active BE1 assignments in the same database transaction. Platform Admin does not receive child-profile or child-media access.
4. A Platform Admin-created Firebase account has no application-generated password. The user sets one through Firebase password recovery. Passwords, reset links, ID tokens, service-account material and provider credentials are never stored in application tables or logs.
5. The bootstrap command refuses to promote an unrelated existing Firebase account. It is idempotent only for the same already-bootstrapped Platform Admin email.
6. Raw recipient email and display name are not stored in PostgreSQL, audit entries or logs. Platform Admin account list responses resolve those fields from Firebase Auth on demand.
7. Firebase Authentication is the only Firebase product used. No Firebase Storage, Firestore or Realtime Database is introduced.

## API contract

| Method and path | Purpose | Authorization / result |
|---|---|---|
| `POST /api/auth/v1/registrations` | Create Firebase identity and persist the server-assigned Parent role | Public, bounded rate limit; returns `IDENTITY_CREATED`, `role: parent`, and `email_verified: false`; generic conflict response |
| `GET /api/auth/v1/me` | Resolve the authenticated account's active product role | Firebase ID token; returns role and account state, never Firebase UID/email |
| `GET /api/platform-admin/v1/accounts` | Search/page accounts for role administration | Active Platform Admin only; returns opaque account ID, email, display name, role, state and revision |
| `POST /api/platform-admin/v1/accounts` | Create Firebase identity plus backend role record | Active Platform Admin only; roles are validated server-side; School Manager creation requires an existing organization |
| `PATCH /api/platform-admin/v1/accounts/{account_id}` | Change product role and/or active state | Active Platform Admin only; opaque account ID; prevents self-demotion and removing/disabling the last active Platform Admin |

School Manager-to-class assignment remains on the existing BE1 assignment API. A newly provisioned Teacher account receives no implicit organization/class access. API errors use generic account-setup responses for public callers and never expose the Firebase UID or a cross-scope account-existence result.

## Implementation sequence

1. Add an explicit account-role persistence record and additive Alembic migration; backfill only roles unambiguously evidenced by existing active BE1 assignments.
2. Extend the Firebase Admin adapter to create/disable/delete identities with no role claims and return the verified provider subject internally.
3. Make Parent registration persist role `parent`, add authenticated `/me`, and make BE1 assignment authorization reject identities whose stored account role is inconsistent with the requested assignment role.
4. Add Platform Admin account list/create/update endpoints, transactional role/assignment revocation, safe bootstrap command, and persistent-role checks for existing Platform Admin-only content operations.
5. Gate Parent Android, Teacher Web, School Manager routes and Platform Admin account screens by `/me`; wire actual account create/list/role-edit actions.
6. Wire Firebase password reset and reauthenticated password change in all three clients. Add generic UI copy that does not confirm whether an email exists.
7. Update the single root `.env.example`, API contract, feature context/decisions/status/source register, and record implementation evidence and any external configuration blockers.

## Acceptance criteria

- Role is persisted server-side and returned only by authenticated `/me`; registration cannot submit a role.
- Parent sign-up creates a Firebase Auth identity and a backend `parent` role record, with compensation deleting the Firebase identity if the database write fails.
- Teacher Web rejects Parent, School Manager and Platform Admin accounts before rendering Teacher routes; Parent Android similarly rejects all non-Parent roles, including on restored sessions.
- School Manager continues to access only existing organization-scoped functions. Platform Admin can access account management but not child profile/media by virtue of that role.
- Platform Admin create/change/disable operations are server-authorized, auditable at metadata level, and synchronized with Firebase Auth; non-admins receive 403.
- Role changes revoke incompatible BE1 assignments, self-demotion is rejected, and the last active Platform Admin cannot be removed or disabled.
- Bootstrap is explicit and one-time, reads only root `.env` configuration, creates no repository credential, and creates an identity that can use Firebase password recovery.
- Parent, Teacher and management login screens can request Firebase password reset; authenticated users can reauthenticate and change their Firebase password. No password is sent to backend or persisted locally by these flows.
- Existing login/signup surfaces remain separate by app role; no account can enter a different role's app by changing client state or URL.
- API schema/docs and FEAT-063 evidence distinguish implemented behavior from the Firebase Web API key/email-delivery configuration needed for live end-to-end verification.

## Verification plan and limits

- The implementation will be reviewed against the listed acceptance criteria and existing API/client contracts.
- This task does not authorize adding or executing test suites unless the owner separately asks to test/verify. No live Firebase account will be created as part of this implementation because no bootstrap email was supplied and the current Web API key is known to fail Firebase REST authentication. A live database migration also requires Docker/PostgreSQL; the local Docker engine was unavailable during planning.
- Record static review and environment blockers in this feature's `evidence/` folder. Do not claim a live auth flow or production readiness until the owner supplies a valid Firebase Web API key/bootstrap email and a database runtime is available.

## Exact implementation path manifest

### FEAT-063 records

- `features/FEAT-063-system-architecture-rearchitecture/plan/PLAN_REV63_ROLE_BASED_AUTH_AND_ACCOUNT_RECOVERY_20261110.md`
- `features/FEAT-063-system-architecture-rearchitecture/approvals/TASK_APPROVAL.md`
- `features/FEAT-063-system-architecture-rearchitecture/CONTEXT.md`
- `features/FEAT-063-system-architecture-rearchitecture/DECISIONS.md`
- `features/FEAT-063-system-architecture-rearchitecture/SOURCE_REGISTER.md`
- `features/FEAT-063-system-architecture-rearchitecture/status/STATUS.md`
- `features/FEAT-063-system-architecture-rearchitecture/artifacts/AUTH_ROLE_API_CONTRACT_REV63_20261110.md`
- `features/FEAT-063-system-architecture-rearchitecture/artifacts/DATA_TABLE_REGISTER.md`
- `features/FEAT-063-system-architecture-rearchitecture/evidence/EV-063-73_ROLE_BASED_AUTH_AND_RECOVERY_20261110.md`

### Backend

- `backend/src/sketch2life/application/ports/identity.py`
- `backend/src/sketch2life/infrastructure/config/settings.py`
- `backend/src/sketch2life/infrastructure/identity/firebase_admin_account_provisioner.py`
- `backend/src/sketch2life/infrastructure/identity/firebase_token_verifier.py`
- `backend/src/sketch2life/infrastructure/identity/bootstrap_platform_admin.py`
- `backend/src/sketch2life/infrastructure/persistence/be1_models.py`
- `backend/src/sketch2life/infrastructure/persistence/be1_bootstrap.py`
- `backend/alembic/versions/20261110_ar_0001_account_roles.py`
- `backend/src/sketch2life/interfaces/http/routers/be1_registry.py`
- `backend/src/sketch2life/interfaces/http/routers/auth_registration.py`
- `backend/src/sketch2life/interfaces/http/routers/platform_admin_accounts.py`
- `backend/src/sketch2life/interfaces/http/routers/be1_common.py`
- `backend/src/sketch2life/interfaces/http/routers/lesson_library.py`
- `backend/src/sketch2life/interfaces/http/router_composition.py`
- `backend/src/sketch2life/interfaces/http/app.py`

### Parent Android

- `apps/mobile/src/app/AppRoot.tsx`
- `apps/mobile/src/features/auth/ParentAuthScreen.tsx`
- `apps/mobile/src/infrastructure/auth/AuthSessionPort.ts`
- `apps/mobile/src/infrastructure/auth/firebaseAuthSession.ts`

### Teacher Web

- `apps/teacher-ui/src/App.tsx`
- `apps/teacher-ui/src/services/authService.ts`
- `apps/teacher-ui/src/pages/LoginPage.tsx`
- `apps/teacher-ui/src/components/TeacherLayout.tsx`

### Management Web

- `apps/admin-ui/vite.config.ts`
- `apps/admin-ui/src/App.tsx`
- `apps/admin-ui/src/services/authService.ts`
- `apps/admin-ui/src/services/be1Client.ts`
- `apps/admin-ui/src/services/userService.ts`
- `apps/admin-ui/src/pages/LoginPage.tsx`
- `apps/admin-ui/src/pages/UsersPage.tsx`
- `apps/admin-ui/src/components/AdminLayout.tsx`

### Shared setup

- `compose.yaml`
- `.env.example`

Any additional source path, live Firebase action, Docker lifecycle action, test addition/execution, commit or push requires a separate authorization or a plan addendum before that action.

### Rev63 scope addendum — Docker bootstrap environment

- Add only the `compose.yaml` mapping for `SKETCH2LIFE_PLATFORM_ADMIN_BOOTSTRAP_EMAIL`; remove forwarding of the retired `SKETCH2LIFE_PLATFORM_ADMIN_SUBJECTS` allowlist.
- This passes the existing root `.env` bootstrap setting to the API container so the approved one-time Platform Admin command can run in the same Docker environment. No service lifecycle, account creation, migration, secret value, test, commit or push is included.
- Owner authorization: prior direct instruction in this conversation to configure Firebase/auth through Docker using one repository-root `.env`, combined with the current request for the first Platform Admin bootstrap flow.

### Rev63 scope addendum — end-to-end acceptance run

- Run a manual end-to-end acceptance pass for the implemented role/auth flows using synthetic identities only: Parent registration and `/me`, Parent/Teacher/management role gates, Platform Admin bootstrap and account CRUD, Firebase password reset/change where provider configuration allows, and the Docker-backed account-role migration.
- Docker services may be started for this run. Preserve services/volumes already running before the task. Use a dedicated disposable PostgreSQL database named with `rev63_e2e`; never drop or reset the shared development database. Remove only the dedicated database and Firebase identities created by this run when cleanup is supported.
- Do not create or use child profiles/media. Do not expose `.env`, service-account material, passwords, tokens, reset codes, or email action links. Do not send mail to a real recipient; use a reserved synthetic email domain and Firebase action-code APIs where available.
- No test source files, deployment, production Firebase actions, commit, or push are included. Record each pass/block/failure and cleanup result in the existing Rev63 evidence artifact.
- Owner authorization: direct request in this conversation on 2026-11-10 to test the end-to-end role/auth flow.
