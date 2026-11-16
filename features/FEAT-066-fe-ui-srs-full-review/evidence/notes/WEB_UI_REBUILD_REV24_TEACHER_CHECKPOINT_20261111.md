# FEAT-066-EV-028 — Rev24 Teacher UI rebuild and checkpoint

- Date: 2026-11-11 (Asia/Bangkok).
- Worktree/branch: `F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation`, `codex/fe-ui-web-remediation`.
- Plan: Rev24, SHA-256 `072778CC86CCF6C2CDE18CDD034276F75371A4930FF5C18924F58191187BC345`; direct user authorization is recorded before implementation.
- Product baseline: FEAT-063 SRS v2.7-draft Rev57, SHA-256 `BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5`; authority marks it unsigned. Product target is §§1–31; §32 is evidence only.
- Design reference: the reviewed Teacher board and flow/API atlas in FEAT-066 Rev23. No new policy is inferred from the visuals.

## SRS/API boundary

Teacher flow coverage follows SRS §§3, 5.2, 7.3, 20, 21.5–21.6 and 31.5/Q-01:

- Workbench: organization/class assignments and lesson summaries may load from existing APIs after Firebase identity and organization scope are available. No occurrence schedule or quota count is invented.
- Assigned classes and roster: class rows are filtered to active Teacher assignments with matching `class_id`; class detail rechecks the exact class assignment before requesting class, profile and consent data. Profile creation/edit/lifecycle stays unavailable. The local preview makes no API request and renders no class or child rows.
- Học liệu: existing Lesson Library list/detail/create/update/archive/public-review methods remain the only action boundary. New lesson form starts without an assumed age-band reference/version. Public review is described as a request that enters Manager review, not as publication.
- Document import: existing upload session, part, status/recovery and extracted-revision reads remain. The interface does not claim that extraction was corrected or confirmed into a new immutable lesson revision; that contract is still missing.
- Buổi dạy/Sketch Deck, server-selected one-child sample, context/transcript confirmation, StoryRun, job/reconciliation, quota, safe playback, class projection and run lifecycle remain unavailable. Q-01 selection policy stays open; no Teacher-picked roster fallback is shown.
- History, inbox/unread state, feedback thread/reply, Teacher profile/settings have no corresponding current FE API surface and remain explicitly unavailable.
- The dashboard reports no quota count or unread badge. The shared local-preview notice no longer claims sample data is present; it says that Firebase/backend calls and persistence are disabled.

No Parent/Manager/Admin behavior, backend, contract, package or lockfile was changed for this section. No child image, story, transcript or video is shown. The preview used no credentials, real user/child data, authenticated API or production/provider service.

## Implementation

- Added the Teacher role rail and responsive layout in `apps/teacher-ui/src/components/TeacherPortalLayout.tsx`, plus the Rev24 paper/crayon styles in `apps/teacher-ui/src/styles/teacher-rebuild.css`.
- Replaced the active dashboard route with `TeacherWorkbenchPage`; the workbench is API-backed when configured and otherwise displays a clearly labeled no-data preview.
- Added reusable SRS/API-unavailable pages for sessions, activities, sample video, projection, quota-related dependencies, history, inbox, profile and settings.
- Active class list/detail routes use the existing class/profile/consent APIs with exact active class-assignment gating. The previous local-preview roster branch is no longer used by the app route.
- Updated Lesson Library entry actions, import-file label/layout, and shared API-mode copy. No backend/API methods were added.

## Manual local review

`capture_teacher_rev24.mjs` used isolated headless Chrome with a synthetic `TEACHER` session flag only. Network requests were restricted to `127.0.0.1:5172`; other HTTP(S) requests were blocked. The 24 PNGs are in `evidence/screenshots/teacher-rev24/`, covering 12 routes at 1440×900 and 390×844:

`/t01-lesson-workspace`, `/t05-classes-and-children`, `/t02-lesson-authoring`, `/t03-document-import-review`, `/t04-session-sketch-deck`, `/t06-sample-story-run`, `/t07-video-presentation-confirmation`, `/t08-settings`, `/t09-history`, `/t10-inbox`, `/t11-profile`, and `/t12-activities`.

- All 24 captures report no horizontal document overflow or Vite error overlay. No runtime exceptions were observed.
- The capture found no local preview markers for a teacher name, class or school. No fixture rows, sample child, quota count, unread count or fake success is shown.
- Narrow navigation keyboard review: Tab focuses the menu button; Enter expands the drawer and moves focus to “Tổng quan”; Escape closes it, hides the drawer and restores focus to the menu button. The current navigation link exposes `aria-current="page"`.
- Desktop/narrow screenshots were inspected, including workbench, classes, lessons, import and unavailable routes. File selection and API mutation were not activated.

This is a local presentation/source checkpoint, not authenticated API validation. Class scoping and endpoint wiring were source-reviewed only because no Firebase identity or backend was configured. No dedicated screen-reader device/session was used. No automated tests/builds, commit or push.

Teacher is complete for this section. Next: rebuild School Manager and review it before starting Platform Admin.
