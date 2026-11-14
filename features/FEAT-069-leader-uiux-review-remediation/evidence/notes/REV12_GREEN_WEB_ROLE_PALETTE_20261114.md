# Rev12 — Green palette for the three web roles

Date: 2026-11-14 (Asia/Saigon). Approved plan: `plan/PLAN_REV12_GREEN_WEB_ROLE_PALETTE.md`, SHA-256 `4DA12CF06585D6D7141D4A62167C657541B45562ADF045F34A2F3F20EDA1ADAC`.

## Finding and implementation

The last-loaded shared web stylesheet (`UI_Project/shared/rev8ColorSystem.css`) still used blue, teal-blue, and purple accent tokens and surfaces for Teacher, School Manager, Platform Admin, and the shared role-entry portal, while `webWorkspace.css` and `roleDashboards.css` also had teal-blue and blue welcome/intro backgrounds for School Manager and Platform Admin and `BrandMark.tsx` fell back to `#315efb` without `--brand-primary`.

Updated `UI_Project/shared/rev8ColorSystem.css` so:
- Teacher, School Manager, and Platform Admin web workspaces share a coordinated green brand/action palette aligned to Parent's `#3f7559` action color (`--brand-primary`, `--accent`, `--accent-dark`, `--accent-soft`, `--hero`, `--hero-2`, ink/muted/line/subtle tokens, focus outlines, and `.dashboard-welcome` / `.dash-intro` role surfaces).
- The shared role-entry/sign-in preview (`.unified-auth*`) uses the same green palette for active role selection, focus rings, primary submit button, links, and soft backgrounds.
- Warm yellow decorative/CTA accents (`.web-hero-cta`, `.unified-preview-actions button`) and semantic warning, danger, and status colors remain intact.

## Verification

- `npm --prefix UI_Project run build`: passed all five workspaces (`parent-ui`, `teacher-ui`, `school-manager-ui`, `platform-admin-ui`, `web-ui`).
- Live browser visual inspection of all four web previews (`http://localhost:5172/`, `http://localhost:5173/`, `http://localhost:5174/`, `http://localhost:5175/`): rendered with 0 console errors; primary buttons, selected navigation/tabs/role cards, links, focus outlines, and hero/welcome banners use the green palette while warm yellow accents and semantic status pills (active, warning, error) remain intact and readable.
- `git diff --check` and `python tools/validate_repository_security.py` passed.
- No automated tests were run. No API, backend, authentication, SRS, layout, or data behavior changed.

## Limits

This is a focused UI color synchronization pass across the three web roles and shared web portal. It is not formal leader acceptance, SRS sign-off, or API integration.
