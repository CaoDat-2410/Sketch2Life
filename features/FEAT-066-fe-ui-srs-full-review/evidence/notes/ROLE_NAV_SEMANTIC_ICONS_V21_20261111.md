# FEAT-066 EV-024 — Semantic monochrome crayon navbar icons (Rev21)

- Date: 2026-11-11 (Asia/Bangkok).
- Plan: revision 21, SHA-256 `D97702B032B44573A9733F3978A175EF0C9EF45A50AF5D5A88A673192104FFE2`; matching direct-user authorization is recorded in `approvals/TASK_APPROVAL.md`.
- Worktree/branch: `F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation`, `codex/fe-ui-web-remediation`.
- Product reference: FEAT-063 SRS v2.7-draft Rev57, SHA-256 `BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5`; unsigned and awaiting owner sign-off. This change is a navigation affordance correction, not a new SRS behavior.
- Design workflow: `frontend-design` and `ui-ux-pro-max`; reuse the local SVG system and preserve the app's rounded crayon character.

## Changes

- Updated the semantic SVG paths and the navbar mappings in the shared renderer and three role shells.
- Teacher: overview/home; classes and students/users; teaching group/classroom board; lesson management/book; AI assisted/wand; sample video/video; projection/projector; public library/library; history/reports/history; profile/user; settings/gear; quota/gauge; role/teacher; notifications/bell; logout/exit.
- School Manager: overview/home; teachers and groups/users; classes and capacity/classroom board; quota/gauge; public review/shield; settings/gear; school context/school; notifications/bell; logout/exit.
- Platform Admin: overview/home; organizations/building; lesson library/library; activity catalog/catalog grid; quota and policy/sliders; audit log/audit document; platform role/shield; notifications/bell; logout/exit.
- Navigation and notification glyphs use one `currentColor` outline, rounded caps/joins, no emoji and no internal colored fill. The containing active/inactive icon surface retains its existing state styling. Page-content icon appearance, labels, routes, actions, roles, dimensions, and hit targets were not changed for this revision.

## Manual preview

- Local preview was captured with isolated headless Chrome, allowing HTTP only to loopback ports `127.0.0.1:5172`, `:5173`, and `:5174`.
- Nine screenshots are in `screenshots/role-nav-icons-v21/`: each role at 1440x900 and 390x844, plus dark desktop at 1440x900. `capture_role_nav_semantic_icons_v21.mjs` is the capture script; `observations.json` holds per-capture measurements.
- All nine were visually inspected. Observed navigation icon counts: Teacher 16, School Manager 10, Platform Admin 9. Every notification affordance rendered as a bell outline.
- All captures: `horizontalOverflow: false`, `viteError: false`; browser `runtimeExceptions` is empty.
- This is local visual preview evidence only; no authenticated service or real user/child data was used. No screen-reader device audit was performed.

## Validation and limits

- `git diff --check`: passed.
- Per the user's instruction, no automated tests or build were added or run. No backend/API, mobile/Parent, external provider, dependency, or package changes; no commit or push.
- The separate Rev20 Teacher layout proposal remains pending user review and was not implemented by this icon task.