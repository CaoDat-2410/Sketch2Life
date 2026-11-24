# Parent seed-account check — Rev24

Date: 2026-11-19  
Branch: `feature/fe-mobile-remediation`  
`origin/dev`: `a43c2aee71160926b3d7979a0235f39d735ead1c` (already an ancestor of this branch)

## Finding

The new seed code is present in `origin/dev` and already included in this branch. It was added by `b945fb45` (`feat(FEAT-066): B seed: SEED-1 S1 core data, seed design D-066-80, goal v2 program, SEED-7a`). It creates synthetic BE1 principals and related database rows, including five Parent principals, Parent profiles, lesson-library data, grants, and sample StoryRuns.

These are **database principals, not Firebase login accounts**. They use the seed issuer `urn:sketch2life:seed:issuer`; the seed package contains no Firebase user creation, email, or password for those Parent principals. The Firebase Admin account provisioner found elsewhere in the source is a generic account-provisioning adapter, not a seeded Parent credential.

## Current database

A read-only count against `s2l-feat081-rev23-postgres-1` found **0** rows in `be1_adult_identities` for the seed issuer and `seed-parent-*` subjects. No seed write was attempted.

The seed guard explicitly requires `auth_provider=development`, `ai_provider=disabled`, and no Firebase project/admin credential. The running Parent API is configured for Firebase authentication and Modal workloads, and its Postgres database is the active application database. Applying the development seed to this DB would both violate the guard and produce identities whose issuer does not match the Firebase-authenticated Parent. I did not bypass the guard or write directly to the database.

## Runtime and emulator check

- Parent API `/health`: HTTP 200.
- Runtime OpenAPI contains Parent profile CRUD, topic suggestions, activity suggestions, and story revision routes.
- `/v1/story-runs/{run_id}/cancel` is callable at the runtime router but absent from the served OpenAPI document; track this as an API contract visibility mismatch.
- Current shell could not locate `adb` on PATH or under the standard Android SDK path, so no new emulator session was started from this turn.
- The existing evidence screenshots remain `screenshots/01-after-config-restart.png` and `screenshots/02-signup-form.png`. The earlier root `.env` resolver fix was verified to expose the public Firebase config and API origin to Expo without copying `.env` into the worktree.

## E2E result

**Full authenticated Parent flow was not run.** The dev seed is not a usable sign-in account; no Firebase Parent credentials were found or created. No authenticated request, Modal inference, quota action, or direct database mutation was sent in this check. Therefore this does not establish an end-to-end pass.

Earlier static validation for the current worktree reported mobile typecheck clean and 121 mobile tests passing; those checks do not substitute for authenticated emulator E2E.

## 2026-11-20 — real Android E2E rerun (supersedes the runtime/emulator statement above)

The Android emulator **was online and used** (`emulator-5554`). The Rev24 `origin/dev` seed still does not provide Firebase login accounts; it is development-only PostgreSQL seed data and its guard was not bypassed. A fresh synthetic Parent was registered through the real Expo app after starting the API with the single root `<local-machine-path>; no secret values were copied or recorded.

The real UI flow passed signup/auth, synthetic profile creation, topic suggestions, subject suggestions, run creation, Qwen3.5 drawing understanding, adult subject confirmation, and context confirmation. It then **blocked at activity suggestion**. Detailed status/API crosswalk: `API_WORKFLOW_RESULT_20261120.md`.

The activity route first failed because its Modal app was not deployed, next because `parent.activity.suggest` was missing from the L4 worker allowlist, then after the approved allowlist fix and redeploy the one recovery call timed out at 1,800 seconds during `model_inference`. No selection receipt was produced; story and video were not invoked. We did not tap retry again or manufacture an activity selection. The language/audio and drawing Modal apps used for this run were stopped; video app was untouched. Task Compose containers and Metro were stopped without deleting volumes; the emulator remains online. The final Android screen is `screenshots/activity-after-timeout.png`.

This is a partial real E2E, not a full-flow pass. `logs/activity-modal-timeout.md` records the sanitized worker boundary and `logs/api-e2e-events.log` records the exercised API outcomes.
