# Parent auth UI refinement — 2026-11-10

## Approval

Plan revision 12, PLAN_REV12_COMPACT_AUTH_PREVIEW_AND_RECOVERY_UI.md, was explicitly approved by the owner. Its SHA-256 is 28ECAF08E925A1DE55C675062027639A34DFE0C2C2F32F2B017B3328E39F9DFC and is recorded in approvals/TASK_APPROVAL.md.

## Implementation

- Shortened the preview-only login notice and supporting copy.
- Changed the preview card from a stacked layout to a compact two-column row. The preview action remains 44 px high.
- Rebuilt the password-recovery presentation around the existing approved Parent login scene, background, color wash, auth panel, typography, fields, button, and focus styling.
- Preserved email prefill, return-to-login with the current email, unavailable status, and no-send/no-OTP/no-success behavior.
- Added no asset, dependency, backend/auth operation, or product requirement change.

## Rendered visual evidence

Captured the local Vite app in Microsoft Edge with mobile CSS viewport emulation. The login preview state was reached through the local Parent settings logout action in a temporary browser profile; it uses only the app’s synthetic preview data. The recovery route was opened directly.

| Screen | Viewport | Document scroll width | Main panel bounds |
|---|---:|---:|---:|
| Login preview | 375×812 | 375 px | 311×60 px; button 108×44 px |
| Login preview | 320×568 | 320 px | 264×70.4 px; button 108×44 px |
| Password recovery | 375×812 | 375 px | x=16 px, 343×367.6 px; bottom=796 px |
| Password recovery | 320×568 | 320 px | x=16 px, 288×347.2 px; bottom=552 px |

Screenshot files are stored locally under evidence/screenshots/parent-auth-revision12/:

- login-375x812.png — SHA-256 3D36503E79A614C06EAA1101FE01F8893A21EA9EC0D8C7B9A788C2D4337F61E4
- login-320x568.png — SHA-256 A4AEEDA5A13BB23D06382E4AF7A606DD9CBBEBFD97169F7BA6A8AA1B7B3A38D3
- recovery-375x812.png — SHA-256 E8961AE643E666AC521172B8386121AC3F438D0951E71F4341C0DEC73489D4B1
- recovery-320x568.png — SHA-256 6D6933BCAD59AEE46F686E3F103DFB54627664E7235B4B2F52E76963715D4F

The repository .gitignore rule at line 107 excludes FEAT-036 screenshot PNGs, so these rendered captures remain local and were not staged.

## Verification and limits

- Vite returned HTTP 200 for /p11-authentication, /p14-password-recovery, the transformed ParentScreens.tsx module, and parent-login-animation.css.
- git diff --check exited successfully. Git reported CRLF-to-LF normalization warnings for the modified FEAT-036 Markdown files; there were no whitespace errors.
- No automated tests or production build were run.
- Screenshots use synthetic local preview data and do not establish physical-device behavior. The canonical FEAT-063 SRS v2.7-draft still leaves exact Parent account-recovery UX and Parent Web target scope open. The task worktree’s SRS authority copy still says v2.5-draft; that drift was not changed.
