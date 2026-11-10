# FEAT-036 plan revision 14 — Optimize Parent auth layout for tablets

- Revision: 14
- Status: APPROVED
- Prepared / approved: 2026-11-10
- Type: Parent authentication responsive UI refinement
- Product baseline: FEAT-063 SRS v2.7-draft, the canonical working baseline. It remains unsigned.
- Requirement boundary: Parent Web target-client scope and Parent registration/recovery flows remain open in the SRS. This plan changes presentation and responsive layout only.

## Objective

Use tablet screen space well across Parent sign-in, password recovery, and registration while preserving the current mobile auth design.

## Scope

1. Add a tablet breakpoint for the three Parent auth routes, using a spacious two-column composition with the existing auth illustration on one side and the form panel on the other.
2. Set tablet panel width, spacing, typography, control size, and safe-area padding for portrait and landscape layouts.
3. Preserve the current single-column phone layout below the tablet breakpoint, including its compact preview card and registration/recovery links.
4. Keep dark theme, keyboard-visible focus, reduced-motion behavior, and auth-page safe-area ownership.
5. Reuse existing approved illustration and UI components. Add no assets, dependencies, account behavior, auth/backend calls, or product requirements.
6. Record tablet and phone visual review in FEAT-036 status, context, decisions, and feature-local evidence.

## Acceptance criteria

1. At 768x1024 portrait and 1024x768 landscape, sign-in, recovery, and registration use the wider tablet composition; the art and panel remain distinct and readable.
2. The sign-in preview card and registration/recovery links remain visible and usable on tablet.
3. Tablet layouts have no horizontal overflow and respect safe areas. Touch targets remain at least 44 px.
4. Existing phone layouts at 320x568 and 375x812 remain usable without horizontal overflow.
5. Rendered review and screenshot evidence are stored under FEAT-036; Vite routes/modules return HTTP 200 and git diff --check passes. No automated tests or production build are included.

## Out of scope

- Authentication, account creation, recovery, backend/API, or Firebase behavior.
- Deciding Parent Web target-client scope or open Parent registration/recovery requirements.
- Teacher, School Manager, or Platform Admin UI.
- New/generated assets, dependencies, SRS changes, deployment, publishing, commit, or push.
- Automated tests and production build.

## Authorization

The project owner explicitly requested: “Sau đó tối ưu cho các thiết bị tablet ipad đồ lun cho tôi”. This authorizes responsive presentation changes for the Parent auth screens described above.
