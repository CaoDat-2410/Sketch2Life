# FEAT-067 web source inventory

## Migrated sources

| Working-tree source before retirement | Active destination | Source files accounted for |
| --- | --- | ---: |
| `apps/teacher-ui/src` | `apps/web/src/modules/teacher` | 28 |
| `apps/school-manager-ui/src` | `apps/web/src/modules/school-manager/preview` | 23 |
| `apps/platform-admin-ui/src` | `apps/web/src/modules/platform-admin` | 23 |
| `apps/admin-ui/src` | `apps/web/src/modules/school-manager/be1` | 95 |
| `apps/shared` | `apps/web/src/shared` | 17 |
| `apps/teacher-ui/docs` | `apps/web/docs/source-portals/teacher` | 15 |
| `apps/admin-ui/docs` | `apps/web/docs/source-portals/admin-ui` | 7 |

The old per-portal `main.tsx` files were replaced by the one `apps/web/src/main.tsx`; Vite configuration, HTML, package manifest, and lockfile were consolidated. The Teacher and BE1 public assets had two same-name collisions (`favicon.svg`, `icons.svg`); both pairs were byte-identical. Three unimported shared CSS files (`parent-ui.css`, `portal-redesign.css`, `portal-storybook.css`) were kept under `apps/web/docs/source-portals/shared/reference-only`, outside active source.

## Runtime route map

- `/login`: central role entry.
- `/teacher/*`: Teacher portal and its existing login/backend/local-preview behavior.
- `/school/login` and `/school/*`: Firebase/BE1-backed organization-admin UI; current API-backed capability is class list/create and unsupported actions remain unavailable.
- `/school/preview/*`: fixture-only M01/M02 preview; it remains explicitly non-persistent.
- `/platform/*`: Platform Admin and Content Admin-permission UI.

One `BrowserRouter`, one `src/main.tsx`, and one Vite `index.html` remain. Portal CSS selectors are scoped by the `html[data-portal]` marker; differing `s2l-float-slow` keyframe names were also separated per portal because keyframe identifiers are document-global.

## Retired and preserved paths

After confirming every source path/import and the public asset collisions, removed exactly `apps/teacher-ui`, `apps/school-manager-ui`, `apps/platform-admin-ui`, `apps/admin-ui`, and `apps/shared`. The resulting app roots are `apps/api`, `apps/ui-mobile`, and `apps/web`. `apps/api` and `apps/ui-mobile` were not modified. Current dirty FEAT-066 changes outside the retired portal directories remain untouched and uncommitted.
