# PR #27 conflict resolution record

- Evidence ID: `FEAT-071-E01`
- Date: 2026-11-16 (Asia/Bangkok)
- Reviewer/operator: Codex, at the project owner's request
- PR: https://github.com/CaoDat-2410/Sketch2Life/pull/27
- PR head before resolution: `f13726bb2325ffd0e7f90e5c7e0221853167cbc0`
- Base `dev` before resolution: `c87d8008b70910eb0a4d3579b9490312e7e3143f`
- Common ancestor: `1431ef81972b71303fd4a7909748fd3005769a3c`
- Initial PR state: open, unmerged, base `dev`; GitHub reported the branch was not mergeable.
- Product authority consulted: `docs/context/SRS_AUTHORITY.md`; canonical working SRS is FEAT-063 v2.7-draft Rev60 and remains unsigned. No product requirement or SRS text was changed.

## Method

Fetched both parent trees into a temporary repository under the writable workspace and ran a real `git merge --no-commit --no-ff dev` with the PR head checked out. This exposed 19 unmerged paths. Resolved the merge in that isolated worktree, kept the PR head as first parent and `dev` as second parent, and left the PR base unchanged. The old linked worktree outside the writable workspace was not touched.

## Conflict inventory and resolution

| # | Initially unmerged path | Resolution |
|---:|---|---|
| 1 | `approvals/TASK_APPROVAL.md` | Retained the append-only records from both parent histories and appended the FEAT-071 task approval. No earlier approval section was rewritten. |
| 2 | `apps/admin-ui/src/App.tsx` | Kept the old portal directory removed as required by the single-web migration. Its current role routing is handled by `apps/web`; account management is routed to the migrated Platform Admin page. |
| 3 | `apps/admin-ui/src/components/AdminLayout.tsx` | Kept the old layout removed. Ported the shared password-change action into `apps/web/src/shared/WebAppShell.tsx`. |
| 4 | `apps/admin-ui/src/pages/LoginPage.tsx` | Kept the old login page removed. The shared `/login` flow now verifies all selected roles through the backend and provides account-neutral Firebase password recovery. |
| 5 | `apps/admin-ui/src/pages/UsersPage.tsx` | Moved the current account-management page to `apps/web/src/modules/platform-admin/pages/UsersPage.tsx` and connected it to the shared backend API. |
| 6 | `apps/admin-ui/src/services/userService.ts` | Kept the old service removed and mapped its list/create/update operations to typed Platform Admin methods in `apps/web/src/shared/backendApi.tsx`. |
| 7 | `apps/mobile/android/app/build.gradle` | Restored from `dev` as part of the complete `apps/mobile` tree; the web migration does not own mobile. |
| 8 | `apps/mobile/babel.config.js` | Restored from `dev` with the rest of the mobile app. |
| 9 | `apps/mobile/package.json` | Restored from `dev`; retained its root workspace and lockfile importer entries. |
| 10 | `apps/mobile/src/app/AppRoot.tsx` | Restored from `dev` with the complete mobile source tree. |
| 11 | `apps/mobile/src/infrastructure/auth/AuthSessionPort.ts` | Restored from `dev`; kept the mobile auth boundary intact. |
| 12 | `apps/mobile/src/infrastructure/auth/README.md` | Restored from `dev` with its implementation notes. |
| 13 | `apps/teacher-ui/src/App.tsx` | Kept the legacy portal removed and routed the current T13 AI lesson workflow through `apps/web/src/modules/teacher/App.tsx`. |
| 14 | `apps/teacher-ui/src/components/TeacherLayout.tsx` | Kept the legacy layout removed; carried its current T13 destination into the consolidated Teacher navigation. |
| 15 | `apps/teacher-ui/src/pages/LoginPage.tsx` | Kept the old login page removed; password recovery is available in the shared login flow. |
| 16 | `apps/teacher-ui/src/services/authService.ts` | Kept the duplicate service removed; the consolidated app uses the shared Firebase auth service for login, token, recovery, and password change. |
| 17 | `apps/teacher-ui/vite.config.ts` | Kept the legacy config removed; the consolidated `apps/web/vite.config.ts` already reads repository-root environment values through `envDir`. |
| 18 | `backend/tests/contract/test_app_composition.py` | Kept the `dev` expected route adjustments and mounted-route view, while retaining the PR's unprojected OpenAPI view; the test now compares both views before the expected route-set assertions. |
| 19 | `pnpm-lock.yaml` | Retained the `dev` `apps/mobile` importer and package graph alongside the existing PR lockfile content. Added `apps/mobile` to `pnpm-workspace.yaml`; kept `apps/ui-mobile` and `packages/art-renderer`. `apps/web` remains a standalone npm package with its own `package-lock.json`, as on the PR branch. |

The `dev` additions `apps/teacher-ui/src/components/TeacherDeckPresentation.tsx`, `apps/teacher-ui/src/pages/ModalAiLessonFlowPage.tsx`, and `apps/teacher-ui/src/services/aiWorkflowService.ts` were also carried into the consolidated Teacher module. During the review I found that `apps/web` read `window.sketch2lifeAuth` without initializing it; `apps/web/src/main.tsx` now connects that bridge to the app's Firebase auth service so role verification and authenticated API calls can use the configured account session.

## Validation and limitations

- `python tools/validate_harness.py`: final result `HARNESS_VALID`. The first run identified missing required evidence subdirectories in FEAT-070 and FEAT-071; added the required empty directory placeholders (`.gitkeep`) and reran successfully. The FEAT-070 change is repository harness scaffolding only.
- `python tools/validate_repository_security.py`: `REPOSITORY_SECURITY_VALID`, 7,487 publishable files scanned; environment files, seed accounts, credentials/signing keys, and external reference documents excluded; no absolute machine paths found.
- `python tools/validate_architecture.py`: `ARCHITECTURE_VALID`; dependency direction, mobile feature isolation, frontend asset gate, mobile AI boundary, and Firebase data-product checks passed.
- `git diff --check`: no output on the staged worktree.
- `git diff --cached --check` on the directly resolved paths and FEAT-071 records: no output. The full staged candidate reports 114 historical whitespace findings; its complete warning set matches `git diff --check 1431ef81972b71303fd4a7909748fd3005769a3c c87d8008b70910eb0a4d3579b9490312e7e3143f` exactly. They are inherited from the incoming `dev` history and do not come from these conflict resolutions.
- `pnpm install --lockfile-only --offline --ignore-scripts --frozen-lockfile`: could not start because the bundled Node/pnpm runtime returned `EPERM` while resolving the isolated worktree path. The workspace/importer entries were inspected directly; this command did not establish a pnpm install result.
- Automated application tests and builds were not run under the approved task scope.

## Publication closeout

The merge commit was pushed with a regular, non-force `git push` to `codex/fe-ui-web-remediation`; GitHub accepted it as a fast-forward from the original PR head. The GitHub connector's direct blob write returned `403 Resource not accessible by integration`, so publication used the configured Git transport instead.

- Merge commit now on the PR branch: `417410486dde0e660e37dacab26ed07b2f7b948d`.
- Parents: first `f13726bb2325ffd0e7f90e5c7e0221853167cbc0` (original PR head), second `c87d8008b70910eb0a4d3579b9490312e7e3143f` (`dev`).
- Post-push PR metadata: state `open`, `merged=false`, base `dev`, head `417410486dde0e660e37dacab26ed07b2f7b948d`, `mergeable=true`.
- The branch update did not merge the PR into `dev`; no PR merge action was invoked.
- At the metadata snapshot, the PR-triggered `CI` workflow run `43864760305` was `in_progress`; the commit had no combined status entries yet.

## Rev2 owner instruction and merge attempt

After Rev1 publication, the owner directly authorized merging PR #27 into `dev` and said the current CI errors can be handled later. This instruction supersedes Rev1's earlier no-merge boundary. Rev2 approval and plan addendum are recorded in this feature folder and in the root approval register before the merge request.

- PR head at the start of Rev2: `8eb5415da1bea69d2018320e2ad7c465778a44a4`; base remains `dev` at `c87d8008b70910eb0a4d3579b9490312e7e3143f`.
- Latest observed PR metadata before this addendum: open, unmerged, `mergeable=true`.
- CI run `43865121003` (`CI`, run 179) showed `Repository policy checks` failed because the active Android app uses application ID `com.sketch2life.parentexpo.dev` while `tools/validate_skeleton.py` requires `com.sketch2life.mobile`; `Backend unit and contract tests` failed during dependency setup because `backend/uv.lock` needs updating for `backend/pyproject.toml`; the Web UI job was still running in the latest inspected snapshot.
- The owner authorized proceeding with these checks not green. The planned action is GitHub's standard merge operation against the exact current PR head. No required checks or branch protection will be bypassed. The resulting GitHub merge response will determine and record whether the operation succeeded or was blocked.
