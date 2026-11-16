# Paper-and-crayon content canvas — Rev26

## Scope and authority

The user's direct request authorizes a paper/crayon backdrop matching the Rev23 UI boards. Canonical product requirements remain FEAT-063 SRS v2.7-draft Rev57, SHA-256 `BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5`; the draft is unsigned. The Rev23 boards are visual references only.

Plan Rev26 SHA-256: `247E06100BD2506B1872EBA47E71549ACE8DFDC200614320464933A428800B38`. Matching approval is recorded in `approvals/TASK_APPROVAL.md` before source changes.

## Approved implementation scope

Add a restrained CSS-native paper texture and sparse crayon corner marks behind authenticated content canvases in Teacher, School Manager and Platform Admin. Preserve the accepted shell, cards, typography, routes, API/authorization behavior and privacy boundaries. Exclude Auth, Parent/mobile, backend, external assets, packages, tests/builds, commit and push.

## Review record

Completed the CSS-only background pass in `apps/shared/role-crayon-theme.css`. The shared role content canvases now use a subtle warm paper grain, soft corner washes, and sparse crayon strokes. The strokes are decorative, pointer-transparent, and remain behind cards and controls; the narrow layout simplifies them to two lower-corner marks. No route, card, shell, typography, API, authorization, or privacy behavior was changed.

Manually inspected all 12 loopback captures in `evidence/screenshots/paper-crayon-background-rev26/` at 1440×900 and 390×844. The paper surface fills the visible content canvas on desktop and narrow screens; corner marks sit outside the card content and remain legible against the page.

| Role | Overview route | Representative route | Captures |
|---|---|---|---|
| Teacher | `/t01-lesson-workspace` | `/t05-classes-and-children` | `teacher-overview-1440.png`, `teacher-overview-390.png`, `teacher-classes-1440.png`, `teacher-classes-390.png` |
| School Manager | `/m02-organization-management` | `/m02-organization-management?section=finance` | `manager-overview-1440.png`, `manager-overview-390.png`, `manager-finance-1440.png`, `manager-finance-390.png` |
| Platform Admin | `/a02-platform-operations` | `/a02-platform-operations?panel=queues` | `admin-overview-1440.png`, `admin-overview-390.png`, `admin-queues-1440.png`, `admin-queues-390.png` |

`observations.json` records that all 12 captures have `documentWidth` equal to viewport width, `horizontalOverflow: false`, `viteError: false`, `paperCanvas: true`, and `crayonCornerLayer: true`. All three roles report empty runtime-exception and console-error arrays. For each narrow drawer, Enter opens it, focuses the first navigation item and exposes logout; Escape closes it and returns focus to the trigger. The preview helper allowed HTTP only to each app's own loopback port (Teacher 5172, Manager 5173, Admin 5174); no product API or external service was called.

No automated tests or builds were run. Auth, Parent/mobile, backend, external assets, package files, commit and push were untouched.
