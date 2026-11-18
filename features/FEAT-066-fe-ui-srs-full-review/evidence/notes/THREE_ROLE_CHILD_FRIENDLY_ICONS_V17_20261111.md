# Three-role child-friendly icon refresh (Rev17)

Date: 2026-11-11 (Asia/Bangkok)

## Authority and approval

- The current working SRS remains FEAT-063 v2.7-draft Rev57, SHA-256 `BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5`; it is unsigned and awaiting owner sign-off.
- Rev17 is a visual implementation request from the user, not a new SRS requirement. The plan and direct approval were recorded before changing source code. Plan SHA-256: `49D2B35334A952201387661B50C57DA971453F6C3A8F7518E4E86D48A90AC0E4`.
- Worktree/branch: `F:/Github/Sketch2Life-worktrees/fe-ui-web-remediation`, `codex/fe-ui-web-remediation`.

## Implementation

- Updated the shared local renderer at `apps/shared/RoleDashboardIcon.tsx`. All three role apps re-export this component as their existing `Icon`, so the revised set applies to Teacher, School Manager, and Platform Admin shell navigation, dashboard/content icons, role/status indicators, and shared login-page icons.
- Used rounded strokes, slightly stronger pastel accent echoes, and semantic crayon colors (blue, teal, mint, yellow, coral, and lilac). Current foreground color remains controlled by each existing UI context to preserve contrast; the existing glyph names and their meanings are unchanged.
- Softened the shared icon badge corners and added a subtle sticker-like edge. No route, text, role check, action, interaction, touch target, aria label, package, manifest, network asset, backend, or API changed.
- Brand artwork and custom inline illustrations are outside this shared icon renderer and were not changed.

## Manual review

- Captured 15 screenshots in `evidence/screenshots/role-icons-v17/`: Teacher, School Manager, and Platform Admin login plus representative dashboard at 1440x900 and 390x844.
- Used an isolated headless browser tab. Only requests to the three existing loopback Vite previews on `127.0.0.1:5172`, `:5173`, and `:5174` were allowed; other HTTP(S) requests were blocked.
- The login screenshots show each unauthenticated role login. Dashboard routes use synthetic local preview session state and existing fixture/unavailable UI; no credentials or real user/child data were used.
- Across all 15 captures: no horizontal overflow, Vite error overlay, or observed browser runtime exception. `observations.json` records per-page route, dimensions, document width, visible heading and SVG count.
- Screenshots were visually inspected at desktop and narrow widths, plus dark-mode desktop dashboards for all roles. Icons remain aligned with their text and buttons; layouts and hit targets remain unchanged. Admin's dashboard capture displays the existing truthful backend-unavailable state. The helper restores the browser storage snapshots after capture.

## Validation limits

- This is a visual preview. No automated tests or builds were run. No screen-reader audit was run; the icon component remains `aria-hidden="true"`, with existing adjacent accessible names retained.
- Changes remain uncommitted and unpushed for user review.
