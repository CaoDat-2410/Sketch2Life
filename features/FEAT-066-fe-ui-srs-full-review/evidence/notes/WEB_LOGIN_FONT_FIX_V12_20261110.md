# FEAT-066-EV-014 — Shared web login Vietnamese font correction

Date: 2026-11-10 (Asia/Bangkok)
Plan: revision 12, SHA-256 00D41575B3D5912DE9A2CB2D1080DC9D588C91E366D762B79092DC7F618FBCC7
Approval: recorded in approvals/TASK_APPROVAL.md before app code changes
Worktree/branch: F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation, codex/fe-ui-web-remediation

## Change

The shared login headline in apps/shared/portal-login.css used Georgia with tight tracking and an italic accent span. Replaced that title treatment with the login shell's existing Be Vietnam Pro, Segoe UI, system-ui, sans-serif stack, 700 weight, normal accent style, looser tracking, and a 1.08 line height so Vietnamese combining marks remain clear. No font import, dependency, route, copy, layout redesign, or auth change was added.

## Manual review

Captured the shared login pages from loopback previews at 1440×900 and 390×844:

- Teacher: screenshots/web-login-font-v12/teacher-login-desktop.png, teacher-login-narrow.png
- School Manager: screenshots/web-login-font-v12/school-manager-login-desktop.png, school-manager-login-narrow.png
- Platform Admin: screenshots/web-login-font-v12/platform-admin-login-desktop.png, platform-admin-login-narrow.png
- User-provided before reference: screenshots/web-login-font-v12/teacher-login-before-user.png
- Machine-readable observations: screenshots/web-login-font-v12/observations.json

All six previews remained on /login, used the expected role-specific Vietnamese headline, and had no horizontal overflow. The 390px captures reported document width 390px; desktop document widths were 1440px (Teacher and School Manager) and 1430px (Platform Admin) inside 1440px viewports. Captured CSS reported the shared sans-serif stack, font weight 700, normal style, and 1.08 line-height; the emphasized phrase inherited the same values. No Vite error overlay or runtime errors were observed. Visual inspection confirmed the headline diacritics align cleanly at both sizes.

The screenshot session temporarily cleared only per-origin preview storage to show login pages, then restored each origin's original local/session storage. It used no credentials, authenticated backend, production data, or external provider.

No automated tests or builds were run. No commit or push was made.