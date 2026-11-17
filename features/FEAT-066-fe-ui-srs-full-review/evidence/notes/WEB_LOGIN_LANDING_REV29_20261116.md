# FEAT-066-EV-035 — Rev29 role login landing and removal of preview UX

**Date:** 2026-11-16
**Plan:** Revision 29, SHA-256 87F02A9B3CD64D21F1D1D1D051445E0413B5C03AC635BFF507E7CF3F962576C0
**Task SRS:** Owner-selected unsigned v2.7-draft Rev68 recorded in Revision 28. The repository's Rev60 source-register mismatch remains open.

## Change record

- /login is the shared role-entry page shown in the approved reference; the School Manager preview panel is gone.
- The legacy /teacher/login URL redirects to /login. Teacher continues at /teacher/sign-in; the role cards lead to /teacher/sign-in, /school/login, and /platform/login.
- /school/preview/* redirects to /login; the old School Manager preview app and its role navigation/source implementation were removed. The School Manager login now links back to the role chooser instead of a preview.
- Removed the no-password local login bypass. Teacher and Platform Admin use the existing Firebase sign-in/role-resolution adapter; School Manager retains its BE1 authService and assignment gate. Stored web roles are accepted only with the verified-session source marker written after role resolution; old local preview flags are cleared.
- Existing API contracts and role checks were preserved. The Platform Admin warning remains because the backend does not expose role/capability discovery. No API success or user data is fabricated.
- Removed the existing Google Fonts remote import found during browser review; current system font fallbacks are used, so the final local review makes no external requests.

## Visual and route review

Screenshots are in screenshots/web-login-rev29-20261116/:

- role-chooser.png and role-chooser-390.png
- teacher-login-redirect.png and preview-route-redirect.png
- teacher-sign-in.png
- school-manager-login.png and school-manager-login-390.png
- platform-admin-login.png

observations.json records browser checks at 1280×900 and 390×844. The three role destinations resolved from the DOM to the expected sign-in paths. /teacher/login and /school/preview/login both ended at /login. The chooser had three cards and no form/preview copy; Teacher and School Manager routes contained real sign-in forms with password fields. The Platform Admin warning remained visible.

Document width matched the viewport at 390px; no horizontal overflow was reported at any captured size. Runtime exceptions and console errors were empty. External requests were empty after the font import removal. Keyboard verification focused the first role card after two Tabs and the sign-in button after seven Teacher Tabs or five School Manager Tabs; each reported :focus-visible, a solid outline, and 3px width.

## Validation limits

npm run build passed after the final source changes. No application tests were run, no credentials were entered, no sign-in was submitted, and no product API was called. Platform Admin role discovery remains unavailable until the backend provides its API. Required repository pre-commit validators and final commit state are recorded in the FEAT-066 status closeout.
