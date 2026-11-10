# FEAT-077 Context — Parent account edit entry point

- Owner request: keep the outer settings area organized into “Tài khoản & cài đặt” and “Bảo mật”, and add an edit/settings icon beside the parent identity card.
- Worktree: F:/Github/Sketch2Life-worktrees/fe-ui-full-remediation.
- Product baseline: FEAT-063 SRS v2.7-draft Rev57 is the unsigned working baseline. This is a presentation/navigation refinement; no product requirement changed.
- Parent web: both outer category rows remain present; the account row and adjacent edit icon open the existing account form. The security and child-profile destinations remain available.
- React Native: the settings screen mirrors the parent identity card, role, edit entry, and the two categories. Parent name/email edits update only the in-memory local demo snapshot.
- Responsive detail: at phone widths, the parent role chip moves below the name/email so identity text has room; the edit action remains a 44×44 control. Tablet retains a single-row card.
- Data boundary: no API, auth provider, or persistent account mutation was introduced.
- Validation: Parent UI and mobile TypeScript checks pass. Browser preview evidence covers phone (390×844), tablet (768×1024), the scrolled phone settings rows, and the web edit action. No native emulator visual run was available in this task.