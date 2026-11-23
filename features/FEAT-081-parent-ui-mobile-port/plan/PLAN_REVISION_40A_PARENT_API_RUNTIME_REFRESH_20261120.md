# FEAT-081 — Plan Revision 40A: refresh the task API runtime

- **Status:** APPROVED under the owner's continuing 2026-11-20 request to fix and exercise the real Parent flow.
- **Parent plan:** Plan Revision 40, Addendum 64. This only authorizes the local runtime step required to exercise its already-approved single UI inference; it adds no code boundary or AI-call allowance.
- **Feature/worktree:** FEAT-081, `feature/fe-mobile-remediation`, `<local-machine-path>

## 1. Evidence

- Docker reports `s2l-feat081-rev23-api-1` as healthy on `127.0.0.1:58100`.
- `docker inspect` reports no source bind mounts. Its Compose labels identify project `s2l-feat081-rev23`, `compose.yaml`, and the existing Rev23 override under `evidence/ANDROID_PARENT_ACTIVITY_STORY_VIDEO_E2E_REV23_20261119/compose.rev23.override.yaml`.
- The changed backend source therefore is not yet running in the healthy API container. The Compose stack uses the existing `<local-machine-path>; do not read values into output or modify that file.

## 2. Authorized runtime operation

- Using the same two Compose files and existing external volumes, rebuild and recreate only service `api` for project `s2l-feat081-rev23`, with `--no-deps`.
- Do not recreate/restart Postgres, MinIO, ClamAV, Redis, Expo/Metro, or any other Modal app. Do not remove or rename containers/volumes.
- Do not run migrations, seed data, alter environment/secrets, or print Compose-resolved environment.
- Verify the recreated API container is healthy and `/health` responds on `127.0.0.1:58100` before the already-approved Rev40 Android UI attempt.
- This refresh does not add a request. Rev40's one activity UI request remains the only activity inference allowance. If the API fails health or the approved inference fails, stop and record evidence.

## 3. Exact file boundary

- `features/FEAT-081-parent-ui-mobile-port/plan/PLAN_REVISION_40A_PARENT_API_RUNTIME_REFRESH_20261120.md`
- `features/FEAT-081-parent-ui-mobile-port/approvals/TASK_APPROVAL.md`
- `features/FEAT-081-parent-ui-mobile-port/status/STATUS.md`
- `features/FEAT-081-parent-ui-mobile-port/evidence/PARENT_API_AUTH_FULL_E2E_REV24_20261119/REV32_AUTH_RECOVERY_AND_E2E/`

No source, Compose, `.env`, database, migration, account, or seed changes are authorized by this runtime-only addendum.
