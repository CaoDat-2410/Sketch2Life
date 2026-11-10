# FEAT-036 plan revision 13 — Restore Parent registration UI and auth link

- Revision: 13
- Status: APPROVED
- Prepared / approved: 2026-11-10
- Type: Parent authentication UI refinement
- Product baseline: FEAT-063 SRS v2.7-draft, the canonical working baseline. It remains unsigned.
- Requirement boundary: Parent registration UX remains an open product question in the SRS. This plan adds the requested visual screen and navigation only; it does not decide the registration flow.

## Objective

Restore a Parent registration screen in the auth visual system and make it reachable from the sign-in UI.

## Scope

1. Add a clear, keyboard-accessible registration link to the Parent sign-in screen.
2. Add a responsive Parent registration page at /p15-parent-registration, reusing the approved auth background, panel, typography, fields, button, focus, dark-theme, reduced-motion, and safe-area patterns.
3. Carry the entered email from sign-in to registration and back to sign-in.
4. Keep the registration form visual-only and clearly unavailable until a product flow and service are defined. Do not create accounts, call auth/backend services, send email or verification codes, persist credentials, or show false success.
5. Allow unauthenticated access to the registration route and classify it as an auth page in the mobile shell.
6. Reuse existing approved assets and dependencies. Update FEAT-036 context, decisions, status, and feature-local evidence.

## Acceptance criteria

1. The sign-in UI presents a visible “Chưa có tài khoản? Đăng ký” entry that opens the registration page.
2. The registration page matches the existing Parent auth visual system and provides labeled email, password, and password confirmation fields, a truthful unavailable state, and a return-to-sign-in link.
3. Email is carried between sign-in and registration; passwords are not placed in route state. The unavailable action performs no account or provider operation and reports no success.
4. The unauthenticated registration route renders directly and through the sign-in link; the mobile shell applies auth safe-area ownership.
5. At 320x568 and 375x812, the registration view remains readable and usable by scrolling when needed, with no horizontal overflow or controls clipped.
6. Route/module responses and rendered visual review are recorded under FEAT-036 evidence; git diff --check passes. No automated tests or production build are included.

## Out of scope

- Deciding or implementing Parent account creation, verification, consent, role provisioning, or recovery behavior.
- Changes to the SRS, backend/API, Firebase configuration, email delivery, other portals, assets, or dependencies.
- Automated tests/builds, deployment, publishing, commit, or push.

## Authorization

The project owner explicitly requested: “Thiếu đăng ký lấy lại UI và đường dẫn đăng ký ở UI auth cho tôi đi”. This authorizes the visual-only registration page and sign-in entry described above.
