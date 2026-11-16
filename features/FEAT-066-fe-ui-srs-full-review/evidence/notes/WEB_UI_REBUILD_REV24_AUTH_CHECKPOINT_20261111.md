# FEAT-066-EV-027 — Rev24 shared Auth rebuild and checkpoint

- Date: 2026-11-11 (Asia/Bangkok).
- Worktree/branch: `F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation`, `codex/fe-ui-web-remediation`.
- Plan: Rev24, SHA-256 `072778CC86CCF6C2CDE18CDD034276F75371A4930FF5C18924F58191187BC345`; direct user approval is recorded in `approvals/TASK_APPROVAL.md` before source changes.
- Product baseline: FEAT-063 v2.7-draft Rev57, SHA-256 `BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5`. Authority still marks the draft unsigned. Target requirements are §§1–31; §32 is implementation evidence only.
- Design reference: user-reviewed FEAT-066 Rev23 crayon concept boards and `WEB_UI_CRAYON_ATLAS_REV23.md`. Visual choices are not treated as new product policy.

## Scope and SRS boundary

The shared entry page presents the three SRS web portals: Teacher, School Manager and Platform Admin (§§2.3, 3, 21.5). Choosing a portal changes the destination and active label; it does not grant a role. Existing Firebase/auth and role-resolution boundaries remain. The visible local-preview action is explicitly labeled as non-persistent and does not call Firebase or the backend. Platform Admin role discovery is still unavailable in the current contract and is not claimed to work.

An authenticated session with a role that does not match a portal receives a shared role-mismatch state. The wrong portal shell and its data are not rendered; the existing logout action is offered. This is consistent with role separation and the SRS access-control/recovery requirements. No Parent route or role was added.

## Implementation

- Rebuilt the shared portal login markup and responsive paper/crayon layout in `apps/shared/WebPortalLoginPage.tsx` and `apps/shared/portal-login.css`.
- Added `apps/shared/RoleMismatchPage.tsx` and shared access-state styling in `apps/shared/role-crayon-theme.css`.
- Connected all three existing role apps to the shared visual tokens and ensured their role-mismatch route bypasses the foreign role shell. Existing app routes, login handlers, logout handlers and API contracts remain in place.
- Auth illustration is local SVG; no new dependency, image provider or remote 3D runtime was introduced.

## Manual local review

`capture_auth_rev24.mjs` used the isolated headless Chrome target. Network requests were restricted to HTTP on `127.0.0.1` ports 5172–5174; non-loopback HTTP(S) requests were blocked. Evidence is in `evidence/screenshots/auth-rev24/`.

- Captures: 9 total — each portal login at 1440×900 and 390×844, plus a wrong-role route for each portal at 1440×900.
- All six login captures have the correct active portal link and corresponding loopback destination; the preview notice is visible and the submit action fits within the first viewport.
- All nine captures report document width equal to viewport width, with no Vite error overlay. The capture observed no browser runtime exceptions.
- Each wrong-role route shows the role-specific mismatch heading and logout action, with no role shell visible.
- The School Manager process on port 5173 was verified by command line as Vite from this exact worktree. It returned stale transformed source despite the current files. Only that identified process was restarted, still bound to `127.0.0.1`; the fresh capture then showed the current guard and mismatch page.
- Desktop and narrow layouts and all mismatch screenshots were visually inspected. The login action remains clear and visible at 390px; mismatch content is centered, legible and unclipped.

## Limits and next section

This local review does not validate Firebase credentials, real sign-in, server-resolved roles or authenticated API behavior. It does not resolve the existing Platform Admin role-discovery dependency. Keyboard focus order and assistive-technology output were not device-tested. No automated tests/builds, live API, backend, production data, external provider or credentials were used. No commit or push was made.

Auth is the completed first Rev24 section. The next section is Teacher, to be rebuilt and checked against §§5.2, 7.3, 19–21 and applicable Teacher contracts before starting School Manager.
