# FEAT-066-EV-015 — Three-role web logout visibility and interaction

Date: 2026-11-10 (Asia/Bangkok)
Plan: revision 13, SHA-256 5DF172969F85296D5A1100BB288337CD0EEFF06373CC157DE719EA59B3C6029B
Approval: recorded in approvals/TASK_APPROVAL.md before app code changes
Worktree/branch: F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation, codex/fe-ui-web-remediation

## Implementation

- Teacher: moved the existing shell logout action from the top bar to the bottom of the sidebar beside the account profile. The collapsed sidebar shows a 48×48 logout icon button with a role-specific accessible name and title.
- School Manager: retained the existing labeled sidebar logout control beside the profile. It was already present and visible in the current shell.
- Platform Admin: added a sidebar logout control and passed the existing context logout handler through AdminPortalFrame to AdminLayout. The collapsed sidebar shows a 48×48 logout icon button with a role-specific accessible name and title.
- All three controls use the existing logout handler, which clears s2l-web-role and s2l-web-authenticated and returns through the existing route guard. The existing optional auth bridge behavior is unchanged.

## Manual review

Evidence screenshots and observations are in screenshots/web-logout-v13/:

- Teacher: teacher-dashboard-desktop.png and teacher-dashboard-narrow.png
- School Manager: school-manager-dashboard-desktop.png and school-manager-dashboard-narrow.png
- Platform Admin: platform-admin-dashboard-desktop.png and platform-admin-dashboard-narrow.png
- Machine-readable results: observations.json

At 1440×900 and 390×844, all three logout controls were visible and inside the viewport. Document widths were 1430–1440px on desktop and 390px on narrow viewports; none overflowed horizontally. Each control is a native button with an accessible name and a visible 3px cobalt focus outline. The School Manager button retains its visible label at 390px; Teacher and Platform Admin use a recognizable 48×48 icon button in the collapsed rail while retaining their accessible names.

A local pointer activation of each logout control returned its app to /login and cleared both role/auth session keys. No Vite overlay or runtime errors were observed. Per-origin preview storage was restored after capture. The interaction used temporary local preview state only, without credentials, backend auth, production data, or external services.

No automated tests or builds were run. No commit or push was made.