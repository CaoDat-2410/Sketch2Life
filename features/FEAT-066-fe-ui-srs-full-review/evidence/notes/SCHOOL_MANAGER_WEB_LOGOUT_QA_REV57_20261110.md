# School Manager logout flow QA — 2026-11-10

## Scope and source

- Worktree: `F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation`; branch `codex/fe-ui-web-remediation`.
- Plan: revision 5, approved before implementation; SHA-256 `D90C628F1A8283E59582256CB8ED656C8E69C6C27A520D827C1BAD7CB42FEE53`.
- Canonical product source remains FEAT-063 SRS v2.7-draft Rev57, SHA-256 `BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5`, unsigned. §21.5 does not define a School Manager logout screen/control; this issue was reported directly by the user while reviewing School Manager flows.
- The UI exposes the existing `TeacherContext.logout` handler from the shared authenticated `ManagerLayout`. No auth policy, backend, provider, or separate session-clearing behavior was added.

## Local review method

The existing Vite preview returned HTTP 200 at `http://127.0.0.1:5173/` and was already listening on `127.0.0.1:5173`; it was reused. A clean Edge headless review browser used CDP on `127.0.0.1:9233` only. HTTPS and the local backend ports used by the frontend were blocked for this capture. No credentials, real user/child data, backend, or external provider were used.

The local preview was given only its existing synthetic School Manager session keys (`s2l-web-role=MANAGER`, `s2l-web-authenticated=true`) so the authenticated routes could be reviewed. The actual logout button was focused and activated with Enter. After logout, the test directly navigated back to the protected route to check the auth guard.

## Results

| Route | Viewport | Logout control | Enter activation and session result | Protected-route revisit |
|---|---:|---|---|---|
| `/m02-organization-management` | 1440×900 | Native button, accessible name `Đăng xuất`, 219×44px, visible in viewport | Returned to `/login`; both session keys were removed | Direct route visit remained at `/login` |
| `/m02-organization-management?section=settings` | 1440×900 | Native button, accessible name `Đăng xuất`, 219×44px, visible in viewport | Returned to `/login`; both session keys were removed | Direct route visit remained at `/login` |
| `/m02-organization-management` | 390×844 | Accessible name retained on the collapsed icon button, 44×44px, visible in viewport | Returned to `/login`; both session keys were removed | Direct route visit remained at `/login` |
| `/m02-organization-management?section=settings` | 390×844 | Accessible name retained on the collapsed icon button, 44×44px, visible in viewport | Returned to `/login`; both session keys were removed | Direct route visit remained at `/login` |

All four routes/viewports had no page-level horizontal overflow. The button has native button semantics, `tabIndex=0`, `aria-label="Đăng xuất"`, and visible keyboard focus styling. `window.sketch2lifeAuth` was not configured in this preview; optional Firebase sign-out behavior was therefore not exercised. The existing handler's local session clearing and protected-route behavior were verified.

## Evidence files

- `evidence/screenshots/logout-check/observations.json` — route, viewport, target size, keyboard activation, session state, and protected-route results.
- `evidence/screenshots/logout-check/logout-{dashboard|settings}-{desktop|narrow}-before.png` — authenticated state with the logout action visible.
- `evidence/screenshots/logout-check/logout-{dashboard|settings}-{desktop|narrow}-after.png` — login screen after logout and protected-route revisit.
- `evidence/capture_school_manager_logout.mjs` — local CDP evidence-capture helper.
- `evidence/screenshots/remediation-before/m02-dashboard-desktop.png` — original dashboard image without a logout action.

No automated test, test suite, scanner, or build was run. This was a local visual and keyboard interaction review only.
