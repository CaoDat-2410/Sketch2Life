# Sketch2Life Web

The single Vite application for Teacher, School Manager, BE1-backed school administration, and Platform Admin surfaces.

## Run locally

```powershell
npm ci
npm run dev
```

Open `http://localhost:5173/login` to choose a portal.

| Portal | Entry | Behavior |
| --- | --- | --- |
| Teacher | `/teacher/login` | Existing backend login and local-preview behavior are preserved. |
| School Manager | `/school/login` | Firebase sign-in followed by BE1 verification of the organization-level `school_admin` assignment; current UI supports class list/create. |
| School Manager preview | `/school/preview/login` | Fixture-only M01/M02 screens; actions are not persisted. |
| Platform Admin | `/platform/login` | Existing backend login and local-preview behavior are preserved. |

## Source layout

- `src/app`: the one browser router and central portal entry.
- `src/modules/teacher`: Teacher portal.
- `src/modules/school-manager/be1`: Firebase/BE1-backed school-admin routes and services.
- `src/modules/school-manager/preview`: existing fixture-only School Manager M01/M02 UI.
- `src/modules/platform-admin`: Platform Admin and Content Admin permission surfaces.
- `src/shared`: shared web login, role mismatch, API helpers, themes, and visual components.

The route prefixes organize presentation only. The backend remains responsible for authorization on each protected resource/action. Production hosting must serve this SPA entry for the role deep links; deployment configuration is outside this migration.
