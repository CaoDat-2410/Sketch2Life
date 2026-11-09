# Parent login transition and recovery implementation — 2026-11-09

## Approved scope

Plan revision 7 is approved in `approvals/TASK_APPROVAL.md`. It covers the Parent login transition,
its separate public password-recovery route, and removal of the Settings recovery row/mock OTP flow.
It does not authorize backend or identity-provider changes, automated tests/builds, deployment,
commit, or push.

## Reference provenance

- Owner-supplied video: `Ghi Màn hình 2026-10-29 lúc 23.50.22.mov`
- Video SHA-256: `46CF7A155F751F0FD11CF9C8CB6DA267924236E0C9E79CE9B75014443B7DA5C8`
- Video: 2880×1800, 60 fps, 31.366667 seconds. Contact sheets are stored under
  `evidence/raw/login-transition-video-20261029/`.
- Account/security screenshot supplied in the request: `codex-clipboard-4276e37c-25f6-421b-a2bd-e6ff8a6fc80f.png`
- Screenshot SHA-256: `A0C02F5B87E12122CD158647337FE605886E1FB3A85CF3892618B5D356E8ACA8`

## Changes

- `P11AuthenticationPage` now opens with the ZIP-based splash alone, then transitions to the login
  form. The animation plays once per browser session; returning from recovery does not replay it.
  `prefers-reduced-motion` skips the animated wait and displays the final login composition.
- The login page has a “Quên mật khẩu?” link that opens `/p14-password-recovery` and carries the
  entered email as an optional prefill.
- `P14PasswordRecoveryPage` is reachable while logged out. It has email entry, clear return-to-login
  actions, and a visible unavailable notice. Its submit handler does not send email, issue OTP, or
  claim a successful reset because no reset operation exists in the current auth bridge/API.
- `P13SettingsPage` no longer shows “Quên mật khẩu” and no longer contains the local fake OTP/send/
  reset-success flow. The separate “Đổi mật khẩu” row remains.
- `MobileLayout` hides the status bar, preview banner, and navigation tabs on recovery just as it
  does on login.

## Verification and limits

- `git diff --check` passed. Git emitted line-ending notices for existing feature context/decision
  files; no whitespace error was reported.
- The running Vite server returned HTTP 200 for `/p14-password-recovery`, `/src/App.tsx`, the
  transformed `ParentScreens.tsx` module, and `parent-login-animation.css`. The transformed page
  module includes `P14PasswordRecoveryPage` and contains no Vite internal-server-error response.
- The applied background, logo, and pencil PNG assets each returned HTTP 200 from Vite.
- No automated tests or builds were run, consistent with the approved plan.
- A rendered screenshot was not captured because the local Edge CDP page did not respond in the
  earlier capture attempt. Pixel-level comparison against the recording remains pending.
