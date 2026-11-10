# Three-role web login UI — Rev57 review

Date: 2026-11-10 (Asia/Bangkok)
Evidence ID: FEAT-066-EV-008
Plan: revision 7, SHA-256 72F462DCECE9DC2545368094FBA86E68AC3992589FD448CED5E76E82F057FD36
SRS: FEAT-063 v2.7-draft Rev57, SHA-256 BE0D656966FDE91BA7CD5C914C319EF301D137985EF5CC91B94F36FEBCF61FB5; unsigned / awaiting owner sign-off.

## SRS role mapping

SRS §3 identifies the three web portal roles as Teacher, School Manager, and Platform Admin. The shared login maps them to the existing auth values teacher, school_manager, and platform_admin. Content review is a Platform Admin permission, not a fourth role. Parent is a separate Android-targeted role and was not included.

Each portal retains its existing /login route and portalRole:

| SRS role | Visible label | App / local login URL | API role |
|---|---|---|---|
| Teacher | Giáo viên / Teacher | apps/teacher-ui / http://127.0.0.1:5172/login | teacher |
| School Manager | Quản lý trường / School Manager | apps/school-manager-ui / http://127.0.0.1:5173/login | school_manager |
| Platform Admin | Quản trị nền tảng / Platform Admin | apps/platform-admin-ui / http://127.0.0.1:5174/login | platform_admin |

The recording was used only for visual direction (warm paper colors, editorial hierarchy, restrained ornament and a product-style 3D focal point). Its unrelated copy and instructions were not used.

## Changed implementation

- Reworked apps/shared/WebPortalLoginPage.tsx and added apps/shared/portal-login.css for the shared role-aware login layout, portal navigation, fields, preview/error states, and responsive structure.
- Added apps/shared/PortalLoginScene.tsx, a local low-poly school/book sculpture with no external model, texture, or runtime request.
- Pinned three 0.187.0 as runtime dependency and @types/three 0.187.0 as development dependency in the three approved web apps. Updated their applicable npm lockfiles and Vite/TypeScript aliases so shared source resolves each app's local modules. Local pnpm/npm caches were empty; install scripts and npm audit were disabled during official npm package installation. The browser loads Three from the local Vite bundle.
- Existing Firebase sign-in, backend role resolution, errors, preview notice, role-specific landing route, and Admin role-discovery failure remain unchanged.
- Development role links use loopback ports 5172/5173/5174. Production destinations are never guessed; each other portal requires an explicit HTTPS /login environment URL: VITE_S2L_TEACHER_LOGIN_URL, VITE_S2L_SCHOOL_MANAGER_LOGIN_URL, and VITE_S2L_PLATFORM_ADMIN_LOGIN_URL. Missing or invalid destinations display as unavailable.

## Manual UI review

Local Vite previews were launched only on 127.0.0.1 ports 5172, 5173, and 5174. An isolated headless Edge browser was bound to 127.0.0.1:9233; screenshot scripts blocked HTTPS requests and no credentials, backend, Firebase, provider, or real user data were used.

Before screenshots are in evidence/screenshots/auth-before/; after screenshots and observations.json are in evidence/screenshots/auth-after/. Each contains Teacher, School Manager, and Platform Admin login at 1440×900 and 390×844.

Observed results:

- All three /login pages loaded with their matching role heading and current portal selected.
- Each local page exposed exactly the other two login destinations. Click-through by keyboard from School Manager to Teacher and direct link from Teacher to Platform Admin landed at the expected app /login pages.
- Two Tab presses from the document start focused the Teacher role link with a visible outline; Enter activated it.
- Role navigation exposes the accessible label “Chọn cổng đăng nhập”, anchor link semantics, aria-current="page" on the active role, and current labels. Email uses a visible label and type=email. The browser accessibility tree exposed the main/navigation landmarks, role links, headings, email textbox label, and preview button name; the DOM also confirmed aria-current="page" on the selected role. No screen-reader device/application session was run.
- At 390px, each page has documentWidth equal to innerWidth (390px). After the first capture exposed overlapping mobile heading and description margins, spacing was corrected and all three pages were recaptured. Submit action bottoms are within the 844px viewport: Teacher 731px, School Manager 731px, Platform Admin 750px. Role links are at least 48px high. Desktop pages fit 1440×900 with no horizontal overflow.
- Three.js rendered locally at 520×243 desktop and 354×135 narrow, capped at DPR 1.35 and throttled to about 30fps. The CSS fallback is hidden while WebGL is ready.
- With prefers-reduced-motion: reduce, the scene remains visible but uses the static frame (data-animation="reduced-motion"). Forcing WebGL context loss switched to the visible fallback without page overflow.

The browser was in the repository's existing local preview state because no Firebase auth bridge was configured. The observed form therefore showed the explicit “Xem thử cục bộ” email-only action. No real sign-in was attempted. The production credential form was reviewed in source only, not submitted.

## Existing authentication/API limitations

- Teacher and School Manager real sign-in still depends on the existing Firebase bridge and backend assignment resolution; it was not end-to-end tested.
- Existing signInAndResolveRole explicitly rejects Platform Admin role discovery with ROLE_DISCOVERY_UNAVAILABLE (HTTP 501) because no Platform Admin role API exists. The Platform Admin login UI is present and accurately warns about this; successful real Platform Admin login remains blocked on backend role discovery.
- Production portal hostnames are absent from the SRS and were not configured or tested. Release configuration must supply the three HTTPS /login URLs.

No automated tests or builds were added or run. This evidence covers local presentation, links, keyboard behavior, reduced motion, and WebGL fallback only; it does not claim authenticated or backend behavior.
