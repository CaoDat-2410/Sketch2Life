# FEAT-066-EV-013 — Three-role dashboard icon refresh

Date: 2026-11-10 (Asia/Bangkok)

## Authority and approval

- Canonical source: docs/context/SRS_AUTHORITY.md points to features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md.
- Baseline: FEAT-063 v2.7-draft Rev57, SHA-256 BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5; awaiting owner sign-off. §32 was not used as a product requirement.
- SRS §3 web-role mapping: Teacher (teacher), School Manager (school_manager), Platform Admin (platform_admin). Parent and the additional Admin UI surface are outside this dashboard change.
- Worktree/branch: F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation, codex/fe-ui-web-remediation.
- Plan revision 11 SHA-256: 0B2B90980B2D2CB491DCCC15BC1E22ED6FFCEBD3D8B21AEADE795670B9875BC1; matching direct user approval was recorded before app changes.

## Implementation

- Added apps/shared/RoleDashboardIcon.tsx as the shared local SVG set: rounded strokes, restrained duotone fills, consistent sizing and existing palette colors.
- Re-exported the set through Icon.tsx and MgIcon.tsx for School Manager, Teacher and Platform Admin so navigation, shell and route content use the same glyph shapes.
- Added 32×32 cobalt-compatible navigation icon tiles and active-state foreground styling. Teacher navigation now uses the same tile treatment as the other two dashboards.
- Existing labels, route targets, role checks, actions and accessible names remain in place. SVGs remain decorative (aria-hidden). Shared glyphs are reused by the three login pages, so their icon artwork follows the same set; login layout and auth behavior were not changed.
- No dependencies, manifests, lockfiles, APIs, backend, mobile, Parent, or additional Admin UI files were changed for this work.

## Manual review

The three local fixture routes were inspected in a browser at 1440×900 and 390×844:

| Role | Route | Captures |
|---|---|---|
| School Manager | /m02-organization-management | school-manager-dashboard-desktop.png, school-manager-dashboard-narrow.png |
| Teacher | /t01-lesson-workspace | teacher-dashboard-desktop.png, teacher-dashboard-narrow.png |
| Platform Admin | /a02-platform-operations | platform-admin-dashboard-desktop.png, platform-admin-dashboard-narrow.png |

- All six captures have no horizontal overflow and no Vite error overlay.
- Runtime error count was 0; the active navigation icon tile measured 32×32 px in each role and viewport, with a white glyph on cobalt.
- Teacher's document width was 1430 px at a 1440 px viewport; the 390 px narrow capture measured 390 px.
- Screenshots and observations: evidence/screenshots/web-dashboard-icons-v11/observations.json. The pre-icon visual baseline is in EV-012.
- Previews used local synthetic role state and loopback-only servers on ports 5172, 5173 and 5174. No real credentials, backend requests or production data were used.
- No automated tests or builds were run. Changes remain uncommitted and unpushed.