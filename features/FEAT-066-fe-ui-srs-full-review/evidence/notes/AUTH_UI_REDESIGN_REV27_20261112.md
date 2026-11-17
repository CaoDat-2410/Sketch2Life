# Shared web auth UI redesign — Rev27 completion

**Status:** Implementation complete for user review. The `design-taste-frontend` manual gate ended `GATE: OPEN 22 (rounds used up)` after round 3; its remaining findings are recorded below. No commit or push was made.

## Approval and product authority

- The implementation follows the direct user authorization recorded in Rev27 of `plan/PLAN.md` and `approvals/TASK_APPROVAL.md` before source edits.
- Pre-code plan SHA-256: `C9EF609A920F3C53F0153ED109660B85003D4D03A8E1E76C2F46C3EB2EEF21C2` (rechecked at completion).
- Product baseline: `docs/context/SRS_AUTHORITY.md` points to FEAT-063 `SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`, v2.7-draft Rev57, SHA-256 `BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5`. The authority record still identifies it as an unsigned draft.
- Web portals are Teacher, School Manager and Platform Admin. Content Admin remains a Platform Admin permission; Parent remains outside this web auth scope.
- Brainstorm alternatives and selection are recorded in `AUTH_UI_REDESIGN_BRAINSTORM_REV27_20261111.md`. The selected direction is a Vietnamese-first crayon learning-studio login with direct role links and one clear sign-in action; no extra role-selection step or invented auth flow.

## Changes

- Rebuilt the shared login composition in `apps/shared/WebPortalLoginPage.tsx` and `apps/shared/portal-login.css`: role-aware school-friendly heading and accent, clearer portal links, warm paper surface, large school illustration, and a distinct login panel.
- Added a keyboard skip link, retained visible focus rings and explicit field labels, and ensured the small-screen brand link has a 44px minimum touch height. Portal links expose one `aria-current="page"` for the active route.
- Reused the installed Three.js school/book scene on wide screens. At narrower widths the static SVG is used. The same SVG now sits inside the scene host as a true fallback; shader-link failure clears the ready state and stops animation so the illustration remains visible. Reduced-motion mode renders a static frame.
- Kept the existing `/login` URLs, role mappings, sign-in adapter, pending/error behavior, post-login destinations, preview behavior and Platform Admin role-discovery warning. The local preview remains explicitly non-authenticating and does not call the backend or persist credentials. No new asset, dependency, auth contract, price, account-recovery, organization-selection or support flow was added.
- No Parent/mobile, Teacher/Manager/Admin authenticated UI or backend files were changed for Rev27.

## Manual browser review

The loopback-only preview apps were already listening at Teacher `127.0.0.1:5172`, School Manager `127.0.0.1:5173` and Platform Admin `127.0.0.1:5174`. Existing listeners were reused. The capture harness allowed only those three local HTTP origins and did not submit a form.

- `capture_auth_redesign_rev27.mjs` saved 12 screenshots: each role at 1440×900, 1024×768, 768×1024 and 390×844. Files are in `screenshots/auth-redesign-rev27/`.
- All 12 observations have zero horizontal overflow, Vite overlays, incorrect active-portal counts, missing first-viewport submit controls, runtime exceptions, console errors or HTTP error responses. Role names and current routes match the page.
- Keyboard review for all three roles records focus in this order: skip link, brand link, Teacher, School Manager, Platform Admin, email field. Every step has `:focus-visible`; Shift+Tab from the email field returns to the Platform Admin link. One portal link per page is marked current.
- After the final post-gate fallback adjustment, computed-layer observations report WebGL ready + SVG opacity 0 for all six 1440/1024 captures, and SVG fallback visible for all six 768/390 captures. The desktop images were visually reviewed again after the cross-role fix.
- `verify_auth_webgl_fallback_rev27.mjs` forced WebGL2 program-link checks to fail at 1440×900. Two link failures were injected; `data-webgl-ready` stayed false, the canvas did not claim ready, the SVG fallback remained at opacity 1, and there were zero runtime exceptions. Evidence: `webgl-failure-fallback-1440x900.png` and `webgl-fallback-observation.json`.
- The harness blocked all non-loopback requests. This included the existing Google Fonts CSS request during the isolated fallback check; no external request was allowed. Browser capture recorded no product API response. The app was not authenticated and no credentials or real user/child data were used.
- No automated tests or builds were added or run.

## Frontend skill gate

The full design-taste gate reached round 3 and returned `GATE: OPEN 22 (rounds used up)` before the last manual review found that fallback opacity was not consistently applied in two portals. The final source now binds the fallback layer opacity directly to React scene readiness. After that adjustment, all 12 role/viewport screenshots and the forced shader-link failure observation were rerun; all three desktop scenes now show only the WebGL model, while the forced-failure case shows the SVG. No fourth full gate round was run because the skill maximum had been reached. The stored 22 open findings do not include `gl-fallback`; they are the shader scanner and marketing-layout assumptions below, unchanged by the final opacity binding. The 22 open findings are:

- Three `shader-lint` findings on bundled Three.js shader text (`#include <common>`, `sampler3D`, `sampler2DShadow`). The static scanner treats preprocessor/built-in shader tokens as identifier violations; the installed Three.js scene renders in the local browser, and failure recovery was exercised separately.
- The other 19 are landing-page composition heuristics that do not fit an authentication page: full-screen/section rhythm (`hero-fill`, `hero-screen`, `section-height`, `flush`); treating the two portal links and the single primary action as three kinds of buttons (`button-styles` ×2); expecting a hero CTA and product-selling headline (`cta`, `copy-headline`); requiring marketing-page section structure and a single content container (`one-section`, `one-heading`, `container-edges` ×5, `container`, `split-pair`); and treating the form panel as a closing/visual-only section (`text-only`, `moment-none`). Duplicating the sign-in action in the hero or reshaping the auth form solely for these checks would make the auth hierarchy less clear, so these were left open and are reported rather than hidden with waivers.

The gate also emitted warnings that are checker-specific: it does not recognize the Vietnamese skip-link wording, reads the login field’s standard `autocomplete="username"` token as lacking `autocomplete="email"`, and assumes marketing share metadata. The source markup and manual focus evidence show the skip link is the first keyboard stop; the password-manager token remains `username` because this is a sign-in identifier paired with `current-password`.

## Evidence index

- Brainstorm: `evidence/notes/AUTH_UI_REDESIGN_BRAINSTORM_REV27_20261111.md`
- This completion note: `evidence/notes/AUTH_UI_REDESIGN_REV27_20261112.md`
- 12 role/viewport captures and `observations.json`: `evidence/screenshots/auth-redesign-rev27/`
- Forced WebGL-failure screenshot and observation: `webgl-failure-fallback-1440x900.png`, `webgl-fallback-observation.json`
- Capture helpers: `evidence/capture_auth_redesign_rev27.mjs`, `evidence/verify_auth_webgl_fallback_rev27.mjs`
- Taste gate report: `evidence/screenshots/auth-redesign-rev27/.taste-skill/gate.json` and `.taste-skill/gate/consistency/report.json`