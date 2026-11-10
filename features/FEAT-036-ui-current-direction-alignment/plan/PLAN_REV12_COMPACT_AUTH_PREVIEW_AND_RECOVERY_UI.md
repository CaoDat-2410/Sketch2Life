# FEAT-036 plan revision 12 — Compact preview panel and align password recovery with auth UI

- Revision: 12
- Status: APPROVED
- Prepared / approved: 2026-11-10
- Type: Parent authentication UI refinement
- Product baseline: FEAT-063 SRS v2.7-draft, as required by the repository AGENTS instructions; the task worktree's authority copy still records v2.5-draft, so that source-register drift remains open and is not resolved by this task.
- Parent Web target scope and exact Parent account-recovery UX remain open in the canonical SRS. This plan changes the existing local Parent UI only and does not decide those questions.

## Objective

Reduce the vertical footprint of the local-preview panel on Parent sign-in and make the password-recovery screen use the same auth visual system as sign-in.

## Scope

1. Compact the local-preview panel on /p11-authentication into a small responsive layout. Keep its purpose, data disclaimer, and “Mở bản xem thử” action clear, and preserve a minimum 44 px action target.
2. Shorten the local-preview-only unavailable message where it repeats the preview action; keep the separate generic unavailable message for non-preview auth sessions.
3. Restyle /p14-password-recovery to reuse the existing approved Parent auth background, palette, panel, heading, field, button, and focus patterns.
4. Preserve the recovery email prefill, return-to-login action with the current email, unavailable status, and no-send/no-OTP/no-success behavior.
5. Preserve responsive layout, dark theme, keyboard focus, semantic labels/status announcements, reduced-motion support, and safe-area handling.
6. Reuse existing approved assets and code primitives. Add no assets, external dependencies, backend/auth operations, or product requirement changes.
7. Record the exact implementation and visual/source verification in FEAT-036 evidence, context, decisions, and status.

## Acceptance criteria

1. The preview panel uses less vertical space than its current stacked layout while retaining concise explanatory copy and a clearly labeled action.
2. The preview action remains keyboard accessible and at least 44 px high; the compact panel has no horizontal overflow at 320 px and 375 px mobile widths.
3. The recovery page visibly follows the sign-in page's auth styling: shared approved background/palette, panel hierarchy, typography, form controls, and primary-button treatment.
4. At mobile widths and short viewport heights, the recovery page remains usable without horizontal overflow or obscured controls; safe-area padding is applied once.
5. Recovery email prefill and return navigation remain functional. Submitting continues to show that recovery is unavailable; no email, OTP, backend call, or false success is introduced.
6. Dark theme, keyboard-visible focus, semantic labels/status, and reduced-motion behavior remain supported.
7. The Vite routes/modules return HTTP 200, rendered mobile review is recorded, and git diff --check passes. No automated tests or production build are included.

## Out of scope

- SRS changes or a decision on Parent Web support or exact Parent account-recovery behavior.
- Authentication provider, backend/API, email, OTP, registration, credential, or account-state changes.
- Changes to other Parent screens or other portals.
- New/generated assets, dependency changes, deployment, publishing, commit, or push.
- Automated tests and production build.

## Authorization

The project owner explicitly requested in this conversation: “Thu gọn cái này lại cho tôi và làm UI phần quên mật khẩu theo format của UI auth đi”. This is the task approval for the bounded scope above.