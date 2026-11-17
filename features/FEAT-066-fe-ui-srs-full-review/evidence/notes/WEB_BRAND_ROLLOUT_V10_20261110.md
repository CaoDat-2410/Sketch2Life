# FEAT-066-EV-012 — User logo and bright palette across browser UIs

Date: 2026-11-10 (Asia/Bangkok)
Worktree: `F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation`
Branch: `codex/fe-ui-web-remediation`
Plan: revision 10, SHA-256 `9EA74203319688B6E4D456E3CB278DB7BA314F423AC0BF7581D802807255269D`; matching direct-user approval is recorded in `approvals/TASK_APPROVAL.md`.
Canonical product source: FEAT-063 SRS v2.7-draft Rev57, SHA-256 `BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5`; unsigned. The SRS does not prescribe these colors.

## Change

Applied the user-provided image unchanged as the shared browser brand mark and on the existing Admin sidebar/login and Parent login splash. Source SHA-256: `86010669F03972BC1273DC02BEB8F34B39BD5E47C00771B2632003C1D62F9042`. Local copy: `apps/shared/assets/sketch2life-brand-art-20261110.jpg`.

Applied Cool Grey + Cobalt across the five existing browser apps (`parent-ui` preview, `school-manager-ui`, `teacher-ui`, `platform-admin-ui`, and `admin-ui`) and shared web styles: canvas `#EEF0F3`, secondary surface `#E2E5EA`, raised surface `#FFFFFF`, ink `#0B0C0E`, muted `#5D6470`, action `#1F2DE6`, hover `#1B25C5`, pale action tint `#E8EAFF`. Existing success, warning and error meanings are preserved. The visual direction comes from the user's request and the preceding palette preview, not from the unsigned SRS.

The scope excludes all native/mobile packages, historical `parent-web`, backend/API contracts, auth/business logic, credentials, real user/child data and external providers. Parent browser screens are an existing preview; this does not redefine the SRS Parent target as web. Admin UI remains an existing browser interface; this does not add or rename a product role.

## Manual review

Reused loopback Vite apps from this worktree: Teacher `127.0.0.1:5172`, School Manager `:5173`, Platform Admin `:5174`; started Parent preview from this worktree on `:5175`. No main-checkout preview process was used.

Captured 18 screenshots at 1440x900 and 390x844 for existing login and primary screens: School Manager login/M02/M01, Teacher login/T01, Platform Admin login/A02, and Parent auth redirect/P01. Captures and `observations.json` are in `evidence/screenshots/web-brand-rollout-v10/`. Browser observations recorded 0 document-width overflow across all 18 captures; the shared logo loaded in all 14 captures where the shared portal mark is rendered. School Manager M01 request-change, approved and pending controls remained in view at narrow width. The Platform Admin banner and Parent primary story action were reviewed after converting their remaining old gradients.

Parent local preview initializes an authenticated fixture and redirects `/p11-authentication` to `/p01-lesson-library`; the two `parent-auth-redirect` captures therefore show the library and are not evidence of the login screen.

Admin UI implementation is updated, but its local browser preview was not captured: `npm install --offline --ignore-scripts --no-save --package-lock=false` stopped with `ENOTCACHED` because `@tailwindcss/vite` is not in the local npm cache. No network install was attempted. No manifest or lockfile changed. Local auth, real APIs, screen-reader hardware and dark mode were not exercised.

No automated tests or builds ran. No backend/provider calls, credentials, production data, commit or push were used.